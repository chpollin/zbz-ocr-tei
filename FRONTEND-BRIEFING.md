# Frontend-Briefing: Digitale Edition auf GitHub Pages publizieren

**Fuer:** Frontend-Entwickler:in (Claude Code oder Mensch)
**Stand:** 2026-03-15, nach Abschluss des Agent-Based Quality Screening
**Kontext:** 285 TEI-Dokumente sind erzeugt, gescreent und finalisiert. Die Edition soll auf GitHub Pages funktionieren.

---

## 1. Aktueller Zustand

### Was funktioniert
- `docs/index.html` — Landing Page
- `docs/catalog.html` — Katalog mit 286 Dokumenten
- `docs/reader.html` — TEI-Reader mit Faksimile + Entity-Sidebar
- `docs/about.html` — Projektinformation
- 4 Demo-Docs (1000, 1330, 1540, 2310) in `docs/data/examples/` — nur diese funktionieren auf GitHub Pages
- Lokal funktioniert alles ueber den Curation Server (`python -m scripts.server.curation_server`)

### Was NICHT funktioniert auf GitHub Pages
- 281 von 285 Docs haben keine TEI-Daten im `docs/`-Verzeichnis
- Der Reader versucht `../output/tei_final/` als Fallback — das existiert auf GitHub Pages nicht
- Kein Layout-Overlay, keine OCR-Ansicht, keine Entity-Daten fuer die meisten Docs
- Scan-Bilder nur fuer 4 Demo-Docs (4 GB waere zu gross fuer Git)

---

## 2. Daten, die nach docs/ kopiert werden muessen

Alle Daten liegen in `output/`. Sie muessen nach `docs/data/` kopiert werden, damit GitHub Pages sie servieren kann.

### Pflicht (Edition funktioniert ohne diese nicht)

| Quelle | Ziel | Groesse | Dateien | Zweck |
|--------|------|---------|---------|-------|
| `output/tei_final/{ID}_final.xml` | `docs/data/tei/{ID}_final.xml` | 17 MB | 285 | TEI fuer den Reader |
| `output/tei_final/{ID}_review.json` | `docs/data/tei/{ID}_review.json` | 1.1 MB | 285 | Screening-Status (Badges) |
| `docs/data/catalog.json` | (existiert) | 1.5 MB | 1 | Katalog-Daten |
| `docs/data/entity_index.json` | (existiert) | 2.5 MB | 1 | Entity-Sidebar |

### Empfohlen (Viewer-Features)

| Quelle | Ziel | Groesse | Dateien | Zweck |
|--------|------|---------|---------|-------|
| `output/page_xml/{ID}/` | `docs/data/page_xml/{ID}/` | 37 MB | ~4377 | PAGE-XML-Ansicht |
| `output/layout/{ID}/{ID}_p*_layout_gemini.json` | `docs/data/layout/{ID}/` | 2.8 MB | ~4300 | Layout-Overlay-Daten |
| `output/ocr_results/{ID}_p*.md` | `docs/data/ocr/{ID}/` | 29 MB | ~4100 | OCR-Text-Ansicht |
| `output/entities/{ID}/` | `docs/data/entities/{ID}/` | 22 MB | ~285 | Entity-Detail-Daten |

### Optional

| Quelle | Ziel | Groesse | Zweck |
|--------|------|---------|-------|
| `output/tei_unified/{ID}/{ID}_final.xml` | `docs/data/tei_unified/` | 16 MB | Pipeline-Zwischenschritt |
| `output/tei_ner/{ID}/` | `docs/data/tei_ner/` | 17 MB | NER-annotierte TEIs |

### NICHT hochladen (zu gross)

| Daten | Groesse | Grund |
|-------|---------|-------|
| `output/layout/{ID}/*.png` | 364 MB | Layout-Overlay-PNGs — zu gross, nur lokal |
| `docs/images/` (alle) | 4 GB | Scan-Bilder — viel zu gross |
| `output/layout/330/` | 1.2 GB | Einzelnes Doc mit 318 Seiten |

**Scan-Bilder:** Nur die 4 Demo-Docs behalten (`docs/images/1000/`, `1330/`, `1540/`, `2310/`). Fuer die restlichen 281 Docs braucht es entweder IIIF-Hosting oder einen Hinweis "Faksimile nur lokal verfuegbar".

---

## 3. JavaScript-Aenderungen

### edition-shared.js — TEI-Ladepfad

Aktuell (`fetchFullTei`, Zeile ~270):
```javascript
const paths = [
    `data/examples/${docId}/${docId}_final.xml`,
    `../output/tei_final/${docId}_final.xml`
];
```

Aendern zu:
```javascript
const paths = [
    `data/tei/${docId}_final.xml`,           // Neue Struktur (alle 285 Docs)
    `data/examples/${docId}/${docId}_final.xml`,  // Fallback (alte Demo-Docs)
    `../output/tei_final/${docId}_final.xml`      // Lokal-Fallback
];
```

Gleiches Muster fuer `fetchTei` (page-level Fallback).

### edition-catalog.js — Screening-Badge

`catalog.json` enthaelt pro Dokument:
```json
{
    "id": "290",
    "screening": "APPROVED",
    "screening_reviewer": "agent-screening-v2",
    "screening_date": "2026-03-15",
    ...
}
```

Badge-Logik:
- `APPROVED` → gruener Badge (z.B. "Geprueft")
- `APPROVED_WITH_NOTES` → gelber Badge ("Geprueft, Hinweise")
- `NEEDS_REVIEW` → roter Badge ("Pruefung noetig")
- `null` → grauer Badge ("Nicht gescreent")

Optional: Filter im Katalog nach Screening-Status.

### edition-reader.js — revisionDesc anzeigen

Jedes finale TEI hat im Header:
```xml
<revisionDesc>
    <change when="2026-03-15" who="pipeline">TEI generated</change>
    <change when="2026-03-15" who="agent-screening-v2" status="APPROVED">
        Agent-Based Quality Screening (L1:ok L2:ok ...). Findings...
    </change>
</revisionDesc>
```

Vorschlag: Im Reader als "Dokumentstatus"-Badge oder als ausklappbare Bearbeitungshistorie anzeigen.

### edition-editor.js — revisionDesc beim Speichern

Wenn der Curation Editor ein Dokument speichert, soll er automatisch einen neuen `<change>`-Eintrag in die `<revisionDesc>` schreiben:
```xml
<change when="2026-03-20" who="editor:{USERNAME}" status="in_review">
    Korrektur: [Beschreibung der Aenderung]
</change>
```

Das erfordert auch eine Anpassung im Curation Server (`scripts/server/curation_server.py`, `save_page_tei`).

---

## 4. Kopier-Script

Ein einfaches Script, das die Daten von `output/` nach `docs/data/` kopiert:

```bash
# TEI final (285 Docs)
mkdir -p docs/data/tei
cp output/tei_final/*_final.xml docs/data/tei/
cp output/tei_final/*_review.json docs/data/tei/

# Layout JSONs (nur JSONs, keine PNGs)
for dir in output/layout/*/; do
    doc_id=$(basename "$dir")
    mkdir -p "docs/data/layout/$doc_id"
    cp "$dir"/*_layout_gemini.json "docs/data/layout/$doc_id/" 2>/dev/null
    cp "$dir"/*_layout.json "docs/data/layout/$doc_id/" 2>/dev/null
done

# PAGE-XML
cp -r output/page_xml/ docs/data/page_xml/

# OCR Markdown
mkdir -p docs/data/ocr
cp output/ocr_results/*.md docs/data/ocr/

# Entity JSONs
cp -r output/entities/ docs/data/entities/
```

Geschaetzte Gesamtgroesse nach Kopie: **~110 MB** (ohne Bilder).

---

## 5. docs/edition/ Problem

Es gibt ein Verzeichnis `docs/edition/` mit aelteren Kopien der HTML/JS/CSS-Dateien. Die JS-Dateien in `docs/edition/js/` unterscheiden sich von `docs/js/`. `docs/edition/` ist **nicht committed** und stammt vermutlich von einem Refactoring-Versuch.

**Empfehlung:** Vergleichen, ob `docs/edition/` neuere oder aeltere Versionen enthaelt. Wenn aelter: loeschen. Wenn neuer: nach `docs/` mergen und `docs/edition/` loeschen.

---

## 6. Zusammenfassung der Aenderungen

| Bereich | Aufgabe | Prioritaet |
|---------|---------|------------|
| Daten kopieren | TEI + Review-JSONs nach `docs/data/tei/` | Hoch |
| JS anpassen | `fetchFullTei` Pfad auf `data/tei/` | Hoch |
| Katalog-Badge | Screening-Status als farbiger Badge | Mittel |
| Layout-Daten | Layout-JSONs nach `docs/data/layout/` | Mittel |
| Reader-Badge | revisionDesc als Dokumentstatus anzeigen | Mittel |
| OCR + Entities | Nach `docs/data/ocr/` + `docs/data/entities/` | Niedrig |
| Editor-Integration | revisionDesc beim Speichern schreiben | Niedrig (spaeter) |
| docs/edition/ | Duplikat klaeren und aufraumen | Niedrig |

---

## 7. Relevante Dateien

| Datei | Beschreibung |
|-------|-------------|
| `docs/js/edition-shared.js` | Zentrale Lade-Logik (fetchFullTei, fetchTei) |
| `docs/js/edition-catalog.js` | Katalog-Rendering |
| `docs/js/edition-reader.js` | TEI-Reader |
| `docs/js/edition-editor.js` | Curation Editor |
| `docs/data/catalog.json` | Katalog mit screening-Feld pro Doc |
| `scripts/generate_edition_data.py` | Erzeugt catalog.json (liest aus tei_final/) |
| `scripts/server/curation_server.py` | FastAPI Server (save_page_tei) |
| `knowledge/EDITION.md` | Edition-Architektur |
| `knowledge/CURATION.md` | Curation-Editor-Doku |
