"""Tests fuer scripts/config.py."""

from pathlib import Path


def test_project_root_exists():
    from scripts.config import PROJECT_ROOT
    assert PROJECT_ROOT.exists()
    assert (PROJECT_ROOT / "scripts").is_dir()


def test_data_dir_exists():
    from scripts.config import DATA_DIR
    assert DATA_DIR.exists()


def test_tei_ns_valid():
    from scripts.config import TEI_NS
    assert TEI_NS == "http://www.tei-c.org/ns/1.0"


def test_valid_div_types_non_empty():
    from scripts.config import VALID_DIV_TYPES
    assert isinstance(VALID_DIV_TYPES, set)
    assert len(VALID_DIV_TYPES) >= 5
    assert "review" in VALID_DIV_TYPES
    assert "interview" in VALID_DIV_TYPES


def test_testplan_structure():
    from scripts.config import TESTPLAN
    assert isinstance(TESTPLAN, dict)
    assert "phase1" in TESTPLAN
    assert "phase2" in TESTPLAN
    for phase_key, phase_data in TESTPLAN.items():
        assert "name" in phase_data
        assert "tests" in phase_data
        for test in phase_data["tests"]:
            assert "pdf" in test
            assert "type" in test


def test_known_entities():
    from scripts.config import KNOWN_ENTITIES
    assert isinstance(KNOWN_ENTITIES, dict)
    assert len(KNOWN_ENTITIES) >= 5
    assert "Karl Jaspers" in KNOWN_ENTITIES
    assert KNOWN_ENTITIES["Karl Jaspers"].startswith("GND:")


def test_get_test_metadata_found():
    from scripts.config import get_test_metadata
    meta = get_test_metadata("2310")
    assert meta is not None
    assert meta["pdf"] == "2310.pdf"
    assert meta["type"] == "A"


def test_get_test_metadata_not_found():
    from scripts.config import get_test_metadata
    assert get_test_metadata("99999") is None


def test_docling_to_zbz_mapping():
    from scripts.config import DOCLING_TO_ZBZ
    assert DOCLING_TO_ZBZ["title"] == "zb_heading"
    assert DOCLING_TO_ZBZ["text"] == "zb_paragraph"
    assert DOCLING_TO_ZBZ["footnote"] == "footnote"
    assert DOCLING_TO_ZBZ["page_header"] == "_filter"


def test_label_colors_complete():
    from scripts.config import LABEL_COLORS, DOCLING_TO_ZBZ
    for key in DOCLING_TO_ZBZ:
        assert key in LABEL_COLORS, f"LABEL_COLORS fehlt: {key}"
