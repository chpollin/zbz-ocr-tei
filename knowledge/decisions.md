---
title: Decisions
type: knowledge
project:
  name: zbz-ocr-tei
  repository: https://github.com/chpollin/zbz-ocr-tei.git
method:
  name: Promptotyping
  url: https://dhcraft.org/Promptotyping/
status: complete
created: 2026-02-18
updated: 2026-07-07
tags: [zbz-ocr-tei, decisions, open, decided]
---

# Decisions

Consolidated register of all decisions and open questions. Cross-cutting, collected from all documents. Entries are dated records; later corrections are inline update annotations, never silent rewrites.

---

## Decided (E1-E63)

| # | Decision | Rationale | Date | Document |
|---|---|---|---|---|
| E1 | Hybrid pipeline: Docling (layout) plus LLM OCR (text) | layout analysis without OCR, OCR separate | 2026-01-29 | [pipeline.md](pipeline.md) |
| E2 | Docling for layout only, not for OCR | RapidOCR has encoding problems (`e -> O`) on French | 2026-01-29 | [pipeline.md](pipeline.md) |
| E3 | Deterministic first, LLM only for complex cases | reproducible, cost-efficient, debuggable | 2026-01-29 | [pipeline.md](pipeline.md) |
| E4 | Four document types (A-D) classified | different pipeline strategies | 2026-01-29 | [project.md](project.md) |
| E6 | Mistral OCR 3 as production engine | ZBZ has Azure access, no GPU needed | 2026-02-14 | [pipeline.md](pipeline.md) |
| E7 | Fee unchanged | Azure integration without extra cost | 2026-02-14 | [project.md](project.md) |
| E8 | Configurable API endpoints | switch between local and Azure | 2026-02-14 | [infrastructure.md](infrastructure.md) |
| E9 | Containerisation with Podman | ZBZ does not use Docker; Podman is OCI-compatible | 2026-02-14 | [infrastructure.md](infrastructure.md) |
| E10 | Fork on GitLab University of Zurich | ZBZ runs its own instance | 2026-02-14 | [infrastructure.md](infrastructure.md) |
| E13 | Export as PAGE-XML plus METS for coOCR | coOCR expects PAGE-XML 2013-07-15 plus PNG | 2026-02-20 | [pipeline.md](pipeline.md) |
| E14 | Preserve Markdown formatting | coOCR stores text as-is in `<Unicode>` | 2026-02-20 | [pipeline.md](pipeline.md) |
| E15 | Dashboard redesign: multi-page UI with shared CSS/JS | unified design system, static JSON data | 2026-02-25 | [pipeline.md](pipeline.md) |
| E16 | Page-by-page comparison for monographs (>10 TEI pages) | global alignment fails from ~50 pages | 2026-02-25 | [pipeline.md](pipeline.md) |
| E17 | LLM correction optional, not default | degrades documents with CER below 5 % | 2026-02-25 | [pipeline.md](pipeline.md) |
| E18 | Content-based page matching instead of fixed offset | TEI facs numbers differ from PDF pages | 2026-02-25 | [pipeline.md](pipeline.md) |
| E19 | Layout: Docling plus Gemini hybrid | Docling mAP 0.699, 17 classes, free; Gemini as validator | 2026-02-25 | [pipeline.md](pipeline.md) |
| E20 | Docling 2.75 confirmed as layout engine | type sample passed, 0.4-3.3 s/page | 2026-02-25 | [pipeline.md](pipeline.md) |
| E21 | Scope expansion: full pipeline in zbz-ocr-tei | meeting 2026-02-25: OCR plus layout plus PAGE-XML plus NER plus TEI | 2026-02-25 | [pipeline.md](pipeline.md) |
| E22 | TEI generator directly from layout plus OCR (no PAGE-XML) | extended later for NER/PAGE-XML | 2026-02-25 | [pipeline.md](pipeline.md) |
| E23 | Data delivery Feb 2026: 286 PDFs, 25 TEI-XML, 24 PAGE-XML exports | PAGE-XML schema 2013-07-15, empty | 2026-02-27 | [project.md](project.md) |
| E24 | docling-serve API for layout (no local GPU) | Docker container, identical output format | 2026-03-03 | [pipeline.md](pipeline.md) |
| E25 | Gemini 3.1 Flash Lite as layout QA validator | overlay PNG plus layout JSON to corrected JSON, structured output | 2026-03-03 | [pipeline.md](pipeline.md) |
| E26 | Gemini layout detect mode | Docling fails on ~15 % (landscape, multi-column); three modes qa/detect/auto | 2026-03-04 | [pipeline.md](pipeline.md) |
| E27 | Gemini document classification (stage 1a) | 271/286 without metadata, heuristics fail (7/15 wrong) | 2026-03-05 | [pipeline.md](pipeline.md) |
| E28 | Online demo: 4 demo documents on GitHub Pages | full data local only (gitignored) | 2026-03-05 | [pipeline.md](pipeline.md) |
| E29 | Gemini OCR correction stage 2b | two-step (analysis plus correction), variants A/B | 2026-03-05 | [pipeline.md](pipeline.md) |
| E30 | Gemini vision TEI generator plus type-specific prompts | four-level prompts (layout type, pub form, genre, language), 12 genre prompts | 2026-03-06 | [pipeline.md](pipeline.md) |
| E31 | Layout QA full run plus overlay generator | `--mode auto --force` over 286 documents, 14,708 corrections | 2026-03-06 | [pipeline.md](pipeline.md) |
| E32 | Unified TEI pipeline (scaffold plus Gemini plus assembly) | four stages, 50/50 VALID in the pilot | 2026-03-07 | [pipeline.md](pipeline.md) |
| E33 | Digital edition (`docs/`) | public website next to the internal dashboard | 2026-03-06 | superseded by E56 |
| E34 | NER pipeline plus entity index (phase 3) | post-hoc NER via Gemini Flash Lite (6 types), Wikidata as primary id | 2026-03-07 | removed by E71 |
| E35 | NER production-ready (phase 3 scale-up) | seven quality improvements before the production run | 2026-03-08 | removed by E71 |
| E36 | Curation editor (editor in the loop) | FastAPI server, 11 API endpoints, WYSIWYG | 2026-03-08 | superseded by E56 |
| E37 | TEI validation quality gate plus entity tagging fix | two levels (errors blocking, warnings informative), W1-W10, HTML report default | 2026-03-15 | [pipeline.md](pipeline.md) |
| E38 | Entity tagging type-correct with internal ids | `annotate_entities()` uses the entity index for type-correct tags | 2026-03-15 | removed by E71 |
| E39 | Language mapping plus facsimile/pb fix | map multilingual codes (`fra/deu`) correctly; empty `<surface>` for pages without layout zones | 2026-03-15 | [pipeline.md](pipeline.md) |
| E40 | div merge: page divs to document divs | post-assembly fix `_merge_page_divs()`, reference comparison `--compare-ref` | 2026-03-15 | [pipeline.md](pipeline.md) |
| E41 | Agent-based quality screening as pre-curation | structured 7-layer review, review JSON per document | 2026-03-15 | abolished by E66 |
| E42 | `<revisionDesc>` as status in the TEI header | status travels with the document | 2026-03-15 | [pipeline.md](pipeline.md) |
| E43 | `output/tei_final/` as single source of truth | only final TEI are published | 2026-03-15 | [pipeline.md](pipeline.md) |
| E44 | Entity stopword extension needed | screening showed generic nouns as false positives | 2026-03-15 | removed by E71 |
| E45 | Entity stopword extension done | 20 new entries, reassembly of 32 documents, all VALID | 2026-03-15 | removed by E71 |
| E46 | OCR deduplication as deterministic post-processing | `ocr_dedup.py`: token loops, barcode artifacts, year repetitions | 2026-03-15 | removed by E75 |
| E47 | `div type="essay"` is not a valid DTA type | `type="text"` as generic replacement for philosophical essays | 2026-03-15 | [pipeline.md](pipeline.md) |
| E48 | Project-specific schema `zbz_hersch.rng` | generic `tei_all.rng` replaced by a project schema (from ODD, 551 definitions) | 2026-03-26 | [pipeline.md](pipeline.md) |
| E49 | ZBZ editorial guidelines as binding reference | full guidelines as `data/source/guidelines/Editionsrichtlinien_ZBZ.md` | 2026-03-26 | [pipeline.md](pipeline.md) |
| E50 | Dual-attribute strategy for entity references | `ref="GND:..."` (primary) plus `corresp="#zbz-p.N"` (internal) | 2026-03-26 | removed by E71 |
| E51 | End-to-end CER benchmark (TEI versus TEI) | 25 ZBZ reference TEIs as ground truth, `benchmark_cer.py` with stratified analysis | 2026-03-26 | [quality: see specification.md and final-report.md] |
| E54 | Scientific CER re-evaluation | BCa bootstrap (B=10000, seed 42), paired bootstrap E2E versus OCR-only, HCPR, multi-norm, content-aligned eval. Headline then n=19: mean 4.10 % [2.01, 6.75], median 1.83 % [0.84, 5.14] (historical state 2026-04-27; current headline see E85: mean 2.71 % / median 1.40 %, n=25) | 2026-04-27 | [final-report.md](final-report.md) |
| E55 | Interactive CER dashboard | 12 sections, vanilla SVG. Abolished with E56; data remains as `docs/data/cer_statistics.json` | 2026-04-27 | superseded |
| E56 | Frontend reduction to the pipeline viewer | edition site, curation editor (FastAPI), diagnostics, and CER dashboard abolished without replacement. New single-page app `docs/viewer.html` (sidebar, facsimile plus layout overlay plus OCR/TEI panel; layout editor with bbox drag, resize, add, delete, reading-order drag; persistence via file download at that time). Volume 9 to 1 HTML, 23 to 6 JS (minus 81 %), CSS minus 84 %. E33/E36 superseded | 2026-04-27 | [workflow.md](workflow.md) |
| E57 | Per-page mirror plus GitHub Pages deploy | `generate_edition_data.py` mirrors layout JSON, Mistral OCR, and per-page TEI (split from `_final.xml` via `<pb>` at sequential position 1..N because of pagination drift) for all 285 documents to `docs/data/pages/`; three-stage path resolver in `core.js`; `.nojekyll`; image delivery stays local (only demo images versioned) | 2026-05-25 | [workflow.md](workflow.md) |
| E58 | OpenSeadragon 5.0.1 as facsimile renderer (view mode) | pan, zoom, rotate; plain image loading (no deep-zoom tiling); CDN via jsDelivr, no build pipeline. Layout edit mode keeps the static `<img>` editor | 2026-05-25 | [workflow.md](workflow.md) |
| E59 | Polygon support not introduced | Hersch facsimiles are cleanly set print (1926-2000); rectangles cover all region types. Annotorious and similar libraries explicitly unnecessary; data model stays `bbox.x_pct/y_pct/w_pct/h_pct` | 2026-05-25 | [pipeline.md](pipeline.md) |
| E60 | Mode button redesign, option C: edit toggle per panel | global mode bar removed; each panel gets a small edit toggle in its header; `setMode()` split into `setImageEdit()` plus `setTextEdit()` | 2026-05-25 | [workflow.md](workflow.md) |
| E61 | Export module with JSZip 3.10.1 | per-document export drawer plus multi-select bulk export; ZIP built in the browser, no server component; planned, not yet wired in | 2026-05-25 | [workflow.md](workflow.md) |
| E62 | Method page `docs/methode.html` | lean static page with headline CER, stratified values, literature comparison, limitations, tool documentation; deliberately no interactive dashboard. Implicit methodology position: never LLMs for entity-id linking | 2026-05-26 | [specification.md](specification.md) |
| E63 | Blank-page detection plus viewer handling (phase 1) | 79 blank pages corpus-wide; phantom regions from layout QA hallucination countered by the Docling zero signal; viewer fix interim/heuristic; phase 2 in E65 | 2026-05-26 | [workflow.md](workflow.md) |

---

## Decided (E64-E94, detail)

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

Documents: [final-report.md](final-report.md)

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

Documents: [final-report.md](final-report.md)

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

Documents: [final-report.md](final-report.md), [methode.html](../docs/methode.html)

### E81 Transkribus export plus REST upload: PAGE-XML round trip into a collection (2026-06-08)

The stage-4 PAGE-XML (standard PAGE 2013-07-15) is losslessly playable back into Transkribus for manual post-correction or HTR training. Two scripts: `transkribus_export.py` builds the Transkribus folder convention from `page_xml/` plus `docs/images/` (selection `--sample` stratified, `--all`, `--reference`, `--doc`; verifies PNG size equals declared image size so coordinates align). `transkribus_upload.py` uploads bundles via the legacy TrpServer REST API; verified 2026-06-08 against a collection of the new platform (test object doc 1500 appeared with regions, text, and reading order). Auth exclusively via environment variables, never in code or repo. No dedup: every run creates new documents, hence dry run plus test object first. Dialect caveat: line polygons, no baselines (import fine, HTR training would need them).

Documents: [pipeline.md §Transkribus Export](pipeline.md)

### E82 Doc-30 dedup published, corpus mean 3.99 % (was 4.26), tail-cause register (2026-06-08)

In document 30 a duplicated OCR block was removed; fidelity CER 18.25 to 11.59 %, published to the SoT and mirror. Corpus mean fidelity 4.26 to 3.99 % (CI [2.36; 5.96]), median unchanged; statistics JSON regenerated (seed 42). The old figure is retired (user decision: only the current CER counts). Caveat: 3.99 = 24 documents pure pipeline output plus one manually deduplicated, because no automatic block deduplication exists; the `ocr_dedup.py` once referenced in work-report appendix A and CLAUDE.md is not in the repo [update 2026-07-07: clarified; CLAUDE.md has not referenced it since Session 73, the script itself was removed with E75]. Tail causes documented: the high CER values are structural, not character recognition. Open defects registered: (a) the layout QA over-detects footnotes, body-as-note on 290/1910/90, not safely auto-fixable because of real long footnotes in 1520/40/3040; (b) double-page reading order, sorted only by y [update E90 (2026-06-21): (b) fixed generator-side, validator warning W19 scopes the not-yet-regenerated corpus, delivery M3 operator-gated; (a) remains open]. E80 remains valid.

Documents: [final-report.md](final-report.md)

### E83 Code-doc drift fixed; header metadata stays ZBZ domain (E76/O8 confirmed) (2026-06-08)

User assignment: "fix the code-doc drift; build only what is genuinely sensible". (a) Drift fixed (kept): revisionDesc documentation on workflow status instead of the old "APPROVED"; dead reference in the mapping prompt replaced; scope note added (step 2 delivers only a per-page div fragment, so front/back/anchor/unclear cannot be produced automatically); header comment honest about the data source; docstring and validator comments corrected. (b) An MMSID/citation header projection was built as a test and REJECTED again after consultation: catalog numbers and bibliographic citations are library domain (confirms E76/O8; note for future sessions: do not retry without an explicit ZBZ requirement). (c) Confirmed: front/back/anchor/unclear stay curation (data source free text, too rare, or image judgment).

Documents: [pipeline.md](pipeline.md), [decisions.md](decisions.md)

### E84 Conformity audit pipeline versus editorial guidelines plus wave-1/2 generator fixes (implemented, deploy operator-gated) (2026-06-08)

Exhaustive comparison of the delivered TEI structure against the editorial guidelines as a multi-agent workflow (126 agents, 62 rules, adversarially verified). 18 real generator defects proven; one earlier claim corrected (`div type="text"` is NOT a violation). Wave 1 implemented and tested: exclusive div n/type, sequential figure ids, `head type="lemma"` for encyclopedias. Wave 2 partial: first document head as `<title type="main">`, `<foreign xml:lang>` normalised to 639-2/B. All as fault-tolerant post-assembly passes; validator warnings W15-W18 added (non-blocking). The largest defect (62 % empty speakers) deliberately NOT rebuilt: the ground truth encodes speakers via GND persName, GND linking left the pipeline with E71, so the empty `<speaker/>` is a curation slot, not a bug. Adversarial code review (39 agents) confirmed three findings, all addressed. Deploy operator-gated: fixes take effect only after corpus regeneration, which must be coordinated with the curation lanes. Wave-2 remainder classified: no safely deterministic fix remains (collision, curation slot, ZBZ-blocked, or non-defect). reference_tei/1520.xml is broken XML, escalated to ZBZ.

Documents: [pipeline.md](pipeline.md), [specification.md](specification.md)

### E85 Reference-verified footnote demotion (3.99 to 2.71 %) plus sup-marker strip (2026-06-08)

Two reference-backed footnote conformity corrections as idempotent, reversible post-passes on `tei_final`. (a) Demotion: some `<note place="foot">` actually carried body text; if a contiguous stretch of at least 150 characters appears in the ground-truth body (footnotes excluded), the block is provably body text and is demoted to `<p>`. 14 blocks in 5 documents (290/1910/90 plus, on operator instruction, 40/1520). Corpus fidelity mean 3.99 to 2.71 %, median 1.40 %; the pipeline's advantage over raw OCR thereby significant (-9.45 pp, p=0.013). Tool `tei_footnote_demote.py` (backup, hold list, `--include-hold`). (b) Sup-marker strip: leading print markers removed from note text per the guidelines (mark only via `@n`); 16 notes in 4 documents, CER-neutral. Wave-2 remainder classified by a ground-truth-based adversarial workflow; footnote-n was the only safe fix. The note "3 W19 diagnosis specs handed over" was a provisional label, superseded by E90.

Documents: [final-report.md](final-report.md)

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
[cer-gegenprobe-2026-07-03.md](../reports/cer-gegenprobe-2026-07-03.md), and the counter-check
scripts live in the paper repo (DHCraft/promptotyping-paper, `verification/`).

Consequence: the upper-bound passage in [final-report.md](final-report.md) is concretized by the
two cause classes that inflate fidelity without a recognition error (apparatus insertions,
capitalization divergence). Open follow-up: ellipsis normalization (U+2026 versus `...`), a
possible dedicated reporting category for apparatus insertions, and the doc 30/760 stock
correction via M3 (operator-gated, E90).

Documents: [final-report.md](final-report.md), [cer-gegenprobe-2026-07-03.md](../reports/cer-gegenprobe-2026-07-03.md)

### E92 Guideline conformity quantified corpus-wide: five audit instruments plus step-1 generator fixes (2026-07-07)

Occasion: operator question whether the delivered TEI satisfies the ZBZ editorial guidelines beyond schema validity. The session built a ground-truth map of the 25 reference TEIs (consolidated as Appendix B of [final-report.md](final-report.md), including the exception catalog of reference-side defects and the ill-formed 1520.xml) and quantified every suspicion with five new offline audit instruments in `scripts/eval/`, each test-gated, JSON output to `output/audits/`:

- `char_lint_audit.py`: typewriter apostrophe U+0027 between letters, guillemet deviations, space before punctuation (incl. U+00A0), U+00AC residue.
- `pb_number_audit.py`: scan-sequence suspicion on pb@n, digit-only paragraphs in the body, cross-check against layout footer regions.
- `hi_preservation_audit.py`: survival of the OCR emphasis signal into the delivered TEI (per page, via `pb_split.iter_page_spans`).
- `relation_integrity_audit.py`: `@next`/`@prev` pairs, anchor pairs, title-main cardinality, `sp`/`speaker` context.
- `body_note_audit.py`: body-text-as-footnote candidates via a marker/length/position score; its candidate set feeds the facsimile verification consumed by E94.

Measured state (snapshot 2026-07-07): character normalization is the largest gap (241 documents with letter-internal U+0027 at 88,978 occurrences; 228 with guillemet deviations at 16,013; 215 with space-before-punctuation at 9,928); print pagination is broadly missing (245 documents with scan-sequence pb@n, 226 with a layout-footer/pb mismatch, 191 with digit-only paragraphs); hi survival is nearly clean pipeline-side (18 pages in 12 documents); relations are nearly clean (one `@next`/`@prev` case in doc 1350; `sp`/`speaker` outside interview context concentrated in doc 1240).

Generator fixes (step 1, test-first): `detect_page_number` reads the printed page number from layout `_filter`/`_skip` footer regions into pb@n (fallback stays the scan number), and `drop_filter_echoes` stops filtered-region text (footer page numbers, cover boilerplate) from leaking into the body through positional paragraph matching. Verified on the doc 570 scaffold regeneration. Both act on regeneration; correcting the delivered corpus runs over the operator-gated marker path (deterministic post-steps on `tei_final` with backup and before/after audit measurement).

Documents: [final-report.md](final-report.md) (Appendix B), [journal.md](journal.md) session 83

### E93 Image-based italics re-detection rejected; `<hi>` stays OCR-signal-bound (2026-07-07)

Occasion: the reference TEIs mark italics roughly an order of magnitude more often than the delivered corpus, and the loss chain was traced end to end. Mistral OCR emits `*emphasis*` markers on only a minority of pages; the step-1 scaffold preserves the emitted markers nearly completely (`md_to_tei_inline`); step 3 strips nothing; the Gemini refinement image channel is instructed to verify existing emphasis, and only where semantically relevant. The dominant loss therefore sits in the OCR engine, before the pipeline.

The apparent fixes, sharpening the Gemini prompt from verify to detect or adding an image-based re-detection pass, are rejected (operator ratified 2026-07-07): the OCR signal is the only machine-readable evidence for italics the pipeline has, an instructed LLM detection is non-deterministic run to run, and the footnote overdetection precedent (E82, repaired by E85) shows what instructed detection does to corpus-wide stock. No Gemini prompt change ships.

Consequence: `<hi>` in pipeline output remains bound to the OCR emphasis signal, guarded by `hi_preservation_audit` (E92). Complete rendering markup per guideline vocabulary (`#i` etc.) is downstream curation at the facsimile, in the viewer or in teiCrafter.

Documents: [final-report.md](final-report.md), [specification.md](specification.md)

### E94 Stock-correction wave ratified: printed-folio pb@n, hybrid correction mode, targeted verification depth (2026-07-07)

Operator ratifications after the calibration round, answered as three conceptual questions: (1) `pb@n` carries the printed page number in square brackets, matching the corpus-wide bracket convention of the ZBZ references; pages without a reliable signal keep the unbracketed scan number. (2) Correction mode hybrid: safe classes are corrected machine-side as reversible marker runs with backup; unsafe classes (space type, dehyphenation residue) stay curation worklists. (3) Verification depth: targeted adjudication of known conflicts plus supplementary samples of under-covered strata, instead of a full stratified sample.

Executed: `tei_char_normalize.py` normalized the letter-internal typewriter apostrophe corpus-wide (88,978 occurrences in 241 documents to U+2019; after-audit 0; backup `output/_backup_pre_char_normalize/`; schema, header, and validator gates green). The tool imports the audit regex, so measurement and correction share one definition.

Built and dry-run verified, corpus write pending (the session's permission mode blocked the write; the operator executes or re-authorizes): `tei_pb_folio.py` (folio from footer detection 1753 pages, interpolation 1033, stable offset 151, bracketing of already printed folio 208, fallback 970; `--strip-folio-echo` removes 1212 stray page-number paragraphs) and `tei_body_note_demote.py` (verdict-driven: 59 demotions to `<p>`, 2 epigraphs to `<quote>`, 2 genuine footnotes untouched, 19 conservative footnote promotions reversing the verified role swap of body and footnote). The verdicts come from the facsimile verification of all 63 `body_note_audit` candidates and are persisted in `output/audits/body_note_verdicts.json`.

Findings feeding later decisions: the sampled doc-30 double pages show no character loss, conflicting with the E91 loss classification (adjudication pending); Mistral OCR degenerated into a repetition loop on doc 1520 page 70 and the correction layer's refusal text leaked into the delivered TEI (single-page re-OCR gated); `<foreign>` markup exists in only 30 of 285 documents while at least 27 foreign-less documents carry unmarked Latin/Greek phrases, with an inconsistent de/deu language code; a naive OCR-versus-TEI volume audit was tested and rejected because about 90 percent of its hits are the intentional e-periodica boilerplate filtering (a filtered triage variant plus a refusal-string check and a duplicate-facs check remain recommended).

Documents: [journal.md](journal.md) session 83, [specification.md](specification.md)

### E95 Echo-strip repaired sp-aware after the executed stock runs; rerun made semantically idempotent (2026-07-07)

Occasion: the operator executed both pending E94 stock runs (`tei_pb_folio --strip-folio-echo`, then `tei_body_note_demote --promote-footnotes`); both reproduced the dry-run-verified figures exactly. The post-run gates then caught four schema-invalid interview documents (2330, 2400, 2540, 3180), all previously valid.

Root cause: in interview documents the footer echo sits inside `<sp>` with an empty `<speaker/>`; the echo strip removed the `<p>` but left the wrapper, and the schema requires at least one `<p>` per `<sp>` (14 orphaned wrappers corpus-wide). The dry run could not see this because it counts removals without validating.

Repair (test-first): the strip is sp-aware. An echo that is the sole content of an `<sp>` with empty speaker removes the whole block; an `<sp>` with a named speaker stays untouched, echo included (content over cosmetics); already orphaned empty wrappers are healed on any strip run, so re-running the tool repairs the corpus. Healing verified end-to-end on copies of all four documents (schema-valid afterwards, second run a no-op).

Second defect found by the new post-state tests: a rerun reclassified mostly-bracketed documents as printed_folio and would have bracketed the remaining unbracketed scan fallbacks into false print folios (e.g. doc 110 scan page 1 to `[1]`). Guard: once a document carries bracketed pb@n, unbracketed values are by the R-PBN convention scan fallbacks of a prior run and are never reinterpreted (`doc_has_brackets` in `resolve_page_folio`).

The integration tests in `tests/test_pb_folio.py` now assert the delivered post-run state plus rerun idempotence instead of the pre-run proposals. Corpus healing runs over the operator-gated marker path (a repeated `tei_pb_folio --strip-folio-echo`).

Documents: [journal.md](journal.md) session 85

---

## Open items

| # | Question | Context | Blocks | Clarification |
|---|---|---|---|---|
| O8 | Metadata from Alma/MMSID | ID plus MMSID plus PubForm in the `teiHeader` (per the ZBZ editorial guidelines) | phase 3 TEI | Open, with ZBZ (state 2026-06-08, E76/E83 confirmed): header metadata from Alma including the MMSID is ZBZ domain and does not belong in the OCR/layout/TEI pipeline. A projection was introduced with E69, removed with E76, rejected again with E83. Spec conflict: the guidelines demand these fields; to be clarified with ZBZ (who pulls from Alma, which fields). Decider: ZBZ together with DHCraft. While open, most delivered headers carry an empty container title (intended, not a defect). |
| O13 | TEI editorial details (subject headings) | who creates them, where in the header? Guidelines say "being clarified" | phase 3 TEI | Decider: ZBZ. Until settled, headers stay without subject headings; no pipeline blocker. |
| O18 | Test multimodal LLM correction (scan image plus OCR text) | research reports sub-1 % CER (Crosilla 2025); infrastructure exists | quality | Decider: DHCraft (project lead), own experiment; blocks nothing. |
| ~~O25~~ | Surface `<graphic url>` produced pipeline-side. RESOLVED (2026-06-21, E89) | the surface-to-image pointer was missing; blank-page placeholder pointed to a non-existent file | makes the facsimile self-contained | Implemented in E89; all surfaces carry the graphic, committed gate. |
| ~~O26~~ | teiCrafter annotation model versus ZBZ editorial guidelines. RESOLVED (2026-06-21, E88) | guidelines demand inline GND at the mention site; E87 had additionally schema-allowed a standOff register | none | Order: only the ZBZ rules apply; inline GND is the delivery model. Implemented in E88; teiCrafter output model to be aligned. |
| O27 | ZBZ README contradicts itself on captions | the register section says entities in captions are not tagged; the figures example tags an `<orgName ref="GND:...">` inside a `<figure>`. Found during the conformity check (E88) | nothing (no effect on the entity-free corpus; concerns future teiCrafter output) | Decider: ZBZ. Deliberately not machine-enforced while the contradiction is open. Question: does the ban cover the caption (`<head>`) or the whole `<figure>` block including the explanation (`<p>`)? |
| ~~O22~~ | 289 versus 286 PDF discrepancy. RESOLVED (2026-05-27) | Masterfile has 325 texts, 289 digitised, 286 delivered as PDF; the three undelivered: 1745, 1750, 1970; verified via corpus_audit | none | done |
| ~~O23~~ | `tei_final` headers not schema-valid. RESOLVED (2026-05-27, E68) | diagnosis had named only `idno`; corpus-wide validation showed four causes, all omitted by the ODD subset; fixed by E68, gated by `tests/test_tei_schema.py` | none | done |
| ~~O24~~ | `tei_validator --compare-ref` showed a wrong reference CER. RESOLVED (2026-05-27, E69) | a silent import failure fell back to a length approximation; fixed and gated | none | done |

### Stability (LLM non-determinism, released 2026-07-07, execution at the workstation)

- (a) Stability pilot: 5 documents x 3 pipeline re-runs, standard deviation of per-document CER. Currently `stability.status: open` in the JSON.
- (b) Inter-engine CER: a second OCR run with a different engine as cross-validation. Medium effort.

### Closed questions

- ~~O6~~ Normalisation versus source fidelity: E49 (source-faithful with defined normalisations)
- ~~O9~~ `div type` values for front/back matter: E49 (front: editorial, dedication; back: translation, reprint, otherEdition)
- ~~O11~~ Entities without GND entry: E38/E50 (internal ids as primary reference; removed with E71)
- ~~O21~~ Layout region post-processing: E25/E26 (Gemini QA plus detect, no manual heuristic fix)

---

## Risks

| # | Risk | Impact | Mitigation | Status |
|---|---|---|---|---|
| R2 | TEI complexity plus schema incompatibility | high | E48 (`zbz_hersch.rng`) plus E49 (guidelines) | mitigated |
| R3 | GND hallucinations | medium | none | obsolete (E71: NER removed) |
| R5 | Fork divergence DHCraft versus ZBZ | medium | define merge strategy plus CI tests | open |
| R7 | Transkribus incompatibility PAGE-XML | high | schema 2013-07-15, id scheme `{NNNN}_p{NNN}`, JPG; `@type`/`@custom` not verifiable (empty TextRegions) | partly resolved (E23, E81) |
| R10 | NER quality on French (66 % of corpus) | medium | none | obsolete (E71: NER removed) |

---

## References

- [project.md](project.md): milestones plus status
- [pipeline.md](pipeline.md): pipeline decisions
- [workflow.md](workflow.md): end-to-end workflow, viewer, round trip, save mechanism, provenance concept
- [specification.md](specification.md): requirements, gates, epics
- [final-report.md](final-report.md): measured quality state, delivery synthesis
- [journal.md](journal.md): chronological session history
