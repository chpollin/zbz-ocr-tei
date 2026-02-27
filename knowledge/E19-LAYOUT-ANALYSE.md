# E19: Layout Analysis -- Research and Decision

> **Status:** Research completed, recommendation formulated, evaluation pending
> **Date:** 25.02.2026
> **Context:** Scope expansion after meeting 25.02.2026 -- zbz-ocr-tei now covers the entire pipeline (PDF -> TEI-XML). For PAGE-XML generation (Stage 3) we need layout analysis with structural recognition and bounding-box coordinates.

## Requirements

The layout analysis must:
1. **Recognize structural elements:** Headings, Paragraphs, Footnotes, Page-Numbers, Captions, Spaces
2. **Map to ZBZ tags:** zb_heading, zb_paragraph, zb_space, zb_type_document, footnote, page-number, caption
3. **Provide bounding-box coordinates** for PAGE-XML TextRegion/Coords
4. **Support French/German** (66% FR, 30% DE)
5. **Affordable costs** for 7,200 pages (<$100 total)
6. **Convertible to PAGE-XML 2013-07-15** (or deliver natively) *(corrected from 2019-07-15 per E23)*

## Evaluated Approaches

### A. Gemini 2.5 Flash / 3.0 Flash (Vision + Structured Output)

**Capabilities:**
- BBox output: Yes, `[ymin, xmin, ymax, xmax]` on 0-1000 scale, custom labels possible
- Structured JSON: Fully supported (`response_json_schema` with Pydantic)
- PDF-native: Up to 1,000 pages/request, 258 tokens/page
- Segmentation masks: From Gemini 2.5 onwards (pixel-level)
- Multilingual: Strong for FR/DE (Latin script)

**Costs:**
- Gemini 2.5 Flash-Lite: $0.10/1M input tokens → ~$0.00003/page
- Gemini 3 Flash: $0.50/1M → ~$0.00013/page
- **7,200 pages: ~$0.20 - $1.00** (extremely affordable)

**Limits:** Max 3,600 images/request. Gemini 2.0 is deprecated, 2.5 stable, 3.x preview.

**Strengths:** A single API call delivers OCR + layout + structural classification + BBox in JSON. Most flexible prompt schema. Cheapest option.

**Weaknesses:** No dedicated layout model -- BBox quality is prompt-dependent. No published benchmarks for document layout segmentation. Preview models may change.

**Rating:** ★★★★☆

### B. Claude Vision (Opus 4.6 / Haiku 4.5)

**Capabilities:**
- BBox output: **No** -- qualitative descriptions ("top left"), no pixel coordinates
- Structured JSON: Via Tool Use, but without coordinates
- PDF-native: Yes, up to 100 pages/request
- Multilingual: Excellent for FR/DE

**Costs:**
- Haiku 4.5: ~$0.003-0.006/page (3,000 tokens/image)
- **7,200 pages: ~$22 - $43**

**Strengths:** Best reasoning about document structure and semantics. Ideal for QA/verification and TEI generation.

**Weaknesses:** **Cannot provide BBox coordinates** -- disqualified for layout analysis with PAGE-XML coordinates. Image downscaling to 1,568px max.

**Rating:** ★★☆☆☆ (unsuitable for layout analysis, but valuable for TEI generation/QA)

### C. Mistral Document AI 2512 (already in the project)

**Capabilities:**
- OCR: Excellent (93.58% accuracy, validated)
- BBox for images/figures: Yes (pixel coordinates)
- BBox for text regions: **No** -- no coordinates for headings, paragraphs, footnotes
- `document_annotation`: Structured JSON extraction possible, but **max 8 pages/request**
- `extract_header`/`extract_footer`: Yes (not yet tested, O19)
- Structural recognition via Markdown: Implicit (# Heading, Paragraphs, Lists)

**Costs:**
- OCR: $2/1,000 pages → **7,200 pages: $14.40**
- Annotation: $3/1,000 pages

**Strengths:** Already integrated and validated. Markdown output encodes structure implicitly. extract_header/footer useful.

**Weaknesses:** **No BBox for text regions** -- cannot say "here a paragraph begins at pixel x,y". Annotation limit of 8 pages/request is restrictive. No newer model than 2512 available.

**Rating:** ★★★☆☆ (excellent for OCR, insufficient for layout coordinates)

### D. Docling (IBM, Open Source)

**Capabilities:**
- Layout model: RT-DETR V2 "Heron" (42.9M params), trained on DocLayNet
- **17 block types:** Caption, Footnote, Formula, List-item, Page-footer, Page-header, Picture, Section-header, Table, Text, Title, Document Index, Code, etc.
- BBox: Yes, for all detected blocks (JSON with provenance)
- Body vs. Furniture: Distinguishes main content from headers/footers
- DocLayNet mAP: **0.699** (Heron), AP-50: 0.859

**Costs:** Free (MIT license). CPU: ~1 sec/page. GPU: 28ms/page (A100).
- **7,200 pages CPU: ~2 hours. Cost: $0.**

**Limits:** v2.75.0 (24.02.2026, latest). No native PAGE-XML export -- JSON conversion required.

**Mapping Docling → ZBZ Tags:**

| Docling BlockType | ZBZ Structural Tag |
|-------------------|--------------------|
| Title | zb_heading |
| Section-header | zb_heading |
| Text / Paragraph | zb_paragraph |
| Footnote | footnote |
| Page-header | (filter/ignore) |
| Page-footer | (filter/ignore) |
| Caption | caption |
| (Infer vertical spacing) | zb_space |

**Strengths:** Already validated in the project (Stage 1a). Best open-source layout segmentation. 17 classes cover our needs. Free.

**Weaknesses:** No PAGE-XML export (custom converter needed). Encoding issues with integrated OCR (E2 -- we only use layout). No own OCR text.

**Rating:** ★★★★★

### E. Surya

**Capabilities:**
- 15 block types incl. Footnote, Caption, Section-header, Page-header/footer
- BBox + polygon coordinates + reading order + confidence
- OCR in 90+ languages, LaTeX-OCR, table structure
- GPU: 7-20 GB VRAM depending on model

**Costs:** Free for research and startups (<$2M revenue). GPL license.

**Strengths:** Strong alternative to Docling. Native reading order. Confidence scores per region.

**Weaknesses:** GPL license could be problematic for ZBZ fork. GPU-intensive. No PAGE-XML.

**Rating:** ★★★★☆

### F. Kraken OCR

**Capabilities:**
- Specifically developed for **historical documents** (EPHE Paris)
- Trainable layout analysis with baseline segmentation
- **Native PAGE-XML and ALTO export**
- Reading order detection
- Word-BBox and character-level segmentation

**Costs:** Free (Apache 2.0). v6.0.4 (Feb 2026), actively maintained.

**Strengths:** Only tool with native PAGE-XML export. Designed for historical French documents. Perfect domain fit.

**Weaknesses:** Trainable classes (no predefined ZBZ schema). Layout model may need training or customization. Smaller community than Docling.

**Rating:** ★★★★☆

### G. Azure Document Intelligence

**Capabilities:**
- Paragraph roles: title, sectionHeading, footnote, pageNumber, pageHeader, pageFooter
- BBox (polygon coordinates) for all elements
- Tables with cell structure, Figures with Captions
- FR/DE fully supported

**Costs:** ~$0.01/page → **7,200 pages: ~$72**. Free tier: 500 pages/month.

**Strengths:** ZBZ already uses Azure (Mistral). Very good paragraph role detection. Enterprise-grade.

**Weaknesses:** Cloud-only. No PAGE-XML. Higher costs than Docling (free).

**Rating:** ★★★☆☆

## Evaluation Matrix

| Criterion (Weight) | Gemini | Claude | Mistral | Docling | Surya | Kraken | Azure DI |
|---------------------|--------|--------|---------|---------|-------|--------|----------|
| **Structural Recognition** (30%) | 4 | 3 | 2 | 5 | 4 | 4 | 4 |
| **BBox Coordinates** (25%) | 4 | 0 | 1 | 5 | 5 | 5 | 5 |
| **PAGE-XML Proximity** (15%) | 2 | 0 | 0 | 3 | 2 | 5 | 2 |
| **FR/DE** (10%) | 4 | 5 | 5 | 4 | 4 | 5 | 5 |
| **Cost** (10%) | 5 | 2 | 3 | 5 | 5 | 5 | 2 |
| **Integration** (10%) | 3 | 4 | 5 | 4 | 3 | 3 | 3 |
| **Weighted Score** | **3.45** | **1.95** | **2.15** | **4.35** | **3.85** | **4.15** | **3.45** |

Scale: 0 = unsuitable, 1 = poor, 2 = fair, 3 = acceptable, 4 = good, 5 = excellent

## Recommendation

### Primary: Docling + Gemini Hybrid (Approach D+A)

**Recommended Architecture:**

```
Page image
  |
  +--> Docling (layout analysis, CPU, free)
  |      Result: Regions with BBox + block types (17 classes)
  |
  +--> Mistral OCR (text per page, already available)
  |      Result: Markdown with implicit structure
  |
  +--> Gemini 2.5 Flash (validation + enrichment, optional)
         Result: Structural classification, reading order, ZBZ tag assignment
         Only for problem cases (Type B two-column, Type D special)
```

**Rationale:**
1. **Docling** delivers the best open-source BBox coordinates (mAP 0.699) with 17 classes incl. Footnote -- free, CPU-capable, already in the project
2. **Mistral OCR** remains the text engine (93.58% validated) -- no switch needed
3. **Gemini** as an optional "arbiter" for mapping Docling block type → ZBZ tag and for problem cases (Type B columns, Type D special) -- extremely affordable ($0.20-1.00 for 7,200 pages)
4. **Claude** not for layout, but for downstream TEI generation and NER (where it excels)

### Alternative: Kraken (if native PAGE-XML is highest priority)

Kraken is the only tool with native PAGE-XML export and was developed for historical French documents. Downside: Trainable classes require initial configuration, smaller community. Recommended as a **fallback** if the Docling-to-PAGE-XML conversion proves too error-prone.

### Surprise Find: ocr-fileformat (UB Mannheim)

The tool `ocr-fileformat` (https://github.com/UB-Mannheim/ocr-fileformat) can convert between 30+ OCR formats, including hOCR ↔ PAGE-XML ↔ ALTO ↔ TEI. If we have one format, we can convert it to any other. This significantly reduces the risk of the format decision.

## Next Steps

**Evaluation on all 15 pilot PDFs:**
1. Run Docling layout analysis on all 383 page images
2. Map Docling block types → ZBZ tags (table above)
3. Visually inspect results: Do the regions match the page image?
4. For problem cases (Type B): Test Gemini as an alternative
5. Finalize decision E19

## Sources

- Gemini API Docs: https://ai.google.dev/gemini-api/docs/vision, /structured-output, /document-processing
- Gemini Pricing: https://ai.google.dev/pricing
- Mistral OCR 3 Docs: https://docs.mistral.ai/capabilities/document_ai/
- Mistral OCR 3 Blog: https://mistral.ai/news/mistral-ocr-3
- Docling: https://github.com/DS4SD/docling, arXiv:2408.09869, arXiv:2509.11720
- Surya: https://github.com/VikParuchuri/surya
- Kraken: https://github.com/mittagessen/kraken
- PaddleOCR: https://github.com/PaddlePaddle/PaddleOCR
- Azure Document Intelligence: https://learn.microsoft.com/en-us/azure/ai-services/document-intelligence/
- OCR-D: https://github.com/OCR-D, https://ocr-d.de
- ocr-fileformat: https://github.com/UB-Mannheim/ocr-fileformat
- PAGE-XML Schema: https://github.com/PRImA-Research-Lab/PAGE-XML
- DocLayNet: https://github.com/DS4SD/DocLayNet (KDD'22)
- DocLayout-YOLO: https://github.com/opendatalab/DocLayout-YOLO
