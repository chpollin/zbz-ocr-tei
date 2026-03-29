---
type: knowledge
created: 2026-03-09
updated: 2026-03-15
tags: [zbz-ocr-tei, edition, frontend, digital-edition]
status: active
---

# Digitale Edition

Oeffentliche digitale Edition der Jeanne-Hersch-Korrespondenz fuer Forschende und Oeffentlichkeit. Statisch auf GitHub Pages, mit optionalem Kurations-Modus wenn der Server laeuft.

**Dependencies:** [PIPELINE](PIPELINE.md) (TEI-XML als Input), [CURATION](CURATION.md) (Edit-Modus), [DESIGN](DESIGN.md) (Design-System)

---

## Zwei Modi — ein System

| Modus | Zugang | Funktion |
|-------|--------|----------|
| **Lesen** | `docs/` auf GitHub Pages | Katalog, Register, Reader (Faksimile + TEI), Entities, XML-Ansicht, Volltext-Suche |
| **Kuratieren** | `localhost:8000` (FastAPI Server) | Alles wie Lesen + Text-Korrektur, Struktur-Editing, Entity-Kuration, Review-Workflow |

Der Edit-Button erscheint automatisch wenn der Curation Server laeuft (Health-Check, nur auf localhost). Details zum Kurations-Workflow: [CURATION.md](CURATION.md).

---

## Architektur

**Directory:** Edition: `docs/` | Infrastruktur: `docs/infrastruktur/`

| Datei | Zweck |
|-------|-------|
| `docs/index.html` | Discovery Hub: Suchleiste, Korpus-Chips, Screening-Fortschritt, Projekt-Teaser |
| `docs/catalog.html` | Katalog: Tabellen-/Karten-/Galerie-Ansicht, Volltext-Suche, Screening-Filter, URL-Deep-Linking |
| `docs/register.html` | Entity-Register: Typ-Tabs (4504 Entitaeten), Kontext-Preview, Doc-Titel-Links |
| `docs/reader.html` | Reader: Faksimile-Viewer (Pan/Zoom/Rotate) + TEI-Text, Text/XML-Toggle, Metadaten-Header |
| `docs/about.html` | Projektinformation, Pipeline-Visualisierung, Divider-Seuils |

### JavaScript-Module (ES6+, IIFE, `ZBZ.*` Namespaces)

| Modul | Zweck |
|-------|-------|
| `edition-shared.js` | Kern: Nav, Daten-Loader, TEI-Fetch (Volldokument-Cache), Volltext-Suche, Badge-Konstanten |
| `edition-landing.js` | Discovery Hub: Hero-Suche, Screening-Chips, Kategorie-Chips |
| `edition-catalog.js` | Katalog: MiniSearch + Volltext, Filter, 3 Views (Tabelle/Karten/Galerie), URL-State-Sync |
| `edition-register.js` | Register: Typ-Tabs, Suche, Resolution-Filter, Detail-Expansion mit Doc-Titeln |
| `edition-reader.js` | Reader: Integrierter Viewer (Pan/Zoom/Rotate/Fit), Text/XML-Toggle, Edit-Modus |
| `edition-tei.js` | TEI Renderer: rekursives Node-Rendering, Entity-Extraktion, XML-Ansicht |
| `edition-editor.js` | Curation Orchestrator (laedt 6 Sub-Module aus `js/editor/`) |
| `editor/editor-api.js` | Server-Erkennung, API-Helpers, Editor-State |
| `editor/editor-save.js` | Save, Dirty State, Toast Notifications |
| `editor/editor-serialize.js` | DOM-zu-XML Serialisierung |
| `editor/editor-block-toolbar.js` | Block-Editing: Typ-Wechsel, Split, Merge, Delete, B/I/U |
| `editor/editor-entity.js` | Entity-Tagging, Popover, Autocomplete |
| `editor/editor-render.js` | TEI-XML zu editierbarem DOM Rendering |
| `entity-utils.js` | Entity-Resolution: ZBZ-ID/Wikidata/GND Lookup, Entity-Spans, Extraktion |

### Daten (generiert via `scripts/generate_edition_data.py`)

| Datei | Inhalt |
|-------|--------|
| `docs/data/catalog.json` | 285 Docs mit Screening- + Curation-Status, Corpus-Statistiken |
| `docs/data/search_index.json` | Volltext-Index: 285 Docs (Body-Text + Entity-Namen) |
| `docs/data/entity_index.json` | 4504 Entitaeten (schneller Lookup) |
| `docs/data/entity_register.json` | Cross-Doc-Register mit Varianten, Doc-IDs, Kontexten |
| `docs/data/tei/*.xml` | 285 finale TEI-Dokumente (fuer GitHub Pages) |
| `docs/data/tei/*.json` | 285 Review-JSONs (Screening-Befunde) |
| `docs/data/examples/` | 4 Demo-Docs mit Seiten-Bildern |

---

## Zwei-Stufen-Qualitaetsworkflow

Screening (LLM) und Curation (Editor) sind getrennte Status:

| Schicht | Akteur | Status-Werte | Badge-Farben |
|---------|--------|-------------|--------------|
| **Screening** | Agent (quality-pass-auto, agent-screening-v2) | APPROVED, APPROVED_WITH_NOTES, NEEDS_REVIEW | gruen, gelb, rot |
| **Curation** | Mensch (Editor) | uncurated, draft, in_progress, in_review, editor_approved | grau, amber, blau, blau, dunkelgruen |

Beide Status werden in `catalog.json` pro Dokument gefuehrt. Fortschrittsbalken auf der Startseite zeigen beide Schichten getrennt.

Badge-Konstanten zentral in `edition-shared.js`: `SCREENING_LABELS`, `SCREENING_CLASSES`, `CURATION_LABELS`, `CURATION_CLASSES`, `screeningBadgeHtml()`, `curationBadgeHtml()`.

---

## Design System

Siehe [DESIGN](DESIGN.md) fuer das vollstaendige Hersch Design System:
EB Garamond (Brotschrift), Jost (Ueberschriften), Ziegelrot-Akzent,
zweistufige Token-Architektur (`--h-*` Hersch-Tokens / `--ed-*` Edition-Aliases).

Implementierung: `docs/css/shared.css` (970 Zeilen, vollstaendiges Token-System).

---

## TEI-Lade-Strategie

`fetchFullTei(docId)` laedt das Volldokument und cached es. Seiten werden per `extractPageFromFull(xml, page)` via `<pb>`-Regex extrahiert mit automatischem Tag-Balancing.

Pfad-Prioritaet:
1. `data/tei/{id}_final.xml` (alle 285 Docs, GitHub Pages)
2. `data/examples/{id}/{id}_final.xml` (Demo-Docs, Fallback)
3. `../output/tei_final/{id}_final.xml` (Lokal-Fallback)

---

## Design-Entscheidungen

| Entscheidung | Begruendung |
|-------------|-------------|
| Edition in `docs/`, Dashboard in `docs/infrastruktur/` | Dashboard = internes QA-Tool; Edition = oeffentlich |
| ES6+/IIFE, `ZBZ.Edition` Namespace | Konsistent mit Dashboard-Konvention, kein Build-Tool |
| Nav/Footer JS Slot Pattern (`#ed-nav-slot`) | DRY: einmal in JS definiert, HTML hat leere Slots |
| Badge-Konstanten zentral in `edition-shared.js` | Single Source of Truth, verhindert Label-Inkonsistenz |
| Health-Check nur auf localhost | Vermeidet 404-Fehler in Konsole auf GitHub Pages |
| MiniSearch via CDN (~22KB) | Client-seitige Volltext- + Metadatensuche, kein Server noetig |
| Volldokument-Cache + pb-Extraktion | Vermeidet Re-Fetch bei Seitennavigation, 285 Docs je 50-200 KB |
| Screening + Curation getrennt | LLM-Ergebnis unveraenderlich, Editor-Workflow unabhaengig |
| 285 TEIs in `docs/data/tei/` (18 MB) | Alle Docs auf GitHub Pages lesbar, nicht nur 4 Demos |

---

## Daten-Generierung

```bash
python -m scripts.generate_edition_data
```

Erzeugt: `catalog.json` (285 Docs, Screening + Curation), `search_index.json` (285 Docs Volltext), `entity_index.json`, `entity_register.json`. Kopiert Demo-TEIs nach `docs/data/examples/`.

---

## Navigation

| Label | Ziel | Kontext |
|-------|------|---------|
| Start | `index.html` | Discovery Hub |
| Katalog | `catalog.html` | Dokument-Suche + Filter |
| Register | `register.html` | Entity-Index |
| Projekt | `about.html` | Projektinformation |
| Promptotyping-Artefakte | `infrastruktur/index.html` | Pipeline-QA-Tools |

---

## Referenzen

- [CURATION](CURATION.md) — Kurations-Workflow (Server, API, Editor-Operationen)
- [PIPELINE](PIPELINE.md) — TEI-XML Pipeline (Input fuer die Edition)
- [GND-STRATEGIE](GND-STRATEGIE.md) — Entity Linking (Wikidata/GND in Sidebar)

---

*Created: 2026-03-09 | Updated: 2026-03-26*
