#!/usr/bin/env python3
"""
PDF zu Seitenbildern extrahieren.

Extrahiert alle Seiten aus PDFs als PNG-Bilder für:
- Digitale Edition (Faksimile)
- QS-Viewer (Bild neben Transkription)
- OCR-Pipeline (Bilder statt PDF)
"""

import json
import sys
from pathlib import Path

# Repo-Root auf sys.path, damit der Direktaufruf (python scripts/edition/extract_pages.py)
# das scripts-Paket findet -- nicht nur die Modul-Form (python -m scripts.edition.extract_pages).
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from scripts.config import IMAGES_DIR, SCANS_DIR, WEB_DPI
from scripts.utils import page_image_name


def extract_pdf_pages(pdf_path: Path, output_dir: Path, dpi: int = 150) -> dict:
    """
    Extrahiert alle Seiten eines PDFs als PNG.

    Args:
        pdf_path: Pfad zur PDF-Datei
        output_dir: Zielverzeichnis für Bilder
        dpi: Auflösung (150 für Web, 300 für OCR)

    Returns:
        Metadaten-Dict mit Seitenzahl und Dateipfaden
    """
    import pypdfium2 as pdfium

    doc_id = pdf_path.stem
    doc_output_dir = output_dir / doc_id
    doc_output_dir.mkdir(parents=True, exist_ok=True)

    pdf = pdfium.PdfDocument(str(pdf_path))
    page_count = len(pdf)

    pages = []
    for i in range(page_count):
        page = pdf[i]
        # Render bei angegebener DPI
        bitmap = page.render(scale=dpi/72)
        pil_image = bitmap.to_pil()

        # Dateiname: {doc_id}_p{page:03d}.png (zentral in scripts.utils.page_image_name)
        filename = page_image_name(doc_id, i + 1)
        image_path = doc_output_dir / filename
        pil_image.save(str(image_path), "PNG", optimize=True)

        pages.append({
            "page": i + 1,
            "filename": filename,
            "width": pil_image.width,
            "height": pil_image.height
        })

        print(f"  Seite {i+1}/{page_count}: {filename}")

    pdf.close()

    return {
        "doc_id": doc_id,
        "source_pdf": pdf_path.name,
        "page_count": page_count,
        "dpi": dpi,
        "pages": pages
    }


def extract_all_pdfs(scans_dir: Path, output_dir: Path, dpi: int = 150) -> list:
    """Extrahiert alle PDFs im Verzeichnis."""

    pdfs = sorted(scans_dir.glob("*.pdf"))
    if not pdfs:
        print(f"Keine PDFs gefunden in: {scans_dir}")
        return []

    print(f"Gefunden: {len(pdfs)} PDFs")
    print(f"Ausgabe: {output_dir}")
    print(f"DPI: {dpi}")
    print("=" * 50)

    results = []
    for pdf_path in pdfs:
        print(f"\n{pdf_path.name}:")
        try:
            metadata = extract_pdf_pages(pdf_path, output_dir, dpi)
            results.append(metadata)
        except Exception as e:
            print(f"  FEHLER: {e}")
            results.append({
                "doc_id": pdf_path.stem,
                "error": str(e)
            })

    return results


def main():
    import argparse

    parser = argparse.ArgumentParser(description="PDF zu Seitenbildern extrahieren")
    parser.add_argument("--dpi", type=int, default=WEB_DPI,
                        help="Aufloesung (150=Web, 300=OCR)")
    parser.add_argument("--pdf", type=str, default=None,
                        help="Einzelnes PDF extrahieren")
    args = parser.parse_args()

    output_dir = IMAGES_DIR

    if args.pdf:
        # Einzelnes PDF
        pdf_path = SCANS_DIR / args.pdf
        if not pdf_path.exists():
            print(f"PDF nicht gefunden: {pdf_path}")
            sys.exit(1)

        print(f"Extrahiere: {pdf_path.name}")
        metadata = extract_pdf_pages(pdf_path, output_dir, args.dpi)
        results = [metadata]
    else:
        # Alle PDFs
        results = extract_all_pdfs(SCANS_DIR, output_dir, args.dpi)

    # Metadaten speichern
    metadata_file = output_dir / "manifest.json"
    metadata_file.write_text(
        json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")

    print("\n" + "=" * 50)
    print(f"Manifest gespeichert: {metadata_file}")

    # Zusammenfassung
    total_pages = sum(r.get("page_count", 0) for r in results if "error" not in r)
    errors = sum(1 for r in results if "error" in r)
    print(f"Gesamt: {total_pages} Seiten aus {len(results) - errors} PDFs")
    if errors:
        print(f"Fehler: {errors} PDFs")


if __name__ == "__main__":
    main()
