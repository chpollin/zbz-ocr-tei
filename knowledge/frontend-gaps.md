---
type: knowledge
created: 2026-06-07
updated: 2026-06-10
tags: [zbz-ocr-tei, frontend, viewer, gap-analyse, qa, accessibility, ux]
status: active
---

# Frontend-Gaps & Qualitaet

Wo stehen die Frontends gemessen an ihren Aufgaben, und was muss verbessert werden?
Dieses Dokument ist die **Single Source of Truth fuer Frontend-Befunde** (Bugs, UX-,
A11y-, Performance-Luecken). Es ergaenzt [viewer.md](viewer.md) (das beschreibt, *wie* der
Viewer funktioniert) um die Dimension *wie gut* er seine User-Stories erfuellt.

> **Abgrenzung:** Funktionsweise, Architektur, Design-System → [viewer.md](viewer.md).
> Qualitaet der *Pipeline-Daten* (CER, TEI-Validierung) → [quality.md](quality.md).
> Hier ausschliesslich: Qualitaet der *Benutzeroberflaeche*.

Erhebung: 2026-06-07, Live-Inspektion im Browser + statische Quellcode-Analyse.
Vollstaendiger zeitpunktbezogener Befundbericht inkl. Oekosystem-Detail:
[../reports/frontend-gap-analyse-2026-06-07.md](../reports/frontend-gap-analyse-2026-06-07.md).

---

## User-Stories als Messlatte

Der Hersch-Viewer dient drei konkreten Zwecken (aus [viewer.md](viewer.md)). Jeder Befund
unten wird gegen sie gewichtet:

| # | User-Story | Persona | Was sie braucht |
|---|---|---|---|
| US1 | **QA** der OCR-/Layout-/TEI-Ergebnisse | Projektteam | schnelles Sichten vieler Seiten, Problemstellen finden |
| US2 | **Human-in-the-Loop-Korrektur** | ZBZ-Kuratoren | Layout/Text/TEI editieren + verlaesslich speichern |
| US3 | **Demonstration** gegenueber ZBZ | Projektleitung | verstaendliche, vertrauenswuerdige Praesentation |

---

## Hersch-Viewer (`docs/`) — Befunde

**Live verifiziert:** Korpus-Uebersicht, Viewer (Cover + Inhaltsseite), Layout-Edit-Modus,
Konsole (0 Fehler, alle 8 Module geladen), Accessibility-Tree.

### Staerken (Bestand sichern, nicht anfassen)

- **Token-Disziplin vollstaendig** — `base.css`/`catalog.css`/`viewer.css` ohne Hex-/rgb-Verstoss
  (letzte `rgba()`-Ausnahme seit 2026-06-10 als Token `--h-overlay`). Kein reines Schwarz/Weiss.
- **Leerseiten-Behandlung** konsistent ueber Faksimile + Text, primaer aus `<pb type="blank"/>`.
- **Status-Auto-Uebergang** `unverifiziert→in_arbeit` erst bei echter Aenderung (richtige Semantik).
- **Doppel-Schreiben kanonisch + Mirror** mit Download-Fallback (siehe [viewer.md §Persistenz](viewer.md)).
- Semantisches HTML, gute Button-ARIA, `aria-live` am Zaehler, `aria-current` in der Nav.

### Behoben (2026-06-10, Sitzung Repo-Audit)

| ID | Befund (Kurzform) | Fix |
|---|---|---|
| **H1** | TEI-XML-Edit ueberschrieb gesamtes `{doc}_final.xml` mit per-Seiten-Inhalt (im Code verifiziert: `loadTeiPage` → `writeTei`) | XML-Modus laedt jetzt das Gesamtdokument (`loadTeiFinal`); Save-Guard verweigert unvollstaendige TEI (`viewer.js`) |
| **H2** | „Gespeichert"-Meldung verschwieg Download-Fallback | `persistSilent`-Rueckgabe ausgewertet; Download-Fall meldet explizit „Dateien manuell ins Repo legen" |
| **H3** | Layout-Editor nur mausbedienbar | Pointer Events (Maus+Touch+Stift), `touch-action:none`, Pfeiltasten-Nudge (1%, Shift=5%) |
| **H5** | Modal ohne Fokus-Trap/ESC/Fokus-Rueckgabe | Initial-Fokus, Tab-Trap, ESC=Abbrechen, Fokus-Rueckgabe (`showFsaInfo`/`hideFsaInfo`) |
| **M2** | Race bei schnellem Seitenwechsel | `pageLoadSeq`-Token + stale-Guards nach jedem `await`; OSD-Handler instanz-gebunden |
| **M4** | „Titel"-Spalte sortierte nach ID | `data-sort="title"` (`index.html`) |
| **M6** | `contenteditable` ohne ARIA | `role="textbox"`, `aria-multiline`, `aria-label` in `transcription-editor.js` |
| **M7** | Status-Pills ohne aktuellen Wert im `aria-label` | dynamisches `aria-label` in `renderStatusPills` |
| **N4** | OSD-Fehlerzustand ohne `destroyOsd()` (Leak) | `destroyOsd()` vor `innerHTML`-Ersatz in `open-failed` |
| **N5** | `rgba(44,40,37,0.45)` statt Token | Token `--h-overlay` in `tokens.css`, genutzt in `viewer.css` |

### Befunde — Schweregrad HOCH

| ID | Befund | Ort | US | Fix |
|---|---|---|---|---|
| **H4** | **Keine Seiten-QA-Navigation.** Nur Prev/Next ueber ~4.100 Seiten; kein „gehe zu Seite N", keine Status-/Leerseiten-Uebersicht. | `viewer.html:112-116` | US1 | Seiten-Eingabefeld + Seiten-Strip mit Statusmarkern |

### Befunde — Schweregrad MITTEL

| ID | Befund | Ort | US | Fix |
|---|---|---|---|---|
| **M1** | **Katalog-Status aktualisiert nicht nach Speichern** — Korpus liest Status nur aus `catalog.json`, nicht aus dem Manifest-Mirror. | `catalog.js:87,291` vs. `fs-access.js:218` | US1 | Manifest-Mirror nachladen oder Verhalten dokumentieren |
| **M3** | **Lade- vs. Fehlerzustand nicht unterscheidbar** — 404 und Netzwerkfehler liefern beide „Keine OCR-Daten". | `viewer.js:754-767` | US1 | Fehlerzustand trennen, Retry-Button |
| **M5** | **Fehlende Status-Legende** — Ampelfarben (grau/gelb/gruen, rot reserviert) nur in Tooltips erklaert. | Katalog + Viewer | US1/US3 | Sichtbare Legende ueber Tabelle und in Subbar |

### Befunde — Schweregrad NIEDRIG

| ID | Befund | Ort | Fix |
|---|---|---|---|
| **N1** | Kein Multi-Select-Export/Batch im Katalog (JSZip vorgesehen, nicht eingebunden) | `download.js` | Sammel-Export, siehe Roadmap E61 in [viewer.md](viewer.md) |
| **N2** | Tastatur-Shortcuts minimal (nur ←/→) | `viewer.js:939-943` | Ctrl+S, Home/End, Toggle-Tasten |
| **N3** | OSD laedt unkacheltes Voll-PNG, re-instanziiert pro Seitenwechsel | `viewer.js:602-604` | Tiling/DZI oder Nachbar-Preload |
| **N6** | Mobile-Katalog blendet Datum/Sprache/Typ/Form/Seiten alle aus (<1000px) | `catalog.css:360-364` | mind. Datum/Typ behalten |
| **N7** | Kontrast `--h-text-muted` (~3.3:1) unter WCAG AA fuer Kleintext | `tokens.css:32` | nur fuer Hilfstexte nutzen |

### Umsetzungsreihenfolge (offen)

1. **M1** Katalog-Status nach Speichern (US1)
2. **H4** Seiten-QA-Navigation (US1)
3. **M5** Status-Legende (US1/US3 — schnell & sichtbar)
4. **M3 + N2** Fehlerzustaende + Ctrl+S (US1/US2)
5. **N3/N6/N7** Performance + Mobile + Kontrast

---

## Oekosystem-Vergleich

Sechs Frontends im DHCraft-Editions-Oekosystem, gemessen am gleichen Raster. Detail je
Frontend im [Befundbericht](../reports/frontend-gap-analyse-2026-06-07.md).

| Frontend | Zweck | Reifegrad | Dringlichste Luecke |
|---|---|---|---|
| **Hersch** (`zbz-ocr-tei/docs`) | OCR/Layout/TEI-Inspektion + Kuration | nutzbar → produktionsnah | H4 Seiten-QA-Navigation, M1 Katalog-Status-Lag |
| **szd-htr** (`szd-htr/docs`) | VLM-Transkriptions-Viewer + Review | **produktionsnah (Referenz)** | Empty-States Vault/Stats, Deeplink-Nav |
| **teiCrafter** (`ResearchTools/teiCrafter`) | verlustfreier TEI-Editor | fortgeschr. Prototyp | Editor nicht responsive, A11y Tabs/Modal |
| **SZD** (`SZD/docs`) | Ontologie-Referenz + Graph | produktionsnah (Doku) | D3-CDN ohne Fallback, Graph-A11y |
| **editionCrafter** (`editionCrafter/docs`) | Konzept-Landing + Mock | Prototyp/Showcase | Live-Markdown-Fetch bricht auf Pages |
| **agentic-edition-pipeline** (`.../docs`) | forkbares Editions-Template | nutzbar (Template) | TEI-Download-Pfad 404 |

**szd-htr ist die Referenzimplementierung** des Oekosystems (Empty/Error-States, `aria-sort`,
`aria-live`, URL-State, lokal gevendorte Dependencies, Local/Remote-Capability-Detection).
Die uebrigen Frontends sollten sich daran ausrichten.

---

## Querschnitts-Muster (oekosystemweit)

1. **Fragile externe/relative `fetch` ohne Fehlerbehandlung** ist das haeufigste Bug-Muster:
   editionCrafter (Repo-Markdown), agentic-pipeline (TEI ausserhalb `docs/`), SZD (D3-CDN).
   Auf GitHub Pages → stille 404. → Build-Kopie nach `docs/` oder Fallback + `r.ok`-Check.
2. **A11y interaktiver Visualisierungen** (SVG-Graphen, Faksimile-Overlays, klickbare
   Tabellenzeilen) ist die groesste gemeinsame Luecke: Tastatur + Text-Aequivalent fehlen.
3. **CDN- statt lokale Dependencies** (OSD, D3, marked/hljs, Chart.js) — szd-htr vendored
   lokal; erhoeht Robustheit auf Pages und offline.
4. **Visuelle/sprachliche Inkonsistenz** zwischen den Frontends (Hersch warmes Editorial vs.
   teiCrafter dunkler Tech-Header; DE vs. EN) — relevant fuer die ZBZ-Demonstration (US3) und
   das DHCraft-Markenbild. Kandidat fuer gemeinsame Design-Tokens.

---

## Methodische Notizen (fuer kuenftige Frontend-Tests)

- **OpenSeadragon blockiert `Page.captureScreenshot`**: solange OSD im Faksimile-Panel aktiv
  ist, friert der Renderer fuer Screenshots nach Klick-Interaktionen ein (CDP-Timeout). Frische
  Navigationen liefern stabile Screenshots, Klick-Folgen nicht. → Fuer automatisierte Visual-
  Tests OSD vor dem Capture pausieren/zerstoeren.
- **Live-Resize unzuverlaessig** im Automations-Tooling (Viewport spiegelt die Fenstergroesse
  nicht). Responsive-Verhalten daher aus den CSS-Media-Queries verifizieren — Hersch: Katalog
  `@1000px` → Kartenliste, Viewer `@900px` → gestapelte Panels (vorhanden und korrekt).
- **szd-htr** wurde rein statisch analysiert (Live ausgelassen, Browser-Konflikt vermieden).

---

## Verweise

- [viewer.md](viewer.md) — Funktionsweise, Architektur, Hersch Design-System, Persistenz
- [quality.md](quality.md) — Qualitaet der Pipeline-*Daten* (CER, TEI-Validierung)
- [workflow.md](workflow.md) — Save-Mechanismus + Round-Trip (Kontext fuer H1/H2)
- [decisions.md](decisions.md) — E58 (OSD), E60 (Mode-Toggle), E61 (Export/JSZip), E78/E79 (Persistenz)
- [../reports/frontend-gap-analyse-2026-06-07.md](../reports/frontend-gap-analyse-2026-06-07.md) — vollstaendiger zeitpunktbezogener Befundbericht (alle 6 Frontends, datei:zeile-genau)

## Wartung

- **Befund behoben?** Zeile hier streichen oder als erledigt markieren (mit Commit-Verweis).
- **Neuer Befund?** in die passende Schweregrad-Tabelle, mit Ort (`datei:zeile`) und betroffener User-Story.
- **Periodische Re-Erhebung** als datierten Bericht in `reports/` ablegen, Synthese hierher.
