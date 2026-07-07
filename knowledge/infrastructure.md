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
updated: 2026-07-07
tags: [zbz-ocr-tei, infrastructure, azure, podman, cicd]
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
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

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

`.github/workflows/tests.yml` (since 2026-06-10) runs the full pytest suite on every push/PR
(Python 3.11, `pip install -r requirements.txt`). Data-dependent tests (`output/`,
`data/source/`) skip themselves on the fresh checkout; this covers the schema compilation,
the statistics library, helpers, and script health.

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

pip install -r requirements.txt

# GPU check (optional)
python scripts/ocr/ocr_pipeline.py --check-gpu
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
for Git) except for the four DEMO docs (1000, 1330, 1540, 2310). On GitHub
Pages every other document shows OCR/layout/TEI text but no facsimile. Full
online inspection needs an external image host (IIIF server, S3, CDN) and a
configurable `ZBZ.path.image()` with a base-URL variable.

### Regenerating viewer data

When pipeline output or workflow status (manifest) changes:

```bash
python -m scripts.edition.generate_edition_data                  # full run incl. per-page mirror
python -m scripts.edition.generate_edition_data --mirror-only    # rebuild pages/ only
python -m scripts.edition.generate_edition_data --no-mirror      # catalog + indices only
```

The per-page mirror (`docs/data/pages/`) is large (many thousands of small
files); regenerate it after every change to `output/tei_final/`.

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
