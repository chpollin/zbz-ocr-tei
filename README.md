# ZBZ-OCR-TEI

LLM-powered OCR and TEI pipeline for the Jeanne Hersch Edition at the Zentralbibliothek Zurich.

## What does this repo do?

Fully automated end-to-end pipeline for 286 documents (~4,100 pages) from the estate of Jeanne Hersch:

```
PDF-Scans -> Images -> OCR (Mistral) ──┐
                                       ├──► TEI-XML ──► workflow status
             (PNG)  -> Layout (Docling)─┘    (Unified:    per stream
                       + Gemini-QA           Scaffold +    (E66/E67)
                       │                     Gemini +
                       │                     Assembly)
                       ▼
                       PAGE-XML (parallel export for coOCR / Transkribus, NOT the TEI input)
```

Note: PAGE-XML is generated in parallel as an export format (for coOCR / Transkribus
compatibility, E13). TEI is produced **directly** from layout JSON + OCR markdown
via `scripts/tei/tei_unified.py` (E22). See [knowledge/workflow.md](knowledge/workflow.md)
for the full end-to-end data flow, the manual round-trip for curated edits, and
the planned `_complete.xml` variant with embedded `<facsimile>` / `<zone>`.

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
| TEI-XML (Unified Pipeline) | Scaffold + Gemini + RelaxNG validation | Done (285/285) |
| Workflow status per stream | Manifest + revisionDesc projection | Done (replaces agent screening, E66/E67) |

Current metrics: see [Korpus-Uebersicht](https://chpollin.github.io/zbz-ocr-tei/) (GitHub Pages) or `docs/index.html` locally. Detailed status: [knowledge/projekt.md](knowledge/projekt.md).

## Frontend

Three static HTML pages under `docs/`, deployed via GitHub Pages:

- `docs/index.html` &mdash; corpus overview with thumbnails, search, filters, workflow status
- `docs/viewer.html` &mdash; per-document inspector: OpenSeadragon facsimile (pan/zoom, E58) + layout overlay + OCR/TEI panel + per-panel edit toggle (E60)
- `docs/about.html` &mdash; project info

All data is loaded from static JSON/XML/MD files under `docs/data/`. No backend. Editor changes (layout corrections, transcription edits) are exported as file downloads; full round-trip to the pipeline is manual (see [knowledge/workflow.md](knowledge/workflow.md)).

Frontend dependencies are loaded from CDN at runtime — no build pipeline:

| Library | Version | CDN | Used for |
|---|---|---|---|
| OpenSeadragon | 5.0.1 | jsDelivr | facsimile viewer in view mode (E58) |
| JSZip | 3.10.1 | cdnjs | ZIP bundles for per-doc and bulk export (E61, planned) |

```bash
python -m http.server 8000 -d docs    # http://localhost:8000/
```

## Directory Structure

```
zbz-ocr-tei/
  knowledge/              # 10 documents incl. navigation index (Single Source of Truth, all lowercase)
  scripts/                # Python pipeline (grouped by domain; inventory: scripts/README.md)
    config.py             # Central configuration
    utils.py              # Shared utilities
    ocr/                  # OCR + correction: ocr_pipeline, gemini_ocr_correct, llm_postprocess, ocr_dedup, classify_docs
    layout/               # Layout analysis (Docling/Gemini) + PAGE-XML/METS + overlays
    tei/                  # TEI-XML pipeline (scaffold, Gemini, assembly, validator, status marker)
    eval/                 # CER benchmark + statistics, quality proxy, corpus audit, HTML report
    edition/              # Catalog/mirror generation, per-object manifest, page extraction
    core/                 # Shared data loaders
  docs/                   # Static frontend (GitHub Pages source)
    index.html            # Corpus overview
    viewer.html           # Per-document viewer
    about.html            # Project info
    css/                  # tokens.css, base.css, viewer.css, catalog.css
    js/                   # core.js, viewer.js, catalog.js, tei-render.js, ...
    data/                 # catalog.json, pages/, thumbs/, tei/
    images/               # Page scans (4 DEMO docs committed: 1000, 1330, 1540, 2310; rest local-only, ~4 GB)
  data/                   # Input + reference data
    source/               # ZBZ delivery, immutable input (mostly not versioned)
      pdf/                # PDF digitizations
      reference_tei/      # reference/gold TEIs (ZBZ-annotated, Transkribus)
      transkribus_page_xml/ # Transkribus PAGE-XML exports
      masterfile/         # Masterfile.xlsx (catalog + steering)
      guidelines/         # editorial guidelines (ZBZ + DTA link)
    schema/               # zbz_hersch.rng (project TEI schema)
    curated_tei/          # curated gold-standard TEI
    doc_metadata.json     # generated Gemini classification (committed cache)
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
python -m scripts.ocr.ocr_pipeline -i data/source/pdf/2310.pdf -e mistral

# Layout analysis (GPU for local Docling, or docling-serve API)
python -m scripts.layout.run_layout_analysis --doc 2310

# Generate TEI-XML (no GPU, uses Gemini API)
python -m scripts.tei.tei_unified --doc 2310

# Validate all TEI (RelaxNG + project rules + quality warnings)
python -m scripts.tei.tei_validator --all --html-report

# CER evaluation (no GPU)
python -m scripts.eval.evaluate_ocr --all
python -m scripts.eval.benchmark_cer --all --html

# Frontend data: catalog, thumbnails, per-page mirror for viewer
python -m scripts.edition.generate_edition_data
```

Complete CLI reference: [CLAUDE.md](CLAUDE.md) at the bottom.

## OCR Engines

| Engine | Access | Usage |
|---|---|---|
| Mistral Document AI 2512 | Azure AI Foundry | Production OCR |
| Claude Haiku 4.5 | Anthropic API | LLM post-correction (optional) |
| Docling 2.75 | Local / docling-serve API | Layout analysis (BBox + regions) |
| Gemini 3.1 Flash Lite | Google AI API | Layout QA/Detect, classification, OCR correction, TEI refinement, opt-in Vision-OCR (`-e gemini`) |

## Documentation

| Topic | File |
|---|---|
| Navigation (start here) | [knowledge/index.md](knowledge/index.md) |
| Project + milestones + corpus | [knowledge/projekt.md](knowledge/projekt.md) |
| Pipeline + engines + TEI mapping | [knowledge/pipeline.md](knowledge/pipeline.md) |
| **End-to-end workflow + save mechanism + round-trip + provenance concept** | **[knowledge/workflow.md](knowledge/workflow.md)** |
| Quality (CER, validation, screening) | [knowledge/quality.md](knowledge/quality.md) |
| Viewer (frontend architecture, OSD, edit toggles, export) | [knowledge/viewer.md](knowledge/viewer.md) |
| Infrastructure (Azure, Podman, CI/CD) | [knowledge/infrastruktur.md](knowledge/infrastruktur.md) |
| Methodology + Promptotyping | [knowledge/methodik.md](knowledge/methodik.md) |
| Decisions + open items (E1–E72) | [knowledge/decisions.md](knowledge/decisions.md) |
| Session journal | [knowledge/journal.md](knowledge/journal.md) |

## Team

A project of the Zentralbibliothek Zurich (ZBZ) in collaboration with DHCraft.
