"""Regressions-Tests fuer scripts/tei/tei_validator.py.

Schwerpunkt: O24 -- _compute_cer muss CER in PROZENT liefern (nicht als Ratio
0-1). Der Validator-Report formatiert ueberall ``{cer:.1f}%``; lieferte die
Funktion ein Ratio, waeren alle Referenz-CERs um Faktor 100 zu klein. Frueher
importierte _compute_cer ein nicht existentes ``compute_cer`` und fiel still
auf eine Laengen-Approximation zurueck.
"""

from scripts.tei.tei_validator import _compute_cer
from scripts.eval.evaluate_ocr import calculate_cer


def test_identical_text_is_zero():
    assert _compute_cer("Hello World", "Hello World") == 0.0


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
