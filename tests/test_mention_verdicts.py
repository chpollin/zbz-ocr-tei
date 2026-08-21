"""Tests for the mention-level verdict store (scripts/entity/build_mention_verdicts).

Three layers. The unit layer runs on synthetic fixtures in memory and pins the pure
functions (occurrence indexing, record construction, validation, serialization). The
merge layer builds two waves from two synthetic sample directories on disk and pins the
multi-snapshot semantics of the store. The wave layer runs against the real adjudication
evidence. For the 2026-08-12 wave it pins the counts, the verdict distribution and the
two known IAA disagreements; the store tests run once per adjudicated sample directory
and compare only the records carrying that sample's wave name. The whole layer skips
when the evidence directory is absent, so a checkout without output/ still has a green
suite.

GND ids in the synthetic fixtures are placeholders; real ids come from the curated list.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.core.pb_split import page_of, pb_offsets
from scripts.entity.build_mention_verdicts import (
    ENTITIES_PATH,
    EXPECTED_IAA_CASES,
    EXPECTED_IAA_DISAGREEMENTS,
    EXPECTED_PRECISION,
    EXPECTED_RECALL,
    MARK_FIELDS,
    OUT_PATH,
    PRECISION_WAVE,
    RECALL_MENTION_FIELDS,
    RECALL_WAVE,
    SAMPLE_DIR,
    SCAN_GLOB,
    SNAPSHOT,
    build_recall_mentions,
    build_report,
    check_distributions,
    entity_gids,
    frozen_scan_path,
    load_inputs,
    load_precision_verdicts,
    main,
    merge_store,
    occurrence_map,
    record_snapshot,
    serialize,
    snapshot_label,
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
    report = {"snapshot": SNAPSHOT, "marks": [_mark()], "recall_mentions": []}
    anomalies = check_distributions(report)
    assert anomalies and any("precision" in a for a in anomalies)


def test_check_distributions_pins_only_the_wave_it_describes():
    """The expected counts belong to the 2026-08-12 wave; another wave has its own."""
    report = {"snapshot": "2026-08-21", "marks": [_mark()], "recall_mentions": []}
    assert check_distributions(report) == []


def test_serialize_is_stable_and_newline_terminated():
    report = {"snapshot": SNAPSHOT, "sources": ["a"], "marks": [_mark()],
              "recall_mentions": []}
    text = serialize(report)
    assert text.endswith("\n")
    assert serialize(report) == text


# --- merge layer (two synthetic waves on disk) ------------------------------
#
# Two sample directories, one document, one adjudicated case and one read recall page
# each. Synthetic because the second real wave is drawn but not adjudicated; the store
# semantics under test (which wave a record belongs to, what a rebuild replaces) are
# independent of the judgments themselves.


def _make_sample(root, snapshot, *, surface, gid, verdict, page_ref):
    sample = root / f"eval_sample_{snapshot}"
    (sample / "verdicts").mkdir(parents=True)
    start = _XML.index(surface)
    case_id = "p001"
    _write_json(sample / "precision_cases.json", [{
        "case_id": case_id, "doc": "100", "page": page_of(pb_offsets(_XML), start),
        "surface": surface, "gid": gid, "start": start, "end": start + len(surface),
        "category": "person", "rule": "full-name", "matched_form": surface,
        "form_source": "headword"}])
    _write_json(sample / "recall_pages.json",
                [{"case_id": page_ref, "doc": "100", "page": 1}])
    _write_json(sample / "sample_manifest.json",
                {"sources": {"scan": {"modified": f"{snapshot}T10:00:00+00:00"}}})
    _write_json(sample / f"entity_corpus_scan_frozen_{snapshot}.json",
                {"candidates": [_candidate(surface=surface, start=start, gid=gid)]})
    _write_json(sample / "verdicts" / f"precision_{case_id}.json",
                [{"case_id": case_id, "verdict": verdict, "reason": "synthetic"}])
    _write_json(sample / "verdicts" / "precision_iaa.json", [])
    _write_json(sample / "verdicts" / f"recall_{page_ref}.json",
                {page_ref: {"doc": "100", "page": 1, "mentions": [
                    {"surface": "Hersch", "gid": "TEST-0002", "status": "hit",
                     "note": "synthetic"}]}})
    return sample


@pytest.fixture
def corpus(tmp_path):
    """TEI directory and entity list the synthetic samples are adjudicated against."""
    tei_dir = tmp_path / "tei_final"
    tei_dir.mkdir()
    (tei_dir / "100_final.xml").write_bytes(_XML.encode("utf-8"))
    entities = _write_json(tmp_path / "all_entities.json", {
        "persons": [{"GND_id": "TEST-0001"}, {"GND_id": "TEST-0002"}], "works": []})
    return {"tei_dir": tei_dir, "entities_path": entities}


@pytest.fixture
def waves(tmp_path, corpus):
    """The two built wave payloads, A older than B, judging different mentions."""
    sample_a = _make_sample(tmp_path, "2026-08-12", surface="Jaspers", gid="TEST-0001",
                            verdict="correct", page_ref="r001")
    sample_b = _make_sample(tmp_path, "2026-08-21", surface="Hersch", gid="TEST-0002",
                            verdict="wrong_entity", page_ref="r002")
    return {"a": build_report(sample_dir=sample_a, **corpus),
            "b": build_report(sample_dir=sample_b, **corpus),
            "dir_a": sample_a, "dir_b": sample_b}


def test_frozen_scan_path_reads_the_one_scan_of_a_sample_directory(tmp_path):
    sample = _make_sample(tmp_path, "2026-08-21", surface="Hersch", gid="TEST-0002",
                          verdict="correct", page_ref="r002")
    assert frozen_scan_path(sample).name == "entity_corpus_scan_frozen_2026-08-21.json"


def test_frozen_scan_path_refuses_an_ambiguous_or_empty_directory(tmp_path):
    empty = tmp_path / "empty"
    empty.mkdir()
    with pytest.raises(FileNotFoundError):
        frozen_scan_path(empty)
    _write_json(empty / "entity_corpus_scan_frozen_a.json", {})
    _write_json(empty / "entity_corpus_scan_frozen_b.json", {})
    with pytest.raises(ValueError, match="several"):
        frozen_scan_path(empty)


def test_snapshot_label_follows_the_sample_manifest():
    assert snapshot_label({"sources": {"scan": {"modified": "2026-08-21T10:00:00+00:00"},
                                       "catalog": {"modified": "2026-08-13T00:00:00+00:00"}}}) \
        == "2026-08-21"
    with pytest.raises(ValueError):
        snapshot_label({"sources": {"tei_dir": "output/tei_final"}})


def test_a_second_sample_directory_builds_its_own_wave(waves, corpus):
    wave = waves["b"]
    assert wave["snapshot"] == "2026-08-21"
    assert [m["source"]["wave"] for m in wave["marks"]] == ["adjudication-2026-08-21"]
    assert [m["source"]["wave"] for m in wave["recall_mentions"]] == [
        "recall-adjudication-2026-08-21"]
    inputs = load_inputs(sample_dir=waves["dir_b"], **corpus)
    assert validate(wave, inputs["cases"], inputs["gids"], inputs["drawn_pages"],
                    inputs["placement"]) == []


def test_a_sample_without_adjudication_files_is_named_as_such(corpus, waves):
    """The second wave is drawn long before it is judged; the builder says what is missing."""
    sample = waves["dir_b"]
    (sample / "verdicts" / "precision_iaa.json").unlink()
    for path in (sample / "verdicts").glob("recall_r*.json"):
        path.unlink()
    with pytest.raises(FileNotFoundError, match=r"precision_iaa\.json"):
        load_inputs(sample_dir=sample, **corpus)
    assert main(["--sample-dir", str(sample), "--dry-run"]) == 1


def test_record_snapshot_reads_the_label_back_out_of_both_wave_names():
    for template in (PRECISION_WAVE, RECALL_WAVE):
        record = {"source": {"wave": template.format(snapshot="2026-08-21")}}
        assert record_snapshot(record) == "2026-08-21"
    assert record_snapshot({}, default="2026-08-21") == "2026-08-21"


def test_merge_keeps_the_other_wave_and_replaces_its_own(waves):
    store = merge_store(merge_store(None, waves["a"]), waves["b"])
    assert [m["source"]["wave"] for m in store["marks"]] == [
        "adjudication-2026-08-12", "adjudication-2026-08-21"]
    assert [m["source"]["wave"] for m in store["recall_mentions"]] == [
        "recall-adjudication-2026-08-12", "recall-adjudication-2026-08-21"]

    rebuilt = merge_store(store, waves["b"])
    assert serialize(rebuilt) == serialize(store)
    assert len(rebuilt["marks"]) == 2

    reordered = merge_store(merge_store(None, waves["b"]), waves["a"])
    assert serialize(reordered) == serialize(store)


def test_merge_names_the_latest_snapshot_and_unions_the_sources(waves):
    store = merge_store(merge_store(None, waves["a"]), waves["b"])
    assert store["snapshot"] == "2026-08-21"
    assert [entry["snapshot"] for entry in store["snapshots"]] == ["2026-08-12", "2026-08-21"]
    assert store["sources"] == sorted(set(waves["a"]["sources"]) | set(waves["b"]["sources"]))
    for entry, wave in zip(store["snapshots"], (waves["a"], waves["b"]), strict=True):
        assert entry["sources"] == wave["sources"]
        assert len(entry["scan_sha256"]) == 64
    assert list(store) == ["snapshot", "sources", "snapshots", "marks", "recall_mentions"]


def test_merge_lifts_a_store_written_before_the_snapshots_list(waves):
    legacy = {"snapshot": waves["a"]["snapshot"], "sources": waves["a"]["sources"],
              "marks": waves["a"]["marks"],
              "recall_mentions": waves["a"]["recall_mentions"]}
    store = merge_store(legacy, waves["b"])
    assert [entry["snapshot"] for entry in store["snapshots"]] == ["2026-08-12", "2026-08-21"]
    assert store["snapshots"][0]["sources"] == waves["a"]["sources"]
    assert store["snapshots"][0]["scan_sha256"] is None
    assert len(store["marks"]) == 2


def test_a_single_wave_store_keeps_the_records_of_the_wave_payload(waves):
    store = merge_store(None, waves["a"])
    assert store["marks"] == waves["a"]["marks"]
    assert store["recall_mentions"] == waves["a"]["recall_mentions"]
    assert store["snapshot"] == waves["a"]["snapshot"]
    assert store["sources"] == waves["a"]["sources"]


# --- wave layer (real adjudication evidence) --------------------------------

_HAVE_EVIDENCE = (SAMPLE_DIR.exists() and any(SAMPLE_DIR.glob(SCAN_GLOB))
                  and ENTITIES_PATH.exists())
def requires_evidence(fn):
    """Wave-layer test: needs the adjudication evidence under the gitignored output/."""
    skip = pytest.mark.skipif(
        not _HAVE_EVIDENCE, reason="adjudication evidence under output/ not present")
    return pytest.mark.requires_corpus(skip(fn))


def _adjudicated_samples() -> list[Path]:
    """Every sample directory that carries a complete adjudication, oldest wave first.

    A sample is drawn long before it is judged, so a drawn-only directory is no wave of
    the store and stays out of the parametrization.
    """
    if not _HAVE_EVIDENCE:
        return []
    candidates = [SAMPLE_DIR, *sorted(SAMPLE_DIR.parent.glob("eval_sample_*"))]
    return [path for path in candidates if any(path.glob(SCAN_GLOB))
            and any((path / "verdicts").glob("precision_p*.json"))]


_SAMPLES = _adjudicated_samples()
_SAMPLE_IDS = [path.name for path in _SAMPLES]


def _wave_records(records: list[dict], snapshot: str) -> list[dict]:
    """The store records belonging to one wave, in stored order."""
    return [record for record in records if record_snapshot(record) == snapshot]


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
    assert set(wave) == {"snapshot", "sources", "scan_sha256", "marks", "recall_mentions"}
    assert wave["sources"] == sorted(wave["sources"])
    assert len(wave["scan_sha256"]) == 64
    for mark in wave["marks"]:
        assert set(MARK_FIELDS) <= set(mark)
        assert len(mark["text_sha256"]) == 64
        assert mark["occurrence"] >= 1
        assert mark["source"]["wave"] == f"adjudication-{SNAPSHOT}"
    for mention in wave["recall_mentions"]:
        assert set(RECALL_MENTION_FIELDS) <= set(mention)
        assert ("cause" in mention) == (mention["status"] == "missed")


@requires_evidence
@pytest.mark.parametrize("sample_dir", _SAMPLES, ids=_SAMPLE_IDS)
def test_written_store_matches_a_fresh_build(sample_dir):
    """A fresh build of a sample must still be exactly the stored records of its wave.

    Scoped by wave, because the store holds several adjudications and a rebuild of one
    sample speaks for its own records alone. Only the records are compared; the
    envelope carries the union over all waves and would fail on that alone.
    """
    if not OUT_PATH.exists():
        pytest.skip("store not built yet")
    stored = json.loads(OUT_PATH.read_text(encoding="utf-8"))
    fresh = json.loads(serialize(build_report(sample_dir=sample_dir)))
    snapshot = fresh["snapshot"]
    assert snapshot in [entry["snapshot"] for entry in stored["snapshots"]]
    # text_sha256 fingerprints the live tei_final and drifts when a text repair
    # touches a document after the snapshot; the verdict guard consumes that
    # drift as text_changed. Every adjudication payload must still reproduce.
    for record in (*stored["marks"], *fresh["marks"]):
        record["text_sha256"] = "MASKED"
    assert _wave_records(stored["marks"], snapshot) == fresh["marks"]
    assert _wave_records(stored["recall_mentions"], snapshot) == fresh["recall_mentions"]


@requires_evidence
@pytest.mark.parametrize("sample_dir", _SAMPLES, ids=_SAMPLE_IDS)
def test_remerging_a_wave_into_the_committed_store_changes_no_record(sample_dir):
    """Rebuilding one wave leaves every record of every wave, its own included, as is.

    The ``snapshots`` list must keep naming exactly the waves the records carry, so a
    wave can neither vanish from the listing nor be listed without records.
    """
    if not OUT_PATH.exists():
        pytest.skip("store not built yet")
    stored = json.loads(OUT_PATH.read_text(encoding="utf-8"))
    merged = merge_store(stored, json.loads(serialize(build_report(sample_dir=sample_dir))))
    for record in (*stored["marks"], *merged["marks"]):
        record["text_sha256"] = "MASKED"
    assert merged["marks"] == stored["marks"]
    assert merged["recall_mentions"] == stored["recall_mentions"]
    assert merged["snapshot"] == stored["snapshot"]
    listed = [entry["snapshot"] for entry in merged["snapshots"]]
    assert listed == [entry["snapshot"] for entry in stored["snapshots"]]
    assert listed == sorted({record_snapshot(record) for record
                             in (*merged["marks"], *merged["recall_mentions"])})
