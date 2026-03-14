---
type: knowledge
created: 2026-03-08
updated: 2026-03-09
tags: [zbz-ocr-tei, curation, editor, tei]
status: active
---

# Curation Editor

Browser-basierter Editor zur manuellen Kuration von Pipeline-generierten TEI-XML-Dokumenten. Erweitert die Digitale Edition ([EDITION](EDITION.md)) um einen Edit-Modus — gleiche UI, zusaetzliche Editing-Funktionen wenn der Server laeuft.

**Dependencies:** [EDITION](EDITION.md) (Lese-Edition, Architektur), [PIPELINE](PIPELINE.md) (TEI-XML als Input), [GND-STRATEGIE](GND-STRATEGIE.md) (Entity-Kuration)

---

## Architektur

```
Edition Reader (read-only)  <-->  Edit-Modus (Curation)
         |                            |
    Statische Dateien          FastAPI Server (localhost:8000)
    (docs/data/examples/)             |
                                      v
                             data/tei_curated/{doc_id}/        (git-tracked)
                               {doc_id}_p{NNN}.xml    (kuratierte Seiten)
                               {doc_id}_final.xml     (assembliert)
                               {doc_id}_curation.json (Status + Historie)
                                      |
                              POST /publish
                                      v
                             docs/data/examples/{doc_id}/      (GitHub Pages)
```

**TEI-Prioritaet:** kuratiert > NER > unified > examples

**Speicher-Strategie:**
- `data/tei_curated/` — git-tracked, Gold-Standard, versioniert
- `output/tei_unified/`, `output/tei_ner/` — transient, gitignored, Pipeline-Output
- `docs/data/examples/` — publiziert via GitHub Pages (Kopie aus kuratiert)

## Server

**Datei:** `scripts/server/curation_server.py`

**Start:** `python -m scripts.server.curation_server [--port 8000]`

**URL:** `http://localhost:8000/reader.html`

### API Endpoints

| Methode | Pfad | Beschreibung |
|---------|------|-------------|
| GET | `/api/health` | Server-Status |
| GET | `/api/tei/{doc_id}/page/{page}` | Seiten-TEI laden |
| PUT | `/api/tei/{doc_id}/page/{page}` | Bearbeitete Seite speichern |
| POST | `/api/tei/{doc_id}/validate` | RelaxNG-Validierung (Final-XML) |
| POST | `/api/tei/{doc_id}/validate-page` | RelaxNG-Validierung (Seiten-XML) |
| POST | `/api/tei/{doc_id}/assemble` | Final-XML zusammenbauen |
| GET | `/api/tei/{doc_id}/status` | Kurations-Status |
| PUT | `/api/tei/{doc_id}/status` | Status aendern |
| POST | `/api/wikidata/search` | Wikidata-Suche (CORS-Proxy) |
| GET | `/api/entities/search?q=` | Lokalen Entity Index durchsuchen |
| POST | `/api/tei/{doc_id}/publish` | Kuratiertes TEI nach docs/examples publizieren |

## Frontend-Module

| Modul | Namespace | Zweck |
|-------|-----------|-------|
| `edition-editor.js` | `ZBZ.EditionEditor` | WYSIWYG Rendering, Serializer, Save |
| `edition-reader.js` | `ZBZ.EditionReader` | Edit-Toggle, Dirty-Tracking, Ctrl+S |
| `edition-tei.js` | `ZBZ.EditionTei` | Read-Only Rendering (unveraendert) |

## Editor-Operationen

### Text-Korrektur (Phase 1, implementiert)
- `contenteditable="true"` auf Block-Elementen (p, head, note)
- Entity-Spans sind `contenteditable="false"`
- Aenderungen werden via DOM-zu-XML Serializer gespeichert
- XML-Modus: direktes Editieren in Textarea

### Struktur-Editing (Phase 2, implementiert)
- Floating Block-Toolbar ueber fokussiertem Block
- Typ aendern (p/head/note/figure) via Dropdown
- Bloecke teilen (am Cursor), zusammenfuegen, loeschen

### Entity-Kuration (Phase 3, implementiert)
- Text markieren: Floating-Toolbar zeigt Person/Org/Ort/Werk Buttons
- Klick auf Entity: Popover mit Autocomplete (Entity Index + Wikidata)
- Autocomplete: Parallele Suche in lokalem Index + Wikidata API
- Tastatur-Navigation: Pfeil-Hoch/Runter, Enter zum Auswaehlen
- Entity-Typ aendern oder entfernen (X-Button)
- Wikidata-Suche via Server-Proxy (`/api/wikidata/search`)
- Lokaler Entity Index (`/api/entities/search`, Varianten-Match)

### TEI-Validierung (implementiert)
- "Validieren"-Button in Edit-Toolbar
- Server-seitige RelaxNG-Validierung (TEI All Schema)
- Validierungspanel zeigt Fehler mit Zeilennummern
- Wohlgeformtheitspruefung beim Speichern

### Review-Workflow (Phase 4, implementiert)
- Dokumenten-Status: pipeline > draft > in_review > approved
- Status-Badge im Reader-Header (nur wenn Server laeuft)
- Status-Badge im Katalog (Tabellen- und Kartenansicht)
- Publish-Endpoint: nur freigegebene Dokumente publizierbar

## Kurations-Metadaten

```json
{
  "doc_id": "2310",
  "status": "draft",
  "pages": {
    "1": {"status": "edited", "last_modified": "2026-03-08T14:30:00"}
  },
  "history": [
    {"timestamp": "...", "action": "page_saved", "page": 1}
  ]
}
```

## DOM-zu-XML Mapping

| DOM (CSS-Klasse) | TEI-Element | Attribute |
|---|---|---|
| `div.ed-tei-pb` | `<pb/>` | facs, n |
| `div.ed-tei-head` | `<head>` | facs |
| `div.ed-tei-p` | `<p>` | facs |
| `div.ed-tei-note` | `<note>` | place, n |
| `span.ed-tei-entity-person` | `<persName>` | ref |
| `span.ed-tei-entity-org` | `<orgName>` | ref |
| `span.ed-tei-entity-place` | `<placeName>` | ref |
| `span.ed-tei-entity-work` | `<bibl>` | ref |
| `span.ed-tei-hi-bold` | `<hi rendition="#b">` | |
| `br` | `<lb/>` | |

## Workflow

```
1. Pipeline laeuft  → output/tei_unified/ + output/tei_ner/ (transient)
2. Editor oeffnen   → http://localhost:8000/reader.html?doc=XXXX
3. Text korrigieren  → Speichern → data/tei_curated/{doc_id}/ (persistent)
4. Status setzen     → draft → in_review → approved
5. Publizieren       → POST /api/tei/{doc_id}/publish → docs/data/examples/
6. Git commit        → Kuratiertes TEI + Status versioniert
```

*Created: 2026-03-08 | Updated: 2026-03-09*
