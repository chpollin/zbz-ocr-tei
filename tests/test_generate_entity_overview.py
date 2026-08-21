"""Tests for scripts/entity/generate_entity_overview.py (entity overview mirror).

Synthetic candidate fixtures for the aggregation contract: class assignment per rule
string, the per-entity completeness aggregation including zero-mention list entries and
their alternative-bearer count, per-document counts, deterministic ordering,
closed-world failure on an unknown gid, and byte-identical serialization. The quality
block is pinned synthetically for the formula and then against the committed verdict
store, once per wave that store holds, so the published figures of neither wave can
drift silently.
"""

from __future__ import annotations

import json

import pytest

from scripts.config import DATA_DIR
from scripts.entity.build_mention_verdicts import record_snapshot
from scripts.entity.generate_entity_overview import (
    CLASSES,
    build_overview,
    classify,
    list_entries,
    provenance_block,
    quality_block,
    serialize,
)

VERDICTS_PATH = DATA_DIR / "entities" / "mention_verdicts.json"


def _store() -> dict:
    return json.loads(VERDICTS_PATH.read_text(encoding="utf-8"))


def _wave_slice(store: dict, snapshot: str) -> dict:
    """The store restricted to one wave, shaped the way quality_block reads a store."""
    return {
        "snapshot": snapshot,
        "marks": [m for m in store["marks"] if record_snapshot(m) == snapshot],
        "recall_mentions": [m for m in store["recall_mentions"]
                            if record_snapshot(m) == snapshot],
    }


def _cand(doc, gid, tier, rule, category="person", page=1, alternatives=None):
    return {"doc": doc, "gid": gid, "tier": tier, "rule": rule,
            "category": category, "page": page,
            "alternatives": list(alternatives or [])}


def _mark(verdict, iaa=None, agrees=None, case="p001", wave=None):
    mark = {"doc": "20", "page": 1, "surface": "Jaspers", "gid": "g1",
            "verdict": verdict, "source": {"case_id": case, "wave": wave} if wave
            else {"case_id": case}}
    if iaa is not None:
        mark["iaa"] = {"verdict": iaa}
        mark["iaa_agrees"] = agrees
    return mark


ENTRIES = {
    "g1": {"label": "Jaspers, Karl", "category": "person"},
    "g2": {"label": "UNESCO", "category": "organisation"},
    "g3": {"label": "Nietzsche", "category": "work"},
}


# ---------------------------------------------------------------------------
# Class assignment
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("tier,rule,expected", [
    (1, "full-name", "auto"),
    (1, "org-name", "auto"),
    (2, "caps-full-name:running-head", "running_head"),
    (2, "full-name:in-figure", "figure"),
    (2, "bare-surname:ambiguous:in-figure", "ambiguous"),
    (2, "org-token:suspect", "suspect"),
    (2, "bare-surname:ambiguous", "ambiguous"),
    (2, "ambiguous-surname", "ambiguous"),
    (2, "full-name:in-plain-bibl", "bibliography"),
    (2, "full-name:initials", "derived"),
    (2, "org-name:acronym-case", "derived"),
    (2, "work-title:subtitle-join", "derived"),
    (2, "legacy-form", "derived"),
    (2, "adjective-form", "derived"),
    (2, "bare-surname", "unanchored"),
    (2, "caps-surname", "unanchored"),
    (2, "crosses-markup", "markup"),
    (2, "short-title", "short_title"),
    (2, "speaker:unknown-future-suffix", "other"),
])
def test_classify_assigns_the_documented_class(tier, rule, expected):
    assert classify(rule, tier) == expected


def test_classify_priority_running_head_beats_every_other_suffix():
    assert classify("bare-surname:ambiguous:running-head", 2) == "running_head"
    assert classify("org-token:suspect:running-head", 2) == "running_head"
    assert classify("org-name:in-figure:running-head", 2) == "running_head"


def test_class_catalog_keys_are_unique_and_cover_classify_output():
    keys = [key for key, _, _ in CLASSES]
    assert len(keys) == len(set(keys))
    assert set(keys) >= {"ambiguous", "suspect", "unanchored", "running_head", "figure",
                         "bibliography", "derived", "markup", "short_title", "other"}


# ---------------------------------------------------------------------------
# List intake
# ---------------------------------------------------------------------------


def test_list_entries_read_all_three_categories_and_skip_defects():
    entries = list_entries({
        "persons": [{"GND_id": "p1", "name": "Jaspers, Karl"},
                    {"GND_id": "", "name": "no id"},
                    {"GND_id": "p2", "name": ""}],
        "organisations": [{"GND_id": "o1", "orgName": "UNESCO"}],
        "works": [{"GND_id": "w1", "title": "Nietzsche"}],
    })
    assert set(entries) == {"p1", "o1", "w1"}
    assert entries["o1"] == {"label": "UNESCO", "category": "organisation"}


# ---------------------------------------------------------------------------
# Aggregation
# ---------------------------------------------------------------------------


def test_per_entity_aggregation_includes_zero_mention_entries():
    candidates = [
        _cand("20", "g1", 1, "full-name"),
        _cand("20", "g1", 2, "bare-surname"),
        _cand("30", "g1", 1, "full-name"),
        _cand("30", "g2", 2, "org-token:suspect", category="organisation"),
    ]
    overview = build_overview(candidates, ENTRIES)
    g1 = overview["entities"]["g1"]
    assert g1["label"] == "Jaspers, Karl"
    assert g1["auto"] == 2 and g1["review"] == 1
    assert g1["docs"] == {"20": [1, 1], "30": [1, 0]}
    # the completeness signal: a listed entity without a single mention stays visible
    g3 = overview["entities"]["g3"]
    assert g3["auto"] == 0 and g3["review"] == 0 and g3["docs"] == {}
    totals = overview["totals"]
    assert totals["listed_entities"] == 3
    assert totals["entities_found"] == 2


def test_per_document_aggregation_counts_and_orders():
    candidates = [
        _cand("20", "g1", 1, "full-name"),
        _cand("20", "g1", 1, "full-name"),
        _cand("20", "g1", 2, "bare-surname:ambiguous"),
        _cand("20", "g2", 2, "org-token:suspect", category="organisation"),
    ]
    overview = build_overview(candidates, ENTRIES)
    doc20 = overview["documents"]["20"]
    assert doc20["auto"] == 2 and doc20["review"] == 2
    assert doc20["classes"] == {"ambiguous": 1, "suspect": 1}
    assert [e["gid"] for e in doc20["entities"]] == ["g1", "g2"]
    assert doc20["entities"][0] == {
        "gid": "g1", "auto": 2, "review": 1, "classes": {"ambiguous": 1},
    }


def test_entity_records_carry_the_review_class_breakdown():
    candidates = [
        _cand("20", "g1", 1, "full-name"),
        _cand("20", "g1", 2, "bare-surname"),
        _cand("30", "g1", 2, "bare-surname:ambiguous"),
        _cand("30", "g1", 2, "org-token:suspect"),
    ]
    overview = build_overview(candidates, ENTRIES)
    assert overview["entities"]["g1"]["classes"] == {
        "ambiguous": 1, "suspect": 1, "unanchored": 1,
    }
    assert overview["entities"]["g2"]["classes"] == {}


def test_totals_carry_the_explicit_mention_sum_and_the_split():
    candidates = [
        _cand("20", "g1", 1, "full-name"),
        _cand("20", "g1", 2, "bare-surname"),
        _cand("30", "g2", 2, "org-token:suspect", category="organisation"),
    ]
    totals = build_overview(candidates, ENTRIES)["totals"]
    assert totals["mentions"] == 3
    assert totals["auto"] == 1 and totals["review"] == 2
    assert totals["mentions"] == totals["auto"] + totals["review"]


# ---------------------------------------------------------------------------
# Ambiguity: entities that only ever appear as an alternative bearer
# ---------------------------------------------------------------------------


def test_alternative_bearers_are_counted_apart_from_the_main_counts():
    candidates = [
        _cand("20", "g1", 1, "anchored-surname", alternatives=["g1", "g2"]),
        _cand("30", "g1", 2, "bare-surname:ambiguous", alternatives=["g1", "g2"]),
    ]
    overview = build_overview(candidates, ENTRIES)
    g1, g2 = overview["entities"]["g1"], overview["entities"]["g2"]
    # the reported bearer keeps exactly the accounting of a run without alternatives
    assert (g1["auto"], g1["review"], g1["alternative_only"]) == (1, 1, 0)
    # the other possible bearer is visible without being folded into auto/review
    assert (g2["auto"], g2["review"], g2["alternative_only"]) == (0, 0, 2)
    totals = overview["totals"]
    assert totals["mentions"] == 2
    assert totals["ambiguous_mentions"] == 2
    assert totals["entities_found"] == 1
    assert totals["entities_alternative_only"] == 1


def test_alternative_gid_outside_the_curated_list_fails_the_closed_world():
    with pytest.raises(ValueError, match="outside the curated list"):
        build_overview([_cand("20", "g1", 1, "full-name", alternatives=["g1", "nope"])],
                       ENTRIES)


def test_unknown_gid_fails_the_closed_world():
    with pytest.raises(ValueError, match="outside the curated list"):
        build_overview([_cand("20", "nope", 1, "full-name")], ENTRIES)


def test_serialization_is_deterministic():
    candidates = [
        _cand("20", "g1", 1, "full-name"),
        _cand("30", "g2", 2, "org-token:suspect", category="organisation"),
    ]
    first = serialize(build_overview(candidates, ENTRIES))
    second = serialize(build_overview(list(reversed(candidates)), dict(ENTRIES)))
    assert first == second
    json.loads(first)


# ---------------------------------------------------------------------------
# Quality block (adjudicated evidence)
# ---------------------------------------------------------------------------


def test_quality_block_mirrors_the_distributions_and_the_protocol_reading():
    verdicts = {
        "snapshot": "2026-01-01",
        "marks": [_mark("correct", iaa="correct", agrees=True, case="p001"),
                  _mark("correct", case="p002"),
                  _mark("wrong_entity", iaa="correct", agrees=False, case="p003"),
                  _mark("undecidable", case="p004")],
        "recall_mentions": [
            {"doc": "20", "page": 1, "status": "hit"},
            {"doc": "20", "page": 2, "status": "on_worklist"},
            {"doc": "30", "page": 3, "status": "missed", "cause": "rule_gap"},
        ],
    }
    quality = quality_block(verdicts)
    assert quality["snapshot"] == "2026-01-01"
    precision = quality["precision"]
    assert precision["n"] == 4
    assert precision["distribution"] == {"correct": 2, "undecidable": 1,
                                         "wrong_entity": 1}
    # undecidable verdicts leave the denominator (protocol reading)
    assert precision["decidable"] == 3 and precision["correct"] == 2
    assert precision["rate"] == round(2 / 3, 4)
    assert precision["ci95"][0] <= precision["rate"] <= precision["ci95"][1]
    recall = quality["recall"]
    assert recall["mentions"] == 3
    assert recall["status"] == {"hit": 1, "missed": 1, "on_worklist": 1}
    assert recall["causes_missed"] == {"rule_gap": 1}
    assert recall["pages_with_mentions"] == 3
    agreement = quality["agreement"]
    assert agreement["n"] == 2 and agreement["agree"] == 1
    assert [d["case"] for d in agreement["disagreements"]] == ["p003"]
    assert agreement["disagreements"][0]["second_verdict"] == "correct"


def test_quality_block_reports_the_latest_wave_and_keeps_the_older_one_visible():
    """Two waves in the store: the figures are the newest wave, the older stays listed."""
    verdicts = {
        "snapshot": "2026-08-21",
        "marks": [_mark("correct", case="p001", wave="adjudication-2026-08-12"),
                  _mark("wrong_entity", case="p002", wave="adjudication-2026-08-12"),
                  _mark("correct", case="p001", wave="adjudication-2026-08-21"),
                  _mark("correct", case="p002", wave="adjudication-2026-08-21"),
                  _mark("undecidable", case="p003", wave="adjudication-2026-08-21")],
        "recall_mentions": [
            {"doc": "20", "page": 1, "status": "hit",
             "source": {"wave": "recall-adjudication-2026-08-12"}},
            {"doc": "20", "page": 2, "status": "missed", "cause": "rule_gap",
             "source": {"wave": "recall-adjudication-2026-08-21"}},
        ],
    }
    quality = quality_block(verdicts)
    assert quality["snapshot"] == "2026-08-21"
    assert quality["precision"]["n"] == 3
    assert quality["precision"]["decidable"] == 2
    assert quality["precision"]["rate"] == 1.0
    assert quality["recall"]["mentions"] == 1
    assert quality["recall"]["status"] == {"missed": 1}
    assert [entry["snapshot"] for entry in quality["snapshots"]] == ["2026-08-12",
                                                                     "2026-08-21"]
    older = quality["snapshots"][0]
    assert older == {"snapshot": "2026-08-12", "n": 2, "decidable": 2, "correct": 1,
                     "rate": 0.5}
    assert quality["snapshots"][1]["n"] == quality["precision"]["n"]


def test_quality_block_treats_a_store_without_wave_names_as_one_wave():
    """A store written before the wave field keeps reporting all of its marks."""
    verdicts = {"snapshot": "2026-01-01", "marks": [_mark("correct")],
                "recall_mentions": [{"doc": "20", "page": 1, "status": "hit"}]}
    quality = quality_block(verdicts)
    assert quality["precision"]["n"] == 1
    assert quality["recall"]["mentions"] == 1
    assert [entry["snapshot"] for entry in quality["snapshots"]] == ["2026-01-01"]


def test_quality_block_without_decidable_marks_reports_no_rate():
    quality = quality_block({"marks": [_mark("undecidable")], "recall_mentions": []})
    assert quality["precision"]["rate"] is None
    assert quality["precision"]["ci95"] is None
    assert quality["recall"]["mentions"] == 0


@pytest.mark.skipif(not VERDICTS_PATH.exists(), reason="verdict store not available")
@pytest.mark.requires_mirror
def test_quality_block_reproduces_the_published_snapshot_figures():
    """The committed verdict store must keep yielding the published evaluation figures.

    The reported wave is the newest one; `snapshots` carries one entry per wave in the
    store, so the earlier measurement stays pinned beside the current one. Interval
    procedure and values follow the executed evaluation (knowledge/verification.md,
    appendix, output/audits/entity_eval_report.json).
    """
    quality = quality_block(_store())
    assert quality["snapshot"] == "2026-08-21"
    precision = quality["precision"]
    assert precision["n"] == 300
    assert precision["distribution"] == {"correct": 296, "not_in_source": 1,
                                         "wrong_entity": 3}
    assert precision["decidable"] == 300 and precision["correct"] == 296
    assert precision["rate"] == 0.9867
    assert precision["ci95"] == [0.9733, 0.9967]
    assert quality["recall"]["mentions"] == 63
    assert quality["recall"]["status"] == {"hit": 38, "missed": 3, "on_worklist": 22}
    assert quality["agreement"] == {"n": 50, "agree": 50, "rate": 1.0,
                                    "disagreements": []}
    assert quality["snapshots"] == [
        {"snapshot": "2026-08-12", "n": 300, "decidable": 293, "correct": 279,
         "rate": 0.9522},
        {"snapshot": "2026-08-21", "n": 300, "decidable": 300, "correct": 296,
         "rate": 0.9867},
    ]


@pytest.mark.skipif(not VERDICTS_PATH.exists(), reason="verdict store not available")
@pytest.mark.requires_mirror
def test_quality_block_reproduces_the_published_figures_of_the_earlier_wave():
    """Read on its own, the 2026-08-12 wave still yields its published figures.

    Two waves are drawn over different candidate populations, so the block reports the
    newest alone and the earlier interval, the recall statuses and the two known IAA
    disagreements would otherwise stop being pinned anywhere.
    """
    quality = quality_block(_wave_slice(_store(), "2026-08-12"))
    precision = quality["precision"]
    assert precision["n"] == 300
    assert precision["distribution"] == {"correct": 279, "not_in_source": 5,
                                         "undecidable": 7, "wrong_entity": 5,
                                         "wrong_span": 4}
    assert precision["decidable"] == 293 and precision["correct"] == 279
    assert precision["rate"] == 0.9522
    assert precision["ci95"] == [0.9249, 0.9761]
    assert quality["recall"]["mentions"] == 67
    assert quality["recall"]["status"] == {"hit": 20, "missed": 30, "on_worklist": 17}
    assert quality["agreement"] == {
        "n": 50, "agree": 48, "rate": 0.96,
        "disagreements": quality["agreement"]["disagreements"],
    }
    assert len(quality["agreement"]["disagreements"]) == 2
    assert [d["case"] for d in quality["agreement"]["disagreements"]] == ["p145", "p193"]


# ---------------------------------------------------------------------------
# Provenance
# ---------------------------------------------------------------------------


def test_provenance_block_names_the_snapshot_and_the_list_size():
    provenance = provenance_block("abc123", 9556, 289)
    assert provenance["scan_sha256"] == "abc123"
    assert provenance["scan_candidates"] == 9556
    assert provenance["listed_entities"] == 289
    assert provenance["scan"].endswith("entity_corpus_scan.json")
    assert "/" in provenance["scan"] and "\\" not in provenance["scan"]
    assert provenance["entity_list"] == "data/entities/all_entities.json"


def test_overview_carries_quality_and_provenance_when_supplied():
    quality = quality_block({"marks": [_mark("correct")], "recall_mentions": []})
    provenance = provenance_block("abc123", 1, 3)
    overview = build_overview([_cand("20", "g1", 1, "full-name")], ENTRIES,
                              quality=quality, provenance=provenance)
    assert overview["provenance"] == provenance
    assert overview["quality"]["precision"]["n"] == 1
    assert list(overview) == ["classes", "provenance", "totals", "quality",
                              "entities", "documents"]
