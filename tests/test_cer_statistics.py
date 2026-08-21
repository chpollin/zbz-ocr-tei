"""
Tests fuer scripts/cer_statistics.py.

Pruefen die statistischen Primitiven mit kontrollierten Synthetic-Daten:
- Bootstrap-CI deckt das wahre Mittel mit der erwarteten Wahrscheinlichkeit.
- Block-Bootstrap erhaelt Within-Block-Korrelation (CI breiter als naiver Bootstrap).
- Paired Bootstrap unterscheidet Null-Effekt von echtem Effekt.
- Selektionsbias-Tests reagieren wie erwartet auf bekannte Verzerrungen.
- Multi-Norm-CER reduziert sich monoton mit jeder Normalisierungs-Stufe (auf
  konstruierten Beispielen).
- Diakritik-Erhaltungsrate ist 1.0 bei perfekter Erhaltung, 0.0 bei totalem Verlust.

Reproduzierbarkeit: alle Tests fixieren Seed = 42.
"""

from __future__ import annotations

import numpy as np
import pytest

from scripts.eval.cer_statistics import (
    NORM_REGIMES,
    DocCERRecord,
    _erf_inv,
    _norm_cdf,
    _norm_ppf,
    aggregate_overall,
    bca_ci,
    block_bootstrap_resample,
    cer,
    cer_under_norms,
    chi_square_categorical,
    diacritic_preservation_rate,
    ks_continuous,
    levenshtein,
    normalize_text,
    paired_bootstrap_diff,
)

# ---------------- Levenshtein / CER ---------------- #

class TestLevenshtein:
    def test_identical(self):
        assert levenshtein("abc", "abc") == 0

    def test_substitution(self):
        assert levenshtein("abc", "abd") == 1

    def test_insertion(self):
        assert levenshtein("abc", "abcd") == 1

    def test_deletion(self):
        assert levenshtein("abcd", "abc") == 1

    def test_empty_vs_string(self):
        assert levenshtein("", "abc") == 3
        assert levenshtein("abc", "") == 3

    def test_unicode_diacritics(self):
        # 'café' vs 'cafe' = 1 substitution (é -> e)
        assert levenshtein("café", "cafe") == 1


class TestCER:
    def test_perfect(self):
        assert cer("hello", "hello") == 0.0

    def test_full_diff(self):
        assert cer("abc", "xyz") == 1.0

    def test_empty_reference(self):
        # Konvention: leere Referenz + leere Hypothese = 0.0
        assert cer("", "") == 0.0

    def test_empty_reference_nonempty_hyp(self):
        # leere Referenz, nicht-leere Hypothese: maximale Unsicherheit
        assert cer("", "hello") == 1.0

    def test_known_ratio(self):
        # 1 Fehler / 5 Zeichen = 0.2
        assert cer("hello", "jello") == pytest.approx(0.2)


# ---------------- Multi-Norm-CER ---------------- #

class TestNormalize:
    def test_raw_unchanged(self):
        s = "café­-Test"  # mit soft-hyphen
        assert normalize_text(s, "raw") == s

    def test_nfc_combines(self):
        # 'café' kann als 'café' (NFD) oder 'café' (NFC) vorliegen
        nfd = "café"
        assert normalize_text(nfd, "nfc") == "café"

    def test_nfc_hyphen_removes_soft_hyphen(self):
        s = "Wort­trennung"
        out = normalize_text(s, "nfc_hyphen")
        assert "­" not in out
        assert out == "Worttrennung"

    def test_nfc_hyphen_normalizes_dash_variants(self):
        # en-dash, em-dash -> ASCII '-'
        s = "a–b—c"  # U+2013, U+2014
        out = normalize_text(s, "nfc_hyphen")
        assert out == "a-b-c"

    def test_case_normalization(self):
        out = normalize_text("Hello WORLD", "nfc_hyphen_case")
        assert out == "hello world"

    def test_invalid_regime_raises(self):
        with pytest.raises(ValueError):
            normalize_text("x", "bogus")


class TestCERUnderNorms:
    def test_keys_match_regimes(self):
        result = cer_under_norms("foo", "foo")
        assert set(result.keys()) == set(NORM_REGIMES)

    def test_case_only_diff_resolved_by_case_norm(self):
        # "Hello" vs "hello": CER 0.2 unter raw/nfc, CER 0 unter case-fold
        result = cer_under_norms("Hello", "hello")
        assert result["raw"] == pytest.approx(0.2)
        assert result["nfc_hyphen_case"] == 0.0

    def test_soft_hyphen_diff_resolved_by_hyphen_norm(self):
        # "Wort­trennung" vs "Worttrennung": fehlt 1 Zeichen
        result = cer_under_norms("Wort­trennung", "Worttrennung")
        assert result["raw"] > 0
        assert result["nfc_hyphen"] == 0.0

    def test_monotonic_reduction(self):
        # Konstruierter Worst-Case: case + soft-hyphen Differenzen.
        ref = "Wort­trennung HELLO"
        hyp = "worttrennung hello"
        r = cer_under_norms(ref, hyp)
        # Jede Stufe <= vorherige
        assert r["raw"] >= r["nfc"] >= r["nfc_hyphen"] >= r["nfc_hyphen_case"]


# ---------------- Diakritik-Erhaltungsrate ---------------- #

class TestDiacriticRate:
    def test_perfect_preservation(self):
        ref = "café crème éphémère"
        hyp = "café crème éphémère"
        r = diacritic_preservation_rate(ref, hyp, "fra")
        assert r["rate"] == 1.0
        assert r["expected_count"] == r["observed_count"]

    def test_total_loss(self):
        ref = "éàçùôê"
        hyp = "eaucoe"  # alle Diakritika weg
        r = diacritic_preservation_rate(ref, hyp, "fra")
        assert r["rate"] == 0.0

    def test_partial_loss(self):
        # 4 Diakritika, davon 2 erhalten
        ref = "éàçù"
        hyp = "éàcu"
        r = diacritic_preservation_rate(ref, hyp, "fra")
        assert r["expected_count"] == 4
        assert r["observed_count"] == 2
        assert r["rate"] == 0.5

    def test_unknown_language_yields_none(self):
        r = diacritic_preservation_rate("abc", "abc", "klingon")
        assert r["rate"] is None

    def test_no_diacritics_in_reference(self):
        # Wenn die Referenz keine Diakritika hat, ist die Rate definiert als 1.0
        # (perfekt) wenn auch die Hypothese keine hat, sonst 0.0 (Halluzination).
        r_perfect = diacritic_preservation_rate("abc", "abc", "fra")
        r_halluc = diacritic_preservation_rate("abc", "abé", "fra")
        assert r_perfect["rate"] == 1.0
        assert r_halluc["rate"] == 0.0


# ---------------- Normal-CDF / PPF / erf-inv ---------------- #

class TestNormalApprox:
    def test_norm_cdf_known_values(self):
        assert _norm_cdf(0.0) == pytest.approx(0.5, abs=1e-6)
        assert _norm_cdf(1.96) == pytest.approx(0.975, abs=1e-3)
        assert _norm_cdf(-1.96) == pytest.approx(0.025, abs=1e-3)

    def test_norm_ppf_inverse_of_cdf(self):
        for p in [0.025, 0.1, 0.25, 0.5, 0.75, 0.9, 0.975]:
            z = _norm_ppf(p)
            assert _norm_cdf(z) == pytest.approx(p, abs=1e-3)

    def test_erf_inv_known(self):
        # erf_inv(0) = 0, erf_inv(erf(1)) ~ 1
        from math import erf
        assert _erf_inv(0.0) == pytest.approx(0.0, abs=1e-6)
        assert _erf_inv(erf(1.0)) == pytest.approx(1.0, abs=1e-2)


# ---------------- Block-Bootstrap-Resample ---------------- #

class TestBlockResample:
    def test_returns_concatenated_blocks(self):
        rng = np.random.default_rng(0)
        blocks = [[1.0, 2.0], [3.0], [4.0, 5.0, 6.0]]
        sample = block_bootstrap_resample(blocks, rng)
        # Resample muss aus einer Konkatenation **vollstaendiger** Bloecke bestehen.
        # Total-Length = Summe der gezogenen Block-Laengen.
        assert sample.size > 0
        # Pruefen: jede Wert ist aus einem der Bloecke (kein "Mischen")
        all_vals = set(v for b in blocks for v in b)
        assert all(v in all_vals for v in sample)

    def test_empty_blocks(self):
        rng = np.random.default_rng(0)
        sample = block_bootstrap_resample([], rng)
        assert sample.size == 0

    def test_seed_determinism(self):
        blocks = [[1.0, 2.0], [3.0], [4.0, 5.0]]
        rng_a = np.random.default_rng(42)
        rng_b = np.random.default_rng(42)
        sa = block_bootstrap_resample(blocks, rng_a)
        sb = block_bootstrap_resample(blocks, rng_b)
        np.testing.assert_array_equal(sa, sb)


# ---------------- BCa-CI ---------------- #

class TestBcaCI:
    def test_point_estimate_matches_statistic(self):
        # Jeder Block ein Doc; alle Werte = 0.05
        blocks = [[0.05] * 10 for _ in range(20)]
        point, lo, hi = bca_ci(blocks, np.mean, n_resamples=500, seed=42)
        assert point == pytest.approx(0.05, abs=1e-9)
        # Bei null Varianz: CI ist degeneriert (lo == hi == point)
        assert lo == pytest.approx(point, abs=1e-9)
        assert hi == pytest.approx(point, abs=1e-9)

    def test_ci_contains_point_and_is_ordered(self):
        rng = np.random.default_rng(123)
        # 30 "Docs" mit 5 Pages, normalverteilt um 0.04
        blocks = [list(rng.normal(0.04, 0.01, size=5)) for _ in range(30)]
        point, lo, hi = bca_ci(blocks, np.mean, n_resamples=2000, seed=42)
        assert lo <= point <= hi
        # CI sollte wahres Mittel (0.04) enthalten
        assert lo <= 0.04 <= hi

    def test_block_bootstrap_wider_than_naive_for_correlated_data(self):
        # Konstruktion: 20 Docs, jedes Doc 10 Pages mit perfekter Within-Doc-Korrelation
        # (alle Pages eines Docs = derselbe Wert, aber Wert variiert pro Doc).
        # Naiver Bootstrap ueber 200 unabhaengige "Pages" wuerde n=200 annehmen,
        # Block-Bootstrap erkennt: effektiv n=20.
        rng = np.random.default_rng(7)
        doc_vals = rng.normal(0.05, 0.02, size=20)
        blocks = [[v] * 10 for v in doc_vals]
        _, lo_block, hi_block = bca_ci(blocks, np.mean, n_resamples=2000, seed=42)

        # Naiver Bootstrap: alle 200 Werte als ein einziger "Block" pro Wert
        naive_blocks = [[v] for b in blocks for v in b]
        _, lo_naive, hi_naive = bca_ci(naive_blocks, np.mean, n_resamples=2000, seed=42)

        block_width = hi_block - lo_block
        naive_width = hi_naive - lo_naive
        # Block-CI muss strikt breiter sein -- das ist der Punkt der Methodik.
        assert block_width > naive_width * 1.5, (
            f"Block-CI ({block_width:.4f}) sollte deutlich breiter als naiver CI "
            f"({naive_width:.4f}) sein bei Within-Doc-Korrelation."
        )

    def test_empty_blocks(self):
        point, lo, hi = bca_ci([], np.mean, n_resamples=100)
        assert all(np.isnan([point, lo, hi]))

    def test_single_block(self):
        # n=1 -> CI nicht berechenbar, Fallback auf Punktwert
        point, lo, hi = bca_ci([[0.05, 0.06]], np.mean, n_resamples=100)
        assert lo == hi == point

    def test_seed_determinism(self):
        rng = np.random.default_rng(0)
        blocks = [list(rng.normal(0.05, 0.01, size=5)) for _ in range(10)]
        a = bca_ci(blocks, np.mean, n_resamples=500, seed=42)
        b = bca_ci(blocks, np.mean, n_resamples=500, seed=42)
        assert a == b


# ---------------- Paired Bootstrap ---------------- #

class TestPairedBootstrap:
    def test_zero_diff_yields_high_p(self):
        # Differenzen um 0 -> p_two_sided gross
        rng = np.random.default_rng(0)
        diffs = list(rng.normal(0.0, 0.005, size=20))
        res = paired_bootstrap_diff(diffs, n_resamples=2000, seed=42)
        assert res["p_two_sided"] > 0.05
        assert res["ci_low"] < 0 < res["ci_high"]

    def test_clear_positive_effect(self):
        # Differenzen klar > 0 -> p klein, CI ueber 0
        rng = np.random.default_rng(0)
        diffs = list(rng.normal(0.05, 0.01, size=20))
        res = paired_bootstrap_diff(diffs, n_resamples=2000, seed=42)
        assert res["mean_diff"] > 0
        assert res["ci_low"] > 0
        assert res["p_two_sided"] < 0.05

    def test_empty_input(self):
        res = paired_bootstrap_diff([])
        assert res["n"] == 0
        assert np.isnan(res["mean_diff"])

    def test_seed_determinism(self):
        diffs = [0.01, 0.02, -0.01, 0.03, 0.0, 0.015]
        a = paired_bootstrap_diff(diffs, n_resamples=500, seed=42)
        b = paired_bootstrap_diff(diffs, n_resamples=500, seed=42)
        assert a == b


# ---------------- Selektionsbias-Tests ---------------- #

class TestChiSquare:
    def test_identical_distributions_high_p(self):
        ref = {"fra": 11, "deu": 5, "fra/deu": 3}
        cor = {"fra": 110, "deu": 50, "fra/deu": 30}
        res = chi_square_categorical(ref, cor)
        assert res["p"] > 0.5
        assert res["comparable"] is True

    def test_skewed_reference_low_p(self):
        # Korpus: 90% A, 10% B. Referenz: 50/50 -> deutliche Verzerrung.
        ref = {"A": 50, "B": 50}
        cor = {"A": 900, "B": 100}
        res = chi_square_categorical(ref, cor)
        assert res["p"] < 0.001
        assert res["comparable"] is False

    def test_empty_inputs(self):
        res = chi_square_categorical({}, {})
        assert res["comparable"] is None


class TestKS:
    def test_same_distribution_high_p(self):
        rng = np.random.default_rng(0)
        a = list(rng.normal(10, 3, size=50))
        b = list(rng.normal(10, 3, size=200))
        res = ks_continuous(a, b)
        assert res["p"] > 0.05
        assert res["comparable"] is True

    def test_different_distributions_low_p(self):
        rng = np.random.default_rng(0)
        a = list(rng.normal(10, 3, size=50))
        b = list(rng.normal(50, 3, size=200))
        res = ks_continuous(a, b)
        assert res["p"] < 0.001
        assert res["comparable"] is False

    def test_empty_inputs(self):
        res = ks_continuous([], [])
        assert res["comparable"] is None


# ---------------- Aggregate-Overall ---------------- #

class TestWeightedCER:
    """DocCERRecord.weighted_cer muss char-gewichtete Doc-CER liefern,
    nicht den naiven Per-Page-Mittelwert.
    """
    def test_uniform_weights_match_mean(self):
        # Alle Seiten gleich gross -> weighted_cer == arithm. Mittel
        rec = DocCERRecord(
            doc_id="x",
            page_cers=[0.01, 0.02, 0.03],
            page_ref_chars=[100, 100, 100],
            cer_by_regime={},
            metadata={},
            scope_status="full",
        )
        assert rec.weighted_cer == pytest.approx(0.02)

    def test_outlier_page_with_few_chars_does_not_dominate(self):
        # Eine 1-Char-Seite mit absurdem CER (50.0) darf den Doc-CER nicht zerstoeren.
        rec = DocCERRecord(
            doc_id="x",
            page_cers=[0.01, 50.0],
            page_ref_chars=[10000, 1],
            cer_by_regime={},
            metadata={},
            scope_status="full",
        )
        # weighted = (0.01*10000 + 50.0*1) / 10001 = 150/10001 ~ 0.0150
        assert rec.weighted_cer == pytest.approx(0.015, abs=1e-3)

    def test_doc_cer_override(self):
        # Wenn doc_cer explizit gesetzt: das ist die Quelle der Wahrheit.
        rec = DocCERRecord(
            doc_id="x",
            page_cers=[0.99],
            page_ref_chars=[100],
            cer_by_regime={},
            metadata={},
            scope_status="full",
            doc_cer=0.04,
        )
        assert rec.weighted_cer == 0.04

    def test_zero_chars_returns_zero(self):
        rec = DocCERRecord(
            doc_id="x", page_cers=[], page_ref_chars=[],
            cer_by_regime={}, metadata={}, scope_status="full",
        )
        assert rec.weighted_cer == 0.0


class TestAggregateOverall:
    def _make_records(self, n_docs: int, n_pages: int, mean: float, sd: float, seed: int):
        rng = np.random.default_rng(seed)
        recs = []
        for i in range(n_docs):
            page_cers = list(np.clip(rng.normal(mean, sd, size=n_pages), 0, 1))
            recs.append(DocCERRecord(
                doc_id=str(i),
                page_cers=page_cers,
                page_ref_chars=[100] * n_pages,
                cer_by_regime={r: float(np.mean(page_cers)) for r in NORM_REGIMES},
                metadata={"language": "fra", "layout_type": "A", "pub_form": "book"},
                scope_status="full",
            ))
        return recs

    def test_recovers_synthetic_mean(self):
        recs = self._make_records(n_docs=20, n_pages=5, mean=0.04, sd=0.01, seed=0)
        out = aggregate_overall(recs, n_resamples=500, seed=42)
        assert out["mean"] == pytest.approx(0.04, abs=0.01)
        assert out["mean_ci95"][0] <= 0.04 <= out["mean_ci95"][1]
        assert out["n_docs"] == 20

    def test_empty_records(self):
        out = aggregate_overall([], n_resamples=100, seed=42)
        assert out["n_docs"] == 0
        assert out["mean"] is None

    def test_deterministic(self):
        recs = self._make_records(10, 5, 0.05, 0.01, seed=0)
        a = aggregate_overall(recs, n_resamples=500, seed=42)
        b = aggregate_overall(recs, n_resamples=500, seed=42)
        assert a == b
