---
type: knowledge
created: 2026-01-29
updated: 2026-05-25
tags: [zbz-ocr-tei, entities, ner, gnd, wikidata, entity-linking]
status: active
---

# Entitaeten (NER + Wikidata + GND)

Named Entity Recognition und Entity Linking im Hersch-Korpus.

**Strategie:** Dual-Attribut (E50, 2026-03-26). GND als primaere Referenz im TEI-Output
(wie Editionsrichtlinien), interne IDs (`zbz-p.N`) als Arbeits-Referenz in `corresp`.
Entity Index bleibt Single Source of Truth.

Implementierung: `scripts/ner/` (7 Module). Pipeline-Position: Stufe 5 in [pipeline.md](pipeline.md).

---

## Strategie

Index-Erstellung ist editorial zentral. Alle Personen, Organisationen, Orte und Werke werden
identifiziert und verlinkt. Grundregel: **Jede Erwaehnung wird verlinkt**, auch bei Wiederholung.

### Entity-Typen (6)

| Typ | TEI-Element | ref (GND) | corresp (intern) | Beispiel |
|---|---|---|---|---|
| Person | `<persName>` | `ref="GND:118557106"` | `corresp="#zbz-p.1"` | `<persName ref="GND:118557106" corresp="#zbz-p.1">Karl Jaspers</persName>` |
| Organisation | `<orgName>` | `ref="GND:1010450-1"` | `corresp="#zbz-o.5"` | `<orgName ref="GND:1010450-1" corresp="#zbz-o.5">UNESCO</orgName>` |
| Ort | `<placeName>` | `ref="GND:..."` | `corresp="#zbz-l.1"` | `<placeName corresp="#zbz-l.1">Paris</placeName>` |
| Werk | `<bibl>` | `ref="GND:..."` | `corresp="#zbz-w.3"` | `<bibl ref="GND:1088036961" corresp="#zbz-w.3">Philosophie</bibl>` |
| Event | `<name type="event">` | `ref="GND:..."` | `corresp="#zbz-e.1"` | `<name type="event" corresp="#zbz-e.1">Mai 68</name>` |
| Datum | `<date>` | — | — | `<date when="1947">1947</date>` |

### ID-Hierarchie (E50)

1. **GND-ID** (`ref`): primaere Referenz im TEI, nur wenn im Entity Index vorhanden
2. **Interne ID** (`corresp`): immer vorhanden, verweist auf Entity Index
3. **Wikidata QID**: im Entity Index gespeichert (corresp-Attribut), nicht im TEI-Attribut

### Entity Index (TEI-XML)

```
data/entities/
  person_index.xml    # <listPerson> mit <person xml:id="zbz-p.1" corresp="https://www.wikidata.org/wiki/Q123559">
  org_index.xml       # <listOrg>
  place_index.xml     # <listPlace>
  work_index.xml      # <listBibl>
```

Jeder Eintrag hat: `xml:id` (interne ID), optionales `corresp` (Wikidata-URL),
`type="main"` + `type="variant"` Namensvarianten fuer String-Matching, ggf. `<idno type="GND">`.

### Ausnahmen (Editionsrichtlinien)

- Keine Annotation in Bildunterschriften (`<figure>/<p>`)
- Keine Annotation in `<div type="bibliography">/<listBibl>` (Lexikonartikel)
- Adjektivierte Personennamen werden nicht annotiert (`kantien`, `hegelsche`)
- "Nested" Tagging vermeiden

### Pipeline-Position

```
OCR → TEI-Basisstruktur → NER → Wikidata/GND-Lookup → Injection → Validierung → Curation
```

Post-hoc-Ansatz (E34): TEI ohne GND-Verknuepfung erzeugen, NER separat, Wikidata-Reconciliation per
API (kein LLM fuer IDs — verhindert Halluzinationen). Manuelle Pruefung im Pipeline-Viewer
(Edit-Modus, siehe [viewer.md](viewer.md)).

### Herausforderungen

1. Mehrsprachigkeit (66% FR) — unterschiedliche Namenskonventionen
2. Historische Varianten (J. Hersch vs. Jeanne Hersch)
3. Kontextabhaengigkeit ("Jaspers" als Person vs. Werk)
4. Pronomen werden nicht verlinkt

---

## Production-Stand (April 2026)

Single Source of Truth fuer die Entity-Zahlen — regenerierbar via
`python -m scripts.ner.entity_index --stats`. Andere Docs verweisen hierher,
statt diese Zahlen zu wiederholen.

| Komponente | Wert |
|---|---|
| NER-Extraction | 285 Docs, 11.685 unique Entities, 26.197 Mentions |
| Typ-Verteilung | person 36.7%, place 22.3%, date 15.0%, org 13.6%, work 10.8%, event 1.6% |
| Entity Index | 4.504 Eintraege |
| Wikidata-Linking | 2.101/4.504 (47%) |
| GND-IDs im Index | 958 (21.7%) |
| TEI Entity Injection | 285/285 mit Dual-Attribut (`ref="GND:..."` + `corresp="#zbz-..."`) |
| NER-Evaluation | HTML-Report `output/ner_report.html`; FR 45%, DE 38%, EN 32% Recall |

### Linking-Quote pro Typ

| Typ | Total | Linked | Quote | Hauptproblem |
|---|---|---|---|---|
| Person | 2.146 | 1.068 | 50% | Nischenautoren, OCR-Namensvarianten |
| Organisation | 781 | 319 | 41% | franzoesische Universitaeten, Verlage |
| Ort | 723 | 455 | 63% | Duplikate (3x "Suisse"), Ortsteile |
| Werk | 854 | 259 | 30% | Hersch-Eigenwerke, franzoesische Titel |
| **Gesamt** | **4.504** | **2.101** | **47%** | |

**Ziel:** >60% Linking (Works >45%). Kein 100%-Anspruch — Entities ohne Wikidata-Eintrag bleiben
bewusst unverlinkt.

---

## Wikidata-Workflow

Konkrete Schritte zur Vervollstaendigung des Entity-Linkings. Grundlage:
`entity_index.py --diagnostics` (Stand 2026-03-29).

### Priorisierung (3 Kriterien)

1. **Mention-Frequenz** (primaer) — Top-20 unverlinkte Entities pro Typ decken typischerweise 30-50% der fehlenden Mentions
2. **Dokument-Breite** (sekundaer) — Entity in 15 Docs editorial wichtiger als 50 Mentions in einem Doc; `docs_count` im CSV
3. **Typ-Dringlichkeit** — Works zuerst (niedrigste Quote), dann Organisations, Persons, Places

Der CSV-Export ist bereits nach Typ und Mention-Count sortiert — Works zuerst bearbeiten.

### Matching-Schritt (automatisiert)

Kein SPARQL. `wikidata_linker.py` arbeitet sequentiell pro Entity:

1. **Wikidata Search API** (`wbsearchentities`) in 3 Sprachen (fra, deu, eng)
2. **Label-Match** case-insensitive zwischen Suchergebnis und Entity-Name
3. **Typ-Verifikation** ueber P31 (instance of: Person=Q5, Ort=Q515, etc.)
4. **GND-Extraktion** aus P227
5. **Konfidenz-Zuweisung:**
   - 1.0 — exakter Label-Match + P31 verifiziert
   - 0.8 — Top-Kandidat + P31 verifiziert
   - 0.6 — Top-Kandidat ohne Typ-Verifikation
   - kein Match → unverlinkt

### Batch-Ausfuehrung

```bash
# Nur Docs mit unaufgeloesten Entities (inkrementell, Cache-basiert)
python -m scripts.ner.wikidata_linker --all --resume

# Statistiken pruefen
python -m scripts.ner.wikidata_linker --stats
```

Erwartete Laufzeit: ~2h bei 2.403 unverlinkten Entities (1 req/s Rate-Limit). Cache reduziert
Re-Runs auf Minuten. Erwartetes Ergebnis: 30-40% der aktuell unverlinkten Entities werden
automatisch aufgeloest (v.a. Personen und Orte). Works bleiben groesstenteils unaufgeloest.

### Manueller Review

```bash
# Diagnostik + CSV nach Batch-Run aktualisieren
python -m scripts.ner.entity_index --diagnostics --export-csv output/evaluation/entity_review.csv
```

Die CSV (`entity_review.csv`) enthaelt pro Eintrag: `xml_id`, `type`, `main_name`, `variants`,
`mention_count`, `docs_count`, `wikidata_status`, `wikidata_qid`, `gnd_id`.

**Rollenverteilung:**

| Rolle | Aufgabe | Werkzeug |
|---|---|---|
| Editorin (ZBZ) | Fachentscheidung: Ist "Mensch" Person oder Stoppwort? Ist "Schweizer Bundesrat" die richtige Wikidata-Entity? | CSV in Excel/Calc |
| Entwickler (DHCraft) | Technische Korrekturen: Duplikate mergen, Stoppwoerter aufnehmen, GND-IDs nachtragen | `entity_index.py` + `wikidata_linker.py` |

**Ablauf:**

1. CSV oeffnen, `wikidata_status=unlinked` filtern, nach `mention_count` absteigend sortieren
2. Pro Entity entscheiden:
   - Stoppwort? (z.B. "Mensch" als Person getaggt) → fuer Stoppwort-Liste markieren
   - Duplikat? (3x "Suisse" als separate Orte) → fuer Merge markieren
   - Korrekt unverlinkt? (existiert nicht auf Wikidata) → belassen
   - Verlinkbar? (Linker hat nur nicht getroffen) → QID manuell eintragen
3. Annotierte CSV zurueck an Entwickler
4. Korrekturen einspielen:
   - Stoppwoerter → `_ENTITY_STOPWORDS` in `tei_mapping_prompt.py`
   - Duplikate → manueller Merge im Entity Index
   - manuelle QIDs → in Entity Index eintragen, GND-Lookup automatisch

**Aufwand:**

| Schritt | Aufwand | Wer |
|---|---|---|
| Batch-Run | 2h (automatisch) | Entwickler |
| CSV-Review (Top-100) | 2-3h | Editorin |
| Korrekturen einspielen | 1h | Entwickler |
| Re-Injection in TEIs | 30min (automatisch) | Entwickler |

---

## Bekannte Probleme

### Hersch-Eigenwerke (Works 30% Linking)

"Temps alternes", "Ideologies et Realite", "L'etre et la forme" sind auf Wikidata nicht
oder unter anderem Titel eingetragen. Optionen:

- GND-IDs manuell recherchieren (DNB-Katalog)
- Interne ID (`zbz-w.N`) als einzige Referenz belassen
- langfristig: Wikidata-Eintraege fuer Hersch-Werke anlegen

### Duplikate im Index

3x "Suisse" (`zbz-l.720`, `zbz-l.723`, `zbz-l.713`) mit zusammen 685 Mentions. Ursache:
NER erzeugt separate Eintraege fuer identische Strings in verschiedenen Dokumenten.
Loesung: manueller Merge.

### Stoppwort-Kandidaten

"Mensch" (`zbz-p.1251`, 38 Mentions in 10 Docs) ist kein Personenname. Weitere Kandidaten
pruefen: Entities mit hoher Mention-Zahl aber niedrigem `docs_count` koennten Fehlextraktionen sein.

**Erweiterte Stopwort-Liste (E45, 20 Eintraege):** Mensch, Der Mensch, Wahl, Rolle, Angst,
Geist, Ursprung, Gott, Christ, Philosophie, Demokratie, Philosophen, Marxisten, Est, Homme,
Schweizer, Zuercher, Zahler, Zeit, Gesamtschule. Reassembly 32 Docs.

### Bekannte Hersch-Kontextentitaeten (Seeds)

| Person | GND | Relevanz |
|---|---|---|
| Karl Jaspers | 118557106 | Lehrer, haeufigste Referenz (90 Mentions) |
| Martin Heidegger | 118547798 | philosophischer Kontext |
| Hannah Arendt | 118502751 | Zeitgenossin |
| Jean-Paul Sartre | 118605895 | Existentialismus |
| UNESCO | (corporate) | Arbeitgeberin 1966-1968 |
| Bergson | 118509578 | 8 Mentions |
| Kierkegaard | 118562002 | 7 Mentions |

---

## Erfolgskriterien

| Metrik | Vor Workflow | Ziel nach Workflow |
|---|---|---|
| Gesamt-Linking | 47% | >60% |
| Person-Linking | 50% | >65% |
| Work-Linking | 30% | >45% |
| Stoppwoerter bereinigt | 0 | Top-10 Kandidaten geprueft |
| Duplikate aufgeloest | unbekannt | Top-5 Cluster gemergt |

---

## Verweise

- [pipeline.md §TEI-Mapping](pipeline.md) — Entity-Tagging-Regeln im TEI
- [viewer.md](viewer.md) — Entity-Highlighting im TEI-Renderer des Pipeline-Viewers
- [decisions.md](decisions.md) — E34, E35, E38, E50, O11, R3, R10
- Diagnostik: `python -m scripts.ner.entity_index --diagnostics`
- CSV-Export: `python -m scripts.ner.entity_index --diagnostics --export-csv output/evaluation/entity_review.csv`
- Batch-Linking: `python -m scripts.ner.wikidata_linker --all --resume`
