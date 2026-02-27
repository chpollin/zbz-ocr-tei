---
type: knowledge
created: 2026-02-18
updated: 2026-02-27
tags: [zbz-ocr-tei, project, ecosystem, vision]
status: active
---

# Project: ZBZ-OCR-TEI Pipeline

LLM-powered OCR and TEI transformation pipeline for 289 Jeanne Hersch texts (7,200 pages) from the Zentralbibliothek Zuerich.

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
| Layout engine | Docling 2.75 (RT-DETR V2 Heron, E19/E20) |
| NER | Claude Haiku 4.5 + lobid.org GND API |
| Mode | Batch, no manual intervention |
| Implementation plan | [PLAN.md](../PLAN.md) |

---

## Milestones

**Scope:** Full pipeline PDF → TEI-XML (since 25.02.2026). Implementation plan: [PLAN.md](../PLAN.md).

| # | Milestone | Success criterion | Status |
|---|-----------|-------------------|--------|
| M0 | Image extraction + QA viewer | Images + viewer available | Done |
| M1 | OCR validated | >=95% accuracy all types | Done: 93.58% (Mistral), dashboard UI |
| M2 | Layout + PAGE-XML | Regions + BBox + PAGE-XML for 15 pilots | **Phase 1** |
| M3 | NER + GND | Entity recall >70%, GND linking >60% | **Phase 2** |
| M4 | TEI-XML | DTA-compliant TEI for 15 pilots, schema-valid | Partial (383 files generated, E22: without PAGE-XML/NER) |
| M5 | Production run | 289 docs processed, spot-check QA passed | Phase 5 |

### Dependencies

```
M0 (Images) ──► M1 (OCR) ──► M2 (Layout+PAGE-XML) ──► M3 (NER+GND) ──► M4 (TEI) ──► M5 (Production)
```

---

## Component Status (26.02.2026)

| Component | Status | Details |
|-----------|--------|---------|
| Image extraction | Done | `scripts/extract_pages.py`, 383 pages |
| QA viewer | Done | `docs/` with HTML viewer |
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
| Dashboard data | Done | `scripts/generate_dashboard_data.py` → dashboard.json |
| Layout analysis | Partial | `scripts/run_layout_analysis.py`, 8/15 docs with JSON + overlay PNGs. QA: BBox correct, 3 issues (O21) |
| TEI generator | Done | `scripts/tei/tei_generator.py`, 383 TEI-XML files, DTA-Basisformat |
| Viewer TEI panel | Done | 3-panel viewer (facsimile + OCR + TEI), toggle T, rendered view, syntax highlighting, diff, entity sidebar |
| Viewer TEI refactoring | Done | TEI JS extracted to `docs/tei-viewer.js` (~300 lines), viewer.html 1200→816 lines |
| Layout post-processing | Pending | Overlap filter, single-line merge, page-number heuristic (O21) |
| PAGE-XML generator | Pending | Layout + OCR → PAGE-XML (phase 1 in PLAN.md) |
| NER + GND | Pending | Entity recognition + GND linking (phase 2 in PLAN.md) |
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
| Mistral OCR (Azure, 289 docs) | 6-15 USD |
| LLM correction (Haiku 4.5, 289 docs) | ~35 USD |
| GPU cloud (optional) | ~10-20 USD |

---

## References

- [PIPELINE](PIPELINE.md) for technical pipeline details
- [QUELLENANALYSE](QUELLENANALYSE.md) for corpus and document types
- [DECISIONS](DECISIONS.md) for open questions and decisions
- [INFRASTRUKTUR](INFRASTRUKTUR.md) for deployment details

---

*Created: 2026-02-18 | Updated: 2026-02-27*
