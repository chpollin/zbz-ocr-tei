"""Intake audit for the curated entity list (entity integration, M1).

Checks data/entities/all_entities.json on its own terms and, when the GND cache
built by scripts.tei.fetch_gnd_variants exists, against that cache. When the legacy
mention index exists as well, every surface form it pairs with an id is checked
against that id's own GND record. Reports the defects so the matcher can exclude the
affected entries; repairing the list is the job of the tool that produced it.

DIAGNOSIS ONLY -- reads the entity list and the cache, writes a JSON report to
output/audits/, changes no data and is no pass/fail gate (exit code always 0).

Errors (block an entry or one of its forms from automatic matching):
  missing_label        persons.name / organisations.orgName / works.title absent or empty
  invalid_gnd_id       GND_id absent or outside both real GND id forms
  duplicate_gnd_id     the same GND id twice, inside or across the categories
  dnb_link_mismatch    listBibl DNB_link does not match https://d-nb.info/gnd/{GND_id}
  unresolved_author    works.author_gnd_id points to no persons entry
  invalid_variants     the optional variants field is no list of non-empty strings
  duplicate_variant    the same curated variant twice inside one entry
  redundant_variant    a curated variant repeats the entry's own label
  gnd_not_found        the cache holds HTTP 404 for the id (defective id)
  cache_status         the cache holds another non-200 status (retrieval incomplete)

Warnings (reported, never blocking):
  not_in_cache             id missing from the cache, so the remote checks did not run
  preferred_name_mismatch  lobid preferredName differs from the local label
  type_mismatch            the cache types do not carry the category type
  legacy_pairing           a legacy surface form the id's own GND record does not
                           corroborate (gid plus form); the matcher demotes exactly
                           these forms to tier 2
  variant_collision        a curated variant that another entry carries as its label or
                           as its own variant; both entries then own the same form
  editor_reviewed = false is counted only, never listed per entry

The curated variants field is the operator's channel for a corpus spelling the GND norm
form does not carry ("Kolumbus" for "Colombo, Cristoforo"). Its strings are compared
like labels, in NFC with collapsed whitespace and case folded.

Usage:
    python -m scripts.eval.entity_lint
    python -m scripts.eval.entity_lint --entities PATH --cache PATH --legacy PATH --out PATH
"""
import argparse
import json
import re
import unicodedata
from collections import Counter
from pathlib import Path

from scripts.config import DATA_DIR
from scripts.eval.audit_common import AUDIT_OUTPUT_DIR
from scripts.tei.entity_matcher import (
    legacy_form_is_covered,
    legacy_names,
    normalize_gid,
)

ENTITIES_PATH = DATA_DIR / "entities" / "all_entities.json"
CACHE_PATH = DATA_DIR / "entities" / "gnd_cache.json"
LEGACY_PATH = DATA_DIR / "entities" / "legacy_mentions.json"
REPORT_PATH = AUDIT_OUTPUT_DIR / "entity_lint.json"

CATEGORIES = ("persons", "organisations", "works")
LABEL_FIELD = {"persons": "name", "organisations": "orgName", "works": "title"}
EXPECTED_TYPE = {"persons": "Person", "organisations": "CorporateBody", "works": "Work"}
DNB_LINK_PATTERN = "https://d-nb.info/gnd/{id}"

# Both real GND id forms: a digit run with an optional X check character
# (104535342, 11860564X) and the older hyphen form (4558181-2, 5005966-X).
_GND_ID_RE = re.compile(r"^[0-9]+-?[0-9X]$")
_WHITESPACE_RE = re.compile(r"\s+")


def is_valid_gnd_id(value) -> bool:
    """True for both GND id forms. Surrounding whitespace counts as a defect."""
    return isinstance(value, str) and bool(_GND_ID_RE.match(value))


def _label(entry: dict, category: str):
    """The category label of an entry, or None when absent, empty or not a string."""
    value = entry.get(LABEL_FIELD[category])
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def _normalized(text: str) -> str:
    """Comparison form for labels: NFC, collapsed whitespace, case-folded."""
    return _WHITESPACE_RE.sub(" ", unicodedata.normalize("NFC", text)).strip().casefold()


def _finding(kind: str, category: str, index: int, gnd_id, message: str, **extra) -> dict:
    finding = {
        "type": kind,
        "category": category,
        "index": index,
        "gnd_id": gnd_id if isinstance(gnd_id, str) else None,
        "message": message,
    }
    finding.update(extra)
    return finding


def _dnb_findings(entry: dict, category: str, index: int, gnd_id) -> list:
    """Compare every present DNB_link with the pattern. An absent listBibl is no defect."""
    bibls = entry.get("listBibl")
    if not isinstance(bibls, list) or not isinstance(gnd_id, str):
        return []
    expected = DNB_LINK_PATTERN.format(id=gnd_id)
    findings = []
    for bibl in bibls:
        link = bibl.get("DNB_link") if isinstance(bibl, dict) else None
        if isinstance(link, str) and link.strip() and link.strip() != expected:
            findings.append(
                _finding(
                    "dnb_link_mismatch", category, index, gnd_id,
                    f"DNB_link {link} weicht von {expected} ab",
                    dnb_link=link, expected=expected,
                )
            )
    return findings


def _cache_findings(record, category: str, index: int, gnd_id, label) -> tuple:
    """Remote checks for one entry. Returns (errors, warnings)."""
    if record is None:
        return [], [_finding("not_in_cache", category, index, gnd_id, "GND-ID fehlt im Cache")]

    status = record.get("http_status")
    if status == 404:
        return [_finding("gnd_not_found", category, index, gnd_id, "lobid meldet HTTP 404")], []
    if status != 200:
        return [
            _finding("cache_status", category, index, gnd_id, f"Cache-Status {status}", status=status)
        ], []

    warnings = []
    preferred = record.get("preferred_name")
    if (label and isinstance(preferred, str) and preferred.strip()
            and _normalized(preferred) != _normalized(label)):
        warnings.append(
            _finding(
                "preferred_name_mismatch", category, index, gnd_id,
                "lokales Label weicht vom GND-Vorzugsnamen ab",
                local_label=label, preferred_name=preferred,
            )
        )
    types = record.get("types") or []
    if types and EXPECTED_TYPE[category] not in types:
        warnings.append(
            _finding(
                "type_mismatch", category, index, gnd_id,
                f"Cache-Typen tragen {EXPECTED_TYPE[category]} nicht",
                types=types, expected=EXPECTED_TYPE[category],
            )
        )
    return [], warnings


def _cache_counts(cache: dict, listed_ids: set) -> dict:
    entries = cache.get("entries") or {}
    statuses = Counter(record.get("http_status") for record in entries.values())
    return {
        "retrieved": cache.get("retrieved"),
        "entries": len(entries),
        "status_200": statuses.get(200, 0),
        "status_404": statuses.get(404, 0),
        "status_other": sum(c for s, c in statuses.items() if s not in (200, 404)),
        "listed_not_in_cache": sum(1 for gid in listed_ids if gid not in entries),
    }


def _variant_strings(entry: dict) -> list:
    """The usable curated variants of an entry; malformed items are left to the checks."""
    values = entry.get("variants")
    if not isinstance(values, list):
        return []
    return [value for value in values if isinstance(value, str) and value.strip()]


def _form_owners(entities: dict) -> dict:
    """Normalized label and curated variant strings -> the entries that carry them."""
    owners = {}
    for category in CATEGORIES:
        for index, entry in enumerate(entities.get(category) or []):
            forms = [_label(entry, category), *_variant_strings(entry)]
            for form in forms:
                if form:
                    owners.setdefault(_normalized(form), []).append(
                        (category, index, entry.get("GND_id"))
                    )
    return owners


def _variant_findings(entry: dict, category: str, index: int, gnd_id, label,
                      owners: dict) -> tuple:
    """Checks for the curated variants field of one entry. Returns (errors, warnings).

    An absent field is the normal case and yields nothing. A variant another entry
    carries as its label or its own variant is a warning: both entries then own the
    same form, which the matcher reports as a multi-owner candidate.
    """
    values = entry.get("variants")
    if values is None:
        return [], []
    if not isinstance(values, list):
        return [_finding("invalid_variants", category, index, gnd_id,
                         "Feld variants ist keine Liste")], []

    errors, warnings, seen = [], [], set()
    for value in values:
        if not isinstance(value, str) or not value.strip():
            errors.append(
                _finding("invalid_variants", category, index, gnd_id,
                         "Variante ist kein nicht-leerer String",
                         variant=value if isinstance(value, str) else None)
            )
            continue
        key = _normalized(value)
        if key in seen:
            errors.append(
                _finding("duplicate_variant", category, index, gnd_id,
                         "Variante steht mehrfach im selben Eintrag", variant=value)
            )
            continue
        seen.add(key)
        if label and key == _normalized(label):
            errors.append(
                _finding("redundant_variant", category, index, gnd_id,
                         "Variante wiederholt das Label des Eintrags", variant=value)
            )
        foreign = [
            other_id for other_category, other_index, other_id in owners.get(key, ())
            if (other_category, other_index) != (category, index)
            and isinstance(other_id, str)
        ]
        if foreign:
            warnings.append(
                _finding("variant_collision", category, index, gnd_id,
                         "Variante ist zugleich Form eines anderen Eintrags",
                         variant=value, collides_with=foreign)
            )
    return errors, warnings


def _legacy_findings(forms, category: str, index: int, gnd_id, label, record) -> tuple:
    """Pairing check for one entry: (checked pairs, warnings).

    Corroboration is `legacy_form_is_covered`, the same predicate the matcher uses to
    decide which legacy forms stay tier-2 only, so lint and lexicon cannot drift.
    """
    pairs, findings = 0, []
    for raw_form in forms:
        form = _WHITESPACE_RE.sub(" ", str(raw_form)).strip()
        if not form:
            continue
        pairs += 1
        if not legacy_form_is_covered(form, label or "", record):
            findings.append(
                _finding(
                    "legacy_pairing", category, index, gnd_id,
                    "Legacy-Form ist durch den GND-Eintrag des Traegers nicht gedeckt",
                    form=form,
                )
            )
    return pairs, findings


def lint(entities: dict, cache: dict | None = None, legacy: dict | None = None) -> dict:
    """Audit the entity list, optionally against the GND cache and the legacy index.

    Pure: takes and returns plain data, touches no files. Without a cache only the
    offline checks run and counts["cache"] stays None; without the legacy index the
    pairing check does not run and counts["legacy"] stays None.
    """
    errors, warnings = [], []
    cache_entries = None if cache is None else (cache.get("entries") or {})
    legacy_index = legacy_names(legacy) if legacy is not None else {}
    form_owners = _form_owners(entities)
    legacy_pairs = 0
    variant_entries, variant_strings = 0, 0
    person_ids = {
        entry.get("GND_id")
        for entry in entities.get("persons") or []
        if isinstance(entry.get("GND_id"), str)
    }
    first_seen, listed_ids = {}, set()
    reviewed_false = 0

    for category in CATEGORIES:
        for index, entry in enumerate(entities.get(category) or []):
            gnd_id = entry.get("GND_id")
            label = _label(entry, category)
            if not entry.get("editor_reviewed"):
                reviewed_false += 1

            if label is None:
                errors.append(
                    _finding("missing_label", category, index, gnd_id,
                             f"Feld {LABEL_FIELD[category]} fehlt oder ist leer")
                )
            if not is_valid_gnd_id(gnd_id):
                errors.append(
                    _finding("invalid_gnd_id", category, index, gnd_id,
                             f"GND_id {gnd_id!r} entspricht keiner GND-Form")
                )
            if isinstance(gnd_id, str) and gnd_id:
                listed_ids.add(gnd_id)
                if gnd_id in first_seen:
                    prior_category, prior_index = first_seen[gnd_id]
                    errors.append(
                        _finding("duplicate_gnd_id", category, index, gnd_id,
                                 f"GND-ID bereits in {prior_category}[{prior_index}]",
                                 first_category=prior_category, first_index=prior_index)
                    )
                else:
                    first_seen[gnd_id] = (category, index)

            errors.extend(_dnb_findings(entry, category, index, gnd_id))

            variant_errors, variant_warnings = _variant_findings(
                entry, category, index, gnd_id, label, form_owners
            )
            errors.extend(variant_errors)
            warnings.extend(variant_warnings)
            usable_variants = _variant_strings(entry)
            variant_entries += bool(usable_variants)
            variant_strings += len(usable_variants)

            if category == "works":
                author = entry.get("author_gnd_id")
                if isinstance(author, str) and author.strip() and author.strip() not in person_ids:
                    errors.append(
                        _finding("unresolved_author", category, index, gnd_id,
                                 f"author_gnd_id {author} hat keinen persons-Eintrag",
                                 author_gnd_id=author)
                    )

            record = None
            if cache_entries is not None and isinstance(gnd_id, str) and gnd_id:
                record = cache_entries.get(gnd_id)
                cache_errors, cache_warnings = _cache_findings(
                    record, category, index, gnd_id, label
                )
                errors.extend(cache_errors)
                warnings.extend(cache_warnings)

            if legacy is not None and isinstance(gnd_id, str) and gnd_id:
                pairs, findings = _legacy_findings(
                    legacy_index.get(normalize_gid(gnd_id), ()),
                    category, index, gnd_id, label, record,
                )
                legacy_pairs += pairs
                warnings.extend(findings)

    sizes = {category: len(entities.get(category) or []) for category in CATEGORIES}
    counts = {
        "entities": {**sizes, "total": sum(sizes.values())},
        "errors": len(errors),
        "warnings": len(warnings),
        "errors_by_type": dict(Counter(item["type"] for item in errors)),
        "warnings_by_type": dict(Counter(item["type"] for item in warnings)),
        "editor_reviewed_false": reviewed_false,
        "variants": {"entries": variant_entries, "strings": variant_strings},
        "cache": _cache_counts(cache, listed_ids) if cache is not None else None,
        "legacy": None if legacy is None else {
            "index_ids": len(legacy_index),
            "checked_pairs": legacy_pairs,
            "uncorroborated": sum(1 for w in warnings if w["type"] == "legacy_pairing"),
        },
    }
    return {"errors": errors, "warnings": warnings, "counts": counts}


def build_report(entities: dict, cache, entities_path, cache_path,
                 legacy=None, legacy_path=None) -> dict:
    """Full JSON payload: the lint result plus its provenance."""
    result = lint(entities, cache, legacy)
    return {
        "audit": "entity_lint",
        "entities_file": str(entities_path),
        "cache_file": str(cache_path) if cache_path else None,
        "legacy_file": str(legacy_path) if legacy_path else None,
        "cache_retrieved": cache.get("retrieved") if cache else None,
        "errors": result["errors"],
        "warnings": result["warnings"],
        "counts": result["counts"],
    }


def _ascii(text: str) -> str:
    """Fold to ASCII for the Windows console (the JSON report keeps full Unicode)."""
    return str(text).encode("ascii", "replace").decode("ascii")


def _print_summary(report: dict) -> None:
    counts = report["counts"]
    entities = counts["entities"]
    print("Entitaeten-Lint (Diagnose, aendert keine Daten)\n")
    print(f"  Eintraege: {entities['total']} "
          f"(persons {entities['persons']}, organisations {entities['organisations']}, "
          f"works {entities['works']})")
    print(f"  editor_reviewed = false: {counts['editor_reviewed_false']}")
    variants = counts["variants"]
    print(f"  Kuratierte Varianten: {variants['strings']} Strings "
          f"in {variants['entries']} Eintraegen")
    if counts["cache"] is None:
        print("  Cache: nicht vorhanden (nur Offline-Pruefungen)")
    else:
        cache = counts["cache"]
        print(f"  Cache vom {cache['retrieved']}: {cache['entries']} Eintraege "
              f"(200: {cache['status_200']}, 404: {cache['status_404']}, "
              f"sonstige: {cache['status_other']})")
    if counts["legacy"] is None:
        print("  Legacy-Index: nicht vorhanden (keine Paarungspruefung)")
    else:
        legacy = counts["legacy"]
        print(f"  Legacy-Index: {legacy['index_ids']} IDs, "
              f"{legacy['checked_pairs']} Paarungen geprueft, "
              f"{legacy['uncorroborated']} ungedeckt")

    print(f"\n  Fehler: {counts['errors']}")
    for kind, number in sorted(counts["errors_by_type"].items()):
        print(f"    {kind:20} {number}")
    for error in report["errors"]:
        print(f"    - [{error['category']}] {error['gnd_id']}: "
              f"{error['type']} -- {_ascii(error['message'])}")

    print(f"\n  Warnungen: {counts['warnings']}")
    for kind, number in sorted(counts["warnings_by_type"].items()):
        print(f"    {kind:24} {number}")


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser(description="Entitaeten-Lint: prueft Liste und GND-Cache")
    parser.add_argument("--entities", default=str(ENTITIES_PATH), help="Entitaetendatei (JSON)")
    parser.add_argument("--cache", default=str(CACHE_PATH), help="GND-Cache (JSON, optional)")
    parser.add_argument("--legacy", default=str(LEGACY_PATH),
                        help="Legacy-Erwaehnungsindex (JSON, optional)")
    parser.add_argument("--out", default=str(REPORT_PATH), help="Zieldatei fuer den Report")
    args = parser.parse_args()

    entities_path, cache_path, out_path = Path(args.entities), Path(args.cache), Path(args.out)
    legacy_path = Path(args.legacy)
    if not entities_path.exists():
        print(f"FEHLER: Entitaetendatei nicht gefunden: {entities_path}")
        return

    entities = _load(entities_path)
    cache = _load(cache_path) if cache_path.exists() else None
    legacy = _load(legacy_path) if legacy_path.exists() else None
    report = build_report(entities, cache, entities_path, cache_path if cache else None,
                          legacy, legacy_path if legacy else None)
    _print_summary(report)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n  JSON-Report: {out_path}")


if __name__ == "__main__":
    main()
