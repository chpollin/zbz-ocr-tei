"""Entity previews as a read-only inspection layer in the generated viewer mirror.

Reads the pilot artifacts of ``scripts.entity.tei_entity_preview`` (``output/entity_preview/``,
read only) and projects them into ``docs/data/``:

- ``pages/{doc}/{doc}_entity_p{N}.xml``: the preview split per page with the same splitter
  the TEI mirror uses, so an entity page always sits next to the same facsimile as
  ``{doc}_p{N}.xml``.
- ``pages/{doc}/{doc}_entity_worklist.json``: the tier-2 worklist of the pilot report,
  grouped per page.
- ``entities.json``: gid -> label, category, life dates, lobid link. This is the lookup the
  viewer popover resolves ``ref="GND:..."`` against; ids come exclusively from the curated
  list ``data/entities/all_entities.json``.

Nothing under ``output/`` is written and ``output/tei_final`` is not even read. Design plan:
knowledge/entity-integration.md, section Instruments ("Viewer entity stream").

Page assignment. The candidate offsets of the report index the SOURCE document, the preview
carries the tier-1 wrappers on top of it. Both files hold the same ``<pb>`` elements in the
same order, so an offset is shifted by the wrapper lengths (computable from the report alone)
and then compared against the pb positions of the preview. Every mapped span is verified
against the preview text; a mismatch means report and preview file are out of sync, and the
entry is dropped with a visible count instead of being parked on a wrong page.

Deterministic and idempotent: same inputs, byte-identical outputs, no timestamps.

Usage:
    python -m scripts.entity.generate_entity_preview_data
    python -m scripts.entity.generate_entity_preview_data --docs 100,1060
"""

from __future__ import annotations

import argparse
import html
import json
import re
from bisect import bisect_left, bisect_right
from pathlib import Path

from scripts.config import DATA_DIR, DOCS_DIR

# Same splitter as the per-page TEI mirror: page number = sequential <pb> position. A second,
# diverging implementation would place entity pages next to the wrong facsimile.
from scripts.core.pb_split import (
    extract_pages_from_final as split_pages,
    page_of,
    pb_offsets,
)
from scripts.entity.entity_matcher import build_lexicon
from scripts.entity.tei_entity_preview import (
    CATEGORY_ELEMENT,
    ENTITY_PREVIEW_DIR,
    REPORT_STEM,
    opening_tag,
)

PAGES_DIR = DOCS_DIR / "data" / "pages"
ENTITIES_JSON_PATH = DOCS_DIR / "data" / "entities.json"
ENTITIES_PATH = DATA_DIR / "entities" / "all_entities.json"
GND_CACHE_PATH = DATA_DIR / "entities" / "gnd_cache.json"
VARIANT_REVIEW_PATH = DATA_DIR / "entities" / "variant_review.json"

LOBID_URL = "https://lobid.org/gnd/{gid}"
# Provenance label written into every worklist JSON of the git-tracked mirror.
GENERATOR = "scripts/entity/generate_entity_preview_data.py"
# Fields copied from the pilot report; offsets and tier stay there. Each entry additionally
# carries "text" (the surface as the renderer shows it) and "occurrence".
WORKLIST_FIELDS = ("gid", "category", "surface", "rule", "alternatives", "matched_form",
                   "form_source", "context")
# Carried only where the matcher reports it (one-word work titles).
OPTIONAL_WORKLIST_FIELDS = ("evidence",)

_TAG_RE = re.compile(r"<[^>]*>")


# ---------------------------------------------------------------------------
# Offsets: source document -> preview file -> page
# ---------------------------------------------------------------------------


def wrapper_shifts(wrapped: list[dict]) -> tuple[list[int], list[int]]:
    """Insertion positions of the tier-1 wrappers plus their cumulative lengths.

    The opening tag is rebuilt by the preview runner's own builder, because it carries
    per-mark provenance attributes whose length a second implementation would get wrong.
    """
    events: list[tuple[int, int]] = []
    for cand in wrapped:
        element = CATEGORY_ELEMENT.get(cand.get("category"))
        if element is None:
            continue
        events.append((cand["start"], len(opening_tag(cand))))
        events.append((cand["end"], len(f"</{element}>")))
    events.sort()
    positions: list[int] = []
    cumulative: list[int] = []
    total = 0
    for position, length in events:
        total += length
        positions.append(position)
        cumulative.append(total)
    return positions, cumulative


def shifted(positions: list[int], cumulative: list[int], offset: int, *, inclusive: bool) -> int:
    """Map a source offset into the preview string.

    ``inclusive`` counts insertions sitting exactly at the offset, which is what a span start
    needs (its first character comes after the inserted tag). A span end is exclusive: an
    insertion at that offset belongs behind the last character of the span.
    """
    index = bisect_right(positions, offset) if inclusive else bisect_left(positions, offset)
    return offset + (cumulative[index - 1] if index else 0)


def plain_text(fragment: str) -> str:
    """Text of an XML fragment as the viewer renders it: markup gone, entities decoded.

    Mirrors ZBZ.TeiRender, which drops every tag (an ``lb`` becomes a ``br`` element and
    contributes no character) and shows decoded text. The viewer walks exactly this string
    to find the n-th occurrence, so both sides must strip identically. Line ends are
    normalized because the XML parser does it too: the delivered files carry CRLF, the DOM
    only ever shows LF.
    """
    stripped = _TAG_RE.sub("", fragment).replace("\r\n", "\n").replace("\r", "\n")
    return html.unescape(stripped)


def nth_occurrence(haystack: str, needle: str, n: int) -> int:
    """Start index of the n-th non-overlapping occurrence, -1 when there are fewer.

    Non-overlapping is the convention shared with the viewer walker; overlapping counting
    would put the marker on a different instance of a repeated surface.
    """
    if not needle or n < 1:
        return -1
    index = -1
    start = 0
    for _ in range(n):
        index = haystack.find(needle, start)
        if index < 0:
            return -1
        start = index + len(needle)
    return index


def occurrence_in_page(preview_xml: str, page_start: int, start: int, text: str) -> int | None:
    """Which occurrence of ``text`` in the page's plain text the entry sits on (1-based).

    None when the entry cannot be located: content before the first ``<pb>`` is in no page
    file, and a counting mismatch (repeated substrings) must not place the marker on the
    wrong instance.
    """
    if not text or start < page_start:
        return None
    prefix = plain_text(preview_xml[page_start:start])
    occurrence = prefix.count(text) + 1
    if nth_occurrence(prefix + text, text, occurrence) != len(prefix):
        return None
    return occurrence


def worklist_pages(doc_result: dict, preview_xml: str) -> tuple[dict[str, list[dict]], int]:
    """Group the tier-2 worklist per page; the second value counts dropped stale entries."""
    positions, cumulative = wrapper_shifts(doc_result.get("wrapped") or [])
    # The respStmt declarations sit in the header, in front of the body, so they move
    # every body offset by a constant the preview runner records per document.
    header_shift = doc_result.get("header_shift") or 0
    pb_starts = pb_offsets(preview_xml)
    pages: dict[int, list[dict]] = {}
    stale = 0
    for cand in doc_result.get("worklist") or []:
        start = header_shift + shifted(positions, cumulative, cand["start"], inclusive=True)
        end = header_shift + shifted(positions, cumulative, cand["end"], inclusive=False)
        if preview_xml[start:end] != cand.get("surface"):
            stale += 1
            continue
        page = page_of(pb_starts, start)
        page_start = pb_starts[page - 1] if pb_starts else 0
        entry = {field: cand.get(field) for field in WORKLIST_FIELDS}
        entry.update({f: cand[f] for f in OPTIONAL_WORKLIST_FIELDS if f in cand})
        entry["text"] = plain_text(cand.get("surface") or "")
        entry["occurrence"] = occurrence_in_page(preview_xml, page_start, start, entry["text"])
        pages.setdefault(page, []).append(entry)
    return {str(page): entries for page, entries in sorted(pages.items())}, stale


# ---------------------------------------------------------------------------
# Mirror writing
# ---------------------------------------------------------------------------


def write_doc(doc_id: str, preview_path: Path, doc_result: dict, pages_dir: Path) -> dict:
    """Write the per-page entity XML plus the page-grouped worklist of one document."""
    # bytes in, like the preview runner: text mode would collapse the CRLF of the delivered
    # files and shift every offset the report carries.
    preview_xml = preview_path.read_bytes().decode("utf-8")
    pages = split_pages(preview_path)
    doc_dir = pages_dir / doc_id
    doc_dir.mkdir(parents=True, exist_ok=True)

    for page_number, page_xml in sorted(pages.items()):
        (doc_dir / f"{doc_id}_entity_p{page_number}.xml").write_text(page_xml, encoding="utf-8")

    worklist, stale = worklist_pages(doc_result, preview_xml)
    payload = {"doc": doc_id, "generator": GENERATOR, "pages": worklist}
    (doc_dir / f"{doc_id}_entity_worklist.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    entries = [entry for page_entries in worklist.values() for entry in page_entries]
    return {
        "pages": len(pages),
        "worklist": len(entries),
        "stale": stale,
        # entries the viewer cannot mark inline; they stay visible as a list
        "unplaced": sum(1 for entry in entries if entry["occurrence"] is None),
    }


def life_dates(record: dict) -> str | None:
    """Life dates as years, as far as the GND cache carries them."""
    birth = (record.get("date_of_birth") or "")[:4]
    death = (record.get("date_of_death") or "")[:4]
    if not birth and not death:
        return None
    return f"{birth}-{death}"


def build_entities_index(entities_path: Path, cache_path: Path) -> dict:
    """gid -> label, category, life dates, lobid link.

    Built on the matcher lexicon, so the viewer resolves exactly the ids the matcher can
    produce: same label normalization, same drop of ids the GND answers with 404.
    """
    review = VARIANT_REVIEW_PATH if VARIANT_REVIEW_PATH.exists() else None
    lexicon = build_lexicon(entities_path, cache_path, review_path=review)
    cache = json.loads(cache_path.read_text(encoding="utf-8")) if cache_path.exists() else {}
    cached = cache.get("entries", {}) if isinstance(cache, dict) else {}
    index = {}
    for gid, entry in sorted(lexicon["entries"].items()):
        # The cache is keyed by the full id; the check-character-free form is the fallback
        # the matcher uses as well.
        record = cached.get(gid) or cached.get(gid.split("-", 1)[0]) or {}
        index[gid] = {
            "label": entry["label"],
            "category": entry["category"],
            "dates": life_dates(record),
            "lobid": LOBID_URL.format(gid=gid),
        }
    return index


def run(
    preview_dir: Path,
    pages_dir: Path,
    entities_json_path: Path,
    entities_path: Path,
    cache_path: Path,
    doc_ids: list[str] | None = None,
) -> dict:
    """Project every reported preview into the mirror and write the entity lookup."""
    report_path = preview_dir / f"{REPORT_STEM}.json"
    if not report_path.exists():
        raise FileNotFoundError(
            f"pilot report not found: {report_path} "
            "(run python -m scripts.entity.tei_entity_preview --panel first)"
        )
    report = json.loads(report_path.read_text(encoding="utf-8"))
    wanted = set(doc_ids) if doc_ids else None

    stats = {"docs": [], "pages": 0, "worklist": 0, "stale": 0, "unplaced": 0,
             "skipped": [], "entities": 0}
    for doc_result in report.get("documents") or []:
        doc_id = str(doc_result.get("doc") or "").strip()
        if not doc_id or (wanted and doc_id not in wanted):
            continue
        preview_path = preview_dir / f"{doc_id}_final.xml"
        if not preview_path.exists():
            print(f"  SKIP {doc_id}: no preview file")
            stats["skipped"].append(doc_id)
            continue
        result = write_doc(doc_id, preview_path, doc_result, pages_dir)
        stats["docs"].append(doc_id)
        stats["pages"] += result["pages"]
        stats["worklist"] += result["worklist"]
        stats["stale"] += result["stale"]
        stats["unplaced"] += result["unplaced"]
        note = f", {result['stale']} stale (offset mismatch)" if result["stale"] else ""
        if result["unplaced"]:
            note += f", {result['unplaced']} not locatable inline"
        print(f"  {doc_id}: {result['pages']} pages, {result['worklist']} worklist entries{note}")

    index = build_entities_index(entities_path, cache_path)
    entities_json_path.parent.mkdir(parents=True, exist_ok=True)
    entities_json_path.write_text(
        json.dumps(index, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    stats["entities"] = len(index)
    return stats


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Entity previews into the viewer mirror (docs/data, read-only layer)"
    )
    parser.add_argument("--docs", nargs="+", help="Document ids, e.g. --docs 100,1060")
    parser.add_argument("--preview-dir", type=Path, default=ENTITY_PREVIEW_DIR,
                        help="Preview directory (read only)")
    parser.add_argument("--pages-dir", type=Path, default=PAGES_DIR,
                        help="Per-page mirror directory")
    parser.add_argument("--entities-json", type=Path, default=ENTITIES_JSON_PATH,
                        help="Target path of the entity lookup")
    args = parser.parse_args()

    doc_ids = [d for value in (args.docs or []) for d in value.split(",") if d.strip()]

    print("Entity preview mirror -> docs/data/ ...")
    stats = run(args.preview_dir, args.pages_dir, args.entities_json,
                ENTITIES_PATH, GND_CACHE_PATH, doc_ids or None)
    print(f"\n  Documents: {len(stats['docs'])}  pages: {stats['pages']}  "
          f"worklist entries: {stats['worklist']}  (not locatable inline: {stats['unplaced']})")
    if stats["stale"]:
        print(f"  WARNUNG: {stats['stale']} worklist entries dropped (offsets do not match "
              "the preview; rerun scripts.entity.tei_entity_preview)")
    if stats["skipped"]:
        print(f"  SKIP: {', '.join(stats['skipped'])}")
    print(f"  Entity lookup: {stats['entities']} ids -> {args.entities_json}")


if __name__ == "__main__":
    main()
