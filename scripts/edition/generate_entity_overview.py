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

Ambiguity is reported apart from that accounting. A candidate names the reported bearer
in `gid` and every other possible bearer of the same surface in `alternatives`; the
counts above follow the reported bearer alone. A listed entity that only ever appears in
an alternatives set would otherwise read as "not found", so every entity carries
`alternative_only`, the number of mentions naming it as a possible bearer without
reporting it. The auto and review counts stay untouched by it and remain comparable to
earlier runs.

Quality is the adjudicated evidence of data/entities/mention_verdicts.json, mirrored
into the page so the static site carries its own measurement (method:
knowledge/entity-evaluation.md). Precision is the protocol reading, correct over the
decidable verdicts, with the seeded percentile interval of the executed evaluation.
Recall has no single defined rate there, so the status counts travel raw next to the
coverage share the executed evaluation reports.

Output docs/data/entity_overview.json is deterministic (no timestamp, fixed ordering,
seeded bootstrap), so the git diff of the mirror shows the exact effect of a rule change.

Usage:
    python -m scripts.edition.generate_entity_overview
"""

from __future__ import annotations

import hashlib
import json
import random
import sys
from collections import Counter, defaultdict

from scripts.config import DATA_DIR, DOCS_DIR, OUTPUT_DIR
from scripts.tei.entity_matcher import base_rule

SCAN_PATH = OUTPUT_DIR / "audits" / "entity_corpus_scan.json"
ENTITIES_PATH = DATA_DIR / "entities" / "all_entities.json"
VERDICTS_PATH = DATA_DIR / "entities" / "mention_verdicts.json"
OUT_PATH = DOCS_DIR / "data" / "entity_overview.json"

# Repo-relative provenance labels; the scan's own generated_from carries absolute
# machine paths, which must not reach the versioned mirror.
SCAN_LABEL = "output/audits/entity_corpus_scan.json"
ENTITIES_LABEL = "data/entities/all_entities.json"
VERDICTS_LABEL = "data/entities/mention_verdicts.json"

CORRECT_VERDICT = "correct"
DECIDABLE_VERDICTS = frozenset({"correct", "wrong_entity", "wrong_span",
                                "not_in_source"})
# Interval procedure of the executed evaluation: percentile bootstrap, seed 42,
# 10000 resamples (reports/2026-08-12_entity-eval-ergebnis.md). Reproducing its
# published bounds requires this resampler, so the block keeps its own.
BOOTSTRAP_SEED = 42
BOOTSTRAP_N = 10000

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


def build_overview(candidates: list[dict], entries: dict[str, dict], *,
                   quality: dict | None = None,
                   provenance: dict | None = None) -> dict:
    """Aggregate scan candidates per entity (primary) and per document (secondary)."""
    seen = {c["gid"] for c in candidates}
    seen.update(alt for c in candidates for alt in c.get("alternatives") or ())
    unknown = sorted(seen - set(entries))
    if unknown:
        raise ValueError(f"gids outside the curated list: {', '.join(unknown)}")

    docs: dict[str, dict] = defaultdict(lambda: {
        "auto": 0, "review": 0,
        "classes": defaultdict(int),
        "entities": defaultdict(lambda: {"auto": 0, "review": 0,
                                         "classes": defaultdict(int)}),
    })
    per_entity: dict[str, dict] = {
        gid: {"auto": 0, "review": 0, "alternative_only": 0,
              "classes": defaultdict(int), "docs": defaultdict(lambda: [0, 0])}
        for gid in entries
    }
    ambiguous_mentions = 0

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
            entity["classes"][cls] += 1
        alternatives = cand.get("alternatives") or ()
        if alternatives:
            ambiguous_mentions += 1
        for alt in alternatives:
            if alt != cand["gid"]:
                per_entity[alt]["alternative_only"] += 1

    entity_records = {}
    for gid in sorted(entries, key=lambda g: (_label_order(entries[g]["label"]), g)):
        entity = per_entity[gid]
        entity_records[gid] = {
            "label": entries[gid]["label"],
            "category": entries[gid]["category"],
            "auto": entity["auto"],
            "review": entity["review"],
            "alternative_only": entity["alternative_only"],
            "classes": _plain(entity["classes"]),
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

    auto = sum(d["auto"] for d in documents.values())
    review = sum(d["review"] for d in documents.values())
    totals = {
        "documents": len(documents),
        "listed_entities": len(entries),
        "entities_found": sum(1 for e in entity_records.values()
                              if e["auto"] + e["review"] > 0),
        "entities_alternative_only": sum(
            1 for e in entity_records.values()
            if e["auto"] + e["review"] == 0 and e["alternative_only"] > 0),
        "mentions": auto + review,
        "auto": auto,
        "review": review,
        "ambiguous_mentions": ambiguous_mentions,
    }
    return {
        "classes": [{"key": key, "label": label, "description": description}
                    for key, label, description in CLASSES],
        "provenance": provenance or {},
        "totals": totals,
        "quality": quality or {},
        "entities": entity_records,
        "documents": documents,
    }


# ---------------------------------------------------------------------------
# Adjudicated evidence and provenance
# ---------------------------------------------------------------------------


def quality_block(verdicts: dict) -> dict:
    """Mirror of the facsimile-adjudicated sample (knowledge/entity-evaluation.md).

    Precision follows the protocol reading, correct over the decidable verdicts, with
    `undecidable` outside numerator and denominator. Recall carries no defined single
    rate, so the three adjudicated statuses travel as counts beside the coverage share
    (hit or on the worklist) the executed evaluation reports.
    """
    marks = verdicts.get("marks") or []
    recall = verdicts.get("recall_mentions") or []
    decidable = [m for m in marks if m.get("verdict") in DECIDABLE_VERDICTS]
    correct = sum(1 for m in decidable if m["verdict"] == CORRECT_VERDICT)
    judged = [m for m in marks if m.get("iaa")]
    disagreements = [m for m in judged if not m.get("iaa_agrees")]
    status = Counter(m.get("status") for m in recall)
    covered = status["hit"] + status["on_worklist"]
    return {
        "source": VERDICTS_LABEL,
        "method": "knowledge/entity-evaluation.md",
        "snapshot": verdicts.get("snapshot") or "",
        "precision": {
            "n": len(marks),
            "distribution": _plain(Counter(m.get("verdict") for m in marks)),
            "decidable": len(decidable),
            "correct": correct,
            "rate": round(correct / len(decidable), 4) if decidable else None,
            "ci95": _percentile_ci([1 if m["verdict"] == CORRECT_VERDICT else 0
                                    for m in decidable]) if decidable else None,
            "ci_method": f"percentile bootstrap, seed {BOOTSTRAP_SEED}, "
                         f"{BOOTSTRAP_N} resamples",
        },
        "recall": {
            "mentions": len(recall),
            "pages_with_mentions": len({(m.get("doc"), m.get("page")) for m in recall}),
            "status": _plain(status),
            "causes_missed": _plain(Counter(m["cause"] for m in recall
                                            if m.get("cause"))),
            "coverage_hit_or_worklist": (round(covered / len(recall), 4)
                                         if recall else None),
        },
        "agreement": {
            "n": len(judged),
            "agree": len(judged) - len(disagreements),
            "rate": round((len(judged) - len(disagreements)) / len(judged), 4)
                    if judged else None,
            "disagreements": sorted(
                ({"case": m.get("source", {}).get("case_id") or "",
                  "doc": str(m.get("doc") or ""),
                  "page": m.get("page"),
                  "surface": m.get("surface") or "",
                  "verdict": m.get("verdict") or "",
                  "second_verdict": m["iaa"].get("verdict") or ""}
                 for m in disagreements),
                key=lambda d: (d["case"], d["doc"], d["surface"])),
        },
    }


def provenance_block(scan_sha256: str, scan_candidates: int,
                     listed_entities: int) -> dict:
    """The snapshot the overview was cut from, as repo-relative labels."""
    return {
        "scan": SCAN_LABEL,
        "scan_sha256": scan_sha256,
        "scan_candidates": scan_candidates,
        "entity_list": ENTITIES_LABEL,
        "listed_entities": listed_entities,
    }


def _percentile_ci(outcomes: list[int]) -> list[float]:
    """Seeded percentile bootstrap of the mean, deterministic across runs."""
    rng = random.Random(BOOTSTRAP_SEED)
    n = len(outcomes)
    means = sorted(sum(rng.choices(outcomes, k=n)) / n for _ in range(BOOTSTRAP_N))
    return [round(means[int(0.025 * BOOTSTRAP_N)], 4),
            round(means[min(int(0.975 * BOOTSTRAP_N), BOOTSTRAP_N - 1)], 4)]


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
    scan_bytes = SCAN_PATH.read_bytes()
    scan = json.loads(scan_bytes.decode("utf-8"))
    entities = json.loads(ENTITIES_PATH.read_text(encoding="utf-8"))
    entries = list_entries(entities)
    candidates = scan.get("candidates", [])

    quality = quality_block(json.loads(VERDICTS_PATH.read_text(encoding="utf-8")))
    provenance = provenance_block(hashlib.sha256(scan_bytes).hexdigest(),
                                  len(candidates), len(entries))
    overview = build_overview(candidates, entries, quality=quality,
                              provenance=provenance)
    OUT_PATH.write_text(serialize(overview), encoding="utf-8")

    totals = overview["totals"]
    print(f"Entity overview: {totals['entities_found']} of "
          f"{totals['listed_entities']} listed entities found in "
          f"{totals['documents']} document(s); {totals['mentions']} mentions, "
          f"{totals['auto']} auto-marked, {totals['review']} on review.")
    print(f"  Ambiguity: {totals['ambiguous_mentions']} mentions name another "
          f"possible bearer; {totals['entities_alternative_only']} listed entities "
          f"appear only as such an alternative.")
    precision = quality["precision"]
    print(f"  Adjudicated sample ({quality['snapshot']}): {precision['correct']} of "
          f"{precision['decidable']} decidable marks correct, "
          f"{quality['recall']['mentions']} recall mentions.")
    print(f"  JSON: {OUT_PATH}")


if __name__ == "__main__":
    main()
