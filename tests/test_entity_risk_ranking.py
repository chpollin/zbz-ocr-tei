"""Tests for the risk ranking of the tier-1 entity marks (scripts/eval/entity_risk_ranking).

The ranking is a read-only instrument over the corpus scan snapshot: it scores every
tier-1 mark by additive risk features so the false-positive hunt can start with the
riskiest stratum. All fixtures are synthetic records and a tiny entity list; no test
reads output/, none touches the network. GND ids in the fixtures are placeholders.
"""

from __future__ import annotations

import json
import random

from scripts.eval.entity_risk_ranking import (
    ANOMALY_FEATURE,
    FEATURE_ORDER,
    HIGH_MIN,
    SNAPSHOT,
    WEIGHTS,
    anomalies_of,
    base_rule,
    build_report,
    features_of,
    is_case_tolerant_rule,
    main,
    page_of,
    pb_offsets,
    rank_marks,
    score_of,
    shared_surname_gids,
    stratum,
    surface_tokens,
)

# --- fixtures ---------------------------------------------------------------

_ENTITIES = {
    "persons": [
        {"GND_id": "TEST-0001", "name": "Mueller, Karl"},
        {"GND_id": "TEST-0002", "name": "Mueller, Anna"},
        {"GND_id": "TEST-0003", "name": "Jaspers, Karl"},
        {"GND_id": "TEST-0004", "name": "Voltaire"},
    ],
    "organisations": [{"GND_id": "TEST-0100", "orgName": "Jaspers, Verein"}],
    "works": [{"GND_id": "TEST-0200", "title": "Mueller, Roman"}],
}


def _rec(doc="100", gid="TEST-0003", surface="Karl Jaspers", start=100, tier=1,
         rule="full-name", category="person", form_source="headword", page=None):
    """One scan candidate record in the shape of entity_corpus_scan.json.

    ``page=None`` produces a record of the old schema, without the page field; the
    ranking then falls back to its own pb reading.
    """
    record = {
        "doc": doc,
        "gid": gid,
        "category": category,
        "surface": surface,
        "start": start,
        "end": start + len(surface),
        "tier": tier,
        "rule": rule,
        "alternatives": [],
        "matched_form": surface,
        "form_source": form_source,
        "context": f"... {surface} ...",
    }
    if page is not None:
        record["page"] = page
    return record


def _page_fn(doc, start):
    return 1 + start // 1000


def _no_page_fn(doc, start):
    raise AssertionError("the scan page must be used; no TEI may be read")


# --- single features --------------------------------------------------------

def test_headword_form_source_is_not_a_variant_channel():
    assert features_of(_rec(form_source="headword"), frozenset()) == []


def test_non_headword_form_source_scores_the_variant_channel():
    for source in ("cache-variant", "surname-index", "legacy", ""):
        features = features_of(_rec(form_source=source), frozenset())
        assert features == ["variant_form_source"], source


def test_caps_rules_are_the_case_tolerant_channel():
    assert is_case_tolerant_rule("caps-full-name")
    assert is_case_tolerant_rule("caps-surname")


def test_case_tolerant_classification_survives_rule_suffixes():
    assert base_rule("caps-surname:ambiguous:suspect") == "caps-surname"
    assert is_case_tolerant_rule("caps-surname:ambiguous:suspect")


def test_other_rules_are_not_the_case_tolerant_channel():
    for rule in ("full-name", "anchored-surname", "bare-surname", "org-token",
                 "org-variant", "work-variant", "initial-surname", "speaker"):
        assert not is_case_tolerant_rule(rule), rule


def test_single_token_surface_counts_tokens_without_markup():
    assert surface_tokens("Philosophie") == ["Philosophie"]
    assert surface_tokens('Universitaet <lb n="N002" />Genf') == ["Universitaet", "Genf"]
    assert "single_token_surface" in features_of(_rec(surface="Philosophie"), frozenset())
    assert "single_token_surface" not in features_of(
        _rec(surface='Universitaet <lb n="N002" />Genf'), frozenset())


def test_short_surface_measures_the_markup_free_surface():
    assert "short_surface" in features_of(_rec(surface="Kant"), frozenset())
    assert "short_surface" not in features_of(_rec(surface="Jaspers"), frozenset())
    assert "short_surface" in features_of(_rec(surface='Ka<lb n="N001" />nt'), frozenset())


def test_work_category_scores_one():
    features = features_of(_rec(category="work", surface="Von der Wahrheit"), frozenset())
    assert features == ["category_work"]


def test_shared_surname_gids_flags_only_persons_sharing_a_bare_surname():
    shared = shared_surname_gids(_ENTITIES)
    assert shared == frozenset({"TEST-0001", "TEST-0002"})
    assert "TEST-0100" not in shared and "TEST-0200" not in shared


def test_shared_surname_comparison_is_case_and_accent_folded():
    entities = {
        "persons": [
            {"GND_id": "A", "name": "Müller, Karl"},
            {"GND_id": "B", "name": "MüLLER, Anna"},
        ],
        "organisations": [],
        "works": [],
    }
    assert shared_surname_gids(entities) == frozenset({"A", "B"})


def test_shared_surname_feature_uses_the_gid_of_the_mark():
    shared = shared_surname_gids(_ENTITIES)
    assert "shared_surname_gid" in features_of(_rec(gid="TEST-0001"), shared)
    assert "shared_surname_gid" not in features_of(_rec(gid="TEST-0003"), shared)


# --- scoring and strata -----------------------------------------------------

def test_weights_cover_every_feature_in_the_fixed_order():
    assert set(FEATURE_ORDER) == set(WEIGHTS)
    assert FEATURE_ORDER[-1] == ANOMALY_FEATURE
    assert WEIGHTS[ANOMALY_FEATURE] == 99


def test_features_are_reported_in_the_fixed_order():
    shared = shared_surname_gids(_ENTITIES)
    features = features_of(
        _rec(gid="TEST-0001", surface="Mueller", category="work",
             rule="caps-surname", form_source="cache-variant"), shared)
    assert features == [name for name in FEATURE_ORDER if name in features]


def test_score_is_the_sum_of_the_feature_weights():
    shared = shared_surname_gids(_ENTITIES)
    record = _rec(gid="TEST-0001", surface="Mueller", rule="caps-surname",
                  form_source="cache-variant")
    features = features_of(record, shared)
    # variant channel 2 + caps channel 2 + single token 2 + shared surname 1
    assert score_of(features) == 7


def test_strata_boundaries():
    assert stratum(0) == "low"
    assert stratum(1) == "low"
    assert stratum(2) == "medium"
    assert stratum(3) == "medium"
    assert stratum(HIGH_MIN) == "high"
    assert stratum(99) == "high"


# --- anomalies --------------------------------------------------------------

def test_suspect_rule_in_tier_one_is_an_anomaly():
    listed = frozenset({"TEST-0003"})
    assert anomalies_of(_rec(rule="bare-surname:suspect"), listed) == ["suspect_rule_in_tier1"]


def test_suspect_rule_outside_tier_one_is_no_anomaly():
    listed = frozenset({"TEST-0003"})
    assert anomalies_of(_rec(rule="bare-surname:suspect", tier=2), listed) == []


def test_unlisted_gid_is_an_anomaly():
    assert anomalies_of(_rec(gid="TEST-9999"), frozenset({"TEST-0003"})) == ["gid_not_listed"]


def test_anomalies_lift_the_mark_into_the_high_stratum_and_are_listed_separately():
    records = [_rec(gid="TEST-9999", rule="bare-surname:suspect")]
    report = build_report(records, _ENTITIES, {}, page_fn=_page_fn)
    mark = report["marks"][0]
    assert mark["anomalies"] == ["gid_not_listed", "suspect_rule_in_tier1"]
    assert ANOMALY_FEATURE in mark["features"]
    assert mark["score"] >= WEIGHTS[ANOMALY_FEATURE]
    assert mark["stratum"] == "high"
    assert [item["case_id"] for item in report["anomalies"]] == [mark["case_id"]]


def test_clean_marks_carry_no_anomaly_key():
    report = build_report([_rec()], _ENTITIES, {}, page_fn=_page_fn)
    assert "anomalies" not in report["marks"][0]
    assert report["anomalies"] == []


# --- ranking ----------------------------------------------------------------

def test_only_tier_one_marks_are_ranked():
    records = [_rec(start=100), _rec(start=200, tier=2), _rec(start=300, tier=3)]
    ranked = rank_marks(records, frozenset(), frozenset({"TEST-0003"}), _page_fn)
    assert [mark["start"] for mark in ranked] == [100]


def test_ordering_is_score_desc_then_doc_page_surface():
    records = [
        _rec(doc="200", surface="Kant", rule="caps-surname", form_source="cache-variant"),
        _rec(doc="100", surface="Karl Jaspers"),
        _rec(doc="100", surface="Anna Jaspers"),
        _rec(doc="100", surface="Zeno Jaspers", start=5000),
    ]
    ranked = rank_marks(records, frozenset(), frozenset({"TEST-0003"}), _page_fn)
    assert [(m["doc"], m["page"], m["surface"]) for m in ranked] == [
        ("200", 1, "Kant"),
        ("100", 1, "Anna Jaspers"),
        ("100", 1, "Karl Jaspers"),
        ("100", 6, "Zeno Jaspers"),
    ]


def test_ordering_is_independent_of_the_input_order():
    records = [
        _rec(doc=doc, surface=surface, start=start, category=category)
        for doc, surface, start, category in [
            ("100", "Philosophie", 10, "work"),
            ("100", "Karl Jaspers", 20, "person"),
            ("290", "Kant", 30, "person"),
            ("290", "Karl Jaspers", 40, "person"),
            ("1520", "Von der Wahrheit", 50, "work"),
        ]
    ]
    listed = frozenset({"TEST-0003"})
    reference = rank_marks(records, frozenset(), listed, _page_fn)
    for seed in (1, 2, 3):
        shuffled = list(records)
        random.Random(seed).shuffle(shuffled)
        assert rank_marks(shuffled, frozenset(), listed, _page_fn) == reference


def test_case_ids_follow_the_risk_order():
    records = [_rec(doc="100"), _rec(doc="290", surface="Philosophie", category="work")]
    ranked = rank_marks(records, frozenset(), frozenset({"TEST-0003"}), _page_fn)
    assert [mark["case_id"] for mark in ranked] == ["f0001", "f0002"]
    assert ranked[0]["surface"] == "Philosophie"


def test_marks_carry_the_facsimile_path_of_their_page():
    ranked = rank_marks([_rec(doc="760", start=17_000)], frozenset(),
                        frozenset({"TEST-0003"}), _page_fn)
    assert ranked[0]["page"] == 18
    assert ranked[0]["facsimile"] == "docs/images/760/760_p018.png"


def test_unresolved_page_stays_null():
    ranked = rank_marks([_rec()], frozenset(), frozenset({"TEST-0003"}),
                        lambda doc, start: None)
    assert ranked[0]["page"] is None
    assert ranked[0]["facsimile"] is None


# --- page assignment --------------------------------------------------------

_MINI = (
    '<TEI xmlns="http://www.tei-c.org/ns/1.0"><text><body><div type="text">'
    '<pb n="1" facs="#f1"/><p>Karl Jaspers.</p>'
    '<pb n="2" facs="#f2"/><p>Jeanne Hersch.</p>'
    "</div></body></text></TEI>"
)


def test_page_of_counts_the_pb_elements_of_the_body():
    starts = pb_offsets(_MINI)
    assert len(starts) == 2
    assert page_of(starts, starts[0] - 1) == 1  # before the first pb
    assert page_of(starts, _MINI.index("Karl Jaspers")) == 1
    assert page_of(starts, _MINI.index("Jeanne Hersch")) == 2
    assert page_of([], 500) == 1


def test_the_scan_page_wins_and_no_tei_is_read():
    """The snapshot is the single source of the page number once it carries one."""
    ranked = rank_marks([_rec(doc="760", start=17_000, page=7)], frozenset(),
                        frozenset({"TEST-0003"}), _no_page_fn)
    assert ranked[0]["page"] == 7
    assert ranked[0]["facsimile"] == "docs/images/760/760_p007.png"


def test_a_scan_without_the_page_field_falls_back_to_the_pb_reading():
    """Old snapshots stay usable: the field is absent, the ranking reads the TEI."""
    record = _rec(doc="760", start=17_000)
    assert "page" not in record
    ranked = rank_marks([record], frozenset(), frozenset({"TEST-0003"}), _page_fn)
    assert ranked[0]["page"] == 18


def test_the_fallback_is_used_per_record():
    """A mixed snapshot resolves each mark from its own source."""
    records = [_rec(doc="100", start=3_000, page=2),
               _rec(doc="100", surface="Anna Jaspers", start=3_000)]
    ranked = rank_marks(records, frozenset(), frozenset({"TEST-0003"}), _page_fn)
    assert {mark["surface"]: mark["page"] for mark in ranked} == {
        "Karl Jaspers": 2, "Anna Jaspers": 4
    }


# --- report and CLI ---------------------------------------------------------

def test_report_shape_is_deterministic_and_carries_no_timestamp():
    records = [_rec(doc="100"), _rec(doc="290", surface="Philosophie", category="work"),
               _rec(doc="290", surface="Mueller", gid="TEST-0001",
                    form_source="cache-variant", rule="caps-surname")]
    sources = {"scan": "scan.json", "entities": "entities.json", "tei_dir": "tei_final"}
    report = build_report(records, _ENTITIES, sources, page_fn=_page_fn)
    assert report["snapshot"] == SNAPSHOT
    assert report["source"] == sources
    assert set(report) == {"snapshot", "source", "feature_doc", "strata_counts",
                           "anomalies", "marks"}
    assert sum(report["strata_counts"].values()) == len(report["marks"])
    assert list(report["strata_counts"]) == ["high", "medium", "low"]
    assert report["feature_doc"]["weights"] == WEIGHTS
    assert build_report(records, _ENTITIES, sources, page_fn=_page_fn) == report


def test_feature_doc_names_the_case_tolerant_rule_strings():
    report = build_report([_rec()], _ENTITIES, {}, page_fn=_page_fn)
    documented = report["feature_doc"]["case_tolerant_rules"]
    assert "caps-full-name" in documented["treated_as_case_tolerant"]
    assert "caps-surname" in documented["treated_as_case_tolerant"]
    assert documented["excluded"]  # the exclusions are stated, not silent


def test_main_writes_the_ranking_and_prints_ascii(tmp_path, monkeypatch, capsys):
    src = tmp_path / "tei"
    src.mkdir()
    (src / "100_final.xml").write_text(_MINI, encoding="utf-8")
    scan = tmp_path / "scan.json"
    scan.write_text(json.dumps({"candidates": [
        _rec(doc="100", surface="Müller", gid="TEST-0001", rule="caps-surname",
             form_source="cache-variant", start=_MINI.index("Karl Jaspers")),
        _rec(doc="100", start=_MINI.index("Jeanne Hersch"), tier=2),
    ]}, ensure_ascii=False), encoding="utf-8")
    entities = tmp_path / "entities.json"
    entities.write_text(json.dumps(_ENTITIES, ensure_ascii=False), encoding="utf-8")
    out = tmp_path / "fp_hunt" / "risk_ranking.json"
    monkeypatch.setattr("sys.argv", [
        "entity_risk_ranking", "--scan", str(scan), "--entities", str(entities),
        "--tei-dir", str(src), "--out", str(out),
    ])

    main()  # diagnosis instrument: returns, never exits non-zero

    payload = json.loads(out.read_text(encoding="utf-8"))
    assert [mark["surface"] for mark in payload["marks"]] == ["Müller"]
    assert payload["marks"][0]["page"] == 1
    assert payload["strata_counts"]["high"] == 1
    captured = capsys.readouterr().out
    captured.encode("ascii")  # Windows console safety: no unicode in print output
    assert "high" in captured


def test_main_takes_the_page_from_the_scan_without_reading_tei(tmp_path, monkeypatch):
    """With the page in the snapshot the ranking needs no TEI directory at all."""
    scan = tmp_path / "scan.json"
    scan.write_text(json.dumps({"candidates": [
        _rec(doc="100", start=4_000, page=3),
        _rec(doc="100", surface="Jeanne Hersch", start=9_000, tier=2, page=8),
    ]}, ensure_ascii=False), encoding="utf-8")
    entities = tmp_path / "entities.json"
    entities.write_text(json.dumps(_ENTITIES, ensure_ascii=False), encoding="utf-8")
    out = tmp_path / "fp_hunt" / "risk_ranking.json"
    monkeypatch.setattr("sys.argv", [
        "entity_risk_ranking", "--scan", str(scan), "--entities", str(entities),
        "--tei-dir", str(tmp_path / "no_such_tei"), "--out", str(out),
    ])

    main()

    payload = json.loads(out.read_text(encoding="utf-8"))
    assert [(mark["surface"], mark["page"]) for mark in payload["marks"]] == [
        ("Karl Jaspers", 3)
    ]
    assert payload["marks"][0]["facsimile"] == "docs/images/100/100_p003.png"
