"""Entity overview mirror: per-document entity counts and certainty classes.

Feeds docs/entities.html, the corpus-wide answer to "which entities are annotated in
this object, how many, and how certain is the annotation". Source of the candidate
population is the corpus scan snapshot (output/audits/entity_corpus_scan.json), the
same stream the previews are cut from; the facsimile-adjudicated judgments of
data/entities/mention_verdicts.json join per document as the hand-checked layer.

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

SCAN_PATH = Path("output/audits/entity_corpus_scan.json")
ENTITIES_PATH = DATA_DIR / "entities" / "all_entities.json"
VERDICTS_PATH = DATA_DIR / "entities" / "mention_verdicts.json"
OUT_PATH = DOCS_DIR / "data" / "entity_overview.json"

# Review classes in display order. The key is stable API for the frontend; label and
# description are shown verbatim in the UI legend.
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
    base = rule.split(":", 1)[0]
    if ":running-head" in rule:
        return "running_head"
    if ":suspect" in rule:
        return "suspect"
    if ":ambiguous" in rule or base == "ambiguous-surname":
        return "ambiguous"
    if ":in-plain-bibl" in rule:
        return "bibliography"
    if any(marker in rule for marker in _DERIVED_MARKERS) or base in _DERIVED_BASES:
        return "derived"
    if base in ("bare-surname", "caps-surname"):
        return "unanchored"
    if base == "crosses-markup":
        return "markup"
    if base == "short-title":
        return "short_title"
    return "other"


def build_overview(candidates: list[dict], marks: list[dict],
                   allowed_gids: set[str]) -> dict:
    """Aggregate scan candidates and adjudicated marks into the overview structure."""
    docs: dict[str, dict] = defaultdict(lambda: {
        "auto": 0, "review": 0,
        "classes": defaultdict(int),
        "entities": defaultdict(lambda: {"auto": 0, "review": 0,
                                         "classes": defaultdict(int)}),
    })
    unknown = sorted({c["gid"] for c in candidates} - allowed_gids)
    if unknown:
        raise ValueError(f"gids outside the curated list: {', '.join(unknown)}")

    for cand in candidates:
        doc = docs[str(cand["doc"])]
        entity = doc["entities"][cand["gid"]]
        cls = classify(cand["rule"], cand["tier"])
        if cls == "auto":
            doc["auto"] += 1
            entity["auto"] += 1
        else:
            doc["review"] += 1
            entity["review"] += 1
            doc["classes"][cls] += 1
            entity["classes"][cls] += 1

    checked: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for mark in marks:
        verdicts = checked[str(mark["doc"])]
        verdicts["total"] += 1
        verdicts[str(mark["verdict"])] += 1
    for doc_id in checked:
        docs.setdefault(doc_id, {"auto": 0, "review": 0, "classes": defaultdict(int),
                                 "entities": defaultdict(dict)})

    documents = {}
    for doc_id in sorted(docs, key=_doc_order):
        doc = docs[doc_id]
        entities = [
            {"gid": gid,
             "auto": entity["auto"],
             "review": entity["review"],
             "classes": _plain(entity["classes"])}
            for gid, entity in doc["entities"].items() if entity
        ]
        entities.sort(key=lambda e: (-(e["auto"] + e["review"]), e["gid"]))
        record = {"auto": doc["auto"], "review": doc["review"],
                  "classes": _plain(doc["classes"]), "entities": entities}
        if doc_id in checked:
            record["checked"] = _plain(checked[doc_id])
        documents[doc_id] = record

    totals = {
        "documents": len(documents),
        "auto": sum(d["auto"] for d in documents.values()),
        "review": sum(d["review"] for d in documents.values()),
        "checked": _plain(_merge(checked.values())),
    }
    return {
        "classes": [{"key": key, "label": label, "description": description}
                    for key, label, description in CLASSES],
        "totals": totals,
        "documents": documents,
    }


def _doc_order(doc_id: str):
    return (0, int(doc_id)) if doc_id.isdigit() else (1, doc_id)


def _plain(counter) -> dict:
    return {key: counter[key] for key in sorted(counter)}


def _merge(counters) -> dict[str, int]:
    merged: dict[str, int] = defaultdict(int)
    for counter in counters:
        for key, value in counter.items():
            merged[key] += value
    return merged


def serialize(overview: dict) -> str:
    return json.dumps(overview, ensure_ascii=False, indent=1) + "\n"


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    scan = json.loads(SCAN_PATH.read_text(encoding="utf-8"))
    entities = json.loads(ENTITIES_PATH.read_text(encoding="utf-8"))
    allowed = {
        str(entry.get("GND_id") or "").strip()
        for group in ("persons", "organisations", "works")
        for entry in entities.get(group, []) or []
    } - {""}
    verdicts = (json.loads(VERDICTS_PATH.read_text(encoding="utf-8"))
                if VERDICTS_PATH.exists() else {})

    overview = build_overview(scan.get("candidates", []),
                              verdicts.get("marks", []), allowed)
    OUT_PATH.write_text(serialize(overview), encoding="utf-8")

    totals = overview["totals"]
    print(f"Entity overview over {totals['documents']} document(s): "
          f"{totals['auto']} auto-marked, {totals['review']} on review, "
          f"{totals['checked'].get('total', 0)} hand-checked marks.")
    print(f"  JSON: {OUT_PATH}")


if __name__ == "__main__":
    main()
