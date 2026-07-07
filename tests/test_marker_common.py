"""Direct unit tests for scripts/tei/marker_common.py.

The module is the shared write path of every reversible marker run on
output/tei_final/; backup_and_write is the undo path of those runs, so its
contract (backup holds the pre-state, target holds the new text) is tested
here directly rather than only through the tools.
"""

from scripts.tei import marker_common
from scripts.tei.marker_common import backup_and_write, iter_final_files


def _make_final_dir(tmp_path):
    d = tmp_path / "tei_final"
    d.mkdir()
    (d / "110_final.xml").write_text("<TEI>110</TEI>", encoding="utf-8")
    (d / "20_final.xml").write_text("<TEI>20</TEI>", encoding="utf-8")
    (d / "notes.txt").write_text("ignored", encoding="utf-8")
    return d


def test_iter_final_files_yields_sorted_doc_ids(tmp_path, monkeypatch):
    monkeypatch.setattr(marker_common, "TEI_FINAL_DIR", _make_final_dir(tmp_path))
    result = list(iter_final_files())
    assert [doc_id for doc_id, _ in result] == ["110", "20"]
    assert all(p.name == f"{doc_id}_final.xml" for doc_id, p in result)


def test_iter_final_files_filters_single_doc(tmp_path, monkeypatch):
    monkeypatch.setattr(marker_common, "TEI_FINAL_DIR", _make_final_dir(tmp_path))
    assert [doc_id for doc_id, _ in iter_final_files("20")] == ["20"]
    assert list(iter_final_files("999")) == []


def test_backup_and_write_preserves_pre_state(tmp_path):
    target = tmp_path / "20_final.xml"
    target.write_text("original", encoding="utf-8")
    backup_dir = tmp_path / "_backup"

    backup_and_write(target, backup_dir, "rewritten")

    assert target.read_text(encoding="utf-8") == "rewritten"
    assert (backup_dir / "20_final.xml").read_text(encoding="utf-8") == "original"


def test_backup_and_write_creates_nested_backup_dir(tmp_path):
    target = tmp_path / "20_final.xml"
    target.write_text("original", encoding="utf-8")
    backup_dir = tmp_path / "a" / "b"

    backup_and_write(target, backup_dir, "new")

    assert (backup_dir / "20_final.xml").exists()
