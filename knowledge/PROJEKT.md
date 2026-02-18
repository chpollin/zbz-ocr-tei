---
type: knowledge
created: 2026-02-18
updated: 2026-02-18
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

## Ökosystem — Drei Tools, eine Pipeline

Das Projekt besteht aus drei eigenständigen Tools, die zusammen eine End-to-End-Pipeline bilden:

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  zbz-ocr-tei    │     │   coOCR/HTR     │     │   teiCrafter    │
│  Batch-OCR      │ ──► │  Korrektur      │ ──► │  Tiefenerschl.  │
│  (Python)       │     │  (Browser-App)  │     │  (Browser-App)  │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

### Stufe 1: zbz-ocr-tei (dieses Repo)

**Zweck:** Massenverarbeitung — 289 PDFs automatisiert transkribieren.

| Aspekt | Details |
|--------|---------|
| Input | PDF-Scans (7.200 Seiten) |
| Output | Seitenweise Markdown + PNG-Bilder |
| Engines | Mistral OCR 3 (Azure), DeepSeek-OCR-2 (lokal), Gemini 3 Flash (API) |
| Modus | Batch, ohne manuellen Eingriff |
| Repo | `DHCraft/zbz-ocr-tei` |

### Stufe 2: coOCR/HTR (Korrektur)

**Zweck:** Qualitätssicherung — Experte korrigiert OCR-Fehler am Bild.

| Aspekt | Details |
|--------|---------|
| Input | Bilder + OCR-Text (aus Stufe 1) |
| Workflow | Bild links, Text rechts, LLM-Validierung, Experte korrigiert |
| Output | Basis-TEI (`<ab>`, `<lb/>`, `<unclear>`, `<gap>`) |
| Modus | Einzeldokument, Expert-in-the-Loop |
| Repo | `DHCraft/co-ocr-htr` |

### Stufe 3: teiCrafter (Tiefenerschließung)

**Zweck:** Veredelung — Entitäten, Struktur, GND-Verknüpfung.

| Aspekt | Details |
|--------|---------|
| Input | Basis-TEI (aus Stufe 2) oder Plaintext |
| Workflow | LLM annotiert → Experte reviewt (Accept/Edit/Reject) → Validierung |
| Output | Produktions-TEI (DTA-konform, `<persName>`, `<orgName>`, `<bibl>`, GND-Refs) |
| Modus | Einzeldokument, 3-Schichten-Prompt, 5-Level-Validierung |
| Repo | `DHCraft/teiCrafter` |

### Schnittstellen

| Von → Nach | Format | Status |
|------------|--------|--------|
| zbz-ocr-tei → coOCR | Bilder (PNG) + Markdown oder PAGE-XML | Zu definieren |
| coOCR → teiCrafter | Basis-TEI (`.tei.xml`) | Grundsätzlich möglich, Mapping `<ab>` → `<p>` klären |
| teiCrafter → Produktion | Produktions-TEI → oXygen, ediarum, GAMS | Funktional |

Offene Schnittstellenfragen: Siehe [DECISIONS](DECISIONS.md).

---

## Meilensteine

**Scope dieses Repos:** PDF -> korrigiertes Markdown. TEI-Transformation und GND-Verknuepfung finden in coOCR/HTR und teiCrafter statt.

| # | Meilenstein | Aufwand | Erfolgskriterium | Status |
|---|-------------|---------|-------------------|--------|
| M0 | Bildextraktion + QS-Viewer | Erledigt | Bilder + Viewer verfuegbar | Erledigt |
| M1 | OCR validiert | 5-7 Tage | >=95% Genauigkeit alle Typen | Phase 1-3: 94.14% (Mistral) + LLM 94.45% |
| M2 | Produktions-OCR alle 289 Docs | 3-5 Tage | Alle PDFs verarbeitet, QS geprueft | Ausstehend |
| M3 | Integration mit coOCR/HTR | 4-6 Tage | Export-Format definiert, Schnittstelle funktional | Ausstehend |
| M4 | Pilotbetrieb | 6-10 Tage | Kundenabnahme | Ausstehend |

### Abhaengigkeiten

```
M0 (Bilder) ──► M1 (OCR validiert) ──► M2 (Produktion) ──► M3 (coOCR-Integration) ──► M4 (Pilot)
                  │                                              ▲
                  └── Phase 1-3: 94.14% + LLM 94.45%             │
                                                                 │
                  coOCR/HTR + teiCrafter ────────────────────────┘
```

---

## Komponentenstatus (18.02.2026, spaet)

| Komponente | Status | Details |
|------------|--------|---------|
| Bildextraktion | Erledigt | `scripts/extract_pages.py`, 383 Seiten |
| QS-Viewer | Erledigt | `docs/` mit HTML-Viewer |
| OCR Phase 1 (Typ A) | Erledigt | Mistral 90.60%, DeepSeek 94.4% |
| OCR Phase 2 (Typ B) | Erledigt | Mistral 93.69% Genauigkeit |
| OCR Phase 3 (Typ D) | Erledigt | Mistral 97.12% Genauigkeit |
| OCR Phase 4 (Typ C) | Teilweise | OCR fertig, CER-Evaluation eingeschraenkt |
| Post-Processing | Erledigt | 4-stufig in `scripts/postprocess/` |
| GND-Seed | Erledigt | 75 Entitaeten, `scripts/extract_gnd.py` |
| LLM-Nachkorrektur | Erledigt | `scripts/llm_postprocess.py`, Haiku 4.5, Variante C |
| Evaluation | Erledigt | `scripts/evaluate_ocr.py`, CER/WER + HTML-Report |
| Azure-Integration | Erledigt | Mistral Document AI 2512, `.env` konfiguriert |
| Benchmark-UI | Erledigt | `docs/benchmark.html`, Mistral vs DeepSeek |
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
| LLM-Korrektur (Haiku 4.5, 289 Docs) | ~48 USD |
| GPU-Cloud (optional) | ~10-20 USD |

---

## Referenzen

- [ARCHITEKTUR](ARCHITEKTUR.md) für technische Pipeline-Details
- [QUELLENANALYSE](QUELLENANALYSE.md) für Korpus und Dokumenttypen
- [DECISIONS](DECISIONS.md) für offene Fragen und Entscheidungen
- [INFRASTRUKTUR](INFRASTRUKTUR.md) für Deployment-Details

---

*Erstellt: 2026-02-18 | Aktualisiert: 2026-02-19*
