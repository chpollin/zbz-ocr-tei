"""Blank-page detection and its projection into the delivered TEI (E63 phase 2, E65).

Two steps of one chain, both on synthetic data under tmp_path:

1. ``scripts.edition.page_manifest.detect_blanks`` classifies a page as blank from the OCR
   rule and confirms it with the Docling region count; a text-blank page that Docling still
   sees regions on is a contradiction and gets ``review=true`` instead of a silent pass.
2. ``scripts.tei.tei_blank_marker`` projects exactly the confirmed blanks into
   ``{doc}_final.xml`` as ``<pb type="blank"/>`` and empties the page body.

``tei_blank_marker`` was the only ``marker_common`` consumer without a contract test; the
reversibility promise of the marker runs (dry run writes nothing, real run backs up, second
run is byte-identical) is pinned here.
"""

from __future__ import annotations

import json

import pytest

from scripts.edition import page_manifest
from scripts.tei import tei_blank_marker

DOC_ID = "9002"

BLANK_OCR = "\n\n"
TEXT_OCR = "Un paragraphe de texte courant sur la page.\n"


# --- detect_blanks ---------------------------------------------------------------

@pytest.fixture
def manifest_dirs(tmp_path, monkeypatch):
    """OCR source and Docling mirror of a two-page document, page 2 blank."""
    ocr_dir = tmp_path / "mistral_results"
    mirror = tmp_path / "pages"
    ocr_dir.mkdir()
    (mirror / DOC_ID).mkdir(parents=True)
    monkeypatch.setattr(page_manifest, "OCR_DIR", ocr_dir)
    monkeypatch.setattr(page_manifest, "MIRROR_PAGES", mirror)
    return ocr_dir, mirror / DOC_ID


def _write_page(dirs, page: int, ocr: str, regions: int | None) -> None:
    ocr_dir, layout_dir = dirs
    (ocr_dir / f"{DOC_ID}_p{page}.md").write_text(ocr, encoding="utf-8")
    if regions is not None:
        (layout_dir / f"{DOC_ID}_p{page:03d}_layout.json").write_text(
            json.dumps({"num_regions": regions}), encoding="utf-8")


def test_detect_blanks_reports_only_the_blank_page(manifest_dirs):
    """A page with text is absent from the map; the blank page carries class=blank."""
    _write_page(manifest_dirs, 1, TEXT_OCR, 3)
    _write_page(manifest_dirs, 2, BLANK_OCR, 0)
    pages = page_manifest.detect_blanks(DOC_ID, 2)
    assert list(pages) == ["2"]
    assert pages["2"]["class"] == "blank"
    assert pages["2"]["source"] == "auto"


def test_detect_blanks_confirmed_by_docling_needs_no_review(manifest_dirs):
    """OCR blank plus zero Docling regions is the safe case: review=false."""
    _write_page(manifest_dirs, 1, BLANK_OCR, 0)
    assert page_manifest.detect_blanks(DOC_ID, 1)["1"]["review"] is False


def test_detect_blanks_contradicted_by_docling_is_flagged_for_review(manifest_dirs):
    """OCR blank but Docling sees regions: the contradiction is marked, not waved through."""
    _write_page(manifest_dirs, 1, BLANK_OCR, 2)
    page = page_manifest.detect_blanks(DOC_ID, 1)["1"]
    assert page["review"] is True
    assert page["evidence"]["docling_regions"] == 2


def test_detect_blanks_records_the_ocr_evidence(manifest_dirs):
    """The evidence block names the rule that fired, so a verdict stays auditable."""
    _write_page(manifest_dirs, 1, "   ", 0)
    evidence = page_manifest.detect_blanks(DOC_ID, 1)["1"]["evidence"]
    assert evidence["ocr_reason"] == "len<=5"
    assert evidence["ocr_len"] == 0


def test_detect_blanks_without_docling_layout_keeps_the_page_unconfirmed(manifest_dirs):
    """No Docling file means no confirmation channel; the page stays a blank without conflict."""
    _write_page(manifest_dirs, 1, BLANK_OCR, None)
    page = page_manifest.detect_blanks(DOC_ID, 1)["1"]
    assert page["review"] is False
    assert page["evidence"]["docling_regions"] is None


def test_detect_blanks_missing_ocr_file_is_not_a_blank(manifest_dirs):
    """A page without any OCR file carries no evidence at all and is not classified."""
    assert page_manifest.detect_blanks(DOC_ID, 2) == {}


# --- tei_blank_marker ------------------------------------------------------------

FINAL_XML = (
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    '<TEI xmlns="http://www.tei-c.org/ns/1.0" type="naegeli">\n'
    "  <text>\n    <body>\n"
    '      <div type="text">\n'
    '        <pb facs="#facs_1" n="1"/>\n'
    "        <p>Un paragraphe de la premiere page.</p>\n"
    '        <pb facs="#facs_2" n="2"/>\n'
    "        <p>Reste d'OCR sur une page vide.</p>\n"
    '        <pb facs="#facs_3" n="3"/>\n'
    "        <p>Un paragraphe de la troisieme page.</p>\n"
    "      </div>\n"
    "    </body>\n  </text>\n</TEI>\n"
)

MANIFEST = {
    "doc_id": DOC_ID,
    "page_count": 3,
    "pages": {
        "2": {"class": "blank", "source": "auto", "review": False},
        "3": {"class": "blank", "source": "auto", "review": True},
    },
}


@pytest.fixture
def final_dir(tmp_path, monkeypatch):
    """A synthetic tei_final directory with one document and its manifest."""
    final = tmp_path / "tei_final"
    final.mkdir()
    (final / f"{DOC_ID}_final.xml").write_text(FINAL_XML, encoding="utf-8")
    (final / f"{DOC_ID}_manifest.json").write_text(
        json.dumps(MANIFEST, ensure_ascii=False), encoding="utf-8")
    monkeypatch.setattr(tei_blank_marker, "FINAL_DIR", final)
    monkeypatch.setattr(tei_blank_marker, "BACKUP_DIR", tmp_path / "_backup_pre_blank_marker")
    return final


def test_manifest_yields_only_the_confirmed_blank_page(final_dir):
    """Page 3 is blank but flagged for review, so it is not a safe blank and stays out."""
    doc_id, pages = tei_blank_marker.blank_pages_from_manifest(
        final_dir / f"{DOC_ID}_manifest.json")
    assert doc_id == DOC_ID
    assert pages == [2]


def test_marker_types_exactly_the_blank_page(final_dir):
    """Only the blank page's pb gets type="blank"; the other page breaks stay untouched."""
    report = tei_blank_marker.project_doc(DOC_ID, [2], dry_run=False)
    assert report["ok"] and report["typed"] == [2]
    written = (final_dir / f"{DOC_ID}_final.xml").read_text(encoding="utf-8")
    assert '<pb facs="#facs_2" n="2" type="blank" />' in written
    assert '<pb facs="#facs_1" n="1"/>' in written
    assert '<pb facs="#facs_3" n="3"/>' in written


def test_marker_empties_the_blank_page_body_only(final_dir):
    """The residual OCR text of the blank page goes; the other pages keep their text."""
    report = tei_blank_marker.project_doc(DOC_ID, [2], dry_run=False)
    written = (final_dir / f"{DOC_ID}_final.xml").read_text(encoding="utf-8")
    assert report["removed"] == {2: ["Reste d'OCR sur une page vide."]}
    assert report["residual"] == {}
    assert "Reste d'OCR" not in written
    assert "Un paragraphe de la premiere page." in written
    assert "Un paragraphe de la troisieme page." in written


def test_marker_dry_run_writes_nothing(final_dir):
    """Dry run reports the change and leaves file and backup directory alone."""
    report = tei_blank_marker.project_doc(DOC_ID, [2], dry_run=True)
    assert report["changed"] is True
    assert (final_dir / f"{DOC_ID}_final.xml").read_text(encoding="utf-8") == FINAL_XML
    assert not tei_blank_marker.BACKUP_DIR.exists()


def test_marker_run_backs_up_the_pre_state(final_dir):
    """The backup is the undo path: it holds the file exactly as it was before the run."""
    tei_blank_marker.project_doc(DOC_ID, [2], dry_run=False)
    backup = tei_blank_marker.BACKUP_DIR / f"{DOC_ID}_final.xml"
    assert backup.read_text(encoding="utf-8") == FINAL_XML


def test_marker_is_idempotent(final_dir):
    """A second run reports no change and leaves the file byte-identical."""
    tei_blank_marker.project_doc(DOC_ID, [2], dry_run=False)
    after_first = (final_dir / f"{DOC_ID}_final.xml").read_bytes()

    second = tei_blank_marker.project_doc(DOC_ID, [2], dry_run=False)

    assert second["changed"] is False
    assert second["typed"] == []
    assert (final_dir / f"{DOC_ID}_final.xml").read_bytes() == after_first


def test_marker_refuses_a_page_beyond_the_pb_count(final_dir):
    """Pagination drift is an error, not a silent miss: nothing is written."""
    report = tei_blank_marker.project_doc(DOC_ID, [9], dry_run=False)
    assert report["ok"] is False
    assert "Pagination-Drift" in report["error"]
    assert (final_dir / f"{DOC_ID}_final.xml").read_text(encoding="utf-8") == FINAL_XML


def test_marker_reports_a_missing_document(final_dir):
    """A manifest without a final TEI is reported, not raised."""
    report = tei_blank_marker.project_doc("9999", [1], dry_run=False)
    assert report["ok"] is False
    assert report["error"] == "final.xml fehlt"


def test_add_type_blank_leaves_an_existing_type_alone():
    """The idempotence guard sits in add_type_blank: an existing @type is never overwritten."""
    tag = '<pb facs="#facs_2" n="2" type="blank" />'
    assert tei_blank_marker.add_type_blank(tag) == (tag, False)
