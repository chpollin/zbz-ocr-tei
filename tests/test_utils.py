"""Tests fuer scripts/utils.py."""

import json
import pytest
from pathlib import Path


def test_extract_page_num_standard():
    from scripts.utils import extract_page_num
    assert extract_page_num("2310_p001.png") == 1
    assert extract_page_num("2310_p12.md") == 12
    assert extract_page_num("doc_p003_layout.json") == 3


def test_extract_page_num_invalid():
    from scripts.utils import extract_page_num
    with pytest.raises(ValueError):
        extract_page_num("no_page_here.txt")


def test_load_json_valid(tmp_json):
    from scripts.utils import load_json
    data = {"key": "value", "num": 42}
    path = tmp_json(data)
    result = load_json(path)
    assert result == data


def test_load_json_missing():
    from scripts.utils import load_json
    result = load_json(Path("/nonexistent/file.json"))
    assert result is None


def test_load_json_invalid(tmp_path):
    from scripts.utils import load_json
    bad = tmp_path / "bad.json"
    bad.write_text("{invalid json", encoding="utf-8")
    result = load_json(bad)
    assert result is None


def test_write_json(tmp_path):
    from scripts.utils import write_json, load_json
    data = {"name": "Hersch", "year": 1910}
    path = tmp_path / "sub" / "output.json"
    write_json(path, data)
    assert path.exists()
    loaded = load_json(path)
    assert loaded == data


def test_write_json_unicode(tmp_path):
    from scripts.utils import write_json
    data = {"text": "Zuerich aeoeue"}
    path = tmp_path / "unicode.json"
    write_json(path, data)
    content = path.read_text(encoding="utf-8")
    assert "Zuerich" in content
    assert "\\u" not in content  # ensure_ascii=False


def test_get_phase_doc_ids():
    from scripts.utils import get_phase_doc_ids
    phase1 = get_phase_doc_ids("phase1")
    assert isinstance(phase1, list)
    assert "2310" in phase1
    assert len(phase1) == 3


def test_get_phase_doc_ids_all():
    from scripts.utils import get_phase_doc_ids
    all_ids = get_phase_doc_ids("all")
    assert len(all_ids) >= 10
    assert "2310" in all_ids
    assert "2530" in all_ids


def test_get_phase_doc_ids_invalid():
    from scripts.utils import get_phase_doc_ids
    assert get_phase_doc_ids("nonexistent") == []


def test_discover_doc_ids(tmp_path):
    from scripts.utils import discover_doc_ids
    (tmp_path / "100").mkdir()
    (tmp_path / "200").mkdir()
    (tmp_path / ".hidden").mkdir()
    (tmp_path / "file.txt").touch()
    result = discover_doc_ids(tmp_path)
    assert result == ["100", "200"]


def test_discover_doc_ids_missing():
    from scripts.utils import discover_doc_ids
    result = discover_doc_ids(Path("/nonexistent"))
    assert result == []
