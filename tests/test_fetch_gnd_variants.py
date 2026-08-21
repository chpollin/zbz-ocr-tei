"""Tests for the lobid-GND cache builder (scripts.entity.fetch_gnd_variants).

Parser logic only: the fixtures stand in for lobid responses, no network is touched.
"""

import json

import pytest

from scripts.entity.fetch_gnd_variants import (
    SOURCE_PATTERN,
    build_payload,
    collect_gnd_ids,
    parse_lobid_record,
)

PERSON_FIXTURE = {
    "id": "https://d-nb.info/gnd/118826875",
    "type": ["AuthorityResource", "DifferentiatedPerson", "Person"],
    "preferredName": "Zinov'ev, Aleksandr Aleksandrovic",
    "variantName": ["Zinoviev, Alexander", "Sinowjew, Alexander"],
    "dateOfBirth": ["1922-10-29"],
    "dateOfDeath": ["2006-05-10"],
    "sameAs": [
        {"id": "https://viaf.org/viaf/17226624", "collection": {"name": "VIAF"}},
        {"id": "http://www.wikidata.org/entity/Q347254", "collection": {"name": "Wikidata"}},
    ],
}


def test_parse_person_record():
    parsed = parse_lobid_record(PERSON_FIXTURE)
    assert parsed["http_status"] == 200
    assert parsed["preferred_name"] == "Zinov'ev, Aleksandr Aleksandrovic"
    assert parsed["variant_names"] == ["Zinoviev, Alexander", "Sinowjew, Alexander"]
    assert parsed["date_of_birth"] == "1922-10-29"
    assert parsed["date_of_death"] == "2006-05-10"
    assert parsed["wikidata"] == "Q347254"


def test_authority_resource_type_is_dropped():
    assert parse_lobid_record(PERSON_FIXTURE)["types"] == ["DifferentiatedPerson", "Person"]


def test_sparse_record_yields_null_and_empty_defaults():
    parsed = parse_lobid_record({"id": "https://d-nb.info/gnd/4558181-2"})
    assert parsed == {
        "http_status": 200,
        "preferred_name": None,
        "variant_names": [],
        "types": [],
        "date_of_birth": None,
        "date_of_death": None,
        "wikidata": None,
    }


def test_https_wikidata_url_is_accepted_and_other_sameas_ignored():
    parsed = parse_lobid_record(
        {"sameAs": [{"id": "https://d-nb.info/gnd/4558181-2"}, {"id": "https://www.wikidata.org/entity/Q42"}]}
    )
    assert parsed["wikidata"] == "Q42"


def test_no_wikidata_sameas_is_null():
    parsed = parse_lobid_record({"sameAs": [{"id": "https://isni.org/isni/0000000121032683"}]})
    assert parsed["wikidata"] is None


def test_dates_take_the_first_list_value():
    parsed = parse_lobid_record({"dateOfBirth": ["1900", "1901"], "dateOfDeath": []})
    assert parsed["date_of_birth"] == "1900"
    assert parsed["date_of_death"] is None


def test_collect_ids_covers_all_three_lists_and_deduplicates():
    entities = {
        "persons": [{"GND_id": "104535342"}, {"GND_id": "118826875"}, {"GND_id": "104535342"}],
        "organisations": [{"GND_id": "5005966-X"}],
        "works": [{"GND_id": "4558181-2"}, {"GND_id": "  "}, {}],
    }
    assert collect_gnd_ids(entities) == [
        "104535342",
        "118826875",
        "5005966-X",
        "4558181-2",
    ]


def test_payload_shape_is_the_cache_contract():
    payload = build_payload({"118826875": parse_lobid_record(PERSON_FIXTURE)}, "2026-08-12")
    assert payload["retrieved"] == "2026-08-12"
    assert payload["source_pattern"] == SOURCE_PATTERN
    assert list(payload) == ["retrieved", "source_pattern", "entries"]
    assert payload["entries"]["118826875"]["preferred_name"]
    json.dumps(payload, ensure_ascii=False)


@pytest.mark.requires_mirror
def test_real_cache_file_keeps_the_contract():
    """The committed cache must keep the shape a refetch could silently change."""
    from scripts.config import DATA_DIR

    cache_file = DATA_DIR / "entities" / "gnd_cache.json"
    if not cache_file.exists():
        pytest.skip("GND cache not built")
    payload = json.loads(cache_file.read_text(encoding="utf-8"))
    assert list(payload) == ["retrieved", "source_pattern", "entries"]
    assert payload["source_pattern"] == SOURCE_PATTERN
    contract = {"http_status", "preferred_name", "variant_names", "types",
                "date_of_birth", "date_of_death", "wikidata"}
    for gid, entry in payload["entries"].items():
        if entry["http_status"] == 404:
            assert set(entry) == {"http_status"}, gid
        else:
            assert entry["http_status"] == 200, gid
            assert set(entry) == contract, gid
            assert isinstance(entry["variant_names"], list), gid
            assert isinstance(entry["types"], list), gid
