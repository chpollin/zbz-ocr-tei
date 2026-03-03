"""
Layout-Utilities fuer das zbz-ocr-tei Projekt.

Gemeinsame Funktionen fuer Layout-Analyse, Overlay-Erzeugung und Koordinaten-Konvertierung.
Genutzt von: run_layout_analysis.py, run_layout_cloud.py, layout_qa_gemini.py.
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from scripts.config import LABEL_COLORS


def to_pixel_pct(bbox: dict, doc_w: float, doc_h: float, img_w: int, img_h: int) -> dict:
    """Docling-Koordinaten (Punkte, Ursprung unten-links) -> Prozent (Ursprung oben-links)."""
    scale_x = img_w / doc_w if doc_w > 0 else 1
    scale_y = img_h / doc_h if doc_h > 0 else 1

    x1 = bbox["l"] * scale_x
    x2 = bbox["r"] * scale_x
    # Y-Flip: Docling Ursprung unten-links, Bild Ursprung oben-links
    y1 = (doc_h - bbox["t"]) * scale_y
    y2 = (doc_h - bbox["b"]) * scale_y
    if y1 > y2:
        y1, y2 = y2, y1

    w = x2 - x1
    h = y2 - y1

    return {
        "x_pct": round(x1 / img_w * 100, 3),
        "y_pct": round(y1 / img_h * 100, 3),
        "w_pct": round(w / img_w * 100, 3),
        "h_pct": round(h / img_h * 100, 3),
    }


def draw_overlay_from_json(img_path: Path, layout_json: dict, output_path: Path):
    """Zeichnet BBox-Overlay auf Bild und speichert als PNG.

    Liest Regionen aus dem Layout-JSON (Prozent-Koordinaten)
    und zeichnet sie als farbige Rechtecke auf das Originalbild.
    """
    img = Image.open(img_path).convert("RGB")
    draw = ImageDraw.Draw(img, "RGBA")
    img_w, img_h = img.size

    # Font laden (Fallback auf Default)
    try:
        font = ImageFont.truetype("arial.ttf", 14)
    except (OSError, IOError):
        font = ImageFont.load_default()

    for region in layout_json.get("regions", []):
        bbox = region.get("bbox")
        if not bbox:
            continue

        label = region.get("label", "text")
        zbz_tag = region.get("zbz_tag", "zb_paragraph")
        text_preview = region.get("text", "")[:60]
        color = LABEL_COLORS.get(label, (100, 100, 100))

        # Prozent -> Pixel
        x1 = bbox["x_pct"] / 100.0 * img_w
        y1 = bbox["y_pct"] / 100.0 * img_h
        w = bbox["w_pct"] / 100.0 * img_w
        h = bbox["h_pct"] / 100.0 * img_h
        x2 = x1 + w
        y2 = y1 + h

        # Gefuelltes Rechteck mit Transparenz
        fill_color = color + (40,)
        draw.rectangle([x1, y1, x2, y2], outline=color, fill=fill_color, width=2)

        # Label-Text oben links im Rechteck
        label_text = f"{label} -> {zbz_tag}"
        draw.text((x1 + 3, y1 + 3), label_text, fill=color, font=font)

        # Text-Vorschau darunter (falls Platz)
        if text_preview and h > 30:
            draw.text((x1 + 3, y1 + 18), text_preview, fill=color, font=font)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path)
