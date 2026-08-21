"""Annotationen als vierter Workflow-Strom (Manifest + Katalog-Aggregation).

Der Strom `entities` folgt dem E65/E66-Datenmodell der drei bestehenden Stroeme
(status + history, Default `unverifiziert`), entsteht aber nur dort, wo eine
Entity-Preview existiert. Zwei Richtungen sind abzusichern:

1. Kein Strom ohne Preview (der Katalog wuerde sonst Annotationen behaupten, die es
   nicht gibt).
2. Bestandsschutz: ein einmal angelegter Strom mit Status/History ueberlebt jeden
   Re-Lauf, auch wenn die Preview-Datei verschwindet.

Dazu die Pfad-Regression aus dem scripts-Reorg: page_manifest.ROOT muss das
Projekt-Root sein, sonst laufen Katalog, OCR und Layout-Mirror ins Leere.
"""

from __future__ import annotations

import json

from scripts.edition import generate_edition_data as ged, page_manifest as pm


def _doc(doc_id: str = "100") -> dict:
    # page_count 0 haelt detect_blanks hermetisch (kein OCR/Layout-Zugriff)
    return {"id": doc_id, "page_count": 0}


def _stream(status: str = "verifiziert") -> dict:
    return {
        "source": "entity_preview",
        "status": status,
        "history": [{"at": "2026-08-12T10:00:00Z", "by": "CP",
                     "from": "unverifiziert", "to": status, "note": None}],
    }


# --- Pfade ----------------------------------------------------------------------------


def test_root_points_at_the_project_root():
    """Regression aus dem scripts-Reorg: ROOT zeigte auf scripts/ statt aufs Repo."""
    assert (pm.ROOT / "docs" / "data").is_dir()
    assert (pm.ROOT / "scripts" / "edition" / "page_manifest.py").is_file()


# --- Manifest -------------------------------------------------------------------------


def test_entities_stream_only_with_preview():
    without = pm._migrate_streams(None, with_entities=False)
    assert set(without) == {"ocr", "layout", "tei"}
    with_preview = pm._migrate_streams(None, with_entities=True)
    assert with_preview["entities"]["status"] == pm.DEFAULT_STATUS
    assert with_preview["entities"]["history"] == []


def test_existing_entities_stream_survives_without_preview():
    existing = {"ocr": {"engine": "mistral", "status": "unverifiziert", "history": []},
                "entities": _stream("in_arbeit")}
    out = pm._migrate_streams(existing, with_entities=False)
    assert out["entities"]["status"] == "in_arbeit"
    assert len(out["entities"]["history"]) == 1


def test_entities_stream_preserves_status_and_history_on_rerun():
    existing = {"entities": _stream("verifiziert")}
    out = pm._migrate_streams(existing, with_entities=True)
    assert out["entities"]["status"] == "verifiziert"
    assert out["entities"]["history"][0]["by"] == "CP"


def test_entities_stream_migrates_legacy_status():
    out = pm._migrate_streams({"entities": {"status": "fertig", "history": []}}, with_entities=True)
    assert out["entities"]["status"] == "verifiziert"


def test_build_manifest_reads_preview_existence(tmp_path, monkeypatch):
    monkeypatch.setattr(pm, "ENTITY_PREVIEW_DIR", tmp_path)
    assert "entities" not in pm.build_manifest(_doc())["streams"]
    (tmp_path / "100_final.xml").write_text("<TEI/>", encoding="utf-8")
    assert pm.build_manifest(_doc())["streams"]["entities"]["status"] == pm.DEFAULT_STATUS


def test_build_manifest_is_idempotent_for_the_entities_stream(tmp_path, monkeypatch):
    monkeypatch.setattr(pm, "ENTITY_PREVIEW_DIR", tmp_path)
    (tmp_path / "100_final.xml").write_text("<TEI/>", encoding="utf-8")
    first = pm.build_manifest(_doc())
    first["streams"]["entities"]["status"] = "in_arbeit"
    second = pm.build_manifest(_doc(), existing=first)
    third = pm.build_manifest(_doc(), existing=second)
    assert second["streams"] == third["streams"]
    assert third["streams"]["entities"]["status"] == "in_arbeit"


# --- Katalog-Aggregation --------------------------------------------------------------


def _catalog_fixture(tmp_path, monkeypatch, with_entities_doc: bool = True):
    final_dir = tmp_path / "tei_final"
    final_dir.mkdir()
    docs = {"100": with_entities_doc, "200": False}
    for doc_id, has_entities in docs.items():
        (final_dir / f"{doc_id}_final.xml").write_text("<TEI/>", encoding="utf-8")
        streams = {
            "ocr":    {"engine": "mistral", "status": "unverifiziert", "history": []},
            "layout": {"engines": ["docling"], "status": "unverifiziert", "history": []},
            "tei":    {"source": "final", "status": "unverifiziert", "history": []},
        }
        if has_entities:
            streams["entities"] = _stream("in_arbeit")
        (final_dir / f"{doc_id}_manifest.json").write_text(
            json.dumps({"doc_id": doc_id, "streams": streams, "pages": {}}), encoding="utf-8")
    monkeypatch.setattr(ged, "TEI_FINAL_DIR", final_dir)
    monkeypatch.setattr(ged, "TEI_CURATED_DIR", tmp_path / "curated")
    monkeypatch.setattr(ged, "DOCS_DIR", tmp_path / "docs")
    monkeypatch.setattr(ged, "DOC_METADATA_PATH", tmp_path / "doc_metadata.json")
    return ged.build_catalog()


def test_catalog_carries_the_entities_stream_only_where_it_exists(tmp_path, monkeypatch):
    catalog = _catalog_fixture(tmp_path, monkeypatch)
    entries = {e["id"]: e for e in catalog["documents"]}
    assert entries["100"]["streams"]["entities"]["status"] == "in_arbeit"
    assert entries["100"]["streams"]["entities"]["last_by"] == "CP"
    assert "entities" not in entries["200"]["streams"]


def test_catalog_counts_the_entities_stream_separately(tmp_path, monkeypatch):
    catalog = _catalog_fixture(tmp_path, monkeypatch)
    counts = catalog["corpus"]["stream_status"]
    assert counts["entities"] == {"in_arbeit": 1}
    # Die drei Pflichtstroeme zaehlen weiterhin ueber alle Dokumente
    assert counts["tei"] == {"unverifiziert": 2}


def test_catalog_keeps_entities_bucket_empty_without_any_stream(tmp_path, monkeypatch):
    catalog = _catalog_fixture(tmp_path, monkeypatch, with_entities_doc=False)
    assert catalog["corpus"]["stream_status"]["entities"] == {}
