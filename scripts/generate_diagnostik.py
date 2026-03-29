"""
Generiert Diagnostik-Daten fuer das Frontend-Dashboard.

Outputs:
  - docs/data/diagnostik_ocr.json      (CER/WER, Konfusion, Pipeline-Effekt, Pagewise)
  - docs/data/diagnostik_corpus.json   (konsolidiertes Qualitaetsprofil aller 285 Docs)
  - docs/data/diagnostik_entities.json (Entity-Linking, Sprach-Stratifizierung, Top-Unverlinkte)

Usage:
    python -m scripts.generate_diagnostik              # nur OCR-Diagnostik
    python -m scripts.generate_diagnostik --corpus      # + Corpus-JSON
    python -m scripts.generate_diagnostik --entities    # + Entity-JSON
    python -m scripts.generate_diagnostik --all         # alles
"""

import argparse
import json
import re
import statistics
from pathlib import Path
from datetime import datetime

from scripts.config import (
    REFERENZ_TEI_DIR, TEI_FINAL_DIR, EVALUATION_DIR,
    DOC_METADATA_PATH, MISTRAL_RESULTS_DIR, PROJECT_ROOT,
)
from scripts.evaluate_ocr import (
    evaluate_tei_vs_tei, find_differences, build_confusion_matrix,
    extract_text_for_comparison, load_ocr_result, calculate_cer,
    normalize_for_comparison,
)
from scripts.benchmark_cer import (
    load_metadata, get_ground_truth_doc_ids,
)

DOCS_DATA_DIR = PROJECT_ROOT / "docs" / "data"
DIAGNOSTIK_JSON = DOCS_DATA_DIR / "diagnostik_ocr.json"
DIAGNOSTIK_CORPUS_JSON = DOCS_DATA_DIR / "diagnostik_corpus.json"
DIAGNOSTIK_ENTITIES_JSON = DOCS_DATA_DIR / "diagnostik_entities.json"
DIAGNOSTIK_LOG = DOCS_DATA_DIR / "diagnostik_log.json"

QUALITY_PROXY_JSON = EVALUATION_DIR / "quality_proxy.json"
COMPLETENESS_JSON = EVALUATION_DIR / "completeness_check.json"
DIAGNOSTIK_TEI_JSON = DOCS_DATA_DIR / "diagnostik_tei.json"
BENCHMARK_PAGEWISE_JSON = EVALUATION_DIR / "benchmark_pagewise.json"
REFERENCE_COMPARISON_JSON = EVALUATION_DIR / "benchmark_tei_vs_tei.json"

OUTLIER_DOC_IDS = ["1910", "290", "30", "90"]

# Scope-Mismatch-Definitionen (manuell verifiziert, Session 33)
SCOPE_MISMATCHES = {
    "30": {
        "ref_pages": "[222]-229 (8 Seiten)",
        "pipe_pages": "1-4 (4 Seiten)",
        "ocr_pages": 4,
        "detail": "Referenz 8 Seiten, Pipeline nur 4. OCR deckt ~50% ab.",
        "status": "partial",
    },
    "300": {
        "ref_pages": "87-88 (2 Seiten)",
        "pipe_pages": "1-4 (4 Seiten, inkl. Deckblatt)",
        "ocr_pages": 4,
        "detail": "Referenz nur 2 Seiten, Pipeline hat 4 (inkl. Bibliotheks-Metadaten).",
        "status": "partial",
    },
    "1440": {
        "ref_pages": "263-270 (8 Seiten)",
        "pipe_pages": "263-266, 268-269, 5 (7 Seiten, S.267 fehlt)",
        "ocr_pages": 5,
        "detail": "Seite 267 fehlt in Pipeline, letzte Seite falsch nummeriert. 2 OCR-Seiten fehlen.",
        "status": "partial",
    },
}


def log_action(action: str, docs_affected: list, result_summary: str, details: str = ""):
    """Schreibt Eintrag in diagnostik_log.json."""
    log_path = DIAGNOSTIK_LOG
    entries = []
    if log_path.exists():
        entries = json.loads(log_path.read_text(encoding='utf-8'))

    entries.append({
        "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "lane": "ocr",
        "action": action,
        "docs_affected": docs_affected,
        "result_summary": result_summary,
        "details": details,
    })
    log_path.write_text(json.dumps(entries, indent=2, ensure_ascii=False), encoding='utf-8')


def load_pre_normfix_results() -> dict:
    """Laedt vorherige Benchmark-Ergebnisse (vor Normalisierungsfix)."""
    pre_path = EVALUATION_DIR / "benchmark_pre_normfix.json"
    if pre_path.exists():
        return json.loads(pre_path.read_text(encoding='utf-8'))
    return {}


def load_post_normfix_results() -> dict:
    """Laedt aktuelle Benchmark-Ergebnisse (nach Normalisierungsfix)."""
    post_path = EVALUATION_DIR / "benchmark_post_normfix.json"
    if post_path.exists():
        return json.loads(post_path.read_text(encoding='utf-8'))
    return {}


def build_baseline_comparison(pre: dict, post: dict) -> list:
    """Erstellt Vorher/Nachher-Vergleich pro Doc."""
    comparison = []
    pre_docs = pre.get('documents', {})
    post_docs = post.get('documents', {})

    for doc_id in sorted(set(pre_docs.keys()) | set(post_docs.keys())):
        pre_d = pre_docs.get(doc_id, {})
        post_d = post_docs.get(doc_id, {})
        if pre_d.get('status') != 'OK' and post_d.get('status') != 'OK':
            continue

        pre_cer = pre_d.get('cer', None)
        post_cer = post_d.get('cer', None)
        delta = (post_cer - pre_cer) if pre_cer is not None and post_cer is not None else None

        comparison.append({
            'doc_id': doc_id,
            'cer_before': pre_cer,
            'cer_after': post_cer,
            'cer_delta': delta,
            'wer_before': pre_d.get('wer'),
            'wer_after': post_d.get('wer'),
            'language': post_d.get('metadata', {}).get('language', '?'),
            'type': post_d.get('metadata', {}).get('type', '?'),
        })

    return sorted(comparison, key=lambda x: abs(x.get('cer_delta') or 0), reverse=True)


def build_corpus_confusion_matrix(post: dict) -> dict:
    """Baut Konfusionsmatrix ueber alle evaluierten Docs."""
    all_diffs = []
    for doc_id, doc_data in post.get('documents', {}).items():
        if doc_data.get('status') != 'OK':
            continue
        diffs = doc_data.get('differences', [])
        all_diffs.extend(diffs)

    return build_confusion_matrix(all_diffs)


def compute_ocr_baseline_cer(doc_id: str) -> dict:
    """Berechnet OCR-Baseline-CER (Mistral OCR vs. Referenz) fuer ein Doc."""
    ref_path = None
    for p in REFERENZ_TEI_DIR.glob(f'{doc_id}*'):
        if p.suffix == '.xml':
            ref_path = p
            break
    if not ref_path:
        for p in (REFERENZ_TEI_DIR / 'Pilot').glob(f'{doc_id}*'):
            if p.suffix == '.xml':
                ref_path = p
                break

    if not ref_path:
        return {'status': 'SKIP', 'error': 'Referenz nicht gefunden'}

    # OCR-Text laden (alle Seiten eines Docs zusammenfuegen)
    ocr_pages = sorted(MISTRAL_RESULTS_DIR.glob(f'{doc_id}_p*.md'))
    if not ocr_pages:
        return {'status': 'SKIP', 'error': 'Kein OCR-Output'}

    ocr_text = ""
    for p in ocr_pages:
        ocr_text += load_ocr_result(p) + " "
    ocr_text = normalize_for_comparison(ocr_text)

    ref_text = extract_text_for_comparison(ref_path, include_footnotes=False)

    if not ref_text:
        return {'status': 'SKIP', 'error': 'Referenz leer'}

    cer = calculate_cer(ref_text, ocr_text)
    return {
        'status': 'OK',
        'ocr_cer': cer,
        'ocr_chars': len(ocr_text),
        'ref_chars': len(ref_text),
    }


def diagnose_outlier(doc_id: str, post_data: dict) -> dict:
    """Analysiert ein verschlechtertes Doc im Detail."""
    doc_result = post_data.get('documents', {}).get(doc_id, {})

    # OCR-Baseline
    ocr_baseline = compute_ocr_baseline_cer(doc_id)

    # Error-Kategorien aus Post-Normfix
    error_cats = doc_result.get('error_categories', {})

    # Top-Fehler identifizieren
    dominant_category = max(
        error_cats.items(),
        key=lambda x: x[1].get('cer_contribution', 0),
        default=('unknown', {})
    )

    # Diagnosis
    cer_e2e = doc_result.get('cer', 0)
    ocr_cer = ocr_baseline.get('ocr_cer', 0) if ocr_baseline.get('status') == 'OK' else None

    if ocr_cer is not None and ocr_cer > 0.15:
        primary_cause = "source_ocr_quality"
        explanation = f"OCR-Baseline bereits bei {ocr_cer*100:.1f}% CER. Schlechte Scanqualitaet oder komplexes Layout."
    elif dominant_category[0] == 'layout':
        primary_cause = "layout_alignment"
        explanation = "Layout-Fehler dominant. Gemini-Layout oder TEI-Strukturierung verursacht Textverschiebungen."
    elif dominant_category[0] == 'ocr_artifact':
        primary_cause = "ocr_hallucination"
        explanation = "OCR-Halluzinationen (wiederholte Muster, Barcode-Artefakte)."
    else:
        primary_cause = "mixed"
        explanation = f"Mischbild: dominant '{dominant_category[0]}' ({dominant_category[1].get('cer_contribution', 0)*100:.1f}% CER-Beitrag)."

    return {
        'doc_id': doc_id,
        'cer_end_to_end': cer_e2e,
        'ocr_baseline_cer': ocr_cer,
        'pipeline_delta': (cer_e2e - ocr_cer) if ocr_cer is not None else None,
        'primary_cause': primary_cause,
        'explanation': explanation,
        'error_categories': error_cats,
        'alignment_info': doc_result.get('alignment_info', ''),
        'metadata': doc_result.get('metadata', {}),
    }


def build_pipeline_effect(post: dict) -> list:
    """Erstellt OCR-Baseline vs. End-to-End Vergleich pro Doc."""
    effects = []
    for doc_id, doc_data in post.get('documents', {}).items():
        if doc_data.get('status') != 'OK':
            continue
        ocr_base = compute_ocr_baseline_cer(doc_id)
        ocr_cer = ocr_base.get('ocr_cer') if ocr_base.get('status') == 'OK' else None
        e2e_cer = doc_data.get('cer', 0)

        effects.append({
            'doc_id': doc_id,
            'ocr_baseline_cer': ocr_cer,
            'end_to_end_cer': e2e_cer,
            'delta': (e2e_cer - ocr_cer) if ocr_cer is not None else None,
            'improved': (e2e_cer < ocr_cer) if ocr_cer is not None else None,
            'language': doc_data.get('metadata', {}).get('language', '?'),
            'type': doc_data.get('metadata', {}).get('type', '?'),
        })

    return sorted(effects, key=lambda x: x.get('delta') or 0)


def main():
    print("Generiere OCR-Diagnostik-Daten...")
    print()

    # Benchmark-Ergebnisse laden
    pre = load_pre_normfix_results()
    post = load_post_normfix_results()

    if not post:
        print("FEHLER: benchmark_post_normfix.json nicht gefunden!")
        return 1

    # 1. Baseline-Vergleich
    print("1. Baseline-Vergleich (vor/nach Normalisierung)...")
    baseline = build_baseline_comparison(pre, post)
    log_action(
        "baseline_comparison",
        [b['doc_id'] for b in baseline],
        f"{len(baseline)} Docs verglichen, mittl. Delta: "
        f"{sum(b['cer_delta'] for b in baseline if b['cer_delta'] is not None) / max(len(baseline), 1) * 100:.2f}pp",
    )

    # 2. Konfusionsmatrix
    print("2. Konfusionsmatrix (alle Docs)...")
    confusion = build_corpus_confusion_matrix(post)
    print(f"   {confusion['total_substitutions']} Substitutionen, "
          f"{confusion['total_insertions']} Insertions, "
          f"{confusion['total_deletions']} Deletions")
    print(f"   Top-5 Substitutionen:")
    for s in confusion['substitutions'][:5]:
        print(f"     {s['ref_codepoint']} -> {s['hyp_codepoint']}: {s['count']}x")
    log_action(
        "confusion_matrix",
        [],
        f"Top-Substitution: {confusion['substitutions'][0]['ref_codepoint']} -> "
        f"{confusion['substitutions'][0]['hyp_codepoint']} ({confusion['substitutions'][0]['count']}x)"
        if confusion['substitutions'] else "Keine Substitutionen",
    )

    # 3. Outlier-Diagnose
    print("\n3. Outlier-Diagnose...")
    outliers = {}
    for doc_id in OUTLIER_DOC_IDS:
        print(f"   Doc {doc_id}...")
        outliers[doc_id] = diagnose_outlier(doc_id, post)
        diag = outliers[doc_id]
        if diag['ocr_baseline_cer']:
            print(f"     E2E-CER: {diag['cer_end_to_end']*100:.1f}%, "
                  f"OCR-Baseline: {diag['ocr_baseline_cer']*100:.1f}% "
                  f"-> {diag['primary_cause']}")
        else:
            print(f"     E2E-CER: {diag['cer_end_to_end']*100:.1f}% "
                  f"-> {diag['primary_cause']}")
    log_action(
        "outlier_diagnosis",
        OUTLIER_DOC_IDS,
        "; ".join(f"Doc {d}: {o['primary_cause']}" for d, o in outliers.items()),
    )

    # 4. Pipeline-Effekt
    print("\n4. Pipeline-Effekt (OCR vs. E2E)...")
    pipeline_effect = build_pipeline_effect(post)
    improved = sum(1 for e in pipeline_effect if e.get('improved') is True)
    worsened = sum(1 for e in pipeline_effect if e.get('improved') is False)
    print(f"   {improved} verbessert, {worsened} verschlechtert, "
          f"{len(pipeline_effect) - improved - worsened} ohne OCR-Baseline")
    log_action(
        "pipeline_effect",
        [e['doc_id'] for e in pipeline_effect],
        f"{improved} verbessert, {worsened} verschlechtert",
    )

    # 5. Per-Doc Daten mit Scope-Annotation
    per_doc = {}
    for doc_id, doc_data in post.get('documents', {}).items():
        if doc_data.get('status') != 'OK':
            continue

        scope = SCOPE_MISMATCHES.get(doc_id)
        if scope:
            scope_status = scope['status']
            scope_detail = scope['detail']
        elif doc_data.get('scope_mismatch'):
            scope_status = 'partial'
            scope_detail = doc_data.get('scope_info', '')
        else:
            scope_status = 'full'
            scope_detail = (
                f"Ref {doc_data.get('ref_pages', '?')} Seiten, "
                f"Pipeline {doc_data.get('pipe_pages', '?')} Seiten"
            )

        per_doc[doc_id] = {
            'cer': doc_data['cer'],
            'wer': doc_data['wer'],
            'ref_chars': doc_data['ref_chars'],
            'scope_status': scope_status,
            'scope_detail': scope_detail,
            'error_categories': {
                cat: {
                    'count': data['count'],
                    'cer_contribution': data['cer_contribution'],
                }
                for cat, data in doc_data.get('error_categories', {}).items()
            },
            'metadata': doc_data.get('metadata', {}),
        }

    # 6. Finale CER-Statistik (nur scope=full Docs)
    print("\n5. Finale Statistik...")
    all_cers = [d['cer'] for d in per_doc.values()]
    full_docs = {did: d for did, d in per_doc.items() if d['scope_status'] == 'full'}
    partial_docs = {did: d for did, d in per_doc.items() if d['scope_status'] == 'partial'}
    full_cers = sorted([d['cer'] for d in full_docs.values()])

    def _stats(cers):
        if not cers:
            return {}
        s = sorted(cers)
        n = len(s)
        q1 = s[n // 4] if n >= 4 else s[0]
        q3 = s[3 * n // 4] if n >= 4 else s[-1]
        return {
            'n_evaluated': n,
            'mean_cer': statistics.mean(s),
            'median_cer': statistics.median(s),
            'std_cer': statistics.stdev(s) if n > 1 else 0.0,
            'min_cer': min(s),
            'max_cer': max(s),
            'q1_cer': q1,
            'q3_cer': q3,
            'docs_under_3pct': sum(1 for c in s if c < 0.03),
            'docs_over_15pct': sum(1 for c in s if c > 0.15),
        }

    final_summary = _stats(full_cers)
    final_summary['n_excluded'] = len(partial_docs)
    final_summary['excluded_doc_ids'] = sorted(partial_docs.keys())

    all_summary = _stats(all_cers)
    all_summary['n_excluded'] = 0
    all_summary['note'] = 'Alle Docs inkl. Scope-Mismatches'

    print(f"   Bereinigte Statistik ({final_summary['n_evaluated']} Docs, "
          f"{final_summary['n_excluded']} excluded):")
    print(f"   Mean CER: {final_summary['mean_cer']*100:.2f}%, "
          f"Median: {final_summary['median_cer']*100:.2f}%")
    print(f"   Docs <3%: {final_summary['docs_under_3pct']}, "
          f"Docs >15%: {final_summary['docs_over_15pct']}")

    # 7. Stratifizierte Statistik
    print("\n6. Stratifizierte Statistik...")
    by_language = {}
    by_layout = {}
    for did, d in full_docs.items():
        lang = d['metadata'].get('language', '?')
        ltype = d['metadata'].get('type', '?')
        by_language.setdefault(lang, []).append(d['cer'])
        by_layout.setdefault(ltype, []).append(d['cer'])

    strat_lang = [
        {'lang': lang, 'n': len(cers),
         'mean': statistics.mean(cers), 'median': statistics.median(cers)}
        for lang, cers in sorted(by_language.items())
    ]
    strat_layout = [
        {'type': lt, 'n': len(cers),
         'mean': statistics.mean(cers), 'median': statistics.median(cers)}
        for lt, cers in sorted(by_layout.items())
    ]

    for s in strat_lang:
        print(f"   {s['lang']}: n={s['n']}, mean={s['mean']*100:.1f}%, median={s['median']*100:.1f}%")
    for s in strat_layout:
        print(f"   Typ {s['type']}: n={s['n']}, mean={s['mean']*100:.1f}%, median={s['median']*100:.1f}%")

    # 8. Reduktions-Timeline
    reduction_timeline = [
        {"step": "Ausgangslage E51", "mean": 9.33, "median": 5.52},
        {"step": "Sym. Normalisierung", "mean": 8.11, "median": 5.36},
        {"step": "Hyphen-Norm.", "mean": 7.29, "median": 2.61},
        {"step": "CI-Alignment", "mean": 5.97, "median": 2.42},
        {"step": "Scope-bereinigt",
         "mean": round(final_summary['mean_cer'] * 100, 2),
         "median": round(final_summary['median_cer'] * 100, 2),
         "note": f"Nur {final_summary['n_evaluated']} Docs mit scope=full"},
    ]

    log_action(
        "scope_bereinigung",
        sorted(partial_docs.keys()),
        f"{len(partial_docs)} Docs als partial markiert: {sorted(partial_docs.keys())}. "
        f"Bereinigte Statistik: Mean {final_summary['mean_cer']*100:.2f}%, "
        f"Median {final_summary['median_cer']*100:.2f}%",
    )

    # Zusammenstellen
    output = {
        'generated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'generator': 'scripts/generate_diagnostik.py',
        'summary': {
            'all_docs': all_summary,
            'scope_clean': final_summary,
            'pre_normfix': pre.get('summary', {}),
            'post_normfix': post.get('summary', {}),
            'normalization_effect': {
                'mean_cer_delta': (
                    post['summary']['avg_cer'] - pre['summary']['avg_cer']
                ) if pre.get('summary') else None,
                'median_cer_delta': (
                    post['summary']['median_cer'] - pre['summary']['median_cer']
                ) if pre.get('summary') else None,
            },
        },
        'by_language': strat_lang,
        'by_layout': strat_layout,
        'reduction_timeline': reduction_timeline,
        'baseline_comparison': baseline,
        'confusion_matrix': {
            'substitutions': confusion['substitutions'][:50],
            'insertions': confusion['insertions'][:30],
            'deletions': confusion['deletions'][:30],
            'totals': {
                'substitutions': confusion['total_substitutions'],
                'insertions': confusion['total_insertions'],
                'deletions': confusion['total_deletions'],
            },
        },
        'outlier_diagnosis': outliers,
        'pipeline_effect': pipeline_effect,
        'per_doc': per_doc,
    }

    # Speichern
    DOCS_DATA_DIR.mkdir(parents=True, exist_ok=True)
    json_text = json.dumps(output, indent=2, ensure_ascii=False, default=str)
    DIAGNOSTIK_JSON.write_text(json_text, encoding='utf-8')
    print(f"\nJSON: {DIAGNOSTIK_JSON}")

    log_action(
        "diagnostik_json_final",
        list(per_doc.keys()),
        f"Finale diagnostik_ocr.json: {len(per_doc)} Docs, "
        f"{final_summary['n_evaluated']} scope=full, "
        f"{final_summary['n_excluded']} scope=partial, "
        f"Mean {final_summary['mean_cer']*100:.2f}%, "
        f"Median {final_summary['median_cer']*100:.2f}%",
    )

    return 0


def _quality_bucket(hit_rate):
    """Quality-Bucket basierend auf Proxy Hit Rate."""
    if hit_rate is None:
        return "unknown"
    if hit_rate >= 0.95:
        return "excellent"
    if hit_rate >= 0.90:
        return "good"
    if hit_rate >= 0.85:
        return "acceptable"
    if hit_rate >= 0.75:
        return "check"
    return "outlier"


def generate_corpus_json():
    """Konsolidiert alle Qualitaetssignale in diagnostik_corpus.json."""
    print("\n=== Generiere diagnostik_corpus.json ===\n")

    # --- Quellen laden ---
    proxy_data = {}
    if QUALITY_PROXY_JSON.exists():
        raw = json.loads(QUALITY_PROXY_JSON.read_text(encoding='utf-8'))
        proxy_data = raw.get('documents', {})
        proxy_summary = raw.get('summary', {})
        print(f"  Quality Proxy: {len(proxy_data)} Docs geladen")
    else:
        proxy_summary = {}
        print("  WARNUNG: quality_proxy.json nicht gefunden")

    completeness_data = {}
    completeness_summary = {}
    if COMPLETENESS_JSON.exists():
        raw = json.loads(COMPLETENESS_JSON.read_text(encoding='utf-8'))
        completeness_data = raw.get('documents', {})
        completeness_summary = raw.get('summary', {})
        print(f"  Completeness: {len(completeness_data)} Docs geladen")
    else:
        print("  WARNUNG: completeness_check.json nicht gefunden")

    ocr_per_doc = {}
    if DIAGNOSTIK_JSON.exists():
        raw = json.loads(DIAGNOSTIK_JSON.read_text(encoding='utf-8'))
        ocr_per_doc = raw.get('per_doc', {})
        print(f"  OCR-Diagnostik: {len(ocr_per_doc)} Docs geladen")

    tei_per_doc = {}
    if DIAGNOSTIK_TEI_JSON.exists():
        raw = json.loads(DIAGNOSTIK_TEI_JSON.read_text(encoding='utf-8'))
        tei_per_doc = raw.get('per_doc', {})
        print(f"  TEI-Diagnostik: {len(tei_per_doc)} Docs geladen")

    # Metadaten fuer Sprache/Typ
    metadata = {}
    if DOC_METADATA_PATH.exists():
        raw = json.loads(DOC_METADATA_PATH.read_text(encoding='utf-8'))
        metadata = raw.get('documents', raw)

    # --- Alle Doc-IDs sammeln ---
    all_ids = sorted(
        set(proxy_data.keys())
        | set(completeness_data.keys())
        | set(tei_per_doc.keys()),
        key=lambda x: int(x) if x.isdigit() else x,
    )
    print(f"\n  Gesamtkorpus: {len(all_ids)} Docs")

    # --- Pro-Doc-Profil erstellen ---
    docs = {}
    buckets = {"excellent": 0, "good": 0, "acceptable": 0, "check": 0, "outlier": 0, "unknown": 0}

    for doc_id in all_ids:
        proxy = proxy_data.get(doc_id, {})
        compl = completeness_data.get(doc_id, {})
        ocr = ocr_per_doc.get(doc_id, {})
        tei = tei_per_doc.get(doc_id, {})
        meta = metadata.get(doc_id, {})

        hit_rate = proxy.get('hit_rate')
        bucket = _quality_bucket(hit_rate)
        buckets[bucket] += 1

        docs[doc_id] = {
            'cer': ocr.get('cer'),
            'wer': ocr.get('wer'),
            'has_ground_truth': doc_id in ocr_per_doc,
            'proxy_hit_rate': hit_rate,
            'pages_expected': compl.get('expected_pages'),
            'pages_actual': compl.get('actual_pb'),
            'pages_empty': compl.get('empty_pages', 0),
            'pages_thin': compl.get('thin_pages', 0),
            'completeness': compl.get('status', 'unknown'),
            'language': compl.get('language') or meta.get('language', ''),
            'layout_type': compl.get('layout_type') or meta.get('type', ''),
            'tei_valid': tei.get('valid', True),
            'tei_warnings': tei.get('warnings', []),
            'quality_bucket': bucket,
        }

    # --- Summary ---
    hit_rates = [d['proxy_hit_rate'] for d in docs.values() if d['proxy_hit_rate'] is not None]
    compl_counts = {}
    for d in docs.values():
        c = d['completeness']
        compl_counts[c] = compl_counts.get(c, 0) + 1

    summary = {
        'total': len(docs),
        'with_ground_truth': sum(1 for d in docs.values() if d['has_ground_truth']),
        'completeness': compl_counts,
        'proxy_median': statistics.median(hit_rates) if hit_rates else None,
        'proxy_mean': statistics.mean(hit_rates) if hit_rates else None,
        'quality_buckets': {k: v for k, v in buckets.items() if v > 0},
    }

    output = {
        'generated': datetime.now().isoformat(),
        'generator': 'scripts/generate_diagnostik.py --corpus',
        'summary': summary,
        'docs': docs,
    }

    DOCS_DATA_DIR.mkdir(parents=True, exist_ok=True)
    json_text = json.dumps(output, indent=2, ensure_ascii=False, default=str)
    DIAGNOSTIK_CORPUS_JSON.write_text(json_text, encoding='utf-8')
    print(f"\n  Output: {DIAGNOSTIK_CORPUS_JSON}")
    print(f"  Summary: {summary}")

    return 0


def add_pagewise_to_ocr():
    """Erweitert diagnostik_ocr.json um Pagewise-CER und Referenz-Vergleich."""
    if not DIAGNOSTIK_JSON.exists():
        print("  WARNUNG: diagnostik_ocr.json nicht gefunden -- ueberspringe Pagewise")
        return

    ocr_data = json.loads(DIAGNOSTIK_JSON.read_text(encoding='utf-8'))

    # Pagewise-Daten einlesen
    if BENCHMARK_PAGEWISE_JSON.exists():
        pw_raw = json.loads(BENCHMARK_PAGEWISE_JSON.read_text(encoding='utf-8'))
        pw_report = pw_raw.get('outlier_report', {})
        pw_docs = pw_raw.get('pagewise', {})

        # Nur Fokus-Docs (mit Outlier-Seiten) detailliert aufnehmen
        focus_docs = {}
        for doc_id, pw in pw_docs.items():
            outlier_count = len([p for p in pw.get('page_results', []) if p.get('cer', 0) > 0.10])
            if outlier_count > 0:
                focus_docs[doc_id] = {
                    'page_count': pw.get('page_count', 0),
                    'cer': pw.get('cer', 0),
                    'outlier_count': outlier_count,
                    'pages': pw.get('page_results', []),
                }

        ocr_data['pagewise'] = {
            'outlier_summary': {
                'total_pages': pw_report.get('total_pages_evaluated', 0),
                'outlier_pages': pw_report.get('total_outlier_pages', 0),
                'outlier_rate': pw_report.get('outlier_rate', 0),
                'threshold': pw_report.get('threshold', 0.10),
            },
            'top_outliers': pw_report.get('outliers', [])[:20],
            'focus_docs': focus_docs,
        }
        print(f"  Pagewise: {pw_report.get('total_outlier_pages', 0)} Outlier-Seiten, "
              f"{len(focus_docs)} Fokus-Docs")
    else:
        print("  WARNUNG: benchmark_pagewise.json nicht gefunden")

    # Referenz-Vergleich einlesen
    if REFERENCE_COMPARISON_JSON.exists():
        ref_raw = json.loads(REFERENCE_COMPARISON_JSON.read_text(encoding='utf-8'))
        ref_docs = ref_raw.get('documents', {})
        comparison = []
        for doc_id, d in sorted(ref_docs.items()):
            if d.get('status') != 'OK':
                continue
            comparison.append({
                'doc_id': doc_id,
                'cer': d.get('cer', 0),
                'wer': d.get('wer', 0),
                'ref_chars': d.get('ref_chars', 0),
                'scope_mismatch': d.get('scope_mismatch', False),
                'language': d.get('metadata', {}).get('language', '?'),
                'type': d.get('metadata', {}).get('type', '?'),
            })
        ocr_data['reference_comparison'] = comparison
        print(f"  Referenz-Vergleich: {len(comparison)} Docs")
    else:
        print("  WARNUNG: benchmark_tei_vs_tei.json nicht gefunden")

    # Zurueckschreiben
    ocr_data['generated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    json_text = json.dumps(ocr_data, indent=2, ensure_ascii=False, default=str)
    DIAGNOSTIK_JSON.write_text(json_text, encoding='utf-8')
    print(f"  Aktualisiert: {DIAGNOSTIK_JSON}")


def generate_entities_json():
    """Generiert diagnostik_entities.json mit Entity-Linking-Diagnostik."""
    print("\n=== Generiere diagnostik_entities.json ===\n")

    from scripts.ner.entity_index import EntityIndex
    from scripts.ner.ner_evaluate import corpus_summary_by_language, corpus_summary

    # Entity-Index laden + Diagnostik
    index = EntityIndex()
    index.load_all()
    diag = index.diagnostics()

    # Sprach-Stratifizierung
    lang_data = corpus_summary_by_language()
    corpus = corpus_summary()

    # Typ-Verteilung mit Linking-Status
    by_type = {}
    for entity_type, td in diag.get('by_type', {}).items():
        total = td['total']
        linked = td['linked']
        by_type[entity_type] = {
            'total': total,
            'linked': linked,
            'unlinked': td['unlinked'],
            'linked_pct': round(linked / max(total, 1) * 100, 1),
            'top_unlinked': td['unlinked_entries'][:10],
        }

    # Sprach-Metriken
    by_language = {}
    for lang, stats in lang_data.get('by_language', {}).items():
        by_language[lang] = {
            'documents': stats['documents'],
            'total_entities': stats['total_entities'],
            'total_mentions': stats['total_mentions'],
            'avg_density': stats['avg_density_per_page'],
            'resolution_rate': stats['resolution_rate'],
            'type_distribution': stats['type_distribution'],
        }

    # Top-20 unverlinkte Entities (alle Typen gemischt, nach Mentions)
    all_unlinked = []
    for entity_type, td in diag.get('by_type', {}).items():
        for entry in td.get('unlinked_entries', []):
            all_unlinked.append({**entry, 'type': entity_type})
    all_unlinked.sort(key=lambda x: -x.get('mention_count', 0))

    output = {
        'generated': datetime.now().isoformat(),
        'generator': 'scripts/generate_diagnostik.py --entities',
        'summary': {
            'total': diag['total'],
            'linked': diag['linked'],
            'unlinked': diag['unlinked'],
            'linked_pct': round(diag['linked'] / max(diag['total'], 1) * 100, 1),
            'corpus_entities': corpus.get('total_entities', 0),
            'corpus_mentions': corpus.get('total_mentions', 0),
            'corpus_documents': corpus.get('documents', 0),
            'resolution_rate': corpus.get('resolution_rate', 0),
        },
        'by_type': by_type,
        'by_language': by_language,
        'top_unlinked': all_unlinked[:20],
    }

    DOCS_DATA_DIR.mkdir(parents=True, exist_ok=True)
    json_text = json.dumps(output, indent=2, ensure_ascii=False, default=str)
    DIAGNOSTIK_ENTITIES_JSON.write_text(json_text, encoding='utf-8')
    print(f"  Output: {DIAGNOSTIK_ENTITIES_JSON}")
    print(f"  Total: {diag['total']}, Linked: {diag['linked']} ({output['summary']['linked_pct']}%)")
    for t, td in by_type.items():
        print(f"    {t}: {td['total']} ({td['linked_pct']}% linked)")

    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Diagnostik-Daten generieren")
    parser.add_argument('--corpus', action='store_true',
                        help='Corpus-JSON generieren (konsolidierte Qualitaetsprofile)')
    parser.add_argument('--entities', action='store_true',
                        help='Entity-JSON generieren (Linking-Diagnostik, Sprach-Eval)')
    parser.add_argument('--pagewise', action='store_true',
                        help='Pagewise-CER + Referenz-Vergleich in OCR-JSON einfuegen')
    parser.add_argument('--all', action='store_true',
                        help='Alles generieren (OCR + Corpus + Entities + Pagewise)')
    parser.add_argument('--corpus-only', action='store_true',
                        help='Nur Corpus-JSON generieren (kein OCR-Benchmark)')
    args = parser.parse_args()

    rc = 0
    if not args.corpus_only:
        rc = main() or 0
    if args.pagewise or args.all:
        add_pagewise_to_ocr()
    if args.corpus or args.all or args.corpus_only:
        rc = generate_corpus_json() or rc
    if args.entities or args.all:
        rc = generate_entities_json() or rc

    exit(rc)
