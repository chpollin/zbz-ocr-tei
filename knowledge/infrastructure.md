---
title: Infrastructure
type: knowledge
project:
  name: zbz-ocr-tei
  repository: https://github.com/chpollin/zbz-ocr-tei.git
method:
  name: Promptotyping
  url: https://dhcraft.org/Promptotyping/
status: complete
created: 2026-02-18
updated: 2026-08-21
tags: [zbz-ocr-tei, infrastructure, azure, podman, cicd]
template:
  name: Vorlage Architecture
  version: 0.3
  url: https://dhcraft.org/Promptotyping/promptotyping-document/architecture
authors: [Christopher Pollin]
---

# Infrastructure

Deployment, API access, containerization, and CI/CD for ZBZ production operation.

---

## Overview

| Aspect | Details |
|---|---|
| API access | Azure (Mistral Document AI 2512, key available), Anthropic + Google API |
| Versioning | GitHub (development) + GitLab University of Zurich (production, fork) |
| Containers | Podman (no Docker, OCI-compatible) |
| Deployment | fork of the development repo on ZBZ infrastructure |
| Registry | GitLab container registry, University of Zurich |

---

## Azure Integration

### Mistral Document AI

| Aspect | Details |
|---|---|
| Provider | Azure AI Foundry (serverless API, pay-as-you-go) |
| Model | `mistral-document-ai-2512` |
| Endpoint format | `https://<deployment>.<region>.models.ai.azure.com/v1/ocr` |
| Regions | East US, East US 2, West US, West US 3, South Central US, North Central US, Sweden Central |
| Role | primary production engine for ZBZ |
| Status | API key available, engine implemented |
| Advantage | no GPU, server-based, scalable, 30 pages/request |

Setup:

- Deploy in Azure AI Foundry: Model Catalog > `mistral-document-ai-2512` > Serverless Endpoint
- `.env`: `MISTRAL_DOC_AI_ENDPOINT`, `MISTRAL_DOC_AI_KEY` (see `.env.example`)

API:

- `POST {endpoint}/v1/ocr` with bearer token
- Input: base64 PDF in the `document.document_url` field
- Response: `pages[]` with `index`, `markdown`, `images[]`, `dimensions`
- Limits: 30 pages/request, 30 MB max (the pipeline splits automatically via `MistralOCR._split_pdf()`)
- Annotations: `bbox_annotation` + `document_annotation` (max 8 pages)

Typical errors:

- 404 after deployment: append `/v1/ocr` to the endpoint URL. The endpoint must be `*.models.ai.azure.com` (NOT `*.services.ai.azure.com`)
- 413 / file too large: compress or split the PDF
- Base64 errors: no line breaks in the base64 string
- "Mistral OCR" not in the catalog: renamed to "Mistral Document AI" (`mistral-document-ai-2505` / `-2512`)

### Other APIs

| API | Access | Use | Status |
|---|---|---|---|
| Gemini 3.1 Flash Lite | Google API | layout QA/detect, classification, OCR correction, TEI refinement | active |
| Claude Haiku 4.5 | Anthropic | LLM post-correction (optional, E17) | active |

### Configuration (planned)

A YAML-based configuration is planned; currently the engines are configured directly in
`scripts/config.py` and `scripts/ocr/ocr_pipeline.py`.

```yaml
# example config.yaml (planned)
ocr:
  default_engine: mistral
  engines:
    mistral:
      provider: azure-foundry
      endpoint_env: MISTRAL_DOC_AI_ENDPOINT
      model: mistral-document-ai-2512
      api_key_env: MISTRAL_DOC_AI_KEY
    gemini:
      provider: google
      model: gemini-3.1-flash-lite-preview
      api_key_env: GEMINI_API_KEY
```

---

## Containerization (Podman)

### Requirements

- OCI-compatible image (Podman = daemonless Docker alternative)
- multi-stage build: base (Python + dependencies) plus optional GPU
- configuration via environment variables (API keys, endpoints)
- no secrets in the image

### Containerfile (draft, not yet implemented)

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY pyproject.toml .
RUN python -c "import tomllib; print(chr(10).join(tomllib.load(open('pyproject.toml','rb'))['project']['dependencies']))" > requirements.txt     && pip install --no-cache-dir -r requirements.txt

COPY scripts/ scripts/

ENV MISTRAL_DOC_AI_ENDPOINT=""
ENV MISTRAL_DOC_AI_KEY=""
ENV GEMINI_API_KEY=""

ENTRYPOINT ["python", "-m", "scripts.ocr.ocr_pipeline"]
```

Not yet implemented.

---

## CI/CD

### Active: GitHub Actions (development repo)

`.github/workflows/tests.yml` (since 2026-06-10) runs two gates on every push/PR under
Python 3.11: `ruff check scripts tests` and the full pytest suite. Data-dependent tests
(`output/`, `data/source/`) skip themselves on the fresh checkout; this covers the schema
compilation, the statistics library, helpers, and script health.

`pyproject.toml` is the only manifest since 2026-08-21; `requirements.txt` is gone. The repo
declares no build backend, because it is a dependency set and script pipeline rather than an
installable package, so the workflow materializes the dependency list from
`[project] dependencies` plus the `dev` extra and installs it with pip. The `dev` extra pins
ruff to one version, which the local `.pre-commit-config.yaml` hook reuses, so hook and CI
report the same findings. The heavy layout engines (torch, Docling) are the separate
optional extra `layout` and are not installed in CI.

### Planned: GitLab CI (University of Zurich, E10)

- GitLab CI on the University of Zurich instance
- container build plus push to the GitLab registry
- automatic tests on push
- merge strategy: upstream changes from the development repo into the fork

### Fork model

| Aspect | Details |
|---|---|
| Development repo | GitHub: `chpollin/zbz-ocr-tei` |
| Production repo | GitLab University of Zurich (fork) |
| Merge direction | GitHub -> GitLab (upstream updates) |
| Fork adjustments | API keys, endpoints, ZBZ-specific config |

Details of the merge strategy are still to be defined.

`.gitlab-ci.yml` is not yet implemented.

---

## Local Development

### Prerequisites

| Tool | Version | Purpose |
|---|---|---|
| Python | 3.11+ | pipeline scripts |
| CUDA | 12.4+ | Docling (local layout analysis, optional) |
| GPU | 8+ GB VRAM | Docling (local layout analysis, optional) |
| Git | 2.x | version control |

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

uv sync --extra dev   # pip fallback: see README, Getting started

# GPU check (optional)
python -m scripts.ocr.ocr_pipeline --check-gpu
```

---

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
for Git) except for the committed demo documents, which
[pipeline.md](pipeline.md) lists in its online demo section. On GitHub
Pages every other document shows OCR/layout/TEI text but no facsimile. Full
online inspection needs an external image host (IIIF server, S3, CDN) and a
configurable `ZBZ.path.image()` with a base-URL variable.

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
`@font-face` rules.

### Regenerating viewer data

Pages delivers the generated mirror `docs/data/`; the pipeline tree `output/` stays local
and never reaches the server. A deployment therefore shows a change only once the mirror
has been rebuilt and committed:

```bash
python -m scripts.edition.generate_edition_data --mirror-only
```

The full run and the remaining flags are in [CLAUDE.md](../CLAUDE.md), viewer data
section; where this step sits in the curation round trip is in
[workflow.md](workflow.md), section 4.3.

---

## Security Convention

- the `.env` file is NEVER read or printed (it contains API keys)
- no secrets in code or docs
- API keys, tokens, and passwords exclusively in environment variables
- see the top-level [CLAUDE.md](../CLAUDE.md) §Security

---

## References

- [pipeline.md §Engines](pipeline.md): engine details and setup notes
- [project.md §ZBZ Workflow](project.md): manual workflow plus integration points
- [decisions.md](decisions.md): E6, E8, E9, E10 (Mistral, endpoints, Podman, GitLab fork)
