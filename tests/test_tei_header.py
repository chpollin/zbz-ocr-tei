"""Regressions-Tests fuer scripts/tei/tei_step3.build_tei_header (A1).

Haelt den teiHeader-Generator auf dem ausgelieferten Datenvertrag fest. Frueher
war er aermer als tei_final (docID nur als Kommentar, einfaches <bibl> statt
<biblStruct>, kein <langUsage>) -- ein tei_unified-Neulauf regressierte damit
jeden Header. Diese Tests scheitern, falls der Generator wieder verarmt oder
ein E68-Element aus dem Schema faellt.
"""

from __future__ import annotations

import pytest

from scripts.tei.tei_step3 import build_tei_header, _language_idents

REPO_SCHEMA = "data/schema/zbz_hersch.rng"

try:
    from lxml import etree as _etree
    HAS_LXML = True
except ImportError:  # pragma: no cover
    HAS_LXML = False
    _etree = None


_META_FULL = {
    "title": "Transformer l'ecole",
    "author": "Jeanne Hersch",
    "date": "1973",
    "pub_form": "journalArticle",
    "lang": "fra",
}


def _wrap(header: str) -> str:
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<TEI xmlns="http://www.tei-c.org/ns/1.0" type="naegeli">\n'
            + header +
            '\n  <text><body><div type="text"><p>x</p></div></body></text>\n</TEI>')


# --- Inhaltsvertrag --------------------------------------------------------

def test_idno_docid_present_not_comment():
    """docID ist ein echtes <idno>, NICHT der alte Kommentar."""
    h = build_tei_header("1000", _META_FULL)
    assert '<idno type="docID">1000</idno>' in h
    assert "<!-- docID" not in h


def test_biblstruct_replaces_simple_bibl():
    h = build_tei_header("1000", _META_FULL)
    assert '<biblStruct type="journalArticle">' in h
    assert "<analytic>" in h and "<monogr>" in h and "<imprint>" in h
    assert "<date>1973</date>" in h


def test_langusage_present():
    h = build_tei_header("1000", _META_FULL)
    assert "<langUsage>" in h
    assert '<language ident="fra" />' in h


def test_multilang_emits_one_language_each():
    h = build_tei_header("1330", {**_META_FULL, "lang": "fra/deu"})
    assert '<language ident="fra" />' in h
    assert '<language ident="deu" />' in h


def test_empty_date_yields_self_closing_imprint():
    h = build_tei_header("500", {**_META_FULL, "date": ""})
    assert "<imprint />" in h
    assert "<date>" not in h


# --- Sprachcode-Normalisierung --------------------------------------------

@pytest.mark.parametrize("raw,expected", [
    ("fra", ["fra"]),
    ("fra/deu", ["fra", "deu"]),
    ("fr", ["fra"]),
    ("de", ["deu"]),
    ("", ["und"]),
    ("?", ["und"]),
    ("fra/fra", ["fra"]),         # Duplikate raus
    ("eng", ["eng"]),
])
def test_language_idents(raw, expected):
    assert _language_idents(raw) == expected


# --- Schema-Validierung (der eigentliche A1-Waechter) ----------------------

@pytest.mark.skipif(not HAS_LXML, reason="lxml nicht installiert")
@pytest.mark.parametrize("meta", [
    _META_FULL,
    {**_META_FULL, "date": ""},             # ohne Datum -> leeres imprint
    {**_META_FULL, "lang": "fra/deu"},      # mehrsprachig -> zwei language
    {**_META_FULL, "lang": "", "pub_form": "other"},  # und + other
])
def test_generated_header_validates_against_schema(meta):
    relaxng = _etree.RelaxNG(_etree.parse(REPO_SCHEMA))
    doc = _etree.fromstring(_wrap(build_tei_header("9999", meta)).encode("utf-8"))
    assert relaxng.validate(doc), "\n".join(str(e) for e in relaxng.error_log)
