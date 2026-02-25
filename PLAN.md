# Implementierungsplan: Volle KI-Pipeline (PDF → TEI-XML)

> **Version:** 1.0 | **Datum:** 25.02.2026 | **Autor:** KI-Pipeline-Architekt (Claude Opus 4.6)
> **Kontext:** Nach Meeting 25.02.2026 -- zbz-ocr-tei deckt die gesamte Pipeline ab. ZBZ behaelt Transkribus, DHCraft baut parallel eine vollautomatische KI-Pipeline.

---

## Ausgangslage

### Was existiert (Stufen 1-4)

| Stufe | Was | Script | Status |
|-------|-----|--------|--------|
| 1 | PDF → Seitenbilder (PNG) | `extract_pages.py` | Produktiv |
| 1a | Layout-Analyse (nur Typ B) | Docling in `ocr_pipeline.py` | Produktiv |
| 2 | OCR (Mistral Document AI) | `ocr_pipeline.py` | Produktiv, 93.58% Genauigkeit |
| 2a | LLM-Nachkorrektur (optional) | `llm_postprocess.py` | Produktiv, E17: optional |
| 3 | Evaluation (CER/WER) | `evaluate_ocr.py` | Produktiv, 15 Pilot-Docs |
| 4 | Dashboard | `generate_dashboard_data.py` | Produktiv |

**Datenbestand:** 15 Pilot-PDFs, 383 Seitenbilder, 15 Referenz-TEI, 75 GND-Entitaeten (Seed).

### Was fehlt (Stufen 5-9)

| Stufe | Was | Status |
|-------|-----|--------|
| 5 | Layout-Analyse → Strukturregionen + BBox | **Neu** (E19: Docling + Gemini) |
| 6 | Regionen + OCR → PAGE-XML | **Neu** |
| 7 | NER + GND-Verknuepfung | **Neu** |
| 8 | PAGE-XML + Entitaeten → TEI-XML | **Neu** |
| 9 | Erweiterte Evaluation + Dashboard | **Erweiterung** |

---

## Ziel-Pipeline (7 Stufen)

```
Stufe 1: PDF → Seitenbilder (PNG)              [EXISTIERT]
Stufe 2: Bilder → OCR-Markdown                 [EXISTIERT]
Stufe 3: Bilder → Layout-Regionen + BBox        [NEU - Docling]
Stufe 4: Layout + OCR → PAGE-XML               [NEU - Generator]
Stufe 5: PAGE-XML → NER + GND                  [NEU - Claude Haiku + lobid.org]
Stufe 6: PAGE-XML + Entitaeten → TEI-XML       [NEU - Transformation]
Stufe 7: Evaluation + Dashboard                 [ERWEITERUNG]
```

### Datenfluss

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

## Phase 0: Layout-Evaluation (Entscheidung E19)

> **Status:** Recherche abgeschlossen, Evaluation an Pilotdaten ausstehend

### Entscheidung E19: Docling + Gemini Hybrid

**Primaer:** Docling (IBM, MIT-Lizenz, gratis, CPU)
- RT-DETR V2 "Heron" Modell, 17 Blocktypen, DocLayNet mAP 0.699
- Bereits im Projekt validiert (Stufe 1a fuer Typ B Spaltenerkennung)
- Liefert BBox-Koordinaten fuer alle erkannten Regionen

**Sekundaer:** Gemini 2.5 Flash (Validierung + Anreicherung, optional)
- BBox-Output auf 0-1000 Skala, Structured JSON
- Extrem guenstig: $0.20-1.00 fuer 7.200 Seiten
- Nur bei Problemfaellen (Typ B zweispaltig, Typ D Spezial)

**Fallback:** Kraken OCR (nativer PAGE-XML-Export, historische FR-Dokumente)

**Ausfuehrliche Analyse:** [knowledge/E19-LAYOUT-ANALYSE.md](knowledge/E19-LAYOUT-ANALYSE.md)

### Naechster Schritt: Evaluation an Pilotdaten

1. Docling Layout-Analyse auf alle 383 Seitenbilder laufen lassen
2. Blocktypen → ZBZ-Tags mappen (siehe Tabelle unten)
3. Visuell pruefen: Stimmen die Regionen mit dem Seitenbild ueberein?
4. Bei Problemfaellen (Typ B): Gemini als Alternative testen

**Bewertungskriterien:**

| Metrik | Schwellwert |
|--------|-------------|
| Regiontyp-Genauigkeit | >80% korrekte ZBZ-Tags |
| Lesereihenfolge Typ A | >90% korrekt |
| Spalten-Trennung Typ B | korrekt fuer 2530, 890, 3040 |
| API-Kosten/Seite | <$0.002 |
| Laufzeit/Seite | <3s (CPU) |

---

## Phase 1: Layout-Analyse + PAGE-XML-Generator

> **Geschaetzter Aufwand:** 3-4 Tage
> **Vorbedingung:** Phase 0 abgeschlossen (E19 finalisiert)

### Neue Dateien

```
scripts/layout/
  __init__.py
  layout_analyzer.py       # Seitenbilder → LayoutRegion-Liste
  region_classifier.py     # Docling-Blocktypen → ZBZ-Tags
  page_xml_generator.py    # LayoutRegion + OCR-Text → PAGE-XML
  mets_generator.py        # METS-Manifest (Images + PAGE-XML)
```

### Zu erweitern

- `scripts/config.py` -- Neue Konstanten (siehe unten)

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

### Risiko R7: Transkribus-Kompatibilitaet

Die @type/@custom-Attribute muessen mit dem Transkribus-Format kompatibel sein. **Mitigation:** Vor Implementierung eine echte Transkribus-PAGE-XML-Exportdatei von der ZBZ anfordern und Konvention verifizieren.

---

## Phase 2: NER + GND-Verknuepfung

> **Geschaetzter Aufwand:** 2-3 Tage
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

### Risiko R10: NER-Qualitaet auf Franzoesisch

66% des Korpus ist Franzoesisch. **Mitigation:** Seed-Dictionary als erste Schicht VOR LLM-NER. Bekannte Entitaeten werden ohne LLM erkannt.

---

## Phase 3: TEI-XML-Generator

> **Geschaetzter Aufwand:** 4-5 Tage
> **Vorbedingung:** Phase 1 + Phase 2 abgeschlossen

### Neue Dateien

```
scripts/tei/
  __init__.py
  tei_generator.py    # PAGE-XML + Entitaeten → TEI-XML
  tei_header.py       # teiHeader-Skelett (Titel, Publisher, Sprache)
  tei_validator.py    # Schema-Validierung + ZBZ-Inhaltsregeln
```

### Transformationslogik

| PAGE-XML Region (ZBZ-Tag) | TEI-Element |
|---------------------------|-------------|
| zb_heading | `<head>` innerhalb `<div n="1/2/3">` |
| zb_paragraph | `<p facs="#facs_{N}_r_{M}">` mit `<lb>` pro Zeile |
| zb_space | `<space dim="vertical"/>` |
| footnote | `<note place="foot" n="..." xml:id="fn{page}-{num}">` |
| page-number | `<pb facs="#f{N}" n="..."/>` |
| caption | `<figure><head>...</head></figure>` |
| zb_type_document | `<div type="...">` (interview, review, entry) |

### Spezielle Dokumenttypen

| Typ | Docs | TEI-Besonderheit |
|-----|------|------------------|
| Rezension | 2310 | `<div type="review">` + `<bibl>` im `<head>` |
| Interview | 1440 | `<sp>/<speaker>` bei Sprecherwechsel |
| Lexikon | 3040 | `<div type="entry">` + `<head type="lemma">` |
| Monografie | 40, 1520 | Kapitel → `<div n="1">`, Abschnitte → `<div n="2">` |

### Markdown → TEI-Inline

| Markdown | TEI |
|----------|-----|
| `**bold**` | `<hi rendition="#b">` |
| `*italic*` | `<hi rendition="#i">` |
| Person (NER) | `<persName ref="GND:...">` |
| Organisation (NER) | `<orgName ref="GND:...">` |
| Werk (NER) | `<bibl corresp="GND:...">` |

### TEI-Grundgeruest (DTA-Basisformat)

```xml
<?xml version='1.0' encoding='UTF-8'?>
<TEI xmlns='http://www.tei-c.org/ns/1.0' type="naegeli">
  <teiHeader>
    <fileDesc>
      <titleStmt><title>{Dokumenttitel}</title></titleStmt>
      <publicationStmt><publisher>ZBZ</publisher></publicationStmt>
      <sourceDesc><p>OCR-Pipeline zbz-ocr-tei</p></sourceDesc>
    </fileDesc>
    <profileDesc>
      <langUsage><language ident="{iso639-3}">{Sprache}</language></langUsage>
    </profileDesc>
  </teiHeader>
  <text>
    <body>
      <pb facs="#f0001" n="1"/>
      <div n="1">
        <!-- Transformierter Inhalt -->
      </div>
    </body>
  </text>
</TEI>
```

### Risiko R9: Fussnoten-Platzierung

Fussnoten koennen inline (an der Textstelle) oder gesammelt (am div-Ende) platziert werden. **Default:** `--footnote-strategy end-of-div` (sicherer). `inline` als Opt-in.

### Validierung

1. TEI gegen DTA-Basisformat-Schema validieren
2. Vergleich mit Referenz-TEI (15 Pilot-Docs): Strukturelle Uebereinstimmung
3. Stichprobe in oXygen XML Editor: Keine fatalen Schema-Fehler

---

## Phase 4: Erweiterte Evaluation + Dashboard

> **Geschaetzter Aufwand:** 2 Tage
> **Vorbedingung:** Phase 3 abgeschlossen

### Zu erweitern

| Datei | Aenderung |
|-------|-----------|
| `scripts/evaluate_ocr.py` | Neuer Modus `--mode tei`: Text-CER + Strukturgenauigkeit + Entity-Scores |
| `scripts/generate_dashboard_data.py` | Pipeline-Status um 3 neue Stufen (page_xml, entities, tei_xml) |
| `docs/index.html` | Neue "TEI Pipeline"-Sektion mit 7-Stufen-Anzeige |

### Neue Metriken

| Metrik | Beschreibung | Ziel |
|--------|--------------|------|
| Text-CER | Zeichenfehlerrate OCR vs. Referenz | <7% (aktuell 6.42%) |
| Struktur-Genauigkeit | Anteil korrekt zugeordneter ZBZ-Tags | >80% |
| Entity Precision | Korrekt erkannte Entitaeten / alle erkannten | >80% |
| Entity Recall | Korrekt erkannte / alle im Referenz-TEI | >70% |
| GND-Korrektheit | Richtige GND-IDs / alle zugeordneten | >90% |
| TEI-Validitaet | Valide TEI-Dateien / alle generierten | 100% |

---

## Phase 5: Produktionslauf (alle 289 Dokumente)

> **Geschaetzter Aufwand:** 2-3 Tage (inkl. Monitoring + Nacharbeit)
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

## Neue Abhaengigkeiten

### Python-Pakete (zu ergaenzen in requirements.txt)

```
# Layout-Analyse (Phase 1)
docling>=2.75.0               # Layout-Analyse mit RT-DETR Heron

# NER + GND (Phase 2)
# (Claude Haiku via Anthropic API -- bereits vorhanden)
# (rapidfuzz -- bereits vorhanden)
# (requests -- bereits vorhanden)

# TEI-Validierung (Phase 3)
# (lxml -- bereits vorhanden)
```

### API-Keys (in .env)

| Key | Fuer | Status |
|-----|------|--------|
| `MISTRAL_DOC_AI_KEY` | OCR (Stufe 2) | Vorhanden |
| `ANTHROPIC_API_KEY` | LLM-Korrektur + NER | Vorhanden |
| `GOOGLE_API_KEY` | Gemini (Layout-Validierung, optional) | **Fehlt** |

---

## Risikomatrix

| # | Risiko | Impact | Wahrsch. | Mitigation |
|---|--------|--------|----------|------------|
| R7 | Transkribus-Inkompatibilitaet PAGE-XML | Hoch | Mittel | ZBZ-Exportdatei anfordern, Format verifizieren |
| R8 | Docling BBox-Qualitaet unzureichend | Mittel | Niedrig | Gemini als Fallback, Kraken als Alternative |
| R9 | Fussnoten-Inline-Platzierung fehlerhaft | Mittel | Mittel | Default: end-of-div, inline als Opt-in |
| R10 | NER-Qualitaet auf Franzoesisch | Mittel | Mittel | Seed-Dictionary vor LLM-NER |
| R11 | lobid.org API-Aenderungen | Niedrig | Niedrig | Cache + Fallback auf lokale GND-Daten |
| R12 | TEI-Schema-Inkompatibilitaet | Hoch | Niedrig | Referenz-TEI als Ground Truth, Schema-Validierung |
| R13 | Gemini API-Key fehlt | Niedrig | Sicher | Gemini ist optional, Docling reicht fuer Hauptfall |

---

## Kritische Dateien

| Datei | Rolle | Aenderungsart |
|-------|-------|---------------|
| `scripts/config.py` | Zentrale Konfiguration | **Erweitern** (ZUERST) |
| `scripts/layout/*.py` | Layout + PAGE-XML | **Neu** (4 Dateien) |
| `scripts/ner/*.py` | NER + GND | **Neu** (3 Dateien) |
| `scripts/tei/*.py` | TEI-Transformation | **Neu** (3 Dateien) |
| `scripts/evaluate_ocr.py` | Evaluation | **Erweitern** |
| `scripts/generate_dashboard_data.py` | Dashboard | **Erweitern** |
| `data/referenz-tei/Pilot/*.xml` | Ground Truth | **Nur lesen** |

---

## Verifikation pro Phase

Nach jeder Phase:
1. **Automatische Tests:** Schema-Validierung, CER-Vergleich, Unit-Tests
2. **Manuelle Stichprobe:** 2-3 Pilotdokumente (1x Typ A, 1x Typ B, 1x Typ C/D)
3. **Dokumentation:** Ergebnis in TESTPLAN.md und JOURNAL.md
4. **Entscheidungen:** Neue E-Nummern in DECISIONS.md

**Finaler Akzeptanztest:** Generiertes TEI fuer Doc 2310 (Referenz-Rezension) in oXygen oeffnen → keine fatalen Schema-Fehler, Entitaeten korrekt verlinkt.

---

## Abhaengigkeitsdiagramm

```
Phase 0 (Layout-Eval)
    |
    v
Phase 1 (Layout + PAGE-XML) -----> Phase 2 (NER + GND)
                                        |
                                        v
                                   Phase 3 (TEI-XML)
                                        |
                                        v
                                   Phase 4 (Evaluation + Dashboard)
                                        |
                                        v
                                   Phase 5 (Produktion: 289 Docs)
```

Phase 1 und Phase 2 koennten theoretisch parallel entwickelt werden (NER braucht nur den OCR-Text, nicht PAGE-XML). Die TEI-Transformation in Phase 3 benoetigt jedoch beides.

---

*Erstellt: 25.02.2026 | Naechster Schritt: Phase 0 Evaluation (Docling auf Pilotdaten)*
