"""Tests for the PAGE-XML generator (scripts/layout/page_xml_generator.py).

The generator turns layout regions plus OCR markdown into PAGE-XML 2013-07-15, the
Transkribus round-trip format. Its pure transforms (paragraph split, percent bbox to
polygon, paragraph-to-region matching) and the emitted element shape (ReadingOrder,
TextRegion custom attribute, one TextLine per region, empty region-level TextEquiv) are
pinned here on synthetic regions, without touching disk beyond tmp_path.
"""

import pytest

from scripts.layout.page_xml_generator import (
    PAGE_NS,
    XSI_NS,
    bbox_to_coords,
    generate_page_xml,
    match_ocr_to_regions,
    split_paragraphs,
)

IMG_W, IMG_H = 1000, 2000


def _region(y_pct, tag="zb_paragraph", **bbox):
    box = {"x_pct": 10.0, "y_pct": y_pct, "w_pct": 40.0, "h_pct": 10.0}
    box.update(bbox)
    return {"zbz_tag": tag, "bbox": box}


def _find(root, local_name):
    return root.findall(f".//{{{PAGE_NS}}}{local_name}")


# ---------------------------------------------------------------------------
# Pure transforms
# ---------------------------------------------------------------------------

def test_split_paragraphs_splits_on_blank_lines_and_trims():
    assert split_paragraphs("  eins\n\n  zwei \n\n\n drei ") == ["eins", "zwei", "drei"]


def test_split_paragraphs_keeps_single_newlines_inside_a_paragraph():
    assert split_paragraphs("eins\nzwei") == ["eins\nzwei"]


def test_split_paragraphs_of_blank_text_is_empty():
    assert split_paragraphs("   \n\n  ") == []


def test_bbox_to_coords_emits_four_clockwise_corners():
    bbox = {"x_pct": 10.0, "y_pct": 20.0, "w_pct": 30.0, "h_pct": 25.0}
    assert bbox_to_coords(bbox, IMG_W, IMG_H) == "100,400 400,400 400,900 100,900"


def test_bbox_to_coords_clamps_to_the_page():
    bbox = {"x_pct": -5.0, "y_pct": -5.0, "w_pct": 200.0, "h_pct": 200.0}
    assert bbox_to_coords(bbox, IMG_W, IMG_H) == "0,0 1000,0 1000,2000 0,2000"


# ---------------------------------------------------------------------------
# OCR to region matching
# ---------------------------------------------------------------------------

def test_matching_pairs_paragraphs_with_regions_top_down():
    regions = [_region(50.0), _region(10.0)]
    matched = match_ocr_to_regions("oben\n\nunten", regions)
    assert [text for _, text in matched] == ["oben", "unten"]
    assert [r["bbox"]["y_pct"] for r, _ in matched] == [10.0, 50.0]


def test_matching_skips_filtered_and_untagged_regions():
    regions = [_region(10.0, tag="_filter"), _region(20.0, tag="_skip"),
               _region(30.0, tag=None), {"zbz_tag": "zb_paragraph"}, _region(40.0)]
    matched = match_ocr_to_regions("text", regions)
    assert len(matched) == 1
    assert matched[0][0]["bbox"]["y_pct"] == 40.0


def test_matching_leaves_surplus_regions_empty():
    matched = match_ocr_to_regions("nur eins", [_region(10.0), _region(20.0)])
    assert [text for _, text in matched] == ["nur eins", ""]


def test_matching_appends_surplus_paragraphs_to_the_last_region():
    matched = match_ocr_to_regions("eins\n\nzwei\n\ndrei", [_region(10.0)])
    assert [text for _, text in matched] == ["eins\n\nzwei\n\ndrei"]


def test_matching_without_ocr_text_yields_empty_texts():
    matched = match_ocr_to_regions(None, [_region(10.0)])
    assert [text for _, text in matched] == [""]


# ---------------------------------------------------------------------------
# PAGE-XML shape
# ---------------------------------------------------------------------------

def test_root_declares_the_page_schema():
    root = generate_page_xml("2310", 2, [], IMG_W, IMG_H)
    assert root.tag == f"{{{PAGE_NS}}}PcGts"
    assert root.get(f"{{{XSI_NS}}}schemaLocation").startswith(PAGE_NS)


def test_metadata_records_the_layout_source():
    root = generate_page_xml("2310", 2, [], IMG_W, IMG_H, layout_source="gemini")
    creator = root.find(f"{{{PAGE_NS}}}Metadata/{{{PAGE_NS}}}Creator")
    assert creator.text == "zbz-ocr-tei:page_xml_generator:layout=gemini"


def test_page_element_carries_padded_image_name_and_dimensions():
    root = generate_page_xml("2310", 2, [], IMG_W, IMG_H)
    page = root.find(f"{{{PAGE_NS}}}Page")
    assert page.get("imageFilename") == "2310_p002.png"
    assert (page.get("imageWidth"), page.get("imageHeight")) == ("1000", "2000")


def test_page_without_regions_carries_no_reading_order():
    root = generate_page_xml("2310", 2, [], IMG_W, IMG_H)
    assert _find(root, "ReadingOrder") == []
    assert _find(root, "TextRegion") == []


def test_reading_order_indexes_regions_from_zero():
    matched = [(_region(10.0), "eins"), (_region(50.0), "zwei")]
    root = generate_page_xml("2310", 1, matched, IMG_W, IMG_H)
    group = root.find(f".//{{{PAGE_NS}}}ReadingOrder/{{{PAGE_NS}}}OrderedGroup")
    assert group.get("id") == "ro_1"
    refs = group.findall(f"{{{PAGE_NS}}}RegionRefIndexed")
    assert [(r.get("index"), r.get("regionRef")) for r in refs] == [("0", "r_1"),
                                                                   ("1", "r_2")]


def test_text_region_custom_attribute_maps_the_zbz_tag():
    matched = [(_region(10.0, tag="zb_heading"), "Titel")]
    root = generate_page_xml("2310", 1, matched, IMG_W, IMG_H)
    region = _find(root, "TextRegion")[0]
    assert region.get("id") == "r_1"
    assert region.get("custom") == "readingOrder {index:0;} structure {type:heading;}"


def test_unknown_zbz_tag_falls_back_to_paragraph():
    matched = [(_region(10.0, tag="zb_unknown"), "Text")]
    root = generate_page_xml("2310", 1, matched, IMG_W, IMG_H)
    assert "structure {type:paragraph;}" in _find(root, "TextRegion")[0].get("custom")


def test_region_and_line_share_the_bbox_polygon():
    matched = [(_region(20.0), "Text")]
    root = generate_page_xml("2310", 1, matched, IMG_W, IMG_H)
    points = [c.get("points") for c in _find(root, "Coords")]
    assert points == ["100,400 500,400 500,600 100,600"] * 2


def test_text_line_strips_markdown_headings():
    matched = [(_region(10.0, tag="zb_heading"), "## Titel\n\nZeile")]
    root = generate_page_xml("2310", 1, matched, IMG_W, IMG_H)
    line = _find(root, "TextLine")[0]
    assert line.get("id") == "r_1_tl_1"
    assert line.get("custom") == "readingOrder {index:0;}"
    assert line.find(f"{{{PAGE_NS}}}TextEquiv/{{{PAGE_NS}}}Unicode").text == "Titel\n\nZeile"


def test_region_level_text_equiv_stays_empty():
    matched = [(_region(10.0), "Text")]
    root = generate_page_xml("2310", 1, matched, IMG_W, IMG_H)
    region_unicode = _find(root, "TextRegion")[0].find(
        f"{{{PAGE_NS}}}TextEquiv/{{{PAGE_NS}}}Unicode")
    assert region_unicode.text == ""


def test_region_without_text_carries_no_text_line():
    matched = [(_region(10.0), "")]
    root = generate_page_xml("2310", 1, matched, IMG_W, IMG_H)
    assert _find(root, "TextLine") == []
    assert len(_find(root, "TextRegion")) == 1


def test_region_without_bbox_carries_no_coords():
    matched = [({"zbz_tag": "zb_paragraph"}, "Text")]
    root = generate_page_xml("2310", 1, matched, IMG_W, IMG_H)
    assert _find(root, "Coords") == []
    assert _find(root, "TextLine")


@pytest.mark.parametrize("img_w,img_h", [(None, 2000), (1000, None), (0, 0)])
def test_missing_dimensions_suppress_coords_and_default_to_zero(img_w, img_h):
    matched = [(_region(10.0), "Text")]
    root = generate_page_xml("2310", 1, matched, img_w, img_h)
    page = root.find(f"{{{PAGE_NS}}}Page")
    assert page.get("imageWidth") == str(img_w or 0)
    assert page.get("imageHeight") == str(img_h or 0)
    assert _find(root, "Coords") == []
