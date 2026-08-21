"""
Step 1: Enhanced Rule-Based TEI.

Erzeugt regelbasiertes TEI-XML aus OCR-Text und Layout-Daten.
Ergebnis: TEI-Fragment + Facsimile-Zonen pro Seite.

Wird aufgerufen von: tei_unified.py (Orchestrierung).
"""

import html
import re
from xml.sax.saxutils import escape as xml_escape

from scripts.core.loaders import load_layout_gemini, load_ocr_text
from scripts.tei.tei_generator import (
    md_to_tei_inline,
    split_paragraphs,
)
from scripts.tei.tei_xml_utils import normalize_for_tei, reading_order_permutation

# Speaker-Erkennung: "Name:" am Zeilenanfang (Interview/Debate)
SPEAKER_PATTERN = re.compile(r'^([A-Z][a-zA-Z\u00e9\u00e8\u00ea\u00e0\u00e2\u00fc\u00f6\u00e4\s.\-]+?):\s*')

# ---------------------------------------------------------------------------
# Chrome-Projektion: gedruckte Seitenzahl + Filter-Absatz-Verwerfung
# ---------------------------------------------------------------------------
# Beide Defekte teilen eine Ursache: match_paragraphs_to_regions entfernt _filter/_skip-
# Regionen (Kopf-/Fusszeilen, Deckblatt-Metadaten) aus der Regionsliste, laesst die zuge-
# hoerigen OCR-Absaetze aber stehen. Bei Laengen-Mismatch werden sie positionsbasiert echten
# Regionen zugeordnet oder als bbox-loser Ueberhang angehaengt. drop_filter_echoes verwirft
# diese Absaetze VOR dem Matching; detect_page_number liest die gedruckte Seitenzahl aus der
# Fusszeilen-Filter-Region, damit <pb n=...> die Druckseite statt der Scan-Nummer traegt.

_TOKEN_RE = re.compile(r"\w+", re.UNICODE)

# Plausible gedruckte Seitenzahl in einer Filter-Region: reine Ziffern, Punkt-Notation
# (7.14), optional in eckigen Klammern ([248]). Auf 4 Stellen begrenzt. Eine allein
# stehende vierstellige Jahreszahl waere formgleich und wuerde fehlgelesen; solche
# isolierten Jahres-Filterregionen kommen im Korpus-Chrome nicht vor.
_PAGE_NUMBER_RE = re.compile(r"^\[?\s*(\d{1,4}(?:\.\d{1,4})?)\s*\]?$")

# Schwelle fuer "Absatz ist Echo einer Filter-Region": ein Absatz wird nur verworfen, wenn
# fast alle seine Wort-Tokens auch in den Filter-Regionen vorkommen. Konservativ nach oben
# kalibriert -- lieber eine Deckblattzeile durchlassen als echten Fliesstext verwerfen, der
# ein Metadaten-Wort (z.B. "ETH-Bibliothek") nur nebenbei nutzt.
_FILTER_ECHO_MIN_COVERAGE = 0.8


def _tokens(text: str) -> set[str]:
    return {t.lower() for t in _TOKEN_RE.findall(text)}


def _filter_regions(regions: list[dict]) -> list[dict]:
    return [
        r for r in regions
        if r.get("zbz_tag") in ("_filter", "_skip") and (r.get("text") or "").strip()
    ]


def detect_page_number(regions: list[dict]) -> str | None:
    """Gedruckte Seitenzahl aus einer _filter/_skip-Region, sonst None.

    Durchsucht die Chrome-Regionen (Kopf-/Fusszeile) nach einem plausiblen Seitenzahl-Text
    und gibt dessen numerischen Wert zurueck, damit Step 1 <pb n=...> auf die Druckseite
    statt die laufende Scan-Nummer setzen kann. Keine seitenuebergreifende Interpolation.
    """
    for r in _filter_regions(regions):
        m = _PAGE_NUMBER_RE.match(r["text"].strip())
        if m:
            return m.group(1)
    return None


def drop_filter_echoes(paragraphs: list[str], regions: list[dict]) -> list[str]:
    """Verwirft OCR-Absaetze, die eine _filter/_skip-Region wiederholen, vor dem Matching.

    Ein Absatz faellt, wenn seine Wort-Tokens zu mindestens _FILTER_ECHO_MIN_COVERAGE von der
    Vereinigung aller Filter-Region-Tokens abgedeckt sind. Das faengt Deckblatt-/Kopf-/Fusszeilen-
    Text ebenso wie den Seitenzahl-Absatz (siehe detect_page_number). Absaetze ohne Tokens bleiben.
    """
    filters = _filter_regions(regions)
    if not filters:
        return paragraphs
    filter_bag: set[str] = set()
    for r in filters:
        filter_bag |= _tokens(r["text"])

    kept = []
    for para in paragraphs:
        toks = _tokens(para)
        if toks and len(toks & filter_bag) / len(toks) >= _FILTER_ECHO_MIN_COVERAGE:
            continue
        kept.append(para)
    return kept


# ---------------------------------------------------------------------------
# Dokumentweiter Seitenzahl-Interpolations-Pass
# ---------------------------------------------------------------------------
# detect_page_number liest die gedruckte Zahl nur dort, wo eine Fusszeilen-Filter-
# Region existiert. Wo sie fehlt, faellt pb@n auf die Scan-Nummer zurueck. Der Pass
# fuellt solche Luecken aus den erkannten Nachbarn, aber nur wo die Arithmetik
# eindeutig ist. Regel (forward-verankert): ein linker Anker (erkannte Zahl auf einer
# frueheren Seite) setzt den Folgewert fort; existiert zusaetzlich ein rechter Anker,
# muss er denselben Wert stuetzen, sonst bleibt Fallback. Eine reine Rueckwaerts-
# Extrapolation (nur rechter Anker) fuellt NICHT -- unpaginiertes Frontmatter (Deckblatt)
# vor der ersten gedruckten Zahl behaelt so seine Scan-Nummer.
# Erschlossene Zahlen werden in eckige Klammern gesetzt (ZBZ-Referenzkonvention,
# z.B. reference_tei: n="[249]"); erkannte Zahlen bleiben blank.

# Per-Dokument-Cache der erschlossenen Luecken; process_page_step1 wird pro Seite
# aufgerufen, der Pass braucht aber das ganze Dokument. Innerhalb eines Laufs sind die
# Layout-Daten stabil, daher ist die einmalige Projektion pro doc_id deterministisch.
_INTERP_CACHE: dict[str, dict[int, int]] = {}


def interpolate_document_pb(detected: dict[int, int], pages: list[int]) -> dict[int, int]:
    """Fuellt Luecken gedruckter Seitenzahlen forward-verankert und konsistenzgeprueft.

    Args:
        detected: erkannte, rein ganzzahlige Druckseitenzahl je Seite (Punktnotation und
                  nicht-numerische Werte sind vom Aufrufer ausgeschlossen).
        pages: existierende Seitennummern des Dokuments.

    Returns:
        Seite -> erschlossene Ganzzahl, nur fuer Luecken (Seiten ohne Erkennung) und nur
        dort, wo die Regel genau einen Wert stuetzt. Fehlt eine Seite im Ergebnis, bleibt
        der Scan-Nummern-Fallback.
    """
    result: dict[int, int] = {}
    for p in pages:
        if p in detected:
            continue
        left = max((q for q in detected if q < p), default=None)
        right = min((q for q in detected if q > p), default=None)
        forward = detected[left] + (p - left) if left is not None else None
        backward = detected[right] - (right - p) if right is not None else None
        if forward is None:
            continue  # no left anchor -> no backward-only extrapolation (frontmatter)
        if backward is not None and backward != forward:
            continue  # neighbors contradict -> ambiguous
        result[p] = forward
    return result


def _scan_printed_numbers(doc_id: str) -> tuple[list[int], dict[int, int]]:
    """Probt die Seiten 1..N eines Dokuments und sammelt rein ganzzahlige Druckseitenzahlen.

    Eine Seite existiert, solange sie OCR-Text oder Layout hat; die Suche stoppt an der
    ersten fehlenden Seite (Seiten sind konventionsgemaess 1..N zusammenhaengend).
    """
    pages: list[int] = []
    detected: dict[int, int] = {}
    page = 1
    while True:
        layout = load_layout_gemini(doc_id, page)
        ocr = load_ocr_text(doc_id, page)
        if not layout and not ocr:
            break
        pages.append(page)
        if layout and layout.get("regions"):
            printed = detect_page_number(layout["regions"])
            if printed and printed.isdigit():
                detected[page] = int(printed)
        page += 1
    return pages, detected


def resolve_pb_number(doc_id: str, page: int, printed_this_page: str | None) -> str:
    """Bestimmt pb@n: erkannt (blank), erschlossen ([n]) oder Scan-Nummer-Fallback."""
    if printed_this_page:
        return printed_this_page
    interp = _INTERP_CACHE.get(doc_id)
    if interp is None:
        pages, detected = _scan_printed_numbers(doc_id)
        interp = interpolate_document_pb(detected, pages)
        _INTERP_CACHE[doc_id] = interp
    if page in interp:
        return f"[{interp[page]}]"
    return str(page)


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
    order = reading_order_permutation([r["bbox"] for r in relevant])
    relevant = [relevant[i] for i in order]

    result = []
    if len(paragraphs) == len(relevant):
        for i, (para, region) in enumerate(zip(paragraphs, relevant, strict=True)):
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
    return bool(prev_was_question)


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


def _build_tei_body(
    matched: list[dict], page: int, genre: str | None, is_interview: bool, pb_n: str
) -> str:
    """Baut das TEI body-Fragment aus gematchten Regionen.

    pb_n ist die @n des <pb> (gedruckte Seitenzahl oder Scan-Nummer als Fallback); die
    @facs-Referenz bleibt scan-basiert (#facs_{page}), da sie auf das Scan-Bild zeigt.

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
    lines.append(f'        <pb facs="#facs_{page}" n="{pb_n}"/>')

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

        # OCR-Markdown enthaelt Sonderzeichen teils bereits als HTML-Entity
        # (z.B. "&amp;"). Erst auf Literale kollabieren, dann genau einmal
        # XML-escapen -- sonst entsteht Doppelkodierung ("&amp;amp;").
        raw_text = html.unescape(raw_text)

        safe_text = xml_escape(raw_text)
        safe_text = md_to_tei_inline(safe_text)
        safe_text = insert_line_breaks(safe_text, page, rid)

        if tag == "zb_heading" and not any_content_emitted:
            # Lexikonartikel: erste Ueberschrift ist das Lemma (Richtlinie head type="lemma")
            head_type = ' type="lemma"' if genre == "encyclopedia" else ""
            lines.append(f"        <head{head_type}{facs_attr}>")
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

    printed = None
    if layout and layout.get("regions"):
        regions = layout["regions"]
        printed = detect_page_number(regions)
        paragraphs = drop_filter_echoes(paragraphs, regions)
        matched = match_paragraphs_to_regions(paragraphs, regions)
    else:
        matched = [
            {"text": p, "zbz_tag": "zb_paragraph", "label": "text",
             "region_id": i + 1, "bbox": None}
            for i, p in enumerate(paragraphs)
        ]

    # Detected number on this page stays blank; a gap is filled from neighbors
    # ([n], bracketed) or falls back to the running scan number.
    pb_n = resolve_pb_number(doc_id, page, printed)

    facsimile_data = _compute_facsimile_zones(matched, layout, page)
    is_interview = genre in ("interview", "debate", "conversation")
    tei_fragment = _build_tei_body(matched, page, genre, is_interview, pb_n)

    return tei_fragment, facsimile_data
