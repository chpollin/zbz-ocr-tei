"""
LLM-basierte OCR-Nachkorrektur mit Anthropic Claude Haiku.

Liest OCR-Markdown-Dateien, korrigiert OCR-Fehler mittels LLM,
speichert korrigierte Dateien.

Usage:
    python -m scripts.ocr.llm_postprocess --check
    python -m scripts.ocr.llm_postprocess --doc 2310 --dry-run
    python -m scripts.ocr.llm_postprocess --doc 2310
    python -m scripts.ocr.llm_postprocess --phase phase1
    python -m scripts.ocr.llm_postprocess --all
    python -m scripts.ocr.llm_postprocess --phase phase1 --variant B --force
"""

import argparse
import json
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path

from scripts.config import (
    MISTRAL_RESULTS_DIR,
    LLM_CORRECTED_DIR,
    TESTPLAN,
    ANTHROPIC_MODEL,
    ANTHROPIC_MAX_RETRIES,
    ANTHROPIC_TIMEOUT_SECONDS,
    get_test_metadata,
)
from scripts.utils import extract_page_num, get_phase_doc_ids, load_env


# --- Dokumenttyp-Beschreibungen ---

TYPE_DESC = {
    "A": "Einspaltig, Standard-Fliesstext",
    "B": "Zweispaltig (Zeitschrift/Lexikon)",
    "C": "Monografie (Buch, 100+ Seiten)",
    "D": "Spezialformat (historisch, Interview, Bildband)",
}

# --- Prompt-Varianten ---

VARIANTS = ["A", "B", "C"]


def build_system_prompt(lang: str, variant: str = "A") -> str:
    """Baut den System-Prompt je nach Variante."""
    if variant == "A":
        return _prompt_variant_a(lang)
    elif variant == "B":
        return _prompt_variant_b(lang)
    elif variant == "C":
        return _prompt_variant_c(lang)
    raise ValueError(f"Unbekannte Variante: {variant}")


def _lang_hint(lang: str) -> str:
    """Kurzer Sprach-Hinweis fuer alle Varianten."""
    hints = {
        "FR": "Sprache: Franzoesisch. Achte auf Akzente, Guillemets, Apostrophe (l', d', qu').",
        "DE": "Sprache: Deutsch. Achte auf Umlaute, Eszett, Komposita.",
        "DE/FR": "Sprache: Deutsch/Franzoesisch gemischt. Achte auf Umlaute UND Akzente.",
        "EN": "Sprache: Englisch.",
    }
    return hints.get(lang, hints["FR"])


def _prompt_variant_a(lang: str) -> str:
    """Variante A: Original-Prompt mit Analysis + Corrected (Baseline)."""
    return (
        "Du bist ein Experte fuer OCR-Nachkorrektur akademischer Texte des 20. Jahrhunderts "
        "von Jeanne Hersch (Philosophin, 1910-2000). Du erhaeltst OCR-Output aus gescannten "
        "Dokumenten und korrigierst Zeichenfehler.\n\n"
        "Regeln:\n"
        "- Korrigiere NUR OCR-Fehler: falsch erkannte Buchstaben, fehlende Akzente, "
        "zusammengeklebte oder getrennte Woerter, Artefakte\n"
        "- Formuliere NICHTS um. Der Originaltext muss erhalten bleiben.\n"
        "- Erfinde KEINE neuen Inhalte.\n"
        "- Behalte Markdown-Formatierung bei (**fett**, *kursiv*, ## Ueberschriften)\n"
        "- Entferne offensichtliche OCR-Artefakte (JSTOR-Header, wiederholte Seitenzahlen, "
        "Copyright-Zeilen) NUR wenn sie klar maschinenerzeugt sind\n"
        "- Wenn du unsicher bist, lasse den Text unveraendert\n\n"
        f"{_lang_hint(lang)}\n\n"
        "Antwortformat:\n"
        "1. Zuerst in einem <analysis>-Block: Liste der gefundenen OCR-Fehler "
        "(max. 20, Format: 'original -> korrektur (Grund)')\n"
        "2. Dann in einem <corrected>-Block: Der vollstaendig korrigierte Text"
    )


def _prompt_variant_b(lang: str) -> str:
    """Variante B: Schlank — nur korrigierter Text, kein Analysis-Block."""
    return (
        "Korrigiere OCR-Fehler im folgenden Text. "
        "Der Text stammt aus gescannten akademischen Texten von Jeanne Hersch (20. Jh.).\n\n"
        "Regeln:\n"
        "- NUR Zeichenfehler korrigieren (falsche Buchstaben, fehlende Akzente, "
        "zusammengeklebte Woerter, OCR-Artefakte)\n"
        "- NICHTS umformulieren, NICHTS hinzufuegen\n"
        "- Markdown beibehalten\n"
        "- Im Zweifel: NICHT aendern\n"
        "- Maschinenerzeugte Artefakte (JSTOR-Header, Copyright-Zeilen) entfernen\n\n"
        f"{_lang_hint(lang)}\n\n"
        "Gib NUR den korrigierten Text aus, ohne Erklaerungen oder Kommentare."
    )


def _prompt_variant_c(lang: str) -> str:
    """Variante C: Few-Shot mit echten Fehlerbeispielen aus Mistral-OCR."""
    return (
        "Korrigiere OCR-Fehler im folgenden Text. "
        "Der Text stammt aus gescannten akademischen Texten von Jeanne Hersch (20. Jh.).\n\n"
        "Regeln:\n"
        "- NUR Zeichenfehler korrigieren, NICHTS umformulieren\n"
        "- Markdown beibehalten\n"
        "- Im Zweifel: NICHT aendern\n"
        "- Maschinenerzeugte Artefakte (JSTOR-Header, Copyright-Zeilen) entfernen\n\n"
        f"{_lang_hint(lang)}\n\n"
        "Typische OCR-Fehler dieser Engine (Mistral Document AI):\n"
        "- 'inconnaisable' -> 'inconnaissable' (fehlender Buchstabe)\n"
        "- 'etrente' -> 'etreinte' (falsche Zeichenfolge)\n"
        "- 'Scussion' -> 'Scission' (Buchstabenvertauschung)\n"
        "- 'seule tu le courant' -> 'sens-tu le courant' (Wortgrenze falsch)\n"
        "- 'rereferme' -> 'se referme' (zusammengeklebte Woerter)\n"
        "- 'lisse, comme' -> 'hisse, comme' (aehnliche Buchstaben verwechselt)\n"
        "- 'This content downloaded from...' -> entfernen (JSTOR-Artefakt)\n\n"
        "Gib NUR den korrigierten Text aus, ohne Erklaerungen oder Kommentare."
    )


def build_user_message(
    doc_id: str,
    page_num: int,
    total_pages: int,
    ocr_text: str,
    metadata: dict | None,
) -> str:
    """Baut die User-Nachricht mit Dokumentkontext."""
    doc_type = metadata.get("type", "?") if metadata else "?"
    type_desc = TYPE_DESC.get(doc_type, "Unbekannt")
    lang = metadata.get("lang", "?") if metadata else "?"
    genre = metadata.get("desc", "Unbekannt") if metadata else "Unbekannt"

    return (
        f"Dokument: {doc_id}\n"
        f"Typ: {doc_type} ({type_desc})\n"
        f"Sprache: {lang}\n"
        f"Genre: {genre}\n"
        f"OCR-Engine: Mistral Document AI\n"
        f"Seite: {page_num} von {total_pages}\n\n"
        f"<ocr_text>\n{ocr_text}\n</ocr_text>"
    )


def call_anthropic(
    system_prompt: str,
    user_message: str,
    api_key: str,
) -> dict:
    """
    Ruft die Anthropic Messages API auf.

    Returns:
        dict mit {analysis, corrected, input_tokens, output_tokens, raw_response}
    """
    import anthropic

    client = anthropic.Anthropic(
        api_key=api_key,
        timeout=ANTHROPIC_TIMEOUT_SECONDS,
    )

    last_error = None
    for attempt in range(ANTHROPIC_MAX_RETRIES):
        try:
            response = client.messages.create(
                model=ANTHROPIC_MODEL,
                max_tokens=4096,
                system=system_prompt,
                messages=[{"role": "user", "content": user_message}],
            )

            text = response.content[0].text
            parsed = parse_response(text)

            return {
                "analysis": parsed["analysis"],
                "corrected": parsed["corrected"],
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
                "raw_response": text,
            }

        except anthropic.RateLimitError as e:
            last_error = e
            wait = min(5 * (2 ** attempt), 60)
            print(f"    Rate limit, warte {wait}s...")
            time.sleep(wait)

        except anthropic.APIError as e:
            last_error = e
            if attempt < ANTHROPIC_MAX_RETRIES - 1:
                wait = 2 * (2 ** attempt)
                print(f"    API-Fehler ({e}), Retry in {wait}s...")
                time.sleep(wait)

    raise RuntimeError(f"API-Aufruf fehlgeschlagen nach {ANTHROPIC_MAX_RETRIES} Versuchen: {last_error}")


def parse_response(text: str, variant: str = "A") -> dict:
    """Extrahiert analysis und corrected aus der LLM-Antwort."""
    analysis = ""
    corrected = text.strip()  # Fallback: gesamter Text

    if variant == "A":
        # Variante A: <analysis> und <corrected> Bloecke
        analysis_match = re.search(r"<analysis>(.*?)</analysis>", text, re.DOTALL)
        if analysis_match:
            analysis = analysis_match.group(1).strip()

        corrected_match = re.search(r"<corrected>(.*?)</corrected>", text, re.DOTALL)
        if corrected_match:
            corrected = corrected_match.group(1).strip()
    else:
        # Variante B/C: Gesamttext ist der korrigierte Text
        # Entferne eventuelle Wrapper falls das Modell trotzdem Tags nutzt
        corrected_match = re.search(r"<corrected>(.*?)</corrected>", text, re.DOTALL)
        if corrected_match:
            corrected = corrected_match.group(1).strip()

    return {"analysis": analysis, "corrected": corrected}


def find_page_files(doc_id: str, ocr_dir: Path) -> list[Path]:
    """Findet alle Seitendateien fuer ein Dokument, sortiert nach Seitennummer."""
    pattern = f"{doc_id}_p*.md"
    files = sorted(ocr_dir.glob(pattern))
    return files


def process_document(
    doc_id: str,
    ocr_dir: Path,
    output_dir: Path,
    api_key: str,
    dry_run: bool = False,
    force: bool = False,
    variant: str = "A",
) -> dict:
    """
    Verarbeitet ein Dokument: LLM-Korrektur aller Seiten.

    Returns:
        dict mit Stats (pages, tokens, errors)
    """
    page_files = find_page_files(doc_id, ocr_dir)
    if not page_files:
        print(f"  Keine OCR-Dateien fuer {doc_id} in {ocr_dir}")
        return {"doc_id": doc_id, "pages": 0, "error": "no_files"}

    metadata = get_test_metadata(doc_id)
    lang = metadata.get("lang", "FR") if metadata else "FR"
    system_prompt = build_system_prompt(lang, variant=variant)
    total_pages = len(page_files)

    output_dir.mkdir(parents=True, exist_ok=True)

    stats = {
        "doc_id": doc_id,
        "pages": total_pages,
        "processed": 0,
        "skipped": 0,
        "errors": 0,
        "input_tokens": 0,
        "output_tokens": 0,
    }

    for page_file in page_files:
        page_num = extract_page_num(page_file)
        out_file = output_dir / page_file.name
        analysis_file = output_dir / f"{page_file.stem}.analysis.json"

        # Ueberspringe existierende
        if out_file.exists() and not force:
            stats["skipped"] += 1
            continue

        ocr_text = page_file.read_text(encoding="utf-8")
        user_msg = build_user_message(doc_id, page_num, total_pages, ocr_text, metadata)

        if dry_run:
            print(f"\n{'='*60}")
            print(f"  DRY RUN: {page_file.name}")
            print(f"{'='*60}")
            print(f"  System-Prompt ({len(system_prompt)} Zeichen):")
            print(f"  {system_prompt[:200]}...")
            print(f"\n  User-Message ({len(user_msg)} Zeichen):")
            print(f"  {user_msg[:300]}...")
            stats["skipped"] += 1
            continue

        try:
            print(f"    Seite {page_num}/{total_pages}...", end=" ", flush=True)
            start = time.time()

            result = call_anthropic(system_prompt, user_msg, api_key)
            # Re-parse mit korrekter Variante
            reparsed = parse_response(result["raw_response"], variant=variant)
            result["analysis"] = reparsed["analysis"]
            result["corrected"] = reparsed["corrected"]

            elapsed = time.time() - start
            stats["processed"] += 1
            stats["input_tokens"] += result["input_tokens"]
            stats["output_tokens"] += result["output_tokens"]

            # Korrigierten Text speichern
            out_file.write_text(result["corrected"], encoding="utf-8")

            # Analyse speichern
            analysis_data = {
                "doc_id": doc_id,
                "page": page_num,
                "variant": variant,
                "analysis": result["analysis"],
                "input_tokens": result["input_tokens"],
                "output_tokens": result["output_tokens"],
                "elapsed_seconds": round(elapsed, 1),
                "model": ANTHROPIC_MODEL,
            }
            analysis_file.write_text(
                json.dumps(analysis_data, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

            print(f"OK ({elapsed:.1f}s, {result['input_tokens']}+{result['output_tokens']} tokens)")

            # Kurze Pause zwischen Requests
            time.sleep(0.3)

        except Exception as e:
            stats["errors"] += 1
            print(f"FEHLER: {e}")

    return stats


def check_api_key(api_key: str) -> bool:
    """Prueft ob der API-Key gueltig ist."""
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key, timeout=10)
        response = client.messages.create(
            model=ANTHROPIC_MODEL,
            max_tokens=10,
            messages=[{"role": "user", "content": "Test"}],
        )
        print(f"API-Key gueltig. Modell: {ANTHROPIC_MODEL}")
        print(f"  Test-Tokens: {response.usage.input_tokens} input, {response.usage.output_tokens} output")
        return True
    except Exception as e:
        print(f"API-Key ungueltig oder Fehler: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="LLM OCR-Korrektur mit Claude Haiku 4.5"
    )
    parser.add_argument("--doc", nargs="+", help="Dokument-IDs (z.B. 2310 1180)")
    parser.add_argument("--phase", help="Testplan-Phase: phase1, phase2, ..., all")
    parser.add_argument("--all", action="store_true", help="Alle Testplan-Dokumente")
    parser.add_argument(
        "--ocr-dir",
        type=Path,
        default=MISTRAL_RESULTS_DIR,
        help="OCR-Verzeichnis (default: output/mistral_results)",
    )
    parser.add_argument(
        "--output", "-o",
        type=Path,
        default=LLM_CORRECTED_DIR,
        help="Ausgabeverzeichnis (default: output/llm_corrected)",
    )
    parser.add_argument("--variant", choices=VARIANTS, default="C",
                        help="Prompt-Variante: A=analysis+corrected, B=schlank, C=few-shot (default: C)")
    parser.add_argument("--dry-run", action="store_true", help="Nur Prompts anzeigen")
    parser.add_argument("--force", action="store_true", help="Existierende ueberschreiben")
    parser.add_argument("--check", action="store_true", help="Nur API-Key pruefen")

    args = parser.parse_args()

    # .env laden
    load_env()
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")

    if not api_key and not args.dry_run:
        print("FEHLER: ANTHROPIC_API_KEY nicht in .env gesetzt")
        print("  Key von https://console.anthropic.com/settings/keys holen")
        sys.exit(1)

    # --check: Nur Key pruefen
    if args.check:
        sys.exit(0 if check_api_key(api_key) else 1)

    # Output-Verzeichnis pro Variante (wenn nicht explizit gesetzt)
    if args.output == LLM_CORRECTED_DIR and args.variant != "A":
        args.output = LLM_CORRECTED_DIR.parent / f"llm_corrected_{args.variant.lower()}"

    # Doc-IDs bestimmen
    doc_ids = []
    if args.doc:
        doc_ids = args.doc
    elif args.phase:
        doc_ids = get_phase_doc_ids(args.phase)
    elif args.all:
        doc_ids = get_phase_doc_ids("all")

    if not doc_ids:
        print("FEHLER: --doc, --phase oder --all angeben")
        parser.print_help()
        sys.exit(1)

    # Verzeichnis pruefen
    if not args.ocr_dir.exists():
        print(f"FEHLER: OCR-Verzeichnis nicht gefunden: {args.ocr_dir}")
        sys.exit(1)

    # Header
    variant_names = {"A": "Analysis+Corrected", "B": "Schlank (nur Text)", "C": "Few-Shot"}
    mode = "DRY RUN" if args.dry_run else "LLM-Korrektur"
    print(f"\n{'='*60}")
    print(f"  {mode} mit {ANTHROPIC_MODEL}")
    print(f"  Variante: {args.variant} ({variant_names.get(args.variant, '?')})")
    print(f"  Quelle: {args.ocr_dir}")
    print(f"  Ausgabe: {args.output}")
    print(f"  Dokumente: {len(doc_ids)} ({', '.join(doc_ids)})")
    print(f"{'='*60}\n")

    # Verarbeitung
    all_stats = []
    total_start = time.time()

    for doc_id in doc_ids:
        print(f"  [{doc_id}]")
        stats = process_document(
            doc_id=doc_id,
            ocr_dir=args.ocr_dir,
            output_dir=args.output,
            api_key=api_key,
            dry_run=args.dry_run,
            force=args.force,
            variant=args.variant,
        )
        all_stats.append(stats)

    total_elapsed = time.time() - total_start

    # Summary
    total_processed = sum(s.get("processed", 0) for s in all_stats)
    total_skipped = sum(s.get("skipped", 0) for s in all_stats)
    total_errors = sum(s.get("errors", 0) for s in all_stats)
    total_input = sum(s.get("input_tokens", 0) for s in all_stats)
    total_output = sum(s.get("output_tokens", 0) for s in all_stats)

    print(f"\n{'='*60}")
    print(f"  Zusammenfassung")
    print(f"{'='*60}")
    print(f"  Verarbeitet: {total_processed} Seiten")
    print(f"  Uebersprungen: {total_skipped}")
    print(f"  Fehler: {total_errors}")
    print(f"  Tokens: {total_input:,} input + {total_output:,} output")
    print(f"  Dauer: {total_elapsed:.1f}s")

    # Manifest schreiben (nur wenn nicht dry-run)
    if not args.dry_run and total_processed > 0:
        manifest = {
            "timestamp": datetime.now().isoformat(),
            "model": ANTHROPIC_MODEL,
            "variant": args.variant,
            "source_dir": str(args.ocr_dir),
            "documents": all_stats,
            "totals": {
                "documents": len(doc_ids),
                "pages_processed": total_processed,
                "pages_skipped": total_skipped,
                "errors": total_errors,
                "input_tokens": total_input,
                "output_tokens": total_output,
                "elapsed_seconds": round(total_elapsed, 1),
            },
        }
        manifest_path = args.output / "manifest.json"
        manifest_path.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"\n  Manifest: {manifest_path}")


if __name__ == "__main__":
    main()
