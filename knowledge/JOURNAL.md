---
type: journal
created: 2026-01-29
updated: 2026-02-25
tags: [zbz-ocr-tei, journal, log]
status: active
---

# Arbeitsjournal

Chronologisches Arbeitslog. Entscheidungen sind in [DECISIONS](DECISIONS.md) konsolidiert, Projektstatus in [PROJEKT](PROJEKT.md).

**Abhängigkeiten:** Keine (eigenständiges Log)

---

## 2026-02-25 | Pipeline komplett: Alle 15 Pilot-Dokumente verarbeitet

### Durchgefuehrt

1. **OCR fuer 3 fehlende Typ-A-Dokumente** (1060, 130, 1410): Mistral OCR, 32 Seiten in 24s
2. **LLM-Korrektur fuer 5 Dokumente** (1060, 130, 1410, 40, 1520): Haiku 4.5 Variante C, 330 Seiten, Kosten $1.45
3. **Seitenweiser Vergleich implementiert** (`evaluate_ocr.py`): Content-basiertes Page-Matching loest Phase-4-Blocker
   - `extract_pages_from_tei()`: Splittet TEI anhand `<pb facs='#facs_N'>` Tags
   - `_match_tei_to_ocr()`: Automatischer Seitenversatz-Erkennung (z.B. 1520.pdf hat +8 Offset)
   - `evaluate_document_pagewise()`: Pro-Seite CER/WER, gewichteter Durchschnitt
   - Auto-Erkennung: Seitenweise bei >10 TEI-Seiten, sonst globales Alignment
4. **Evaluation aller 15 Dokumente**: Mistral-raw + LLM-korrigiert
5. **Dashboard regeneriert**: 15/15 OCR, 15/15 LLM, 15/15 Eval

### Ergebnisse der neuen Dokumente

| Doc | Typ | Mistral CER | LLM CER | Anmerkung |
|-----|-----|------------|---------|-----------|
| 1060 | A | 22.60% | 26.92% | Alignment-Problem (nur 6 TEI-Seiten) |
| 130 | A | 4.13% | 4.15% | Seitenweise, Deckblatt korrekt ignoriert |
| 1410 | A | 5.58% | 5.78% | Zweisprachig DE/FR, akzeptabel |
| 40 | C | 2.57% | 2.65% | Exzellent, 147 Seiten gematcht |
| 1520 | C | 2.73% | 2.75% | Exzellent, 116 Seiten, Offset +8 erkannt |

**Phase 4 (Monografien) CER 2.65%** — beste aller Phasen. Seitenweiser Vergleich loest das Alignment-Problem bei langen Dokumenten vollstaendig.

### TESTPLAN-Items aktualisiert

- [x] Item 10: Seitenweisen Vergleich implementiert
- [x] Item 11: OCR+LLM+Eval fuer alle 15 Docs abgeschlossen
- [ ] Doc 1060 und 290 haben hohe CER — Scan-Qualitaet pruefen
- [ ] Doc 1520 Sprache als FR identifiziert (war "?" in config.py)

---

## 2026-02-25 | Code-Qualitaet: Resource Leak + Duplikation behoben

### Durchgefuehrt

- **`scripts/ocr_pipeline.py`**: Resource Leak in `MistralOCR._split_pdf()` gefixt — `fitz.open()`-Dokumente werden jetzt mit try-finally geschuetzt, sodass sie bei Exceptions nicht offen bleiben
- **`scripts/utils.py`**: `pdf_to_images()` Duplikation aufgeloest — delegiert jetzt an `pdf_to_images_pages()` statt identische Logik zu duplizieren. Dabei Dateinamen-Padding vereinheitlicht (beide nutzen jetzt `:03d`)
- Modul-Docstrings geprueft: Alle 14 Python-Module haben bereits Docstrings, kein Handlungsbedarf

### Begruendung

Systematisches Code-Audit identifizierte 3 potenzielle Verbesserungen, davon 2 umgesetzt:
1. Resource Leak: Bei Exception zwischen `fitz.open()` und `.close()` blieben Dokumente offen — behoben mit try-finally
2. Code-Duplikation: `pdf_to_images()` und `pdf_to_images_pages()` hatten nahezu identische Implementierungen — konsolidiert
3. Fehlende Docstrings: Bereits vorhanden, kein Handlungsbedarf

### Neue/geaenderte Dateien

| Datei | Aenderung |
|-------|-----------|
| `scripts/ocr_pipeline.py` | FIX: try-finally in `_split_pdf()` |
| `scripts/utils.py` | REFACTOR: `pdf_to_images()` delegiert an `pdf_to_images_pages()` |

---

## 2026-02-25 | ARCHITEKTUR.md → PIPELINE.md umbenannt + inhaltlich korrigiert

### Durchgefuehrt

- `knowledge/ARCHITEKTUR.md` → `knowledge/PIPELINE.md` umbenannt (git mv)
- Alle 35 Referenzen in 14 Dateien aktualisiert (CLAUDE.md, README.md, 9 Knowledge-Docs)
- Header, Tags und Beschreibung angepasst
- **6 inhaltliche Korrekturen:**
  1. Pipeline-Diagramm: Zeigt jetzt den tatsaechlichen Datenfluss (OCR → LLM → Eval → Dashboard)
  2. Docling als integralen Teil von `ocr_pipeline.py` dokumentiert (nicht eigene Stufe)
  3. Engine-Auswahl: Auto-Modus aus dem Code beschrieben
  4. Evaluation und Dashboard als eigene Stufen ergaenzt (fehlten komplett)
  5. Post-Processing-Widerspruch behoben (R6: `clean_markdown()` nicht im Produktionspfad)
  6. CLI-Befehle vollstaendig mit allen Parametern

### Begruendung

"Architektur" suggeriert High-Level-Systemdesign. Der Inhalt beschreibt den konkreten
Datenfluss durch die Scripts — das ist eine Pipeline-Dokumentation. Ausserdem stimmte
der dokumentierte Ablauf nicht mit dem Code ueberein (veraltetes Diagramm, fehlende Stufen).

### Neue/geaenderte Dateien

| Datei | Aktion |
|-------|--------|
| `knowledge/ARCHITEKTUR.md` | UMBENANNT → `knowledge/PIPELINE.md` |
| `knowledge/PIPELINE.md` | UPDATE (Header, Diagramm, 6 Korrekturen) |
| `CLAUDE.md` | UPDATE (Referenz) |
| `README.md` | UPDATE (Referenz) |
| `knowledge/INDEX.md` | UPDATE (6 Referenzen + Verzeichnisstruktur) |
| `knowledge/DECISIONS.md` | UPDATE (7 Referenzen) |
| `knowledge/OCR-ENGINES.md` | UPDATE (2 Referenzen) |
| `knowledge/INFRASTRUKTUR.md` | UPDATE (2 Referenzen) |
| `knowledge/PROJEKT.md` | UPDATE (1 Referenz) |
| `knowledge/QUELLENANALYSE.md` | UPDATE (1 Referenz) |
| `knowledge/TEI-MAPPING.md` | UPDATE (1 Referenz) |
| `knowledge/GND-STRATEGIE.md` | UPDATE (1 Referenz) |
| `knowledge/ZBZ-WORKFLOW.md` | UPDATE (1 Referenz) |

---

## 2026-02-25 | Projekt-Aufraeumung: Redundante Dateien entfernt

### Durchgefuehrt

**Geloeschte Dateien (7):**
- `nul` — Leere Datei, Windows-Artefakt (0 Bytes, nicht getrackt)
- `scripts/test_deepseek_ocr.py` — Redundant mit `ocr_pipeline.py --engine deepseek`
- `scripts/test_docling.py` — Redundant mit `ocr_pipeline.py --engine docling`
- `scripts/test_mistral_ocr.py` — Redundant mit `ocr_pipeline.py --engine mistral`
- `scripts/test_column_prompt.py` — Einmaliges Spalten-Experiment, erledigt
- `scripts/extract_layout.py` — Layout-Extraktion in `ocr_pipeline.py` integriert
- `PROJEKTWISSEN.md` — 95% Duplikat der 12 Knowledge-Docs, verletzt Single-Source-of-Truth

**Bereinigte Redundanzen:**
- `knowledge/OCR-ENGINES.md`: Evaluationstabellen (CER/WER) entfernt, Verweis auf TESTPLAN.md
- `knowledge/ARCHITEKTUR.md`: `extract_layout.py`-Referenz durch `ocr_pipeline.py` ersetzt
- `README.md`: Link `knowledge/journal.md` → `knowledge/JOURNAL.md` korrigiert, Datum aktualisiert
- `scripts/README.md`: Script-Tabelle aktualisiert (geloeschte raus, fehlende rein)
- `scripts/__pycache__/` + `scripts/postprocess/__pycache__/` lokal entfernt

### Begruendung

Systematische Analyse aller Projektdateien ergab:
- 5 Test-Scripts waren vollstaendig redundant mit `ocr_pipeline.py` (keine Imports, nicht in CLAUDE.md)
- PROJEKTWISSEN.md duplizierte Inhalte aus PROJEKT, ARCHITEKTUR, QUELLENANALYSE, TESTPLAN, DECISIONS, INFRASTRUKTUR
- OCR-ENGINES.md enthielt identische Evaluationstabellen wie TESTPLAN.md

### Neue/geaenderte Dateien

| Datei | Aktion |
|-------|--------|
| `nul` | GELOESCHT |
| `PROJEKTWISSEN.md` | GELOESCHT |
| `scripts/test_deepseek_ocr.py` | GELOESCHT |
| `scripts/test_docling.py` | GELOESCHT |
| `scripts/test_mistral_ocr.py` | GELOESCHT |
| `scripts/test_column_prompt.py` | GELOESCHT |
| `scripts/extract_layout.py` | GELOESCHT |
| `knowledge/OCR-ENGINES.md` | UPDATE (Evaluationstabellen entfernt) |
| `knowledge/ARCHITEKTUR.md` | UPDATE (extract_layout-Referenz) |
| `README.md` | UPDATE (Link-Fix, Datum) |
| `scripts/README.md` | UPDATE (Script-Tabelle) |

---

## 2026-02-25 | Dashboard-Redesign + Engine-Sichtbarkeit + Knowledge-Update

### Durchgefuehrt

**Dashboard-Redesign (Session 1):**
- Vollstaendige Projektanalyse und Dateninventur (15 Pilot-PDFs, 383 Seiten, 12 mit OCR, 10 mit LLM)
- `scripts/generate_dashboard_data.py` erstellt: Generiert `docs/data/dashboard.json` aus allen Pipeline-Quellen
- `docs/shared.css` erstellt: Unified Design System (CSS Custom Properties, warm-beige Light Theme)
- `docs/shared.js` erstellt: Shared Utilities (Data Loading, Text-Fetching, Formatting, DOM Helpers)
- `docs/index.html` komplett neu geschrieben: Dashboard + Dokumentkatalog + Qualitaetsvergleich
- `docs/viewer.html` komplett redesigned: Light Theme, Source-Toggle (Mistral/LLM/DeepSeek)
- benchmark.html-Inhalte in index.html integriert (Phasen-Summary + Dokument-Vergleichskarten)
- Pipeline-Steps beschriftet (IMG, OCR, LLM, EVAL, EXP statt anonyme Punkte)
- Viewer als vollwertige Dokumentseite mit Info-Bar (Metriken, CER-Bars, Keyboard-Shortcuts)

**Engine-Sichtbarkeit (Session 2):**
- `shared.js`: `engineBadges()` Funktion + OCR-Pipeline-Step als Composite (Mistral/DeepSeek Sub-Dots)
- `shared.css`: Engine-Dot Styles (.teal/.violet), Engine-Badges Container
- `index.html`: Engine-Filter Dropdown, DeepSeek-CER-Spalte, Engine-Badges-Spalte, per-Engine Metriken
- `viewer.html`: Engine-Badges in Doc-Info-Bar

**Knowledge-Update (Session 2):**
- Alle 12 Knowledge-Docs + PROJEKTWISSEN.md auf Stand 25.02.2026 gebracht
- TEI-MAPPING.md + GND-STRATEGIE.md: E12-Scope-Hinweis ergaenzt
- INFRASTRUKTUR.md: Stale Dockerfile-Referenz (`templates/`) entfernt, Dashboard-Deployment ergaenzt
- DECISIONS.md: E15 (Dashboard-Redesign) hinzugefuegt
- ARCHITEKTUR.md: Dashboard-QA-UI Sektion + CLI-Befehl ergaenzt
- INDEX.md: Dashboard-Navigation + Kernbegriff ergaenzt
- TESTPLAN.md: Dashboard-Link ergaenzt
- OCR-ENGINES.md: benchmark.html-Referenz durch Dashboard ersetzt
- ZBZ-WORKFLOW.md: QA-Dashboard Sektion ergaenzt
- PROJEKTWISSEN.md: Dashboard-Dateien, E15, Scripts-Tabelle aktualisiert

### Architektur

- Multi-Page mit Shared CSS/JS (statt drei unabhaengige Designs)
- Statische JSON-Datenbasis (`dashboard.json`) statt hardcodierter Daten in HTML
- Source-Toggle im Viewer: Tastatur 1/2/3 fuer Mistral/LLM/DeepSeek
- Filterbarer Dokumentkatalog mit Pipeline-Status-Anzeige (beschriftete Steps)
- CER-Vergleichsbalken (Mistral vs LLM-C, optional DeepSeek)
- Engine-Badges (M/DS/LLM) fuer sofortige Engine-Erkennung pro Dokument

### Entscheidung

- **E15**: Dashboard-Redesign — Multi-Page UI, Shared CSS/JS, Light Theme, statische JSONs, Engine-Sichtbarkeit

### Neue/Geaenderte Dateien

| Datei | Aktion |
|-------|--------|
| `scripts/generate_dashboard_data.py` | NEU |
| `docs/data/dashboard.json` | GENERIERT |
| `docs/shared.css` | NEU + Engine-Styles |
| `docs/shared.js` | NEU + engineBadges() + Composite Pipeline |
| `docs/index.html` | REWRITE + Engine-Spalten/Filter |
| `docs/viewer.html` | REWRITE + Engine-Badges in Info-Bar |
| `docs/benchmark.html` | ARCHIV (nicht mehr verlinkt) |
| `knowledge/*.md` (alle 12) | UPDATE (Timestamps, Inhalte, E12-Scope) |
| `PROJEKTWISSEN.md` | UPDATE (Dashboard, E15, Scripts) |

---

## 2026-02-20 | coOCR-Interface-Analyse: PAGE-XML + PNG

### Durchgefuehrt

- coOCR/HTR-Repo ([DHCraft/co-ocr-htr](https://github.com/DHCraft/co-ocr-htr)) vollstaendig analysiert
- Import-Format identifiziert: PAGE-XML (Schema 2019-07-15) + PNG + METS-XML
- Exportstruktur definiert: `output/export/{doc_id}/` mit mets.xml, images/, page/
- Batch-Orchestrierungs-Architektur entworfen (noch nicht implementiert)

### Erkenntnisse

- coOCR ist eine reine Browser-App (kein Backend-API) — Import ueber File-Upload
- PAGE-XML Namespace: `http://schema.primaresearch.org/PAGE/gts/pagecontent/2019-07-15`
- Text wird in `<TextEquiv><Unicode>` as-is gespeichert — Markdown-Formatierung muss erhalten bleiben
- Confidence-Mapping: Mistral-roh=0.85, LLM-korrigiert=0.95
- coOCR exportiert `<ab>` (nicht `<p>`) — relevant fuer teiCrafter-Schnittstelle (O5)

### Geloest

- **O4**: Schnittstelle zbz-ocr-tei -> coOCR = PAGE-XML + PNG + METS (E13)
- **R6**: Markdown-Formatierung erhalten, Post-Processing darf Markup nicht entfernen (E14)

### Naechste Schritte

- `scripts/export_page_xml.py` implementieren (Markdown -> PAGE-XML Konverter)
- `scripts/run_pipeline.py` implementieren (Batch-Orchestrierung mit Resume/Retry)
- Post-Processing anpassen: Markdown-Markup erhalten

---

## 2026-02-19 | Scope-Klaerung: Nur OCR, keine TEI-Transformation

### Entscheidung (E12)

zbz-ocr-tei ist rein fuer OCR zustaendig (PDF -> korrigiertes Markdown). TEI-Transformation und GND-Verknuepfung finden in coOCR/HTR und teiCrafter statt.

### Aufgeraeumt

- `scripts/transform_to_tei.py` entfernt (393 Zeilen)
- `templates/` entfernt (5 TEI-Templates + README)
- `DOC_TYPES` und `TEI_DIR` aus config.py entfernt
- ARCHITEKTUR.md: Pipeline auf 4 Stufen reduziert (ohne TEI/GND)
- PROJEKT.md: Meilensteine angepasst (M2=Produktion, M3=coOCR-Integration)
- DECISIONS.md: E12 hinzugefuegt, TEI-Fragen (O6-O9, O11-O14, R2-R3) nach coOCR/teiCrafter verschoben
- README.md komplett neu geschrieben

### Behalten

- `evaluate_ocr.py` + Referenz-TEI-Lesefunktion (Ground Truth fuer CER)
- `extract_gnd.py` + KNOWN_ENTITIES (GND-Seed fuer Downstream)
- `knowledge/TEI-MAPPING.md` und `GND-STRATEGIE.md` (Referenzwissen)

---

## 2026-02-19 | Prompt-Optimierung: A/B/C-Test fuer LLM-Korrektur

### Durchgefuehrt

- Drei Prompt-Varianten implementiert: A (Analysis+Corrected), B (Schlank), C (Few-Shot)
- `--variant` Flag in `llm_postprocess.py` ergaenzt
- Alle drei Varianten auf Phase 1-3 (10 Docs, 53 Seiten) getestet
- CER-Vergleich gegen Referenz-TEI

### Ergebnisse

| Variante | Avg CER | Kosten | Beschreibung |
|----------|---------|--------|--------------|
| Mistral (kein LLM) | 5.87% | $0.00 | Baseline |
| A (Analysis+Corrected) | 5.47% | $0.39 | Chain-of-Thought |
| B (Schlank, nur Text) | 5.59% | $0.33 | Minimal-Prompt |
| **C (Few-Shot)** | **5.55%** | **$0.33** | Fehlerbeispiele |

### Entscheidung

**Variante C als Default** — bester CER/Kosten-Tradeoff. Gesamtverbesserung: 5.87% -> 5.55% (5.5% relativ).
Unterschiede zwischen A/B/C sind gering (~0.1 Punkte). Few-Shot-Beispiele helfen leicht.

---

## 2026-02-19 | LLM-basierte OCR-Nachkorrektur mit Haiku 4.5

### Durchgefuehrt

- `scripts/llm_postprocess.py` erstellt: LLM-basierte OCR-Korrektur mit Anthropic Claude Haiku 4.5
- `scripts/config.py` erweitert: LLM_CORRECTED_DIR, ANTHROPIC_MODEL, get_test_metadata()
- `.env.example` erstellt als Vorlage (ohne Secrets)
- ANTHROPIC_API_KEY in `.env` konfiguriert (bereits in .gitignore + .claudeignore)
- Pilot-Test: Phase 1-3 (10 Docs, 50 Seiten) durch LLM-Korrektur + CER-Vergleich

### Architektur

Ein API-Call pro Seite (Chain-of-Thought): `<analysis>` listet Fehler, `<corrected>` gibt korrigierten Text.
Prompt enthaelt Dokumentkontext aus TESTPLAN (Typ, Sprache, Genre).

### Ergebnisse: Mistral vs. LLM-korrigiert

| Doc | Typ | Mistral CER | LLM CER | Delta |
|-----|-----|-------------|---------|-------|
| 2310 | A | 7.00% | 3.93% | **-3.07** |
| 1180 | A | 3.12% | 3.17% | +0.05 |
| 290 | A | 18.07% | 18.20% | +0.13 |
| 2530 | B | 3.96% | 3.98% | +0.02 |
| 890 | B | 5.96% | 6.05% | +0.09 |
| 3040 | B | 9.02% | 8.97% | -0.05 |
| 90 | D | 1.21% | 1.10% | **-0.11** |
| 1440 | D | 3.71% | 3.71% | 0.00 |
| 830 | D | 4.00% | 3.29% | **-0.71** |
| 1330 | D | 2.60% | 2.78% | +0.18 |

| Phase | Mistral Avg CER | LLM Avg CER | Delta |
|-------|-----------------|-------------|-------|
| Phase 1 (A) | 9.40% | 8.43% | -0.97 |
| Phase 2 (B) | 6.31% | 6.34% | +0.03 |
| Phase 3 (D) | 2.88% | 2.72% | -0.16 |
| **Gesamt** | **5.87%** | **5.47%** | **-0.40 (7% relativ)** |

### Kosten

- Phase 1-3 (50 Seiten): $0.39
- Hochrechnung 289 Docs (7.200 Seiten): ~$56

### Erkenntnisse

- Staerkste Verbesserung bei Dokumenten mit OCR-Artefakten (JSTOR-Header, Coverseiten)
- Gute Verbesserung bei Spezialformaten (historisch, Bildband)
- Kein Effekt bei Scan-Qualitaetsproblemen (Doc 290 bleibt bei ~18%)
- Bei bereits guter OCR (~3% CER) kein signifikanter Gewinn
- Vereinzelt minimale Verschlechterung moeglich (1330: +0.18) durch LLM-"Korrekturen"

### Neue Dateien

- `scripts/llm_postprocess.py` — LLM-Korrektur-Pipeline
- `.env.example` — Vorlage fuer API-Keys

---

## 2026-02-18 | M1: OCR-Validierung + Mistral-Integration + Refactoring

**Mistral Document AI integriert und gegen alle 12 Testdokumente (Phase 1-4) evaluiert.**

- `MistralOCR`-Klasse in `ocr_pipeline.py` implementiert (Azure AI Foundry Endpoint, Base64-Upload, automatisches PDF-Splitting bei >30 Seiten)
- `evaluate_ocr.py` erweitert: `--ocr-dir`, `--engine`, `--phase` Parameter, Fuzzy TEI-Lookup, rapidfuzz fuer CER (loest MemoryError)
- **Ergebnis Phase 1-3: CER 5.87%, Genauigkeit 94.14%** — Einzelwerte in [TESTPLAN](TESTPLAN.md) §Ergebnisse
- Phase 4 (Monografien): Alignment bei 142-156-seitigen Buechern nicht zuverlaessig, seitenweiser Vergleich noetig
- Doc 290 (Comptes Rendus FR): CER 18% — vermutlich Scan-Qualitaet, nicht OCR-Problem
- Mistral ~1.3s/Seite (Cloud-API, kein GPU noetig), erkennt Kursivschrift und Akzente

**Code-Refactoring: Zentrale Module eingefuehrt.**

- `scripts/config.py` erstellt: Alle Pfade, Modellnamen, Konstanten, Testplan
- `scripts/utils.py` erstellt: `pdf_to_images()`, `check_gpu()`, `load_env()`, `load_deepseek_model()`
- 12 Scripts refactored: Eliminiert 4x `pdf_to_images`, 4x `check_gpu`, 4x `load_model`, 2x `load_env`, 2x `TESTPLAN`

**Technisch:** Azure AI Foundry hat eigenes URL-Format; PyMuPDF >= 1.24 hat `fitz` zu `pymupdf` umbenannt.

---

## 2026-02-18 | Knowledge-Vault Refactoring

- Knowledge-Ordner nach coOCR/teiCrafter-Muster aufgebaut: INDEX.md, PROJEKT.md, DECISIONS.md, INFRASTRUKTUR.md als neue Kerndokumente
- Single Source of Truth eingefuehrt, Duplikation eliminiert
- Oekosystem-Kontext dokumentiert (zbz-ocr-tei -> coOCR -> teiCrafter)
- Erkannt: Post-Processing entfernt Markdown-Formatierung vor TEI — Informationsverlust (-> R6); TEI-Transformation nur Prototyp; Schnittstellen zwischen Tools undefiniert

---

## 2026-02-14 | Auftrag beidseitig bestaetigt, Projektstart

- Auftrag bestaetigt: ZBZ erteilt (Mail Elias, nach 07.02.), DHCraft angenommen (Mail Christopher, 14.02.)
- Rahmenbedingungen: Mistral OCR 3 ueber Azure, Claude Max Subscription, Gemini API, Fork auf GitLab Uni Zuerich, Podman
- Team ZBZ: Anouschka (Editions- und Informatik-Background, seit Januar)
- coOCR/HTR als Community-Projekt positioniert (Klugseder-Fork als Referenz)
- Alignment-Call: Terminvorschlaege gesendet (Agenda: Fork-Modell, Merge-Strategie, GitLab, Podman, Vor-Ort Zuerich)

---

## 2026-02-02 | Gemini 3 Agentic Vision Analyse

- Google Agentic Vision fuer Gemini 3 Flash (27.01.2026): Think-Act-Observe Loop fuer Auto-Crop von Spalten — potenzielle Loesung fuer Typ-B-Problem (O10)
- Details: [OCR-ENGINES](OCR-ENGINES.md) §Gemini
- Quellen: [Announcement](https://blog.google/innovation-and-ai/technology/developers-tools/agentic-vision-gemini-3-flash/), [IIIF Example](https://gist.github.com/charlesLoder/5341c539ab8330cfebc2d807e6b9c765)

---

## 2026-01-29 | Materialanalyse & Pipeline-Entwicklung

**Erste Arbeitssession: Korpusanalyse, Hybrid-Pipeline validiert, OCR Phase 1 durchgefuehrt.**

- 289 Texte (7.200 Seiten) analysiert, 4 Dokumenttypen klassifiziert (A-D) — Details in [QUELLENANALYSE](QUELLENANALYSE.md)
- Hybrid-Pipeline validiert: Docling (Layout, CPU) + DeepSeek (OCR, GPU) funktioniert
- Docling OCR nicht nutzbar (RapidOCR Encoding-Fehler: `e` -> `O` bei frz. Text) — nur fuer Layout eingesetzt (E2)
- OCR Phase 1: 94.4% Genauigkeit auf Typ-A-Dokumenten — Details in [TESTPLAN](TESTPLAN.md)
- GND-Seed: 75 Entitaeten extrahiert — Details in [GND-STRATEGIE](GND-STRATEGIE.md)
- TEI-Prototyp: 5 Templates erstellt (spaeter entfernt mit E12)
- 383 Seitenbilder aus 15 Pilot-PDFs extrahiert

---

*Erstellt: 2026-01-29 | Aktualisiert: 2026-02-25*
