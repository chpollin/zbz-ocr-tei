"""Tests fuer TEI-Inline-Konvertierung und Entity-Annotation."""


def test_md_to_tei_bold():
    from scripts.tei.tei_generator import md_to_tei_inline
    result = md_to_tei_inline("Das ist **fett** hier.")
    assert '<hi rendition="#b">fett</hi>' in result
    assert "**" not in result


def test_md_to_tei_italic():
    from scripts.tei.tei_generator import md_to_tei_inline
    result = md_to_tei_inline("Das ist *kursiv* hier.")
    assert '<hi rendition="#i">kursiv</hi>' in result
    assert result.count("*") == 0


def test_md_to_tei_bold_and_italic():
    from scripts.tei.tei_generator import md_to_tei_inline
    result = md_to_tei_inline("**bold** und *italic*")
    assert '<hi rendition="#b">bold</hi>' in result
    assert '<hi rendition="#i">italic</hi>' in result


def test_md_to_tei_no_markdown():
    from scripts.tei.tei_generator import md_to_tei_inline
    text = "Kein Markdown hier."
    assert md_to_tei_inline(text) == text


def test_annotate_entities_jaspers():
    from scripts.tei.tei_generator import annotate_entities
    result = annotate_entities("Karl Jaspers war Philosoph.")
    assert '<persName ref="GND:118557106">Karl Jaspers</persName>' in result


def test_annotate_entities_no_nesting():
    from scripts.tei.tei_generator import annotate_entities
    result = annotate_entities("Karl Jaspers und Jaspers")
    # "Karl Jaspers" soll als Ganzes annotiert werden, "Jaspers" separat
    assert result.count("<persName") == 2
    assert result.count("</persName>") == 2


def test_annotate_entities_no_match():
    from scripts.tei.tei_generator import annotate_entities
    text = "Ein Text ohne bekannte Namen."
    assert annotate_entities(text) == text


def test_annotate_entities_multiple():
    from scripts.tei.tei_generator import annotate_entities
    result = annotate_entities("Heidegger und Sartre diskutierten.")
    assert "GND:118547798" in result  # Heidegger
    assert "GND:118605895" in result  # Sartre
