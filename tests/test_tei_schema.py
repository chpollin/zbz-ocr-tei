"""
Schema-Gate fuer die ausgelieferte Edition.

Schliesst die Luecke, die im Mai 2026 (E68) sichtbar wurde: ``tei_final`` ist die
Single Source of Truth (E43), wurde aber nie als Ganzes gegen das eigene Schema
validiert. ``tei_unified`` validiert beim Erzeugen (verschachtelte Ablage), ``tei_final``
ist flach abgelegt und faellt durch ``validate_all`` durch -- die nachtraeglichen
Schritte ``tei_blank_marker``/``tei_status_marker`` schreiben dort ohne Re-Validierung.

Drei Ebenen:

1. ``test_schema_compiles`` -- das projektspezifische RelaxNG
   (``data/schema/zbz_hersch.rng``, git-getrackt) laedt fehlerfrei. Laeuft auf jedem
   Clone und faengt einen kaputten Schema-Patch sofort.
2. ``test_schema_accepts_pipeline_header`` -- ein synthetischer Minimal-Header mit genau
   den Elementen, die das ODD-Subset (2026-01-28) faelschlich weggelassen hatte
   (``revisionDesc``/``change``, ``langUsage``, ``idno``, ``biblStruct/monogr``) ist gegen
   das Schema valide. Git-getrackt, datenunabhaengig -- haelt die E68-Erweiterung fest,
   damit sie nicht versehentlich wieder herausfaellt.
3. ``test_final_doc_valid`` -- jedes ausgelieferte TEI ist gegen Schema + Projektregeln
   valide. ``output/`` ist gitignored, daher skippt diese Ebene auf einem frischen
   Clone / in CI, hat aber lokal volle Zaehne (alle ``*_final.xml``).
"""

from __future__ import annotations

from pathlib import Path

import pytest
from lxml import etree as _etree

from tests.conftest import FINAL_DOCS, FINAL_IDS, delivery_doc

REPO = Path(__file__).resolve().parent.parent
SCHEMA = REPO / "data" / "schema" / "zbz_hersch.rng"

# Synthetischer Header mit genau den E68-Elementen (kein echtes Dokument noetig).
_PIPELINE_HEADER = delivery_doc('<div type="text"><p>Text.</p></div>')

# Synthetischer Korpus mit Inline-GND-Auszeichnung (ZBZ-Editionsrichtlinie, order
# 2026-06-21): Person/Organisation/Werk werden an der Erwaehnungsstelle ausgezeichnet,
# jede mit ref="GND:..." auf die GND, kein separates Register. persName/orgName/bibl
# entsprechen den Beispielen aus der ZBZ-README. Git-getrackt, datenunabhaengig --
# haelt das Inline-GND-Modell fest, damit es nicht versehentlich aufweicht.
_INLINE_GND_DOC = delivery_doc(
    '<div type="article"><pb facs="#facs_1" n="1"/>'
    '<p><persName ref="GND:118815679">Hersch</persName> lehrte an der '
    '<orgName ref="GND:1010450-1">Universitaet Genf</orgName> und schrieb '
    '<bibl ref="GND:1088036961">L\'etre et la forme</bibl>.</p></div>',
    text_attrs='type="naegeli"',
)

# Negativ-Fixture: das verworfene standOff-Register (E87, durch das ZBZ-Material
# ueberholt) plus eine In-Text-Mention <name ref="#id">. Muss vom Schema abgelehnt
# werden -- der Guard kippt, falls jemand das standOff-Modell wieder einzieht.
_STANDOFF_DOC = """<?xml version="1.0" encoding="UTF-8"?>
<TEI xmlns="http://www.tei-c.org/ns/1.0" type="naegeli">
  <teiHeader>
    <fileDesc>
      <titleStmt><title type="main">Test</title><author>Hersch, Jeanne</author></titleStmt>
      <publicationStmt><publisher>ZBZ / DHCraft</publisher><idno type="docID">9999</idno></publicationStmt>
      <sourceDesc>
        <biblStruct type="journalArticle">
          <analytic><title>Test</title><author>Hersch, Jeanne</author></analytic>
          <monogr><title>Zeitschrift</title><imprint><date>1975</date></imprint></monogr>
        </biblStruct>
      </sourceDesc>
    </fileDesc>
    <profileDesc><langUsage><language ident="fra"/></langUsage></profileDesc>
    <revisionDesc><change when="2026-06-21" who="pipeline">init</change></revisionDesc>
  </teiHeader>
  <standOff>
    <listPerson>
      <person xml:id="pers_jeanne_hersch"><persName>Jeanne Hersch</persName></person>
    </listPerson>
  </standOff>
  <text type="naegeli">
    <body>
      <div type="article">
        <pb facs="#facs_1" n="1"/>
        <p><name ref="#pers_jeanne_hersch">Jeanne Hersch</name> schrieb.</p>
      </div>
    </body>
  </text>
</TEI>
"""


def test_schema_compiles():
    """Das projektspezifische RelaxNG laedt fehlerfrei (git-getrackt, laeuft immer)."""
    assert SCHEMA.exists(), f"Schema fehlt: {SCHEMA}"
    _etree.RelaxNG(_etree.parse(str(SCHEMA)))  # wirft RelaxNGParseError bei kaputtem Schema


def test_schema_accepts_pipeline_header():
    """Schema akzeptiert die E68-Header-Elemente (revisionDesc/langUsage/idno/monogr)."""
    relaxng = _etree.RelaxNG(_etree.parse(str(SCHEMA)))
    doc = _etree.fromstring(_PIPELINE_HEADER.encode("utf-8"))
    # The schema requires only biblStruct; the E68 pin rests on these elements being present.
    for name in ("revisionDesc", "langUsage", "idno", "monogr"):
        assert doc.find(f".//{{http://www.tei-c.org/ns/1.0}}{name}") is not None, name
    assert relaxng.validate(doc), (
        "Synthetischer Pipeline-Header nicht schema-valide -- E68-Erweiterung verloren?\n  "
        + "\n  ".join(str(e) for e in relaxng.error_log)
    )


def test_schema_accepts_inline_gnd():
    """Schema akzeptiert Inline-GND-Auszeichnung (persName/orgName/bibl mit ref=GND:...)."""
    relaxng = _etree.RelaxNG(_etree.parse(str(SCHEMA)))
    doc = _etree.fromstring(_INLINE_GND_DOC.encode("utf-8"))
    assert relaxng.validate(doc), (
        "Inline-GND-Dokument nicht schema-valide -- ZBZ-Auszeichnungsmodell verloren?\n  "
        + "\n  ".join(str(e) for e in relaxng.error_log)
    )


def test_schema_rejects_standoff_register():
    """Schema lehnt das verworfene standOff-Register und <name>-Mentions ab (Inline-GND-Guard)."""
    relaxng = _etree.RelaxNG(_etree.parse(str(SCHEMA)))
    doc = _etree.fromstring(_STANDOFF_DOC.encode("utf-8"))
    assert not relaxng.validate(doc), (
        "standOff-Register weiterhin schema-valide -- das ZBZ-Material (order 2026-06-21) "
        "verlangt Inline-GND, kein Register. Wurde E87 versehentlich wieder eingezogen?"
    )


@pytest.mark.skipif(not FINAL_DOCS, reason="output/tei_final leer (gitignored, kein lokaler Korpus)")
@pytest.mark.parametrize("doc", FINAL_DOCS, ids=FINAL_IDS)
@pytest.mark.requires_corpus
def test_final_doc_valid(doc: Path):
    """Jedes ausgelieferte TEI ist gegen Schema + Projektregeln valide."""
    from scripts.tei.tei_validator import validate_tei_file

    result = validate_tei_file(doc)
    assert result["valid"], (
        f"{doc.name}: {result['schema_errors']} Schema-, "
        f"{result['project_errors']} Projekt-Fehler\n  "
        + "\n  ".join(
            f"[{e.get('rule', 'schema')}] {e['message'][:100]}"
            for e in result["errors"][:5]
        )
    )
