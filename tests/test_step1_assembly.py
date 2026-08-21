"""Synthetic end-to-end contract for the TEI generator without any API call.

Covers the free path of the pipeline (``tei_unified --step 1`` plus assembly): step 1
builds a page scaffold from OCR markdown and layout JSON, step 3 assembles the scaffolds
into the delivered document. The Gemini refinement of step 2 is skipped entirely, which is
exactly what ``assemble_document`` supports: it consumes page fragments, and a step-1
scaffold is a valid fragment, so no step-2 surrogate is needed.

The generator produces the deliverable and was the least covered part of the suite; the
fixtures here pin its structural promises (pb numbering, region-to-paragraph mapping,
facsimile zones, reading order, RelaxNG validity) on data that lives under ``tmp_path``.
Loader directories are monkeypatched on ``scripts.core.loaders`` as in
``tests/test_curated_loaders.py``, so no ``output/`` file is read.
"""

from __future__ import annotations

import json

import pytest
from lxml import etree as _etree

from scripts.config import TEI_NS, TEI_SCHEMA_PATH
from scripts.core import loaders
from scripts.tei import tei_step1
from scripts.tei.tei_step3 import assemble_document

DOC_ID = "9001"

METADATA = {
    "title": "Le probleme de la liberte",
    "author": "Hersch, Jeanne",
    "date": "1975",
    "pub_form": "journalArticle",
    "lang": "fra",
}

PAGE1_HEAD = "Le probleme de la liberte"
PAGE1_PARA_A = "Premier paragraphe de la page un, assez long pour rester du texte courant."
PAGE1_PARA_B = "Second paragraphe de la page un, lui aussi du texte courant."
PAGE2_PARA = "Le seul paragraphe de la page deux."


def _region(tag: str, x: float, y: float, w: float, h: float) -> dict:
    return {"zbz_tag": tag, "label": "text",
            "bbox": {"x_pct": x, "y_pct": y, "w_pct": w, "h_pct": h}}


@pytest.fixture
def corpus(tmp_path, monkeypatch):
    """A two-page synthetic document: OCR markdown plus single-column Docling layout."""
    ocr_dir = tmp_path / "mistral_results"
    layout_dir = tmp_path / "layout"
    doc_layout = layout_dir / DOC_ID
    doc_layout.mkdir(parents=True)
    ocr_dir.mkdir()

    monkeypatch.setattr(loaders, "_OCR_DIRS", [ocr_dir])
    monkeypatch.setattr(loaders, "LAYOUT_DIR", layout_dir)
    # process_page_step1 caches the interpolated printed page numbers per doc_id.
    monkeypatch.setattr(tei_step1, "_INTERP_CACHE", {})

    (ocr_dir / f"{DOC_ID}_p1.md").write_text(
        f"# {PAGE1_HEAD}\n\n{PAGE1_PARA_A}\n\n{PAGE1_PARA_B}\n", encoding="utf-8")
    (ocr_dir / f"{DOC_ID}_p2.md").write_text(f"{PAGE2_PARA}\n", encoding="utf-8")

    (doc_layout / f"{DOC_ID}_p001_layout.json").write_text(json.dumps({
        "image_width": 1000, "image_height": 1500,
        "regions": [_region("zb_heading", 10, 5, 80, 5),
                    _region("zb_paragraph", 10, 15, 80, 20),
                    _region("zb_paragraph", 10, 40, 80, 20)],
    }), encoding="utf-8")
    (doc_layout / f"{DOC_ID}_p002_layout.json").write_text(json.dumps({
        "image_width": 1000, "image_height": 1500,
        "regions": [_region("zb_paragraph", 10, 15, 80, 20)],
    }), encoding="utf-8")
    return ocr_dir, doc_layout


def _generate(genre: str | None = None, pages: tuple[int, ...] = (1, 2)) -> str:
    """Run step 1 for each page and assemble the document, exactly as --step 1 would."""
    page_teis: dict[int, str] = {}
    page_facsimiles: dict[int, dict] = {}
    for page in pages:
        fragment, facsimile = tei_step1.process_page_step1(DOC_ID, page, METADATA, genre)
        page_teis[page] = fragment
        page_facsimiles[page] = facsimile
    return assemble_document(DOC_ID, page_teis, METADATA, page_facsimiles)


def _root(xml: str):
    return _etree.fromstring(xml.encode("utf-8"))


def _texts(root, tag: str) -> list[str]:
    return [" ".join("".join(el.itertext()).split())
            for el in root.iter(f"{{{TEI_NS}}}{tag}")]


# --- page breaks -----------------------------------------------------------------

def test_one_pb_per_page_numbered_by_scan_position(corpus):
    """Without a printed page number in the layout chrome, pb@n is the scan number."""
    root = _root(_generate())
    pbs = list(root.iter(f"{{{TEI_NS}}}pb"))
    assert [pb.get("n") for pb in pbs] == ["1", "2"]
    assert [pb.get("facs") for pb in pbs] == ["#facs_1", "#facs_2"]


def test_pages_are_merged_into_one_document_div(corpus):
    """Step 3 merges the per-page divs; both page breaks end up inside a single div."""
    root = _root(_generate())
    body = root.find(f".//{{{TEI_NS}}}body")
    top_divs = body.findall(f"{{{TEI_NS}}}div")
    assert len(top_divs) == 1
    assert len(top_divs[0].findall(f"{{{TEI_NS}}}pb")) == 2


# --- region to paragraph mapping -------------------------------------------------

def test_each_ocr_paragraph_becomes_one_p_with_its_region(corpus):
    """A known region text ends up in exactly one <p> carrying that region's zone id."""
    root = _root(_generate())
    paragraphs = {" ".join("".join(p.itertext()).split()): p.get("facs")
                  for p in root.iter(f"{{{TEI_NS}}}p")}
    assert paragraphs[PAGE1_PARA_A] == "#facs_1_r_2"
    assert paragraphs[PAGE1_PARA_B] == "#facs_1_r_3"
    assert paragraphs[PAGE2_PARA] == "#facs_2_r_1"
    assert len(paragraphs) == 3


def test_heading_region_becomes_head_not_paragraph(corpus):
    """A zb_heading region is a <head>, and the running text stays out of it."""
    root = _root(_generate())
    heads = _texts(root, "head")
    assert heads == [PAGE1_HEAD]
    assert PAGE1_PARA_A not in heads


def test_footnote_region_becomes_note_with_page_scoped_id(corpus):
    """A footnote region becomes <note place="foot"> with the guideline id fn{page}-{nr}."""
    ocr_dir, doc_layout = corpus
    (ocr_dir / f"{DOC_ID}_p2.md").write_text(
        f"{PAGE2_PARA}\n\nUne note en bas de page.\n", encoding="utf-8")
    (doc_layout / f"{DOC_ID}_p002_layout.json").write_text(json.dumps({
        "image_width": 1000, "image_height": 1500,
        "regions": [_region("zb_paragraph", 10, 15, 80, 20),
                    _region("footnote", 10, 85, 80, 5)],
    }), encoding="utf-8")
    root = _root(_generate())
    notes = list(root.iter(f"{{{TEI_NS}}}note"))
    assert len(notes) == 1
    assert notes[0].get("place") == "foot"
    assert notes[0].get("n") == "1"
    assert notes[0].get("{http://www.w3.org/XML/1998/namespace}id") == "fn2-1"


def test_two_column_page_is_emitted_in_column_reading_order(corpus):
    """Blocks follow the column-aware reading order, not the raw y order (W19 defect class)."""
    ocr_dir, doc_layout = corpus
    left_top, right_top, left_bottom = "Colonne gauche haut.", "Colonne droite haut.", "Colonne gauche bas."
    (ocr_dir / f"{DOC_ID}_p2.md").write_text(
        f"{left_top}\n\n{left_bottom}\n\n{right_top}\n", encoding="utf-8")
    # Layout order is left-top, right-top, left-bottom; the canonical order finishes the
    # left column first, so the OCR paragraphs are given in that canonical order.
    (doc_layout / f"{DOC_ID}_p002_layout.json").write_text(json.dumps({
        "image_width": 1000, "image_height": 1500,
        "regions": [_region("zb_paragraph", 5, 10, 40, 10),
                    _region("zb_paragraph", 55, 12, 40, 10),
                    _region("zb_paragraph", 5, 40, 40, 10)],
    }), encoding="utf-8")
    root = _root(_generate(pages=(2,)))
    order = [(" ".join("".join(p.itertext()).split()), p.get("facs"))
             for p in root.iter(f"{{{TEI_NS}}}p")]
    assert order == [(left_top, "#facs_2_r_1"),
                     (left_bottom, "#facs_2_r_2"),
                     (right_top, "#facs_2_r_3")]


def test_line_breaks_inside_a_paragraph_become_numbered_lb(corpus):
    """OCR line breaks survive as <lb/> with the N001 counter reset per element."""
    ocr_dir, _ = corpus
    (ocr_dir / f"{DOC_ID}_p2.md").write_text(
        "Premiere ligne du paragraphe\nseconde ligne du paragraphe\n", encoding="utf-8")
    root = _root(_generate(pages=(2,)))
    lbs = list(root.iter(f"{{{TEI_NS}}}lb"))
    assert [lb.get("n") for lb in lbs] == ["N001"]
    assert lbs[0].get("facs") == "#facs_2_l_1_1"


# --- facsimile -------------------------------------------------------------------

def test_one_surface_per_page_with_page_scoped_zone_ids(corpus):
    """Every page gets a surface facs_{page}; each matched region gets its zone."""
    root = _root(_generate())
    surfaces = list(root.iter(f"{{{TEI_NS}}}surface"))
    ids = [s.get("{http://www.w3.org/XML/1998/namespace}id") for s in surfaces]
    assert ids == ["facs_1", "facs_2"]
    zone_ids = [z.get("{http://www.w3.org/XML/1998/namespace}id")
                for z in root.iter(f"{{{TEI_NS}}}zone")]
    assert zone_ids == ["facs_1_r_1", "facs_1_r_2", "facs_1_r_3", "facs_2_r_1"]


def test_zone_coordinates_are_the_percentage_bbox_scaled_to_the_image(corpus):
    """A bbox at 10/15 percent of a 1000x1500 image becomes ulx=100, uly=225."""
    root = _root(_generate())
    zone = next(z for z in root.iter(f"{{{TEI_NS}}}zone")
                if z.get("{http://www.w3.org/XML/1998/namespace}id") == "facs_1_r_2")
    assert (zone.get("ulx"), zone.get("uly")) == ("100", "225")
    assert (zone.get("lrx"), zone.get("lry")) == ("900", "525")


def test_every_surface_carries_a_graphic_before_its_zones(corpus):
    """The pb@facs reference resolves on its own: graphic is the first child of surface."""
    root = _root(_generate())
    for surface in root.iter(f"{{{TEI_NS}}}surface"):
        assert surface[0].tag == f"{{{TEI_NS}}}graphic"
        assert surface[0].get("url").endswith(".png")


def test_surface_count_matches_pb_count(corpus):
    """W3 of the validator: as many surfaces as page breaks."""
    root = _root(_generate())
    assert len(list(root.iter(f"{{{TEI_NS}}}surface"))) == len(list(root.iter(f"{{{TEI_NS}}}pb")))


# --- header and schema -----------------------------------------------------------

def test_header_carries_the_delivery_contract_fields(corpus):
    """idno/docID, biblStruct and langUsage are part of the delivered header (E69)."""
    root = _root(_generate())
    idno = root.find(f".//{{{TEI_NS}}}idno")
    assert idno is not None and idno.get("type") == "docID" and idno.text == DOC_ID
    assert root.find(f".//{{{TEI_NS}}}biblStruct").get("type") == "journalArticle"
    assert [lg.get("ident") for lg in root.iter(f"{{{TEI_NS}}}language")] == ["fra"]


def test_assembled_document_is_schema_valid(corpus):
    """The assembled document validates against the delivery schema zbz_hersch.rng."""
    schema = _etree.RelaxNG(_etree.parse(str(TEI_SCHEMA_PATH)))
    doc = _root(_generate())
    assert schema.validate(doc), str(schema.error_log)


@pytest.mark.parametrize("genre,div_type", [
    ("review", "review"),
    ("interview", "interview"),
    ("encyclopedia", "entry"),
])
def test_genre_selects_the_div_type_and_stays_schema_valid(corpus, genre, div_type):
    """The inferred genre reaches the document div, and the result stays schema valid."""
    schema = _etree.RelaxNG(_etree.parse(str(TEI_SCHEMA_PATH)))
    doc = _root(_generate(genre=genre))
    body = doc.find(f".//{{{TEI_NS}}}body")
    assert [d.get("type") for d in body.findall(f"{{{TEI_NS}}}div")] == [div_type]
    assert schema.validate(doc), str(schema.error_log)


def test_page_without_ocr_yields_no_fragment(corpus):
    """A page with no OCR text produces nothing; the caller skips it (no empty div)."""
    assert tei_step1.process_page_step1(DOC_ID, 7, METADATA, None) == ("", {})
