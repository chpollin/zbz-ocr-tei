#!/usr/bin/env python3
"""
Web image export: the local page PNGs (docs/images/, gitignored) as a JPEG mirror
for the public facsimile repo served from GitHub Pages.

Data flow: docs/images/{doc}/{doc}_pNNN.png -> output/web_images/{doc}/{doc}_pNNN.jpg.
Names and numbering stay identical, so the viewer only swaps base URL and extension
(ZBZ.path.image in docs/assets/js/core.js). Idempotent: existing JPEGs are skipped
unless --force. Usage:

    python -m scripts.edition.export_web_images            # all documents
    python -m scripts.edition.export_web_images --doc 2310
"""

import argparse
import sys
from pathlib import Path

from PIL import Image

from scripts.config import IMAGES_DIR, OUTPUT_DIR

WEB_IMAGES_DIR = OUTPUT_DIR / "web_images"
DEFAULT_QUALITY = 80


def jpeg_name(png_name: str) -> str:
    return Path(png_name).with_suffix(".jpg").name


def export_doc(doc_id: str, src_root: Path, out_root: Path, quality: int, force: bool) -> dict:
    src_dir = src_root / doc_id
    if not src_dir.is_dir():
        raise FileNotFoundError(f"no page images for {doc_id} under {src_root}")
    out_dir = out_root / doc_id
    out_dir.mkdir(parents=True, exist_ok=True)
    written = skipped = 0
    for png in sorted(src_dir.glob("*.png")):
        target = out_dir / jpeg_name(png.name)
        if target.exists() and not force:
            skipped += 1
            continue
        with Image.open(png) as im:
            im.convert("RGB").save(target, "JPEG", quality=quality, optimize=True)
        written += 1
    return {"doc_id": doc_id, "written": written, "skipped": skipped}


def main() -> int:
    parser = argparse.ArgumentParser(description="Export page PNGs as JPEG web mirror")
    parser.add_argument("--doc", help="single document id (default: all)")
    parser.add_argument("--out", type=Path, default=WEB_IMAGES_DIR)
    parser.add_argument("--quality", type=int, default=DEFAULT_QUALITY)
    parser.add_argument("--force", action="store_true", help="rewrite existing JPEGs")
    args = parser.parse_args()

    doc_ids = [args.doc] if args.doc else sorted(p.name for p in IMAGES_DIR.iterdir() if p.is_dir())
    errors = []
    total_written = total_skipped = 0
    for doc_id in doc_ids:
        try:
            r = export_doc(doc_id, IMAGES_DIR, args.out, args.quality, args.force)
        except (FileNotFoundError, OSError) as exc:
            errors.append({"doc_id": doc_id, "error": str(exc)})
            print(f"FEHLER {doc_id}: {exc}", file=sys.stderr)
            continue
        total_written += r["written"]
        total_skipped += r["skipped"]
        print(f"OK {doc_id}: {r['written']} written, {r['skipped']} skipped")
    print(f"Summe: {total_written} written, {total_skipped} skipped, {len(errors)} errors -> {args.out}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
