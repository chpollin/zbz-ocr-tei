---
title: Work Journal
type: journal
project:
  name: zbz-ocr-tei
  repository: https://github.com/chpollin/zbz-ocr-tei.git
method:
  name: Promptotyping
  url: https://dhcraft.org/Promptotyping/
status: draft
language: en
created: 2026-01-29
updated: 2026-07-07
tags: [zbz-ocr-tei, journal]
template:
  name: Vorlage Journal
  version: 0.2
  url: https://dhcraft.org/Promptotyping/promptotyping-document/journal
related: [decisions, index]
---

# Work Journal

Chronological development history of the project, newest entries first. The journal
condenses occasion, course, decisions, and status for each session. It is neither a git
log nor a meeting protocol: individual commits belong in the git history, decision
rationale in the register [decisions.md](decisions.md).

## Format Contract

Each entry is written at the end of the session; on re-entry, the topmost entry is read
first. New entries always appear directly under the heading "Entries". Existing entries
are never changed retroactively; corrections are new entries referencing the old one.

Fixed field order per entry: **Occasion** (one sentence: why this work now),
**Goal** (one sentence), **Course** (at most one paragraph, with references),
**Decisions** (per point: what, why, rejected alternative; register number if
available), **Status** (a few sentences, self-contained; optional commit hash as
savepoint), **Next steps** (numbered), **Dead Ends** (optional, with rationale).
Required fields: Occasion, Goal, Course, Status, Next steps.

Compact standard: entries are distilled knowledge, not protocols. Keep every decision,
identifier, figure, and hash; drop narrative detail. The full-length originals of all
entries up to session 79 remain in the git history.

Style rules: formal and project-specific; explain technical terms on first use within
the entry; quantities with reference unit. Not included here: specifications (they
belong in [decisions.md](decisions.md) or the domain docs), code diffs and commit
texts, hour-by-hour protocols, self-assessments, notes on documentation maintenance
itself, personal names (use roles and organisations instead).

Translated to English and compacted on 2026-07-07 by operator decision; knowledge
preserved, pre-compaction entries in git history.

Sessions 1 to 68 remain in the compact archive below (one line per session); from
session 69 onwards the entry structure of Journal template v0.2 applies.

## Entries

### 2026-07-07 Session 80: Knowledge restructuring completed, site in English, final report v2, push

**Occasion** Operator assignment to work everything off up to one push and one compact report, including the dissolution of viewer.md, quality.md, and frontend-gaps.md into other knowledge documents.

**Goal** A pushed repository state in which the documentation set is English, deduplicated, and correct: specification and final report exist, the three dissolved documents are gone without dangling references, and the docs/ site speaks English.

**Course** Integration first: workflow.md absorbed the viewer knowledge (pages, modes, editors, blank pages, workflow status model, Hersch design system), infrastructure.md the viewer deployment, specification.md the normative quality method plus the validation rule catalog (R1-R7, W1-W19, Z1-Z6/Z8) and the open frontend requirements (N1/N3/N6/N7 plus page strip and provenance panel), ecosystem-synthesis.md the six-frontend survey with its stale H1-H5 risk list corrected to the fixed state. Then the three source files were deleted and every reference remapped (README, data/README, scripts/README, project/pipeline/methodology/index, CLAUDE.md, six Python docstrings). knowledge/final-report.md was authored as v2 of the 2026-05-27 work report, same structure, English, updated values (fidelity mean 2.71%, median 1.40%, CI [1.77, 3.82], paired gain -9.45 pp at p=0.013), the schema-validation placeholder resolved (285/285, warning docs 145), the footnote-demotion and E90 reading-order chapters added, appendix cleaned (no ocr_dedup.py, JSZip correctly marked planned). Site wave: viewer.html, methode.html, about.html, impressum.html translated in the main loop (methode.html also fixed the Nosova-to-Levchenko attribution and the stability status; about.html the stale download-only persistence claim); the eight JS modules were translated by three Sonnet agents in parallel, a fourth swept the Markdown set (result: zero broken links, zero German prose outside exempt categories). Data values `unverifiziert | in_arbeit | verifiziert` and all `zbz_tag` values remained invariant throughout; only display labels changed.

**Decisions** Dissolution mapping: normative content to specification.md, operative viewer knowledge to workflow.md, measured values to final-report.md (dated snapshot, therefore allowed to carry figures); rejected keeping a thin quality.md stub because the SSoT rule forbids two homes per fact. The final report lives in knowledge/ as a versioned document, reports/ keeps only the generated M3 preview artifact. Foreground Sonnet agents for bulk translation after two background fleets had died silently on this host; the main loop keeps integration and authoring.

**Status** pytest green on the laptop (326 passed, 9 skipped; the skips are the data-bound gates whose data lives at the workstation). Committed and pushed this session on top of savepoint `16b3323c`.

**Next steps**
1. Workstation, M3 rollout: re-run `reading_order_audit` and `tei_reassemble_preview --all`, confirm 831 to 39, then release `tei_unified --all --reassemble`; afterwards full pytest, `tei_validator --all`, `corpus_audit`, mirror regeneration via `generate_edition_data`.
2. Workstation, residual pages: `reading_order_audit --worklist`, review the 39 pages at the facsimile (35 count mismatches, 4 column edge cases).
3. Workstation, stability measurement (released): 5 documents times 3 runs, report per-document CER spread, close `stability.status` in `cer_statistics.json`.
4. Workstation, fresh frontend gap analysis on the full corpus; findings land in specification.md.
5. teiCrafter handover preparation (TEI control + inline-GND annotation); entity gate Z1-Z4 turns sharp there.
6. Backlog: translate the report strings of `tei_reassemble_preview.py` so the regenerated M3 report is English (current artifact is German).

### 2026-07-07 Session 79: Documentation correctness pass, style rules, README slimming

**Occasion** Operator assignment: knowledge folder, README, and CLAUDE.md must contain only correct and constructive statements.

**Goal** Find and fix factually wrong, colliding, and missing documentation statements without touching code or data.

**Course** Nine findings, all fixed: a false "not checked in" claim about `cer_statistics.json` (CLAUDE.md and methode.html; git history proves the file is a deliberate evidence artifact), the validator report path still pointing to `tei_unified` after the Session 76 default change, a wrong knowledge-doc count in the README, the M3 identifier collision (removed NER milestone versus structural-fix delivery), the README concealing the reading-order defect and pending rollout, the M5 pending item misread as an own obligation, the M3 tools missing from the CLI reference and inventory, unbound volatile test counts, and the stale E82 `ocr_dedup` caveat. A second wave codified new Markdown style rules (no bold emphasis, no dash connectors, no volatile quantities in durable documents) in CLAUDE.md and slimmed the README by SSoT deduplication after verifying every fact exists in its target knowledge doc.

**Decisions** `cer_statistics.json` stays versioned (history proves intent; untracking rejected). M3 collision resolved by an identifier note in project.md, not renumbering (avoids alias drift against journal entries 74 to 78). Volatile counts removed rather than maintained (no drift watcher exists). Subsequent operator decisions: all Markdown documentation becomes English including journal, register, and reports; four knowledge files renamed to English; savepoint commit before the translation wave; reports/ collapses into one final work report in knowledge/; journal entries are compacted to a distilled standard.

**Status** Both waves done and verified; savepoint `16b3323c`. The translation, integration, and consolidation wave runs as its own unit on top. M3 remains operator-gated (Session 78).

**Next steps**
1. Finish translation wave, integrate viewer/quality/frontend-gaps into other docs, write final report, sweep, commit, push.
2. Operator decision M3 at the workstation: accept dry run, release delivery, review the 39 remaining pages at the facsimile.

### 2026-06-21 Session 78: Root cause of the 39 remaining pages isolated (count mismatch, not geometry gap; corrects Session 77)

**Occasion** Operator assignment to continue; the open item was the root-cause analysis of the 39 W19 pages that reassembly does not fix.

**Goal** Understand why the 39 pages stay, and whether a safe fix exists or they belong to facsimile review.

**Course** The Session 77 hypothesis (geometry gap between region and zone bboxes) is refuted: `reading_order_permutation` is idempotent. 35 of 39 pages have an OCR-paragraph versus layout-region count mismatch (810 p.56: 3 against 236; 1240 p.3: 50 against 61); in the mismatch branch of `match_paragraphs_to_regions` the emitted zone slice becomes non-canonical, so W19 fires correctly. The remaining 4 pages have 1:1 counts but a geometry that breaks column detection (sub-60% header protruding into the second column, e.g. 460 p.1).

**Decisions** Rejected re-sorting the emitted zone slice to force W19 to zero: it silences the warning without fixing the upstream segmentation problem. The 39 pages are genuine facsimile-review cases, not tool defects. E90 updated; corrects Session 77.

**Status** Root cause verified (35 count mismatch, 4 column edge cases), reproducible from the caches. No code changed. Reassembly stays at 831 to 39.

**Next steps**
1. Operator decision M3 (gated): accept dry run, release delivery, review the 39 pages.
2. Optionally address the count mismatch upstream (OCR paragraph versus layout region segmentation).

### 2026-06-21 Session 77: M3 reassemble preview built (reversible dry run, W19 831 to 39)

**Occasion** Research coordination sync revealed the ordered artifact of this iteration was still open: a verified dry run of the reading-order correction.

**Goal** Prove that corpus regeneration corrects the W19 pages without overwriting the delivered source of truth, with a deterministic before/after report and tests.

**Course** The M1 fix sits in `tei_step1.match_paragraphs_to_regions` and reassembly recomputes step 1, so it applies. `process_document` writes to the `tei_unified/` workspace, never to `tei_final`, making the preview inherently reversible. The new tool `scripts/tei/tei_reassemble_preview.py` reassembles every W19-affected document into `output/tei_preview` and counts W19 with the same shared logic as validator and audit. Cold step-2 caches would trigger Gemini calls, so the preview runs with `dry_run=True` (warm cache used, cold pages fall back to the step-1 scaffold, no API cost). Result over all 216 affected documents: W19 drops from 831 to 39 pages, 188 documents reach 0, 28 keep 39 pages; `tei_final` stayed byte-identical (SHA256).

**Decisions** Preview offline and free via `dry_run=True` (reading order originates in step 1, independent of paid refinement; live path rejected). Report deterministic (sorted, no timestamps). The residual gap not fixed autonomously (design decision touching the W19 definition). No new register number (E90 continued); rollout stays operator-gated.

**Status** Tool, 6 tests, and deterministic report `reports/m3-reassemble-preview.md` in place; full suite 1187 green. The 39 remaining pages over 28 documents are the facsimile worklist.

**Next steps**
1. Operator decision M3: accept the dry run and release the delivery, or close the geometry gap first.

### 2026-06-21 Session 76: Delivery verification (samples plus full check), validator default fixed to the SoT

**Occasion** Operator question whether the delivered corpus is actually verifiable, with instruction to check the data, not just the git state.

**Goal** Back the delivery claim "schema-valid and ZBZ-conformant" with reproducible measurement, sample real content, and surface any findings from the verification path itself.

**Course** Read-only checks over the SoT `output/tei_final` (n=285): schema 285/285 valid, ZBZ conformity Z1-Z8 285/285. The reading-order audit reproduces 216 documents / 831 pages (557 robust, 274 fragile over 145 documents); corpus funnel confirmed. Warning profile non-blocking throughout, largest items W17 (844 empty speaker slots, a curation slot) and W19 (831). Three content samples (2310 French, 760 Chagall with correct ligatures, 810 German two-column) confirm OCR quality; 810 p.7 directly evidences the interleaved column order the M1 fix corrects. A tool pitfall surfaced: the validator default targeted the stale `tei_unified` directory and would have produced a false alarm; the default now points to `tei_final`, `--doc` resolves layout-tolerantly, `--dir` still overrides.

**Decisions** Validator default corrected instead of documented around (the wrong default was itself the defect). No register number (pure tool fix).

**Status** SoT fully green at the machine-checkable level; warnings are curation signals. Full suite 1179 green. The reading-order defect is confirmed real in the delivered corpus.

**Next steps**
1. Operator decides the M3 cut (trust robust majority after sampling plus review of the 274 fragile pages, or piecewise).

### 2026-06-21 Session 75: M3 triage, reading-order audit (robust/fragile) with shared W19 extraction

**Occasion** Operator assignment after the milestone round: make the operator-gated M3 decidable and safe instead of writing to the corpus.

**Goal** Triage the W19 set into threshold-independent (trustable) reorderings and edge cases needing review.

**Course** Behaviour-preserving refactor first: page/zone extraction moved into the shared generator `iter_page_zone_bboxes` so validator and audit see the same page set; `reading_order_permutation` gained optional threshold parameters with behaviour-preserving defaults. New diagnostic `scripts/eval/reading_order_audit.py` recomputes the canonical permutation under threshold perturbation (WIDE 60 +/-5, GAP 12 +/-3): stable means robust, flipping means fragile. Finding: 831 pages over 216 documents; 557 robust, 274 fragile, 145 documents carry at least one fragile page. Review work shrinks from 216 documents to 274 pages plus a sample over the robust majority.

**Decisions** Documented under E90 as M3 preparation, deliberately no new register number (rollout unratified). Recommendation: trust robust pages after a small sample; review fragile pages individually (`--worklist`).

**Status** Audit instrument acceptance-ready, 9 tests, full suite 1179; no write to the corpus. Savepoint `8aa3a87d`.

**Next steps**
1. M3 waits for the operator cut decision.

### 2026-06-21 Session 74: Milestone round, column/band-aware reading order (M1) plus validator warning W19 (M2)

**Occasion** Milestone round of research coordination: pick, build, and verify the next two milestones from the edition-philology persona, scope the third.

**Goal** Address the proven structural defects behind the high CER tail (E80): the double-page reading order complementing the footnote overdetection.

**Course** Finding: `match_paragraphs_to_regions` sorted regions purely by `y_pct` (live and legacy call site, identical bug), re-interleaving columns that layout detection had already delivered left-first. M1: shared pure function `reading_order_permutation` (full-width blocks at w>=60% segment the page into bands; within a band, columns split at >12% x-center gap are read left to right, top to bottom per column; single-column pages fall back exactly to the old order). Both call sites converged; 9 tests; commit `6f51eac2`. M2: non-blocking validator warning W19 compares delivered block order against the canonical order of the same zones, scoping the not-yet-regenerated corpus; 4 tests; commit `f72743ac`.

**Decisions** Registered as E90. W19 naming clarified (the E85 note "3 W19 diagnosis specs" was a provisional label for never-implemented proposals; future specs start at W20). Philological judgment: repair the generator and make the backlog visible instead of blindly rewriting delivered edition text by geometric heuristic; automatic reordering of the delivered corpus stays operator-gated (M3, green criteria: 0 W19, schema and conformity stay 285/285, fidelity CER of 30/760 drops).

**Status** Both milestones acceptance-ready, full suite 1168, savepoint `f72743ac`. Remaining roadmap: M3 rollout; entity gate Z1-Z4 on curated inline-GND output; footnote residue curation; LLM OCR stability quantification; ZBZ questions O8/O13/O27.

**Next steps**
1. M3 operator-gated; W19 runs in the validation gate and reports the scope.

### 2026-06-21 Session 73: Consolidation part 1 (code base) verified, orphan note removed

**Occasion** Next work phase of research coordination; the code-base consolidation pass was still open.

**Goal** Check whether the code base needs behaviour-preserving cleanup; remove only what is provably dead.

**Course** Survey over all tracked scripts and tests. The only apparent redundancy, the three `cer_statistics*` files, is deliberate tested layering (pure statistics library, corpus-dependent collector, orchestrator CLI); merging would break the architecture. One stale artifact remained: `HANDOFF-cc3.md` in the repo root, a dated handover note fully superseded by E89 with zero references; removed (commit `0e1712c3`). Committed gates green afterwards.

**Decisions** No new register number. CER statistics layering deliberately kept.

**Status** Code base consolidated; savepoint `0e1712c3`.

**Next steps**
1. Entity conformity gate Z1-Z4 on curated inline-GND output once teiCrafter switches its output model.

### 2026-06-21 Session 72: Independent verification of the ZBZ delivery, consolidation report to research coordination

**Occasion** After completing the order (Session 71), the delivered corpus had to be verified independently and reported.

**Goal** Reproduce the three conformity gates on the real corpus and state the gate's reach precisely.

**Course** Checks directly on `output/tei_final` (285 files): schema plus project rules 285 valid / 0 invalid / 145 with non-blocking warnings; ZBZ conformity 285 conformant / 0 violations; committed gates together 583 passed. Reach finding: the corpus carries 0 files with `ref="GND:"`, 6 bare `<persName>`, 400 `<bibl>` without authority linking; the entity rules Z1-Z4 idle on an authority-free corpus and become sharp only once curated inline-GND documents pass through (lesson L14).

**Status** Delivery independently verified, matching the committed tests. Handoff to research coordination updated with the vault knowledge delta. No open gates.

**Next steps**
1. Switch the teiCrafter output model to inline GND, then apply the conformity gate to curated output.
2. Clarify ZBZ questions O27, O13, O8 via the operator.

### 2026-06-21 Session 71: ZBZ order implemented: inline-GND schema (E88), conformity check, page-image linking (E89)

**Occasion** Research coordination issued three tasks from the evaluated ZBZ material; corrects Session 70, which built the standOff model (E87) before the ZBZ material was available.

**Goal** Implement and verify all three task items; anchor inline GND as the binding delivery model.

**Course** (1) Model: the schema diff showed the active schema equals the ZBZ template plus E68 plus E87; the corpus is entity-free since E71, so removing E87 was risk-free. E87 reverted, `@ref` patterns narrowed to GND-only; active schema now exactly ZBZ template plus E68; 285/285 still valid, new standOff guard test. (2) Conformity: editorial rules already partly encoded as R/W rules were complemented by the inline-GND model rules RelaxNG cannot express (`zbz_conformity.py`, `--conformity` mode): 285/285 conformant. (3) Page image: `<pb facs>` is the binding form; every surface now gets `<graphic url="{doc_id}_p{NNN}.png"/>` as first child; all 4108 referenced images exist.

**Decisions** E88 (inline GND as delivery model; raw ZBZ template adoption rejected, it would invalidate all 285). E89 (surface graphic with relative address scheme; absolute URL and IIIF rejected, hosting open). O26 and O25 closed, O27 opened.

**Status** All three items implemented and test-gated (schema gate, `test_zbz_conformity.py`, `test_tei_surface_graphic.py`); full suite green; three commits on main.

**Next steps**
1. Align teiCrafter output model with inline GND.
2. Clarify O27, O13, O8 with ZBZ.

### 2026-06-21 Session 70: Schema extension teiCrafter standOff (E87), facsimile finding, warning alignment

**Occasion** Documents annotated in teiCrafter were invalid against their own schema because the ODD subset lacked `standOff` and generic `<name>`.

**Goal** Make curated documents schema-valid, document the decision, regression-check the corpus, align the knowledge docs.

**Course** Data contract lifted from teiCrafter; schema minimally extended following the E68 pattern (standOff, name, eleven element defines plus a dedicated standOff work register). Verified: synthetic curated document valid, all 285 `tei_final` still valid, new tracked schema gate. Facsimile check: the generator produces `surface`/`zone`/`@facs` completely, only the surface-to-image pointer `<graphic>` was missing (opened O25). Warning figures aligned across the knowledge docs (15 active warning rules W1-W7, W11-W18 versus documents-with-warnings, previously conflated).

**Decisions** E87 (later reverted by E88 in Session 71). O25 opened.

**Status** Schema extended and gated; knowledge docs consistent with the measured state.

**Next steps**
1. Operator decision O25 (URL scheme for surface graphics).

### 2026-06-10 Session 69: Repository audit with implementation wave (E86)

**Occasion** Before ZBZ acceptance the whole repository was to be reviewed, including known viewer defects.

**Goal** Fix all verified findings in one pass and bring the knowledge base redundancy-free to the actual state.

**Course** Viewer: the XML mode's data-loss risk fixed (it loaded a single page while saving overwrote the whole `_final.xml`; now it loads the whole document and a save guard rejects incomplete TEI). Remaining gap-analysis findings fixed: go-to-page with keyboard navigation, live status lamps in the catalog, clear error messages with retry, modal focus management, keyboard/screen-reader operability of both editors. Process: GitHub Actions runs the full test suite on every push/PR; `requirements.txt` made runnable for fresh environments; two Transkribus scripts close file handles on error. Documentation: stale CER figures pulled to the canonical state site-wide; decision register entries from E64 as dated subchapters; roadmap separated done from open.

**Decisions** XML mode shows and saves the whole document (E86; single-page alternative rejected as inconsistent with the save architecture E72). Four comfort findings N1/N3/N6/N7 deferred until after ZBZ acceptance. `data/curated_tei/` declared reserved and currently empty (gold-standard label rejected, nothing is verified yet).

**Status** Suite 563 green, 285/285 schema-valid, all high and medium findings fixed. First content curation via the viewer exists (work titles as `<bibl>` in 3200 and 760). All 855 streams `unverifiziert`.

**Next steps**
1. Render check of the TEI data in the teiCrafter integration.
2. Begin content curation in the viewer.
3. Implement deferred N findings after acceptance.

---

## Compact Archive (Sessions 1 to 68)

One line per session, newest first. Rationale in the [decision register](decisions.md),
details in the git history.

### June 2026: acceptance preparation

| # | Date | Topic |
|---|---|---|
| 68 | 2026-06-08 | Doc-30 cleanup and tail analysis (E82): duplicated OCR block pair removed (fidelity CER 18.25 to 11.59 %); remaining outliers have structural causes, not character recognition. Corpus mean 4.26 to 3.99 % published consistently. |
| 67 | 2026-06-08 | Transkribus export/upload (E81): pipeline PAGE-XML playable back into Transkribus (bundle builder plus REST upload); sample of 18 documents built, doc 1500 verified on the platform; auth via env vars only. |
| 66 | 2026-06-08 | CER framing print-calibrated (E80): print corpus must not be judged by handwriting benchmarks; evaluation anchored to print literature, evaluative labels removed. |
| 65 | 2026-06-07 | M2.4 image URL scheme plus ZBZ test plan for the teiCrafter integration: `{id}_p{KKK}.png` with K as scan position; deployment verified live (GitHub Pages, no IIIF); demo object 1540. |
| 64 | 2026-06-07 | Frontend gap analysis over 6 frontends: Hersch high findings H1 (TEI edit could overwrite `_final.xml`) to H5 (modal without focus trap); token discipline confirmed; frontend-gaps.md created as SSoT. |
| 63 | 2026-06-07 | Viewer curation: one save button (E78) plus mirror-write fix (E79); every save now writes both the canonical `output/` location and the `docs/data/` mirror, viewer reads curated data first. |
| 62 | 2026-06-07 | Workflow status collapsed from four to three stages (E77): `unverifiziert`/`in_arbeit`/`verifiziert`, one colour per stage, red reserved; new gate `test_workflow_status.py`. |
| 61 | 2026-06-03 | Acceptance deep analysis, repo hygiene, MMSID removal (E76): corpus invariants verified on real data; Alma catalog number projection removed (catalog metadata is ZBZ domain, O8); root README rewritten for acceptance. |

### May 2026: viewer data supply, deploy preparation, edition uplift

| # | Date | Topic |
|---|---|---|
| 60 | 2026-05-27 | Frontend UI review of all 5 docs/ pages plus quick wins: blocking prompt replaced by inline field, dirty markers per stream, mobile/filter/sort fixes, JS cache versioning. |
| 59 | 2026-05-27 | Repository cleanup wave W1-W5: documentation drift, dead NER remnants, hex-to-token fixed; OCR sources unified on `loaders.OCR_SOURCES`; incoherent CER scope exclusion removed (E73); Schematron documented instead of built (E74); `ocr_dedup` and DoclingOCR engine removed (E75). |
| 58 | 2026-05-27 | Direct-write loop for viewer curation (E72): File System Access API writes into the repo folder (Chromium, download fallback); `loaders.py` consumes curated files in `--reassemble`. |
| 57 | 2026-05-27 | Documentation correctness wave: all Markdown audited against the real repo state alongside E70/E71. |
| 56 | 2026-05-27 | NER/entity linking fully removed (E71): only ~2.6 % of ~30,500 mentions carried real GND ids; deterministic tag strip over all 285 TEI, 285/285 schema-valid. |
| 55 | 2026-05-27 | CER methodology deep-checked and corrected (E70): ZBZ references are selective partial transcriptions; new fidelity/scope decomposition, three CER paths unified, paired test corrected. |
| 54 | 2026-05-27 | Hygiene and correctness wave (E69): silent validator CER import error fixed, `<pb>` splitter deduplicated into `pb_split.py` (byte-identical over all 285 finals), `build_tei_header` lifted to the delivery contract. |
| 53 | 2026-05-27 | Schema regression found and fixed (E68): the delivered layer `tei_final` had never been batch-validated and stood at 0/285 valid; schema extended, 285/285 valid, new gate `test_tei_schema.py`. |
| 52 | 2026-05-26 | E66 completion: `tei_status_marker` over all 285 documents (misleading agent-screening entries out, honest workflow entries in); frontend audit with 15 prioritised findings. |
| 51 | 2026-05-26 | Catalog UI refactor plus traffic-light reframing (E67): status `offen` renamed to `unverifiziert`, red reserved; filters, sorting, workflow column reworked. |
| 50 | 2026-05-26 | Agent screening abolished, per-stream workflow status introduced (E66): human-set status per data stream with provenance history in the per-object manifest. |
| 49 | 2026-05-26 | Blank-page manifest plus TEI marker (E63 phase 2; E65): 79 blank pages in 15 documents detected deterministically, `<pb type="blank"/>` projected, junk bodies emptied. |
| 48 | 2026-05-26 | Viewer UI condensed (E64): dead OCR engine dropdown removed (viewer = delivered edition = Mistral), doc subbar and toolbar fused. |
| 47 | 2026-05-26 | Viewer live review plus blank-page wave (E63): per-object manifest decided as SSoT for page facts, TEI marker as projection. |
| 46 | 2026-05-26 | Method page `docs/methode.html` as lean successor of the abolished CER dashboard (E62). |
| 45 | 2026-05-25 | Edition uplift wave started (E58-E61): OpenSeadragon facsimile renderer, edit toggle per panel, JSZip export module planned. |
| 44 | 2026-05-25 | Finding fixes plus consistency refactoring: TEI double encoding fixed, `<pb>` splitter balances `<div>` boundaries; all 4970 delivered XML well-formed. |
| 43 | 2026-05-25 | Viewer extended to the full corpus (E57): mirror generator for all 285 documents, three-stage path resolver, GitHub-Pages ready; image delivery stays local. |

### April 2026: frontend radical cut, scientific CER re-evaluation

| # | Date | Topic |
|---|---|---|
| 42 | 2026-04-27 | Knowledge consolidation (25 to 10 docs) plus frontend radical reduction: 9 to 1 HTML, 23 to 6 JS, CSS minus 84 %; new single-page viewer (E56). |
| 41 | 2026-04-27 | CER scientifically grounded: BCa bootstrap CIs (B=10000, seed 42), paired test E2E versus OCR-only, selection bias flagged honestly (E54/E55). |

### March 2026: pipeline consolidation plus edition

| # | Date | Topic |
|---|---|---|
| 40 | 2026-03-27 | Frontend refactoring phases 1+2: CSS token consolidation, HTML semantics, JS foundation layer, unified TEI renderer. |
| 39 | 2026-03-26 | OCR diagnostics closing: 6 scope mismatches identified; cleaned statistics n=19 mean 4.18 % / median 1.83 %. |
| 38 | 2026-03-26 | Diagnostics UI rewrite: 4 tabs, search index 279 to 285 (XML parsing fix). |
| 37 | 2026-03-26 | Diagnostics data production: W10 deep analysis, corpus statistics, validation timeline. |
| 36 | 2026-03-26 | Edition sync continuation: log tab, page count 383 to 4117. |
| 35 | 2026-03-26 | Edition synchronisation: catalog 15 to 285 documents, revisionDesc in the reader. |
| 34 | 2026-03-26 | TEI quality: ref pattern extended (GND plus #zbz), 285/285 schema-valid; heuristic lb injection (10,635 lb in 46 documents). |
| 33 | 2026-03-26 | OCR diagnostics plus eval optimisation: symmetric normalisation, hyphens, CI alignment; mean CER 9.33 to 5.97 %, median 5.52 to 2.42 %. |
| 32 | 2026-03-26 | End-to-end CER benchmark (E51): TEI-versus-TEI eval, median 5.5 %. |
| 31 | 2026-03-26 | New schema `zbz_hersch.rng` plus binding ZBZ editorial guidelines incorporated (E48/E49/E50). |
| 30 | 2026-03-15 | Hersch design system: anthracite plus brick red plus EB Garamond plus Jost, two-level CSS tokens. |
| 29 | 2026-03-15 | NEEDS_REVIEW 32 to 0: 20 new entity stopwords (E45), structure fixes, OCR dedup tool (E46; removed later by E75). |
| 28 | 2026-03-15 | Edition frontend refactoring: discovery hub, full-text search, gallery, screening and curation workflow separated. |
| 27 | 2026-03-15 | Agent-based quality screening rollout 285/285; revisionDesc standard (E42), `output/tei_final/` as single source of truth (E43). |
| 26 | 2026-03-15 | TEI validation quality gate refactored: two levels (errors/warnings), W1-W11, HTML report; `--reassemble` flag. |
| 25 | 2026-03-14 | Frontend consolidation: edition to `docs/`, ES5 to ES6+ in 13 JS files. |
| 24 | 2026-03-12 | Viewer extension: GND 0 % bug fixed (`entity_index.py` never wrote GND into the TEI; fix plus cache backfill, 0 to 21.7 %). |
| 23 | 2026-03-09 | NER completion plus TEI entity injection: 285 documents, 11,685 entities, 26,197 mentions. |
| 22 | 2026-03-09 | Knowledge refactoring: EDITION and CURATION separated; NER production run over 285 documents. |
| 19-21 | 2026-03-08 to 09 | Curation editor phases 2-5: block toolbar, entity curation with autocomplete, review workflow, TEI validation. |
| 17-18 | 2026-03-08 | tei_unified refactoring (orchestrator ~1100 to ~70 lines); NER robustness; NER production phase 1 (E35). |
| 14-16 | 2026-03-06 to 07 | Unified TEI pipeline (E32): four stages; NER pipeline (E34): Gemini Flash Lite, six entity types, Wikidata reconciliation. |
| 12-13 | 2026-03-06 | Gemini vision TEI (E30, superseded); document-type-specific prompts; layout QA full run E31 (14,708 corrections). |
| 11 | 2026-03-05 | Gemini document classification (E27), online demo (E28), Gemini OCR correction stage 2b (E29). |
| 9-10 | 2026-03-03 to 04 | docling-serve API (E24), Gemini layout QA plus detect (E25/E26): three modes. |

### February 2026: pipeline build-up

| # | Date | Topic |
|---|---|---|
| 7-8 | 2026-02-25 to 27 | Scope expansion (E21): full pipeline (OCR, layout, PAGE-XML, NER/GND, TEI); pilot 15 documents; data delivery E23 (286 PDFs, 25 TEI). |
| 4-6 | 2026-02-14 to 20 | Mistral OCR as production engine (E6); Azure integration; PAGE-XML plus METS export (E13); dashboard redesign (E15). |
| 1-3 | 2026-01-29 to 02-14 | Initial source analysis: 286 PDFs, four document types (A-D), language split FR 66 % / DE 30 %; hybrid pipeline decision (E1): Docling layout plus LLM OCR text. |

Older detail entries preserved in the git history.

---

## Lessons

Observations distilled from the sessions that stay relevant for future work:

- L1: Validation must be actionable. A false-positive rate above 50 % makes reports useless; every warning needs a concrete action.
- L2: Entity type must not get lost; annotation needs `(tag, id)` from the index, not just names.
- L3: A stopword filter is essential; generic nouns produce ~30 % false positives without it.
- L4: Merge page fragments into document structure; the ZBZ reference has one top-level div, and the post-assembly merge is deterministic and free.
- L5: Invalidate the step-2 cache on prompt changes; `--force` does not regenerate it.
- L6: LLM NER carries ~5-10 % inherent false positives; the answer is a curation editor, not a code fix.
- L7: Page-numbering drift breaks pagewise CER; content-aligned evaluation is immune.
- L8: Parse multilingual codes correctly ("fra/deu" otherwise decays to "und"); affects ~40 documents.
- L9: Keep facsimile and pb in sync; empty surfaces for pages without layout zones.
- L10: Internal ids as primary reference; GND in `ref`, internal in `corresp` (dual attribute, E50).
- L11: Server-less persistence has two truths: the canonical consumption location (`output/`) and the frontend's read location (`docs/data/` mirror). Writing only to the first saves for real but invisibly for the curator.
- L12: With parallel instances in the same tree, `git status` plus verification against the real file state is mandatory; a "file modified since read" conflict is the signal to step back, not to force.
- L13: A prose figure ("285/285 valid") is no evidence; the delivered SSoT needs an automated gate, not a claim.
- L14: A green conformity gate is only as sharp as the corpus it runs over; on the entity-free `tei_final`, "285/285 conformant" means "no violation", not "entities correctly GND-tagged". The entity rules Z1-Z4 bite only after inline-GND curation.
- L15: Newspaper layouts fail systematically (>40 zones, OCR hallucinations); ~3 % of the corpus.
- L16: Tier-2 documents (4-8 pages) reached 85 %+ APPROVED rate, tier-1 (1-3 pages) only 40 %.

<!--
Entry template (insert new entries directly under "## Entries"):

### YYYY-MM-DD Session N: session title

**Occasion** [One sentence: why this work now.]

**Goal** [One sentence: what should exist at the end.]

**Course** [At most one paragraph: what actually happened, with references. Distill.]

**Decisions**
- [What, why, rejected alternative. Register number if available.]

**Status** [A few sentences, readable on their own. Optional commit hash as savepoint.]

**Next steps**
1. [Concrete enough to start the next session.]

**Dead Ends** [Optional: tried and rejected, with rationale.]
-->
