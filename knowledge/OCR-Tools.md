# OCR-Tools

Pipeline: **Docling (Layout) + DeepSeek-OCR-2 (Text)** - getrennte Aufgaben.

---

## Architektur

```
PDF → Docling (nur Layout) → DeepSeek-OCR-2 (nur Text) → Markdown → TEI
      └─ do_ocr=False        └─ pro Region oder Seite
```

**Wichtig:** Docling wird **nur für Layout-Analyse** verwendet, nicht für OCR.

---

## DeepSeek-OCR-2

**Modell:** 3B Parameter Vision-Language-Modell
**Rolle:** Texterkennung (OCR)
**Status:** Validiert, 94.4% Genauigkeit bei Typ A

### Systemanforderungen

| Komponente | Minimum | Empfohlen |
|------------|---------|-----------|
| GPU | 8 GB VRAM | 16+ GB VRAM |
| CUDA | 11.8+ | 12.x |
| Python | 3.11+ | 3.12 |

### Performance

| Metrik | Wert |
|--------|------|
| Geschwindigkeit | ~1.6 s/Seite |
| Genauigkeit | 94-97% CER |
| VRAM | 5-8 GB |

### Skript

`scripts/ocr_pipeline.py`

---

## Docling

**Projekt:** IBM Research, Linux Foundation
**Rolle:** Nur Layout-Analyse (Spalten, Regionen, Tabellen)
**Status:** Funktioniert auf Windows (mit Symlink-Warnung)

### Wichtig: Keine OCR mit Docling

Docling's integrierte OCR (RapidOCR) hat **Encoding-Probleme** bei französischem Text:
- `é` wird zu `Ø`
- `ê` wird zu `Œ`
- etc.

**Lösung:** `do_ocr=False` setzen, nur Layout nutzen.

### Installation

```bash
pip install docling
```

### Verwendung (nur Layout)

```python
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.datamodel.base_models import InputFormat

# OCR deaktivieren
pipeline_options = PdfPipelineOptions()
pipeline_options.do_ocr = False

converter = DocumentConverter(
    format_options={
        InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
    }
)

result = converter.convert("dokument.pdf")
# → Koordinaten der Textregionen, keine OCR
```

### Skript

`scripts/extract_layout.py`

---

## Vergleich

| Aspekt | DeepSeek-OCR-2 | Docling (Layout) |
|--------|----------------|------------------|
| Zweck | Texterkennung | Layout-Analyse |
| OCR-Qualität | Sehr gut | Nicht nutzen |
| Layout-Analyse | Gut | Exzellent |
| Spalten | Problematisch | Korrekt erkannt |
| Output | Markdown | JSON (Koordinaten) |

---

## Hybrid-Pipeline

### Dokumenttypen

| Typ | Beschreibung | Pipeline |
|-----|--------------|----------|
| A | Einspaltig | DeepSeek direkt |
| B | Zweispaltig | Docling Layout → DeepSeek pro Region |
| C | Monografie | DeepSeek + Chunking |
| D | Spezial | Fallweise |

### Validiert (29.01.2026)

| Test | Ergebnis |
|------|----------|
| Docling Layout (2530.pdf) | Zweispaltig erkannt, 14 Regionen/Seite |
| DeepSeek OCR (2310.pdf) | 94.4% Genauigkeit |

---

## Troubleshooting

### CUDA prüfen

```python
import torch
print(torch.cuda.is_available())
print(torch.cuda.get_device_name(0))
```

### Out of Memory (DeepSeek)

- `image_size` reduzieren (768 → 512)
- Bilder einzeln verarbeiten
- Andere GPU-Prozesse beenden

### Docling Symlink-Warnung (Windows)

```
UserWarning: `huggingface_hub` cache-system uses symlinks by default...
```

**Status:** Ignorierbar - Docling funktioniert trotzdem.

---

## LLM für komplexe Aufgaben

### Gemini 3 Flash

**Modell:** google/gemini-3.0-flash
**Kosten:** $0.50/1M Input, $3.00/1M Output
**Kontextfenster:** 1M Tokens

| Aufgabe | Beschreibung |
|---------|--------------|
| NER | Personennamen, Orte, Institutionen erkennen |
| Interview-Struktur | Dialog-Markup (`<sp>`, `<speaker>`) |
| OCR-Korrektur | Kontextbasierte Fehlerkorrektur |
| GND-Vorschläge | Entitäts-Kandidaten generieren |

**Strategie:** Regelbasiert für Grundstruktur, LLM nur für komplexe Aufgaben.

---

## Quellen

- [DeepSeek-OCR-2](https://github.com/deepseek-ai/DeepSeek-OCR)
- [Docling](https://github.com/docling-project/docling)
- [Gemini 3 Flash](https://ai.google.dev/gemini-api/docs/gemini-3)

---

*Aktualisiert: 29.01.2026*
