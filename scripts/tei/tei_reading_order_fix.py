"""Lesereihenfolge-Instrument: kanonische Umordnung robuster W19-Seiten (M3-Falsifikation, E99).

KORPUS-LAUF EMPIRISCH WIDERLEGT (E99, 2026-07-07): Die CER-geschuetzte Probe ueber
alle 25 Referenzdokumente ergab 0 Verbesserungen und 9 Verschlechterungen (bis +40
Prozentpunkte Fidelity). Der ausgelieferte TEXT der W19-Seiten ist ueberwiegend
korrekt; korrupt ist die Zonen-ZUORDNUNG im Faksimile (Block traegt die Box eines
anderen Blocks), sodass die geometrisch "kanonische" Ordnung verifizierten Text
zerstoert. W19 ist damit ein Zonen-Verdachtssignal, kein Reorder-Auftrag.

Das Modul bleibt als Instrument: der Dry-Run (Default) erzeugt die triagierte
Worklist samt Report, und die CER-Probe auf Kopien ist der Beweisweg fuer jede
kuenftige Reorder-Idee. Ein Schreiblauf braucht das explizite --write und ist nur
fuer einzeln am Faksimile verifizierte Seiten (--doc) vertretbar.

Mechanik: ordnet Region-Bloecke einer Seite als Byte-Splice ganzer Block-Substrings
(alles ausserhalb bleibt Byte fuer Byte erhalten); nur robuste Seiten (classify_page
aus reading_order_audit) mit sauber abbildbarer Struktur (Geschwister-Bloecke, flach
oder genau ein umschliessendes <div>); Selbstpruefung auf Identitaetspermutation
nach dem Splice; idempotent; Backup nach output/_backup_pre_reading_order_fix/;
JSON-Report nach output/audits/reading_order_fix_run.json.

Aufruf:
    python -m scripts.tei.tei_reading_order_fix                 # Dry-Run (Default)
    python -m scripts.tei.tei_reading_order_fix --doc 330       # Dry-Run, ein Dokument
    python -m scripts.tei.tei_reading_order_fix --doc 330 --write   # realer Lauf (gated)
"""

import argparse
import json
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass

from scripts.config import OUTPUT_DIR
from scripts.core.pb_split import BODY_INNER_RE, iter_page_spans
from scripts.core.tei_xml_utils import build_zone_bbox, reading_order_permutation
from scripts.eval.reading_order_audit import classify_page
from scripts.tei.marker_common import backup_and_write, iter_final_files

BACKUP_DIR = OUTPUT_DIR / "_backup_pre_reading_order_fix"
REPORT_PATH = OUTPUT_DIR / "audits" / "reading_order_fix_run.json"

RFACS_RE = re.compile(r'facs="#(facs_\d+_r_\d+)"')
# tags that never open nesting depth in delivered TEI
VOID_TAGS = frozenset({"lb", "pb", "gap", "graphic", "milestone", "space", "pc", "cb", "anchor", "ptr"})
# containers the scope search may descend into (exactly one level)
DESCEND_TAGS = frozenset({"div"})
_TOKEN_RE = re.compile(r"<!--.*?-->|<[^>]+>", re.DOTALL)
_TAG_NAME_RE = re.compile(r"</?\s*([A-Za-z][\w.-]*)")


@dataclass(frozen=True)
class BlockUnit:
    """One depth-0 element of a scope string, with byte offsets into that scope."""
    tag: str
    ref: str | None        # own region ref from the opening tag, or None
    start: int
    end: int
    nested_refs: tuple     # region refs found strictly inside the unit


def scan_units(scope: str):
    """Depth-0 elements of `scope` in document order, or None if nesting breaks.

    Comments are opaque; VOID_TAGS and self-closing tags never open depth. The
    returned offsets delimit the verbatim substring of each unit including its
    closing tag, so callers can splice whole blocks byte-safely.
    """
    units = []
    depth = 0
    open_start = None
    open_tag = None
    for m in _TOKEN_RE.finditer(scope):
        tok = m.group(0)
        if tok.startswith("<!--"):
            continue
        name_m = _TAG_NAME_RE.match(tok)
        if not name_m:
            return None
        name = name_m.group(1)
        closing = tok.startswith("</")
        selfclosing = tok.endswith("/>") or name in VOID_TAGS
        if closing:
            if depth == 0:
                return None  # stray close: scope is not a clean sibling group
            depth -= 1
            if depth == 0:
                if name != open_tag:
                    return None
                units.append((open_tag, open_start, m.end()))
                open_start = open_tag = None
        elif selfclosing:
            if depth == 0:
                units.append((name, m.start(), m.end()))
        else:
            if depth == 0:
                open_start, open_tag = m.start(), name
            depth += 1
    if depth != 0:
        return None
    out = []
    for tag, start, end in units:
        body = scope[start:end]
        open_end = body.index(">") + 1
        own = RFACS_RE.search(body[:open_end])
        nested = tuple(r for r in RFACS_RE.findall(body[open_end:]))
        out.append(BlockUnit(tag=tag, ref=own.group(1) if own else None,
                             start=start, end=end, nested_refs=nested))
    return out


def locate_reorder_scope(chunk: str):
    """(scope_start, scope_end, units) of the sibling group holding the region blocks.

    Flat case: the chunk itself. Descent case: exactly one depth-0 DESCEND_TAGS
    container holds every region ref; descend one level into its inner content.
    None if the structure is not cleanly mappable.
    """
    units = scan_units(chunk)
    if units is None:
        return None
    if any(u.ref for u in units):
        return 0, len(chunk), units
    carriers = [u for u in units if u.nested_refs]
    if len(carriers) != 1 or carriers[0].tag not in DESCEND_TAGS:
        return None
    outer = carriers[0]
    body = chunk[outer.start:outer.end]
    open_end = outer.start + body.index(">") + 1
    close_start = outer.start + body.rindex("<")
    inner = chunk[open_end:close_start]
    inner_units = scan_units(inner)
    if inner_units is None or not any(u.ref for u in inner_units):
        return None
    shifted = [BlockUnit(u.tag, u.ref, u.start + open_end, u.end + open_end, u.nested_refs)
               for u in inner_units]
    return open_end, close_start, shifted


def plan_page(chunk: str, zone_bbox: dict):
    """('fix', scope_start, scope_end, units, region_idx, perm) or ('skip', reason)."""
    all_refs = RFACS_RE.findall(chunk)
    if len(all_refs) < 2:
        return ("skip", "under_two_regions")
    if any(r not in zone_bbox for r in all_refs):
        return ("skip", "unresolved_zone")
    label = classify_page([zone_bbox[r] for r in all_refs])
    if label is None:
        return ("skip", "already_canonical")
    if label == "fragil":
        return ("skip", "fragile")

    scope = locate_reorder_scope(chunk)
    if scope is None:
        return ("skip", "unmappable_structure")
    scope_start, scope_end, units = scope

    region_idx = [i for i, u in enumerate(units) if u.ref]
    region_units = [units[i] for i in region_idx]
    refs = [u.ref for u in region_units]
    if len(set(refs)) != len(refs):
        return ("skip", "dup_block_ref")
    for u in units:
        if u.ref and any(r != u.ref for r in u.nested_refs):
            return ("skip", "nested_foreign_region")
        if not u.ref and u.nested_refs:
            return ("skip", "region_below_scope")
    if set(refs) != set(all_refs):
        return ("skip", "ref_set_mismatch")
    if any(not units[i].ref for i in range(region_idx[0], region_idx[-1] + 1)):
        return ("skip", "interleaved_block")

    perm = reading_order_permutation([zone_bbox[r] for r in refs])
    if perm == list(range(len(refs))):
        return ("skip", "block_order_canonical")
    return ("fix", scope_start, scope_end, units, region_idx, perm)


def apply_plan(chunk: str, scope_start: int, scope_end: int, units, region_idx, perm) -> str:
    """Splice the region blocks into canonical order; separators keep their slots."""
    scope = chunk[scope_start:scope_end]
    first, last = units[region_idx[0]], units[region_idx[-1]]
    blocks = [scope[units[i].start:units[i].end] for i in region_idx]
    seps = [scope[units[region_idx[k]].end:units[region_idx[k + 1]].start]
            for k in range(len(region_idx) - 1)]
    run = "".join(
        blocks[perm[k]] + (seps[k] if k < len(seps) else "")
        for k in range(len(perm))
    )
    new_scope = scope[:first.start] + run + scope[last.end:]
    return chunk[:scope_start] + new_scope + chunk[scope_end:]


def verify_canonical(chunk: str, zone_bbox: dict) -> bool:
    """Audit view of the rewritten chunk: full ref list must be identity-ordered."""
    refs = RFACS_RE.findall(chunk)
    bboxes = [zone_bbox[r] for r in refs]
    return reading_order_permutation(bboxes) == list(range(len(bboxes)))


def process_doc(doc_id: str, path, dry_run: bool) -> dict:
    raw = path.read_text(encoding="utf-8")
    rec = {"doc_id": doc_id, "changed": False, "pages_fixed": [], "skips": {}, "error": None}
    try:
        zone_bbox = build_zone_bbox(ET.fromstring(raw))
    except ET.ParseError as exc:
        rec["error"] = str(exc)
        return rec
    body_m = BODY_INNER_RE.search(raw)
    if not body_m or not zone_bbox:
        return rec

    body_inner = body_m.group(1)
    spans = iter_page_spans(body_inner)
    if not spans:
        return rec

    pieces = [body_inner[:spans[0].pb_start]]
    for span in spans:
        chunk = body_inner[span.content_start:span.content_end]
        plan = plan_page(chunk, zone_bbox)
        if plan[0] == "fix":
            new_chunk = apply_plan(chunk, *plan[1:])
            if verify_canonical(new_chunk, zone_bbox):
                rec["pages_fixed"].append(str(span.page))
                chunk = new_chunk
            else:
                rec["skips"].setdefault("post_reorder_noncanonical", []).append(str(span.page))
        elif plan[1] == "unresolved_zone":
            # not part of the W19 universe: the audit/W19 never evaluate pages whose
            # refs lack zone coordinates, so they are counted but not worklisted
            rec["zones_unresolved"] = rec.get("zones_unresolved", 0) + 1
        elif plan[1] not in ("already_canonical", "under_two_regions"):
            rec["skips"].setdefault(plan[1], []).append(str(span.page))
        pieces.append(span.pb_tag + chunk)
    new_body = "".join(pieces)

    if new_body != body_inner:
        rec["changed"] = True
        new_raw = raw[:body_m.start(1)] + new_body + raw[body_m.end(1):]
        if not dry_run:
            backup_and_write(path, BACKUP_DIR, new_raw)
    return rec


def run(only_doc=None, dry_run=False) -> dict:
    records = []
    for doc_id, path in iter_final_files(only_doc):
        records.append(process_doc(doc_id, path, dry_run))

    skip_totals = {}
    for r in records:
        for reason, pages in r["skips"].items():
            skip_totals[reason] = skip_totals.get(reason, 0) + len(pages)
    summary = {
        "docs_changed": sum(1 for r in records if r["changed"]),
        "pages_fixed": sum(len(r["pages_fixed"]) for r in records),
        "skips": skip_totals,
        "zones_unresolved": sum(r.get("zones_unresolved", 0) for r in records),
        "errors": [r["doc_id"] for r in records if r["error"]],
    }

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "tool": "tei_reading_order_fix",
        "dry_run": dry_run,
        "backup_dir": str(BACKUP_DIR),
        "summary": summary,
        "documents": {
            r["doc_id"]: {k: r[k] for k in ("changed", "pages_fixed", "skips", "error")}
            for r in records
            if r["changed"] or r["pages_fixed"] or r["skips"] or r["error"]
        },
    }
    REPORT_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary


def main():
    ap = argparse.ArgumentParser(
        description="Lesereihenfolge-Instrument: W19-Worklist (Dry-Run-Default); "
                    "Korpus-Reorder empirisch widerlegt (E99)"
    )
    ap.add_argument("--doc", help="nur dieses Dokument")
    ap.add_argument("--write", action="store_true",
                    help="realer Schreiblauf (nur fuer am Faksimile verifizierte Seiten)")
    args = ap.parse_args()

    summary = run(only_doc=args.doc, dry_run=not args.write)

    print("-" * 60)
    print(f"Dokumente geaendert:       {summary['docs_changed']}")
    print(f"Seiten kanonisch gemacht:  {summary['pages_fixed']}")
    if summary["skips"]:
        print("Uebersprungen (Review-Worklist):")
        for reason in sorted(summary["skips"]):
            print(f"    {reason:28}: {summary['skips'][reason]}")
    if summary["zones_unresolved"]:
        print(f"Ohne Zonen (kein W19):     {summary['zones_unresolved']}")
    if summary["errors"]:
        print(f"Parse-Fehler:              {', '.join(summary['errors'])}")
    print(f"JSON-Report:               {REPORT_PATH}")
    if args.write:
        print(f"Backups:                   {BACKUP_DIR}")
    else:
        print("(dry-run: nichts an den TEI-Daten geschrieben; Korpus-Reorder ist "
              "empirisch widerlegt, siehe decisions.md E99)")


if __name__ == "__main__":
    main()
