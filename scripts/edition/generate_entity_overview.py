"""Entity overview mirror: completeness and certainty of the annotation layer.

Feeds docs/entities.html, a developer instrument for the question "do we really have
every listed entity". The primary aggregation is per entity: every entry of the curated
list appears, including entries without a single corpus mention (the completeness
signal), with its auto/review counts and the documents it occurs in. The per-document
aggregation stays as the secondary view. Source of the candidate population is the
corpus scan snapshot (output/audits/entity_corpus_scan.json), the same stream the
previews are cut from.

Certainty model, aligned with the tier architecture of the matcher
(knowledge/entity-integration.md): tier 1 counts as "auto" (auto-marked, the layer the
measured precision covers), tier 2 as "review" (held on the worklist), broken down into
the classes of CLASSES. Classification is by rule string only, so the overview follows
every matcher change through a plain regeneration.

Output docs/data/entity_overview.json is deterministic (no timestamp, fixed ordering),
so the git diff of the mirror shows the exact effect of a rule change.

Usage:
    python -m scripts.edition.generate_entity_overview
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

from scripts.config import DATA_DIR, DOCS_DIR
from scripts.tei.entity_matcher import base_rule

SCAN_PATH = Path("output/audits/entity_corpus_scan.json")
ENTITIES_PATH = DATA_DIR / "entities" / "all_entities.json"
OUT_PATH = DOCS_DIR / "data" / "entity_overview.json"

_CATEGORY_BY_LIST = {"persons": "person", "organisations": "organisation",
                     "works": "work"}
_LABEL_FIELD = {"persons": "name", "organisations": "orgName", "works": "title"}

# Review classes in display order. The key is stable API for the frontend; the label
# is the chip text, the description its on-demand tooltip.
CLASSES = (
    ("ambiguous", "Ambiguous",
     "several listed entities share the form; the reported id is undecided"),
    ("suspect", "Suspicion signal",
     "a deterministic warning fired: homograph, compound, citation frame or container"),
    ("unanchored", "Unanchored surname",
     "a bare surname without a full-name anchor in the document"),
    ("running_head", "Running head",
     "repeated page furniture; outside the marking scope by convention (E105)"),
    ("bibliography", "Citation context",
     "inside a plain bibl element; identity needs the citation read"),
    ("figure", "Figure caption",
     "inside a figure zone; scanned but never asserted (plate provenance, credits)"),
    ("derived", "Derived spelling",
     "a spelling derived from a listed form (initials, acronym case, subtitle join, legacy)"),
    ("markup", "Markup boundary",
     "the match crosses markup and is reported truncated"),
    ("short_title", "Short work title",
     "a one-word title; typography has to corroborate the reading"),
    ("other", "Other review",
     "remaining worklist candidates"),
)

_DERIVED_MARKERS = (":acronym-case", ":qualifier-strip", ":place-adjective",
                    ":initials", ":subtitle-join")
_DERIVED_BASES = frozenset({"legacy-form", "adjective-form"})


def classify(rule: str, tier: int) -> str:
    """Certainty class of one candidate; priority mirrors the suffix semantics.

    The running-head demotion is a position property appended last and outranks every
    other reading; a suspicion signal outranks ambiguity because it questions the
    mention itself, not only its bearer.
    """
    if tier == 1:
        return "auto"
    base = base_rule(rule)
    if ":running-head" in rule:
        return "running_head"
    if ":suspect" in rule:
        return "suspect"
    if ":ambiguous" in rule or base == "ambiguous-surname":
        return "ambiguous"
    if ":in-plain-bibl" in rule:
        return "bibliography"
    if ":in-figure" in rule:
        return "figure"
    if any(marker in rule for marker in _DERIVED_MARKERS) or base in _DERIVED_BASES:
        return "derived"
    if base in ("bare-surname", "caps-surname"):
        return "unanchored"
    if base == "crosses-markup":
        return "markup"
    if base == "short-title":
        return "short_title"
    return "other"


def list_entries(entities: dict) -> dict[str, dict]:
    """gid -> {label, category} for every curated list entry with id and label."""
    entries: dict[str, dict] = {}
    for list_key, category in _CATEGORY_BY_LIST.items():
        for raw in entities.get(list_key, []) or []:
            gid = str(raw.get("GND_id") or "").strip()
            label = " ".join(str(raw.get(_LABEL_FIELD[list_key]) or "").split())
            if gid and label and gid not in entries:
                entries[gid] = {"label": label, "category": category}
    return entries


def build_overview(candidates: list[dict], entries: dict[str, dict]) -> dict:
    """Aggregate scan candidates per entity (primary) and per document (secondary)."""
    unknown = sorted({c["gid"] for c in candidates} - set(entries))
    if unknown:
        raise ValueError(f"gids outside the curated list: {', '.join(unknown)}")

    docs: dict[str, dict] = defaultdict(lambda: {
        "auto": 0, "review": 0,
        "classes": defaultdict(int),
        "entities": defaultdict(lambda: {"auto": 0, "review": 0,
                                         "classes": defaultdict(int)}),
    })
    per_entity: dict[str, dict] = {
        gid: {"auto": 0, "review": 0, "docs": defaultdict(lambda: [0, 0])}
        for gid in entries
    }

    for cand in candidates:
        doc_id = str(cand["doc"])
        doc = docs[doc_id]
        doc_entity = doc["entities"][cand["gid"]]
        entity = per_entity[cand["gid"]]
        cls = classify(cand["rule"], cand["tier"])
        slot = 0 if cls == "auto" else 1
        entity["docs"][doc_id][slot] += 1
        if cls == "auto":
            doc["auto"] += 1
            doc_entity["auto"] += 1
            entity["auto"] += 1
        else:
            doc["review"] += 1
            doc_entity["review"] += 1
            entity["review"] += 1
            doc["classes"][cls] += 1
            doc_entity["classes"][cls] += 1

    entity_records = {}
    for gid in sorted(entries, key=lambda g: (_label_order(entries[g]["label"]), g)):
        entity = per_entity[gid]
        entity_records[gid] = {
            "label": entries[gid]["label"],
            "category": entries[gid]["category"],
            "auto": entity["auto"],
            "review": entity["review"],
            "docs": {doc_id: entity["docs"][doc_id]
                     for doc_id in sorted(entity["docs"], key=_doc_order)},
        }

    documents = {}
    for doc_id in sorted(docs, key=_doc_order):
        doc = docs[doc_id]
        doc_entities = [
            {"gid": gid,
             "auto": e["auto"],
             "review": e["review"],
             "classes": _plain(e["classes"])}
            for gid, e in doc["entities"].items()
        ]
        doc_entities.sort(key=lambda e: (-(e["auto"] + e["review"]), e["gid"]))
        documents[doc_id] = {"auto": doc["auto"], "review": doc["review"],
                             "classes": _plain(doc["classes"]),
                             "entities": doc_entities}

    totals = {
        "documents": len(documents),
        "listed_entities": len(entries),
        "entities_found": sum(1 for e in entity_records.values()
                              if e["auto"] + e["review"] > 0),
        "auto": sum(d["auto"] for d in documents.values()),
        "review": sum(d["review"] for d in documents.values()),
    }
    return {
        "classes": [{"key": key, "label": label, "description": description}
                    for key, label, description in CLASSES],
        "totals": totals,
        "entities": entity_records,
        "documents": documents,
    }


def _doc_order(doc_id: str):
    return (0, int(doc_id)) if doc_id.isdigit() else (1, doc_id)


def _label_order(label: str) -> str:
    return label.casefold()


def _plain(counter) -> dict:
    return {key: counter[key] for key in sorted(counter)}


def serialize(overview: dict) -> str:
    return json.dumps(overview, ensure_ascii=False, indent=1) + "\n"


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    scan = json.loads(SCAN_PATH.read_text(encoding="utf-8"))
    entities = json.loads(ENTITIES_PATH.read_text(encoding="utf-8"))
    entries = list_entries(entities)

    overview = build_overview(scan.get("candidates", []), entries)
    OUT_PATH.write_text(serialize(overview), encoding="utf-8")

    totals = overview["totals"]
    print(f"Entity overview: {totals['entities_found']} of "
          f"{totals['listed_entities']} listed entities found in "
          f"{totals['documents']} document(s); {totals['auto']} auto-marked, "
          f"{totals['review']} on review.")
    print(f"  JSON: {OUT_PATH}")


if __name__ == "__main__":
    main()
