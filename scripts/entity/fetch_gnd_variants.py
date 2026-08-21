"""Build the versioned GND cache for the entity integration (M1).

Reads every GND id from the curated entity list (persons, organisations, works),
asks lobid.org for the authority record and stores name variants, life dates,
entity types and the Wikidata QID in data/entities/gnd_cache.json. The same pass
validates the ids: a defective id answers 404, which is a legitimate result and
gets recorded as such.

Read-only with respect to the entity list and the TEI corpus; the only write is
the cache file. Standard library only, no API key, deterministic apart from the
retrieval date.

Usage:
    python -m scripts.entity.fetch_gnd_variants
    python -m scripts.entity.fetch_gnd_variants --entities PATH --out PATH
"""
import argparse
import json
import re
import time
import urllib.error
import urllib.request
from datetime import date
from pathlib import Path

from scripts.config import DATA_DIR

SOURCE_PATTERN = "https://lobid.org/gnd/{id}.json"
ENTITIES_PATH = DATA_DIR / "entities" / "all_entities.json"
CACHE_PATH = DATA_DIR / "entities" / "gnd_cache.json"

CATEGORIES = ("persons", "organisations", "works")
TIMEOUT_SECONDS = 15
REQUEST_PAUSE_SECONDS = 0.15
PROGRESS_EVERY = 25
USER_AGENT = "zbz-ocr-tei entity integration (lobid batch lookup)"

# lobid marks every record with this umbrella type; it carries no information.
_UMBRELLA_TYPE = "AuthorityResource"
_WIKIDATA_RE = re.compile(r"^https?://www\.wikidata\.org/entity/(Q[0-9]+)$")


def _first(values):
    """First entry of a lobid value list, or None when absent or empty."""
    if isinstance(values, list) and values:
        return values[0]
    return None


def _wikidata_qid(same_as) -> str | None:
    """Pick the Wikidata QID out of the lobid sameAs list."""
    if not isinstance(same_as, list):
        return None
    for item in same_as:
        target = item.get("id") if isinstance(item, dict) else item
        m = _WIKIDATA_RE.match(target) if isinstance(target, str) else None
        if m:
            return m.group(1)
    return None


def parse_lobid_record(data: dict) -> dict:
    """Project a lobid JSON record onto the cache entry contract."""
    types = [t for t in data.get("type", []) if t != _UMBRELLA_TYPE]
    variants = [v for v in data.get("variantName", []) if isinstance(v, str)]
    return {
        "http_status": 200,
        "preferred_name": data.get("preferredName"),
        "variant_names": variants,
        "types": types,
        "date_of_birth": _first(data.get("dateOfBirth")),
        "date_of_death": _first(data.get("dateOfDeath")),
        "wikidata": _wikidata_qid(data.get("sameAs")),
    }


def collect_gnd_ids(entities: dict) -> list:
    """All non-empty GND ids across the three lists, deduplicated, in list order."""
    ids = []
    seen = set()
    for category in CATEGORIES:
        for entry in entities.get(category) or []:
            gnd_id = entry.get("GND_id")
            if not isinstance(gnd_id, str) or not gnd_id.strip():
                continue
            gnd_id = gnd_id.strip()
            if gnd_id not in seen:
                seen.add(gnd_id)
                ids.append(gnd_id)
    return ids


def fetch_record(gnd_id: str) -> dict:
    """One lobid lookup with a single retry. 404 is a result, never a retry cause."""
    request = urllib.request.Request(
        SOURCE_PATTERN.format(id=gnd_id),
        headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
    )
    status, error = None, "no attempt"
    for attempt in (1, 2):
        try:
            with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
                return parse_lobid_record(json.loads(response.read().decode("utf-8")))
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                return {"http_status": 404}
            status, error = exc.code, f"HTTP {exc.code}"
        except (urllib.error.URLError, OSError, ValueError) as exc:
            status, error = None, str(exc)
        if attempt == 1:
            time.sleep(REQUEST_PAUSE_SECONDS)
    return {"http_status": status, "error": error}


def build_payload(entries: dict, retrieved: str) -> dict:
    """Assemble the cache file contract around the fetched entries."""
    return {"retrieved": retrieved, "source_pattern": SOURCE_PATTERN, "entries": entries}


def fetch_all(gnd_ids, verbose: bool = True) -> dict:
    entries = {}
    total = len(gnd_ids)
    for index, gnd_id in enumerate(gnd_ids, start=1):
        entries[gnd_id] = fetch_record(gnd_id)
        if verbose and (index % PROGRESS_EVERY == 0 or index == total):
            print(f"  {index}/{total} abgefragt")
        if index < total:
            time.sleep(REQUEST_PAUSE_SECONDS)
    return entries


def _summarize(entries: dict) -> dict:
    ok = [e for e in entries.values() if e.get("http_status") == 200]
    return {
        "total": len(entries),
        "ok": len(ok),
        "not_found": sum(1 for e in entries.values() if e.get("http_status") == 404),
        "failed": sum(1 for e in entries.values() if e.get("http_status") not in (200, 404)),
        "variants": sum(len(e.get("variant_names", [])) for e in ok),
        "wikidata": sum(1 for e in ok if e.get("wikidata")),
    }


def _print_summary(stats: dict, out_path: Path) -> None:
    print("\nGND-Cache (lobid.org)")
    print(f"  IDs gesamt:        {stats['total']}")
    print(f"  HTTP 200:          {stats['ok']}")
    print(f"  HTTP 404:          {stats['not_found']}")
    if stats["failed"]:
        print(f"  fehlgeschlagen:    {stats['failed']}")
    print(f"  Namensvarianten:   {stats['variants']}")
    print(f"  mit Wikidata-QID:  {stats['wikidata']}")
    print(f"  Cache: {out_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="lobid-GND-Abruf: baut den Varianten-Cache")
    parser.add_argument("--entities", default=str(ENTITIES_PATH), help="Entitaetendatei (JSON)")
    parser.add_argument("--out", default=str(CACHE_PATH), help="Zieldatei fuer den Cache")
    args = parser.parse_args()

    entities_path, out_path = Path(args.entities), Path(args.out)
    if not entities_path.exists():
        print(f"FEHLER: Entitaetendatei nicht gefunden: {entities_path}")
        return

    entities = json.loads(entities_path.read_text(encoding="utf-8"))
    gnd_ids = collect_gnd_ids(entities)
    print(f"lobid-Abruf fuer {len(gnd_ids)} GND-IDs (Timeout {TIMEOUT_SECONDS}s)")
    entries = fetch_all(gnd_ids)

    payload = build_payload(entries, date.today().isoformat())
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    _print_summary(_summarize(entries), out_path)


if __name__ == "__main__":
    main()
