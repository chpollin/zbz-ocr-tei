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

import hashlib
import json
import re

import pytest

from scripts.tei.tei_entity_preview import (
    ADJUDICATION_RESP_ID,
    MATCHER_RESP_ID,
    PANEL_DOCS,
    apply_candidates,
    build_report,
    check_text_invariance,
    discover_doc_ids,
    insert_resp_stmts,
    mark_attributes,
    matcher_fingerprint,
    preview_document,
    resp_statements,
    run_preview,
    text_signature,
    validate_rng,
    verified_spans,
)

# --- fixtures ---------------------------------------------------------------

# The wrapper format restated independently of the implementation: a mark names its
# GND id, the rule that produced it, its certainty token and the responsibilities.
_MATCHER_RESP = f"#{MATCHER_RESP_ID}"
_BOTH_RESP = f"#{MATCHER_RESP_ID} #{ADJUDICATION_RESP_ID}"


def _open(element: str, gid: str, rule: str = "full_name", cert: str = "medium",
          resp: str = _MATCHER_RESP) -> str:
    """Expected opening tag of a wrapped mark."""
    return f'<{element} ref="GND:{gid}" source="{rule}" cert="{cert}" resp="{resp}">'

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
    assert _open("persName", "118557505") + "Karl Jaspers</persName>" in out
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
        + _open("persName", "118557505") + "Karl Jaspers</persName>"
        " und "
        + _open("persName", "118815679") + "Jeanne Hersch</persName>"
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
    assert _open("orgName", "1010450-1", "org_name") + "Universitaet Genf</orgName>" in out
    assert (_open("bibl", "1088036961", "work_title")
            + "Das philosophische Staunen</bibl>") in out


def test_surface_with_embedded_lb_is_wrapped_as_a_whole():
    surface = 'Jeanne <lb break="no"/>Hersch'
    out = apply_candidates(_MINI_LB, [_cand(_MINI_LB, surface, "118815679")])
    assert _open("persName", "118815679") + f"{surface}</persName>" in out
    assert check_text_invariance(_MINI_LB, out)


# --- bibl outside an existing hi --------------------------------------------


def _work_cand(xml, surface="Das philosophische Staunen", gid="1088036961"):
    return _cand(xml, surface, gid, category="work", rule="work-title")


def test_bibl_wraps_a_fully_covered_hi_from_outside():
    out = apply_candidates(_MINI_HI, [_work_cand(_MINI_HI)])
    assert (_open("bibl", "1088036961", "work-title")
            + '<hi rendition="#i">Das philosophische Staunen</hi>'
            "</bibl>") in out
    assert '<hi rendition="#i"><bibl' not in out
    assert check_text_invariance(_MINI_HI, out)


def test_partial_hit_inside_an_hi_stays_inside():
    out = apply_candidates(_MINI_HI_WIDE, [_work_cand(_MINI_HI_WIDE)])
    assert ('<hi rendition="#i">'
            + _open("bibl", "1088036961", "work-title")
            + "Das philosophische Staunen</bibl>"
            ", Muenchen 1964</hi>") in out
    assert check_text_invariance(_MINI_HI_WIDE, out)


def test_hi_envelope_requires_the_closing_tag_immediately_after_the_span():
    # a trailing space inside the hi means the candidate is not its whole content
    xml = _MINI_HI.replace("Staunen</hi>", "Staunen </hi>")
    out = apply_candidates(xml, [_work_cand(xml)])
    assert '<hi rendition="#i">' + _open("bibl", "1088036961", "work-title") in out
    assert check_text_invariance(xml, out)


def test_a_non_hi_neighbour_tag_does_not_trigger_the_outside_wrap():
    out = apply_candidates(_MINI_LB_LEAD, [_cand(_MINI_LB_LEAD, "Karl Jaspers", "118557505")])
    assert "<lb/>" + _open("persName", "118557505") + "Karl Jaspers</persName>" in out


def test_offsets_stay_valid_when_an_hi_wrap_widens_the_span():
    cands = [
        _cand(_MINI_HI_MIXED, "Karl Jaspers", "118557505"),
        _work_cand(_MINI_HI_MIXED, surface="Von der Wahrheit", gid="TEST-0001"),
    ]
    out = apply_candidates(_MINI_HI_MIXED, cands)
    assert _open("persName", "118557505") + "Karl Jaspers</persName>" in out
    assert (_open("bibl", "TEST-0001", "work-title")
            + '<hi rendition="#i">Von der Wahrheit</hi></bibl>') in out
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
    assert (_open("bibl", "TEST-0001", "work-title")
            + '<hi rendition="#i">Von der Wahrheit</hi></bibl>') in out
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
    assert _open("persName", "118557505") in written.read_text(encoding="utf-8")
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
# The header declaration is the second insertion preview_document makes; stripping both
# insertions must give the source back byte for byte.
_RESPSTMT_RE = re.compile(r"[ \t]*<respStmt xml:id=\"resp-entity-[^\"]*\">.*?</respStmt>\r?\n?")


def _strip_insertions(xml_string: str) -> str:
    return _WRAPPER_RE.sub("", _RESPSTMT_RE.sub("", xml_string))


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
    assert _strip_insertions(raw.decode("utf-8")) == crlf_doc
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
    assert totals["by_certainty"] == {}


# --- provenance, certainty, verification state --------------------------------------
#
# Three separate things, never merged: @resp says who asserted the mark, @cert says
# whether a human checked it, @source says which rule produced it. Measured reliability
# of a rule class is a property of the adjudicated sample and stays out of the mark.


_DIGEST = "a" * 64
_OTHER_DIGEST = "b" * 64


def _store(marks) -> dict:
    return {"snapshot": "2026-08-12", "marks": marks, "recall_mentions": []}


def _store_mark(cand, doc="9999", verdict="correct", text_sha256=_DIGEST):
    """Verdict-store record for a candidate, keyed as build_mention_verdicts keys it."""
    return {"doc": doc, "page": 1, "gid": cand["gid"], "surface": cand["surface"],
            "verdict": verdict, "start": cand["start"], "end": cand["end"],
            "text_sha256": text_sha256}


def test_unverified_mark_is_medium_and_names_only_the_matcher():
    cand = _cand(_MINI, "Karl Jaspers", "118557505", rule="full-name")
    assert mark_attributes(cand) == {
        "ref": "GND:118557505", "source": "full-name",
        "cert": "medium", "resp": _MATCHER_RESP,
    }


def test_verified_mark_is_high_and_names_the_adjudication_too():
    cand = dict(_cand(_MINI, "Karl Jaspers", "118557505", rule="full-name"), verified=True)
    assert mark_attributes(cand) == {
        "ref": "GND:118557505", "source": "full-name",
        "cert": "high", "resp": _BOTH_RESP,
    }


def test_certainty_is_only_ever_a_schema_token_never_a_number():
    for verified in (False, True):
        cand = dict(_cand(_MINI, "Karl Jaspers", "1", rule="full-name"), verified=verified)
        assert mark_attributes(cand)["cert"] in {"high", "medium", "low", "unknown"}


def test_a_candidate_without_a_rule_omits_the_source_attribute():
    cand = _cand(_MINI, "Karl Jaspers", "1")
    del cand["rule"]
    assert "source" not in mark_attributes(cand)


def test_the_rule_travels_on_source_because_evidence_is_illegal_on_bibl():
    """@source is the one candidate the schema allows on all three wrapped elements."""
    with_source = _VALID_DOC_HI.replace(
        '<hi rendition="#i">Von der Wahrheit</hi>',
        '<bibl ref="GND:TEST-0001" source="work-title" cert="medium" resp="#r">'
        '<hi rendition="#i">Von der Wahrheit</hi></bibl>')
    assert validate_rng(with_source) == []
    for illegal in ('evidence="work-title"', 'ana="work-title"'):
        broken = with_source.replace('source="work-title"', illegal)
        assert validate_rng(broken), f"{illegal} unexpectedly valid on bibl"


def test_wrapped_marks_of_every_category_stay_schema_valid_with_the_attributes():
    cands = [
        dict(_cand(_VALID_DOC, "Karl Jaspers", "118557505", rule="full-name"), verified=True),
        _cand(_VALID_DOC, "Universitaet Basel", "1010450-1",
              category="organisation", rule="org-token"),
    ]
    out = apply_candidates(_VALID_DOC, cands)
    out = insert_resp_stmts(out, resp_statements(cands, "2026-08-12"))
    assert validate_rng(out) == []
    assert check_text_invariance(_VALID_DOC, out)


# --- respStmt declaration ------------------------------------------------------------


def test_resp_statements_declare_only_the_responsibilities_in_use():
    plain = [_cand(_MINI, "Karl Jaspers", "1", rule="full-name")]
    assert [rid for rid, _ in resp_statements(plain, "2026-08-12")] == [MATCHER_RESP_ID]

    verified = [dict(plain[0], verified=True)]
    assert [rid for rid, _ in resp_statements(verified, "2026-08-12")] == [
        MATCHER_RESP_ID, ADJUDICATION_RESP_ID]


def test_no_responsibility_is_declared_without_a_wrapped_mark():
    tier2 = [_cand(_MINI, "Karl Jaspers", "1", tier=2, rule="bare-surname")]
    assert resp_statements(tier2, "2026-08-12") == []


def test_the_matcher_responsibility_carries_a_stable_rule_fingerprint():
    fingerprint = matcher_fingerprint()
    assert re.fullmatch(r"[0-9a-f]{12}", fingerprint)
    assert fingerprint == matcher_fingerprint()
    _, text = resp_statements([_cand(_MINI, "K", "1", rule="full-name")], None)[0]
    assert fingerprint in text


def test_the_adjudication_responsibility_names_the_wave_snapshot():
    verified = [dict(_cand(_MINI, "K", "1", rule="full-name"), verified=True)]
    _, text = resp_statements(verified, "2026-08-12")[1]
    assert "2026-08-12" in text


def test_resp_stmts_land_in_the_titlestmt_and_keep_the_document_valid():
    out = insert_resp_stmts(_VALID_DOC, [(MATCHER_RESP_ID, "Automatic entity matching")])
    assert f'<respStmt xml:id="{MATCHER_RESP_ID}">' in out
    assert out.index("<respStmt") < out.index("</titleStmt>")
    assert validate_rng(out) == []


def test_resp_stmt_insertion_is_idempotent():
    once = insert_resp_stmts(_VALID_DOC, [(MATCHER_RESP_ID, "Automatic entity matching")])
    assert insert_resp_stmts(once, [(MATCHER_RESP_ID, "Automatic entity matching")]) == once


def test_resp_stmt_insertion_leaves_a_header_less_fragment_alone():
    assert insert_resp_stmts(_MINI, [(MATCHER_RESP_ID, "x")]) == _MINI


def test_resp_stmt_insertion_does_not_touch_the_text_subtree():
    out = insert_resp_stmts(_VALID_DOC, [(MATCHER_RESP_ID, "Automatic entity matching")])
    assert check_text_invariance(_VALID_DOC, out)


# --- verification state against the verdict store ------------------------------------


def test_an_adjudicated_correct_mark_at_its_exact_span_counts_as_verified():
    cand = _cand(_VALID_DOC, "Karl Jaspers", "118557505", rule="full-name")
    spans = verified_spans(_store([_store_mark(cand)]), "9999", [cand], {"9999": _DIGEST})
    assert spans == {(cand["start"], cand["end"], "118557505")}


def test_a_moved_text_digest_falls_back_to_unverified():
    """A judgment made on other bytes never claims verification (guard: text_changed)."""
    cand = _cand(_VALID_DOC, "Karl Jaspers", "118557505", rule="full-name")
    store = _store([_store_mark(cand, text_sha256=_OTHER_DIGEST)])
    assert verified_spans(store, "9999", [cand], {"9999": _DIGEST}) == set()


def test_a_missing_document_digest_falls_back_to_unverified():
    cand = _cand(_VALID_DOC, "Karl Jaspers", "118557505", rule="full-name")
    store = _store([_store_mark(cand)])
    assert verified_spans(store, "9999", [cand], {"9999": None}) == set()


def test_a_changed_span_falls_back_to_unverified():
    cand = _cand(_VALID_DOC, "Karl Jaspers", "118557505", rule="full-name")
    mark = _store_mark(cand)
    mark["end"] -= 3  # the adjudicated extent is not the extent we would wrap
    assert verified_spans(_store([mark]), "9999", [cand], {"9999": _DIGEST}) == set()


def test_a_wrong_verdict_never_verifies_a_mark():
    cand = _cand(_VALID_DOC, "Karl Jaspers", "118557505", rule="full-name")
    for verdict in ("wrong_entity", "wrong_span", "not_in_source", "undecidable"):
        store = _store([_store_mark(cand, verdict=verdict)])
        assert verified_spans(store, "9999", [cand], {"9999": _DIGEST}) == set()


def test_a_worklist_candidate_is_never_verified():
    cand = _cand(_VALID_DOC, "Karl Jaspers", "118557505", tier=2, rule="bare-surname")
    store = _store([_store_mark(cand)])
    assert verified_spans(store, "9999", [cand], {"9999": _DIGEST}) == set()


def test_a_judgment_about_another_entity_does_not_verify_this_mark():
    cand = _cand(_VALID_DOC, "Karl Jaspers", "118557505", rule="full-name")
    mark = _store_mark(cand)
    mark["gid"] = "999999999"
    assert verified_spans(_store([mark]), "9999", [cand], {"9999": _DIGEST}) == set()


def test_a_judgment_about_another_document_does_not_verify_this_mark():
    cand = _cand(_VALID_DOC, "Karl Jaspers", "118557505", rule="full-name")
    store = _store([_store_mark(cand, doc="8888")])
    assert verified_spans(store, "9999", [cand], {"9999": _DIGEST}) == set()


# --- end to end through run_preview ---------------------------------------------------


def _preview_run(tmp_path, store=None, marks_verdict="correct"):
    src, out = tmp_path / "src", tmp_path / "out"
    src.mkdir(parents=True)
    (src / "9999_final.xml").write_bytes(_VALID_DOC.encode("utf-8"))
    digest = hashlib.sha256((src / "9999_final.xml").read_bytes()).hexdigest()

    def fake_matcher(xml_string, lexicon):
        return [_cand(xml_string, "Karl Jaspers", "118557505", rule="full-name"),
                _cand(xml_string, "Universitaet Basel", "1010450-1",
                      category="organisation", rule="org-token")]

    if store is None:
        cand = _cand(_VALID_DOC, "Karl Jaspers", "118557505", rule="full-name")
        store = _store([_store_mark(cand, verdict=marks_verdict, text_sha256=digest)])
    verdicts = tmp_path / "verdicts.json"
    verdicts.write_text(json.dumps(store), encoding="utf-8")
    report = run_preview(["9999"], fake_matcher, {}, src_dir=src, out_dir=out,
                         verdicts_path=verdicts)
    return report, (out / "9999_final.xml").read_text(encoding="utf-8")


def test_run_preview_projects_the_verdict_store_into_the_marks(tmp_path):
    report, written = _preview_run(tmp_path)
    assert _open("persName", "118557505", "full-name", "high", _BOTH_RESP) in written
    assert _open("orgName", "1010450-1", "org-token") in written
    assert f'<respStmt xml:id="{ADJUDICATION_RESP_ID}">' in written
    assert report["documents"][0]["counts"]["by_certainty"] == {"high": 1, "medium": 1}
    assert report["totals"]["by_certainty"] == {"high": 1, "medium": 1}


def test_run_preview_without_a_verdict_store_marks_everything_unverified(tmp_path):
    report, written = _preview_run(tmp_path, store=_store([]))
    assert 'cert="high"' not in written
    assert f'<respStmt xml:id="{ADJUDICATION_RESP_ID}">' not in written
    assert f'<respStmt xml:id="{MATCHER_RESP_ID}">' in written
    assert report["totals"]["by_certainty"] == {"medium": 2}


def test_run_preview_tolerates_a_missing_verdict_store(tmp_path):
    src, out = tmp_path / "src", tmp_path / "out"
    src.mkdir()
    (src / "9999_final.xml").write_bytes(_VALID_DOC.encode("utf-8"))
    report = run_preview(["9999"], lambda xml, lex: [], {}, src_dir=src, out_dir=out,
                         verdicts_path=tmp_path / "absent.json")
    assert report["totals"]["by_certainty"] == {}


def test_the_preview_stays_valid_and_text_invariant_end_to_end(tmp_path):
    report, written = _preview_run(tmp_path)
    doc = report["documents"][0]
    assert doc["rng_valid"] is True
    assert doc["text_invariant"] is True
    assert check_text_invariance(_VALID_DOC, written)
    assert _strip_insertions(written) == _VALID_DOC


def test_two_runs_produce_byte_identical_previews(tmp_path):
    first = _preview_run(tmp_path / "a")[1]
    second = _preview_run(tmp_path / "b")[1]
    assert first == second


