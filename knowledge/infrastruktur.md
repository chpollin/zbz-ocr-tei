---
type: knowledge
created: 2026-02-18
updated: 2026-05-25
tags: [zbz-ocr-tei, infrastruktur, azure, podman, cicd]
status: active
---

# Infrastruktur

Deployment, API-Zugang, Containerisierung, CI/CD fuer den ZBZ-Production-Betrieb.

---

## Uebersicht

| Aspekt | Details |
|---|---|
| API-Zugang | Azure (Mistral Document AI 2512, Key verfuegbar), Anthropic + Google API |
| Versionierung | GitHub (Development) + GitLab Uni Zuerich (Production, Fork) |
| Container | Podman (kein Docker, OCI-kompatibel) |
| Deployment | Fork des Development-Repo auf ZBZ-Infrastruktur |
| Registry | GitLab Container Registry Uni Zuerich |

---

## Azure-Integration

### Mistral Document AI

| Aspekt | Details |
|---|---|
| Provider | Azure AI Foundry (Serverless API, Pay-as-you-go) |
| Modell | `mistral-document-ai-2512` |
| Endpoint-Format | `https://<deployment>.<region>.models.ai.azure.com/v1/ocr` |
| Regionen | East US, East US 2, West US, West US 3, South Central US, North Central US, Sweden Central |
| Rolle | Primary Production Engine fuer ZBZ |
| Status | API-Key verfuegbar, Engine implementiert |
| Vorteil | keine GPU, server-basiert, skalierbar, 30 Seiten/Request |

**Setup:**

- Deploy in Azure AI Foundry: Model Catalog > `mistral-document-ai-2512` > Serverless Endpoint
- `.env`: `MISTRAL_DOC_AI_ENDPOINT`, `MISTRAL_DOC_AI_KEY` (siehe `.env.example`)

**API:**

- `POST {endpoint}/v1/ocr` mit Bearer-Token
- Input: Base64-PDF im `document.document_url`-Feld
- Response: `pages[]` mit `index`, `markdown`, `images[]`, `dimensions`
- Limits: 30 Seiten/Request, 30 MB max (Pipeline splittet automatisch ueber `MistralOCR._split_pdf()`)
- Annotations: `bbox_annotation` + `document_annotation` (max 8 Seiten)

**Typische Fehler:**

- **404 nach Deployment:** `/v1/ocr` an Endpoint-URL anhaengen. Endpoint muss `*.models.ai.azure.com` sein (NICHT `*.services.ai.azure.com`)
- **413 / file too large:** PDF komprimieren oder splitten
- **Base64-Fehler:** keine Zeilenumbrueche im Base64-String
- **"Mistral OCR" nicht im Katalog:** umbenannt zu "Mistral Document AI" (`mistral-document-ai-2505` / `-2512`)

### Weitere APIs

| API | Zugang | Verwendung | Status |
|---|---|---|---|
| Gemini 3.1 Flash Lite | Google API | Layout-QA/Detect, Klassifikation, OCR-Korrektur, TEI-Refinement | aktiv |
| Claude Haiku 4.5 | Anthropic | LLM-Postkorrektur (optional, E17) | aktiv |

### Konfiguration (in Planung)

Eine YAML-basierte Konfiguration ist geplant, aktuell sind Engines direkt in `scripts/config.py`
und `scripts/ocr/ocr_pipeline.py` konfiguriert.

```yaml
# Beispiel config.yaml (geplant)
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

## Containerisierung (Podman)

### Anforderungen

- OCI-kompatibles Image (Podman = daemonless Docker-Alternative)
- Multi-Stage Build: Base (Python + Dependencies) + optional GPU
- Konfiguration via Environment Variables (API-Keys, Endpoints)
- keine Secrets im Image

### Containerfile (Entwurf, noch nicht implementiert)

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

**Status:** noch nicht implementiert.

---

## CI/CD (GitLab)

### Anforderungen

- GitLab CI auf der Uni-Zuerich-Instanz
- Container Build + Push zur GitLab Registry
- automatische Tests bei Push
- Merge-Strategie: Upstream-Aenderungen vom Development-Repo in den Fork

### Fork-Modell

| Aspekt | Details |
|---|---|
| Development-Repo | GitHub: `chpollin/zbz-ocr-tei` |
| Production-Repo | GitLab Uni Zuerich (Fork) |
| Merge-Richtung | GitHub → GitLab (Upstream-Updates) |
| Fork-Anpassungen | API-Keys, Endpoints, ZBZ-spezifische Config |

Details zur Merge-Strategie: noch zu definieren.

**Status:** `.gitlab-ci.yml` noch nicht implementiert.

---

## Lokale Entwicklung

### Voraussetzungen

| Tool | Version | Zweck |
|---|---|---|
| Python | 3.11+ | Pipeline-Skripte |
| CUDA | 12.4+ | Docling (lokale Layout-Analyse, optional) |
| GPU | 8+ GB VRAM | Docling (lokale Layout-Analyse, optional) |
| Git | 2.x | Versionierung |

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

pip install -r requirements.txt

# GPU-Check (optional)
python scripts/ocr/ocr_pipeline.py --check-gpu
```

---

## Dashboard-Deployment

Das QA-Dashboard (`docs/`) ist eine rein statische Web-App, kein Backend noetig.

| Methode | Beschreibung |
|---|---|
| Live Server (VS Code) | lokale Vorschau waehrend Development |
| GitHub Pages | `docs/` als Source, automatisches Deployment |
| beliebiger HTTP-Server | `python -m http.server` im `docs/`-Verzeichnis |

**Daten aktualisieren:** `python -m scripts.edition.generate_edition_data` erzeugt Katalog
und den Per-Seiten-Mirror in `docs/data/` aus Pipeline-Outputs.

---

## Sicherheits-Konvention

- `.env`-Datei wird NIE gelesen oder ausgegeben (enthaelt API-Keys)
- keine Secrets in Code oder Doku
- API-Keys, Tokens, Passwoerter ausschliesslich in Environment-Variablen
- siehe Top-Level [CLAUDE.md](../CLAUDE.md) §Security

---

## Verweise

- [pipeline.md §Engines](pipeline.md) — Engine-Details und Setup-Hinweise
- [projekt.md §ZBZ-Workflow](projekt.md) — manueller Workflow + Integrationspunkte
- [decisions.md](decisions.md) — E6, E8, E9, E10 (Mistral, Endpoints, Podman, GitLab Fork)
