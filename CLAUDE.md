# Claude Code Rules

Projekt-Konstitution. Operative Regeln und Konventionen, die bei jedem Pipeline-Schritt gelten.

## Workflow

1. **Journal fuehren:** jede Sitzung als Eintrag nach der Journal-Vorlage v0.2 in [knowledge/journal.md](knowledge/journal.md) dokumentieren: neuester Eintrag ganz oben unter "Eintraege", Felder Anlass / Ziel / Verlauf / Entscheidungen / Stand / Naechste Schritte (Format-Kontrakt + kopierbares Eintrags-Template stehen im Journal selbst). Sitzungen 1-68 bleiben unveraendert im Kompakt-Archiv.
2. **Wissen in `knowledge/`:** nicht in CLAUDE.md duplizieren. Single Source of Truth pro Fakt.
3. **Output nicht versionieren:** generierte Dateien gehoeren in `output/` (gitignored). Ausnahme: `data/curated_tei/` (vorgesehen fuer von Hand verifizierte TEI, derzeit leer).
4. **Vor Aenderungen testen:** Evaluierung laufen lassen, Metriken vergleichen.
5. **Single Source of Truth:** jeder Fakt steht in genau einem Dokument. Andere Dokumente verweisen via Cross-Reference.

## Knowledge Base

Einstiegspunkt: [knowledge/index.md](knowledge/index.md) — Navigation, Abhaengigkeiten, Schluesselkonzepte.

12 thematisch klar getrennte Dokumente:

- [projekt.md](knowledge/projekt.md) — Auftrag, Korpus, ZBZ-Workflow, Status
- [pipeline.md](knowledge/pipeline.md) — 6-Stufen-Pipeline, Engines, TEI-Mapping
- [workflow.md](knowledge/workflow.md) — End-to-End-Datenfluss, Save/Round-Trip, Provenance
- [quality.md](knowledge/quality.md) — CER + Validierung + Screening
- [viewer.md](knowledge/viewer.md) — Pipeline-Viewer (Faksimile + OCR + Layout + TEI + Editor)
- [frontend-gaps.md](knowledge/frontend-gaps.md) — Frontend-Befunde (Bugs/UX/A11y/Performance) je Schweregrad
- [oekosystem-synthese.md](knowledge/oekosystem-synthese.md) — Gesamtbild der drei Projekte (zbz / szd-htr / teiCrafter)
- [infrastruktur.md](knowledge/infrastruktur.md) — Azure, Podman, CI/CD
- [methodik.md](knowledge/methodik.md) — Promptotyping + epistemische Infrastruktur
- [decisions.md](knowledge/decisions.md) — Entscheidungsregister
- [journal.md](knowledge/journal.md) — chronologischer Sitzungs-Ueberblick
- [index.md](knowledge/index.md) — Navigation + Schluesselkonzepte

## Security

- **NIEMALS `.env` lesen:** die `.env`-Datei enthaelt API-Keys und darf unter keinen Umstaenden gelesen, angezeigt oder in Ausgaben aufgenommen werden
- **keine Secrets in Code oder Doku:** API-Keys, Tokens und Passwoerter ausschliesslich in Environment-Variablen

## Code-Konventionen

- **Code-Kommentare:** ausschliesslich Englisch, kompakt, und nur wo wirklich noetig — fuer Constraints, die der Code selbst nicht zeigt. Keine Erklaerungen des Offensichtlichen, keine Herkunfts- oder Aenderungsnotizen (kein "added 2026-06-10", kein "fixes H1") im Code; Entscheidungs-Provenienz gehoert in [knowledge/decisions.md](knowledge/decisions.md) bzw. ins Journal.
- **Keine Personennamen in Markdown:** in Repo-Markdown (knowledge/, README, reports/) Rollen und Organisationen verwenden (ZBZ, DHCraft, Projektleitung). Jeanne Hersch als Gegenstand des Korpus ist davon ausgenommen.
- **Keine Kostenangaben:** in Doku, Reports und Code keine Geldbetraege/Budgets (USD/$/CHF/EUR) nennen. Betriebshinweise wie `kostenlos`/`kostenpflichtig` (= kein/ein API-Call) sind erlaubt, da sie Aufrufe steuern, keine Kosten beziffern.
- **Windows-Encoding:** keine Unicode-Sonderzeichen in Print-Statements
- **Pfade:** absolute Pfade oder `pathlib`
- **Output:** JSON fuer Daten, HTML fuer Reports
- **Frontend:** ES6+ JavaScript (`const`/`let`, Arrow-Functions, Template-Literals, IIFE-Wrappers), `ZBZ.*` / `TeiViewer.*` Namespaces
- **Frontend-Dependencies:** zur Laufzeit via CDN nachgeladen, keine npm/Build-Pipeline:
  - OpenSeadragon 5.0.1 (jsDelivr) — Faksimile-Renderer im View-Modus (E58)
  - JSZip 3.10.1 (cdnjs) — ZIP-Bundle fuer Export-Modul (E61)

## Design

Bei UI- oder Frontend-Generierung ist [knowledge/viewer.md §Hersch Design-System](knowledge/viewer.md) die Wertequelle. Imperative Designprinzipien:

- ausschliesslich `--h-*`-Tokens, niemals Hex-Werte direkt im Komponenten-CSS
- Akzentfarben (Ziegelrot, Preussischblau, Olivgruen) gelten fuer Akzente und Status-Indikatoren, nicht fuer Flaechen
- keine reinen Schwarz/Weiss-Werte; immer den warmen Anthrazit `--h-text` und das warme Cream `--h-bg`
- bei neuen Komponenten zuerst pruefen, ob ein bestehender Token oder eine Komponente in `base.css` traegt

Token-Katalog: `docs/assets/css/tokens.css`. Basis-Komponenten: `docs/assets/css/base.css`. Viewer-spezifisch: `docs/assets/css/viewer.css`.

## Projektstruktur & Datenfluss

### Verzeichnisse (Orientierung)

- `data/` — Eingangs- und Referenzdaten. `source/` = ZB-Lieferung (immutabler Input, grösstenteils gitignored): `pdf/`, `reference_tei/`, `transkribus_page_xml/`, `masterfile/Masterfile.xlsx`, `guidelines/` (Editionsrichtlinien). Projekt-Autorität (git-tracked): `schema/zbz_hersch.rng`, `curated_tei/` (vorgesehen fuer von Hand verifizierte TEI, derzeit leer). Generiert: `doc_metadata.json` (Gemini-Cache)
- `scripts/` — Pipeline + Werkzeuge, nach Domaene gruppiert: `ocr/`, `layout/`, `tei/`, `eval/`, `edition/`, `core/` (nur `config.py` + `utils.py` top-level). Inventar: [scripts/README.md](scripts/README.md)
- `output/` — alle generierten Datenströme (gitignored, NICHT versioniert)
- `docs/` — statische Inspektions-/Demo-Site (GitHub-Pages-tauglich): HTML, `assets/` (`css/` + `js/`), `data/` (generierter Mirror), `images/`
- `knowledge/` — Wissensbasis (12 Docs), Einstieg [knowledge/index.md](knowledge/index.md)
- `tests/` — pytest-Suites

### Objekt = Bündel paralleler Datenströme

Ein **Objekt** (Dokument) trägt mehrere Ströme, alle nach `{doc_id}_p{N}`-Konvention:

- **OCR** — `output/mistral_results/` (Basis); alt. Engines: `output/ocr_results/`, `gemini_corrected_{a,b}/`, `llm_corrected_c/`
- **Layout / PAGE-XML** — `output/layout/` (Docling + Gemini, JSON) → `output/page_xml/` (PAGE-XML + METS-Export)
- **TEI** — `output/tei_unified/` (Pipeline-Output) → `output/tei_final/` (final, ausgeliefert)
- **Pro-Objekt-Metadaten** — `{doc_id}_manifest.json` (Workflow-Status je Strom + History + Leerseiten, E65/E66) neben dem finalen TEI. Legacy: `_screening_legacy.json` (abgeschafftes Agent-Screening, nur als Diagnose-Spur, gitignored).

Detaillierte Stufen / Skripte / Engines: [knowledge/pipeline.md](knowledge/pipeline.md).

### Source of Truth → generierter Mirror (verbindlich)

- **`output/tei_final/{doc}_final.xml` ist die Single Source of Truth der ausgelieferten TEI-Daten** (E43). Nur `tei_final/` wird angezeigt. Jedes finale TEI traegt `<revisionDesc>` mit Pipeline-Status (E42); der Workflow-Status pro Strom wird beim ZBZ-Uebergabe-Schritt via `tei_status_marker.py` aus dem Manifest in den `<revisionDesc>` projiziert (E66).
- **`docs/data/pages/{doc}/` ist ein GENERIERTER Mirror — niemals direkt editieren.** Erzeugt von `scripts/edition/generate_edition_data.py` aus: per-Seiten-TEI (aus `tei_final` gesplittet) + Mistral-`.md` + Layout-JSON. Nach Aenderungen an der Quelle Mirror neu generieren.
- `output/tei_unified/` ist Pipeline-Output (nicht editieren). Von Hand verifizierte TEIs sind fuer `data/curated_tei/` (git-tracked) vorgesehen; der Ordner ist derzeit leer.

## Methodik

Dreischichtung Command / Artifact / Tool — Details: [knowledge/methodik.md](knowledge/methodik.md).

- **Command** = Entscheidungsregel (wann was tun)
- **Artifact** = materielles Werkzeug im Repo (Script, Index, Report)
- **Tool** = konkreter Aufruf eines Artifacts durch den Agent

Verifikationskaskade (oekonomisch geordnet): automatisch → kontextuell → visuell → fachlich.
Operative Werkzeuge und Arbeitszyklus: [knowledge/methodik.md](knowledge/methodik.md).

---

# Commands (CLI-Referenz)

Operative Werkzeuge fuer den Promptotyping-Zyklus. Jede Operation erzeugt Qualitaetssignale,
die den naechsten Schritt informieren. Der Critical Expert in the Loop entscheidet.

Methodische Einbettung (Diagnose → Exploration → Ausfuehrung → Re-Validierung → Eskalation):
[knowledge/methodik.md](knowledge/methodik.md). Konventionen (`--dry-run`, `--force`, `--reassemble`): siehe dort.

## Diagnose

```bash
python -m scripts.tei.tei_validator --doc {DOC_ID}             # TEI-Validierung
python -m scripts.tei.tei_validator --all --html-report         # Korpus-Report
python -m scripts.tei.tei_validator --compare-ref               # Referenz-Vergleich (25 ZBZ-Referenz-TEIs)
python -m scripts.eval.evaluate_ocr --all                            # OCR-Metriken
python -m scripts.eval.quality_proxy --all --html                    # Quality Proxy (Hit Rate)
python -m scripts.eval.completeness_check --html                     # Vollstaendigkeits-Check (Seiten)
python -m scripts.eval.benchmark_cer --all --html                    # CER-Benchmark (25 GT-Docs)
python -m scripts.eval.cer_statistics_full --seed 42 --bootstrap-n 10000  # wiss. CER-Statistik (BCa-CIs, Paired, HCPR)
python -m scripts.eval.corpus_audit                             # Korpus-Audit: Trichter 325->289->286->285 + Drift-Check
python -m scripts.eval.structure_audit                          # Struktur-Audit: Pipeline-TEI vs 25 Ground Truth (Diagnose, kein Gate; E84)
python -m pytest tests/test_cer_statistics.py -q                # 55 Tests fuer Statistik-Library
python -m pytest tests/test_corpus_audit.py -q                  # 24 Tests: Korpus-Invarianten + delivered-Verteilung + Vollstaendigkeits-Gate
python -m pytest tests/test_scripts_health.py -q                # Script-Health: Syntax + interne Imports (alle scripts/)
python -m pytest tests/test_tei_schema.py -q                    # Schema-Gate: tei_final gegen zbz_hersch.rng (E68)
python -m pytest tests/test_tei_header.py -q                    # teiHeader-Liefer-Vertrag: idno + biblStruct + langUsage (E69)
python -m pytest tests/test_tei_validator.py -q                 # Validator: Referenz-CER in Prozent (O24/E69)
python -m pytest tests/test_pb_split.py -q                      # <pb>-Segmentierung: pb_split.py byte-identisch (E69)
python -m pytest tests/test_tei_conformance.py -q               # Konformitaets-Fixes: div-n/type, figure-xmlid, head-lemma, title-main, foreign-lang (E84)
```

Output `docs/data/cer_statistics.json` (regenerierbar, derzeit nicht eingecheckt). Das interaktive CER-Dashboard wurde mit E56 abgeschafft. Methodik: [knowledge/quality.md §CER-Methodik](knowledge/quality.md).

## Textschicht

```bash
python scripts/ocr/ocr_pipeline.py -i data/source/pdf/{DOC_ID}.pdf -e mistral    # Basis-OCR
python -m scripts.ocr.gemini_ocr_correct --doc {DOC_ID} --variant B          # Gemini-Korrektur
python -m scripts.ocr.gemini_ocr_correct --doc {DOC_ID} --dry-run            # Vorschau
```

## Layout

```bash
python -m scripts.layout.run_layout_analysis --doc {DOC_ID}                     # Docling
python -m scripts.layout.layout_qa_gemini --doc {DOC_ID}                        # Gemini QA
python -m scripts.layout.layout_qa_gemini --mode detect --doc {DOC_ID}          # Neudetektion
python -m scripts.layout.generate_layout_overlays --doc {DOC_ID} --compare      # Overlay
```

## TEI erzeugen

```bash
python -m scripts.tei.tei_unified --doc {DOC_ID}                         # Standard (3 Stufen)
python -m scripts.tei.tei_unified --doc {DOC_ID} --step 1                # nur Scaffold (kostenlos)
python -m scripts.tei.tei_unified --doc {DOC_ID} --reassemble            # Re-Assembly (Gemini-Cache; kuratierte Seiten je 1 Call)
python -m scripts.tei.tei_unified --doc {DOC_ID} --force                 # alles neu (inkl. Gemini)
python -m scripts.tei.tei_unified --doc {DOC_ID} --dry-run               # Prompt-Vorschau
python -m scripts.tei.tei_unified --all --reassemble                     # Korpus Re-Assembly
```

## Validierung (Qualitaetsgate)

```bash
python -m scripts.tei.tei_validator --doc {DOC_ID}                       # Einzeldokument
python -m scripts.tei.tei_validator --all --report                       # JSON-Report
python -m scripts.tei.tei_validator --all --html-report                  # HTML-Report
```

## Quality Screening (deprecated, E66)

Das Agent-basierte 7-Schichten-Screening ist seit E66 (2026-05-26) **abgeschafft**. Keiner der
285/285 "APPROVED"-Status kam von einem Menschen — der Agent zertifizierte sich selbst mit
eingebauter Ignorier-Liste (W3/W6/W10 als "normal"). Befunde leben jetzt als `_screening_legacy.json`
(reine Diagnose-Spur, nicht im Mirror). Ersatz: **Workflow-Status pro Strom** (siehe unten).

Tools fuer Validierung bleiben:

```bash
python -m scripts.tei.tei_validator --doc {DOC_ID}                       # RelaxNG + Projektregeln
python -m scripts.tei.tei_validator --compare-ref --doc {DOC_ID}         # gegen ZBZ-Referenz
```

## Pro-Objekt-Manifest (Leerseiten + Workflow-Status, E65/E66)

```bash
python -m scripts.edition.page_manifest                                          # alle 285 Docs (idempotent: status+history bleiben)
python -m scripts.edition.page_manifest --doc {DOC_ID}                           # Einzeldokument
python -m scripts.edition.page_manifest --dry-run                                # nur Bericht, nichts schreiben
python -m scripts.tei.tei_blank_marker --dry-run                         # Leerseiten-Marker: Vorschau
python -m scripts.tei.tei_blank_marker                                   # <pb type="blank"/> in tei_final schreiben (mit Backup)
python -m scripts.tei.tei_status_marker --dry-run                        # Workflow-History -> revisionDesc: Vorschau
python -m scripts.tei.tei_status_marker                                  # History als <change> in tei_final schreiben (mit Backup, ZBZ-Uebergabe)
```

Pro-Objekt-Manifest `output/tei_final/{DOC_ID}_manifest.json` ist der **Annotations-Slot pro Objekt**:
- `streams.{ocr,layout,tei}.status` — Workflow-Status (unverifiziert | in_arbeit | verifiziert, drei Stufen seit E77). Ampel-Mapping im UI: neutral/grau fuer `unverifiziert`, gelb fuer `in_arbeit`, gruen fuer `verifiziert`, rot reserviert fuer einen kuenftigen Problem-Status.
- `streams.{ocr,layout,tei}.history` — Provenienz der menschlichen Bearbeitungsschritte
- `pages.{N}` — Ausnahme-Seiten (aktuell nur sichere Leerseiten; OCR-Regel + Docling=0)

`page_manifest` befuellt automatisch nur Engine-Deskriptoren und die sichere `blank`-Klasse;
Status/History werden ausschliesslich vom Viewer (Klick auf Status-Pill) ergaenzt und bleiben
ueber Re-Laeufe erhalten. `tei_blank_marker` projiziert Leerseiten als `<pb type="blank"/>`;
`tei_status_marker` projiziert die Workflow-History deterministisch als `<change>` in den
`<revisionDesc>` und raeumt dabei die irrefuehrenden Agent-Screening-Eintraege weg. Danach Mirror neu:
`python -m scripts.edition.generate_edition_data --mirror-only`. Details: [knowledge/decisions.md](knowledge/decisions.md) E63/E65/E66.

## Viewer-Daten

```bash
python -m scripts.edition.generate_edition_data                                  # Katalog (data/catalog.json) + Per-Seiten-Mirror
```

Der Viewer (`docs/viewer.html`) ist eine statische Single-Page-App ohne Backend. **Ein** "Speichern"-Knopf
sichert alle ungespeicherten Stroeme zugleich (Layout, Text/TEI, Manifest, E78); geschrieben wird direkt
in den Working Tree (File System Access API, Chromium) oder als Datei-Download (Fallback). Jede
Speicher-Aktion legt die Nutzlast doppelt ab: kanonisch nach `output/` (von `--reassemble` real konsumiert, E72)
und in den Mirror `docs/data/`, damit der server-lose Viewer (Docroot `docs/`) den Stand nach einem Reload zeigt (E79).
Einzel-Downloads pro Strom liegen im "Export ▾"-Dropdown. Siehe [knowledge/viewer.md §Persistenz](knowledge/viewer.md).

## Visuelle Artefakte

```bash
python scripts/edition/extract_pages.py --pdf {DOC_ID}.pdf --dpi 300             # Seitenbilder
python -m scripts.layout.generate_layout_overlays --doc {DOC_ID} --compare      # Layout-Overlay
```

## Transkribus-Export / Upload (PAGE-XML-Round-Trip)

Pipeline-PAGE-XML (`output/page_xml/`) zurueck nach Transkribus: erst Bundle bauen, dann via REST hochladen.
Konzept + Dialekt-Details: [knowledge/pipeline.md §Transkribus-Export](knowledge/pipeline.md).

```bash
python -m scripts.edition.transkribus_export --sample                            # stratifizierte Stichprobe (~18) -> output/transkribus_upload/
python -m scripts.edition.transkribus_export --all                               # kompletter Korpus
python -m scripts.edition.transkribus_export --reference                         # die 24 Objekte, die ZBZ schon in Transkribus hat
python -m scripts.edition.transkribus_export --doc {DOC_ID} [--zip]              # gezielt (+ optional ein .zip je Objekt)
```

Upload braucht den Login als Umgebungsvariablen (NIE im Code/Repo/.env): `TRANSKRIBUS_USER`, `TRANSKRIBUS_PASSWORD`,
optional `TRANSKRIBUS_COLLECTION`. Jeder Lauf legt NEUE Dokumente an (kein Dedup) -- erst `--dry-run`, dann ein Testobjekt.

```bash
python -m scripts.edition.transkribus_upload --dry-run --collection {COLL}       # Login + Collection-Zugriff pruefen, nichts hochladen
python -m scripts.edition.transkribus_upload --doc {DOC_ID} --collection {COLL}  # ein Objekt testweise hochladen
python -m scripts.edition.transkribus_upload --collection {COLL}                 # ganzes Bundle hochladen
```

---

# Hilfe

- `/help` — Hilfe zur Verwendung von Claude Code
- Feedback: https://github.com/anthropics/claude-code/issues
