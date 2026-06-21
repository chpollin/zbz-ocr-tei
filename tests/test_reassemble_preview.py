"""Tests fuer die M3-Reassemble-Vorschau (scripts/tei/tei_reassemble_preview).

Zwei Ebenen:
1. Logik (CI-sicher, datenunabhaengig): w19_pages zaehlt nicht-kanonische Lesereihenfolge
   auf synthetischem TEI; build_report ist deterministisch.
2. Pipeline (lokal, gated): die Vorschau eines bekannten Spalten-Dokuments reassembliert
   nach tei_preview, bringt dessen W19 auf 0 und laesst tei_final unangetastet. Skippt auf
   einem frischen Clone / in CI, wo output/ (gitignored) fehlt.
"""

from __future__ import annotations

import hashlib

import pytest

from scripts.config import TEI_FINAL_DIR
from scripts.tei.tei_reassemble_preview import build_report, preview_document, w19_pages

_TEI_TWO_COLUMN_INVERTED = """<TEI xmlns="http://www.tei-c.org/ns/1.0">
  <facsimile>
    <surface xml:id="facs_1" ulx="0" uly="0" lrx="1000" lry="1000">
      <zone xml:id="facs_1_r_1" ulx="80" uly="50" lrx="920" lry="120"/>
      <zone xml:id="facs_1_r_2" ulx="550" uly="200" lrx="850" lry="380"/>
      <zone xml:id="facs_1_r_3" ulx="100" uly="200" lrx="400" lry="380"/>
    </surface>
  </facsimile>
  <text><body>
    <p facs="#facs_1_r_1">Kopf</p>
    <p facs="#facs_1_r_2">rechts</p>
    <p facs="#facs_1_r_3">links</p>
  </body></text>
</TEI>"""

_TEI_SINGLE_COLUMN = """<TEI xmlns="http://www.tei-c.org/ns/1.0">
  <facsimile>
    <surface xml:id="facs_1" ulx="0" uly="0" lrx="1000" lry="1000">
      <zone xml:id="facs_1_r_1" ulx="100" uly="100" lrx="900" lry="200"/>
      <zone xml:id="facs_1_r_2" ulx="100" uly="300" lrx="900" lry="400"/>
    </surface>
  </facsimile>
  <text><body>
    <p facs="#facs_1_r_1">oben</p>
    <p facs="#facs_1_r_2">unten</p>
  </body></text>
</TEI>"""


# --- Ebene 1: Logik ---

def test_w19_pages_flags_inverted_columns(tmp_path):
    f = tmp_path / "999_final.xml"
    f.write_text(_TEI_TWO_COLUMN_INVERTED, encoding="utf-8")
    assert w19_pages(f) == ["1"]


def test_w19_pages_clean_single_column_is_empty(tmp_path):
    f = tmp_path / "998_final.xml"
    f.write_text(_TEI_SINGLE_COLUMN, encoding="utf-8")
    assert w19_pages(f) == []


def test_w19_pages_malformed_returns_none(tmp_path):
    f = tmp_path / "997_final.xml"
    f.write_text("<TEI><unclosed>", encoding="utf-8")
    assert w19_pages(f) is None


def test_build_report_is_deterministic():
    summary = {
        "results": [
            {"doc_id": "890", "before": 6, "after": 0},
            {"doc_id": "1240", "before": 13, "after": 7},
        ],
        "docs": 2, "before_total": 19, "after_total": 7, "failed": [], "dropped": 0,
    }
    a = build_report(summary)
    b = build_report(summary)
    assert a == b
    assert "| 890 | 6 | 0 | -6 |" in a
    assert "| 1240 | 13 | 7 | -6 |" in a


def test_build_report_notes_dropped_and_failed():
    summary = {
        "results": [{"doc_id": "890", "before": 6, "after": 0}],
        "docs": 1, "before_total": 6, "after_total": 0,
        "failed": ["3040"], "dropped": 5,
    }
    report = build_report(summary)
    assert "3040" in report
    assert "5" in report


# --- Ebene 2: Pipeline (gated) ---

_GREEN_DOC = "890"  # Spalten-Dokument, dessen Reassemblierung W19 nachweislich auf 0 bringt
_HAS_LOCAL_CORPUS = (TEI_FINAL_DIR / f"{_GREEN_DOC}_final.xml").exists()


@pytest.mark.skipif(not _HAS_LOCAL_CORPUS, reason="output/tei_final fehlt (gitignored, kein lokaler Korpus)")
def test_preview_clears_w19_and_leaves_final_untouched():
    src = TEI_FINAL_DIR / f"{_GREEN_DOC}_final.xml"
    before_bytes = src.read_bytes()
    before_hash = hashlib.sha256(before_bytes).hexdigest()

    res = preview_document(_GREEN_DOC)

    # tei_final byte-identisch -> Vorschau ist reversibel, beruehrt die SoT nicht
    assert src.read_bytes() == before_bytes
    assert hashlib.sha256(src.read_bytes()).hexdigest() == before_hash

    # Vorschau korrigiert die Lesereihenfolge dieses Dokuments vollstaendig
    assert res["status"] == "ok"
    assert res["before"] > 0
    assert res["after"] == 0
