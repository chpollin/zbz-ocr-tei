"""Draw the two evaluation samples of the entity layer (phase 1 of the workflow).

Implements section "1. Draw" of knowledge/entity-evaluation.md: one precision sample of
tier-1 marks out of the corpus scan, stratified by category and rule family, and one
recall sample of pages out of the delivered corpus, stratified by layout type and
language. Both draws are seeded (default 42) and reproducible; every cell of both
stratifications is written into the manifest with what was available and what was drawn,
so the sample itself is auditable.

Read-only with respect to the corpus: it reads the scan report, the catalog and the
delivered TEI (only to map a candidate offset onto its page) and writes exclusively into
the output directory.

Output (default output/audits/eval_sample/):
  precision_cases.json  drawn tier-1 marks, one adjudication case each (verdict null)
  recall_pages.json     drawn pages, one exhaustive-reading case each (mentions null)
  sample_manifest.json  seed, source files with timestamps and counters, strata tables

Usage:
    python -m scripts.entity.entity_eval_sample
    python -m scripts.entity.entity_eval_sample --precision-n 100 --recall-pages 20
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from datetime import UTC, datetime
from pathlib import Path

from scripts.config import PROJECT_ROOT, TEI_FINAL_DIR
from scripts.entity.entity_matcher import _base_rule

# Page assignment uses the pb rule of the per-page mirror (page = sequential <pb>
# position); a second implementation would place cases next to the wrong facsimile.
from scripts.entity.generate_entity_preview_data import (
    page_of as page_of_offset,
    pb_offsets as page_starts,
)
from scripts.eval.audit_common import AUDIT_OUTPUT_DIR

SCAN_PATH = AUDIT_OUTPUT_DIR / "entity_corpus_scan.json"
CATALOG_PATH = PROJECT_ROOT / "docs" / "data" / "catalog.json"
EVAL_SAMPLE_DIR = AUDIT_OUTPUT_DIR / "eval_sample"

DEFAULT_SEED = 42
DEFAULT_PRECISION_N = 300
DEFAULT_RECALL_PAGES = 40
PRECISION_MIN_PER_CELL = 3
RECALL_MIN_PER_CELL = 1

GENERATOR = "scripts/entity/entity_eval_sample.py"
CASE_FIELDS = ("doc", "surface", "start", "end", "gid", "category", "rule",
               "matched_form", "form_source", "context")


# ---------------------------------------------------------------------------
# Allocation
# ---------------------------------------------------------------------------

def allocate(available: dict, total: int, minimum: int) -> dict:
    """Draws per cell: minimum coverage first, the rest proportional to what is left.

    A cell holding fewer items than the minimum contributes all of them. When the
    minima alone exceed the budget, the largest allocations are trimmed first and only
    then whole cells are dropped, smallest first, so rare cells survive longest.
    """
    cells = {key: count for key, count in available.items() if count > 0}
    alloc = {key: min(minimum, count) for key, count in cells.items()}
    booked = sum(alloc.values())
    if booked > total:
        return _trim(alloc, cells, total)
    residual = {key: cells[key] - alloc[key] for key in cells}
    for key, extra in _proportional(residual, total - booked).items():
        alloc[key] += extra
    return alloc


def _proportional(residual: dict, amount: int) -> dict:
    """Largest-remainder distribution of ``amount`` over the residual capacities."""
    extra = dict.fromkeys(residual, 0)
    pool = {key: count for key, count in residual.items() if count > 0}
    capacity = sum(pool.values())
    if not pool or amount <= 0:
        return extra
    if amount >= capacity:
        return {**extra, **pool}
    quotas = {key: amount * count / capacity for key, count in pool.items()}
    for key, quota in quotas.items():
        extra[key] = int(quota)
    rest = amount - sum(extra.values())
    order = sorted(pool, key=lambda key: (-(quotas[key] - int(quotas[key])),
                                          -pool[key], _cell_label(key)))
    for key in order[:rest]:
        extra[key] += 1
    return extra


def _trim(alloc: dict, cells: dict, total: int) -> dict:
    """Reduce an over-booked minimum allocation to the budget, deterministically."""
    while sum(alloc.values()) > total:
        reducible = [key for key, count in alloc.items() if count > 1]
        if reducible:
            key = max(reducible, key=lambda k: (alloc[k], cells[k], _cell_label(k)))
            alloc[key] -= 1
            continue
        key = min(alloc, key=lambda k: (cells[k], _cell_label(k)))
        del alloc[key]
    return alloc


def _cell_label(key) -> str:
    """Stable string form of a cell key, used as the final tie-break."""
    return "|".join(str(part) for part in key) if isinstance(key, tuple) else str(key)


# ---------------------------------------------------------------------------
# Precision sample
# ---------------------------------------------------------------------------

def _page_index(tei_dir: Path, doc: str, cache: dict) -> list[int] | None:
    """<pb> offsets of a delivered TEI; None when the document has no final TEI."""
    if doc not in cache:
        path = Path(tei_dir) / f"{doc}_final.xml"
        cache[doc] = page_starts(path.read_bytes().decode("utf-8")) if path.exists() else None
    return cache[doc]


def facsimile_path(doc: str, page: int) -> str:
    """Repo-relative page image of a document page."""
    return f"docs/images/{doc}/{doc}_p{page:03d}.png"


def _precision_case(candidate: dict, case_id: str, page: int | None) -> dict:
    case = {"case_id": case_id, "doc": candidate["doc"], "page": page}
    case.update({field: candidate.get(field) for field in CASE_FIELDS if field != "doc"})
    case["facsimile"] = facsimile_path(candidate["doc"], page) if page is not None else None
    case["verdict"] = None
    case["reason"] = None
    return case


def draw_precision(candidates: list[dict], total: int, seed: int,
                   tei_dir: Path) -> tuple[list[dict], list[dict], int]:
    """Cases, strata table and the count of cases whose page could not be resolved.

    Only tier-1 marks are drawn; tier 2 is worklist material and is measured elsewhere.
    """
    cells: dict[tuple[str, str], list[dict]] = {}
    for candidate in candidates:
        if candidate.get("tier") != 1:
            continue
        key = (candidate.get("category", ""), _base_rule(candidate.get("rule", "")))
        cells.setdefault(key, []).append(candidate)
    for items in cells.values():
        items.sort(key=lambda c: (c["doc"], c["start"], c["gid"], c["rule"]))

    rng = random.Random(seed)
    alloc = allocate({key: len(items) for key, items in cells.items()}, total,
                     PRECISION_MIN_PER_CELL)
    drawn: list[dict] = []
    for key in sorted(cells):
        count = alloc.get(key, 0)
        if count:
            drawn.extend(rng.sample(cells[key], count))

    drawn.sort(key=lambda c: (c["category"], _base_rule(c["rule"]), c["doc"],
                              c["start"], c["gid"]))
    cache: dict[str, list[int] | None] = {}
    cases, without_page = [], 0
    for index, candidate in enumerate(drawn, start=1):
        starts = _page_index(tei_dir, candidate["doc"], cache)
        page = page_of_offset(starts, candidate["start"]) if starts is not None else None
        without_page += int(page is None)
        cases.append(_precision_case(candidate, f"p{index:03d}", page))
    strata = [{"cell": list(key), "available": len(cells[key]), "drawn": alloc.get(key, 0)}
              for key in sorted(cells)]
    return cases, strata, without_page


# ---------------------------------------------------------------------------
# Recall sample
# ---------------------------------------------------------------------------

def _recall_cells(documents: list[dict]) -> dict[tuple[str, str], list[dict]]:
    """Documents grouped by (layout type, language); documents without pages drop out."""
    cells: dict[tuple[str, str], list[dict]] = {}
    for doc in documents:
        if (doc.get("page_count") or 0) <= 0:
            continue
        cells.setdefault((doc.get("type", ""), doc.get("lang", "")), []).append(doc)
    for items in cells.values():
        items.sort(key=lambda d: d["id"])
    return cells


def _draw_cell_pages(items: list[dict], count: int, rng: random.Random) -> list[tuple[str, int]]:
    """Distinct (doc, page) pairs: document weighted by page count, page uniform.

    A collision retries; once the retries are spent the remaining pages of the cell are
    enumerated and drawn uniformly, which keeps small cells from spinning.
    """
    weights = [doc["page_count"] for doc in items]
    seen: set[tuple[str, int]] = set()
    drawn: list[tuple[str, int]] = []
    attempts = 0
    while len(drawn) < count and attempts < 20 * count:
        attempts += 1
        doc = rng.choices(items, weights=weights, k=1)[0]
        pair = (doc["id"], rng.randint(1, doc["page_count"]))
        if pair not in seen:
            seen.add(pair)
            drawn.append(pair)
    if len(drawn) < count:
        rest = sorted({(doc["id"], page) for doc in items
                       for page in range(1, doc["page_count"] + 1)} - seen)
        drawn.extend(rng.sample(rest, min(count - len(drawn), len(rest))))
    return drawn


def draw_recall(documents: list[dict], total: int, seed: int) -> tuple[list[dict], list[dict]]:
    """Drawn pages plus the strata table of the (layout type, language) cells."""
    cells = _recall_cells(documents)
    pages_per_cell = {key: sum(doc["page_count"] for doc in items)
                      for key, items in cells.items()}
    alloc = allocate(pages_per_cell, total, RECALL_MIN_PER_CELL)

    rng = random.Random(seed)
    drawn: list[tuple[str, int, dict]] = []
    for key in sorted(cells):
        count = alloc.get(key, 0)
        if not count:
            continue
        by_id = {doc["id"]: doc for doc in cells[key]}
        for doc_id, page in _draw_cell_pages(cells[key], count, rng):
            drawn.append((doc_id, page, by_id[doc_id]))

    drawn.sort(key=lambda item: (item[2].get("type", ""), item[2].get("lang", ""),
                                 item[0], item[1]))
    cases = [{"case_id": f"r{index:03d}", "doc": doc_id, "page": page,
              "facsimile": facsimile_path(doc_id, page), "lang": doc.get("lang", ""),
              "layout_type": doc.get("type", ""), "mentions": None}
             for index, (doc_id, page, doc) in enumerate(drawn, start=1)]
    strata = [{"cell": list(key), "available_pages": pages_per_cell[key],
               "available_docs": len(cells[key]), "drawn": alloc.get(key, 0)}
              for key in sorted(cells)]
    return cases, strata


# ---------------------------------------------------------------------------
# Manifest and run
# ---------------------------------------------------------------------------

def _source_info(path: Path, **counters) -> dict:
    stat = path.stat()
    modified = datetime.fromtimestamp(stat.st_mtime, tz=UTC)
    return {"path": _repo_path(path), "modified": modified.isoformat(timespec="seconds"),
            "size_bytes": stat.st_size, **counters}


def _repo_path(path: Path) -> str:
    """Repo-relative posix path where possible, so the manifest diffs across machines."""
    try:
        return Path(path).resolve().relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return Path(path).as_posix()


def _write(out_dir: Path, name: str, payload) -> Path:
    path = out_dir / name
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8")
    return path


def run(*, scan_path: Path = SCAN_PATH, catalog_path: Path = CATALOG_PATH,
        out_dir: Path = EVAL_SAMPLE_DIR, seed: int = DEFAULT_SEED,
        precision_n: int = DEFAULT_PRECISION_N,
        recall_pages: int = DEFAULT_RECALL_PAGES,
        tei_dir: Path = TEI_FINAL_DIR) -> dict:
    """Draw both samples and write the three files; returns the manifest."""
    scan_path, catalog_path, out_dir = Path(scan_path), Path(catalog_path), Path(out_dir)
    scan = json.loads(scan_path.read_text(encoding="utf-8"))
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    candidates = scan.get("candidates", [])
    documents = catalog.get("documents", [])

    cases, precision_strata, without_page = draw_precision(candidates, precision_n,
                                                           seed, Path(tei_dir))
    pages, recall_strata = draw_recall(documents, recall_pages, seed)

    manifest = {
        "generator": GENERATOR,
        "seed": seed,
        "sources": {
            "scan": _source_info(scan_path, candidates=len(candidates),
                                 tier1=sum(1 for c in candidates if c.get("tier") == 1)),
            "catalog": _source_info(catalog_path, documents=len(documents),
                                    pages=sum(d.get("page_count") or 0 for d in documents)),
            "tei_dir": _repo_path(tei_dir),
        },
        "precision": {"requested": precision_n, "drawn": len(cases),
                      "minimum_per_cell": PRECISION_MIN_PER_CELL,
                      "without_page": without_page, "strata": precision_strata},
        "recall": {"requested": recall_pages, "drawn": len(pages),
                   "minimum_per_cell": RECALL_MIN_PER_CELL, "strata": recall_strata},
    }

    out_dir.mkdir(parents=True, exist_ok=True)
    _write(out_dir, "precision_cases.json", cases)
    _write(out_dir, "recall_pages.json", pages)
    _write(out_dir, "sample_manifest.json", manifest)
    return manifest


def _print_summary(manifest: dict, out_dir: Path) -> None:
    print(f"\n  Seed {manifest['seed']}  ->  {_repo_path(out_dir)}")
    precision = manifest["precision"]
    print(f"\n  Precision: {precision['drawn']}/{precision['requested']} cases, "
          f"{len(precision['strata'])} cells, {precision['without_page']} without page")
    for row in precision["strata"]:
        print(f"    {'/'.join(row['cell']):40} available {row['available']:5}  "
              f"drawn {row['drawn']:4}")
    recall = manifest["recall"]
    print(f"\n  Recall: {recall['drawn']}/{recall['requested']} pages, "
          f"{len(recall['strata'])} cells")
    for row in recall["strata"]:
        print(f"    {'/'.join(row['cell']):40} pages {row['available_pages']:5}  "
              f"docs {row['available_docs']:4}  drawn {row['drawn']:4}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Draw the precision and recall samples of the entity evaluation")
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--precision-n", type=int, default=DEFAULT_PRECISION_N)
    parser.add_argument("--recall-pages", type=int, default=DEFAULT_RECALL_PAGES)
    parser.add_argument("--scan", type=Path, default=SCAN_PATH)
    parser.add_argument("--catalog", type=Path, default=CATALOG_PATH)
    parser.add_argument("--out", type=Path, default=EVAL_SAMPLE_DIR)
    parser.add_argument("--tei-dir", type=Path, default=TEI_FINAL_DIR,
                        help="TEI source for the offset-to-page assignment")
    args = parser.parse_args(argv)

    for path in (args.scan, args.catalog):
        if not Path(path).exists():
            print(f"  FEHLER: missing input {path}", file=sys.stderr)
            return 1
    manifest = run(scan_path=args.scan, catalog_path=args.catalog, out_dir=args.out,
                   seed=args.seed, precision_n=args.precision_n,
                   recall_pages=args.recall_pages, tei_dir=args.tei_dir)
    _print_summary(manifest, Path(args.out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
