"""Run-zu-Run-Stabilitaets-Pilot: 5 Referenzdokumente x 3 volle Pipeline-Laeufe (E100).

Misst die Streuung der Fidelity-CER ueber unabhaengige --force-Laeufe der
nicht-deterministischen LLM-Stufe (Step 2, ein Gemini-Call je Seite). Jeder Lauf
schreibt in ein eigenes Verzeichnis output/stability_runs/run{N}/; der produktive
Step-2-Cache (output/tei_unified/) und tei_final bleiben unberuehrt. Die CER je
Lauf entsteht ueber die kanonischen Funktionen aus evaluate_ocr gegen die
ZBZ-Referenz, identisch zur Benchmark-Strecke.

Das Artefakt output/audits/stability_pilot.json schliesst den stability-Block in
cer_statistics_full (status: measured); danach docs/data/cer_statistics.json
regenerieren.

Aufruf:
    python -m scripts.eval.stability_pilot --dry-run      # Umfang + Call-Schaetzung
    python -m scripts.eval.stability_pilot                # Pilot fahren (API-Calls!)
    python -m scripts.eval.stability_pilot --runs 3 --docs 570 2310 1910 830 890
"""

import argparse
import json
import statistics
from datetime import date
from pathlib import Path

from scripts.config import GEMINI_MODEL, OUTPUT_DIR, REFERENCE_TEI_DIR

# stratified over layout types and languages, reference-covered, small page counts
PILOT_DOCS = ["570", "2310", "1910", "830", "890"]
N_RUNS = 3
RUNS_DIR = OUTPUT_DIR / "stability_runs"
REPORT_PATH = OUTPUT_DIR / "audits" / "stability_pilot.json"


def fidelity_cer(final_path: Path, doc_id: str) -> float:
    from scripts.eval.evaluate_ocr import (
        classify_edit_operations,
        extract_text_for_comparison,
        normalize_for_comparison,
    )
    ref = normalize_for_comparison(
        extract_text_for_comparison(str(REFERENCE_TEI_DIR / f"{doc_id}.xml"))
    )
    hyp = normalize_for_comparison(extract_text_for_comparison(str(final_path)))
    return classify_edit_operations(hyp, ref)["cer_fidelity"]


def aggregate(per_run_cer: dict) -> dict:
    """{doc: [cer je Lauf]} -> per-doc mean/std/range plus summary.

    std is the sample standard deviation (ddof=1); with all-equal runs it is 0.0.
    """
    per_doc = {}
    for doc, cers in per_run_cer.items():
        per_doc[doc] = {
            "cers": cers,
            "mean": statistics.fmean(cers),
            "std": statistics.stdev(cers) if len(cers) > 1 else 0.0,
            "range": max(cers) - min(cers),
        }
    stds = [v["std"] for v in per_doc.values()]
    return {
        "per_doc": per_doc,
        "summary": {
            "mean_std": statistics.fmean(stds) if stds else None,
            "max_std": max(stds) if stds else None,
            "max_range": max((v["range"] for v in per_doc.values()), default=None),
        },
    }


def run_pilot(docs, n_runs, dry_run=False) -> dict:
    from scripts.core.loaders import discover_pages

    pages = {d: len(discover_pages(d)) for d in docs}
    total_calls = sum(pages.values()) * n_runs
    print(f"Pilot: {len(docs)} Dokumente x {n_runs} Laeufe, "
          f"{sum(pages.values())} Seiten/Lauf -> {total_calls} Step-2-Calls")
    for d in docs:
        print(f"    {d:>5}: {pages[d]} Seiten")
    if dry_run:
        print("(dry-run: keine Laeufe gestartet)")
        return {}

    import scripts.tei.tei_unified as tu

    per_run_cer = {d: [] for d in docs}
    for run_no in range(1, n_runs + 1):
        run_dir = RUNS_DIR / f"run{run_no}"
        run_dir.mkdir(parents=True, exist_ok=True)
        tu.TEI_UNIFIED_DIR = run_dir  # redirect: production caches stay untouched
        print(f"\n--- Lauf {run_no}/{n_runs} -> {run_dir}")
        for d in docs:
            tu.process_document(d, max_step=3, force=True)
            final = run_dir / d / f"{d}_final.xml"
            cer = fidelity_cer(final, d)
            per_run_cer[d].append(cer)
            print(f"    {d:>5}: Fidelity {cer*100:.2f}%")

    result = aggregate(per_run_cer)
    payload = {
        "tool": "stability_pilot",
        "generated": date.today().isoformat(),
        "model": GEMINI_MODEL,
        "n_docs": len(docs),
        "n_runs": n_runs,
        "docs": docs,
        "pages_per_doc": pages,
        **result,
    }
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    print("\n" + "-" * 60)
    for d, v in result["per_doc"].items():
        cers = ", ".join(f"{c*100:.2f}" for c in v["cers"])
        print(f"  {d:>5}: [{cers}] %  std {v['std']*100:.3f}pp  range {v['range']*100:.3f}pp")
    s = result["summary"]
    print(f"  mean_std {s['mean_std']*100:.3f}pp  max_std {s['max_std']*100:.3f}pp")
    print(f"JSON-Report: {REPORT_PATH}")
    return payload


def main():
    ap = argparse.ArgumentParser(description="Run-zu-Run-Stabilitaets-Pilot (5 Docs x 3 Laeufe)")
    ap.add_argument("--docs", nargs="+", default=PILOT_DOCS)
    ap.add_argument("--runs", type=int, default=N_RUNS)
    ap.add_argument("--dry-run", action="store_true", help="nur Umfang zeigen, keine Calls")
    args = ap.parse_args()
    run_pilot(args.docs, args.runs, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
