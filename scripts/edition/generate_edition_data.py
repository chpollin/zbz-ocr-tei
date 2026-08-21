"""
Generiert Edition-Daten fuer den statischen Viewer (docs/):

- catalog.json          : Korpus-Uebersicht mit Metadaten, Stream-Status (E66) und
                          `assets` (welche Mirror-Dateien es pro Dokument gibt; der Viewer
                          fragt nur Gelistetes an statt auf Verdacht)
- entity_index.json     : Entity-Index fuer NER-Highlighting im TEI-Render
- manifests/{doc}.json  : Spiegel der Pro-Objekt-Manifeste (Status + History + Leerseiten)
- pages/{doc}/...       : Per-Seiten-Mirror (Layout, Mistral-OCR, TEI extrahiert aus _final.xml)
                          inkl. {doc}_facs.json (Textseite -> Scanbild aus pb@facs)
- thumbs/{doc}.jpg      : Thumbnail der ersten Seite (140x200 JPEG)

Damit funktioniert der Viewer ohne lokalen Server fuer alle 285 Docs (GitHub Pages tauglich).

Usage:
    python -m scripts.edition.generate_edition_data                  # voller Lauf inkl. Mirror + Thumbs
    python -m scripts.edition.generate_edition_data --no-mirror      # nur Katalog + Entity-Index
    python -m scripts.edition.generate_edition_data --mirror-only    # nur Mirror + Thumbs
    python -m scripts.edition.generate_edition_data --doc 1350       # nur dieses Dokument spiegeln
    python -m scripts.edition.generate_edition_data --facs-audit     # read-only pb->facs-Befund
"""

import argparse
import json
import re
import shutil
from datetime import datetime
from itertools import pairwise
from pathlib import Path

from scripts.config import (
    DOC_METADATA_PATH,
    DOCS_DIR,
    LAYOUT_DIR,
    MISTRAL_RESULTS_DIR,
    OUTPUT_DIR,
    TEI_CURATED_DIR,
    TEI_FINAL_DIR,
)
from scripts.tei.pb_split import BODY_INNER_RE, iter_page_spans
from scripts.utils import load_json

MISTRAL_DIR = MISTRAL_RESULTS_DIR
PAGES_DIR = DOCS_DIR / "data" / "pages"
THUMBS_DIR = DOCS_DIR / "data" / "thumbs"
MANIFESTS_DIR = DOCS_DIR / "data" / "manifests"
IMAGES_DIR = DOCS_DIR / "images"
THUMB_SIZE = (140, 200)
THUMB_QUALITY = 70


FEATURED_DOCS = ["2310", "1000", "1330", "1540", "1620"]

# Three-level workflow status (E67/E77); legacy values are mapped on mirror read
# so catalog and histogram stay consistent.
DEFAULT_STREAM_STATUS = "unverifiziert"
_STREAM_STATUS_MIGRATION = {"offen": "unverifiziert", "bearbeitet": "in_arbeit", "fertig": "verifiziert"}

# Die drei Pflichtstroeme hat jedes Dokument; `entities` nur dort, wo eine Entity-Preview
# existiert (page_manifest legt ihn an). Ein fehlender Strom heisst "keine Annotationen",
# nicht "unverifiziert" -- deshalb wird er nicht aufgefuellt.
WORKFLOW_STREAMS = ("ocr", "layout", "tei")
ENTITY_STREAM = "entities"

LANG_LABELS = {
    "FR": "Franzoesisch",
    "DE": "Deutsch",
    "EN": "Englisch",
    "IT": "Italienisch",
    "DE/FR": "Deutsch/Franzoesisch",
    "?": "Unbestimmt",
}

TYPE_LABELS = {
    "A": "Einspaltig",
    "B": "Zweispaltig",
    "C": "Monografie",
    "D": "Spezialformat",
}

PUB_FORM_LABELS = {
    "journalArticle": "Zeitschriftenartikel",
    "book": "Buch",
    "bookSection": "Buchkapitel",
    "encyclopedia": "Lexikonartikel",
    "brochure": "Broschure",
    "interview": "Interview",
    "anthology": "Anthologie",
    "other": "Sonstige",
}


# ---------------------------------------------------------------------------
# Per-Seiten-Mirror: macht den Viewer ohne lokalen Server fuer alle 285 Docs
# ---------------------------------------------------------------------------

_NS_RE = re.compile(r'\s+xmlns\s*=\s*"[^"]*"')
_REVISION_RE = re.compile(r"<revisionDesc.*?</revisionDesc>", re.DOTALL)
# <div>-Tags (offen, nicht self-closing) bzw. schliessend, fuer das Balancieren
# von Seiten-Chunks, die zwischen zwei <pb> aus dem Dokument geschnitten werden.
_DIV_TAG_RE = re.compile(r'<div\b[^>]*?(?<!/)>|</div\s*>')


def _balance_divs(chunk: str) -> str:
    """Balanciert <div>-Tags eines zwischen zwei <pb> geschnittenen Chunks.

    Ein Seiten-Chunk kann ein </div> tragen, dessen <div> auf einer frueheren
    Seite geoeffnet wurde (oder umgekehrt). Fuehrende ueberzaehlige </div>
    bekommen ein <div> davor, am Ende offene <div> ein </div> dahinter -- damit
    ist das Fragment standalone wohlgeformt (core.js parst strikt als text/xml).
    """
    stack = 0
    leading_closes = 0
    for m in _DIV_TAG_RE.finditer(chunk):
        if m.group().startswith("</"):
            if stack > 0:
                stack -= 1
            else:
                leading_closes += 1
        else:
            stack += 1
    return ("<div>" * leading_closes) + chunk + ("</div>" * stack)


def _extract_pages_from_final(final_path: Path) -> dict:
    """Splittet ein assembliertes TEI-Dokument in einzelne Seiten-Bodies.

    Seitenzahl = sequenzielle Position der <pb>-Elemente (1-basiert), NICHT
    das n-Attribut — denn etliche Docs (z. B. 100) tragen die originale
    Journal-Pagination im n-Attribut (n="56"), wir brauchen aber 1,2,3...
    passend zu den Bilddateinamen.

    Returns: {page_number: xml_string} (mit minimalem TEI-Envelope).
    """
    try:
        raw = final_path.read_text(encoding="utf-8")
    except OSError:
        return {}

    clean = _NS_RE.sub("", raw)

    # Body extrahieren
    body_match = BODY_INNER_RE.search(clean)
    if not body_match:
        return {}
    body_inner = body_match.group(1)

    spans = iter_page_spans(body_inner)
    if not spans:
        return {1: _wrap_page(f"<body>{body_inner}</body>")}

    pages = {}
    for span in spans:
        # Chunk inkl. pb-Tag (Seitenanfang) bis zum naechsten pb
        chunk = _balance_divs(body_inner[span.pb_start:span.content_end])
        pages[span.page] = _wrap_page(f"<body>{chunk}</body>")
    return pages


def _wrap_page(body_xml: str) -> str:
    """Umschliesst einen Seiten-Body mit minimalem TEI-Envelope."""
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<TEI xmlns="http://www.tei-c.org/ns/1.0">\n'
        '  <text>\n'
        f'    {body_xml}\n'
        '  </text>\n'
        '</TEI>\n'
    )


# ---------------------------------------------------------------------------
# Textseite -> Scanbild: pb@facs statt sequenzieller Annahme
# ---------------------------------------------------------------------------

# Doppelseitige Scans tragen mehr <pb> als Bilder, gestrippte Deckblaetter weniger;
# die sequenzielle Annahme "Textseite N = Bild N" bricht dort. <pb facs="#facs_N">
# benennt den physischen Scan, die zugehoerige <surface> traegt sein Bild.
_SURFACE_GRAPHIC_RE = re.compile(
    r'<surface\b[^>]*\bxml:id="facs_(\d+)"[^>]*>\s*<graphic\b[^>]*\burl="([^"]+)"'
)
_PB_FACS_RE = re.compile(r'\bfacs="#facs_(\d+)"')


def _surface_images(clean: str) -> dict:
    """facs-Index -> Bilddateiname, aus <surface xml:id="facs_N"><graphic url=.../>."""
    return {int(m.group(1)): m.group(2) for m in _SURFACE_GRAPHIC_RE.finditer(clean)}


def facs_anchors(clean: str) -> list:
    """facs-Index je Textseite in Dokumentreihenfolge; None wo ein <pb> keinen Anker hat."""
    body_match = BODY_INNER_RE.search(clean)
    if not body_match:
        return []
    out = []
    for span in iter_page_spans(body_match.group(1)):
        m = _PB_FACS_RE.search(span.pb_tag)
        out.append(int(m.group(1)) if m else None)
    return out


def build_facs_map(final_text: str) -> dict:
    """Textseite (1-basierte <pb>-Position) -> Bilddateiname des Scans.

    Seiten ohne facs-Anker und Anker ohne aufloesbare <surface> bleiben weg; dort
    gilt beim Konsumenten weiter die sequenzielle Konvention.
    """
    clean = _NS_RE.sub("", final_text)
    images = _surface_images(clean)
    out = {}
    for page, idx in enumerate(facs_anchors(clean), start=1):
        img = images.get(idx) if idx is not None else None
        if img:
            out[page] = img
    return out


def write_facs_map(doc_dir: Path, doc_id: str, final_text: str) -> bool:
    """Schreibt den Spiegel-Sidecar {doc}_facs.json (deterministisch, ohne Zeitstempel)."""
    facs_map = build_facs_map(final_text)
    dst = doc_dir / f"{doc_id}_facs.json"
    if not facs_map:
        if dst.exists():
            dst.unlink()
        return False
    payload = {
        "doc_id": doc_id,
        "facs_image": {str(p): name for p, name in sorted(facs_map.items())},
    }
    dst.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return True


def audit_facs_mapping(final_dir: Path = TEI_FINAL_DIR, images_dir: Path = IMAGES_DIR) -> dict:
    """Read-only-Befund: Dokumente, deren pb->facs-Folge nicht 1,2,3... ist.

    Klassen pro Dokument: `offset_start` (erster Anker != 1, z. B. gestripptes
    Deckblatt), `duplicate_scan` (zwei Textseiten auf einem Scan = Doppelseite),
    `out_of_order` (Folge nicht monoton steigend), `unresolved_surface` (Anker ohne
    <surface>), `missing_anchor` (<pb> ohne facs).
    """
    entries = []
    scanned = 0
    for final_path in sorted(final_dir.glob("*_final.xml"), key=lambda p: int(p.stem.split("_")[0])):
        doc_id = final_path.stem.replace("_final", "")
        try:
            clean = _NS_RE.sub("", final_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError):
            continue
        scanned += 1
        anchors = facs_anchors(clean)
        if not anchors:
            continue
        present = [a for a in anchors if a is not None]
        if anchors == list(range(1, len(anchors) + 1)):
            continue

        images = _surface_images(clean)
        seen, duplicates = set(), []
        for a in present:
            if a in seen and a not in duplicates:
                duplicates.append(a)
            seen.add(a)
        unresolved = sorted({a for a in present if a not in images})
        facs_map = build_facs_map(clean)
        on_disk = {p.name for p in (images_dir / doc_id).glob("*.png")} if (images_dir / doc_id).is_dir() else set()
        missing_images = sorted({n for n in facs_map.values() if n not in on_disk}) if on_disk else []

        kinds = []
        if present and present[0] != 1:
            kinds.append("offset_start")
        if duplicates:
            kinds.append("duplicate_scan")
        if any(b < a for a, b in pairwise(present)):
            kinds.append("out_of_order")
        if unresolved:
            kinds.append("unresolved_surface")
        if len(present) != len(anchors):
            kinds.append("missing_anchor")

        entries.append({
            "doc_id": doc_id,
            "kinds": kinds,
            "pb_count": len(anchors),
            "surface_count": len(images),
            "image_count": len(on_disk),
            "facs_sequence": anchors,
            "duplicate_scans": duplicates,
            "unresolved_facs": unresolved,
            "mapped_pages": len(facs_map),
            "missing_images": missing_images,
        })

    return {
        "generator": "scripts/edition/generate_edition_data.py --facs-audit",
        "source": "output/tei_final/*_final.xml",
        "summary": {
            "documents_scanned": scanned,
            "documents_affected": len(entries),
            "affected_ids": [e["doc_id"] for e in entries],
        },
        "documents": entries,
    }


def generate_thumbnails(verbose: bool = False) -> int:
    """Erzeugt JPEG-Thumbnails (140x200, q=70) der ersten Seite jedes Dokuments
    fuer die Korpus-Uebersicht. Lokal verfuegbare Bilder aus docs/images/{doc}/
    werden gelesen; Docs ohne lokales Bild bekommen kein Thumb (Placeholder im UI).

    Output: docs/data/thumbs/{doc}.jpg, ~3-5 KB pro Datei.
    """
    try:
        from PIL import Image
    except ImportError:
        print("  Thumbs: Pillow nicht verfuegbar, ueberspringe")
        return 0

    if not IMAGES_DIR.exists():
        print("  Thumbs: docs/images/ nicht gefunden, ueberspringe")
        return 0

    THUMBS_DIR.mkdir(parents=True, exist_ok=True)
    created = 0

    for doc_dir in sorted(IMAGES_DIR.iterdir(), key=lambda p: p.name):
        if not doc_dir.is_dir():
            continue
        doc_id = doc_dir.name

        # Erste Seite finden (sortiert nach Name → p001 zuerst)
        first_pages = sorted(doc_dir.glob(f"{doc_id}_p*.png")) + \
                      sorted(doc_dir.glob(f"{doc_id}_p*.jpg"))
        if not first_pages:
            continue
        src = first_pages[0]

        dst = THUMBS_DIR / f"{doc_id}.jpg"
        if dst.exists() and src.stat().st_mtime <= dst.stat().st_mtime:
            continue

        try:
            with Image.open(src) as img:
                if img.mode != "RGB":
                    img = img.convert("RGB")
                img.thumbnail(THUMB_SIZE, Image.LANCZOS)
                img.save(dst, "JPEG", quality=THUMB_QUALITY, optimize=True)
            created += 1
            if verbose:
                print(f"  thumb {doc_id}: {dst.stat().st_size // 1024} KB")
        except Exception as e:
            if verbose:
                print(f"  thumb {doc_id} FEHLER: {e}")

    return created


def mirror_manifests(verbose: bool = False) -> int:
    """Spiegelt Pro-Objekt-Manifeste nach docs/data/manifests/{doc}_manifest.json.

    Der Viewer liest aus diesem Spiegel den Workflow-Status pro Strom (E66) und
    schreibt Aenderungen als Datei-Download zurueck; Anwender:innen legen die
    Datei dann manuell in `output/tei_final/` ab. Beim naechsten Mirror-Lauf
    wandert der neue Stand wieder hierher.
    """
    if not TEI_FINAL_DIR.exists():
        return 0
    MANIFESTS_DIR.mkdir(parents=True, exist_ok=True)
    n = 0
    for src in TEI_FINAL_DIR.glob("*_manifest.json"):
        dst = MANIFESTS_DIR / src.name
        if not dst.exists() or src.stat().st_mtime > dst.stat().st_mtime:
            shutil.copy2(src, dst)
            n += 1
            if verbose:
                print(f"  manifest {src.name}")
    return n


def mirror_per_page_data(verbose: bool = False, only_docs=None) -> dict:
    """Spiegelt per-Seiten-Daten (Layout, Mistral-OCR, TEI) fuer alle 285 Docs
    nach docs/data/pages/{doc}/.

    Damit funktioniert der Viewer ohne lokalen Server (GitHub Pages tauglich)
    fuer das gesamte Korpus, nicht nur die 4 Demo-Docs.

    `only_docs` beschraenkt den Lauf auf einzelne Dokument-IDs (gezielte
    Regeneration statt Vollspiegelung).

    Returns: Statistik-Dict {layout, ocr, tei, facs, docs}.
    """
    stats = {"docs": 0, "layout": 0, "ocr": 0, "tei": 0, "facs": 0, "skipped": 0}

    if not TEI_FINAL_DIR.exists():
        print("  Mirror: tei_final/ nicht gefunden, ueberspringe")
        return stats

    PAGES_DIR.mkdir(parents=True, exist_ok=True)
    final_files = sorted(TEI_FINAL_DIR.glob("*_final.xml"))
    if only_docs:
        wanted = {str(d) for d in only_docs}
        final_files = [p for p in final_files if p.stem.replace("_final", "") in wanted]

    for final_path in final_files:
        doc_id = final_path.stem.replace("_final", "")
        doc_dir = PAGES_DIR / doc_id
        doc_dir.mkdir(parents=True, exist_ok=True)

        # 1. Layout-JSONs (Docling + Gemini)
        layout_src = LAYOUT_DIR / doc_id
        layout_n = 0
        if layout_src.exists():
            for src in layout_src.glob(f"{doc_id}_p*_layout*.json"):
                dst = doc_dir / src.name
                if not dst.exists() or src.stat().st_mtime > dst.stat().st_mtime:
                    shutil.copy2(src, dst)
                    layout_n += 1
        stats["layout"] += layout_n

        # 2. Mistral-OCR (Markdown, unpadded)
        ocr_n = 0
        for src in MISTRAL_DIR.glob(f"{doc_id}_p*.md"):
            dst = doc_dir / src.name
            if not dst.exists() or src.stat().st_mtime > dst.stat().st_mtime:
                shutil.copy2(src, dst)
                ocr_n += 1
        stats["ocr"] += ocr_n

        # 3. Per-Seiten-TEI aus tei_final extrahieren
        pages = _extract_pages_from_final(final_path)
        tei_n = 0
        for page_num, xml in pages.items():
            dst = doc_dir / f"{doc_id}_p{page_num}.xml"
            try:
                dst.write_text(xml, encoding="utf-8")
                tei_n += 1
            except OSError:
                pass
        stats["tei"] += tei_n

        # 3b. Textseite -> Scanbild (pb@facs); ohne diesen Sidecar zeigt der Viewer
        # bei Doppelseiten-Scans und gestrippten Deckblaettern das falsche Faksimile.
        try:
            if write_facs_map(doc_dir, doc_id, final_path.read_text(encoding="utf-8")):
                stats["facs"] += 1
        except (OSError, UnicodeDecodeError):
            pass

        # 4. Finales TEI auch nach pages/ kopieren (fuer Download-Fallback)
        dst_final = doc_dir / f"{doc_id}_final.xml"
        if not dst_final.exists() or final_path.stat().st_mtime > dst_final.stat().st_mtime:
            shutil.copy2(final_path, dst_final)

        stats["docs"] += 1
        if verbose:
            print(f"  {doc_id}: {layout_n} layout, {ocr_n} ocr, {tei_n} tei")

    return stats


# ---------------------------------------------------------------------------
# Asset-Existenz: welche Mirror-Dateien es pro Dokument wirklich gibt
# ---------------------------------------------------------------------------

# Ohne diesen Index fragt der Viewer pro Seite auf Verdacht an (404-Rauschen in der
# Browser-Konsole). Seitenlisten kompakt: "*" = genau 1..page_count, sonst "1-9,12".
_ASSET_PAGE_PATTERNS = (
    ("ocr", r"_p(\d+)\.md"),
    ("tei", r"_p(\d+)\.xml"),
    ("layout", r"_p(\d+)_layout\.json"),
    ("layout_gemini", r"_p(\d+)_layout_gemini\.json"),
    ("layout_curated", r"_p(\d+)_layout_curated\.json"),
    ("entity", r"_entity_p(\d+)\.xml"),
)
_ASSET_FLAGS = (
    ("entity_worklist", "_entity_worklist.json"),
    ("facs_map", "_facs.json"),
    ("final", "_final.xml"),
)


def _encode_pages(pages: set, page_count: int) -> str:
    if not pages:
        return ""
    if page_count and pages == set(range(1, page_count + 1)):
        return "*"
    parts = []
    start = prev = None
    for p in sorted(pages):
        if start is None:
            start = prev = p
        elif p == prev + 1:
            prev = p
        else:
            parts.append(str(start) if start == prev else f"{start}-{prev}")
            start = prev = p
    parts.append(str(start) if start == prev else f"{start}-{prev}")
    return ",".join(parts)


def scan_mirror_assets(doc_dir: Path, doc_id: str, page_count: int) -> dict:
    """Existenz-Index der gespiegelten Dateien eines Dokuments (Seitenlisten + Flags)."""
    if not doc_dir.is_dir():
        return {}
    names = {p.name for p in doc_dir.iterdir()}
    assets = {}
    for kind, suffix in _ASSET_PAGE_PATTERNS:
        rx = re.compile(re.escape(doc_id) + suffix)
        pages = {int(m.group(1)) for n in names if (m := rx.fullmatch(n))}
        spec = _encode_pages(pages, page_count)
        if spec:
            assets[kind] = spec
    for flag, suffix in _ASSET_FLAGS:
        if f"{doc_id}{suffix}" in names:
            assets[flag] = True
    return assets


_TITLECASE_WORD_RE = re.compile(r"\b([\wÀ-ÿ]+)\b", re.UNICODE)

def _normalize_author(name):
    """Vermeidet HARTE-Caps-Autoren (z.B. "JEANNE HERSCH" -> "Jeanne Hersch").

    Wirkt nur, wenn der gesamte Name fast vollstaendig in Grossbuchstaben steht
    (>=80% der Buchstaben). Reine Initialen oder gemischte Faelle bleiben
    unveraendert. Diakritik wird respektiert (À-ÿ).
    """
    if not name or not isinstance(name, str):
        return name
    letters = [c for c in name if c.isalpha()]
    if not letters:
        return name
    upper_ratio = sum(1 for c in letters if c.isupper()) / len(letters)
    if upper_ratio < 0.8:
        return name
    # Title-case mit Spezialfaellen fuer kleine Worte und Apostrophe (l', d', ...)
    def fix_word(m):
        w = m.group(1)
        if len(w) <= 1:
            return w
        return w[0].upper() + w[1:].lower()
    return _TITLECASE_WORD_RE.sub(fix_word, name.lower()).replace(" L'", " l'").replace(" D'", " d'")


def build_catalog():
    """Baut catalog.json aus doc_metadata.json + tei_final/ + Pro-Objekt-Manifesten.

    dashboard.json wurde mit E56 abgeschafft. Falls vorhanden, dient es als Initial-
    Map; sonst werden alle Docs aus tei_final/*_final.xml entdeckt und mit Gemini-
    Metadaten aufgefuellt.
    """
    dashboard = load_json(DOCS_DIR / "data" / "dashboard.json") or {}

    doc_metadata = load_json(DOC_METADATA_PATH) or {}
    gemini_docs = doc_metadata.get("documents", {})

    docs = dict(dashboard.get("documents", {}))

    # Discover docs from tei_final/ that are not in dashboard
    if TEI_FINAL_DIR.exists():
        for tei_file in TEI_FINAL_DIR.glob("*_final.xml"):
            doc_id = tei_file.stem.replace("_final", "")
            if doc_id not in docs:
                # Build minimal entry from Gemini metadata + TEI
                gm = gemini_docs.get(doc_id, {})
                lang_map = {"fra": "FR", "deu": "DE", "fra/deu": "DE/FR",
                            "deu/fra": "DE/FR", "eng": "EN", "ita": "IT", "und": "?"}
                lang_raw = gm.get("language", "und")
                page_count = gm.get("page_count", 0)
                if not page_count:
                    # Count pages from images directory
                    img_dir = DOCS_DIR / "images" / doc_id
                    if img_dir.exists():
                        page_count = len(list(img_dir.glob("*.jpg"))) + len(list(img_dir.glob("*.png")))
                docs[doc_id] = {
                    "title": gm.get("title") or "Dokument " + doc_id,
                    "author": gm.get("author"),
                    "date": gm.get("date"),
                    "lang": lang_map.get(lang_raw, lang_raw.upper() if lang_raw else "?"),
                    "type": gm.get("layout_type", "-"),
                    "pub_form": gm.get("pub_form"),
                    "desc": gm.get("description", ""),
                    "page_count": page_count,
                    "pipeline_status": {"tei": True},
                }

    # Workflow-Status vorladen (aus Pro-Objekt-Manifesten, E66)
    # streams = { ocr: {status, last_at, last_by}, layout: {...}, tei: {...} }
    manifest_streams = {}
    if TEI_FINAL_DIR.exists():
        for mf in TEI_FINAL_DIR.glob("*_manifest.json"):
            try:
                m = json.loads(mf.read_text(encoding="utf-8"))
                did = m.get("doc_id", mf.stem.replace("_manifest", ""))
                streams_in = m.get("streams") or {}
                streams_out = {}
                names = list(WORKFLOW_STREAMS)
                if isinstance(streams_in.get(ENTITY_STREAM), dict):
                    names.append(ENTITY_STREAM)
                for sname in names:
                    s = streams_in.get(sname)
                    if not isinstance(s, dict):
                        streams_out[sname] = {"status": "unverifiziert", "last_at": None, "last_by": None}
                        continue
                    history = s.get("history") or []
                    last = history[-1] if history else {}
                    raw_status = s.get("status", DEFAULT_STREAM_STATUS)
                    streams_out[sname] = {
                        "status": _STREAM_STATUS_MIGRATION.get(raw_status, raw_status),
                        "last_at": last.get("at"),
                        "last_by": last.get("by"),
                    }
                manifest_streams[did] = streams_out
            except (OSError, json.JSONDecodeError):
                pass

    # Kurations-Status vorladen (aus curated_tei/ Metadaten)
    curation_status = {}
    if TEI_CURATED_DIR.exists():
        for meta_file in TEI_CURATED_DIR.glob("*/*_curation.json"):
            try:
                meta = json.loads(meta_file.read_text(encoding="utf-8"))
                did = meta.get("doc_id", meta_file.parent.name)
                curation_status[did] = meta.get("status", "uncurated")
            except (OSError, json.JSONDecodeError):
                pass

    # Dokument-Eintraege bauen
    entries = []
    pages_dir = DOCS_DIR / "data" / "pages"
    for doc_id, doc in sorted(docs.items(), key=lambda x: int(x[0])):
        page_count = doc.get("page_count", 0)
        entry = {
            "id": doc_id,
            "title": doc.get("title") or "Dokument " + doc_id,
            "author": _normalize_author(doc.get("author")),
            "date": doc.get("date"),
            "lang": doc.get("lang", "?"),
            "type": doc.get("type", "-"),
            "pub_form": doc.get("pub_form"),
            "desc": doc.get("desc", ""),
            "page_count": page_count,
            "has_tei": doc.get("pipeline_status", {}).get("tei", False),
            "assets": scan_mirror_assets(pages_dir / doc_id, doc_id, page_count),
            "streams": manifest_streams.get(doc_id, {
                "ocr":    {"status": "unverifiziert", "last_at": None, "last_by": None},
                "layout": {"status": "unverifiziert", "last_at": None, "last_by": None},
                "tei":    {"status": "unverifiziert", "last_at": None, "last_by": None},
            }),
            "curation": curation_status.get(doc_id, "uncurated"),
            "demo": doc_id in FEATURED_DOCS,
        }
        entries.append(entry)

    # Sprach-Verteilung
    lang_counts = {}
    type_counts = {}
    form_counts = {}
    for e in entries:
        lang_counts[e["lang"]] = lang_counts.get(e["lang"], 0) + 1
        type_counts[e["type"]] = type_counts.get(e["type"], 0) + 1
        pf = e["pub_form"] or "other"
        form_counts[pf] = form_counts.get(pf, 0) + 1

    # Pro Strom: Verteilung der Workflow-Status (E66)
    stream_status_counts = {name: {} for name in (*WORKFLOW_STREAMS, ENTITY_STREAM)}
    curation_counts = {}
    for e in entries:
        streams = e.get("streams") or {}
        names = list(WORKFLOW_STREAMS)
        if ENTITY_STREAM in streams:
            names.append(ENTITY_STREAM)
        for sname in names:
            st = streams.get(sname, {}).get("status") or "unverifiziert"
            stream_status_counts[sname][st] = stream_status_counts[sname].get(st, 0) + 1
        c = e.get("curation") or "uncurated"
        curation_counts[c] = curation_counts.get(c, 0) + 1

    catalog = {
        "generated": datetime.now().isoformat(timespec="seconds"),
        "generator": "scripts/edition/generate_edition_data.py",
        "edition": {
            "title": "Nachlass Jeanne Hersch",
            "subtitle": "Digitale Edition",
            "institution": "Zentralbibliothek Zuerich",
            "project": "DHCraft",
            "total_docs": len(entries),
            "total_pages": sum(e.get("page_count", 0) for e in entries),
            "languages": len(lang_counts),
            "date_range": "1926-2000",
        },
        "featured": FEATURED_DOCS,
        "corpus": {
            "languages": lang_counts,
            "types": type_counts,
            "forms": form_counts,
            "stream_status": stream_status_counts,
            "curation": curation_counts,
        },
        "labels": {
            "languages": LANG_LABELS,
            "types": TYPE_LABELS,
            "pub_forms": PUB_FORM_LABELS,
        },
        "documents": entries,
    }

    return catalog


def main():
    parser = argparse.ArgumentParser(description="Edition-Daten fuer den Viewer generieren")
    parser.add_argument("--no-mirror", action="store_true",
                        help="Per-Seiten-Mirror ueberspringen (schneller, aber Viewer broken fuer 281 Docs)")
    parser.add_argument("--mirror-only", action="store_true",
                        help="Nur per-Seiten-Mirror laufen lassen, Katalog/Index unveraendert")
    parser.add_argument("--doc", action="append", metavar="DOC_ID",
                        help="Nur diese Dokument-ID(s) spiegeln (mehrfach angebbar); "
                             "Katalog und Thumbs bleiben unberuehrt")
    parser.add_argument("--facs-audit", action="store_true",
                        help="Read-only: pb->facs-Folgen des Korpus pruefen "
                             "-> output/audits/facs_mapping_report.json")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Pro Doc Output")
    args = parser.parse_args()

    if args.facs_audit:
        report = audit_facs_mapping()
        out = OUTPUT_DIR / "audits" / "facs_mapping_report.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        s = report["summary"]
        print(f"facs-Audit: {s['documents_affected']}/{s['documents_scanned']} Docs nicht sequenziell")
        print(f"  betroffen: {', '.join(s['affected_ids'])}")
        print(f"  Bericht: {out}")
        return

    print("Edition-Daten generieren...")

    if args.doc:
        print(f"Gezielter Mirror fuer {', '.join(args.doc)} nach docs/data/pages/...")
        stats = mirror_per_page_data(verbose=args.verbose, only_docs=args.doc)
        print(f"  Mirror fertig: {stats['docs']} Docs, {stats['layout']} Layout, "
              f"{stats['ocr']} OCR, {stats['tei']} TEI-Seiten, {stats['facs']} facs-Maps")
        return

    if args.mirror_only:
        print("Per-Seiten-Mirror nach docs/data/pages/...")
        stats = mirror_per_page_data(verbose=args.verbose)
        print(f"  Mirror fertig: {stats['docs']} Docs, "
              f"{stats['layout']} Layout, {stats['ocr']} OCR, {stats['tei']} TEI-Seiten")
        print("Manifeste nach docs/data/manifests/...")
        n_mf = mirror_manifests(verbose=args.verbose)
        print(f"  Manifeste gespiegelt: {n_mf}")
        print("Thumbnails nach docs/data/thumbs/...")
        n_thumbs = generate_thumbnails(verbose=args.verbose)
        print(f"  Thumbs erzeugt: {n_thumbs}")
        return

    # 1. Manifeste spiegeln (klein, immer mitlaufen lassen)
    n_mf = mirror_manifests(verbose=args.verbose)
    print(f"  Manifeste gespiegelt: {n_mf} -> docs/data/manifests/")

    # 2. Per-Seiten-Mirror fuer alle 285 Docs (kann mit --no-mirror uebersprungen werden)
    if not args.no_mirror:
        print("\nPer-Seiten-Mirror nach docs/data/pages/...")
        stats = mirror_per_page_data(verbose=args.verbose)
        print(f"  Mirror fertig: {stats['docs']} Docs, "
              f"{stats['layout']} Layout, {stats['ocr']} OCR, {stats['tei']} TEI-Seiten")
        print("Thumbnails nach docs/data/thumbs/...")
        n_thumbs = generate_thumbnails(verbose=args.verbose)
        print(f"  Thumbs erzeugt/aktualisiert: {n_thumbs}")

    # 3. Katalog bauen (nach dem Mirror: `assets` indiziert den tatsaechlichen Mirror-Stand)
    catalog = build_catalog()
    if not catalog:
        return

    # 4. Katalog schreiben
    output_path = DOCS_DIR / "data" / "catalog.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(catalog, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(f"\nEdition-Katalog geschrieben: {output_path}")
    print(f"  Dokumente: {catalog['edition']['total_docs']}")
    print(f"  Seiten: {catalog['edition']['total_pages']}")
    print(f"  Featured: {catalog['featured']}")
    print(f"  Sprachen: {catalog['edition']['languages']}")

    # Verifikation
    doc_count = len(catalog["documents"])
    demo_count = sum(1 for d in catalog["documents"] if d["demo"])
    tei_count = sum(1 for d in catalog["documents"] if d["has_tei"])
    print(f"\n  Verifikation: {doc_count} Eintraege, {demo_count} Demo-Docs, {tei_count} mit TEI")


if __name__ == "__main__":
    main()
