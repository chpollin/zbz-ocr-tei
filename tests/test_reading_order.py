"""Tests fuer scripts.core.tei_xml_utils.reading_order_permutation.

Sichert die EINE Entscheidung ab: in welcher Reihenfolge werden Layout-Regionen gelesen?
Regel (Defekt 30/760, decisions.md): nicht rein nach y, sondern spalten- und bandbewusst.
Vollbreite Bloecke (w >= 60%) segmentieren die Seite in waagrechte Baender; innerhalb eines
Bands liest man Spalte fuer Spalte links nach rechts (x-Mitten-Abstand > 12% = Spaltensteg),
je Spalte oben nach unten. Einspaltig ist gleich der reinen y-Reihenfolge, also keine
Regression gegenueber der frueheren Sortierung.
"""
from scripts.core.tei_xml_utils import reading_order_permutation


def bb(x, y, w=20.0, h=8.0):
    return {"x_pct": x, "y_pct": y, "w_pct": w, "h_pct": h}


def order_ids(items):
    """items: Liste von (id, bbox) in Eingangs-(Liefer-)Reihenfolge; gibt die ids kanonisch."""
    bboxes = [b for _, b in items]
    perm = reading_order_permutation(bboxes)
    return [items[i][0] for i in perm]


def test_empty_and_single():
    assert reading_order_permutation([]) == []
    assert reading_order_permutation([bb(20, 10)]) == [0]


def test_single_column_already_sorted_is_identity():
    items = [("a", bb(25, 10, w=40)), ("b", bb(25, 30, w=40)), ("c", bb(25, 60, w=40))]
    assert order_ids(items) == ["a", "b", "c"]


def test_single_column_unsorted_becomes_top_to_bottom():
    items = [("c", bb(25, 60, w=40)), ("a", bb(25, 10, w=40)), ("b", bb(25, 30, w=40))]
    assert order_ids(items) == ["a", "b", "c"]


def test_single_column_matches_pure_y_sort():
    # Garantie der Nicht-Regression: in einer Spalte ist die kanonische Ordnung exakt die
    # stabile y-Sortierung, die die alte relevant.sort(key=y_pct) erzeugte.
    items = [("c", bb(30, 60, w=30)), ("a", bb(30, 10, w=30)), ("b", bb(30, 35, w=30))]
    bboxes = [b for _, b in items]
    perm = reading_order_permutation(bboxes)
    expected = sorted(range(len(bboxes)), key=lambda i: bboxes[i]["y_pct"])
    assert perm == expected


def test_two_columns_not_interleaved_by_y():
    # linke Spalte (x-Mitte 30) y=10,40 ; rechte Spalte (x-Mitte 70) y=20,30
    # Eingang in der verschraenkten y-Reihenfolge, die die alte Sortierung erzeugt haette
    items = [
        ("L1", bb(20, 10)),
        ("R1", bb(60, 20)),
        ("R2", bb(60, 30)),
        ("L2", bb(20, 40)),
    ]
    assert order_ids(items) == ["L1", "L2", "R1", "R2"]


def test_double_page_three_regions_per_side():
    items = [
        ("R1", bb(60, 5)),
        ("L1", bb(15, 8)),
        ("L2", bb(15, 50)),
        ("R2", bb(60, 55)),
        ("L3", bb(15, 90)),
        ("R3", bb(60, 95)),
    ]
    assert order_ids(items) == ["L1", "L2", "L3", "R1", "R2", "R3"]


def test_full_width_header_reads_first():
    items = [
        ("Lbody", bb(20, 40)),
        ("header", bb(5, 5, w=90)),
        ("Rbody", bb(60, 40)),
    ]
    assert order_ids(items) == ["header", "Lbody", "Rbody"]


def test_full_width_footer_reads_last():
    items = [
        ("footer", bb(5, 92, w=90)),
        ("Lbody", bb(20, 30)),
        ("Rbody", bb(60, 30)),
    ]
    assert order_ids(items) == ["Lbody", "Rbody", "footer"]


def test_header_then_two_columns_then_footer():
    items = [
        ("R1", bb(60, 30)),
        ("footer", bb(5, 92, w=90)),
        ("L1", bb(20, 30)),
        ("header", bb(5, 5, w=90)),
        ("L2", bb(20, 60)),
        ("R2", bb(60, 60)),
    ]
    assert order_ids(items) == ["header", "L1", "L2", "R1", "R2", "footer"]
