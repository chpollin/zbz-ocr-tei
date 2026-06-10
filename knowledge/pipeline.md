---
type: knowledge
created: 2026-01-29
updated: 2026-05-25
tags: [zbz-ocr-tei, pipeline, ocr, layout, tei, engines]
status: active
---

# Pipeline

Datenfluss von PDF zu TEI-XML: Stufen, Skripte, Engines, TEI-Mapping. Seit der Scope-Expansion
(25.02.2026, E21) umfasst zbz-ocr-tei den gesamten Weg.

CLI-Referenz und operative Werkzeuge: [methodik.md §Commands](methodik.md).
Status pro Stufe: [projekt.md](projekt.md).
Vollstaendiger End-to-End-Workflow mit Round-Trip-Logik, Save-Mechanismus und
Provenance-Konzept: [workflow.md](workflow.md).

---

## Uebersicht

```
PDF
 │
 ▼
Bilder (extract_pages.py)
 │
 ├──────────────────────────────┐
 ▼                              ▼
OCR (Mistral)                  Layout (Docling + Gemini-QA)
 │                              │
 │                              ├──► PAGE-XML (page_xml_generator.py)
 │                              │    = paralleler Export fuer coOCR
 │                              │    NICHT TEI-Input (E22)
 │                              │
 └──────────────────────────────┴──► TEI-XML (tei_unified.py)
                                     │
                                     ▼
                                     Workflow-Status pro Strom (E66, menschgesetzt)
                                     │
                                     ▼
                                     Evaluation + Viewer
```

**Wichtig (E22, oft missverstanden):** PAGE-XML ist KEIN Zwischenschritt fuer
TEI. TEI wird DIREKT aus Layout-JSON + OCR-Markdown via
`scripts/tei/tei_unified.py` generiert. PAGE-XML wird parallel als Export fuer
coOCR / Transkribus erzeugt (E13). Beide leiten sich unabhaengig voneinander
aus Layout-JSON + OCR ab.

| Stufe | Aufgabe | Skript | Output | Status |
|---|---|---|---|---|
| 1 | PDF → PNG | `scripts/edition/extract_pages.py` | PNG (`docs/images/`) | Production |
| 1a | Dokumentklassifikation (Gemini) | `scripts/ocr/classify_docs.py` | `data/doc_metadata.json` + `output/classification/` | Production (285 docs, E27) |
| 2 | OCR | `scripts/ocr/ocr_pipeline.py` (`-e mistral` Basis, `-e gemini` opt-in Vision-OCR) | Page-Markdown (`output/mistral_results/`) | Production |
| 2a | LLM-Postkorrektur (optional) | `scripts/ocr/llm_postprocess.py` | `output/llm_corrected_c/` | Production, E17: optional |
| 2b | Gemini OCR-Korrektur (optional) | `scripts/ocr/gemini_ocr_correct.py` | `output/gemini_corrected_a/` / `_b/` | Sample (E29) |
| 3 | Layout-Analyse | `scripts/layout/run_layout_analysis.py` (local GPU) oder `run_layout_cloud.py` (docling-serve) | Regionen + BBox (`output/layout/`) | Production |
| 3a | Layout-QA/Detect (Gemini) | `scripts/layout/layout_qa_gemini.py --mode {qa\|detect\|auto}` | `_layout_gemini.json` | Production (E25/E26/E31) |
| 3b | Overlay-Generator | `scripts/layout/generate_layout_overlays.py` | PNGs + side-by-side compare | Production |
| 4 | PAGE-XML + METS | `scripts/layout/page_xml_generator.py` + `mets_generator.py` | `output/page_xml/` | Production |
| 5 | TEI-XML (regelbasiert) | `scripts/tei/tei_generator.py` | `output/tei/` | Production |
| 5b | **Unified TEI Pipeline** (E32) | `scripts/tei/tei_unified.py` | `output/tei_unified/` | **285/285** |
| 5b+ | Post-Assembly Fixes | `tei_step3.py` | Fixes E/F/G + heuristische lb-Injection | Production (Session 34) |
| 5c | TEI Validation | `scripts/tei/tei_validator.py` | JSON + HTML-Report | **285/285 valide**, 29 Warnings |
| 6 | Evaluation | `scripts/eval/evaluate_ocr.py` + `benchmark_cer.py` + `cer_statistics_full.py` | `output/evaluation/` + `docs/data/cer_statistics.json` | Production |

**Manuelle Kuration (E56, Stand 2026-04-27):** Erfolgt im Pipeline-Viewer
(`docs/viewer.html`) mit Layout- und Transkriptions-Editor. Aenderungen werden als JSON/MD/XML
heruntergeladen und manuell im Repo abgelegt. Details: [viewer.md](viewer.md).
Frueher (E36): FastAPI Curation Server unter localhost:8000 — abgeschafft.

**Qualitaetssicherung (E66):** Das fruehere Agent-Screening ist abgeschafft (kein Mensch hatte die
„APPROVED" vergeben — der Agent zertifizierte sich selbst). Ersatz: menschgesetzter
**Workflow-Status pro Strom** (`unverifiziert | in_arbeit | verifiziert` je OCR/Layout/TEI, drei Stufen seit E77),
im Viewer gesetzt, History im Pro-Objekt-Manifest, Projektion in den `<revisionDesc>`. Stand:
285/285 `unverifiziert`. Details: [quality.md §Workflow-Status](quality.md).

---

## Engines

Aktive Engines in zwei Rollen. Modellwahl ist weniger entscheidend als Pipeline-Design:
Pipeline-Investitionen lohnen sich (Chunking,
Page-Matching, Quality-Routing). API-Kosten vernachlaessigbar.
LLM-Postkorrektur schadet bei CER <5% (E17).

### Mistral Document AI — OCR Production

| Aspekt | Details |
|---|---|
| Modell | `mistral-document-ai-2512` auf Azure AI Foundry (Serverless API) |
| Rolle | Primary OCR Engine fuer ZBZ-Production |
| Speed | ~1.3 s/Seite |
| Output | Per-Seite Markdown (`output/mistral_results/{doc_id}_p{N}.md`) |
| Sprachen | 36 (de, fr, en, es, it, ...) |
| Endpoint | `https://<deployment>.<region>.models.ai.azure.com/v1/ocr` |
| Limit | 30 Seiten/Request, 30 MB max (Pipeline splittet automatisch) |

Setup-Hinweise und Fehler-Diagnose: [infrastruktur.md](infrastruktur.md) §Azure.

### Docling 2.75 — Layout Primary

| Aspekt | Details |
|---|---|
| Modell | RT-DETR V2 Heron (42.9M, IBM Research, DocLayNet) |
| Rolle | Primary Layout Engine (nur Layout, kein OCR — RapidOCR hat FR-Encoding-Probleme) |
| Speed | ~5 s/Seite (RTX 4060 GPU), ~27 s/Seite (CPU / docling-serve) |
| Erkennung | 17 Block-Typen (Title, Section-header, Text, Footnote, Caption, Page-header/footer, Picture, Table, Formula, ...) |
| API | `scripts/layout/run_layout_cloud.py` → docling-serve (Docker, IBM offiziell) |

Coverage-basiertes Quality-Scoring ist ein starker Proxy fuer Layout-Qualitaet — kein ML noetig.
Landscape/multi-column sind die harten Faelle (~64% bad vs. ~14% Portrait).

### Gemini 3.1 Flash Lite — Layout-QA + Detect + Refinement

| Aspekt | Details |
|---|---|
| Modell | `gemini-3.1-flash-lite-preview` |
| Rollen | Layout-Korrektur, Layout-Detect (Fallback fuer Docling-Failures, ~15%), Dokumentklassifikation, OCR-Korrektur, Vision-OCR (opt-in `-e gemini`, Ausnahme-Ersatz fuer Mistral, schreibt nach `output/mistral_results/`), TEI-Refinement |
| SDK | `google-genai` |

3 Modi in `layout_qa_gemini.py`:
- `--mode qa` — Overlay-PNG + Layout-JSON → Gemini, Labels korrigiert, False Positives entfernt, Quality-Score 0-100
- `--mode detect` — Full Re-Detection mit `box_2d`-Koordinaten (0-1000 Scale → x_pct/y_pct/w_pct/h_pct)
- `--mode auto` — routet pro Seite via `compute_page_quality()` (detect fuer bad/empty, qa fuer good/warning)

Strukturierte Outputs via `response_schema`. Beide Versionen bleiben erhalten (`_layout.json` + `_layout_gemini.json`) — in DH ist Provenienz so wichtig wie Qualitaet.

### Architektur-Entscheidung (E19/E20)

Anforderungen: strukturelle Erkennung, BBox, FR/DE, PAGE-XML 2013-07-15.
Evaluiert (25.02.2026): Gemini, Claude, Mistral (fuer Layout), Docling, Surya, Kraken, Azure Document Intelligence.

**Entscheidung:** Docling + Gemini hybrid. Docling = bester Open-Source-BBox (mAP 0.699, 17 Klassen, free, CPU-faehig).
Gemini = QA-Validator + Detect-Fallback. Claude = nicht fuer Layout (keine BBox), aber wertvoll fuer TEI. Mistral = bleibt Text-Engine.

Fallback: Kraken (native PAGE-XML, historische FR). `ocr-fileformat` (UB Mannheim) konvertiert
zwischen 30+ Formaten (hOCR, PAGE-XML, ALTO, TEI).

---

## TEI-Mapping (DTA-Basisformat + ZBZ-Anpassungen)

Transformationsregeln aus dem Quelltext zu TEI-XML nach DTA-Basisformat mit projektspezifischen
Erweiterungen. Verbindlich seit E48/E49 (2026-03-26).

**Quellen:**
- `data/source/guidelines/Editionsrichtlinien_ZBZ.md` — verbindliche Editionsrichtlinien
- DTA-Basisformat — externer Standard, verlinkt in [data/source/guidelines/README.md](../data/source/guidelines/README.md) (deutschestextarchiv.de)
- `data/schema/zbz_hersch.rng` — projektspezifisches RelaxNG-Schema (TEI P5 v4.10.2)

### Kernprinzipien

1. Vorlagengetreue Lesetext-Transkription mit Index-Annotation
2. DTA-Basisformat als Fundament + projektspezifische Anpassungen
3. Definierte Normalisierungen (keine diplomatische Transkription)
4. Quelltreue Transkription

### Dokumentstruktur

```xml
<?xml version='1.0' encoding='UTF-8'?>
<TEI xmlns='http://www.tei-c.org/ns/1.0' type="naegeli">
  <teiHeader><!-- aus doc_metadata.json via build_tei_header; Alma-Metadaten (MMSID) = ZBZ-Domaene, O8 --></teiHeader>
  <text>
    <front><!-- optional: Vorworte, Widmungen --></front>
    <body>
      <pb facs="#f0001" n="1"/>  <!-- erste pb VOR div n="1" -->
      <div n="1"><!-- Hauptstruktur --></div>
    </body>
    <back><!-- optional: Uebersetzungen, Nachdrucke --></back>
  </text>
</TEI>
```

| Ebene | Element | Verwendung |
|---|---|---|
| 1 | `<div n="1">` | Hauptkapitel |
| 2 | `<div n="2">` | Unterkapitel |
| 3 | `<div n="3">` | Abschnitt |

`<pb>` steht **innerhalb** von `<div>`.

### Zeichennormalisierung (E49 verbindlich)

| Quellzeichen | Zielzeichen | Unicode | Regel |
|---|---|---|---|
| Gedanken/Spiegelstriche, von-bis | Halbgeviertstrich `–` | U+2013 | alle horizontalen ausser Trenn/Bindestrich |
| Trenn/Bindestriche | Viertelgeviertstrich `‐` | U+2010 | Worttrennungen, Komposita |
| Anfuehrungszeichen | `"`/`"` | U+201C / U+201D | typografisch |
| einfache Anfuehrungszeichen | `'`/`'` | U+2018 / U+2019 | typografisch |
| Apostrophe | `'` | U+2019 | `l'homme` |
| nicht darstellbare Zeichen | `~` (Tilde) | U+007E | Platzhalter |

Whitespace: Vor `:`, `;`, `?`, `!` und Anfuehrungszeichen Leerzeichen loeschen. Aufzaehlungen
mit Trennstrichen normalisieren zu `/` (Zuerich/Bern/Basel). Beibehalten: `ß` (U+00DF),
Klammern wie Vorlage, Akzente, Ligaturen.

### Seitenstruktur

```xml
<pb facs="#f0001" n="1"/>
<pb facs="#f0002" n="2"/>
<pb facs="#f0003" n="[3]"/>  <!-- Seitennummer nicht gedruckt -->
```

- `facs` = Referenz auf Digitalisat (`#f` + Digitalisierungsnummer)
- `n` = gedruckte Seitennummer, `[Nummer]` bei fehlender Nummer
- pb steht **am Anfang der Seite**, erste pb VOR `<div n="1">`

Zeilenumbrueche (`<lb>`) werden auf Datenebene erhalten (nicht im Frontend angezeigt).
Heuristische lb-Injection (Fix-002, Session 34): ~60 Zeichen an Wortgrenzen.

### Highlighting

| Rendering | TEI | Beispiel |
|---|---|---|
| Bold | `<hi rendition="#b">` | `<hi rendition="#b">wichtig</hi>` |
| Italic | `<hi rendition="#i">` | `<hi rendition="#i">Philosophie</hi>` |
| Underline | `<hi rendition="#u">` | |
| Spaced | `<hi rendition="#g">` | |
| Small caps | `<hi rendition="#k">` | |
| Superscript | `<hi rendition="#sup">` | |
| Subscript | `<hi rendition="#sub">` | |

Nur semantisch relevantes Highlighting wird kodiert.

### Spezielle Strukturen

- **Sprachwechsel:** `<foreign xml:lang="deu">...</foreign>` (ISO 639-3: `fra`, `deu`, `eng`, `ita`, `lat`)
- **Fussnoten:** `<note place="foot" n="1" xml:id="fn{Seite}-{Nr}">...</note>` mit `next`/`prev` bei Mehrseitigkeit
- **Druckfehler:** `<choice><sic>Eclairement</sic><corr>Eclairement</corr></choice>`
- **Unleserlich:** `<unclear cert="high\|low">...</unclear>`
- **Marginalien:** `<note place="left\|right">...</note>`
- **Leere Seiten:** `<pb .../><p>[Leer]</p>`

### Entitaeten

Named-Entity-Auszeichnung wurde mit **E71 (2026-05-27) entfernt** (siehe [decisions.md](decisions.md)):
Die Verlinkung war im ausgelieferten TEI nicht funktionsfaehig (~2.6% der Erwaehnungen mit echter
GND-ID, Rest `GND:unknown` oder interne IDs). `<persName>`, `<orgName>`, `<placeName>` werden nicht
mehr getaggt. `<bibl>` bleibt ausschliesslich als bibliografische Struktur erhalten (Literaturlisten
in `<listBibl>`, Review-Zitation im `<head>`), ohne `ref`/`corresp`.

### Kuration statt Automatik: front/back/anchor/unclear (Stand 2026-06-08)

Die Pipeline erzeugt pro Seite ein `<div>`-Body-Fragment (Step 2, OUTPUT FORMAT in
`tei_mapping_prompt.py`). Dokument- und seitenuebergreifende Strukturen entstehen daher
NICHT automatisch — sie werden in der Kuration (Viewer) gesetzt. Begruendung je Fall (mit
Haeufigkeit in den 25 Referenz-TEIs):

- **`<front>`/`<back>`** (Widmung, redaktionelle Hinweise; Uebersetzung/Nachdruck/otherEdition;
  front 6/25, back 5/25): Dokumentebene. Die Nachspann-Quelle im Masterfile (Spalte
  "Anmerkungen") ist **Freitext** ("deutsche Uebersetzung: ID 320", teils nur interne
  Verweise) — kein verlaessliches Zitat, daher bewusst **kein Auto-Bau** (sonst falsches TEI).
  Nachspann-Zitation nach MLA 9 + Swisscovery-Link bleibt ZBZ/Kuration.
- **seitenuebergreifende `<anchor>`** (Doppelseiten-Abbildung, 1/25): braucht beide Seiten,
  zu selten + zu fehleranfaellig fuer Automatik.
- **`<unclear>`** (0/25): Urteil pro Zeichen am Scan-Bild; nur Kuration.
- **`<epigraph>`** (1/25): wird uebernommen, wenn die KI es am div-Anfang setzt; ein
  fehlplatziertes Motto entpackt `tei_step2._fix_structural_issues`.

### Spezielle Dokumenttypen

- `<div type="review">` mit `<bibl>` im `<head>`
- `<div type="interview">` mit `<sp>/<speaker>` (E47: `essay` → `text`)
- `<div type="conversation">` fuer Gespraechsrunden
- `<div type="entry">` fuer Enzyklopaedie-Eintraege, mit `<div type="bibliography">/<listBibl>`
- `<ab type="redactional" hand="xy">` fuer redaktionelle Texte (nicht von Hersch)

Paratexte: `<front>` (`editorial`, `dedication`), `<back>` (`translation`, `reprint`, `otherEdition`).
Zitierung in `<back>` nach MLA 9, mit Swisscovery-Permalink als `<ref target="...">`.

### Figures

```xml
<figure xml:id="fig1">
  <graphic url="..\..\images\fig1.tif"/>
  <head>[optional]</head>
  <p>[optional Erlaeuterung]</p>
</figure>
```

- `xml:id` auf `<figure>` (nicht `<graphic>`), fortlaufend
- `<figure>` ist immer eigenstaendiger Block, nicht in `<p>`
- Doppelseitige Abbildungen: `<anchor xml:id="figN-start/end"/>` markiert Spannweite

### Auslassungen

| Auslassung | Notiz |
|---|---|
| Titelseiten | ausser bei Monografien |
| Curriculum Vitae | auch wenn vorangestellt |
| Kolumnentitel | — |
| Klappentexte | — |
| Verfasservermerk | "von Jeanne Hersch" nur im Header |
| Initialen | nicht annotiert |
| Mehrspaltigkeit | nicht reproduziert als solche |

### revisionDesc (Workflow-Status, E66/E77)

Jedes finale TEI in `output/tei_final/` enthaelt `<revisionDesc>` direkt vor `</teiHeader>`.
Der erste `<change>` haelt die Pipeline-Erzeugung fest; danach folgt je ein Summary-`<change>`
pro Strom (OCR/Layout/TEI) mit dem menschgesetzten Workflow-Status. Projiziert vom Manifest
in den Header durch `tei_status_marker.py` (E66):

```xml
<revisionDesc>
  <change when="2026-03-15" who="pipeline">TEI generated (Unified Pipeline v1, Gemini + RelaxNG)</change>
  <change status="unverifiziert" n="ocr-summary">OCR-Strom (Stand): unverifiziert</change>
  <change status="unverifiziert" n="layout-summary">LAYOUT-Strom (Stand): unverifiziert</change>
  <change status="unverifiziert" n="tei-summary">TEI-Strom (Stand): unverifiziert</change>
</revisionDesc>
```

Status-Werte (drei Stufen seit E77): `unverifiziert` | `in_arbeit` | `verifiziert`. Das fruehere
Agent-Screening (Status-Werte `APPROVED`/`NEEDS_REVIEW`/...) ist mit E66 abgeschafft — kein Mensch
hatte diese „APPROVED" vergeben. Stand: 285/285 `unverifiziert`. Der Viewer zeigt den Status als Ampel-Pill.

### Element-Inventar

| Element | Attribute | Verwendung |
|---|---|---|
| `<TEI>` | `xmlns`, `type="naegeli"` | Root |
| `<teiHeader>` | — | Metadaten |
| `<text>`, `<front>`, `<body>`, `<back>` | — | Container |
| `<div>` | `n`, `type` | strukturell |
| `<pb>` | `facs`, `n` | Seitenumbruch |
| `<lb>` | `facs`, `n`, `break` | Zeilenumbruch |
| `<head>` | `type` | Ueberschrift |
| `<title>` | `type` (main/sub) | Titel |
| `<p>` | `facs` | Absatz |
| `<hi>` | `rendition` | Highlighting |
| `<bibl>` | — | Bibliografische Eintraege (`<listBibl>`, Review-`<head>`); seit E71 keine Entity-Refs |
| `<note>` | `place`, `n`, `xml:id`, `next`, `prev` | Fussnote/Marginalie |
| `<foreign>` | `xml:lang` | Sprachwechsel |
| `<space>` | `dim` | Abstand |
| `<list>`, `<item>`, `<table>`, `<row>`, `<cell>` | — | Listen + Tabellen |
| `<figure>` | `xml:id` | Abbildung |
| `<graphic>` | `xml:id`, `url` | Bildreferenz |
| `<choice>`, `<sic>`, `<corr>` | — | Druckfehler |
| `<sp>`, `<speaker>` | `type` | Sprechakt |
| `<listBibl>` | — | Bibliografie |
| `<ab>` | `type`, `hand` | redaktioneller Block |
| `<unclear>` | `cert` | unleserliche Passage |
| `<anchor>` | `xml:id` | Doppelseiten-Bilder |
| `<ref>` | `target` | externer Verweis |
| `<revisionDesc>`, `<change>` | `who`, `when`, `status` | Versionsstatus |

---

## Implementierungsphasen

| Phase | Inhalt | Status |
|---|---|---|
| 0 | Pilot: Layout-Eval + OCR + TEI auf 15 Docs | Done |
| 1 | Scale Layout: Docling + Gemini QA auf 285 Docs | Done |
| 2 | PAGE-XML Generator + METS | Done (285 Docs) |
| 3 | NER + Wikidata Linking | Entfernt (E71, 2026-05-27) |
| 4 | TEI-XML mit PAGE-XML | Done (285/285 schema-valide) |
| 5 | Extended Evaluation (CER-Benchmark) | Done — siehe [quality.md](quality.md) |
| 6 | Production Run + fachliche Kuration | In Progress — 285/285 generiert, Workflow-Status `unverifiziert` (E66), Kuration offen |

**Querschnitt** (parallel zu Phasen 3-6): Pipeline-Viewer mit Edit-Modus — siehe [viewer.md](viewer.md). Die fruehere oeffentliche Lese-Edition (E33) und der Curation Editor (E36) wurden mit E56 abgeschafft.

### Sub-Projekt: CER-Verbesserung

Systematische OCR-Qualitaetsverbesserung durch iteratives Experimentieren und Benchmarken.
Baseline und Ziel siehe [quality.md §CER](quality.md). Werkzeuge: `scripts/eval/benchmark_cer.py`,
`scripts/eval/cer_statistics.py`, `scripts/eval/cer_statistics_full.py`. Phasen 0-4 mit Erfolgsmetriken
(Phase 1 Ziel Median <5%, Phase 2 Ziel Median <4%).

---

## ZBZ Structural Tags (Docling → ZBZ → PAGE-XML)

| Docling | ZBZ | PAGE-XML |
|---|---|---|
| Title, Section-header | `zb_heading` | heading |
| Text, Paragraph, List-item, Table, Formula | `zb_paragraph` | paragraph |
| Footnote | `footnote` | footnote |
| Caption | `caption` | caption |
| Page-header, Page-footer | `_filter` | (entfernt) |
| Picture, Figure | `_skip` | — |

---

## Online-Demo (E28)

Volle Pipeline-Output (`output/`) ist gitignored, nur lokal verfuegbar. Fuer die Online-Demo
(GitHub Pages) sind 4 repraesentative Dokumente committed:

| Doc | Typ | Sprache | Seiten | Besonderheit |
|---|---|---|---|---|
| 2310 | A | FR | 3 | Journal-Artikel, JSTOR-Cover |
| 1000 | B | FR | 4 | zweispaltig |
| 1330 | D | DE/FR | 6 | bilingualer Sammelband |
| 1540 | C | DE | 8 | deutsche Monografie |

Mit E57 (Per-Seiten-Mirror) liegen zusaetzlich fuer ALLE 285 Docs Layout-,
OCR- und TEI-Daten in `docs/data/pages/` — damit funktioniert der Viewer auf
GitHub Pages fuer das gesamte Korpus, nur Faksimile-Bilder fehlen ausserhalb
der 4 DEMO-Docs (Bildlieferung lokal-only, 4 GB).

---

## Manuelle Edits zurueck in die Pipeline (Round-Trip)

Der Viewer schreibt Kuration (Layout, OCR-Text, Workflow-Status) direkt in den
Working Tree (File System Access API, E72/E78) und spiegelt sie nach `docs/data/`
(E79); `tei_unified --reassemble` konsumiert die kuratierten Dateien real und
refined gezielt die geaenderten Seiten (je 1 Gemini-Call). Vollstaendiger Ablauf
inkl. Save-Mechanismus, Schrittfolge, Provenance-Konzept und geplanter
`_complete.xml`-Variante: [workflow.md §Round-Trip](workflow.md).

Daten: Scan-Bilder in `docs/images/{doc_id}/`, OCR/Layout/TEI in `docs/data/examples/{doc_id}/`.
`core.js`-Pfadresolver mit dreistufiger Fallback-Kette: `data/pages/` → `data/examples/{doc_id}/`
→ `../output/...` (E57).

---

## Transkribus-Export (PAGE-XML-Round-Trip, E81)

Die in Stufe 4 erzeugte PAGE-XML (`output/page_xml/{doc}/page/`) ist Standard-PAGE
2013-07-15 und laesst sich verlustfrei nach Transkribus zurueckspielen -- als Layout +
Transkription, fuer manuelle Nachkorrektur oder HTR-Modelltraining. Gegenrichtung zum
Viewer-Round-Trip oben: dort kommen Edits rein, hier geht Pipeline-Layout raus.

**Ordnerkonvention.** Transkribus liest zu jedem Bild eine gleichnamige PAGE-XML aus
einem `page/`-Unterordner; ein Ordner = ein Dokument:

```
{doc}/
  {doc}_p001.png          # Bild oben
  page/{doc}_p001.xml     # gleichnamige PAGE-XML
```

`scripts/edition/transkribus_export.py` baut diese Struktur aus `output/page_xml/` +
`docs/images/{doc}/` nach `output/transkribus_upload/` (gitignored). Auswahl: `--sample`
(stratifiziert ueber Seitenzahl x Sprache), `--all`, `--reference` (die 24 Objekte, die
ZBZ bereits in ihrer eigenen Transkribus-Collection hat), `--doc`. Pro Seite verifiziert
es, dass das PNG-Pixelmass den deklarierten `imageWidth`/`imageHeight` entspricht
(Koordinaten alignt); Seiten ohne Bild oder mit Mass-Drift werden gemeldet statt still
kopiert. Der Export laeuft ueber die PAGE-XML, nicht ueber die Bilder -- Seiten ohne
Layout (z. B. Leerseiten) bleiben aussen vor.

**Dialekt.** Out-of-the-box kompatibel (TextRegion/Coords/TextLine/TextEquiv/
ReadingOrder + `custom`-Strukturtypen). Einschraenkung: die Pipeline-PAGE traegt
Zeilen-Polygone, aber **keine Baselines** -- fuer Import, Anzeige und Struktur reicht das;
nur HTR-*Training* in Transkribus braucht Baselines (die ZBZ-Originale haben sie). Die
Pipeline-Bilder sind 1240x1754 (150 dpi), die ZBZ-Originale 2479x3508 (300 dpi); jeder
Stand ist in sich konsistent.

**Upload per API.** `scripts/edition/transkribus_upload.py` laedt die gebauten Bundles
ueber die Legacy-TrpServer-REST-API (`transkribus.eu/TrpServer/rest`): `POST /auth/login`
-> `POST /uploads?collId=` (JSON-Manifest mit `md.title` + `pageList`) -> `PUT
/uploads/{id}` (Bild + XML je Seite). Verifiziert 2026-06-08: die Legacy-API schreibt
korrekt in eine Collection der **neuen** Plattform (app.transkribus.org); Login +
Collection teilen sich den readcoop-Account. Auth ausschliesslich ueber Umgebungsvariablen
(`TRANSKRIBUS_USER`/`TRANSKRIBUS_PASSWORD`/`TRANSKRIBUS_COLLECTION`), nie im Code/Repo/.env.
Jeder Lauf legt **neue** Dokumente an (kein Dedup) -- vor dem Vollupload `--dry-run`
(prueft Login + Zugriff) und `--doc {ID}` (ein Testobjekt). CLI:
[CLAUDE.md §Transkribus-Export / Upload](../CLAUDE.md).

---

## Verweise

- [methodik.md](methodik.md) — operative Werkzeuge, CLI-Referenz, Arbeitszyklus
- [quality.md](quality.md) — CER + TEI-Validierung + Screening
- [viewer.md](viewer.md) — Pipeline-Viewer mit Layout- und Transkriptions-Editor
- [infrastruktur.md](infrastruktur.md) — Azure, Podman, CI/CD
- [decisions.md](decisions.md) — Entscheidungsregister
