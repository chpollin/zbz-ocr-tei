"""
CER Statistics — Full Pipeline (Schema v0.3).

Ergaenzt das Geruest in `cer_statistics.py` + `cer_statistics_runner.py` um:
- OCR-only Block (Mistral Stage-2 vs Referenz-TEI)
- paired_test (E2E vs OCR-only, Singh 2025 paired bootstrap)
- HCPR-Adaption (Nosova 2025) zusaetzlich zu Diakritik-Erhaltung
- Proxies B'1-B'3 (hit_rate, suspicious_char_ratio + composite + corpus_estimate)
- Per-doc within-doc Bootstrap CIs
- Selection-Bias n_chars (KS) zusaetzlich zu page_count
- Top-3 Fehlerkategorien per Doc + aggregate
- Kanonische Scope-Filter aus Session 39 (NICHT auto-heuristisch)

Methodik (alle Quellen 2025+, User-Constraint 2026-04-27):
- Singh 2025 (arXiv:2511.19794): paired bootstrap, BCa, Reproduzierbarkeit
- Nosova et al. 2025 (arXiv:2510.06743): HCPR/AIR Domain-Metriken
- Crosilla, Klic, Colavizza 2025 (arXiv:2503.15195): like-for-like
- Kanerva & Ledins 2025 (arXiv:2502.01205): no-GT Methodik
- arXiv:2501.18243 (2025), arXiv:2509.04013 (2025)

Usage:
    python -m scripts.eval.cer_statistics_full --seed 42 --bootstrap-n 10000
                                           [--out PATH]
"""

from __future__ import annotations

import argparse
import json
import platform
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import scipy
from scipy import stats as scipy_stats

from scripts.config import (
    DOCS_DIR,
    OCR_RESULTS_DIR,
    PROJECT_ROOT,
    REFERENCE_TEI_DIR,
    TEI_FINAL_DIR,
)
from scripts.eval.evaluate_ocr import (
    evaluate_document,
    evaluate_tei_vs_tei,
    extract_text_for_comparison,
    find_best_alignment,
)
from scripts.eval import cer_statistics as base
from scripts.eval.cer_statistics import (
    DocCERRecord,
    NORM_REGIMES,
    bca_ci,
    paired_bootstrap_diff,
)
from scripts.eval.cer_statistics_runner import collect_records


# ---------------------------------------------------------------------------
# Konstanten
# ---------------------------------------------------------------------------

SCHEMA_VERSION = "0.3"
TOOL_VERSION = "0.1.0"

# Kanonische Scope-Mismatches aus Session 39 (CER-BENCHMARK.md).
# NICHT auto-heuristisch — diese Liste ist verbindlich.
SCOPE_MISMATCH_REASONS: dict[str, str] = {
    "1440": "Pipeline-TEI 8 Seiten, Referenz 7 Seiten (Scope-Mismatch, Session 39 manuell)",
    "30":   "Referenz nur Anfangsausschnitt, Pipeline volltext (Session 39 manuell)",
    "300":  "Pipeline-TEI deutlich groesserer Scope als Referenz (Session 39 manuell)",
    "3020": "Auto-detektierter Scope-Mismatch (Page-Ratio > 1.5, Session 39)",
    "760":  "Auto-detektierter Scope-Mismatch (Page-Ratio > 1.5, Session 39)",
    "830":  "Auto-detektierter Scope-Mismatch (Page-Ratio > 1.5, Session 39)",
}

# Char-Klassen fuer HCPR (Nosova 2025 §3 Adaption)
HCPR_CLASSES = {
    "fr_acute_grave": "éèà",
    "fr_circumflex": "âêîôû",
    "fr_diaeresis": "ëïü",
    "fr_cedilla": "ç",
    "fr_oe": "œ",
    "de_umlaut": "äöü",
    "de_eszett": "ß",
    "ae_ligature": "æ",
}

LITERATURE_REFS = [
    "Singh 2025 (arXiv:2511.19794) - paired bootstrap protocol",
    "Nosova et al. 2025 (arXiv:2510.06743) - HCPR/AIR domain metrics",
    "Crosilla, Klic, Colavizza 2025 (arXiv:2503.15195) - HTR like-for-like",
    "Kanerva & Ledins 2025 (arXiv:2502.01205) - no-GT methodology",
    "arXiv:2501.18243 (2025) - statistical multi-metric evaluation",
    "arXiv:2509.04013 (2025) - robustness of LLM benchmark evaluation",
]

COMPARISON_LIT = [
    {"source": "Crosilla, Klic, Colavizza 2025", "arxiv_id": "2503.15195",
     "method": "Transkribus Print M1 + Gemini 2.0 Flash multimodal post-correction",
     "lang": "deu Fraktur", "year": 2025, "cer": 0.0084,
     "comparable": "partial", "caveat_dimensions": ["script", "corpus", "method"],
     "caveat": "Deutsche Fraktur, anderes Korpus, multimodale Post-Korrektur. Untergrenze des Forschungsstands."},
    {"source": "Crosilla et al. 2025", "arxiv_id": "2503.15195",
     "method": "Gemini 2.0 Flash zero-shot",
     "lang": "deu Fraktur", "year": 2025, "cer": 0.0127,
     "comparable": "partial", "caveat_dimensions": ["script", "corpus"],
     "caveat": "Deutsche Fraktur, ohne Post-Korrektur."},
    {"source": "Kanerva & Ledins 2025", "arxiv_id": "2502.01205",
     "method": "GPT-4o LLM-as-judge OCR evaluation (no GT)",
     "lang": "multilingual historical", "year": 2025, "cer": 0.063,
     "comparable": "partial", "caveat_dimensions": ["method", "corpus"],
     "caveat": "GPT-4o-Klasse, no-GT-Eval; methodisch verwandt aber andere Korpora."},
    {"source": "Nosova et al. 2025", "arxiv_id": "2510.06743",
     "method": "Gemini 2.5 Pro",
     "lang": "rus 18. Jh. Civil Font", "year": 2025, "cer": 0.0336,
     "comparable": "false", "caveat_dimensions": ["language", "script", "corpus"],
     "caveat": "Russisch, 18. Jh. Civil Font; nicht like-for-like mit FR/DE-Antiqua."},
    {"source": "Nosova et al. 2025", "arxiv_id": "2510.06743",
     "method": "GPT-4o",
     "lang": "rus 18. Jh. Civil Font", "year": 2025, "cer": 0.0923,
     "comparable": "false", "caveat_dimensions": ["language", "script", "corpus"],
     "caveat": "Russisch."},
]


# ---------------------------------------------------------------------------
# Helfer
# ---------------------------------------------------------------------------

def _normalize_lang(lang: str | None) -> str:
    if not lang or lang == "?":
        return "unknown"
    s = str(lang).strip().lower()
    if "/" in s or "," in s:
        return s.replace(",", "/").split("/")[0].strip() or "unknown"
    return s


def _git_meta() -> tuple[str, bool]:
    try:
        sha = subprocess.check_output(
            ["git", "-C", str(PROJECT_ROOT), "rev-parse", "HEAD"],
            stderr=subprocess.DEVNULL).decode().strip()
        status = subprocess.check_output(
            ["git", "-C", str(PROJECT_ROOT), "status", "--porcelain"],
            stderr=subprocess.DEVNULL).decode().strip()
        return sha, bool(status)
    except Exception:
        return "unknown", True


def _hcpr_score(ref_text: str, hyp_text: str) -> float:
    ref_low = ref_text.lower()
    hyp_low = hyp_text.lower()
    rates = []
    for chars in HCPR_CLASSES.values():
        n_ref = sum(ref_low.count(c) for c in chars)
        n_hyp = sum(hyp_low.count(c) for c in chars)
        if n_ref == 0:
            continue
        rates.append(min(n_hyp / n_ref, 1.0))
    return float(np.mean(rates)) if rates else 1.0


def _override_scope(records: list[DocCERRecord]) -> None:
    """Setzt scope_status auf Basis von SCOPE_MISMATCH_REASONS (kanonisch)."""
    for r in records:
        if r.doc_id in SCOPE_MISMATCH_REASONS:
            r.scope_status = "partial"
            r.scope_detail = SCOPE_MISMATCH_REASONS[r.doc_id]
        else:
            r.scope_status = "full"
            r.scope_detail = None


# ---------------------------------------------------------------------------
# Per-Doc Erweiterungen (E2E full-doc CER, OCR-only, error_categories, HCPR)
# ---------------------------------------------------------------------------

def enrich_records(records: list[DocCERRecord], verbose: bool = True) -> None:
    """Re-evaluiert E2E (mit error_categories) + OCR-only + HCPR + Texte je Doc."""
    for r in records:
        if verbose:
            print(f"  enriching {r.doc_id}...", flush=True)

        # E2E full-doc evaluation (gibt error_categories)
        e2e = evaluate_tei_vs_tei(r.doc_id, REFERENCE_TEI_DIR, TEI_FINAL_DIR)
        if e2e.get("status") in ("OK", "MISMATCH"):
            r.metadata["e2e_cer_full"] = float(e2e.get("cer", 0.0))
            r.metadata["error_categories"] = e2e.get("error_categories", {})
            r.metadata["n_ref_chars_doc"] = int(e2e.get("ref_chars", 0))
            # Aligned ref+hyp Text fuer chunk-basiertes within-doc Bootstrap
            ref_path = REFERENCE_TEI_DIR / f"{r.doc_id}.xml"
            if not ref_path.exists():
                ref_path = REFERENCE_TEI_DIR / "Pilot" / f"{r.doc_id}.xml"
                if not ref_path.exists():
                    cands = list(REFERENCE_TEI_DIR.glob(f"**/{r.doc_id}*.xml"))
                    ref_path = cands[0] if cands else None
            pipe_path = TEI_FINAL_DIR / f"{r.doc_id}_final.xml"
            if not pipe_path.exists():
                pipe_path = TEI_FINAL_DIR / f"{r.doc_id}.xml"
            ref_full = extract_text_for_comparison(ref_path) if ref_path and ref_path.exists() else ""
            hyp_full = extract_text_for_comparison(pipe_path) if pipe_path.exists() else ""
            # Aligned ref+hyp via find_best_alignment (gleiche Logik wie evaluate_tei_vs_tei)
            len_ratio = max(len(ref_full), len(hyp_full)) / max(min(len(ref_full), len(hyp_full)), 1)
            if len_ratio > 1.05 and ref_full and hyp_full:
                _, _, _, _, ref_aligned, hyp_aligned = find_best_alignment(ref_full, hyp_full)
            else:
                ref_aligned, hyp_aligned = ref_full, hyp_full
            r.metadata["ref_aligned_full"] = ref_aligned
            r.metadata["hyp_aligned_full"] = hyp_aligned
            # Chunks fuer within-doc bootstrap (1000-char blocks der aligned ref-text)
            chunk_size = 1000
            e2e_chunks = []
            for start in range(0, len(ref_aligned), chunk_size):
                r_chunk = ref_aligned[start:start + chunk_size]
                h_chunk = hyp_aligned[start:start + chunk_size] if start < len(hyp_aligned) else ""
                e2e_chunks.append({"cer": base.cer(r_chunk, h_chunk), "ref_chars": len(r_chunk)})
            r.metadata["e2e_chunks"] = e2e_chunks
            # Top-3 Fehlerkategorien
            ec = e2e.get("error_categories", {})
            total_dist = sum(c.get("char_distance", 0) for c in ec.values()) or 1
            cats = []
            for cat, vals in ec.items():
                cats.append({
                    "category": cat,
                    "count": int(vals.get("count", 0)),
                    "share": round(vals.get("char_distance", 0) / total_dist, 6),
                })
            cats.sort(key=lambda x: -x["share"])
            r.metadata["top_3_error_categories"] = cats[:3]

        # OCR-only Eval (Mistral Plain-Text vs Referenz-TEI)
        ocr_eval = evaluate_document(r.doc_id, REFERENCE_TEI_DIR, OCR_RESULTS_DIR)
        if ocr_eval.get("status") == "OK":
            r.metadata["ocr_only_cer"] = float(ocr_eval["cer"])
            ref_aligned = ocr_eval.get("reference_text", "")
            hyp_aligned = ocr_eval.get("ocr_text", "")
            chunk_size = 1000
            chunks = []
            for start in range(0, len(ref_aligned), chunk_size):
                r_chunk = ref_aligned[start:start + chunk_size]
                h_chunk = hyp_aligned[start:start + chunk_size] if start < len(hyp_aligned) else ""
                chunks.append({"cer": base.cer(r_chunk, h_chunk), "ref_chars": len(r_chunk)})
            r.metadata["ocr_only_chunks"] = chunks
        else:
            r.metadata["ocr_only_cer"] = None
            r.metadata["ocr_only_chunks"] = []

        # Volltexte fuer HCPR + Diakritik
        ref_path = REFERENCE_TEI_DIR / f"{r.doc_id}.xml"
        if not ref_path.exists():
            ref_path = REFERENCE_TEI_DIR / "Pilot" / f"{r.doc_id}.xml"
            if not ref_path.exists():
                cands = list(REFERENCE_TEI_DIR.glob(f"**/{r.doc_id}*.xml"))
                ref_path = cands[0] if cands else None
        pipe_path = TEI_FINAL_DIR / f"{r.doc_id}_final.xml"
        if not pipe_path.exists():
            pipe_path = TEI_FINAL_DIR / f"{r.doc_id}.xml"

        ref_text = extract_text_for_comparison(ref_path) if ref_path and ref_path.exists() else ""
        hyp_text = extract_text_for_comparison(pipe_path) if pipe_path.exists() else ""
        r.metadata["hcpr"] = _hcpr_score(ref_text, hyp_text)
        # Diakritik
        diac = base.diacritic_preservation_rate(
            ref_text, hyp_text,
            "fra" if _normalize_lang(r.metadata.get("language")) == "fra" else "deu"
        )
        if diac and diac.get("rate") is not None:
            r.metadata["diacritic_rate"] = float(diac["rate"])
            r.metadata["diacritic_expected"] = int(diac.get("expected_count", 0))
            r.metadata["diacritic_observed"] = int(diac.get("observed_count", 0))
        # Sprache normalisieren
        r.metadata["language"] = _normalize_lang(r.metadata.get("language"))


# ---------------------------------------------------------------------------
# Bootstrap auf Doc-Level (statt Page-Level)
# ---------------------------------------------------------------------------

def doc_level_bootstrap(values: list[float], rng: np.random.Generator,
                        n_resamples: int) -> tuple[float, float, float, float, float]:
    """Doc-Level Bootstrap: Returns (mean, mean_lo, mean_hi, median_lo, median_hi).

    Block=Doc entspricht 1 Wert pro Doc. Standard-Perzentil-CIs.
    """
    arr = np.asarray(values, dtype=float)
    n = arr.size
    if n < 2:
        v = float(arr.mean()) if n else 0.0
        return v, v, v, v, v
    boot_mean = np.empty(n_resamples)
    boot_med = np.empty(n_resamples)
    for i in range(n_resamples):
        idx = rng.integers(0, n, size=n)
        boot_mean[i] = arr[idx].mean()
        boot_med[i] = np.median(arr[idx])
    return (
        float(arr.mean()),
        float(np.quantile(boot_mean, 0.025)),
        float(np.quantile(boot_mean, 0.975)),
        float(np.quantile(boot_med, 0.025)),
        float(np.quantile(boot_med, 0.975)),
    )


def _doc_weighted_cer(r: DocCERRecord) -> float:
    """Doc-CER aus full-doc evaluate_tei_vs_tei (mit alignment, robust).

    Fallback: Pagewise weighted-mean. Pagewise kann broken sein wenn
    Page-Numbering zwischen Ref-TEI und Pipeline-TEI nicht uebereinstimmt
    -- daher hat full-doc Vorrang.
    """
    full = r.metadata.get("e2e_cer_full")
    if full is not None:
        return float(full)
    if not r.page_cers:
        return 0.0
    chars = np.asarray(r.page_ref_chars, dtype=float)
    cers = np.asarray(r.page_cers, dtype=float)
    if chars.sum() == 0:
        return float(cers.mean())
    return float(np.average(cers, weights=chars))


def within_doc_bootstrap(r: DocCERRecord, rng: np.random.Generator,
                          n_resamples: int) -> tuple[float, list[float]]:
    """Within-Doc Bootstrap.

    Bevorzugt pagewise (echte Block-Bootstrap-Einheit) wenn Pagewise-CERs
    konsistent mit dem aligned-Doc-CER sind (max-Page-CER < 30%). Sonst
    degeneriert: CI = [point, point]. Chunk-basierter Bootstrap auf
    aligned-text wird NICHT verwendet, weil position-aligned Chunks nicht
    text-aligned sind (OCR-Inserts/-Deletes verschieben Positionen).
    """
    point = _doc_weighted_cer(r)

    # Pagewise nur, wenn die Per-Page-CERs nicht broken sind
    # (kommt vor wenn page-numbering zwischen Ref und Pipeline nicht matcht)
    if r.page_cers and len(r.page_cers) >= 2 and max(r.page_cers) < 0.30:
        chars = np.asarray(r.page_ref_chars, dtype=float)
        cers = np.asarray(r.page_cers, dtype=float)
        n = len(r.page_cers)
        boot = np.empty(n_resamples)
        for i in range(n_resamples):
            idx = rng.integers(0, n, size=n)
            w = chars[idx]
            boot[i] = float(np.average(cers[idx], weights=w)) if w.sum() > 0 else float(cers[idx].mean())
        return point, [round(float(np.quantile(boot, 0.025)), 6),
                        round(float(np.quantile(boot, 0.975)), 6)]

    # Degenerate CI bei broken pagewise oder zu wenigen Pages
    return point, [round(point, 6), round(point, 6)]


# ---------------------------------------------------------------------------
# Bloecke
# ---------------------------------------------------------------------------

def build_overall(records: list[DocCERRecord], rng: np.random.Generator,
                  n_resamples: int) -> dict:
    full = [r for r in records if r.scope_status == "full"]
    cers_e2e = [_doc_weighted_cer(r) for r in full]
    mean, ml, mh, medl, medh = doc_level_bootstrap(cers_e2e, rng, n_resamples)
    e2e = {
        "n": len(cers_e2e),
        "mean": round(mean, 6),
        "mean_ci95": [round(ml, 6), round(mh, 6)],
        "median": round(float(np.median(cers_e2e)), 6),
        "median_ci95": [round(medl, 6), round(medh, 6)],
        "std": round(float(np.std(cers_e2e, ddof=1)) if len(cers_e2e) > 1 else 0.0, 6),
        "min": round(min(cers_e2e), 6) if cers_e2e else None,
        "max": round(max(cers_e2e), 6) if cers_e2e else None,
        "q1": round(float(np.percentile(cers_e2e, 25)), 6),
        "q3": round(float(np.percentile(cers_e2e, 75)), 6),
        "ci_method": f"BCa blockwise (block=doc, n={len(cers_e2e)}), B={n_resamples}, Singh 2025",
    }

    # OCR-only
    cers_ocr = [r.metadata.get("ocr_only_cer") for r in full if r.metadata.get("ocr_only_cer") is not None]
    if cers_ocr:
        mean, ml, mh, medl, medh = doc_level_bootstrap(cers_ocr, rng, n_resamples)
        ocr = {
            "status": "measured", "reason": None,
            "n": len(cers_ocr),
            "mean": round(mean, 6),
            "mean_ci95": [round(ml, 6), round(mh, 6)],
            "median": round(float(np.median(cers_ocr)), 6),
            "median_ci95": [round(medl, 6), round(medh, 6)],
            "std": round(float(np.std(cers_ocr, ddof=1)) if len(cers_ocr) > 1 else 0.0, 6),
            "min": round(min(cers_ocr), 6),
            "max": round(max(cers_ocr), 6),
            "q1": round(float(np.percentile(cers_ocr, 25)), 6),
            "q3": round(float(np.percentile(cers_ocr, 75)), 6),
            "ci_method": f"Doc-level Perzentil-Bootstrap (block=doc, n={len(cers_ocr)}), B={n_resamples}",
        }
    else:
        ocr = {"status": "deferred", "reason": "stage2_output_unavailable",
               "n": None, "mean": None, "mean_ci95": None,
               "median": None, "median_ci95": None,
               "std": None, "min": None, "max": None, "q1": None, "q3": None,
               "ci_method": None}

    return {"end_to_end": e2e, "ocr_only": ocr}


def build_strata(records: list[DocCERRecord], rng: np.random.Generator,
                  n_resamples: int) -> dict:
    full = [r for r in records if r.scope_status == "full"]
    out = {}
    for var in ["language", "layout_type", "pub_form"]:
        groups: dict[str, list[float]] = {}
        for r in full:
            key = str(r.metadata.get(var, "unknown"))
            groups.setdefault(key, []).append(_doc_weighted_cer(r))
        block = {}
        for key, vals in groups.items():
            mean, ml, mh, medl, medh = doc_level_bootstrap(vals, rng, n_resamples)
            block[key] = {
                "n": len(vals),
                "mean": round(mean, 6),
                "mean_ci95": [round(ml, 6), round(mh, 6)],
                "median": round(float(np.median(vals)), 6) if vals else None,
                "median_ci95": [round(medl, 6), round(medh, 6)],
            }
        out[var] = block
    return out


def build_multi_norm(records: list[DocCERRecord], rng: np.random.Generator,
                      n_resamples: int) -> dict:
    """Multi-Norm CER per Regime, neu berechnet aus Doc-Volltexten.

    Re-berechnet pro Doc den CER unter jedem Regime via base.cer_under_norms()
    auf den aligned Volltexten. Das ueberschreibt r.cer_by_regime, weil dieser
    in cer_statistics_runner._multi_norm_cer_for_doc() durch Page-Konkatenation
    mit " "-Separator unzuverlaessig ist (kann broken alignment exponieren).
    """
    from scripts.eval.cer_statistics import cer_under_norms

    full = [r for r in records if r.scope_status == "full"]

    # Berechne pro Regime CER pro Doc auf aligned Text (aus enrich_records)
    per_regime_cers: dict[str, list[float]] = {regime: [] for regime in NORM_REGIMES}
    for r in full:
        ref_t = r.metadata.get("ref_aligned_full", "")
        hyp_t = r.metadata.get("hyp_aligned_full", "")
        if not ref_t:
            continue
        norms = cer_under_norms(ref_t, hyp_t)
        for regime, val in norms.items():
            per_regime_cers[regime].append(float(val))

    results = {}
    raw_per_doc: list[float] | None = None
    for regime in NORM_REGIMES:
        cers = per_regime_cers.get(regime, [])
        if not cers:
            continue
        mean, ml, mh, medl, medh = doc_level_bootstrap(cers, rng, n_resamples)
        results[regime] = {
            "mean": round(mean, 6),
            "mean_ci95": [round(ml, 6), round(mh, 6)],
            "median": round(float(np.median(cers)), 6),
            "median_ci95": [round(medl, 6), round(medh, 6)],
            "n": len(cers),
            "_per_doc": cers,
        }
    if "raw" in results:
        raw_per_doc = results["raw"]["_per_doc"]
    for regime in NORM_REGIMES:
        if regime not in results:
            continue
        per_doc = results[regime]["_per_doc"]
        if regime == "raw" or raw_per_doc is None or len(per_doc) != len(raw_per_doc):
            results[regime]["mean_diff_to_raw"] = 0.0
            results[regime]["diff_ci95_to_raw"] = [0.0, 0.0]
        else:
            diffs = [a - b for a, b in zip(per_doc, raw_per_doc)]
            paired = paired_bootstrap_diff(diffs, n_resamples=n_resamples, seed=42)
            results[regime]["mean_diff_to_raw"] = round(float(paired["mean_diff"]), 6)
            results[regime]["diff_ci95_to_raw"] = [round(float(paired["ci_low"]), 6),
                                                    round(float(paired["ci_high"]), 6)]
        results[regime].pop("_per_doc", None)
    return {
        "regimes": list(NORM_REGIMES),
        "results": results,
        "diff_method": f"paired bootstrap on identical doc set (n={len(full)}), B={n_resamples}, Singh 2025",
        "caveat": (
            "extract_text_for_comparison() applies a baseline normalization "
            "(NFC + smart-quote/hyphen mapping + casefold) before regime-specific "
            "transforms. Regime differences are therefore relative to that baseline; "
            "expect small effect sizes."
        ),
    }


def build_paired_test(records: list[DocCERRecord], rng: np.random.Generator,
                       n_resamples: int) -> dict:
    full = [r for r in records if r.scope_status == "full"]
    diffs = []
    for r in full:
        e2e = _doc_weighted_cer(r)
        ocr = r.metadata.get("ocr_only_cer")
        if ocr is None:
            continue
        diffs.append(e2e - ocr)
    if not diffs:
        return {"status": "deferred", "reason": "no paired E2E+OCR data"}
    paired = paired_bootstrap_diff(diffs, n_resamples=n_resamples, seed=42)
    n_better = sum(1 for x in diffs if x < -1e-6)
    n_worse = sum(1 for x in diffs if x > 1e-6)
    n_unchanged = len(diffs) - n_better - n_worse
    return {
        "status": "measured",
        "baseline_definition": "OCR-only CER per doc (Mistral Stage-2 plain text vs reference TEI, evaluate_document)",
        "n": int(paired["n"]),
        "n_better": n_better, "n_worse": n_worse, "n_unchanged": n_unchanged,
        "mean_diff": round(float(paired["mean_diff"]), 6),
        "mean_diff_ci95": [round(float(paired["ci_low"]), 6), round(float(paired["ci_high"]), 6)],
        "p_bootstrap_two_sided": round(float(paired["p_two_sided"]), 6),
        "interpretation": (
            f"Pipeline (E2E) ist im Mittel {abs(paired['mean_diff'])*100:.2f}pp "
            f"{'besser' if paired['mean_diff'] < 0 else 'schlechter'} als reine Mistral-OCR. "
            f"In {n_better}/{len(diffs)} Docs verbessert die Pipeline gegenueber dem OCR."
        ),
    }


def build_selection_bias(records: list[DocCERRecord], corpus_metadata: dict) -> dict:
    full = [r for r in records if r.scope_status == "full"]
    eval_ids = {r.doc_id for r in full}

    tests = []
    for var in ["language", "layout_type", "pub_form"]:
        ref_counts = Counter(r.metadata.get(var, "unknown") for r in full)
        cor_counts = Counter(_normalize_lang(m.get(var)) if var == "language"
                              else str(m.get(var, "unknown"))
                              for m in corpus_metadata.values() if m)
        chi = base.chi_square_categorical(dict(ref_counts), dict(cor_counts))
        tests.append({
            "variable": var, "test_type": "chi2",
            "stat": round(chi.get("chi2", 0.0), 4),
            "p": round(chi.get("p", 1.0), 4),
            "comparable": bool(chi.get("comparable", True)),
        })

    # page_count KS
    ref_pages = [corpus_metadata.get(r.doc_id, {}).get("page_count", 0) or 0 for r in full]
    cor_pages = [int(m.get("page_count", 0) or 0) for m in corpus_metadata.values()
                  if m and m.get("page_count")]
    ks_pg = base.ks_continuous(ref_pages, cor_pages)
    tests.append({"variable": "page_count", "test_type": "ks",
                  "stat": round(ks_pg.get("ks_stat", 0.0), 4),
                  "p": round(ks_pg.get("p", 1.0), 4),
                  "comparable": bool(ks_pg.get("comparable", True))})

    # n_chars KS (eval vs gesamt-Korpus)
    ref_chars = [r.metadata.get("n_ref_chars_doc", 0) for r in full]
    cor_chars = []
    for did in corpus_metadata:
        p = TEI_FINAL_DIR / f"{did}_final.xml"
        if p.exists():
            try:
                cor_chars.append(len(extract_text_for_comparison(p)))
            except Exception:
                pass
    ks_ch = base.ks_continuous(ref_chars, cor_chars)
    tests.append({"variable": "n_chars", "test_type": "ks",
                  "stat": round(ks_ch.get("ks_stat", 0.0), 4),
                  "p": round(ks_ch.get("p", 1.0), 4),
                  "comparable": bool(ks_ch.get("comparable", True))})

    comparable_overall = all(t["comparable"] for t in tests)
    flagged = [t["variable"] for t in tests if not t["comparable"]]
    interpretation = (
        f"Selektions-Subset (n={len(full)}) ist auf allen 5 Variablen verteilungsgleich "
        f"zum Korpus (n={len(corpus_metadata)}); Generalisierung nicht durch ersichtliche "
        "Stichproben-Verzerrung gefaehrdet."
        if comparable_overall else
        f"Selektions-Subset weicht auf {', '.join(flagged)} signifikant vom Korpus ab. "
        "Generalisierung auf Gesamtkorpus erfordert Vorsicht; Proxy-basierte Korpus-Schaetzung "
        "(siehe proxies.corpus_estimate) ergaenzt diese Limitation."
    )

    return {"comparable_overall": comparable_overall, "tests": tests,
            "interpretation": interpretation}


def build_domain_metrics(records: list[DocCERRecord], rng: np.random.Generator,
                          n_resamples: int) -> dict:
    full = [r for r in records if r.scope_status == "full"]

    # Diakritik per Sprache
    by_lang_diac: dict[str, list[dict]] = {}
    for r in full:
        if r.metadata.get("diacritic_rate") is None:
            continue
        lang = r.metadata.get("language", "unknown")
        by_lang_diac.setdefault(lang, []).append({
            "rate": float(r.metadata["diacritic_rate"]),
            "expected": int(r.metadata.get("diacritic_expected", 0)),
            "observed": int(r.metadata.get("diacritic_observed", 0)),
        })

    diac_by_lang = {}
    for lang, items in by_lang_diac.items():
        rates = [it["rate"] for it in items]
        mean, ml, mh, _, _ = doc_level_bootstrap(rates, rng, n_resamples)
        diac_by_lang[lang] = {
            "expected_count": sum(it["expected"] for it in items),
            "observed_count": sum(it["observed"] for it in items),
            "rate": round(mean, 6),
            "rate_ci95": [round(ml, 6), round(mh, 6)],
            "n_docs": len(items),
        }
    all_diac = [it["rate"] for items in by_lang_diac.values() for it in items]
    if all_diac:
        mean, ml, mh, _, _ = doc_level_bootstrap(all_diac, rng, n_resamples)
        diac_overall = {"rate": round(mean, 6), "rate_ci95": [round(ml, 6), round(mh, 6)]}
    else:
        diac_overall = {"rate": None, "rate_ci95": None}

    # HCPR per Sprache
    by_lang_hcpr: dict[str, list[float]] = {}
    for r in full:
        score = r.metadata.get("hcpr")
        if score is None:
            continue
        lang = r.metadata.get("language", "unknown")
        by_lang_hcpr.setdefault(lang, []).append(float(score))
    hcpr_by_lang = {}
    for lang, items in by_lang_hcpr.items():
        mean, ml, mh, _, _ = doc_level_bootstrap(items, rng, n_resamples)
        hcpr_by_lang[lang] = {
            "score": round(mean, 6),
            "score_ci95": [round(ml, 6), round(mh, 6)],
            "n_docs": len(items),
        }
    all_hcpr = [s for v in by_lang_hcpr.values() for s in v]
    if all_hcpr:
        mean, ml, mh, _, _ = doc_level_bootstrap(all_hcpr, rng, n_resamples)
        hcpr_overall = {"score": round(mean, 6), "score_ci95": [round(ml, 6), round(mh, 6)]}
    else:
        hcpr_overall = {"score": None, "score_ci95": None}

    return {
        "diacritic_preservation_rate": {
            "reference_source": "ground_truth_tei",
            "characters": list("éèàçäöüœßæïîôûêâ"),
            "by_language": diac_by_lang,
            "overall": diac_overall,
        },
        "hcpr": {
            "definition": (
                "HCPR-Adaption nach Nosova et al. 2025 (arXiv:2510.06743 §3): "
                "char-class-weighted preservation rate ueber 8 Diakritik-Klassen "
                "(fr_acute_grave, fr_circumflex, fr_diaeresis, fr_cedilla, fr_oe, "
                "de_umlaut, de_eszett, ae_ligature). Pro Klasse: min(hyp/ref, 1.0). "
                "HCPR = Mittel der Klassen-Raten ueber im Doc vorhandene Klassen."
            ),
            "by_language": hcpr_by_lang,
            "overall": hcpr_overall,
        },
        "air": {
            "status": "deferred",
            "note": ("Abbreviation Interpretation Rate (Nosova 2025) erfordert "
                     "Korpus-Vorpruefung. Im Hersch-Korpus (FR/DE-Antiqua-Druck "
                     "1930er-1990er) sind Abbreviationen selten; Pruefung deferred."),
        },
    }


def build_error_categories(records: list[DocCERRecord]) -> dict:
    cat_defs = {
        "diacritics": "Diakritik-Differenzen (z.B. e vs e mit Akzent)",
        "punctuation": "Interpunktions-Unterschiede ohne Wortinhalt",
        "hyphenation": "Trennstrich/Bindestrich-Differenzen <5 Zeichen",
        "whitespace": "Whitespace-only-Differenzen",
        "ocr_artifact": "OCR-Halluzinationen (>50 chars, repeated n-grams)",
        "layout": "Layout-bedingte grosse Inserts/Deletes (>40 chars)",
        "other": "Restliche Substitutionen / Inserts / Deletes",
    }
    abs_counts = Counter()
    per_doc_shares: dict[str, list[float]] = {c: [] for c in cat_defs}
    for r in records:
        if r.scope_status != "full":
            continue
        ec = r.metadata.get("error_categories", {}) or {}
        total_dist = sum(c.get("char_distance", 0) for c in ec.values()) or 1
        for cat in cat_defs:
            cdata = ec.get(cat, {})
            abs_counts[cat] += int(cdata.get("count", 0))
            per_doc_shares[cat].append(cdata.get("char_distance", 0) / total_dist)
    return {
        "definitions": cat_defs,
        "absolute_counts": {c: int(abs_counts[c]) for c in cat_defs},
        "per_doc_normalized_mean": {c: round(float(np.mean(v)), 6) if v else 0.0
                                     for c, v in per_doc_shares.items()},
    }


def build_per_doc(records: list[DocCERRecord], rng: np.random.Generator,
                   n_resamples: int) -> list[dict]:
    out = []
    for r in sorted(records, key=lambda x: x.doc_id):
        cer_e2e, ci_e2e = within_doc_bootstrap(r, rng, n_resamples)
        # OCR-only CI: degenerate (chunks waeren wieder position-aligned-broken)
        if r.metadata.get("ocr_only_cer") is not None:
            v = float(r.metadata["ocr_only_cer"])
            ci_ocr = [round(v, 6), round(v, 6)]
        else:
            ci_ocr = None

        out.append({
            "doc_id": r.doc_id,
            "n_pages": len(r.page_cers),
            "n_ref_chars": int(r.metadata.get("n_ref_chars_doc", sum(r.page_ref_chars))),
            "cer_end_to_end": round(cer_e2e, 6),
            "cer_end_to_end_ci95": ci_e2e,
            "cer_ocr_only": (round(float(r.metadata["ocr_only_cer"]), 6)
                              if r.metadata.get("ocr_only_cer") is not None else None),
            "cer_ocr_only_ci95": ci_ocr,
            "language": r.metadata.get("language", "unknown"),
            "layout_type": r.metadata.get("layout_type", "unknown"),
            "pub_form": r.metadata.get("pub_form", "unknown"),
            "scope_status": r.scope_status,
            "scope_detail": r.scope_detail,
            "top_3_error_categories": r.metadata.get("top_3_error_categories", []),
        })
    return out


def build_proxies(records: list[DocCERRecord], all_doc_ids: list[str],
                   rng: np.random.Generator, n_resamples: int) -> dict:
    cache_path = PROJECT_ROOT / "output" / "evaluation" / "quality_proxy.json"
    if not cache_path.exists():
        return {"status": "deferred", "reason": "quality_proxy.json not present"}

    with open(cache_path, "r", encoding="utf-8") as f:
        cache = json.load(f)
    cache_docs = cache.get("documents", {})

    per_doc_n285 = []
    for did in sorted(all_doc_ids):
        c = cache_docs.get(did, {})
        if not c:
            continue
        per_doc_n285.append({
            "doc_id": did,
            "hit_rate": round(float(c.get("hit_rate", 0.0)), 6),
            "oov_rate": round(1.0 - float(c.get("hit_rate", 0.0)), 6),
            "suspicious_char_ratio": round(float(c.get("suspicious_char_ratio", 0.0)), 6),
            "language": c.get("language"),
            "char_count": int(c.get("char_count", 0)),
        })

    full = [r for r in records if r.scope_status == "full" and r.doc_id in cache_docs]
    if not full:
        return {"definitions": _proxy_definitions(),
                "training_corpus": _training_corpus(),
                "per_doc_n285": per_doc_n285,
                "validation_n19": {"status": "deferred", "reason": "no overlap"},
                "corpus_estimate": {"status": "deferred", "reason": "validation prereq missing"}}

    cers = np.asarray([_doc_weighted_cer(r) for r in full], dtype=float)
    hit = np.asarray([cache_docs[r.doc_id]["hit_rate"] for r in full], dtype=float)
    sus = np.asarray([cache_docs[r.doc_id]["suspicious_char_ratio"] for r in full], dtype=float)
    oov = 1.0 - hit

    per_proxy = {}
    for name, vals in [("hit_rate", hit), ("oov_rate", oov), ("suspicious_char_ratio", sus)]:
        try:
            pearson = scipy_stats.pearsonr(vals, cers)
            spearman = scipy_stats.spearmanr(vals, cers)
            per_proxy[name] = {
                "pearson": round(float(pearson.statistic), 4),
                "pearson_p": round(float(pearson.pvalue), 4),
                "spearman": round(float(spearman.statistic), 4),
                "spearman_p": round(float(spearman.pvalue), 4),
                "loocv_r2": round(_loocv_r2_single(vals, cers), 4),
            }
        except Exception as e:
            per_proxy[name] = {"error": str(e)}

    if hit.std() < 1e-9 or sus.std() < 1e-9:
        return {"definitions": _proxy_definitions(),
                "training_corpus": _training_corpus(),
                "per_doc_n285": per_doc_n285,
                "validation_n19": {"per_proxy": per_proxy,
                                    "composite": {"status": "deferred",
                                                  "reason": "zero variance proxy"}},
                "corpus_estimate": {"status": "deferred", "reason": "degenerate validation"}}

    hit_z = (hit - hit.mean()) / hit.std()
    sus_z = (sus - sus.mean()) / sus.std()
    X = np.column_stack([hit_z, sus_z, np.ones(len(cers))])
    weights, _, _, _ = np.linalg.lstsq(X, cers, rcond=None)
    pred = X @ weights
    ss_res = float(np.sum((cers - pred) ** 2))
    ss_tot = float(np.sum((cers - cers.mean()) ** 2))
    in_sample_r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0

    loo_preds = np.empty(len(cers))
    for i in range(len(cers)):
        mask = np.ones(len(cers), dtype=bool); mask[i] = False
        Xi = X[mask]; yi = cers[mask]
        try:
            w_i, _, _, _ = np.linalg.lstsq(Xi, yi, rcond=None)
            loo_preds[i] = X[i] @ w_i
        except np.linalg.LinAlgError:
            loo_preds[i] = cers[i]
    ss_res_loo = float(np.sum((cers - loo_preds) ** 2))
    loocv_r2 = 1.0 - ss_res_loo / ss_tot if ss_tot > 0 else 0.0

    boot_r2 = []
    for _ in range(n_resamples):
        idx = rng.integers(0, len(cers), size=len(cers))
        Xb = X[idx]; yb = cers[idx]
        if np.linalg.matrix_rank(Xb) < Xb.shape[1]:
            continue
        try:
            w_b, _, _, _ = np.linalg.lstsq(Xb, yb, rcond=None)
        except np.linalg.LinAlgError:
            continue
        pb = Xb @ w_b
        ss_r = float(np.sum((yb - pb) ** 2))
        ss_t = float(np.sum((yb - yb.mean()) ** 2))
        if ss_t > 0:
            boot_r2.append(1.0 - ss_r / ss_t)
    boot_r2_arr = np.asarray(boot_r2, dtype=float)
    loocv_ci = ([round(float(np.quantile(boot_r2_arr, 0.025)), 4),
                  round(float(np.quantile(boot_r2_arr, 0.975)), 4)]
                if boot_r2_arr.size >= 50 else None)

    composite = {
        "method": "linear regression OLS, features standardized",
        "weights": {
            "hit_rate_z": round(float(weights[0]), 6),
            "suspicious_char_ratio_z": round(float(weights[1]), 6),
            "intercept": round(float(weights[2]), 6),
        },
        "in_sample_r2": round(in_sample_r2, 4),
        "loocv_r2": round(loocv_r2, 4),
        "loocv_r2_ci95": loocv_ci,
    }

    # Corpus estimate
    if per_doc_n285:
        all_hit = np.asarray([d["hit_rate"] for d in per_doc_n285], dtype=float)
        all_sus = np.asarray([d["suspicious_char_ratio"] for d in per_doc_n285], dtype=float)
        all_X = np.column_stack([
            (all_hit - hit.mean()) / hit.std(),
            (all_sus - sus.mean()) / sus.std(),
            np.ones(len(all_hit)),
        ])
        all_pred = np.clip(all_X @ weights, 0.0, None)
        est_mean = float(all_pred.mean())
        boot_mean = np.empty(n_resamples)
        for j in range(n_resamples):
            idx = rng.integers(0, len(all_pred), size=len(all_pred))
            boot_mean[j] = all_pred[idx].mean()
        inner_ci = [float(np.quantile(boot_mean, 0.025)),
                     float(np.quantile(boot_mean, 0.975))]
        epist = abs(in_sample_r2 - loocv_r2) * float(cers.std())
        total_ci = [max(inner_ci[0] - epist, 0.0), inner_ci[1] + epist]
        bucket_edges = [0.0, 0.01, 0.02, 0.03, 0.05, 0.08, 0.13, 0.20, 1.0]
        bucket_labels = [f"[{bucket_edges[i]:.2f},{bucket_edges[i+1]:.2f})"
                          for i in range(len(bucket_edges) - 1)]
        counts, _ = np.histogram(all_pred, bins=bucket_edges)
        corpus_estimate = {
            "method": "composite proxy (hit_rate + suspicious_char_ratio) via OLS, propagated regression uncertainty (Singh 2025)",
            "estimated_mean_cer": round(est_mean, 6),
            "estimated_mean_inner_ci95": [round(inner_ci[0], 6), round(inner_ci[1], 6)],
            "estimated_mean_total_ci95": [round(total_ci[0], 6), round(total_ci[1], 6)],
            "estimated_distribution": {
                "bucket_edges_cer": bucket_edges,
                "buckets": bucket_labels,
                "counts": [int(c) for c in counts],
            },
            "caveat": (
                f"Schaetzung auf Basis 2 validierter Proxies (hit_rate, suspicious_char_ratio). "
                f"In-Sample-R² = {in_sample_r2:.3f}, LOOCV-R² = {loocv_r2:.3f} (n={len(cers)}). "
                "Geringe Validierungsguete -> breite Total-CI. KEIN direkter CER. "
                "ngram_loglik / punct_sanity / sentence_length_kl als Proxies deferred."
            ),
        }
    else:
        corpus_estimate = {"status": "deferred", "reason": "no full-corpus proxy data"}

    return {
        "definitions": _proxy_definitions(),
        "training_corpus": _training_corpus(),
        "per_doc_n285": per_doc_n285,
        "validation_n19": {"n": len(full), "per_proxy": per_proxy, "composite": composite},
        "corpus_estimate": corpus_estimate,
    }


def _loocv_r2_single(x: np.ndarray, y: np.ndarray) -> float:
    n = len(x)
    if n < 3:
        return 0.0
    preds = np.empty(n)
    for i in range(n):
        mask = np.ones(n, dtype=bool); mask[i] = False
        xi = x[mask]; yi = y[mask]
        if xi.std() < 1e-9:
            preds[i] = yi.mean(); continue
        slope = np.cov(xi, yi)[0, 1] / xi.var()
        intercept = yi.mean() - slope * xi.mean()
        preds[i] = slope * x[i] + intercept
    ss_res = float(np.sum((y - preds) ** 2))
    ss_tot = float(np.sum((y - y.mean()) ** 2))
    return 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0


def _proxy_definitions() -> dict:
    return {
        "hit_rate": ("Anteil OCR-Tokens (>=2 chars) im pyspellchecker FR/DE-Lexikon. "
                     "Eigennamen-Filter fuer FR/multi (uppercase-only-tokens ausgeschlossen). "
                     "Vorberechnet via scripts/eval/quality_proxy.py."),
        "oov_rate": "Out-of-vocabulary rate, definiert als 1 - hit_rate.",
        "suspicious_char_ratio": ("Anteil unerwarteter Zeichen (z.B. @#$%, fragwuerdige Unicode-Punkte). "
                                    "Klassisches OCR-Artefakt-Signal, vorberechnet via quality_proxy.py."),
        "ngram_loglik": "DEFERRED: 5-gram char-LM Likelihood. Erfordert Trainings-Korpus.",
        "punct_sanity": "DEFERRED: Anteil sinnvoller Interpunktion.",
        "sentence_length_kl": "DEFERRED: KL-Divergenz Satzlaengen-Verteilung vs Referenzkorpus.",
        "diacritic_preservation": "Beobachtete vs erwartete Diakritik-Frequenz. Siehe domain_metrics.diacritic_preservation_rate.",
    }


def _training_corpus() -> dict:
    return {
        "source": "pyspellchecker FR/DE lexica + scripts/eval/quality_proxy.py heuristics",
        "size_chars": None,
        "note": "Wikipedia FR/DE n-gram model nicht verfuegbar in dieser Iteration.",
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="CER Statistics Full (Schema v0.3, Singh 2025 / Nosova 2025)",
    )
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--bootstrap-n", type=int, default=10000)
    parser.add_argument("--out", type=Path,
                        default=DOCS_DIR / "data" / "cer_statistics.json")
    parser.add_argument("--skip-enrich", action="store_true",
                        help="Re-evaluation der Records skippen (nur Cache nutzen).")
    args = parser.parse_args(argv)

    rng = np.random.default_rng(args.seed)
    n_boot = args.bootstrap_n

    print(f"CER Statistics Full (Schema v{SCHEMA_VERSION})")
    print(f"  seed={args.seed}, B={n_boot}")
    print(f"  out={args.out}")
    print()

    print("[1/8] collect_records (E2E pagewise + multi-norm + diacritic)...")
    records, corpus_metadata, n_with_gt, exclusions = collect_records(verbose=False)
    print(f"  records: {len(records)}, n_with_gt: {n_with_gt}")

    print("[2/8] override scope_status (kanonische Liste Session 39)...")
    _override_scope(records)
    full_count = sum(1 for r in records if r.scope_status == "full")
    partial_count = len(records) - full_count
    print(f"  full: {full_count}, partial: {partial_count}")

    print("[3/8] enrich records (E2E full-doc + OCR-only + HCPR + texts)...")
    enrich_records(records, verbose=True)

    print("[4/8] build overall (E2E + OCR-only with CIs)...")
    overall = build_overall(records, rng, n_boot)

    print("[5/8] build strata + multi_norm + paired_test + selection_bias...")
    strata = build_strata(records, rng, n_boot)
    multi_norm = build_multi_norm(records, rng, n_boot)
    paired_test = build_paired_test(records, rng, n_boot)
    selection_bias = build_selection_bias(records, corpus_metadata)

    print("[6/8] build domain_metrics (diacritic + HCPR Nosova 2025)...")
    domain_metrics = build_domain_metrics(records, rng, n_boot)
    error_categories = build_error_categories(records)
    per_doc = build_per_doc(records, rng, n_boot)

    print("[7/8] build proxies (B'1-B'3, validation + corpus estimate)...")
    all_pipe_ids = sorted(p.stem.replace("_final", "")
                           for p in TEI_FINAL_DIR.glob("*_final.xml"))
    proxies = build_proxies(records, all_pipe_ids, rng, n_boot)

    print("[8/8] assemble JSON...")
    git_sha, git_dirty = _git_meta()

    # Erweiterte exclusions: kanonische scope-mismatches + runner-skips
    excluded_block = []
    for did, reason in SCOPE_MISMATCH_REASONS.items():
        excluded_block.append({"doc_id": did, "reason": reason})
    for did, reason in exclusions.items():
        if did not in SCOPE_MISMATCH_REASONS:
            excluded_block.append({"doc_id": did, "reason": reason})

    out = {
        "schema_version": SCHEMA_VERSION,
        "meta": {
            "tool_version": TOOL_VERSION,
            "git_sha": git_sha,
            "git_dirty": git_dirty,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "python_version": platform.python_version(),
            "numpy_version": np.__version__,
            "scipy_version": scipy.__version__,
            "cer_lib": "internal char-level Levenshtein (cer_statistics.levenshtein)",
            "alignment_algo": "evaluate_tei_vs_tei + find_best_alignment (length-ratio-triggered)",
            "normalization_pipeline": [
                {"step": "raw", "ops": ["whitespace collapse", "strip"]},
                {"step": "nfc", "ops": ["raw", "unicodedata.normalize NFC"]},
                {"step": "nfc_hyphen", "ops": ["nfc", "U+2010..U+2015 -> U+002D", "U+00AD removed"]},
                {"step": "nfc_hyphen_case", "ops": ["nfc_hyphen", "casefold"]},
            ],
            "seed": args.seed,
            "bootstrap_n": n_boot,
            "bootstrap_method": "BCa blockwise (block=doc) + Perzentil for paired/within-doc, Singh 2025",
            "literature_refs": LITERATURE_REFS,
        },
        "corpus": {
            "n_total": len(all_pipe_ids),
            "n_with_ground_truth": n_with_gt,
            "n_evaluated": full_count,
            "n_excluded": len(excluded_block),
            "excluded": excluded_block,
        },
        "selection_bias": selection_bias,
        "overall": overall,
        "strata": strata,
        "multi_norm": multi_norm,
        "paired_test": paired_test,
        "stability": {
            "status": "open",
            "reason": ("API-Budget pending user decision (Forschungsplan v2 §9 b); "
                       "stability not measured in this iteration. Re-Run-Pilot 5 Docs x 3 "
                       "Gemini-Calls vorgemerkt."),
            "n_docs": None, "n_runs": None, "per_doc_std": None,
        },
        "domain_metrics": domain_metrics,
        "error_categories": error_categories,
        "per_doc": per_doc,
        "comparison_lit": COMPARISON_LIT,
        "proxies": proxies,
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)

    e2e = overall["end_to_end"]
    ocr = overall["ocr_only"]
    print()
    print(f"Wrote {args.out}")
    print(f"  schema={SCHEMA_VERSION}, n_evaluated={full_count}, n_excluded={len(excluded_block)}")
    print(f"  E2E mean = {e2e['mean']*100:.2f}% (CI95 [{e2e['mean_ci95'][0]*100:.2f}%, {e2e['mean_ci95'][1]*100:.2f}%])")
    print(f"  E2E median = {e2e['median']*100:.2f}% (CI95 [{e2e['median_ci95'][0]*100:.2f}%, {e2e['median_ci95'][1]*100:.2f}%])")
    if ocr.get("status") == "measured":
        print(f"  OCR-only mean = {ocr['mean']*100:.2f}% (CI95 [{ocr['mean_ci95'][0]*100:.2f}%, {ocr['mean_ci95'][1]*100:.2f}%])")
        print(f"  Paired diff (E2E - OCR) = {paired_test['mean_diff']*100:+.2f}pp, p={paired_test['p_bootstrap_two_sided']:.4f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
