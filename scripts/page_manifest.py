"""Pro-Objekt-Manifest (E63 Phase 2 + E66 Workflow-Status).

Erzeugt fuer jedes Objekt eine Datei `output/tei_final/{doc}_manifest.json`. Das Manifest
ist der **Pro-Objekt-Annotations-Slot** und tragt zwei Sektionen:

1. `streams` -- Workflow-Status + Provenienz-History je Datenstrom (OCR, Layout, TEI).
   Statuswerte: offen | in_arbeit | bearbeitet | fertig. Default: offen.
   `history` ist eine Liste von Eintraegen `{at, by, from, to, note}` und enthaelt die
   Provenienz der menschlichen Bearbeitungsschritte (Edit-Toggles, Status-Wechsel im
   Viewer). Eintraege werden NUR vom Skript hinzugefuegt, das die Aenderung anstoesst
   (Viewer oder explizites Skript); die Detektion hier ueberschreibt sie niemals.

2. `pages` -- Ausnahme-Seiten (Leerseiten und Grauzone). Aktuell befuellt der Detektor
   ausschliesslich die sichere Klasse `blank` (Vorsatz-, Rueck-, Durchschlagseiten).
   Die Grauzonen-Klassen `image_only` / `ocr_loop` bleiben dem manuellen Experten-
   Review vorbehalten (Auto-Erkennung erzeugt Fehlalarme).

Detektion-Signale pro Seite:
  - OCR-Text (Mistral): blank, wenn getrimmt <=5 Zeichen ODER kein alphanumerisches
    Zeichen [A-Za-zÀ-ÿ0-9] (identisch zu ZBZ.isBlankPageText im Viewer),
    ODER kurzer "Blank Page"-Marker.
  - Docling-Layout (Mirror): num_regions. 0 bestaetigt eine Leerseite.

Konfidenz: text-blank UND docling==0 -> review=false. Text-blank aber docling>0
(Widerspruch) -> review=true (Anomalie, nicht stillschweigend durchwinken).

Idempotenz: existierende Manifeste werden gelesen, die `streams.*.status` und
`streams.*.history` Felder bleiben erhalten. Nur die Detektor-Felder (Engine-
Deskriptoren, `pages`-Map, `generated`, `generator`) werden neu geschrieben.

Aufruf:
    python -m scripts.page_manifest                  # ganzes Korpus
    python -m scripts.page_manifest --doc 20         # ein Dokument
    python -m scripts.page_manifest --dry-run        # nichts schreiben, nur Bericht
"""

import argparse
import json
import re
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CATALOG = ROOT / "docs" / "data" / "catalog.json"
OCR_DIR = ROOT / "output" / "mistral_results"
MIRROR_PAGES = ROOT / "docs" / "data" / "pages"
OUT_DIR = ROOT / "output" / "tei_final"

GENERATOR = "page_manifest-v3"
# E67: `offen` umbenannt zu `unverifiziert` -- die Pipeline produziert OCR/Layout/TEI
# fuer alle 285 Docs deterministisch, der Default-Zustand ist also "Pipeline-Output
# existiert, kein Mensch hat verifiziert", nicht "nichts da". Rot bleibt reserviert
# fuer einen spaeteren expliziten Problem/Reject-Status.
VALID_STATUS = ("unverifiziert", "in_arbeit", "bearbeitet", "fertig")
DEFAULT_STATUS = "unverifiziert"
# Map alter Status-Werte (v2-Manifeste) auf die neuen.
STATUS_MIGRATION = {"offen": "unverifiziert"}

# Identisch zu ZBZ.isBlankPageText (docs/js/core.js)
_ALNUM = re.compile(r"[A-Za-zÀ-ÿ0-9]")
_MARKER_CLEAN = re.compile(r"[^a-z ]+")
_BLANK_MARKERS = {"blank page", "blank", "blank pages", "page blanche", "page vide"}


def is_blank_text(text):
    """True, wenn der OCR-Text eine Leerseite signalisiert. Gibt (blank, reason) zurueck."""
    if text is None:
        return False, ""
    s = text.strip()
    if len(s) <= 5:
        return True, "len<=5"
    if not _ALNUM.search(s):
        return True, "no-alnum"
    if len(s) < 40:
        cleaned = _MARKER_CLEAN.sub(" ", s.lower()).strip()
        cleaned = re.sub(r"\s+", " ", cleaned)
        if cleaned in _BLANK_MARKERS:
            return True, "blank-marker"
    return False, ""


def docling_regions(doc_id, page):
    """num_regions aus dem Docling-Layout des Mirrors; None, wenn nicht vorhanden."""
    fp = MIRROR_PAGES / doc_id / f"{doc_id}_p{page:03d}_layout.json"
    if not fp.exists():
        return None
    try:
        data = json.loads(fp.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    if "num_regions" in data:
        return data["num_regions"]
    regions = data.get("regions")
    return len(regions) if isinstance(regions, list) else None


def ocr_text(doc_id, page):
    fp = OCR_DIR / f"{doc_id}_p{page}.md"
    if not fp.exists():
        return None
    try:
        return fp.read_text(encoding="utf-8")
    except OSError:
        return None


def load_documents():
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    return catalog["documents"]


def detect_blanks(doc_id, page_count):
    """Detektor-Schritt: liefert die `pages`-Map (nur sichere blank-Faelle + Konflikte)."""
    pages = {}
    for page in range(1, page_count + 1):
        text = ocr_text(doc_id, page)
        blank, reason = is_blank_text(text)
        if not blank:
            continue
        regions = docling_regions(doc_id, page)
        conflict = regions is not None and regions > 0
        pages[str(page)] = {
            "class": "blank",
            "source": "auto",
            "review": bool(conflict),
            "evidence": {
                "ocr_len": len(text.strip()) if text else 0,
                "ocr_reason": reason,
                "docling_regions": regions,
            },
        }
    return pages


def _initial_streams():
    """Default-Streams-Block fuer ein frisches Manifest (alle Stroeme `offen`, leere History)."""
    return {
        "ocr": {
            "engine": "mistral",
            "status": DEFAULT_STATUS,
            "history": [],
        },
        "layout": {
            "engines": ["docling", "gemini"],
            "status": DEFAULT_STATUS,
            "history": [],
        },
        "tei": {
            "source": "final",
            "status": DEFAULT_STATUS,
            "history": [],
        },
    }


def _migrate_streams(existing):
    """Aktualisiert den `streams`-Block ohne Status/History zu zerstoeren.

    - v1-Manifeste tragen `streams` als flache Engine-Beschreibung
      ({"ocr": "mistral", "layout": [...], "tei": "final"}). Wir erweitern jeden
      Strom zu einem Objekt mit status+history.
    - v2-Manifeste tragen schon Status/History; wir refreshen nur die Engine-
      Deskriptoren und lassen status/history unangetastet.
    """
    fresh = _initial_streams()
    if not isinstance(existing, dict):
        return fresh

    for stream_name in ("ocr", "layout", "tei"):
        old = existing.get(stream_name)
        fresh_stream = fresh[stream_name]
        if isinstance(old, dict):
            status = old.get("status", DEFAULT_STATUS)
            # Alte Status-Werte (v2) auf neue mappen
            status = STATUS_MIGRATION.get(status, status)
            if status not in VALID_STATUS:
                status = DEFAULT_STATUS
            history = old.get("history") or []
            if not isinstance(history, list):
                history = []
            # Auch History-Eintraege migrieren (from/to-Felder)
            for entry in history:
                if isinstance(entry, dict):
                    if entry.get("from") in STATUS_MIGRATION:
                        entry["from"] = STATUS_MIGRATION[entry["from"]]
                    if entry.get("to") in STATUS_MIGRATION:
                        entry["to"] = STATUS_MIGRATION[entry["to"]]
            fresh_stream["status"] = status
            fresh_stream["history"] = history
        # alte v1-Form (Strom = String oder Liste): keine status/history -> Default
    return fresh


def build_manifest(doc, existing=None):
    """Erzeugt das Manifest-Dict fuer ein Dokument. Wird IMMER geschrieben (auch ohne Ausnahme-Seiten).

    Wenn `existing` uebergeben wird, bleiben dessen `streams.*.status` und
    `streams.*.history` erhalten -- die Detektion ueberschreibt nur die eigenen Felder.
    """
    doc_id = str(doc["id"])
    page_count = int(doc.get("page_count") or 0)

    pages = detect_blanks(doc_id, page_count)
    streams = _migrate_streams((existing or {}).get("streams"))

    return {
        "doc_id": doc_id,
        "page_count": page_count,
        "generated": date.today().isoformat(),
        "generator": GENERATOR,
        "streams": streams,
        "pages": pages,
    }


def _load_existing(doc_id):
    fp = OUT_DIR / f"{doc_id}_manifest.json"
    if not fp.exists():
        return None
    try:
        return json.loads(fp.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def main():
    ap = argparse.ArgumentParser(description="Pro-Objekt-Manifest (Workflow-Status + Leerseiten)")
    ap.add_argument("--doc", help="nur dieses Dokument (id)")
    ap.add_argument("--dry-run", action="store_true", help="nichts schreiben, nur Bericht")
    args = ap.parse_args()

    documents = load_documents()
    if args.doc:
        documents = [d for d in documents if str(d["id"]) == str(args.doc)]
        if not documents:
            print(f"[FEHLER] Dokument {args.doc} nicht im Katalog gefunden.")
            return

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    total_docs = 0
    docs_with_blanks = 0
    total_blanks = 0
    total_conflicts = 0
    written = 0
    preserved_history = 0

    for doc in documents:
        total_docs += 1
        existing = _load_existing(str(doc["id"]))
        manifest = build_manifest(doc, existing=existing)

        n_pages = len(manifest["pages"])
        n_conflict = sum(1 for p in manifest["pages"].values() if p["review"])

        # Wieviele History-Eintraege wurden erhalten?
        if existing:
            for s in ("ocr", "layout", "tei"):
                old_s = (existing.get("streams") or {}).get(s)
                if isinstance(old_s, dict):
                    preserved_history += len(old_s.get("history") or [])

        if n_pages:
            docs_with_blanks += 1
            total_blanks += n_pages
            total_conflicts += n_conflict
            flag = "  [KONFLIKT: Docling>0]" if n_conflict else ""
            sample = ",".join(sorted(manifest["pages"], key=int))
            print(f"  {manifest['doc_id']:>5}  blank-Seiten: {n_pages}  (S. {sample}){flag}")

        if not args.dry_run:
            out = OUT_DIR / f"{manifest['doc_id']}_manifest.json"
            out.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
            written += 1

    print("-" * 60)
    print(f"Dokumente geprueft:        {total_docs}")
    print(f"Dokumente mit Leerseiten:  {docs_with_blanks}")
    print(f"Leerseiten gesamt:         {total_blanks}")
    print(f"davon Konflikt (review):   {total_conflicts}")
    print(f"History-Eintraege bewahrt: {preserved_history}")
    if args.dry_run:
        print("(dry-run: nichts geschrieben)")
    else:
        print(f"Manifeste geschrieben:     {written} -> {OUT_DIR}")


if __name__ == "__main__":
    main()
