"""
DeepSeek-OCR-2 Test Script
Testet die OCR-Funktionalitaet mit einem Pilot-PDF.
"""

import sys
from pathlib import Path

from scripts.config import SCANS_DIR, OUTPUT_DIR, DEEPSEEK_PROMPT
from scripts.utils import check_gpu, load_deepseek_model, pdf_to_images


def process_image(model, tokenizer, image_path: Path, output_dir: Path) -> str:
    """Verarbeitet ein einzelnes Bild mit OCR und gibt den Text zurueck."""
    print(f"  Verarbeite: {image_path.name}")

    model.infer(
        tokenizer,
        prompt=DEEPSEEK_PROMPT,
        image_file=str(image_path),
        output_path=str(output_dir),
        base_size=1024,
        image_size=768,
        crop_mode=True,
        save_results=True
    )

    result_file = output_dir / "result.mmd"
    if result_file.exists():
        return result_file.read_text(encoding='utf-8')
    return f"[FEHLER: Keine Ausgabe fuer {image_path}]"


def main():
    # GPU pruefen
    gpu = check_gpu()
    if not gpu["available"]:
        print("FEHLER: Keine GPU verfuegbar!")
        sys.exit(1)
    print(f"GPU: {gpu['name']} ({gpu['vram_gb']:.1f} GB)")

    # Modell laden
    model, tokenizer = load_deepseek_model()

    # Suche nach kleinstem PDF
    pdfs = list(SCANS_DIR.glob("*.pdf"))
    if not pdfs:
        print(f"Keine PDFs gefunden in: {SCANS_DIR}")
        print("Bitte PDFs in data/scans/ ablegen.")
        sys.exit(1)

    pdfs.sort(key=lambda p: p.stat().st_size)
    test_pdf = pdfs[0]

    print(f"Test-PDF: {test_pdf.name} ({test_pdf.stat().st_size / 1024:.1f} KB)")
    print(f"Output: {OUTPUT_DIR}")

    # PDF zu Bildern konvertieren
    print("\nKonvertiere PDF zu Bildern...")
    temp_images_dir = OUTPUT_DIR / "temp_images"
    image_paths = pdf_to_images(test_pdf, temp_images_dir)

    # OCR durchfuehren
    print("\nStarte OCR...")
    all_results = []
    for i, image_path in enumerate(image_paths):
        print(f"Seite {i+1}/{len(image_paths)}:")
        result = process_image(model, tokenizer, image_path, OUTPUT_DIR)
        all_results.append(f"<!-- Seite {i+1} -->\n\n{result}")

    combined_result = "\n\n".join(all_results)

    print("\nErgebnis (erste 2000 Zeichen):")
    print("=" * 50)
    print(combined_result[:2000] if len(combined_result) > 2000 else combined_result)

    # Speichere Ergebnis
    output_file = OUTPUT_DIR / f"{test_pdf.stem}_ocr.md"
    output_file.write_text(combined_result, encoding='utf-8')
    print(f"\nGespeichert: {output_file}")


if __name__ == "__main__":
    main()
