"""
Systematischer OCR-Test fuer alle Dokumenttypen.
Fuehrt Tests gemaess Testplan durch.
"""

import sys
import json
from pathlib import Path
from datetime import datetime

from scripts.config import PROJECT_ROOT, SCANS_DIR, OUTPUT_DIR, TESTPLAN, DEEPSEEK_PROMPT
from scripts.utils import check_gpu, load_deepseek_model, pdf_to_images_pages


def process_image_ocr(model, tokenizer, image_path: Path, output_dir: Path) -> str:
    """Fuehrt OCR auf einem Bild durch."""
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
    return "[FEHLER: Keine Ausgabe]"


def run_test(model, tokenizer, test_config: dict, scan_dir: Path, output_dir: Path) -> dict:
    """Fuehrt einen einzelnen Test durch."""
    pdf_path = scan_dir / test_config["pdf"]

    if not pdf_path.exists():
        return {
            "status": "SKIP",
            "error": f"PDF nicht gefunden: {pdf_path}",
            "results": []
        }

    # Bilder extrahieren
    temp_dir = output_dir / "temp_images"
    image_paths = pdf_to_images_pages(pdf_path, test_config["pages"], temp_dir)

    if not image_paths:
        return {
            "status": "ERROR",
            "error": "Keine Bilder extrahiert",
            "results": []
        }

    # OCR durchfuehren
    results = []
    for img_path in image_paths:
        page_name = img_path.stem
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
    """Fuehrt alle Tests einer Phase durch."""
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
            print(f"  [OK] Erfolgreich: {len(result['results'])} Seiten")
        else:
            print(f"  [FAIL] {result['status']}: {result.get('error', 'Unbekannt')}")

    return phase_results


def main():
    import argparse

    parser = argparse.ArgumentParser(description="OCR-Tests fuer alle Dokumenttypen")
    parser.add_argument("--phase", choices=["phase1", "phase2", "phase3", "phase4", "all"],
                        default="phase1", help="Welche Phase testen")
    parser.add_argument("--dry-run", action="store_true", help="Nur Konfiguration anzeigen")
    args = parser.parse_args()

    # Pfade
    output_dir = OUTPUT_DIR
    output_dir.mkdir(exist_ok=True)

    # Dry-Run: Nur Konfiguration anzeigen
    if args.dry_run:
        print("Testplan-Konfiguration:")
        for phase_key, phase in TESTPLAN.items():
            print(f"\n{phase_key}: {phase['name']}")
            for test in phase["tests"]:
                pdf_path = SCANS_DIR / test["pdf"]
                exists = "[OK]" if pdf_path.exists() else "[--]"
                print(f"  {exists} {test['pdf']}: {test['desc']} (Seiten {test['pages']})")
        return

    # GPU pruefen
    gpu = check_gpu()
    if not gpu["available"]:
        print("FEHLER: Keine GPU verfuegbar!")
        sys.exit(1)
    print(f"GPU: {gpu['name']} ({gpu['vram_gb']:.1f} GB)")

    # Modell laden
    model, tokenizer = load_deepseek_model()

    # Phasen bestimmen
    if args.phase == "all":
        phases_to_run = list(TESTPLAN.keys())
    else:
        phases_to_run = [args.phase]

    # Tests durchfuehren
    all_results = {
        "timestamp": datetime.now().isoformat(),
        "phases": {}
    }

    for phase_key in phases_to_run:
        phase_results = run_phase(model, tokenizer, phase_key, SCANS_DIR, output_dir)
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
                print(f"  [OK] {pdf_name}: {pages} Seiten")
            else:
                print(f"  [--] {pdf_name}: {status}")


if __name__ == "__main__":
    main()
