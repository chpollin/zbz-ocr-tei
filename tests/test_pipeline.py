"""Tests fuer scripts/postprocess/pipeline.py."""

import pytest


class TestPostprocess:
    def test_full_pipeline(self):
        from scripts.postprocess.pipeline import postprocess
        text = "## Titel\n\n**Fett** und Wis-\nsenschaft mit\u00a0Leerzeichen."
        result = postprocess(text)
        # Heading entfernt
        assert "##" not in result
        # Bold entfernt
        assert "**" not in result
        # NBSP normalisiert
        assert "\u00a0" not in result
        # Titel-Text erhalten
        assert "Titel" in result

    def test_empty_string(self):
        from scripts.postprocess.pipeline import postprocess
        assert postprocess("") == ""

    def test_disable_all_steps(self):
        from scripts.postprocess.pipeline import postprocess
        text = "## **Bold** und\u00a0Wis- senschaft"
        result = postprocess(
            text,
            remove_markdown=False,
            normalize=False,
            fix_hyphenation=False,
            fix_whitespace=False,
        )
        # Nichts sollte veraendert werden (nur strip)
        assert "##" in result
        assert "**" in result

    def test_whitespace_normalization(self):
        from scripts.postprocess.pipeline import postprocess
        text = "Zeile 1\n\n\n\n\nZeile 2\n\n\n\nZeile 3"
        result = postprocess(text, remove_markdown=False, normalize=False, fix_hyphenation=False)
        # Maximal 2 Newlines hintereinander
        assert "\n\n\n" not in result

    def test_trailing_whitespace_removed(self):
        from scripts.postprocess.pipeline import postprocess
        text = "Zeile mit Spaces   \nNaechste Zeile"
        result = postprocess(text, remove_markdown=False, normalize=False, fix_hyphenation=False)
        for line in result.split("\n"):
            assert line == line.rstrip()

    def test_multiple_spaces_collapsed(self):
        from scripts.postprocess.pipeline import postprocess
        text = "Wort   mit    vielen   Spaces"
        result = postprocess(text, remove_markdown=False, normalize=False, fix_hyphenation=False)
        assert "  " not in result


class TestProcessFile:
    def test_process_file_read_write(self, tmp_path):
        from scripts.postprocess.pipeline import process_file
        inp = tmp_path / "input.md"
        out = tmp_path / "output.md"
        inp.write_text("## Titel\n\n**Bold** Text", encoding="utf-8")
        result = process_file(inp, out)
        assert "Titel" in result
        assert "**" not in result
        assert out.exists()
        assert out.read_text(encoding="utf-8") == result

    def test_process_file_no_output(self, tmp_path):
        from scripts.postprocess.pipeline import process_file
        inp = tmp_path / "input.md"
        inp.write_text("Einfacher Text", encoding="utf-8")
        result = process_file(inp)
        assert result == "Einfacher Text"


class TestGetProcessingReport:
    def test_report_structure(self):
        from scripts.postprocess.pipeline import get_processing_report
        report = get_processing_report("Ein einfacher Text.")
        assert "length" in report
        assert "lines" in report
        assert "paragraphs" in report
        assert "issues" in report
        assert isinstance(report["issues"], list)

    def test_report_detects_markdown(self):
        from scripts.postprocess.pipeline import get_processing_report
        report = get_processing_report("## Heading\n\n**Bold** text")
        types = [i["type"] for i in report["issues"]]
        assert "markdown_elements" in types

    def test_report_detects_unnormalized(self):
        from scripts.postprocess.pipeline import get_processing_report
        report = get_processing_report("Text mit \u201eAnfuehrungszeichen\u201c")
        types = [i["type"] for i in report["issues"]]
        assert "unnormalized_chars" in types

    def test_report_detects_hyphenation(self):
        from scripts.postprocess.pipeline import get_processing_report
        report = get_processing_report("Wis- senschaft")
        types = [i["type"] for i in report["issues"]]
        assert "potential_hyphenations" in types

    def test_report_clean_text_no_issues(self):
        from scripts.postprocess.pipeline import get_processing_report
        report = get_processing_report("Ein sauberer Text ohne Probleme.")
        assert report["issues"] == []
