"""Tests for the unlisted-name scan (scripts/eval/entity_unlisted_scan).

The scan is the proposal channel for list extensions: it collects name-shaped surfaces
OUTSIDE the curated entity list with frequency, documents and contexts, and it never
assigns a GND id. Curation and id assignment stay with ZBZ.

All fixtures are synthetic mini TEIs and a tiny entity list in tmp_path. No test reads
output/, none touches the network, and the real corpus run is an operator step outside
the suite. GND ids in the fixtures are placeholders; real ids come from the curated
list only.
"""

from __future__ import annotations

import csv
import json

from scripts.eval.entity_unlisted_scan import (
    CLASS_CAPS,
    CLASS_MULTI,
    CLASS_SINGLE,
    CLASSES,
    DEFAULT_MIN_MULTI,
    DEFAULT_MIN_SINGLE,
    MAX_EXAMPLES,
    aggregate,
    build_report,
    find_unlisted,
    load_languages,
    main,
    run_scan,
    scan_document,
    single_words_allowed,
    write_csv,
)

# --- fixtures ---------------------------------------------------------------

_ENTITIES = {
    "persons": [
        {"GND_id": "TEST-0001", "name": "Jaspers, Karl"},
        {"GND_id": "TEST-0002", "name": "Hersch, Jeanne"},
        {"GND_id": "TEST-0003", "name": "Mayer, Karl"},
    ],
    "organisations": [],
    "works": [],
}


def _tei(body: str) -> str:
    """Mini TEI; the header carries a name that must never reach the report."""
    return (
        '<TEI xmlns="http://www.tei-c.org/ns/1.0">'
        "<teiHeader><fileDesc><titleStmt><title>Yehuda Amichai</title>"
        "</titleStmt></fileDesc></teiHeader>"
        '<text><body><div type="text">' + body + "</div></body></text></TEI>"
    )


def _lexicon(tmp_path):
    from scripts.tei.entity_matcher import build_lexicon

    path = tmp_path / "entities.json"
    path.write_text(json.dumps(_ENTITIES), encoding="utf-8")
    return build_lexicon(path, tmp_path / "missing_cache.json")


def _found(body, tmp_path, allow_single_words=False):
    """Occurrences of one synthetic body, run through the real matcher."""
    from scripts.tei.entity_matcher import find_candidates

    return find_unlisted(_tei(body), _lexicon(tmp_path), find_candidates,
                         allow_single_words=allow_single_words)


def _surfaces(occurrences):
    return [occ["surface"] for occ in occurrences]


def _occ(surface="Hilde Domin", doc="1540", cls=CLASS_MULTI, words=2, start=0,
         context=None, overlap=False):
    return {
        "doc": doc,
        "surface": surface,
        "class": cls,
        "words": words,
        "start": start,
        "context": surface if context is None else context,
        "known_surname_overlap": overlap,
    }


# --- detection: multi-word ---------------------------------------------------

def test_multi_word_name_is_found(tmp_path):
    found = _found("<p>Dazu schrieb Hilde Domin einen Brief.</p>", tmp_path)
    assert "Hilde Domin" in _surfaces(found)
    hit = next(occ for occ in found if occ["surface"] == "Hilde Domin")
    assert hit["class"] == CLASS_MULTI
    assert hit["words"] == 2
    assert "Hilde Domin" in hit["context"]


def test_particle_stays_inside_the_surface(tmp_path):
    found = _found("<p>Ein Text von Simone de Beauvoir und Gustave Le Bon.</p>", tmp_path)
    assert "Simone de Beauvoir" in _surfaces(found)
    assert "Gustave Le Bon" in _surfaces(found)


def test_particle_before_a_two_name_tail_breaks_the_run(tmp_path):
    # "das Buch von Hilde Domin": the German noun keeps its own run, the name its own
    found = _surfaces(_found("<p>Ein Buch von Hilde Domin.</p>", tmp_path))
    assert "Hilde Domin" in found
    assert "Buch von Hilde Domin" not in found


def test_secondary_particle_binds_only_behind_another_particle(tmp_path):
    assert "Johannes van der Waals" in _surfaces(
        _found("<p>Text von Johannes van der Waals.</p>", tmp_path))
    # the bare German article carries genitive prose, not a name
    assert _found("<p>Ueber Arten der Treue.</p>", tmp_path) == []


def test_elided_particle_joins_without_a_space(tmp_path):
    assert "Jean d'Alembert" in _surfaces(_found("<p>Zitiert nach Jean d'Alembert.</p>", tmp_path))


def test_initial_plus_name_is_found(tmp_path):
    assert "W. James" in _surfaces(_found("<p>Nach W. James kam die Wende.</p>", tmp_path))


def test_lowercase_abbreviation_is_no_initial(tmp_path):
    found = _found("<p>selon Royce u. a.</p>", tmp_path, allow_single_words=True)
    assert _surfaces(found) == ["Royce"]


def test_run_longer_than_four_names_is_dropped(tmp_path):
    found = _found("<p>selon Alfred Bernard Charles Daniel Ernest.</p>", tmp_path,
                   allow_single_words=True)
    assert found == []


def test_hyphenated_forename_keeps_the_whole_surface(tmp_path):
    assert "Jean-Paul Sartre" in _surfaces(_found("<p>Text von Jean-Paul Sartre.</p>", tmp_path))


# --- detection: exclusion zones ----------------------------------------------

def test_known_candidate_span_is_excluded(tmp_path):
    found = _surfaces(_found("<p>Dazu schrieb Karl Jaspers einen Brief.</p>", tmp_path))
    assert "Karl Jaspers" not in found
    assert "Jaspers" not in found


def test_reported_names_are_trimmed_off_a_longer_run(tmp_path):
    found = _found("<p>selon Karl Jaspers Bradley.</p>", tmp_path, allow_single_words=True)
    assert _surfaces(found) == ["Bradley"]


def test_header_and_bibliography_are_excluded_while_figures_are_scanned(tmp_path):
    # figure zones joined the scan scope with the ":in-figure" demotion; the
    # unlisted channel reads them on purpose, plate captions carry unlisted names
    body = (
        "<figure><figDesc>Foto von Jurek Becker</figDesc></figure>"
        '<div type="bibliography"><bibl>Hilde Domin, Gedichte</bibl></div>'
    )
    found = _found(body, tmp_path, allow_single_words=True)
    assert "Jurek Becker" in {f["surface"] for f in found}
    assert not any("Domin" in f["surface"] for f in found)


def test_marked_entity_element_is_excluded(tmp_path):
    body = '<p>Dazu schrieb <persName ref="GND:TEST-0009">Hilde Domin</persName>.</p>'
    assert _found(body, tmp_path) == []


# --- detection: single words -------------------------------------------------

def test_single_words_appear_only_outside_german(tmp_path):
    body = "<p>selon Bradley et Royce.</p>"
    assert _found(body, tmp_path, allow_single_words=False) == []
    found = _found(body, tmp_path, allow_single_words=True)
    assert set(_surfaces(found)) == {"Bradley", "Royce"}
    assert all(occ["class"] == CLASS_SINGLE and occ["words"] == 1 for occ in found)


def test_sentence_initial_single_word_is_dropped(tmp_path):
    found = _found("<p>Er las Bradley. Bradley war wichtig.</p>", tmp_path,
                   allow_single_words=True)
    assert _surfaces(found) == ["Bradley"]


def test_short_single_word_is_dropped(tmp_path):
    found = _found("<p>selon Ada et Royce.</p>", tmp_path, allow_single_words=True)
    assert _surfaces(found) == ["Royce"]


# --- detection: caps class ---------------------------------------------------

def test_caps_sequence_gets_its_own_class(tmp_path):
    found = _found("<p>Der Beitrag von YEHUDA AMICHAI.</p>", tmp_path)
    hit = next(occ for occ in found if occ["surface"] == "YEHUDA AMICHAI")
    assert hit["class"] == CLASS_CAPS


def test_known_caps_form_is_not_reported(tmp_path):
    assert "JEANNE HERSCH" not in _surfaces(
        _found("<p>Ein Vortrag von JEANNE HERSCH.</p>", tmp_path))


# --- detection: known surname overlap ----------------------------------------

def test_known_surname_overlap_is_flagged(tmp_path):
    found = _found("<p>Auch Hans Mayer war dabei.</p>", tmp_path)
    hit = next(occ for occ in found if occ["surface"] == "Hans Mayer")
    assert hit["known_surname_overlap"] is True


def test_unknown_surname_is_not_flagged(tmp_path):
    found = _found("<p>Dazu schrieb Hilde Domin einen Brief.</p>", tmp_path)
    hit = next(occ for occ in found if occ["surface"] == "Hilde Domin")
    assert hit["known_surname_overlap"] is False


# --- language rule -----------------------------------------------------------

def test_single_words_allowed_only_for_a_known_non_german_language():
    assert single_words_allowed("FR") is True
    assert single_words_allowed("ENG/FRA") is True
    assert single_words_allowed("DE") is False
    assert single_words_allowed("DE/FR") is False
    assert single_words_allowed("FRA/DEU/ITA") is False
    assert single_words_allowed("?") is False
    assert single_words_allowed(None) is False


def test_load_languages_reads_the_catalog(tmp_path):
    catalog = tmp_path / "catalog.json"
    catalog.write_text(json.dumps({"documents": [
        {"id": "1350", "lang": "FR"}, {"id": "1540", "lang": "DE"}]}), encoding="utf-8")
    assert load_languages(catalog) == {"1350": "FR", "1540": "DE"}
    assert load_languages(tmp_path / "missing.json") == {}


# --- aggregation -------------------------------------------------------------

def test_aggregate_counts_documents_and_examples():
    occurrences = [
        _occ(doc="1540", context="ctx a"),
        _occ(doc="1540", context="ctx b"),
        _occ(doc="100", context="ctx c"),
        _occ(doc="100", context="ctx d"),
    ]
    entry = aggregate(occurrences)[0]
    assert entry["count"] == 4
    assert entry["docs"] == ["100", "1540"]
    assert entry["examples"] == ["ctx a", "ctx b", "ctx c"]
    assert len(entry["examples"]) == MAX_EXAMPLES


def test_aggregate_orders_by_count_then_alphabetically():
    occurrences = [
        _occ(surface="Bbb Ccc"), _occ(surface="Aaa Bbb"), _occ(surface="Aaa Bbb"),
        _occ(surface="Aaa Ccc"),
    ]
    assert [e["surface"] for e in aggregate(occurrences)] == [
        "Aaa Bbb", "Aaa Ccc", "Bbb Ccc"]


def test_min_count_defaults_differ_by_word_count():
    assert DEFAULT_MIN_SINGLE == 2
    assert DEFAULT_MIN_MULTI == 1
    single_once = [_occ(surface="Royce", cls=CLASS_SINGLE, words=1)]
    assert aggregate(single_once) == []
    assert aggregate(single_once * 2)[0]["count"] == 2
    assert aggregate([_occ()])[0]["surface"] == "Hilde Domin"


def test_min_count_override_applies_to_every_class():
    occurrences = [_occ(surface="Royce", cls=CLASS_SINGLE, words=1), _occ()]
    assert [e["surface"] for e in aggregate(occurrences, min_single=1, min_multi=1)] == [
        "Hilde Domin", "Royce"]
    assert aggregate(occurrences, min_single=2, min_multi=2) == []


def test_overlap_flag_survives_aggregation():
    entry = aggregate([_occ(surface="Hans Mayer"),
                       _occ(surface="Hans Mayer", overlap=True)])[0]
    assert entry["known_surname_overlap"] is True


# --- report ------------------------------------------------------------------

def _sources():
    return {"entities": "entities.json", "cache": None, "legacy": None, "catalog": None}


def _params():
    return {"min_count_single": DEFAULT_MIN_SINGLE, "min_count_multi": DEFAULT_MIN_MULTI}


def test_report_totals_and_by_doc():
    occurrences = [_occ(doc="1540"), _occ(doc="100", surface="Royce",
                                          cls=CLASS_SINGLE, words=1)]
    entries = aggregate(occurrences, min_single=1, min_multi=1)
    report = build_report(entries, occurrences, 2, _sources(), _params())
    assert report["totals"] == {
        "documents": 2, "entries": 2, "occurrences": 2,
        "by_class": {CLASS_MULTI: 1, CLASS_SINGLE: 1, CLASS_CAPS: 0},
    }
    assert report["by_doc"] == {"100": 1, "1540": 1}
    assert report["generated_from"] == {**_sources(), "code": "entity_matcher"}
    assert set(report["totals"]["by_class"]) == set(CLASSES)


def test_report_counts_only_surviving_entries_per_document():
    occurrences = [_occ(doc="100", surface="Royce", cls=CLASS_SINGLE, words=1),
                   _occ(doc="1540")]
    entries = aggregate(occurrences)  # the single word misses the default threshold
    report = build_report(entries, occurrences, 2, _sources(), _params())
    assert report["by_doc"] == {"1540": 1}


def test_report_carries_no_entity_id():
    occurrences = [_occ(), _occ(surface="Hans Mayer", overlap=True)]
    report = build_report(aggregate(occurrences), occurrences, 1, _sources(), _params())
    dumped = json.dumps(report, ensure_ascii=False)
    assert "gid" not in dumped
    assert "GND" not in dumped
    assert "TEST-0" not in dumped


# --- csv ---------------------------------------------------------------------

def test_csv_carries_the_documented_columns(tmp_path):
    entries = aggregate([_occ(doc="1540", context="ein Text; mit Semikolon"),
                         _occ(doc="100")], min_multi=1)
    out = tmp_path / "report.csv"
    write_csv(entries, out)
    with out.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.reader(handle, delimiter=";"))
    assert rows[0] == ["surface", "class", "count", "docs", "example"]
    assert rows[1] == ["Hilde Domin", CLASS_MULTI, "2", "100,1540", "ein Text; mit Semikolon"]


def test_csv_is_deterministic(tmp_path):
    entries = aggregate([_occ(), _occ(surface="Hans Mayer")])
    first, second = tmp_path / "a.csv", tmp_path / "b.csv"
    write_csv(entries, first)
    write_csv(entries, second)
    assert first.read_bytes() == second.read_bytes()


# --- run ---------------------------------------------------------------------

def _corpus(tmp_path):
    """Two documents: one German, one French, plus their catalog entry."""
    src = tmp_path / "src"
    src.mkdir(exist_ok=True)
    (src / "1540_final.xml").write_text(
        _tei("<p>Dazu schrieb Hilde Domin einen Brief. Auch Jurek Becker war da.</p>"),
        encoding="utf-8")
    (src / "1350_final.xml").write_text(
        _tei("<p>selon Bradley et Royce. Le monde de Royce.</p>"), encoding="utf-8")
    catalog = tmp_path / "catalog.json"
    catalog.write_text(json.dumps({"documents": [
        {"id": "1540", "lang": "DE"}, {"id": "1350", "lang": "FR"}]}), encoding="utf-8")
    return src, catalog


def _run(tmp_path):
    from scripts.eval.entity_corpus_scan import resolve_docs
    from scripts.tei.entity_matcher import find_candidates

    src, catalog = _corpus(tmp_path)
    return run_scan(resolve_docs(src), _lexicon(tmp_path), find_candidates,
                    load_languages(catalog), DEFAULT_MIN_SINGLE, DEFAULT_MIN_MULTI,
                    _sources())


def test_run_scan_aggregates_over_documents(tmp_path):
    report = _run(tmp_path)
    surfaces = {entry["surface"] for entry in report["entries"]}
    assert {"Hilde Domin", "Jurek Becker"} <= surfaces
    assert "Royce" in surfaces  # French document, twice
    assert "Bradley" not in surfaces  # French document, once: below the single default
    assert report["totals"]["documents"] == 2


def test_run_scan_is_deterministic(tmp_path):
    first = json.dumps(_run(tmp_path), ensure_ascii=False)
    second = json.dumps(_run(tmp_path), ensure_ascii=False)
    assert first == second


def test_run_scan_leaves_the_source_files_untouched(tmp_path):
    src, _ = _corpus(tmp_path)
    before = {path.name: path.read_bytes() for path in src.glob("*.xml")}
    _run(tmp_path)
    assert {path.name: path.read_bytes() for path in src.glob("*.xml")} == before


def test_scan_document_stamps_the_document_id(tmp_path):
    from scripts.tei.entity_matcher import find_candidates

    xml = _tei("<p>Dazu schrieb Hilde Domin einen Brief.</p>")
    found = scan_document("1540", xml, _lexicon(tmp_path), find_candidates, False)
    assert {occ["doc"] for occ in found} == {"1540"}


# --- CLI ---------------------------------------------------------------------

def _argv(tmp_path, src, catalog, out, *extra):
    return [
        "entity_unlisted_scan",
        "--src-dir", str(src),
        "--entities", str(tmp_path / "entities.json"),
        "--cache", str(tmp_path / "missing_cache.json"),
        "--legacy", str(tmp_path / "missing_legacy.json"),
        "--catalog", str(catalog),
        "--out", str(out),
        *extra,
    ]


def test_main_writes_json_and_csv_and_prints_ascii(tmp_path, monkeypatch, capsys):
    src, catalog = _corpus(tmp_path)
    _lexicon(tmp_path)  # writes the entity list the CLI reads
    # non-ASCII surface: the summary must survive the Windows console
    (src / "100_final.xml").write_text(
        _tei("<p>Dazu schrieb Hilde Müller einen Brief.</p>"), encoding="utf-8")
    catalog.write_text(json.dumps({"documents": [
        {"id": "1540", "lang": "DE"}, {"id": "1350", "lang": "FR"},
        {"id": "100", "lang": "DE"}]}), encoding="utf-8")
    out = tmp_path / "audits" / "entity_unlisted_report.json"
    monkeypatch.setattr("sys.argv", _argv(tmp_path, src, catalog, out))

    main()  # diagnosis instrument: returns, never exits non-zero

    payload = json.loads(out.read_text(encoding="utf-8"))
    surfaces = [entry["surface"] for entry in payload["entries"]]
    assert "Hilde Müller" in surfaces  # the report keeps unicode
    assert payload["params"] == _params()
    assert out.with_suffix(".csv").exists()
    captured = capsys.readouterr().out
    captured.encode("ascii")  # Windows console safety: no unicode in print output
    assert "Hilde Domin" in captured


def test_main_honours_min_count_and_doc_selection(tmp_path, monkeypatch):
    src, catalog = _corpus(tmp_path)
    _lexicon(tmp_path)
    out = tmp_path / "report.json"
    monkeypatch.setattr("sys.argv", _argv(tmp_path, src, catalog, out,
                                          "--docs", "1350", "--min-count", "2"))

    main()

    payload = json.loads(out.read_text(encoding="utf-8"))
    assert list(payload["by_doc"]) == ["1350"]
    assert payload["params"] == {"min_count_single": 2, "min_count_multi": 2}
