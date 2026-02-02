# Pipeline: OCR → Post-Processing → TEI

## Architektur

```
PDF → Docling (Layout) → DeepSeek (OCR) → Markdown → Post-Processing → TEI-XML → [GND]
      └─ output/layout/  └─ output/ocr_results/     └─ output/clean/   └─ output/tei/
```

## Stufe 1: Layout-Analyse (Docling)

**Skript:** `scripts/extract_layout.py`
**Zweck:** Nur Layout-Erkennung, keine OCR

```
PDF → Docling (do_ocr=False) → JSON mit Koordinaten
```

| Aspekt | Details |
|--------|---------|
| Tool | Docling (IBM) |
| Modus | `do_ocr=False` |
| Output | JSON mit BBox-Koordinaten pro Region |
| Erkennt | Spalten, Header, Text, Listen, Tabellen |

### Validiert (29.01.2026)

| PDF | Seiten | Spalten | Regionen |
|-----|--------|---------|----------|
| 2530.pdf | 2 | Zweispaltig erkannt | 14 pro Seite |

**Wichtig:** Docling OCR nicht nutzen (RapidOCR hat Encoding-Probleme bei französischem Text).

---

## Stufe 2: OCR (DeepSeek-OCR-2)

**Skript:** `scripts/ocr_pipeline.py`
**Zweck:** Texterkennung mit hoher Genauigkeit

| Aspekt | Details |
|--------|---------|
| Modell | DeepSeek-OCR-2 (3B VLM) |
| Hardware | GPU mit 8+ GB VRAM |
| Genauigkeit | 94-97% (validiert) |

### Engine-Auswahl nach Dokumenttyp

| Typ | Beschreibung | Pipeline |
|-----|--------------|----------|
| A | Einspaltig | DeepSeek direkt |
| B | Zweispaltig | Docling Layout → DeepSeek pro Region |
| C | Monografie | DeepSeek + Chunking |
| D | Spezial | Fallweise |

### OCR-Qualität (gemessen)

| Dokument | Typ | CER | Genauigkeit |
|----------|-----|-----|-------------|
| 2310 | Einspaltig | 2.67% | 97.33% |
| 1180 | Einspaltig | 4.89% | 95.11% |
| 290 | Einspaltig | 9.21% | 90.79% |
| 2530 | Zweispaltig | - | Layout validiert |

---

## Stufe 3: Post-Processing

**Implementiert in:** `scripts/postprocess/`

### Transformationen

| Schritt | Funktion | Beispiel |
|---------|----------|----------|
| 1. Markdown entfernen | `clean_markdown()` | `## Titel` → `Titel` |
| 2. Zeichen normalisieren | `normalize_text()` | `„"` → `""` |
| 3. Silbentrennung | `dehyphenate()` | `Wis- senschaft` → `Wissenschaft` |
| 4. Whitespace | (inline) | Mehrfache Leerzeilen → eine |

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

### LLM-Unterstützung (Gemini 3 Flash)

**Modell:** Gemini 3 Flash (google/gemini-3.0-flash)
**Kosten:** $0.50/1M Input-Tokens, $3.00/1M Output-Tokens
**Geschätzte Projektkosten:** ~$20 für 289 Dokumente (7.200 Seiten)

| Aufgabe | Einsatz |
|---------|---------|
| NER (Named Entity Recognition) | Personennamen, Orte, Werke erkennen |
| Interview-Strukturierung | `<sp>` mit `<speaker>` für Dialoge |
| OCR-Korrektur | Kontextbasierte Fehlerkorrektur |
| GND-Vorschläge | Kandidaten für Entitäten generieren |
| Qualitätssicherung | Strukturprüfung nach Transformation |

**Wichtig:** LLM nur für komplexe Aufgaben, Grundstruktur bleibt regelbasiert (deterministisch).

### Agentic Vision (Typ B, D)

**Neu seit 27.01.2026:** Gemini 3 Flash kann Bilder aktiv manipulieren.

**Think-Act-Observe Loop:**
1. **Think**: Analysiert Bild, plant Schritte
2. **Act**: Generiert Python-Code (Crop, Zoom, Rotate)
3. **Observe**: Validiert eigenes Ergebnis, iteriert bei Bedarf

| Fahigkeit | Nutzen fur Projekt |
|-----------|-------------------|
| Auto-Crop Spalten | Typ B ohne Docling-Vorverarbeitung |
| Selbstvalidierung | 5-10% Qualitatsboost |
| BBox-Output | `<facsimile>` Koordinaten fur TEI |
| Iteratives Zoomen | Historische Drucke, kleine Schrift |

**Empfohlene Strategie:**

| Dokumenttyp | Pipeline |
|-------------|----------|
| Typ A (einspaltig) | DeepSeek-OCR-2 (lokal, kostenlos) |
| Typ B (zweispaltig) | Gemini 3 Agentic Vision |
| Typ C (Monografie) | DeepSeek + Chunking |
| Typ D (Spezial) | Gemini 3 Agentic Vision |

**Kosten:** ~$27 gesamt (statt ~$20 nur fur NER)

---

## Stufe 5: Validierung

| Prüfung | Tool |
|---------|------|
| XML-Wohlgeformtheit | lxml |
| TEI P5 Schema | RelaxNG |
| Seitenzählung | Custom |
| GND-Format | Regex `ref="GND:\d+"` |

---

## CLI-Befehle

```bash
# Layout-Extraktion (ohne GPU)
python scripts/extract_layout.py --input data/scans/2530.pdf --visualize

# OCR Pipeline (GPU erforderlich)
python scripts/ocr_pipeline.py --input data/scans/2310.pdf
python scripts/ocr_pipeline.py --all --engine auto

# TEI Transformation
python scripts/transform_to_tei.py --doc 2310 --type review --add-gnd

# Evaluation
python scripts/evaluate_ocr.py --all
```

---

## Risiken

| Risiko | Status | Mitigation |
|--------|--------|------------|
| Spalten-Reihenfolge (Typ B) | Gelöst | Docling Layout-Extraktion |
| Docling OCR Encoding | Gelöst | Docling nur für Layout |
| GND-Verknüpfung | Offen | Nachgelagert, lobid.org API |
| Historische Drucke | Offen | Beide Engines testen |

---

## Offene Punkte

→ Siehe [journal.md](journal.md#offene-punkte)

---

*Aktualisiert: 02.02.2026*
