"""Bestandskorrektur: gerader Apostroph U+0027 zwischen zwei Buchstaben -> U+2019.

Operator-freigegebene erste Bestandskorrektur (2026-07-07, Modus hybrid: nur die
sichere Klasse). Korrigiert exakt die Klasse `straight_apostrophe` aus
scripts/eval/char_lint_audit.py; deren Regex `_APOSTROPHE_RE` wird importiert und 1:1
uebernommen, damit Vorher/Nachher-Messung (char_lint_audit) und Korrektur deckungs-
gleich sind. KEINE anderen Klassen (keine Guillemets, keine Leerzeichen).

Geltungsbereich: nur Textknoten INNERHALB von `<text>...</text>` in
`output/tei_final/{doc}_final.xml`. teiHeader (steht vor `<text>`), facsimile
(steht vor `<text>`), Attribute und Kommentare bleiben unangetastet. Die Korrektur
laeuft byte-schonend ueber den Rohtext (keine XML-Neuserialisierung), analog zu den
Schwester-Tools tei_blank_marker.py / tei_status_marker.py: das `<text>`-Segment wird
in Tags/Kommentare (verbatim) und Textknoten (korrigiert) zerlegt, alles andere bleibt
Byte fuer Byte erhalten. Voraussetzung, dass Rohtext-Sicht und geparste Sicht
deckungsgleich sind: keine `&apos;`-Entities im Korpus (verifiziert 2026-07-07).

Kontrakt (Projektkonvention, vgl. tei_blank_marker.py):
  --dry-run   Report je Dokument (Anzahl Ersetzungen), nichts an den TEI-Daten schreiben.
  realer Lauf Backup jeder geaenderten Datei nach output/_backup_pre_char_normalize/,
              dann schreiben. Idempotent (zweiter Lauf: 0 Aenderungen).
  Immer       JSON-Report nach output/audits/char_normalize_run.json, ASCII-Konsole.

Aufruf:
    python -m scripts.tei.tei_char_normalize --dry-run    # nur Bericht, nichts schreiben
    python -m scripts.tei.tei_char_normalize              # schreiben (mit Backup)
    python -m scripts.tei.tei_char_normalize --doc 130    # einzelnes Dokument
"""

import argparse
import json
import re
import shutil
from pathlib import Path

from scripts.config import OUTPUT_DIR, TEI_FINAL_DIR
from scripts.eval.char_lint_audit import _APOSTROPHE_RE as APOSTROPHE_RE

BACKUP_DIR = OUTPUT_DIR / "_backup_pre_char_normalize"
REPORT_PATH = OUTPUT_DIR / "audits" / "char_normalize_run.json"

REPLACEMENT = "’"  # U+2019 RIGHT SINGLE QUOTATION MARK

# Tags and comments are copied verbatim; only the gaps between them are text nodes.
_TOKEN_RE = re.compile(r"<!--.*?-->|<[^>]*>", re.DOTALL)
_TEXT_OPEN_RE = re.compile(r"<text\b[^>]*>")


def normalize_text_region(region: str) -> tuple[str, int]:
    """Correct straight apostrophes in the text nodes of an XML fragment.

    Splits `region` into markup (tags + comments, preserved byte-for-byte) and the
    text between it, and applies APOSTROPHE_RE only to the text. Returns
    (new_region, replacement_count).
    """
    out = []
    count = 0
    pos = 0
    for m in _TOKEN_RE.finditer(region):
        seg, n = APOSTROPHE_RE.subn(REPLACEMENT, region[pos:m.start()])
        out.append(seg)
        count += n
        out.append(m.group(0))
        pos = m.end()
    seg, n = APOSTROPHE_RE.subn(REPLACEMENT, region[pos:])
    out.append(seg)
    count += n
    return "".join(out), count


def normalize_document(raw: str) -> tuple[str, int]:
    """Correct only within `<text>...</text>`; teiHeader and facsimile stay untouched.

    Returns (new_raw, count). Without a `<text>` element the document is returned
    unchanged. The document is spliced from three verbatim slices so everything outside
    the text region (including the `<text>` open tag and the `</text>` close tag) is
    byte-identical.
    """
    m = _TEXT_OPEN_RE.search(raw)
    if not m:
        return raw, 0
    end = raw.rfind("</text>")
    if end < m.end():
        return raw, 0
    new_region, count = normalize_text_region(raw[m.end():end])
    if count == 0:
        return raw, 0
    return raw[:m.end()] + new_region + raw[end:], count


def process_file(path: Path, backup_dir: Path, dry_run: bool) -> tuple[int, bool]:
    """Correct one final TEI file. Returns (count, changed).

    On a real run a changed file is first backed up to `backup_dir`, then overwritten.
    dry_run reports the count but writes nothing (no file, no backup).
    """
    raw = path.read_text(encoding="utf-8")
    new_raw, count = normalize_document(raw)
    changed = count > 0 and new_raw != raw
    if changed and not dry_run:
        backup_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, backup_dir / path.name)
        path.write_text(new_raw, encoding="utf-8")
    return count, changed


def _iter_files(doc: str | None):
    files = sorted(TEI_FINAL_DIR.glob("*_final.xml"))
    if doc:
        files = [f for f in files if f.stem == f"{doc}_final"]
    return files


def _write_report(records: list[dict], dry_run: bool) -> None:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "tool": "tei_char_normalize",
        "class": "straight_apostrophe",
        "replacement": "U+2019",
        "dry_run": dry_run,
        "tei_dir": str(TEI_FINAL_DIR),
        "backup_dir": str(BACKUP_DIR),
        "documents_changed": sum(1 for r in records if r["changed"]),
        "replacements_total": sum(r["count"] for r in records),
        "documents": [r for r in records if r["count"]],
    }
    REPORT_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Bestandskorrektur: gerader Apostroph zwischen Buchstaben -> U+2019"
    )
    ap.add_argument("--doc", help="nur dieses Dokument")
    ap.add_argument("--dry-run", action="store_true", help="nichts schreiben, nur Bericht")
    args = ap.parse_args()

    files = _iter_files(args.doc)
    if not files:
        target = args.doc or "tei_final"
        print(f"[FEHLER] keine finale TEI fuer {target}")
        return

    records = []
    total = changed_docs = 0
    for f in files:
        doc_id = f.stem.replace("_final", "")
        count, changed = process_file(f, BACKUP_DIR, args.dry_run)
        records.append({"doc_id": doc_id, "count": count, "changed": changed})
        total += count
        if changed:
            changed_docs += 1
            print(f"  {doc_id:>5}  Ersetzungen: {count}")

    _write_report(records, args.dry_run)

    print("-" * 60)
    print(f"Dokumente gesamt:          {len(files)}")
    print(f"Dokumente geaendert:       {changed_docs}")
    print(f"Ersetzungen gesamt:        {total}")
    print(f"JSON-Report:               {REPORT_PATH}")
    if args.dry_run:
        print("(dry-run: nichts an den TEI-Daten geschrieben)")
    else:
        print(f"Backups:                   {BACKUP_DIR}")


if __name__ == "__main__":
    main()
