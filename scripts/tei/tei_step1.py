"""
Step 1: Enhanced Rule-Based TEI.

Erzeugt regelbasiertes TEI-XML aus OCR-Text und Layout-Daten.
Ergebnis: TEI-Fragment + Facsimile-Zonen pro Seite.

Wird aufgerufen von: tei_unified.py (Orchestrierung).
"""

import re

from xml.sax.saxutils import escape as xml_escape

from scripts.core.loaders import load_layout_gemini, load_ocr_text
from scripts.tei.tei_generator import (
    annotate_entities,
    md_to_tei_inline,
    split_paragraphs,
)
from scripts.tei.tei_xml_utils import normalize_for_tei

# Speaker-Erkennung: "Name:" am Zeilenanfang (Interview/Debate)
SPEAKER_PATTERN = re.compile(r'^([A-Z][a-zA-Z\u00e9\u00e8\u00ea\u00e0\u00e2\u00fc\u00f6\u00e4\s.\-]+?):\s*')


# ---------------------------------------------------------------------------
# Absatz-Region-Matching (erweitert)
# ---------------------------------------------------------------------------

def match_paragraphs_to_regions(
    paragraphs: list[str],
    regions: list[dict],
) -> list[dict]:
    """Matched OCR-Absaetze zu Layout-Regionen nach y-Position.

    Erweitert gegenueber tei_generator.py:
    - Nutzt label direkt (section_header, footnote, caption, text, etc.)
    - Filtert _filter/_skip
    """
    relevant = [
        r for r in regions
        if r.get("zbz_tag") not in ("_filter", "_skip", None)
        and r.get("bbox")
    ]
    relevant.sort(key=lambda r: r["bbox"]["y_pct"])

    result = []
    if len(paragraphs) == len(relevant):
        for i, (para, region) in enumerate(zip(paragraphs, relevant)):
            result.append({
                "text": para,
                "zbz_tag": region["zbz_tag"],
                "label": region.get("label", "text"),
                "region_id": i + 1,
                "bbox": region["bbox"],
            })
    elif paragraphs:
        for i, para in enumerate(paragraphs):
            if i < len(relevant):
                region = relevant[i]
                result.append({
                    "text": para,
                    "zbz_tag": region["zbz_tag"],
                    "label": region.get("label", "text"),
                    "region_id": i + 1,
                    "bbox": region["bbox"],
                })
            else:
                result.append({
                    "text": para,
                    "zbz_tag": "zb_paragraph",
                    "label": "text",
                    "region_id": i + 1,
                    "bbox": None,
                })
    return result


# ---------------------------------------------------------------------------
# Line-Break-Einfuegung + Silbentrennung
# ---------------------------------------------------------------------------

def insert_line_breaks(text: str, page: int, region_id: int) -> str:
    """Konvertiert Zeilenumbrueche im OCR-Text zu <lb/> Elementen.

    - Jedes \\n innerhalb eines Absatzes wird zu <lb/>
    - Silbentrennung: Zeile endet mit '-' + naechste beginnt mit Kleinbuchstabe
      -> Bindestrich entfernen, break="no"
    - Zaehler N001, N002, ... (reset pro Element)
    """
    lines = text.split("\n")
    if len(lines) <= 1:
        return text

    result_parts = []
    lb_counter = 0

    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            continue

        if i > 0 and result_parts:
            lb_counter += 1
            # Silbentrennung pruefen
            prev_part = result_parts[-1] if result_parts else ""
            has_hyphen = prev_part.rstrip().endswith("-")
            starts_lower = stripped and stripped[0].islower()

            if has_hyphen and starts_lower:
                # Bindestrich entfernen
                result_parts[-1] = prev_part.rstrip()[:-1]
                lb = (f'<lb facs="#facs_{page}_l_{region_id}_{lb_counter}" '
                      f'n="N{lb_counter:03d}" break="no"/>')
            else:
                lb = (f'<lb facs="#facs_{page}_l_{region_id}_{lb_counter}" '
                      f'n="N{lb_counter:03d}"/>')
            result_parts.append(lb)

        result_parts.append(stripped)

    return "".join(result_parts)


# ---------------------------------------------------------------------------
# Step 1: Enhanced Rule-Based TEI
# ---------------------------------------------------------------------------

def _is_interview_turn(raw_text: str, prev_was_question: bool) -> bool:
    """Erkennt ob ein Paragraph ein Interview-Turn ist.

    Heuristik:
    - Endet mit '?' -> Interviewer-Frage
    - Beginnt mit 'Name:' -> expliziter Speaker
    - Folgt auf eine Frage -> Antwort
    """
    text = raw_text.strip()
    if not text:
        return False
    if text.endswith("?"):
        return True
    if SPEAKER_PATTERN.match(text):
        return True
    if prev_was_question:
        return True
    return False


def _compute_facsimile_zones(matched: list[dict], layout: dict | None, page: int) -> dict:
    """Berechnet Facsimile-Zonen aus gematchten Regionen.

    Returns:
        {zones: [...], image_width, image_height}
    """
    img_w = layout.get("image_width", 0) if layout else 0
    img_h = layout.get("image_height", 0) if layout else 0
    zones = []
    for item in matched:
        bbox = item["bbox"]
        if bbox:
            ulx = int(bbox["x_pct"] / 100 * img_w)
            uly = int(bbox["y_pct"] / 100 * img_h)
            lrx = int((bbox["x_pct"] + bbox["w_pct"]) / 100 * img_w)
            lry = int((bbox["y_pct"] + bbox["h_pct"]) / 100 * img_h)
            zones.append({
                "zone_id": f"facs_{page}_r_{item['region_id']}",
                "ulx": ulx, "uly": uly, "lrx": lrx, "lry": lry,
            })
    return {"zones": zones, "image_width": img_w, "image_height": img_h}


def _build_tei_body(matched: list[dict], page: int, genre: str | None, is_interview: bool) -> str:
    """Baut das TEI body-Fragment aus gematchten Regionen.

    Returns:
        TEI-XML Fragment als String.
    """
    lines = []

    # Div-Typ bestimmen
    div_type_attr = 'n="1"'
    if genre == "review":
        div_type_attr = 'type="review"'
    elif genre in ("interview", "debate"):
        div_type_attr = 'type="interview"'
    elif genre == "encyclopedia":
        div_type_attr = 'type="entry"'
    elif genre == "conversation":
        div_type_attr = 'type="conversation"'

    lines.append(f"      <div {div_type_attr}>")
    lines.append(f'        <pb facs="#facs_{page}" n="{page}"/>')

    fn_counter = 0
    any_content_emitted = False
    last_was_question = False

    for item in matched:
        tag = item["zbz_tag"]
        rid = item["region_id"]
        facs_attr = f' facs="#facs_{page}_r_{rid}"' if item["bbox"] else ""

        raw_text = item["text"]
        raw_text = re.sub(r'^#{1,6}\s+', '', raw_text, flags=re.MULTILINE)
        raw_text = re.sub(r'!\[.*?\]\(.*?\)', '', raw_text)

        safe_text = xml_escape(raw_text)
        safe_text = md_to_tei_inline(safe_text)
        safe_text = annotate_entities(safe_text)
        safe_text = insert_line_breaks(safe_text, page, rid)

        if tag == "zb_heading" and not any_content_emitted:
            lines.append(f"        <head{facs_attr}>")
            lines.append(f"          {safe_text}")
            lines.append("        </head>")
            any_content_emitted = True
        elif tag == "zb_heading":
            lines.append(f"        <p{facs_attr}>")
            lines.append(f"          {safe_text}")
            lines.append("        </p>")
            any_content_emitted = True
        elif tag == "footnote":
            fn_counter += 1
            fn_id = f"fn{page}-{fn_counter}"
            lines.append(
                f'        <note place="foot" n="{fn_counter}" '
                f'xml:id="{fn_id}"{facs_attr}>'
            )
            lines.append(f"          {safe_text}")
            lines.append("        </note>")
            any_content_emitted = True
        elif tag == "caption":
            lines.append(f"        <figure{facs_attr}>")
            lines.append(f"          <head>{safe_text}</head>")
            lines.append("        </figure>")
            any_content_emitted = True
        elif is_interview and tag == "zb_paragraph" and _is_interview_turn(raw_text, last_was_question):
            is_question = raw_text.rstrip().endswith("?")
            speaker_match = SPEAKER_PATTERN.match(raw_text)
            speaker_name = speaker_match.group(1).strip() if speaker_match else ""

            if speaker_name:
                speaker_tei = f'<persName>{xml_escape(speaker_name)}</persName>'
            else:
                speaker_tei = ""

            lines.append("        <sp>")
            lines.append(f"          <speaker>{speaker_tei}</speaker>")
            lines.append(f"          <p{facs_attr}>")
            lines.append(f"            {safe_text}")
            lines.append("          </p>")
            lines.append("        </sp>")
            last_was_question = is_question
            any_content_emitted = True
        else:
            lines.append(f"        <p{facs_attr}>")
            lines.append(f"          {safe_text}")
            lines.append("        </p>")
            if is_interview:
                last_was_question = raw_text.rstrip().endswith("?")
            any_content_emitted = True

    lines.append("      </div>")
    return "\n".join(lines)


def process_page_step1(
    doc_id: str,
    page: int,
    metadata: dict,
    genre: str | None,
) -> tuple[str, dict]:
    """Step 1: Erzeugt erweitertes regel-basiertes TEI fuer eine Seite.

    Returns:
        (tei_fragment, facsimile_data)
    """
    ocr_text = load_ocr_text(doc_id, page)
    if not ocr_text:
        return "", {}

    # TEI-Zeichennormalisierung (Editionsrichtlinien ZBZ, E49)
    ocr_text = normalize_for_tei(ocr_text)

    layout = load_layout_gemini(doc_id, page)
    paragraphs = split_paragraphs(ocr_text)

    if layout and layout.get("regions"):
        matched = match_paragraphs_to_regions(paragraphs, layout["regions"])
    else:
        matched = [
            {"text": p, "zbz_tag": "zb_paragraph", "label": "text",
             "region_id": i + 1, "bbox": None}
            for i, p in enumerate(paragraphs)
        ]

    facsimile_data = _compute_facsimile_zones(matched, layout, page)
    is_interview = genre in ("interview", "debate", "conversation")
    tei_fragment = _build_tei_body(matched, page, genre, is_interview)

    return tei_fragment, facsimile_data
