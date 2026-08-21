"""Tests fuer scripts/tei/tei_body_note_demote.py.

Sichert die verdict-gesteuerten Operationen ab: HAUPTTEXT-Demotion zu <p> mit
facs-Erhalt und Wegfall der Fussnoten-Attribute, ECHTE_FUSSNOTE bleibt, BLOCKZITAT
zu <quote> (bzw. dokumentierter <p>-Fallback), Rollentausch-Promotion nur bei
Marker-Treffer, UNMATCHED bei len-Abweichung, Dry-Run schreibt nichts, Idempotenz
des Schreibpfads. Zuletzt: ein demotetes reales Dokument bleibt gegen
data/schema/zbz_hersch.rng valide.
"""
import re

import pytest

from scripts.tei.tei_body_note_demote import (
    FINAL_DIR,
    clean_footnote_attrs,
    is_footnote_id,
    iter_foot_notes,
    process_document,
    schema_validator,
    transform_document,
)

# --- synthetic fixture: one HAUPTTEXT note + following marker <p>, one ECHTE note ---
SYN = (
    "<TEI><text><body>\n"
    '      <pb facs="#facs_2" n="2" />\n'
    '        <p facs="#facs_2_r_1">Body paragraph, normal running prose.</p>\n'
    '        <note place="foot" n="1" xml:id="fn2-1" facs="#facs_2_r_3">'
    "This is actually running body text wrongly framed as a footnote and it is "
    "clearly long enough to pass the audit length gate for a candidate.</note>\n"
    "        <p>\n"
    "          ¹ Real footnote line that starts with a superscript marker.\n"
    "        </p>\n"
    '        <note place="foot" n="2" xml:id="fn2-2" facs="#facs_2_r_5">'
    "Genuine short footnote.</note>\n"
    "</body></text></TEI>"
)


def _notes():
    return iter_foot_notes(SYN)


def _entry(note, verdict, following=False):
    return {"doc": "T", "page": note.page, "len": note.length,
            "verdict": verdict, "real_footnote_following": following}


def test_is_footnote_id():
    assert is_footnote_id("fn5-1")
    assert is_footnote_id("fn12a-3")
    assert not is_footnote_id("intro-1")
    assert not is_footnote_id("")


def test_clean_footnote_attrs_keeps_facs_drops_footnote_atts():
    attrs = ' place="foot" n="1" xml:id="fn5-1" facs="#facs_5_r_3"'
    cleaned = clean_footnote_attrs(attrs)
    assert "facs=" in cleaned
    assert "place=" not in cleaned
    assert re.search(r"\bn=", cleaned) is None
    assert "xml:id" not in cleaned


def test_clean_footnote_attrs_keeps_non_footnote_xml_id():
    cleaned = clean_footnote_attrs(' place="foot" xml:id="intro-1"')
    assert 'xml:id="intro-1"' in cleaned


def test_demote_hauptext_to_p_preserves_facs():
    notes = _notes()
    haupt = notes[0]
    new_raw, report = transform_document(SYN, [_entry(haupt, "HAUPTTEXT")])
    assert report[0]["operation"] == "demote_p"
    # the demoted block is now a <p> carrying facs, without footnote attributes
    assert '<p facs="#facs_2_r_3">' in new_raw
    assert '<note place="foot" n="1" xml:id="fn2-1"' not in new_raw
    assert "fn2-1" not in new_raw
    # inner text is unchanged
    assert "wrongly framed as a footnote" in new_raw


def test_echte_fussnote_preserved():
    notes = _notes()
    echte = notes[1]
    new_raw, report = transform_document(SYN, [_entry(echte, "ECHTE_FUSSNOTE")])
    assert report[0]["operation"] == "preserve"
    assert new_raw == SYN


def test_blockzitat_to_quote_with_stub_validator():
    notes = _notes()
    haupt = notes[0]
    new_raw, report = transform_document(
        SYN, [_entry(haupt, "BLOCKZITAT")], validator=lambda raw: True)
    assert report[0]["operation"] == "demote_quote"
    assert "<quote" in new_raw


def test_blockzitat_fallback_p_when_schema_rejects():
    notes = _notes()
    haupt = notes[0]
    new_raw, report = transform_document(
        SYN, [_entry(haupt, "BLOCKZITAT")], validator=lambda raw: False)
    assert report[0]["operation"] == "quote_fallback_p"
    assert "reason" in report[0]
    assert "<quote" not in new_raw


def test_promotion_only_on_marker_match():
    notes = _notes()
    haupt = notes[0]
    new_raw, report = transform_document(
        SYN, [_entry(haupt, "HAUPTTEXT", following=True)], promote=True)
    promo = report[0]["promotion"]
    assert promo["matched"] is True
    assert promo["para_start"].startswith("¹")
    # the marker paragraph became a foot note
    assert new_raw.count('place="foot"') == 2  # fn2-2 stays + the promoted one


def test_promotion_skipped_without_marker():
    raw = (
        "<TEI><text><body>\n"
        '      <pb facs="#facs_3" n="3" />\n'
        '        <note place="foot" facs="#facs_3_r_2">Body text framed as note, '
        "long enough to be a candidate for demotion in the audit.</note>\n"
        "        <p>Ordinary following paragraph without any footnote marker.</p>\n"
        "</body></text></TEI>"
    )
    note = iter_foot_notes(raw)[0]
    new_raw, report = transform_document(
        raw, [_entry(note, "HAUPTTEXT", following=True)], promote=True)
    assert report[0]["promotion"]["matched"] is False
    assert new_raw.count("place=") == 0  # nothing promoted


def test_unmatched_on_len_mismatch():
    notes = _notes()
    haupt = notes[0]
    bad = {"doc": "T", "page": haupt.page, "len": haupt.length + 999,
           "verdict": "HAUPTTEXT"}
    new_raw, report = transform_document(SYN, [bad])
    assert report[0]["operation"] == "unmatched"
    assert new_raw == SYN


def test_dry_run_writes_nothing(tmp_path, monkeypatch):
    import scripts.tei.tei_body_note_demote as mod
    monkeypatch.setattr(mod, "FINAL_DIR", tmp_path)
    f = tmp_path / "T_final.xml"
    f.write_text(SYN, encoding="utf-8")
    haupt = iter_foot_notes(SYN)[0]
    res = process_document("T", [_entry(haupt, "HAUPTTEXT")], promote=False,
                           dry_run=True, validator=None)
    assert res["changed"] is True          # would change, but dry-run
    assert f.read_text(encoding="utf-8") == SYN


def test_write_and_idempotency(tmp_path, monkeypatch):
    import scripts.tei.tei_body_note_demote as mod
    monkeypatch.setattr(mod, "FINAL_DIR", tmp_path)
    monkeypatch.setattr(mod, "BACKUP_DIR", tmp_path / "_backup")
    f = tmp_path / "T_final.xml"
    f.write_text(SYN, encoding="utf-8")
    notes = iter_foot_notes(SYN)
    entries = [_entry(notes[0], "HAUPTTEXT", following=True),
               _entry(notes[1], "ECHTE_FUSSNOTE")]

    r1 = process_document("T", entries, promote=True, dry_run=False, validator=None)
    assert r1["changed"] is True
    after_first = f.read_text(encoding="utf-8")
    assert (tmp_path / "_backup" / "T_final.xml").exists()

    r2 = process_document("T", entries, promote=True, dry_run=False, validator=None)
    assert r2["changed"] is False
    assert f.read_text(encoding="utf-8") == after_first


def _real_doc(doc_id):
    p = FINAL_DIR / f"{doc_id}_final.xml"
    if not p.exists():
        pytest.skip(f"{doc_id}_final.xml nicht vorhanden")
    return p.read_text(encoding="utf-8")


# --- schema-valid fixture: one wrongly framed foot note + following marker <p> ---
SYN_VALID = (
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    '<TEI xmlns="http://www.tei-c.org/ns/1.0">\n'
    "  <teiHeader>\n"
    "    <fileDesc>\n"
    "      <titleStmt><title>Testdokument</title></titleStmt>\n"
    "      <publicationStmt><p>ZBZ</p></publicationStmt>\n"
    "      <sourceDesc><p>Testquelle</p></sourceDesc>\n"
    "    </fileDesc>\n"
    "  </teiHeader>\n"
    "  <text>\n"
    "    <body>\n"
    '      <div type="text">\n'
    '        <pb facs="#facs_2" n="2" />\n'
    '        <p facs="#facs_2_r_1">Erster Absatz der Seite.</p>\n'
    '        <note place="foot" n="1" xml:id="fn2-1" facs="#facs_2_r_3">'
    "Dies ist fortlaufender Haupttext, der faelschlich als Fussnote gerahmt wurde. Dies ist fortlaufender Haupttext, der faelschlich als Fussnote gerahmt wurde. Dies ist fortlaufender Haupttext, der faelschlich als Fussnote gerahmt wurde. Dies ist fortlaufender Haupttext, der faelschlich als Fussnote gerahmt wurde. Dies ist fortlaufender Haupttext, der faelschlich als Fussnote gerahmt wurde. Dies ist fortlaufender Haupttext, der faelschlich als Fussnote gerahmt wurde."
    "</note>\n"
    "        <p>\n"
    "          ¹ Echte Fussnote mit vorangestelltem Marker.\n"
    "        </p>\n"
    "      </div>\n"
    "    </body>\n"
    "  </text>\n"
    "</TEI>\n"
)


def test_demoted_document_stays_schema_valid():
    """Der Demotions-Schreibpfad bleibt gegen data/schema/zbz_hersch.rng valide.

    Frueher lief der Fall gegen Dokument 530; nach dem Bestandslauf E94 traegt kein
    Lieferdokument mehr eine lange fehlgerahmte Fussnote, und der Test uebersprang sich
    seither selbst. Die synthetische Fixture haelt den Fall deterministisch fest.
    """
    validator = schema_validator()
    assert validator is not None, "lxml und data/schema/zbz_hersch.rng sind Pflicht"
    assert validator(SYN_VALID), "Baseline-Fixture muss valide sein"
    notes = iter_foot_notes(SYN_VALID)
    entries = [{"doc": "T", "page": n.page, "len": n.length,
                "verdict": "HAUPTTEXT", "real_footnote_following": True}
               for n in notes]
    assert entries, "Fixture traegt eine fehlgerahmte Fussnote"
    new_raw, _ = transform_document(SYN_VALID, entries, promote=True, validator=validator)
    assert new_raw != SYN_VALID
    assert 'xml:id="fn2-1"' not in new_raw   # fehlgerahmte Fussnote ist jetzt Haupttext
    assert '<note place="foot">' in new_raw  # Markerabsatz wurde zur echten Fussnote
    assert validator(new_raw), "Demotiertes Dokument muss valide bleiben"


def test_blockzitat_quote_real_doc_valid():
    validator = schema_validator()
    assert validator is not None, "lxml und data/schema/zbz_hersch.rng sind Pflicht"
    raw = _real_doc("2420")
    notes = iter_foot_notes(raw)
    target = max(notes, key=lambda n: n.length)  # the 1055-char blockzitat note
    new_raw, report = transform_document(
        raw, [{"doc": "2420", "page": target.page, "len": target.length,
               "verdict": "BLOCKZITAT"}], validator=validator)
    assert report[0]["operation"] == "demote_quote"
    assert validator(new_raw)
