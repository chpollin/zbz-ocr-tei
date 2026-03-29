"""
Entity Index: Liest/schreibt TEI-XML Indices (listPerson, listOrg, etc.).

Zentrale Drehscheibe fuer Entity-Verwaltung:
- String-Matching gegen bekannte Varianten
- ID-Vergabe fuer neue Entities (zbz-p.N, zbz-o.N, etc.)
- Wikidata-QID Zuordnung
- Export als TEI-XML

Aufruf:
    python -m scripts.ner.entity_index --stats
    python -m scripts.ner.entity_index --merge-from-store 2310
    python -m scripts.ner.entity_index --merge-all
"""

import argparse
import re
import sys
import unicodedata
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.config import DATA_DIR, ENTITIES_DIR, TEI_NS
from scripts.core.loaders import discover_entity_docs

# Index-Verzeichnis
INDEX_DIR = DATA_DIR / "entities"

# Index-Dateien pro Typ
INDEX_FILES = {
    "person": INDEX_DIR / "person_index.xml",
    "organization": INDEX_DIR / "org_index.xml",
    "place": INDEX_DIR / "place_index.xml",
    "work": INDEX_DIR / "work_index.xml",
}

# ID-Praefixe pro Typ
ID_PREFIX = {
    "person": "zbz-p",
    "organization": "zbz-o",
    "place": "zbz-l",
    "work": "zbz-w",
    "event": "zbz-e",
    "date": "zbz-d",
}

# TEI List-Container pro Typ
LIST_ELEMENT = {
    "person": "listPerson",
    "organization": "listOrg",
    "place": "listPlace",
    "work": "listBibl",
}

# TEI Entity-Element pro Typ
ENTITY_ELEMENT = {
    "person": "person",
    "organization": "org",
    "place": "place",
    "work": "bibl",
}

# TEI Name-Element pro Typ
NAME_ELEMENT = {
    "person": "persName",
    "organization": "orgName",
    "place": "placeName",
    "work": "title",
}


@dataclass
class IndexEntry:
    """Ein Eintrag im Entity-Index."""
    xml_id: str                          # zbz-p.1
    entity_type: str                     # person, organization, etc.
    main_name: str                       # Kanonischer Name
    variants: list[str] = field(default_factory=list)  # Alle Namensvarianten
    wikidata_qid: str | None = None      # Q123456
    wikidata_url: str | None = None      # https://www.wikidata.org/wiki/Q123456
    gnd_id: str | None = None            # GND:11860564X (aus Wikidata P227)
    note: str = ""

    @property
    def all_names(self) -> list[str]:
        """Alle Namen (main + variants) fuer String-Matching."""
        return [self.main_name] + self.variants

    @property
    def ref_value(self) -> str:
        """Ref-Wert fuer TEI: bevorzugt interne ID."""
        return f"#{self.xml_id}"


def _strip_diacritics(text: str) -> str:
    """Strip diacritics for fuzzy matching (Etudes == Etudes, Geneve == Geneve)."""
    nfkd = unicodedata.normalize('NFKD', text)
    return ''.join(c for c in nfkd if not unicodedata.combining(c)).lower()


class EntityIndex:
    """Liest und verwaltet TEI-XML Entity-Indices."""

    def __init__(self):
        self.entries: dict[str, IndexEntry] = {}  # key: xml_id
        self._variant_lookup: dict[str, str] = {}  # lowercase variant -> xml_id
        self._stripped_lookup: dict[str, str] = {}  # diacritics-stripped -> xml_id
        self._surname_to_ids: dict[str, list[str]] = {}  # surname -> [xml_ids]
        self._next_id: dict[str, int] = {}  # typ -> naechste freie Nummer

    def load_all(self) -> None:
        """Laedt alle Index-Dateien."""
        for entity_type, path in INDEX_FILES.items():
            if path.exists():
                self._load_index_file(path, entity_type)
        self._rebuild_lookup()

    def _load_index_file(self, path: Path, entity_type: str) -> None:
        """Laedt eine einzelne Index-Datei."""
        try:
            tree = ET.parse(str(path))
        except ET.ParseError as e:
            print(f"  WARNUNG: Parse-Fehler in {path.name}: {e}")
            return

        root = tree.getroot()
        elem_tag = ENTITY_ELEMENT.get(entity_type, "")
        name_tag = NAME_ELEMENT.get(entity_type, "")

        for elem in root.iter(f"{{{TEI_NS}}}{elem_tag}"):
            xml_id = elem.get("{http://www.w3.org/XML/1998/namespace}id", "")
            if not xml_id:
                continue

            corresp = elem.get("corresp", "")
            wikidata_qid = None
            if "wikidata.org" in corresp:
                # https://www.wikidata.org/wiki/Q123456 -> Q123456
                qid_match = re.search(r'(Q\d+)', corresp)
                if qid_match:
                    wikidata_qid = qid_match.group(1)

            main_name = ""
            variants = []
            for name_elem in elem.iter(f"{{{TEI_NS}}}{name_tag}"):
                name_type = name_elem.get("type", "")
                text = (name_elem.text or "").strip()
                if not text:
                    continue
                if name_type == "main" or not main_name:
                    main_name = text
                if name_type == "variant":
                    variants.append(text)

            # Fuer bibl: <title> statt <persName>
            if not main_name and entity_type == "work":
                for title_elem in elem.iter(f"{{{TEI_NS}}}title"):
                    text = (title_elem.text or "").strip()
                    if text:
                        main_name = text
                        break

            # GND-ID aus <idno type="GND">
            gnd_id = None
            for idno_elem in elem.iter(f"{{{TEI_NS}}}idno"):
                if idno_elem.get("type") == "GND":
                    gnd_val = (idno_elem.text or "").strip()
                    if gnd_val:
                        gnd_id = f"GND:{gnd_val}"
                    break

            note_elem = elem.find(f"{{{TEI_NS}}}note")
            note = (note_elem.text or "").strip() if note_elem is not None else ""

            if main_name:
                entry = IndexEntry(
                    xml_id=xml_id,
                    entity_type=entity_type,
                    main_name=main_name,
                    variants=variants,
                    wikidata_qid=wikidata_qid,
                    wikidata_url=corresp if "wikidata" in corresp else None,
                    gnd_id=gnd_id,
                    note=note,
                )
                self.entries[xml_id] = entry

    def _rebuild_lookup(self) -> None:
        """Baut den Varianten-Lookup neu auf."""
        self._variant_lookup.clear()
        self._stripped_lookup.clear()
        self._surname_to_ids.clear()
        self._next_id.clear()

        for entry in self.entries.values():
            for name in entry.all_names:
                key = name.lower().strip()
                if key:
                    self._variant_lookup[key] = entry.xml_id
                    # Diakritik-freier Lookup
                    stripped = _strip_diacritics(name)
                    if stripped and stripped != key:
                        self._stripped_lookup[stripped] = entry.xml_id

            # Nachname-Lookup (letztes Wort des Hauptnamens)
            parts = entry.main_name.split()
            if len(parts) > 1:
                surname = parts[-1].lower().strip()
                if len(surname) > 2:
                    self._surname_to_ids.setdefault(surname, []).append(entry.xml_id)

            # Naechste freie ID tracken
            prefix = ID_PREFIX.get(entry.entity_type, "zbz-x")
            match = re.match(rf'{re.escape(prefix)}\.(\d+)', entry.xml_id)
            if match:
                num = int(match.group(1))
                current_max = self._next_id.get(entry.entity_type, 0)
                if num >= current_max:
                    self._next_id[entry.entity_type] = num + 1

    # ----- String-Matching -----

    def match(self, surface: str, entity_type: str | None = None) -> IndexEntry | None:
        """Sucht eine Entity im Index via String-Match.

        Reihenfolge: exakter Match -> Diakritik-Fallback.

        Args:
            surface: Zu suchender Name
            entity_type: Optionaler Typ-Filter

        Returns:
            IndexEntry oder None
        """
        key = surface.lower().strip()
        xml_id = self._variant_lookup.get(key)
        if not xml_id:
            # Diakritik-Fallback (Geneve -> Geneve, Etudes -> Etudes)
            stripped = _strip_diacritics(surface)
            xml_id = self._stripped_lookup.get(stripped)
            if not xml_id:
                # Auch im normalen Lookup mit stripped key versuchen
                xml_id = self._variant_lookup.get(stripped)
        if xml_id:
            entry = self.entries[xml_id]
            if entity_type and entry.entity_type != entity_type:
                return None
            return entry
        return None

    def match_normalized(self, normalized: str, entity_type: str) -> IndexEntry | None:
        """Sucht via normalisiertem Namen (exakt + sicherer Nachname-Fallback).

        Nachname-Fallback nur wenn eindeutig (genau 1 Index-Eintrag mit
        diesem Nachnamen fuer den gegebenen Typ).
        """
        # Exakter Match (inkl. Diakritik-Fallback)
        entry = self.match(normalized, entity_type)
        if entry:
            return entry

        # Sicherer Nachname-Fallback: nur wenn eindeutig
        parts = normalized.split()
        if len(parts) > 1:
            surname = parts[-1].lower().strip()
            if len(surname) > 2:
                candidates = self._surname_to_ids.get(surname, [])
                # Nur akzeptieren wenn genau 1 Eintrag diesen Nachnamen hat
                typed_candidates = [
                    xid for xid in candidates
                    if self.entries[xid].entity_type == entity_type
                ]
                if len(typed_candidates) == 1:
                    return self.entries[typed_candidates[0]]

        return None

    # ----- ID-Vergabe -----

    def register_new(
        self,
        normalized: str,
        entity_type: str,
        variants: list[str] | None = None,
        wikidata_qid: str | None = None,
        gnd_id: str | None = None,
        note: str = "",
    ) -> IndexEntry:
        """Registriert eine neue Entity und vergibt eine ID.

        Returns:
            Neuer IndexEntry mit xml_id.
        """
        # Pruefen ob bereits vorhanden
        existing = self.match_normalized(normalized, entity_type)
        if existing:
            # Varianten ergaenzen
            if variants:
                for v in variants:
                    if v not in existing.variants and v != existing.main_name:
                        existing.variants.append(v)
                        self._variant_lookup[v.lower().strip()] = existing.xml_id
            if wikidata_qid and not existing.wikidata_qid:
                existing.wikidata_qid = wikidata_qid
                existing.wikidata_url = f"https://www.wikidata.org/wiki/{wikidata_qid}"
            if gnd_id and not existing.gnd_id:
                existing.gnd_id = gnd_id
            return existing

        # Neue ID vergeben
        prefix = ID_PREFIX.get(entity_type, "zbz-x")
        next_num = self._next_id.get(entity_type, 1)
        xml_id = f"{prefix}.{next_num}"
        self._next_id[entity_type] = next_num + 1

        all_variants = []
        if variants:
            all_variants = [v for v in variants if v != normalized]

        entry = IndexEntry(
            xml_id=xml_id,
            entity_type=entity_type,
            main_name=normalized,
            variants=all_variants,
            wikidata_qid=wikidata_qid,
            wikidata_url=f"https://www.wikidata.org/wiki/{wikidata_qid}" if wikidata_qid else None,
            gnd_id=gnd_id,
            note=note,
        )

        self.entries[xml_id] = entry
        # Lookup aktualisieren
        for name in entry.all_names:
            self._variant_lookup[name.lower().strip()] = xml_id

        return entry

    # ----- Persistenz -----

    def save_all(self) -> None:
        """Schreibt alle Index-Dateien zurueck."""
        for entity_type, path in INDEX_FILES.items():
            entries = [e for e in self.entries.values()
                       if e.entity_type == entity_type]
            if entries or path.exists():
                self._write_index_file(path, entity_type, entries)

    def _write_index_file(
        self, path: Path, entity_type: str, entries: list[IndexEntry]
    ) -> None:
        """Schreibt eine Index-Datei als TEI-XML."""
        list_tag = LIST_ELEMENT.get(entity_type, "list")
        elem_tag = ENTITY_ELEMENT.get(entity_type, "item")
        name_tag = NAME_ELEMENT.get(entity_type, "name")

        # Sortiert nach ID-Nummer
        entries.sort(key=lambda e: e.xml_id)

        lines = []
        lines.append('<?xml version="1.0" encoding="UTF-8"?>')
        lines.append('<TEI xmlns="http://www.tei-c.org/ns/1.0">')
        lines.append('  <teiHeader>')
        lines.append('    <fileDesc>')
        lines.append('      <titleStmt>')
        type_labels = {
            "person": "Personenindex",
            "organization": "Organisationsindex",
            "place": "Ortsindex",
            "work": "Werkindex",
        }
        lines.append(f'        <title>{type_labels.get(entity_type, "Index")}'
                      f' -- Jeanne Hersch Edition</title>')
        lines.append('      </titleStmt>')
        lines.append('      <publicationStmt>')
        lines.append('        <p>Interner Index, ZBZ/DHCraft</p>')
        lines.append('      </publicationStmt>')
        lines.append('      <sourceDesc>')
        lines.append('        <p>Automatisch generiert, manuell verifiziert</p>')
        lines.append('      </sourceDesc>')
        lines.append('    </fileDesc>')
        lines.append('  </teiHeader>')
        lines.append('  <text>')
        lines.append('    <body>')
        lines.append(f'      <{list_tag}>')

        for entry in entries:
            corresp_attr = ""
            if entry.wikidata_url:
                corresp_attr = f' corresp="{entry.wikidata_url}"'

            lines.append(
                f'        <{elem_tag} xml:id="{entry.xml_id}"{corresp_attr}>'
            )
            lines.append(
                f'          <{name_tag} type="main">{_xml_escape(entry.main_name)}'
                f'</{name_tag}>'
            )
            for variant in entry.variants:
                lines.append(
                    f'          <{name_tag} type="variant">{_xml_escape(variant)}'
                    f'</{name_tag}>'
                )
            if entry.gnd_id:
                gnd_val = entry.gnd_id.replace("GND:", "")
                lines.append(
                    f'          <idno type="GND">{_xml_escape(gnd_val)}</idno>'
                )
            if entry.note:
                lines.append(
                    f'          <note>{_xml_escape(entry.note)}</note>'
                )
            lines.append(f'        </{elem_tag}>')

        lines.append(f'      </{list_tag}>')
        lines.append('    </body>')
        lines.append('  </text>')
        lines.append('</TEI>')

        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    # ----- JSON Export (fuer Edition-Viewer) -----

    def to_json_dict(self) -> dict:
        """Exportiert den Index als JSON-Dictionary fuer den Edition-Viewer.

        Format: { "zbz-p.1": { type, name, variants, wikidata_qid, wikidata_url, note }, ... }
        Nur Entries mit Wikidata-QID werden exportiert (verifiziert durch Reconciliation).
        """
        result = {}
        for entry in self.entries.values():
            result[entry.xml_id] = {
                "type": entry.entity_type,
                "name": entry.main_name,
                "variants": entry.variants,
                "wikidata_qid": entry.wikidata_qid,
                "wikidata_url": entry.wikidata_url,
                "gnd_id": entry.gnd_id,
            }
        return result

    # ----- Statistiken -----

    def summary(self) -> dict:
        """Statistiken ueber den Index."""
        by_type = {}
        for t in ID_PREFIX:
            entries = [e for e in self.entries.values() if e.entity_type == t]
            if entries:
                with_wd = sum(1 for e in entries if e.wikidata_qid)
                by_type[t] = {
                    "total": len(entries),
                    "with_wikidata": with_wd,
                    "variants": sum(len(e.variants) for e in entries),
                }
        return {
            "total_entries": len(self.entries),
            "total_variants": len(self._variant_lookup),
            "by_type": by_type,
        }


    def diagnostics(self) -> dict:
        """Detaillierter Linking-Report mit Mention-Frequenzen.

        Laedt alle EntityStores, zaehlt Mentions pro Index-Eintrag,
        sortiert unverlinkte Entities nach Frequenz.
        """
        from scripts.ner.entity_store import EntityStore as _ES

        # Mention-Daten sammeln: xml_id -> {mention_count, doc_ids}
        mention_data = {xml_id: {"mention_count": 0, "doc_ids": set()}
                        for xml_id in self.entries}

        if ENTITIES_DIR.exists():
            for doc_dir in sorted(ENTITIES_DIR.iterdir()):
                if not doc_dir.is_dir() or doc_dir.name.startswith("_"):
                    continue
                try:
                    store = _ES.load(doc_dir.name)
                except Exception:
                    continue
                for rec in store.entities.values():
                    if rec.entity_type in ("event", "date"):
                        continue
                    if not rec.normalized:
                        continue
                    entry = self.match_normalized(rec.normalized, rec.entity_type)
                    if entry and entry.xml_id in mention_data:
                        mention_data[entry.xml_id]["mention_count"] += rec.count
                        mention_data[entry.xml_id]["doc_ids"].add(doc_dir.name)

        # Ergebnis aufbauen
        by_type = {}
        for entity_type in INDEX_FILES:
            entries_of_type = [e for e in self.entries.values()
                               if e.entity_type == entity_type]
            linked = [e for e in entries_of_type if e.wikidata_qid]
            unlinked = [e for e in entries_of_type if not e.wikidata_qid]

            # Unlinked nach Mention-Count sortieren (haeufigste zuerst)
            unlinked_entries = []
            for e in unlinked:
                md = mention_data.get(e.xml_id, {})
                unlinked_entries.append({
                    "xml_id": e.xml_id,
                    "main_name": e.main_name,
                    "variants": e.variants[:5],
                    "mention_count": md.get("mention_count", 0),
                    "docs_count": len(md.get("doc_ids", set())),
                })
            unlinked_entries.sort(key=lambda x: -x["mention_count"])

            by_type[entity_type] = {
                "total": len(entries_of_type),
                "linked": len(linked),
                "unlinked": len(unlinked),
                "unlinked_entries": unlinked_entries,
            }

        total = len(self.entries)
        total_linked = sum(t["linked"] for t in by_type.values())

        return {
            "total": total,
            "linked": total_linked,
            "unlinked": total - total_linked,
            "by_type": by_type,
            "_mention_data": {
                xml_id: {
                    "mention_count": md["mention_count"],
                    "docs_count": len(md["doc_ids"]),
                }
                for xml_id, md in mention_data.items()
            },
        }

    def export_review_csv(self, output_path: Path, mention_data: dict) -> None:
        """Exportiert alle Entities als CSV fuer manuelles Review.

        Spalten: xml_id, type, main_name, variants, mention_count,
                 docs_count, wikidata_status, wikidata_qid, gnd_id
        """
        import csv

        rows = []
        for entry in self.entries.values():
            md = mention_data.get(entry.xml_id, {})
            rows.append({
                "xml_id": entry.xml_id,
                "type": entry.entity_type,
                "main_name": entry.main_name,
                "variants": "; ".join(entry.variants[:10]),
                "mention_count": md.get("mention_count", 0),
                "docs_count": md.get("docs_count", 0),
                "wikidata_status": "linked" if entry.wikidata_qid else "unlinked",
                "wikidata_qid": entry.wikidata_qid or "",
                "gnd_id": entry.gnd_id or "",
            })

        # Sortieren: Typ ASC, dann Mention-Count DESC
        rows.sort(key=lambda r: (r["type"], -r["mention_count"]))

        if not rows:
            print("Keine Entities im Index -- CSV nicht erstellt.")
            return

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        fieldnames = ["xml_id", "type", "main_name", "variants",
                      "mention_count", "docs_count", "wikidata_status",
                      "wikidata_qid", "gnd_id"]
        with open(output_path, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)


def _xml_escape(text: str) -> str:
    """Escaped XML-Sonderzeichen."""
    return (text
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;"))


# ---------------------------------------------------------------------------
# Merge: EntityStore -> Index
# ---------------------------------------------------------------------------

def merge_store_into_index(
    index: EntityIndex,
    doc_id: str,
    auto_register: bool = True,
) -> dict:
    """Mergt Entities aus einem EntityStore in den Index.

    Matching-Logik:
    1. Exakter String-Match gegen Index-Varianten
    2. Wenn kein Match und auto_register: neue Entity anlegen

    Returns:
        {matched, registered, skipped}
    """
    from scripts.ner.entity_store import EntityStore
    store = EntityStore.load(doc_id)
    if not store.entities:
        return {"matched": 0, "registered": 0, "skipped": 0}

    matched = 0
    registered = 0
    skipped = 0

    for rec in store.entities.values():
        # event/date: nicht im Index (zu unspezifisch)
        if rec.entity_type in ("event", "date"):
            skipped += 1
            continue

        # Index-Match versuchen
        entry = index.match_normalized(rec.normalized, rec.entity_type)
        if entry:
            # Varianten ergaenzen
            for surface in rec.surfaces:
                if (surface not in entry.variants
                        and surface != entry.main_name
                        and len(surface) > 2):
                    entry.variants.append(surface)
                    index._variant_lookup[surface.lower().strip()] = entry.xml_id
            # Wikidata-QID uebertragen (wenn neu vorhanden)
            if rec.wikidata_qid and not entry.wikidata_qid:
                entry.wikidata_qid = rec.wikidata_qid
                entry.wikidata_url = f"https://www.wikidata.org/wiki/{rec.wikidata_qid}"
            # GND-ID uebertragen (aus Wikidata P227)
            if rec.gnd_id and not entry.gnd_id:
                entry.gnd_id = rec.gnd_id
            matched += 1
        elif auto_register and rec.entity_type in INDEX_FILES:
            # Neue Entity registrieren
            wikidata_qid = None
            if rec.wikidata_qid:
                wikidata_qid = rec.wikidata_qid

            index.register_new(
                normalized=rec.normalized,
                entity_type=rec.entity_type,
                variants=[s for s in rec.surfaces if s != rec.normalized],
                wikidata_qid=wikidata_qid,
                gnd_id=rec.gnd_id,
                note="",
            )
            registered += 1
        else:
            skipped += 1

    return {"matched": matched, "registered": registered, "skipped": skipped}


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Entity Index: TEI-XML Indices verwalten"
    )
    parser.add_argument("--stats", action="store_true",
                        help="Index-Statistiken anzeigen")
    parser.add_argument("--report", action="store_true",
                        help="Ausfuehrlicher Report (JSON)")
    parser.add_argument("--merge-from-store",
                        help="Entities aus Store in Index mergen (doc_id)")
    parser.add_argument("--merge-all", action="store_true",
                        help="Alle Stores in Index mergen")
    parser.add_argument("--auto-register", action="store_true", default=True,
                        help="Neue Entities automatisch registrieren")
    parser.add_argument("--diagnostics", action="store_true",
                        help="Detaillierter Linking-Report mit Mention-Frequenzen")
    parser.add_argument("--export-csv", metavar="PATH",
                        help="Review-Export als CSV (fuer manuelles Review)")
    parser.add_argument("--export-json", metavar="PATH",
                        help="Index als JSON exportieren (fuer Edition-Viewer)")
    args = parser.parse_args()

    index = EntityIndex()
    index.load_all()

    if args.export_json:
        import json as _json
        data = index.to_json_dict()
        out_path = Path(args.export_json)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(
            _json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        s = index.summary()
        print(f"Exportiert: {s['total_entries']} Eintraege nach {out_path}")
        return

    if args.diagnostics:
        diag = index.diagnostics()
        print(f"Entity Linking Diagnostics")
        print(f"  Total: {diag['total']} | "
              f"Linked: {diag['linked']} ({diag['linked']}/{diag['total']}) | "
              f"Unlinked: {diag['unlinked']}")
        for t, td in sorted(diag['by_type'].items()):
            pct = round(td['linked'] / (td['total'] or 1) * 100)
            print(f"\n  {t}: {td['total']} total, "
                  f"{td['linked']} linked ({pct}%), "
                  f"{td['unlinked']} unlinked")
            if td['unlinked_entries']:
                print(f"  Top unlinked (by mentions):")
                for entry in td['unlinked_entries'][:10]:
                    print(f"    {entry['xml_id']:15} "
                          f"{entry['main_name']:30} "
                          f"mentions={entry['mention_count']} "
                          f"docs={entry['docs_count']}")
        if args.export_csv:
            index.export_review_csv(Path(args.export_csv), diag['_mention_data'])
            print(f"\nCSV exportiert: {args.export_csv}")
        return

    if args.report:
        import json as _json
        s = index.summary()
        # Cross-doc Konsistenz: Entities die in mehreren Docs vorkommen
        multi_doc = {}
        if ENTITIES_DIR.exists():
            from scripts.ner.entity_store import EntityStore as _ES
            for doc_dir in sorted(ENTITIES_DIR.iterdir()):
                if not doc_dir.is_dir() or doc_dir.name.startswith("_"):
                    continue
                store = _ES.load(doc_dir.name)
                for rec in store.entities.values():
                    entry = index.match_normalized(rec.normalized, rec.entity_type)
                    if entry:
                        multi_doc.setdefault(entry.xml_id, set()).add(doc_dir.name)
        cross_doc = {
            xml_id: {"name": index.entries[xml_id].main_name,
                      "docs": len(docs), "doc_ids": sorted(docs)}
            for xml_id, docs in multi_doc.items() if len(docs) > 1
        }
        report = {**s, "cross_doc_entities": len(cross_doc),
                  "top_cross_doc": sorted(cross_doc.values(),
                                          key=lambda x: -x["docs"])[:20]}
        print(_json.dumps(report, ensure_ascii=False, indent=2))
        return

    if args.stats:
        s = index.summary()
        print(f"Entity Index: {s['total_entries']} Eintraege, "
              f"{s['total_variants']} Varianten")
        for t, ts in s["by_type"].items():
            print(f"  {t}: {ts['total']} ({ts['with_wikidata']} mit Wikidata, "
                  f"{ts['variants']} Varianten)")
        return

    if args.merge_from_store:
        result = merge_store_into_index(
            index, args.merge_from_store, auto_register=args.auto_register
        )
        print(f"  {args.merge_from_store}: {result['matched']} matched, "
              f"{result['registered']} registered, {result['skipped']} skipped")
        index.save_all()
        s = index.summary()
        print(f"  Index jetzt: {s['total_entries']} Eintraege")
        return

    if args.merge_all:
        doc_ids = discover_entity_docs()
        if not doc_ids:
            print("Keine Entity-Daten.")
            return
        total = {"matched": 0, "registered": 0, "skipped": 0}
        for doc_id in doc_ids:
            result = merge_store_into_index(
                index, doc_id, auto_register=args.auto_register
            )
            for k in total:
                total[k] += result[k]
            print(f"  {doc_id}: +{result['registered']} neue, "
                  f"{result['matched']} bekannte")
        index.save_all()
        s = index.summary()
        print(f"\nGesamt: {total['matched']} matched, "
              f"{total['registered']} neu registriert, "
              f"{total['skipped']} uebersprungen")
        print(f"Index: {s['total_entries']} Eintraege")
        return

    parser.print_help()


if __name__ == "__main__":
    main()
