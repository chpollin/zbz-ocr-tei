"""
Generiert docs/edition/data/catalog.json fuer die Digitale Edition.

Liest docs/data/dashboard.json + data/doc_metadata.json und erzeugt
einen kompakten Katalog mit allen Dokumenten + Edition-Metadaten.
Kopiert fehlende TEI-XMLs fuer Demo-Docs nach docs/data/examples/.

Usage:
    python scripts/generate_edition_data.py
"""

import json
import shutil
from datetime import datetime
from pathlib import Path

from scripts.config import PROJECT_ROOT, DOCS_DIR, TEI_DIR, DOC_METADATA_PATH
from scripts.utils import load_json


FEATURED_DOCS = ["2310", "1000", "1330", "1540"]

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


def copy_demo_tei_files():
    """Kopiert fehlende TEI-XMLs fuer Demo-Docs nach docs/data/examples/."""
    copied = 0
    for doc_id in FEATURED_DOCS:
        examples_dir = DOCS_DIR / "data" / "examples" / doc_id
        examples_dir.mkdir(parents=True, exist_ok=True)

        for tei_file in sorted(TEI_DIR.glob(f"{doc_id}_p*.xml")):
            target = examples_dir / tei_file.name
            if not target.exists():
                shutil.copy2(tei_file, target)
                copied += 1

    return copied


def build_catalog():
    """Baut catalog.json aus dashboard.json + doc_metadata.json."""
    dashboard = load_json(DOCS_DIR / "data" / "dashboard.json")
    if not dashboard:
        print("FEHLER: dashboard.json nicht gefunden!")
        return None

    doc_metadata = load_json(DOC_METADATA_PATH) or {}
    gemini_docs = doc_metadata.get("documents", {})

    docs = dashboard.get("documents", {})
    overview = dashboard.get("pipeline_summary", {})

    # Dokument-Eintraege bauen
    entries = []
    for doc_id, doc in sorted(docs.items(), key=lambda x: int(x[0])):
        entry = {
            "id": doc_id,
            "title": doc.get("title") or "Dokument " + doc_id,
            "author": doc.get("author"),
            "date": doc.get("date"),
            "lang": doc.get("lang", "?"),
            "type": doc.get("type", "-"),
            "pub_form": doc.get("pub_form"),
            "desc": doc.get("desc", ""),
            "page_count": doc.get("page_count", 0),
            "has_tei": doc.get("pipeline_status", {}).get("tei", False),
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

    catalog = {
        "generated": datetime.now().isoformat(timespec="seconds"),
        "generator": "scripts/generate_edition_data.py",
        "edition": {
            "title": "Nachlass Jeanne Hersch",
            "subtitle": "Digitale Edition",
            "institution": "Zentralbibliothek Zuerich",
            "project": "DHCraft",
            "total_docs": len(entries),
            "total_pages": overview.get("total_pages", 0),
            "languages": len(lang_counts),
            "date_range": "1926-2000",
        },
        "featured": FEATURED_DOCS,
        "corpus": {
            "languages": lang_counts,
            "types": type_counts,
            "forms": form_counts,
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
    print("Edition-Daten generieren...")

    # 1. TEI-XMLs fuer Demo-Docs kopieren
    copied = copy_demo_tei_files()
    print(f"  TEI-XMLs kopiert: {copied}")

    # 2. Katalog bauen
    catalog = build_catalog()
    if not catalog:
        return

    # 3. Schreiben
    output_path = DOCS_DIR / "edition" / "data" / "catalog.json"
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
