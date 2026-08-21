---
title: Pipeline
project:
  name: zbz-ocr-tei
  repository: https://github.com/chpollin/zbz-ocr-tei.git
method:
  name: Promptotyping
  url: https://dhcraft.org/Promptotyping/
template:
  name: Vorlage Architecture
  version: 0.3
  url: https://dhcraft.org/Promptotyping/promptotyping-document/architecture
status: complete
language: en
version: 1.0
created: 2026-01-29
updated: 2026-08-21
authors: [Christopher Pollin]
related: [project, data, specification, tei-mapping, workflow, infrastructure, integration, testing, plan]
---

# Pipeline

Data flow from PDF to TEI-XML with its stages, scripts and engines. Since the scope
expansion (25.02.2026, E21) zbz-ocr-tei covers the entire path.

CLI reference and operational tools are in [CLAUDE.md](../CLAUDE.md), Commands section.
The markup rules the generator applies are in [tei-mapping.md](tei-mapping.md). The
end-to-end workflow with viewer, save mechanism and provenance is in
[workflow.md](workflow.md), the delivery status per milestone in [plan.md](plan.md).

## Overview

```
PDF
 |
 v
Images (extract_pages.py)
 |
 +------------------------------+
 v                              v
OCR (base text layer)          Layout (Docling + Gemini QA)
 |                              |
 |                              +--> PAGE-XML (page_xml_generator.py)
 |                              |    = parallel export for coOCR
 |                              |    NOT TEI input (E22)
 |                              |
 +------------------------------+--> TEI-XML (tei_unified.py)
                                     |
                                     v
                                     Workflow status per stream (E66, human-set)
                                     |
                                     v
                                     Evaluation + Viewer
```

PAGE-XML is an export that runs beside the TEI path rather than a station on it (E22, a
recurring misreading). TEI is generated DIRECTLY from layout JSON plus OCR Markdown
via `scripts/tei/tei_unified.py`, and PAGE-XML is produced in parallel for coOCR and
Transkribus (E13). Both derive independently from layout JSON plus OCR.

| Stage | Task | Script | Output | Status |
|---|---|---|---|---|
| 1 | PDF -> PNG | `scripts/edition/extract_pages.py` | PNG (`docs/images/`) | Production |
| 1a | Document classification (Gemini) | `scripts/ocr/classify_docs.py` | `data/doc_metadata.json` + `output/classification/` | Production (full corpus, E27) |
| 2 | OCR | `scripts/ocr/ocr_pipeline.py` (`--engine auto` resolves to Gemini, `-e mistral` reproduces the delivered corpus) | page Markdown (`output/mistral_results/`) | Production |
| 2a | LLM post-correction (optional) | `scripts/ocr/llm_postprocess.py` | `output/llm_corrected_c/` | Production, E17: optional |
| 2b | Gemini OCR correction (optional) | `scripts/ocr/gemini_ocr_correct.py` | `output/gemini_corrected_a/` / `_b/` | Sample (E29) |
| 3 | Layout analysis | `scripts/layout/run_layout_analysis.py` (local GPU) or `run_layout_cloud.py` (docling-serve) | regions + bbox (`output/layout/`) | Production |
| 3a | Layout QA/detect (Gemini) | `scripts/layout/layout_qa_gemini.py --mode {qa\|detect\|auto}` | `_layout_gemini.json` | Production (E25/E26/E31) |
| 3b | Overlay generator | `scripts/layout/generate_layout_overlays.py` | PNGs + side-by-side compare | Production |
| 4 | PAGE-XML + METS | `scripts/layout/page_xml_generator.py` + `mets_generator.py` | `output/page_xml/` | Production |
| 5 | TEI-XML (rule-based) | `scripts/tei/tei_generator.py` | `output/tei/` | Production |
| 5b | Unified TEI Pipeline (E32) | `scripts/tei/tei_unified.py` | `output/tei_unified/` | Production (full corpus) |
| 5b+ | Post-assembly fixes | `tei_step3.py` | fixes E/F/G + heuristic lb injection | Production (Session 34) |
| 5c | TEI validation | `scripts/tei/tei_validator.py` | JSON + HTML report | schema-valid across the delivered corpus (gate: `tests/test_tei_schema.py`); warnings informative (rule catalog in [specification.md](specification.md), current tallies via `python -m scripts.tei.tei_validator --all --report`) |
| 6 | Evaluation | `scripts/eval/evaluate_ocr.py` + `benchmark_cer.py` + `cer_statistics_full.py` | `output/evaluation/` + `docs/data/cer_statistics.json` | Production |

Manual curation (E56) takes place in the pipeline viewer (`docs/viewer.html`) with layout
and transcription editor. A single save writes canonically to `output/` and to the
`docs/data/` mirror (File System Access API, download fallback, E72/E78/E79). The curated
files return into the pipeline through `tei_unified --reassemble`, which selectively
re-refines the changed pages; the round trip with its step sequence, the save mechanism
and the editors are described in [workflow.md](workflow.md), round-trip section.

Quality assurance (E66): the pipeline asserts no verification state of its own. A human
sets the workflow status per stream in the viewer; `tei_status_marker.py` projects that
status deterministically into the `<revisionDesc>` of the final TEI (XML shape in
[tei-mapping.md](tei-mapping.md), revision description section). Status values,
traffic-light mapping, history semantics and the streams they cover are described in
[workflow.md](workflow.md), workflow status section.

OCR quality is measured rather than asserted. The measurement method is in
[cer-methodology.md](cer-methodology.md), the requirement in
[specification.md](specification.md), the verification of the published claim in
[verification.md](verification.md), and the measured values in
`docs/data/cer_statistics.json`. The measuring instruments are
`scripts/eval/benchmark_cer.py`, `scripts/eval/cer_statistics.py` and
`scripts/eval/cer_statistics_full.py`.

Where the pipeline output is published and which facsimiles the online demo carries is
described in [infrastructure.md](infrastructure.md), GitHub Pages section.

## Engines

Active engines in two roles. Pipeline design carries more weight than model choice, since
the investments that pay off are chunking, page matching and quality routing. LLM
post-correction hurts at CER below five per cent (E17).

`ocr_pipeline --engine auto` resolves to Gemini
([ocr_pipeline.py](../scripts/ocr/ocr_pipeline.py), lines 295 to 298), which makes Gemini
the default text engine, while Mistral stays selectable as the reproducibility record of the
delivered corpus; the engine roles, endpoints and credentials are owned by
[infrastructure.md](infrastructure.md), engine roles section. The loader priority in
[scripts/core/loaders.py](../scripts/core/loaders.py) reads the base text layer
`output/mistral_results/` last, behind curated text, the two Gemini correction variants and
the LLM-corrected variant.

The layout hybrid was decided on 25.02.2026 after a comparative engine evaluation, with Docling as the
bbox engine and Gemini as validator and detect fallback; the rationale is registered as
E19 and E20 in [decisions.md](decisions.md).

### Mistral Document AI: the delivered text layer

| Aspect | Details |
|---|---|
| Model | `mistral-document-ai-2512` on Azure AI Foundry (serverless API) |
| Role | produced the delivered text layer of the corpus and stays selectable as its reproducibility record |
| Speed | ~1.3 s/page |
| Output | per-page Markdown (`output/mistral_results/{doc_id}_p{N}.md`) |
| Languages | 36 (de, fr, en, es, it, ...) |
| Endpoint | `https://<deployment>.<region>.models.ai.azure.com/v1/ocr` (answers 401) |
| Limit | 30 pages/request, 30 MB max (pipeline splits automatically) |

Setup notes and error diagnosis are in [infrastructure.md](infrastructure.md), section
Mistral Document AI on Azure.

### Docling 2.75: Layout Primary

| Aspect | Details |
|---|---|
| Model | RT-DETR V2 Heron (42.9M, IBM Research, DocLayNet) |
| Role | primary layout engine (layout only, no OCR; RapidOCR has FR encoding problems) |
| Speed | ~5 s/page (RTX 4060 GPU), ~27 s/page (CPU / docling-serve) |
| Detection | 17 block types (Title, Section-header, Text, Footnote, Caption, Page-header/footer, Picture, Table, Formula, ...) |
| API | `scripts/layout/run_layout_cloud.py` -> docling-serve (Docker, IBM official) |

Coverage-based quality scoring is a strong proxy for layout quality; no ML needed.
Landscape and multi-column pages are the hard cases (~64% bad vs. ~14% portrait).

### Gemini 3.1 Flash Lite: Layout QA + Detect + Refinement

| Aspect | Details |
|---|---|
| Model | `gemini-3.1-flash-lite-preview` |
| Roles | layout correction, layout detect (fallback for Docling failures, ~15%), document classification, OCR correction, vision OCR (`-e gemini`, writes to `output/mistral_results/`), TEI refinement |
| SDK | `google-genai` |

3 modes in `layout_qa_gemini.py`:
- `--mode qa`: overlay PNG + layout JSON to Gemini, labels corrected, false positives removed, quality score 0-100
- `--mode detect`: full re-detection with `box_2d` coordinates (0-1000 scale -> x_pct/y_pct/w_pct/h_pct)
- `--mode auto`: routes per page via `compute_page_quality()` (detect for bad/empty, qa for good/warning)

The routing value is an area coverage. `compute_page_quality`
([layout_qa_gemini.py](../scripts/layout/layout_qa_gemini.py), lines 319 to 344) returns a
quality class, an area-coverage value and the region count per page; its single call site
(line 691) sends a page below the threshold into re-detection and prints the coverage. The
quality figure that reaches a layout JSON is the Gemini `score` (line 239), so the coverage
steers the run while the score is what later stages read.

Structured outputs via `response_schema`. Both versions are kept (`_layout.json` +
`_layout_gemini.json`); in DH, provenance is as important as quality.

## TEI mapping

The generator follows the markup rulebook in [tei-mapping.md](tei-mapping.md), which holds
the document structure, page breaks, character normalization, highlighting, special
structures, figures, omissions, the entity target model, the facsimile binding, the
revision description and the element inventory of the delivered corpus. The three stages
of `tei_unified.py` divide the work between them. Step 1
([tei_step1.py](../scripts/tei/tei_step1.py)) builds the rule-based scaffold from layout
JSON and OCR Markdown and produces one body fragment plus its facsimile zones per page.
Step 2 ([tei_step2.py](../scripts/tei/tei_step2.py)) refines each page fragment through
Gemini inside the schema subset and repairs the recurring model errors. Step 3
([tei_step3.py](../scripts/tei/tei_step3.py)) assembles the document, writes the header
and the facsimile block and applies the post-assembly fixes. Since the generator sees one
page at a time, document-level and cross-page structures stay with curation; the rulebook
states which phenomena those are.

## Entity stage (preview layer)

A controlled entity layer sits beside the TEI stages and writes read-only previews. It
binds mentions to the curated ZBZ entity list with a deterministic matcher, marks sure
hits, and parks ambiguous candidates on a review worklist. The markup rules and the
provenance vocabulary are in [tei-mapping.md](tei-mapping.md), the measured precision and
recall in [verification.md](verification.md), the gates in [testing.md](testing.md), and
the open milestones together with the instruments still to be built in [plan.md](plan.md).
The curated list, the GND variant cache, the legacy mention index, the variant review and
the marking policy are described as input data in [data.md](data.md).

One rule binds the whole stage, nothing writes into `output/tei_final/`.
`tei_entity_preview.py` refuses that directory outright, and the operator-gated stock tool
`scripts/entity/tei_entity_marker.py` remains to be built ([plan.md](plan.md), phase A).

| Instrument | Reads | Writes |
|---|---|---|
| `scripts/entity/fetch_gnd_variants.py` | `data/entities/all_entities.json`, lobid | `data/entities/gnd_cache.json` |
| `scripts/entity/entity_lint.py` | entity list, GND cache, legacy mention index, marking policy | `output/audits/entity_lint.json` |
| `scripts/entity/entity_lexicon.py` | entity list, GND cache, variant review, legacy mentions, marking policy | the in-memory lexicon (headwords, inverted forms, cache variants, legacy surfaces, derived-form channels) |
| `scripts/entity/entity_matcher.py` | the lexicon plus a TEI document | candidates with exact offsets, tier and rule; re-exports the lexicon API, so both read as one module from outside |
| `scripts/entity/running_heads.py` | the page-head lines of a document | the running-head zones the matcher demotes into tier 2 |
| `scripts/entity/running_head_audit.py` | scan snapshot, adjudicated verdicts | running-head validation report under `output/audits/` |
| `scripts/entity/tei_entity_preview.py` | `output/tei_final/` read-only, entity data, verdict store | `output/entity_preview/` plus a JSON report |
| `scripts/entity/entity_corpus_scan.py` | `output/tei_final/` read-only, entity data | `output/audits/entity_corpus_scan.json` |
| `scripts/entity/entity_corpus_digest.py` | scan snapshot, entity list | `output/audits/entity_corpus_digest.md` |
| `scripts/entity/entity_unlisted_scan.py` | `output/tei_final/`, entity data, viewer catalog | `output/audits/entity_unlisted_report.json` plus a CSV |
| `scripts/entity/entity_gold_benchmark.py` | the 25 reference TEIs, entity data | `output/audits/entity_gold_benchmark.json` |
| `scripts/entity/entity_eval_sample.py` | scan snapshot, catalog, delivered TEI | `output/audits/eval_sample/` with precision cases, recall pages and the sample manifest |
| `scripts/entity/build_mention_verdicts.py` | frozen scan snapshot, adjudication files under `output/audits/eval_sample/verdicts/` | `data/entities/mention_verdicts.json` |
| `scripts/entity/entity_verdict_guard.py` | verdict store, current scan snapshot | `output/audits/verdict_guard_report.json`, exit 1 on a violation |
| `scripts/entity/entity_risk_ranking.py` | scan snapshot, entity list | `output/audits/fp_hunt/risk_ranking.json` beside its wave protocol |
| `scripts/entity/generate_entity_preview_data.py` | `output/entity_preview/` read-only | `docs/data/pages/{doc}/{doc}_entity_p{N}.xml`, `{doc}_entity_worklist.json`, `docs/data/entities.json` |
| `scripts/entity/generate_entity_overview.py` | scan snapshot, entity list, verdict store | `docs/data/entity_overview.json` for `docs/entities.html` |
| `scripts/tei/tei_cover_strip.py` | `output/tei_final/` | operator-gated cover-sheet removal with backup, report under `output/audits/` |

The variant review is an operator-gated channel rather than a script.
`data/entities/variant_review.json` carries one verdict per cache-derived name form
(approve, suspect, reject, each with a reason), and `build_lexicon` consumes it
deterministically. A rejected form stays out of the lexicon, a suspect form yields tier-2
candidates only, and a cache form the review does not know counts as suspect until the
next review pass. Headwords of the curated list and legacy forms stay outside its reach.
The operator worklist of all suspect and reject forms lands in
`output/audits/variant_review_report.md`.

Four contracts hold the stage together. The matcher returns candidates that are
offset-verified, non-overlapping and embed at most `lb` tags, and it excludes everything
outside `text` as well as figures, bibliography divs and already marked elements. The
preview run proves per document that the result is RelaxNG-valid against `zbz_hersch.rng`,
that the text of the `text` subtree is character-identical, and that the bytes outside the
insertions are unchanged, so stripping the wrappers and the header declarations restores
the original. The corpus scan is a diffable snapshot, which lets a rule change show its
exact corpus effect before it binds, and a frozen copy of that snapshot is what an
adjudication wave draws from. The verdict store keys a judgment by document, page, surface,
identifier and occurrence index over the frozen snapshot and carries a sha256 fingerprint
of the TEI it was judged on, so a later text change marks the affected records stale for
re-adjudication.

The viewer shows the previews read-only under `viewer.html?doc={DOC_ID}&entities=1` with
category colours, a popover per mention and a per-page worklist panel; the rendering is
described in [workflow.md](workflow.md), entity layer section.

## ZBZ Structural Tags (Docling -> ZBZ -> PAGE-XML)

| Docling | ZBZ | PAGE-XML |
|---|---|---|
| Title, Section-header | `zb_heading` | heading |
| Text, Paragraph, List-item, Table, Formula | `zb_paragraph` | paragraph |
| Footnote | `footnote` | footnote |
| Caption | `caption` | caption |
| Page-header, Page-footer | `_filter` | (removed) |
| Picture, Figure | `_skip` | - |

The PAGE-XML of stage 4 also travels outbound as a Transkribus bundle; folder convention,
dialect and upload are in [integration.md](integration.md), Transkribus section.

## References

- [tei-mapping.md](tei-mapping.md): the markup rulebook the generator applies
- [workflow.md](workflow.md): data flow, viewer with layout and transcription editor, persistence, round trip
- [data.md](data.md): corpus, delivery tree, entity input data, reference corpus
- [specification.md](specification.md): requirements, quality method, validation rule catalog
- [testing.md](testing.md): test strategy and the gates that hold the pipeline contracts
- [verification.md](verification.md): the verified quality claims and their finding register
- [integration.md](integration.md): ZBZ, Transkribus and teiCrafter contracts
- [infrastructure.md](infrastructure.md): Azure, containers, CI, GitHub Pages delivery
- [plan.md](plan.md): open milestones and deferred work
- [decisions.md](decisions.md): decision register
- [methodology.md](methodology.md): Promptotyping, verification cascade, work cycle
