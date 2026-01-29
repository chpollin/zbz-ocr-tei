# DeepSeek-OCR-2 Lokale Installation

Anleitung zur lokalen Ausführung von DeepSeek-OCR-2 auf einer NVIDIA GPU (Windows/Linux).

**Modell:** DeepSeek-OCR-2 (3B Parameter, "Visual Causal Flow")
**Release:** 27. Januar 2026
**Quellen:** [GitHub](https://github.com/deepseek-ai/DeepSeek-OCR-2), [Dev.to Guide](https://dev.to/czmilo/deepseek-ocr-2-complete-guide-to-running-fine-tuning-in-2026-3odb)

---

## Systemanforderungen

### Minimum

| Komponente | Anforderung |
|------------|-------------|
| GPU | NVIDIA mit Compute Capability 6.0+ |
| VRAM | 8 GB (16 GB empfohlen) |
| CUDA | 11.8 |
| Python | 3.12.x |
| RAM | 16 GB |
| Speicher | 10-15 GB frei |

### Empfohlen

| Komponente | Empfehlung |
|------------|------------|
| GPU | RTX 3090 / RTX 4090 (24 GB VRAM) |
| CUDA | 11.8 oder 12.1 |
| OS | Ubuntu 22.04/24.04 (Linux) oder Windows 10/11 |

### GPU-Kompatibilität

| GPU-Serie | Status | Hinweis |
|-----------|--------|---------|
| RTX 40xx | Exzellent | Beste Performance |
| RTX 30xx | Exzellent | Primäre Testplattform |
| RTX 20xx / GTX 16xx | Gut | Funktioniert zuverlässig |
| GTX 10xx | Möglich | Langsamer |
| Älter als GTX 900 | Nicht unterstützt | - |

---

## Installation (Linux - Empfohlen)

### 1. Repository klonen

```bash
git clone https://github.com/deepseek-ai/DeepSeek-OCR-2.git
cd DeepSeek-OCR-2
```

### 2. Conda-Umgebung erstellen

```bash
conda create -n deepseek-ocr2 python=3.12.9 -y
conda activate deepseek-ocr2
```

### 3. PyTorch mit CUDA installieren

```bash
pip install torch==2.6.0 torchvision==0.21.0 torchaudio==2.6.0 --index-url https://download.pytorch.org/whl/cu118
```

### 4. vLLM installieren

Download der vLLM-Wheel von den [offiziellen Releases](https://github.com/vllm-project/vllm/releases):

```bash
pip install vllm-0.8.5+cu118-cp38-abi3-manylinux1_x86_64.whl
```

### 5. Weitere Abhängigkeiten

```bash
pip install -r requirements.txt
pip install flash-attn==2.7.3 --no-build-isolation
```

---

## Installation (Windows)

### Option A: Native Windows mit CUDA

```bash
git clone https://github.com/oscar-o-oneill/deepseek-ocr-windows.git
cd deepseek-ocr-windows
pip install -r requirements.txt
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
pip install -U "huggingface_hub[cli]"
hf download deepseek-ai/DeepSeek-OCR-2
```

**Quelle:** [deepseek-ocr-windows](https://github.com/oscar-o-oneill/deepseek-ocr-windows)

### Option B: Universal Version (Cross-Platform)

Für maximale Kompatibilität (CPU, CUDA, MPS):

```bash
git clone https://github.com/Dogacel/Universal-DeepSeek-OCR-2.git
cd Universal-DeepSeek-OCR-2
conda create -n deepseek-ocr2 python=3.12.9 -y
conda activate deepseek-ocr2
pip install -r requirements.txt
pip install torch==2.6.0 --index-url https://download.pytorch.org/whl/cu118
```

**Quelle:** [Universal-DeepSeek-OCR-2](https://github.com/Dogacel/Universal-DeepSeek-OCR-2)

---

## Verwendung

### Transformers API (Einfach)

```python
from transformers import AutoModel, AutoTokenizer
import torch
import os

os.environ["CUDA_VISIBLE_DEVICES"] = '0'
model_name = 'deepseek-ai/DeepSeek-OCR-2'

tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
model = AutoModel.from_pretrained(
    model_name,
    _attn_implementation='flash_attention_2',
    trust_remote_code=True,
    use_safetensors=True
)
model = model.eval().cuda().to(torch.bfloat16)

# OCR durchführen
prompt = "<image>\n<|grounding|>Convert the document to markdown."
image_file = 'dokument.jpg'
output_path = './output'

res = model.infer(
    tokenizer,
    prompt=prompt,
    image_file=image_file,
    output_path=output_path,
    base_size=1024,
    image_size=768,
    crop_mode=True,      # "Gundam mode" - optimal für komplexe Layouts
    save_results=True
)
```

### vLLM Server (Produktion)

```bash
vllm serve deepseek-ai/DeepSeek-OCR-2 \
  --host 0.0.0.0 \
  --port 8000 \
  --logits_processors vllm.model_executor.models.deepseek_ocr:NGramPerReqLogitsProcessor \
  --no-enable-prefix-caching \
  --mm-processor-cache-gb 0 \
  --max-model-len 16384 \
  --gpu-memory-utilization 0.9
```

### Batch-Verarbeitung

```bash
cd DeepSeek-OCR2-vllm
# config.py anpassen (Input/Output-Pfade)
python run_dpsk_ocr2_pdf.py      # PDF-Verarbeitung
python run_dpsk_ocr2_image.py    # Einzelbilder
python run_dpsk_ocr2_eval_batch.py  # Batch-Evaluation
```

---

## Prompts

| Anwendung | Prompt |
|-----------|--------|
| Dokument → Markdown | `<image>\n<|grounding|>Convert the document to markdown.` |
| Einfache OCR | `<image>\nFree OCR.` |

---

## Performance

### Benchmarks (RTX 3090/4090)

| Metrik | Wert |
|--------|------|
| Verarbeitungszeit | ~1.6 Sekunden/Seite |
| Genauigkeit | 97-98% |
| VRAM-Nutzung | 5-8 GB (Inferenz) |
| Durchsatz | 60-120 Dokumente/Stunde |
| Max. Durchsatz (optimiert) | 200.000+ Seiten/Tag |

### Parameter-Optimierung

| Parameter | Standard | Für weniger VRAM |
|-----------|----------|------------------|
| `base_size` | 1024 | 768 |
| `image_size` | 768 | 512-640 |
| `crop_mode` | True | True |

---

## Troubleshooting

### CUDA nicht verfügbar

```bash
# Prüfen
python -c "import torch; print(torch.cuda.is_available())"
nvidia-smi

# Neu installieren
pip install torch==2.6.0 --index-url https://download.pytorch.org/whl/cu118 --force-reinstall
```

### Out of Memory (OOM)

1. `image_size` reduzieren (768 → 512)
2. Andere GPU-Prozesse beenden
3. Bilder sequentiell statt parallel verarbeiten
4. `--quality small` Flag verwenden (Windows-Version)

### Modell nicht gefunden

```bash
pip install -U "huggingface_hub[cli]"
hf download deepseek-ai/DeepSeek-OCR-2
```

Cache-Pfad Windows: `C:\Users\<USERNAME>\.cache\huggingface\hub\`

---

## Quantisierung (für weniger VRAM)

Für GPUs mit weniger VRAM können quantisierte Versionen verwendet werden:

| Quantisierung | VRAM-Reduktion | Genauigkeitsverlust |
|---------------|----------------|---------------------|
| FP16 (Standard) | - | - |
| INT8 | ~30% | Minimal |
| INT4 | ~60% | Gering |

**Hinweis:** DeepSeek-OCR-2 mit 3B Parametern läuft auch ohne Quantisierung auf 24 GB GPUs problemlos.

---

## Relevanz für ZBZ-Projekt

### Vorteile für Hersch-Edition

- **Hohe Genauigkeit** (97-98%) für französische und deutsche Texte
- **Layout-Erkennung** durch "Visual Causal Flow" – versteht Fußnoten, Spalten, Tabellen
- **Markdown-Output** – direkt weiterverarbeitbar für TEI-Konvertierung
- **Lokale Verarbeitung** – kein Cloud-Upload urheberrechtlich geschützter Texte

### Empfohlene Konfiguration für ZBZ

```python
# Für Hersch-PDFs optimiert
prompt = "<image>\n<|grounding|>Convert the document to markdown."
base_size = 1024
image_size = 768
crop_mode = True  # Wichtig für Fußnoten und mehrspaltige Layouts
```

---

## Quellen

- [DeepSeek-OCR-2 GitHub](https://github.com/deepseek-ai/DeepSeek-OCR-2)
- [Universal-DeepSeek-OCR-2](https://github.com/Dogacel/Universal-DeepSeek-OCR-2)
- [Windows-Version](https://github.com/oscar-o-oneill/deepseek-ocr-windows)
- [RTX 4090 Benchmarks](https://github.com/LumiVerseHR/deepseek-ocr)
- [Complete Guide 2026](https://dev.to/czmilo/deepseek-ocr-2-complete-guide-to-running-fine-tuning-in-2026-3odb)
- [GPU Requirements](https://sparkco.ai/blog/deepseek-ocr-gpu-requirements-a-comprehensive-guide)

---

*Erstellt: 29.01.2026*
