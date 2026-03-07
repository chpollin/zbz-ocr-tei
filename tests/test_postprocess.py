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
