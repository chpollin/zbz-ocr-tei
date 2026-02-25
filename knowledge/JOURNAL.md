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

## 2026-02-18 | M1: OCR-Validierung alle Dokumenttypen

### Durchgefuehrt

- `evaluate_ocr.py` erweitert: `--ocr-dir`, `--engine`, `--phase` Parameter
- Fuzzy TEI-Lookup (findet `1520 - in Arbeit.xml`)
- rapidfuzz fuer CER-Berechnung (loest MemoryError bei langen Texten)
- Verbessertes Alignment (Markdown-Stripping, abgestufte Phrase-Suche)
- Mistral OCR fuer alle 12 Testdokumente (Phase 1-4) ausgefuehrt
- CER/WER-Evaluation gegen Referenz-TEI abgeschlossen

### Ergebnisse Mistral Document AI

| Phase | Typ | Docs | Avg CER | Avg WER | Genauigkeit |
|-------|-----|------|---------|---------|-------------|
| Phase 1 | A (einspaltig) | 3 | 9.40% | 20.22% | 90.60% |
| Phase 2 | B (zweispaltig) | 3 | 6.31% | 17.53% | 93.69% |
| Phase 3 | D (Spezial) | 4 | 2.88% | 12.62% | 97.12% |
| Phase 4 | C (Monografie) | 2 | n/a | n/a | Alignment-Problem |

**Phase 1-3 Durchschnitt: CER 5.87%, Genauigkeit 94.14%**

Phase 4 (Monografien) nicht aussagekraeftig: Alignment bei 156/142-seitigen Buechern funktioniert
nicht zuverlaessig (gesamter Referenz-Text vs. gesamte OCR verglichen).

### Einzelergebnisse

| Doc | Typ | CER | WER |
|-----|-----|-----|-----|
| 2310 | A | 7.00% | 22.04% |
| 1180 | A | 3.12% | 10.45% |
| 290 | A | 18.07% | 28.17% |
| 2530 | B | 3.96% | 17.06% |
| 890 | B | 5.96% | 12.80% |
| 3040 | B | 9.02% | 22.73% |
| 90 | D | 1.21% | 8.92% |
| 1440 | D | 3.71% | 12.69% |
| 830 | D | 4.00% | 17.46% |
| 1330 | D | 2.60% | 11.42% |

### Erkenntnisse

- Mistral Document AI zeigt beste Ergebnisse bei Typ D (Spezialformate): 97% Genauigkeit
- Doc 290 (Comptes Rendus FR) hat schlechteste CER in Phase 1-3 (18%) - vermutlich Scan-Qualitaet
- Zweispaltige Docs (Typ B) werden ueberraschend gut erkannt (CER 6.3%)
- Fuer Monografien braucht die Evaluation einen seitenweisen Vergleichsansatz

---

## 2026-02-18 | Code-Refactoring: Zentrale Module

### Durchgefuehrt

- `scripts/config.py` erstellt: Alle Pfade, Modellnamen, Konstanten, Testplan an einem Ort
- `scripts/utils.py` erstellt: `pdf_to_images()`, `check_gpu()`, `load_env()`, `load_deepseek_model()`
- 12 Scripts refactored: Duplizierte Funktionen durch shared imports ersetzt
- Eliminiert: 4x `pdf_to_images()`, 4x `check_gpu()`, 4x `load_model()`, 2x `load_env()`, 2x `TESTPLAN`
- Alle Imports verifiziert (16 Module laden korrekt)

### Betroffene Dateien

| Datei | Aenderung |
|-------|-----------|
| `scripts/config.py` | **NEU** - Zentrale Konfiguration |
| `scripts/utils.py` | **NEU** - Gemeinsame Hilfsfunktionen |
| `scripts/ocr_pipeline.py` | Nutzt config/utils, lokale Duplikate entfernt |
| `scripts/test_mistral_ocr.py` | Nutzt config/utils statt eigener load_env/PHASE1_TESTS |
| `scripts/test_all_pdfs.py` | Nutzt config/utils statt eigenem TESTPLAN/check_gpu/load_model |
| `scripts/test_deepseek_ocr.py` | Nutzt config/utils statt eigener pdf_to_images/check_gpu/load_model |
| `scripts/test_column_prompt.py` | Nutzt config/utils statt eigener check_gpu/load_model |
| `scripts/evaluate_ocr.py` | Nutzt config statt PROJECT_ROOT-Pfade |
| `scripts/transform_to_tei.py` | Nutzt config statt lokaler DOC_TYPES/KNOWN_ENTITIES |
| `scripts/extract_pages.py` | Nutzt config statt PROJECT_ROOT-Pfade |
| `scripts/extract_layout.py` | Nutzt config statt PROJECT_ROOT-Pfade |
| `scripts/extract_gnd.py` | Nutzt config statt PROJECT_ROOT-Pfade |
| `scripts/test_docling.py` | Nutzt config statt PROJECT_ROOT-Pfade |

---

## 2026-02-18 | Mistral Document AI Integration & Benchmark

### Durchgefuehrt

- Mistral Document AI 2512 als OCR-Engine in Pipeline integriert (MistralOCR-Klasse)
- Azure AI Foundry Endpoint konfiguriert (.env, .claudeignore, .gitignore)
- Phase-1-Benchmark: alle 3 Typ-A-Dokumente erfolgreich verarbeitet
- Benchmark-Ergebnis: Mistral erkennt 142% mehr Zeichen als DeepSeek (alle Seiten vs 2 Seiten)
- Interaktives Benchmark Web-UI erstellt (docs/benchmark.html)
- Knowledge-Vault aktualisiert (OCR-ENGINES.md, INFRASTRUKTUR.md)

### Benchmark-Ergebnisse Phase 1

| Dokument | Seiten | Mistral Zeichen | DeepSeek Zeichen | Mistral Zeit |
|----------|--------|-----------------|------------------|--------------|
| 2310.pdf | 3 | 8.041 | 6.597 | 5.6s (1.9s/S) |
| 1180.pdf | 8 | 20.121 | 6.070 | 6.4s (0.8s/S) |
| 290.pdf | 5 | 15.148 | 5.213 | 6.3s (1.3s/S) |

Hinweis: DeepSeek hatte in frueheren Tests nur 2 Seiten pro Dokument verarbeitet (lokale GPU), Mistral verarbeitet alle Seiten serverseitig.

### Neue Dateien

- `scripts/test_mistral_ocr.py` - Benchmark-Skript
- `docs/benchmark.html` - Interaktives Benchmark-UI
- `.env` / `.env.example` / `.claudeignore` - Konfiguration & Sicherheit
- `output/mistral_results/` - OCR-Ergebnisse + Manifest

### Technische Erkenntnisse

- Azure AI Foundry Endpoint hat eigenes URL-Format (nicht Standard Mistral-API)
- PyMuPDF >= 1.24 hat `fitz` zu `pymupdf` umbenannt
- Mistral erkennt Kursivschrift (*italics*), Fussnoten und Akzente zuverlaessig
- Kein GPU noetig (Cloud-API), ~1.3s/Seite Durchschnitt

---

## 2026-02-18 | Knowledge-Vault Refactoring

### Durchgeführt

- Vollständige Repository-Analyse (Struktur, Code, Dokumentation)
- Knowledge-Ordner nach coOCR/teiCrafter-Muster refactored
- Neue Kerndokumente: INDEX.md, PROJEKT.md, DECISIONS.md, INFRASTRUKTUR.md
- Duplikation eliminiert, Single Source of Truth eingeführt
- Ökosystem-Kontext dokumentiert (zbz-ocr-tei → coOCR → teiCrafter)

### Erkenntnisse

- Post-Processing entfernt Markdown-Formatierung *vor* TEI-Transformation — Informationsverlust (→ R6 in [DECISIONS](DECISIONS.md))
- TEI-Transformation nur als Einzelseiten-Prototyp, nicht als Dokument-Assembly
- Kein Code für Azure/Mistral/Gemini — nur DeepSeek + Docling implementiert
- Schnittstellen zwischen den drei Tools noch undefiniert

---

## 2026-02-14 | Auftrag beidseitig bestätigt, Projektstart

### Zusammenfassung

Auftrag beidseitig bestätigt. ZBZ hat erteilt (Mail Elias, nach 07.02.), DHCraft hat angenommen (Mail Christopher, 14.02.). Projekt wechselt von Akquisephase in Umsetzung.

### Neue Rahmenbedingungen

- Mistral OCR 3 über Azure verfügbar, API-Key wird bereitgestellt
- Claude Max Subscription empfohlen (Coding, Promptotyping)
- Gemini API empfohlen (OCR/HTR, multimodale Stärke)
- CI/CD: Fork auf GitLab Uni Zürich, Podman
- Team ZBZ: Anouschka (Editions- und Informatik-Background, seit Januar)
- coOCR/HTR als Community-Projekt positioniert (Klugseder-Fork als Referenz)

### Alignment-Call

Terminvorschläge gesendet, Rückmeldung ausstehend. Agenda: Fork-Modell, Merge-Strategie, GitLab-Setup, Podman-Details, Vor-Ort-Termin Zürich.

### Dokumentation aktualisiert

- Vault-Dokument, Projektplan, Pipeline, OCR-Tools

---

## 2026-02-02 | Gemini 3 Agentic Vision Analyse

### Zusammenfassung

Google hat am 27.01.2026 Agentic Vision für Gemini 3 Flash veröffentlicht. Think-Act-Observe Loop ermöglicht Auto-Crop von Spalten — potenzielle Lösung für Typ-B-Problem.

Details: Siehe [OCR-ENGINES](OCR-ENGINES.md) §Gemini.

### Quellen

- [Agentic Vision Announcement](https://blog.google/innovation-and-ai/technology/developers-tools/agentic-vision-gemini-3-flash/)
- [IIIF Annotation Example](https://gist.github.com/charlesLoder/5341c539ab8330cfebc2d807e6b9c765)

---

## 2026-01-29 | Materialanalyse & Pipeline-Entwicklung

### Zusammenfassung

Intensive Arbeitssession: Korpusanalyse, Hybrid-Pipeline validiert, OCR Phase 1 durchgeführt, TEI-Prototyp erstellt, GND-Seed extrahiert, Bildextraktion abgeschlossen.

### Ergebnisse

| Bereich | Ergebnis |
|---------|----------|
| OCR Phase 1 | 94.4% Genauigkeit — Details in [TESTPLAN](TESTPLAN.md) |
| Docling Layout | Funktioniert auf Windows, Spalten erkannt |
| Docling OCR | Nicht nutzbar (Encoding-Fehler) — Details in [OCR-ENGINES](OCR-ENGINES.md) |
| GND-Extraktion | 75 Entitäten — Details in [GND-STRATEGIE](GND-STRATEGIE.md) |
| TEI-Templates | 5 erstellt in `templates/` |
| Bildextraktion | 383 Seiten aus 15 PDFs |

### Gelernt

1. Docling nur für Layout — OCR-Komponente hat Encoding-Probleme
2. Hybrid-Ansatz validiert — Docling Koordinaten + DeepSeek Text funktioniert
3. Windows funktioniert — Docling läuft (mit Symlink-Warnung)
4. OCR-Qualität ist dokumenttyp-abhängig
5. Single Source of Truth für offene Punkte

### Technische Hindernisse

| Problem | Status | Workaround |
|---------|--------|------------|
| Docling OCR: Encoding-Fehler | Gelöst | Docling nur für Layout |
| Docling: Symlink-Warnung | Ignorierbar | Funktioniert trotzdem |
| DeepSeek: Hohe GPU-Last | Bekannt | Tests einzeln oder Cloud |

---

*Erstellt: 2026-01-29 | Aktualisiert: 2026-02-25*
