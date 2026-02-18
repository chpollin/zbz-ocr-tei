#!/usr/bin/env python3
"""
Mistral Document AI Test: Benchmark gegen DeepSeek auf Phase-1-Daten.

Testet die Mistral Document AI Engine (Azure AI Foundry) auf den
Phase-1-Pilotdateien und vergleicht mit bestehenden DeepSeek-Ergebnissen.

Usage:
    # Einzelnes PDF testen
    python scripts/test_mistral_ocr.py --input data/scans/2310.pdf

    # Phase 1 komplett (Benchmark)
    python scripts/test_mistral_ocr.py --phase1

    # Beliebiges PDF
    python scripts/test_mistral_ocr.py --input data/scans/2530.pdf

Voraussetzungen:
    - .env-Datei mit MISTRAL_DOC_AI_ENDPOINT und MISTRAL_DOC_AI_KEY
    - Oder Umgebungsvariablen direkt gesetzt
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path
from datetime import datetime

from scripts.config import PROJECT_ROOT, SCANS_DIR, MISTRAL_RESULTS_DIR, OCR_RESULTS_DIR, PHASE1_TESTS
from scripts.utils import load_env


def check_config():
    """Prueft ob Mistral-Konfiguration vorhanden ist."""
    endpoint = os.environ.get("MISTRAL_DOC_AI_ENDPOINT", "")
    key = os.environ.get("MISTRAL_DOC_AI_KEY", "")

    if not endpoint:
        print("FEHLER: MISTRAL_DOC_AI_ENDPOINT nicht gesetzt.")
        print("Erstelle eine .env-Datei basierend auf .env.example")
        return False
    if not key:
        print("FEHLER: MISTRAL_DOC_AI_KEY nicht gesetzt.")
        print("Erstelle eine .env-Datei basierend auf .env.example")
        return False

    print(f"Endpoint: {endpoint[:50]}...")
    print(f"API-Key: {key[:8]}...{key[-4:]}")
    return True


def test_single_pdf(pdf_path: Path, output_dir: Path) -> dict:
    """Testet ein einzelnes PDF mit Mistral Document AI."""
    from scripts.ocr_pipeline import MistralOCR

    output_dir.mkdir(parents=True, exist_ok=True)

    ocr = MistralOCR()
    start_time = time.time()

    try:
        result = ocr.process_pdf(pdf_path, output_dir)
        elapsed = time.time() - start_time

        result["elapsed_seconds"] = round(elapsed, 2)
        result["seconds_per_page"] = round(elapsed / max(result["pages"], 1), 2)
        result["status"] = "OK"

        print(f"  OK: {result['pages']} Seiten in {elapsed:.1f}s "
              f"({result['seconds_per_page']:.1f}s/Seite)")

        return result

    except Exception as e:
        elapsed = time.time() - start_time
        print(f"  FEHLER: {e}")
        return {
            "doc_id": pdf_path.stem,
            "status": "ERROR",
            "error": str(e),
            "elapsed_seconds": round(elapsed, 2),
        }


def run_phase1(scan_dir: Path, output_dir: Path) -> list:
    """Fuehrt Phase-1-Benchmark durch."""
    results = []

    for test in PHASE1_TESTS:
        pdf_path = scan_dir / test["pdf"]
        print(f"\n--- {test['pdf']} ({test['desc']}) ---")

        if not pdf_path.exists():
            print(f"  SKIP: {pdf_path} nicht gefunden")
            results.append({
                "doc_id": pdf_path.stem,
                "status": "SKIP",
                "desc": test["desc"],
            })
            continue

        result = test_single_pdf(pdf_path, output_dir)
        result["desc"] = test["desc"]
        result["type"] = test["type"]
        result["lang"] = test["lang"]
        results.append(result)

    return results


def compare_with_deepseek(output_dir: Path) -> dict:
    """Vergleicht Mistral-Ergebnisse mit bestehenden DeepSeek-Ergebnissen."""
    comparison = {}

    for test in PHASE1_TESTS:
        doc_id = Path(test["pdf"]).stem
        deepseek_files = sorted(OCR_RESULTS_DIR.glob(f"{doc_id}_p*.md"))
        mistral_files = sorted(output_dir.glob(f"{doc_id}_p*.md"))

        if not deepseek_files:
            comparison[doc_id] = {"status": "no_deepseek", "note": "Keine DeepSeek-Ergebnisse vorhanden"}
            continue
        if not mistral_files:
            comparison[doc_id] = {"status": "no_mistral", "note": "Keine Mistral-Ergebnisse vorhanden"}
            continue

        # Texte laden und Laenge vergleichen
        ds_text = " ".join(f.read_text(encoding="utf-8") for f in deepseek_files)
        mi_text = " ".join(f.read_text(encoding="utf-8") for f in mistral_files)

        comparison[doc_id] = {
            "status": "OK",
            "deepseek_chars": len(ds_text),
            "mistral_chars": len(mi_text),
            "deepseek_pages": len(deepseek_files),
            "mistral_pages": len(mistral_files),
        }

        print(f"\n  {doc_id}: DeepSeek {len(ds_text)} Zeichen vs. Mistral {len(mi_text)} Zeichen")

    return comparison


def main():
    parser = argparse.ArgumentParser(description="Mistral Document AI Benchmark")
    parser.add_argument("--input", "-i", type=Path, help="Einzelnes PDF testen")
    parser.add_argument("--phase1", action="store_true", help="Phase-1-Benchmark (Typ A)")
    parser.add_argument("--compare", action="store_true", help="Mit DeepSeek-Ergebnissen vergleichen")
    parser.add_argument("--check", action="store_true", help="Nur Konfiguration pruefen")
    args = parser.parse_args()

    load_env()

    print("=" * 60)
    print("Mistral Document AI - OCR Benchmark")
    print("=" * 60)
    print(f"Modell: mistral-document-ai-2512")
    print(f"Datum: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print()

    # Konfiguration pruefen
    if not check_config():
        return 1

    if args.check:
        print("\nKonfiguration OK.")
        return 0

    print()

    # Pfade
    scan_dir = SCANS_DIR
    output_dir = MISTRAL_RESULTS_DIR

    if args.input:
        # Einzelnes PDF
        if not args.input.exists():
            print(f"FEHLER: {args.input} nicht gefunden")
            return 1

        result = test_single_pdf(args.input, output_dir)
        results = [result]

    elif args.phase1:
        # Phase-1-Benchmark
        print("Phase 1: Baseline (einspaltig, Typ A)")
        print("-" * 40)
        results = run_phase1(scan_dir, output_dir)

        if args.compare:
            print("\n\nVergleich mit DeepSeek:")
            print("-" * 40)
            comparison = compare_with_deepseek(output_dir)

            # Zusammenfassung speichern
            comp_file = output_dir / "comparison_deepseek.json"
            comp_file.write_text(
                json.dumps(comparison, indent=2, ensure_ascii=False),
                encoding="utf-8"
            )
            print(f"\nVergleich gespeichert: {comp_file}")

    else:
        parser.print_help()
        return 1

    # Ergebnisse speichern
    manifest = {
        "timestamp": datetime.now().isoformat(),
        "engine": "mistral-document-ai-2512",
        "results": results,
    }

    manifest_file = output_dir / "manifest.json"
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_file.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    # Zusammenfassung
    print("\n" + "=" * 60)
    print("ZUSAMMENFASSUNG")
    print("=" * 60)

    successful = [r for r in results if r.get("status") == "OK"]
    failed = [r for r in results if r.get("status") == "ERROR"]
    skipped = [r for r in results if r.get("status") == "SKIP"]

    print(f"Erfolgreich: {len(successful)}/{len(results)}")
    if skipped:
        print(f"Uebersprungen: {len(skipped)}")
    if failed:
        print(f"Fehlgeschlagen: {len(failed)}")
        for r in failed:
            print(f"  - {r['doc_id']}: {r.get('error', '?')}")

    total_pages = sum(r.get("pages", 0) for r in successful)
    total_time = sum(r.get("elapsed_seconds", 0) for r in successful)
    print(f"Seiten gesamt: {total_pages}")
    if total_pages > 0:
        print(f"Gesamtzeit: {total_time:.1f}s ({total_time/total_pages:.1f}s/Seite)")

    print(f"\nErgebnisse: {output_dir}")
    print(f"Manifest: {manifest_file}")

    print("\nNaechster Schritt: Evaluation mit")
    print(f"  python scripts/evaluate_ocr.py --all")
    print(f"  (OCR-Ergebnisse muessen dafuer in output/ocr_results/ liegen)")

    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
