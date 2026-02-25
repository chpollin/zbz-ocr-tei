---
type: knowledge
created: 2026-02-18
updated: 2026-02-25
tags: [zbz-ocr-tei, projekt, oekosystem, vision]
status: active
---

# Projekt: ZBZ-OCR-TEI Pipeline

LLM-gestützte OCR- und TEI-Transformationspipeline für 289 Jeanne-Hersch-Texte (7.200 Seiten) der Zentralbibliothek Zürich.

**Abhängigkeiten:** Keine (Wurzeldokument)

---

## Auftrag

| Aspekt | Details |
|--------|---------|
| Auftraggeber | Zentralbibliothek Zürich (ZBZ) |
| Auftragnehmer | DHCraft |
| Gegenstand | Automatisierte OCR + TEI-Auszeichnung für Jeanne Hersch Nachlass |
| Status | Beidseitig bestätigt (14.02.2026) |
| Offerte | Unverändert (Azure/Mistral kein Mehraufwand) |
| Ansprechpartner ZBZ | Elias Kreyenbühl, Anouschka (Editions- und Informatik-Background) |

---

## Oekosystem

Seit dem Alignment-Meeting (25.02.2026) deckt zbz-ocr-tei die **gesamte Pipeline** ab: OCR + Layout + PAGE-XML + NER/GND + TEI-XML. ZBZ behaelt parallel ihren Transkribus-Workflow. coOCR und teiCrafter bleiben als optionale Downstream-Tools bestehen.

```
┌───────────────────────────────────────────────────────┐
│  zbz-ocr-tei (dieses Repo)                           │
│  PDF → Bilder → OCR → Layout → PAGE-XML → NER → TEI │
│  (Python, Batch, vollautomatisch)                     │
└──────────────────────┬────────────────────────────────┘
                       │ PAGE-XML + PNG (optional)
                       ▼
              ┌─────────────────┐     ┌─────────────────┐
              │   coOCR/HTR     │ ──► │   teiCrafter    │
              │  Korrektur      │     │  Tiefenerschl.  │
              │  (Browser-App)  │     │  (Browser-App)  │
              └─────────────────┘     └─────────────────┘
```

### zbz-ocr-tei (dieses Repo)

**Zweck:** Vollautomatische End-to-End-Pipeline -- 289 PDFs zu TEI-XML.

| Aspekt | Details |
|--------|---------|
| Input | PDF-Scans (7.200 Seiten) |
| Output | TEI-XML (DTA-Basisformat), PAGE-XML + PNG + METS |
| OCR-Engines | Mistral OCR 3 (Azure), DeepSeek-OCR-2 (lokal) |
| Layout-Engine | Docling 2.75 (RT-DETR V2 Heron, E19) |
| NER | Claude Haiku 4.5 + lobid.org GND-API |
| Modus | Batch, ohne manuellen Eingriff |
| Repo | `DHCraft/zbz-ocr-tei` |
| Implementierungsplan | [PLAN.md](../PLAN.md) |

### coOCR/HTR (optional, Downstream)

**Zweck:** Manuelle Korrektur einzelner Dokumente am Bild.

| Aspekt | Details |
|--------|---------|
| Input | PAGE-XML + PNG (aus zbz-ocr-tei) |
| Output | Korrigierte PAGE-XML / Basis-TEI |
| Repo | `DHCraft/co-ocr-htr` |

### teiCrafter (optional, Downstream)

**Zweck:** Veredelung -- Entitaeten reviewen, Struktur verfeinern.

| Aspekt | Details |
|--------|---------|
| Input | Basis-TEI (aus coOCR) oder TEI-XML (aus zbz-ocr-tei) |
| Output | Produktions-TEI (DTA-konform, GND-Refs) |
| Repo | `DHCraft/teiCrafter` |

---

## Meilensteine

**Scope:** Volle Pipeline PDF → TEI-XML (seit 25.02.2026). Implementierungsplan: [PLAN.md](../PLAN.md).

| # | Meilenstein | Erfolgskriterium | Status |
|---|-------------|-------------------|--------|
| M0 | Bildextraktion + QS-Viewer | Bilder + Viewer verfuegbar | Erledigt |
| M1 | OCR validiert | >=95% Genauigkeit alle Typen | Erledigt: 93.58% (Mistral), Dashboard-UI |
| M2 | Layout + PAGE-XML | Regionen + BBox + PAGE-XML fuer 15 Pilots | **Phase 1** |
| M3 | NER + GND | Entity Recall >70%, GND-Linking >60% | **Phase 2** |
| M4 | TEI-XML | DTA-konformes TEI fuer 15 Pilots, Schema-valide | **Phase 3** |
| M5 | Produktionslauf | 289 Docs verarbeitet, Stichproben-QA bestanden | Phase 5 |

### Abhaengigkeiten

```
M0 (Bilder) ──► M1 (OCR) ──► M2 (Layout+PAGE-XML) ──► M3 (NER+GND) ──► M4 (TEI) ──► M5 (Produktion)
```

---

## Komponentenstatus (25.02.2026)

| Komponente | Status | Details |
|------------|--------|---------|
| Bildextraktion | Erledigt | `scripts/extract_pages.py`, 383 Seiten |
| QS-Viewer | Erledigt | `docs/` mit HTML-Viewer |
| OCR Phase 1 (Typ A) | Erledigt | Mistral 90.60%, DeepSeek 94.4% |
| OCR Phase 2 (Typ B) | Erledigt | Mistral 93.69% Genauigkeit |
| OCR Phase 3 (Typ D) | Erledigt | Mistral 97.12% Genauigkeit |
| OCR Phase 4 (Typ C) | Erledigt | CER 2.65% (seitenweiser Vergleich, beste Phase) |
| Post-Processing | Erledigt | 4-stufig in `scripts/postprocess/` |
| GND-Seed | Erledigt | 75 Entitaeten, `scripts/extract_gnd.py` |
| LLM-Nachkorrektur | Erledigt | `scripts/llm_postprocess.py`, Haiku 4.5, Variante C |
| Evaluation | Erledigt | `scripts/evaluate_ocr.py`, CER/WER + HTML-Report |
| Azure-Integration | Erledigt | Mistral Document AI 2512, `.env` konfiguriert |
| Benchmark-UI | Erledigt | `docs/benchmark.html`, Mistral vs DeepSeek |
| Dashboard-Redesign | Erledigt | `docs/` mit shared.css/js, index.html, viewer.html |
| Dashboard-Daten | Erledigt | `scripts/generate_dashboard_data.py` → dashboard.json |
| Containerisierung | Ausstehend | Dockerfile fuer Podman |
| CI/CD | Ausstehend | GitLab Uni Zürich |

---

## Team

| Person | Rolle | Organisation |
|--------|-------|-------------|
| Christopher | Projektleitung, Entwicklung | DHCraft |
| Elias Kreyenbühl | Auftraggeber, Koordination | ZBZ |
| Anouschka | Edition, Informatik | ZBZ |
| Bibliotheksinformatik | CI/CD, Podman, Infrastruktur | ZBZ |

---

## Kosten

| Posten | Betrag |
|--------|--------|
| Mistral OCR (Azure, 289 Docs) | 6-15 USD |
| LLM-Korrektur (Haiku 4.5, 289 Docs) | ~35 USD |
| GPU-Cloud (optional) | ~10-20 USD |

---

## Referenzen

- [PIPELINE](PIPELINE.md) für technische Pipeline-Details
- [QUELLENANALYSE](QUELLENANALYSE.md) für Korpus und Dokumenttypen
- [DECISIONS](DECISIONS.md) für offene Fragen und Entscheidungen
- [INFRASTRUKTUR](INFRASTRUKTUR.md) für Deployment-Details

---

*Erstellt: 2026-02-18 | Aktualisiert: 2026-02-25*
