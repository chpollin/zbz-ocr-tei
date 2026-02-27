---
type: knowledge
created: 2026-01-29
updated: 2026-02-27
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
| Gemini 3 Flash | Google API | - | Type B/D (Agentic Vision), NER | Not tested for OCR; evaluated as optional layout validator (E19) |
| Claude | Anthropic/Azure | - | Complex structures, QA | Not tested |
| Docling | Local (CPU) | IBM Research | Layout analysis only | Validated |

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

## Gemini 3 Flash

| Aspect | Details |
|--------|---------|
| Model | google/gemini-3.0-flash |
| Cost | $0.50/1M Input, $3.00/1M Output |
| Use Case | Type B/D (Agentic Vision), NER, OCR correction, QA |
| Estimated Cost | ~$27 for 289 documents |

### Agentic Vision (since 27.01.2026)

Think-Act-Observe loop for active image manipulation:

1. **Think**: Analyzes image, plans steps
2. **Act**: Generates Python code (crop, zoom, rotate)
3. **Observe**: Validates own result, iterates if needed

| Capability | Benefit |
|------------|---------|
| Auto-crop columns | Type B without Docling preprocessing |
| Self-validation | 5-10% quality boost |
| BBox output | `<facsimile>` coordinates for TEI |
| Iterative zooming | Historical prints, small font |

### Recommended Strategy by Document Type

Document types: See [QUELLENANALYSE](QUELLENANALYSE.md) section Document Types.

| Type | Engine |
|------|--------|
| A (single-column) | DeepSeek-OCR-2 / Mistral Document AI (local/free or Azure) |
| B (two-column) | Gemini 3 Agentic Vision |
| C (monograph) | DeepSeek / Mistral Document AI + chunking |
| D (special) | Gemini 3 Agentic Vision |

### Still To Do

- [ ] Obtain API key for Gemini
- [ ] Test Agentic Vision on 2530.pdf (Type B)
- [ ] Compare quality vs. DeepSeek
- [ ] Implement engine class `GeminiOCR` in `ocr_pipeline.py`

---

## Docling (Layout Only)

| Aspect | Details |
|--------|---------|
| Origin | IBM Research |
| Mode | `do_ocr=False` — layout analysis only |
| Detects | Columns, headers, text, lists, tables |
| Output | JSON with bounding box coordinates |
| Status | Validated (Windows, with symlink warning) |

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

| Criterion | DeepSeek | Mistral | Gemini | Docling |
|-----------|----------|---------|--------|---------|
| Accuracy (CER) | 94-97% (Phase 1) | 93.58% (15 Docs) | Untested | Layout only |
| GPU required | Yes (8GB+) | No (API) | No (API) | No (CPU) |
| Cost | Free | Azure subscription | ~$27/project | Free |
| Columns (Type B) | No | 93.69% accuracy | Yes (Agentic) | Yes (layout) |
| Speed | ~1.6s/page | ~1.3s/page | Untested | ~3s/page |
| Offline | Yes | No | No | Yes |
| Italic/formatting | No | Yes (*italics*) | Untested | - |
| All pages | Partial (GPU limit) | Yes (Cloud) | Untested | - |

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
- [DECISIONS](DECISIONS.md) O1 (Azure key), O10 (column solution)

---

*Created: 2026-01-29 | Updated: 2026-02-27*
