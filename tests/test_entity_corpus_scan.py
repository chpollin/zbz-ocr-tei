"""Tests for the corpus-wide entity candidate scan (scripts/eval/entity_corpus_scan).

The scan is a read-only diagnosis instrument: it dumps every candidate the matcher
finds, with rule, tier and context, and checks two invariants on the tier-1 set.

All fixtures are synthetic mini TEIs and a tiny entity list in tmp_path. No test reads
output/, none touches the network, and the real corpus run is an operator step outside
the suite. GND ids in the fixtures are placeholders; real ids come from the curated
list only.
"""

from __future__ import annotations

import json

from scripts.eval.entity_corpus_scan import (
    FUNCTION_WORDS,
    INVARIANTS,
    build_scan_report,
    check_invariants,
    main,
    resolve_docs,
    run_scan,
    scan_document,
)

# --- fixtures ---------------------------------------------------------------

_MINI = (
    '<TEI xmlns="http://www.tei-c.org/ns/1.0"><text><body><div type="text">'
    "<p>Karl Jaspers und Jeanne Hersch.</p>"
    "</div></body></text></TEI>"
)

_MINI_HYPHEN = (
    '<TEI xmlns="http://www.tei-c.org/ns/1.0"><text><body><div type="text">'
    "<p>Karl Jaspers sprach am Karl-Jaspers-Symposium.</p>"
    "</div></body></text></TEI>"
)

_ENTITIES = {
    "persons": [
        {"GND_id": "TEST-0001", "name": "Jaspers, Karl"},
        {"GND_id": "TEST-0002", "name": "Hersch, Jeanne"},
    ],
    "organisations": [],
    "works": [],
}


def _rec(doc="100", gid="TEST-0001", surface="Karl Jaspers", start=0, tier=1,
         rule="full-name", category="person", context=None):
    return {
        "doc": doc,
        "gid": gid,
        "category": category,
        "surface": surface,
        "start": start,
        "end": start + len(surface),
        "tier": tier,
        "rule": rule,
        "context": surface if context is None else context,
    }


def _fake_matcher(xml_string, lexicon):
    """Two candidates per document, offsets taken from the string itself."""
    start = xml_string.index("Karl Jaspers")
    return [
        _drop_doc(_rec(start=start)),
        _drop_doc(_rec(gid="TEST-0002", surface="Hersch", tier=2, rule="bare-surname",
                       start=xml_string.index("Hersch"))),
    ]


def _drop_doc(record):
    """The matcher contract has no doc key; the scan adds it."""
    return {k: v for k, v in record.items() if k != "doc"}


def _write_entities(tmp_path):
    path = tmp_path / "entities.json"
    path.write_text(json.dumps(_ENTITIES), encoding="utf-8")
    return path


# --- record shape and ordering ----------------------------------------------

def test_record_carries_the_documented_keys_in_order():
    records, _ = scan_document("100", _MINI, {}, _fake_matcher)
    assert [list(r) for r in records] == [
        ["doc", "gid", "category", "surface", "start", "end", "tier", "rule", "context"]
    ] * 2
    assert {r["doc"] for r in records} == {"100"}


def test_candidates_are_sorted_by_doc_and_start():
    records = [
        _rec(doc="290", start=50),
        _rec(doc="100", start=90),
        _rec(doc="100", start=10),
    ]
    report = build_scan_report(records, {}, _no_violations(), {}, _sources())
    assert [(c["doc"], c["start"]) for c in report["candidates"]] == [
        ("100", 10), ("100", 90), ("290", 50)
    ]


# --- invariants --------------------------------------------------------------

def _no_violations():
    return {name: [] for name in INVARIANTS}


def _sources():
    return {"entities": "entities.json", "cache": "cache.json", "legacy": None}


def test_function_word_list_carries_the_documented_minimum():
    assert {"weil", "wahl"} <= FUNCTION_WORDS


def test_function_word_invariant_flags_a_tier1_surface():
    xml = "<p>Weil sie kam.</p>"
    records = [_rec(surface="Weil", start=xml.index("Weil"), rule="anchored-surname")]
    violations = check_invariants(records, xml)
    assert [v["surface"] for v in violations["function_word_tier1"]] == ["Weil"]
    assert violations["function_word_tier1"][0]["doc"] == "100"
    assert violations["hyphen_adjacent_tier1"] == []


def test_function_word_invariant_ignores_tier2():
    xml = "<p>Weil sie kam.</p>"
    records = [_rec(surface="Weil", start=xml.index("Weil"), tier=2, rule="bare-surname")]
    assert check_invariants(records, xml)["function_word_tier1"] == []


def test_hyphen_adjacent_invariant_flags_a_span_touching_a_hyphen():
    start = _MINI_HYPHEN.index("Karl-Jaspers") + 5
    records = [_rec(surface="Jaspers", start=start, rule="anchored-surname")]
    violations = check_invariants(records, _MINI_HYPHEN)["hyphen_adjacent_tier1"]
    assert len(violations) == 1
    assert violations[0]["surface"] == "Jaspers"
    assert violations[0]["hyphen"] == "both"


def test_hyphen_adjacent_invariant_names_the_touching_side():
    xml = "<p>Jaspers-Symposium</p>"
    records = [_rec(surface="Jaspers", start=xml.index("Jaspers"))]
    assert check_invariants(records, xml)["hyphen_adjacent_tier1"][0]["hyphen"] == "after"


def test_a_clean_tier1_span_violates_nothing():
    records = [_rec(start=_MINI.index("Karl Jaspers"))]
    assert check_invariants(records, _MINI) == _no_violations()


def test_every_invariant_is_reported_even_without_violations():
    report = build_scan_report([], {}, _no_violations(), {}, _sources())
    assert set(report["invariants"]) == set(INVARIANTS)
    assert all(payload["violations"] == [] for payload in report["invariants"].values())


# --- report ------------------------------------------------------------------

def test_report_totals_by_rule_and_by_doc():
    records = [
        _rec(doc="100", start=10),
        _rec(doc="100", gid="TEST-0002", surface="Hersch", start=40, tier=2,
             rule="bare-surname"),
        _rec(doc="290", start=20),
    ]
    by_doc = {"290": {"tier1": 1, "tier2": 0}, "100": {"tier1": 1, "tier2": 1}}
    report = build_scan_report(records, by_doc, _no_violations(),
                               {"TEST-0001": "Jaspers, Karl"}, _sources())
    assert report["totals"] == {"tier1": 2, "tier2": 1, "candidates": 3}
    assert report["by_rule"] == {"full-name": 2, "bare-surname": 1}
    assert list(report["by_doc"]) == ["100", "290"]
    assert report["by_doc"]["100"] == {"tier1": 1, "tier2": 1}
    assert report["generated_from"] == {**_sources(), "code": "entity_matcher"}


def test_top_entities_count_tier1_only_and_stay_capped():
    records = [_rec(gid=f"TEST-{i:04d}", start=i) for i in range(30)]
    records += [_rec(gid="TEST-0001", start=100), _rec(gid="TEST-0001", start=200)]
    records += [_rec(gid="TEST-9999", start=300, tier=2, rule="bare-surname")]
    labels = {"TEST-0001": "Jaspers, Karl"}
    top = build_scan_report(records, {}, _no_violations(), labels, _sources())["by_entity_top"]
    assert len(top) == 25
    assert top[0] == ["TEST-0001", "Jaspers, Karl", 3]
    assert all(entry[0] != "TEST-9999" for entry in top)
    assert [entry[2] for entry in top] == sorted((e[2] for e in top), reverse=True)


def test_report_is_json_serializable_and_stable():
    records = [_rec(doc="290", start=5), _rec(doc="100", start=7)]
    args = (records, {"100": {"tier1": 1, "tier2": 0}}, _no_violations(), {}, _sources())
    first = json.dumps(build_scan_report(*args), ensure_ascii=False, sort_keys=False)
    second = json.dumps(build_scan_report(*args), ensure_ascii=False, sort_keys=False)
    assert first == second


# --- document resolution ------------------------------------------------------

def test_resolve_docs_takes_the_whole_directory_by_default(tmp_path):
    (tmp_path / "290_final.xml").write_text(_MINI, encoding="utf-8")
    (tmp_path / "100_final.xml").write_text(_MINI, encoding="utf-8")
    (tmp_path / "notes.txt").write_text("x", encoding="utf-8")
    assert [doc for doc, _ in resolve_docs(tmp_path)] == ["100", "290"]


def test_resolve_docs_skips_a_missing_document(tmp_path):
    (tmp_path / "100_final.xml").write_text(_MINI, encoding="utf-8")
    assert [doc for doc, _ in resolve_docs(tmp_path, ["100", "8888"])] == ["100"]


# --- run ----------------------------------------------------------------------

def test_run_scan_aggregates_over_documents(tmp_path):
    for doc in ("100", "290"):
        (tmp_path / f"{doc}_final.xml").write_text(_MINI, encoding="utf-8")
    lexicon = {"entries": {"TEST-0001": {"label": "Jaspers, Karl"}}}
    report = run_scan(resolve_docs(tmp_path), lexicon, _fake_matcher, _sources())
    assert report["totals"] == {"tier1": 2, "tier2": 2, "candidates": 4}
    assert list(report["by_doc"]) == ["100", "290"]
    assert report["by_entity_top"][0] == ["TEST-0001", "Jaspers, Karl", 2]


def test_run_scan_leaves_the_source_files_untouched(tmp_path):
    src = tmp_path / "100_final.xml"
    src.write_text(_MINI, encoding="utf-8")
    before = src.read_bytes()
    run_scan(resolve_docs(tmp_path), {}, _fake_matcher, _sources())
    assert src.read_bytes() == before


def test_run_scan_with_the_real_matcher(tmp_path):
    from scripts.tei.entity_matcher import build_lexicon, find_candidates

    src = tmp_path / "src"
    src.mkdir()
    (src / "100_final.xml").write_text(_MINI, encoding="utf-8")
    lexicon = build_lexicon(_write_entities(tmp_path), tmp_path / "missing_cache.json")

    report = run_scan(resolve_docs(src), lexicon, find_candidates, _sources())
    surfaces = {c["surface"] for c in report["candidates"] if c["tier"] == 1}
    assert {"Karl Jaspers", "Jeanne Hersch"} <= surfaces
    assert report["totals"]["candidates"] == len(report["candidates"])
    assert all(c["doc"] == "100" for c in report["candidates"])


# --- CLI ------------------------------------------------------------------------

def test_main_writes_the_report_and_prints_ascii(tmp_path, monkeypatch, capsys):
    src = tmp_path / "src"
    src.mkdir()
    # non-ASCII label and surface: the summary must survive the Windows console
    (src / "100_final.xml").write_text(
        _MINI.replace("Karl Jaspers", "Karl Müller"), encoding="utf-8")
    entities = tmp_path / "entities.json"
    entities.write_text(
        json.dumps({"persons": [{"GND_id": "TEST-0001", "name": "Müller, Karl"}],
                    "organisations": [], "works": []}),
        encoding="utf-8",
    )
    out = tmp_path / "audits" / "entity_corpus_scan.json"
    monkeypatch.setattr("sys.argv", [
        "entity_corpus_scan", "--all",
        "--src-dir", str(src), "--entities", str(entities),
        "--cache", str(tmp_path / "missing_cache.json"),
        "--legacy", str(tmp_path / "missing_legacy.json"),
        "--out", str(out),
    ])

    main()  # diagnosis instrument: returns, never exits non-zero

    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["generated_from"]["code"] == "entity_matcher"
    assert payload["generated_from"]["legacy"] is None
    assert list(payload["by_doc"]) == ["100"]
    assert payload["by_entity_top"] == [["TEST-0001", "Müller, Karl", 1]]  # report keeps unicode
    captured = capsys.readouterr().out
    captured.encode("ascii")  # Windows console safety: no unicode in print output
    assert "TEST-0001" in captured


def test_main_scans_only_the_requested_documents(tmp_path, monkeypatch):
    src = tmp_path / "src"
    src.mkdir()
    for doc in ("100", "290"):
        (src / f"{doc}_final.xml").write_text(_MINI, encoding="utf-8")
    out = tmp_path / "scan.json"
    monkeypatch.setattr("sys.argv", [
        "entity_corpus_scan", "--docs", "290",
        "--src-dir", str(src), "--entities", str(_write_entities(tmp_path)),
        "--cache", str(tmp_path / "missing_cache.json"),
        "--legacy", str(tmp_path / "missing_legacy.json"),
        "--out", str(out),
    ])

    main()

    assert list(json.loads(out.read_text(encoding="utf-8"))["by_doc"]) == ["290"]
