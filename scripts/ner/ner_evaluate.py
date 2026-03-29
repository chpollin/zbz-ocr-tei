"""
NER Evaluation: Metriken + optionaler Ground-Truth-Vergleich.

Berechnet automatische Metriken (Entity-Dichte, Typ-Verteilung,
Surface-Validierung) und optional Precision/Recall gegen Ground Truth.

Aufruf:
    python -m scripts.ner.ner_evaluate --summary
    python -m scripts.ner.ner_evaluate --doc 2310
    python -m scripts.ner.ner_evaluate --gt data/ground_truth/2310_gt.json --doc 2310
"""

import argparse
import json
import sys
import unicodedata
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.config import ENTITIES_DIR, PROJECT_ROOT, DOC_METADATA_PATH
from scripts.ner.entity_index import EntityIndex
from scripts.ner.entity_store import EntityStore


def _strip_diacritics(text: str) -> str:
    """Strip diacritics for lenient matching."""
    nfkd = unicodedata.normalize('NFKD', text)
    return ''.join(c for c in nfkd if not unicodedata.combining(c)).lower()


def _load_language_map() -> dict:
    """Laedt {doc_id: language_code} aus doc_metadata.json."""
    if not DOC_METADATA_PATH.exists():
        return {}
    data = json.loads(DOC_METADATA_PATH.read_text(encoding='utf-8'))
    docs = data.get('documents', data)
    return {
        did: meta.get('language', 'unknown')
        for did, meta in docs.items()
        if isinstance(meta, dict)
    }


def doc_report(doc_id: str) -> dict:
    """Bericht fuer ein einzelnes Dokument."""
    store = EntityStore.load(doc_id)
    if not store.entities:
        return {"doc_id": doc_id, "error": "no_entities"}

    summary = store.summary()

    # Entity-Dichte (Entities pro Seite)
    all_pages = set()
    for rec in store.entities.values():
        all_pages.update(rec.pages)
    n_pages = len(all_pages) or 1
    density = round(summary["total_entities"] / n_pages, 1)

    # Typ-Verteilung
    type_pct = {}
    total = summary["total_entities"] or 1
    for t, ts in summary["by_type"].items():
        if ts["total"] > 0:
            type_pct[t] = round(ts["total"] / total * 100, 1)

    return {
        "doc_id": doc_id,
        "pages": n_pages,
        "total_entities": summary["total_entities"],
        "total_mentions": summary["total_mentions"],
        "density_per_page": density,
        "mentions_per_entity": round(
            summary["total_mentions"] / total, 1
        ),
        "resolved": summary["resolved"],
        "resolution_rate": summary["resolution_rate"],
        "type_distribution": type_pct,
        "by_type": {
            t: ts for t, ts in summary["by_type"].items() if ts["total"] > 0
        },
    }


def corpus_summary() -> dict:
    """Aggregierte Metriken ueber alle verarbeiteten Dokumente."""
    if not ENTITIES_DIR.exists():
        return {"error": "no_entity_data"}

    doc_ids = sorted(
        d.name for d in ENTITIES_DIR.iterdir()
        if d.is_dir() and not d.name.startswith("_")
    )

    docs = []
    total_ents = 0
    total_mentions = 0
    total_resolved = 0
    total_pages = 0
    type_totals = {}

    for doc_id in doc_ids:
        report = doc_report(doc_id)
        if "error" in report:
            continue
        docs.append(report)
        total_ents += report["total_entities"]
        total_mentions += report["total_mentions"]
        total_resolved += report["resolved"]
        total_pages += report["pages"]
        for t, pct in report["type_distribution"].items():
            type_totals.setdefault(t, 0)
            type_totals[t] += report["by_type"].get(t, {}).get("total", 0)

    # Typ-Verteilung ueber Korpus
    type_pct = {}
    for t, count in type_totals.items():
        type_pct[t] = round(count / (total_ents or 1) * 100, 1)

    return {
        "documents": len(docs),
        "total_pages": total_pages,
        "total_entities": total_ents,
        "total_mentions": total_mentions,
        "avg_entities_per_doc": round(total_ents / (len(docs) or 1), 1),
        "avg_density_per_page": round(total_ents / (total_pages or 1), 1),
        "avg_mentions_per_entity": round(
            total_mentions / (total_ents or 1), 1
        ),
        "resolved": total_resolved,
        "resolution_rate": round(
            total_resolved / (total_ents or 1), 3
        ),
        "type_distribution": type_pct,
    }


def corpus_summary_by_language() -> dict:
    """NER-Metriken gruppiert nach Dokumentsprache."""
    if not ENTITIES_DIR.exists():
        return {"error": "no_entity_data"}

    lang_map = _load_language_map()

    doc_ids = sorted(
        d.name for d in ENTITIES_DIR.iterdir()
        if d.is_dir() and not d.name.startswith("_")
    )

    # Gruppiere Reports nach Sprache
    by_lang = {}  # lang -> list of doc_reports
    for doc_id in doc_ids:
        report = doc_report(doc_id)
        if "error" in report:
            continue
        lang = lang_map.get(doc_id, "unknown")
        # Normalisiere mehrsprachige Codes (z.B. "fra/deu" -> "multilingual")
        if "/" in lang:
            lang = "multilingual"
        by_lang.setdefault(lang, []).append(report)

    # Aggregiere pro Sprache
    result = {}
    for lang, reports in sorted(by_lang.items()):
        total_ents = sum(r["total_entities"] for r in reports)
        total_mentions = sum(r["total_mentions"] for r in reports)
        total_resolved = sum(r["resolved"] for r in reports)
        total_pages = sum(r["pages"] for r in reports)

        type_totals = {}
        for r in reports:
            for t, ts in r.get("by_type", {}).items():
                type_totals[t] = type_totals.get(t, 0) + ts.get("total", 0)

        type_pct = {
            t: round(count / (total_ents or 1) * 100, 1)
            for t, count in type_totals.items()
        }

        result[lang] = {
            "documents": len(reports),
            "total_pages": total_pages,
            "total_entities": total_ents,
            "total_mentions": total_mentions,
            "avg_entities_per_doc": round(total_ents / (len(reports) or 1), 1),
            "avg_density_per_page": round(total_ents / (total_pages or 1), 1),
            "avg_mentions_per_entity": round(
                total_mentions / (total_ents or 1), 1
            ),
            "resolved": total_resolved,
            "resolution_rate": round(
                total_resolved / (total_ents or 1), 3
            ),
            "type_distribution": type_pct,
        }

    return {
        "by_language": result,
        "languages": sorted(result.keys()),
    }


def evaluate_ground_truth(doc_id: str, gt_path: str,
                          lenient: bool = False) -> dict:
    """Precision/Recall gegen manuell annotiertes Ground Truth.

    Ground Truth Format (JSON):
    {
        "doc_id": "2310",
        "pages": {
            "1": [
                {"surface": "Karl Jaspers", "type": "person"},
                {"surface": "JSTOR", "type": "organization"}
            ]
        }
    }

    Args:
        lenient: Diakritik-normalisierter Vergleich (Geneve == Geneve)
    """
    gt_data = json.loads(Path(gt_path).read_text(encoding="utf-8"))
    store = EntityStore.load(doc_id)

    normalize = _strip_diacritics if lenient else lambda t: t.lower()

    # Ground Truth Entities sammeln
    gt_entities = set()
    for page_str, entities in gt_data.get("pages", {}).items():
        for ent in entities:
            gt_entities.add(
                (normalize(ent["surface"]), ent["type"])
            )

    # Predicted Entities (nur Seiten die im GT vorkommen)
    gt_pages = {int(p) for p in gt_data.get("pages", {}).keys()}
    pred_entities = set()
    for rec in store.entities.values():
        if gt_pages & set(rec.pages):
            for surface in rec.surfaces:
                pred_entities.add((normalize(surface), rec.entity_type))

    # Precision / Recall
    true_positives = gt_entities & pred_entities
    precision = len(true_positives) / len(pred_entities) if pred_entities else 0
    recall = len(true_positives) / len(gt_entities) if gt_entities else 0
    f1 = (
        2 * precision * recall / (precision + recall)
        if (precision + recall) > 0
        else 0
    )

    return {
        "doc_id": doc_id,
        "mode": "lenient" if lenient else "strict",
        "gt_entities": len(gt_entities),
        "pred_entities": len(pred_entities),
        "true_positives": len(true_positives),
        "precision": round(precision, 3),
        "recall": round(recall, 3),
        "f1": round(f1, 3),
        "false_positives": sorted(
            f"{t}:{s}" for s, t in (pred_entities - gt_entities)
        ),
        "false_negatives": sorted(
            f"{t}:{s}" for s, t in (gt_entities - pred_entities)
        ),
    }


# ---------------------------------------------------------------------------
# HTML Report
# ---------------------------------------------------------------------------

def _generate_html_report(corpus: dict, output_path: str) -> None:
    """Erzeugt einen HTML-Report mit NER-Korpus-Metriken."""
    # Sprach-Daten sammeln
    lang_data = corpus_summary_by_language()
    lang_table_rows = ""
    if "by_language" in lang_data:
        for lang, stats in sorted(
            lang_data["by_language"].items(),
            key=lambda x: -x[1]["total_entities"],
        ):
            pct_of_corpus = round(
                stats["documents"] / (corpus.get("documents", 1) or 1) * 100
            )
            lang_table_rows += (
                f'<tr><td>{lang}</td>'
                f'<td>{stats["documents"]} ({pct_of_corpus}%)</td>'
                f'<td>{stats["total_entities"]}</td>'
                f'<td>{stats["total_mentions"]}</td>'
                f'<td>{stats["avg_density_per_page"]}</td>'
                f'<td>{stats["resolution_rate"]:.0%}</td></tr>\n'
            )

    # Per-Doc Daten sammeln
    doc_rows = []
    top_entities = []
    if ENTITIES_DIR.exists():
        entity_freq = {}  # (normalized, type) -> count
        for d in sorted(ENTITIES_DIR.iterdir()):
            if not d.is_dir() or d.name.startswith("_"):
                continue
            report = doc_report(d.name)
            if "error" not in report:
                doc_rows.append(report)
                store = EntityStore.load(d.name)
                for rec in store.entities.values():
                    key = (rec.normalized, rec.entity_type)
                    entity_freq[key] = entity_freq.get(key, 0) + 1
        # Top-20 cross-doc entities
        top_entities = sorted(entity_freq.items(), key=lambda x: -x[1])[:20]

    # Typ-Verteilung als HTML-Balken
    type_bars = ""
    for t, pct in sorted(
        corpus.get("type_distribution", {}).items(), key=lambda x: -x[1]
    ):
        type_bars += (
            f'<div style="margin:4px 0">'
            f'<span style="display:inline-block;width:100px">{t}</span>'
            f'<span style="display:inline-block;width:{pct * 2}px;'
            f'height:16px;background:#4a6fa5"></span>'
            f' {pct}%</div>\n'
        )

    # Doc-Tabelle
    doc_table_rows = ""
    for r in doc_rows:
        doc_table_rows += (
            f'<tr><td>{r["doc_id"]}</td>'
            f'<td>{r["total_entities"]}</td>'
            f'<td>{r["total_mentions"]}</td>'
            f'<td>{r["density_per_page"]}</td>'
            f'<td>{r["resolution_rate"]:.0%}</td></tr>\n'
        )

    # Top-Entities-Tabelle
    top_table = ""
    for (norm, etype), freq in top_entities:
        top_table += (
            f'<tr><td>{norm}</td><td>{etype}</td><td>{freq}</td></tr>\n'
        )

    html = f"""<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="utf-8">
<title>NER Corpus Report</title>
<style>
body {{ font-family: system-ui, sans-serif; max-width: 960px; margin: 2em auto; padding: 0 1em; }}
h1 {{ color: #1a2744; }}
h2 {{ color: #4a6fa5; border-bottom: 1px solid #ccc; padding-bottom: 4px; }}
table {{ border-collapse: collapse; width: 100%; margin: 1em 0; }}
th, td {{ padding: 6px 10px; border: 1px solid #ddd; text-align: left; }}
th {{ background: #f0f4f8; }}
.metric {{ display: inline-block; padding: 12px 20px; margin: 6px; background: #f0f4f8; border-radius: 8px; text-align: center; }}
.metric .value {{ font-size: 1.8em; font-weight: bold; color: #1a2744; }}
.metric .label {{ font-size: 0.85em; color: #666; }}
</style>
</head>
<body>
<h1>NER Corpus Report</h1>
<p>Generiert: {datetime.now().strftime("%Y-%m-%d %H:%M")}</p>

<div>
<div class="metric"><div class="value">{corpus.get('documents', 0)}</div><div class="label">Dokumente</div></div>
<div class="metric"><div class="value">{corpus.get('total_entities', 0)}</div><div class="label">Entities</div></div>
<div class="metric"><div class="value">{corpus.get('total_mentions', 0)}</div><div class="label">Mentions</div></div>
<div class="metric"><div class="value">{corpus.get('resolution_rate', 0):.0%}</div><div class="label">Resolution</div></div>
<div class="metric"><div class="value">{corpus.get('avg_entities_per_doc', 0)}</div><div class="label">Avg/Doc</div></div>
<div class="metric"><div class="value">{corpus.get('avg_density_per_page', 0)}</div><div class="label">Avg/Seite</div></div>
</div>

<h2>Typ-Verteilung</h2>
{type_bars}

<h2>Per Sprache</h2>
<table>
<tr><th>Sprache</th><th>Docs</th><th>Entities</th><th>Mentions</th><th>Ent/Seite</th><th>Resolved</th></tr>
{lang_table_rows}
</table>

<h2>Top-20 Entities (Cross-Doc-Frequenz)</h2>
<table>
<tr><th>Entity</th><th>Typ</th><th>Docs</th></tr>
{top_table}
</table>

<h2>Per-Dokument-Metriken</h2>
<table>
<tr><th>Doc</th><th>Entities</th><th>Mentions</th><th>Ent/Seite</th><th>Resolved</th></tr>
{doc_table_rows}
</table>
</body>
</html>"""

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    print(f"HTML-Report geschrieben: {out}")
    print(f"  {corpus.get('documents', 0)} Docs, "
          f"{corpus.get('total_entities', 0)} Entities, "
          f"Resolution {corpus.get('resolution_rate', 0):.0%}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="NER Evaluation: Metriken + Ground-Truth-Vergleich"
    )
    parser.add_argument("--doc", help="Einzelnes Dokument auswerten")
    parser.add_argument("--summary", action="store_true",
                        help="Korpus-Zusammenfassung")
    parser.add_argument("--gt", help="Ground-Truth JSON-Datei (fuer P/R/F1)")
    parser.add_argument("--lenient", action="store_true",
                        help="Diakritik-normalisierter Vergleich")
    parser.add_argument("--json", action="store_true",
                        help="Ausgabe als JSON")
    parser.add_argument("--by-language", action="store_true",
                        help="Sprach-stratifizierte Korpus-Zusammenfassung")
    parser.add_argument("--report", help="HTML-Report Ausgabepfad")
    args = parser.parse_args()

    if args.report:
        result = corpus_summary()
        if "error" in result:
            print("Keine Entity-Daten vorhanden.")
            return
        _generate_html_report(result, args.report)
        return

    if args.by_language:
        result = corpus_summary_by_language()
        if "error" in result:
            print("Keine Entity-Daten vorhanden.")
            return
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            for lang, stats in sorted(result['by_language'].items()):
                print(f"\n{lang} ({stats['documents']} Docs):")
                print(f"  Entities:    {stats['total_entities']}")
                print(f"  Mentions:    {stats['total_mentions']}")
                print(f"  Avg/Doc:     {stats['avg_entities_per_doc']}")
                print(f"  Avg/Seite:   {stats['avg_density_per_page']}")
                print(f"  Resolved:    {stats['resolution_rate']:.0%}")
                types_str = ", ".join(
                    f"{t} {p}%" for t, p in sorted(
                        stats['type_distribution'].items(), key=lambda x: -x[1]
                    )
                )
                print(f"  Typen:       {types_str}")
        return

    if args.summary:
        result = corpus_summary()
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(f"NER Corpus Summary ({result.get('documents', 0)} Docs)")
            print(f"  Seiten:      {result.get('total_pages', 0)}")
            print(f"  Entities:    {result.get('total_entities', 0)}")
            print(f"  Mentions:    {result.get('total_mentions', 0)}")
            print(f"  Avg/Doc:     {result.get('avg_entities_per_doc', 0)}")
            print(f"  Avg/Seite:   {result.get('avg_density_per_page', 0)}")
            print(f"  Resolved:    {result.get('resolved', 0)} "
                  f"({result.get('resolution_rate', 0):.0%})")
            print(f"  Typ-Verteilung:")
            for t, pct in sorted(
                result.get("type_distribution", {}).items(),
                key=lambda x: -x[1],
            ):
                print(f"    {t}: {pct}%")
        return

    if args.doc and args.gt:
        result_strict = evaluate_ground_truth(args.doc, args.gt, lenient=False)
        results = [result_strict]
        if args.lenient:
            result_lenient = evaluate_ground_truth(
                args.doc, args.gt, lenient=True
            )
            results.append(result_lenient)
        if args.json:
            out = results if args.lenient else results[0]
            print(json.dumps(out, ensure_ascii=False, indent=2))
        else:
            for result in results:
                mode = result.get("mode", "strict").upper()
                print(f"Ground Truth Evaluation: Doc {args.doc} ({mode})")
                print(f"  GT Entities:     {result['gt_entities']}")
                print(f"  Predicted:       {result['pred_entities']}")
                print(f"  True Positives:  {result['true_positives']}")
                print(f"  Precision:       {result['precision']:.1%}")
                print(f"  Recall:          {result['recall']:.1%}")
                print(f"  F1:              {result['f1']:.1%}")
                if result['false_negatives']:
                    print(f"  Missed ({len(result['false_negatives'])}):")
                    for fn in result['false_negatives'][:10]:
                        print(f"    - {fn}")
                if result['false_positives']:
                    print(f"  Extra ({len(result['false_positives'])}):")
                    for fp in result['false_positives'][:10]:
                        print(f"    - {fp}")
                if len(results) > 1:
                    print()
        return

    if args.doc:
        result = doc_report(args.doc)
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(f"Doc {args.doc}: {result.get('total_entities', 0)} entities, "
                  f"{result.get('total_mentions', 0)} mentions, "
                  f"{result.get('density_per_page', 0)} ent/page, "
                  f"resolved {result.get('resolution_rate', 0):.0%}")
            for t, ts in sorted(result.get("by_type", {}).items()):
                print(f"  {t}: {ts['total']} "
                      f"({ts['mentions']} mentions, "
                      f"{ts['resolved']} resolved)")
        return

    parser.print_help()


if __name__ == "__main__":
    main()
