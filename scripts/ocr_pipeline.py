#!/usr/bin/env python3
"""
OCR-Pipeline: Docling + DeepSeek-OCR-2

Kombiniert Docling (Layout-Analyse) mit DeepSeek-OCR-2 (Texterkennung)
für optimale Ergebnisse bei allen Dokumenttypen.

Usage:
    # Einzelnes PDF
    python scripts/ocr_pipeline.py --input data/scans/2310.pdf

    # Alle PDFs
    python scripts/ocr_pipeline.py --all

    # Nur DeepSeek (einspaltige Dokumente)
    python scripts/ocr_pipeline.py --input data/scans/2310.pdf --engine deepseek

    # Nur Docling (zweispaltige Dokumente)
    python scripts/ocr_pipeline.py --input data/scans/2530.pdf --engine docling
"""

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path
from datetime import datetime

# Projekt-Root
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Windows: Symlink-Warnung unterdrücken
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"


def check_gpu():
    """Prüft GPU-Verfügbarkeit."""
    try:
        import torch
        if torch.cuda.is_available():
            return {
                "available": True,
                "name": torch.cuda.get_device_name(0),
                "vram_gb": torch.cuda.get_device_properties(0).total_memory / 1024**3
            }
    except ImportError:
        pass
    return {"available": False}


def pdf_to_images(pdf_path: Path, output_dir: Path, dpi: int = 300) -> list[Path]:
    """Konvertiert PDF zu Bildern."""
    import pypdfium2 as pdfium

    output_dir.mkdir(parents=True, exist_ok=True)
    pdf = pdfium.PdfDocument(str(pdf_path))
    image_paths = []

    for i, page in enumerate(pdf):
        bitmap = page.render(scale=dpi / 72)
        pil_image = bitmap.to_pil()
        image_path = output_dir / f"{pdf_path.stem}_p{i+1:03d}.png"
        pil_image.save(str(image_path), "PNG")
        image_paths.append(image_path)

    pdf.close()
    return image_paths


class DeepSeekOCR:
    """DeepSeek-OCR-2 Engine."""

    def __init__(self):
        self.model = None
        self.tokenizer = None

    def load(self):
        """Lädt das Modell."""
        if self.model is not None:
            return

        from transformers import AutoModel, AutoTokenizer
        import torch

        print("Lade DeepSeek-OCR-2...")
        model_name = "deepseek-ai/DeepSeek-OCR-2"

        self.tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
        self.model = AutoModel.from_pretrained(
            model_name,
            trust_remote_code=True,
            use_safetensors=True
        )
        self.model = self.model.eval().cuda().to(torch.bfloat16)
        print("DeepSeek-OCR-2 geladen.")

    def process_image(self, image_path: Path, output_dir: Path) -> str:
        """Verarbeitet ein Bild."""
        self.load()

        prompt = "<image>\n<|grounding|>Convert the document to markdown."

        self.model.infer(
            self.tokenizer,
            prompt=prompt,
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


class DoclingOCR:
    """Docling Engine (mit optionalem DeepSeek-Backend)."""

    def __init__(self, use_deepseek: bool = False):
        self.use_deepseek = use_deepseek
        self.converter = None

    def load(self):
        """Lädt den Converter."""
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

        # Speichere Gesamtdokument
        output_file = output_dir / f"{pdf_path.stem}_docling.md"
        output_file.write_text(markdown, encoding="utf-8")

        # Zähle Seiten (approximativ über Seitenumbrüche)
        page_count = markdown.count("---") + 1

        return {
            "doc_id": pdf_path.stem,
            "pages": page_count,
            "markdown": markdown,
            "engine": "docling"
        }


def process_pdf(pdf_path: Path, output_dir: Path, engine: str = "auto") -> dict:
    """
    Verarbeitet ein PDF mit der gewählten Engine.

    Args:
        pdf_path: Pfad zum PDF
        output_dir: Ausgabeverzeichnis
        engine: "deepseek", "docling", oder "auto"
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    # Auto-Auswahl basierend auf Dokumenttyp
    if engine == "auto":
        # Typ B (zweispaltig) → Docling
        two_column_docs = ["2530", "890", "3040"]
        if pdf_path.stem in two_column_docs:
            engine = "docling"
        else:
            engine = "deepseek"

    print(f"\nVerarbeite: {pdf_path.name} (Engine: {engine})")
    print("-" * 50)

    if engine == "deepseek":
        ocr = DeepSeekOCR()
        return ocr.process_pdf(pdf_path, output_dir)
    elif engine == "docling":
        ocr = DoclingOCR()
        return ocr.process_pdf(pdf_path, output_dir)
    else:
        raise ValueError(f"Unbekannte Engine: {engine}")


def main():
    parser = argparse.ArgumentParser(description="OCR-Pipeline: Docling + DeepSeek")
    parser.add_argument("--input", "-i", type=Path, help="PDF-Datei")
    parser.add_argument("--all", action="store_true", help="Alle PDFs verarbeiten")
    parser.add_argument(
        "--engine", "-e",
        choices=["auto", "deepseek", "docling"],
        default="auto",
        help="OCR-Engine (default: auto)"
    )
    parser.add_argument("--output", "-o", type=Path, help="Ausgabeverzeichnis")
    parser.add_argument("--check-gpu", action="store_true", help="Nur GPU prüfen")

    args = parser.parse_args()

    # GPU-Check
    if args.check_gpu:
        gpu = check_gpu()
        if gpu["available"]:
            print(f"GPU: {gpu['name']} ({gpu['vram_gb']:.1f} GB)")
        else:
            print("Keine GPU verfügbar")
        return 0

    # Pfade
    scans_dir = PROJECT_ROOT / "data" / "scans"
    output_dir = args.output or PROJECT_ROOT / "output" / "ocr_results"

    # PDFs sammeln
    if args.input:
        pdfs = [args.input]
    elif args.all:
        pdfs = sorted(scans_dir.glob("*.pdf"))
    else:
        parser.print_help()
        return 1

    if not pdfs:
        print(f"Keine PDFs gefunden in: {scans_dir}")
        return 1

    # Verarbeiten
    print("=" * 60)
    print("OCR-Pipeline: Docling + DeepSeek-OCR-2")
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
