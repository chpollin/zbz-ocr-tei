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
        manifest.json                   # Token-/Kostenstatistik

Usage:
    python -m scripts.gemini_ocr_correct --doc 2310              # Einzeldokument
    python -m scripts.gemini_ocr_correct --sample                # 5 Pilot-Docs
    python -m scripts.gemini_ocr_correct --sample --variant B    # Multimodal
    python -m scripts.gemini_ocr_correct --step analyze          # Nur Schritt 1
    python -m scripts.gemini_ocr_correct --step correct          # Nur Schritt 2
    python -m scripts.gemini_ocr_correct --all                   # Alle Docs mit OCR
    python -m scripts.gemini_ocr_correct --force                 # Cache ueberschreiben
    python -m scripts.gemini_ocr_correct --dry-run               # Prompts anzeigen
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

from dotenv import load_dotenv

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

# .env laden
load_dotenv()
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
            "items": {
                "type": "object",
                "properties": {
                    "original": {
                        "type": "string",
                        "description": "Text as it appears in OCR",
                    },
                    "corrected": {
                        "type": "string",
                        "description": "Proposed correction",
                    },
                    "category": {
                        "type": "string",
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
                        "enum": ["high", "medium", "low"],
                    },
                    "justification": {
                        "type": "string",
                        "description": "Brief reason why this correction is needed",
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
            "description": "OCR quality score 0-100 (100=perfect, 0=unreadable)",
        },
        "num_corrections": {"type": "integer"},
        "summary": {
            "type": "string",
            "description": "Brief summary of OCR quality issues found",
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
        "You are an OCR quality analyst for scanned academic texts from the "
        "Jeanne Hersch archive (Zentralbibliothek Zurich, 20th century, "
        "primarily French and German).\n\n"
        "You receive OCR text produced by Mistral Document AI from a scanned page. "
        "Analyze the text and identify OCR errors that need correction.\n\n"
        "Document context:\n"
        "- Language: {lang}\n"
        "- Document type: {doc_type} ({type_desc})\n"
        "- Publication form: {pub_form}\n"
        "- Author: {author}\n"
        "- Era: {date}\n"
        "- Description: {description}\n\n"
        "{lang_hint}\n\n"
        "RULES:\n"
        "- Only flag CLEAR OCR errors, not stylistic choices or valid alternative spellings\n"
        "- Common OCR error types: missing/wrong accents (French), wrong characters, "
        "merged/split words, JSTOR artifacts, repeated page numbers\n"
        "- Set confidence=high only when you are CERTAIN the change is correct\n"
        "- Set confidence=medium when likely correct but some ambiguity exists\n"
        "- Set confidence=low for changes where the original might also be valid\n"
        "- Do NOT flag Markdown formatting as errors unless clearly broken\n"
        "- JSTOR headers/footers ('This content downloaded from...') are artifacts: "
        "flag as ocr_artifact with confidence=high\n"
        "- Maximum 50 corrections per page (prioritize high-confidence ones)\n"
        "- Do NOT invent or hallucinate text that is not implied by context\n"
        "- If the OCR quality is already excellent (few or no errors), "
        "return an empty corrections list"
    ).format(
        lang=lang,
        doc_type=doc_type,
        type_desc=type_desc,
        pub_form=pub_form,
        author=author,
        date=date,
        description=description,
        lang_hint=_lang_hint(lang),
    )

    if variant == "B":
        base += (
            "\n\nYou also receive the scan image of the page. Use the image to VERIFY "
            "your corrections: compare the OCR text against what is actually visible "
            "in the scan. Only propose corrections that are supported by the visible "
            "text in the image."
        )

    return base


def build_correction_prompt(metadata):
    """Baut den Korrektur-Prompt (Schritt 2)."""
    lang = metadata.get("language", "fra")

    return (
        "You are an OCR text corrector for the Jeanne Hersch archive "
        "(Zentralbibliothek Zurich, 20th century academic texts).\n\n"
        "You receive:\n"
        "1. The original OCR text (from Mistral Document AI)\n"
        "2. An analysis of OCR errors found in the text\n\n"
        "Your task: Apply the corrections from the analysis to produce a clean, "
        "corrected version of the full text.\n\n"
        "RULES:\n"
        "- Apply ONLY the corrections listed in the analysis\n"
        "- Apply only corrections marked as confidence 'high' or 'medium'\n"
        "- Skip corrections marked as confidence 'low'\n"
        "- Preserve ALL Markdown formatting (**bold**, *italic*, ## headings)\n"
        "- Preserve the exact structure and paragraph breaks of the original\n"
        "- Do NOT add, remove, or rearrange content beyond the listed corrections\n"
        "- Do NOT paraphrase or rephrase\n"
        "- Remove OCR artifacts (JSTOR headers, copyright lines) "
        "flagged in the analysis\n"
        "- Output ONLY the corrected text, no commentary or explanation\n\n"
        "Document language: {lang}\n"
    ).format(lang=lang)


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
    pattern = "{}_p*.md".format(doc_id)
    return sorted(Path(ocr_dir).glob(pattern))


def extract_page_str(filepath):
    """Extrahiert Seiten-String aus Dateiname (z.B. '2310_p001.md' -> '001')."""
    m = re.search(r"_p(\d+)\.md$", str(filepath.name))
    return m.group(1) if m else "001"


# --- Schritt 1: Analyse ---


def analyze_page(client, doc_id, page_str, variant, metadata, output_dir, force=False):
    """Schritt 1: OCR-Text analysieren und Fehler identifizieren."""
    from google.genai import types

    analysis_path = output_dir / "{}_p{}.analysis.json".format(doc_id, page_str)
    if analysis_path.exists() and not force:
        cached = load_json(analysis_path)
        if cached:
            return cached

    # OCR-Text laden
    ocr_path = MISTRAL_RESULTS_DIR / "{}_p{}.md".format(doc_id, page_str)
    if not ocr_path.exists():
        print("    WARN: OCR nicht gefunden: {}".format(ocr_path.name))
        return None

    ocr_text = ocr_path.read_text(encoding="utf-8")
    if not ocr_text.strip():
        print("    SKIP: Leere Seite {}".format(ocr_path.name))
        return None

    # Prompt bauen
    prompt = build_analysis_prompt(variant, metadata)
    user_content = "OCR Text (page {page}):\n\n{text}".format(
        page=page_str, text=ocr_text
    )

    # Content-Parts
    contents = []
    if variant == "B":
        try:
            from PIL import Image

            padded = page_str.zfill(3)
            img_path = IMAGES_DIR / doc_id / "{}_p{}.png".format(doc_id, padded)
            if img_path.exists():
                contents.append(Image.open(img_path))
            else:
                print("    WARN: Bild nicht gefunden: {}".format(img_path.name))
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
        print("    FEHLER Analyse: {} ({:.1f}s)".format(e, elapsed))
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
        "    Analyse p{}: {} Korrekturen, Qualitaet {}/100 ({:.1f}s)".format(
            page_str, n_corr, quality, elapsed
        )
    )

    return result


# --- Schritt 2: Korrektur ---


def correct_page(
    client, doc_id, page_str, variant, metadata, output_dir, analysis, force=False
):
    """Schritt 2: OCR-Text korrigieren basierend auf Analyse."""
    from google.genai import types

    corrected_path = output_dir / "{}_p{}.md".format(doc_id, page_str)
    if corrected_path.exists() and not force:
        return {"skipped": True}

    # OCR-Text laden
    ocr_path = MISTRAL_RESULTS_DIR / "{}_p{}.md".format(doc_id, page_str)
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
        print("    Korrektur p{}: keine Korrekturen, Original kopiert".format(page_str))
        return {"copied": True, "elapsed_seconds": 0}

    # Prompt bauen
    prompt = build_correction_prompt(metadata)
    corrections_text = format_corrections_for_prompt(corrections)

    user_content = (
        "Original OCR text:\n\n{ocr}\n\n"
        "Analysis (corrections to apply):\n\n{corr}"
    ).format(ocr=ocr_text, corr=corrections_text)

    # Content-Parts
    contents = []
    if variant == "B":
        try:
            from PIL import Image

            padded = page_str.zfill(3)
            img_path = IMAGES_DIR / doc_id / "{}_p{}.png".format(doc_id, padded)
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
            print("    FEHLER Korrektur: Leere Antwort von Gemini ({:.1f}s)".format(elapsed))
            return None
        corrected_text = response.text.strip()
    except Exception as e:
        elapsed = time.time() - t0
        print("    FEHLER Korrektur: {} ({:.1f}s)".format(e, elapsed))
        return None

    # Speichern
    output_dir.mkdir(parents=True, exist_ok=True)
    corrected_path.write_text(corrected_text, encoding="utf-8")

    print(
        "    Korrektur p{}: {} Korrekturen angewandt ({:.1f}s)".format(
            page_str, len(actionable), elapsed
        )
    )

    return {"elapsed_seconds": round(elapsed, 2), "corrections_applied": len(actionable)}


# --- Dokument verarbeiten ---


def process_document(client, doc_id, output_dir, variant, step, force=False, dry_run=False):
    """Verarbeitet ein Dokument: Analyse + Korrektur aller Seiten."""
    page_files = find_page_files(doc_id, MISTRAL_RESULTS_DIR)
    if not page_files:
        print("  Keine OCR-Dateien fuer {} in {}".format(doc_id, MISTRAL_RESULTS_DIR))
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
            print("  DRY RUN: {}_p{}".format(doc_id, page_str))
            print("{}".format("=" * 60))
            print("  Variante: {}".format(variant))
            print("  Metadaten: lang={}, type={}, pub_form={}".format(
                metadata.get("language"), metadata.get("doc_type"),
                metadata.get("pub_form"),
            ))
            print("  Analyse-Prompt ({} Zeichen):".format(len(prompt)))
            print("  {}...".format(prompt[:300]))
            print("\n  OCR-Text ({} Zeichen):".format(len(ocr_text)))
            print("  {}...".format(ocr_text[:200]))
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
                analysis_path = output_dir / "{}_p{}.analysis.json".format(
                    doc_id, page_str
                )
                analysis = load_json(analysis_path)
                if not analysis:
                    print("    SKIP p{}: keine Analyse vorhanden".format(page_str))
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
    print("  {} mit {}".format(mode, GEMINI_MODEL))
    print("  Variante: {} ({})".format(args.variant, variant_names.get(args.variant)))
    print("  Schritt: {}".format(step_names.get(args.step)))
    print("  Ausgabe: {}".format(output_dir))
    print("  Dokumente: {} ({})".format(len(doc_ids), ", ".join(doc_ids[:10])))
    if len(doc_ids) > 10:
        print("    ... und {} weitere".format(len(doc_ids) - 10))
    print("{}".format("=" * 60))

    # Verarbeitung
    all_stats = []
    total_start = time.time()

    for i, doc_id in enumerate(doc_ids, 1):
        print("\n  [{}/{}] Doc {}".format(i, len(doc_ids), doc_id))
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
    print("  Analysiert: {} Seiten".format(total_analyzed))
    print("  Korrigiert: {} Seiten ({} Original kopiert)".format(
        total_corrected, total_copied
    ))
    print("  Uebersprungen: {}".format(total_skipped))
    print("  Fehler: {}".format(total_errors))
    print("  Korrekturen gesamt: {}".format(total_corrections))
    if avg_quality is not None:
        print("  Durchschn. OCR-Qualitaet: {}/100".format(avg_quality))
    if all_categories:
        print("  Kategorien: {}".format(
            ", ".join("{}={}".format(k, v) for k, v in
                      sorted(all_categories.items(), key=lambda x: -x[1]))
        ))
    print("  Dauer: {:.1f}s".format(total_elapsed))

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
        print("\n  Manifest: {}".format(manifest_path))


if __name__ == "__main__":
    main()
