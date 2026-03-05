---
type: knowledge
created: 2026-02-25
updated: 2026-03-05
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
Phase 1 (Scale: Layout 286 docs + Gemini QA) --- DONE (auto-mode running)
    |
    v
Phase 2 (PAGE-XML generator) --- NEXT
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

Phase 1 -- Scale Layout (286 docs): Docling layout on all 4,152 pages (E24 docling-serve, E20 local GPU RTX 4060 ~5s/page). Gemini QA (E25) + Detect (E26) with auto-routing. Viewer integration with Docling/Gemini toggle. Quality: 75% good, 10% warning, 12% bad, 3% empty. Auto-mode running on all 286 docs.

Open from Phase 1:
- [ ] Gemini auto-mode: complete run on all 286 docs (847/4,152 pages done)
- [ ] Prompt tuning: rightmost column missed on wide landscapes, picture detection weak

---

## Next: Phase 2 -- PAGE-XML Generator

- [ ] scripts/layout/page_xml_generator.py -- LayoutRegion + OCR text -> PAGE-XML
- [ ] scripts/layout/mets_generator.py -- METS manifest (images + PAGE-XML)
- [ ] Schema: PAGE-XML 2013-07-15 (Transkribus standard)
- [ ] ID scheme: facs_{NN}_r_{N} / facs_{NN}_r_{N}_tl_{M}
- [ ] Validate against XSD schema
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

Prerequisite: Phase 2 + Phase 3.
Current: 383 TEI-XML files (E22, layout+OCR -> TEI directly).

- [ ] scripts/tei/tei_header.py -- teiHeader skeleton (title, publisher, language)
- [ ] scripts/tei/tei_validator.py -- Schema validation + ZBZ content rules
- [ ] Integrate NER entities from Phase 3
- [ ] PAGE-XML as alternative input
- [ ] Special document types: reviews, interviews, lexicon, monographs

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
  +---> ocr_pipeline.py ----------> Markdown (per page)             [DONE: 15 pilot]
  |         (Mistral / DeepSeek)
  |
  +---> run_layout_analysis.py --> Layout JSON (per page)           [DONE: 286/286]
  |         (Docling RT-DETR V2)
  |
  +---> layout_qa_gemini.py -----> Corrected Layout JSON            [IN PROGRESS]
  |     --mode auto (Flash Lite)   (qa for good, detect for bad)
  |
  +---> page_xml_generator.py --> PAGE-XML + METS                   [NEXT]
  |
  +---> ner_pipeline.py -------> Entities + GND-IDs (JSON)          [PENDING]
  |
  +---> tei_generator.py ------> TEI-XML (DTA-Basisformat)         [PARTIAL: 15 pilot]
  |
  +---> evaluate_ocr.py -------> CER + Structure + Entity Scores   [DONE for pilot]
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

Created: 2026-02-25 | Updated: 2026-03-05
