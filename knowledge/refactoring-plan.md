---
title: Refactoring Plan 2026-08
type: knowledge
project:
  name: zbz-ocr-tei
  repository: https://github.com/chpollin/zbz-ocr-tei.git
method:
  name: Promptotyping
  url: https://dhcraft.org/Promptotyping/
status: active
language: en
created: 2026-08-21
updated: 2026-08-21
tags: [zbz-ocr-tei, refactoring, documentation, code-hygiene, plan]
related: [index, decisions, journal, agent-orchestration, methodology, entity-integration]
authors: [Christopher Pollin]
---

# Refactoring Plan 2026-08

Working plan for the repository-wide refactoring of documentation, reports, code layout,
code hygiene, frontend and journal. It is a dated working document and therefore carries
the baseline figures it was cut from; when every package is closed the plan is deleted
and the decision register holds the outcome. Convention function: freehand plan, like
[entity-integration.md](entity-integration.md).

## Operator decisions the plan rests on (2026-08-21)

- Scope covers documentation, code hygiene, the `scripts/` layout and the frontend.
- Obsolete artifacts are deleted; git history retains them, the register names the last
  commit that carried them.
- `knowledge/` keeps its thematic split and is streamlined; each fact gets one owner.
- The journal is condensed for sessions 69 to 96 and moves to a more formal entry form; an
  archive document takes the long entries and the journal links to it.
- `knowledge/arbeitsbericht-v3.md` stays outside every package until its uncommitted diff
  (held by another instance) is committed.

## Baseline (2026-08-21, before any change)

- Tests: 2152 collected, 2151 passed, 1 skipped, 22 s, no network, no writes outside
  `tmp_path`.
- Ruff (`ruff check scripts tests`, ruff 0.16.2): 368 findings, 178 safe-fixable; entity
  layer clean; per folder eval 126, layout 68, tei 60, ocr 60, edition 12, core 0.
- CLI contract: 76 `python -m scripts.*` and 2 `python scripts/*.py` occurrences in
  `CLAUDE.md`; every module and every flag resolves today.
- Documents: 17 files in `knowledge/`, 10 in `reports/`, 7 HTML pages in `docs/`.
- Journal: compact archive ends at session 68; 28 full entries since.

## Findings digest (evidence in the six audits of 2026-08-21, file:line as cited there)

### D1 Stale statements in durable documents

specification.md still frames the reading-order rollout, the pb_folio and body-note runs
and the LLM stability measurement as open or operator-gated (all executed or refuted,
E94/E95/E99/E100) and names a frontend gap analysis as planned (ran 2026-08-12);
workflow.md describes the pre-E107 viewer (three modes, edit toggles, three status pills,
five pages, `entities=1` opt-in) and omits the entities stream in §5.1 and the roadmap;
index.md caps the register at E106, carries the pre-E99 W19 concept and no entity-layer
concept; decisions.md heading says E64 to E107 and its stability block says `open`;
pipeline.md links a non-existent `methodology.md §Commands` and an Obsidian wikilink
`[[O25]]`; ground-truth-map.md describes the 1520 repair as pending adoption though 1520 is
measured inside the 25-document benchmark; ecosystem-synthesis.md is a June snapshot that
predates E90 to E119; README.md calls `@facs` cross-linking planned (delivered, E114);
CLAUDE.md overstates `--policy` (five scripts carry it) and omits `legacy_mentions.json`;
scripts/README.md calls the reassembly preview an M3 dry run, misses `blank_text_audit`,
lists 24 of 55 test files and carries a July footer; entity-evaluation.md and
agent-orchestration.md have no frontmatter; entity-evaluation.md does not mention the
second frozen draw `output/audits/eval_sample_2026-08-13/`.

### D2 Duplicated facts (single-source violations)

methodology.md §Operative Tools reproduces the CLAUDE.md command reference; the E66
screening-to-status story sits in methodology, workflow §3.6 and pipeline; the corpus
funnel sits in project.md and ecosystem-synthesis; the E22 clarification in pipeline,
workflow and ecosystem; reference phenomenon frequencies in pipeline and
ground-truth-map; the CER formula and threshold in specification and cer-methodology; the
verdict-store description in entity-integration and entity-evaluation; the validator rule
tally in project and specification; `--reassemble` semantics in workflow and methodology.

### D3 Volatile quantities and names in durable documents

methodology.md screening tallies; literature-comparison.md hard-coded fidelity median and
best-document band; cer-methodology.md test count; entity-evaluation.md "51 deviations,
2 real"; workflow.md provenance example with a third-party editor's initials.

### D4 reports/

Keep unchanged: `2026-08-12_adjudication-protokoll.md` (byte-identical to the operative
protocol, the only tracked copy), `2026-08-12_fp-hunt-protokoll.md` (wave not yet run),
`2026-08-12_entity-eval-ergebnis.md` (referenced from code, tests, README, knowledge),
`cer-gegenprobe-2026-07-03.md` (external verification evidence, referenced from E91 and
cer-methodology). Delete after securing unique content: `2026-07-07_verifikation-
berichtsfragen.md` (corrections applied; diagnosis parts D9/D11/C8/F13-F15 to be checked
for a home), `2026-08-12_doku-frontend-audit.md` (17 of 20 applied, 1 rejected, 1
deferred as an M7 item to record in entity-integration.md, 1 re-lapsed and handled in WP2),
`2026-08-12_workflow-entitaetsannotation.md` (covered by the 2026-08-21 paper except the
"three kinds of knowledge" passage). Keep until the open quick wins are decided:
`2026-08-12_viewer-ui-analyse.md` (E107 cites it; Q1/Q3/Q5/Q10 not applied). Merge target
for the entity papers: the 2026-08-21 paper stays as the one conceptual text, its
category-wise gold-benchmark figures and the stock-run ordering recommendation move into
entity-integration.md and entity-evaluation.md. `m3-reassemble-preview.md` is deleted
together with `tei_reassemble_preview.py` (E99, go pending since session 93).
ecosystem-synthesis.md moves to `reports/2026-06-07_ecosystem-synthesis.md` with an index
pointer, because its cross-repo picture has no other home.

### D5 docs/ static pages

methode.html carries eight CER figures and a regeneration date that contradict
`docs/data/cer_statistics.json` (no page fetches that file, every number is hand-copied);
about.html omits `entity_overview.json` and the entities page in its architecture
section; the unlinked `folien-entitaetsannotation.html` ships a dated German deck with its
own hex palette on the English Pages root; impressum.html and viewer.html lack the
Entities nav link (chrome drift); `tokens.css` is loaded as `?v=3`, `?v=4` and `?v=7` on
different pages, `core.js?v=5` on index.html is stale.

### D6 scripts/ layout and coupling

`pb_split` (11 importers, four folders) and `tei_xml_utils` (8 importers, two folders)
are generic libraries filed under `tei/`; the entity layer (15 modules, 8266 lines) is
spread over `tei/`, `eval/`, `edition/` and causes 11 of the 20 edges of the `eval↔tei`
cycle; `tei_add_revision.py` writes the abolished screening `revisionDesc` that
`tei_status_marker` strips (E66), has no importer, no test, no CLI entry, and shadows
`TEI_FINAL_DIR` with a local constant; `evaluate_ocr.compute_proxy_quality` reads
`_review.json` files that do not exist (0 on disk) and its two call sites in
`benchmark_cer.py` are dead; `tei_footnote_demote`/`tei_footnote_marker_strip` import a
private symbol from the mirror generator; `tei_char_normalize` imports a private regex
from `char_lint_audit`; `layout/__init__.py` imports PIL at package level;
`ocr_pipeline --engine auto` resolves to the dead Mistral endpoint (the Mistral code path
itself is the reproducibility record of the delivered corpus and stays); `classify_docs`
is a live one-shot cache generator missing from the CLI reference.

### D7 Duplicated helpers

`_ascii` in ten scripts, `pb_offsets`/`page_of` in three, `_parse_doc_ids`,
`facsimile_path`, `_sorted_counts`, `_find_open`, `split_paragraphs`, `get_client`
(Gemini client in three files), `_read_json` against the existing `utils.load_json`,
`discover_doc_ids` shadowing `utils.discover_doc_ids`; nine hand-rolled `sys.path`
bootstraps in two variants; 26 re-derived `output/` path literals although `config`
exports the constants; two competing `.env` loaders (`config` via dotenv, `utils.load_env`
by hand) plus three redundant `load_dotenv()` calls; `generate_entity_overview.py:51` uses a
CWD-relative path; `quality_proxy` instantiates two spell checkers at import time.

### D8 Ruff families

25 RUF001/RUF003 hits are domain strings (hyphen classes, NBSP variants, apostrophe
target, corpus fixtures) and become per-file ignores; 12 E402 are warning filters and env
vars that must precede heavy SDK imports; 178 are safe auto-fixes; UP031 (48, three
files) and B905 (10) need per-site decisions; RUF013 (10) is annotation only; the dead-
code families (F401/F841/RUF059/B007, 48) need two inspections (`corpus_audit.py:425`,
`tei_step3.py:557`).

### D9 Tests and tooling

26 scripts are imported by no test; the sharpest gaps are the pure transforms
`page_xml_generator`, `mets_generator`, `audit_common`, `running_heads`, and the
tei_final writers `tei_blank_marker` (and `tei_add_revision`, to be deleted); the single
skip in `test_body_note_demote.py:202` is a stale case kept alive after E94; `HAS_LXML`
skip guards mask a broken install although lxml is mandatory; `openpyxl` is imported by
`corpus_audit` but undeclared; `pyproject.toml` declares no dependencies, there is no
`uv.lock`, no pre-commit, no ruff step in CI, ruff itself is unpinned; no `conftest.py`,
synthetic TEI builders are re-declared per test module.

### D10 Frontend

viewer.js mixes seven concerns in 1976 lines; index.html issues 286 requests on load
(catalog plus one manifest per document); entities.html loads 796 KB eagerly and
re-implements `el` and `fold` because it does not load `core.js`; catalog search does no
diacritic folding; the three dropdowns declare `role="menu"` without arrow-key
navigation; the FSA modal is hand-rolled instead of `<dialog>`; no skip links, no
`prefers-reduced-motion`; twelve German strings in the English viewer; the entity popover
drops `@resp/@cert/@source` (E118); OpenSeadragon is loaded from a CDN without SRI and
Google Fonts on every page without a privacy note; seven dead CSS rules, two dead `core.js`
exports; component CSS is token-clean and accent-on-surface-clean.

## Work packages

Each package names its exclusive file set, so packages of the same wave never touch the
same file. "Owner" is the responsibility an agent receives verbatim; the orchestrator
verifies every self-report against disk before anything counts. No agent commits.

### WP0 Immediate corrections (no structural decision involved)

WP0a, documentation freshness. Files: all of D1 and D3 except arbeitsbericht-v3.md;
README.md; CLAUDE.md (`--policy` sentence, `legacy_mentions.json`, `classify_docs` in the
CLI reference); scripts/README.md; docs/methode.html (eight figures and the date from
`docs/data/cer_statistics.json`); docs/about.html (two gaps); frontmatter for
entity-evaluation.md and agent-orchestration.md. Acceptance: every corrected statement
cites its source of truth in the commit body; all Markdown links resolve; no new volatile
figure outside exempt documents.

WP0b, code quick fixes. Files: `pyproject.toml` (per-file ignores with reason comments),
ruff safe auto-fix over `scripts/` and `tests/`, `scripts/edition/generate_entity_overview.py`
(absolute path), `requirements.txt` (`openpyxl`), `scripts/utils.py` and the three
`load_dotenv()` callers (one `.env` mechanism via `scripts.config`),
`scripts/eval/evaluate_ocr.py` and `scripts/eval/benchmark_cer.py` (remove
`compute_proxy_quality` and its call sites), delete `scripts/tei/tei_add_revision.py` and
its two knowledge references (methodology.md, workflow.md). Acceptance: full suite green
after every step, ruff count only falls, no behaviour change (mirror regeneration
byte-identical, see Verification).

### WP1 Knowledge ownership (two agents, disjoint)

WP1a: methodology.md, specification.md, project.md, index.md. Resolve D2 items owned or
duplicated there (strip the command blocks and the screening story from methodology,
shrink the CER detail in specification to the requirement, add the R-ENTITY line, move
the validator tally to a cross-reference, add the entity concepts and the E99 reading of
W19 to index, qualify the CER extraction-rule namespace against the decision namespace,
record the frontmatter exception rule or drop it). WP1b: pipeline.md, workflow.md,
infrastructure.md, ground-truth-map.md, cer-methodology.md, literature-comparison.md
(pipeline hands the reference frequencies to ground-truth-map and the status semantics to
workflow, keeps the `revisionDesc` XML shape; workflow is rewritten to the E107 viewer
with four streams and the entities layer; `--reassemble` semantics get one owner).
Acceptance: each duplicated fact has exactly one location and cross-references elsewhere;
the dependency map in index.md matches; links resolve.

### WP2 reports/ and docs/ artifacts (one agent)

Secure unique content, then delete per D4; merge the two entity papers into the
2026-08-21 paper and move its measured figures into entity-integration.md and
entity-evaluation.md; move ecosystem-synthesis.md to `reports/` with an index pointer; move
`docs/folien-entitaetsannotation.html` out of `docs/` (to `reports/` as a dated artifact)
unless the operator links it; update every referrer (README, index, decisions E107/E90/E99
lines keep their historical references with the deletion commit named). Files: `reports/`,
`docs/folien-entitaetsannotation.html`, entity-integration.md, entity-evaluation.md,
index.md pointer line only (coordinate with WP1a, which owns the rest of index.md; WP2 adds
one line after WP1a has finished, or WP1a adds the line on WP2's behalf).

### WP3 Code hygiene, non-entity tree (one agent)

Ruff steps 3 to 8 of the audit procedure over ocr/, layout/, edition/, core/, the
non-entity parts of eval/ and tei/, one commit per family; path constants from `config`
(D7); Gemini client creation in one place; lxml skip guards turned into hard imports;
the stale skip in `test_body_note_demote.py` rebuilt on a synthetic fixture or removed.
Tests first for `page_xml_generator`, `mets_generator`, `audit_common`, `running_heads`
before their format strings change. Acceptance: suite green after every family, ruff count
per folder falls to zero outside the entity layer, per-site B905 decisions in the commit
body.

### WP4 scripts/ layout (one agent, runs after WP1, WP2, WP3)

Move `tei/pb_split.py` and `tei/tei_xml_utils.py` to `scripts/core/` (zero commands
change); create `scripts/entity/` with the fifteen entity modules (basenames may keep or
drop the `entity_` prefix, decide once); update every import, every test, the 15 affected
CLAUDE.md commands, scripts/README.md, the knowledge instrument lists, and the JS/HTML
mentions; move the body of `layout/__init__.py` to `layout/overlay.py`; make the private
cross-imports public in their owning module (`_extract_pages_from_final`,
`_APOSTROPHE_RE`); `ocr_pipeline --engine auto` resolves to gemini. Acceptance:
`test_scripts_health` green, every CLAUDE.md command resolves with its flags, the corpus
scan and the previews regenerate byte-identically, entity battery green.

### WP5 Journal (one agent, parallel to WP4)

Condense sessions 69 to 96 to one line each in the archive block; move the long entries
unchanged into `knowledge/journal-archive.md` with a link from the journal header and back;
write the stricter entry template (fields, tense, length cap, decision reference
mandatory); leave sessions 1 to 68 untouched. Files: journal.md, journal-archive.md
(new), CLAUDE.md workflow rule 1 (one sentence).

### WP6 Frontend (one agent, parallel to WP4)

In priority order of the audit: `?v=` hygiene (one tokens version on all pages, core.js
bump); restore the Entities link on impressum.html and viewer.html; generate
`manifest_index.json` and drop the 285 manifest fetches; load `core.js` on entities.html,
promote `fold` into core.js and use it in catalog search; translate the twelve German
strings; show `@resp/@cert/@source` in the entity popover; dropdown arrow keys, native
`<dialog>`, skip links, `prefers-reduced-motion`; delete the seven dead CSS rules and the
two dead `core.js` exports; viewer.js split into the six modules around `ZBZ.Viewer.state`
and `ZBZ.bus` with a load-order check. Operator-gated inside WP6: vendoring OpenSeadragon
and the fonts (licensing and size), and the privacy section on impressum.html. Acceptance:
every page loads via `http.server` without console errors, the feature checklist of the
audit passes, asset versions bumped on every changed asset.

### WP7 Shared helpers and tooling (one agent, after WP4)

Bundle `_ascii`, `pb_offsets`/`page_of`, `_parse_doc_ids`, `facsimile_path`,
`_sorted_counts`, `split_paragraphs` into `audit_common` / `core` as mapped in D7; replace
`_read_json` variants with `utils.load_json`; one `sys.path` bootstrap form or none where
CLAUDE.md documents only `-m`; `conftest.py` with the shared synthetic TEI builders; ruff
pinned and wired into CI; `requirements.txt` migrated into `pyproject.toml` with `uv.lock`
and a pre-commit hook. Acceptance: suite green, ruff zero, CI runs both gates.

### WP8 Test suite strengthening (one agent, wave 3, after WP4 and WP7)

Findings of the test-quality audit of 2026-08-21: the suite is dominated by behaviour
contracts on synthetic input and frozen corpus regressions, assertion density is healthy,
tautological tests are marginal. Three weaknesses: about two fifths of the tests are
parametrized over the gitignored delivered corpus and vanish on a fresh clone, so the CI
signal is far weaker than the local one and the validator rules R1 to R7 and W1 to W18
are covered only through that vanishing layer; the TEI generator itself (`tei_step1` end
to end, `tei_step2`, most of `tei_step3` including `assemble_document` and
`_fix_post_assembly_schema`) is the least-tested part while it produces the deliverable;
two guards are pinned on one side only (`COVER_FIELD_MIN` upward, the two-sided p-value
doubling in `paired_bootstrap_diff`). Package content, in value order:

1. Synthetic end-to-end contract for step 1 plus assembly: a two-page fixture (OCR
   markdown and layout JSON under `tmp_path`, loader dirs monkeypatched, no Gemini)
   asserting `pb` numbering, region-to-paragraph mapping, facsimile zones and RelaxNG
   validity of the assembled document.
2. Direct unit tests for `tei_validator` rules R1 to R7 and W1 to W18, one firing fixture
   and one silent counter-fixture each, in the parametrized style of
   `test_zbz_conformity.py`.
3. `page_manifest.detect_blanks` and `tei_blank_marker` contract and idempotence test (the
   only `marker_common` consumer without one).
4. Mutation-revealed pins: `COVER_FIELD_MIN` upper side, two-sided p-value doubling.
5. Fix the weakest tests: `test_cer_statistics.py` block-concatenation test asserts whole
   blocks; `test_reassemble_preview.py` is deleted with the script (WP3); the
   `zfill` re-implementation in `test_page_names.py` is deleted; the constant pins in
   `test_workflow_status.py` become one test that the status tokens agree between
   `page_manifest`, `tei_status_marker` and `docs/assets/js/*.js`.
6. `conftest.py` with the shared builders (TEI skeleton, delivery header, bbox, entity
   lexicon and record builders, session `final_docs`) replacing the thirteen `_tei`
   builders and the near-verbatim lexicon fixtures; `requires_corpus` and
   `requires_mirror` as named markers so the clone blind spot is visible via `-m`.
7. Catalog document-field contract pinned against the keys `catalog.js` reads; CER
   extraction rules indexed to the E1 to E12 catalog with the missing direct tests
   (whitespace collapsing, markup stripping, `lb break="no"` de-hyphenation, `fw`
   exclusion, blank pages).
8. `tei_step2.fix_gemini_tei` repair path on synthetic malformed Gemini output.

Acceptance: suite green, the clone-safe subset (`-m "not requires_corpus"`) covers the
validator rules and the generator contract, no test writes outside `tmp_path`.

## Waves and parallelism

| Wave | Packages | Agents | Precondition |
|---|---|---|---|
| 0 | WP0a, WP0b | 2 | none |
| 1 | WP1a, WP1b, WP2, WP3 | 4 | wave 0 committed |
| 2 | WP4, WP5, WP6 | 3 | wave 1 committed |
| 3 | WP7, WP8 | 2 | wave 2 committed |

Every build agent runs on Opus with its file set and the guardrails passed verbatim (no
commits, no pushes, no subagents, no `.env`, no `arbeitsbericht-v3.md`, no writes outside
the file set, Grokipedia never). After every wave two verification agents run, one over
code and one over documents; their checklist is below. Commits happen per wave after
verification, staged by explicit path, one coherent commit per package or family.

## Verification per wave

Code verifier: full pytest suite (count must not fall below baseline minus deliberately
removed tests, which the agent lists); `ruff check scripts tests --statistics` (count must
not rise); `tests/test_scripts_health.py`; every `python -m` command and flag in CLAUDE.md
resolves (the programmatic check of the README audit, reused); mirror regeneration
`generate_edition_data --mirror-only` leaves `docs/data/` with an empty git diff; for WP4
additionally `entity_corpus_scan` and `tei_entity_preview --all` reproduce the pre-wave
JSON and XML byte-identically (hashes recorded before the wave). Document verifier: every
relative Markdown link in README, CLAUDE.md, knowledge/, reports/ resolves; the
single-source list of D2 shows one owner per fact; no third-party personal names; no new
volatile quantity outside exempt documents; the four writing prohibitions; index.md table
and dependency map match the file set; frontmatter present on every knowledge document.
The orchestrator reads both reports, spot-checks at least three claims per report against
the disk, and only then commits.

## Operator decisions still open

1. Fate of `folien-entitaetsannotation.html`: link it or move it out of `docs/`.
2. Vendoring OpenSeadragon and the fonts, and the privacy section (WP6).
3. `scripts/entity/` basenames with or without the `entity_` prefix (WP4, one-time).
4. Whether `2026-08-12_viewer-ui-analyse.md` is deleted after the open quick wins are
   decided in WP6.
5. B905 per-site choices are made by WP3 and recorded; the operator reviews the commit body.

## Additions after wave 0

- WP1a also aligns the bootstrap-method claims with the computed method: the generator
  `cer_statistics_full` emits percentile intervals throughout and never calls `bca_ci`,
  while CLAUDE.md (two command comments), index.md (E54 row), specification.md (quality
  section), methodology.md (test comment) and the JSON field `meta.bootstrap_method` say
  BCa. Either the label moves to percentile everywhere, or the generator is switched to
  BCa and the statistics regenerated; the decision is the operator's, the default is the
  label.
- WP1a corrects the CLAUDE.md heading "M0-M4 reached" to the state entity-integration.md
  records (M0-M3 reached, M4 instrument built, frozen-rules run pending).

## Execution record

Wave 0 executed and verified on 2026-08-21 (E120): tests 2149 passed and 1 skipped,
ruff 147, all commands resolve, mirror diff empty. Deleted: `scripts/tei/tei_add_revision.py`
(last carried by 03c478d1).

Wave 1 executed and verified on 2026-08-21 (E121): tests 2204 passed and 0 skipped, ruff
0, all commands resolve, mirror diff empty, benchmark hash identical, 285/285 valid, all
links resolve. Deleted: `scripts/tei/tei_reassemble_preview.py`, `tests/test_reassemble_preview.py`,
four reports (last carried by f6eba697). Moved: ecosystem synthesis and slide deck to
`reports/`. WP1a, WP1b, WP2, WP3 closed.

Wave 2 executed and verified on 2026-08-21 (E122): WP4 (seventeen modules into `scripts/entity/`,
two into `scripts/core/`, basenames kept), WP5 (journal archive, template v0.3), WP6 (frontend,
vendoring), bootstrap label percentile with regenerated statistics. 2212 tests, ruff 0, anchors
identical, headless-browser check clean. WP4, WP5, WP6 closed.

## Homeless findings from the deleted 2026-07-07 verification report (operator decision)

WP2 deleted `reports/2026-07-07_verifikation-berichtsfragen.md` after tracing every finding;
five diagnosis findings have no owner document yet and are recorded here until the operator
assigns or drops them.

- B4: of the five content error classes, class 3 (title-page and library-apparatus text
  landing in running text) has no corpus-wide check, and classes 3 and 4 are invisible to
  the schema plus W-rule layer. Candidate owner: specification.md quality method.
- C8: double-page signals are the aspect ratio from the layout JSON and the two-half
  instruction of the type-D prompt; the removed `page_ratio >= 1.5` heuristic (E73) is
  documented as ineffective; the Masterfile was never checked for a double-page field.
  Candidate owner: pipeline.md.
- D9: Transkribus PAGE-XML is usable as layout ground truth after normalization (absolute
  pixel polygons versus percent bboxes; PAGE structure types versus project labels), so a
  geometric IoU comparison is feasible and a type check needs a mapping table. Candidate
  owner: pipeline.md.
- D11: `compute_page_quality` derives an area-coverage value per page and the auto mode
  re-detects below a threshold, but only the Gemini score is persisted. Candidate owner:
  pipeline.md (routing paragraph).
- F15: the teiCrafter handover is a manual file open without an export or import bridge.
  Candidate owner: workflow.md.

## Register and closure

Each wave receives one decision entry (E120 onward) naming the packages, the deletions
with the last carrying commit, and the verification results. At closure this plan is
deleted and index.md drops the pointer; the journal entries of the sessions carry the
course.
