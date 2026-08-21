"""
Gemini-basierte OCR-Korrektur (Stage 2b): Zwei-Schritt-Verfahren.

Schritt 1 (Analyse): Identifiziert OCR-Fehler mit Begruendung und Konfidenz.
Schritt 2 (Korrektur): Wendet Analyse-Ergebnis an, gibt korrigierten Text aus.

Zwei Varianten:
  A - Text-only: OCR-Text + Metadaten-Kontext
  B - Multimodal: OCR-Text + Metadaten-Kontext + Scan-Bild

Output:
    output/gemini_corrected_a/  oder  output/gemini_corrected_b/
        {doc_id}_p{NNN}.md              # Korrigierter Text
        {doc_id}_p{NNN}.analysis.json   # Analyse (Schritt 1)
        manifest.json                   # Token-Statistik

Usage:
    python -m scripts.ocr.gemini_ocr_correct --doc 2310              # Einzeldokument
    python -m scripts.ocr.gemini_ocr_correct --sample                # 5 Pilot-Docs
    python -m scripts.ocr.gemini_ocr_correct --sample --variant B    # Multimodal
    python -m scripts.ocr.gemini_ocr_correct --step analyze          # Nur Schritt 1
    python -m scripts.ocr.gemini_ocr_correct --step correct          # Nur Schritt 2
    python -m scripts.ocr.gemini_ocr_correct --all                   # Alle Docs mit OCR
    python -m scripts.ocr.gemini_ocr_correct --force                 # Cache ueberschreiben
    python -m scripts.ocr.gemini_ocr_correct --dry-run               # Prompts anzeigen
"""

import argparse
import json
import os
import re
import sys
import time
import warnings
from datetime import datetime
from pathlib import Path

# Suppress Gemini SDK thought_signature warnings
warnings.filterwarnings("ignore", message=".*non-text parts.*thought_signature.*")

from scripts.config import (
    DOC_METADATA_PATH,
    GEMINI_API_KEY,
    GEMINI_CORRECTED_A_DIR,
    GEMINI_CORRECTED_B_DIR,
    GEMINI_MODEL,
    IMAGES_DIR,
    MISTRAL_RESULTS_DIR,
    get_test_metadata,
)
from scripts.utils import get_phase_doc_ids, load_json, write_json

_api_key = os.environ.get("GEMINI_API_KEY", "") or GEMINI_API_KEY

# --- Sample-Docs (5 Pilot-Docs mit Referenz-TEI, alle 4 Typen) ---

SAMPLE_DOC_IDS = ["2310", "1180", "890", "90", "40"]

# --- Dokumenttyp-Beschreibungen ---

TYPE_DESC = {
    "A": "Single-column, standard flowing text",
    "B": "Two-column (journal/lexicon)",
    "C": "Monograph (book, 100+ pages)",
    "D": "Special format (historical, interview, illustrated)",
}

# --- Analyse-Schema (Structured Output, Schritt 1) ---

ANALYSIS_SCHEMA = {
    "type": "object",
    "properties": {
        "corrections": {
            "type": "array",
            "description": "List of OCR errors found. MUST be empty if OCR quality is good.",
            "items": {
                "type": "object",
                "properties": {
                    "original": {
                        "type": "string",
                        "description": "Exact substring as it appears in the OCR text. Must be copy-pasted, not paraphrased.",
                    },
                    "corrected": {
                        "type": "string",
                        "description": "Corrected version of the substring. Empty string means delete (for artifacts).",
                    },
                    "category": {
                        "type": "string",
                        "description": "Type of OCR error: missing_accent (e->e-acute), wrong_character (rn->m), merged_words, split_word, missing_character, extra_character, ocr_artifact (JSTOR/platform text), punctuation, formatting, other",
                        "enum": [
                            "missing_accent",
                            "wrong_character",
                            "merged_words",
                            "split_word",
                            "missing_character",
                            "extra_character",
                            "ocr_artifact",
                            "punctuation",
                            "formatting",
                            "other",
                        ],
                    },
                    "confidence": {
                        "type": "string",
                        "description": "high = certain this is an error, medium = likely an error, low = uncertain",
                        "enum": ["high", "medium", "low"],
                    },
                    "justification": {
                        "type": "string",
                        "description": "One-sentence reason: what OCR error pattern caused this and why the correction is right",
                    },
                },
                "required": [
                    "original",
                    "corrected",
                    "category",
                    "confidence",
                    "justification",
                ],
            },
        },
        "overall_quality": {
            "type": "integer",
            "description": "OCR quality score 0-100. 95-100 = excellent (no/few errors), 80-94 = good, 60-79 = moderate, below 60 = poor",
        },
        "num_corrections": {
            "type": "integer",
            "description": "Total number of corrections in the list. Must match len(corrections).",
        },
        "summary": {
            "type": "string",
            "description": "One sentence: main error pattern found or 'No OCR errors detected' if quality is excellent",
        },
    },
    "required": ["corrections", "overall_quality", "num_corrections", "summary"],
}


# --- Prompts ---


def _lang_hint(lang_code):
    """Sprach-spezifische Hinweise fuer den Prompt."""
    hints = {
        "fra": "Language: French. Pay special attention to accents (e/e-acute/e-grave/e-circumflex), "
               "apostrophes (l', d', qu'), guillemets, and cedilla.",
        "deu": "Language: German. Pay special attention to umlauts (ae/oe/ue), eszett, "
               "and compound words.",
        "eng": "Language: English.",
    }
    # Handle mixed languages like "fra/deu"
    if "/" in str(lang_code):
        return (
            "Language: Mixed French/German. Pay attention to both French accents/apostrophes "
            "AND German umlauts/compounds."
        )
    return hints.get(str(lang_code), hints["fra"])


def build_analysis_prompt(variant, metadata):
    """Baut den Analyse-Prompt (Schritt 1)."""
    lang = metadata.get("language", "fra")
    doc_type = metadata.get("doc_type", "A")
    type_desc = TYPE_DESC.get(doc_type, "Unknown")
    pub_form = metadata.get("pub_form", "other")
    author = metadata.get("author") or "Jeanne Hersch"
    date = metadata.get("date") or "20th century"
    description = metadata.get("description") or ""

    base = (
        "You are an OCR error detection specialist. You analyze OCR text from "
        "scanned 20th-century academic documents (Jeanne Hersch archive, "
        "Zentralbibliothek Zurich, primarily French and German).\n\n"
        "Document context:\n"
        f"- Language: {lang}\n"
        f"- Document type: {doc_type} ({type_desc})\n"
        f"- Publication form: {pub_form}\n"
        f"- Author: {author}\n"
        f"- Era: {date}\n"
        f"- Description: {description}\n\n"
        f"{_lang_hint(lang)}\n\n"
        "TASK: Identify ONLY genuine OCR scanning errors in the text below. "
        "The OCR was produced by Mistral Document AI and is generally high quality.\n\n"
        "RULES:\n"
        "1. Flag character-level OCR errors: wrong/missing/extra characters, "
        "missing accents, character confusion (rn->m, cl->d)\n"
        "2. Flag platform artifacts (JSTOR footers, e-periodica disclaimers, "
        "'This content downloaded from...', 'Nutzungsbedingungen') as "
        "ocr_artifact with confidence=high\n"
        "3. Do NOT flag valid alternative spellings, stylistic choices, or "
        "archaic but correct forms\n"
        "4. Do NOT flag Markdown formatting (headings, bold, italic) as errors\n"
        "5. Do NOT invent corrections for text you cannot verify from context\n"
        "6. The 'original' field MUST be an exact substring of the OCR text -- "
        "copy-paste, do not paraphrase\n"
        "7. If OCR is already perfect, return an empty corrections list -- "
        "but do still flag platform artifacts\n"
        "8. Maximum 50 corrections per page\n\n"
        "EXAMPLES of correct analysis:\n\n"
        "Example 1 (French accent error):\n"
        "  original: \"phenomene\"\n"
        "  corrected: \"phenomene\" -> no, this is wrong: phenomene has no accent\n"
        "  CORRECT: original: \"phenomene\", corrected: \"ph\\u00e9nom\\u00e8ne\", "
        "category: missing_accent, confidence: high\n\n"
        "Example 2 (OCR character confusion):\n"
        "  original: \"inconnaisable\", corrected: \"inconnaissable\", "
        "category: missing_character, confidence: high, "
        "justification: \"Missing 's' -- common OCR drop in double consonants\"\n\n"
        "Example 3 (NOT an error -- do not flag):\n"
        "  \"oeuvre\" vs \"\\u0153uvre\" -- both valid French spellings, do NOT flag\n"
        "  \"Zurich\" vs \"Z\\u00fcrich\" -- valid without umlaut in French context\n\n"
        "Example 4 (Platform artifact):\n"
        "  original: \"This content downloaded from 130.60.149.195...\", "
        "corrected: \"\", category: ocr_artifact, confidence: high"
    )

    if variant == "B":
        base += (
            "\n\nYou also receive the scan image. VERIFY every proposed correction "
            "against the image. Only flag errors where the image clearly shows "
            "different text than the OCR output. If you cannot read the image "
            "clearly at a position, do NOT flag it."
        )

    return base


def build_correction_prompt(metadata):
    """Baut den Korrektur-Prompt (Schritt 2)."""
    lang = metadata.get("language", "fra")

    return (
        "You are a precise text editor. Apply ONLY the listed corrections to the "
        "OCR text. Output the corrected full text.\n\n"
        "CRITICAL RULES -- ANY VIOLATION IS A TOTAL FAILURE:\n"
        "1. Apply ONLY corrections marked confidence 'high' or 'medium'\n"
        "2. SKIP corrections marked 'low'\n"
        "3. Find each 'original' substring and replace with 'corrected'\n"
        "4. For ocr_artifact corrections (corrected=''), DELETE the artifact text\n"
        "5. Do NOT change ANY other text -- every character not in the correction "
        "list MUST remain identical\n"
        "6. Do NOT add commentary, notes, explanations, or metadata\n"
        "7. Do NOT paraphrase, rephrase, or 'improve' the text\n"
        "8. Do NOT fix errors you notice that are NOT in the correction list\n"
        "9. Preserve ALL Markdown formatting (## headings, **bold**, *italic*)\n"
        "10. Preserve exact paragraph breaks and line structure\n"
        "11. Output ONLY the corrected text, nothing else\n\n"
        "The output must be character-for-character identical to the input, "
        "except at the exact positions listed in the corrections.\n\n"
        f"Document language: {lang}\n"
    )


def format_corrections_for_prompt(corrections):
    """Formatiert Analyse-Korrekturen als lesbaren Text fuer Schritt 2."""
    if not corrections:
        return "No corrections needed."

    lines = []
    for i, c in enumerate(corrections, 1):
        conf = c.get("confidence", "?")
        if conf == "low":
            continue  # Low-Confidence gar nicht erst anzeigen
        lines.append(
            "{i}. '{orig}' -> '{corr}' [{cat}] (confidence: {conf}) -- {why}".format(
                i=i,
                orig=c.get("original", ""),
                corr=c.get("corrected", ""),
                cat=c.get("category", "other"),
                conf=conf,
                why=c.get("justification", ""),
            )
        )
    return "\n".join(lines) if lines else "No high/medium-confidence corrections."


# --- Metadaten ---


_metadata_cache = None


def get_doc_metadata(doc_id):
    """Laedt Metadaten aus doc_metadata.json (gecacht), Fallback auf TESTPLAN."""
    global _metadata_cache
    if _metadata_cache is None:
        _metadata_cache = load_json(DOC_METADATA_PATH) or {}
    meta = _metadata_cache
    if meta and doc_id in meta.get("documents", {}):
        dm = meta["documents"][doc_id]
        return {
            "language": dm.get("language", "fra"),
            "doc_type": dm.get("layout_type", "A"),
            "pub_form": dm.get("pub_form", "other"),
            "author": dm.get("author"),
            "date": dm.get("date"),
            "description": dm.get("description", ""),
        }

    # Fallback: TESTPLAN-Metadaten
    test_meta = get_test_metadata(doc_id)
    if test_meta:
        lang_map = {"FR": "fra", "DE": "deu", "DE/FR": "fra/deu", "EN": "eng"}
        return {
            "language": lang_map.get(test_meta.get("lang", "FR"), "fra"),
            "doc_type": test_meta.get("type", "A"),
            "pub_form": "other",
            "author": None,
            "date": None,
            "description": test_meta.get("desc", ""),
        }

    return {
        "language": "fra",
        "doc_type": "A",
        "pub_form": "other",
        "author": None,
        "date": None,
        "description": "",
    }


# --- Gemini Client ---


def get_client():
    """Gemini Client erstellen."""
    from google import genai

    if not _api_key:
        print("FEHLER: GEMINI_API_KEY nicht gesetzt. Bitte in .env eintragen.")
        sys.exit(1)
    return genai.Client(api_key=_api_key)


# --- Seiten-Dateien ---


def find_page_files(doc_id, ocr_dir):
    """Findet alle Seitendateien fuer ein Dokument, sortiert."""
    pattern = f"{doc_id}_p*.md"
    return sorted(Path(ocr_dir).glob(pattern))


def extract_page_str(filepath):
    """Extrahiert Seiten-String aus Dateiname (z.B. '2310_p001.md' -> '001')."""
    m = re.search(r"_p(\d+)\.md$", str(filepath.name))
    return m.group(1) if m else "001"


# --- Schritt 1: Analyse ---


def analyze_page(client, doc_id, page_str, variant, metadata, output_dir, force=False):
    """Schritt 1: OCR-Text analysieren und Fehler identifizieren."""
    from google.genai import types

    analysis_path = output_dir / f"{doc_id}_p{page_str}.analysis.json"
    if analysis_path.exists() and not force:
        cached = load_json(analysis_path)
        if cached:
            return cached

    # OCR-Text laden
    ocr_path = MISTRAL_RESULTS_DIR / f"{doc_id}_p{page_str}.md"
    if not ocr_path.exists():
        print(f"    WARN: OCR nicht gefunden: {ocr_path.name}")
        return None

    ocr_text = ocr_path.read_text(encoding="utf-8")
    if not ocr_text.strip():
        print(f"    SKIP: Leere Seite {ocr_path.name}")
        return None

    # Prompt bauen
    prompt = build_analysis_prompt(variant, metadata)
    user_content = f"OCR Text (page {page_str}):\n\n{ocr_text}"

    # Content-Parts
    contents = []
    if variant == "B":
        try:
            from PIL import Image

            padded = page_str.zfill(3)
            img_path = IMAGES_DIR / doc_id / f"{doc_id}_p{padded}.png"
            if img_path.exists():
                contents.append(Image.open(img_path))
            else:
                print(f"    WARN: Bild nicht gefunden: {img_path.name}")
        except ImportError:
            print("    WARN: PIL nicht installiert, Variante B ohne Bild")

    contents.append(prompt + "\n\n" + user_content)

    # API-Aufruf
    t0 = time.time()
    try:
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=contents,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=ANALYSIS_SCHEMA,
            ),
        )
        elapsed = time.time() - t0
        result = json.loads(response.text)
    except Exception as e:
        elapsed = time.time() - t0
        print(f"    FEHLER Analyse: {e} ({elapsed:.1f}s)")
        return None

    # Metadaten ergaenzen
    result["doc_id"] = doc_id
    result["page"] = page_str
    result["variant"] = variant
    result["elapsed_seconds"] = round(elapsed, 2)
    result["model"] = GEMINI_MODEL

    # Speichern
    output_dir.mkdir(parents=True, exist_ok=True)
    write_json(analysis_path, result)

    n_corr = result.get("num_corrections", len(result.get("corrections", [])))
    quality = result.get("overall_quality", "?")
    print(
        f"    Analyse p{page_str}: {n_corr} Korrekturen, Qualitaet {quality}/100 ({elapsed:.1f}s)"
    )

    return result


# --- Schritt 2: Korrektur ---


def correct_page(
    client, doc_id, page_str, variant, metadata, output_dir, analysis, force=False
):
    """Schritt 2: OCR-Text korrigieren basierend auf Analyse."""

    corrected_path = output_dir / f"{doc_id}_p{page_str}.md"
    if corrected_path.exists() and not force:
        return {"skipped": True}

    # OCR-Text laden
    ocr_path = MISTRAL_RESULTS_DIR / f"{doc_id}_p{page_str}.md"
    if not ocr_path.exists():
        return None

    ocr_text = ocr_path.read_text(encoding="utf-8")

    # Keine Korrekturen noetig? Original kopieren
    corrections = analysis.get("corrections", []) if analysis else []
    # Filtere low-confidence
    actionable = [c for c in corrections if c.get("confidence") != "low"]
    if not actionable:
        output_dir.mkdir(parents=True, exist_ok=True)
        corrected_path.write_text(ocr_text, encoding="utf-8")
        print(f"    Korrektur p{page_str}: keine Korrekturen, Original kopiert")
        return {"copied": True, "elapsed_seconds": 0}

    # Prompt bauen
    prompt = build_correction_prompt(metadata)
    corrections_text = format_corrections_for_prompt(corrections)

    user_content = (
        f"Original OCR text:\n\n{ocr_text}\n\n"
        f"Analysis (corrections to apply):\n\n{corrections_text}"
    )

    # Content-Parts
    contents = []
    if variant == "B":
        try:
            from PIL import Image

            padded = page_str.zfill(3)
            img_path = IMAGES_DIR / doc_id / f"{doc_id}_p{padded}.png"
            if img_path.exists():
                contents.append(Image.open(img_path))
        except ImportError:
            pass

    contents.append(prompt + "\n\n" + user_content)

    # API-Aufruf (Plain Text, kein Schema)
    t0 = time.time()
    try:
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=contents,
        )
        elapsed = time.time() - t0
        if not response or not response.text:
            print(f"    FEHLER Korrektur: Leere Antwort von Gemini ({elapsed:.1f}s)")
            return None
        corrected_text = response.text.strip()
    except Exception as e:
        elapsed = time.time() - t0
        print(f"    FEHLER Korrektur: {e} ({elapsed:.1f}s)")
        return None

    # Speichern
    output_dir.mkdir(parents=True, exist_ok=True)
    corrected_path.write_text(corrected_text, encoding="utf-8")

    print(
        f"    Korrektur p{page_str}: {len(actionable)} Korrekturen angewandt ({elapsed:.1f}s)"
    )

    return {"elapsed_seconds": round(elapsed, 2), "corrections_applied": len(actionable)}


# --- Dokument verarbeiten ---


def process_document(client, doc_id, output_dir, variant, step, force=False, dry_run=False):
    """Verarbeitet ein Dokument: Analyse + Korrektur aller Seiten."""
    page_files = find_page_files(doc_id, MISTRAL_RESULTS_DIR)
    if not page_files:
        print(f"  Keine OCR-Dateien fuer {doc_id} in {MISTRAL_RESULTS_DIR}")
        return {"doc_id": doc_id, "pages": 0, "error": "no_files"}

    metadata = get_doc_metadata(doc_id)
    total_pages = len(page_files)

    stats = {
        "doc_id": doc_id,
        "pages": total_pages,
        "analyzed": 0,
        "corrected": 0,
        "skipped": 0,
        "errors": 0,
        "copied": 0,
        "total_corrections": 0,
        "correction_categories": {},
        "quality_scores": [],
        "elapsed_seconds": 0,
    }

    for page_file in page_files:
        page_str = extract_page_str(page_file)

        if dry_run:
            prompt = build_analysis_prompt(variant, metadata)
            ocr_text = page_file.read_text(encoding="utf-8")
            print("\n{}".format("=" * 60))
            print(f"  DRY RUN: {doc_id}_p{page_str}")
            print("{}".format("=" * 60))
            print(f"  Variante: {variant}")
            print("  Metadaten: lang={}, type={}, pub_form={}".format(
                metadata.get("language"), metadata.get("doc_type"),
                metadata.get("pub_form"),
            ))
            print(f"  Analyse-Prompt ({len(prompt)} Zeichen):")
            print(f"  {prompt[:300]}...")
            print(f"\n  OCR-Text ({len(ocr_text)} Zeichen):")
            print(f"  {ocr_text[:200]}...")
            stats["skipped"] += 1
            continue

        page_start = time.time()

        # Schritt 1: Analyse
        analysis = None
        if step in ("analyze", "both"):
            analysis = analyze_page(
                client, doc_id, page_str, variant, metadata, output_dir, force
            )
            if analysis:
                stats["analyzed"] += 1
                quality = analysis.get("overall_quality")
                if quality is not None:
                    stats["quality_scores"].append(quality)
                for c in analysis.get("corrections", []):
                    cat = c.get("category", "other")
                    stats["correction_categories"][cat] = (
                        stats["correction_categories"].get(cat, 0) + 1
                    )
                    stats["total_corrections"] += 1
            else:
                # Analyse nicht laden moeglich und kein step=correct-only
                if step == "analyze":
                    stats["errors"] += 1
                    continue

        # Schritt 2: Korrektur
        if step in ("correct", "both"):
            # Wenn nur Korrektur: Analyse aus Cache laden
            if analysis is None and step == "correct":
                analysis_path = output_dir / f"{doc_id}_p{page_str}.analysis.json"
                analysis = load_json(analysis_path)
                if not analysis:
                    print(f"    SKIP p{page_str}: keine Analyse vorhanden")
                    stats["skipped"] += 1
                    continue

            result = correct_page(
                client, doc_id, page_str, variant, metadata, output_dir, analysis, force
            )
            if result:
                if result.get("skipped"):
                    stats["skipped"] += 1
                elif result.get("copied"):
                    stats["copied"] += 1
                    stats["corrected"] += 1
                else:
                    stats["corrected"] += 1
            else:
                stats["errors"] += 1

        stats["elapsed_seconds"] += round(time.time() - page_start, 2)

        # Kurze Pause zwischen API-Calls
        if not dry_run:
            time.sleep(0.2)

    return stats


# --- Hauptprogramm ---


def main():
    parser = argparse.ArgumentParser(
        description="Gemini OCR-Korrektur (Zwei-Schritt: Analyse + Korrektur)"
    )
    parser.add_argument("--doc", nargs="+", help="Dokument-IDs (z.B. 2310 1180)")
    parser.add_argument(
        "--sample",
        action="store_true",
        help="5 Sample-Docs (2310, 1180, 890, 90, 40)",
    )
    parser.add_argument("--phase", help="Testplan-Phase: phase1, phase2, ..., all")
    parser.add_argument("--all", action="store_true", help="Alle Docs mit OCR-Ergebnissen")
    parser.add_argument(
        "--variant",
        choices=["A", "B"],
        default="A",
        help="A=text-only, B=multimodal mit Scan-Bild (default: A)",
    )
    parser.add_argument(
        "--step",
        choices=["analyze", "correct", "both"],
        default="both",
        help="Schritt: analyze, correct, both (default: both)",
    )
    parser.add_argument("--force", action="store_true", help="Existierende ueberschreiben")
    parser.add_argument("--dry-run", action="store_true", help="Nur Prompts anzeigen")

    args = parser.parse_args()

    # Doc-IDs bestimmen
    doc_ids = []
    if args.doc:
        doc_ids = args.doc
    elif args.sample:
        doc_ids = SAMPLE_DOC_IDS
    elif args.phase:
        doc_ids = get_phase_doc_ids(args.phase)
    elif args.all:
        # Alle Docs mit OCR-Ergebnissen
        seen = set()
        for f in sorted(MISTRAL_RESULTS_DIR.glob("*_p*.md")):
            m = re.match(r"(\d+)_p", f.name)
            if m:
                seen.add(m.group(1))
        doc_ids = sorted(seen, key=lambda x: int(x))

    if not doc_ids:
        print("FEHLER: --doc, --sample, --phase oder --all angeben")
        parser.print_help()
        sys.exit(1)

    # Output-Verzeichnis
    output_dir = GEMINI_CORRECTED_A_DIR if args.variant == "A" else GEMINI_CORRECTED_B_DIR

    # Client (nur wenn nicht dry-run)
    client = None
    if not args.dry_run:
        if not _api_key:
            print("FEHLER: GEMINI_API_KEY nicht in .env gesetzt")
            sys.exit(1)
        client = get_client()

    # Header
    variant_names = {"A": "Text-only", "B": "Multimodal (mit Scan-Bild)"}
    step_names = {"analyze": "Nur Analyse", "correct": "Nur Korrektur", "both": "Analyse + Korrektur"}
    mode = "DRY RUN" if args.dry_run else "Gemini OCR-Korrektur"

    print("\n{}".format("=" * 60))
    print(f"  {mode} mit {GEMINI_MODEL}")
    print(f"  Variante: {args.variant} ({variant_names.get(args.variant)})")
    print(f"  Schritt: {step_names.get(args.step)}")
    print(f"  Ausgabe: {output_dir}")
    print("  Dokumente: {} ({})".format(len(doc_ids), ", ".join(doc_ids[:10])))
    if len(doc_ids) > 10:
        print(f"    ... und {len(doc_ids) - 10} weitere")
    print("{}".format("=" * 60))

    # Verarbeitung
    all_stats = []
    total_start = time.time()

    for i, doc_id in enumerate(doc_ids, 1):
        print(f"\n  [{i}/{len(doc_ids)}] Doc {doc_id}")
        stats = process_document(
            client=client,
            doc_id=doc_id,
            output_dir=output_dir,
            variant=args.variant,
            step=args.step,
            force=args.force,
            dry_run=args.dry_run,
        )
        all_stats.append(stats)

    total_elapsed = time.time() - total_start

    # Summary
    total_analyzed = sum(s.get("analyzed", 0) for s in all_stats)
    total_corrected = sum(s.get("corrected", 0) for s in all_stats)
    total_skipped = sum(s.get("skipped", 0) for s in all_stats)
    total_copied = sum(s.get("copied", 0) for s in all_stats)
    total_errors = sum(s.get("errors", 0) for s in all_stats)
    total_corrections = sum(s.get("total_corrections", 0) for s in all_stats)

    # Kategorie-Aggregation
    all_categories = {}
    all_quality = []
    for s in all_stats:
        for cat, n in s.get("correction_categories", {}).items():
            all_categories[cat] = all_categories.get(cat, 0) + n
        all_quality.extend(s.get("quality_scores", []))

    avg_quality = (
        round(sum(all_quality) / len(all_quality), 1) if all_quality else None
    )

    print("\n{}".format("=" * 60))
    print("  Zusammenfassung")
    print("{}".format("=" * 60))
    print(f"  Analysiert: {total_analyzed} Seiten")
    print(f"  Korrigiert: {total_corrected} Seiten ({total_copied} Original kopiert)")
    print(f"  Uebersprungen: {total_skipped}")
    print(f"  Fehler: {total_errors}")
    print(f"  Korrekturen gesamt: {total_corrections}")
    if avg_quality is not None:
        print(f"  Durchschn. OCR-Qualitaet: {avg_quality}/100")
    if all_categories:
        print("  Kategorien: {}".format(
            ", ".join(f"{k}={v}" for k, v in
                      sorted(all_categories.items(), key=lambda x: -x[1]))
        ))
    print(f"  Dauer: {total_elapsed:.1f}s")

    # Manifest schreiben
    if not args.dry_run and (total_analyzed > 0 or total_corrected > 0):
        manifest = {
            "timestamp": datetime.now().isoformat(),
            "model": GEMINI_MODEL,
            "variant": args.variant,
            "step": args.step,
            "source_dir": str(MISTRAL_RESULTS_DIR),
            "documents": all_stats,
            "totals": {
                "documents": len(doc_ids),
                "pages_analyzed": total_analyzed,
                "pages_corrected": total_corrected,
                "pages_copied": total_copied,
                "pages_skipped": total_skipped,
                "errors": total_errors,
                "total_corrections": total_corrections,
                "avg_quality_score": avg_quality,
                "correction_categories": all_categories,
                "elapsed_seconds": round(total_elapsed, 1),
            },
        }
        output_dir.mkdir(parents=True, exist_ok=True)
        manifest_path = output_dir / "manifest.json"
        write_json(manifest_path, manifest)
        print(f"\n  Manifest: {manifest_path}")


if __name__ == "__main__":
    main()
