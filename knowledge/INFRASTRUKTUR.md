---
type: knowledge
created: 2026-02-18
updated: 2026-02-25
tags: [zbz-ocr-tei, infrastruktur, azure, podman, cicd]
status: active
---

# Infrastruktur

Deployment, API-Zugang, Containerisierung und CI/CD für den ZBZ-Produktionsbetrieb.

**Abhängigkeiten:** [ARCHITEKTUR](ARCHITEKTUR.md)

---

## Übersicht

| Aspekt | Details |
|--------|---------|
| API-Zugang | Azure (Mistral Document AI 2512, Key vorhanden), Claude und Gemini in Genehmigung |
| Versionskontrolle | GitLab Universität Zürich |
| Container-Runtime | Podman (kein Docker, aber OCI-kompatibel) |
| Deployment | Fork des Entwicklungsrepos auf ZBZ-Infrastruktur |
| Registry | GitLab Container Registry (Uni Zürich) |

---

## Azure-Integration

### Mistral Document AI

| Aspekt | Details |
|--------|---------|
| Provider | Azure AI Foundry (Serverless API) |
| Modell | `mistral-document-ai-2512` |
| Endpoint-Format | `https://<deployment>.<region>.models.ai.azure.com/v1/ocr` |
| Regionen | East US, East US 2, West US, West US 3, South Central US, North Central US, Sweden Central |
| Einsatz | Primaere Produktions-Engine fuer ZBZ |
| Status | API-Key vorhanden, Engine implementiert |
| Vorteil | Kein GPU noetig, serverbasiert, skalierbar, 30 Seiten/Request |

### Weitere APIs (geplant)

| API | Zugang | Einsatz | Status |
|-----|--------|---------|--------|
| Gemini 3 Flash | Google API | Typ B/D (Agentic Vision), NER | In Genehmigung |
| Claude | Anthropic / Azure | Komplexe Strukturerkennung, QS | In Genehmigung |

### Konfiguration (zu implementieren)

Die Pipeline muss konfigurierbare API-Endpoints unterstützen:

```yaml
# Beispiel config.yaml (noch nicht implementiert)
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

**Status:** Noch nicht implementiert. Aktuell sind Engines hardcoded in `scripts/ocr_pipeline.py`.

---

## Containerisierung (Podman)

### Anforderungen

- OCI-kompatibles Image (Podman = daemonless Docker-Alternative)
- Multi-Stage Build: Base (Python + Dependencies) + Optional GPU
- Konfiguration über Umgebungsvariablen (API-Keys, Endpoints)
- Keine Secrets im Image

### Containerfile (zu erstellen)

```dockerfile
# Noch nicht implementiert — Entwurf
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

**Status:** Noch nicht implementiert.

---

## CI/CD (GitLab)

### Anforderungen

- GitLab CI auf Uni Zürich Instanz
- Container-Build + Push in GitLab Registry
- Automatische Tests bei Push
- Merge-Strategie: Upstream-Changes aus Entwicklungsrepo in Fork

### Fork-Modell

| Aspekt | Details |
|--------|---------|
| Entwicklungsrepo | GitHub: DHCraft/zbz-ocr-tei |
| Produktionsrepo | GitLab Uni Zürich (Fork) |
| Merge-Richtung | GitHub -> GitLab (Upstream-Updates) |
| Anpassungen im Fork | API-Keys, Endpoints, ZBZ-spezifische Config |

Details zur Merge-Strategie: Wird im Alignment-Call definiert (-> [DECISIONS](DECISIONS.md) O3).

**Status:** .gitlab-ci.yml noch nicht implementiert.

---

## Lokale Entwicklung

### Voraussetzungen

| Tool | Version | Zweck |
|------|---------|-------|
| Python | 3.11+ | Pipeline-Skripte |
| CUDA | 12.4+ | DeepSeek-OCR-2 (optional, nur lokal) |
| GPU | 8+ GB VRAM | DeepSeek-OCR-2 (optional, nur lokal) |
| Git | 2.x | Versionskontrolle |

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

## Dashboard-Deployment

Das QA-Dashboard (`docs/`) ist eine rein statische Webanwendung und benoetigt keinen Backend-Server.

| Methode | Beschreibung |
|---------|-------------|
| Live Server (VS Code) | Lokale Vorschau waehrend Entwicklung |
| GitHub Pages | `docs/` als Source, automatisch deployed |
| Beliebiger HTTP-Server | `python -m http.server` im `docs/`-Ordner |

**Daten aktualisieren:** `python -m scripts.generate_dashboard_data` generiert `docs/data/dashboard.json` aus Pipeline-Outputs.

---

## Referenzen

- [ARCHITEKTUR](ARCHITEKTUR.md) für Pipeline-Architektur
- [OCR-ENGINES](OCR-ENGINES.md) für Engine-Details
- [DECISIONS](DECISIONS.md) O1 (Azure-Key), O3 (Fork-Modell)

---

*Erstellt: 2026-02-18 | Aktualisiert: 2026-02-25*
