"""Tests for the M3 entity pilot preview (scripts/tei/tei_entity_preview).

The preview wraps tier-1 entity candidates in the ZBZ inline GND elements
(persName / orgName / bibl with ref="GND:...") and proves two things about the
result: it is valid against data/schema/zbz_hersch.rng, and the text of the
<text> subtree is character-identical before and after.

All fixtures are synthetic. No test reads output/tei_final, none touches the
network, and none needs scripts/tei/entity_matcher (the matcher is injected as a
plain callable). The only repo file read is the git-tracked RelaxNG schema.
"""

from __future__ import annotations

import json
import re

import pytest

from scripts.tei.tei_entity_preview import (
    PANEL_DOCS,
    apply_candidates,
    build_html_report,
    build_report,
    check_text_invariance,
    discover_doc_ids,
    preview_document,
    run_preview,
    text_signature,
    validate_rng,
)

# --- fixtures ---------------------------------------------------------------

_MINI = (
    '<TEI xmlns="http://www.tei-c.org/ns/1.0"><text><body><div type="text">'
    "<p>Karl Jaspers und Jeanne Hersch.</p>"
    "</div></body></text></TEI>"
)

_MINI_LB = (
    '<TEI xmlns="http://www.tei-c.org/ns/1.0"><text><body><div type="text">'
    '<p>Jeanne <lb break="no"/>Hersch schrieb.</p>'
    "</div></body></text></TEI>"
)

_MINI_MIXED = (
    '<TEI xmlns="http://www.tei-c.org/ns/1.0"><text><body><div type="text">'
    "<p>An der Universitaet Genf ueber Das philosophische Staunen.</p>"
    "</div></body></text></TEI>"
)

# Work title as the complete content of an <hi>: the wrapper belongs outside the hi.
_MINI_HI = (
    '<TEI xmlns="http://www.tei-c.org/ns/1.0"><text><body><div type="text">'
    '<p>In <hi rendition="#i">Das philosophische Staunen</hi> heisst es.</p>'
    "</div></body></text></TEI>"
)

# Same hi, but the title covers only part of its content: the wrapper stays inside.
_MINI_HI_WIDE = (
    '<TEI xmlns="http://www.tei-c.org/ns/1.0"><text><body><div type="text">'
    '<p>In <hi rendition="#i">Das philosophische Staunen, Muenchen 1964</hi>.</p>'
    "</div></body></text></TEI>"
)

_MINI_HI_MIXED = (
    '<TEI xmlns="http://www.tei-c.org/ns/1.0"><text><body><div type="text">'
    '<p>Karl Jaspers schrieb <hi rendition="#i">Von der Wahrheit</hi> und mehr.</p>'
    "</div></body></text></TEI>"
)

_MINI_LB_LEAD = (
    '<TEI xmlns="http://www.tei-c.org/ns/1.0"><text><body><div type="text">'
    "<p><lb/>Karl Jaspers und mehr.</p>"
    "</div></body></text></TEI>"
)

# Minimal delivery-shaped TEI (same header contract as tests/test_tei_schema.py),
# with the mentions still unmarked. Wrapping must leave it schema-valid.
_VALID_DOC = """<?xml version="1.0" encoding="UTF-8"?>
<TEI xmlns="http://www.tei-c.org/ns/1.0" type="naegeli">
  <teiHeader>
    <fileDesc>
      <titleStmt><title type="main">Test</title><author>Hersch, Jeanne</author></titleStmt>
      <publicationStmt><publisher>ZBZ / DHCraft</publisher><idno type="docID">9999</idno></publicationStmt>
      <sourceDesc>
        <biblStruct type="journalArticle">
          <analytic><title>Test</title><author>Hersch, Jeanne</author></analytic>
          <monogr><title>Zeitschrift</title><imprint><date>1975</date></imprint></monogr>
        </biblStruct>
      </sourceDesc>
    </fileDesc>
    <profileDesc><langUsage><language ident="fra"/></langUsage></profileDesc>
    <revisionDesc><change when="2026-08-12" who="pipeline">init</change></revisionDesc>
  </teiHeader>
  <text type="naegeli">
    <body>
      <div type="text">
        <pb facs="#facs_1" n="1"/>
        <p>Karl Jaspers lehrte an der Universitaet Basel.</p>
      </div>
    </body>
  </text>
</TEI>
"""


_VALID_DOC_HI = _VALID_DOC.replace(
    "<p>Karl Jaspers lehrte an der Universitaet Basel.</p>",
    '<p>In <hi rendition="#i">Von der Wahrheit</hi> schreibt Karl Jaspers.</p>',
)


def _cand(xml, surface, gid, category="person", tier=1, rule="full_name", context=None,
          alternatives=(), matched_form=None, form_source="headword", evidence=None):
    """Candidate dict per the entity_matcher contract, offsets taken from the string."""
    start = xml.index(surface)
    cand = {
        "gid": gid,
        "category": category,
        "surface": surface,
        "start": start,
        "end": start + len(surface),
        "tier": tier,
        "rule": rule,
        "alternatives": list(alternatives),
        "matched_form": surface if matched_form is None else matched_form,
        "form_source": form_source,
        "context": surface if context is None else context,
    }
    if evidence is not None:
        cand["evidence"] = evidence
    return cand


# --- apply_candidates -------------------------------------------------------

def test_wraps_tier1_and_ignores_tier2():
    cands = [
        _cand(_MINI, "Karl Jaspers", "118557505"),
        _cand(_MINI, "Jeanne Hersch", "118815679", tier=2, rule="bare_surname"),
    ]
    out = apply_candidates(_MINI, cands)
    assert '<persName ref="GND:118557505">Karl Jaspers</persName>' in out
    assert "Jeanne Hersch." in out
    assert "118815679" not in out


def test_empty_candidates_leave_the_string_untouched():
    assert apply_candidates(_MINI, []) == _MINI
    assert apply_candidates(_MINI, [_cand(_MINI, "Karl Jaspers", "1", tier=2)]) == _MINI


def test_offsets_stay_valid_across_multiple_wraps_in_one_paragraph():
    cands = [
        _cand(_MINI, "Karl Jaspers", "118557505"),
        _cand(_MINI, "Jeanne Hersch", "118815679"),
    ]
    out = apply_candidates(_MINI, cands)
    assert (
        "<p>"
        '<persName ref="GND:118557505">Karl Jaspers</persName>'
        " und "
        '<persName ref="GND:118815679">Jeanne Hersch</persName>'
        ".</p>"
    ) in out


def test_categories_map_to_their_tei_elements():
    cands = [
        _cand(_MINI_MIXED, "Universitaet Genf", "1010450-1",
              category="organisation", rule="org_name"),
        _cand(_MINI_MIXED, "Das philosophische Staunen", "1088036961",
              category="work", rule="work_title"),
    ]
    out = apply_candidates(_MINI_MIXED, cands)
    assert '<orgName ref="GND:1010450-1">Universitaet Genf</orgName>' in out
    assert '<bibl ref="GND:1088036961">Das philosophische Staunen</bibl>' in out


def test_surface_with_embedded_lb_is_wrapped_as_a_whole():
    surface = 'Jeanne <lb break="no"/>Hersch'
    out = apply_candidates(_MINI_LB, [_cand(_MINI_LB, surface, "118815679")])
    assert f'<persName ref="GND:118815679">{surface}</persName>' in out
    assert check_text_invariance(_MINI_LB, out)


# --- bibl outside an existing hi --------------------------------------------


def _work_cand(xml, surface="Das philosophische Staunen", gid="1088036961"):
    return _cand(xml, surface, gid, category="work", rule="work-title")


def test_bibl_wraps_a_fully_covered_hi_from_outside():
    out = apply_candidates(_MINI_HI, [_work_cand(_MINI_HI)])
    assert ('<bibl ref="GND:1088036961">'
            '<hi rendition="#i">Das philosophische Staunen</hi>'
            "</bibl>") in out
    assert '<hi rendition="#i"><bibl' not in out
    assert check_text_invariance(_MINI_HI, out)


def test_partial_hit_inside_an_hi_stays_inside():
    out = apply_candidates(_MINI_HI_WIDE, [_work_cand(_MINI_HI_WIDE)])
    assert ('<hi rendition="#i">'
            '<bibl ref="GND:1088036961">Das philosophische Staunen</bibl>'
            ", Muenchen 1964</hi>") in out
    assert check_text_invariance(_MINI_HI_WIDE, out)


def test_hi_envelope_requires_the_closing_tag_immediately_after_the_span():
    # a trailing space inside the hi means the candidate is not its whole content
    xml = _MINI_HI.replace("Staunen</hi>", "Staunen </hi>")
    out = apply_candidates(xml, [_work_cand(xml)])
    assert '<hi rendition="#i"><bibl ref="GND:1088036961">' in out
    assert check_text_invariance(xml, out)


def test_a_non_hi_neighbour_tag_does_not_trigger_the_outside_wrap():
    out = apply_candidates(_MINI_LB_LEAD, [_cand(_MINI_LB_LEAD, "Karl Jaspers", "118557505")])
    assert '<lb/><persName ref="GND:118557505">Karl Jaspers</persName>' in out


def test_offsets_stay_valid_when_an_hi_wrap_widens_the_span():
    cands = [
        _cand(_MINI_HI_MIXED, "Karl Jaspers", "118557505"),
        _work_cand(_MINI_HI_MIXED, surface="Von der Wahrheit", gid="TEST-0001"),
    ]
    out = apply_candidates(_MINI_HI_MIXED, cands)
    assert '<persName ref="GND:118557505">Karl Jaspers</persName>' in out
    assert ('<bibl ref="GND:TEST-0001"><hi rendition="#i">Von der Wahrheit</hi></bibl>') in out
    assert check_text_invariance(_MINI_HI_MIXED, out)


def test_offset_surface_mismatch_is_rejected():
    bad = _cand(_MINI, "Karl Jaspers", "118557505")
    bad["end"] -= 2  # slice no longer equals the declared surface
    with pytest.raises(ValueError):
        apply_candidates(_MINI, [bad])


def test_overlapping_candidates_are_rejected():
    a = _cand(_MINI, "Karl Jaspers", "118557505")
    b = dict(a, gid="999", surface="Jaspers", start=a["start"] + 5, end=a["end"])
    with pytest.raises(ValueError):
        apply_candidates(_MINI, [a, b])


# --- text invariance --------------------------------------------------------

def test_text_invariance_holds_after_wrapping():
    out = apply_candidates(_MINI, [_cand(_MINI, "Karl Jaspers", "118557505")])
    assert out != _MINI
    assert text_signature(out) == text_signature(_MINI)
    assert check_text_invariance(_MINI, out)


def test_text_invariance_detects_a_manipulated_character():
    out = apply_candidates(_MINI, [_cand(_MINI, "Karl Jaspers", "118557505")])
    manipulated = out.replace("Karl Jaspers", "Karl Jaspars")
    assert not check_text_invariance(_MINI, manipulated)


def test_text_invariance_fails_on_broken_xml():
    assert not check_text_invariance(_MINI, "<TEI><unclosed>")


# --- RelaxNG ----------------------------------------------------------------

def test_wrapped_persname_stays_schema_valid():
    cands = [
        _cand(_VALID_DOC, "Karl Jaspers", "118557505"),
        _cand(_VALID_DOC, "Universitaet Basel", "1010450-1",
              category="organisation", rule="org_name"),
    ]
    out = apply_candidates(_VALID_DOC, cands)
    errors = validate_rng(out)
    assert errors == [], "wrapped preview not valid against zbz_hersch.rng:\n  " + "\n  ".join(errors)
    assert check_text_invariance(_VALID_DOC, out)


def test_bibl_outside_an_hi_stays_schema_valid():
    cands = [
        _cand(_VALID_DOC_HI, "Von der Wahrheit", "TEST-0001", category="work", rule="work-title"),
        _cand(_VALID_DOC_HI, "Karl Jaspers", "118557505"),
    ]
    out = apply_candidates(_VALID_DOC_HI, cands)
    assert '<bibl ref="GND:TEST-0001"><hi rendition="#i">Von der Wahrheit</hi></bibl>' in out
    errors = validate_rng(out)
    assert errors == [], "bibl around hi not valid against zbz_hersch.rng:\n  " + "\n  ".join(errors)
    assert check_text_invariance(_VALID_DOC_HI, out)


def test_validate_rng_reports_an_invalid_document():
    broken = _VALID_DOC.replace("<p>Karl Jaspers", "<nosuchelement/><p>Karl Jaspers")
    assert validate_rng(broken)


# --- per-document preview ---------------------------------------------------

def test_preview_document_writes_outside_tei_final(tmp_path):
    cands = [
        _cand(_VALID_DOC, "Karl Jaspers", "118557505"),
        _cand(_VALID_DOC, "Universitaet Basel", "1010450-1",
              category="organisation", rule="org_name", tier=2),
    ]
    res = preview_document("9999", _VALID_DOC, cands, tmp_path)

    written = tmp_path / "9999_final.xml"
    assert written.exists()
    assert '<persName ref="GND:118557505">' in written.read_text(encoding="utf-8")
    assert res["doc"] == "9999"
    assert res["rng_valid"] is True
    assert res["text_invariant"] is True
    assert [c["gid"] for c in res["wrapped"]] == ["118557505"]
    assert [c["gid"] for c in res["worklist"]] == ["1010450-1"]
    assert res["counts"]["wrapped"] == 1
    assert res["counts"]["worklist"] == 1
    assert res["counts"]["by_rule"] == {"full_name": 1, "org_name": 1}
    assert res["counts"]["by_category"] == {"organisation": 1, "person": 1}


def test_preview_document_flags_a_failed_text_invariance(tmp_path, monkeypatch):
    import scripts.tei.tei_entity_preview as mod

    # a wrapper that also drops a character proves the invariance column has teeth
    monkeypatch.setattr(mod, "apply_candidates",
                        lambda xml, cands: xml.replace("Karl Jaspers", "Karl Jasper"))
    res = mod.preview_document("9999", _VALID_DOC, [], tmp_path)
    assert res["text_invariant"] is False


def test_run_preview_skips_documents_without_a_final_tei(tmp_path):
    src, out = tmp_path / "src", tmp_path / "out"
    src.mkdir()
    (src / "9999_final.xml").write_text(_VALID_DOC, encoding="utf-8")

    def fake_matcher(xml_string, lexicon):
        return [_cand(xml_string, "Karl Jaspers", "118557505")]

    report = run_preview(["9999", "8888"], fake_matcher, {}, src_dir=src, out_dir=out)
    assert [d["doc"] for d in report["documents"]] == ["9999"]
    assert report["totals"]["documents"] == 1
    assert report["totals"]["wrapped"] == 1
    assert report["totals"]["rng_valid"] == 1
    assert report["totals"]["text_invariant"] == 1
    assert not (out / "8888_final.xml").exists()


# --- report -----------------------------------------------------------------

def _results():
    return [
        {"doc": "1060", "wrapped": [_cand(_MINI, "Karl Jaspers", "118557505")],
         "worklist": [_cand(_MINI, "Jeanne Hersch", "118815679", tier=2, rule="bare_surname")],
         "counts": {"wrapped": 1, "worklist": 1,
                    "by_rule": {"full_name": 1, "bare_surname": 1},
                    "by_category": {"person": 2}},
         "rng_valid": True, "text_invariant": True, "rng_errors": [], "output": "x"},
        {"doc": "100", "wrapped": [], "worklist": [],
         "counts": {"wrapped": 0, "worklist": 0, "by_rule": {"full_name": 2}, "by_category": {"work": 2}},
         "rng_valid": False, "text_invariant": True, "rng_errors": ["boom"], "output": "y"},
    ]


def test_report_totals_and_determinism():
    a = build_report(_results())
    b = build_report(_results())
    assert a == b
    assert a["totals"]["documents"] == 2
    assert a["totals"]["wrapped"] == 1
    assert a["totals"]["worklist"] == 1
    assert a["totals"]["rng_valid"] == 1
    assert a["totals"]["text_invariant"] == 2
    assert a["totals"]["by_rule"] == {"full_name": 3, "bare_surname": 1}
    assert a["totals"]["by_category"] == {"person": 2, "work": 2}
    assert json.dumps(a, ensure_ascii=False) == json.dumps(b, ensure_ascii=False)


def test_html_report_is_standalone_and_uses_words_for_status():
    html = build_html_report(build_report(_results()))
    assert html.startswith("<!DOCTYPE html>")
    assert "PASS" in html and "FAIL" in html
    assert "http://" not in html and "https://" not in html  # no external dependency
    assert "Worklist" in html
    for doc in ("1060", "100"):
        assert doc in html


def test_html_report_escapes_markup_in_surfaces():
    results = _results()
    surface = 'Jeanne <lb break="no"/>Hersch'
    results[0]["wrapped"][0]["surface"] = surface
    results[0]["wrapped"][0]["context"] = surface
    html = build_html_report(build_report(results))
    assert "&lt;lb break=&quot;no&quot;/&gt;" in html
    assert '<lb break="no"/>' not in html


def test_panel_is_the_ten_pilot_documents():
    assert PANEL_DOCS == ["1060", "100", "290", "1440", "890", "1350", "1360", "2030", "1220", "3090"]


# --- corpus discovery (--all) ------------------------------------------------

def test_discover_doc_ids_orders_numerically_and_skips_non_final_files(tmp_path):
    for name in ("100_final.xml", "20_final.xml", "1000_final.xml", "20_manifest.json"):
        (tmp_path / name).write_text("x", encoding="utf-8")
    assert discover_doc_ids(tmp_path) == ["20", "100", "1000"]


def test_discover_doc_ids_puts_non_numeric_ids_after_the_numeric_ones(tmp_path):
    for name in ("100_final.xml", "20_final.xml", "beilage_final.xml", "anhang_final.xml"):
        (tmp_path / name).write_text("x", encoding="utf-8")
    assert discover_doc_ids(tmp_path) == ["20", "100", "anhang", "beilage"]


# --- byte fidelity and round trips -------------------------------------------

_WRAPPER_RE = re.compile(r"</?(?:persName|orgName|bibl)(?=[\s>])[^>]*>")


def test_stripping_the_wrappers_restores_the_original_byte_for_byte():
    cands = [
        _cand(_MINI, "Karl Jaspers", "118557505"),
        _cand(_MINI, "Jeanne Hersch", "118815679"),
    ]
    out = apply_candidates(_MINI, cands)
    assert _WRAPPER_RE.sub("", out) == _MINI


def test_stripping_the_wrappers_restores_the_original_across_an_hi_wrap():
    cands = [
        _cand(_MINI_HI_MIXED, "Karl Jaspers", "118557505"),
        _cand(_MINI_HI_MIXED, "Von der Wahrheit", "TEST-0001",
              category="work", rule="work-title"),
    ]
    out = apply_candidates(_MINI_HI_MIXED, cands)
    assert out != _MINI_HI_MIXED
    assert _WRAPPER_RE.sub("", out) == _MINI_HI_MIXED


def test_crlf_line_endings_survive_the_write_path(tmp_path):
    crlf_doc = _VALID_DOC.replace("\n", "\r\n")
    res = preview_document("7777", crlf_doc, [_cand(crlf_doc, "Karl Jaspers", "118557505")],
                           tmp_path)
    raw = (tmp_path / "7777_final.xml").read_bytes()
    assert b"\r\n" in raw
    assert b"\n" not in raw.replace(b"\r\n", b"")  # no stray bare LF introduced
    assert _WRAPPER_RE.sub("", raw.decode("utf-8")) == crlf_doc
    assert res["rng_valid"] is True
    assert res["text_invariant"] is True


def test_end_to_end_with_the_real_matcher_and_idempotence(tmp_path):
    """Integration: real lexicon and matcher; a second pass over the output finds nothing."""
    from scripts.tei.entity_matcher import build_lexicon, find_candidates

    entities = {
        "persons": [{"GND_id": "118557106", "name": "Jaspers, Karl",
                     "listBibl": [{"DNB_link": "https://d-nb.info/gnd/118557106"}],
                     "editor_reviewed": False}],
        "organisations": [{"GND_id": "36146-X", "orgName": "Universitaet Basel",
                           "listBibl": [{"DNB_link": "https://d-nb.info/gnd/36146-X"}],
                           "editor_reviewed": False}],
        "works": [],
    }
    entities_path = tmp_path / "entities.json"
    entities_path.write_text(json.dumps(entities), encoding="utf-8")

    lexicon = build_lexicon(entities_path, tmp_path / "missing_cache.json")
    candidates = find_candidates(_VALID_DOC, lexicon)
    tier1 = [c for c in candidates if c["tier"] == 1]
    assert {c["surface"] for c in tier1} == {"Karl Jaspers", "Universitaet Basel"}

    wrapped = apply_candidates(_VALID_DOC, candidates)
    assert validate_rng(wrapped) == []
    assert check_text_invariance(_VALID_DOC, wrapped)

    second_pass = find_candidates(wrapped, lexicon)
    assert [c for c in second_pass if c["tier"] == 1] == []


# --- ambiguity, provenance and title evidence in the report (iteration 4) ---------


def _iteration4_candidates():
    """One ambiguous surname, one variant-derived hit, one title without evidence."""
    return [
        _cand(_MINI, "Karl Jaspers", "118557106", matched_form="Karl Jaspers"),
        _cand(_MINI, "Jeanne Hersch", "117085391", tier=2, rule="bare-surname:ambiguous",
              alternatives=("117085391", "118557106"),
              matched_form="Mayer, Gertrud", form_source="cache-variant"),
        _cand(_MINI, "Jaspers", "4006406-2", category="work", tier=2, rule="short-title",
              matched_form="Jaspers", evidence="none"),
    ]


def test_preview_counts_ambiguity_and_title_evidence(tmp_path):
    res = preview_document("9999", _MINI, _iteration4_candidates(), tmp_path)
    assert res["counts"]["ambiguous"] == 1
    assert res["counts"]["by_evidence"] == {"none": 1}


def test_report_totals_carry_ambiguity_and_evidence(tmp_path):
    res = preview_document("9999", _MINI, _iteration4_candidates(), tmp_path)
    totals = build_report([res])["totals"]
    assert totals["ambiguous"] == 1
    assert totals["by_evidence"] == {"none": 1}


def test_report_totals_tolerate_documents_without_the_new_counts():
    totals = build_report(_results())["totals"]
    assert totals["ambiguous"] == 0
    assert totals["by_evidence"] == {}


def test_html_report_names_every_bearer_of_an_ambiguous_candidate(tmp_path):
    res = preview_document("9999", _MINI, _iteration4_candidates(), tmp_path)
    html = build_html_report(build_report([res]))
    assert "117085391, 118557106" in html


def test_html_report_keeps_a_decided_tier1_id_in_the_lead(tmp_path):
    # the anchor decided this one, and the file carries exactly that id
    cands = [_cand(_MINI, "Karl Jaspers", "118557106", rule="anchored-surname",
                   alternatives=("117085391", "118557106"))]
    html = build_html_report(build_report([preview_document("9999", _MINI, cands, tmp_path)]))
    assert "118557106 (alt: 117085391)" in html


def test_html_report_names_the_form_the_hit_came_from(tmp_path):
    res = preview_document("9999", _MINI, _iteration4_candidates(), tmp_path)
    html = build_html_report(build_report([res]))
    assert "cache-variant: Mayer, Gertrud" in html
    assert "headword: Karl Jaspers" in html


def test_html_report_marks_a_title_without_typographic_evidence(tmp_path):
    res = preview_document("9999", _MINI, _iteration4_candidates(), tmp_path)
    html = build_html_report(build_report([res]))
    assert "short-title (evidence: none)" in html
