"""Bestandskorrektur: loest fehlgerahmte <note place="foot">-Bloecke im
Lieferbestand output/tei_final auf (Defekt E82, Facsimile-Verdikte E85+).

Gesteuert durch output/audits/body_note_verdicts.json (Agenten-Verifikation aller
63 Body-als-Note-Kandidaten aus output/audits/body_note_audit.json). Match-Key ist
doc + page + len der <note place="foot">, wobei page = Scan-Seite aus dem facs des
Notes (bzw. dem vorangehenden <pb>) und len = Zeichenlaenge des normalisierten
Notentextes -- identisch zur Berechnung in scripts.eval.body_note_audit, daher
stabil unter der laengenneutralen Apostroph-Normalisierung.

Operationen je Verdikt:
  HAUPTTEXT      -> <note place="foot"> wird zu <p> an derselben Position; facs bleibt,
                    Fussnoten-Attribute (place, n, xml:id vom Muster fn{Seite}-{Nr},
                    W13 in tei_validator.py) fallen weg.
  BLOCKZITAT     -> <quote> falls das Schema data/schema/zbz_hersch.rng das an der
                    Position erlaubt (real per Validierung geprueft), sonst Fallback <p>
                    mit Report-Hinweis.
  ECHTE_FUSSNOTE -> unangetastet.

Rollentausch (--promote-footnotes): fuer Verdikte mit real_footnote_following=true
wird das dem demoteten Block unmittelbar FOLGENDE <p> geprueft; beginnt sein
sichtbarer Text mit einem Fussnotenmarker (Klammer+Zeichen+Klammer, *, Hochziffer,
Ziffer+Punkt), wird es zu <note place="foot">. Ohne Marker-Treffer keine Promotion,
nur Report (konservativ).

Aufruf (Dry-Run ist Default):
    python -m scripts.tei.tei_body_note_demote --dry-run
    python -m scripts.tei.tei_body_note_demote --dry-run --promote-footnotes
    python -m scripts.tei.tei_body_note_demote                 # realer Lauf (mit Backup)
    python -m scripts.tei.tei_body_note_demote --promote-footnotes
    python -m scripts.tei.tei_body_note_demote --doc 530

Der reale Lauf ist operator-gated; er legt je Datei ein Backup unter
output/_backup_pre_body_note_demote/ an und ist idempotent (zweiter Lauf 0 Aenderungen).
Keine LLM-/API-Aufrufe.
"""

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path

from scripts.config import OUTPUT_DIR, TEI_FINAL_DIR, TEI_SCHEMA_PATH
from scripts.tei.marker_common import backup_and_write

FINAL_DIR = TEI_FINAL_DIR
AUDIT_DIR = OUTPUT_DIR / "audits"
VERDICTS_PATH = AUDIT_DIR / "body_note_verdicts.json"
PREVIEW_PATH = AUDIT_DIR / "body_note_demote_preview.json"
BACKUP_DIR = OUTPUT_DIR / "_backup_pre_body_note_demote"
SCHEMA_PATH = TEI_SCHEMA_PATH

SNIPPET = 120

# footnote xml:id pattern (W13 in tei_validator.py): fn{page}[a-z]?-{n}
_FN_ID_RE = re.compile(r"^fn\d+[a-z]?-\d+$")
# leading footnote marker at a paragraph start (role-swap real footnote)
MARKER_RE = re.compile(
    r"^(?:\([0-9A-Za-z]\)|\*+|[¹²³⁰-⁹]+|\d{1,3}\.)"
)
# any <note ...>...</note> (foot notes do not nest); place filtered afterwards
_NOTE_RE = re.compile(r"<note\b([^>]*)>(.*?)</note>", re.DOTALL)
_PB_RE = re.compile(r"<pb\b[^>]*>")
_FACS_ATTR_RE = re.compile(r'facs\s*=\s*"([^"]*)"')
_PLACE_FOOT_RE = re.compile(r'place\s*=\s*"foot"')
_FOLLOWING_P_RE = re.compile(r"\s*<p\b([^>]*)>(.*?)</p>", re.DOTALL)
_TAG_RE = re.compile(r"<[^>]+>")


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def visible_text(fragment: str) -> str:
    """Concatenated text nodes of an XML fragment (all tags removed, whitespace folded).

    Equivalent to "".join(ET element.itertext()) followed by whitespace normalization,
    which is how scripts.eval.body_note_audit derives the note length.
    """
    return _norm(_TAG_RE.sub("", fragment or ""))


def facs_page(ref: str | None) -> int | None:
    m = re.match(r"facs_(\d+)", (ref or "").lstrip("#"))
    return int(m.group(1)) if m else None


def is_footnote_id(value: str) -> bool:
    return bool(_FN_ID_RE.match(value or ""))


def _ascii(s: str) -> str:
    return (s or "").encode("ascii", "replace").decode("ascii")


@dataclass(frozen=True)
class Block:
    """A matched element block in the raw text."""
    tag: str            # p | quote | note
    start: int
    end: int
    attrs: str          # raw attribute string incl. leading whitespace
    inner: str          # raw inner content (tags preserved)
    page: int | None
    length: int


def _pb_pages(raw: str):
    """List of (offset, facs_page) for every <pb> in document order."""
    out = []
    for m in _PB_RE.finditer(raw):
        fm = _FACS_ATTR_RE.search(m.group(0))
        out.append((m.start(), facs_page(fm.group(1) if fm else None)))
    return out


def _page_hint(pb_pages, pos: int) -> int | None:
    page = None
    for off, pg in pb_pages:
        if off < pos:
            page = pg
        else:
            break
    return page


def iter_foot_notes(raw: str) -> list[Block]:
    """Every <note place="foot"> block with its computed (page, length)."""
    pb_pages = _pb_pages(raw)
    blocks = []
    for m in _NOTE_RE.finditer(raw):
        attrs, inner = m.group(1), m.group(2)
        if not _PLACE_FOOT_RE.search(attrs):
            continue
        fm = _FACS_ATTR_RE.search(attrs)
        page = facs_page(fm.group(1)) if fm else None
        if page is None:
            page = _page_hint(pb_pages, m.start())
        blocks.append(Block("note", m.start(), m.end(), attrs, inner,
                            page, len(visible_text(inner))))
    return blocks


def _iter_blocks(raw: str, tag: str) -> list[Block]:
    """Every <tag>...</tag> block with computed (page, length). Non-nesting tags only."""
    pb_pages = _pb_pages(raw)
    rx = re.compile(r"<" + tag + r"\b([^>]*)>(.*?)</" + tag + r">", re.DOTALL)
    blocks = []
    for m in rx.finditer(raw):
        attrs, inner = m.group(1), m.group(2)
        fm = _FACS_ATTR_RE.search(attrs)
        page = facs_page(fm.group(1)) if fm else None
        if page is None:
            page = _page_hint(pb_pages, m.start())
        blocks.append(Block(tag, m.start(), m.end(), attrs, inner,
                            page, len(visible_text(inner))))
    return blocks


def clean_footnote_attrs(attrs: str) -> str:
    """Strip footnote-semantics attributes; keep facs and any positional attribute.

    Removes place, n, and an xml:id that matches the footnote id pattern (W13). The
    remaining attributes stay verbatim so byte layout is preserved.
    """
    a = re.sub(r'\s+place\s*=\s*"[^"]*"', "", attrs)
    a = re.sub(r'\s+n\s*=\s*"[^"]*"', "", a)

    def _drop_fn(m):
        return "" if is_footnote_id(m.group(1)) else m.group(0)

    a = re.sub(r'\s+xml:id\s*=\s*"([^"]*)"', _drop_fn, a)
    return a


def _ensure_place_foot(attrs: str) -> str:
    """Prepend place="foot" to a paragraph's attributes for promotion (idempotent)."""
    if _PLACE_FOOT_RE.search(attrs):
        return attrs
    return ' place="foot"' + attrs


def _apply_edits(raw: str, edits) -> str:
    """Apply non-overlapping (start, end, replacement) edits to raw."""
    edits = sorted(edits, key=lambda e: e[0])
    out = []
    cursor = 0
    for start, end, repl in edits:
        if start < cursor:
            raise ValueError("overlapping edits")
        out.append(raw[cursor:start])
        out.append(repl)
        cursor = end
    out.append(raw[cursor:])
    return "".join(out)


def _following_paragraph(raw: str, note_end: int):
    """The <p> immediately following a note (only whitespace between). Returns
    (start, end, attrs, inner) or None."""
    m = _FOLLOWING_P_RE.match(raw, note_end)
    if not m:
        return None
    # locate the actual <p ...> start (skip the leading whitespace the regex consumed)
    p_open = raw.index("<p", m.start())
    return p_open, m.end(), m.group(1), m.group(2)


def _already_applied(raw: str, page, length, verdict: str) -> bool:
    """Whether a p/quote block with this (page, length) already exists, meaning the
    demotion has run before (idempotency signal, not a fresh match)."""
    tags = ("quote", "p") if verdict == "BLOCKZITAT" else ("p",)
    for tag in tags:
        for b in _iter_blocks(raw, tag):
            if b.page == page and b.length == length:
                return True
    return False


def schema_validator():
    """Return a callable(raw_str) -> bool validating against zbz_hersch.rng, or None."""
    try:
        from lxml import etree
    except ImportError:
        return None
    if not SCHEMA_PATH.exists():
        return None
    rng = etree.RelaxNG(etree.parse(str(SCHEMA_PATH)))

    def _validate(raw_str: str) -> bool:
        try:
            doc = etree.fromstring(raw_str.encode("utf-8"))
        except etree.XMLSyntaxError:
            return False
        return bool(rng.validate(doc))

    return _validate


def _blockzitat_tag(raw: str, note: Block, validator) -> str:
    """Decide quote vs p for a BLOCKZITAT note by validating a candidate whole document.
    Without a validator, default to quote (verified allowed at div level in E-tests)."""
    if validator is None:
        return "quote"
    candidate = f'<quote{clean_footnote_attrs(note.attrs)}>{note.inner}</quote>'
    trial = raw[:note.start] + candidate + raw[note.end:]
    return "quote" if validator(trial) else "p"


def transform_document(raw: str, entries, promote: bool = False, validator=None):
    """Apply all verdict-driven edits to one document's raw text.

    Returns (new_raw, report) where report is a list of per-note dicts. Pure: writing
    is the caller's responsibility.
    """
    notes = iter_foot_notes(raw)
    by_key = {}
    for i, n in enumerate(notes):
        by_key.setdefault((n.page, n.length), []).append(i)

    edits = []
    report = []
    used = set()

    for e in entries:
        page, length, verdict = e["page"], e["len"], e["verdict"]
        rep = {"doc": e["doc"], "page": page, "len": length, "verdict": verdict}
        idxs = [j for j in by_key.get((page, length), []) if j not in used]

        if not idxs:
            if _already_applied(raw, page, length, verdict):
                rep["operation"] = "already_applied"
                rep["reason"] = "no foot note; matching p/quote present"
            else:
                rep["operation"] = "unmatched"
                rep["reason"] = "no foot note with this page/len"
            report.append(rep)
            continue
        if len(idxs) > 1:
            rep["operation"] = "unmatched"
            rep["reason"] = f"ambiguous: {len(idxs)} foot notes share page/len"
            report.append(rep)
            continue

        j = idxs[0]
        used.add(j)
        note = notes[j]
        before = raw[note.start:note.end][:SNIPPET]

        if verdict == "ECHTE_FUSSNOTE":
            rep["operation"] = "preserve"
            rep["before"] = before
            rep["after"] = before
            report.append(rep)
            continue

        if verdict == "BLOCKZITAT":
            tag = _blockzitat_tag(raw, note, validator)
            rep["operation"] = "demote_quote" if tag == "quote" else "quote_fallback_p"
            if tag == "p":
                rep["reason"] = "schema forbids quote at this position; fell back to p"
        else:  # HAUPTTEXT
            tag = "p"
            rep["operation"] = "demote_p"

        new_block = f"<{tag}{clean_footnote_attrs(note.attrs)}>{note.inner}</{tag}>"
        edits.append((note.start, note.end, new_block))
        rep["before"] = before
        rep["after"] = new_block[:SNIPPET]

        if promote and e.get("real_footnote_following"):
            follow = _following_paragraph(raw, note.end)
            if not follow:
                rep["promotion"] = {"matched": False,
                                    "reason": "no <p> immediately following"}
            else:
                p_start, p_end, p_attrs, p_inner = follow
                vis = visible_text(p_inner)
                if MARKER_RE.match(vis):
                    note_block = f'<note{_ensure_place_foot(p_attrs)}>{p_inner}</note>'
                    edits.append((p_start, p_end, note_block))
                    rep["promotion"] = {"matched": True, "para_start": vis[:SNIPPET],
                                        "before": raw[p_start:p_end][:SNIPPET],
                                        "after": note_block[:SNIPPET]}
                else:
                    rep["promotion"] = {"matched": False,
                                        "reason": "no leading footnote marker",
                                        "para_start": vis[:SNIPPET]}
        report.append(rep)

    return _apply_edits(raw, edits), report


def load_verdicts(path=VERDICTS_PATH):
    """Group verdict entries by doc id."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    by_doc = {}
    for e in data.get("entries", []):
        by_doc.setdefault(e["doc"], []).append(e)
    return by_doc


def process_document(doc_id, entries, promote, dry_run, validator):
    """Transform one document; write when not dry_run and something changed."""
    final_path = FINAL_DIR / f"{doc_id}_final.xml"
    result = {"doc": doc_id, "error": None, "changed": False, "notes": []}
    if not final_path.exists():
        result["error"] = "final.xml fehlt"
        return result

    raw = final_path.read_text(encoding="utf-8")
    new_raw, report = transform_document(raw, entries, promote=promote,
                                         validator=validator)
    result["notes"] = report
    result["changed"] = new_raw != raw

    if not dry_run and result["changed"]:
        backup_and_write(final_path, BACKUP_DIR, new_raw)

    return result


def _summarize(results):
    counts = {"demote_p": 0, "demote_quote": 0, "quote_fallback_p": 0,
              "preserve": 0, "unmatched": 0, "already_applied": 0}
    unmatched = []
    promotions = []
    for r in results:
        for n in r["notes"]:
            counts[n["operation"]] = counts.get(n["operation"], 0) + 1
            if n["operation"] == "unmatched":
                unmatched.append((n["doc"], n["page"], n["len"], n["reason"]))
            pr = n.get("promotion")
            if pr and pr.get("matched"):
                promotions.append((n["doc"], n["page"], pr["para_start"]))
    return counts, unmatched, promotions


def main():
    ap = argparse.ArgumentParser(
        description="Body-als-Note-Bestandskorrektur (Verdict-gesteuert)")
    ap.add_argument("--doc", help="nur dieses Dokument")
    ap.add_argument("--dry-run", action="store_true",
                    help="nichts schreiben, nur Bericht (Default-Empfehlung)")
    ap.add_argument("--promote-footnotes", action="store_true",
                    help="Rollentausch: dem demoteten Block folgendes Marker-<p> zu note wandeln")
    args = ap.parse_args()

    by_doc = load_verdicts()
    if args.doc:
        by_doc = {k: v for k, v in by_doc.items() if k == args.doc}
        if not by_doc:
            print(f"[FEHLER] kein Verdikt fuer {args.doc}")
            return

    validator = schema_validator()
    results = []
    for doc_id in sorted(by_doc, key=lambda d: int(d) if d.isdigit() else d):
        results.append(process_document(doc_id, by_doc[doc_id], args.promote_footnotes,
                                        args.dry_run, validator))

    counts, unmatched, promotions = _summarize(results)
    changed_docs = sum(1 for r in results if r["changed"])
    errors = [(r["doc"], r["error"]) for r in results if r["error"]]

    for r in results:
        if r["error"]:
            print(f"  {r['doc']:>5}  [FEHLER] {r['error']}")
            continue
        for n in r["notes"]:
            line = (f"  {r['doc']:>5}  S{n['page']!s:<4} len={n['len']:>4}  "
                    f"{n['verdict']:<14} -> {n['operation']}")
            if n.get("reason"):
                line += f"  ({n['reason']})"
            pr = n.get("promotion")
            if pr:
                if pr.get("matched"):
                    line += f"  [+note: {_ascii(pr['para_start'][:40])}]"
                else:
                    line += f"  [no-promo: {pr.get('reason', '')}]"
            print(line)

    print("-" * 66)
    print(f"Dokumente mit Aenderungen:   {changed_docs}")
    print(f"HAUPTTEXT -> p:              {counts['demote_p']}")
    print(f"BLOCKZITAT -> quote:         {counts['demote_quote']}")
    print(f"BLOCKZITAT -> p (Fallback):  {counts['quote_fallback_p']}")
    print(f"ECHTE_FUSSNOTE erhalten:     {counts['preserve']}")
    print(f"Promotions-Kandidaten:       {len(promotions)}")
    print(f"UNMATCHED:                   {counts['unmatched']}")
    print(f"already_applied:             {counts['already_applied']}")
    if unmatched:
        print("  UNMATCHED-Faelle:")
        for doc, pg, ln, reason in unmatched:
            print(f"    {doc} S{pg} len={ln}: {reason}")
    if promotions:
        print("  Promotions-Kandidaten (doc, seite, Absatzanfang):")
        for doc, pg, start in promotions:
            print(f"    {doc} S{pg}: {_ascii(start)}")
    if errors:
        print(f"FEHLER in {len(errors)} Docs: {[e[0] for e in errors]}")

    if args.dry_run:
        AUDIT_DIR.mkdir(parents=True, exist_ok=True)
        payload = {
            "tool": "body_note_demote",
            "mode": "dry-run",
            "promote_footnotes": args.promote_footnotes,
            "schema_checked": validator is not None,
            "counts": counts,
            "changed_docs": changed_docs,
            "unmatched": [{"doc": d, "page": p, "len": length, "reason": r}
                          for d, p, length, r in unmatched],
            "promotions": [{"doc": d, "page": p, "para_start": s}
                           for d, p, s in promotions],
            "documents": results,
        }
        PREVIEW_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2),
                                encoding="utf-8")
        print(f"(dry-run: nichts geschrieben)  Report: {PREVIEW_PATH}")
    else:
        print(f"Backups: {BACKUP_DIR}")


if __name__ == "__main__":
    main()
