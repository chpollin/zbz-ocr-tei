---
type: knowledge
created: 2026-02-18
updated: 2026-03-09
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
| NER | Gemini 3.1 Flash Lite + Wikidata API (E34) |
| Mode | Batch, no manual intervention |
| Implementation plan | [PLAN.md](PLAN.md) |

---

## Milestones

**Scope:** Full pipeline PDF → TEI-XML (since 25.02.2026). Implementation plan: [PLAN.md](PLAN.md).

| # | Milestone | Success criterion | Status |
|---|-----------|-------------------|--------|
| M0 | Image extraction + QA viewer | Images + viewer available | Done |
| M1 | OCR validated | >=93% accuracy all types | Done (see [TESTPLAN](TESTPLAN.md) + Dashboard) |
| M2 | Layout + PAGE-XML | Regions + BBox + PAGE-XML for all docs | Done |
| M3 | NER + Wikidata | Entity recall >70%, linking >50% | **Done** (285 Docs, 11,685 Entities, Wikidata ~15% ongoing) |
| M4 | TEI-XML | DTA-compliant TEI, schema-valid | **Done** (285/285 unified, 284 schema-valide, typkorrekte Entity-Tags mit internen IDs) |
| M5 | Production run | 286 docs processed, spot-check QA passed | **In Progress** (285/285 erzeugt, Quality Sweep + Kurationspilot ausstehend) |

### Dependencies

```
M0 (Images) ──► M1 (OCR) ──► M2 (Layout+PAGE-XML) ──► M3 (NER+GND) ──► M4 (TEI) ──► M5 (Production)
```

---

## Component Status

Aktuelle Metriken (CER, Dateizahlen, Validierung): siehe Dashboard (`docs/index.html`) und Evaluation-Output (`output/evaluation/`).

| Component | Status | Details |
|-----------|--------|---------|
| Image extraction | Done | `scripts/extract_pages.py` |
| OCR (Mistral + DeepSeek) | Done | `scripts/ocr_pipeline.py`. Ergebnisse: [TESTPLAN](TESTPLAN.md) |
| Post-processing | Done | `scripts/postprocess/` (4-stage) |
| LLM post-correction | Done | `scripts/llm_postprocess.py`, Haiku 4.5, optional (E17) |
| Gemini OCR correction | Sample | `scripts/gemini_ocr_correct.py` (E29) |
| Layout analysis (Docling) | Done | `scripts/run_layout_analysis.py`. Details: [ENGINES](ENGINES.md) |
| Layout QA (Gemini) | Done | `scripts/layout_qa_gemini.py --mode auto` (E25/E26/E31) |
| PAGE-XML generator | Done | `scripts/layout/page_xml_generator.py` + `mets_generator.py` |
| Document classification | Done | `scripts/classify_docs.py` (E27) |
| NER Extraction | **Done** | `scripts/ner/` (7 Module, E34/E35). 285/286 Docs, 11,685 Entities, 26,197 Mentions |
| Entity Index | **Done** | 4,100 Eintraege in `data/entities/`, 341 mit Wikidata. Linking laeuft |
| TEI NER Injection | **285/285** | Entity-Tags mit internen IDs (zbz-p/o/l/w.N) direkt in Step 1 |
| **Unified TEI Pipeline** | **285/285** | `scripts/tei/tei_unified.py` (E32/E37-E40). 284/285 schema-valide |
| TEI Validator | Done | `scripts/tei/tei_validator.py`: RelaxNG + 8 Projekt-Regeln |
| Evaluation + Dashboard | Done | `scripts/evaluate_ocr.py` + `docs/index.html` |
| Digitale Edition + Curation | Done | `docs/` (E33) + Curation Server (E36). Details: [EDITION](EDITION.md), [CURATION](CURATION.md) |
| **Agent-Based Quality Screening** | **In Progress** | 145/285 Docs gescreent. 100 APPROVED, 26 WITH_NOTES, 19 NEEDS_REVIEW (13%) |
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
| Gemini TEI Generation (286 docs) | ~$17 (Flash Lite, E32) |
| Gemini NER (286 docs, est.) | ~$5-12 (Flash Lite, E34) |
| GPU cloud (optional) | ~10-20 USD |

---

## References

- [PIPELINE](PIPELINE.md) for technical pipeline details
- [QUELLENANALYSE](QUELLENANALYSE.md) for corpus and document types
- [DECISIONS](DECISIONS.md) for open questions and decisions
- [INFRASTRUKTUR](INFRASTRUKTUR.md) for deployment details

---

*Created: 2026-02-18 | Updated: 2026-03-08*
