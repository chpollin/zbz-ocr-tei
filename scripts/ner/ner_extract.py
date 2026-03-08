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
import re
import sys
import time
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.config import (
    ENTITIES_DIR,
    GEMINI_API_KEY,
    GEMINI_MODEL,
)
from scripts.core.loaders import discover_documents, discover_pages, load_ocr_text
from scripts.ner.entity_index import EntityIndex
from scripts.ner.entity_store import EntityStore
from scripts.tei.tei_generator import get_document_metadata

SAMPLE_DOCS = [
    "2310", "2530", "1440",  # Original-Pilot (A/FR, B/FR, D/DE)
    "290", "1180", "890",    # A/FR, A/DE-FR bilingual, B/DE
    "3040", "90", "830",     # B/FR Lexikon, D/DE 1944, D/FR Bildband
    "1330", "40", "1520",    # D/FR Sammelband, C/FR Roman, C Monograph
    "1000", "1540", "100",   # B/FR DEMO, C DEMO, A/FR simple
]


def _build_known_entities_hint(index: EntityIndex) -> str:
    """Baut Prompt-Kontext aus dem Entity Index (bekannte Namen fuer bessere Erkennung)."""
    if not index.entries:
        return ""
    lines = ["\nKNOWN ENTITIES FROM INDEX (recognize these names and their variants):"]
    # Top-Entities nach Typ (max 50 pro Typ, sortiert nach Varianten)
    by_type: dict[str, list] = {}
    for entry in index.entries.values():
        by_type.setdefault(entry.entity_type, []).append(entry)
    for etype in ["person", "organization", "place", "work"]:
        entries = by_type.get(etype, [])
        if not entries:
            continue
        # Sortiere: Entries mit mehr Varianten zuerst (wichtiger)
        entries.sort(key=lambda e: len(e.variants), reverse=True)
        lines.append(f"  {etype.upper()}S:")
        for entry in entries[:50]:
            names = [entry.main_name] + entry.variants[:3]
            lines.append(f"    - {' / '.join(names)}")
    return "\n".join(lines)


def _strip_diacritics(text: str) -> str:
    """Strip diacritics for fuzzy matching (Etudes == Etudes)."""
    nfkd = unicodedata.normalize('NFKD', text)
    return ''.join(c for c in nfkd if not unicodedata.combining(c)).lower()

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
{known_entities}

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
    known_entities_hint: str = "",
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
        known_entities=known_entities_hint,
        ocr_text=ocr_text[:8000],  # Max 8k chars OCR (Flash Lite context)
    )

    if dry_run:
        print(f"  [DRY-RUN] {doc_id} p{page}: {len(prompt)} chars prompt, "
              f"{len(ocr_text)} chars OCR")
        return None

    from google import genai
    from google.genai import types

    # Retry mit exponentiellem Backoff (3 Versuche)
    response = None
    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=[types.Part.from_text(text=prompt)],
                config=types.GenerateContentConfig(
                    temperature=0.1,
                    max_output_tokens=4096,
                ),
            )
            break
        except Exception as e:
            err_str = str(e).lower()
            if "api_key" in err_str or "auth" in err_str or "permission" in err_str:
                raise
            if attempt < 2:
                wait = 2 ** (attempt + 1)
                print(f"  Retry {attempt + 1}/3 fuer {doc_id} p{page} "
                      f"(warte {wait}s): {e}")
                time.sleep(wait)
            else:
                print(f"  WARNUNG: Gemini-Fehler nach 3 Versuchen "
                      f"fuer {doc_id} p{page}: {e}")
                return None

    if response is None:
        return None

    try:
        result_text = response.text.strip()

        # JSON aus Markdown-Fences extrahieren
        json_match = re.search(r'```(?:json)?\s*(.*?)\s*```', result_text, re.DOTALL)
        if json_match:
            result_text = json_match.group(1)

        data = json.loads(result_text)

        # Validierung: surface muss im OCR-Text vorkommen
        ocr_lower = ocr_text.lower()
        ocr_stripped = _strip_diacritics(ocr_text)
        validated_entities = []
        for ent in data.get("entities", []):
            surface = ent.get("surface", "")
            if not surface:
                continue
            if surface in ocr_text:
                validated_entities.append(ent)
            elif surface.lower() in ocr_lower:
                validated_entities.append(ent)
            elif _strip_diacritics(surface) in ocr_stripped:
                # Diakritik-Fallback (Etudes vs Etudes)
                validated_entities.append(ent)

        data["entities"] = validated_entities
        data["entity_count"] = len(validated_entities)

        return data

    except json.JSONDecodeError as e:
        print(f"  WARNUNG: JSON-Parse-Fehler fuer {doc_id} p{page}: {e}")
        return None


# ---------------------------------------------------------------------------
# Dokument-Verarbeitung
# ---------------------------------------------------------------------------

# _discover_pages() -> scripts.core.loaders.discover_pages


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

    # Metadaten + Entity Index laden
    metadata = get_document_metadata(doc_id) or {}
    doc_hints = _build_doc_hints(doc_id, metadata)
    index = EntityIndex()
    index.load_all()
    known_entities_hint = _build_known_entities_hint(index)

    # Seiten ermitteln
    pages = discover_pages(doc_id)
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
            client, doc_id, page, ocr_text, doc_hints,
            known_entities_hint=known_entities_hint, dry_run=dry_run,
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

    # String-Matching-Pass: Index-Varianten gegen OCR-Text
    index_added = 0
    if index.entries and not dry_run:
        index_added = _index_matching_pass(store, index, doc_id, pages)

    # Store speichern
    if not dry_run:
        store.save()

    elapsed = round(time.time() - start_time, 1)
    summary = store.summary()
    summary["elapsed_seconds"] = elapsed
    summary["index_matched"] = index_added

    print(f"  {doc_id}: {pages_processed} Seiten, "
          f"{summary['total_entities']} Entities "
          f"({index_added} via Index-Match), "
          f"{total_entities} Mentions, "
          f"{elapsed}s")

    return summary


def _index_matching_pass(
    store: EntityStore,
    index: EntityIndex,
    doc_id: str,
    pages: list[int],
) -> int:
    """Zweiter Pass: Index-Varianten gegen OCR-Text matchen.

    Findet Entities die Gemini uebersehen hat, basierend auf den
    652+ Varianten im Entity Index. Kein API-Call noetig.

    Returns:
        Anzahl neu hinzugefuegter Entities.
    """
    added = 0

    # Baue Lookup: alle Index-Varianten -> (name, type)
    # Laengere Varianten zuerst (vermeidet partielle Matches)
    variant_map: list[tuple[str, str, str]] = []  # (variant, normalized, type)
    for entry in index.entries.values():
        if entry.entity_type not in ("person", "organization", "place"):
            continue  # Werke brauchen komplexere Erkennung
        for name in entry.all_names:
            if len(name) > 3:  # Skip zu kurze Varianten
                variant_map.append((name, entry.main_name, entry.entity_type))
    variant_map.sort(key=lambda x: len(x[0]), reverse=True)

    for page in pages:
        ocr_text = load_ocr_text(doc_id, page) or ""
        if not ocr_text:
            continue

        for variant, normalized, etype in variant_map:
            # Wortgrenzen-Match
            pattern = r'(?<!\w)' + re.escape(variant) + r'(?!\w)'
            if re.search(pattern, ocr_text):
                key = f"{etype}:{normalized.lower()}"
                if key not in store.entities:
                    # Neue Entity aus Index-Match
                    store.add_page_entities(page, [{
                        "surface": variant,
                        "type": etype,
                        "normalized": normalized,
                        "context": f"[Index-Match: {variant}]",
                    }])
                    added += 1
                elif page not in store.entities[key].pages:
                    store.entities[key].pages.append(page)
                    store.entities[key].count += 1

    return added


# discover_documents() -> scripts.core.loaders


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
