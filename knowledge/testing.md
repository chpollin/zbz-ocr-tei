---
title: Testing
project:
  name: zbz-ocr-tei
  repository: https://github.com/chpollin/zbz-ocr-tei.git
method:
  name: Promptotyping
  url: https://dhcraft.org/Promptotyping/
template:
  name: Vorlage Testing
  version: 0.2
  url: https://dhcraft.org/Promptotyping/promptotyping-document/testing
status: complete
language: en
version: 1.0
created: 2026-08-21
updated: 2026-08-21
authors: [Christopher Pollin]
related: [specification, verification, pipeline, infrastructure, governance]
---

# Testing

This document describes the automated test suite that fulfils the gate requirement of
[specification.md](specification.md). It states what the suite guarantees about the
delivered data, which part of it survives a fresh clone, which classes of defect it
deliberately leaves uncovered, and how it is run. The requirement itself and the mapping of
gate to requirement id stay in specification.md; the invocations stay in CLAUDE.md.

## Test strategy

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
verification of agent self-reports against disk, is in [governance.md](governance.md).

## What is guaranteed

The following properties of the delivered data and of the tools that produce it are pinned
by a test and fail the build when they break.

- Schema validity of every document in `output/tei_final/` against `data/schema/zbz_hersch.rng` (`tests/test_tei_schema.py`).
- The delivery contract of the produced `teiHeader`, meaning `idno` of type docID, `biblStruct` with analytic, monogr and imprint, and `langUsage` (`tests/test_tei_header.py`).
- The ZBZ conformity rules over the delivered corpus and the generator fixes behind them (`tests/test_zbz_conformity.py`, `tests/test_tei_conformance.py`).
- The project rules of the validator, errors R1 to R7 and warnings W1 to W7 and W11 to W18, each with one firing fixture and one silent counter-fixture that carries the same construct in correct form; W19 is covered through `tests/test_tei_validator.py` (`tests/test_tei_validator_rules.py`).
- Corpus invariants, the delivered distribution and the completeness gate over the funnel from Masterfile to delivered PDF (`tests/test_corpus_audit.py`, `tests/test_completeness_check.py`).
- Determinism of the CER statistics, the bootstrap and paired-difference machinery, HCPR, and the extraction and normalization rules indexed to the catalog of [cer-methodology.md](cer-methodology.md) (`tests/test_cer_statistics.py`, `tests/test_cer_extraction.py`, `tests/test_guard_pins.py`).
- The step-1 scaffold plus assembly as an end-to-end contract without any API call, asserting `pb` numbering, region-to-paragraph mapping, facsimile zones and RelaxNG validity of the assembled document (`tests/test_step1_assembly.py`).
- The step-2 repair path on malformed model output, including the guard that refuses an empty or whitespace-only answer instead of replacing the page scaffold with nothing (`tests/test_tei_step2_repair.py`).
- The closed world of the entity layer, meaning every GND id that reaches the viewer through the generated mirror compared as a raw string against the curated list, so a formatting drift fails as loudly as an unknown id (`tests/test_entity_ref_invariant.py`).
- The adjudicated mention verdicts as a regression gate against the current corpus scan (`tests/test_entity_verdict_guard.py`, `tests/test_mention_verdicts.py`).
- The blank-page rule and its projection as `<pb type="blank"/>`, together with the idempotence of the shared marker scaffolding, so a second run produces no duplicates (`tests/test_blank_marker.py`, `tests/test_marker_common.py`, `tests/test_status_marker.py`).
- The document-field contract of the catalog against the keys the frontend reads, the aggregated manifest index, and the agreement of the workflow status tokens between `page_manifest`, `tei_status_marker` and the viewer JavaScript (`tests/test_catalog_contract.py`, `tests/test_manifest_index.py`, `tests/test_workflow_status.py`).
- The facsimile binding, meaning surface and graphic completeness in the delivered TEI and the text-page to scan-image resolution of the mirror (`tests/test_tei_surface_graphic.py`, `tests/test_facs_mapping.py`).
- Syntax and internal imports of every module under `scripts/` (`tests/test_scripts_health.py`).

## Acceptance

The gate table in [specification.md](specification.md) names which check answers which
requirement, which owns that mapping. A change is acceptable when those gates
pass and, where the change was meant to preserve behaviour, the anchor set named in the
strategy section is unchanged.

Continuous integration runs the gates on every push and pull request.
`.github/workflows/tests.yml` defines a single job on Ubuntu with Python 3.11, materializes
the dependency list from the `[project] dependencies` block of `pyproject.toml` plus the
`dev` extra, installs it with pip, then runs `ruff check scripts tests` followed by
`python -m pytest tests/ -q`. The heavy layout engines are the separate `layout` extra and
stay uninstalled in CI. Corpus-dependent tests skip themselves on the fresh checkout, so
the CI signal is the clone-safe subset while the local run is the full one. The `dev` extra
pins ruff to one version and `.pre-commit-config.yaml` reuses that pin in a local hook, so
hook and CI report the same findings. Deployment and repository topology are in
[infrastructure.md](infrastructure.md).

## What is deliberately not checked

The guarantee above has named borders. The following classes lie outside it, and a green
suite says nothing about them.

Stamps, shelf marks and catalogue notes that land in running text have no check. No
validator rule and no audit detects that class, so the schema plus W-rule layer is blind to
it. Neighbouring classes do have deterministic instruments, E-Periodica cover sheets
through `tei_cover_strip`, running heads through `running_head_audit` and the shared
detection core, folio echoes through `pb_number_audit`, and the entity matcher excludes
apparatus zones; none of these reaches library apparatus inside the body text.

Two latent defects are recorded and not fixed, so no test asserts the correct behaviour.
`serialize_tei_fragment` drops the namespace declaration of a foreign-namespace element and
returns an unparsable fragment; no corpus impact is known. The catalog JavaScript carries a
fourth status token `ausstehend` that exists in the UI layer alone and in no data model, so
the status contract test pins the three data values and tolerates the fourth. Both are
recorded in [decisions.md](decisions.md) E123.

Behaviour under a missing corpus is checked only to the extent that the marked tests skip.
Whether a script degrades usefully when `output/` is empty stays untested.

Content of language-model output is asserted nowhere. Step 2, the layout QA and the OCR
correction are non-deterministic, so the tests pin the repair path and the guards around
the call instead of the answer. Run-to-run variation is a measurement
question and belongs to [verification.md](verification.md), which holds the stability
pilot.

Visual correctness of the viewer sits outside the suite. The frontend is covered by a
headless browser check during a refactoring wave, which finds console errors, failed asset
requests and broken interactions; whether a rendering looks right stays a human judgement.

## How to run

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

## Pattern: test in the same commit

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

## TDD workflow and anchor strategy

The failing test precedes the implementation, the code is written to make it green, and the
refactoring happens while it stays green. Where a format string or a serialization is about
to change, the test is written against the current output first, so the diff shows the
intended change and nothing else.

For a structural change that must preserve behaviour, the test suite alone is
insufficient, because a moved module can keep every unit green while a generated artifact
drifts. The anchor strategy closes that gap. Before the change, the CER benchmark JSON and
the entity corpus-scan JSON are hashed with the wall-clock `generated` key removed, so the
hash depends on content rather than on run time, and the mirror is regenerated to establish
an empty git diff as the baseline. After the change, both hashes must match and
`generate_edition_data --mirror-only` must again leave `docs/data/` with an empty diff.
Where a generator legitimately changes its output, the deviation is named and accepted in
the register entry instead of being absorbed silently.

## Known exceptions and limits

Tests that need the delivered corpus or tracked repository data carry a `skipif` guard beside
their marker, so a fresh clone reports skips rather than failures while the collection stays
the same; the marker makes the class selectable with `-m`. The consequence
is that the CI signal is systematically weaker than the local one, which is the reason the
validator rules and the generator contract were rebuilt on synthetic fixtures.

Verification runs name an allowlist of scripts, and anything that writes under
`output/audits/eval_sample*` or under `data/` is excluded by name; the rule and the incident
behind it are recorded in [governance.md](governance.md), guardrails section.

`--strict-markers` means a new marker has to be registered in `tests/conftest.py` before it
can be used. This is deliberate, because an unregistered marker deselects nothing and would
let a supposedly guarded test run in an environment it cannot survive.

Lesson L1 of [journal.md](journal.md) bounds what a warning layer is worth. Validation must
be actionable; a false-positive rate above half makes a report useless, and every warning
needs a concrete action. This is why the W rules stay non-blocking curation signals and the
blocking gates are restricted to schema, header contract, corpus invariants and the closed
world.

## Components

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
- edition, viewer data: `test_catalog_contract.py`, `test_manifest_index.py`, `test_workflow_status.py`, `test_facs_mapping.py`.
- entity: the matcher and its rules in `test_entity_matcher.py`, `test_entity_regressions.py`, `test_running_heads.py`, `test_running_head_audit.py`; the intake and cache side in `test_entity_lint.py`, `test_fetch_gnd_variants.py`, `test_variant_review.py`; the preview and mirror generators in `test_entity_preview.py`, `test_generate_entity_preview_data.py`, `test_generate_entity_overview.py`, `test_entity_stream.py`; the corpus instruments in `test_entity_corpus_scan.py`, `test_entity_corpus_digest.py`, `test_entity_unlisted_scan.py`, `test_entity_risk_ranking.py`; the measurement and gate side in `test_entity_eval_sample.py`, `test_entity_gold_benchmark.py`, `test_entity_ref_invariant.py`, `test_mention_verdicts.py`, `test_entity_verdict_guard.py`.
- repository health: `test_scripts_health.py` compiles every module under `scripts/` and resolves its internal imports.

The OCR scripts under `scripts/ocr/` have no dedicated test module. The text layer they
produce enters the suite through the loaders and through the step-1 contract, which reads
OCR markdown from a synthetic fixture directory; the API adapters themselves stay untested.

## Current state

Snapshot of 2026-08-21. The suite passes with no skips, ruff reports no finding, and the
clone-safe subset covers the validator rules and the generator contract. The two counting
commands above produce the current sizes.

```bash
python -m pytest --collect-only -q
python -m pytest --collect-only -q -m "not requires_corpus and not requires_mirror"
```

The last recorded figures, together with the wave that produced this state, are in
[decisions.md](decisions.md) E123.
