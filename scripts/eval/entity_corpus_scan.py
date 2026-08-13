"""Corpus-wide dump of the entity candidates (entity integration, M3 fix package).

Runs ``scripts.tei.entity_matcher`` over the delivered TEI and writes every candidate
with rule, tier, offsets, page and context into one deterministic JSON snapshot, plus the
distribution views per document, per rule and per entity. The snapshot is diffable, so
a rule change shows its exact corpus effect before it binds; the design plan is in
knowledge/entity-integration.md (section "Instruments").

The page is resolved here, once per document, and is the snapshot's answer for every
consumer: a downstream tool reads ``page`` instead of reopening the TEI and rebuilding the
pb grid, which is where a second, diverging implementation would put marks on wrong pages.
The rule is the project-wide one of ``scripts.tei.pb_split``, the 1-based sequential
position of the ``<pb>`` element inside ``<body>`` rather than its ``n`` attribute.

DIAGNOSIS ONLY -- reads output/tei_final and the entity data, writes one report to
output/audits/, changes no TEI and is no pass/fail gate (exit code always 0).

Two invariants run over the tier-1 set, both violations of the automatic tier rather
than of the data:

  function_word_tier1    a tier-1 surface that is an ordinary word (homograph surname)
  hyphen_adjacent_tier1  a tier-1 span with a hyphen immediately before or after it
                         (the open hyphen-compound question, "Karl-Jaspers-Symposium")

Usage:
    python -m scripts.eval.entity_corpus_scan
    python -m scripts.eval.entity_corpus_scan --docs 100 290
    python -m scripts.eval.entity_corpus_scan --out output/audits/entity_corpus_scan.json
"""

from __future__ import annotations

import argparse
import json
from bisect import bisect_right
from collections import Counter
from pathlib import Path

from scripts.config import DATA_DIR, TEI_FINAL_DIR
from scripts.eval.audit_common import AUDIT_OUTPUT_DIR, iter_final_tei
from scripts.tei.entity_matcher import FUNCTION_WORDS as _MATCHER_FUNCTION_WORDS
from scripts.tei.pb_split import BODY_INNER_RE, PB_RE

ENTITIES_PATH = DATA_DIR / "entities" / "all_entities.json"
GND_CACHE_PATH = DATA_DIR / "entities" / "gnd_cache.json"
VARIANT_REVIEW_PATH = DATA_DIR / "entities" / "variant_review.json"
MARKING_POLICY_PATH = DATA_DIR / "entities" / "marking_policy.json"
LEGACY_MENTIONS_PATH = DATA_DIR / "entities" / "legacy_mentions.json"
REPORT_PATH = AUDIT_OUTPUT_DIR / "entity_corpus_scan.json"

TOP_ENTITIES = 25
MAX_PRINTED_VIOLATIONS = 20

INVARIANTS = ("function_word_tier1", "hyphen_adjacent_tier1")

# Ordinary words that a surname rule must never claim automatically. The homograph
# set is imported from the matcher (single source, drift-proof); the plain function
# words below stay as a safety net the matcher never needs to know.
FUNCTION_WORDS = _MATCHER_FUNCTION_WORDS | frozenset({
    "aber", "auch", "dann", "denn", "doch", "durch", "nach", "noch", "oder",
    "sein", "seit", "sind", "unter", "viel", "wenn", "wie", "wird",
    "avec", "dans", "mais", "pour", "sans", "sous", "tout",
})

# hyphen-minus, hyphen, non-breaking hyphen
HYPHENS = frozenset("-\u2010\u2011")


# ---------------------------------------------------------------------------
# Page assignment
# ---------------------------------------------------------------------------

def pb_offsets(xml_string: str) -> list[int]:
    """Offsets of the `<pb>` tags inside `<body>`, in document order."""
    match = BODY_INNER_RE.search(xml_string)
    if not match:
        return []
    base = match.start(1)
    return [base + pb.start() for pb in PB_RE.finditer(match.group(1))]


def page_of(pb_starts: list[int], offset: int) -> int:
    """1-based page of a TEI offset; anything before the first `<pb>` counts as page 1."""
    return max(1, bisect_right(pb_starts, offset))


# ---------------------------------------------------------------------------
# Scan
# ---------------------------------------------------------------------------

def _record(doc_id: str, cand: dict, page: int) -> dict:
    """Candidate plus its document and page, in the documented key order.

    `evidence` sits before the context and only where the matcher reports it (one-word
    work titles), so the snapshot carries the typographic pre-sorting it is measured on.
    """
    record = {
        "doc": doc_id,
        "page": page,
        "gid": cand["gid"],
        "category": cand["category"],
        "surface": cand["surface"],
        "start": cand["start"],
        "end": cand["end"],
        "tier": cand["tier"],
        "rule": cand["rule"],
        "alternatives": cand.get("alternatives", []),
        "matched_form": cand.get("matched_form", ""),
        "form_source": cand.get("form_source", ""),
    }
    if "evidence" in cand:
        record["evidence"] = cand["evidence"]
    record["context"] = cand["context"]
    return record


def _violation(record: dict, **extra) -> dict:
    violation = {key: record[key] for key in ("doc", "gid", "surface", "start", "rule", "context")}
    violation.update(extra)
    return violation


def check_invariants(records: list[dict], xml_string: str) -> dict[str, list[dict]]:
    """Violations per invariant for one document; only tier 1 is checked.

    Tier 2 and 3 are worklist material, where an ordinary word or a hyphen neighbour is
    the expected state rather than a defect.
    """
    violations: dict[str, list[dict]] = {name: [] for name in INVARIANTS}
    for record in records:
        if record["tier"] != 1:
            continue
        if record["surface"].casefold() in FUNCTION_WORDS:
            violations["function_word_tier1"].append(_violation(record))
        before = xml_string[record["start"] - 1] if record["start"] > 0 else ""
        after = xml_string[record["end"]] if record["end"] < len(xml_string) else ""
        side = _hyphen_side(before in HYPHENS, after in HYPHENS)
        if side:
            violations["hyphen_adjacent_tier1"].append(_violation(record, hyphen=side))
    return violations


def _hyphen_side(before: bool, after: bool) -> str:
    if before and after:
        return "both"
    if before:
        return "before"
    return "after" if after else ""


def scan_document(doc_id: str, xml_string: str, lexicon: dict,
                  find_candidates) -> tuple[list[dict], dict[str, list[dict]]]:
    """Candidates of one document as records, plus its invariant violations.

    The pb grid is read once per document and every candidate offset is cut on it.
    """
    pb_starts = pb_offsets(xml_string)
    records = [_record(doc_id, cand, page_of(pb_starts, cand["start"]))
               for cand in find_candidates(xml_string, lexicon)]
    return records, check_invariants(records, xml_string)


def resolve_docs(src_dir: Path, doc_ids: list[str] | None = None) -> list[tuple[str, Path]]:
    """(doc_id, path) pairs to scan; a requested document without TEI is skipped."""
    if doc_ids is None:
        return list(iter_final_tei(src_dir))
    pairs = []
    for doc_id in doc_ids:
        path = Path(src_dir) / f"{doc_id}_final.xml"
        if path.exists():
            pairs.append((doc_id, path))
        else:
            print(f"  {doc_id}: SKIP (no final TEI)")
    return pairs


def run_scan(doc_paths: list[tuple[str, Path]], lexicon: dict, find_candidates,
             sources: dict) -> dict:
    """Scan every document and build the report; the TEI files are only read."""
    records: list[dict] = []
    by_doc: dict[str, dict] = {}
    violations: dict[str, list[dict]] = {name: [] for name in INVARIANTS}
    for doc_id, path in doc_paths:
        xml_string = path.read_bytes().decode("utf-8")
        found, doc_violations = scan_document(doc_id, xml_string, lexicon, find_candidates)
        records.extend(found)
        by_doc[doc_id] = {
            "tier1": sum(1 for r in found if r["tier"] == 1),
            "tier2": sum(1 for r in found if r["tier"] == 2),
        }
        for name in INVARIANTS:
            violations[name].extend(doc_violations[name])
        print(f"  {doc_id}: tier1 {by_doc[doc_id]['tier1']}, tier2 {by_doc[doc_id]['tier2']}")
    labels = {gid: entry.get("label", "") for gid, entry in (lexicon.get("entries") or {}).items()}
    return build_scan_report(records, by_doc, violations, labels, sources)


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

def _sorted_counts(counter: Counter) -> dict:
    """Counts as a plain dict, most frequent first, ties by key (deterministic output)."""
    return dict(sorted(counter.items(), key=lambda kv: (-kv[1], kv[0])))


def build_scan_report(records: list[dict], by_doc: dict, violations: dict,
                      labels: dict, sources: dict) -> dict:
    """The full snapshot; candidates ordered by (doc, start), every view deterministic."""
    ordered = sorted(records, key=lambda r: (r["doc"], r["start"]))
    tier1 = [r for r in ordered if r["tier"] == 1]
    top = sorted(Counter(r["gid"] for r in tier1).items(),
                 key=lambda kv: (-kv[1], kv[0]))[:TOP_ENTITIES]
    return {
        "generated_from": {**sources, "code": "entity_matcher"},
        "totals": {
            "tier1": len(tier1),
            "tier2": sum(1 for r in ordered if r["tier"] == 2),
            "candidates": len(ordered),
            "ambiguous": sum(1 for r in ordered if r.get("alternatives")),
        },
        "by_rule": _sorted_counts(Counter(r["rule"] for r in ordered)),
        "by_evidence": _sorted_counts(
            Counter(r["evidence"] for r in ordered if r.get("evidence"))
        ),
        "by_doc": {doc: by_doc[doc] for doc in sorted(by_doc)},
        "by_entity_top": [[gid, labels.get(gid, ""), count] for gid, count in top],
        "candidates": ordered,
        "invariants": {name: {"violations": violations[name]} for name in INVARIANTS},
    }


def _ascii(text) -> str:
    """Fold to ASCII for the Windows console (the JSON report keeps full Unicode)."""
    return str(text).encode("ascii", "replace").decode("ascii")


def _print_summary(report: dict) -> None:
    totals = report["totals"]
    print(f"\n  Documents: {len(report['by_doc'])}  candidates: {totals['candidates']}  "
          f"(tier 1: {totals['tier1']}, tier 2: {totals['tier2']}, "
          f"several bearers: {totals['ambiguous']})")

    print("\n  By rule:")
    for rule, count in report["by_rule"].items():
        print(f"    {_ascii(rule):30} {count}")

    print("\n  One-word titles by typographic evidence:")
    for evidence, count in (report["by_evidence"] or {"(none reported)": 0}).items():
        print(f"    {_ascii(evidence):30} {count}")

    print("\n  Top entities (tier 1):")
    for gid, label, count in report["by_entity_top"]:
        print(f"    {count:6}  {_ascii(gid):14} {_ascii(label)}")

    print("\n  Invariants (diagnosis, no gate):")
    for name, payload in report["invariants"].items():
        found = payload["violations"]
        print(f"    {name:24} {len(found)} violation(s)")
        for item in found[:MAX_PRINTED_VIOLATIONS]:
            print(f"      {item['doc']} @{item['start']}: {_ascii(item['surface'])} "
                  f"({_ascii(item['rule'])})")
        if len(found) > MAX_PRINTED_VIOLATIONS:
            print(f"      ... {len(found) - MAX_PRINTED_VIOLATIONS} more, see the report")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _parse_doc_ids(values: list[str]) -> list[str]:
    """Accept both comma-separated and space-separated document ids."""
    return [d.strip() for value in values for d in value.split(",") if d.strip()]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Corpus-wide entity candidate scan (read-only diagnosis)")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--docs", nargs="+", help="Document ids, e.g. --docs 100 290")
    group.add_argument("--all", action="store_true", help="Whole corpus (default)")
    parser.add_argument("--out", type=Path, default=REPORT_PATH, help="Report path")
    parser.add_argument("--entities", type=Path, default=ENTITIES_PATH, help="Curated entity list")
    parser.add_argument("--cache", type=Path, default=GND_CACHE_PATH,
                        help="GND variant cache (optional, used when present)")
    parser.add_argument("--legacy", type=Path, default=LEGACY_MENTIONS_PATH,
                        help="Old mention index (optional, used when present)")
    parser.add_argument("--review", type=Path, default=VARIANT_REVIEW_PATH,
                        help="Variant review verdicts (optional, used when present)")
    parser.add_argument("--policy", type=Path, default=MARKING_POLICY_PATH,
                        help="Markierungspolitik (JSON, optional)")
    parser.add_argument("--src-dir", type=Path, default=TEI_FINAL_DIR,
                        help="Source TEI directory (read only)")
    args = parser.parse_args()

    from scripts.tei.entity_matcher import build_lexicon, find_candidates

    doc_paths = resolve_docs(args.src_dir, _parse_doc_ids(args.docs) if args.docs else None)
    legacy = args.legacy if args.legacy and args.legacy.exists() else None
    review = args.review if args.review.exists() else None
    policy = args.policy if args.policy.exists() else None
    lexicon = build_lexicon(args.entities, args.cache, legacy_path=legacy,
                            review_path=review, policy_path=policy)
    sources = {
        "entities": str(args.entities),
        "cache": str(args.cache) if Path(args.cache).exists() else None,
        "legacy": str(legacy) if legacy else None,
    }

    print(f"Entity corpus scan over {len(doc_paths)} document(s); nothing is written to TEI.")
    report = run_scan(doc_paths, lexicon, find_candidates, sources)
    _print_summary(report)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n  JSON report: {args.out}")


if __name__ == "__main__":
    main()
