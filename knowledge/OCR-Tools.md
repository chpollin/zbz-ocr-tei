# OCR-Tools

Pipeline: **Docling + DeepSeek-OCR-2** für Layout-Analyse und Texterkennung.

---

## Architektur

```
PDF → Docling (Layout-Analyse) → DeepSeek-OCR-2 (Text) → Strukturiertes Markdown → TEI
```

**Docling** analysiert das Layout (Spalten, Tabellen, Regionen) und nutzt **DeepSeek-OCR-2** als OCR-Backend für die Texterkennung.

---

## DeepSeek-OCR-2

**Modell:** 3B Parameter Vision-Language-Modell
**Rolle:** OCR-Engine (Texterkennung)
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

---

## Docling

**Projekt:** IBM Research, Linux Foundation
**Rolle:** Layout-Analyse, Strukturerkennung
**Status:** Windows-Problem (Symlinks), Cloud empfohlen

### Vorteile

- Layout-Segmentierung (Spalten, Regionen)
- Tabellenerkennung
- Strukturierter Markdown-Export
- **DeepSeek-OCR als Backend möglich** via VlmPipeline

### Installation

```bash
pip install docling "docling[vlm]"
```

### Docling + DeepSeek Integration

Docling kann DeepSeek-OCR-2 über die VlmPipeline nutzen:

```python
from docling.document_converter import DocumentConverter
from docling.pipeline.vlm_pipeline import VlmPipeline

# DeepSeek-OCR via vLLM Server (OpenAI-kompatibel)
# Umgebungsvariablen setzen:
# OCR_MODEL="deepseek-ai/DeepSeek-OCR-2"
# OCR_BASE_URL="http://localhost:8000/v1"

converter = DocumentConverter()
result = converter.convert("dokument.pdf")
markdown = result.document.export_to_markdown()
```

---

## Vergleich

| Aspekt | DeepSeek-OCR-2 | Docling | Kombiniert |
|--------|----------------|---------|------------|
| OCR-Qualität | Sehr gut | Engine-abhängig | Sehr gut |
| Layout-Analyse | Gut | Exzellent | Exzellent |
| Spalten | Problematisch | Korrekt | Korrekt |
| Tabellen | Gut | Exzellent | Exzellent |
| Strukturierter Output | Markdown | Markdown/JSON | Markdown |

**Strategie:**
- Docling für Layout-Analyse und Spalten-Handling
- DeepSeek-OCR-2 als OCR-Backend für Texterkennung
- Kombiniert: Beste Qualität für alle Dokumenttypen

---

## Pipeline-Konfiguration

### Dokumenttypen

| Typ | Beschreibung | Pipeline |
|-----|--------------|----------|
| A | Einspaltig | DeepSeek direkt oder via Docling |
| B | Zweispaltig | **Docling + DeepSeek** (zwingend) |
| C | Monografie | Docling + DeepSeek + Chunking |
| D | Spezial | Fallweise |

### Output-Format

Docling exportiert strukturiertes Markdown:

```markdown
# Überschrift

Absatz 1 mit Text...

Absatz 2 mit Text...

| Spalte 1 | Spalte 2 |
|----------|----------|
| Daten    | Daten    |
```

Dieses Markdown wird dann regelbasiert zu TEI transformiert.

---

## Troubleshooting

### CUDA prüfen

```python
import torch
print(torch.cuda.is_available())
print(torch.cuda.get_device_name(0))
```

### Out of Memory

- `image_size` reduzieren (768 → 512)
- Bilder einzeln verarbeiten
- Andere GPU-Prozesse beenden

### Windows Symlink-Fehler (Docling)

```
WinError 1314: A required privilege is not held by the client
```

**Workarounds:**
1. Windows Developer Mode aktivieren (Einstellungen → Entwickler)
2. Cloud-VM mit Linux verwenden (empfohlen für Produktion)

---

## Quellen

- [DeepSeek-OCR-2](https://github.com/deepseek-ai/DeepSeek-OCR)
- [Docling](https://github.com/docling-project/docling)
- [Docling + DeepSeek Discussion](https://github.com/docling-project/docling/discussions/2514)
- [Docling VLM Pipeline](https://docling-project.github.io/docling/)

---

*Aktualisiert: 29.01.2026*
