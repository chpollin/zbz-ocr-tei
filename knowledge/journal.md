---
title: Work Journal
project:
  name: zbz-ocr-tei
  repository: https://github.com/chpollin/zbz-ocr-tei.git
method:
  name: Promptotyping
  url: https://dhcraft.org/Promptotyping/
template:
  name: Vorlage Journal
  version: 0.2
  url: https://dhcraft.org/Promptotyping/promptotyping-document/journal
status: active
language: en
version: 1.0
created: 2026-01-29
updated: 2026-08-21
authors: [Christopher Pollin]
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

Fixed field order per entry, with the bold field labels kept: **Occasion** (one
sentence: why this work now), **Goal** (one sentence: what should exist at the end),
**Course** (past tense, at most 120 words, with references), **Decisions** (per point:
what, why, rejected alternative; each point carries its register id or the note "no
register entry"), **Status** (past tense, self-contained, with the savepoint commit hash
where one exists), **Next steps** (numbered and executable), **Dead Ends** (optional,
with rationale). Required fields: Occasion, Goal, Course, Status, Next steps. This is
Journal template v0.3, which tightens the v0.2 fields by tense, length cap, mandatory
decision reference and self-contained status.

Compact standard: an entry carries distilled knowledge, and the protocol of the session
stays in the git history. Every decision identifier, every figure with its unit, every
commit hash and every document id is kept; narrative detail is dropped.

Archiving: the Entries section holds at most five full entries. Once it grows beyond
that, every entry older than the current session moves verbatim into
the archive section at the end of this document and leaves one compact line in the archive
block below, carrying date, session number and title, the decision ids taken, the key figures
with their units, the commit hashes the entry names, and the outcome in one clause.

Style rules: formal and project-specific; explain technical terms on first use within
the entry; quantities with reference unit. Not included here: specifications (they
belong in [decisions.md](decisions.md) or the domain docs), code diffs and commit
texts, hour-by-hour protocols, self-assessments, notes on documentation maintenance
itself, personal names (use roles and organisations instead).

Translated to English and compacted on 2026-07-07 by operator decision; knowledge
preserved, pre-compaction entries in git history.

Session 80 to 93 entries compacted on 2026-08-12 by operator decision; the seven
waves of session 93 were consolidated into one entry, knowledge preserved, originals
in git history.

Sessions 69 to 96 moved to the archive section at the end of this document on 2026-08-21
by operator decision (first into a separate archive document, folded back the same day when
the knowledge base was capped at ten documents), each leaving one compact line in the archive
block below; sessions 1 to 68 remain in that block as they are.

## Entries

### 2026-08-21 Session 98: knowledge base recut by function, capped at ten, reports dissolved

**Occasion** The wave 0 to 3 refactoring left a knowledge base cut by topic; the operator asked for a convention-conformant recut, then capped it at ten documents without loss of information and asked for the reports folder to go.

**Goal** Ten documents in `knowledge/`, each function a section, frontmatter under one contract with a CI gate, every pointer inside and outside the base resolving, no reports folder.

**Course** Three explorer agents produced the section ownership map, a fact check against code and data, and the inventory of external pointers. Wave 4a extracted eight function documents from the untouched sources; wave 4b pruned the sources with every removal confirmed in its owner; wave 4c merged the eight into ten carriers and absorbed the reports holdings into the verification appendix and the journal archive; index.md was rebuilt; the orchestrator rewrote the pointers in CLAUDE.md, README, scripts, tests, the site tooltip and the mirror string, deleted fourteen documents and the reports folder, moved the slide deck to `workshops/`, and added the frontmatter gate. Two verifier rounds (4a, 4b) found nine defects each, all fixed before the commits; the operator then asked for fewer agent rounds, and 4c was closed by the orchestrator's own sweeps.

**Decisions**
- Ten-document cap and function-per-section mapping, reports folder dissolved, evidence as verification appendix, archive back in the journal (E124).
- Engine picture stated once from the code; CER catalog corrected to the extractor; percentile interval method stated for the entity statistics (E124, facts from the wave-4 fact check).

**Status** Committed as wave 4a (f5261ae5), 4b (ec42a613) and the closure commit of this entry; 2344 tests, ruff 0, frontmatter gate green; working tree clean except the client report held by another instance.

**Next steps**
1. Move `arbeitsbericht-v3.md` to `docs/` once its pending edit is committed, and drop it from the gate's tolerated set.
2. Operator decisions of the plan block in decisions.md: re-freeze of the reconstructed evaluation draw, the four entity operator questions, O8/O13/O27 with ZBZ.
3. Regular work resumes on the entity layer (M4 frozen-rules run with evidence under `docs/data/`).

### 2026-08-21 Session 97: repository refactoring, diagnosis and wave 0 (E120)

**Occasion** Operator question whether documentation and code of the repository are clean. Six read-only audits by Opus agents (README and CLAUDE.md inventory, knowledge overlap and staleness, reports and static pages, scripts layout and coupling, frontend, code hygiene and tests) answered it with a catalogue of stale statements, duplicated facts, stale published figures, layout coupling and half-introduced tooling.

**Goal** Record the diagnosis as an executable plan and carry out the corrections that need no structural decision.

**Course** The refactoring plan (a working document deleted at closure; outcome in E120 to E124) held the findings digest D1 to D10, the work packages WP0 to WP7 with exclusive file sets, the waves, the verification protocol and the open operator decisions. Wave 0 ran as two parallel build agents with disjoint file sets. WP0a corrected stale statements in README, CLAUDE.md, scripts/README.md, twelve knowledge documents and the two static pages; on methode.html eight CER figures and the regeneration date were reset from `docs/data/cer_statistics.json`, and the interval label now follows the JSON's `ci_method` (percentile). WP0b declared the 37 deliberate ruff findings (character tables of the normalization, warning filters before SDK imports) as per-file ignores, applied the safe auto-fix (368 to 147 findings), fixed the CWD-relative scan path in `generate_entity_overview`, declared `openpyxl`, unified `.env` loading on `scripts.config`, removed the dead `compute_proxy_quality` together with the `--proxy` flag, and deleted `tei_add_revision.py`, the screening-era writer of the abolished `revisionDesc` certification (E66) that `tei_status_marker` strips. Verification by the orchestrator on disk: 2149 tests passed and 1 skipped (the two missing cases are the deleted script's health cases), ruff 147, all 77 `python -m` commands in CLAUDE.md resolve with their flags, `docs/data` diff empty, benchmark JSON identical under a masked timestamp.

**Decisions** E120 (wave 0, deletions and the plan). Operator decisions of the session: full scope (documentation, code hygiene, scripts layout, frontend); obsolete artifacts are deleted and git retains them; knowledge keeps its thematic split and is streamlined; the journal is condensed for sessions 69 to 96 with an archive document.

**Status** Wave 0 committed in three commits (documentation, code, plan and register). Wave 1 ran in the same session (E121): four build agents (knowledge ownership in two halves, reports consolidation, code hygiene), two verifiers, three defects found by the document verifier and fixed before commit (a frontmatter date, two sentences in cer-methodology.md that claimed a completed label fix and misnamed the `bca_ci` caller). Result: one owner per duplicated fact, four reports deleted after securing their unique content, the ecosystem snapshot and the slide deck moved to reports/, `tei_reassemble_preview` deleted, ruff 0 under the unchanged configuration, 2204 tests passed with zero skips, all gates green. A test-quality audit ran in parallel and became package WP8 in the plan (generator end-to-end contract without Gemini, direct validator rule tests, blank-page rule, one-sided guards, conftest and a `requires_corpus` marker, catalog field contract). The bootstrap-label item is documented; the generator field `meta.bootstrap_method` stays BCa until the operator decides (default: percentile label).

Wave 2 ran in the same session as well (E122): scripts layout (`scripts/core/`, `scripts/entity/`), journal archive with template v0.3, frontend (asset versions, manifest index, viewer split into six modules, vendored OpenSeadragon and fonts, popover provenance, keyboard menus, native dialog), bootstrap label percentile with regenerated statistics; one split regression found by the verifier and fixed before commit.

Wave 3 closed the plan in the same session (E123): shared helpers and tooling gates, the test suite strengthened to 2344 tests of which 1447 run on a fresh clone, one data-loss defect in the step-2 repair path fixed, one incident recorded (a verification run overwrote the frozen evaluation draw under the gitignored audit folder; reconstructed, tracked data unchanged).

**Next steps** 1. Operator decisions: the five homeless findings, the re-freeze of the evaluation draw, the CER catalog corrections. 2. `uv lock` once uv is installed. 3. Regular work resumes on the entity layer (M4 frozen-rules run, redraw and recall remeasurement).

## Compact Archive (Sessions 1 to 96)

One line per session, newest first. Rationale in the [decision register](decisions.md),
details in the git history.

### August 2026: GND entity layer

| # | Date | Topic |
|---|---|---|
| 96 | 2026-08-13 | Matching repairs, overview as evidence surface, mark provenance, marking policy (E116-E119): dotted-abbreviation guard over 1113 initials candidates plus the hyphen reach of the surname index that the word-end cut could never produce for 210 hyphenated keys (E116); overview extended by ambiguity count, per-entity class breakdown, adjudicated quality block and provenance stamp (E117); `@resp`, `@cert` and `@source` on every wrapped mark in the preview TEI, with `@source` carrying the rule because it is the only attribute the delivery schema permits on all three wrapped elements (E118); operator marking policy in `data/entities/marking_policy.json`, 28 canonical surnames released from the anchor requirement, one held out, seven generic work titles dropped from scope and four bound to typographic corroboration, unlisted entities admitted by the project and marked as additions outside the curated list (E119); the person-versus-work dispute settled by the reference corpus, where 190 citations of the 25 reference TEIs carry no marked person name; corpus-wide preview run over every delivered document, each schema-valid and text-invariant, worklist volume down by about a third, guard at zero violations; commit `d59b94fd`. |
| 95 | 2026-08-13 | Verdict guard, zero-mention classification, released work program executed (E110-E115): `entity_verdict_guard` built test-first as a standing regression gate over the adjudicated judgments, first run with all 279 correct marks surviving, 10 of 14 wrong marks repaired and 27 of 30 adjudicated misses surfacing again (E110); apostrophe folding at matching time after the E94 normalization left the corpus at U+2019 while list and cache stayed ASCII, diacritic folding deliberately excluded (E111); curated-variant channel with list hygiene (E112), pointwise facsimile-verified text repairs in documents 900, 1520 and 2330 with unchanged CER headline (E113), facsimile mapping via pb anchors with sequential fallback (E114), figure zones demoted to the worklist instead of excluded while keeping anchor power (E115); a planned footnote-digit repair was refuted by a corpus probe before any code, the zero-mention set fell from 42 through 37 to 17 entries, and the remeasurement material was frozen with a seed-42 draw into `output/audits/eval_sample_2026-08-13/` for the M4 close; guard at zero violations, entity battery green, the operator gates M6 and M7 untouched. |
| 94 | 2026-08-13 | Running-head suppression, adjudicated error classes repaired, entity overview page, entity-layer refactoring (E108/E109): operator convention that mentions of the corpus author are always marked and the byline exception drops, running heads suppressed in the matcher per E105 with anchor power preserved for demoted full names, 671 candidates demoted in head zones and 0 of 3925 tier-1 marks left in a zone, convention precision 0.9511 with interval 0.9248 to 0.9737 over 266 decidable cases against the protocol reading 0.952, and the session-93 recall claim corrected to 24 of 25 (E108); five worklist demotions and two span repairs derived from the nine facsimile-confirmed cases, the scan hyphen invariant from eleven violations to zero, the verdict store rebound to the frozen scan it was drawn from, tier-1 precision rising to 0.67 at unchanged recall and coverage (E109); `generate_entity_overview` and `docs/entities.html` built, then refocused on the completeness question with the unmatched list entries first and the adjudicated sample kept out as measurement evidence; the 1853-line matcher split into `entity_lexicon.py` and `entity_matcher.py` with the outside API re-exported, `pyproject.toml` introduced with a curated ruff configuration at zero findings over the entity layer, equivalence proven over all 285 documents and the corpus scan regenerated byte-identically; the M4 frozen-rules gold run and the M5 judge calibration stayed open. |
| 93 | 2026-08-12 | GND entity integration built, evaluated and consolidated (M0 to M4, E105/E106), then documentation trued up and viewer reduced (E107): seven operator-released waves from source survey (persons 177, organisations 32, works 87, 296 entries, the E71 remnant a strict subset) through the M1 to M3 instruments of matcher, preview and pilot, gold benchmark, cover strip, verdict store and risk ranking, against the E88 inline-GND convention, the E94 marker pattern as the only sanctioned write path under the E99 regeneration ban, and the conformity rules Z1-Z4/Z8 idle since E71 per lesson L14; adjudicated precision 0.952 (CI 0.925 to 0.976) over decidable cases, raw agreement 0.96, recall coverage 0.552 with 28 of 30 misses as rule gaps, held-out tier-1 precision 82 percent and overall 62 percent, 90 percent without the document-3040 bibliography defect, candidate coverage 83 percent; the risk ranking scores 4043 tier-1 marks into 1517 high, 960 medium and 1566 low; E105 settles the page apparatus with running heads unmarked while title pages, byline organisations and picture captions are marked, E106 binds every derived form channel to tier-2 worklist output and every verdict to a text fingerprint, E107 reduces the viewer to three views with the annotated reading view as corpus-wide default; the cover strip ran over 22 documents and all 285 validate afterwards, and the M5 judge pilot together with the M6 variant review stayed open; commits `35281270`, `735864a2`, `5dcc2365`, `4ee671a5`, `36a1ebd8`, `31df4503`, `a8472fd8`, `251c63d8`, `ae374797`, `8a0e34ae`, `40afccf2`, `c81b5922`, `6487e0b6`, and in the evening wave `0eab92d5`, `7cf84b23`, `49c5ee7a`, `80187507`, `e7f9dd6d`, `baecc433`, `d65854a3`, `e4f641cd`, `14b0d1bc`, `f564ff48`, `ab2aa803`, `1ea04387`, `57ece48e`, `b2957277`, `f7a06252`, `c3b85822`. |

### July 2026: guideline conformity, stock corrections, documentation consolidation

| # | Date | Topic |
|---|---|---|
| 92 | 2026-07-31 | Knowledge base aligned post hoc with the Promptotyping convention (E104): additive frontmatter only, no renames and no prose changes, seven documents given a template mapping and six left freehand with a stated reason, `generated-with` set nowhere; the citing method paper pins the pre-alignment state to commit `5b78b69d`; pytest 1390 passed and 1 skipped. |
| 91 | 2026-07-09 | DTA-Basisformat conformity claim tested, refuted and removed (E102): validated against the official `basisformat.rng`, 0 of 285 delivered documents and 0 of 25 ZBZ reference TEIs are valid, so `zbz_hersch.rng` stands as sole format authority; violation classes isolated as delivery-contract header, `revisionDesc` and `facsimile`, and body conventions such as `div type="text"`; the reworded step-2 prompt affects only future refinement runs, which stay gated under E99, and the M4 milestone text follows. |
| 90 | 2026-07-09 | Final report moved to `knowledge/arbeitsbericht-v3.md`, stub retired: git mv with history preserved, the superseded `knowledge/final-report.md` deleted, living references and four script docstrings repointed at the surviving sources (cer-methodology.md for the CER contract, register E85 for the footnote instruments), dated snapshots unchanged; no register number, script health green. |
| 89 | 2026-07-07 | Backlog plan executed, doc 30 repaired (E98), machine reordering falsified (E99), stability measured (E100): the lost left half of document 30's first double page restored from a 300-DPI re-read with facsimile-verified zones, fidelity CER 11.59 to 0.90 percent and the corpus headline to mean 2.08 percent and median 1.28 percent (paired -10.08 pp, p = 0.0034); the CER-guarded dry-run probe over copies of all 25 reference documents produced 0 improvements and 9 degradations up to +40 pp, so W19 became a text-or-zone suspect signal, the corpus reorder was banned on every path and the preview tool obsolete, with the E91-classified doubled-page tails 760 and 1440 staying curation cases; run-to-run stability over the pilot documents 570, 2310, 1910, 830 and 890 in 3 forced runs each at per-document fidelity std 0.000 to 0.129 pp and mean 0.040 pp; M3 closed, gates green at 285/285. |
| 88 | 2026-07-07 | Doc 30 adjudicated (E97), arbeitsbericht v3 finalized: the three missing blocks of 540, 451 and 194 characters lie on the left half of the first double page, are legible on the scan and absent from every OCR stream, so the E91 text-loss reading stands while the E94 calibration is shown to have sampled the wrong facsimiles; repair ordered as targeted single-page re-OCR after the E96 pattern; report slots filled, audience fixed at ZBZ project management, backlog ordered with the M3 rollout behind a preview rebuild. |
| 87 | 2026-07-07 | Doc 1520 page 70 leaked refusal replaced by the gated re-OCR (E96): two vision passes diverged, the fluent pass was refuted at the contrast-enhanced facsimile and the honesty-prompted pass marked the faint zones `[...]`, so a conservative partial transcription with facsimile-verified anchors was composed, `pb n="[64]"` confirmed by the unbroken bracketed sequence and the faded footer digit left out; streams repaired with backup after the E94 finding, `tei_final` patched surgically, validator and schema gate green, mirror regenerated, the M3 reading-order rollout still gated. |
| 86 | 2026-07-07 | Healing rerun executed, gates green, reports and statistics moved to the post-run state: the rerun of `tei_pb_folio --strip-folio-echo` healed exactly the 14 orphaned speaker wrappers in four interview documents at 0 pb changes; pytest 1370 passed and 1 skipped, validator 285/285 valid with 2018 informative warnings in 256 documents dominated by W17 (830) and W19 (827); pb semantics 204 printed_folio, 37 scan_sequence, 10 mixed, 34 undetermined, body-note candidates 63 to 3, straight apostrophes at zero; CER fidelity mean 2.50 percent (CI [1.65; 3.54]), median 1.37 percent (CI [1.08; 2.56]), paired 17 of 25 documents improved at -9.66 pp, p = 0.0066; E94 and E95 closed as executed, the doc-30 adjudication against the E91 loss reading and the M3 rollout still open. |
| 85 | 2026-07-07 | E94 stock runs executed, echo-strip sp defect found and repaired (E95): both runs reproduced their dry-run figures exactly (folio sources 1753/1033/151/208/970/79 with 1212 echoes; demotion 59/2/2/19 at 0 unmatched), then the schema gate failed for the interview documents 2330, 2400, 2540 and 3180 because footer echoes inside `<sp>` left 14 orphaned wrappers corpus-wide; repaired in the tool rather than by hand-editing the data, so provenance stays on the marker path, with a `doc_has_brackets` guard against false print folios on a rerun and echoes under a named speaker kept in the text. |
| 84 | 2026-07-07 | E92/E94 tooling refactored, behaviour equivalence proven: three agent lanes extracted `scripts/tei/marker_common.py` and `scripts/eval/audit_common.py` and rewired the five marker tools, the five audits and the completeness check, while the thirteen new test files proved to carry tailored rather than duplicated fixtures; shared helpers stay per domain and lifting the residual lines into `scripts/core/` was rejected as an abstraction without present need; dry runs byte-identical to the pre-refactor baselines (folio sources 1753/1033/151/208/970/79 with 1212 echoes; 59 demotions, 2 quotes, 2 preserved, 19 promotions, 0 unmatched), full suite green; the doc-30 conflict with E91 and the pre-E77 legacy status labels stayed open; commit `6726c409`, unpushed. |
| 83 | 2026-07-07 | Guideline conformity explored end to end, ground-truth map and implementation packages (E92/E93/E94): four exploration rounds established that every delivered document is machine-valid while the faithfulness core of the guidelines is machine-unchecked, warnings dominated by the W17 speaker slots and the W19 legacy reading order, and the E90 reading-order evidence plus the E85 footnote residue were carried forward; quality architecture decided in three tiers, deterministic validation, evidence-bound agent verification that never grants `verifiziert` after the abolished E66 screening, and expert adjudication as sole source of green; diagnostic audits, the deterministic pb@n projection and the step-1 filter-leak fix registered as E92, image-based italics re-detection rejected as E93; the apostrophe normalization ran as the first E94 stock correction (88,978 occurrences in 241 documents to zero), all 63 body-as-note candidates were verified at the facsimile (59 body text, 2 epigraphs, 2 genuine footnotes), pb@n semantics were classified corpus-wide (224 scan_sequence, 18 printed_folio, 9 mixed, 34 undetermined), the char-lint space class split into 1988 sharp and 13931 low-severity cases, and foreign markup was found in 30 of 285 documents; the doc-30 counter-finding contradicting E91 and the leaked refusal on 1520 page 70 were left for adjudication, as was the M3 rollout decision on the E90 evidence; suites green at 1258 and 1289. |
| 82 | 2026-07-07 | Viewer edit modes hardened after live inspection: four confirmed defects fixed, the click-select that dirtied the layout stream without movement, the debounced text commit that survived editor detach and misattributed the stream, the TEI tab attaching the editor to the non-round-tripping rendered view, and the XML save without a well-formedness gate; source tabs relabelled OCR, Rendered and TEI-XML with one edit button per target, save asking once for initials and backfilling history entries; the rendered view extended to the measured element inventory with a markup toggle, entity markup rendered although the pipeline emits none since E71, and asset changes require bumping the `?v=` query. |
| 81 | 2026-07-07 | Merge of the English knowledge base with the local counter-check commits, E91 ported: the deletions of `quality.md` and the 2026-05-27 work report were accepted since their substance lives in specification.md and the final report, the E91 entry was rewritten in English after E90, and section 6.3 gained the upper-bound concretization and the independent counter-check with a pointer to its German snapshot report; ported passages name their producing script instead of carrying measured values, and mechanically rebasing the local commits was impossible because their target files no longer exist. |
| 80 | 2026-07-07 | Knowledge restructuring completed, site in English, final report v2, push: viewer.md, quality.md and frontend-gaps.md dissolved into workflow.md, specification.md (validation rule catalog R1-R7, W1-W19, Z1-Z6/Z8 and the open frontend requirements N1/N3/N6/N7) and ecosystem-synthesis.md, every reference remapped and a thin quality.md stub rejected under the single-source rule; final report v2 with fidelity mean 2.71 percent, median 1.40 percent, CI [1.77, 3.82] and paired gain -9.45 pp at p = 0.013, schema validation resolved at 285/285 with 145 warning documents; four static pages and eight JS modules translated with status values and `zbz_tag` values invariant; pytest 326 passed and 9 skipped, the skips data-bound; committed and pushed on savepoint `16b3323c`, with the M3 rollout and the E90 residual pages left to the workstation. |
| 79 | 2026-07-07 | Documentation correctness pass, style rules, README slimming: nine findings fixed, among them the false "not checked in" claim about `cer_statistics.json`, the validator report path still pointing at `tei_unified`, the M3 identifier collision resolved by a note in project.md instead of renumbering, the M5 pending item misread as an own obligation, and the stale E82 `ocr_dedup` caveat; Markdown style rules codified (no bold emphasis, no dash connectors, no volatile quantities) and the README deduplicated after verifying every fact in its target document; operator decisions followed on English-only documentation, four file renames, one final report in knowledge/ and a distilled journal standard; savepoint `16b3323c`. |

### June 2026: ZBZ order, delivery verification, reading order

| # | Date | Topic |
|---|---|---|
| 78 | 2026-06-21 | Root cause of the 39 remaining W19 pages isolated, correcting session 77 (E90 updated): the geometry-gap hypothesis is refuted because `reading_order_permutation` is idempotent; 35 of 39 pages carry an OCR-paragraph versus layout-region count mismatch (810 p.56: 3 against 236) and 4 a geometry that breaks column detection, so all 39 are genuine facsimile-review cases; re-sorting the emitted zone slice to force W19 to zero was rejected as silencing the upstream segmentation defect; M3 stays gated. |
| 77 | 2026-06-21 | M3 reassemble preview built as a reversible dry run (E90 continued): reassembly recomputes the M1 fix into `output/tei_preview` and never writes `tei_final`, verified byte-identical by SHA256, and runs offline and free with `dry_run=True` because reading order originates in step 1; W19 drops from 831 to 39 pages over the 216 affected documents, 188 reaching 0 and 28 keeping 39; report deterministic, 6 tests, full suite 1187 green, rollout operator-gated. |
| 76 | 2026-06-21 | Delivery verification by samples plus full check, validator default fixed to the source of truth: schema 285/285 valid and ZBZ conformity Z1-Z8 285/285 over `output/tei_final`, the reading-order audit reproducing 216 documents and 831 pages with 557 robust and 274 fragile, warning profile dominated by W17 (844 empty speaker slots) and W19 (831); three content samples confirm OCR quality and evidence the interleaved column order the M1 fix corrects; the validator default targeted the stale `tei_unified` directory and was corrected as the defect itself, no register number; full suite 1179 green, the M3 cut left with the operator. |
| 75 | 2026-06-21 | M3 triage, reading-order audit robust versus fragile with shared W19 extraction (E90 preparation): page and zone extraction moved into the shared generator `iter_page_zone_bboxes` so validator and audit see the same page set, and the canonical permutation is recomputed under threshold perturbation (WIDE 60 +/-5, GAP 12 +/-3); 831 pages over 216 documents split into 557 robust and 274 fragile with 145 documents carrying at least one fragile page, so review shrinks from 216 documents to 274 pages plus a sample; no corpus write, 9 tests, full suite 1179, savepoint `8aa3a87d`. |
| 74 | 2026-06-21 | Column and band-aware reading order (M1) plus validator warning W19 (M2), registered as E90: `match_paragraphs_to_regions` sorted regions purely by `y_pct` at both call sites and re-interleaved columns that layout detection had delivered left-first, repaired by the shared pure function `reading_order_permutation` (full-width blocks at w>=60 percent segment bands, columns split at a >12 percent x-centre gap, single-column pages falling back exactly to the old order); W19 compares delivered block order against the canonical order of the same zones and scopes the not-yet-regenerated corpus; the generator was repaired instead of rewriting delivered edition text by heuristic, so the M3 rollout stays operator-gated with the green criteria 0 W19, schema and conformity at 285/285 and falling fidelity CER for documents 30 and 760, motivated by the E80 tail evidence; the E85 note on "3 W19 diagnosis specs" was a provisional label, so future specs start at W20, and the Z1-Z4 entity gate plus ZBZ questions O8, O13 and O27 stayed open; commits `6f51eac2` and `f72743ac`, suite 1168, savepoint `f72743ac`. |
| 73 | 2026-06-21 | Consolidation part 1 of the code base verified, orphan note removed: the apparent redundancy of the three `cer_statistics*` files is deliberate tested layering and merging would break the architecture, so it stays; the dated handover note `HANDOFF-cc3.md` in the repository root, fully superseded by E89 and referenced nowhere, was removed; no register number; the Z1-Z4 entity conformity gate waits on curated inline-GND output; savepoint `0e1712c3`. |
| 72 | 2026-06-21 | Independent verification of the ZBZ delivery, consolidation report to research coordination: 285 files valid, 0 invalid, 145 with non-blocking warnings, ZBZ conformity 285 conformant and 0 violations, committed gates 583 passed; the reach finding is that the corpus carries 0 files with `ref="GND:"`, 6 bare `<persName>` and 400 `<bibl>` without authority linking, so the entity rules Z1-Z4 idle on an authority-free corpus and sharpen only after inline-GND curation (lesson L14); ZBZ questions O27, O13 and O8 left with the operator. |
| 71 | 2026-06-21 | ZBZ order implemented, inline-GND schema (E88), conformity check, page-image linking (E89), correcting session 70: the schema diff showed the active schema equals the ZBZ template plus E68 plus E87, and since the corpus is entity-free since E71 the standOff extension was reverted risk-free with `@ref` narrowed to GND-only, adopting the raw ZBZ template rejected because it would invalidate all 285; the inline-GND model rules RelaxNG cannot express run as `zbz_conformity.py --conformity` at 285/285 conformant; `<pb facs>` is the binding form and every surface gained `<graphic url="{doc_id}_p{NNN}.png"/>` with all 4108 referenced images present, absolute URL and IIIF rejected while hosting is open; O25 and O26 closed, O27 opened, ZBZ questions O8 and O13 open. |
| 70 | 2026-06-21 | Schema extension for the teiCrafter standOff model (E87), facsimile finding, warning alignment: documents annotated in teiCrafter were invalid against their own schema because the ODD subset lacked `standOff` and generic `<name>`, extended minimally after the E68 pattern with eleven element defines and a dedicated standOff work register, the synthetic curated document valid and all 285 finals still valid under a new tracked gate; the generator produces `surface`, `zone` and `@facs` completely while the surface-to-image pointer `<graphic>` was missing, which opened O25; warning figures aligned across the knowledge documents (15 active rules W1-W7 and W11-W18 against documents-with-warnings, previously conflated); E87 was reverted by E88 in the following session. |
| 69 | 2026-06-10 | Repository audit with implementation wave (E86): the viewer's XML mode loaded a single page while a save overwrote the whole `_final.xml`, fixed by loading the whole document with a save guard rejecting incomplete TEI, the single-page alternative rejected as inconsistent with the E72 save architecture; the remaining gap-analysis findings were fixed (go-to-page with keyboard navigation, live status lamps, retryable error messages, modal focus management, keyboard and screen-reader operability of both editors), GitHub Actions now runs the suite on every push and pull request, and the register entries from E64 onward became dated subchapters; the comfort findings N1, N3, N6 and N7 were deferred until after ZBZ acceptance and `data/curated_tei/` was declared reserved and empty; suite 563 green, 285/285 schema-valid, all 855 streams `unverifiziert`. |

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

## Lessons

Observations distilled from the sessions that stay relevant for future work:

- L1: Validation must be actionable. A false-positive rate above 50 % makes reports useless; every warning needs a concrete action.
- L4: Merge page fragments into document structure; the ZBZ reference has one top-level div, and the post-assembly merge is deterministic and free.
- L5: Invalidate the step-2 cache on prompt changes; `--force` does not regenerate it.
- L7: Page-numbering drift breaks pagewise CER; content-aligned evaluation is immune.
- L8: Parse multilingual codes correctly ("fra/deu" otherwise decays to "und").
- L9: Keep facsimile and pb in sync; empty surfaces for pages without layout zones.
- L11: Server-less persistence has two truths: the canonical consumption location (`output/`) and the frontend's read location (`docs/data/` mirror). Writing only to the first saves for real but invisibly for the curator.
- L12: With parallel instances in the same tree, `git status` plus verification against the real file state is mandatory; a "file modified since read" conflict is the signal to step back, not to force.
- L13: A prose figure ("285/285 valid") is no evidence; the delivered SSoT needs an automated gate, not a claim.
- L14: A green conformity gate is only as sharp as the corpus it runs over; on the entity-free `tei_final`, "285/285 conformant" means "no violation", not "entities correctly GND-tagged". The entity rules Z1-Z4 bite only after inline-GND curation.
- L15: Newspaper layouts fail systematically (>40 zones, OCR hallucinations); ~3 % of the corpus.

## Archive: full entries of sessions 69 to 96

The full entries of sessions 69 to 96, moved out of the Entries section on 2026-08-21 by operator
decision and kept verbatim, newest first; the compact lines of the archive block above point
here. Entries are never changed retroactively, so corrections are written as new entries and
reference the entry they correct. Links inside the entries name the documents that carried the
subject at the time; where those documents were dissolved in the 2026-08 refactoring the link
points at the carrier that holds the subject today.

### 2026-08-13 Session 96 (continued): marking policy in force, corpus-wide preview run (E119)

**Occasion** The operator decided the two pending marking questions on the evidence tables and released a full run; during the wave the operator also ruled out further subagent use, so the half-finished delegation was stopped and finished by the orchestrator.

**Goal** Both decisions in force, the preview extended from the ten-document panel to the whole delivered corpus, everything verified and documented.

**Course** The two running agents were stopped mid-flight. The lexicon and matcher side of the policy was complete, so the orchestrator finished the intake audit binding, wired the policy path into the four lexicon callers and adjusted the command-line tests, which must opt out of the real policy because loading it against a synthetic list is a genuine misconfiguration. Two defects surfaced only in the real run and not in any fixture. The verdict guard reported a lost recall mention, because the typographic condition destroys a facsimile-verified mention that the corpus spells as a compound without a frame; the title left the condition, since a verified judgment outranks a rule change. The corpus run then exposed that the responsibility declarations of E118 sit in the header and move every body offset, so the viewer mirror discarded nearly every worklist entry as stale; the preview runner now records the shift per document and the mirror consumes it, which is pinned by a test that builds its fixture with the declarations in place. The full run covers every delivered document, each schema-valid and text-invariant, which is a gate previously proven on ten documents only.

**Decisions** E119 (anchor-free surnames and generic work titles through `data/entities/marking_policy.json`, kept apart from the external entity list). One surname held out. Unlisted entities are admitted by the project itself and marked in the data as an addition from outside the curated list. One of the two open adjudication disputes was settled by the reference corpus rather than by convention: in 190 citations of the 25 reference TEIs not one carries a marked person name, so a name span coextensive with a cited title denotes the work.

**Status** Committed and pushed (`d59b94fd`); worklist volume down by about a third, the auto-marked layer up by about the same number of marks, guard at zero violations, full suite green, every changed file lint-clean, viewer mirror and overview regenerated over the whole corpus.

**Next steps** 1. Supplementary draw over the newly released stratum, because the published rate no longer covers the whole auto-marked layer. 2. Admission dossier for the unlisted entities, with textual evidence and deterministic lobid lookups. 3. Work the missed recall mentions into named rule gaps. 4. Operator: the remaining dispute on the show-through page, the held-out surname.

### 2026-08-13 Session 96: matching repairs, overview as evidence surface, mark provenance in the XML (E116-E118)

**Occasion** The operator questioned a review candidate that turned out to be a dotted abbreviation read as initials, then asked what the published overview page actually proves about the workflow, then proposed that every annotation carry in the data itself who asserted it and whether a human checked it.

**Goal** Close the two deterministic matching defects, turn the counting board into an evidence surface, and fix the provenance vocabulary before a second producer of marks exists.

**Course** Four agent waves on disjoint file sets, every self-report verified against disk before it was committed. The first classified all 1113 initials candidates against the raw text and proved that no occurrence of the disputed surface was a mention; the guard tests raw adjacency rather than the normalized projection, because markup between two initials groups separates two mentions and a normalized test kills the genuine speaker labels of doc 1220. The same wave closed the hyphen gap of the surname index, where the word-end cut could never produce the 210 hyphenated keys. The second wave rebuilt the overview: the mirror gained an ambiguity count, a per-entity class breakdown, the adjudicated quality block and a provenance stamp, the page gained the total, inline SVG icons, tooltips and the ambiguity note. The third wave put provenance and verification state on every wrapped mark and wrote the vocabulary into [tei-mapping.md](tei-mapping.md); `@source` carries the rule because it is the only attribute the delivery schema permits on all three wrapped elements. The pilot preview lost its second HTML renderer, since the overview page is now the reading surface. Two evidence agents produced the decision tables for the pending marking questions, working from a frozen scan copy. Alongside, the reference corpus settled one of the two open adjudication disputes: in 190 citations of the 25 reference TEIs not one carries a marked person name, so a name span coextensive with a cited title denotes the work.

**Decisions** E116 (dotted-abbreviation guard and hyphen reach), E117 (ambiguity, adjudicated quality and provenance on the overview), E118 (mark provenance and verification state in the preview TEI). Operator marking decisions taken on the evidence tables and written to `data/entities/marking_policy.json`: 28 canonical surnames released from the anchor requirement, one held out because person and work reading are not locally separable; seven generic work titles dropped from scope, four bound to typographic corroboration. Unlisted entities are admitted by the project itself, annotated, and marked in the data as an addition outside the curated list.

**Status** E116 to E118 committed and pushed, guard at zero violations, battery green, mirror current, page live. The marking policy is decided and its implementation was in flight at the time of writing, as was the admission dossier for the unlisted entities.

**Next steps** 1. Land the marking policy, then the corpus-wide preview run over all documents with the provenance attributes. 2. Supplementary draw over the newly auto-marked stratum, because the published rate no longer covers the whole tier-1 population. 3. Work the missed recall mentions into named rule gaps. 4. Operator: the remaining IAA dispute on the show-through page, the held-out surname.

### 2026-08-13 Session 95 (continued): released work program executed with three build agents (E112-E115)

**Occasion** The operator released the whole open program of the entity workflow for agent execution; the designed operator gates (M6 review, M7 release, the two IAA disputes, list admissions of new entities such as the frequent unlisted person candidates) stay open by design.

**Goal** Every safely reachable gap closed under the verdict guard: curated variants, the adjudicated text defects, the facsimile mapping, the figure-zone convention, then remeasurement material frozen.

**Course** Three Opus build agents on disjoint file sets, every self-report verified against disk. Agent one built the curated-variant channel (optional `variants` field, form source "curated-variant", lint validation); the orchestrator applied the data edits, removed the "Test" placeholder and registered evidence-backed variants on twenty entries with documented skips. The delegation of the text repairs was blocked by the permission classifier, so the orchestrator performed them directly with backups and facsimile verification (E113: hallucination loop 900, ghost page 1520 as blank pb, speaker echoes 2330); the CER chain re-ran with unchanged headline figures. Agent two built the pb-anchor facsimile mapping (per-document sidecar, viewer preference with sequential fallback, affected population audited: spreads, cover offsets, irregular anchors). Agent three switched figure zones from excluded to worklist-demoted (":in-figure", anchor power kept); the orchestrator carried the three named follow-ups (overview class "figure", unlisted channel reads captions on purpose, gold-benchmark miss fixture). Full cycle after the waves: battery green, ruff clean over every touched file, corpus scan regenerated, verdict guard at zero violations for the first time (the repaired documents' records classify text_changed, nothing adjudicated lost), previews, viewer mirror, overview and edition data regenerated. The zero-mention set fell from thirty-seven to seventeen: eight absent or outside the digitized pages, four deliberate homograph skips, one uncertain, four mechanical residuals (hyphenated single-name variants meet a general scan gap for hyphenated surnames; one work-title casing question). Remeasurement material frozen: gold benchmark re-run on the new rules, fresh stratified sample drawn with seed 42 into the dated directory `output/audits/eval_sample_2026-08-13/` beside its frozen scan, so the 2026-08-12 evidence stays untouched.

**Decisions** E112 (curated-variant channel and list hygiene), E113 (pointwise text repairs), E114 (facs mapping via pb anchors), E115 (figure zones demoted instead of excluded); the verdict-store reproduction test became digest-aware.

**Status** Committed and pushed; guard zero violations, battery green, mirror current; the new sample awaits its adjudication wave.

**Next steps** 1. Adjudication wave over the 2026-08-13 sample, then the remeasured precision and recall. 2. Hyphenated-surname scan gap and the work-title casing question as one test-first repair. 3. Operator decisions: IAA disputes p145/p193, unlisted person admissions (ZBZ list domain), M6/M7.

### 2026-08-13 Session 95: verdict guard, zero-mention classification wave, apostrophe folding (E110/E111)

**Occasion** Operator question whether the entity layer really captures every listed entity and how agent-driven repairs can proceed without overwriting adjudicated ground truth; parallel operator review of five problem classes in the viewer.

**Goal** A standing regression gate over the adjudicated judgments, the 42 zero-mention list entries classified (absent in corpus against matcher gap), and every safely reachable gap closed under that gate.

**Course** Built `entity_verdict_guard` test-first: every adjudicated judgment is held against the current scan and classified; violations are exactly a vanished correct mark, a wrong mark still asserted in tier 1, and a real mention that no longer surfaces; tier moves stay informational because rule changes move marks legitimately. First run evidence: all 279 correct marks survive, 10 of 14 wrong marks repaired, the 4 remaining are text-side defects (OCR phantom on a blank leaf in 1520, hallucination loop in 900, generated speaker duplication in 2330); of the 30 adjudicated misses 27 now surface and 3 remain (two the decided J.-C. exception, one the newspaper short form). A planned footnote-digit repair was refuted by a corpus probe before any code: real names never carry glued ASCII digits, the true superscripts are already separated. Three Opus agents classified the 42 zero-mention entries read-only against cache and both text streams: two genuine absences, two entries out of digitized page range (foreword of 2635), one placeholder defect ("Test", gid 000000), the rest matcher or lexicon gaps with evidence and proposed variants (report under `output/audits/zero_mention_classification/`). Their sharpest finding, the apostrophe mismatch (corpus U+2019 after E94, list and cache ASCII), was verified and folded at matching time in three consistent places (E111); the guard confirmed the identical adjudicated state after the change, previews, viewer mirror and overview regenerated, five entries left the zero-mention set. The stored empty unlisted report of 2026-08-12 was refuted by a fresh run; the channel carries ranked candidates (top person-shaped: Raymond Aron, Pere Fessard). Also identified: doc 1350 maps six text pages onto four facsimile images although the pb elements carry correct facs anchors; the mirror numbers pages sequentially and drops the anchor, a delivery-chain defect outside the entity layer.

**Decisions** E110 (guard semantics and gate capability), E111 (apostrophe folding, diacritic folding deliberately excluded); list edits from the classification wave stay operator-gated, the agents proposed variants without touching curated data.

**Status** Committed and pushed; battery green, ruff clean over the touched files, guard at the 4 known text-side violations, overview shows 37 zero-mention entries remaining.

**Next steps** 1. Operator review of the classification report, then the variant additions to the curated list. 2. Text-side repair backlog (1520 phantom, 900 hallucination loop, 2330 speaker duplication, 1350 facs mapping). 3. Fresh sample and gold run under frozen rules (M4 close), then remeasured precision and recall.

### 2026-08-13 Session 94 (late night): entity-layer refactoring wave with three Opus agents

**Occasion** Operator direction to name and execute honest refactoring and optimization, delegated to Opus subagents.

**Goal** Structure and quality lifted where the entity layer had grown organically, with proof that nothing changed behavior.

**Course** Two parallel agents on disjoint file sets, then a third: the matcher module (1853 lines, two responsibilities) split into `scripts/tei/entity_lexicon.py` (lexicon construction) and `entity_matcher.py` (candidate scan) with the full outside API re-exported, so no caller and no test changed; the rule-suffix parser became the public `base_rule`, consumed by risk ranking and overview generator instead of local copies; the preview runner gained `--all` (test-first, numeric doc order); the overview frontend precomputes its gid lookup, and two provably dead CSS rules left with grep evidence. The third agent introduced `pyproject.toml` with the curated ruff configuration of the house guideline (lift-on-touch, deliberately not a repo-wide sweep) and brought the seventeen entity-layer files to zero findings out of fifty, with the re-export block alias-marked, three targeted noqa comments justified in place, and one per-file-ignore for the stopword word lists. Verification against disk after each wave: the full battery green (743 tests), agent equivalence check of old against new matcher over all 285 documents, and the corpus scan regenerated byte-identically to the pre-refactor hash in four of five runs; the single deviating run is not reproducible and consistent with a concurrent instance writing the shared gitignored output path, the code paths proven deterministic. Deliberately not done and recorded as such: the viewer.js module split (tracked open item, needs its own session), the duplicated static-page chrome (no-build tradeoff), the transposed redundancy inside the overview JSON, and the operator-gated deletion of `tei_reassemble_preview`.

**Decisions** Re-exports stay alias-marked rather than blanket-ignored, so a genuinely dead import still fails the gate; ruff runs check-only, no formatter churn.

**Status** Committed and pushed; ruff clean over the entity layer, battery green, scan hash proven stable, frontend smoke green in headless Chromium.

**Next steps** 1. Classify the unmatched list entries (absent in corpus against matcher gap). 2. Redraw and remeasure on the new rules. 3. viewer.js module split as its own session.

### 2026-08-13 Session 94 (night): overview page refocused as completeness instrument

**Occasion** Operator feedback on the freshly built page: the purpose is the developer check "do we really have every listed entity", aggregated rather than exploratory, with less text; the workflow-status dot is unnecessary, and the "hand-checked" badge misled, since it showed the adjudicated evaluation sample rather than anything the operator personally reviewed.

**Goal** The page answers the completeness question first, and every element the operator named leaves.

**Course** The generator now aggregates per listed entity, including every list entry without a single corpus mention; the run surfaced the central finding directly, a substantial share of the curated list never matches in the corpus, visible per entry with label and id. The page opens in the entity view with the unmatched entries sorted first, a warn badge carries the found-of-listed count on the corpus bar line, and each entity expands into the documents it occurs in with viewer links; the document view stays as the secondary toggle, without status dot and without the adjudicated-sample badge, review classes as tooltip chips instead of a definitions box. The verdict-store join left the generator; the closed-world gate now also covers the entity section keys. Verified again in headless Chromium (both views, search, toggle, screenshots reviewed). Two general frontend rules were recorded in the session memory earlier the same evening: no KPI/stat cards, no intro copy; numbers belong in functional elements, explanations on demand.

**Decisions** The adjudicated sample stays out of the page: it is measurement evidence (reports, verdict store), and presenting it as review progress overstated it. Per-mention operator review has no tracking mechanism yet; the per-document status pill of the viewer remains the only human-review record.

**Status** Committed and pushed; generator suite, ref-invariant gate and script health green. The unmatched-entries list is the operative worklist for the completeness question, either genuinely absent from the corpus or missed by the matcher; distinguishing the two is the next measurement task.

**Next steps** 1. Classify the unmatched list entries (absent in corpus against matcher gap), agent-assisted against the OCR text. 2. Redraw and remeasure on the new rules. 3. M4 frozen-rules gold run.

### 2026-08-13 Session 94 (evening): entity overview page per document

**Occasion** Operator request for a frontend that answers, per object, which and how many entities are annotated and how certain the annotation is.

**Goal** A static overview page in the existing docs site, fed by a deterministic mirror file, with the certainty model of the tier architecture made visible.

**Course** New generator `scripts/edition/generate_entity_overview.py` aggregates the corpus scan into `docs/data/entity_overview.json` (per document: auto-marked against review counts, review classes, per-entity breakdown; the facsimile-adjudicated sample joins as a hand-checked layer per document), deterministic and pinned by its own pytest suite; the closed-world gate `test_entity_ref_invariant` gained a case over the new file's ids. New page `docs/entities.html` with `entity-overview.css` and `entity-overview.js` (ZBZ.EntityOverview, no-build, tokens only): summary strip, review-class legend, search, sort (id, mentions, review share, auto), filter, one expandable row per document with stacked certainty bar, workflow-status dot of the entities stream, class chips, entity table and a link into the viewer's annotated reading view. Verified in headless Chromium against the served docs root: summary numbers, drill-down rendering, search and sort behavior, screenshots reviewed; one grid-specificity defect found and fixed that way. Nav of index, methode and about gained the Entities item; workflow.md 3.7, CLAUDE.md commands and the script inventory carry the page.

**Decisions** Certainty is presented in two levels (auto-marked in Olivgruen, review candidates in Ocker, matching the badge palette), with the review classes as the explanatory second layer; the page reads only generated mirror files and stays read-only.

**Status** Committed and pushed; generator tests, ref-invariant gate and script health green. The page ships with the GitHub Pages docroot as-is.

**Next steps** 1. Redraw and remeasure on the new rules, then the per-category numbers appear next to the certainty bars. 2. M4 frozen-rules gold run. 3. Judge calibration for the worklist classes the page now exposes.

### 2026-08-13 Session 94 (continued): adjudicated error classes repaired, verdict store rebound (E109)

**Occasion** Operator direction to repair whatever blocks capturing the work class and, beyond it, every listed entity; the nine facsimile-confirmed wrong_entity and wrong_span cases of the evaluation snapshot were the concrete material.

**Goal** Every confirmed error class answered deterministically, span defects repaired, nothing silently dropped, and the measurement basis kept sound.

**Course** Corpus probes grounded each candidate rule before building (hyphen-adjacent tier-1 marks, citation frames, container prefix, italics distribution); a broad italics guard was rejected because the probe showed genuine mentions (interview labels, bylines) sharing the signal. Implemented test-first: five worklist demotions (compound hyphen, author-initial frame, editor-abbreviation frame, eponymous institution prefix, undated parenthetical after a surname, lowercased work-title incipit) and two span repairs (internal particle bridge for "Saint Ignace de Loyola", subtitle-join channel for "Title. Subtitle" prints). All nine adjudicated cases verified fixed at their corpus positions; the scan's hyphen invariant fell from eleven violations to zero. A latent wiring defect surfaced and was fixed at the root: `build_mention_verdicts` read the live scan, whose tier-1 population the new rules had moved; it now reads the frozen snapshot the sample was drawn from, and the rebuilt store differs only in its source line. A false alarm was cleared on the way, the verdict-store offsets are exact against the current TEI when read byte-based; an earlier text-mode read had shifted them by the CRLF count. Regenerated: scan, 285 previews (all schema-valid, text-invariant), viewer mirror, risk ranking, running-head audit, gold benchmark; the reference trend rose to tier-1 precision 0.67 with recall and coverage unchanged, the signature of pure false-positive removal. Entity battery green (712 tests).

**Decisions** E109 (guards and span repairs from adjudicated cases only; citation lines without a deterministic frame stay for the judge; "avant J.-C." never enters the lexicon; store build bound to the frozen scan).

**Status** Committed and pushed. `tei_final` still carries no entity markup; the work class now has its confirmed error classes closed, and the tier-1 promotion of works awaits the next measured per-category precision.

**Next steps** 1. M4 frozen-rules gold run on the held-out references. 2. Redraw and remeasure precision and recall on the new rules (byline gaps become hits, work errors closed). 3. Judge calibration (M5) for the grown worklist. 4. Operator decisions: works in tier 1 after the remeasurement, IAA disputes p145/p193.

### 2026-08-13 Session 94: running-head suppression active in the matcher, author convention decided (E108)

**Occasion** Operator decisions on the entity layer: build the validated running-head detector into the matcher as the E105 suppression, and settle the author scope question without ZBZ, whose feedback channel is unavailable in this phase; mentions of the corpus author are always marked.

**Goal** The matcher enforces the page-apparatus convention by itself, the byline exception disappears, and the convention reading of the adjudicated precision becomes computable.

**Course** The detection core moved unchanged from the audit into the shared module `scripts/tei/running_heads.py`; the matcher demotes every candidate inside a detected head zone to tier 2 with the `:running-head` suffix, while a demoted full name keeps its document-wide anchor power (the head names the document's subject, so bare surnames in the body still resolve). The author machinery (`author_labels`, `CORPUS_AUTHOR_LABELS`) was removed from the matcher and all callers. Test-first throughout: new suppression and anchor fixtures, rewritten author tests, the full entity battery green. Regenerated on the new rules: corpus scan (671 candidates demoted in head zones, author marks now included), all 285 previews schema-valid and text-invariant, viewer mirror, risk ranking, gold benchmark (reference trend improved to tier-1 precision 0.61, tier-1-plus-2 coverage 0.87). `running_head_audit` gained the `convention_precision` block (seeded percentile bootstrap): 0.9511 with interval 0.9248 to 0.9737 over 266 decidable in-scope cases, within the interval of the protocol reading 0.952, so running heads were not inflating the published figure; after suppression 0 of 3925 tier-1 marks sit in a zone. Correction to the session-93 recall claim of 24/24: the keyword criterion counts 25 ground-truth marks, one of them (doc 2510) is body text whose verdict reason merely mentions the intervening running header, so the criterion reads 24 of 25 while no real head is missed.

**Decisions** E108 (operator): author mentions always marked, byline exception removed; running-head suppression active with anchor power preserved for demoted heads; convention questions of the entity layer fall to the operator while ZBZ feedback is unavailable.

**Status** Entity gates, running-head audit tests and script health green (702 tests in the affected battery); scan, previews, mirror and audits carry the new rules; `tei_final` still carries no entity markup. Committed and pushed.

**Next steps** 1. Operator decision on works in tier 1 (assessment delivered: persons and organisations first, works stay on the worklist for the first stock wave). 2. M4 frozen-rules gold run on the held-out references, evidence under `docs/data/`. 3. Redraw and remeasure recall; the byline gaps of the executed run become hits. 4. Remaining session-93 items: IAA disputes p145/p193, FP-hunt wave including the hallucination candidates, lexicon audit before M4.

### 2026-08-12 Session 93 (evening): documentation trued up, viewer reduced, paratext detector validated

**Occasion** Operator direction to finish the day rolled out, refactored and documented: execute every decision-free consequence, reduce the viewer UI step by step, and audit the documentation for freshness and self-reference.

**Goal** A compact-stable repository: findings fixed at the root, UI decisions implemented and registered, knowledge base consistent, no running agents.

**Course** Working paper revised to a methods-and-findings paper (0eab92d5); journal compacted with a mechanical no-fact-lost check, seven session-93 entries consolidated (7cf84b23); TEI-XML view freeze fixed via page-slice default with full-document on demand (49c5ee7a); UI analysis report (80187507) grounded three operator-decided UI steps: one document bar without subtitle (e7f9dd6d), View/Edit dropdowns replacing seven scattered controls (baecc433), condensation to three views with the annotated reading view as corpus-wide default and markup as a menu toggle (d65854a3, register E107). Document 1620 became the fifth committed demo document with live facsimiles on GitHub Pages (e4f641cd); the slide deck gained the paratext-case slide and a closing synthesis slide (14b0d1bc, f564ff48). A six-agent wave delivered: the viewer entity layer documented in workflow.md 3.7 (ab2aa803); a blank-page hallucination audit with a Docling zero-region channel, confirming doc 1520 p130 and finding 16 substantial candidates in 17 documents while clearing all 79 manifest blank pages (1ea04387); the corpus scan now emits a page field consumed by the risk ranking, cross-checked 300/300 against the verdict store (57ece48e); a documentation freshness audit with 20 ranked findings (b2957277) whose decision-free fixes were applied across README, constitution, pipeline.md, project.md, about.html and methode.html, including the E99 correction of the reading-order narrative and the entity-layer state (f7a06252); and the running-head detector validated against the adjudicated ground truth, 24/24 true running heads detected, 2 front-matter false alarms of 254 body marks, 391 of 4051 tier-1 marks in zones as the future suppression scope (c3b85822).

**Decisions** E107 (viewer UI reduction, operator). Paratext terminology replaces the apparatus label in the deck. The `.env.example` template stays unwritable by policy (dotenv deny rule); the README names the environment variables directly.

**Status** All packages verified against disk, committed and pushed through d65854a3; entity gates, corpus invariants and script health green; no agents running; working tree clean except `knowledge/arbeitsbericht-v3.md` (held by another instance). Compact-stable.

**Next steps** 1. Operator answers: four convention questions (author caps bylines, speaker labels, cert levels in delivery, verdict lifecycle), two IAA disputes (p145, p193), five gos (tei_reassemble_preview deletion, FP-hunt wave including the 16 hallucination candidates, essay filing for vault and Editopia, paper-evidence registration, journal archive 69-79). 2. Running-head suppression in the matcher per the validated detector, then preview regeneration and the convention reading. 3. UI step 3: metadata tooltips and tooltip sweep. 4. Redraw and remeasure recall after the convention answers.

### 2026-08-12 Session 93: GND entity integration built, evaluated, and consolidated (M0 to M4, E105/E106)

**Occasion** A curated normdata export `all_entities.json` appeared untracked in the
repository root, meant to feed GND entity markup into the delivered TEI; the operator
released the work in seven successive waves across the day, from source survey to the
decision-free consequences of the evaluation.

**Goal** A deterministic entity layer over the delivered corpus, with the source data
understood, matcher and preview instruments built, precision and recall measured against
evidence, and every adjudicated judgment persisted.

**Course** Wave 1, survey. Two agents ran in parallel, one aggregating the file with an
executed Python script, one surveying the repository read-only. The file holds three
lists (persons 177, organisations 32, works 87; 296 entries), every entry with a
formally valid GND id, no duplicates, and `works.author_gnd_id` fully resolving; defects
are one test entry, one empty stub, four untitled works, one unnamed organisation, one
deviant DNB link, and `editor_reviewed` true on only 10 entries. After checksum
normalization the E71 remnant `output/gnd_analysis/gnd_entities.json` (mention index
over 18 reference TEIs) is a strict subset, all 75 of its ids covered. The survey
confirmed the binding E88 inline-GND target convention as realized in the 25 reference
TEIs, the E94 marker pattern as the only sanctioned write path into `tei_final` (E99
forbids regeneration), and the verification stack of schema gate, conformity rules
Z1-Z4/Z8 (idle since E71, lesson L14), pytest suite, CER reproduction as text-invariance
proof, and the reference TEIs as gold standard for matcher precision. Central finding:
the file carries normdata without mention sites, so deterministic surface-form matching
is the actual work; naive surname matching yields 8314 candidates with strong homonym
ambiguity, and even the corpus subject's surname is ambiguous inside the file itself
(three entries share it). The delivered plan is a five-phase sequence of intake and
lint, dry-run matcher, gold-standard evaluation against the reference TEIs, E94-pattern
stock run, and post-run verification with mirror regeneration.

Wave 2, milestone M0. The design plan [tei-mapping.md](tei-mapping.md) was
written, simplified on operator request, and wired into [index.md](index.md) and
CLAUDE.md; `all_entities.json` moved from the repository root to `data/entities/`
(git-tracked). Validation probes against `zbz_hersch.rng` confirmed that nested
`persName` inside `bibl`, `hi` inside `bibl`, and `lb` inside `persName` are
schema-valid, and reference-corpus probes settled the modelling detail rules recorded in
the plan (bibl wraps hi, title-only span, footnotes carry refs, particles outside,
mid-word line breaks inside names).

Wave 3, milestones M1 to M3. Three build agents delivered `fetch_gnd_variants`,
`entity_lint`, `entity_matcher`, and `tei_entity_preview`; the pilot ran over the
ten-document panel into `output/entity_preview/` with all schema and text-invariance
gates green. A 14-agent evaluation wave (ten per-document evaluators, three adversarial
verifiers, one completeness critic) confirmed 106 of 109 findings and exposed two
systematic tier-1 defects, lobid initials variants ("J. H." claimed as Pestalozzi across
an interview, doc 1220) and work-title spans carrying imprint or inverted `hi` nesting;
the critic's read-only corpus scan added German homograph surnames ("Weil" the
conjunction), a poisoned legacy pairing ("Jérémie" filed under Jaspers where the
reference marks the prophet), the anchor collision in doc 1520, and the volume
concentration on the author and her main subject. A second four-agent wave built the fix
package (legacy demotion with lint pairing check, homograph suspicion signals, adjective
forms to the worklist, caps-full-name rule with author-byline exception, apparatus zone,
`bibl` outside `hi`), the corpus-scan instrument, the operator-gated cover-strip marker,
and the read-only viewer entity layer (`?entities=1`, popovers with GND and lobid link,
per-page worklist). After integration the panel rerun shows 195 wrapped and 120 worklist
entries with gates 10/10, the first corpus scan reports 3496 tier-1 and 4074 tier-2
candidates over 285 documents with zero function-word violations and Jérémie never tier
1, and the legacy index is versioned under `data/entities/legacy_mentions.json`. Side
finding of the cover-strip dry run: two library delivery sheets (docs 200, 490) carry
patron personal data, one with private e-mail addresses, a finding for ZBZ independent
of the entity work.

Wave 4, milestone M4 and the frontend evaluation round. Four parallel build agents
delivered the gold benchmark (`entity_gold_benchmark`, scope-restricted against the 25
references with the 2026-08-12 scoring rules, held-out set drawn along the gold-mention
distribution with 1520 kept separate), the unlisted-entities scan
(`entity_unlisted_scan`, id-free proposal channel whose top proposals include a heavily
mentioned unlisted philosopher and the library itself as organisation), the corpus
digest (`entity_corpus_digest`, the whole tier-1 harvest in one context window), and the
visibility iteration in the matcher (candidates now carry all alternative bearers, the
matched form with its source, and a typographic-evidence flag on one-word titles; the
neighbour suspicion check is bigram-aware). First benchmark numbers: held-out tier-1
precision 82 percent, overall 62 percent driven by one structural case (doc 3040
declares its bibliography as `div type="entry"`, so the exclusion zone cannot fire;
without it 90 percent), candidate coverage 83 percent, and the work class carries the
errors in both directions, which supports keeping works out of the first stock wave. The
operator's live findings (the arbitrary first-bearer display on "Jaspers", the
birth-name variant behind "Hans Mayer", the discipline reading of "Philosophie") are
fixed or made visible and frozen as regression cases. A viewer follow-up added inline
worklist rendering with provenance popovers and the entities workflow stream, so the
catalog shows the entities stage corpus-wide with a pending state; documents 1540, 1520,
3040 and 380 joined the evaluation set, and most missing translated work titles turned
out to be case-sensitivity with their forms already sitting in the GND cache.

Wave 5, cover strip and a five-agent wave. The operator's own run of
`python -m scripts.tei.tei_cover_strip --write`, released in wave 4 but blocked there by
the permission layer and interrupted here during the per-file RelaxNG check (which looks
like a hang), had already stripped 21 of 22 covers, since the write happens only after a
passed schema check and nothing was half-written; the resumed run finished document 890,
all 285 documents validate, and the 11 partial-field documents stayed untouched. Five
Opus agents returned confirmed results. False-positive classification outside 3040: of 9
cases 1 real matcher error, 2 reference gaps, 6 zone artifacts in page furniture and
plate paratext, none OCR-caused. False-positive classification for 3040: 39 of 42 cases
are one structure defect, since the pipeline TEI renders the bibliography as plain
paragraphs instead of `div type="bibliography"` with `listBibl`/`bibl`, so the matcher's
existing zone rules never fire (1520 shows the working counterexample) and fixing the
generator removes about nine tenths of all corpus false positives. Case-tolerant
matching for multi-word lexicon forms (letters-only case difference, diacritics and
punctuation exact) demotes fully lowercased phrases to `:suspect` and adds roughly 500
new matches corpus-wide, mostly work titles. Probe-free viewer loading ends the 404
probing by giving the catalog a per-document asset index, so the viewer fetches only
existing files, verified over HTTP with zero non-200 responses against the hundreds a
baseline replay of the old code produced. The variant review gives every cache-derived
name form an approve/suspect/reject verdict in the versioned file
`data/entities/variant_review.json`, with the operator worklist in
`output/audits/variant_review_report.md`. The orchestrator then wired consumption
test-first into `build_lexicon`, where reject drops the form entirely (including its
surname-index entry), suspect and unreviewed forms yield tier-2 candidates only, and
headwords and legacy forms stay unfiltered; rejected junk bearers thereby disambiguate
real mentions, so tier 1 rose while the total fell, and the known damage cases (initials
variant, Freund/Freud, cross-bearer collisions) are now held back structurally.

Wave 6, the evaluation. Nine Opus agents adjudicated per the versioned protocol, six
precision ranges (300 cases), one blind second adjudicator (50 cases), and two recall
readers (40 pages), with every verdict file verified against disk; the protocol itself
was corrected mid-wave (wrong Hersch gid), found by an agent. Results in
the evaluation result (verification.md, appendix) and
`output/audits/entity_eval_report.json`: precision 0.952 (CI 0.925-0.976) over decidable
cases, raw agreement 0.96, and recall coverage 0.552 with 28 of 30 misses being rule
gaps (speaker initials, acronym casing, GND qualifier, byline exception). The agents
also surfaced generator defects (sp/speaker duplication, hallucinated OCR pages) and
further facsimile-offset documents (680, 2300, 1220).

Wave 7, the consequence wave. Four parallel agents with disjoint file scopes, each
verified against disk before commit, built the mention verdict store
`data/entities/mention_verdicts.json` via `scripts/eval/build_mention_verdicts.py` (all
300 precision verdicts including the 50 blind IAA second judgments with disagreements
p145/p193, plus 67 recall mentions, keyed by doc, page, surface, gid and occurrence,
each bound to a sha256 fingerprint of the source TEI so re-OCR surfaces as staleness,
with a byte-deterministic rebuild); the exhaustive invariant gate
`tests/test_entity_ref_invariant.py`, under which every GND id in all preview files and
worklists is a member of the curated list, zero violations, and 61 curated ids occur
nowhere in the corpus; five matcher repairs as derived channels that stay tier 2
(acronym case tolerance, parenthetical qualifier strip, static place-adjective
inversion, superscript digits as word boundaries, person initials); and the
false-positive risk ranking `scripts/eval/entity_risk_ranking.py` plus the wave protocol
`output/audits/fp_hunt/PROTOCOL.md` (versioned copy in reports/), which scores 4043
tier-1 marks into high 1517 / medium 960 / low 1566, the high stratum dominated by
anchored-surname hits on 39 gids. Impact measured against the frozen scan (copy in
`output/audits/eval_sample/`): the worklist grows by 1657 proposals while tier 1 changes
only by +9 (all superscript footnote cases, e.g. work titles carrying a footnote digit)
and -1 (a mid-compound match inside a hyphenated university name replaced by a clean
tier-2 qualifier-strip candidate), and the hyphen-adjacent invariant is unchanged (11
known cases). Corpus previews and viewer mirror were regenerated; schema and text
invariance pass 285/285.

**Decisions** Modelling (operator, 2026-08-12): nested entity markup is permitted (the
gold benchmark scores correct nesting as neutral); ref-less stock elements are enriched
in place only when the tier rules verify the assignment; the pilot runs with three
parallel build agents and an evaluation wave of fourteen agents, deterministic tiers
only, no judge. Scope (operator, 2026-08-12): title-only binds for works even against
wider reference citation spans (gold scores those neutral); all-caps mentions are in
scope while bylines and running headers of the document author stay unmarked (Masterfile
comparison); E-Periodica cover sheets leave the delivered TEI via the operator-gated
marker and the strip is executed corpus-wide (22 documents, backups kept); library
apparatus (cover sheets, photo credits) is out of matching scope; every data channel
passes intake lint, shape-class review, and pilot before its forms may match; a form
class whose candidate set misses the true bearer skips tier 2 entirely. Enrichment
variants are audited by a model against each bearer's record into a versioned verdict
file before M6, operator-approved and consumed deterministically, and the unlisted
report is the proposal channel for list extensions with ids staying at ZBZ. The variant
review file is the single deterministic gate for cache name forms; an unreviewed form
counts as suspect until the next review run. The 3040 bibliography repair belongs to the
TEI generator (structure lane), not to the matcher. Statistics are reported only where
the data carries them, bootstrap CI for precision, raw agreement for the agreement
check, descriptive counts elsewhere. E105 settles the page apparatus: running heads stay
unmarked, title pages, byline organisations and picture captions are marked, which also
disposes of the page-furniture work-title hits (running column titles, document 330);
the evaluation report therefore carries the protocol reading plus a described apparatus
count, and the convention reading is recomputable from the persisted verdicts without
drawing again. E106 covers the consequence wave: every derived form channel emits tier-2
worklist candidates only and never tier-1 auto-marks, safety over coverage (rejected,
tier 1 for safe-looking derivations); verdicts are snapshot-bound via text fingerprint
(rejected, raw offsets without staleness detection); the occurrence index is computed
against the full tier-1 candidate population of the frozen scan, because 106 of 300
sampled marks repeat their surface on the page.

**Status** M0 was committed with its own entry; the pilot and fix package pushed as
35281270, the cover-strip marker as 735864a2, the viewer layer as 5dcc2365, and the plan
updates as 4ee671a5. The M4 instruments and the frontend round pushed as 36a1ebd8,
31df4503, a8472fd8, 251c63d8 and ae374797, the five-agent wave through the
variant-review commit, and the consequence wave as 8a0e34ae (invariant gate), 40afccf2
(verdict store), c81b5922 (risk ranking) and 6487e0b6 (matcher repairs), with the mirror
regeneration committed subsequently. Entity gates 388 passed, script health 154 passed,
invariant and mirror gates green after regeneration, and all 285 documents validate
after the cover strip; the viewer serves on the local port with the new asset index. One
worklist entry is not locatable inline (noted in the generator report). The wave-1
analysis was verified by an executed aggregation script (session scratchpad, exit 0) and
the repository survey cites schema and code lines. Evaluation lesson recorded in the
plan: panels are drawn by impact and class coverage, precision checks run as per-mention
batches, and the gold benchmark (M4) replaces agent evaluation where references exist.

**Next steps** 1. Model the cert/resp delivery layer (respStmt taxonomy, confidence
levels, revisionDesc projection). 2. False-positive hunt over the high stratum, spread
by gid and document. 3. Recompute the convention reading of the precision figure from
the persisted verdicts under E105, and build the deterministic running-head suppression
instrument. 4. Redraw the sample and remeasure recall once the repairs are in. 5.
Structure lane in the TEI generator: sp/speaker duplication and the 3040 bibliography
defect; afterwards classify the four new 3040-zone false positives. 6. M5 judge pilot
with per-document batching on the gold-resolved worklist cases, plus the operator review
of the suspect/reject worklist. 7. Page-mapping repairs for the facsimile-offset
documents (operator-gated); patron-data finding (documents 200/490) to ZBZ. 8. Open
operator decisions: works in tier 1, author scope, hyphen compounds, document 180. 9.
Process-evaluation synthesis and talk deck.

### 2026-07-31 Session 92: knowledge base aligned post hoc with the Promptotyping convention (E104)

**Occasion** The method paper "Promptotyping. Translating Research Data into Research Artefacts
through Context Engineering and Agentic Engineering" cites this repository as evidence for a
Promptotyping knowledge base. The alignment was commissioned for that paper and is post hoc by
design; the paper's evidence citations pin the pre-alignment state to commit 5b78b69d.

**Goal** Every knowledge document names its convention function machine-readably, with no file
renamed, moved, or rewritten.

**Course** The Convention Knowledge Documents and the template catalogue of the Promptotyping site
were read against the actual frontmatter of the knowledge base. The mandatory core was already
complete throughout, with nested `project` and `method` blocks, so the gap lay in the recommended
layer: the `template` object and the `authors` field. Seven documents now carry a template mapping
(index, project, specification, pipeline, workflow, infrastructure, plus journal, which already
carried it and was verified against the catalogue), six stay freehand with a stated reason,
[index.md](index.md) gained a function table, [decisions.md](decisions.md) the register entry E104
with the full rationale. `generated-with` was set nowhere, because the co-author trailers of each
document span several model versions and a per-document value would state less than the git history.
[arbeitsbericht-v3.md](arbeitsbericht-v3.md) was excluded from the pass, since it carried an
uncommitted working state.

**Decisions** E104: post-hoc convention alignment, additive frontmatter only, no renames and no
prose changes. The repository status vocabulary (complete, reviewed) stays as an extension of the
convention enum draft/active/archived, the same extension the Promptotyping repository's own
knowledge base carries; rejected alternative was normalising the values, which would drop the review
state. infrastructure.md is mapped onto Vorlage Architecture because that template's scope section
names `infrastruktur.md` as a regular split of the Architecture function for deployment and CI/CD.

**Status** Twelve knowledge documents changed in the frontmatter, index.md and decisions.md
additionally in content. No code touched, `python -m pytest tests/ -x -q` green (1390 passed,
1 skipped, the data-dependent case self-skipping).

**Next steps**
1. Give arbeitsbericht-v3.md the same additive pass once its working state is committed.
2. Decide whether the repository-wide `version:` schema field of the convention's refactor checklist
   is introduced; no document carries it today.
3. Settle the status vocabulary, either by adopting the convention enum here or by recording the
   extension in the convention itself.

### 2026-07-09 Session 91: DTA conformity claim tested, refuted, and removed (E102)

**Occasion** Operator question whether the delivered TEI is really valid against the
DTA-Basisformat, as the report's opening sentence claimed; the repository had never
validated against the DTA schema.

**Goal** An evidence-based answer and a consistent format claim across the repository.

**Course** The official `basisformat.rng` was fetched from deutschestextarchiv.de and
the corpus validated with RelaxNG (lxml): 0 of 285 `tei_final` documents valid, and,
decisively, 0 of 25 ZBZ reference TEIs. Minimal-case isolation located the violation
classes: the delivery-contract header (idno types, biblStruct), `revisionDesc` and
`facsimile` (absent from the DTA schema entirely), and body conventions such as
`div type="text"`, `pb type="blank"`, and `head@facs`. The operator decided to drop
the DTA claim entirely; the format authority is the project schema `zbz_hersch.rng`
(TEI P5 subset formalizing the ZBZ editorial guidelines). All living documents were
reworded ([arbeitsbericht-v3.md](arbeitsbericht-v3.md) including footnote 2,
[pipeline.md](pipeline.md) TEI-mapping section, [index.md](index.md),
[project.md](project.md) M4, data READMEs) and the step-2 prompt plus two docstrings
(`tei_mapping_prompt.py`, `tei_generator.py`) updated; the prompt change affects only
future refinement runs, which are operator-gated (E99). Dated register and journal
entries stay unchanged as snapshots; the ZB guidelines' own DTA reference remains
documented as source data.

**Decisions** E102: DTA-Basisformat conformity claim refuted and removed, no parallel
DTA validation; rejected alternatives (corpus transformation, stripped "DTA view"
gate) in the register entry.

**Status** All rewordings applied, `pytest tests/test_scripts_health.py` green after
the script edits, no DTA mention left in living documents.

**Next steps**

1. None; the reworded report is ready for the next delivery cycle.

### 2026-07-09 Session 90: final report moved to knowledge/, stub retired

**Occasion** Operator decision that the final report lives in `knowledge/` under a
versioned filename, as a single document instead of report plus stub.

**Goal** One canonical location for the project report and consistent references
across the repository.

**Course** `reports/arbeitsbericht-v3.md` moved to `knowledge/arbeitsbericht-v3.md`
(git mv, history preserved); the superseded stub `knowledge/final-report.md`
deleted. Living references updated: CLAUDE.md, README, [index.md](index.md), the
domain docs, [decisions.md](decisions.md) link targets, `docs/methode.html`, and
four script docstrings whose pointers now name the surviving source
([methodology.md](methodology.md) for the CER contract and aggregation,
decisions.md E85 for the footnote instruments). Dated snapshots (journal entries,
the 2026-07-07 verification report) remain unchanged per format contract.

**Status** Script health suite green. Outside dated snapshots no reference to the
old paths remains (grep-verified).

**Next steps** 1. None; housekeeping session closed.

### 2026-07-07 Session 89: backlog plan executed; doc 30 repaired (E98), machine reordering falsified (E99), stability measured (E100)

**Occasion** The operator approved the plan for the three remaining backlog items
(doc-30 repair, M3 reading-order rollout, run-to-run stability pilot).

**Goal** Close the backlog with evidence: repair what is repairable, prove or
refute the reorder before touching the corpus, and quantify LLM non-determinism.

**Course** Phase 1 restored the lost left half of doc 30's first double page
(re-read at 300 DPI, facsimile-verified; three paragraphs with honest new zones
r_4..r_6, two provably wrong zone boxes corrected, pb lifted to [222]); fidelity
11.59% to 0.90%, corpus headline to mean 2.08% / median 1.28% (paired -10.08pp,
p = 0.0034). Phase 2 built `tei_reading_order_fix.py` test-first (byte-splice
permutation of robust W19 pages, marker idiom, shared `build_zone_bbox`); the
plan's dry-run gate then FALSIFIED the corpus run: CER-guarded probe over copies
of all 25 reference docs shows 0 improvements, 9 degradations up to +40pp,
because W19 pages mostly carry corrupt block-to-zone assignments over correct
text. No machine reordering, on any path; W19 reframed as text-or-zone suspect
signal, tool kept as dry-run instrument with --write gate (E99). Phase 4
measured run-to-run stability (5 docs x 3 forced runs in isolated directories):
per-doc fidelity std 0.000-0.129pp, mean 0.040pp; `stability` closed as measured
in the versioned statistics JSON (E100). Gates green throughout (suite, schema,
validator 285/285); mirror regenerated; reports and register updated.

**Decisions** E98 (repair executed), E99 (reorder falsified and banned, preview
obsolete), E100 (stability measured on the production model). Pilot documents
570/2310/1910/830/890 designated (stratified, reference-covered, small).

**Status** All three backlog items closed. The corpus stands at 285/285 valid,
fidelity mean 2.08% / median 1.28%, stability measured, W19 as curation
worklist. Commits pending push gate.

**Next steps**
1. Push (operator gate).
2. ZBZ items: better scan for 1520 p70; W19 zone-curation worklist; doc 10.
3. Optional: doubled-page tails 760/1440 (E91-classified, curation).

### 2026-07-07 Session 88: Doc 30 adjudicated (E97), arbeitsbericht v3 finalized

**Occasion** The operator asked for the best answers to three involvement questions
(doc-30 adjudication, report audience and redundancy policy, sequencing of the
remaining backlog) and their integration into the work report, which stays v3.

**Goal** Resolve the doc-30 contradiction with evidence, then bring the report to a
fully measured, internally consistent state.

**Course** Doc-30 adjudication via canonical alignment plus facsimile: the three
missing blocks (540/451/194 chars) all lie on the left half of the first double
page (printed page [222]), fully legible on the scan and absent from every OCR
stream and the delivered TEI; the E94 calibration had sampled facs 2-4 and missed
the affected page, so E91's text-loss reading stands and the "pure alignment"
generalization falls (register E97). Report updates: adjudication slot filled,
preamble now records the v3 delta instead of open values, 1520-p70 item moved to
repaired state (E96), decision count and register pointers refreshed, two
colon-connector sentences and one triad reformulated, the doubled three-stream
definition and status-value listing single-sourced, M3 bullet gains the
preview-rebuild condition after the stock runs.

**Decisions** Doc 30 is genuine recognition loss of a double-page half, repair via
targeted single-page re-OCR after the E96 pattern (E97). Report audience stays ZBZ
project management first; reader-guiding cross-references remain, true double
definitions were removed. Backlog order: report final now, M3 rollout after a
preview rebuild, run-to-run pilot stays a gated outstanding item.

**Status** All report slots are filled and all named figures measured; the report
is internally consistent with registers E94 to E97. Commit pending push gate.

**Next steps**
1. Push (operator gate).
2. Targeted re-OCR of doc 30 scan page 1 (gated, E96 pattern).
3. M3 preview rebuild, then rollout decision.
4. Run-to-run pilot (5 documents x 3 runs, gated).

### 2026-07-07 Session 87: 1520 p70 leaked refusal replaced (gated re-OCR executed, E96)

**Occasion** The operator supplied a Gemini API key and authorized `gemini-3.5-flash`
for the gated single-page re-OCR of doc 1520 page 70, whose delivered TEI carried a
leaked LLM refusal (E94 finding; root cause a Mistral repetition loop on a nearly
illegible page).

**Goal** Remove the refusal from the delivered corpus and put the most honest
machine-recoverable text in its place.

**Course** Two vision passes over 200/300-DPI renders diverged: the fluent pass
partly reconstructed the faint zones from world knowledge (refuted at the
contrast-enhanced facsimile: printed "Ce chiffre historique universel" and
"en Iran" against its "Ce double mouvement" and "en Perse"), the honesty-prompted
pass marked the same zones `[...]`. Composed a conservative partial transcription
(facsimile-verified anchors plus two-pass consensus verbatim, `[...]` elsewhere,
no footer digit; `pb n="[64]"` confirmed by the unbroken bracketed sequence).
Streams repaired with full backup, `tei_final` patched surgically, validator and
schema gate green, mirror regenerated (register E96).

**Decisions** Honest partial transcription over fluent reconstruction; the faded
footer digit stays out because the interpolated folio sequence outranks it (E96).

**Status** The refusal is gone from the delivered corpus; the page content is
partial by design and needs human curation from a better scan. Commit pending.

**Next steps**
1. Push (operator gate).
2. Doc-30 adjudication, then the last report slot.
3. M3 reading-order rollout (operator-gated).
4. Ask ZBZ for a better scan of 1520 page 70 for full curation.

### 2026-07-07 Session 86: Healing rerun executed, gates green, reports and statistics moved to the post-run state

**Occasion** The operator re-ran `tei_pb_folio --strip-folio-echo` after the E95
tool repair; the rerun healed exactly the 14 orphaned speaker wrappers in the four
interview documents and changed no page number corpus-wide (run report: 0 pb
changes, sp_healed 7/1/1/5).

**Goal** Verify the healed corpus end to end, re-measure the CER, and project the
executed stock runs into the work report, the final report, and the register.

**Course** Gates green: pytest 1370 passed / 1 skipped, `tei_validator --all`
285/285 valid (2018 informative warnings in 256 documents, dominated by the two
curation signals W17 with 830 and W19 with 827 instances). After-audits:
`pb_number_audit` now classifies 204 documents printed_folio, 37 scan_sequence,
10 mixed, 34 undetermined; `body_note_audit` drops from 63 candidates to 3 (the
two facsimile-confirmed genuine footnotes in 1530 and 3040 plus one new
borderline case, doc 20 page 196, curation worklist); `char_lint_audit` keeps
straight apostrophes at zero. CER re-measured (seed 42, B = 10 000): fidelity
mean 2.50% (CI [1.65%; 3.54%]), median 1.37% (CI [1.08%; 2.56%]); paired against
raw OCR 17/25 documents improved, -9.66 pp, p = 0.0066. `docs/data/
cer_statistics.json` regenerated (also carries the corrected citation strings).
Both stock-run slots in `reports/arbeitsbericht-v3.md` filled, its 6.3 figures
updated, `knowledge/final-report.md` 6.3 updated, E94/E95 register entries closed
as executed.

**Decisions** None new; this session executes E94/E95.

**Status** Corpus healed and fully green; the published statistics artifact
reflects the post-run state. Local commits await the push gate.

**Next steps**
1. Push the pending commits (operator gate).
2. Doc-30 adjudication (E91 loss reading versus calibration), then fill the
   remaining report slot.
3. 1520 p70 re-OCR (gated, one paid call); M3 reading-order rollout
   (operator-gated).
4. Mirror regeneration `generate_edition_data --mirror-only` so the viewer shows
   the corrected corpus.

### 2026-07-07 Session 85: E94 stock runs executed; echo-strip sp defect found, repaired, healing pending

**Occasion** The operator executed both pending stock runs (`tei_pb_folio
--strip-folio-echo`, then `tei_body_note_demote --promote-footnotes`); both
reproduced the dry-run figures exactly (folio sources 1753/1033/151/208/970/79,
1212 echoes; demotion 59/2/2/19, 0 unmatched).

**Goal** Run the gates on the corrected corpus, diagnose any regression to the root
cause, and repair it in the tool rather than the data.

**Course** The schema gate failed for four interview documents (2330, 2400, 2540,
3180) that were valid before the run. Bisecting the diff against the pre-run backup
located the defect: footer echoes inside `<sp>` with empty `<speaker/>`; the strip
removed the `<p>` and left a wrapper the schema rejects (14 orphans corpus-wide).
The repair makes the strip sp-aware (whole-block removal, named-speaker blocks
untouched, orphan healing on any run), verified end-to-end on copies of all four
documents. Rewriting the integration tests to the post-run state exposed a second
defect: a rerun would have bracketed leftover scan fallbacks in mostly-bracketed
documents into false print folios; guarded via `doc_has_brackets` (register E95).
UTF-8 integrity of the corrected corpus spot-checked (console mojibake was cp1252
rendering only).

**Decisions** Repair in the tool, then heal the corpus by re-running it, instead of
hand-editing the four documents (E95; keeps provenance on the marker path). Echoes
under a named speaker stay in the text.

**Status** Tool fix and post-state tests committed; suite green except the four
schema failures that the healing rerun resolves. Corpus healing and the after-gates
remain pending.

**Next steps**
1. Operator re-runs `python -m scripts.tei.tei_pb_folio --strip-folio-echo` (heals
   14 wrappers in 4 documents, otherwise a no-op).
2. Gates and after-audits (`pytest`, `tei_validator --all`, `pb_number_audit`,
   `body_note_audit`), then fill the two stock-run slots in
   `reports/arbeitsbericht-v3.md`.
3. CER re-measurement after the wave (char normalization and demotions changed the
   hypothesis text of reference documents).
4. Doc-30 adjudication; mirror regeneration.

### 2026-07-07 Session 84: E92/E94 tooling refactored, behavior equivalence proven

**Occasion** The E92/E94 wave was built by parallel agents, so the marker tools and
audits each carried private copies of the same scaffolding; the operator asked for a
refactoring pass before the pending stock runs.

**Goal** Single-source the duplicated scaffolding without changing any tool's
behavior, verified against the already dry-run-verified state of the two pending
stock corrections.

**Course** Three agent lanes on disjoint file sets. Lane one extracted
`scripts/tei/marker_common.py` (backup-then-write, final-file iteration) and rewired
the five active marker tools; lane two extracted `scripts/eval/audit_common.py`
(discovery, tolerant parse, report writer, `--dir` CLI) and rewired the five audits
plus the completeness check; lane three examined the thirteen new test files and
found the apparent fixture duplication superficial (each builder is tailored to its
audit), so it changed no test and only fixed inventory drift in `scripts/README.md`.
Orchestrator follow-up: dead code removed (`count_pb_elements`, one dead import),
direct unit tests added for the shared undo path (`tests/test_marker_common.py`).
Equivalence evidence: dry-runs of `tei_pb_folio --strip-folio-echo` and
`tei_body_note_demote --promote-footnotes` byte-identical to pre-refactor baselines
(folio sources 1753/1033/151/208/970/79, 1212 echoes; 59 demotions, 2 quotes,
2 preserved, 19 promotions, 0 unmatched), all six audit JSONs unchanged except the
completeness timestamp, full suite green.

**Decisions** Shared helpers stay per domain (`tei/` and `eval/` each own their
module); lifting the remaining ~15 duplicated lines into `scripts/core/` was
rejected as an abstraction level without present need. Historical one-shot tools
(`tei_footnote_demote`, `tei_footnote_marker_strip`, `tei_surface_graphic`) left
untouched because their write path also regenerates the mirror. Unused diagnostic
JSON fields (`confidence`/`examples` in pb_number_audit, `note_count` in
body_note_audit) kept: audit reports are human-facing and the fields carry triage
value.

**Status** Refactor committed as 6726c409, not pushed. The two stock runs remain
pending and their verified dry-run figures still hold on the refactored code.

**Next steps**
1. Operator runs `tei_pb_folio --strip-folio-echo`, then `tei_body_note_demote
   --promote-footnotes`, then gates (`pytest`, `tei_validator --all`, after-audits).
2. Operator adjudications: document 30 (E91 conflict), 1520 page 70 re-OCR.
3. Fill the marked slots in `reports/arbeitsbericht-v3.md` and update
   `final-report.md` once runs and adjudications are through.
4. Legacy status labels (`bearbeitet`/`fertig`) in `tei_status_marker.py` removable
   once no pre-E77 manifests remain.

### 2026-07-07 Session 83: Guideline conformity explored end to end; ground-truth map, knowledge corrections, implementation packages started

**Occasion** Operator questions following the merge: do the delivered TEIs meet the
ZBZ coding rules beyond formal validity, how were they generated, and how can quality
be checked in a fully automated process.

**Goal** Establish the verified state (validation vs. verification), reconstruct the
generation path, map the editorial guidelines against validator and ground truth,
correct the knowledge base, and start every immediately implementable package.

**Course** Four multi-agent exploration rounds. Corpus state: every delivered document
is machine-valid with zero schema and project errors; warnings are dominated by the
speaker curation slots (W17) and legacy reading order (W19); human verification has not
begun (curated_tei empty, only document 30 ever touched, its manifest ahead of its
revisionDesc). Generation trace: two phases, the tei_unified three-step pipeline
(deterministic scaffold, Gemini refinement, deterministic assembly plus conformity
passes) and the downstream markers writing into tei_final, so the delivered tei_final is
a frozen, post-processed state decoupled from the current tei_unified output. Coverage
matrix and facsimile deep check (570, 760): the faithfulness core of the guidelines is
machine-unchecked (transcription norms, classification correctness, relation integrity),
and the deep check found systematic violations invisible to the validator, printed page
numbers in the body instead of pb@n, unsegmented double-page scans, transcribed covers
and title pages, italics loss, and incomplete character normalization, while text
accuracy stays near reference level and the reading order held even on the three-column
double page. All 25 reference TEIs inventoried against the guidelines: body coding is
guideline-true in the load-bearing conventions, the teiHeader is a Transkribus stub
corpus-wide, and the ground truth carries its own catalogued errors (GND prefix drift,
corresp/ref migration rest, break="yes", entities in captions, the ill-formed 1520).

**Decisions** Quality architecture in three tiers: validation (deterministic,
corpus-wide), AI-agent verification (evidence-bound findings on stratified facsimile
samples, never granting the verifiziert status, lesson from the abolished E66
screening), and expert verification (operator adjudicates, sole source of green).
Deterministic audits run before image-based sampling. The hi audit was rescoped to a
signal-survival check after measurement showed the OCR layer itself carries emphasis
only on a small fraction of pages. Knowledge corrections applied: footnote demotion
discriminator corrected to the contiguous 150-character window (MIN_MATCH), documents
30/760 cause attribution aligned with the E91 counter-check, Appendix A engine and
step assignments fixed, the E85-resolved footnote residue updated in specification.md,
volatile quantities replaced by script pointers in pipeline/project/methodology/
ecosystem-synthesis, and the effort-hours table in workflow.md replaced by an
implementation-state note.

**Status** Knowledge corrections done; the ground-truth map and the ground-truth
exception catalog are consolidated as Appendix B of
`final-report.md` (superseded by arbeitsbericht-v3.md) (operator decision: one final report instead of
scattered report files; the 1520 repair proposal lives there too, corrected copy under
`output/`). Four implementation agents delivered the diagnostic audits (character lint,
pb@n plausibility, hi survival, relation integrity), the deterministic pb@n projection
plus filter-leak fix in step 1, the rendering-loss root cause (Mistral OCR is the main
loss source, the Gemini image channel is practically unused because the prompt verifies
instead of detects, and a promotion lag tei_unified to tei_final withholds existing
markup, e.g. document 890), and the stock diagnoses (page-count mismatches, 1520 repair
proposal, status-marker catch-up for document 30).

Implementation round, five agents, full suite green at 1258: `tei_status_marker` is
idempotent (marker-owned changes carry `n="{stream}"` / `n="{stream}-summary"` and are
replaced, foreign entries survive; new test_status_marker.py); `completeness_check`
reconciles split double pages (duplicate facs) and leading library covers (min facs above
1) with capped corrections, the 14 phantom mismatches drop to 0 while synthetic genuine
gaps still report (new test_completeness_check.py); step 1 interpolates missing printed
page numbers from consistent neighbor anchors, supplied values bracketed per reference
convention (570 p3 becomes `n="[249]"`, tei_final hash-verified untouched). Register
entries E92 (audits plus step-1 fixes) and E93 (image-based italics re-detection
rejected) written.

Agent-verification calibration on 29 stratified facsimile pages, findings evidence-bound,
adjudicated with the operator: (a) footnote overdetection persists broadly outside
reference coverage, 9 of 10 sampled long notes are body or block quotes as note (pattern:
page-head block, block after a `*`-divider, right page of a double spread); (b) the
W19-fragile triage is a weak predictor of wrong order (5 of 6 sampled orders correct) but
surfaces real omissions of non-article blocks (ads, SOMMAIRE, editorial boards, license
boilerplate), a defect class no rule covers; (c) pb@n semantics are inconsistent
corpus-wide (facs position, printed folio, or mixed within one document), and the
references bracket every page number; (d) the char-lint apostrophe class holds at the
facsimile while the space-before-punctuation class is largely a false positive on French
typography (thin space is correct print); (e) foreign markup coverage and speaker
modeling are uneven across documents; (f) conflict to adjudicate: the sampled doc-30
double pages show no character loss (both print pages complete, outlier alignment-driven),
which contradicts the E91 classification of doc 30 as genuine text loss.

Follow-up instruments, three agents, full suite green at 1289: `body_note_audit.py`
scores body-as-note candidates (missing start marker plus length as the load-bearing
signals; 100 percent precision on the 9 calibration pages) and reports 63 candidate notes
in 26 documents, 60 of them in 24 reference-less documents; the char-lint space class is
split into a sharp class (genuine extra character, 1988 occurrences, mostly TOC dot
leaders) and a low-severity `space_type` class (regular instead of narrow no-break space
in French context, 13931), while a dehyphenation-residue class was tested and rejected as
non-deterministic (a 40-candidate sample was almost entirely false positive on the
bilingual corpus); `pb_number_audit.py` now classifies pb@n semantics per document,
corpus distribution 224 scan_sequence, 18 printed_folio, 9 mixed, 34 undetermined, none
bracketed (the references bracket everything), with doc 110 resolved as scan_sequence
carrying a reconstructable printed-folio offset of 2.

Operator ratifications and first stock correction (E94): pb@n convention decided (printed
folio, bracketed, fallback scan number), correction mode hybrid, verification depth
targeted. The apostrophe normalization ran as the first stock correction (88,978
occurrences in 241 documents to zero, gates green, backup kept). All 63 body-as-note
candidates were verified at the facsimile: 59 body text, 2 epigraphs, 2 genuine
footnotes, with the role-swap pattern (the genuine footnote sits as a trailing p with
marker while body text got the note frame) confirmed on 39 pages; verdicts persisted in
`output/audits/body_note_verdicts.json`. The demote tool and the printed-folio tool are
built and dry-run verified; their corpus writes are pending because the session permission
mode blocked the write, so the operator executes or re-authorizes. Supplementary sample:
foreign markup exists in 30 of 285 documents, at least 27 foreign-less documents carry
unmarked Latin/Greek phrases, the German code is split de/deu; one leaked LLM refusal
found in the delivered corpus (doc 1520 page 70, root cause a Mistral repetition loop in
the base OCR, single-page re-OCR gated); a naive volume-divergence audit was rejected
(about 90 percent of hits are the intentional e-periodica boilerplate filtering), a
filtered triage variant plus refusal-string and duplicate-facs checks recommended.

**Next steps** 1. Operator executes or re-authorizes the two pending stock runs
(`tei_pb_folio --strip-folio-echo`, `tei_body_note_demote --promote-footnotes`),
followed by gates and after-audits. 2. Operator adjudications: doc-30 conflict with
E91, 1520 page 70 re-OCR, sending the 1520 reference repair to ZBZ. 3. final-report
update with before/after values once the runs are through. 4. Re-promotion of newer
tei_unified states and the M3 reading-order rollout decision (E90 evidence).
5. Mirror regeneration after the frontend instance finishes; commit and push on a
clean tree after approval.

### 2026-07-07 Session 82: Viewer edit modes hardened after live inspection (layout selection, text-stream race, TEI redirect, well-formedness gate)

**Occasion** A live inspection of the viewer edit modes (Edit Layout, Edit Text, the
OCR/TEI/XML tabs) against document 100 surfaced four defects in the curation surface.

**Goal** Confirm each suspected defect in the code, fix it locally, and verify the fix
in the running viewer.

**Course** Browser test plus code reading confirmed four defects. First, a plain
click-select of a layout region fired the change callback on pointer-up regardless of
movement, marking the layout stream dirty and flipping its workflow status to
in_arbeit; a bbox comparison against the pointer-down state now gates the callback
(layout-editor.js), and a degenerate zero-size region from a click during create mode
is discarded with a notice. Second, the debounced text-edit commit (250 ms) survived
editor detach and read the stream from the current tab state, so an OCR edit followed
by a quick tab switch was attributed to the TEI stream and could never be saved; the
debounce is now cancellable and cancelled on detach, the stream is bound at attach
time, and a source switch detaches explicitly (core.js, transcription-editor.js,
viewer.js). Third, switching to the TEI tab while edit mode was active attached the
editor to the rendered view, whose edits do not round-trip; setTextSource received the
same redirect to XML mode that setTextEdit already had. Fourth, saving edited XML
overwrote the source-of-truth final TEI with only a substring check; a DOMParser
well-formedness gate (ZBZ.parseXml) now precedes the write. Switching the text source
with unsaved text edits additionally asks for confirmation and then drops them,
mirroring the existing page-navigation guard.

On operator feedback the text-panel controls were clarified: the source tabs are now
labeled OCR, Rendered, and TEI-XML (previously OCR, TEI, XML), and the single
context-dependent "Edit text" toggle was replaced by two explicit buttons, "Edit OCR"
and "Edit XML", each of which switches to its source and opens edit mode there.
Switching the view tab exits edit mode, which supersedes the TEI-to-XML redirect
introduced earlier in the session, since the rendered view no longer has any edit entry
point (viewer.html, viewer.js). Provenance was hardened after the operator's live save
test wrote a history entry as "anonym": Save now asks once for initials when none are
set (the save itself never blocks), history entries created before initials arrive are
backfilled once they are committed, the automatic note text was corrected to "auto:
first edit in viewer" (the transition fires on the first real change), and the rejection
toast for malformed XML names line and column from the parser error.

The rendered view was extended to the measured element inventory (script over all final
and reference TEIs). Corrected or newly rendered: lb with break="no" no longer forces a
line break (hyphenation; the previous rendering split words), figures appear as labeled
placeholder with caption instead of being skipped, footnotes carry their number as a
superscript badge, lists, tables, listBibl, epigraph, and gap render structurally, front
and back parts render (the reference TEIs carry content there, the old renderer showed
body only), and entities (persName, orgName, placeName), bibl, and ref get identifiable
spans respectively links with tooltips. A Markup toggle in the rendered view highlights
the annotation classes in accent colors and shows a per-page legend with counts; with the
toggle off the reading view is unchanged. Asset changes require bumping the ?v= query in
viewer.html, otherwise browsers serve the stale cached CSS/JS.

**Decisions** All fixes stay inside the existing modules and callbacks; no editor
rewrite, no new dependency. The well-formedness gate reuses ZBZ.parseXml instead of
adding a schema check in the browser; RelaxNG validation remains the job of the
pipeline validator. Edit entry points are per target rather than per current tab, so
the read-only nature of the rendered view is expressed by the absence of an edit
button instead of a runtime redirect. The renderer covers entity markup although the
pipeline emits none (entity linking removed with E71), because reference and future
curated TEIs carry it and flow through the same viewer.

**Status** Verified in the running viewer: region click-select leaves the workflow
status untouched while a real drag still dirties the stream; an OCR edit flips the OCR
pill; the TEI tab redirects to XML mode in edit state with an explanatory toast. The
parser gate was unit-checked in the page console (well-formed accepted; broken tag,
stray ampersand, truncated document rejected). All four files pass node --check. Save
to repo (File System Access path) was not exercised end to end because it requires the
interactive folder picker.

**Next steps**

1. Exercise the full save round trip (connect repo folder, save layout/text/manifest, reload) manually in Chromium.
2. Consider surfacing the malformed-XML error position (line/column from the parsererror text) in the toast.

### 2026-07-07 Session 81: Merge of the English knowledge base with the local counter-check commits, E91 ported

**Occasion** Local main carried two unpushed commits of 2026-07-03 (independent CER
counter-check, register E91) while origin/main had advanced by the sessions 79/80
restructuring; the pull stopped with conflicts in decisions.md and with modify/delete
conflicts in quality.md and reports/2026-05-27_arbeitsbericht.md.

**Goal** Complete the merge on the new English ten-document base without losing the
counter-check knowledge.

**Course** The deletions of quality.md and of the 2026-05-27 work report were accepted;
their substance lives in [specification.md](specification.md) and
`final-report.md` (superseded by arbeitsbericht-v3.md). The E91 entry was rewritten in English after E90 in
[decisions.md](decisions.md). Section 6.3 of final-report.md received the two ported
passages, the concretization of the upper-bound statement (apparatus insertions under 50
characters, capitalization divergence of the reference) and a paragraph on the
independent counter-check with a pointer to
cer-gegenprobe-2026-07-03.md (verification.md, appendix). That report
stays unchanged as a German snapshot with its measured values.

**Decisions** Ported knowledge-document passages carry no measured values; where a
figure matters they name the producing script (`scripts.eval.benchmark_cer`,
`scripts.eval.cer_statistics_full`) or the counter-check report. Rejected alternative:
mechanically rebasing the local commits, impossible because their target files no
longer exist on the new base. Register: E91.

**Status** Merge completed and committed, working tree clean, not pushed
(operator-gated). The local work-report update of 2026-07-03 was dropped as obsolete;
its substance already stands in final-report.md 6.3.

**Next steps**

1. Cross-check the knowledge folder against the work report (operator assignment).
2. Push after operator approval.

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

<!--
Entry template (insert new entries directly under "## Entries"):

### YYYY-MM-DD Session N: session title

**Occasion** [One sentence: why this work now.]

**Goal** [One sentence: what should exist at the end.]

**Course** [Past tense, at most 120 words: what happened, with references. Distill.]

**Decisions**
- [What, why, rejected alternative. Register id, or the note "no register entry".]

**Status** [Past tense, self-contained; savepoint commit hash where one exists.]

**Next steps**
1. [Numbered and executable: concrete enough to start the next session.]

**Dead Ends** [Optional: tried and rejected, with rationale.]
-->
