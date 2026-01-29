# Docling Lokale Installation

Anleitung zur lokalen Ausführung von Docling für Dokumentenverarbeitung und OCR.

**Projekt:** [Docling](https://www.docling.ai/) (IBM Research / Linux Foundation)
**Quellen:** [Dokumentation](https://docling-project.github.io/docling/), [GitHub](https://github.com/docling-project/docling)

---

## Was ist Docling?

Docling ist ein KI-basiertes Dokumentenverarbeitungs-Tool, das:

- **Strukturierte Daten** aus Dokumenten extrahiert (Tabellen, Formeln, Layouts)
- **OCR** für gescannte Dokumente durchführt
- **Lesereihenfolge** automatisch erkennt
- **Export** in Markdown, HTML, JSON, CSV ermöglicht

### Unterstützte Formate

| Kategorie | Formate |
|-----------|---------|
| Dokumente | PDF, Word, PowerPoint, Excel, Markdown, HTML, AsciiDoc, CSV |
| Medien | WebVTT, MP3, WAV |
| Bilder | PNG, JPEG, TIFF, BMP, WEBP |

---

## Systemanforderungen

### Minimum

| Komponente | Anforderung |
|------------|-------------|
| Python | 3.10 - 3.13 |
| OS | Windows, Linux, macOS |
| Architektur | x86_64 oder arm64 |

### Für GPU-Beschleunigung

| Komponente | Anforderung |
|------------|-------------|
| GPU | NVIDIA RTX (40xx/50xx empfohlen) |
| CUDA | 12.8 oder 13.0 |
| VRAM | 8+ GB (mehr = größere Batches) |

### Batch-Größen nach GPU

| GPU | VRAM | Empfohlene Batch Size |
|-----|------|----------------------|
| RTX 5090 | 32 GB | 64-128 |
| RTX 4090 | 24 GB | 32-64 |
| RTX 5070/4070 | 12 GB | 16-32 |
| RTX 3090 | 24 GB | 32-64 |

---

## Installation

### Basis-Installation

```bash
pip install docling
```

### Mit GPU-Unterstützung (CUDA)

```bash
# PyTorch mit CUDA installieren
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128

# Docling installieren
pip install docling
```

### Mit OCR-Engines

```bash
# Verschiedene OCR-Backends verfügbar
pip install "docling[easyocr]"      # EasyOCR
pip install "docling[tesserocr]"    # Tesseract
pip install "docling[rapidocr]"     # RapidOCR (GPU-fähig mit PyTorch)
pip install "docling[ocrmac]"       # macOS native OCR
```

### Alle Extras

```bash
pip install "docling[asr,vlm,easyocr,rapidocr]"
```

### Linux CPU-Only

```bash
pip install docling --extra-index-url https://download.pytorch.org/whl/cpu
```

### macOS Intel

```bash
pip install "docling[mac_intel]"
# Oder manuell:
pip install torch==2.2.2 torchvision==0.17.2 docling
```

---

## Verwendung

### Kommandozeile

```bash
# PDF konvertieren
docling dokument.pdf

# URL verarbeiten
docling https://arxiv.org/pdf/2408.09869
```

### Python API (Einfach)

```python
from docling.document_converter import DocumentConverter

# Konverter erstellen
converter = DocumentConverter()

# Dokument verarbeiten
result = converter.convert("dokument.pdf")
doc = result.document

# Export
print(doc.export_to_markdown())
```

### Python API (Mit GPU)

```python
from docling.document_converter import DocumentConverter
from docling.datamodel.accelerator_options import AcceleratorDevice, AcceleratorOptions
from docling.datamodel.pipeline_options import ThreadedPdfPipelineOptions

# GPU-Beschleunigung konfigurieren
accelerator_options = AcceleratorOptions(
    device=AcceleratorDevice.CUDA  # NVIDIA GPU verwenden
)

# Pipeline für GPU optimieren
pipeline_options = ThreadedPdfPipelineOptions(
    ocr_batch_size=64,      # Standard: 4
    layout_batch_size=64,   # Standard: 4
    table_batch_size=4
)

# Konverter mit GPU-Einstellungen
converter = DocumentConverter(
    accelerator_options=accelerator_options,
    pipeline_options=pipeline_options
)

result = converter.convert("dokument.pdf")
print(result.document.export_to_markdown())
```

### Mit RapidOCR (GPU-fähig)

```python
from docling.document_converter import DocumentConverter
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.plugins.ocr.rapid_ocr_options import RapidOcrOptions

# RapidOCR mit PyTorch-Backend (GPU)
pipeline_options = PdfPipelineOptions()
pipeline_options.ocr_options = RapidOcrOptions(backend="torch")

converter = DocumentConverter(pipeline_options=pipeline_options)
result = converter.convert("scan.pdf")
```

### Full-Page OCR erzwingen

```python
from docling.datamodel.pipeline_options import EasyOcrOptions

ocr_options = EasyOcrOptions(
    force_full_page_ocr=True,
    use_gpu=True
)
```

---

## VLM Pipeline (Fortgeschritten)

Für beste GPU-Nutzung mit Vision Language Models:

### vLLM Server starten (Linux)

```bash
vllm serve ibm-granite/granite-docling-258M \
  --host 127.0.0.1 --port 8000 \
  --max-num-seqs 512 \
  --max-num-batched-tokens 8192 \
  --enable-chunked-prefill \
  --gpu-memory-utilization 0.9
```

### Docling mit VLM konfigurieren

```python
from docling.datamodel.pipeline_options import VlmPipelineOptions
from docling.datamodel.settings import settings

vlm_options = VlmPipelineOptions(
    enable_remote_services=True,
    vlm_options={
        "url": "http://localhost:8000/v1/chat/completions",
        "params": {
            "model": "ibm-granite/granite-docling-258M",
            "max_tokens": 4096
        },
        "concurrency": 64,
        "timeout": 90
    }
)

settings.perf.page_batch_size = 64  # >= concurrency
```

### Unterstützte Inference Server

| Server | URL | Plattform |
|--------|-----|-----------|
| vLLM | `http://localhost:8000/v1/chat/completions` | Linux |
| LM Studio | `http://localhost:1234/v1/chat/completions` | Linux, Windows |
| Ollama | `http://localhost:11434/v1/chat/completions` | Linux, Windows |
| llama-server | - | Windows (empfohlen) |

---

## Export-Formate

```python
doc = result.document

# Markdown
markdown = doc.export_to_markdown()

# HTML
html = doc.export_to_html()

# JSON
json_data = doc.export_to_json()

# Text
text = doc.export_to_text()

# Doctags (für ML)
doctags = doc.export_to_doctags()
```

---

## Performance

### Benchmarks

| Metrik | CPU | GPU (RTX) |
|--------|-----|-----------|
| Speedup | 1x | **bis zu 6x** |
| VLM Performance | - | **4x** (vLLM vs llama-server) |

### Optimierungstipps

1. **Batch-Größe erhöhen** für GPU (64 statt 4)
2. **RapidOCR mit torch-Backend** für GPU-OCR
3. **vLLM Server** für VLM-Workloads (Linux)
4. **Concurrent Processing** aktivieren

---

## Troubleshooting

### CUDA prüfen

```python
import torch
print(f"PyTorch: {torch.__version__}")
print(f"CUDA verfügbar: {torch.cuda.is_available()}")
print(f"CUDA Version: {torch.version.cuda}")
print(f"GPU: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'Keine'}")
```

### PyTorch neu installieren

```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128 --force-reinstall
```

### Modelle herunterladen

Docling lädt automatisch Modelle herunter:
- Layout Model
- Tableformer Model
- Picture Classifier
- Code/Formula Model
- EasyOCR Models

Cache-Pfad: `~/.cache/docling/`

---

## Relevanz für ZBZ-Projekt

### Vorteile für Hersch-Edition

| Feature | Nutzen |
|---------|--------|
| **Tabellen-Erkennung** | Strukturierte Extraktion aus Lexikonartikeln |
| **Layout-Analyse** | Erkennung von Fußnoten, Spalten, Marginalien |
| **Markdown-Export** | Direkt weiterverarbeitbar für TEI-Konvertierung |
| **Batch-Verarbeitung** | Effizient für 289 Texte |
| **Multi-Format** | PDF, Bilder, gescannte Dokumente |

### Vergleich mit DeepSeek-OCR-2

| Aspekt | Docling | DeepSeek-OCR-2 |
|--------|---------|----------------|
| Fokus | Dokumentstruktur | OCR-Qualität |
| Tabellen | Exzellent | Gut |
| Formeln | Ja | Begrenzt |
| Geschwindigkeit | Schneller (6x mit GPU) | ~1.6s/Seite |
| Integration | Mehr Export-Optionen | Markdown |
| Setup | Einfacher | Komplexer |

### Empfehlung

**Docling** für strukturierte Dokumente (Lexikonartikel, Tabellen).
**DeepSeek-OCR-2** für reine Fließtexte mit komplexer Typografie.

Beide können kombiniert werden: Docling für Layout → DeepSeek für OCR-Nachbesserung.

---

## Quellen

- [Docling Website](https://www.docling.ai/)
- [Docling Dokumentation](https://docling-project.github.io/docling/)
- [GPU Support](https://docling-project.github.io/docling/usage/gpu/)
- [RTX Guide](https://docling-project.github.io/docling/getting_started/rtx/)
- [Installation](https://docling-project.github.io/docling/getting_started/installation/)
- [RapidOCR Integration](https://dev.to/aairom/using-doclings-ocr-features-with-rapidocr-29hd)
- [Codecademy Guide](https://www.codecademy.com/article/docling-ai-a-complete-guide-to-parsing)

---

*Erstellt: 29.01.2026*
