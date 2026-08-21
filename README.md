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

The per-stream workflow status (OCR / Layout / TEI / Entities, E66/E67/E77) is `unverified` as
the handover default ("pipeline output exists, not yet human-checked"); isolated documents are
already advanced (see the live catalog). Content verification by a domain expert is ZBZ's task,
tracked via this status.

In short, this repository delivers a high-quality, schema-valid data starting point plus curation
tooling for the ZBZ edition; the edition itself is ZBZ's downstream product. See
[Scope & limitations](#scope--limitations) for what is in scope, out of scope, and pending.

## What does this repo do?

End-to-end pipeline for the estate of Jeanne Hersch: the delivered PDFs are turned into OCR text,
layout, and schema-valid TEI. The corpus funnel from catalogued texts to digitized to delivered
as PDF to final TEI is generated and drift-checked by `python -m scripts.eval.corpus_audit`; the
current figures and the four-unit page reconciliation live in
[knowledge/project.md §Corpus](knowledge/project.md).

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
  [knowledge/workflow.md](knowledge/workflow.md)).

Component status per stage: [knowledge/project.md §Component Status](knowledge/project.md).
Engines and TEI mapping: [knowledge/pipeline.md](knowledge/pipeline.md).

## Quality

The quality measure is the fidelity character error rate against the fixed set of 25 ZBZ reference
TEIs (Transkribus ground truth), which isolates real OCR and transcription errors from cases where
the pipeline produced more text than the selective reference. It is calibrated against print-OCR
literature rather than HTR quality bands (E80), placing the pipeline in the solid range for
historical print. Caveat: the ZBZ reference TEIs are partial transcriptions, so naive full-text CER
is a diagnostic artifact, not a quality measure. Full methodology, stratified values, limitations,
and the literature comparison, with all current values: [docs/methode.html](docs/methode.html) and
[knowledge/arbeitsbericht-v3.md](knowledge/arbeitsbericht-v3.md); the normative method is in
[knowledge/specification.md](knowledge/specification.md).

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
([reports/2026-08-12_entity-eval-ergebnis.md](reports/2026-08-12_entity-eval-ergebnis.md));
the delivered TEI under `output/tei_final/` carries no entity markup yet, the stock run is
operator-gated. Design and method: [knowledge/entity-integration.md](knowledge/entity-integration.md),
[knowledge/entity-evaluation.md](knowledge/entity-evaluation.md).

ZBZ domain (not produced here): TEI header metadata from Alma (project id / MMSID / PubForm, as
required by the editorial guidelines). An earlier MMSID projection was removed (E76); header
enrichment is the library's Alma-to-header workflow (open item O8). Consequently most delivered
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

Measurement caveat: ground truth exists only for the 25 reference documents, so corpus-wide quality
(dictionary hit rate) is an estimate, not a measurement. See
[knowledge/specification.md](knowledge/specification.md), quality measurement section.

## Frontend

Static site under `docs/`, deployed via GitHub Pages, no backend; all data is loaded from static
JSON/XML/MD files under `docs/data/`. The viewer (`docs/viewer.html`) is a single-page inspector
(OpenSeadragon facsimile, layout overlay, OCR/TEI panel with a read-only entity preview layer,
per-panel edit toggle) with a single
"Save" button that persists all unsaved streams at once, written directly into the working
tree via the File System Access API (Chromium) or exported as downloads. Architecture, save
mechanism, CDN dependencies, and design system: [knowledge/workflow.md](knowledge/workflow.md).

```bash
python -m http.server 8000 -d docs    # http://localhost:8000/
```

## Getting started

Re-running any stage requires valid API keys in `.env`. The existing pipeline output lives under
`output/` (gitignored, regenerable).

```bash
# Set up environment
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -r requirements.txt

# Configure API keys: create .env in the repo root (never committed) with
#   MISTRAL_DOC_AI_ENDPOINT / MISTRAL_DOC_AI_KEY   (OCR, Azure)
#   GEMINI_API_KEY                                 (layout QA, TEI refinement)
#   ANTHROPIC_API_KEY                              (optional, correction variant C)
#   TRANSKRIBUS_USER / TRANSKRIBUS_PASSWORD        (only for the Transkribus upload)

# Representative commands
python -m scripts.ocr.ocr_pipeline -i data/source/pdf/2310.pdf -e mistral   # OCR (Mistral)
python -m scripts.tei.tei_unified --doc 2310                                 # generate TEI-XML
python -m scripts.tei.tei_validator --all --html-report                      # validate corpus
python -m scripts.eval.corpus_audit                                          # corpus funnel + drift check
```

Complete CLI reference: [CLAUDE.md §Commands](CLAUDE.md).

## Documentation

| Topic | File |
|---|---|
| Navigation (start here) | [knowledge/index.md](knowledge/index.md) |
| Project + milestones + corpus | [knowledge/project.md](knowledge/project.md) |
| Pipeline + engines + TEI mapping | [knowledge/pipeline.md](knowledge/pipeline.md) |
| End-to-end workflow + viewer + save mechanism + round-trip + provenance concept | [knowledge/workflow.md](knowledge/workflow.md) |
| Requirements, quality method, validation rules, epics + user stories | [knowledge/specification.md](knowledge/specification.md) |
| Ecosystem synthesis (zbz / szd-htr / teiCrafter), dated snapshot | [reports/2026-06-07_ecosystem-synthesis.md](reports/2026-06-07_ecosystem-synthesis.md) |
| Infrastructure (Azure, Podman, CI/CD) | [knowledge/infrastructure.md](knowledge/infrastructure.md) |
| Methodology + Promptotyping | [knowledge/methodology.md](knowledge/methodology.md) |
| CER measurement method | [knowledge/cer-methodology.md](knowledge/cer-methodology.md) |
| Print-OCR state of research | [knowledge/literature-comparison.md](knowledge/literature-comparison.md) |
| Reference TEIs, phenomenon map | [knowledge/ground-truth-map.md](knowledge/ground-truth-map.md) |
| Entity integration (design + built state) | [knowledge/entity-integration.md](knowledge/entity-integration.md) |
| Entity evaluation (method + execution record) | [knowledge/entity-evaluation.md](knowledge/entity-evaluation.md) |
| Multi-agent wave pattern | [knowledge/agent-orchestration.md](knowledge/agent-orchestration.md) |
| Final work report (delivery synthesis, German) | [knowledge/arbeitsbericht-v3.md](knowledge/arbeitsbericht-v3.md) |
| Decisions + open items | [knowledge/decisions.md](knowledge/decisions.md) |
| Session journal | [knowledge/journal.md](knowledge/journal.md) |

## Team

A project of the Zentralbibliothek Zurich (ZBZ) in collaboration with DHCraft.

## Licence

The code in this repository is released under the MIT Licence (see `LICENSE`).
Documentation, knowledge documents, and other textual content are licensed under
CC BY 4.0. Third-party research data is excluded from these terms; the source
material and the edition texts remain with the Zentralbibliothek Zürich.
