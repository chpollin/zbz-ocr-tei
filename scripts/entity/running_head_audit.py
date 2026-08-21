"""Audit of the deterministic running-head detector (Kolumnentitel zones).

Operator convention E105 keeps running heads out of the entity layer: the author name or
work title printed as page furniture on every page is not a mention of the person or the
work. The detection core lives in scripts.entity.running_heads (shared with the entity
matcher, which holds in-zone candidates out of tier 1). This module is the measurement
half: it locates the head zones corpus-wide, scores them against the facsimile-adjudicated
ground truth, counts the suppression scope on the corpus scan, and computes the convention
reading of the adjudicated precision (precision over the marks the E105 convention keeps
in scope). Nothing here writes TEI and nothing here touches the matcher.

DIAGNOSIS ONLY -- reads output/tei_final, the adjudicated verdicts and the corpus scan
snapshot, writes one report and is no pass/fail gate.

Usage:
    python -m scripts.entity.running_head_audit
    python -m scripts.entity.running_head_audit --dir other_tei --out other.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
from collections import defaultdict
from pathlib import Path

from scripts.config import DATA_DIR, TEI_FINAL_DIR
from scripts.entity.running_heads import (
    CONTAINS_LENGTH_FACTOR,
    EXCLUDED_PARENT_TAGS,
    MAX_HEAD_CHARS,
    MAX_HEAD_SEGMENTS,
    MIN_COMPANION_RECURRENCE,
    MIN_HEAD_CHARS,
    MIN_RECURRENCE,
    detect_document,
    normalize_head,
    zone_lookup,
)
from scripts.eval.audit_common import AUDIT_OUTPUT_DIR, ascii_only, doc_id_from_path

__all__ = [
    "CONTAINS_LENGTH_FACTOR", "MAX_HEAD_CHARS", "MAX_HEAD_SEGMENTS",
    "MIN_COMPANION_RECURRENCE", "MIN_RECURRENCE", "audit_corpus", "build_report",
    "convention_precision", "detect_document", "normalize_head", "zone_lookup",
]

SNAPSHOT = "2026-08-12"

VERDICTS_PATH = DATA_DIR / "entities" / "mention_verdicts.json"
SCAN_PATH = AUDIT_OUTPUT_DIR / "entity_corpus_scan.json"
REPORT_PATH = AUDIT_OUTPUT_DIR / "running_head_audit.json"

RUNNING_HEAD_REASON = "running head"
CORRECT_VERDICT = "correct"
DECIDABLE_VERDICTS = frozenset({"correct", "wrong_entity", "wrong_span", "not_in_source"})
TIER_1 = 1
TOP_PRINTED = 12

# Bootstrap parameters of the convention reading, matching the executed evaluation
# (percentile interval, seed 42; reports/2026-08-12_entity-eval-ergebnis.md).
BOOTSTRAP_SEED = 42
BOOTSTRAP_N = 10000


def audit_corpus(tei_dir) -> list[dict]:
    """Per-document detection over every delivered TEI, ordered by filename."""
    documents = []
    for path in sorted(Path(tei_dir).glob("*_final.xml")):
        xml_text = path.read_bytes().decode("utf-8")
        documents.append(dict(detect_document(xml_text),
                              doc=doc_id_from_path(path),
                              sha256=hashlib.sha256(xml_text.encode("utf-8")).hexdigest()))
    return documents


# ---------------------------------------------------------------------------
# Validation against the adjudicated ground truth
# ---------------------------------------------------------------------------

def is_running_head_mark(mark: dict) -> bool:
    """A mark the facsimile adjudication justified with the running head."""
    return (mark.get("verdict") == CORRECT_VERDICT
            and RUNNING_HEAD_REASON in (mark.get("reason") or "").casefold())


def _mark_view(mark: dict, zone: dict | None) -> dict:
    view = {"doc": mark.get("doc"), "page": mark.get("page"), "surface": mark.get("surface"),
            "start": mark.get("start"), "end": mark.get("end"), "reason": mark.get("reason")}
    if zone is not None:
        view["zone"] = {"form": zone["form"], "kind": zone["kind"], "page": zone["page"],
                        "start": zone["start"], "end": zone["end"], "text": zone["text"]}
    return view


def _tei_drift(documents: list[dict], marks: list[dict]) -> list[str]:
    """Documents whose TEI changed since the adjudication; their offsets are stale."""
    current = {document["doc"]: document.get("sha256") for document in documents}
    drifted = set()
    for mark in marks:
        recorded = mark.get("text_sha256")
        doc = mark.get("doc")
        if recorded and doc in current and current[doc] != recorded:
            drifted.add(doc)
    return sorted(drifted)


def validate(documents: list[dict], verdicts: dict | None, lookup) -> dict:
    """Recall on the known running-head marks and false alarms on the other correct ones."""
    marks = (verdicts or {}).get("marks") or []
    heads = [m for m in marks if is_running_head_mark(m)]
    others = [m for m in marks if m.get("verdict") == CORRECT_VERDICT
              and not is_running_head_mark(m)]

    detected, misses = [], []
    for mark in heads:
        zone = lookup(mark.get("doc"), mark.get("start"))
        (detected if zone else misses).append(_mark_view(mark, zone))
    alarms = []
    for mark in others:
        zone = lookup(mark.get("doc"), mark.get("start"))
        if zone:
            alarms.append(_mark_view(mark, zone))
    alarms.sort(key=lambda m: (m["doc"], m["start"]))

    return {
        "ground_truth": str(VERDICTS_PATH),
        "criterion": f"a mark counts as a running head when its adjudication reason "
                     f"contains '{RUNNING_HEAD_REASON}' and its verdict is "
                     f"'{CORRECT_VERDICT}'",
        "tei_drift": _tei_drift(documents, marks),
        "running_head_marks": {
            "total": len(heads),
            "detected": len(detected),
            "recall": round(len(detected) / len(heads), 4) if heads else None,
            "misses": misses,
        },
        "other_correct_marks": {
            "total": len(others),
            "in_zone": len(alarms),
            "false_alarm_rate": round(len(alarms) / len(others), 4) if others else None,
            "cases": alarms,
        },
    }


def corpus_impact(scan: dict | None, lookup) -> dict:
    """Tier-1 marks of the corpus scan falling inside a zone; the later suppression cost.

    Only doc and start are read, so a scan snapshot with or without the per-candidate
    page field is handled the same way.
    """
    if not isinstance(scan, dict):
        return {"available": False, "reason": "corpus scan snapshot unavailable"}
    candidates = scan.get("candidates")
    if not isinstance(candidates, list):
        return {"available": False, "reason": "corpus scan carries no candidate list"}
    tier1 = [c for c in candidates if c.get("tier") == TIER_1]
    by_doc: dict[str, int] = defaultdict(int)
    for candidate in tier1:
        if lookup(candidate.get("doc"), candidate.get("start")):
            by_doc[candidate["doc"]] += 1
    in_zone = sum(by_doc.values())
    return {
        "available": True,
        "scan": str(SCAN_PATH),
        "tier1_marks": len(tier1),
        "in_zone": in_zone,
        "share": round(in_zone / len(tier1), 4) if tier1 else None,
        "by_doc": dict(sorted(by_doc.items())),
    }


# ---------------------------------------------------------------------------
# Convention reading of the adjudicated precision (E105)
# ---------------------------------------------------------------------------

def convention_precision(verdicts: dict | None, lookup) -> dict:
    """Precision over the adjudicated marks the E105 convention keeps in scope.

    The executed evaluation measured precision over every decidable drawn mark
    (reports/2026-08-12_entity-eval-ergebnis.md). The convention reading drops the
    marks inside a running-head zone from both numerator and denominator, because
    E105 puts them outside the marking scope; `undecidable` verdicts stay excluded
    exactly as in the protocol reading. The interval is a percentile bootstrap with
    a fixed seed, matching the evaluation's statistics discipline.
    """
    marks = (verdicts or {}).get("marks") or []
    if not marks:
        return {"available": False, "reason": "no adjudicated marks available"}
    in_scope = [m for m in marks if not lookup(m.get("doc"), m.get("start"))]
    in_zone_verdicts: dict[str, int] = defaultdict(int)
    for mark in marks:
        if lookup(mark.get("doc"), mark.get("start")):
            in_zone_verdicts[mark.get("verdict") or "missing"] += 1
    decidable = [m for m in in_scope if m.get("verdict") in DECIDABLE_VERDICTS]
    correct = sum(1 for m in decidable if m["verdict"] == CORRECT_VERDICT)
    result = {
        "available": True,
        "criterion": "marks inside a detected running-head zone are out of scope "
                     "(E105); undecidable verdicts stay excluded",
        "marks_total": len(marks),
        "in_zone": len(marks) - len(in_scope),
        "in_zone_by_verdict": dict(sorted(in_zone_verdicts.items())),
        "in_scope_decidable": len(decidable),
        "correct": correct,
    }
    if decidable:
        result["precision"] = round(correct / len(decidable), 4)
        result["ci95"] = _bootstrap_ci([1 if m["verdict"] == CORRECT_VERDICT else 0
                                        for m in decidable])
    else:
        result["precision"] = None
        result["ci95"] = None
    return result


def _bootstrap_ci(outcomes: list[int]) -> list[float]:
    """Seeded percentile bootstrap of the mean, deterministic across runs."""
    rng = random.Random(BOOTSTRAP_SEED)
    n = len(outcomes)
    means = sorted(sum(rng.choice(outcomes) for _ in range(n)) / n
                   for _ in range(BOOTSTRAP_N))
    lo = means[int(0.025 * BOOTSTRAP_N)]
    hi = means[min(int(0.975 * BOOTSTRAP_N), BOOTSTRAP_N - 1)]
    return [round(lo, 4), round(hi, 4)]


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

def parameter_doc() -> dict:
    """The detection contract as data, so the report explains its own numbers."""
    return {
        "max_head_segments": MAX_HEAD_SEGMENTS,
        "min_head_chars": MIN_HEAD_CHARS,
        "max_head_chars": MAX_HEAD_CHARS,
        "min_recurrence": MIN_RECURRENCE,
        "min_companion_recurrence": MIN_COMPANION_RECURRENCE,
        "contains_length_factor": CONTAINS_LENGTH_FACTOR,
        "excluded_parent_tags": sorted(EXCLUDED_PARENT_TAGS),
        "kinds": {
            "primary": f"the normalized form recurs at the page start of at least "
                       f"{MIN_RECURRENCE} distinct pages",
            "companion": f"at least {MIN_COMPANION_RECURRENCE} pages in a document that "
                         f"already carries a primary pattern; this is the alternating "
                         f"verso/recto counterpart of a short document",
            "contains": f"a single page-start segment containing a primary form as a "
                        f"whole word and at most {CONTAINS_LENGTH_FACTOR} times its "
                        f"length; OCR merges folio or author prefix into the head line",
        },
    }


def build_report(documents: list[dict], verdicts: dict | None, scan: dict | None,
                 sources: dict) -> dict:
    """The full audit snapshot; every view deterministic, no timestamp."""
    lookup = zone_lookup(documents)
    with_heads = [d for d in documents if d["patterns"]]
    zones = sum(len(p["zones"]) for d in documents for p in d["patterns"])
    pages_with_zone = sum(len({page for p in d["patterns"] for page in p["pages"]})
                          for d in documents)
    kinds: dict[str, int] = defaultdict(int)
    for document in documents:
        for pattern in document["patterns"]:
            kinds[pattern["kind"]] += 1
    return {
        "snapshot": SNAPSHOT,
        "sources": sources,
        "parameters": parameter_doc(),
        "totals": {
            "documents": len(documents),
            "documents_with_heads": len(with_heads),
            "pages": sum(d["pages"] for d in documents),
            "patterns": sum(len(d["patterns"]) for d in documents),
            "patterns_by_kind": {k: kinds[k] for k in ("primary", "companion", "contains")},
            "zones": zones,
            "pages_with_zone": pages_with_zone,
        },
        "validation": validate(documents, verdicts, lookup),
        "convention_precision": convention_precision(verdicts, lookup),
        "corpus_impact": corpus_impact(scan, lookup),
        "documents": [{"doc": d["doc"], "pages": d["pages"], "patterns": d["patterns"]}
                      for d in documents if d["patterns"]],
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _load(path: Path) -> dict | None:
    """Tolerant read of a JSON snapshot a concurrent run may be rewriting."""
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        print(f"  WARNING: {path} unreadable ({exc.__class__.__name__})")
        return None


def _print_summary(report: dict) -> None:
    totals = report["totals"]
    print(f"\n  Documents: {totals['documents']} "
          f"({totals['documents_with_heads']} with a running head)")
    print(f"  Patterns:  {totals['patterns']} {totals['patterns_by_kind']}")
    print(f"  Zones:     {totals['zones']} on {totals['pages_with_zone']} page(s)")

    validation = report["validation"]
    heads = validation["running_head_marks"]
    others = validation["other_correct_marks"]
    print(f"\n  Recall on adjudicated running-head marks: "
          f"{heads['detected']}/{heads['total']} ({heads['recall']})")
    for miss in heads["misses"]:
        print(f"    MISS  {miss['doc']:>5} p{miss['page']} @{miss['start']} "
              f"{ascii_only(miss['surface'])}")
    print(f"\n  False alarms on other correct marks: "
          f"{others['in_zone']}/{others['total']} ({others['false_alarm_rate']})")
    for case in others["cases"]:
        print(f"    ALARM {case['doc']:>5} p{case['page']} @{case['start']} "
              f"{ascii_only(case['surface'])} -> {case['zone']['kind']} "
              f"'{ascii_only(case['zone']['form'])[:40]}'")
        print(f"          reason: {ascii_only(case['reason'])[:110]}")
    if validation["tei_drift"]:
        print(f"\n  WARNING: TEI changed since adjudication in "
              f"{', '.join(validation['tei_drift'])}; offsets may be stale.")

    reading = report["convention_precision"]
    if reading.get("available"):
        print(f"\n  Convention precision (in-scope marks): {reading['precision']} "
              f"[{reading['ci95'][0]}, {reading['ci95'][1]}] over "
              f"{reading['in_scope_decidable']} decidable "
              f"({reading['in_zone']} of {reading['marks_total']} marks in a zone)")
    else:
        print(f"\n  Convention precision unavailable: {reading.get('reason')}")

    impact = report["corpus_impact"]
    if impact["available"]:
        print(f"\n  Corpus impact: {impact['in_zone']}/{impact['tier1_marks']} tier-1 "
              f"marks inside a zone ({impact['share']})")
        top = sorted(impact["by_doc"].items(), key=lambda kv: (-kv[1], kv[0]))
        for doc, count in top[:TOP_PRINTED]:
            print(f"    {doc:>5} {count}")
    else:
        print(f"\n  Corpus impact unavailable: {impact['reason']}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Deterministic running-head detector (read-only measurement audit)")
    parser.add_argument("--dir", type=Path, default=TEI_FINAL_DIR,
                        help="TEI directory to scan (default tei_final)")
    parser.add_argument("--verdicts", type=Path, default=VERDICTS_PATH,
                        help="Adjudicated mark verdicts used as ground truth")
    parser.add_argument("--scan", type=Path, default=SCAN_PATH,
                        help="Corpus scan snapshot for the impact count")
    parser.add_argument("--out", type=Path, default=REPORT_PATH, help="Report path")
    args = parser.parse_args()

    if not args.dir.is_dir():
        print(f"  TEI directory missing: {args.dir}")
        sys.exit(1)

    print(f"Running-head detection over {args.dir}; nothing is written to TEI.")
    documents = audit_corpus(args.dir)
    verdicts = _load(args.verdicts)
    # Read last: a concurrent scan run may be rewriting the snapshot while this audit runs.
    scan = _load(args.scan)
    report = build_report(documents, verdicts, scan, sources={
        "tei_dir": str(args.dir),
        "verdicts": str(args.verdicts),
        "scan": str(args.scan),
    })
    _print_summary(report)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n  JSON report: {args.out}")


if __name__ == "__main__":
    main()
