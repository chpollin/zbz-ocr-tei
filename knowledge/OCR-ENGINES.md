---
type: knowledge
created: 2026-01-29
updated: 2026-03-04
tags: [zbz-ocr-tei, ocr, deepseek, mistral, gemini, docling]
status: active
---

# OCR Engines

All OCR tools and their roles in the pipeline. Docling is used exclusively for layout analysis.

**Dependencies:** [PIPELINE](PIPELINE.md)

---

## Overview

| Engine | Access | Parameters | Use Case | Status |
|--------|--------|------------|----------|--------|
| DeepSeek-OCR-2 | Local (GPU) | 3B VLM | Development, Type A | Validated |
| Mistral Document AI | Azure AI Foundry | mistral-document-ai-2512 | Production (ZBZ) | API key available |
| Gemini 3.1 Flash Lite | Google API | gemini-3.1-flash-lite-preview | Layout QA (E25) + Layout Detect (E26) | Production (286/286 docs) |
| Claude | Anthropic/Azure | - | Complex structures, QA | Not tested |
| Docling | Local (GPU/CPU) | IBM Research, RT-DETR V2 | Layout analysis only | Production (286/286 docs, 4,152 pages) |

---

## DeepSeek-OCR-2

| Aspect | Details |
|--------|---------|
| Model | deepseek-ai/DeepSeek-OCR-2 (3B VLM) |
| Hardware | GPU with 8+ GB VRAM, CUDA 12.4+ |
| Accuracy | 94-97% (validated on Type A) |
| Speed | ~1.6 seconds/page (RTX 3070) |
| Use Case | Development, Type A (single-column), Type C (monographs) |

### Prompt Modes (Research 25.02.2026)

`<|grounding|>` activates layout recognition with bounding boxes. Six modes available:

| Mode | Prompt | Use Case |
|------|--------|----------|
| **Document (Default)** | `<image>\n<|grounding|>Convert the document to markdown.` | Type A, B, C — our standard |
| Free OCR | `<image>\nOCR this image.` (without grounding) | Faster, no layout needed |
| Figure Parsing | Special prompt for charts/diagrams | Type D (illustrated books?) |
| Localization | `<image>\nLocate <\|ref\|>{TEXT}<\|/ref\|>` | Not relevant |

**Open:** Test Free OCR (without `<|grounding|>`) for Type A/C — potentially faster without quality loss.

Sources: [DeepSeek-OCR Prompts](https://deepwiki.com/deepseek-ai/DeepSeek-OCR/3.4-working-with-prompts), [HuggingFace Model Card](https://huggingface.co/deepseek-ai/DeepSeek-OCR-2)

### Known Issues

| Issue | Workaround |
|-------|------------|
| High GPU load (PC freezes) | Run tests individually or on cloud VM |
| Column order incorrect for Type B | Layout preprocessing or use Gemini |
| safetensors required | `use_safetensors=True` when loading |

---

## Mistral Document AI (Azure)

| Aspect | Details |
|--------|---------|
| Provider | Azure AI Foundry (Serverless API, Pay-as-you-go) |
| Model | `mistral-document-ai-2512` (Preview, based on mistral-ocr-2512) |
| Previous Version | `mistral-document-ai-2505` (available but superseded) |
| Discontinued | `mistral-ocr-2503` (no longer deployable since 30.01.2026) |
| Endpoint | `/v1/ocr` with Base64-encoded documents |
| Output | Per-page Markdown with image references and dimensions |
| Use Case | Primary production engine (ZBZ has Azure access) |
| Status | API key available, engine implemented |

### Model Versions

| Model | Status | Note |
|-------|--------|------|
| `mistral-document-ai-2512` | Available (Preview) | Current, +74% on scans/tables/handwriting |
| `mistral-document-ai-2505` | Available | First Document AI version |
| `mistral-ocr-2503` | Discontinued (30.01.2026) | No longer deployable |

### Limits

| Parameter | Value |
|-----------|-------|
| Max. file size | 30 MB |
| Max. pages (OCR) | 30 per request |
| Max. pages (Annotations) | 8 per request |
| Input | PDF, PNG, JPEG, TIFF, GIF, WEBP, PPTX, DOCX, TXT, EPUB |
| Output | Markdown (tables optionally as HTML) |
| Languages | 36 (de, fr, en, es, it, nl, pt, hu, pl, cs, zh, ja, ko, ar, ...) |

### Setup on Azure

1. **Create Azure AI Foundry resource** in Azure Portal (portal.azure.com)
2. **Deploy model**: In Foundry Portal (ai.azure.com) under Model Catalog, search for `mistral-document-ai-2512`, deploy as Serverless Endpoint
3. **Retrieve credentials**: Under My Resources > Models and Endpoints — copy Endpoint URL and API Key

**Project configuration:** Enter values in `.env` (see `.env.example`):
```bash
MISTRAL_DOC_AI_ENDPOINT="https://<deployment>.<region>.models.ai.azure.com"
MISTRAL_DOC_AI_KEY="<api-key>"
```

**Supported regions:** East US, East US 2, West US, West US 3, South Central US, North Central US, Sweden Central.

### API Details

**Endpoint:** `POST {endpoint}/v1/ocr` with Bearer token authentication.

**Input:** Documents as Base64 in the `document.document_url` field (format: `data:application/pdf;base64,...`). Direct URLs are not supported on Azure.

**Response structure:** JSON with `pages[]`, each page contains:
- `index` — page number (0-based)
- `markdown` — extracted text
- `images[]` — bounding boxes (and optionally Base64 with `include_image_base64: true`)
- `dimensions` — DPI, height, width

**Large documents (>30 pages):** Pipeline splits automatically with PyMuPDF (`MistralOCR._split_pdf()`).

### Annotations (Structured Extraction)

In addition to OCR, the model can extract content directly into a JSON schema:
- **`bbox_annotation`**: Labels detected image regions (e.g., diagrams)
- **`document_annotation`**: Extracts entire document into a defined JSON format

Annotations are limited to 8 pages. Relevant for: metadata extraction, TEI header generation.

### Error Handling

| Issue | Solution |
|-------|----------|
| 404 after deployment | Append `/v1/ocr` to endpoint URL |
| 413 / file too large | Compress or split PDF (max 30 MB) |
| Timeout on annotations | Set timeout to min. 120s |
| Base64 error | No line breaks in Base64 string |

### Alternative Access Methods

| Access | Model | Advantage |
|--------|-------|-----------|
| Azure AI Foundry | `mistral-document-ai-2512` | Data residency, enterprise governance |
| Mistral API direct (console.mistral.ai) | `mistral-ocr-latest` | Simplest setup, no Azure needed |
| Google Vertex AI | `mistral-ocr-2512` | Google Cloud infrastructure |

### Benchmark and CER/WER Results

All evaluation data (CER, WER, per-document results) are consolidated in [TESTPLAN](TESTPLAN.md) section Results.

Interactive engine comparison in the dashboard: `docs/index.html`

### Configuration Options (Research 25.02.2026)

Mistral OCR does **not accept a custom prompt**. Controllable parameters:

| Parameter | Default | Potential |
|-----------|---------|-----------|
| `table_format` | null | Irrelevant (no tables in corpus) |
| `extract_header` | false | Could filter JSTOR headers — **test** |
| `extract_footer` | false | Could filter copyright lines — **test** |

Sources: [Mistral OCR API Docs](https://docs.mistral.ai/capabilities/document_ai/basic_ocr), [OCR 3 Model Card](https://docs.mistral.ai/models/ocr-3-25-12)

### Open

- [ ] Analyze Doc 290 (CER 18% — scan or OCR issue?) — low priority
- [ ] Analyze Doc 1060 (CER 22.6% — alignment issue with short PDF?) — low priority
- [ ] Test `extract_header/footer` — reduces JSTOR artifacts without LLM?

---

## Gemini 3.1 Flash Lite (Layout QA + Detect)

| Aspect | Details |
|--------|---------|
| QA Model | gemini-3.1-flash-lite-preview (E25) |
| Detect Model | gemini-3.1-flash-lite-preview (E26) |
| SDK | `google-genai` (new SDK) |
| Cost | $0.25/1M Input, $1.50/1M Output |
| Use Case | Layout QA (label correction) + Layout Detect (full re-detection for bad pages) |
| Estimated Cost | ~$3-4 for 4,152 pages (QA + Detect combined) |
| Status | Production (auto mode running on 286 docs) |

### Three Modes (`layout_qa_gemini.py`)

| Mode | Input | Model | Use Case |
|------|-------|-------|----------|
| `--mode qa` | Overlay PNG + Layout JSON | Flash Lite | Label corrections on Docling results |
| `--mode detect` | Raw scan PNG | Flash Lite | Full re-detection for bad/empty pages |
| `--mode auto` | Depends on quality | Flash Lite | Routes by Docling quality score |

**Auto routing:** `compute_page_quality()` classifies pages as good/warning/bad/empty based on bbox coverage. Bad/empty -> detect, good/warning -> qa.

### Model History

| Model | Used for | Period | Note |
|-------|----------|--------|------|
| gemini-3.1-flash-lite-preview | QA + Detect | 04.03.2026+ | Current, ~10x cheaper than 2.5 Flash |
| gemini-2.5-flash | Detect (initial tests) | 04.03.2026 | Equivalent quality, switched to Flash Lite |
| gemini-3.1-flash-lite-preview | QA | 03.03.2026 | First QA runs (E25) |

### Quality Results

- **QA mode:** Score 0-100, average ~70. Catches page numbers, running headers, JSTOR metadata
- **Detect mode:** Doc 510 p7: found 4 regions (vs Docling 2, missing paragraph recovered). Doc 900 p1: found 47 regions (vs Docling 26), rightmost column still missed on wide landscapes

---

## Docling (Layout Only)

| Aspect | Details |
|--------|---------|
| Origin | IBM Research |
| Version | Docling 2.75, RT-DETR V2 Heron (42.9M params) |
| Mode | `do_ocr=False` — layout analysis only |
| Detects | 17 block types: Title, Section-header, Text, Footnote, Caption, Page-header/footer, etc. |
| Output | JSON with bounding box coordinates |
| Speed | ~5s/page (RTX 4060 GPU), ~27s/page (CPU/docling-serve) |
| Status | Production (286/286 docs, 4,152 pages) |
| Quality | 62% good, 20% warning, 13% bad, 3% empty (bbox coverage analysis) |

### Important: Do Not Use Docling OCR

Docling's built-in OCR (RapidOCR) has encoding issues with French text. Example: `e` becomes `O`. Docling is used exclusively for layout analysis.

### Troubleshooting

| Issue | Solution |
|-------|----------|
| Symlink warning on Windows | `HF_HUB_DISABLE_SYMLINKS_WARNING=1` — can be ignored |
| Encoding errors with OCR | Use `do_ocr=False`, OCR via DeepSeek/Mistral |
| CUDA conflict with DeepSeek | Run Docling on CPU (default) |

---

## Comparison Table

| Criterion | DeepSeek | Mistral | Gemini Flash Lite | Docling |
|-----------|----------|---------|-------------------|---------|
| Role | OCR | OCR (production) | Layout QA/Detect | Layout analysis |
| Accuracy (CER) | 94-97% (Phase 1) | 93.58% (15 Docs) | N/A (layout only) | N/A (layout only) |
| GPU required | Yes (8GB+) | No (API) | No (API) | Optional (GPU ~5x faster) |
| Cost | Free | Azure subscription | ~$3-4/project | Free |
| Speed | ~1.6s/page | ~1.3s/page | ~2.4-5s/page | ~5s/page (GPU) |
| Offline | Yes | No | No | Yes |
| Status | Development | Production | Production (286 docs) | Production (286 docs) |

---

## Findings from Pilot Evaluation (15 Docs)

| Finding | Detail | Decision |
|---------|--------|----------|
| Monographs have best CER | Phase 4 (Type C): 2.65% — clean layout, consistent typography | — |
| LLM correction only useful at high CER | Improves CER >10%, worsens CER <5% (corrects away correct proper names/accents) | E17 |
| Per-page comparison for long docs | Global alignment fails above ~50 pages; `<pb facs>` as anchor points | E16 |
| TEI page numbers ≠ PDF page numbers | Cover pages, blank pages shift offset variably; content matching solves this | E18 |
| API costs negligible | 330 pages OCR + LLM = ~$1.55; projection 7200 pages: ~$35 | — |

---

## References

- [PIPELINE](PIPELINE.md) for pipeline integration
- [TESTPLAN](TESTPLAN.md) for quality measurements
- [INFRASTRUKTUR](INFRASTRUKTUR.md) for Azure configuration
- [DECISIONS](DECISIONS.md) for open questions

---

*Created: 2026-01-29 | Updated: 2026-03-04 (Gemini E25/E26, Docling 286/286)*
