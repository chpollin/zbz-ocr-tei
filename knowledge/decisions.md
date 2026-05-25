---
type: knowledge
created: 2026-02-18
updated: 2026-05-25
tags: [zbz-ocr-tei, decisions, open, decided]
status: active
---

# Decisions

Konsolidiertes Register aller Entscheidungen und offenen Fragen. Cross-cutting, sammelt aus allen Dokumenten.

---

## Entschieden (E1-E61)

| # | Entscheidung | Begruendung | Datum | Dokument |
|---|---|---|---|---|
| E1 | Hybrid Pipeline: Docling (Layout) + LLM-OCR (Text) | Layout-Analyse ohne OCR, OCR separat | 2026-01-29 | [pipeline.md](pipeline.md) |
| E2 | Docling nur fuer Layout, nicht fuer OCR | RapidOCR hat Encoding-Probleme (`e → O`) bei FR | 2026-01-29 | [pipeline.md](pipeline.md) |
| E3 | Deterministisch zuerst, LLM nur fuer komplexe Faelle | reproduzierbar, kosteneffizient, debuggbar | 2026-01-29 | [pipeline.md](pipeline.md) |
| E4 | 4 Dokumenttypen (A-D) klassifiziert | unterschiedliche Pipeline-Strategien | 2026-01-29 | [projekt.md](projekt.md) |
| E6 | Mistral OCR 3 als Production Engine | ZBZ hat Azure-Zugang, keine GPU noetig | 2026-02-14 | [pipeline.md](pipeline.md) |
| E7 | Honorar unveraendert | Azure-Integration ohne Mehrkosten | 2026-02-14 | [projekt.md](projekt.md) |
| E8 | konfigurierbare API-Endpoints | Wechsel zwischen lokal und Azure | 2026-02-14 | [infrastruktur.md](infrastruktur.md) |
| E9 | Containerisierung mit Podman | ZBZ nutzt kein Docker, Podman OCI-kompatibel | 2026-02-14 | [infrastruktur.md](infrastruktur.md) |
| E10 | Fork auf GitLab Uni Zuerich | ZBZ betreibt eigene Instanz | 2026-02-14 | [infrastruktur.md](infrastruktur.md) |
| E13 | Export als PAGE-XML + METS fuer coOCR | coOCR erwartet PAGE-XML 2013-07-15 + PNG | 2026-02-20 | [pipeline.md](pipeline.md) |
| E14 | Markdown-Formatierung bewahren | coOCR speichert Text as-is in `<Unicode>` | 2026-02-20 | [pipeline.md](pipeline.md) |
| E15 | Dashboard-Redesign: Multi-Page UI mit shared CSS/JS | Unified Design System, statische JSON-Daten | 2026-02-25 | [pipeline.md](pipeline.md) |
| E16 | Page-by-page Comparison fuer Monografien (>10 TEI-Seiten) | Global Alignment scheitert ab ~50 Seiten | 2026-02-25 | [pipeline.md](pipeline.md) |
| E17 | LLM-Korrektur optional, nicht default | verschlechtert Docs mit CER <5% | 2026-02-25 | [pipeline.md](pipeline.md) |
| E18 | Content-based Page Matching statt fester Offset | TEI-facs-Nummern ≠ PDF-Seiten | 2026-02-25 | [pipeline.md](pipeline.md) |
| E19 | Layout: Docling + Gemini hybrid | Docling mAP 0.699, 17 Klassen, free; Gemini als Validator | 2026-02-25 | [pipeline.md](pipeline.md) |
| E20 | Docling 2.75 als Layout-Engine bestaetigt | Type-Sample bestanden, 0.4-3.3s/Seite | 2026-02-25 | [pipeline.md](pipeline.md) |
| E21 | Scope-Expansion: volle Pipeline in zbz-ocr-tei | Meeting 25.02.: OCR + Layout + PAGE-XML + NER + TEI | 2026-02-25 | [pipeline.md](pipeline.md) |
| E22 | TEI-Generator direkt aus Layout+OCR (ohne PAGE-XML) | spaeter erweitert bei NER/PAGE-XML | 2026-02-25 | [pipeline.md](pipeline.md) |
| E23 | Datenlieferung Feb 2026: 286 PDFs + 25 TEI-XMLs + 24 PAGE-XML-Exports | PAGE-XML Schema 2013-07-15, leer | 2026-02-27 | [projekt.md](projekt.md) |
| E24 | docling-serve API fuer Layout (keine lokale GPU) | Docker Container, identisches Output-Format | 2026-03-03 | [pipeline.md](pipeline.md) |
| E25 | Gemini 3.1 Flash Lite als Layout-QA-Validator | Overlay-PNG + Layout-JSON → korrigiertes JSON, Structured Output | 2026-03-03 | [pipeline.md](pipeline.md) |
| E26 | Gemini Layout-Detect-Modus | Docling scheitert auf ~15% (landscape, multi-column), 3 Modi qa/detect/auto | 2026-03-04 | [pipeline.md](pipeline.md) |
| E27 | Gemini-Dokumentklassifikation (Stage 1a) | 271/286 ohne Metadaten, Heuristiken versagen (7/15 falsch) | 2026-03-05 | [pipeline.md](pipeline.md) |
| E28 | Online-Demo: 4 DEMO-Docs auf GitHub Pages | volle Daten nur lokal (gitignored) | 2026-03-05 | [pipeline.md](pipeline.md) |
| E29 | Gemini OCR-Korrektur Stage 2b | 2-Schritt (Analyse + Korrektur), Variant A/B | 2026-03-05 | [pipeline.md](pipeline.md) |
| E30 | Gemini Vision TEI Generator + dokumenttypspezifische Prompts | 4-Ebenen-Prompts (Layout-Typ, Pub-Form, Genre, Sprache), 12 Genre-Prompts | 2026-03-06 | [pipeline.md](pipeline.md) |
| E31 | Layout-QA Full Run + Overlay-Generator | `--mode auto --force` auf 286 Docs, 14.708 Korrekturen | 2026-03-06 | [pipeline.md](pipeline.md) |
| E32 | Unified TEI Pipeline (Scaffold + Gemini + Assembly) | 4 Stufen, 50/50 VALID im Pilot, ~$17 fuer Korpus | 2026-03-07 | [pipeline.md](pipeline.md) |
| E33 | Digitale Edition (`docs/`) | oeffentliche Website neben internem Dashboard | 2026-03-06 | [viewer.md](viewer.md) |
| E34 | NER Pipeline + Entity Index (Phase 3) | Post-hoc NER via Gemini Flash Lite (6 Typen), Wikidata als Primaer-ID | 2026-03-07 | [entities.md](entities.md) |
| E35 | NER Production-Ready (Phase 3 Scale-Up) | 7 Qualitaetsverbesserungen vor Production Run (Known-Entities-Hint, Diakritik-Matching, Surname-Fallback, 4-Stufen-Konfidenz, OCR-Chunking) | 2026-03-08 | [pipeline.md](pipeline.md) |
| E36 | Curation Editor (Editor in the Loop) | FastAPI Server, 11 API-Endpoints, WYSIWYG | 2026-03-08 | [viewer.md](viewer.md) |
| E37 | TEI Validation Quality Gate + Entity-Tagging Fix | 2-Ebenen (Errors blockierend / Warnings informativ), W1-W10, HTML-Report Default | 2026-03-15 | [pipeline.md](pipeline.md) |
| E38 | Entity-Tagging typkorrekt mit internen IDs | `annotate_entities()` nutzt Entity Index fuer typkorrekte Tags mit interner ID als ref | 2026-03-15 | [entities.md](entities.md) |
| E39 | Sprach-Mapping + facsimile/pb Fix | mehrsprachige Codes (`fra/deu`) korrekt mappen, leere `<surface>` fuer Seiten ohne Layout-Zones | 2026-03-15 | [pipeline.md](pipeline.md) |
| E40 | div-Merge: Seiten-divs zu Dokument-divs | Post-Assembly-Fix `_merge_page_divs()`, Referenz-Vergleich `--compare-ref` | 2026-03-15 | [pipeline.md](pipeline.md) |
| E41 | Agent-Based Quality Screening als Pre-Curation | strukturiertes 7-Schichten-Review, Review-JSON pro Doc | 2026-03-15 | [quality.md](quality.md) |
| E42 | `<revisionDesc>` als Screening-Status im TEI-Header | Status reist mit dem Dokument | 2026-03-15 | [pipeline.md](pipeline.md) |
| E43 | `output/tei_final/` als Single Source of Truth | nur gescreente TEIs werden publiziert | 2026-03-15 | [pipeline.md](pipeline.md) |
| E44 | Entity-Stopwort-Erweiterung noetig | Screening zeigt: Mensch, Est, Gott, Rolle, Wahl, Christ → False Positives | 2026-03-15 | [entities.md](entities.md) |
| E45 | Entity-Stopwort-Erweiterung durchgefuehrt | 20 neue Eintraege, Reassembly 32 Docs, alle VALID, $0 | 2026-03-15 | [entities.md](entities.md) |
| E46 | OCR-Deduplizierung als deterministische Nachbearbeitung | `ocr_dedup.py`: Token-Loops, Barcode-Artefakte, Jahrzahl-Wiederholungen | 2026-03-15 | [pipeline.md](pipeline.md) |
| E47 | `div type="essay"` kein valider DTA-Typ | `type="text"` als generischer Ersatz fuer philosophische Essays | 2026-03-15 | [pipeline.md](pipeline.md) |
| E48 | projektspezifisches Schema `zbz_hersch.rng` | generisches `tei_all.rng` ersetzt durch projektspezifisches Schema (aus ODD, 551 Definitionen) | 2026-03-26 | [pipeline.md](pipeline.md), [quality.md](quality.md) |
| E49 | Editionsrichtlinien ZBZ als verbindliche Referenz | vollstaendige Richtlinien als `data/richtlinien/Editionsrichtlinien_ZBZ.md` | 2026-03-26 | [pipeline.md](pipeline.md) |
| E50 | Dual-Attribut-Strategie fuer Entity-Referenzen | `ref="GND:..."` (primaer) + `corresp="#zbz-p.N"` (intern) | 2026-03-26 | [entities.md](entities.md) |
| E51 | End-to-End CER-Benchmark (TEI vs TEI) | 25 ZBZ-Referenz-TEIs als Ground Truth, `benchmark_cer.py` mit stratifizierter Analyse | 2026-03-26 | [quality.md](quality.md) |
| E54 | wissenschaftliche CER-Re-Evaluation | BCa-Bootstrap (B=10000, Seed=42), Paired Bootstrap E2E vs OCR-only, HCPR (Nosova 2025), Multi-Norm, content-aligned Eval. Headline n=19: Mean 4.10% [2.01,6.75]%, Median 1.83% [0.84,5.14]%. 55 Tests gruen | 2026-04-27 | [quality.md](quality.md) |
| E55 | interaktives CER-Dashboard | `docs/infrastruktur/cer.html` (12 Sektionen) + `docs/js/cer-dashboard.js` (vanilla SVG) + `infra.css` additiv. CIs visuell, Limitations sticky, Lit-Vergleich mit comparable-Enum. **Mit E56 abgeschafft** (CER-Dashboard und Diagnostik wurden ersatzlos entfernt — Daten weiterhin als JSON unter `docs/data/cer_statistics.json` verfuegbar) | 2026-04-27 | [quality.md](quality.md) |
| E56 | Frontend-Reduktion auf Pipeline-Viewer | Edition (Landing, Katalog, Reader, Register, About), Curation Editor (FastAPI), Diagnostik und CER-Dashboard ersatzlos abgeschafft. Neue Single-Page-App `docs/viewer.html` mit Sidebar (Doc-Liste), Faksimile + Layout-Overlay + OCR/TEI-Panel, drei Modi: Anzeigen / Layout bearbeiten / Transkription bearbeiten. Layout-Editor unterstuetzt BBox-Drag, Resize, Add, Delete und Reading-Order-Drag. Persistenz nur via Datei-Download (kein Backend). Volumen: 9→1 HTML, 23→6 JS (7.509→1.420 Z., −81%), 5.023→806 Z. CSS (−84%). E33/E36 ueberholt. `scripts/server/curation_server.py` wird vom Frontend nicht mehr angesteuert (mit E57 aus dem Repo entfernt) | 2026-04-27 | [viewer.md](viewer.md) |
| E57 | Per-Seiten-Mirror + GitHub-Pages-Deploy | `scripts/generate_edition_data.py` mit `mirror_per_page_data()` erweitert: spiegelt Layout-JSONs, Mistral-OCR und per-Seiten-TEI (extrahiert aus `_final.xml` via `<pb>`-Splitting, sequentielle Position 1..N statt n-Attribut wegen Pagination-Drift) fuer alle 285 Docs nach `docs/data/pages/` (8083 Layout + 4117 OCR + 4115 TEI-Seiten, ~99 MB / 16.564 Dateien). Damit funktioniert der Viewer ohne lokalen Server fuer das gesamte Korpus. `core.js`-Pfadresolver mit dreistufiger Fallback-Kette (`pages/` → `examples/` → `../output/`). `docs/.nojekyll` fuer Pages. Bildlieferung weiterhin lokal-only (4 GB PNG via `.gitignore` ausgenommen, nur DEMO-Bilder versioniert). CLI-Flags `--no-mirror`, `--mirror-only`, `--verbose` | 2026-05-25 | [viewer.md](viewer.md) |
| E58 | OpenSeadragon 5.0.1 als Faksimile-Renderer (View-Modus) | Pan + Zoom + Rotate fuer komfortable Faksimile-Arbeit; einfaches Image-Loading (kein Deep-Zoom-Tiling — Pipeline unveraendert); CDN-Bezug via jsDelivr, keine npm/Build-Pipeline. Im Layout-Edit-Modus weiterhin statisches `<img>` mit Eigenbau-Editor — Editor-Integration in OSD per `viewport.viewerElementToImageCoordinates()` ist Folge-Schritt. Renderer in `viewer.js` zweigeteilt: `renderFacsimileOsd()` / `renderFacsimileImg()`, `setMode()` re-rendert bei Variant-Wechsel | 2026-05-25 | [viewer.md](viewer.md) |
| E59 | Polygon-Support nicht eingefuehrt | Hersch-Faksimiles sind sauber gesetzter Druck (1926-2000, Verlagsdruck), Rechtecke decken alle benoetigten Region-Typen (Heading, Paragraph, Footnote, Caption, Filter, Skip). Bedarf an Polygonen entstuende erst bei schraegen Spalten, runden Initialen oder mehrteiligen Regionen — irrelevant fuer dieses Korpus. Damit Annotorious und vergleichbare DH-Libraries explizit nicht noetig; TEI-Datenmodell bleibt `bbox.x_pct/y_pct/w_pct/h_pct` | 2026-05-25 | [viewer.md](viewer.md), [pipeline.md](pipeline.md) |
| E60 | Mode-Button-Redesign Option C: Edit-Toggle pro Panel | Aufloesung der Wort-Redundanz zwischen globalem Mode-Button "Transkription" und Text-Source-Switch "OCR". Globale Mode-Leiste (Anzeigen / Layout / Transkription) entfaellt. Jedes Panel bekommt einen kleinen Bearbeiten-Toggle im Panel-Header. Faksimile-Toggle aktiviert Layout-Editor; Text-Toggle aktiviert Transkriptions-Editor fuer aktive Text-Quelle. `setMode()` in `setImageEdit()` + `setTextEdit()` zerlegt | 2026-05-25 | [viewer.md](viewer.md) |
| E61 | Export-Modul mit JSZip 3.10.1 | Per-Doc-Export-Drawer (Doc-Subbar "Alles ↓") + Multi-Select-Bulk-Export aus Korpus-Uebersicht. Auswahlbare Datentypen: Faksimile-PNGs, OCR pro Engine, Layout-JSON, TEI per-Seite, TEI final, Review-JSON, PAGE-XML. Eine Datei: direkter Download. Mehrere: ZIP mit Verzeichnis-Struktur `{doc_id}/{kategorie}/...` + `manifest.json`. ZIP-Erzeugung im Browser, keine Server-Komponente. Limit bei Multi-Doc-Export ueber 50 Docs (Browser-Memory) | 2026-05-25 | [viewer.md](viewer.md) |

---

## Offene Punkte

| # | Frage | Kontext | Blockiert | Klaerung |
|---|---|---|---|---|
| O8 | Metadaten aus ALMA/MMSID | MMSIDs fuer `teiHeader` | Phase 3 TEI | ZBZ |
| O13 | TEI-Editorial-Details (Schlagworte) | wer erstellt diese? Im Header? Richtlinien: "in Abklaerung" | Phase 3 TEI | ZBZ |
| O18 | multimodale LLM-Korrektur testen (Scan-Bild + OCR-Text) | Forschung: <1% CER (Crosilla 2025). Infrastruktur steht | Quality | eigener Test, [quality.md](quality.md) |
| O22 | 289 vs 286 PDF-Diskrepanz | Masterfile listet 289, E23 hat 286. 3 fehlen | Klaerung | ZBZ |

### Stabilitaet (LLM-Non-Determinismus, pending User-Entscheidung)

- (a) **Stabilitaets-Pilot:** 5 Docs × 3 Pipeline-Re-Runs (~$1-2 API), Std-Dev der Per-Doc-CER. Aktuell `stability.status: open` im JSON.
- (b) **Inter-Engine-CER:** zweiter OCR-Run mit anderer Engine als Cross-Validation. Mittlere Kosten.

### Geschlossene Fragen

- ~~O6~~ Normalisierung vs Quelltreue → E49 (vorlagengetreu mit definierten Normalisierungen)
- ~~O9~~ `div-type`-Werte front/back-Matter → E49 (front: editorial, dedication; back: translation, reprint, otherEdition)
- ~~O11~~ Entities ohne GND-Eintrag → E38/E50 (interne IDs als primaere Referenz, GND in `ref` wenn vorhanden)
- ~~O21~~ Layout-Region Post-Processing → E25/E26 (Gemini QA + Detect, kein manueller Heuristik-Fix)

---

## Risiken

| # | Risiko | Impact | Mitigation | Status |
|---|---|---|---|---|
| R2 | TEI-Komplexitaet + Schema-Inkompatibilitaet | hoch | E48 (`zbz_hersch.rng`) + E49 (Richtlinien) | mitigiert |
| R3 | GND-Halluzinationen | mittel | Seed-Dictionary + Konfidenz-Threshold | offen |
| R5 | Fork-Divergenz DHCraft vs ZBZ | mittel | Merge-Strategie + CI-Tests definieren | offen |
| R7 | Transkribus-Inkompatibilitaet PAGE-XML | hoch | Schema 2013-07-15, ID-Schema `{NNNN}_p{NNN}`, JPG. `@type`/`@custom` nicht verifizierbar (leere TextRegions) | teilweise geklaert (E23) |
| R10 | NER-Qualitaet auf Franzoesisch (66% Korpus) | mittel | Seed-Dictionary vor LLM-NER | offen |

---

## Verweise

- [projekt.md](projekt.md) — Meilensteine + Status
- [pipeline.md](pipeline.md) — Pipeline-Entscheidungen
- [viewer.md](viewer.md) — Edition + Curation (E33, E36, E42, E56, E57, E58, E59, E60, E61)
- [entities.md](entities.md) — Entity Linking (E34/E35/E38/E50)
- [quality.md](quality.md) — CER + Screening (E41-E47, E51, E54/E55)
- [journal.md](journal.md) — chronologische Sitzungs-Historie
