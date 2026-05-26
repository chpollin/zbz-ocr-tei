"""Projiziert Workflow-Status-History aus dem Manifest in den TEI-Header (E66).

Liest `output/tei_final/{doc}_manifest.json` und schreibt fuer jeden Strom
(`ocr`, `layout`, `tei`) die `history`-Eintraege als `<change>`-Elemente in den
`<revisionDesc>` von `output/tei_final/{doc}_final.xml`. Damit reist die
Bearbeitungs-Provenienz mit dem ausgelieferten Dokument.

Im selben Schritt werden die irrefuehrenden Agent-Screening-`<change>`-Eintraege
entfernt (z.B. `who="agent-screening-v2"`, `who="quality-screener-*"` etc.) -- diese
beanspruchen "APPROVED", obwohl kein Mensch das Dokument freigegeben hat.

Erhaltene Eintraege: alle `<change>`-Elemente, deren `who` weder mit "agent-screening",
"quality-screen", "quality-pass" noch mit "claude" beginnt. Der typische Pipeline-
Generierungs-Eintrag (`who="pipeline"`) bleibt also erhalten.

Aufruf:
    python -m scripts.tei.tei_status_marker --dry-run     # nur Bericht, nichts schreiben
    python -m scripts.tei.tei_status_marker               # schreiben (mit Backup)
    python -m scripts.tei.tei_status_marker --doc 20      # einzelnes Dokument
    python -m scripts.tei.tei_status_marker --keep-legacy # Agent-Screening-Eintraege NICHT entfernen
"""

import argparse
import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
FINAL_DIR = ROOT / "output" / "tei_final"
BACKUP_DIR = ROOT / "output" / "_backup_pre_status_marker"

STREAMS = ("ocr", "layout", "tei")
STATUS_LABEL = {
    "unverifiziert": "unverifiziert",
    "in_arbeit":     "in Arbeit",
    "bearbeitet":    "bearbeitet",
    "fertig":        "fertig",
}

# Pseudo-Reviewer aus E41-E44 (Agent-Screening): rausschmeissen, weil kein Mensch geprueft hat
LEGACY_WHO_RE = re.compile(r"^(agent-screening|quality-screen|quality-pass|claude)", re.IGNORECASE)

_REVISION_RE = re.compile(r"(<revisionDesc[^>]*>)(.*?)(</revisionDesc>)", re.DOTALL)
_CHANGE_RE = re.compile(r"<change\b([^>]*)>(.*?)</change>", re.DOTALL)
_WHO_RE = re.compile(r'who\s*=\s*"([^"]*)"')


def _xml_escape(s):
    if s is None:
        return ""
    return (str(s)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;"))


def parse_changes(revision_body):
    """Liste der `<change>`-Elemente als Roh-XML, in Original-Reihenfolge."""
    return [(m.group(0), m.group(1)) for m in _CHANGE_RE.finditer(revision_body)]


def is_legacy_change(attrs):
    m = _WHO_RE.search(attrs or "")
    if not m:
        return False
    return bool(LEGACY_WHO_RE.match(m.group(1)))


def build_change_for_history_entry(stream, entry):
    when = _xml_escape(entry.get("at") or "")
    who = _xml_escape(entry.get("by") or "anonym")
    frm = entry.get("from") or "unverifiziert"
    to = entry.get("to") or "unverifiziert"
    note = entry.get("note")
    txt = f"{stream.upper()}-Strom: {STATUS_LABEL.get(frm, frm)} → {STATUS_LABEL.get(to, to)}"
    if note:
        txt += f" ({_xml_escape(note)})"
    return (f'<change when="{when}" who="{who}" status="{_xml_escape(to)}" '
            f'n="{stream}">{txt}</change>')


def build_change_summary(stream, status, last_at, last_by):
    """Eine Summen-Zeile pro Strom mit aktuellem Status."""
    txt = f"{stream.upper()}-Strom (Stand): {STATUS_LABEL.get(status, status)}"
    if last_by:
        txt += f", zuletzt {_xml_escape(last_by)}"
    if last_at:
        txt += f" am {_xml_escape(last_at[:10])}"
    when_attr = f' when="{_xml_escape(last_at)}"' if last_at else ""
    who_attr = f' who="{_xml_escape(last_by)}"' if last_by else ""
    return (f'<change{when_attr}{who_attr} status="{_xml_escape(status)}" '
            f'n="{stream}-summary">{txt}</change>')


def project_doc(doc_id, manifest, dry_run, keep_legacy):
    final_path = FINAL_DIR / f"{doc_id}_final.xml"
    report = {
        "doc_id": doc_id,
        "ok": False,
        "removed_legacy": 0,
        "added_history": 0,
        "added_summary": 0,
        "error": None,
    }
    if not final_path.exists():
        report["error"] = "final.xml fehlt"
        return report

    raw = final_path.read_text(encoding="utf-8")
    rev_match = _REVISION_RE.search(raw)
    if not rev_match:
        report["error"] = "kein <revisionDesc>"
        return report

    open_tag, body, close_tag = rev_match.group(1), rev_match.group(2), rev_match.group(3)

    # Bestehende changes filtern (Legacy raus, Rest behalten)
    kept_raw = []
    for full, attrs in parse_changes(body):
        if not keep_legacy and is_legacy_change(attrs):
            report["removed_legacy"] += 1
            continue
        kept_raw.append(full)

    # Neue Eintraege aus der Manifest-History
    new_changes = []
    streams = manifest.get("streams") or {}
    for stream in STREAMS:
        s = streams.get(stream) or {}
        history = s.get("history") or []
        for entry in history:
            new_changes.append(build_change_for_history_entry(stream, entry))
            report["added_history"] += 1

    # Summen-Zeile je Strom (nur wenn Manifest existiert)
    for stream in STREAMS:
        s = streams.get(stream) or {}
        status = s.get("status") or "unverifiziert"
        history = s.get("history") or []
        last = history[-1] if history else {}
        new_changes.append(build_change_summary(
            stream, status, last.get("at"), last.get("by")))
        report["added_summary"] += 1

    # Neuen revisionDesc-Block bauen
    indent = "    "
    block_inner = "\n" + "\n".join(indent + c for c in (kept_raw + new_changes)) + "\n  "
    new_revision = open_tag + block_inner + close_tag
    new_raw = raw[:rev_match.start()] + new_revision + raw[rev_match.end():]

    report["ok"] = True
    report["changed"] = new_raw != raw

    if not dry_run and report["changed"]:
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy2(final_path, BACKUP_DIR / f"{doc_id}_final.xml")
        final_path.write_text(new_raw, encoding="utf-8")

    return report


def manifests_to_process(only_doc):
    out = []
    for mp in sorted(FINAL_DIR.glob("*_manifest.json")):
        # nur "{doc_id}_manifest.json" (nicht 'screening_manifest_legacy.json' etc.)
        if not re.match(r"^\d+_manifest$", mp.stem):
            continue
        if only_doc and mp.stem != f"{only_doc}_manifest":
            continue
        out.append(mp)
    return out


def main():
    ap = argparse.ArgumentParser(description="Workflow-Status in revisionDesc projizieren (E66)")
    ap.add_argument("--doc", help="nur dieses Dokument")
    ap.add_argument("--dry-run", action="store_true", help="nichts schreiben, nur Bericht")
    ap.add_argument("--keep-legacy", action="store_true",
                    help="Agent-Screening-Eintraege NICHT entfernen (default: entfernen)")
    args = ap.parse_args()

    manifests = manifests_to_process(args.doc)
    if not manifests:
        print(f"[FEHLER] keine Manifeste gefunden{' fuer ' + args.doc if args.doc else ''}")
        return

    total_removed = total_history = total_summary = 0
    changed_docs = 0
    errors = []

    for mp in manifests:
        manifest = json.loads(mp.read_text(encoding="utf-8"))
        doc_id = manifest.get("doc_id") or mp.stem.replace("_manifest", "")
        r = project_doc(doc_id, manifest, args.dry_run, args.keep_legacy)
        if r["error"]:
            errors.append((doc_id, r["error"]))
            print(f"  {doc_id:>5}  [FEHLER] {r['error']}")
            continue
        if r.get("changed"):
            changed_docs += 1
        total_removed += r["removed_legacy"]
        total_history += r["added_history"]
        total_summary += r["added_summary"]
        flag = ""
        if r["removed_legacy"]:
            flag += f"  -legacy:{r['removed_legacy']}"
        if r["added_history"]:
            flag += f"  +history:{r['added_history']}"
        print(f"  {doc_id:>5}  +summary:{r['added_summary']}{flag}")

    print("-" * 60)
    print(f"Dokumente geaendert:        {changed_docs}")
    print(f"Legacy-Screening entfernt:  {total_removed}")
    print(f"History-<change> ergaenzt:  {total_history}")
    print(f"Summary-<change> ergaenzt:  {total_summary}")
    if errors:
        print(f"FEHLER in {len(errors)} Docs: {[e[0] for e in errors]}")
    if args.dry_run:
        print("(dry-run: nichts geschrieben)")
    else:
        print(f"Backups: {BACKUP_DIR}")


if __name__ == "__main__":
    main()
