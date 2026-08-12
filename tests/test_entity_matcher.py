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


def _build(tmp_path, persons=(), orgs=(), works=(), cache=None, legacy=None, review=None):
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
    review_path = None
    if review is not None:
        review_path = tmp_path / "variant_review.json"
        review_path.write_text(json.dumps(review, ensure_ascii=False), encoding="utf-8")
    return em.build_lexicon(entities_path, cache_path, legacy_path, review_path=review_path)


def _review(persons=None, orgs=None, works=None):
    """Minimal variant_review.json payload; verdicts keyed by gid and cache form."""
    return {
        "reviewed": "2026-08-12",
        "source_cache_retrieved": "2026-08-12",
        "scope": "test",
        "verdict_values": ["approve", "suspect", "reject"],
        "persons": persons or {},
        "organisations": orgs or {},
        "works": works or {},
    }


def _verdicts(gid, headword, forms):
    """{gid: {headword, verdicts}} with a verdict string per cache form."""
    return {
        gid: {
            "headword": headword,
            "verdicts": {
                form: {"verdict": verdict, "reason": "test"}
                for form, verdict in forms.items()
            },
        }
    }


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


def test_forms_carry_their_provenance(tmp_path):
    lexicon = _build(tmp_path, persons=PERSONS, orgs=ORGS, works=WORKS, cache=CACHE)
    assert lexicon["forms"]["Karl Jaspers"][0] == ("118557106", "person", "full-name", "headword")
    assert lexicon["forms"]["Karl Theodor Jaspers"][0][3] == "cache-variant"
    assert lexicon["forms"]["UNESCO"][0][3] == "headword"


def test_surname_index_carries_the_form_that_registered_it(tmp_path):
    # ids and variants from data/entities/all_entities.json plus its GND cache
    cache = {"117085391": _cache_entry("Jaspers, Gertrud", ("Mayer, Gertrud",))}
    lexicon = _build(tmp_path, persons=[_person("117085391", "Jaspers, Gertrud")], cache=cache)
    assert lexicon["surname_forms"]["Jaspers"]["117085391"] == ("Jaspers", "surname-index")
    assert lexicon["surname_forms"]["Mayer"]["117085391"] == ("Mayer, Gertrud", "cache-variant")


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
    # fix package 3: the function-word list marks the homograph suspicion
    assert cands[0]["rule"] == "bare-surname:suspect"
    assert cands[0]["tier"] == 2


def test_lowercase_word_is_never_a_candidate(lex):
    xml = _tei("<p>Die wahl war frei, ganz kantien gedacht.</p>")
    assert em.find_candidates(xml, lex) == []


def test_adjective_form_is_a_tier2_candidate(lex):
    # fix package 6: the derived form is reported on the worklist instead of dropped
    xml = _tei("<p>Die Freudschen Schriften, aber Freuds Schriften.</p>")
    cands = em.find_candidates(xml, lex)
    assert [c["surface"] for c in cands] == ["Freudschen", "Freuds"]
    assert cands[0]["rule"] == "adjective-form"
    assert cands[0]["tier"] == 2
    assert cands[0]["gid"] == "118535749"


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
    assert cands[0]["rule"] == "speaker:ambiguous"
    assert cands[0]["tier"] == 2
    assert cands[0]["alternatives"] == ["118557106", "118557107"]


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
    "<p>In der Bibel steht es.</p>"
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


CANDIDATE_KEYS = {
    "gid", "category", "surface", "start", "end", "tier", "rule",
    "alternatives", "matched_form", "form_source", "context",
}


def test_candidate_keys_are_exactly_the_contract(lex):
    cands = em.find_candidates(COMPOSITE, lex)
    assert any(c["rule"].split(":")[0] == "short-title" for c in cands)
    for cand in cands:
        # evidence is carried by the one-word work titles only (typography pre-sorting)
        extra = {"evidence"} if cand["rule"].split(":")[0] == "short-title" else set()
        assert set(cand) == CANDIDATE_KEYS | extra
        assert cand["tier"] in (1, 2)
        assert cand["category"] in ("person", "organisation", "work")
        assert cand["context"]
        assert isinstance(cand["alternatives"], list)
        assert cand["matched_form"]
        assert cand["form_source"] in em.FORM_SOURCES


def test_alternatives_are_empty_or_name_at_least_two_bearers(lex):
    for cand in em.find_candidates(COMPOSITE, lex):
        assert len(cand["alternatives"]) != 1
        if cand["alternatives"]:
            assert cand["gid"] in cand["alternatives"]
            assert cand["alternatives"] == sorted(cand["alternatives"])


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


# --- legacy demotion (fix package 1) ----------------------------------------------

LEGACY_JEREMIE = {"persons": {"118557106": {"names": ["Jérémie", "Karl Jaspers"]}}}


def test_legacy_only_form_is_demoted(tmp_path):
    lexicon = _build(tmp_path, persons=PERSONS, cache=CACHE, legacy=LEGACY_JEREMIE)
    assert lexicon["forms"]["Jérémie"] == (("118557106", "person", "legacy-form", "legacy"),)
    assert "Jérémie" not in lexicon["surnames"]
    assert ("118557106", "Jérémie") in lexicon["legacy_demoted"]


def test_legacy_form_corroborated_by_the_record_stays_a_full_name(tmp_path):
    lexicon = _build(tmp_path, persons=PERSONS, cache=CACHE, legacy=LEGACY_JEREMIE)
    assert lexicon["forms"]["Karl Jaspers"][0][2] == "full-name"
    assert all(form != "Karl Jaspers" for _, form in lexicon["legacy_demoted"])


def test_legacy_only_form_never_reaches_tier1(tmp_path):
    lexicon = _build(tmp_path, persons=PERSONS, cache=CACHE, legacy=LEGACY_JEREMIE)
    xml = _tei("<p>Karl Jaspers citait souvent Jérémie.</p>")
    found = _by_surface(em.find_candidates(xml, lexicon))
    assert found["Karl Jaspers"]["tier"] == 1
    assert found["Jérémie"]["rule"] == "legacy-form"
    assert found["Jérémie"]["tier"] == 2


# --- homograph suspicion (fix package 3) ------------------------------------------


def test_function_word_homograph_drops_the_anchor(lex):
    xml = _tei("<p>Jean Wahl schrieb.</p><p>Die Wahl war frei.</p>")
    cands = em.find_candidates(xml, lex)
    assert [c["rule"] for c in cands] == ["full-name", "anchored-surname:suspect"]
    assert cands[1]["tier"] == 2


def test_lowercase_twin_in_the_document_drops_the_anchor(lex):
    xml = _tei("<p>Gabriel Marcel schrieb.</p><p>Marcel bleibt.</p><p>ein marcel dazu.</p>")
    cands = em.find_candidates(xml, lex)
    assert [c["rule"] for c in cands] == ["full-name", "anchored-surname:suspect"]
    assert cands[1]["tier"] == 2


def test_adjacent_hyphen_drops_the_anchor(lex):
    xml = _tei("<p>Karl Jaspers schrieb.</p><p>Der Jaspers-Kreis tagte.</p>")
    cands = em.find_candidates(xml, lex)
    assert cands[1]["surface"] == "Jaspers"
    assert cands[1]["rule"] == "anchored-surname:suspect"
    assert cands[1]["tier"] == 2


def test_unknown_capitalized_neighbour_drops_the_anchor(lex):
    xml = _tei("<p>Gabriel Marcel schrieb.</p><p>Der Fotograf Marcel Duchamp kam.</p>")
    cands = em.find_candidates(xml, lex)
    assert cands[1]["surface"] == "Marcel"
    assert cands[1]["rule"] == "anchored-surname:suspect"
    assert cands[1]["tier"] == 2


def test_capitalized_neighbour_at_a_sentence_start_is_no_signal(lex):
    xml = _tei("<p>Gabriel Marcel schrieb.</p><p>Pour Marcel, la question reste.</p>")
    cands = em.find_candidates(xml, lex)
    assert [c["rule"] for c in cands] == ["full-name", "anchored-surname"]
    assert all(c["tier"] == 1 for c in cands)


def test_genitive_before_a_capitalized_noun_keeps_the_anchor(lex):
    # German capitalizes nouns; a genitive name is followed by its head noun
    xml = _tei("<p>Jeanne Hersch schrieb.</p><p>Herschs Werk bleibt.</p>")
    cands = em.find_candidates(xml, lex)
    assert cands[1]["surface"] == "Herschs"
    assert cands[1]["rule"] == "anchored-surname"
    assert cands[1]["tier"] == 1


def test_honorific_before_the_surname_is_no_signal(lex):
    # "Frau Hersch", "Mlle Hersch": the honorific corroborates the name reading
    xml = _tei("<p>Jeanne Hersch schrieb.</p><p>Dazu sagte Mlle Hersch nichts.</p>")
    cands = em.find_candidates(xml, lex)
    assert [c["rule"] for c in cands] == ["full-name", "anchored-surname"]
    assert all(c["tier"] == 1 for c in cands)


def test_full_name_rules_ignore_the_suspicion_signals(lex):
    xml = _tei("<p>Karl Jaspers Duchamp und K. Jaspers Duchamp.</p>")
    cands = em.find_candidates(xml, lex)
    assert [c["rule"] for c in cands] == ["full-name", "initial-surname"]
    assert all(c["tier"] == 1 for c in cands)


# --- adjective forms (fix package 6) ----------------------------------------------


@pytest.mark.parametrize(
    "word", ["Freudien", "Freudienne", "Freudiens", "Freudiano", "Freudian"]
)
def test_romance_adjective_forms_are_candidates(lex, word):
    xml = _tei(f"<p>Un concept {word} bleibt.</p>")
    cands = em.find_candidates(xml, lex)
    assert [c["surface"] for c in cands] == [word]
    assert cands[0]["rule"] == "adjective-form"
    assert cands[0]["tier"] == 2


# --- single-word title shadowing a surname (fix package 6) -------------------------


def test_single_word_title_that_shadows_a_surname_is_ambiguous(tmp_path):
    lexicon = _build(
        tmp_path,
        persons=[_person("118587943", "Nietzsche, Friedrich")],
        works=[_work("1078795312", "Nietzsche")],
    )
    xml = _tei("<p>In Nietzsche steht es.</p>")
    cands = em.find_candidates(xml, lexicon)
    assert len(cands) == 1
    assert cands[0]["rule"] == "short-title:ambiguous"
    assert cands[0]["tier"] == 2
    # both candidates stay reconstructible for the judge stage
    assert lexicon["forms"]["Nietzsche"] == (("1078795312", "work", "short-title", "headword"),)
    assert lexicon["surnames"]["Nietzsche"] == ("118587943",)
    assert cands[0]["alternatives"] == ["1078795312", "118587943"]


# --- all-caps mentions (fix package 4) --------------------------------------------


def test_caps_full_name_is_tier1(lex):
    xml = _tei("<head>UNE PHILOSOPHIE DE L'EXISTENCE: KARL JASPERS</head>")
    cands = em.find_candidates(xml, lex)
    assert [c["surface"] for c in cands] == ["KARL JASPERS"]
    assert cands[0]["rule"] == "caps-full-name"
    assert cands[0]["tier"] == 1
    assert cands[0]["gid"] == "118557106"


def test_caps_surname_alone_is_tier2(lex):
    xml = _tei("<p>HERSCH antwortete.</p>")
    cands = em.find_candidates(xml, lex)
    assert [c["surface"] for c in cands] == ["HERSCH"]
    assert cands[0]["rule"] == "caps-surname"
    assert cands[0]["tier"] == 2
    assert cands[0]["gid"] == "118708422"


def test_caps_hits_of_the_document_author_are_skipped(lex):
    xml = _tei("<p>JEANNE HERSCH</p>\n<p>HERSCH und KARL JASPERS.</p>")
    assert [c["surface"] for c in em.find_candidates(xml, lex)] == [
        "JEANNE HERSCH",
        "HERSCH",
        "KARL JASPERS",
    ]
    skipped = em.find_candidates(xml, lex, author_labels=("Hersch, Jeanne",))
    assert [c["surface"] for c in skipped] == ["KARL JASPERS"]


def test_author_exception_applies_only_to_caps_hits(lex):
    xml = _tei("<p>Jeanne Hersch schrieb.</p>")
    cands = em.find_candidates(xml, lex, author_labels=("Hersch, Jeanne",))
    assert [c["rule"] for c in cands] == ["full-name"]
    assert cands[0]["tier"] == 1


# --- apparatus zone (fix package 5) -----------------------------------------------

COVER_SHEET = (
    '<pb n="1"/>'
    "<p>Zeitschrift: Schweizerische Lehrerzeitung</p>"
    "<p>Herausgeber: UNESCO</p>"
    "<p>Band: 105</p>"
    "<p>Heft: 3</p>"
    '<pb n="2"/>'
    "<p>Karl Jaspers schrieb.</p>"
)


def test_e_periodica_cover_sheet_is_excluded(lex):
    xml = _tei(COVER_SHEET)
    assert [c["surface"] for c in em.find_candidates(xml, lex)] == ["Karl Jaspers"]


def test_two_cover_fields_are_not_enough(lex):
    xml = _tei(
        '<pb n="1"/>\n<p>Band: 105</p>\n<p>Herausgeber: UNESCO</p>\n'
        '<pb n="2"/>\n<p>Weiter im Text.</p>'
    )
    assert [c["surface"] for c in em.find_candidates(xml, lex)] == ["UNESCO"]


@pytest.mark.parametrize("prefix", ["Porträts:", "Fotos:"])
def test_photo_credit_paragraph_is_excluded(lex, prefix):
    xml = _tei(f"<p>{prefix} Karl Jaspers, Basel.</p><p>Jeanne Hersch schrieb.</p>")
    assert [c["surface"] for c in em.find_candidates(xml, lex)] == ["Jeanne Hersch"]


# --- alternatives: every bearer of an ambiguous form (iteration 4, point 1) ---------


def test_bare_surname_with_several_bearers_names_them_all(lex):
    xml = _tei("<p>Dazu meinte Jaspers nichts.</p>")
    cands = em.find_candidates(xml, lex)
    assert len(cands) == 1
    assert cands[0]["rule"] == "bare-surname:ambiguous"
    assert cands[0]["tier"] == 2
    assert cands[0]["alternatives"] == ["118557106", "118557107"]
    assert cands[0]["gid"] in cands[0]["alternatives"]


def test_unique_candidate_carries_an_empty_alternatives_list(lex):
    cands = em.find_candidates(_tei("<p>Jeanne Hersch schrieb.</p>"), lex)
    assert cands[0]["alternatives"] == []


def test_anchored_surname_stays_decided_but_lists_the_bearers(lex):
    xml = _tei("<p>Karl Jaspers schrieb.</p><p>Spaeter meinte Jaspers dazu nichts.</p>")
    cands = em.find_candidates(xml, lex)
    assert cands[1]["rule"] == "anchored-surname"
    assert cands[1]["tier"] == 1
    assert cands[1]["gid"] == "118557106"
    # the anchor decided among the two bearers; the alternatives stay visible
    assert cands[1]["alternatives"] == ["118557106", "118557107"]


def test_collided_anchor_lists_the_bearers(lex):
    xml = _tei("<p>Karl Jaspers und Gertrud Jaspers.</p><p>Jaspers antwortete.</p>")
    cands = em.find_candidates(xml, lex)
    assert cands[-1]["rule"] == "ambiguous-surname"
    assert cands[-1]["alternatives"] == ["118557106", "118557107"]


def test_caps_surname_with_several_bearers_is_ambiguous(lex):
    cands = em.find_candidates(_tei("<p>Dazu meinte JASPERS nichts.</p>"), lex)
    assert cands[0]["rule"] == "caps-surname:ambiguous"
    assert cands[0]["alternatives"] == ["118557106", "118557107"]


# --- provenance of the matched form (iteration 4, point 2) -------------------------


def test_headword_hit_reports_the_curated_form(lex):
    cands = em.find_candidates(_tei("<p>Hier spricht Karl Jaspers.</p>"), lex)
    assert cands[0]["matched_form"] == "Karl Jaspers"
    assert cands[0]["form_source"] == "headword"


def test_cache_variant_hit_reports_the_variant(lex):
    cands = em.find_candidates(_tei("<p>Von Karl Theodor Jaspers stammt es.</p>"), lex)
    assert cands[0]["matched_form"] == "Karl Theodor Jaspers"
    assert cands[0]["form_source"] == "cache-variant"


def test_curated_surname_hit_reports_the_surname_index(lex):
    cands = em.find_candidates(_tei("<p>Pour Marcel, la question reste.</p>"), lex)
    assert cands[0]["matched_form"] == "Marcel"
    assert cands[0]["form_source"] == "surname-index"


def test_surname_from_a_cache_variant_names_the_variant(tmp_path):
    # ids and variant forms from data/entities/all_entities.json and its GND cache
    cache = {"117085391": _cache_entry("Jaspers, Gertrud", ("Mayer, Gertrud",))}
    lexicon = _build(tmp_path, persons=[_person("117085391", "Jaspers, Gertrud")], cache=cache)
    cands = em.find_candidates(_tei("<p>Der Kritiker Hans Mayer schrieb.</p>"), lexicon)
    assert [c["surface"] for c in cands] == ["Mayer"]
    assert cands[0]["matched_form"] == "Mayer, Gertrud"
    assert cands[0]["form_source"] == "cache-variant"


def test_legacy_form_hit_reports_the_legacy_index(tmp_path):
    lexicon = _build(tmp_path, persons=PERSONS, cache=CACHE, legacy=LEGACY_JEREMIE)
    found = _by_surface(em.find_candidates(_tei("<p>Er zitierte Jérémie.</p>"), lexicon))
    assert found["Jérémie"]["form_source"] == "legacy"
    assert found["Jérémie"]["matched_form"] == "Jérémie"


def test_org_and_work_hits_report_their_headword(lex):
    xml = _tei("<p>An der UNESCO las er Allgemeine Psychopathologie.</p>")
    cands = em.find_candidates(xml, lex)
    assert [(c["matched_form"], c["form_source"]) for c in cands] == [
        ("UNESCO", "headword"),
        ("Allgemeine Psychopathologie", "headword"),
    ]


# --- bigram refinement of the suspicion signal (iteration 4, point 3) --------------


def test_known_forename_neighbour_no_longer_suppresses_the_signal(lex):
    # "Jean" starts listed forms (Jean Wahl, Jean Alembert), but "Jean Marcel" is none
    xml = _tei("<p>Der Fotograf Jean Marcel kam.</p>")
    cands = em.find_candidates(xml, lex)
    assert [c["surface"] for c in cands] == ["Marcel"]
    assert cands[0]["rule"] == "bare-surname:suspect"
    assert cands[0]["tier"] == 2


def test_a_known_word_pair_still_suppresses_the_signal(tmp_path):
    # the scan consumes "Jean Paul" as a full name, so "Sartre" reaches the surname
    # rule with a capitalized neighbour whose pair IS a listed form
    lexicon = _build(
        tmp_path,
        persons=[_person("118591053", "Paul, Jean"), _person("118605690", "Sartre, Paul")],
    )
    cands = em.find_candidates(_tei("<p>Zitiert nach Jean Paul Sartre und mehr.</p>"), lexicon)
    assert [c["surface"] for c in cands] == ["Jean Paul", "Sartre"]
    assert cands[1]["rule"] == "bare-surname"


def test_ambiguity_suffix_precedes_the_suspicion_suffix(lex):
    xml = _tei("<p>Der Jaspers-Kreis tagte.</p>")
    cands = em.find_candidates(xml, lex)
    assert cands[0]["rule"] == "bare-surname:ambiguous:suspect"
    assert cands[0]["tier"] == 2
    assert cands[0]["alternatives"] == ["118557106", "118557107"]


def test_full_name_hit_keeps_ignoring_the_neighbour_signals(lex):
    # counter-check to the bigram change: a full name stays tier 1
    cands = em.find_candidates(_tei("<p>Der Philosoph Karl Jaspers Duchamp.</p>"), lex)
    assert [c["rule"] for c in cands] == ["full-name"]
    assert cands[0]["tier"] == 1


# --- case-tolerant multiword forms (iteration 5) -----------------------------------
#
# Specification of the rule under test:
#   1. A form of at least two tokens matches even when only letter case differs. The
#      one-token forms keep the exact rules, because there the collision with ordinary
#      vocabulary is the known failure mode.
#   2. Tolerance covers letter case only. Diacritics, punctuation and whitespace stay
#      exact.
#   3. matched_form stays the lexicon form, surface is the text as it stands, and
#      form_source stays the source of that form.
#   4. Rule and tier are the ones the exact hit of the same form carries.
#   5. All-caps person surfaces stay with the caps channel, which carries the byline
#      exception of the document author, and a case-deviating writing of the author's
#      own name is skipped like an all-caps one.
#   6. A capitalized form written all in lower case is tier 2 with the ":suspect"
#      suffix; the corpus sets "le capital" as ordinary prose far more often than as
#      the listed title.


def test_multiword_work_title_matches_across_case(lex):
    xml = _tei("<p>Er las Allgemeine psychopathologie im Original.</p>")
    cands = em.find_candidates(xml, lex)
    assert [c["surface"] for c in cands] == ["Allgemeine psychopathologie"]
    assert cands[0]["matched_form"] == "Allgemeine Psychopathologie"
    assert cands[0]["form_source"] == "headword"
    assert cands[0]["rule"] == "work-title"
    assert cands[0]["tier"] == 1
    assert xml[cands[0]["start"]:cands[0]["end"]] == cands[0]["surface"]


def test_multiword_cache_variant_matches_across_case(tmp_path):
    # doc 2330: the cache carries "La foi philosophique", the text sets "La Foi philosophique"
    cache = {"1088013937": _cache_entry("Der philosophische Glaube", ("La foi philosophique",))}
    lexicon = _build(
        tmp_path, works=[_work("1088013937", "Der philosophische Glaube")], cache=cache
    )
    cands = em.find_candidates(_tei("<p>Sie uebersetzte La Foi philosophique.</p>"), lexicon)
    assert [c["surface"] for c in cands] == ["La Foi philosophique"]
    assert cands[0]["matched_form"] == "La foi philosophique"
    assert cands[0]["form_source"] == "cache-variant"
    assert cands[0]["rule"] == "work-variant"
    assert cands[0]["tier"] == 1


def test_multiword_org_name_matches_across_case(lex):
    cands = em.find_candidates(_tei("<p>Der deutscher Gewerkschaftsbund tagte.</p>"), lex)
    assert [c["surface"] for c in cands] == ["deutscher Gewerkschaftsbund"]
    assert cands[0]["matched_form"] == "Deutscher Gewerkschaftsbund"
    assert cands[0]["rule"] == "org-name"


def test_one_word_title_keeps_the_exact_rules(lex):
    # the known failure mode of one-word titles is the collision with ordinary
    # vocabulary; case tolerance would multiply it
    assert em.find_candidates(_tei("<p>In der bibel steht es.</p>"), lex) == []
    assert em.find_candidates(_tei("<p>In der BIBEL steht es.</p>"), lex) == []


def test_one_word_org_token_keeps_the_exact_rules(lex):
    # the case-tolerant channel stays out of one-token forms; the capitalized spelling
    # of an acronym is the separate worklist channel below, never a tier-1 hit
    assert em.find_candidates(_tei("<p>Die Abteilung an der unesco.</p>"), lex) == []
    cands = em.find_candidates(_tei("<p>Die Abteilung an der Unesco.</p>"), lex)
    assert [c["rule"] for c in cands] == ["org-token:acronym-case"]
    assert cands[0]["tier"] == 2


def test_case_tolerance_does_not_reach_diacritics(tmp_path):
    lexicon = _build(tmp_path, works=[_work("1088026605", "Idéologies et réalité")])
    assert em.find_candidates(_tei("<p>Er las Ideologies et realite.</p>"), lexicon) == []
    cands = em.find_candidates(_tei("<p>Er las idéologies et Réalité.</p>"), lexicon)
    assert [c["surface"] for c in cands] == ["idéologies et Réalité"]


def test_case_tolerance_does_not_reach_punctuation_or_whitespace(tmp_path):
    lexicon = _build(tmp_path, persons=[_person("118557106", "Jaspers, Karl")])
    assert em.find_candidates(_tei("<p>Zitiert nach jaspers karl.</p>"), lexicon) == []


def test_case_tolerant_hit_stays_inside_the_word_boundary(lex):
    xml = _tei("<p>Er las Allgemeine psychopathologien im Original.</p>")
    assert em.find_candidates(xml, lex) == []


def test_all_lowercase_writing_of_a_title_is_suspect(tmp_path):
    # "le capital" is the ordinary noun phrase far more often than the listed work
    lexicon = _build(tmp_path, works=[_work("4099309-7", "Le capital")])
    cands = em.find_candidates(_tei("<p>Der Zins auf le capital steigt.</p>"), lexicon)
    assert [c["surface"] for c in cands] == ["le capital"]
    assert cands[0]["rule"] == "work-title:suspect"
    assert cands[0]["tier"] == 2
    # one capital is enough to make it a title mention again
    kept = em.find_candidates(_tei("<p>Er las Le Capital von Marx.</p>"), lexicon)
    assert kept[0]["rule"] == "work-title"
    assert kept[0]["tier"] == 1


def test_case_deviating_hit_on_the_document_author_is_skipped(lex):
    # the corpus sets the byline as "Jeanne HERSCH"; bylines stay unmarked
    xml = _tei("<p>Jeanne HERSCH</p>\n<p>Dazu schrieb Jeanne Hersch spaeter mehr.</p>")
    cands = em.find_candidates(xml, lex, author_labels=("Hersch, Jeanne",))
    assert [c["surface"] for c in cands] == ["Jeanne Hersch"]
    # without the author metadata the same byline is a normal full-name hit
    assert [c["surface"] for c in em.find_candidates(xml, lex)] == [
        "Jeanne HERSCH",
        "Jeanne Hersch",
    ]


# --- typographic evidence of one-word titles (iteration 4, point 4) ----------------


def test_short_title_inside_hi_is_typographic(lex):
    xml = _tei('<p>In der <hi rendition="#i">Bibel</hi> steht es.</p>')
    cands = em.find_candidates(xml, lex)
    assert cands[0]["rule"] == "short-title"
    assert cands[0]["evidence"] == "typographic"


@pytest.mark.parametrize(("open_q", "close_q"), [('"', '"'), ("\u00ab", "\u00bb"),
                                                 ("\u201e", "\u201c")])
def test_short_title_in_quotes_is_typographic(lex, open_q, close_q):
    xml = _tei(f"<p>In der {open_q}Bibel{close_q} steht es.</p>")
    cands = em.find_candidates(xml, lex)
    assert cands[0]["surface"] == "Bibel"
    assert cands[0]["evidence"] == "typographic"


@pytest.mark.parametrize("possessive", ["sa", "son", "ses", "seine", "seiner", "his", "her"])
def test_short_title_behind_a_possessive_is_typographic(lex, possessive):
    cands = em.find_candidates(_tei(f"<p>Er las {possessive} Bibel laut.</p>"), lex)
    assert cands[0]["evidence"] == "typographic"


def test_short_title_without_a_signal_has_no_evidence(lex):
    cands = em.find_candidates(_tei("<p>In der Bibel steht es.</p>"), lex)
    assert cands[0]["rule"] == "short-title"
    assert cands[0]["tier"] == 2
    assert cands[0]["evidence"] == "none"


def test_evidence_stays_on_the_one_word_titles(lex):
    xml = _tei('<p>Er las <hi rendition="#i">Allgemeine Psychopathologie</hi> und Jaspers.</p>')
    for cand in em.find_candidates(xml, lex):
        assert "evidence" not in cand


def test_evidence_survives_the_ambiguity_suffix(tmp_path):
    lexicon = _build(
        tmp_path,
        persons=[_person("118587943", "Nietzsche, Friedrich")],
        works=[_work("1078795312", "Nietzsche")],
    )
    xml = _tei('<p>In <hi rendition="#i">Nietzsche</hi> steht es.</p>')
    cands = em.find_candidates(xml, lexicon)
    assert cands[0]["rule"] == "short-title:ambiguous"
    assert cands[0]["evidence"] == "typographic"


# --- variant review (operator-gated verdicts over the cache channel) ----------------


def _freud_fixture(tmp_path, review):
    return _build(
        tmp_path,
        persons=[_person("118535749", "Freud, Sigmund")],
        cache={"118535749": _cache_entry("Freud, Sigmund", ("Freund, Sigmund",))},
        review=review,
    )


def test_review_reject_drops_cache_form_and_its_surname(tmp_path):
    review = _review(persons=_verdicts("118535749", "Freud, Sigmund",
                                       {"Freud, Sigmund": "approve",
                                        "Freund, Sigmund": "reject"}))
    lexicon = _freud_fixture(tmp_path, review)
    assert "Sigmund Freund" not in lexicon["forms"]
    assert "Freund, Sigmund" not in lexicon["forms"]
    assert "Freund" not in lexicon["surnames"]
    assert "Sigmund Freud" in lexicon["forms"]
    assert "Freud" in lexicon["surnames"]
    assert lexicon["skipped"]["review_reject"] == 1


def test_review_absent_keeps_the_cache_form(tmp_path):
    lexicon = _freud_fixture(tmp_path, review=None)
    assert "Sigmund Freund" in lexicon["forms"]
    assert "Freund" in lexicon["surnames"]


def test_review_suspect_demotes_variant_hit_to_tier2(tmp_path):
    review = _review(persons=_verdicts("118519778", "Voltaire",
                                       {"Voltaire": "approve",
                                        "Akakia, Docteur": "suspect"}))
    lexicon = _build(
        tmp_path,
        persons=[_person("118519778", "Voltaire")],
        cache={"118519778": _cache_entry("Voltaire", ("Akakia, Docteur",))},
        review=review,
    )
    cands = em.find_candidates(_tei("<p>Docteur Akakia schrieb den Brief.</p>"), lexicon)
    assert cands[0]["rule"] == "variant-full-name:suspect"
    assert cands[0]["tier"] == 2


def test_review_unreviewed_cache_form_counts_as_suspect(tmp_path):
    review = _review(persons=_verdicts("118557106", "Jaspers, Karl",
                                       {"Jaspers, Karl": "approve"}))
    lexicon = _build(
        tmp_path,
        persons=[_person("118557106", "Jaspers, Karl")],
        cache={"118557106": _cache_entry("Jaspers, Karl", ("Jaspers, Karl Theodor",))},
        review=review,
    )
    cands = em.find_candidates(_tei("<p>Karl Theodor Jaspers sprach.</p>"), lexicon)
    assert cands[0]["rule"] == "variant-full-name:suspect"
    assert cands[0]["tier"] == 2


def test_review_reject_leaves_the_headword_channel_untouched(tmp_path):
    review = _review(persons=_verdicts("118557106", "Jaspers, Karl",
                                       {"Jaspers, Karl": "reject"}))
    lexicon = _build(
        tmp_path,
        persons=[_person("118557106", "Jaspers, Karl")],
        cache={"118557106": _cache_entry("Jaspers, Karl", ())},
        review=review,
    )
    cands = em.find_candidates(_tei("<p>Karl Jaspers sprach.</p>"), lexicon)
    assert cands[0]["rule"] == "full-name"
    assert cands[0]["tier"] == 1


def test_review_suspect_covers_the_caps_projection(tmp_path):
    review = _review(persons=_verdicts("118519778", "Voltaire",
                                       {"Voltaire": "approve",
                                        "Akakia, Docteur": "suspect"}))
    lexicon = _build(
        tmp_path,
        persons=[_person("118519778", "Voltaire")],
        cache={"118519778": _cache_entry("Voltaire", ("Akakia, Docteur",))},
        review=review,
    )
    cands = em.find_candidates(_tei("<p>von DOCTEUR AKAKIA unterzeichnet.</p>"), lexicon)
    assert cands[0]["rule"] == "caps-full-name:suspect"
    assert cands[0]["tier"] == 2


# --- derived form channels (recall gaps of the facsimile-adjudicated evaluation) ----
#
# Each channel registers additional lexicon forms for a listed entity and is
# worklist-only: its rule carries a suffix, and a suffixed lexicon rule is tier 2 by
# construction. Ids and name forms come from data/entities/all_entities.json and its
# GND cache.

UNESCO = _org("2023755-8", "UNESCO")
POPULAIRE = _work("4676707-1", "Le populaire de Paris (Zeitung)")
POPULAIRE_CACHE = {
    "4676707-1": _cache_entry(
        "Le populaire de Paris (Zeitung)",
        ("Le populaire (Zeitung, Paris, 1916-1940)",),
    )
}
BUND_LABEL = "Allgemeiner Jüdischer Arbeiterbund in Litauen, Polen und Rußland"
BUND = _org("5005966-X", BUND_LABEL)
BUND_CACHE = {"5005966-X": _cache_entry(BUND_LABEL, (f"Bund ({BUND_LABEL})",))}
GENEVE = _org("1010450-1", "Université de Genève")
GENEVE_CACHE = {
    "1010450-1": _cache_entry("Université de Genève", ("Universität Genf",))
}
NIETZSCHE = _person("118587943", "Nietzsche, Friedrich")
JASPERS = _person("118557106", "Jaspers, Karl")


# --- acronym case tolerance -------------------------------------------------------


def test_acronym_case_form_is_a_worklist_candidate(tmp_path):
    lexicon = _build(tmp_path, orgs=[UNESCO])
    cands = em.find_candidates(_tei("<p>Ein Bericht der l'Unesco aus Paris.</p>"), lexicon)
    assert [c["surface"] for c in cands] == ["Unesco"]
    assert cands[0]["rule"] == "org-token:acronym-case"
    assert cands[0]["tier"] == 2
    assert cands[0]["gid"] == "2023755-8"
    assert cands[0]["matched_form"] == "Unesco"


def test_acronym_all_caps_writing_keeps_its_tier(tmp_path):
    lexicon = _build(tmp_path, orgs=[UNESCO])
    cands = em.find_candidates(_tei("<p>Ein Bericht der UNESCO aus Paris.</p>"), lexicon)
    assert cands[0]["rule"] == "org-token"
    assert cands[0]["tier"] == 1


def test_acronym_case_does_not_reach_the_lowercase_writing(tmp_path):
    lexicon = _build(tmp_path, orgs=[UNESCO])
    assert em.find_candidates(_tei("<p>Ein Bericht der unesco.</p>"), lexicon) == []


def test_short_acronym_gets_no_case_form(lex):
    # "UNO" already misses the length guard of the org token; no channel resurrects it
    assert "Uno" not in lex["forms"]


def test_dotted_acronym_gets_no_case_form(tmp_path):
    # "C.E.E." capitalizes to "C.e.e.", a spelling no text carries
    legacy = {"organizations": {"35433": {"names": ["C.E.E."]}}}
    lexicon = _build(
        tmp_path, orgs=[_org("35433-8", "Europäische Wirtschaftsgemeinschaft")],
        legacy=legacy,
    )
    assert "C.E.E." in lexicon["forms"]
    assert "C.e.e." not in lexicon["forms"]


# --- qualifier strip --------------------------------------------------------------


def test_qualifier_strip_registers_the_bare_title(tmp_path):
    lexicon = _build(tmp_path, works=[POPULAIRE], cache=POPULAIRE_CACHE)
    xml = _tei("<p>Er schrieb im Le populaire ueber Europa.</p>")
    cands = em.find_candidates(xml, lexicon)
    assert [c["surface"] for c in cands] == ["Le populaire"]
    assert cands[0]["rule"] == "work-variant:qualifier-strip"
    assert cands[0]["tier"] == 2
    assert cands[0]["gid"] == "4676707-1"


def test_qualifier_strip_reaches_the_case_tolerant_channel(tmp_path):
    # the corpus sets "Le Populaire", the GND variant carries the lower-case spelling
    lexicon = _build(tmp_path, works=[POPULAIRE], cache=POPULAIRE_CACHE)
    cands = em.find_candidates(_tei("<p>Er schrieb im Le Populaire ueber Europa.</p>"), lexicon)
    assert [c["surface"] for c in cands] == ["Le Populaire"]
    assert cands[0]["matched_form"] == "Le populaire"
    assert cands[0]["tier"] == 2


def test_qualifier_strip_of_a_generic_word_stays_on_the_worklist(tmp_path):
    # "Bund" is an ordinary German word; the channel carries it because it is
    # worklist-only and never auto-marks
    lexicon = _build(tmp_path, orgs=[BUND], cache=BUND_CACHE)
    cands = em.find_candidates(_tei("<p>Der Bund berichtete darueber.</p>"), lexicon)
    assert [c["surface"] for c in cands] == ["Bund"]
    assert cands[0]["rule"] == "org-variant:qualifier-strip"
    assert cands[0]["tier"] == 2
    assert cands[0]["gid"] == "5005966-X"


def test_qualifier_strip_needs_length_and_a_capital(tmp_path):
    # the head must carry the distinctiveness the org token rule asks for; the two
    # variant shapes are synthetic, the id is the listed one
    cache = {
        "4676707-1": _cache_entry(
            "Le populaire de Paris (Zeitung)", ("Pop (Zeitung)", "populaire (Zeitung)")
        )
    }
    lexicon = _build(tmp_path, works=[POPULAIRE], cache=cache)
    assert "Pop" not in lexicon["forms"]
    assert "populaire" not in lexicon["forms"]


def test_a_rejected_cache_form_has_no_derived_form(tmp_path):
    # the variant review governs the cache channel; a rejected form must not resurrect
    review = _review(works=_verdicts(
        "4676707-1", "Le populaire de Paris (Zeitung)",
        {"Le populaire de Paris (Zeitung)": "approve",
         "Le populaire (Zeitung, Paris, 1916-1940)": "reject"},
    ))
    lexicon = _build(tmp_path, works=[POPULAIRE], cache=POPULAIRE_CACHE, review=review)
    assert "Le populaire" not in lexicon["forms"]
    assert "Le populaire de Paris" in lexicon["forms"]


# --- adjectival place inversion ---------------------------------------------------


def test_place_adjective_inversion_is_a_worklist_candidate(tmp_path):
    lexicon = _build(tmp_path, orgs=[GENEVE], cache=GENEVE_CACHE)
    xml = _tei("<p>Sie lehrte an der Genfer Universität weiter.</p>")
    cands = em.find_candidates(xml, lexicon)
    assert [c["surface"] for c in cands] == ["Genfer Universität"]
    assert cands[0]["rule"] == "org-variant:place-adjective"
    assert cands[0]["tier"] == 2
    assert cands[0]["gid"] == "1010450-1"
    assert cands[0]["matched_form"] == "Genfer Universität"


def test_place_adjective_leaves_the_listed_form_at_its_tier(tmp_path):
    lexicon = _build(tmp_path, orgs=[GENEVE], cache=GENEVE_CACHE)
    cands = em.find_candidates(_tei("<p>Die Universität Genf lud ein.</p>"), lexicon)
    assert cands[0]["rule"] == "org-variant"
    assert cands[0]["tier"] == 1


def test_place_adjective_table_stays_static(tmp_path):
    # no generative morphology: a place outside the table derives nothing, and
    # Lausanne has no German adjective at all
    assert "Lausanne" not in em.PLACE_ADJECTIVES
    lexicon = _build(tmp_path, orgs=[_org("2024349-2", "Universität Heidelberg")])
    assert not any(form.startswith("Heidelberger") for form in lexicon["forms"])


# --- word boundary before superscript footnote digits ------------------------------


@pytest.mark.parametrize("mark", ["²", "³", "¹"])
def test_superscript_footnote_digit_ends_the_word(tmp_path, mark):
    lexicon = _build(tmp_path, persons=[NIETZSCHE])
    xml = _tei(f"<p>So steht es bei Nietzsche{mark} nachzulesen.</p>")
    cands = em.find_candidates(xml, lexicon)
    assert [c["surface"] for c in cands] == ["Nietzsche"]
    assert cands[0]["rule"] == "bare-surname"
    assert cands[0]["tier"] == 2
    assert xml[cands[0]["start"]:cands[0]["end"]] == cands[0]["surface"]


def test_superscript_marker_matches_like_a_comma(tmp_path):
    lexicon = _build(tmp_path, persons=[NIETZSCHE])
    with_comma = em.find_candidates(
        _tei("<p>So steht es bei Nietzsche, wie bekannt.</p>"), lexicon
    )
    with_mark = em.find_candidates(
        _tei("<p>So steht es bei Nietzsche² wie bekannt.</p>"), lexicon
    )
    assert [(c["surface"], c["rule"], c["tier"]) for c in with_comma] == [
        (c["surface"], c["rule"], c["tier"]) for c in with_mark
    ]


def test_an_ordinary_digit_still_binds_the_word(tmp_path):
    # the fix is a boundary fix for superscript markers, not a general digit rule
    lexicon = _build(tmp_path, persons=[NIETZSCHE])
    assert em.find_candidates(_tei("<p>Die Datei Nietzsche2 liegt bereit.</p>"), lexicon) == []


# --- person initials --------------------------------------------------------------


def test_person_initials_enter_the_lexicon_as_derived_forms(tmp_path):
    lexicon = _build(tmp_path, persons=[JASPERS])
    assert lexicon["forms"]["K.J."] == (
        ("118557106", "person", "full-name:initials", "headword"),
    )
    assert lexicon["forms"]["K. J."][0][2] == "full-name:initials"
    assert "K.J." not in lexicon["surnames"]


@pytest.mark.parametrize("surface", ["K.J.", "K. J."])
def test_interview_initials_are_worklist_candidates(tmp_path, surface):
    lexicon = _build(tmp_path, persons=[JASPERS])
    xml = _tei(f"<sp><speaker>{surface}</speaker><p>Ja, gewiss.</p></sp>")
    cands = em.find_candidates(xml, lexicon)
    assert [c["surface"] for c in cands] == [surface]
    assert cands[0]["rule"] == "full-name:initials"
    assert cands[0]["tier"] == 2
    assert cands[0]["gid"] == "118557106"


def test_initials_need_both_letters(tmp_path):
    # a mononym has no forename, so the channel produces nothing
    lexicon = _build(tmp_path, persons=[_person("118594893", "Plato")])
    assert all(":initials" not in owner[2]
               for owners in lexicon["forms"].values() for owner in owners)


def test_shared_initials_produce_a_multi_owner_candidate(tmp_path):
    lexicon = _build(tmp_path, persons=[
        _person("118507184", "Baudelaire, Charles"),
        _person("123159296", "Baudouin, Charles"),
    ])
    cands = em.find_candidates(_tei("<p>C.B. antwortete darauf.</p>"), lexicon)
    assert cands[0]["rule"] == "full-name:initials:ambiguous"
    assert cands[0]["tier"] == 2
    assert cands[0]["alternatives"] == ["118507184", "123159296"]


def test_initials_hit_never_anchors_a_bare_surname(tmp_path):
    lexicon = _build(tmp_path, persons=[JASPERS])
    xml = _tei("<p>K.J. sagte es.</p><p>Spaeter meinte Jaspers dazu nichts.</p>")
    cands = em.find_candidates(xml, lexicon)
    assert [c["rule"] for c in cands] == ["full-name:initials", "bare-surname"]
    assert all(c["tier"] == 2 for c in cands)


# --- tier guarantee of the derived channels ---------------------------------------


def test_speaker_slot_never_promotes_a_derived_form(tmp_path):
    # the speaker rule is tier 1; a derived form must not reach it. "Eckhardus" comes
    # from the cache variant "Eckhardus (Magister)" and is no listed surname.
    lexicon = _build(
        tmp_path,
        persons=[_person("118528823", "Eckhart, Meister")],
        cache={"118528823": _cache_entry("Eckhart, Meister", ("Eckhardus (Magister)",))},
    )
    cands = em.find_candidates(_tei("<sp><speaker>Eckhardus:</speaker><p>Ja.</p></sp>"), lexicon)
    assert [c["surface"] for c in cands] == ["Eckhardus"]
    assert cands[0]["rule"] == "variant-full-name:qualifier-strip"
    assert cands[0]["tier"] == 2


def test_a_derived_form_never_displaces_a_surname(tmp_path):
    # "Eckhart (Meister)" strips to the listed surname, which an anchor reads at
    # tier 1; the channel adds recall and must not cost that reading
    lexicon = _build(
        tmp_path,
        persons=[_person("118528823", "Eckhart, Meister")],
        cache={"118528823": _cache_entry("Eckhart, Meister", ("Eckhart (Meister)",))},
    )
    assert lexicon["surnames"]["Eckhart"] == ("118528823",)
    assert "Eckhart" not in lexicon["forms"]
    xml = _tei("<p>Meister Eckhart schrieb.</p><p>Dazu meinte Eckhart nichts.</p>")
    cands = em.find_candidates(xml, lexicon)
    assert [c["rule"] for c in cands] == ["full-name", "anchored-surname"]
    assert all(c["tier"] == 1 for c in cands)


def _derived_lexicon(tmp_path):
    return _build(
        tmp_path,
        persons=[JASPERS, NIETZSCHE],
        orgs=[UNESCO, GENEVE, BUND],
        works=[POPULAIRE],
        cache={**GENEVE_CACHE, **BUND_CACHE, **POPULAIRE_CACHE},
    )


def test_no_derived_form_reaches_a_tier1_index(tmp_path):
    lexicon = _derived_lexicon(tmp_path)
    derived = {form for form, owners in lexicon["forms"].items()
               if any(":" in owner[2] for owner in owners)}
    assert derived
    assert not derived & set(lexicon["surnames"])
    assert all(":" not in rule
               for owners in lexicon["caps_forms"].values() for _, _, rule, _ in owners)


DERIVED_COMPOSITE = _tei(
    "<p>Ein Bericht der l'Unesco, dazu der Bund.</p>"
    "<p>Sie lehrte an der Genfer Universität.</p>"
    "<p>Im Le populaire stand es, so K.J. weiter.</p>"
)


def test_every_derived_candidate_is_tier2_and_span_exact(tmp_path):
    cands = em.find_candidates(DERIVED_COMPOSITE, _derived_lexicon(tmp_path))
    assert [c["surface"] for c in cands] == [
        "Unesco", "Bund", "Genfer Universität", "Le populaire", "K.J.",
    ]
    for cand in cands:
        assert ":" in cand["rule"]
        assert cand["tier"] == 2
        assert DERIVED_COMPOSITE[cand["start"]:cand["end"]] == cand["surface"]
        assert cand["form_source"] in em.FORM_SOURCES
