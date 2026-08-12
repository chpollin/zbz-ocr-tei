"""Tests for the entity intake audit (scripts.eval.entity_lint)."""

import json

import pytest

from scripts.eval.entity_lint import (
    CACHE_PATH,
    ENTITIES_PATH,
    build_report,
    is_valid_gnd_id,
    lint,
)


def _person(gnd, name="Muster, Anna", **extra):
    entry = {
        "GND_id": gnd,
        "name": name,
        "listBibl": [{"DNB_link": f"https://d-nb.info/gnd/{gnd}"}],
        "editor_reviewed": True,
    }
    entry.update(extra)
    return entry


def _org(gnd, org_name="Musterverein", **extra):
    entry = {
        "GND_id": gnd,
        "orgName": org_name,
        "listBibl": [{"DNB_link": f"https://d-nb.info/gnd/{gnd}"}],
        "editor_reviewed": True,
    }
    entry.update(extra)
    return entry


def _work(gnd, title="Musterwerk", author=None, **extra):
    entry = {
        "GND_id": gnd,
        "title": title,
        "author_gnd_id": author,
        "listBibl": [{"DNB_link": f"https://d-nb.info/gnd/{gnd}"}],
        "editor_reviewed": True,
    }
    entry.update(extra)
    return entry


def _entities(persons=(), organisations=(), works=()):
    return {
        "persons": list(persons),
        "organisations": list(organisations),
        "works": list(works),
    }


def _types(report, key="errors"):
    return [item["type"] for item in report[key]]


# --- GND id syntax -------------------------------------------------------


@pytest.mark.parametrize(
    "value",
    ["104535342", "1150680555", "11860564X", "103153914X", "4558181-2", "5005966-X"],
)
def test_valid_gnd_ids(value):
    assert is_valid_gnd_id(value)


@pytest.mark.parametrize(
    "value",
    ["", None, "abc", "12-", "-12", "118-5-2", "11860564Y", "1186 0564", "118X5", "X"],
)
def test_invalid_gnd_ids(value):
    assert not is_valid_gnd_id(value)


def test_invalid_gnd_id_is_error():
    report = lint(_entities(persons=[_person("no-gnd")]))
    assert "invalid_gnd_id" in _types(report)


# --- labels --------------------------------------------------------------


def test_missing_label_per_category():
    entities = _entities(
        persons=[{"GND_id": "104535342", "editor_reviewed": False}],
        organisations=[_org("5005966-X", org_name=None)],
        works=[_work("4558181-2", title="   ")],
    )
    report = lint(entities)
    missing = [e for e in report["errors"] if e["type"] == "missing_label"]
    assert len(missing) == 3
    assert {e["category"] for e in missing} == {"persons", "organisations", "works"}


def test_present_label_is_clean():
    report = lint(_entities(persons=[_person("104535342")]))
    assert report["errors"] == []


# --- duplicates ----------------------------------------------------------


def test_duplicate_within_category():
    report = lint(_entities(persons=[_person("104535342"), _person("104535342")]))
    dups = [e for e in report["errors"] if e["type"] == "duplicate_gnd_id"]
    assert len(dups) == 1


def test_duplicate_across_categories():
    report = lint(
        _entities(persons=[_person("4558181-2")], works=[_work("4558181-2")])
    )
    dups = [e for e in report["errors"] if e["type"] == "duplicate_gnd_id"]
    assert len(dups) == 1
    assert dups[0]["category"] == "works"


# --- DNB link ------------------------------------------------------------


def test_dnb_link_mismatch():
    entry = _person("104535342")
    entry["listBibl"] = [{"DNB_link": "https://d-nb.info/104535342"}]
    report = lint(_entities(persons=[entry]))
    assert _types(report) == ["dnb_link_mismatch"]


def test_absent_listbibl_is_no_dnb_error():
    entry = _person("104535342")
    entry["listBibl"] = None
    report = lint(_entities(persons=[entry]))
    assert report["errors"] == []


# --- work author resolution ---------------------------------------------


def test_unresolved_author_is_error():
    report = lint(
        _entities(persons=[_person("104535342")], works=[_work("4558181-2", author="999999999")])
    )
    assert _types(report) == ["unresolved_author"]


def test_resolved_author_is_clean():
    report = lint(
        _entities(persons=[_person("104535342")], works=[_work("4558181-2", author="104535342")])
    )
    assert report["errors"] == []


def test_empty_author_is_no_error():
    report = lint(_entities(works=[_work("4558181-2", author="")]))
    assert report["errors"] == []


# --- cache checks --------------------------------------------------------


def _cache(entries):
    return {
        "retrieved": "2026-08-12",
        "source_pattern": "https://lobid.org/gnd/{id}.json",
        "entries": entries,
    }


def test_cache_404_is_error():
    report = lint(
        _entities(persons=[_person("000000", name="Test")]),
        _cache({"000000": {"http_status": 404}}),
    )
    assert _types(report) == ["gnd_not_found"]


def test_preferred_name_mismatch_is_warning():
    cache = _cache(
        {
            "104535342": {
                "http_status": 200,
                "preferred_name": "Aebi, Hugo",
                "variant_names": [],
                "types": ["Person"],
                "date_of_birth": None,
                "date_of_death": None,
                "wikidata": None,
            }
        }
    )
    report = lint(_entities(persons=[_person("104535342", name="Aebi, H.")]), cache)
    assert report["errors"] == []
    assert "preferred_name_mismatch" in _types(report, "warnings")


def test_preferred_name_match_ignores_case_and_spacing():
    cache = _cache(
        {
            "104535342": {
                "http_status": 200,
                "preferred_name": "Aebi,  hugo",
                "variant_names": [],
                "types": ["Person"],
                "date_of_birth": None,
                "date_of_death": None,
                "wikidata": None,
            }
        }
    )
    report = lint(_entities(persons=[_person("104535342", name="Aebi, Hugo")]), cache)
    assert _types(report, "warnings") == []


def test_type_mismatch_is_warning():
    cache = _cache(
        {
            "4558181-2": {
                "http_status": 200,
                "preferred_name": "Musterwerk",
                "variant_names": [],
                "types": ["SubjectHeadingSensoStricto"],
                "date_of_birth": None,
                "date_of_death": None,
                "wikidata": None,
            }
        }
    )
    report = lint(_entities(works=[_work("4558181-2")]), cache)
    assert report["errors"] == []
    assert "type_mismatch" in _types(report, "warnings")


def test_expected_type_is_no_warning():
    cache = _cache(
        {
            "104535342": {
                "http_status": 200,
                "preferred_name": "Muster, Anna",
                "variant_names": [],
                "types": ["DifferentiatedPerson", "Person"],
                "date_of_birth": None,
                "date_of_death": None,
                "wikidata": None,
            }
        }
    )
    report = lint(_entities(persons=[_person("104535342")]), cache)
    assert report["warnings"] == []


def test_missing_cache_entry_is_warning():
    report = lint(_entities(persons=[_person("104535342")]), _cache({}))
    assert "not_in_cache" in _types(report, "warnings")


def test_without_cache_only_offline_checks_run():
    report = lint(_entities(persons=[_person("104535342")]), None)
    assert report["errors"] == []
    assert report["warnings"] == []
    assert report["counts"]["cache"] is None


# --- editor_reviewed -----------------------------------------------------


def test_editor_reviewed_false_is_counted_not_listed():
    entities = _entities(
        persons=[_person("104535342", editor_reviewed=False)],
        organisations=[_org("5005966-X", editor_reviewed=True)],
    )
    report = lint(entities)
    assert report["counts"]["editor_reviewed_false"] == 1
    assert "editor_not_reviewed" not in _types(report, "warnings")


# --- report shape --------------------------------------------------------


def test_report_is_json_serializable_and_complete(tmp_path):
    entities = _entities(persons=[_person("104535342")], works=[_work("4558181-2")])
    report = build_report(entities, None, tmp_path / "e.json", None)
    for key in ("audit", "entities_file", "cache_file", "errors", "warnings", "counts"):
        assert key in report
    counts = report["counts"]["entities"]
    assert (counts["persons"], counts["organisations"], counts["works"]) == (1, 0, 1)
    assert counts["total"] == 2
    json.dumps(report, ensure_ascii=False)


# --- real stock ----------------------------------------------------------


def _real_entities():
    if not ENTITIES_PATH.exists():
        pytest.skip("entity list not available")
    return json.loads(ENTITIES_PATH.read_text(encoding="utf-8"))


def test_real_stock_reports_the_known_defects():
    report = lint(_real_entities())
    by_id = {}
    for err in report["errors"]:
        by_id.setdefault(err["gnd_id"], set()).add(err["type"])

    assert "missing_label" in by_id.get("11862974", set())
    for work_id in ("1076202632", "1088014070", "1393920942", "4197012-3"):
        assert "missing_label" in by_id.get(work_id, set()), work_id
    assert "missing_label" in by_id.get("2026220-6", set())
    assert "dnb_link_mismatch" in by_id.get("1076202632", set())


def test_real_stock_has_no_unexpected_error_ids():
    report = lint(_real_entities())
    known = {"11862974", "2026220-6", "1076202632", "1088014070", "1393920942", "4197012-3"}
    assert {e["gnd_id"] for e in report["errors"]} <= known


def test_real_cache_marks_the_defective_ids_as_not_found():
    if not CACHE_PATH.exists():
        pytest.skip("GND cache not built")
    cache = json.loads(CACHE_PATH.read_text(encoding="utf-8"))
    report = lint(_real_entities(), cache)
    not_found = {e["gnd_id"] for e in report["errors"] if e["type"] == "gnd_not_found"}
    # full 404 set of the 2026-08-12 cache: test entry, truncated stub, and the three
    # works the API lookup exposed (one of them a DNB catalog number, not a GND id)
    assert not_found == {"000000", "11862974", "454611536", "1076202632", "1393920942"}
    assert not [e for e in report["errors"] if e["type"] == "cache_status"]
