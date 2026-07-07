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

The per-stream workflow status (OCR / Layout / TEI, E66/E67) is `unverified` across the corpus,
the honest default ("pipeline output exists, not yet human-checked"). Content verification by a
domain expert is ZBZ's task, tracked via this status.

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
- The delivered TEI already embeds `<facsimile>` with `<zone>` coordinates per page. Planned
  extensions are `@facs` cross-linking on the text and a provenance drawer in the viewer (see
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
[knowledge/final-report.md](knowledge/final-report.md); the normative method is in
[knowledge/specification.md](knowledge/specification.md).

Live corpus overview with current per-document status:
[chpollin.github.io/zbz-ocr-tei](https://chpollin.github.io/zbz-ocr-tei/) (or `docs/index.html`
locally).

## Scope & limitations

Delivered (in scope): OCR (Mistral), layout analysis (Docling plus Gemini QA), PAGE-XML/METS
export, TEI-XML generation, schema-valid across the corpus.

Removed from scope: NER / entity linking (GND/Wikidata). Implemented earlier, removed (E71):
in the delivered TEI only a small fraction of tagged mentions carried a real GND id, so the
linking, the actual editorial value, was not deliverable. Honest removal over placeholder noise.

ZBZ domain (not produced here): TEI header metadata from Alma (project id / MMSID / PubForm, as
required by the editorial guidelines). An earlier MMSID projection was removed (E76); header
enrichment is the library's Alma-to-header workflow (open item O8). Consequently most delivered
headers still carry an empty container/journal title.

Known limitation, reading order: on two-column and double-page layouts the delivered TEI can
interleave the columns in reading order; validator warning W19 (E90) scopes the affected pages.
The generator fix is built, and a reversible corpus-wide preview confirms it corrects the large
majority of affected pages (`reports/m3-reassemble-preview.md`); a small residue needs facsimile
review because OCR and layout segmentation disagree there. Rolling the fix out rewrites the
delivered TEI and awaits operator approval (M3, see [knowledge/decisions.md](knowledge/decisions.md)
E90).

Pending / not done:
- Reading-order rollout (M3): generator fix and reversible preview exist (see known limitation
  above); the corpus regeneration that rewrites the delivered TEI is operator-gated.
- Containerization (Podman) and GitLab-UZH CI, decided (E9/E10), not built. A GitHub Actions test
  gate (full pytest suite on every push/PR) exists.
- Human verification of the corpus: ZBZ's downstream task, tracked via the per-stream workflow
  status (milestone M5; see [Status](#status-acceptance--handover)).
- Live facsimile images: only four demo documents are committed (`1000`, `1330`, `1540`, `2310`);
  the rest are local-only, so the GitHub Pages viewer shows scans only for those four.

Measurement caveat: ground truth exists only for the 25 reference documents, so corpus-wide quality
(dictionary hit rate) is an estimate, not a measurement. See
[knowledge/specification.md](knowledge/specification.md), quality measurement section.

## Frontend

Static site under `docs/`, deployed via GitHub Pages, no backend; all data is loaded from static
JSON/XML/MD files under `docs/data/`. The viewer (`docs/viewer.html`) is a single-page inspector
(OpenSeadragon facsimile, layout overlay, OCR/TEI panel, per-panel edit toggle) with a single
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

# Configure API keys
cp .env.example .env
# Enter Mistral, Anthropic, Gemini keys in .env

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
| Ecosystem synthesis (zbz / szd-htr / teiCrafter) | [knowledge/ecosystem-synthesis.md](knowledge/ecosystem-synthesis.md) |
| Infrastructure (Azure, Podman, CI/CD) | [knowledge/infrastructure.md](knowledge/infrastructure.md) |
| Methodology + Promptotyping | [knowledge/methodology.md](knowledge/methodology.md) |
| Final work report (delivery synthesis) | [knowledge/final-report.md](knowledge/final-report.md) |
| Decisions + open items | [knowledge/decisions.md](knowledge/decisions.md) |
| Session journal | [knowledge/journal.md](knowledge/journal.md) |

## Team

A project of the Zentralbibliothek Zurich (ZBZ) in collaboration with DHCraft.
