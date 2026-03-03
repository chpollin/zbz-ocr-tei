"""
Layout-Analyse via docling-serve API.

Sendet Seitenbilder (PNGs) an eine docling-serve Instanz (lokal oder Cloud)
und speichert Layout-JSONs im gleichen Format wie run_layout_analysis.py.

Voraussetzung: docling-serve laeuft (z.B. Docker):
    docker run -p 5001:5001 quay.io/docling-project/docling-serve-cpu

Usage:
    python -m scripts.run_layout_cloud                         # alle Dokumente
    python -m scripts.run_layout_cloud --doc 2310              # einzelnes Dokument
    python -m scripts.run_layout_cloud --url http://host:5001  # andere URL
    python -m scripts.run_layout_cloud --force                 # ueberschreibt existierende
"""

import argparse
import base64
import json
import time
from pathlib import Path

import requests

from scripts.config import IMAGES_DIR, LAYOUT_DIR, DOCLING_SERVE_URL
from scripts.run_layout_analysis import DOCLING_TO_ZBZ, to_pixel_pct


def check_server(url):
    """Prueft ob docling-serve erreichbar ist."""
    try:
        r = requests.get(f"{url}/health", timeout=5)
        return r.status_code == 200
    except requests.ConnectionError:
        return False


def send_image(img_path, url):
    """Sendet ein PNG an docling-serve und gibt die JSON-Response zurueck."""
    img_bytes = img_path.read_bytes()
    b64 = base64.b64encode(img_bytes).decode("ascii")

    payload = {
        "sources": [{
            "kind": "file",
            "base64_string": b64,
            "filename": img_path.name,
        }],
        "options": {
            "to_formats": ["json"],
            "from_formats": ["image"],
        },
    }

    r = requests.post(
        f"{url}/v1/convert/source",
        json=payload,
        timeout=120,
    )
    r.raise_for_status()
    return r.json()


def extract_regions(doc_json, page_dims):
    """Extrahiert Regionen aus dem Docling-Dokument-JSON (Einzelbild = Seite 1).

    Returns:
        Liste von Region-Dicts im Layout-JSON-Format
    """
    doc_w = page_dims.get("width", 1)
    doc_h = page_dims.get("height", 1)

    regions = []

    for item in doc_json.get("texts", []):
        label = item.get("label", "text")
        zbz_tag = DOCLING_TO_ZBZ.get(label, "zb_paragraph")
        if zbz_tag in ("_filter", "_skip"):
            continue

        text = (item.get("text", "") or "")[:100]

        bbox_pct = None
        prov_list = item.get("prov", [])
        if prov_list:
            bbox_data = prov_list[0].get("bbox", {})
            if bbox_data and "l" in bbox_data:
                bbox_pct = to_pixel_pct(bbox_data, doc_w, doc_h, doc_w, doc_h)

        regions.append({
            "label": label,
            "zbz_tag": zbz_tag,
            "text": text,
            "bbox": bbox_pct,
        })

    return regions


def process_page(img_path, out_path, url, force=False):
    """Einzelne Seite via API analysieren und JSON schreiben."""
    if out_path.exists() and not force:
        try:
            return json.loads(out_path.read_text(encoding="utf-8"))
        except Exception:
            pass

    t0 = time.time()
    response = send_image(img_path, url)
    elapsed = time.time() - t0

    doc_json = response["document"]["json_content"]

    # Seitendimensionen (Einzelbild = Seite 1)
    page_info = doc_json.get("pages", {}).get("1", {})
    page_size = page_info.get("size", {"width": 1, "height": 1})

    regions = extract_regions(doc_json, page_size)

    # Seitennummer aus Dateiname
    page_num = int(img_path.stem.split("_p")[1])

    result = {
        "doc_id": img_path.parent.name,
        "page": page_num,
        "image_width": round(page_size["width"]),
        "image_height": round(page_size["height"]),
        "elapsed_seconds": round(elapsed, 2),
        "num_regions": len(regions),
        "regions": regions,
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(result, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return result


def process_document(doc_id, url, force=False):
    """Alle Seiten eines Dokuments via API analysieren."""
    img_dir = IMAGES_DIR / doc_id
    out_dir = LAYOUT_DIR / doc_id

    images = sorted(img_dir.glob(f"{doc_id}_p*.png"))
    if not images:
        print(f"  Keine Bilder in {img_dir}")
        return None

    print(f"\n{'='*60}")
    print(f"Doc {doc_id}: {len(images)} Seiten")

    results = []
    for img_path in images:
        page_str = img_path.stem.split("_p")[1]
        out_path = out_dir / f"{doc_id}_p{page_str}_layout.json"

        if out_path.exists() and not force:
            print(f"  SKIP: {out_path.name}")
            try:
                results.append(json.loads(out_path.read_text(encoding="utf-8")))
            except Exception:
                pass
            continue

        try:
            r = process_page(img_path, out_path, url, force)
            if r:
                print(f"  OK: {out_path.name} ({r['num_regions']} Regionen, {r['elapsed_seconds']:.1f}s)")
                results.append(r)
        except requests.RequestException as e:
            print(f"  FEHLER: {img_path.name}: {e}")

    # Summary
    type_counts = {}
    total_regions = 0
    total_time = 0.0
    for r in results:
        total_regions += r["num_regions"]
        total_time += r.get("elapsed_seconds", 0)
        for region in r.get("regions", []):
            tag = region["zbz_tag"]
            type_counts[tag] = type_counts.get(tag, 0) + 1

    summary = {
        "doc_id": doc_id,
        "pages_analyzed": len(results),
        "total_regions": total_regions,
        "total_time_seconds": round(total_time, 2),
        "type_counts": type_counts,
        "source": "docling-serve",
    }

    summary_path = out_dir / "summary.json"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"  Summary: {total_regions} Regionen, {total_time:.1f}s")

    return summary


def main():
    parser = argparse.ArgumentParser(description="Layout-Analyse via docling-serve API")
    parser.add_argument("--doc", type=str, help="Einzelnes Dokument (doc_id)")
    parser.add_argument("--url", type=str, default=DOCLING_SERVE_URL,
                        help=f"docling-serve URL (default: {DOCLING_SERVE_URL})")
    parser.add_argument("--force", action="store_true",
                        help="Existierende ueberschreiben")
    args = parser.parse_args()

    # Server-Check
    print(f"docling-serve URL: {args.url}")
    if not check_server(args.url):
        print(f"\nFEHLER: docling-serve nicht erreichbar unter {args.url}")
        print("Starte den Server z.B. mit:")
        print("  docker run -p 5001:5001 quay.io/docling-project/docling-serve-cpu")
        return

    print("Server erreichbar.\n")

    # Dokument-IDs bestimmen
    if args.doc:
        doc_ids = [args.doc]
    else:
        doc_ids = sorted([
            d.name for d in IMAGES_DIR.iterdir()
            if d.is_dir() and not d.name.startswith(".")
        ])

    print(f"Layout-Analyse fuer {len(doc_ids)} Dokumente...")

    summaries = []
    t_start = time.time()

    for i, doc_id in enumerate(doc_ids, 1):
        print(f"\n[{i}/{len(doc_ids)}] {doc_id}")
        s = process_document(doc_id, args.url, args.force)
        if s:
            summaries.append(s)

    t_total = time.time() - t_start
    print(f"\n{'='*60}")
    print(f"FERTIG: {len(summaries)} Dokumente, "
          f"{sum(s['total_regions'] for s in summaries)} Regionen, "
          f"{t_total:.1f}s")


if __name__ == "__main__":
    main()
