"""Tests fuer ungetestete Funktionen in scripts/tei/tei_generator.py."""


class TestSplitParagraphs:
    def test_two_paragraphs(self):
        from scripts.tei.tei_generator import split_paragraphs
        result = split_paragraphs("Absatz 1\n\nAbsatz 2")
        assert result == ["Absatz 1", "Absatz 2"]

    def test_single_paragraph(self):
        from scripts.tei.tei_generator import split_paragraphs
        result = split_paragraphs("Nur ein Absatz")
        assert result == ["Nur ein Absatz"]

    def test_empty_string(self):
        from scripts.tei.tei_generator import split_paragraphs
        result = split_paragraphs("")
        assert result == []

    def test_whitespace_only(self):
        from scripts.tei.tei_generator import split_paragraphs
        result = split_paragraphs("   \n\n   ")
        assert result == []

    def test_multiple_blank_lines(self):
        from scripts.tei.tei_generator import split_paragraphs
        result = split_paragraphs("A\n\n\n\nB")
        assert result == ["A", "B"]

    def test_strips_paragraphs(self):
        from scripts.tei.tei_generator import split_paragraphs
        result = split_paragraphs("  A  \n\n  B  ")
        assert result == ["A", "B"]


class TestMatchParagraphsToRegions:
    def test_one_to_one_matching(self):
        from scripts.tei.tei_generator import match_paragraphs_to_regions
        paras = ["Titel", "Text"]
        regions = [
            {"zbz_tag": "zb_heading", "bbox": {"y_pct": 10, "x_pct": 0, "w_pct": 100, "h_pct": 5}},
            {"zbz_tag": "zb_paragraph", "bbox": {"y_pct": 20, "x_pct": 0, "w_pct": 100, "h_pct": 30}},
        ]
        result = match_paragraphs_to_regions(paras, regions)
        assert len(result) == 2
        assert result[0]["zbz_tag"] == "zb_heading"
        assert result[0]["text"] == "Titel"
        assert result[1]["zbz_tag"] == "zb_paragraph"

    def test_more_paras_than_regions(self):
        from scripts.tei.tei_generator import match_paragraphs_to_regions
        paras = ["A", "B", "C"]
        regions = [
            {"zbz_tag": "zb_heading", "bbox": {"y_pct": 10, "x_pct": 0, "w_pct": 100, "h_pct": 5}},
        ]
        result = match_paragraphs_to_regions(paras, regions)
        assert len(result) == 3
        assert result[0]["zbz_tag"] == "zb_heading"
        # Ueberschuessige als zb_paragraph
        assert result[1]["zbz_tag"] == "zb_paragraph"
        assert result[2]["zbz_tag"] == "zb_paragraph"

    def test_filter_regions_excluded(self):
        from scripts.tei.tei_generator import match_paragraphs_to_regions
        paras = ["Text"]
        regions = [
            {"zbz_tag": "_filter", "bbox": {"y_pct": 5, "x_pct": 0, "w_pct": 100, "h_pct": 3}},
            {"zbz_tag": "zb_paragraph", "bbox": {"y_pct": 20, "x_pct": 0, "w_pct": 100, "h_pct": 30}},
        ]
        result = match_paragraphs_to_regions(paras, regions)
        assert len(result) == 1
        assert result[0]["zbz_tag"] == "zb_paragraph"

    def test_empty_paragraphs(self):
        from scripts.tei.tei_generator import match_paragraphs_to_regions
        result = match_paragraphs_to_regions([], [])
        assert result == []

    def test_sorts_by_y_position(self):
        from scripts.tei.tei_generator import match_paragraphs_to_regions
        paras = ["A", "B"]
        regions = [
            {"zbz_tag": "footnote", "bbox": {"y_pct": 90, "x_pct": 0, "w_pct": 100, "h_pct": 5}},
            {"zbz_tag": "zb_heading", "bbox": {"y_pct": 10, "x_pct": 0, "w_pct": 100, "h_pct": 5}},
        ]
        result = match_paragraphs_to_regions(paras, regions)
        # zb_heading (y=10) sollte zuerst kommen
        assert result[0]["zbz_tag"] == "zb_heading"
        assert result[1]["zbz_tag"] == "footnote"


class TestGenerateTeiPage:
    def test_basic_output(self):
        from scripts.tei.tei_generator import generate_tei_page
        xml = generate_tei_page("2310", 1, "Hallo Welt", None)
        assert '<?xml version="1.0"' in xml
        assert 'xmlns="http://www.tei-c.org/ns/1.0"' in xml
        assert 'type="naegeli"' in xml
        assert "Hallo Welt" in xml
        assert '<pb facs="#facs_1"' in xml

    def test_with_metadata(self):
        from scripts.tei.tei_generator import generate_tei_page
        meta = {
            "title": "Testtitel",
            "author": "Max Muster",
            "date": "1960",
            "lang": "deu",
            "desc": "Beschreibung",
        }
        xml = generate_tei_page("2310", 1, "Text", None, meta)
        assert "Testtitel" in xml
        assert "Max Muster" in xml
        assert "1960" in xml
        assert 'ident="deu"' in xml

    def test_heading_tag(self):
        from scripts.tei.tei_generator import generate_tei_page
        layout = {
            "regions": [
                {"zbz_tag": "zb_heading", "bbox": {"y_pct": 10, "x_pct": 0, "w_pct": 100, "h_pct": 5}},
            ],
            "image_width": 1000,
            "image_height": 1500,
        }
        xml = generate_tei_page("2310", 1, "## Titel", layout)
        assert "<head" in xml
        assert "Titel" in xml
        # ## sollte entfernt worden sein
        assert "##" not in xml

    def test_footnote_tag(self):
        from scripts.tei.tei_generator import generate_tei_page
        layout = {
            "regions": [
                {"zbz_tag": "footnote", "bbox": {"y_pct": 90, "x_pct": 0, "w_pct": 100, "h_pct": 5}},
            ],
            "image_width": 1000,
            "image_height": 1500,
        }
        xml = generate_tei_page("2310", 1, "Fussnote", layout)
        assert 'place="foot"' in xml

    def test_no_layout_all_paragraphs(self):
        from scripts.tei.tei_generator import generate_tei_page
        import re
        xml = generate_tei_page("2310", 1, "Abs 1\n\nAbs 2", None)
        # Zaehle nur <p> und <p ...> Tags (nicht <pb>, <publisher> etc.)
        body_ps = re.findall(r'<p[ >]', xml)
        assert len(body_ps) == 2

    def test_entity_annotation(self):
        from scripts.tei.tei_generator import generate_tei_page
        xml = generate_tei_page("2310", 1, "Karl Jaspers war wichtig.", None)
        assert "<persName" in xml
        assert "GND:118557106" in xml

    def test_bold_inline(self):
        from scripts.tei.tei_generator import generate_tei_page
        xml = generate_tei_page("2310", 1, "Ein **fettes** Wort.", None)
        assert '<hi rendition="#b">fettes</hi>' in xml

    def test_facsimile_with_layout(self):
        from scripts.tei.tei_generator import generate_tei_page
        layout = {
            "regions": [
                {"zbz_tag": "zb_paragraph", "bbox": {"y_pct": 20, "x_pct": 10, "w_pct": 80, "h_pct": 60}},
            ],
            "image_width": 1000,
            "image_height": 1500,
        }
        xml = generate_tei_page("2310", 1, "Text", layout)
        assert "<facsimile>" in xml
        assert "<zone" in xml
        assert "</facsimile>" in xml

    def test_no_facsimile_without_layout(self):
        from scripts.tei.tei_generator import generate_tei_page
        xml = generate_tei_page("2310", 1, "Text", None)
        assert "<facsimile>" not in xml

    def test_xml_escape(self):
        from scripts.tei.tei_generator import generate_tei_page
        xml = generate_tei_page("2310", 1, "A < B & C > D", None)
        assert "&lt;" in xml
        assert "&amp;" in xml
        assert "&gt;" in xml

    def test_lang_mapping(self):
        from scripts.tei.tei_generator import generate_tei_page
        meta_fr = {"lang": "FR"}
        xml = generate_tei_page("2310", 1, "Text", None, meta_fr)
        assert 'ident="fra"' in xml

        meta_de = {"lang": "DE"}
        xml = generate_tei_page("2310", 1, "Text", None, meta_de)
        assert 'ident="deu"' in xml

        meta_iso = {"lang": "fra"}
        xml = generate_tei_page("2310", 1, "Text", None, meta_iso)
        assert 'ident="fra"' in xml
