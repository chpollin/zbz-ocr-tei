---
type: knowledge
created: 2026-01-29
updated: 2026-02-18
tags: [zbz-ocr-tei, architektur, pipeline, workflow]
status: active
---

# Architektur

Technische Pipeline-Architektur: 5 Stufen von PDF zu TEI-XML.

**Abhängigkeiten:** [PROJEKT](PROJEKT.md)

---

## Pipeline-Übersicht

```
PDF --> Docling (Layout) --> OCR Engine --> Markdown --> Post-Processing --> TEI-XML --> [GND]
        output/layout/       output/ocr_results/          output/clean/      output/tei/
```

### 5 Stufen

| Stufe | Aufgabe | Tool | Output |
|-------|---------|------|--------|
| 1 | Layout-Analyse | Docling (do_ocr=False) | JSON mit BBox-Koordinaten |
| 2 | OCR | DeepSeek / Mistral / Gemini | Seitenweises Markdown |
| 3 | Post-Processing | `scripts/postprocess/` | Bereinigtes Markdown |
| 4 | TEI-Transformation | `scripts/transform_to_tei.py` | TEI-XML |
| 5 | Validierung | lxml, RelaxNG (geplant) | Validierte TEI-XML |

---

## Stufe 1: Layout-Analyse (Docling)

**Skript:** `scripts/extract_layout.py`

| Aspekt | Details |
|--------|---------|
| Tool | Docling (IBM) |
| Modus | `do_ocr=False` |
| Output | JSON mit BBox-Koordinaten pro Region |
| Erkennt | Spalten, Header, Text, Listen, Tabellen |

Validiert: 2530.pdf — zweispaltig erkannt, 14 Regionen pro Seite.

**Wichtig:** Docling OCR nicht nutzen (RapidOCR hat Encoding-Probleme). Details: [OCR-ENGINES](OCR-ENGINES.md) §Docling.

---

## Stufe 2: OCR

**Skript:** `scripts/ocr_pipeline.py`

### Engine-Auswahl nach Dokumenttyp

Dokumenttypen: Siehe [QUELLENANALYSE](QUELLENANALYSE.md) §Dokumenttypen.

| Typ | Pipeline | Engine |
|-----|----------|--------|
| A (einspaltig) | OCR direkt | DeepSeek / Mistral |
| B (zweispaltig) | Layout + OCR pro Region, oder Agentic Vision | Docling + DeepSeek, oder Gemini |
| C (Monografie) | OCR + Chunking | DeepSeek / Mistral |
| D (Spezial) | Fallweise | Gemini Agentic Vision |

Engine-Details: Siehe [OCR-ENGINES](OCR-ENGINES.md).

### OCR-Qualität (gemessen)

Vollständige Ergebnisse: Siehe [TESTPLAN](TESTPLAN.md) §Ergebnisse.

| Dokument | Typ | CER | Genauigkeit |
|----------|-----|-----|-------------|
| 2310 | A | 2.67% | 97.33% |
| 1180 | A | 4.89% | 95.11% |
| 290 | A | 9.21% | 90.79% |

---

## Stufe 3: Post-Processing

**Implementiert in:** `scripts/postprocess/`

| Schritt | Funktion | Beispiel |
|---------|----------|----------|
| 1. Markdown entfernen | `clean_markdown()` | `## Titel` -> `Titel` |
| 2. Zeichen normalisieren | `normalize_text()` | typografische Varianten vereinheitlichen |
| 3. Silbentrennung | `dehyphenate()` | `Wis- senschaft` -> `Wissenschaft` |
| 4. Whitespace | (inline) | Mehrfache Leerzeilen -> eine |

**Bekanntes Problem:** Markdown-Formatierung (`**bold**`, `*italic*`) wird entfernt, bevor sie in TEI-`<hi>`-Tags umgewandelt werden kann. Architektur-Fix nötig (-> [DECISIONS](DECISIONS.md) R6).

---

## Stufe 4: TEI-Transformation

**Skript:** `scripts/transform_to_tei.py`
**Ansatz:** Regelbasiert (deterministisch), LLM nur für komplexe Strukturen

### Regelbasierte Transformation

| Input (Markdown) | Output (TEI) |
|------------------|--------------|
| Leere Zeile | `</p><p>` (Absatztrennung) |
| `# Überschrift` | `<head>` |
| Erster Absatz (Rezension) | `<head><bibl>` |
| Bekannte Namen | `<persName ref="GND:...">` |

### LLM-Unterstützung (geplant)

| Aufgabe | Engine |
|---------|--------|
| NER (Named Entity Recognition) | Gemini 3 Flash |
| Interview-Strukturierung (`<sp>`, `<speaker>`) | Gemini 3 Flash |
| OCR-Korrektur | Gemini 3 Flash |
| GND-Vorschläge | Gemini 3 Flash |
| Qualitätssicherung | Claude |

**Kosten:** ~$20-27 für 289 Dokumente (7.200 Seiten). Details: [OCR-ENGINES](OCR-ENGINES.md) §Gemini.

TEI-Regeln: Siehe [TEI-MAPPING](TEI-MAPPING.md).

---

## Stufe 5: Validierung

| Prüfung | Tool | Status |
|---------|------|--------|
| XML-Wohlgeformtheit | lxml | Zu implementieren |
| TEI P5 Schema | RelaxNG | Zu implementieren |
| Seitenzählung | Custom | Zu implementieren |
| GND-Format | Regex `ref="GND:\d+"` | Zu implementieren |

---

## CLI-Befehle

```bash
# Layout-Extraktion (ohne GPU)
python scripts/extract_layout.py --input data/scans/2530.pdf --visualize

# OCR Pipeline (GPU erforderlich)
python scripts/ocr_pipeline.py --input data/scans/2310.pdf
python scripts/ocr_pipeline.py --all --engine auto

# Post-Processing (ohne GPU)
python -m scripts.postprocess.pipeline

# TEI Transformation
python scripts/transform_to_tei.py --doc 2310 --type review --add-gnd

# Evaluation
python scripts/evaluate_ocr.py --all
```

---

## Referenzen

- [PROJEKT](PROJEKT.md) für Ökosystem und Meilensteine
- [OCR-ENGINES](OCR-ENGINES.md) für Engine-Details
- [TEI-MAPPING](TEI-MAPPING.md) für Transformationsregeln
- [TESTPLAN](TESTPLAN.md) für Testergebnisse
- [INFRASTRUKTUR](INFRASTRUKTUR.md) für Deployment

---

*Erstellt: 2026-01-29 | Aktualisiert: 2026-02-18*
