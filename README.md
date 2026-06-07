# ZBZ-OCR-TEI

LLM-powered OCR and TEI pipeline for the Jeanne Hersch Edition at the Zentralbibliothek Zurich.

## Status (acceptance / handover)

The pipeline is complete and its output is schema-valid; the **edition is not yet
content-verified**. These are two different things, and the distinction matters for the
handover:

- **Pipeline** &mdash; all six stages are built and have run across the corpus. **285/285**
  final TEI files validate against the project schema `zbz_hersch.rng` (test-gated, E68).
- **Edition** &mdash; no document has been reviewed by a domain expert yet. The per-stream
  workflow status (OCR / Layout / TEI, E66/E67) is **`unverified` for all 285 documents** &mdash;
  the honest default ("pipeline output exists, not yet human-checked"). Expert curation in the
  viewer is the remaining step (milestone M5).

In short: this repository delivers a high-quality, schema-valid **starting point** for the
edition, plus the tooling to verify and curate it &mdash; not a finished, signed-off edition.
See [Scope & limitations](#scope--limitations) for what is in scope, out of scope, and pending.

## What does this repo do?

End-to-end pipeline for the estate of Jeanne Hersch: **286 delivered PDFs (~4,120 pages)**,
of which **285 have a final TEI** (doc `10` has incomplete OCR). Funnel verified by
`python -m scripts.eval.corpus_audit`: 325 catalogued texts &rarr; 289 digitized &rarr; 286
delivered as PDF &rarr; 285 with final TEI.

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

Notes:
- PAGE-XML is generated in parallel as an export format (for coOCR / Transkribus
  compatibility, E13). TEI is produced **directly** from layout JSON + OCR markdown via
  `scripts/tei/tei_unified.py` (E22).
- The delivered TEI already embeds `<facsimile>` with `<zone>` coordinates per page. Planned
  extensions are `@facs` cross-linking on the text and a provenance drawer in the viewer
  (see [knowledge/workflow.md](knowledge/workflow.md)).

## Pipeline Components

| Component | Engine | Status |
|---|---|---|
| Image extraction | Python (PDF to PNG) | Built |
| Document classification | Gemini Flash Lite | Built |
| OCR | Mistral Document AI (Azure) | Built |
| OCR correction | Gemini Flash Lite | Sample / opt-in |
| Layout analysis | Docling RT-DETR V2 / docling-serve | Built |
| Layout QA/Detect | Gemini Flash Lite | Built |
| PAGE-XML + METS | Rule-based generator | Built |
| TEI-XML (Unified Pipeline) | Scaffold + Gemini + RelaxNG validation | Built &mdash; 285/285 schema-valid |
| Workflow status per stream | Manifest + revisionDesc projection | Built &mdash; all 285 currently `unverified` (E66/E67, replaces agent screening) |

*"Built" means the stage is implemented and has run across the corpus &mdash; **not** that the
output is human-verified. See [Status](#status-acceptance--handover).* Detailed component
status: [knowledge/projekt.md](knowledge/projekt.md).

## Quality at a glance

End-to-end character error rate against 25 ZBZ reference TEIs (Transkribus ground truth),
BCa bootstrap, seed 42 (regenerate via `scripts/eval/cer_statistics_full.py`):

| Metric | Median | Mean | 95% CI (mean) |
|---|---|---|---|
| **Fidelity CER** (the quality measure) | **1.83%** | **4.26%** | [2.39%, 6.48%] |

By Transkribus quality bands the median is "excellent", the mean "good". Caveat: the ZBZ
reference TEIs are selective **partial** transcriptions, so naive full-text CER (mean 20.75%)
is a diagnostic artifact, not a quality measure &mdash; the fidelity CER isolates real
OCR/transcription errors from "the pipeline produced more text than the reference". Full
methodology, stratified values, limitations and literature comparison:
[docs/methode.html](docs/methode.html) and [knowledge/quality.md](knowledge/quality.md).

Live corpus overview with current per-document status:
[chpollin.github.io/zbz-ocr-tei](https://chpollin.github.io/zbz-ocr-tei/) (or `docs/index.html` locally).

## Scope & limitations

**Delivered (in scope):** OCR (Mistral), layout analysis (Docling + Gemini QA),
PAGE-XML/METS export, TEI-XML generation &mdash; 285/285 schema-valid.

**Removed from scope:** NER / entity linking (GND/Wikidata). Implemented earlier, removed
(E71): in the delivered TEI only ~2.6% of tagged mentions carried a real GND id, so the
linking &mdash; the actual editorial value &mdash; was not deliverable. Honest removal over
placeholder noise.

**ZBZ domain (not produced here):** TEI header metadata from Alma (project id / MMSID /
PubForm, as required by the editorial guidelines). An earlier MMSID projection was removed
(E76); header enrichment is the library's Alma&rarr;header workflow (open item O8).
Consequently 195/285 delivered headers still carry an empty container/journal title.

**Pending / not done:**
- Containerization (Podman) and CI/CD (GitLab UZH) &mdash; decided (E9/E10), not built.
- Human verification of all 285 documents (milestone M5).
- Live facsimile images: only 4 demo documents are committed (`1000`, `1330`, `1540`,
  `2310`); the rest are local-only (~4 GB), so the GitHub Pages viewer shows scans only for
  those four.

**Measurement caveat:** ground truth exists for only 25 of 285 documents; corpus-wide quality
(dictionary hit rate, median 97.7%) is an estimate, not a measurement.

## Frontend

Five static HTML pages under `docs/`, deployed via GitHub Pages:

- `docs/index.html` &mdash; corpus overview with thumbnails, search, filters, workflow status
- `docs/viewer.html` &mdash; per-document inspector: OpenSeadragon facsimile (pan/zoom, E58) + layout overlay + OCR/TEI panel + per-panel edit toggle (E60)
- `docs/methode.html` &mdash; quality & method (CER headline, stratified values, limitations, literature)
- `docs/about.html` &mdash; project info
- `docs/impressum.html` &mdash; legal notice

All data is loaded from static JSON/XML/MD files under `docs/data/`. No backend. A single **"Speichern"**
button persists all unsaved streams at once (layout, text/TEI, manifest); changes are written directly
into the working tree via the File System Access API (Chromium; the repo folder is picked once on first
save) or exported as file downloads. Each save writes both the canonical `output/` path (consumed by the
pipeline) and the `docs/data/` mirror, so a reload reflects the edit (E78/E79); folding curated edits back
into the final TEI via `--reassemble` is manual (see [knowledge/workflow.md](knowledge/workflow.md)).
On the public site, facsimile scans are present only for the 4 demo documents listed above.

Frontend dependencies are loaded from CDN at runtime &mdash; no build pipeline:

| Library | Version | CDN | Used for |
|---|---|---|---|
| OpenSeadragon | 5.0.1 | jsDelivr | facsimile viewer in view mode (E58) |
| JSZip | 3.10.1 | cdnjs | per-doc / bulk export (E61) &mdash; planned, export module not yet wired in |

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
    ocr/                  # OCR + correction: ocr_pipeline, gemini_ocr_correct, llm_postprocess, classify_docs
    layout/               # Layout analysis (Docling/Gemini) + PAGE-XML/METS + overlays
    tei/                  # TEI-XML pipeline (scaffold, Gemini, assembly, validator, status marker)
    eval/                 # CER benchmark + statistics, quality proxy, corpus audit, HTML report
    edition/              # Catalog/mirror generation, per-object manifest, page extraction
    core/                 # Shared data loaders
  docs/                   # Static frontend (GitHub Pages source)
    index.html            # Corpus overview
    viewer.html           # Per-document viewer
    methode.html          # Quality & method
    about.html            # Project info
    impressum.html        # Legal notice
    assets/css/           # tokens.css, base.css, viewer.css, catalog.css
    assets/js/            # core.js, viewer.js, catalog.js, tei-render.js, layout-editor.js, ...
    data/                 # catalog.json, pages/, thumbs/, manifests/, tei/
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

The delivered corpus was produced with the engines below; re-running any stage requires valid
API keys in `.env`. The existing pipeline output lives under `output/` (gitignored, regenerable).

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

Verify the corpus and test gates at any time:

```bash
python -m scripts.eval.corpus_audit          # funnel 325 -> 289 -> 286 -> 285, drift check
python -m pytest -q                           # full test suite (incl. 285/285 schema gate)
```

Complete CLI reference: [CLAUDE.md](CLAUDE.md) at the bottom.

## OCR Engines

| Engine | Access | Usage |
|---|---|---|
| Mistral Document AI 2512 | Azure AI Foundry | Production OCR (produced the delivered corpus) |
| Claude Haiku 4.5 | Anthropic API | LLM post-correction (optional, E17) |
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
| Decisions + open items (E1–E76) | [knowledge/decisions.md](knowledge/decisions.md) |
| Session journal | [knowledge/journal.md](knowledge/journal.md) |

## Team

A project of the Zentralbibliothek Zurich (ZBZ) in collaboration with DHCraft.
