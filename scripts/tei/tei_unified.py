"""
Unified TEI Pipeline: Rule-Based Scaffold + Gemini Refinement.

4-Stufen-Pipeline:
  Step 1: Enhanced rule-based TEI (kostenlos, deterministisch)
  Step 2: Gemini Refinement (1 API-Call/Seite, Mapping-Table-Prompt)
  Step 3: Document Assembly (teiHeader + facsimile + body)
  Step 4: RelaxNG Validation (optional)

Aufruf:
    python -m scripts.tei.tei_unified --doc 2310
    python -m scripts.tei.tei_unified --sample
    python -m scripts.tei.tei_unified --all
    python -m scripts.tei.tei_unified --doc 2310 --step 1
    python -m scripts.tei.tei_unified --validate
    python -m scripts.tei.tei_unified --force
    python -m scripts.tei.tei_unified --dry-run
"""

import argparse
import functools
import json
import os
import re
import sys
import time
import traceback
import xml.etree.ElementTree as ET
from pathlib import Path
from xml.sax.saxutils import escape as xml_escape

from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.config import (
    DOC_METADATA_PATH,
    GEMINI_CORRECTED_A_DIR,
    GEMINI_CORRECTED_B_DIR,
    GEMINI_MODEL,
    IMAGES_DIR,
    KNOWN_ENTITIES,
    LAYOUT_DIR,
    LLM_CORRECTED_C_DIR,
    MISTRAL_RESULTS_DIR,
    TEI_NS,
    TEI_UNIFIED_DIR,
)

# Re-read after dotenv (config.py reads os.environ at import time)
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
from scripts.tei.tei_generator import (
    annotate_entities,
    get_document_metadata,
    load_ocr_text,
    md_to_tei_inline,
    split_paragraphs,
)
from scripts.tei.tei_mapping_prompt import (
    build_mapping_prompt,
    build_refinement_input,
)

# Speaker-Erkennung: "Name:" am Zeilenanfang (Interview/Debate)
SPEAKER_PATTERN = re.compile(r'^([A-Z][a-zA-Z\u00e9\u00e8\u00ea\u00e0\u00e2\u00fc\u00f6\u00e4\s.\-]+?):\s*')

# Lazy import fuer build_doc_hints / infer_genre (vermeidet zirkulaere Imports)
@functools.lru_cache(maxsize=1)
def _get_layout_qa():
    import scripts.layout_qa_gemini as m
    return m


# ---------------------------------------------------------------------------
# Layout laden (bevorzugt Gemini-korrigiert)
# ---------------------------------------------------------------------------

def load_layout_gemini(doc_id: str, page: int) -> dict | None:
    """Laedt Gemini-korrigiertes Layout-JSON, Fallback auf Docling.

    Gemini-JSON hat evtl. kein image_width/image_height -- wird aus
    Docling-JSON ergaenzt falls vorhanden.
    """
    padded = str(page).zfill(3)
    gemini_path = LAYOUT_DIR / doc_id / f"{doc_id}_p{padded}_layout_gemini.json"
    docling_path = LAYOUT_DIR / doc_id / f"{doc_id}_p{padded}_layout.json"

    layout = None
    if gemini_path.exists():
        layout = json.loads(gemini_path.read_text(encoding="utf-8"))
    elif docling_path.exists():
        layout = json.loads(docling_path.read_text(encoding="utf-8"))

    if layout is None:
        return None

    # Bildgroesse ergaenzen falls fehlend (aus Docling-JSON)
    if not layout.get("image_width") and docling_path.exists():
        try:
            docling = json.loads(docling_path.read_text(encoding="utf-8"))
            layout["image_width"] = docling.get("image_width", 0)
            layout["image_height"] = docling.get("image_height", 0)
        except (json.JSONDecodeError, OSError) as e:
            print(f"  WARNUNG: Docling-Fallback fuer Bildgroesse fehlgeschlagen: {e}")

    return layout


# ---------------------------------------------------------------------------
# Seiten entdecken
# ---------------------------------------------------------------------------

def discover_pages(doc_id: str) -> list[int]:
    """Findet alle verfuegbaren Seiten (aus OCR-Dateien)."""
    pages = set()
    for base_dir in [GEMINI_CORRECTED_B_DIR, GEMINI_CORRECTED_A_DIR,
                     LLM_CORRECTED_C_DIR, MISTRAL_RESULTS_DIR]:
        if base_dir.exists():
            for f in base_dir.glob(f"{doc_id}_p*.md"):
                match = re.search(r'_p(\d+)\.md$', f.name)
                if match:
                    pages.add(int(match.group(1)))
    return sorted(pages)


def skip_jstor_cover(pages: list[int], metadata: dict) -> list[int]:
    """Entfernt JSTOR-Coverseite (Seite 1) falls has_jstor_cover."""
    if metadata and metadata.get("has_jstor_cover"):
        return [p for p in pages if p != 1]
    return pages


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

            if speaker_name and speaker_name in KNOWN_ENTITIES:
                gnd = KNOWN_ENTITIES[speaker_name]
                speaker_tei = f'<persName ref="{gnd}">{xml_escape(speaker_name)}</persName>'
            elif speaker_name:
                speaker_tei = f'<persName ref="GND:unknown">{xml_escape(speaker_name)}</persName>'
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


# ---------------------------------------------------------------------------
# Step 2: Gemini Refinement
# ---------------------------------------------------------------------------

def get_overlay_path(doc_id: str, page: int) -> Path | None:
    """Findet das Overlay-PNG fuer eine Seite."""
    padded = str(page).zfill(3)
    overlay = LAYOUT_DIR / doc_id / f"{doc_id}_p{padded}_overlay_gemini.png"
    if overlay.exists():
        return overlay
    overlay = LAYOUT_DIR / doc_id / f"{doc_id}_p{padded}_overlay.png"
    if overlay.exists():
        return overlay
    # Fallback: Scan-Bild
    scan = IMAGES_DIR / doc_id / f"{doc_id}_p{padded}.png"
    if scan.exists():
        return scan
    return None


def reannotate_entities(xml_text: str) -> str:
    """Tag-aware Entity Re-Annotation: taggt fehlende KNOWN_ENTITIES.

    Findet Entitaetsnamen im Text die NICHT bereits innerhalb eines
    <persName>/<orgName>-Tags stehen und fuegt Tags hinzu.
    Laengere Namen zuerst (wie annotate_entities).
    """
    sorted_names = sorted(KNOWN_ENTITIES.keys(), key=len, reverse=True)

    for name in sorted_names:
        gnd = KNOWN_ENTITIES[name]
        tag = f'<persName ref="{gnd}">{name}</persName>'
        # Regex: name muss an Wortgrenzen stehen UND darf nicht
        # bereits innerhalb eines <persName>...</persName> sein.
        # Strategie: Split an bestehenden persName/orgName-Tags,
        # annotiere nur in den Zwischenraeumen.
        parts = re.split(r'(<(?:persName|orgName)[^>]*>.*?</(?:persName|orgName)>)',
                         xml_text, flags=re.DOTALL)
        new_parts = []
        for i, part in enumerate(parts):
            if i % 2 == 0:
                # Text ausserhalb bestehender Entity-Tags -> annotieren
                pattern = r'(?<!\w)' + re.escape(name) + r'(?!\w)'
                part = re.sub(pattern, tag, part)
            # else: bestehender Tag -> unveraendert lassen
            new_parts.append(part)
        xml_text = "".join(new_parts)

    return xml_text


# ---------------------------------------------------------------------------
# Shared XML Utilities
# ---------------------------------------------------------------------------

def _make_element(tag: str, tail: str = None, **attribs):
    """Erzeugt ein ET.Element mit optionalem tail und Attributen."""
    elem = ET.Element(tag)
    if tail is not None:
        elem.tail = tail
    for k, v in attribs.items():
        elem.set(k, v)
    return elem


def _wrap_orphan_groups(container, is_orphan, make_wrapper) -> None:
    """Wickelt zusammenhaengende Orphan-Kinder eines Containers in Wrapper ein.

    Args:
        container: ET.Element mit Kindern
        is_orphan: Callable(child) -> bool, ob Kind eingewickelt werden soll
        make_wrapper: Callable() -> ET.Element, erzeugt den Wrapper
    """
    children = list(container)
    groups = []
    current_group = []
    current_start = None
    for i, child in enumerate(children):
        if is_orphan(child):
            if current_start is None:
                current_start = i
            current_group.append(child)
        else:
            if current_group:
                groups.append((current_start, current_group))
                current_group = []
                current_start = None
    if current_group:
        groups.append((current_start, current_group))

    for start_idx, elems in reversed(groups):
        wrapper = make_wrapper()
        for e in elems:
            container.remove(e)
            wrapper.append(e)
        container.insert(start_idx, wrapper)


def _fix_simple_patterns(xml: str) -> str:
    """Regex-basierte Fixes fuer haeufige Gemini-TEI-Fehler.

    Fix -1: <ab> mit <p> darin -> entferne <ab>-Wrapper
    Fix 0:  <head> innerhalb <speaker> -> entferne <head>-Tags
    Fix 1:  <head><p ...>...</p></head> -> <head ...>...</head>
    """
    # Fix -1: <ab> mit <p> darin -> entferne <ab>-Wrapper, behalte Inhalt
    def _unwrap_ab(m):
        inner = m.group(1)
        if "<p" in inner or "<p>" in inner:
            return inner
        return m.group(0)

    xml = re.sub(r'<ab[^>]*>(.*?)</ab>', _unwrap_ab, xml, flags=re.DOTALL)

    # Fix 0: <head> innerhalb <speaker> -> entferne <head>-Tags
    xml = re.sub(
        r'<speaker>\s*<head[^>]*>(.*?)</head>\s*</speaker>',
        lambda m: f'<speaker>{m.group(1)}</speaker>',
        xml, flags=re.DOTALL,
    )

    # Fix 1: <head><p ...>...</p></head> -> <head ...>...</head>
    def _fix_head_with_p(match):
        head_attrs = match.group(1) or ""
        p_attrs = match.group(2) or ""
        content = match.group(3)
        if "facs=" not in head_attrs and "facs=" in p_attrs:
            head_attrs = head_attrs.rstrip() + " " + p_attrs.strip()
        return f"<head{head_attrs}>{content}</head>"

    xml = re.sub(
        r'<head([^>]*)>\s*<p([^>]*)>(.*?)</p>\s*</head>',
        _fix_head_with_p, xml, flags=re.DOTALL,
    )

    return xml


def _parse_tei_fragment(xml: str):
    """Parst ein TEI-Fragment in einen ET-Root mit Namespace-Wrapper.

    Returns:
        root Element oder None bei ParseError.
    """
    wrapped = f'<root xmlns="{TEI_NS}">{xml}</root>'
    try:
        return ET.fromstring(wrapped)
    except ET.ParseError:
        return None


def _serialize_tei_fragment(root) -> str:
    """Serialisiert einen ET-Root zurueck zu TEI-Fragment-String."""
    ET.register_namespace("", TEI_NS)
    result = ET.tostring(root, encoding="unicode")
    result = re.sub(r'^<root[^>]*>', '', result)
    result = re.sub(r'</root>$', '', result)
    result = result.replace("ns0:", "").replace(":ns0", "")
    return result


def _fix_structural_issues(xml: str) -> str:
    """ET-basierte Fixes fuer Strukturprobleme in Gemini-TEI.

    Fix 2:  <head> nach Content -> <p>
    Fix 2b: <epigraph> nach Content -> entpacken
    Fix 3:  <sp> gemischt mit <p>/<figure>/<epigraph> -> split in sub-divs
    Fix 3b: Lose Inline-Elemente in <div> -> in <p> einwickeln
    """
    root = _parse_tei_fragment(xml)
    if root is None:
        return xml

    # Fix 2 + 2b: <head>/<epigraph> nach Content
    for div in root.iter(f"{{{TEI_NS}}}div"):
        children = list(div)
        any_content = False
        for child in children:
            tag = child.tag.replace(f"{{{TEI_NS}}}", "")
            if tag == "head" and any_content:
                child.tag = f"{{{TEI_NS}}}p"
            elif tag == "epigraph" and any_content:
                idx = list(div).index(child)
                inner = list(child)
                div.remove(child)
                for j, ic in enumerate(inner):
                    div.insert(idx + j, ic)
            elif tag in ("pb",):
                pass
            else:
                any_content = True

    # Fix 3: <sp> gemischt mit <p>/<figure>/<epigraph> -> split into sub-divs
    for div in list(root.iter(f"{{{TEI_NS}}}div")):
        children = list(div)
        has_sp = any(c.tag == f"{{{TEI_NS}}}sp" for c in children)
        has_pre_sp_content = False
        if has_sp:
            for c in children:
                tag = c.tag.replace(f"{{{TEI_NS}}}", "")
                if tag == "sp":
                    break
                if tag in ("p", "figure", "epigraph"):
                    has_pre_sp_content = True

        if has_sp and has_pre_sp_content:
            pre_sp = []
            sp_and_after = []
            found_sp = False
            pb_elem = None
            for c in children:
                tag = c.tag.replace(f"{{{TEI_NS}}}", "")
                if tag == "sp":
                    found_sp = True
                if tag == "pb" and not found_sp:
                    pb_elem = c
                    continue
                if not found_sp:
                    pre_sp.append(c)
                else:
                    sp_and_after.append(c)

            div_type = div.get("type", "text")
            for c in children:
                div.remove(c)
            if pb_elem is not None:
                div.append(pb_elem)
            if pre_sp:
                intro_div = ET.SubElement(div, f"{{{TEI_NS}}}div")
                intro_div.set("type", "text")
                for c in pre_sp:
                    intro_div.append(c)
            if sp_and_after:
                sp_div = ET.SubElement(div, f"{{{TEI_NS}}}div")
                sp_div.set("type", div_type)
                for c in sp_and_after:
                    sp_div.append(c)
            if div.get("type"):
                div.set("n", "1")
                del div.attrib["type"]

    # Fix 3b: Lose Inline-Elemente direkt in <div> -> in <p> einwickeln
    inline_tags = {"lb", "persName", "orgName", "placeName", "hi",
                   "foreign", "ref", "date", "num"}
    for div in list(root.iter(f"{{{TEI_NS}}}div")):
        _wrap_orphan_groups(
            div,
            is_orphan=lambda child: child.tag.replace(f"{{{TEI_NS}}}", "") in inline_tags,
            make_wrapper=lambda: _make_element(f"{{{TEI_NS}}}p", tail="\n"),
        )

    return _serialize_tei_fragment(root)


def fix_gemini_tei(xml_fragment: str) -> str:
    """Korrigiert haeufige Gemini-TEI-Fehler (Orchestrator).

    Pipeline: Regex-Fixes -> Struktur-Fixes -> Entity Re-Annotation.
    """
    xml_fragment = _fix_simple_patterns(xml_fragment)
    xml_fragment = _fix_structural_issues(xml_fragment)
    xml_fragment = reannotate_entities(xml_fragment)
    return xml_fragment


def process_page_step2(
    client,
    doc_id: str,
    page: int,
    scaffold_xml: str,
    metadata: dict,
    genre: str | None,
    doc_hints: str,
    dry_run: bool = False,
) -> str:
    """Step 2: Gemini Refinement einer Seite.

    Args:
        client: google.genai Client
        scaffold_xml: TEI-Fragment aus Step 1
        metadata: Dokument-Metadaten
        genre: Inferiertes Genre
        doc_hints: Dokumenttypspezifische Hints
        dry_run: Nur Prompt anzeigen, kein API-Call

    Returns:
        Angereichertes TEI-Fragment
    """
    ocr_text = load_ocr_text(doc_id, page) or ""
    total_pages = metadata.get("page_count", "?") if metadata else "?"

    doc_context = {
        "doc_id": doc_id,
        "page_num": page,
        "total_pages": total_pages,
        "genre": genre,
        "pub_form": metadata.get("pub_form", "other") if metadata else "other",
        "main_lang": metadata.get("lang", "und") if metadata else "und",
        "layout_type": metadata.get("type", "A") if metadata else "A",
        "title": metadata.get("title", doc_id) if metadata else doc_id,
        "author": metadata.get("author", "Jeanne Hersch") if metadata else "Jeanne Hersch",
        "date": metadata.get("date", "?") if metadata else "?",
        "doc_hints": doc_hints,
    }

    prompt = build_mapping_prompt(doc_context)
    input_block = build_refinement_input(scaffold_xml, ocr_text)
    full_prompt = prompt + "\n\n" + input_block

    if dry_run:
        print(f"  [DRY-RUN] Prompt fuer {doc_id} p{page}: {len(full_prompt)} chars")
        return scaffold_xml

    # Overlay-Bild laden
    overlay_path = get_overlay_path(doc_id, page)

    try:
        from google import genai
        from google.genai import types

        contents = []

        # Bild hinzufuegen falls vorhanden
        if overlay_path and overlay_path.exists():
            img_bytes = overlay_path.read_bytes()
            mime = "image/png"
            contents.append(types.Part.from_bytes(data=img_bytes, mime_type=mime))

        contents.append(types.Part.from_text(text=full_prompt))

        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=contents,
            config=types.GenerateContentConfig(
                temperature=0.1,
                max_output_tokens=8192,
            ),
        )

        result_text = response.text.strip()

        # XML-Bloecke extrahieren falls in Markdown-Fences
        xml_match = re.search(r'```xml\s*(.*?)\s*```', result_text, re.DOTALL)
        if xml_match:
            result_text = xml_match.group(1)

        # Well-formedness pruefen
        ET.fromstring(f"<root>{result_text}</root>")

        # Post-Processing: haeufige Gemini-Fehler korrigieren
        result_text = fix_gemini_tei(result_text)

        return result_text

    except ImportError as e:
        print(f"  FEHLER: google-genai nicht installiert: {e}")
        return scaffold_xml
    except ET.ParseError as e:
        print(f"  WARNUNG: Gemini-XML nicht wohlgeformt fuer {doc_id} p{page}: {e}")
        return fix_gemini_tei(scaffold_xml)
    except Exception as e:
        err_str = str(e).lower()
        if "api_key" in err_str or "auth" in err_str or "permission" in err_str:
            print(f"  FEHLER: Gemini-Auth-Fehler fuer {doc_id} p{page}: {e}")
            raise
        print(f"  WARNUNG: Gemini-Fehler fuer {doc_id} p{page}: {e}")
        return scaffold_xml


# ---------------------------------------------------------------------------
# Step 3: Document Assembly
# ---------------------------------------------------------------------------

def build_tei_header(doc_id: str, metadata: dict) -> str:
    """Erzeugt teiHeader mit biblStruct aus Metadaten."""
    title = xml_escape(metadata.get("title") or doc_id)
    author = xml_escape(metadata.get("author") or "Jeanne Hersch")
    date = xml_escape(metadata.get("date") or "")
    desc = xml_escape(metadata.get("desc") or "")
    pub_form = metadata.get("pub_form", "other")

    lang = metadata.get("lang", "und")
    if len(lang) != 3 or not lang.isalpha():
        lang_map = {"FR": "fra", "DE": "deu", "DE/FR": "fra", "?": "und"}
        lang = lang_map.get(lang, "und")

    lines = []
    lines.append("  <teiHeader>")
    lines.append("    <fileDesc>")
    lines.append("      <titleStmt>")
    lines.append(f'        <title type="main">{title}</title>')
    lines.append(f"        <author>{author}</author>")
    lines.append("      </titleStmt>")
    lines.append("      <publicationStmt>")
    lines.append("        <publisher>ZBZ / DHCraft</publisher>")
    lines.append(f'        <idno type="docID">{doc_id}</idno>')
    lines.append("      </publicationStmt>")
    lines.append("      <sourceDesc>")

    # biblStruct statt einfacher bibl
    if pub_form in ("journalArticle", "bookSection"):
        lines.append(f'        <biblStruct type="{pub_form}">')
        lines.append("          <analytic>")
        lines.append(f'            <title>{title}</title>')
        lines.append(f"            <author>{author}</author>")
        lines.append("          </analytic>")
        lines.append("          <monogr>")
        lines.append("            <title/>")
        lines.append("            <imprint>")
        lines.append(f"              <date>{date or 'unknown'}</date>")
        lines.append("            </imprint>")
        lines.append("          </monogr>")
        lines.append("        </biblStruct>")
    else:
        lines.append("        <bibl>")
        lines.append(f"          <title>{title}</title>")
        lines.append(f"          <author>{author}</author>")
        if date:
            lines.append(f"          <date>{date}</date>")
        lines.append("        </bibl>")

    lines.append("      </sourceDesc>")
    lines.append("    </fileDesc>")
    lines.append("    <profileDesc>")
    lines.append("      <langUsage>")
    lines.append(f'        <language ident="{lang}"/>')
    lines.append("      </langUsage>")
    lines.append("    </profileDesc>")
    lines.append("  </teiHeader>")

    return "\n".join(lines)


def build_facsimile(page_facsimiles: dict[int, dict]) -> str:
    """Erzeugt <facsimile> Element aus gesammelten Seitendaten."""
    if not page_facsimiles:
        return ""

    lines = ["  <facsimile>"]
    for page_num in sorted(page_facsimiles.keys()):
        facs = page_facsimiles[page_num]
        if not facs or not facs.get("zones"):
            continue
        img_w = facs.get("image_width", 0)
        img_h = facs.get("image_height", 0)
        lines.append(
            f'    <surface xml:id="facs_{page_num}" ulx="0" uly="0" '
            f'lrx="{img_w}" lry="{img_h}">'
        )
        for z in facs["zones"]:
            lines.append(
                f'      <zone xml:id="{z["zone_id"]}" '
                f'ulx="{z["ulx"]}" uly="{z["uly"]}" '
                f'lrx="{z["lrx"]}" lry="{z["lry"]}"/>'
            )
        lines.append("    </surface>")
    lines.append("  </facsimile>")

    return "\n".join(lines)


def assemble_document(
    doc_id: str,
    page_teis: dict[int, str],
    metadata: dict,
    page_facsimiles: dict[int, dict],
) -> str:
    """Step 3: Kombiniert Seiten-TEI-Fragmente zu komplettem Dokument."""
    lines = []
    lines.append('<?xml version="1.0" encoding="UTF-8"?>')
    lines.append('<TEI xmlns="http://www.tei-c.org/ns/1.0" type="naegeli">')

    # teiHeader
    lines.append(build_tei_header(doc_id, metadata))

    # facsimile
    facs = build_facsimile(page_facsimiles)
    if facs:
        lines.append(facs)

    # text/body
    lines.append("  <text>")
    lines.append("    <body>")

    for page_num in sorted(page_teis.keys()):
        fragment = page_teis[page_num]
        if fragment.strip():
            lines.append(fragment)

    lines.append("    </body>")
    lines.append("  </text>")
    lines.append("</TEI>")

    result = "\n".join(lines)

    # Post-Assembly Fix: verwaiste <p>/<figure>/<note> direkt in <body>
    # (ausserhalb <div>) in <div type="text"> einwickeln
    result = _fix_orphaned_body_children(result)

    # Post-Assembly Fix: Schema-Verletzungen nach Assembly korrigieren
    result = _fix_post_assembly_schema(result)

    return result


def _fix_post_assembly_schema(xml_text: str) -> str:
    """Post-Assembly-Fixes fuer RelaxNG-Schema-Verletzungen.

    Fix A: <graphic> ohne url-Attribut -> url="unknown" hinzufuegen
    Fix B: <p> innerhalb <head> -> Inhalt entpacken (Text beibehalten)
    Fix C: <epigraph> nach Content in <div> -> Inhalt entpacken (divTop-Regel)
    """
    try:
        ET.register_namespace("", TEI_NS)
        tree = ET.fromstring(xml_text)

        # Fix A: <graphic> ohne url -> url="unknown"
        for graphic in tree.iter(f"{{{TEI_NS}}}graphic"):
            if not graphic.get("url"):
                graphic.set("url", "unknown")

        # Fix B: <p> innerhalb <head> -> Inhalt als Text in <head>
        for head in list(tree.iter(f"{{{TEI_NS}}}head")):
            ps_in_head = head.findall(f"{{{TEI_NS}}}p")
            if not ps_in_head:
                continue
            for p in ps_in_head:
                # p-Inhalt (Text + Kinder) vor dem <p> einfuegen
                idx = list(head).index(p)
                p_text = p.text or ""
                p_children = list(p)
                # Text vor dem p anhaengen
                if idx == 0:
                    head.text = (head.text or "") + p_text
                else:
                    prev = list(head)[idx - 1]
                    prev.tail = (prev.tail or "") + p_text
                # Kinder des <p> nach oben verschieben
                for j, child in enumerate(p_children):
                    head.insert(idx + j, child)
                # Tail des <p> an letztes verschobenes Kind oder head.text
                p_tail = p.tail or ""
                if p_children:
                    last = p_children[-1]
                    last.tail = (last.tail or "") + p_tail
                elif idx == 0:
                    head.text = (head.text or "") + p_tail
                else:
                    prev = list(head)[idx - 1]
                    prev.tail = (prev.tail or "") + p_tail
                head.remove(p)

        # Fix C: <epigraph> nach Content in <div> -> entpacken
        for div in list(tree.iter(f"{{{TEI_NS}}}div")):
            children = list(div)
            any_content = False
            for child in children:
                tag = child.tag.replace(f"{{{TEI_NS}}}", "")
                if tag == "epigraph" and any_content:
                    idx = list(div).index(child)
                    inner = list(child)
                    # Epigraph-Text an erstes Kind oder als eigenes <p>
                    epi_text = (child.text or "").strip()
                    div.remove(child)
                    for j, ic in enumerate(inner):
                        div.insert(idx + j, ic)
                elif tag not in ("pb", "head"):
                    any_content = True

        return ET.tostring(tree, encoding="unicode", xml_declaration=True)
    except Exception:
        return xml_text



    """Wickelt verwaiste Block-Elemente in <body> und <div> in Sub-<div> ein.

    TEI-Regel: wenn ein <div> oder <body> bereits <div>-Kinder hat,
    duerfen keine <p>/<figure>/<note>/<sp> etc. als Geschwister stehen.
    Diese werden in <div type='text'> eingewickelt.
    """
    try:
        ET.register_namespace("", TEI_NS)
        tree = ET.fromstring(xml_text)

        block_tags = {"p", "figure", "note", "sp", "epigraph", "lg",
                      "table", "list", "ab", "bibl"}

        # Fix fuer body UND alle divs
        containers = [tree.find(f".//{{{TEI_NS}}}body")]
        containers.extend(tree.iter(f"{{{TEI_NS}}}div"))

        for container in containers:
            if container is None:
                continue
            children = list(container)

            has_div = any(c.tag == f"{{{TEI_NS}}}div" for c in children)
            has_blocks = any(
                c.tag.replace(f"{{{TEI_NS}}}", "") in block_tags
                for c in children
            )

            if not (has_div and has_blocks):
                continue

            def _make_text_div():
                div = _make_element(f"{{{TEI_NS}}}div", tail="\n", type="text")
                div.text = "\n"
                return div

            _wrap_orphan_groups(
                container,
                is_orphan=lambda c: c.tag.replace(f"{{{TEI_NS}}}", "") in block_tags,
                make_wrapper=_make_text_div,
            )

        return ET.tostring(tree, encoding="unicode", xml_declaration=True)
    except Exception:
        return xml_text


# ---------------------------------------------------------------------------
# Dokument-Verarbeitung (Orchestrierung)
# ---------------------------------------------------------------------------

def process_document(
    doc_id: str,
    max_step: int = 3,
    force: bool = False,
    dry_run: bool = False,
    validate: bool = False,
) -> dict:
    """Verarbeitet ein Dokument durch alle Pipeline-Schritte.

    Returns:
        Manifest-Dict mit Verarbeitungsstatistiken
    """
    start_time = time.time()

    # Metadaten laden
    metadata = get_document_metadata(doc_id) or {}

    # Erweiterte Metadaten aus doc_metadata.json
    raw_meta = _load_raw_metadata(doc_id)
    if raw_meta:
        metadata["has_jstor_cover"] = raw_meta.get("has_jstor_cover", False)
        metadata["page_count"] = raw_meta.get("page_count")

    # Genre und Hints
    lqa = _get_layout_qa()
    desc = metadata.get("desc", "")
    pub_form = metadata.get("pub_form", "other")
    genre = lqa.infer_genre(desc, pub_form)
    doc_hints = lqa.build_doc_hints(doc_id)

    # Seiten entdecken
    pages = discover_pages(doc_id)
    pages = skip_jstor_cover(pages, metadata)

    if not pages:
        print(f"  Keine Seiten fuer {doc_id}")
        return {"doc_id": doc_id, "status": "no_pages"}

    # Output-Verzeichnis
    doc_dir = TEI_UNIFIED_DIR / doc_id
    doc_dir.mkdir(parents=True, exist_ok=True)

    page_teis = {}
    page_facsimiles = {}
    step2_count = 0

    # Gemini-Client (nur fuer Step 2+)
    client = None
    if max_step >= 2 and not dry_run and GEMINI_API_KEY:
        try:
            from google import genai
            client = genai.Client(api_key=GEMINI_API_KEY)
        except Exception as e:
            print(f"  WARNUNG: Gemini-Client nicht verfuegbar: {e}")

    print(f"  Verarbeite {doc_id}: {len(pages)} Seiten, Genre={genre or 'standard'}")

    for page in pages:
        # Step 1: Enhanced Rule-Based TEI
        scaffold_path = doc_dir / f"{doc_id}_p{str(page).zfill(3)}_scaffold.xml"

        if scaffold_path.exists() and not force:
            scaffold = scaffold_path.read_text(encoding="utf-8")
            facs_json_path = doc_dir / f"{doc_id}_p{str(page).zfill(3)}_facs.json"
            if facs_json_path.exists():
                facs_data = json.loads(facs_json_path.read_text(encoding="utf-8"))
            else:
                facs_data = {}
        else:
            scaffold, facs_data = process_page_step1(doc_id, page, metadata, genre)
            if scaffold:
                scaffold_path.write_text(scaffold, encoding="utf-8")
                facs_json_path = doc_dir / f"{doc_id}_p{str(page).zfill(3)}_facs.json"
                facs_json_path.write_text(
                    json.dumps(facs_data, ensure_ascii=False), encoding="utf-8"
                )

        if not scaffold:
            continue

        page_facsimiles[page] = facs_data

        # Step 2: Gemini Refinement
        if max_step >= 2:
            refined_path = doc_dir / f"{doc_id}_p{str(page).zfill(3)}_refined.xml"

            if refined_path.exists() and not force:
                refined = refined_path.read_text(encoding="utf-8")
            elif client or dry_run:
                refined = process_page_step2(
                    client, doc_id, page, scaffold,
                    metadata, genre, doc_hints, dry_run
                )
                if not dry_run and refined:
                    refined_path.write_text(refined, encoding="utf-8")
                step2_count += 1

                # Rate-Limiting (Gemini Flash Lite)
                if not dry_run:
                    time.sleep(0.5)
            else:
                refined = scaffold

            page_teis[page] = refined
        else:
            page_teis[page] = scaffold

    # Step 3: Document Assembly
    if max_step >= 3 and page_teis:
        final_xml = assemble_document(doc_id, page_teis, metadata, page_facsimiles)
        final_path = doc_dir / f"{doc_id}_final.xml"
        final_path.write_text(final_xml, encoding="utf-8")
        print(f"    -> {final_path.name} ({len(final_xml)} chars)")

    # Step 4: Validation
    validation_result = None
    if validate and max_step >= 3:
        try:
            from scripts.tei.tei_validator import validate_tei_file
            final_path = doc_dir / f"{doc_id}_final.xml"
            if final_path.exists():
                validation_result = validate_tei_file(final_path)
                val_path = doc_dir / f"{doc_id}_validation.json"
                val_path.write_text(
                    json.dumps(validation_result, ensure_ascii=False, indent=2),
                    encoding="utf-8"
                )
                status = "VALID" if validation_result.get("valid") else "INVALID"
                n_errors = len(validation_result.get("errors", []))
                print(f"    Validation: {status} ({n_errors} errors)")
        except ImportError:
            print("    WARNUNG: tei_validator nicht verfuegbar")

    elapsed = time.time() - start_time

    # Manifest
    manifest = {
        "doc_id": doc_id,
        "genre": genre,
        "total_pages": len(pages),
        "pages_step1": len(page_teis),
        "pages_step2": step2_count,
        "has_final": (doc_dir / f"{doc_id}_final.xml").exists(),
        "elapsed_seconds": round(elapsed, 1),
        "max_step": max_step,
        "validation": validation_result,
    }
    manifest_path = doc_dir / f"{doc_id}_manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    return manifest


# ---------------------------------------------------------------------------
# Hilfsfunktionen
# ---------------------------------------------------------------------------

_raw_metadata_cache = None


def _load_raw_metadata(doc_id: str) -> dict | None:
    """Laedt Roh-Metadaten aus doc_metadata.json."""
    global _raw_metadata_cache
    if _raw_metadata_cache is None:
        if DOC_METADATA_PATH.exists():
            raw = json.loads(DOC_METADATA_PATH.read_text(encoding="utf-8"))
            _raw_metadata_cache = raw.get("documents", {})
        else:
            _raw_metadata_cache = {}
    return _raw_metadata_cache.get(str(doc_id))


def discover_documents() -> list[str]:
    """Findet alle Dokumente mit OCR-Daten."""
    doc_ids = set()
    for base_dir in [GEMINI_CORRECTED_B_DIR, GEMINI_CORRECTED_A_DIR,
                     LLM_CORRECTED_C_DIR, MISTRAL_RESULTS_DIR]:
        if base_dir.exists():
            for f in base_dir.glob("*_p*.md"):
                match = re.match(r'(\d+)_p\d+\.md$', f.name)
                if match:
                    doc_ids.add(match.group(1))
    return sorted(doc_ids)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

SAMPLE_DOCS = ["2310", "2530", "1440"]


def main():
    parser = argparse.ArgumentParser(
        description="Unified TEI Pipeline: Rule-Based + Gemini Refinement"
    )
    parser.add_argument("--doc", help="Einzelnes Dokument (z.B. 2310)")
    parser.add_argument("--sample", action="store_true",
                        help=f"Pilotdokumente: {', '.join(SAMPLE_DOCS)}")
    parser.add_argument("--all", action="store_true", help="Alle Dokumente")
    parser.add_argument("--step", type=int, default=3, choices=[1, 2, 3],
                        help="Maximaler Step (1=nur Rule-Based, 2=+Gemini, 3=+Assembly)")
    parser.add_argument("--validate", action="store_true",
                        help="Step 4: RelaxNG-Validierung")
    parser.add_argument("--force", action="store_true",
                        help="Gecachte Ergebnisse ueberschreiben")
    parser.add_argument("--dry-run", action="store_true",
                        help="Prompts anzeigen, keine API-Calls")
    args = parser.parse_args()

    print("=== Unified TEI Pipeline ===")
    print(f"  Step: 1-{args.step}"
          + (" + Validation" if args.validate else ""))

    if args.doc:
        doc_ids = [args.doc]
    elif args.sample:
        doc_ids = SAMPLE_DOCS
    elif args.all:
        doc_ids = discover_documents()
        print(f"  {len(doc_ids)} Dokumente gefunden")
    else:
        parser.print_help()
        return

    total_start = time.time()
    results = []

    for doc_id in doc_ids:
        print(f"\n--- Dokument {doc_id} ---")
        try:
            manifest = process_document(
                doc_id,
                max_step=args.step,
                force=args.force,
                dry_run=args.dry_run,
                validate=args.validate,
            )
            results.append(manifest)
        except Exception as e:
            print(f"  FEHLER: {e}")
            traceback.print_exc()
            results.append({"doc_id": doc_id, "status": "error", "error": str(e)})

    total_elapsed = time.time() - total_start

    # Zusammenfassung
    print(f"\n=== Zusammenfassung ===")
    print(f"  Dokumente: {len(results)}")
    ok = sum(1 for r in results if r.get("has_final"))
    print(f"  Erfolgreich: {ok}")
    total_pages = sum(r.get("pages_step1", 0) for r in results)
    print(f"  Seiten total: {total_pages}")
    step2_pages = sum(r.get("pages_step2", 0) for r in results)
    if step2_pages:
        print(f"  Gemini-Calls: {step2_pages}")
    print(f"  Dauer: {total_elapsed:.1f}s")
    print(f"  Output: {TEI_UNIFIED_DIR}")


if __name__ == "__main__":
    main()
