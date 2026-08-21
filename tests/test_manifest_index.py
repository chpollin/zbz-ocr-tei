"""Contract of the aggregated manifest index (docs/data/manifest_index.json).

The catalog page reads the workflow status of every document from one file instead of
one request per manifest, so the index must carry the manifest `streams` block verbatim
under the document id. A manifest without a usable `streams` block is skipped rather
than filled with a default, because an invented status would show up as a traffic light.
"""

from __future__ import annotations

import json

from scripts.edition.generate_edition_data import write_manifest_index


def _manifest(doc_id: str, streams: dict) -> dict:
    return {
        "doc_id": doc_id,
        "page_count": 2,
        "generated": "2026-08-21",
        "generator": "test",
        "streams": streams,
        "pages": {},
    }


def _write(tmp_path, name: str, payload) -> None:
    (tmp_path / name).write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def test_index_carries_stream_blocks_verbatim(tmp_path):
    src = tmp_path / "manifests"
    src.mkdir()
    streams_a = {
        "ocr": {"engine": "mistral", "status": "unverifiziert", "history": []},
        "layout": {"engines": ["docling", "gemini"], "status": "in_arbeit",
                   "history": [{"at": "2026-08-01T10:00:00", "by": "AB",
                                "from": "unverifiziert", "to": "in_arbeit", "note": None}]},
        "tei": {"source": "final", "status": "verifiziert", "history": []},
    }
    streams_b = {
        "ocr": {"engine": "mistral", "status": "unverifiziert", "history": []},
        "layout": {"engines": ["docling"], "status": "unverifiziert", "history": []},
        "tei": {"source": "final", "status": "unverifiziert", "history": []},
        "entities": {"source": "entity_preview", "status": "unverifiziert", "history": []},
    }
    _write(src, "100_manifest.json", _manifest("100", streams_a))
    _write(src, "1010_manifest.json", _manifest("1010", streams_b))

    out = tmp_path / "manifest_index.json"
    assert write_manifest_index(src, out) == 2

    index = json.loads(out.read_text(encoding="utf-8"))
    assert index == {"100": streams_a, "1010": streams_b}


def test_index_skips_broken_and_streamless_manifests(tmp_path):
    src = tmp_path / "manifests"
    src.mkdir()
    good = {"ocr": {"status": "verifiziert", "history": []}}
    _write(src, "100_manifest.json", _manifest("100", good))
    _write(src, "200_manifest.json", {"doc_id": "200", "pages": {}})
    (src / "300_manifest.json").write_text("{not json", encoding="utf-8")

    out = tmp_path / "manifest_index.json"
    assert write_manifest_index(src, out) == 1
    assert json.loads(out.read_text(encoding="utf-8")) == {"100": good}


def test_index_falls_back_to_the_filename_for_the_document_id(tmp_path):
    src = tmp_path / "manifests"
    src.mkdir()
    streams = {"tei": {"status": "unverifiziert", "history": []}}
    _write(src, "1350_manifest.json", {"streams": streams})

    out = tmp_path / "manifest_index.json"
    write_manifest_index(src, out)
    assert list(json.loads(out.read_text(encoding="utf-8"))) == ["1350"]


def test_missing_manifest_directory_writes_nothing(tmp_path):
    out = tmp_path / "manifest_index.json"
    assert write_manifest_index(tmp_path / "absent", out) == 0
    assert not out.exists()
