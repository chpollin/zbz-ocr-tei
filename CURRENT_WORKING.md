# CURRENT_WORKING.md

Stand: 2026-05-25 (Session 45 + Knowledge-Refactoring-Welle). Destillat der laufenden Edition-Uplift-Welle. Nicht commiten ohne Pruefung.

---

## Status

**Letzter Commit:** `7ae3b1a1` auf `main` "Befund 3: TEI strikt wohlgeformt". Branch `chore/consistency-refactor` per Fast-Forward in `main` gemergt. **origin/main 2 Commits zurueck** (push offen).

**Aktive Welle:** Edition-Uplift fuer alle drei Seiten (index, viewer, about). Plan in
[`C:\Users\Chrisi\.claude\plans\edition-uplift-three-pages.md`](C:\Users\Chrisi\.claude\plans\edition-uplift-three-pages.md).

**Noch nicht committed:**

| Stack-Ebene | Dateien | Status |
|---|---|---|
| Befund-1-Politur (Screening-Zaehler) | `docs/js/catalog.js`, `docs/index.html` | bereit zum Commit |
| Viewer-Visual-Politur | `docs/js/core.js`, `docs/js/viewer.js`, `docs/viewer.html`, `docs/about.html`, `docs/css/viewer.css`, `docs/index.html` | Visual-Test bestanden, bereit zum Commit |
| OSD-Integration (Schritt 1 der Welle) | `docs/viewer.html` (CDN-Script + `?v=3`), `docs/css/viewer.css` (`.panel__body--canvas`, `.facsimile-osd`, OSD-Overlay-Region), `docs/js/viewer.js` (zweigeteilter Renderer + setMode) | **Visual-Test offen** |
| `CURRENT_WORKING.md` (dieses File) | — | untracked |

**Korpus-Status (unveraendert):** 285/285 schema-valide. 242 APPROVED, 43 APPROVED_WITH_NOTES, 0 NEEDS_REVIEW.

**CER (unveraendert):** Mean 4.10 %, Median 1.83 %. BCa-Bootstrap B=10000, seed=42.

---

## Edition-Uplift — Plan im Ueberblick

Vier Etappen (~25 h gesamt). Reihenfolge per User-Entscheidung: erst Viewer-UX (2.1 + 2.8), dann index, dann about, dann Quer-Politur.

### Etappe 1 — index.html (Korpus-Eingangstuer)
1.1 Edition-Hero aus `catalog.edition` · 1.2 Quality-Strip (Schema-Valide / CER / Entitaeten) · 1.3 Smart-Filter mit kreuzkonditionalen Live-Counts + Verdichtung · 1.4 Tabellenzeile: Entity-Count + Screening-Datum · 1.4b Klickbare Spalten-Header zum Sortieren · 1.5 Featured-Sektion · **1.6 Multi-Select + Bulk-Export aus Korpus-Uebersicht** (User-Wunsch 2026-05-25).

### Etappe 2 — viewer.html (Edition-Qualitaet sichtbar)
2.1 Mode-Button-Redesign Option C (Edit-Toggle pro Panel) · 2.2 Quality-Drawer aus `{doc}_review.json` · 2.3 Provenance-Panel aus `<revisionDesc>` · 2.4 Entity-Hover mit Wikidata/GND-Tooltip · 2.5 OCR-Engine-Empfehlung · 2.6 Panel-Hoehen-Asymmetrie · 2.7 Text-Panel-Header entdoppeln · 2.8 Layout-Editor-Reichtum (Region-Liste, Live-Koords, Add-Flow) **+ OSD-Integration** · **2.9 Per-Doc-Export-Drawer** (User-Wunsch 2026-05-25).

### Etappe 3 — about.html (Methodik wissenschaftlich darstellen)
3.1 Edition-Hero · 3.2 Pipeline-SVG-Diagramm · 3.3 CER-Visualisierung aus `cer_statistics.json` · 3.4 Korpus-Komposition (3 Bar-Charts) · 3.5 Screening-Pyramide · 3.6 Featured-Verlinkung.

### Etappe 4 — Quer-Politur
4.1 Token-Disziplin-Audit · 4.2 Print-CSS · 4.3 Site-Header / Subline.

---

## Architektur-Entscheidungen dieser Welle

| # | Entscheidung | Begruendung |
|---|---|---|
| E58 | OpenSeadragon 5.0.1 als Faksimile-Renderer (View-Mode) | Pan + Zoom + Rotate; einfaches Image-Loading ohne Tile-Pipeline; via jsDelivr-CDN |
| E59 | Polygon-Support **nicht** eingefuehrt | Hersch-Faksimiles sind sauber gesetzter Druck, Rechtecke reichen; Annotorious nicht noetig; TEI-Datenmodell bleibt `bbox.x_pct/y_pct/w_pct/h_pct` |
| E60 | Mode-Button-Redesign Option C (Edit-Toggle pro Panel) | Aufloesung der Redundanz "Transkription"-Mode ↔ "OCR"-Source; semantisch klare Trennung von Lesen vs Bearbeiten |
| E61 | Export-Modul mit JSZip 3.10.1 | Per-Doc-Drawer ("Alles ↓") und Multi-Select-Bulk-Export aus index. Eine Datei direkt, mehrere als ZIP mit `{doc_id}/{kategorie}/...` + `manifest.json`. ZIP-Erzeugung im Browser, kein Server |

Details in [knowledge/decisions.md](knowledge/decisions.md).

---

## Status der Code-Aenderungen (Welle)

| Schritt | Status | Code |
|---|---|---|
| OSD im View-Mode | umgesetzt, Visual-Test offen | `viewer.html`, `viewer.css`, `viewer.js` |
| Mode-Button-Redesign Option C | pending | — |
| Layout-Editor an OSD anpassen | pending | — |
| Layout-Editor-Reichtum | pending | — |
| **Per-Doc-Export-Drawer (2.9)** | **pending** | — |
| **Bulk-Export aus index (1.6)** | **pending** | — |
| Etappe 1 (index) ohne 1.6 | pending | — |
| Etappe 3 (about) | pending | — |
| Etappe 4 (Quer-Politur) | pending | — |

---

## OSD-Integration im Detail (Schritt 1)

**Renderer zweigeteilt:**
- `renderFacsimileOsd()` — fuer `state.mode === 'view' | 'text'`. Initialisiert OpenSeadragon-Instanz auf `<div class="facsimile-osd">`. Tile-Source `{ type: 'image', url: PNG }`. Layout-Regionen via `viewer.addOverlay()` nach `'open'`-Event (Koordinaten-Conversion Prozent -> Image-Pixel via `viewport.imageToViewportRectangle()`).
- `renderFacsimileImg()` — fuer `state.mode === 'layout'`. Bisheriges `<img>` + `.facsimile__overlay` + alter Editor.

`setMode()` re-rendert das Faksimile, wenn die Variante wechselt (`prevMode === 'layout' !== mode === 'layout'`).

**Container-Style:** `.panel__body--canvas` (kein Padding, `overflow: hidden`, `min-height: 60vh`) wird dynamisch toggled.

**Bekannte Limitierung:** Layout-Mode laeuft weiterhin auf img+Eigenbau-Editor. Editor in OSD integrieren ist Schritt 3 der Welle (Conversion Drag/Resize via `viewport.viewerElementToImageCoordinates`).

---

## Operative Befehle (unveraendert)

```bash
# Lokaler Server
python -m http.server 8765 -d docs

# Daten-Regenerierung
python -m scripts.generate_edition_data

# Validierung / CER
python -m scripts.tei.tei_validator --all --html-report
python -m scripts.benchmark_cer --all --html
python -m scripts.cer_statistics_full --seed 42 --bootstrap-n 10000
```

---

## Wichtige Datei-Anker

- `docs/viewer.html` — OSD-Script-Tag (CDN), cache-bust `?v=3`
- `docs/js/viewer.js:25-37` — State (jetzt mit `osdViewer`)
- `docs/js/viewer.js:138-249` — Renderer zweigeteilt (`renderFacsimile`, `renderFacsimileOsd`, `addOsdOverlays`, `renderFacsimileImg`)
- `docs/js/viewer.js:330-360` — `setMode()` mit Variant-Re-Render
- `docs/css/viewer.css:285-313` — OSD-Container + OSD-Region-Overlay
- `C:\Users\Chrisi\.claude\plans\edition-uplift-three-pages.md` — vollstaendiger Plan dieser Welle

---

## User-Praeferenzen (aus Memory)

- **Sprache:** neutrales Deutsch, kein technischer Jargon
- **Keine Emojis** (auch keine Unicode-Statussymbole)
- **Kein Dark-Theme** — Hersch-Design bleibt Light-Mode
- **Frontend nur bei expliziter Anfrage** — diese Welle ist explizit gewuenscht
- **User:** Christopher Pollin, DHCraft, Projektleiter
- **ZBZ-Kontakte:** Elias Kreyenbuehl, Anouschka

---

## Naechste Schritte

1. Knowledge-Refactoring-Welle abschliessen (workflow.md neu, pipeline/projekt/index/viewer/decisions + README + alle 4 Sanity-Updates) — **diese Session, fast fertig**
2. Code-Drift fixen: `scripts/generate_edition_data.py:268-271` referenziert geloeschte `dashboard.json` (Catalog-Rebuild vermutlich kaputt)
3. Pipeline-Welle planen: `_complete.xml` mit eingebettetem `<facsimile>` + `<zone>` + `@facs`; `provenance.json`-Generator. Voraussetzung fuer Etappe 2.11 (Provenance-Drawer) und vollwertiges Export-Modul (E61).
4. UI-Welle fortsetzen: Region-Liste als Sub-Spalte (Etappe 2.10-A), UI-Verdichtung (Toolbar-Fusion, Layout-Tools in Panel-Header, Downloads als Dropdown, Hints als Tooltips, Edit-Toggles als Icons), Per-Doc-Export-Drawer (Etappe 2.9)
5. Dann Etappe 1 (index), 3 (about), 4 (Quer-Politur)

---

## Knowledge-Refactoring-Welle (diese Session)

Anlass: viele Knowledge-Dokumente waren seit Session 41 (April) nicht aktualisiert, obwohl Session 42-45 viel passiert ist (Frontend-Reduktion E56, Per-Seiten-Mirror E57, Knowledge-Drift bereinigt Session 44, OSD + Mode-Edit-Toggle + Layout-Reichtum + Export-Konzept E58-E61 Session 45).

Plus zwei konzeptionelle User-Fragen, die in die Doku einflossen:
- Wie funktioniert der Round-Trip Layout → PAGE-XML → TEI?
- Macht ein `_complete.xml` mit eingebetteten Layout-Informationen Sinn?

Umgesetzt:

| Datei | Aenderung |
|---|---|
| `knowledge/workflow.md` | **neu** — End-to-End-Datenfluss, Datenformate pro Stufe, Save-Mechanismus, Round-Trip-Erklaerung, Provenance-Konzept (`{doc}_provenance.json`), `_complete.xml`-Konzept (TEI mit eingebettetem `<facsimile>` + `<zone>` + `@facs`), Roadmap, Drift-Befunde |
| `knowledge/pipeline.md` | Datenfluss-Diagramm korrigiert (PAGE-XML parallel, nicht in TEI-Kette), neue Sektion "Manuelle Edits zurueck in die Pipeline (Round-Trip)", Verweis auf workflow.md, E22-Wichtigpunkt klarer formuliert |
| `knowledge/projekt.md` | `scripts/postprocess/` Verweis entfernt (Orphan), Edition-Uplift-Welle + Workflow-Doku als Status-Eintrage |
| `knowledge/index.md` | workflow.md als drittes Top-Dokument eingefuegt, Abhaengigkeits-Diagramm erweitert, neue Schluesselkonzepte (End-to-End-Workflow, Manueller Round-Trip, Provenance, `_complete.xml`) |
| `knowledge/viewer.md` | workflow-Verweis im Verweise-Block |
| `knowledge/decisions.md` | workflow-Verweis im Verweise-Block |
| `knowledge/quality/entities/infrastruktur/methodik.md` | nur Datum-Updates auf 2026-05-25 (keine Drift in den Inhalten gefunden) |
| `README.md` | Pipeline-Diagramm korrigiert (PAGE-XML parallel, nicht in der TEI-Kette), `scripts/postprocess/` aus Struktur-Listing entfernt, DEMO-Docs als konkrete Liste, `tei_curated/` ehrlich kommentiert (nur `.gitkeep`), CDN-Dependencies-Tabelle, workflow.md im Doku-Block prominent verlinkt |
| `CURRENT_WORKING.md` | dieses File, Knowledge-Welle dokumentiert |

## Code-Drift-Befund (offen, nicht in dieser Session gefixt)

`scripts/generate_edition_data.py:268-271`:
```python
def build_catalog():
    """Baut catalog.json aus dashboard.json + doc_metadata.json."""
    dashboard = load_json(DOCS_DIR / "data" / "dashboard.json")
    if dashboard is None:
        print("FEHLER: dashboard.json nicht gefunden!")
```

`docs/data/dashboard.json` wurde in Session 44 als Orphan geloescht (kein
Konsument). `build_catalog()` ist seitdem vermutlich kaputt — ein Re-Run von
`python -m scripts.generate_edition_data` ohne `--mirror-only` koennte den
Catalog nicht mehr aufbauen.

Fix-Optionen:
- `build_catalog()` umstellen auf direkte Quellen (`output/tei_final/*_review.json` + `data/doc_metadata.json`)
- ODER `dashboard.json`-Generator neu aufbauen (vorher: `scripts/generate_dashboard_data.py` — ebenfalls in Session 44 geloescht)
- ODER `build_catalog()` als deprecated markieren und stattdessen eine neue Funktion `build_catalog_from_sources()` anlegen

**Action-Item:** in der naechsten Session vor weiteren Daten-Regenerierungen pruefen.
