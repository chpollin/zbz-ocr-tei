# ZBZ-OCR-TEI

LLM-powered OCR and TEI pipeline for the Jeanne Hersch Edition at the Zentralbibliothek Zurich.

## What does this repo do?

Fully automated end-to-end pipeline for 286 documents (4,152 pages) from the estate of Jeanne Hersch:

```
PDF-Scans --> Images --> OCR --> Layout --> PAGE-XML --> NER/GND --> TEI-XML
              (PNG)     (Mistral)  (Docling)              (Haiku)    (DTA-Basisformat)
```

## Status (05.03.2026)

286 PDFs received (E23), 15 pilot documents (383 pages) fully processed. OCR + Layout + Classification complete for all 286 docs.

| Component | Status | Result |
|-----------|--------|--------|
| Image extraction | 286/286 Docs | 4,152 page images (PNG) |
| Document classification | 286/286 Docs | Gemini 3.1 Flash Lite (Stage 1a, E27) |
| OCR (Mistral) | 285/286 Docs | CER 6.42% (15 Pilot-Docs evaluiert) |
| LLM post-correction | 15/286 Docs | Optional (E17), Haiku 4.5 Variant C |
| Layout analysis (Docling) | 286/286 Docs | 4,152 layout JSONs, RTX 4060 ~5s/page |
| Gemini Layout QA/Detect | 286/286 Docs | Auto mode: QA for good, detect for bad pages (E25/E26) |
| TEI-XML | 15/286 Docs | 383 TEI-XML files (DTA-Basisformat, E22) |
| Evaluation | 15/286 Docs | CER/WER per page + dashboard |

### OCR Quality by Document Type

| Type | Description | Mistral CER | Accuracy |
|------|-------------|-------------|----------|
| A | Single-column | 9.40% | 90.60% |
| B | Two-column | 6.31% | 93.69% |
| C | Monograph | 2.65% | 97.35% |
| D | Special format | 2.88% | 97.12% |

### Online Demo

4 representative documents are available on [GitHub Pages](https://dhcraft.github.io/zbz-ocr-tei/) with full viewer functionality (facsimile, OCR text, layout overlay). All results are AI-generated. Full data (286 docs) is only available locally.

| Doc | Type | Language | Pages |
|-----|------|----------|-------|
| 2310 | A (single-column) | FR | 3 |
| 1000 | B (two-column) | FR | 4 |
| 1330 | D (special) | DE/FR | 6 |
| 1540 | C (monograph) | DE | 8 |

### Next Steps

PAGE-XML -> NER+GND -> TEI extension -> Production run (286 docs). Details: [PLAN.md](knowledge/PLAN.md).

## Directory Structure

```
zbz-ocr-tei/
  knowledge/              # 14 project documents (Single Source of Truth)
  scripts/                # Python pipeline
    config.py             # Central configuration
    ocr_pipeline.py       # OCR (Mistral/DeepSeek)
    llm_postprocess.py    # LLM post-correction (Haiku 4.5)
    run_layout_analysis.py  # Layout analysis (Docling, local GPU)
    run_layout_cloud.py     # Layout analysis (docling-serve API, E24)
    layout_qa_gemini.py     # Layout QA + Detect (Gemini 3.1 Flash Lite, E25/E26)
    evaluate_ocr.py       # CER/WER evaluation
    generate_dashboard_data.py  # Dashboard data
    tei/                  # TEI-XML generator
    postprocess/          # Deterministic post-processing
  docs/                   # Dashboard + QA viewer (GitHub Pages)
    index.html            # Dashboard: metrics, document catalog, CER comparison
    viewer.html           # 3-panel viewer: facsimile + OCR + TEI
    tei-viewer.js         # TEI rendering: rendered view, diff, entities
    shared.css / shared.js  # Design system + shared utilities
    data/dashboard.json   # Generated data
    data/examples/        # 4 DEMO docs (OCR + Layout for online demo)
    images/               # Page scans (4 DEMO docs committed, rest local)
  data/                   # Source data (not versioned)
    scans/                # 286 PDF digitizations
    referenz-tei/         # 25 reference TEI (ZBZ-annotated)
    page-xml-transkribus/ # 24 Transkribus exports (PAGE-XML)
  output/                 # Generated data (not versioned)
  .env.example            # Template for API keys
```

## Quick Start

```bash
# Set up environment
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -r requirements.txt

# Configure API keys
cp .env.example .env
# Enter values in .env (Mistral, Anthropic)

# OCR with Mistral (no GPU)
python -m scripts.ocr_pipeline -i data/scans/2310.pdf -e mistral

# Layout analysis (GPU for Docling)
python -m scripts.run_layout_analysis --doc 2310

# Generate TEI-XML (no GPU)
python -m scripts.tei.tei_generator --doc 2310

# Evaluation (no GPU)
python scripts/evaluate_ocr.py --all

# Generate dashboard data
python -m scripts.generate_dashboard_data
```

Complete CLI reference: [knowledge/PIPELINE.md](knowledge/PIPELINE.md) §CLI Commands.

## OCR Engines

| Engine | Access | Usage |
|--------|--------|-------|
| Mistral Document AI 2512 | Azure AI Foundry | Production OCR |
| DeepSeek-OCR-2 | Local (GPU) | Development |
| Claude Haiku 4.5 | Anthropic API | LLM post-correction (optional) |
| Docling 2.75 | Local / docling-serve API (E24) | Layout analysis (BBox + regions) |
| Gemini 3.1 Flash Lite | Google AI API (E25/E26) | Layout QA + Detect (3 modes) |

## Dashboard + Viewer

The QA dashboard (`docs/index.html`) shows pipeline status, CER comparison, and a filterable document catalog. The viewer (`docs/viewer.html`) offers:

- **3-panel layout:** Facsimile + OCR text + TEI-XML side by side
- **TEI viewer:** Rendered view, XML with syntax highlighting, reference diff
- **Entity sidebar:** Persons/organizations/works with GND links
- **Layout overlay:** SVG BBox visualization over the facsimile (Docling/Gemini toggle)
- **Gemini QA highlights:** Changed regions shown with yellow dashed borders + change reasons

## Documentation

| Topic | File |
|-------|------|
| **Navigation (start here)** | [knowledge/INDEX.md](knowledge/INDEX.md) |
| Project + milestones | [knowledge/PROJEKT.md](knowledge/PROJEKT.md) |
| Pipeline (7 stages) | [knowledge/PIPELINE.md](knowledge/PIPELINE.md) |
| Implementation plan | [knowledge/PLAN.md](knowledge/PLAN.md) |
| Decisions + open items | [knowledge/DECISIONS.md](knowledge/DECISIONS.md) |
| Test plan + results | [knowledge/TESTPLAN.md](knowledge/TESTPLAN.md) |
| TEI rules | [knowledge/TEI-MAPPING.md](knowledge/TEI-MAPPING.md) |
| OCR + Layout engines | [knowledge/ENGINES.md](knowledge/ENGINES.md) |
| Work journal | [knowledge/JOURNAL.md](knowledge/JOURNAL.md) |

## Team

A project of the Zentralbibliothek Zurich (ZBZ) in collaboration with DHCraft.

---

*Last updated: 2026-03-05*
