"""
Layout-Overlay-Bilder erzeugen: Gemini-Ergebnisse auf Scan-Bilder zeichnen.

Erzeugt fuer jede Seite ein PNG mit farbigen Bounding-Boxen aus dem
Gemini-Layout-JSON. Optional: Side-by-side-Vergleich Docling vs. Gemini.

Output:
    output/layout/{doc_id}/{doc_id}_p{NNN}_overlay_gemini.png
    output/layout/{doc_id}/{doc_id}_p{NNN}_overlay_compare.png  (--compare)

Usage:
    python -m scripts.layout.generate_layout_overlays                  # Alle Docs
    python -m scripts.layout.generate_layout_overlays --doc 2310       # Einzelnes Doc
    python -m scripts.layout.generate_layout_overlays --compare        # Mit Vergleichsbildern
    python -m scripts.layout.generate_layout_overlays --force          # Ueberschreiben
"""

import argparse
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from scripts.config import IMAGES_DIR, LABEL_COLORS, LAYOUT_DIR
from scripts.core.loaders import discover_layout_documents


def draw_overlay_with_changes(img_path, layout_json, output_path):
    """Overlay mit Changed-Highlighting (gelb gestrichelt fuer geaenderte Regionen)."""
    img = Image.open(img_path).convert("RGB")
    draw = ImageDraw.Draw(img, "RGBA")
    img_w, img_h = img.size

    try:
        font = ImageFont.truetype("arial.ttf", 14)
    except (OSError, IOError):
        font = ImageFont.load_default()

    try:
        font_small = ImageFont.truetype("arial.ttf", 11)
    except (OSError, IOError):
        font_small = font

    for region in layout_json.get("regions", []):
        bbox = region.get("bbox")
        if not bbox:
            continue

        label = region.get("label", "text")
        zbz_tag = region.get("zbz_tag", "zb_paragraph")
        text_preview = region.get("text", "")[:60]
        is_changed = region.get("changed", False)
        change_reason = region.get("change_reason", "")
        is_added = change_reason.startswith("ADDED")

        color = LABEL_COLORS.get(label, (100, 100, 100))

        # Prozent -> Pixel
        x1 = bbox["x_pct"] / 100.0 * img_w
        y1 = bbox["y_pct"] / 100.0 * img_h
        w = bbox["w_pct"] / 100.0 * img_w
        h = bbox["h_pct"] / 100.0 * img_h
        x2 = x1 + w
        y2 = y1 + h

        if is_added:
            # ADDED: gelber Rahmen, keine Fuellung
            draw.rectangle([x1, y1, x2, y2], outline=(234, 179, 8), width=3)
            label_text = f"ADDED: {label}"
            draw.text((x1 + 3, y1 + 3), label_text, fill=(234, 179, 8), font=font)
        elif is_changed:
            # Geaendert: orange Rahmen
            fill_color = (234, 179, 8, 30)
            draw.rectangle([x1, y1, x2, y2], outline=(234, 179, 8), fill=fill_color, width=2)
            label_text = f"* {label} -> {zbz_tag}"
            draw.text((x1 + 3, y1 + 3), label_text, fill=(234, 179, 8), font=font)
            if change_reason and h > 35:
                draw.text((x1 + 3, y1 + 18), change_reason[:70], fill=(180, 140, 0), font=font_small)
        else:
            # Unveraendert: normale Farbe
            fill_color = color + (40,)
            draw.rectangle([x1, y1, x2, y2], outline=color, fill=fill_color, width=2)
            label_text = f"{label} -> {zbz_tag}"
            draw.text((x1 + 3, y1 + 3), label_text, fill=color, font=font)

        # Text-Vorschau
        if text_preview and h > 50 and not is_added:
            y_text = y1 + 33 if is_changed else y1 + 18
            draw.text((x1 + 3, y_text), text_preview, fill=color, font=font_small)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path)


def create_compare_image(img_path, docling_json, gemini_json, output_path):
    """Side-by-side: Docling (links) vs. Gemini (rechts)."""
    img = Image.open(img_path).convert("RGB")
    img_w, img_h = img.size

    # Zwei Kopien erstellen
    img_docling = img.copy()
    img_gemini = img.copy()

    draw_d = ImageDraw.Draw(img_docling, "RGBA")
    draw_g = ImageDraw.Draw(img_gemini, "RGBA")

    try:
        font = ImageFont.truetype("arial.ttf", 14)
        font_title = ImageFont.truetype("arial.ttf", 20)
    except (OSError, IOError):
        font = ImageFont.load_default()
        font_title = font

    def _draw_regions(draw_ctx, layout_json):
        for region in layout_json.get("regions", []):
            bbox = region.get("bbox")
            if not bbox:
                continue
            label = region.get("label", "text")
            color = LABEL_COLORS.get(label, (100, 100, 100))
            x1 = bbox["x_pct"] / 100.0 * img_w
            y1 = bbox["y_pct"] / 100.0 * img_h
            w = bbox["w_pct"] / 100.0 * img_w
            h = bbox["h_pct"] / 100.0 * img_h
            fill_color = color + (40,)
            draw_ctx.rectangle([x1, y1, x1 + w, y1 + h], outline=color, fill=fill_color, width=2)
            draw_ctx.text((x1 + 3, y1 + 3), label, fill=color, font=font)

    _draw_regions(draw_d, docling_json)
    _draw_regions(draw_g, gemini_json)

    # Titel-Banner
    draw_d.rectangle([0, 0, img_w, 28], fill=(0, 0, 0, 180))
    draw_d.text((8, 4), "DOCLING", fill=(255, 255, 255), font=font_title)

    draw_g.rectangle([0, 0, img_w, 28], fill=(0, 0, 0, 180))
    draw_g.text((8, 4), "GEMINI", fill=(234, 179, 8), font=font_title)

    # Regionen-Count
    n_doc = len([r for r in docling_json.get("regions", []) if r.get("bbox")])
    n_gem = len([r for r in gemini_json.get("regions", []) if r.get("bbox")])
    draw_d.text((img_w - 100, 4), f"{n_doc} Regionen", fill=(200, 200, 200), font=font)
    draw_g.text((img_w - 100, 4), f"{n_gem} Regionen", fill=(200, 200, 200), font=font)

    # Zusammenfuegen: Docling links, Gemini rechts, 4px Trennlinie
    gap = 4
    combined = Image.new("RGB", (img_w * 2 + gap, img_h), (40, 40, 40))
    combined.paste(img_docling, (0, 0))
    combined.paste(img_gemini, (img_w + gap, 0))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    combined.save(output_path)


def process_document(doc_id, compare=False, force=False):
    """Overlay-Bilder fuer ein Dokument erzeugen."""
    layout_dir = LAYOUT_DIR / doc_id
    img_dir = IMAGES_DIR / doc_id

    if not layout_dir.exists() or not img_dir.exists():
        return 0, 0

    # Gemini-Layout-Dateien finden
    gemini_files = sorted(layout_dir.glob(f"{doc_id}_p*_layout_gemini.json"))
    if not gemini_files:
        return 0, 0

    created = 0
    skipped = 0

    for gemini_json_path in gemini_files:
        page_str = gemini_json_path.stem.replace(f"{doc_id}_p", "").replace("_layout_gemini", "")

        # Gemini-Overlay
        overlay_path = layout_dir / f"{doc_id}_p{page_str}_overlay_gemini.png"
        img_path = img_dir / f"{doc_id}_p{page_str}.png"

        if not img_path.exists():
            continue

        if overlay_path.exists() and not force:
            skipped += 1
        else:
            gemini_data = json.loads(gemini_json_path.read_text(encoding="utf-8"))
            draw_overlay_with_changes(img_path, gemini_data, overlay_path)
            created += 1

        # Compare-Bild (optional)
        if compare:
            compare_path = layout_dir / f"{doc_id}_p{page_str}_overlay_compare.png"
            docling_json_path = layout_dir / f"{doc_id}_p{page_str}_layout.json"

            if compare_path.exists() and not force:
                pass
            elif docling_json_path.exists():
                docling_data = json.loads(docling_json_path.read_text(encoding="utf-8"))
                gemini_data = json.loads(gemini_json_path.read_text(encoding="utf-8"))
                create_compare_image(img_path, docling_data, gemini_data, compare_path)
                created += 1

    return created, skipped


def main():
    parser = argparse.ArgumentParser(description="Layout-Overlay-Bilder erzeugen")
    parser.add_argument("--doc", type=str, help="Einzelnes Dokument (doc_id)")
    parser.add_argument("--compare", action="store_true", help="Side-by-side Vergleichsbilder")
    parser.add_argument("--force", action="store_true", help="Existierende ueberschreiben")
    args = parser.parse_args()

    if args.doc:
        doc_ids = [args.doc]
    else:
        doc_ids = discover_layout_documents()

    if not doc_ids:
        print("Keine Dokumente gefunden.")
        sys.exit(1)

    mode = "Overlay + Compare" if args.compare else "Overlay"
    print(f"Layout-Overlay-Generator: {len(doc_ids)} Docs ({mode})")
    print()

    total_created = 0
    total_skipped = 0

    for i, doc_id in enumerate(doc_ids):
        created, skipped = process_document(doc_id, compare=args.compare, force=args.force)
        if created > 0 or skipped > 0:
            print(f"  [{i+1}/{len(doc_ids)}] Doc {doc_id}: {created} erzeugt, {skipped} uebersprungen")
        total_created += created
        total_skipped += skipped

    print(f"\nFertig: {total_created} Bilder erzeugt, {total_skipped} uebersprungen")


if __name__ == "__main__":
    main()
