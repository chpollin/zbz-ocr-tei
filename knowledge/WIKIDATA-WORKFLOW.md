---
type: knowledge
created: 2026-03-29
updated: 2026-03-29
tags: [zbz-ocr-tei, wikidata, entity-linking, workflow]
status: draft
---

# Wikidata-Linking-Workflow

Konkreter Workflow zur Vervollstaendigung des Entity-Linkings. Grundlage:
Diagnostik-Ergebnisse aus `entity_index.py --diagnostics` (Stand 2026-03-29).

**Abhaengigkeiten:** [GND-STRATEGIE](GND-STRATEGIE.md), [PLAN](PLAN.md) Phase 3

---

## Ausgangslage

| Typ | Total | Linked | Quote | Hauptproblem |
|-----|-------|--------|-------|--------------|
| Person | 2.146 | 1.068 | 50% | Nischenautoren, OCR-Namensvarianten |
| Organisation | 781 | 319 | 41% | Franzoesische Universitaeten, Verlage |
| Ort | 723 | 455 | 63% | Duplikate (3x "Suisse"), Ortsteile |
| Werk | 854 | 259 | 30% | Hersch-Eigenwerke, franzoesische Titel |
| **Gesamt** | **4.504** | **2.101** | **47%** | |

**Ziel:** >60% Linking (bei Works: >45%). Kein 100%-Anspruch -- Entities
ohne Wikidata-Eintrag bleiben bewusst unverlinkt.

---

## Priorisierung

Drei Kriterien, gewichtet:

### 1. Mention-Frequenz (primaer)

Entities mit vielen Mentions haben den groessten Effekt auf die
Editionsqualitaet. Die Top-20 unverlinkten Entities pro Typ decken
typischerweise 30-50% der fehlenden Mentions ab.

### 2. Dokument-Breite (sekundaer)

Eine Entity, die in 15 Dokumenten vorkommt, ist editorisch wichtiger
als eine mit 50 Mentions in einem einzigen Dokument. `docs_count` im
CSV-Export zeigt die Streuung.

### 3. Typ-Dringlichkeit

| Prioritaet | Typ | Begruendung |
|-------------|-----|-------------|
| 1 | Work | Niedrigste Quote (30%), Hersch-Eigenwerke sind Kernbestand |
| 2 | Organization | 41%, viele franzoesische Institutionen ohne Match |
| 3 | Person | 50%, aber hoehere absolute Zahl |
| 4 | Place | 63%, bereits gut; Hauptproblem sind Duplikate |

**Praktische Sortierung:** Der CSV-Export (`--export-csv`) ist bereits
nach Typ und Mention-Count sortiert. Works zuerst bearbeiten.

---

## Matching-Schritt (automatisiert)

Kein SPARQL. Der bestehende `wikidata_linker.py` arbeitet sequentiell:

### Ablauf pro Entity

1. **Wikidata Search API** (`wbsearchentities`): Suche nach `main_name`
   in drei Sprachen (fra, deu, eng).
2. **Label-Match**: Exakter Label-Vergleich zwischen Suchergebnis und
   Entity-Name (case-insensitive).
3. **Typ-Verifikation**: P31 (instance of) gegen erwarteten Typ pruefen
   (Person=Q5, Ort=Q515 etc.).
4. **GND-Extraktion**: P227 (GND-Identifier) aus Wikidata holen.
5. **Konfidenz-Zuweisung:**
   - 1.0: Exakter Label-Match + P31 verifiziert
   - 0.8: Top-Kandidat + P31 verifiziert
   - 0.6: Top-Kandidat ohne Typ-Verifikation
   - Kein Match: Entity bleibt unverlinkt

### Batch-Ausfuehrung

```bash
# Nur Docs mit unaufgeloesten Entities (inkrementell, Cache-basiert)
python -m scripts.ner.wikidata_linker --all --resume

# Statistiken pruefen
python -m scripts.ner.wikidata_linker --stats
```

**Erwartete Laufzeit:** ~2h bei 2.403 unverlinkten Entities (1 req/s
Wikidata Rate Limit). Cache reduziert Re-Runs auf Minuten.

**Erwartetes Ergebnis:** Schaetzungsweise 30-40% der aktuell
unverlinkten Entities werden automatisch aufgeloest (v.a. Personen und
Orte). Works bleiben groesstenteils unaufgeloest (Wikidata hat wenige
Hersch-spezifische Werke).

---

## Manueller Review-Schritt

### Vorbereitung

```bash
# Diagnostik + CSV nach Batch-Run aktualisieren
python -m scripts.ner.entity_index --diagnostics --export-csv output/evaluation/entity_review.csv
```

### Review-Material

Die CSV-Datei (`entity_review.csv`) enthaelt pro Zeile:

| Spalte | Inhalt |
|--------|--------|
| xml_id | Interne ID (zbz-p.42) |
| type | person / organization / place / work |
| main_name | Kanonischer Name |
| variants | Namensvarianten (Semikolon-getrennt) |
| mention_count | Haeufigkeit im Gesamtkorpus |
| docs_count | In wievielen Dokumenten |
| wikidata_status | linked / unlinked |
| wikidata_qid | QID (wenn verlinkt) |
| gnd_id | GND-ID (wenn vorhanden) |

### Wer prueft was

| Rolle | Aufgabe | Werkzeug |
|-------|---------|----------|
| **Editorin (ZBZ)** | Fachliche Entscheidung: Ist "Mensch" eine Person oder ein Stoppwort? Ist "Schweizer Bundesrat" die richtige Wikidata-Entity? | CSV in Excel/Calc |
| **Entwickler (DHCraft)** | Technische Korrekturen: Duplikate zusammenfuehren, Stoppwoerter in die Liste aufnehmen, GND-IDs nachtragen | entity_index.py + wikidata_linker.py |

### Review-Ablauf

1. **CSV oeffnen**, nach `wikidata_status=unlinked` filtern, nach `mention_count` absteigend sortieren.
2. **Pro Entity entscheiden:**
   - **Stoppwort?** (z.B. "Mensch" als Person getaggt) → Markieren fuer Stoppwort-Liste
   - **Duplikat?** (z.B. 3x "Suisse" als separate Orte) → Markieren fuer Merge
   - **Korrekt unverlinkt** (existiert nicht auf Wikidata) → Belassen
   - **Verlinkbar** (existiert auf Wikidata, Linker hat nur nicht getroffen) → QID manuell eintragen
3. **Rueckmeldung** als annotierte CSV an Entwickler.
4. **Entwickler fuehrt Korrekturen durch:**
   - Stoppwoerter → `_ENTITY_STOPWORDS` in `tei_mapping_prompt.py`
   - Duplikate → Manueller Merge in Entity Index
   - Manuelle QIDs → In Entity Index eintragen, GND-Lookup automatisch

### Aufwand-Schaetzung

| Schritt | Aufwand | Wer |
|---------|---------|-----|
| Batch-Run | 2h (automatisch) | Entwickler |
| CSV Review (Top-100 Entities) | 2-3h | Editorin |
| Korrekturen einspielen | 1h | Entwickler |
| Re-Injection in TEIs | 30min (automatisch) | Entwickler |

---

## Bekannte Probleme

### Works (30% Linking)

Hersch-Eigenwerke ("Temps alternes", "Ideologies et Realite",
"L'etre et la forme") sind auf Wikidata nicht oder unter anderem Titel
eingetragen. Fuer diese Werke:

- GND-IDs manuell recherchieren (DNB-Katalog)
- Alternativ: Interne ID (zbz-w.N) als einzige Referenz belassen
- Langfristig: Wikidata-Eintraege fuer Hersch-Werke anlegen

### Duplikate im Index

3x "Suisse" (zbz-l.720, zbz-l.723, zbz-l.713) mit zusammen 685
Mentions. Ursache: NER-Extraktion erzeugt separate Eintraege fuer
identische Strings in verschiedenen Dokumenten. Loesung: Manueller
Merge auf einen Eintrag.

### Stoppwort-Kandidaten

"Mensch" (zbz-p.1251, 38 Mentions in 10 Docs) ist kein Personenname.
Weitere Kandidaten pruefen: Entities mit hoher Mention-Zahl aber
niedrigem docs_count koennten Fehlextraktionen sein.

---

## Erfolgskriterien

| Metrik | Vor Workflow | Ziel nach Workflow |
|--------|-------------|-------------------|
| Gesamt-Linking | 47% | >60% |
| Person-Linking | 50% | >65% |
| Work-Linking | 30% | >45% |
| Stoppwoerter bereinigt | 0 | Top-10 Kandidaten geprueft |
| Duplikate aufgeloest | Unbekannt | Top-5 Duplikat-Cluster gemergt |

---

## Referenzen

- Diagnostik: `python -m scripts.ner.entity_index --diagnostics`
- CSV-Export: `python -m scripts.ner.entity_index --diagnostics --export-csv output/evaluation/entity_review.csv`
- Batch-Linking: `python -m scripts.ner.wikidata_linker --all --resume`
- Entity-Strategie: [GND-STRATEGIE](GND-STRATEGIE.md)
- Implementierungsplan: [PLAN](PLAN.md) Phase 3

---

*Created: 2026-03-29*
