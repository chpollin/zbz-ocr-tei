---
title: Pipeline
project:
  name: zbz-ocr-tei
  repository: https://github.com/chpollin/zbz-ocr-tei.git
method:
  name: Promptotyping
  url: https://dhcraft.org/Promptotyping/
template:
  name: Vorlage Architecture
  version: 0.3
  url: https://dhcraft.org/Promptotyping/promptotyping-document/architecture
status: complete
language: en
version: 1.0
created: 2026-01-29
updated: 2026-08-21
authors: [Christopher Pollin]
related: [index, project, specification, tei-mapping, workflow, methodology, verification, decisions]
absorbed: [infrastructure (Vorlage Architecture 0.3)]
---

# Pipeline

Data flow from PDF to TEI-XML with its stages and scripts, the engines that run them, the
entity preview layer beside them, and the deployment, continuous integration and static
delivery that carry the output. Since the scope expansion (25.02.2026, E21) zbz-ocr-tei
covers the entire path.

CLI reference and operational tools are in [CLAUDE.md](../CLAUDE.md), Commands section.
The markup rules the generator applies are in [tei-mapping.md](tei-mapping.md). The
end-to-end workflow with viewer, save mechanism and provenance is in
[workflow.md](workflow.md), the delivery status per milestone in
[decisions.md](decisions.md), plan section.

## Overview

```
PDF
 |
 v
Images (extract_pages.py)
 |
 +------------------------------+
 v                              v
OCR (base text layer)          Layout (Docling + Gemini QA)
 |                              |
 |                              +--> PAGE-XML (page_xml_generator.py)
 |                              |    = parallel export for coOCR
 |                              |    NOT TEI input (E22)
 |                              |
 +------------------------------+--> TEI-XML (tei_unified.py)
                                     |
                                     v
                                     Workflow status per stream (E66, human-set)
                                     |
                                     v
                                     Evaluation + Viewer
```

PAGE-XML is a parallel export beside the TEI path; the recurring misreading treats it as a
station on that path (E22). TEI is generated directly from layout JSON plus OCR Markdown
via `scripts/tei/tei_unified.py`, and PAGE-XML is produced in parallel for coOCR and
Transkribus (E13). Both derive independently from layout JSON plus OCR.

| Stage | Task | Script | Output | Status |
|---|---|---|---|---|
| 1 | PDF -> PNG | `scripts/edition/extract_pages.py` | PNG (`docs/images/`) | Production |
| 1b | PNG -> JPEG web mirror | `scripts/edition/export_web_images.py` | JPEG for the facsimile repository (`output/web_images/` or `--out`) | Production (E126) |
| 1a | Document classification (Gemini) | `scripts/ocr/classify_docs.py` | `data/doc_metadata.json` + `output/classification/` | Production (full corpus, E27) |
| 2 | OCR | `scripts/ocr/ocr_pipeline.py` (`--engine auto` resolves to Gemini, `-e mistral` reproduces the delivered corpus) | page Markdown (`output/mistral_results/`) | Production |
| 2a | LLM post-correction (optional) | `scripts/ocr/llm_postprocess.py` | `output/llm_corrected_c/` | Production, E17: optional |
| 2b | Gemini OCR correction (optional) | `scripts/ocr/gemini_ocr_correct.py` | `output/gemini_corrected_a/` / `_b/` | Sample (E29) |
| 3 | Layout analysis | `scripts/layout/run_layout_analysis.py` (local GPU) or `run_layout_cloud.py` (docling-serve) | regions + bbox (`output/layout/`) | Production |
| 3a | Layout QA/detect (Gemini) | `scripts/layout/layout_qa_gemini.py --mode {qa\|detect\|auto}` | `_layout_gemini.json` | Production (E25/E26/E31) |
| 3b | Overlay generator | `scripts/layout/generate_layout_overlays.py` | PNGs + side-by-side compare | Production |
| 4 | PAGE-XML + METS | `scripts/layout/page_xml_generator.py` + `mets_generator.py` | `output/page_xml/` | Production |
| 5 | TEI-XML (rule-based) | `scripts/tei/tei_generator.py` | `output/tei/` | Production |
| 5b | Unified TEI Pipeline (E32) | `scripts/tei/tei_unified.py` | `output/tei_unified/` | Production (full corpus) |
| 5b+ | Post-assembly fixes | `tei_step3.py` | fixes E/F/G + heuristic lb injection | Production (Session 34) |
| 5c | TEI validation | `scripts/tei/tei_validator.py` | JSON + HTML report | schema-valid across the delivered corpus (gate: `tests/test_tei_schema.py`); warnings informative (rule catalog in [specification.md](specification.md), current tallies via `python -m scripts.tei.tei_validator --all --report`) |
| 6 | Evaluation | `scripts/eval/evaluate_ocr.py` + `benchmark_cer.py` + `cer_statistics_full.py` | `output/evaluation/` + `docs/data/cer_statistics.json` | Production |

Manual curation (E56) takes place in the pipeline viewer (`docs/viewer.html`) with layout
and transcription editor. A single save writes canonically to `output/` and to the
`docs/data/` mirror (File System Access API, download fallback, E72/E78/E79). The curated
files return into the pipeline through `tei_unified --reassemble`, which selectively
re-refines the changed pages; the round trip with its step sequence, the save mechanism
and the editors are described in [workflow.md](workflow.md), round-trip section.

Quality assurance follows E66. The pipeline asserts no verification state of its own. A
human sets the workflow status per stream in the viewer, and `tei_status_marker.py`
projects that status deterministically into the `<revisionDesc>` of the final TEI (XML
shape in [tei-mapping.md](tei-mapping.md), revision description section). Status values,
traffic-light mapping, history semantics and the streams they cover are described in
[workflow.md](workflow.md), workflow status section.

OCR quality is a measured value. The measurement method is in
[methodology.md](methodology.md), CER measurement section, the requirement in
[specification.md](specification.md), the verification of the published claim in
[verification.md](verification.md), and the measured values in
`docs/data/cer_statistics.json`. The measuring instruments are
`scripts/eval/benchmark_cer.py`, `scripts/eval/cer_statistics.py` and
`scripts/eval/cer_statistics_full.py`.

The GitHub Pages and facsimile repository section below states where the pipeline output is
published and where the online viewer takes its facsimiles from.

## Engines

Three engines are active, one per subsection below. Pipeline design carries more weight
than model choice, since the investments that pay off are chunking, page matching and
quality routing. LLM post-correction hurts at CER below five per cent (E17).

`ocr_pipeline --engine auto` is the documented default and resolves to Gemini
([ocr_pipeline.py](../scripts/ocr/ocr_pipeline.py), lines 295 to 298), which makes Gemini
the effective production OCR engine. The Mistral Document AI path on Azure stays selectable
under `--engine mistral` as the reproducibility record of the delivered corpus, which was
produced with it; the deployed endpoint answers 401 today, so a rerun through that path
needs a new deployment first. Every engine writes its result into the base text layer
directory `output/mistral_results/`, whose name is historical and independent of the engine
that produced the text. The loader priority in
[scripts/core/loaders.py](../scripts/core/loaders.py) reads that base text layer last,
behind curated text, the two Gemini correction variants and the LLM-corrected variant.

The layout hybrid was decided on 25.02.2026 after a comparative engine evaluation, with Docling as the
bbox engine and Gemini as validator and detect fallback; the rationale is registered as
E19 and E20 in [decisions.md](decisions.md).

### Mistral Document AI: the delivered text layer

| Aspect | Details |
|---|---|
| Model | `mistral-document-ai-2512` on Azure AI Foundry (serverless API) |
| Role | produced the delivered text layer of the corpus and stays selectable as its reproducibility record |
| Speed | ~1.3 s/page |
| Output | per-page Markdown (`output/mistral_results/{doc_id}_p{N}.md`) |
| Languages | 36 (de, fr, en, es, it, ...) |
| Limit | 30 pages/request, 30 MB max (pipeline splits automatically) |

Endpoint shape, regions, credentials, setup notes and error diagnosis are in the Mistral
Document AI on Azure section below.

### Docling 2.75: Layout Primary

| Aspect | Details |
|---|---|
| Model | RT-DETR V2 Heron (42.9M, IBM Research, DocLayNet) |
| Role | primary layout engine (layout only, no OCR; RapidOCR has FR encoding problems) |
| Speed | ~5 s/page (RTX 4060 GPU), ~27 s/page (CPU / docling-serve) |
| Detection | 17 block types (Title, Section-header, Text, Footnote, Caption, Page-header/footer, Picture, Table, Formula, ...) |
| API | `scripts/layout/run_layout_cloud.py` -> docling-serve (Docker, IBM official) |

Coverage-based quality scoring is a strong proxy for layout quality and runs on the region
geometry alone. Landscape and multi-column pages are the hard cases (~64% bad vs. ~14%
portrait).

### Gemini 3.1 Flash Lite: Layout QA + Detect + Refinement

| Aspect | Details |
|---|---|
| Model | `gemini-3.1-flash-lite-preview` (`GEMINI_MODEL`); the vision-OCR path uses `gemini-3.1-flash-lite` (`GEMINI_OCR_MODEL`) |
| Roles | layout correction, layout detect (fallback for Docling failures, ~15%), document classification, OCR correction, vision OCR (`-e gemini`, writes to `output/mistral_results/`), TEI refinement |
| SDK | `google-genai` |

Three modes run in `layout_qa_gemini.py`:
- `--mode qa`: overlay PNG + layout JSON to Gemini, labels corrected, false positives removed, quality score 0-100
- `--mode detect`: full re-detection with `box_2d` coordinates (0-1000 scale -> x_pct/y_pct/w_pct/h_pct)
- `--mode auto`: routes per page via `compute_page_quality()` (detect for bad/empty, qa for good/warning)

The routing value is an area coverage. `compute_page_quality`
([layout_qa_gemini.py](../scripts/layout/layout_qa_gemini.py), lines 319 to 344) returns a
quality class, an area-coverage value and the region count per page. Its single call site
(line 691) sends a page classed `bad` or `empty` into re-detection and prints the coverage.
The quality figure that reaches a layout JSON is the Gemini `score` (line 239), so the
coverage steers the run while the score is what later stages read.

Both calls request structured output through `response_schema`. Both layout versions are
kept, `_layout.json` and `_layout_gemini.json`, so the Docling result stays inspectable
beside the Gemini-corrected one and the provenance of a region stays reconstructable.

## TEI mapping

The generator follows the markup rulebook in [tei-mapping.md](tei-mapping.md), which holds
the document structure, page breaks, character normalization, highlighting, special
structures, figures, omissions, the entity target model, the facsimile binding, the
revision description and the element inventory of the delivered corpus. The three stages
of `tei_unified.py` divide the work between them. Step 1
([tei_step1.py](../scripts/tei/tei_step1.py)) builds the rule-based scaffold from layout
JSON and OCR Markdown and produces one body fragment plus its facsimile zones per page.
Step 2 ([tei_step2.py](../scripts/tei/tei_step2.py)) refines each page fragment through
Gemini inside the schema subset and repairs the recurring model errors. Step 3
([tei_step3.py](../scripts/tei/tei_step3.py)) assembles the document, writes the header
and the facsimile block and applies the post-assembly fixes. Since the generator sees one
page at a time, document-level and cross-page structures stay with curation; the rulebook
states which phenomena those are.

## Entity stage (preview layer)

A controlled entity layer sits beside the TEI stages and writes read-only previews. It
binds mentions to the curated ZBZ entity list with a deterministic matcher, marks sure
hits, and holds ambiguous candidates on a review worklist. The markup rules and the
provenance vocabulary are in [tei-mapping.md](tei-mapping.md). The measured precision and
recall live in [verification.md](verification.md), the gates that hold them in its quality
assurance section. The open milestones and the instruments still to be built are in
[decisions.md](decisions.md), plan section. The curated list, the GND variant cache, the
legacy mention index, the variant review and the marking policy are described as input
data in [project.md](project.md), data section.

One rule binds the whole stage. Every instrument leaves `output/tei_final/` untouched and
writes into an output directory of its own; `tei_entity_preview.py` refuses that directory
outright. The operator-gated stock tool `scripts/entity/tei_entity_marker.py` remains to be
built ([decisions.md](decisions.md), plan section, phase A).

| Instrument | Reads | Writes |
|---|---|---|
| `scripts/entity/fetch_gnd_variants.py` | `data/entities/all_entities.json`, lobid | `data/entities/gnd_cache.json` |
| `scripts/entity/entity_lint.py` | entity list, GND cache, legacy mention index, marking policy | `output/audits/entity_lint.json` |
| `scripts/entity/entity_lexicon.py` | entity list, GND cache, variant review, legacy mentions, marking policy | the in-memory lexicon (headwords, inverted forms, cache variants, legacy surfaces, derived-form channels) |
| `scripts/entity/entity_matcher.py` | the lexicon plus a TEI document | candidates with exact offsets, tier and rule; re-exports the lexicon API, so both read as one module from outside |
| `scripts/entity/running_heads.py` | the page-head lines of a document | the running-head zones the matcher demotes into tier 2 |
| `scripts/entity/running_head_audit.py` | scan snapshot, adjudicated verdicts | running-head validation report under `output/audits/` |
| `scripts/entity/tei_entity_preview.py` | `output/tei_final/` read-only, entity data, verdict store | `output/entity_preview/` plus a JSON report |
| `scripts/entity/entity_corpus_scan.py` | `output/tei_final/` read-only, entity data | `output/audits/entity_corpus_scan.json` |
| `scripts/entity/entity_corpus_digest.py` | scan snapshot, entity list | `output/audits/entity_corpus_digest.md` |
| `scripts/entity/entity_unlisted_scan.py` | `output/tei_final/`, entity data, viewer catalog | `output/audits/entity_unlisted_report.json` plus a CSV |
| `scripts/entity/entity_gold_benchmark.py` | the 25 reference TEIs, entity data | `output/audits/entity_gold_benchmark.json` |
| `scripts/entity/entity_eval_sample.py` | scan snapshot, catalog, delivered TEI | `output/audits/eval_sample/` with precision cases, recall pages and the sample manifest |
| `scripts/entity/build_mention_verdicts.py` | frozen scan snapshot, adjudication files under `output/audits/eval_sample/verdicts/` | `data/entities/mention_verdicts.json` |
| `scripts/entity/entity_verdict_guard.py` | verdict store, current scan snapshot | `output/audits/verdict_guard_report.json`, exit 1 on a violation |
| `scripts/entity/entity_risk_ranking.py` | scan snapshot, entity list | `output/audits/fp_hunt/risk_ranking.json` beside its wave protocol |
| `scripts/entity/generate_entity_preview_data.py` | `output/entity_preview/` read-only | `docs/data/pages/{doc}/{doc}_entity_p{N}.xml`, `{doc}_entity_worklist.json`, `docs/data/entities.json` |
| `scripts/entity/generate_entity_overview.py` | scan snapshot, entity list, verdict store | `docs/data/entity_overview.json` for `docs/entities.html` |
| `scripts/tei/tei_cover_strip.py` | `output/tei_final/` | operator-gated cover-sheet removal with backup, report under `output/audits/` |

The variant review is an operator-gated channel maintained by hand.
`data/entities/variant_review.json` carries one verdict per cache-derived name form
(approve, suspect, reject, each with a reason), and `build_lexicon` consumes it
deterministically. A rejected form stays out of the lexicon, a suspect form yields tier-2
candidates only, and a cache form the review does not know counts as suspect until the
next review pass. Headwords of the curated list and legacy forms stay outside its reach.
The operator worklist of all suspect and reject forms lands in
`output/audits/variant_review_report.md`.

Four contracts hold the stage together. The matcher returns candidates that are
offset-verified, non-overlapping and embed at most `lb` tags; it scans only inside `text`
and skips the bibliography div, `bibl` elements that already carry a reference, the library
apparatus and already marked `persName` and `orgName`. Figure captions take part in the
scan and reach the worklist through the `:in-figure` demotion. The preview run proves per
document that the result is RelaxNG-valid against `zbz_hersch.rng` and that the text of the
`text` subtree is character-identical; the test gate adds that stripping the wrappers and
the header declarations restores the original byte for byte. The corpus scan is a diffable
snapshot, so a rule change shows its exact corpus effect before it binds, and a frozen copy
of that snapshot is what an adjudication wave draws from. The verdict store keys a judgment
by document, page, surface, identifier and occurrence index over the frozen snapshot and
carries a sha256 fingerprint of the TEI it was judged on, so a later text change marks the
affected records stale for re-adjudication.

The viewer shows the previews read-only in `viewer.html?doc={DOC_ID}`. The annotated
reading view is the default for every document that has a preview, and `&entities=0` opts
out (E107). It renders category colours, a popover per mention with label, category and
GND link, and a panel for the worklist entries that carry no position in the text; the
rendering is described in [workflow.md](workflow.md), entity layer section.

## ZBZ Structural Tags (Docling -> ZBZ -> PAGE-XML)

| Docling | ZBZ | PAGE-XML |
|---|---|---|
| Title, Section-header | `zb_heading` | heading |
| Text, Paragraph, List-item, Table, Formula | `zb_paragraph` | paragraph |
| Footnote | `footnote` | footnote |
| Caption | `caption` | caption |
| Page-header, Page-footer | `_filter` | (removed) |
| Picture, Figure | `_skip` | - |

The PAGE-XML of stage 4 is also exported as a Transkribus bundle; folder convention,
dialect and upload are in [project.md](project.md), integration section.

## Model APIs and credentials

### Infrastructure overview

| Aspect | Details |
|---|---|
| Model APIs | Google Gemini (resolved default OCR engine, layout QA, TEI refinement), Anthropic (optional post-correction), Azure AI Foundry (Mistral Document AI, reproducibility path) |
| Credentials | environment variables, loaded from an uncommitted `.env` at the repository root |
| Versioning | GitHub for development, GitLab University of Zurich for the production fork |
| Continuous integration | GitHub Actions on the development repository |
| Delivery | static GitHub Pages site served from `docs/`, no backend |
| Pipeline execution | local clone or the production fork; no hosted runtime |

The production fork, its container image and its own CI exist as plan only; the items and
their conditions are in [decisions.md](decisions.md), plan section, phase E, and
the counterpart relationship is in [project.md](project.md), integration section.

### API access

| API | Access | Use |
|---|---|---|
| Gemini 3.1 Flash Lite | Google API | OCR, layout QA and detection, document classification, TEI refinement |
| Claude Haiku | Anthropic API | optional LLM post-correction (E17) |
| Mistral Document AI 2512 | Azure AI Foundry, serverless | reproducibility path for the delivered base text layer |
| Docling Serve | self-hosted or local | layout analysis |
| Transkribus REST | ZBZ account | PAGE-XML upload (E81) |

The roles these engines play in the pipeline are described in the Engines section above.

### Environment variables

Credentials live in a `.env` file at the repository root. The file stays uncommitted, and
the project neither reads nor prints it; no example file is tracked either, so the table
below is the reference for the variable names. `scripts.config` is the single loader, and
other modules read the values from there.

| Variable | Consumer |
|---|---|
| `GEMINI_API_KEY` | Gemini client (`scripts/core/gemini.py`, `scripts/config.py`) |
| `ANTHROPIC_API_KEY` | LLM post-correction (`scripts/ocr/llm_postprocess.py`) |
| `MISTRAL_DOC_AI_ENDPOINT`, `MISTRAL_DOC_AI_KEY` | Mistral path (`scripts/ocr/ocr_pipeline.py`) |
| `DOCLING_SERVE_URL` | layout analysis (`scripts/config.py`) |
| `TRANSKRIBUS_USER`, `TRANSKRIBUS_PASSWORD`, `TRANSKRIBUS_COLLECTION` | Transkribus upload (`scripts/edition/transkribus_upload.py`) |

### Mistral Document AI on Azure

The deployment sits in Azure AI Foundry as a serverless endpoint of
`mistral-document-ai-2512`, available in East US, East US 2, West US, West US 3, South
Central US, North Central US and Sweden Central. The endpoint has the shape
`https://<deployment>.<region>.models.ai.azure.com/v1/ocr`. The call is
`POST {endpoint}/v1/ocr` with a bearer token, the PDF travels base64-encoded in the
`document.document_url` field, and the response returns `pages[]` with `index`, `markdown`,
`images[]` and `dimensions`. The page limit per request named in the engine table above is
enforced by `MistralOCR._split_pdf()`, which splits an oversized document. Bounding-box and
document annotations are available for at most eight pages per request.

The failure modes seen during setup are kept here because they cost time to rediscover.

- A 404 after deployment means the endpoint URL lacks `/v1/ocr`; the host must be
  `*.models.ai.azure.com` and never `*.services.ai.azure.com`.
- A 413 means the PDF is too large and needs compression or splitting.
- Base64 errors come from line breaks inside the encoded string.
- The catalog entry is named "Mistral Document AI" (`mistral-document-ai-2505` and
  `-2512`); a search for "Mistral OCR" finds nothing.

Engine configuration currently lives in `scripts/config.py` and
`scripts/ocr/ocr_pipeline.py`. Moving it into one configuration file is a planned item in
[decisions.md](decisions.md), plan section, phase E.

## Deployment, CI and viewer delivery

### CI/CD

`.github/workflows/tests.yml` runs two gates on every push and pull request under Python
3.11, `ruff check scripts tests` and the full pytest suite. Which part of the suite survives
a fresh checkout, and which markers select it, is owned by
[verification.md](verification.md), quality assurance section.

`pyproject.toml` is the only manifest and declares no build backend, because the repository
is a dependency set and a script pipeline. The workflow therefore materializes the
dependency list from `[project] dependencies` plus the `dev` extra and installs it with
pip. The `dev` extra pins ruff to one version, which the local
`.pre-commit-config.yaml` hook reuses, so hook and CI report the same findings. The heavy
layout engines are the separate optional extra `layout` and stay uninstalled in CI.

### Production fork

The production repository is a fork on the GitLab instance of the University of Zurich; the
fork relationship, its merge direction and its adjustments are described in
[project.md](project.md), integration section. The container image, the GitLab CI
configuration and the merge strategy for upstream changes are planned and specified in
[decisions.md](decisions.md), plan section, phase E.

### Local development

Setup, dependency installation and the `.env` keys are in the README, section "Getting
started". The optional local layout stack has its own requirement, kept here. Docling runs
locally only with CUDA 12.4 or newer and a GPU with at least 8 GB VRAM; on other machines
layout analysis goes through a Docling Serve instance named by `DOCLING_SERVE_URL`. The
hardware check is one command.

```bash
python -m scripts.ocr.ocr_pipeline --check-gpu
```

Python 3.11 or newer is required, matching the CI environment.

### Viewer deployment and local server

The viewer (`docs/`) is a purely static site and runs from any file server.

```bash
python -m http.server 8000 -d docs           # docroot docs/ (mirror data only)
python -m http.server 8000                   # repo root: enables ../output/ fallback (Gemini A/B, LLM engines)
```

In the second case the viewer is reachable under
`http://localhost:8000/docs/viewer.html` and can read all OCR engines in the
`output/` tree. The File System Access write path works under `localhost`
and HTTPS, and every write lands in the local clone.

### GitHub Pages and the facsimile repository (E28, E126)

The repo settings under Settings > Pages carry Source "Deploy from a branch",
branch `main`, folder `/docs`. The `.nojekyll` file in the directory
prevents Pages from interpreting the content as a Jekyll site.

Since the per-page mirror (E57), layout, OCR and TEI data for the whole corpus live in
`docs/data/pages/`, so the viewer works on GitHub Pages for every document. The facsimiles
take a second route (E126). `docs/images/` holds the page PNGs locally and is gitignored,
because the full set exceeds what a Git repository and a Pages site should carry. The
published facsimiles live in the separate repository `chpollin/zbz-hersch-images`
(local checkout beside this one under `Documents/GitHub/`), one folder per document id with
`{doc}/{doc}_pNNN.jpg`, served by its own GitHub Pages at
`https://chpollin.github.io/zbz-hersch-images/`. GitHub Pages sends
`Access-Control-Allow-Origin: *`, so OpenSeadragon loads the images cross-origin without
further configuration.

The viewer switches by host. `ZBZ.imageBase` in `docs/assets/js/core.js` is set on
`github.io` hosts and empty everywhere else; `ZBZ.path.image()` and `ZBZ.path.imageFile()`
prepend the base and replace `.png` by `.jpg` when it is set, so a local docroot keeps
reading the PNGs under `docs/images/` unchanged and the page-level `facs_image` sidecar
resolves through the same function.

The JPEGs are produced by `scripts/edition/export_web_images.py` from the local PNGs
(150 dpi, JPEG quality 80, names and numbering identical, idempotent with `--force` to
rewrite). `--out` can point straight at the checkout of the facsimile repository, which
saves a second copy of the set; afterwards commit and push there. The facsimile repository
is a mirror of generated files. A regeneration of the whole set is committed as a fresh
orphan history and force-pushed, because appending would keep every earlier encoding in
the repository and double its size per run.

Before E126 a demo set of five documents (2310, 1000, 1330, 1540, 1620) was committed as
PNG under `docs/images/` so that the online viewer showed at least those facsimiles; the
files and the `.gitignore` exceptions are still tracked and have lost their purpose.

The material is the ZB's digitized holdings; the public delivery of the complete set was an
operator decision on 2026-08-21 and stays subject to the ZB's rights.

### No third-party resources

Every asset the site loads comes from `docs/`. OpenSeadragon 5.0.1 sits in
`docs/assets/vendor/openseadragon/` with its build, its button sprites and its
BSD-3 license text; the three web font families of the design system sit in
`docs/assets/fonts/` as WOFF2 in the latin and latin-ext subsets with their SIL
Open Font License texts, declared in `docs/assets/css/fonts.css`. Every request the
pages issue therefore stays inside the site; the legal notice states that, and the
viewer keeps working in an environment without outbound internet access. A future
runtime dependency is vendored the same way. The token catalog keeps the font stacks,
and `fonts.css` adds the `@font-face` rules alone. The design rationale behind the
token catalog is in [workflow.md](workflow.md), design section.

### Regenerating viewer data

Pages delivers the generated mirror `docs/data/`; the pipeline tree `output/` stays local
and never reaches the server. A deployment therefore shows a change only once the mirror
has been rebuilt and committed:

```bash
python -m scripts.edition.generate_edition_data --mirror-only
```

The full run and the remaining flags are in [CLAUDE.md](../CLAUDE.md), viewer data
section; where this step sits in the curation round trip is in
[workflow.md](workflow.md), round-trip section.

### Security convention

Credentials live exclusively in environment variables, and code, documents and commits
stay free of them. The binding rules, including the prohibition on reading or printing
`.env`, are in [CLAUDE.md](../CLAUDE.md), section Security.

## References

- [tei-mapping.md](tei-mapping.md): the markup rulebook the generator applies
- [workflow.md](workflow.md): data flow, viewer with layout and transcription editor, persistence, round trip, design system
- [project.md](project.md): corpus, delivery tree, entity input data, reference corpus, and the ZBZ, Transkribus and teiCrafter contracts including the fork model
- [specification.md](specification.md): requirements, quality method, validation rule catalog
- [verification.md](verification.md): the verified quality claims, their finding register, the test strategy and the gates that hold the pipeline contracts
- [methodology.md](methodology.md): Promptotyping, verification cascade, work cycle, CER measurement method
- [decisions.md](decisions.md): decision register with E6, E8, E9 and E10 (Mistral, endpoints, Podman, GitLab fork), and the plan section with the open milestones, the configuration file, the container image, the GitLab CI and the merge strategy
- [index.md](index.md): navigation and key concepts
