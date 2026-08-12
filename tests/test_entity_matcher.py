"""Tests for scripts/tei/entity_matcher.py (entity integration, milestone M2).

Synthetic mini TEI strings and mini lexicon fixtures only: no repo data files, no
network. The hard cases named in knowledge/entity-integration.md (line breaks inside
names, genitive forms, particles, adjective forms, ambiguous surnames, excluded zones)
drive the fixtures one by one.
"""

from __future__ import annotations

import json

import pytest

from scripts.tei import entity_matcher as em

TEI_HEAD = (
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    '<TEI xmlns="http://www.tei-c.org/ns/1.0">\n'
    "<teiHeader><fileDesc><titleStmt><title>Karl Jaspers</title></titleStmt>"
    "</fileDesc></teiHeader>\n"
    '<facsimile><surface><graphic url="p1.jpg"/></surface></facsimile>\n'
)


def _tei(body: str) -> str:
    """Minimal TEI skeleton; the teiHeader carries a name so header exclusion is testable."""
    return TEI_HEAD + f"<text><body>{body}</body></text>\n</TEI>\n"


def _person(gid: str, name: str) -> dict:
    return {"GND_id": gid, "name": name, "listBibl": [], "editor_reviewed": False}


def _org(gid: str, org_name: str) -> dict:
    return {"GND_id": gid, "orgName": org_name, "listBibl": [], "editor_reviewed": False}


def _work(gid: str, title: str, author: str = "") -> dict:
    return {"GND_id": gid, "title": title, "author_gnd_id": author, "listBibl": []}


def _cache_entry(preferred: str | None = None, variants: tuple[str, ...] = ()) -> dict:
    return {
        "http_status": 200,
        "preferred_name": preferred,
        "variant_names": list(variants),
        "types": ["Person"],
        "date_of_birth": None,
        "date_of_death": None,
        "wikidata": None,
    }


def _build(tmp_path, persons=(), orgs=(), works=(), cache=None, legacy=None):
    """Write the mini fixtures to tmp_path and build the lexicon from them."""
    entities_path = tmp_path / "all_entities.json"
    entities_path.write_text(
        json.dumps(
            {"persons": list(persons), "organisations": list(orgs), "works": list(works)},
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    cache_path = tmp_path / "gnd_cache.json"
    if cache is not None:
        cache_path.write_text(
            json.dumps(
                {"retrieved": "2026-08-12", "source_pattern": "test", "entries": cache},
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
    legacy_path = None
    if legacy is not None:
        legacy_path = tmp_path / "gnd_entities.json"
        legacy_path.write_text(json.dumps(legacy, ensure_ascii=False), encoding="utf-8")
    return em.build_lexicon(entities_path, cache_path, legacy_path)


PERSONS = [
    _person("118557106", "Jaspers, Karl"),
    _person("118557107", "Jaspers, Gertrud"),
    _person("118708422", "Hersch, Jeanne"),
    _person("118577190", "Marcel, Gabriel"),
    _person("118628828", "Wahl, Jean"),
    _person("118535749", "Freud, Sigmund"),
    _person("118647962", "Alembert, Jean"),
    _person("118594893", "Platon"),
]
ORGS = [
    _org("5157117-3", "UNESCO"),
    _org("2008287-3", "Deutscher Gewerkschaftsbund"),
    _org("1000-1", "UNO"),
]
WORKS = [
    _work("4558181-2", "Allgemeine Psychopathologie", "118557106"),
    _work("4006406-2", "Bibel"),
]
CACHE = {
    "118557106": _cache_entry("Jaspers, Karl", ("Jaspers, Karl Theodor", "Karl Jaspers")),
    "118708422": _cache_entry("Hersch, Jeanne", ()),
}


@pytest.fixture
def lex(tmp_path):
    return _build(tmp_path, persons=PERSONS, orgs=ORGS, works=WORKS, cache=CACHE)


def _by_surface(cands: list[dict]) -> dict[str, dict]:
    return {c["surface"]: c for c in cands}


# --- lexicon build ---------------------------------------------------------------


def test_build_lexicon_without_cache_file_uses_headwords(tmp_path):
    lexicon = em.build_lexicon(
        _write_entities(tmp_path, PERSONS), tmp_path / "does_not_exist.json"
    )
    assert "Karl Jaspers" in lexicon["forms"]
    assert lexicon["surnames"]["Jaspers"] == ("118557106", "118557107")


def _write_entities(tmp_path, persons):
    path = tmp_path / "all_entities.json"
    path.write_text(
        json.dumps({"persons": list(persons), "organisations": [], "works": []}),
        encoding="utf-8",
    )
    return path


def test_build_lexicon_skips_missing_label_and_404(tmp_path):
    persons = [
        _person("118557106", "Jaspers, Karl"),
        _person("999999999", ""),
        _person("118708422", "Hersch, Jeanne"),
    ]
    cache = {"118708422": {"http_status": 404}}
    lexicon = _build(tmp_path, persons=persons, cache=cache)
    assert "118557106" in lexicon["entries"]
    assert "118708422" not in lexicon["entries"]
    assert "999999999" not in lexicon["entries"]
    assert lexicon["skipped"]["no_label"] == 1
    assert lexicon["skipped"]["gnd_404"] == 1


def test_build_lexicon_joins_legacy_index_over_normalized_ids(tmp_path):
    legacy = {
        "persons": {"118557106": {"names": ["JASPERS Karl", "Karl\n\t\tJaspers"]}},
        "organizations": {"5157117": {"names": ["Unesco"]}},
        "works": {"4558181": {"names": ["Psychopathologie"]}},
    }
    lexicon = _build(tmp_path, persons=PERSONS, orgs=ORGS, works=WORKS, legacy=legacy)
    assert "JASPERS Karl" in lexicon["forms"]
    assert "Unesco" in lexicon["forms"]
    assert lexicon["forms"]["Psychopathologie"][0][2] == "short-title"


def test_build_lexicon_guards_variant_surnames(tmp_path):
    # lobid carries transliteration fragments; neither "Ma" nor "Ma, Kesi" may become
    # a surname, while the multiword variant form itself stays usable
    cache = {"118578537": _cache_entry("Marx, Karl", ("Ma", "Ma, Kesi", "Marks"))}
    lexicon = _build(tmp_path, persons=[_person("118578537", "Marx, Karl")], cache=cache)
    assert "Ma" not in lexicon["surnames"]
    assert "Marks" in lexicon["surnames"]
    assert lexicon["surnames"]["Marx"] == ("118578537",)
    assert "Kesi Ma" in lexicon["forms"]


def test_curated_one_token_headword_stays_unguarded(tmp_path):
    # the curated headword is authority, the length guard applies to variants only
    lexicon = _build(tmp_path, persons=[_person("118579555", "Mao")])
    assert lexicon["surnames"]["Mao"] == ("118579555",)


def test_build_lexicon_drops_short_org_token(tmp_path):
    lexicon = _build(tmp_path, orgs=ORGS)
    assert "UNESCO" in lexicon["forms"]
    assert "UNO" not in lexicon["forms"]
    assert lexicon["skipped"]["short_org_token"] == 1


# --- full names ------------------------------------------------------------------


def test_full_name_both_orders(lex):
    xml = _tei("<p>Hier spricht Karl Jaspers.</p><p>Zitiert nach Jaspers, Karl.</p>")
    cands = em.find_candidates(xml, lex)
    surfaces = _by_surface(cands)
    assert set(surfaces) == {"Karl Jaspers", "Jaspers, Karl"}
    for cand in cands:
        assert cand["gid"] == "118557106"
        assert cand["category"] == "person"
        assert cand["tier"] == 1
        assert cand["rule"] == "full-name"


def test_full_name_across_line_break(lex):
    xml = _tei('<p>Der Lehrer Karl<lb n="N002"/>Jaspers schrieb.</p>')
    cands = em.find_candidates(xml, lex)
    assert len(cands) == 1
    cand = cands[0]
    assert cand["surface"] == 'Karl<lb n="N002"/>Jaspers'
    assert cand["tier"] == 1
    assert cand["gid"] == "118557106"
    assert xml[cand["start"]:cand["end"]] == cand["surface"]


def test_surname_across_word_internal_break(lex):
    xml = _tei('<p>Also Jas<lb break="no" n="N002"/>pers meinte.</p>')
    cands = em.find_candidates(xml, lex)
    assert len(cands) == 1
    assert cands[0]["surface"] == 'Jas<lb break="no" n="N002"/>pers'
    assert cands[0]["tier"] == 2


def test_genitive_form_is_part_of_surface(lex):
    xml = _tei("<p>Jeanne Hersch schrieb. Herschs Werk bleibt.</p>")
    cands = em.find_candidates(xml, lex)
    assert [c["surface"] for c in cands] == ["Jeanne Hersch", "Herschs"]
    assert cands[1]["rule"] == "anchored-surname"
    assert cands[1]["tier"] == 1
    assert cands[1]["gid"] == "118708422"


def test_trailing_apostrophe_stays_outside_surface(lex):
    xml = _tei("<p>Jaspers&#8217; Werk und Jaspers' Buch.</p>")
    cands = em.find_candidates(xml, lex)
    assert [c["surface"] for c in cands] == ["Jaspers", "Jaspers"]
    assert all(xml[c["start"]:c["end"]] == c["surface"] for c in cands)


def test_particle_stays_outside_surface(lex):
    xml = _tei("<p>Bei d'Alembert steht es anders.</p>")
    cands = em.find_candidates(xml, lex)
    assert len(cands) == 1
    assert cands[0]["surface"] == "Alembert"
    assert xml[cands[0]["start"] - 2:cands[0]["start"]] == "d'"


# --- initial plus surname --------------------------------------------------------


@pytest.mark.parametrize(
    ("text", "gid"),
    [("K. Jaspers", "118557106"), ("G. Jaspers", "118557107")],
)
def test_initial_surname_resolves_unique_forename(lex, text, gid):
    xml = _tei(f"<p>Nach {text} ist das klar.</p>")
    cands = em.find_candidates(xml, lex)
    assert len(cands) == 1
    assert cands[0]["surface"] == text
    assert cands[0]["rule"] == "initial-surname"
    assert cands[0]["tier"] == 1
    assert cands[0]["gid"] == gid


def test_initial_without_matching_forename_gives_no_tier1(lex):
    xml = _tei("<p>Nach X. Jaspers ist das offen.</p>")
    cands = em.find_candidates(xml, lex)
    assert all(c["rule"] != "initial-surname" for c in cands)
    assert all(c["tier"] == 2 for c in cands)
    assert [c["surface"] for c in cands] == ["Jaspers"]


# --- surnames --------------------------------------------------------------------


def test_anchored_surname_after_full_name(lex):
    xml = _tei("<p>Gabriel Marcel schrieb.</p><p>Pour Marcel, la question reste.</p>")
    cands = em.find_candidates(xml, lex)
    assert [c["rule"] for c in cands] == ["full-name", "anchored-surname"]
    assert all(c["gid"] == "118577190" for c in cands)
    assert all(c["tier"] == 1 for c in cands)


def test_surname_before_the_full_name_is_anchored_document_wide(lex):
    xml = _tei("<p>Pour Marcel, la question reste.</p><p>Gabriel Marcel schrieb.</p>")
    cands = em.find_candidates(xml, lex)
    assert [c["rule"] for c in cands] == ["anchored-surname", "full-name"]
    assert all(c["tier"] == 1 for c in cands)
    assert all(c["gid"] == "118577190" for c in cands)


def test_bare_surname_without_anchor_is_tier2(lex):
    xml = _tei("<p>Pour Marcel, la question reste.</p>")
    cands = em.find_candidates(xml, lex)
    assert len(cands) == 1
    assert cands[0]["rule"] == "bare-surname"
    assert cands[0]["tier"] == 2


def test_ambiguous_anchor_is_tier2(lex):
    xml = _tei("<p>Karl Jaspers und Gertrud Jaspers.</p><p>Jaspers antwortete.</p>")
    cands = em.find_candidates(xml, lex)
    assert cands[-1]["surface"] == "Jaspers"
    assert cands[-1]["rule"] == "ambiguous-surname"
    assert cands[-1]["tier"] == 2


def test_common_noun_homonym_stays_tier2(lex):
    xml = _tei("<p>Die Wahl war frei.</p>")
    cands = em.find_candidates(xml, lex)
    assert len(cands) == 1
    assert cands[0]["surface"] == "Wahl"
    assert cands[0]["rule"] == "bare-surname"
    assert cands[0]["tier"] == 2


def test_lowercase_word_is_never_a_candidate(lex):
    xml = _tei("<p>Die wahl war frei, ganz kantien gedacht.</p>")
    assert em.find_candidates(xml, lex) == []


def test_adjective_form_is_rejected(lex):
    xml = _tei("<p>Die Freudschen Schriften, aber Freuds Schriften.</p>")
    cands = em.find_candidates(xml, lex)
    assert [c["surface"] for c in cands] == ["Freuds"]


# --- excluded zones --------------------------------------------------------------


def test_teiheader_is_excluded(lex):
    xml = _tei("<p>Nichts.</p>")
    assert em.find_candidates(xml, lex) == []


def test_figure_content_is_excluded(lex):
    xml = _tei("<figure><figDesc>Karl Jaspers im Garten</figDesc></figure>")
    assert em.find_candidates(xml, lex) == []


def test_bibliography_div_is_excluded(lex):
    xml = _tei('<div type="bibliography"><bibl>Karl Jaspers, Werke</bibl></div>')
    assert em.find_candidates(xml, lex) == []


def test_existing_persname_is_skipped(lex):
    xml = _tei(
        '<p><persName ref="GND:118557106">Karl Jaspers</persName> und Karl Jaspers.</p>'
    )
    cands = em.find_candidates(xml, lex)
    assert len(cands) == 1
    assert cands[0]["start"] > xml.index("</persName>")


def test_existing_orgname_is_skipped(lex):
    xml = _tei('<p><orgName ref="GND:5157117-3">UNESCO</orgName> in Paris.</p>')
    assert em.find_candidates(xml, lex) == []


def test_bibl_with_ref_is_excluded(lex):
    xml = _tei('<p><bibl ref="GND:4558181-2">Allgemeine Psychopathologie</bibl></p>')
    assert em.find_candidates(xml, lex) == []


def test_plain_bibl_is_tier2_with_suffix(lex):
    xml = _tei("<p><bibl>Karl Jaspers, Allgemeine Psychopathologie</bibl></p>")
    cands = em.find_candidates(xml, lex)
    assert [c["surface"] for c in cands] == ["Karl Jaspers", "Allgemeine Psychopathologie"]
    assert all(c["tier"] == 2 for c in cands)
    assert all(c["rule"].endswith(":in-plain-bibl") for c in cands)
    assert cands[0]["rule"] == "full-name:in-plain-bibl"


def test_footnote_is_a_normal_matching_zone(lex):
    xml = _tei('<p>Text</p><note place="foot" n="1">Vgl. Karl Jaspers, Werke.</note>')
    cands = em.find_candidates(xml, lex)
    assert [c["surface"] for c in cands] == ["Karl Jaspers"]
    assert cands[0]["tier"] == 1


# --- markup boundaries -----------------------------------------------------------


def test_match_crossing_markup_is_downgraded(lex):
    xml = _tei('<p>Karl <hi rendition="#i">Jaspers</hi> schrieb.</p>')
    cands = em.find_candidates(xml, lex)
    assert cands[0]["surface"] == "Karl"
    assert cands[0]["rule"] == "crosses-markup"
    assert cands[0]["tier"] == 2
    assert [c["surface"] for c in cands] == ["Karl", "Jaspers"]


# --- speaker, organisations, works ------------------------------------------------


def test_speaker_slot_with_unique_surname(lex):
    xml = _tei("<sp><speaker>Hersch:</speaker><p>Ja.</p></sp>")
    cands = em.find_candidates(xml, lex)
    assert len(cands) == 1
    assert cands[0]["surface"] == "Hersch"
    assert cands[0]["rule"] == "speaker"
    assert cands[0]["tier"] == 1
    assert cands[0]["gid"] == "118708422"


def test_speaker_slot_with_ambiguous_surname_is_tier2(lex):
    xml = _tei("<sp><speaker>Jaspers:</speaker><p>Ja.</p></sp>")
    cands = em.find_candidates(xml, lex)
    assert cands[0]["rule"] == "speaker"
    assert cands[0]["tier"] == 2


def test_empty_speaker_stays_empty(lex):
    xml = _tei('<sp><speaker><persName ref="GND:118708422"/></speaker><p>Ja.</p></sp>')
    assert em.find_candidates(xml, lex) == []


def test_org_token_needs_length_and_capital(lex):
    xml = _tei("<p>Die Abteilung an der UNESCO in Paris.</p>")
    cands = em.find_candidates(xml, lex)
    assert len(cands) == 1
    assert cands[0]["surface"] == "UNESCO"
    assert cands[0]["category"] == "organisation"
    assert cands[0]["rule"] == "org-token"
    assert cands[0]["tier"] == 1


def test_multiword_org_name(lex):
    xml = _tei("<p>Der Deutscher Gewerkschaftsbund tagte.</p>")
    cands = em.find_candidates(xml, lex)
    assert cands[0]["surface"] == "Deutscher Gewerkschaftsbund"
    assert cands[0]["rule"] == "org-name"
    assert cands[0]["tier"] == 1


def test_multiword_work_title_is_tier1(lex):
    xml = _tei("<p>Er las Allgemeine Psychopathologie im Original.</p>")
    cands = em.find_candidates(xml, lex)
    assert cands[0]["surface"] == "Allgemeine Psychopathologie"
    assert cands[0]["category"] == "work"
    assert cands[0]["rule"] == "work-title"
    assert cands[0]["tier"] == 1


def test_single_word_title_is_tier2(lex):
    xml = _tei("<p>In der Bibel steht es.</p>")
    cands = em.find_candidates(xml, lex)
    assert cands[0]["surface"] == "Bibel"
    assert cands[0]["rule"] == "short-title"
    assert cands[0]["tier"] == 2


def test_cache_variant_full_name(lex):
    xml = _tei("<p>Von Karl Theodor Jaspers stammt der Satz.</p>")
    cands = em.find_candidates(xml, lex)
    assert cands[0]["surface"] == "Karl Theodor Jaspers"
    assert cands[0]["rule"] == "variant-full-name"
    assert cands[0]["tier"] == 1


# --- hard invariants over a composite document ------------------------------------

COMPOSITE = _tei(
    '<div n="1" type="speech">'
    '<p>Karl<lb n="N001"/>Jaspers und Jas<lb break="no" n="N002"/>pers, dazu Herschs Werk.</p>'
    "<p>Jeanne Hersch, K. Jaspers, d'Alembert, Die Wahl, Platon.</p>"
    '<p>An der UNESCO, in <hi rendition="#i">Allgemeine Psychopathologie</hi>.</p>'
    "<note place=\"foot\" n=\"1\">Vgl. Jaspers&#8217; Werk.</note>"
    "<sp><speaker>Hersch:</speaker><p>Die Freudschen Thesen.</p></sp>"
    "<figure><figDesc>Karl Jaspers</figDesc></figure>"
    "<p><bibl>Gabriel Marcel, Werke</bibl></p>"
    '<div type="bibliography"><bibl>Karl Jaspers, Werke</bibl></div>'
    "</div>"
)


def test_surface_matches_offsets_for_every_candidate(lex):
    cands = em.find_candidates(COMPOSITE, lex)
    assert cands
    for cand in cands:
        assert COMPOSITE[cand["start"]:cand["end"]] == cand["surface"]


def test_candidates_are_sorted_and_free_of_overlap(lex):
    cands = em.find_candidates(COMPOSITE, lex)
    for prev, cur in zip(cands, cands[1:]):
        assert prev["start"] < cur["start"]
        assert prev["end"] <= cur["start"]


def test_candidates_stay_inside_text_element(lex):
    text_start = COMPOSITE.index("<text>")
    text_end = COMPOSITE.index("</text>")
    for cand in em.find_candidates(COMPOSITE, lex):
        assert text_start < cand["start"] < cand["end"] <= text_end


def test_surface_carries_only_lb_markup(lex):
    for cand in em.find_candidates(COMPOSITE, lex):
        for tag in em.iter_tags(cand["surface"]):
            assert tag.startswith("<lb")


def test_candidate_keys_are_exactly_the_contract(lex):
    expected = {"gid", "category", "surface", "start", "end", "tier", "rule", "context"}
    for cand in em.find_candidates(COMPOSITE, lex):
        assert set(cand) == expected
        assert cand["tier"] in (1, 2)
        assert cand["category"] in ("person", "organisation", "work")
        assert cand["context"]


def test_run_is_deterministic(lex):
    first = em.find_candidates(COMPOSITE, lex)
    second = em.find_candidates(COMPOSITE, lex)
    assert first == second


# --- initials-only cache variants (doc-1220 defect) --------------------------------


def test_initials_only_cache_variant_never_reaches_the_lexicon(tmp_path):
    # lobid lists bare initials as variants (Pestalozzi: "J. H."); as a tier-1
    # full-name form they mislabel every "J. H." in the corpus (doc-1220 defect).
    persons = [_person("118592912", "Pestalozzi, Johann Heinrich")]
    cache = {
        "118592912": _cache_entry(
            "Pestalozzi, Johann Heinrich",
            ("J. H.", "J.H.", "H., J.", "Pestalozzi, J. H."),
        )
    }
    lexicon = _build(tmp_path, persons=persons, cache=cache)
    assert "J. H." not in lexicon["forms"]
    assert "J.H." not in lexicon["forms"]
    # initials next to a real name word keep working
    assert "J. H. Pestalozzi" in lexicon["forms"]
    xml = _tei("<p>J. H. antwortet dem Interviewer.</p>")
    assert em.find_candidates(xml, lexicon) == []


def test_transliteration_word_variants_are_not_initials(tmp_path):
    # two-letter words without dots ("Mo Ti" for Mozi) are real name forms
    persons = [_person("118584553", "Mo, Di")]
    cache = {"118584553": _cache_entry("Mo, Di", ("Mo Ti",))}
    lexicon = _build(tmp_path, persons=persons, cache=cache)
    assert "Mo Ti" in lexicon["forms"]
