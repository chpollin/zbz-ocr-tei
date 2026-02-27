---
type: knowledge
created: 2026-02-25
updated: 2026-02-27
tags: [zbz-ocr-tei, plan, implementation, phases]
status: active
---

# Implementation Plan: Full AI Pipeline (PDF → TEI-XML)

> **Version:** 1.2 | **Date:** 27.02.2026 | **Author:** Claude Opus 4.6
> **Context:** zbz-ocr-tei covers the entire pipeline. ZBZ retains Transkribus, DHCraft builds a parallel AI pipeline.

Current component status: [PROJEKT.md](PROJEKT.md) §Component Status.
Pipeline stages and CLI: [PIPELINE.md](PIPELINE.md).

---

## Phase Overview

| Phase | Description | Status |
|-------|-------------|--------|
| 0 | Layout evaluation (E19/E20) | **Done** — Docling confirmed, 8/15 docs analyzed |
| 1 | Layout post-processing + PAGE-XML generator | **Next step** |
| 2 | NER + GND linking | Pending |
| 3 | TEI-XML generator extension | Partial (383 files generated, E22) |
| 4 | Extended evaluation + dashboard | Pending |
| 5 | Production run (289 docs) | Pending |

```
Phase 0 (Layout-Eval) ✓
    |
    v
Phase 1 (Layout + PAGE-XML) -----> Phase 2 (NER + GND)
                                        |
                                        v
                                   Phase 3 (TEI-XML extend)
                                        |
                                        v
                                   Phase 4 (Evaluation + Dashboard)
                                        |
                                        v
                                   Phase 5 (Production: 289 Docs)
```

Phase 1 and Phase 2 can be developed in parallel (NER only needs OCR text, not PAGE-XML). Phase 3 requires both.

---

## Target Data Flow

```
PDF-Scan
  |
  +---> extract_pages.py -----> PNG images (300 DPI)
  |                                |
  +---> ocr_pipeline.py -----> Markdown (per page)
  |                                |
  +---> layout_analyzer.py --> Regions + BBox (JSON)
           |                       |
           +--- region_classifier.py --> ZBZ tags
                    |
                    v
          page_xml_generator.py --> PAGE-XML (per page) + METS
                    |
                    v
          ner_pipeline.py -------> Entities (JSON)
          gnd_linker.py ---------> GND-IDs (JSON)
                    |
                    v
          tei_generator.py ------> TEI-XML (DTA-Basisformat)
                    |
                    v
          evaluate_ocr.py -------> CER + Structure + Entity Scores
          generate_dashboard_data.py --> Dashboard
```

---

## Phase 1: Layout Post-Processing + PAGE-XML Generator

> **Effort:** 3-4 days
> **Prerequisite:** Phase 0 done (E19/E20 finalized)
> **Blocker:** O21 (Layout post-processing: overlap, single-liners, page numbers)

### New Files

```
scripts/layout/
  __init__.py
  layout_analyzer.py       # Page images → LayoutRegion list
  region_classifier.py     # Docling block types → ZBZ tags
  page_xml_generator.py    # LayoutRegion + OCR text → PAGE-XML
  mets_generator.py        # METS-Manifest (Images + PAGE-XML)
```

### ZBZ Structural Tags (Mapping Docling → ZBZ)

| Docling BlockType | ZBZ Structural Tag | PAGE-XML TextRegion/@type | @custom |
|-------------------|--------------------|--------------------------|---------|
| Title | zb_heading | heading | `structure {type:zb_heading;}` |
| Section-header | zb_heading | heading | `structure {type:zb_heading;}` |
| Text / Paragraph | zb_paragraph | paragraph | `structure {type:zb_paragraph;}` |
| Footnote | footnote | footnote | `structure {type:footnote;}` |
| Page-header | (filter out) | - | - |
| Page-footer | (filter out) | - | - |
| Caption | caption | caption | `structure {type:caption;}` |
| (infer spacing) | zb_space | other | `structure {type:zb_space;}` |

### ID Schema (Transkribus-compatible)

```
Page:    {doc_id}_p{NN:03d}.xml
Region:  id="facs_{NN}_r_{N}"    → TEI: <p facs="#facs_{NN}_r_{N}">
Line:    id="facs_{NN}_r_{N}_tl_{M}" → TEI: <lb facs="#facs_{NN}_r_{N}_tl_{M}">
```

### Output Structure

```
output/page_xml/{doc_id}/
  mets.xml                    # METS-Manifest
  images/{doc_id}_p001.png    # Page images (symlink or copy)
  page/{doc_id}_p001.xml      # PAGE-XML per page
```

### PAGE-XML Template

```xml
<?xml version="1.0" encoding="UTF-8"?>
<PcGts xmlns="http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15"
       xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
       xsi:schemaLocation="http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15
                           http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15/pagecontent.xsd">
  <Metadata>
    <Creator>zbz-ocr-tei pipeline</Creator>
    <Created>2026-02-25T00:00:00</Created>
  </Metadata>
  <Page imageFilename="../images/{doc_id}_p001.png"
        imageWidth="{width}" imageHeight="{height}">
    <TextRegion id="facs_1_r_1" type="paragraph"
                custom="structure {type:zb_paragraph;}">
      <Coords points="{x1},{y1} {x2},{y1} {x2},{y2} {x1},{y2}"/>
      <TextLine id="facs_1_r_1_tl_1">
        <Coords points="..."/>
        <TextEquiv>
          <Unicode>OCR text of this line</Unicode>
        </TextEquiv>
      </TextLine>
    </TextRegion>
  </Page>
</PcGts>
```

### New Config Constants

```python
# Layout + PAGE-XML
PAGE_XML_DIR = OUTPUT_DIR / "page_xml"
PAGE_XML_NAMESPACE = "http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15"

ZBZ_STRUCTURAL_TAGS = {
    "zb_heading": {"page_type": "heading"},
    "zb_paragraph": {"page_type": "paragraph"},
    "zb_space": {"page_type": "other"},
    "zb_type_document": {"page_type": "other"},
    "footnote": {"page_type": "footnote"},
    "page-number": {"page_type": "page-number"},
    "caption": {"page_type": "caption"},
}

# Confidence-Mapping
CONFIDENCE_MISTRAL_RAW = 0.85
CONFIDENCE_LLM_CORRECTED = 0.95
```

### Validation

1. Validate PAGE-XML against XSD schema (download schema from primaresearch.org)
2. Visual spot-check: 3 documents (1x Type A, 1x Type B, 1x Type C)
3. Transkribus import test (if access available)

---

## Phase 2: NER + GND Linking

> **Effort:** 2-3 days
> **Prerequisite:** Phase 1 completed (PAGE-XML exists)

### New Files

```
scripts/ner/
  __init__.py
  ner_pipeline.py    # LLM-based NER (Claude Haiku 4.5)
  gnd_linker.py      # Two-stage: seed lookup → lobid.org API
  entity_store.py    # Per-document JSON registry
```

### Approach

1. **NER via Claude Haiku 4.5:** JSON output with `{text, type, start_char, end_char}`
   - Types: person, organization, work
   - Page-level or paragraph-level processing
   - Prompt with context (Jeanne Hersch, philosophy, 20th century)

2. **GND Linking Phase 1 (Seed):** Exact + fuzzy match against 75 known entities
   - `config.py:KNOWN_ENTITIES` (11 entries) + `output/gnd_analysis/gnd_entities.json` (75 entries)
   - rapidfuzz for fuzzy matching (already in requirements.txt)

3. **GND Linking Phase 2 (lobid.org):** REST API for unknown entities
   - `https://lobid.org/gnd/search?q={name}&filter=type:Person`
   - Cache + rate limiting (max 10 req/s)
   - Result: GND-ID + confidence

4. **Output:** `output/entity_registry/{doc_id}_entities.json`

### Evaluation Criteria

| Metric | Target |
|--------|--------|
| Entity Recall | >70% (against reference TEI) |
| Entity Precision | >80% |
| GND linking rate | >60% of recognized entities |
| GND correctness | >90% of linked entities |

---

## Phase 3: TEI-XML Generator Extension

> **Status:** PARTIALLY IMPLEMENTED (E22)
> **Implemented:** `scripts/tei/tei_generator.py` — 383 TEI-XML files from layout JSON + OCR Markdown. Entity annotation from seed dict.
> **Open:** PAGE-XML as input, NER entities from Phase 2, schema validation, tei_header.py, tei_validator.py
> **Remaining effort:** 2-3 days (after Phase 1+2)

### Still to Create

```
scripts/tei/
  tei_header.py       # teiHeader skeleton (title, publisher, language)
  tei_validator.py    # Schema validation + ZBZ content rules
```

Transformation rules: [TEI-MAPPING.md](TEI-MAPPING.md).

### Special Document Types

| Type | Docs | TEI Specifics |
|------|------|---------------|
| Review | 2310 | `<div type="review">` + `<bibl>` in `<head>` |
| Interview | 1440 | `<sp>/<speaker>` for speaker changes |
| Lexicon | 3040 | `<div type="entry">` + `<head type="lemma">` |
| Monograph | 40, 1520 | Chapters → `<div n="1">`, sections → `<div n="2">` |

### Validation

1. Validate TEI against DTA-Basisformat schema
2. Compare with reference TEI (15 pilot docs): structural agreement
3. Spot-check in oXygen XML Editor: no fatal schema errors

---

## Phase 4: Extended Evaluation + Dashboard

> **Effort:** 2 days
> **Prerequisite:** Phase 3 completed

| File | Change |
|------|--------|
| `scripts/evaluate_ocr.py` | New mode `--mode tei`: text CER + structural accuracy + entity scores |
| `scripts/generate_dashboard_data.py` | Pipeline status extended with 3 new stages (page_xml, entities, tei_xml) |
| `docs/index.html` | New "TEI Pipeline" section with 7-stage display |

### New Metrics

| Metric | Target |
|--------|--------|
| Text CER | <7% (currently 6.42%) |
| Structural accuracy (ZBZ tags) | >80% |
| Entity Precision / Recall | >80% / >70% |
| GND correctness | >90% |
| TEI validity | 100% |

---

## Phase 5: Production Run (all 289 documents)

> **Effort:** 2-3 days (incl. monitoring + rework)
> **Prerequisite:** Phase 4 completed, metrics achieved

### Runtime Estimate

| Stage | Per Page | 7,200 Pages | Cost |
|-------|----------|-------------|------|
| OCR (Mistral) | ~1s | ~2h | $14.40 |
| Layout (Docling, CPU) | ~1s | ~2h | $0 |
| NER (Haiku 4.5) | ~0.5s | ~1h | ~$5 |
| GND (lobid.org) | ~0.1s | Cache-efficient | $0 |
| TEI transformation | ~0.1s | ~12min | $0 |
| **Total** | | **~6h** | **~$20** |

### Procedure

1. Process all 289 PDFs through stages 1-6 (batch mode)
2. Run evaluation on full corpus
3. Update dashboard
4. Spot-check QA: manually review 10 random documents
5. Document results in TESTPLAN.md and JOURNAL.md

---

## Dependencies

### Python Packages

```
docling>=2.75.0               # Layout analysis (already installed)
# anthropic, rapidfuzz, lxml, requests -- already available
```

### API Keys (in .env)

| Key | Purpose | Status |
|-----|---------|--------|
| `MISTRAL_DOC_AI_KEY` | OCR | Available |
| `ANTHROPIC_API_KEY` | LLM correction + NER | Available |
| `GOOGLE_API_KEY` | Gemini (optional) | Missing (not blocking) |

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

**Final acceptance test:** Open generated TEI for Doc 2310 in oXygen → no schema errors, entities correctly linked.

---

*Created: 25.02.2026 | Updated: 27.02.2026 (moved to knowledge/, internal refs updated, v1.2)*
