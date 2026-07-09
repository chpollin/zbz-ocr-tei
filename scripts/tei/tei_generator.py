"""
TEI-XML Generator: Layout-JSON + OCR-Markdown -> seitenweises TEI-XML.

Erzeugt TEI-XML nach dem Projektschema zbz_hersch.rng, TEI-P5-Subset
(type="naegeli"). Nutzt Layout-Regionen fuer Strukturerkennung und
OCR-Markdown fuer den Textinhalt.

Aufruf:
    python -m scripts.tei.tei_generator                 # alle Docs mit Layout
    python -m scripts.tei.tei_generator --doc 2310      # einzelnes Dokument
    python -m scripts.tei.tei_generator --doc 2310 --page 2  # einzelne Seite
"""

import argparse
import json
import re
import sys
from pathlib import Path
from xml.sax.saxutils import escape as xml_escape

# Projekt-Imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from scripts.config import (
    DOC_METADATA_PATH,
    LAYOUT_DIR,
    TEI_DIR,
    get_test_metadata,
)
from scripts.core.loaders import (
    discover_documents,
    discover_pages,
    load_ocr_text,
)
from scripts.utils import page_layout_name
from scripts.tei.tei_xml_utils import reading_order_permutation


# ---------------------------------------------------------------------------
# Markdown -> TEI Inline-Konvertierung
# ---------------------------------------------------------------------------

def md_to_tei_inline(text: str) -> str:
    """Konvertiert Markdown-Inline-Formatierung zu TEI.

    *italic*  -> <hi rendition="#i">italic</hi>
    **bold**  -> <hi rendition="#b">bold</hi>
    """
    # Bold zuerst (greedy vermeiden)
    text = re.sub(
        r'\*\*(.+?)\*\*',
        r'<hi rendition="#b">\1</hi>',
        text,
    )
    # Dann Italic
    text = re.sub(
        r'\*(.+?)\*',
        r'<hi rendition="#i">\1</hi>',
        text,
    )
    return text


# ---------------------------------------------------------------------------
# Dokument-Metadaten (doc_metadata.json > TESTPLAN Fallback)
# ---------------------------------------------------------------------------

_doc_metadata_cache = None


def get_document_metadata(doc_id: str) -> dict | None:
    """Laedt Metadaten aus doc_metadata.json, Fallback auf TESTPLAN."""
    global _doc_metadata_cache
    if _doc_metadata_cache is None:
        if DOC_METADATA_PATH.exists():
            raw = json.loads(DOC_METADATA_PATH.read_text(encoding="utf-8"))
            _doc_metadata_cache = raw.get("documents", {})
        else:
            _doc_metadata_cache = {}

    if doc_id in _doc_metadata_cache:
        dm = _doc_metadata_cache[doc_id]
        return {
            "lang": dm.get("language", "und"),
            "desc": dm.get("description", ""),
            "title": dm.get("title"),
            "author": dm.get("author"),
            "date": dm.get("date"),
            "type": dm.get("layout_type", "A"),
            "pub_form": dm.get("pub_form", "other"),
        }

    return get_test_metadata(doc_id)


# load_ocr_text() -> scripts.core.loaders


# ---------------------------------------------------------------------------
# Layout-JSON laden
# ---------------------------------------------------------------------------

def load_layout(doc_id: str, page: int) -> dict | None:
    """Laedt Layout-JSON fuer eine Seite."""
    path = LAYOUT_DIR / doc_id / page_layout_name(doc_id, page)
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return None


# ---------------------------------------------------------------------------
# OCR-Absaetze extrahieren
# ---------------------------------------------------------------------------

def split_paragraphs(ocr_text: str) -> list[str]:
    """Teilt OCR-Markdown in Absaetze (getrennt durch Leerzeilen)."""
    blocks = re.split(r'\n\s*\n', ocr_text.strip())
    return [b.strip() for b in blocks if b.strip()]


# ---------------------------------------------------------------------------
# Absatz-Layout-Matching
# ---------------------------------------------------------------------------

def match_paragraphs_to_regions(
    paragraphs: list[str],
    regions: list[dict],
) -> list[dict]:
    """Matched OCR-Absaetze zu Layout-Regionen nach Position (y_pct).

    Gibt eine Liste von dicts zurueck:
    {text, zbz_tag, region_id, bbox}
    """
    # Filtere relevante Regionen (nicht _filter, _skip)
    relevant = [
        r for r in regions
        if r.get("zbz_tag") not in ("_filter", "_skip", None)
        and r.get("bbox")
    ]

    # Spalten- und bandbewusste Lesereihenfolge (geteilt mit tei_step1, behebt die
    # Spalten-Verschraenkung der frueheren reinen y-Sortierung bei Doppelseiten/Zwei-Spaltern)
    order = reading_order_permutation([r["bbox"] for r in relevant])
    relevant = [relevant[i] for i in order]

    result = []

    if len(paragraphs) == len(relevant):
        # 1:1 Matching moeglich
        for i, (para, region) in enumerate(zip(paragraphs, relevant)):
            result.append({
                "text": para,
                "zbz_tag": region["zbz_tag"],
                "region_id": i + 1,
                "bbox": region["bbox"],
            })
    elif len(paragraphs) > 0:
        # Heuristik: Absaetze der Reihe nach zuordnen
        # Wenn mehr Absaetze als Regionen -> ueberschuessige als zb_paragraph
        for i, para in enumerate(paragraphs):
            if i < len(relevant):
                region = relevant[i]
                result.append({
                    "text": para,
                    "zbz_tag": region["zbz_tag"],
                    "region_id": i + 1,
                    "bbox": region["bbox"],
                })
            else:
                result.append({
                    "text": para,
                    "zbz_tag": "zb_paragraph",
                    "region_id": i + 1,
                    "bbox": None,
                })

    return result


# ---------------------------------------------------------------------------
# TEI-XML Generierung
# ---------------------------------------------------------------------------

def generate_tei_page(
    doc_id: str,
    page: int,
    ocr_text: str,
    layout: dict | None,
    metadata: dict | None = None,
) -> str:
    """Generiert TEI-XML fuer eine einzelne Seite."""

    paragraphs = split_paragraphs(ocr_text)

    if layout and layout.get("regions"):
        matched = match_paragraphs_to_regions(paragraphs, layout["regions"])
    else:
        # Kein Layout -> alle als zb_paragraph
        matched = [
            {"text": p, "zbz_tag": "zb_paragraph", "region_id": i + 1, "bbox": None}
            for i, p in enumerate(paragraphs)
        ]

    # TEI-Header Metadaten
    desc = ""
    title = doc_id
    author = None
    date = None
    if metadata:
        desc = metadata.get("desc", metadata.get("description", ""))
        title = metadata.get("title") or doc_id
        author = metadata.get("author")
        date = metadata.get("date")

    lang = "und"
    if metadata:
        lang_raw = metadata.get("lang", metadata.get("language", "und"))
        # ISO 639-3 (3 Buchstaben) direkt durchreichen
        if len(lang_raw) == 3 and lang_raw.isalpha():
            lang = lang_raw
        else:
            lang_map = {"FR": "fra", "DE": "deu", "DE/FR": "fra", "?": "und"}
            lang = lang_map.get(lang_raw, "und")

    lines = []
    lines.append('<?xml version="1.0" encoding="UTF-8"?>')
    lines.append('<TEI xmlns="http://www.tei-c.org/ns/1.0" type="naegeli">')
    lines.append("  <teiHeader>")
    lines.append("    <fileDesc>")
    lines.append("      <titleStmt>")
    lines.append(f'        <title type="main">{xml_escape(title)}</title>')
    if author:
        lines.append(f"        <author>{xml_escape(author)}</author>")
    lines.append("      </titleStmt>")
    lines.append("      <publicationStmt>")
    lines.append("        <publisher>ZBZ / DHCraft</publisher>")
    lines.append("      </publicationStmt>")
    lines.append("      <sourceDesc>")
    lines.append("        <bibl>")
    lines.append(f"          <publisher>Generated by tei_generator.py</publisher>")
    if date:
        lines.append(f"          <date>{xml_escape(date)}</date>")
    if desc:
        lines.append(f"          <note>{xml_escape(desc)}</note>")
    lines.append("        </bibl>")
    lines.append("      </sourceDesc>")
    lines.append("    </fileDesc>")
    lines.append("  </teiHeader>")

    # Facsimile (BBox-Koordinaten, falls Layout vorhanden)
    if layout:
        img_w = layout.get("image_width", 0)
        img_h = layout.get("image_height", 0)
        lines.append("  <facsimile>")
        lines.append(
            f'    <surface xml:id="facs_{page}" ulx="0" uly="0" '
            f'lrx="{img_w}" lry="{img_h}">'
        )
        for m in matched:
            if m["bbox"]:
                b = m["bbox"]
                # Prozent -> absolute Pixel
                ulx = int(b["x_pct"] / 100 * img_w)
                uly = int(b["y_pct"] / 100 * img_h)
                lrx = int((b["x_pct"] + b["w_pct"]) / 100 * img_w)
                lry = int((b["y_pct"] + b["h_pct"]) / 100 * img_h)
                zone_id = f"facs_{page}_r_{m['region_id']}"
                lines.append(
                    f'      <zone xml:id="{zone_id}" '
                    f'ulx="{ulx}" uly="{uly}" lrx="{lrx}" lry="{lry}"/>'
                )
        lines.append("    </surface>")
        lines.append("  </facsimile>")

    # Text/Body
    lines.append("  <text>")
    lines.append("    <body>")
    lines.append('      <div n="1">')
    lines.append(f'        <pb facs="#facs_{page}" n="{page}"/>')

    for m in matched:
        tag = m["zbz_tag"]
        rid = m["region_id"]
        facs_attr = f' facs="#facs_{page}_r_{rid}"' if m["bbox"] else ""

        # Text aufbereiten: XML-Escape, dann Markdown->TEI
        raw_text = m["text"]

        # Markdown-Heading-Prefix entfernen (## Titel -> Titel)
        raw_text = re.sub(r'^#{1,6}\s+', '', raw_text, flags=re.MULTILINE)

        # XML-Escape (aber Markdown-* beibehalten)
        # Erst escapen, dann Markdown konvertieren
        safe_text = xml_escape(raw_text)
        safe_text = md_to_tei_inline(safe_text)

        if tag == "zb_heading":
            lines.append(f"        <head{facs_attr}>")
            lines.append(f"          {safe_text}")
            lines.append("        </head>")
        elif tag == "footnote":
            # Fussnote: note place="foot"
            fn_id = f"fn{page}-{rid}"
            lines.append(
                f'        <note place="foot" xml:id="{fn_id}"{facs_attr}>'
            )
            lines.append(f"          {safe_text}")
            lines.append("        </note>")
        elif tag == "caption":
            lines.append(f"        <figure{facs_attr}>")
            lines.append(f"          <head>{safe_text}</head>")
            lines.append("        </figure>")
        else:
            # Default: Absatz
            lines.append(f"        <p{facs_attr}>")
            lines.append(f"          {safe_text}")
            lines.append("        </p>")

    lines.append("      </div>")
    lines.append("    </body>")
    lines.append("  </text>")
    lines.append("</TEI>")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Batch-Verarbeitung
# ---------------------------------------------------------------------------

def process_page(doc_id: str, page: int, metadata: dict | None = None) -> Path | None:
    """Verarbeitet eine einzelne Seite und schreibt TEI-XML."""
    ocr_text = load_ocr_text(doc_id, page)
    if not ocr_text:
        return None

    layout = load_layout(doc_id, page)
    tei_xml = generate_tei_page(doc_id, page, ocr_text, layout, metadata)

    TEI_DIR.mkdir(parents=True, exist_ok=True)
    out_path = TEI_DIR / f"{doc_id}_p{page}.xml"
    out_path.write_text(tei_xml, encoding="utf-8")
    return out_path


def process_document(doc_id: str) -> list[Path]:
    """Verarbeitet alle Seiten eines Dokuments."""
    metadata = get_document_metadata(doc_id)
    generated = []

    pages = discover_pages(doc_id)

    for page in pages:
        result = process_page(doc_id, page, metadata)
        if result:
            generated.append(result)

    return generated


# discover_documents() -> scripts.core.loaders


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="TEI-XML Generator: Layout-JSON + OCR-Markdown -> TEI-XML"
    )
    parser.add_argument("--doc", help="Einzelnes Dokument (z.B. 2310)")
    parser.add_argument("--page", type=int, help="Einzelne Seite (nur mit --doc)")
    args = parser.parse_args()

    if args.doc and args.page:
        # Einzelne Seite
        metadata = get_document_metadata(args.doc)
        result = process_page(args.doc, args.page, metadata)
        if result:
            print(f"  Generiert: {result}")
        else:
            print(f"  Keine OCR-Daten fuer {args.doc} Seite {args.page}")
    elif args.doc:
        # Ganzes Dokument
        print(f"Generiere TEI fuer Dokument {args.doc}...")
        results = process_document(args.doc)
        print(f"  {len(results)} Seiten generiert")
        for r in results:
            print(f"    {r.name}")
    else:
        # Alle Dokumente
        doc_ids = discover_documents()
        print(f"Generiere TEI fuer {len(doc_ids)} Dokumente...")
        total = 0
        for doc_id in doc_ids:
            results = process_document(doc_id)
            total += len(results)
            has_layout = any(
                load_layout(doc_id, int(re.search(r'_p(\d+)', r.name).group(1)))
                for r in results
            ) if results else False
            layout_tag = " [+Layout]" if has_layout else " [nur OCR]"
            print(f"  {doc_id}: {len(results)} Seiten{layout_tag}")
        print(f"\nGesamt: {total} TEI-XML Dateien in {TEI_DIR}")


if __name__ == "__main__":
    main()
