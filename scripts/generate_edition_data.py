"""
Generiert Edition-Daten: catalog.json, entity_index.json, entity_register.json.

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

from scripts.config import PROJECT_ROOT, DOCS_DIR, TEI_DIR, TEI_FINAL_DIR, TEI_CURATED_DIR, DOC_METADATA_PATH, ENTITIES_DIR
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
    """Kopiert finale TEI-XMLs fuer Demo-Docs nach docs/data/examples/.

    Bevorzugt tei_final/ (gescreente Dokumente mit revisionDesc).
    Fallback auf TEI_DIR (alte rule-based TEIs) wenn tei_final nicht vorhanden.
    """
    copied = 0
    for doc_id in FEATURED_DOCS:
        examples_dir = DOCS_DIR / "data" / "examples" / doc_id
        examples_dir.mkdir(parents=True, exist_ok=True)

        # Bevorzugt: Finale TEI aus Quality Screening
        final_tei = TEI_FINAL_DIR / f"{doc_id}_final.xml"
        if final_tei.exists():
            target = examples_dir / f"{doc_id}_final.xml"
            if not target.exists() or final_tei.stat().st_mtime > target.stat().st_mtime:
                shutil.copy2(final_tei, target)
                copied += 1
        else:
            # Fallback: Alte page-level TEIs
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

    docs = dict(dashboard.get("documents", {}))
    overview = dashboard.get("pipeline_summary", {})

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

    # Screening-Status vorladen (aus Review-JSONs)
    screening_status = {}
    if TEI_FINAL_DIR.exists():
        for review_file in TEI_FINAL_DIR.glob("*_review.json"):
            try:
                review = json.loads(review_file.read_text(encoding="utf-8"))
                did = review.get("doc_id", review_file.stem.replace("_review", ""))
                screening_status[did] = {
                    "status": review.get("status", "UNKNOWN"),
                    "reviewer": review.get("reviewer", "unknown"),
                    "date": review.get("date", ""),
                }
            except (json.JSONDecodeError, IOError):
                pass

    # Entity-Counts vorladen
    entity_counts = {}
    if ENTITIES_DIR.exists():
        try:
            from scripts.ner.entity_store import EntityStore
            for d in ENTITIES_DIR.iterdir():
                if d.is_dir() and not d.name.startswith("_"):
                    store = EntityStore.load(d.name)
                    s = store.summary()
                    entity_counts[d.name] = s["total_entities"]
        except Exception:
            pass

    # Kurations-Status vorladen (aus tei_curated/ Metadaten)
    curation_status = {}
    if TEI_CURATED_DIR.exists():
        for meta_file in TEI_CURATED_DIR.glob("*/*_curation.json"):
            try:
                meta = json.loads(meta_file.read_text(encoding="utf-8"))
                did = meta.get("doc_id", meta_file.parent.name)
                curation_status[did] = meta.get("status", "uncurated")
            except (json.JSONDecodeError, IOError):
                pass

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
            "entity_count": entity_counts.get(doc_id, 0),
            "screening": screening_status.get(doc_id, {}).get("status"),
            "screening_reviewer": screening_status.get(doc_id, {}).get("reviewer"),
            "screening_date": screening_status.get(doc_id, {}).get("date"),
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

    screening_counts = {}
    curation_counts = {}
    for e in entries:
        s = e.get("screening") or "NOT_SCREENED"
        screening_counts[s] = screening_counts.get(s, 0) + 1
        c = e.get("curation") or "uncurated"
        curation_counts[c] = curation_counts.get(c, 0) + 1

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
            "screening": screening_counts,
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


def export_entity_index():
    """Exportiert den Entity Index als JSON fuer den Edition-Viewer."""
    try:
        from scripts.ner.entity_index import EntityIndex
        index = EntityIndex()
        index.load_all()
        if not index.entries:
            print("  Entity Index: keine Eintraege")
            return 0
        data = index.to_json_dict()
        output_path = DOCS_DIR / "data" / "entity_index.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        print(f"  Entity Index: {len(data)} Eintraege -> {output_path}")
        return len(data)
    except Exception as e:
        print(f"  Entity Index WARNUNG: {e}")
        return 0


def export_entity_register():
    """Exportiert entity_register.json mit Cross-Doc-Referenzen fuer das Register."""
    try:
        from scripts.ner.entity_index import EntityIndex
        from scripts.ner.entity_store import EntityStore
        from scripts.core.loaders import discover_entity_docs

        index = EntityIndex()
        index.load_all()
        if not index.entries:
            print("  Entity Register: keine Index-Eintraege")
            return 0

        # Cross-Doc-Aggregation: iteriere alle Entity-Stores
        entity_docs = {}      # xml_id -> set of doc_ids
        entity_mentions = {}  # xml_id -> total mention count
        entity_contexts = {}  # xml_id -> list of context strings (max 3)

        doc_ids = discover_entity_docs()
        for doc_id in doc_ids:
            store = EntityStore.load(doc_id)
            for rec in store.entities.values():
                if rec.entity_type in ("event", "date"):
                    continue
                entry = index.match_normalized(rec.normalized, rec.entity_type)
                if not entry:
                    continue
                xid = entry.xml_id
                entity_docs.setdefault(xid, set()).add(doc_id)
                entity_mentions[xid] = entity_mentions.get(xid, 0) + rec.count
                if xid not in entity_contexts:
                    entity_contexts[xid] = []
                for ctx in (rec.contexts or []):
                    if ctx and len(entity_contexts[xid]) < 3 and ctx not in entity_contexts[xid]:
                        entity_contexts[xid].append(ctx)

        # Entity-Array bauen
        entities = []
        by_type = {}
        for entry in index.entries.values():
            xid = entry.xml_id
            doc_set = entity_docs.get(xid, set())
            entities.append({
                "id": xid,
                "type": entry.entity_type,
                "name": entry.main_name,
                "variants": entry.variants,
                "wikidata_qid": entry.wikidata_qid,
                "wikidata_url": entry.wikidata_url,
                "gnd_id": entry.gnd_id,
                "doc_ids": sorted(doc_set),
                "doc_count": len(doc_set),
                "mention_count": entity_mentions.get(xid, 0),
                "contexts": entity_contexts.get(xid, []),
            })
            t = entry.entity_type
            if t not in by_type:
                by_type[t] = {"total": 0, "with_wikidata": 0, "with_gnd": 0, "with_docs": 0}
            by_type[t]["total"] += 1
            if entry.wikidata_qid:
                by_type[t]["with_wikidata"] += 1
            if entry.gnd_id:
                by_type[t]["with_gnd"] += 1
            if doc_set:
                by_type[t]["with_docs"] += 1

        data = {
            "generated": datetime.now().isoformat(timespec="seconds"),
            "summary": {
                "total_entities": len(entities),
                "total_with_docs": sum(1 for e in entities if e["doc_count"] > 0),
                "by_type": by_type,
            },
            "entities": entities,
        }

        output_path = DOCS_DIR / "data" / "entity_register.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        with_docs = data["summary"]["total_with_docs"]
        print(f"  Entity Register: {len(entities)} Eintraege ({with_docs} mit Docs) -> {output_path}")
        return len(entities)
    except Exception as e:
        print(f"  Entity Register WARNUNG: {e}")
        import traceback
        traceback.print_exc()
        return 0


def build_search_index():
    """Extrahiert Klartext aus allen TEI-Bodies fuer Volltext-Suche."""
    from xml.etree import ElementTree as ET

    if not TEI_FINAL_DIR.exists():
        print("  Search Index: tei_final/ nicht gefunden")
        return 0

    ns = {"tei": "http://www.tei-c.org/ns/1.0"}
    entries = []

    for tei_file in sorted(TEI_FINAL_DIR.glob("*_final.xml")):
        doc_id = tei_file.stem.replace("_final", "")
        try:
            tree = ET.parse(tei_file)
            root = tree.getroot()

            # Titel
            title_el = root.find(".//tei:titleStmt/tei:title", ns)
            title = title_el.text.strip() if title_el is not None and title_el.text else ""

            # Body-Text
            body = root.find(".//tei:body", ns)
            if body is None:
                continue
            text_parts = []
            for t in body.itertext():
                t = t.strip()
                if t:
                    text_parts.append(t)
            full_text = " ".join(text_parts)[:2000]

            # Entity-Namen
            entity_names = set()
            for tag in ("tei:persName", "tei:orgName", "tei:placeName"):
                for el in body.iter(tag.replace("tei:", f"{{{ns['tei']}}}")):
                    name = "".join(el.itertext()).strip()
                    if name and len(name) > 1:
                        entity_names.add(name)

            entries.append({
                "id": doc_id,
                "title": title,
                "text": full_text,
                "entities": sorted(entity_names)[:50],
            })
        except Exception:
            continue

    output_path = DOCS_DIR / "data" / "search_index.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(entries, ensure_ascii=False),
        encoding="utf-8",
    )
    size_kb = output_path.stat().st_size // 1024
    print(f"  Search Index: {len(entries)} Docs ({size_kb} KB) -> {output_path}")
    return len(entries)


def main():
    print("Edition-Daten generieren...")

    # 1. TEI-XMLs fuer Demo-Docs kopieren
    copied = copy_demo_tei_files()
    print(f"  TEI-XMLs kopiert: {copied}")

    # 2. Katalog bauen
    catalog = build_catalog()
    if not catalog:
        return

    # 3. Entity Index exportieren
    entity_count = export_entity_index()

    # 4. Entity Register exportieren (mit Cross-Doc-Referenzen)
    register_count = export_entity_register()

    # 5. Volltext-Suchindex bauen
    search_count = build_search_index()

    # 6. Katalog schreiben
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
    if entity_count:
        print(f"  Entity Index: {entity_count} Eintraege")
    if register_count:
        print(f"  Entity Register: {register_count} Eintraege")

    # Verifikation
    doc_count = len(catalog["documents"])
    demo_count = sum(1 for d in catalog["documents"] if d["demo"])
    tei_count = sum(1 for d in catalog["documents"] if d["has_tei"])
    print(f"\n  Verifikation: {doc_count} Eintraege, {demo_count} Demo-Docs, {tei_count} mit TEI")


if __name__ == "__main__":
    main()
