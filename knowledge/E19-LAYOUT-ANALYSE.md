# E19: Layout-Analyse -- Recherche und Entscheidung

> **Status:** Recherche abgeschlossen, Empfehlung formuliert, Evaluation ausstehend
> **Datum:** 25.02.2026
> **Kontext:** Scope-Erweiterung nach Meeting 25.02.2026 -- zbz-ocr-tei deckt jetzt die gesamte Pipeline ab (PDF -> TEI-XML). Fuer die PAGE-XML-Erzeugung (Stufe 3) brauchen wir Layout-Analyse mit Strukturerkennung und Bounding-Box-Koordinaten.

## Anforderungen

Die Layout-Analyse muss:
1. **Strukturelemente erkennen:** Headings, Paragraphs, Footnotes, Page-Numbers, Captions, Spaces
2. **ZBZ-Tags zuordnen:** zb_heading, zb_paragraph, zb_space, zb_type_document, footnote, page-number, caption
3. **Bounding-Box-Koordinaten liefern** fuer PAGE-XML TextRegion/Coords
4. **Franzoesisch/Deutsch** unterstuetzen (66% FR, 30% DE)
5. **Kosten tragbar** bei 7.200 Seiten (<$100 gesamt)
6. **In PAGE-XML 2019-07-15 konvertierbar** sein (oder nativ liefern)

## Bewertete Ansaetze

### A. Gemini 2.5 Flash / 3.0 Flash (Vision + Structured Output)

**Faehigkeiten:**
- BBox-Output: Ja, `[ymin, xmin, ymax, xmax]` auf 0-1000 Skala, custom Labels moeglich
- Structured JSON: Voll unterstuetzt (`response_json_schema` mit Pydantic)
- PDF-nativ: Bis 1.000 Seiten/Request, 258 Tokens/Seite
- Segmentierungsmasken: Ab Gemini 2.5 (Pixel-Level)
- Mehrsprachig: Stark fuer FR/DE (Latein-Schrift)

**Kosten:**
- Gemini 2.5 Flash-Lite: $0.10/1M Input-Tokens → ~$0.00003/Seite
- Gemini 3 Flash: $0.50/1M → ~$0.00013/Seite
- **7.200 Seiten: ~$0.20 - $1.00** (extrem guenstig)

**Limits:** Max 3.600 Bilder/Request. Gemini 2.0 ist deprecated, 2.5 stabil, 3.x Preview.

**Staerken:** Ein API-Call liefert OCR + Layout + Strukturklassifikation + BBox in JSON. Flexibelstes Prompt-Schema. Guenstigste Option.

**Schwaechen:** Kein dediziertes Layout-Modell -- Qualitaet der BBoxen promptabhaengig. Keine Benchmarks fuer Dokumenten-Layout-Segmentierung publiziert. Preview-Modelle koennen sich aendern.

**Bewertung:** ★★★★☆

### B. Claude Vision (Opus 4.6 / Haiku 4.5)

**Faehigkeiten:**
- BBox-Output: **Nein** -- qualitative Beschreibungen ("oben links"), keine Pixel-Koordinaten
- Structured JSON: Via Tool Use, aber ohne Koordinaten
- PDF-nativ: Ja, bis 100 Seiten/Request
- Mehrsprachig: Exzellent fuer FR/DE

**Kosten:**
- Haiku 4.5: ~$0.003-0.006/Seite (3.000 Tokens/Bild)
- **7.200 Seiten: ~$22 - $43**

**Staerken:** Bestes Reasoning ueber Dokumentstruktur und Semantik. Ideal fuer QA/Verifikation und TEI-Erzeugung.

**Schwaechen:** **Kann keine BBox-Koordinaten liefern** -- disqualifiziert fuer Layout-Analyse mit PAGE-XML-Koordinaten. Bild-Downscaling auf 1.568px max.

**Bewertung:** ★★☆☆☆ (fuer Layout-Analyse ungeeignet, aber wertvoll fuer TEI-Erzeugung/QA)

### C. Mistral Document AI 2512 (bereits im Projekt)

**Faehigkeiten:**
- OCR: Exzellent (93.58% Genauigkeit, validiert)
- BBox fuer Bilder/Figures: Ja (Pixel-Koordinaten)
- BBox fuer Text-Regionen: **Nein** -- keine Koordinaten fuer Headings, Paragraphs, Footnotes
- `document_annotation`: Strukturierte JSON-Extraktion moeglich, aber **max 8 Seiten/Request**
- `extract_header`/`extract_footer`: Ja (noch nicht getestet, O19)
- Strukturerkennung via Markdown: Implizit (# Heading, Paragraphs, Listen)

**Kosten:**
- OCR: $2/1.000 Seiten → **7.200 Seiten: $14.40**
- Annotation: $3/1.000 Seiten

**Staerken:** Bereits integriert und validiert. Markdown-Output kodiert Struktur implizit. extract_header/footer nuetzlich.

**Schwaechen:** **Keine BBox fuer Text-Regionen** -- kann nicht "hier beginnt ein Paragraph bei Pixel x,y" sagen. Annotation-Limit 8 Seiten/Request ist restriktiv. Kein neueres Modell als 2512 verfuegbar.

**Bewertung:** ★★★☆☆ (hervorragend fuer OCR, unzureichend fuer Layout-Koordinaten)

### D. Docling (IBM, Open Source)

**Faehigkeiten:**
- Layout-Modell: RT-DETR V2 "Heron" (42.9M Params), trainiert auf DocLayNet
- **17 Blocktypen:** Caption, Footnote, Formula, List-item, Page-footer, Page-header, Picture, Section-header, Table, Text, Title, Document Index, Code, u.a.
- BBox: Ja, fuer alle erkannten Bloecke (JSON mit Provenance)
- Body vs. Furniture: Unterscheidet Hauptinhalt von Kopf-/Fusszeilen
- DocLayNet mAP: **0.699** (Heron), AP-50: 0.859

**Kosten:** Gratis (MIT-Lizenz). CPU: ~1 Sek/Seite. GPU: 28ms/Seite (A100).
- **7.200 Seiten CPU: ~2 Stunden. Kosten: $0.**

**Limits:** v2.75.0 (24.02.2026, aktuellste). Kein PAGE-XML-Export nativ -- JSON-Konvertierung noetig.

**Mapping Docling → ZBZ-Tags:**

| Docling BlockType | ZBZ Structural Tag |
|-------------------|--------------------|
| Title | zb_heading |
| Section-header | zb_heading |
| Text / Paragraph | zb_paragraph |
| Footnote | footnote |
| Page-header | (filtern/ignorieren) |
| Page-footer | (filtern/ignorieren) |
| Caption | caption |
| (Vertikaler Abstand inferieren) | zb_space |

**Staerken:** Bereits im Projekt validiert (Stufe 1a). Beste Open-Source Layout-Segmentierung. 17 Klassen decken unsere Beduerfnisse ab. Gratis.

**Schwaechen:** Kein PAGE-XML-Export (Custom-Konverter noetig). Encoding-Probleme bei integrierter OCR (E2 -- wir verwenden nur Layout). Kein eigener OCR-Text.

**Bewertung:** ★★★★★

### E. Surya

**Faehigkeiten:**
- 15 Blocktypen incl. Footnote, Caption, Section-header, Page-header/footer
- BBox + Polygon-Koordinaten + Lesereihenfolge + Confidence
- OCR in 90+ Sprachen, LaTeX-OCR, Tabellenstruktur
- GPU: 7-20 GB VRAM je nach Modell

**Kosten:** Gratis fuer Forschung und Startups (<$2M Umsatz). GPL-Lizenz.

**Staerken:** Starke Alternative zu Docling. Lesereihenfolge nativ. Confidence-Werte pro Region.

**Schwaechen:** GPL-Lizenz koennte fuer ZBZ-Fork problematisch sein. GPU-intensiv. Kein PAGE-XML.

**Bewertung:** ★★★★☆

### F. Kraken OCR

**Faehigkeiten:**
- Speziell fuer **historische Dokumente** entwickelt (EPHE Paris)
- Trainierbare Layout-Analyse mit Baseline-Segmentierung
- **Nativer PAGE-XML und ALTO Export**
- Lesereihenfolge-Erkennung
- Wort-BBox und Zeichen-Level-Segmentierung

**Kosten:** Gratis (Apache 2.0). v6.0.4 (Feb 2026), aktiv gepflegt.

**Staerken:** Einziges Tool mit nativem PAGE-XML-Export. Fuer historische franzoesische Dokumente konzipiert. Perfekter Domain-Fit.

**Schwaechen:** Trainierbare Klassen (kein vordefiniertes ZBZ-Schema). Layout-Modell muss ggf. trainiert oder angepasst werden. Kleinere Community als Docling.

**Bewertung:** ★★★★☆

### G. Azure Document Intelligence

**Faehigkeiten:**
- Paragraph-Rollen: title, sectionHeading, footnote, pageNumber, pageHeader, pageFooter
- BBox (Polygon-Koordinaten) fuer alle Elemente
- Tabellen mit Zellstruktur, Figures mit Captions
- FR/DE voll unterstuetzt

**Kosten:** ~$0.01/Seite → **7.200 Seiten: ~$72**. Kostenlos: 500 Seiten/Monat.

**Staerken:** ZBZ nutzt bereits Azure (Mistral). Sehr gute Paragraph-Rollen-Erkennung. Enterprise-Grade.

**Schwaechen:** Cloud-only. Kein PAGE-XML. Kosten hoeher als Docling (gratis).

**Bewertung:** ★★★☆☆

## Bewertungsmatrix

| Kriterium (Gewicht) | Gemini | Claude | Mistral | Docling | Surya | Kraken | Azure DI |
|---------------------|--------|--------|---------|---------|-------|--------|----------|
| **Strukturerkennung** (30%) | 4 | 3 | 2 | 5 | 4 | 4 | 4 |
| **BBox-Koordinaten** (25%) | 4 | 0 | 1 | 5 | 5 | 5 | 5 |
| **PAGE-XML-nah** (15%) | 2 | 0 | 0 | 3 | 2 | 5 | 2 |
| **FR/DE** (10%) | 4 | 5 | 5 | 4 | 4 | 5 | 5 |
| **Kosten** (10%) | 5 | 2 | 3 | 5 | 5 | 5 | 2 |
| **Integration** (10%) | 3 | 4 | 5 | 4 | 3 | 3 | 3 |
| **Gewichteter Score** | **3.45** | **1.95** | **2.15** | **4.35** | **3.85** | **4.15** | **3.45** |

Skala: 0 = ungeeignet, 1 = schlecht, 2 = maessig, 3 = akzeptabel, 4 = gut, 5 = exzellent

## Empfehlung

### Primaer: Docling + Gemini Hybrid (Ansatz D+A)

**Empfohlene Architektur:**

```
Seitenbild
  |
  +--> Docling (Layout-Analyse, CPU, gratis)
  |      Ergebnis: Regionen mit BBox + Blocktypen (17 Klassen)
  |
  +--> Mistral OCR (Text pro Seite, bereits vorhanden)
  |      Ergebnis: Markdown mit impliziter Struktur
  |
  +--> Gemini 2.5 Flash (Validierung + Anreicherung, optional)
         Ergebnis: Strukturklassifikation, Lesereihenfolge, ZBZ-Tag-Zuordnung
         Nur bei Problemfaellen (Typ B zweispaltig, Typ D Spezial)
```

**Begruendung:**
1. **Docling** liefert die besten Open-Source BBox-Koordinaten (mAP 0.699) mit 17 Klassen incl. Footnote -- gratis, CPU-tauglich, bereits im Projekt
2. **Mistral OCR** bleibt die Text-Engine (93.58% validiert) -- kein Wechsel noetig
3. **Gemini** als optionaler "Schiedsrichter" fuer die Zuordnung Docling-Blocktyp → ZBZ-Tag und fuer Problemfaelle (Typ B Spalten, Typ D Spezial) -- extrem guenstig ($0.20-1.00 fuer 7.200 Seiten)
4. **Claude** nicht fuer Layout, sondern fuer die nachgelagerte TEI-Erzeugung und NER (dort ist es stark)

### Alternativ: Kraken (falls PAGE-XML-Nativitaet hoechste Prioritaet)

Kraken ist das einzige Tool mit nativem PAGE-XML-Export und wurde fuer historische franzoesische Dokumente entwickelt. Nachteil: Trainierbare Klassen erfordern initiale Konfiguration, kleinere Community. Empfohlen als **Fallback** falls die Docling-zu-PAGE-XML-Konvertierung sich als zu fehleranfaellig erweist.

### Ueberraschungsfund: ocr-fileformat (UB Mannheim)

Das Tool `ocr-fileformat` (https://github.com/UB-Mannheim/ocr-fileformat) kann zwischen 30+ OCR-Formaten konvertieren, darunter hOCR ↔ PAGE-XML ↔ ALTO ↔ TEI. Falls wir ein Format haben, koennen wir es zu jedem anderen konvertieren. Das reduziert das Risiko der Format-Entscheidung erheblich.

## Naechster Schritt

**Evaluation an allen 15 Pilot-PDFs:**
1. Docling Layout-Analyse auf alle 383 Seitenbilder laufen lassen
2. Docling-Blocktypen → ZBZ-Tags mappen (Tabelle oben)
3. Ergebnis visuell pruefen: Stimmen die Regionen mit dem Seitenbild ueberein?
4. Bei Problemfaellen (Typ B): Gemini als Alternative testen
5. Entscheidung E19 finalisieren

## Quellen

- Gemini API Docs: https://ai.google.dev/gemini-api/docs/vision, /structured-output, /document-processing
- Gemini Pricing: https://ai.google.dev/pricing
- Mistral OCR 3 Docs: https://docs.mistral.ai/capabilities/document_ai/
- Mistral OCR 3 Blog: https://mistral.ai/news/mistral-ocr-3
- Docling: https://github.com/DS4SD/docling, arXiv:2408.09869, arXiv:2509.11720
- Surya: https://github.com/VikParuchuri/surya
- Kraken: https://github.com/mittagessen/kraken
- PaddleOCR: https://github.com/PaddlePaddle/PaddleOCR
- Azure Document Intelligence: https://learn.microsoft.com/en-us/azure/ai-services/document-intelligence/
- OCR-D: https://github.com/OCR-D, https://ocr-d.de
- ocr-fileformat: https://github.com/UB-Mannheim/ocr-fileformat
- PAGE-XML Schema: https://github.com/PRImA-Research-Lab/PAGE-XML
- DocLayNet: https://github.com/DS4SD/DocLayNet (KDD'22)
- DocLayout-YOLO: https://github.com/opendatalab/DocLayout-YOLO
