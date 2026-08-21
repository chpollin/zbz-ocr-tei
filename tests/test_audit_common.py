"""Direct unit tests for scripts/eval/audit_common.py.

The module is the shared scaffolding of every guideline-conformity audit (E92): it
derives the doc id, discovers the delivered TEI files, parses tolerantly and writes the
JSON report. Those four contracts are pinned here directly, because a silent change to
them shifts every audit report at once.
"""

import json

import pytest

from scripts.config import TEI_FINAL_DIR
from scripts.eval import audit_common
from scripts.eval.audit_common import (
    doc_id_from_path,
    iter_final_tei,
    parse_tei,
    resolve_tei_dir,
    write_audit_report,
)

VALID_TEI = '<TEI xmlns="http://www.tei-c.org/ns/1.0"><text><body><p>x</p></body></text></TEI>'


def _final_dir(tmp_path):
    d = tmp_path / "tei_final"
    d.mkdir()
    (d / "110_final.xml").write_text(VALID_TEI, encoding="utf-8")
    (d / "20_final.xml").write_text(VALID_TEI, encoding="utf-8")
    (d / "20_manifest.json").write_text("{}", encoding="utf-8")
    return d


def test_doc_id_from_path_strips_final_suffix():
    assert doc_id_from_path("output/tei_final/2310_final.xml") == "2310"
    assert doc_id_from_path("2310_final.xml") == "2310"


def test_iter_final_tei_yields_only_final_xml_sorted_by_filename(tmp_path):
    d = _final_dir(tmp_path)
    result = list(iter_final_tei(d))
    assert [doc_id for doc_id, _ in result] == ["110", "20"]
    assert all(path.name == f"{doc_id}_final.xml" for doc_id, path in result)


def test_parse_tei_returns_root_without_error(tmp_path):
    path = tmp_path / "20_final.xml"
    path.write_text(VALID_TEI, encoding="utf-8")
    root, error = parse_tei(path)
    assert error is None
    assert root.tag.endswith("TEI")


def test_parse_tei_reports_broken_xml_instead_of_raising(tmp_path):
    path = tmp_path / "broken_final.xml"
    path.write_text("<TEI><text>", encoding="utf-8")
    root, error = parse_tei(path)
    assert root is None
    assert error


def test_parse_tei_reports_missing_file_instead_of_raising(tmp_path):
    root, error = parse_tei(tmp_path / "absent_final.xml")
    assert root is None
    assert error


def test_write_audit_report_writes_indented_utf8_json(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(audit_common, "AUDIT_OUTPUT_DIR", tmp_path / "audits")
    payload = {"documents": 2, "note": "Kolumnentitel"}

    out = write_audit_report("demo_audit", payload)

    assert out.name == "demo_audit.json"
    assert json.loads(out.read_text(encoding="utf-8")) == payload
    assert "\n  " in out.read_text(encoding="utf-8")
    assert "Kolumnentitel" in out.read_text(encoding="utf-8")
    assert str(out) in capsys.readouterr().out


def test_resolve_tei_dir_defaults_to_tei_final(monkeypatch):
    monkeypatch.setattr("sys.argv", ["audit"])
    assert resolve_tei_dir("demo") == TEI_FINAL_DIR


def test_resolve_tei_dir_honours_dir_flag(monkeypatch, tmp_path):
    monkeypatch.setattr("sys.argv", ["audit", "--dir", str(tmp_path)])
    assert resolve_tei_dir("demo") == tmp_path


def test_resolve_tei_dir_rejects_unknown_flag(monkeypatch):
    monkeypatch.setattr("sys.argv", ["audit", "--unknown"])
    with pytest.raises(SystemExit):
        resolve_tei_dir("demo")
