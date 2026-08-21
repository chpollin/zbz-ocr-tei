"""Risk ranking of the tier-1 entity marks (false-positive hunt).

Reads the corpus scan snapshot output/audits/entity_corpus_scan.json, scores every
tier-1 mark with additive, deterministic risk features and writes the ranked case list
to output/audits/fp_hunt/risk_ranking.json. The adjudication wave works the strata top
down, so the checked sample is bought where a false positive is most likely instead of
spread evenly over thousands of marks. The binding wave protocol lives next to the
ranking in output/audits/fp_hunt/PROTOCOL.md.

Score contributions, additive per mark:

  variant_form_source  +2  the matched form is not the list headword (variant channel)
  case_tolerant_rule   +2  the rule matched through the all-caps channel
  single_token_surface +2  the surface is one word (homograph and short-title risk)
  short_surface        +1  the markup-free surface is at most five characters
  category_work        +1  works carry the weakest title evidence
  shared_surname_gid   +1  the gid shares a bare surname with another listed person
  anomaly             +99  a state the tier rule excludes (see anomalies_of)

Strata: high >= 4, medium 2-3, low 0-1.

DIAGNOSIS ONLY -- reads the scan snapshot, the entity list and, only for a snapshot
without page numbers, output/tei_final; writes one report and is no pass/fail gate.

The page comes from the scan snapshot, which resolves it once for every candidate. The
pb reading below stays as the fallback for snapshots written before the scan carried the
field, so an archived ranking can still be reproduced from its own inputs.

Usage:
    python -m scripts.entity.entity_risk_ranking
    python -m scripts.entity.entity_risk_ranking --scan other_scan.json --out other.json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

from scripts.config import DATA_DIR, TEI_FINAL_DIR
from scripts.core.pb_split import page_of, pb_offsets
from scripts.entity.entity_matcher import base_rule
from scripts.eval.audit_common import AUDIT_OUTPUT_DIR, ascii_only, facsimile_path

# Label of the fp-hunt ranking wave (PROTOCOL.md); the ranking reads no verdict store.
SNAPSHOT = "2026-08-12"

ENTITIES_PATH = DATA_DIR / "entities" / "all_entities.json"
SCAN_PATH = AUDIT_OUTPUT_DIR / "entity_corpus_scan.json"
FP_HUNT_DIR = AUDIT_OUTPUT_DIR / "fp_hunt"
REPORT_PATH = FP_HUNT_DIR / "risk_ranking.json"

ANOMALY_FEATURE = "anomaly"
FEATURE_ORDER = (
    "variant_form_source",
    "case_tolerant_rule",
    "single_token_surface",
    "short_surface",
    "category_work",
    "shared_surname_gid",
    ANOMALY_FEATURE,
)
WEIGHTS = {
    "variant_form_source": 2,
    "case_tolerant_rule": 2,
    "single_token_surface": 2,
    "short_surface": 1,
    "category_work": 1,
    "shared_surname_gid": 1,
    ANOMALY_FEATURE: 99,
}

HEADWORD_SOURCE = "headword"
SHORT_SURFACE_MAX = 5
HIGH_MIN = 4
MEDIUM_MIN = 2
TOP_PRINTED = 10

# The matcher writes the all-caps channel as a "caps-" base rule; the case-tolerant
# path (a form written in deviating case) always drops to tier 2 with ":suspect" and
# therefore never reaches this ranking as its own rule string.
CASE_TOLERANT_PREFIX = "caps-"
CASE_TOLERANT_EXCLUDED = {
    "org-token": "matches a distinctive organisation token regardless of case; its "
                 "risk is already carried by single_token_surface",
    "org-variant": "variant channel, case-sensitive; all-caps hits arrive through the "
                   "variant form itself, counted as variant_form_source",
}

SUSPECT_SUFFIX = ":suspect"
TAG_RE = re.compile(r"<[^>]*>")


def is_case_tolerant_rule(rule: str) -> bool:
    """True for the all-caps channel of the matcher."""
    return base_rule(rule).startswith(CASE_TOLERANT_PREFIX)


# ---------------------------------------------------------------------------
# Surfaces and lexicon signals
# ---------------------------------------------------------------------------

def plain_surface(surface: str) -> str:
    """The surface without inline markup (`<lb/>` inside a name), whitespace collapsed."""
    return " ".join(TAG_RE.sub(" ", surface).split())


def surface_tokens(surface: str) -> list[str]:
    """Whitespace tokens of the markup-free surface."""
    return plain_surface(surface).split()


def _fold(text: str) -> str:
    """Accent- and case-insensitive key for surname comparison."""
    decomposed = unicodedata.normalize("NFD", text)
    return "".join(c for c in decomposed if not unicodedata.combining(c)).casefold()


def shared_surname_gids(entities: dict) -> frozenset[str]:
    """Gids of persons whose bare surname is borne by at least one other listed person.

    The bare surname is the part before the first comma of the list headword, so a
    mononym counts as its own surname. Organisations and works are out of scope: their
    ambiguity is not a surname collision.
    """
    by_surname: dict[str, set[str]] = defaultdict(set)
    for person in entities.get("persons") or []:
        gid = person.get("GND_id")
        name = person.get("name") or ""
        if not gid or not name:
            continue
        by_surname[_fold(name.split(",")[0].strip())].add(gid)
    return frozenset(gid for gids in by_surname.values() if len(gids) > 1 for gid in gids)


def listed_gids(entities: dict) -> frozenset[str]:
    """Every gid of the curated list, across the three categories."""
    return frozenset(entry["GND_id"] for group in entities.values()
                     for entry in group if entry.get("GND_id"))


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------

def features_of(record: dict, shared_surnames: frozenset[str]) -> list[str]:
    """Risk features of one mark, in the fixed feature order (anomalies excluded)."""
    found = set()
    if record.get("form_source", "") != HEADWORD_SOURCE:
        found.add("variant_form_source")
    if is_case_tolerant_rule(record.get("rule", "")):
        found.add("case_tolerant_rule")
    surface = record.get("surface", "")
    if len(surface_tokens(surface)) == 1:
        found.add("single_token_surface")
    if len(plain_surface(surface)) <= SHORT_SURFACE_MAX:
        found.add("short_surface")
    if record.get("category") == "work":
        found.add("category_work")
    if record.get("gid") in shared_surnames:
        found.add("shared_surname_gid")
    return [name for name in FEATURE_ORDER if name in found]


def anomalies_of(record: dict, listed: frozenset[str]) -> list[str]:
    """States the tier rule excludes; each one alone justifies a look at the mark."""
    found = []
    if record.get("gid") not in listed:
        found.append("gid_not_listed")
    if record.get("tier") == 1 and SUSPECT_SUFFIX in record.get("rule", ""):
        found.append("suspect_rule_in_tier1")
    return found


def score_of(features: list[str]) -> int:
    """Sum of the feature weights."""
    return sum(WEIGHTS[name] for name in features)


def stratum(score: int) -> str:
    """Risk stratum of a score."""
    if score >= HIGH_MIN:
        return "high"
    return "medium" if score >= MEDIUM_MIN else "low"


# ---------------------------------------------------------------------------
# Page assignment
# ---------------------------------------------------------------------------

def page_from(record: dict, page_fn) -> int | None:
    """Page of a scan record: its own field, or the pb fallback for an old snapshot."""
    if "page" in record:
        return record["page"]
    return page_fn(record["doc"], record["start"])


def page_resolver(tei_dir: Path):
    """(doc, offset) -> page, reading each final TEI once; None when the TEI is missing."""
    cache: dict[str, list[int] | None] = {}

    def resolve(doc: str, offset: int) -> int | None:
        if doc not in cache:
            path = Path(tei_dir) / f"{doc}_final.xml"
            cache[doc] = pb_offsets(path.read_bytes().decode("utf-8")) if path.exists() else None
        starts = cache[doc]
        return page_of(starts, offset) if starts is not None else None

    return resolve


# ---------------------------------------------------------------------------
# Ranking and report
# ---------------------------------------------------------------------------

def rank_marks(records: list[dict], shared_surnames: frozenset[str],
               listed: frozenset[str], page_fn) -> list[dict]:
    """Tier-1 marks as ranked cases: score desc, then doc, page, surface, offset.

    Case ids follow the risk order, so an agent range like f0001-f0050 is always the
    riskiest untouched block.
    """
    marks = []
    for record in records:
        if record.get("tier") != 1:
            continue
        features = features_of(record, shared_surnames)
        anomalies = anomalies_of(record, listed)
        if anomalies:
            features.append(ANOMALY_FEATURE)
        score = score_of(features)
        page = page_from(record, page_fn)
        mark = {
            "case_id": "",
            "doc": record["doc"],
            "page": page,
            "surface": record["surface"],
            "gid": record["gid"],
            "category": record["category"],
            "rule": record["rule"],
            "form_source": record.get("form_source", ""),
            "start": record["start"],
            "end": record["end"],
            "score": score,
            "stratum": stratum(score),
            "features": features,
            "facsimile": facsimile_path(record["doc"], page) if page is not None else None,
            "context": record.get("context", ""),
        }
        if anomalies:
            mark["anomalies"] = anomalies
        marks.append(mark)
    marks.sort(key=lambda m: (-m["score"], m["doc"], m["page"] if m["page"] is not None else -1,
                              m["surface"], m["start"]))
    for index, mark in enumerate(marks, start=1):
        mark["case_id"] = f"f{index:04d}"
    return marks


def feature_doc() -> dict:
    """The scoring contract as data, so the report explains its own numbers."""
    return {
        "scope": "tier-1 marks of the corpus scan; tier 2 and 3 are worklist material",
        "weights": WEIGHTS,
        "descriptions": {
            "variant_form_source": "matched form is not the list headword "
                                   "(surname index, GND cache variant, legacy form)",
            "case_tolerant_rule": "rule matched through the all-caps channel",
            "single_token_surface": "surface is a single word once inline markup is removed",
            "short_surface": f"markup-free surface is at most {SHORT_SURFACE_MAX} characters",
            "category_work": "work titles carry the weakest evidence of all categories",
            "shared_surname_gid": "the gid shares a bare surname with another listed "
                                  "person (computed from all_entities.json, persons only)",
            ANOMALY_FEATURE: "a state the tier rule excludes; listed separately",
        },
        "anomalies": {
            "suspect_rule_in_tier1": "rule carries ':suspect' although the mark is tier 1",
            "gid_not_listed": "the gid is absent from all_entities.json",
        },
        "case_tolerant_rules": {
            "treated_as_case_tolerant": ["caps-full-name", "caps-surname"],
            "criterion": f"base rule starts with '{CASE_TOLERANT_PREFIX}'",
            "excluded": CASE_TOLERANT_EXCLUDED,
            "note": "the matcher's case-tolerant path always drops to tier 2 with the "
                    "':suspect' suffix, so inside tier 1 the caps rules are the whole "
                    "case-tolerant channel",
        },
        "strata": {"high": f">= {HIGH_MIN}", "medium": f"{MEDIUM_MIN}-{HIGH_MIN - 1}",
                   "low": f"0-{MEDIUM_MIN - 1}"},
    }


def build_report(records: list[dict], entities: dict, sources: dict, page_fn) -> dict:
    """The full ranking snapshot; every view deterministic, no timestamp."""
    marks = rank_marks(records, shared_surname_gids(entities), listed_gids(entities), page_fn)
    counts = Counter(mark["stratum"] for mark in marks)
    return {
        "snapshot": SNAPSHOT,
        "source": sources,
        "feature_doc": feature_doc(),
        "strata_counts": {name: counts.get(name, 0) for name in ("high", "medium", "low")},
        "anomalies": [{"case_id": mark["case_id"], "doc": mark["doc"], "page": mark["page"],
                       "surface": mark["surface"], "gid": mark["gid"], "rule": mark["rule"],
                       "anomalies": mark["anomalies"]}
                      for mark in marks if mark.get("anomalies")],
        "marks": marks,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _print_summary(report: dict) -> None:
    marks = report["marks"]
    counts = report["strata_counts"]
    print(f"\n  Tier-1 marks ranked: {len(marks)}")
    for name in ("high", "medium", "low"):
        print(f"    {name:8} {counts[name]}")
    print(f"\n  Anomalies: {len(report['anomalies'])}")
    for item in report["anomalies"][:TOP_PRINTED]:
        print(f"    {item['case_id']} {item['doc']} p{item['page']}: "
              f"{ascii_only(item['surface'])} ({','.join(item['anomalies'])})")

    print(f"\n  Riskiest {TOP_PRINTED}:")
    for mark in marks[:TOP_PRINTED]:
        print(f"    {mark['case_id']}  score {mark['score']:3}  {mark['doc']:>5} "
              f"p{mark['page']}  {ascii_only(mark['surface'])[:40]:40} {ascii_only(mark['gid'])}")

    print("\n  By rule (high stratum):")
    high = Counter(mark["rule"] for mark in marks if mark["stratum"] == "high")
    for rule, count in sorted(high.items(), key=lambda kv: (-kv[1], kv[0])):
        print(f"    {ascii_only(rule):24} {count}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Risk ranking of the tier-1 entity marks (read-only diagnosis)")
    parser.add_argument("--scan", type=Path, default=SCAN_PATH,
                        help="Corpus scan snapshot (entity_corpus_scan.json)")
    parser.add_argument("--entities", type=Path, default=ENTITIES_PATH,
                        help="Curated entity list")
    parser.add_argument("--tei-dir", type=Path, default=TEI_FINAL_DIR,
                        help="TEI source for the page fallback of a scan snapshot "
                             "without page field (read only)")
    parser.add_argument("--out", type=Path, default=REPORT_PATH, help="Report path")
    args = parser.parse_args()

    if not args.scan.exists():
        print(f"  Corpus scan missing: {args.scan}")
        sys.exit(1)
    scan = json.loads(args.scan.read_text(encoding="utf-8"))
    entities = json.loads(args.entities.read_text(encoding="utf-8"))
    sources = {
        "scan": str(args.scan),
        "entities": str(args.entities),
        "tei_dir": str(args.tei_dir),
    }

    print(f"Risk ranking over {len(scan.get('candidates', []))} scan candidate(s); "
          f"nothing is written to TEI.")
    report = build_report(scan.get("candidates", []), entities, sources,
                          page_fn=page_resolver(args.tei_dir))
    _print_summary(report)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n  JSON report: {args.out}")


if __name__ == "__main__":
    main()
