---
type: knowledge
created: 2026-02-18
updated: 2026-02-25
tags: [zbz-ocr-tei, decisions, offen, entschieden]
status: active
---

# Entscheidungen

Konsolidiertes Register aller Entscheidungen und offenen Fragen im Projekt.

**Abhängigkeiten:** Querschnittlich — sammelt aus allen Dokumenten.

---

## Entschieden

| # | Entscheidung | Begründung | Datum | Dokument |
|---|-------------|------------|-------|----------|
| E1 | Hybrid-Pipeline: Docling (Layout) + LLM-OCR (Text) | Layout-Analyse ohne OCR, OCR separat | 2026-01-29 | [PIPELINE](PIPELINE.md) |
| E2 | Docling nur für Layout, nicht für OCR | RapidOCR hat Encoding-Probleme (e → O) bei frz. Text | 2026-01-29 | [OCR-ENGINES](OCR-ENGINES.md) |
| E3 | Deterministisch first, LLM nur für Komplexes | Reproduzierbar, kostengünstig, debugbar | 2026-01-29 | [PIPELINE](PIPELINE.md) |
| E4 | 4 Dokumenttypen (A-D) klassifiziert | Unterschiedliche Pipeline-Strategien nötig | 2026-01-29 | [QUELLENANALYSE](QUELLENANALYSE.md) |
| E5 | Nachgelagerte GND-Verknüpfung | TEI-Struktur zuerst validieren, NER separat | 2026-01-29 | [GND-STRATEGIE](GND-STRATEGIE.md) |
| E6 | Mistral OCR 3 als Produktions-Engine | ZBZ hat Azure-Zugang, kein GPU nötig | 2026-02-14 | [OCR-ENGINES](OCR-ENGINES.md) |
| E7 | Offerte bleibt unverändert | Azure-Integration kein Mehraufwand | 2026-02-14 | [PROJEKT](PROJEKT.md) |
| E8 | Konfigurierbare API-Endpoints | Wechsel zwischen lokaler und Azure-OCR | 2026-02-14 | [INFRASTRUKTUR](INFRASTRUKTUR.md) |
| E9 | Containerisierung mit Podman | ZBZ nutzt kein Docker, Podman ist OCI-kompatibel | 2026-02-14 | [INFRASTRUKTUR](INFRASTRUKTUR.md) |
| E10 | Fork auf GitLab Uni Zürich | ZBZ betreibt eigene Instanz | 2026-02-14 | [INFRASTRUKTUR](INFRASTRUKTUR.md) |
| E11 | Dreistufiges Ökosystem: zbz-ocr-tei → coOCR → teiCrafter | Batch-OCR → Korrektur → Tiefenerschließung | 2026-02-18 | [PROJEKT](PROJEKT.md) |
| E12 | zbz-ocr-tei nur OCR, keine TEI-Transformation | TEI + GND in coOCR/teiCrafter, nicht hier | 2026-02-19 | [PIPELINE](PIPELINE.md) |
| E13 | Export als PAGE-XML + METS fuer coOCR | coOCR erwartet PAGE-XML (2019-07-15) + PNG, nicht Markdown | 2026-02-20 | [PIPELINE](PIPELINE.md) |
| E14 | Markdown-Formatierung erhalten (R6 geloest) | coOCR speichert Text as-is in `<Unicode>`, Formatierung darf nicht entfernt werden | 2026-02-20 | [PIPELINE](PIPELINE.md) |
| E15 | Dashboard-Redesign: Multi-Page UI mit Shared CSS/JS | Unified Design System, statische JSON-Datenbasis, Engine-Sichtbarkeit, Light Theme | 2026-02-25 | [PIPELINE](PIPELINE.md) |
| E16 | Seitenweiser Vergleich fuer Monografien (>10 TEI-Seiten) | Globales Alignment scheitert bei 140+ Seiten; Content-Matching loest variable PDF/TEI-Offsets | 2026-02-25 | [PIPELINE](PIPELINE.md) |
| E17 | LLM-Korrektur optional, nicht als Default | Verschlechtert Docs mit CER <5% (Phase 2: +0.03, Phase 4: +0.05); Nutzen nur bei CER >10% | 2026-02-25 | [PIPELINE](PIPELINE.md) |
| E18 | Content-basiertes Page-Matching statt fixem Offset | TEI facs-Nummern ≠ PDF-Seitennummern (Deckblaetter, Leerseiten); fixer Offset driftet | 2026-02-25 | [PIPELINE](PIPELINE.md) |
| E19 | Layout-Analyse: Docling + Gemini Hybrid | Docling (mAP 0.699, gratis, 17 Klassen) als Primaer; Gemini 2.5 Flash als optionaler Validator; Kraken als Fallback. Claude Vision disqualifiziert (keine BBox), Mistral unzureichend (keine Text-BBox) | 2026-02-25 | [E19-LAYOUT-ANALYSE](E19-LAYOUT-ANALYSE.md) |
| E20 | Docling 2.75 als Layout-Engine bestaetigt (Phase 0) | Typenstichprobe bestanden: alle 4 Dokumenttypen korrekt erkannt, Spalten-Trennung Type B funktioniert (L: x120-529, R: x560-969), 0.4-3.3s/Seite | 2026-02-25 | [E19-LAYOUT-ANALYSE](E19-LAYOUT-ANALYSE.md) |
| E21 | Scope-Erweiterung: Volle Pipeline in zbz-ocr-tei | Nach Meeting 25.02.: zbz-ocr-tei deckt OCR + Layout + PAGE-XML + NER/GND + TEI-XML ab. E12 (nur OCR) ist damit ueberholt. ZBZ behaelt Transkribus parallel | 2026-02-25 | [PLAN.md](../PLAN.md) |

---

## Offen: Priorität Hoch

Diese Fragen blockieren den Fortschritt.

| # | Frage | Kontext | Blockiert | Klärung durch |
|---|-------|---------|-----------|---------------|
| ~~O1~~ | ~~Azure-API-Key~~ | **Erledigt (18.02.2026)** -- Key vorhanden, Endpoint getestet, Benchmark durchgefuehrt | ~~M1~~ | -- |
| O2 | Alignment-Call Termin? | Terminvorschläge gesendet (18./19./20./24.02.) | Alle offenen Fragen | ZBZ |
| O3 | Fork-Modell und Merge-Strategie? | Upstream-Changes in Fork mergen, CI-basierte Tests | M4 Integration | ZBZ (im Meeting) |
| ~~O4~~ | ~~Schnittstelle zbz-ocr-tei -> coOCR: Welches Format?~~ | **Geloest (20.02.2026)** -- PAGE-XML (2019-07-15) + PNG + METS. Siehe E13 | ~~M4~~ | -- |
| ~~O5~~ | ~~Schnittstelle coOCR → teiCrafter~~ | Entfaellt -- coOCR/teiCrafter nicht mehr im Scope (E21) | -- | -- |

---

## Offen: Priorität Mittel

Wichtig für Qualität, aber nicht blockierend.

| # | Frage | Kontext | Blockiert | Klärung durch |
|---|-------|---------|-----------|---------------|
| O6 | Normalisierung vs. Vorlagentreue | Zurueck im Scope (E21). Klaerung mit Expertin Baehler ausstehend | Phase 3 TEI | ZBZ |
| O7 | Typografie der Ueberschriften | Zurueck im Scope (E21). Dieselbe Frage wie O6 | Phase 3 TEI | ZBZ |
| O8 | Metadaten aus ALMA/MMSID | Zurueck im Scope (E21). MMSIDs fuer teiHeader benoetigt | Phase 3 TEI | ZBZ |
| O9 | div-type-Werte Front/Back-Matter | Zurueck im Scope (E21). editorial, context, translation etc. | Phase 3 TEI | Eigene Entscheidung |
| O10 | Spalten-Problem Typ B: Welcher Loesungsansatz? | A: Docling+Crop, B: Gemini Agentic Vision, C: Prompt-Tuning | M1 Phase 2 | Eigener Test |
| O11 | Entitaeten ohne GND-Eintrag | Zurueck im Scope (E21). Lokale ID oder Freilassen? | Phase 2 NER | Eigene Entscheidung |
| O12 | GND-Verknuepfung im PoC | Zurueck im Scope (E21). Ja -- Seed + lobid.org in Phase 2 | Phase 2 NER | Eigene Entscheidung |
| O18 | Multimodale LLM-Korrektur testen (Scan-Bild + OCR-Text) | Forschung zeigt <1% CER (arXiv:2504.00414); aktuell nur Text | Qualitaet | Eigener Test |
| O19 | Mistral `extract_header/footer` testen | Koennte JSTOR-Artefakte ohne LLM filtern | Qualitaet | Eigener Test |
| O20 | DeepSeek Free OCR (ohne `<\|grounding\|>`) fuer Typ A/C testen | Potenziell schneller ohne Qualitaetsverlust bei einspaltigem Layout | Performance | Eigener Test |

---

## Offen: Priorität Niedrig

Kann später geklärt werden.

| # | Frage | Kontext | Dokument |
|---|-------|---------|----------|
| O13 | Schlagworte: Wer erstellt diese? | Zurueck im Scope (E21). Kommen sie in teiHeader? | [TEI-MAPPING](TEI-MAPPING.md) |
| O14 | GND-Werksaetze in Back-Matter? | Zurueck im Scope (E21) | [TEI-MAPPING](TEI-MAPPING.md) |
| O15 | Systematischer Einsatz von Textual Tags in Transkribus? | div, organization, person, sic, speech, unclear, work | [ZBZ-WORKFLOW](ZBZ-WORKFLOW.md) |
| O16 | Option Editionsansicht: Wird sie gebaut? | Noch nicht entschieden (Mail 14.02.) | [PROJEKT](PROJEKT.md) |
| O17 | GitHub Pages für QS-Viewer aktivieren? | HTML bereit, aber Pages nicht aktiviert | [PROJEKT](PROJEKT.md) |

---

## Risiken

| # | Risiko | Impact | Mitigation | Status |
|---|--------|--------|------------|--------|
| R1 | Spalten-Problem unlösbar | Hoch | Docling trennt Spalten korrekt (E20). Gemini als Fallback | **Geloest** (E20) |
| R2 | TEI zu komplex | Mittel | Zurueck im Scope (E21). Referenz-TEI als Ground Truth, schrittweise Umsetzung | Offen |
| R3 | GND-Halluzinationen | Mittel | Zurueck im Scope (E21). Seed-Dictionary + Confidence-Schwelle | Offen |
| R4 | Azure-API-Kompatibilitaet Mistral OCR 3 | Mittel | Endpoint testen, Fallback auf direkte API | **Geloest** -- Azure AI Foundry Endpoint funktioniert (18.02.) |
| R5 | Fork-Divergenz zwischen DHCraft und ZBZ | Mittel | Merge-Strategie definieren, CI-basierte Tests | Wartet auf Meeting (→ O3) |
| R6 | Post-Processing entfernt Formatierungsinformation | Mittel | Markdown-Markup vor Cleanup erhalten | **Geloest** -- Formatierung erhalten, PAGE-XML/TEI-Transformation konvertiert zu Markup (E14) |

---

## Referenzen

- [PROJEKT](PROJEKT.md) für Meilensteine und Status
- [PIPELINE](PIPELINE.md) für Pipeline-Entscheidungen
- [TEI-MAPPING](TEI-MAPPING.md) für offene TEI-Fragen (O6-O9, O13-O14)
- [JOURNAL](JOURNAL.md) für chronologische Entscheidungshistorie

---

*Erstellt: 2026-02-18 | Aktualisiert: 2026-02-25 (E16-E18: Evaluation + LLM-Erkenntnisse, O18-O20: Recherche-Ergebnisse)*
