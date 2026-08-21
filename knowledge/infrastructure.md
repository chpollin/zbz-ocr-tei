---
title: Infrastructure
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
created: 2026-02-18
updated: 2026-08-21
authors: [Christopher Pollin]
related: [pipeline, workflow, testing, integration, plan, design]
---

# Infrastructure

Deployment, API access, continuous integration and the static delivery of the viewer.

## Overview

| Aspect | Details |
|---|---|
| Model APIs | Google Gemini (resolved default OCR engine, layout QA, TEI refinement), Anthropic (optional post-correction), Azure AI Foundry (Mistral Document AI, reproducibility path) |
| Credentials | environment variables, loaded from an uncommitted `.env` at the repository root |
| Versioning | GitHub for development, GitLab University of Zurich for the production fork |
| Continuous integration | GitHub Actions on the development repository |
| Delivery | static GitHub Pages site served from `docs/`, no backend |
| Pipeline execution | local clone or the production fork; no hosted runtime |

The production fork, its container image and its own CI are planned rather than built; the
items and their conditions are in [plan.md](plan.md), phase E, and the counterpart
relationship is in [integration.md](integration.md).

## Model APIs and credentials

### Engine roles

`ocr_pipeline --engine auto` is the documented default and resolves to Gemini, so Gemini is
the effective production OCR engine. The Mistral Document AI path on Azure stays selectable
under `--engine mistral` as the reproducibility record of the delivered corpus, which was
produced with it; the deployed endpoint answers 401 today, so a rerun through that path
needs a new deployment first. Every engine writes its result into the base text layer
directory `output/mistral_results/`, whose name is historical and independent of the engine
that produced the text. Which source a downstream stage prefers is decided by the loader
priority described in [pipeline.md](pipeline.md).

| API | Access | Use |
|---|---|---|
| Gemini 3.1 Flash Lite | Google API | OCR, layout QA and detection, document classification, TEI refinement |
| Claude Haiku | Anthropic API | optional LLM post-correction (E17) |
| Mistral Document AI 2512 | Azure AI Foundry, serverless | reproducibility path for the delivered base text layer |
| Docling Serve | self-hosted or local | layout analysis |
| Transkribus REST | ZBZ account | PAGE-XML upload (E81) |

### Environment variables

Credentials live in a `.env` file at the repository root. The file is never committed, never
read and never printed, and no example file is tracked, so the following list is the
reference for the variable names. `scripts.config` is the single loader; other modules read
the values from there.

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
Central US, North Central US and Sweden Central. The call is `POST {endpoint}/v1/ocr` with a
bearer token, the PDF travels base64-encoded in the `document.document_url` field, and the
response returns `pages[]` with `index`, `markdown`, `images[]` and `dimensions`. A request
carries at most 30 pages and 30 MB, which `MistralOCR._split_pdf()` handles by splitting.
Bounding-box and document annotations are available for at most eight pages per request.

Failure modes seen during setup, kept because they cost time to rediscover.

- A 404 after deployment means the endpoint URL lacks `/v1/ocr`; the host must be
  `*.models.ai.azure.com` and never `*.services.ai.azure.com`.
- A 413 means the PDF is too large and needs compression or splitting.
- Base64 errors come from line breaks inside the encoded string.
- The catalog entry appears under "Mistral Document AI" rather than "Mistral OCR"
  (`mistral-document-ai-2505` and `-2512`).

Engine configuration currently lives in `scripts/config.py` and
`scripts/ocr/ocr_pipeline.py`. Moving it into one configuration file is a planned item in
[plan.md](plan.md), phase E.

## CI/CD

`.github/workflows/tests.yml` runs two gates on every push and pull request under Python
3.11, `ruff check scripts tests` and the full pytest suite. Which part of the suite survives
a fresh checkout, and which markers select it, is owned by [testing.md](testing.md).

`pyproject.toml` is the only manifest. The repository declares no build backend, because it
is a dependency set and a script pipeline rather than an installable package, so the workflow
materializes the dependency list from `[project] dependencies` plus the `dev` extra and
installs it with pip. The `dev` extra pins ruff to one version, which the local
`.pre-commit-config.yaml` hook reuses, so hook and CI report the same findings. The heavy
layout engines are the separate optional extra `layout` and stay uninstalled in CI.

### Production fork

The production repository is a fork on the GitLab instance of the University of Zurich; the
fork relationship, its merge direction and its adjustments are described in
[integration.md](integration.md). The container image, the GitLab CI configuration and the
merge strategy for upstream changes are planned and specified in [plan.md](plan.md), phase E.

## Local Development

Setup, dependency installation and the `.env` keys are in the README, section "Getting
started". What the README does not carry is the optional local layout stack. Docling runs
locally only with CUDA 12.4 or newer and a GPU with at least 8 GB VRAM; without it, layout
analysis goes through a Docling Serve instance named by `DOCLING_SERVE_URL`. The hardware
check is one command.

```bash
python -m scripts.ocr.ocr_pipeline --check-gpu
```

Python 3.11 or newer is required, matching the CI environment.

## Viewer Deployment

The viewer (`docs/`) is a purely static site; no backend is needed.

### Local server

```bash
python -m http.server 8000 -d docs           # docroot docs/ (mirror data only)
python -m http.server 8000                   # repo root: enables ../output/ fallback (Gemini A/B, LLM engines)
```

In the second case the viewer is reachable under
`http://localhost:8000/docs/viewer.html` and can read all OCR engines in the
`output/` tree. The File System Access write path works under `localhost`
and HTTPS; writes always go to the local clone, never to a server.

### GitHub Pages

In the repo settings under Settings > Pages: Source "Deploy from a branch",
branch `main`, folder `/docs`. The `.nojekyll` file in the directory
prevents Pages from interpreting the content as a Jekyll site.

Constraint: `docs/images/` is gitignored (the facsimile PNGs are too large
for Git) except for the committed demo documents listed below. On GitHub
Pages every other document shows OCR/layout/TEI text but no facsimile. Full
online inspection needs an external image host (IIIF server, S3, CDN) and a
configurable `ZBZ.path.image()` with a base-URL variable.

### Online demo (E28)

The full pipeline output under `output/` is gitignored and available locally only. For the
online demo the facsimiles of a few representative documents are committed under
`docs/images/`, and the same ids form the `featured` set in `docs/data/catalog.json`. They
were chosen to cover the layout classes, both main languages and the length range.

| Doc | Type | Language | Pages | Note |
|---|---|---|---|---|
| 2310 | A | FR | 3 | journal article, JSTOR cover |
| 1000 | B | FR | 4 | two-column |
| 1330 | D | DE/FR | 6 | bilingual anthology |
| 1540 | C | DE | 8 | German monograph |
| 1620 | B | DE | 5 | two-column brochure |

Since the per-page mirror (E57), layout, OCR and TEI data for the whole corpus live in
`docs/data/pages/`, so the viewer works on GitHub Pages for every document and only the
facsimile images stay local outside this demo set.

### No third-party resources

Every asset the site loads comes from `docs/`. OpenSeadragon 5.0.1 sits in
`docs/assets/vendor/openseadragon/` with its build, its button sprites and its
BSD-3 license text; the three web font families of the design system sit in
`docs/assets/fonts/` as WOFF2 in the latin and latin-ext subsets with their SIL
Open Font License texts, declared in `docs/assets/css/fonts.css`. The pages
therefore issue no request to a CDN or a font host, the legal notice states that
plainly, and the viewer keeps working in an environment without outbound
internet access. A future runtime dependency is vendored the same way rather
than linked; the token catalog keeps the font stacks, `fonts.css` only adds the
`@font-face` rules. The design rationale behind the token catalog is in
[design.md](design.md).

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

## Security convention

Credentials live in environment variables only, never in code, documents or commits. The
binding rules, including the prohibition on reading or printing `.env`, are in
[CLAUDE.md](../CLAUDE.md), section Security.

## References

- [pipeline.md](pipeline.md): stages, engines and the loader priority of the text layer
- [workflow.md](workflow.md): data flow, viewer and round trip
- [testing.md](testing.md): the suite the CI gates run and its clone-safe subset
- [integration.md](integration.md): ZBZ, Transkribus and teiCrafter, including the fork model
- [plan.md](plan.md): configuration file, container image, GitLab CI, merge strategy
- [design.md](design.md): the design system behind the delivered pages
- [decisions.md](decisions.md): E6, E8, E9, E10 (Mistral, endpoints, Podman, GitLab fork)
