"""Condense the entity corpus scan into a context-window-sized digest.

Reads the snapshot of scripts.entity.entity_corpus_scan and aggregates the raw
candidate list (one record per mention) into one block per entity: distinct
surface/rule pairs with counts and a single sample context. Tier 2 follows as
a per-rule summary. The digest is the review surface for the whole tier-1
harvest; the scan JSON stays the source of truth for per-mention detail.

Read-only; output belongs to output/audits/ (not versioned). A milestone that
needs frozen evidence copies the dated file to reports/.
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

from scripts.config import DATA_DIR
from scripts.eval.audit_common import AUDIT_OUTPUT_DIR

SCAN_PATH = AUDIT_OUTPUT_DIR / "entity_corpus_scan.json"
DIGEST_PATH = AUDIT_OUTPUT_DIR / "entity_corpus_digest.md"
ENTITIES_PATH = DATA_DIR / "entities" / "all_entities.json"

MAX_TIER2_SURFACES = 15

_LABEL_FIELD = {"persons": "name", "organisations": "orgName", "works": "title"}


def load_labels(entities_path: Path) -> dict[str, str]:
    entities = json.loads(Path(entities_path).read_text(encoding="utf-8"))
    labels: dict[str, str] = {}
    for list_key, field in _LABEL_FIELD.items():
        for entry in entities.get(list_key, []) or []:
            gid = str(entry.get("GND_id") or "").strip()
            label = " ".join(str(entry.get(field) or "").split())
            if gid and label:
                labels[gid] = label
    return labels


def build_digest(scan: dict, labels: dict[str, str]) -> str:
    tier1 = defaultdict(lambda: defaultdict(lambda: {"count": 0, "docs": set(), "context": ""}))
    tier1_totals: dict[str, int] = defaultdict(int)
    tier1_docs: dict[str, set] = defaultdict(set)
    tier2 = defaultdict(lambda: defaultdict(lambda: {"count": 0, "docs": set(), "gids": set()}))
    tier2_totals: dict[str, int] = defaultdict(int)

    for cand in scan.get("candidates", []):
        key = (cand["surface"], cand["rule"])
        if cand["tier"] == 1:
            slot = tier1[cand["gid"]][key]
            slot["count"] += 1
            slot["docs"].add(cand["doc"])
            if not slot["context"]:
                slot["context"] = cand.get("context", "")
            tier1_totals[cand["gid"]] += 1
            tier1_docs[cand["gid"]].add(cand["doc"])
        else:
            slot = tier2[cand["rule"]][cand["surface"]]
            slot["count"] += 1
            slot["docs"].add(cand["doc"])
            slot["gids"].add(cand["gid"])
            tier2_totals[cand["rule"]] += 1

    lines = ["# Entity corpus digest", ""]
    totals = scan.get("totals", {})
    lines.append(
        f"Aggregated from the corpus scan: {totals.get('tier1', 0)} tier-1 and "
        f"{totals.get('tier2', 0)} tier-2 candidates. Source of truth per mention: "
        "`output/audits/entity_corpus_scan.json`."
    )

    lines += ["", "## Tier 1 by entity", ""]
    for gid in sorted(tier1_totals, key=lambda g: (-tier1_totals[g], g)):
        label = labels.get(gid, "(label unknown)")
        lines.append(f"### {label} ({gid}) | {tier1_totals[gid]} hits in {len(tier1_docs[gid])} docs")
        forms = tier1[gid]
        for surface, rule in sorted(forms, key=lambda k: (-forms[k]["count"], k)):
            slot = forms[(surface, rule)]
            context = " ".join(slot["context"].split())[:90]
            lines.append(
                f"- `{surface}` | {rule} | {slot['count']}x in {len(slot['docs'])} docs | \"{context}\""
            )
        lines.append("")

    lines += ["## Tier 2 by rule", ""]
    for rule in sorted(tier2_totals, key=lambda r: (-tier2_totals[r], r)):
        surfaces = tier2[rule]
        lines.append(f"### {rule} | {tier2_totals[rule]} candidates, {len(surfaces)} distinct surfaces")
        ordered = sorted(surfaces, key=lambda s: (-surfaces[s]["count"], s))
        for surface in ordered[:MAX_TIER2_SURFACES]:
            slot = surfaces[surface]
            owners = ", ".join(
                labels.get(g, g) for g in sorted(slot["gids"])[:3]
            ) + (" ..." if len(slot["gids"]) > 3 else "")
            lines.append(
                f"- `{surface}` | {slot['count']}x in {len(slot['docs'])} docs | {owners}"
            )
        if len(ordered) > MAX_TIER2_SURFACES:
            lines.append(f"- ... {len(ordered) - MAX_TIER2_SURFACES} further surfaces in the scan JSON")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Entity corpus digest (read-only)")
    parser.add_argument("--scan", type=Path, default=SCAN_PATH, help="Corpus scan JSON")
    parser.add_argument("--entities", type=Path, default=ENTITIES_PATH, help="Curated entity list")
    parser.add_argument("--out", type=Path, default=DIGEST_PATH, help="Digest markdown path")
    args = parser.parse_args()

    scan = json.loads(args.scan.read_text(encoding="utf-8"))
    digest = build_digest(scan, load_labels(args.entities))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(digest, encoding="utf-8")

    entity_count = digest.count("\n### ")
    print(f"Digest: {args.out}")
    print(f"  lines: {digest.count(chr(10))}  entity blocks + rule blocks: {entity_count}")


if __name__ == "__main__":
    main()
