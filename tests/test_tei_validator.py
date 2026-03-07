"""Tests fuer scripts/tei/tei_validator.py - Projekt-Regeln R1-R8."""

import pytest
from pathlib import Path

TEI_NS = "http://www.tei-c.org/ns/1.0"

# Pruefe ob lxml verfuegbar ist (R2-R8 brauchen lxml)
try:
    from lxml import etree as _lxml_etree
    HAS_LXML = True
except ImportError:
    HAS_LXML = False

requires_lxml = pytest.mark.skipif(not HAS_LXML, reason="lxml nicht installiert")


def _write_tei(tmp_path, content, name="test.xml"):
    """Hilfsfunktion: schreibt TEI-XML in tmp_path."""
    path = tmp_path / name
    path.write_text(content, encoding="utf-8")
    return path


def _valid_tei():
    """Minimal-gueltiges TEI nach Projektregeln."""
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<TEI xmlns="{TEI_NS}" type="naegeli">\n'
        '  <teiHeader>\n'
        '    <fileDesc><titleStmt><title>Test</title></titleStmt>\n'
        '    <publicationStmt><p/></publicationStmt>\n'
        '    <sourceDesc><p/></sourceDesc></fileDesc>\n'
        '    <profileDesc><langUsage>\n'
        '      <language ident="deu"/>\n'
        '    </langUsage></profileDesc>\n'
        '  </teiHeader>\n'
        '  <text><body>\n'
        '    <div n="1"><p>Text</p></div>\n'
        '  </body></text>\n'
        '</TEI>'
    )


class TestValidateProjectRules:
    def test_valid_tei_no_errors(self, tmp_path):
        from scripts.tei.tei_validator import validate_project_rules
        path = _write_tei(tmp_path, _valid_tei())
        errors = validate_project_rules(path)
        assert errors == []

    def test_r1_missing_naegeli_type(self, tmp_path):
        from scripts.tei.tei_validator import validate_project_rules
        tei = _valid_tei().replace('type="naegeli"', '')
        path = _write_tei(tmp_path, tei)
        errors = validate_project_rules(path)
        # Ohne lxml: Fehler hat kein "rule"-Key, aber "naegeli" in message
        assert len(errors) >= 1
        messages = " ".join(e.get("message", "") for e in errors)
        assert "naegeli" in messages

    @requires_lxml
    def test_r2_missing_header(self, tmp_path):
        from scripts.tei.tei_validator import validate_project_rules
        tei = (
            f'<?xml version="1.0"?>\n'
            f'<TEI xmlns="{TEI_NS}" type="naegeli">\n'
            f'  <text><body><div n="1"><p>Text</p></div></body></text>\n'
            f'</TEI>'
        )
        path = _write_tei(tmp_path, tei)
        errors = validate_project_rules(path)
        rules = [e.get("rule") for e in errors]
        assert "R2" in rules

    @requires_lxml
    def test_r3_missing_body(self, tmp_path):
        from scripts.tei.tei_validator import validate_project_rules
        tei = (
            f'<?xml version="1.0"?>\n'
            f'<TEI xmlns="{TEI_NS}" type="naegeli">\n'
            f'  <teiHeader><fileDesc><titleStmt><title>T</title></titleStmt>\n'
            f'  <publicationStmt><p/></publicationStmt>\n'
            f'  <sourceDesc><p/></sourceDesc></fileDesc></teiHeader>\n'
            f'  <text></text>\n'
            f'</TEI>'
        )
        path = _write_tei(tmp_path, tei)
        errors = validate_project_rules(path)
        rules = [e.get("rule") for e in errors]
        assert "R3" in rules

    @requires_lxml
    def test_r4_missing_div(self, tmp_path):
        from scripts.tei.tei_validator import validate_project_rules
        tei = _valid_tei().replace(
            '<div n="1"><p>Text</p></div>',
            '<p>Text ohne div</p>'
        )
        path = _write_tei(tmp_path, tei)
        errors = validate_project_rules(path)
        rules = [e.get("rule") for e in errors]
        assert "R4" in rules

    @requires_lxml
    def test_r5_invalid_div_type(self, tmp_path):
        from scripts.tei.tei_validator import validate_project_rules
        tei = _valid_tei().replace(
            '<div n="1">',
            '<div type="ungueltig_typ">'
        )
        path = _write_tei(tmp_path, tei)
        errors = validate_project_rules(path)
        rules = [e.get("rule") for e in errors]
        assert "R5" in rules

    @requires_lxml
    def test_r6_note_without_place(self, tmp_path):
        from scripts.tei.tei_validator import validate_project_rules
        tei = _valid_tei().replace(
            '<p>Text</p>',
            '<p>Text</p><note>Fussnote ohne place</note>'
        )
        path = _write_tei(tmp_path, tei)
        errors = validate_project_rules(path)
        rules = [e.get("rule") for e in errors]
        assert "R6" in rules

    @requires_lxml
    def test_r6_note_with_place_ok(self, tmp_path):
        from scripts.tei.tei_validator import validate_project_rules
        tei = _valid_tei().replace(
            '<p>Text</p>',
            '<p>Text</p><note place="foot">Fussnote</note>'
        )
        path = _write_tei(tmp_path, tei)
        errors = validate_project_rules(path)
        rules = [e.get("rule") for e in errors]
        assert "R6" not in rules

    @requires_lxml
    def test_r7_persname_without_ref(self, tmp_path):
        from scripts.tei.tei_validator import validate_project_rules
        tei = _valid_tei().replace(
            '<p>Text</p>',
            '<p><persName>Karl Jaspers</persName></p>'
        )
        path = _write_tei(tmp_path, tei)
        errors = validate_project_rules(path)
        rules = [e.get("rule") for e in errors]
        assert "R7" in rules

    @requires_lxml
    def test_r7_persname_with_ref_ok(self, tmp_path):
        from scripts.tei.tei_validator import validate_project_rules
        tei = _valid_tei().replace(
            '<p>Text</p>',
            '<p><persName ref="GND:118557106">Karl Jaspers</persName></p>'
        )
        path = _write_tei(tmp_path, tei)
        errors = validate_project_rules(path)
        rules = [e.get("rule") for e in errors]
        assert "R7" not in rules

    @requires_lxml
    def test_r8_language_without_ident(self, tmp_path):
        from scripts.tei.tei_validator import validate_project_rules
        tei = _valid_tei().replace(
            '<language ident="deu"/>',
            '<language/>'
        )
        path = _write_tei(tmp_path, tei)
        errors = validate_project_rules(path)
        rules = [e.get("rule") for e in errors]
        assert "R8" in rules


class TestValidateTeiFile:
    def test_valid_file(self, tmp_path):
        from scripts.tei.tei_validator import validate_tei_file
        path = _write_tei(tmp_path, _valid_tei())
        result = validate_tei_file(path)
        assert result["project_errors"] == 0

    def test_invalid_xml(self, tmp_path):
        from scripts.tei.tei_validator import validate_tei_file
        path = _write_tei(tmp_path, "<broken xml><<>")
        result = validate_tei_file(path)
        assert result["valid"] is False
        assert len(result["errors"]) > 0
