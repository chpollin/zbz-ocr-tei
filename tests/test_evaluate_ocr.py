"""Tests fuer scripts/evaluate_ocr.py - Kern-Metriken und Hilfsfunktionen."""

import pytest


class TestLevenshteinDistance:
    def test_identical_strings(self):
        from scripts.evaluate_ocr import _levenshtein_distance
        assert _levenshtein_distance("abc", "abc") == 0

    def test_empty_strings(self):
        from scripts.evaluate_ocr import _levenshtein_distance
        assert _levenshtein_distance("", "") == 0

    def test_one_empty(self):
        from scripts.evaluate_ocr import _levenshtein_distance
        assert _levenshtein_distance("abc", "") == 3
        assert _levenshtein_distance("", "abc") == 3

    def test_single_insertion(self):
        from scripts.evaluate_ocr import _levenshtein_distance
        assert _levenshtein_distance("abc", "abcd") == 1

    def test_single_deletion(self):
        from scripts.evaluate_ocr import _levenshtein_distance
        assert _levenshtein_distance("abcd", "abc") == 1

    def test_single_substitution(self):
        from scripts.evaluate_ocr import _levenshtein_distance
        assert _levenshtein_distance("abc", "axc") == 1

    def test_completely_different(self):
        from scripts.evaluate_ocr import _levenshtein_distance
        assert _levenshtein_distance("abc", "xyz") == 3

    def test_known_distance(self):
        from scripts.evaluate_ocr import _levenshtein_distance
        # "kitten" -> "sitting": k->s, e->i, +g = 3
        assert _levenshtein_distance("kitten", "sitting") == 3


class TestCalculateCER:
    def test_identical(self):
        from scripts.evaluate_ocr import calculate_cer
        assert calculate_cer("Hallo Welt", "Hallo Welt") == 0.0

    def test_empty_reference_empty_hypothesis(self):
        from scripts.evaluate_ocr import calculate_cer
        assert calculate_cer("", "") == 0.0

    def test_empty_reference_nonempty_hypothesis(self):
        from scripts.evaluate_ocr import calculate_cer
        assert calculate_cer("", "abc") == 1.0

    def test_completely_different(self):
        from scripts.evaluate_ocr import calculate_cer
        cer = calculate_cer("aaa", "bbb")
        assert cer == 1.0  # 3 substitutions / 3 chars

    def test_one_error(self):
        from scripts.evaluate_ocr import calculate_cer
        cer = calculate_cer("abcd", "abxd")
        assert cer == pytest.approx(0.25)  # 1 error / 4 chars

    def test_cer_can_exceed_one(self):
        from scripts.evaluate_ocr import calculate_cer
        # hypothesis much longer than reference -> CER > 1.0
        cer = calculate_cer("a", "abcdef")
        assert cer > 1.0


class TestCalculateWER:
    def test_identical(self):
        from scripts.evaluate_ocr import calculate_wer
        assert calculate_wer("hello world", "hello world") == 0.0

    def test_empty_both(self):
        from scripts.evaluate_ocr import calculate_wer
        assert calculate_wer("", "") == 0.0

    def test_empty_reference(self):
        from scripts.evaluate_ocr import calculate_wer
        assert calculate_wer("", "some words") == 1.0

    def test_one_word_error(self):
        from scripts.evaluate_ocr import calculate_wer
        wer = calculate_wer("die Wissenschaft ist wichtig", "die Wissenschaft ist falsch")
        assert wer == pytest.approx(0.25)  # 1 error / 4 words

    def test_all_wrong(self):
        from scripts.evaluate_ocr import calculate_wer
        wer = calculate_wer("eins zwei drei", "vier fuenf sechs")
        assert wer == 1.0


class TestNormalizeText:
    def test_whitespace_collapse(self):
        from scripts.evaluate_ocr import normalize_text
        assert normalize_text("hello   world") == "hello world"

    def test_newlines_collapsed(self):
        from scripts.evaluate_ocr import normalize_text
        assert normalize_text("hello\n\nworld") == "hello world"

    def test_tabs_collapsed(self):
        from scripts.evaluate_ocr import normalize_text
        assert normalize_text("hello\tworld") == "hello world"

    def test_strip(self):
        from scripts.evaluate_ocr import normalize_text
        assert normalize_text("  text  ") == "text"

    def test_empty_string(self):
        from scripts.evaluate_ocr import normalize_text
        assert normalize_text("") == ""


class TestFindDifferences:
    def test_identical_no_diffs(self):
        from scripts.evaluate_ocr import find_differences
        assert find_differences("abc", "abc") == []

    def test_single_replace(self):
        from scripts.evaluate_ocr import find_differences
        diffs = find_differences("abc", "axc")
        assert len(diffs) == 1
        assert diffs[0]["type"] == "replace"
        assert diffs[0]["reference"] == "b"
        assert diffs[0]["hypothesis"] == "x"

    def test_insertion(self):
        from scripts.evaluate_ocr import find_differences
        diffs = find_differences("ac", "abc")
        assert any(d["type"] == "insert" for d in diffs)

    def test_deletion(self):
        from scripts.evaluate_ocr import find_differences
        diffs = find_differences("abc", "ac")
        assert any(d["type"] == "delete" for d in diffs)

    def test_has_context(self):
        from scripts.evaluate_ocr import find_differences
        diffs = find_differences("abcdef", "abxdef")
        assert diffs[0]["context"]  # context should be non-empty


class TestStripMarkdown:
    def test_bold(self):
        from scripts.evaluate_ocr import _strip_markdown
        assert _strip_markdown("**bold**") == "bold"

    def test_italic(self):
        from scripts.evaluate_ocr import _strip_markdown
        assert _strip_markdown("*italic*") == "italic"

    def test_headers(self):
        from scripts.evaluate_ocr import _strip_markdown
        assert _strip_markdown("## Header").strip() == "Header"

    def test_no_markdown(self):
        from scripts.evaluate_ocr import _strip_markdown
        assert _strip_markdown("plain text") == "plain text"


class TestFindPhraseInText:
    def test_exact_match(self):
        from scripts.evaluate_ocr import _find_phrase_in_text
        assert _find_phrase_in_text("world", "hello world") == 6

    def test_no_match(self):
        from scripts.evaluate_ocr import _find_phrase_in_text
        assert _find_phrase_in_text("xyz", "hello world") == -1

    def test_markdown_fallback(self):
        from scripts.evaluate_ocr import _find_phrase_in_text
        # Phrase without markdown should be found in markdown text
        pos = _find_phrase_in_text("bold text", "some **bold text** here")
        assert pos != -1


class TestExtractTextFromTei:
    def test_simple_tei(self, tmp_path):
        from scripts.evaluate_ocr import extract_text_from_tei
        tei = tmp_path / "test.xml"
        tei.write_text(
            '<?xml version="1.0"?>'
            '<TEI xmlns="http://www.tei-c.org/ns/1.0">'
            '<teiHeader/>'
            '<text><body><p>Hallo Welt</p></body></text>'
            '</TEI>',
            encoding="utf-8",
        )
        result = extract_text_from_tei(tei)
        assert "Hallo Welt" in result

    def test_no_body(self, tmp_path):
        from scripts.evaluate_ocr import extract_text_from_tei
        tei = tmp_path / "empty.xml"
        tei.write_text(
            '<?xml version="1.0"?>'
            '<TEI xmlns="http://www.tei-c.org/ns/1.0">'
            '<teiHeader/><text></text></TEI>',
            encoding="utf-8",
        )
        result = extract_text_from_tei(tei)
        assert result == ""

    def test_lb_break_no(self, tmp_path):
        from scripts.evaluate_ocr import extract_text_from_tei
        tei = tmp_path / "lb.xml"
        tei.write_text(
            '<?xml version="1.0"?>'
            '<TEI xmlns="http://www.tei-c.org/ns/1.0">'
            '<teiHeader/>'
            '<text><body><p>Wissen<lb break="no"/>schaft</p></body></text>'
            '</TEI>',
            encoding="utf-8",
        )
        result = extract_text_from_tei(tei)
        assert "Wissenschaft" in result
