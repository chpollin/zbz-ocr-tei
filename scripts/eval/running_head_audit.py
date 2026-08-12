"""Deterministic detector for running heads (Kolumnentitel) at page starts.

Operator convention E105 keeps running heads out of the entity layer: the author name or
work title printed as page furniture on every page is not a mention of the person or the
work. The convention names a deterministic suppression instrument as its follow-up. This
module builds the measurement half of it -- it locates the head zones and scores them
against the facsimile-adjudicated ground truth, so the suppression can later be switched
on with a known recall and a known false-alarm cost. Nothing here writes TEI and nothing
here touches the matcher.

Detection, applied per document to output/tei_final/{doc}_final.xml:

  1. Page starts are the `<pb>` positions inside `<body>`, taken from the shared
     segmentation of scripts.tei.pb_split (read only), so the page numbering matches the
     rest of the pipeline.
  2. The head window of a page is its first MAX_HEAD_SEGMENTS non-empty segments. A
     segment ends at every line or block tag (`<lb/>`, `<p>`, `<head>`, ...); inline
     markup stays inside it. Whitespace-only and pure-number segments are skipped without
     consuming a slot of the window, because the printed folio often stands alone in its
     own line ahead of the head.
  3. A segment is normalized for recurrence: inline markup dropped, whitespace collapsed,
     apostrophe variants unified, diacritics folded (the same OCR word appears with and
     without accents across the corpus), casefolded, leading and trailing digits and
     punctuation stripped -- the printed page number rides along with the head and varies
     per page.
  4. A normalized form recurring on MIN_RECURRENCE distinct pages of the document is a
     head pattern. Alternating verso/recto heads (author on one side, work title on the
     other) need no separate rule at this step: each of the two forms still recurs on its
     own half of the pages. In a short document that halving can push the counterpart
     below the threshold, so inside a document that already carries a primary pattern a
     second form recurring on MIN_COMPANION_RECURRENCE pages is accepted as its companion.
  5. A one-off segment that contains a primary form as a whole word and stays within
     CONTAINS_LENGTH_FACTOR of its length is accepted too; OCR merges the folio or the
     author prefix into the head line on single pages.

Speaker labels are excluded: `<speaker>` is a structural element of the recorded
discussions, and the speaker name at a page start is a real mention rather than page
furniture.

DIAGNOSIS ONLY -- reads output/tei_final, the adjudicated verdicts and the corpus scan
snapshot, writes one report and is no pass/fail gate.

Usage:
    python -m scripts.eval.running_head_audit
    python -m scripts.eval.running_head_audit --dir other_tei --out other.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import unicodedata
from bisect import bisect_right
from collections import defaultdict
from pathlib import Path

from scripts.config import DATA_DIR, TEI_FINAL_DIR
from scripts.eval.audit_common import AUDIT_OUTPUT_DIR, doc_id_from_path
from scripts.tei.pb_split import BODY_INNER_RE, PB_RE

SNAPSHOT = "2026-08-12"

VERDICTS_PATH = DATA_DIR / "entities" / "mention_verdicts.json"
SCAN_PATH = AUDIT_OUTPUT_DIR / "entity_corpus_scan.json"
REPORT_PATH = AUDIT_OUTPUT_DIR / "running_head_audit.json"

# Detection constants. Calibrated against the 25 facsimile-adjudicated running-head marks
# of data/entities/mention_verdicts.json; every value is deliberately on the conservative
# side, because a false alarm costs a real entity mention while a miss only leaves a head
# unsuppressed.
MAX_HEAD_SEGMENTS = 2       # head window: first non-empty segments of a page
MIN_HEAD_CHARS = 2          # below this a normalized form is noise
MAX_HEAD_CHARS = 80         # a head line is short; body prose is not
MIN_RECURRENCE = 3          # distinct pages carrying the form -> primary pattern
MIN_COMPANION_RECURRENCE = 2  # alternating counterpart in a document with a primary
CONTAINS_LENGTH_FACTOR = 2.0  # a merged head variant stays close to the primary length

TAG_RE = re.compile(r"<\s*(/?)\s*([A-Za-z][\w:.-]*)[^>]*>")

# Inline markup stays inside a segment; every other element ends one. The whitelist is the
# safe direction: an unknown element becomes a boundary rather than silently gluing two
# printed lines into one candidate.
INLINE_TAGS = frozenset({
    "hi", "foreign", "title", "sic", "corr", "choice", "orig", "reg", "unclear",
    "supplied", "add", "del", "ref", "persName", "name", "rs", "orgName", "placeName",
    "date", "abbr", "expan", "seg", "q", "emph", "gap", "space", "num", "g", "c",
})

# A speaker label is a structural element of the discussion transcripts, not page
# furniture; its name is a real mention even when it opens a page.
EXCLUDED_PARENT_TAGS = frozenset({"speaker"})

APOSTROPHES = {0x2018: "'", 0x2019: "'", 0x201B: "'", 0x02BC: "'", 0x00B4: "'", 0x0060: "'"}

RUNNING_HEAD_REASON = "running head"
CORRECT_VERDICT = "correct"
TIER_1 = 1
TOP_PRINTED = 12


# ---------------------------------------------------------------------------
# Normalization and page segmentation
# ---------------------------------------------------------------------------

def normalize_head(raw: str) -> str:
    """Recurrence key of a page-start segment; empty when nothing but furniture is left."""
    text = " ".join(TAG_RE.sub(" ", raw).split())
    text = text.translate(APOSTROPHES)
    text = "".join(c for c in unicodedata.normalize("NFD", text)
                   if not unicodedata.combining(c))
    text = text.casefold()
    text = re.sub(r"^[\W\d_]+", "", text)
    text = re.sub(r"[\W\d_]+$", "", text)
    return " ".join(text.split())


def head_window(xml_text: str, lo: int, hi: int) -> list[dict]:
    """The first MAX_HEAD_SEGMENTS non-empty segments of the page span [lo, hi).

    Offsets are absolute in `xml_text`, so a zone can be looked up against the mark
    offsets of the entity wave, which index the same stream.
    """
    raw: list[tuple[int, int, str]] = []
    cursor, stack = lo, []
    for match in TAG_RE.finditer(xml_text, lo, hi):
        name = match.group(2)
        if name in INLINE_TAGS:
            continue
        if match.start() > cursor:
            raw.append((cursor, match.start(), stack[-1] if stack else ""))
        if match.group(1) == "/":
            if stack and stack[-1] == name:
                stack.pop()
        elif not match.group(0).rstrip().endswith("/>"):
            stack.append(name)
        cursor = match.end()
    if hi > cursor:
        raw.append((cursor, hi, stack[-1] if stack else ""))

    window = []
    for start, end, parent in raw:
        form = normalize_head(xml_text[start:end])
        if not form:
            continue
        window.append({"start": start, "end": end, "form": form, "parent": parent,
                       "position": len(window),
                       "text": " ".join(TAG_RE.sub(" ", xml_text[start:end]).split())})
        if len(window) >= MAX_HEAD_SEGMENTS:
            break
    return window


def page_candidates(xml_text: str) -> tuple[int, dict[str, list[dict]]]:
    """(page count, normalized form -> its page-start occurrences) for one document."""
    body = BODY_INNER_RE.search(xml_text)
    if not body:
        return 0, {}
    base, inner = body.start(1), body.group(1)
    breaks = list(PB_RE.finditer(inner))
    by_form: dict[str, list[dict]] = defaultdict(list)
    for index, pb in enumerate(breaks):
        end = breaks[index + 1].start() if index + 1 < len(breaks) else len(inner)
        for segment in head_window(xml_text, base + pb.end(), base + end):
            if segment["parent"] in EXCLUDED_PARENT_TAGS:
                continue
            if not MIN_HEAD_CHARS <= len(segment["form"]) <= MAX_HEAD_CHARS:
                continue
            by_form[segment["form"]].append(dict(segment, page=index + 1))
    return len(breaks), dict(by_form)


# ---------------------------------------------------------------------------
# Detection
# ---------------------------------------------------------------------------

def _pages_of(occurrences: list[dict]) -> set[int]:
    return {occurrence["page"] for occurrence in occurrences}


def _accept(by_form: dict[str, list[dict]]) -> dict[str, str]:
    """Accepted forms mapped to the rule that accepted them, applied in a fixed order."""
    accepted = {form: "primary" for form, occurrences in by_form.items()
                if len(_pages_of(occurrences)) >= MIN_RECURRENCE}
    if not accepted:
        return accepted
    primary = sorted(accepted)
    for form, occurrences in by_form.items():
        if form not in accepted and len(_pages_of(occurrences)) >= MIN_COMPANION_RECURRENCE:
            accepted[form] = "companion"
    for form in sorted(by_form):
        if form in accepted:
            continue
        for base in primary:
            if len(form) <= CONTAINS_LENGTH_FACTOR * len(base) and re.search(
                    r"(?:^|\W)" + re.escape(base) + r"(?:\W|$)", form):
                accepted[form] = "contains"
                break
    return accepted


def _parity(pages: list[int]) -> str:
    """Page parity of a pattern; an alternating verso/recto head lands on one side."""
    remainders = {page % 2 for page in pages}
    if len(remainders) > 1:
        return "mixed"
    return "odd" if remainders == {1} else "even"


def detect_document(xml_text: str) -> dict:
    """Head patterns of one document, ordered by normalized form."""
    page_count, by_form = page_candidates(xml_text)
    accepted = _accept(by_form)
    patterns = []
    for form in sorted(accepted):
        occurrences = sorted(by_form[form], key=lambda o: (o["page"], o["start"]))
        pages = sorted(_pages_of(occurrences))
        patterns.append({
            "form": form,
            "kind": accepted[form],
            "pages": pages,
            "page_parity": _parity(pages),
            "segment_positions": sorted({o["position"] for o in occurrences}),
            "parent_elements": sorted({o["parent"] for o in occurrences}),
            "zones": [{"page": o["page"], "start": o["start"], "end": o["end"],
                       "text": o["text"]} for o in occurrences],
        })
    return {"pages": page_count, "patterns": patterns}


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
# Zone lookup
# ---------------------------------------------------------------------------

def zone_lookup(documents: list[dict]):
    """(doc, offset) -> the zone containing the offset, or None."""
    index: dict[str, tuple[list[int], list[dict]]] = {}
    for document in documents:
        zones = [dict(zone, form=pattern["form"], kind=pattern["kind"])
                 for pattern in document["patterns"] for zone in pattern["zones"]]
        zones.sort(key=lambda z: z["start"])
        index[document["doc"]] = ([z["start"] for z in zones], zones)

    def resolve(doc: str, offset: int) -> dict | None:
        starts, zones = index.get(doc, ([], []))
        position = bisect_right(starts, offset) - 1
        if position < 0:
            return None
        zone = zones[position]
        return zone if zone["start"] <= offset < zone["end"] else None

    return resolve


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
        "corpus_impact": corpus_impact(scan, lookup),
        "documents": [{"doc": d["doc"], "pages": d["pages"], "patterns": d["patterns"]}
                      for d in documents if d["patterns"]],
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _ascii(text) -> str:
    """Fold to ASCII for the Windows console (the JSON report keeps full Unicode)."""
    return str(text).encode("ascii", "replace").decode("ascii")


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
              f"{_ascii(miss['surface'])}")
    print(f"\n  False alarms on other correct marks: "
          f"{others['in_zone']}/{others['total']} ({others['false_alarm_rate']})")
    for case in others["cases"]:
        print(f"    ALARM {case['doc']:>5} p{case['page']} @{case['start']} "
              f"{_ascii(case['surface'])} -> {case['zone']['kind']} "
              f"'{_ascii(case['zone']['form'])[:40]}'")
        print(f"          reason: {_ascii(case['reason'])[:110]}")
    if validation["tei_drift"]:
        print(f"\n  WARNING: TEI changed since adjudication in "
              f"{', '.join(validation['tei_drift'])}; offsets may be stale.")

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
