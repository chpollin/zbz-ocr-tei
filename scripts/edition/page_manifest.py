"""Pro-Objekt-Manifest (E63 Phase 2 + E66 Workflow-Status).

Erzeugt fuer jedes Objekt eine Datei `output/tei_final/{doc}_manifest.json`. Das Manifest
ist der **Pro-Objekt-Annotations-Slot** und tragt zwei Sektionen:

1. `streams` -- Workflow-Status + Provenienz-History je Datenstrom (OCR, Layout, TEI,
   dazu `entities`, sobald eine Entity-Preview existiert).
   Statuswerte: unverifiziert | in_arbeit | verifiziert. Default: unverifiziert.
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

Der Strom `entities` wird nur angelegt, wenn `output/entity_preview/{doc}_final.xml`
existiert; ein bereits vorhandener Strom bleibt in jedem Fall erhalten, damit ein
geloeschtes Preview keine Pruef-Provenienz vernichtet.

Aufruf:
    python -m scripts.edition.page_manifest                  # ganzes Korpus
    python -m scripts.edition.page_manifest --doc 20         # ein Dokument
    python -m scripts.edition.page_manifest --dry-run        # nichts schreiben, nur Bericht
"""

import argparse
import json
import re
from datetime import date
from pathlib import Path

# scripts/edition/page_manifest.py -> Projekt-Root sind drei Ebenen hoch (Reorg-Regression:
# zwei Ebenen zeigten auf scripts/, wodurch Katalog, OCR und Layout-Mirror ins Leere liefen).
ROOT = Path(__file__).resolve().parents[2]
CATALOG = ROOT / "docs" / "data" / "catalog.json"
OCR_DIR = ROOT / "output" / "mistral_results"
MIRROR_PAGES = ROOT / "docs" / "data" / "pages"
OUT_DIR = ROOT / "output" / "tei_final"
ENTITY_PREVIEW_DIR = ROOT / "output" / "entity_preview"

GENERATOR = "page_manifest-v5"
ENTITY_STREAM = "entities"
# Three-level workflow status (E67/E77). The pipeline produces OCR/layout/TEI for
# every doc deterministically, so the default state means "pipeline output exists,
# no human has verified" rather than "nothing there". Traffic light: unverifiziert
# (neutral/gray), in_arbeit (yellow), verifiziert (green); red stays reserved for a
# future explicit problem/reject status.
VALID_STATUS = ("unverifiziert", "in_arbeit", "verifiziert")
DEFAULT_STATUS = "unverifiziert"
# Map alter Status-Werte auf die neuen (idempotent ueber Re-Laeufe).
STATUS_MIGRATION = {"offen": "unverifiziert", "bearbeitet": "in_arbeit", "fertig": "verifiziert"}

# Identisch zu ZBZ.isBlankPageText (docs/assets/js/core.js)
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


def _entity_stream():
    """Default-Deskriptor des Annotations-Stroms (nur bei vorhandener Entity-Preview)."""
    return {
        "source": "entity_preview",
        "status": DEFAULT_STATUS,
        "history": [],
    }


def _carry_status(old, fresh_stream):
    """Uebernimmt Status und History eines bestehenden Stroms in den frischen Deskriptor.

    Alte v1-Form (Strom = String oder Liste) traegt weder Status noch History; der
    frische Deskriptor behaelt dann seine Defaults.
    """
    if not isinstance(old, dict):
        return
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


def _migrate_streams(existing, with_entities=False):
    """Aktualisiert den `streams`-Block ohne Status/History zu zerstoeren.

    - v1-Manifeste tragen `streams` als flache Engine-Beschreibung
      ({"ocr": "mistral", "layout": [...], "tei": "final"}). Wir erweitern jeden
      Strom zu einem Objekt mit status+history.
    - v2-Manifeste tragen schon Status/History; wir refreshen nur die Engine-
      Deskriptoren und lassen status/history unangetastet.
    - `entities` entsteht nur mit vorhandener Preview, bleibt aber erhalten, sobald
      er einmal existiert (sonst ginge die Pruef-Provenienz verloren).
    """
    existing = existing if isinstance(existing, dict) else {}
    fresh = _initial_streams()
    if with_entities or isinstance(existing.get(ENTITY_STREAM), dict):
        fresh[ENTITY_STREAM] = _entity_stream()

    for stream_name, fresh_stream in fresh.items():
        _carry_status(existing.get(stream_name), fresh_stream)
    return fresh


def build_manifest(doc, existing=None, has_entities=None):
    """Erzeugt das Manifest-Dict fuer ein Dokument. Wird IMMER geschrieben (auch ohne Ausnahme-Seiten).

    Wenn `existing` uebergeben wird, bleiben dessen `streams.*.status` und
    `streams.*.history` erhalten -- die Detektion ueberschreibt nur die eigenen Felder.
    `has_entities` ueberschreibt die Preview-Detektion (Testeinstieg).
    """
    doc_id = str(doc["id"])
    page_count = int(doc.get("page_count") or 0)

    pages = detect_blanks(doc_id, page_count)
    if has_entities is None:
        has_entities = (ENTITY_PREVIEW_DIR / f"{doc_id}_final.xml").exists()
    streams = _migrate_streams((existing or {}).get("streams"), with_entities=has_entities)

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
    docs_with_entities = 0
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

        if ENTITY_STREAM in manifest["streams"]:
            docs_with_entities += 1

        # Wieviele History-Eintraege wurden erhalten?
        if existing:
            for old_s in (existing.get("streams") or {}).values():
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
    print(f"Dokumente mit Entities:    {docs_with_entities}")
    print(f"davon Konflikt (review):   {total_conflicts}")
    print(f"History-Eintraege bewahrt: {preserved_history}")
    if args.dry_run:
        print("(dry-run: nichts geschrieben)")
    else:
        print(f"Manifeste geschrieben:     {written} -> {OUT_DIR}")


if __name__ == "__main__":
    main()
