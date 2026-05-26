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

**Zweck:** Inspektion und Korrektur der Pipeline-Ergebnisse. Vier konkrete Funktionen:
QA der OCR-/Layout-/TEI-Ergebnisse, manuelle Korrektur durch Human-in-the-Loop,
Engine-Vergleich (Mistral/Gemini/DeepSeek), Demonstration gegenueber ZBZ. Nicht
gedacht als oeffentliche Edition oder Lese-Frontend — das macht ZBZ ueber Oxygen/Alma.

**Vier Seiten:** Korpus-Uebersicht (`index.html`: filter- und sortierbare Doc-Liste mit
Screening-Status), der eigentliche Viewer (`viewer.html`: Faksimile + Layout-Overlay links,
Transkription/TEI rechts), eine Methode-Seite (`methode.html`: CER-Headline + stratifizierte
Werte + Limitations + Literatur-Vergleich, E62, statisch) und eine About-Seite (`about.html`).
Der Viewer kennt drei Modi: *Anzeigen*, *Layout bearbeiten*, *Transkription bearbeiten*.
Persistenz erfolgt ausschliesslich via Datei-Download (kein Server).

**In Umbau (Mai 2026 Edition-Uplift-Welle):** Mode-Buttons werden zu Edit-Toggle pro Panel
(E60), Faksimile-Renderer ist im View-Modus auf OpenSeadragon umgestellt (E58, Pan + Zoom +
Rotate), Layout-Editor wird mit OSD-Koordinaten-Conversion neu verdrahtet. Polygon-Support
bewusst ausgeschlossen (E59) — Hersch-Druck reicht mit Rechtecken. Plan-Dokument:
`C:\Users\Chrisi\.claude\plans\edition-uplift-three-pages.md`.

---

## Architektur

```
docs/
├── index.html                   # Korpus-Uebersicht: filter-/sortierbare Doc-Liste, Screening-Status
├── viewer.html                  # Doc-Detail: Faksimile + Layout-Overlay + OCR/TEI-Panel, 3 Modi
├── methode.html                 # CER-Methodik, Headline, Stratifiziert, Limitations, Literatur (E62, statisch)
├── about.html                   # Projekt-Seite (verweist auf methode.html fuer Qualitaets-Details)
├── css/
│   ├── tokens.css               # Hersch Design Tokens (--h-*)
│   ├── base.css                 # Reset, Typography, Buttons, Badges, Tabs
│   ├── viewer.css               # Viewer-Shell, Faksimile-Overlay, TEI-Render, Editor-UI
│   └── catalog.css              # Korpus-Uebersicht: Status-Leiste, Filter, Doc-Tabelle
├── js/
│   ├── core.js                  # DOM, URL, Fetch, Format, Cache, Toast, EventBus, Markdown-Renderer
│   ├── viewer.js                # Viewer-Orchestrator: Doc-Selektion + Mode-Switching
│   ├── catalog.js               # Korpus-Uebersicht: Laden, Filter, Sortierung, Screening-Legende
│   ├── tei-render.js            # TEI-XML → DOM (mit Entity-Highlighting)
│   ├── layout-editor.js         # BBox Drag/Resize/Add/Delete + Reading-Order
│   ├── transcription-editor.js  # OCR/TEI/XML mit contenteditable
│   └── download.js              # Datei-Download (JSON/MD/XML)
└── data/                        # generiert via scripts/generate_edition_data.py
    ├── catalog.json             # 285 Docs (id, title, author, lang, type, page_count, screening)
    ├── entity_index.json        # 4504 Entities mit GND/Wikidata
    ├── entity_register.json     # Cross-Doc-Aggregation
    ├── search_index.json        # Volltext fuer Doc-Suche
    ├── tei/                     # 285 finale TEIs (*_final.xml + *_review.json)
    ├── pages/                   # alle 285 Docs: Layout-JSONs + Mistral-OCR + per-Seiten-TEI
    └── examples/                # Legacy: 4 DEMO-Docs (Backward-Kompatibilitaet)
```

**Volumen:** 4 HTML (~520 Z.), 4 CSS (~1.420 Z.), 7 JS (1.832 Z.). Die Korpus-Uebersicht
(`index.html` + `catalog.js` + `catalog.css`) und die About-Seite kamen nach der E56-Radikalkur
hinzu (Commit „Korpus-Uebersicht + Top-Nav"); die Methode-Seite folgte 2026-05-26 (E62).

**CDN-Dependencies:**

| Library | Version | CDN | Zweck |
|---|---|---|---|
| OpenSeadragon | 5.0.1 | jsDelivr | Faksimile-Renderer (Pan/Zoom/Rotate) im View-Modus (E58) |
| JSZip | 3.10.1 | cdnjs | ZIP-Bundle fuer Multi-Datei-Export (siehe `Persistenz / Export`) |

Beide Libraries werden zur Laufzeit aus dem CDN nachgeladen. Keine npm/Build-Pipeline.

---

## Drei Modi

| Modus | Editierbar | Zweck | Persistenz |
|---|---|---|---|
| **Anzeigen** | nein | reine Inspektion (read-only) | — |
| **Layout** | Layout-Overlay | Regionen (BBox, Typ, Reihenfolge) korrigieren | Download `{doc}_p{N}_layout_curated.json` |
| **Transkription** | Text-Panel | OCR-Text oder TEI-Text/XML korrigieren | Download `{doc}_p{N}_curated.md` oder `{doc}_curated.xml` |

Edit-Toggle in der Toolbar oben rechts. Im Layout-Modus erscheint eine zweite Toolbar mit
Regions-Tools (`+ Region`, `Loeschen`, Typ-Dropdown).

**In Umbau (E60, Mai 2026):** Globale Mode-Leiste wird abgeloest durch je einen Edit-Toggle
pro Panel — Faksimile-Panel-Toggle aktiviert den Layout-Editor, Text-Panel-Toggle aktiviert
den Transkriptions-Editor fuer die aktive Text-Quelle (OCR/TEI/XML). Begruendung:
Wortdoppelung "Transkription"-Mode mit "OCR"-Source.

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
| **OCR** | Markdown | rohen OCR-Text aus Mistral/DeepSeek/Gemini/Haiku |
| **TEI** | gerendertes TEI | nur Text-Inhalte (keine Struktur — fuer Tags den XML-Modus nutzen) |
| **XML** | TEI-XML mit Syntax-Highlighting | rohes XML inklusive Tags und Attribute |

Aenderungen werden debounced eingesammelt. Speichern ueber den `Text ↓` / `TEI ↓` Button im Header
loest den Download aus.

---

## Persistenz

Kein Server. Alle Aenderungen muessen explizit als Datei heruntergeladen werden.
Der Nutzer legt die Dateien dann manuell im Repo ab — z.B.:

- Layout: `output/layout/{doc}/{doc}_p{N}_layout_curated.json` (manuell anlegen)
- OCR: `output/{source}_curated/{doc}_p{N}.md`
- TEI: `data/tei_curated/{doc}/{doc}_curated.xml`

`data/tei_curated/` bleibt der Gold-Standard-Speicher fuer kuratierte TEIs (git-tracked).
Der frueher vorhandene FastAPI-Curation-Server (`scripts/server/curation_server.py`) wurde mit E57
geloescht, weil das Frontend ihn seit E56 nicht mehr ansteuert.

### Export-Modul (in Umbau, geplant Etappe 2.9 + 1.6)

Der Per-Seite-Einzel-Download (Layout/Text/TEI in der Doc-Subbar) bleibt erhalten.
Zusaetzlich kommt ein Komplett-Export:

| Ort | Funktion | Granularitaet |
|---|---|---|
| Doc-Subbar im Viewer | "Alles ↓" oeffnet Export-Drawer mit Checkboxen pro Datentyp | ein Dokument, alle Seiten, alle Engines |
| Aktionsleiste in `index.html` | Multi-Select-Checkboxen + Sticky-Bar "N ausgewaehlt · Export ▾" | mehrere Dokumente aus aktuellem Filter |

Exportierbare Datentypen pro Dokument:

- Faksimile-PNGs (alle Seiten, `images/{doc}/{doc}_pNNN.png`)
- OCR-Rohtext pro Engine (Mistral / Gemini A / Gemini B / LLM / DeepSeek)
- Layout-JSON (Docling + Gemini-Varianten)
- TEI per-Seite (`*_p001.xml` ... `*_pNNN.xml`)
- TEI final (`*_final.xml`)
- Review-JSON (`*_review.json`, 7-Schichten-Quality-Befund)
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
| Korpus-Liste | `data/catalog.json` | — | `scripts/generate_edition_data.py` |
| Thumbnail | `data/thumbs/{doc}.jpg` | — | `scripts/generate_edition_data.py` (PIL, 140x200, JPEG q=70) |
| Faksimile | `images/{doc}/{doc}_pNNN.png` | — | Pipeline (`scripts/extract_pages.py`) |
| Layout (Gemini) | `data/pages/{doc}/{doc}_pNNN_layout_gemini.json` | `../output/layout/` | `scripts/layout_qa_gemini.py` |
| Layout (Docling) | `data/pages/{doc}/{doc}_pNNN_layout.json` | `../output/layout/` | Pipeline |
| OCR Mistral | `data/pages/{doc}/{doc}_pN.md` | `../output/mistral_results/` | Pipeline |
| OCR (andere) | — | `../output/{source}/...` | nur lokal: Gemini A/B, LLM, DeepSeek |
| TEI pro Seite | `data/pages/{doc}/{doc}_pN.xml` | `../output/tei_unified/` | aus `_final.xml` extrahiert |
| TEI final | `data/tei/{doc}_final.xml` | `pages/`, `../output/tei_final/` | `output/tei_final/` |

Alle 285 Docs haben vollstaendige Per-Seiten-Daten in `docs/data/pages/` (Layout, Mistral-OCR, TEI)
und ein Thumbnail in `docs/data/thumbs/`. Damit funktioniert der Viewer ohne lokalen Server fuer
das gesamte Korpus. Die alternativen OCR-Engines (Gemini A/B, LLM, DeepSeek) bleiben unter
`output/` und sind nur lokal abrufbar.

### Leerseiten (E63)

Vorsatz-, Rueck- und Durchschlagseiten liefern nur Muell-OCR (`.`, `^{}[]`, leeres Tabellengeruest)
und das Gemini-Layout-QA halluziniert dort Phantom-Regionen (Docling sagt korrekt 0). Der Viewer
erkennt solche Seiten **interim heuristisch** (`ZBZ.isBlankPageText` in `core.js`: getrimmter Text
<=5 Zeichen ODER ohne Buchstaben/Ziffern) und zeigt statt Muell den ruhigen Hinweis
"Leerseite — kein Text" (`.empty--blank-page`); die Phantom-Kaesten werden nicht gezeichnet, der
Faksimile-Header zeigt "Leerseite". Korpusweit 79 sichere Leerseiten. **Geplant:** die Erkennung
zieht in ein Pro-Objekt-Manifest (`{doc}_manifest.json`, Single Source of Truth fuer Seiten-Fakten),
der Viewer liest dann den Marker statt die Heuristik, und in der TEI markiert `<pb type="blank"/>`
die Seite. Details: [decisions.md](decisions.md) E63.

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
# oder fuer ../output/ Fallback (Gemini A/B, LLM, DeepSeek):
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

Wenn sich Pipeline-Output oder Screening-Status aendert:

```bash
python -m scripts.generate_edition_data                  # voller Lauf inkl. Per-Seiten-Mirror
python -m scripts.generate_edition_data --mirror-only    # nur pages/ neu aufbauen
python -m scripts.generate_edition_data --no-mirror      # nur Katalog + Indices
```

Der Per-Seiten-Mirror (`docs/data/pages/`) ist ~99 MB, ca. 16.500 Dateien. Bei jeder
Aenderung am `output/tei_final/` sollte er neu erzeugt werden.

---

## Verweise

- [pipeline.md](pipeline.md) — Pipeline-Output, der vom Viewer angezeigt wird
- [entities.md](entities.md) — Entity-Highlighting im TEI-Renderer
- [quality.md](quality.md) — Diagnostik-Daten in `docs/data/` (CER, TEI-Quality)
- [workflow.md](workflow.md) — End-to-End-Datenfluss, Save-Mechanismus, Round-Trip vom Edit zur regenerierten TEI, Provenance-Konzept, geplante `_complete.xml`-Variante
- [decisions.md](decisions.md) — E56 (Frontend-Reduktion auf Viewer-only), E57 (Per-Seiten-Mirror + Pages-Deploy), E58 (OpenSeadragon), E59 (Polygone verworfen), E60 (Mode-Button-Redesign Option C), E61 (Export-Modul JSZip)
- Plan-Dokument: `C:\Users\Chrisi\.claude\plans\edition-uplift-three-pages.md`
