#!/usr/bin/env python3
"""
OCR-Pipeline: Mistral Document AI + Gemini

Unterstuetzt mehrere OCR-Engines fuer verschiedene Dokumenttypen.

Usage:
    # Einzelnes PDF
    python -m scripts.ocr.ocr_pipeline --input data/source/pdf/2310.pdf

    # Alle PDFs
    python -m scripts.ocr.ocr_pipeline --all

    # Bestimmte Engine
    python -m scripts.ocr.ocr_pipeline --input data/source/pdf/2310.pdf --engine mistral
"""

import argparse
import base64
import json
import os
import sys
import time
from pathlib import Path

from scripts.config import (
    GEMINI_API_KEY,
    GEMINI_OCR_MODEL,
    MISTRAL_MAX_PAGES_PER_REQUEST,
    MISTRAL_MODEL,
    MISTRAL_RESULTS_DIR,
    MISTRAL_TIMEOUT_SECONDS,
    SCANS_DIR,
)
from scripts.utils import check_gpu, pdf_to_images

# Windows: Symlink-Warnung unterdruecken
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"


class MistralOCR:
    """Mistral Document AI via Azure AI Foundry."""

    def __init__(self):
        self.endpoint = os.environ.get("MISTRAL_DOC_AI_ENDPOINT", "")
        self.api_key = os.environ.get("MISTRAL_DOC_AI_KEY", "")
        self.model = MISTRAL_MODEL
        self.max_pages_per_request = MISTRAL_MAX_PAGES_PER_REQUEST

    def _check_config(self):
        """Prueft ob Endpoint und Key konfiguriert sind."""
        if not self.endpoint:
            raise ValueError(
                "MISTRAL_DOC_AI_ENDPOINT nicht gesetzt. "
                "Setze die Umgebungsvariable oder erstelle eine .env-Datei."
            )
        if not self.api_key:
            raise ValueError(
                "MISTRAL_DOC_AI_KEY nicht gesetzt. "
                "Setze die Umgebungsvariable oder erstelle eine .env-Datei."
            )

    def _split_pdf(self, pdf_path: Path, max_pages: int = 30) -> list[bytes]:
        """Teilt ein PDF in Chunks a max_pages Seiten."""
        try:
            import fitz  # PyMuPDF < 1.24
        except ImportError:
            import pymupdf as fitz  # PyMuPDF >= 1.24

        doc = fitz.open(str(pdf_path))
        try:
            total = len(doc)

            if total <= max_pages:
                return [pdf_path.read_bytes()]

            chunks = []
            for start in range(0, total, max_pages):
                end = min(start + max_pages - 1, total - 1)
                chunk = fitz.open()
                try:
                    chunk.insert_pdf(doc, from_page=start, to_page=end)
                    chunks.append(chunk.tobytes())
                finally:
                    chunk.close()

            return chunks
        finally:
            doc.close()

    def _ocr_request(self, pdf_bytes: bytes) -> dict:
        """Sendet einen OCR-Request an die Mistral API."""
        import requests

        encoded = base64.b64encode(pdf_bytes).decode("utf-8")

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        payload = {
            "model": self.model,
            "document": {
                "type": "document_url",
                "document_url": f"data:application/pdf;base64,{encoded}",
            },
        }

        endpoint = self.endpoint.rstrip("/")
        if endpoint.endswith("/v1/ocr") or endpoint.endswith("/ocr"):
            url = endpoint
        else:
            url = f"{endpoint}/v1/ocr"

        response = requests.post(
            url,
            json=payload,
            headers=headers,
            timeout=MISTRAL_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        return response.json()

    def process_pdf(self, pdf_path: Path, output_dir: Path) -> dict:
        """Verarbeitet ein PDF ueber die Mistral Document AI API."""
        self._check_config()

        chunks = self._split_pdf(pdf_path, self.max_pages_per_request)
        print(f"  {len(chunks)} Chunk(s) fuer API-Request")

        all_pages = []
        page_offset = 0

        for chunk_idx, chunk_bytes in enumerate(chunks):
            if len(chunks) > 1:
                print(f"  Chunk {chunk_idx + 1}/{len(chunks)}...")

            start_time = time.time()
            result = self._ocr_request(chunk_bytes)
            elapsed = time.time() - start_time

            for page in result.get("pages", []):
                page_num = page_offset + page["index"] + 1
                markdown = page.get("markdown", "")

                all_pages.append({
                    "page": page_num,
                    "text": markdown,
                    "dimensions": page.get("dimensions"),
                })

                # Speichere Einzelseite
                page_file = output_dir / f"{pdf_path.stem}_p{page_num}.md"
                page_file.write_text(markdown, encoding="utf-8")

            pages_in_chunk = len(result.get("pages", []))
            page_offset += pages_in_chunk
            print(f"  {pages_in_chunk} Seiten in {elapsed:.1f}s")

        usage = result.get("usage_info", {})

        return {
            "doc_id": pdf_path.stem,
            "pages": len(all_pages),
            "results": all_pages,
            "engine": "mistral",
            "model": self.model,
            "usage": usage,
        }


class GeminiOCR:
    """Gemini-Vision OCR (Bild -> Markdown-Text).

    Opt-in Ausnahme-Engine (``-e gemini``): rendert die PDF-Seiten und transkribiert
    sie mit ``GEMINI_OCR_MODEL``. Output-Format identisch zu :class:`MistralOCR`
    (``{stem}_p{N}.md`` flach in ``mistral_results/``), damit der Rest der Pipeline
    (``load_ocr_text``) es unveraendert konsumiert. Die normale OCR bleibt Mistral.
    """

    PROMPT = (
        "Transkribiere den Text dieser Buchseite vollstaendig und originalgetreu als Markdown.\n"
        "Regeln:\n"
        "- Gib NUR den transkribierten Text aus -- keine Einleitung, keine Kommentare, keine Code-Fences.\n"
        "- Bewahre Originalsprache und -orthographie (meist Franzoesisch oder Deutsch), uebersetze nichts.\n"
        "- Erhalte Absatzstruktur, Ueberschriften (als Markdown-Headings), Fussnoten und Hervorhebungen.\n"
        "- Unleserliche Stellen mit [...] markieren, nichts erfinden.\n"
        "- Enthaelt die Seite keinen Text (leer oder reines Bild), gib eine leere Antwort zurueck."
    )

    def __init__(self):
        self.api_key = GEMINI_API_KEY or os.environ.get("GEMINI_API_KEY", "")
        self.model = GEMINI_OCR_MODEL

    def _check_config(self):
        if not self.api_key:
            raise ValueError(
                "GEMINI_API_KEY nicht gesetzt. Setze die Umgebungsvariable oder die .env-Datei."
            )

    @staticmethod
    def _strip_fences(text: str) -> str:
        """Entfernt versehentliche ```-Code-Fences um die Antwort."""
        if not text.startswith("```"):
            return text
        lines = text.split("\n")
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        return "\n".join(lines).strip()

    def process_pdf(self, pdf_path: Path, output_dir: Path) -> dict:
        self._check_config()
        import shutil

        from google import genai
        from google.genai import types
        from PIL import Image

        client = genai.Client(api_key=self.api_key)
        gen_config = types.GenerateContentConfig(
            thinking_config=types.ThinkingConfig(thinking_budget=0),
        )

        # Seiten rendern (temporaeres Bildverzeichnis, danach aufgeraeumt)
        img_dir = output_dir / f"_gemini_ocr_img_{pdf_path.stem}"
        image_paths = pdf_to_images(pdf_path, img_dir, dpi=200)
        print(f"  {len(image_paths)} Seiten gerendert (200 DPI)")

        all_pages = []
        empty_pages = []
        try:
            for idx, img_path in enumerate(image_paths, start=1):
                page_file = output_dir / f"{pdf_path.stem}_p{idx}.md"
                if page_file.exists():
                    print(f"  SKIP Seite {idx} (bereits vorhanden)")
                    all_pages.append({"page": idx, "text": page_file.read_text(encoding="utf-8")})
                    continue

                image = Image.open(img_path)
                text = ""
                finish = None
                t0 = time.time()
                for attempt in range(2):
                    response = client.models.generate_content(
                        model=self.model,
                        contents=[image, self.PROMPT],
                        config=gen_config,
                    )
                    text = self._strip_fences((response.text or "").strip())
                    try:
                        finish = response.candidates[0].finish_reason
                    except (AttributeError, IndexError, TypeError):
                        finish = None
                    if text or attempt == 1:
                        break

                page_file.write_text(text, encoding="utf-8")
                all_pages.append({"page": idx, "text": text})
                if not text:
                    empty_pages.append(idx)
                    print(f"  Seite {idx}/{len(image_paths)}: LEER (finish_reason={finish})")
                else:
                    print(f"  Seite {idx}/{len(image_paths)}: {len(text)} Zeichen in {time.time() - t0:.1f}s")
        finally:
            shutil.rmtree(img_dir, ignore_errors=True)

        if empty_pages:
            print(f"  WARNUNG: {len(empty_pages)} leere Seite(n): {empty_pages} "
                  f"(moeglich: Leerseite oder Gemini-Recitation-Filter)")

        return {
            "doc_id": pdf_path.stem,
            "pages": len(all_pages),
            "results": all_pages,
            "engine": "gemini",
            "model": self.model,
            "empty_pages": empty_pages,
        }


def process_pdf(pdf_path: Path, output_dir: Path, engine: str = "auto") -> dict:
    """
    Verarbeitet ein PDF mit der gewaehlten Engine.

    Args:
        pdf_path: Pfad zum PDF
        output_dir: Ausgabeverzeichnis
        engine: "mistral", "gemini", oder "auto"
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    if engine == "auto":
        # The Mistral endpoint answers 401; "mistral" stays selectable as the
        # reproducibility record of the delivered corpus.
        engine = "gemini"

    # Skip if first page already exists (resume-capable)
    first_page = output_dir / f"{pdf_path.stem}_p1.md"
    if first_page.exists():
        print(f"\nSKIP: {pdf_path.name} (bereits vorhanden)")
        # Count existing pages
        existing = list(output_dir.glob(f"{pdf_path.stem}_p*.md"))
        return {"doc_id": pdf_path.stem, "pages": len(existing), "engine": engine, "skipped": True}

    print(f"\nVerarbeite: {pdf_path.name} (Engine: {engine})")
    print("-" * 50)

    if engine == "mistral":
        ocr = MistralOCR()
        return ocr.process_pdf(pdf_path, output_dir)
    elif engine == "gemini":
        ocr = GeminiOCR()
        return ocr.process_pdf(pdf_path, output_dir)
    else:
        raise ValueError(f"Unbekannte Engine: {engine}")


def main():
    parser = argparse.ArgumentParser(description="OCR-Pipeline: Mistral + Gemini")
    parser.add_argument("--input", "-i", type=Path, help="PDF-Datei")
    parser.add_argument("--all", action="store_true", help="Alle PDFs verarbeiten")
    parser.add_argument(
        "--engine", "-e",
        choices=["auto", "mistral", "gemini"],
        default="auto",
        help="OCR-Engine (default: auto -> gemini). 'gemini' = Vision-OCR (Ausnahme, schreibt nach mistral_results/)"
    )
    parser.add_argument("--output", "-o", type=Path, help="Ausgabeverzeichnis")
    parser.add_argument("--check-gpu", action="store_true", help="Nur GPU pruefen")

    args = parser.parse_args()

    # GPU-Check
    if args.check_gpu:
        gpu = check_gpu()
        if gpu["available"]:
            print(f"GPU: {gpu['name']} ({gpu['vram_gb']:.1f} GB)")
        else:
            print("Keine GPU verfuegbar")
        return 0

    # Alle Engines (auto/mistral/gemini) schreiben die Basis-Textschicht nach
    # mistral_results/, wo load_ocr_text() sie als Basis findet. (Gemini-OCR ist der
    # Ausnahme-Ersatz fuer die Mistral-Basis-OCR -> gleiches Verzeichnis.)
    output_dir = args.output or MISTRAL_RESULTS_DIR

    # PDFs sammeln
    if args.input:
        pdfs = [args.input]
    elif args.all:
        pdfs = sorted(SCANS_DIR.glob("*.pdf"))
    else:
        parser.print_help()
        return 1

    if not pdfs:
        print(f"Keine PDFs gefunden in: {SCANS_DIR}")
        return 1

    print("=" * 60)
    print("OCR-Pipeline: Mistral Document AI + Gemini")
    print("=" * 60)
    # GPU-Status nur auf explizite Anfrage (--check-gpu); die Cloud-OCR braucht keine GPU.

    results = []
    for pdf_path in pdfs:
        if not pdf_path.exists():
            print(f"SKIP: {pdf_path} nicht gefunden")
            continue

        try:
            result = process_pdf(pdf_path, output_dir, engine=args.engine)
            results.append(result)
            print(f"  OK: {result['pages']} Seiten")
        except Exception as e:
            print(f"  FEHLER: {e}")
            results.append({"doc_id": pdf_path.stem, "error": str(e)})

    # Zusammenfassung
    print("\n" + "=" * 60)
    print("Zusammenfassung")
    print("=" * 60)

    successful = [r for r in results if "error" not in r]
    failed = [r for r in results if "error" in r]

    print(f"Erfolgreich: {len(successful)}/{len(results)}")
    if failed:
        print(f"Fehlgeschlagen: {[r['doc_id'] for r in failed]}")

    total_pages = sum(r.get("pages", 0) for r in successful)
    print(f"Seiten gesamt: {total_pages}")
    print(f"Ausgabe: {output_dir}")

    # Manifest speichern
    manifest_file = output_dir / "manifest.json"
    manifest_file.write_text(
        json.dumps(results, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
