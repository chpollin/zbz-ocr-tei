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

---

## Offen: Priorität Hoch

Diese Fragen blockieren den Fortschritt.

| # | Frage | Kontext | Blockiert | Klärung durch |
|---|-------|---------|-----------|---------------|
| ~~O1~~ | ~~Azure-API-Key~~ | **Erledigt (18.02.2026)** -- Key vorhanden, Endpoint getestet, Benchmark durchgefuehrt | ~~M1~~ | -- |
| O2 | Alignment-Call Termin? | Terminvorschläge gesendet (18./19./20./24.02.) | Alle offenen Fragen | ZBZ |
| O3 | Fork-Modell und Merge-Strategie? | Upstream-Changes in Fork mergen, CI-basierte Tests | M4 Integration | ZBZ (im Meeting) |
| ~~O4~~ | ~~Schnittstelle zbz-ocr-tei -> coOCR: Welches Format?~~ | **Geloest (20.02.2026)** -- PAGE-XML (2019-07-15) + PNG + METS. Siehe E13 | ~~M4~~ | -- |
| O5 | Schnittstelle coOCR → teiCrafter: `<ab>` vs. `<p>`? | coOCR exportiert `<ab>`, teiCrafter erwartet `<p>` / `<div>` | M4 Integration | Eigene Entscheidung |

---

## Offen: Priorität Mittel

Wichtig für Qualität, aber nicht blockierend.

| # | Frage | Kontext | Blockiert | Klärung durch |
|---|-------|---------|-----------|---------------|
| ~~O6~~ | ~~Normalisierung vs. Vorlagentreue~~ | Verschoben nach coOCR/teiCrafter (E12) | ~~TEI~~ | -- |
| ~~O7~~ | ~~Typografie der Ueberschriften~~ | Verschoben nach coOCR/teiCrafter (E12) | ~~TEI~~ | -- |
| ~~O8~~ | ~~Metadaten aus ALMA/MMSID~~ | Verschoben nach coOCR/teiCrafter (E12) | ~~TEI~~ | -- |
| ~~O9~~ | ~~div-type-Werte Front/Back-Matter~~ | Verschoben nach coOCR/teiCrafter (E12) | ~~TEI~~ | -- |
| O10 | Spalten-Problem Typ B: Welcher Loesungsansatz? | A: Docling+Crop, B: Gemini Agentic Vision, C: Prompt-Tuning | M1 Phase 2 | Eigener Test |
| ~~O11~~ | ~~Entitaeten ohne GND-Eintrag~~ | Verschoben nach teiCrafter (E12) | ~~GND~~ | -- |
| ~~O12~~ | ~~GND-Verknuepfung im PoC~~ | Verschoben nach teiCrafter (E12) | ~~GND~~ | -- |

---

## Offen: Priorität Niedrig

Kann später geklärt werden.

| # | Frage | Kontext | Dokument |
|---|-------|---------|----------|
| ~~O13~~ | ~~Schlagworte~~ | Verschoben nach teiCrafter (E12) | -- |
| ~~O14~~ | ~~GND-Werksaetze in Back-Matter~~ | Verschoben nach teiCrafter (E12) | -- |
| O15 | Systematischer Einsatz von Textual Tags in Transkribus? | div, organization, person, sic, speech, unclear, work | [ZBZ-WORKFLOW](ZBZ-WORKFLOW.md) |
| O16 | Option Editionsansicht: Wird sie gebaut? | Noch nicht entschieden (Mail 14.02.) | [PROJEKT](PROJEKT.md) |
| O17 | GitHub Pages für QS-Viewer aktivieren? | HTML bereit, aber Pages nicht aktiviert | [PROJEKT](PROJEKT.md) |

---

## Risiken

| # | Risiko | Impact | Mitigation | Status |
|---|--------|--------|------------|--------|
| R1 | Spalten-Problem unlösbar | Hoch | Cloud-VM für Docling, Gemini Agentic Vision, notfalls manuell | Offen (→ O10) |
| ~~R2~~ | ~~TEI zu komplex~~ | -- | Verschoben nach teiCrafter (E12) | -- |
| ~~R3~~ | ~~GND-Halluzinationen~~ | -- | Verschoben nach teiCrafter (E12) | -- |
| R4 | Azure-API-Kompatibilitaet Mistral OCR 3 | Mittel | Endpoint testen, Fallback auf direkte API | **Geloest** -- Azure AI Foundry Endpoint funktioniert (18.02.) |
| R5 | Fork-Divergenz zwischen DHCraft und ZBZ | Mittel | Merge-Strategie definieren, CI-basierte Tests | Wartet auf Meeting (→ O3) |
| R6 | Post-Processing entfernt Formatierungsinformation | Mittel | Markdown-Markup vor Cleanup erhalten fuer coOCR | **Geloest** -- Formatierung erhalten, coOCR speichert as-is (E14, 20.02.) |

---

## Referenzen

- [PROJEKT](PROJEKT.md) für Meilensteine und Status
- [PIPELINE](PIPELINE.md) für Pipeline-Entscheidungen
- [TEI-MAPPING](TEI-MAPPING.md) für offene TEI-Fragen (O6-O9, O13-O14)
- [JOURNAL](JOURNAL.md) für chronologische Entscheidungshistorie

---

*Erstellt: 2026-02-18 | Aktualisiert: 2026-02-25 (E15: Dashboard-Redesign)*
