"""Tests fuer die hi-Erhaltung (scripts.eval.hi_preservation_audit)."""

from scripts.eval.hi_preservation_audit import (
    audit_document,
    has_emphasis,
    mistral_pages,
    page_span_content,
    span_has_hi,
)


def test_has_emphasis_star_and_bold():
    assert has_emphasis("ein *wort* hier") is True
    assert has_emphasis("ein **gras** hier") is True
    assert has_emphasis("ein _kursiv_ hier") is True


def test_has_emphasis_negatives():
    assert has_emphasis("kein snake_case_name hier") is False
    assert has_emphasis("5 * 3 = 15") is False
    assert has_emphasis("nur klartext ohne signal") is False
    assert has_emphasis("* Aufzaehlungspunkt am Rand") is False


def test_page_span_content_by_sequential_position():
    body_inner = '<div><pb n="99"/><p>erste seite</p><pb n="100"/><p>zweite <hi>x</hi></p></div>'
    # page = sequential pb position, NOT @n
    assert "erste seite" in page_span_content(body_inner, 1)
    assert "<hi>" in page_span_content(body_inner, 2)
    assert page_span_content(body_inner, 3) is None


def test_span_has_hi():
    assert span_has_hi('<p><hi rendition="#i">x</hi></p>') is True
    assert span_has_hi("<p>plain</p>") is False


def test_mistral_pages(tmp_path):
    (tmp_path / "570_p1.md").write_text("a", encoding="utf-8")
    (tmp_path / "570_p2.md").write_text("b", encoding="utf-8")
    (tmp_path / "580_p1.md").write_text("c", encoding="utf-8")
    pages = mistral_pages(tmp_path, "570")
    assert set(pages) == {1, 2}


def test_audit_document_flags_signal_without_hi(tmp_path):
    mistral = tmp_path / "mistral"
    mistral.mkdir()
    # page 1: emphasis + TEI has hi -> ok; page 2: emphasis, TEI no hi -> flagged
    (mistral / "570_p1.md").write_text("das *wichtige* wort", encoding="utf-8")
    (mistral / "570_p2.md").write_text("auch *betont* hier", encoding="utf-8")
    tei = tmp_path / "570_final.xml"
    tei.write_text(
        '<?xml version="1.0"?><TEI xmlns="http://www.tei-c.org/ns/1.0"><teiHeader/>'
        "<text><body><div>"
        '<pb n="1"/><p>das <hi rendition="#i">wichtige</hi> wort</p>'
        '<pb n="2"/><p>auch betont hier</p>'
        "</div></body></text></TEI>",
        encoding="utf-8",
    )
    findings, err = audit_document(tei, mistral_dir=mistral)
    assert err is None
    assert findings["emphasis_pages"] == 2
    assert findings["has_any_hi"] is True
    missing = [m["page"] for m in findings["missing_hi"]]
    assert missing == [2]
