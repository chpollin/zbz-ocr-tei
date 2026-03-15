# ZBZ-OCR-TEI

LLM-powered OCR and TEI pipeline for the Jeanne Hersch Edition at the Zentralbibliothek Zurich.

## What does this repo do?

Fully automated end-to-end pipeline for 286 documents (4,152 pages) from the estate of Jeanne Hersch:

```
PDF-Scans --> Images --> OCR --> Layout --> PAGE-XML --> NER/Wikidata --> TEI-XML --> Quality Screening --> Curation --> Publication
              (PNG)     (Mistral)  (Docling)              (Gemini)       (DTA-Basis)  (Agent-Based)    (Editor)    (GitHub Pages)
```

## Pipeline Components

| Component | Engine | Status |
|-----------|--------|--------|
| Image extraction | Python (PDF to PNG) | Done |
| Document classification | Gemini Flash Lite | Done |
| OCR | Mistral Document AI (Azure) | Done |
| OCR correction | Gemini Flash Lite | Pilot |
| Layout analysis | Docling RT-DETR V2 (local GPU) | Done |
| Layout QA/Detect | Gemini Flash Lite | Done |
| PAGE-XML + METS | Rule-based generator | Done |
| NER extraction | Gemini Flash Lite (6 entity types) | Done |
| Entity Index + Wikidata/GND linking | Wikidata API + TEI-XML indices | Done (24% linked) |
| TEI-XML (Unified Pipeline) | Scaffold + Gemini + RelaxNG validation | Done (285/285) |
| TEI NER injection | Rule-based annotation + Entity Index | Done (285/285) |
| **Agent-Based Quality Screening** | **Claude Code (7-layer review)** | **Done (285/285)** |
| **Curation (Human-in-the-Loop)** | **Browser WYSIWYG + FastAPI server** | **Done** |
| Review + Publication | Status workflow + publish to GitHub Pages | Done |
| Evaluation + Dashboard | CER/WER + interactive QA UI | Done |

Current metrics and progress: see [Dashboard](https://dhcraft.github.io/zbz-ocr-tei/) or run locally (`docs/infrastruktur/index.html`). Detailed status: [PROJEKT.md](knowledge/PROJEKT.md).

### Online Demo

4 representative documents are available on [GitHub Pages](https://dhcraft.github.io/zbz-ocr-tei/) with full viewer functionality (facsimile, OCR text, layout overlay, entities). All results are AI-generated. Full data is only available locally.

### Digital Edition + Curation (Human-in-the-Loop)

The final pipeline step: editors verify and correct AI-generated TEI in the browser. The curation editor supports text correction, structure editing, and entity curation (WYSIWYG + XML mode). A review workflow (draft > in_review > approved) ensures quality before publication. The edition (`docs/index.html`) provides the public reading interface with catalog, reader, and entity sidebar.

```bash
python -m scripts.server.curation_server    # http://localhost:8000
```

Details: [EDITION.md](knowledge/EDITION.md), [CURATION.md](knowledge/CURATION.md).

## Directory Structure

```
zbz-ocr-tei/
  knowledge/              # 14 project documents (Single Source of Truth)
  scripts/                # Python pipeline
    config.py             # Central configuration
    ocr_pipeline.py       # OCR (Mistral/DeepSeek)
    classify_docs.py      # Document classification (Gemini, Stage 1a)
    gemini_ocr_correct.py # Gemini OCR correction (Stage 2b)
    llm_postprocess.py    # LLM post-correction (Haiku 4.5)
    run_layout_analysis.py  # Layout analysis (Docling, local GPU)
    run_layout_cloud.py     # Layout analysis (docling-serve API, E24)
    layout_qa_gemini.py     # Layout QA + Detect (Gemini 3.1 Flash Lite, E25/E26)
    evaluate_ocr.py       # CER/WER evaluation
    generate_dashboard_data.py  # Dashboard data
    layout/               # PAGE-XML + METS generators
    tei/                  # TEI-XML generator
    ner/                  # NER + Wikidata linking (6 modules, E34)
    server/               # Curation Server (FastAPI, E36)
    core/                 # Shared data loaders
    postprocess/          # Deterministic post-processing
  docs/                   # Digital Edition + Pipeline Infrastructure (GitHub Pages)
    index.html            # Edition landing page
    catalog.html          # Document catalog
    reader.html           # TEI reader with entity sidebar
    about.html            # Project information
    infrastruktur/        # Pipeline QA tools (dashboard, viewer, benchmark)
    js/                   # ES6+ modules (edition, TEI, entities, shared)
    css/                  # Stylesheets
    data/                 # Dashboard data + 4 DEMO docs
    images/               # Page scans (4 DEMO docs committed, rest local)
  data/                   # Source data (not versioned)
    scans/                # 286 PDF digitizations
    doc_metadata.json     # Gemini classification (286 docs, versioned)
    referenz-tei/         # 25 reference TEI (ZBZ-annotated)
    page-xml-transkribus/ # 24 Transkribus exports (PAGE-XML)
    tei_curated/          # Curated TEI gold-standard (versioned, E36)
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
# Enter values in .env (Mistral, Anthropic, Gemini)

# OCR with Mistral (no GPU)
python -m scripts.ocr_pipeline -i data/scans/2310.pdf -e mistral

# Layout analysis (GPU for Docling)
python -m scripts.run_layout_analysis --doc 2310

# Generate TEI-XML (no GPU, uses Gemini API)
python -m scripts.tei.tei_unified --doc 2310

# Validate all TEI (RelaxNG + project rules + quality warnings)
python -m scripts.tei.tei_validator --all --html-report

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
| Gemini 3.1 Flash Lite | Google AI API (E25/E26/E27/E29/E34) | Layout QA/Detect, classification, OCR correction, NER |

## Pipeline Infrastructure

The QA tools are under `docs/infrastruktur/`:

- **Dashboard:** Pipeline status, CER comparison, filterable document catalog
- **Viewer:** 3-panel layout (facsimile + OCR + TEI/PAGE-XML), entity sidebar, layout overlay
- **Benchmark:** OCR engine comparison (Mistral vs DeepSeek)

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
| Digital edition | [knowledge/EDITION.md](knowledge/EDITION.md) |
| Curation Editor | [knowledge/CURATION.md](knowledge/CURATION.md) |
| Work journal | [knowledge/JOURNAL.md](knowledge/JOURNAL.md) |

## Team

A project of the Zentralbibliothek Zurich (ZBZ) in collaboration with DHCraft.

---

*Last updated: 2026-03-15*
