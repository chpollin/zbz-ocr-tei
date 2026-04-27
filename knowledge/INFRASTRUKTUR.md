---
type: knowledge
created: 2026-02-18
updated: 2026-02-27
tags: [zbz-ocr-tei, infrastruktur, azure, podman, cicd]
status: active
---

# Infrastructure

Deployment, API access, containerization, and CI/CD for ZBZ production operations.

**Dependencies:** [PIPELINE](PIPELINE.md)

---

## Overview

| Aspect | Details |
|--------|---------|
| API Access | Azure (Mistral Document AI 2512, key available), Claude and Gemini pending approval |
| Version Control | GitLab University of Zurich |
| Container Runtime | Podman (no Docker, but OCI-compatible) |
| Deployment | Fork of development repo on ZBZ infrastructure |
| Registry | GitLab Container Registry (University of Zurich) |

---

## Azure Integration

### Mistral Document AI

| Aspect | Details |
|--------|---------|
| Provider | Azure AI Foundry (Serverless API) |
| Model | `mistral-document-ai-2512` |
| Endpoint Format | `https://<deployment>.<region>.models.ai.azure.com/v1/ocr` |
| Regions | East US, East US 2, West US, West US 3, South Central US, North Central US, Sweden Central |
| Usage | Primary production engine for ZBZ |
| Status | API key available, engine implemented |
| Advantage | No GPU required, server-based, scalable, 30 pages/request |

### Additional APIs (planned)

| API | Access | Usage | Status |
|-----|--------|-------|--------|
| Gemini 3 Flash | Google API | Type B/D (Agentic Vision), NER | Pending approval |
| Claude | Anthropic / Azure | Complex structure recognition, QA | Pending approval |

### Configuration (to be implemented)

The pipeline must support configurable API endpoints:

```yaml
# Example config.yaml (not yet implemented)
ocr:
  default_engine: mistral
  engines:
    mistral:
      provider: azure-foundry
      endpoint_env: MISTRAL_DOC_AI_ENDPOINT
      model: mistral-document-ai-2512
      api_key_env: MISTRAL_DOC_AI_KEY
    deepseek:
      provider: local
      model: deepseek-ai/DeepSeek-OCR-2
    gemini:
      provider: google
      model: gemini-3.0-flash
      api_key_env: GEMINI_API_KEY
```

**Note:** Currently engines are configured directly in `scripts/config.py` and `scripts/ocr_pipeline.py`. A YAML-based configuration is planned but not yet implemented.

---

## Containerization (Podman)

### Requirements

- OCI-compatible image (Podman = daemonless Docker alternative)
- Multi-stage build: Base (Python + dependencies) + optional GPU
- Configuration via environment variables (API keys, endpoints)
- No secrets in the image

### Containerfile (to be created)

```dockerfile
# Not yet implemented — draft
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY scripts/ scripts/

ENV MISTRAL_DOC_AI_ENDPOINT=""
ENV MISTRAL_DOC_AI_KEY=""
ENV GEMINI_API_KEY=""

ENTRYPOINT ["python", "-m", "scripts.ocr_pipeline"]
```

**Status:** Not yet implemented.

---

## CI/CD (GitLab)

### Requirements

- GitLab CI on University of Zurich instance
- Container build + push to GitLab Registry
- Automatic tests on push
- Merge strategy: upstream changes from development repo into fork

### Fork Model

| Aspect | Details |
|--------|---------|
| Development Repo | GitHub: DHCraft/zbz-ocr-tei |
| Production Repo | GitLab University of Zurich (fork) |
| Merge Direction | GitHub -> GitLab (upstream updates) |
| Fork Customizations | API keys, endpoints, ZBZ-specific config |

Details on merge strategy: To be defined.

**Status:** .gitlab-ci.yml not yet implemented.

---

## Local Development

### Prerequisites

| Tool | Version | Purpose |
|------|---------|---------|
| Python | 3.11+ | Pipeline scripts |
| CUDA | 12.4+ | DeepSeek-OCR-2 (optional, local only) |
| GPU | 8+ GB VRAM | DeepSeek-OCR-2 (optional, local only) |
| Git | 2.x | Version control |

### Setup

```bash
# Virtual Environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# Dependencies
pip install -r requirements.txt

# GPU-Check (optional)
python scripts/ocr_pipeline.py --check-gpu
```

---

## Dashboard Deployment

The QA dashboard (`docs/`) is a purely static web application and does not require a backend server.

| Method | Description |
|--------|-------------|
| Live Server (VS Code) | Local preview during development |
| GitHub Pages | `docs/` as source, automatically deployed |
| Any HTTP Server | `python -m http.server` in the `docs/` directory |

**Update data:** `python -m scripts.generate_dashboard_data` generates `docs/data/dashboard.json` from pipeline outputs.

---

## References

- [PIPELINE](PIPELINE.md) for pipeline architecture
- [ENGINES](ENGINES.md) for engine details
- [DECISIONS](DECISIONS.md) for open questions

## Siehe auch

- [ZBZ-WORKFLOW](ZBZ-WORKFLOW.md) — Bestehender redaktioneller Workflow der ZBZ

---

*Created: 2026-02-18 | Updated: 2026-02-27*
