---
type: knowledge
created: 2026-01-29
updated: 2026-03-05
tags: [zbz-ocr-tei, pipeline, dataflow, ocr]
status: active
---

# Pipeline

Data flow from PDF to TEI-XML: stages, scripts, formats. Since the scope expansion (25.02.2026), zbz-ocr-tei covers the entire pipeline (OCR + Layout + PAGE-XML + NER/GND + TEI-XML). Implementation plan: [PLAN.md](PLAN.md).

**Dependencies:** [PROJEKT](PROJEKT.md)

---

## Pipeline Overview

```
PDF ──→ Page images ──→ OCR ──→ Layout ──→ PAGE-XML ──→ NER/GND ──→ TEI-XML
         extract_pages    ocr_pipeline  layout/    page_xml_gen    ner/       tei/
         docs/images/     output/       output/    output/         output/    output/
                          mistral_res/  layout/    page_xml/       entities/  tei_xml/
                                                       │
                              ┌─────────────────────────┘
                              ▼
                    Evaluation + Dashboard
                    evaluate_ocr + generate_dashboard_data
```

### Stages (7-Stage Pipeline)

| Stage | Task | Script | Output | Status |
|-------|------|--------|--------|--------|
| 1 | PDF → Page images | `scripts/extract_pages.py` | PNG (`docs/images/`) | Production |
| 1a | Document classification (Gemini) | `scripts/classify_docs.py` | `data/doc_metadata.json` + `output/classification/` | Production (286 docs) |
| 2 | OCR | `scripts/ocr_pipeline.py` | Page-level Markdown (Mistral: `output/mistral_results/`, DeepSeek: `output/ocr_results/`) | Production |
| 2a | LLM post-correction (optional) | `scripts/llm_postprocess.py` | Corrected Markdown (`output/llm_corrected_c/`) | Production, E17: optional |
| 2b | Gemini OCR correction (optional) | `scripts/gemini_ocr_correct.py` | Corrected Markdown (`output/gemini_corrected_a/` or `_b/`) | Sample (5 docs), E29 |
| 3 | Layout analysis | `scripts/run_layout_analysis.py` (local GPU) or `scripts/run_layout_cloud.py` (docling-serve API) | Regions + BBox (JSON, `output/layout/`) + overlay PNGs | Production (286/286 docs, 4,152 pages) |
| 3a | Layout QA/Detect (Gemini) | `scripts/layout_qa_gemini.py` (3 modes: qa/detect/auto) | Corrected/detected regions (`_layout_gemini.json`) | Production (E25/E26) |
| 4 | Layout + OCR → PAGE-XML | `scripts/layout/page_xml_generator.py` | PAGE-XML + METS (`output/page_xml/`) | **Phase 1** |
| 5 | NER + GND | `scripts/ner/ner_pipeline.py` + `gnd_linker.py` | Entity JSON (`output/entities/`) | **Phase 2** |
| 6 | Layout + OCR → TEI-XML | `scripts/tei/tei_generator.py` | TEI-XML (`output/tei/`) | Production (15/15 docs, 383 files) |
| 7 | Evaluation + Dashboard | `scripts/evaluate_ocr.py` + `generate_dashboard_data.py` | Reports + `docs/data/dashboard.json` | Production (extension in Phase 4) |

**Note on Stage 6:** The TEI generator currently goes directly from layout JSON + OCR Markdown to TEI-XML, without PAGE-XML as an intermediate format. PAGE-XML (Stage 4) and NER (Stage 5) are not yet implemented — once they are, the TEI generator will be extended accordingly.

Lessons from E16-E18: TEI page numbers != PDF page numbers (cover pages, blanks shift offset). Always match by content, not page number. Monographs (50-250 pages) need page-by-page comparison; global alignment fails above ~50 pages. Both layout versions preserved (_layout.json + _layout_gemini.json) -- in DH, provenance is as important as quality.

**Helper scripts:** `extract_pages.py` (page images), `extract_gnd.py` (GND IDs), `postprocess/` (normalization).

**Layout engine (E19/E20):** Docling 2.75 (RT-DETR V2 Heron, 17 block types). All 286 docs analyzed (4,152 pages). Local GPU (RTX 4060): ~5s/page. Quality: 75% good, 10% warning, 12% bad, 3% empty (`compute_page_quality`, 4,152 pages). Details: [ENGINES](ENGINES.md).

**Layout via API (E24):** `run_layout_cloud.py` sends page PNGs to a docling-serve instance (IBM's official API server for Docling). Same output format as `run_layout_analysis.py`. Server: `docker run -p 5001:5001 quay.io/docling-project/docling-serve-cpu`. CPU: ~27s/page, GPU (Cloud Run L4): ~28ms/page. Resume-capable, configurable via `DOCLING_SERVE_URL` env var. **Note:** Local GPU via `run_layout_analysis.py` is now preferred (~5s/page on RTX 4060).

**Automated Layout QA (E25):** `layout_qa_gemini.py --mode qa` sends Overlay-PNG + Layout-JSON to Gemini 3.1 Flash Lite Preview. Gemini corrects labels, removes false positives, flags missing regions. Returns corrected JSON with quality score (0-100). Both versions preserved: `_layout.json` (Docling original) + `_layout_gemini.json` (Gemini-corrected). Viewer supports toggle between both sources. Cost: ~$2 for 4,152 pages. SDK: `google-genai`.

**Gemini Layout Detect (E26):** `layout_qa_gemini.py --mode detect` uses Gemini 3.1 Flash Lite Preview as a full layout detector for pages where Docling fails (~15% bad+empty). Sends raw scan (no overlay) to Gemini Vision with structured output schema. Returns regions with `box_2d` coordinates (0-1000 scale), converted to project format (`x_pct/y_pct/w_pct/h_pct`, 0-100%). Three modes: `--mode qa` (label correction), `--mode detect` (full re-detection), `--mode auto` (routes by Docling quality score — detect for bad/empty, qa for good/warning). Source field: `"gemini-detect"` vs `"gemini"` for QA. Cost: ~$1-2 for ~1,570 detect pages.

---

## Stage 1a: Document Classification

**Script:** `scripts/classify_docs.py`

Sends the first 5 page images per document to Gemini 3.1 Flash Lite Preview. Extracts metadata via Structured Output (response_schema): language, pub_form, layout_type, title, author, date, description, has_jstor_cover, num_columns. Cost: ~$1-2 for 286 docs. Output: `data/doc_metadata.json` (aggregate, TEI-mappable) + `output/classification/{doc_id}_classification.json` (raw per-doc). Resume-capable (skip-existing). Used by tei_generator (teiHeader), generate_dashboard_data (dashboard/viewer), and pipeline routing (engine selection).

---

## Stage 1: OCR

**Script:** `scripts/ocr_pipeline.py`

### Engine Selection (Auto mode in `ocr_pipeline.py`)

1. Document in `TWO_COLUMN_DOCS`? → Docling (Layout) + DeepSeek
2. `MISTRAL_DOC_AI_KEY` set? → Mistral Document AI (API)
3. Otherwise → DeepSeek (local, GPU)

Document types: See [QUELLENANALYSE](QUELLENANALYSE.md) §Document Types.
Engine details: See [ENGINES](ENGINES.md).

### Layout Analysis (Type B only)

For two-column documents, `ocr_pipeline.py` internally uses Docling (IBM) with `do_ocr=False` for column detection. Docling's own OCR is not used (RapidOCR has encoding issues). Details: [ENGINES](ENGINES.md) §Docling.

### Prompts

**Mistral Document AI:** No prompt — the API receives only the PDF as Base64, no instruction text. Output is page-level Markdown.

**DeepSeek-OCR-2:** Fixed prompt in `config.py:31`:
```
<image>\n<|grounding|>Convert the document to markdown.
```

### OCR Quality

Full results: See [TESTPLAN](TESTPLAN.md) §Results.

---

## Stage 2: LLM Post-Correction

**Script:** `scripts/llm_postprocess.py`

| Aspect | Details |
|--------|---------|
| Model | Claude Haiku 4.5 (Anthropic) |
| Input | OCR Markdown from Stage 2 |
| Output | Corrected Markdown |
| Role | Correction, NOT transcription — the LLM never sees the image |
| Cost | ~$0.33 for 50 pages, ~$48 for 7,200 pages |

**Important:** The LLM does not perform OCR. It only corrects the text produced by Mistral/DeepSeek. It receives document context (type, language, genre) and identifies character errors, missing accents, OCR artifacts.

### Prompt (Variant C, Default)

Three variants tested (A/B/C, see `llm_postprocess.py`). Variant C (Few-Shot) is default (E17): best CER/cost tradeoff. Includes typical Mistral OCR errors as examples (missing letters, wrong sequences, merged words, JSTOR artifacts). Language hints (FR: accents/guillemets, DE: umlauts/compounds) inserted dynamically.

Results: See [TESTPLAN](TESTPLAN.md) §LLM Post-Correction. LLM correction improves docs with CER >10%, slightly degrades good OCR (<5%). Optional, not default.

---

## Stage 2b: Gemini OCR Correction

**Script:** `scripts/gemini_ocr_correct.py`

| Aspect | Details |
|--------|---------|
| Model | Gemini 3.1 Flash Lite Preview (`gemini-3.1-flash-lite-preview`) |
| Input | OCR Markdown from Stage 2 + metadata from `doc_metadata.json` |
| Output | Corrected Markdown + Analysis JSON |
| Approach | Two-step: Analyse (structured JSON) then Korrektur (plain text) |
| Variants | A = text-only + metadata context, B = multimodal (+ scan image) |
| Cost | ~$1-3 for all 4,152 pages (Variant A), ~$2-5 (Variant B) |

**Two-step process (E29):**

1. **Analyse:** Gemini receives OCR text + document metadata (language, pub_form, layout_type, title, author, date, description). Variant B additionally receives the scan image. Returns structured JSON with corrections (original, corrected, category, confidence, justification), overall quality score (0-100), and summary. Categories: `missing_accent`, `wrong_character`, `merged_words`, `split_word`, `missing_character`, `extra_character`, `ocr_artifact`, `punctuation`, `formatting`, `other`.

2. **Korrektur:** Gemini receives original OCR text + analysis from step 1. Applies only high/medium confidence corrections. Output: corrected full text as Markdown. Optimization: if step 1 finds zero actionable corrections, step 2 is skipped and original text is copied.

**Output structure:**
```
output/
  gemini_corrected_a/           # Variant A: text-only
    {doc_id}_p{page}.md         # Corrected text
    {doc_id}_p{page}.analysis.json  # Analysis
    manifest.json
  gemini_corrected_b/           # Variant B: multimodal
    (same structure)
```

**Sample results (5 docs, E29):**

| Doc | Mistral CER | Gemini A CER | Gemini B CER |
|-----|-------------|--------------|--------------|
| 2310 | 7.00% | 3.88% | 3.88% |
| 1180 | 3.12% | 3.08% | 3.09% |
| 890 | 5.96% | 5.77% | 5.72% |
| 90 | 1.21% | 1.20% | 1.12% |
| 40 | 2.57% | 2.58% | n/a |
| **Avg** | **3.97%** | **3.30%** | **3.45%** (4 docs) |

Variant A avg CER 3.30% vs Mistral 3.97% (-0.67pp). Biggest improvement on Doc 2310 (JSTOR cover, French accents): 7.00% to 3.88%. Both variants improve CER; Variant A slightly better on average and cheaper.

---

## Post-Processing (Helper Module)

**Implemented in:** `scripts/postprocess/` — not run automatically in the pipeline, but manually as needed.

| Function | Purpose | Example |
|----------|---------|---------|
| `normalize_text()` | Unify typographic variants | `\u201e` -> `"` |
| `dehyphenate()` | Resolve hyphenation | `Wis- senschaft` -> `Wissenschaft` |
| `clean_markdown()` | Remove Markdown syntax | `## Titel` -> `Titel` |

**Important:** Markdown formatting (`**bold**`, `*italic*`) must be PRESERVED for export. PAGE-XML stores text as-is in `<TextEquiv><Unicode>`, TEI transformation converts to `<hi rendition>`. Therefore `clean_markdown()` is **not** called in the production path — only `normalize_text()` and `dehyphenate()` are safe.

---

## Stage 3: Evaluation

**Script:** `scripts/evaluate_ocr.py`

| Aspect | Details |
|--------|---------|
| Input | OCR Markdown + reference TEI (`data/referenz-tei/*.xml`) |
| Metrics | CER (Character Error Rate), WER (Word Error Rate) |
| Alignment | Global (short docs) or page-wise (monographs) |
| Output | JSON (`output/evaluation/evaluation_results.json`) + HTML report |

Compares OCR output character-by-character with manually created reference TEI. Uses `rapidfuzz` for Levenshtein distance.

### Two Comparison Modes

| Mode | Condition | Method |
|------|-----------|--------|
| Global | ≤10 TEI pages | Full-text alignment (phrase search) |
| Page-wise | >10 TEI pages | Per-page comparison via `<pb facs>` tags |

**Auto-detection:** The script automatically selects the mode based on TEI page count. CLI flags `--pagewise` / `--no-pagewise` override.

**Page-wise comparison (for monographs):**
1. TEI is split into individual pages using `<pb facs="#facs_N">` tags
2. Content-based matching assigns each TEI page to the corresponding OCR file (word overlap with sliding window)
3. CER/WER is computed per page, then character-weighted averaged

**Why no fixed offset:** Library PDFs contain cover pages, blank pages, and illustrations that do not appear in the TEI. The offset between TEI page numbers and OCR file numbers is not constant (e.g., Doc 1520: offset +8, drifts to +9). Content matching solves this automatically.

---

## Stage 4: Dashboard

**Script:** `scripts/generate_dashboard_data.py`

Aggregates all pipeline outputs (page images, evaluation results, LLM manifest) into `docs/data/dashboard.json`. Checks per document the existence of each pipeline stage and computes averages per phase.

---

## PAGE-XML Export (Phase 1)

**Scripts:** `scripts/layout/page_xml_generator.py`, `scripts/layout/mets_generator.py`

PAGE-XML is the intermediate format for layout regions + OCR text. It serves as input for the TEI transformation (Phase 3) and as an optional export for Transkribus-compatible tools.

| Aspect | Details |
|--------|---------|
| Schema | PAGE-XML 2013-07-15 (Transkribus standard, confirmed by ZBZ export E23) |
| Namespace | `http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15` |
| Layout engine | Docling 2.75 (E19/E20) |

### Export Structure per Document

```
output/page_xml/{doc_id}/
  mets.xml                    # METS-Manifest
  images/{doc_id}_p001.png    # Page images
  page/{doc_id}_p001.xml      # PAGE-XML per page
```

Details: See [PLAN.md](PLAN.md) Phase 1.

---

## CLI Commands

```bash
# Extract page images (for viewer)
python scripts/extract_pages.py                              # all PDFs, 150 DPI
python scripts/extract_pages.py --pdf 2310.pdf --dpi 300     # single PDF

# Document classification (stage 1a, requires GEMINI_API_KEY)
python -m scripts.classify_docs                              # all 286 docs
python -m scripts.classify_docs --doc 2310                   # single document
python -m scripts.classify_docs --force                      # overwrite existing

# OCR (stage 1)
python scripts/ocr_pipeline.py -i data/scans/2310.pdf -e mistral
python scripts/ocr_pipeline.py --all --engine auto

# LLM post-correction (stage 2, requires ANTHROPIC_API_KEY)
python -m scripts.llm_postprocess --phase phase1 --variant C
python -m scripts.llm_postprocess --all

# Gemini OCR correction (stage 2b, requires GEMINI_API_KEY)
python -m scripts.gemini_ocr_correct --sample                # 5 pilot docs, Variant A
python -m scripts.gemini_ocr_correct --sample --variant B     # 5 pilot docs, multimodal
python -m scripts.gemini_ocr_correct --doc 2310               # single document
python -m scripts.gemini_ocr_correct --doc 2310 --variant B   # single doc, multimodal
python -m scripts.gemini_ocr_correct --all                    # all docs with OCR
python -m scripts.gemini_ocr_correct --step analyze           # analysis only
python -m scripts.gemini_ocr_correct --step correct           # correction only
python -m scripts.gemini_ocr_correct --force                  # overwrite existing
python -m scripts.gemini_ocr_correct --dry-run                # show prompts, no API calls

# Evaluation (stage 3)
python scripts/evaluate_ocr.py --all
python scripts/evaluate_ocr.py --phase phase1 --engine mistral
python -m scripts.evaluate_ocr --all --ocr-dir output/gemini_corrected_a  # evaluate Gemini A

# Layout analysis (stage 3, local GPU preferred, ~5s/page on RTX 4060)
python -m scripts.run_layout_analysis                      # all documents
python -m scripts.run_layout_analysis --doc 2310           # single document
python -m scripts.run_layout_analysis --overlay            # Generate overlay PNGs (no GPU)
python -m scripts.run_layout_analysis --overlay --doc 2310 # Overlay for single document

# Layout analysis via docling-serve API (stage 3, fallback if no local GPU)
python -m scripts.run_layout_cloud                         # all documents
python -m scripts.run_layout_cloud --doc 2310              # single document
python -m scripts.run_layout_cloud --url http://host:5001  # custom server URL
python -m scripts.run_layout_cloud --force                 # overwrite existing

# Layout QA/Detect via Gemini (stage 3a, requires GEMINI_API_KEY)
python -m scripts.layout_qa_gemini                         # all docs, QA mode (default)
python -m scripts.layout_qa_gemini --doc 2310              # single document
python -m scripts.layout_qa_gemini --mode detect --doc 510 # full re-detection
python -m scripts.layout_qa_gemini --mode auto             # auto-route by quality
python -m scripts.layout_qa_gemini --force                 # overwrite existing

# Generate TEI-XML (stage 6)
python -m scripts.tei.tei_generator                      # all documents
python -m scripts.tei.tei_generator --doc 2310           # single document
python -m scripts.tei.tei_generator --doc 2310 --page 2  # single page

# Dashboard data (stage 7)
python -m scripts.generate_dashboard_data

# Post-processing (manual, as needed)
python -m scripts.postprocess.pipeline
```

---

## Dashboard & QA UI

**Directory:** `docs/`

| File | Purpose |
|------|---------|
| `docs/index.html` | Dashboard: metrics, document catalog, quality comparison |
| `docs/viewer.html` | Document view: facsimile + OCR text + TEI-XML, source toggle, layout overlay |
| `docs/shared.css` | Unified design system (CSS Custom Properties) |
| `docs/shared.js` | Shared utilities (data loading, formatting, DOM helpers) |
| `docs/tei-viewer.js` | TEI rendering: rendered view, syntax highlighting, diff, entities |
| `docs/data/dashboard.json` | Generated data (from `scripts/generate_dashboard_data.py`) |

The dashboard shows pipeline status, CER comparison (Mistral/LLM/DeepSeek/Gemini), engine availability, and a filterable document catalog. Data is statically generated from pipeline outputs. TEI rendering (rendered view, XML highlighting, reference diff, entity sidebar) is in `tei-viewer.js`.

### GitHub Pages / Online-Demo (E28)

Full pipeline output (`output/`) is gitignored and only available locally. For the online demo (GitHub Pages), 4 representative documents are committed:

| Doc | Type | Language | Pages | Variety |
|-----|------|----------|-------|---------|
| 2310 | A (single-column) | FR | 3 | Journal article, JSTOR cover |
| 1000 | B (two-column) | FR | 4 | Two-column journal article |
| 1330 | D (special) | DE/FR | 6 | Bilingual book |
| 1540 | C (monograph) | DE | 8 | German monograph |

**Data locations:**
- Scan images: `docs/images/{doc_id}/` (gitignore exception)
- OCR + Layout + TEI: `docs/data/examples/{doc_id}/` (flat files)

**Fallback mechanism:** `shared.js` fetch functions try the primary path (`../output/...`) first, then `data/examples/{doc_id}/...` as fallback. This ensures both local (full data) and online (DEMO data) work without configuration.

**UI indicators:** Disclaimer banner on dashboard + viewer ("Prototyping Interface", "KI-generiert"). DEMO badge (teal tag) on the 4 example docs in the catalog. DEMO docs sorted first.

---

## References

- [PROJEKT](PROJEKT.md) for ecosystem and milestones
- [ENGINES](ENGINES.md) for engine details
- [TESTPLAN](TESTPLAN.md) for test results
- [INFRASTRUKTUR](INFRASTRUKTUR.md) for deployment

---

*Created: 2026-01-29 | Renamed from ARCHITEKTUR.md: 2026-02-25 | Updated: 2026-03-05*
