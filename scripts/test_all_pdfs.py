"""
Systematischer OCR-Test für alle Dokumenttypen.
Führt Tests gemäß Testplan-OCR.md durch.
"""

import os
import sys
from pathlib import Path
import json
from datetime import datetime

# Projekt-Root hinzufügen
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Testplan-Konfiguration
TESTPLAN = {
    "phase1": {
        "name": "Baseline (einspaltig)",
        "tests": [
            {"pdf": "2310.pdf", "pages": [1, 2], "type": "A", "lang": "FR", "desc": "JSTOR Rezension"},
            {"pdf": "1180.pdf", "pages": [1, 2], "type": "A", "lang": "DE/FR", "desc": "Jahresbericht"},
            {"pdf": "290.pdf", "pages": [0, 1], "type": "A", "lang": "FR", "desc": "Comptes Rendus"},
        ]
    },
    "phase2": {
        "name": "Zweispaltig",
        "tests": [
            {"pdf": "2530.pdf", "pages": [0, 1], "type": "B", "lang": "FR", "desc": "Zeitschrift zweispaltig"},
            {"pdf": "890.pdf", "pages": [1, 2], "type": "B", "lang": "DE", "desc": "Lehrerzeitung"},
            {"pdf": "3040.pdf", "pages": [0, 1], "type": "B", "lang": "FR", "desc": "Lexikon mit Fußnoten"},
        ]
    },
    "phase3": {
        "name": "Spezialformate",
        "tests": [
            {"pdf": "90.pdf", "pages": [1, 2], "type": "D", "lang": "DE", "desc": "Historisch 1944"},
            {"pdf": "1440.pdf", "pages": [0, 1], "type": "D", "lang": "DE", "desc": "Interview/Dialog"},
            {"pdf": "830.pdf", "pages": [0, 1], "type": "D", "lang": "FR", "desc": "Bildband"},
            {"pdf": "1330.pdf", "pages": [0, 1], "type": "D", "lang": "FR", "desc": "Sammelband"},
        ]
    },
    "phase4": {
        "name": "Monografien",
        "tests": [
            {"pdf": "40.pdf", "pages": [4, 5], "type": "C", "lang": "FR", "desc": "Roman"},
            {"pdf": "1520.pdf", "pages": [2, 3], "type": "C", "lang": "?", "desc": "Monografie"},
        ]
    },
}


def pdf_to_images(pdf_path: str, pages: list[int], output_dir: Path) -> list[str]:
    """Konvertiert spezifische PDF-Seiten zu Bildern."""
    import pypdfium2 as pdfium

    output_dir.mkdir(parents=True, exist_ok=True)
    pdf = pdfium.PdfDocument(pdf_path)
    image_paths = []

    for page_num in pages:
        if page_num >= len(pdf):
            print(f"    Warnung: Seite {page_num+1} existiert nicht (max: {len(pdf)})")
            continue

        bitmap = pdf[page_num].render(scale=300/72)
        pil_image = bitmap.to_pil()

        image_path = output_dir / f"{Path(pdf_path).stem}_p{page_num+1}.png"
        pil_image.save(str(image_path), "PNG")
        image_paths.append(str(image_path))

    pdf.close()
    return image_paths


def process_image_ocr(model, tokenizer, image_path: str, output_dir: Path) -> str:
    """Führt OCR auf einem Bild durch."""
    prompt = "<image>\n<|grounding|>Convert the document to markdown."

    model.infer(
        tokenizer,
        prompt=prompt,
        image_file=image_path,
        output_path=str(output_dir),
        base_size=1024,
        image_size=768,
        crop_mode=True,
        save_results=True
    )

    result_file = output_dir / "result.mmd"
    if result_file.exists():
        return result_file.read_text(encoding='utf-8')
    return "[FEHLER: Keine Ausgabe]"


def run_test(model, tokenizer, test_config: dict, scan_dir: Path, output_dir: Path) -> dict:
    """Führt einen einzelnen Test durch."""
    pdf_path = scan_dir / test_config["pdf"]

    if not pdf_path.exists():
        return {
            "status": "SKIP",
            "error": f"PDF nicht gefunden: {pdf_path}",
            "results": []
        }

    # Bilder extrahieren
    temp_dir = output_dir / "temp_images"
    image_paths = pdf_to_images(str(pdf_path), test_config["pages"], temp_dir)

    if not image_paths:
        return {
            "status": "ERROR",
            "error": "Keine Bilder extrahiert",
            "results": []
        }

    # OCR durchführen
    results = []
    for img_path in image_paths:
        page_name = Path(img_path).stem
        print(f"    OCR: {page_name}")

        ocr_text = process_image_ocr(model, tokenizer, img_path, output_dir)

        # Ergebnis speichern
        result_file = output_dir / "ocr_results" / f"{page_name}.md"
        result_file.parent.mkdir(parents=True, exist_ok=True)
        result_file.write_text(ocr_text, encoding='utf-8')

        results.append({
            "page": page_name,
            "file": str(result_file),
            "chars": len(ocr_text),
            "lines": ocr_text.count('\n')
        })

    return {
        "status": "OK",
        "results": results
    }


def run_phase(model, tokenizer, phase_key: str, scan_dir: Path, output_dir: Path) -> dict:
    """Führt alle Tests einer Phase durch."""
    phase = TESTPLAN[phase_key]
    print(f"\n{'='*60}")
    print(f"Phase: {phase['name']}")
    print(f"{'='*60}")

    phase_results = {
        "name": phase["name"],
        "tests": {}
    }

    for test in phase["tests"]:
        pdf_name = test["pdf"]
        print(f"\n  Test: {pdf_name} ({test['desc']})")
        print(f"  Typ: {test['type']}, Sprache: {test['lang']}, Seiten: {test['pages']}")

        result = run_test(model, tokenizer, test, scan_dir, output_dir)
        phase_results["tests"][pdf_name] = {
            **test,
            **result
        }

        if result["status"] == "OK":
            print(f"  ✓ Erfolgreich: {len(result['results'])} Seiten")
        else:
            print(f"  ✗ {result['status']}: {result.get('error', 'Unbekannt')}")

    return phase_results


def check_gpu():
    """Prüft GPU-Verfügbarkeit."""
    import torch
    if not torch.cuda.is_available():
        return False
    print(f"GPU: {torch.cuda.get_device_name(0)}")
    print(f"VRAM: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")
    return True


def load_model():
    """Lädt das DeepSeek-OCR-2 Modell."""
    from transformers import AutoModel, AutoTokenizer
    import torch

    print("Lade DeepSeek-OCR-2 Modell...")
    model_name = 'deepseek-ai/DeepSeek-OCR-2'

    tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
    model = AutoModel.from_pretrained(
        model_name,
        trust_remote_code=True,
        use_safetensors=True
    )
    model = model.eval().cuda().to(torch.bfloat16)
    print("Modell geladen.")

    return model, tokenizer


def main():
    import argparse

    parser = argparse.ArgumentParser(description="OCR-Tests für alle Dokumenttypen")
    parser.add_argument("--phase", choices=["phase1", "phase2", "phase3", "phase4", "all"],
                        default="phase1", help="Welche Phase testen")
    parser.add_argument("--dry-run", action="store_true", help="Nur Konfiguration anzeigen")
    args = parser.parse_args()

    # Pfade
    scan_dir = PROJECT_ROOT / "data" / "scans"
    output_dir = PROJECT_ROOT / "output"
    output_dir.mkdir(exist_ok=True)

    # Dry-Run: Nur Konfiguration anzeigen
    if args.dry_run:
        print("Testplan-Konfiguration:")
        for phase_key, phase in TESTPLAN.items():
            print(f"\n{phase_key}: {phase['name']}")
            for test in phase["tests"]:
                pdf_path = scan_dir / test["pdf"]
                exists = "✓" if pdf_path.exists() else "✗"
                print(f"  {exists} {test['pdf']}: {test['desc']} (Seiten {test['pages']})")
        return

    # GPU prüfen
    if not check_gpu():
        print("FEHLER: Keine GPU verfügbar!")
        sys.exit(1)

    # Modell laden
    model, tokenizer = load_model()

    # Phasen bestimmen
    if args.phase == "all":
        phases_to_run = list(TESTPLAN.keys())
    else:
        phases_to_run = [args.phase]

    # Tests durchführen
    all_results = {
        "timestamp": datetime.now().isoformat(),
        "phases": {}
    }

    for phase_key in phases_to_run:
        phase_results = run_phase(model, tokenizer, phase_key, scan_dir, output_dir)
        all_results["phases"][phase_key] = phase_results

    # Ergebnisse speichern
    results_file = output_dir / "evaluation" / f"results_{args.phase}.json"
    results_file.parent.mkdir(parents=True, exist_ok=True)
    results_file.write_text(json.dumps(all_results, indent=2, ensure_ascii=False), encoding='utf-8')
    print(f"\n\nErgebnisse gespeichert: {results_file}")

    # Zusammenfassung
    print("\n" + "="*60)
    print("ZUSAMMENFASSUNG")
    print("="*60)

    for phase_key, phase_data in all_results["phases"].items():
        print(f"\n{phase_data['name']}:")
        for pdf_name, test_result in phase_data["tests"].items():
            status = test_result["status"]
            if status == "OK":
                pages = len(test_result["results"])
                print(f"  ✓ {pdf_name}: {pages} Seiten")
            else:
                print(f"  ✗ {pdf_name}: {status}")


if __name__ == "__main__":
    main()
