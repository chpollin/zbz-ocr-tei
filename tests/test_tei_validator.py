"""Regressions-Tests fuer scripts/tei/tei_validator.py.

Schwerpunkt: O24 -- _compute_cer muss CER in PROZENT liefern (nicht als Ratio
0-1). Der Validator-Report formatiert ueberall ``{cer:.1f}%``; lieferte die
Funktion ein Ratio, waeren alle Referenz-CERs um Faktor 100 zu klein. Frueher
importierte _compute_cer ein nicht existentes ``compute_cer`` und fiel still
auf eine Laengen-Approximation zurueck.
"""

from lxml import etree

from scripts.eval.evaluate_ocr import calculate_cer
from scripts.tei.tei_validator import (
    _check_project_rules,
    _collect_finals,
    _compute_cer,
)

# --- W19: Lesereihenfolge-Anomalie (Spalten-/Band-Ordnung, Defekt 30/760) ---

def _tei(zones, blocks):
    return (
        '<TEI xmlns="http://www.tei-c.org/ns/1.0" type="naegeli">'
        '<teiHeader><fileDesc><titleStmt><title>T</title><author>A</author></titleStmt>'
        '<publicationStmt><publisher>p</publisher></publicationStmt>'
        '<sourceDesc><bibl><publisher>p</publisher></bibl></sourceDesc></fileDesc></teiHeader>'
        '<facsimile><surface xml:id="facs_1" ulx="0" uly="0" lrx="1000" lry="1000">'
        f'{zones}</surface></facsimile>'
        '<text><body><div n="1"><pb facs="#facs_1" n="1"/>'
        f'{blocks}</div></body></text></TEI>'
    )


def _w19(zones, blocks):
    root = etree.fromstring(_tei(zones, blocks).encode("utf-8"))
    _, warnings = _check_project_rules(root)
    return [w for w in warnings if w["rule"] == "W19"]


# zwei Spalten: links (cx ~27.5%) facs_1_r_1/r_3, rechts (cx ~72.5%) facs_1_r_2
_TWO_COL_ZONES = (
    '<zone xml:id="facs_1_r_1" ulx="100" uly="100" lrx="450" lry="200"/>'
    '<zone xml:id="facs_1_r_2" ulx="550" uly="150" lrx="900" lry="250"/>'
    '<zone xml:id="facs_1_r_3" ulx="100" uly="400" lrx="450" lry="500"/>'
)


def test_w19_fires_on_column_interleaved_order():
    # ausgeliefert in der verschraenkten y-Reihenfolge (L1, R1, L2) der alten Sortierung
    blocks = (
        '<p facs="#facs_1_r_1">L1</p>'
        '<p facs="#facs_1_r_2">R1</p>'
        '<p facs="#facs_1_r_3">L2</p>'
    )
    found = _w19(_TWO_COL_ZONES, blocks)
    assert len(found) == 1
    assert "Seite 1" in found[0]["message"]


def test_w19_silent_on_correct_column_order():
    # dieselben Zonen, aber in kanonischer Ordnung ausgeliefert (linke Spalte ganz, dann rechte)
    blocks = (
        '<p facs="#facs_1_r_1">L1</p>'
        '<p facs="#facs_1_r_3">L2</p>'
        '<p facs="#facs_1_r_2">R1</p>'
    )
    assert _w19(_TWO_COL_ZONES, blocks) == []


def test_w19_silent_on_single_column():
    zones = (
        '<zone xml:id="facs_1_r_1" ulx="100" uly="100" lrx="900" lry="200"/>'
        '<zone xml:id="facs_1_r_2" ulx="100" uly="400" lrx="900" lry="500"/>'
        '<zone xml:id="facs_1_r_3" ulx="100" uly="700" lrx="900" lry="800"/>'
    )
    blocks = (
        '<p facs="#facs_1_r_1">A</p>'
        '<p facs="#facs_1_r_2">B</p>'
        '<p facs="#facs_1_r_3">C</p>'
    )
    assert _w19(zones, blocks) == []


def test_w19_silent_without_zone_coords():
    # pb traegt nur #facs_1 (kein _r_), kein region-genauer Beleg -> keine Auswertung
    blocks = '<p>kein facs</p><p>auch nicht</p>'
    assert _w19(_TWO_COL_ZONES, blocks) == []


def test_identical_text_is_zero():
    assert _compute_cer("Hello World", "Hello World") == 0.0


# --- _collect_finals: beide Ablage-Layouts (E68-Luecke, 2026-06-21) ---------

def test_collect_finals_flat_layout(tmp_path):
    """Flache Ablage (ausgelieferte SoT tei_final): direkte *_final.xml werden erfasst."""
    (tmp_path / "100_final.xml").write_text("<TEI/>", encoding="utf-8")
    (tmp_path / "2310_final.xml").write_text("<TEI/>", encoding="utf-8")
    (tmp_path / "notes.txt").write_text("x", encoding="utf-8")
    assert sorted(doc_id for doc_id, _ in _collect_finals(tmp_path)) == ["100", "2310"]


def test_collect_finals_nested_layout(tmp_path):
    """Verschachtelte Ablage (tei_unified): {id}/{id}_final.xml."""
    d = tmp_path / "100"
    d.mkdir()
    (d / "100_final.xml").write_text("<TEI/>", encoding="utf-8")
    assert [doc_id for doc_id, _ in _collect_finals(tmp_path)] == ["100"]


def test_collect_finals_flat_takes_precedence(tmp_path):
    """Liegen flache *_final.xml vor, werden sie genommen, nicht die Unterordner."""
    (tmp_path / "100_final.xml").write_text("<TEI/>", encoding="utf-8")
    sub = tmp_path / "200"
    sub.mkdir()
    (sub / "200_final.xml").write_text("<TEI/>", encoding="utf-8")
    assert [doc_id for doc_id, _ in _collect_finals(tmp_path)] == ["100"]


def test_empty_reference_is_zero():
    assert _compute_cer("", "irgendwas") == 0.0


def test_single_substitution_in_percent():
    # 1 von 11 Zeichen falsch -> ~9.09 %, NICHT 0.0909
    cer = _compute_cer("Hello World", "Hallo World")
    assert 8.0 < cer < 11.0


def test_scale_matches_calculate_cer_times_100():
    """Der eigentliche O24-Waechter: Prozent == Ratio * 100."""
    ref, hyp = "Jeanne Hersch, philosophe", "Jeanne Hersh, philosoph"
    assert _compute_cer(ref, hyp) == round(calculate_cer(ref, hyp) * 100, 2)


def test_totally_different_is_large_percent():
    # Komplett verschieden -> deutlich zweistelliger Prozentwert, nicht < 1
    cer = _compute_cer("abcdefghij", "9876543210")
    assert cer > 50.0
