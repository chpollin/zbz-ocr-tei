"""
Gemeinsame Hilfsfunktionen fuer das zbz-ocr-tei Projekt.

Konsolidiert: pdf_to_images, check_gpu, load_env, load_deepseek_model.
"""

import os
from pathlib import Path

from scripts.config import PROJECT_ROOT, DEFAULT_DPI


def load_env():
    """Laedt .env-Datei ins Environment (falls vorhanden)."""
    env_file = PROJECT_ROOT / ".env"
    if not env_file.exists():
        return

    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def check_gpu() -> dict:
    """
    Prueft GPU-Verfuegbarkeit.

    Returns:
        dict mit "available" (bool), optional "name" (str) und "vram_gb" (float)
    """
    try:
        import torch
        if torch.cuda.is_available():
            return {
                "available": True,
                "name": torch.cuda.get_device_name(0),
                "vram_gb": torch.cuda.get_device_properties(0).total_memory / 1024**3,
            }
    except ImportError:
        pass
    return {"available": False}


def pdf_to_images(pdf_path: Path, output_dir: Path, dpi: int = DEFAULT_DPI) -> list[Path]:
    """
    Konvertiert alle PDF-Seiten zu PNG-Bildern.

    Args:
        pdf_path: Pfad zur PDF-Datei
        output_dir: Verzeichnis fuer die Bilder
        dpi: Aufloesung (default: 300)

    Returns:
        Liste der erzeugten Bildpfade
    """
    import pypdfium2 as pdfium

    pdf = pdfium.PdfDocument(str(pdf_path))
    total = len(pdf)
    pdf.close()

    return pdf_to_images_pages(pdf_path, list(range(total)), output_dir, dpi)


def pdf_to_images_pages(
    pdf_path: Path, pages: list[int], output_dir: Path, dpi: int = DEFAULT_DPI
) -> list[Path]:
    """
    Konvertiert spezifische PDF-Seiten zu PNG-Bildern.

    Args:
        pdf_path: Pfad zur PDF-Datei
        pages: 0-basierte Seitenindizes
        output_dir: Verzeichnis fuer die Bilder
        dpi: Aufloesung (default: 300)

    Returns:
        Liste der erzeugten Bildpfade
    """
    import pypdfium2 as pdfium

    output_dir.mkdir(parents=True, exist_ok=True)
    pdf = pdfium.PdfDocument(str(pdf_path))
    image_paths = []

    for page_num in pages:
        if page_num >= len(pdf):
            print(f"    Warnung: Seite {page_num+1} existiert nicht (max: {len(pdf)})")
            continue

        bitmap = pdf[page_num].render(scale=dpi / 72)
        pil_image = bitmap.to_pil()
        image_path = output_dir / f"{pdf_path.stem}_p{page_num+1:03d}.png"
        pil_image.save(str(image_path), "PNG")
        image_paths.append(image_path)

    pdf.close()
    return image_paths


def load_deepseek_model():
    """
    Laedt das DeepSeek-OCR-2 Modell.

    Returns:
        (model, tokenizer) Tuple
    """
    from transformers import AutoModel, AutoTokenizer
    import torch

    from scripts.config import DEEPSEEK_MODEL

    print("Lade DeepSeek-OCR-2...")
    tokenizer = AutoTokenizer.from_pretrained(DEEPSEEK_MODEL, trust_remote_code=True)
    model = AutoModel.from_pretrained(
        DEEPSEEK_MODEL,
        trust_remote_code=True,
        use_safetensors=True,
    )
    model = model.eval().cuda().to(torch.bfloat16)
    print("DeepSeek-OCR-2 geladen.")

    return model, tokenizer
