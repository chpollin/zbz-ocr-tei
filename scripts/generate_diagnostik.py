"""
Generiert docs/data/diagnostik_ocr.json fuer das OCR-Diagnostik-Dashboard.

Inhalt:
  - baseline_comparison: CER vor/nach Normalisierungskorrektur (24 Docs)
  - confusion_matrix: Zeichenweise Substitutionen, Insertions, Deletions
  - outlier_diagnosis: Einzelanalyse der 4 verschlechterten Docs
  - per_doc: CER, WER, Fehlerkategorien, Metadata pro Doc
  - pipeline_effect: OCR-Baseline-CER vs. End-to-End-CER

Usage:
    python -m scripts.generate_diagnostik
"""

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
DIAGNOSTIK_LOG = DOCS_DATA_DIR / "diagnostik_log.json"

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


if __name__ == "__main__":
    exit(main() or 0)
