"""Bestandskorrektur: entfernt E-Periodica-Deckblaetter aus dem Lieferbestand
output/tei_final (Operator-Entscheidung 2026-08-12, Bibliotheksapparat gehoert nicht in
die ausgelieferte TEI; siehe knowledge/entity-integration.md, Fix-Paket Punkt 5).

Erkennung (deterministisch, ohne LLM): ein Dokument traegt ein Deckblatt, wenn der
sichtbare Text zwischen dem ERSTEN und dem ZWEITEN <pb> mindestens drei der vier
E-Periodica-Feldzeilen "Zeitschrift:", "Herausgeber:", "Band:", "Heft:" enthaelt.
Teiltreffer (ein bis zwei Felder) werden NIE veraendert; sie erscheinen nur als
"partial" im Report, weil dort auch echte Titelseiten und fremde Lieferdeckblaetter
(Fernleihe, Kopienbestellung) liegen.

Wirkung: der Seiteninhalt der ersten Seite faellt weg, die Seitenmarke bleibt. Vom
Chunk ueberleben ausschliesslich unbalancierte <div>-Grenzen (ein </div>, das ein vor
dem ersten <pb> geoeffnetes div schliesst, bzw. ein <div>, das die Folgeseite
eroeffnet); balancierte Elemente und Text verschwinden vollstaendig. Das erste <pb>
erhaelt type="cover" (pb@type ist in data/schema/zbz_hersch.rng ein freies token,
tei_blank_marker setzt dort bereits type="blank").

Sicherheitsverweigerungen, jeweils Datei unangetastet:
  - Ein-Seiten-Dokument (nur ein <pb>): der Umfang der Loeschung waere das ganze Dokument.
  - Das erste <pb> traegt bereits einen fremden type (z. B. blank).
  - Der Chunk endet in einer unbalancierten Nicht-div-Grenze (ein ueber die Seiten-
    grenze laufender Absatz): die Loeschung waere Textverlust.
  - Das Ergebnis validiert nicht gegen data/schema/zbz_hersch.rng.

Kontrakt (E94-Muster, vgl. tei_char_normalize.py / tei_pb_folio.py):
  ohne --write  Report je Dokument, an den TEI-Daten wird nichts geschrieben.
  --write       Backup jeder geaenderten Datei nach output/_backup_pre_cover_strip/,
                dann schreiben; dazu ein datierter <change>-Eintrag im <revisionDesc>
                (Muster tei_status_marker, eigene n-Signatur, daher idempotent).
  immer         JSON-Report nach output/audits/cover_strip_report.json, ASCII-Konsole.

Aufruf:
    python -m scripts.tei.tei_cover_strip --dry-run          # Report, nichts schreiben
    python -m scripts.tei.tei_cover_strip --doc 570 --dry-run
    python -m scripts.tei.tei_cover_strip --write            # realer Lauf (operator-gated)
"""

import argparse
import json
import re
from datetime import date
from functools import lru_cache
from pathlib import Path

from scripts.config import OUTPUT_DIR, TEI_FINAL_DIR, TEI_SCHEMA_PATH
from scripts.tei.marker_common import backup_and_write
from scripts.tei.pb_split import BODY_INNER_RE, iter_page_spans

BACKUP_DIR = OUTPUT_DIR / "_backup_pre_cover_strip"
REPORT_PATH = OUTPUT_DIR / "audits" / "cover_strip_report.json"

# E-Periodica-Deckblatt: Feldzeilen des Kopfblocks. Drei Treffer genuegen, weil real
# je nach Zeitschrift eine Zeile fehlt (kein Heft bei Jahresbaenden, kein Herausgeber).
FIELD_LABELS = ("Zeitschrift:", "Herausgeber:", "Band:", "Heft:")
MIN_FIELDS = 3

PB_TYPE = "cover"
CHANGE_N = "cover-strip"
CHANGE_WHO = "cover-strip"
CHANGE_TEXT = ("E-Periodica-Deckblatt entfernt (Seite 1); "
               "Seitenmarke bleibt als pb type=cover erhalten.")

SNIPPET = 160

_TAG_RE = re.compile(r"<[^>]+>")
# Tags, Kommentare, PI und CDATA als einzelne Token (Kommentare koennen > enthalten)
_TOKEN_RE = re.compile(r"<!--.*?-->|<\?.*?\?>|<!\[CDATA\[.*?\]\]>|<[^>]*>", re.DOTALL)
_NAME_RE = re.compile(r"</?\s*([A-Za-z_][\w:.-]*)")
_TYPE_ATTR_RE = re.compile(r'\stype\s*=\s*"([^"]*)"')
_REVISION_RE = re.compile(r"(<revisionDesc[^>]*>)(.*?)(</revisionDesc>)", re.DOTALL)
_CHANGE_RE = re.compile(r"<change\b([^>]*)>.*?</change>", re.DOTALL)
_N_ATTR_RE = re.compile(r'\bn\s*=\s*"([^"]*)"')


# ---------------------------------------------------------------------------
# Erkennung
# ---------------------------------------------------------------------------

def visible_text(fragment: str) -> str:
    """Sichtbarer Text eines XML-Fragments (alle Tags entfernt, Whitespace gefaltet)."""
    return re.sub(r"\s+", " ", _TAG_RE.sub("", fragment or "")).strip()


def detect_fields(text: str) -> list:
    """Die enthaltenen E-Periodica-Feldzeilen, in FIELD_LABELS-Reihenfolge."""
    return [label for label in FIELD_LABELS if label in text]


def is_cover(fields) -> bool:
    """True, wenn die Feldtreffer die Deckblatt-Schwelle erreichen."""
    return len(fields) >= MIN_FIELDS


# ---------------------------------------------------------------------------
# Transformation der Seite
# ---------------------------------------------------------------------------

def strip_page_content(chunk: str):
    """Leert einen Seiten-Chunk bis auf seine unbalancierten Tag-Grenzen.

    Balancierte Elemente (inklusive eines eigenen Deckblatt-<div>), leere Elemente,
    Kommentare und Text fallen weg. Was uebrig bleibt, sind genau die Tags, deren
    Partner ausserhalb des Chunks steht; sie muessen erhalten bleiben, sonst wird das
    Dokument nicht wohlgeformt. Returns (neuer_chunk, uebrige_tags).
    """
    stack = []          # offene Tags: (name, position, tag)
    unbalanced = []     # (position, tag)
    for m in _TOKEN_RE.finditer(chunk):
        tok = m.group(0)
        if tok.startswith("<!") or tok.startswith("<?"):
            continue
        name_match = _NAME_RE.match(tok)
        if not name_match:
            continue
        name = name_match.group(1)
        if tok.startswith("</"):
            if stack and stack[-1][0] == name:
                stack.pop()
            else:
                unbalanced.append((m.start(), tok))
        elif not tok.endswith("/>"):
            stack.append((name, m.start(), tok))
    unbalanced.extend((pos, tok) for _, pos, tok in stack)
    kept = [tok for _, tok in sorted(unbalanced)]
    return "\n" + "".join(tok + "\n" for tok in kept), kept


def boundaries_are_safe(kept) -> bool:
    """True, wenn nur <div>-Grenzen uebrig bleiben.

    Eine unbalancierte Nicht-div-Grenze bedeutet, dass ein Inhaltselement ueber den
    Seitenumbruch laeuft; dann waere das Leeren der Seite Textverlust.
    """
    for tok in kept:
        name_match = _NAME_RE.match(tok)
        if not name_match or name_match.group(1) != "div":
            return False
    return True


def set_pb_type(pb_tag: str, value: str):
    """Setzt type="value" in ein <pb>-Tag. Returns (tag, geaendert, vorhandener_type)."""
    existing = _TYPE_ATTR_RE.search(pb_tag)
    if existing:
        return pb_tag, False, existing.group(1)
    if pb_tag.endswith("/>"):
        return pb_tag[:-2].rstrip() + f' type="{value}" />', True, None
    if pb_tag.endswith(">"):
        return pb_tag[:-1].rstrip() + f' type="{value}">', True, None
    return pb_tag, False, None


# ---------------------------------------------------------------------------
# revisionDesc
# ---------------------------------------------------------------------------

def add_run_change(raw: str, when: str):
    """Ergaenzt den datierten Lauf-Eintrag im <revisionDesc>. Returns (raw, ergaenzt).

    Ein frueherer Eintrag derselben n-Signatur wird ersetzt, nicht gestapelt; fremde
    <change>-Eintraege bleiben in Reihenfolge erhalten (Muster tei_status_marker).
    """
    match = _REVISION_RE.search(raw)
    if not match:
        return raw, False
    kept = [m.group(0) for m in _CHANGE_RE.finditer(match.group(2))
            if not _is_own_change(m.group(1))]
    entry = (f'<change when="{when}" who="{CHANGE_WHO}" n="{CHANGE_N}">'
             f"{CHANGE_TEXT}</change>")
    inner = "\n" + "\n".join("    " + c for c in [*kept, entry]) + "\n  "
    new_revision = match.group(1) + inner + match.group(3)
    return raw[:match.start()] + new_revision + raw[match.end():], True


def _is_own_change(attrs: str) -> bool:
    m = _N_ATTR_RE.search(attrs or "")
    return bool(m) and m.group(1) == CHANGE_N


# ---------------------------------------------------------------------------
# Dokument
# ---------------------------------------------------------------------------

def _report(doc_id=None):
    return {"doc_id": doc_id, "class": "none", "action": "none", "reason": None,
            "fields": [], "field_count": 0, "pages": 0, "changed": False,
            "removed_chars": 0, "removed_head": "", "removed_tail": "",
            "kept_boundaries": [], "change_entry": False, "error": None}


def transform_document(raw: str, when: str, doc_id=None):
    """Reine Transformation eines Dokuments. Returns (neues_raw, report).

    Schreibt nichts; jede Verweigerung gibt das Original unveraendert zurueck.
    """
    report = _report(doc_id)

    body_match = BODY_INNER_RE.search(raw)
    if not body_match:
        report["error"] = "kein <body>"
        return raw, report

    body_inner = body_match.group(1)
    spans = iter_page_spans(body_inner)
    if not spans:
        report["error"] = "kein <pb>"
        return raw, report

    report["pages"] = len(spans)
    first = spans[0]
    _, _, existing_type = set_pb_type(first.pb_tag, PB_TYPE)
    if existing_type == PB_TYPE:
        report["class"] = "already_stripped"
        return raw, report

    chunk = body_inner[first.content_start:first.content_end]
    text = visible_text(chunk)
    report["fields"] = detect_fields(text)
    report["field_count"] = len(report["fields"])

    if not is_cover(report["fields"]):
        report["class"] = "partial" if report["fields"] else "none"
        return raw, report

    report["class"] = "cover"
    report["removed_chars"] = len(text)
    report["removed_head"] = text[:SNIPPET]
    report["removed_tail"] = text[-SNIPPET:]

    if len(spans) < 2:
        report["action"] = "skip"
        report["reason"] = "single page document"
        return raw, report

    if existing_type is not None:
        report["action"] = "skip"
        report["reason"] = f"pb carries type={existing_type}"
        return raw, report

    new_chunk, kept = strip_page_content(chunk)
    report["kept_boundaries"] = kept
    if not boundaries_are_safe(kept):
        report["action"] = "skip"
        report["reason"] = "unsafe page boundary"
        return raw, report

    new_pb, _, _ = set_pb_type(first.pb_tag, PB_TYPE)
    new_body = (body_inner[:first.pb_start] + new_pb + new_chunk
                + body_inner[first.content_end:])
    new_raw = raw[:body_match.start(1)] + new_body + raw[body_match.end(1):]
    new_raw, report["change_entry"] = add_run_change(new_raw, when)

    report["action"] = "strip"
    report["changed"] = new_raw != raw
    return new_raw, report


# ---------------------------------------------------------------------------
# Schema-Gate
# ---------------------------------------------------------------------------

@lru_cache(maxsize=1)
def schema_validator(schema_path: Path = TEI_SCHEMA_PATH):
    """Callable(raw) -> Liste von RelaxNG-Fehlern (leer = valide), oder None.

    None bedeutet: kein lxml oder kein Schema vorhanden, das Gate entfaellt und der
    Report haelt rng_valid=None fest.
    """
    try:
        from lxml import etree
    except ImportError:
        return None
    if not Path(schema_path).exists():
        return None
    rng = etree.RelaxNG(etree.parse(str(schema_path)))

    def _validate(raw: str):
        try:
            doc = etree.fromstring(raw.encode("utf-8"))
        except etree.XMLSyntaxError as exc:
            return [f"XML syntax: {exc}"]
        if rng.validate(doc):
            return []
        return [f"line {err.line}: {err.message}" for err in rng.error_log][:5]

    return _validate


# ---------------------------------------------------------------------------
# Datei / Korpus
# ---------------------------------------------------------------------------

def process_file(path: Path, backup_dir: Path, write: bool, when: str, validator=None):
    """Verarbeitet eine Datei; schreibt nur bei write=True und valider Wirkung."""
    doc_id = path.name[: -len("_final.xml")] if path.name.endswith("_final.xml") else path.stem
    raw = path.read_text(encoding="utf-8")
    new_raw, report = transform_document(raw, when, doc_id)
    report["rng_valid"] = None
    report["rng_errors"] = []

    if not report["changed"]:
        return report

    validator = schema_validator() if validator is None else validator
    if validator is not None:
        errors = validator(new_raw)
        report["rng_valid"] = not errors
        report["rng_errors"] = errors
        if errors:
            report["action"] = "failed"
            report["reason"] = "RelaxNG invalid after strip"
            report["changed"] = False
            return report

    if write:
        backup_and_write(path, backup_dir, new_raw)
    return report


def run_corpus(final_dir: Path, backup_dir: Path, report_path: Path, write: bool,
               when: str, only_doc=None, validator=None):
    """Verarbeitet alle Dokumente, schreibt den JSON-Report und gibt ihn zurueck."""
    documents = {}
    buckets = {"candidates": [], "stripped": [], "partial": [], "skipped": [],
               "failed": [], "already_stripped": [], "errors": []}
    scanned = 0

    for path in sorted(Path(final_dir).glob("*_final.xml")):
        doc_id = path.name[: -len("_final.xml")]
        if only_doc and doc_id != only_doc:
            continue
        scanned += 1
        report = process_file(path, backup_dir, write, when, validator)
        if report["error"]:
            buckets["errors"].append(doc_id)
        elif report["class"] == "cover":
            buckets["candidates"].append(doc_id)
            if report["action"] == "strip":
                buckets["stripped"].append(doc_id)
            elif report["action"] == "failed":
                buckets["failed"].append(doc_id)
            else:
                buckets["skipped"].append(doc_id)
        elif report["class"] == "partial":
            buckets["partial"].append(doc_id)
        elif report["class"] == "already_stripped":
            buckets["already_stripped"].append(doc_id)
        if report["class"] != "none" or report["error"]:
            documents[doc_id] = report

    for key in buckets:
        buckets[key] = _sorted_ids(buckets[key])

    payload = {
        "tool": "cover_strip",
        "mode": "write" if write else "dry-run",
        "when": when,
        "field_labels": list(FIELD_LABELS),
        "min_fields": MIN_FIELDS,
        "corpus_totals": {"scanned": scanned,
                          **{k: len(v) for k, v in buckets.items()}},
        **buckets,
        "documents": {k: documents[k] for k in _sorted_ids(documents)},
    }
    report_path = Path(report_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2),
                           encoding="utf-8")
    return payload


def _sorted_ids(ids):
    return sorted(ids, key=lambda d: (0, int(d)) if str(d).isdigit() else (1, str(d)))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _print_summary(payload):
    docs = payload["documents"]
    for doc_id in payload["candidates"]:
        r = docs[doc_id]
        line = (f"  {doc_id:>5}  cover   fields={r['field_count']}/4  pages={r['pages']}"
                f"  chars={r['removed_chars']:>5}  -> {r['action']}")
        if r["reason"]:
            line += f"  ({r['reason']})"
        print(line)
    for doc_id in payload["partial"]:
        r = docs[doc_id]
        print(f"  {doc_id:>5}  partial fields={r['field_count']}/4  "
              f"[{', '.join(f.rstrip(':') for f in r['fields'])}]  -> untouched")
    for doc_id in payload["already_stripped"]:
        print(f"  {doc_id:>5}  already stripped (pb type={PB_TYPE})")
    for doc_id in payload["errors"]:
        print(f"  {doc_id:>5}  [FEHLER] {docs[doc_id]['error']}")

    totals = payload["corpus_totals"]
    print("-" * 66)
    print(f"Dokumente geprueft:        {totals['scanned']}")
    print(f"Deckblatt-Kandidaten:      {totals['candidates']}")
    print(f"davon gestrippt:           {totals['stripped']}")
    print(f"davon verweigert:          {totals['skipped']}")
    print(f"davon Schema-Fehler:       {totals['failed']}")
    print(f"Teiltreffer (unberuehrt):  {totals['partial']}")
    print(f"bereits gestrippt:         {totals['already_stripped']}")
    if totals["errors"]:
        print(f"FEHLER:                    {totals['errors']}")


def main():
    ap = argparse.ArgumentParser(
        description="E-Periodica-Deckblaetter aus tei_final entfernen (Bestandskorrektur)")
    ap.add_argument("--doc", help="nur dieses Dokument")
    ap.add_argument("--dry-run", action="store_true",
                    help="nichts schreiben, nur Report (Default ohne --write)")
    ap.add_argument("--write", action="store_true",
                    help="realer Lauf: schreibt mit Backup (operator-gated)")
    args = ap.parse_args()

    write = args.write and not args.dry_run
    payload = run_corpus(TEI_FINAL_DIR, BACKUP_DIR, REPORT_PATH, write,
                         date.today().isoformat(), only_doc=args.doc)
    _print_summary(payload)
    print(f"JSON-Report: {REPORT_PATH}")
    if write:
        print(f"Backups: {BACKUP_DIR}")
    else:
        print("(dry-run: nur Report geschrieben, tei_final unberuehrt)")


if __name__ == "__main__":
    main()
