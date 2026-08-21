"""
Batch Layout-Analyse: Docling auf alle Seitenbilder.

Erzeugt pro Seite eine JSON-Datei in output/layout/{doc_id}/{doc_id}_p{NNN}_layout.json
Erzeugt pro Dokument eine summary.json in output/layout/{doc_id}/summary.json

Mit --overlay: Erzeugt annotierte PNG-Bilder mit eingebrannten BBox-Overlays
  Output: output/layout/{doc_id}/{doc_id}_p{NNN}_overlay.png

Usage:
    python -m scripts.layout.run_layout_analysis                      # alle Dokumente
    python -m scripts.layout.run_layout_analysis --doc 2310           # einzelnes Dokument
    python -m scripts.layout.run_layout_analysis --overlay            # nur Overlay-PNGs erzeugen
    python -m scripts.layout.run_layout_analysis --overlay --doc 2310 # Overlay fuer ein Dokument
    python -m scripts.layout.run_layout_analysis --force              # ueberschreibt existierende
"""

import argparse
import json
import os
import time
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

from PIL import Image

from scripts.config import DOCLING_TO_ZBZ, IMAGES_DIR, LAYOUT_DIR
from scripts.layout.overlay import draw_overlay_from_json, to_pixel_pct
from scripts.utils import discover_doc_ids, extract_page_num

# Lazy Docling converter
_converter = None


def get_converter():
    """Lazy-load DocumentConverter (Docling ist schwer)."""
    global _converter
    if _converter is None:
        from docling.document_converter import DocumentConverter
        _converter = DocumentConverter()
    return _converter


def analyze_page(img_path: Path) -> dict:
    """Docling Layout-Analyse auf einem einzelnen Seitenbild."""
    converter = get_converter()

    t0 = time.time()
    result = converter.convert(str(img_path))
    elapsed = time.time() - t0

    doc = result.document
    items = list(doc.iterate_items())

    regions = []
    for item, level in items:
        label = getattr(item, "label", type(item).__name__)
        text = (getattr(item, "text", "") or "")[:200]
        bbox = None
        if hasattr(item, "prov") and item.prov:
            p = item.prov[0]
            if hasattr(p, "bbox"):
                b = p.bbox
                bbox = {"l": round(b.l, 1), "t": round(b.t, 1),
                        "r": round(b.r, 1), "b": round(b.b, 1)}

        zbz_tag = DOCLING_TO_ZBZ.get(label, "zb_paragraph")
        regions.append({
            "label": label,
            "zbz_tag": zbz_tag,
            "level": level,
            "text": text,
            "bbox": bbox,
        })

    # Seitendimensionen
    page_info = {}
    for page_no, page in doc.pages.items():
        page_info[str(page_no)] = {
            "width": round(page.size.width, 1),
            "height": round(page.size.height, 1),
        }

    return {
        "elapsed_seconds": round(elapsed, 2),
        "num_regions": len(regions),
        "pages": page_info,
        "regions": regions,
    }


def process_page(img_path: Path, output_path: Path, force: bool = False):
    """Einzelne Seite analysieren und JSON schreiben."""
    if output_path.exists() and not force:
        # Existierende Daten laden fuer Summary-Aggregation
        try:
            return json.loads(output_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            print(f"  WARN: defektes Cache {output_path.name}: {e}")

    # Bilddimensionen
    with Image.open(img_path) as img:
        img_w, img_h = img.size

    # Docling-Analyse
    raw = analyze_page(img_path)

    # Seitendimensionen aus Docling
    page_info = list(raw["pages"].values())
    doc_w = page_info[0]["width"] if page_info else img_w
    doc_h = page_info[0]["height"] if page_info else img_h

    # Regionen konvertieren
    regions = []
    for r in raw["regions"]:
        zbz_tag = r["zbz_tag"]
        if zbz_tag in ("_filter", "_skip"):
            continue

        region = {
            "label": r["label"],
            "zbz_tag": zbz_tag,
            "text": r["text"][:100],
        }

        if r["bbox"]:
            region["bbox"] = to_pixel_pct(r["bbox"], doc_w, doc_h, img_w, img_h)
        else:
            region["bbox"] = None

        regions.append(region)

    # Seitennummer aus Dateiname extrahieren
    page_num = extract_page_num(img_path.name)

    result = {
        "doc_id": img_path.parent.name,
        "page": page_num,
        "image_width": img_w,
        "image_height": img_h,
        "elapsed_seconds": raw["elapsed_seconds"],
        "num_regions": len(regions),
        "regions": regions,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(result, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return result


def process_document(doc_id: str, force: bool = False):
    """Alle Seiten eines Dokuments analysieren + summary.json schreiben."""
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

        skip = out_path.exists() and not force
        if skip:
            print(f"  SKIP: {out_path.name}")

        r = process_page(img_path, out_path, force)
        if r:
            if not skip:
                print(f"  OK: {out_path.name} ({r['num_regions']} Regionen, {r.get('elapsed_seconds', 0):.1f}s)")
            results.append(r)

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
    }

    summary_path = out_dir / "summary.json"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"  Summary: {total_regions} Regionen, {total_time:.1f}s")
    print(f"  Typen: {type_counts}")

    return summary


def generate_overlays(doc_id: str, force: bool = False):
    """Erzeugt annotierte Overlay-PNGs fuer alle Seiten eines Dokuments.

    Liest existierende Layout-JSONs und zeichnet BBoxes auf Originalbilder.
    Braucht KEINE erneute Docling-Analyse.
    """
    img_dir = IMAGES_DIR / doc_id
    layout_dir = LAYOUT_DIR / doc_id

    if not layout_dir.exists():
        print(f"  Kein Layout-Verzeichnis: {layout_dir}")
        return 0

    images = sorted(img_dir.glob(f"{doc_id}_p*.png"))
    if not images:
        print(f"  Keine Bilder in {img_dir}")
        return 0

    print(f"\n{'='*60}")
    print(f"Overlay-PNGs fuer Doc {doc_id}: {len(images)} Seiten")

    count = 0
    for img_path in images:
        page_str = img_path.stem.split("_p")[1]
        json_path = layout_dir / f"{doc_id}_p{page_str}_layout.json"
        overlay_path = layout_dir / f"{doc_id}_p{page_str}_overlay.png"

        if overlay_path.exists() and not force:
            print(f"  SKIP: {overlay_path.name}")
            count += 1
            continue

        if not json_path.exists():
            print(f"  SKIP: {json_path.name} nicht vorhanden")
            continue

        try:
            layout_data = json.loads(json_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            print(f"  FEHLER: {json_path.name}: {e}")
            continue

        draw_overlay_from_json(img_path, layout_data, overlay_path)
        print(f"  OK: {overlay_path.name} ({len(layout_data.get('regions', []))} Regionen)")
        count += 1

    print(f"  Gesamt: {count} Overlay-PNGs")
    return count


def main():
    parser = argparse.ArgumentParser(description="Batch Docling Layout-Analyse")
    parser.add_argument("--doc", type=str, help="Einzelnes Dokument (doc_id)")
    parser.add_argument("--force", action="store_true", help="Existierende ueberschreiben")
    parser.add_argument("--overlay", action="store_true",
                        help="Nur Overlay-PNGs erzeugen (keine Docling-Analyse)")
    args = parser.parse_args()

    doc_ids = [args.doc] if args.doc else discover_doc_ids(IMAGES_DIR)

    if args.overlay:
        # Nur Overlay-PNGs erzeugen (aus existierenden Layout-JSONs)
        print(f"Overlay-PNGs fuer {len(doc_ids)} Dokumente...")
        total = 0
        for doc_id in doc_ids:
            total += generate_overlays(doc_id, args.force)
        print(f"\n{'='*60}")
        print(f"FERTIG: {total} Overlay-PNGs erzeugt")
    else:
        # Docling Layout-Analyse
        print(f"Layout-Analyse fuer {len(doc_ids)} Dokumente...")
        summaries = []
        for doc_id in doc_ids:
            s = process_document(doc_id, args.force)
            if s:
                summaries.append(s)

        print(f"\n{'='*60}")
        print(f"FERTIG: {len(summaries)} Dokumente, "
              f"{sum(s['total_regions'] for s in summaries)} Regionen, "
              f"{sum(s['total_time_seconds'] for s in summaries):.1f}s")


if __name__ == "__main__":
    main()
