"""
Konformitaets-Tests fuer die Welle-1/2-Generator-Fixes (Audit 2026-06-08).

Synthetisch und datenunabhaengig (kein lokaler Korpus noetig, CI-faehig). Jeder Test
haelt einen einzelnen, am Audit belegten Editionsrichtlinien-Verstoss fest, damit er
nicht wieder hereinrutscht:

- div-n-vs-type-exclusive: ein <div> darf nicht @type UND @n tragen (GT: 0 BOTH-divs).
- figure-xmlid: jede <figure> traegt eine fortlaufende xml:id figN (GT 760: fig3..fig35).
- head-type-lemma: bei Lexikonartikeln ist die erste Ueberschrift <head type="lemma">.
- title-main-sub: der erste STRUKTUR-Head wird in <title type="main"> gewickelt; eine
  vorangestellte Bildunterschrift (<figure><head>) bleibt unangetastet (Code-Review 2026-06-08).
- foreign-lang: <foreign xml:lang> wird via normalize_lang_code auf 639-2/T gehoben; der
  Normalizer-Pass und Validator-W18 sind deckungsgleich (Code-Review 2026-06-08).
"""

from __future__ import annotations

import xml.etree.ElementTree as ET

from scripts.tei.tei_step3 import (
    _assign_figure_ids,
    _fix_div_n_type_exclusive,
    _normalize_foreign_lang,
    _wrap_first_title,
)
from scripts.tei.tei_step1 import _build_tei_body
from scripts.tei.tei_xml_utils import normalize_lang_code

TEI = "{http://www.tei-c.org/ns/1.0}"
XML_ID = "{http://www.w3.org/XML/1998/namespace}id"


def _wrap(body_inner: str) -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<TEI xmlns="http://www.tei-c.org/ns/1.0"><text><body>'
        + body_inner
        + "</body></text></TEI>"
    )


# --- div-n-vs-type-exclusive --------------------------------------------------

def test_div_type_removes_n():
    """Ein <div> mit type UND n verliert das n; der Typ bleibt."""
    out = _fix_div_n_type_exclusive(_wrap('<div type="interview" n="1"><p>x</p></div>'))
    div = ET.fromstring(out).find(f".//{TEI}div")
    assert div.get("type") == "interview"
    assert div.get("n") is None


def test_div_plain_n_kept():
    """Ein reines Struktur-<div n='2'> ohne type bleibt unveraendert."""
    out = _fix_div_n_type_exclusive(_wrap('<div n="2"><p>y</p></div>'))
    div = ET.fromstring(out).find(f".//{TEI}div")
    assert div.get("n") == "2"
    assert div.get("type") is None


def test_div_type_only_unchanged():
    """Ein Spezial-<div type='review'> ohne n bleibt unveraendert."""
    out = _fix_div_n_type_exclusive(_wrap('<div type="review"><p>z</p></div>'))
    div = ET.fromstring(out).find(f".//{TEI}div")
    assert div.get("type") == "review"
    assert div.get("n") is None


# --- figure-xmlid -------------------------------------------------------------

def test_figures_get_sequential_ids():
    """Alle <figure> erhalten fortlaufende xml:id fig1, fig2, ... in Dokumentreihenfolge."""
    body = (
        '<div n="1">'
        '<figure facs="#facs_1_r_1"><head>A</head></figure>'
        '<p>dazwischen</p>'
        '<figure facs="#facs_2_r_1"><head>B</head></figure>'
        '</div>'
    )
    figs = ET.fromstring(_assign_figure_ids(_wrap(body))).findall(f".//{TEI}figure")
    assert [f.get(XML_ID) for f in figs] == ["fig1", "fig2"]


def test_no_figures_noop():
    """Ohne <figure> bleibt das Dokument unveraendert parsebar."""
    out = _assign_figure_ids(_wrap('<div n="1"><p>x</p></div>'))
    assert ET.fromstring(out).find(f".//{TEI}figure") is None


# --- head-type-lemma ----------------------------------------------------------

def _heading(text="Freiheit"):
    return [{"text": text, "zbz_tag": "zb_heading", "label": "section_header",
             "region_id": 1, "bbox": None}]


def test_encyclopedia_first_heading_is_lemma():
    """Bei genre=encyclopedia traegt die erste Ueberschrift type='lemma'."""
    out = _build_tei_body(_heading(), page=1, genre="encyclopedia", is_interview=False, pb_n="1")
    assert 'type="lemma"' in out
    assert "type=\"entry\"" in out  # div-Typ fuer Lexikonartikel


def test_non_encyclopedia_heading_has_no_lemma():
    """Ausserhalb encyclopedia bleibt die Ueberschrift ein blankes <head>."""
    out = _build_tei_body(_heading(), page=1, genre=None, is_interview=False, pb_n="1")
    assert "type=\"lemma\"" not in out
    assert "<head" in out


# --- title-main-sub -----------------------------------------------------------

def test_first_head_wrapped_in_title_main():
    """Die erste <head> im Dokument wird in <title type='main'> gewickelt."""
    body = '<div n="1"><head>Werktitel</head><p>x</p><head>Kapitel</head></div>'
    root = ET.fromstring(_wrap_first_title(_wrap(body), genre=None))
    heads = root.findall(f".//{TEI}head")
    first_title = heads[0].find(f"{TEI}title")
    assert first_title is not None and first_title.get("type") == "main"
    assert (first_title.text or "").strip() == "Werktitel"
    # zweite Ueberschrift bleibt unangetastet (kein title)
    assert heads[1].find(f"{TEI}title") is None


def test_title_skipped_for_encyclopedia():
    """Bei encyclopedia bleibt die erste <head> (= Lemma) ohne title-Wrapping."""
    body = '<div type="entry"><head type="lemma">Freiheit</head><p>x</p></div>'
    root = ET.fromstring(_wrap_first_title(_wrap(body), genre="encyclopedia"))
    assert root.find(f".//{TEI}head/{TEI}title") is None


def test_title_skips_figure_caption():
    """Eine vorangestellte Bildunterschrift (<figure><head>) wird NICHT zum Werktitel.

    body.iter('head') steigt rekursiv in <figure> ab; ohne den Struktur-Eltern-Filter
    wuerde die Caption faelschlich in <title type='main'> gewickelt (Code-Review 2026-06-08).
    Der echte Struktur-Head danach traegt den Titel.
    """
    body = (
        '<div n="1">'
        '<figure facs="#facs_1_r_1"><head>Abbildung 1: Portrait</head></figure>'
        '<head>Echter Werktitel</head>'
        '<p>x</p>'
        '</div>'
    )
    root = ET.fromstring(_wrap_first_title(_wrap(body), genre=None))
    fig_head = root.find(f".//{TEI}figure/{TEI}head")
    assert fig_head.find(f"{TEI}title") is None
    assert (fig_head.text or "").strip() == "Abbildung 1: Portrait"
    # Der erste Struktur-Head (direktes Kind von <div>) traegt den Werktitel.
    div_head = root.find(f".//{TEI}div/{TEI}head")
    title = div_head.find(f"{TEI}title")
    assert title is not None and title.get("type") == "main"
    assert (title.text or "").strip() == "Echter Werktitel"


# --- foreign-lang -------------------------------------------------------------

XMLLANG = "{http://www.w3.org/XML/1998/namespace}lang"


def test_foreign_lang_normalized_to_639_2t():
    """xml:lang auf <foreign> wird auf 639-2/T normalisiert (de->deu, fr->fra, fre->fra)."""
    body = (
        '<div n="1"><p>'
        '<foreign xml:lang="de">a</foreign>'
        '<foreign xml:lang="fr">b</foreign>'
        '<foreign xml:lang="fre">c</foreign>'
        '<foreign xml:lang="deu">d</foreign>'
        '</p></div>'
    )
    langs = [f.get(XMLLANG) for f in ET.fromstring(_normalize_foreign_lang(_wrap(body))).findall(f".//{TEI}foreign")]
    assert langs == ["deu", "fra", "fra", "deu"]


def test_foreign_lang_extended_codes():
    """Latein/Spanisch und ein BCP-47-Region-Subtag werden gehoben (la->lat, es->spa, en-US->eng)."""
    body = (
        '<div n="1"><p>'
        '<foreign xml:lang="la">a</foreign>'
        '<foreign xml:lang="es">b</foreign>'
        '<foreign xml:lang="en-US">c</foreign>'
        '</p></div>'
    )
    langs = [f.get(XMLLANG) for f in ET.fromstring(_normalize_foreign_lang(_wrap(body))).findall(f".//{TEI}foreign")]
    assert langs == ["lat", "spa", "eng"]


def test_foreign_lang_unknown_unchanged():
    """Ein unbekannter Code, den der Pass nicht heben kann, bleibt unveraendert.

    Bedingung fuer Deckungsgleichheit mit W18: was der Pass nicht aendert, meldet W18 nicht
    (kein un-raeumbarer Dauer-Warnhinweis). Ein schon kanonisches 'grc' bleibt ebenfalls.
    """
    body = (
        '<div n="1"><p>'
        '<foreign xml:lang="zxx">a</foreign>'
        '<foreign xml:lang="grc">b</foreign>'
        '</p></div>'
    )
    langs = [f.get(XMLLANG) for f in ET.fromstring(_normalize_foreign_lang(_wrap(body))).findall(f".//{TEI}foreign")]
    assert langs == ["zxx", "grc"]


def test_normalize_lang_code_contract():
    """Vertrag der gemeinsamen Quelle: kanonische Form, sonst Eingang unveraendert.

    normalize_lang_code speist sowohl _normalize_foreign_lang als auch Validator-W18; W18
    flaggt genau dann, wenn normalize_lang_code(x) != x. Diese Tabelle haelt das fest.
    """
    assert normalize_lang_code("fre") == "fra"   # B->T-Variante
    assert normalize_lang_code("ger") == "deu"
    assert normalize_lang_code("de") == "deu"    # 2-Letter bekannt
    assert normalize_lang_code("la") == "lat"
    assert normalize_lang_code("EN-us") == "eng"  # Case + Region-Subtag
    assert normalize_lang_code("[fr]") == "fra"   # eckige Klammern
    assert normalize_lang_code("fra") == "fra"    # schon kanonisch -> kein Flag
    assert normalize_lang_code("grc") == "grc"    # schon 3-Letter -> kein Flag
    assert normalize_lang_code("zxx") == "zxx"    # unbekannt -> kein Flag
