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
related: [decisions, journal-archive, plan, index]
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
[journal-archive.md](journal-archive.md) and leaves one compact line in the archive block
below, carrying date, session number and title, the decision ids taken, the key figures
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

Sessions 69 to 96 moved to [journal-archive.md](journal-archive.md) on 2026-08-21 by
operator decision, each leaving one compact line in the archive block below; sessions 1
to 68 remain in that block as they are.

## Entries
### 2026-08-21 Session 97: repository refactoring, diagnosis and wave 0 (E120)

**Occasion** Operator question whether documentation and code of the repository are clean. Six read-only audits by Opus agents (README and CLAUDE.md inventory, knowledge overlap and staleness, reports and static pages, scripts layout and coupling, frontend, code hygiene and tests) answered it with a catalogue of stale statements, duplicated facts, stale published figures, layout coupling and half-introduced tooling.

**Goal** Record the diagnosis as an executable plan and carry out the corrections that need no structural decision.

**Course** The plan [refactoring-plan.md](refactoring-plan.md) holds the findings digest D1 to D10, the work packages WP0 to WP7 with exclusive file sets, the waves, the verification protocol and the open operator decisions. Wave 0 ran as two parallel build agents with disjoint file sets. WP0a corrected stale statements in README, CLAUDE.md, scripts/README.md, twelve knowledge documents and the two static pages; on methode.html eight CER figures and the regeneration date were reset from `docs/data/cer_statistics.json`, and the interval label now follows the JSON's `ci_method` (percentile). WP0b declared the 37 deliberate ruff findings (character tables of the normalization, warning filters before SDK imports) as per-file ignores, applied the safe auto-fix (368 to 147 findings), fixed the CWD-relative scan path in `generate_entity_overview`, declared `openpyxl`, unified `.env` loading on `scripts.config`, removed the dead `compute_proxy_quality` together with the `--proxy` flag, and deleted `tei_add_revision.py`, the screening-era writer of the abolished `revisionDesc` certification (E66) that `tei_status_marker` strips. Verification by the orchestrator on disk: 2149 tests passed and 1 skipped (the two missing cases are the deleted script's health cases), ruff 147, all 77 `python -m` commands in CLAUDE.md resolve with their flags, `docs/data` diff empty, benchmark JSON identical under a masked timestamp.

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
