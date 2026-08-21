---
title: Decisions
project:
  name: zbz-ocr-tei
  repository: https://github.com/chpollin/zbz-ocr-tei.git
method:
  name: Promptotyping
  url: https://dhcraft.org/Promptotyping/
status: active
language: en
version: 1.0
created: 2026-02-18
updated: 2026-08-21
authors: [Christopher Pollin]
related: [index, journal, specification, project, verification]
absorbed: [plan (Vorlage Plan 0.2)]
---

# Decisions

Consolidated register of the decisions taken in the project, cross-cutting and collected from all documents. Entries are dated records. A later correction is added as an inline update annotation inside the entry it corrects, and an entry is never rewritten silently. The plan block below holds the forward programme with its milestones, its open decisions and its deviations. The chronological course of the work lives in [journal.md](journal.md).

## Decided (E1-E63)

| # | Decision | Rationale | Date | Document |
|---|---|---|---|---|
| E1 | Hybrid pipeline: Docling (layout) plus LLM OCR (text) | layout analysis without OCR, OCR separate | 2026-01-29 | [pipeline.md](pipeline.md) |
| E2 | Docling for layout only, not for OCR | RapidOCR has encoding problems (`e -> O`) on French | 2026-01-29 | [pipeline.md](pipeline.md) |
| E3 | Deterministic first, LLM only for complex cases | reproducible, cost-efficient, debuggable | 2026-01-29 | [pipeline.md](pipeline.md) |
| E4 | Four document types (A-D) classified | different pipeline strategies | 2026-01-29 | [project.md](project.md), data section |
| E6 | Mistral OCR 3 as production engine | ZBZ has Azure access, no GPU needed | 2026-02-14 | [pipeline.md](pipeline.md) |
| E7 | Fee unchanged | Azure integration without extra cost | 2026-02-14 | [project.md](project.md) |
| E8 | Configurable API endpoints | switch between local and Azure | 2026-02-14 | [pipeline.md](pipeline.md), deployment section |
| E9 | Containerisation with Podman | ZBZ does not use Docker; Podman is OCI-compatible | 2026-02-14 | [pipeline.md](pipeline.md), deployment section |
| E10 | Fork on GitLab University of Zurich | ZBZ runs its own instance | 2026-02-14 | [project.md](project.md), integration section |
| E13 | Export as PAGE-XML plus METS for coOCR | coOCR expects PAGE-XML 2013-07-15 plus PNG | 2026-02-20 | [project.md](project.md), integration section |
| E14 | Preserve Markdown formatting | coOCR stores text as-is in `<Unicode>` | 2026-02-20 | [pipeline.md](pipeline.md) |
| E15 | Dashboard redesign: multi-page UI with shared CSS/JS | unified design system, static JSON data | 2026-02-25 | [pipeline.md](pipeline.md) |
| E16 | Page-by-page comparison for monographs (>10 TEI pages) | global alignment fails from ~50 pages | 2026-02-25 | [pipeline.md](pipeline.md) |
| E17 | LLM correction optional, not default | degrades documents with CER below 5 % | 2026-02-25 | [pipeline.md](pipeline.md) |
| E18 | Content-based page matching instead of fixed offset | TEI facs numbers differ from PDF pages | 2026-02-25 | [pipeline.md](pipeline.md) |
| E19 | Layout: Docling plus Gemini hybrid | Docling mAP 0.699, 17 classes, free; Gemini as validator | 2026-02-25 | [pipeline.md](pipeline.md) |
| E20 | Docling 2.75 confirmed as layout engine | type sample passed, 0.4-3.3 s/page | 2026-02-25 | [pipeline.md](pipeline.md) |
| E21 | Scope expansion: full pipeline in zbz-ocr-tei | meeting 2026-02-25: OCR plus layout plus PAGE-XML plus NER plus TEI | 2026-02-25 | [pipeline.md](pipeline.md) |
| E22 | TEI generator directly from layout plus OCR (no PAGE-XML) | extended later for NER/PAGE-XML | 2026-02-25 | [pipeline.md](pipeline.md) |
| E23 | Data delivery Feb 2026: 286 PDFs, 25 TEI-XML, 24 PAGE-XML exports | PAGE-XML schema 2013-07-15, empty | 2026-02-27 | [project.md](project.md), data section |
| E24 | docling-serve API for layout (no local GPU) | Docker container, identical output format | 2026-03-03 | [pipeline.md](pipeline.md) |
| E25 | Gemini 3.1 Flash Lite as layout QA validator | overlay PNG plus layout JSON to corrected JSON, structured output | 2026-03-03 | [pipeline.md](pipeline.md) |
| E26 | Gemini layout detect mode | Docling fails on ~15 % (landscape, multi-column); three modes qa/detect/auto | 2026-03-04 | [pipeline.md](pipeline.md) |
| E27 | Gemini document classification (stage 1a) | 271/286 without metadata, heuristics fail (7/15 wrong) | 2026-03-05 | [pipeline.md](pipeline.md) |
| E28 | Online demo: 4 demo documents on GitHub Pages | full data local only (gitignored) | 2026-03-05 | [pipeline.md](pipeline.md), deployment section |
| E29 | Gemini OCR correction stage 2b | two-step (analysis plus correction), variants A/B | 2026-03-05 | [pipeline.md](pipeline.md) |
| E30 | Gemini vision TEI generator plus type-specific prompts | four-level prompts (layout type, pub form, genre, language), 12 genre prompts | 2026-03-06 | [pipeline.md](pipeline.md) |
| E31 | Layout QA full run plus overlay generator | `--mode auto --force` over 286 documents, 14,708 corrections | 2026-03-06 | [pipeline.md](pipeline.md) |
| E32 | Unified TEI pipeline (scaffold plus Gemini plus assembly) | four stages, 50/50 VALID in the pilot | 2026-03-07 | [pipeline.md](pipeline.md) |
| E33 | Digital edition (`docs/`) | public website next to the internal dashboard | 2026-03-06 | superseded by E56 |
| E34 | NER pipeline plus entity index (phase 3) | post-hoc NER via Gemini Flash Lite (6 types), Wikidata as primary id | 2026-03-07 | removed by E71 |
| E35 | NER production-ready (phase 3 scale-up) | seven quality improvements before the production run | 2026-03-08 | removed by E71 |
| E36 | Curation editor (editor in the loop) | FastAPI server, 11 API endpoints, WYSIWYG | 2026-03-08 | superseded by E56 |
| E37 | TEI validation quality gate plus entity tagging fix | two levels (errors blocking, warnings informative), W1-W10, HTML report default | 2026-03-15 | [specification.md](specification.md) |
| E38 | Entity tagging type-correct with internal ids | `annotate_entities()` uses the entity index for type-correct tags | 2026-03-15 | removed by E71 |
| E39 | Language mapping plus facsimile/pb fix | map multilingual codes (`fra/deu`) correctly; empty `<surface>` for pages without layout zones | 2026-03-15 | [tei-mapping.md](tei-mapping.md) |
| E40 | div merge: page divs to document divs | post-assembly fix `_merge_page_divs()`, reference comparison `--compare-ref` | 2026-03-15 | [pipeline.md](pipeline.md) |
| E41 | Agent-based quality screening as pre-curation | structured 7-layer review, review JSON per document | 2026-03-15 | abolished by E66 |
| E42 | `<revisionDesc>` as status in the TEI header | status travels with the document | 2026-03-15 | [tei-mapping.md](tei-mapping.md) |
| E43 | `output/tei_final/` as single source of truth | only final TEI are published | 2026-03-15 | [project.md](project.md), data section |
| E44 | Entity stopword extension needed | screening showed generic nouns as false positives | 2026-03-15 | removed by E71 |
| E45 | Entity stopword extension done | 20 new entries, reassembly of 32 documents, all VALID | 2026-03-15 | removed by E71 |
| E46 | OCR deduplication as deterministic post-processing | `ocr_dedup.py`: token loops, barcode artifacts, year repetitions | 2026-03-15 | removed by E75 |
| E47 | `div type="essay"` is not a valid DTA type | `type="text"` as generic replacement for philosophical essays | 2026-03-15 | [tei-mapping.md](tei-mapping.md) |
| E48 | Project-specific schema `zbz_hersch.rng` | generic `tei_all.rng` replaced by a project schema (from ODD, 551 definitions) | 2026-03-26 | [specification.md](specification.md) |
| E49 | ZBZ editorial guidelines as binding reference | full guidelines as `data/source/guidelines/Editionsrichtlinien_ZBZ.md` | 2026-03-26 | [specification.md](specification.md) |
| E50 | Dual-attribute strategy for entity references | `ref="GND:..."` (primary) plus `corresp="#zbz-p.N"` (internal) | 2026-03-26 | removed by E71 |
| E51 | End-to-end CER benchmark (TEI versus TEI) | 25 ZBZ reference TEIs as ground truth, `benchmark_cer.py` with stratified analysis | 2026-03-26 | [specification.md](specification.md), [project-report.md](../docs/project-report.md) |
| E54 | Scientific CER re-evaluation | BCa bootstrap (B=10000, seed 42), paired bootstrap E2E versus OCR-only, HCPR, multi-norm, content-aligned eval. Headline then n=19: mean 4.10 % [2.01, 6.75], median 1.83 % [0.84, 5.14] (historical state 2026-04-27; current headline see E98/E99: mean 2.08 % / median 1.28 %, n=25) | 2026-04-27 | [project-report.md](../docs/project-report.md) |
| E55 | Interactive CER dashboard | 12 sections, vanilla SVG. Abolished with E56; data remains as `docs/data/cer_statistics.json` | 2026-04-27 | superseded |
| E56 | Frontend reduction to the pipeline viewer | edition site, curation editor (FastAPI), diagnostics, and CER dashboard abolished without replacement. New single-page app `docs/viewer.html` (sidebar, facsimile plus layout overlay plus OCR/TEI panel; layout editor with bbox drag, resize, add, delete, reading-order drag; persistence via file download at that time). Volume 9 to 1 HTML, 23 to 6 JS (minus 81 %), CSS minus 84 %. E33/E36 superseded | 2026-04-27 | [workflow.md](workflow.md) |
| E57 | Per-page mirror plus GitHub Pages deploy | `generate_edition_data.py` mirrors layout JSON, Mistral OCR, and per-page TEI (split from `_final.xml` via `<pb>` at sequential position 1..N because of pagination drift) for all 285 documents to `docs/data/pages/`; three-stage path resolver in `core.js`; `.nojekyll`; image delivery stays local (only demo images versioned) | 2026-05-25 | [workflow.md](workflow.md) |
| E58 | OpenSeadragon 5.0.1 as facsimile renderer (view mode) | pan, zoom, rotate; plain image loading (no deep-zoom tiling); CDN via jsDelivr, no build pipeline. Layout edit mode keeps the static `<img>` editor | 2026-05-25 | [workflow.md](workflow.md) |
| E59 | Polygon support not introduced | Hersch facsimiles are cleanly set print (1926-2000); rectangles cover all region types. Annotorious and similar libraries explicitly unnecessary; data model stays `bbox.x_pct/y_pct/w_pct/h_pct` | 2026-05-25 | [pipeline.md](pipeline.md) |
| E60 | Mode button redesign, option C: edit toggle per panel | global mode bar removed; each panel gets a small edit toggle in its header; `setMode()` split into `setImageEdit()` plus `setTextEdit()` | 2026-05-25 | [workflow.md](workflow.md) |
| E61 | Export module with JSZip 3.10.1 | per-document export drawer plus multi-select bulk export; ZIP built in the browser, no server component; planned, not yet wired in | 2026-05-25 | plan section below |
| E62 | Method page `docs/methode.html` | lean static page with headline CER, stratified values, literature comparison, limitations, tool documentation; deliberately no interactive dashboard. Implicit methodology position: never LLMs for entity-id linking | 2026-05-26 | [specification.md](specification.md) |
| E63 | Blank-page detection plus viewer handling (phase 1) | 79 blank pages corpus-wide; phantom regions from layout QA hallucination countered by the Docling zero signal; viewer fix interim/heuristic; phase 2 in E65 | 2026-05-26 | [workflow.md](workflow.md) |

## Decided (E64-E125, detail)

More recent decisions with full rationale as dedicated sections.

### E64 Viewer condensation: OCR source switcher removed, bars fused, edit toggles named (2026-05-26)

The OCR source dropdown (5 engines) was removed from the viewer. Finding: the delivered mirror contains only Mistral; the alternative engines point to `../output/` (gitignored, not deployed) and are pure benchmark artifacts, dead on the live site. Principle: viewer = delivered edition = Mistral; engine comparison is separate research. `ocrSource` fixed to `mistral`. Doc subbar and toolbar fused; edit toggles renamed to object labels, the active state shown by the filled button.

Documents: [workflow.md](workflow.md)

### E65 Blank-page manifest plus TEI marker (E63 phase 2, steps 1+2) (2026-05-26)

`page_manifest.py` produces per object `output/tei_final/{doc}_manifest.json` (regenerable; exception pages only). The detector (OCR rule identical to the viewer heuristic plus blank markers, AND Docling `num_regions==0` as counter-signal) finds 79 safe blank pages in 15 documents, all cross-validated, 0 conflicts. `tei_blank_marker.py` projects `<pb type="blank"/>` into the final TEI (page = sequential pb position, identical to the mirror splitter) and empties the page body (user decision: a confirmed blank page carries only the marker). 82 junk elements removed, 0 residual, 0 schema regression. Safety: dry run, backup, residual check.

Documents: [workflow.md](workflow.md)

### E67 Catalog UI refactor plus traffic-light reframing plus site consistency (2026-05-26)

Iterative UI pass on the corpus overview and site-wide: table reworked (one typeface logic, sortable headers, author and date as columns, workflow column with per-stream lamps); the traffic-light reframing follows the user finding "no human approved anything" plus "pipeline output EXISTS, it is merely unverified": the earlier reading of `offen` as red was epistemically wrong. Status `offen` renamed to `unverifiziert` (default for all 285 documents), migration idempotent. Red reserved for a future explicit problem status. Sticky filter bar, site-wide footer, legal notice stub, author-name normalisation. Viewer reads `<pb type="blank"/>` marker-driven, heuristic only as fallback.

Documents: [workflow.md](workflow.md)

### E68 `zbz_hersch.rng` extended by omitted standard TEI elements (2026-05-27)

The ODD subset of E48 had omitted `revisionDesc`/`change`, `langUsage`/`language`, `idno` (publicationStmt), and `monogr`/`imprint` (biblStruct), all standard TEI/DTA that the pipeline regularly produces. Consequence: 0/285 delivered TEI valid against their own schema, never noticed because `tei_final` is laid out flat and fell through `validate_all`. Fix: seven definitions added, four content models wired, deliberately minimal against the actually produced data contract. Result 285/285 valid. New pytest gate `tests/test_tei_schema.py` (skips on a fresh clone, `output/` is gitignored). Resolves O23, which had named only `idno`; in truth there were four causes.

Documents: [specification.md](specification.md), [pipeline.md](pipeline.md)

### E66 Abolish agent screening, introduce per-stream workflow status (2026-05-26)

User finding: no human granted the 285 "APPROVED"; the agent screened itself with a built-in ignore list, and the label was epistemically misleading toward ZBZ. Replacement: status values per data stream (`ocr`, `layout`, `tei`), set by humans in the viewer. Data model: the per-object manifest from E65 extended to `{engine, status, history}` with full provenance history. `page_manifest.py` is idempotent: re-runs preserve status and history. UI: three bars plus stream-by-status filter in the catalog, status pills in the viewer with click cycle. ZBZ handover: `tei_status_marker.py` projects the history deterministically as `<change>` entries into `<revisionDesc>` and removes all agent-screening entries. Legacy findings live on as `_screening_legacy.json` (gitignored diagnosis trace). All 285 documents start at the honest anchor `unverifiziert`.

Documents: [workflow.md](workflow.md), [specification.md](specification.md)

### E70 CER methodology corrected: three-figure decomposition (fidelity/scope/full), no trimming, case-sensitive, three paths unified (2026-05-27)

Deep audit of CER production, externally verified against OCR-D/dinglehopper/Transkribus/jiwer. Core finding: the ZBZ reference TEIs are selective partial transcriptions; the pipeline is often more complete. The old alignment trimming hid insertions and losses; naive full-text CER conversely punishes completeness (doc 570: 113 %). Solution: `classify_edit_operations` decomposes every edit operation into fidelity CER (substitutions, small indels, all deletions = real errors) versus scope rate (insertions >= 50 characters = pipeline surplus text, not an error); fidelity plus scope equals full CER. Headline = fidelity over ALL 25 documents (no circular exclusion). Further fixes: case-sensitive default; three CER paths unified on `extract_text_for_comparison` plus `calculate_cer`; circular exclusion criterion removed; error categories via rapidfuzz opcodes (sum exactly to the Levenshtein distance); paired test like-for-like on fidelity (then -7.12 pp, p=0.14, n=19, not significant; the earlier "-14.83 pp p=0.0004" was a trimming artifact and is withdrawn). Citation corrected (arXiv:2510.06743 is Levchenko 2025). 18 golden tests.

Documents: [project-report.md](../docs/project-report.md)

### E69 Correctness wave: O24 fix, `<pb>` segmentation centralised, teiHeader generator on the delivery contract (2026-05-27)

Three silent correctness problems closed, each test-gated. (a) O24: the validator imported a non-existent `compute_cer` and silently fell back to a length approximation; fixed with `calculate_cer` times 100 and a narrowed except. (b) `<pb>` DRY: the rule "page number = 1-based sequential pb position" was duplicated in two scripts; new helper `scripts/tei/pb_split.py`, byte-identical verified over all 285 finals. (c) teiHeader poverty: `build_tei_header` regressed headers on regeneration (losing `idno`/`biblStruct` that E68 needed); rewritten congruent with the delivery contract (`<idno type="docID">`, `<biblStruct>`, `<langUsage>`). (d) An MMSID projection introduced here was removed again with E76.

Documents: [specification.md](specification.md), [pipeline.md](pipeline.md)

### E71 NER / entity linking fully removed (2026-05-27)

User decision. Finding: linking was not functional in the delivered TEI; only ~2.6 % of ~30,500 tagged mentions carried a real GND id, the rest `GND:unknown` or internal ids; the documented dual attribute (E50) did not exist in the output at all. Removed: the NER step from `tei_unified`, entity seeding from the mapping prompt, annotation functions, `scripts/ner/` (6 modules), entity data and index, viewer entity highlighting. Deterministic body strip over all 285 TEI in all three locations; `<bibl>` inside `<listBibl>` kept as bibliographic structure. 285/285 schema-valid. Makes risks R3/R10 obsolete. Honest removal over placeholder noise.

Documents: [pipeline.md](pipeline.md)

### E72 Direct-write loop for viewer curation (File System Access API plus backend consumers) (2026-05-27)

Curation previously persisted only via browser download plus manual filing, and the curated layout/OCR files had no consumer in the pipeline; the documented round trip was partly aspirational. Both halves built: (a) frontend module `fs-access.js` writes curated files via the File System Access API directly into the user-granted repo folder (handle persisted in IndexedDB; Chromium, download fallback); (b) backend: `load_layout_gemini` reads `_layout_curated.json` first, curated OCR directory first in the OCR source order, so `--reassemble` really consumes the edits. Caveat: direct TEI editing overwrites the SoT and is regenerated by a later `--reassemble`; the recommended path is layout/OCR edits. Gate `tests/test_curated_loaders.py`. Security: no token, no auto-write, access only after explicit folder grant.

Documents: [workflow.md](workflow.md)

### E73 CER scope: hard-coded six-document exclusion list removed, all metrics over all 25 documents (2026-05-27)

Raw-data verification: the list followed no reproducible criterion (it did not exclude doc 570 with 112 % surplus, but flagged documents whose scope insertion was negligible), and two code comments were factually wrong. `_override_scope` now sets all documents to full scope. Fidelity CER unchanged (it already computes over all documents and is scope-robust); the raw end-to-end figure is marked as diagnosis, not a quality measure. Paired test then n=25: -7.90 pp, p=0.07, not significant. Closes the OPEN point from E70.

Documents: [project-report.md](../docs/project-report.md)

### E74 Embedded Schematron rules deliberately NOT executed (documented instead of built) (2026-05-27)

Question: should the 36 embedded `sch:rule` run in addition to RelaxNG? Spike verification: 14/36 rules need XPath 2.0 (not runnable on libxslt); the 22 runnable ones target TEI-ODD/schema constructs and find 0 hits over all 285 editions (harness proven correct with a synthetic always-fail rule). Generic TEI P5 boilerplate, not editorial rules; a partial pass would be misleading validation theatre. Decision: do not build. Real editorial validation would be new project-specific rules (separate undertaking, possibly Saxon/XSLT 2.0).

Documents: [specification.md](specification.md)

### E75 Dead OCR paths removed: `ocr_dedup` plus DoclingOCR engine (2026-05-27)

Cleanup wave. (a) `ocr_dedup.py` (E46) was orphaned (no code importer), read a hard-coded wrong directory, and mutated OCR in place without backup; removed instead of repaired (repair would have armed a destructive tool on the base OCR). (b) `DoclingOCR` as an OCR engine wrote a dead-end single file never consumed by the pipeline, and auto mode routed two-column documents there (latent misrouting); class, choice, and routing removed. Docling as layout engine untouched.

Documents: [pipeline.md](pipeline.md)

### E76 MMSID projection removed from the pipeline (header metadata = ZBZ domain) (2026-06-03)

User decision: the MMSID projection introduced with E69 part (d) is removed again. Header metadata from Alma is ZBZ-side per O8; the MMSID existed only in code, never in a delivered TEI (0/285). Removed: `scripts/core/masterfile.py` (whole module), the call sites, the emission, tests, and docs. Spec conflict knowingly accepted: the editorial guidelines demand ID plus MMSID plus PubForm in the header; to be clarified with ZBZ (O8). Untouched: ZBZ's guidelines file (immutable input).

Documents: [decisions.md](decisions.md)

### E77 Workflow status collapsed from four to three stages (variant A) (2026-06-07)

User decision. Instead of `unverifiziert|in_arbeit|bearbeitet|fertig` now `unverifiziert|in_arbeit|verifiziert` per stream. Finding: the four stages collapsed to only two lamp colours in the UI anyway, and `bearbeitet` versus `fertig` was a blurred seam. Three stages give one colour per stage: neutral grey, yellow, green; red stays reserved for a future explicit problem status (E67-conformant; a literal red/yellow/green reading was rejected). Migration old-to-new idempotent across manifest, mirror reading, and both frontends; timing ideal because all 285 documents stood at `unverifiziert` with empty history, so no data loss and no mirror regeneration. New gate `tests/test_workflow_status.py`. E67 remains valid; its four-stage table is superseded.

Documents: [workflow.md](workflow.md), [specification.md](specification.md)

### E78 Viewer curation: one save button instead of three separate downloads (2026-06-07)

User decision: "one shared save button, and it must not be a download, it must land at the right place in the repo". One "Speichern" (save) action now persists all unsaved streams at once: layout (page), text or TEI (page, by source), and the manifest (workflow status plus provenance), each to its canonical repo location (`saveAll()`, FSA with download fallback). The individual downloads moved into an export dropdown. Further condensation: identity chip next to the save button, page navigation moved into the facsimile panel header, edit toggles renamed to "edit layout"/"edit text", the separate connect-folder menu item removed (connection happens on first save, with a first-use modal and a folder plausibility check). E72 remains the foundation; E78 is the UI unification on top.

Documents: [workflow.md](workflow.md)

### E79 Mirror write: save mirrors to `docs/data/`, viewer reads curated layout first (2026-06-07)

User bug: layout edited, saved, reload, edit gone. Root cause: the server-less viewer runs with docroot `docs/` and on reload reads exclusively from `docs/data/`, but E72 wrote curation only to `output/`; additionally `fetchLayout` never read `_layout_curated.json`. Two-part fix: (a) every FSA write mirrors the identical payload into `docs/data/` (layout, text, manifest, TEI final), the canonical `output/` write unchanged; (b) the viewer reads curated first (`layoutCurated > gemini > docling`, analogous to the pipeline loaders). `generate_edition_data --mirror-only` reproduces exactly the same mirror files, so no drift. Caveat: per-page TEI splits only appear on `--reassemble`.

Documents: [workflow.md](workflow.md)

### E80 CER framing print-calibrated: HTR bands flatter, headline anchored to print literature (2026-06-08)

User finding (critical expert): the corpus is pure print, not handwriting; the Transkribus quality bands (below 2 % excellent / publication-ready) come from HTR practice and flatter a print OCR task. Headline words like "excellent/state of the art/publication-ready" contradicted the project's own print literature comparison (Crosilla et al. 2025: best specialised stack 0.84 %, Transkribus alone 3.67 %). Correction without changing any number: the median is solid for historical print, not state of the art; SotA only for the best individual documents; CER additionally measures against a reference that itself contains errors, so it is an upper bound.

Documents: [project-report.md](../docs/project-report.md), [methode.html](../docs/methode.html)

### E81 Transkribus export plus REST upload: PAGE-XML round trip into a collection (2026-06-08)

The stage-4 PAGE-XML (standard PAGE 2013-07-15) is losslessly playable back into Transkribus for manual post-correction or HTR training. Two scripts: `transkribus_export.py` builds the Transkribus folder convention from `page_xml/` plus `docs/images/` (selection `--sample` stratified, `--all`, `--reference`, `--doc`; verifies PNG size equals declared image size so coordinates align). `transkribus_upload.py` uploads bundles via the legacy TrpServer REST API; verified 2026-06-08 against a collection of the new platform (test object doc 1500 appeared with regions, text, and reading order). Auth exclusively via environment variables, never in code or repo. No dedup: every run creates new documents, hence dry run plus test object first. Dialect caveat: line polygons, no baselines (import fine, HTR training would need them).

Documents: [project.md](project.md), integration section

### E82 Doc-30 dedup published, corpus mean 3.99 % (was 4.26), tail-cause register (2026-06-08)

In document 30 a duplicated OCR block was removed; fidelity CER 18.25 to 11.59 %, published to the SoT and mirror. Corpus mean fidelity 4.26 to 3.99 % (CI [2.36; 5.96]), median unchanged; statistics JSON regenerated (seed 42). The old figure is retired (user decision: only the current CER counts). Caveat: 3.99 = 24 documents pure pipeline output plus one manually deduplicated, because no automatic block deduplication exists; the `ocr_dedup.py` once referenced in work-report appendix A and CLAUDE.md is not in the repo [update 2026-07-07: clarified; CLAUDE.md has not referenced it since Session 73, the script itself was removed with E75]. Tail causes documented: the high CER values are structural, not character recognition. Open defects registered: (a) the layout QA over-detects footnotes, body-as-note on 290/1910/90, not safely auto-fixable because of real long footnotes in 1520/40/3040; (b) double-page reading order, sorted only by y [update E90 (2026-06-21): (b) fixed generator-side, validator warning W19 scopes the not-yet-regenerated corpus, delivery M3 operator-gated; (a) remains open]. E80 remains valid.

Documents: [project-report.md](../docs/project-report.md)

### E83 Code-doc drift fixed; header metadata stays ZBZ domain (E76/O8 confirmed) (2026-06-08)

User assignment: "fix the code-doc drift; build only what is genuinely sensible". (a) Drift fixed (kept): revisionDesc documentation on workflow status instead of the old "APPROVED"; dead reference in the mapping prompt replaced; scope note added (step 2 delivers only a per-page div fragment, so front/back/anchor/unclear cannot be produced automatically); header comment honest about the data source; docstring and validator comments corrected. (b) An MMSID/citation header projection was built as a test and REJECTED again after consultation: catalog numbers and bibliographic citations are library domain (confirms E76/O8; note for future sessions: do not retry without an explicit ZBZ requirement). (c) Confirmed: front/back/anchor/unclear stay curation (data source free text, too rare, or image judgment).

Documents: [pipeline.md](pipeline.md), [decisions.md](decisions.md)

### E84 Conformity audit pipeline versus editorial guidelines plus wave-1/2 generator fixes (implemented, deploy operator-gated) (2026-06-08)

Exhaustive comparison of the delivered TEI structure against the editorial guidelines as a multi-agent workflow (126 agents, 62 rules, adversarially verified). 18 real generator defects proven; one earlier claim corrected (`div type="text"` is NOT a violation). Wave 1 implemented and tested: exclusive div n/type, sequential figure ids, `head type="lemma"` for encyclopedias. Wave 2 partial: first document head as `<title type="main">`, `<foreign xml:lang>` normalised to 639-2/B. All as fault-tolerant post-assembly passes; validator warnings W15-W18 added (non-blocking). The largest defect (62 % empty speakers) deliberately NOT rebuilt: the ground truth encodes speakers via GND persName, GND linking left the pipeline with E71, so the empty `<speaker/>` is a curation slot, not a bug. Adversarial code review (39 agents) confirmed three findings, all addressed. Deploy operator-gated: fixes take effect only after corpus regeneration, which must be coordinated with the curation lanes. Wave-2 remainder classified: no safely deterministic fix remains (collision, curation slot, ZBZ-blocked, or non-defect). reference_tei/1520.xml is broken XML, escalated to ZBZ.

Documents: [pipeline.md](pipeline.md), [specification.md](specification.md)

### E85 Reference-verified footnote demotion (3.99 to 2.71 %) plus sup-marker strip (2026-06-08)

Two reference-backed footnote conformity corrections as idempotent, reversible post-passes on `tei_final`. (a) Demotion: some `<note place="foot">` actually carried body text; if a contiguous stretch of at least 150 characters appears in the ground-truth body (footnotes excluded), the block is provably body text and is demoted to `<p>`. 14 blocks in 5 documents (290/1910/90 plus, on operator instruction, 40/1520). Corpus fidelity mean 3.99 to 2.71 %, median 1.40 %; the pipeline's advantage over raw OCR thereby significant (-9.45 pp, p=0.013). Tool `tei_footnote_demote.py` (backup, hold list, `--include-hold`). (b) Sup-marker strip: leading print markers removed from note text per the guidelines (mark only via `@n`); 16 notes in 4 documents, CER-neutral. Wave-2 remainder classified by a ground-truth-based adversarial workflow; footnote-n was the only safe fix. The note "3 W19 diagnosis specs handed over" was a provisional label, superseded by E90.

Documents: [project-report.md](../docs/project-report.md)

### E86 Repo audit wave: viewer data-loss fix (H1) plus CI gate plus documentation consistency (2026-06-10)

Four parallel audits, findings implemented in one wave. (a) H1 fixed (data loss): the XML mode loaded a single page while save overwrote the whole `_final.xml`; the mode now loads the whole document and a save guard rejects content without a TEI root. Plus honest download fallback labelling, stale-guards against page-switch races, accessibility fixes (pointer events, arrow-key nudge, modal focus trap, editor ARIA), and a sort fix. (b) CI introduced: GitHub Actions runs the full pytest suite on every push/PR (data-dependent tests skip on fresh checkouts). (c) `requirements.txt` made runnable for fresh environments (missing packages added, six dead ones removed, torch documented as optional). (d) Python hygiene: file handles closed on error paths in the Transkribus scripts. (e) Documentation: stale CER headline pulled to the canonical 2.71 % / 1.40 % site-wide; code-comment convention from now on: compact, English, only where needed.

Documents: [specification.md](specification.md), [workflow.md](workflow.md)

### E87 `zbz_hersch.rng` extended by teiCrafter standOff register plus name mentions (2026-06-21)

> Superseded by E88 (2026-06-21). The ZBZ material handed over the same day decided the
> markup model in favour of inline GND; the standOff register is irrelevant for delivery
> and was removed from the active schema again. The entry remains as derivation.

The curation editor teiCrafter wrote a `<standOff>` register when annotating (person/place/org/event/bibl lists with authority `<idno>`, editorial notes, an AI respStmt, in-text `<name ref>` mentions; data contract lifted exactly from the teiCrafter source). The ODD subset had omitted standOff and generic `<name>`; since E71 the delivered TEI is entity-free. Consequence: a document curated in teiCrafter was invalid against its own schema although `{id}_final.xml` is teiCrafter's native format. Fix following the E68 pattern: standOff attached to `model.resource`, name to `model.nameLike.agent`, eleven element defines plus a dedicated standOff work register (the shared ODD-reduced bibl stays untouched). Verified: synthetic curated document valid, 285/285 still valid, tracked gate. The facsimile check in the same session found the missing surface-to-image pointer (opened O25). Which model would be the delivery model was left open (O26): the guidelines demand inline markup at the mention site, E87 only made the tool model schema-legal.

Documents: [pipeline.md](pipeline.md)

### E88 Inline GND as the binding markup model; standOff (E87) removed from the active schema (2026-06-21)

Resolves O26. The ZBZ material (`data/source/zbz-lieferung-2026-06-21/`, README = complete editorial guideline, `zbz_hersch.rng` = ZBZ check template) decides the markup model: persons, organisations, and works are tagged inline at the mention site, every mention with `ref="GND:..."`, no separate register; only person/organisation/work, no places or events, no GeoNames or Wikidata, no tagging in captions. The ZBZ template knows no standOff. Order of research coordination: only the ZBZ editorial rules apply. Schema consequence: the eleven E87 defines and both model refs removed, the three `@ref` patterns narrowed from `(GND:...|#zbz-...)` to `GND:...` (inline GND only). The E68 header elements remain, so the active schema is exactly the ZBZ template plus E68 (full diff verified). Rationale for additive-minus-E87 instead of raw template adoption: the ZBZ template is older than the repo state and lacks the E68 header elements the pipeline regularly produces; raw adoption would invalidate all 285. Verified: inline GND document valid, standOff document now rejected (guard test), 285/285 still valid (the corpus is entity-free since E71, no migration needed). Effect on teiCrafter: its output model must be aligned to inline GND; delta reported to research coordination.

Documents: [pipeline.md](pipeline.md), [specification.md](specification.md), [index.md](index.md)

### E89 Page-image linking ZBZ-conformant: `<graphic>` as first child of every `<surface>` (2026-06-21)

Resolves O25. Order of research coordination: page-image linking follows the ZBZ rules entirely; the address scheme is a technical decision of the lane, no operator gate. Finding: the binding linking form is `<pb facs="#facs_N" n="..."/>`, present on all 285 (conformity rule Z6); the README does not mandate a surface `<graphic>` but the schema allows it (graphic before zone). So that the `<pb facs>` reference resolves self-contained to the image, every surface now carries `<graphic url="{doc_id}_p{NNN}.png"/>` as first child (three-digit, 1-based, sequential to `facs_N`), a bare relative filename resolved against the document's image folder. Rejected: absolute GitHub Pages URL and IIIF (hosting open; the relative path is the ZBZ requirement). Implemented twice: `build_facsimile` for fresh runs and the idempotent post-step `tei_surface_graphic.py` for the delivered corpus (also fixes the broken blank-page placeholder). Verified: 4108 surfaces carry the graphic, all referenced images exist, 285/285 valid and conformant, committed gate.

Documents: [pipeline.md](pipeline.md), [specification.md](specification.md)

### E90 Reading order column- and band-aware (generator fix, M1) plus validator warning W19 (M2) (2026-06-21)

Resolves open defect (b) from the doc-30/CER entry generator-side. Milestone round of research coordination.

Finding: `match_paragraphs_to_regions` sorted the layout regions purely by `y_pct` (live and legacy call site, identical bug). Layout detection already delivers regions left-column-first; pure y-sorting re-interleaves left and right columns on two-column and double-page layouts (30/760). No stored reading-order field, only bbox geometry. Structural tail cause, not character recognition (E80).

M1 (generator fix): shared pure function `reading_order_permutation` in `tei_xml_utils.py`: full-width blocks (w >= 60 %) segment the page into horizontal bands; within a band, columns split at an x-center gap above 12 % are read left to right, top to bottom per column. A single-column page falls back exactly to the old y-order, hence regression-free. Both call sites converge on this one function. Tests `tests/test_reading_order.py` (9). Commit `6f51eac2`.

M2 (diagnosis): non-blocking validator warning W19 (`_check_reading_order`) compares the delivered block order per page against the canonical order of the same zones, reusing the same function. It fires only on the not-yet-regenerated corpus and thereby scopes exactly the M3 documents. Tests in `tests/test_tei_validator.py` (4). Commit `f72743ac`.

W19 naming clarification: the implemented W19 is the reading-order warning; the E85 note "3 W19 diagnosis specs" was a provisional label for never-implemented proposals, superseded; future specs take identifiers from W20 upward.

Delivery to the corpus: M3, operator-gated. Corpus regeneration (`tei_unified --all --reassemble`) rewrites the SoT and must be coordinated with the curation lanes (E84-consistent). Green criteria: `tei_validator --all` reports 0 W19; schema and ZBZ conformity stay 285/285; the fidelity CER of 30/760 drops.

M3 preparation (audit instrument plus triage, 2026-06-21, commit `8aa3a87d`): behaviour-preserving refactor first (shared `iter_page_zone_bboxes`, optional threshold parameters on the permutation). The tool `reading_order_audit.py` recomputes the canonical permutation per affected page under threshold perturbation (WIDE 60 +/-5, GAP 12 +/-3): stable = robust, flipping = fragile. Measurement over `tei_final`: 831 pages over 216 documents, 557 robust, 274 fragile, 145 documents with at least one fragile page (spread: doc 810 54/33, doc 520 9/0). Recommendation: trust the robust majority after a review sample; review the fragile worklist (`--worklist`) at the facsimile. Robust means threshold-independent, not proven correct. Deliberately no new register number; rollout unratified.

M3 preview (reversible dry run, 2026-06-21): the tool `tei_reassemble_preview.py` reassembles every affected document (steps 1+3, M1 acts in step 1) into `output/tei_preview`; `output/tei_final` is never touched (hash- and test-verified). Offline and free (`dry_run=True`): the preview proves the reading order, not the text refinement, which is independent and reserved for the gated delivery. Tests `tests/test_reassemble_preview.py` (6, one gated pipeline test on doc 890), full suite 1187. Report `reports/m3-reassemble-preview.md`, deterministic.

Finding that sharpens the green criterion: reassembly lowers W19 from 831 to 39 pages; 188 documents reach 0, 28 keep 39 pages (heavy cases collapse: 810 54 to 1, 1520 40 to 1, 1830 11 to 1; largest rest 1240 13 to 7). The literal criterion "0 W19" is not reachable by reassembly alone.

Cause of the 39 remaining pages (diagnostically isolated, no geometry gap): the permutation is idempotent. 35 of 39 pages carry an OCR-paragraph versus layout-region count mismatch (810 p.56: 3 against 236; 1240 p.3: 50 against 61); in the mismatch branch, paragraphs pair by index to a slice of the re-sorted regions, the emitted zone slice is non-canonical, W19 fires correctly. The remaining 4 pages have 1:1 counts but geometry that breaks column detection (sub-60 % header protruding into the second column, 460 p.1). Both mean the same: the 39 are exactly the pages where automatic correction is unreliable, the facsimile-review worklist for M3, largely congruent with the fragile triage. Rejected: re-sorting the emitted zone slice to force W19 to 0 (silences the signal without fixing the upstream segmentation problem). No new register number; rollout stays operator-gated.

Documents: [journal.md](journal.md) sessions 74, 75, 77, 78

### E91 Independent CER counter-check confirms the source of truth (2026-07-03)

Occasion: operator doubt about the solidity of the CER figures, examined from an external session
(promptotyping-paper lane). The counter-check imported no repo code. Extraction and normalization
were re-implemented from the documented specification, python-Levenshtein ran as a second engine
besides rapidfuzz, and the aggregation was independent. It added secondary metrics (WER,
case-insensitive CER, alignment-free bag-of-chars miss, bag-of-words recall), a content pass over
the top error blocks of all 25 ground-truth documents, and two facsimile spot checks (docs 30 and 100).

Result: every headline and per-document value reproduced exactly; genuine text loss is the
exception. The fidelity values depend on the scope threshold (`SCOPE_BLOCK_MIN = 50`), so any
citation of them must name the threshold. The fidelity drivers were classified as apparatus
insertions under 50 characters (no recognition error), genuine losses (double page in doc 30,
facsimile-verified; passages in 1910; citation references in 1520; picture captions in 760),
convention divergences of the reference (capitalized titles in doc 100, facsimile-verified), and
rare genuine misrecognitions. Current figures are produced by
`python -m scripts.eval.benchmark_cer --all` and
`python -m scripts.eval.cer_statistics_full --seed 42 --bootstrap-n 10000`; the counter-check
report with its measured values is
cer-gegenprobe-2026-07-03.md (verification.md, appendix), and the counter-check
scripts live in the paper repo (DHCraft/promptotyping-paper, `verification/`).

Consequence: the upper-bound passage in [project-report.md](../docs/project-report.md) is concretized by the
two cause classes that inflate fidelity without a recognition error (apparatus insertions,
capitalization divergence). Open follow-up: ellipsis normalization (U+2026 versus `...`), a
possible dedicated reporting category for apparatus insertions, and the doc 30/760 stock
correction via M3 (operator-gated, E90).

Documents: [project-report.md](../docs/project-report.md), cer-gegenprobe-2026-07-03.md (verification.md, appendix)

### E92 Guideline conformity quantified corpus-wide: five audit instruments plus step-1 generator fixes (2026-07-07)

Occasion: operator question whether the delivered TEI satisfies the ZBZ editorial guidelines beyond schema validity. The session built a ground-truth map of the 25 reference TEIs (consolidated as Appendix B of [project-report.md](../docs/project-report.md), including the exception catalog of reference-side defects and the ill-formed 1520.xml) and quantified every suspicion with five new offline audit instruments in `scripts/eval/`, each test-gated, JSON output to `output/audits/`:

- `char_lint_audit.py`: typewriter apostrophe U+0027 between letters, guillemet deviations, space before punctuation (incl. U+00A0), U+00AC residue.
- `pb_number_audit.py`: scan-sequence suspicion on pb@n, digit-only paragraphs in the body, cross-check against layout footer regions.
- `hi_preservation_audit.py`: survival of the OCR emphasis signal into the delivered TEI (per page, via `pb_split.iter_page_spans`).
- `relation_integrity_audit.py`: `@next`/`@prev` pairs, anchor pairs, title-main cardinality, `sp`/`speaker` context.
- `body_note_audit.py`: body-text-as-footnote candidates via a marker/length/position score; its candidate set feeds the facsimile verification consumed by E94.

Measured state (snapshot 2026-07-07): character normalization is the largest gap (241 documents with letter-internal U+0027 at 88,978 occurrences; 228 with guillemet deviations at 16,013; 215 with space-before-punctuation at 9,928); print pagination is broadly missing (245 documents with scan-sequence pb@n, 226 with a layout-footer/pb mismatch, 191 with digit-only paragraphs); hi survival is nearly clean pipeline-side (18 pages in 12 documents); relations are nearly clean (one `@next`/`@prev` case in doc 1350; `sp`/`speaker` outside interview context concentrated in doc 1240).

Generator fixes (step 1, test-first): `detect_page_number` reads the printed page number from layout `_filter`/`_skip` footer regions into pb@n (fallback stays the scan number), and `drop_filter_echoes` stops filtered-region text (footer page numbers, cover boilerplate) from leaking into the body through positional paragraph matching. Verified on the doc 570 scaffold regeneration. Both act on regeneration; correcting the delivered corpus runs over the operator-gated marker path (deterministic post-steps on `tei_final` with backup and before/after audit measurement).

Documents: [project-report.md](../docs/project-report.md) (Appendix B), [journal.md](journal.md) session 83

### E93 Image-based italics re-detection rejected; `<hi>` stays OCR-signal-bound (2026-07-07)

Occasion: the reference TEIs mark italics roughly an order of magnitude more often than the delivered corpus, and the loss chain was traced end to end. Mistral OCR emits `*emphasis*` markers on only a minority of pages; the step-1 scaffold preserves the emitted markers nearly completely (`md_to_tei_inline`); step 3 strips nothing; the Gemini refinement image channel is instructed to verify existing emphasis, and only where semantically relevant. The dominant loss therefore sits in the OCR engine, before the pipeline.

The apparent fixes, sharpening the Gemini prompt from verify to detect or adding an image-based re-detection pass, are rejected (operator ratified 2026-07-07): the OCR signal is the only machine-readable evidence for italics the pipeline has, an instructed LLM detection is non-deterministic run to run, and the footnote overdetection precedent (E82, repaired by E85) shows what instructed detection does to corpus-wide stock. No Gemini prompt change ships.

Consequence: `<hi>` in pipeline output remains bound to the OCR emphasis signal, guarded by `hi_preservation_audit` (E92). Complete rendering markup per guideline vocabulary (`#i` etc.) is downstream curation at the facsimile, in the viewer or in teiCrafter.

Documents: [project-report.md](../docs/project-report.md), [specification.md](specification.md)

### E94 Stock-correction wave ratified: printed-folio pb@n, hybrid correction mode, targeted verification depth (2026-07-07)

Operator ratifications after the calibration round, answered as three conceptual questions: (1) `pb@n` carries the printed page number in square brackets, matching the corpus-wide bracket convention of the ZBZ references; pages without a reliable signal keep the unbracketed scan number. (2) Correction mode hybrid: safe classes are corrected machine-side as reversible marker runs with backup; unsafe classes (space type, dehyphenation residue) stay curation worklists. (3) Verification depth: targeted adjudication of known conflicts plus supplementary samples of under-covered strata, instead of a full stratified sample.

Executed: `tei_char_normalize.py` normalized the letter-internal typewriter apostrophe corpus-wide (88,978 occurrences in 241 documents to U+2019; after-audit 0; backup `output/_backup_pre_char_normalize/`; schema, header, and validator gates green). The tool imports the audit regex, so measurement and correction share one definition.

Built and dry-run verified; executed by the operator on 2026-07-07, reproducing the dry-run figures exactly (the echo-strip defect this exposed and its healing are E95): `tei_pb_folio.py` (folio from footer detection 1753 pages, interpolation 1033, stable offset 151, bracketing of already printed folio 208, fallback 970; `--strip-folio-echo` removes 1212 stray page-number paragraphs) and `tei_body_note_demote.py` (verdict-driven: 59 demotions to `<p>`, 2 epigraphs to `<quote>`, 2 genuine footnotes untouched, 19 conservative footnote promotions reversing the verified role swap of body and footnote). The verdicts come from the facsimile verification of all 63 `body_note_audit` candidates and are persisted in `output/audits/body_note_verdicts.json`.

Findings feeding later decisions: the sampled doc-30 double pages show no character loss, conflicting with the E91 loss classification (adjudication pending); Mistral OCR degenerated into a repetition loop on doc 1520 page 70 and the correction layer's refusal text leaked into the delivered TEI (single-page re-OCR gated); `<foreign>` markup exists in only 30 of 285 documents while at least 27 foreign-less documents carry unmarked Latin/Greek phrases, with an inconsistent de/deu language code; a naive OCR-versus-TEI volume audit was tested and rejected because about 90 percent of its hits are the intentional e-periodica boilerplate filtering (a filtered triage variant plus a refusal-string check and a duplicate-facs check remain recommended).

Documents: [journal.md](journal.md) session 83, [specification.md](specification.md)

### E95 Echo-strip repaired sp-aware after the executed stock runs; rerun made semantically idempotent (2026-07-07)

Occasion: the operator executed both pending E94 stock runs (`tei_pb_folio --strip-folio-echo`, then `tei_body_note_demote --promote-footnotes`); both reproduced the dry-run-verified figures exactly. The post-run gates then caught four schema-invalid interview documents (2330, 2400, 2540, 3180), all previously valid.

Root cause: in interview documents the footer echo sits inside `<sp>` with an empty `<speaker/>`; the echo strip removed the `<p>` but left the wrapper, and the schema requires at least one `<p>` per `<sp>` (14 orphaned wrappers corpus-wide). The dry run could not see this because it counts removals without validating.

Repair (test-first): the strip is sp-aware. An echo that is the sole content of an `<sp>` with empty speaker removes the whole block; an `<sp>` with a named speaker stays untouched, echo included (content over cosmetics); already orphaned empty wrappers are healed on any strip run, so re-running the tool repairs the corpus. Healing verified end-to-end on copies of all four documents (schema-valid afterwards, second run a no-op).

Second defect found by the new post-state tests: a rerun reclassified mostly-bracketed documents as printed_folio and would have bracketed the remaining unbracketed scan fallbacks into false print folios (e.g. doc 110 scan page 1 to `[1]`). Guard: once a document carries bracketed pb@n, unbracketed values are by the R-PBN convention scan fallbacks of a prior run and are never reinterpreted (`doc_has_brackets` in `resolve_page_folio`).

The integration tests in `tests/test_pb_folio.py` now assert the delivered post-run state plus rerun idempotence instead of the pre-run proposals. Corpus healing ran over the operator-gated marker path on 2026-07-07: the repeated `tei_pb_folio --strip-folio-echo` removed exactly the 14 wrappers, changed no pb@n corpus-wide, and left all gates green (285/285 valid, suite fully green).

Documents: [journal.md](journal.md) session 85

### E96 Doc 1520 page 70: leaked refusal replaced by an honest partial transcription (2026-07-07)

Occasion: E94 finding, Mistral OCR degenerated into a repetition loop on this page and the correction layer's refusal text leaked into the delivered TEI. The operator supplied a Gemini API key and authorized `gemini-3.5-flash` for the gated single-page re-OCR.

Findings: the page is largely illegible in the delivered scan (very faint print plus verso bleed-through, which is also why Mistral looped). Two vision passes diverged tellingly. The fluent pass produced complete text that is partly reconstructed from world knowledge; contrast-enhanced facsimile bands refute it at verifiable spots (printed "Ce chiffre historique universel" where it wrote "Ce double mouvement", printed "en Iran" where it wrote "en Perse"). The honesty-prompted pass marked the same zones `[...]`. Machine transcription of this scan has a hard ceiling.

Decision: the delivered TEI carries an honest partial transcription, facsimile-verified anchors and two-pass consensus verbatim, every unresolved span as `[...]`, and no footer digit (the passes read 253/256 in the faded footer, but `pb n="[64]"` stands in an unbroken bracketed sequence [59]..[70] with stable offset 6 and outranks the illegible digit). Rejected alternative: the fluent single-pass text, because it fabricates unreadable regions.

Execution: full backup to `output/_backup_pre_1520_p70_reocr/`; new base text written to `mistral_results/` (the canonical target of the Gemini-vision engine), refusal removed from `llm_corrected_c/`, poisoned per-page step-1 caches removed, `tei_final` page 70 patched surgically (pb tag, folio, and all stock corrections untouched). Validator 0 errors, schema gate green, mirror regenerated. The page remains a curation case; full transcription needs a better scan (ZBZ).

Documents: [journal.md](journal.md) session 87

### E97 Doc 30 adjudicated: E91 text-loss reading confirmed, the calibration conflict was a sampling gap (2026-07-07)

Occasion: E94 left open the contradiction between the counter-check (E91: the CER outlier is genuine text loss on double pages) and the facsimile calibration (complete text on the double pages it sampled, suggesting a pure alignment problem).

Adjudication (facsimile-verified): the three missing blocks of doc 30 (540/451/194 normalized characters via the canonical alignment) all sit at reference positions 0-6 percent, i.e. on the left half of the FIRST double page (printed page [222]). The scan shows this text fully legible; it is absent from the delivered TEI and from every OCR stream (grep across mistral/ocr_results/gemini_corrected/llm_corrected). Both prior findings are therefore correct: the calibration sample (facs 2-4) did not include the affected page, and only its generalization to "pure alignment problem" was wrong.

Consequence: the fidelity outlier (11.59 percent) is genuine recognition loss of one double-page half; a reading-order correction cannot recover it. Repair path: targeted single-page re-OCR of scan page 1 following the E96 pattern (gated). The adjudication slot in `arbeitsbericht-v3.md` is filled.

Documents: [journal.md](journal.md) session 88

### E98 Doc 30 double-page half restored (2026-07-07)

Occasion: E97 adjudicated the doc-30 CER outlier as genuine recognition loss of the left half of scan page 1 (printed page [222]); the operator approved the targeted repair (plan phase 1).

Execution (E96 pattern, backup `output/_backup_pre_30_p1_reocr/`): the double page was re-read with `gemini-3.5-flash` at 300 DPI (the scan is well legible, unlike 1520 p70) and verified against the facsimile. The base OCR stream now carries the full spread in canonical order (this also preserves the E82 dedup, since the duplicated block is gone from the source text); stale per-page caches were removed; `tei_final` page 1 was patched surgically. The patch also repaired the facsimile metadata: the three recovered paragraphs got honest new zones (`facs_1_r_4..r_6` from the Gemini layout), and the two provably wrong zone boxes were corrected (`r_2` carried the heading box while holding a right-column paragraph, `r_3` carried the first left paragraph's box). `pb@n` was lifted from the fallback `[1]` to `[222]`, consistent with the `[224]`/`[226]` neighbours.

Result: doc-30 fidelity CER 11.59 to 0.90 percent (corpus maximum gone); corpus headline (seed 42, B=10000) fidelity mean 2.50 to 2.08 percent, median 1.37 to 1.28 percent; paired against raw OCR -10.08pp, p = 0.0034. Validator and schema gates green; W19 cleared for page 1 (pages 2/3 remain flagged, see E99 for why they stay untouched).

Documents: [journal.md](journal.md) session 89

### E99 Machine reading-order rollout falsified: W19 pages carry corrupt zone assignments over correct text (2026-07-07)

Occasion: the plan for the M3 rollout replaced the barred reassembly path (it would revert the E94-E96 stock state, which includes non-re-runnable hand patches E82/E96) with an in-place instrument: `scripts/tei/tei_reading_order_fix.py`, built test-first, permutes the region blocks of robust W19 pages as byte splices (marker idiom, dry-run default, idempotent, self-check on the identity permutation), reusing `classify_page`, `reading_order_permutation`, `pb_split`, and a new shared `build_zone_bbox` in `tei_xml_utils`.

Falsification (the decisive evidence, produced BEFORE any real run by the plan's dry-run gate): applying the fix to copies of all 25 reference documents and measuring fidelity CER per document yields 0 improvements and 9 degradations, up to +40 percentage points (doc 30: 0.90 to 24.04; doc 2635: 0.73 to 40.71). Root-cause inspection (doc 30 page 3) shows the delivered TEXT is correct (CER-proven against the human reference, textually continuous across pages) while the block-to-zone ASSIGNMENT lies (blocks carry other blocks' boxes, as first seen on doc 30 page 1 in E98). This matches the E94 calibration finding that 5 of 6 W19 sample pages read correctly at the facsimile.

Decision: NO machine reordering of the delivered corpus, on either path; rejected alternatives are the E90 reassembly rollout (stock-state loss AND the same corrupt-zone risk) and the corpus-wide in-place run (measured damage). W19 is reframed as a text-OR-zone suspect signal (validator message updated); its resolution is facsimile curation. The tool stays as the evidence instrument: dry-run default produces the triaged worklist, a real run requires the explicit `--write` and is defensible only for individually facsimile-verified pages. The 2026-06-21 preview (`output/tei_preview/`, E90) is obsolete on both grounds and must not be promoted.

Documents: [journal.md](journal.md) session 89

### E100 Run-to-run stability measured: the LLM refinement is practically deterministic in CER effect (2026-07-07)

Occasion: the released stability pilot (5 documents x 3 runs, decisions "Stability" 2026-07-07) had neither tooling nor designated documents.

Execution: new harness `scripts/eval/stability_pilot.py` runs full `--force` regenerations into isolated `output/stability_runs/run{N}/` directories (the production step-2 cache and tei_final stay untouched) and measures fidelity CER per run over the canonical `evaluate_ocr` path. Documents 570, 2310, 1910, 830, 890 (stratified over layout types A/B/D and both languages; type C excluded, the only measurable candidate has 147 pages). 20 pages per run, 60 step-2 calls total, pipeline model `gemini-3.1-flash-lite-preview` (deliberately the configured production model, not 3.5-flash, for representativeness).

Result: per-document standard deviation of fidelity CER across runs 0.000 to 0.129 percentage points (mean 0.040, doc 2310 exactly 0); the refinement stage is practically deterministic in its text effect. The `stability` block in `docs/data/cer_statistics.json` is closed (`status: measured`) via a loader in `cer_statistics_full` that consumes `output/audits/stability_pilot.json`. Side finding: the ABSOLUTE fidelity of fresh regenerations lies far above the delivered corpus values (the delivered tei_final embodies accumulated corrections the pipeline caches do not reproduce), which independently reinforces the E99 ban on regenerating the delivered corpus. The pilot's absolute values are therefore not comparable to the headline; only the within-pilot spread is the measurement.

Documents: [journal.md](journal.md) session 89

### E101 Scan-versus-text mismatch resolved by the fidelity/scope decomposition, no document excluded (2026-07-08)

Occasion: operator question (vault register W5.1), the delivered TEI text and the ZBZ reference diverge in extent; does that force excluding the affected documents from the CER measurement? Write-up delegated to the agent on 2026-07-08.

Finding: the divergence is structural, not a recognition error. The ZBZ reference TEIs are selective partial transcriptions, so the pipeline is often the more complete text (journal masthead, a neighbouring review, a table of contents). A naive full-text CER punishes that completeness (doc 570 reaches an end-to-end CER above 100 percent purely from surplus text). The correct instrument is already in place and needs no new code. `classify_edit_operations` (`scripts/eval/evaluate_ocr.py`, `SCOPE_BLOCK_MIN = 50`) splits every Levenshtein operation into fidelity (substitutions, all deletions, small insertions under the threshold) and scope (contiguous insertions at or above the threshold). The split is exact, `cer_fidelity + scope_insertion_rate == cer_full` per document, and asymmetric by design: being more complete than the reference is not an error, being less complete is. Genuine losses stay in fidelity as deletions and are not absorbed into scope.

Verification against the data (2026-07-08): the decomposition reproduces exactly, `cer_fidelity + scope_insertion_rate == cer_end_to_end` for all 25 documents in `docs/data/cer_statistics.json` (0 mismatches), the recomputed fidelity mean is 2.08 percent and median 1.28 percent, identical to `overall.end_to_end_fidelity`. All 25 documents remain in the measurement (`n_excluded = 0`); the circular exclusion list was already removed by E73. The genuine text-loss case that the decomposition does not mask (doc 30, a double-page half) was adjudicated (E97) and repaired (E98) on its own track, which independently confirms that the decomposition isolates surplus text without hiding real loss. The independent counter-check (E91) reproduced every value from the documented specification without importing repo code.

Decision (resolves W5.1): keep all 25 ground-truth documents in the CER measurement; the reported quality figure is the end-to-end fidelity CER, mean 2.08 percent and median 1.28 percent (n=25, `docs/data/cer_statistics.json`). It is stated as an upper bound of the recognition error rate (E80, E91: the reference itself is fallible, and apparatus insertions inflate it without a recognition error). The scope-inclusive end-to-end CER stays a diagnosis figure, never a quality measure. Consequence for the talk and the project report: cite the fidelity headline with n=25 and the source file, name the `SCOPE_BLOCK_MIN = 50` threshold when the fidelity values are quoted (E91), and carry the `n_chars` selection-bias caveat when generalizing beyond the 25 documents (`selection_bias` in the JSON). No document is dropped, no separate mismatch metric is introduced.

Documents: [project-report.md](../docs/project-report.md), [journal.md](journal.md), cer-gegenprobe-2026-07-03.md (verification.md, appendix)

### E102 DTA-Basisformat conformity claim empirically refuted and removed; `zbz_hersch.rng` is the single format authority (2026-07-09)

Occasion: operator question whether the delivered TEI is actually valid against the DTA-Basisformat, as the report's opening sentence ("TEI-XML im DTA-Basisformat") claimed. The repository had never validated against the DTA schema; the validation authority has always been the project schema `zbz_hersch.rng` (E48, ODD-generated TEI P5 4.10.2 subset).

Finding (2026-07-09, official `basisformat.rng` fetched from deutschestextarchiv.de, RelaxNG validation via lxml): 0 of 285 `tei_final` documents are DTA-valid. The violations fall into deliberate project features on three levels. Header: the delivery-contract header (E68/E69) uses `idno@type` values and `biblStruct`/`bibl` in `sourceDesc` outside the DTA model (DTA requires `biblFull`). Infrastructure: `<revisionDesc>` (workflow-status projection, E42/E66) and `<facsimile>` (zone coordinates) do not exist in the DTA schema at all (zero definitions). Body: minimal-case isolation shows `div type="text"` (the E47 replacement value, valid in the project schema, is itself not a DTA type), `pb type="blank"` (E65), `head@facs`, and further project conventions violate the DTA content models. Decisively, ZBZ's own 25 reference TEIs also validate 0 of 25 against DTA, with genuine body-level violations (`TEI@type`, `div`/`pb` placement, `title` inside `head`); the ZBZ guidelines themselves claim only to follow the DTA "weitgehend" with documented deviations. Strict DTA conformity therefore contradicts the delivery contract, the provenance and facsimile deliverables, and the reference style the project is measured against.

Decision (operator, 2026-07-09): the project's format claim is the project schema `zbz_hersch.rng`, a TEI P5 subset formalizing the binding ZBZ editorial guidelines; the DTA-Basisformat conformity claim is removed from all living documents (report, pipeline.md, index.md, project.md, data READMEs, step-2 prompt, docstrings). No parallel DTA validation is introduced. Rejected alternatives: (a) transforming the corpus to DTA validity, which would strip delivered features and move the output away from the ZBZ reference style; (b) a stripped-down "DTA view" gate, tested and refuted because even the text bodies fail the DTA content models, so the gate would guard a format no project consumer requires. The guidelines' own DTA reference remains documented as source data (`data/source/guidelines/`); dated register and journal entries mentioning the DTA stay unchanged as snapshots.

Documents: [pipeline.md](pipeline.md), [project-report.md](../docs/project-report.md), [journal.md](journal.md) session 91

### E103 Print-OCR comparison values re-attributed from Crosilla to Greif et al.; Levchenko peer-reviewed version added (2026-07-09)

Occasion: verification of the literature comparison table against the cited full texts (web search) revealed that the four printed-OCR reference values (0.84% Transkribus Print M1 + Gemini 2.0 Flash post-correction, 1.27% Gemini 2.0 Flash zero-shot, 3.67% Transkribus Print M1 alone, 6.31% GPT-4o) were attributed to the wrong paper.

Finding (2026-07-09): the four values stem from Greif, Griesshaber and Greif, "Multimodal LLMs for OCR, OCR Post-Correction, and Named Entity Recognition in Historical Documents", arXiv:2504.00414, 2025 (German-language address books 1754-1870, predominantly Fraktur with one Antiqua source). The repository attributed them to "Crosilla et al. 2025 (arXiv:2503.15195)", which is Crosilla, Klic and Colavizza, "Benchmarking Large Language Models for Handwritten Text Recognition", an HTR benchmark that does not contain these values. The Levchenko 2025 attribution (arXiv:2510.06743, full-page CER Gemini 2.5 Pro 3.36%, Flash 4.94%, traditional OCR 21.55-45.96%) was verified correct; a peer-reviewed version exists (LM4DH 2025 workshop at RANLP 2025, Varna, pp. 75-85, DOI 10.26615/978-954-452-106-6-007).

Decision: the misattribution is corrected everywhere the four values appear (literature-comparison.md, docs/methode.html, the COMPARISON_LIT/LITERATURE_REFS blocks in scripts/eval/cer_statistics_full.py and cer_statistics.py, and the regenerated docs/data/cer_statistics.json). The "like-for-like" characterization tied to the old Crosilla reference was false (Greif is printed OCR, Crosilla is HTR) and was dropped. The Crosilla HTR paper is not retained as a separate reference in these documents because it served no independent function there. Regeneration of docs/data/cer_statistics.json changed only literature and meta fields; all measured CER values, confidence intervals and per_doc records stayed byte-identical.

Documents: [methodology.md](methodology.md), CER measurement section, [project-report.md](../docs/project-report.md)

### E104 Knowledge base aligned post hoc with the Promptotyping convention Knowledge Documents; frontmatter only, no renames (2026-07-31)

Occasion: the method paper "Promptotyping. Translating Research Data into Research Artefacts through Context Engineering and Agentic Engineering" cites this repository as evidence for a Promptotyping knowledge base. The paper's evidence citations pin the pre-alignment state to commit 5b78b69d. The knowledge documents already carried the mandatory core of the convention with nested `project` and `method` blocks; what was missing was the machine-readable link to the catalogue template each document follows, which only the journal and the project report carried.

Execution (2026-07-31, additive frontmatter pass): every document under `knowledge/` except the project report received the recommended `authors` field, and every document whose function matches a catalogue template additionally received the `template` object with name, version and latest URL. Mapped are index.md to Vorlage Index, project.md to Vorlage Projekt-Wissensdokument, specification.md to Vorlage Specification, journal.md to Vorlage Journal (already present, verified against the catalogue), and pipeline.md, workflow.md and infrastructure.md to Vorlage Architecture, whose scope section names `pipeline.md` for the flow through processing stages and `infrastruktur.md` for deployment and CI/CD as the regular splits of the Architecture function in larger systems. [index.md](index.md) gained a section that maps each document to its convention function.

Deliberately left freehand, because no catalogue template carries the function: decisions.md (the register split out of the Specification function; the catalogue has no template of its own for a decision register), cer-methodology.md (the convention names `cer-methodik.md` in OCR projects as a legitimate function without a template), ground-truth-map.md (a specialisation of the Material function as a deviation catalogue, without the corpus description that the Datengrundlage template structures), literature-comparison.md (state of research, no function in the catalogue), methodology.md (the working method of the project rather than scholarly domain knowledge, so Vorlage Domänenwissen does not carry), ecosystem-synthesis.md (a cross-project survey without the bilateral delivery contract that triggers the Integration function). A reasoned gap is a design decision and is marked as such in the index.

Kept unchanged, with reason: all file names, the document order and the whole prose layer, so that the paper's evidence citations against 5b78b69d stay readable. The `status` vocabulary of the repository (complete, reviewed, draft) extends the convention enum draft/active/archived and carries a review state the enum cannot express; the Promptotyping repository's own knowledge base carries the same extension, so the values stay. The `type` field from the vault vocabulary stays. `created` and `updated` stay as semantic project dates, older in part than the git history of the files, which starts after the consolidation of 2026-04-27. `generated-with` was set nowhere: the co-author trailers of each document span several model versions across its history, so a per-document value would state less than the git history does. The `authors` field names the human with curatorial responsibility, which the convention reserves for persons; the repository rule on personal names governs running prose, and the project report already carried the field. `arbeitsbericht-v3.md` was excluded from the pass because it carried an uncommitted working state.

Documents: [index.md](index.md), [journal.md](journal.md) session 92

### E105 Page-apparatus convention for entity marks: running heads unmarked, title pages, bylines and captions marked (2026-08-12)

Occasion: the entity evaluation of 2026-08-12 measured tier-1 precision at 0.952 over 293 decidable cases but had to leave the page apparatus open. By keyword heuristic, 56 of the 279 correct marks sit in running heads, title pages and bylines, document 330 alone carrying sixteen repetitions of the same running head, so a second reading of the precision figure was not computable before the convention was set (verification.md, appendix (evaluation result), section "Beschrieben").

Finding from the facsimile-adjudicated cases: a running head repeats the identical line at the head of every page of a volume, so each occurrence carries exactly the information the previous one already carried; the model case is a monograph whose own title stands as the running head throughout. Title pages, byline organisations (the university affiliation in a thesis byline) and picture captions behave differently, each naming a fact a reader would query; the model case is a museum catalogue whose captions name artists and holding institutions.

Decision (operator, 2026-08-12): running heads are not marked, because repeated page furniture is redundant as annotation. Title pages, byline organisations and picture captions are marked, because they carry research value. Rejected alternatives: marking running heads and flagging them as apparatus, rejected because the flag would preserve redundant information and inflate the mark population without adding a queryable fact; and a blanket apparatus exclusion, rejected because title pages and captions carry genuine research value. Consequences: a deterministic running-head suppression instrument becomes the follow-up work item, keyed on the repetition of the identical normalized line at page start across several pages of one document; and because the adjudicated verdicts are persisted per mention (E106), the convention reading of the precision measurement can be computed from the existing sample without drawing again.

Documents: [tei-mapping.md](tei-mapping.md), [verification.md](verification.md), [journal.md](journal.md) session 93

### E106 Entity consequence wave: derived matcher channels stay tier 2, adjudicated verdicts persisted snapshot-bound (2026-08-12)

Occasion: the entity evaluation named several consequences that needed no further operator decision (precision 0.952 over 293 decidable cases, recall coverage 0.552 with 28 of 30 misses classified as rule gaps). They were released as one wave of four parallel agents with disjoint file scopes; commits 8a0e34ae (exhaustive ref-in-list invariant gate), 40afccf2 (mention verdict store), c81b5922 (false-positive risk ranking plus adjudication protocol), 6487e0b6 (matcher rule repairs) and f130800c (preview and viewer-mirror regeneration).

Decision (a), tier policy for derived name forms: the five closed rule gaps (acronym case tolerance, parenthetical GND qualifier strip, static place-adjective inversion, superscript digits as word boundaries, person initials) run as a second pass over the finished base lexicon and emit tier-2 worklist candidates only, never tier-1 auto-marks. A shadowing guard keeps a derived form from overriding a base match, and the reject verdicts of the variant review bind derived forms as well. Rationale: safety over coverage. A derived form is an inference about a name, and an inference belongs in the channel a human reads before it enters the delivered text. Rejected alternative: tier 1 for derivations that look safe, rejected because the auto-marked layer carries the precision figure the delivery is judged on, while a candidate that only reaches the worklist costs a proposal. Measured against the frozen scan, the worklist grew by 1657 proposals while tier 1 changed by plus 9 (superscript footnote cases) and minus 1.

Decision (b), persistence of the adjudicated judgments: `data/entities/mention_verdicts.json`, built deterministically by `scripts/eval/build_mention_verdicts.py`, holds all 300 precision verdicts including the 50 blind second judgments of the agreement check and the 67 recall mentions, keyed by (doc, page, surface, gid, occurrence) and bound per document to a sha256 fingerprint of the source TEI. The key carries no character offsets, so a changed text surfaces as a stale fingerprint instead of a silently misplaced judgment; re-OCR or a stock correction therefore invalidates a verdict visibly. Rejected alternative: recording the provenance inside the TEI files only, rejected because regeneration erases it and because the judgments must stay readable outside the delivered documents, as the input of a re-measurement.

Documents: [tei-mapping.md](tei-mapping.md), [verification.md](verification.md), [methodology.md](methodology.md), governance section, [journal.md](journal.md) session 93

### E107 Viewer UI reduction: one document bar, two dropdowns, annotated reading view as default (2026-08-12)

Occasion: the operator judged the viewer over-structured (stacked border edges, redundant state labels, seven scattered panel controls) and decided the reduction step by step at screenshots; the chrome inventory in `reports/2026-08-12_viewer-ui-analyse.md` grounded the findings.

Decision (operator, 2026-08-12): the subtitle and the panel state labels are removed; document metadata, workflow pills and actions share one bar with one bottom edge, status words move into pill tooltips (the dot color carries the traffic light); the seven panel controls become two dropdowns, View and Edit, with Edit gathering layout, OCR and XML editing in one place; the page number between the pager arrows is the jump input; the view set is condensed to three (Text, OCR, XML) with the annotated reading view (rendered TEI plus GND entities and review candidates) as the default for every document (`entities=0` opts out) and markup highlighting as a toggle inside the view menu. Rejected alternatives: a visible segmented source control (rejected because three equally pressed buttons from two semantic groups misread as one active group), and a dedicated Entities view (rejected because the annotated text is the primary reading need and specialized views should be the exception, per operator).

Documents: [workflow.md](workflow.md), Entity Layer (read-only) section, the UI analysis of 2026-08-12 (deleted with E124, git ec42a613); commits e7f9dd6d, baecc433, d65854a3.

### E108 Author mentions always marked; running-head suppression active in the matcher (2026-08-13)

Occasion: two open points of the entity layer were ready for decision. The volumetrically largest open convention asked whether mentions of the corpus author herself are annotated (open operator decision 4 of the design plan; the recall evaluation priced the byline exception at four gaps in the drawn pages), and E105 had named a deterministic running-head suppression as its follow-up instrument, whose detector was already validated against the adjudicated ground truth. ZBZ feedback is not available in this project phase, so convention questions of the entity layer fall to the operator.

Decision (operator, 2026-08-13): mentions of the corpus author are marked like every other listed entity, in bylines and signatures as well; the byline exception of the caps channel is removed (matcher parameter `author_labels` and `CORPUS_AUTHOR_LABELS` deleted). At the same time the running-head suppression is switched on in the matcher: the detection core moved to `scripts/tei/running_heads.py`, shared by matcher and audit, and every candidate inside a detected head zone is demoted to tier 2 with the `:running-head` suffix. A demoted full name keeps its document-wide anchor power, because the head still names the document's subject. Rejected alternatives: dropping in-zone candidates entirely, rejected because the validated detector carries two known false alarms and a dropped candidate is invisible to curation, while a demoted one stays countable on the worklist; and letting suppressed heads lose their anchor power, rejected because bare surnames in the body would then drop to the worklist beyond the intended furniture scope.

Consequences: corpus scan, all 285 previews (schema-valid and text-invariant), viewer mirror, risk ranking and gold benchmark regenerated; no tier-1 mark sits in a head zone any more (suppression scope 671 candidates corpus-wide). The convention reading of the adjudicated precision is computed by `running_head_audit` (`convention_precision`, seeded percentile bootstrap) at 0.9511 over 266 decidable in-scope cases, within the interval of the protocol reading 0.952, so the running heads were not inflating the measured figure. One ground-truth caveat: a single adjudicated mark counts as a running head only through the keyword in its verdict reason while being body text (doc 2510), so the keyword criterion reads detector recall as 24 of 25 without a real head being missed.

Documents: [tei-mapping.md](tei-mapping.md), [verification.md](verification.md), [journal.md](journal.md) session 94

### E109 Adjudicated error classes repaired by deterministic guards; verdict store rebound to the frozen scan (2026-08-13)

Occasion: the operator directed the repair program toward capturing the work class and, beyond it, every listed entity. The facsimile adjudication of 2026-08-12 had confirmed nine wrong_entity and wrong_span cases (five of them naming a work or an institution where a person was marked), and corpus probes grounded each candidate rule before it was built: the scan invariant carried eleven hyphen-adjacent tier-1 marks, the citation frames matched twelve tier-1 full names, the eponymous container exactly one.

Decision (operator direction, implementation 2026-08-13): every confirmed error class receives a deterministic answer, grown from adjudicated cases only. Five guards demote to the worklist: hyphen at the span border (compound "UNESCO-Kommission"), author-initial citation frame ("Salamun K., Karl Jaspers, Munich, 1985"), editor-abbreviation frame ("Karl Jaspers, éd. P.A. Schilpp"), eponymous institution prefix ("Fondation Karl Jaspers"), undated parenthetical after a surname ("Augustin (de Malègue)"), and the lowercased incipit of a case-tolerant work title ("die Mauer", works only, because German inflects the leading adjective of organisation names). Two repairs correct the span: the internal particle bridge ("Saint Ignace de Loyola" as one mention) and the subtitle-join channel ("Nietzsche. Einfuehrung in das Verstaendnis seines Philosophierens" as one worklist span). Rejected alternatives: a broad italics guard for person names, rejected because the probe showed the signal mixed (interview labels and bylines in italics are genuine mentions); and a general citation-line detector, rejected as heuristic-fragile, so title-position names without a deterministic frame stay tier 1 for the judge stage. One recall exception is decided: the calendar formula "avant J.-C." never enters the lexicon.

Root-cause fix in the same wave: `build_mention_verdicts` read the live corpus scan, which E108/E109 made diverge from the population the sample was drawn from; the build now reads the frozen snapshot `entity_corpus_scan_frozen_2026-08-12.json`, and the store reproduces byte-identically however the live rules move.

Consequences: all nine adjudicated cases verified fixed at their corpus positions; the hyphen invariant of the scan reads zero violations; 285 previews schema-valid and text-invariant; the reference trend rose to tier-1 precision 0.67 with recall and coverage unchanged, which is the expected signature of pure false-positive removal; entity battery green.

Documents: [tei-mapping.md](tei-mapping.md), adjudicated precision guards, [verification.md](verification.md), [journal.md](journal.md) session 94

### E110 Verdict guard as standing regression gate over the adjudicated judgments (2026-08-13)

Occasion: the operator asked how agent-driven repairs can proceed without overwriting what the facsimile adjudication secured. The verdict store (E109) held the judgments, but nothing compared them against the live scan; the comparison was manual.

Decision: `scripts/eval/entity_verdict_guard.py` holds every adjudicated judgment against the current corpus scan and classifies it. Violations are exactly three cases: a correct mark that disappeared, a wrong_entity or not_in_source mark still asserted in tier 1, and an adjudicated real mention that no longer surfaces at all. Tier moves are reported, never violations, because rule changes move marks legitimately (the running-head demotion postdates the adjudication). Ambiguous candidates match over their `alternatives` list, and a changed document digest shields its records as text_changed instead of producing false alarms. The guard runs after every matcher, lexicon or text change; exit code 1 on violations makes it gate-capable.

Refuted in the same session: a matcher repair for footnote digits glued to names. The corpus probe showed the phenomenon does not exist on real names (the corpus writes true superscripts, which the scan already separates; the only glued ASCII digits sit in OCR garbage of two documents), and the adjudicated Nietzsche case already surfaces through the superscript rule. Verification replaced code.

First run evidence (2026-08-13, scan of the E109 state): 279 correct marks all survive (252 tier 1, 27 legitimate moves to the worklist), 10 of 14 wrong marks repaired, the 4 remaining are text-side defects outside the matcher's reach (OCR phantom on a blank leaf, hallucination loop, generated speaker duplication); of the 30 adjudicated misses 27 now surface and 3 remain (two of them the decided J.-C. exception of E109, one the newspaper short form "Populaire"). The empty unlisted report of 2026-08-12 was refuted by a fresh run; the proposal channel carries ranked candidates (top person-shaped: Raymond Aron, Pere Fessard).

Documents: [verification.md](verification.md), [journal.md](journal.md) session 95

### E111 Apostrophe folding between corpus text and entity lexicon (2026-08-13)

Occasion: the zero-mention classification wave (three Opus agents over the 42 list entries without a single match) isolated one root cause behind most missed work titles: the E94 stock correction normalized the corpus text to the typographic apostrophe U+2019, while the curated list and the GND cache carry ASCII U+0027, and the matcher compares literally. One French title alone was invisible in every document that cites it.

Decision: both sides fold U+2019 to ASCII at matching time, in exactly three places with one semantics: the scan projection (`entity_matcher._normalize`), the form registration (`entity_lexicon._collapse`), and the review-verdict key lookup (`_split_by_verdict`), so verdicts keyed with either spelling keep applying. Raw text, surfaces and offsets stay untouched; the fold exists only in the comparison space. Diacritic folding stays out (an accent difference is a real spelling difference, no adjudicated case requires it).

Consequences: 53 additional marks corpus-wide, five list entries left the zero-mention set (37 remain), the recovered title surfaces in 15 documents; the verdict guard (E110) confirms the identical adjudicated state before and after, no judgment violated; previews, viewer mirror and overview regenerated; battery green, ruff clean.

Documents: [tei-mapping.md](tei-mapping.md), [journal.md](journal.md) session 95

### E112 Curated-variant channel and list hygiene (2026-08-13)

Occasion: the zero-mention classification (E110 wave) isolated entries whose corpus spelling the GND norm form does not carry, and one placeholder defect in the curated list. The operator released the open work program for agent execution; list content changes stay orchestrator-applied, never agent-applied.

Decision: the curated list gains an optional per-entry field `variants`, the operator's channel for corpus spellings ("Kolumbus" for "Colombo, Cristoforo"). Every string runs through the form derivation of its category headword with form source "curated-variant" and takes the tier its own shape earns; the field lifts nothing into tier 1 by itself. Curated variants bypass the cache-variant review split (operator authority outranks the review of generated forms); `entity_lint` validates the field (list of non-empty strings, no in-entry duplicates by fold, no headword echo, cross-entity collisions as warnings). Applied stock: the "Test" placeholder (gid 000000) left the list; twenty entries received evidence-backed variants from the classification report. Deliberately not added, each with its reason in the wave report: bare "Elie" (homograph with a listed historian), "Phedre" (mostly Racine's title), "Hadassah" (organisation homograph), the subphrase "Le probleme du mal" (common philosophical French, tier-1 shape), "Bund"/"Populaire" bare short forms (precision holes without a context rule), the work "Karl Marx" (person-name homograph).

Consequences: lint green with the two hard-coded real-stock expectations updated (placeholder gone from the 404 set); the verdict-store reproduction test became digest-aware, because legitimate text repairs move the live fingerprint while every adjudication payload must still reproduce (the guard consumes the drift as text_changed).

Documents: [project.md](project.md), data section, [tei-mapping.md](tei-mapping.md), [journal.md](journal.md) session 95

### E113 Pointwise text repairs of the three adjudicated OCR defects (2026-08-13)

Occasion: the verdict guard held four adjudicated-wrong marks in tier 1, all of them text-side defects (E110). The operator released the repair.

Decision: three pointwise, facsimile-verified, backed-up repairs on `output/tei_final/` (backups `output/_backup_pre_text_repairs/`, evidence report `output/audits/text_repairs/report.json`). Doc 900: the degenerate OCR loop of the Jaures spread truncated after the last facsimile-corroborated sentence. Doc 1520: the ghost page transcribed from a blank leaf's show-through replaced by the house blank convention (`<pb type="blank"/>`, pb kept so page ordinals stay stable); the page-level blank ruling outranks the single ghost-legible heading mark. Doc 2330: the two adjudicated speaker echoes unwrapped to plain paragraphs. The six further sp/speaker title-echo constructs of doc 2330 sit on interview and credit content where the correct repair differs; they stay a named open generator defect rather than a bulk fix.

Consequences: validator and corpus schema gate green; CER chain re-run, headline unchanged (fidelity mean 2.08, median 1.28, `docs/data/cer_statistics.json` regenerated), so the repairs lie outside the partial-transcription reference scope; the guard now classifies the three documents' records as text_changed instead of carrying violations.

Documents: [methodology.md](methodology.md), CER measurement section unchanged, [journal.md](journal.md) session 95

### E114 Facsimile mapping via pb anchors in the delivery chain (2026-08-13)

Occasion: the adjudication had marked three mentions undecidable because the viewer showed the wrong facsimile; the defect class (double-page spreads, more text pages than scans) was identified on docs 1350 and 120.

Decision: the generated mirror carries a per-document sidecar `{doc}_facs.json` mapping text page to image file, derived from `pb@facs` resolved against the TEI's surface/graphic elements; the viewer prefers the sidecar and keeps the sequential convention as fallback; the page cap counts text pages instead of scans so spread pages stay reachable. The corpus audit of the pb-to-facs sequences found the affected population (spreads, cover-offset starts, irregular anchor reuse) and lives in `output/audits/facs_mapping_report.json`.

Consequences: doc 1350 text pages 5 and 6 resolve to the correct third and fourth scan; the layout-overlay stream still resolves per text page and is a named follow-up, because sharing one scan's curated layout between two text pages is a data-model decision.

Documents: [workflow.md](workflow.md) persistence section to be extended on the next touch, [journal.md](journal.md) session 95

### E115 Figure zones scanned and demoted instead of excluded (2026-08-13)

Occasion: the zero-mention classification proved that the blanket `<figure>` exclusion loses real content; the Chagall plate catalogue (doc 760) keeps its whole provenance apparatus (Fondation Maeght, Maeght editeur, Galerie d'Etat Tretiakov, Musee d'Art Moderne) in captions the matcher never read.

Decision (operator-released program, reversible middle path): `<figure>` zones take part in the scan, and every candidate inside is demoted to the worklist with the ":in-figure" suffix; the machine asserts nothing there, exactly like the running-head convention. Suffix order extends to base rule, derived channel, ":ambiguous", ":suspect", ":in-plain-bibl", ":in-figure", ":running-head" last. A demoted full name keeps its document-wide anchor power. The apparatus exclusion (E-Periodica cover, photo credit lines) stays. The unlisted proposal channel reads figure zones on purpose, because plate captions carry exactly the unlisted names. Rejected alternative: marking figure candidates tier 1, rejected because caption identity (depicted person against owning institution against work title) needs the caption read.

Consequences: corpus-wide the change adds worklist candidates only, the tier-1 population is unchanged; doc 760's provenance apparatus is fully visible; overview gains the class "figure"; the gold-benchmark miss fixture moved off figure captions. Downstream follow-up recorded: the layout-overlay stream of spread documents still resolves per text page (E114 note).

Documents: [tei-mapping.md](tei-mapping.md), [journal.md](journal.md) session 95

### E116 Dotted-abbreviation guard and hyphen reach of the surname index (2026-08-13)

Occasion: the operator questioned a tier-2 hit "S.S." inside "U.R.S.S." on the review list. The empirical classification of all 1113 initials candidates against the raw TEI showed that not one occurrence of "S.S." or "S. S." was a genuine mention; all of them sat inside "U.R.S.S.", "U.S.S.R." or "S.S.P.". The same defect produced the document outlier of the interview transcript in doc 2330, where the interviewer label "G.D.K." fed 351 candidates for the surface "G.D.". Independently the scan reported zero candidates for hyphenated single-token names, although "Merleau-Ponty", "Cohn-Bendit" and "Lao-Tseu" occur in the corpus.

Decision: two narrow repairs in the matcher. An initials hit is dropped when the raw text directly adjoins a single-letter dotted token on either side, so an abbreviation is recognized as one contiguous run. The test runs on the raw text rather than the normalized projection, because markup between two initials groups separates two mentions; a normalized test kills the 35 genuine speaker labels of doc 1220, where "J. H." as speaker and "J. H." in the paragraph collapse into one run. The surname channel extends a hit across a hyphen as far as the index still carries the compound token, which closes the gap that the word-end cut opened against the 210 hyphenated surname keys. An unknown second token changes nothing, so the compound demotion of "Jaspers-Kreis" stays.

Consequences: the worklist loses 442 candidates that were provably no mention, the tier-1 population is bit-identical, and 22 truncated suspect spans become correct spans ("Merleau" plus "Ponty" to "Merleau-Ponty", "Bendit" to "Cohn-Bendit"). Three list entries leave the zero-mention set. The verdict guard confirms the identical adjudicated state, no judgment violated. Recall accounting turns six partial hits of the surface "G.D.K." from "now_worklist" to "still_missing", which restores the honest state; a three-letter initials form derived from a hyphenated surname would close them and is a recall feature, not part of this repair. Open on the data side: the work entry with GND id 454611536 stays unreachable because the variant cache holds a 404 for it, so the title never enters the lexicon; `entity_lint` reports it, and it needs either a resolvable id or an exception for operator-curated titles.

Documents: [tei-mapping.md](tei-mapping.md), [journal.md](journal.md) session 95

### E117 The entity overview carries ambiguity and adjudicated quality (2026-08-13)

Occasion: the overview page counted a candidate only for its reported id, so an entity that occurs exclusively as the other possible bearer of an ambiguous surface was displayed as "not found". Three list entries were affected, one of them sixteen times. The page also showed volume only, never the measured quality, although the adjudicated judgments have been available since the evaluation wave.

Decision: the mirror gains three blocks and the page renders them. Ambiguity is counted separately as `alternative_only` per entity and as `ambiguous_mentions` in the totals, never folded into the auto and review counts, so the existing series stays comparable. The quality block projects the adjudicated sample from the verdict store, precision with its confidence interval, the raw recall status distribution, and the second-judgment agreement including both open disputes; recall stays a set of raw counts because the evaluation method defines no single rate, which keeps an invented formula out of the delivery surface. A provenance block names the scan digest and the list size, so a displayed number can be traced to the run that produced it. Every rate is displayed next to its sample size, because the sample is evidence about the corpus rather than a corpus-wide fact. Icons are inline SVG in the text colour; the standing ban on emojis and unicode status symbols is untouched by this.

Consequences: the completeness question the page exists for is answered without the ambiguity distortion; the delivered instrument states what was measured, on which sample, and against which run. The pilot preview lost its separate HTML report in the same step, since the overview page is now the reading surface. Open: the sample-based recall of the annotation layer remains the weakest measured value and waits on the adjudication wave over the frozen 2026-08-13 draw.

Documents: [verification.md](verification.md), [journal.md](journal.md) session 95

### E118 Every mark carries its provenance and verification state (2026-08-13)

Occasion: the operator asked that an annotation state in the data itself who asserted it and whether a human checked it, so a later pass can separate settled marks from open ones and so the annotation stays auditable outside this pipeline.

Decision: three things stay separate and never merge. Provenance names the asserting agency and travels as `@resp` pointing to a `respStmt` this run declares per document, so no document declares a responsibility none of its marks uses. The verification state travels as `@cert` and takes only the tokens `high` for an adjudicated-correct mark and `medium` for a plain matcher assertion; a number never enters, although the schema would accept a double, so the ban is a project rule with its own test rather than a schema effect. The producing rule travels as `@source`, the one attribute the delivery schema permits on `persName`, `orgName` and `bibl` alike, since `bibl` carries no `@evidence` and `@ana` exists nowhere in the schema. The measured reliability of a rule class stays out of the individual mark and remains a property of the adjudicated sample. Only responsibilities with a real producer are declared, so no model judge appears until one exists. The verdict store stays the source of truth of the judgments; the attributes are a regenerable projection that reuses the classification of the verdict guard, so a document whose text moved since the adjudication falls back to unverified instead of claiming a verification its bytes no longer support. The version of the assertion is a digest over the rule-bearing modules, because a hand-maintained version constant ages silently.

Consequences: the preview panel wraps its marks with provenance, schema validity and text invariance unchanged, two runs byte-identical. A mark with an adjudicated-wrong judgment is deliberately not suppressed inside the writer, because the verdict guard exists to fail such a run loudly and a silent drop would mask the regression. The delivered TEI stays untouched; whether these attributes belong in the delivery is the library's decision, its guidelines require the inline reference and say nothing about certainty.

Documents: [tei-mapping.md](tei-mapping.md), [journal.md](journal.md) session 95

### E119 Operator marking policy: anchor-free surnames and generic work titles (2026-08-13)

Occasion: the anchor rule requires a full-name anchor in the same document before a bare surname reaches tier 1, which punishes exactly the canonical authors philosophical prose never spells out; the evidence table counted several hundred review candidates for single such names. In the opposite direction, generic titles flooded the worklist with surfaces that are ordinary words in running text.

Decision: the operator decisions live in `data/entities/marking_policy.json`, deliberately apart from the curated entity list, which is an external export and may be replaced wholesale. Twenty-eight surnames are released from the anchor requirement for exactly the keys the entry names, so nothing derived from a released key inherits the release, and every demotion suffix keeps its effect: a released surname inside a running head, a figure zone, a plain bibl or under a suspicion signal stays on the worklist. Seven generic titles leave the marking scope entirely, three are bound to typographic corroboration. One surname was held out because person and work reading are not locally separable and the list carries no work entry the surface could resolve against. The policy is a trust boundary, validated on load, and a gid absent from the list is an error rather than a silent skip. Rejected alternative: an entry-level field inside the entity list, rejected because a re-export would silently drop the decisions.

Consequences: the worklist loses roughly a third of its volume while the auto-marked layer grows by about the same number of marks; the verdict guard stays at zero violations. One title left the corroboration bucket during verification, because the guard proved that the condition destroys a facsimile-verified recall mention where the corpus spells the title as a compound without typographic frame; a verified judgment outranks a rule change. The corpus-wide preview run now covers every document with schema validity and text invariance, a gate previously proven on ten documents only. A defect the corpus run exposed: the responsibility declarations of E118 sit in the header and move every body offset, so the viewer mirror dropped nearly every worklist entry as stale; the preview runner now records that shift per document and the mirror consumes it.

Follow-up, binding: the released marks exist in no earlier draw, so the published precision no longer covers the whole auto-marked layer until a supplementary sample is adjudicated ([verification.md](verification.md), population validity).

Documents: [tei-mapping.md](tei-mapping.md), [verification.md](verification.md), [journal.md](journal.md) session 96

### E120 Repository refactoring: diagnosis, plan and wave 0 (2026-08-21)

Occasion: six read-only audits (inventory, knowledge overlap, reports and static pages, scripts layout, frontend, code hygiene and tests) found stale statements in durable documents, duplicated facts against the single-source rule, published CER figures on methode.html that contradicted `docs/data/cer_statistics.json`, a screening-era script contradicting E66, a dead proxy function, generic libraries filed under `tei/`, the entity layer spread over three folders, 368 ruff findings outside the entity layer, 26 untested scripts and missing tooling gates.

Decision: the refactoring runs by a written wave plan, executed in waves of parallel Opus build agents with exclusive file sets, each wave followed by independent code and document verification and one coherent commit per package. Operator decisions: full scope (documentation, code hygiene, scripts layout, frontend); obsolete artifacts are deleted and git history retains them, the register names the last carrying commit; `knowledge/` keeps its thematic split and is streamlined to one owner per fact; the journal is condensed for sessions 69 to 96 and gets an archive document. Rejected alternatives: an archive folder for obsolete artifacts (keeps dead weight in the tree), a strongly condensed knowledge base of few large documents (changes every cross-reference for little gain).

Wave 0 executed: documentation freshness corrections (D1, D3, D5 of the plan) and code quick fixes (per-file ruff ignores for the 37 deliberate findings, safe auto-fix 368 to 147, absolute scan path in `generate_entity_overview`, `openpyxl` declared, one `.env` mechanism via `scripts.config`, `compute_proxy_quality` and `--proxy` removed). Deleted: `scripts/tei/tei_add_revision.py` (last carried by commit 03c478d1). Verified: 2149 tests passed and 1 skipped, ruff 147, all CLAUDE.md commands resolve, mirror diff empty, benchmark output identical.

Open, assigned to WP1a: the published confidence intervals are percentile bootstrap (generator `ci_method` throughout, `bca_ci` never called in `cer_statistics_full`) while CLAUDE.md, index.md, specification.md, methodology.md and `meta.bootstrap_method` say BCa.

Documents: E120 to E124 in this register, [journal.md](journal.md) session 97

### E121 Refactoring wave 1: knowledge ownership, reports consolidation, code hygiene to zero (2026-08-21)

Occasion: wave 0 (E120) corrected stale statements; the duplicated facts, the accumulated reports and the remaining ruff findings outside the entity layer were still open.

Decision: four parallel build agents with exclusive file sets, two independent verifiers, one commit per side. Knowledge ownership (WP1a, WP1b): each duplicated fact of the plan's D2 list now has one owner and cross-references elsewhere; methodology.md carries no command blocks and owns the `--dry-run`/`--force`/`--reassemble` conventions; workflow.md owns the status semantics; pipeline.md owns the E22 clarification and the `revisionDesc` shape; ground-truth-map.md owns the reference phenomenon attestations (verified by counting over the 25 reference files); cer-methodology.md states the computed interval method (document-level percentile bootstrap; `bca_ci` exists in the library and is called only by aggregation functions the published pipeline does not use); specification.md gains R-ENTITY. Reports (WP2): `2026-07-07_verifikation-berichtsfragen.md`, `2026-08-12_doku-frontend-audit.md`, `2026-08-12_workflow-entitaetsannotation.md` and `m3-reassemble-preview.md` deleted after their unique content was secured (three kinds of knowledge and the redraw ordering in entity-evaluation.md; the class-wise principle, the qualitative gold-benchmark reading, the M7 methode.html item and the shared-module requirement for the stock marker in entity-integration.md); `knowledge/ecosystem-synthesis.md` moved to `reports/2026-06-07_ecosystem-synthesis.md` as a dated snapshot; `docs/folien-entitaetsannotation.html` moved to `reports/2026-08-12_folien-entitaetsannotation.html` (off the Pages root, links rewritten). Five diagnosis findings of the deleted verification report have no owner yet and are recorded in the plan for the operator. Code (WP3): `tei_reassemble_preview.py` and its test deleted (E99; last carried by f6eba697); four new test modules for `page_xml_generator`, `mets_generator`, `audit_common`, `running_heads` written before their format strings changed; ruff 147 to 0 under the unchanged curated configuration (dead code, printf formatting, `Path.open`, explicit `T | None`, `zip(strict=True)` at eight guarded sites and `pairwise` at one, remainder); re-derived `output/` paths replaced by `scripts.config` constants; one Gemini client factory `scripts/core/gemini.py` (key resolved per call, same precedence and fail-fast); spell checkers cached behind an accessor; lxml skip guards turned into hard imports; the stale doc-530 skip rebuilt as a synthetic schema-valid case. Rejected: moving the Gemini error message to stderr inside this wave (house guideline, but a behaviour change; deferred).

Verified on disk by two verifiers and the orchestrator: 2204 tests passed, 0 skipped (delta reconciled: minus six preview tests, plus sixty new, health cases swapped); ruff 0; all 77 CLAUDE.md commands and flags resolve; mirror regeneration leaves `docs/data` unchanged; benchmark JSON hash identical with the `generated` key dropped; `tei_validator --all` 285/285 valid; every relative link in README, CLAUDE.md, scripts/README.md, knowledge/ and reports/ resolves; no removed statement without an owner; entity-layer modules untouched apart from one docstring phrase.

Latent findings recorded, not acted on: `tei_step3` Fix-D unwrap drops text standing directly inside `<epigraph>` before its first child (empirically inert on the corpus, guideline decision pending); `eval_report.py` lost a nested conditional whose two else branches were both empty, so a second CSS class for the middle CER band existed as intent only; `meta.bootstrap_method` in the generator still says BCa (operator decision, default is the percentile label); `reports/2026-08-12_viewer-ui-analyse.md` names the deleted 2026-08-12 paper in an inline code span and stays byte-unchanged by decision.

Documents: E120 to E124 in this register, [journal.md](journal.md) session 97

### E122 Refactoring wave 2: scripts layout, journal archive, frontend (2026-08-21)

Occasion: after waves 0 and 1 the remaining structural items were the scripts layout (generic libraries under `tei/`, the entity layer over three folders), the journal's length, and the frontend findings of the audit (cache versions, chrome drift, 286 requests per catalog load, German strings in the English viewer, dropped mark provenance, missing keyboard paths, third-party resources, one viewer file with seven concerns).

Decision and execution: WP4 moved `pb_split` and `tei_xml_utils` into `scripts/core/` and seventeen modules into the new package `scripts/entity/` (the fifteen entity modules plus `running_heads` and `running_head_audit`, because the matcher imports the running-head core), basenames kept by operator decision; `layout/__init__.py` lost its executable body to `layout/overlay.py` so package imports no longer load PIL; private cross-imports became public in their owning module; `ocr_pipeline --engine auto` resolves to gemini. The preview fingerprint digests module bytes including import lines, so every preview's `respStmt` now records the new digest without any rule change; accepted, previews are regenerable. The worklist provenance label in the mirror follows the new path (285 files, label line only). WP5 moved the full entries of sessions 69 to 96 byte-identically into `journal-archive.md`, left one compact line per session carrying decision ids and commit hashes, and raised the entry template to v0.3 (past tense, length cap, mandatory register reference, archiving rule); CLAUDE.md rule 1 follows. WP6 unified the asset versions, re-synced the page chrome and restored the Entities link, replaced the 285 manifest fetches of the catalog by one generated `manifest_index.json` with a fallback, loaded `core.js` on the entities page and promoted diacritic folding into `ZBZ.fold`, translated the viewer strings, rendered `@resp/@cert/@source` in the entity popover, added keyboard navigation to the menus, a native dialog, skip links and reduced-motion support, deleted five dead rules and two dead exports (two rules the audit called dead are live through string-built class names), split `viewer.js` into six `ZBZ.Viewer` modules with four `ZBZ.bus` events, vendored OpenSeadragon 5.0.1 and the three font families with their licenses (no third-party requests, data-protection section on the imprint). The bootstrap label of the statistics generator moved to percentile and `docs/data/cer_statistics.json` was regenerated with seed 42: every CER block identical, only `meta` and the proxy block changed, because the proxy cache the published file carried predated the 2026-07-07 stock corrections (verified on the pre-run backup); the corpus estimate on methode.html follows.

Verified on disk: 2212 tests, ruff 0, all CLAUDE.md commands resolve, corpus scan and benchmark hashes identical, mirror regeneration leaves `docs/data` unchanged, 285/285 valid, every asset 200 under a local server, zero third-party hosts, headless Chrome without console errors on all pages and the interaction list. One regression of the module split found by the verifier and fixed before commit: the dialog cancel listener in `viewer.js` read a variable that had become private to `viewer-persist.js`; the listener now calls the exported `cancelFsaInfo`.

Latent and deferred: `scripts/eval/cer_statistics.py` still computes and labels BCa in its own aggregation and defaults its output to the published path, so a run of that second generator would overwrite the file with BCa labels (WP7, single source); the viewer page carries no `aria-current`; `reports/2026-08-12_viewer-ui-analyse.md` cites pre-split viewer line numbers; the preview fingerprint stays path-dependent until the digest normalizes import lines.

Documents: E120 to E124 in this register, [workflow.md](workflow.md), [journal.md](journal.md) session 97

### E123 Refactoring wave 3: shared helpers, tooling gates, test suite strengthening (2026-08-21)

Occasion: after wave 2 the remaining items were the duplicated helpers across the audits, the hand-rolled path bootstraps, the second generator able to overwrite the published statistics with BCa labels, the half-migrated manifest without lock, pre-commit or linter gate, and the test-quality findings (generator and validator rules untested outside the vanishing corpus gate, no shared fixtures, the clone blind spot invisible).

Decision and execution: WP7 centralized `ascii_only`, `parse_doc_ids`, `facsimile_path`, `sorted_counts` in `audit_common`, `pb_offsets`, `page_of`, `extract_pages_from_final` in `core/pb_split`, `split_paragraphs` in `core/loaders`, `read_json_strict` in `utils` (the lenient `load_json` swallows broken files, the trust-boundary readers must fail fast); the variant differences were resolved on the majority form and reported (a `None` input and whitespace inside comma lists, neither reachable from the callers); `discover_doc_ids` in the preview runner became `discover_final_doc_ids` because its semantics differ from the shared helper; all eight `sys.path` bootstraps removed and the two path-form commands documented as `python -m`; the statistics library CLI writes to `output/evaluation/` so `cer_statistics_full.py` is the only writer of `docs/data/cer_statistics.json`; `requirements.txt` migrated into `pyproject.toml` with a `layout` extra and a `dev` group pinning ruff, CI installs from the manifest and runs ruff before pytest, a pre-commit hook pins the same ruff; no `uv.lock` because uv is absent on the workstation (`uv lock` pending). WP8 added five contract files (step 1 plus assembly end to end without Gemini with RelaxNG validity, all 22 validator rules with firing and silent fixtures, blank-page rule and marker with idempotence, catalog field contract against the keys the frontend reads, the two one-sided guards), a `conftest.py` with shared builders replacing thirteen local ones and the near-verbatim lexicon fixtures, the markers `requires_corpus` and `requires_mirror` so the clone-safe subset is addressable, the weak tests repaired or deleted, thirteen direct CER extraction rule tests indexed to the catalog, and the step-2 repair path under test. The orchestrator closed the data-loss defect the repair tests exposed: an empty or whitespace-only model answer passed the well-formedness check and replaced the page scaffold with nothing; `process_page_step2` now keeps the repaired scaffold, the test pins it.

Verified on disk: 2344 tests passed, 0 skipped, of which 1447 run on a fresh clone; ruff 0; all CLAUDE.md commands resolve; benchmark and corpus-scan hashes identical; mirror unchanged; 285/285 valid; manifest, workflow and hook files parse.

Incident: WP7 ran `entity_eval_sample --seed 42` as a smoke test and overwrote the frozen evaluation draw under the gitignored `output/audits/eval_sample/`, which the adjudication protocol forbids. The agent reconstructed the draw from the frozen scan snapshot, froze the matching catalog state beside it, restored four page values from the versioned verdict store, and reverted the rewritten `data/entities/mention_verdicts.json` with a checkout; the tracked data is unchanged. The draw is now derivable from two frozen inputs and is a reconstruction rather than the original file set; a deliberate re-freeze decision is the operator's. The lesson, binding for every later wave: verification runs name an allowlist of scripts, and anything writing under `output/audits/eval_sample*` or `data/` is excluded by name.

Recorded, not acted on: the CER catalog says a page break stays recognizable as a double newline and implies a running-head exclusion, while the code collapses the break to one space and includes `fw` text (tests pin the code; the catalog is to be corrected); `serialize_tei_fragment` drops the namespace declaration of a foreign-namespace element and returns an unparsable fragment (no corpus impact known); the catalog JS carries a fourth UI-only status token `ausstehend`.

Documents: E120 to E124 in this register, [journal.md](journal.md) session 97

### E124 Refactoring wave 4: the knowledge base recut by function and capped at ten documents, reports dissolved (2026-08-21)

Occasion: after waves 0 to 3 every fact had one owner, but the folder was still cut by topic, several convention functions had no carrier (quality assurance, verification, planning, design, integration, material, governance), forward-looking sections sat in seven documents, and the operator set a cap of ten documents with no loss of information and asked for the reports folder to go.

Decision and execution: four sub-waves. 4a extracted eight function documents from the topic-cut sources without touching them (data, tei-mapping, verification, plan, testing, design, integration, governance), each to its catalogue template. 4b pruned the sources, every removed section confirmed in its owner by a distinctive phrase, history and negation lists removed, workflow.md section numbers dropped, the engine picture corrected to the code (Gemini as resolved default, Mistral selectable as reproducibility record with a 401 endpoint), CER catalog rules E8 and running heads aligned with the extractor and its tests. 4c merged the eight into ten carriers, duplicates removed: project.md absorbed data and integration; pipeline.md absorbed infrastructure; workflow.md absorbed design; methodology.md absorbed cer-methodology and governance; verification.md absorbed testing and, as its appendix, the four dated holdings of the reports folder (adjudication protocol, evaluation result, CER counter-check, false-positive hunt protocol); decisions.md absorbed plan and received the rewritten register links; journal.md took the archive of sessions 69 to 96 back as its last section. index.md was rebuilt to Vorlage Index with a function map per document and section. Frontmatter repo-wide: core keys, `version: 1.0`, `template` where a catalogue template exists, `absorbed` naming the merged functions, no `type`, `tags`, `dependencies` or `source`; the new gate `tests/test_knowledge_frontmatter.py` pins the document set, the contract, the equal version, resolvable links and the absence of horizontal rules. Pointers outside the base followed: CLAUDE.md knowledge list, design pointer, entity heading and comment pointers, the vendored-assets line; README documentation table and eight pointers; scripts and data READMEs; the tei-quality-editor skill; twenty script and test docstrings; the entity-overview tooltip with its cache-busting bump and the `method` string the overview generator writes into the mirror (regenerated, the only change under `docs/data/`).

Deleted, git holds them at ec42a613: entity-integration.md, entity-evaluation.md, ground-truth-map.md, literature-comparison.md, agent-orchestration.md, data.md, integration.md, infrastructure.md, design.md, cer-methodology.md, governance.md, testing.md, plan.md, refactoring-plan.md; the whole `reports/` folder (2026-06-07 ecosystem synthesis, whose cross-project picture the vault carries; the 2026-08-12 viewer UI analysis, whose four open quick wins moved into the plan block; the 2026-08-21 entity concept report, whose substance lives in tei-mapping.md and verification.md; the four holdings now in the verification appendix; the journal archive now in journal.md). Moved: the 2026-08-12 slide deck to `workshops/`. The client report stays in `knowledge/` beside the ten until its pending edit is committed, then moves to `docs/`.

Verified on disk: 2344 tests passed, ruff 0, the frontmatter gate green over the ten carriers, every relative link in README, CLAUDE.md, knowledge/ and the script docstrings resolves, `docs/data` diff limited to the method string, all CLAUDE.md commands unchanged. Two verifiers ran on 4a and 4b (nine and nine defects, fixed before the commits); 4c was verified by the orchestrator's sweeps (structure, prohibitions, links, gate) after the operator asked for fewer agent rounds.

Recorded, not acted on: the CER counter-check in the verification appendix keeps its bold paragraph labels as a verbatim dated holding; register entries and archived journal entries name the documents that existed at their date in prose; `project.md` carries repeated H4 names (ZBZ, Transkribus, teiCrafter) under several integration subsections, which produces duplicate anchor slugs if anything links to them.

Documents: [index.md](index.md), [journal.md](journal.md) session 98

### E125 Knowledge base verified claim by claim against code and data; client report rewritten as v3 and moved to the site (2026-08-21)

Occasion: after E124 the operator asked whether the ten documents were correct, precise and well formulated, and for the client report to be improved, given an English name and taken out of `knowledge/`.

Decision and execution: one Opus agent per document, nine in parallel and the index last, each with an exclusive file, checked every verifiable statement against code, schema, tests and data, fixed wrong claims in place with `path:line` evidence in `output/refactoring/wave5_*.md`, rewrote imprecise sentences and applied the house style; dated register entries, journal entries and the verification appendix kept their content. The agents reported their sibling findings instead of editing siblings, and the orchestrator settled them: the O27 source (editorial guidelines), lesson L5 (`--force` bypasses the step-2 cache), the E92 provenance of the reference reading, the caption sentence of the plan (figure zones scanned and demoted, E115), the viewer entity switch (`entities=0` opts out since E107), the stale W18 label (639-2/T), the config comment on the OCR default, the data README tree (`entities/`, June delivery folder), the guideline README pointer (tei-mapping.md), and the method page (methodology.md pointers, Levchenko range, regeneration date). The client report was rewritten as v3 from the operator's working state: export artefacts removed, facts aligned with the repository (engine default and Mistral endpoint, the ten-document base, the entity preview layer with its measured precision and coverage, literature attribution to Greif et al. per E103, full-text and scope means of the current regeneration, the 1520 value, the script inventory including `entity/`, footnotes deduplicated and renumbered), frontmatter to Vorlage Report 0.2 with `status: snapshot`, English title and file name, moved to `docs/project-report.md`; every pointer followed (CLAUDE.md, README, index, register links, methodology, specification, project, method page) and the gate's tolerated set removed, so `knowledge/` holds exactly the ten carriers. A tenth agent reviewed README.md and CLAUDE.md read-only; the defects it found were fixed (status literal `unverifiziert`, catalog path, conditional `entities` stream without a pill, JSZip line, stale session range, screening count, horizontal rules, missing gate lines, quick-start premise, credentials pointer, license spelling, citation section), and its proposal to subtract the passages CLAUDE.md duplicates from the knowledge base (manifest semantics, save mechanism, marking-policy rationale, per-document gloss) stays with the operator.

Verified on disk: 2393 tests passed (2350 in the suite plus the 43 of the knowledge gate), ruff 0, frontmatter gate green over the ten carriers, every relative link in README, CLAUDE.md, data README, the report and `knowledge/` resolves.

Recorded, not acted on: unverifiable claims per document are listed in the wave-5 reports (engine figures without code evidence, Transkribus band edges, the commission date, the methodology literature without identifiers); E80 keeps its Crosilla attribution as a dated record superseded by E103; the `comparison_lit` block of `docs/data/cer_statistics.json` and the comparison tables differ in the Levchenko GPT-4o row and the guide-value row; the demo table names five documents while `.gitignore` whitelists four image folders, moot once the external image repository (f8191e34) carries the facsimiles; `output/audits/entity_eval_report.json` carries a method string naming dissolved documents and regenerates with the next run.

Documents: [journal.md](journal.md) session 99, [project-report.md](../docs/project-report.md)

### E126 Facsimiles online from a separate image repository (2026-08-21)

Occasion: the operator asked how all page images could be made available online. `docs/images/` holds the page PNGs locally (about four gigabytes) and is gitignored except for a five-document demo set, so the online viewer showed no facsimile for the rest of the corpus.

Decision: the published facsimiles live in the separate repository `chpollin/zbz-hersch-images`, served by its own GitHub Pages, as JPEG (150 dpi, quality 80) with the same folder and file naming as the local PNGs. The viewer switches by host (`ZBZ.imageBase` in `core.js`, set on `github.io`, empty locally), so local use keeps the PNGs. A new script `scripts/edition/export_web_images.py` writes the JPEG set idempotently; `--out` may target the image repository directly. Regenerations of the whole set are committed as a fresh orphan history and force-pushed, since the repository is a mirror of generated files.

Alternatives weighed: an object store with a private bucket and an access layer in front (fits a delivery restricted to the ZB, needs an account and a CORS rule), a IIIF server on the ZB side (the cleanest route, depends on the ZB), and committing the JPEGs into this repository (fits under the Pages limit but grows the project history with every regeneration). The separate repository needs no account, no CORS configuration and keeps this repository small; it cannot restrict access.

Execution: demo set pushed first as a mechanism test, then the complete set on the operator's instruction after the rights question was raised twice; stage table, scripts inventory and this register updated. Open: the tracked demo PNGs under `docs/images/`, their `.gitignore` exceptions and the `featured` set in the catalog have lost their purpose and await removal; whether the delivered TEI should carry absolute facsimile URLs in its `<graphic>` elements is a question for the ZBZ.

Documents: [pipeline.md](pipeline.md) GitHub Pages and the facsimile repository, [journal.md](journal.md) session 100

## Plan

This block orders the work still outstanding into phases and milestones, each carrying the
condition under which it counts as finished. It is the forward-looking pendant to
[journal.md](journal.md), which records how the project reached its current state, and it is
rewritten as milestones close. Completed work leaves the active phases and stays visible in the
status tracker. What has been decided lives in the register above. What is required, and against
which gates it is measured, lives in [specification.md](specification.md); the plan anchors its
exit conditions there instead of restating them.

### Target state

The plan runs toward a handover state with five properties.

- The delivered TEI carries the entity layer, released by the operator on a measured gold
  benchmark, and every mark carries its provenance and its verification state.
- The editing history of an object is machine-readable and travels inside the TEI, so an object can
  be read without the repository beside it.
- The curation loop closes inside the viewer without manual pipeline steps, and an object leaves
  the repository as one bundle.
- The measurement layer answers the quality questions ZBZ can ask, including variation
  across OCR engines.
- The production fork reproduces its environment from a lock file and runs the same gates as the
  development repository.

### Phases and milestones

| Phase | Milestones | Quality gate |
|---|---|---|
| A, entity layer to delivery | schema hardening, lexicon shape audit, gold benchmark (M4), population redraw, admission dossier, judge calibration (M5), corpus dry run (M6), stock run (M7) | schema gate, entity gates, closed-world invariant ([verification.md](verification.md), quality assurance section) |
| B, provenance and self-contained TEI | provenance log per object, `_complete.xml` remainder, provenance drawer | schema gate, mirror regeneration |
| C, viewer and export | ZIP export, round-trip wrapper, deferred frontend findings | page load checks, validator |
| D, measurement follow-ups | inter-engine CER, remaining tail documents, ratio heuristic residue | CER statistics regenerated under the recorded seed |
| E, deferred tooling and infrastructure | dependency lock, configuration file, production fork and container, serialization defect, BCa aggregation | CI gates |

#### Phase A, entity layer to delivery

The goal is the entity layer inside the delivered TEI, released by the operator on measured
numbers. Nothing before the stock run touches `output/tei_final/`. The markup rules of the layer
live in [tei-mapping.md](tei-mapping.md), the measurement method and its findings in
[verification.md](verification.md).

##### Schema hardening

Begins immediately, since the schema is the format authority of the delivery (E102) and every
measurement whose numbers should survive belongs after it. `persName@ref` and `orgName@ref` already
carry the `GND:` pattern inline. `bibl` pulls `tei_att.canonical.attributes` and inherits an
unconstrained `@ref` through it, while its GND pattern sits on `@corresp`; `rs` inherits the same
unconstrained `@ref` through `tei_att.naming.attributes`. Tightening means narrowing the inherited
`@ref` on `bibl` the way `persName` and `orgName` do, or dropping `att.canonical` from `bibl`, and
handling `rs` the same way through `att.naming`. `placeName` stays untouched, since Z3 forbids it
and the corpus has no usage. The change takes its own commit and register entry.

Done when all delivered TEI and the valid reference TEIs still validate against
`data/schema/zbz_hersch.rng` and the schema gate named in [verification.md](verification.md), quality assurance section, is green.

##### Lexicon shape audit

Begins once the schema is settled. A new instrument, `scripts/entity/entity_lexicon_audit.py`,
groups every form the built lexicon would match by shape class, among them dotted initials, single
tokens at the length floor, all-caps forms, forms carrying digits, and non-Latin scripts, each with
counts and examples. The operator then approves or bans a whole class instead of chasing single
forms. The audit reruns after every refresh of the GND variant cache.

Done when the operator has ruled on every shape class and the rulings are recorded in
`data/entities/marking_policy.json`, which the matcher loads and validates.

##### Gold benchmark under frozen rules (M4)

Begins once schema hardening and the lexicon audit are closed and the matcher rules are frozen. One
run of `entity_gold_benchmark` measures precision and recall against the held-out part of the 25
reference TEIs. The held-out set is drawn along the distribution of gold mentions. The densest
reference, document 1520, is measured on its own, because it carries a large share of the gold, a
known file defect and the anchor-collision case the pilot panel never saw. The script today writes
`output/audits/entity_gold_benchmark.json` only, so the milestone also adds the versioned evidence
path under `docs/data/`.

Done when a frozen-rules precision and recall measurement is versioned under `docs/data/` and
[verification.md](verification.md) carries the figures together with their sample basis.

##### Population redraw and recall remeasurement

The adjudicated sample belongs to a mark population that the marking policy of E119 has since
widened, and the released marks appear in no earlier draw. The recall side has stood unmeasured
since several of its named rule gaps were closed. A fresh stratified draw over the current
population, the E119 stratum included, and a recall remeasurement on newly read pages come before
any further rule work. Rules built on a population whose rate is unknown widen the gap between
what is measured and what is delivered. A second draw already lies frozen and unadjudicated
under `output/audits/eval_sample_2026-08-13/`; whether it is adjudicated as it stands or re-cut is
the re-freeze decision.

Done when the fresh draw is adjudicated, the judgments are folded into
`data/entities/mention_verdicts.json`, the verdict guard runs clean, and
[verification.md](verification.md) reports precision and recall for the current population.

##### Admission dossier for unlisted entities

Entities the corpus names frequently while the curated list omits them are admitted by the project
itself and marked in the data as an addition from outside that list (operator decision of
2026-08-13). The proposal channel `entity_unlisted_scan` supplies the candidates. The dossier
collects, per candidate, the textual evidence and a deterministic lobid lookup; a language model
never assigns an identifier. The provenance vocabulary carries the distinction through a third
responsibility declaration with `cert="low"`, and a reference is written only once an
identification is confirmed.

Done when every admitted entity has a dossier entry with its evidence and its lookup result, and
the marks it produces validate under the vocabulary described in [tei-mapping.md](tei-mapping.md).

##### Judge calibration (M5)

Begins once the gold benchmark and the redraw have fixed the current rates. A model judge is
measured against ambiguities the reference TEIs already resolve, repeat-run stability included, so
its role in tiers two and three is bounded by a measured accuracy. The judge picks among presented
candidates; identifiers come from the curated list.

Done when accuracy and repeat-run stability on gold-resolved ambiguities are measured and recorded
in [verification.md](verification.md).

##### Corpus dry run (M6)

Begins once the four entity operator questions and the open modelling points are decided. A new
instrument, `scripts/entity/entity_audit.py`, measures the stock before and after, and the full
change preview plus the distribution report go to the operator. A second, independent layer runs
before the dry run, an adversarial agent review of the built lexicon searching for forms that would
strike in ordinary prose; agent findings are proposals, and class decisions stay with the
deterministic shape rules. The review follows the wave pattern of [methodology.md](methodology.md), governance section.

Done when the operator has reviewed the full change preview and the distribution report and
released the stock run.

##### Stock run into the delivered TEI (M7)

`scripts/entity/tei_entity_marker.py` does not exist yet, and `tei_entity_preview.py` refuses to
write into `output/tei_final/`. The marker is built on `marker_common` with dry-run, backup,
byte-splice inside `text`, idempotence and a `revisionDesc` entry. One design condition binds the
milestone. The marker reuses the wrapping and checking logic of the preview instead of growing a
second copy of it. `apply_candidates`, `mark_attributes`, `hi_envelope`, the text-invariance check
and the schema check move out of `tei_entity_preview.py` into a shared module both consume, so
preview and stock run provably produce the same wrapping. Whether the `@resp`, `@cert` and
`@source` attributes travel into the delivered TEI is decided before the run.

Done when the released run has written the marks into `output/tei_final/` and the technical gates
of [verification.md](verification.md), quality assurance section, are green, meaning byte-identical
text extraction, deterministic CER reproduction, the schema gate, the conformity rules, the
idempotence proof and the closed-world invariant over every identifier in the shipped mirror. The
milestone also requires that the mirror is regenerated, the register carries the entry, and
`docs/methode.html` has gained its entity-quality paragraph pointing to
[verification.md](verification.md).

#### Phase B, provenance and self-contained TEI

The goal is an editing history per object that is machine-readable and travels inside the TEI. The
built state of the provenance layer is described in [workflow.md](workflow.md), provenance section.

##### Machine-readable provenance log per object

Today the provenance of an object is split between the `<revisionDesc>` of its final TEI and its
`{doc}_manifest.json`. A `{doc}_provenance.json` beside the final TEI becomes the single editing
log per object and carries these fields:

- `doc_id`
- `current_state` with layout source, OCR source, TEI version and workflow status per stream
- `history`, a list whose items carry a timestamp, an actor (engine and version, or a human role),
  a kind (OCR, layout QA, layout edit, text edit, workflow status), a scope (page or whole
  document), an optional detail string, and a `ref` to the concrete file under `output/`

Actor entries name engines and roles. The log answers four questions in one place that the current
split answers nowhere. It gives the edit history per object, an audit trail per agent decision, a
roll-back to an earlier state without git history, and the direct link between a layout region and
a body element, which today is implicit in the reading order.

Done when every delivered object carries a `provenance.json` whose history reproduces the
`<change>` entries of its `<revisionDesc>` and whose `ref` values resolve to existing files.

##### The self-contained `_complete.xml`

The facsimile side of this plan is realized in the delivered TEI. Step 1 computes pixel zones per
region, the assembly writes `<facsimile>` with one `<surface>` per page and a `<graphic url>` as
its first child, and body elements carry `@facs`; the page break carries `<pb facs="#facs_N">`
(E89, described in [tei-mapping.md](tei-mapping.md)). What remains is the extended `<revisionDesc>`
assembled one to one from the provenance log, and the export arrangement in which `_complete.xml`
becomes the default export variant while `_final.xml` stays the compact reading variant. The
milestone stays a pipeline package separate from the viewer work.

Done when the generator writes `_complete.xml` with the provenance items as `<change>` elements,
the file validates against `zbz_hersch.rng`, and the export module offers both variants.

##### Provenance drawer in the viewer

Begins once the provenance log exists. The viewer reads an object's log and shows it as a drawer
beside the status pills, so a curator sees which engine or which human step produced the state in
front of them. Values come from the token catalogue described in [workflow.md](workflow.md), design section.

Done when the drawer renders the full history of an object from `provenance.json` and the page
loads without a console error.

#### Phase C, viewer and export

The goal is a curation loop that needs no manual pipeline step and an object that leaves the
repository as one file.

##### ZIP export per object (E61)

All pipeline artifacts of an object become one download via JSZip, optionally collected from the
corpus overview for several objects at once. This closes frontend finding N1, which records that
only per-stream single export exists. JSZip is named as a runtime dependency in `CLAUDE.md` and is
absent from the code; the vendoring convention established with E122 applies to it.

Done when a document downloads as one archive carrying its final TEI, its per-page layout JSON, its
OCR text and its manifest, and the catalog offers the multi-select path.

##### Round-trip wrapper for the curated edit

Steps three to six of the round trip described in [workflow.md](workflow.md), round-trip section,
run manually today. They are the reassembly, the status projection into the `revisionDesc`, the
validation and the mirror regeneration. A wrapper command, `scripts/apply_curated.py --doc {ID}`,
runs them in order and stops at the first failing gate.

Done when one command takes a curated edit from the viewer save through to a regenerated mirror and
the validator reports no error for that document.

##### Deferred frontend findings

Deferred until after acceptance by ZBZ. N3 records that OpenSeadragon loads an untiled full
PNG and re-instantiates on every page switch, to be fixed through tiling or neighbour preload. N6
records that the mobile catalog below 1000px hides date, language, type, form and pages entirely;
the recorded remedy keeps date and type visible. N7 records that the contrast of
`--h-text-muted` sits below WCAG AA for small text, so the token is restricted to auxiliary text.
Two further items belong here. One is the page strip with per-page status markers as QA
navigation, a follow-up idea from the go-to-page fix; the other is the missing `aria-current` in
the viewer. One feature of the edition uplift is still outstanding as well, the integration of the
layout editor into the OpenSeadragon facsimile view, so a region is corrected on the image instead
of beside it. Four quick wins of the 2026-08-12 UI analysis stay open and are decided together
with them (the analysis itself was
deleted with E124, git holds it at ec42a613; the other quick wins of that analysis went in with
E107). Q1, layout overlays switchable in the reading view through a control in the facsimile
header that toggles a class hiding the region boxes, off by default, while the layout edit mode
always shows them. Q3, the export tooltip corrected to what the menu offers, since it names a
repo-folder connection the menu does not contain. Q5, the triple marking of the export menu
reduced to one, the menu label and the four arrows dropped and the button kept. Q10, `--h-filter`
switched to `var(--h-text-muted)` and the dead CSS around it removed.

Done when each finding is implemented or recorded in the register as declined, and the page checks
named in [verification.md](verification.md), quality assurance section, pass.

#### Phase D, measurement follow-ups

The goal is closing the questions the measurement layer left open. Two catalog corrections the
register had recorded without acting on them, the page break collapsing to one space and the
running-head text entering the extraction, were carried into
[methodology.md](methodology.md), CER measurement section, in the wave-4 documentation pass; the code and its pinning
tests were already the authority.

##### Inter-engine CER cross-validation

Item (b) of the stability question, a second OCR run with a different engine as cross-validation of
the headline CER. Item (a), run-to-run stability of the pipeline, was measured with E100, and its
result sits in the `stability` block of `docs/data/cer_statistics.json`. The measurement method,
the reference choice and the extraction rules are fixed in
[methodology.md](methodology.md), CER measurement section. The run consumes API calls and is therefore
operator-gated.

Done when a second engine has read the reference documents, the paired difference against the
delivered layer is reported with its interval, and the statistics JSON carries the result under the
recorded seed.

##### Remaining tail documents

The CER tail is structural. It is not a failure of character recognition. The documents whose tail
traces to a doubled-page reading order, 760 and 1440, stay facsimile-verified curation cases.
Machine reordering of the corpus was refuted empirically (E99) and is banned on every path, so
W19 is read as a suspect signal for text or zones. Targeted per-page re-reading is the pattern E96
and E98 established, and it stays operator-gated per page.

Done when both documents are curated page by page against the facsimile, or the operator records
that they stay as they are.

##### Ratio heuristic residue

`scripts/eval/evaluate_ocr.py` still derives a scope mismatch from the ratio of reference to
pipeline page-break counts. The published statistics no longer use it, since
`cer_statistics_runner.py` returns a neutral scope. Either the residue goes, or its diagnostic role
is documented where the metric is defined.

Done when the heuristic has one documented purpose or no call site.

#### Phase E, deferred tooling and infrastructure

The goal is the production side of the repository. Each item names the condition that opens it.

##### Dependency lock

`pyproject.toml` is the only manifest since the wave-3 tooling package; the accompanying `uv.lock`
is missing because uv is not installed on the working machine. CI materializes the dependency list
from `[project] dependencies` plus the `dev` extra and installs it with pip, so both gates run
without the lock.

Done when `uv lock` has produced a committed lock file and CI installs from it.

##### Configuration file

Engines are configured in `scripts/config.py` and `scripts/ocr/ocr_pipeline.py`. A YAML
configuration would move engine name, model and environment-variable names out of the code. An
earlier draft named Mistral as the default engine, which the code resolves to Gemini; the draft
was removed with the 2026-08 refactoring (git holds it at f5261ae5) and a new one starts from the
current engine picture.

Done when engine selection reads from one configuration file and every pipeline command behaves
unchanged.

##### Production fork, container image and its CI

The production repository at the University of Zurich is a fork of the development repository, and
three pieces belong to it. An OCI image built from a Containerfile, configured through environment
variables and carrying no secrets (an earlier draft was removed with the 2026-08 refactoring; git
holds it at f5261ae5). A `.gitlab-ci.yml` that runs the same two gates as the GitHub
Actions workflow and additionally builds the image and pushes it to the GitLab registry. A defined
merge strategy for upstream changes from the development repository into the fork, which is the
mitigation of the fork-divergence risk recorded in [project.md](project.md), integration section.

Done when the fork builds its image in its own CI, both gates run there, and the merge strategy is
written down in [project.md](project.md), integration section.

##### Foreign-namespace serialization defect

`serialize_tei_fragment` drops the namespace declaration of a foreign-namespace element and returns
an unparsable fragment. No corpus impact is known, which is why it was recorded without being acted
on. The fix carries a test pinning a foreign-namespace child.

Done when the function round-trips a foreign-namespace element and the pinning test is green.

##### BCa aggregation kept as library code

`cer_statistics.py` carries a BCa implementation with its own tests and calls it in its own
aggregation functions, which the generator of the published statistics never uses; the published
intervals are percentile intervals throughout, and every aggregate names its own `ci_method`. The
label question was settled by moving the label (E122), and the implementation stays as library
code (E123). The item reopens only if a published aggregate needs bias correction.

Done when either the published generator calls it and the statistics are regenerated under the
recorded seed, or the code is removed with a register entry.

### Status tracker

Snapshot of 2026-08-21. States used here are done, built (the instrument exists, the run is
outstanding), open, and blocked-by with the named party.

| Milestone | State | Evidence |
|---|---|---|
| Pilot, layout scaling, PAGE-XML and METS | done | [project.md](project.md), scope of functions |
| TEI generation schema-valid | done | E102, `tests/test_tei_schema.py` |
| CER evaluation | done | `docs/data/cer_statistics.json`, [methodology.md](methodology.md), CER measurement section |
| Corpus handover to ZBZ | done | E66/E67, every stream `unverifiziert` as handover default |
| Entity layer to preview (M0 to M3) | done | E105 to E119, [verification.md](verification.md) |
| CER catalog corrections | done | [methodology.md](methodology.md), CER measurement section, extraction rules |
| Schema hardening | open | `data/schema/zbz_hersch.rng`, `bibl` via `att.canonical`, `rs` via `att.naming` |
| Lexicon shape audit | open | `entity_lexicon_audit.py` does not exist |
| Gold benchmark (M4) | built | `entity_gold_benchmark` writes `output/audits/entity_gold_benchmark.json`; no evidence under `docs/data/` |
| Population redraw and recall remeasurement | blocked-by operator (re-freeze decision) | `output/audits/eval_sample_2026-08-13/` frozen and unadjudicated |
| Admission dossier for unlisted entities | open | `entity_unlisted_scan` supplies the candidates |
| Judge calibration (M5) | open | no calibration run recorded |
| Corpus dry run (M6) | open | `entity_audit.py` does not exist |
| Stock run (M7) | open | `tei_entity_marker.py` does not exist; `tei_entity_preview.py` refuses `output/tei_final/` |
| Provenance log per object | open | [workflow.md](workflow.md), provenance section |
| `_complete.xml` remainder | open | facsimile side realized (E89, [tei-mapping.md](tei-mapping.md)) |
| Provenance drawer | blocked-by the provenance log | [workflow.md](workflow.md), viewer section |
| ZIP export (E61) | open | JSZip named in `CLAUDE.md`, absent from the code |
| Round-trip wrapper | open | [workflow.md](workflow.md), round-trip section |
| Deferred frontend findings N3, N6, N7, page strip, `aria-current`, quick wins Q1/Q3/Q5/Q10 | open | UI analysis of 2026-08-12 (deleted with E124, git ec42a613), E123 residue |
| Layout editor inside the OpenSeadragon view | open | E58 facsimile view, E60 edit toggle |
| Inter-engine CER | open | stability item (b); item (a) measured with E100 |
| Tail documents 760 and 1440 | open | E91 classification, E99 refutation |
| Ratio heuristic residue | open | `scripts/eval/evaluate_ocr.py` |
| Dependency lock | blocked-by toolchain (uv not installed) | E123 |
| Configuration file | open | `scripts/config.py`, `scripts/ocr/ocr_pipeline.py` (current engine configuration) |
| Container image, GitLab CI, merge strategy | blocked-by the production fork | [project.md](project.md), integration section |
| Foreign-namespace serialization defect | open | `serialize_tei_fragment` |
| BCa aggregation as library code | open, decision pending | E122 (label), E123 (code kept) |

### Open decisions and dependencies

Four open questions are recorded here. Three of them have ZBZ as decider, and O27 among those
shapes the entity layer.

- O8, header metadata from Alma including the MMSID. Decider is ZBZ together with DHCraft.
  While it is open, most delivered headers carry an empty container title by intention.
- O13, editorial subject headings in the header. Decider is ZBZ. Headers stay without them.
- O27, the caption contradiction in the editorial guidelines. Decider is ZBZ. It falls
  before the matcher widens its figure zone, so before the corpus dry run.
- O18, the multimodal correction experiment with scan image and OCR text together. Decider is
  DHCraft; it blocks no milestone.

Four operator questions of the entity layer fall before the corpus dry run, since each changes what
the dry run would show.

- Works in tier one, or worklist-only in the first stock wave. The proposal is persons and
  organisations first, strengthened by the pilot evaluation, where every confirmed span error sat
  in the work class.
- The curation channel for tiers two and three. The proposal is the viewer entity stream, read-only
  first, with confirm and reject actions writing verdict files later.
- The role of `editor_reviewed`. The proposal is a report field without gate function.
- Hyphen compounds, meaning compound event and lecture titles built on a listed surname. The
  references leave them unmarked and the tool decides them inconsistently, so the suspicion signal
  parks them on the worklist until the decision falls.

Three modelling points stay open and fall before the stock run.

- Image captions, tied to O27. The operator convention of 2026-08-12 puts captions in scope, while
  the matcher scans figure zones, demotes their candidates to tier 2 (E115) and reports caption
  candidates separately.
- Empty `speaker` elements stay curation slots (W17); the matcher never invents text.
- Adjective forms of names. The guideline excludes them while the references mark at least one.
  The automatic tiers exclude them and candidates go to the worklist.

Two further decisions belong to single milestones. Whether the `@resp`, `@cert` and `@source`
attributes travel from the preview layer into the delivered TEI falls before the stock run and is a
decision for ZBZ. The re-freeze of the reconstructed evaluation draw falls before the
population redraw and is the operator's.

Feedback from ZBZ is unavailable in this project phase, so open convention questions of the
entity layer fall to the operator; that rule and the verification of agent self-reports are
recorded in [methodology.md](methodology.md), governance section.

Four orderings across the phases are binding. Schema hardening and the lexicon audit precede the
gold benchmark. The fresh draw precedes any further rule work. The corpus dry run precedes the
stock run. The provenance log precedes both the extended `<revisionDesc>` and the viewer drawer.
The round-trip wrapper presupposes none of them and may be pulled forward.

### Deviations

The gates hold independently of the sequence, and a milestone closes on its done-when criterion
alone. Re-prioritisation is allowed when a blocked milestone would otherwise idle the work, and the
deviation is recorded with its reason in [journal.md](journal.md). Decisions taken along the way enter
the register above as new entries.

Six deviations from earlier plans are in force and are recorded here so that they are not planned
again.

- Machine reordering of the reading order was planned as a corpus delivery and refuted empirically
  (E99). The corpus reorder is banned on every path, W19 is read as a suspect signal for text or
  zones, and the affected pages resolve through facsimile-verified per-page curation.
- LLM-driven entity recognition and linking left the scope (E71). The deterministic closed-world
  layer of this plan is a separate requirement and is unaffected by that removal.
- Automatic `front`, `back`, `anchor` and `unclear` markup was left to curation (E83). The scope
  sentence stays in [specification.md](specification.md), the markup rule in
  [tei-mapping.md](tei-mapping.md).
- Layout ground truth from Transkribus PAGE-XML was assessed as feasible after normalization and
  then dropped as unrequested. The Transkribus direction stays outbound only
  ([project.md](project.md), integration section).
- The double-page detection question was closed after the Masterfile check. The Masterfile carries
  no double-page column, no aspect ratio is computed anywhere, and the judgement stays with the
  layout model's prompt. The residue is the page-break ratio heuristic in `evaluate_ocr.py`, which
  Phase D resolves.
- The knowledge base was recut by function in the refactoring waves recorded from E120 onward. The
  plan carries the outstanding work of that recut and none of its history.

## References

- [journal.md](journal.md): the chronological course of the work
- [index.md](index.md): navigation across the knowledge base
- [specification.md](specification.md): the requirements and the gates the plan anchors to
- [verification.md](verification.md): the verification chain behind the measured claims
- [project.md](project.md), integration section: the delivery contracts with ZBZ, Transkribus and teiCrafter
