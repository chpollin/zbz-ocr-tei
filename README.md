# ZBZ-OCR-TEI

LLM-powered OCR and TEI pipeline for the Jeanne Hersch Edition at the Zentralbibliothek Zurich.

## What does this repo do?

Fully automated end-to-end pipeline for 286 documents (~4,100 pages) from the estate of Jeanne Hersch:

```
PDF-Scans -> Images -> OCR -> Layout -> PAGE-XML -> NER/Wikidata -> TEI-XML -> Quality Screening
             (PNG)    (Mistral) (Docling)            (Gemini)       (DTA-Basis) (Agent-Based)
```

## Pipeline Components

| Component | Engine | Status |
|---|---|---|
| Image extraction | Python (PDF to PNG) | Done |
| Document classification | Gemini Flash Lite | Done |
| OCR | Mistral Document AI (Azure) | Done |
| OCR correction | Gemini Flash Lite | Pilot |
| Layout analysis | Docling RT-DETR V2 / docling-serve | Done |
| Layout QA/Detect | Gemini Flash Lite | Done |
| PAGE-XML + METS | Rule-based generator | Done |
| NER extraction | Gemini Flash Lite (6 entity types) | Done |
| Entity Index + Wikidata/GND linking | Wikidata API + TEI indices | Done (47 % linked) |
| TEI-XML (Unified Pipeline) | Scaffold + Gemini + RelaxNG validation | Done (285/285) |
| Agent-Based Quality Screening | Claude Code (7-layer review) | Done (242 Approved, 43 With Notes) |

Current metrics: see [Korpus-Uebersicht](https://dhcraft.github.io/zbz-ocr-tei/) (GitHub Pages) or `docs/index.html` locally. Detailed status: [knowledge/projekt.md](knowledge/projekt.md).

## Frontend

Three static HTML pages under `docs/`, deployed via GitHub Pages:

- `docs/index.html` &mdash; corpus overview with thumbnails, search, filters, screening progress
- `docs/viewer.html` &mdash; per-document inspector (facsimile + layout overlay + OCR/TEI panel + editor modes)
- `docs/about.html` &mdash; project info

All data is loaded from static JSON/XML/MD files under `docs/data/`. No backend. Editor changes (layout corrections, transcription edits) are exported as file downloads.

```bash
python -m http.server 8000 -d docs    # http://localhost:8000/
```

## Directory Structure

```
zbz-ocr-tei/
  knowledge/              # 10 project documents (Single Source of Truth, all lowercase)
  scripts/                # Python pipeline
    config.py             # Central configuration
    ocr_pipeline.py       # OCR (Mistral / DeepSeek)
    classify_docs.py      # Document classification (Gemini)
    gemini_ocr_correct.py # Gemini OCR correction
    llm_postprocess.py    # LLM post-correction (Haiku 4.5)
    run_layout_analysis.py   # Layout analysis (Docling local)
    run_layout_cloud.py      # Layout analysis (docling-serve API)
    layout_qa_gemini.py      # Layout QA + Detect (Gemini)
    evaluate_ocr.py       # CER/WER evaluation
    benchmark_cer.py      # End-to-end CER benchmark
    cer_statistics_full.py   # BCa-Bootstrap + Paired + HCPR
    generate_edition_data.py     # Catalog, thumbnails, per-page mirror for viewer
    layout/               # PAGE-XML + METS generators
    tei/                  # TEI-XML pipeline (scaffold, Gemini, assembly, validator)
    ner/                  # NER + Wikidata/GND linking
    core/                 # Shared data loaders
    postprocess/          # Deterministic post-processing
  docs/                   # Static frontend (GitHub Pages source)
    index.html            # Corpus overview
    viewer.html           # Per-document viewer
    about.html            # Project info
    css/                  # tokens.css, base.css, viewer.css, catalog.css
    js/                   # core.js, viewer.js, catalog.js, tei-render.js, ...
    data/                 # catalog.json, entity_index.json, pages/, thumbs/, tei/
    images/               # Page scans (4 DEMO docs committed, rest local-only)
  data/                   # Source data (mostly not versioned)
    scans/                # 286 PDF digitizations
    doc_metadata.json     # Gemini classification (versioned)
    referenz-tei/         # 25 reference TEIs (ZBZ-annotated)
    tei_curated/          # Curated gold-standard TEI (versioned)
  output/                 # Generated pipeline data (not versioned)
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
# Enter Mistral, Anthropic, Gemini keys in .env

# OCR with Mistral (no GPU)
python -m scripts.ocr_pipeline -i data/scans/2310.pdf -e mistral

# Layout analysis (GPU for local Docling, or docling-serve API)
python -m scripts.run_layout_analysis --doc 2310

# Generate TEI-XML (no GPU, uses Gemini API)
python -m scripts.tei.tei_unified --doc 2310

# Validate all TEI (RelaxNG + project rules + quality warnings)
python -m scripts.tei.tei_validator --all --html-report

# CER evaluation (no GPU)
python -m scripts.evaluate_ocr --all
python -m scripts.benchmark_cer --all --html

# Frontend data: catalog, thumbnails, per-page mirror for viewer
python -m scripts.generate_edition_data
```

Complete CLI reference: [CLAUDE.md](CLAUDE.md) at the bottom.

## OCR Engines

| Engine | Access | Usage |
|---|---|---|
| Mistral Document AI 2512 | Azure AI Foundry | Production OCR |
| DeepSeek-OCR-2 | Local (GPU) | Development / comparison |
| Claude Haiku 4.5 | Anthropic API | LLM post-correction (optional) |
| Docling 2.75 | Local / docling-serve API | Layout analysis (BBox + regions) |
| Gemini 3.1 Flash Lite | Google AI API | Layout QA/Detect, classification, OCR correction, NER, TEI refinement |

## Documentation

| Topic | File |
|---|---|
| Navigation (start here) | [knowledge/index.md](knowledge/index.md) |
| Project + milestones + corpus | [knowledge/projekt.md](knowledge/projekt.md) |
| Pipeline + engines + TEI mapping | [knowledge/pipeline.md](knowledge/pipeline.md) |
| Entities (NER + GND + Wikidata) | [knowledge/entities.md](knowledge/entities.md) |
| Quality (CER, validation, screening) | [knowledge/quality.md](knowledge/quality.md) |
| Viewer (frontend architecture) | [knowledge/viewer.md](knowledge/viewer.md) |
| Infrastructure (Azure, Podman, CI/CD) | [knowledge/infrastruktur.md](knowledge/infrastruktur.md) |
| Methodology + Promptotyping | [knowledge/methodik.md](knowledge/methodik.md) |
| Decisions + open items | [knowledge/decisions.md](knowledge/decisions.md) |
| Session journal | [knowledge/journal.md](knowledge/journal.md) |

## Team

A project of the Zentralbibliothek Zurich (ZBZ) in collaboration with DHCraft.
