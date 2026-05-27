"""
Unified TEI Pipeline: Rule-Based Scaffold + Gemini Refinement.

4-Stufen-Pipeline:
  Step 1: Enhanced rule-based TEI (kostenlos, deterministisch)
  Step 2: Gemini Refinement (1 API-Call/Seite, Mapping-Table-Prompt)
  Step 3: Document Assembly (teiHeader + facsimile + body)
  Step 4: RelaxNG Validation (optional)

Aufruf:
    python -m scripts.tei.tei_unified --doc 2310
    python -m scripts.tei.tei_unified --sample
    python -m scripts.tei.tei_unified --all
    python -m scripts.tei.tei_unified --doc 2310 --step 1
    python -m scripts.tei.tei_unified --validate
    python -m scripts.tei.tei_unified --force
    python -m scripts.tei.tei_unified --dry-run
"""

import argparse
import functools
import json
import sys
import time
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.config import (
    DOC_METADATA_PATH,
    GEMINI_API_KEY,
    TEI_UNIFIED_DIR,
)
from scripts.core.loaders import (
    discover_documents,
    discover_pages,
    skip_jstor_cover,
)
from scripts.core.masterfile import mmsid_for
from scripts.tei.tei_generator import get_document_metadata
from scripts.tei.tei_step1 import process_page_step1
from scripts.tei.tei_step2 import process_page_step2
from scripts.tei.tei_step3 import assemble_document

# Lazy import fuer build_doc_hints / infer_genre (vermeidet zirkulaere Imports)
@functools.lru_cache(maxsize=1)
def _get_layout_qa():
    import scripts.layout.layout_qa_gemini as m
    return m


# ---------------------------------------------------------------------------
# Hilfsfunktionen
# ---------------------------------------------------------------------------

_raw_metadata_cache = None


def _load_raw_metadata(doc_id: str) -> dict | None:
    """Laedt Roh-Metadaten aus doc_metadata.json."""
    global _raw_metadata_cache
    if _raw_metadata_cache is None:
        if DOC_METADATA_PATH.exists():
            raw = json.loads(DOC_METADATA_PATH.read_text(encoding="utf-8"))
            _raw_metadata_cache = raw.get("documents", {})
        else:
            _raw_metadata_cache = {}
    return _raw_metadata_cache.get(str(doc_id))


# ---------------------------------------------------------------------------
# Dokument-Verarbeitung (Orchestrierung)
# ---------------------------------------------------------------------------

def process_document(
    doc_id: str,
    max_step: int = 3,
    force: bool = False,
    reassemble: bool = False,
    dry_run: bool = False,
    validate: bool = False,
    ner: bool = False,
) -> dict:
    """Verarbeitet ein Dokument durch alle Pipeline-Schritte.

    Args:
        reassemble: Nur Step 1+3 neu (mit Fixes), Step 2 aus Cache.
                    Kostenlos, kein Gemini-Call.

    Returns:
        Manifest-Dict mit Verarbeitungsstatistiken
    """
    start_time = time.time()

    # Metadaten laden
    metadata = get_document_metadata(doc_id) or {}

    # Erweiterte Metadaten aus doc_metadata.json
    raw_meta = _load_raw_metadata(doc_id)
    if raw_meta:
        metadata["has_jstor_cover"] = raw_meta.get("has_jstor_cover", False)
        metadata["page_count"] = raw_meta.get("page_count")

    # MMSID aus der Masterfile (Alma-Norm-ID, O8) -> <idno type="MMSID"> im Header
    metadata["mmsid"] = mmsid_for(doc_id)

    # Genre und Hints
    lqa = _get_layout_qa()
    desc = metadata.get("desc", "")
    pub_form = metadata.get("pub_form", "other")
    genre = lqa.infer_genre(desc, pub_form)
    metadata["genre"] = genre
    doc_hints = lqa.build_doc_hints(doc_id)

    # Seiten entdecken
    pages = discover_pages(doc_id)
    pages = skip_jstor_cover(pages, metadata)

    if not pages:
        print(f"  Keine Seiten fuer {doc_id}")
        return {"doc_id": doc_id, "status": "no_pages"}

    # Output-Verzeichnis
    doc_dir = TEI_UNIFIED_DIR / doc_id
    doc_dir.mkdir(parents=True, exist_ok=True)

    page_teis = {}
    page_facsimiles = {}
    step2_count = 0

    # Gemini-Client (nur fuer Step 2+)
    client = None
    if max_step >= 2 and not dry_run and GEMINI_API_KEY:
        try:
            from google import genai
            client = genai.Client(api_key=GEMINI_API_KEY)
        except Exception as e:
            print(f"  WARNUNG: Gemini-Client nicht verfuegbar: {e}")

    print(f"  Verarbeite {doc_id}: {len(pages)} Seiten, Genre={genre or 'standard'}")

    for page in pages:
        # Step 1: Enhanced Rule-Based TEI
        scaffold_path = doc_dir / f"{doc_id}_p{str(page).zfill(3)}_scaffold.xml"

        force_step1 = force or reassemble
        if scaffold_path.exists() and not force_step1:
            scaffold = scaffold_path.read_text(encoding="utf-8")
            facs_json_path = doc_dir / f"{doc_id}_p{str(page).zfill(3)}_facs.json"
            if facs_json_path.exists():
                facs_data = json.loads(facs_json_path.read_text(encoding="utf-8"))
            else:
                facs_data = {}
        else:
            scaffold, facs_data = process_page_step1(doc_id, page, metadata, genre)
            if scaffold:
                scaffold_path.write_text(scaffold, encoding="utf-8")
                facs_json_path = doc_dir / f"{doc_id}_p{str(page).zfill(3)}_facs.json"
                facs_json_path.write_text(
                    json.dumps(facs_data, ensure_ascii=False), encoding="utf-8"
                )

        if not scaffold:
            continue

        page_facsimiles[page] = facs_data

        # Step 2: Gemini Refinement
        if max_step >= 2:
            refined_path = doc_dir / f"{doc_id}_p{str(page).zfill(3)}_refined.xml"

            if refined_path.exists() and not force:
                refined = refined_path.read_text(encoding="utf-8")
            elif client or dry_run:
                refined = process_page_step2(
                    client, doc_id, page, scaffold,
                    metadata, genre, doc_hints, dry_run
                )
                if not dry_run and refined:
                    refined_path.write_text(refined, encoding="utf-8")
                step2_count += 1

                # Rate-Limiting (Gemini Flash Lite)
                if not dry_run:
                    time.sleep(0.5)
            else:
                refined = scaffold

            page_teis[page] = refined
        else:
            page_teis[page] = scaffold

    # Step 3: Document Assembly
    if max_step >= 3 and page_teis:
        final_xml = assemble_document(doc_id, page_teis, metadata, page_facsimiles)
        final_path = doc_dir / f"{doc_id}_final.xml"
        final_path.write_text(final_xml, encoding="utf-8")
        print(f"    -> {final_path.name} ({len(final_xml)} chars)")

    # Step 4: Validation
    validation_result = None
    if validate and max_step >= 3:
        try:
            from scripts.tei.tei_validator import validate_tei_file
            final_path = doc_dir / f"{doc_id}_final.xml"
            if final_path.exists():
                validation_result = validate_tei_file(final_path)
                val_path = doc_dir / f"{doc_id}_validation.json"
                val_path.write_text(
                    json.dumps(validation_result, ensure_ascii=False, indent=2),
                    encoding="utf-8"
                )
                status = "VALID" if validation_result.get("valid") else "INVALID"
                n_errors = len(validation_result.get("errors", []))
                print(f"    Validation: {status} ({n_errors} errors)")
        except ImportError:
            print("    WARNUNG: tei_validator nicht verfuegbar")

    # Step 5: NER Entity-Injection
    ner_result = None
    if ner and max_step >= 3:
        final_path = doc_dir / f"{doc_id}_final.xml"
        if final_path.exists():
            try:
                from scripts.ner.ner_inject_tei import process_document as ner_inject
                ner_result = ner_inject(doc_id, validate=validate)
                ner_status = "ok" if ner_result.get("status") != "error" else "error"
                injected = ner_result.get("injected", 0)
                print(f"    NER: {injected} entities injected ({ner_status})")
            except Exception as e:
                print(f"    NER WARNUNG: {e}")
                ner_result = {"status": "error", "error": str(e)}

    elapsed = time.time() - start_time

    # Manifest
    manifest = {
        "doc_id": doc_id,
        "genre": genre,
        "total_pages": len(pages),
        "pages_step1": len(page_teis),
        "pages_step2": step2_count,
        "has_final": (doc_dir / f"{doc_id}_final.xml").exists(),
        "elapsed_seconds": round(elapsed, 1),
        "max_step": max_step,
        "validation": validation_result,
        "ner": ner_result,
    }
    manifest_path = doc_dir / f"{doc_id}_manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    return manifest


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

SAMPLE_DOCS = ["2310", "2530", "1440"]


def main():
    parser = argparse.ArgumentParser(
        description="Unified TEI Pipeline: Rule-Based + Gemini Refinement"
    )
    parser.add_argument("--doc", help="Einzelnes Dokument (z.B. 2310)")
    parser.add_argument("--sample", action="store_true",
                        help=f"Pilotdokumente: {', '.join(SAMPLE_DOCS)}")
    parser.add_argument("--all", action="store_true", help="Alle Dokumente")
    parser.add_argument("--step", type=int, default=3, choices=[1, 2, 3],
                        help="Maximaler Step (1=nur Rule-Based, 2=+Gemini, 3=+Assembly)")
    parser.add_argument("--skip-validate", action="store_true",
                        help="Validierung ueberspringen (Default: aktiv)")
    parser.add_argument("--force", action="store_true",
                        help="Alle Schritte neu (inkl. Gemini)")
    parser.add_argument("--reassemble", action="store_true",
                        help="Nur Step 1+3 neu (Fixes anwenden), Step 2 aus Cache (kostenlos)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Prompts anzeigen, keine API-Calls")
    parser.add_argument("--ner", action="store_true",
                        help="Step 5: NER Entity-Injection in TEI")
    args = parser.parse_args()

    validate = not args.skip_validate

    reassemble = getattr(args, 'reassemble', False)

    print("=== Unified TEI Pipeline ===")
    print(f"  Step: 1-{args.step}"
          + (" + Validation" if validate else " (Validation OFF)")
          + (" + NER" if args.ner else "")
          + (" [REASSEMBLE: Step 1+3 neu, Step 2 Cache]" if reassemble else ""))

    if args.doc:
        doc_ids = [args.doc]
    elif args.sample:
        doc_ids = SAMPLE_DOCS
    elif args.all:
        doc_ids = discover_documents()
        print(f"  {len(doc_ids)} Dokumente gefunden")
    else:
        parser.print_help()
        return

    total_start = time.time()
    results = []

    for doc_id in doc_ids:
        print(f"\n--- Dokument {doc_id} ---")
        try:
            manifest = process_document(
                doc_id,
                max_step=args.step,
                force=args.force,
                reassemble=reassemble,
                dry_run=args.dry_run,
                validate=validate,
                ner=args.ner,
            )
            results.append(manifest)
        except Exception as e:
            print(f"  FEHLER: {e}")
            traceback.print_exc()
            results.append({"doc_id": doc_id, "status": "error", "error": str(e)})

    total_elapsed = time.time() - total_start

    # Zusammenfassung
    print(f"\n=== Zusammenfassung ===")
    print(f"  Dokumente: {len(results)}")
    ok = sum(1 for r in results if r.get("has_final"))
    print(f"  Erfolgreich: {ok}")
    total_pages = sum(r.get("pages_step1", 0) for r in results)
    print(f"  Seiten total: {total_pages}")
    step2_pages = sum(r.get("pages_step2", 0) for r in results)
    if step2_pages:
        print(f"  Gemini-Calls: {step2_pages}")
    print(f"  Dauer: {total_elapsed:.1f}s")
    print(f"  Output: {TEI_UNIFIED_DIR}")

    # Nach Batch-Run: Validierungsbericht erzeugen
    if validate and args.all:
        try:
            from scripts.tei.tei_validator import validate_all, generate_html_report
            print("\n=== Validierungsbericht ===")
            summary = validate_all(TEI_UNIFIED_DIR)
            print(f"  Valid: {summary['valid']}/{summary['total']}"
                  f" | Warnings: {summary['with_warnings']}")

            html_path = TEI_UNIFIED_DIR / "validation_report.html"
            generate_html_report(summary, html_path)

            json_path = TEI_UNIFIED_DIR / "validation_report.json"
            json_path.write_text(
                json.dumps(summary, ensure_ascii=False, indent=2),
                encoding="utf-8"
            )
        except Exception as e:
            print(f"  Validierungsbericht fehlgeschlagen: {e}")


if __name__ == "__main__":
    main()
