"""
PAGE-XML Generator: Layout-JSON + OCR-Markdown -> PAGE-XML (2013-07-15).

Erzeugt PAGE-XML nach Schema 2013-07-15 (Transkribus-Standard) mit
METS-Manifest. Nutzt Layout-Regionen fuer Strukturerkennung und
OCR-Markdown fuer den Textinhalt.

Aufruf:
    python -m scripts.layout.page_xml_generator                 # alle Docs
    python -m scripts.layout.page_xml_generator --doc 2310      # einzelnes Dok
    python -m scripts.layout.page_xml_generator --doc 2310 --page 2
    python -m scripts.layout.page_xml_generator --force         # ueberschreiben
    python -m scripts.layout.page_xml_generator --sample        # Pilot-Docs
"""

import argparse
import json
import re
import sys
from datetime import UTC, datetime
from pathlib import Path

from lxml import etree

# Projekt-Imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from scripts.config import (
    IMAGES_DIR,
    LAYOUT_DIR,
    PAGE_XML_DIR,
    ZBZ_TO_PAGE_TYPE,
)
from scripts.core.loaders import discover_layout_documents, discover_layout_pages

# PAGE-XML Namespace (2013-07-15)
PAGE_NS = "http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15"
XSI_NS = "http://www.w3.org/2001/XMLSchema-instance"
SCHEMA_LOC = PAGE_NS + " " + PAGE_NS + "/pagecontent.xsd"

# Sample-Docs (gleich wie gemini_ocr_correct.py)
SAMPLE_DOCS = ["2310", "1180", "890", "90", "40"]


# ---------------------------------------------------------------------------
# Daten laden
# ---------------------------------------------------------------------------

def load_layout_for_page(doc_id, page_padded):
    """Layout laden: Gemini-korrigiert bevorzugt, Fallback Docling.

    Returns: (regions, image_width, image_height, source)
    """
    base = LAYOUT_DIR / doc_id

    # Image-Dimensionen immer aus Docling (Gemini hat keine)
    docling_path = base / f"{doc_id}_p{page_padded}_layout.json"
    img_w, img_h = None, None
    docling_data = None
    if docling_path.exists():
        docling_data = json.loads(docling_path.read_text(encoding="utf-8"))
        img_w = docling_data.get("image_width")
        img_h = docling_data.get("image_height")

    # Gemini-korrigiertes Layout bevorzugen
    gemini_path = base / f"{doc_id}_p{page_padded}_layout_gemini.json"
    if gemini_path.exists():
        gemini_data = json.loads(gemini_path.read_text(encoding="utf-8"))
        regions = gemini_data.get("regions", [])
        if regions:
            # Fallback: Dimensionen aus Bild lesen
            if img_w is None:
                img_w, img_h = _get_image_dimensions(doc_id, page_padded)
            return regions, img_w, img_h, "gemini"

    # Fallback: Docling-Original
    if docling_data and docling_data.get("regions"):
        return docling_data["regions"], img_w, img_h, "docling"

    return [], img_w, img_h, None


def _get_image_dimensions(doc_id, page_padded):
    """Bild-Dimensionen aus der tatsaechlichen Bilddatei lesen."""
    img_path = IMAGES_DIR / doc_id / f"{doc_id}_p{page_padded}.png"
    if img_path.exists():
        from PIL import Image
        with Image.open(img_path) as img:
            return img.size
    return None, None


def load_ocr_text_for_page(doc_id, page_num):
    """Besten OCR-Text laden: kuratiert > Gemini B > Gemini A > LLM C > Mistral.

    Delegiert an die kanonische Kette (loaders.OCR_SOURCES), damit kuratiertes OCR
    auch ins PAGE-XML fliesst und die Reihenfolge nicht an zwei Stellen driftet.

    Returns: (text, source_name) oder (None, None)
    """
    from scripts.core.loaders import load_ocr_text_with_source
    return load_ocr_text_with_source(doc_id, page_num)


# ---------------------------------------------------------------------------
# OCR-Text <-> Region Matching
# ---------------------------------------------------------------------------

def split_paragraphs(ocr_text):
    """Teilt OCR-Markdown in Absaetze (getrennt durch Leerzeilen)."""
    blocks = re.split(r'\n\s*\n', ocr_text.strip())
    return [b.strip() for b in blocks if b.strip()]


def match_ocr_to_regions(ocr_text, regions):
    """Matched OCR-Absaetze zu Layout-Regionen nach Position.

    Returns: Liste von (region, matched_text) Tupeln.
    Regionen mit _filter/_skip werden uebersprungen.
    """
    paragraphs = split_paragraphs(ocr_text) if ocr_text else []

    # Relevante Regionen filtern
    relevant = [
        r for r in regions
        if r.get("zbz_tag") not in ("_filter", "_skip", None)
        and r.get("bbox")
    ]
    relevant.sort(key=lambda r: r["bbox"]["y_pct"])

    result = []
    if len(paragraphs) == len(relevant):
        for para, region in zip(paragraphs, relevant):
            result.append((region, para))
    else:
        for i, region in enumerate(relevant):
            text = paragraphs[i] if i < len(paragraphs) else ""
            result.append((region, text))
        # Ueberschuessige Absaetze: an letztes Region anhaengen
        if len(paragraphs) > len(relevant) and result:
            extra = paragraphs[len(relevant):]
            last_region, last_text = result[-1]
            result[-1] = (last_region, last_text + "\n\n" + "\n\n".join(extra))

    return result


# ---------------------------------------------------------------------------
# Koordinaten-Konvertierung
# ---------------------------------------------------------------------------

def bbox_to_coords(bbox, img_w, img_h):
    """Prozent-BBox -> PAGE-XML Polygon-String (4 Eckpunkte, Uhrzeigersinn)."""
    x1 = int(max(0, bbox["x_pct"]) / 100 * img_w)
    y1 = int(max(0, bbox["y_pct"]) / 100 * img_h)
    x2 = int(min(100, bbox["x_pct"] + bbox["w_pct"]) / 100 * img_w)
    y2 = int(min(100, bbox["y_pct"] + bbox["h_pct"]) / 100 * img_h)
    return f"{x1},{y1} {x2},{y1} {x2},{y2} {x1},{y2}"


# ---------------------------------------------------------------------------
# PAGE-XML Generierung
# ---------------------------------------------------------------------------

def generate_page_xml(doc_id, page_num, matched_regions, img_w, img_h,
                      layout_source="docling"):
    """Erzeugt PAGE-XML fuer eine Seite.

    Args:
        doc_id: Dokument-ID
        page_num: Seitennummer (1-basiert)
        matched_regions: Liste von (region_dict, ocr_text) Tupeln
        img_w: Bildbreite in Pixel
        img_h: Bildhoehe in Pixel
        layout_source: "docling" oder "gemini"

    Returns: lxml.etree.Element (PcGts Root)
    """
    page_padded = str(page_num).zfill(3)

    nsmap = {None: PAGE_NS, "xsi": XSI_NS}
    root = etree.Element("{%s}PcGts" % PAGE_NS, nsmap=nsmap)
    root.set("{%s}schemaLocation" % XSI_NS, SCHEMA_LOC)

    # Metadata
    metadata = etree.SubElement(root, "{%s}Metadata" % PAGE_NS)
    creator = etree.SubElement(metadata, "{%s}Creator" % PAGE_NS)
    creator.text = f"zbz-ocr-tei:page_xml_generator:layout={layout_source}"
    created = etree.SubElement(metadata, "{%s}Created" % PAGE_NS)
    created.text = datetime.now(UTC).isoformat()
    last_change = etree.SubElement(metadata, "{%s}LastChange" % PAGE_NS)
    last_change.text = datetime.now(UTC).isoformat()

    # Page
    page = etree.SubElement(root, "{%s}Page" % PAGE_NS)
    page.set("imageFilename", f"{doc_id}_p{page_padded}.png")
    page.set("imageWidth", str(img_w or 0))
    page.set("imageHeight", str(img_h or 0))

    if not matched_regions:
        return root

    # ReadingOrder
    reading_order = etree.SubElement(page, "{%s}ReadingOrder" % PAGE_NS)
    ordered_group = etree.SubElement(
        reading_order, "{%s}OrderedGroup" % PAGE_NS
    )
    ordered_group.set("id", "ro_1")
    ordered_group.set("caption", "Regions reading order")

    for idx, (region, text) in enumerate(matched_regions):
        region_id = f"r_{idx + 1}"

        ref = etree.SubElement(
            ordered_group, "{%s}RegionRefIndexed" % PAGE_NS
        )
        ref.set("index", str(idx))
        ref.set("regionRef", region_id)

    # TextRegions
    for idx, (region, text) in enumerate(matched_regions):
        region_id = f"r_{idx + 1}"
        zbz_tag = region.get("zbz_tag", "zb_paragraph")
        page_type = ZBZ_TO_PAGE_TYPE.get(zbz_tag, "paragraph")

        text_region = etree.SubElement(page, "{%s}TextRegion" % PAGE_NS)
        text_region.set("id", region_id)
        text_region.set(
            "custom",
            f"readingOrder {{index:{idx};}} structure {{type:{page_type};}}"
        )

        # Region Coords
        bbox = region.get("bbox")
        if bbox and img_w and img_h:
            coords = etree.SubElement(
                text_region, "{%s}Coords" % PAGE_NS
            )
            coords.set("points", bbox_to_coords(bbox, img_w, img_h))

        # TextLine (eine pro Region)
        if text:
            # Markdown-Headings entfernen fuer reinen Text
            clean_text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
            clean_text = clean_text.strip()

            text_line = etree.SubElement(
                text_region, "{%s}TextLine" % PAGE_NS
            )
            text_line.set("id", f"{region_id}_tl_1")
            text_line.set("custom", "readingOrder {index:0;}")

            # TextLine Coords = gleich wie Region
            if bbox and img_w and img_h:
                tl_coords = etree.SubElement(
                    text_line, "{%s}Coords" % PAGE_NS
                )
                tl_coords.set(
                    "points", bbox_to_coords(bbox, img_w, img_h)
                )

            tl_te = etree.SubElement(
                text_line, "{%s}TextEquiv" % PAGE_NS
            )
            tl_unicode = etree.SubElement(tl_te, "{%s}Unicode" % PAGE_NS)
            tl_unicode.text = clean_text

        # Region-Level TextEquiv (leer, Transkribus-Konvention)
        region_te = etree.SubElement(
            text_region, "{%s}TextEquiv" % PAGE_NS
        )
        region_unicode = etree.SubElement(
            region_te, "{%s}Unicode" % PAGE_NS
        )
        region_unicode.text = ""

    return root


# ---------------------------------------------------------------------------
# Verarbeitung
# ---------------------------------------------------------------------------

def process_page(doc_id, page_num, force=False):
    """Verarbeitet eine einzelne Seite und schreibt PAGE-XML.

    Returns: Path oder None
    """
    page_padded = str(page_num).zfill(3)

    out_dir = PAGE_XML_DIR / doc_id / "page"
    out_path = out_dir / f"{doc_id}_p{page_padded}.xml"

    if out_path.exists() and not force:
        return out_path

    # Layout laden
    regions, img_w, img_h, layout_source = load_layout_for_page(
        doc_id, page_padded
    )
    if not regions:
        return None

    # Dimensionen-Fallback
    if img_w is None:
        img_w, img_h = _get_image_dimensions(doc_id, page_padded)
    if img_w is None:
        return None

    # OCR-Text laden
    ocr_text, ocr_source = load_ocr_text_for_page(doc_id, page_num)

    # Matching
    matched = match_ocr_to_regions(ocr_text, regions)

    # PAGE-XML generieren
    root = generate_page_xml(
        doc_id, page_num, matched, img_w, img_h, layout_source or "unknown"
    )

    # Schreiben
    out_dir.mkdir(parents=True, exist_ok=True)
    tree = etree.ElementTree(root)
    tree.write(
        str(out_path),
        xml_declaration=True,
        encoding="UTF-8",
        pretty_print=True,
        standalone=True,
    )

    return out_path


def process_document(doc_id, force=False):
    """Verarbeitet alle Seiten eines Dokuments + METS. Returns: Anzahl generierter Dateien."""
    pages = discover_layout_pages(doc_id)
    generated = 0
    for page_num in pages:
        result = process_page(doc_id, page_num, force)
        if result:
            generated += 1

    # METS generieren wenn mindestens eine Seite vorhanden
    if generated > 0:
        from scripts.layout.mets_generator import write_mets
        write_mets(doc_id)

    return generated


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="PAGE-XML Generator: Layout-JSON + OCR -> PAGE-XML (2013-07-15)"
    )
    parser.add_argument("--doc", help="Einzelnes Dokument (z.B. 2310)")
    parser.add_argument("--page", type=int, help="Einzelne Seite (nur mit --doc)")
    parser.add_argument("--force", action="store_true", help="Existierende ueberschreiben")
    parser.add_argument("--sample", action="store_true", help="Nur Sample-Docs")
    args = parser.parse_args()

    if args.doc and args.page:
        result = process_page(args.doc, args.page, args.force)
        if result:
            print(f"  Generiert: {result}")
        else:
            print(f"  Keine Daten fuer {args.doc} Seite {args.page}")
    elif args.doc:
        print(f"Generiere PAGE-XML fuer Dokument {args.doc}...")
        count = process_document(args.doc, args.force)
        print(f"  {count} Seiten generiert")
    else:
        if args.sample:
            doc_ids = SAMPLE_DOCS
        else:
            doc_ids = discover_layout_documents()

        print(f"Generiere PAGE-XML fuer {len(doc_ids)} Dokumente...")
        total = 0
        for doc_id in doc_ids:
            count = process_document(doc_id, args.force)
            total += count
            if count > 0:
                print(f"  {doc_id}: {count} Seiten")

        print(f"\nGesamt: {total} PAGE-XML Dateien in {PAGE_XML_DIR}")


if __name__ == "__main__":
    main()
