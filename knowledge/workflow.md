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
 │   PAGE-XML (rule-based)                 NER (Gemini + Wikidata/GND)
 │   = paralleler Export                    │
 │   fuer coOCR-Kompatibilitaet             │
 │   NICHT TEI-Input                        │
 │                                          │
 │                                          ▼
 └────────► TEI-XML (Unified: Scaffold + Gemini-Refinement + Assembly)
            │
            ▼
            Quality Screening (Agent, 7 Schichten)
            │
            ▼
            output/tei_final/{doc}_final.xml + {doc}_review.json
            │
            ▼
            docs/data/tei/{doc}_final.xml (Git-tracked Mirror)
            │
            ▼
            Viewer (Inspektion + Korrektur)
            │
            ▼
            Browser-Download als JSON/MD/XML
            │
            ▼
            (manuell ins Repo, Pipeline-Re-Run)
```

**Schluesselpunkt (E22, oft missverstanden):** PAGE-XML ist KEIN Zwischenschritt
fuer TEI. TEI wird DIREKT aus Layout-JSON + OCR-Markdown via
`scripts/tei/tei_unified.py` generiert. PAGE-XML wird PARALLEL als Export fuer
coOCR / Transkribus erzeugt (`scripts/layout/page_xml_generator.py`).

---

## 2. Datenformate pro Stufe

| Stufe | Format | Hauptpfad | Quelle |
|---|---|---|---|
| Quell-PDF | PDF | `data/scans/{doc}.pdf` | ZBZ-Lieferung (E23) |
| Faksimile | PNG 300 dpi | `docs/images/{doc}/{doc}_pNNN.png` | `scripts/extract_pages.py` |
| Doc-Metadaten | JSON | `data/doc_metadata.json` | `scripts/classify_docs.py` (Gemini, E27) |
| OCR (Mistral) | Markdown pro Seite | `output/mistral_results/{doc}_pN.md` | `scripts/ocr_pipeline.py` |
| OCR (Gemini A/B) | Markdown korrigiert | `output/gemini_corrected_a/`, `_b/` | `scripts/gemini_ocr_correct.py` (E29) |
| Layout (Docling) | JSON, bbox in % | `output/layout/{doc}/{doc}_pNNN_layout.json` | `scripts/run_layout_analysis.py` oder `run_layout_cloud.py` |
| Layout-QA (Gemini) | JSON | `output/layout/{doc}/{doc}_pNNN_layout_gemini.json` | `scripts/layout_qa_gemini.py` (E25/E26) |
| Overlay-PNG | PNG | `output/overlay/{doc}/...` | `scripts/generate_layout_overlays.py` |
| PAGE-XML | XML 2013-07-15 | `output/page_xml/{doc}/{doc}_pNNN.xml` | `scripts/layout/page_xml_generator.py` (E13) |
| METS | XML | `output/page_xml/{doc}/mets.xml` | `scripts/layout/mets_generator.py` |
| NER-Output | JSON | `output/entities/{doc_id}/` | `scripts/ner/ner_extract.py` |
| Entity-Index | XML + JSON | `data/entities/*.xml`, `docs/data/entity_index.json` | `scripts/ner/entity_index.py` |
| Wikidata-Cache | JSON | `_wikidata_cache.json` | `scripts/ner/wikidata_linker.py` |
| TEI-Scaffold (Step 1) | XML, regelbasiert | `output/tei_unified/{doc}_step1.xml` | `scripts/tei/tei_step1.py` |
| TEI-Gemini (Step 2) | XML, LLM-refined | `output/tei_unified/{doc}_step2.xml` | `scripts/tei/tei_step2.py` |
| TEI-Assembly (Step 3) | XML, post-processed | `output/tei_unified/{doc}.xml` | `scripts/tei/tei_step3.py` |
| TEI-NER-injected | XML mit `<persName>` etc | `output/tei_ner/{doc}.xml` | `scripts/ner/ner_inject_tei.py` |
| TEI final | XML mit `<revisionDesc>` | `output/tei_final/{doc}_final.xml` | `scripts/tei/tei_add_revision.py` (E42, E43) |
| Review-JSON | JSON (7 Schichten) | `output/tei_final/{doc}_review.json` | Agent-Screening (E41) |
| TEI-Mirror (Frontend) | XML | `docs/data/tei/{doc}_final.xml` | `scripts/generate_edition_data.py` |
| TEI per-Seite (Frontend) | XML (split via `<pb>`) | `docs/data/pages/{doc}/{doc}_pN.xml` | dito (E57) |
| Catalog (Frontend) | JSON | `docs/data/catalog.json` | dito |
| Entity-Index (Frontend) | JSON | `docs/data/entity_index.json` | dito |
| Thumbnails (Frontend) | JPG 140x200 q70 | `docs/data/thumbs/{doc}.jpg` | dito |
| Kuratierte TEI | XML | `data/tei_curated/{doc}/` | manuell (aktuell leer + `.gitkeep`) |

---

## 3. Persistenz im Viewer

Der Viewer (`docs/viewer.html`) ist eine statische Single-Page-App ohne
Backend. Der frueher vorhandene FastAPI-Curation-Server wurde mit E56/E57
abgeschafft. Aenderungen mussten seitdem manuell aus dem Browser zurueck ins
Repo.

### 3.1 Lese-Pfad (read-only)

Der Viewer laedt ausschliesslich statische Files. Der Pfad-Resolver in
`docs/js/core.js` benutzt eine dreistufige Fallback-Kette:

```
1. docs/data/pages/{doc}/{doc}_pN.{ext}   (Frontend-Mirror, alle 285 Docs)
2. docs/data/examples/{doc}/...           (Legacy 4 DEMO-Docs, Backward-Kompatibilitaet)
3. ../output/{stage}/...                  (lokaler Fallback fuer Engines, die nicht im Mirror sind)
```

Damit funktioniert der Viewer auf GitHub Pages fuer das gesamte Korpus. Lokal
sind zusaetzlich Gemini-A/B, LLM-Korrektur und DeepSeek-OCR erreichbar.

### 3.2 Save-Mechanismus (Datei-Download)

Drei Edit-Modi liefern je einen Download:

| Aktion | Modul | Output-Dateiname | MIME |
|---|---|---|---|
| Layout speichern | `ZBZ.Download.layout()` in `docs/js/download.js` | `{doc}_p{N}_layout_curated.json` | `application/json` |
| Text speichern | `ZBZ.Download.text()` | `{doc}_p{N}_curated.md` | `text/markdown` |
| TEI speichern | `ZBZ.Download.tei()` | `{doc}_curated.xml` | `application/xml` |

Die Dateien werden vom Browser-Download-Dialog im Default-Ordner abgelegt.
Der User muss sie manuell ins Repo umkopieren — typischerweise nach:

- `output/layout/{doc}_curated/{doc}_p{N}_layout_curated.json`
- `output/{source}_curated/{doc}_p{N}.md`
- `data/tei_curated/{doc}/{doc}_curated.xml`

**Bekannte Limitierungen (real, ehrlich):**

- Keine Auto-Save im Browser. Schliesst der User den Tab ohne Download, gehen Edits verloren.
- Keine Wiederherstellung von Edits beim Neuladen der Seite (kein localStorage).
- Kein Konflikt-Erkennungs-Mechanismus bei parallelem Edit (Browser-State == Wahrheit).
- Die Ablage-Konvention (`output/layout/{doc}_curated/`) ist nicht erzwungen — kein Script prueft, ob kuratierte Files da landen, wo sie hingehoeren.
- Re-Run der Pipeline (`tei_unified --reassemble`) muss manuell angestossen werden. Das Frontend kann das nicht triggern.

### 3.3 Round-Trip vom User-Edit zur regenerierten TEI

Vollstaendiger Ablauf, wenn ein User eine Layout-Region korrigiert hat:

1. **Edit im Viewer**: User klickt Faksimile-Bearbeiten-Toggle, korrigiert eine BBox, klickt "Layout ↓".
2. **Download**: Browser laedt `{doc}_p{N}_layout_curated.json` in den Default-Download-Ordner.
3. **Manuelles Ablegen**: User kopiert die Datei nach `output/layout/{doc}_curated/{doc}_p{N}_layout_curated.json` (oder direkt ueberschreibt `_layout_gemini.json` — Konvention nicht final festgelegt).
4. **Pipeline-Re-Run** mit kuratierten Layout-Daten als Input:
   ```bash
   python -m scripts.tei.tei_unified --doc {ID} --reassemble
   ```
   Der `--reassemble`-Flag macht Step 1 (Scaffold) und Step 3 (Assembly) neu, nutzt Step-2-Cache (Gemini-Refinement bleibt). Damit reproduziert sich der TEI inkl. der manuellen Layout-Korrektur, kostenlos (kein neuer Gemini-Call).
5. **revisionDesc-Update**:
   ```bash
   python -m scripts.tei.tei_add_revision --doc {ID}
   ```
   Schreibt `<revisionDesc>` neu mit aktuellem Pipeline-Lauf + Screening-Status.
6. **Validierung**:
   ```bash
   python -m scripts.tei.tei_validator --doc {ID}
   ```
7. **Frontend-Daten regenerieren**:
   ```bash
   python -m scripts.generate_edition_data --doc {ID}
   ```
   Aktualisiert `docs/data/tei/{doc}_final.xml` und `docs/data/pages/{doc}/`.

**Aktuelles Manko:** Schritte 3-7 sind nicht automatisiert. Es gibt keinen
"Apply Curated Edit"-Wrapper-Befehl. Ein solches Convenience-Script (z.B.
`scripts/apply_curated.py --doc {ID}`) waere ein sinnvoller naechster Schritt.

---

## 4. Provenance — aktuell vs. geplant

### 4.1 Aktuell: revisionDesc + review.json

| Speicher | Inhalt | Wo |
|---|---|---|
| `<revisionDesc>` im TEI-Header (E42) | `<change>`-Elemente: Pipeline-Stufen + Versionen + Screening-Reviewer + Datum | jedes finale TEI in `output/tei_final/` |
| `{doc}_review.json` (E41) | 7-Schichten-Quality-Befund vom Agent-Screening (Scan, OCR, Layout, Struktur, Referenz, Entities, Kohaerenz) | `output/tei_final/` |
| Git-Log | Datei- und Code-Aenderungs-Historie | Repo |

**Was fehlt:**

- Edit-History pro Objekt (wer/was/wann hat manuell ediert)
- AI-Agent-Audit-Trails mit Konfidenz pro Entscheidung (Modell, Prompt-Version, Konfidenz, Kosten pro Call)
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
    "screening": "APPROVED",
    "screening_date": "2026-03-15"
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
      "ts": "2026-03-15T10:23:00Z",
      "actor": "agent-screening-v2",
      "kind": "screening",
      "result": "APPROVED",
      "ref": "output/tei_final/20_review.json"
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
- Erweiterbar fuer AI-Agent-Audit (Modell-Hash, Prompt-Version, Konfidenz, Cost-USD)
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
  <change when="2026-03-15T10:23:00Z" who="#agent-screening-v2" type="screening">
    7-Schichten-Screening, Status: APPROVED</change>
  <change when="2026-05-25T14:00:00Z" who="#person-chpollin" type="layoutEdit">
    Manuelle Layout-Korrektur, Seite 1, 3 Regionen</change>
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
| Knowledge-Refactoring | alle 10 knowledge-Docs + README auf Stand bringen, workflow.md neu, Drift-Befunde fixen | **in Arbeit (diese Session)** |
| Code-Drift-Fix | `generate_edition_data.py` referenziert geloeschte `dashboard.json` — Catalog-Rebuild ist vermutlich kaputt | offen |
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

### 7.1 Code-Drift

- **`scripts/generate_edition_data.py:268-271`** liest `docs/data/dashboard.json`,
  die in Session 44 geloescht wurde. Catalog-Rebuild ist vermutlich kaputt.
  Fix: entweder die Funktion `build_catalog()` umstellen auf direkte
  Quellen, oder `dashboard.json` aus den Quellen neu generieren.
- **`README.md:68`** + **`knowledge/projekt.md:129`** verweisen auf
  `scripts/postprocess/` — in Session 44 geloescht (Orphan, kein Konsument).
- **`scripts/llm_postprocess.py`** existiert noch — anders als der
  geloeschte `scripts/postprocess/`-Ordner. Naming-Verwirrung kann auftreten.

### 7.2 Doku-Drift (vor dieser Session)

| Datei | Drift |
|---|---|
| README.md | Pipeline-Diagramm zeigt PAGE-XML in der TEI-Kette (falsch, E22); `data/tei_curated/` als "versioned gold-standard" — real nur `.gitkeep` |
| knowledge/pipeline.md | gleicher Diagramm-Drift; kein Manual-Edit-Round-Trip; kein complete-TEI-Konzept; kein workflow.md-Verweis |
| knowledge/projekt.md | `scripts/postprocess/` Verweis; kein Session-45-Status |
| knowledge/quality.md | leichter Drift (E58–E61 nicht relevant, aber Stand-Update sinnvoll) |
| knowledge/{entities,infrastruktur,methodik}.md | wahrscheinlich nur Datum-Update noetig |

Alle Doku-Drift-Punkte werden in dieser Session adressiert (siehe Commit-Log
ab `54c0c735`).

---

## 8. Verweise

- [pipeline.md](pipeline.md) — Pipeline-Stufen, Engines, TEI-Mapping
- [viewer.md](viewer.md) — Viewer-Architektur, Persistenz, Design-System
- [quality.md](quality.md) — CER, Screening, Validierung
- [entities.md](entities.md) — NER, Wikidata, GND, Dual-Attribut (E50)
- [decisions.md](decisions.md) — E1–E61, offene Punkte
- [methodik.md](methodik.md) — Promptotyping, Verifikationskaskade, Dreischichtung
- [journal.md](journal.md) — chronologische Sitzungs-Historie
- [index.md](index.md) — Navigation + Schluesselkonzepte
- Plan-Dokument fuer aktuelle Welle: `~/.claude/plans/edition-uplift-three-pages.md`
