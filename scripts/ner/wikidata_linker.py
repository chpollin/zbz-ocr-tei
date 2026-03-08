"""
Wikidata Reconciliation: Matcht NER-Entities gegen Wikidata.

Verwendet wbsearchentities + wbgetentities API.
Cache in output/entities/_wikidata_cache.json.

Aufruf:
    python -m scripts.ner.wikidata_linker --doc 2310
    python -m scripts.ner.wikidata_linker --all
    python -m scripts.ner.wikidata_linker --stats
"""

import argparse
import json
import sys
import time
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.config import (
    ENTITIES_DIR,
    WIKIDATA_API_URL,
    WIKIDATA_CACHE_PATH,
    WIKIDATA_RATE_LIMIT,
    WIKIDATA_USER_AGENT,
)
from scripts.ner.entity_store import EntityStore

# Typ-Filter: NER-Typ -> Wikidata P31 (instance of) QIDs
TYPE_INSTANCE_OF = {
    "person": {"Q5"},                          # human
    "organization": {"Q43229", "Q4830453",     # organization, business
                     "Q3918", "Q7278"},         # university, political party
    "place": {"Q515", "Q6256", "Q3624078",     # city, country, admin territory
              "Q486972", "Q5107"},              # settlement, continent
    "work": {"Q7725634", "Q571", "Q5633421",   # literary work, book, journal
             "Q13442814", "Q732577"},           # scholarly article, publication
}

# ISO 639-3 -> Wikidata Sprachcode
LANG_MAP = {"fra": "fr", "deu": "de", "eng": "en", "und": "en"}

# Persistenter Cache
_cache: dict[str, dict] = {}


# ---------------------------------------------------------------------------
# Cache
# ---------------------------------------------------------------------------

def load_cache() -> None:
    global _cache
    if WIKIDATA_CACHE_PATH.exists():
        _cache = json.loads(WIKIDATA_CACHE_PATH.read_text(encoding="utf-8"))
    else:
        _cache = {}


def save_cache() -> None:
    WIKIDATA_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    WIKIDATA_CACHE_PATH.write_text(
        json.dumps(_cache, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def _cache_key(entity_type: str, normalized: str) -> str:
    return f"{entity_type}:{normalized.lower().strip()}"


# ---------------------------------------------------------------------------
# Wikidata API
# ---------------------------------------------------------------------------

def _api_get(params: dict) -> dict | None:
    """Wikidata API GET mit Rate Limiting, Retry und User-Agent."""
    params["format"] = "json"
    headers = {"User-Agent": WIKIDATA_USER_AGENT}
    for attempt in range(3):
        try:
            resp = requests.get(WIKIDATA_API_URL, params=params,
                                headers=headers, timeout=15)
            resp.raise_for_status()
            time.sleep(WIKIDATA_RATE_LIMIT)
            return resp.json()
        except requests.RequestException as e:
            if attempt < 2:
                wait = 2 ** (attempt + 1)
                print(f"  Retry {attempt + 1}/3 Wikidata (warte {wait}s): {e}")
                time.sleep(wait)
            else:
                print(f"  WARNUNG: Wikidata-API-Fehler nach 3 Versuchen: {e}")
                return None
    return None


def search_wikidata(query: str, language: str = "en",
                    limit: int = 5) -> list[dict]:
    """Sucht Entities via wbsearchentities.

    Returns:
        Liste von Kandidaten: [{id, label, description}]
    """
    data = _api_get({
        "action": "wbsearchentities",
        "search": query,
        "language": language,
        "uselang": language,
        "limit": limit,
    })
    if not data:
        return []

    results = []
    for item in data.get("search", []):
        results.append({
            "qid": item.get("id", ""),
            "label": item.get("label", ""),
            "description": item.get("description", ""),
        })
    return results


def get_entity_types(qid: str) -> set[str]:
    """Holt P31 (instance of) Werte fuer eine Entity.

    Returns:
        Set von QIDs (z.B. {"Q5"} fuer human).
    """
    data = _api_get({
        "action": "wbgetentities",
        "ids": qid,
        "props": "claims",
    })
    if not data:
        return set()

    entity_data = data.get("entities", {}).get(qid, {})
    claims = entity_data.get("claims", {})
    p31_claims = claims.get("P31", [])

    types = set()
    for claim in p31_claims:
        mainsnak = claim.get("mainsnak", {})
        datavalue = mainsnak.get("datavalue", {})
        value = datavalue.get("value", {})
        if isinstance(value, dict) and "id" in value:
            types.add(value["id"])

    return types


def verify_type(qid: str, entity_type: str) -> bool:
    """Prueft ob eine Entity den erwarteten Typ hat (P31-Check)."""
    expected = TYPE_INSTANCE_OF.get(entity_type)
    if not expected:
        return True  # event, date: kein Type-Check

    actual = get_entity_types(qid)
    return bool(expected & actual)


# ---------------------------------------------------------------------------
# Reconciliation
# ---------------------------------------------------------------------------

def reconcile_entity(
    normalized: str,
    entity_type: str,
    doc_language: str = "und",
    context: str = "",
) -> dict | None:
    """Reconciliation einer einzelnen Entity.

    Returns:
        {qid, label, description, confidence} oder None.
    """
    # Cache pruefen
    key = _cache_key(entity_type, normalized)
    if key in _cache:
        cached = _cache[key]
        if cached is None:
            return None
        return cached

    # event/date: kein Wikidata-Lookup (zu unspezifisch)
    if entity_type in ("event", "date"):
        _cache[key] = None
        return None

    # Schweizer Korpus: immer FR + DE + EN durchsuchen
    wd_lang = LANG_MAP.get(doc_language, "en")
    languages = list(dict.fromkeys([wd_lang, "fr", "de", "en"]))  # dedupliziert, Reihenfolge erhalten

    for lang in languages:
        candidates = search_wikidata(normalized, language=lang, limit=5)
        if not candidates:
            continue

        # Exakter Label-Match (case-insensitive) -- Typ-Check uebersprungen
        # bei exaktem Match (spart 1 API-Call, >95% korrekt fuer bekannte Entities)
        for cand in candidates:
            if cand["label"].lower().strip() == normalized.lower().strip():
                result = {
                    "qid": cand["qid"],
                    "label": cand["label"],
                    "description": cand["description"],
                    "confidence": 1.0,
                }
                _cache[key] = result
                return result

        # Top-Kandidat mit Typ-Match (etwas weniger Confidence)
        for cand in candidates:
            if verify_type(cand["qid"], entity_type):
                result = {
                    "qid": cand["qid"],
                    "label": cand["label"],
                    "description": cand["description"],
                    "confidence": 0.8,
                }
                _cache[key] = result
                return result

    # Kein Match
    _cache[key] = None
    return None


def reconcile_store(store: EntityStore, doc_language: str = "und") -> dict:
    """Reconciled alle unresolved Entities in einem Store.

    Returns:
        Summary: {resolved, unresolved, skipped, errors}
    """
    unresolved = store.get_unresolved()
    resolved_count = 0
    skipped_count = 0

    for rec in unresolved:
        context = rec.contexts[0] if rec.contexts else ""
        result = reconcile_entity(
            rec.normalized, rec.entity_type,
            doc_language=doc_language, context=context,
        )

        if result:
            rec.wikidata_qid = result["qid"]
            rec.wikidata_label = result["label"]
            rec.wikidata_description = result["description"]
            rec.confidence = result["confidence"]
            resolved_count += 1
        else:
            skipped_count += 1

    return {
        "resolved": resolved_count,
        "unresolved": skipped_count,
        "total": len(unresolved),
    }


# ---------------------------------------------------------------------------
# Dokument-Verarbeitung
# ---------------------------------------------------------------------------

def process_document(doc_id: str, force: bool = False) -> dict:
    """Reconciled alle Entities eines Dokuments."""
    store = EntityStore.load(doc_id)
    if not store.entities:
        print(f"  {doc_id}: keine Entities gefunden")
        return {"doc_id": doc_id, "total": 0}

    # Sprache aus Store oder Metadaten
    doc_lang = "und"
    # Erste Seiten-JSON fuer Sprache checken
    page_files = sorted((ENTITIES_DIR / doc_id).glob(f"{doc_id}_p*_entities.json"))
    if page_files:
        page_data = json.loads(page_files[0].read_text(encoding="utf-8"))
        doc_lang = page_data.get("language", "und")

    result = reconcile_store(store, doc_language=doc_lang)

    # Store mit QIDs speichern
    store.save()

    summary = store.summary()
    print(f"  {doc_id}: {result['resolved']} resolved, "
          f"{result['unresolved']} unresolved, "
          f"Rate: {summary['resolution_rate']:.0%}")

    return summary


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Wikidata Reconciliation fuer NER Entities"
    )
    parser.add_argument("--doc", help="Einzelnes Dokument")
    parser.add_argument("--all", action="store_true",
                        help="Alle Dokumente mit Entities")
    parser.add_argument("--force", action="store_true",
                        help="Cache ignorieren, neu abfragen")
    parser.add_argument("--stats", action="store_true",
                        help="Statistiken anzeigen")
    args = parser.parse_args()

    load_cache()

    if args.stats:
        if not ENTITIES_DIR.exists():
            print("Keine Entity-Daten vorhanden.")
            return
        total_ents = 0
        total_resolved = 0
        for doc_dir in sorted(ENTITIES_DIR.iterdir()):
            if not doc_dir.is_dir():
                continue
            store = EntityStore.load(doc_dir.name)
            s = store.summary()
            total_ents += s["total_entities"]
            total_resolved += s["resolved"]
            if s["total_entities"] > 0:
                print(f"  {doc_dir.name}: {s['total_entities']} entities, "
                      f"{s['resolved']} resolved ({s['resolution_rate']:.0%})")
        print(f"\nGesamt: {total_ents} entities, "
              f"{total_resolved} resolved "
              f"({total_resolved/total_ents:.0%})" if total_ents > 0 else "")
        return

    if args.doc:
        doc_ids = [args.doc]
    elif args.all:
        if not ENTITIES_DIR.exists():
            print("Keine Entity-Daten vorhanden. Zuerst ner_extract ausfuehren.")
            return
        doc_ids = sorted(d.name for d in ENTITIES_DIR.iterdir()
                         if d.is_dir() and not d.name.startswith("_"))
    else:
        parser.print_help()
        return

    if args.force:
        _cache.clear()

    print(f"Wikidata Reconciliation: {len(doc_ids)} Dokumente")
    start = time.time()

    for i, doc_id in enumerate(doc_ids, 1):
        print(f"[{i}/{len(doc_ids)}] {doc_id}:")
        process_document(doc_id, force=args.force)

    save_cache()
    elapsed = round(time.time() - start, 1)
    print(f"\nFertig in {elapsed}s. Cache: {len(_cache)} Eintraege.")


if __name__ == "__main__":
    main()
