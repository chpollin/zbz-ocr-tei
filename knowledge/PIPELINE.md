---
type: knowledge
created: 2026-01-29
updated: 2026-02-27
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
| 2 | OCR | `scripts/ocr_pipeline.py` | Page-level Markdown (`output/mistral_results/`) | Production |
| 2a | LLM post-correction (optional) | `scripts/llm_postprocess.py` | Corrected Markdown (`output/llm_corrected_c/`) | Production, E17: optional |
| 3 | Layout analysis | `scripts/run_layout_analysis.py` | Regions + BBox (JSON, `output/layout/`) + overlay PNGs | Production (7/15 docs) |
| 4 | Layout + OCR → PAGE-XML | `scripts/layout/page_xml_generator.py` | PAGE-XML + METS (`output/page_xml/`) | **Phase 1** |
| 5 | NER + GND | `scripts/ner/ner_pipeline.py` + `gnd_linker.py` | Entity JSON (`output/entities/`) | **Phase 2** |
| 6 | Layout + OCR → TEI-XML | `scripts/tei/tei_generator.py` | TEI-XML (`output/tei/`) | Production (15/15 docs, 383 files) |
| 7 | Evaluation + Dashboard | `scripts/evaluate_ocr.py` + `generate_dashboard_data.py` | Reports + `docs/data/dashboard.json` | Production (extension in Phase 4) |

**Note on Stage 6:** The TEI generator currently goes directly from layout JSON + OCR Markdown to TEI-XML, without PAGE-XML as an intermediate format. PAGE-XML (Stage 4) and NER (Stage 5) are not yet implemented — once they are, the TEI generator will be extended accordingly.

**Helper scripts:** `extract_pages.py` (page images), `extract_gnd.py` (GND IDs), `postprocess/` (normalization).

**Layout engine (E19):** Docling 2.75 (RT-DETR V2 Heron, 17 block types, CPU). Phase 0 evaluation passed: all 4 document types correctly recognized, column separation Type B works. Details: [E19-LAYOUT-ANALYSE](E19-LAYOUT-ANALYSE.md).

**Layout QA (25.02.2026):** Visual inspection of 8 docs (186 overlay PNGs) showed:
- BBox positioning correct, no systematic offset
- Headings reliably detected (titles, subtitles, thesis numbers)
- Two-column layout correctly separated (Doc 1410)
- **3 issues identified (O21):** (1) Overlapping regions in dense text, (2) single-line fragments as separate regions, (3) page numbers detected as `text` instead of `page_footer`
- Post-processing needed: overlap filter, single-line merge, page number heuristic

---

## Stage 1: OCR

**Script:** `scripts/ocr_pipeline.py`

### Engine Selection (Auto mode in `ocr_pipeline.py`)

1. Document in `TWO_COLUMN_DOCS`? → Docling (Layout) + DeepSeek
2. `MISTRAL_DOC_AI_KEY` set? → Mistral Document AI (API)
3. Otherwise → DeepSeek (local, GPU)

Document types: See [QUELLENANALYSE](QUELLENANALYSE.md) §Document Types.
Engine details: See [OCR-ENGINES](OCR-ENGINES.md).

### Layout Analysis (Type B only)

For two-column documents, `ocr_pipeline.py` internally uses Docling (IBM) with `do_ocr=False` for column detection. Docling's own OCR is not used (RapidOCR has encoding issues). Details: [OCR-ENGINES](OCR-ENGINES.md) §Docling.

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

### Prompts (3 Variants)

All prompts in `llm_postprocess.py`. Variant C is the default (E17).

**Variant A (Analysis)** — System prompt with `<analysis>` + `<corrected>` blocks:
```
Du bist ein Experte fuer OCR-Nachkorrektur akademischer Texte des 20. Jahrhunderts
von Jeanne Hersch (Philosophin, 1910-2000). Du erhaeltst OCR-Output aus gescannten
Dokumenten und korrigierst Zeichenfehler.

Regeln:
- Korrigiere NUR OCR-Fehler (falsche Buchstaben, fehlende Akzente, zusammengeklebte Woerter)
- Formuliere NICHTS um, erfinde NICHTS
- Markdown beibehalten
- Maschinenerzeugte Artefakte (JSTOR-Header, Copyright-Zeilen) entfernen
- Im Zweifel: unveraendert lassen

{Sprach-Hint}

Antwortformat: 1. <analysis>-Block mit Fehlerliste, 2. <corrected>-Block mit Text
```

**Variant B (Lean)** — Corrected text only, no analysis block:
```
Korrigiere OCR-Fehler im folgenden Text. [Gleiche Regeln wie A, ohne Antwortformat]
Gib NUR den korrigierten Text aus, ohne Erklaerungen.
```

**Variant C (Few-Shot, Default)** — Like B, plus typical Mistral OCR errors as examples:
```
...
Typische OCR-Fehler dieser Engine (Mistral Document AI):
- 'inconnaisable' -> 'inconnaissable' (fehlender Buchstabe)
- 'etrente' -> 'etreinte' (falsche Zeichenfolge)
- 'seule tu le courant' -> 'sens-tu le courant' (Wortgrenze falsch)
- 'rereferme' -> 'se referme' (zusammengeklebte Woerter)
- 'lisse, comme' -> 'hisse, comme' (aehnliche Buchstaben)
- 'This content downloaded from...' -> entfernen (JSTOR-Artefakt)
Gib NUR den korrigierten Text aus, ohne Erklaerungen.
```

**Language hints** (dynamically inserted, `_lang_hint()` in `llm_postprocess.py:62`):

| Language | Hint |
|----------|------|
| FR | Achte auf Akzente, Guillemets, Apostrophe (l', d', qu') |
| DE | Achte auf Umlaute, Eszett, Komposita |
| DE/FR | Achte auf Umlaute UND Akzente |

**User message template** (per page, `build_user_message()` in `llm_postprocess.py:136`):
```
Dokument: {doc_id}
Typ: {doc_type} ({Einspaltig|Zweispaltig|Monografie|Spezialformat})
Sprache: {language}
Genre: {genre}
OCR-Engine: Mistral Document AI
Seite: {page_num} von {total_pages}

<ocr_text>
{ocr_text}
</ocr_text>
```

### Variant Comparison (Phase 1-3, 10 Docs)

| Variant | Avg CER | Notes |
|---------|---------|-------|
| A (Analysis) | 5.47% | Best CER, but more expensive (longer output) |
| B (Lean) | 5.59% | Cheapest |
| C (Few-Shot) | 5.55% | Best CER/cost tradeoff → Default |

**Pilot results (all 15 docs, Variant C Few-Shot):**

| Phase | Mistral CER | LLM CER | Delta |
|-------|-------------|---------|-------|
| Phase 1 (A) | 9.40% | 8.43% | -0.97 |
| Phase 2 (B) | 6.31% | 6.34% | +0.03 |
| Phase 3 (D) | 2.88% | 2.72% | -0.16 |
| Phase 4 (C) | 2.65% | 2.70% | +0.05 |
| **Total (15 Docs)** | **6.42%** | **6.52%** | **+0.10** |

**Findings:** LLM correction improves docs with CER >10%, slightly degrades quality for good OCR (<5%). Recommendation: use optionally, not as default.

### Optimization Potential (Research 25.02.2026)

| Idea | Expected Effect | Effort | Source |
|------|-----------------|--------|--------|
| **Multimodal correction** (scan image + OCR text) | <1% CER per research | Medium (Sonnet/Opus needed, higher cost) | [arXiv:2504.00414](https://arxiv.org/abs/2504.00414) |
| Larger model (Sonnet instead of Haiku) | Better for FR (training data) | Low (config change only) | [ACL 2025](https://arxiv.org/abs/2502.01205) |
| Segment length 200-300 words | Optimal per study; we send full pages — already good | None | [ACL 2025](https://arxiv.org/abs/2502.01205) |

**Risk:** 66% of our corpus is French. Studies show that LLM correction for non-English texts often has a negative effect — confirming our observation (Phase 2/4: slight degradation).

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

# OCR (stage 1)
python scripts/ocr_pipeline.py -i data/scans/2310.pdf -e mistral
python scripts/ocr_pipeline.py --all --engine auto

# LLM post-correction (stage 2, requires ANTHROPIC_API_KEY)
python -m scripts.llm_postprocess --phase phase1 --variant C
python -m scripts.llm_postprocess --all

# Evaluation (stage 3)
python scripts/evaluate_ocr.py --all
python scripts/evaluate_ocr.py --phase phase1 --engine mistral

# Layout analysis (stage 3, requires GPU for Docling)
python -m scripts.run_layout_analysis                      # all documents
python -m scripts.run_layout_analysis --doc 2310           # single document
python -m scripts.run_layout_analysis --overlay            # Generate overlay PNGs (no GPU)
python -m scripts.run_layout_analysis --overlay --doc 2310 # Overlay for single document

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

The dashboard shows pipeline status, CER comparison (Mistral/LLM/DeepSeek), engine availability, and a filterable document catalog. Data is statically generated from pipeline outputs. TEI rendering (rendered view, XML highlighting, reference diff, entity sidebar) is in `tei-viewer.js`.

---

## References

- [PROJEKT](PROJEKT.md) for ecosystem and milestones
- [OCR-ENGINES](OCR-ENGINES.md) for engine details
- [TESTPLAN](TESTPLAN.md) for test results
- [INFRASTRUKTUR](INFRASTRUKTUR.md) for deployment

---

*Created: 2026-01-29 | Renamed from ARCHITEKTUR.md: 2026-02-25 | Updated: 2026-02-27 (PAGE-XML Schema 2019→2013 after E23)*
