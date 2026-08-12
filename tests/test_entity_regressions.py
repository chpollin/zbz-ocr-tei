"""Frozen corpus findings of the M3 entity pilot (scripts/tei/entity_matcher).

Every case is one defect the pilot evaluation wave found in the real stock, reduced
to a synthetic mini TEI that carries the original sentence. The fixtures need no
file under output/: the entity records are built here, and the GND ids are taken
from the curated list data/entities/all_entities.json.

Findings and their fix package: knowledge/entity-integration.md, section "Fix
package". Counter-cases sit next to each finding, because a rule that silences the
defect by silencing the correct mention as well is no fix.
"""

from __future__ import annotations

import json

import pytest

from scripts.tei import entity_matcher as em

TEI_HEAD = (
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    '<TEI xmlns="http://www.tei-c.org/ns/1.0">\n'
    "<teiHeader><fileDesc><titleStmt><title>Test</title></titleStmt>"
    "</fileDesc></teiHeader>\n"
)


def _tei(body: str) -> str:
    return TEI_HEAD + f"<text><body>{body}</body></text>\n</TEI>\n"


def _person(gid: str, name: str) -> dict:
    return {"GND_id": gid, "name": name, "listBibl": [], "editor_reviewed": False}


def _org(gid: str, org_name: str) -> dict:
    return {"GND_id": gid, "orgName": org_name, "listBibl": [], "editor_reviewed": False}


def _cache_entry(preferred: str, variants: tuple[str, ...] = ()) -> dict:
    return {
        "http_status": 200,
        "preferred_name": preferred,
        "variant_names": list(variants),
        "types": ["Person"],
        "date_of_birth": None,
        "date_of_death": None,
        "wikidata": None,
    }


def _build(tmp_path, persons=(), orgs=(), cache=None, legacy=None):
    entities_path = tmp_path / "all_entities.json"
    entities_path.write_text(
        json.dumps(
            {"persons": list(persons), "organisations": list(orgs), "works": []},
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    cache_path = tmp_path / "gnd_cache.json"
    if cache is not None:
        cache_path.write_text(
            json.dumps({"retrieved": "2026-08-12", "entries": cache}, ensure_ascii=False),
            encoding="utf-8",
        )
    legacy_path = None
    if legacy is not None:
        legacy_path = tmp_path / "gnd_entities.json"
        legacy_path.write_text(json.dumps(legacy, ensure_ascii=False), encoding="utf-8")
    return em.build_lexicon(entities_path, cache_path, legacy_path)


def _by_surface(cands: list[dict]) -> dict[str, dict]:
    return {c["surface"]: c for c in cands}


# --- "Weil" as a conjunction (German prose, corpus critic finding) -----------------


@pytest.fixture
def weil_lexicon(tmp_path):
    return _build(
        tmp_path,
        persons=[_person("118630148", "Weil, Simone")],
        cache={"118630148": _cache_entry("Weil, Simone", ("Weill, Simone",))},
    )


WEIL_DOC = _tei(
    "<p>Simone Weil schrieb dazu.</p>"
    "<p>Weil ich Jude war, fand ich mich frei von vielen Vorurteilen.</p>"
)


def test_conjunction_weil_after_the_anchor_is_tier2(weil_lexicon):
    cands = em.find_candidates(WEIL_DOC, weil_lexicon)
    assert [c["surface"] for c in cands] == ["Simone Weil", "Weil"]
    assert cands[1]["rule"] == "anchored-surname:suspect"
    assert cands[1]["tier"] == 2


def test_the_full_name_of_the_same_document_stays_tier1(weil_lexicon):
    cands = em.find_candidates(WEIL_DOC, weil_lexicon)
    assert cands[0]["rule"] == "full-name"
    assert cands[0]["tier"] == 1
    assert cands[0]["gid"] == "118630148"


# --- forename collision "Thomas Hoepker" (surname of Thomas Aquinas) ---------------


def test_forename_collision_is_tier2(tmp_path):
    lexicon = _build(
        tmp_path,
        persons=[_person("118622110", "Thomas, von Aquin, Heiliger")],
        cache={"118622110": _cache_entry("Thomas, von Aquin, Heiliger", ("Thomas, von Aquin",))},
    )
    xml = _tei(
        "<p>Bei Thomas, von Aquin, heisst es anders.</p>"
        "<p>Der Fotograf Thomas Höpker berichtete.</p>"
    )
    cands = em.find_candidates(xml, lexicon)
    assert [c["surface"] for c in cands] == ["Thomas, von Aquin", "Thomas"]
    assert cands[0]["tier"] == 1
    assert cands[1]["rule"] == "anchored-surname:suspect"
    assert cands[1]["tier"] == 2


# --- hyphen compound "Schwarz-Bart" (variant surname "Bart" of Karl Barth) ---------


def test_hyphen_compound_is_tier2(tmp_path):
    lexicon = _build(
        tmp_path,
        persons=[_person("118506803", "Barth, Karl")],
        cache={"118506803": _cache_entry("Barth, Karl", ("Bart, Karl", "Barth"))},
    )
    xml = _tei("<p>Karl Barth predigte.</p><p>Der Roman von Schwarz-Bart erschien.</p>")
    cands = em.find_candidates(xml, lexicon)
    assert [c["surface"] for c in cands] == ["Karl Barth", "Bart"]
    assert cands[1]["rule"] == "anchored-surname:suspect"
    assert cands[1]["tier"] == 2


# --- poisoned legacy pairing "Jérémie" filed under Jaspers ------------------------


@pytest.fixture
def jaspers_lexicon(tmp_path):
    return _build(
        tmp_path,
        persons=[_person("118557106", "Jaspers, Karl")],
        cache={"118557106": _cache_entry("Jaspers, Karl", ("Jaspers, Carl",))},
        legacy={"persons": {"118557106": {"names": ["Jérémie", "Jaspers"]}}},
    )


JASPERS_DOC = _tei("<p>Karl Jaspers ecrivit. Jaspers citait souvent Jérémie.</p>")


def test_legacy_only_form_never_reaches_tier1(jaspers_lexicon):
    found = _by_surface(em.find_candidates(JASPERS_DOC, jaspers_lexicon))
    assert found["Jérémie"]["rule"] == "legacy-form"
    assert found["Jérémie"]["tier"] == 2


def test_the_plain_anchored_surname_stays_tier1(jaspers_lexicon):
    found = _by_surface(em.find_candidates(JASPERS_DOC, jaspers_lexicon))
    assert found["Jaspers"]["rule"] == "anchored-surname"
    assert found["Jaspers"]["tier"] == 1
    assert found["Karl Jaspers"]["tier"] == 1


# --- all-caps title mention -------------------------------------------------------


def test_caps_full_name_in_a_title_is_tier1(tmp_path):
    lexicon = _build(tmp_path, persons=[_person("118557106", "Jaspers, Karl")])
    xml = _tei("<head>UNE PHILOSOPHIE DE L'EXISTENCE: KARL JASPERS</head>")
    cands = em.find_candidates(xml, lexicon)
    assert [c["surface"] for c in cands] == ["KARL JASPERS"]
    assert cands[0]["rule"] == "caps-full-name"
    assert cands[0]["tier"] == 1
    assert cands[0]["gid"] == "118557106"


def test_caps_byline_of_the_document_author_is_skipped(tmp_path):
    lexicon = _build(tmp_path, persons=[_person("118815679", "Hersch, Jeanne")])
    xml = _tei("<p>JEANNE HERSCH</p>")
    assert em.find_candidates(xml, lexicon, author_labels=("Hersch, Jeanne",)) == []
    # without the author metadata the same mention is a normal caps hit
    assert [c["rule"] for c in em.find_candidates(xml, lexicon)] == ["caps-full-name"]


# --- E-Periodica cover sheet ------------------------------------------------------


COVER_DOC = _tei(
    '<pb n="1"/>'
    "<p>Zeitschrift: Schweizerische Lehrerzeitung</p>"
    "<p>Herausgeber: Schweizerischer Lehrerverein</p>"
    "<p>Band: 105</p>"
    "<p>Heft: 3</p>"
    '<pb n="2"/>'
    "<p>Der Schweizerischer Lehrerverein tagte in Bern.</p>"
)


def test_cover_sheet_mention_is_no_candidate(tmp_path):
    lexicon = _build(tmp_path, orgs=[_org("2021817-5", "Schweizerischer Lehrerverein")])
    cands = em.find_candidates(COVER_DOC, lexicon)
    assert len(cands) == 1
    assert cands[0]["start"] > COVER_DOC.index('<pb n="2"/>')
    assert cands[0]["surface"] == "Schweizerischer Lehrerverein"
    assert cands[0]["tier"] == 1
