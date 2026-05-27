---
type: knowledge
created: 2026-02-18
updated: 2026-05-25
tags: [zbz-ocr-tei, projekt, korpus, zbz, workflow]
status: active
---

# Projekt

LLM-gestuetzte OCR- und TEI-Pipeline fuer den Nachlass Jeanne Hersch der Zentralbibliothek Zuerich.

---

## Auftrag

| Aspekt | Details |
|---|---|
| Auftraggeber | Zentralbibliothek Zuerich (ZBZ) |
| Auftragnehmer | DHCraft |
| Gegenstand | Automatisierte OCR + TEI-Annotation fuer den Hersch-Nachlass |
| Bestaetigung | 14.02.2026 |
| Honorar | unveraendert (Azure/Mistral keine Mehrkosten) |
| ZBZ-Kontakte | Elias Kreyenbuehl, Anouschka |
| Projektleitung | Christopher (DHCraft) |

Seit dem Abstimmungsmeeting (25.02.2026, E21) deckt zbz-ocr-tei den **vollstaendigen Pipeline-Weg** ab:
OCR + Layout + PAGE-XML + NER/GND + TEI-XML. ZBZ behaelt Transkribus parallel als zweite Quelle.

---

## Korpus

Korpus-Trichter (verifiziert via `python -m scripts.eval.corpus_audit`, Stand 2026-05-27):
**325 Masterfile-Texte → 289 digitalisiert → 286 als PDF geliefert → 285 mit finalem TEI.**
Die fruehere Zahl „289" ist der `digitalisiert`-Zaehler der Masterfile, nicht die Textmenge.
3 digitalisierte Texte ohne PDF-Lieferung: `1745`, `1750`, `1970`; 1 PDF ohne finales TEI: `10`.

| Aspekt | Wert | Einheit / Quelle |
|---|---|---|
| Masterfile-Texte | 325 | Text-Ebene (ZBZ-Masterfile) |
| als PDF geliefert | 286 | PDFs (`data/source/pdf/`) |
| produktiv (finales TEI) | 285 | `output/tei_final/` |
| Seiten bibliografisch | 7.186 | Masterfile (325 Texte) |
| Seiten physisch | 4.152 | gelieferte PDFs (pypdfium2) |
| Seiten verarbeitet | 4.117 OCR / 4.115 TEI-`<pb>` | Pipeline |
| Median pro Text | 6 Seiten | Masterfile |
| Maximum | 588 Seiten | Masterfile (biblio.) |
| Zeitraum | 1931–2010, Fokus 1970er/1980er (193 Texte) | Masterfile |

### Publikationsformen

Auf Text-Ebene laut Masterfile (n=325) — der katalogisierte Bestand, nicht die 286 verarbeiteten PDFs.

| Genre | Anzahl | Anteil |
|---|---|---|
| Journal articles | 159 | 49% |
| Edited volume contributions | 127 | 39% |
| Monographs | 38 | 12% |
| AV medium | 1 | <1% |

### Sprachverteilung

Auf Text-Ebene laut Masterfile (n=325). Geminis PDF-Klassifikation (`doc_metadata.json`, n=286) weicht ab und ueberschaetzt Mehrsprachigkeit — fuer Metadaten ist die Masterfile massgeblich.

| Sprache | Anzahl | Anteil |
|---|---|---|
| Franzoesisch | 215 | 66% |
| Deutsch | 98 | 30% |
| Englisch | 8 | 2% |
| Italienisch | 2 | 1% |
| Mehrsprachig fr/de | 1 | <1% |

Konsequenzen fuer die Pipeline: franzoesische Typografie (Guillemets, Akzente, Ligaturen,
Leerzeichen vor Interpunktion), franzoesische Trennregeln, Beispiele in Prompts ueberwiegend FR.

### Dokumenttypen A-D

| Typ | Layout | Strategie |
|---|---|---|
| **A** | einspaltig | OCR direkt (DeepSeek/Mistral) |
| **B** | zweispaltig (Journals, Lexika) | Layout-Analyse + OCR pro Region (Docling + Gemini) |
| **C** | Monografie (100+ Seiten) | OCR + Chunking, page-by-page Comparison (E16) |
| **D** | Spezial (historisch, Interview, Bildband) | Fall-zu-Fall |

### Pilotdateien (15 PDFs)

| Datei | Seiten | Sprache | Typ | Genre | Besonderheit |
|---|---|---|---|---|---|
| 2310.pdf | 3 | FR | A | Rezension | JSTOR-Cover |
| 1180.pdf | 8 | DE/FR | A | Jahresbericht | Titelseite |
| 130.pdf | 18 | FR | A | Zeitschriftenartikel | Cover-Page |
| 290.pdf | 5 | FR | A | Comptes Rendus | Essay |
| 1410.pdf | 6 | DE/FR | A | Beitrag | bilingual, teils zweispaltig |
| 1060.pdf | 8 | DE | A | Broschuere | Rede |
| 2530.pdf | 2 | FR | B | Artikel | zweispaltig |
| 890.pdf | 7 | DE | B | Lehrerzeitschrift | kleine Schrift |
| 3040.pdf | 9 | FR | B | Enzyklopaedie | Fussnoten |
| 40.pdf | 156 | FR | C | Roman | hs. Notizen |
| 1520.pdf | 142 | FR | C | Monografie | lang |
| 90.pdf | 6 | DE | D | hist. Druck | 1944 |
| 830.pdf | 2 | FR | D | Bildband | wenig Text |
| 1440.pdf | 5 | DE | D | Interview | Dialogformat |
| 1330.pdf | 6 | FR | D | Sammelband | Vorwort |

### Datenlieferung Feb 2026 (E23)

| Kategorie | Anzahl | Notiz |
|---|---|---|
| PDFs mit kompletter TEI-Annotation | 24 | + PAGE-XML-Export (Transkribus, Schema 2013, leer) |
| Komplette TEI-XMLs | 25 | 890 + 1520 haben XML aber PDF in anderem Ordner |
| PDFs ohne Annotation | 262 | noch nicht verarbeitet |

PAGE-XML-Detail: 24 Transkribus-Exports enthalten 302 Seiten total (alle leer — keine TextRegions). Bottleneck ist die TEI-Annotation — hier liefert die LLM-Pipeline den groessten Mehrwert.

---

## Status

Aktuelle Metriken (CER, Dateizahlen, Validierung): siehe Dashboard `docs/index.html`
und [quality.md](quality.md).

### Meilensteine

| # | Meilenstein | Erfolgskriterium | Status |
|---|---|---|---|
| M0 | Bildextraktion + QA-Viewer | Bilder + Viewer verfuegbar | Done |
| M1 | OCR validiert | >=93% Accuracy alle Typen | Done |
| M2 | Layout + PAGE-XML | Regionen + BBox + PAGE-XML alle Docs | Done |
| M3 | NER + Wikidata | Recall >70%, Linking >50% | Done (285 Docs, 11.685 Entities, 47% verlinkt) |
| M4 | TEI-XML | DTA-konform, schema-valide | Done (285/285 valide gegen `zbz_hersch.rng`) |
| M5 | Production Run | 285 Docs verarbeitet, fachliche QA | In Progress (285/285 generiert; Workflow-Status alle Stroeme `unverifiziert`, E66/E67; fachliche Kuration offen) |

### Komponenten-Status

| Komponente | Status | Details |
|---|---|---|
| Bildextraktion | Done | `scripts/edition/extract_pages.py` |
| OCR (Mistral + DeepSeek) | Done | `scripts/ocr/ocr_pipeline.py` |
| LLM-Postkorrektur (Haiku) | Done, optional (E17) | `scripts/ocr/llm_postprocess.py`, bei CER <5% schaedlich |
| Gemini OCR-Korrektur | Sample | `scripts/ocr/gemini_ocr_correct.py` (E29) |
| Layout (Docling) | Done | `scripts/layout/run_layout_analysis.py` |
| Layout-QA (Gemini) | Done | `--mode auto` (E25/E26/E31) |
| PAGE-XML Generator | Done | `page_xml_generator.py` + METS |
| Dokumentklassifikation | Done | `classify_docs.py` (E27) |
| NER Extraction | Done | 285 Docs, 11.685 Entities, 26.197 Mentions |
| Entity Index | Done | 4.504 Eintraege, 2.101 mit Wikidata/GND (47%) |
| Unified TEI Pipeline | Done | 285/285 schema-valide (E32) |
| TEI Validator | Done | RelaxNG + 8 Projektregeln + 14 Warnings |
| Workflow-Status pro Strom (E66/E67) | Done (Datenmodell) | ersetzt Agent-Screening; 285/285 `unverifiziert`, im Viewer setzbar, Provenienz im Manifest |
| Pipeline-Viewer (E56) | Done | `docs/viewer.html` Single-Page mit Layout- + Transkriptions-Editor, Persistenz via Download |
| Viewer Edition-Uplift (Mai 2026) | In Arbeit | OSD-Integration (E58), Mode-Edit-Toggle pro Panel (E60), Layout-Editor-Reichtum, geplant: UI-Verdichtung + Quality/Provenance-Drawer + complete-TEI + Export-Modul (E61). Plan: `~/.claude/plans/edition-uplift-three-pages.md` |
| Workflow + Provenance | Konzept dokumentiert | [workflow.md](workflow.md) beschreibt Datenfluss, Save-Mechanismus, Round-Trip, `_complete.xml`- und `provenance.json`-Konzept |
| Containerisierung | Pending | Dockerfile/Podman |
| CI/CD | Pending | GitLab Uni Zuerich |

---

## Kosten

| Posten | Betrag |
|---|---|
| Mistral OCR (Azure, 286 Docs) | 6-15 USD |
| LLM-Korrektur Haiku 4.5 | ~35 USD |
| Gemini Layout-QA + Detect | ~12 USD |
| Gemini TEI-Generation | ~17 USD (Flash Lite, E32) |
| Gemini NER | ~5-12 USD (Flash Lite, E34) |
| GPU-Cloud (optional) | ~10-20 USD |

Gesamtbudget bewegt sich knapp ueber 100 USD fuer den vollen Korpus.

---

## ZBZ-Workflow (Ist-Stand)

Kontextwissen ueber die manuelle Editionsproduktion bei ZBZ — relevant fuer Integrationspunkte.
Quelle: `WorkflowDiagramm_Hersch.pdf` (entfernt, vollstaendig uebernommen).

### Drei parallele Spuren

1. **Transkription:** Digitalisate → Transkribus → GitLab → Oxygen → GitLab
2. **Metadaten:** Digitalisate → Alma → Masterfile → Swisscovery → TEI-Header
3. **Korrekturschleife:** Oxygen → PDF → externe Reviewer → Oxygen

Das **Masterfile (Excel)** ist die zentrale Koordinationsstelle.

### Systeme

| System | Funktion | Format |
|---|---|---|
| Transkribus | OCR/HTR + Transkription | nicht standardisiert |
| Masterfile | Workflow + Status | Excel |
| GitLab | Versionierung TEI | XML |
| Oxygen | TEI-Markup + Transformation | XML |
| Alma | Katalogisierung + Metadaten | Katalogdaten |
| Swisscovery | Discovery | Katalogdaten |
| GND | Normdatenverknuepfung | IDs |

### Beobachtungen

- Fast alle Schritte sind manuell.
- Der Transkribus-Prozess ist nicht standardisiert.
- Der TEI-Header-Workflow aus Alma existiert noch nicht ([decisions.md](decisions.md) O8).
- Externe Korrekturen laufen ueber PDF, nicht direkt auf dem XML.
- GND-Verknuepfung in Oxygen manuell.

### Integration mit der AI-Pipeline

Seit E21 ersetzt bzw. ergaenzt zbz-ocr-tei folgende Schritte:

| Bestehender Schritt | Ersetzt durch |
|---|---|
| Transkribus OCR | Batch-OCR (Mistral/DeepSeek) |
| Manueller Transkribus-Export | automatischer PAGE-XML-Export |
| Oxygen TEI-Markup | automatische TEI-Transformation |
| Manuelles GND-Linking | NER + lobid.org / Wikidata |

### Was manuell bleibt

- Alma-Katalogisierung (bibliotheksspezifisch)
- Masterfile-Pflege (Koordination)
- Swisscovery-Zuweisung
- TEI-Header aus Alma (Workflow existiert noch nicht, O8)
- Finale QA in Oxygen vor Publikation

---

## Bekannte Problemfaelle

| Problem | Betroffene PDFs | Loesungsansatz |
|---|---|---|
| Zweispaltige Lesereihenfolge | 2530, 890, 3040 | Docling + Gemini Detect |
| Seitenuebergreifende Fussnoten | 3040 | `@next/@prev` |
| Interview-Sprecherwechsel | 1440 | Pattern-Erkennung |
| Historischer Druck | 90 | beide OCR-Engines testen |
| Handschriftliche Annotationen | 40 | offen |

---

## Verweise

- [pipeline.md](pipeline.md) — technische Pipeline-Details
- [quality.md](quality.md) — Qualitaetsmetriken und CER-Benchmark
- [decisions.md](decisions.md) — offene Punkte und Entscheidungen
- [infrastruktur.md](infrastruktur.md) — Deployment + APIs
