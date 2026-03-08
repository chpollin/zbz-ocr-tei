---
type: knowledge
created: 2026-03-09
updated: 2026-03-09
tags: [zbz-ocr-tei, edition, frontend, digital-edition]
status: active
---

# Digitale Edition

Oeffentliche digitale Edition der Jeanne-Hersch-Korrespondenz fuer Forschende und Oeffentlichkeit. Statisch auf GitHub Pages, mit optionalem Kurations-Modus wenn der Server laeuft.

**Dependencies:** [PIPELINE](PIPELINE.md) (TEI-XML als Input), [CURATION](CURATION.md) (Edit-Modus)

---

## Zwei Modi — ein System

| Modus | Zugang | Funktion |
|-------|--------|----------|
| **Lesen** | `docs/edition/` auf GitHub Pages | Katalog, Reader (Faksimile + TEI), Entities, XML-Ansicht |
| **Kuratieren** | `localhost:8000` (FastAPI Server) | Alles wie Lesen + Text-Korrektur, Struktur-Editing, Entity-Kuration, Review-Workflow |

Der Edit-Button erscheint automatisch wenn der Server laeuft (Health-Check). Details zum Kurations-Workflow: [CURATION.md](CURATION.md).

---

## Architektur

**Directory:** `docs/edition/`

| Datei | Zweck | Zeilen |
|-------|-------|--------|
| `index.html` | Landing: Hero, Featured Docs, Corpus Stats | ~102 |
| `catalog.html` | Katalog: facettierte Filter, Tabellen-/Kartenansicht, MiniSearch | ~82 |
| `reader.html` | Reader: Faksimile + TEI nebeneinander, Entities, XML-Ansicht | ~67 |
| `about.html` | About: Hersch-Biographie, Projekt, Pipeline, Technologie | ~138 |
| `css/edition.css` | Design System: `--ed-*` CSS Vars, Dark Mode, 3 Breakpoints | ~1300 |
| `js/edition-shared.js` | Shared: Nav/Footer Slots, Dark Mode, Katalog-Loader, Card Builder | ~283 |
| `js/edition-landing.js` | Landing: Metriken-Animation, Featured Docs, Corpus Stats | ~140 |
| `js/edition-catalog.js` | Katalog: MiniSearch (CDN), Filter, Sort, Rendering | ~354 |
| `js/edition-reader.js` | Reader: Seitennavigation, Zoom, Font-Toggle, Divider, Entity Sidebar | ~305 |
| `js/edition-tei.js` | TEI Renderer: rekursives Node-Rendering, Entity-Extraktion, XML-Ansicht | ~302 |
| `js/edition-editor.js` | Curation: WYSIWYG, DOM-zu-XML Serializer, Save (nur mit Server) | ~370 |
| `data/catalog.json` | Generierter Katalog (via `scripts/generate_edition_data.py`) | -- |

---

## Design System

- **Farben:** Parchment `#faf8f5` (Hintergrund), Scholarly Navy `#1e3a5f` (Primaer), Warm Gold `#b8860b` (Akzent)
- **Dark Mode:** `.dark` auf `<body>`, alle `--ed-*` Variablen ueberschrieben
- **Typographie:** Inter (UI), Source Serif 4 (Lesen), JetBrains Mono (Code/XML)
- **Responsive:** 1200px (voll), 768px (kompakt), 480px (mobil)
- **Namespace:** `ZBZ.Edition` (ES5/IIFE, kein Build-Tool)

---

## Design-Entscheidungen

| Entscheidung | Begruendung |
|-------------|-------------|
| Getrennt vom Dashboard (`docs/edition/`) | Dashboard = internes QA-Tool; Edition = oeffentlich |
| ES5/IIFE, `ZBZ.Edition` Namespace | Konsistent mit Dashboard-Konvention, kein Build-Tool |
| Nav/Footer JS Slot Pattern (`#ed-nav-slot`) | DRY: einmal in JS definiert, HTML hat leere Slots |
| `buildCardHtml()` Shared Helper | DRY: Card-Rendering in Landing + Katalog |
| `sanitizeDocId()` fuer URL-Params | Sicherheit: nur Ziffern erlaubt, verhindert Path Traversal |
| MiniSearch via CDN (~22KB) | Client-seitige Volltextsuche, kein Server noetig |
| TEI Renderer kopiert von `tei-viewer.js` | Lese-optimierte Version, keine Regression im Dashboard |
| CSS-Klassen fuer TEI `<hi>` Renditions | Ersetzt Inline-Styles, wartbar via CSS |
| 4 Demo-Docs (2310, 1000, 1330, 1540) | Gleich wie Dashboard-Demo, erweiterbar auf ganzes Korpus |

---

## Daten-Generierung

```bash
python -m scripts.generate_edition_data   # catalog.json + TEI XMLs kopieren
```

Liest `docs/data/dashboard.json` + `data/doc_metadata.json`. Erzeugt `docs/edition/data/catalog.json` (286 Docs, Corpus Stats, Featured-Liste). Kopiert TEI-XMLs der Demo-Docs nach `docs/data/examples/`.

---

## Referenzen

- [CURATION](CURATION.md) — Kurations-Workflow (Server, API, Editor-Operationen)
- [PIPELINE](PIPELINE.md) — TEI-XML Pipeline (Input fuer die Edition)
- [GND-STRATEGIE](GND-STRATEGIE.md) — Entity Linking (Wikidata/GND in Sidebar)

---

*Created: 2026-03-09 | Updated: 2026-03-09*
