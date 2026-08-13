"""Tests for scripts/edition/generate_entity_overview.py (entity overview mirror).

Synthetic candidate and verdict fixtures only; the aggregation contract is pinned here:
class assignment per rule string, per-document and per-entity counts, deterministic
ordering, closed-world failure on an unknown gid, and byte-identical serialization.
"""

from __future__ import annotations

import json

import pytest

from scripts.edition.generate_entity_overview import (
    CLASSES,
    build_overview,
    classify,
    serialize,
)


def _cand(doc, gid, tier, rule, category="person", page=1):
    return {"doc": doc, "gid": gid, "tier": tier, "rule": rule,
            "category": category, "page": page}


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
# Aggregation
# ---------------------------------------------------------------------------


ALLOWED = {"g1", "g2", "g3"}


def test_build_overview_counts_per_document_and_entity():
    candidates = [
        _cand("20", "g1", 1, "full-name"),
        _cand("20", "g1", 1, "full-name"),
        _cand("20", "g1", 2, "bare-surname:ambiguous"),
        _cand("20", "g2", 2, "org-token:suspect", category="organisation"),
        _cand("30", "g3", 1, "work-title", category="work"),
    ]
    overview = build_overview(candidates, marks=[], allowed_gids=ALLOWED)
    doc20 = overview["documents"]["20"]
    assert doc20["auto"] == 2
    assert doc20["review"] == 2
    assert doc20["classes"] == {"ambiguous": 1, "suspect": 1}
    assert [e["gid"] for e in doc20["entities"]] == ["g1", "g2"]
    assert doc20["entities"][0] == {
        "gid": "g1", "auto": 2, "review": 1, "classes": {"ambiguous": 1},
    }
    assert overview["documents"]["30"]["auto"] == 1
    totals = overview["totals"]
    assert totals["documents"] == 2
    assert totals["auto"] == 3
    assert totals["review"] == 2


def test_entities_are_ordered_by_volume_then_gid():
    candidates = [
        _cand("20", "g2", 1, "org-name", category="organisation"),
        _cand("20", "g1", 1, "full-name"),
        _cand("20", "g1", 1, "full-name"),
        _cand("20", "g3", 1, "work-title", category="work"),
    ]
    overview = build_overview(candidates, marks=[], allowed_gids=ALLOWED)
    assert [e["gid"] for e in overview["documents"]["20"]["entities"]] == [
        "g1", "g2", "g3",
    ]


def test_adjudicated_marks_join_per_document():
    marks = [
        {"doc": "20", "verdict": "correct"},
        {"doc": "20", "verdict": "correct"},
        {"doc": "20", "verdict": "wrong_entity"},
        {"doc": "99", "verdict": "correct"},
    ]
    overview = build_overview([_cand("20", "g1", 1, "full-name")],
                              marks=marks, allowed_gids=ALLOWED)
    assert overview["documents"]["20"]["checked"] == {
        "total": 3, "correct": 2, "wrong_entity": 1,
    }
    # a verdict for a document without candidates still surfaces
    assert overview["documents"]["99"]["checked"]["total"] == 1
    assert overview["totals"]["checked"]["total"] == 4


def test_unknown_gid_fails_the_closed_world():
    with pytest.raises(ValueError, match="outside the curated list"):
        build_overview([_cand("20", "nope", 1, "full-name")],
                       marks=[], allowed_gids=ALLOWED)


def test_serialization_is_deterministic():
    candidates = [
        _cand("20", "g1", 1, "full-name"),
        _cand("30", "g2", 2, "org-token:suspect", category="organisation"),
    ]
    first = serialize(build_overview(candidates, [], ALLOWED))
    second = serialize(build_overview(list(reversed(candidates)), [], ALLOWED))
    assert first == second
    json.loads(first)
