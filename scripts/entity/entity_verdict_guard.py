"""Verdict guard: holds the adjudicated mention verdicts against the current scan.

The facsimile adjudication of 2026-08-12 (knowledge/entity-evaluation.md) left a store
of mention-level judgments, data/entities/mention_verdicts.json. After any matcher or
lexicon change this audit answers, per judgment, whether the current corpus scan still
honors it: marks adjudicated correct must survive, marks adjudicated wrong must stay
out of tier 1, and mentions the matcher was known to miss should have become hits.
The store is the immutable oracle; the scan under output/audits/ is the state under
test. Read-only with respect to both; the single output is
output/audits/verdict_guard_report.json.

Comparability. Mark offsets index the delivered TEI of the snapshot. The guard
recomputes each document's sha256 and compares spans only where the text is unchanged;
a changed document classifies its records as text_changed (re-anchor needed) instead
of producing false violations. Recall mentions carry no offsets and match by
(doc, page, gid) plus case-insensitive surface containment.

Classes. Rule changes move marks legitimately (running-head demotion postdates the
adjudication), so tier moves are reported, never treated as violations. Violations are
exactly: a correct mark that disappeared, a wrong_entity/not_in_source mark still
asserted in tier 1, and an adjudicated real mention (hit / on_worklist) that no longer
surfaces at all. Everything else is informational.

Determinism: no timestamps, fixed sort orders; two runs over the same inputs produce
byte-identical output.

Exit codes: 0 no violations, 1 violations found, 2 missing input.

Usage:
    python -m scripts.entity.entity_verdict_guard
    python -m scripts.entity.entity_verdict_guard --scan PATH --verdicts PATH
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

from scripts.config import DATA_DIR, PROJECT_ROOT, TEI_FINAL_DIR
from scripts.eval.audit_common import AUDIT_OUTPUT_DIR
from scripts.utils import read_json_strict

VERDICTS_PATH = DATA_DIR / "entities" / "mention_verdicts.json"
SCAN_PATH = AUDIT_OUTPUT_DIR / "entity_corpus_scan.json"
OUT_PATH = AUDIT_OUTPUT_DIR / "verdict_guard_report.json"

WRONG_VERDICTS = frozenset({"wrong_span", "wrong_entity", "not_in_source"})
MARK_VIOLATIONS = frozenset({"missing", "still_tier1"})
RECALL_VIOLATIONS = frozenset({"lost"})


def _repo_path(path: Path) -> str:
    try:
        return Path(path).resolve().relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return Path(path).as_posix()


def text_digests(docs, tei_dir: Path) -> dict[str, str | None]:
    """doc -> sha256 of the delivered TEI bytes, None where the document is missing."""
    digests: dict[str, str | None] = {}
    for doc in sorted(set(docs)):
        path = Path(tei_dir) / f"{doc}_final.xml"
        digests[doc] = hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None
    return digests


def _gid_matches(candidate: dict, gid: str) -> bool:
    """An ambiguous candidate reports its first bearer; the others stand in alternatives."""
    return gid == candidate["gid"] or gid in candidate.get("alternatives", ())


def _span_index(candidates) -> dict[tuple, list[dict]]:
    index: dict[tuple, list[dict]] = {}
    for c in candidates:
        index.setdefault((c["doc"], c["start"], c["end"]), []).append(c)
    return index


def _doc_index(candidates) -> dict[str, list[dict]]:
    index: dict[str, list[dict]] = {}
    for c in candidates:
        index.setdefault(c["doc"], []).append(c)
    return index


def _page_index(candidates) -> dict[tuple, list[dict]]:
    index: dict[tuple, list[dict]] = {}
    for c in candidates:
        index.setdefault((c["doc"], c["page"]), []).append(c)
    return index


def _current(candidate: dict | None) -> dict | None:
    if candidate is None:
        return None
    return {k: candidate[k] for k in ("tier", "rule", "start", "end", "surface")}


def _overlapping(pool: list[dict], gid: str, start: int, end: int) -> dict | None:
    """Best overlapping candidate of the gid (tier 1 preferred, then leftmost)."""
    hits = [c for c in pool
            if _gid_matches(c, gid) and c["start"] < end and start < c["end"]]
    hits.sort(key=lambda c: (c["tier"], c["start"]))
    return hits[0] if hits else None


def classify_mark(mark: dict, span_index: dict, doc_index: dict,
                  digests: dict[str, str | None]) -> tuple[str, dict | None]:
    """Class of one adjudicated mark against the current scan; see module docstring."""
    if mark["verdict"] == "undecidable":
        return "skipped_undecidable", None
    if digests.get(mark["doc"]) != mark["text_sha256"]:
        return "text_changed", None
    at_span = span_index.get((mark["doc"], mark["start"], mark["end"]), [])
    exact = next((c for c in at_span if _gid_matches(c, mark["gid"])), None)
    overlap = None
    if exact is None:
        overlap = _overlapping(doc_index.get(mark["doc"], []), mark["gid"],
                               mark["start"], mark["end"])
    found = exact or overlap
    if mark["verdict"] == "correct":
        if found is None:
            return "missing", None
        if found["tier"] == 1:
            return ("kept_tier1" if exact is not None else "kept_tier1_span_changed",
                    _current(found))
        return "moved_to_worklist", _current(found)
    # wrong_span / wrong_entity / not_in_source
    if found is None:
        return "gone", None
    if found["tier"] != 1:
        return "demoted", _current(found)
    if mark["verdict"] == "wrong_span" and exact is None:
        return "span_changed", _current(found)
    return "still_tier1", _current(found)


def _surface_matches(a: str, b: str) -> bool:
    a, b = a.lower(), b.lower()
    return a in b or b in a


def classify_recall(mention: dict, page_index: dict) -> tuple[str, dict | None]:
    """Class of one facsimile-read mention against the current scan."""
    pool = page_index.get((mention["doc"], mention["page"]), [])
    hits = [c for c in pool if _gid_matches(c, mention["gid"])
            and _surface_matches(mention["surface"], c["surface"])]
    hits.sort(key=lambda c: (c["tier"], c["start"]))
    best = hits[0] if hits else None
    status = mention["status"]
    if status == "missed":
        if best is None:
            return "still_missing", None
        return ("now_tier1" if best["tier"] == 1 else "now_worklist"), _current(best)
    if best is None:
        return "lost", None
    if status == "hit":
        return ("kept_tier1" if best["tier"] == 1 else "demoted_to_worklist"), _current(best)
    # on_worklist
    return ("upgraded_tier1" if best["tier"] == 1 else "still_listed"), _current(best)


def guard_report(store: dict, candidates: list[dict],
                 digests: dict[str, str | None]) -> dict:
    """The full comparison, deterministic; violations named in their own list."""
    span_index = _span_index(candidates)
    doc_index = _doc_index(candidates)
    page_index = _page_index(candidates)

    marks_out = []
    for mark in sorted(store["marks"], key=lambda m: (m["doc"], m["start"], m["gid"])):
        cls, current = classify_mark(mark, span_index, doc_index, digests)
        marks_out.append({
            "doc": mark["doc"], "page": mark["page"], "gid": mark["gid"],
            "surface": mark["surface"], "verdict": mark["verdict"],
            "start": mark["start"], "end": mark["end"],
            "class": cls, "current": current,
        })

    recall_out = []
    for mention in sorted(store["recall_mentions"],
                          key=lambda m: (m["doc"], m["page"], m["surface"], m["gid"])):
        cls, current = classify_recall(mention, page_index)
        recall_out.append({
            "doc": mention["doc"], "page": mention["page"], "gid": mention["gid"],
            "surface": mention["surface"], "status": mention["status"],
            "class": cls, "current": current,
        })

    violations = ([m for m in marks_out if m["class"] in MARK_VIOLATIONS]
                  + [m for m in recall_out if m["class"] in RECALL_VIOLATIONS])
    return {
        "summary": {
            "marks": dict(sorted(Counter(m["class"] for m in marks_out).items())),
            "recall": dict(sorted(Counter(m["class"] for m in recall_out).items())),
            "violations": len(violations),
        },
        "marks": marks_out,
        "recall": recall_out,
        "violations": violations,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Adjudicated verdicts vs current scan")
    parser.add_argument("--verdicts", type=Path, default=VERDICTS_PATH)
    parser.add_argument("--scan", type=Path, default=SCAN_PATH)
    parser.add_argument("--tei-dir", type=Path, default=TEI_FINAL_DIR)
    parser.add_argument("--out", type=Path, default=OUT_PATH)
    args = parser.parse_args()

    for path in (args.verdicts, args.scan):
        if not Path(path).exists():
            print(f"FEHLER missing input: {_repo_path(path)}", file=sys.stderr)
            return 2

    store = read_json_strict(args.verdicts)
    scan = read_json_strict(args.scan)
    candidates = scan["candidates"]
    docs = {m["doc"] for m in store["marks"]}
    digests = text_digests(docs, args.tei_dir)

    report = guard_report(store, candidates, digests)
    report["generated_from"] = {
        "verdicts": _repo_path(args.verdicts),
        "scan": _repo_path(args.scan),
        "scan_sha256": hashlib.sha256(
            Path(args.scan).read_bytes()).hexdigest(),
        "tei_dir": _repo_path(args.tei_dir),
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")

    for scope in ("marks", "recall"):
        parts = ", ".join(f"{k}={v}" for k, v in report["summary"][scope].items())
        print(f"OK {scope}: {parts}")
    for v in report["violations"]:
        where = f"doc {v['doc']} p{v['page']} '{v['surface']}' gid {v['gid']}"
        print(f"FEHLER {v['class']}: {where}", file=sys.stderr)
    print(f"{'FEHLER' if report['violations'] else 'OK'} "
          f"violations={report['summary']['violations']} "
          f"report={_repo_path(args.out)}")
    return 1 if report["violations"] else 0


if __name__ == "__main__":
    sys.exit(main())
