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
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.config import ENTITIES_DIR
from scripts.ner.entity_index import EntityIndex
from scripts.ner.entity_store import EntityStore


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


def evaluate_ground_truth(doc_id: str, gt_path: str) -> dict:
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
    """
    gt_data = json.loads(Path(gt_path).read_text(encoding="utf-8"))
    store = EntityStore.load(doc_id)

    # Ground Truth Entities sammeln
    gt_entities = set()
    for page_str, entities in gt_data.get("pages", {}).items():
        for ent in entities:
            gt_entities.add(
                (ent["surface"].lower(), ent["type"])
            )

    # Predicted Entities (nur Seiten die im GT vorkommen)
    gt_pages = {int(p) for p in gt_data.get("pages", {}).keys()}
    pred_entities = set()
    for rec in store.entities.values():
        if gt_pages & set(rec.pages):
            for surface in rec.surfaces:
                pred_entities.add((surface.lower(), rec.entity_type))

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
    parser.add_argument("--json", action="store_true",
                        help="Ausgabe als JSON")
    args = parser.parse_args()

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
        result = evaluate_ground_truth(args.doc, args.gt)
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(f"Ground Truth Evaluation: Doc {args.doc}")
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
