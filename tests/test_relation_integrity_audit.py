"""Tests fuer die Relations-Integritaet (scripts.eval.relation_integrity_audit)."""

import xml.etree.ElementTree as ET

from scripts.eval.relation_integrity_audit import audit_root
from tests.conftest import tei_doc


def _root(body_inner: str):
    return ET.fromstring(tei_doc(body_inner, header="<teiHeader/>"))


def test_note_links_reciprocal_ok():
    body = (
        '<div><p>x<note xml:id="fn1-1" next="#fn2-1">a</note></p>'
        '<p>y<note xml:id="fn2-1" prev="#fn1-1">b</note></p></div>'
    )
    res = audit_root(_root(body))
    assert res["note_links"] == []


def test_note_next_target_missing():
    body = '<div><p><note xml:id="fn1-1" next="#nope">a</note></p></div>'
    res = audit_root(_root(body))
    assert any(i["type"] == "next_target_missing" for i in res["note_links"])


def test_note_next_not_reciprocated():
    # target exists but does not point back with @prev
    body = (
        '<div><p><note xml:id="fn1-1" next="#fn2-1">a</note></p>'
        '<p><note xml:id="fn2-1">b</note></p></div>'
    )
    res = audit_root(_root(body))
    assert any(i["type"] == "next_not_reciprocated" for i in res["note_links"])


def test_anchor_pair_unmatched():
    body = '<div><anchor xml:id="fig8-start"/><p>x</p></div>'
    res = audit_root(_root(body))
    assert any(i["missing"] == "fig8-end" for i in res["anchor_pairs"])


def test_anchor_pair_matched_ok():
    body = '<div><anchor xml:id="fig8-start"/><p>x</p><anchor xml:id="fig8-end"/></div>'
    res = audit_root(_root(body))
    assert res["anchor_pairs"] == []


def test_head_multiple_title_main():
    body = (
        '<div><head><title type="main">A</title>'
        '<title type="main">B</title></head><p>x</p></div>'
    )
    res = audit_root(_root(body))
    assert len(res["head_titles"]) == 1
    # single main title is fine
    body_ok = '<div><head><title type="main">A</title><title type="sub">B</title></head></div>'
    assert audit_root(_root(body_ok))["head_titles"] == []


def test_speech_context():
    inside = '<div type="interview"><sp><speaker>X</speaker><p>a</p></sp></div>'
    assert audit_root(_root(inside))["speech_context"] == []
    outside = '<div type="text"><sp><speaker>X</speaker><p>a</p></sp></div>'
    res = audit_root(_root(outside))
    assert len(res["speech_context"]) >= 1
