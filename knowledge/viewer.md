---
type: knowledge
created: 2026-03-09
updated: 2026-05-25
tags: [zbz-ocr-tei, viewer, frontend, editor, osd]
status: active
---

# Pipeline-Viewer

Interne Web-UI zur Inspektion und Kuration der Pipeline-Ergebnisse (OCR, Layout, TEI).
Ersetzt seit E56 (2026-04-27) die zuvor vorhandene oeffentliche Edition und die separaten
Diagnostik-/CER-Dashboards.

**Zweck:** Inspektion und Korrektur der Pipeline-Ergebnisse. Drei konkrete Funktionen:
QA der OCR-/Layout-/TEI-Ergebnisse, manuelle Korrektur durch Human-in-the-Loop,
Demonstration gegenueber ZBZ. Der Viewer zeigt die **ausgelieferte Edition = Mistral-OCR**;
der frueher hier moegliche Engine-Vergleich liegt seit E64 ausserhalb des Viewers
(CER-Benchmark + Methode-Seite, E62). Nicht gedacht als oeffentliche Edition oder
Lese-Frontend — das macht ZBZ ueber Oxygen/Alma.

**Vier Seiten:** Korpus-Uebersicht (`index.html`: filter- und sortierbare Doc-Liste mit
Workflow-Status pro Strom, E66), der eigentliche Viewer (`viewer.html`: Faksimile + Layout-Overlay links,
Transkription/TEI rechts), eine Methode-Seite (`methode.html`: CER-Headline + stratifizierte
Werte + Limitations + Literatur-Vergleich, E62, statisch) und eine About-Seite (`about.html`).
Der Viewer kennt drei Modi: *Anzeigen*, *Layout bearbeiten*, *Text bearbeiten*.
Persistenz erfolgt server-los ueber **einen** Speichern-Knopf: er sichert alle ungespeicherten
Stroeme (Layout, Text, Workflow-Status) in einem Akt -- direkt in den Repo-Klon via File System
Access API (Chromium) oder als Datei-Download (Fallback) -- und spiegelt sie zugleich in den
Viewer-Mirror (`docs/data/`), damit ein Reload den Stand zeigt (E72/E78/E79).

**In Umbau (Mai 2026 Edition-Uplift-Welle):** Mode-Buttons sind Edit-Toggle pro Panel
(E60, erledigt; benannt "Layout"/"Text", E64), Faksimile-Renderer ist im View-Modus auf
OpenSeadragon umgestellt (E58, Pan + Zoom + Rotate), Layout-Editor wird mit
OSD-Koordinaten-Conversion neu verdrahtet. Polygon-Support
bewusst ausgeschlossen (E59) — Hersch-Druck reicht mit Rechtecken. Plan-Dokument:
`C:\Users\Chrisi\.claude\plans\edition-uplift-three-pages.md`.

---

## Architektur

```
docs/
├── index.html                   # Korpus-Uebersicht: filter-/sortierbare Doc-Liste, Workflow-Status pro Strom (E66)
├── viewer.html                  # Doc-Detail: Faksimile + Layout-Overlay + OCR/TEI-Panel, 3 Modi
├── methode.html                 # CER-Methodik, Headline, Stratifiziert, Limitations, Literatur (E62, statisch)
├── about.html                   # Projekt-Seite (verweist auf methode.html fuer Qualitaets-Details)
├── assets/
│   ├── css/
│   │   ├── tokens.css               # Hersch Design Tokens (--h-*)
│   │   ├── base.css                 # Reset, Typography, Buttons, Badges, Tabs
│   │   ├── viewer.css               # Viewer-Shell, Faksimile-Overlay, TEI-Render, Editor-UI
│   │   └── catalog.css              # Korpus-Uebersicht: Status-Leiste, Filter, Doc-Tabelle
│   └── js/
│       ├── core.js                  # DOM, URL, Fetch, Format, Cache, Toast, EventBus, Markdown-Renderer
│       ├── viewer.js                # Viewer-Orchestrator: Doc-Selektion + Mode-Switching
│       ├── catalog.js               # Korpus-Uebersicht: Laden, Filter (Strom × Status, E66), Sortierung
│       ├── tei-render.js            # TEI-XML → DOM
│       ├── layout-editor.js         # BBox Drag/Resize/Add/Delete + Reading-Order
│       ├── transcription-editor.js  # OCR/TEI/XML mit contenteditable
│       ├── fs-access.js             # Direkt-Schreiben in den Working Tree (File System Access API, E72)
│       └── download.js              # Datei-Download (JSON/MD/XML)
└── data/                        # generiert via scripts/edition/generate_edition_data.py
    ├── catalog.json             # 285 Docs (id, title, author, lang, type, page_count, streams.{ocr,layout,tei}.{status,last_at,last_by})
    ├── manifests/{doc}.json     # Mirror der Pro-Objekt-Manifeste (Workflow + History + Leerseiten, E66)
    ├── search_index.json        # Volltext fuer Doc-Suche
    ├── tei/                     # 285 finale TEIs (*_final.xml; legacy *_screening_legacy.json bleibt gitignored im output/)
    ├── pages/                   # alle 285 Docs: Layout-JSONs + Mistral-OCR + per-Seiten-TEI
    └── examples/                # Legacy: 4 DEMO-Docs (Backward-Kompatibilitaet)
```

**Volumen:** 5 HTML, 4 CSS, 8 JS-Module (alle als IIFE im `ZBZ.*`-Namespace). Die Korpus-Uebersicht
(`index.html` + `catalog.js` + `catalog.css`) und die About-Seite kamen nach der E56-Radikalkur
hinzu (Commit „Korpus-Uebersicht + Top-Nav"); die Methode-Seite folgte 2026-05-26 (E62).

**CDN-Dependencies:**

| Library | Version | CDN | Zweck |
|---|---|---|---|
| OpenSeadragon | 5.0.1 | jsDelivr | Faksimile-Renderer (Pan/Zoom/Rotate) im View-Modus (E58) |
| JSZip | 3.10.1 | cdnjs | GEPLANT (E61) fuer Multi-Datei-Export, im Code noch nicht eingebunden |

OpenSeadragon wird zur Laufzeit aus dem CDN nachgeladen; JSZip ist geplant (E61), aber noch nicht eingebunden. Keine npm/Build-Pipeline.

---

## Drei Modi

| Modus | Editierbar | Zweck | Persistenz |
|---|---|---|---|
| **Anzeigen** | nein | reine Inspektion (read-only) | — |
| **Layout bearbeiten** | Layout-Overlay | Regionen (BBox, Typ, Reihenfolge) korrigieren | "Speichern" (alle Stroeme zugleich), siehe §Persistenz |
| **Text bearbeiten** | Text-Panel | OCR-Text oder TEI-Text/XML korrigieren | "Speichern" (alle Stroeme zugleich), siehe §Persistenz |

Je ein Edit-Toggle im Panel-Header (E60): das Faksimile-Panel traegt den Knopf
**"Layout bearbeiten"**, das Text-Panel **"Text bearbeiten"** (E78). Aktiv = anthrazit-gefuellter
Knopf (Farbe zeigt den Modus, E64). Im Layout-Modus erscheint eine zweite Toolbar mit
Regions-Tools (`+ Region`, `Loeschen`, Typ-Dropdown). Die Seitennavigation (prev/page-info/next)
sitzt im Faksimile-Panel-Header neben der Regionen-Zahl (E78). Die globale Mode-Leiste
(Anzeigen/Layout/Transkription) entfiel mit E60 — Begruendung: Wortdoppelung "Transkription"-Mode
mit "OCR"-Source.

---

## Layout-Editor

| Operation | Bedienung |
|---|---|
| Region selektieren | Klick |
| Region verschieben | Drag |
| Region skalieren | Eckpunkt ziehen (NW/NE/SW/SE) |
| Region-Typ aendern | Dropdown in Toolbar (Heading/Paragraph/Footnote/Caption/Filter/Skip) |
| Region hinzufuegen | Toolbar `+ Region` → auf leere Faksimile-Flaeche ziehen |
| Region loeschen | `Delete`-Taste oder Toolbar-Button |
| Reading-Order aendern | Drag-and-Drop in der Region-Liste unter dem Faksimile |

Koordinaten sind in Prozent (0-100) relativ zum Bild — kompatibel mit dem bestehenden
Layout-JSON-Format (`bbox.x_pct/y_pct/w_pct/h_pct`).

### Region-Typen

Aus `tokens.css`-Status-Farben, kompatibel mit `zbz_tag` aus der Pipeline:

| `zbz_tag` | Label | Farbe |
|---|---|---|
| `zb_heading` | Heading | Ziegelrot |
| `zb_paragraph` | Paragraph | Anthrazit |
| `footnote` | Fussnote | Preussischblau |
| `caption` | Caption | Olivgruen |
| `_filter` | Filter (entfernen) | grau, gestrichelt |
| `_skip` | Skip | hellgrau, gepunktet |

---

## Transcription-Editor

Editiert das aktive Text-Panel via `contenteditable`. Drei Quellen waehlbar:

| Quelle | Format | Editiert man… |
|---|---|---|
| **OCR** | Markdown | rohen OCR-Text aus Mistral/Gemini/Haiku |
| **TEI** | gerendertes TEI | nur Text-Inhalte (keine Struktur — fuer Tags den XML-Modus nutzen) |
| **XML** | TEI-XML mit Syntax-Highlighting | rohes XML inklusive Tags und Attribute |

Aenderungen werden debounced eingesammelt und als ungespeichert markiert; der gemeinsame
**Speichern**-Knopf sichert sie zusammen mit Layout und Status (siehe §Persistenz). Einzeln
exportieren laesst sich der Text/TEI ueber **Export ▾** (E78).

---

## Persistenz

Kein Server. **Ein** "Speichern"-Knopf sichert alle ungespeicherten Stroeme als einen Akt --
Layout (aktuelle Seite), Text bzw. TEI (aktuelle Seite, je nach Text-Quelle) und das
Pro-Objekt-Manifest (Workflow-Status + Provenienz). Jeder Strom landet an seiner kanonischen
Stelle im Repo (`saveAll()` in `viewer.js`). Zwei Schreibwege, je nach Browser (E72):

**1. Direkt-Schreiben (File System Access API, Normalweg, Chromium).** Beim ersten Speichern
fragt der Viewer einmal nach dem Repo-Wurzelordner (`connectWithInfo()` mit Erst-Info-Modal:
welcher Ordner = `zbz-ocr-tei`, was geschrieben wird) und erteilt Schreibrecht; danach schreiben
Speicher-Aktionen direkt in den Working Tree. Der Handle bleibt in IndexedDB; Schreibrecht muss
pro Sitzung per Geste re-granted werden. Ein Plausibilitaetscheck (`looksLikeRepoRoot`: `docs/` +
`scripts/`) warnt bei falscher Ordnerwahl. Modul: `docs/assets/js/fs-access.js` (`ZBZ.FsAccess`).
Funktioniert unter `localhost` und HTTPS; geschrieben wird stets in den lokalen Klon, nie auf einen Server.

**2. Download (Fallback, alle Browser).** Ohne FSA (Firefox/Safari) oder bei abgebrochener
Ordnerwahl bietet `ZBZ.Download` (`docs/assets/js/download.js`) die Datei als Download an.
Die Einzel-Downloads pro Strom bleiben zusaetzlich als **"Export ▾"**-Dropdown erreichbar (E78).

Das Bearbeiterkuerzel (ZBZ-Partner) steht als **Identity-Chip** neben dem Speichern-Knopf und
geht in die Manifest-History ein (`{at, by, from, to}`); kein blockierendes `prompt()` mehr.

**Doppel-Schreibung kanonisch + Mirror (E79).** Der server-lose Viewer laeuft mit Docroot=`docs/`
und liest beim Reload **nur** aus `docs/data/` (`output/` ist von dort nicht erreichbar). Damit ein
gespeicherter Edit den Reload ueberlebt, schreibt jede Speicher-Aktion die identische Nutzlast an
**zwei** Orte -- den kanonischen `output/`-Pfad (Pipeline-Konsum) **und** den Mirror unter `docs/data/`:

| Strom | Kanonisch (Pipeline liest) | Mirror (Viewer-Reload liest) |
|---|---|---|
| Layout | `output/layout/{doc}/{doc}_p{NNN}_layout_curated.json` | `docs/data/pages/{doc}/{doc}_p{NNN}_layout_curated.json` |
| OCR/Text | `output/ocr_curated/{doc}_p{N}.md` | `docs/data/pages/{doc}/{doc}_p{N}.md` |
| Manifest | `output/tei_final/{doc}_manifest.json` | `docs/data/manifests/{doc}_manifest.json` |
| TEI | `output/tei_final/{doc}_final.xml` | `docs/data/pages/{doc}/{doc}_final.xml` |

Pipeline-Praezedenz: `load_layout_gemini` liest curated > gemini > docling; `OCR_CURATED_DIR` ist
erstes Element in `_OCR_DIRS` (`scripts/core/loaders.py`). Viewer-Praezedenz: `fetchLayout` probiert
`layoutCurated > gemini > docling` (E79). `generate_edition_data --mirror-only` reproduziert exakt
dieselben Mirror-Dateien -> kein Drift.

Caveat TEI: `output/tei_final/{doc}_final.xml` ist die **Single Source of Truth**; ein spaeterer
`--reassemble` regeneriert sie aus OCR+Layout und ueberschreibt einen manuellen TEI-Edit wieder
(die Per-Seiten-TEI-Splits im Mirror entstehen ohnehin erst beim Reassemble). Fuer dauerhafte
Korrekturen daher Layout/OCR editieren und neu zusammenbauen, nicht das finale TEI direkt.

Nach dem Schreiben faltet ein Pipeline-Lauf die Kuration ins TEI und regeneriert den Mirror:

```bash
python -m scripts.tei.tei_unified --doc {DOC} --reassemble ; python -m scripts.edition.generate_edition_data --mirror-only
```

`data/curated_tei/` bleibt der Gold-Standard-Speicher fuer kuratierte TEIs (git-tracked).
Der frueher vorhandene FastAPI-Curation-Server (`scripts/server/curation_server.py`) wurde mit E57
geloescht, weil das Frontend ihn seit E56 nicht mehr ansteuert.

### Export-Modul (Einzel-Export umgesetzt, ZIP-Bundle weiter Roadmap)

> Stand 2026-06-07: Die **Einzel-Downloads pro Strom** sind als **"Export ▾"**-Dropdown in der
> Doc-Subbar umgesetzt (Layout/Text/TEI/Manifest je einzeln, E78). Das hier beschriebene
> **Komplett-/Multi-Doc-ZIP** (JSZip) ist weiter Roadmap -- es gibt noch kein JSZip-CDN-Tag und
> kein `ZBZ.Export`.

Das geplante ZIP-Bundle zusaetzlich zum Einzel-Export:

| Ort | Funktion | Granularitaet |
|---|---|---|
| Doc-Subbar im Viewer | "Alles ↓" oeffnet Export-Drawer mit Checkboxen pro Datentyp | ein Dokument, alle Seiten, alle Engines |
| Aktionsleiste in `index.html` | Multi-Select-Checkboxen + Sticky-Bar "N ausgewaehlt · Export ▾" | mehrere Dokumente aus aktuellem Filter |

Exportierbare Datentypen pro Dokument:

- Faksimile-PNGs (alle Seiten, `images/{doc}/{doc}_pNNN.png`)
- OCR-Rohtext pro Engine (Mistral / Gemini A / Gemini B / LLM)
- Layout-JSON (Docling + Gemini-Varianten)
- TEI per-Seite (`*_p001.xml` ... `*_pNNN.xml`)
- TEI final (`*_final.xml`)
- Pro-Objekt-Manifest (`*_manifest.json`, Workflow-Status + History, E66)
- Legacy: Review-JSON (`*_screening_legacy.json`, abgeschafftes 7-Schichten-Screening, nur als Diagnose-Spur)
- PAGE-XML pro Seite, falls vorhanden

Bei einer Datei: direkter Download. Bei mehreren: ZIP-Bundle mit Verzeichnis-Struktur
`{doc_id}/{kategorie}/{datei}` plus Top-Level `manifest.json` (Zeitstempel, Auswahl,
Datei-Liste). Library: **JSZip 3.10.1** via cdnjs, ZIP-Erzeugung im Browser. Bei
Multi-Doc-Export ueber 50 Docs: Warnhinweis wegen Browser-Memory.

---

## Datenquellen

`viewer.html` laedt ausschliesslich statische Daten — keine API-Calls.

| Daten | Pfad (primaer) | Fallback | Quelle |
|---|---|---|---|
| Korpus-Liste | `data/catalog.json` | — | `scripts/edition/generate_edition_data.py` |
| Thumbnail | `data/thumbs/{doc}.jpg` | — | `scripts/edition/generate_edition_data.py` (PIL, 140x200, JPEG q=70) |
| Faksimile | `images/{doc}/{doc}_pNNN.png` | — | Pipeline (`scripts/edition/extract_pages.py`) |
| Layout (Gemini) | `data/pages/{doc}/{doc}_pNNN_layout_gemini.json` | `../output/layout/` | `scripts/layout/layout_qa_gemini.py` |
| Layout (Docling) | `data/pages/{doc}/{doc}_pNNN_layout.json` | `../output/layout/` | Pipeline |
| OCR Mistral | `data/pages/{doc}/{doc}_pN.md` | `../output/mistral_results/` | Pipeline |
| OCR (andere) | — | `../output/{source}/...` | nur lokal: Gemini A/B, LLM |
| TEI pro Seite | `data/pages/{doc}/{doc}_pN.xml` | `../output/tei_unified/` | aus `_final.xml` extrahiert |
| TEI final | `data/pages/{doc}/{doc}_final.xml` | `../output/tei_final/` | `output/tei_final/` |

Alle 285 Docs haben vollstaendige Per-Seiten-Daten in `docs/data/pages/` (Layout, Mistral-OCR, TEI)
und ein Thumbnail in `docs/data/thumbs/`. Damit funktioniert der Viewer ohne lokalen Server fuer
das gesamte Korpus. Die alternativen OCR-Engines (Gemini A/B, LLM) bleiben unter
`output/` und sind nur lokal abrufbar. Der Viewer bietet seit E64 **keinen OCR-Quellen-Umschalter**
mehr — er zeigt ausschliesslich Mistral (die ausgelieferte Edition); die Alt-Engines sind reine
Benchmark-Artefakte (E51/E54) und nicht Teil der Edition.

### Leerseiten (E63 + Schritt 3, E67)

Vorsatz-, Rueck- und Durchschlagseiten liefern nur Muell-OCR (`.`, `^{}[]`, leeres Tabellengeruest)
und das Gemini-Layout-QA halluziniert dort Phantom-Regionen (Docling sagt korrekt 0). Korpusweit
79 sichere Leerseiten in 15 Docs.

Erkennung im Viewer (`detectBlankPage` in `viewer.js`) liest **primaer den `<pb type="blank"/>`-
Marker aus der per-Seiten-TEI** (deterministisch, von `tei_blank_marker.py` projiziert -- E65).
Fallback nur fuer Faelle ohne TEI: die OCR-Heuristik `ZBZ.isBlankPageText` (getrimmter Text
<=5 Zeichen ODER ohne Buchstaben/Ziffern). Damit ist die Regel-Duplikation JS/Python aufgeloest --
die Markierungs-Wahrheit lebt im TEI bzw. im Pro-Objekt-Manifest, der Viewer nur projiziert.
Bei Leerseiten zeigt der Faksimile-Header "Leerseite", das Text-Panel den ruhigen Hinweis
"Leerseite — kein Text", Phantom-Boxen werden unterdrueckt. Details: [decisions.md](decisions.md) E63/E65/E67.

---

## Hersch Design-System

Die Edition-Designhaltung bleibt erhalten — nur die "Edition als Lese-Web"-Komponenten sind weg.
Tokens und Komponenten sind in `tokens.css`, `base.css`, `viewer.css`.

### Kernprinzipien

| Entscheidung | Begruendung |
|---|---|
| EB Garamond (Serif) als Grundschrift | humanistische Tradition des frankophonen Raums |
| Jost (geometrische Sans) fuer Headings | formale Klarheit als Kontrapunkt |
| Kleine Terz (1.2) als Typoskala | feine Differenzierung |
| kein reines Schwarz/Weiss | Denken im Gebrochenen |
| Ziegelrot `#8B3A3A` als Primaer-Akzent | existenzielle Leiblichkeit |
| Preussischblau `#2B4C7E` als Sekundaer-Akzent | Universalitaetsanspruch |
| Olivgruen `#6B7B5E` als Tertiaer-Akzent | natuerliche Gelassenheit |
| warmer Anthrazit `#2C2825` statt Navy | Materialitaet von Druckerschwarz auf Papier |

### Token-Schicht

`tokens.css` definiert die Hersch-Werte (`--h-*`). `base.css` baut die Komponenten-Layer
darauf auf (`.btn`, `.badge`, `.card`, `.input`, `.tabs`, `.toast`). `viewer.css` enthaelt
den App-spezifischen Layout-Code (Sidebar, Faksimile-Overlay, TEI-Renderer-Klassen, Editor-UI).

### Imperative Designprinzipien

- ausschliesslich `--h-*`-Tokens, niemals Hex-Werte direkt im Komponenten-CSS
- Akzentfarben (Ziegelrot, Preussischblau, Olivgruen) fuer Akzente und Status-Indikatoren, nicht fuer Flaechen
- kein reines Schwarz/Weiss
- bei neuen Komponenten zuerst pruefen, ob ein bestehender Token traegt

---

## Deployment

Der Viewer ist eine reine Static-Site und kann ohne Backend ueber GitHub Pages
ausgeliefert werden. Quellverzeichnis ist `docs/`.

### Lokaler Server (volle Funktionalitaet inklusive aller OCR-Engines)

```bash
cd c:/Users/Chrisi/Documents/GitHub/DHCraft/zbz-ocr-tei
python -m http.server 8000 -d docs
# oder fuer ../output/ Fallback (Gemini A/B, LLM):
python -m http.server 8000
```

Im zweiten Fall ist der Viewer unter `http://localhost:8000/docs/viewer.html` erreichbar
und kann auf alle OCR-Engines im `output/`-Tree zugreifen.

### GitHub Pages

In den Repo-Einstellungen unter Settings → Pages: Source auf "Deploy from a branch",
Branch `main`, Folder `/docs`. Die `.nojekyll`-Datei im Verzeichnis verhindert, dass Pages
die Inhalte als Jekyll-Site interpretiert.

**Wichtige Einschraenkung:** `docs/images/` ist via `.gitignore` ausgenommen
(4 GB PNG-Daten zu gross fuer Git), bis auf die vier DEMO-Docs (1000, 1330, 1540, 2310).
Auf GitHub Pages sieht man fuer alle anderen Docs OCR/Layout/TEI-Texte, aber kein Faksimile.
Fuer eine vollstaendige Online-Inspektion brauchen die Bilder einen externen Host (IIIF-Server,
S3, CDN) und einen anpassbaren `ZBZ.path.image()` mit `BASE_URL`-Variable.

### Daten regenerieren

Wenn sich Pipeline-Output oder Workflow-Status (Manifest) aendert:

```bash
python -m scripts.edition.generate_edition_data                  # voller Lauf inkl. Per-Seiten-Mirror
python -m scripts.edition.generate_edition_data --mirror-only    # nur pages/ neu aufbauen
python -m scripts.edition.generate_edition_data --no-mirror      # nur Katalog + Indices
```

Der Per-Seiten-Mirror (`docs/data/pages/`) ist ~99 MB, ca. 16.500 Dateien. Bei jeder
Aenderung am `output/tei_final/` sollte er neu erzeugt werden.

---

## Verweise

- [pipeline.md](pipeline.md) — Pipeline-Output, der vom Viewer angezeigt wird
- [quality.md](quality.md) — Diagnostik-Daten in `docs/data/` (CER, TEI-Quality)
- [workflow.md](workflow.md) — End-to-End-Datenfluss, Save-Mechanismus, Round-Trip vom Edit zur regenerierten TEI, Provenance-Konzept, geplante `_complete.xml`-Variante
- [decisions.md](decisions.md) — E56 (Frontend-Reduktion auf Viewer-only), E57 (Per-Seiten-Mirror + Pages-Deploy), E58 (OpenSeadragon), E59 (Polygone verworfen), E60 (Mode-Button-Redesign Option C), E61 (Export-Modul JSZip)
- Plan-Dokument: `C:\Users\Chrisi\.claude\plans\edition-uplift-three-pages.md`
