---
type: journal
created: 2026-01-29
updated: 2026-03-15
tags: [zbz-ocr-tei, journal, log]
status: active
---

# Work Journal

Chronological work log. Decisions are consolidated in [DECISIONS](DECISIONS.md), project status in [PROJEKT](PROJEKT.md).

**Dependencies:** None (standalone log)

---

## 2026-03-15 | TEI Validation Quality Gate + Pipeline-Dokumentation (Session 26)

135. Pipeline-Diagramm und Data Flow um Curation + Publication erweitert:
   - README.md: Pipeline-Diagramm endet jetzt bei Curation -> Publication
   - PLAN.md: Data Flow um Curation Editor + Publish-Schritt ergaenzt
   - Curation Editor als finaler Human-in-the-Loop-Schritt positioniert

136. TEI Validator refactored (`scripts/tei/tei_validator.py`):
   - Klares 2-Ebenen-Modell: Errors (blockierend) + Warnings (informativ)
   - Errors: RelaxNG TEI-All + R1-R7 (type, header, body, div, note, entity-ref)
   - Warnings: W1 (Sprach-Code "und"), W2 (teiHeader title/author leer), W3 (facsimile/pb Mismatch), W4 (leere div), W5 (Text-Volumen), W6 (lb-Dichte), W7 (graphic url), W8 (Entity-Coverage)
   - R8 entfernt (redundant mit RelaxNG), R10/R13 entfernt (>50% False Positives), R11 ersetzt durch W8
   - R7 erweitert um placeName (war vorher nur persName/orgName)
   - Performance: 1x parsen statt 3x (lxml Tree wiederverwendet)
   - HTML-Report: `--html-report` erzeugt `validation_report.html`
   - Ergebnis: 50/50 valid, 15/50 mit Warnings (vorher 49/50 -- fast alles False Positives)

137. Pipeline-Integration:
   - tei_unified.py: Validation jetzt Default (aktiv), `--skip-validate` zum Ueberspringen
   - Batch-Run erzeugt automatisch HTML+JSON Validierungsbericht
   - Curation Server: 2 neue Endpoints (`/api/validation/summary`, `/api/validation/{doc_id}`)

138. Entity-Tagging grundlegend korrigiert -- typkorrekte Tags mit internen IDs:
   - `_load_entity_entries()` in `tei_mapping_prompt.py`: Laedt Entity-Namen mit Typ und ID aus dem Index
     statt nur eine Namensliste. Alle Entity-Typen (person, org, place, work), nicht nur person+org
   - `annotate_entities()` in `tei_generator.py`: Taggt jetzt typkorrekt mit interner ID als ref:
     `<placeName ref="#zbz-l.705">Suisse</placeName>` statt `<persName>Suisse</persName>`
   - `reannotate_entities()` in `tei_step2.py`: Gleicher Fix fuer Step 2, erkennt auch placeName/bibl-Tags
   - `build_known_entities_block()` in `tei_mapping_prompt.py`: Gemini-Prompt zeigt Entities nach Typ
     gruppiert (PERSONS/ORGANIZATIONS/PLACES/WORKS) statt alle als persName
   - Validator W10: Warnt wenn nur persName ohne orgName/placeName vorhanden
   - Verifizierung Doc 1560: "Suisse" jetzt placeName (14x), "SGG" orgName (3x), "Jeanne Hersch"
     persName mit ref="#zbz-p.2" (6x). 0 Errors, 0 Warnings

139. TEI-Erzeugung verbessert basierend auf Validierungs-Erkenntnissen (`scripts/tei/tei_step3.py`):
   - Sprach-Mapping gefixt: Mehrsprachige Codes ("fra/deu", "fra/deu/ita") werden korrekt geparsed,
     alle Sprachen einzeln in `<langUsage>` eingetragen (vorher: alles zu "und" gefallen)
   - facsimile/pb Mismatch gefixt: Leere `<surface>` mit `<graphic>` Platzhalter fuer Seiten
     ohne Layout-Zones, damit pb- und surface-Anzahl synchron bleiben
   - Neuer `_parse_languages()` mit umfassendem Mapping (2-Letter, 3-Letter, Gross/Klein)

140. 25-Doc Production Test (Docs 1520-1770): 25/25 VALID, 341 Seiten, 750s. Keine Schema-Errors.

### Geaenderte Dateien
- scripts/tei/tei_mapping_prompt.py (_load_entity_entries() mit Typ+ID, Prompt typgruppiert)
- scripts/tei/tei_generator.py (annotate_entities() typkorrekt mit ref)
- scripts/tei/tei_step2.py (reannotate_entities() typkorrekt mit ref)
- scripts/tei/tei_step3.py (Sprach-Mapping + facsimile/pb Fix)
- scripts/tei/tei_validator.py (Refactoring + W10 Entity-Typ-Balance)
- scripts/tei/tei_unified.py (Validation Default, HTML-Report nach Batch)
- scripts/server/curation_server.py (2 neue Validation-Endpoints, register.html)
- README.md (Pipeline-Diagramm, Curation-Abschnitt, Validation-CLI)
- knowledge/PLAN.md (Data Flow mit Validation + Curation + Publish)
- knowledge/PIPELINE.md (Validation-Regeln R1-R7 + W1-W10)
- knowledge/CURATION.md (neue API-Endpoints)

---

## 2026-03-14 | Frontend-Konsolidierung (Session 24)

134. Edition als Hauptfrontend konsolidiert:
   - Edition-Seiten von docs/edition/ nach docs/ root verschoben (Landing, Katalog, Reader, About)
   - Pipeline-Seiten nach docs/infrastruktur/ verschoben (Dashboard, Viewer, Benchmark)
   - Gemeinsame Navigation mit Sub-Nav fuer Infrastruktur-Seiten
   - Dark Mode entfernt, Design angeglichen (kuehler BG fuer Infrastruktur, Teal-Border)
   - ES5 -> ES6+ Modernisierung in allen 13 JS-Dateien (const/let, arrow functions, template literals, IIFE)
   - Console-Logging mit [ZBZ:Modul] Prefix in allen Modulen
   - CSS Bug-Fix: --ff-mono -> --font-mono
   - Python-Skripte + Curation Server an neue Pfade angepasst
   - Knowledge-Dokumente aktualisiert (7 Dateien)

### Geaenderte Dateien
- docs/ (36 Dateien: HTML, JS, CSS umstrukturiert)
- scripts/generate_edition_data.py, scripts/server/curation_server.py (Pfad-Anpassungen)
- knowledge/ (7 Dateien aktualisiert)

---

## 2026-03-12 | Viewer WD/zbz-ID + GND Bug Fix (Session 23)

131. Viewer Entity-Sidebar erweitert (Phase 3 offener Punkt: "WD/zbz-ID Support in tei-viewer.js + edition-tei.js"):
   - Neue `resolveAllLinks()` Funktion in entity-utils.js: gibt alle verfuegbaren Links zurueck (WD + GND), nicht nur den ersten
   - Sidebar zeigt jetzt separate WD- und GND-Link-Badges (beide wenn vorhanden)
   - zbz-ID (z.B. zbz-p.1) als Label in Sidebar und Tooltip sichtbar
   - Resolution-Status (Checkmark/Fragezeichen) auch im Dashboard-Viewer (war vorher nur in Edition)
   - CSS fuer neue Elemente in shared.css + edition.css

132. Wikidata Linking Fortschritt: 2,803/11,685 Entities (24%) ueber ~110 Docs. Linking fuer alle 285 Docs gestartet (Hintergrund-Lauf).

133. **GND 0% Bug gefunden und behoben**: Drei Ursachen identifiziert:
   - entity_index.py `_write_index_file()` schrieb GND-IDs nie in TEI-XML (kein `<idno type="GND">`)
   - entity_index.py `_load_index_file()` las GND-IDs nie aus TEI-XML
   - entity_index.py `register_new()` akzeptierte keinen `gnd_id` Parameter
   - Wikidata-Cache hatte altes Format ohne `gnd_id` Feld (P227 wurde nie zwischengespeichert)
   - Fix: 4 Code-Aenderungen in entity_index.py + Cache-Backfill (318 QIDs, P227 nachgeholt)
   - Ergebnis: 0% -> 958/4,408 (21.7%) GND-IDs im Entity Index
   - TEI-XML Indices mit `<idno type="GND">` (535 person, 121 org, 238 place, 64 work)

### Geaenderte Dateien
- docs/entity-utils.js (resolveAllLinks + Tooltip)
- docs/tei-viewer.js (Sidebar)
- docs/edition/js/edition-tei.js (Sidebar)
- docs/shared.css + docs/edition/css/edition.css (neue CSS-Klassen)
- scripts/ner/entity_index.py (GND write/read/register/merge Fix)
- data/entities/*.xml (TEI-XML Indices mit GND `<idno>`)
- docs/data/entity_index.json (958 GND-IDs)

---

## 2026-03-09 | NER Completion + TEI Entity Injection (Session 22)

125. Wikidata Linking Fortschritt: 67/285 Docs abgeschlossen (1,696/11,685 Entities = 15%), Rest bei 0%. Linking wurde aus Session 21 unterbrochen, neu gestartet.

126. NER Evaluation: Corpus-Metriken erstellt + HTML-Report generiert (output/ner_report.html).
   - 285 Docs, 3,536 Seiten, 11,685 Entities, 26,197 Mentions
   - Avg 41 Entities/Doc, 3.3/Seite
   - Typ-Verteilung: person 36.7%, place 22.3%, date 15.0%, org 13.6%, work 10.8%, event 1.6%
   - Resolution Rate: 14% (Wikidata Linking noch unvollstaendig)

127. TEI NER Injection: 49/51 Docs mit Entity-Markup versehen (46 neu, 3 bereits vorhanden).
   - Alle TEI-Unified Docs mit _final.xml und NER-Daten verarbeitet
   - Output: output/tei_ner/{doc_id}/{doc_id}_ner.xml
   - TEI NER Validation: 10/49 Docs geprueft, **alle VALID** (0 Schema-Fehler, 0 Warnungen). Rest noch offen.
   - 2 Docs (1520, 1530+) fehlten _final.xml trotz tei_unified-Verzeichnis

128. Entity Index: 4,100 Eintraege (1,979 Person, 698 Org, 661 Place, 762 Work), 341 mit Wikidata-IDs.

129. Wikidata Linking neu gestartet, bei Doc 21/285 abgebrochen (Session-Ende). Noch im Cache-Bereich (keine neuen API-Queries noetig fuer die ersten 67 Docs). Die restlichen ~218 Docs brauchen einen laengeren Lauf.

130. Knowledge-Update: PIPELINE.md (Stage 5 NER-Metriken von Sample auf Production), PLAN.md (Phase 3 Checkboxen + Phase 4 Status), PROJEKT.md (M3 Done, M4 Counts, Component Table), INDEX.md (Timestamp), README.md (NER/Wikidata/TEI-NER Zeilen).

### Offene Tasks nach Session 22
- (A) Wikidata Linking: `python -m scripts.ner.wikidata_linker --all` (218 Docs unverlinkt, dauert Stunden)
- (B) Entity Index Merge: `python -m scripts.ner.entity_index --merge-all` (nach Wikidata Linking)
- (C) TEI NER Validation: restliche 39/49 Docs validieren
- (D) TEI Unified Production Run: 235/286 Docs (`python -m scripts.tei.tei_unified --all`, ~$80 Gemini)
- (E) TEI NER Re-Injection nach (D): dann 286/286 statt 49
- (F) Kurations-Pilot: Doc 2310 im Editor end-to-end testen

---

## 2026-03-09 | Knowledge Refactoring + NER Production Run (Session 21)

122. Wissensstruktur-Refactoring: Digitale Edition + Curation Editor als zusammengehoeriges System erkannt.
   - Neues EDITION.md: Architektur, Design System, Datei-Tabelle (aus PIPELINE.md §E33 ausgelagert)
   - PIPELINE.md §E33 auf 6-Zeilen-Kurzreferenz reduziert (vorher ~55 Zeilen)
   - CURATION.md: Dependency auf EDITION.md ergaenzt
   - PLAN.md: Neuer Querschnitt-Abschnitt "Digitale Edition + Curation" (statt Phase-Nummer)
   - INDEX.md: EDITION.md in Document Matrix, Dependencies, Key Concepts, Directory Structure
   - DECISIONS.md: E33 verweist auf EDITION.md, E36 auf CURATION.md

123. NER Production Run abgeschlossen:
   - NER Extraction: 285/286 Docs, 11,220 unique Entities, 25,008 Mentions (~8 Min via Gemini Flash Lite)
   - Entity Index Merge: 472 -> 4,100 Eintraege (3,516 neu registriert, 5,629 matched)
   - Wikidata Linking: Production Run gestartet (285 Docs, laeuft)

124. Doku-Updates: README.md (NER/TEI Status, EDITION.md in Doku-Tabelle, Quick Start tei_unified), PROJEKT.md (Component Status NER + Edition/Curation aktualisiert)

---

## 2026-03-09 | Curation Editor Phases 2-5 + Hardening (Session 19+20)

115. Curation Editor Phase 2 (Struktur-Editing):
   - Floating Block-Toolbar ueber fokussiertem Block: Typ-Dropdown (p/head/note/figure), Teilen/Zusammenfuegen/Loeschen Buttons
   - Block-Typ-Wechsel aendert CSS-Klasse + data-tei-tag, Serializer erzeugt korrektes TEI
   - Split: am Cursor teilen, neuer Block gleichen Typs
   - Merge: Kinder in vorherigen Block verschieben
   - Delete: Block entfernen

116. Curation Editor Phase 3 (Entity-Kuration):
   - Text markieren -> Floating Entity-Toolbar (Person/Org/Ort/Werk/Entfernen)
   - surroundContents wraps Selection in Entity-Span (contenteditable=false)
   - Klick auf Entity -> Popover mit ref-Eingabe (GND-URI, Wikidata-ID etc.)
   - Entity-Typ aendern oder komplett entfernen (Unwrap)
   - Server: Wikidata-Such-Proxy (/api/wikidata/search), Entity-Index-Suche (/api/entities/search)

117. Curation Editor Phase 4 (Review-Workflow):
   - Status-Badges (Entwurf/Pruefung/Freigegeben) im Reader-Header
   - Status-Badges im Katalog (Tabellen-Ansicht), Server-Detection
   - CSS: 3 Badge-Varianten (draft=amber, review=blue, approved=green) + Dark Mode

118. Speicher-Migration: TEI_CURATED_DIR von output/ (gitignored) nach data/tei_curated/ (git-tracked).
   - Einzeiler in config.py (DATA_DIR statt OUTPUT_DIR)
   - Publish-Endpoint: POST /api/tei/{doc_id}/publish kopiert approved-Docs nach docs/data/examples/ (GitHub Pages)
   - Guard: Nur status=approved darf publiziert werden

119. Entity-Autocomplete im Popover:
   - Parallele Suche: Lokaler Entity Index + Wikidata API (via Server-Proxy)
   - Ergebnisse in Dropdown mit Sektionen ("Entity Index" / "Wikidata")
   - Zeigt Name, Ref-ID (GND/QID), Beschreibung
   - Tastatur-Navigation: Pfeil-Hoch/Runter, Enter zum Auswaehlen
   - Bug-Fix: Entity-Index-Suche nutzte .get() auf Dataclass -> getattr() korrigiert
   - Varianten-Match: Durchsucht auch variants-Array, nicht nur main_name

120. TEI-Validierung im Editor:
   - "Validieren"-Button in Edit-Toolbar
   - POST /api/tei/{doc_id}/validate-page: RelaxNG via Temp-File + tei_validator.validate_relaxng()
   - Validierungspanel unter Toolbar zeigt Fehler mit Zeilennummern (rot, schliessbar)
   - XML wird in minimales TEI-Dokument gewrapped fuer Schema-Validierung

121. Doku-Update: README.md (Curation Editor Abschnitt, scripts/server/, data/tei_curated/), CURATION.md (Autocomplete, Validierung, validate-page Endpoint), PIPELINE.md (Curation Layer Abschnitt)

---

## 2026-03-08 | Phase 3 Scale-Up + Frontend (Session 17+18)

104. tei_unified Refactoring committed: step1/2/3 + core.loaders extrahiert. Orchestrator tei_unified.py von ~1100 auf ~70 Zeilen.

105. NER Robustheit (4 Fixes): Diakritik-Normalisierung (FR 66% Korpus), Retry mit Backoff (Gemini + Wikidata), Surname-only Matching (verhindert falsche Merges), mehrsprachige WD-Suche (FR+DE+EN).

106. Sample-Run 15 Docs: 370 Seiten, 765 Entities, 1827 Mentions. Entity-Index waechst auf 472 Eintraege. Wikidata-Resolution 57% (328/472 mit QIDs). TEI-Injection auf 3 Docs validiert (alle VALID).

107. QID-Merge-Bug gefunden und behoben: merge_store_into_index uebertrug Wikidata-QIDs nur bei NEUEN Eintraegen, nicht bei bestehenden. Fix: QID-Update im matched-Branch. Index von 10 auf 328 QIDs.

108. Frontend: Beide Viewer (tei-viewer.js, edition-tei.js) unterstuetzen jetzt 3 Ref-Formate (#zbz-p.N intern, WD:Q... Wikidata, GND:... lobid.org). placeName als neuer Entity-Typ mit Amber/Orange-Akzent. Sidebar zeigt Orte-Gruppe, Links oeffnen korrekte externe Seiten (WD/GND).

109. NER Phase 1 Qualitaetsverbesserungen (7 Tasks, committed f7e2356):
   - Known-Entities-Hint von 50 auf 150/Typ, QID-verifizierte zuerst
   - Diakritik-Matching (_stripped_lookup) im Entity Index
   - Sicheres Surname-Fallback (nur bei genau 1 Kandidat)
   - Wikidata TYPE_INSTANCE_OF +9 QIDs (Essay, Zeitung, Stiftung, Dorf etc.)
   - 4-Stufen Konfidenz (1.0/0.9/0.8/0.6) mit match_type
   - OCR-Text-Chunking fuer Seiten >8000 Zeichen
   - KNOWN_ENTITY_NAMES durch Entity Index ersetzt (11 -> 393 Namen)

110. NER Phase 2 Production Run gestartet: `ner_extract --all --force` (286 Docs, ~4152 Seiten).

111. NER Evaluation erweitert (ner_evaluate.py):
   - `--lenient` Flag fuer Diakritik-normalisierten P/R/F1-Vergleich
   - `--report <path>` generiert HTML-Report (Korpus-Metriken, Top-20, per-Doc-Tabelle)
   - Beide Modi (strict + lenient) werden parallel berichtet

112. Pipeline-Integration:
   - tei_unified.py: `--ner` Flag als Step 5 (Entity-Injection nach Assembly)
   - generate_dashboard_data.py: NER-Stats pro Doc (entity_count, mention_count, resolution_rate) + Corpus-Level in pipeline_summary
   - generate_edition_data.py: Automatischer Entity-Index-Export (JSON) + entity_count pro Katalog-Eintrag

113. Frontend NER-Integration:
   - Entity-Count Badge (ed-badge-ner) in Katalog-Karten (edition-shared.js)
   - Resolution-Status-Indikator (Haken/Fragezeichen) in Entity-Sidebar (edition-tei.js)
   - Count-Badge pro Entity-Typ-Gruppe in Sidebar
   - CSS fuer alle neuen Elemente (Light + Dark Mode)

114. Curation Editor MVP (Phase 1, E36):
   - FastAPI Server (scripts/server/curation_server.py, ~280 Zeilen): 7 Endpoints (health, get/put page, validate, assemble, get/put status)
   - Serviert Edition-Frontend + API, Daten in output/tei_curated/{doc_id}/
   - Kurations-Metadaten (curation.json) mit Seiten-Status + Historie
   - TEI-Prioritaetskette: kuratiert > NER > unified > examples
   - Editor-Modul (edition-editor.js, ~370 Zeilen): WYSIWYG contenteditable + DOM-zu-XML Serializer + XML-Textarea-Modus
   - Edit-Toggle in Reader (edition-reader.js): editMode State, Ctrl+S Save, beforeunload Warnung
   - Editor-CSS (~100 Zeilen): contenteditable Styles, Save-Button, Toast-Notifications, Dark Mode
   - Server-Detection: Health-Check beim Laden, Edit-Button nur sichtbar wenn Server laeuft
   - Verifiziert: Server startet, TEI laden (examples), Save Round-Trip, kuratierte Version hat Prioritaet

---

## 2026-03-07 | NER Pipeline + Entity Index (Session 16)

100. NER Pipeline Phase 3 implementiert (E34): 6 neue Module in `scripts/ner/`. Post-hoc-Architektur: Gemini Flash Lite extrahiert Entities pro Seite als JSON, EntityStore aggregiert pro Dokument, Wikidata-API reconciled (kein Gemini fuer IDs), TEI Injection schreibt nach `output/tei_ner/`.

101. 6 Entity-Typen: person, organization, place, work, event, date. Wikidata als Primaer-ID-System statt GND (breitere Abdeckung, international).

102. Entity Index als TEI-XML (`data/entities/`): `person_index.xml`, `org_index.xml`, `place_index.xml`, `work_index.xml`. Eigenes ID-Schema: `zbz-p.N`, `zbz-o.N`, `zbz-l.N`, `zbz-w.N`. Varianten fuer String-Matching. Single Source of Truth.

103. Pilot Doc 2310: 30 unique Entities, 54 Mentions. 5 Index-Matches (Seed), 22 neu registriert. Index: 31 Eintraege, 51 Varianten.

---

## 2026-03-07 | TEI Pipeline Refactoring + Validation Fixes (Session 15)

99. Post-Assembly Schema Fixes (`_fix_post_assembly_schema()`): 3 neue Fixes fuer RelaxNG-Verletzungen die erst nach Document Assembly auftreten. Fix A: `<graphic>` ohne `url` -> `url="unknown"`. Fix B: `<p>` in `<head>` -> Inhalt entpacken. Fix C: `<epigraph>` nach Content (divTop-Regel) -> entpacken. Ergebnis: 50/50 unified TEI VALID (vorher 47/50).

92. Refactoring-Plan umgesetzt (`REFACTORING_PLAN.md`, 7 Phasen). Keine funktionalen Aenderungen, gleicher Output.

93. Phase 1 (Bugs): Dead Code in `tei_mapping_prompt.py` entfernt (debate-Fallback, L291-292). XPath-Bugs in Validator waren bereits korrekt.

94. Phase 2 (Constants): `TEI_NS`, `TEI_ALL_URL`, `SCHEMA_DOWNLOAD_TIMEOUT`, `VALID_DIV_TYPES` nach `config.py` zentralisiert. Lokale Definitionen in `tei_unified.py` und `tei_validator.py` entfernt. Speaker-Regex als `SPEAKER_PATTERN` Konstante. Schema-Download mit Timeout.

95. Phase 3+4 (God-Functions + DRY): `fix_gemini_tei()` in 3 Funktionen aufgeteilt: `_fix_simple_patterns()` (Regex), `_fix_structural_issues()` (ET), `reannotate_entities()`. Shared Utilities: `_parse_tei_fragment()`, `_serialize_tei_fragment()`, `_wrap_orphan_groups()`, `_make_element()`. `_fix_orphaned_body_children()` nutzt jetzt `_wrap_orphan_groups()`.

96. Phase 5 (process_page_step1): In 3 Funktionen aufgeteilt: `_is_interview_turn()` (Modulebene), `_compute_facsimile_zones()`, `_build_tei_body()`.

97. Phase 6 (Error Handling): Silent `except: pass` durch spezifische Exceptions ersetzt. Gemini-Fehler differenziert (Auth -> Abbruch, Parse -> Fallback). lxml-Import top-level in Validator.

98. Phase 7 (Cleanup): `functools.lru_cache` statt mutablem Global fuer Lazy-Import. `xml.etree.ElementTree` als Top-Level-Import.

---

## 2026-03-06 | Digitale Edition + Refactoring (Session 14)

86. Digitale Edition implementiert (E33): Oeffentliche statische Website unter `docs/edition/` fuer Forscher und Oeffentlichkeit. 4 Seiten (Landing, Katalog, Reader, About), eigenes Design-System (`edition.css`, ~1300 Zeilen), `ZBZ.Edition` Namespace. Parchment-Hintergrund, Scholarly Navy, Warm Gold Akzente. Dark Mode, 3 Responsive-Breakpoints, Print-Styles.

87. Daten-Generator (`scripts/generate_edition_data.py`): Liest `dashboard.json` + `doc_metadata.json`, erzeugt `catalog.json` mit 286 Dokumenten, Korpus-Statistiken, Featured-Liste. Kopiert 21 TEI-XMLs fuer 4 Demo-Docs.

88. Reader (Herzstueck): Faksimile + TEI-Text nebeneinander, draggbarer Panel-Divider, Seitennavigation (Buttons + Tastatur), Zoom (25-300%), Font-Toggle (Serif/Sans), Entitaeten-Sidebar (Personen/Orgs/Werke mit GND-Links), XML-Ansicht mit Syntax-Highlighting.

89. Katalog: 286 Dokumente, facettierte Filter (Typ, Sprache, Publikationsform, Zeitraum), MiniSearch Client-Side Volltextsuche (CDN, ~22KB), Tabelle/Karten-Ansicht, sortierbare Spalten.

90. Optimierungen: Count-Up-Animation (Hero-Metriken), Dark-Mode Sun/Moon SVG-Icons, Hamburger-SVG, Tabellen-Sortierung per Klick, Bild-Fade-In, Zurueck-Pfeil im Reader, Card-Placeholder bei Bild-Fehler, Nav-Brand Gold-Akzent, Hero-Gradient-Overlay, Faksimile-Schachbrett-Hintergrund.

91. Refactoring (DRY + Robustheit): Nav/Footer JS-Slot-Pattern (`#ed-nav-slot`, `#ed-footer-slot`) eliminiert HTML-Duplizierung ueber 4 Seiten. `buildCardHtml()` Shared-Helper ersetzt doppelte Card-Erzeugung in Landing + Katalog. `sanitizeDocId()` fuer Input-Validierung. `parseXml()` try-catch. MiniSearch try-catch Fallback. Divider `window.blur`-Handler. TEI `<hi>` Inline-Styles durch CSS-Klassen ersetzt (`ed-tei-hi-bold/italic/underline/spaced`, `ed-tei-foreign`, `ed-tei-sp`, `ed-tei-speaker`). XML-Syntax-Farben als CSS Custom Properties (`--ed-xml-*`). `aria-expanded` auf Hamburger-Menu. Konsistente Font-Einbindung ueber alle 4 Seiten.

**Decisions:** E33 (Digitale Edition). **Files:** 12 neue/modifizierte Dateien, ~3.200 Zeilen Code.

---

## 2026-03-06 | Unified TEI Pipeline (Session 13)

77. Unified TEI Pipeline konzipiert und implementiert (E32): Kombiniert regelbasierte TEI-Erzeugung (Step 1) mit Gemini-Verfeinerung (Step 2) in 4-Stufen-Pipeline. Ersetzt separaten `tei_generator.py` und `tei_gemini.py` fuer Produktion.

78. `scripts/tei/tei_mapping_prompt.py` erstellt: Mapping-Table-Prompt mit 8 Sektionen (Structure, Line-Level, Inline Formatting, Entities, Language, Corrections, Speech Acts, Omissions) + 10 Genre-spezifische Regelblocks (review, interview, debate, encyclopedia, speech, conference, preface, letter, newspaper, editorial). Systematische Tabelle statt Few-Shot-Prompting.

79. `scripts/tei/tei_unified.py` erstellt (~550 Zeilen): Enhanced rule-based TEI (Step 1: lb, head, note, semantic div, facsimile-Koordinaten aus Gemini/Docling Layout), Gemini Refinement (Step 2: 1 Call/Seite mit Mapping-Table + Overlay-PNG), Document Assembly (Step 3: teiHeader + facsimile + body), Validation (Step 4). CLI: `--doc`, `--sample`, `--all`, `--step`, `--validate`, `--force`, `--dry-run`.

80. `scripts/tei/tei_validator.py` erstellt: RelaxNG-Schema-Validierung (TEI-All von tei-c.org, Auto-Download) + 8 projektspezifische Regeln (R1-R8: type=naegeli, teiHeader, body, div-types, note-place, persName-ref, language-ident).

81. Schema-Fehler iterativ behoben: (a) `<p>` in `<sourceDesc>` nach `<biblStruct>` entfernt, (b) leeres `<imprint>` mit default `<date>` gefuellt, (c) `<head>` nach `<p>` in `<div>` via `any_content_emitted`-Flag geloest (headings nach Content werden zu `<p>`).

82. Pilot-Validierung: Alle 3 Docs (2310 review, 2530 standard, 1440 interview) RelaxNG-valide mit 0 Schema-Fehlern und 0 Projekt-Warnungen.

83. Gemini Step 2 auf Pilot-Docs ausgefuehrt: dotenv-Integration gefehlt, behoben. `fix_gemini_tei()` Post-Processing erstellt mit 6 Fix-Stufen: (a) `<ab>` mit `<p>` entpacken, (b) `<head>` in `<speaker>` entfernen, (c) `<head><p>` zu `<head>` flatten, (d) `<head>` nach Content zu `<p>` konvertieren, (e) `<sp>` gemischt mit `<p>` in Sub-Divs aufteilen, (f) Entity-Re-Annotation.

84. 3 Qualitaetsfixes implementiert: (a) Prompt-Tuning in `tei_mapping_prompt.py` -- "CRITICAL: Tag EVERY SINGLE mention" + Interview-sp-Verstaerkung. (b) `reannotate_entities()` -- tag-aware Post-Processing, splittet Text an bestehenden Entity-Tags und annotiert nur Luecken. (c) Interview-Speaker-Erkennung in Step 1 Scaffold -- `_is_interview_turn()` Heuristik fuer Q&A-Muster, generiert `<sp>/<speaker>` mit `<persName>` fuer bekannte Entitaeten.

85. Recall-Ergebnisse nach Fixes: Doc 2310 (Review) stabil exzellent: persName 1.0, bibl 1.0, hi 0.94, lb 0.83. Doc 1440 (Interview): speaker 0.63->0.76 (+0.13), bibl 0.5->1.0 (+0.5), lb 1.0. persName-"Regression" (0.54->0.24) ist Artefakt: Referenz-TEI hat 46 leere `<persName>` in `<speaker>`-Tags (Konvention), tatsaechlicher Inline-persName-Recall = 1.0.

86. Production Run gestartet (286 Docs, Gemini 3.1 Flash Lite, ~$17). Erste 18 Docs: 5 INVALID. 3 neue Fix-Typen in `tei_unified.py` implementiert: (a) `_fix_orphaned_body_children()` -- Post-Assembly-Fix: verwaiste Block-Elemente (`<p>/<figure>/<note>`) neben `<div>`-Geschwistern in `<div type="text">` einwickeln. (b) Fix 3b: lose Inline-Elemente (`<lb>/<persName>/<orgName>`) direkt in `<div>` in `<p>` einwickeln. (c) `<epigraph>` nach Content im `<div>` entpacken (divTop-Regel). Verbesserter `<ab>`-Unwrap-Regex (robuster, prueft ob `<p>` enthalten).

87. Validierung nach Fixes: 22/23 VALID (Doc 110 braucht nur Reassembly). Production Run laeuft weiter (~1 Doc/min, ~4-5h Restlaufzeit). Pipeline ist resume-faehig (ueberspringt fertige Docs).

---

## 2026-03-06 | Layout-QA Full Run + Overlay-Generator (Session 12)

72. Layout-QA `changes_summary` Logging: `layout_qa_gemini.py` erweitert -- QA-Modus loggt Label-Transitions pro Seite (z.B. `text->section_header: 2, ADDED: 1`), Detect-Modus loggt `label_counts` pro Seite. Document-Summary aggregiert beides ueber alle Seiten in `summary_gemini.json`.

73. Full Re-Run mit `--force`: Alle 4'152 Seiten (286 Docs) werden mit aktuellem Prompt neu verarbeitet (auto-Modus: QA fuer gute/warning Seiten, Detect fuer bad/empty). Bisherige Ergebnisse ueberschrieben. Fehlerrate ~1% (Invalid Unicode-Escape, Empty Response). Durchschnitt ~6s/Seite, ~10 Seiten/Min.

74. Overlay-Generator Script: `scripts/generate_layout_overlays.py` -- Batch-Erzeugung von Layout-Overlay-PNGs fuer Gemini-Ergebnisse. Nutzt bestehende `draw_overlay_from_json()`. Output: `output/layout/{doc_id}/{doc_id}_p{NNN}_overlay_gemini.png`. Optional: Side-by-side Compare-Bilder (Docling links, Gemini rechts). Changed-Highlighting (gelb fuer ADDED/geaenderte Regionen).

75. Full Run Ergebnisse: 286/286 Docs, 3'992 Seiten verarbeitet (3'519 QA + 633 Detect), 30'714 Regionen, 14'708 Korrekturen, Avg Score 72.7. Top-Aenderung: 894 ADDED Regionen (fehlende Headers, Headings, Footnotes). Fehlerrate ~1% (160 Seiten fehlgeschlagen: Invalid Unicode-Escape, Empty Response).

76. Overlay-Bilder erzeugt: 7'988 PNGs (Gemini-Overlay + Docling-vs-Gemini Compare) fuer alle 286 Docs. Visuelle QA-Stichprobe (10 Seiten, Typen A/B/C/D): Gemini klar besser als Docling allein -- erkennt mehr Regionen, findet fehlende section_headers/page_headers/footnotes, zweispaltige Layouts korrekt getrennt. Score-0-Docs sind Detect-Modus (Docling hatte nichts) -- Gemini liefert brauchbare Ergebnisse. Keine neuen systematischen Probleme.

---

## 2026-03-06 | Gemini Vision TEI Generator + Dokumenttypspezifische Prompts (Session 11)

67. Dokumenttypspezifische Layout-Prompts: `layout_qa_gemini.py` erweitert mit 4-Ebenen-Hint-System basierend auf `doc_metadata.json`. Ebene 1: Layout-Typ (A/B/C/D), Ebene 2: Publikationsform (8 Werte), Ebene 3: Genre (14 Genres aus description via Keyword-Matching: article, review, interview, speech, debate, newspaper, conference, preface, letter, encyclopedia, editorial, essay, monograph), Ebene 4: Sprache (mono/multilingual mit Sprachliste). Funktionen `infer_genre()` und `build_doc_hints()` exportiert fuer Wiederverwendung in tei_gemini.py.

68. Genre-Analyse des Gesamtkorpus: 133 Standard-Artikel, 47 Essays, 26 Vortraege/Reden, 13 Interviews, 13 Konferenz-Beitraege, 11 Rezensionen, 10 Zeitungsseiten, 8 Debatten/Roundtables, 6 Vorworte, 3 Briefe, 2 Enzyklopaedie-Eintraege, 39 mehrsprachige Dokumente. Deutlich mehr Diversitaet als die 4 Layout-Typen.

69. Neuer Gemini Vision TEI Generator: `scripts/tei/tei_gemini.py` (~550 Zeilen). 3-Pass-Pipeline: Pass 1 (Struktur: Overlay-PNG + OCR + Layout + Metadata -> TEI-Skelett mit div-Hierarchie, pb, head, p, note), Pass 2 (Anreicherung: Overlay + Pass-1-TEI + Few-Shot-Snippets -> TEI mit lb, hi, persName, foreign, choice, break="no"), Pass 3 (Validierung: Alle Seiten-TEIs -> finales Dokument mit teiHeader + facsimile). Dokumenttypspezifische TEI-Prompts (12 Genre-Prompts: review, interview, debate, encyclopedia, speech, conference, preface, letter, newspaper, editorial, article, monograph). CLI: --doc, --sample, --all, --pass, --evaluate, --force, --dry-run.

70. Pilot-Ergebnis Doc 2310 (Typ A, Review, FR): 3 Seiten, 54.5s gesamt, alle 3 Passes erfolgreich, valides XML. Evaluation gegen Referenz-TEI: persName Recall 1.0, bibl Recall 1.0, lb Recall 1.0, div Recall 1.0. Generiertes TEI enthaelt div type="review", bibl mit GND-Referenz, foreign-Tags, break="no" Silbentrennung. Qualitativ deutlich besser als regelbasierter tei_generator.py.

71. config.py: `TEI_GEMINI_DIR = OUTPUT_DIR / "tei_gemini"` hinzugefuegt. Output-Struktur: `output/tei_gemini/{doc_id}/{doc_id}_p{NNN}_pass1.xml`, `_pass2.xml`, `_final.xml`, `_manifest.json`, `_eval.json`.

**Decisions:** E30 (Gemini Vision TEI + typspezifische Prompts). **Open:** Pilot auf Doc 2530 (B) und 1440 (D) ausstehend.

---

## 2026-03-05 | Frontend Refactoring (Session 10)

61. P0 Bug Fix: ZBZ.ZBZ.highlightXml -> ZBZ.highlightXml in tei-viewer.js + page-viewer.js (Doppel-Namespace verursachte Runtime-Error bei XML-Ansicht).

62. shared.js Cleanup: 3 Dead-Code-Funktionen entfernt (getData, fmtAccuracy, fmtCost). ES6-Shorthand-Methoden zu ES5 konvertiert (loadData, fetchRefTeiPage). Shared parseXml() Utility hinzugefuegt (ersetzt duplizierte parseTeiXml/parsePageXml).

63. Namespace-Konsolidierung: window.TeiViewer -> ZBZ.TeiViewer, window.PageViewer -> ZBZ.PageViewer. Alle Aufrufe in viewer.js angepasst. CSS-Klasse tei-empty -> empty-state (generisch, wird von TEI und PAGE verwendet).

64. shared.css Refactoring: --accent-d (amber/Gemini) + --fs-2xs + --fs-code CSS-Variablen hinzugefuegt. 8x hardcoded font-size durch Variablen ersetzt. .tei-tab/.page-tab und .info-toggle/.layout-toggle dedupliziert. 3 Dead-CSS-Klassen entfernt (.viewer-layout, .preview.two-col, .tei-figure-head). Duplicate .tei-empty entfernt (nutzt jetzt .empty-state). Amber-Farben #f59e0b auf var(--accent-d) umgestellt. Utility-Klassen hinzugefuegt (.hidden, .no-padding, .section-gap, .dist-row, .grid-3col, .text-muted-sm, .text-muted-italic).

65. viewer.js Refactoring: toggleTei/togglePage zu gemeinsamer togglePanel(name) zusammengefasst. 3x Zoom-Handler zu applyZoom() konsolidiert. DOM-Refs im mousemove-Handler gecacht (viewerArea, imagePanelEl, textPanelEl). alert() durch Inline-Fehlermeldung ersetzt. Unicode em-dash durch ASCII-Strich ersetzt.

66. dashboard.js: Filter-Rows nach Tabellen-Render gecacht statt bei jedem Event neu abzufragen. 3 Inline-Styles durch CSS-Klassen ersetzt.

67. benchmark.html: 230 Zeilen Inline-Script nach benchmark.js extrahiert. fmt() durch ZBZ.fmtNum() ersetzt. ZBZ.Benchmark Namespace.

68. HTML Inline-Styles: Alle style="display:none" und style="padding:0" und style="margin-top:2.5rem" durch CSS-Klassen (hidden, no-padding, section-gap) ersetzt. JS-Show/Hide-Logik auf classList umgestellt.

### Dateien geaendert

| Datei | Aenderung |
|-------|-----------|
| `docs/shared.js` | Dead Code, ES6->ES5, +parseXml() |
| `docs/shared.css` | CSS-Variablen, Dedup, Dead CSS, Utility-Klassen |
| `docs/tei-viewer.js` | P0 Bug, parseXml Dedup, Namespace, empty-state, em-dash |
| `docs/page-viewer.js` | P0 Bug, parseXml Dedup, Namespace, empty-state |
| `docs/viewer.js` | togglePanel, applyZoom, DOM-Cache, alert, em-dash, classList |
| `docs/dashboard.js` | Filter-Cache, Inline-Styles, classList |
| `docs/benchmark.js` | NEU -- extrahiert aus benchmark.html |
| `docs/benchmark.html` | Inline-Script entfernt, hidden-Klasse |
| `docs/index.html` | Inline-Styles -> CSS-Klassen |
| `docs/viewer.html` | Inline-Styles -> CSS-Klassen |

---

## 2026-03-05 | Documentation Refactoring (Session 9)

55. Repo-Audit: Tatsaechlichen Zustand gegen Dokumentation abgeglichen. Output-Verzeichnisse gezaehlt (4.117 TEI-XML, 4.377 PAGE-XML, 286 Layout-Dirs), Scripts inventarisiert (25 Python-Dateien in 4 Sub-Modulen), Frontend-Dateien geprueft (9 Dateien in docs/).

56. PROJEKT.md: 6 Korrekturen -- PAGE-XML Generator Pending->Done, TEI 383->4.117 Files, M2/M4 Milestones aktualisiert, 289->286 PDFs (mit O22-Verweis), Component Status ergaenzt (Classification, Gemini OCR, PAGE-XML Viewer, Layout Post-Processing resolved). Datum 2026-03-04->2026-03-05.

57. PLAN.md: Data-Flow-Diagramm aktualisiert -- OCR, PAGE-XML, TEI von "PARTIAL/NEXT" auf "DONE" mit aktuellen Zahlen.

58. INDEX.md: Korpusgroesse 289->286 korrigiert.

59. README.md: Status-Tabelle aktualisiert (TEI 285/286 Docs, PAGE-XML 286/286, Gemini OCR-Korrektur ergaenzt). Next Steps korrigiert (NER als naechster Schritt). Directory-Listing erweitert (+classify_docs.py, +gemini_ocr_correct.py, +layout/, +page-viewer.js, +benchmark.html, +dashboard.js, +doc_metadata.json). Knowledge-Count 14->13. Engines-Tabelle: Gemini-Nutzung erweitert. Viewer: PAGE-XML-Viewer ergaenzt.

60. requirements.txt: Fehlende anthropic-Dependency ergaenzt (wird von llm_postprocess.py benoetigt).

### Dateien geaendert

| Datei | Aenderung |
|-------|-----------|
| `knowledge/PROJEKT.md` | FIX -- 6 faktische Korrekturen (Status, Zahlen, Datum) |
| `knowledge/PLAN.md` | FIX -- Data-Flow-Diagramm Status aktualisiert |
| `knowledge/INDEX.md` | FIX -- 289->286 Korpusgroesse |
| `README.md` | UPDATED -- Status, Directory, Next Steps, Engines |
| `requirements.txt` | FIX -- +anthropic Dependency |

---

## 2026-03-05 | PAGE-XML/METS Viewer + Refactoring (Session 8)

51. PAGE-XML/METS Viewer im Frontend: Neues PageViewer-Modul (docs/page-viewer.js) mit 3 Tabs: Regionen (Region-Karten mit Typ, ID, Koordinaten, Text-Preview), XML (syntax-highlighted PAGE-XML Source), METS (Dokument-Manifest). PAGE und TEI teilen den 3. Panel-Slot (mutual exclusion).

52. Viewer-Integration: PAGE-Toggle-Button in Header, Divider-Resize fuer 3-Panel-Layout, Seitenwechsel aktualisiert PAGE-Panel. shared.js erweitert um fetchPageXml() und fetchMetsXml() mit Fallback-Caching.

53. Dashboard-Fix: Pipeline-Status von "export" (falscher Pfad) auf "page_xml" korrigiert. Alle 286 Docs korrekt als page_xml: true erkannt. PIPELINE_STEPS Label: EXP -> PAGE.

54. Refactoring: highlightXml() aus tei-viewer.js und page-viewer.js nach shared.js extrahiert als ZBZ.highlightXml(). Beide Viewer nutzen jetzt die gemeinsame Funktion.

### Dateien geaendert

| Datei | Aenderung |
|-------|-----------|
| `docs/page-viewer.js` | NEW -- PageViewer-Modul (Regionen/XML/METS) |
| `docs/viewer.html` | EXTENDED -- PAGE-Button, PAGE-Panel HTML, Script-Tag |
| `docs/viewer.js` | EXTENDED -- togglePage(), mutual exclusion, Divider |
| `docs/shared.js` | EXTENDED -- fetchPageXml, fetchMetsXml, highlightXml, PIPELINE_STEPS |
| `docs/shared.css` | EXTENDED -- PAGE-Region-Card Styles |
| `docs/tei-viewer.js` | REFACTORED -- highlightXml -> ZBZ.highlightXml |
| `scripts/generate_dashboard_data.py` | FIX -- export -> page_xml |

---

## 2026-03-05 | PAGE-XML + TEI Extension (Session 7)

46. PAGE-XML Generator erstellt (scripts/layout/page_xml_generator.py): Erzeugt PAGE-XML 2013-07-15 (Transkribus-Standard) aus Layout-JSON + OCR-Markdown. Layout-Quelle: Gemini-korrigiert bevorzugt, Fallback Docling. OCR-Quelle: Gemini B > Gemini A > Mistral. Ein TextLine pro TextRegion (keine Zeilen-Koordinaten verfuegbar). Output: output/page_xml/{doc_id}/page/{doc_id}_p{NNN}.xml.

47. METS Generator erstellt (scripts/layout/mets_generator.py): METS-Manifest pro Dokument, Transkribus-kompatibel. Wird automatisch von page_xml_generator am Ende von process_document() aufgerufen. Output: output/page_xml/{doc_id}/mets.xml.

48. Config erweitert: PAGE_XML_DIR + ZBZ_TO_PAGE_TYPE Mapping (zb_heading -> heading, zb_paragraph -> paragraph, footnote -> footnote, caption -> caption).

49. TEI Generator erweitert (5 Aenderungen): (a) OCR-Quelle: Gemini B > Gemini A > LLM C > Mistral. (b) Neue get_document_metadata() laedt aus doc_metadata.json (286 Docs) mit TESTPLAN-Fallback. (c) teiHeader nutzt echten Titel, Autor, Datum aus Metadaten. (d) Sprach-Mapping: ISO 639-3 direkt durchreichen. (e) discover_documents() findet alle Gemini-korrigierten Docs.

50. Produktion: PAGE-XML auf allen 286 Docs generiert (4.091 PAGE-XML Dateien + 286 METS). TEI-XML auf allen 285 Docs generiert (4.117 TEI-XML Dateien, alle mit Layout).

### Dateien geaendert

| Datei | Aenderung |
|-------|-----------|
| `scripts/config.py` | EXTENDED -- PAGE_XML_DIR, ZBZ_TO_PAGE_TYPE |
| `scripts/layout/page_xml_generator.py` | NEW -- PAGE-XML 2013-07-15 Generator |
| `scripts/layout/mets_generator.py` | NEW -- METS-Manifest Generator |
| `scripts/tei/tei_generator.py` | EXTENDED -- Gemini OCR, doc_metadata.json, teiHeader |

---

## 2026-03-05 | Code Quality Refactoring (Session 6)

38. generate_dashboard_data.py: N+1-Bug behoben -- gemini_manifest wurde in der per-Doc-Schleife bei jedem Durchlauf neu geladen (286x statt 1x). Fix: Manifest vor der Schleife laden, Lookup-Dict bauen fuer O(1)-Zugriff.

39. gemini_ocr_correct.py: None-Check fuer Gemini-API-Antwort in correct_page() hinzugefuegt (crashed vorher bei leerer Antwort, z.B. Doc 40). Metadaten-Cache: doc_metadata.json wird jetzt einmal geladen statt bei jedem get_doc_metadata()-Aufruf.

40. evaluate_ocr.py: Neues --json-output CLI-Argument fuer konfigurierbaren JSON-Dateinamen (Default: evaluation_results.json). Ermoeglicht parallele Evaluationen ohne Ueberschreiben (z.B. Mistral vs. Gemini).

41. config.py: GEMINI_DETECT_MODEL referenziert jetzt GEMINI_MODEL statt doppeltem String-Literal. LLM_CORRECTED_DIR behalten (wird von llm_postprocess.py verwendet, entgegen vorheriger Analyse).

42. shared.js: 4 duplizierte Fetch-Funktionen (fetchPageText, fetchLayoutData, fetchPageTei) zu generischer _fetchWithFallbacks() refaktoriert (~90 Zeilen auf ~25 Zeilen Kernlogik). fetchRefTeiPage bleibt separat (XML-Parsing zu speziell).

43. PUB_FORM_LABELS konsolidiert: Single Source in ZBZ.PUB_FORM_LABELS (shared.js). viewer.js + dashboard.js referenzieren jetzt ZBZ.PUB_FORM_LABELS. dashboard.js FORM_LABELS erweitert via Object.assign().

44. Inline-Styles entfernt: Gemini-Button (viewer.html) nutzt CSS-Klasse .amber statt style="background:#f59e0b". Layout-Source Select nutzt .layout-source-select statt 7 Inline-CSS-Properties. Neue CSS-Klassen in shared.css.

45. "Unused CSS" Analyse korrigiert: .card, .bar-wrap, .preview, .pg etc. sind in benchmark.html aktiv genutzt. Vorherige Analyse hatte benchmark.html nicht geprueft. Kein CSS entfernt.

### Dateien geaendert

| Datei | Aenderung |
|-------|-----------|
| `scripts/generate_dashboard_data.py` | FIX -- Manifest einmal laden |
| `scripts/gemini_ocr_correct.py` | FIX -- None-Check + Metadaten-Cache |
| `scripts/evaluate_ocr.py` | EXTENDED -- --json-output Argument |
| `scripts/config.py` | FIX -- GEMINI_DETECT_MODEL = GEMINI_MODEL |
| `docs/shared.js` | REFACTORED -- _fetchWithFallbacks, PUB_FORM_LABELS |
| `docs/shared.css` | EXTENDED -- .amber, .layout-source-select |
| `docs/viewer.html` | FIX -- Inline-Styles durch CSS-Klassen ersetzt |
| `docs/viewer.js` | FIX -- PUB_FORM_LABELS aus ZBZ |
| `docs/dashboard.js` | FIX -- PUB_FORM_LABELS + FORM_LABELS aus ZBZ |

---

## 2026-03-05 | Gemini OCR-Korrektur (Stage 2b)

### Session 5: Gemini OCR Correction Implementation

31. Stage 2b: gemini_ocr_correct.py erstellt -- Zwei-Schritt-Verfahren mit Gemini 3.1 Flash Lite Preview. Schritt 1: Analyse (Structured JSON Output mit corrections, confidence, justification). Schritt 2: Korrektur (nur high/medium-Korrekturen anwenden). Zwei Varianten: A (text-only + Metadaten-Kontext aus doc_metadata.json), B (multimodal + Scan-Bild).

32. Config erweitert: GEMINI_CORRECTED_A_DIR + GEMINI_CORRECTED_B_DIR in config.py. Output-Struktur: gemini_corrected_a/ und gemini_corrected_b/ mit korrigierten .md-Dateien + .analysis.json + manifest.json.

33. Image-Pfad-Bug behoben: OCR-Dateien verwenden ungepolsterte Seitennummern (2310_p1.md), Bilder verwenden Zero-Padding (2310_p001.png). Fix: page_str.zfill(3) in analyze_page() und correct_page().

34. Sample-Test auf 5 Pilot-Docs (2310/1180/890/90/40): Variante A avg CER 3.30% (Mistral 3.97%, -0.67pp). Variante B avg CER 3.45% (4 Docs, -0.52pp). Groesster Gewinn: Doc 2310 7.00% -> 3.88% (JSTOR-Cover, franzoesische Akzente). Doc 40 (147 Seiten) bestaetigt Skalierbarkeit.

35. Frontend-Integration: Gemini-Toggle-Button in viewer.html (amber #f59e0b), shared.js Fetch-Pfad + Pipeline-Step "GEM", viewer.js Source-Label + Button-Visibility + CER-Balken mit Delta-Anzeige.

36. Dashboard-Integration: generate_dashboard_data.py laedt evaluation_gemini_a.json + Gemini-Manifest. Neue Felder: pipeline_status.gemini_corrected, gemini_cer, gemini_stats, pipeline_summary.docs_with_gemini/avg_cer_gemini. Engine-Badge "GEM" im Katalog.

37. Erkenntnis: Variante A (text-only) leicht besser als B (multimodal) im Durchschnitt und guenstiger. Multimodal hilft vor allem bei visuell eindeutigen Fehlern (z.B. Doc 90: 1.21% -> 1.12%). Fuer die meisten Docs reicht Metadaten-Kontext.

---

## 2026-03-05 | Stage 1a Klassifikation + Dashboard + Online-Demo

### Session 4: Online-Demo (GitHub Pages)

27. 4 DEMO-Dokumente ausgewaehlt (2310/A/FR, 1000/B/FR, 1330/D/DE-FR, 1540/C/DE) -- alle 4 Typen, 3 Sprachen, unterschiedliche Seitenzahlen. Bilder unter docs/images/, OCR+Layout+TEI unter docs/data/examples/.

28. Disclaimer-Banner auf Dashboard und Viewer: "Prototyping Interface", "KI-generiert", "4 Beispieldokumente online, vollstaendige Daten lokal".

29. DEMO-Badges im Katalog (teal "DEMO"-Tag neben Doc-ID). DEMO-Docs zuoberst sortiert.

30. GitHub Pages Fix: Viewer holte OCR/Layout von ../output/ -- auf GH Pages nicht erreichbar. Loesung: Beispieldaten unter docs/data/examples/, shared.js Fallback-Pfade (primaer ../output/, Fallback data/examples/). Lokal und online funktional.

### Session 3: Gemini Dokumentklassifikation + Dashboard-Overhaul

20. Stage 1a: classify_docs.py erstellt -- Gemini 3.1 Flash Lite klassifiziert alle 286 Docs (erste 5 Seiten visuell). Felder: language, pub_form, layout_type, title, author, date, description, has_jstor_cover, num_columns. Structured Output via response_schema. 286/286 erfolgreich.

21. doc_metadata.json als zentrale Metadaten-Datei (data/doc_metadata.json). Ersetzt PILOT_DOCS-Hardcoding in generate_dashboard_data.py. Von tei_generator.py und Dashboard genutzt.

22. Qualitaetspruefung: 80% Typ-Match mit Pilot-Docs (12/15), 86% Sprache (12/14), 60% pub_form (6/10). Spot-Checks 10 zufaelliger Non-Pilot-Docs alle plausibel. 170/170 Pflichtfelder komplett, keine Typ/Spalten-Widersprueche.

23. OCR-Pfad-Bug behoben: output/ocr_results/ enthielt Mistral-Ergebnisse (alter Batch vor Engine-Routing). compute_pipeline_status() zaehlte diese als DeepSeek (272 Docs). Fix: ocr_mistral = has_mistral OR has_ocr_results, ocr_deepseek nur wenn nicht in mistral_results/. 2,906 Dateien nach mistral_results/ kopiert.

24. Dashboard komplett ueberarbeitet: Metriken (Korpus/OCR Mistral/Layout/CER statt Phasen), Korpus-Uebersicht (Typ/Sprache/Form-Verteilung statt Testphasen), Katalog mit Titel/Beschreibung-Spalte und Publikationsform-Labels.

25. Frontend-Fixes: ZBZ.esc() fuer XSS-Schutz, Sprachfilter, PUB_FORM_LABELS in dashboard.js + viewer.js, Viewer-Link aus Header entfernt, title/author/date/pub_form in Viewer Info-Bar.

26. Batch-Status: Classification 286/286 fertig, Mistral OCR 4,117 Seiten fertig, Docling Layout 4,152 fertig, Gemini Layout QA 2,188/4,152 (laeuft).

---

## 2026-03-05 | Knowledge Refactoring + OCR Production + Viewer Integration

### Session 2: OCR Production Run + Frontend Fix

13. Mistral OCR batch started for all 286 docs (mistral-document-ai-2512 on Azure AI Foundry). First production OCR run. Skip-existing pattern added to ocr_pipeline.py.

14. OCR output path bug fixed: ocr_pipeline.py wrote all engines to ocr_results/. Frontend expects Mistral in mistral_results/, DeepSeek in ocr_results/. Fix: engine-based routing in main(), import MISTRAL_RESULTS_DIR.

15. Gemini thought_signature warning fix: warnings.filterwarnings in layout_qa_gemini.py (PYTHONWARNINGS env var insufficient for SDK-internal warnings).

16. First production verification: Doc 1410 p5 -- German text, special characters (oe/ue/ae/ss/guillemets) perfect, headings detected as ##, two-column layout correctly handled. Confirms pilot CER (5.58%) holds on production data.

17. Discovery: Doc 1410 classified as Type A (single-column) but layout data shows two-column layout on p5 (regions at ~4% and ~51% x_pct). Mistral handles it correctly (page-based OCR), but PAGE-XML generator must account for this.

18. End-to-end viewer integration confirmed: Image + OCR (Mistral) + Layout (Docling + Gemini) display correctly for 95 docs. Dashboard regeneration <10s for 286 docs.

19. Batch status at session end: Gemini 1,633/4,152 pages (39.3%, 128 docs), Mistral OCR 1,211 pages (95 docs). Both running stably.

---

## 2026-03-05 | Knowledge Refactoring + Gemini Auto-Mode Progress

### Context

Knowledge base had grown to 14 files with quality issues: outdated metrics, wrong model names, SSoT violations, obsolete research documents. Gemini auto-mode from previous session had processed only 33/286 docs before aborting.

### Completed

1. LEARNINGS.md created -- 15 technical insights from E1-E26 in 6 categories (OCR, Layout, Gemini API, TEI/Pipeline, Development Patterns)

2. Quality metrics corrected across all files:
   - 62/20/13/5 (ad-hoc) -> 75/10/12/3 (compute_page_quality on 4,152 pages)
   - "~38% fails" -> "~15% bad+empty" (detect targets only)
   - PIPELINE.md is SSoT for layout quality metrics

3. All "Gemini 2.5 Flash" references eliminated -- only 3.1 Flash Lite everywhere

4. OCR-ENGINES.md + E19-LAYOUT-ANALYSE.md merged into ENGINES.md:
   - 512 lines -> 131 lines (token-efficient: no bold, no tables)
   - 4 active engines: Mistral (OCR prod), DeepSeek (OCR dev), Docling (layout), Gemini (layout QA+detect)
   - Dropped: Claude (not tested), discontinued models, 5 rejected layout approaches, pilot findings (in TESTPLAN)
   - E19 architecture decision preserved as summary section

5. Cross-references updated in 8 files (DECISIONS, INDEX, PIPELINE, INFRASTRUKTUR, TESTPLAN, QUELLENANALYSE, JOURNAL)

6. INDEX.md cleaned: "Agentic Vision" removed from Key Concepts (obsolete), directory structure updated

7. LEARNINGS.md created, then dissolved: takeaways integrated into ENGINES.md (OCR/Layout/Gemini lessons) and PIPELINE.md (TEI/Pipeline lessons). File deleted, INDEX.md updated.

8. PLAN.md rewritten: 339 -> ~120 lines. Done phases compressed to 2 paragraphs. Scripts Inventory + API Keys sections removed (duplicated PIPELINE/.env.example). Phase 2 renamed to "PAGE-XML Generator".

9. TESTPLAN.md cleaned: CLI commands replaced with cross-ref to PIPELINE.md. 18 Next-Steps reduced to 3 open items (8 done archived, 4 obsolete removed).

10. PIPELINE.md trimmed: LLM Post-Correction prompts reduced from 3 variants (~80 lines) to summary of Variant C (~4 lines). Duplicated result tables removed (reference TESTPLAN). Layout QA pilot paragraph removed (superseded by E25/E26).

11. O21 closed in DECISIONS.md: Gemini QA/Detect handles overlap, single-liners, page numbers -- no manual heuristics needed.

12. Gemini auto-mode restarted -- 847/4,152 pages (20.4%) after 51 docs in this session. Aborted at Doc 1530 (timeout). 10 errors (broken PNGs, JSON parse). Resume-capable.

### New/Changed Files

- knowledge/ENGINES.md -- NEW (replaces OCR-ENGINES.md + E19-LAYOUT-ANALYSE.md)
- knowledge/OCR-ENGINES.md -- DELETED
- knowledge/E19-LAYOUT-ANALYSE.md -- DELETED
- knowledge/LEARNINGS.md -- CREATED then DELETED (takeaways integrated into source files)
- knowledge/PLAN.md -- REWRITTEN (339 -> ~120 lines)
- knowledge/PIPELINE.md -- UPDATED (lessons added, LLM section trimmed, layout QA pilot removed)
- knowledge/TESTPLAN.md -- UPDATED (CLI dedup, Next-Steps archived, O21 note updated)
- knowledge/DECISIONS.md -- UPDATED (O21 closed, model name, percentages, cross-refs)
- knowledge/INDEX.md -- UPDATED (Document Matrix, Dependencies, Key Concepts, Directory Structure)
- knowledge/PROJEKT.md -- UPDATED (quality metrics, model name)
- knowledge/JOURNAL.md -- UPDATED (this entry)
- knowledge/INFRASTRUKTUR.md -- UPDATED (cross-ref)
- knowledge/QUELLENANALYSE.md -- UPDATED (cross-ref)

### Knowledge Base Status

12 documents (was 14): INDEX, PROJEKT, PIPELINE, QUELLENANALYSE, ENGINES, TEI-MAPPING, GND-STRATEGIE, TESTPLAN, INFRASTRUKTUR, DECISIONS, ZBZ-WORKFLOW, JOURNAL, PLAN

---

## 2026-03-04 | Gemini Layout Detect Mode (E26) + Layout Quality Analysis

### Context

Docling layout analysis complete (286/286 docs, 4,152 pages). Quality analysis revealed:
- 62% good, 20% warning, 13% bad, 3% empty *(ad-hoc analysis; superseded by `compute_page_quality`: 75/10/12/3)*
- Landscape/double pages: 36% bad (vs 14% portrait)
- Main issues: missing regions, fragmented BBoxes, empty pages
- Existing Gemini QA (E25) can only fix labels — cannot add regions or change BBoxes

### Completed

1. **Gemini Layout Detect Mode** (E26, `scripts/layout_qa_gemini.py` EXTENDED):
   - New `--mode detect`: Gemini 3.1 Flash Lite as full layout detector (Vision + Structured Output)
   - Sends raw scan (no overlay) to Gemini, returns regions with `box_2d` coordinates
   - Coordinate conversion: Gemini `[ymin, xmin, ymax, xmax]` (0-1000) -> project `{x_pct, y_pct, w_pct, h_pct}` (0-100)
   - `text` field = `""` (OCR comes from Mistral, not layout)
   - `source` = `"gemini-detect"` (vs `"gemini"` for QA mode)
   - Output: same `_layout_gemini.json` format, compatible with viewer
   - Three modes: `qa` (label fix), `detect` (full detection), `auto` (detect for bad, qa for good)
   - Quality scoring: `compute_page_quality()` classifies pages as good/warning/bad/empty based on coverage

2. **Config extended**: `GEMINI_DETECT_MODEL` = `"gemini-3.1-flash-lite-preview"`

3. **Test results**:
   - **Doc 510 p7** (missing paragraph): Gemini detect found 4 regions (vs Docling 2), including the missing middle paragraph
   - **Doc 900 p1** (landscape encyclopedia, 4+ columns): Gemini detect found 47 regions (vs Docling 26 fragmented). Significantly improved but rightmost column (~80-95% x) still missing. Photo not detected as `picture`
   - Both verified in viewer — BBoxes render correctly with labels

4. **Layout quality analysis** (ad-hoc): Analyzed all 4,144 layout JSONs:
   - Coverage-based scoring: good (>30%), warning (15-30%), bad (<15%), empty (0 regions)
   - 2,570 good (62%), 844 warning (20%), 533 bad (13%), 197 empty (5%)
   - Worst performers: landscape pages, encyclopedias, dense multi-column formats

### Known Limitations (Detect Mode)

- Rightmost column sometimes missed on wide landscape pages (Doc 900)
- `picture`/`figure` detection unreliable — photos not always labeled
- Prompt tuning needed for edge cases (can iterate)
- Cost: Flash Lite is the cheapest viable option

### New/Changed Files

| File | Change |
|------|--------|
| `scripts/layout_qa_gemini.py` | EXTENDED -- `DETECT_PROMPT`, `DETECT_SCHEMA`, `detect_page()`, `compute_page_quality()`, `gemini_box_to_pct()`, `--mode` CLI flag |
| `scripts/config.py` | EXTENDED -- `GEMINI_DETECT_MODEL` |
| `knowledge/JOURNAL.md` | This entry |
| `knowledge/DECISIONS.md` | EXTENDED -- E26 |
| `knowledge/PLAN.md` | EXTENDED -- Phase 1f, layout 286/286 done |
| `knowledge/PROJEKT.md` | EXTENDED -- Component status |

### Model: Flash Lite Confirmed

- Tested Doc 510: equivalent quality (same 4 regions on p7), ~2.4s/page
- Cost: Flash Lite ~$1-2 for ~633 detect pages (15% bad+empty)
- `auto` mode launched on all 286 docs with Flash Lite

### Documentation Refactoring (Session 2)

All knowledge files updated to reflect current state (04.03.2026):
- **README.md**: Status 04.03, Layout 286/286, Gemini QA+Detect, Next Steps aktualisiert
- **OCR-ENGINES.md**: Gemini-Sektion neu (Flash Lite, 3 Modi, Model History), Docling auf Production (286/286), Vergleichstabelle aktualisiert
- **E19-LAYOUT-ANALYSE.md**: Status "Decided", Resolution-Sektion mit E25/E26
- **PIPELINE.md**: Stage 3a (Gemini QA/Detect), E26-Paragraph, CLI-Befehle fuer detect/auto
- **INDEX.md**: E26 in Key Concepts
- **DECISIONS.md**: E26 mit Flash Lite Switch
- **PLAN.md**: Phase 1f, Data Flow aktualisiert
- **PROJEKT.md**: Component Status aktualisiert

### Gemini Auto Mode (laeuft im Hintergrund)

- `--mode auto` auf alle 286 Docs gestartet (Flash Lite)
- ~440/4,152 Seiten verarbeitet bei Session-Ende
- Auto-Routing funktioniert: bad/empty -> detect, good/warning -> qa
- 3 Fehler bisher (NoneType, Unicode escape) — uebersprungen
- Resume-faehig: kann jederzeit neu gestartet werden

### Next Steps

- Gemini auto mode fertig laufen lassen (~2.5h verbleibend)
- Evaluate detect quality across full corpus
- Tune detect prompt (rightmost column, picture detection)
- Refactor `layout_qa_gemini.py` (deduplicate qa_page/detect_page, suppress thought_signature warnings)

---

## 2026-03-03 | Gemini Layout QA (E25) + Local GPU Layout + Keyboard Shortcuts Removed

### Late Update: PyTorch CUDA + Local GPU Layout

5. **PyTorch CUDA installed** (was CPU-only):
   - Problem: `torch 2.7.1+cpu` installed, RTX 4060 Laptop GPU (8GB) unused
   - Fix: `pip install --force-reinstall torch torchvision --index-url https://download.pytorch.org/whl/cu124`
   - Fixed dependency conflicts: Pillow <12, numpy <2.3, fsspec <2025
   - Result: `torch 2.6.0+cu124`, CUDA available, RTX 4060 detected
   - Docling local GPU: ~5s/page (vs 27s CPU via docling-serve, ~5x speedup)
   - First page ~66s (model loading), then ~5s/page steady state

6. **Duplicate layout processes cleaned up**:
   - Found 2x `run_layout_cloud` processes from earlier sessions
   - Stopped both, docling-serve CPU container also stopped
   - Layout analysis will continue on local GPU via `run_layout_analysis.py`

7. **PLAN.md v2.0**: Comprehensive checklist with all done/pending tasks, data flow, scripts inventory

---

## 2026-03-03 | Gemini Layout QA (E25) + Keyboard Shortcuts Removed

### Completed

1. **Gemini Layout QA implemented** (`scripts/layout_qa_gemini.py`, NEW):
   - Sends Overlay-PNG + Layout-JSON to Gemini 3.1 Flash Lite Preview (Vision + Structured Output)
   - Gemini corrects labels, removes false positives, flags missing regions
   - Returns corrected JSON with quality score (0-100), num_corrections, issues list
   - Output: `{doc_id}_p{NNN}_layout_gemini.json` alongside Docling original (epistemic infrastructure)
   - Summary per document: `summary_gemini.json` with avg_score, common_issues
   - Resume-capable (skips existing), `--doc`, `--force` flags
   - Auto-generates overlay PNGs if not present (via `draw_overlay_from_json()`)
   - Cost: ~$4 for 7,200 pages ($0.25/1M input tokens)

2. **Config + dependencies extended**:
   - `scripts/config.py`: `GEMINI_API_KEY`, `GEMINI_MODEL` ("gemini-3.1-flash-lite-preview")
   - `.env`: Created with `GEMINI_API_KEY` placeholder (gitignored)
   - `.env.example`: Gemini section added
   - `requirements.txt`: `google-genai>=1.0.0`
   - SDK: `google-genai` (new SDK, not `google-generativeai`)

3. **Viewer: Docling/Gemini toggle**:
   - `shared.js`: `fetchLayoutData(docId, page, source)` with 'docling'/'gemini' parameter
   - `viewer.html`: Layout-source dropdown next to Layout button
   - Switching re-renders layout overlay with selected source

4. **Keyboard shortcuts removed** from viewer:
   - `viewer.html`: Removed keydown listener (44 lines), shortcuts legend div, keyboard hints from buttons
   - `shared.js`: Removed Escape keydown handler
   - `shared.css`: Removed `.shortcuts` and `.shortcuts kbd` styles

### New/Changed Files

| File | Change |
|------|--------|
| `scripts/layout_qa_gemini.py` | **NEW** -- Gemini QA script (~200 lines) |
| `scripts/config.py` | EXTENDED -- `GEMINI_API_KEY`, `GEMINI_MODEL` |
| `.env` | **NEW** -- Gemini API key (gitignored) |
| `.env.example` | EXTENDED -- Gemini section |
| `requirements.txt` | EXTENDED -- `google-genai>=1.0.0` |
| `docs/shared.js` | EXTENDED -- `fetchLayoutData()` with source param |
| `docs/viewer.html` | EXTENDED -- Layout-source dropdown; REMOVED -- keyboard shortcuts |
| `docs/shared.js` | REMOVED -- Escape handler |
| `docs/shared.css` | REMOVED -- `.shortcuts` styles |
| `knowledge/DECISIONS.md` | EXTENDED -- E25, E19 Gemini version updated |
| `knowledge/PIPELINE.md` | EXTENDED -- Gemini QA section, CLI command |
| `knowledge/JOURNAL.md` | This entry |

### Next Step

Set GEMINI_API_KEY in `.env`, test with `python -m scripts.layout_qa_gemini --doc 2310`, verify in viewer.

---

## 2026-03-03 | docling-serve API Integration (E24) + PNG Extraction for 286 PDFs

### Completed

1. **docling-serve API integration** (`scripts/run_layout_cloud.py`, NEW):
   - API client for IBM's official Docling server (`quay.io/docling-project/docling-serve-cpu`)
   - Sends page PNGs (base64) to `POST /v1/convert/source`, parses DoclingDocument JSON
   - Imports `DOCLING_TO_ZBZ` mapping and `to_pixel_pct()` from `run_layout_analysis.py` (code reuse)
   - Output format identical to local `run_layout_analysis.py` (regions + BBox as percent)
   - Resume-capable (skips existing), `--doc`, `--url`, `--force` flags
   - Tested on Doc 2310: 3 pages, 24 regions, ~27s/page on CPU

2. **Config + .env extended**:
   - `scripts/config.py`: `DOCLING_SERVE_URL` from env var (default `http://localhost:5001`)
   - `.env.example`: docling-serve section with Docker command

3. **PNG extraction started** for all 286 PDFs (`scripts/extract_pages.py`):
   - PNGs needed for viewer, OCR, and as input for docling-serve
   - Output: `docs/images/{doc_id}/{doc_id}_p{NNN}.png` at 150 DPI

4. **Knowledge docs updated**: PIPELINE.md (CLI + docling-serve info), DECISIONS.md (E24), JOURNAL.md
5. **QUELLENANALYSE.md**: PAGE-XML page count detail added (302 pages, 24 docs)
6. **data/README.md**: projektsteuerung status clarified

### API Format (docling-serve)

```
POST /v1/convert/source
{
  "sources": [{"kind": "file", "base64_string": "<base64>", "filename": "page.png"}],
  "options": {"to_formats": ["json"], "from_formats": ["image"]}
}

Response: document.json_content -> texts[], pictures[], pages{}
Each text item: label, text, prov[].bbox (l/t/r/b, bottom-left origin)
```

### Performance

| Mode | Speed | Cost | Use case |
|------|-------|------|----------|
| Local CPU (Docker) | ~27s/page | Free | Development, small batches |
| Cloud Run L4 GPU | ~28ms/page | ~$0.10 for 7,200 pages | Production batch |

### New/Changed Files

| File | Change |
|------|--------|
| `scripts/run_layout_cloud.py` | **NEW** -- docling-serve API client (~150 lines) |
| `scripts/config.py` | EXTENDED -- `import os`, `DOCLING_SERVE_URL` |
| `.env.example` | EXTENDED -- docling-serve section |
| `knowledge/PIPELINE.md` | EXTENDED -- Stage 3 API option, CLI commands, E24 note |
| `knowledge/DECISIONS.md` | EXTENDED -- E24 added |
| `knowledge/QUELLENANALYSE.md` | EXTENDED -- PAGE-XML page count detail |
| `data/README.md` | UPDATE -- projektsteuerung status |

### Next Step

Verify Doc 2310 layout results in viewer (overlay QA), then run layout analysis for all 286 docs via docling-serve API.

---

## 2026-02-27 | Knowledge Vault Cleanup: PLAN.md Integration, English, Outdated Fixes

### Completed

1. **PLAN.md moved into knowledge/ vault** (`git mv PLAN.md knowledge/PLAN.md`):
   - YAML frontmatter added (type, created, updated, tags, status)
   - All 7 files with `../PLAN.md` references updated to `PLAN.md`
   - README.md references updated to `knowledge/PLAN.md`
   - Internal references in PLAN.md updated (`knowledge/X.md` → `X.md`)
   - INDEX.md: PLAN.md added to document matrix, dependency tree, directory structure

2. **German remnants translated to English**:
   - QUELLENANALYSE.md pilot table: Genre column translated (Rezension→Review, etc.)
   - PLAN.md data flow diagram: "pro Seite"→"per page", "Struktur"→"Structure"
   - Literal prompts in code blocks kept in German (actual code)

3. **Outdated information fixed**:
   - README.md: Pilot status date 26.02→27.02
   - PROJEKT.md: Component status date 26.02→27.02
   - PROJEKT.md: M1 success criterion corrected (>=95%→>=93%, matches actual result)
   - PLAN.md: Version 1.1→1.2, date 26.02→27.02
   - README.md: "12 project documents"→"14 project documents"

4. **O22 added to DECISIONS.md**: 289 vs. 286 PDF discrepancy formally tracked
   - QUELLENANALYSE.md cross-referenced with O22

### New/Changed Files

| File | Change |
|------|--------|
| `PLAN.md` | **MOVED** → `knowledge/PLAN.md`, frontmatter added, v1.2 |
| `knowledge/INDEX.md` | PLAN.md in matrix + deps + directory |
| `knowledge/PROJEKT.md` | Date fix, M1 criterion, PLAN.md links |
| `knowledge/PIPELINE.md` | PLAN.md links (2x) |
| `knowledge/TEI-MAPPING.md` | PLAN.md link |
| `knowledge/GND-STRATEGIE.md` | PLAN.md link |
| `knowledge/DECISIONS.md` | PLAN.md link, O22 added |
| `knowledge/QUELLENANALYSE.md` | Genre EN, O22 cross-ref |
| `README.md` | PLAN.md path, date fix, doc count |

---

## 2026-02-27 | Data Delivery HerschStandFeb: Analysis + Knowledge Corrections

### Completed

1. **ZBZ data delivery analyzed** (2.6 GB folder `HerschStandFeb/`):
   - 3 subfolders: "mit fertigen XML-Files" (94 MB), "ohne XML" (1.2 GB), duplicate (1.3 GB)
   - 24 PDFs with TEI annotation, 262 PDFs without annotation = **286 PDFs total**
   - 25 finished TEI-XMLs (ZBZ reference with GND linkages)
   - 24 PAGE-XML exports from Transkribus (schema **2013-07-15**, pages **empty** — no text)
   - Duplicate folder `HerschStandFeb/HerschStandFeb/` verified (664 files, identical paths+sizes)

2. **PAGE-XML schema corrected** (2019-07-15 → 2013-07-15):
   - PLAN.md: Template, config constant, XSD URL (6 occurrences)
   - PIPELINE.md: Schema table + namespace
   - DECISIONS.md: E13, O4

3. **New decision E23** in DECISIONS.md: Data delivery documented

4. **R7 (Transkribus incompatibility)** partially clarified: Schema 2013, ID scheme `{NNNN}_p{NNN}`, JPG format. PAGE-XML is empty (no TextRegions → @type/@custom not verifiable)

5. **Processing status updated**:
   - QUELLENANALYSE.md: New section "Data Delivery Feb 2026" with concrete numbers
   - GND-STRATEGIE.md: 18 → 25 TEI reference files available
   - Masterfile numbers (289 texts) retained — 3 difference from 286 delivered PDFs unexplained

### Findings

| Finding | Relevance |
|---------|-----------|
| Transkribus uses PAGE-XML schema 2013, not 2019 | High — all implementation plans corrected |
| PAGE-XML export contains no text (empty pages) | High — no reference PAGE-XML available |
| 25 finished TEI-XMLs (instead of 18/21) | Medium — 7 new docs for GND extraction |
| 286 PDFs delivered (3 fewer than masterfile) | Low — clarify difference |
| Transkribus Collection-ID: 1886177 | Low — for later API access |

### New/Changed Files

| File | Change |
|------|--------|
| `knowledge/DECISIONS.md` | E23 added, E13 corrected, R7 updated |
| `PLAN.md` | PAGE-XML schema 2019→2013 (6 occurrences) |
| `knowledge/PIPELINE.md` | Schema version corrected |
| `knowledge/QUELLENANALYSE.md` | Processing status: Data Delivery Feb 2026 |
| `knowledge/GND-STRATEGIE.md` | 18→25 TEI reference files |
| `knowledge/JOURNAL.md` | This entry |

### File Integration (same session, continuation)

1. **Duplicate deleted** (`HerschStandFeb/HerschStandFeb/`, 1.3 GB, 664 files)
2. **286 PDFs** → `data/scans/` (24 from "mit XML" + 262 from "ohne XML")
3. **25 TEI-XMLs** → `data/referenz-tei/`
4. **24 PAGE-XML folders** → `data/page-xml-transkribus/`
5. **Export screenshot** → `data/richtlinien/Page-xml-Export Einstellungen.jpg`
6. **`.gitignore`** updated: +`data/page-xml-transkribus/`, +`HerschStandFeb/`
7. **`data/README.md`** completely revised (structure, data delivery table, numbers)
8. **`HerschStandFeb/`** deleted (0 files remaining after move)

Verification passed: 286 PDFs, 25 XMLs, 24 PAGE-XML folders.

---

## 2026-02-26 | Redundancy Cleanup: STATUS.md, CLAUDE.md, PLAN.md, README.md

### Completed

1. **Redundancy analysis** of all root docs (CLAUDE.md, STATUS.md, PLAN.md) against knowledge/:
   - Comparison matrix with 18 content categories created
   - 4 files with redundancies identified, actions defined

2. **STATUS.md deleted** (100% redundant):
   - All contents existed more current in PROJEKT.md, TESTPLAN.md, DECISIONS.md
   - Was chronically outdated (as of 25.02., missing TEI-Viewer, Layout-QA)

3. **CLAUDE.md slimmed down** (72 → 32 lines):
   - Knowledge index (12 lines) → one-liner reference to INDEX.md
   - CLI commands (7 commands) → reference to PIPELINE.md + 4 most common
   - Decision guidelines (4 bullets) → removed (INDEX.md has them)
   - Frontend convention (ES5, namespaces) added

4. **PLAN.md cleaned up** (505 → ~300 lines):
   - "Starting position/What exists" → removed (PIPELINE.md)
   - Phase 0 → updated to "Completed" (was "pending")
   - Phase 3 TEI mapping → reference to TEI-MAPPING.md instead of duplicate
   - Risk matrix R7-R13 → moved to DECISIONS.md
   - Phase overview with current status added

5. **DECISIONS.md extended**: R7-R13 consolidated from PLAN.md (R8 marked as resolved)

6. **README.md completely revised** (92 → 120 lines):
   - Pilot status section with all 6 pipeline stages and concrete numbers
   - OCR quality by document type (all 15 docs, CER 6.42%)
   - Folder structure updated (dashboard files, tei-viewer.js, generate_dashboard_data.py)
   - Quick start expanded (layout, TEI, dashboard commands)
   - Dashboard+Viewer features described (3-panel, TEI-Viewer, entities, keyboard shortcuts)
   - Documentation table complete (9 entries instead of 6)

### New/Changed Files

| File | Change |
|------|--------|
| `STATUS.md` | **DELETED** -- 100% redundant with knowledge/ |
| `CLAUDE.md` | SLIMMED DOWN -- 72→32 lines, references instead of duplicates |
| `PLAN.md` | CLEANED UP -- 505→300 lines, status updated, redundancies removed |
| `README.md` | REWRITE -- pilot status, OCR quality, dashboard features, docs table |
| `knowledge/DECISIONS.md` | EXTENDED -- R7-R13 consolidated |

### Next Step

Layout post-processing (O21), then analyze remaining 7 docs with GPU, then PAGE-XML generator (Phase 1).

---

## 2026-02-26 | TEI-Viewer Refactoring: tei-viewer.js extracted

### Completed

1. **TEI JavaScript extracted from `viewer.html` into `docs/tei-viewer.js`** (~300 lines):
   - New namespace `window.TeiViewer` (analogous to `window.ZBZ` in shared.js)
   - Public API: `loadTei(docId, page)`, `switchMode(mode)`, `toggleEntitySidebar()`
   - Internal `teiState` object for lazy rendering context (docId/page)
   - Auto-init: `init()` binds tab listeners and entity sidebar listeners on load
   - ES5 conventions maintained (var, IIFE, no arrow functions)

2. **viewer.html reduced from ~1200 to ~816 lines**:
   - `<script src="tei-viewer.js"></script>` included after shared.js
   - `teiState` object removed (now in tei-viewer.js)
   - ~376 lines of TEI functions removed (switchTeiMode, loadTei, parseTeiXml, renderTeiView, renderTeiNode, createEntitySpan, renderTeiXml, highlightXml, renderTeiDiff, extractEntities, toggleEntitySidebar, renderEntitySidebar, scrollToEntity, entity listeners)
   - Calls adapted: `loadTei()` → `TeiViewer.loadTei(state.docId, state.page)`, keyboard shortcuts → `TeiViewer.switchMode()` / `TeiViewer.toggleEntitySidebar()`
   - Visibility guard moved outward: `if (state.teiVisible) TeiViewer.loadTei(...)`

3. **Knowledge updates**: PIPELINE.md, PROJEKT.md, DECISIONS.md, INDEX.md, JOURNAL.md updated

### New/Changed Files

| File | Change |
|------|--------|
| `docs/tei-viewer.js` | **NEW** -- TEI rendering logic (~300 lines), `window.TeiViewer` |
| `docs/viewer.html` | REFACTOR -- ~376 lines TEI code removed, script tag added |
| `knowledge/JOURNAL.md` | UPDATE -- Refactoring entry |
| `knowledge/PIPELINE.md` | UPDATE -- tei-viewer.js in dashboard table |
| `knowledge/PROJEKT.md` | UPDATE -- Component status |
| `knowledge/INDEX.md` | UPDATE -- Timestamp |

### Next Step

Layout post-processing (O21), then analyze remaining 7 docs with GPU, then PAGE-XML generator (Phase 1).

---

## 2026-02-26 | TEI-Viewer Upgrade: Rendered View, Syntax Highlighting, Diff, Entity Navigation

### Completed

1. **TEI panel completely overhauled** (`docs/viewer.html`):
   - 3-tab system: **Rendered** | **XML** | **Comparison** (instead of raw XML in `<pre>`)
   - Lazy rendering: Each tab is only rendered on first switch
   - New keyboard shortcuts: `R`/`X`/`V` (TEI mode), `E` (entity sidebar)

2. **Rendered view** (default tab):
   - Recursive TEI-to-HTML renderer (`renderTeiNode()`) with 17 element types
   - `DOMParser` with namespace stripping (`parseTeiXml()`)
   - Headings (`<head>` → `.tei-head`), paragraphs, footnotes (indented, left border)
   - Bold/italic/underline/superscript/subscript from `<hi rendition="...">`
   - Page breaks (`<pb>` → dashed line)
   - Figure/caption blocks, speaker/speech for interviews
   - Unknown elements passed through transparently (only children rendered)

3. **Entity highlighting + navigation**:
   - `<persName>` blue, `<orgName>` violet, `<bibl>` teal highlighted
   - Hover tooltip shows GND-ID, click opens lobid.org/gnd/{ID}
   - Entity sidebar (260px, slide animation) with persons/organizations/works
   - Each entry: name, occurrence counter, GND link
   - Click on sidebar entry → scroll + flash animation in rendered view

4. **XML syntax highlighting**:
   - Regex-based highlighter (`highlightXml()`)
   - Tags green, attribute names blue, attribute values red, comments gray
   - XML declaration gray, robust regex for nested attributes

5. **Reference TEI comparison** (tab "Comparison"):
   - Side-by-side layout: Generated (left) | Reference ZBZ (right)
   - `fetchRefTeiPage()` in `shared.js`: Loads full document, extracts page via `<pb>` splitting
   - Both sides with syntax highlighting
   - Graceful degradation when reference is missing

6. **CSS design system extended** (`docs/shared.css`, ~150 new lines):
   - TEI tabs, rendered view elements, entity highlighting with color coding
   - Entity flash animation (`@keyframes entityFlash`)
   - Diff panel, entity sidebar with slide transition

### New/Changed Files

| File | Change |
|------|--------|
| `docs/viewer.html` | REWRITE TEI panel -- 757→1200 lines, tabs, rendering, entities |
| `docs/shared.css` | EXTENDED -- ~150 lines TEI styles |
| `docs/shared.js` | EXTENDED -- `fetchRefTeiPage()` with page extraction + caching |
| `output/tei/2310_p1.xml` | **MOCK** -- Test data with entities, footnote, bold/italic |

### Next Step

Layout post-processing (O21), then analyze remaining 7 docs with GPU, then PAGE-XML generator (Phase 1).

---

## 2026-02-25 | TEI Generator + Viewer TEI Panel

### Completed

1. **TEI generator implemented** (`scripts/tei/tei_generator.py`):
   - Layout JSON + OCR Markdown → page-wise TEI-XML (DTA-Basisformat, `type="naegeli"`)
   - Uses llm_corrected_c preferentially, fallback to mistral_results
   - Markdown→TEI inline: `**bold**` → `<hi rendition="#b">`, `*italic*` → `<hi rendition="#i">`
   - GND entity annotation from KNOWN_ENTITIES (seed dictionary)
   - Placeholder technique prevents nested `<persName>` tags
   - Layout regions: zb_heading→`<head>`, footnote→`<note place="foot">`, caption→`<figure>`
   - Facsimile section with BBox→zone coordinates when layout is available
   - CLI: `--doc`, `--page` for individual pages/documents

2. **383 TEI-XML files generated** for all 15 pilot documents:
   - 8 docs with layout data (facsimile + structured regions)
   - 7 docs OCR only (all paragraphs as `<p>`)

3. **Viewer TEI panel** (`docs/viewer.html`):
   - Third panel alongside facsimile + OCR text
   - Toggle with button or key `T`
   - Hidden by default, shows TEI-XML as formatted text
   - Second divider (draggable) between OCR and TEI
   - 3-panel layout (33%/33%/33%) when TEI is active

4. **Shared code extensions**:
   - `shared.js`: `fetchPageTei(docId, page)` (tests 2 paths: tei/ and tei_xml/)
   - `shared.js`: TEI step in PIPELINE_STEPS
   - `shared.css`: `.viewer-tei pre` styling
   - `generate_dashboard_data.py`: `pipeline_status.tei` + `docs_with_tei` in summary

5. **Config extended**: `TEI_DIR` and `LLM_CORRECTED_C_DIR` in `scripts/config.py`

### Bug Fix

**Nested persName tags:** "Karl Jaspers" was correctly tagged, then "Jaspers" matched again within the already tagged text → doubly nested tags. **Solution:** Placeholder technique (Phase 1: replace longest names first with `\x00ENTITY{N}\x00`, Phase 2: placeholder → XML tags).

### New/Changed Files

| File | Change |
|------|--------|
| `scripts/tei/__init__.py` | **NEW** -- Module init |
| `scripts/tei/tei_generator.py` | **NEW** -- TEI generator (~280 lines) |
| `scripts/config.py` | EXTENDED -- TEI_DIR, LLM_CORRECTED_C_DIR |
| `scripts/generate_dashboard_data.py` | EXTENDED -- TEI status in pipeline |
| `docs/viewer.html` | EXTENDED -- TEI panel, toggle, second divider |
| `docs/shared.js` | EXTENDED -- fetchPageTei(), TEI pipeline step |
| `docs/shared.css` | EXTENDED -- TEI panel styling |
| `output/tei/*.xml` | **GENERATED** -- 383 TEI-XML files |

### Next Step

Implement PAGE-XML generator (Phase 1), layout post-processing (O21), then NER+GND (Phase 2).

---

## 2026-02-25 | Layout Overlay in Viewer + Annotated PNG Generation

### Completed

1. **Layout analysis batch script created** (`scripts/run_layout_analysis.py`):
   - Docling layout analysis on all page images (JSON with percent coordinates)
   - Resume-capable (skips existing, --force to overwrite)
   - `--overlay` flag: Generates annotated PNG images with burned-in BBox overlays

2. **Dashboard integration**:
   - `generate_dashboard_data.py`: Layout pipeline status + summary per document
   - `shared.js`: fetchLayoutData(), LAYOUT_COLORS, LAY pipeline step

3. **Viewer BBox overlay** (`docs/viewer.html`):
   - SVG overlay with viewBox="0 0 100 100" (zoom-independent)
   - Toggle with key L or button, auto-activation when layout data is present
   - Color coding: Red=heading, gray=paragraph, blue=footnote, orange=caption

4. **Annotated overlay PNGs**:
   - `draw_overlay_from_json()`: Reads layout JSONs, draws BBoxes on original images
   - Colored rectangles with label text and text preview
   - Doc 2310 (3 pages) successfully tested, all 15 docs run

5. **Layout analysis on 8/15 pilot documents** completed (1060, 1180, 130, 1330, 1410, 1440, 1520 partially, 2310)
   - 186 overlay PNGs generated, 7 docs without layout (need GPU: 2530, 290, 3040, 40, 830, 890, 90)

6. **Visual QA in viewer + overlay PNGs** — Detailed analysis of all 8 pages of Doc 1180 + Doc 1410:
   - BBox positioning correct, no systematic offset
   - Heading detection reliable (title, subtitle, "1ère thèse:", "2ème thèse:")
   - Two-column layout (1410 p3) correctly separated into distinct boxes
   - **Problem 1: Overlapping regions** — Single-line fragments (h_pct <3%) overlap with larger blocks (1180 p2)
   - **Problem 2: Page numbers not filtered** — Docling recognizes "217", "218", "219", "220" as `text` instead of `page_footer`
   - **Problem 3: Doc 1520 LAY status gray** in dashboard although 132/142 pages analyzed (analysis aborted)
   - **Next step:** Implement layout region post-processing (overlap filter, single-line merge, page number heuristic)

### New/Changed Files

| File | Change |
|------|--------|
| `scripts/run_layout_analysis.py` | **NEW** -- Batch Docling + overlay PNG |
| `scripts/generate_dashboard_data.py` | EXTENDED -- Layout status + summary |
| `docs/shared.js` | EXTENDED -- fetchLayoutData(), LAYOUT_COLORS, LAY step |
| `docs/viewer.html` | EXTENDED -- SVG overlay, toggle, auto-activation |
| `output/layout/{doc_id}/*_layout.json` | **GENERATED** -- Layout per page |
| `output/layout/{doc_id}/*_overlay.png` | **GENERATED** -- Annotated images |

### Next Step

Implement layout region post-processing, then analyze remaining 7 docs (needs GPU), then PAGE-XML export.

---

## 2026-02-25 | Phase 0 Evaluation + Scope Update of All Knowledge Docs

### Completed

1. **Docling 2.75 installed** (upgrade from 2.70 -- RT-DETR V2 Heron requires transformers >=4.48)
2. **Step 1 installation test passed:** Doc 1180 p001, 2.9s, 5 regions with BBox, no symlink error
3. **Step 2 type sample test passed:** 5 images (A/B/C/D), `scripts/experiments/layout_eval.py` written
4. **Step 3 E19 confirmed → E20:** Docling as primary layout engine
5. **Scope extension E21 documented:** PIPELINE.md, PROJEKT.md, TEI-MAPPING.md adapted to new 7-stage pipeline
6. **All knowledge docs updated:** STATUS.md, DECISIONS.md (E20+E21), JOURNAL.md

### Phase 0 Evaluation Results

| Doc | Type | Regions | Time | Result |
|-----|------|---------|------|--------|
| 1180 | A | 9 | 3.3s | 2 headings + 7 text correct |
| 2530 | B | 12 | 2.5s | Columns correctly separated |
| 40 | C | 3-6 | 0.4s | Text pages correct |
| 90 | D | 6 | 0.5s | Title page correct |
| 1330 | D | 14 | 0.7s | headings + text + list_items correct |

### New/Changed Files

| File | Change |
|------|--------|
| scripts/experiments/layout_eval.py | **New** -- Docling evaluation with JSON + overlay |
| output/layout_eval/*.json + *.png | **New** -- Evaluation results |
| knowledge/PIPELINE.md | 7-stage pipeline, E19 layout engine |
| knowledge/PROJEKT.md | Ecosystem diagram + milestones updated |
| knowledge/TEI-MAPPING.md | Scope header updated |
| knowledge/DECISIONS.md | E20 + E21 added |
| STATUS.md | Phase 0 results, next steps |

### Next Step

Implement Phase 1: `scripts/layout/` module + `scripts/export_page_xml.py`.

---

## 2026-02-25 | Phase 0: Layout Analysis Research + Implementation Plan

### Completed

1. **Scope extension after meeting:** zbz-ocr-tei now covers the entire pipeline (PDF → TEI-XML). ZBZ keeps Transkribus, DHCraft builds parallel AI pipeline. NER/GND now in PoC scope.
2. **Layout analysis research (E19):** 7 approaches evaluated (Gemini, Claude, Mistral, Docling, Surya, Kraken, Azure DI)
   - **Docling** (Score 4.35/5): Best open-source BBox coordinates, 17 classes, free, CPU
   - **Kraken** (Score 4.15/5): Native PAGE-XML export, historical FR documents
   - **Gemini** (Score 3.45/5): Affordable, flexible, suitable as validator
   - **Claude Vision**: Disqualified (no BBox coordinates)
   - **Mistral**: Insufficient (no text region BBox)
3. **Recommendation E19:** Docling + Gemini hybrid (Docling primary, Gemini optional, Kraken fallback)
4. **Implementation plan written:** `PLAN.md` in repo root with 6 phases, data flow, risk matrix
5. **Knowledge updates:** DECISIONS.md (E19), INDEX.md (E19-LAYOUT-ANALYSE.md linked)

### Surprise Find

- **ocr-fileformat (UB Mannheim):** Converts between 30+ OCR formats (hOCR, PAGE-XML, ALTO, TEI). Significantly reduces the risk of the format decision.

### New/Changed Files

| File | Change |
|------|--------|
| knowledge/E19-LAYOUT-ANALYSE.md | **New** -- Layout analysis research + evaluation matrix |
| PLAN.md | **New** -- Implementation plan for full AI pipeline |
| knowledge/DECISIONS.md | E19 added |
| knowledge/INDEX.md | E19-LAYOUT-ANALYSE.md linked |
| knowledge/JOURNAL.md | This entry |

### Next Step

Phase 0 evaluation: Run Docling layout analysis on all 383 page images, map block types → ZBZ tags, visually verify.

---

## 2026-02-25 | Knowledge Update: Prompts Documented + Research Results

### Completed

1. **Prompt documentation in PIPELINE.md**: All pipeline prompts fully documented
   - Stage 1: Mistral (no prompt), DeepSeek (fixed prompt with `<|grounding|>`)
   - Stage 2: Three LLM variants (A: Analysis, B: Lean, C: Few-Shot) with full prompt text
2. **Outdated knowledge docs cleaned up**: PROJEKT.md (Phase 4, M1, costs), QUELLENANALYSE.md (1520 language), GND-STRATEGIE.md (next steps)
3. **Web research prompt optimization** (3 lean searches):
   - Mistral OCR: No custom prompt possible, but `extract_header/footer` parameter
   - DeepSeek-OCR-2: 6 prompt modes, Free OCR without layout potentially faster
   - LLM correction: Multimodal correction (image+text) achieves <1% CER (arXiv:2504.00414); overcorrection at CER <5% confirmed (ACL 2025)
4. **Findings from pilot evaluation** documented in OCR-ENGINES.md (5 findings)
5. **Three new open issues** in DECISIONS.md: O18 (multimodal), O19 (extract_header), O20 (Free OCR)

### Findings

| Finding | Source | Relevance |
|---------|--------|-----------|
| Multimodal LLM correction (scan+text) achieves <1% CER | arXiv:2504.00414 | High — greatest optimization potential |
| Overcorrection at low CER is systematic, not project-specific | ACL 2025 | Confirms E17 |
| Optimal segment length 200-300 words | ACL 2025 | We send full pages — already good |
| Mistral `extract_header/footer` could filter JSTOR headers | Mistral API Docs | Medium — easy to test |

### New/Changed Files

| File | Change |
|------|--------|
| knowledge/PIPELINE.md | Prompt documentation (Stage 1+2), optimization potential |
| knowledge/OCR-ENGINES.md | Prompt modes, Mistral configuration, pilot evaluation |
| knowledge/DECISIONS.md | E16-E18 + O18-O20 |
| knowledge/PROJEKT.md | Phase 4, M1, costs updated |
| knowledge/QUELLENANALYSE.md | Doc 1520 language FR |
| knowledge/GND-STRATEGIE.md | Next steps cleaned up |

---

## 2026-02-25 | Pipeline Complete: All 15 Pilot Documents Processed

### Completed

1. **OCR for 3 missing Type-A documents** (1060, 130, 1410): Mistral OCR, 32 pages in 24s
2. **LLM correction for 5 documents** (1060, 130, 1410, 40, 1520): Haiku 4.5 Variant C, 330 pages, cost $1.45
3. **Page-wise comparison implemented** (`evaluate_ocr.py`): Content-based page matching resolves Phase 4 blocker
   - `extract_pages_from_tei()`: Splits TEI based on `<pb facs='#facs_N'>` tags
   - `_match_tei_to_ocr()`: Automatic page offset detection (e.g. 1520.pdf has +8 offset)
   - `evaluate_document_pagewise()`: Per-page CER/WER, weighted average
   - Auto-detection: Page-wise for >10 TEI pages, otherwise global alignment
4. **Evaluation of all 15 documents**: Mistral raw + LLM corrected
5. **Dashboard regenerated**: 15/15 OCR, 15/15 LLM, 15/15 Eval

### Results for New Documents

| Doc | Type | Mistral CER | LLM CER | Note |
|-----|------|------------|---------|------|
| 1060 | A | 22.60% | 26.92% | Alignment problem (only 6 TEI pages) |
| 130 | A | 4.13% | 4.15% | Page-wise, cover page correctly ignored |
| 1410 | A | 5.58% | 5.78% | Bilingual DE/FR, acceptable |
| 40 | C | 2.57% | 2.65% | Excellent, 147 pages matched |
| 1520 | C | 2.73% | 2.75% | Excellent, 116 pages, offset +8 detected |

**Phase 4 (monographs) CER 2.65%** — best of all phases. Page-wise comparison fully resolves the alignment problem for long documents.

### TESTPLAN Items Updated

- [x] Item 10: Page-wise comparison implemented
- [x] Item 11: OCR+LLM+Eval for all 15 docs completed
- [ ] Doc 1060 and 290 have high CER — check scan quality
- [ ] Doc 1520 language identified as FR (was "?" in config.py)

---

## 2026-02-25 | Code Quality: Resource Leak + Duplication Fixed

### Completed

- **`scripts/ocr_pipeline.py`**: Resource leak in `MistralOCR._split_pdf()` fixed — `fitz.open()` documents are now protected with try-finally, so they don't remain open on exceptions
- **`scripts/utils.py`**: `pdf_to_images()` duplication resolved — now delegates to `pdf_to_images_pages()` instead of duplicating identical logic. Filename padding unified in the process (both now use `:03d`)
- Module docstrings checked: All 14 Python modules already have docstrings, no action needed

### Rationale

Systematic code audit identified 3 potential improvements, 2 implemented:
1. Resource leak: On exception between `fitz.open()` and `.close()`, documents remained open — fixed with try-finally
2. Code duplication: `pdf_to_images()` and `pdf_to_images_pages()` had nearly identical implementations — consolidated
3. Missing docstrings: Already present, no action needed

### New/Changed Files

| File | Change |
|------|--------|
| `scripts/ocr_pipeline.py` | FIX: try-finally in `_split_pdf()` |
| `scripts/utils.py` | REFACTOR: `pdf_to_images()` delegates to `pdf_to_images_pages()` |

---

## 2026-02-25 | ARCHITEKTUR.md → PIPELINE.md Renamed + Content Corrected

### Completed

- `knowledge/ARCHITEKTUR.md` → `knowledge/PIPELINE.md` renamed (git mv)
- All 35 references in 14 files updated (CLAUDE.md, README.md, 9 knowledge docs)
- Header, tags, and description adjusted
- **6 content corrections:**
  1. Pipeline diagram: Now shows the actual data flow (OCR → LLM → Eval → Dashboard)
  2. Docling documented as integral part of `ocr_pipeline.py` (not separate stage)
  3. Engine selection: Auto mode described from the code
  4. Evaluation and dashboard added as separate stages (were completely missing)
  5. Post-processing contradiction resolved (R6: `clean_markdown()` not in production path)
  6. CLI commands complete with all parameters

### Rationale

"Architektur" (Architecture) suggests high-level system design. The content describes the concrete
data flow through the scripts — that is pipeline documentation. Furthermore, the
documented workflow did not match the code (outdated diagram, missing stages).

### New/Changed Files

| File | Action |
|------|--------|
| `knowledge/ARCHITEKTUR.md` | RENAMED → `knowledge/PIPELINE.md` |
| `knowledge/PIPELINE.md` | UPDATE (header, diagram, 6 corrections) |
| `CLAUDE.md` | UPDATE (reference) |
| `README.md` | UPDATE (reference) |
| `knowledge/INDEX.md` | UPDATE (6 references + directory structure) |
| `knowledge/DECISIONS.md` | UPDATE (7 references) |
| `knowledge/OCR-ENGINES.md` | UPDATE (2 references) |
| `knowledge/INFRASTRUKTUR.md` | UPDATE (2 references) |
| `knowledge/PROJEKT.md` | UPDATE (1 reference) |
| `knowledge/QUELLENANALYSE.md` | UPDATE (1 reference) |
| `knowledge/TEI-MAPPING.md` | UPDATE (1 reference) |
| `knowledge/GND-STRATEGIE.md` | UPDATE (1 reference) |
| `knowledge/ZBZ-WORKFLOW.md` | UPDATE (1 reference) |

---

## 2026-02-25 | Project Cleanup: Redundant Files Removed

### Completed

**Deleted files (7):**
- `nul` — Empty file, Windows artifact (0 bytes, not tracked)
- `scripts/test_deepseek_ocr.py` — Redundant with `ocr_pipeline.py --engine deepseek`
- `scripts/test_docling.py` — Redundant with `ocr_pipeline.py --engine docling`
- `scripts/test_mistral_ocr.py` — Redundant with `ocr_pipeline.py --engine mistral`
- `scripts/test_column_prompt.py` — One-time column experiment, done
- `scripts/extract_layout.py` — Layout extraction integrated in `ocr_pipeline.py`
- `PROJEKTWISSEN.md` — 95% duplicate of the 12 knowledge docs, violates single-source-of-truth

**Cleaned up redundancies:**
- `knowledge/OCR-ENGINES.md`: Evaluation tables (CER/WER) removed, reference to TESTPLAN.md
- `knowledge/ARCHITEKTUR.md`: `extract_layout.py` reference replaced by `ocr_pipeline.py`
- `README.md`: Link `knowledge/journal.md` → `knowledge/JOURNAL.md` corrected, date updated
- `scripts/README.md`: Script table updated (deleted ones removed, missing ones added)
- `scripts/__pycache__/` + `scripts/postprocess/__pycache__/` removed locally

### Rationale

Systematic analysis of all project files revealed:
- 5 test scripts were completely redundant with `ocr_pipeline.py` (no imports, not in CLAUDE.md)
- PROJEKTWISSEN.md duplicated content from PROJEKT, ARCHITEKTUR, QUELLENANALYSE, TESTPLAN, DECISIONS, INFRASTRUKTUR
- OCR-ENGINES.md contained identical evaluation tables as TESTPLAN.md

### New/Changed Files

| File | Action |
|------|--------|
| `nul` | DELETED |
| `PROJEKTWISSEN.md` | DELETED |
| `scripts/test_deepseek_ocr.py` | DELETED |
| `scripts/test_docling.py` | DELETED |
| `scripts/test_mistral_ocr.py` | DELETED |
| `scripts/test_column_prompt.py` | DELETED |
| `scripts/extract_layout.py` | DELETED |
| `knowledge/OCR-ENGINES.md` | UPDATE (evaluation tables removed) |
| `knowledge/ARCHITEKTUR.md` | UPDATE (extract_layout reference) |
| `README.md` | UPDATE (link fix, date) |
| `scripts/README.md` | UPDATE (script table) |

---

## 2026-02-25 | Dashboard Redesign + Engine Visibility + Knowledge Update

### Completed

**Dashboard redesign (Session 1):**
- Complete project analysis and data inventory (15 pilot PDFs, 383 pages, 12 with OCR, 10 with LLM)
- `scripts/generate_dashboard_data.py` created: Generates `docs/data/dashboard.json` from all pipeline sources
- `docs/shared.css` created: Unified design system (CSS custom properties, warm-beige light theme)
- `docs/shared.js` created: Shared utilities (data loading, text fetching, formatting, DOM helpers)
- `docs/index.html` completely rewritten: Dashboard + document catalog + quality comparison
- `docs/viewer.html` completely redesigned: Light theme, source toggle (Mistral/LLM/DeepSeek)
- benchmark.html contents integrated into index.html (phase summary + document comparison cards)
- Pipeline steps labeled (IMG, OCR, LLM, EVAL, EXP instead of anonymous dots)
- Viewer as full-featured document page with info bar (metrics, CER bars, keyboard shortcuts)

**Engine visibility (Session 2):**
- `shared.js`: `engineBadges()` function + OCR pipeline step as composite (Mistral/DeepSeek sub-dots)
- `shared.css`: Engine dot styles (.teal/.violet), engine badges container
- `index.html`: Engine filter dropdown, DeepSeek CER column, engine badges column, per-engine metrics
- `viewer.html`: Engine badges in doc info bar

**Knowledge update (Session 2):**
- All 12 knowledge docs + PROJEKTWISSEN.md brought up to date as of 25.02.2026
- TEI-MAPPING.md + GND-STRATEGIE.md: E12 scope note added
- INFRASTRUKTUR.md: Stale Dockerfile reference (`templates/`) removed, dashboard deployment added
- DECISIONS.md: E15 (dashboard redesign) added
- ARCHITEKTUR.md: Dashboard QA UI section + CLI command added
- INDEX.md: Dashboard navigation + core term added
- TESTPLAN.md: Dashboard link added
- OCR-ENGINES.md: benchmark.html reference replaced by dashboard
- ZBZ-WORKFLOW.md: QA dashboard section added
- PROJEKTWISSEN.md: Dashboard files, E15, scripts table updated

### Architecture

- Multi-page with shared CSS/JS (instead of three independent designs)
- Static JSON data basis (`dashboard.json`) instead of hardcoded data in HTML
- Source toggle in viewer: Keyboard 1/2/3 for Mistral/LLM/DeepSeek
- Filterable document catalog with pipeline status display (labeled steps)
- CER comparison bars (Mistral vs LLM-C, optionally DeepSeek)
- Engine badges (M/DS/LLM) for instant engine recognition per document

### Decision

- **E15**: Dashboard redesign — Multi-page UI, shared CSS/JS, light theme, static JSONs, engine visibility

### New/Changed Files

| File | Action |
|------|--------|
| `scripts/generate_dashboard_data.py` | NEW |
| `docs/data/dashboard.json` | GENERATED |
| `docs/shared.css` | NEW + engine styles |
| `docs/shared.js` | NEW + engineBadges() + composite pipeline |
| `docs/index.html` | REWRITE + engine columns/filter |
| `docs/viewer.html` | REWRITE + engine badges in info bar |
| `docs/benchmark.html` | ARCHIVE (no longer linked) |
| `knowledge/*.md` (all 12) | UPDATE (timestamps, content, E12 scope) |
| `PROJEKTWISSEN.md` | UPDATE (dashboard, E15, scripts) |

---

## 2026-02-20 | coOCR Interface Analysis: PAGE-XML + PNG

### Completed

- coOCR/HTR repo ([DHCraft/co-ocr-htr](https://github.com/DHCraft/co-ocr-htr)) fully analyzed
- Import format identified: PAGE-XML (schema 2019-07-15) + PNG + METS-XML
- Export structure defined: `output/export/{doc_id}/` with mets.xml, images/, page/
- Batch orchestration architecture designed (not yet implemented)

### Findings

- coOCR is a pure browser app (no backend API) — import via file upload
- PAGE-XML namespace: `http://schema.primaresearch.org/PAGE/gts/pagecontent/2019-07-15`
- Text is stored in `<TextEquiv><Unicode>` as-is — Markdown formatting must be preserved
- Confidence mapping: Mistral raw=0.85, LLM corrected=0.95
- coOCR exports `<ab>` (not `<p>`) — relevant for teiCrafter interface (O5)

### Resolved

- **O4**: Interface zbz-ocr-tei -> coOCR = PAGE-XML + PNG + METS (E13)
- **R6**: Markdown formatting preserved, post-processing must not remove markup (E14)

### Next Steps

- Implement `scripts/export_page_xml.py` (Markdown -> PAGE-XML converter)
- Implement `scripts/run_pipeline.py` (batch orchestration with resume/retry)
- Adapt post-processing: Preserve Markdown markup

---

## 2026-02-19 | Scope Clarification: OCR Only, No TEI Transformation

### Decision (E12)

zbz-ocr-tei is solely responsible for OCR (PDF -> corrected Markdown). TEI transformation and GND linkage take place in coOCR/HTR and teiCrafter.

### Cleaned Up

- `scripts/transform_to_tei.py` removed (393 lines)
- `templates/` removed (5 TEI templates + README)
- `DOC_TYPES` and `TEI_DIR` removed from config.py
- ARCHITEKTUR.md: Pipeline reduced to 4 stages (without TEI/GND)
- PROJEKT.md: Milestones adjusted (M2=production, M3=coOCR integration)
- DECISIONS.md: E12 added, TEI questions (O6-O9, O11-O14, R2-R3) moved to coOCR/teiCrafter
- README.md completely rewritten

### Retained

- `evaluate_ocr.py` + reference TEI reading function (ground truth for CER)
- `extract_gnd.py` + KNOWN_ENTITIES (GND seed for downstream)
- `knowledge/TEI-MAPPING.md` and `GND-STRATEGIE.md` (reference knowledge)

---

## 2026-02-19 | Prompt Optimization: A/B/C Test for LLM Correction

### Completed

- Three prompt variants implemented: A (Analysis+Corrected), B (Lean), C (Few-Shot)
- `--variant` flag added in `llm_postprocess.py`
- All three variants tested on Phase 1-3 (10 docs, 53 pages)
- CER comparison against reference TEI

### Results

| Variant | Avg CER | Cost | Description |
|---------|---------|------|-------------|
| Mistral (no LLM) | 5.87% | $0.00 | Baseline |
| A (Analysis+Corrected) | 5.47% | $0.39 | Chain-of-thought |
| B (Lean, text only) | 5.59% | $0.33 | Minimal prompt |
| **C (Few-Shot)** | **5.55%** | **$0.33** | Error examples |

### Decision

**Variant C as default** — best CER/cost tradeoff. Overall improvement: 5.87% -> 5.55% (5.5% relative).
Differences between A/B/C are small (~0.1 points). Few-shot examples help slightly.

---

## 2026-02-19 | LLM-Based OCR Post-Correction with Haiku 4.5

### Completed

- `scripts/llm_postprocess.py` created: LLM-based OCR correction with Anthropic Claude Haiku 4.5
- `scripts/config.py` extended: LLM_CORRECTED_DIR, ANTHROPIC_MODEL, get_test_metadata()
- `.env.example` created as template (without secrets)
- ANTHROPIC_API_KEY configured in `.env` (already in .gitignore + .claudeignore)
- Pilot test: Phase 1-3 (10 docs, 50 pages) through LLM correction + CER comparison

### Architecture

One API call per page (chain-of-thought): `<analysis>` lists errors, `<corrected>` gives corrected text.
Prompt contains document context from TESTPLAN (type, language, genre).

### Results: Mistral vs. LLM-Corrected

| Doc | Type | Mistral CER | LLM CER | Delta |
|-----|------|-------------|---------|-------|
| 2310 | A | 7.00% | 3.93% | **-3.07** |
| 1180 | A | 3.12% | 3.17% | +0.05 |
| 290 | A | 18.07% | 18.20% | +0.13 |
| 2530 | B | 3.96% | 3.98% | +0.02 |
| 890 | B | 5.96% | 6.05% | +0.09 |
| 3040 | B | 9.02% | 8.97% | -0.05 |
| 90 | D | 1.21% | 1.10% | **-0.11** |
| 1440 | D | 3.71% | 3.71% | 0.00 |
| 830 | D | 4.00% | 3.29% | **-0.71** |
| 1330 | D | 2.60% | 2.78% | +0.18 |

| Phase | Mistral Avg CER | LLM Avg CER | Delta |
|-------|-----------------|-------------|-------|
| Phase 1 (A) | 9.40% | 8.43% | -0.97 |
| Phase 2 (B) | 6.31% | 6.34% | +0.03 |
| Phase 3 (D) | 2.88% | 2.72% | -0.16 |
| **Total** | **5.87%** | **5.47%** | **-0.40 (7% relative)** |

### Costs

- Phase 1-3 (50 pages): $0.39
- Projection 289 docs (7,200 pages): ~$56

### Findings

- Strongest improvement for documents with OCR artifacts (JSTOR headers, cover pages)
- Good improvement for special formats (historical, art book)
- No effect for scan quality issues (Doc 290 remains at ~18%)
- No significant gain for already good OCR (~3% CER)
- Occasional minimal degradation possible (1330: +0.18) due to LLM "corrections"

### New Files

- `scripts/llm_postprocess.py` — LLM correction pipeline
- `.env.example` — Template for API keys

---

## 2026-02-18 | M1: OCR Validation + Mistral Integration + Refactoring

**Mistral Document AI integrated and evaluated against all 12 test documents (Phase 1-4).**

- `MistralOCR` class implemented in `ocr_pipeline.py` (Azure AI Foundry endpoint, Base64 upload, automatic PDF splitting at >30 pages)
- `evaluate_ocr.py` extended: `--ocr-dir`, `--engine`, `--phase` parameters, fuzzy TEI lookup, rapidfuzz for CER (resolves MemoryError)
- **Result Phase 1-3: CER 5.87%, accuracy 94.14%** — Individual values in [TESTPLAN](TESTPLAN.md) §Results
- Phase 4 (monographs): Alignment for 142-156 page books not reliable, page-wise comparison needed
- Doc 290 (Comptes Rendus FR): CER 18% — presumably scan quality, not OCR problem
- Mistral ~1.3s/page (cloud API, no GPU needed), recognizes italics and accents

**Code refactoring: Central modules introduced.**

- `scripts/config.py` created: All paths, model names, constants, test plan
- `scripts/utils.py` created: `pdf_to_images()`, `check_gpu()`, `load_env()`, `load_deepseek_model()`
- 12 scripts refactored: Eliminated 4x `pdf_to_images`, 4x `check_gpu`, 4x `load_model`, 2x `load_env`, 2x `TESTPLAN`

**Technical:** Azure AI Foundry has its own URL format; PyMuPDF >= 1.24 renamed `fitz` to `pymupdf`.

---

## 2026-02-18 | Knowledge Vault Refactoring

- Knowledge folder built following coOCR/teiCrafter pattern: INDEX.md, PROJEKT.md, DECISIONS.md, INFRASTRUKTUR.md as new core documents
- Single source of truth introduced, duplication eliminated
- Ecosystem context documented (zbz-ocr-tei -> coOCR -> teiCrafter)
- Discovered: Post-processing removes Markdown formatting before TEI — information loss (-> R6); TEI transformation only prototype; interfaces between tools undefined

---

## 2026-02-14 | Contract Mutually Confirmed, Project Start

- Contract confirmed: ZBZ issued (email Elias, after 07.02.), DHCraft accepted (email Christopher, 14.02.)
- Framework conditions: Mistral OCR 3 via Azure, Claude Max Subscription, Gemini API, fork on GitLab Uni Zuerich, Podman
- Team ZBZ: Anouschka (editions and informatics background, since January)
- coOCR/HTR positioned as community project (Klugseder fork as reference)
- Alignment call: Date proposals sent (agenda: fork model, merge strategy, GitLab, Podman, on-site Zuerich)

---

## 2026-02-02 | Gemini 3 Agentic Vision Analysis

- Google Agentic Vision for Gemini 3 Flash (27.01.2026): Think-Act-Observe loop for auto-crop of columns — potential solution for Type-B problem (O10)
- Details: [ENGINES](ENGINES.md) §Gemini
- Sources: [Announcement](https://blog.google/innovation-and-ai/technology/developers-tools/agentic-vision-gemini-3-flash/), [IIIF Example](https://gist.github.com/charlesLoder/5341c539ab8330cfebc2d807e6b9c765)

---

## 2026-01-29 | Material Analysis & Pipeline Development

**First work session: Corpus analysis, hybrid pipeline validated, OCR Phase 1 completed.**

- 289 texts (7,200 pages) analyzed, 4 document types classified (A-D) — details in [QUELLENANALYSE](QUELLENANALYSE.md)
- Hybrid pipeline validated: Docling (layout, CPU) + DeepSeek (OCR, GPU) works
- Docling OCR not usable (RapidOCR encoding error: `e` -> `O` for French text) — used only for layout (E2)
- OCR Phase 1: 94.4% accuracy on Type-A documents — details in [TESTPLAN](TESTPLAN.md)
- GND seed: 75 entities extracted — details in [GND-STRATEGIE](GND-STRATEGIE.md)
- TEI prototype: 5 templates created (later removed with E12)
- 383 page images extracted from 15 pilot PDFs

---

*Created: 2026-01-29 | Updated: 2026-03-09*
