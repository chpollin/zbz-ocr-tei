"""Gate fuer die Seitenbild-Anbindung (Task 3, order 2026-06-21).

ZBZ-Editionsrichtlinie: <pb facs="#facs_N" n=...> verweist auf die Surface, die das
Seitenbild traegt. Jede <surface> bekommt ein <graphic url> als erstes Kind (Schema:
graphic vor zone), Adressschema {doc_id}_p{NNN}.png. Zwei Ebenen:

1. Synthetik (git-getrackt, CI): build_facsimile erzeugt graphic-first-child fuer
   zonenbehaftete und leere Surfaces; page_image_url folgt dem Schema; der Projektor
   tei_surface_graphic ist idempotent und korrigiert den alten {N}.png-Platzhalter.
2. Realer Bestand (gitignored -> skippt im CI): jede Surface jedes ausgelieferten TEI
   traegt ein <graphic> als erstes Kind, dessen url dem Schema entspricht.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from lxml import etree as _etree

from scripts.tei.tei_step3 import build_facsimile, page_image_url
from scripts.tei.tei_surface_graphic import project_graphics
from tests.conftest import FINAL_DOCS, FINAL_IDS

REPO = Path(__file__).resolve().parent.parent
SCHEMA = REPO / "data" / "schema" / "zbz_hersch.rng"
TEI_NS = "http://www.tei-c.org/ns/1.0"


def test_page_image_url_scheme():
    assert page_image_url("110", 2) == "110_p002.png"
    assert page_image_url("100", 1) == "100_p001.png"
    assert page_image_url("3200", 14) == "3200_p014.png"


def test_build_facsimile_graphic_first_child_zoned_and_empty():
    """Jede Surface (zonenbehaftet wie leer) traegt graphic als erstes Kind, korrekte URL."""
    page_facsimiles = {
        1: {"image_width": 1240, "image_height": 1754,
            "zones": [{"zone_id": "facs_1_r_1", "ulx": 1, "uly": 2, "lrx": 3, "lry": 4}]},
        2: {"image_width": 1240, "image_height": 1754, "zones": []},  # leere Surface
    }
    out = build_facsimile(page_facsimiles, page_teis={1: "x", 2: "y"}, doc_id="777")
    assert '<surface xml:id="facs_1"' in out
    # graphic steht VOR der ersten zone
    s1 = out.index('xml:id="facs_1"')
    g1 = out.index('<graphic url="777_p001.png"/>')
    z1 = out.index('<zone xml:id="facs_1_r_1"')
    assert s1 < g1 < z1
    # leere Surface bekommt ebenfalls den korrekten Pfad (nicht den alten {N}.png-Platzhalter)
    assert '<graphic url="777_p002.png"/>' in out
    assert '<graphic url="2.png"/>' not in out


def test_build_facsimile_output_is_schema_valid():
    """graphic-vor-zone muss schema-valide sein (Surface-Modell)."""
    page_facsimiles = {
        1: {"image_width": 1240, "image_height": 1754,
            "zones": [{"zone_id": "facs_1_r_1", "ulx": 1, "uly": 2, "lrx": 3, "lry": 4}]},
    }
    facs = build_facsimile(page_facsimiles, page_teis={1: "x"}, doc_id="777")
    xml = (f'<TEI xmlns="{TEI_NS}" type="naegeli"><teiHeader><fileDesc>'
           '<titleStmt><title>t</title></titleStmt>'
           '<publicationStmt><publisher>p</publisher></publicationStmt>'
           '<sourceDesc><p>s</p></sourceDesc></fileDesc></teiHeader>'
           f'{facs}<text><body><div type="text"><pb facs="#facs_1" n="1"/><p>x</p></div></body></text></TEI>')
    rng = _etree.RelaxNG(_etree.parse(str(SCHEMA)))
    doc = _etree.fromstring(xml.encode("utf-8"))
    assert rng.validate(doc), "\n".join(str(e) for e in rng.error_log)


def test_project_graphics_inserts_and_is_idempotent():
    """Projektor setzt graphic in zonenbehaftete Surface, korrigiert {N}.png, ist idempotent."""
    xml = (
        '<facsimile>'
        '<surface xml:id="facs_1" ulx="0" uly="0" lrx="9" lry="9">'
        '<zone xml:id="facs_1_r_1" ulx="1" uly="1" lrx="2" lry="2"/>'
        '</surface>'
        '<surface xml:id="facs_2" ulx="0" uly="0" lrx="9" lry="9">'
        '<graphic url="2.png"/>'  # alter, fehlerhafter Platzhalter
        '</surface>'
        '</facsimile>'
    )
    out, total, changed = project_graphics(xml, "110")
    assert total == 2 and changed == 2
    assert '<graphic url="110_p001.png"/>' in out  # zonenbehaftet: eingefuegt
    assert '<graphic url="110_p002.png"/>' in out  # Platzhalter korrigiert
    assert '<graphic url="2.png"/>' not in out
    # Idempotenz: zweiter Lauf aendert nichts
    out2, _, changed2 = project_graphics(out, "110")
    assert changed2 == 0 and out2 == out


@pytest.mark.skipif(not FINAL_DOCS, reason="output/tei_final leer (gitignored)")
@pytest.mark.parametrize("doc", FINAL_DOCS, ids=FINAL_IDS)
@pytest.mark.requires_corpus
def test_final_doc_every_surface_has_graphic(doc: Path):
    """Jede Surface des ausgelieferten TEI traegt ein <graphic> als erstes Kind, URL nach Schema."""
    doc_id = doc.name[: -len("_final.xml")]
    root = _etree.parse(str(doc)).getroot()
    for surface in root.iter(f"{{{TEI_NS}}}surface"):
        children = [c for c in surface if isinstance(c.tag, str)]
        assert children and children[0].tag == f"{{{TEI_NS}}}graphic", (
            f"{doc.name}: Surface ohne <graphic> als erstes Kind")
        url = children[0].get("url", "")
        assert url.startswith(f"{doc_id}_p") and url.endswith(".png"), (
            f"{doc.name}: graphic url '{url}' entspricht nicht {{doc_id}}_p{{NNN}}.png")
