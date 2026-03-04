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
    python -m scripts.layout_qa_gemini                              # QA (default)
    python -m scripts.layout_qa_gemini --mode detect --doc 510      # Detect einzeln
    python -m scripts.layout_qa_gemini --mode auto                  # Auto (detect/qa)
    python -m scripts.layout_qa_gemini --force                      # ueberschreibt
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
from PIL import Image

from scripts.config import (
    DOCLING_TO_ZBZ, GEMINI_API_KEY, GEMINI_DETECT_MODEL, GEMINI_MODEL,
    IMAGES_DIR, LAYOUT_DIR,
)
from scripts.layout import draw_overlay_from_json
from scripts.utils import discover_doc_ids

# .env laden
load_dotenv()

# API Key aus .env (Reload nach dotenv)
_api_key = os.environ.get("GEMINI_API_KEY", "") or GEMINI_API_KEY

PROMPT = """You are a strict layout QA reviewer for scanned pages from the \
Jeanne Hersch Edition (ZBZ Zurich, 20th century academic texts, \
primarily French/German). Your job is to AGGRESSIVELY correct mistakes.

IMAGE: The overlay shows colored bounding boxes detected by Docling.
JSON: The layout regions with labels, zbz_tags, and bounding boxes \
(x_pct, y_pct, w_pct, h_pct as percentage of image dimensions).

Label-to-zbz_tag mapping (MUST be consistent):
  title/section_header -> zb_heading
  text/paragraph/list_item/table/formula -> zb_paragraph
  footnote -> footnote
  caption -> caption
  page_header/page_footer -> _filter
  picture/figure -> _skip

COMMON MISTAKES TO FIX (be aggressive):
1. PAGE NUMBERS (e.g. "567", "12") labeled as "text" -> change to "page_footer" / _filter
2. RUNNING HEADERS (e.g. "Analyses et comptes rendus", journal titles at top) \
   labeled as "text" -> change to "page_header" / _filter
3. SECTION HEADINGS (titles, author names in caps, bibliographic entries with \
   author+title+publisher) labeled as "text" -> change to "section_header" / zb_heading
4. AUTHOR SIGNATURES (e.g. "Jeanne HERSCH.", name at end of review) labeled as \
   "text" -> keep as "text" but note it in issues
5. FOOTNOTE MARKERS or footnote text at bottom of page labeled as "text" \
   -> change to "footnote"
6. Remove false positives (boxes around empty space, artifacts, logos)
7. Very small regions (<2% height) that contain only a page number or header \
   -> change to page_header/page_footer

RULES:
- Do NOT change bounding box coordinates
- DO change labels and zbz_tags aggressively when wrong
- Set changed=true and explain WHY in change_reason
- Score 0-100: deduct 10 points per wrong label, 5 per minor issue
- Be thorough: check EVERY region against what you see in the image"""

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
- For LANDSCAPE or DOUBLE-PAGE scans: treat each page/column independently
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


def get_client():
    """Gemini Client erstellen."""
    from google import genai

    if not _api_key:
        print("FEHLER: GEMINI_API_KEY nicht gesetzt. Bitte in .env eintragen.")
        sys.exit(1)

    return genai.Client(api_key=_api_key)


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

    # Layout-JSON als Text (nur Regionen)
    layout_text = json.dumps(layout_data.get("regions", []), indent=2)

    # An Gemini senden
    t0 = time.time()
    try:
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=[image, PROMPT + "\n\nLayout JSON:\n" + layout_text],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=QA_SCHEMA,
            ),
        )
        elapsed = time.time() - t0

        result = json.loads(response.text)
    except Exception as e:
        elapsed = time.time() - t0
        print(f"  FEHLER: {doc_id}_p{page_str}: {e} ({elapsed:.1f}s)")
        return None

    # Metadaten hinzufuegen
    result["doc_id"] = doc_id
    result["page"] = int(page_str)
    result["elapsed_seconds"] = round(elapsed, 2)
    result["model"] = GEMINI_MODEL
    result["source"] = "gemini"

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

    # An Gemini senden
    t0 = time.time()
    try:
        response = client.models.generate_content(
            model=GEMINI_DETECT_MODEL,
            contents=[image, DETECT_PROMPT],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=DETECT_SCHEMA,
            ),
        )
        elapsed = time.time() - t0
        raw_result = json.loads(response.text)
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
