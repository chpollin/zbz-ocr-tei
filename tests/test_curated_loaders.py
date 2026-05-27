"""Praezedenz-Tests fuer kuratierte Loader-Pfade (Direkt-Schreiben-Loop).

Sichert den Vertrag des Viewer-Direktschreibens ab: Vom Menschen kuratierte
Layout-/OCR-Dateien (vom Viewer per File System Access API geschrieben) muessen in
der Pipeline Vorrang vor allen Engine-Outputs haben, damit `--reassemble` die Edits
tatsaechlich verwendet. Die Loader lesen ihre Verzeichnisse aus Modul-Konstanten;
die Tests isolieren ueber tmp_path + monkeypatch.
"""

from __future__ import annotations

import json

import pytest

from scripts.core import loaders


def _write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


# --------------------------------------------------------------------- #
# load_ocr_text / discover_*  (OCR-Praezedenz)
# --------------------------------------------------------------------- #

@pytest.fixture
def ocr_dirs(tmp_path, monkeypatch):
    """Legt eine kuratierte und eine Mistral-OCR-Quelle an, kuratiert zuerst."""
    curated = tmp_path / "ocr_curated"
    mistral = tmp_path / "mistral_results"
    curated.mkdir()
    mistral.mkdir()
    monkeypatch.setattr(loaders, "_OCR_DIRS", [curated, mistral])
    return curated, mistral


def test_ocr_curated_wins_over_engine(ocr_dirs):
    curated, mistral = ocr_dirs
    _write(curated / "100_p3.md", "KURATIERT")
    _write(mistral / "100_p3.md", "MISTRAL")
    assert loaders.load_ocr_text("100", 3) == "KURATIERT"


def test_ocr_falls_back_when_no_curated(ocr_dirs):
    curated, mistral = ocr_dirs
    _write(mistral / "100_p3.md", "MISTRAL")
    assert loaders.load_ocr_text("100", 3) == "MISTRAL"


def test_ocr_missing_everywhere_returns_none(ocr_dirs):
    assert loaders.load_ocr_text("100", 3) is None


def test_discover_pages_unions_curated_and_engine(ocr_dirs):
    curated, mistral = ocr_dirs
    _write(curated / "100_p5.md", "x")   # nur kuratiert
    _write(mistral / "100_p1.md", "y")   # nur Engine
    _write(mistral / "100_p5.md", "z")   # in beiden
    assert loaders.discover_pages("100") == [1, 5]


def test_discover_documents_includes_curated_only_doc(ocr_dirs):
    curated, mistral = ocr_dirs
    _write(curated / "200_p1.md", "x")   # Doc existiert nur kuratiert
    _write(mistral / "100_p1.md", "y")
    assert loaders.discover_documents() == ["100", "200"]


# --------------------------------------------------------------------- #
# load_ocr_text_with_source  (gelabelte Kette -> PAGE-XML-Provenienz, E72/Welle4)
# Deckt zugleich den page_xml_generator-Pfad ab: dieser delegiert hierher,
# also wird so verifiziert, dass kuratiertes OCR auch ins PAGE-XML fliesst.
# --------------------------------------------------------------------- #

@pytest.fixture
def ocr_sources(tmp_path, monkeypatch):
    """Gelabelte OCR-Quellen, kuratiert zuerst, fuer load_ocr_text_with_source."""
    curated = tmp_path / "ocr_curated"
    mistral = tmp_path / "mistral_results"
    curated.mkdir()
    mistral.mkdir()
    monkeypatch.setattr(loaders, "OCR_SOURCES",
                        [(curated, "curated"), (mistral, "mistral")])
    return curated, mistral


def test_with_source_curated_wins_and_labels(ocr_sources):
    curated, mistral = ocr_sources
    _write(curated / "100_p3.md", "KURATIERT")
    _write(mistral / "100_p3.md", "MISTRAL")
    text, src = loaders.load_ocr_text_with_source("100", 3)
    assert text == "KURATIERT"
    assert src == "curated"


def test_with_source_falls_back_and_labels(ocr_sources):
    curated, mistral = ocr_sources
    _write(mistral / "100_p3.md", "MISTRAL")
    text, src = loaders.load_ocr_text_with_source("100", 3)
    assert text == "MISTRAL"
    assert src == "mistral"


def test_with_source_missing_returns_none_none(ocr_sources):
    assert loaders.load_ocr_text_with_source("100", 3) == (None, None)


# --------------------------------------------------------------------- #
# load_layout_gemini  (Layout-Praezedenz)
# --------------------------------------------------------------------- #

@pytest.fixture
def layout_dir(tmp_path, monkeypatch):
    base = tmp_path / "layout"
    base.mkdir()
    monkeypatch.setattr(loaders, "LAYOUT_DIR", base)
    return base


def _layout_json(tag, **extra):
    payload = {"regions": [{"label": "p", "zbz_tag": tag,
                            "bbox": {"x_pct": 1, "y_pct": 2, "w_pct": 3, "h_pct": 4}}]}
    payload.update(extra)
    return json.dumps(payload)


def test_layout_curated_wins_over_gemini_and_docling(layout_dir):
    doc = layout_dir / "100"
    _write(doc / "100_p001_layout_curated.json", _layout_json("zb_curated"))
    _write(doc / "100_p001_layout_gemini.json", _layout_json("zb_gemini"))
    _write(doc / "100_p001_layout.json", _layout_json("zb_docling"))
    out = loaders.load_layout_gemini("100", 1)
    assert out["regions"][0]["zbz_tag"] == "zb_curated"


def test_layout_falls_back_to_gemini_then_docling(layout_dir):
    doc = layout_dir / "100"
    _write(doc / "100_p002_layout_gemini.json", _layout_json("zb_gemini"))
    assert loaders.load_layout_gemini("100", 2)["regions"][0]["zbz_tag"] == "zb_gemini"

    doc2 = layout_dir / "200"
    _write(doc2 / "200_p001_layout.json", _layout_json("zb_docling"))
    assert loaders.load_layout_gemini("200", 1)["regions"][0]["zbz_tag"] == "zb_docling"


def test_layout_curated_gets_image_dims_from_docling(layout_dir):
    """Kuratierte JSON ohne Bildgroesse wird aus Docling ergaenzt (Augmentierung bleibt)."""
    doc = layout_dir / "100"
    _write(doc / "100_p001_layout_curated.json", _layout_json("zb_curated"))  # ohne image_width
    _write(doc / "100_p001_layout.json", _layout_json("zb_docling", image_width=1275, image_height=1796))
    out = loaders.load_layout_gemini("100", 1)
    assert out["regions"][0]["zbz_tag"] == "zb_curated"
    assert out["image_width"] == 1275
    assert out["image_height"] == 1796


def test_layout_missing_returns_none(layout_dir):
    assert loaders.load_layout_gemini("999", 1) is None
