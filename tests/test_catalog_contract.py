"""Document-field contract between the catalog builder and the catalog page.

``docs/assets/js/catalog.js`` reads a fixed set of fields off every document of
``docs/data/catalog.json`` (search, filters, sorting, table columns and the workflow
traffic lights). The builder ``scripts.edition.generate_edition_data.build_catalog`` is the
only producer of that file, so the field set is a contract between two files that no test
held: a renamed or dropped key would leave the page silently empty in that column.

The fixtures are synthetic (a tmp_path corpus with one final TEI, one manifest and a
metadata cache); the builder is called directly, nothing under ``docs/data`` or ``output``
is read. The stream aggregation over the entities stream is already covered by
``tests/test_entity_stream.py`` and not repeated here.
"""

from __future__ import annotations

import json

import pytest

from scripts.edition import generate_edition_data as ged

# Every field catalog.js touches on a document object (rowFor, filters, sort, streamStatus).
CATALOG_JS_FIELDS = frozenset({
    "id", "title", "author", "date", "desc", "lang", "pub_form", "page_count",
    "type", "streams",
})

# The full entry as the builder writes it; the extra keys serve viewer links and the
# corpus histograms rather than the catalog table.
CATALOG_ENTRY_FIELDS = CATALOG_JS_FIELDS | {"has_tei", "assets", "curation", "demo"}

DOC_ID = "1000"

METADATA = {
    "title": "Le probleme de la liberte",
    "author": "Hersch, Jeanne",
    "date": "1975",
    "language": "fra",
    "layout_type": "B",
    "pub_form": "journalArticle",
    "description": "Un article de revue.",
    "page_count": 12,
}

STREAMS = {
    "ocr": {"engine": "mistral", "status": "verifiziert",
            "history": [{"at": "2026-08-01T10:00:00", "by": "CP", "from": "in_arbeit",
                         "to": "verifiziert", "note": ""}]},
    "layout": {"engines": ["docling"], "status": "in_arbeit", "history": []},
    "tei": {"source": "final", "status": "unverifiziert", "history": []},
}


@pytest.fixture
def catalog(tmp_path, monkeypatch):
    """Builds a catalog from one synthetic document with metadata and a manifest."""
    def build(metadata: dict | None = None, streams: dict | None = None) -> dict:
        final_dir = tmp_path / "tei_final"
        final_dir.mkdir(exist_ok=True)
        (final_dir / f"{DOC_ID}_final.xml").write_text("<TEI/>", encoding="utf-8")
        if streams is not None:
            (final_dir / f"{DOC_ID}_manifest.json").write_text(
                json.dumps({"doc_id": DOC_ID, "streams": streams, "pages": {}}),
                encoding="utf-8")
        meta_path = tmp_path / "doc_metadata.json"
        meta_path.write_text(
            json.dumps({"documents": {DOC_ID: metadata if metadata is not None else METADATA}},
                       ensure_ascii=False), encoding="utf-8")
        monkeypatch.setattr(ged, "TEI_FINAL_DIR", final_dir)
        monkeypatch.setattr(ged, "TEI_CURATED_DIR", tmp_path / "curated")
        monkeypatch.setattr(ged, "DOCS_DIR", tmp_path / "docs")
        monkeypatch.setattr(ged, "DOC_METADATA_PATH", meta_path)
        return ged.build_catalog()
    return build


def _entry(catalog_dict: dict) -> dict:
    return next(e for e in catalog_dict["documents"] if e["id"] == DOC_ID)


# --- field contract --------------------------------------------------------------

def test_every_document_carries_the_fields_the_page_reads(catalog):
    """No field catalog.js addresses may be missing from a document entry."""
    for entry in catalog(streams=STREAMS)["documents"]:
        assert set(entry) >= CATALOG_JS_FIELDS


def test_document_entry_has_exactly_the_documented_field_set(catalog):
    """The entry shape is pinned so an added or dropped key is a deliberate change."""
    assert set(_entry(catalog(streams=STREAMS))) == CATALOG_ENTRY_FIELDS


def test_catalog_top_level_carries_generated_and_documents(catalog):
    """The page reads data.generated for its footer and data.documents for the table."""
    result = catalog(streams=STREAMS)
    assert isinstance(result["generated"], str) and result["generated"]
    assert isinstance(result["documents"], list)


# --- metadata mapping ------------------------------------------------------------

def test_metadata_reaches_the_document_fields(catalog):
    """Title, author, date, description, form and page count come from the metadata cache."""
    entry = _entry(catalog(streams=STREAMS))
    assert entry["title"] == METADATA["title"]
    assert entry["author"] == METADATA["author"]
    assert entry["date"] == METADATA["date"]
    assert entry["desc"] == METADATA["description"]
    assert entry["pub_form"] == METADATA["pub_form"]
    assert entry["page_count"] == METADATA["page_count"]


def test_layout_type_and_language_are_projected_to_the_filter_values(catalog):
    """The filters compare against the short forms: layout type B and language code FR."""
    entry = _entry(catalog(streams=STREAMS))
    assert entry["type"] == "B"
    assert entry["lang"] == "FR"


def test_bilingual_language_code_keeps_both_languages(catalog):
    """A document in two languages carries the combined filter value, not one of them."""
    entry = _entry(catalog(metadata={**METADATA, "language": "fra/deu"}, streams=STREAMS))
    assert entry["lang"] == "DE/FR"


def test_all_caps_author_is_normalized_for_display(catalog):
    """A metadata author in hard caps would shout in the table; the builder title-cases it."""
    entry = _entry(catalog(metadata={**METADATA, "author": "JEANNE HERSCH"}, streams=STREAMS))
    assert entry["author"] == "Jeanne Hersch"


def test_missing_metadata_yields_placeholder_fields_not_missing_keys(catalog):
    """A document without metadata still gets every field, so the page never reads undefined."""
    entry = _entry(catalog(metadata={}, streams=STREAMS))
    assert set(entry) >= CATALOG_JS_FIELDS
    assert entry["title"] == "Dokument " + DOC_ID
    assert entry["lang"] == "?"
    assert entry["type"] == "-"
    assert entry["page_count"] == 0


# --- workflow streams ------------------------------------------------------------

def test_stream_block_carries_status_and_last_edit_per_stream(catalog):
    """Each traffic light reads status, last_by and last_at off its stream block."""
    streams = _entry(catalog(streams=STREAMS))["streams"]
    assert set(streams) == {"ocr", "layout", "tei"}
    assert streams["ocr"]["status"] == "verifiziert"
    assert streams["ocr"]["last_by"] == "CP"
    assert streams["ocr"]["last_at"] == "2026-08-01T10:00:00"
    assert streams["layout"]["status"] == "in_arbeit"
    assert streams["tei"] == {"status": "unverifiziert", "last_at": None, "last_by": None}


def test_document_without_manifest_defaults_to_unverified_streams(catalog):
    """The default is unverified pipeline output, not a missing traffic light."""
    streams = _entry(catalog(streams=None))["streams"]
    assert set(streams) == {"ocr", "layout", "tei"}
    assert all(s["status"] == "unverifiziert" for s in streams.values())


def test_legacy_status_values_are_migrated_on_read(catalog):
    """Manifests written before E77 carry offen/bearbeitet/fertig; the page knows only the new set."""
    legacy = {name: {**block, "status": old}
              for (name, block), old in zip(STREAMS.items(),
                                            ("offen", "bearbeitet", "fertig"), strict=True)}
    streams = _entry(catalog(streams=legacy))["streams"]
    assert [streams[n]["status"] for n in ("ocr", "layout", "tei")] == [
        "unverifiziert", "in_arbeit", "verifiziert"]
