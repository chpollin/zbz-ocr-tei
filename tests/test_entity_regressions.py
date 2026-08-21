"""Frozen corpus findings of the M3 entity pilot (scripts/entity/entity_matcher).

Every case is one defect the pilot evaluation wave found in the real stock, reduced
to a synthetic mini TEI that carries the original sentence. The fixtures need no
file under output/: the entity records are built here, and the GND ids are taken
from the curated list data/entities/all_entities.json.

Findings and their fix package: knowledge/entity-integration.md, section "Fix
package". Counter-cases sit next to each finding, because a rule that silences the
defect by silencing the correct mention as well is no fix.
"""

from __future__ import annotations

import pytest

from scripts.entity import entity_matcher as em
from tests.conftest import build_lexicon_dir, gnd_cache_entry, org_record, person_record

TEI_HEAD = (
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    '<TEI xmlns="http://www.tei-c.org/ns/1.0">\n'
    "<teiHeader><fileDesc><titleStmt><title>Test</title></titleStmt>"
    "</fileDesc></teiHeader>\n"
)


def _tei(body: str) -> str:
    return TEI_HEAD + f"<text><body>{body}</body></text>\n</TEI>\n"


def _by_surface(cands: list[dict]) -> dict[str, dict]:
    return {c["surface"]: c for c in cands}


# --- "Weil" as a conjunction (German prose, corpus critic finding) -----------------


@pytest.fixture
def weil_lexicon(tmp_path):
    return build_lexicon_dir(
        tmp_path,
        persons=[person_record("118630148", "Weil, Simone")],
        cache={"118630148": gnd_cache_entry("Weil, Simone", ("Weill, Simone",))},
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
    lexicon = build_lexicon_dir(
        tmp_path,
        persons=[person_record("118622110", "Thomas, von Aquin, Heiliger")],
        cache={"118622110": gnd_cache_entry("Thomas, von Aquin, Heiliger", ("Thomas, von Aquin",))},
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
    lexicon = build_lexicon_dir(
        tmp_path,
        persons=[person_record("118506803", "Barth, Karl")],
        cache={"118506803": gnd_cache_entry("Barth, Karl", ("Bart, Karl", "Barth"))},
    )
    xml = _tei("<p>Karl Barth predigte.</p><p>Der Roman von Schwarz-Bart erschien.</p>")
    cands = em.find_candidates(xml, lexicon)
    assert [c["surface"] for c in cands] == ["Karl Barth", "Bart"]
    assert cands[1]["rule"] == "anchored-surname:suspect"
    assert cands[1]["tier"] == 2


# --- poisoned legacy pairing "Jérémie" filed under Jaspers ------------------------


@pytest.fixture
def jaspers_lexicon(tmp_path):
    return build_lexicon_dir(
        tmp_path,
        persons=[person_record("118557106", "Jaspers, Karl")],
        cache={"118557106": gnd_cache_entry("Jaspers, Karl", ("Jaspers, Carl",))},
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
    lexicon = build_lexicon_dir(tmp_path, persons=[person_record("118557106", "Jaspers, Karl")])
    xml = _tei("<head>UNE PHILOSOPHIE DE L'EXISTENCE: KARL JASPERS</head>")
    cands = em.find_candidates(xml, lexicon)
    assert [c["surface"] for c in cands] == ["KARL JASPERS"]
    assert cands[0]["rule"] == "caps-full-name"
    assert cands[0]["tier"] == 1
    assert cands[0]["gid"] == "118557106"


def test_caps_byline_of_the_document_author_is_marked(tmp_path):
    # the author is marked like every other listed entity (operator decision E108);
    # running heads are held back by the zone suppression, not by an author exception
    lexicon = build_lexicon_dir(tmp_path, persons=[person_record("118815679", "Hersch, Jeanne")])
    xml = _tei("<p>JEANNE HERSCH</p>")
    cands = em.find_candidates(xml, lexicon)
    assert [c["rule"] for c in cands] == ["caps-full-name"]
    assert cands[0]["tier"] == 1


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
    lexicon = build_lexicon_dir(tmp_path, orgs=[org_record("2021817-5", "Schweizerischer Lehrerverein")])
    cands = em.find_candidates(COVER_DOC, lexicon)
    assert len(cands) == 1
    assert cands[0]["start"] > COVER_DOC.index('<pb n="2"/>')
    assert cands[0]["surface"] == "Schweizerischer Lehrerverein"
    assert cands[0]["tier"] == 1


# --- case-divergent work title (doc 2330, corpus finding) --------------------------


def test_case_divergent_work_title_is_a_candidate(tmp_path):
    # the GND cache carries "La foi philosophique", doc 2330 sets "La Foi philosophique";
    # the mention used to be lost on the capital F alone
    lexicon = build_lexicon_dir(
        tmp_path,
        works=[{"GND_id": "1088013937", "title": "Der philosophische Glaube",
                "author_gnd_id": "118557106", "listBibl": []}],
        cache={"1088013937": gnd_cache_entry("Der philosophische Glaube",
                                          ("La foi philosophique",))},
    )
    xml = _tei(
        "<p>Vous avez traduit <hi rendition=\"#i\">La Foi philosophique</hi>, "
        "ainsi que d'autres textes de Jaspers.</p>"
    )
    cands = em.find_candidates(xml, lexicon)
    assert [c["surface"] for c in cands] == ["La Foi philosophique"]
    assert cands[0]["gid"] == "1088013937"
    assert cands[0]["matched_form"] == "La foi philosophique"
    assert cands[0]["form_source"] == "cache-variant"
    assert cands[0]["tier"] == 1


def test_case_tolerance_leaves_the_all_caps_person_regime_alone(tmp_path):
    # the caps channel keeps its own rule; the case-tolerant channel must not take
    # an all-caps person name away from it
    lexicon = build_lexicon_dir(tmp_path, persons=[person_record("118815679", "Hersch, Jeanne")])
    xml = _tei("<p>JEANNE HERSCH</p>")
    assert [c["rule"] for c in em.find_candidates(xml, lexicon)] == ["caps-full-name"]


# --- ambiguous bare surname: both Jaspers spouses (frontend evaluation, point 1) ---

# ids from data/entities/all_entities.json; the GND variants from its cache
JASPERS_SPOUSES = [
    person_record("118557106", "Jaspers, Karl"),
    person_record("117085391", "Jaspers, Gertrud"),
]
SPOUSE_CACHE = {
    "118557106": gnd_cache_entry("Jaspers, Karl", ("Jaspers, Carl",)),
    "117085391": gnd_cache_entry("Jaspers, Gertrud",
                              ("Jaspers-Mayer, Gertrud", "Mayer, Gertrud")),
}


@pytest.fixture
def spouse_lexicon(tmp_path):
    return build_lexicon_dir(tmp_path, persons=JASPERS_SPOUSES, cache=SPOUSE_CACHE)


def test_bare_surname_names_both_spouses(spouse_lexicon):
    # the report used to show the numerically first bearer alone, which read as decided
    xml = _tei("<p>Dazu meinte Jaspers spaeter nichts mehr.</p>")
    cands = em.find_candidates(xml, spouse_lexicon)
    assert [c["surface"] for c in cands] == ["Jaspers"]
    assert cands[0]["rule"] == "bare-surname:ambiguous"
    assert cands[0]["tier"] == 2
    assert cands[0]["alternatives"] == ["117085391", "118557106"]


def test_full_name_of_one_spouse_stays_unambiguous(spouse_lexicon):
    cands = em.find_candidates(_tei("<p>Hier spricht Karl Jaspers.</p>"), spouse_lexicon)
    assert cands[0]["rule"] == "full-name"
    assert cands[0]["tier"] == 1
    assert cands[0]["gid"] == "118557106"
    assert cands[0]["alternatives"] == []


# --- "Hans Mayer": surname from a GND variant, no bigram corroboration (point 2/3) --


@pytest.fixture
def mayer_lexicon(tmp_path):
    # "Bauer, Hans" puts a listed form under the first word "Hans", which used to
    # silence the neighbour signal all by itself
    persons = [*JASPERS_SPOUSES, person_record("13143568X", "Bauer, Hans")]
    return build_lexicon_dir(tmp_path, persons=persons, cache=SPOUSE_CACHE)


MAYER_DOC = _tei("<p>Der Literaturwissenschaftler Hans Mayer schrieb dazu.</p>")


def test_hans_mayer_carries_the_homograph_suspicion(mayer_lexicon):
    cands = em.find_candidates(MAYER_DOC, mayer_lexicon)
    assert [c["surface"] for c in cands] == ["Mayer"]
    assert cands[0]["rule"] == "bare-surname:suspect"
    assert cands[0]["tier"] == 2


def test_hans_mayer_names_the_variant_it_came_from(mayer_lexicon):
    cand = em.find_candidates(MAYER_DOC, mayer_lexicon)[0]
    assert cand["gid"] == "117085391"
    assert cand["matched_form"] == "Mayer, Gertrud"
    assert cand["form_source"] == "cache-variant"


def test_karl_jaspers_stays_untouched_by_the_bigram_change(mayer_lexicon):
    xml = _tei("<p>Der Philosoph Karl Jaspers schrieb dazu.</p>")
    cands = em.find_candidates(xml, mayer_lexicon)
    assert [c["surface"] for c in cands] == ["Karl Jaspers"]
    assert cands[0]["rule"] == "full-name"
    assert cands[0]["tier"] == 1
