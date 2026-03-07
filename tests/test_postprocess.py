"""Tests fuer postprocess-Module."""


class TestNormalize:
    def test_normalize_quotes(self):
        from scripts.postprocess.normalize import normalize_text
        # U+201E (double low-9 quote) is mapped
        result = normalize_text("\u201eTitel")
        assert "\u201e" not in result
        assert result == '"Titel'

    def test_normalize_guillemets(self):
        from scripts.postprocess.normalize import normalize_text
        assert normalize_text("\u00abTexte\u00bb") == '"Texte"'

    def test_normalize_dashes(self):
        from scripts.postprocess.normalize import normalize_text
        assert normalize_text("A \u2013 B") == "A - B"
        assert normalize_text("A \u2014 B") == "A - B"

    def test_normalize_spaces(self):
        from scripts.postprocess.normalize import normalize_text
        assert normalize_text("Mot\u00a0fin") == "Mot fin"

    def test_normalize_ellipsis(self):
        from scripts.postprocess.normalize import normalize_text
        assert normalize_text("Ende\u2026") == "Ende..."

    def test_normalize_custom_rules(self):
        from scripts.postprocess.normalize import normalize_text
        result = normalize_text("ABC", custom_rules={"A": "X"})
        assert result == "XBC"

    def test_get_normalize_stats(self):
        from scripts.postprocess.normalize import get_normalize_stats
        stats = get_normalize_stats("\u201eTest\u201c und \u2013")
        assert len(stats) >= 2  # mindestens \u201e und \u2013


    def test_normalize_empty_string(self):
        from scripts.postprocess.normalize import normalize_text
        assert normalize_text("") == ""

    def test_normalize_multiplication(self):
        from scripts.postprocess.normalize import normalize_text
        assert normalize_text("17\u00d725") == "17x25"

    def test_get_normalize_stats_clean_text(self):
        from scripts.postprocess.normalize import get_normalize_stats
        assert get_normalize_stats("Normaler Text") == {}


class TestDehyphenate:
    def test_simple_dehyphenation(self):
        from scripts.postprocess.dehyphenate import dehyphenate
        assert dehyphenate("Wis- senschaft") == "Wissenschaft"

    def test_proper_name_preserved(self):
        from scripts.postprocess.dehyphenate import dehyphenate
        result = dehyphenate("Karl- Marx")
        assert "Karl- Marx" in result or "Karl-" in result

    def test_no_change_without_hyphen(self):
        from scripts.postprocess.dehyphenate import dehyphenate
        text = "Ein normaler Text."
        assert dehyphenate(text) == text

    def test_french_dehyphenation(self):
        from scripts.postprocess.dehyphenate import dehyphenate
        result = dehyphenate("con- cernent")
        assert result == "concernent"

    def test_empty_string(self):
        from scripts.postprocess.dehyphenate import dehyphenate
        assert dehyphenate("") == ""

    def test_acronym_preserved(self):
        from scripts.postprocess.dehyphenate import dehyphenate
        result = dehyphenate("Das UN- Abkommen")
        assert "UN-" in result or "UN " in result

    def test_newline_dehyphenation(self):
        from scripts.postprocess.dehyphenate import dehyphenate
        result = dehyphenate("Wis-\nsenschaft")
        assert result == "Wissenschaft"


class TestDehyphenateAggressive:
    def test_aggressive_join(self):
        from scripts.postprocess.dehyphenate import dehyphenate_aggressive
        result = dehyphenate_aggressive("philo-\nsophie")
        assert result == "philosophie"

    def test_aggressive_french(self):
        from scripts.postprocess.dehyphenate import dehyphenate_aggressive
        result = dehyphenate_aggressive("con-\ncernent")
        assert result == "concernent"


class TestFindPotentialHyphenations:
    def test_finds_hyphenation(self):
        from scripts.postprocess.dehyphenate import find_potential_hyphenations
        result = find_potential_hyphenations("Wis- senschaft")
        assert len(result) >= 1
        assert result[0]["part1"] == "Wis"
        assert result[0]["part2"] == "senschaft"

    def test_has_context(self):
        from scripts.postprocess.dehyphenate import find_potential_hyphenations
        result = find_potential_hyphenations("Die Wis- senschaft ist gut.")
        assert result[0]["context"]

    def test_would_join_flag(self):
        from scripts.postprocess.dehyphenate import find_potential_hyphenations
        result = find_potential_hyphenations("Wis- senschaft")
        assert result[0]["would_join"] is True

    def test_would_not_join_uppercase(self):
        from scripts.postprocess.dehyphenate import find_potential_hyphenations
        result = find_potential_hyphenations("Karl- Marx")
        assert result[0]["would_join"] is False

    def test_no_hyphenations(self):
        from scripts.postprocess.dehyphenate import find_potential_hyphenations
        assert find_potential_hyphenations("Kein Bindestrich hier") == []


class TestCleanMarkdown:
    def test_remove_headings(self):
        from scripts.postprocess.clean_markdown import clean_markdown
        assert clean_markdown("## Titel").strip() == "Titel"

    def test_remove_bold(self):
        from scripts.postprocess.clean_markdown import clean_markdown
        assert "**" not in clean_markdown("**fett**")

    def test_remove_links(self):
        from scripts.postprocess.clean_markdown import clean_markdown
        result = clean_markdown("[Text](http://example.com)")
        assert "Text" in result
        assert "http" not in result

    def test_remove_images(self):
        from scripts.postprocess.clean_markdown import clean_markdown
        result = clean_markdown("![alt](image.png)")
        assert "image.png" not in result

    def test_remove_lists(self):
        from scripts.postprocess.clean_markdown import clean_markdown
        result = clean_markdown("- Item 1\n- Item 2")
        assert "Item 1" in result
        assert "- " not in result

    def test_remove_code_backticks(self):
        from scripts.postprocess.clean_markdown import clean_markdown
        result = clean_markdown("Ein `code` Wort")
        assert "`" not in result
        assert "code" in result

    def test_remove_blockquotes(self):
        from scripts.postprocess.clean_markdown import clean_markdown
        result = clean_markdown("> Zitat hier")
        assert result.strip() == "Zitat hier"

    def test_remove_horizontal_rule(self):
        from scripts.postprocess.clean_markdown import clean_markdown
        result = clean_markdown("Text\n---\nMehr Text")
        assert "---" not in result
        assert "Text" in result

    def test_remove_numbered_list(self):
        from scripts.postprocess.clean_markdown import clean_markdown
        result = clean_markdown("1. Erstens\n2. Zweitens")
        assert "1." not in result
        assert "Erstens" in result

    def test_remove_underscore_bold(self):
        from scripts.postprocess.clean_markdown import clean_markdown
        result = clean_markdown("__fett__")
        assert "__" not in result
        assert "fett" in result

    def test_empty_string(self):
        from scripts.postprocess.clean_markdown import clean_markdown
        assert clean_markdown("") == ""

    def test_preserve_structure_false(self):
        from scripts.postprocess.clean_markdown import clean_markdown
        result = clean_markdown("## Heading", preserve_structure=False)
        assert result.strip() == "Heading"


class TestExtractStructure:
    def test_finds_headings(self):
        from scripts.postprocess.clean_markdown import extract_structure
        result = extract_structure("## Titel\n\n### Untertitel")
        assert len(result["headings"]) == 2
        assert result["headings"][0]["level"] == 2
        assert result["headings"][0]["text"] == "Titel"
        assert result["headings"][1]["level"] == 3

    def test_finds_bold(self):
        from scripts.postprocess.clean_markdown import extract_structure
        result = extract_structure("Ein **fettes** Wort")
        assert len(result["bold"]) == 1
        assert result["bold"][0]["text"] == "fettes"

    def test_finds_italic(self):
        from scripts.postprocess.clean_markdown import extract_structure
        result = extract_structure("Ein *kursives* Wort")
        assert len(result["italic"]) == 1
        assert result["italic"][0]["text"] == "kursives"

    def test_empty_text(self):
        from scripts.postprocess.clean_markdown import extract_structure
        result = extract_structure("")
        assert result["headings"] == []
        assert result["bold"] == []
        assert result["italic"] == []

    def test_no_markdown(self):
        from scripts.postprocess.clean_markdown import extract_structure
        result = extract_structure("Normaler Text ohne Formatierung")
        assert all(v == [] for v in result.values())
