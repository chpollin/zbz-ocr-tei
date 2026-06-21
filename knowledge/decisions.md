---
title: Decisions
type: knowledge
project:
  name: zbz-ocr-tei
  repository: https://github.com/chpollin/zbz-ocr-tei.git
method:
  name: Promptotyping
  url: https://dhcraft.org/Promptotyping/
status: complete
created: 2026-02-18
updated: 2026-06-10
tags: [zbz-ocr-tei, decisions, open, decided]
---

# Decisions

Konsolidiertes Register aller Entscheidungen und offenen Fragen. Cross-cutting, sammelt aus allen Dokumenten.

---

## Entschieden (E1-E63)

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
| E32 | Unified TEI Pipeline (Scaffold + Gemini + Assembly) | 4 Stufen, 50/50 VALID im Pilot | 2026-03-07 | [pipeline.md](pipeline.md) |
| E33 | Digitale Edition (`docs/`) | oeffentliche Website neben internem Dashboard | 2026-03-06 | [viewer.md](viewer.md) |
| E34 | NER Pipeline + Entity Index (Phase 3) | Post-hoc NER via Gemini Flash Lite (6 Typen), Wikidata als Primaer-ID | 2026-03-07 | [pipeline.md](pipeline.md) |
| E35 | NER Production-Ready (Phase 3 Scale-Up) | 7 Qualitaetsverbesserungen vor Production Run (Known-Entities-Hint, Diakritik-Matching, Surname-Fallback, 4-Stufen-Konfidenz, OCR-Chunking) | 2026-03-08 | [pipeline.md](pipeline.md) |
| E36 | Curation Editor (Editor in the Loop) | FastAPI Server, 11 API-Endpoints, WYSIWYG | 2026-03-08 | [viewer.md](viewer.md) |
| E37 | TEI Validation Quality Gate + Entity-Tagging Fix | 2-Ebenen (Errors blockierend / Warnings informativ), W1-W10, HTML-Report Default | 2026-03-15 | [pipeline.md](pipeline.md) |
| E38 | Entity-Tagging typkorrekt mit internen IDs | `annotate_entities()` nutzt Entity Index fuer typkorrekte Tags mit interner ID als ref | 2026-03-15 | [pipeline.md](pipeline.md) |
| E39 | Sprach-Mapping + facsimile/pb Fix | mehrsprachige Codes (`fra/deu`) korrekt mappen, leere `<surface>` fuer Seiten ohne Layout-Zones | 2026-03-15 | [pipeline.md](pipeline.md) |
| E40 | div-Merge: Seiten-divs zu Dokument-divs | Post-Assembly-Fix `_merge_page_divs()`, Referenz-Vergleich `--compare-ref` | 2026-03-15 | [pipeline.md](pipeline.md) |
| E41 | Agent-Based Quality Screening als Pre-Curation | strukturiertes 7-Schichten-Review, Review-JSON pro Doc | 2026-03-15 | [quality.md](quality.md) |
| E42 | `<revisionDesc>` als Screening-Status im TEI-Header | Status reist mit dem Dokument | 2026-03-15 | [pipeline.md](pipeline.md) |
| E43 | `output/tei_final/` als Single Source of Truth | nur gescreente TEIs werden publiziert | 2026-03-15 | [pipeline.md](pipeline.md) |
| E44 | Entity-Stopwort-Erweiterung noetig | Screening zeigt: Mensch, Est, Gott, Rolle, Wahl, Christ → False Positives | 2026-03-15 | [pipeline.md](pipeline.md) |
| E45 | Entity-Stopwort-Erweiterung durchgefuehrt | 20 neue Eintraege, Reassembly 32 Docs, alle VALID | 2026-03-15 | [pipeline.md](pipeline.md) |
| E46 | OCR-Deduplizierung als deterministische Nachbearbeitung | `ocr_dedup.py`: Token-Loops, Barcode-Artefakte, Jahrzahl-Wiederholungen | 2026-03-15 | [pipeline.md](pipeline.md) |
| E47 | `div type="essay"` kein valider DTA-Typ | `type="text"` als generischer Ersatz fuer philosophische Essays | 2026-03-15 | [pipeline.md](pipeline.md) |
| E48 | projektspezifisches Schema `zbz_hersch.rng` | generisches `tei_all.rng` ersetzt durch projektspezifisches Schema (aus ODD, 551 Definitionen) | 2026-03-26 | [pipeline.md](pipeline.md), [quality.md](quality.md) |
| E49 | Editionsrichtlinien ZBZ als verbindliche Referenz | vollstaendige Richtlinien als `data/source/guidelines/Editionsrichtlinien_ZBZ.md` | 2026-03-26 | [pipeline.md](pipeline.md) |
| E50 | Dual-Attribut-Strategie fuer Entity-Referenzen | `ref="GND:..."` (primaer) + `corresp="#zbz-p.N"` (intern) | 2026-03-26 | [pipeline.md](pipeline.md) |
| E51 | End-to-End CER-Benchmark (TEI vs TEI) | 25 ZBZ-Referenz-TEIs als Ground Truth, `benchmark_cer.py` mit stratifizierter Analyse | 2026-03-26 | [quality.md](quality.md) |
| E54 | wissenschaftliche CER-Re-Evaluation | BCa-Bootstrap (B=10000, Seed=42), Paired Bootstrap E2E vs OCR-only, HCPR (Nosova 2025), Multi-Norm, content-aligned Eval. Headline n=19: Mean 4.10% [2.01,6.75]%, Median 1.83% [0.84,5.14]% (historischer Stand 2026-04-27; aktuelle Headline siehe [[E85]]: Mean 2.71%/Median 1.40%, n=25). 55 Tests gruen | 2026-04-27 | [quality.md](quality.md) |
| E55 | interaktives CER-Dashboard | `docs/infrastruktur/cer.html` (12 Sektionen) + `docs/js/cer-dashboard.js` (vanilla SVG) + `infra.css` additiv. CIs visuell, Limitations sticky, Lit-Vergleich mit comparable-Enum. **Mit E56 abgeschafft** (CER-Dashboard und Diagnostik wurden ersatzlos entfernt — Daten weiterhin als JSON unter `docs/data/cer_statistics.json` verfuegbar) | 2026-04-27 | [quality.md](quality.md) |
| E56 | Frontend-Reduktion auf Pipeline-Viewer | Edition (Landing, Katalog, Reader, Register, About), Curation Editor (FastAPI), Diagnostik und CER-Dashboard ersatzlos abgeschafft. Neue Single-Page-App `docs/viewer.html` mit Sidebar (Doc-Liste), Faksimile + Layout-Overlay + OCR/TEI-Panel, drei Modi: Anzeigen / Layout bearbeiten / Transkription bearbeiten. Layout-Editor unterstuetzt BBox-Drag, Resize, Add, Delete und Reading-Order-Drag. Persistenz nur via Datei-Download (kein Backend). Volumen: 9→1 HTML, 23→6 JS (7.509→1.420 Z., −81%), 5.023→806 Z. CSS (−84%). E33/E36 ueberholt. `scripts/server/curation_server.py` wird vom Frontend nicht mehr angesteuert (mit E57 aus dem Repo entfernt) | 2026-04-27 | [viewer.md](viewer.md) |
| E57 | Per-Seiten-Mirror + GitHub-Pages-Deploy | `scripts/edition/generate_edition_data.py` mit `mirror_per_page_data()` erweitert: spiegelt Layout-JSONs, Mistral-OCR und per-Seiten-TEI (extrahiert aus `_final.xml` via `<pb>`-Splitting, sequentielle Position 1..N statt n-Attribut wegen Pagination-Drift) fuer alle 285 Docs nach `docs/data/pages/` (8083 Layout + 4117 OCR + 4115 TEI-Seiten, ~99 MB / 16.564 Dateien). Damit funktioniert der Viewer ohne lokalen Server fuer das gesamte Korpus. `core.js`-Pfadresolver mit dreistufiger Fallback-Kette (`pages/` → `examples/` → `../output/`). `docs/.nojekyll` fuer Pages. Bildlieferung weiterhin lokal-only (4 GB PNG via `.gitignore` ausgenommen, nur DEMO-Bilder versioniert). CLI-Flags `--no-mirror`, `--mirror-only`, `--verbose` | 2026-05-25 | [viewer.md](viewer.md) |
| E58 | OpenSeadragon 5.0.1 als Faksimile-Renderer (View-Modus) | Pan + Zoom + Rotate fuer komfortable Faksimile-Arbeit; einfaches Image-Loading (kein Deep-Zoom-Tiling — Pipeline unveraendert); CDN-Bezug via jsDelivr, keine npm/Build-Pipeline. Im Layout-Edit-Modus weiterhin statisches `<img>` mit Eigenbau-Editor — Editor-Integration in OSD per `viewport.viewerElementToImageCoordinates()` ist Folge-Schritt. Renderer in `viewer.js` zweigeteilt: `renderFacsimileOsd()` / `renderFacsimileImg()`, `setMode()` re-rendert bei Variant-Wechsel | 2026-05-25 | [viewer.md](viewer.md) |
| E59 | Polygon-Support nicht eingefuehrt | Hersch-Faksimiles sind sauber gesetzter Druck (1926-2000, Verlagsdruck), Rechtecke decken alle benoetigten Region-Typen (Heading, Paragraph, Footnote, Caption, Filter, Skip). Bedarf an Polygonen entstuende erst bei schraegen Spalten, runden Initialen oder mehrteiligen Regionen — irrelevant fuer dieses Korpus. Damit Annotorious und vergleichbare DH-Libraries explizit nicht noetig; TEI-Datenmodell bleibt `bbox.x_pct/y_pct/w_pct/h_pct` | 2026-05-25 | [viewer.md](viewer.md), [pipeline.md](pipeline.md) |
| E60 | Mode-Button-Redesign Option C: Edit-Toggle pro Panel | Aufloesung der Wort-Redundanz zwischen globalem Mode-Button "Transkription" und Text-Source-Switch "OCR". Globale Mode-Leiste (Anzeigen / Layout / Transkription) entfaellt. Jedes Panel bekommt einen kleinen Bearbeiten-Toggle im Panel-Header. Faksimile-Toggle aktiviert Layout-Editor; Text-Toggle aktiviert Transkriptions-Editor fuer aktive Text-Quelle. `setMode()` in `setImageEdit()` + `setTextEdit()` zerlegt | 2026-05-25 | [viewer.md](viewer.md) |
| E61 | Export-Modul mit JSZip 3.10.1 | Per-Doc-Export-Drawer (Doc-Subbar "Alles ↓") + Multi-Select-Bulk-Export aus Korpus-Uebersicht. Auswahlbare Datentypen: Faksimile-PNGs, OCR pro Engine, Layout-JSON, TEI per-Seite, TEI final, Review-JSON, PAGE-XML. Eine Datei: direkter Download. Mehrere: ZIP mit Verzeichnis-Struktur `{doc_id}/{kategorie}/...` + `manifest.json`. ZIP-Erzeugung im Browser, keine Server-Komponente. Limit bei Multi-Doc-Export ueber 50 Docs (Browser-Memory) | 2026-05-25 | [viewer.md](viewer.md) |
| E62 | Methode-Seite `docs/methode.html` | Schlanke statische Seite (Prose-Layout wie About) mit Headline-CER, stratifizierten Werten (Layout-Typ + Sprache), Forschungs-Literatur-Vergleich, Limitations und Werkzeug-Doku. Daten statisch eingebettet (kein Lazy-Load aus `cer_statistics.json`, da JSON nicht eingecheckt). Bewusst kein interaktives Dashboard (E55 wurde mit E56 abgeschafft) — wer Bootstrap-Verteilungen visuell sehen will, regeneriert das JSON ueber `cer_statistics_full.py`. Nav-Eintrag "Methode" in allen 3 Hauptseiten; About-Qualitaets-Absatz verweist auf Methode-Seite. `.prose table` zu `base.css` additiv hinzugefuegt. **Niemals LLMs fuer Entity-ID-Linking** als implizite Methodik-Position (siehe [[feedback-no-llm-for-id-linking]]) | 2026-05-26 | [viewer.md](viewer.md) |
| E63 | Leerseiten-Erkennung + Viewer-Handling (Phase 1) | 79 Leerseiten korpusweit (Vorsatz/Rueck/Durchschlag): trivialer OCR-Muell (`.`, `^{}[]`, leeres Tabellengeruest) + explizite "Blank Page"-Marker. Ursache Phantom-Regionen: Gemini-Layout-QA halluziniert Boxen (bis 21), Docling sagt korrekt 0 — Doppelsignal. Viewer-Fix **interim/heuristisch** (`core.js` `isBlankPageText`: <=5 Zeichen ODER keine Buchstaben/Ziffern): leere Seiten zeigen "Leerseite — kein Text", Phantom-Kaesten unterdrueckt. **Phase 2 umgesetzt: siehe E65.** Grauzone (Nur-Bild ~10, OCR-Schleifen) NICHT automatisch — zwei Auto-Detektoren erzeugten Fehlalarme (Zeitungskoepfe, Inhaltsverzeichnisse), Experten-Review im Manifest noetig | 2026-05-26 | [viewer.md](viewer.md) |

---

## Entschieden (E64-E88, Detail)

Juengere Entscheidungen mit ausfuehrlicher Begruendung als eigene Abschnitte
(Reihenfolge wie zuvor in der Tabelle).

### E64 — Viewer-Verdichtung: OCR-Quellen-Umschalter entfernt, Leisten fusioniert, Edit-Toggles benannt (2026-05-26)

OCR-Source-Dropdown (5 Engines: Mistral/Gemini A/Gemini B/LLM Haiku/DeepSeek) aus dem Viewer entfernt. Befund: der ausgelieferte Mirror (`docs/data/pages/`) enthaelt nur Mistral; die Alt-Engines zeigen auf `../output/` (gitignored, nicht deployed) und sind reine Benchmark-/Forschungs-Artefakte (E51/E54), auf der Live-Seite tot. Prinzip: **Viewer = ausgelieferte Edition = Mistral**; Engine-Vergleich ist separate Forschung, nicht im Viewer-UI. `ocrSource` fest auf `mistral`. Doc-Subbar + Toolbar **fusioniert** (Etappe 2.10 teilweise erledigt): Seitennav wandert in die Doc-Subbar, separate `.toolbar` entfaellt (war nach Dropdown-Wegfall fast leer); `.toolbar`/`.toolbar__inner`/`.toolbar__group--right` CSS entfernt, `.doc-subbar__inner` erbt `--v-toolbar-height`. Edit-Toggles umbenannt "Bearbeiten"/"Bearbeiten" → **"Layout"/"Text"** (Objekt-Label; Aktiv-Zustand zeigt der anthrazit-gefuellte Button — User-Entscheidung gegen Label-Wechsel/Icons). Verifiziert in Chrome (Konsole sauber, Aktiv-Zustand visuell bestaetigt; `getComputedStyle` im isolierten Browser-Kontext liefert bei nativen Buttons irrefuehrende Werte — Bodenwahrheit ist das Bild)

Dokumente: [viewer.md](viewer.md)

### E65 — Leerseiten-Manifest + TEI-Marker (E63 Phase 2, Schritt 1+2) (2026-05-26)

`scripts/edition/page_manifest.py` erzeugt pro Objekt `output/tei_final/{doc}_manifest.json` (gitignored, regenerierbar; nur Ausnahme-Seiten; Felder `class`/`source`/`review`/`evidence` + `streams`-Header) — Detektor (OCR-Regel identisch `ZBZ.isBlankPageText` + Blank-Marker, UND Docling `num_regions==0` als Gegensignal) findet **79 sichere Leerseiten in 15 Docs, alle cross-validiert, 0 Konflikte**. `scripts/tei/tei_blank_marker.py` projiziert daraus `<pb type="blank"/>` in die finalen TEI (Seite = sequenzielle pb-Position, identisch zum Mirror-Splitter) und **leert den Seiten-Body** (User-Entscheidung: bestaetigte Leerseite = nur Marker; entfernt symbolischen Muell + "blank"-Woerter + LLM-Korrektur-Kommentar + Seitenzahlen; leer gewordene `<div>` eingeklappt, strukturelle div-Grenzen bewahrt). 82 Junk-Elemente entfernt, 0 Residual, **0 Schema-Regression** (Backup vs. editiert je 4 Fehler unveraendert — die 4 sind der vorbestehende idno-Header-Befund [[O23]]). Mirror via `--mirror-only` neu (94 Dateien), in Chrome verifiziert (doc 20). Sicherheit: Dry-Run, Backup, Residual-/Konsistenzpruefung. **Offen (Schritt 3):** Viewer von Heuristik auf Manifest/Marker umstellen

Dokumente: [viewer.md](viewer.md)

### E67 — Catalog-UI-Refactor + Ampel-Reframing + Site-Konsistenz (2026-05-26)

Iterativer UI-Pass auf der Korpus-Uebersicht (`docs/index.html`) und site-weit: (a) Tabelle komplett ueberarbeitet -- ein Schriftbild (Body EB Garamond, mono nur fuer Doc-IDs/Stream-Labels), Header sitzt im gleichen Surface wie der Body (kein zweikartiges Bild), klickbare Spaltenheader mit Sortier-Affordance im Ruhezustand (gedimmtes `↕`-Pfeil, aktiv `↑`/`↓` in Ziegelrot), Autor + Datum als separate Spalten, Workflow-Spalte vertikal mit OCR/Layout/TEI-XML-Labels rechts neben den Ampel-Dots, einheitliche 32-px-Hoehe fuer Filter-Bar-Eingaben + Reset-Button in einer Reihe; (b) **Ampel-Reframing**: User-Befund "kein Mensch hat approved" plus "Pipeline-Output EXISTIERT, ist nur nicht verifiziert" → die fruehere `offen=rot`-Lesart war epistemisch schief. Datenstatus `offen` umbenannt in `unverifiziert` (Default fuer alle 285 Docs), Migration in [page_manifest.py](../scripts/edition/page_manifest.py) idempotent. Ampel-Mapping: **gelb** = `unverifiziert|in_arbeit|bearbeitet` (vorhanden, nicht freigegeben), **gruen** = `fertig`. **Rot reserviert** fuer einen kuenftigen expliziten Problem-/Reject-Status. Tooltip im Catalog erklaert das fuer den Default-Fall ("Pipeline-Output existiert, noch nicht menschlich verifiziert"); (c) sticky Filter-Bar + single Page-Scroll loest fruehere Doppel-Scroll-Insel; (d) Site-weiter Footer (Edition / Tech-Umsetzung / Impressum / GitHub-Icon), `Experimentell`-Badge im Header-Zentrum mit Tooltip, [impressum.html](../docs/impressum.html) als Stub mit Verantwortlichkeiten; (e) Author-Namen normalisiert in `generate_edition_data._normalize_author` (HARTE-Caps wie "JEANNE HERSCH" → "Jeanne Hersch"); (f) [E63 Phase 2 Schritt 3]: Viewer liest jetzt primär `<pb type="blank"/>` aus der per-Seiten-TEI (Marker-getrieben), Heuristik `isBlankPageText` bleibt nur als Fallback fuer Faelle ohne TEI.

Dokumente: [viewer.md](viewer.md), [quality.md §Workflow-Status](quality.md)

### E68 — `zbz_hersch.rng` um weggelassene Standard-TEI-Elemente erweitert (2026-05-27)

Das ODD-Subset von E48 (2026-01-28) hatte `revisionDesc`/`change` (E42/E66), `langUsage`/`language`, `idno` (im `publicationStmt`) und `monogr`/`imprint` (im `biblStruct`) weggelassen -- alles Standard-TEI/DTA, das die Pipeline regulaer erzeugt. Folge: **0/285** ausgelieferte TEI valide gegen ihr eigenes Schema (gegen das alte `tei_all.rng` aber 8/8 valide), nie aufgefallen, weil `tei_final` flach abgelegt ist und durch `validate_all` (erwartet verschachtelt wie `tei_unified`) durchfaellt und die `tei_blank_marker`/`tei_status_marker`-Schritte ohne Re-Validierung dort schreiben. Fix: 7 Definitionen ergaenzt + 4 Inhaltsmodelle verdrahtet (teiHeader, publicationStmtPart.detail, profileDescPart, biblStruct), Inhaltsmodelle bewusst minimal am real erzeugten Datenvertrag (korpusweite Kind-Element-Erhebung). `source-metadata` als kuratierter div-Typ in `config.py` registriert (Doc 1170). Ergebnis **285/285 valide**. Neues pytest-Gate `tests/test_tei_schema.py` (Schema kompiliert + synthetischer E68-Header valide + jedes `tei_final` valide; lokal volle Zaehne, skippt auf frischem Clone, da `output/` gitignored). Loest [[O23]] -- der dort nur `idno` benannte, tatsaechlich waren es vier Ursachen

Dokumente: [quality.md](quality.md), [pipeline.md](pipeline.md)

### E66 — Agent-Screening abschaffen, Workflow-Status pro Strom einfuehren (2026-05-26)

User-Befund: kein Mensch hat die 285 "APPROVED" gegeben -- der Agent screent sich selbst mit eingebauter Ignorier-Liste (W3/W6/W10 als "normal" deklariert), und das Etikett ist gegenueber ZBZ epistemisch irrefuehrend. Ersatz: vier Statuswerte (`offen | in_arbeit | bearbeitet | fertig`) je Datenstrom (`ocr`, `layout`, `tei`), gesetzt von Menschen im Viewer. Datenmodell: das Pro-Objekt-Manifest aus [[E65]] wird erweitert -- `streams.*` wird vom statischen Engine-Deskriptor zum Objekt `{engine|engines|source, status, history}` mit voller History-Provenienz (`[{at, by, from, to, note}]`). `page_manifest.py` ist idempotent: Re-Lauf bewahrt status+history, schreibt fuer alle 285 Docs (vorher nur Docs mit Leerseiten). UI: drei Bars (OCR/Layout/TEI) plus Filter `Strom × Status` in [index.html](../docs/index.html), Status-Pills in der Doc-Subbar des Viewers mit Klick-Cycle; erstes Edit-Toggle setzt automatisch `offen → in_arbeit`. Mirror nach `docs/data/manifests/{doc}_manifest.json`. ZBZ-Uebergabe: `scripts/tei/tei_status_marker.py` projiziert die History deterministisch als `<change when= who= status= n={stream}>...</change>` in den `<revisionDesc>` und entfernt dabei alle Eintraege mit `who` matched `^(agent-screening|quality-screen|quality-pass|claude)` -- der `who="pipeline"`-Eintrag bleibt. Legacy: `_review.json` -> `_screening_legacy.json` (gitignored), Stand bleibt als Diagnose-Spur. Stand: 285/285 Docs auf `offen`, der ehrliche Anker

Dokumente: [viewer.md](viewer.md), [quality.md §Workflow-Status](quality.md)

### E70 — CER-Methodik korrigiert: Drei-Zahlen-Zerlegung (Fidelity/Scope/Full), kein Trimming, case-sensitiv, drei Pfade vereinheitlicht (2026-05-27)

Tiefe Pruefung der CER-Erzeugung (User-Auftrag "ganz genau und richtig"), extern verifiziert gegen OCR-D/dinglehopper/Transkribus/jiwer/Singh 2025. **Kernbefund**: die ZBZ-Referenz-TEIs sind selektive Teiltranskriptionen (Doc 580: 2 Rezensionen vs 1; Doc 570: Masthead fehlt; Doc 90: Inhaltsverzeichnis), die Pipeline ist oft vollstaendiger. Das alte `find_best_alignment`-Trimming verbarg Insertions UND Verluste (+ Padding-auf-Referenzlaenge = Deflation); naive Volltext-CER bestraft umgekehrt das Vollstaendiger-Sein (Doc 570: 113%). **Loesung**: `classify_edit_operations` zerlegt jede Editieroperation -> **Fidelity-CER** (Substitutionen + kleine Indels + ALLE Loeschungen = echte Fehler) vs **Scope-Rate** (grosse Einfuegungen >=50 Zeichen = Pipeline-Mehrtext, kein Fehler); `cer_fidelity + scope_insertion_rate = cer`. Headline = Fidelity, **Mean 4.26% / Median 1.83% ueber ALLE 25 Docs** (kein zirkulaerer Ausschluss noetig) -- reproduziert die fruehere Zahl sauber. Weitere Fixes: (a) pauschales `.lower()` raus, case-sensitiv als Default (Effekt ~0, Case nur in Versal-Lauftiteln); (b) drei CER-Pfade (`benchmark_cer`, `cer_statistics_full`, `tei_validator --compare-ref`) auf `extract_text_for_comparison`+`calculate_cer` vereinheitlicht, `--compare-ref` nutzt `tei_final/` statt rohem `itertext()` aus `tei_unified/{id}/`; (c) zirkulaeres `cer>50%`-Ausschlusskriterium entfernt (nur noch struktureller Seitenzahl-Filter), latenter Bug `ref_pages_total`->`ref_pages` behoben; (d) Blank-`<pb>` aus Page-Count; (e) Fehlerkategorien via `rapidfuzz.opcodes` (summieren exakt zur Levenshtein-Distanz) statt `difflib`; (f) Paired-Test like-for-like auf Fidelity: **-7.12pp, p=0.14 (n=19, nicht signifikant)** -- die fruehere Angabe "-14.83pp p=0.0004" war ein Trimming-Artefakt und ist zurueckgezogen. Zitation korrigiert: arXiv:2510.06743 ist Levchenko 2025, nicht "Nosova et al.". Neue goldene Tests `tests/test_cer_extraction.py` (18). Suite **507 gruen**. JSON `docs/data/cer_statistics.json` neu (Seed 42). OFFEN (User-Entscheidung): ob Topf A (Pipeline-Mehrtext: Masthead/Nachbar-Rezensionen) erwuenschter Editions-Inhalt oder rauszufilternder Beifang ist

Dokumente: [quality.md §Korrektheits-Welle](quality.md)

### E69 — Korrektheits-Welle: O24-Fix + `<pb>`-Segmentierung zentralisiert + teiHeader-Generator auf Liefer-Vertrag + MMSID (2026-05-27)

Drei stille Korrektheitsprobleme geschlossen, alle mit Test-Gate. (a) **O24**: `tei_validator._compute_cer` importierte ein nicht existentes `compute_cer` -> still auf Laengen-Approximation gefallen; Fix `calculate_cer` * 100 (Ratio->Prozent), `except` auf `ImportError`. (b) **`<pb>`-DRY**: die Regel "Seitenzahl = 1-basierte sequenzielle pb-Position" war in `generate_edition_data.py` und `tei_blank_marker.py` dupliziert (nur per Kommentar synchron) -> neuer Helfer `scripts/tei/pb_split.py` (`PB_RE`, `BODY_INNER_RE`, `iter_page_spans`); byte-identisch verifiziert ueber alle 285 Finals + 15 Blank-Reports (Baseline-Snapshot). (c) **teiHeader-Armut**: `build_tei_header` erzeugte docID nur als Kommentar + einfaches `<bibl>` + kein `langUsage` -> ein `tei_unified`-Neulauf regressierte jeden Header (Verlust von `<idno>`/`biblStruct`, die [[E68]] erst schema-valide machte). Neufassung deckungsgleich zum Liefer-Vertrag (`<idno type="docID">` + `<biblStruct>`/`<monogr>`/`<imprint>` + `<langUsage>` je Sprachcode). (d) **MMSID/[[O8]]**: `scripts/core/masterfile.py` liest die Alma-MMSID aus der Masterfile, Header fuehrt sie als `<idno type="MMSID">` (konditional; **Teil (d) mit [[E76]] 2026-06-03 wieder entfernt**). Verifiziert: Header valide in allen Kanten, `--reassemble` doc 100 end-to-end VALID, Suite 503 gruen

Dokumente: [quality.md](quality.md), [pipeline.md](pipeline.md)

### E71 — NER / Entity-Linking vollstaendig entfernt (2026-05-27)

Named-Entity-Recognition + Entity-Linking aus der Pipeline genommen (User-Entscheidung). Befund: die Verlinkung war im ausgelieferten TEI nicht funktionsfaehig -- nur ~2.6% der ~30.500 getaggten Erwaehnungen trugen eine echte GND-ID, der Rest `GND:unknown` (1.274x) oder interne `#zbz-`-IDs; das dokumentierte Dual-Attribut [[E50]] existierte im Output gar nicht (0x `corresp="#zbz-"`). Entfernt: NER-Schritt aus `tei_unified` (`--ner`), Entity-Seeding + Mapping-Table-Section-4 aus `tei_mapping_prompt`, `annotate_entities` (`tei_generator`/`tei_step1`) + `reannotate_entities` (`tei_step2`), `scripts/ner/` (6 Module), `data/entities/*.xml`, `docs/data/entity_index.json`, NER-Konstanten in `config.py`, `export_entity_index` in `generate_edition_data`, Viewer-Entity-Highlighting (`tei-render.js` + `.tei__entity*` in `viewer.css`), About-NER-Bullet. Deterministischer Body-Strip ueber alle 285 TEI (3 Ablagen: `tei_final`, `docs/data/tei`, Per-Seiten-Mirror): `<persName>`/`<orgName>`/`<placeName>` + Inline-Werk-`<bibl>` aufgeloest; `<bibl>` in `<listBibl>` + Review-`<head>` als bibliografische Struktur behalten (ref/corresp entfernt). 285/285 schema-valide (`test_tei_schema`), Script-Health gruen. Macht [[R3]]/[[R10]] hinfaellig. Restposten: stale Entity-Prosa in 7 `<revisionDesc>`-`<change>`-Eintraegen (Agent-Screening-Log im teiHeader)

Dokumente: [pipeline.md](pipeline.md)

### E72 — Direkt-Schreiben-Loop fuer die Viewer-Kuration (File System Access API + Backend-Konsumenten) (2026-05-27)

Die Kuration persistierte bisher nur per Browser-Download + manuelles Ablegen; zudem hatten die kuratierten Layout-/OCR-Dateien **gar keinen Konsumenten** in der Pipeline (nur das Manifest war verdrahtet), der dokumentierte Round-Trip war also teils aspirativ. Zwei Haelften umgesetzt: (a) **Frontend** -- neues Modul `docs/assets/js/fs-access.js` (`ZBZ.FsAccess`) schreibt kuratierte Dateien per File System Access API direkt in den vom Nutzer einmal freigegebenen Repo-Ordner (Handle in IndexedDB persistiert; Schreibrecht pro Sitzung per Geste re-granted). `viewer.js` Save-Handler nutzen FSA bei Verbindung, sonst `ZBZ.Download` (Fallback fuer Firefox/Safari); neuer "Ordner verbinden"-Button in der Doc-Subbar. (b) **Backend** -- `load_layout_gemini` liest `{doc}_p{NNN}_layout_curated.json` vor Gemini/Docling; `OCR_CURATED_DIR` (`output/ocr_curated/`) als erstes Element in `_OCR_DIRS` (`scripts/core/loaders.py`), damit `--reassemble` die Edits real verwendet. Regeneration per dokumentiertem One-Liner (`tei_unified --reassemble` + `generate_edition_data --mirror-only`). Caveat: TEI-XML-Direktedit ueberschreibt `tei_final/{doc}_final.xml` (SoT) und wird von einem spaeteren `--reassemble` wieder regeneriert -- empfohlener Pfad sind Layout/OCR-Edits. Gate: `tests/test_curated_loaders.py` (9 Tests, Loader-Praezedenz). Sicherheit: kein Token, kein Auto-Write -- Zugriff nur nach expliziter Ordnerwahl + readwrite-Grant. Out of scope (Nutzer-Entscheidung): lokaler Watcher + GitHub-Actions-Regeneration

Dokumente: [viewer.md §Persistenz](viewer.md)

### E73 — CER-Scope: hartkodierte 6er-Ausschlussliste (`SCOPE_MISMATCH_REASONS`) entfernt, alle Metriken ueber alle 25 Docs (2026-05-27)

Rohdaten-Verifikation (User-Auftrag "ganz genau in die Daten schauen"): die Liste (1440, 30, 300, 3020, 760, 830) folgte **keinem reproduzierbaren Kriterium** -- schloss Doc 570 (112% Mehrtext, Voll-CER 113%, Fidelity 0.9%) NICHT aus, markierte aber 3020/760/830 (scope_insertion ~0.5-1.2% = kein Inhalts-Mismatch, nur feinere `<pb>`-Segmentierung der Referenz). Zwei Code-Kommentare faktisch falsch (1440: Seitenzahlen vertauscht; 30: "Anfangsausschnitt" -- real hat die Referenz mehr Seiten + gleiche Zeichenzahl). Die Liste diente nur, eine scope-inklusive Subset-Kennzahl "fair" zu machen. **`_override_scope` setzt jetzt alle `scope_status="full"`** (kein Ausschluss). **Fidelity-CER bleibt unveraendert: Mean 4.26% / Median 1.83% (n=25)** -- sie rechnet schon ueber alle Docs und ist via `classify_edit_operations` scope-robust. Der rohe `end_to_end` (jetzt n=25, Mean 20.75%) ist als **Diagnose, kein Qualitaetsmass** gekennzeichnet; Paired-Test jetzt n=25: **-7.90pp, p=0.07** (war -7.12pp/n=19, weiterhin n.s.). 55 CER-Tests + Suite (524) gruen; `methode.html` + Arbeitsbericht 6.1 nachgezogen. Schliesst den OFFEN-Punkt aus [[E70]]

Dokumente: [quality.md](quality.md)

### E74 — Eingebettete Schematron-Regeln bewusst NICHT ausgefuehrt (dokumentiert statt gebaut) (2026-05-27)

`tei_validator` prueft `zbz_hersch.rng` als RelaxNG-Grammatik (285/285 valide). Frage: sollen die 36 eingebetteten `sch:rule` (50 `assert` + 24 `report`) zusaetzlich laufen? Spike-Verifikation (`lxml.isoschematron`, 3 Wegwerf-Skripte): (a) **14/36 Regeln brauchen XPath 2.0** (`gt`/`cast as xs:date`/`tokenize`/`current-date`) -- libxslt ist XSLT 1.0, nicht lauffaehig; (b) die **22 lauffaehigen** Regeln zielen auf TEI-ODD/Schema-Konstrukte (`elementSpec`, `attDef`, `schemaSpec`, `@validUntil`, `addSpan`) und finden ueber **alle 285 Editionen 0 Treffer** (Harness mit synthetischer Immer-Fehl-Regel als korrekt bewiesen). Es ist generisches TEI-P5-Boilerplate, keine editorischen Editions-Regeln. Ein lxml-Pass liefe nur halb und meldete immer "0" = irrefuehrendes Validierungs-Theater. **Entscheidung: nicht bauen.** Echte editorische Validierung waeren NEUE projektspezifische Regeln (separates Vorhaben, ggf. via Saxon/XSLT-2.0 fuer volle Abdeckung)

Dokumente: [quality.md](quality.md)

### E75 — Tote OCR-Wege entfernt: `ocr_dedup` + DoclingOCR-Engine (2026-05-27)

Aufraeum-Welle (User-Auftrag). (a) `ocr_dedup.py` ([[E46]]) war **verwaist** (kein Code-Importeur), las hartkodiert `output/ocr_results` (falsch/leer statt `mistral_results`) und mutierte OCR in-place **ohne Backup** -> entfernt statt repariert (Reparatur haette ein destruktives Tool auf der Basis-OCR scharfgeschaltet). (b) `DoclingOCR` als OCR-Engine schrieb Single-File `_docling.md` (**Sackgasse**, von der `_p{N}.md`-Pipeline nie konsumiert), `auto`-Modus routete `TWO_COLUMN_DOCS` dorthin (latentes **Fehlrouting**) -> Klasse + `docling`-Choice + auto-Routing entfernt; auto/mistral/gemini schreiben jetzt einheitlich nach `mistral_results/`. Docling als **Layout**-Engine ([[E19]]/[[E20]], war nie OCR) unberuehrt. 524 Tests gruen

Dokumente: [pipeline.md](pipeline.md)

### E76 — MMSID-Projektion aus der Pipeline entfernt (Header-Metadaten = ZBZ-Domaene) (2026-06-03)

User-Entscheidung: die mit [[E69]] Teil (d) eingefuehrte MMSID-Projektion wird wieder entfernt. Begruendung: Header-Metadaten aus Alma sind laut [[O8]] ZBZ-seitig; die MMSID war zudem nur im Code, **nie in einem ausgelieferten TEI** (0/285). Entfernt: `scripts/core/masterfile.py` (ganzes Modul, nur von `tei_unified` importiert), Import + `metadata["mmsid"]`-Aufruf in `tei_unified`, Emission + Docstring in `tei_step3.build_tei_header`, MMSID-Test + Schema-Fall in `tests/test_tei_header.py`, Doku in CLAUDE.md + scripts/README.md. Suite 524 -> **520 gruen**, keine Regression. **Spec-Konflikt bewusst in Kauf genommen:** die ZBZ-Editionsrichtlinien (`data/source/guidelines/Editionsrichtlinien_ZBZ.md`, [[E49]]) fordern ID+MMSID+PubForm im Header — mit ZBZ zu klaeren ([[O8]]). Unberuehrt: ZBZs Richtlinien-Datei (immutabler Input) und der faktische Masterfile-Spalten-Hinweis im Arbeitsbericht (beschreibt nur die Quelle, kein Header-Claim)

Dokumente: [decisions.md](decisions.md)

### E77 — Workflow-Status von vier auf drei Stufen kollabiert (Variante A) (2026-06-07)

User-Entscheidung. Statt `unverifiziert|in_arbeit|bearbeitet|fertig` jetzt **`unverifiziert|in_arbeit|verifiziert`** je Strom. Befund: die vier Stufen kollabierten im UI ohnehin auf nur zwei Ampel-Farben (gelb fuer die ersten drei, gruen fuer `fertig`), und `bearbeitet` vs `fertig` war eine unscharfe Naht ("bearbeitet, aber nicht fertig" = in Arbeit). Drei Stufen geben **eine Farbe je Stufe**: neutral/grau (`unverifiziert`, `--h-text-muted`), gelb (`in_arbeit`, `--h-ocker`), gruen (`verifiziert`, `--h-olivgruen`). **Rot bleibt reserviert** fuer einen spaeteren expliziten Problem/Reject-Status -- bewusst Variante A, **E67-konform** (unverifiziert ist neutral, kein Alarm; literale rot/gelb/gruen-Ampel verworfen). Migration alt->neu (idempotent): `bearbeitet`->`in_arbeit`, `fertig`->`verifiziert`, `offen`->`unverifiziert` in `page_manifest.py` (`STATUS_MIGRATION`/`_migrate_streams`, inkl. History-`from`/`to`), `generate_edition_data.py` (Mirror-Lesen), `viewer.js` + `catalog.js` (`STATUS_LEGACY`). Timing ideal: alle 285 Docs standen auf `unverifiziert`, History leer -> **kein Datenverlust, keine Mirror-Regeneration noetig** (vorhandene `catalog.json`/Manifeste schon konform; verifiziert via Grep + Histogramm). Geaendert: 3 Python-Module, `viewer.js`/`catalog.js` (`STATUS_CYCLE`/`LABEL`/`LEGACY` + Tooltips), Status-Filter in `index.html` (4->3 Optionen), Pill-/Ampel-Farben + Kommentare in `viewer.css`/`catalog.css`. Neues Gate `tests/test_workflow_status.py` (5 Tests). Suite **520 -> 525 gruen**. [[E67]] bleibt gueltig (Reframing-Begruendung); seine 4-Stufen-Ampel-Tabelle ist durch E77 ueberholt

Dokumente: [quality.md](quality.md), [viewer.md](viewer.md)

### E78 — Viewer-Kuration: **ein** Speichern-Knopf statt drei Einzel-Downloads (2026-06-07)

User-Entscheidung: "ich will einen gemeinsamen Speichern-Button, und das darf kein Download sein, das muss an der richtigen Stelle im Repo abgelegt werden". Die drei Edit-Modi lieferten bisher je einen separaten Download (Layout ↓ / Text ↓ / Manifest ↓), den der Nutzer manuell ablegen musste. Neu: **ein "Speichern"** sichert alle ungespeicherten Stroeme als einen Akt -- Layout (Seite), Text bzw. TEI (Seite, je nach Quelle) UND das Manifest (Workflow-Status + Provenienz). Jeder Strom landet an seiner kanonischen Stelle im Repo (`saveAll()` in `viewer.js`, `persistSilent()` = FSA-mit-Download-Fallback). Die Einzel-Downloads wandern in ein **"Export ▾"**-Dropdown (Layout/Text/TEI/Manifest je einzeln). Weitere UI-Verdichtung: **Identity-Chip** (Bearbeiterkuerzel/ZBZ-Partner) neben dem Speichern-Knopf statt separatem Inline-Feld; **Seitennavigation** (prev/page-info/next) aus der Doc-Subbar in den **Faksimile-Panel-Header** verschoben (naeher am Bild, wo auch "X Regionen" steht); Edit-Toggles umbenannt **"Layout"/"Text" -> "Layout bearbeiten"/"Text bearbeiten"**; "Ordner verbinden" als eigener Menuepunkt **entfernt** -- die Repo-Verbindung passiert nur noch beim ersten Speichern (`connectWithInfo()`), mit **Erst-Info-Modal** (erklaert: Projekt-Wurzelordner `zbz-ocr-tei` waehlen, was geschrieben wird) und **Ordner-Plausibilitaetscheck** (`looksLikeRepoRoot`: warnt, wenn kein `docs/`+`scripts/`). Status-Tooltip am Speichern-Knopf ist zustandsabhaengig (was wird wohin gespeichert). [[E72]] (FSA-Schreibweg) bleibt die Grundlage; E78 ist die UI-Vereinheitlichung darueber

Dokumente: [viewer.md §Persistenz](viewer.md)

### E79 — Mirror-Write: Save spiegelt nach `docs/data/`, Viewer liest kuratiertes Layout zuerst (2026-06-07)

User-Bug: Layout bearbeitet, "Speichern", Reload -> Edit weg. Ursachenanalyse: der server-lose Viewer laeuft mit **Docroot=`docs/`** und liest beim Reload **ausschliesslich** aus `docs/data/` -- `output/` ist von dort nicht erreichbar. [[E72]] schrieb die Kuration aber nur nach `output/` (kanonisch, Pipeline-Konsum), also ueberlebte **kein** Edit (Layout/Text/Status) den Reload. Zweite Ursache: `fetchLayout` in `viewer.js` las nur `_layout_gemini.json`/`_layout.json`, **nie** `_layout_curated.json` (anders als die Pipeline `loaders.load_layout_gemini`, die curated zuerst liest). Fix zweiteilig: (a) **jeder FSA-Write spiegelt die identische Nutzlast zusaetzlich in den Mirror** (`fs-access.js`): Layout -> `docs/data/pages/{doc}/{doc}_p{NNN}_layout_curated.json`, Text -> `docs/data/pages/{doc}/{doc}_p{N}.md`, Manifest -> `docs/data/manifests/{doc}_manifest.json`, TEI-Final -> `docs/data/pages/{doc}/{doc}_final.xml`; der kanonische `output/`-Schrieb bleibt unveraendert. (b) **Viewer liest curated zuerst** -- neuer Pfad-Helfer `ZBZ.path.layoutCurated` (`core.js`), `fetchLayout` probiert `layoutCurated > gemini > docling` (analog Pipeline). `generate_edition_data --mirror-only` reproduziert exakt dieselben Mirror-Dateien (Layout via `_layout*.json`-Glob, Manifest via `mirror_manifests`) -> kein Drift. Caveat: Per-Seiten-TEI-Splits entstehen erst beim `--reassemble`; der Text-Mirror ueberschreibt die Mistral-Mirror-`.md` (Label "OCR · mistral" bleibt, Inhalt ist curated). Cache-Bust `core.js?v=2`/`fs-access.js?v=3`/`viewer.js?v=12`; node --check + HTTP-200 verifiziert

Dokumente: [viewer.md §Persistenz](viewer.md), [workflow.md §3](workflow.md)

### E80 — CER-Einordnung print-kalibriert: HTR-Baender schmeicheln, Headline an Print-Literatur verankert (2026-06-08)

User-Befund (Critical Expert): Das Korpus ist reiner **Druck**, kein HTR; die Transkribus-Qualitaetsbaender (<2 % exzellent / publikationsreif) stammen aber aus der Handschriften-Praxis und schmeicheln einer Druck-OCR-Aufgabe, wo die Messlatte hoeher liegt. Drift: Headline-Worte „exzellent/State-of-the-Art/publikationsreif" widersprachen dem eigenen, bereits vorhandenen Print-Literaturvergleich (Crosilla et al. 2025: bester Stack 0.84 %, Transkribus allein 3.67 %). Korrektur (keine Zahlenaenderung, nur Framing): Median 1.83 % = **solide, nicht SotA** (liegt zwischen 0.84 % und 3.67 %); SotA nur fuer beste Einzeldocs (0.3-0.8 %); CER misst zudem gegen eine selbst fehlerbehaftete Referenz (Doc 1440) und ist damit eine Obergrenze. Geaendert: `quality.md` (Headline-Block + Lesehilfe), `methode.html` (Baender-Absatz), `reports/2026-05-27_arbeitsbericht.md` (§6.3 Headline-Satz, jetzt mit Print-Vergleich)

Dokumente: [quality.md](quality.md), [methode.html](../docs/methode.html)

### E81 — Transkribus-Export + REST-Upload: PAGE-XML-Round-Trip in eine Collection (2026-06-08)

Die Stufe-4-PAGE-XML (`output/page_xml/`, Standard-PAGE 2013-07-15) ist verlustfrei nach Transkribus rueckspielbar -- fuer manuelle Nachkorrektur oder HTR-Training. Zwei Skripte in `scripts/edition/`: **`transkribus_export.py`** baut die Transkribus-Ordnerkonvention (`{doc}/` Bilder oben + gleichnamige PAGE-XML im `page/`-Unterordner) aus `page_xml/` + `docs/images/` nach `output/transkribus_upload/` (gitignored); Auswahl `--sample` (stratifiziert Seitenzahl x Sprache), `--all`, `--reference` (24 ZBZ-Overlap-Objekte), `--doc`; pro Seite verifiziert es PNG-Mass == deklariertes `imageWidth/Height` (Koordinaten alignt) und faehrt ueber die PAGE-XML statt die Bilder (Leerseiten ohne Layout bleiben aussen vor). **`transkribus_upload.py`** laedt die Bundles ueber die Legacy-TrpServer-REST-API (`transkribus.eu/TrpServer/rest`: `POST /auth/login` -> `POST /uploads?collId=` JSON-Manifest -> `PUT /uploads/{id}` Bild+XML je Seite). **Verifiziert 2026-06-08**: die Legacy-API schreibt korrekt in eine Collection der **neuen** Plattform (app.transkribus.org, colId 2426839 "zbz hersch"); Testobjekt doc 1500 erschien mit Layout-Regionen (heading/paragraph) + Text + Reading-Order. Auth ausschliesslich ueber Env-Vars (`TRANSKRIBUS_USER/PASSWORD/COLLECTION`), nie im Code/Repo/.env. Kein Dedup -- jeder Lauf legt neue Dokumente an, daher `--dry-run` + Testobjekt vor Vollupload. Dialekt-Caveat: Pipeline-PAGE hat Zeilen-Polygone, **keine Baselines** (Import/Anzeige ok, nur HTR-Training braucht sie). Abzugrenzen vom Viewer-Round-Trip ([[E72]]/[[E79]]): andere Richtung (Pipeline-Layout raus statt Edits rein)

Dokumente: [pipeline.md §Transkribus-Export](pipeline.md)

### E82 — Doc-30-Dedup publiziert + Korpus-Mean 3.99 % (vorher 4.26) + Tail-Ursachen-Register (2026-06-08)

Bei Doc 30 wurde ein OCR-**Block**duplikat (ein doppelt erfasster Absatz, in Mistral x2) entfernt; Fidelity-CER 18.25 -> 11.59 %, publiziert nach `tei_final/30` (revisionDesc erhalten) + Mirror `docs/data/pages/30/`. Dadurch Korpus-Mean Fidelity **4.26 -> 3.99 %** (CI [2.36; 5.96]), Median 1.83 % unveraendert; `cer_statistics.json` neu (Seed 42, B=10000). **4.26 entfaellt als aktuelle Zahl** (User-Entscheidung: nur der aktuelle/echte CER zaehlt); konsistent gezogen in `quality.md`, `methode.html`, `about.html`, `oekosystem-synthese.md`. Caveat: 3.99 = 24 Docs reines Pipeline-Output + 1 manuell entdupliziertes (Doc 30), weil **keine automatische Block-Deduplikation existiert** -- das in Arbeitsbericht Anhang A und CLAUDE.md referenzierte `scripts/ocr/ocr_dedup.py` ist NICHT im Repo (nur verwaiste `.pyc`); Doku-Drift, separat zu klaeren. Tail-Ursachen belegt + in Bericht 6.3 (25-Objekt-Tabelle) / 7 (Problem-Uebersicht): die hohen CER sind strukturell, NICHT Zeichenerkennung. **Offene Defekte registriert:** (a) Gemini-Layout-QA ueber-detektiert Fussnoten -> Body-als-`<note>` (290/1910/90), nicht sicher auto-fixbar wg. echter langer Fussnoten in 1520/40/3040; (b) Doppelseiten-Lesereihenfolge -- `match_paragraphs_to_regions` (tei_step1) sortiert nur nach y, ignoriert x + `reading_order` (30/760). [[E80]] (print-kalibriert) bleibt gueltig

Dokumente: [quality.md](quality.md), [reports/2026-05-27_arbeitsbericht.md](../reports/2026-05-27_arbeitsbericht.md)

### E83 — Code-Doku-Drift behoben; Header-Metadaten bleiben ZBZ-Domaene (E76/O8 bestaetigt) (2026-06-08)

User-Auftrag: "fixe den Code-Doku-Drift; baue nur das wirklich Sinnvolle". (a) **Doku-Drift behoben (bleibt):** pipeline.md `revisionDesc` auf Workflow-Status ([[E66]]/[[E77]]) statt altem "APPROVED"; toter Verweis `knowledge/TEI-MAPPING.md` im Mapping-Prompt -> Editionsrichtlinien + pipeline.md; Scope-Notiz im Mapping-Prompt (Step 2 liefert nur ein per-Seiten-`<div>`-Fragment, daher front/back/anchor/unclear NICHT automatisch erzeugbar); teiHeader-Kommentar "aus ALMA" -> ehrlich `doc_metadata.json`; `tei_unified`-Docstring "4-Stufen" -> "3 + Validierung"; Validator-Kommentar W1-W8 -> W1-W14. (b) **MMSID/Zitat-Header-Projektion testweise gebaut, dann nach Ruecksprache WIEDER VERWORFEN:** Katalog-Nummer + bibliografisches Zitat gehoeren nicht zu OCR/Layout/TEI-Inhalt, sondern sind Bibliotheks-/ZBZ-Domaene -- bestaetigt [[E76]]/[[O8]]. Der gebaute Masterfile-Leser (`scripts/core/masterfile.py`) + Header-Emission wurden in derselben Sitzung wieder entfernt; `build_tei_header` ist wieder wie vor der Sitzung. (Notiz fuer kuenftige Sitzungen: nicht erneut versuchen ohne ausdrueckliche ZBZ-Anforderung.) (c) **Bestaetigt:** front/back/anchor/unclear werden NICHT automatisch erzeugt (Datenquelle Freitext / zu selten / Bild-Urteil; Haeufigkeit in 25 GT: front 6, back 5, anchor 1, unclear 0, epigraph 1) -- bleiben Kuration; Widmungen/Paratext bewusst draussen (Editionsrichtlinien-Auslassungen). Suite gruen.

Dokumente: [pipeline.md](pipeline.md), [decisions.md](decisions.md)

### E84 — Konformitaets-Audit Pipeline vs Editionsrichtlinien + Welle-1/2-Generator-Fixes (implementiert, Deploy operator-gated) (2026-06-08)

Auftrag "arbeite zum naechsten Milestone": erschoepfender Abgleich der ausgelieferten TEI-Struktur gegen die Editionsrichtlinien als Multi-Agent-Workflow (126 Agenten, 62 Regeln, adversarisch verifiziert), Bericht `reports/tei-konformitaet-audit-welle1-2026-06-08.md`. **18 echte Generator-Defekte** belegt. **Korrektur:** `div type="text"` ist KEIN Verstoss (Orphan-Wrapper, gleichwertig + schema-valide) -- die zuvor (zaehl-Audit) behauptete Richtlinienwidrigkeit war falsch. **Welle 1 implementiert+getestet:** `_fix_div_n_type_exclusive` (entfernt @n von divs mit @type, 73 Faelle, GT hat 0), `_assign_figure_ids` (fortlaufende xml:id figN, 0/52 -> alle), head type="lemma" fuer encyclopedia (tei_step1). **Welle 2 teilweise:** `_wrap_first_title` (erste Dokument-`<head>` -> `<title type="main">`, 207/285 Docs), `_normalize_foreign_lang` (`<foreign xml:lang>` auf 639-2/B, de->deu, fre->fra). Alle als fehlertolerante Post-Assembly-Paesse in `tei_step3.assemble_document`, DRY ueber Helfer `_transform_tree`. **Validator W15-W18** (nicht-blockierend): div type+n, figure ohne xml:id, leerer speaker, foreign-Code. **sp-speaker-p (groesster Defekt, 62% leere speaker) bewusst NICHT umgebaut:** GT kodiert Sprecher via `<persName ref="GND:...">`, GND-Linking ist mit [[E71]] aus der Pipeline -> leeres `<speaker/>` ist Kurations-Slot (User-Entscheidung, E71-konsistent), kein Bug. Tests `tests/test_tei_conformance.py`; Suite 554 gruen. **Code-Review (2026-06-08, 39 Agenten, adversarisch):** drei CONFIRMED-Befunde -- `_wrap_first_title` ignoriert jetzt Bildunterschrift-Heads (nur Struktur-Heads unter div/body); `_normalize_foreign_lang` + W18 teilen eine Quelle `normalize_lang_code` in `tei_xml_utils` (639-2/T, deckungsgleich, kein duplizierter Varianten-Satz); figure-id-Ueberschreiben ist beabsichtigt (dokumentweite Neunummerierung, kein Guard). Vorbestands-Befund `debate`->`interview` vs `conversation` an Operator gereicht. **Deploy operator-gated:** Fixes wirken erst nach Korpus-Neugenerierung (`tei_unified --all --reassemble`), die wegen aktiver Kurations-Lanes (Fussnoten 1910/290/90) NICHT eigenmaechtig laeuft. **Welle-2-Rest klassifiziert (Workflow + Korpus-Messung 2026-06-08):** kein sicher-deterministischer Fix mehr -- footnote-inline-anchor + footnote-n = COLLISION (Fussnoten-Lane/CER), review-bibl = CURATION_SLOT (freie Bibliographie/GND, E71), pb-blank = ZBZ_BLOCKED (Pipeline `<pb type="blank"/>` widerspricht Richtlinie `<p>[Leer]</p>`), lb-break-no-hyphenation = NON-DEFEKT (0 echte Silbentrennungs-Faelle, 301 Strich-Zeilen sind Listen/Preise). Deterministisch-sichere Konformitaets-Flaeche damit ausgeschoepft. Welle 3/4 offen. reference_tei/1520.xml = kaputtes XML, an ZBZ

Dokumente: [reports/tei-konformitaet-audit-welle1-2026-06-08.md](../reports/tei-konformitaet-audit-welle1-2026-06-08.md), [pipeline.md](pipeline.md)

### E85 — Referenz-verifizierte Fussnoten-Demotion (3,99->2,71%) + #sup-Marker-Strip (Welle-2-Rest footnote-n) (2026-06-08)

Zwei referenz-belegte Fussnoten-Konformitaets-Korrekturen als idempotente, reversible Post-Paesse auf `tei_final` (gitignored, nach Neugenerierung re-applizierbar). **(a) Demotion (3,99->2,71%):** manche `<note place="foot">` trugen in Wahrheit Fliesstext (Gemini Stufe 6); steht ein zusammenhaengender >=150-Zeichen-Ausschnitt im GT-Body (Fussnoten ausgeschlossen, [[E5]]), ist der Block beweisbar Fliesstext -> nach `<p>` demotet. 14 Bloecke/5 Docs (290/1910/90 + nach Operator-Anweisung 40/1520). Korpus-Fidelity-Mean **3,99->2,71%**, Median 1,40%, micro 2,13%; Pipeline-Mehrwert ggue. reiner OCR dadurch signifikant (-9,45pp, p=0,013). Tool `tei_footnote_demote.py` (Backup, HOLD={40,1520}, --include-hold). **(b) #sup-Marker-Strip (Welle-2-Rest footnote-n):** fuehrender `<hi rendition="#sup">`-Druckmarker aus dem Notentext entfernt -- Editionsrichtlinie Z.354 (Marke nur via @n), 0/25 GT-Notes oeffnen mit Marker. 16 Notes/4 Docs (110/130/1140/1500), alle schema+regel-valide, CER-neutral. Tool `tei_footnote_marker_strip.py`. **Welle-2-Rest per Workflow klassifiziert** (10 Agenten, GT-gegruendet, adversarisch): footnote-n war [[E84]] als Fussnoten-Lane an diese Lane gepunktet und ist der einzige sichere Fix; inline-anchor (243/251 ohne Anker), review-bibl (GND-Linking verboten, [[feedback_no_llm_for_id_linking]]), pb-blank (110 wird schema-invalid -> ZBZ), lb-break-no (Rest = Preise/Komposita) evidenz-begruendet als Diagnose/Kuration/ZBZ verworfen -- 3 W19-Diagnose-Specs an die TEI-Struktur-Lane uebergeben. Tests: test_footnote_demote.py + test_footnote_marker_strip.py (14)

Dokumente: [quality.md](quality.md), [reports/welle2-rest-verifikation-2026-06-08.md](../reports/welle2-rest-verifikation-2026-06-08.md)

### E86 — Repo-Audit-Welle: Viewer-Datenverlust-Fix (H1) + CI-Gate + Doku-Konsistenz (2026-06-10)

Vier parallele Audits (Doku/Python/Frontend/Prozesse), Befunde in einer Welle umgesetzt. (a) **H1 behoben (Datenverlust):** der XML-Modus lud die per-Seiten-TEI, `writeTei` ueberschreibt aber `{doc}_final.xml` als Ganzes -- ein Seiten-Edit konnte das gesamte Dokument ersetzen. Fix: XML-Modus laedt das Gesamtdokument (`loadTeiFinal`), Save-Guard verweigert Inhalte ohne `teiHeader`/`TEI`-Wurzel, Session-Cache wird nach Save aktualisiert. Dazu H2 (Download-Fallback meldet sich ehrlich als Download), M2 (`pageLoadSeq` + stale-Guards gegen Seitenwechsel-Races), N4 (`destroyOsd()` vor Fehler-DOM), M4 (Titel-Spalte sortiert nach Titel), A11y H3/H5/M6/M7 (Layout-Editor auf Pointer-Events + Pfeiltasten-Nudge inkl. `touch-action:none`; Modal-Fokus-Trap/ESC/Fokus-Rueckgabe; Editor-ARIA `role=textbox`; dynamische Status-Pill-Labels), N5 (Token `--h-overlay`). Befund-Register [frontend-gaps.md](frontend-gaps.md) nachgezogen (10 behoben, offen: H4/M1/M3/M5/N1-N3/N6/N7). (b) **CI eingefuehrt:** `.github/workflows/tests.yml` (volle pytest-Suite bei Push/PR; datenabhaengige Tests skippen auf frischem Checkout) -- erste automatisierte Absicherung bei parallel committenden Instanzen. (c) **requirements.txt lauffaehig:** top-level importierte Pakete ergaenzt (`python-dotenv`, `numpy`, `scipy`, `pyspellchecker`), tote entfernt (`fastapi`, `uvicorn`, `jiwer`, `torchvision`, `transformers`, `accelerate`), `torch` als optional/lazy dokumentiert. (d) **Python-Hygiene:** `ExitStack` in `transkribus_upload.put_page` (Handle-Leak bei fehlgeschlagenem zweiten `open()`), with-Block fuer `_selection.json` in `transkribus_export`. (e) **Doku-Konsistenz:** stale CER-Headline (4,26 %/1,83 %) in README, methode.html, about.html, oekosystem-synthese.md, index.md auf kanonisch **2,71 %/1,40 %** (CI [1,77; 3,82]) gezogen, Paired-Mehrwert -9,45 pp p=0,013 nachgefuehrt; CLAUDE.md fuehrt 12 statt 10 Knowledge-Docs; E-Range E1-E85; E54 als historisch markiert. Code-Kommentar-Konvention ab jetzt: kompakt, englisch, nur wo noetig. Suite 563 gruen, node --check sauber

Dokumente: [frontend-gaps.md](frontend-gaps.md), [viewer.md](viewer.md)

### E87 — `zbz_hersch.rng` um teiCrafter-standOff-Register + `name`-Mentions erweitert (2026-06-21)

> **Ueberholt durch [[E88]] (2026-06-21).** Das am selben Tag uebergebene ZBZ-Material
> hat das Auszeichnungsmodell zugunsten Inline-GND entschieden; das standOff-Register ist
> fuer die Auslieferung gegenstandslos und wurde aus dem aktiven Schema wieder entfernt.
> Der Eintrag bleibt als Herleitung stehen.

Der Kurations-Editor teiCrafter schreibt beim Annotieren ein `<standOff>`-Register
(`listPerson`/`listPlace`/`listOrg`/`listEvent`/`listBibl` mit `person`/`place`/`org`/
`event`/`bibl`, je ein Namens-Element plus optionale Normdaten als `<idno type="GND|GeoNames|Wikidata">`),
eine editoriale `<note target="#id">`, einen `<respStmt xml:id="ai">` mit `<name>AI</name>`
und In-Text-Mentions `<name ref="#id">`; AI-vorgeschlagene, noch nicht menschlich
gepruefte Eintraege tragen `resp="#ai"` (Datenvertrag exakt aus `ResearchTools/teiCrafter`,
`docs/js/editor/standoff.js`). Das ODD-Subset (E48) hatte `standOff` samt aller
Register-Elemente und das generische `<name>` weggelassen, weil die Pipeline sie nie
erzeugt; seit [[E71]] ist das ausgelieferte TEI entitaetenfrei. Folge: ein im teiCrafter
kuratiertes ZBZ-Dokument war gegen sein eigenes Schema invalide, obwohl `{id}_final.xml`
teiCrafters natives Format ist.

Fix nach Muster [[E68]] (Inhaltsmodelle minimal am real erzeugten Datenvertrag,
verdrahtet an die bestehenden TEI-Klassen): `tei_standOff` in `tei_model.resource`
gehaengt (kanonischer `model.resourceLike`-Slot neben `text`/`facsimile`), `tei_name`
in `tei_model.nameLike.agent` (deckt in einem Zug die Inline-Mentions in `<p>`/`<head>`/`<l>`
und das `<name>AI</name>` im `respStmt` ab). Elf neue Element-Defines (`standOff`,
`listPerson`/`listPlace`/`listOrg`/`listEvent`, `person`/`place`/`org`/`event`, `label`,
`name`) plus ein dediziertes `tei_standOff.listBibl`/`tei_standOff.bibl`, weil das
geteilte ODD-reduzierte `tei_bibl` (teiHeader/Body) weder `<title>` noch `@resp` zulaesst
und unangetastet bleiben soll. `@resp`/`@ref`/`@target` reiten auf den schon vorhandenen
Klassen `att.global.responsibility`/`att.canonical`/`att.pointing`; keine neue
Attribut-Definition noetig. `standOff` als `zeroOrMore` der Listen modelliert, damit ein
verlustfrei editiertes, transient leeres Register nicht invalidiert.

Verifiziert: Schema kompiliert; synthetisches teiCrafter-kuratiertes Dokument (alle
Strukturen) valide; **285/285 `tei_final` weiterhin valide, keine Regression**; neues
git-getracktes Gate `test_schema_accepts_teicrafter_standoff` haelt die Erweiterung fest,
Suite gruen.

Faksimile-Anbindung (geprueft, Entscheidung offen, siehe [[O25]]): die Pipeline erzeugt
`<facsimile>`/`<surface ulx uly lrx lry>`/`<zone>` und die `@facs`-Bindung bereits
selbst und vollstaendig; was fehlt, ist der Surface->Bild-Zeiger `<graphic url>` im
Normalfall (zonenbehaftete Seite) -- nur der Leerseiten-Zweig in `build_facsimile`
([tei_step3.py](../scripts/tei/tei_step3.py) Z. 117) schreibt einen blossen Dateinamen
`{seite}.png`. Den dauerhaften Einbau leistet ein `<graphic>` als erstes `<surface>`-Kind
(Schema verlangt graphic vor zone, verifiziert); das macht das Faksimile selbst-enthaltend
und loest teiCrafters hartcodierten Demo-Bildpfad ab. Offen bleibt das URL-Schema
(relativ `<id>_p{KKK}.png` vs. absolute GitHub-Pages-URL vs. IIIF) und dass der Einbau
alle 285 `tei_final` (SoT) neu schreibt -- beides operator-gated.

Offen (Richtlinien-Konformitaet, siehe [[O26]]): E87 richtet sich am teiCrafter-Datenvertrag
aus, nicht an den ZBZ-Editionsrichtlinien (E49). Die Richtlinien fordern Inline-Auszeichnung
am Erwaehnungsort (`<persName ref="GND:...">`/`<orgName>`/`<bibl>`, alle `@ref` auf die GND),
nicht ein standOff-Register mit `<name ref="#id">` und GND als `<idno>`. E87 macht das
Tool-Modell valide, ohne zu entscheiden, ob es das Liefermodell ist; beide Modelle sind jetzt
schema-erlaubt. Welches gilt, ist ZBZ-/Operator-Sache.

Dokumente: [quality.md](quality.md), [pipeline.md](pipeline.md)

### E88 — Inline-GND als maßgebliches Auszeichnungsmodell; standOff (E87) aus dem aktiven Schema entfernt (2026-06-21)

Loest [[O26]]. Das von ZBZ uebergebene Material (`data/source/zbz-lieferung-2026-06-21/`,
README = vollstaendige Editionsrichtlinie, `zbz_hersch.rng` = ZBZ-Pruefvorlage) entscheidet
das Auszeichnungsmodell: Personen, Organisationen und Werke werden **inline an der
Erwaehnungsstelle** ausgezeichnet, jede Nennung mit `ref="GND:..."` auf die GND, kein
separates Register. Belegstellen der README: `<persName ref="GND:118815679">Hersch</persName>`,
`<orgName ref="GND:1010450-1">Universitaet Genf</orgName>`, `<bibl ref="GND:1088036961">L'etre
et la forme</bibl>`; nur Person/Organisation/Werk, keine Orte/Events, keine GeoNames/Wikidata,
keine Auszeichnung in Bildunterschriften. Die ZBZ-Pruefvorlage kennt kein `standOff`. Order
der Forschungsleitstelle (2026-06-21): nur die ZBZ-Editionsregeln gelten.

Schema-Konsequenz: das standOff-Register aus [[E87]] ist fuer die Auslieferung gegenstandslos
und wurde aus dem aktiven `data/schema/zbz_hersch.rng` wieder entfernt: die elf E87-Defines
(`standOff`, `listPerson`/`listPlace`/`listOrg`/`listEvent`, `person`/`place`/`org`/`event`,
`label`, `name`) samt `tei_standOff.listBibl`/`tei_standOff.bibl`, der `tei_standOff`-Ref in
`tei_model.resource` und der `tei_name`-Ref in `tei_model.nameLike.agent`. Zusaetzlich die drei
`@ref`-Pattern von `(GND:...|#zbz-...)` auf `GND:...` verengt (Inline-GND-only, keine internen
Register-Verweise). Die E68-Kopf-Elemente (revisionDesc/change, langUsage/language, idno,
monogr/imprint) bleiben erhalten. Damit ist das aktive Schema **exakt die ZBZ-Pruefvorlage plus
E68**; der vollstaendige Diff zwischen beiden besteht nur noch aus den E68-Elementen
(verifiziert). Begruendung fuer additiv-minus-E87 statt roher Schema-Uebernahme: die ZBZ-Vorlage
ist aelter als der Repo-Stand, ihr fehlen die E68-Kopf-Elemente, die die Pipeline regulaer
erzeugt (revisionDesc/langUsage/idno in allen 285); eine rohe Uebernahme wuerde alle 285
invalidieren (Widerspruch im ZBZ-Material, das im Header `idno`/Metadaten fordert, vgl. [[O8]]).

Verifiziert: Schema kompiliert; Inline-GND-Dokument (persName/orgName/bibl mit GND) valide;
standOff-Dokument jetzt **abgelehnt** (neuer Guard `test_schema_rejects_standoff_register`);
neuer Positiv-Test `test_schema_accepts_inline_gnd`; **285/285 `tei_final` weiterhin valide**
(der ausgelieferte Bestand ist seit [[E71]] entitaetenfrei, daher keine Migration noetig);
Suite gruen (289). Der frueher hinzugefuegte Test `test_schema_accepts_teicrafter_standoff`
ist durch die beiden neuen ersetzt.

Wirkung auf teiCrafter (lane teicrafter-editor): der Editor erzeugt bisher standOff; sein
Ausgabemodell ist an Inline-GND anzugleichen, damit sein `{id}_final.xml` gegen das
maßgebliche Schema valide bleibt. Nur-lesend aus dieser Lane beruehrt, keine Schreibzugriffe
ausserhalb von zbz-ocr-tei; als Delta an die Forschungsleitstelle gemeldet.

Dokumente: [quality.md](quality.md), [pipeline.md](pipeline.md), [index.md](index.md)

---

## Offene Punkte

| # | Frage | Kontext | Blockiert | Klaerung |
|---|---|---|---|---|
| O8 | Metadaten aus ALMA/MMSID | ID + MMSID + PubForm im `teiHeader` (laut ZBZ-Editionsrichtlinien) | Phase 3 TEI | **offen, an ZBZ (Stand 2026-06-08, [[E76]]/[[E83]] bestaetigt):** Header-Metadaten aus Alma (inkl. MMSID) gelten als ZBZ-Domaene und gehoeren nicht in die OCR/Layout/TEI-Pipeline. Eine MMSID-Projektion wurde mit [[E69]] eingefuehrt, mit [[E76]] entfernt und mit [[E83]] erneut verworfen. Achtung Spec-Konflikt: die Editionsrichtlinien (`data/source/guidelines/Editionsrichtlinien_ZBZ.md`, E49) fordern ID+MMSID+PubForm im Header; mit ZBZ zu klaeren (wer zieht aus Alma, welche Felder). **Entscheider: ZBZ gemeinsam mit DHCraft.** Solange offen, tragen 195/285 ausgelieferte Header einen leeren Container-Titel (beabsichtigt, kein Defekt) |
| O13 | TEI-Editorial-Details (Schlagworte) | wer erstellt diese? Im Header? Richtlinien: "in Abklaerung" | Phase 3 TEI | **Entscheider: ZBZ** (Richtlinien selbst sagen "in Abklaerung"). Haengt ab von der ZBZ-internen Festlegung, wer Schlagworte vergibt und wo sie im Header stehen. Solange bleiben die Header ohne Schlagworte; kein Pipeline-Blocker |
| O18 | multimodale LLM-Korrektur testen (Scan-Bild + OCR-Text) | Forschung: <1% CER (Crosilla 2025). Infrastruktur steht | Quality | **Entscheider: DHCraft (Projektleitung)**, eigener Test. Haengt ab von Priorisierung nach der ZBZ-Abnahme; blockiert nichts (reines Verbesserungs-Experiment auf der bestehenden Gemini-Infrastruktur), [quality.md](quality.md) |
| O25 | Faksimile-`<graphic url>` pipeline-seitig erzeugen statt nachgelagert via teiCrafter | Die Pipeline erzeugt `surface`/`zone`/`@facs` schon selbst ([[E87]]); nur der Surface->Bild-Zeiger `<graphic>` fehlt im Normalfall. Einbau = `<graphic>` als erstes `<surface>`-Kind in `build_facsimile` (`tei_step3.py`), Schema valide (graphic vor zone). | macht Faksimile selbst-enthaltend, loest teiCrafter-Demo-Bildpfad ab | **Entscheider: DHCraft (Projektleitung).** Offen: URL-Schema (relativ `<id>_p{KKK}.png` vs. absolute GitHub-Pages-URL vs. IIIF) und dass der Einbau alle 285 `tei_final` (SoT) neu schreibt. Kein Blocker, reine Pipeline-Erweiterung |
| ~~O26~~ | teiCrafter-Annotationsmodell vs. ZBZ-Editionsrichtlinien — **GEKLAERT (2026-06-21, [[E88]])** | Die Richtlinien fordern Inline `<persName ref="GND:...">`/`<orgName>`/`<bibl>` am Erwaehnungsort (alle `@ref` auf die GND); E87 hatte zusaetzlich ein standOff-Register schema-erlaubt gemacht. | — | Order der Forschungsleitstelle (2026-06-21): nur die ZBZ-Editionsregeln gelten, Inline-GND ist das Liefermodell. Umgesetzt in [[E88]]: standOff aus dem aktiven Schema entfernt, `@ref` auf GND-only verengt, aktives Schema = ZBZ-Pruefvorlage + E68; 285/285 valide, Guard-Test gegen Wiedereinzug. teiCrafter-Ausgabemodell ist anzugleichen (Delta an Leitstelle gemeldet) |
| ~~O22~~ | 289 vs 286 PDF-Diskrepanz — **GEKLAERT** (2026-05-27) | Masterfile hat 325 Texte, davon 289 `digitalisiert`, davon 286 als PDF geliefert; die 3 nicht gelieferten: `1745`, `1750`, `1970`. Verifiziert via `python -m scripts.eval.corpus_audit` | — | erledigt |
| ~~O23~~ | `tei_final`-Header nicht schema-valide — **GEKLAERT (2026-05-27, E68)** | Diagnose bei E65 nannte nur `<idno>`; die korpusweite Validierung zeigte vier Ursachen (`idno`, `langUsage`, `revisionDesc`/`change`, `biblStruct/monogr`), alle vom ODD-Subset weggelassen. Behoben durch Schema-Erweiterung E68; alle 285 ausgelieferten TEI valide; gegen Regression abgesichert durch `tests/test_tei_schema.py`. | — | erledigt |
| ~~O24~~ | `tei_validator --compare-ref` zeigt falschen Referenz-CER — **GEKLAERT (2026-05-27, E69)** | `compute_cer`-Import schlug still fehl (Funktion heisst `calculate_cer`), Validator fiel auf Laengen-Approximation zurueck. Fix: `calculate_cer` * 100 (Ratio->Prozent, passend zur Report-Formatierung), `except` auf `ImportError` verengt. Gate `tests/test_tei_validator.py`. | — | erledigt |

### Stabilitaet (LLM-Non-Determinismus, pending User-Entscheidung)

- (a) **Stabilitaets-Pilot:** 5 Docs × 3 Pipeline-Re-Runs, Std-Dev der Per-Doc-CER. Aktuell `stability.status: open` im JSON.
- (b) **Inter-Engine-CER:** zweiter OCR-Run mit anderer Engine als Cross-Validation. Mittlerer Aufwand.

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
| R3 | GND-Halluzinationen | mittel | — | hinfaellig (E71: NER entfernt) |
| R5 | Fork-Divergenz DHCraft vs ZBZ | mittel | Merge-Strategie + CI-Tests definieren | offen |
| R7 | Transkribus-Inkompatibilitaet PAGE-XML | hoch | Schema 2013-07-15, ID-Schema `{NNNN}_p{NNN}`, JPG. `@type`/`@custom` nicht verifizierbar (leere TextRegions) | teilweise geklaert (E23) |
| R10 | NER-Qualitaet auf Franzoesisch (66% Korpus) | mittel | — | hinfaellig (E71: NER entfernt) |

---

## Verweise

- [projekt.md](projekt.md) — Meilensteine + Status
- [pipeline.md](pipeline.md) — Pipeline-Entscheidungen
- [workflow.md](workflow.md) — End-to-End-Workflow, Round-Trip, Save-Mechanismus, Provenance-Konzept
- [viewer.md](viewer.md) — Edition + Curation (E33, E36, E42, E56, E57, E58, E59, E60, E61, E62, E63)
- [quality.md](quality.md) — CER + Screening (E41-E47, E51, E54/E55)
- [journal.md](journal.md) — chronologische Sitzungs-Historie
