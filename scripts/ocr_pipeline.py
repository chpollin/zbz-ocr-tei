#!/usr/bin/env python3
"""
OCR-Pipeline: DeepSeek + Mistral Document AI + Docling

Unterstuetzt mehrere OCR-Engines fuer verschiedene Dokumenttypen.

Usage:
    # Einzelnes PDF
    python scripts/ocr_pipeline.py --input data/scans/2310.pdf

    # Alle PDFs
    python scripts/ocr_pipeline.py --all

    # Bestimmte Engine
    python scripts/ocr_pipeline.py --input data/scans/2310.pdf --engine deepseek
    python scripts/ocr_pipeline.py --input data/scans/2310.pdf --engine mistral
    python scripts/ocr_pipeline.py --input data/scans/2530.pdf --engine docling
"""

import argparse
import base64
import json
import os
import sys
import tempfile
import time
from pathlib import Path

from scripts.config import (
    PROJECT_ROOT, SCANS_DIR, OCR_RESULTS_DIR, MISTRAL_RESULTS_DIR,
    DEEPSEEK_MODEL, DEEPSEEK_PROMPT, MISTRAL_MODEL,
    MISTRAL_MAX_PAGES_PER_REQUEST, MISTRAL_TIMEOUT_SECONDS,
    TWO_COLUMN_DOCS,
)
from scripts.utils import check_gpu, load_env, pdf_to_images

# Windows: Symlink-Warnung unterdruecken
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"


class DeepSeekOCR:
    """DeepSeek-OCR-2 Engine."""

    def __init__(self):
        self.model = None
        self.tokenizer = None

    def load(self):
        """Laedt das Modell."""
        if self.model is not None:
            return

        from scripts.utils import load_deepseek_model
        self.model, self.tokenizer = load_deepseek_model()

    def process_image(self, image_path: Path, output_dir: Path) -> str:
        """Verarbeitet ein Bild."""
        self.load()

        self.model.infer(
            self.tokenizer,
            prompt=DEEPSEEK_PROMPT,
            image_file=str(image_path),
            output_path=str(output_dir),
            base_size=1024,
            image_size=768,
            crop_mode=True,
            save_results=True
        )

        result_file = output_dir / "result.mmd"
        if result_file.exists():
            return result_file.read_text(encoding="utf-8")
        return ""

    def process_pdf(self, pdf_path: Path, output_dir: Path) -> dict:
        """Verarbeitet ein PDF."""
        temp_dir = Path(tempfile.mkdtemp())
        images = pdf_to_images(pdf_path, temp_dir)

        results = []
        for i, image_path in enumerate(images):
            print(f"  Seite {i+1}/{len(images)}...")
            text = self.process_image(image_path, temp_dir)
            results.append({"page": i + 1, "text": text})

            # Speichere Einzelseite
            page_file = output_dir / f"{pdf_path.stem}_p{i+1}.md"
            page_file.write_text(text, encoding="utf-8")

        return {
            "doc_id": pdf_path.stem,
            "pages": len(images),
            "results": results,
            "engine": "deepseek"
        }


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


class DoclingOCR:
    """Docling Engine (mit optionalem DeepSeek-Backend)."""

    def __init__(self, use_deepseek: bool = False):
        self.use_deepseek = use_deepseek
        self.converter = None

    def load(self):
        """Laedt den Converter."""
        if self.converter is not None:
            return

        try:
            from docling.document_converter import DocumentConverter
            print("Lade Docling...")
            self.converter = DocumentConverter()
            print("Docling geladen.")
        except ImportError as e:
            raise ImportError(f"Docling nicht installiert: {e}\nInstalliere mit: pip install docling")

    def process_pdf(self, pdf_path: Path, output_dir: Path) -> dict:
        """Verarbeitet ein PDF."""
        self.load()

        print(f"  Docling konvertiert {pdf_path.name}...")
        result = self.converter.convert(str(pdf_path))
        markdown = result.document.export_to_markdown()

        output_file = output_dir / f"{pdf_path.stem}_docling.md"
        output_file.write_text(markdown, encoding="utf-8")

        page_count = markdown.count("---") + 1

        return {
            "doc_id": pdf_path.stem,
            "pages": page_count,
            "markdown": markdown,
            "engine": "docling"
        }


def process_pdf(pdf_path: Path, output_dir: Path, engine: str = "auto") -> dict:
    """
    Verarbeitet ein PDF mit der gewaehlten Engine.

    Args:
        pdf_path: Pfad zum PDF
        output_dir: Ausgabeverzeichnis
        engine: "deepseek", "mistral", "docling", oder "auto"
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    if engine == "auto":
        if pdf_path.stem in TWO_COLUMN_DOCS:
            engine = "docling"
        elif os.environ.get("MISTRAL_DOC_AI_KEY"):
            engine = "mistral"
        else:
            engine = "deepseek"

    # Skip if first page already exists (resume-capable)
    first_page = output_dir / f"{pdf_path.stem}_p1.md"
    if first_page.exists():
        print(f"\nSKIP: {pdf_path.name} (bereits vorhanden)")
        # Count existing pages
        existing = list(output_dir.glob(f"{pdf_path.stem}_p*.md"))
        return {"doc_id": pdf_path.stem, "pages": len(existing), "engine": engine, "skipped": True}

    print(f"\nVerarbeite: {pdf_path.name} (Engine: {engine})")
    print("-" * 50)

    if engine == "deepseek":
        ocr = DeepSeekOCR()
        return ocr.process_pdf(pdf_path, output_dir)
    elif engine == "mistral":
        ocr = MistralOCR()
        return ocr.process_pdf(pdf_path, output_dir)
    elif engine == "docling":
        ocr = DoclingOCR()
        return ocr.process_pdf(pdf_path, output_dir)
    else:
        raise ValueError(f"Unbekannte Engine: {engine}")


def main():
    parser = argparse.ArgumentParser(description="OCR-Pipeline: DeepSeek + Mistral + Docling")
    parser.add_argument("--input", "-i", type=Path, help="PDF-Datei")
    parser.add_argument("--all", action="store_true", help="Alle PDFs verarbeiten")
    parser.add_argument(
        "--engine", "-e",
        choices=["auto", "deepseek", "mistral", "docling"],
        default="auto",
        help="OCR-Engine (default: auto)"
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

    # .env laden
    load_env()

    # Pfade: Engine-basiert (Mistral -> mistral_results/, DeepSeek -> ocr_results/)
    if args.output:
        output_dir = args.output
    elif args.engine == "mistral":
        output_dir = MISTRAL_RESULTS_DIR
    else:
        output_dir = OCR_RESULTS_DIR

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
    print("OCR-Pipeline: DeepSeek + Mistral Document AI + Docling")
    print("=" * 60)

    gpu = check_gpu()
    if gpu["available"]:
        print(f"GPU: {gpu['name']} ({gpu['vram_gb']:.1f} GB)")
    else:
        print("WARNUNG: Keine GPU - DeepSeek wird langsam sein")

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
