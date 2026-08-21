# ZBZ-OCR-TEI

LLM-powered OCR and TEI pipeline for the Jeanne Hersch Edition at the Zentralbibliothek Zurich.

## Status (acceptance / handover)

This repository is a tool that produces edition-ready *data* (OCR text, layout, schema-valid TEI)
plus the tooling to verify and curate it. The edition itself is built and published by ZBZ
downstream (Oxygen / Alma / Swisscovery). Two things matter for the handover, and they are
different.

### Pipeline (this repo's deliverable)

All six stages are built and have run across the corpus; every final TEI validates against the
project schema `zbz_hersch.rng` (test-gated, E68).

### Verification status of the delivered data

The per-stream workflow status (OCR / Layout / TEI, E66/E67/E77; an `entities` stream exists only
where an entity preview does) is `unverifiziert` as the handover default, meaning the pipeline
output exists and is not yet human-checked; isolated documents are already advanced (see the live
catalog). Content verification by a domain expert is ZBZ's task, tracked via this status. The
edition itself is ZBZ's downstream product; see [Scope & limitations](#scope--limitations) for what
is in scope, out of scope, and pending.

## What does this repo do?

End-to-end pipeline for the estate of Jeanne Hersch. The delivered PDFs are turned into OCR text,
layout, and schema-valid TEI. The corpus funnel from catalogued texts to digitized to delivered
as PDF to final TEI is generated and drift-checked by `python -m scripts.eval.corpus_audit`; the
current figures and the four-unit page reconciliation live in
[knowledge/project.md](knowledge/project.md), data section.

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
- PAGE-XML is generated in parallel as an export format (for coOCR / Transkribus compatibility,
  E13). TEI is produced directly from layout JSON plus OCR markdown via
  `scripts/tei/tei_unified.py` (E22).
- The delivered TEI embeds `<facsimile>` with `<zone>` coordinates per page and carries `@facs`
  on `pb`, `p`, `lb` and `note`; the generated mirror ships a per-document facsimile map
  `{doc}_facs.json` (E114). Still planned is the provenance drawer in the viewer (see
  [knowledge/decisions.md](knowledge/decisions.md), plan section).

Delivered scope: [knowledge/project.md](knowledge/project.md), scope of functions; open milestones: [knowledge/decisions.md](knowledge/decisions.md), plan section.
Engines: [knowledge/pipeline.md](knowledge/pipeline.md); TEI mapping: [knowledge/tei-mapping.md](knowledge/tei-mapping.md).

## Quality

The quality measure is the fidelity character error rate against the fixed set of 25 ZBZ reference
TEIs (Transkribus ground truth), which isolates real OCR and transcription errors from cases where
the pipeline produced more text than the selective reference. It is calibrated against the
print-OCR literature (E80). The ZBZ reference TEIs are partial transcriptions, so a naive full-text
CER measures the difference in scope between reference and pipeline and serves as a diagnostic.
Full methodology, stratified values, limitations and the literature comparison, with all current
values, are on two pages.

- [docs/methode.html](docs/methode.html), the method page of the site
- [docs/project-report.md](docs/project-report.md), the client report

The normative method is in [knowledge/specification.md](knowledge/specification.md).

Live corpus overview with current per-document status:
[chpollin.github.io/zbz-ocr-tei](https://chpollin.github.io/zbz-ocr-tei/) (or `docs/index.html`
locally).

## Scope & limitations

Delivered (in scope): OCR (Mistral), layout analysis (Docling plus Gemini QA), PAGE-XML/METS
export, TEI-XML generation, schema-valid across the corpus.

Entity annotation (GND): rebuilt in 2026-08 as a controlled two-tier layer after the earlier
free NER was removed (E71). A deterministic matcher binds mentions to the curated ZBZ entity
list (persons, organisations, works; ids are never assigned by an LLM, E62); sure matches are
auto-marked in read-only previews, everything uncertain lands on a review worklist. The layer
is measured by facsimile-adjudicated sampling
([knowledge/verification.md](knowledge/verification.md), finding register and appendix);
the delivered TEI under `output/tei_final/` carries no entity markup yet, the stock run is
operator-gated. Rules: [knowledge/tei-mapping.md](knowledge/tei-mapping.md); instruments: [knowledge/pipeline.md](knowledge/pipeline.md), entity stage;
measurement: [knowledge/verification.md](knowledge/verification.md).

Header metadata from Alma (project id / MMSID / PubForm, as required by the editorial guidelines)
comes from the library's own Alma-to-header workflow (open item O8); an earlier MMSID projection
in the pipeline was removed (E76). Consequently most delivered
headers still carry an empty container/journal title.

Known limitation, reading order: on two-column and double-page layouts the delivered TEI can
interleave the columns in reading order; validator warning W19 (E90) scopes the affected pages.
Machine reordering was tested against the 25 reference documents and refuted (E99: zero pages
improved, nine degraded), so no automated corpus reorder runs on either path. W19 pages are
treated as suspect zone assignment over correct text and resolve through facsimile-verified,
page-wise curation (`tei_reading_order_fix`, operator-gated; see
[knowledge/decisions.md](knowledge/decisions.md) E99).

Pending / not done:
- Reading-order curation: facsimile-verified page-wise fixes via the W19 worklist (machine
  rollout refuted, E99; see known limitation above).
- Containerization (Podman) and GitLab-UZH CI, decided (E9/E10), not built. A GitHub Actions test
  gate (full pytest suite on every push/PR) exists.
- Human verification of the corpus: ZBZ's downstream task, tracked via the per-stream workflow
  status (milestone M5; see [Status](#status-acceptance--handover)).
- Live facsimile images: only five demo documents are committed (`1000`, `1330`, `1540`, `1620`,
  `2310`); the rest are local-only, so the GitHub Pages viewer shows scans only for those five.

Ground truth exists only for the 25 reference documents, so corpus-wide quality (dictionary hit
rate) remains an estimate. See
[knowledge/specification.md](knowledge/specification.md), quality measurement section.

## Frontend

Static site under `docs/`, deployed via GitHub Pages, no backend; all data is loaded from static
JSON/XML/MD files under `docs/data/`. The viewer (`docs/viewer.html`) is a single-page inspector
(OpenSeadragon facsimile, layout overlay, OCR/TEI panel with a read-only entity preview layer,
per-panel edit toggle) with a single
"Save" button that persists all unsaved streams at once, written directly into the working
tree via the File System Access API (Chromium) or exported as downloads. Architecture, save
mechanism, vendored assets and design system: [knowledge/workflow.md](knowledge/workflow.md).

```bash
python -m http.server 8000 -d docs    # http://localhost:8000/
```

## Getting started

The source PDFs and the Masterfile are the ZBZ delivery and are not part of the repository, and
the pipeline output under `output/` is gitignored, so a fresh clone reproduces the environment and
the test suite (data-bound tests skip themselves) while the pipeline commands need the delivery.
The model-backed stages (OCR, layout QA, TEI refinement) need API keys in `.env`; validation and
the audits run without.

`pyproject.toml` is the only manifest; the repo declares no build backend, because it is a
dependency set and script pipeline rather than an installable package. The heavy layout
engines are the optional extra `layout`, the quality gate is the extra `dev` (pytest plus the
pinned ruff that the pre-commit hook and CI both use).

```bash
# Set up environment (uv)
uv sync --extra dev

# or with pip
python -m venv .venv
.venv\Scripts\activate  # Windows
python -c "import tomllib; p = tomllib.load(open('pyproject.toml', 'rb'))['project']; print('\n'.join(p['dependencies'] + p['optional-dependencies']['dev']))" > zbz-requirements.txt
pip install -r zbz-requirements.txt   # generated list, delete afterwards

# Configure API keys: create .env in the repo root (never committed); the variable table is in
# knowledge/pipeline.md, environment variables section

# Representative commands
python -m scripts.ocr.ocr_pipeline -i data/source/pdf/2310.pdf -e mistral   # OCR (Mistral)
python -m scripts.tei.tei_unified --doc 2310                                 # generate TEI-XML
python -m scripts.tei.tei_validator --all --html-report                      # validate corpus
python -m scripts.eval.corpus_audit                                          # corpus funnel + drift check
```

Complete CLI reference: [CLAUDE.md §Commands](CLAUDE.md).

The commit hook is optional and self-contained: install `pre-commit` and run
`pre-commit install`; it runs the same pinned `ruff check` that CI runs.

## Documentation

The knowledge base holds ten documents; [knowledge/index.md](knowledge/index.md) is the entry point with reading paths and the function map.

| Topic | File |
|---|---|
| Navigation, reading paths, glossary | [knowledge/index.md](knowledge/index.md) |
| Charter, corpus and data, integration with ZBZ, Transkribus and teiCrafter | [knowledge/project.md](knowledge/project.md) |
| Requirements, quality method, validation rules, gates, epics, scope | [knowledge/specification.md](knowledge/specification.md) |
| TEI markup rulebook and entity target model | [knowledge/tei-mapping.md](knowledge/tei-mapping.md) |
| Pipeline stages, engines, entity stage, deployment, CI, viewer delivery | [knowledge/pipeline.md](knowledge/pipeline.md) |
| End-to-end workflow, viewer, save mechanism, round trip, provenance, design system | [knowledge/workflow.md](knowledge/workflow.md) |
| Methodology, CER measurement method, state of research, governance | [knowledge/methodology.md](knowledge/methodology.md) |
| Quality assurance (test suite), verification of claims, dated protocols and results | [knowledge/verification.md](knowledge/verification.md) |
| Decision register and plan (milestones, open decisions) | [knowledge/decisions.md](knowledge/decisions.md) |
| Session journal with archive | [knowledge/journal.md](knowledge/journal.md) |

The client report for ZBZ (German, a dated snapshot) lives on the site as
[docs/project-report.md](docs/project-report.md).

## Team

A project of the Zentralbibliothek Zürich (ZBZ) in collaboration with DHCraft.

## Citation

`CITATION.cff` at the repository root is the canonical citation record; `codemeta.json` carries
the same metadata for software catalogues.

## License

The code in this repository is released under the MIT License (see `LICENSE`).
Documentation, knowledge documents, and other textual content are licensed under
CC BY 4.0. Third-party research data is excluded from these terms; the source
material and the edition texts remain with the Zentralbibliothek Zürich.
