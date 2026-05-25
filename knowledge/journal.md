---
type: journal
created: 2026-01-29
updated: 2026-05-25
tags: [zbz-ocr-tei, journal]
status: active
---

# Arbeitsjournal

Kompakter chronologischer Ueberblick aller Arbeitssitzungen. Eine Zeile pro Sitzung,
Details und Entscheidungen in [decisions.md](decisions.md). Code-Aenderungen im Git-Log.

---

## Mai 2026 — Viewer-Datenversorgung + Deploy-Vorbereitung + Edition-Uplift

| # | Datum | Thema |
|---|---|---|
| 45 | 2026-05-25 | Edition-Uplift-Welle gestartet (Plan: `~/.claude/plans/edition-uplift-three-pages.md`). Vier Etappen ueber alle drei Frontend-Seiten (index, viewer, about) + Quer-Politur, ~25 h. Architektur-Entscheidungen: E58 OpenSeadragon 5.0.1 als Faksimile-Renderer (Pan/Zoom, View-Modus), E59 Polygone explizit ausgeschlossen (Druck-Korpus, Rechtecke reichen), E60 Mode-Button-Redesign Option C (Edit-Toggle pro Panel statt globaler Mode-Leiste — loest Wort-Redundanz Transkription↔OCR), E61 Export-Modul mit JSZip 3.10.1 (Per-Doc-Drawer "Alles ↓" + Multi-Select-Bulk-Export aus Korpus-Uebersicht). Code: Schritt 1 OSD-Integration umgesetzt (`viewer.html` CDN-Script, `viewer.css` `.panel__body--canvas`+`.facsimile-osd`, `viewer.js` Renderer zweigeteilt `renderFacsimileOsd()`/`renderFacsimileImg()`, `setMode()` re-rendert bei Variant-Wechsel). Layout-Mode behaelt vorerst Eigenbau-Editor + img. Visual-Test offen. Plan-Erweiterungen on-the-fly: Smart-Filter mit kreuzkonditionalen Live-Counts (1.3), klickbare Spalten-Header (1.4b), Per-Doc-Export-Drawer (2.9), Bulk-Export aus index (1.6). Politur aus Session 44 + Visual-Test-Politur + Befund 1 weiterhin uncommitted (User-Entscheidung). |
| 44 | 2026-05-25 | Befund-Fixes + Konsistenz-Refactoring. Fixes: Frontend-Screening-Zaehler `WITH_NOTES`→`APPROVED_WITH_NOTES` (catalog.js/index.html); TEI-Doppelkodierung `&amp;amp;` behoben (tei_step1.py `html.unescape` + Bestandsdaten 26 Docs). Refactoring: Knowledge-Drift nach E56/E57 bereinigt (viewer.md auf reale 3-Seiten-App, CLAUDE.md cer.html-Verweis entfernt, `data/tei_curated/` angelegt, E56-curation_server-Widerspruch, shared.js→core.js, edition→viewer-Knoten); tote CSS-Tokens entfernt; `.btn--ghost`-Dopplung auf `#filter-reset` gescoped; Orphans geloescht (`scripts/postprocess/`, `generate_dashboard_data.py` + `dashboard.json`). Befund 3 geschlossen: 6 Finals (revisionDesc-Escaping -- Writer `tei_add_revision.py` + Bestand) und 309 Per-Seiten-Fragmente (`<pb>`-Splitter balancierte `<div>` nicht -> `_balance_divs` in `generate_edition_data.py` + Bestand). Alle 4970 served XML strikt wohlgeformt (vorher 327 nicht). |
| 43 | 2026-05-25 | Viewer auf vollen Korpus erweitert: `scripts/generate_edition_data.py` mit `mirror_per_page_data()` (alle 285 Docs → `docs/data/pages/`, 8083 Layout + 4117 OCR + 4115 TEI-Seiten extrahiert via `<pb>`-Splitting, sequentielle Pagination 1..N statt n-Attribut). `core.js`-Resolver mit dreistufigem Fallback (`pages/` → `examples/` → `../output/`). `docs/.nojekyll` fuer GitHub Pages. Deployment-Section in `viewer.md`. Smoke-Test via HTTP-Probes (5 Docs ueber Typen A-D) erfolgreich. Bildlieferung bleibt lokal-only (4 GB). E57. |

---

## April 2026 — Frontend-Radikalkur + Wissenschaftliche CER-Re-Evaluation

| # | Datum | Thema |
|---|---|---|
| 42 | 2026-04-27 | Knowledge-Konsolidierung (25→10 Docs, alle filenames lowercase) + Frontend-Radikalreduktion: Edition + Diagnostik + CER-Dashboard + Curation Editor ersatzlos abgeschafft. Neue Single-Page-App `docs/viewer.html` mit Faksimile + OCR/TEI-Panel + Layout- und Transkriptions-Editor. Persistenz via Datei-Download (kein FastAPI mehr). Volumen-Reduktion: 9→1 HTML, 23→6 JS (−81%), 5.023→806 Z. CSS (−84%). E56. |
| 41 | 2026-04-27 | CER wissenschaftlich fundiert: BCa-Bootstrap-CIs (B=10000, Seed=42), Paired-Test E2E vs OCR-only (−14.83 pp, p<0.001), HCPR ~99%, Selektionsbias n_chars p=0.041 ehrlich geflaggt. Multi-Claude-Koordination ueber CLAUDES-WORKING-SESSION.md. Pagewise-vs-Global-Mess-Artefakt diagnostiziert und in [quality.md](quality.md) dokumentiert. Interaktives Dashboard `docs/infrastruktur/cer.html` mit 12 Sektionen. E54/E55. |

---

## Maerz 2026 — Pipeline-Konsolidierung + Edition

| # | Datum | Thema |
|---|---|---|
| 40 | 2026-03-27 | Frontend-Refactoring Phase 1+2: CSS-Token-Konsolidierung, HTML-Semantik (Skip-Nav, ARIA), JS-Foundation-Layer (`zbz-core.js`), Unified TEI Renderer. |
| 39 | 2026-03-26 | OCR-Diagnostik Abschluss: 6 Scope-Mismatches identifiziert; bereinigte Statistik n=19 Mean 4.18% / Median 1.83%. |
| 38 | 2026-03-26 | Diagnostik-UI Rewrite: 4 Tabs, ZBZ.Diagnostik-Namespace, Search-Index 279→285 (XML-Parsing-Fix). |
| 37 | 2026-03-26 | Diagnostik-Datenproduktion: W10-Tiefenanalyse, Corpus-Statistik (285 Docs / 4.108 Seiten), Validierungs-Timeline. |
| 36 | 2026-03-26 | Edition-Sync Fortsetzung: Log-Tab, Seitenzaehlung 383→4.117. |
| 35 | 2026-03-26 | Edition-Synchronisation: Katalog 15→285 Docs, Wikidata-Resume-Flag, revisionDesc im Reader. |
| 34 | 2026-03-26 | TEI-Qualitaet: ref-Pattern in `zbz_hersch.rng` erweitert (GND + #zbz), 285/285 schema-valide. Heuristische lb-Injection (10.635 lb in 46 Docs), Post-Assembly-Fixes W3/W4/W7. |
| 33 | 2026-03-26 | OCR-Diagnostik + Eval-Optimierung: Symmetrische Normalisierung, Hyphen, CI-Alignment. Mean CER 9.33%→5.97%, Median 5.52%→2.42%. |
| 32 | 2026-03-26 | End-to-End CER Benchmark (E51): TEI-vs-TEI Eval, `benchmark_cer.py`, Median 5.5%. Sub-Projekt CER-Verbesserung definiert. |
| 31 | 2026-03-26 | Neues Schema `zbz_hersch.rng` + verbindliche Editionsrichtlinien ZBZ eingearbeitet (18 Dateien). E48/E49/E50 (Dual-Attribut). |
| 30 | 2026-03-15 | Hersch Design-System: Migration auf Anthrazit+Ziegelrot+EB Garamond+Jost. Zweistufige CSS-Tokens (`--h-*` / `--ed-*`). Hersch-Komponenten (Seuil, Etonnement, Polyphonie). |
| 29 | 2026-03-15 | NEEDS_REVIEW 32→0: 20 neue Entity-Stopwoerter (E45), Strukturfixes, OCR-Dedup `ocr_dedup.py` (E46). Finalstand 242 APPROVED / 43 WITH_NOTES / 0 NEEDS_REVIEW. |
| 28 | 2026-03-15 | Edition Frontend Refactoring: Discovery Hub, Volltextsuche, Galerie, Screening + Curation Workflow getrennt, 5 Curation-States. |
| 27 | 2026-03-15 | Agent-Based Quality Screening Rollout 285/285 (58 Batches, 4 Tiers): 210 APPROVED, 43 WITH_NOTES, 32 NEEDS_REVIEW. revisionDesc-Standard etabliert (E42), `output/tei_final/` als Single Source of Truth (E43). |
| 26 | 2026-03-15 | TEI Validation Quality Gate refactored: 2-Ebenen (Errors/Warnings), W1-W11, HTML-Report. Entity-Tagging typkorrekt mit internen IDs. div-Merge. `--reassemble` Flag. 284/285 VALID. |
| 25 | 2026-03-14 | Frontend-Konsolidierung: Edition nach `docs/`, Pipeline-UI nach `docs/infrastruktur/`. ES5→ES6+ in 13 JS-Dateien. |
| 24 | 2026-03-12 | Viewer-Erweiterung: WD/zbz-ID Support, GND-0%-Bug behoben (`entity_index.py` schrieb GND nie ins TEI-XML — Fix + Cache-Backfill, 0%→21.7%). |
| 23 | 2026-03-09 | NER Completion + TEI Entity Injection: 285 Docs, 11.685 Entities, 26.197 Mentions. Wikidata-Linking gestartet. |
| 22 | 2026-03-09 | Knowledge-Refactoring: EDITION + CURATION getrennt. NER Production Run 285 Docs, 4.100 Index-Eintraege. |
| 19-21 | 2026-03-08–09 | Curation Editor Phasen 2-5: Block-Toolbar, Entity-Kuration mit Autocomplete, Review-Workflow (3 Status), TEI-Validierung. `data/tei_curated/` als git-tracked Gold-Standard. |
| 17-18 | 2026-03-08 | tei_unified Refactoring (Orchestrator ~1100→~70 Z.). NER-Robustheit (Diakritik, Retry, Surname-Matching). NER Production Phase 1 (7 Qualitaetsverbesserungen, E35). |
| 14-16 | 2026-03-06–07 | Unified TEI Pipeline (E32): 4 Stufen (Scaffold + Gemini + Assembly + Validation). NER Pipeline (E34): Gemini Flash Lite, 6 Entity-Typen, Wikidata-Reconciliation. |
| 12-13 | 2026-03-06 | Gemini Vision TEI (E30, superseded). Dokumenttyp-spezifische Prompts (4-Ebenen). Layout-QA Full Run E31 (14.708 Korrekturen). |
| 11 | 2026-03-05 | Gemini-Dokumentklassifikation (E27, Stage 1a). Online-Demo (E28). Gemini OCR-Korrektur Stage 2b (E29). |
| 9-10 | 2026-03-03–04 | docling-serve API (E24), Gemini Layout QA + Detect (E25/E26): 3 Modi (qa/detect/auto). |

---

## Februar 2026 — Pipeline-Aufbau

| # | Datum | Thema |
|---|---|---|
| 7-8 | 2026-02-25–27 | Scope-Expansion (E21): Full Pipeline (OCR + Layout + PAGE-XML + NER/GND + TEI). Pilot 15 Docs, page-by-page Comparison (E16/E18). Data Delivery E23 (286 PDFs, 25 TEI-XMLs). |
| 4-6 | 2026-02-14–20 | Mistral OCR 3 als Production Engine (E6). Azure-Integration. PAGE-XML + METS Export (E13, Schema 2013-07-15). Dashboard-Redesign (E15). |
| 1-3 | 2026-01-29–02-14 | Initiale Quellenanalyse: 286 PDFs, 4 Dokumenttypen (A-D), Sprachverteilung FR 66% / DE 30%. Hybrid Pipeline-Entscheidung (E1): Docling Layout + LLM-OCR Text. |

Aeltere Detail-Eintraege im Git-Verlauf erhalten.

---

## Wiederkehrende Muster

Aus den Sessions destillierte Beobachtungen, die fuer kuenftige Arbeit relevant bleiben:

- **L1** Validierung muss actionable sein. False-Positive-Quote >50% macht Reports nutzlos. Jede Warning braucht eine konkrete Aktion.
- **L2** Entity-Typ darf nicht verloren gehen. `annotate_entities()` braucht `(tag, id)` aus dem Index, nicht nur Namen.
- **L3** Stopwort-Filter ist essenziell. Gattungsbegriffe (Mensch, Gott, Wahl) erzeugen ohne Filter ~30% False Positives.
- **L4** Seiten-Fragmente zu Dokument-Struktur mergen. ZBZ-Referenz hat 1 top-level div. Post-Assembly-Merge ist deterministisch und kostenlos.
- **L5** Step-2-Cache invalidieren bei Prompt-Aenderungen. `--force` regeneriert nicht den Step-2-Cache.
- **L6** LLM-NER hat ~5-10% False Positives. Inhaerent. Loesung: Curation Editor, nicht Code-Fix.
- **L7** Page-Numbering-Drift macht Pagewise-CER unbrauchbar. Content-aligned Eval (`evaluate_tei_vs_tei`) ist immun.
- **L8** Mehrsprachige Codes korrekt parsen. "fra/deu" zerfaellt sonst zu "und". Betrifft ~40 Docs.
- **L9** facsimile/pb synchron halten. Leere surfaces fuer Seiten ohne Layout-Zones.
- **L10** Interne IDs (zbz-p/o/l/w.N) als primaere Referenz. GND in `ref`, intern in `corresp` (Dual-Attribut, E50).
- **P7** Gattungsbegriffe im Entity-Index erzeugen False Positives in ~30% der Docs.
- **P8** Zeitungslayouts versagen systematisch (>40 Zones, OCR-Halluzinationen). ~3% des Korpus.
- **P10** Tier-2-Docs (4-8 Seiten) haben 85%+ APPROVED-Rate, Tier-1 (1-3 Seiten) nur 40%.
