"""Idempotenz des Status-Markers (E66): zweiter Lauf erzeugt keine Duplikate.

Der Marker projiziert die Workflow-History aus dem Manifest als <change>-Eintraege
in den <revisionDesc>. Markereigene Eintraege (n="{stream}" / n="{stream}-summary")
werden bei jedem Lauf vollstaendig ersetzt; Fremdeintraege (z.B. who="pipeline",
Pipeline-Status E42) ueberleben unangetastet.
"""


from scripts.tei import tei_status_marker as tsm

FIXTURE_TEI = """<?xml version="1.0" encoding="UTF-8"?>
<TEI xmlns="http://www.tei-c.org/ns/1.0">
  <teiHeader>
    <revisionDesc>
    <change when="2026-03-15" who="pipeline">TEI generated (Unified Pipeline v1, Gemini + RelaxNG)</change>
    </revisionDesc>
  </teiHeader>
  <text><body><p>x</p></body></text>
</TEI>
"""

MANIFEST = {
    "doc_id": "999",
    "streams": {
        "ocr": {
            "engine": "mistral",
            "status": "verifiziert",
            "history": [
                {"at": "2026-06-01T10:00:00Z", "by": "CP", "from": "unverifiziert",
                 "to": "in_arbeit", "note": None},
                {"at": "2026-06-02T10:00:00Z", "by": "CP", "from": "in_arbeit",
                 "to": "verifiziert", "note": "geprueft"},
            ],
        },
        "layout": {"engines": ["docling", "gemini"], "status": "unverifiziert", "history": []},
        "tei":    {"source": "final", "status": "unverifiziert", "history": []},
    },
}


def _setup(tmp_path, monkeypatch):
    final_dir = tmp_path / "tei_final"
    backup_dir = tmp_path / "_backup"
    final_dir.mkdir()
    monkeypatch.setattr(tsm, "FINAL_DIR", final_dir)
    monkeypatch.setattr(tsm, "BACKUP_DIR", backup_dir)
    (final_dir / "999_final.xml").write_text(FIXTURE_TEI, encoding="utf-8")
    return final_dir


def test_second_run_is_idempotent(tmp_path, monkeypatch):
    final_dir = _setup(tmp_path, monkeypatch)
    path = final_dir / "999_final.xml"

    r1 = tsm.project_doc("999", MANIFEST, dry_run=False, keep_legacy=False)
    assert r1["ok"]
    assert r1["changed"]
    after_first = path.read_text(encoding="utf-8")

    r2 = tsm.project_doc("999", MANIFEST, dry_run=False, keep_legacy=False)
    assert r2["ok"]
    after_second = path.read_text(encoding="utf-8")

    assert after_second == after_first
    assert not r2["changed"]


def test_no_duplicate_marker_changes(tmp_path, monkeypatch):
    final_dir = _setup(tmp_path, monkeypatch)
    path = final_dir / "999_final.xml"

    tsm.project_doc("999", MANIFEST, dry_run=False, keep_legacy=False)
    tsm.project_doc("999", MANIFEST, dry_run=False, keep_legacy=False)
    content = path.read_text(encoding="utf-8")

    assert content.count('n="ocr-summary"') == 1
    assert content.count('n="layout-summary"') == 1
    assert content.count('n="tei-summary"') == 1
    # two OCR history entries, none for empty layout/tei histories
    assert content.count('n="ocr"') == 2
    assert content.count('n="layout"') == 0
    assert content.count('n="tei"') == 0


def test_foreign_change_survives(tmp_path, monkeypatch):
    final_dir = _setup(tmp_path, monkeypatch)
    path = final_dir / "999_final.xml"

    tsm.project_doc("999", MANIFEST, dry_run=False, keep_legacy=False)
    tsm.project_doc("999", MANIFEST, dry_run=False, keep_legacy=False)
    content = path.read_text(encoding="utf-8")

    assert content.count('who="pipeline"') == 1
    assert "TEI generated (Unified Pipeline v1, Gemini + RelaxNG)" in content


def test_dry_run_writes_nothing(tmp_path, monkeypatch):
    final_dir = _setup(tmp_path, monkeypatch)
    path = final_dir / "999_final.xml"
    before = path.read_text(encoding="utf-8")

    r = tsm.project_doc("999", MANIFEST, dry_run=True, keep_legacy=False)
    assert r["ok"]
    assert r["changed"]
    assert path.read_text(encoding="utf-8") == before
