"""
TEI Injection: Fuegt NER-Entities in bestehende TEI-XML ein.

Liest tei_unified _final.xml, ersetzt GND-Refs durch WD-Refs,
fuegt fehlende Entity-Tags hinzu, schreibt nach tei_ner/.

Aufruf:
    python -m scripts.ner.ner_inject_tei --doc 2310
    python -m scripts.ner.ner_inject_tei --all
    python -m scripts.ner.ner_inject_tei --doc 2310 --validate
"""

import argparse
import json
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.config import (
    ENTITIES_DIR,
    TEI_NER_DIR,
    TEI_NS,
    TEI_UNIFIED_DIR,
)
from scripts.core.loaders import discover_entity_docs
from scripts.ner.entity_index import EntityIndex
from scripts.ner.entity_store import EntityRecord, EntityStore

# TEI Element-Mapping fuer Entity-Typen
ENTITY_TEI_MAP = {
    "person": ("persName", "ref"),
    "organization": ("orgName", "ref"),
    "place": ("placeName", "ref"),
    "work": ("bibl", "corresp"),
    "event": ("name", "ref"),  # <name type="event" ref="...">
}

# Tags die bereits Entities enthalten (nicht doppelt taggen)
ENTITY_TAG_PATTERN = re.compile(
    r'<(?:persName|orgName|placeName|bibl|name)\b[^>]*>.*?'
    r'</(?:persName|orgName|placeName|bibl|name)>',
    re.DOTALL,
)


# ---------------------------------------------------------------------------
# Ref-Update: Dual-Attribut-Strategie (E50)
#   ref="GND:{id}"       -- primaere Referenz (nur wenn GND vorhanden)
#   corresp="#zbz-p.N"   -- interne ID (immer vorhanden)
# ---------------------------------------------------------------------------

def update_existing_refs(
    xml_text: str,
    store: EntityStore,
    index: "EntityIndex | None" = None,
) -> str:
    """Aktualisiert bestehende Entity-Tags mit Dual-Attributen (E50).

    Zwei-Pass-Strategie:
    1. Leaf-Pass: Innere Tags (persName/orgName/placeName ohne Sub-Tags)
    2. Nested-Pass: Aeussere Tags (bibl etc. die Sub-Tags enthalten)

    Dual-Attribut-Strategie:
    - ref="GND:{id}" wenn GND-ID im Entity Index vorhanden
    - corresp="#zbz-p.N" als interne Referenz (immer)
    """
    # Build lookup: surface text -> EntityRecord (resolved only)
    surface_to_rec: dict[str, EntityRecord] = {}
    for rec in store.get_resolved():
        for surface in rec.surfaces:
            surface_to_rec[surface.lower()] = rec

    def _resolve_dual_ref(text_only: str, tag_name: str) -> tuple[str | None, str | None]:
        """Loest einen Entity-Text in GND-Ref + interne ID auf.

        Returns:
            (gnd_ref, internal_id) z.B. ("GND:118557106", "#zbz-p.1")
        """
        gnd_ref = None
        internal_id = None

        # 1. Store-Lookup
        rec = surface_to_rec.get(text_only)
        if rec:
            index_id = getattr(rec, '_index_id', None)
            if index_id:
                internal_id = f"#{index_id}"
            if rec.gnd_id:
                gnd_ref = rec.gnd_id  # already "GND:..."

        # 2. Index-Fallback
        if index:
            entity_type = {"persName": "person", "orgName": "organization",
                           "placeName": "place", "bibl": "work"}.get(tag_name)
            entry = index.match(text_only, entity_type)
            if entry:
                if not internal_id:
                    internal_id = f"#{entry.xml_id}"
                if not gnd_ref and entry.gnd_id:
                    gnd_ref = entry.gnd_id  # already "GND:..."

        return gnd_ref, internal_id

    def _replace_ref(match):
        full_tag = match.group(0)
        tag_name = match.group(1)
        attrs = match.group(2) or ""
        content = match.group(3)

        # Entity-Text extrahieren (ohne Sub-Tags)
        text_only = re.sub(r'<[^>]+>', '', content).strip().lower()

        gnd_ref, internal_id = _resolve_dual_ref(text_only, tag_name)
        if not gnd_ref and not internal_id:
            return full_tag

        # Bestehende ref/corresp entfernen fuer sauberen Neuaufbau
        attrs = re.sub(r'\s*ref="[^"]*"', '', attrs)
        attrs = re.sub(r'\s*corresp="[^"]*"', '', attrs)

        # GND-Ref setzen (wenn vorhanden)
        if gnd_ref:
            attrs = f'{attrs} ref="{gnd_ref}"'

        # Interne ID immer als corresp setzen
        if internal_id:
            attrs = f'{attrs} corresp="{internal_id}"'

        return f"<{tag_name}{attrs}>{content}</{tag_name}>"

    # Pass 1: Leaf-Level Entity-Tags (kein Nesting im Content)
    leaf_pattern = re.compile(
        r'<(persName|orgName|placeName|name)(\s[^>]*)?>([^<]*)</\1>',
    )
    xml_text = leaf_pattern.sub(_replace_ref, xml_text)

    # Pass 2: Tags mit verschachteltem Content (bibl etc.)
    nested_pattern = re.compile(
        r'<(persName|orgName|placeName|bibl|name)(\s[^>]*)?>([^<]*(?:<(?!/\1>)[^<]*)*)</\1>',
        re.DOTALL,
    )
    xml_text = nested_pattern.sub(_replace_ref, xml_text)

    return xml_text


# ---------------------------------------------------------------------------
# Neue Entity-Tags einfuegen
# ---------------------------------------------------------------------------

def _mask_excluded_zones(xml_text: str) -> tuple[str, list[tuple[str, str]]]:
    """Maskiert Bereiche, in denen keine Entities annotiert werden duerfen.

    Editionsrichtlinien (E49):
    - Keine Entities in <figure>...</figure> (Bildunterschriften)
    - Keine Entities in <listBibl>...</listBibl> (Lexikonartikel-Bibliografie)
    """
    masks = []
    counter = 0
    for pattern in [
        re.compile(r'<figure\b[^>]*>.*?</figure>', re.DOTALL),
        re.compile(r'<listBibl\b[^>]*>.*?</listBibl>', re.DOTALL),
    ]:
        for match in pattern.finditer(xml_text):
            placeholder = f"\x01EXCL{counter}\x01"
            masks.append((placeholder, match.group(0)))
            counter += 1
        for placeholder, original in masks[-counter:] if counter else []:
            xml_text = xml_text.replace(original, placeholder, 1)
    return xml_text, masks


def _unmask_excluded_zones(xml_text: str, masks: list[tuple[str, str]]) -> str:
    """Stellt maskierte Bereiche wieder her."""
    for placeholder, original in masks:
        xml_text = xml_text.replace(placeholder, original)
    return xml_text


def inject_new_entities(xml_text: str, store: EntityStore) -> str:
    """Fuegt Entity-Tags fuer ungetaggte Mentions ein.

    Verwendet die bewaehrte Tag-aware Split + Placeholder Technik.
    Schliesst <figure> und <listBibl> Bereiche aus (E49).
    """
    # Ausschluss-Zonen maskieren
    xml_text, masks = _mask_excluded_zones(xml_text)
    # Nur resolved Entities mit hoeherem Count injizieren
    entities_to_inject = []
    for rec in store.entities.values():
        if not rec.is_resolved:
            continue
        for surface in rec.surfaces:
            entities_to_inject.append((surface, rec))

    if not entities_to_inject:
        return xml_text

    # Laengste zuerst (verhindert Partial Matches)
    entities_to_inject.sort(key=lambda x: len(x[0]), reverse=True)

    # Tag-aware Split: nur in Text-Teilen annotieren
    # Split an bestehenden Entity-Tags
    parts = ENTITY_TAG_PATTERN.split(xml_text)
    tags = ENTITY_TAG_PATTERN.findall(xml_text)

    # Nur in ungeraden Positionen (Text zwischen Tags) annotieren
    new_parts = []
    tag_idx = 0
    for i, part in enumerate(parts):
        if i > 0 and tag_idx < len(tags):
            new_parts.append(tags[tag_idx])
            tag_idx += 1

        # Nicht in XML-Tags annotieren
        if '<' in part and '>' in part:
            # Vorsicht: Teil koennte gemischt sein (Text + Tags)
            # Nur Text ausserhalb von Tags annotieren
            annotated = _annotate_text_segments(part, entities_to_inject)
            new_parts.append(annotated)
        else:
            annotated = _annotate_text_segments(part, entities_to_inject)
            new_parts.append(annotated)

    xml_text = "".join(new_parts)

    # Ausschluss-Zonen wiederherstellen
    xml_text = _unmask_excluded_zones(xml_text, masks)

    return xml_text


def _annotate_text_segments(
    text: str,
    entities: list[tuple[str, EntityRecord]],
) -> str:
    """Annotiert Entity-Mentions in einem Text-Segment.

    Verwendet Placeholder-Technik um verschachtelte Matches zu vermeiden.
    """
    placeholders = {}
    counter = 0

    for surface, rec in entities:
        tei_elem, ref_attr = ENTITY_TEI_MAP.get(rec.entity_type, ("name", "ref"))

        # Bevorzuge Index-ID (#zbz-p.N), Fallback: WD:Q... / GND:...
        index_id = getattr(rec, '_index_id', None)
        ref_val = f"#{index_id}" if index_id else rec.ref_value()

        if ref_val == "WD:unknown":
            continue

        # Tag aufbauen
        if rec.entity_type == "event":
            tag = f'<name type="event" {ref_attr}="{ref_val}">{surface}</name>'
        else:
            tag = f'<{tei_elem} {ref_attr}="{ref_val}">{surface}</{tei_elem}>'

        placeholder = f"\x00ENT{counter}\x00"
        placeholders[placeholder] = tag
        counter += 1

        # Wortgrenzen-Match, nicht in XML-Tags
        pattern = r'(?<![<\w])' + re.escape(surface) + r'(?![>\w])'
        text = re.sub(pattern, placeholder, text)

    # Placeholders einsetzen
    for ph, tag in placeholders.items():
        text = text.replace(ph, tag)

    return text


# ---------------------------------------------------------------------------
# Dokument-Verarbeitung
# ---------------------------------------------------------------------------

def process_document(
    doc_id: str,
    force: bool = False,
    validate: bool = False,
) -> dict:
    """Injiziert Entities in ein TEI-Dokument.

    Returns:
        Manifest dict.
    """
    start = time.time()

    # Source TEI laden
    source_path = TEI_UNIFIED_DIR / doc_id / f"{doc_id}_final.xml"
    if not source_path.exists():
        print(f"  {doc_id}: kein unified TEI gefunden ({source_path})")
        return {"doc_id": doc_id, "error": "no_source"}

    # Output pruefen
    out_dir = TEI_NER_DIR / doc_id
    out_path = out_dir / f"{doc_id}_final.xml"
    if out_path.exists() and not force:
        print(f"  {doc_id}: bereits vorhanden (--force zum Ueberschreiben)")
        return {"doc_id": doc_id, "skipped": True}

    # Entity Store + Index laden
    store = EntityStore.load(doc_id)
    if not store.entities:
        print(f"  {doc_id}: keine Entities, kopiere Original")
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path.write_text(
            source_path.read_text(encoding="utf-8"), encoding="utf-8"
        )
        return {"doc_id": doc_id, "entities_injected": 0}

    # Index-IDs (#zbz-p.N) als primaere Refs zuordnen
    index = EntityIndex()
    index.load_all()
    for rec in store.entities.values():
        entry = index.match_normalized(rec.normalized, rec.entity_type)
        if entry:
            rec._index_id = entry.xml_id  # fuer ref_value_with_index()

    # TEI lesen
    xml_text = source_path.read_text(encoding="utf-8")

    # Entity-Counts vorher
    before_counts = {
        "persName": len(re.findall(r'<persName\b', xml_text)),
        "orgName": len(re.findall(r'<orgName\b', xml_text)),
        "placeName": len(re.findall(r'<placeName\b', xml_text)),
        "bibl": len(re.findall(r'<bibl\b', xml_text)),
    }

    # Phase 1: Bestehende Refs updaten (GND -> Index-Ref)
    xml_text = update_existing_refs(xml_text, store, index)

    # Phase 2: Neue Entity-Tags einfuegen
    xml_text = inject_new_entities(xml_text, store)

    # Entity-Counts nachher
    after_counts = {
        "persName": len(re.findall(r'<persName\b', xml_text)),
        "orgName": len(re.findall(r'<orgName\b', xml_text)),
        "placeName": len(re.findall(r'<placeName\b', xml_text)),
        "bibl": len(re.findall(r'<bibl\b', xml_text)),
    }

    # Speichern
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path.write_text(xml_text, encoding="utf-8")

    # Validation (optional)
    validation_result = None
    if validate:
        try:
            from scripts.tei.tei_validator import validate_tei_file
            validation_result = validate_tei_file(out_path)
            status = "VALID" if validation_result["valid"] else "INVALID"
            print(f"    Validation: {status}")
        except ImportError:
            print("    WARNUNG: tei_validator nicht verfuegbar")

    elapsed = round(time.time() - start, 1)

    # Manifest
    manifest = {
        "doc_id": doc_id,
        "entities_total": len(store.entities),
        "entities_resolved": len(store.get_resolved()),
        "before": before_counts,
        "after": after_counts,
        "added": {k: after_counts[k] - before_counts.get(k, 0)
                  for k in after_counts},
        "elapsed_seconds": elapsed,
        "validation": validation_result,
    }

    manifest_path = out_dir / f"{doc_id}_manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    refs_updated = sum(1 for r in store.get_resolved()
                       if r.ref_value().startswith("WD:"))
    total_added = sum(after_counts[k] - before_counts.get(k, 0)
                      for k in after_counts)

    print(f"  {doc_id}: {refs_updated} refs updated, "
          f"{total_added} tags added, {elapsed}s")

    return manifest


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="TEI Entity Injection (NER -> TEI)"
    )
    parser.add_argument("--doc", help="Einzelnes Dokument")
    parser.add_argument("--all", action="store_true",
                        help="Alle Dokumente mit Entities")
    parser.add_argument("--force", action="store_true",
                        help="Bestehende ueberschreiben")
    parser.add_argument("--validate", action="store_true",
                        help="RelaxNG-Validierung")
    parser.add_argument("--dry-run", action="store_true",
                        help="Nur anzeigen, nicht schreiben")
    args = parser.parse_args()

    if args.doc:
        doc_ids = [args.doc]
    elif args.all:
        doc_ids = discover_entity_docs()
        if not doc_ids:
            print("Keine Entity-Daten. Zuerst ner_extract ausfuehren.")
            return
    else:
        parser.print_help()
        return

    print(f"TEI Entity Injection: {len(doc_ids)} Dokumente")
    start = time.time()

    for i, doc_id in enumerate(doc_ids, 1):
        print(f"[{i}/{len(doc_ids)}] {doc_id}:")
        process_document(doc_id, force=args.force, validate=args.validate)

    elapsed = round(time.time() - start, 1)
    print(f"\nFertig in {elapsed}s.")


if __name__ == "__main__":
    main()
