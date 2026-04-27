"""
Runner: liest reale TEIs ein und produziert DocCERRecord-Liste fuer
`scripts/cer_statistics.py`. Getrennt vom Statistik-Modul, damit Tests
ohne Daten laufen koennen.
"""

from __future__ import annotations

import json
from pathlib import Path

from scripts.cer_statistics import (
    DocCERRecord,
    cer_under_norms,
    diacritic_preservation_rate,
)
from scripts.config import (
    DOC_METADATA_PATH,
    REFERENZ_TEI_DIR,
    TEI_FINAL_DIR,
)
from scripts.evaluate_ocr import (
    evaluate_tei_vs_tei,
    evaluate_tei_vs_tei_pagewise,
    extract_pages_for_comparison,
    extract_text_for_comparison,
    _find_tei_path,
)


def _load_metadata() -> dict[str, dict]:
    """Laedt doc_metadata.json. Field-Normalisierung (layout_type vs type)."""
    if not DOC_METADATA_PATH.exists():
        return {}
    with open(DOC_METADATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    docs = data.get("documents", data)
    out = {}
    for doc_id, meta in docs.items():
        if not isinstance(meta, dict):
            continue
        m = dict(meta)
        if "layout_type" not in m and "type" in m:
            m["layout_type"] = m["type"]
        out[str(doc_id)] = m
    return out


def _ground_truth_doc_ids() -> list[str]:
    """Findet alle Dok-IDs mit Referenz-TEI."""
    ids = set()
    if REFERENZ_TEI_DIR.exists():
        for p in REFERENZ_TEI_DIR.glob("*.xml"):
            ids.add(p.stem)
        pilot = REFERENZ_TEI_DIR / "Pilot"
        if pilot.exists():
            for p in pilot.glob("*.xml"):
                ids.add(p.stem.split(" ")[0])
    return sorted(ids)


def _detect_scope_mismatch(eval_result: dict) -> tuple[str, str | None]:
    """Heuristische Scope-Bereinigung. Markiert als 'partial' wenn:
      (a) Pipeline-/Referenz-Seitenzahl deutlich abweicht (Faktor >= 1.5), ODER
      (b) Doc-CER > 50% (Schwellwert aus existierendem benchmark_cer.py;
          CER ueber 50% ist ein klares Indiz fuer Text-/Scope-Mismatch, nicht
          OCR-Qualitaet -- z.B. Pipeline-TEI deckt anderen Text-Abschnitt ab).
    """
    ref_total = eval_result.get("ref_pages_total", 0) or 0
    pipe_total = eval_result.get("pipe_pages_total", 0) or 0
    cer_val = float(eval_result.get("cer", 0.0) or 0.0)

    reasons = []
    if ref_total > 0 and pipe_total > 0:
        ratio = max(ref_total, pipe_total) / max(min(ref_total, pipe_total), 1)
        if ratio >= 1.5:
            reasons.append(f"page_ratio={ref_total}/{pipe_total} ({ratio:.1f}x)")

    if cer_val > 0.50:
        reasons.append(f"cer={cer_val*100:.1f}% > 50% (text-scope mismatch)")

    if reasons:
        return ("partial", "; ".join(reasons))
    return ("full", None)


def _diacritic_for_doc(doc_id: str, language: str) -> dict | None:
    """Berechnet Diakritik-Erhaltungsrate ueber den ganzen Dok-Text
    (Volltext-Vergleich, nicht per-Page -- Aggregat ist robust genug).
    """
    ref_path = _find_tei_path(doc_id, REFERENZ_TEI_DIR)
    pipe_path = TEI_FINAL_DIR / f"{doc_id}_final.xml"
    if not pipe_path.exists():
        pipe_path = TEI_FINAL_DIR / f"{doc_id}.xml"
    if ref_path is None or not pipe_path.exists():
        return None
    ref_pages = extract_pages_for_comparison(ref_path)
    pipe_pages = extract_pages_for_comparison(pipe_path)
    ref_text = " ".join(ref_pages.values())
    pipe_text = " ".join(pipe_pages.values())
    return diacritic_preservation_rate(ref_text, pipe_text, language)


def _multi_norm_cer_for_doc(doc_id: str) -> dict[str, float] | None:
    """CER pro Normalisierungs-Regime auf dem **Volltext** des Dokuments.

    Nutzt `extract_text_for_comparison()` (gleiche Quelle wie das globale
    `evaluate_tei_vs_tei`), damit der nfc_hyphen-Wert dieser Funktion mit
    `global_result['cer']` konsistent ist. Pagewise-Vergleich ist seit der
    Pipeline-Aenderung 2026-04 unzuverlaessig (Page-Numbering-Drift).
    """
    from scripts.cer_statistics import normalize_text, cer as cer_fn, NORM_REGIMES

    ref_path = _find_tei_path(doc_id, REFERENZ_TEI_DIR)
    pipe_path = TEI_FINAL_DIR / f"{doc_id}_final.xml"
    if not pipe_path.exists():
        pipe_path = TEI_FINAL_DIR / f"{doc_id}.xml"
    if ref_path is None or not pipe_path.exists():
        return None

    ref_text = extract_text_for_comparison(ref_path)
    pipe_text = extract_text_for_comparison(pipe_path)
    if not ref_text:
        return None

    return {
        regime: cer_fn(normalize_text(ref_text, regime), normalize_text(pipe_text, regime))
        for regime in NORM_REGIMES
    }


def collect_records(verbose: bool = True) -> tuple[
    list[DocCERRecord], dict[str, dict], int, dict[str, str]
]:
    """Liest alle Referenz-Pipeline-Paare ein, baut DocCERRecord-Liste.

    Returns:
        records:          List[DocCERRecord] der erfolgreich evaluierten Docs.
        corpus_metadata:  Vollstaendiges metadata-dict (alle 285 Docs) fuer Korpus-Stats.
        n_with_gt:        Anzahl Docs mit Referenz-TEI (Bruttowert vor Filter).
        exclusions:       {doc_id: reason} fuer alles, was nicht in records gelandet ist.
    """
    metadata = _load_metadata()
    gt_ids = _ground_truth_doc_ids()
    n_with_gt = len(gt_ids)

    records: list[DocCERRecord] = []
    exclusions: dict[str, str] = {}

    for doc_id in gt_ids:
        if verbose:
            print(f"  evaluating {doc_id}...", flush=True)
        try:
            # Global Eval (content-aligned) ist die robuste Doc-CER-Quelle.
            # Pagewise ist seit Maerz 2026 fragil, weil die Pipeline die
            # <pb>-Nummerierung geaendert hat: dieselbe Page-ID kann jetzt
            # unterschiedlichen Inhalt enthalten, was Pagewise-CER absurd hochzieht.
            global_result = evaluate_tei_vs_tei(
                doc_id, REFERENZ_TEI_DIR, TEI_FINAL_DIR
            )
            pagewise_result = evaluate_tei_vs_tei_pagewise(
                doc_id, REFERENZ_TEI_DIR, TEI_FINAL_DIR
            )
        except Exception as e:
            exclusions[doc_id] = f"eval_error: {type(e).__name__}: {e}"
            continue

        if global_result.get("status") != "OK":
            exclusions[doc_id] = global_result.get("error", "unknown")
            continue

        # Per-Page-CERs aus pagewise (fuer Outlier-Detection und Visualisierung).
        page_results = pagewise_result.get("page_results", []) if pagewise_result.get("status") == "OK" else []
        page_cers = [float(pr["cer"]) for pr in page_results]
        page_chars = [int(pr.get("ref_chars", 0)) for pr in page_results]

        # Verwende GLOBAL fuer scope_status + doc_cer.
        scope_status, scope_detail = _detect_scope_mismatch(global_result)
        # Fallback-Result fuer ref_pages_total etc.
        result = global_result

        meta = dict(metadata.get(doc_id, {}))
        meta.setdefault("language", "unknown")
        meta.setdefault("layout_type", "unknown")
        meta.setdefault("pub_form", "unknown")

        # Multi-Norm CER pro Doc (Volltext-Vergleich -- ergaenzend zur per-page Liste)
        norms = _multi_norm_cer_for_doc(doc_id)
        if norms is None:
            norms = {}

        # Diakritik-Erhaltungsrate
        diac = _diacritic_for_doc(doc_id, meta.get("language", "unknown"))
        if diac and diac.get("rate") is not None:
            meta["diacritic_rate"] = diac["rate"]
            meta["diacritic_expected"] = diac["expected_count"]
            meta["diacritic_observed"] = diac["observed_count"]

        # Top-3 Fehlerkategorien aus dem Doc-Result, falls vorhanden
        # (evaluate_tei_vs_tei_pagewise liefert Categories nicht direkt;
        # nutzen wir den nicht-pagewise Result nur falls noetig).
        # doc_cer aus GLOBAL eval (content-aligned, robust gegen pb-Drift).
        # Multi-Norm-Werte sind nur informativ; canonical CER ist global.
        doc_cer = float(global_result.get("cer", 0.0))

        records.append(DocCERRecord(
            doc_id=doc_id,
            page_cers=page_cers,
            page_ref_chars=page_chars,
            cer_by_regime=norms,
            metadata=meta,
            scope_status=scope_status,
            scope_detail=scope_detail,
            doc_cer=doc_cer,
        ))

    return records, metadata, n_with_gt, exclusions
