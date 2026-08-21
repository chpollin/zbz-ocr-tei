"""
Gemini Layout QA + Detect: Layout-Ergebnisse korrigieren oder neu erkennen.

Zwei Modi:
  qa     - Label-Korrektur auf Docling-Ergebnissen (bestehendes Verhalten)
  detect - Vollstaendige Layout-Erkennung vom Scan-Bild (fuer schlechte Docling-Seiten)
  auto   - Automatisch: detect fuer schlechte Seiten, qa fuer gute

Output:
    output/layout/{doc_id}/{doc_id}_p{NNN}_layout_gemini.json   # Gemini-Ergebnis
    output/layout/{doc_id}/summary_gemini.json                  # Summary

Usage:
    python -m scripts.layout.layout_qa_gemini                              # QA (default)
    python -m scripts.layout.layout_qa_gemini --mode detect --doc 510      # Detect einzeln
    python -m scripts.layout.layout_qa_gemini --mode auto                  # Auto (detect/qa)
    python -m scripts.layout.layout_qa_gemini --force                      # ueberschreibt
"""

import argparse
import json
import time
import warnings

# Suppress Gemini SDK thought_signature warnings
warnings.filterwarnings("ignore", message=".*non-text parts.*thought_signature.*")

from PIL import Image

from scripts.config import (
    DOC_METADATA_PATH,
    DOCLING_TO_ZBZ,
    GEMINI_DETECT_MODEL,
    GEMINI_MODEL,
    IMAGES_DIR,
    LAYOUT_DIR,
)
from scripts.core.gemini import get_client
from scripts.layout.overlay import draw_overlay_from_json
from scripts.utils import discover_doc_ids

# ---- Dokumenttypspezifische Prompt-Hints (4 Ebenen) ----

# doc_metadata.json laden (global, einmalig)
_doc_metadata = {}
if DOC_METADATA_PATH.exists():
    try:
        _raw = json.loads(DOC_METADATA_PATH.read_text(encoding="utf-8"))
        _doc_metadata = _raw.get("documents", _raw)
    except Exception:
        pass

# Ebene 1: Layout-Typ
LAYOUT_TYPE_HINTS = {
    "A": "LAYOUT: Single-column flowing text. Focus: distinguish headings from body text, detect footnotes at bottom of page.",
    "B": "LAYOUT: TWO-COLUMN layout. CRITICAL: detect each column separately as independent text regions. Process left column first (top-to-bottom), then right column. Do NOT merge text across columns into one region. Column gutter is typically at ~50% page width. LANDSCAPE WARNING: If the page is wider than tall, there may be THREE or more columns -- scan the ENTIRE width and do NOT stop after two columns. The RIGHTMOST column is frequently missed.",
    "C": "LAYOUT: Monograph/book chapter (long document, many pages). Expect: running headers at top (-> page_header/_filter), chapter headings, continuous body paragraphs. Page numbers at bottom (-> page_footer/_filter).",
    "D": "LAYOUT: Special/complex format. Examine carefully: may contain interviews (speaker names in bold/caps), illustrations, historical print, newspaper-style multi-article pages, mixed column layouts, or unusual formatting. LANDSCAPE/WIDE PAGES: If the scan appears wider than tall, it may be a double-page spread -- detect regions on BOTH halves independently. Check the right half for missed text columns.",
}

# Ebene 2: Publikationsform
PUB_FORM_HINTS = {
    "journalArticle": "FORMAT: Journal article -- expect running header with journal name or section title at top of page, page numbers at top or bottom.",
    "book": "FORMAT: Book/monograph -- expect chapter structure, possibly table of contents, running headers with chapter title.",
    "bookSection": "FORMAT: Contribution in edited volume -- typically starts with title + author name, then body text. May have section numbering.",
    "brochure": "FORMAT: Brochure/pamphlet -- shorter text, may have different formatting, possibly with organizational logos.",
    "interview": "FORMAT: INTERVIEW -- expect speaker names (often in bold, CAPS, or followed by colon/dash) alternating with response text. Detect speaker labels as section_header, NOT as regular text.",
    "encyclopedia": "FORMAT: ENCYCLOPEDIA entry -- expect lemma heading in bold/caps, structured sub-sections (definition, biography, works, bibliography). Dense, reference-style text. Often TWO or THREE narrow columns per page -- detect EACH column as separate text regions. Do not merge adjacent columns.",
    "anthology": "FORMAT: Anthology contribution -- title + author header, then essay body text.",
    "other": "FORMAT: Non-standard format -- examine layout carefully for structural patterns.",
}

# Ebene 3: Genre (abgeleitet aus description)
GENRE_HINTS = {
    "newspaper": "GENRE: NEWSPAPER PAGE -- multiple independent articles on one page, each with its own heading. Detect article boundaries carefully. Very complex layout possible (mixed column widths, boxes, adverts).",
    "interview": "GENRE: INTERVIEW -- speaker names appear before each turn (often bold, CAPS, or followed by colon/dash). Each speaker turn should be detected as a separate text region. Speaker labels should be section_header.",
    "review": "GENRE: BOOK REVIEW -- typically starts with a bibliographic entry (author, title, publisher, year, pages) as a heading block. The review text follows as body paragraphs.",
    "debate": "GENRE: DEBATE/ROUNDTABLE -- multiple speakers, similar to interview but with more participants. Speaker names mark each contribution.",
    "speech": "GENRE: SPEECH/LECTURE transcript -- usually continuous flowing text with few structural divisions. May have been transcribed from oral presentation.",
    "conference": "GENRE: CONFERENCE PAPER -- may have abstract block, section numbering, extensive footnotes. Possibly bilingual (abstract in another language).",
    "preface": "GENRE: PREFACE/FOREWORD -- short introductory meta-text. May reference the main work's author and title.",
    "letter": "GENRE: LETTER -- has salutation at top, body text, and closing formula with signature. May have date and addressee header.",
    "encyclopedia": "GENRE: ENCYCLOPEDIA ENTRY -- structured with lemma heading, sub-sections for definition, biography, bibliography. Dense reference-style text with cross-references.",
    "editorial": "GENRE: EDITORIAL -- short opinion text, usually at beginning of journal issue.",
}

# Ebene 4: Sprach-Hints
LANGUAGE_HINTS = {
    "fra": "LANGUAGE: French text -- watch for guillemets (<< >>), accents (e/e/e), spaces before :;?! (French typographic convention).",
    "deu": "LANGUAGE: German text -- watch for umlauts (ae/oe/ue), eszett (ss), long compound words.",
    "eng": "LANGUAGE: English text.",
    "ita": "LANGUAGE: Italian text -- watch for accents and apostrophes.",
    "multilingual": "LANGUAGE: MULTILINGUAL document ({languages}) -- text switches between languages. Different sections may have different formatting. Watch for language boundaries.",
}


def infer_genre(description, pub_form):
    """Genre aus Beschreibung + pub_form ableiten."""
    if not description:
        return None
    desc = description.lower()

    # pub_form hat Vorrang fuer bestimmte Typen
    if pub_form == "interview":
        return "interview"
    if pub_form == "encyclopedia":
        return "encyclopedia"

    # Keyword-Matching auf description
    if "newspaper" in desc or "journal de gen" in desc or "zeitung" in desc:
        return "newspaper"
    if "interview" in desc or "entretien" in desc:
        return "interview"
    if "review" in desc or "compte rendu" in desc or "rezension" in desc or "book review" in desc:
        return "review"
    if "roundtable" in desc or "debate" in desc or "discussion" in desc or "dialogue" in desc:
        return "debate"
    if "speech" in desc or "lecture" in desc or "vortrag" in desc or "address" in desc or "rede" in desc:
        return "speech"
    if "conference" in desc or "congress" in desc or "proceedings" in desc or "colloquium" in desc:
        return "conference"
    if "preface" in desc or "foreword" in desc or "introduction" in desc or "vorwort" in desc:
        return "preface"
    if "letter" in desc or "brief" in desc:
        return "letter"
    if "encyclopedia" in desc or "lexicon" in desc or "dictionnaire" in desc:
        return "encyclopedia"
    if "editorial" in desc:
        return "editorial"

    return None


def build_doc_hints(doc_id):
    """Dokumenttypspezifische Prompt-Erweiterung zusammenbauen."""
    meta = _doc_metadata.get(str(doc_id), {})
    if not meta:
        return ""

    hints = []

    # Ebene 1: Layout-Typ
    layout_type = meta.get("layout_type", "")
    if layout_type in LAYOUT_TYPE_HINTS:
        hints.append(LAYOUT_TYPE_HINTS[layout_type])

    # Ebene 2: Publikationsform
    pub_form = meta.get("pub_form", "")
    if pub_form in PUB_FORM_HINTS:
        hints.append(PUB_FORM_HINTS[pub_form])

    # Ebene 3: Genre
    genre = infer_genre(meta.get("description", ""), pub_form)
    if genre and genre in GENRE_HINTS:
        hints.append(GENRE_HINTS[genre])

    # Ebene 4: Sprache
    language = meta.get("language", "")
    if "/" in language:
        hint = LANGUAGE_HINTS["multilingual"].replace("{languages}", language)
        hints.append(hint)
    elif language in LANGUAGE_HINTS:
        hints.append(LANGUAGE_HINTS[language])

    if not hints:
        return ""

    return "\n\nDOCUMENT-SPECIFIC CONTEXT:\n" + "\n".join(hints)

PROMPT = """\
You review layout regions on scanned pages (Jeanne Hersch Edition, ZBZ Zurich, \
academic French/German texts).

INPUT: Overlay image with colored bounding boxes + JSON with regions.

LABEL MAPPING (enforce strictly):
  section_header -> zb_heading | text -> zb_paragraph | footnote -> footnote
  caption -> caption | page_header/page_footer -> _filter | picture -> _skip

TASK 1 — FIX WRONG LABELS:
- Page numbers ("567") as text -> page_footer/_filter
- Running headers (journal name at top) as text -> page_header/_filter
- Headings, titles, bibliographic entries as text -> section_header/zb_heading
- Footnotes at page bottom as text -> footnote
- Empty/artifact regions -> _filter

TASK 2 — ADD MISSING REGIONS:
Look at the image for visible text NOT covered by any existing box. Add with:
- bbox as page % (x_pct, y_pct, w_pct, h_pct). All values 0-100.
- page_header: ALWAYS y_pct 0-5. page_footer: ALWAYS y_pct 88-100.
- text: first few visible words (max 50 chars)
- changed: true, change_reason: "ADDED: ..."
Check especially: top/bottom of page, gaps between boxes, column tops.
CRITICAL for multi-column layouts: Verify the RIGHTMOST column has been detected. \
Scan from the right edge of the page leftward -- if there is text in the rightmost \
30% of the page without a bounding box, ADD it as a new region.

PICTURE/FIGURE DETECTION:
- Photographs, illustrations, portraits, logos, decorative elements -> "picture"
- Graphs, charts, diagrams with data -> "picture"
- Blank areas with only a frame/border are NOT pictures -> _filter
- Text inside a framed box is still "text", not "picture"

OUTPUT:
- Return ALL regions (existing unchanged + corrected + new)
- Existing regions: keep original text and bbox EXACTLY as provided
- Only change label and zbz_tag on existing regions
- changed=true ONLY for label changes or new regions
- Score 0-100: deduct 10 per wrong or missing label"""

# JSON Schema fuer Structured Output
QA_SCHEMA = {
    "type": "object",
    "properties": {
        "regions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "label": {"type": "string"},
                    "zbz_tag": {"type": "string"},
                    "text": {"type": "string"},
                    "bbox": {
                        "type": "object",
                        "nullable": True,
                        "properties": {
                            "x_pct": {"type": "number"},
                            "y_pct": {"type": "number"},
                            "w_pct": {"type": "number"},
                            "h_pct": {"type": "number"},
                        },
                    },
                    "changed": {"type": "boolean"},
                    "change_reason": {"type": "string"},
                },
                "required": ["label", "zbz_tag", "text"],
            },
        },
        "score": {"type": "integer", "description": "Quality score 0-100"},
        "num_corrections": {"type": "integer"},
        "issues": {
            "type": "array",
            "items": {"type": "string"},
        },
    },
    "required": ["regions", "score", "num_corrections", "issues"],
}

# ---- Detect Mode: Full layout detection from scan image ----

DETECT_PROMPT = """You are a document layout analysis expert for scanned pages from the \
Jeanne Hersch Edition (ZBZ Zurich, 20th century academic texts, \
primarily French/German).

Detect ALL text and structural regions in this scanned page image. \
For each region, provide a bounding box and a label.

Labels (use exactly these):
  "section_header" - headings, chapter titles, author names in large/bold/caps
  "text" - body paragraphs, regular text blocks, bibliographic entries
  "footnote" - footnotes at the bottom of the page (smaller font, separated)
  "caption" - figure or table captions
  "page_header" - running headers at the top (journal title, section name, page range)
  "page_footer" - page numbers at the bottom
  "picture" - images, illustrations, logos, photographs
  "table" - tabular content with rows and columns
  "list_item" - enumerated or bulleted list entries

RULES:
- Detect EVERY visible text region, even small ones (page numbers, headers)
- Each bounding box should tightly enclose its text content
- For MULTI-COLUMN layouts: detect each column's text blocks SEPARATELY
- For LANDSCAPE or DOUBLE-PAGE scans: treat each page/column independently. \
CRITICAL: scan the FULL WIDTH of the image. The rightmost column or right-side \
page is frequently missed -- explicitly check x > 60% of image width for \
uncovered text regions.
- Order regions in reading order: top-to-bottom, left-to-right
- Do NOT merge separate paragraphs into one region
- Do NOT miss paragraphs between other detected regions
- Separate headings from body text (different regions)
- Page numbers at top or bottom are page_header or page_footer"""

DETECT_SCHEMA = {
    "type": "object",
    "properties": {
        "regions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "box_2d": {
                        "type": "array",
                        "items": {"type": "integer"},
                    },
                    "label": {"type": "string"},
                },
                "required": ["box_2d", "label"],
            },
        },
        "page_orientation": {"type": "string"},
        "num_columns": {"type": "integer"},
    },
    "required": ["regions"],
}


def _validate_bbox(bbox):
    """Clip bbox coordinates to valid 0-100 range."""
    if not bbox:
        return bbox
    return {
        "x_pct": round(max(0, min(100, bbox.get("x_pct", 0))), 3),
        "y_pct": round(max(0, min(100, bbox.get("y_pct", 0))), 3),
        "w_pct": round(max(0, min(100, bbox.get("w_pct", 0))), 3),
        "h_pct": round(max(0, min(100, bbox.get("h_pct", 0))), 3),
    }


def compute_page_quality(layout_data):
    """Docling-Layout-Qualitaet bewerten.

    Returns (quality, coverage, num_regions).
    quality: 'good', 'warning', 'bad', or 'empty'
    """
    regions = layout_data.get("regions", [])
    num_regions = len(regions)

    if num_regions == 0:
        return "empty", 0.0, 0

    coverage = sum(
        r["bbox"]["h_pct"] * r["bbox"]["w_pct"] / 100
        for r in regions
        if r.get("bbox")
    )

    if coverage < 15:
        return "bad", round(coverage, 1), num_regions
    if num_regions <= 2 and coverage < 30:
        return "bad", round(coverage, 1), num_regions
    if coverage < 30:
        return "warning", round(coverage, 1), num_regions

    return "good", round(coverage, 1), num_regions


def gemini_box_to_pct(box_2d):
    """Gemini [ymin, xmin, ymax, xmax] (0-1000) -> {x_pct, y_pct, w_pct, h_pct} (0-100)."""
    ymin, xmin, ymax, xmax = box_2d
    return {
        "x_pct": round(xmin / 10.0, 3),
        "y_pct": round(ymin / 10.0, 3),
        "w_pct": round(max(0, xmax - xmin) / 10.0, 3),
        "h_pct": round(max(0, ymax - ymin) / 10.0, 3),
    }


def _extract_response_text(response):
    """Extract text from Gemini response, handling thought_signature parts."""
    if response.text is not None:
        return response.text
    # Fallback: manually search for text parts in candidates
    try:
        for candidate in response.candidates:
            for part in candidate.content.parts:
                if hasattr(part, "text") and part.text:
                    return part.text
    except (AttributeError, IndexError, TypeError):
        pass
    return None


def ensure_overlay(doc_id, page_str):
    """Overlay-PNG erzeugen falls nicht vorhanden. Gibt Pfad zurueck."""
    overlay_path = LAYOUT_DIR / doc_id / f"{doc_id}_p{page_str}_overlay.png"

    if overlay_path.exists():
        return overlay_path

    # Overlay aus Layout-JSON + Originalbild erzeugen
    img_path = IMAGES_DIR / doc_id / f"{doc_id}_p{page_str}.png"
    json_path = LAYOUT_DIR / doc_id / f"{doc_id}_p{page_str}_layout.json"

    if not img_path.exists() or not json_path.exists():
        return None

    layout_data = json.loads(json_path.read_text(encoding="utf-8"))
    draw_overlay_from_json(img_path, layout_data, overlay_path)
    return overlay_path


def qa_page(client, doc_id, page_str, force=False):
    """Eine Seite mit Gemini QA pruefen."""
    from google.genai import types

    gemini_path = LAYOUT_DIR / doc_id / f"{doc_id}_p{page_str}_layout_gemini.json"

    if gemini_path.exists() and not force:
        print(f"  SKIP: {gemini_path.name}")
        try:
            return json.loads(gemini_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            print(f"  WARN: defektes Cache {gemini_path.name}: {e}")

    # Layout-JSON laden
    json_path = LAYOUT_DIR / doc_id / f"{doc_id}_p{page_str}_layout.json"
    if not json_path.exists():
        print(f"  SKIP: {json_path.name} nicht vorhanden")
        return None

    layout_data = json.loads(json_path.read_text(encoding="utf-8"))

    # Overlay erzeugen/laden
    overlay_path = ensure_overlay(doc_id, page_str)
    if not overlay_path:
        print(f"  SKIP: Overlay fuer {doc_id}_p{page_str} nicht erzeugbar")
        return None

    # Bild laden
    image = Image.open(overlay_path)

    # Layout-JSON als Text (nur Regionen, Text auf 50 Zeichen kuerzen um
    # Gemini Recitation-Filter zu vermeiden)
    regions = layout_data.get("regions", [])
    truncated_regions = []
    for r in regions:
        tr = dict(r)
        if "text" in tr and len(tr["text"]) > 50:
            tr["text"] = tr["text"][:50] + "..."
        truncated_regions.append(tr)
    layout_text = json.dumps(truncated_regions, indent=2)

    # Typspezifische Prompt-Erweiterung
    doc_hints = build_doc_hints(doc_id)
    full_prompt = PROMPT + doc_hints + "\n\nLayout JSON:\n" + layout_text

    # An Gemini senden (mit 1 Retry bei leerer Antwort)
    t0 = time.time()
    try:
        config = types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=QA_SCHEMA,
            thinking_config=types.ThinkingConfig(thinking_budget=0),
        )
        for attempt in range(2):
            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=[image, full_prompt],
                config=config,
            )
            text = _extract_response_text(response)
            if text is not None:
                break
            if attempt == 0:
                print(f"  RETRY: {doc_id}_p{page_str} (empty response)")
        elapsed = time.time() - t0

        if text is None:
            raise ValueError("Gemini returned empty response after retry")
        result = json.loads(text)
    except Exception as e:
        elapsed = time.time() - t0
        print(f"  FEHLER: {doc_id}_p{page_str}: {e} ({elapsed:.1f}s)")
        return None

    # -- Post-Processing: Text-Schutz + Bbox-Fixes --

    # Index der Original-Regionen nach Bbox-Schluessel
    def _bbox_key(r):
        b = r.get("bbox", {})
        return (b.get("x_pct"), b.get("y_pct"), b.get("w_pct"), b.get("h_pct"))

    original_text = {_bbox_key(r): r.get("text", "") for r in regions}

    valid_regions = []
    for region in result.get("regions", []):
        bbox = region.get("bbox")
        if bbox:
            region["bbox"] = _validate_bbox(bbox)
            if region["bbox"]["w_pct"] <= 0 or region["bbox"]["h_pct"] <= 0:
                continue

        is_added = region.get("change_reason", "").startswith("ADDED")

        # Text-Schutz: Original-Text wiederherstellen (ausser bei ADDED)
        if not is_added:
            key = _bbox_key(region)
            if key in original_text:
                region["text"] = original_text[key]

        # Bbox-Anker: ADDED page_header muss oben sein, page_footer unten
        if is_added and bbox:
            label = region.get("label", "")
            if label == "page_header" and region["bbox"]["y_pct"] > 10:
                region["bbox"]["y_pct"] = 2.0
                region["bbox"]["h_pct"] = 2.0
            elif label == "page_footer" and region["bbox"]["y_pct"] < 85:
                region["bbox"]["y_pct"] = 93.0
                region["bbox"]["h_pct"] = 3.0

        valid_regions.append(region)
    result["regions"] = valid_regions

    # -- Changes-Summary: Label-Transitions zaehlen --
    changes_summary = {}
    added_count = 0
    for region in valid_regions:
        reason = region.get("change_reason", "")
        if not region.get("changed"):
            continue
        if reason.startswith("ADDED"):
            added_count += 1
        elif "→" in reason or "->" in reason:
            # z.B. "LABEL CORRECTION: text→section_header"
            changes_summary[reason] = changes_summary.get(reason, 0) + 1
        else:
            changes_summary[reason] = changes_summary.get(reason, 0) + 1
    if added_count:
        changes_summary["ADDED"] = added_count

    # Metadaten hinzufuegen
    result["doc_id"] = doc_id
    result["page"] = int(page_str)
    result["elapsed_seconds"] = round(elapsed, 2)
    result["model"] = GEMINI_MODEL
    result["source"] = "gemini"
    if changes_summary:
        result["changes_summary"] = changes_summary

    # Speichern
    gemini_path.parent.mkdir(parents=True, exist_ok=True)
    gemini_path.write_text(
        json.dumps(result, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    corrections = result.get("num_corrections", 0)
    score = result.get("score", "?")
    print(f"  OK: {gemini_path.name} (Score: {score}, Korrekturen: {corrections}, {elapsed:.1f}s)")

    return result


def detect_page(client, doc_id, page_str, force=False):
    """Layout-Regionen vollstaendig neu erkennen mit Gemini Vision."""
    from google.genai import types

    gemini_path = LAYOUT_DIR / doc_id / f"{doc_id}_p{page_str}_layout_gemini.json"

    if gemini_path.exists() and not force:
        print(f"  SKIP: {gemini_path.name}")
        try:
            return json.loads(gemini_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            print(f"  WARN: defektes Cache {gemini_path.name}: {e}")

    # RAW-Scan laden (kein Overlay)
    img_path = IMAGES_DIR / doc_id / f"{doc_id}_p{page_str}.png"
    if not img_path.exists():
        print(f"  SKIP: {img_path.name} nicht vorhanden")
        return None

    image = Image.open(img_path)
    img_w, img_h = image.size

    # Typspezifische Prompt-Erweiterung
    doc_hints = build_doc_hints(doc_id)
    full_prompt = DETECT_PROMPT + doc_hints

    # An Gemini senden
    t0 = time.time()
    try:
        config = types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=DETECT_SCHEMA,
            thinking_config=types.ThinkingConfig(thinking_budget=0),
        )
        for attempt in range(2):
            response = client.models.generate_content(
                model=GEMINI_DETECT_MODEL,
                contents=[image, full_prompt],
                config=config,
            )
            text = _extract_response_text(response)
            if text is not None:
                break
            if attempt == 0:
                print(f"  RETRY: {doc_id}_p{page_str} (empty response)")
        elapsed = time.time() - t0
        if text is None:
            raise ValueError("Gemini returned empty response after retry")
        raw_result = json.loads(text)
    except Exception as e:
        elapsed = time.time() - t0
        print(f"  FEHLER: {doc_id}_p{page_str}: {e} ({elapsed:.1f}s)")
        return None

    # Gemini-Format -> Projekt-Format konvertieren
    regions = []
    for r in raw_result.get("regions", []):
        box_2d = r.get("box_2d", [])
        if len(box_2d) != 4:
            continue

        label = r.get("label", "text")
        zbz_tag = DOCLING_TO_ZBZ.get(label, "zb_paragraph")

        regions.append({
            "label": label,
            "zbz_tag": zbz_tag,
            "text": "",
            "bbox": gemini_box_to_pct(box_2d),
        })

    # Label-Verteilung fuer Detect-Modus
    label_counts = {}
    for r in regions:
        lbl = r.get("label", "text")
        label_counts[lbl] = label_counts.get(lbl, 0) + 1

    result = {
        "doc_id": doc_id,
        "page": int(page_str),
        "image_width": img_w,
        "image_height": img_h,
        "num_regions": len(regions),
        "regions": regions,
        "elapsed_seconds": round(elapsed, 2),
        "model": GEMINI_DETECT_MODEL,
        "source": "gemini-detect",
        "page_orientation": raw_result.get("page_orientation", "unknown"),
        "num_columns": raw_result.get("num_columns", 1),
        "label_counts": label_counts,
    }

    # Speichern
    gemini_path.parent.mkdir(parents=True, exist_ok=True)
    gemini_path.write_text(
        json.dumps(result, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    orient = result.get("page_orientation", "?")
    cols = result.get("num_columns", "?")
    print(f"  OK: {gemini_path.name} (Detect: {len(regions)} Regionen, {orient}/{cols}col, {elapsed:.1f}s)")

    return result


def process_document(client, doc_id, force=False, mode="qa"):
    """Alle Seiten eines Dokuments verarbeiten.

    mode: 'qa' (Label-Korrektur), 'detect' (vollstaendige Erkennung), 'auto'
    """
    layout_dir = LAYOUT_DIR / doc_id
    img_dir = IMAGES_DIR / doc_id

    # Seiten ermitteln
    if mode == "detect":
        # Detect braucht nur Bilder, keine Docling-Layouts
        if not img_dir.exists():
            return None
        image_files = sorted(img_dir.glob(f"{doc_id}_p*.png"))
        if not image_files:
            return None
        pages = [f.stem.split("_p")[1] for f in image_files]
    else:
        # QA/Auto braucht Docling-Layout-Dateien
        if not layout_dir.exists():
            return None
        layout_files = sorted(layout_dir.glob(f"{doc_id}_p*_layout.json"))
        layout_files = [f for f in layout_files if "_gemini" not in f.name]
        if not layout_files:
            return None
        pages = [lf.stem.replace(f"{doc_id}_p", "").replace("_layout", "") for lf in layout_files]

    print(f"\n{'='*60}")
    print(f"Gemini {mode.upper()} fuer Doc {doc_id}: {len(pages)} Seiten")

    results = []
    detect_count = 0
    qa_count = 0

    for page_str in pages:
        page_mode = mode

        if mode == "auto":
            json_path = layout_dir / f"{doc_id}_p{page_str}_layout.json"
            if json_path.exists():
                layout_data = json.loads(json_path.read_text(encoding="utf-8"))
                quality, coverage, n_reg = compute_page_quality(layout_data)
                if quality in ("bad", "empty"):
                    page_mode = "detect"
                    print(f"  AUTO p{page_str}: DETECT (quality={quality}, coverage={coverage}%, regions={n_reg})")
                else:
                    page_mode = "qa"
            else:
                page_mode = "detect"
                print(f"  AUTO p{page_str}: DETECT (kein Docling-Layout)")

        if page_mode == "detect":
            r = detect_page(client, doc_id, page_str, force)
            detect_count += 1
        else:
            r = qa_page(client, doc_id, page_str, force)
            qa_count += 1

        if r:
            results.append(r)

    if not results:
        return None

    # Summary erzeugen
    total_regions = sum(r.get("num_regions", len(r.get("regions", []))) for r in results)

    # QA-spezifische Metriken
    scores = [r.get("score", 0) for r in results if "score" in r]
    total_corrections = sum(r.get("num_corrections", 0) for r in results)
    pages_with_issues = []
    all_issues = []

    for r in results:
        issues = r.get("issues", [])
        if issues:
            pages_with_issues.append(f"p{r.get('page', '?'):03d}")
            all_issues.extend(issues)

    issue_counts = {}
    for issue in all_issues:
        issue_counts[issue] = issue_counts.get(issue, 0) + 1
    common_issues = sorted(issue_counts.keys(), key=lambda k: -issue_counts[k])[:5]

    # Aggregierte Changes-Summary und Label-Counts
    agg_changes = {}
    agg_labels = {}
    for r in results:
        for key, cnt in r.get("changes_summary", {}).items():
            agg_changes[key] = agg_changes.get(key, 0) + cnt
        for key, cnt in r.get("label_counts", {}).items():
            agg_labels[key] = agg_labels.get(key, 0) + cnt

    model = GEMINI_DETECT_MODEL if mode in ("detect", "auto") else GEMINI_MODEL
    summary = {
        "doc_id": doc_id,
        "mode": mode,
        "pages_evaluated": len(results),
        "total_regions": total_regions,
        "detect_pages": detect_count,
        "qa_pages": qa_count,
        "avg_score": round(sum(scores) / len(scores), 1) if scores else 0,
        "total_corrections": total_corrections,
        "pages_with_issues": pages_with_issues,
        "common_issues": common_issues,
        "model": model,
    }
    if agg_changes:
        summary["changes_summary"] = agg_changes
    if agg_labels:
        summary["label_counts"] = agg_labels

    summary_path = layout_dir / "summary_gemini.json"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(f"  Summary: {total_regions} Regionen, {detect_count} detect / {qa_count} qa")
    if scores:
        print(f"  QA Score: {summary['avg_score']}, {total_corrections} Korrekturen")
    if common_issues:
        print(f"  Issues: {', '.join(common_issues[:3])}")

    return summary


def main():
    parser = argparse.ArgumentParser(description="Gemini Layout QA + Detect")
    parser.add_argument("--doc", type=str, help="Einzelnes Dokument (doc_id)")
    parser.add_argument("--force", action="store_true", help="Existierende ueberschreiben")
    parser.add_argument(
        "--mode", choices=["qa", "detect", "auto"], default="qa",
        help="qa=Label-Korrektur, detect=volle Erkennung, auto=detect fuer schlechte Seiten",
    )
    args = parser.parse_args()

    client = get_client()

    if args.doc:
        doc_ids = [args.doc]
    elif args.mode == "detect":
        # Detect: Bilder-Verzeichnis durchsuchen
        doc_ids = discover_doc_ids(IMAGES_DIR)
    else:
        # QA/Auto: Layout-Verzeichnis durchsuchen
        doc_ids = discover_doc_ids(LAYOUT_DIR)

    model_name = GEMINI_DETECT_MODEL if args.mode in ("detect", "auto") else GEMINI_MODEL
    print(f"Gemini Layout {args.mode.upper()} fuer {len(doc_ids)} Dokumente...")
    print(f"Model: {model_name}")

    summaries = []
    for doc_id in doc_ids:
        s = process_document(client, doc_id, args.force, mode=args.mode)
        if s:
            summaries.append(s)

    if summaries:
        total_regions = sum(s.get("total_regions", 0) for s in summaries)
        total_detect = sum(s.get("detect_pages", 0) for s in summaries)
        total_qa = sum(s.get("qa_pages", 0) for s in summaries)
        print(f"\n{'='*60}")
        print(f"FERTIG: {len(summaries)} Dokumente, {total_regions} Regionen")
        print(f"  Detect: {total_detect} Seiten, QA: {total_qa} Seiten")


if __name__ == "__main__":
    main()
