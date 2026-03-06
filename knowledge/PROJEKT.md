---
type: knowledge
created: 2026-02-18
updated: 2026-03-06
tags: [zbz-ocr-tei, project, ecosystem, vision]
status: active
---

# Project: ZBZ-OCR-TEI Pipeline

LLM-powered OCR and TEI transformation pipeline for 286 Jeanne Hersch texts (4,152 pages) from the Zentralbibliothek Zuerich. (Masterfile lists 289 texts; 3 missing — see [DECISIONS](DECISIONS.md) O22.)

**Dependencies:** None (root document)

---

## Commission

| Aspect | Details |
|--------|---------|
| Client | Zentralbibliothek Zuerich (ZBZ) |
| Contractor | DHCraft |
| Subject | Automated OCR + TEI annotation for Jeanne Hersch estate |
| Status | Mutually confirmed (14.02.2026) |
| Quote | Unchanged (Azure/Mistral no additional cost) |
| ZBZ contacts | Elias Kreyenbuehl, Anouschka (editions and IT background) |

---

## Ecosystem

Since the alignment meeting (25.02.2026), zbz-ocr-tei covers the **entire pipeline**: OCR + Layout + PAGE-XML + NER/GND + TEI-XML. ZBZ maintains their Transkribus workflow in parallel.

```
┌───────────────────────────────────────────────────────┐
│  zbz-ocr-tei (this repo)                              │
│  PDF → Images → OCR → Layout → PAGE-XML → NER → TEI  │
│  (Python, batch, fully automated)                     │
└───────────────────────────────────────────────────────┘
```

| Aspect | Details |
|--------|---------|
| Input | PDF scans (7,200 pages) |
| Output | TEI-XML (DTA-Basisformat), PAGE-XML + PNG + METS |
| OCR engines | Mistral OCR 3 (Azure), DeepSeek-OCR-2 (local) |
| Layout engine | Docling 2.75 (RT-DETR V2 Heron, E19/E20) + Gemini 3.1 Flash Lite (E26) |
| NER | Claude Haiku 4.5 + lobid.org GND API |
| Mode | Batch, no manual intervention |
| Implementation plan | [PLAN.md](PLAN.md) |

---

## Milestones

**Scope:** Full pipeline PDF → TEI-XML (since 25.02.2026). Implementation plan: [PLAN.md](PLAN.md).

| # | Milestone | Success criterion | Status |
|---|-----------|-------------------|--------|
| M0 | Image extraction + QA viewer | Images + viewer available | Done |
| M1 | OCR validated | >=93% accuracy all types | Done: 93.58% (Mistral), dashboard UI |
| M2 | Layout + PAGE-XML | Regions + BBox + PAGE-XML for all docs | Done: 286 docs, 4,091 PAGE-XML + 286 METS |
| M3 | NER + GND | Entity recall >70%, GND linking >60% | **Pending** (Phase 3) |
| M4 | TEI-XML | DTA-compliant TEI, schema-valid | Done: Unified TEI Pipeline (E32), 286 docs production run, RelaxNG-valid. Rule-based scaffold + Gemini refinement |
| M5 | Production run | 286 docs processed, spot-check QA passed | Pending (Phase 6) |

### Dependencies

```
M0 (Images) ──► M1 (OCR) ──► M2 (Layout+PAGE-XML) ──► M3 (NER+GND) ──► M4 (TEI) ──► M5 (Production)
```

---

## Component Status (06.03.2026)

| Component | Status | Details |
|-----------|--------|---------|
| Image extraction | Done | `scripts/extract_pages.py`, 4,152 pages (286 PDFs) |
| QA viewer | Done | `docs/` with HTML viewer, Docling/Gemini layout toggle |
| OCR phase 1 (type A) | Done | Mistral 90.60%, DeepSeek 94.4% |
| OCR phase 2 (type B) | Done | Mistral 93.69% accuracy |
| OCR phase 3 (type D) | Done | Mistral 97.12% accuracy |
| OCR phase 4 (type C) | Done | CER 2.65% (page-level comparison, best phase) |
| Post-processing | Done | 4-stage in `scripts/postprocess/` |
| GND seed | Done | 75 entities, `scripts/extract_gnd.py` |
| LLM post-correction | Done | `scripts/llm_postprocess.py`, Haiku 4.5, variant C |
| Evaluation | Done | `scripts/evaluate_ocr.py`, CER/WER + HTML report |
| Azure integration | Done | Mistral Document AI 2512, `.env` configured |
| Benchmark UI | Done | `docs/benchmark.html`, Mistral vs DeepSeek |
| Dashboard redesign | Done | `docs/` with shared.css/js, index.html, viewer.html |
| Dashboard data | Done | `scripts/generate_dashboard_data.py` -> dashboard.json |
| Layout analysis (Docling) | Done | 286/286 docs, 4,152 layout JSONs. Quality: 75% good, 10% warning, 12% bad, 3% empty |
| Layout QA (Gemini) | Done | `layout_qa_gemini.py --mode auto --force`: 286 docs, 3,992 pages (3,519 QA + 633 Detect), 14,708 corrections, avg score 72.7. Typspezifische Prompts (E30), changes_summary logging (E31) |
| Layout Overlays | Done | `generate_layout_overlays.py --compare`: 7,988 PNGs (Gemini overlay + Docling-vs-Gemini side-by-side) |
| TEI generator (rule-based) | Done | `scripts/tei/tei_generator.py`, 4,117 TEI-XML files (285 docs), flat structure |
| TEI generator (Gemini Vision) | Pilot | `scripts/tei/tei_gemini.py`, 1 Call/Seite (E30), Doc 2310 successful, typspez. Prompts |
| **Unified TEI Pipeline** | **Production** | `scripts/tei/tei_unified.py` (E32): Rule-based scaffold + Gemini refinement + assembly + RelaxNG validation. 286 docs. Post-processing: `fix_gemini_tei()`, `reannotate_entities()`, interview speaker detection |
| TEI Validator | Done | `scripts/tei/tei_validator.py`: RelaxNG (TEI-All) + 8 Projekt-Regeln (R1-R8) |
| PAGE-XML generator | Done | `scripts/layout/page_xml_generator.py` + `mets_generator.py`, 286 docs, 4,091 PAGE-XML + 286 METS |
| Document classification | Done | `scripts/classify_docs.py`, Gemini 3.1 Flash Lite, 286/286 docs (E27) |
| Gemini OCR correction | Sample | `scripts/gemini_ocr_correct.py`, 5 pilot docs, CER 3.97% -> 3.30% (E29) |
| Viewer TEI panel | Done | 3-panel viewer (facsimile + OCR + TEI), toggle T, rendered view, syntax highlighting, diff, entity sidebar |
| Viewer TEI refactoring | Done | TEI JS extracted to `docs/tei-viewer.js` (~300 lines), viewer.html 1200->816 lines |
| Viewer PAGE-XML panel | Done | `docs/page-viewer.js`, regions/XML/METS tabs, mutual exclusion with TEI |
| Layout post-processing | Resolved | Handled by E25/E26 (Gemini QA/Detect) — see [DECISIONS](DECISIONS.md) O21 |
| NER + GND | Pending | Entity recognition + GND linking (phase 2 in [PLAN](PLAN.md)) |
| Containerization | Pending | Dockerfile for Podman |
| CI/CD | Pending | GitLab Uni Zuerich |

---

## Team

| Person | Role | Organization |
|--------|------|-------------|
| Christopher | Project lead, development | DHCraft |
| Elias Kreyenbuehl | Client, coordination | ZBZ |
| Anouschka | Edition, IT | ZBZ |
| Library IT | CI/CD, Podman, infrastructure | ZBZ |

---

## Costs

| Item | Amount |
|------|--------|
| Mistral OCR (Azure, 286 docs) | 6-15 USD |
| LLM correction (Haiku 4.5, 286 docs) | ~35 USD |
| Gemini Layout QA + Detect | ~12 USD |
| Gemini TEI Generation (286 docs) | TBD (Flash Lite, ~$5-20 est.) |
| GPU cloud (optional) | ~10-20 USD |

---

## References

- [PIPELINE](PIPELINE.md) for technical pipeline details
- [QUELLENANALYSE](QUELLENANALYSE.md) for corpus and document types
- [DECISIONS](DECISIONS.md) for open questions and decisions
- [INFRASTRUKTUR](INFRASTRUKTUR.md) for deployment details

---

*Created: 2026-02-18 | Updated: 2026-03-06*
