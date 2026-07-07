"""Tests fuer scripts/tei/tei_char_normalize.py (Bestandskorrektur straight_apostrophe).

Die Korrekturklasse ist identisch zu char_lint_audit.straight_apostrophe: gerader
Apostroph U+0027 zwischen zwei Buchstaben wird zu U+2019. Geprueft werden Ersetzung
zwischen Buchstaben, Nichtberuehrung von Attributen/teiHeader/Kommentaren, Idempotenz,
Backup-Entstehung und dry-run ohne Schreibzugriff.
"""

from scripts.tei import tei_char_normalize as norm

STRAIGHT = "'"
CURLY = "’"


def _doc(header_extra="", text_body=""):
    """Minimales TEI-Geruest: teiHeader vor <text>, damit Scope-Grenzen testbar sind."""
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<TEI xmlns="http://www.tei-c.org/ns/1.0">\n'
        f"<teiHeader>{header_extra}</teiHeader>\n"
        "<facsimile><surface><graphic url=\"p1.jpg\"/></surface></facsimile>\n"
        f"<text><body>{text_body}</body></text>\n"
        "</TEI>\n"
    )


def test_replaces_between_letters():
    region = "d'une l'homme s'est"
    new, count = norm.normalize_text_region(region)
    assert count == 3
    assert STRAIGHT not in new
    assert new == f"d{CURLY}une l{CURLY}homme s{CURLY}est"


def test_not_between_letters_is_ignored():
    # boundary/space/digit cases: none is a letter-letter apostrophe
    region = "l' ordre 'abc mots' 70' d'2"
    new, count = norm.normalize_text_region(region)
    assert count == 0
    assert new == region


def test_tags_and_comments_in_region_preserved():
    region = "<div n=\"l'an\"><!-- d'ici --><p>d'une</p></div>"
    new, count = norm.normalize_text_region(region)
    assert count == 1  # only the <p> text node
    assert "n=\"l'an\"" in new          # attribute untouched
    assert "<!-- d'ici -->" in new       # comment untouched
    assert f"<p>d{CURLY}une</p>" in new


def test_teiheader_and_facsimile_untouched():
    raw = _doc(header_extra="<title>l'ordre du jour</title>", text_body="<p>d'une chose</p>")
    new, count = norm.normalize_document(raw)
    assert count == 1
    assert "<title>l'ordre du jour</title>" in new   # teiHeader stays straight
    assert f"<p>d{CURLY}une chose</p>" in new


def test_attribute_inside_text_untouched():
    raw = _doc(text_body="<div type=\"entry\" n=\"l'an\"><p>s'est</p></div>")
    new, count = norm.normalize_document(raw)
    assert count == 1
    assert "n=\"l'an\"" in new
    assert f"<p>s{CURLY}est</p>" in new


def test_idempotent():
    raw = _doc(text_body="<p>d'une l'homme</p>")
    once, c1 = norm.normalize_document(raw)
    assert c1 == 2
    twice, c2 = norm.normalize_document(once)
    assert c2 == 0
    assert twice == once


def test_dry_run_writes_nothing(tmp_path):
    f = tmp_path / "999_final.xml"
    original = _doc(text_body="<p>d'une</p>")
    f.write_text(original, encoding="utf-8")
    backup_dir = tmp_path / "_backup"
    count, changed = norm.process_file(f, backup_dir, dry_run=True)
    assert count == 1
    assert changed is True
    assert f.read_text(encoding="utf-8") == original   # file not modified
    assert not backup_dir.exists()                       # no backup written


def test_real_run_creates_backup_and_writes(tmp_path):
    f = tmp_path / "999_final.xml"
    original = _doc(text_body="<p>d'une</p>")
    f.write_text(original, encoding="utf-8")
    backup_dir = tmp_path / "_backup"
    count, changed = norm.process_file(f, backup_dir, dry_run=False)
    assert count == 1
    assert changed is True
    backup = backup_dir / "999_final.xml"
    assert backup.exists()
    assert backup.read_text(encoding="utf-8") == original          # backup = pre-state
    assert CURLY in f.read_text(encoding="utf-8")                  # file corrected
    assert STRAIGHT not in f.read_text(encoding="utf-8").split("</teiHeader>")[1]


def test_no_text_element_returns_unchanged():
    raw = "<TEI xmlns=\"http://www.tei-c.org/ns/1.0\"><teiHeader/></TEI>"
    new, count = norm.normalize_document(raw)
    assert count == 0
    assert new == raw
