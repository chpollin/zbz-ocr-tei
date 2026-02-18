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

| # | Meilenstein | Aufwand | Erfolgskriterium | Status |
|---|-------------|---------|-------------------|--------|
| M0 | Bildextraktion + QS-Viewer | Erledigt | Bilder + Viewer verfügbar | Erledigt |
| M1 | OCR validiert | 5-7 Tage | ≥95% Genauigkeit alle Typen | Phase 1 erledigt (94.4%), Phase 2-4 ausstehend |
| M2 | TEI-Transformation | 6-9 Tage | ≥90% Struktur-Korrektheit | Prototyp, rudimentär |
| M3 | GND-Verknüpfung | 5-6 Tage | ≥85% Precision | Seed extrahiert, Pipeline fehlt |
| M4 | Integration | 4-6 Tage | End-to-End ohne Eingriff | Ausstehend |
| M5 | Pilotbetrieb | 6-10 Tage | Kundenabnahme | Ausstehend |

**Gesamt:** 26-38 Tage (konservativ: 38-50 mit Puffer)

### Abhängigkeiten

```
M0 (Bilder) ──► M1 (OCR) ──► M2 (TEI) ──► M3 (GND) ──► M4 (Integration) ──► M5 (Pilot)
                  │                                         ▲
                  └── Spalten-Problem blockiert Phase 2-4   │
                                                            │
                  Schnittstellen zu coOCR/teiCrafter ───────┘
```

---

## Komponentenstatus (18.02.2026)

| Komponente | Status | Details |
|------------|--------|---------|
| Bildextraktion | Erledigt | `scripts/extract_pages.py`, 383 Seiten |
| QS-Viewer | Erledigt | `docs/` mit HTML-Viewer |
| OCR Phase 1 (Typ A) | Erledigt | 94.4% Genauigkeit, siehe [TESTPLAN](TESTPLAN.md) |
| OCR Phase 2-4 | Ausstehend | GPU + Spalten-Lösung erforderlich |
| Post-Processing | Erledigt | 4-stufig in `scripts/postprocess/` |
| TEI-Templates | Erledigt | 5 Templates in `templates/` |
| TEI-Transformation | Prototyp | `scripts/transform_to_tei.py`, rudimentär |
| GND-Seed | Erledigt | 75 Entitäten, `scripts/extract_gnd.py` |
| GND-Pipeline | Ausstehend | API-Anbindung + NER fehlen |
| Evaluation | Erledigt | `scripts/evaluate_ocr.py`, CER/WER + HTML-Report |
| Azure-Integration | Ausstehend | API-Key kommt von ZBZ |
| Containerisierung | Ausstehend | Dockerfile für Podman |
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
| LLM-API (289 Docs) | 6-15 USD |
| GPU-Cloud (optional) | ~10-20 USD |

---

## Referenzen

- [ARCHITEKTUR](ARCHITEKTUR.md) für technische Pipeline-Details
- [QUELLENANALYSE](QUELLENANALYSE.md) für Korpus und Dokumenttypen
- [DECISIONS](DECISIONS.md) für offene Fragen und Entscheidungen
- [INFRASTRUKTUR](INFRASTRUKTUR.md) für Deployment-Details

---

*Erstellt: 2026-02-18 | Aktualisiert: 2026-02-18*
