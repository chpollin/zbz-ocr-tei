---
title: Verification
project:
  name: zbz-ocr-tei
  repository: https://github.com/chpollin/zbz-ocr-tei.git
method:
  name: Promptotyping
  url: https://dhcraft.org/Promptotyping/
template:
  name: Vorlage Verification
  version: 0.1
  url: https://dhcraft.org/Promptotyping/promptotyping-document/verification
status: complete
language: en
version: 1.0
created: 2026-08-21
updated: 2026-08-21
scope: [empirical-claims]
verdict-vocabulary: see section Verdict vocabulary
authors: [Christopher Pollin]
related: [index, specification, methodology, tei-mapping, project, pipeline, decisions, journal]
absorbed: [testing (Vorlage Testing 0.2)]
---

# Verification

This document carries two functions that answer to the same standard of evidence; the
automated test suite checks system behaviour against the specification, and verification
checks whether the empirical claims the project carries outward are covered by the raw data.
The verification part holds each such claim, the evidence behind it, the procedure that
produced that evidence, and what remains open. Lesson L13 of [journal.md](journal.md)
fixes the standard that part works to. A figure written into prose, "285/285 valid" being
the original case, is no evidence, so every claim named here is bound to a regenerable
artifact or to an automated gate.

## Quality assurance (test suite)

This part describes the automated test suite that fulfils the gate requirement of
[specification.md](specification.md). It states what the suite guarantees about the
delivered data, which part of it survives a fresh clone, which classes of defect it
deliberately leaves uncovered, and how it is run. The requirement itself and the mapping of
gate to requirement id stay in specification.md; the invocations stay in CLAUDE.md.

### Test strategy

The suite has two layers with different evidential value. Contract tests build synthetic
input in `tmp_path` from the shared builders in `tests/conftest.py` and pin the behaviour
of one unit or of a short chain, so they hold on a checkout without any pipeline output.
Corpus gates parametrize over the delivered data under `output/tei_final/` and over the
tracked mirror in `docs/data/`, so they measure the artifact that goes to ZBZ rather than a
fixture. Both layers use pytest as the only runner. `pyproject.toml` sets
`--strict-markers`, so a misspelled marker fails the run instead of silently deselecting
tests.

Two markers separate the layers and make the clone blind spot addressable.
`requires_corpus` marks what needs the gitignored delivered corpus and therefore vanishes
on a fresh clone. `requires_mirror` marks what reads tracked repository data, the
`docs/data` mirror and the curated entity snapshots under `data/entities`, so it still runs
after a clone while depending on committed artifacts rather than on fixtures. The subset
reported as clone-safe excludes both markers, which is the stricter reading and counts only
what synthetic fixtures carry.

The suite also serves as the behaviour-preserving anchor set of a refactoring wave. An
anchor run records the full suite result, `ruff check scripts tests`, the resolution of
every `python -m` command in CLAUDE.md, an empty git diff under `docs/data/` after mirror
regeneration, the JSON hashes of the CER benchmark and of the entity corpus scan, and the
validity verdict of `tei_validator --all` over the whole delivered corpus. After the wave
the same set is produced again and compared. The process around such a wave, including the
verification of agent self-reports against disk, is in
[methodology.md](methodology.md), governance section.

### What is guaranteed

The following properties of the delivered data and of the tools that produce it are pinned
by a test and fail the build when they break.

- Schema validity of every document in `output/tei_final/` against `data/schema/zbz_hersch.rng`, together with the data-independent pins of the schema itself, the E68 header elements, the inline GND model, the rejected standOff register and the GND pattern on `@ref` of all four name-bearing elements (`tests/test_tei_schema.py`, E127).
- The delivery contract of the produced `teiHeader`, meaning `idno` of type docID, `biblStruct` with analytic, monogr and imprint, and `langUsage` (`tests/test_tei_header.py`).
- The ZBZ conformity rules over the delivered corpus and the generator fixes behind them (`tests/test_zbz_conformity.py`, `tests/test_tei_conformance.py`).
- The project rules of the validator, errors R1 to R7 and warnings W1 to W7 and W11 to W18, each with one firing fixture and one silent counter-fixture that carries the same construct in correct form; W19 is covered through `tests/test_tei_validator.py` (`tests/test_tei_validator_rules.py`).
- Corpus invariants and the delivered distribution over the funnel from Masterfile to final TEI, together with the known completeness gap as an exact document list (`tests/test_corpus_audit.py`), and the page-count reconciliation rule that neutralizes split double pages and leading cover leaves (`tests/test_completeness_check.py`).
- Determinism of the CER statistics, the bootstrap and paired-difference machinery, HCPR, and the extraction and normalization rules indexed to the catalog of [methodology.md](methodology.md), CER measurement section (`tests/test_cer_statistics.py`, `tests/test_cer_extraction.py`).
- The deciding side of two thresholds that were pinned on one side only, the doubling of the two-sided bootstrap p-value and the number of field lines at which the entity matcher reads a first page as a library cover sheet (`tests/test_guard_pins.py`).
- The step-1 scaffold plus assembly as an end-to-end contract without any API call, asserting `pb` numbering, region-to-paragraph mapping, facsimile zones and RelaxNG validity of the assembled document (`tests/test_step1_assembly.py`).
- The step-2 repair path on malformed model output, including the guard that refuses an empty or whitespace-only answer instead of replacing the page scaffold with nothing (`tests/test_tei_step2_repair.py`).
- The closed world of the entity layer, meaning every GND id that reaches the viewer through the generated mirror compared as a raw string against the curated list, so a formatting drift fails as loudly as an unknown id (`tests/test_entity_ref_invariant.py`).
- The adjudicated mention verdicts as a regression gate against the current corpus scan (`tests/test_entity_verdict_guard.py`, `tests/test_mention_verdicts.py`).
- The blank-page rule and its projection as `<pb type="blank"/>`, together with the idempotence of the shared marker scaffolding, so a second run produces no duplicates (`tests/test_blank_marker.py`, `tests/test_marker_common.py`, `tests/test_status_marker.py`).
- The document-field contract of the catalog against the keys the frontend reads, the aggregated manifest index, and the agreement of the workflow status tokens between `page_manifest`, `tei_status_marker` and the viewer JavaScript (`tests/test_catalog_contract.py`, `tests/test_manifest_index.py`, `tests/test_workflow_status.py`).
- The facsimile binding, meaning surface and graphic completeness in the delivered TEI and the text-page to scan-image resolution of the mirror (`tests/test_tei_surface_graphic.py`, `tests/test_facs_mapping.py`).
- Syntax and internal imports of every module under `scripts/` (`tests/test_scripts_health.py`).

### Acceptance

[specification.md](specification.md) owns the mapping from check to requirement, and its
gate table names which check answers which requirement. A change is acceptable when those
gates pass and, where the change was meant to preserve behaviour, the anchor set named in
the strategy section is unchanged.

Continuous integration runs the gates on every push and pull request.
`.github/workflows/tests.yml` defines a single job on Ubuntu with Python 3.11, materializes
the dependency list from the `[project] dependencies` block of `pyproject.toml` plus the
`dev` extra, installs it with pip, then runs `ruff check scripts tests` followed by
`python -m pytest tests/ -q`. The heavy layout engines are the separate `layout` extra and
stay uninstalled in CI. Corpus-dependent tests skip themselves on the fresh checkout, so
the CI signal is the clone-safe subset while the local run is the full one. The `dev` extra
pins ruff to one version and `.pre-commit-config.yaml` reuses that pin in a local hook, so
hook and CI report the same findings. Deployment and repository topology are in
[pipeline.md](pipeline.md), deployment section.

### What is deliberately not checked

The guarantee above is bounded. The following classes lie outside it, and a green suite
says nothing about them.

Stamps, shelf marks and catalogue notes that land in running text have no check, since no
validator rule and no audit detects that class. Neighbouring classes do have deterministic
instruments, E-Periodica cover sheets through `tei_cover_strip`, running heads through
`running_head_audit` and the shared detection core, folio echoes through
`pb_number_audit`, and the entity matcher excludes apparatus zones; none of these reaches
library apparatus inside the body text.

Two latent defects are recorded and left unfixed; in both cases the suite pins the state
as it stands instead of the correct behaviour. `serialize_tei_fragment` drops the
namespace declaration of a foreign-namespace element and returns an unparsable fragment,
and no corpus impact is known. The catalog JavaScript carries a fourth status token
`ausstehend` that exists in the UI layer alone and in no data model, so the status
contract test pins the three data values and tolerates the fourth. Both are recorded in
[decisions.md](decisions.md) E123.

Behaviour under a missing corpus is checked only to the extent that the marked tests skip.
Whether a script degrades usefully when `output/` is empty stays untested.

Content of language-model output is asserted nowhere. Step 2, the layout QA and the OCR
correction are non-deterministic, so the tests pin the repair path and the guards around
the call instead of the answer. Run-to-run variation is a measurement question and belongs
to the verification part below, which holds the stability pilot.

Visual correctness of the viewer sits outside the suite. The frontend is covered by a
headless browser check during a refactoring wave, which finds console errors, failed asset
requests and broken interactions; whether a rendering looks right stays a human judgement.

### How to run

The command reference is CLAUDE.md, section Diagnosis, which is the single source of the
invocations and lists the gates individually. The whole suite runs as `python -m pytest`.
Two marker expressions address the layers.

```bash
python -m pytest -m "not requires_corpus and not requires_mirror"   # clone-safe subset
python -m pytest -m "requires_corpus"                               # delivered-corpus gates only
```

Locally the ruff gate runs through the pre-commit hook declared in
`.pre-commit-config.yaml`, which installs its own pinned ruff and checks staged Python
files. Formatting is deliberately outside the hook, because the tree has never been
ruff-format-clean and reformatting it would bury real diffs. Tests do not run on commit;
the CI job is the enforcing instance.

### Pattern: test in the same commit

Non-trivial logic leaves a runnable check behind in the commit that introduces it. A bug
fix carries the test that reproduces the reported symptom, written against the shared
function every caller routes through rather than against the reporting call site. Trivial
one-liners need no test, and exploratory code needs none until it is committed to the main
branch, imported by another module, or its output feeds downstream processing; from that
point the rule applies retroactively.

An operator-gated stock correction over `output/tei_final/` follows a stricter form. The
tool ships with its contract and idempotence tests, a dry run precedes the real run, the
run writes a backup, and the matching audit plus `tei_validator --all` plus the pytest
gates run again afterwards, so the before and after state is measured rather than asserted.

### TDD workflow and anchor strategy

The failing test precedes the implementation, the code is written to make it green, and the
refactoring happens while it stays green. Where a format string or a serialization is about
to change, the test is written against the current output first, so the diff shows the
intended change and nothing else.

For a structural change that must preserve behaviour, the test suite alone is
insufficient, because a moved module can keep every unit green while a generated artifact
drifts. The anchor strategy closes that gap over the anchor set named in the strategy
section. Its JSON hashes are taken with the wall-clock `generated` key removed, so a hash
depends on content rather than on run time, and the mirror is regenerated before the change
to establish an empty git diff as the baseline. After the change, both hashes must match and
`generate_edition_data --mirror-only` must again leave `docs/data/` with an empty diff.
Where a generator legitimately changes its output, the deviation is named and accepted in
the register entry instead of being absorbed silently.

### Known exceptions and limits

Tests that need the delivered corpus or tracked repository data carry a skip guard beside
their marker, either a `skipif` on the test or a `pytest.skip` where the missing input only
shows at call time, so a fresh clone reports skips rather than failures while the collection
stays the same; the marker makes the class selectable with `-m`. The consequence is that
the CI signal is systematically weaker than the local one, which is the reason the
validator rules and the generator contract were rebuilt on synthetic fixtures.

Verification runs name an allowlist of scripts, and anything that writes under
`output/audits/eval_sample*` or under `data/` is excluded by name; the rule and the incident
behind it are recorded in [methodology.md](methodology.md), governance section, and the
incident itself stands in the finding register below.

`--strict-markers` means a new marker has to be registered in `tests/conftest.py` before it
can be used. This is deliberate, because an unregistered marker deselects nothing and would
let a supposedly guarded test run in an environment it cannot survive.

Lesson L1 of [journal.md](journal.md) bounds what a warning layer is worth. Validation must
be actionable; a false-positive rate above half makes a report useless, and every warning
needs a concrete action. This is why the W rules stay non-blocking curation signals and the
blocking gates are restricted to schema, header contract, corpus invariants and the closed
world.

### Components

Test modules under `tests/`, grouped by the domain of the code they cover.

Shared scaffolding sits in `tests/conftest.py`, which holds the TEI skeleton and the
delivery-shaped header, the layout bbox, the entity lexicon and record builders, the
module-level list of delivered documents that the parametrizing suites need at collection
time, and the registration of the two markers.

- core, the domain-free shared library: `test_pb_split.py` for the `<pb>` segmentation, `test_reading_order.py` for the reading-order permutation in `tei_xml_utils`, `test_page_names.py` for the page path helpers, `test_curated_loaders.py` for loader precedence on curated paths, `test_audit_common.py` and `test_marker_common.py` for the shared audit and marker helpers.
- tei, generation and delivery: `test_step1_assembly.py`, `test_step1_filter.py`, `test_tei_step2_repair.py`, `test_tei_header.py`, `test_tei_schema.py`, `test_tei_conformance.py`, `test_zbz_conformity.py`, `test_tei_validator.py`, `test_tei_validator_rules.py`, `test_tei_surface_graphic.py`.
- tei, markers and stock corrections: `test_blank_marker.py`, `test_status_marker.py`, `test_char_normalize.py`, `test_pb_folio.py`, `test_body_note_demote.py`, `test_footnote_demote.py`, `test_footnote_marker_strip.py`, `test_cover_strip.py`, `test_reading_order_fix.py`.
- layout: `test_page_xml_generator.py` and `test_mets_generator.py` cover the PAGE-XML and METS export as pure transforms.
- eval, metrics and audits: `test_cer_statistics.py`, `test_cer_extraction.py`, `test_guard_pins.py`, `test_corpus_audit.py`, `test_completeness_check.py`, `test_stability_pilot.py`, plus the guideline-conformity audits `test_char_lint_audit.py`, `test_pb_number_audit.py`, `test_hi_preservation_audit.py`, `test_relation_integrity_audit.py`, `test_body_note_audit.py`, `test_blank_text_audit.py`, `test_reading_order_audit.py`.
- edition, viewer data: `test_catalog_contract.py`, `test_manifest_index.py`, `test_workflow_status.py`, `test_facs_mapping.py`, and `test_export_web_images.py` for the JPEG web mirror of the page images.
- entity: the matcher and its rules in `test_entity_matcher.py`, `test_entity_regressions.py`, `test_running_heads.py`, `test_running_head_audit.py`; the intake and cache side in `test_entity_lint.py`, `test_fetch_gnd_variants.py`, `test_variant_review.py`; the preview and mirror generators in `test_entity_preview.py`, `test_generate_entity_preview_data.py`, `test_generate_entity_overview.py`, `test_entity_stream.py`; the corpus instruments in `test_entity_corpus_scan.py`, `test_entity_corpus_digest.py`, `test_entity_unlisted_scan.py`, `test_entity_risk_ranking.py`; the measurement and gate side in `test_entity_eval_sample.py`, `test_entity_gold_benchmark.py`, `test_entity_ref_invariant.py`, `test_mention_verdicts.py`, `test_entity_verdict_guard.py`.
- repository health: `test_scripts_health.py` compiles every module under `scripts/` and resolves its internal imports; `test_knowledge_frontmatter.py` pins the ten documents of this knowledge base, their frontmatter contract, the equal schema version, resolvable links and the absence of horizontal rules.

The OCR scripts under `scripts/ocr/` have no dedicated test module. The text layer they
produce enters the suite through the loaders and through the step-1 contract, which reads
OCR markdown from a synthetic fixture directory; the API adapters themselves stay untested.

### Current state

Snapshot of 2026-08-21. The suite passes with no skips, ruff reports no finding, and the
clone-safe subset covers the validator rules and the generator contract. The two commands
below produce the current sizes.

```bash
python -m pytest --collect-only -q
python -m pytest --collect-only -q -m "not requires_corpus and not requires_mirror"
```

The last recorded figures, together with the wave that produced this state, are in
[decisions.md](decisions.md) E123.

## Subject of verification

Three claims leave the repository and are therefore in scope.

The character error rate of the delivered text layer, measured against the reference corpus
and decomposed into fidelity and scope. The published values live in
`docs/data/cer_statistics.json`, deterministically regenerable with seed 42 through
`scripts.eval.cer_statistics_full`; the public method page and the client-facing project
report quote that file. Metric definition, extraction and normalization rules are in
[methodology.md](methodology.md), CER measurement section.

The precision and recall of the entity preview layer, measured on a facsimile-adjudicated
sample of the closed-world marking. The published block is `quality` in
`docs/data/entity_overview.json`, rendered on the entities page; the readable result of the
executed run is the evaluation result in the appendix, the aggregate
`output/audits/entity_eval_report.json`. The marking rules the adjudication judges against
are in [tei-mapping.md](tei-mapping.md).

The completeness of the delivery, meaning that every catalogued and delivered scan reaches a
final TEI apart from a named and pinned exception, and that each document's page structure
reconciles with its physical scan. The instruments are `scripts.eval.corpus_audit` and
`scripts.eval.completeness_check`, the gate is `tests/test_corpus_audit.py`. The corpus
material itself is described in [project.md](project.md), data section.

## Verification problems

Six conditions make a naive check wrong in this project, and each one shaped a design
decision of the chain below.

The reference TEIs are partial transcriptions. They omit page apparatus, neighbouring
articles and other material the pipeline transcribes, so a full-text distance charges the
pipeline for text that is correctly present. The fidelity and scope decomposition answers
this, and the fidelity value stays an upper bound of the recognition error rate because
apparatus insertions below the scope block threshold still count as error.

Page numbering drifts between reference and pipeline (L7). A pagewise comparison therefore
measures the drift rather than the recognition; content-aligned evaluation over the whole
document is immune to it.

The frozen evaluation draw of the entity layer was overwritten by a verification run and
reconstructed afterwards (E123). The current file set under `output/audits/eval_sample/` is
derivable from two frozen inputs and is a reconstruction of the original.

The refinement stages call an LLM, whose output is not guaranteed identical across runs, so
a measured difference can be run noise. The stability pilot bounds that noise for the text
effect (E100); the delivered corpus is never regenerated to obtain a measurement.

The abolished agent screening certified its own output through a built-in ignore list, so
no human stood behind its approvals (E66); every verdict scheme since then names an
adjudicating role outside the producing agent.

Documented figures age the moment the data moves. Every figure in this document therefore
carries its date and the file that regenerates it.

## Verdict vocabulary

The entity adjudication uses a five-value ballot, one value per drawn mark, in the wording
the adjudication protocol of the appendix makes binding:

- `correct`: the surface is on the page, refers to exactly the linked entity, and the span
  covers the mention
- `wrong_entity`: the surface exists but refers to a different person, organisation or work,
  or to no entity at all
- `wrong_span`: right entity, wrong extent (partial name, swallowed punctuation, split
  across unrelated words)
- `not_in_source`: the page does not carry this surface at the claimed position, so the mark
  rests on an OCR phantom
- `undecidable`: the page does not decide it, and the case goes to the operator

The recall side records every mention of a listed entity on a drawn page as `hit`,
`on_worklist` or `missed`, and every `missed` carries exactly one cause label, `lexicon_gap`
(the surface form is not derivable from list and cache), `rule_gap` (the form exists in the
lexicon world and no matcher rule reaches it) or `ocr_corruption` (the page text is garbled
at this position).

The CER side carries no per-case ballot, since its unit is a document-level number. Its
findings take four forms, and the register below uses these words in this sense:

- reproduced: an independent recomputation returns the documented value
- confirmed: a reading survives adversarial examination against the facsimile
- refuted: a proposed mechanism fails an empirical test built to detect it
- measured: a quantity previously asserted or estimated is computed

## Verification chain

The chain is ordered by what each layer proves, and three kinds of knowledge come out of it.
An exhaustively checked invariant holds for the whole stock, for instance the proof that
every assigned entity id is a member of the curated list, which a test gate runs over all
shipped artifacts. Verified single knowledge holds for the adjudicated cases, and the
reliability of the judging itself is quantified by a double assessment. Statistical inference
generalizes from a sample to the corpus and is reported only with its interval. Each
additionally verified mark moves a part of the third kind into the second, which is why
per-mention verification accumulates across runs instead of being spent on one report.

### The CER claim

Five layers stand behind the published CER values.

Hand-computed regression tests in `tests/test_cer_extraction.py` pin the behaviour
independently of any corpus result, among them the canonical formula, case sensitivity, the
absence of trimming, the `<choice>` resolution, the normalization, and the decomposition into
fidelity and scope including the character-exact sum check.

The three formerly separate CER implementations (`benchmark_cer`, `cer_statistics_full`,
`tei_validator --compare-ref`) run on shared canonical functions since E70, so all three
paths return the same number for the same document.

An independent counter-check of 2026-07-03 recomputed everything without importing repo
code, with extraction re-implemented from the specification, a second distance engine, its
own aggregation, four secondary metrics and facsimile spot checks. Its record is the
counter-check in the appendix, and the register entry behind it is E91.

Every stock repair that moves the number is verified against evidence before it is applied
and re-measured afterwards. The footnote demotion accepted a block only where a contiguous
stretch of at least 150 characters appears in the ground-truth body (E85); the doc-30
outlier was adjudicated at the facsimile before the targeted re-OCR (E97) and re-measured
after it (E98).

The stability pilot measures run-to-run variance of the refinement stage in isolated run
directories, without touching the production caches or the delivered TEI (E100). Its result
is the `stability` block of `docs/data/cer_statistics.json`.

The interval method behind every published aggregate is the document-level block
percentile bootstrap, seed 42, B = 10,000, resampling documents with replacement and
reading the 2.5th and 97.5th percentile; every aggregate of the `overall` block names it
in its own `ci_method` field. The paired comparison against OCR-only runs on per-document
differences of the fidelity CER and reports a percentile interval with a two-sided
bootstrap p-value. No BCa interval is computed for any published value. The statistics
library carries a BCa implementation that the publishing generator never calls; the label in
the published JSON was aligned to percentile in E122, and the remaining library question is a
register and planning item.

### The entity claim

The measurement runs in six phases, and the drawn sizes and results of the executed run are
in the register below.

1. Draw. `scripts/entity/entity_eval_sample.py` cuts two seeded samples from a frozen corpus
   scan, a precision sample of tier-1 marks stratified by category and rule family, and a
   recall sample of pages stratified by layout type and language. Every stratification cell
   enters the sample manifest with what was available and what was drawn. The precision output
   holds one case record per drawn mark in `precision_cases.json`, with document, page,
   surface, offsets, linked entity, rule, matched form, context excerpt and facsimile path;
   the recall output holds one record per drawn page in `recall_pages.json`, with document,
   page, language, layout type and facsimile path.
2. Adjudicate precision. Every drawn mark receives one of the five verdicts at the facsimile
   with a one-sentence reason, recorded in the adjudicating agent's own file under
   `output/audits/eval_sample/verdicts/`, so the sample stays re-checkable.
3. Adjudicate recall. Every drawn page is read exhaustively against the curated list, each
   recorded mention is compared with the pipeline output of the same page, and every miss
   gets its cause label.
4. Agreement check. A subsample of the precision cases is adjudicated a second time, blind,
   by an adjudicator who does not see the first verdicts. The raw agreement rate is reported
   next to the headline figures, and the operator breaks ties.
5. Statistics. Precision is computed over the decidable cases, with `undecidable` excluded
   from numerator and denominator, and reported with a seeded percentile bootstrap interval
   of the mean (seed 42, 10,000 resamples). The reproducible computation lives in
   `scripts/entity/generate_entity_overview.py` and, for the convention reading, in
   `scripts/entity/running_head_audit.py`; the executed run stores the interval as
   `ci95_bootstrap_percentile_seed42` in `output/audits/entity_eval_report.json`.
6. Consequences. Every confirmed error becomes a pinned regression fixture, systematic causes
   become matcher rules, variant-review verdicts or list proposals to ZBZ, and the measured
   precision per category gates the decision whether tier-1 marks are written into the
   delivered TEI corpus-wide.

Two instruments keep the judgments alive after the run. The verdict store
`data/entities/mention_verdicts.json`, built deterministically by
`scripts/entity/build_mention_verdicts.py` from the frozen scan snapshot, holds every
judgment keyed by (doc, page, surface, gid, occurrence) with the reason, the second judgment
where one exists, and a sha256 fingerprint of the TEI it was made on; a later text change
moves the fingerprint and marks the affected records stale. The regression gate
`scripts/entity/entity_verdict_guard.py` holds the store against the current corpus scan and
exits 1 on a violation, which is a vanished correct mark, a wrong mark still asserted in tier
1, or an adjudicated real mention that no longer surfaces (E110). Tier moves are reported
without counting as violations, because rule changes move marks legitimately.

### The completeness claim

`scripts.eval.corpus_audit` reconciles the Masterfile as the gold source against delivered
scans, processed OCR pages and final TEIs as a funnel and reports drift against the claims
the knowledge base states. `tests/test_corpus_audit.py` pins five invariants over the real
data, namely that the funnel is monotonically decreasing, that no final TEI exists without a
source PDF, that every delivered scan is catalogued in the Masterfile, that every page count
of the funnel stays positive, and that the known completeness gap matches an exact document
list, so a new loss and a silent closing of the gap both fail the gate.
`scripts.eval.completeness_check` works per document, reconciling the expected physical page
count against the `pb` structure of the final TEI, with capped adjustments for page splits and
leading cover leaves so that a facsimile labelling issue is not reported as a missing page,
and classifies each document as OK, MINOR, WARNING or MISMATCH. What these gates run on
and how they are invoked is in the quality assurance section above.

## Anti-anchoring protocol

Adjudication is organized so that a judgment cannot be derived from the artifact it judges.

Agents work on disjoint ranges and are instructed not to read another agent's verdict file,
so a doubtful case is decided without knowing how a neighbour decided it. A fixed subsample
is adjudicated a second time blind, and the resulting agreement rate is published next to the
headline figures, because without it the measurement has unknown reliability.

The facsimile is the only admissible evidence for a verdict, and the pipeline text is the
object under judgment. The reference TEIs are used as a trend indicator; they are partial and
internally inconsistent, so they cannot serve as the truth standard of the entity layer.

The seeded draw carries the statistical statement about the whole mark population. Beside it,
the risk ranking sorts marks by deterministic false-positive features so that further
adjudication is spent on the suspicious end of the corpus, which keeps the additional
verification adversarial instead of confirmatory.

Every agent self-report is verified against the real file state before aggregation, and the
frozen sample is read-only for adjudicators, with write access limited to a single output
file. The process side of this, the wave contract, the verbatim guardrails and the roles, is
in [methodology.md](methodology.md), governance section.

## Novelty claims

Three claims of this project are comparative, and only the first reaches outside the
repository. The fidelity CER of the delivered corpus is set against published print-OCR
values; that comparison, its sources and its caveats live in
[methodology.md](methodology.md), CER measurement section. The pipeline is compared
against its own raw OCR in a paired test over the same documents, which is internal and
free of cross-tool comparability problems. The entity layer is compared against the
reference TEIs, which yields a trend across the categories.

The first claim carries a caveat. CER values between different tools stay limited in
comparability even under a nominally identical metric, because already the transformation
of structured ground truth into comparison text is an error source when reading order is
not considered, and because the scope threshold of the fidelity decomposition changes the
value. Any citation names the threshold, the reference count and the date, as the counter-
check of 2026-07-03 established.

## Finding register

Dated findings, each with the file that carries its evidence. The decision provenance
behind them is the register in [decisions.md](decisions.md), and the session-level record
is [journal.md](journal.md).

2026-07-07, concordance of the reference corpus (three parallel readers, provenance E92).
The body coding of the references follows the editorial guidelines in the load-bearing
conventions, among them genre div types, bracketed supplied page numbers, the hyphenation
rule across page breaks, the footnote id scheme, the inline GND entity model and the
rendition vocabulary. Two restrictions hold corpus-wide. No reference fulfils the header
requirement, since all carry the raw Transkribus export stub instead of the ALMA citation, so
header comparisons against the references are meaningless. All carry the undocumented root
attribute `type="naegeli"`. The phenomenon map and the exception catalog derived from this
reading are in [project.md](project.md), data section.

2026-07-03, independent CER counter-check (E91, the counter-check in the appendix).
Every headline and per-document value of the then-current state reproduced exactly, fidelity
mean 2.71 % and median 1.40 % over the 25 reference documents, with both distance engines
agreeing on all 25 documents. The headline depends on the scope block threshold of 50
characters, so a citation names it. Content classification of the largest error blocks in all
25 documents found apparatus insertions below the threshold as the most frequent class,
which is one of the two reasons the fidelity value overstates the recognition error.

2026-07-07, doc 30 adjudicated and repaired (E97, E98). The counter-check reading of genuine
text loss was confirmed at the facsimile, and the calibration that contradicted it had
sampled pages the defect does not touch. The missing blocks all sit on the left half of the
first double page, legible on the scan and absent from every OCR stream, so a reading-order
correction could not recover them. After the targeted single-page re-OCR the document's
fidelity CER fell from 11.59 % to 0.90 %, and the corpus headline moved to fidelity mean
2.08 % and median 1.28 % (seed 42, B = 10,000), the current values in
`docs/data/cer_statistics.json`.

2026-07-07, stability pilot (E100). Five documents, three full regenerations each, in
isolated run directories. The per-document standard deviation of the fidelity CER across runs
stayed between 0.000 and 0.129 percentage points, so the refinement stage is practically
deterministic in its text effect. A side finding of the pilot is that the absolute
fidelity of fresh regenerations lies far above the delivered values, because the delivered
TEI carries accumulated corrections the pipeline caches do not reproduce, so only the
within-pilot spread is the measurement. Evidence in the `stability` block of
`docs/data/cer_statistics.json`.

2026-08-12, entity evaluation, executed run. Nine independent agents adjudicated at the
facsimile under the versioned protocol, six on precision ranges, two reading drawn pages
exhaustively, one delivering the blind second judgment; every verdict file was verified
against disk before aggregation. Precision over 293 decidable cases of 300 drawn marks is
0.952 with a seeded percentile interval of 0.925 to 0.976. Raw agreement on the 50 doubly
judged cases is 48 of 50, and both disagreements are documented and went to the operator.
Recall over 40 drawn pages covers 67 mentions of listed entities, of which 20 were marked and
17 stood on the worklist, giving a coverage of 0.552; of the 30 misses, 28 are rule gaps and
2 are lexicon gaps. Error classes and repair classes by yield are in the evaluation result
in the appendix, the aggregate in `output/audits/entity_eval_report.json` and the raw
evidence under `output/audits/eval_sample/`.

2026-08-13, convention reading of the precision figure (E105, E108). After the operator set
the page-apparatus convention, running heads left the marking scope and the second reading
became computable from the persisted verdicts without drawing again.
`scripts/entity/running_head_audit.py` computes it at 0.9511 over 266 in-scope decidable
cases, inside the interval of the protocol reading, so the running heads were not inflating
the published figure. One ground-truth caveat is recorded, since a single adjudicated mark
counts as a running head only through the keyword in its verdict reason while being body
text (doc 2510), so the keyword criterion reads detector recall as 24 of 25 without a real
head being missed.

2026-08-13, gold benchmark read as a trend. `scripts/entity/entity_gold_benchmark.py` measures
against the reference TEIs, scope-restricted to shared text. Facsimile classification of its
deviations showed that about half of them are convention differences rather than errors,
above all the corpus author in bylines, which the references leave unmarked. Read per
category the trend orders the classes consistently, persons highest, organisations in the
middle, works lowest by a wide margin, and the overall tier-1 figure stays well below the
facsimile-adjudicated precision. The weak work class is the empirical backing for keeping
works on the worklist in the first stock wave. After the guard wave the reference trend rose
to tier-1 precision 0.67 with recall and coverage unchanged, which is the expected signature
of pure false-positive removal (E109). The figure is the state at that date as the
register records it; `output/audits/entity_gold_benchmark.json` regenerates with every run
and carries the current trend.

2026-08-13, first verdict-guard run (E110), on the scan of the repaired state. All 279
adjudicated correct marks survive, 252 in tier 1 and 27 as legitimate moves to the worklist;
10 of 14 wrong marks are repaired, and the remaining 4 are text-side defects outside the
matcher's reach, an OCR phantom on a blank leaf, a hallucination loop and a generated speaker
duplication. Of the 30 adjudicated misses 27 now surface. The figures are the state at
that date as E110 records it; `output/audits/verdict_guard_report.json` regenerates with
every guard run.

2026-08-21, reconstruction of the frozen draw (E123, incident). A verification run executed
the draw script as a smoke test and overwrote the frozen evaluation sample, which the
adjudication protocol forbids. The draw was reconstructed from the frozen scan snapshot, the
matching catalog state was frozen beside it, four page values were restored from the
versioned verdict store, and the tracked verdict file was reverted, so the tracked data is
unchanged. The current sample directory is a reconstruction that is derivable from two frozen
inputs.

## Open findings and escalation

The re-freeze of the reconstructed draw is an operator decision. Until it is taken, the
sample directory stays a reconstruction and any statement about it says so.

The second draw of 2026-08-13 under `output/audits/eval_sample_2026-08-13/` is frozen and has
never been adjudicated. Every measured entity figure therefore belongs to the 2026-08-12
snapshot.

Population validity is broken for the current mark population. The anchor-free surname
release (E119) lifts bare surnames of canonical authors into tier 1 without a document
anchor, and those marks exist in no earlier draw, so the published rate no longer describes
the whole auto-marked layer even though every sampled mark still holds. The speaker-initials
rule (E128) adds a second uncovered stratum, the interview labels of three documents, which
the guard binds through the adjudicated "G.D.K." and "J.H." cases of document 2330 without
any drawn sample describing the whole stratum. Until a supplementary draw over the new
strata is adjudicated, the rate is reported per stratum, the covered one and the new ones. A fresh draw over the current population together with a recall
remeasurement on newly read pages comes before further rule work, and
[decisions.md](decisions.md), plan section, carries it as a work item. The same reasoning
applies in reverse to a change that removes marks from tier 1, with the difference that a
shrinking population keeps its rate conservative.

Targeted re-OCR stays operator-gated. The doc-30 case was executed after adjudication (E98);
any further single-page re-OCR of a tail document needs the same adjudication first and an
explicit release, and one earlier candidate was refused because its scan is not legible
enough to improve on.

The stability programme has an open second item, an inter-engine CER cross-validation with a
second OCR engine; it is released in principle and carried as planning work.

## Limits

A measured rate describes the population its sample was drawn from and says nothing about
marks outside it. Ground truth exists only for the 25 reference documents, so for the rest of
the corpus no CER is measurable and only the documented proxies apply, schema validity,
layout QA and the dictionary plausibility band.

The measured rates inform the judgment about the unverified remainder without settling it.
The decision per object stays with the human, who sets a document's workflow status per
stream in the viewer; that standing layer is described in [workflow.md](workflow.md),
workflow status per stream section.

Reference-based checks measure against a ground truth that is guideline-true in the body,
empty in the header and locally flawed, so the exception catalog belongs in every scoring
logic and phenomena the references never show can only be checked against guideline and
facsimile.

Several questions cannot be closed inside this repository. Header metadata from Alma
including the MMSID (O8) and the editorial details of the header (O13) are ZBZ decisions; the
repair of the damaged reference file is ZBZ-side; and what counts as a mention in ZBZ
editorial practice, together with list extensions derived from the recall causes, needs their
answer. While that feedback is absent, the operator decides convention questions, and each
such decision enters the register with its rationale.

## Appendix: protocols and dated results

Four dated holdings the finding register cites. They are snapshots and stay as written at their
date; the operative copies of the two protocols live beside their evidence under `output/audits/`.

### Adjudication protocol of the entity evaluation (2026-08-12)

Binding instructions for every adjudication agent. The sample is frozen; do not
regenerate it, do not rerun the corpus scan, do not modify any file outside
`output/audits/eval_sample/verdicts/`.

#### Inputs

- Precision cases: `output/audits/eval_sample/precision_cases.json` (300 cases, p001..p300)
- Recall pages: `output/audits/eval_sample/recall_pages.json` (40 pages, r001..r040)
- Facsimile per case: `docs/images/{doc}/{doc}_p{NNN}.png` (open with the Read tool)
- Pipeline output per page: `docs/data/pages/{doc}/{doc}_entity_p{N}.xml` (tier-1 wraps)
  and `docs/data/pages/{doc}/{doc}_entity_worklist.json` (tier-2 entries, keyed by page)
- Page text: `docs/data/pages/{doc}/{doc}_p{N}.xml` (pipeline TEI of the page)
- Entity list: `data/entities/all_entities.json` (persons/organisations/works,
  headword `name`/`orgName`/`title`, id field `GND_id`)
- Name variants: `data/entities/gnd_cache.json` (entries keyed by gid)

#### Precision verdicts (one per case)

Look at the facsimile page, locate the surface, decide exactly one verdict:

- `correct`: the surface is on the page and refers to exactly the linked entity
  (gid), and the span covers the mention.
- `wrong_entity`: the surface exists but refers to a different person,
  organisation or work, or to no entity at all (generic word, term, title of a
  section rather than the listed work).
- `wrong_span`: right entity, wrong extent (partial name, swallowed punctuation,
  split across unrelated words).
- `not_in_source`: the page does not carry this surface at the claimed position
  (OCR phantom).
- `undecidable`: the page does not decide it. Use sparingly and say why.

Special rule: documents 120 and 1350 carry more `pb` elements than physical pages
(duplicate facs references), so their page-to-image mapping is broken. Every case in
doc 120 or 1350 gets `undecidable` with reason "facsimile mapping defect (pb/page
mismatch, known data defect)". Do not try to guess the right image.

Surfaces may contain `<lb/>` (line break inside a name); on the page the name then
spans two lines. That is still `correct` if entity and extent are right.

Judge independently. Do not read any other agent's verdict file.

#### Recall records (one list per page)

Read the page text and the facsimile side by side. Record EVERY mention of a listed
entity on that page (persons, organisations, works from `all_entities.json`,
including name variants from the cache and obvious inflected/genitive forms).
Ignore entities that are not on the list. A blank page yields an empty list.
The author of the corpus (Jeanne Hersch, gid 118815679) counts as a mention like
any other; record it where it appears in the page body (not in running headers).

For each mention, compare with the pipeline output of the same page:

- `hit`: wrapped in `{doc}_entity_p{N}.xml` with the right gid
- `on_worklist`: present in the worklist entries of that page
- `missed`: in neither

Every `missed` gets exactly one cause label:

- `lexicon_gap`: the surface form is not derivable from list + cache (missing variant)
- `rule_gap`: the form exists in the lexicon world but no matcher rule reaches it
  (unusual inflection, split, casing) - judge by plausibility and say why
- `ocr_corruption`: the page text is garbled at this position, the clean form never
  existed in the text stream

#### Output format

Write ONLY to your assigned output file under `output/audits/eval_sample/verdicts/`.

Precision agents write a JSON list:
`[{"case_id": "p001", "verdict": "correct", "reason": "<one short English sentence>"}, ...]`

Recall agents write a JSON object:
`{"r001": {"doc": "...", "page": N, "mentions": [{"surface": "...", "gid": "...",
"status": "hit|on_worklist|missed", "cause": "<only when missed>",
"note": "<short English>"}]}, ...}`

Reasons and notes are English, compact, one sentence. Every case/page of your range
must appear exactly once. If an image file is missing, verdict `undecidable` with
the reason naming the missing path.

#### Guardrails (verbatim, binding)

- "NEVER read `.env`: the `.env` file contains API keys and must under no circumstances be read, displayed, or included in output"
- "no secrets in code or docs: API keys, tokens, and passwords live exclusively in environment variables"
- "Grokipedia is never used as a source, in any context"
- "Entity-Linking (GND/Wikidata-IDs) niemals per LLM, nur deterministische API-Lookups" (you judge existing links and record gids already on the list; you never introduce new ids)
- "No cost figures"
- "Windows encoding: no Unicode special characters in print statements"
- knowledge/arbeitsbericht-v3.md must never be touched
- output/tei_final/, data/, docs/, scripts/, tests/ must never be written; write access is limited to your single output file
- no commits, no pushes, no subagents

### Entity evaluation, result of the 2026-08-12 snapshot (German)

Methode: Verifikationskette, Entity-Anspruch (oben); Protokoll: Adjudikationsprotokoll (oben);
Rohdaten: output/audits/eval_sample/ (Manifest, Fall-Dateien, 9 Verdict-Dateien),
aggregiert in output/audits/entity_eval_report.json. Alle Urteile faksimile-adjudiziert
durch 9 unabhaengige Agenten; jede Datei gegen die Vorgabe verifiziert.

#### Gemessen (Praezision, Tier 1)

300 gezogene Markierungen: 279 correct, 5 wrong_entity, 4 wrong_span, 5 not_in_source,
7 undecidable (Seitenzuordnungs-Defekte Dok 120/1350). Praezision nach Protokoll-Lesart
ueber 293 entscheidbare Faelle: 0.952, Bootstrap-95%-Intervall (Perzentil, Seed 42):
0.925 bis 0.976. Inter-Annotator-Agreement (50 Faelle, blind doppelt): 48/50 = 0.96;
beide Abweichungen (p145 Geisterbild-Durchdruck, p193 Name im Titelslot) sind
dokumentiert und gehen an den Operator.

#### Beschrieben (nicht gemessen)

Seitenapparat-Konvention offen: nach Stichwort-Heuristik sitzen 56 der 279 correct in
Kolumnentiteln, Titelblaettern, Bylines (allein 16x derselbe Kolumnentitel in Dok 330);
Lesart ohne Seitenapparat ist erst nach Konventionsentscheid berechenbar. Fehlerklassen:
Werk/Person-Verwechslung in Bibliographie-Slots (Augustin-Roman, Schilpp-/Salamun-Titel),
UNESCO-Kommission-Kompositum (Bindestrich-Guard fehlt), kurze Werkvariante trifft
Gattungswort (Die Mauer), Split-Wrap Saint Ignace/Loyola, sp/speaker-Duplikation der
TEI-Generierung (2330/3180/2540/2400; auf 2330 S.234 erfundene Sprecherstruktur),
OCR-Halluzinationen (900 S.2 Schleife, 1520 S.130 Phantomseite), Faksimile-Versatz
Dok 680, 2300 (Verlagsdeckblatt), 1220.

#### Recall (40 Seiten, erschoepfend gelesen)

67 Nennungen gelisteter Entitaeten: 20 hit, 17 on_worklist, 30 missed (Abdeckung 0.552).
Ursachen: 28 rule_gap, 2 lexicon_gap, 0 OCR. Reparaturklassen nach Ertrag: Sprecherkuerzel
in Interviews (J.H., G.D.K., HERSCH-Labels), Byline-Ausnahme der Autorin (bewusste Regel,
4 Luecken; Hersch-Umfangsfrage jetzt mit Zahlen), Akronym-Kleinschreibung (l'Unesco),
GND-Klammerqualifikator nicht abgestreift (Bund, Le populaire), adjektivische Inversion
(Genfer Universitaet), Wortgrenze vor Fussnotenziffer (Nietzsche2).

#### Naechste Schritte

Konventionsentscheid Seitenapparat, dann zweite Lesart der Praezision; Reparaturklassen
als Matcher-Wave; Generator-Defekte (sp/speaker, 3040-Bibliographie) in die Struktur-Spur;
Seitenzuordnungs-Reparatur 120/1350/680/2300 operator-gated; danach neu ziehen und
nachmessen.

### Independent CER counter-check (2026-07-03, German)

Externe Verifikation der Fidelity-CER-Headline (Mean 2,71 % / Median 1,40 %, n=25) im Zuge der Arbeit am kanonischen Promptotyping-Paper. Anlass war die Operator-Frage, ob die Zahlen solide sind. Die Gegenprobe wurde ohne jeden Import von Repo-Code durchgeführt; Extraktion und Normalisierung wurden aus der dokumentierten Spezifikation neu implementiert (stdlib ElementTree, eigene Regexes), die Distanzen kommen aus python-Levenshtein 0.27.3 als zweiter C-Engine neben rapidfuzz, Aggregation und Statistik sind eigener Code. Skripte: `gegenprobe_cer.py`, `gegenprobe_metrics.py` im Verifikationsordner des Paper-Repos (`DHCraft/promptotyping-paper/verification/`). Das Repo blieb unangetastet (read-only).

#### 1. Arithmetik: vollständig bestätigt

Alle dokumentierten Werte reproduzieren auf die Dezimale: Fidelity 2,71 %/1,40 %, micro 2,13 %, Volltext 18,94 %/12,13 %, Scope 16,23 %/7,06 %, die Einzelwerte der sechs korrigierten Docs (30, 290, 1910, 90, 40, 1520) exakt, ebenso die Vorher-Vektoren 3,99 %/1,83 % und 4,26 %/1,83 %. Beide Engines liefern auf allen 25 Distanzen identische Werte; die Fidelity/Scope-Zerlegung ist auf den 15 speicherseitig kreuz-alignierbaren Docs alignment-stabil (Delta 0,0000 pp). Da die Extraktion aus der Spezifikation neu geschrieben wurde und trotzdem exakt trifft, beschreibt `quality.md` das tatsächliche Verhalten von `evaluate_ocr.py` korrekt.

**Schwellen-Sensitivität.** Die Headline hängt an `SCOPE_BLOCK_MIN = 50`:

| Schwelle | Mean | Median |
|---|---|---|
| 30 | 2,38 % | 1,21 % |
| **50 (Headline)** | **2,71 %** | **1,40 %** |
| 100 | 3,33 % | 2,10 % |

Beim Zitieren der Zahl gehört die 50-Zeichen-Schwelle genannt.

#### 2. Zweitmetriken (n=25, unabhängig gerechnet)

| Metrik | Mean | Median | misst |
|---|---|---|---|
| Fidelity-CER (Kontrolle) | 2,71 % | 1,40 % | wie Headline |
| WER total (scope-inkl.) | 22,98 % | 14,19 % | Wortebene, volle Divergenz |
| CER case-insensitiv total | 18,87 % | 11,98 % | Case-Anteil an der Volltext-Divergenz |
| Bag-of-chars-Miss | 0,36 % | **0,01 %** | echt fehlende Referenzzeichen, alignmentfrei |
| Bag-of-words-Recall | 94,78 % | 95,50 % | formgleich wiedergefundene Referenzwörter |

Die Triangulation ist kohärent. Der alignmentfreie Bag-of-chars-Miss zeigt, dass vom Referenztext im Median praktisch nichts fehlt; die Fidelity-CER besteht überwiegend aus Substitutionen und kleinen Einfügungen. Ein Word-Recall von ~95 % passt rechnerisch zu ~1,4 % Zeichenfehlern (ein Zeichenfehler berührt ein ganzes Wort). WER und CER-total bestätigen nur das bekannte Scope-Phänomen der selektiven Referenzen (Extremfall Doc 570 mit Volltext-CER 113 % bei Scope 112 %).

#### 3. Inhaltlicher Durchgang: alle 25 Docs, Top-Fehlerblöcke klassifiziert

Für jedes der 25 Dokumente wurden die sechs größten Fidelity-Blöcke inhaltlich geprüft (Dump regenerierbar über `gegenprobe_metrics.py`). Vier Fehlerklassen tragen die Headline:

**a) Seitenapparat-Einfügungen unter 50 Zeichen (häufigste Klasse, kein Erkennungsfehler).** Kolumnentitel, Seitenzahlen, Impressum, Copyright, Katalogmetadaten, Sprecherlabels, die die Pipeline transkribiert und die selektive Referenz weglässt: „TEMPS ALTERNÉS 153" (Doc 40), „LE PROBLÈME DE L'ÉLITE OUVRIÈRE" (130), „SLZ 51/52, 17. Dezember 1970" (890), „JASPERS" (3040), „JEANNE HERSCH" (100, 560, 2530, 3020), Bibliotheksvermerke (300), Inhaltsverzeichnis-Fragmente (90). Diese Klasse erklärt die Schwellen-Sensitivität aus §1 und bedeutet, dass die Fidelity-CER die reine Erkennungsleistung auch aus diesem Grund überschätzt (zusätzlich zur bekannten Referenz-Fehlbarkeit).

**b) Echter Textverlust (die eigentlich relevanten Fälle).**
- **Doc 30** (11,59 %, char_miss 6,87 %): drei Blöcke à 540/449/194 Zeichen fehlen. Am Faksimile visuell verifiziert: Das PDF ist ein aufgeschlagenes Buch als Doppelseite, der gesamte fehlende Text steht auf der linken Seite. Wurzelursache ist die Doppelseiten-Fotografie, kein OCR-Zeichenproblem. Kandidat für gezielte Nachbearbeitung.
- **Doc 1910** (7,69 %): mehrere fehlende deutsche Passagen (199/71/38/26/26 Zeichen) im Umfeld von Fachbegriffserläuterungen.
- **Doc 1520** (2,11 %): systematisches Muster, fehlende eingeklammerte Quellenangaben wie „(Introduction à la philosophie, trad. française 1re édition p. 55-57)"; sechs der Top-Blöcke sind sämtlich solche Zitatnachweise.
- **Doc 760** (5,87 %): fehlende Bildlegenden im Kunstkatalog („Le Cirque - l'écuyère" 1957, 150,5 x 100 …).
- **Doc 1180** (1,12 %): ein fehlender Satz (~150 Zeichen, zusammenhängend).
- **Doc 2635** (0,76 %): eine Bildlegende plus eine getilgte Wortwiederholung („und Schichten").

**c) Konventionsdivergenzen zulasten der Referenz.** Am Faksimile von Doc 100 visuell verifiziert: Der Druck zeigt „UNE PHILOSOPHIE DE L'EXISTENCE: KARL JASPERS" in Versalien, die Pipeline transkribiert versalientreu, die Transkribus-Referenz normalisiert auf Kleinschreibung; die case-sensitiven „Fehler" messen hier Referenzkonvention, nicht Erkennung (gleiche Signatur in Doc 2635 und 3040). Verwandt: Akzent-Setzung auf Großbuchstaben (Doc 2530, A↔À, E↔É) und die Ellipse U+2026 gegen drei Punkte (Doc 570), die die symmetrische Normalisierung derzeit nicht abfängt.

**d) Echte Zeichen-Fehlerkennungen.** In den Top-Blöcken selten: Einzelzeichen-Substitutionen (Doc 1060 u↔i, Doc 830 ô↔à, Trennstrich-Reste), eine verstümmelte Zeile (Doc 2310).

#### 4. Konsequenzen

1. Die Headline 2,71 %/1,40 % ist arithmetisch korrekt, reproduzierbar und als **Obergrenze** der Erkennungsfehlerrate doppelt abgesichert (fehlbare Referenz, Apparat-Einfügungen). Die tatsächliche Zeichen-Erkennungsleistung liegt darunter.
2. Zitierform überall mit n=25, Schwelle 50 und Stand 2026-06-08.
3. Mögliche Folgearbeiten (Entscheidung liegt beim Projekt, nicht hier getroffen): Ellipsen-Normalisierung (U+2026 ↔ „...") symmetrisch ergänzen; Apparat-Einfügungen als eigene Kategorie ausweisen, falls eine reine Erkennungsrate gewünscht ist; Doc 30 wegen der Doppelseiten-Ursache gezielt nachziehen; die Versalien-Konventionsdivergenz der Referenz in `quality.md` bei der Referenz-Fehlbarkeit mit dokumentieren.

**Grenze der Aussage.** Ground Truth existiert nur für diese 25 Dokumente. Für die übrigen ~260 Dokumente des Korpus ist keine CER messbar; dort gelten weiterhin nur die dokumentierten Proxys (Schema-Validität, Layout-QA, Wörterbuch-Plausibilitätsband).

### False-positive hunt protocol (tier-1 entity marks, 2026-08-12; operative file `output/audits/fp_hunt/PROTOCOL.md`)

Binding instructions for every agent of the false-positive hunt. The ranking is frozen;
do not regenerate it, do not rerun the corpus scan, do not modify any file outside
`output/audits/fp_hunt/verdicts/`.

The hunt adjudicates automatic tier-1 marks in risk order instead of sampling them
evenly. `scripts/entity/entity_risk_ranking.py` scores every tier-1 mark by additive
features and sorts the corpus into three strata, so the wave buys its checked cases
where a false positive is most likely.

#### Inputs

- Ranked cases: `output/audits/fp_hunt/risk_ranking.json`, list `marks`, case ids
  `f0001`, `f0002`, ... in risk order; the highest stratum comes first, so a low case
  number is a high-risk case
- Facsimile per case: `docs/images/{doc}/{doc}_p{NNN}.png` (open with the Read tool);
  the case record carries the path as `facsimile`
- Page text: `docs/data/pages/{doc}/{doc}_p{N}.xml` (pipeline TEI of the page)
- Pipeline entity output per page: `docs/data/pages/{doc}/{doc}_entity_p{N}.xml`
  (tier-1 wraps) and `docs/data/pages/{doc}/{doc}_entity_worklist.json` (tier-2 entries)
- Entity list: `data/entities/all_entities.json` (persons/organisations/works, headword
  `name`/`orgName`/`title`, id field `GND_id`)
- Name variants: `data/entities/gnd_cache.json` (entries keyed by gid)

Every case record carries `doc`, `page`, `surface`, `gid`, `category`, `rule`, `score`,
`features` and the surrounding `context`. Score and features say why the case was drawn
forward; they are never evidence for a verdict. The facsimile decides, and the scoring
contract is documented inside the ranking under `feature_doc`.

#### Assignment

Cases are handed out as contiguous ranges of the ranking, highest stratum first, 50 cases
per agent. Each agent writes exactly one file
`output/audits/fp_hunt/verdicts/fp_{first}_{last}.json`, named after its range, for
example `fp_f0001_f0050.json`. An agent never writes into another agent's file and never
reads another agent's verdicts.

#### Verdicts (one per case)

Look at the facsimile page, locate the surface, decide exactly one verdict:

- `correct`: the surface is on the page and refers to exactly the linked entity
  (gid), and the span covers the mention.
- `wrong_entity`: the surface exists but refers to a different person,
  organisation or work, or to no entity at all (generic word, term, title of a
  section rather than the listed work).
- `wrong_span`: right entity, wrong extent (partial name, swallowed punctuation,
  split across unrelated words).
- `not_in_source`: the page does not carry this surface at the claimed position
  (OCR phantom).
- `undecidable`: the page does not decide it. Use sparingly and say why.

Special rule: documents 120 and 1350 carry more `pb` elements than physical pages
(duplicate facs references), so their page-to-image mapping is broken. Every case in
doc 120 or 1350 gets `undecidable` with reason "facsimile mapping defect (pb/page
mismatch, known data defect)". Do not try to guess the right image.

Surfaces may contain `<lb/>` (line break inside a name); on the page the name then
spans two lines. That is still `correct` if entity and extent are right.

A bare surname is `correct` only when the page context makes the linked bearer the one
meant. Where two listed persons share the surname and the page leaves the bearer open,
the verdict is `wrong_entity` when the linked gid is the wrong bearer and `undecidable`
when the page decides nothing.

Judge independently. Do not read any other agent's verdict file.

#### Output format

Write ONLY to your assigned output file under `output/audits/fp_hunt/verdicts/`.

A JSON list, one object per case:
`[{"case_id": "f0001", "verdict": "correct", "reason": "<one short English sentence>"}, ...]`

Reasons are English, compact, one sentence. Every case of your range must appear exactly
once, in ascending case id. If an image file is missing, verdict `undecidable` with the
reason naming the missing path.

#### Guardrails (verbatim, binding)

- "NEVER read `.env`: the `.env` file contains API keys and must under no circumstances be read, displayed, or included in output"
- "no secrets in code or docs: API keys, tokens, and passwords live exclusively in environment variables"
- "Grokipedia is never used as a source, in any context"
- "Entity-Linking (GND/Wikidata-IDs) niemals per LLM, nur deterministische API-Lookups" (you judge existing links and record gids already on the list; you never introduce new ids)
- "No cost figures"
- "Windows encoding: no Unicode special characters in print statements"
- knowledge/arbeitsbericht-v3.md must never be touched
- output/tei_final/, data/, docs/, scripts/, tests/ must never be written; write access is limited to your single output file
- no commits, no pushes, no subagents

#### After the wave

A confirmed false positive is fixed at its root cause, either as a reject verdict on the
offending name form in `data/entities/variant_review.json` or as a rule guard in
`scripts/entity/entity_matcher.py`, followed by a rerun of the corpus scan and the ranking.
Hand-editing the TEI in `output/tei_final/` or the mirror in `docs/data/` is never the
fix; it removes the symptom and leaves the rule that produced it in place. Both root-cause
paths are operator-gated steps outside this wave.

The verdict files are the mention verdict store of the hunt. Confirmed-correct verdicts
stay there, joined to the ranking by `case_id`, and carry the checked state of a mark
into the next snapshot, so a rerun re-adjudicates only what the scan actually changed.
