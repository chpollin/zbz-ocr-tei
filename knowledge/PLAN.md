---
type: knowledge
created: 2026-02-25
updated: 2026-03-06
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

Phase 0 -- Pilot (15 docs): Layout evaluation (E19/E20), image extraction (4,152 PNGs), OCR (Mistral, CER 6.42%), LLM correction tested and made optional (E17), TEI-XML (383 files, E22), evaluation + dashboard, data delivery (E23: 286 PDFs + 25 TEI + 24 PAGE-XML).

Phase 1 -- Scale Layout (286 docs): Docling layout on all 4,152 pages (E24 docling-serve, E20 local GPU RTX 4060 ~5s/page). Gemini QA (E25) + Detect (E26) with auto-routing (E31: full run completed). Viewer integration with Docling/Gemini toggle. Quality: 75% good, 10% warning, 12% bad, 3% empty. Full run: 3,992 pages processed, 14,708 corrections, 894 ADDED regions. Overlay generator: 7,988 PNGs.

Open from Phase 1:
- [x] Gemini auto-mode: complete run on all 286 docs (3,992/4,152 pages, 160 failed)
- [ ] Prompt tuning: rightmost column missed on wide landscapes, picture detection weak

---

## Completed: Phase 2 -- PAGE-XML Generator

- [x] scripts/layout/page_xml_generator.py -- LayoutRegion + OCR text -> PAGE-XML
- [x] scripts/layout/mets_generator.py -- METS manifest (PAGE-XML refs)
- [x] Schema: PAGE-XML 2013-07-15 (Transkribus standard)
- [x] ID scheme: r_{N} / r_{N}_tl_1 (region-level, 1 TextLine per region)
- [x] Production: 286 docs, 4,091 PAGE-XML + 286 METS
- [ ] Validate against XSD schema (optional)
- [ ] Transkribus import test (if access available)

## Phase 3 -- NER + GND Linking

Prerequisite: OCR text exists (independent of PAGE-XML).

- [ ] scripts/ner/ner_pipeline.py -- LLM-based NER (Claude Haiku 4.5)
- [ ] scripts/ner/gnd_linker.py -- Seed lookup + lobid.org API
- [ ] scripts/ner/entity_store.py -- Per-document JSON registry
- [ ] Entity types: person, organization, work
- [ ] GND linking: 75 seed entities + lobid.org REST API
- [ ] Targets: Recall >70%, Precision >80%, GND linking >60%, GND correctness >90%

## Phase 4 -- TEI-XML Extension

Prerequisite: Phase 3 (NER) for full entities; Gemini Vision TEI works independently.
Current: Rule-based generator (4,117 TEI-XML, 285 docs, flat structure). Gemini Vision TEI (E30): Pilot Doc 2310 successful.

- [x] teiHeader with real title, author, date from doc_metadata.json
- [x] OCR source priority: Gemini B > Gemini A > LLM C > Mistral
- [x] Language mapping: ISO 639-3 + legacy 2-letter fallback
- [x] Production (rule-based): 285 docs, 4,117 TEI-XML files
- [x] **Gemini Vision TEI Generator** (E30): `scripts/tei/tei_gemini.py`, 3-Pass pipeline
- [x] **Dokumenttypspezifische Prompts** (E30): 4-Ebenen (Layout-Typ, Pub-Form, Genre, Sprache) in `layout_qa_gemini.py` + `tei_gemini.py`
- [x] **Pilot Doc 2310** (E30): persName/bibl/lb/div Recall 1.0, valides XML
- [x] **Unified TEI Pipeline** (E32): `tei_unified.py` + `tei_mapping_prompt.py` + `tei_validator.py`
- [x] **Pilot auf 3 Docs** (E32): 2310 (review), 2530 (standard), 1440 (interview) -- alle RelaxNG-valide
- [x] scripts/tei/tei_validator.py -- RelaxNG + 8 Projekt-Regeln (R1-R8)
- [x] LINE breaks (`<lb/>`) from OCR line structure (in unified Step 1)
- [x] Special document types via genre-conditional mapping table (10 genres)
- [x] **Qualitaetsfixes** (E32): Entity Re-Annotation, Prompt-Tuning, Interview-Speaker-Erkennung
- [ ] Unified TEI production run (286 docs, ~$17) -- **RUNNING**
- [ ] Integrate NER entities from Phase 3

## Phase 5 -- Extended Evaluation

- [ ] evaluate_ocr.py new mode --mode tei: text CER + structural accuracy + entity scores
- [ ] Dashboard extended with page_xml, entities, tei_xml stages
- [ ] Metrics: Text CER <7%, Structural accuracy >80%, Entity P/R >80%/>70%

## Phase 6 -- Production Run (286 docs)

- [ ] Process all 286 PDFs through full pipeline
- [ ] Spot-check QA: manually review 10 random documents
- [ ] Final acceptance: Doc 2310 in oXygen -> no schema errors, entities linked

---

## Data Flow

```
PDF-Scans (286 PDFs)
  |
  +---> extract_pages.py ---------> 4,152 PNGs (300 DPI)           [DONE]
  |
  +---> ocr_pipeline.py ----------> Markdown (per page)             [DONE: 286/286]
  |         (Mistral / DeepSeek)
  |
  +---> run_layout_analysis.py --> Layout JSON (per page)           [DONE: 286/286]
  |         (Docling RT-DETR V2)
  |
  +---> layout_qa_gemini.py -----> Corrected Layout JSON            [DONE: 286 docs, 3,992 pages]
  |     --mode auto (Flash Lite)   (3,519 qa + 633 detect)
  |
  +---> page_xml_generator.py --> PAGE-XML + METS                   [DONE: 286 docs, 4,091 pages]
  |
  +---> ner_pipeline.py -------> Entities + GND-IDs (JSON)          [PENDING]
  |
  +---> tei_generator.py ------> TEI-XML (rule-based, flat)         [DONE: 285 docs, 4,117 files]
  |
  +---> tei_gemini.py --------> TEI-XML (3-Pass, Gemini Vision)    [PILOT: Doc 2310, E30]
  |
  +---> tei_unified.py -------> TEI-XML (Scaffold+Gemini+Validate) [PILOT: 3 docs, E32]
  |
  +---> evaluate_ocr.py -------> CER + Structure + Entity Scores   [DONE for pilot]
  |
  +---> generate_edition_data.py -> docs/edition/data/catalog.json  [DONE: E33]
```

---

## Runtime Estimate (286 docs, ~4,100 pages)

Full pipeline GPU path: ~11h, ~$25.
Breakdown: Images <1h/$0, OCR ~1.5h/~$14, Layout ~5.5h/$0, Gemini ~7h/~$5, NER ~1h/~$5, TEI ~7min/$0.

---

## ZBZ Structural Tags (Docling -> ZBZ -> PAGE-XML)

Title, Section-header -> zb_heading / heading
Text, Paragraph, List-item, Table, Formula -> zb_paragraph / paragraph
Footnote -> footnote / footnote
Caption -> caption / caption
Page-header, Page-footer -> _filter (remove)
Picture, Figure -> _skip

---

Created: 2026-02-25 | Updated: 2026-03-06
