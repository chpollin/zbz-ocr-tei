"""Tests for the M4 gold benchmark (scripts/eval/entity_gold_benchmark).

The benchmark scores the matcher against the ZBZ reference TEIs, restricted to the
text both sides share, and is a read-only diagnosis instrument.

All fixtures are synthetic mini pairs (reference TEI plus pipeline TEI) in tmp_path
with a tiny entity list. No test reads data/source or output/, none touches the
network, and the real corpus run is an operator step outside the suite. Every GND id
in the fixtures is copied from data/entities/all_entities.json; none is invented.
"""

from __future__ import annotations

import json

from scripts.eval.entity_gold_benchmark import (
    AUTHOR_GID,
    SPECIAL_DOC,
    benchmark_document,
    build_report,
    build_stream,
    legacy_indexed_docs,
    main,
    normalize_reference_gid,
    reference_mentions,
    shared_regions,
    split_of,
    surface_text,
)

# --- fixtures ---------------------------------------------------------------

# Ids read from data/entities/all_entities.json (curated list, never invented).
JASPERS = "118557106"          # Jaspers, Karl
HERSCH = "118815679"           # Hersch, Jeanne (the corpus author)
SARTRE = "11860564X"           # Sartre, Jean-Paul
PSYCHOPATHOLOGIE = "4558181-2"  # Allgemeine Psychopathologie
GERTRUD = "117085391"          # Jaspers, Gertrud: listed, but kept out of the mini lexicon

_ENTITIES = {
    "persons": [
        {"GND_id": JASPERS, "name": "Jaspers, Karl"},
        {"GND_id": HERSCH, "name": "Hersch, Jeanne"},
        {"GND_id": SARTRE, "name": "Sartre, Jean-Paul"},
    ],
    "organisations": [],
    "works": [{"GND_id": PSYCHOPATHOLOGIE, "title": "Allgemeine Psychopathologie"}],
}

SHARED = ("Im Sommer sprach der Redner in Basel ueber die Grenzen der Vernunft "
          "und die Freiheit des Menschen.")
SECOND_PAGE = ("Auf der zweiten Seite erwaehnt der Verfasser erneut {mention} und "
               "dessen spaete Schriften ueber Wahrheit und Verantwortung.")


def _tei(body: str) -> str:
    return ('<TEI xmlns="http://www.tei-c.org/ns/1.0"><teiHeader/><text><body>'
            f'<div type="text">{body}</div></body></text></TEI>')


def _persname(gid: str, surface: str) -> str:
    return f'<persName ref="GND:{gid}">{surface}</persName>'


def _finder(tmp_path):
    """The real matcher, bound to the mini entity list (no cache, no legacy index)."""
    from scripts.tei.entity_matcher import build_lexicon, find_candidates

    path = tmp_path / "entities.json"
    path.write_text(json.dumps(_ENTITIES), encoding="utf-8")
    lexicon = build_lexicon(path, tmp_path / "missing_cache.json")

    def find(xml_string):
        return find_candidates(xml_string, lexicon)

    return find, set(lexicon["entries"])


def _run(tmp_path, ref_body: str, pipe_body: str, doc: str = "100") -> dict:
    find, known = _finder(tmp_path)
    return benchmark_document(doc, _tei(ref_body), _tei(pipe_body), find, known_gids=known)


def _counts(result: dict) -> dict:
    return result["counts"]


def _verdicts(result: dict, verdict: str) -> list[dict]:
    return [r for r in result["records"] if r["verdict"] == verdict]


# --- reference extraction ----------------------------------------------------

def test_reference_mentions_carry_gid_category_and_document_order():
    xml = _tei(
        f"<p>Im Sommer sprach {_persname(JASPERS, 'Karl Jaspers')} ueber "
        f'<bibl ref="GND:{PSYCHOPATHOLOGIE}">Allgemeine Psychopathologie</bibl>.</p>'
    )
    mentions = reference_mentions(xml)
    assert [(m["gid"], m["category"]) for m in mentions] == [
        (JASPERS, "person"), (PSYCHOPATHOLOGIE, "work"),
    ]
    assert [m["surface"] for m in mentions] == ["Karl Jaspers", "Allgemeine Psychopathologie"]
    assert [m["order"] for m in mentions] == [0, 1]


def test_reference_mentions_take_bibl_corresp_and_a_missing_gnd_prefix():
    xml = _tei(
        f'<p>Erwaehnt sind <bibl corresp="GND:{PSYCHOPATHOLOGIE}">Allgemeine '
        f'Psychopathologie</bibl> und <persName ref="{JASPERS}">Karl Jaspers</persName>.</p>'
    )
    assert [m["gid"] for m in reference_mentions(xml)] == [PSYCHOPATHOLOGIE, JASPERS]


def test_reference_mentions_ignore_a_non_gnd_reference():
    xml = _tei('<p>Siehe <bibl ref="https://swisscovery.example/x">die Uebersetzung</bibl>.</p>')
    assert reference_mentions(xml) == []


def test_normalize_reference_gid_strips_prefix_and_whitespace():
    assert normalize_reference_gid("GND:\t\n  10182087-2") == "10182087-2"
    assert normalize_reference_gid(f"GND:{JASPERS}") == JASPERS
    assert normalize_reference_gid("https://d-nb.info/gnd/118557106") is None


def test_broken_reference_file_is_reported_instead_of_crashing(tmp_path):
    find, known = _finder(tmp_path)
    broken = '<TEI xmlns="http://www.tei-c.org/ns/1.0"><text><body><p>offen</body></text></TEI>'
    result = benchmark_document("1520", broken, _tei("<p>offen</p>"), find, known_gids=known)
    assert result["status"] == "unreadable"
    assert result["error"]
    assert result["counts"]["hit"] == 0


# --- text stream -------------------------------------------------------------

def test_stream_joins_a_word_broken_by_lb_break_no():
    xml = _tei('<p>Hu<lb break="no"/>\n\t\t\tmanismus als Programm</p>')
    assert [t.word for t in build_stream(xml)] == ["humanismus", "als", "programm"]


def test_stream_treats_a_plain_lb_as_a_word_boundary():
    xml = _tei('<p>Grenzen<lb/>der Vernunft</p>')
    assert [t.word for t in build_stream(xml)] == ["grenzen", "der", "vernunft"]


def test_stream_offsets_point_back_into_the_raw_string():
    xml = _tei("<p>Karl Jaspers</p>")
    tokens = build_stream(xml)
    assert [xml[t.start:t.end] for t in tokens] == ["Karl", "Jaspers"]


def test_stream_stays_inside_the_text_element():
    xml = ('<TEI xmlns="http://www.tei-c.org/ns/1.0"><teiHeader><title>Kopfdaten</title>'
           "</teiHeader><text><body><p>Vernunft</p></body></text></TEI>")
    assert [t.word for t in build_stream(xml)] == ["vernunft"]


def test_surface_text_normalizes_markup_and_line_breaks():
    assert surface_text('Karl<lb break="no"/>\n  Jaspers') == "KarlJaspers"
    assert surface_text('<hi rendition="#i">Allgemeine</hi> Psychopathologie') == (
        "Allgemeine Psychopathologie")


# --- alignment ---------------------------------------------------------------

def test_shared_regions_pair_the_common_word_blocks():
    words = SHARED.lower().split()
    regions = shared_regions(words, words)
    assert len(regions) == 1
    assert regions[0].ref_start == 0
    assert regions[0].ref_end == len(words)


def test_shared_regions_drop_an_accidental_short_block():
    regions = shared_regions(["und"], ["und"] + [f"w{i}" for i in range(40)])
    assert regions == []


# --- scoring -----------------------------------------------------------------

def test_hit_when_the_pipeline_marks_the_same_mention(tmp_path):
    ref = (f"<p>Im Sommer sprach {_persname(JASPERS, 'Karl Jaspers')} in Basel ueber "
           "die Grenzen.</p>")
    pipe = "<p>Im Sommer sprach Karl Jaspers in Basel ueber die Grenzen.</p>"
    result = _run(tmp_path, ref, pipe)
    assert _counts(result)["hit"] == 1
    assert _counts(result)["miss"] == 0
    assert _counts(result)["false_positive"] == 0
    assert _verdicts(result, "hit")[0]["rule"] == "full-name"


def test_miss_when_neither_tier_reaches_the_mention(tmp_path):
    # the pipeline text carries an OCR-corrupted spelling no lexicon form reaches;
    # a figure caption no longer works as the unreachable place (":in-figure" scans)
    ref = (f"<p>Im Sommer sprach {_persname(JASPERS, 'Karl Jaspers')} in Basel ueber die "
           "Grenzen der Vernunft.</p>"
           f"<p>Im Herbst kehrte {_persname(JASPERS, 'Karl Jaspers')} nach Basel "
           "zurueck und sprach erneut.</p>")
    pipe = ("<p>Im Sommer sprach Karl Jaspers in Basel ueber die Grenzen der Vernunft.</p>"
            "<p>Im Herbst kehrte Karl Jaspars nach Basel zurueck und sprach erneut.</p>")
    result = _run(tmp_path, ref, pipe)
    assert _counts(result)["hit"] == 1
    assert _counts(result)["miss"] == 1
    assert _verdicts(result, "miss")[0]["gid"] == JASPERS


def test_worklist_available_is_its_own_class_with_the_rule(tmp_path):
    ref = (f"<p>Die Vorlesung von {_persname(JASPERS, 'Jaspers')} in Basel behandelte die "
           "Grenzen der Vernunft und die Freiheit des Menschen.</p>")
    pipe = ("<p>Die Vorlesung von Jaspers in Basel behandelte die Grenzen der Vernunft "
            "und die Freiheit des Menschen.</p>")
    result = _run(tmp_path, ref, pipe)
    assert _counts(result)["worklist_available"] == 1
    assert _counts(result)["miss"] == 0
    assert _verdicts(result, "worklist_available")[0]["rule"] == "bare-surname"
    assert _verdicts(result, "worklist_available")[0]["tier"] == 2


def test_an_ambiguous_surname_counts_as_worklist_not_as_miss(tmp_path):
    """Both Jaspers spouses are listed, so the matcher reports one id and defers the choice."""
    from scripts.eval.entity_gold_benchmark import candidate_alternatives
    from scripts.tei.entity_matcher import build_lexicon, find_candidates

    entities = dict(_ENTITIES, persons=[*_ENTITIES["persons"],
                                        {"GND_id": GERTRUD, "name": "Jaspers, Gertrud"}])
    path = tmp_path / "entities.json"
    path.write_text(json.dumps(entities), encoding="utf-8")
    lexicon = build_lexicon(path, tmp_path / "missing_cache.json")
    ref = (f"<p>Die Vorlesung von {_persname(JASPERS, 'Jaspers')} in Basel behandelte die "
           "Grenzen der Vernunft und die Freiheit des Menschen.</p>")
    pipe = ("<p>Die Vorlesung von Jaspers in Basel behandelte die Grenzen der Vernunft "
            "und die Freiheit des Menschen.</p>")

    result = benchmark_document(
        "100", _tei(ref), _tei(pipe), lambda xml: find_candidates(xml, lexicon),
        known_gids=set(lexicon["entries"]),
        alternatives=lambda surface: candidate_alternatives(lexicon, surface),
    )

    assert _counts(result)["worklist_available"] == 1
    assert _counts(result)["miss"] == 0
    record = _verdicts(result, "worklist_available")[0]
    assert record["resolved_by"] == "alternative_id"
    assert record["reference_gid"] == JASPERS
    assert record["gid"] == GERTRUD  # the matcher reports the first owner of the form


def test_false_positive_for_a_tier1_candidate_without_reference_counterpart(tmp_path):
    body = ("<p>Im Sommer sprach Jean-Paul Sartre in Basel ueber die Grenzen der Vernunft "
            "und die Freiheit.</p>")
    result = _run(tmp_path, body, body)
    assert _counts(result)["false_positive"] == 1
    assert _verdicts(result, "false_positive")[0]["gid"] == SARTRE


def test_author_mentions_are_counted_apart_from_the_main_precision(tmp_path):
    ref = (f"<p>Im Sommer sprach {_persname(JASPERS, 'Karl Jaspers')} mit Jeanne Hersch "
           "ueber die Grenzen der Vernunft und die Freiheit.</p>")
    pipe = ("<p>Im Sommer sprach Karl Jaspers mit Jeanne Hersch ueber die Grenzen der "
            "Vernunft und die Freiheit.</p>")
    result = _run(tmp_path, ref, pipe)
    assert _counts(result)["fp_author"] == 1
    assert _counts(result)["false_positive"] == 0
    assert _verdicts(result, "fp_author")[0]["gid"] == AUTHOR_GID
    report = build_report([result], _sources())
    assert report["totals"]["precision_tier1"] == 1.0
    assert report["totals"]["author_false_positives"] == 1


def test_reference_pages_the_pipeline_lacks_stay_neutral(tmp_path):
    ref = (f"<p>{SHARED}</p><pb n=\"2\"/><p>"
           + SECOND_PAGE.format(mention=_persname(JASPERS, "Karl Jaspers")) + "</p>")
    pipe = f"<p>{SHARED}</p>"
    result = _run(tmp_path, ref, pipe)
    assert _counts(result)["neutral_out_of_scope"] == 1
    assert _counts(result)["miss"] == 0


def test_pipeline_pages_the_reference_lacks_stay_neutral(tmp_path):
    ref = f"<p>{SHARED}</p>"
    pipe = (f"<p>{SHARED}</p><pb n=\"2\"/><p>"
            + SECOND_PAGE.format(mention="Karl Jaspers") + "</p>")
    result = _run(tmp_path, ref, pipe)
    assert _counts(result)["neutral_out_of_scope_candidate"] == 1
    assert _counts(result)["false_positive"] == 0


def _wide_citation(marked: bool) -> str:
    citation = "Karl Jaspers, Allgemeine Psychopathologie, Berlin 1913"
    inner = (f'<bibl ref="GND:{PSYCHOPATHOLOGIE}">{citation}</bibl>' if marked else citation)
    return (f"<p>Im Sommer erschien {inner} in neuer Auflage und wurde in Basel "
            "viel gelesen.</p>")


def test_a_wide_reference_citation_span_scores_neutral(tmp_path):
    result = _run(tmp_path, _wide_citation(True), _wide_citation(False))
    assert _counts(result)["neutral_wide_span"] == 1
    assert _counts(result)["miss"] == 0
    assert _verdicts(result, "neutral_wide_span")[0]["gid"] == PSYCHOPATHOLOGIE


def test_a_candidate_nested_in_a_reference_span_scores_neutral(tmp_path):
    result = _run(tmp_path, _wide_citation(True), _wide_citation(False))
    assert _counts(result)["neutral_nested"] == 1
    assert _counts(result)["false_positive"] == 0
    assert _verdicts(result, "neutral_nested")[0]["gid"] == JASPERS


def test_a_reference_gid_outside_the_lexicon_is_no_miss(tmp_path):
    ref = (f"<p>Im Sommer sprach {_persname(GERTRUD, 'Gertrud Jaspers')} in Basel ueber "
           "die Grenzen der Vernunft und die Freiheit.</p>")
    pipe = ("<p>Im Sommer sprach Gertrud Jaspers in Basel ueber die Grenzen der Vernunft "
            "und die Freiheit.</p>")
    result = _run(tmp_path, ref, pipe)
    assert _counts(result)["neutral_unlisted"] == 1
    assert _counts(result)["miss"] == 0


def test_missing_pipeline_tei_is_reported(tmp_path):
    find, known = _finder(tmp_path)
    result = benchmark_document("100", _tei("<p>Vernunft</p>"), None, find, known_gids=known)
    assert result["status"] == "no_pipeline"


# --- splits ------------------------------------------------------------------

def _sources() -> dict:
    return {"entities": "entities.json", "cache": None, "legacy": None,
            "reference_dir": "ref", "pipeline_dir": "pipe"}


def test_split_of_separates_dev_held_out_and_the_dense_reference():
    legacy = {"100", "290", SPECIAL_DOC}
    assert split_of("100", legacy) == "dev"
    assert split_of("760", legacy) == "held_out"
    assert split_of(SPECIAL_DOC, legacy) == f"special_{SPECIAL_DOC}"


def test_legacy_indexed_docs_reads_the_file_lists(tmp_path):
    path = tmp_path / "legacy.json"
    path.write_text(json.dumps({
        "persons": {"118557106": {"names": ["Jaspers"], "files": ["100.xml", "290.xml"]}},
        "organizations": {},
        "works": {"4558181-2": {"names": ["Psychopathologie"], "files": ["100.xml"]}},
    }), encoding="utf-8")
    assert legacy_indexed_docs(path) == {"100", "290"}
    assert legacy_indexed_docs(tmp_path / "missing.json") == set()


# --- report ------------------------------------------------------------------

def test_report_splits_metrics_and_lists_every_error(tmp_path):
    hit = _run(tmp_path, _wide_citation(True), _wide_citation(False), doc="100")
    hit["split"] = "dev"
    fp_body = ("<p>Im Sommer sprach Jean-Paul Sartre in Basel ueber die Grenzen der "
               "Vernunft und die Freiheit.</p>")
    fp = _run(tmp_path, fp_body, fp_body, doc="760")
    fp["split"] = "held_out"
    report = build_report([hit, fp], _sources())
    assert set(report["splits"]) == {"dev", "held_out"}
    assert report["splits"]["held_out"]["counts"]["false_positive"] == 1
    assert report["splits"]["held_out"]["precision_tier1"] == 0.0
    assert [r["doc"] for r in report["errors"]["false_positive"]] == ["760"]
    assert report["totals"]["counts"]["neutral_wide_span"] == 1
    assert set(report["by_category"]) <= {"person", "organisation", "work"}


def test_report_is_deterministic(tmp_path):
    result = _run(tmp_path, _wide_citation(True), _wide_citation(False))
    result["split"] = "dev"
    first = json.dumps(build_report([result], _sources()), ensure_ascii=False)
    second = json.dumps(build_report([result], _sources()), ensure_ascii=False)
    assert first == second


# --- CLI ---------------------------------------------------------------------

def _corpus(tmp_path) -> tuple:
    ref_dir, pipe_dir = tmp_path / "ref", tmp_path / "pipe"
    ref_dir.mkdir()
    pipe_dir.mkdir()
    ref = (f"<p>Im Sommer sprach {_persname(JASPERS, 'Karl Jaspers')} in Basel ueber "
           "die Grenzen.</p>")
    pipe = "<p>Im Sommer sprach Karl Jaspers in Basel ueber die Grenzen.</p>"
    for doc in ("100", "760"):
        (ref_dir / f"{doc}.xml").write_text(_tei(ref), encoding="utf-8")
        (pipe_dir / f"{doc}_final.xml").write_text(_tei(pipe), encoding="utf-8")
    entities = tmp_path / "entities.json"
    entities.write_text(json.dumps(_ENTITIES), encoding="utf-8")
    return ref_dir, pipe_dir, entities


def _argv(tmp_path, out, extra=()):
    ref_dir, pipe_dir, entities = _corpus(tmp_path)
    return ["entity_gold_benchmark", "--out", str(out),
            "--ref-dir", str(ref_dir), "--src-dir", str(pipe_dir),
            "--entities", str(entities),
            "--cache", str(tmp_path / "missing_cache.json"),
            "--legacy", str(tmp_path / "missing_legacy.json"),
            "--policy", str(tmp_path / "missing_policy.json"), *extra]


def test_main_writes_the_report_and_prints_ascii(tmp_path, monkeypatch, capsys):
    out = tmp_path / "audits" / "entity_gold_benchmark.json"
    monkeypatch.setattr("sys.argv", _argv(tmp_path, out))

    assert main() == 0

    payload = json.loads(out.read_text(encoding="utf-8"))
    assert [d["doc"] for d in payload["documents"]] == ["100", "760"]
    assert payload["totals"]["counts"]["hit"] == 2
    assert payload["totals"]["recall_tier1"] == 1.0
    captured = capsys.readouterr().out
    captured.encode("ascii")  # Windows console safety: no unicode in print output
    assert "recall" in captured.lower()


def test_main_restricts_to_the_requested_documents(tmp_path, monkeypatch):
    out = tmp_path / "benchmark.json"
    monkeypatch.setattr("sys.argv", _argv(tmp_path, out, extra=["--docs", "760"]))

    assert main() == 0

    payload = json.loads(out.read_text(encoding="utf-8"))
    assert [d["doc"] for d in payload["documents"]] == ["760"]


def test_main_leaves_the_reference_and_pipeline_files_untouched(tmp_path, monkeypatch):
    out = tmp_path / "benchmark.json"
    argv = _argv(tmp_path, out)
    before = {p: p.read_bytes() for p in tmp_path.rglob("*.xml")}
    monkeypatch.setattr("sys.argv", argv)

    main()

    assert {p: p.read_bytes() for p in tmp_path.rglob("*.xml")} == before
