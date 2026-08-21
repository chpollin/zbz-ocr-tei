"""Unit-Tests fuer die zentralen Seitenpfad-Helfer (Welle 4 / W4.1).

Sichert die bewusst asymmetrische Padding-Konvention an EINER Stelle ab:
.md ungepaddet, Seitenbild/Layout-JSON 3-stellig. Die Aufrufer (loaders,
page_manifest, extract_pages, tei_step2, tei_generator, pdf_to_images_pages)
ersetzen ihre Inline-f-Strings durch diese Helfer; die Migration ist genau dann
verhaltenserhaltend, wenn diese Erwartungswerte stimmen.
"""

from scripts.utils import page_image_name, page_layout_name, page_md_name


def test_page_md_name_unpadded():
    assert page_md_name("2310", 7) == "2310_p7.md"
    assert page_md_name("90", 1) == "90_p1.md"
    assert page_md_name("100", 100) == "100_p100.md"


def test_page_image_name_padded_3():
    assert page_image_name("2310", 7) == "2310_p007.png"
    assert page_image_name("90", 1) == "90_p001.png"
    assert page_image_name("100", 100) == "100_p100.png"      # >=3-stellig bleibt
    assert page_image_name("100", 1000) == "100_p1000.png"


def test_page_layout_name_variants():
    assert page_layout_name("2310", 7) == "2310_p007_layout.json"
    assert page_layout_name("2310", 7, "_gemini") == "2310_p007_layout_gemini.json"
    assert page_layout_name("2310", 7, "_curated") == "2310_p007_layout_curated.json"
