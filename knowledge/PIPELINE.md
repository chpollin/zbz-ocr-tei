---
type: knowledge
created: 2026-01-29
updated: 2026-03-15
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
| 1a | Document classification (Gemini) | `scripts/classify_docs.py` | `data/doc_metadata.json` + `output/classification/` | Production (285 docs) |
| 2 | OCR | `scripts/ocr_pipeline.py` | Page-level Markdown (Mistral: `output/mistral_results/`, DeepSeek: `output/ocr_results/`) | Production |
| 2a | LLM post-correction (optional) | `scripts/llm_postprocess.py` | Corrected Markdown (`output/llm_corrected_c/`) | Production, E17: optional |
| 2b | Gemini OCR correction (optional) | `scripts/gemini_ocr_correct.py` | Corrected Markdown (`output/gemini_corrected_a/` or `_b/`) | Sample (5 docs), E29 |
| 3 | Layout analysis | `scripts/run_layout_analysis.py` (local GPU) or `scripts/run_layout_cloud.py` (docling-serve API) | Regions + BBox (JSON, `output/layout/`) + overlay PNGs | Production |
| 3a | Layout QA/Detect (Gemini) | `scripts/layout_qa_gemini.py` (3 modes: qa/detect/auto) | Corrected/detected regions (`_layout_gemini.json`) | Production (E25/E26/E31) |
| 3b | Layout Overlay Generator | `scripts/generate_layout_overlays.py` | Overlay PNGs + side-by-side compare | Production (E31) |
| 4 | Layout + OCR → PAGE-XML | `scripts/layout/page_xml_generator.py` + `mets_generator.py` | PAGE-XML + METS (`output/page_xml/`) | Production |
| 5 | **NER + Wikidata** | `scripts/ner/` (7 Module) | Entity JSON + TEI Indices (`data/entities/`) | **Production (285/285, E34/E35)** |
| 5a | NER Entity Extraction (Gemini) | `scripts/ner/ner_extract.py` | Per-page JSON (`output/entities/{doc_id}/`) | 285/285 Docs, 11,685 Entities, 26,197 Mentions |
| 5b | Entity Index (TEI-XML) | `scripts/ner/entity_index.py` | TEI Indices (`data/entities/*.xml`) | 4,504 Eintraege, 341 mit Wikidata |
| 5c | Wikidata Reconciliation | `scripts/ner/wikidata_linker.py` | Wikidata cache (`output/entities/_wikidata_cache.json`) | 67/285 Docs (15%), restliche pending |
| 5d | TEI Entity Injection | `scripts/ner/ner_inject_tei.py` | Enriched TEI (`output/tei_ner/`) | 285/285 Docs (Dual-Attribut E50: ref=GND + corresp=#zbz) |
| 5e | NER Evaluation | `scripts/ner/ner_evaluate.py` | Metrics (density, P/R/F1 vs GT) + HTML-Report | Done (output/ner_report.html) |
| 6 | Layout + OCR → TEI-XML (rule-based) | `scripts/tei/tei_generator.py` | TEI-XML (`output/tei/`) | Production |
| 6b | **Unified TEI Pipeline** (rule-based + Gemini) | `scripts/tei/tei_unified.py` | TEI-XML (`output/tei_unified/`) | **285/285, E32** |
| 6b+ | Post-Assembly Fixes | `scripts/tei/tei_step3.py` | Fix E/F/G + heuristische lb-Injection | Production (Session 34) |
| 6c | TEI Validation (RelaxNG + R1-R7 + W1-W14) | `scripts/tei/tei_validator.py` | JSON + HTML Report | **285/285 valid**, 29 Warnings |
| 7 | Evaluation + Dashboard | `scripts/evaluate_ocr.py` + `generate_dashboard_data.py` | Reports + `docs/data/dashboard.json` | Production (extension in Phase 4) |

**Curation Layer (E36, post-pipeline):** Manuelle Kuration ueber Browser-Editor (`scripts/server/curation_server.py`, localhost:8000). Nicht Teil der automatischen Pipeline, sondern editoriale Schicht darueber. Kuratiertes TEI in `data/tei_curated/` (git-tracked, Gold-Standard). TEI-Prioritaet: kuratiert > NER > unified > examples. Features: WYSIWYG Text-Editing, Block-Toolbar, Entity-Tagging mit Autocomplete, RelaxNG-Validierung, Review-Workflow (draft > in_review > approved). Publish: freigegebene Docs werden nach `docs/data/examples/` kopiert. Details: [CURATION](CURATION.md).

**Note on Stage 5 (E34/E35):** Post-hoc NER Pipeline via Gemini Flash Lite (6 Entity-Typen). 7 Module: `ner_extract`, `entity_store`, `entity_index`, `wikidata_linker`, `ner_inject_tei`, `ner_evaluate`. Architektur, ID-Schema und Wikidata-Strategie: siehe [GND-STRATEGIE](GND-STRATEGIE.md). Production Run (285 Docs): 11,685 Entities, 26,197 Mentions, 4,504 Index-Eintraege, 341 mit Wikidata-QIDs. Typ-Verteilung: person 36.7%, place 22.3%, date 15.0%, org 13.6%, work 10.8%, event 1.6%. Dual-Attribut-Strategie (E50): `ref="GND:{id}"` + `corresp="#zbz-{typ}.{N}"`. CLI: `--doc`, `--sample`, `--all`, `--force`, `--dry-run`.

**Note on Stage 6:** Stage 6 (rule-based) produces flat TEI structure. **Stage 6a (E30)** was Gemini Vision standalone (Pilot, deleted). **Stage 6b (E32)** is the production pipeline: enhanced rule-based scaffold (Step 1) + Gemini refinement (Step 2, mapping-table prompt) + document assembly (Step 3) + RelaxNG validation (Step 4, default active). Post-processing: `fix_gemini_tei()` (6 fix types), `reannotate_entities()`, interview speaker detection. CLI: `--doc`, `--sample`, `--all`, `--step`, `--skip-validate`, `--force`, `--dry-run`. OCR source priority: Gemini B > Gemini A > LLM C > Mistral.

**Stage 6c Validation Rules:** Zwei Ebenen: Errors (blockierend, valid=false) und Warnings (informativ fuer Editoren). **Errors:** RelaxNG-Schema (TEI-All) + R1 (type="naegeli"), R2 (teiHeader), R3 (body), R4 (min 1 div), R5 (gueltige div-types), R6 (note place). **Warnings:** W1 (Sprach-Code "und"), W2 (teiHeader title/author leer), W3 (facsimile/pb Mismatch), W4 (leere div), W5 (Text-Volumen <50 chars/Seite), W6 (keine lb-Elemente), W7 (graphic ohne url), W8 (keine Entity-Tags bei >500 Zeichen), W9 (Entity-Tags ohne ref), W10 (nur persName, keine orgName/placeName). HTML-Report: `--html-report` erzeugt `validation_report.html`.

**Entity-Tagging (Step 1+2):** `annotate_entities()` und `reannotate_entities()` nutzen den Entity Index fuer typkorrekte Tags (persName/orgName/placeName/bibl) mit interner ID als ref-Attribut (`#zbz-p.N`, `#zbz-o.N`, `#zbz-l.N`, `#zbz-w.N`). Alle 4 Entity-Typen werden getaggt (nicht nur Personen). Gemini-Prompt zeigt Entities nach Typ gruppiert. Interne IDs verlinken via Entity Index weiter auf Wikidata/GND.

**Quality Learnings (Session 26, 100-Doc Test):**
1. **Validierungs-Regeln muessen actionable sein:** Erste Version hatte 49/50 Docs mit Warnings (False Positives). Nach Bereinigung: 15/50. Jede Warning muss dem Editor eine konkrete Aktion ermoeglichen.
2. **Entity-Typ-Information darf nicht verloren gehen:** `annotate_entities()` muss den entity_type aus dem Index nutzen, nicht nur den Namen. Sonst wird alles `<persName>` -- auch Orte und Organisationen.
3. **Stopwort-Filter gegen False Positives:** Entity Index enthaelt generische Begriffe (Dieu, Monde, suisse). `_ENTITY_STOPWORDS` + Regel "kleingeschriebene Einzelwoerter ausschliessen" filtert ~66 problematische Eintraege.
4. **Seiten-Fragmente zu Dokument-Struktur mergen:** Pipeline erzeugt pro Seite einen `<div>`. ZBZ-Referenz hat immer 1 top-level div. `_merge_page_divs()` ist ein deterministischer Post-Assembly-Fix.
5. **Step-2-Cache invalidieren bei Aenderungen:** `--force` regeneriert Step 1+3, aber Step 2 kommt aus Cache (`_refined.xml`). Bei Prompt/Scaffold-Aenderungen muessen `_refined.xml` geloescht werden.
6. **Gemini-NER hat ~5-10% False Positives:** Inhaerent bei LLM-NER. Loesung: Curation Editor, nicht Code-Fix.
7. **Referenz-Vergleich fuer objektive Metriken:** `--compare-ref` vergleicht 11 Docs mit ZBZ-Referenz (CER, Struktur, Entity-Recall). CER-Streuung 0.4%-63.7% zeigt: einige Docs brauchen Aufmerksamkeit.
8. **Mehrsprachige Codes korrekt parsen:** "fra/deu" -> separate `<language>` Elemente. Betrifft ~40 Docs.
9. **facsimile/pb synchron halten:** Leere surfaces fuer Seiten ohne Layout-Zones.
10. **Interne IDs (zbz-p/o/l/w.N) als primaere Referenz:** Entity-Tags bekommen sofort die ID als ref. Wikidata/GND Verlinkung ueber Entity Index.
11. **Production-Run-Kommando:** `python -m scripts.tei.tei_unified --all --ner` (Cache) oder `--all --ner --force` (voll). Validation ist Default, HTML-Report automatisch.

### Quality Learnings (Session 26-27)

L1: Entity-Index hat Typ-Konflikte bei Namen die sowohl Person als auch Werk sind (Kierkegaard, Nietzsche). Person-Typ sollte Prioritaet haben.
L2: Gemini korrigiert OCR-Fehler im Step-2 Refinement (z.B. cruelé→croulé). Undokumentierter Qualitaetsgewinn.
L3: Generische Begriffe (La philosophie) werden faelschlich als Entity getaggt. Stopwort-Filter noetig.
L4: Doppelseiten-Scans (Buchformat) erzeugen W3, sind aber kein Fehler.
L5: JSTOR-Scans koennen mehrere Rezensionen pro Seite enthalten. Nicht automatisch loesbar.
L6: Abstrakte philosophische Texte haben weniger Entities als biographische — inhaltlich erklaerbar, kein Fehler.
L7: Multi-column newspaper layouts (Journal de Geneve, Cooperation, NZZ) systematically fail the pipeline. >40 zones cause OCR hallucinations, text duplication, and garbage. Affects ~3% of corpus. Fix: Manual cropping or specialized newspaper handler.
L8: Entity stopword list needs expansion: Mensch, Est, Gott, Rolle, Wahl, Christ, Schweizer, Zuercher, Zahler, Europaeer cause false positives in ~30% of docs.
L9: French "Est-ce que" pattern: "Est" consistently matched as placeName zbz-l.13. Needs language-aware entity filtering.
L10: Short docs (1-3 pages, Tier 1) have lower quality (40% APPROVED) than medium docs (4-8 pages, 85%+ APPROVED). Short docs are often newspaper clips with complex layouts.

Lessons from E16-E18: TEI page numbers != PDF page numbers (cover pages, blanks shift offset). Always match by content, not page number. Monographs (50-250 pages) need page-by-page comparison; global alignment fails above ~50 pages. Both layout versions preserved (_layout.json + _layout_gemini.json) -- in DH, provenance is as important as quality.

**Helper scripts:** `extract_pages.py` (page images), `postprocess/` (normalization).

**Layout engine (E19/E20):** Docling 2.75 (RT-DETR V2 Heron, 17 block types). Details: [ENGINES](ENGINES.md). Quality metrics: see Dashboard.

**Layout via API (E24):** `run_layout_cloud.py` sends page PNGs to a docling-serve instance (IBM's official API server for Docling). Same output format as `run_layout_analysis.py`. Server: `docker run -p 5001:5001 quay.io/docling-project/docling-serve-cpu`. CPU: ~27s/page, GPU (Cloud Run L4): ~28ms/page. Resume-capable, configurable via `DOCLING_SERVE_URL` env var. **Note:** Local GPU via `run_layout_analysis.py` is now preferred (~5s/page on RTX 4060).

**Automated Layout QA (E25):** `layout_qa_gemini.py --mode qa` sends Overlay-PNG + Layout-JSON to Gemini 3.1 Flash Lite Preview. Gemini corrects labels, removes false positives, flags missing regions. Returns corrected JSON with quality score (0-100). Both versions preserved: `_layout.json` (Docling original) + `_layout_gemini.json` (Gemini-corrected). Viewer supports toggle between both sources. SDK: `google-genai`. **Document-type-specific prompts (E30):** Prompts augmented with 4-level hints from `doc_metadata.json` (layout type, pub_form, genre, language) via `build_doc_hints(doc_id)`. Genre inferred from description text via `infer_genre()` (14 genres: article, review, interview, speech, debate, newspaper, conference, preface, letter, encyclopedia, editorial, essay, monograph).

**Gemini Layout Detect (E26):** `layout_qa_gemini.py --mode detect` uses Gemini 3.1 Flash Lite Preview as a full layout detector for pages where Docling fails. Sends raw scan (no overlay) to Gemini Vision with structured output schema. Returns regions with `box_2d` coordinates (0-1000 scale), converted to project format (`x_pct/y_pct/w_pct/h_pct`, 0-100%). Three modes: `--mode qa` (label correction), `--mode detect` (full re-detection), `--mode auto` (routes by Docling quality score — detect for bad/empty, qa for good/warning). Source field: `"gemini-detect"` vs `"gemini"` for QA.

**Full Run (E31):** `layout_qa_gemini.py --mode auto --force` on all docs. Per-page `changes_summary` logging (label transitions) and per-doc aggregation in `summary_gemini.json`. Results: see Dashboard. Visual QA: Gemini clearly better than Docling alone (more regions, missing headers/headings/footnotes recovered, two-column layouts correct).

**Layout Overlay Generator (E31):** `scripts/generate_layout_overlays.py` generates overlay PNGs from Gemini layout JSONs. Uses existing `draw_overlay_from_json()` from `scripts/layout/__init__.py`. Changed-highlighting: yellow border for ADDED regions, orange for label changes. Optional `--compare` flag generates side-by-side Docling-vs-Gemini images (2x width). Output: `_overlay_gemini.png` and `_overlay_compare.png` per page.

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

Sample results: see evaluation output. Both variants improve CER; Variant A slightly better on average and cheaper. Biggest improvement on docs with JSTOR covers and French accents.

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
python -m scripts.tei.tei_unified --skip-validate         # skip validation (default: active)
python -m scripts.tei.tei_unified --force                # overwrite cached results
python -m scripts.tei.tei_unified --dry-run              # show prompts, no API calls

# TEI Validation (stage 6c, no API key needed)
python -m scripts.tei.tei_validator --doc 2310           # validate single document
python -m scripts.tei.tei_validator --all                # validate all unified TEI
python -m scripts.tei.tei_validator --all --report       # save JSON validation report
python -m scripts.tei.tei_validator --all --html-report  # generate HTML quality report

# NER + Wikidata (stage 5, requires GEMINI_API_KEY for extraction)
python -m scripts.ner.ner_extract --doc 2310            # single document
python -m scripts.ner.ner_extract --sample               # 15 sample docs
python -m scripts.ner.ner_extract --all                  # all documents
python -m scripts.ner.ner_extract --doc 2310 --force     # overwrite existing
python -m scripts.ner.ner_extract --doc 2310 --dry-run   # show prompts, no API calls
python -m scripts.ner.entity_index --merge-all           # merge all stores into index
python -m scripts.ner.entity_index --stats               # index statistics
python -m scripts.ner.entity_index --report              # cross-doc consistency report (JSON)
python -m scripts.ner.wikidata_linker --doc 2310         # reconcile single document
python -m scripts.ner.wikidata_linker --all              # reconcile all
python -m scripts.ner.wikidata_linker --stats            # resolution statistics
python -m scripts.ner.ner_inject_tei --doc 2310          # inject entities into TEI
python -m scripts.ner.ner_inject_tei --doc 2310 --validate  # with RelaxNG validation
python -m scripts.ner.ner_inject_tei --all               # inject all documents
python -m scripts.ner.ner_evaluate --summary             # corpus metrics
python -m scripts.ner.ner_evaluate --doc 2310            # single doc report
python -m scripts.ner.ner_evaluate --doc 2310 --gt data/ground_truth/2310_gt.json  # P/R/F1

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

## Digitale Edition + Curation (E33/E36)

**Directory:** Edition: `docs/` | Infrastruktur: `docs/infrastruktur/` | **Details:** [EDITION](EDITION.md) (Architektur, Design System) | [CURATION](CURATION.md) (Edit-Modus, Server, API)

Oeffentliche digitale Edition auf GitHub Pages (Lese-Modus) mit optionalem Kurations-Modus (FastAPI Server). Zwei Modi, ein System: Reader, Katalog, Entity-Sidebar im Lese-Modus; Text-Korrektur, Struktur-Editing, Entity-Kuration, Review-Workflow im Edit-Modus.

```bash
python -m scripts.generate_edition_data        # Katalog-Daten generieren
python -m scripts.server.curation_server       # Edit-Modus starten (localhost:8000)
```

---

## References

- [PROJEKT](PROJEKT.md) for ecosystem and milestones
- [ENGINES](ENGINES.md) for engine details
- [TESTPLAN](TESTPLAN.md) for test results
- [INFRASTRUKTUR](INFRASTRUKTUR.md) for deployment

---

*Created: 2026-01-29 | Renamed from ARCHITEKTUR.md: 2026-02-25 | Updated: 2026-03-06*
