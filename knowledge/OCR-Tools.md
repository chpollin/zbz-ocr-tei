# OCR-Tools

Zwei Optionen für die OCR-Stufe der Pipeline.

---

## DeepSeek-OCR-2 (primär)

**Modell:** 3B Parameter Vision-Language-Modell
**Status:** Getestet, funktioniert

### Systemanforderungen

| Komponente | Minimum | Empfohlen |
|------------|---------|-----------|
| GPU | 8 GB VRAM | 16+ GB VRAM |
| CUDA | 11.8+ | 12.x |
| Python | 3.11+ | 3.12 |

### Installation (Windows)

```bash
# Projekt venv
python -m venv .venv
.venv\Scripts\activate

# PyTorch mit CUDA
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu124

# Abhängigkeiten
pip install transformers accelerate pypdfium2
```

### Verwendung

```python
from transformers import AutoModel, AutoTokenizer
import torch

model = AutoModel.from_pretrained('deepseek-ai/DeepSeek-OCR-2', trust_remote_code=True)
model = model.eval().cuda().to(torch.bfloat16)
tokenizer = AutoTokenizer.from_pretrained('deepseek-ai/DeepSeek-OCR-2', trust_remote_code=True)

# OCR
model.infer(tokenizer,
    prompt="<image>\n<|grounding|>Convert the document to markdown.",
    image_file="seite.png",
    output_path="./output",
    crop_mode=True)
```

### Performance

| Metrik | Wert |
|--------|------|
| Geschwindigkeit | ~1.6 s/Seite |
| Genauigkeit | 95-97% CER |
| VRAM | 5-8 GB |

---

## Docling (Alternative)

**Projekt:** IBM Research, Linux Foundation
**Status:** Noch nicht getestet

### Vorteile

- Modulare Pipeline (Layout → Tabellen → OCR)
- Bessere Strukturerkennung
- Wählbare OCR-Engine (Tesseract, EasyOCR, RapidOCR)

### Installation

```bash
pip install docling
pip install "docling[easyocr]"  # Mit OCR
```

### Verwendung

```python
from docling.document_converter import DocumentConverter

converter = DocumentConverter()
result = converter.convert("dokument.pdf")
print(result.document.export_to_markdown())
```

---

## Vergleich

| Aspekt | DeepSeek-OCR-2 | Docling |
|--------|----------------|---------|
| Architektur | Monolithisches VLM | Modulare Pipeline |
| OCR-Qualität | Sehr gut | Gut (Engine-abhängig) |
| Layout-Analyse | Gut | Sehr gut |
| Tabellen | Gut | Exzellent |
| Spalten-Erkennung | **Problematisch** | Besser |
| Setup | Komplexer | Einfacher |

**Empfehlung:**
- **DeepSeek** für einspaltige Fließtexte
- **Docling** für zweispaltige Layouts und Tabellen

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

---

## Quellen

- [DeepSeek-OCR-2](https://github.com/deepseek-ai/DeepSeek-OCR-2)
- [Docling](https://github.com/docling-project/docling)
- [Docling GPU Guide](https://docling-project.github.io/docling/usage/gpu/)

---

*Aktualisiert: 29.01.2026*
