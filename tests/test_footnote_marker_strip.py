"""Tests fuer scripts/tei/tei_footnote_marker_strip.strip_sup_markers.

Sichert die EINE Entscheidung ab: WANN wird ein fuehrender <hi rendition="#sup">M</hi> aus einer
<note place="foot"> entfernt? Regel (Welle-2-Rest, Fix note-footnote-n, Audit 2026-06-08):
nur als ERSTES signifikantes Kind (hoechstens hinter einem fuehrenden <lb/>), Marke <= 3 Zeichen,
nur place="foot". @n defensiv nur setzen, falls fehlend. Mitten-im-Text-Hochstellungen bleiben.
"""
from scripts.tei.tei_footnote_marker_strip import strip_sup_markers


def test_strips_leading_sup_and_keeps_n():
    src = ('<note place="foot" n="1" xml:id="fn6-1"><lb n="N001"/>'
           '<hi rendition="#sup">1</hi> K. Jaspers, Philosophie, p. 202.</note>')
    out, n = strip_sup_markers(src)
    assert n == 1
    assert '<hi rendition="#sup">' not in out
    assert 'n="1"' in out                       # vorhandenes @n bleibt
    assert "K. Jaspers, Philosophie, p. 202." in out
    assert '<lb n="N001"/>' in out              # fuehrendes lb bleibt erhalten


def test_sets_n_from_marker_when_missing():
    src = '<note place="foot" xml:id="fn3-1"><hi rendition="#sup">2</hi> Voir note precedente.</note>'
    out, n = strip_sup_markers(src)
    assert n == 1
    assert 'n="2"' in out                       # @n aus der Marke gesetzt (war leer)
    assert '<hi rendition="#sup">' not in out
    assert "Voir note precedente." in out


def test_footnote_without_sup_unchanged():
    # GT-Form: Body oeffnet mit <hi rendition="#i"> (Kursiv), kein #sup-Marker -> unangetastet
    src = ('<note place="foot" n="1" xml:id="fn22-1">Voir '
           '<hi rendition="#i">Revue syndicale suisse</hi>, novembre 1944.</note>')
    out, n = strip_sup_markers(src)
    assert n == 0
    assert out == src


def test_midtext_superscript_untouched():
    # Hochstellung MITTEN im Text (kein fuehrender Marker) bleibt -- echtes inhaltliches sup
    src = '<note place="foot" n="1" xml:id="fn1-1">Voir p. 3<hi rendition="#sup">9</hi> ff.</note>'
    out, n = strip_sup_markers(src)
    assert n == 0
    assert out == src


def test_non_foot_note_untouched():
    # nur place="foot"; eine Endnote mit fuehrendem #sup bleibt unberuehrt
    src = '<note place="end" n="1" xml:id="en1-1"><hi rendition="#sup">1</hi> Endnote.</note>'
    out, n = strip_sup_markers(src)
    assert n == 0
    assert out == src


def test_long_sup_is_not_a_marker():
    # >3 Zeichen ist keine Druckmarke (z.B. ganzer hochgestellter Text) -> nicht entfernen
    src = '<note place="foot" n="1" xml:id="fn1-1"><hi rendition="#sup">abcd</hi> Text.</note>'
    out, n = strip_sup_markers(src)
    assert n == 0
    assert out == src


def test_idempotent():
    src = ('<note place="foot" n="1" xml:id="fn6-1"><lb n="N001"/>'
           '<hi rendition="#sup">1</hi> K. Jaspers, Philosophie, p. 202.</note>')
    once, n1 = strip_sup_markers(src)
    twice, n2 = strip_sup_markers(once)
    assert n1 == 1 and n2 == 0
    assert twice == once
