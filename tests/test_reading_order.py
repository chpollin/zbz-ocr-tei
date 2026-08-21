"""Tests fuer scripts.core.tei_xml_utils.reading_order_permutation.

Sichert die EINE Entscheidung ab: in welcher Reihenfolge werden Layout-Regionen gelesen?
Regel (Defekt 30/760, decisions.md): nicht rein nach y, sondern spalten- und bandbewusst.
Vollbreite Bloecke (w >= 60%) segmentieren die Seite in waagrechte Baender; innerhalb eines
Bands liest man Spalte fuer Spalte links nach rechts (x-Mitten-Abstand > 12% = Spaltensteg),
je Spalte oben nach unten. Einspaltig ist gleich der reinen y-Reihenfolge, also keine
Regression gegenueber der frueheren Sortierung.
"""
from scripts.core.tei_xml_utils import reading_order_permutation
from tests.conftest import bbox


def order_ids(items):
    """items: Liste von (id, bbox) in Eingangs-(Liefer-)Reihenfolge; gibt die ids kanonisch."""
    bboxes = [b for _, b in items]
    perm = reading_order_permutation(bboxes)
    return [items[i][0] for i in perm]


def test_empty_and_single():
    assert reading_order_permutation([]) == []
    assert reading_order_permutation([bbox(20, 10)]) == [0]


def test_single_column_already_sorted_is_identity():
    items = [("a", bbox(25, 10, w=40)), ("b", bbox(25, 30, w=40)), ("c", bbox(25, 60, w=40))]
    assert order_ids(items) == ["a", "b", "c"]


def test_single_column_unsorted_becomes_top_to_bottom():
    items = [("c", bbox(25, 60, w=40)), ("a", bbox(25, 10, w=40)), ("b", bbox(25, 30, w=40))]
    assert order_ids(items) == ["a", "b", "c"]


def test_single_column_matches_pure_y_sort():
    # Garantie der Nicht-Regression: in einer Spalte ist die kanonische Ordnung exakt die
    # stabile y-Sortierung, die die alte relevant.sort(key=y_pct) erzeugte.
    items = [("c", bbox(30, 60, w=30)), ("a", bbox(30, 10, w=30)), ("b", bbox(30, 35, w=30))]
    bboxes = [b for _, b in items]
    perm = reading_order_permutation(bboxes)
    expected = sorted(range(len(bboxes)), key=lambda i: bboxes[i]["y_pct"])
    assert perm == expected


def test_two_columns_not_interleaved_by_y():
    # linke Spalte (x-Mitte 30) y=10,40 ; rechte Spalte (x-Mitte 70) y=20,30
    # Eingang in der verschraenkten y-Reihenfolge, die die alte Sortierung erzeugt haette
    items = [
        ("L1", bbox(20, 10)),
        ("R1", bbox(60, 20)),
        ("R2", bbox(60, 30)),
        ("L2", bbox(20, 40)),
    ]
    assert order_ids(items) == ["L1", "L2", "R1", "R2"]


def test_double_page_three_regions_per_side():
    items = [
        ("R1", bbox(60, 5)),
        ("L1", bbox(15, 8)),
        ("L2", bbox(15, 50)),
        ("R2", bbox(60, 55)),
        ("L3", bbox(15, 90)),
        ("R3", bbox(60, 95)),
    ]
    assert order_ids(items) == ["L1", "L2", "L3", "R1", "R2", "R3"]


def test_full_width_header_reads_first():
    items = [
        ("Lbody", bbox(20, 40)),
        ("header", bbox(5, 5, w=90)),
        ("Rbody", bbox(60, 40)),
    ]
    assert order_ids(items) == ["header", "Lbody", "Rbody"]


def test_full_width_footer_reads_last():
    items = [
        ("footer", bbox(5, 92, w=90)),
        ("Lbody", bbox(20, 30)),
        ("Rbody", bbox(60, 30)),
    ]
    assert order_ids(items) == ["Lbody", "Rbody", "footer"]


def test_header_then_two_columns_then_footer():
    items = [
        ("R1", bbox(60, 30)),
        ("footer", bbox(5, 92, w=90)),
        ("L1", bbox(20, 30)),
        ("header", bbox(5, 5, w=90)),
        ("L2", bbox(20, 60)),
        ("R2", bbox(60, 60)),
    ]
    assert order_ids(items) == ["header", "L1", "L2", "R1", "R2", "footer"]
