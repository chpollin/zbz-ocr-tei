"""Tests for scripts.eval.body_note_audit (body-as-note over-detection diagnosis).

Pure-function tests for the weighted signals plus small synthetic TEI fixtures that
exercise document parsing, page grouping and the candidate decision. No corpus files
are read; fixtures are built inline.
"""
import xml.etree.ElementTree as ET

import pytest

from scripts.eval import body_note_audit as bna
from tests.conftest import tei_doc

# --- pure signal functions -------------------------------------------------

def test_length_signal_gate_and_saturation():
    assert bna.length_signal(bna.MIN_LEN) == 0.0
    assert bna.length_signal(bna.MIN_LEN - 100) == 0.0
    assert bna.length_signal(bna.LEN_SATURATION) == pytest.approx(1.0)
    assert bna.length_signal(bna.LEN_SATURATION + 5000) == pytest.approx(1.0)
    mid = bna.length_signal((bna.MIN_LEN + bna.LEN_SATURATION) // 2)
    assert 0.4 < mid < 0.6


def test_position_signal_bottom_is_zero_top_is_one():
    assert bna.position_signal(90.0) == 0.0          # bottom third: footnote lives here
    assert bna.position_signal(10.0) == 1.0          # top third: unexpected for a footnote
    assert bna.position_signal(50.0) == 0.5          # middle
    assert bna.position_signal(None) == 0.5          # unknown -> neutral


def test_marker_class_detects_asterisk_and_digit_and_none():
    assert bna.leading_marker_class("*) An dieser Stelle ...")[0] == "asterisk"
    assert bna.leading_marker_class("1) Siehe oben")[0] == "digit"
    assert bna.leading_marker_class("2 L'Etre et la Forme.")[0] == "digit"
    assert bna.leading_marker_class("Individuums seinen Ort ...")[0] is None


def test_marker_signal_present_with_body_correspondence_is_low():
    # genuine footnote: leading marker and the same marker in the body
    assert bna.marker_signal("asterisk", body_corresp=True) == 0.0
    # orphaned marker (present, but no body correspondence): mild suspicion
    assert 0.0 < bna.marker_signal("asterisk", body_corresp=False) < 0.5
    # no leading marker at all: strongest body-as-note indicator
    assert bna.marker_signal(None, body_corresp=False) == 1.0


def test_body_has_corresponding_marker_asterisk():
    body = "... ein Grund der Feigheit werden*. Die ueberfruehte Heirat ..."
    assert bna.body_has_corresponding_marker("asterisk", body) is True
    assert bna.body_has_corresponding_marker("asterisk", "kein Marker hier") is False


def test_score_orders_calibration_shapes():
    # body-as-note: long, no marker, bottom of page
    s_pos, _ = bna.score_note(length=1991, y_pct=76.0, marker_cls=None, body_corresp=False)
    # genuine footnote: shorter, leading marker with body correspondence, bottom
    s_neg, _ = bna.score_note(length=897, y_pct=79.0, marker_cls="asterisk", body_corresp=True)
    assert s_pos > bna.CANDIDATE_THRESHOLD
    assert s_neg < bna.CANDIDATE_THRESHOLD
    assert s_pos > s_neg


# --- document parsing / integration on synthetic TEI -----------------------

def _tei(surfaces_zones, body_inner):
    """Build a minimal TEI document string from surface/zone specs and a body fragment.

    surfaces_zones: list of (page, lry, [(zone_suffix, uly), ...]).
    """
    surf = []
    for page, lry, zones in surfaces_zones:
        z = "".join(
            f'<zone xml:id="facs_{page}_r_{sfx}" ulx="10" uly="{uly}" lrx="90" lry="{uly+20}" />'
            for sfx, uly in zones
        )
        surf.append(
            f'<surface xml:id="facs_{page}" ulx="0" uly="0" lrx="100" lry="{lry}">'
            f'<graphic url="p{page}.png"/>{z}</surface>'
        )
    return tei_doc(f"<div>{body_inner}</div>", facsimile="".join(surf), xml_decl=True)


def _score_map(findings):
    """map (page) -> best candidate score present in a document's findings list."""
    out = {}
    for c in findings["candidates"]:
        out[c["page"]] = max(out.get(c["page"], 0.0), c["score"])
    return out


def test_document_flags_body_as_note_not_genuine_footnote():
    long_text = "Fortlaufender Haupttext ohne Marker. " * 30  # ~1100 chars, no leading marker
    body = (
        '<pb facs="#facs_1" n="1" />'
        '<p facs="#facs_1_r_1">Haupttext auf Seite eins.</p>'
        f'<note place="foot" n="1" facs="#facs_1_r_2">{long_text}</note>'
        '<pb facs="#facs_2" n="2" />'
        '<p facs="#facs_2_r_1">Echter Verweis mit Marker*.</p>'
        '<note place="foot" n="1" facs="#facs_2_r_2">*) kurze echte Fussnote am Fuss.</note>'
    )
    # page 1: note zone near bottom; page 2: note zone near bottom too
    xml = _tei(
        [
            (1, 1000, [("1", 50), ("2", 760)]),
            (2, 1000, [("1", 50), ("2", 780)]),
        ],
        body,
    )
    root = ET.fromstring(xml)
    findings = bna.analyze_document(root, doc_id="X")
    scores = _score_map(findings)
    assert 1 in scores and scores[1] > bna.CANDIDATE_THRESHOLD   # body-as-note flagged
    assert 2 not in scores                                        # genuine footnote not flagged


def test_short_note_below_length_gate_is_not_a_candidate():
    body = (
        '<pb facs="#facs_1" n="1" />'
        '<p facs="#facs_1_r_1">Text.</p>'
        '<note place="foot" n="1" facs="#facs_1_r_2">Kurz.</note>'
    )
    xml = _tei([(1, 1000, [("1", 50), ("2", 800)])], body)
    findings = bna.analyze_document(ET.fromstring(xml), doc_id="X")
    assert findings["candidates"] == []


def test_reference_docs_are_marked(tmp_path):
    long_text = "Haupttext ohne jeglichen Marker. " * 30
    body = (
        '<pb facs="#facs_1" n="1" />'
        '<p facs="#facs_1_r_1">Text.</p>'
        f'<note place="foot" n="1" facs="#facs_1_r_2">{long_text}</note>'
    )
    xml = _tei([(1, 1000, [("1", 50), ("2", 760)])], body)
    tei_dir = tmp_path / "tei"
    tei_dir.mkdir()
    (tei_dir / "111_final.xml").write_text(xml, encoding="utf-8")
    (tei_dir / "222_final.xml").write_text(xml, encoding="utf-8")
    summary = bna.audit_corpus(tei_dir, reference_ids={"111"})
    docs = {d["doc"]: d for d in summary["documents"]}
    assert docs["111"]["has_reference"] is True
    assert docs["222"]["has_reference"] is False
    assert summary["corpus_totals"]["candidate_docs"] == 2
    assert summary["corpus_totals"]["candidate_docs_no_reference"] == 1
