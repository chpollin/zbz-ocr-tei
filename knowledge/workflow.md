---
type: knowledge
created: 2026-05-25
updated: 2026-05-25
tags: [zbz-ocr-tei, workflow, datafluss, persistenz, provenance, complete-tei, round-trip]
status: active
---

# Workflow + Datenfluss

End-to-End: vom PDF zum kuratierten TEI. Erklaert was real funktioniert, was
manuell ist, was noch fehlt, und welche Erweiterungen geplant sind. Quer-Doku
zu [pipeline.md](pipeline.md) (Stufen), [viewer.md](viewer.md) (Frontend),
[decisions.md](decisions.md) (Architektur-Entscheidungen).

---

## 1. Datenfluss-Diagramm

```
PDF
 │
 ▼
Bilder (PNG 300 dpi)
 │
 ├──────────────────────────────────────────┐
 ▼                                          ▼
OCR (Mistral / Gemini-korrigiert)          Layout (Docling + Gemini-QA)
 │                                          │
 │   ┌──────────────────────────────────────┤
 │   │                                      │
 │   ▼                                      ▼
 │   PAGE-XML (rule-based)                  │
 │   = paralleler Export                    │
 │   fuer coOCR-Kompatibilitaet             │
 │   NICHT TEI-Input                        │
 │                                          │
 │                                          ▼
 └────────► TEI-XML (Unified: Scaffold + Gemini-Refinement + Assembly)
            │
            ▼
            output/tei_final/{doc}_final.xml + {doc}_manifest.json
            (Workflow-Status pro Strom, E66/E67 — ersetzt das fruehere Agent-Screening)
            │
            ▼
            docs/data/pages/{doc}/ (generierter Mirror, inkl. {doc}_final.xml)
            │
            ▼
            Viewer (Inspektion + Korrektur)
            │
            ▼
            "Speichern" -> output/ (kanonisch, Pipeline) + docs/data/ (Mirror, Reload), E78/E79
            │
            ▼
            (Pipeline-Re-Run --reassemble faltet die Kuration ins finale TEI)
```

**Schluesselpunkt (E22, oft missverstanden):** PAGE-XML ist KEIN Zwischenschritt
fuer TEI. TEI wird DIREKT aus Layout-JSON + OCR-Markdown via
`scripts/tei/tei_unified.py` generiert. PAGE-XML wird PARALLEL als Export fuer
coOCR / Transkribus erzeugt (`scripts/layout/page_xml_generator.py`).

---

## 2. Datenformate pro Stufe

| Stufe | Format | Hauptpfad | Quelle |
|---|---|---|---|
| Quell-PDF | PDF | `data/source/pdf/{doc}.pdf` | ZBZ-Lieferung (E23) |
| Faksimile | PNG 300 dpi | `docs/images/{doc}/{doc}_pNNN.png` | `scripts/edition/extract_pages.py` |
| Doc-Metadaten | JSON | `data/doc_metadata.json` | `scripts/ocr/classify_docs.py` (Gemini, E27) |
| OCR (Mistral) | Markdown pro Seite | `output/mistral_results/{doc}_pN.md` | `scripts/ocr/ocr_pipeline.py` |
| OCR (Gemini A/B) | Markdown korrigiert | `output/gemini_corrected_a/`, `_b/` | `scripts/ocr/gemini_ocr_correct.py` (E29) |
| Layout (Docling) | JSON, bbox in % | `output/layout/{doc}/{doc}_pNNN_layout.json` | `scripts/layout/run_layout_analysis.py` oder `run_layout_cloud.py` |
| Layout-QA (Gemini) | JSON | `output/layout/{doc}/{doc}_pNNN_layout_gemini.json` | `scripts/layout/layout_qa_gemini.py` (E25/E26) |
| Overlay-PNG | PNG | `output/overlay/{doc}/...` | `scripts/layout/generate_layout_overlays.py` |
| PAGE-XML | XML 2013-07-15 | `output/page_xml/{doc}/{doc}_pNNN.xml` | `scripts/layout/page_xml_generator.py` (E13) |
| METS | XML | `output/page_xml/{doc}/mets.xml` | `scripts/layout/mets_generator.py` |
| TEI-Scaffold (Step 1) | XML, regelbasiert | `output/tei_unified/{doc}_step1.xml` | `scripts/tei/tei_step1.py` |
| TEI-Gemini (Step 2) | XML, LLM-refined | `output/tei_unified/{doc}_step2.xml` | `scripts/tei/tei_step2.py` |
| TEI-Assembly (Step 3) | XML, post-processed | `output/tei_unified/{doc}.xml` | `scripts/tei/tei_step3.py` |
| TEI final | XML mit `<revisionDesc>` | `output/tei_final/{doc}_final.xml` | `scripts/tei/tei_add_revision.py` + `tei_status_marker.py` (E42, E43, E66) |
| Pro-Objekt-Manifest | JSON (Workflow-Status + History je Strom) | `output/tei_final/{doc}_manifest.json` | `scripts/edition/page_manifest.py` (E65/E66) |
| Review-JSON (Legacy) | JSON (abgeschafftes 7-Schichten-Screening, nur Diagnose-Spur) | `output/tei_final/{doc}_screening_legacy.json` | Agent-Screening, deprecated E66 |
| TEI final (Frontend) | XML | `docs/data/pages/{doc}/{doc}_final.xml` | `scripts/edition/generate_edition_data.py` |
| TEI per-Seite (Frontend) | XML (split via `<pb>`) | `docs/data/pages/{doc}/{doc}_pN.xml` | dito (E57) |
| Catalog (Frontend) | JSON | `docs/data/catalog.json` | dito |
| Thumbnails (Frontend) | JPG 140x200 q70 | `docs/data/thumbs/{doc}.jpg` | dito |
| Kuratierte TEI | XML | `data/curated_tei/{doc}/` | manuell (aktuell leer + `.gitkeep`) |

---

## 3. Persistenz im Viewer

Der Viewer (`docs/viewer.html`) ist eine statische Single-Page-App ohne
Backend. Der frueher vorhandene FastAPI-Curation-Server wurde mit E56/E57
abgeschafft. Aenderungen schreibt **ein** "Speichern"-Knopf direkt in den Repo-Klon
(File System Access API, Chromium) bzw. als Datei-Download (Fallback) und spiegelt sie
zugleich in den Viewer-Mirror, damit ein Reload den Stand zeigt (E72/E78/E79).

### 3.1 Lese-Pfad (read-only)

Der Viewer laedt ausschliesslich statische Files. Der Pfad-Resolver in
`docs/assets/js/core.js` benutzt eine dreistufige Fallback-Kette:

```
1. docs/data/pages/{doc}/{doc}_pN.{ext}   (Frontend-Mirror, alle 285 Docs)
2. docs/data/examples/{doc}/...           (Legacy 4 DEMO-Docs, Backward-Kompatibilitaet)
3. ../output/{stage}/...                  (lokaler Fallback fuer Engines, die nicht im Mirror sind)
```

Damit funktioniert der Viewer auf GitHub Pages fuer das gesamte Korpus. Lokal
sind zusaetzlich Gemini-A/B und LLM-Korrektur erreichbar.

### 3.2 Save-Mechanismus (ein "Speichern" -> direkt ins Repo + Mirror)

**Ein** "Speichern"-Knopf sichert alle ungespeicherten Stroeme zugleich (Layout, Text/TEI,
Manifest mit Workflow-Status; `saveAll()` in `viewer.js`). Schreibweg ist die File System Access
API (`ZBZ.FsAccess`, Chromium); ohne sie greift der Datei-Download (`ZBZ.Download`,
Firefox/Safari). Jede Speicher-Aktion schreibt die identische Nutzlast an **zwei** Orte --
kanonisch nach `output/` (Pipeline-Konsum) und in den Mirror `docs/data/` (Viewer-Reload, E79):

| Strom | Kanonisch (`output/`) | Mirror (`docs/data/`) | Modul |
|---|---|---|---|
| Layout | `layout/{doc}/{doc}_p{NNN}_layout_curated.json` | `pages/{doc}/{doc}_p{NNN}_layout_curated.json` | `ZBZ.FsAccess.writeLayout()` |
| Text | `ocr_curated/{doc}_p{N}.md` | `pages/{doc}/{doc}_p{N}.md` | `ZBZ.FsAccess.writeText()` |
| Manifest | `tei_final/{doc}_manifest.json` | `manifests/{doc}_manifest.json` | `ZBZ.FsAccess.writeManifest()` |
| TEI | `tei_final/{doc}_final.xml` | `pages/{doc}/{doc}_final.xml` | `ZBZ.FsAccess.writeTei()` |

Einzel-Export pro Strom bleibt ueber das **"Export ▾"**-Dropdown erreichbar (`ZBZ.Download.*`, E78).

**Bekannte Limitierungen (real, ehrlich):**

- Schreibrecht muss pro Sitzung per Geste re-granted werden (Browser-Vertrauensmodell, kein Defekt).
- Kein Konflikt-Erkennungs-Mechanismus bei parallelem Edit (Browser-State == Wahrheit).
- Per-Seiten-TEI-Splits im Mirror entstehen erst beim `--reassemble`; ein direkter TEI-XML-Edit ueberschreibt die SoT und wird von einem spaeteren `--reassemble` regeneriert.
- Re-Run der Pipeline (`tei_unified --reassemble`) muss manuell angestossen werden. Das Frontend kann das nicht triggern.

### 3.3 Round-Trip vom User-Edit zur regenerierten TEI

Vollstaendiger Ablauf, wenn ein User eine Layout-Region korrigiert hat:

1. **Edit im Viewer**: User klickt "Layout bearbeiten", korrigiert eine BBox.
2. **Speichern**: Klick auf "Speichern" schreibt `{doc}_p{NNN}_layout_curated.json` direkt nach `output/layout/{doc}/` (kanonisch) UND in den Mirror `docs/data/pages/{doc}/` (E78/E79); beim ersten Mal fragt der Viewer einmal nach dem Repo-Ordner. Ein Reload zeigt den Stand sofort.
3. (entfaellt — kein manuelles Ablegen mehr; der Edit liegt bereits an der kanonischen Stelle.)
4. **Pipeline-Re-Run** mit kuratierten Layout-Daten als Input:
   ```bash
   python -m scripts.tei.tei_unified --doc {ID} --reassemble
   ```
   Der `--reassemble`-Flag macht Step 1 (Scaffold aus kuratierter OCR/Layout) und Step 3 (Assembly) neu und nutzt den Gemini-Step-2-Cache. Seiten ohne neue Kuration bleiben kostenlos; Seiten mit neuerer kuratierter OCR/Layout werden gezielt neu von Gemini refined (je 1 Call), damit die Korrektur ins finale TEI gelangt (sonst assembliert Step 3 aus dem stale Cache an der Kuration vorbei). Wichtig: Gemini re-derivt dabei den Text — eine OCR-Korrektur ist ein Vorschlag, kein Verbatim-Durchgriff. Fuer wortgenaue Textaenderungen den TEI-XML-Modus nutzen; er schreibt `output/tei_final/{doc}_final.xml` direkt, an der Pipeline vorbei (verbatim, deterministisch).
5. **revisionDesc-Update**:
   ```bash
   python -m scripts.tei.tei_add_revision --doc {ID}
   ```
   Schreibt `<revisionDesc>` neu mit aktuellem Pipeline-Lauf. Der menschgesetzte Workflow-Status pro Strom wird bei der ZBZ-Uebergabe via `tei_status_marker.py` aus dem Manifest in den `<revisionDesc>` projiziert (E66).
6. **Validierung**:
   ```bash
   python -m scripts.tei.tei_validator --doc {ID}
   ```
7. **Frontend-Daten regenerieren**:
   ```bash
   python -m scripts.edition.generate_edition_data --mirror-only
   ```
   Aktualisiert `docs/data/pages/{doc}/` (inkl. `{doc}_final.xml`).

**Aktuelles Manko:** Schritte 4-7 sind nicht automatisiert. Es gibt keinen
"Apply Curated Edit"-Wrapper-Befehl. Ein solches Convenience-Script (z.B.
`scripts/apply_curated.py --doc {ID}`) waere ein sinnvoller naechster Schritt.

---

## 4. Provenance — aktuell vs. geplant

### 4.1 Aktuell: revisionDesc + Pro-Objekt-Manifest

| Speicher | Inhalt | Wo |
|---|---|---|
| `<revisionDesc>` im TEI-Header (E42) | `<change>`-Elemente: Pipeline-Stufen + Versionen + projizierter Workflow-Status (E66) + Datum | jedes finale TEI in `output/tei_final/` |
| `{doc}_manifest.json` (E65/E66) | Workflow-Status pro Strom (`ocr`/`layout`/`tei`) + History `[{at, by, from, to, note}]` + Ausnahme-Seiten (Leerseiten) | `output/tei_final/` |
| `{doc}_screening_legacy.json` (Legacy) | abgeschaffter 7-Schichten-Screening-Befund, nur Diagnose-Spur (deprecated E66) | `output/tei_final/` (gitignored) |
| Git-Log | Datei- und Code-Aenderungs-Historie | Repo |

**Was fehlt:**

- Edit-History pro Objekt (wer/was/wann hat manuell ediert)
- AI-Agent-Audit-Trails mit Konfidenz pro Entscheidung (Modell, Prompt-Version, Konfidenz)
- Roll-Back-Moeglichkeit auf frueheren Edit-Stand ohne Git-History
- Direkte Verknuepfung Region ↔ Body-Element (aktuell ueber Reading-Order implizit)

### 4.2 Geplant: `{doc}_provenance.json` pro Objekt

Ein zentrales Bearbeitungs-Log pro Dokument. Schema-Vorschlag:

```json
{
  "doc_id": "20",
  "current_state": {
    "layout_source": "gemini_corrected_v3.1+curated",
    "ocr_source": "mistral_2512",
    "tei_version": "1.4.2",
    "workflow_status": { "ocr": "unverifiziert", "layout": "bearbeitet", "tei": "unverifiziert" }
  },
  "history": [
    {
      "ts": "2026-02-14T09:23:00Z",
      "actor": "mistral-document-ai-2512",
      "kind": "ocr",
      "scope": "all pages",
      "ref": "output/mistral_results/20_p*.md"
    },
    {
      "ts": "2026-03-04T16:01:00Z",
      "actor": "gemini-3.1-flash-lite",
      "kind": "layout_qa",
      "scope": "all pages",
      "changes": 14,
      "ref": "output/layout/20_p*_layout_gemini.json"
    },
    {
      "ts": "2026-05-26T10:23:00Z",
      "actor": "human:ek",
      "kind": "workflow_status",
      "scope": "layout",
      "details": "unverifiziert -> bearbeitet",
      "ref": "output/tei_final/20_manifest.json"
    },
    {
      "ts": "2026-05-25T14:00:00Z",
      "actor": "human:chpollin",
      "kind": "layout_edit",
      "scope": "page 1",
      "details": "3 regions modified (bbox tweaks)",
      "ref": "output/layout/20_curated/20_p001_layout_curated.json"
    }
  ]
}
```

Eigenschaften:

- Single Source of Truth pro Objekt fuer die gesamte Bearbeitungsgeschichte
- Anzeigbar im Viewer als Provenance-Drawer (Etappe 2.11 in der UI-Welle)
- Erweiterbar fuer AI-Agent-Audit (Modell-Hash, Prompt-Version, Konfidenz)
- Roll-Back: jede Aktion verweist auf konkrete Datei in `output/...`
- Maschinenlesbar fuer Reports, Reviews und Archive

---

## 5. Geplant: `_complete.xml` — selbst-enthaltenes TEI

Aktuell ist `{doc}_final.xml` ein schlanker TEI ohne Layout-Apparat. Layout
liegt parallel in JSONs. Fuer Edition + Archiv + ZBZ-Uebergabe waere ein
**selbst-enthaltenes TEI** sinnvoll, das alle Layout-Informationen via
TEI-Standard-Apparat mitfuehrt.

### 5.1 TEI-Standard fuer eingebettetes Layout

```xml
<facsimile>
  <surface n="1" ulx="0" uly="0" lrx="2480" lry="3508">
    <graphic url="../images/20/20_p001.png"/>
    <zone xml:id="z_20_p001_r1" ulx="93" uly="660" lrx="2347" lry="803" type="heading"/>
    <zone xml:id="z_20_p001_r2" ulx="184" uly="838" lrx="2231" lry="901" type="paragraph"/>
    <!-- ... weitere Regionen ... -->
  </surface>
</facsimile>

<text>
  <body>
    <div type="text">
      <head facs="#z_20_p001_r1">JEANNE HERSCH</head>
      <p facs="#z_20_p001_r2">L'illusion philosophique</p>
      <!-- ... -->
```

Damit ist jedes Stueck Text rueckverfolgbar zur exakten Region im Faksimile —
Edition-Standard fuer digitale TEI-Editionen (eXist-db, TEI-Publisher, EVT,
FuD).

### 5.2 Zwei TEI-Varianten beim Export

| Variante | Inhalt | Verwendung |
|---|---|---|
| `{doc}_final.xml` (heute) | schlanker TEI, nur Text-Struktur, mit `<revisionDesc>` | bleibt als kompakte Lese-Variante |
| `{doc}_complete.xml` (geplant) | TEI + `<facsimile>` + `<zone>` + `@facs` + erweitertes `<revisionDesc>` mit Provenance-Items | Edition-Standard, Archiv, Export (E61), ZBZ-Uebergabe |

`_complete.xml` wird im Export-Modul (E61) Default-Variante; `_final.xml`
bleibt als Mini-Variante optional.

### 5.3 Verknuepfung Provenance ↔ revisionDesc

Im `<revisionDesc>` des `_complete.xml` werden die Items aus
`{doc}_provenance.json` eins-zu-eins als `<change>`-Elemente eingetragen:

```xml
<revisionDesc>
  <change when="2026-02-14T09:23:00Z" who="#mistral-2512" type="ocr">
    OCR durch Mistral Document AI 2512, alle Seiten</change>
  <change when="2026-03-04T16:01:00Z" who="#gemini-3.1-flash-lite" type="layoutQA">
    Layout-QA durch Gemini, 14 Korrekturen</change>
  <change when="2026-05-25T14:00:00Z" who="#person-chpollin" type="layoutEdit">
    Manuelle Layout-Korrektur, Seite 1, 3 Regionen</change>
  <change when="2026-05-26T10:23:00Z" who="#person-ek" status="bearbeitet" n="layout">
    Workflow-Status layout: unverifiziert -&gt; bearbeitet (E66)</change>
</revisionDesc>
```

Damit ist Provenance **innerhalb** des TEI, nicht parallel daneben. Single
Source of Truth in genau einer Datei.

### 5.4 Aufwand grob

| Schritt | Aufwand |
|---|---|
| `tei_unified.py step3 (Assembly)` um `<facsimile>` + `<zone>`-Generator erweitern | ~3 h |
| Body-Elements mit `@facs` annotieren (Mapping Region ↔ Body) | ~2 h |
| `<revisionDesc>` aus `provenance.json` zusammenbauen | ~1 h |
| Re-Run auf 285 Docs + Validierung gegen `zbz_hersch.rng` | ~2 h |
| Schema-Anpassung in `zbz_hersch.rng` falls noetig (`@type` auf `<zone>`, `@facs` auf Body) | ~1 h |
| **Gesamt** | **~9 h Pipeline-Welle** |

Separat von der UI-Welle, sollte ein eigenes Etappen-Paket sein.

---

## 6. Roadmap (vorlaeufig, Stand 2026-05-25)

| Welle | Inhalt | Status |
|---|---|---|
| Knowledge-Refactoring | alle knowledge-Docs + README auf Stand bringen, workflow.md neu, Drift-Befunde fixen | erledigt |
| Code-Drift-Fix | `generate_edition_data.py` behandelt fehlende `dashboard.json` jetzt als optional (`or {}`, mit E56-Kommentar) | erledigt |
| UI-Verdichtung Viewer (Etappe 2.10) | Erledigt (E64): Doc-Subbar + Toolbar fusioniert, OCR-Quellen-Umschalter entfernt (Viewer = Mistral), Edit-Toggles benannt ("Layout"/"Text" als Text-Label, **nicht** als Icons — User-Entscheidung). Offen: Region-Liste als Sub-Spalte, Downloads als Dropdown, Hint-Texte als Tooltips | teilweise (E64) |
| Per-Doc-Export-Drawer (Etappe 2.9) | JSZip-basierter Export aller Pipeline-Artefakte pro Doc, im Bulk-Modus auch aus Korpus-Uebersicht (Etappe 1.6) | geplant, abhaengig von Knowledge-Welle + (optional) `_complete.xml` |
| Quality-Drawer (Etappe 2.2) | `{doc}_review.json` als oeffenbares Drawer-Panel im Viewer | geplant |
| Provenance-Drawer (Etappe 2.11, neu) | `{doc}_provenance.json` als oeffenbares Drawer-Panel im Viewer; setzt voraus dass provenance.json existiert | geplant, blockiert durch Pipeline-Welle |
| Pipeline-Welle complete-TEI + Provenance | `tei_unified` erweitern um `<facsimile>` + `<zone>` + `@facs`; `provenance.json`-Generator (zunaechst aus revisionDesc + Datei-Timestamps abgeleitet); Schema-Anpassung | geplant |
| Etappe 1 (Korpus-Uebersicht) | Edition-Hero, Quality-Strip, Smart-Filter mit Live-Counts, klickbare Spalten-Header, Featured-Sektion, Multi-Select-Bulk-Export | geplant |
| Etappe 3 (about.html) | Workflow-Sektion mit Pipeline-Diagramm, CER-Visualisierung, Korpus-Komposition (3 Bar-Charts), Screening-Pyramide, Featured-Karten | geplant |
| Etappe 4 (Quer-Politur) | Token-Audit, Print-CSS, Site-Header schlanker | geplant |

Plan-Dokument (Stand der Welle):
`C:\Users\Chrisi\.claude\plans\edition-uplift-three-pages.md`.

---

## 7. Bekannte Drift / Action-Items

Die frueher hier gelisteten Code- und Doku-Drift-Punkte sind behoben:
`generate_edition_data.py` behandelt die geloeschte `dashboard.json` als optional (`or {}`),
die `scripts/postprocess/`-Verweise sind aus README und projekt.md entfernt (der eigenstaendige
`scripts/ocr/llm_postprocess.py` bleibt davon unberuehrt), und die Pipeline-Diagramme zeigen
PAGE-XML korrekt als Parallel-Export (E22). Historische Details im Git-Log.

Offen bleibt: der manuelle Round-Trip (Schritte 4-7 in §3.3 sind nicht in einem Wrapper
automatisiert) und die geplante Pipeline-Welle (`_complete.xml` + `provenance.json`, §5).

---

## 8. Verweise

- [pipeline.md](pipeline.md) — Pipeline-Stufen, Engines, TEI-Mapping
- [viewer.md](viewer.md) — Viewer-Architektur, Persistenz, Design-System
- [quality.md](quality.md) — CER, Screening, Validierung
- [decisions.md](decisions.md) — E1–E75, offene Punkte
- [methodik.md](methodik.md) — Promptotyping, Verifikationskaskade, Dreischichtung
- [journal.md](journal.md) — chronologische Sitzungs-Historie
- [index.md](index.md) — Navigation + Schluesselkonzepte
- Plan-Dokument fuer aktuelle Welle: `~/.claude/plans/edition-uplift-three-pages.md`
