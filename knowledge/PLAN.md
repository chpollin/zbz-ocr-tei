---
type: knowledge
created: 2026-02-25
updated: 2026-03-03
tags: [zbz-ocr-tei, plan, implementation, phases, checklist]
status: active
---

# Implementation Plan: Full AI Pipeline (PDF -> TEI-XML)

> **Version:** 2.0 | **Date:** 03.03.2026 | **Author:** Claude Opus 4.6
> **Context:** zbz-ocr-tei covers the entire pipeline. ZBZ retains Transkribus, DHCraft builds a parallel AI pipeline.

Current component status: [PROJEKT.md](PROJEKT.md) §Component Status.
Pipeline stages and CLI: [PIPELINE.md](PIPELINE.md).

---

## Phase Overview

| Phase | Description | Status |
|-------|-------------|--------|
| 0 | Layout evaluation (E19/E20) | **Done** |
| 0b | Image extraction (all 286 PDFs) | **Done** |
| 0c | OCR pilot (15 docs) | **Done** |
| 0d | TEI-XML pilot (15 docs) | **Done** |
| 0e | Data delivery E23 | **Done** |
| 1a | docling-serve integration (E24) | **Done** |
| 1b | Layout analysis (286 docs) | **In progress** (11/286) |
| 1c | Gemini Layout QA (E25) | **Done** (script ready, tested on 2310) |
| 1d | Cloud GPU for layout analysis | **Next step** |
| 2 | Layout post-processing (O21) | Pending |
| 3 | PAGE-XML generator | Pending |
| 4 | NER + GND linking | Pending |
| 5 | TEI-XML generator extension | Partial (383 files, E22) |
| 6 | Extended evaluation + dashboard | Pending |
| 7 | Production run (286 docs) | Pending |

```
Phase 0 (Pilot: Layout-Eval + OCR + TEI) --- DONE
    |
    v
Phase 1 (Scale: Layout 286 docs + Gemini QA) --- IN PROGRESS
    |
    v
Phase 2 (Post-processing: overlap, page numbers, headers)
    |
    v
Phase 3 (PAGE-XML generator)  -----> Phase 4 (NER + GND)
                                        |
                                        v
                                   Phase 5 (TEI-XML extend)
                                        |
                                        v
                                   Phase 6 (Evaluation + Dashboard)
                                        |
                                        v
                                   Phase 7 (Production: 286 Docs)
```

Phase 3 and Phase 4 can be developed in parallel (NER only needs OCR text, not PAGE-XML). Phase 5 requires both.

---

## Master Checklist

### Infrastructure + Setup

- [x] Git repository initialized
- [x] `.gitignore` configured (`.env`, `output/`, `data/`, caches)
- [x] `.env.example` with all API keys (Mistral, Anthropic, Docling-Serve, Gemini)
- [x] `requirements.txt` maintained
- [x] `scripts/config.py` central configuration
- [x] Knowledge vault: 14 documents in `knowledge/`
- [x] Dashboard + Viewer UI (`docs/`)

### Phase 0: Pilot (15 docs) --- DONE

- [x] **E19/E20:** Layout evaluation — Docling 2.75 confirmed (5 type samples)
- [x] **Image extraction:** 286 PDFs -> 4,152 PNGs (300 DPI) via `extract_pages.py`
- [x] **OCR:** 15 pilot docs with Mistral Document AI, CER 6.42%
- [x] **LLM post-correction:** Tested, made optional (E17, worsens docs <5% CER)
- [x] **TEI-XML:** 15/15 docs, 383 TEI-XML files (E22, DTA-Basisformat)
- [x] **Evaluation:** CER/WER per page, HTML diff reports
- [x] **Dashboard:** Metrics, engine comparison, document catalog
- [x] **E23 Data delivery:** 286 PDFs + 25 reference TEI + 24 PAGE-XML received

### Phase 1: Scale Layout Analysis (286 docs) --- IN PROGRESS

#### 1a: docling-serve integration (E24) --- DONE

- [x] `scripts/run_layout_cloud.py` created (~150 lines)
- [x] Docker container `docling-serve-cpu` tested
- [x] Same Docling RT-DETR V2 model, identical output format
- [x] Config: `DOCLING_SERVE_URL` in `scripts/config.py`
- [x] `.env.example` updated with `DOCLING_SERVE_URL`

#### 1b: Layout analysis progress --- IN PROGRESS

- [x] 11/286 docs analyzed (98 layout JSONs)
- [ ] Remaining 275 docs (CPU too slow: ~27s/page = ~31h for 4,100 pages)
- [ ] **Cloud GPU needed** — options: Colab, Modal, RunPod, GCP

#### 1c: Gemini Layout QA (E25) --- DONE (script ready)

- [x] `scripts/layout_qa_gemini.py` created (~200 lines)
- [x] Gemini 3.1 Flash Lite Preview (Vision + Structured Output)
- [x] Aggressive prompt: catches page numbers, running headers, logos, JSTOR metadata
- [x] SDK: `google-genai` (new SDK), `response_mime_type="application/json"`
- [x] Schema fix: `"nullable": True` instead of `["object", "null"]`
- [x] Output: `_layout_gemini.json` alongside Docling original (epistemic infrastructure)
- [x] Summary: `summary_gemini.json` per document
- [x] Resume-capable, `--doc`, `--force` flags
- [x] Tested on Doc 2310: Score 80, 26 corrections (logos, headers, JSTOR filtered)
- [ ] Run on all docs with layout (once layout analysis progresses)

#### 1d: Viewer integration --- DONE

- [x] `shared.js`: `fetchLayoutData(docId, page, source)` with docling/gemini parameter
- [x] `viewer.html`: Layout-source dropdown (Docling/Gemini)
- [x] Changed regions: yellow dashed border, `*` prefix, change_reason in tooltip
- [x] Keyboard shortcuts removed (cleaner UI)

#### 1e: Cloud GPU for layout analysis --- NEXT STEP

- [ ] Choose cloud GPU platform (Colab / Modal / RunPod / GCP)
- [ ] Upload/mount PDF scans + PNGs
- [ ] Run `run_layout_cloud.py` or `run_layout_analysis.py` with GPU
- [ ] Expected: ~2-3s/page with GPU = ~2-3h for 4,100 pages
- [ ] Download results to `output/layout/`

### Phase 2: Layout Post-Processing (O21) --- PENDING

> **Blocker:** O21 (overlap, single-liners, page numbers)

- [ ] Overlap resolution: merge overlapping regions
- [ ] Single-liner handling: fragments to nearest region
- [ ] Page number detection: small regions at top/bottom -> page_header/page_footer
- [ ] Running header detection: repeated text at top -> page_header
- [ ] Note: Gemini QA (E25) already catches many of these — evaluate overlap

### Phase 3: PAGE-XML Generator --- PENDING

> **Prerequisite:** Phase 2 done

- [ ] `scripts/layout/page_xml_generator.py` — LayoutRegion + OCR text -> PAGE-XML
- [ ] `scripts/layout/mets_generator.py` — METS manifest (images + PAGE-XML)
- [ ] Schema: PAGE-XML 2013-07-15 (Transkribus standard)
- [ ] ID scheme: `facs_{NN}_r_{N}` / `facs_{NN}_r_{N}_tl_{M}`
- [ ] Validate against XSD schema
- [ ] Transkribus import test (if access available)

### Phase 4: NER + GND Linking --- PENDING

> **Prerequisite:** OCR text exists (independent of PAGE-XML)

- [ ] `scripts/ner/ner_pipeline.py` — LLM-based NER (Claude Haiku 4.5)
- [ ] `scripts/ner/gnd_linker.py` — Seed lookup + lobid.org API
- [ ] `scripts/ner/entity_store.py` — Per-document JSON registry
- [ ] Entity types: person, organization, work
- [ ] GND linking: 75 seed entities + lobid.org REST API
- [ ] Targets: Recall >70%, Precision >80%, GND linking >60%, GND correctness >90%

### Phase 5: TEI-XML Generator Extension --- PARTIAL

> **Current:** 383 TEI-XML files generated (E22, layout+OCR -> TEI directly)
> **Open:** PAGE-XML input, NER entities, schema validation

- [x] `scripts/tei/tei_generator.py` — basic TEI from layout JSON + OCR Markdown
- [x] Entity annotation from seed dict (KNOWN_ENTITIES)
- [ ] `scripts/tei/tei_header.py` — teiHeader skeleton (title, publisher, language)
- [ ] `scripts/tei/tei_validator.py` — Schema validation + ZBZ content rules
- [ ] Integrate NER entities from Phase 4
- [ ] PAGE-XML as alternative input
- [ ] Special document types: reviews, interviews, lexicon, monographs

### Phase 6: Extended Evaluation + Dashboard --- PENDING

> **Prerequisite:** Phase 5 completed

- [ ] `evaluate_ocr.py` new mode `--mode tei`: text CER + structural accuracy + entity scores
- [ ] `generate_dashboard_data.py` extended with page_xml, entities, tei_xml stages
- [ ] `docs/index.html` new "TEI Pipeline" section
- [ ] Metrics: Text CER <7%, Structural accuracy >80%, Entity P/R >80%/>70%

### Phase 7: Production Run (all 286 docs) --- PENDING

> **Prerequisite:** Phase 6 completed, metrics achieved

- [ ] Process all 286 PDFs through full pipeline
- [ ] Run evaluation on full corpus
- [ ] Update dashboard
- [ ] Spot-check QA: manually review 10 random documents
- [ ] Document results in TESTPLAN.md and JOURNAL.md

---

## Data Flow (Current State)

```
PDF-Scans (286 PDFs, E23)
  |
  +---> extract_pages.py ---------> 4,152 PNGs (300 DPI)     [DONE: 286/286]
  |                                    |
  +---> ocr_pipeline.py ----------> Markdown (per page)       [DONE: 15/286 pilot]
  |         (Mistral Doc AI)           |
  |                                    |
  +---> run_layout_analysis.py --> Layout JSON (per page)     [IN PROGRESS: 11/286]
  |     run_layout_cloud.py            |
  |         (Docling RT-DETR V2)       |
  |                                    |
  +---> layout_qa_gemini.py -----> Corrected Layout JSON      [READY: tested on 2310]
            (Gemini 3.1 Flash Lite)    |
                                       |
            [PENDING BELOW]            |
                                       v
          layout_postprocess.py --> Clean regions (O21)
                    |
                    v
          page_xml_generator.py --> PAGE-XML + METS
                    |
                    v
          ner_pipeline.py -------> Entities (JSON)
          gnd_linker.py ---------> GND-IDs (JSON)
                    |
                    v
          tei_generator.py ------> TEI-XML (DTA-Basisformat)  [PARTIAL: 15/286 pilot]
                    |
                    v
          evaluate_ocr.py -------> CER + Structure + Entity Scores
          generate_dashboard_data.py --> Dashboard             [DONE for pilot]
```

---

## Scripts Inventory

| Script | Purpose | Status |
|--------|---------|--------|
| `scripts/extract_pages.py` | PDF -> PNG images | Production |
| `scripts/ocr_pipeline.py` | OCR (Mistral/DeepSeek) | Production |
| `scripts/llm_postprocess.py` | LLM post-correction (Haiku) | Production (optional) |
| `scripts/run_layout_analysis.py` | Layout via local Docling | Production |
| `scripts/run_layout_cloud.py` | Layout via docling-serve API | Production |
| `scripts/layout_qa_gemini.py` | Gemini QA correction | Production |
| `scripts/tei/tei_generator.py` | Layout+OCR -> TEI-XML | Production (basic) |
| `scripts/evaluate_ocr.py` | CER/WER evaluation | Production |
| `scripts/generate_dashboard_data.py` | Dashboard data | Production |
| `scripts/extract_gnd.py` | GND seed extraction | Production |
| `scripts/test_all_pdfs.py` | Systematic OCR testing | Production |
| `scripts/postprocess/pipeline.py` | Post-processing chain | Production |
| `scripts/layout/page_xml_generator.py` | PAGE-XML generator | **Not yet created** |
| `scripts/layout/mets_generator.py` | METS manifest | **Not yet created** |
| `scripts/ner/ner_pipeline.py` | LLM-based NER | **Not yet created** |
| `scripts/ner/gnd_linker.py` | GND linking | **Not yet created** |
| `scripts/tei/tei_header.py` | teiHeader generator | **Not yet created** |
| `scripts/tei/tei_validator.py` | TEI validation | **Not yet created** |

---

## API Keys (in .env)

| Key | Purpose | Status |
|-----|---------|--------|
| `MISTRAL_DOC_AI_KEY` | OCR (Mistral Document AI) | Available |
| `ANTHROPIC_API_KEY` | LLM correction + NER | Available |
| `DOCLING_SERVE_URL` | docling-serve API (layout) | Available (localhost) |
| `GEMINI_API_KEY` | Gemini Layout QA (E25) | Available |

---

## Runtime Estimate (Production, 286 docs / ~4,100 pages)

| Stage | Per Page | Total | Cost |
|-------|----------|-------|------|
| Image extraction | <1s | ~1h | $0 |
| OCR (Mistral) | ~1s | ~1.5h | ~$14 |
| Layout (Docling, GPU) | ~2-3s | ~3h | Cloud GPU cost |
| Layout (Docling, CPU) | ~27s | ~31h | $0 |
| Gemini QA | ~4s | ~5h | ~$4 |
| NER (Haiku 4.5) | ~0.5s | ~1h | ~$5 |
| TEI transformation | ~0.1s | ~7min | $0 |
| **Total (GPU path)** | | **~11h** | **~$25 + GPU** |

---

## ZBZ Structural Tags (Mapping Docling -> ZBZ)

| Docling BlockType | ZBZ Structural Tag | PAGE-XML TextRegion/@type | zbz_tag |
|-------------------|--------------------|--------------------------|---------|
| Title | zb_heading | heading | zb_heading |
| Section-header | zb_heading | heading | zb_heading |
| Text / Paragraph | zb_paragraph | paragraph | zb_paragraph |
| List-item | zb_paragraph | paragraph | zb_paragraph |
| Table / Formula | zb_paragraph | paragraph | zb_paragraph |
| Footnote | footnote | footnote | footnote |
| Caption | caption | caption | caption |
| Page-header | _filter | - | _filter |
| Page-footer | _filter | - | _filter |
| Picture / Figure | _skip | - | _skip |

---

## Risks

See [DECISIONS.md](DECISIONS.md) §Risks.

---

## Verification per Phase

After each phase:
1. **Automated tests:** Schema validation, CER comparison, unit tests
2. **Manual spot-check:** 2-3 pilot documents (1x Type A, 1x Type B, 1x Type C/D)
3. **Documentation:** Results in TESTPLAN.md and JOURNAL.md
4. **Decisions:** New E-numbers in DECISIONS.md

**Final acceptance test:** Open generated TEI for Doc 2310 in oXygen -> no schema errors, entities correctly linked.

---

*Created: 25.02.2026 | Updated: 03.03.2026 (v2.0: comprehensive checklist, current state documented)*
