# ZBZ-OCR-TEI

LLM-powered OCR and TEI pipeline for the Jeanne Hersch Edition at the Zentralbibliothek Zurich.

## What does this repo do?

Fully automated end-to-end pipeline for 286 documents (4,152 pages) from the estate of Jeanne Hersch:

```
PDF-Scans --> Images --> OCR --> Layout --> PAGE-XML --> NER/Wikidata --> TEI-XML
              (PNG)     (Mistral)  (Docling)              (Gemini)       (DTA-Basisformat)
```

## Status (09.03.2026)

286 PDFs received (E23). OCR + Layout + Classification + PAGE-XML complete for all documents. TEI Unified pipeline validated on 51 docs. NER extraction complete (285/286 docs), 49 docs with entity markup. Wikidata linking 67/285 docs (15%), rest pending.

| Component | Status | Result |
|-----------|--------|--------|
| Image extraction | 286/286 Docs | 4,152 page images (PNG) |
| Document classification | 286/286 Docs | Gemini 3.1 Flash Lite (Stage 1a, E27) |
| OCR (Mistral) | 286/286 Docs | CER 6.42% (15 Pilot-Docs evaluated) |
| Gemini OCR correction | 5/286 Docs | CER 3.97% -> 3.30% (Stage 2b, E29) |
| Layout analysis (Docling) | 286/286 Docs | 4,152 layout JSONs, RTX 4060 ~5s/page |
| Gemini Layout QA/Detect | 286/286 Docs | Auto mode: QA for good, detect for bad pages (E25/E26) |
| PAGE-XML + METS | 286/286 Docs | 4,091 PAGE-XML + 286 METS (Transkribus-compatible) |
| TEI Unified | 51/286 Docs | Scaffold + Gemini Refinement + RelaxNG Validation (E32) |
| NER Extraction | 285/286 Docs | 11,685 entities, 26,197 mentions (Gemini Flash Lite, E34/E35) |
| Entity Index | 4,100 entries | TEI-XML indices in `data/entities/`, 341 with Wikidata QIDs |
| TEI NER Injection | 49/286 Docs | Entity markup in `output/tei_ner/`, all validated VALID |
| Wikidata Linking | 67/285 Docs | 15% resolution, remaining 218 docs pending |
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

### Curation Editor (E36)

Browser-basierter Editor fuer manuelle Kuration der Pipeline-generierten TEI-XML. Editoren korrigieren Text, Struktur und Entities direkt im Reader (Edit-Modus). Ein lokaler FastAPI-Server speichert kuratiertes TEI in `data/tei_curated/` (git-tracked, versioniert).

```bash
python -m scripts.server.curation_server    # http://localhost:8000
```

Features: WYSIWYG Text-Editing, Block-Toolbar (Typ/Split/Merge), Entity-Tagging mit Autocomplete (Entity Index + Wikidata), RelaxNG-Validierung, Review-Workflow (draft > in_review > approved). Details: [CURATION.md](knowledge/CURATION.md).

### Next Steps

TEI Unified production run (remaining 235 docs) -> Wikidata linking completion -> TEI NER injection -> Curation pilot -> Production delivery. Details: [PLAN.md](knowledge/PLAN.md), [EDITION.md](knowledge/EDITION.md), [CURATION.md](knowledge/CURATION.md).

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
  docs/                   # Dashboard + QA viewer (GitHub Pages)
    index.html            # Dashboard: metrics, document catalog, CER comparison
    viewer.html           # 3-panel viewer: facsimile + OCR + TEI/PAGE-XML
    benchmark.html        # OCR engine comparison (Mistral vs DeepSeek)
    tei-viewer.js         # TEI rendering: rendered view, diff, entities
    page-viewer.js        # PAGE-XML rendering: regions, XML, METS
    dashboard.js / viewer.js  # Dashboard + viewer logic
    shared.css / shared.js  # Design system + shared utilities
    data/dashboard.json   # Generated data
    data/examples/        # 4 DEMO docs (OCR + Layout for online demo)
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

## Dashboard + Viewer

The QA dashboard (`docs/index.html`) shows pipeline status, CER comparison, and a filterable document catalog. The viewer (`docs/viewer.html`) offers:

- **3-panel layout:** Facsimile + OCR text + TEI-XML or PAGE-XML side by side
- **TEI viewer:** Rendered view, XML with syntax highlighting, reference diff
- **PAGE-XML viewer:** Region cards, syntax-highlighted XML, METS manifest
- **Entity sidebar:** Persons/organizations/places/works with Wikidata + GND links
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
| Digital edition | [knowledge/EDITION.md](knowledge/EDITION.md) |
| Curation Editor | [knowledge/CURATION.md](knowledge/CURATION.md) |
| Work journal | [knowledge/JOURNAL.md](knowledge/JOURNAL.md) |

## Team

A project of the Zentralbibliothek Zurich (ZBZ) in collaboration with DHCraft.

---

*Last updated: 2026-03-09*
