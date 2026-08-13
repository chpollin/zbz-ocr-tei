"""Tests for the mention-level verdict store (scripts/eval/build_mention_verdicts).

Two layers. The unit layer runs on synthetic fixtures in memory and pins the pure
functions (occurrence indexing, record construction, validation, serialization). The
wave layer runs against the real adjudication evidence of the 2026-08-12 wave and pins
its counts, its verdict distribution and the two known IAA disagreements; it skips when
the evidence directory is absent, so a checkout without output/ still has a green suite.

GND ids in the synthetic fixtures are placeholders; real ids come from the curated list.
"""

from __future__ import annotations

import json

import pytest

from scripts.eval.build_mention_verdicts import (
    ENTITIES_PATH,
    EXPECTED_IAA_CASES,
    EXPECTED_IAA_DISAGREEMENTS,
    EXPECTED_PRECISION,
    EXPECTED_RECALL,
    MARK_FIELDS,
    OUT_PATH,
    RECALL_MENTION_FIELDS,
    SAMPLE_DIR,
    SCAN_PATH,
    SNAPSHOT,
    build_recall_mentions,
    build_report,
    check_distributions,
    entity_gids,
    load_precision_verdicts,
    occurrence_map,
    serialize,
    validate,
)

# --- synthetic fixtures -----------------------------------------------------

_XML = (
    '<TEI xmlns="http://www.tei-c.org/ns/1.0"><text><body>'
    '<pb n="1"/><p>Jaspers und Jaspers, dazu Hersch.</p>'
    '<pb n="2"/><p>Jaspers erneut.</p>'
    "</body></text></TEI>"
)


def _candidate(doc="100", surface="Jaspers", start=0, gid="TEST-0001", tier=1):
    return {"doc": doc, "surface": surface, "start": start, "end": start + len(surface),
            "gid": gid, "tier": tier}


def _pb_by_doc(xml=_XML):
    from scripts.edition.generate_entity_preview_data import pb_offsets

    return {"100": pb_offsets(xml)}


def _write_json(path, payload):
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


# --- unit layer -------------------------------------------------------------


def test_occurrence_map_indexes_per_page_and_pair():
    pb = _pb_by_doc()
    page2 = _XML.index("Jaspers erneut")
    first, second = (_XML.index("Jaspers"), _XML.index("Jaspers", _XML.index("Jaspers") + 1))
    candidates = [
        _candidate(start=second),
        _candidate(start=first),
        _candidate(start=page2),
        _candidate(start=_XML.index("Hersch"), surface="Hersch", gid="TEST-0002"),
    ]
    placement = occurrence_map(candidates, pb)
    assert placement[("100", first)] == (1, 1)
    assert placement[("100", second)] == (1, 2)
    # New page restarts the count, and a different (surface, gid) pair counts separately.
    assert placement[("100", page2)] == (2, 1)
    assert placement[("100", _XML.index("Hersch"))] == (1, 1)


def test_occurrence_map_ignores_tier2():
    pb = _pb_by_doc()
    first = _XML.index("Jaspers")
    placement = occurrence_map([_candidate(start=first, tier=2)], pb)
    assert placement == {}


def test_load_precision_verdicts_rejects_duplicate_case(tmp_path):
    a = _write_json(tmp_path / "precision_p001_p050.json",
                    [{"case_id": "p001", "verdict": "correct", "reason": "r"}])
    b = _write_json(tmp_path / "precision_p051_p100.json",
                    [{"case_id": "p001", "verdict": "wrong_span", "reason": "r"}])
    with pytest.raises(ValueError, match="p001"):
        load_precision_verdicts([a, b])


def test_build_recall_mentions_carries_cause_only_when_missed():
    pages = {
        "r002": {"doc": "100", "page": 3, "mentions": [
            {"surface": "Hersch", "gid": "TEST-0002", "status": "hit", "note": "wrapped"},
            {"surface": "Jaspers", "gid": "TEST-0001", "status": "missed",
             "cause": "rule_gap", "note": "not reported"},
        ]},
        "r001": {"doc": "100", "page": 1, "mentions": [
            {"surface": "Jaspers", "gid": "TEST-0001", "status": "on_worklist", "note": "tier 2"},
        ]},
    }
    mentions = build_recall_mentions(pages, "recall-wave")
    assert [m["source"]["page_ref"] for m in mentions] == ["r001", "r002", "r002"]
    assert "cause" not in mentions[0] and "cause" not in mentions[1]
    assert mentions[2]["cause"] == "rule_gap"
    for mention in mentions:
        assert set(RECALL_MENTION_FIELDS) <= set(mention)
        assert mention["source"]["wave"] == "recall-wave"


def test_entity_gids_reads_all_three_groups(tmp_path):
    path = _write_json(tmp_path / "all_entities.json", {
        "persons": [{"GND_id": "TEST-0001"}],
        "organisations": [{"GND_id": "TEST-0002"}],
        "works": [{"GND_id": "TEST-0003"}],
    })
    assert entity_gids(json.loads(path.read_text(encoding="utf-8"))) == {
        "TEST-0001", "TEST-0002", "TEST-0003"}


def _mark(case_id="p001", occurrence=1, gid="TEST-0001", start=10, page=1):
    return {"doc": "100", "page": page, "surface": "Jaspers", "gid": gid,
            "occurrence": occurrence, "category": "person", "rule": "surname",
            "matched_form": "Jaspers", "form_source": "headword", "start": start,
            "end": start + 7, "verdict": "correct", "reason": "r",
            "source": {"wave": "w", "case_id": case_id}, "text_sha256": "0" * 64}


def _case(case_id="p001", start=10, page=1, gid="TEST-0001"):
    return {"case_id": case_id, "doc": "100", "page": page, "surface": "Jaspers",
            "gid": gid, "start": start, "end": start + 7}


def test_validate_accepts_a_consistent_pair():
    report = {"marks": [_mark()], "recall_mentions": []}
    placement = {("100", 10): (1, 1)}
    assert validate(report, [_case()], {"TEST-0001"}, {"r001": ("100", 1)}, placement) == []


def test_validate_flags_unknown_gid_and_normalization_hit():
    report = {"marks": [_mark(gid="test-0001")], "recall_mentions": []}
    errors = validate(report, [_case(gid="test-0001")], {"TEST-0001"},
                      {}, {("100", 10): (1, 1)})
    assert any("normalization" in e for e in errors)


def test_validate_flags_duplicate_key_and_missing_case():
    report = {"marks": [_mark(), _mark(case_id="p002", start=40)], "recall_mentions": []}
    placement = {("100", 10): (1, 1), ("100", 40): (1, 1)}
    errors = validate(report, [_case(), _case("p002", start=40)], {"TEST-0001"}, {}, placement)
    assert any("duplicate mark key" in e for e in errors)

    report = {"marks": [_mark()], "recall_mentions": []}
    errors = validate(report, [_case(), _case("p002", start=40)], {"TEST-0001"}, {},
                      {("100", 10): (1, 1), ("100", 40): (1, 1)})
    assert any("p002" in e for e in errors)


def test_validate_flags_page_disagreement_with_the_scan():
    report = {"marks": [_mark(page=1)], "recall_mentions": []}
    errors = validate(report, [_case(page=1)], {"TEST-0001"}, {}, {("100", 10): (2, 1)})
    assert any("page" in e for e in errors)


def test_check_distributions_reports_deviation():
    report = {"marks": [_mark()], "recall_mentions": []}
    anomalies = check_distributions(report)
    assert anomalies and any("precision" in a for a in anomalies)


def test_serialize_is_stable_and_newline_terminated():
    report = {"snapshot": SNAPSHOT, "sources": ["a"], "marks": [_mark()],
              "recall_mentions": []}
    text = serialize(report)
    assert text.endswith("\n")
    assert serialize(report) == text


# --- wave layer (real adjudication evidence) --------------------------------

_HAVE_EVIDENCE = SAMPLE_DIR.exists() and SCAN_PATH.exists() and ENTITIES_PATH.exists()
requires_evidence = pytest.mark.skipif(
    not _HAVE_EVIDENCE, reason="adjudication evidence under output/ not present")


@pytest.fixture(scope="module")
def wave():
    return build_report()


@requires_evidence
def test_build_is_deterministic(wave):
    assert serialize(build_report()) == serialize(wave)


@requires_evidence
def test_counts_and_distribution(wave):
    assert wave["snapshot"] == SNAPSHOT
    assert len(wave["marks"]) == sum(EXPECTED_PRECISION.values()) == 300
    assert len(wave["recall_mentions"]) == sum(EXPECTED_RECALL.values()) == 67
    counted = {}
    for mark in wave["marks"]:
        counted[mark["verdict"]] = counted.get(mark["verdict"], 0) + 1
    assert counted == EXPECTED_PRECISION
    recall = {}
    for mention in wave["recall_mentions"]:
        recall[mention["status"]] = recall.get(mention["status"], 0) + 1
    assert recall == EXPECTED_RECALL
    assert check_distributions(wave) == []


@requires_evidence
def test_undecidable_cases_are_kept(wave):
    undecidable = [m for m in wave["marks"] if m["verdict"] == "undecidable"]
    assert len(undecidable) == 7


@requires_evidence
def test_mark_key_is_unique(wave):
    keys = {(m["doc"], m["page"], m["surface"], m["gid"], m["occurrence"])
            for m in wave["marks"]}
    assert len(keys) == len(wave["marks"])


@requires_evidence
def test_every_gid_is_listed(wave):
    listed = entity_gids(json.loads(ENTITIES_PATH.read_text(encoding="utf-8")))
    used = {m["gid"] for m in wave["marks"]} | {m["gid"] for m in wave["recall_mentions"]}
    assert used <= listed


@requires_evidence
def test_iaa_is_attached_with_the_known_disagreements(wave):
    with_iaa = [m for m in wave["marks"] if "iaa" in m]
    assert len(with_iaa) == EXPECTED_IAA_CASES
    disagreeing = sorted(m["source"]["case_id"] for m in with_iaa if not m["iaa_agrees"])
    assert disagreeing == sorted(EXPECTED_IAA_DISAGREEMENTS)
    for mark in with_iaa:
        assert set(mark["iaa"]) == {"verdict", "reason"}
        assert mark["iaa_agrees"] == (mark["iaa"]["verdict"] == mark["verdict"])


@requires_evidence
def test_schema_fields_present(wave):
    assert set(wave) == {"snapshot", "sources", "marks", "recall_mentions"}
    assert wave["sources"] == sorted(wave["sources"])
    for mark in wave["marks"]:
        assert set(MARK_FIELDS) <= set(mark)
        assert len(mark["text_sha256"]) == 64
        assert mark["occurrence"] >= 1
        assert mark["source"]["wave"] == f"adjudication-{SNAPSHOT}"
    for mention in wave["recall_mentions"]:
        assert set(RECALL_MENTION_FIELDS) <= set(mention)
        assert ("cause" in mention) == (mention["status"] == "missed")


@requires_evidence
def test_written_store_matches_a_fresh_build(wave):
    if not OUT_PATH.exists():
        pytest.skip("store not built yet")
    stored = json.loads(OUT_PATH.read_text(encoding="utf-8"))
    fresh = json.loads(serialize(wave))
    # text_sha256 fingerprints the live tei_final and drifts when a text repair
    # touches a document after the snapshot; the verdict guard consumes that
    # drift as text_changed. Every adjudication payload must still reproduce.
    for record in (*stored["marks"], *fresh["marks"]):
        record["text_sha256"] = "MASKED"
    assert stored == fresh
