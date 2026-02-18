#!/usr/bin/env python3
"""
Layout-Extraktion mit Docling (ohne OCR).

Extrahiert Textregionen und deren Koordinaten aus PDFs.
Die eigentliche OCR erfolgt separat mit DeepSeek-OCR-2.

Usage:
    python scripts/extract_layout.py --input data/scans/2530.pdf
    python scripts/extract_layout.py --input data/scans/2530.pdf --visualize
"""

import argparse
import json
import sys
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional

from scripts.config import LAYOUT_DIR


@dataclass
class TextRegion:
    """Eine Textregion mit Koordinaten."""
    page: int
    region_type: str  # text, header, list, table
    bbox_left: float
    bbox_top: float
    bbox_right: float
    bbox_bottom: float
    reading_order: int
    column: Optional[int] = None  # 0=left, 1=right für zweispaltig


@dataclass
class PageLayout:
    """Layout einer Seite."""
    page_num: int
    width: float
    height: float
    regions: list[TextRegion]
    is_two_column: bool = False


def extract_layout(pdf_path: Path) -> list[PageLayout]:
    """
    Extrahiert Layout-Informationen aus einem PDF.

    Returns:
        Liste von PageLayout-Objekten
    """
    from docling.document_converter import DocumentConverter, PdfFormatOption
    from docling.datamodel.pipeline_options import PdfPipelineOptions
    from docling.datamodel.base_models import InputFormat

    # Pipeline ohne OCR - nur Layout
    pipeline_options = PdfPipelineOptions()
    pipeline_options.do_ocr = False

    converter = DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
        }
    )

    result = converter.convert(str(pdf_path))
    doc = result.document

    # Sammle Regionen pro Seite
    pages_regions: dict[int, list[TextRegion]] = {}

    for idx, text_item in enumerate(doc.texts):
        if not hasattr(text_item, 'prov') or not text_item.prov:
            continue

        for prov in text_item.prov:
            page_num = prov.page_no
            bbox = prov.bbox

            # Region-Typ bestimmen
            item_type = type(text_item).__name__
            if 'Header' in item_type:
                region_type = 'header'
            elif 'List' in item_type:
                region_type = 'list'
            elif 'Table' in item_type:
                region_type = 'table'
            else:
                region_type = 'text'

            region = TextRegion(
                page=page_num,
                region_type=region_type,
                bbox_left=bbox.l,
                bbox_top=bbox.t,
                bbox_right=bbox.r,
                bbox_bottom=bbox.b,
                reading_order=idx,
            )

            if page_num not in pages_regions:
                pages_regions[page_num] = []
            pages_regions[page_num].append(region)

    # PageLayouts erstellen
    layouts = []
    for page_num, page in doc.pages.items():
        regions = pages_regions.get(page_num, [])

        # Spalten-Erkennung: Ist die Seite zweispaltig?
        page_width = page.size.width
        mid_x = page_width / 2

        left_regions = [r for r in regions if r.bbox_right < mid_x + 50]
        right_regions = [r for r in regions if r.bbox_left > mid_x - 50]

        is_two_column = len(left_regions) > 2 and len(right_regions) > 2

        # Spalten-Zuordnung
        if is_two_column:
            for region in regions:
                center_x = (region.bbox_left + region.bbox_right) / 2
                region.column = 0 if center_x < mid_x else 1

        layout = PageLayout(
            page_num=page_num,
            width=page.size.width,
            height=page.size.height,
            regions=regions,
            is_two_column=is_two_column,
        )
        layouts.append(layout)

    return layouts


def visualize_layout(pdf_path: Path, layouts: list[PageLayout], output_dir: Path):
    """
    Erstellt Visualisierung der erkannten Layout-Regionen.
    """
    import pypdfium2 as pdfium
    from PIL import Image, ImageDraw

    output_dir.mkdir(parents=True, exist_ok=True)

    pdf = pdfium.PdfDocument(str(pdf_path))

    for layout in layouts:
        page_idx = layout.page_num - 1
        if page_idx >= len(pdf):
            continue

        page = pdf[page_idx]
        bitmap = page.render(scale=2)  # 144 DPI
        img = bitmap.to_pil()
        draw = ImageDraw.Draw(img)

        # Skalierungsfaktor
        scale = img.width / layout.width

        # Regionen zeichnen
        colors = {
            'header': 'red',
            'text': 'blue',
            'list': 'green',
            'table': 'orange',
        }

        for region in layout.regions:
            # Koordinaten von bottom-left zu top-left konvertieren
            x1 = region.bbox_left * scale
            y1 = (layout.height - region.bbox_top) * scale
            x2 = region.bbox_right * scale
            y2 = (layout.height - region.bbox_bottom) * scale

            color = colors.get(region.region_type, 'gray')
            draw.rectangle([x1, y1, x2, y2], outline=color, width=2)

            # Spalten-Markierung
            if region.column is not None:
                label = f"C{region.column}"
                draw.text((x1 + 2, y1 + 2), label, fill=color)

        # Mittellinie bei zweispaltigen Seiten
        if layout.is_two_column:
            mid_x = img.width / 2
            draw.line([(mid_x, 0), (mid_x, img.height)], fill='purple', width=1)

        output_file = output_dir / f"{pdf_path.stem}_layout_p{layout.page_num}.png"
        img.save(str(output_file))
        print(f"  Visualisierung: {output_file}")

    pdf.close()


def main():
    parser = argparse.ArgumentParser(description="Layout-Extraktion mit Docling")
    parser.add_argument("--input", "-i", type=Path, required=True, help="PDF-Datei")
    parser.add_argument("--output", "-o", type=Path, help="Ausgabeverzeichnis")
    parser.add_argument("--visualize", "-v", action="store_true", help="Visualisierung erstellen")

    args = parser.parse_args()

    if not args.input.exists():
        print(f"Datei nicht gefunden: {args.input}")
        return 1

    output_dir = args.output or LAYOUT_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Layout-Extraktion: {args.input.name}")
    print("-" * 50)

    layouts = extract_layout(args.input)

    # Ergebnis ausgeben
    for layout in layouts:
        col_info = " (zweispaltig)" if layout.is_two_column else ""
        print(f"Seite {layout.page_num}: {len(layout.regions)} Regionen{col_info}")

        by_type = {}
        for r in layout.regions:
            by_type[r.region_type] = by_type.get(r.region_type, 0) + 1
        for t, count in by_type.items():
            print(f"  - {t}: {count}")

    # JSON speichern
    json_file = output_dir / f"{args.input.stem}_layout.json"
    json_data = [
        {
            "page_num": l.page_num,
            "width": l.width,
            "height": l.height,
            "is_two_column": l.is_two_column,
            "regions": [asdict(r) for r in l.regions]
        }
        for l in layouts
    ]
    json_file.write_text(json.dumps(json_data, indent=2), encoding="utf-8")
    print(f"\nLayout gespeichert: {json_file}")

    # Visualisierung
    if args.visualize:
        print("\nErstelle Visualisierung...")
        visualize_layout(args.input, layouts, output_dir)

    return 0


if __name__ == "__main__":
    sys.exit(main())
