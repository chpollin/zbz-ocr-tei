---
type: knowledge
created: 2026-01-29
updated: 2026-03-06
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
                          mistral_res/  layout/    page_xml/       entities/  tei_unified/
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
| 3a | Layout QA/Detect (Gemini) | `scripts/layout_qa_gemini.py` (3 modes: qa/detect/auto) | Corrected/detected regions (`_layout_gemini.json`) | Production: 286 docs, 3,992 pages (E25/E26/E31) |
| 3b | Layout Overlay Generator | `scripts/generate_layout_overlays.py` | Overlay PNGs + side-by-side compare | Production: 7,988 PNGs (E31) |
| 4 | Layout + OCR → PAGE-XML | `scripts/layout/page_xml_generator.py` + `mets_generator.py` | PAGE-XML + METS (`output/page_xml/`) | Production (286 docs, 4,091 pages) |
| 5 | NER + GND | `scripts/ner/ner_pipeline.py` + `gnd_linker.py` | Entity JSON (`output/entities/`) | **Phase 3** |
| 6 | Layout + OCR → TEI-XML (rule-based) | `scripts/tei/tei_generator.py` | TEI-XML (`output/tei/`) | Production (285 docs, 4,117 files) |
| 6a | Gemini Vision TEI (1 call/page) | `scripts/tei/tei_gemini.py` | TEI-XML (`output/tei_gemini/`) | Pilot (Doc 2310), E30 |
| 6b | **Unified TEI Pipeline** (rule-based + Gemini) | `scripts/tei/tei_unified.py` | TEI-XML (`output/tei_unified/`) | **Production (286 docs), E32** |
| 6c | TEI Validation (RelaxNG + project rules) | `scripts/tei/tei_validator.py` | Validation JSON | Production, E32 |
| 7 | Evaluation + Dashboard | `scripts/evaluate_ocr.py` + `generate_dashboard_data.py` | Reports + `docs/data/dashboard.json` | Production (extension in Phase 4) |

**Note on Stage 6:** The rule-based TEI generator goes directly from layout JSON + OCR Markdown to TEI-XML. Produces flat structure (no div hierarchy, no lb, no entities beyond seed dict). **Stage 6a (E30)** was the first Gemini Vision approach (standalone, 1 call/page). **Stage 6b (E32)** is the production pipeline: combines enhanced rule-based scaffold (Step 1) with Gemini refinement (Step 2, mapping-table prompt), document assembly (Step 3), and RelaxNG validation (Step 4). Post-processing (`fix_gemini_tei()`) corrects 6 types of Gemini structural errors. Entity re-annotation (`reannotate_entities()`) catches missed mentions. Interview speaker detection in scaffold. CLI: `--doc`, `--sample`, `--all`, `--step`, `--validate`, `--force`, `--dry-run`. Cost: ~$17 for 286 docs (Gemini 3.1 Flash Lite). OCR source priority: Gemini B > Gemini A > LLM C > Mistral.

Lessons from E16-E18: TEI page numbers != PDF page numbers (cover pages, blanks shift offset). Always match by content, not page number. Monographs (50-250 pages) need page-by-page comparison; global alignment fails above ~50 pages. Both layout versions preserved (_layout.json + _layout_gemini.json) -- in DH, provenance is as important as quality.

**Helper scripts:** `extract_pages.py` (page images), `extract_gnd.py` (GND IDs), `postprocess/` (normalization).

**Layout engine (E19/E20):** Docling 2.75 (RT-DETR V2 Heron, 17 block types). All 286 docs analyzed (4,152 pages). Local GPU (RTX 4060): ~5s/page. Quality: 75% good, 10% warning, 12% bad, 3% empty (`compute_page_quality`, 4,152 pages). Details: [ENGINES](ENGINES.md).

**Layout via API (E24):** `run_layout_cloud.py` sends page PNGs to a docling-serve instance (IBM's official API server for Docling). Same output format as `run_layout_analysis.py`. Server: `docker run -p 5001:5001 quay.io/docling-project/docling-serve-cpu`. CPU: ~27s/page, GPU (Cloud Run L4): ~28ms/page. Resume-capable, configurable via `DOCLING_SERVE_URL` env var. **Note:** Local GPU via `run_layout_analysis.py` is now preferred (~5s/page on RTX 4060).

**Automated Layout QA (E25):** `layout_qa_gemini.py --mode qa` sends Overlay-PNG + Layout-JSON to Gemini 3.1 Flash Lite Preview. Gemini corrects labels, removes false positives, flags missing regions. Returns corrected JSON with quality score (0-100). Both versions preserved: `_layout.json` (Docling original) + `_layout_gemini.json` (Gemini-corrected). Viewer supports toggle between both sources. Cost: ~$2 for 4,152 pages. SDK: `google-genai`. **Document-type-specific prompts (E30):** Since 06.03.2026, prompts are augmented with 4-level hints from `doc_metadata.json` (layout type, pub_form, genre, language) via `build_doc_hints(doc_id)`. Genre is inferred from description text via `infer_genre()` (14 genres).

**Gemini Layout Detect (E26):** `layout_qa_gemini.py --mode detect` uses Gemini 3.1 Flash Lite Preview as a full layout detector for pages where Docling fails (~15% bad+empty). Sends raw scan (no overlay) to Gemini Vision with structured output schema. Returns regions with `box_2d` coordinates (0-1000 scale), converted to project format (`x_pct/y_pct/w_pct/h_pct`, 0-100%). Three modes: `--mode qa` (label correction), `--mode detect` (full re-detection), `--mode auto` (routes by Docling quality score — detect for bad/empty, qa for good/warning). Source field: `"gemini-detect"` vs `"gemini"` for QA. Cost: ~$1-2 for ~1,570 detect pages.

**Full Run (E31):** `layout_qa_gemini.py --mode auto --force` on all 286 docs. Results: 3,992/4,152 pages processed (160 failed: Invalid Unicode-Escape, Empty Response), 3,519 QA + 633 Detect, 30,714 regions, 14,708 corrections, avg score 72.7. Top change: 894 ADDED regions (missing headers, headings, footnotes). Per-page `changes_summary` logging (label transitions) and per-doc aggregation in `summary_gemini.json`. Visual QA on 10 sample pages (types A/B/C/D): Gemini clearly better than Docling alone.

**Layout Overlay Generator (E31):** `scripts/generate_layout_overlays.py` generates overlay PNGs from Gemini layout JSONs. Uses existing `draw_overlay_from_json()` from `scripts/layout/__init__.py`. Changed-highlighting: yellow border for ADDED regions, orange for label changes. Optional `--compare` flag generates side-by-side Docling-vs-Gemini images (2x width). Output: `_overlay_gemini.png` and `_overlay_compare.png` per page. 7,988 PNGs generated for all 286 docs.

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

## PAGE-XML Export (Stage 4)

**Scripts:** `scripts/layout/page_xml_generator.py`, `scripts/layout/mets_generator.py`

PAGE-XML is the intermediate format for layout regions + OCR text. It serves as an optional export for Transkribus-compatible tools and as a future input for TEI transformation.

| Aspect | Details |
|--------|---------|
| Schema | PAGE-XML 2013-07-15 (Transkribus standard, confirmed by ZBZ export E23) |
| Namespace | `http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15` |
| Layout source | Gemini-corrected preferred, Docling fallback |
| OCR source | Gemini B > Gemini A > Mistral |
| Status | Production: 286 docs, 4,091 pages |
| Granularity | Region-level (1 TextLine per TextRegion, no line-level coordinates) |

### Export Structure per Document

```
output/page_xml/{doc_id}/
  mets.xml                    # METS-Manifest
  page/{doc_id}_p001.xml      # PAGE-XML per page
```

ZBZ tag to PAGE-XML structure type mapping: `zb_heading` -> heading, `zb_paragraph` -> paragraph, `footnote` -> footnote, `caption` -> caption. Regions with `_filter`/`_skip` are excluded.

### Frontend Viewer

PAGE-XML and METS can be viewed in `docs/viewer.html` via the PAGE toggle button. The PageViewer module (`docs/page-viewer.js`) provides 3 sub-tabs:
- **Regionen:** Region cards with type label, ID, coordinates, text preview (color-coded: red=heading, grey=paragraph, blue=footnote, yellow=caption)
- **XML:** Syntax-highlighted PAGE-XML source
- **METS:** Document-level METS manifest (syntax-highlighted)

TEI and PAGE panels share the 3rd panel slot (mutual exclusion). Dashboard pipeline status tracks `page_xml` (286/286 docs).

---

## Stage 6a: Gemini Vision TEI Generator

**Script:** `scripts/tei/tei_gemini.py`

| Aspect | Details |
|--------|---------|
| Model | Gemini 3.1 Flash Lite Preview (`gemini-3.1-flash-lite-preview`) |
| Input | Overlay-PNG + OCR-Markdown + Layout-JSON + doc_metadata.json |
| Output | TEI-XML (DTA-Basisformat) with div hierarchy, lb, hi, persName, foreign, choice |
| Approach | Default: 1 call/page. Optional: --refine (2nd call), --consolidate (doc-level) |
| Cost | ~$0.005/page (1 call), TBD after sample run |
| Status | Pilot (Doc 2310 successful), E30 |

**Iterative Architecture:**

**Default (1 call/page):** Overlay-PNG + OCR + Layout + Metadata + Known Entities + Few-Shot -> complete TEI fragment with `<div>` hierarchy, `<pb>`, `<head>`, `<p>`, `<note>`, `<lb>`, `<hi>`, `<persName>`, `<foreign>`, `<choice>`, `break="no"`. Document assembled locally (teiHeader + page TEIs).

**Optional --refine:** 2nd Gemini call per page with overlay image, reviews and fixes markup quality (lb positions, entity tagging, formatting).

**Optional --consolidate:** API call for document-level consolidation (cross-page footnotes, entity consistency, div merging). Without this flag, pages are assembled locally with a generated teiHeader.

**Document-type-specific prompts (4 levels):**

| Level | Source | Examples |
|-------|--------|----------|
| Layout Type | `layout_type` in doc_metadata.json | A=single-column, B=two-column, C=monograph, D=special |
| Publication Form | `pub_form` in doc_metadata.json | journalArticle, book, bookSection, interview, encyclopedia |
| Genre | Inferred from `description` via keyword matching | 14 genres: article, review, interview, speech, debate, newspaper, conference, preface, letter, encyclopedia, editorial, essay, monograph |
| Language | `language` in doc_metadata.json | mono (fra/deu) or multilingual (fra/deu/ita) |

Genre inference (`infer_genre()`) and hint assembly (`build_doc_hints()`) are defined in `layout_qa_gemini.py` and reused by both layout prompts and TEI prompts.

**Output structure:**
```
output/tei_gemini/{doc_id}/
  {doc_id}_p{NNN}.xml          # Per-page TEI fragment (default)
  {doc_id}_p{NNN}_refined.xml  # Refined version (optional, --refine)
  {doc_id}_final.xml           # Assembled document (local) or consolidated (--consolidate)
  {doc_id}_manifest.json       # Timing, mode, model
  {doc_id}_eval.json           # Comparison with reference (if available)
```

**Evaluation (--evaluate):** For documents with reference TEI (`data/referenz-tei/`), computes element-level precision/recall for div, persName, bibl, lb, note, hi, foreign, choice, figure.

**Pilot results (Doc 2310, Typ A, Review, FR):** 3 pages, 54.5s total. persName recall 1.0, bibl recall 1.0, lb recall 1.0, div recall 1.0. Generated `<div type="review">`, `<bibl>` with GND reference, `<foreign>` tags, `break="no"` hyphenation. Qualitatively far superior to rule-based tei_generator.py.

**Reused functions:** `load_ocr_text()`, `load_layout()`, `get_document_metadata()` from `tei_generator.py`; `ensure_overlay()`, `build_doc_hints()`, `infer_genre()` from `layout_qa_gemini.py`; `discover_doc_ids()` from `utils.py`.

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

# Layout overlay images (stage 3b, no API key needed)
python -m scripts.generate_layout_overlays                 # Gemini overlays for all docs
python -m scripts.generate_layout_overlays --doc 2310      # single document
python -m scripts.generate_layout_overlays --compare        # + Docling-vs-Gemini side-by-side
python -m scripts.generate_layout_overlays --force          # overwrite existing

# Generate TEI-XML (stage 6, rule-based)
python -m scripts.tei.tei_generator                      # all documents
python -m scripts.tei.tei_generator --doc 2310           # single document
python -m scripts.tei.tei_generator --doc 2310 --page 2  # single page

# Gemini Vision TEI (stage 6a, requires GEMINI_API_KEY)
python -m scripts.tei.tei_gemini --doc 2310              # single document (1 call/page)
python -m scripts.tei.tei_gemini --doc 2310 --evaluate   # with reference comparison
python -m scripts.tei.tei_gemini --sample                # 3 pilot docs (2310, 2530, 1440)
python -m scripts.tei.tei_gemini --all                   # all 286 docs
python -m scripts.tei.tei_gemini --doc 2310 --refine     # + 2nd call/page for quality
python -m scripts.tei.tei_gemini --doc 2310 --consolidate # + API doc consolidation
python -m scripts.tei.tei_gemini --force                 # overwrite existing
python -m scripts.tei.tei_gemini --dry-run               # show prompts, no API calls

# Unified TEI Pipeline (stage 6b, PRODUCTION, requires GEMINI_API_KEY)
python -m scripts.tei.tei_unified --doc 2310             # single document (4 steps)
python -m scripts.tei.tei_unified --sample               # 3 pilot docs (2310, 2530, 1440)
python -m scripts.tei.tei_unified --all                  # all 286 docs
python -m scripts.tei.tei_unified --doc 2310 --step 1    # rule-based scaffold only (free)
python -m scripts.tei.tei_unified --all --validate       # include RelaxNG validation
python -m scripts.tei.tei_unified --force                # overwrite cached results
python -m scripts.tei.tei_unified --dry-run              # show prompts, no API calls

# TEI Validation (stage 6c, no API key needed)
python -m scripts.tei.tei_validator --doc 2310           # validate single document
python -m scripts.tei.tei_validator --all                # validate all unified TEI
python -m scripts.tei.tei_validator --report             # save JSON validation report

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

## Digitale Edition (E33)

**Directory:** `docs/edition/`

Public-facing digital edition for researchers and the general public, deployed on GitHub Pages alongside the internal pipeline dashboard. Separate design system, no modifications to the dashboard code.

### Architecture

| File | Purpose | Lines |
|------|---------|-------|
| `docs/edition/index.html` | Landing page: Hero, Featured Docs, Corpus Stats | ~102 |
| `docs/edition/catalog.html` | Document catalog: faceted filters, table/card views, MiniSearch | ~82 |
| `docs/edition/reader.html` | Reader: Faksimile + TEI side-by-side, entities, XML view | ~67 |
| `docs/edition/about.html` | About page: Hersch biography, project, pipeline, technology | ~138 |
| `docs/edition/css/edition.css` | Design system: `--ed-*` CSS vars, dark mode, responsive (3 breakpoints) | ~1300 |
| `docs/edition/js/edition-shared.js` | Shared module: Nav/Footer slot rendering, Dark Mode, catalog loader, card builder, utilities | ~283 |
| `docs/edition/js/edition-landing.js` | Landing page: metrics animation, featured docs, corpus stats | ~140 |
| `docs/edition/js/edition-catalog.js` | Catalog: MiniSearch (CDN), faceted filters, sort, table/card rendering | ~354 |
| `docs/edition/js/edition-reader.js` | Reader: page navigation, zoom, font toggle, draggable divider, entity sidebar | ~305 |
| `docs/edition/js/edition-tei.js` | TEI renderer: recursive node rendering, entity extraction, XML view | ~302 |
| `docs/edition/data/catalog.json` | Generated catalog data (from `scripts/generate_edition_data.py`) | -- |
| `scripts/generate_edition_data.py` | Data generator: reads dashboard.json + doc_metadata.json, outputs catalog.json, copies TEI XMLs | ~172 |

### Design System

- **Colors:** Parchment `#faf8f5` (bg), Scholarly Navy `#1e3a5f` (primary), Warm Gold `#b8860b` (accent)
- **Dark Mode:** `.dark` class on `<body>`, all `--ed-*` vars overridden
- **Typography:** Inter (UI), Source Serif 4 (reading), JetBrains Mono (code/XML)
- **Responsive:** 1200px (full), 768px (compact), 480px (mobile)

### Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| Separate from dashboard (`docs/edition/`) | Dashboard is internal QA tool; edition is public-facing |
| ES5/IIFE, `ZBZ.Edition` namespace | Consistent with dashboard convention, no build tools |
| Nav/Footer JS slot pattern (`#ed-nav-slot`) | DRY: nav/footer defined once in JS, HTML has empty slots |
| `buildCardHtml()` shared helper | DRY: card rendering used by landing + catalog |
| `sanitizeDocId()` for URL params | Security: only digits allowed, prevents path traversal |
| MiniSearch via CDN (~22KB) | Client-side fulltext search, no server needed |
| TEI renderer copied from `tei-viewer.js` | Reading-optimized version, no regression in dashboard viewer |
| CSS classes for TEI `<hi>` renditions | Replaces inline styles, maintainable via CSS |
| XML syntax colors as CSS custom properties | Automatic dark mode adaptation |
| 4 Demo docs (2310, 1000, 1330, 1540) | Same as dashboard demo, expandable to full corpus |

### Data Generation

```bash
python -m scripts.generate_edition_data   # Generate catalog.json + copy TEI XMLs
```

Reads `docs/data/dashboard.json` + `data/doc_metadata.json`. Outputs `docs/edition/data/catalog.json` (286 docs, corpus stats, featured list). Copies TEI XMLs for demo docs to `docs/data/examples/`.

---

## References

- [PROJEKT](PROJEKT.md) for ecosystem and milestones
- [ENGINES](ENGINES.md) for engine details
- [TESTPLAN](TESTPLAN.md) for test results
- [INFRASTRUKTUR](INFRASTRUKTUR.md) for deployment

---

*Created: 2026-01-29 | Renamed from ARCHITEKTUR.md: 2026-02-25 | Updated: 2026-03-06*
