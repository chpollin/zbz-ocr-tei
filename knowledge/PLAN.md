---
type: knowledge
created: 2026-02-25
updated: 2026-03-26
tags: [zbz-ocr-tei, plan, implementation, phases]
status: active
---

# Implementation Plan: Full AI Pipeline (PDF -> TEI-XML)

Context: zbz-ocr-tei covers the entire pipeline. ZBZ retains Transkribus, DHCraft builds a parallel AI pipeline.
Component status: [PROJEKT](PROJEKT.md). Pipeline stages and CLI: [PIPELINE](PIPELINE.md).

---

## Phase Overview

```
Phase 0 (Pilot: Layout-Eval + OCR + TEI) --- DONE
    |
    v
Phase 1 (Scale: Layout 285 docs + Gemini QA) --- DONE
    |
    v
Phase 2 (PAGE-XML generator) --- DONE (285 docs, 4,108 pages)
    |
    v
Phase 3 (NER + GND)  <-- can run parallel with Phase 2
    |
    v
Phase 4 (TEI-XML extend with PAGE-XML + NER) --- DONE (285/285, 285/285 schema-valide)
    |
    v
Phase 5 (Evaluation + Dashboard extension)
    |
    v
Phase 6 (Production + Quality Screening)
```

---

## Completed

Phase 0 -- Pilot (15 docs): Layout evaluation (E19/E20), image extraction, OCR (Mistral, E6), LLM correction tested and made optional (E17), TEI-XML (E22), evaluation + dashboard, data delivery (E23).

Phase 1 -- Scale Layout (285 docs): Docling layout (E24 docling-serve, E20 local GPU). Gemini QA (E25) + Detect (E26) with auto-routing (E31: full run completed). Viewer integration with Docling/Gemini toggle. Overlay generator.

Open from Phase 1:
- [ ] Prompt tuning: rightmost column missed on wide landscapes, picture detection weak

---

## Completed: Phase 2 -- PAGE-XML Generator

- [x] scripts/layout/page_xml_generator.py -- LayoutRegion + OCR text -> PAGE-XML
- [x] scripts/layout/mets_generator.py -- METS manifest (PAGE-XML refs)
- [x] Schema: PAGE-XML 2013-07-15 (Transkribus standard)
- [x] ID scheme: r_{N} / r_{N}_tl_1 (region-level, 1 TextLine per region)
- [x] Production run complete
- [ ] Validate against XSD schema (optional)
- [ ] Transkribus import test (if access available)

## Phase 3 -- NER + Wikidata Linking (E34)

Prerequisite: OCR text exists (independent of PAGE-XML).

- [x] scripts/ner/ner_extract.py -- Gemini Flash Lite NER (6 Entity-Typen)
- [x] scripts/ner/entity_store.py -- Per-document JSON registry
- [x] scripts/ner/entity_index.py -- TEI-XML Indices + String-Matching + ID-Vergabe
- [x] scripts/ner/wikidata_linker.py -- Wikidata API Reconciliation + Cache
- [x] scripts/ner/ner_inject_tei.py -- TEI Entity Injection
- [x] data/entities/*.xml -- TEI Entity Indices (person, org, place, work)
- [x] Entity types: person, organization, place, work, event, date
- [x] ID-Schema: zbz-p.N, zbz-o.N, zbz-l.N, zbz-w.N, zbz-e.N, zbz-d.N
- [x] Pilot Doc 2310 erfolgreich
- [x] NER Production Run: 285/285 Docs, 11,685 Entities, 26,197 Mentions (E35)
- [x] Entity Index Merge: 4,504 Eintraege (person 1,979, org 698, place 661, work 762)
- [x] TEI Injection Production: 285/285 Docs mit Entity-Markup (Dual-Attribut E50: ref=GND + corresp=#zbz)
- [x] NER Evaluation: HTML-Report (output/ner_report.html)
- [ ] Wikidata Reconciliation: 67/285 Docs fertig (15%), restliche 218 pending
- [x] Viewer: WD/zbz-ID Support in tei-viewer.js + edition-tei.js (Session 23)
- [ ] Targets: Recall >70%, Precision >80%, Wikidata linking >50%

## Phase 4 -- TEI-XML Extension

Prerequisite: Phase 3 (NER) for full entities; Gemini Vision TEI works independently.
Current: Rule-based generator (flat structure). Gemini Vision TEI (E30): Pilot Doc 2310 successful.

- [x] teiHeader with real title, author, date from doc_metadata.json
- [x] OCR source priority: Gemini B > Gemini A > LLM C > Mistral
- [x] Language mapping: ISO 639-3 + legacy 2-letter fallback
- [x] Production (rule-based) complete
- [x] **Gemini Vision TEI Generator** (E30): 3-Pass pipeline (Pilot, superseded by Unified E32)
- [x] **Dokumenttypspezifische Prompts** (E30): 4-Ebenen (Layout-Typ, Pub-Form, Genre, Sprache) in `layout_qa_gemini.py`
- [x] **Pilot Doc 2310** (E30): valides XML
- [x] **Unified TEI Pipeline** (E32): `tei_unified.py` + `tei_mapping_prompt.py` + `tei_validator.py`
- [x] **Pilot auf 3 Docs** (E32): 2310 (review), 2530 (standard), 1440 (interview) -- alle RelaxNG-valide
- [x] scripts/tei/tei_validator.py -- RelaxNG + 8 Projekt-Regeln (R1-R8)
- [x] LINE breaks (`<lb/>`) from OCR line structure (in unified Step 1)
- [x] Special document types via genre-conditional mapping table (10 genres)
- [x] **Qualitaetsfixes** (E32): Entity Re-Annotation, Prompt-Tuning, Interview-Speaker-Erkennung
- [x] Unified TEI production run -- **285/285 done** (**285/285 schema-valide** gegen zbz_hersch.rng, 29 Warnings)
- [x] Post-Assembly Fixes (tei_step3.py): pb-Duplikate (E), leere div (F), leere figure (G), heuristische lb-Injection
- [x] Schema ref-Pattern erweitert: `(GND:[0-9A-Za-z\-]+|#zbz-[a-z]+\.[0-9]+)` (Session 34)
- [x] NER Entity Integration: 285/285 Docs mit Entity-Markup (Dual-Attribut E50)
- [x] Re-Injection nach Unified-TEI-Completion: 285/285 Docs mit Entity-Markup in Unified Step 1

## Phase 5 -- Extended Evaluation

- [x] **End-to-End CER Benchmark** (E51): `benchmark_cer.py` vergleicht Pipeline-TEI vs. Referenz-TEI
- [x] Stratifizierte Analyse (Typ, Sprache, Publikationsform, Seitenumfang)
- [x] Fehlermuster-Kategorisierung (7 Kategorien) in `evaluate_ocr.py`
- [x] Proxy-Metriken fuer 260 Docs ohne Ground Truth
- [x] Dashboard-Integration (`benchmark_tei` Key in dashboard.json)
- [x] Forschungsvergleich dokumentiert: [CER-BENCHMARK](CER-BENCHMARK.md)
- [ ] Seitenweises CER-Benchmarking (pro Seite statt pro Dokument)
- [ ] Schema-Validierung x CER Kreuzanalyse
- [ ] Zielwerte: Text CER <3.5% (Median), Structural accuracy >80%, Entity P/R >80%/>70%

## Phase 6 -- Production Run (285 docs)

- [x] Process all 285 PDFs through full pipeline
- [ ] Spot-check QA: manually review 10 random documents
- [ ] Final acceptance: Doc 2310 in oXygen -> no schema errors, entities linked
- [x] Agent-Based Quality Screening Pilot: 5 Docs (290, 2310, 100, 1440, 1330), alle APPROVED_WITH_NOTES
- [x] Reassembly mit allen Fixes: 285/285 VALID (2026-03-15)
- [x] NEEDS_REVIEW Nachbearbeitung: 32 -> 0 Docs (Entity-Stopwoerter, Strukturfixes, OCR-Dedup)

---

## Querschnitt: Digitale Edition + Curation (E33/E36)

Kein sequentieller Pipeline-Schritt, sondern Praesentations- und Kurationschicht auf den Pipeline-Ergebnissen. Parallel zu den Phasen 3-6 entwickelt.

**Details:** [EDITION](EDITION.md) (Architektur, Design) | [CURATION](CURATION.md) (Server, API, Editor)

- [x] Lese-Edition: Landing, Katalog, Reader, About (E33)
- [x] Design System: Parchment/Navy/Gold, Dark Mode, Responsive
- [x] Curation Server: FastAPI, 11 API Endpoints (E36)
- [x] Text-Korrektur: WYSIWYG contenteditable + XML-Modus
- [x] Struktur-Editing: Block-Toolbar (Typ/Split/Merge/Delete)
- [x] Entity-Kuration: Markieren, Autocomplete (Entity Index + Wikidata)
- [x] Review-Workflow: Status-Badges, Publish-Endpoint
- [x] TEI-Validierung: RelaxNG im Editor
- [ ] Kurations-Durchlauf: Pilot-Docs (2310 etc.) vollstaendig kuratieren

### Agent-Based Quality Screening (E41)

Agentengestuetztes Pre-Curation-Verfahren: Claude Code prueft jedes Dokument durch 7 Schichten (Scan, OCR, Layout, Struktur, Referenz, Entities, Kohaerenz). Ergebnis: Review-JSON pro Dokument + Sweep-Summary mit systematischen Mustern.

- [x] Pilot: 5 Docs (290, 2310, 100, 1440, 1330), 6 systematische Muster (P1-P6)
- [x] Screening-Infrastruktur: tei_screening_prep.py (4 Tiers, 58 Batches), tei_add_revision.py, screening_prompt.py
- [x] revisionDesc in alle 285 TEIs injiziert (E42)
- [x] output/tei_final/ als Single Source of Truth (E43)
- [x] **Rollout: 285/285 Docs gescreent** (242 APPROVED, 43 WITH_NOTES, 0 NEEDS_REVIEW)
- [x] **Nachbearbeitung 32 NEEDS_REVIEW Docs** (E45-E47): Entity-Stopwoerter, Strukturfixes, OCR-Deduplizierung
- [ ] Vergleich Agent-Befund vs. ZBZ-Fachexpertin (Kurationspilot)

### Frontend-TODOs (separate Session)

- [ ] Datenquelle auf tei_final/ umstellen (Reader)
- [ ] Screening-Badge im Katalog (APPROVED/WITH_NOTES/NEEDS_REVIEW/grau)
- [ ] revisionDesc im Reader anzeigen (Bearbeitungshistorie)
- [ ] Curation Editor: revisionDesc beim Speichern automatisch schreiben
- [ ] docs/edition/ Duplikat klaeren (mergen oder loeschen)
- [ ] Katalog-Filter nach Screening-Status
- [ ] Publish-Workflow mit ZBZ testen

---

## Sub-Projekt: CER-Verbesserung (ab E51)

Systematische Verbesserung der OCR-Qualitaet durch iteratives Experimentieren und Benchmarken.

**Baseline:** Median CER 5.5%, Mean 9.3% (24 Docs, Maerz 2026). Details: [CER-BENCHMARK](CER-BENCHMARK.md)
**Ziel:** Median CER < 3.5%, keine Docs > 15%
**Methode:** Isolierte Experimente, jedes gemessen mit `benchmark_cer.py`
**Infrastruktur:** `scripts/benchmark_cer.py`, `scripts/evaluate_ocr.py` (Phasen A-F, Maerz 2026)

### Phase 0: Diagnostik
- [ ] Outlier-Diagnose: Pro Stufe CER messen fuer 6 Problemdocs (290, 1440, 1060, 30, 300, 1910)
- [ ] Experiment-Framework: `scripts/experiment_runner.py` fuer reproduzierbares A/B-Testing

### Phase 1: Low-Hanging Fruit
- [ ] Baseline-Korrektur: Schaerfere Zeichennormalisierung (Interpunktion, Apostrophe) in Benchmark
- [ ] Auto-Deduplizierung in Pipeline integrieren (ocr_dedup.py)
- [ ] Sprachhinweise fuer Mistral OCR-Request

### Phase 2: Gezielte Post-Korrektur
- [ ] Multimodale Gemini-Korrektur (Variante B) als Default fuer Docs mit hoher CER
- [ ] Gemini-Modell-Upgrade (flash-lite -> flash oder 2.5 Pro)
- [ ] Sprachspezifische Korrektur-Prompts

### Phase 3: Strukturelle Verbesserungen
- [ ] Seitenweises CER-Benchmarking (pro-Seite statt pro-Dokument)
- [ ] Quality-Gate zwischen Pipeline-Stufen
- [ ] Schema-Validierung x CER Kreuzanalyse als Diagnostik

### Phase 4: Fortgeschritten
- [ ] Multimodale TEI-Generierung (Bild + OCR-Text -> TEI direkt)
- [ ] Ground-Truth-Erweiterung (eng, ita, Typ C)

### Erfolgsmetriken
- Phase 1 Ziel: Median < 5.0%, Mean < 7.0%
- Phase 2 Ziel: Median < 4.0%
- Non-Regression: Kein gutes Doc (<3%) darf sich verschlechtern

### Referenzen
- Forschungskontext und Benchmark-Vergleich: [CER-BENCHMARK](CER-BENCHMARK.md)
- Offener Punkt O18 in [DECISIONS](DECISIONS.md)

---

## Data Flow

```
PDF-Scans (285 PDFs)
  |
  +---> extract_pages.py ----------> PNGs (300 DPI)
  |
  +---> ocr_pipeline.py -----------> Markdown (per page)
  |         (Mistral / DeepSeek)
  |
  +---> run_layout_analysis.py ----> Layout JSON (per page)
  |         (Docling RT-DETR V2)
  |
  +---> layout_qa_gemini.py -------> Corrected Layout JSON
  |     --mode auto (Flash Lite)
  |
  +---> page_xml_generator.py ----> PAGE-XML + METS
  |
  +---> ner/ (ner_extract +      -> Entities + Wikidata-IDs (JSON)
  |     entity_index +
  |     wikidata_linker)
  |
  +---> tei_unified.py -----------> TEI-XML (Scaffold+Gemini+Validate)
  |
  +---> ner_inject_tei.py -------> TEI-XML with Entity Markup
  |
  +---> tei_validator.py ---------> Validation Report (RelaxNG + R1-R14)
  |     --all --html-report          output/tei_unified/validation_report.html
  |
  +---> Curation Editor ----------> Curated TEI (Human-in-the-Loop)
  |     (localhost:8000)             data/tei_curated/ (Gold-Standard)
  |     Text + Struktur +            Status: draft > in_review > approved
  |     Entity-Kuration
  |
  +---> evaluate_ocr.py ----------> CER + Structure + Entity Scores
  |
  +---> generate_edition_data.py -> docs/data/catalog.json
  |
  +---> Publish -----------------> docs/data/examples/ (GitHub Pages)
```

Aktueller Status pro Stufe: siehe [PROJEKT](PROJEKT.md) §Component Status.

---

## Runtime Estimate

Kosten: siehe [PROJEKT](PROJEKT.md) §Costs.

---

## ZBZ Structural Tags (Docling -> ZBZ -> PAGE-XML)

Title, Section-header -> zb_heading / heading
Text, Paragraph, List-item, Table, Formula -> zb_paragraph / paragraph
Footnote -> footnote / footnote
Caption -> caption / caption
Page-header, Page-footer -> _filter (remove)
Picture, Figure -> _skip

---

Created: 2026-02-25 | Updated: 2026-03-15
