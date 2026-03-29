"""
End-to-End CER Benchmark: Vergleicht Pipeline-TEIs mit ZBZ-Referenz-TEIs.

Stratifizierte Analyse nach Dokumenttyp, Sprache und Publikationsform.
Fehlermuster-Kategorisierung und optionale Proxy-Metriken.

Usage:
    python -m scripts.benchmark_cer [--all] [--docs 2310 290] [--proxy] [--html]
"""

import json
import argparse
import statistics
from pathlib import Path
from datetime import datetime

from scripts.config import (
    REFERENZ_TEI_DIR, TEI_FINAL_DIR, EVALUATION_DIR, DOC_METADATA_PATH,
)
from scripts.evaluate_ocr import (
    evaluate_tei_vs_tei, categorize_errors, evaluate_tei_vs_tei_pagewise,
)


def load_metadata() -> dict:
    """Laedt doc_metadata.json und gibt Dict {doc_id: metadata} zurueck."""
    if not DOC_METADATA_PATH.exists():
        return {}
    with open(DOC_METADATA_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
    docs = data.get('documents', data)
    result = {}
    for doc_id, meta in docs.items():
        if isinstance(meta, dict):
            # Feld-Normalisierung: layout_type -> type
            if 'layout_type' in meta and 'type' not in meta:
                meta['type'] = meta['layout_type']
            result[doc_id] = meta
    return result


def get_ground_truth_doc_ids(ref_dir: Path) -> list[str]:
    """Findet alle Dokument-IDs mit Referenz-TEI (ohne Pilot-Unterordner-Duplikate)."""
    ids = set()
    for p in ref_dir.glob('*.xml'):
        ids.add(p.stem)
    for p in (ref_dir / 'Pilot').glob('*.xml'):
        stem = p.stem.split(' ')[0]  # "1520 - in Arbeit.xml" -> "1520"
        ids.add(stem)
    return sorted(ids)


def compute_stratum_stats(results: list[dict]) -> dict:
    """Berechnet Aggregat-Statistiken fuer eine Gruppe von Evaluierungen."""
    if not results:
        return {'count': 0, 'avg_cer': 0, 'median_cer': 0, 'std_cer': 0,
                'min_cer': 0, 'max_cer': 0, 'avg_wer': 0}
    cers = [r['cer'] for r in results]
    wers = [r['wer'] for r in results]
    return {
        'count': len(results),
        'avg_cer': statistics.mean(cers),
        'median_cer': statistics.median(cers),
        'std_cer': statistics.stdev(cers) if len(cers) > 1 else 0.0,
        'min_cer': min(cers),
        'max_cer': max(cers),
        'avg_wer': statistics.mean(wers),
        'doc_ids': [r['doc_id'] for r in results],
    }


def stratify_results(results: list[dict], metadata: dict) -> dict:
    """Gruppiert Ergebnisse nach Typ, Sprache, Publikationsform und Seitenumfang."""
    strata = {
        'by_type': {},
        'by_language': {},
        'by_form': {},
        'by_size': {},
    }

    for r in results:
        doc_id = r['doc_id']
        meta = metadata.get(doc_id, {})

        # Nach Layout-Typ
        layout_type = meta.get('type', 'unknown')
        strata['by_type'].setdefault(layout_type, []).append(r)

        # Nach Sprache (vereinfacht: Hauptsprache)
        lang = meta.get('language', 'unknown')
        strata['by_language'].setdefault(lang, []).append(r)

        # Nach Publikationsform
        form = meta.get('pub_form', 'unknown')
        strata['by_form'].setdefault(form, []).append(r)

        # Nach Seitenumfang
        pages = meta.get('page_count', 0)
        if pages <= 5:
            size = 'short'
        elif pages <= 20:
            size = 'medium'
        else:
            size = 'long'
        strata['by_size'].setdefault(size, []).append(r)

    # Stats pro Stratum berechnen
    return {
        dim: {key: compute_stratum_stats(docs) for key, docs in groups.items()}
        for dim, groups in strata.items()
    }


def aggregate_error_patterns(results: list[dict], metadata: dict) -> dict:
    """Aggregiert Fehlermuster ueber alle Dokumente und pro Stratum."""
    categories = ['diacritics', 'punctuation', 'hyphenation', 'whitespace',
                  'ocr_artifact', 'layout', 'other']

    def _agg(docs):
        totals = {c: {'total_count': 0, 'total_cer_contrib': 0.0} for c in categories}
        for r in docs:
            for cat_name in categories:
                cat_data = r.get('error_categories', {}).get(cat_name, {})
                totals[cat_name]['total_count'] += cat_data.get('count', 0)
                totals[cat_name]['total_cer_contrib'] += cat_data.get('cer_contribution', 0)
        n = max(len(docs), 1)
        for cat_name in categories:
            totals[cat_name]['avg_cer_contrib'] = totals[cat_name]['total_cer_contrib'] / n
        return totals

    patterns = {'overall': _agg(results)}

    # Pro Layout-Typ
    by_type = {}
    for r in results:
        t = metadata.get(r['doc_id'], {}).get('type', 'unknown')
        by_type.setdefault(t, []).append(r)
    patterns['by_type'] = {t: _agg(docs) for t, docs in by_type.items()}

    # Pro Sprache
    by_lang = {}
    for r in results:
        lang = metadata.get(r['doc_id'], {}).get('language', 'unknown')
        by_lang.setdefault(lang, []).append(r)
    patterns['by_language'] = {l: _agg(docs) for l, docs in by_lang.items()}

    return patterns


def build_outlier_report(pagewise_results: dict, threshold: float = 0.10) -> dict:
    """Identifiziert Outlier-Seiten (CER > threshold) ueber alle Dokumente."""
    outliers = []
    total_pages = 0

    for doc_id, pw in pagewise_results.items():
        if pw.get('status') != 'OK':
            continue
        for pr in pw.get('page_results', []):
            total_pages += 1
            if pr['cer'] > threshold:
                outliers.append({
                    'doc_id': doc_id,
                    'page': pr['page'],
                    'cer': pr['cer'],
                    'wer': pr.get('wer', 0),
                    'ref_chars': pr.get('ref_chars', 0),
                })

    outliers.sort(key=lambda x: -x['cer'])

    return {
        'threshold': threshold,
        'total_pages_evaluated': total_pages,
        'total_outlier_pages': len(outliers),
        'outlier_rate': round(len(outliers) / max(total_pages, 1), 3),
        'outliers': outliers,
    }


def generate_benchmark_html(data: dict, output_path: Path):
    """Generiert HTML-Benchmark-Report."""
    summary = data['summary']
    docs = data['documents']
    strat = data['stratified']

    # CSS-Balken-Breite (max 100% bei CER 15%)
    def bar_width(cer):
        return min(cer / 0.15 * 100, 100)

    def cer_class(cer):
        if cer < 0.03:
            return 'good'
        elif cer < 0.08:
            return 'acceptable'
        return 'problematic'

    html_parts = [f"""<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<title>CER Benchmark: TEI vs. TEI</title>
<style>
* {{ box-sizing: border-box; }}
body {{ font-family: 'Segoe UI', sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }}
.container {{ max-width: 1200px; margin: 0 auto; }}
h1 {{ color: #333; border-bottom: 3px solid #2196F3; padding-bottom: 10px; }}
h2 {{ color: #555; margin-top: 30px; }}
.cards {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 16px; margin: 16px 0; }}
.card {{ background: white; padding: 16px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); text-align: center; }}
.card .value {{ font-size: 2em; font-weight: bold; }}
.card .label {{ color: #666; margin-top: 4px; font-size: 0.9em; }}
.card.good .value {{ color: #4CAF50; }}
.card.acceptable .value {{ color: #FF9800; }}
.card.problematic .value {{ color: #f44336; }}
table {{ width: 100%; border-collapse: collapse; background: white; border-radius: 8px; overflow: hidden;
         box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin: 16px 0; }}
th {{ background: #2196F3; color: white; padding: 10px 12px; text-align: left; }}
td {{ padding: 8px 12px; border-bottom: 1px solid #eee; }}
tr:hover {{ background: #f0f7ff; }}
.bar-cell {{ position: relative; min-width: 120px; }}
.bar {{ height: 20px; border-radius: 3px; }}
.bar.good {{ background: #4CAF50; }}
.bar.acceptable {{ background: #FF9800; }}
.bar.problematic {{ background: #f44336; }}
.bar-label {{ position: absolute; right: 8px; top: 50%; transform: translateY(-50%); font-size: 0.85em; font-weight: bold; }}
.note {{ color: #888; font-size: 0.85em; margin: 8px 0; }}
.timestamp {{ color: #999; text-align: center; margin-top: 30px; font-size: 0.9em; }}
</style>
</head>
<body>
<div class="container">
<h1>CER Benchmark: Pipeline-TEI vs. Referenz-TEI</h1>
<p class="note">End-to-End-Vergleich der generierten TEIs gegen ZBZ Ground Truth (Transkribus).
Fussnoten exkludiert. Alignment bei Laengendifferenz.</p>

<div class="cards">
<div class="card"><div class="value">{summary['total_documents']}</div><div class="label">Dokumente</div></div>
<div class="card {cer_class(summary['avg_cer'])}"><div class="value">{summary['avg_cer']*100:.1f}%</div><div class="label">Mittlere CER</div></div>
<div class="card"><div class="value">{summary['median_cer']*100:.1f}%</div><div class="label">Median CER</div></div>
<div class="card"><div class="value">{summary['avg_wer']*100:.1f}%</div><div class="label">Mittlere WER</div></div>
</div>
"""]

    # Stratifizierte Tabellen
    for dim_key, dim_label in [('by_type', 'Layout-Typ'), ('by_language', 'Sprache'),
                                ('by_form', 'Publikationsform'), ('by_size', 'Seitenumfang')]:
        dim_data = strat.get(dim_key, {})
        if not dim_data:
            continue
        html_parts.append(f"<h2>Nach {dim_label}</h2>\n<table><tr><th>{dim_label}</th>"
                          "<th>n</th><th>CER (Mittel)</th><th>CER (Median)</th>"
                          "<th>Min</th><th>Max</th><th></th></tr>")
        for key in sorted(dim_data.keys()):
            s = dim_data[key]
            avg = s['avg_cer']
            html_parts.append(
                f"<tr><td><b>{key}</b></td><td>{s['count']}</td>"
                f"<td>{avg*100:.1f}%</td><td>{s['median_cer']*100:.1f}%</td>"
                f"<td>{s['min_cer']*100:.1f}%</td><td>{s['max_cer']*100:.1f}%</td>"
                f"<td class='bar-cell'><div class='bar {cer_class(avg)}' "
                f"style='width:{bar_width(avg):.0f}%'></div></td></tr>"
            )
        html_parts.append("</table>")

    # Einzeldokument-Tabelle
    html_parts.append("<h2>Einzeldokumente</h2>\n<table><tr><th>Doc</th><th>Typ</th>"
                      "<th>Sprache</th><th>CER</th><th>WER</th><th>Ref-Zeichen</th>"
                      "<th></th></tr>")
    for doc_id in sorted(docs.keys(), key=lambda d: docs[d].get('cer', 0), reverse=True):
        d = docs[doc_id]
        if d.get('status') != 'OK':
            continue
        cer = d['cer']
        meta = d.get('metadata', {})
        html_parts.append(
            f"<tr><td><b>{doc_id}</b></td><td>{meta.get('type','?')}</td>"
            f"<td>{meta.get('language','?')}</td>"
            f"<td>{cer*100:.1f}%</td><td>{d['wer']*100:.1f}%</td>"
            f"<td>{d['ref_chars']}</td>"
            f"<td class='bar-cell'><div class='bar {cer_class(cer)}' "
            f"style='width:{bar_width(cer):.0f}%'></div></td></tr>"
        )
    html_parts.append("</table>")

    # Fehlermuster-Tabelle
    patterns = data.get('error_patterns', {}).get('overall', {})
    if patterns:
        html_parts.append("<h2>Fehlermuster (gesamt)</h2>\n<table><tr><th>Kategorie</th>"
                          "<th>Anzahl</th><th>Mittl. CER-Beitrag</th></tr>")
        for cat in sorted(patterns.keys(), key=lambda c: patterns[c].get('avg_cer_contrib', 0),
                          reverse=True):
            p = patterns[cat]
            if p['total_count'] == 0:
                continue
            html_parts.append(
                f"<tr><td>{cat}</td><td>{p['total_count']}</td>"
                f"<td>{p['avg_cer_contrib']*100:.2f}%</td></tr>"
            )
        html_parts.append("</table>")

    # Pagewise Outlier-Report
    outlier_report = data.get('outlier_report', {})
    if outlier_report and outlier_report.get('outliers'):
        html_parts.append(
            f"<h2>Outlier-Seiten (CER &gt; {outlier_report['threshold']*100:.0f}%)</h2>"
            f"<p class='note'>{outlier_report['total_outlier_pages']} von "
            f"{outlier_report['total_pages_evaluated']} Seiten "
            f"({outlier_report['outlier_rate']*100:.1f}%)</p>"
            "<table><tr><th>Doc</th><th>Seite</th><th>CER</th><th>WER</th>"
            "<th>Ref-Zeichen</th><th></th></tr>"
        )
        for o in outlier_report['outliers'][:50]:  # Top 50
            cer = o['cer']
            html_parts.append(
                f"<tr><td><b>{o['doc_id']}</b></td><td>S.{o['page']}</td>"
                f"<td>{cer*100:.1f}%</td><td>{o['wer']*100:.1f}%</td>"
                f"<td>{o['ref_chars']}</td>"
                f"<td class='bar-cell'><div class='bar {cer_class(cer)}' "
                f"style='width:{bar_width(cer):.0f}%'></div></td></tr>"
            )
        html_parts.append("</table>")

    # Per-Doc Pagewise Details (nur fuer Docs mit Outliers)
    pagewise_data = data.get('pagewise', {})
    focus_docs = {o['doc_id'] for o in outlier_report.get('outliers', [])}
    if pagewise_data and focus_docs:
        html_parts.append("<h2>Seitendetails (Fokus-Dokumente)</h2>")
        for doc_id in sorted(focus_docs):
            pw = pagewise_data.get(doc_id)
            if not pw:
                continue
            html_parts.append(
                f"<h3>Doc {doc_id} (CER {pw['cer']*100:.1f}%, "
                f"{pw['page_count']} Seiten)</h3>"
                "<table><tr><th>Seite</th><th>CER</th><th>Ref-Zeichen</th>"
                "<th></th></tr>"
            )
            for pr in pw.get('page_results', []):
                cer = pr['cer']
                html_parts.append(
                    f"<tr><td>S.{pr['page']}</td>"
                    f"<td>{cer*100:.1f}%</td>"
                    f"<td>{pr['ref_chars']}</td>"
                    f"<td class='bar-cell'><div class='bar {cer_class(cer)}' "
                    f"style='width:{bar_width(cer):.0f}%'></div></td></tr>"
                )
            html_parts.append("</table>")

    html_parts.append(f"""
<div class="timestamp">Generiert: {data['generated']}</div>
</div></body></html>""")

    output_path.write_text('\n'.join(html_parts), encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(
        description="End-to-End CER Benchmark: Pipeline-TEI vs. Referenz-TEI"
    )
    parser.add_argument("--docs", nargs='+', help="Spezifische Dokument-IDs")
    parser.add_argument("--all", action="store_true", default=True,
                        help="Alle Ground-Truth-Docs evaluieren (Default)")
    parser.add_argument("--proxy", action="store_true",
                        help="Proxy-Metriken fuer Docs ohne Ground Truth berechnen")
    parser.add_argument("--html", action="store_true", default=True,
                        help="HTML-Report generieren (Default)")
    parser.add_argument("--json-output", default="benchmark_tei_vs_tei.json",
                        help="Name der JSON-Ausgabedatei")
    parser.add_argument("--ref-dir", type=Path, default=None,
                        help="Referenz-TEI-Verzeichnis (Default: data/referenz-tei)")
    parser.add_argument("--pipe-dir", type=Path, default=None,
                        help="Pipeline-TEI-Verzeichnis (Default: output/tei_final)")
    parser.add_argument("--pagewise", action="store_true",
                        help="Seitenweise CER berechnen und Outlier-Report generieren")
    args = parser.parse_args()

    ref_dir = args.ref_dir or REFERENZ_TEI_DIR
    pipe_dir = args.pipe_dir or TEI_FINAL_DIR
    EVALUATION_DIR.mkdir(parents=True, exist_ok=True)

    # Dokument-IDs bestimmen
    if args.docs:
        doc_ids = args.docs
    else:
        doc_ids = get_ground_truth_doc_ids(ref_dir)

    # Metadaten laden
    metadata = load_metadata()

    print(f"CER Benchmark: TEI vs. TEI")
    print(f"==========================")
    print(f"Referenz: {ref_dir}")
    print(f"Pipeline: {pipe_dir}")
    print(f"Dokumente: {len(doc_ids)}")
    print()

    # Evaluation
    results = []
    doc_results = {}

    for doc_id in doc_ids:
        r = evaluate_tei_vs_tei(doc_id, ref_dir, pipe_dir)

        meta = metadata.get(doc_id, {})
        r['metadata'] = {
            'type': meta.get('type', '?'),
            'language': meta.get('language', '?'),
            'pub_form': meta.get('pub_form', '?'),
            'page_count': meta.get('page_count', 0),
        }

        doc_results[doc_id] = r

        if r['status'] == 'OK':
            results.append(r)
            status_icon = 'OK' if r['cer'] < 0.05 else 'WARN' if r['cer'] < 0.10 else 'HIGH'
            print(f"  {doc_id:>5} [{meta.get('type','?'):>1}] "
                  f"CER={r['cer']*100:5.1f}%  WER={r['wer']*100:5.1f}%  "
                  f"({r['ref_chars']} Zeichen) [{status_icon}]")
        elif r['status'] == 'MISMATCH':
            doc_results[doc_id] = r
            print(f"  {doc_id:>5} [{meta.get('type','?'):>1}] "
                  f"[MISMATCH] CER={r['cer']*100:.0f}% -- Texte stimmen nicht ueberein")
        else:
            print(f"  {doc_id:>5} [SKIP] {r.get('error', '')}")

    print()

    # Pagewise Analyse (optional)
    pagewise_results = {}
    if args.pagewise:
        print("Seitenweise Analyse...")
        for doc_id in doc_ids:
            pw = evaluate_tei_vs_tei_pagewise(doc_id, ref_dir, pipe_dir)
            if pw['status'] == 'OK':
                pagewise_results[doc_id] = pw
                n_outliers = len(pw.get('outlier_pages', []))
                marker = f" [{n_outliers} Outlier]" if n_outliers else ""
                print(f"  {doc_id:>5}: {pw['page_count']} Seiten, "
                      f"CER={pw['cer']*100:.1f}%{marker}")
            else:
                print(f"  {doc_id:>5}: [SKIP] {pw.get('error', '')}")
        print()

    # Zusammenfassung
    if not results:
        print("Keine Dokumente evaluiert.")
        return 1

    cers = [r['cer'] for r in results]
    wers = [r['wer'] for r in results]
    summary = {
        'total_documents': len(results),
        'evaluated': len(results),
        'skipped': len(doc_ids) - len(results),
        'avg_cer': statistics.mean(cers),
        'median_cer': statistics.median(cers),
        'std_cer': statistics.stdev(cers) if len(cers) > 1 else 0.0,
        'min_cer': min(cers),
        'max_cer': max(cers),
        'avg_wer': statistics.mean(wers),
    }

    # Stratifizierung
    stratified = stratify_results(results, metadata)

    # Fehlermuster
    error_patterns = aggregate_error_patterns(results, metadata)

    # Output zusammenstellen
    output = {
        'generated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'generator': 'scripts/benchmark_cer.py',
        'comparison': 'tei_vs_tei',
        'ref_source': str(ref_dir),
        'hyp_source': str(pipe_dir),
        'summary': summary,
        'documents': doc_results,
        'stratified': stratified,
        'error_patterns': error_patterns,
    }

    # Pagewise-Daten hinzufuegen
    if pagewise_results:
        outlier_report = build_outlier_report(pagewise_results)
        output['pagewise'] = {
            doc_id: {
                'cer': pw['cer'],
                'wer': pw['wer'],
                'page_count': pw['page_count'],
                'page_results': pw['page_results'],
                'outlier_pages': pw['outlier_pages'],
            }
            for doc_id, pw in pagewise_results.items()
        }
        output['outlier_report'] = outlier_report

    # Proxy-Metriken
    if args.proxy:
        from scripts.evaluate_ocr import compute_proxy_quality
        proxy_data = {}
        pipe_files = sorted(pipe_dir.glob('*_final.xml'))
        gt_set = set(doc_ids)
        proxy_doc_ids = [p.stem.replace('_final', '') for p in pipe_files
                         if p.stem.replace('_final', '') not in gt_set]

        print(f"Proxy-Metriken fuer {len(proxy_doc_ids)} Docs ohne Ground Truth...")
        for did in proxy_doc_ids:
            proxy_data[did] = compute_proxy_quality(did)

        # Kalibrierung: Korrelation Proxy-Score vs. echte CER
        calibration_pairs = []
        for r in results:
            proxy = compute_proxy_quality(r['doc_id'])
            if proxy.get('proxy_score') is not None:
                calibration_pairs.append((proxy['proxy_score'], r['cer']))

        output['proxy_metrics'] = {
            'calibration_pairs': len(calibration_pairs),
            'documents': proxy_data,
            'corpus_quality_estimate': {
                bucket: sum(1 for p in proxy_data.values()
                            if p.get('estimated_cer_bucket') == bucket)
                for bucket in ['excellent', 'good', 'fair', 'poor', 'unknown']
            },
        }
        print(f"  Kalibrierung: {len(calibration_pairs)} Paare")

    # JSON speichern
    json_path = EVALUATION_DIR / args.json_output
    # Nicht-serialisierbare Werte bereinigen
    json_text = json.dumps(output, indent=2, ensure_ascii=False, default=str)
    json_path.write_text(json_text, encoding='utf-8')
    print(f"\nJSON: {json_path}")

    # HTML-Report
    if args.html:
        html_path = EVALUATION_DIR / args.json_output.replace('.json', '.html')
        generate_benchmark_html(output, html_path)
        print(f"HTML: {html_path}")

    # Zusammenfassung
    print(f"\n{'='*50}")
    print(f"ZUSAMMENFASSUNG")
    print(f"{'='*50}")
    print(f"Dokumente:       {summary['total_documents']}")
    print(f"Mittlere CER:    {summary['avg_cer']*100:.2f}%")
    print(f"Median CER:      {summary['median_cer']*100:.2f}%")
    print(f"Std CER:         {summary['std_cer']*100:.2f}%")
    print(f"Min/Max CER:     {summary['min_cer']*100:.2f}% / {summary['max_cer']*100:.2f}%")
    print(f"Mittlere WER:    {summary['avg_wer']*100:.2f}%")

    # Stratifizierte Zusammenfassung
    print(f"\nNach Layout-Typ:")
    for t, s in sorted(stratified['by_type'].items()):
        print(f"  {t}: n={s['count']}, CER={s['avg_cer']*100:.1f}% "
              f"(median={s['median_cer']*100:.1f}%)")

    print(f"\nNach Sprache:")
    for l, s in sorted(stratified['by_language'].items()):
        print(f"  {l}: n={s['count']}, CER={s['avg_cer']*100:.1f}%")

    if pagewise_results:
        outlier_report = output.get('outlier_report', {})
        print(f"\nSeitenweise Analyse:")
        print(f"  Seiten evaluiert: {outlier_report.get('total_pages_evaluated', 0)}")
        print(f"  Outlier (>10%):   {outlier_report.get('total_outlier_pages', 0)} "
              f"({outlier_report.get('outlier_rate', 0)*100:.1f}%)")
        if outlier_report.get('outliers'):
            print(f"  Top-5 Outlier:")
            for o in outlier_report['outliers'][:5]:
                print(f"    Doc {o['doc_id']} S.{o['page']}: "
                      f"CER={o['cer']*100:.1f}%")

    return 0


if __name__ == "__main__":
    exit(main() or 0)
