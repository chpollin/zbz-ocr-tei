"""Projiziert Leerseiten-Marker aus dem Manifest in die finale TEI (E63 Phase 2, Schritt 2).

Liest `output/tei_final/{doc}_manifest.json` und behandelt jede sichere Leerseite
(class=blank, review=false) in `output/tei_final/{doc}_final.xml` so:
  - `type="blank"` an das zugehoerige `<pb>` (Seite = sequenzielle pb-Position, 1-basiert,
    identisch zum Mirror-Splitter in generate_edition_data.py),
  - der Seiten-Body wird GELEERT: alle `<p>`/`<head>` der Seite werden entfernt, dadurch
    leer gewordene `<div>` eingeklappt; strukturelle (unbalancierte) `<div>`/`</div>`-Grenzen
    bleiben erhalten. Eine bestaetigte Leerseite traegt danach nur noch den Marker.

Sicher per Vorbedingung: `clean_chunk` wird nur fuer bestaetigte Leerseiten aufgerufen, daher
ist das bedingungslose Entfernen korrekt. `type="blank"` wird nur gesetzt, wenn noch keins da
ist (idempotent). Ein Residual-Check meldet unerwarteten Resttext (sollte 0 sein); eine
Konsistenzpruefung verlangt genug `<pb>` fuer die hoechste Leerseite. Vor dem Schreiben wird
je Datei ein Backup angelegt.

Aufruf:
    python -m scripts.tei.tei_blank_marker --dry-run        # nur Bericht, nichts schreiben
    python -m scripts.tei.tei_blank_marker                  # schreiben (mit Backup)
    python -m scripts.tei.tei_blank_marker --doc 20         # einzelnes Dokument
"""

import argparse
import json
import re
import shutil
from pathlib import Path

from scripts.tei.pb_split import BODY_INNER_RE, iter_page_spans

ROOT = Path(__file__).resolve().parent.parent.parent
FINAL_DIR = ROOT / "output" / "tei_final"
BACKUP_DIR = ROOT / "output" / "_backup_pre_blank_marker"

# Inhalts-Element einer Leerseite (p oder head); group(2) = Inhalt
_CONTENT_RE = re.compile(r"<(p|head)\b[^>]*>(.*?)</\1>", re.DOTALL)
# leerer <div> (nur Whitespace zwischen oeffnendem und schliessendem Tag)
_EMPTY_DIV_RE = re.compile(r"<div\b[^>]*>\s*</div>", re.DOTALL)


def _visible(inner):
    """Sichtbarer Text eines XML-Fragments (alle Tags entfernt)."""
    return re.sub(r"<[^>]+>", "", inner).strip()


def add_type_blank(pb_tag):
    """Fuegt type='blank' in ein <pb>-Tag ein. Gibt (neues_tag, geaendert) zurueck."""
    if "type=" in pb_tag:
        return pb_tag, False
    if pb_tag.endswith("/>"):
        return pb_tag[:-2].rstrip() + ' type="blank" />', True
    if pb_tag.endswith(">"):
        return pb_tag[:-1].rstrip() + ' type="blank">', True
    return pb_tag, False


def clean_chunk(chunk):
    """Leert eine bestaetigte Leerseite: entfernt allen <p>-Inhalt und dadurch leer
    gewordene <div>. Unbalancierte (strukturelle) <div>/</div>-Grenzen bleiben erhalten.

    Returns (neuer_chunk, removed_texts, residual_text).
    residual_text = sichtbarer Text, der nach dem Leeren uebrig bleibt (sollte "" sein;
    andernfalls steckt unerwarteter Inhalt in einem anderen Element -> Warnung).
    """
    removed = [v for v in (_visible(m.group(2)) for m in _CONTENT_RE.finditer(chunk)) if v]
    new = _CONTENT_RE.sub("", chunk)
    prev = None
    while prev != new:                       # leer gewordene <div> einklappen (auch geschachtelt)
        prev = new
        new = _EMPTY_DIV_RE.sub("", new)
    residual = _visible(new)
    return new, removed, residual


def blank_pages_from_manifest(manifest_path):
    """Sichere Leerseiten (class=blank, review=false) als sortierte int-Liste."""
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    pages = []
    for pg, info in data.get("pages", {}).items():
        if info.get("class") == "blank" and not info.get("review"):
            pages.append(int(pg))
    return data["doc_id"], sorted(pages)


def project_doc(doc_id, blank_pages, dry_run):
    """Projiziert Marker in ein Dokument. Gibt einen Report-Dict zurueck."""
    final_path = FINAL_DIR / f"{doc_id}_final.xml"
    report = {"doc_id": doc_id, "ok": False, "typed": [], "removed": {},
              "residual": {}, "error": None}

    if not final_path.exists():
        report["error"] = "final.xml fehlt"
        return report

    raw = final_path.read_text(encoding="utf-8")
    body_match = BODY_INNER_RE.search(raw)
    if not body_match:
        report["error"] = "kein <body>"
        return report

    body_inner = body_match.group(1)
    spans = iter_page_spans(body_inner)

    # Konsistenzpruefung: genug pb fuer die hoechste Leerseite?
    if blank_pages and max(blank_pages) > len(spans):
        report["error"] = (f"pb-Anzahl {len(spans)} < hoechste Leerseite "
                           f"{max(blank_pages)} (Pagination-Drift?)")
        return report

    blank_set = set(blank_pages)
    out = body_inner[: spans[0].pb_start] if spans else body_inner

    for span in spans:
        page = span.page
        pb_tag = span.pb_tag
        chunk = body_inner[span.content_start:span.content_end]

        if page in blank_set:
            pb_tag, typed = add_type_blank(pb_tag)
            if typed:
                report["typed"].append(page)
            chunk, removed, residual = clean_chunk(chunk)
            if removed:
                report["removed"][page] = removed
            if residual:
                report["residual"][page] = residual

        out += pb_tag + chunk

    new_raw = raw[: body_match.start(1)] + out + raw[body_match.end(1):]
    report["ok"] = True
    report["changed"] = new_raw != raw

    if not dry_run and report["changed"]:
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy2(final_path, BACKUP_DIR / f"{doc_id}_final.xml")
        final_path.write_text(new_raw, encoding="utf-8")

    return report


def main():
    ap = argparse.ArgumentParser(description="Leerseiten-Marker in finale TEI projizieren")
    ap.add_argument("--doc", help="nur dieses Dokument")
    ap.add_argument("--dry-run", action="store_true", help="nichts schreiben, nur Bericht")
    args = ap.parse_args()

    manifests = [p for p in sorted(FINAL_DIR.glob("*_manifest.json"))
                 if re.match(r"\d+_manifest$", p.stem)]
    if args.doc:
        manifests = [p for p in manifests if p.stem == f"{args.doc}_manifest"]
        if not manifests:
            print(f"[FEHLER] kein Manifest fuer {args.doc}")
            return

    total_typed = total_removed = 0
    residual_pages = []  # (doc, page, text) - unerwarteter Restinhalt
    errors = []
    changed_docs = 0

    for mp in manifests:
        doc_id, blank_pages = blank_pages_from_manifest(mp)
        if not blank_pages:
            continue
        r = project_doc(doc_id, blank_pages, args.dry_run)
        if r["error"]:
            errors.append((doc_id, r["error"]))
            print(f"  {doc_id:>5}  [FEHLER] {r['error']}")
            continue
        if r.get("changed"):
            changed_docs += 1
        total_typed += len(r["typed"])
        total_removed += sum(len(v) for v in r["removed"].values())
        for pg, text in r["residual"].items():
            residual_pages.append((doc_id, pg, text))
        resnote = f"  RESIDUAL {sorted(r['residual'])}" if r["residual"] else ""
        print(f"  {doc_id:>5}  type=blank: {len(r['typed'])}  <p> entfernt: "
              f"{sum(len(v) for v in r['removed'].values())}{resnote}")

    print("-" * 60)
    print(f"Dokumente geaendert:       {changed_docs}")
    print(f"pb mit type=blank:         {total_typed}")
    print(f"<p> entfernt (Leerung):    {total_removed}")
    print(f"Seiten mit RESIDUAL-Text:  {len(residual_pages)}  (sollte 0 sein)")
    if residual_pages:
        print("  -> " + "; ".join(f"{d} S.{p}={t!r}" for d, p, t in residual_pages))
    if errors:
        print(f"FEHLER in {len(errors)} Docs: {[e[0] for e in errors]}")
    if args.dry_run:
        print("(dry-run: nichts geschrieben)")
    else:
        print(f"Backups: {BACKUP_DIR}")


if __name__ == "__main__":
    main()
