"""
CER Statistik mit Konfidenzintervallen, Block-Bootstrap und Selektionsbias-Diagnostik.

Produziert `docs/data/cer_statistics.json` als Single Source of Truth fuer das
CER-Dashboard (`docs/infrastruktur/cer.html`) und die Knowledge-Doku
(`knowledge/CER-METHODIK.md`, `knowledge/CER-BENCHMARK.md`).

Methodik (alle Quellen 2025+):
- BCa-Bootstrap (Bias-Corrected and Accelerated), B = 10 000, Seed konfigurierbar.
- Blockwise Resampling mit Block = Dokument: Pages innerhalb eines Docs sind
  korreliert (gleicher Scan, gleicher Engine-Run); naiver Page-Bootstrap
  ueberschaetzt die Praezision. Methodisch begruendet ueber:
    Du 2025, "When +1% Is Not Enough: A Paired Bootstrap Protocol",
    arXiv:2511.19794 (Reproduzierbarkeitsprotokoll, Per-Seed-Metrics).
- Paired Bootstrap fuer Per-Doc-Differenzen (Pipeline vs. Pre-Pipeline-OCR).
- Selektionsbias-Tests: chi-square fuer kategoriale Strata, KS fuer Seitenzahl;
  Referenz-Subset (n=25) vs. Gesamtkorpus (n=285).
- Domain-Metrik: Diakritik-Erhaltungsrate (HCPR-Adaption) fuer franzoesische
  und deutsche Sonderzeichen. Methodisch ueber:
    Levchenko 2025, "Evaluating LLMs for Historical Document OCR",
    arXiv:2510.06743.
- Multi-Normalisierungs-Regimes: raw / nfc / nfc_hyphen / nfc_hyphen_case --
  publiziert alle, damit die Wirkung jeder Normalisierung transparent ist.
- OCR-CER vs End-to-End-CER getrennt (overall.end_to_end vs overall.ocr_only).
"""

from __future__ import annotations

import argparse
import json
import math
import re
import subprocess
import sys
import unicodedata
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import numpy as np

try:
    from scipy import stats as scipy_stats
except ImportError:
    scipy_stats = None  # graceful: chi-square + KS koennen wir auch selbst rechnen


__version__ = "0.1.0"

# Diakritika fuer Domain-Metrik (HCPR-Adaption Levchenko 2025).
# Pro Sprache: erwartete Sonderzeichen aus FR/DE-Korpora.
DIACRITICS = {
    "fra": set("éèàçùâêîôûëïüœÉÈÀÇÙÂÊÎÔÛËÏÜŒ"),
    "deu": set("äöüßÄÖÜẞ"),
    "ita": set("àèéìòùÀÈÉÌÒÙ"),
}

# Normalisierungs-Regimes -- werden alle berechnet und nebeneinander publiziert.
NORM_REGIMES = ("raw", "nfc", "nfc_hyphen", "nfc_hyphen_case")


# -------------------------------------------------------------------- #
# Bootstrap-Primitive
# -------------------------------------------------------------------- #

def block_bootstrap_resample(
    blocks: Sequence[Sequence[float]],
    rng: np.random.Generator,
) -> np.ndarray:
    """Eine Block-Bootstrap-Stichprobe: Bloecke (= Dokumente) mit Zuruecklegen
    ziehen, dann konkatenieren. Block-Struktur erhaelt die Within-Doc-Korrelation.

    Args:
        blocks: Liste von Bloecken; jeder Block ist eine Sequenz von Werten
                (z.B. Per-Page-CERs eines Doks).
        rng: numpy Generator (deterministisch via Seed gesetzt).

    Returns:
        Konkatenierte Werte einer Resample-Iteration (1D-Array).
    """
    n_blocks = len(blocks)
    if n_blocks == 0:
        return np.array([])
    indices = rng.integers(0, n_blocks, size=n_blocks)
    out: list[float] = []
    for i in indices:
        out.extend(blocks[i])
    return np.asarray(out, dtype=float)


def bca_ci(
    blocks: Sequence[Sequence[float]],
    statistic: Callable[[np.ndarray], float],
    n_resamples: int = 10_000,
    alpha: float = 0.05,
    seed: int = 42,
) -> tuple[float, float, float]:
    """BCa-95-%-Konfidenzintervall fuer eine Statistik (mean, median, ...).

    Block-Bootstrap mit Block = Dokument. Bias-Korrektur (z0) und Acceleration (a)
    via Jackknife auf Block-Ebene. Bei n=19 Bloecken ist das stabiler als naive
    Perzentil-CIs, weil die Verteilung skewed sein kann.

    Args:
        blocks: Liste von Bloecken (Pages je Dok).
        statistic: Funktion 1D-Array -> float (z.B. np.mean, np.median).
        n_resamples: Anzahl Bootstrap-Iterationen.
        alpha: Signifikanzniveau (0.05 -> 95%-CI).
        seed: RNG-Seed (Reproduzierbarkeit).

    Returns:
        (point_estimate, ci_low, ci_high). Bei < 2 Bloecken: (point, point, point).
    """
    non_empty = [np.asarray(b, dtype=float) for b in blocks if len(b) > 0]
    if not non_empty:
        return (float("nan"), float("nan"), float("nan"))
    flat = np.concatenate(non_empty)

    point = float(statistic(flat))

    n_blocks = len(blocks)
    if n_blocks < 2:
        return (point, point, point)

    rng = np.random.default_rng(seed)
    boot_stats = np.empty(n_resamples, dtype=float)
    for i in range(n_resamples):
        sample = block_bootstrap_resample(blocks, rng)
        if sample.size == 0:
            boot_stats[i] = point
        else:
            boot_stats[i] = statistic(sample)

    # Bias-Korrektur z0: Anteil der Bootstrap-Werte unter dem Punktwert.
    below = float(np.mean(boot_stats < point))
    # Clamp gegen 0/1, sonst ppf -> +/- inf.
    below = min(max(below, 1.0 / (2 * n_resamples)), 1.0 - 1.0 / (2 * n_resamples))
    z0 = _norm_ppf(below)

    # Jackknife auf Block-Ebene fuer Acceleration a.
    jack = np.empty(n_blocks, dtype=float)
    for i in range(n_blocks):
        kept = [b for j, b in enumerate(blocks) if j != i]
        kept_flat = np.concatenate(
            [np.asarray(b, dtype=float) for b in kept if len(b) > 0]
        )
        jack[i] = statistic(kept_flat) if kept_flat.size > 0 else point
    jack_mean = jack.mean()
    num = float(np.sum((jack_mean - jack) ** 3))
    den = 6.0 * float(np.sum((jack_mean - jack) ** 2)) ** 1.5
    a = num / den if den > 0 else 0.0

    z_lo = _norm_ppf(alpha / 2)
    z_hi = _norm_ppf(1 - alpha / 2)
    alpha_lo = _norm_cdf(z0 + (z0 + z_lo) / max(1 - a * (z0 + z_lo), 1e-12))
    alpha_hi = _norm_cdf(z0 + (z0 + z_hi) / max(1 - a * (z0 + z_hi), 1e-12))
    alpha_lo = min(max(alpha_lo, 0.0), 1.0)
    alpha_hi = min(max(alpha_hi, 0.0), 1.0)

    sorted_stats = np.sort(boot_stats)
    lo = float(sorted_stats[int(alpha_lo * (n_resamples - 1))])
    hi = float(sorted_stats[int(alpha_hi * (n_resamples - 1))])
    return (point, lo, hi)


def paired_bootstrap_diff(
    diffs: Sequence[float],
    n_resamples: int = 10_000,
    alpha: float = 0.05,
    seed: int = 42,
) -> dict:
    """Paired Bootstrap auf Per-Doc-Differenzen (z.B. Pipeline-CER - Baseline-CER).

    Resampling mit Zuruecklegen aus den Per-Doc-Differenzen, Mean der Differenz
    + Perzentil-CI + zwei-seitiger p-Wert (Anteil Resamples mit anderem Vorzeichen
    als der Punktwert -- konventionelle Bootstrap-p-Wert-Approximation).

    Returns:
        Dict mit mean_diff, ci_low, ci_high, p_two_sided, n.
    """
    arr = np.asarray(diffs, dtype=float)
    n = arr.size
    if n == 0:
        return {"mean_diff": float("nan"), "ci_low": float("nan"),
                "ci_high": float("nan"), "p_two_sided": float("nan"), "n": 0}

    rng = np.random.default_rng(seed)
    point = float(arr.mean())

    # Perzentil-CI: einfacher und bei kleinen n robuster als BCa fuer Differenzen.
    boot = np.empty(n_resamples, dtype=float)
    for i in range(n_resamples):
        idx = rng.integers(0, n, size=n)
        boot[i] = arr[idx].mean()
    boot.sort()
    lo = float(boot[int(alpha / 2 * (n_resamples - 1))])
    hi = float(boot[int((1 - alpha / 2) * (n_resamples - 1))])

    # Bootstrap-p-Wert: Anteil Resamples, die das Vorzeichen wechseln.
    if point > 0:
        p_one = float(np.mean(boot <= 0))
    elif point < 0:
        p_one = float(np.mean(boot >= 0))
    else:
        p_one = 0.5
    p_two = min(2 * p_one, 1.0)

    return {
        "mean_diff": point, "ci_low": lo, "ci_high": hi,
        "p_two_sided": p_two, "n": int(n),
    }


def _norm_cdf(z: float) -> float:
    """CDF der Standardnormalverteilung (ohne scipy-Dependency)."""
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def _norm_ppf(p: float) -> float:
    """Inverse CDF (Quantilfunktion) der Standardnormalverteilung.
    Approximation nach Beasley-Springer-Moro; ausreichend fuer alpha in [0.001, 0.999].
    """
    if p <= 0.0:
        return -float("inf")
    if p >= 1.0:
        return float("inf")
    # Symmetrische Inverse via inverse error function.
    return math.sqrt(2.0) * _erf_inv(2.0 * p - 1.0)


def _erf_inv(x: float) -> float:
    """Approximation der inversen Fehlerfunktion (Winitzki 2008)."""
    a = 0.147
    sign = 1.0 if x >= 0 else -1.0
    ln_term = math.log(max(1.0 - x * x, 1e-300))
    first = 2.0 / (math.pi * a) + ln_term / 2.0
    inside = first * first - ln_term / a
    return sign * math.sqrt(math.sqrt(inside) - first)


# -------------------------------------------------------------------- #
# Selektionsbias-Tests
# -------------------------------------------------------------------- #

def chi_square_categorical(
    reference_counts: dict[str, int],
    corpus_counts: dict[str, int],
) -> dict:
    """Chi-Square-Goodness-of-Fit: weicht die Verteilung der Referenz-Doks
    (n=25) von der des Gesamtkorpus (n=285) ab?

    Erwartete Haeufigkeiten = corpus_proportions * n_reference. Kategorien mit
    erwarteter Haeufigkeit < 1 werden gepoolt in "_other_".

    Returns: {chi2, dof, p, comparable, n_reference, n_corpus, categories}.
    """
    n_ref = sum(reference_counts.values())
    n_corp = sum(corpus_counts.values())
    if n_ref == 0 or n_corp == 0:
        return {"chi2": float("nan"), "dof": 0, "p": float("nan"),
                "comparable": None, "n_reference": n_ref, "n_corpus": n_corp,
                "categories": []}

    keys = sorted(set(reference_counts) | set(corpus_counts))
    obs, exp, kept_keys = [], [], []
    pooled_obs = 0.0
    pooled_exp = 0.0
    for k in keys:
        e = corpus_counts.get(k, 0) / n_corp * n_ref
        o = reference_counts.get(k, 0)
        if e < 1.0:
            pooled_obs += o
            pooled_exp += e
        else:
            obs.append(o)
            exp.append(e)
            kept_keys.append(k)
    if pooled_exp >= 1.0:
        obs.append(pooled_obs)
        exp.append(pooled_exp)
        kept_keys.append("_other_")
    if len(obs) < 2:
        return {"chi2": 0.0, "dof": 0, "p": 1.0, "comparable": True,
                "n_reference": n_ref, "n_corpus": n_corp, "categories": kept_keys}

    chi2 = float(sum((o - e) ** 2 / e for o, e in zip(obs, exp)))
    dof = len(obs) - 1
    if scipy_stats is not None:
        p = float(scipy_stats.chi2.sf(chi2, dof))
    else:
        p = _chi2_sf_approx(chi2, dof)
    return {
        "chi2": chi2, "dof": dof, "p": p,
        "comparable": p > 0.05,  # H0 (gleiche Verteilung) nicht abgelehnt
        "n_reference": n_ref, "n_corpus": n_corp,
        "categories": kept_keys,
    }


def ks_continuous(
    reference_values: Sequence[float],
    corpus_values: Sequence[float],
) -> dict:
    """Zwei-Stichproben-Kolmogorov-Smirnov-Test fuer kontinuierliche Strata
    (z.B. Seitenzahl). H0: gleiche Verteilung. p > 0.05 -> 'comparable'.
    """
    a = np.asarray(reference_values, dtype=float)
    b = np.asarray(corpus_values, dtype=float)
    if a.size == 0 or b.size == 0:
        return {"ks_stat": float("nan"), "p": float("nan"),
                "comparable": None, "n_reference": int(a.size), "n_corpus": int(b.size)}

    if scipy_stats is not None:
        res = scipy_stats.ks_2samp(a, b)
        ks = float(res.statistic)
        p = float(res.pvalue)
    else:
        # Manuelle KS-Statistik + asymptotische Approximation.
        merged = np.sort(np.concatenate([a, b]))
        cdf_a = np.searchsorted(np.sort(a), merged, side="right") / a.size
        cdf_b = np.searchsorted(np.sort(b), merged, side="right") / b.size
        ks = float(np.max(np.abs(cdf_a - cdf_b)))
        en = math.sqrt(a.size * b.size / (a.size + b.size))
        p = float(_ks_p_approx((en + 0.12 + 0.11 / en) * ks))
    return {
        "ks_stat": ks, "p": p,
        "comparable": p > 0.05,
        "n_reference": int(a.size), "n_corpus": int(b.size),
    }


def _chi2_sf_approx(chi2: float, dof: int) -> float:
    """Survival Function (1 - CDF) der Chi-Square-Verteilung via Wilson-Hilferty."""
    if chi2 <= 0 or dof <= 0:
        return 1.0
    # Wilson-Hilferty: ((chi2/dof)^(1/3) - (1 - 2/(9 dof))) / sqrt(2/(9 dof)) ~ N(0,1)
    z = ((chi2 / dof) ** (1.0 / 3.0) - (1.0 - 2.0 / (9.0 * dof))) / math.sqrt(2.0 / (9.0 * dof))
    return 1.0 - _norm_cdf(z)


def _ks_p_approx(lam: float) -> float:
    """Asymptotische p-Wert-Approximation fuer KS-Statistik (Numerical Recipes)."""
    if lam <= 0:
        return 1.0
    s = 0.0
    fac = 2.0
    prev = 0.0
    for j in range(1, 101):
        term = fac * math.exp(-2.0 * j * j * lam * lam)
        s += term
        if abs(term) <= 1e-10 * abs(prev) or abs(term) <= 1e-15:
            return min(max(s, 0.0), 1.0)
        fac = -fac
        prev = term
    return 1.0


# -------------------------------------------------------------------- #
# Multi-Norm-CER + Diakritik-Erhaltungsrate
# -------------------------------------------------------------------- #

_HYPHENS = "-­‐‑‒–—"


def normalize_text(text: str, regime: str) -> str:
    """Wendet eines der Normalisierungs-Regimes an. 'raw' = ungetastet."""
    if regime == "raw":
        return text
    if regime not in NORM_REGIMES:
        raise ValueError(f"Unbekanntes Regime: {regime}")
    out = unicodedata.normalize("NFC", text)
    if regime in ("nfc_hyphen", "nfc_hyphen_case"):
        # Alle Bindestrich-Varianten -> ASCII '-', Soft-Hyphen entfernen.
        out = out.replace("­", "")
        out = re.sub(f"[{_HYPHENS[1:]}]", "-", out)
    if regime == "nfc_hyphen_case":
        out = out.casefold()
    return out


try:
    from rapidfuzz.distance import Levenshtein as _RF_Levenshtein  # type: ignore
    _HAS_RAPIDFUZZ = True
except ImportError:  # pragma: no cover -- pure-Python Fallback
    _HAS_RAPIDFUZZ = False


def levenshtein(a: str, b: str) -> int:
    """Levenshtein-Distanz. Nutzt rapidfuzz (C-implementation, ~1000x schneller)
    falls verfuegbar; sonst reines Python (O(n*m), nur fuer Tests/Smoke)."""
    if _HAS_RAPIDFUZZ:
        return int(_RF_Levenshtein.distance(a, b))
    if a == b:
        return 0
    if len(a) < len(b):
        a, b = b, a
    if not b:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        curr = [i] + [0] * len(b)
        for j, cb in enumerate(b, 1):
            cost = 0 if ca == cb else 1
            curr[j] = min(prev[j] + 1, curr[j - 1] + 1, prev[j - 1] + cost)
        prev = curr
    return prev[-1]


def cer(reference: str, hypothesis: str) -> float:
    """Character Error Rate = Levenshtein(ref, hyp) / max(1, len(ref))."""
    if not reference:
        return 0.0 if not hypothesis else 1.0
    return levenshtein(reference, hypothesis) / len(reference)


def cer_under_norms(reference: str, hypothesis: str) -> dict[str, float]:
    """CER unter allen Normalisierungs-Regimes."""
    return {
        regime: cer(normalize_text(reference, regime), normalize_text(hypothesis, regime))
        for regime in NORM_REGIMES
    }


def diacritic_preservation_rate(
    reference: str,
    hypothesis: str,
    language: str,
) -> dict:
    """HCPR-Adaption (Levchenko 2025): Anteil der Referenz-Diakritika, die in der
    Hypothese an *plausibler Stelle* erhalten sind. Wir vergleichen Frequenzen
    pro Zeichen, nicht Position -- das ist eine konservative Adaption (echte
    HCPR braucht Alignment).

    Returns: {expected_count, observed_count, rate_in_0_1}.
              rate = min(observed_count, expected_count) / max(1, expected_count)
    """
    chars = DIACRITICS.get(language, set())
    if not chars:
        return {"expected_count": 0, "observed_count": 0, "rate": None,
                "language": language, "note": "no diacritic set defined"}
    expected = sum(1 for c in reference if c in chars)
    observed = sum(1 for c in hypothesis if c in chars)
    if expected == 0:
        rate = 1.0 if observed == 0 else 0.0
    else:
        rate = min(observed, expected) / expected
    return {
        "expected_count": int(expected),
        "observed_count": int(observed),
        "rate": float(rate),
        "language": language,
    }


# -------------------------------------------------------------------- #
# Aggregation
# -------------------------------------------------------------------- #

@dataclass
class DocCERRecord:
    """Per-Dok-Datensatz fuer Aggregation.

    `doc_cer` ist die kanonische Per-Dok-CER: Volltext-Levenshtein / Ref-Laenge,
    case-sensitiv, OHNE Alignment-Trimming (aus evaluate_tei_vs_tei). Wenn gesetzt,
    gibt `weighted_cer` genau diesen Wert zurueck -- die page_cers/page_ref_chars
    dienen nur noch der Per-Seiten-Outlier-Visualisierung, nicht der Headline.
    Die frueher hier dokumentierte char-gewichtete Per-Page-Aggregation wurde
    aufgegeben (Page-Numbering-Drift, siehe knowledge/cer-methodology.md). Aggregat-Statistik
    bootstraped ueber Per-Dok-Werte (n=Docs), nicht ueber Per-Page-Werte.
    """
    doc_id: str
    page_cers: list[float]            # eine CER pro Seite (regime: nfc_hyphen)
    page_ref_chars: list[int]
    cer_by_regime: dict[str, float]   # 1 Zahl pro Regime (Dok-Mittel)
    metadata: dict                    # language, layout_type, pub_form, ...
    scope_status: str                 # "full" | "partial"
    scope_detail: str | None = None
    doc_cer: float | None = None      # Volltext-CER, case-sensitiv (kein Trimming)
    doc_cer_casefold: float | None = None  # Volltext-CER, case-insensitiv
    doc_cer_fidelity: float | None = None  # nur echte Fehler (Subst.+kleine Indels+Loeschungen)
    doc_scope_insertion_rate: float | None = None  # Pipeline-Mehrtext ggue. Referenz (kein Fehler)

    @property
    def weighted_cer(self) -> float:
        """Gewichtete CER ueber alle Seiten dieses Dokuments. Idempotent."""
        if self.doc_cer is not None:
            return self.doc_cer
        total_chars = sum(self.page_ref_chars)
        if total_chars == 0:
            return 0.0
        total_dist = sum(c * n for c, n in zip(self.page_cers, self.page_ref_chars))
        return total_dist / total_chars


def aggregate_overall(
    records: Sequence[DocCERRecord],
    n_resamples: int,
    seed: int,
    value_fn: Callable[[DocCERRecord], float] | None = None,
) -> dict:
    """Overall-Block: Mean + Median der **Per-Dok-CERs** mit Bootstrap-CI ueber Docs.

    Wir nehmen pro Dok einen einzigen CER-Wert (Default: weighted_cer = case-sensitive
    Volltext-CER). `value_fn` erlaubt eine andere Per-Dok-Groesse (z.B. die case-
    insensitive doc_cer_casefold) ohne Code-Duplikation. Bootstrap zieht n=Docs Werte
    mit Zuruecklegen -- der korrekte Aggregations-Level (Pages innerhalb eines Docs
    sind korreliert).
    """
    if value_fn is None:
        value_fn = lambda r: r.weighted_cer
    doc_cers = [value_fn(r) for r in records if r.page_ref_chars]
    if not doc_cers:
        return {"n_docs": 0, "n_pages": 0, "mean": None, "median": None,
                "ci_method": "bca over docs"}

    # Bootstrap als 1-Block-pro-Doc-Liste (effektiv normaler Bootstrap ueber n=Docs).
    blocks = [[v] for v in doc_cers]
    mean_pt, mean_lo, mean_hi = bca_ci(blocks, np.mean, n_resamples, 0.05, seed)
    med_pt, med_lo, med_hi = bca_ci(blocks, np.median, n_resamples, 0.05, seed + 1)

    arr = np.asarray(doc_cers, dtype=float)
    return {
        "n_docs": int(arr.size),
        "n_pages": int(sum(len(r.page_cers) for r in records)),
        "mean": mean_pt,
        "mean_ci95": [mean_lo, mean_hi],
        "median": med_pt,
        "median_ci95": [med_lo, med_hi],
        "std": float(arr.std(ddof=1)) if arr.size > 1 else 0.0,
        "min": float(arr.min()),
        "max": float(arr.max()),
        "q1": float(np.quantile(arr, 0.25)),
        "q3": float(np.quantile(arr, 0.75)),
        "ci_method": f"BCa over per-doc weighted CERs (n={arr.size}), B={n_resamples}, seed={seed}",
        "unit_of_analysis": "per-doc weighted CER (Levenshtein/ref_chars summed across pages)",
    }


def aggregate_strata(
    records: Sequence[DocCERRecord],
    metadata_field: str,
    n_resamples: int,
    seed: int,
) -> dict[str, dict]:
    """Pro Stratum: Mean + CI ueber Per-Dok-CERs. Strata mit n=1 haben CI = Punkt."""
    groups: dict[str, list[DocCERRecord]] = {}
    for r in records:
        key = str(r.metadata.get(metadata_field, "unknown"))
        groups.setdefault(key, []).append(r)

    out = {}
    for i, (key, recs) in enumerate(sorted(groups.items())):
        doc_cers = [r.weighted_cer for r in recs if r.page_ref_chars]
        if not doc_cers:
            continue
        blocks = [[v] for v in doc_cers]
        mean_pt, mean_lo, mean_hi = bca_ci(blocks, np.mean, n_resamples, 0.05, seed + i)
        med_pt, med_lo, med_hi = bca_ci(blocks, np.median, n_resamples, 0.05, seed + i + 1000)
        out[key] = {
            "n_docs": len(doc_cers),
            "mean": mean_pt,
            "mean_ci95": [mean_lo, mean_hi],
            "median": med_pt,
            "median_ci95": [med_lo, med_hi],
            "doc_ids": [r.doc_id for r in recs],
        }
    return out


def aggregate_multi_norm(records: Sequence[DocCERRecord]) -> dict[str, dict]:
    """Mean + Median je Regime ueber Per-Dok-CERs (kein Bootstrap; deterministisch).

    HINWEIS: Die Eingabe-Texte aus `extract_pages_for_comparison()` sind bereits
    durch `normalize_for_comparison()` (Quotes/Guillemets/Apostroph -> ASCII)
    vorbehandelt. Die Regimes 'raw' / 'nfc' / 'nfc_hyphen' liegen daher bei den
    aktuellen Mistral-Outputs sehr nah beieinander. Der Differenzierungs-Wert
    der Regimes haengt davon ab, dass kuenftig auch ein wirklich roher Text-Pfad
    bereitgestellt wird (z.B. Pre-normalize Hook). Aktuell informativ, nicht
    diagnostisch.
    """
    out = {}
    for regime in NORM_REGIMES:
        vals = [r.cer_by_regime.get(regime) for r in records
                if r.cer_by_regime.get(regime) is not None]
        if not vals:
            continue
        arr = np.asarray(vals, dtype=float)
        out[regime] = {
            "n_docs": int(arr.size),
            "mean": float(arr.mean()),
            "median": float(np.median(arr)),
            "std": float(arr.std(ddof=1)) if arr.size > 1 else 0.0,
        }
    out["_note"] = ("Eingabe-Texte bereits durch normalize_for_comparison "
                    "vorbehandelt; Regime-Differenz daher gering. Echtes raw "
                    "verlangt Pre-normalize-Hook in extract_pages_for_comparison.")
    return out


# -------------------------------------------------------------------- #
# Orchestrator (CLI)
# -------------------------------------------------------------------- #

def _git_sha() -> str:
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            stderr=subprocess.DEVNULL, text=True
        ).strip()
        return out
    except Exception:
        return "unknown"


def _stability_open_block() -> dict:
    """Default-Wert fuer stability bei nicht-gemessenem Status."""
    return {
        "status": "open",
        "n_docs": 0,
        "n_runs": 0,
        "per_doc_std": {},
        "reason": "API-Budget pending user decision; stability not measured "
                  "in this iteration. Methodisch siehe Levchenko 2025 (arXiv:2510.06743).",
    }


def build_statistics(
    records: Sequence[DocCERRecord],
    corpus_metadata: dict[str, dict],
    n_resamples: int = 10_000,
    seed: int = 42,
    include_proxies: bool = False,
) -> dict:
    """Top-Level: produziert das vollstaendige cer_statistics.json-Dict."""
    # Scope-Clean-Subset (nur scope_status == "full") fuer Aggregat-Statistik.
    # Per-Doc-Tabelle zeigt weiterhin alle Records.
    scope_clean = [r for r in records if r.scope_status == "full"]

    # Selektionsbias: Verteilungen Referenz vs. Korpus.
    ref_lang = _count_field(records, "language", from_records=True)
    cor_lang = _count_field(corpus_metadata.values(), "language")
    ref_type = _count_field(records, "layout_type", from_records=True)
    cor_type = _count_field(corpus_metadata.values(), "layout_type")
    ref_form = _count_field(records, "pub_form", from_records=True)
    cor_form = _count_field(corpus_metadata.values(), "pub_form")
    ref_page_counts = [len(r.page_cers) for r in records]
    cor_page_counts = [int(m.get("page_count", 0)) for m in corpus_metadata.values() if m]

    selection_bias = {
        "language": chi_square_categorical(ref_lang, cor_lang),
        "layout_type": chi_square_categorical(ref_type, cor_type),
        "pub_form": chi_square_categorical(ref_form, cor_form),
        "page_count": ks_continuous(ref_page_counts, [c for c in cor_page_counts if c > 0]),
    }
    selection_bias["interpretation"] = _selection_bias_interpretation(selection_bias)

    # Domain-Metrik (Diakritik): nur wo Per-Dok-Texte vorliegen -- hier: aggregate
    # ueber records nach Sprache (records-Metadaten enthalten language).
    diacritic = _aggregate_diacritic(records)

    # Per-doc list for the frontend. 'cer' MUST equal the headline value
    # (r.weighted_cer == doc_cer, case-sensitive full-text CER); cer_casefold is
    # the case-insensitive secondary figure.
    per_doc = []
    for r in records:
        per_doc.append({
            "doc_id": r.doc_id,
            "cer": r.weighted_cer,
            "cer_fidelity": r.doc_cer_fidelity,
            "scope_insertion_rate": r.doc_scope_insertion_rate,
            "cer_casefold": r.doc_cer_casefold,
            "cer_by_regime": r.cer_by_regime,
            "n_ref_chars": int(sum(r.page_ref_chars)),
            "n_pages": len(r.page_cers),
            "language": r.metadata.get("language"),
            "layout_type": r.metadata.get("layout_type"),
            "pub_form": r.metadata.get("pub_form"),
            "scope_status": r.scope_status,
            "scope_detail": r.scope_detail,
            "top_3_error_categories": r.metadata.get("top_3_error_categories", []),
        })

    return {
        "meta": {
            "tool_version": __version__,
            "git_sha": _git_sha(),
            "generated_at": datetime.now(UTC).isoformat(timespec="seconds"),
            "seed": seed,
            "bootstrap_n": n_resamples,
            "ci_method": "BCa blockwise (block=doc)",
            "literature": [
                "Du 2025, arXiv:2511.19794",
                "Levchenko 2025, arXiv:2510.06743",
                "Greif, Griesshaber, Greif 2025, arXiv:2504.00414",
                "Kanerva & Ledins 2025, arXiv:2502.01205",
            ],
        },
        "corpus": {
            "n_total": len(corpus_metadata),
            "n_with_ground_truth": None,  # vom Caller gesetzt
            "n_evaluated": len(records),
            "n_excluded": 0,
            "excluded_doc_ids": [],
            "exclusion_reasons": {},
        },
        "selection_bias": selection_bias,
        "overall": {
            "end_to_end_fidelity": aggregate_overall(
                records, n_resamples, seed + 10,
                value_fn=lambda r: (r.doc_cer_fidelity
                                    if r.doc_cer_fidelity is not None
                                    else r.weighted_cer),
            ),
            "end_to_end": aggregate_overall(scope_clean, n_resamples, seed),
            "end_to_end_casefold": aggregate_overall(
                scope_clean, n_resamples, seed + 25,
                value_fn=lambda r: (r.doc_cer_casefold
                                    if r.doc_cer_casefold is not None
                                    else r.weighted_cer),
            ),
            "end_to_end_all": aggregate_overall(records, n_resamples, seed + 50),
            "metric_note": (
                "end_to_end_fidelity = OCR-/Transkriptionstreue (Substitutionen + kleine "
                "Indels + Loeschungen), grosse Pipeline-Einfuegungen (Mehrtext ggue. der oft "
                "selektiven Referenz) ausgeschlossen -- ueber ALLE Docs, kein Scope-Filter noetig. "
                "end_to_end = volle Volltext-Divergenz (scope-inkl.), case-sensitiv, kein Trimming. "
                "end_to_end_casefold = wie end_to_end, aber case-insensitiv. "
                "Siehe knowledge/specification.md, Abschnitt Quality measurement."
            ),
            "scope_filter_note": (
                f"end_to_end nutzt n={len(scope_clean)} scope-bereinigte Docs "
                f"(scope_status='full', NUR struktureller Seitenzahl-Filter, "
                f"ergebnisunabhaengig); end_to_end_all nutzt n={len(records)} "
                "inkl. scope-mismatched Docs."
            ),
            "ocr_only": {
                "status": "open",
                "reason": "Stage-2-OCR-Output nicht in dieser Iteration evaluiert; "
                          "End-to-End beinhaltet Stage 2 + Stage 6 zusammen.",
            },
        },
        "strata": {
            "language": aggregate_strata(scope_clean, "language", n_resamples, seed + 100),
            "layout_type": aggregate_strata(scope_clean, "layout_type", n_resamples, seed + 200),
            "pub_form": aggregate_strata(scope_clean, "pub_form", n_resamples, seed + 300),
        },
        "multi_norm": aggregate_multi_norm(scope_clean),
        "paired_test": {
            "status": "open",
            "reason": "Pre-Pipeline-OCR-Daten in dieser Iteration nicht eingelesen.",
        },
        "stability": _stability_open_block(),
        "domain_metrics": {"diacritic_preservation_rate": diacritic},
        "error_categories": _aggregate_error_categories(records),
        "per_doc": per_doc,
        "comparison_lit": _comparison_lit_2025_plus(),
        "proxies": {
            "status": "open" if not include_proxies else "todo_b_prime",
            "reason": "Proxy-Framework (Track B') folgt in eigener Iteration.",
        },
        "drift_check": _drift_check_against_diagnostik(records),
    }


def _drift_check_against_diagnostik(records: Sequence[DocCERRecord]) -> dict:
    """Vergleicht aktuelle Per-Dok-CERs gegen `docs/data/diagnostik_ocr.json`
    (Snapshot vom 2026-03-29). Wenn die Pipeline-TEIs in der Zwischenzeit
    re-generiert wurden, divergieren die Werte -- das ist eine wichtige
    Beobachtung, kein Bug.
    """
    snapshot_path = Path("docs/data/diagnostik_ocr.json")
    if not snapshot_path.exists():
        return {"status": "no_snapshot",
                "reason": "docs/data/diagnostik_ocr.json nicht gefunden."}
    try:
        with open(snapshot_path, encoding="utf-8") as f:
            snap = json.load(f)
    except Exception as e:
        return {"status": "snapshot_read_error", "reason": str(e)}

    snap_per_doc = snap.get("per_doc", {}) if isinstance(snap, dict) else {}
    snap_generated = snap.get("generated", "unknown")

    diffs = []
    for r in records:
        old = snap_per_doc.get(r.doc_id, {})
        if not isinstance(old, dict) or "cer" not in old:
            continue
        delta = r.weighted_cer - float(old["cer"])
        if abs(delta) > 0.05:  # > 5pp Drift
            diffs.append({
                "doc_id": r.doc_id,
                "old_cer": float(old["cer"]),
                "new_cer": r.weighted_cer,
                "delta_pp": delta * 100,
                "old_scope_status": old.get("scope_status", "unknown"),
                "new_scope_status": r.scope_status,
            })

    drift_severity = "stale" if len(diffs) > 5 else (
        "minor" if diffs else "in_sync"
    )

    return {
        "status": drift_severity,
        "snapshot_generated": snap_generated,
        "snapshot_path": str(snapshot_path),
        "n_docs_diverged": len(diffs),
        "threshold_pp": 5.0,
        "diverged_docs": sorted(diffs, key=lambda x: -abs(x["delta_pp"])),
        "interpretation": (
            f"{len(diffs)} Docs weichen >5pp vom Snapshot ab. "
            f"Wenn 'stale': Pipeline-TEIs wurden seit {snap_generated} "
            "re-generiert; Snapshot-Werte sind nicht mehr gueltig."
        ),
    }


def _count_field(items: Iterable, field: str, *, from_records: bool = False) -> dict[str, int]:
    """Zaehlt Auftreten eines Metadaten-Felds. items kann ueber records ODER ueber
    corpus-metadata-dict-values laufen."""
    out: dict[str, int] = {}
    for it in items:
        if from_records:
            val = str(it.metadata.get(field, "unknown"))
        else:
            val = str(it.get(field, "unknown")) if it else "unknown"
        out[val] = out.get(val, 0) + 1
    return out


def _selection_bias_interpretation(sb: dict) -> str:
    """1-2-Satz-Klartext fuer das Limitations-Panel."""
    flagged = [k for k, v in sb.items()
               if isinstance(v, dict) and v.get("comparable") is False]
    if not flagged:
        return ("Verteilung von Sprache, Layout-Typ, Pub-Form und Seitenzahl "
                "im Referenz-Subset (n=25) ist statistisch nicht von der "
                "Gesamtkorpus-Verteilung (n=285) zu unterscheiden (alle p > 0.05). "
                "Generalisierung der Ergebnisse auf den Gesamtkorpus bleibt eine "
                "Annahme, ist aber nicht durch ersichtliche Stichproben-Verzerrung gefaehrdet.")
    return (f"Referenz-Subset zeigt signifikante Abweichung vom Gesamtkorpus in: "
            f"{', '.join(flagged)}. Korpus-weite Aussagen aus n=19 sind dadurch "
            f"zusaetzlich limitiert.")


def _aggregate_diacritic(records: Sequence[DocCERRecord]) -> dict:
    """Aggregiert Diakritik-Erhaltungsrate pro Sprache aus den Records."""
    by_lang: dict[str, list[float]] = {}
    for r in records:
        lang = r.metadata.get("language", "unknown")
        rate = r.metadata.get("diacritic_rate")
        if rate is None:
            continue
        by_lang.setdefault(lang, []).append(rate)
    out = {}
    for lang, rates in by_lang.items():
        arr = np.asarray(rates, dtype=float)
        out[lang] = {
            "n_docs": int(arr.size),
            "mean_rate": float(arr.mean()),
            "median_rate": float(np.median(arr)),
            "min_rate": float(arr.min()),
        }
    return out


def _aggregate_error_categories(records: Sequence[DocCERRecord]) -> dict:
    """Summiert Fehlerkategorien-Counts ueber alle Records."""
    totals: dict[str, dict[str, float]] = {}
    for r in records:
        cats = r.metadata.get("error_categories", {}) or {}
        for cat, vals in cats.items():
            t = totals.setdefault(cat, {"count": 0, "char_distance": 0.0})
            t["count"] += int(vals.get("count", 0))
            t["char_distance"] += float(vals.get("char_distance", 0))
    return totals


def _comparison_lit_2025_plus() -> list[dict]:
    """Hardcoded Literatur-Vergleich, ausschliesslich 2025+ (User-Constraint)."""
    return [
        {"source": "Greif, Griesshaber, Greif 2025 (arXiv:2504.00414)",
         "method": "Transkribus Print M1 + Gemini 2.0 Flash multimodal post-correction",
         "language": "deu (ueberwiegend Fraktur)", "cer": 0.0084,
         "comparable": "partial",
         "caveat": "Deutschsprachige Adressbuecher, ueberwiegend Fraktur, anderes Korpus, multimodale Post-Korrektur."},
        {"source": "Greif, Griesshaber, Greif 2025 (arXiv:2504.00414)",
         "method": "Gemini 2.0 Flash zero-shot",
         "language": "deu (ueberwiegend Fraktur)", "cer": 0.0127,
         "comparable": "partial",
         "caveat": "Deutschsprachige Adressbuecher, ueberwiegend Fraktur, ohne Post-Korrektur."},
        {"source": "Levchenko 2025 (arXiv:2510.06743)",
         "method": "Gemini 2.5 Pro",
         "language": "rus 18. Jh.", "cer": 0.0336,
         "comparable": False,
         "caveat": "Russisch, 18. Jh. Civil Font; nicht like-for-like."},
        {"source": "Levchenko 2025 (arXiv:2510.06743)",
         "method": "GPT-4o",
         "language": "rus 18. Jh.", "cer": 0.0923,
         "comparable": False,
         "caveat": "Russisch."},
    ]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--bootstrap-n", type=int, default=10_000)
    parser.add_argument("--include-proxies", action="store_true",
                        help="Proxy-Framework (Track B') aktivieren -- noch nicht implementiert.")
    parser.add_argument("--stability-runs", type=int, default=0,
                        help="Anzahl Re-Runs fuer Stabilitaets-Pilot. 0 = nicht messen.")
    parser.add_argument("--out", type=Path,
                        default=Path("docs/data/cer_statistics.json"))
    parser.add_argument("--dry-run", action="store_true",
                        help="Lese alles, schreibe aber kein JSON (CI-Modus).")
    args = parser.parse_args(argv)

    # Lazy Import: nur fuer den Run noetig, nicht fuer die Tests.
    from scripts.eval.cer_statistics_runner import collect_records  # type: ignore

    records, corpus_metadata, n_with_gt, exclusions = collect_records()
    data = build_statistics(
        records, corpus_metadata,
        n_resamples=args.bootstrap_n,
        seed=args.seed,
        include_proxies=args.include_proxies,
    )
    data["corpus"]["n_with_ground_truth"] = n_with_gt
    data["corpus"]["n_excluded"] = len(exclusions)
    data["corpus"]["excluded_doc_ids"] = sorted(exclusions.keys())
    data["corpus"]["exclusion_reasons"] = exclusions

    if args.dry_run:
        print(json.dumps({"meta": data["meta"], "overall": data["overall"]},
                         indent=2, ensure_ascii=False))
        return 0

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"Wrote {args.out} ({args.out.stat().st_size:,} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
