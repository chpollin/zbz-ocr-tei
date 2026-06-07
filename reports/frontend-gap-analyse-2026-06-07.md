# Frontend-Gap-Analyse — DHCraft Editions-Ökosystem

**Erstellt:** 2026-06-07 · **Autor:** Claude Code 3 (CC3) · **Auftrag:** G1.3 — Live-Frontend-Gap-Analyse, Hersch zuerst
**Methode:** Live-Inspektion im Browser (Chrome-Automation, Screenshots + Accessibility-Tree + Konsole) kombiniert mit statischer Quellcode-Analyse (HTML/CSS/JS).

---

## 0. Management-Summary

Untersucht wurden **sechs Frontends** des DHCraft-Editions-Ökosystems. Der Hersch-Viewer (`zbz-ocr-tei`) im Detail, die übrigen fünf in fundierten Schnelldurchläufen.

**Kernbefunde:**

1. **Hersch-Viewer ist handwerklich sehr sauber** (Token-Disziplin nahezu perfekt, durchdachte Leerseiten-/Persistenz-Logik), hat aber **drei höherstufige Risiken**: ein potenzieller **Datenverlust beim TEI-XML-Edit**, ein **„Gespeichert"-Status der bei Download-Fallback lügt**, und **fehlende Tastatur-/Touch-Bedienbarkeit des Layout-Editors**. Für die QA-User-Story fehlt zudem eine **Seiten-Navigation jenseits von Prev/Next** (kein „gehe zu Seite N", keine Status-Übersicht über ~4.100 Seiten).

2. **szd-htr ist die Referenzimplementierung** des Ökosystems (Empty/Error-States, `aria-sort`, URL-State, lokal gevendorte Dependencies, Local/Remote-Capability-Detection). Die anderen Frontends sollten sich daran ausrichten.

3. **Wiederkehrende Ökosystem-Schwäche:** fragile externe/relative `fetch`-Aufrufe **ohne Fehlerbehandlung** (editionCrafter lädt Repo-Markdown, agentic-pipeline lädt TEI außerhalb `docs/`, SZD lädt D3 vom CDN). Auf GitHub Pages führen diese zu stillen 404-Fehlern.

4. **Accessibility interaktiver Visualisierungen** (SVG-Graphen, Faksimile-Overlays, klickbare Tabellenzeilen) ist die größte gemeinsame Lücke.

5. **Visuelle Konsistenz über die Frontends fehlt:** Hersch (warmes Editorial-Design, EB Garamond) und teiCrafter (dunkler Tech-Header, Monospace) wirken wie zwei verschiedene Produkte. Für die ZBZ-Demonstration und das DHCraft-Markenbild relevant.

---

## 1. Reifegrad-Matrix

| Frontend | Zweck | Tech | Reifegrad | Dringlichste Lücke |
|---|---|---|---|---|
| **Hersch** (`zbz-ocr-tei/docs`) | OCR/Layout/TEI-Inspektion + Kuration | Vanilla, CDN (OSD) | **nutzbar → produktionsnah** | TEI-XML-Edit-Datenverlust (verifizieren) |
| **szd-htr** (`szd-htr/docs`) | VLM-Transkriptions-Viewer + Review | Vanilla, lokal vendored | **produktionsnah** | Empty-States Vault/Stats, Deeplink-Navigation |
| **teiCrafter** (`ResearchTools/teiCrafter`) | verlustfreier TEI-Editor | Vanilla ES-Module, CDN (OSD) | **fortgeschrittener Prototyp** | Editor nicht responsive, A11y Tabs/Modal |
| **SZD** (`SZD/docs`) | SZD-Ontologie-Referenz + Graph | HTML/CSS, CDN (D3) | **produktionsnah (Doku-Site)** | D3-CDN ohne Fallback, Graph-A11y |
| **editionCrafter** (`editionCrafter/docs`) | Konzept-Landingpage + Mock | Vanilla, CDN (marked/hljs) | **Prototyp/Showcase** | Live-Markdown-Fetch bricht auf Pages |
| **agentic-edition-pipeline** (`.../docs`) | forkbares Editions-Template | Vanilla, dependency-frei | **nutzbar (Template)** | TEI-Download-Pfad 404 |

---

## 2. Hersch-Viewer (`zbz-ocr-tei`) — Detailanalyse

**Live verifiziert:** Korpus-Übersicht (`index.html`), Viewer Cover + Inhaltsseite (`viewer.html?doc=20`), Layout-Edit-Modus, Konsole (0 Fehler, alle 8 Module geladen), Accessibility-Tree.

### 2.1 Was man sieht (Inventar)

- **Korpus-Übersicht:** filter-/sortierbare Tabelle über 285 Dokumente (Titel/Autor/Datum/Sprache/Typ/Form/Seiten/Workflow), Thumbnail je Zeile, 3-Strom-Ampel (OCR/Layout/TEI-XML), Filter (Suche, Sprache, Typ, Form, Strom×Status), URL-State. Header mit „Experimentell"-Badge, Top-Nav (Korpus/Methode/About/Repo).
- **Viewer:** Zwei-Panel-Layout. Links Faksimile (OpenSeadragon: Pan/Zoom/Rotate) mit Regionen-Zähler, Seitennav, „Layout bearbeiten". Rechts Textpanel mit Quellen-Tabs OCR/TEI/XML und „Text bearbeiten". Doc-Subbar mit Identitäts-Chip, einem „Speichern"-Knopf, „Export ▾". Workflow-Pills (unverifiziert/in Arbeit/verifiziert).
- **Drei Modi** (Anzeigen / Layout bearbeiten / Text bearbeiten) als Edit-Toggles pro Panel.

### 2.2 Was bereits sehr gut gelöst ist

- **Token-Disziplin nahezu perfekt:** `base.css` und `catalog.css` ohne einen einzigen Hex-/rgb-Verstoß; `viewer.css` mit **genau einer** `rgba()`-Ausnahme (Modal-Overlay, `viewer.css:822`). Kein reines Schwarz/Weiß.
- **Leerseiten-Behandlung** konsistent über Faksimile + Text, primär aus `<pb type="blank"/>`, Fallback OCR-Heuristik.
- **Status-Auto-Übergang** `unverifiziert→in_arbeit` erst bei echter Änderung (richtige Semantik).
- **Doppel-Schreiben kanonisch + Mirror** löst das serverlose Reload-Problem; Download-Fallback durchgängig.
- Sauberes semantisches HTML, gute ARIA-Labels an Buttons, `aria-live` am Ergebniszähler, `aria-current` in der Nav.

### 2.3 Befunde (priorisiert)

**Schweregrad HOCH**

| # | Befund | Ort | Fix |
|---|---|---|---|
| H1 | **TEI-XML-Edit kann gesamtes Final überschreiben.** `_currentEditedText` ist per-Seite, der TEI-Write überschreibt aber das komplette `{doc}_final.xml` — Risiko: ein Seiten-XML-Block ersetzt das ganze Dokument. **Muss verifiziert werden.** | `viewer.js:401-409`, `fs-access.js:209` | Per-Seiten-XML vom Final-Write entkoppeln; vor Write Konsistenz prüfen |
| H2 | **„Gespeichert" lügt bei Download-Fallback.** Dirty-Flag wird gecleart, auch wenn der Repo-Write per Exception auf Download umgelenkt wurde. | `viewer.js:396,418,425` | Dirty erst clearen, wenn echter Repo-Write erfolgte (Rückgabewert auswerten) |
| H3 | **Layout-Editor nur mausbedienbar** (nur `mousedown/move/up`), keine Touch-/Pointer-/Tastatur-Bedienung → auf Tablet und ohne Maus unbenutzbar. | `layout-editor.js:181-184` | Pointer Events; Pfeiltasten-Nudge für selektierte Region |
| H4 | **Keine Seiten-QA-Navigation.** Nur Prev/Next über ~4.100 Seiten; kein „gehe zu Seite N", keine Status-/Leerseiten-Übersicht. Trifft die QA-User-Story zentral. | `viewer.html:112-116` | Seiten-Eingabefeld + Seiten-Strip mit Statusmarkern |
| H5 | **Modal ohne Fokus-Trap/ESC/Fokus-Rückgabe** (`#fsa-info` ist `aria-modal`, fängt Fokus aber nicht). | `viewer.js:505-511` | Ersten Button fokussieren, Tab trappen, ESC=schließen, Fokus zurückgeben |

**Schweregrad MITTEL**

| # | Befund | Ort | Fix |
|---|---|---|---|
| M1 | **Katalog-Status aktualisiert nicht nach Speichern** — Korpus liest Status nur aus `catalog.json`, nicht aus dem Manifest-Mirror. | `catalog.js:87,291` vs. `fs-access.js:218` | Manifest-Mirror nachladen oder Verhalten dokumentieren |
| M2 | **Race bei schnellem Seitenwechsel** — kein Abbruch-Token; zuletzt aufgelöste statt zuletzt angeforderte Seite kann gewinnen. | `viewer.js:515-535` | Sequenz-Token nach jedem `await` prüfen |
| M3 | **Lade- vs. Fehlerzustand nicht unterscheidbar** — 404 und Netzwerkfehler liefern beide „Keine OCR-Daten". | `viewer.js:754-767` | Fehlerzustand trennen, Retry-Button |
| M4 | **„Titel"-Spalte sortiert nach ID** (`data-sort="id"`) — irreführend. | `index.html:81` | Header „ID/Titel" beschriften oder `data-sort="title"` |
| M5 | **Fehlende Status-Legende** — Ampelfarben (grau/gelb/grün, rot reserviert) nirgends erklärt außer Tooltips. Relevant für QA + ZBZ-Demo. | Katalog + Viewer | Sichtbare Legende über Tabelle und in Subbar |
| M6 | **`contenteditable`-Editor ohne ARIA** (kein `role`/`aria-label`/`aria-multiline`). | `transcription-editor.js:48` | ARIA ergänzen |
| M7 | **Status-Pills sagen aktuellen Wert nicht an** (statisches `aria-label`). | `viewer.html:66-68` | `aria-label` dynamisch |

**Schweregrad NIEDRIG**

- N1 **Kein Multi-Select-Export/Batch** im Katalog (JSZip laut Doku vorgesehen, nicht eingebunden) — `download.js`.
- N2 **Tastatur-Shortcuts minimal** (nur ←/→). Kein Ctrl+S, Home/End, Toggle-Tasten — `viewer.js:939-943`.
- N3 **OSD lädt unkacheltes Voll-PNG** und re-instanziiert pro Seitenwechsel; kein Tiling/Preload — `viewer.js:602-604`.
- N4 **Faksimile-Fehlerzustand ersetzt OSD-Container ohne `destroyOsd()`** (Leak-Risiko) — `viewer.js:625-629`.
- N5 **Token-Nacharbeit:** `viewer.css:822` `rgba(44,40,37,0.45)` → neuer Token `--h-overlay`.
- N6 **Mobile-Katalog blendet Datum/Sprache/Typ/Form/Seiten alle aus** (<1000px nur Titel/Autor/Workflow) — evtl. zu aggressiv für QA unterwegs — `catalog.css:360-364`.
- N7 **Kontrast `--h-text-muted`** (~3.3:1) unter WCAG AA für Kleintext — nur für Hilfstexte nutzen — `tokens.css:32`.

### 2.4 Top-10 Hersch (wirkungsorientiert)

1. H1 — TEI-XML-Edit-Datenverlust **verifizieren/fixen** (kritisch)
2. H2 — Dirty-Flag bei Download-Fallback
3. H5 — Modal-Fokus-Management
4. H3 — Layout-Editor Touch/Tastatur
5. M1 — Katalog-Status nach Speichern
6. H4 — Seiten-QA-Navigation
7. M2 — Race bei Seitenwechsel
8. M4 — „Titel"-Sortierung
9. M5 — Status-Legende
10. M3 + N2 — Fehlerzustände + Ctrl+S

---

## 3. teiCrafter (`ResearchTools/teiCrafter`)

**Live verifiziert:** Editor-Startzustand (3-Panel-Layout, Empty-States klar).

- **Was es ist:** verlustfreier, deterministischer TEI-Editor (Wort-/Zeilenebene), Vanilla ES-Module, kein Build, OSD via CDN; LLM-On-Ramp für 6 Provider (Keys nur im Modul-Scope). Editierkern ungewöhnlich solide (DOM-frei, durch Round-Trip-Proofs abgesichert), mit echtem Facsimile-Deep-Zoom und standOff-Index.
- **Befunde:**
  - **HOCH — Editor nicht responsive:** `.ed-main` mit fester 3-Spalten-Grid + 320px-Fixspalte, **keine `@media`-Query** in `editor.css`; Toolbar ohne `flex-wrap`. Auf Tablet/Mobil unbrauchbar. (`editor.css:98-101`)
  - **MITTEL — Layout-`calc()`-Magic-Number** bricht bei eingeblendetem Gen-Banner (`editor.css:100`).
  - **MITTEL — A11y:** Tabs ohne `role="tab"`/`aria-selected`; Editier-Spans ohne `tabindex`/`role` (nicht tastaturbedienbar); Modal ohne Focus-Trap. (`editor.html:69-71`, `editor-app.js:286-303,634-649`)
  - **NIEDRIG-MITTEL — Note-Indexing per Regex** über `[^>]*` bricht bei „arbitrary TEI" (Kernversprechen). (`editor-app.js:112-126`)
  - **NIEDRIG — ~2700 Zeilen Legacy-CSS** vom entfernten Generator. (`style.css:330-2283`)
- **Reifegrad:** fortgeschrittener Prototyp. Kern stark, Frontend-Drumherum (Responsiveness, A11y, In-App-Hilfe) unfertig.

---

## 4. szd-htr (`szd-htr/docs`) — Referenzimplementierung

**Hinweis:** Live-Inspektion bewusst nicht durchgeführt (aktive CC2-Domäne, Browser-Konflikt vermieden) — Analyse rein aus dem Quellcode.

- **Was es ist:** vollwertige SPA (Katalog + Faksimile/Transkriptions-Viewer + Research-Vault + Stats-Dashboard + Edit/Review). Vanilla (`app.js` ~3.300 Z.), Hash-Routing, Chart.js lokal vendored. Local/Remote-Capability-Detection (`detectLocal()`) schaltet Edit/Approve/GT-Verify nur lokal frei.
- **Stärken (Vorbild fürs Ökosystem):** Empty/Error-States, `aria-sort`, `aria-live`, skip-link, URL-Filter-State (teilbar), Touch (Pinch/Swipe), Tastatur-Shortcuts, Cross-Model-Diff + Edit-Diff.
- **Top-Befunde:**
  - **MITTEL — Objekt-Navigation bricht bei Deeplink** (`#view/<id>` ohne vorherigen Katalog-Render → `filteredObjects` leer). (`app.js:1480-1484`)
  - **MITTEL — A11y:** klickbare `<tr tabindex="0">` ohne `role`/`aria-label`. (`app.js:1178`)
  - **MITTEL — Performance:** `catalog.json` (2,4 MB) synchron vor erstem Paint; Chart.js (206 KB) immer geladen. (`index.html:545`)
  - **NIEDRIG-MITTEL — Empty-States für Vault/Stats/About fehlen** (stille leere Seite). (`app.js:678-686,2787-2792`)
  - **NIEDRIG — Reviewer-Name hartkodiert** („Christopher Pollin") → Mehr-Personen-Review (CC2 als zweite Hand) nicht abbildbar. (`app.js:2362,2428,2603`)
  - **NIEDRIG — Bild-Fehlerzustand** überschreibt `className` statt `classList`, kein Retry. (`app.js:1545-1554`)
- **Reifegrad:** produktionsnah. Lücken in Randzuständen und Mehrbenutzer-Review, nicht im Kern.

---

## 5. Begleit-Frontends (Kurzfassung)

### 5.1 SZD (`SZD/docs`) — Ontologie-Referenz
Statische bilinguale Doku-Site + interaktiver D3-Kraftgraph. **Befunde:** D3-CDN ohne `<noscript>`/Fallback (`visualize.html:374`); Graph maus-/touch-only ohne Text-Äquivalent (A11y); riesige `ontology/index.html` (2.169 Z.) ohne On-Page-Suche/Sprungnav; `lang="en"` vs. DE-Ökosystem. **Reifegrad:** produktionsnah (Zenodo, v1.2.0).

### 5.2 editionCrafter (`editionCrafter/docs`) — Konzept-Landing + Mock
Markdown-gespeiste Landingpage + interaktive „Werkzeug-Skizze" (Mock-Kaskade). **Befunde:** **HOCH** — lädt Repo-Markdown per Relativpfad (`../README.md`), bricht auf GitHub Pages (nur `docs/` deployed → 404); harte CDN-Abhängigkeit (marked/hljs) ohne Fallback; kein `<noscript>`-Inhalt; DE statt geplantes EN (vom Team dokumentiert). **Reifegrad:** Prototyp/Showcase (bewusst).

### 5.3 agentic-edition-pipeline (`.../docs`) — forkbares Template
Dependency-freies Editions-Grundgerüst (Katalog + Viewer + Indizes). **Befunde:** **HOCH** — TEI-Download zeigt auf `results/tei/{id}.xml` außerhalb `docs/` → 404 stiller Fehlschlag (`js/app.js:180-184`); Suchfilter über `row.textContent` aller Spalten, keine „0 Treffer"-Meldung; kein Bild-Error-State; keine `aria-sort`-Semantik. **Reifegrad:** nutzbar (Template).

---

## 6. Querschnitt — Ökosystem-Empfehlungen

1. **szd-htr als Muster nehmen.** Empty/Error-States, `aria-sort`, URL-State, lokale Dependencies, Capability-Detection — auf Hersch, teiCrafter und agentic-pipeline übertragen.
2. **Externe/relative Fetches härten.** editionCrafter (Markdown), agentic-pipeline (TEI), SZD (D3): jeweils Build-Kopie nach `docs/` oder Fallback + `r.ok`-Check. Stille 404 sind das häufigste Ökosystem-Bug-Muster.
3. **A11y interaktiver Visualisierungen** als gemeinsame Aufgabe: SVG-Graphen (SZD), Faksimile-Overlay/Layout-Editor (Hersch), klickbare Zeilen (szd-htr) — Tastatur + Text-Äquivalent.
4. **Lokale Dependencies statt CDN** (OSD, D3, marked/hljs, Chart.js): szd-htr macht es vor; erhöht Robustheit auf Pages und offline.
5. **Visuelle/sprachliche Konsistenz:** gemeinsame Design-Tokens und Sprachstrategie (DE vs. EN) über die DHCraft-Frontends — besonders für die ZBZ-Demonstration.

---

## 7. Empfohlene Sofort-Maßnahmen (für CC1/CC2-Koordination)

- **CC3/Hersch (sofort):** H1 verifizieren (Datenverlust-Risiko) → H2 → H5 → M5 (Legende, schnell & sichtbar) → H4 (QA-Navigation).
- **CC1/teiCrafter:** Editor-Responsiveness + A11y-Tab-Pattern; Note-Indexing auf DOM-Walker umstellen (trifft das „arbitrary TEI"-Versprechen).
- **CC2/szd-htr:** Deeplink-Navigation, Vault/Stats-Empty-States, Reviewer-Feld (für zweite Hand).
- **Ökosystem:** Fetch-Härtung in editionCrafter + agentic-pipeline (HOCH-Befunde, schnell behebbar).

---

## Anhang — Methodische Notizen

- **Live-Tooling:** Hersch (Korpus + Viewer) und teiCrafter live im Browser bestätigt (Screenshots, Accessibility-Tree, Konsole). Konsole des Hersch-Viewers fehlerfrei, alle Module geladen.
- **Beobachtung Screenshot-Stabilität:** Solange OpenSeadragon im Faksimile-Panel aktiv ist, blockiert der Canvas wiederholt `Page.captureScreenshot` (Renderer-Timeout) nach Klick-Interaktionen. Frische Navigationen liefern stabile Screenshots; Klick-Folgen nicht. Für künftige automatisierte Visual-Tests des Viewers relevant (z.B. OSD vor dem Capture pausieren).
- **Live-Resize unzuverlässig:** Fenster-Resize spiegelte sich nicht im Screenshot-Viewport — Responsive-Verhalten wurde daher aus den CSS-Media-Queries verifiziert (Hersch: Katalog @1000px → Kartenliste, Viewer @900px → gestapelte Panels; vorhanden und korrekt).
- **szd-htr:** rein statische Analyse (Live ausgelassen, da aktive CC2-Domäne).
- **Hinweis zu HOCH-Befund H1:** Aus der Quellcode-Lese-Analyse abgeleitet, **nicht durch einen echten Speichervorgang reproduziert**. Vor einem Fix mit einem kontrollierten Test bestätigen.

*Quell-Frontends und Zeilennummern beziehen sich auf den Stand 2026-06-07 (zbz-ocr-tei @ bb8bf156).*
