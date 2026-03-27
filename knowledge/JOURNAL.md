---
type: journal
created: 2026-01-29
updated: 2026-03-26
tags: [zbz-ocr-tei, journal, log]
status: active
---

# Work Journal

Chronological work log. Decisions are consolidated in [DECISIONS](DECISIONS.md), project status in [PROJEKT](PROJEKT.md).

**Dependencies:** None (standalone log)

---

## Session 40 (2026-03-27): Frontend Refactoring Phase 1+2 — CSS & HTML Konsolidierung

### Kontext
Codebase-weites Frontend-Refactoring nach umfassender Analyse aller 9 HTML-Seiten, 16 JS-Dateien und 3 CSS-Dateien. Inkonsistenzen durch mehrere Entwicklungsphasen angesammelt.

### Phase 1: CSS Token-Konsolidierung
- **shared.css**: 40+ neue Design-Tokens (Extended Palette, Badge-Farben, Toast/Validation, Infra-Akzentfarben, XML-Syntax). Globale `:focus-visible` und `@keyframes h-flash` Animation hinzugefuegt.
- **edition.css**: `:root`-Block von ~90 auf ~20 Zeilen reduziert (nur edition-spezifische Tokens behalten). ~35 hardcoded Hex-Farben durch Token-Referenzen ersetzt. Duplizierte Resets und `@keyframes ed-flash` entfernt. Dead CSS (`.ed-landing-col {}`) entfernt.
- **infra.css**: `:root`-Block komplett auf `--h-*` Aliases umgestellt. Duplizierter Reset entfernt. Alle hardcoded Hex-Farben (15+) durch Tokens ersetzt. `@keyframes entityFlash` durch `h-flash` ersetzt. Dead CSS (`.grid-3col`, `.text-muted-sm`, `.text-muted-italic`) entfernt. Diagnostik-Inline-Styles (~95 Zeilen) aus diagnostik.html migriert.

### Phase 2: HTML-Normalisierung & Semantik
- **diagnostik.html** (KRITISCH): CSS-Links normalisiert (shared+edition+infra), Body-Class `infrastruktur-page` hinzugefuegt, Skip-Nav, `infra-subnav` mit `aria-current="page"`, `<main>` Element, Script-Tags auf edition-shared+infra-shared umgestellt, Inline-Styles entfernt, volles ARIA-Tab-Pattern.
- **Alle 4 Infra-Seiten**: Skip-Nav, `<main id="main-content">`, `<h1>` Seitentitel, `shared.css` hinzugefuegt, `<footer>` Slot, `infra-subnav` semantisch als `<nav>` mit `aria-current="page"`.
- **catalog.html + register.html**: Sidebar-Headings h3->h2 (Hierarchie-Reparatur), View-Toggle mit `aria-pressed`, Result-Count mit `aria-live="polite"`.
- **reader.html**: Panel-Divider mit `role="separator"`, `tabindex="0"`, `aria-label`. View-Toggle mit `aria-pressed`. Footer-Slot hinzugefuegt.
- **viewer.html**: Panel-Dividers mit ARIA-Rollen. Footer-Slot.
- **index.html**: Search-Input als `role="combobox"` mit `aria-controls`.

### Phase 3: JS Foundation Layer
- **`zbz-core.js` erstellt** (~260 Zeilen): DOM helpers, URL state, XML utils, fetch helpers, formatting, debounce, throttleRAF, LRU Cache, toast, entity index, labels, makeSortable. Geladen als erstes Script auf allen 9 Seiten.
- **edition-shared.js geslimmt**: Lokale Definitionen von $, $$, esc, fmtNum, getParam, setParams, parseXml, highlightXml, padPage, debounce, _fetchFirstOk, loadEntityIndex, lookupEntity, imagePath, PUB_FORM_LABELS entfernt — delegieren jetzt an ZBZ.*.
- **infra-shared.js geslimmt**: $, $$, esc, fmtNum, fmtPct, padPage, imagePath, PUB_FORM_LABELS, parseXml, highlightXml, loadEntityIndex, lookupEntity, getParam, setParams entfernt. Merge-Logik auf non-destructive Ergaenzung umgestellt.
- **infra-utils.js geloescht** (toter Code, 230 Zeilen eliminiert).
- **diagnostik.js** auf `ZBZ.Edition` umgestellt, `makeSortable` lokal eingebettet.

### Phase 4: Unified TEI Renderer
- **`zbz-tei-render.js` erstellt** (~155 Zeilen): Konfigurierbarer TEI-Node-Renderer mit `cssPrefix` und `lookupFn` Options. Ersetzt ~220 Zeilen duplizierten Code.
- **edition-tei.js**: `renderNode()` (~112 Zeilen) entfernt, delegiert an `ZBZ.TeiRender.render()` mit `{cssPrefix: 'ed-tei-'}`.
- **infra-tei-viewer.js**: `renderTeiNode()` (~109 Zeilen) entfernt, delegiert an `ZBZ.TeiRender.renderNode()` mit `{cssPrefix: 'tei-'}`.
- **infra.css**: `tei-hi-bold/italic/underline/spaced`, `tei-foreign`, `tei-sp`, `tei-speaker`, `tei-space` CSS-Klassen hinzugefuegt (vorher Inline-Styles).

### Phase 5: ARIA State-Management
- **catalog.js + register.js**: `aria-pressed` bei View-Toggle-Klicks synchronisiert.
- **edition-reader.js**: `aria-pressed` fuer Text/XML Tab-Toggle.
- **diagnostik.js**: `aria-selected` fuer Tab-Wechsel synchronisiert.
- **edition-landing.js**: `aria-expanded` fuer Search-Suggestions-Dropdown.

### Offene Phasen (Folgesession)
- Phase 6: Editor-Decomposition, var->const/let, Magic Numbers

---

## Session 39 (2026-03-26): OCR-Diagnostik Abschluss — Scope-Bereinigung (Lane 2)

### Kontext
Abschlussrunde Lane 2: Scope-Mismatches bereinigen, finale Statistiken produzieren.

### Ergebnisse
- **6 Scope-Mismatches identifiziert** (3 manuell: Docs 30, 300, 1440; 3 auto-detektiert: 3020, 760, 830)
- Jedes Doc hat `scope_status` (full/partial) und `scope_detail` in diagnostik_ocr.json
- **Bereinigte Statistik (19 Docs):** Mean 4.18%, Median 1.83%, 13 Docs <3%
- Stratifizierte Statistik nach Sprache und Layout-Typ
- Reduktions-Timeline (5 Schritte: 9.33% -> 4.18% Mean)
- CER-BENCHMARK.md mit allen finalen Zahlen aktualisiert

### Lane 2: DONE

---

## Session 38 (2026-03-26): Diagnostik-UI Rewrite + Navigation (Lane 3)

### Durchgefuehrt
- **Navigation:** "Diagnostik" in NAV_ITEMS (edition-shared.js), erscheint auf allen Editions-Seiten
- **Diagnostik-UI:** Komplett neu geschrieben. 4 Tabs (Uebersicht, OCR, TEI, Aktivitaet)
- **Design:** --h-* Tokens, ZBZ.Diagnostik Namespace, graceful empty states
- **Search-Index-Fix:** 279->285 Docs (robustes XML-Parsing bei revisionDesc-Fehlern)
- **Seitenzaehlung:** 383->4.117 (Summe statt Dashboard-Stub)
- **Wikidata:** API wieder erreichbar (200), Batch gestartet

### Geaenderte Dateien
- docs/js/edition-shared.js, docs/infrastruktur/diagnostik.html, docs/js/diagnostik.js (NEU)
- scripts/generate_edition_data.py, docs/data/catalog.json, docs/data/search_index.json

---

## Session 37 (2026-03-26): Diagnostik-Datenproduktion (Lane 1)

### Kontext
Daten fuer Diagnostik-UI produzieren. W10-Tiefenanalyse, Corpus-Statistik, Timeline, Warning-Uebersicht.

### Ergebnisse

**1. W10-Tiefenanalyse (10 Docs)**
- 10/10 Docs = `ner_miss`: alle haben ungetaggte Orgs/Places im Fliesstext
- Beispiele: Doc 1370 (Schweiz, Zurich, societe, ecole), Doc 1380 (conseil, faculte, societe)
- Kein Fall von "content_explains" — NER-Extraktion hat orgName/placeName systematisch uebergangen
- Loesungsweg: NER-Re-Extraktion mit explizitem Org/Place-Fokus noetig (nicht nur Re-Injection)

**2. Corpus-Statistik (285 Docs, 4.108 Seiten)**
- 29.637 lb | 27.615 p | 12.983 persName | 6.314 placeName | 4.860 bibl | 3.814 orgName
- 1.373 div | 1.318 hi | 947 head | 266 note | 250 foreign | 142 figure
- Layout-Typ-Verteilung und avg_entities/avg_pages pro Typ berechnet

**3. Validierungs-Timeline**
- 4 Meilensteine: Initial (50/285) -> Fix-001 (285/285) -> Fix-002 (W6 weg) -> Fix-003 (W3/W4/W7 weg)

**4. warnings_current**
- W9: 17 Docs, blocked_on_ner | W10: 10 Docs, ner_miss | W11: 2 Docs, false_positive

### Artefakte
- `scripts/diagnostik_data_producer.py` — wiederverwendbares Script
- `docs/data/diagnostik_tei.json` — 4 neue Keys (w10_analysis, corpus_stats, validation_timeline, warnings_current)

---

## Session 36 (2026-03-26): Edition-Sync Fortsetzung (Lane 3)

### Kontext
Lane 3 uebernimmt Diagnostik-UI-Ownership. Drei offene Punkte aus Session 35 loesen.

### Durchgefuehrt

**1. Diagnostik-UI konsolidiert:**
- Log-Tab hinzugefuegt (HTML + CSS + JS in diagnostik.html/diagnostik.js)
- Liest diagnostik_log.json, zeigt chronologisch (neueste oben)
- Graceful Handling: "Noch keine Daten" bei leeren/fehlenden JSONs
- Lane-Zuordnung: L1 schreibt diagnostik_tei.json, L2 schreibt diagnostik_ocr.json, alle schreiben diagnostik_log.json

**2. Search-Index-Luecke gefixt:**
- 6 fehlende Docs (1390, 1510, 2590, 2980, 790, 840) identifiziert
- Ursache: unescaptes XML in revisionDesc (& und < in Beschreibungstexten)
- Fix: Fallback-Parser in build_search_index() entfernt revisionDesc bei ParseError
- Search Index: 279 -> 285 Docs

**3. Seitenzaehlung korrigiert:**
- total_pages kam aus dashboard.json (nur 15 Docs = 383 Seiten)
- Fix: Summe aus page_count aller Katalog-Eintraege
- Seitenzaehlung: 383 -> 4.117 Seiten

**4. Wikidata Retry:**
- API-Test: Status 429 (noch rate-limited)
- Batch nicht moeglich, spaeter wiederholen

### Geaenderte Dateien
- `scripts/generate_edition_data.py` — robustes XML-Parsing + total_pages Fix
- `docs/infrastruktur/diagnostik.html` — Log-Tab + Panel + CSS
- `docs/diagnostik.js` — initLogs() Funktion + Aufruf in init()
- `docs/data/catalog.json` — 4.117 Seiten, 285 Docs
- `docs/data/search_index.json` — 285 Docs (vorher 279)

---

## Session 35 (2026-03-26): Edition-Synchronisation (Lane 3)

### Kontext
Edition spiegelte nicht den Pipeline-Stand. Katalog hatte nur 15 Docs (Manifest-Flaschenhals),
Wikidata-Reconciliation bei 44%, Frontend-Features fehlten.

### Durchgefuehrt

**Block 1 — Wikidata Batch:**
- `--resume` Flag in `wikidata_linker.py` implementiert (Document-Level-Skip)
- Batch gestartet: 25 Docs uebersprungen, 260 zu verarbeiten
- **Ergebnis:** 0 neue Resolutions — Wikidata-API rate-limited (429) fuer alle neuen Queries
- Rate bleibt bei 44% (5.163/11.685 Entities)
- `entity_index --merge-all`: 96 neue Entities registriert, Index 4.408 -> 4.504

**Block 2 — Editions-Daten:**
- `generate_edition_data.py` erweitert: Discovery aus `tei_final/` fuer fehlende Dashboard-Docs
- Katalog: 15 -> 285 Dokumente, Screening 242 APPROVED + 43 WITH_NOTES korrekt
- Entity Register: 4.504 Eintraege, Search Index: 279 Docs

**Block 3 — Frontend:**
- 3a: Entfaellt (docs/edition/ existiert nicht)
- 3b: Screening-Badges bereits implementiert
- 3c: revisionDesc im Reader implementiert (reader.html + edition-reader.js, nutzt bestehendes CSS)
- 3d: Katalog-Filter bereits implementiert

**Block 4 — Diagnostik:** Bereits von Lane 2 gebaut (6-Tab-Layout mit echten Daten)

### Geaenderte Dateien
- `scripts/ner/wikidata_linker.py` — `--resume` Flag
- `scripts/generate_edition_data.py` — tei_final Discovery
- `docs/reader.html` — revisionDesc Panel
- `docs/js/edition-reader.js` — loadRevisionDesc()

### Offen
- Wikidata-Batch wiederholen wenn API Cooldown vorbei (--all --resume)
- Search Index: 279/285 Docs (6 ohne Text-Body)
- Seitenzaehlung im Katalog: 383 (nur aus Manifest/Gemini, nicht alle Docs haben page_count)

---

## Session 34 (2026-03-26): TEI-Qualitaet Diagnostik (Lane 1)

### Kontext
Schema-Validierung aller 285 Docs gegen zbz_hersch.rng. Identifikation und Fix der Fehlerursachen.

### Ergebnisse

**1. Initiale Validierung**
- 50 valid, 235 invalid, 82 mit Warnings
- Root Cause: Schema erzwang `ref="GND:*"`, Pipeline injiziert `ref="#zbz-*"` (projektinterne IDs)
- RelaxNG-Kaskade: 1 ref-Pattern-Fehler loest 6+ Kaskaden-Fehler pro Doc aus
- Scheinbare Nebenfehler (idno, langUsage, biblStruct) waren ausschliesslich Kaskaden-Artefakte

**2. Fix: ref-Pattern in zbz_hersch.rng erweitert**
- Pattern: `(GND:[0-9A-Za-z\-]+|#zbz-[a-z]+\.[0-9]+)` an 3 Stellen (bibl/@corresp, orgName/@ref, persName/@ref)
- Ergebnis: **285/285 valid** (100%), 0 Regressionen
- Ein einziger deterministischer Fix heilt alle 235 invaliden Docs

**3. Referenz-TEI Validierung**
- 17/25 Referenz-TEIs valid (68%), wie in Session 31
- 8 invalide: Schema strenger als ZBZ-Praxis (space ohne desc, back-Struktur, foreign)

**4. Artefakte**
- `docs/data/diagnostik_tei.json` — maschinenlesbare Fehlerfrequenz
- `docs/data/diagnostik_log.json` — Aktion-Log
- `docs/infrastruktur/diagnostik.html` Tab "TEI-Qualitaet" — UI mit Fehler/Fix/Warning-Tabellen
- `knowledge/TEI-QUALITY.md` — Dokumentation

**5. Fix-002: Heuristische lb-Injection**
- Root Cause: Mistral OCR liefert keine Zeilen-Umbrueche; nur 51/285 Docs hatten Step 2 (Gemini) durchlaufen
- Fix: `_inject_heuristic_lb()` in tei_step3.py — alle ~60 Zeichen an Wortgrenzen
- Non-Regression: Absaetze mit bestehenden lb unberuehrt
- **46 Docs gefixt, 10.635 lb injiziert, W6 eliminiert (82 -> 37 Warnings)**

**6. Fix-003: Post-Assembly Fixes W3/W4/W7**
- Fix E: Doppelte pb mit identischem facs (5 W3-Docs) — Guard: nur wenn pbs > surfaces
- Fix F: Leere div ohne Textinhalt (1 W4-Doc: 110)
- Fix G: Leere figure mit graphic url="unknown" (2 W7-Docs: 130, 1460)
- W11 (2 Docs: 140, 1240) als false positive dokumentiert (echte Anthologie-Struktur)
- **Warnings: 37 -> 29**

**7. NER-Re-Injection Vorbereitung**
- Dual-Attribut-Strategie (E50) gegen zbz_hersch.rng validiert
- W9 (17 Docs): Entity-Tags ohne ref — Re-Injection loesbar
- W10 (10 Docs): 0 orgName/placeName — vermutlich NER-Extraktionsproblem
- Re-Injection-Befehl: `python -m scripts.ner.ner_inject_tei --all --validate`

### Naechste Schritte
- NER-Re-Injection ausfuehren (nach Entity-Index-Update, Lane 3)
- W10: NER-Extraktion fuer orgName/placeName pruefen

---

## Session 33 (2026-03-26): OCR-Diagnostik + Evaluationsoptimierung (Lane 2)

### Kontext
Systematische Verbesserung der OCR-Qualitaet. Aufbauend auf E51 (Session 32). Ziel: Median CER <3.5%.

### Ergebnisse — Gesamteffekt: Mean CER 9.33% -> 5.97% (-3.36pp), Median 5.52% -> 2.42%. **Ziel erreicht.**

**1. Symmetrische Normalisierung** — Mean CER -1.22pp, WER -6.57pp
**2. Hyphen-Normalisierung** — Median 5.36% -> 2.61%. Doc 570 kein Mismatch mehr. Doc 580: 6.8% -> 0.3%.
**3. Case-insensitive Alignment** — Doc 1060: 21.4% -> 0.6%. Doc 290: 33.5% -> 21.2%.
**4. Konfusionsmatrix** — 1389 verbleibende echte OCR-Substitutionen. Top: e->Space, e->E, Space->e.
**5. Outlier-Diagnose** — 3 von 5 High-CER Docs sind Scope-Mismatches (unfaire Seitenvergleiche).
**6. Diagnostik-UI**
- `docs/infrastruktur/diagnostik.html` + `docs/diagnostik.js`
- 5 Tabs: CER-Heatmap, Konfusionsmatrix, Baseline-Vergleich, Pipeline-Effekt (Dot-Plot), Outlier-Diagnose
- Datenquelle: `docs/data/diagnostik_ocr.json`

### Neue Dateien
- `scripts/generate_diagnostik.py` -- Generiert diagnostik_ocr.json
- `scripts/evaluate_ocr.py`: `normalize_for_comparison()`, `build_confusion_matrix()`
- `docs/infrastruktur/diagnostik.html` -- Diagnostik-Dashboard
- `docs/diagnostik.js` -- Dashboard-Logik
- `docs/data/diagnostik_ocr.json` -- Diagnosedaten
- `docs/data/diagnostik_log.json` -- Aktionslog

### Entscheidungen
- Symmetrische Normalisierung als Standard fuer alle CER-Vergleiche
- Fruehere "4 verschlechterte Docs" auf 1 echten Ausreisser korrigiert (Doc 290)

---

## Session 32 (2026-03-26): End-to-End CER Benchmark (E51)

### Kontext
Erste systematische Messung der End-to-End-Textqualitaet: Pipeline-TEI vs. ZBZ-Referenz-TEI (Transkribus Ground Truth). Bisher wurde CER nur auf OCR-Stufe gemessen.

### Ergebnisse
- **Median CER 5.5%**, Mean 9.3% (24 von 25 Ground-Truth-Docs, 1 Mismatch)
- Vergleichbar mit GPT-4o-Klasse (6.3%) laut Forschungsliteratur 2025/2026
- Beste Docs bei 1.0-2.2% (State of the Art fuer historischen Druck)
- Pipeline hilft 11/25 Docs (teilweise massiv), verschlechtert 4/25 (nur bei vorher schlechtem OCR)
- Fruehere Annahme "Pipeline-Degradation als Hauptproblem" war falsch — korrigiert

### Neue Dateien
- `knowledge/CER-BENCHMARK.md` -- Benchmark-Ergebnisse + Forschungskontext + wiss. Quellen
- `scripts/benchmark_cer.py` -- CLI fuer stratifizierte CER-Analyse (Typ/Sprache/Form)

### Erweiterungen
- `scripts/evaluate_ocr.py`: 4 neue Funktionen (extract_text_for_comparison, categorize_errors, evaluate_tei_vs_tei, compute_proxy_quality)
- `scripts/generate_dashboard_data.py`: benchmark_tei Key in Dashboard-JSON
- `knowledge/PLAN.md`: Sub-Projekt "CER-Verbesserung" mit 4-Phasen-Plan
- `knowledge/DECISIONS.md`: E51 (Benchmark) + O18 Update (multimodale Korrektur)
- `knowledge/INDEX.md`: CER-BENCHMARK in Document Matrix

### Entscheidungen
- E51: End-to-End CER Benchmark
- Sub-Projekt CER-Verbesserung definiert (Phase 0-4, Ziel: Median < 3.5%)

---

## Session 31 (2026-03-26): Neues Schema + Editionsrichtlinien einarbeiten

### Kontext
Projektpartnerinnen (ZBZ) liefern projektspezifisches RelaxNG-Schema (`zbz_hersch.rng`, aus ODD generiert, TEI P5 v4.10.2) und vollstaendige Editionsrichtlinien. Ersetzen bisheriges generisches Schema und konkretisieren TEI-Mapping-Regeln.

### Aenderungen (18 Dateien)

**Phase 1 -- Schema + Config + Validator:**
- `data/schema/zbz_hersch.rng` eingespielt (551 Definitionen, aus ODD generiert, TEI P5 v4.10.2)
- `data/schema/tei_all.rng` → `tei_all.rng.bak` (Backup)
- `scripts/config.py`: Schema-Pfad auf `zbz_hersch.rng`, VALID_DIV_TYPES erweitert (dedication, otherEdition, foreign), TEI_ALL_URL/SCHEMA_DOWNLOAD_TIMEOUT entfernt
- `scripts/tei/tei_validator.py`: Download-Logik entfernt, neue Regeln R7 (figure nicht in p), W12 (Fussnoten-n), W13 (Fussnoten xml:id Pattern), W14 (back/div types)

**Phase 2 -- Knowledge-Dokumente:**
- `knowledge/TEI-MAPPING.md`: Grosses Update -- Zeichennormalisierung verbindlich, Kapitaelchen (#k), unclear, Marginalien, leere Seiten, front/back-Matter, Genre-Strukturen, Dual-Attribut-Entitaeten, Open Questions geloest
- `knowledge/DECISIONS.md`: E48 (Schema), E49 (Richtlinien), E50 (Dual-Attribut-Strategie). O6, O9 geschlossen. R2 mitigiert
- `knowledge/GND-STRATEGIE.md`: GND als primaere Referenz (ref), interne IDs in corresp, Ausschlussregeln

**Phase 3 -- Pipeline-Code:**
- `scripts/tei/tei_mapping_prompt.py`: Rendition #k, unclear, entity-Ausschlussregeln (figure, listBibl, adjektivierte Formen), front/back-Matter, marginalia, leere Seiten, sp type, 12+ neue Stopwords (kantien, hegelsche, cartesien...)
- `scripts/tei/tei_step1.py`: Ruft `normalize_for_tei()` auf OCR-Text auf
- `scripts/tei/tei_step2.py`: Entity-Ausschluss fuer figure/listBibl in reannotate_entities()
- `scripts/tei/tei_step3.py`: Header-Fix (kein idno, langUsage, monogr -- nicht im ODD-Schema), encyclopedia→entry in GENRE_TO_DIV_TYPE, Fix D2 (figure aus p herausloesen), toter Code _parse_languages entfernt
- `scripts/tei/tei_xml_utils.py`: `normalize_for_tei()` -- TEI-spezifische Zeichennormalisierung (Halbgeviertstrich, typographische Anfuehrungszeichen, Apostroph U+2019, Leerzeichen vor Interpunktion)
- `scripts/tei/tei_generator.py`: langUsage/profileDesc aus Header entfernt (Schema-Konformitaet)

**Phase 5 -- NER:**
- `scripts/ner/ner_inject_tei.py`: Dual-Attribut-Strategie (ref="GND:..." + corresp="#zbz-p.N"), Entity-Ausschluss fuer figure/listBibl via Masking-Technik

**Phase 6 -- Richtlinien:**
- `data/richtlinien/Editionsrichtlinien_ZBZ.md` eingespielt (verbindliche Referenz)

### Entscheidungen
- E48: Projektspezifisches Schema zbz_hersch.rng ersetzt generisches tei_all.rng
- E49: Editionsrichtlinien ZBZ als verbindliche Referenz fuer TEI-Mapping
- E50: Dual-Attribut-Strategie (ref=GND + corresp=intern)

### Validierungsergebnisse

```
Baseline (alte TEIs, gegen zbz_hersch.rng):
  4/285 VALID, 3210 Schema-Fehler (idno, langUsage, monogr dominierend)

Nach Re-Assembly (207/285 Docs reassembliert):
  50/207 VALID (24.2%), 0 Header-Fehler
  157 Body-Content-Issues (vorbestehend, Schema strenger als tei_all.rng)

Referenz-TEIs (von ZBZ): 17/25 VALID

Stichprobe (10 Docs, manuell reassembliert): 7/10 VALID
```

Header-Fehler (idno, langUsage, monogr) vollstaendig eliminiert. Verbleibende Body-Issues erfordern vollstaendigen Pipeline-Re-Run (--all --force) mit aktualisierten Prompts und Schema-konformer Generierung.

### Tests durchgefuehrt
- Syntax-Check: Alle 18 Python-Dateien parsen korrekt
- Unit-Test: normalize_for_tei() -- 4 Assertions (Em-Dash, Guillemets, Interpunktion, Apostroph)
- NER Dual-Attribut: ref="GND:118557106" corresp="#zbz-p.1" (mit GND), corresp="#zbz-p.100" (ohne GND)
- Entity-Ausschluss: figure/listBibl Masking funktioniert
- Schema-Validierung: 5 Docs einzeln, 207 Docs batch, Referenz-TEIs komplett

### Naechste Schritte
- Vollstaendiger Pipeline-Re-Run (--all --force) fuer Body-Konformitaet
- NER-Re-Injection mit Dual-Attribut auf allen Docs
- Frontend: Rendition #k, unclear, sic/corr anzeigen
- Verbleibende 78 Docs reassemblieren (Background-Task abgebrochen)

---

## Session 30 (2026-03-15): Hersch Design-System + UI-Redesign

### Kontext
Komplettes Redesign der digitalen Edition basierend auf der Jeanne Hersch Design Specification v1.1. Migration von Navy+Gold+Inter auf Anthrazit+Ziegelrot+EB Garamond+Jost.

### Ergebnisse

**Design-Token-Migration:**
- Zweistufige CSS-Variable-Architektur: `--h-*` Hersch-Tokens + `--ed-*` Aliase
- Farbpalette: Anthrazit #2C2825, Ziegelrot #8B3A3A, Preussischblau #2B4C7E, Olivgruen #6B7B5E
- Typoskala: Kleine Terz (1.2 Ratio) statt lineare Stufen
- EB Garamond (Body) + Jost (Headings) statt Inter + Source Serif
- Helle Navigation und Hero (inspiriert von ZBZ-Website)

**Landing Page Redesign:**
- 3 kompakte Zonen statt 6 Sektionen
- Kategorien als Chips statt grosse Kacheln
- Screening als kompakte Chips + Progressbars
- "Zuletzt bearbeitet" entfernt (Platzfresser)
- Curation-Hinweis als Info-Box

**Reader-Toolbar:**
- Font-Toggle und Entity-Sidebar entfernt
- XML/Text-Toggle aus Toolbar in Textbereich verschoben (Tab-Switch)
- Faksimile-Viewer: Pan (Drag), Mausrad-Zoom, Rotation (90-Grad), Fit-to-Width, Doppelklick-Zoom

**Neue Hersch-Komponenten (CSS):**
- Seuil (Schwellenzonen), Divider-Seuil, Etonnement (4 Varianten), Polyphonie-Grid, Blockquote, Source-Label, Sprach-Indikatoren

**UI-Verbesserungen:**
- Dokumentbeschreibungen (`desc`) auf allen Karten sichtbar
- Curation-Badge immer sichtbar (nicht nur mit Server)
- Entity-Kontext-Preview im Register
- Sprach-Labels fuer `<foreign>` Passagen im Reader
- Fussnoten als Marginalien (CSS-only, responsive Fallback)

**Refactoring:**
- ~200 Zeilen tote CSS entfernt (Screening-Cards, Category-Tiles, Featured-Grid)
- Doppelte `.ed-btn-sm` konsolidiert
- 11 Inline-Styles durch CSS-Klassen ersetzt
- 11x hardcoded `#fff` durch `var(--h-text-inverse)` ersetzt
- Infrastruktur-Seiten (shared.css) auf Hersch-Palette angeglichen

**Wissensdoku:**
- `knowledge/DESIGN.md` neu: Design-System-Referenz
- `knowledge/EDITION.md` um Design-Verweis ergaenzt
- `knowledge/INDEX.md` aktualisiert

### Offene Punkte (naechste Session)
- Register-Redesign: Dropdown statt Tabs, separate Seiten pro Entity-Typ, Kartenansicht entfernen
- Multi-Editor-Workflow dokumentieren

---

## Session 29 (2026-03-15): NEEDS_REVIEW Nachbearbeitung (32 Docs -> 0)

### Kontext
32 Dokumente mit Status NEEDS_REVIEW aus dem Agent-Based Quality Screening systematisch nachbearbeitet. Drei Problemkategorien: Entity False Positives (15 Docs), Strukturprobleme (9 Docs), OCR-Halluzinationen (8 Docs).

### Ergebnisse

**Entity-Stopwoerter erweitert (E45):**
- 20 neue Eintraege in `_ENTITY_STOPWORDS` (tei_mapping_prompt.py)
- Deutsche Gattungsbegriffe: Mensch, Der Mensch, Wahl, Rolle, Angst, Geist, Ursprung, Gott, Christ, Philosophie, Demokratie, Philosophen, Marxisten
- Franzoesische Falsch-Positive: Est (P9: Est-ce que), Homme (droits de l'Homme)
- Demonymen: Schweizer, Zuercher, Zahler
- Abstrakte Werktitel: Zeit, Gesamtschule
- Reassembly aller 32 Docs: 32/32 VALID, $0 Kosten

**Strukturfixes (5 Docs):**
- Doc 2140: div type="interview" -> type="text", 5x sp/speaker -> p rendition="#b" (Thesen, keine Sprecher)
- Doc 2150: Platzhalter-Titel "2150" -> "A la veille de mon premier voyage en Grece"
- Doc 2530: Verwaistes head in div n="1" in div n="2" verschoben
- Doc 2550: 2x head nach p -> p rendition="#b", leeres sp/speaker entfernt, Duplikat-Absatz entfernt
- Doc 2660: div type="interview" -> type="text", 4x spuriose sp/speaker entfernt

**OCR-Halluzinationen bereinigt (3 Docs):**
- Neues Script: `scripts/ocr_dedup.py` -- Token-Repetitions-Loops, Einzel-Buchstaben-Loops, Barcode-Artefakte, Jahrzahl-Wiederholungen, URL-Artefakte
- Doc 900: "les filles" 28x, "1969" 50x, "la sensibilite" 30x, J-Buchstaben-Loop (200x) entfernt
- Doc 1100: "de l'URSS" 13x, "de la situation sociale" 25x entfernt
- Doc 2630: 6 Barcode-Artefakte (KdSvoSsBtGcWIS...) + URL-Artefakt entfernt
- Einschraenkung: Fehlender Originaltext nicht rekonstruierbar ohne Gemini OCR-Rerun

**Neuer Gesamtstatus (285/285 Docs):**

| Status | Vorher | Nachher |
|--------|--------|---------|
| APPROVED | 210 (74%) | 242 (85%) |
| APPROVED_WITH_NOTES | 43 (15%) | 43 (15%) |
| NEEDS_REVIEW | 32 (11%) | 0 (0%) |

### Technische Aenderungen
- `scripts/tei/tei_mapping_prompt.py`: _ENTITY_STOPWORDS erweitert (E45)
- `scripts/ocr_dedup.py`: Neues Script zur OCR-Halluzinations-Bereinigung
- 32 TEIs in output/tei_unified/ reassembliert
- 5 TEIs strukturell gefixt (div-Typen, sp->head, Titel)
- 3 OCR-Quelldateien in output/ocr_results/ bereinigt
- Quality Pass: 285/285 Docs, 242 APPROVED + 43 WITH_NOTES
- revisionDesc in allen 285 TEIs aktualisiert
- catalog.json mit aktualisierten Screening-Status regeneriert

### Entscheidungen
- E45: Entity-Stopwort-Erweiterung durchgefuehrt (20 neue Eintraege)
- E46: OCR-Deduplizierung als deterministische Nachbearbeitung (kein LLM noetig)
- E47: div type="essay" ist kein valider DTA-Typ -> type="text" als generischer Ersatz

---

## Session 28 (2026-03-15): Edition Frontend Refactoring

### Kontext
FRONTEND-BRIEFING.md umgesetzt. Edition von Demo-Praesentation zur Discovery-Plattform weiterentwickelt.

### Ergebnisse

**Datenschicht:**
- TEI_FINAL_DIR in config.py zentralisiert
- 285 finale TEIs + 285 Review-JSONs nach docs/data/tei/ kopiert (18 MB, GitHub Pages)
- search_index.json: Volltext aus 277 TEI-Bodies (688 KB)
- catalog.json: screening + curation Status getrennt, corpus.screening/curation Counts
- Curation Server: tei_final in Prioritaetskette, /api/tei/{id}/full Endpoint, pb-Splitting, revisionDesc beim Save

**Frontend-Features:**
- Startseite: Discovery Hub mit Suchleiste (Volltext-Vorschlaege), Screening-Fortschritt (LLM + Editor getrennt), Kategorien-Kacheln, zuletzt bearbeitete Docs
- Katalog: Galerie-View (Seite-1-Thumbnails), Volltext-Suche mit Snippet-Highlighting, URL-Deep-Linking (?q=, ?type=, ?screening=), URL-State-Sync
- Reader: RevisionDesc-Panel (auto-expand bei NEEDS_REVIEW), Seiten-Thumbnails-Leiste, Screening-Badge im Header
- Register: Doc-Titel in Cross-Links, Typ-Statistiken unter Tabs

**Refactoring:**
- Badge-Konstanten zentralisiert (SCREENING_LABELS/CLASSES + CURATION_LABELS/CLASSES + screeningBadgeHtml/curationBadgeHtml) -- 4 Duplikate eliminiert
- 68 Zeilen verwaiste CSS entfernt (ed-stats-grid, ed-bar-*, ed-pills aus altem Landing)
- Health-Check nur auf localhost (keine 404-Fehler auf GitHub Pages)
- XML-Parse-Fehler bei Seitenextraktion behoben (Regex auf Original-XML + Tag-Balancing)
- docs/edition/ (ES5-Duplikat) geloescht
- Navigation: "Leseansicht" entfernt, "Promptotyping-Artefakte" statt "Epist. Infrastruktur"

**Workflow-Design:**
- Screening (LLM) + Curation (Editor) als getrennte Status (User-Entscheidung)
- 5 Curation-States: uncurated -> draft -> in_progress -> in_review -> editor_approved
- CSS fuer alle States, Fortschrittsbalken auf Startseite

### Commits
- `fb6fe67` Edition Frontend: Discovery Hub, Volltextsuche, Galerie, Screening+Curation Workflow
- `7df4c41` Fix: XML-Parse-Fehler bei Seitenextraktion + Curation-Status + Nav-Cleanup
- `df6be2d` Fix: Health-Check nur auf localhost

---

## Session 27 (2026-03-15): Agent-Based Quality Screening + revisionDesc

### Kontext
Erste Anwendung der Promptotyping-Methodik als operativen Quality-Screening-Prozess. Infrastruktur fuer echtes 7-Schichten-Screening aufgebaut. revisionDesc als Versionierungs-Standard im TEI-Header etabliert.

### Ergebnisse

**Reassembly-Run:** 284/285 VALID (vorheriger Report zeigte 71/285 — war veraltet, nicht re-run nach Session 26 Fixes). Dauer: ~2.5h, Kosten: $0.

**Agent-Based Quality Screening (5 Docs):**
- Methodik: Strukturiertes Review-Protokoll pro Dokument (Scan, OCR, Layout, TEI-Struktur, Referenz, Entities, Kohaerenz)
- Alle 5 Docs: APPROVED_WITH_NOTES (schema-valide, inhaltlich korrekt)
- 19 Learnings dokumentiert (L1-L19)
- 6 systematische Muster identifiziert (P1-P6)

**Systematische Muster:**
- P1: Doppelseiten-Scans erzeugen W3 (kein Fix noetig, Buchformat)
- P2: W10 False Positive bei abstrakten philosophischen Texten
- P3: Seitenzahlen-Erkennung inkonsistent (Mix aus Original und relativ)
- P4: Entity Typ-Konflikte Person/Werk (Kierkegaard, Nietzsche) — fixbar im Index
- P5: JSTOR-Scans koennen mehrere Rezensionen pro Seite enthalten
- P6: Gemini korrigiert OCR-Fehler im Step 2 (undokumentierter Qualitaetsgewinn)

**Methodische Reflexion:**
- Visuelle Verifikation ist der echte Mehrwert gegenueber rein automatischer Validierung
- Methode eignet sich als Pre-Curation Screening, nicht als Ersatz fuer fachliche Kuration
- Agents koennen Konsistenz und Schemata pruefen, aber nicht fachliche Richtigkeit garantieren
- Naechster Schritt: ZBZ-Fachleute pruefen dieselben 5 Docs im Curation Editor

### Technische Aenderungen
- `output/tei_final/` Verzeichnis angelegt (5 finale TEIs + 5 Review-JSONs + Summary)
- Validierungsreport aktualisiert: 284/285 VALID, 81 mit Warnings

### Konzeptionelle Arbeit
- **Agent-Based Quality Screening**: Agentengestuetzter Pre-Curation-Prozess mit strukturiertem Protokoll
- Positionierung: Vorpruefung fuer menschliche Kurator:innen, nicht Ersatz
- Output: Review-JSON pro Dokument + Sweep-Summary mit Mustern
- **Dreischichtung Command/Artifact/Tool**: Konzeptionelle Klarstellung fuer Paper.md
  - Command = Entscheidungsregel (wann was tun)
  - Artifact = materielles Werkzeug im Repo (Script, Index, Report)
  - Tool = konkreter Aufruf eines Artifacts durch den Agent
- Paper.md erweitert: Dreischichtung in Begriffsklaerung, Quality Screening als empirisches Beispiel in Verifikationskaskade
- **revisionDesc im TEI-Header** (E42): Jedes finale TEI hat Pipeline- und Screening-Status
- **output/tei_final/ als Single Source of Truth** (E43): Edition liest nur gescreente TEIs
- **Screening-Infrastruktur aufgebaut**: tei_screening_prep.py (Batch-Manifest, 4 Tiers, 58 Batches), tei_add_revision.py (revisionDesc-Injektion), tei_quality_pass.py (automatischer Check)
- **Erster echter Screening-Batch (10 Docs)**: 3 APPROVED, 6 APPROVED_WITH_NOTES, 1 NEEDS_REVIEW (Doc 660: OCR-Halluzinationen)
- **285/285 TEIs mit revisionDesc**: Status reist mit dem Dokument
- **generate_edition_data.py**: Liest aus tei_final/, Katalog enthaelt screening-Status fuer Frontend-Badges
- **Wikidata-Linking Batch-Run** gestartet (Hintergrund, 26% → Ziel >50%)

**Finales Screening-Ergebnis (285/285 Docs):**
- APPROVED: 210 (74%)
- APPROVED_WITH_NOTES: 43 (15%)
- NEEDS_REVIEW: 32 (11%)
- 58 Batches in 4 Tiers, parallelisiert ueber ~40 Agent-Invocations
- revisionDesc in alle 285 TEIs aktualisiert mit finalem Status
- 32 NEEDS_REVIEW Docs: Hauptursachen OCR-Halluzinationen bei Zeitungslayouts (8), Entity-False-Positives (15), Strukturprobleme (9)

### Dokumentation
- CLAUDE-COMMANDS.md: Quality Screening konkretisiert, Dreischichtung dokumentiert
- Arbeitsbericht: §3.5 Quality Screening + §6 Produktionsstand ergaenzt
- Knowledge-Dokumente: PLAN, PIPELINE, INDEX, PROJEKT, DECISIONS aktualisiert (Daten auf 2026-03-15)
- README: Pipeline-Diagramm + Komponenten-Tabelle um Quality Screening erweitert

### Entscheidungen
- E41: Agent-Based Quality Screening als Pre-Curation Workflow definiert
- E42: revisionDesc als Screening-Status im TEI-Header
- E43: output/tei_final/ als Single Source of Truth fuer die Edition
- E44: Entity-Stopwort-Erweiterung noetig (Mensch, Est, Gott, Rolle, Wahl etc.)

### Neue Muster (P7-P10)
- P7: Gattungsbegriffe im Entity-Index (Mensch, Est, Gott, Rolle, Wahl, Christ, Schweizer) erzeugen False Positives in ~30% der Docs
- P8: Journal de Geneve / mehrspaltige Zeitungslayouts versagen systematisch (OCR-Halluzinationen, Textduplikation)
- P9: Franzoesisches "Est-ce que" wird als placeName "Osten" gematcht
- P10: Tier-2-Docs (4-8 Seiten, gut formatiert) haben 85%+ APPROVED-Rate vs. Tier-1 (1-3 Seiten) mit 40%

---

## Aeltere Sessions (1-26)

Archiviert in [JOURNAL-ARCHIVE](JOURNAL-ARCHIVE.md). Zeitraum: 29. Jaenner - 15. Maerz 2026.
