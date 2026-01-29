"""
DeepSeek-OCR-2 Test Script
Testet die OCR-Funktionalität mit einem Pilot-PDF.
"""

import os
import sys
from pathlib import Path
import tempfile

# Projekt-Root hinzufügen
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def pdf_to_images(pdf_path: str, output_dir: str = None) -> list[str]:
    """Konvertiert PDF zu Bildern mit pypdfium2."""
    import pypdfium2 as pdfium
    from PIL import Image

    if output_dir is None:
        output_dir = tempfile.mkdtemp()

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    pdf = pdfium.PdfDocument(pdf_path)
    image_paths = []

    for i, page in enumerate(pdf):
        # Render bei 300 DPI
        bitmap = page.render(scale=300/72)
        pil_image = bitmap.to_pil()

        # Speichere als PNG
        image_path = output_dir / f"page_{i+1:03d}.png"
        pil_image.save(str(image_path), "PNG")
        image_paths.append(str(image_path))

    pdf.close()
    print(f"  PDF konvertiert: {len(image_paths)} Seiten")
    return image_paths

def check_gpu():
    """Prüft GPU-Verfügbarkeit."""
    import torch
    print("=" * 50)
    print("GPU-Check")
    print("=" * 50)
    print(f"PyTorch Version: {torch.__version__}")
    print(f"CUDA verfügbar: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"CUDA Version: {torch.version.cuda}")
        print(f"GPU: {torch.cuda.get_device_name(0)}")
        print(f"VRAM: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")
    print()
    return torch.cuda.is_available()


def load_model():
    """Lädt das DeepSeek-OCR-2 Modell."""
    from transformers import AutoModel, AutoTokenizer
    import torch

    print("=" * 50)
    print("Lade DeepSeek-OCR-2 Modell...")
    print("=" * 50)

    model_name = 'deepseek-ai/DeepSeek-OCR-2'

    print("Lade Tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)

    print("Lade Modell (dies kann einige Minuten dauern beim ersten Mal)...")
    model = AutoModel.from_pretrained(
        model_name,
        trust_remote_code=True,
        use_safetensors=True
    )

    # Auf GPU verschieben
    model = model.eval().cuda().to(torch.bfloat16)
    print("Modell geladen und auf GPU verschoben.")
    print()

    return model, tokenizer


def process_image(model, tokenizer, image_path: str, output_dir: str) -> str:
    """Verarbeitet ein einzelnes Bild mit OCR und gibt den Text zurück."""
    print(f"  Verarbeite: {Path(image_path).name}")

    prompt = "<image>\n<|grounding|>Convert the document to markdown."
    output_path = Path(output_dir)

    # OCR durchführen
    model.infer(
        tokenizer,
        prompt=prompt,
        image_file=image_path,
        output_path=str(output_path),
        base_size=1024,
        image_size=768,
        crop_mode=True,
        save_results=True
    )

    # Ergebnis aus result.mmd auslesen (das Modell speichert dort)
    result_file = output_path / "result.mmd"
    if result_file.exists():
        result = result_file.read_text(encoding='utf-8')
        return result
    else:
        return f"[FEHLER: Keine Ausgabe für {image_path}]"


def main():
    # GPU prüfen
    if not check_gpu():
        print("FEHLER: Keine GPU verfügbar!")
        sys.exit(1)

    # Modell laden
    model, tokenizer = load_model()

    # Test-Bild/PDF angeben
    # Für den Test nutzen wir ein kleines PDF aus data/scans/
    scan_dir = PROJECT_ROOT / "data" / "scans"
    output_dir = PROJECT_ROOT / "output"
    output_dir.mkdir(exist_ok=True)

    # Suche nach kleinstem PDF
    pdfs = list(scan_dir.glob("*.pdf"))
    if not pdfs:
        print(f"Keine PDFs gefunden in: {scan_dir}")
        print("Bitte PDFs in data/scans/ ablegen.")
        sys.exit(1)

    # Sortiere nach Größe, nimm kleinstes
    pdfs.sort(key=lambda p: p.stat().st_size)
    test_pdf = pdfs[0]

    print(f"Test-PDF: {test_pdf.name} ({test_pdf.stat().st_size / 1024:.1f} KB)")
    print(f"Output: {output_dir}")
    print()

    # PDF zu Bildern konvertieren
    print("=" * 50)
    print("Konvertiere PDF zu Bildern...")
    print("=" * 50)

    temp_images_dir = output_dir / "temp_images"
    image_paths = pdf_to_images(str(test_pdf), str(temp_images_dir))

    # OCR durchführen
    print()
    print("=" * 50)
    print("Starte OCR...")
    print("=" * 50)

    all_results = []
    for i, image_path in enumerate(image_paths):
        print(f"Seite {i+1}/{len(image_paths)}:")
        result = process_image(model, tokenizer, image_path, str(output_dir))
        all_results.append(f"<!-- Seite {i+1} -->\n\n{result}")

    combined_result = "\n\n".join(all_results)

    print()
    print("=" * 50)
    print("Ergebnis (erste 2000 Zeichen):")
    print("=" * 50)
    print(combined_result[:2000] if len(combined_result) > 2000 else combined_result)
    print()

    # Speichere Ergebnis
    output_file = output_dir / f"{test_pdf.stem}_ocr.md"
    output_file.write_text(combined_result, encoding='utf-8')
    print(f"Gespeichert: {output_file}")


if __name__ == "__main__":
    main()
