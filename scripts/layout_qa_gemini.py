"""
Gemini Layout QA: Docling-Ergebnisse mit Gemini 3.1 Flash Lite korrigieren.

Sendet Overlay-PNG + Layout-JSON an Gemini Vision, bekommt korrigiertes JSON zurueck.
Beide Versionen (Docling-Original + Gemini-korrigiert) bleiben erhalten.

Output:
    output/layout/{doc_id}/{doc_id}_p{NNN}_layout_gemini.json   # Gemini-korrigiert
    output/layout/{doc_id}/summary_gemini.json                  # QA-Summary

Usage:
    python -m scripts.layout_qa_gemini                     # alle Docs mit Layout
    python -m scripts.layout_qa_gemini --doc 2310          # einzelnes Doc
    python -m scripts.layout_qa_gemini --force             # ueberschreibt existierende
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
from PIL import Image

from scripts.config import GEMINI_API_KEY, GEMINI_MODEL, IMAGES_DIR, LAYOUT_DIR
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


def process_document(client, doc_id, force=False):
    """Alle Seiten eines Dokuments mit Gemini QA pruefen."""
    layout_dir = LAYOUT_DIR / doc_id

    if not layout_dir.exists():
        return None

    # Alle Layout-JSONs finden
    layout_files = sorted(layout_dir.glob(f"{doc_id}_p*_layout.json"))
    # _layout_gemini.json ausschliessen
    layout_files = [f for f in layout_files if "_gemini" not in f.name]

    if not layout_files:
        return None

    print(f"\n{'='*60}")
    print(f"Gemini QA fuer Doc {doc_id}: {len(layout_files)} Seiten")

    results = []
    for lf in layout_files:
        # Seitennummer extrahieren: {doc_id}_p{NNN}_layout.json
        page_str = lf.stem.replace(f"{doc_id}_p", "").replace("_layout", "")
        r = qa_page(client, doc_id, page_str, force)
        if r:
            results.append(r)

    if not results:
        return None

    # Summary erzeugen
    scores = [r.get("score", 0) for r in results]
    total_corrections = sum(r.get("num_corrections", 0) for r in results)
    pages_with_issues = []
    all_issues = []

    for r in results:
        issues = r.get("issues", [])
        if issues:
            pages_with_issues.append(f"p{r.get('page', '?'):03d}")
            all_issues.extend(issues)

    # Haeufigste Issues
    issue_counts = {}
    for issue in all_issues:
        issue_counts[issue] = issue_counts.get(issue, 0) + 1
    common_issues = sorted(issue_counts.keys(), key=lambda k: -issue_counts[k])[:5]

    summary = {
        "doc_id": doc_id,
        "pages_evaluated": len(results),
        "avg_score": round(sum(scores) / len(scores), 1) if scores else 0,
        "total_corrections": total_corrections,
        "pages_with_issues": pages_with_issues,
        "common_issues": common_issues,
        "model": GEMINI_MODEL,
    }

    summary_path = layout_dir / "summary_gemini.json"
    summary_path.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(f"  Summary: Score {summary['avg_score']}, {total_corrections} Korrekturen")
    if common_issues:
        print(f"  Issues: {', '.join(common_issues[:3])}")

    return summary


def main():
    parser = argparse.ArgumentParser(description="Gemini Layout QA")
    parser.add_argument("--doc", type=str, help="Einzelnes Dokument (doc_id)")
    parser.add_argument("--force", action="store_true", help="Existierende ueberschreiben")
    args = parser.parse_args()

    client = get_client()

    if args.doc:
        doc_ids = [args.doc]
    else:
        # Alle Docs mit Layout-Daten
        doc_ids = discover_doc_ids(LAYOUT_DIR)

    print(f"Gemini Layout QA fuer {len(doc_ids)} Dokumente...")
    print(f"Model: {GEMINI_MODEL}")

    summaries = []
    for doc_id in doc_ids:
        s = process_document(client, doc_id, args.force)
        if s:
            summaries.append(s)

    if summaries:
        avg_score = sum(s["avg_score"] for s in summaries) / len(summaries)
        total_corr = sum(s["total_corrections"] for s in summaries)
        print(f"\n{'='*60}")
        print(f"FERTIG: {len(summaries)} Dokumente, Avg Score: {avg_score:.1f}, {total_corr} Korrekturen")


if __name__ == "__main__":
    main()
