"""Mention-level verdict store: the facsimile-adjudicated entity judgments, persisted.

The entity evaluation of knowledge/verification.md produced two bodies of evidence:
adjudicated tier-1 marks (precision) and the exhaustive reading of the drawn pages
(recall). Both live as loose case files under the sample directory of their wave, which
is evidence rather than a lookup. This script folds them into one store under
data/entities/, keyed per mention, so a later matcher run or agent can tell an
already-verified mention from an unseen one instead of re-adjudicating it.

Read-only with respect to all inputs; the single output is data/entities/mention_verdicts.json.

Waves
-----
One run builds exactly one wave, from the sample directory ``--sample-dir`` names. That
directory carries everything wave-specific: the drawn cases and pages, the adjudicated
verdicts, the manifest that dates the wave and the frozen corpus scan the occurrence
indexes count over. The wave names of its records follow PRECISION_WAVE/RECALL_WAVE and
therefore carry the snapshot label.

The store holds several waves at once. A run replaces the records of the wave it builds
and keeps every record of another wave untouched, so an older adjudication keeps binding
the verdict guard while a newer one is added. ``snapshots`` lists one entry per wave;
top-level ``snapshot`` is the latest label and ``sources`` the union over all waves.

Mention key
-----------
(doc, page, surface, gid, occurrence). ``occurrence`` is the 1-based index of this
(surface, gid) pair among the tier-1 candidates of that page, ordered by start offset,
counted over the FULL candidate population of the corpus scan rather than over the drawn
sample; a sample-relative index would point a consumer at the wrong mention wherever a
page carries several marks of the same pair. ``start``/``end`` stay in the record and
resolve a mention exactly as long as the text is unchanged.

Fingerprint (text_sha256)
-------------------------
sha256 over the bytes of ``output/tei_final/{doc}_final.xml``. Decoded as UTF-8 that file
is exactly the string the scan's start/end offsets index into (verified for the whole wave:
``xml[start:end] == surface`` for all 300 cases), so the digest covers precisely the stream
the offsets refer to. It is a per-document digest because the offsets are document-global;
the per-page mirror under docs/data/pages/ is a split of the same source and carries no
independent offsets. Any re-OCR, correction run or stock correction changes the digest,
which marks every record of that document as stale instead of silently misplacing it.

Determinism: no timestamps, fixed record and key order, snapshot label taken from the
sample manifest. Two runs produce byte-identical output.

Exit codes: 0 clean, 1 unusable sample or validation failure (nothing written), 2 written
but the wave distribution deviates from the adjudicated expectation (reported, never adjusted).

Usage:
    python -m scripts.entity.build_mention_verdicts
    python -m scripts.entity.build_mention_verdicts --dry-run
    python -m scripts.entity.build_mention_verdicts --sample-dir output/audits/eval_sample_2026-08-21
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

from scripts.config import DATA_DIR, PROJECT_ROOT, TEI_FINAL_DIR

# Page assignment via the pb rule of the sample draw (same helpers as
# scripts/entity/entity_eval_sample.py); a second implementation would drift.
from scripts.core.pb_split import page_of, pb_offsets
from scripts.eval.audit_common import AUDIT_OUTPUT_DIR, text_digests
from scripts.utils import read_json_strict

SAMPLE_DIR = AUDIT_OUTPUT_DIR / "eval_sample"
SCAN_GLOB = "entity_corpus_scan_frozen_*.json"
ENTITIES_PATH = DATA_DIR / "entities" / "all_entities.json"
OUT_PATH = DATA_DIR / "entities" / "mention_verdicts.json"

SNAPSHOT = "2026-08-12"
PRECISION_WAVE = "adjudication-{snapshot}"
RECALL_WAVE = "recall-adjudication-{snapshot}"

# The adjudicated result of the 2026-08-12 wave, pinned to SNAPSHOT. Another wave brings
# its own result and is not measured against these. A deviation is reported, never repaired.
EXPECTED_PRECISION = {"correct": 279, "wrong_span": 4, "wrong_entity": 5,
                      "not_in_source": 5, "undecidable": 7}
EXPECTED_RECALL = {"hit": 20, "on_worklist": 17, "missed": 30}
EXPECTED_IAA_CASES = 50
EXPECTED_IAA_DISAGREEMENTS = ("p145", "p193")

MARK_FIELDS = ("doc", "page", "surface", "gid", "occurrence", "category", "rule",
               "matched_form", "form_source", "start", "end", "verdict", "reason",
               "source", "text_sha256")
RECALL_MENTION_FIELDS = ("doc", "page", "surface", "gid", "status", "note", "source")
CASE_COPY_FIELDS = ("category", "rule", "matched_form", "form_source", "start", "end")


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------

def repo_path(path) -> str:
    """Repo-relative posix path where possible, so the store diffs across machines."""
    try:
        return Path(path).resolve().relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return Path(path).as_posix()


def frozen_scan_path(sample_dir: Path) -> Path:
    """The one frozen corpus scan a drawn sample carries.

    The store is snapshot-bound: occurrence indexes count over the FROZEN scan the sample
    was drawn from, never over the live scan, whose tier-1 population moves with every
    matcher rule change (E108/E109 made the two diverge).
    """
    matches = sorted(Path(sample_dir).glob(SCAN_GLOB))
    if not matches:
        raise FileNotFoundError(
            f"no frozen corpus scan ({SCAN_GLOB}) in {repo_path(sample_dir)}")
    if len(matches) > 1:
        raise ValueError(f"several frozen corpus scans in {repo_path(sample_dir)}: "
                         f"{', '.join(path.name for path in matches)}")
    return matches[0]


def snapshot_label(manifest: dict) -> str:
    """Snapshot date of the drawn sample: the day its newest source was recorded."""
    stamps = [source.get("modified") for source in manifest.get("sources", {}).values()
              if isinstance(source, dict) and source.get("modified")]
    if not stamps:
        raise ValueError("sample manifest carries no source timestamp to date the wave")
    return max(stamps)[:10]


def record_snapshot(record: dict, default: str = "") -> str:
    """Snapshot label of a stored mark or recall mention, read off its wave name.

    The two wave templates differ only in their prefix; a record without a wave name
    falls back to ``default``.
    """
    wave = (record.get("source") or {}).get("wave") or ""
    for template in (RECALL_WAVE, PRECISION_WAVE):
        prefix = template.format(snapshot="")
        if wave.startswith(prefix):
            return wave[len(prefix):]
    return wave or default


def load_precision_verdicts(paths) -> dict[str, dict]:
    """case_id -> {verdict, reason} over the batch files; a case may be judged once."""
    verdicts: dict[str, dict] = {}
    for path in paths:
        for entry in read_json_strict(path):
            case_id = entry["case_id"]
            if case_id in verdicts:
                raise ValueError(f"case {case_id} judged twice ({repo_path(path)})")
            verdicts[case_id] = {"verdict": entry["verdict"], "reason": entry.get("reason")}
    return verdicts


def load_iaa(path: Path) -> dict[str, dict]:
    """case_id -> the blind second judgment."""
    return {entry["case_id"]: {"verdict": entry["verdict"], "reason": entry.get("reason")}
            for entry in read_json_strict(path)}


def load_recall_pages(paths) -> dict[str, dict]:
    """page_ref -> {doc, page, mentions} merged over the recall batches."""
    pages: dict[str, dict] = {}
    for path in paths:
        for page_ref, payload in read_json_strict(path).items():
            if page_ref in pages:
                raise ValueError(f"page {page_ref} read twice ({repo_path(path)})")
            pages[page_ref] = payload
    return pages


def entity_gids(entities: dict) -> set[str]:
    """Every GND id of the curated list, raw, over persons, organisations and works."""
    return {entry["GND_id"] for group in entities.values() for entry in group}


def pb_index(docs, tei_dir: Path) -> dict[str, list[int]]:
    """doc -> <pb> offsets of the delivered TEI, the page grid the offsets are cut on."""
    index: dict[str, list[int]] = {}
    for doc in sorted(set(docs)):
        path = Path(tei_dir) / f"{doc}_final.xml"
        index[doc] = pb_offsets(path.read_bytes().decode("utf-8")) if path.exists() else []
    return index


# ---------------------------------------------------------------------------
# Records
# ---------------------------------------------------------------------------

def occurrence_map(candidates, pb_by_doc: dict[str, list[int]]) -> dict[tuple, tuple[int, int]]:
    """(doc, start) -> (page, occurrence) over the tier-1 candidate population.

    Tier 2 is worklist material and is not part of the mark population the occurrence
    index counts.
    """
    grouped: dict[tuple, list[int]] = defaultdict(list)
    for cand in candidates:
        if cand.get("tier") != 1:
            continue
        page = page_of(pb_by_doc.get(cand["doc"], []), cand["start"])
        grouped[(cand["doc"], page, cand["surface"], cand["gid"])].append(cand["start"])
    placement: dict[tuple, tuple[int, int]] = {}
    for key in sorted(grouped):
        doc, page = key[0], key[1]
        for index, start in enumerate(sorted(grouped[key]), start=1):
            placement[(doc, start)] = (page, index)
    return placement


def build_marks(cases, verdicts: dict, iaa: dict, placement: dict, digests: dict,
                wave: str) -> list[dict]:
    """One record per adjudicated case, in the order of the drawn sample.

    Undecidable cases stay in; they are evidence of what a facsimile cannot settle, and
    a consumer filters them by verdict.
    """
    marks = []
    for case in cases:
        case_id = case["case_id"]
        judgment = verdicts.get(case_id, {})
        placed = placement.get((case["doc"], case["start"]))
        mark = {
            "doc": case["doc"],
            "page": case["page"],
            "surface": case["surface"],
            "gid": case["gid"],
            "occurrence": placed[1] if placed else None,
        }
        mark.update({field: case.get(field) for field in CASE_COPY_FIELDS})
        mark["verdict"] = judgment.get("verdict")
        mark["reason"] = judgment.get("reason")
        mark["source"] = {"wave": wave, "case_id": case_id}
        mark["text_sha256"] = digests.get(case["doc"])
        if case_id in iaa:
            mark["iaa"] = dict(iaa[case_id])
            mark["iaa_agrees"] = iaa[case_id]["verdict"] == mark["verdict"]
        marks.append(mark)
    return marks


def build_recall_mentions(pages: dict, wave: str) -> list[dict]:
    """One record per read mention, page by page in page-ref order.

    A ``hit`` is the observation of a mark verified as correct on the facsimile, so the
    store holds positive evidence from both samples.
    """
    mentions = []
    for page_ref in sorted(pages):
        page = pages[page_ref]
        for mention in page.get("mentions") or []:
            record = {"doc": page["doc"], "page": page["page"],
                      "surface": mention["surface"], "gid": mention["gid"],
                      "status": mention["status"]}
            if mention["status"] == "missed":
                record["cause"] = mention.get("cause")
            record["note"] = mention.get("note")
            record["source"] = {"wave": wave, "page_ref": page_ref}
            mentions.append(record)
    return mentions


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def _normalize_gid(gid: str) -> str:
    return str(gid).strip().replace(" ", "").upper()


def validate(report: dict, cases, gids: set[str], drawn_pages: dict,
             placement: dict) -> list[str]:
    """Hard integrity errors; an empty list means the store may be written."""
    errors: list[str] = []
    marks = report["marks"]

    seen = Counter(mark["source"]["case_id"] for mark in marks)
    for case in cases:
        count = seen.get(case["case_id"], 0)
        if count != 1:
            errors.append(f"case {case['case_id']} resolves to {count} mark(s), expected 1")
    for case_id in sorted(set(seen) - {case["case_id"] for case in cases}):
        errors.append(f"mark {case_id} has no case in the drawn sample")
    if len(marks) != len(cases):
        errors.append(f"mark count {len(marks)} does not match {len(cases)} drawn cases")

    normalized = {_normalize_gid(gid) for gid in gids}
    used = {mark["gid"] for mark in marks} | {m["gid"] for m in report["recall_mentions"]}
    for gid in sorted(used - gids):
        hint = " (matches only after normalization)" if _normalize_gid(gid) in normalized else ""
        errors.append(f"gid {gid} is not in the curated entity list{hint}")

    keys = Counter((m["doc"], m["page"], m["surface"], m["gid"], m["occurrence"])
                   for m in marks)
    for key, count in sorted(keys.items(), key=lambda kv: str(kv[0])):
        if count > 1:
            errors.append(f"duplicate mark key {key} ({count} records)")

    by_case = {case["case_id"]: case for case in cases}
    for mark in marks:
        case = by_case.get(mark["source"]["case_id"])
        if case is None:
            continue
        placed = placement.get((case["doc"], case["start"]))
        if placed is None:
            errors.append(f"case {case['case_id']} is not located in the corpus scan snapshot")
            continue
        if placed[0] != mark["page"]:
            errors.append(f"case {case['case_id']}: page {mark['page']} disagrees with "
                          f"the scan page {placed[0]}")
        if mark["verdict"] is None:
            errors.append(f"case {case['case_id']} carries no verdict")
        if not mark["text_sha256"]:
            errors.append(f"case {case['case_id']}: no delivered TEI for document {case['doc']}")

    for mention in report["recall_mentions"]:
        page_ref = mention["source"]["page_ref"]
        drawn = drawn_pages.get(page_ref)
        if drawn is None:
            errors.append(f"recall page {page_ref} is not in the drawn sample")
        elif drawn != (mention["doc"], mention["page"]):
            errors.append(f"recall page {page_ref} sits on {mention['doc']}/{mention['page']}, "
                          f"drawn was {drawn[0]}/{drawn[1]}")
        if mention["status"] == "missed" and not mention.get("cause"):
            errors.append(f"recall page {page_ref}: missed mention without cause")
    return errors


def check_distributions(report: dict) -> list[str]:
    """Deviations from the adjudicated wave result; reported, never repaired.

    Only the wave named in SNAPSHOT carries a pinned expectation here; any other wave
    passes through unmeasured until its own result is written down.
    """
    if report.get("snapshot") != SNAPSHOT:
        return []
    anomalies = []
    precision = dict(Counter(mark["verdict"] for mark in report["marks"]))
    if precision != EXPECTED_PRECISION:
        anomalies.append(f"precision distribution {precision} != expected {EXPECTED_PRECISION}")
    recall = dict(Counter(m["status"] for m in report["recall_mentions"]))
    if recall != EXPECTED_RECALL:
        anomalies.append(f"recall distribution {recall} != expected {EXPECTED_RECALL}")
    with_iaa = [mark for mark in report["marks"] if "iaa" in mark]
    if len(with_iaa) != EXPECTED_IAA_CASES:
        anomalies.append(f"iaa cases {len(with_iaa)} != expected {EXPECTED_IAA_CASES}")
    disagreeing = tuple(sorted(mark["source"]["case_id"] for mark in with_iaa
                               if not mark["iaa_agrees"]))
    if disagreeing != tuple(sorted(EXPECTED_IAA_DISAGREEMENTS)):
        anomalies.append(f"iaa disagreements {list(disagreeing)} != "
                         f"expected {list(EXPECTED_IAA_DISAGREEMENTS)}")
    return anomalies


# ---------------------------------------------------------------------------
# Assembly
# ---------------------------------------------------------------------------

def load_inputs(*, sample_dir: Path = SAMPLE_DIR, entities_path: Path = ENTITIES_PATH,
                tei_dir: Path = TEI_FINAL_DIR) -> dict:
    """Everything the wave is built from, read once.

    Everything wave-specific comes from ``sample_dir``, the frozen scan included; only
    the curated entity list and the delivered TEI are read from the working tree.
    """
    sample_dir = Path(sample_dir)
    scan_path = frozen_scan_path(sample_dir)
    verdicts_dir = sample_dir / "verdicts"
    precision_paths = sorted(verdicts_dir.glob("precision_p*.json"))
    recall_paths = sorted(verdicts_dir.glob("recall_r*.json"))
    iaa_path = verdicts_dir / "precision_iaa.json"
    cases_path = sample_dir / "precision_cases.json"
    pages_path = sample_dir / "recall_pages.json"
    manifest_path = sample_dir / "sample_manifest.json"

    required = {"precision_cases.json": cases_path, "recall_pages.json": pages_path,
                "sample_manifest.json": manifest_path,
                "verdicts/precision_iaa.json": iaa_path}
    missing = sorted(name for name, path in required.items() if not path.exists())
    missing += [f"verdicts/{pattern}" for pattern, found
                in (("precision_p*.json", precision_paths), ("recall_r*.json", recall_paths))
                if not found]
    if missing:
        raise FileNotFoundError(f"{repo_path(sample_dir)} carries no complete adjudication, "
                                f"missing: {', '.join(missing)}")

    cases = read_json_strict(cases_path)
    manifest = read_json_strict(manifest_path)
    docs = [case["doc"] for case in cases]
    scan_bytes = scan_path.read_bytes()
    scan = json.loads(scan_bytes.decode("utf-8"))

    sources = [repo_path(p) for p in [cases_path, pages_path, manifest_path, iaa_path,
                                      Path(entities_path), scan_path,
                                      *precision_paths, *recall_paths]]
    sources.append(repo_path(tei_dir))
    return {
        "snapshot": snapshot_label(manifest),
        "scan_sha256": hashlib.sha256(scan_bytes).hexdigest(),
        "cases": cases,
        "verdicts": load_precision_verdicts(precision_paths),
        "iaa": load_iaa(iaa_path),
        "recall_pages": load_recall_pages(recall_paths),
        "drawn_pages": {page["case_id"]: (page["doc"], page["page"])
                        for page in read_json_strict(pages_path)},
        "gids": entity_gids(read_json_strict(entities_path)),
        "placement": occurrence_map(scan.get("candidates", []), pb_index(docs, Path(tei_dir))),
        "digests": text_digests(docs, Path(tei_dir)),
        "sources": sorted(set(sources)),
    }


def assemble(inputs: dict) -> dict:
    """The payload of one wave, in the documented key order."""
    snapshot = inputs["snapshot"]
    return {
        "snapshot": snapshot,
        "sources": inputs["sources"],
        "scan_sha256": inputs["scan_sha256"],
        "marks": build_marks(inputs["cases"], inputs["verdicts"], inputs["iaa"],
                             inputs["placement"], inputs["digests"],
                             PRECISION_WAVE.format(snapshot=snapshot)),
        "recall_mentions": build_recall_mentions(inputs["recall_pages"],
                                                 RECALL_WAVE.format(snapshot=snapshot)),
    }


def build_report(**paths) -> dict:
    return assemble(load_inputs(**paths))


def _snapshot_entry(snapshot: str, sources: list[str], scan_sha256: str | None) -> dict:
    return {"snapshot": snapshot, "sources": list(sources), "scan_sha256": scan_sha256}


def _merge_records(existing_records: list[dict], new_records: list[dict],
                   own_waves: set[str]) -> list[dict]:
    """Records of other waves first kept, then the rebuilt wave, in snapshot order."""
    kept = [record for record in existing_records
            if (record.get("source") or {}).get("wave") not in own_waves]
    return sorted([*kept, *new_records], key=record_snapshot)


def merge_store(existing: dict | None, wave: dict) -> dict:
    """Fold one built wave into the store: its own records replaced, other waves kept.

    A record belongs to the wave named in ``source.wave``, so rebuilding one wave never
    touches the judgments of another. Waves are emitted in ascending snapshot order and
    keep their internal order, which makes a rebuild byte-stable. ``snapshot`` stays the
    latest label and ``sources`` the union over all waves, so a reader written for the
    single-wave store keeps working; ``snapshots`` carries the per-wave detail. A store
    written before that list is lifted from its top-level keys.
    """
    existing = existing or {}
    snapshot = wave["snapshot"]
    own_waves = {PRECISION_WAVE.format(snapshot=snapshot),
                 RECALL_WAVE.format(snapshot=snapshot)}
    marks = _merge_records(existing.get("marks") or [], wave["marks"], own_waves)
    recall = _merge_records(existing.get("recall_mentions") or [],
                            wave["recall_mentions"], own_waves)

    entries = {snapshot: _snapshot_entry(snapshot, wave["sources"],
                                         wave.get("scan_sha256"))}
    for entry in existing.get("snapshots") or []:
        entries.setdefault(entry["snapshot"], entry)
    if existing.get("snapshot"):
        entries.setdefault(existing["snapshot"],
                           _snapshot_entry(existing["snapshot"],
                                           existing.get("sources") or [], None))
    # a record without a wave name belongs to no listed snapshot, but is still kept
    present = {label for record in (*marks, *recall)
               if (label := record_snapshot(record))} | {snapshot}
    snapshots = [entries.get(label) or _snapshot_entry(label, [], None)
                 for label in sorted(present)]
    return {
        "snapshot": max(present),
        "sources": sorted({source for entry in snapshots for source in entry["sources"]}),
        "snapshots": snapshots,
        "marks": marks,
        "recall_mentions": recall,
    }


def serialize(report: dict) -> str:
    return json.dumps(report, ensure_ascii=False, indent=2) + "\n"


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _print_summary(report: dict) -> None:
    precision = Counter(mark["verdict"] for mark in report["marks"])
    recall = Counter(mention["status"] for mention in report["recall_mentions"])
    with_iaa = [mark for mark in report["marks"] if "iaa" in mark]
    print(f"\n  Snapshot {report['snapshot']}  sources {len(report['sources'])}")
    print(f"\n  Marks: {len(report['marks'])}")
    for verdict, count in sorted(precision.items(), key=lambda kv: (-kv[1], kv[0])):
        print(f"    {verdict:16} {count:5}")
    print(f"\n  Recall mentions: {len(report['recall_mentions'])}")
    for status, count in sorted(recall.items(), key=lambda kv: (-kv[1], kv[0])):
        print(f"    {status:16} {count:5}")
    disagreeing = sorted(mark["source"]["case_id"] for mark in with_iaa
                         if not mark["iaa_agrees"])
    print(f"\n  IAA: {len(with_iaa)} cases, {len(disagreeing)} disagreement(s) "
          f"{' '.join(disagreeing) if disagreeing else '-'}")
    print(f"  Documents fingerprinted: {len({mark['doc'] for mark in report['marks']})}")


def _print_store_summary(store: dict) -> None:
    waves = " ".join(entry["snapshot"] for entry in store["snapshots"])
    print(f"\n  Store waves: {waves}")
    print(f"  Store totals: {len(store['marks'])} marks, "
          f"{len(store['recall_mentions'])} recall mentions")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build the mention-level verdict store from the adjudication evidence")
    parser.add_argument("--sample-dir", type=Path, default=SAMPLE_DIR,
                        help="drawn evaluation sample of the wave to build")
    parser.add_argument("--dry-run", action="store_true",
                        help="build and validate, write nothing")
    args = parser.parse_args(argv)

    try:
        inputs = load_inputs(sample_dir=args.sample_dir)
    except (FileNotFoundError, ValueError) as exc:
        print(f"FEHLER {exc}", file=sys.stderr)
        return 1
    report = assemble(inputs)
    errors = validate(report, inputs["cases"], inputs["gids"], inputs["drawn_pages"],
                      inputs["placement"])
    store = merge_store(read_json_strict(OUT_PATH) if OUT_PATH.exists() else None, report)
    _print_summary(report)
    _print_store_summary(store)

    if errors:
        print(f"\n  VALIDATION FAILED ({len(errors)} error(s)); nothing written:")
        for error in errors:
            print(f"    - {error}")
        return 1

    anomalies = check_distributions(report)
    if args.dry_run:
        print(f"\n  DRY RUN: {repo_path(OUT_PATH)} not written")
    else:
        OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        OUT_PATH.write_text(serialize(store), encoding="utf-8")
        print(f"\n  Store: {repo_path(OUT_PATH)}")

    if anomalies:
        print("\n  !! DISTRIBUTION DEVIATES FROM THE ADJUDICATED WAVE (nothing adjusted):")
        for anomaly in anomalies:
            print(f"    - {anomaly}")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
