"""ZBZ-Konformitaets-Gate fuer den ausgelieferten Bestand (Task 2, order 2026-06-21).

Weist nach, dass der ausgelieferte Bestand dem ZBZ-Inline-GND-Modell (E88) entspricht.
Zwei Ebenen:

1. Synthetische Fixtures (git-getrackt, datenunabhaengig, laufen in CI): jede Z-Regel
   feuert auf einem gezielt nicht-konformen Dokument, und ein konformes Inline-GND-Dokument
   ist sauber. Haelt die Regelsemantik fest.
2. Realer Bestand (``output/tei_final``, gitignored -> skippt auf frischem Clone): jedes
   ausgelieferte TEI ist gegen das ZBZ-Inline-GND-Modell konform (keine Verletzung). Das ist
   das committete Pruefergebnis ueber den realen Bestand.

Die strukturelle Konformitaet (Schema = ZBZ-Pruefvorlage + E68, Projektregeln R1-R7) deckt
``tests/test_tei_schema.py`` ab; dieses Gate ergaenzt die Modell-Regeln, die ein RelaxNG
nicht ausdruecken kann.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from lxml import etree as _etree

from scripts.tei.zbz_conformity import check_conformity
from tests.conftest import FINAL_DOCS, FINAL_IDS

REPO = Path(__file__).resolve().parent.parent

_NS = 'xmlns="http://www.tei-c.org/ns/1.0"'


def _root(body_inner: str, prefix: str = "") -> _etree._Element:
    xml = f'<TEI {_NS} type="naegeli">{prefix}<text><body><div type="text">{body_inner}</div></body></text></TEI>'
    return _etree.fromstring(xml.encode("utf-8"))


def _violations(root) -> list[str]:
    return [f["rule"] for f in check_conformity(root) if f["severity"] == "violation"]


# --- 1. Synthetische Fixtures: jede Regel feuert gezielt --------------------

def test_inline_gnd_doc_is_conformant():
    """Ein korrekt inline mit GND ausgezeichnetes Dokument hat keine Verletzung."""
    root = _root(
        '<pb facs="#facs_1" n="1"/>'
        '<p><persName ref="GND:118815679">Hersch</persName> lehrte an der '
        '<orgName ref="GND:1010450-1">Universitaet Genf</orgName> und schrieb '
        '<bibl ref="GND:1088036961">L\'etre et la forme</bibl>.</p>'
    )
    assert _violations(root) == []


@pytest.mark.parametrize("rule,prefix,inner", [
    ("Z1", "", '<pb facs="#f1" n="1"/><p><persName ref="Wikidata:Q1">x</persName></p>'),
    ("Z2", "", '<pb facs="#f1" n="1"/><p><idno type="GeoNames">2657896</idno></p>'),
    ("Z3", "", '<pb facs="#f1" n="1"/><p><placeName>Zuerich</placeName></p>'),
    ("Z4", "<standOff/>", '<pb facs="#f1" n="1"/><p>x</p>'),
    ("Z5", "", '<pb facs="#f1" n="1"/><p><hi rendition="#xyz">x</hi></p>'),
    ("Z6", "", '<pb n="1"/><p>x</p>'),  # pb ohne facs
])
def test_each_rule_fires(rule, prefix, inner):
    """Jede Z-Regel feuert auf ihrem gezielt nicht-konformen Dokument."""
    root = _root(inner, prefix=prefix)
    assert rule in _violations(root), f"{rule} sollte feuern"


def test_bibliography_bibl_without_gnd_is_ok():
    """README §Lexikonartikel: <bibl> in <div type="bibliography"> bewusst ohne GND -- keine Verletzung."""
    xml = (
        f'<TEI {_NS} type="naegeli"><text><body>'
        '<div type="entry"><pb facs="#f1" n="1"/>'
        '<div type="bibliography"><listBibl><bibl>Ein Eintrag ohne GND</bibl></listBibl></div>'
        '</div></body></text></TEI>'
    )
    root = _etree.fromstring(xml.encode("utf-8"))
    assert _violations(root) == []


def test_unlinked_persname_is_advisory_not_violation():
    """persName ohne @ref ist ein Kurationshinweis (advisory), keine Verletzung."""
    root = _root('<pb facs="#f1" n="1"/><p><persName>Hersch</persName></p>')
    findings = check_conformity(root)
    assert _violations(root) == []
    assert any(f["rule"] == "Z8" and f["severity"] == "advisory" for f in findings)


# --- 2. Realer Bestand: committetes Pruefergebnis ---------------------------

@pytest.mark.skipif(not FINAL_DOCS, reason="output/tei_final leer (gitignored, kein lokaler Korpus)")
@pytest.mark.parametrize("doc", FINAL_DOCS, ids=FINAL_IDS)
@pytest.mark.requires_corpus
def test_final_doc_zbz_conformant(doc: Path):
    """Jedes ausgelieferte TEI ist gegen das ZBZ-Inline-GND-Modell konform (keine Verletzung)."""
    root = _etree.parse(str(doc)).getroot()
    violations = [f for f in check_conformity(root) if f["severity"] == "violation"]
    assert not violations, (
        f"{doc.name}: {len(violations)} ZBZ-Konformitaets-Verletzung(en)\n  "
        + "\n  ".join(f"[{v['rule']}] L{v['line']}: {v['message']}" for v in violations[:5])
    )
