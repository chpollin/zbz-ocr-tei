"""Tests fuer scripts/eval/completeness_check.py -- die Seiten-Zaehlregel.

Nagelt fest, dass zwei deterministisch erkennbare Zaehlartefakte NICHT mehr
als Seiten-Mismatch gemeldet werden:

(a) aufgetrennte Doppelseiten -- ein Scan (facs) traegt zwei logische <pb>;
    Signal: zwei <pb> teilen denselben facs-Verweis.
(b) Bibliotheks-/E-Periodica-Deckblatt -- der erste Scan traegt keine
    Inhaltsseite; Signal: die facs-Nummerierung der <pb> beginnt oberhalb von 1
    (facs_1 fehlt, also (min_facs - 1) fuehrende Deckscans).

Reconciliation: effective = distinct_facs + leading_cover. Diese Groesse gleicht
die physische Scan-Zahl (PDF) ab, waehrend rohe <pb>-Zahl durch Splits/Deckblatt
verzerrt. Ein echter, inhaltlicher Seitenverlust bleibt weiter gemeldet.
"""

from scripts.eval.completeness_check import (
    extract_pb_facs,
    reconcile_page_count,
)


def test_extract_pb_facs_basic():
    content = '<pb facs="#facs_1" n="1"/><p>a</p><pb facs="#facs_2" n="2"/>'
    pb_count, facs, all_have = extract_pb_facs(content)
    assert pb_count == 2
    assert facs == [1, 2]
    assert all_have is True


def test_extract_pb_facs_missing_facs_flags_fallback():
    content = '<pb n="1"/><p>a</p><pb facs="#facs_2" n="2"/>'
    pb_count, facs, all_have = extract_pb_facs(content)
    assert pb_count == 2
    assert facs == [2]
    assert all_have is False


def test_split_double_page_reconciles_to_ok():
    # Class (a): facs_2 reused -> one scan carries two logical pages.
    facs = [1, 2, 2, 3]
    r = reconcile_page_count(
        expected_pages=3, pb_count=4, facs_indices=facs,
        all_have_facs=True, pdf_pages=3,
    )
    assert r["split_pages"] == 1
    assert r["leading_cover"] == 0
    assert r["effective_pages"] == 3
    assert r["count_status"] == "OK"


def test_cover_page_reconciles_to_ok():
    # Class (b): facs numbering starts at 2 -> facs_1 is an untranscribed cover.
    facs = [2, 3]
    r = reconcile_page_count(
        expected_pages=3, pb_count=2, facs_indices=facs,
        all_have_facs=True, pdf_pages=3,
    )
    assert r["split_pages"] == 0
    assert r["leading_cover"] == 1
    assert r["effective_pages"] == 3
    assert r["count_status"] == "OK"


def test_split_and_cover_combined_reconciles():
    # Cover dropped (min=2) plus one split (facs_3 reused).
    facs = [2, 3, 3, 4]
    r = reconcile_page_count(
        expected_pages=4, pb_count=4, facs_indices=facs,
        all_have_facs=True, pdf_pages=4,
    )
    assert r["leading_cover"] == 1
    assert r["split_pages"] == 1
    assert r["effective_pages"] == 4
    assert r["count_status"] == "OK"


def test_genuine_missing_page_still_minor():
    # One interior content scan lacks a <pb>: not a leading cover, not a split.
    facs = [1, 2, 3, 4]
    r = reconcile_page_count(
        expected_pages=5, pb_count=4, facs_indices=facs,
        all_have_facs=True, pdf_pages=5,
    )
    assert r["leading_cover"] == 0
    assert r["split_pages"] == 0
    assert r["effective_pages"] == 4
    assert r["count_status"] == "MINOR"


def test_genuine_large_gap_still_mismatch():
    # Heavy content loss survives reconciliation as a real MISMATCH.
    facs = [1, 2]
    r = reconcile_page_count(
        expected_pages=5, pb_count=2, facs_indices=facs,
        all_have_facs=True, pdf_pages=5,
    )
    assert r["effective_pages"] == 2
    assert r["count_status"] == "MISMATCH"


def test_fallback_without_facs_uses_raw_pb():
    # No facs to reconcile against -> raw pb count drives the comparison.
    r = reconcile_page_count(
        expected_pages=5, pb_count=2, facs_indices=[],
        all_have_facs=False, pdf_pages=5,
    )
    assert r["effective_pages"] == 2
    assert r["count_status"] == "MISMATCH"


def test_facs_label_swap_with_matching_count_stays_ok():
    # Doc-110 pattern: two facs are doubly referenced while two other scans are
    # unreferenced, but pb_count already equals expected. The page count is
    # correct (a facs-integrity concern, not a missing page), so it must not be
    # adjusted below expected and flagged.
    facs = [1, 2, 2, 4]  # facs_2 reused, facs_3 unreferenced; pb_count == 4
    r = reconcile_page_count(
        expected_pages=4, pb_count=4, facs_indices=facs,
        all_have_facs=True, pdf_pages=4,
    )
    assert r["split_pages"] == 1
    assert r["effective_pages"] == 4
    assert r["count_status"] == "OK"


def test_excess_not_explained_by_splits_still_minor():
    # pb exceeds expected by 2 but only one split explains one page.
    facs = [1, 2, 2, 3, 4, 5]  # distinct=5, one split, pb=6
    r = reconcile_page_count(
        expected_pages=4, pb_count=6, facs_indices=facs,
        all_have_facs=True, pdf_pages=4,
    )
    assert r["split_pages"] == 1
    assert r["effective_pages"] == 5
    assert r["count_status"] == "MINOR"


def test_clean_document_is_ok():
    facs = [1, 2, 3, 4, 5]
    r = reconcile_page_count(
        expected_pages=5, pb_count=5, facs_indices=facs,
        all_have_facs=True, pdf_pages=5,
    )
    assert r["split_pages"] == 0
    assert r["leading_cover"] == 0
    assert r["effective_pages"] == 5
    assert r["count_status"] == "OK"
