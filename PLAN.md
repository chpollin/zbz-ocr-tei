# Implementierungsplan: Volle KI-Pipeline (PDF → TEI-XML)

> **Version:** 1.1 | **Datum:** 26.02.2026 | **Autor:** Claude Opus 4.6
> **Kontext:** zbz-ocr-tei deckt die gesamte Pipeline ab. ZBZ behaelt Transkribus, DHCraft baut parallele KI-Pipeline.

Aktueller Komponentenstatus: [PROJEKT.md](knowledge/PROJEKT.md) §Komponentenstatus.
Pipeline-Stufen und CLI: [PIPELINE.md](knowledge/PIPELINE.md).

---

## Phasenuebersicht

| Phase | Beschreibung | Status |
|-------|-------------|--------|
| 0 | Layout-Evaluation (E19/E20) | **Erledigt** — Docling bestaetigt, 8/15 Docs analysiert |
| 1 | Layout-Post-Processing + PAGE-XML-Generator | **Naechster Schritt** |
| 2 | NER + GND-Verknuepfung | Ausstehend |
| 3 | TEI-XML-Generator erweitern | Teilweise (383 Dateien generiert, E22) |
| 4 | Erweiterte Evaluation + Dashboard | Ausstehend |
| 5 | Produktionslauf (289 Docs) | Ausstehend |

```
Phase 0 (Layout-Eval) ✓
    |
    v
Phase 1 (Layout + PAGE-XML) -----> Phase 2 (NER + GND)
                                        |
                                        v
                                   Phase 3 (TEI-XML erweitern)
                                        |
                                        v
                                   Phase 4 (Evaluation + Dashboard)
                                        |
                                        v
                                   Phase 5 (Produktion: 289 Docs)
```

Phase 1 und Phase 2 koennten parallel entwickelt werden (NER braucht nur OCR-Text, nicht PAGE-XML). Phase 3 benoetigt beides.

---

## Ziel-Datenfluss

```
PDF-Scan
  |
  +---> extract_pages.py -----> PNG-Bilder (300 DPI)
  |                                |
  +---> ocr_pipeline.py -----> Markdown (pro Seite)
  |                                |
  +---> layout_analyzer.py --> Regionen + BBox (JSON)
           |                       |
           +--- region_classifier.py --> ZBZ-Tags
                    |
                    v
          page_xml_generator.py --> PAGE-XML (pro Seite) + METS
                    |
                    v
          ner_pipeline.py -------> Entitaeten (JSON)
          gnd_linker.py ---------> GND-IDs (JSON)
                    |
                    v
          tei_generator.py ------> TEI-XML (DTA-Basisformat)
                    |
                    v
          evaluate_ocr.py -------> CER + Struktur + Entity Scores
          generate_dashboard_data.py --> Dashboard
```

---

## Phase 1: Layout-Post-Processing + PAGE-XML-Generator

> **Aufwand:** 3-4 Tage
> **Vorbedingung:** Phase 0 erledigt (E19/E20 finalisiert)
> **Blocker:** O21 (Layout-Post-Processing: Overlap, Einzeiler, Seitenzahlen)

### Neue Dateien

```
scripts/layout/
  __init__.py
  layout_analyzer.py       # Seitenbilder → LayoutRegion-Liste
  region_classifier.py     # Docling-Blocktypen → ZBZ-Tags
  page_xml_generator.py    # LayoutRegion + OCR-Text → PAGE-XML
  mets_generator.py        # METS-Manifest (Images + PAGE-XML)
```

### ZBZ-Structural-Tags (Mapping Docling → ZBZ)

| Docling BlockType | ZBZ Structural Tag | PAGE-XML TextRegion/@type | @custom |
|-------------------|--------------------|--------------------------|---------|
| Title | zb_heading | heading | `structure {type:zb_heading;}` |
| Section-header | zb_heading | heading | `structure {type:zb_heading;}` |
| Text / Paragraph | zb_paragraph | paragraph | `structure {type:zb_paragraph;}` |
| Footnote | footnote | footnote | `structure {type:footnote;}` |
| Page-header | (filtern) | - | - |
| Page-footer | (filtern) | - | - |
| Caption | caption | caption | `structure {type:caption;}` |
| (Abstand inferieren) | zb_space | other | `structure {type:zb_space;}` |

### ID-Schema (Transkribus-kompatibel)

```
Page:    {doc_id}_p{NN:03d}.xml
Region:  id="facs_{NN}_r_{N}"    → TEI: <p facs="#facs_{NN}_r_{N}">
Line:    id="facs_{NN}_r_{N}_tl_{M}" → TEI: <lb facs="#facs_{NN}_r_{N}_tl_{M}">
```

### Output-Struktur

```
output/page_xml/{doc_id}/
  mets.xml                    # METS-Manifest
  images/{doc_id}_p001.png    # Seitenbilder (Symlink oder Kopie)
  page/{doc_id}_p001.xml      # PAGE-XML pro Seite
```

### PAGE-XML Template

```xml
<?xml version="1.0" encoding="UTF-8"?>
<PcGts xmlns="http://schema.primaresearch.org/PAGE/gts/pagecontent/2019-07-15"
       xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
       xsi:schemaLocation="http://schema.primaresearch.org/PAGE/gts/pagecontent/2019-07-15
                           http://schema.primaresearch.org/PAGE/gts/pagecontent/2019-07-15/pagecontent.xsd">
  <Metadata>
    <Creator>zbz-ocr-tei pipeline</Creator>
    <Created>2026-02-25T00:00:00</Created>
  </Metadata>
  <Page imageFilename="../images/{doc_id}_p001.png"
        imageWidth="{width}" imageHeight="{height}">
    <TextRegion id="facs_1_r_1" type="paragraph"
                custom="structure {type:zb_paragraph;}">
      <Coords points="{x1},{y1} {x2},{y1} {x2},{y2} {x1},{y2}"/>
      <TextLine id="facs_1_r_1_tl_1">
        <Coords points="..."/>
        <TextEquiv>
          <Unicode>OCR-Text dieser Zeile</Unicode>
        </TextEquiv>
      </TextLine>
    </TextRegion>
  </Page>
</PcGts>
```

### Neue Config-Konstanten

```python
# Layout + PAGE-XML
PAGE_XML_DIR = OUTPUT_DIR / "page_xml"
PAGE_XML_NAMESPACE = "http://schema.primaresearch.org/PAGE/gts/pagecontent/2019-07-15"

ZBZ_STRUCTURAL_TAGS = {
    "zb_heading": {"page_type": "heading"},
    "zb_paragraph": {"page_type": "paragraph"},
    "zb_space": {"page_type": "other"},
    "zb_type_document": {"page_type": "other"},
    "footnote": {"page_type": "footnote"},
    "page-number": {"page_type": "page-number"},
    "caption": {"page_type": "caption"},
}

# Confidence-Mapping
CONFIDENCE_MISTRAL_RAW = 0.85
CONFIDENCE_LLM_CORRECTED = 0.95
```

### Validierung

1. PAGE-XML gegen XSD-Schema validieren (Schema herunterladen von primaresearch.org)
2. Visuelle Stichprobe: 3 Dokumente (1x Typ A, 1x Typ B, 1x Typ C)
3. Transkribus-Import-Test (falls Zugang vorhanden)

---

## Phase 2: NER + GND-Verknuepfung

> **Aufwand:** 2-3 Tage
> **Vorbedingung:** Phase 1 abgeschlossen (PAGE-XML existiert)

### Neue Dateien

```
scripts/ner/
  __init__.py
  ner_pipeline.py    # LLM-basierte NER (Claude Haiku 4.5)
  gnd_linker.py      # Zweistufig: Seed-Lookup → lobid.org API
  entity_store.py    # Per-Dokument JSON-Registry
```

### Ansatz

1. **NER via Claude Haiku 4.5:** JSON-Output mit `{text, type, start_char, end_char}`
   - Typen: person, organization, work
   - Seiten- oder absatzweise Verarbeitung
   - Prompt mit Kontext (Jeanne Hersch, Philosophie, 20. Jh.)

2. **GND-Linking Phase 1 (Seed):** Exakter + Fuzzy-Match gegen 75 bekannte Entitaeten
   - `config.py:KNOWN_ENTITIES` (11 Eintraege) + `output/gnd_analysis/gnd_entities.json` (75 Eintraege)
   - rapidfuzz fuer Fuzzy-Matching (bereits in requirements.txt)

3. **GND-Linking Phase 2 (lobid.org):** REST-API fuer unbekannte Entitaeten
   - `https://lobid.org/gnd/search?q={name}&filter=type:Person`
   - Cache + Rate-Limiting (max 10 req/s)
   - Ergebnis: GND-ID + Confidence

4. **Output:** `output/entity_registry/{doc_id}_entities.json`

### Bewertungskriterien

| Metrik | Ziel |
|--------|------|
| Entity Recall | >70% (gegen Referenz-TEI) |
| Entity Precision | >80% |
| GND-Linking-Rate | >60% der erkannten Entitaeten |
| GND-Korrektheit | >90% der verlinkten |

---

## Phase 3: TEI-XML-Generator erweitern

> **Status:** TEILWEISE IMPLEMENTIERT (E22)
> **Implementiert:** `scripts/tei/tei_generator.py` — 383 TEI-XML Dateien aus Layout-JSON + OCR-Markdown. Entity-Annotation aus Seed-Dict.
> **Offen:** PAGE-XML als Input, NER-Entitaeten aus Phase 2, Schema-Validierung, tei_header.py, tei_validator.py
> **Restaufwand:** 2-3 Tage (nach Phase 1+2)

### Noch zu erstellen

```
scripts/tei/
  tei_header.py       # teiHeader-Skelett (Titel, Publisher, Sprache)
  tei_validator.py    # Schema-Validierung + ZBZ-Inhaltsregeln
```

Transformationsregeln: [TEI-MAPPING.md](knowledge/TEI-MAPPING.md).

### Spezielle Dokumenttypen

| Typ | Docs | TEI-Besonderheit |
|-----|------|------------------|
| Rezension | 2310 | `<div type="review">` + `<bibl>` im `<head>` |
| Interview | 1440 | `<sp>/<speaker>` bei Sprecherwechsel |
| Lexikon | 3040 | `<div type="entry">` + `<head type="lemma">` |
| Monografie | 40, 1520 | Kapitel → `<div n="1">`, Abschnitte → `<div n="2">` |

### Validierung

1. TEI gegen DTA-Basisformat-Schema validieren
2. Vergleich mit Referenz-TEI (15 Pilot-Docs): Strukturelle Uebereinstimmung
3. Stichprobe in oXygen XML Editor: Keine fatalen Schema-Fehler

---

## Phase 4: Erweiterte Evaluation + Dashboard

> **Aufwand:** 2 Tage
> **Vorbedingung:** Phase 3 abgeschlossen

| Datei | Aenderung |
|-------|-----------|
| `scripts/evaluate_ocr.py` | Neuer Modus `--mode tei`: Text-CER + Strukturgenauigkeit + Entity-Scores |
| `scripts/generate_dashboard_data.py` | Pipeline-Status um 3 neue Stufen (page_xml, entities, tei_xml) |
| `docs/index.html` | Neue "TEI Pipeline"-Sektion mit 7-Stufen-Anzeige |

### Neue Metriken

| Metrik | Ziel |
|--------|------|
| Text-CER | <7% (aktuell 6.42%) |
| Struktur-Genauigkeit (ZBZ-Tags) | >80% |
| Entity Precision / Recall | >80% / >70% |
| GND-Korrektheit | >90% |
| TEI-Validitaet | 100% |

---

## Phase 5: Produktionslauf (alle 289 Dokumente)

> **Aufwand:** 2-3 Tage (inkl. Monitoring + Nacharbeit)
> **Vorbedingung:** Phase 4 abgeschlossen, Metriken erreicht

### Laufzeit-Schaetzung

| Stufe | Pro Seite | 7.200 Seiten | Kosten |
|-------|-----------|-------------|--------|
| OCR (Mistral) | ~1s | ~2h | $14.40 |
| Layout (Docling, CPU) | ~1s | ~2h | $0 |
| NER (Haiku 4.5) | ~0.5s | ~1h | ~$5 |
| GND (lobid.org) | ~0.1s | Cache-effizient | $0 |
| TEI-Transformation | ~0.1s | ~12min | $0 |
| **Gesamt** | | **~6h** | **~$20** |

### Ablauf

1. Alle 289 PDFs durch Stufen 1-6 verarbeiten (Batch-Mode)
2. Evaluation auf Gesamtkorpus laufen lassen
3. Dashboard aktualisieren
4. Stichproben-QA: 10 zufaellige Dokumente manuell pruefen
5. Ergebnisse in TESTPLAN.md und JOURNAL.md dokumentieren

---

## Abhaengigkeiten

### Python-Pakete

```
docling>=2.75.0               # Layout-Analyse (bereits installiert)
# anthropic, rapidfuzz, lxml, requests -- bereits vorhanden
```

### API-Keys (in .env)

| Key | Fuer | Status |
|-----|------|--------|
| `MISTRAL_DOC_AI_KEY` | OCR | Vorhanden |
| `ANTHROPIC_API_KEY` | LLM-Korrektur + NER | Vorhanden |
| `GOOGLE_API_KEY` | Gemini (optional) | Fehlt (nicht blockierend) |

---

## Risiken

Siehe [DECISIONS.md](knowledge/DECISIONS.md) §Risiken (R1-R13).

---

## Verifikation pro Phase

Nach jeder Phase:
1. **Automatische Tests:** Schema-Validierung, CER-Vergleich, Unit-Tests
2. **Manuelle Stichprobe:** 2-3 Pilotdokumente (1x Typ A, 1x Typ B, 1x Typ C/D)
3. **Dokumentation:** Ergebnis in TESTPLAN.md und JOURNAL.md
4. **Entscheidungen:** Neue E-Nummern in DECISIONS.md

**Finaler Akzeptanztest:** Generiertes TEI fuer Doc 2310 in oXygen oeffnen → keine Schema-Fehler, Entitaeten korrekt verlinkt.

---

*Erstellt: 25.02.2026 | Aktualisiert: 26.02.2026 (Redundanzen bereinigt, Status-Marker aktualisiert)*
