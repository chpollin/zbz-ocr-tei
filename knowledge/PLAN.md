---
type: knowledge
created: 2026-02-25
updated: 2026-03-09
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
Phase 1 (Scale: Layout 286 docs + Gemini QA) --- DONE
    |
    v
Phase 2 (PAGE-XML generator) --- DONE (286 docs, 4,091 pages)
    |
    v
Phase 3 (NER + GND)  <-- can run parallel with Phase 2
    |
    v
Phase 4 (TEI-XML extend with PAGE-XML + NER)
    |
    v
Phase 5 (Evaluation + Dashboard extension)
    |
    v
Phase 6 (Production: 286 Docs)
```

---

## Completed

Phase 0 -- Pilot (15 docs): Layout evaluation (E19/E20), image extraction, OCR (Mistral, E6), LLM correction tested and made optional (E17), TEI-XML (E22), evaluation + dashboard, data delivery (E23).

Phase 1 -- Scale Layout (286 docs): Docling layout (E24 docling-serve, E20 local GPU). Gemini QA (E25) + Detect (E26) with auto-routing (E31: full run completed). Viewer integration with Docling/Gemini toggle. Overlay generator.

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
- [x] NER Production Run: 285/286 Docs, 11,685 Entities, 26,197 Mentions (E35)
- [x] Entity Index Merge: 4,100 Eintraege (person 1,979, org 698, place 661, work 762)
- [x] TEI Injection Production: 49/286 Docs mit Entity-Markup (alle 10 geprueft VALID)
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
- [ ] Unified TEI production run -- **100/286 done** (restliche 185 Docs, ~$55 Gemini)
- [x] NER Entity Integration: 49/286 Docs mit Entity-Markup (`output/tei_ner/`)
- [ ] Re-Injection nach Unified-TEI-Completion fuer alle 286 Docs

## Phase 5 -- Extended Evaluation

- [ ] evaluate_ocr.py new mode --mode tei: text CER + structural accuracy + entity scores
- [ ] Dashboard extended with page_xml, entities, tei_xml stages
- [ ] Zielwerte: Text CER <7%, Structural accuracy >80%, Entity P/R >80%/>70%

## Phase 6 -- Production Run (286 docs)

- [ ] Process all 286 PDFs through full pipeline
- [ ] Spot-check QA: manually review 10 random documents
- [ ] Final acceptance: Doc 2310 in oXygen -> no schema errors, entities linked

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
- [ ] Publish-Workflow mit ZBZ testen

---

## Data Flow

```
PDF-Scans (286 PDFs)
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

Created: 2026-02-25 | Updated: 2026-03-09
