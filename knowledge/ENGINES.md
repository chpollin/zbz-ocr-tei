---
type: knowledge
created: 2026-03-05
updated: 2026-03-05
tags: [zbz-ocr-tei, engines, ocr, layout, mistral, deepseek, gemini, docling]
status: active
---

# Engines (OCR + Layout)

OCR and layout tools in the pipeline. Four active engines, two roles.

Dependencies: [PIPELINE](PIPELINE.md)

---

## Mistral Document AI -- OCR Production

Role: Primary OCR engine for ZBZ production.
Model: mistral-document-ai-2512 on Azure AI Foundry (Serverless API, Pay-as-you-go).
Accuracy: 93.58% CER on 15 docs. Details in [TESTPLAN](TESTPLAN.md).
Speed: ~1.3s/page.
Output: Per-page Markdown with image references and dimensions.
Languages: 36 (de, fr, en, es, it, ...).

Setup:
- Deploy in Azure AI Foundry: Model Catalog > mistral-document-ai-2512 > Serverless Endpoint
- .env: MISTRAL_DOC_AI_ENDPOINT, MISTRAL_DOC_AI_KEY (see .env.example)
- Regions: East US, East US 2, West US, West US 3, South Central US, North Central US, Sweden Central

API:
- POST {endpoint}/v1/ocr with Bearer token
- Input: Base64-encoded PDF in document.document_url field
- Response: pages[] with index, markdown, images[], dimensions
- Limit: 30 pages/request, 30 MB max (pipeline splits automatically via MistralOCR._split_pdf())
- Annotations: bbox_annotation + document_annotation for structured extraction (max 8 pages)

Common errors:
- 404 after deployment: append /v1/ocr to endpoint URL
- 413 / file too large: compress or split PDF
- Base64 error: no line breaks in Base64 string

Open:
- Test extract_header/extract_footer to reduce JSTOR artifacts without LLM
- Analyze Doc 290 (CER 18%) and Doc 1060 (CER 22.6%) -- low priority

---

## DeepSeek-OCR-2 -- OCR Development

Role: Development OCR engine, actively used for Type A (single-column) and Type C (monographs).
Model: deepseek-ai/DeepSeek-OCR-2 (3B VLM).
Hardware: GPU with 8+ GB VRAM, CUDA 12.4+.
Accuracy: 94-97% on Type A. Details in [TESTPLAN](TESTPLAN.md).
Speed: ~1.6s/page (RTX 3070).
Output: Markdown with bounding boxes.

Prompt (Document mode, our standard):
`<image>\n<|grounding|>Convert the document to markdown.`

The grounding tag activates layout recognition with bounding boxes. Without it (Free OCR mode: `<image>\nOCR this image.`) runs faster but without layout info.

Known issues:
- High GPU load -- can freeze PC, run tests individually or on cloud VM
- Column order incorrect for Type B two-column -- use Gemini detect instead
- Requires use_safetensors=True when loading model

Sources: https://huggingface.co/deepseek-ai/DeepSeek-OCR-2

---

## Docling 2.75 -- Layout Primary

Role: Primary layout engine. Layout analysis only -- no OCR (RapidOCR has encoding issues with French: e becomes O).
Model: RT-DETR V2 Heron (42.9M params, IBM Research, trained on DocLayNet).
Speed: ~5s/page (RTX 4060 GPU), ~27s/page (CPU/docling-serve).
Status: Production -- 286/286 docs, 4,152 pages processed.
Quality: 75% good, 10% warning, 12% bad, 3% empty (compute_page_quality).

Detects 17 block types: Title, Section-header, Text, Footnote, Caption, Page-header, Page-footer, Picture, Table, Formula, List-item, Code, Document Index, and more.

Tag mapping Docling to ZBZ: see [PLAN](PLAN.md) section ZBZ Structural Tags.

Scripts:
- run_layout_analysis.py: local GPU (~5s/page, preferred)
- run_layout_cloud.py: docling-serve API (~27s/page CPU, Docker)

Troubleshooting:
- Symlink warning on Windows: set HF_HUB_DISABLE_SYMLINKS_WARNING=1
- CUDA conflict with DeepSeek: run Docling on CPU (default)

---

## Gemini 3.1 Flash Lite -- Layout QA + Detect

Role: Layout correction and re-detection for pages where Docling fails (~15% bad+empty).
Model: gemini-3.1-flash-lite-preview.
SDK: google-genai (new SDK).
Cost: $0.25/1M input, $1.50/1M output. ~$3-4 for 4,152 pages total.
Status: Production -- auto mode running on 286 docs.

Three modes in layout_qa_gemini.py:
- --mode qa: sends Overlay PNG + Layout JSON to Gemini. Corrects labels, removes false positives. Returns quality score 0-100.
- --mode detect: sends raw scan to Gemini Vision. Full re-detection with box_2d coordinates (0-1000 scale), converted to project format (x_pct/y_pct/w_pct/h_pct, 0-100%). For bad/empty pages.
- --mode auto: routes by compute_page_quality() -- detect for bad/empty, qa for good/warning.

Structured Output via response_schema. Both versions preserved: _layout.json (Docling original) + _layout_gemini.json (Gemini corrected).

Quality results:
- QA mode: average score ~70. Catches page numbers, running headers, JSTOR metadata.
- Detect mode: Doc 510 p7 found 4 regions (vs Docling 2, missing paragraph recovered). Doc 900 p1 found 47 regions (vs Docling 26).
- Limitations: rightmost column missed on wide landscapes, photo/figure detection unreliable.

Warnings: thought_signature parts in Flash Lite responses cause SDK warnings. Harmless. Suppress with PYTHONWARNINGS=ignore or warnings.filterwarnings in code.

---

## Architecture Decision (E19/E20)

Requirements: structural recognition, BBox coordinates, FR/DE support, <$100 for 7,200 pages, PAGE-XML 2013-07-15 compatible.

Evaluated (25.02.2026): Gemini, Claude, Mistral (for layout), Docling, Surya, Kraken, Azure Document Intelligence.

Decision: Docling + Gemini hybrid.
- Docling: best open-source BBox (mAP 0.699), 17 classes, free, CPU-capable
- Mistral: stays as text engine (93.58% validated)
- Gemini: QA validator + detect fallback (~15% bad pages)
- Claude: not for layout (no BBox output), valuable for downstream TEI/NER

Fallback: Kraken (native PAGE-XML, historical French docs). ocr-fileformat (UB Mannheim, https://github.com/UB-Mannheim/ocr-fileformat) can convert between 30+ OCR formats including hOCR, PAGE-XML, ALTO, TEI.

---

## References

- [PIPELINE](PIPELINE.md) for pipeline integration
- [TESTPLAN](TESTPLAN.md) for CER/WER measurements
- [INFRASTRUKTUR](INFRASTRUKTUR.md) for Azure configuration
- [PLAN](PLAN.md) for ZBZ structural tags and implementation phases
- [DECISIONS](DECISIONS.md) for E2, E6, E19, E20, E25, E26

---

Created: 2026-03-05
