"""
Tests fuer scripts/eval/corpus_audit.py.

Zwei Ebenen:
1. Reine Hilfsfunktionen (_norm_id, _stats, _doc_from_page_file, reconcile,
   drift_check) auf synthetischen Daten -- laufen ueberall, ohne Primaerdaten.
2. Daten-Integritaets-Invarianten auf den echten Primaerquellen -- werden
   uebersprungen, wenn Masterfile/Scans/tei_final fehlen (CI, frischer Clone:
   data/source/pdf + data/source/masterfile sind nicht versioniert).

Operationalisiert die Lehre aus der Primaerdaten-Analyse: Korpus-Kennzahlen
sind reproduzierbare Assertions, nicht handgepflegte Prosa. Insbesondere wird
der stille Verlust eines Dokuments (Doc 10 in scans, aber ohne finales TEI)
zu einem lauten Test-Signal.
"""

from __future__ import annotations

import pytest

from scripts.config import MASTERFILE_PATH, SCANS_DIR, TEI_FINAL_DIR
from scripts.eval.corpus_audit import (
    KNOWLEDGE_CLAIMS,
    _doc_from_page_file,
    _norm_id,
    _stats,
    build_report,
    delivered_distribution,
    drift_check,
    reconcile,
)


# ---------------- reine Hilfsfunktionen ---------------- #

class TestNormId:
    def test_int_like_float(self):
        assert _norm_id(10.0) == "10"

    def test_int(self):
        assert _norm_id(1330) == "1330"

    def test_str_with_space(self):
        assert _norm_id("  1330 ") == "1330"

    def test_none_and_empty(self):
        assert _norm_id(None) is None
        assert _norm_id("") is None
        assert _norm_id("   ") is None

    def test_non_numeric_passthrough(self):
        assert _norm_id("abc") == "abc"


class TestStats:
    def test_empty(self):
        s = _stats([])
        assert s == {"n": 0, "sum": 0, "median": None, "min": None, "max": None}

    def test_ignores_none(self):
        s = _stats([1, None, 3])
        assert s["n"] == 2 and s["sum"] == 4

    def test_basic(self):
        s = _stats([1, 2, 3, 4])
        assert s["median"] == 2.5 and s["min"] == 1 and s["max"] == 4 and s["sum"] == 10


class TestDocFromPageFile:
    def test_basic(self):
        assert _doc_from_page_file("1330_p2.md") == "1330"

    def test_multi_digit_page(self):
        assert _doc_from_page_file("40_p156.md") == "40"

    def test_no_page_suffix(self):
        assert _doc_from_page_file("1330.md") == "1330"


class TestReconcile:
    @staticmethod
    def _tiers():
        t0 = {
            "texts": 4,
            "digitalisiert": {"ja": 3},
            "ids": ["10", "20", "30", "40"],
            "digitalisiert_ja_ids": ["10", "20", "30"],
            "anzahl_seiten": {"sum": 100},
        }
        t1 = {"pdfs": 2, "ids": ["10", "20"], "physical_pages": {"sum": 50}}
        t2 = {"tei_final_docs": 1, "tei_final_ids": ["20"],
              "ocr_md_pages": 48, "tei_pb_total": 47}
        t3 = {"available": True, "page_count": {"sum": 49}}
        return t0, t1, t2, t3

    def test_funnel_values(self):
        rec = reconcile(*self._tiers())
        assert [s["n"] for s in rec["funnel"]] == [4, 3, 2, 1]

    def test_digitalisiert_not_delivered(self):
        rec = reconcile(*self._tiers())
        assert rec["digitalisiert_not_delivered"] == ["30"]

    def test_scans_without_tei(self):
        rec = reconcile(*self._tiers())
        assert rec["scans_without_final_tei"] == ["10"]

    def test_page_counts_by_source(self):
        pcs = reconcile(*self._tiers())["page_counts_by_source"]
        assert pcs["masterfile_bibliographic"] == 100
        assert pcs["pdf_physical"] == 50
        assert pcs["ocr_md"] == 48
        assert pcs["tei_pb"] == 47
        assert pcs["gemini_page_count_field"] == 49


class TestDeliveredDistribution:
    @staticmethod
    def _t0():
        return {"by_id": {
            "10": {"publform": "journalArticle", "sprache": "fr", "jahr": 1975},
            "20": {"publform": "book", "sprache": "de", "jahr": 1980},
            "30": {"publform": "journalArticle", "sprache": "fr", "jahr": 2001},
        }}

    def test_filters_to_delivered_subset(self):
        # geliefert: 10 + 20 (30 nicht); 99 geliefert, aber nicht im Masterfile
        dd = delivered_distribution(self._t0(), ["10", "20", "99"])
        assert dd["n"] == 2
        assert dd["not_in_masterfile"] == ["99"]
        assert dd["publform"] == {"journalArticle": 1, "book": 1}
        assert dd["sprache"] == {"fr": 1, "de": 1}
        assert dd["jahr"] == {"min": 1975, "max": 1980, "count_1970_1989": 2}

    def test_empty_when_no_overlap(self):
        dd = delivered_distribution(self._t0(), ["999"])
        assert dd["n"] == 0 and dd["publform"] == {} and dd["jahr"]["min"] is None


class TestDriftCheck:
    @staticmethod
    def _matching_tiers():
        """Tiers, deren berechnete Werte exakt den KNOWLEDGE_CLAIMS entsprechen."""
        t0 = {"texts": KNOWLEDGE_CLAIMS["masterfile_texts"],
              "anzahl_seiten": {"sum": KNOWLEDGE_CLAIMS["pages_total"]}}
        t1 = {"pdfs": KNOWLEDGE_CLAIMS["pdfs"]}
        t2 = {"tei_final_docs": KNOWLEDGE_CLAIMS["tei_produced"],
              "ocr_md_pages": KNOWLEDGE_CLAIMS["pages_processed"]}
        return t0, t1, t2, {}

    def test_all_ok_when_matching(self):
        result = drift_check(*self._matching_tiers())
        assert all(d["status"] == "OK" for d in result)

    def test_flags_single_drift(self):
        t0, t1, t2, t3 = self._matching_tiers()
        t0["texts"] = KNOWLEDGE_CLAIMS["masterfile_texts"] + 36  # weicht ab
        by = {d["metric"]: d for d in drift_check(t0, t1, t2, t3)}
        assert by["masterfile_texts"]["status"] == "DRIFT"
        assert by["masterfile_texts"]["computed"] == KNOWLEDGE_CLAIMS["masterfile_texts"] + 36
        assert by["pdfs"]["status"] == "OK"


# ---------------- Daten-Integritaet auf den Primaerquellen ---------------- #

def _data_available() -> bool:
    return (
        MASTERFILE_PATH.exists()
        and SCANS_DIR.exists()
        and TEI_FINAL_DIR.exists()
        and any(TEI_FINAL_DIR.glob("*_final.xml"))
    )


@pytest.fixture(scope="module")
def report():
    if not _data_available():
        pytest.skip("Primaerdaten (Masterfile/Scans/tei_final) nicht vorhanden")
    return build_report()


@pytest.mark.skipif(not _data_available(), reason="Primaerdaten nicht vorhanden")
class TestCorpusInvariants:
    def test_funnel_monotonic(self, report):
        ns = [s["n"] for s in report["reconciliation"]["funnel"]]
        assert ns == sorted(ns, reverse=True), f"Trichter nicht monoton fallend: {ns}"

    def test_no_orphan_tei(self, report):
        """Jedes finale TEI muss ein geliefertes Quell-PDF haben."""
        scan_ids = set(report["tier1_pdfs"]["ids"])
        tei_ids = set(report["tier2_pipeline"]["tei_final_ids"])
        orphans = sorted(tei_ids - scan_ids)
        assert orphans == [], f"TEI ohne Quell-PDF: {orphans}"

    def test_scans_in_masterfile(self, report):
        """Jedes gelieferte PDF muss in der Masterfile katalogisiert sein."""
        assert report["reconciliation"]["scans_not_in_masterfile"] == []

    def test_known_completeness_gap(self, report):
        """Known-State-Guard: stiller Doc-Verlust wird zum lauten Signal.
        Schlaegt an, wenn ein NEUES Doc fehlt ODER Doc 10 endlich verarbeitet
        wird -- beides erfordert eine bewusste Aktualisierung dieser Erwartung.
        """
        gap = report["reconciliation"]["scans_without_final_tei"]
        assert gap == ["10"], f"Vollstaendigkeits-Luecke veraendert: {gap}"

    def test_page_counts_positive(self, report):
        pcs = report["reconciliation"]["page_counts_by_source"]
        for key in ("masterfile_bibliographic", "pdf_physical", "ocr_md", "tei_pb"):
            assert pcs[key] and pcs[key] > 0, f"{key} fehlt oder <= 0"
