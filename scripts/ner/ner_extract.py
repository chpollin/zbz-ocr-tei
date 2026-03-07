"""
NER-Extraktion via Gemini Flash Lite.

Extrahiert Named Entities (person, organization, place, work, event, date)
aus OCR-Text. Ergebnis: JSON pro Seite und aggregierter EntityStore pro Dokument.

Aufruf:
    python -m scripts.ner.ner_extract --doc 2310
    python -m scripts.ner.ner_extract --sample
    python -m scripts.ner.ner_extract --all
    python -m scripts.ner.ner_extract --doc 2310 --dry-run
"""

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.config import (
    DOC_METADATA_PATH,
    ENTITIES_DIR,
    GEMINI_CORRECTED_A_DIR,
    GEMINI_CORRECTED_B_DIR,
    GEMINI_MODEL,
    LLM_CORRECTED_C_DIR,
    MISTRAL_RESULTS_DIR,
)
from scripts.ner.entity_store import EntityStore
from scripts.tei.tei_generator import get_document_metadata, load_ocr_text

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

SAMPLE_DOCS = ["2310", "2530", "1440"]

# ---------------------------------------------------------------------------
# NER Prompt
# ---------------------------------------------------------------------------

NER_PROMPT = """You are a Named Entity Recognition (NER) specialist for academic texts
from the Jeanne Hersch Edition (1910-2000), a Swiss philosopher who wrote primarily
in French and German.

TASK: Extract ALL named entities from the following OCR text page.

ENTITY TYPES (exactly 6):
- person: Individual humans (authors, philosophers, politicians, historical figures)
- organization: Institutions, universities, publishers, political bodies, journals
- place: Cities, countries, regions, geographical locations
- work: Book titles, article titles, journal names, philosophical works
- event: Historical events, conferences, wars, treaties
- date: Specific dates, years, centuries, date ranges

RULES:
1. Extract EVERY mention, including repeated names. If "Jaspers" appears 3 times,
   list it 3 times with different context snippets.
2. The "normalized" field should be the full canonical form:
   "Jaspers" -> "Karl Jaspers", "Hersch" -> "Jeanne Hersch"
3. For works, normalize to the full title in the original language.
4. The "context" field must contain the exact sentence fragment where the entity
   appears (max 120 chars), for disambiguation.
5. Do NOT extract:
   - Generic references ("the author", "he", "she", pronouns)
   - Adjective forms ("kantien", "cartesien", "hegelien")
   - Common nouns capitalized at sentence start
   - Page numbers, running headers, publisher addresses

DOCUMENT CONTEXT:
{doc_hints}

Return ONLY a JSON object with this structure:
{{
  "entities": [
    {{
      "surface": "exact text as in source",
      "type": "person|organization|place|work|event|date",
      "normalized": "canonical full form",
      "context": "sentence fragment containing the entity"
    }}
  ],
  "language": "fra|deu|eng|und",
  "entity_count": <number>
}}

OCR TEXT:
{ocr_text}
"""


# ---------------------------------------------------------------------------
# Gemini API Call
# ---------------------------------------------------------------------------

def extract_entities_page(
    client,
    doc_id: str,
    page: int,
    ocr_text: str,
    doc_hints: str,
    dry_run: bool = False,
) -> dict | None:
    """Extrahiert Entities aus einer Seite via Gemini.

    Returns:
        Parsed JSON dict oder None bei Fehler.
    """
    if not ocr_text or not ocr_text.strip():
        return {"entities": [], "language": "und", "entity_count": 0}

    prompt = NER_PROMPT.format(
        doc_hints=doc_hints,
        ocr_text=ocr_text[:8000],  # Max 8k chars OCR (Flash Lite context)
    )

    if dry_run:
        print(f"  [DRY-RUN] {doc_id} p{page}: {len(prompt)} chars prompt, "
              f"{len(ocr_text)} chars OCR")
        return None

    from google import genai
    from google.genai import types

    try:
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=[types.Part.from_text(text=prompt)],
            config=types.GenerateContentConfig(
                temperature=0.1,
                max_output_tokens=4096,
            ),
        )

        result_text = response.text.strip()

        # JSON aus Markdown-Fences extrahieren
        json_match = re.search(r'```(?:json)?\s*(.*?)\s*```', result_text, re.DOTALL)
        if json_match:
            result_text = json_match.group(1)

        data = json.loads(result_text)

        # Validierung: surface muss im OCR-Text vorkommen
        validated_entities = []
        for ent in data.get("entities", []):
            surface = ent.get("surface", "")
            if surface and surface in ocr_text:
                validated_entities.append(ent)
            elif surface:
                # Fuzzy: case-insensitive Suche
                if surface.lower() in ocr_text.lower():
                    validated_entities.append(ent)
                # else: halluziniert, verwerfen

        data["entities"] = validated_entities
        data["entity_count"] = len(validated_entities)

        return data

    except json.JSONDecodeError as e:
        print(f"  WARNUNG: JSON-Parse-Fehler fuer {doc_id} p{page}: {e}")
        return None
    except Exception as e:
        err_str = str(e).lower()
        if "api_key" in err_str or "auth" in err_str or "permission" in err_str:
            print(f"  FEHLER: Gemini-Auth-Fehler: {e}")
            raise
        print(f"  WARNUNG: Gemini-Fehler fuer {doc_id} p{page}: {e}")
        return None


# ---------------------------------------------------------------------------
# Dokument-Verarbeitung
# ---------------------------------------------------------------------------

def _discover_pages(doc_id: str) -> list[int]:
    """Findet alle Seitennummern fuer ein Dokument."""
    pages = set()
    for base_dir in [GEMINI_CORRECTED_B_DIR, GEMINI_CORRECTED_A_DIR,
                     LLM_CORRECTED_C_DIR, MISTRAL_RESULTS_DIR]:
        if base_dir.exists():
            for f in base_dir.glob(f"{doc_id}_p*.md"):
                match = re.match(rf'{doc_id}_p(\d+)\.md$', f.name)
                if match:
                    pages.add(int(match.group(1)))
    return sorted(pages)


def _build_doc_hints(doc_id: str, metadata: dict) -> str:
    """Baut Dokument-Kontext fuer den NER-Prompt."""
    parts = []
    title = metadata.get("title", doc_id)
    author = metadata.get("author", "Jeanne Hersch")
    lang = metadata.get("lang", "und")
    pub_form = metadata.get("pub_form", "other")
    date = metadata.get("date", "?")
    desc = metadata.get("desc", "")

    parts.append(f"Document: {title}")
    parts.append(f"Author: {author}")
    parts.append(f"Language: {lang}")
    parts.append(f"Publication form: {pub_form}")
    parts.append(f"Date: {date}")
    if desc:
        parts.append(f"Description: {desc[:200]}")

    return "\n".join(parts)


def extract_document(
    doc_id: str,
    force: bool = False,
    dry_run: bool = False,
) -> dict:
    """Verarbeitet alle Seiten eines Dokuments.

    Returns:
        Manifest dict mit Statistiken.
    """
    start_time = time.time()
    doc_dir = ENTITIES_DIR / doc_id
    doc_dir.mkdir(parents=True, exist_ok=True)

    # Check ob bereits verarbeitet
    store_path = doc_dir / f"{doc_id}_entities.json"
    if store_path.exists() and not force and not dry_run:
        print(f"  {doc_id}: bereits vorhanden (--force zum Ueberschreiben)")
        existing = json.loads(store_path.read_text(encoding="utf-8"))
        return existing.get("summary", {})

    # Metadaten laden
    metadata = get_document_metadata(doc_id) or {}
    doc_hints = _build_doc_hints(doc_id, metadata)

    # Seiten ermitteln
    pages = _discover_pages(doc_id)
    if not pages:
        print(f"  {doc_id}: keine Seiten gefunden")
        return {"doc_id": doc_id, "total_pages": 0}

    # Gemini Client initialisieren
    client = None
    if not dry_run:
        if not GEMINI_API_KEY:
            print("  FEHLER: GEMINI_API_KEY nicht gesetzt")
            return {"doc_id": doc_id, "error": "no_api_key"}
        from google import genai
        client = genai.Client(api_key=GEMINI_API_KEY)

    # Entity Store
    store = EntityStore(doc_id)
    total_entities = 0
    pages_processed = 0

    for page in pages:
        page_json_path = doc_dir / f"{doc_id}_p{page}_entities.json"

        # Skip falls bereits vorhanden
        if page_json_path.exists() and not force and not dry_run:
            page_data = json.loads(page_json_path.read_text(encoding="utf-8"))
            store.add_page_entities(page, page_data.get("entities", []))
            total_entities += page_data.get("entity_count", 0)
            pages_processed += 1
            continue

        ocr_text = load_ocr_text(doc_id, page) or ""
        result = extract_entities_page(
            client, doc_id, page, ocr_text, doc_hints, dry_run=dry_run
        )

        if result is None:
            continue

        # Per-Page JSON speichern
        page_result = {
            "doc_id": doc_id,
            "page": page,
            "model": GEMINI_MODEL,
            **result,
        }
        if not dry_run:
            page_json_path.write_text(
                json.dumps(page_result, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

        store.add_page_entities(page, result.get("entities", []))
        total_entities += result.get("entity_count", 0)
        pages_processed += 1

    # Seed-Entities anwenden
    seed_matched = store.apply_seed_entities()

    # Store speichern
    if not dry_run:
        store.save()

    elapsed = round(time.time() - start_time, 1)
    summary = store.summary()
    summary["elapsed_seconds"] = elapsed
    summary["seed_matched"] = seed_matched

    print(f"  {doc_id}: {pages_processed} Seiten, "
          f"{summary['total_entities']} Entities, "
          f"{total_entities} Mentions, "
          f"{elapsed}s")

    return summary


# ---------------------------------------------------------------------------
# Dokument-Discovery
# ---------------------------------------------------------------------------

def discover_documents() -> list[str]:
    """Findet alle Dokumente mit OCR-Daten."""
    doc_ids = set()
    for base_dir in [GEMINI_CORRECTED_B_DIR, GEMINI_CORRECTED_A_DIR,
                     LLM_CORRECTED_C_DIR, MISTRAL_RESULTS_DIR]:
        if base_dir.exists():
            for f in base_dir.glob("*_p*.md"):
                match = re.match(r'(\d+)_p\d+\.md$', f.name)
                if match:
                    doc_ids.add(match.group(1))
    return sorted(doc_ids)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="NER-Extraktion via Gemini Flash Lite"
    )
    parser.add_argument("--doc", help="Einzelnes Dokument (z.B. 2310)")
    parser.add_argument("--sample", action="store_true",
                        help=f"Pilotdokumente: {', '.join(SAMPLE_DOCS)}")
    parser.add_argument("--all", action="store_true",
                        help="Alle Dokumente verarbeiten")
    parser.add_argument("--force", action="store_true",
                        help="Bestehende Ergebnisse ueberschreiben")
    parser.add_argument("--dry-run", action="store_true",
                        help="Nur Prompts anzeigen, keine API-Calls")
    args = parser.parse_args()

    if args.doc:
        doc_ids = [args.doc]
    elif args.sample:
        doc_ids = SAMPLE_DOCS
    elif args.all:
        doc_ids = discover_documents()
    else:
        parser.print_help()
        return

    print(f"NER-Extraktion: {len(doc_ids)} Dokumente")
    print(f"  Modell: {GEMINI_MODEL}")
    print()

    total_start = time.time()
    results = []

    for i, doc_id in enumerate(doc_ids, 1):
        print(f"[{i}/{len(doc_ids)}] Dokument {doc_id}:")
        summary = extract_document(doc_id, force=args.force, dry_run=args.dry_run)
        results.append(summary)

    elapsed = round(time.time() - total_start, 1)
    total_ents = sum(r.get("total_entities", 0) for r in results)
    total_mentions = sum(r.get("total_mentions", 0) for r in results)

    print(f"\nFertig: {len(doc_ids)} Docs, "
          f"{total_ents} unique Entities, "
          f"{total_mentions} Mentions, "
          f"{elapsed}s")


if __name__ == "__main__":
    main()
