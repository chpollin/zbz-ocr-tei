"""
Phase 0 Layout-Evaluation: Docling auf 5 Typenstichproben.

Verarbeitet je 1 Seite aus Type A (1180), B (2530), C (40), D (90), D (1330).
Erzeugt JSON mit Layout-Regionen + visuelle Ueberlagerung als PNG.

Usage:
    python scripts/experiments/layout_eval.py
    python scripts/experiments/layout_eval.py --doc 1180
"""

import argparse
import json
import os
import time
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

from PIL import Image, ImageDraw, ImageFont

# Lazy import - Docling is heavy
_converter = None


def get_converter():
    global _converter
    if _converter is None:
        from docling.document_converter import DocumentConverter
        _converter = DocumentConverter()
    return _converter


# Test-Bilder: doc_id -> (image_file, doc_type, description)
TEST_IMAGES = {
    "1180": ("docs/images/1180/1180_p002.png", "A", "Jahresbericht einspaltig DE/FR"),
    "2530": ("docs/images/2530/2530_p001.png", "B", "Zeitschrift zweispaltig FR"),
    "40":   ("docs/images/40/40_p002.png",     "C", "Roman/Monografie FR"),
    "90":   ("docs/images/90/90_p001.png",     "D", "Historisch 1944 DE"),
    "1330": ("docs/images/1330/1330_p001.png",  "D", "Sammelband FR"),
}

# Farben pro Label (RGB)
LABEL_COLORS = {
    "section_header": (255, 0, 0),       # Rot
    "title":          (255, 0, 0),       # Rot
    "text":           (0, 128, 0),       # Gruen
    "paragraph":      (0, 128, 0),       # Gruen
    "list_item":      (0, 128, 0),       # Gruen
    "footnote":       (0, 0, 255),       # Blau
    "caption":        (255, 165, 0),     # Orange
    "picture":        (128, 0, 128),     # Lila
    "figure":         (128, 0, 128),     # Lila
    "table":          (0, 128, 128),     # Teal
    "page_header":    (128, 128, 128),   # Grau
    "page_footer":    (128, 128, 128),   # Grau
    "formula":        (255, 0, 255),     # Magenta
}

# ZBZ-Tag-Mapping
DOCLING_TO_ZBZ = {
    "title":          "zb_heading",
    "section_header": "zb_heading",
    "text":           "zb_paragraph",
    "paragraph":      "zb_paragraph",
    "list_item":      "zb_paragraph",
    "footnote":       "footnote",
    "caption":        "caption",
    "page_header":    "_filter",
    "page_footer":    "_filter",
    "picture":        "_skip",
    "figure":         "_skip",
    "table":          "zb_paragraph",
    "formula":        "zb_paragraph",
}


def analyze_image(img_path: Path) -> dict:
    """Run Docling layout analysis on a single image."""
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

    # Page dimensions
    page_info = {}
    for page_no, page in doc.pages.items():
        page_info[str(page_no)] = {
            "width": round(page.size.width, 1),
            "height": round(page.size.height, 1),
        }

    return {
        "image": str(img_path),
        "elapsed_seconds": round(elapsed, 2),
        "num_regions": len(regions),
        "pages": page_info,
        "regions": regions,
    }


def draw_overlay(img_path: Path, analysis: dict, output_path: Path):
    """Draw BBox overlay on the image and save as PNG."""
    img = Image.open(img_path).convert("RGB")
    draw = ImageDraw.Draw(img, "RGBA")
    img_w, img_h = img.size

    # Docling coords are in points (72 DPI). Images are 150 DPI.
    # Scale factor: image_pixels / docling_points
    page_info = list(analysis["pages"].values())
    if not page_info:
        img.save(output_path)
        return

    doc_w = page_info[0]["width"]
    doc_h = page_info[0]["height"]
    scale_x = img_w / doc_w if doc_w > 0 else 1
    scale_y = img_h / doc_h if doc_h > 0 else 1

    for region in analysis["regions"]:
        bbox = region.get("bbox")
        if not bbox:
            continue

        label = region["label"]
        zbz = region["zbz_tag"]
        color = LABEL_COLORS.get(label, (100, 100, 100))

        # Docling uses (l, t, r, b) but t/b might be inverted (origin bottom-left)
        x1 = bbox["l"] * scale_x
        x2 = bbox["r"] * scale_x
        # Docling origin is bottom-left, PIL is top-left
        y1 = (doc_h - bbox["t"]) * scale_y
        y2 = (doc_h - bbox["b"]) * scale_y
        if y1 > y2:
            y1, y2 = y2, y1

        # Draw filled rectangle with transparency
        fill_color = color + (40,)
        draw.rectangle([x1, y1, x2, y2], outline=color, fill=fill_color, width=2)

        # Label text
        label_text = f"{label} -> {zbz}"
        draw.text((x1 + 2, y1 + 2), label_text, fill=color)

    img.save(output_path)
    print(f"  Overlay: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Phase 0 Layout-Evaluation")
    parser.add_argument("--doc", type=str, help="Single doc_id to test")
    args = parser.parse_args()

    project_root = Path(__file__).parent.parent.parent
    output_dir = project_root / "output" / "layout_eval"
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.doc:
        if args.doc not in TEST_IMAGES:
            print(f"Unknown doc: {args.doc}. Available: {list(TEST_IMAGES.keys())}")
            return
        test_set = {args.doc: TEST_IMAGES[args.doc]}
    else:
        test_set = TEST_IMAGES

    all_results = {}

    for doc_id, (img_rel, doc_type, desc) in test_set.items():
        img_path = project_root / img_rel
        print(f"\n{'='*60}")
        print(f"Doc {doc_id} (Type {doc_type}): {desc}")
        print(f"Image: {img_path}")

        if not img_path.exists():
            print(f"  SKIP: Image not found")
            continue

        analysis = analyze_image(img_path)
        print(f"  Time: {analysis['elapsed_seconds']}s")
        print(f"  Regions: {analysis['num_regions']}")

        for r in analysis["regions"]:
            bbox_str = ""
            if r["bbox"]:
                b = r["bbox"]
                bbox_str = f" ({b['l']:.0f},{b['t']:.0f},{b['r']:.0f},{b['b']:.0f})"
            print(f"    {r['label']:20s} -> {r['zbz_tag']:15s} \"{r['text'][:50]}\"{bbox_str}")

        # Save JSON
        json_path = output_dir / f"{doc_id}_layout.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(analysis, f, indent=2, ensure_ascii=False)
        print(f"  JSON: {json_path}")

        # Save overlay
        overlay_path = output_dir / f"{doc_id}_overlay.png"
        draw_overlay(img_path, analysis, overlay_path)

        all_results[doc_id] = analysis

    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    for doc_id, analysis in all_results.items():
        img_rel, doc_type, desc = TEST_IMAGES[doc_id]
        labels = [r["label"] for r in analysis["regions"]]
        label_counts = {}
        for l in labels:
            label_counts[l] = label_counts.get(l, 0) + 1
        print(f"  {doc_id} (Type {doc_type}): {analysis['num_regions']} regions, "
              f"{analysis['elapsed_seconds']}s -- {label_counts}")


if __name__ == "__main__":
    main()
