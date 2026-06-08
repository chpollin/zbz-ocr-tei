"""Tests fuer den Diskriminator von scripts/tei/tei_footnote_demote.py.

Sichert die EINE kritische Entscheidung ab: WANN gilt eine <note place="foot"> als
verifizierter Fliesstext (-> demote nach <p>)? Regel: ein zusammenhaengender
>= MIN_MATCH Zeichen langer Ausschnitt des Notentextes steht im Body der Referenz.
"""
from scripts.tei.tei_footnote_demote import _verified, _norm, MIN_MATCH, HOLD

# realistische >150-Zeichen-Passage (frei nach Jaspers/Hersch-Stil, keine echten Daten)
PASSAGE = (
    "La communication au sens de la vie avec autrui telle quelle se realise de diverses "
    "manieres dans la vie empirique comprend toujours une part de verite et une part de "
    "malentendu que la raison cherche patiemment a dissiper sans jamais y parvenir."
)
REF_BODY = _norm("Debut du corps de reference. " + PASSAGE + " Et la suite continue ensuite ici.")


def test_passage_im_ref_body_wird_verifiziert():
    # ganze Passage steht im Body -> beweisbar Fliesstext
    assert _verified(PASSAGE, REF_BODY) is True


def test_kurze_note_wird_nie_demoted():
    # unter MIN_MATCH (z.B. Quellenangabe "(Philosophie, I, p. 27)") -> niemals demote
    assert _verified("(Philosophie, I, p. 27-28)", REF_BODY) is False
    assert _verified(PASSAGE[:MIN_MATCH - 1], REF_BODY) is False


def test_langer_text_NICHT_im_ref_body_bleibt_fussnote():
    # 250 Zeichen, aber nicht in der Referenz -> echte Fussnote oder Scope, nicht anfassen
    assert _verified("Zzz " * 80, REF_BODY) is False


def test_ocr_rauschen_am_anfang_wird_per_schiebefenster_gefunden():
    # Erste-120-Check wuerde scheitern; Schiebefenster findet den >=150-Treffer (Fall Doc 290 fn4-1)
    noisy = "BRUITE OCR EN TETE 12 ** " + PASSAGE
    assert _verified(noisy, REF_BODY) is True


def test_nur_kurzer_teiltreffer_reicht_nicht():
    # nur ~130 Zeichen stimmen ueberein, dann Divergenz -> < MIN_MATCH -> bleibt Fussnote (Fall Doc 1910 470)
    partial = PASSAGE[:130] + " " + ("Z" * 200)
    assert _verified(partial, REF_BODY) is False


def test_leerer_oder_fehlender_ref_body():
    assert _verified(PASSAGE, "") is False
    assert _verified("", REF_BODY) is False


def test_hold_set_und_min_match_konstanten():
    # editorisch zurueckgehaltene Docs + Schwelle sind explizit fixiert
    assert HOLD == {"40", "1520"}
    assert MIN_MATCH == 150
