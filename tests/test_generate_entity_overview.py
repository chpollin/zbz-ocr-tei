"""Tests for scripts/edition/generate_entity_overview.py (entity overview mirror).

Synthetic candidate fixtures only; the aggregation contract is pinned here: class
assignment per rule string, the per-entity completeness aggregation including
zero-mention list entries, per-document counts, deterministic ordering, closed-world
failure on an unknown gid, and byte-identical serialization.
"""

from __future__ import annotations

import json

import pytest

from scripts.edition.generate_entity_overview import (
    CLASSES,
    build_overview,
    classify,
    list_entries,
    serialize,
)


def _cand(doc, gid, tier, rule, category="person", page=1):
    return {"doc": doc, "gid": gid, "tier": tier, "rule": rule,
            "category": category, "page": page}


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


def test_class_catalog_keys_are_unique_and_cover_classify_output():
    keys = [key for key, _, _ in CLASSES]
    assert len(keys) == len(set(keys))
    assert set(keys) >= {"ambiguous", "suspect", "unanchored", "running_head",
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
