---
type: knowledge
created: 2026-02-18
updated: 2026-02-27
tags: [zbz-ocr-tei, decisions, open, decided]
status: active
---

# Decisions

Consolidated register of all decisions and open questions in the project.

**Dependencies:** Cross-cutting — collects from all documents.

---

## Decided

| # | Decision | Rationale | Date | Document |
|---|----------|-----------|------|----------|
| E1 | Hybrid pipeline: Docling (layout) + LLM-OCR (text) | Layout analysis without OCR, OCR separately | 2026-01-29 | [PIPELINE](PIPELINE.md) |
| E2 | Docling only for layout, not for OCR | RapidOCR has encoding problems (e → O) with French text | 2026-01-29 | [OCR-ENGINES](OCR-ENGINES.md) |
| E3 | Deterministic first, LLM only for complex cases | Reproducible, cost-effective, debuggable | 2026-01-29 | [PIPELINE](PIPELINE.md) |
| E4 | 4 document types (A-D) classified | Different pipeline strategies needed | 2026-01-29 | [QUELLENANALYSE](QUELLENANALYSE.md) |
| ~~E5~~ | Downstream GND linking [superseded by E21] | Validate TEI structure first, NER separately | 2026-01-29 | [GND-STRATEGIE](GND-STRATEGIE.md) |
| E6 | Mistral OCR 3 as production engine | ZBZ has Azure access, no GPU required | 2026-02-14 | [OCR-ENGINES](OCR-ENGINES.md) |
| E7 | Quotation remains unchanged | Azure integration no additional effort | 2026-02-14 | [PROJEKT](PROJEKT.md) |
| E8 | Configurable API endpoints | Switch between local and Azure OCR | 2026-02-14 | [INFRASTRUKTUR](INFRASTRUKTUR.md) |
| E9 | Containerization with Podman | ZBZ does not use Docker, Podman is OCI-compatible | 2026-02-14 | [INFRASTRUKTUR](INFRASTRUKTUR.md) |
| E10 | Fork on GitLab Uni Zuerich | ZBZ runs its own instance | 2026-02-14 | [INFRASTRUKTUR](INFRASTRUKTUR.md) |
| ~~E11~~ | Three-tier ecosystem: zbz-ocr-tei → coOCR → teiCrafter [superseded by E21] | Batch OCR → correction → deep cataloguing | 2026-02-18 | [PROJEKT](PROJEKT.md) |
| ~~E12~~ | zbz-ocr-tei OCR only, no TEI transformation [superseded by E21] | TEI + GND in coOCR/teiCrafter, not here | 2026-02-19 | [PIPELINE](PIPELINE.md) |
| E13 | Export as PAGE-XML + METS for coOCR | coOCR expects PAGE-XML (2013-07-15, Transkribus standard) + PNG, not Markdown | 2026-02-20 | [PIPELINE](PIPELINE.md) |
| E14 | Preserve Markdown formatting (R6 resolved) | coOCR stores text as-is in `<Unicode>`, formatting must not be removed | 2026-02-20 | [PIPELINE](PIPELINE.md) |
| E15 | Dashboard redesign: multi-page UI with shared CSS/JS | Unified design system, static JSON data basis, engine visibility, light theme | 2026-02-25 | [PIPELINE](PIPELINE.md) |
| E16 | Page-by-page comparison for monographs (>10 TEI pages) | Global alignment fails at 140+ pages; content matching resolves variable PDF/TEI offsets | 2026-02-25 | [PIPELINE](PIPELINE.md) |
| E17 | LLM correction optional, not default | Worsens docs with CER <5% (Phase 2: +0.03, Phase 4: +0.05); benefit only at CER >10% | 2026-02-25 | [PIPELINE](PIPELINE.md) |
| E18 | Content-based page matching instead of fixed offset | TEI facs numbers ≠ PDF page numbers (cover pages, blank pages); fixed offset drifts | 2026-02-25 | [PIPELINE](PIPELINE.md) |
| E19 | Layout analysis: Docling + Gemini hybrid | Docling (mAP 0.699, free, 17 classes) as primary; Gemini 2.5 Flash as optional validator; Kraken as fallback. Claude Vision disqualified (no BBox), Mistral insufficient (no text BBox) | 2026-02-25 | [E19-LAYOUT-ANALYSE](E19-LAYOUT-ANALYSE.md) |
| E20 | Docling 2.75 confirmed as layout engine (Phase 0) | Type sample passed: all 4 document types correctly detected, column separation Type B works (L: x120-529, R: x560-969), 0.4-3.3s/page | 2026-02-25 | [E19-LAYOUT-ANALYSE](E19-LAYOUT-ANALYSE.md) |
| E21 | Scope expansion: full pipeline in zbz-ocr-tei | After meeting 25.02.: zbz-ocr-tei covers OCR + layout + PAGE-XML + NER/GND + TEI-XML. E12 (OCR only) is thereby superseded. ZBZ keeps Transkribus in parallel | 2026-02-25 | [PLAN.md](../PLAN.md) |
| E22 | TEI generator: directly from layout+OCR to TEI (without PAGE-XML) | PAGE-XML (Phase 1) and NER (Phase 2) not yet implemented. TEI generator goes directly from layout JSON + OCR Markdown to DTA-Basisformat-conformant TEI-XML. Will be extended later when PAGE-XML/NER exist. Entity annotation from seed dict (KNOWN_ENTITIES) | 2026-02-25 | [PIPELINE](PIPELINE.md) |
| E23 | Data delivery Feb 2026: 286 PDFs + 25 TEI-XMLs + 24 PAGE-XML exports | ZBZ delivered full corpus as HerschStandFeb. 24 docs with completed TEI annotation + PAGE-XML (Transkribus), 262 docs PDF only. PAGE-XML uses schema 2013-07-15 (not 2019). PAGE-XML pages are empty (no text, only page skeleton — no TextRegions). Transkribus Collection-ID: 1886177 | 2026-02-27 | [QUELLENANALYSE](QUELLENANALYSE.md) |

---

## Open: High Priority

These questions block progress.

| # | Question | Context | Blocks | Clarification by |
|---|----------|---------|--------|------------------|
| ~~O1~~ | ~~Azure API key~~ | **Resolved (18.02.2026)** -- key available, endpoint tested, benchmark performed | ~~M1~~ | -- |
| O2 | Alignment call date? | Date proposals sent (18./19./20./24.02.) | All open questions | ZBZ |
| O3 | Fork model and merge strategy? | Merge upstream changes into fork, CI-based tests | M4 Integration | ZBZ (in meeting) |
| ~~O4~~ | ~~Interface zbz-ocr-tei -> coOCR: which format?~~ | **Resolved (20.02.2026)** -- PAGE-XML (2013-07-15) + PNG + METS. See E13 | ~~M4~~ | -- |
| ~~O5~~ | ~~Interface coOCR → teiCrafter~~ | Dropped — coOCR/teiCrafter no longer in scope (E21) | -- | -- |

---

## Open: Medium Priority

Important for quality, but not blocking.

| # | Question | Context | Blocks | Clarification by |
|---|----------|---------|--------|------------------|
| O6 | Normalization vs. source fidelity | Back in scope (E21). Clarification with expert Baehler pending | Phase 3 TEI | ZBZ |
| O7 | Typography of headings | Back in scope (E21). Same question as O6 | Phase 3 TEI | ZBZ |
| O8 | Metadata from ALMA/MMSID | Back in scope (E21). MMSIDs needed for teiHeader | Phase 3 TEI | ZBZ |
| O9 | div-type values front/back matter | Back in scope (E21). editorial, context, translation etc. | Phase 3 TEI | Own decision |
| O10 | Column problem Type B: which approach? | A: Docling+Crop, B: Gemini Agentic Vision, C: Prompt tuning | M1 Phase 2 | Own test |
| O11 | Entities without GND entry | Back in scope (E21). Local ID or leave empty? | Phase 2 NER | Own decision |
| O12 | GND linking in PoC | Back in scope (E21). Yes — seed + lobid.org in Phase 2 | Phase 2 NER | Own decision |
| O18 | Test multimodal LLM correction (scan image + OCR text) | Research shows <1% CER (arXiv:2504.00414); currently text only | Quality | Own test |
| O19 | Test Mistral `extract_header/footer` | Could filter JSTOR artifacts without LLM | Quality | Own test |
| O20 | Test DeepSeek Free OCR (without `<\|grounding\|>`) for Type A/C | Potentially faster without quality loss for single-column layout | Performance | Own test |
| O21 | Layout region post-processing: overlap, single-liners, page numbers | Docling produces overlapping regions, single-line fragments and does not recognize page numbers as page_footer. 3 heuristics needed | Layout quality | Own impl. |

---

## Open: Low Priority

Can be clarified later.

| # | Question | Context | Document |
|---|----------|---------|----------|
| O13 | Subject headings: who creates these? | Back in scope (E21). Do they go in teiHeader? | [TEI-MAPPING](TEI-MAPPING.md) |
| O14 | GND work records in back matter? | Back in scope (E21) | [TEI-MAPPING](TEI-MAPPING.md) |
| O15 | Systematic use of Textual Tags in Transkribus? | div, organization, person, sic, speech, unclear, work | [ZBZ-WORKFLOW](ZBZ-WORKFLOW.md) |
| O16 | Option edition view: will it be built? | Not yet decided (mail 14.02.) | [PROJEKT](PROJEKT.md) |
| O17 | Activate GitHub Pages for QA viewer? | HTML ready, but Pages not activated | [PROJEKT](PROJEKT.md) |

---

## Risks

| # | Risk | Impact | Mitigation | Status |
|---|------|--------|------------|--------|
| R1 | Column problem unsolvable | High | Docling separates columns correctly (E20). Gemini as fallback | **Resolved** (E20) |
| R2 | TEI too complex | Medium | Reference TEI as ground truth, incremental implementation | Open |
| R3 | GND hallucinations | Medium | Seed dictionary + confidence threshold | Open |
| R4 | Azure API compatibility Mistral OCR 3 | Medium | Test endpoint, fallback to direct API | **Resolved** (18.02.) |
| R5 | Fork divergence between DHCraft and ZBZ | Medium | Define merge strategy, CI-based tests | Waiting for meeting (→ O3) |
| R6 | Post-processing removes formatting information | Medium | Preserve Markdown markup before cleanup | **Resolved** (E14) |
| R7 | Transkribus incompatibility PAGE-XML | High | ZBZ export obtained (E23): schema 2013-07-15, ID scheme `{NNNN}_p{NNN}`, image format JPG. PAGE-XML is empty (no text). @type/@custom not verifiable (no TextRegions in export) | **Partially clarified** (E23) |
| R8 | Docling BBox quality insufficient | Medium | Phase 0 passed (E20). Gemini as fallback, Kraken as alternative | **Resolved** (E20) |
| R9 | Footnote inline placement incorrect | Medium | Default: end-of-div, inline as opt-in | Open |
| R10 | NER quality on French (66% corpus) | Medium | Seed dictionary as first layer BEFORE LLM NER | Open |
| R11 | lobid.org API changes | Low | Cache + fallback to local GND data | Open |
| R12 | TEI schema incompatibility | High | Reference TEI as ground truth, schema validation | Open |
| R13 | Gemini API key missing | Low | Gemini is optional, Docling sufficient for main case | Accepted |

---

## References

- [PROJEKT](PROJEKT.md) for milestones and status
- [PIPELINE](PIPELINE.md) for pipeline decisions
- [TEI-MAPPING](TEI-MAPPING.md) for open TEI questions (O6-O9, O13-O14)
- [JOURNAL](JOURNAL.md) for chronological decision history

---

*Created: 2026-02-18 | Updated: 2026-02-27 (E23 data delivery, R7 partially clarified, E13 schema corrected)*
