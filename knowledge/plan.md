---
title: Plan
project:
  name: zbz-ocr-tei
  repository: https://github.com/chpollin/zbz-ocr-tei.git
method:
  name: Promptotyping
  url: https://dhcraft.org/Promptotyping/
template:
  name: Vorlage Plan
  version: 0.2
  url: https://dhcraft.org/Promptotyping/promptotyping-document/plan
status: active
language: en
version: 1.0
created: 2026-08-21
updated: 2026-08-21
authors: [Christopher Pollin]
related: [specification, decisions, journal, verification, tei-mapping, integration, governance, index]
---

# Plan

This document orders the work still outstanding into phases and milestones, each carrying the
condition under which it counts as finished. It is the forward-looking pendant to
[journal.md](journal.md), which records how the project reached its current state, and it is
rewritten as milestones close. Completed work leaves the active phases and stays visible in the
status tracker. What has been decided lives in the register [decisions.md](decisions.md); what is
required and against which gates it is measured lives in [specification.md](specification.md), and
the plan anchors its exit conditions there instead of restating them.

## Target state

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

## Phases and milestones

| Phase | Milestones | Quality gate |
|---|---|---|
| A, entity layer to delivery | schema hardening, lexicon shape audit, gold benchmark (M4), population redraw, admission dossier, judge calibration (M5), corpus dry run (M6), stock run (M7) | schema gate, entity gates, closed-world invariant ([testing.md](testing.md)) |
| B, provenance and self-contained TEI | provenance log per object, `_complete.xml` remainder, provenance drawer | schema gate, mirror regeneration |
| C, viewer and export | ZIP export, round-trip wrapper, deferred frontend findings | page load checks, validator |
| D, measurement follow-ups | inter-engine CER, remaining tail documents, ratio heuristic residue | CER statistics regenerated under the recorded seed |
| E, deferred tooling and infrastructure | dependency lock, configuration file, production fork and container, serialization defect, BCa aggregation | CI gates |

### Phase A, entity layer to delivery

The goal is the entity layer inside the delivered TEI, released by the operator on measured
numbers. Nothing before the stock run touches `output/tei_final/`. The markup rules of the layer
live in [tei-mapping.md](tei-mapping.md), the measurement method and its findings in
[verification.md](verification.md).

#### Schema hardening

Begins immediately, since the schema is the format authority of the delivery (E102) and every
measurement whose numbers should survive belongs after it. `persName@ref` and `orgName@ref` already
carry the `GND:` pattern inline. `bibl` pulls `tei_att.canonical.attributes` and inherits an
unconstrained `@ref` through it, while its GND pattern sits on `@corresp`; `rs` inherits the same
unconstrained `@ref` through `tei_att.naming.attributes`. Tightening means narrowing the inherited
`@ref` on `bibl` the way `persName` and `orgName` do, or dropping `att.canonical` from `bibl`, and
handling `rs` the same way through `att.naming`. `placeName` stays untouched, since Z3 forbids it
and the corpus has no usage. The change takes its own commit and register entry.

Done when all delivered TEI and the valid reference TEIs still validate against
`data/schema/zbz_hersch.rng` and the schema gate named in [testing.md](testing.md) is green.

#### Lexicon shape audit

Begins once the schema is settled. A new instrument, `scripts/entity/entity_lexicon_audit.py`,
groups every form the built lexicon would match by shape class, among them dotted initials, single
tokens at the length floor, all-caps forms, forms carrying digits, and non-Latin scripts, each with
counts and examples. The operator then approves or bans a whole class instead of chasing single
forms. The audit reruns after every refresh of the GND variant cache.

Done when the operator has ruled on every shape class and the rulings are recorded in
`data/entities/marking_policy.json`, which the matcher loads and validates.

#### Gold benchmark under frozen rules (M4)

Begins once schema hardening and the lexicon audit are closed and the matcher rules are frozen. One
run of `entity_gold_benchmark` measures precision and recall against the held-out part of the 25
reference TEIs. The held-out set is drawn along the distribution of gold mentions. The densest
reference, document 1520, is measured on its own, because it carries a large share of the gold, a
known file defect and the anchor-collision case the pilot panel never saw. The script today writes
`output/audits/entity_gold_benchmark.json` only, so the milestone also adds the versioned evidence
path under `docs/data/`.

Done when a frozen-rules precision and recall measurement is versioned under `docs/data/` and
[verification.md](verification.md) carries the figures together with their sample basis.

#### Population redraw and recall remeasurement

The adjudicated sample belongs to a mark population that the marking policy of E119 has since
widened, and the released marks appear in no earlier draw. The recall side has stood unmeasured
since several of its named rule gaps were closed. A fresh stratified draw over the current
population, the E119 stratum included, and a recall remeasurement on newly read pages come before
any further rule work, because rules built on a population whose rate is unknown widen the gap
between what is measured and what is delivered. A second draw already lies frozen and unadjudicated
under `output/audits/eval_sample_2026-08-13/`; whether it is adjudicated as it stands or re-cut is
the re-freeze decision.

Done when the fresh draw is adjudicated, the judgments are folded into
`data/entities/mention_verdicts.json`, the verdict guard runs clean, and
[verification.md](verification.md) reports precision and recall for the current population.

#### Admission dossier for unlisted entities

Entities the corpus names frequently while the curated list omits them are admitted by the project
itself and marked in the data as an addition from outside that list (operator decision of
2026-08-13). The proposal channel `entity_unlisted_scan` supplies the candidates. The dossier
collects, per candidate, the textual evidence and a deterministic lobid lookup; a language model
never assigns an identifier. The provenance vocabulary carries the distinction through a third
responsibility declaration with `cert="low"`, and a reference is written only once an
identification is confirmed.

Done when every admitted entity has a dossier entry with its evidence and its lookup result, and
the marks it produces validate under the vocabulary described in [tei-mapping.md](tei-mapping.md).

#### Judge calibration (M5)

Begins once the gold benchmark and the redraw have fixed the current rates. A model judge is
measured against ambiguities the reference TEIs already resolve, repeat-run stability included, so
its role in tiers two and three is bounded by a measured accuracy. The judge picks among presented
candidates; identifiers come from the curated list.

Done when accuracy and repeat-run stability on gold-resolved ambiguities are measured and recorded
in [verification.md](verification.md).

#### Corpus dry run (M6)

Begins once the four entity operator questions and the open modelling points are decided. A new
instrument, `scripts/entity/entity_audit.py`, measures the stock before and after, and the full
change preview plus the distribution report go to the operator. A second, independent layer runs
before the dry run, an adversarial agent review of the built lexicon searching for forms that would
strike in ordinary prose; agent findings are proposals, and class decisions stay with the
deterministic shape rules. The review follows the wave pattern of [governance.md](governance.md).

Done when the operator has reviewed the full change preview and the distribution report and
released the stock run.

#### Stock run into the delivered TEI (M7)

`scripts/entity/tei_entity_marker.py` does not exist yet, and `tei_entity_preview.py` refuses to
write into `output/tei_final/`. The marker is built on `marker_common` with dry-run, backup,
byte-splice inside `text`, idempotence and a `revisionDesc` entry. One design condition binds the
milestone, that the marker reuses the wrapping and checking logic of the preview instead of growing
a second copy of it. `apply_candidates`, `mark_attributes`, `hi_envelope`, the text-invariance
check and the schema check move out of `tei_entity_preview.py` into a shared module both consume,
so preview and stock run provably produce the same wrapping. Whether the `@resp`, `@cert` and
`@source` attributes travel into the delivered TEI is decided before the run.

Done when the released run has written the marks into `output/tei_final/`, the technical gates of
[testing.md](testing.md) are green (byte-identical text extraction, deterministic CER reproduction,
schema gate, conformity rules, idempotence proof, closed-world invariant over every identifier in
the shipped mirror), the mirror is regenerated, the register carries the entry, and
`docs/methode.html` has gained its entity-quality paragraph pointing to
[verification.md](verification.md).

### Phase B, provenance and self-contained TEI

The goal is an editing history per object that is machine-readable and travels inside the TEI. The
built state of the provenance layer is described in [workflow.md](workflow.md), provenance section.

#### Machine-readable provenance log per object

Today the provenance of an object is split between the `<revisionDesc>` of its final TEI and its
`{doc}_manifest.json`. A `{doc}_provenance.json` beside the final TEI becomes the single editing
log per object and carries these fields:

- `doc_id`
- `current_state` with layout source, OCR source, TEI version and workflow status per stream
- `history`, a list whose items carry a timestamp, an actor (engine and version, or a human role),
  a kind (OCR, layout QA, layout edit, text edit, workflow status), a scope (page or whole
  document), an optional detail string, and a `ref` to the concrete file under `output/`

Actor entries name engines and roles. The log answers in one place what the current split cannot,
the edit history per object, an audit trail per agent decision, a roll-back to an earlier state
without git history, and the direct link between a layout region and a body element, which is
implicit in the reading order today.

Done when every delivered object carries a `provenance.json` whose history reproduces the
`<change>` entries of its `<revisionDesc>` and whose `ref` values resolve to existing files.

#### The self-contained `_complete.xml`

The facsimile side of this plan is realized in the delivered TEI. Step 1 computes pixel zones per
region, the assembly writes `<facsimile>` with one `<surface>` per page and a `<graphic url>` as
its first child, and body elements carry `@facs`; the page break carries `<pb facs="#facs_N">`
(E89, described in [tei-mapping.md](tei-mapping.md)). What remains is the extended `<revisionDesc>`
assembled one to one from the provenance log, and the export arrangement in which `_complete.xml`
becomes the default export variant while `_final.xml` stays the compact reading variant. The
milestone stays a pipeline package separate from the viewer work.

Done when the generator writes `_complete.xml` with the provenance items as `<change>` elements,
the file validates against `zbz_hersch.rng`, and the export module offers both variants.

#### Provenance drawer in the viewer

Begins once the provenance log exists. The viewer reads an object's log and shows it as a drawer
beside the status pills, so a curator sees which engine or which human step produced the state in
front of them. Values come from the token catalogue described in [design.md](design.md).

Done when the drawer renders the full history of an object from `provenance.json` and the page
loads without a console error.

### Phase C, viewer and export

The goal is a curation loop that needs no manual pipeline step and an object that leaves the
repository as one file.

#### ZIP export per object (E61)

All pipeline artifacts of an object become one download via JSZip, optionally collected from the
corpus overview for several objects at once. This closes frontend finding N1, which records that
only per-stream single export exists. JSZip is named as a runtime dependency in `CLAUDE.md` and is
absent from the code; the vendoring convention established with E122 applies to it.

Done when a document downloads as one archive carrying its final TEI, its per-page layout JSON, its
OCR text and its manifest, and the catalog offers the multi-select path.

#### Round-trip wrapper for the curated edit

Steps four to seven of the round trip described in [workflow.md](workflow.md), round-trip section,
run manually today, the reassembly, the status projection into the `revisionDesc`, the validation
and the mirror regeneration. A wrapper command, `scripts/apply_curated.py --doc {ID}`, runs them in
order and stops at the first failing gate.

Done when one command takes a curated edit from the viewer save through to a regenerated mirror and
the validator reports no error for that document.

#### Deferred frontend findings

Deferred until after acceptance by ZBZ. N3 records that OpenSeadragon loads an untiled full
PNG and re-instantiates on every page switch, to be fixed through tiling or neighbour preload. N6
records that the mobile catalog below 1000px hides date, language, type, form and pages entirely,
of which date and type stay visible. N7 records that the contrast of `--h-text-muted` sits below
WCAG AA for small text, so the token is restricted to auxiliary text. Two further items belong
here, the page strip with per-page status markers as QA navigation, a follow-up idea from the
go-to-page fix, and the missing `aria-current` in the viewer. One feature of the edition uplift is
still outstanding as well, the integration of the layout editor into the OpenSeadragon facsimile
view, so a region is corrected on the image instead of beside it. The open quick wins of the
2026-08-12 UI analysis are decided together with them.

Done when each finding is implemented or recorded in the register as declined, and the page checks
named in [testing.md](testing.md) pass.

### Phase D, measurement follow-ups

The goal is closing the questions the measurement layer left open. Two catalog corrections the
register had recorded without acting on them, the page break collapsing to one space and the
running-head text entering the extraction, were carried into
[cer-methodology.md](cer-methodology.md) in the wave-4 documentation pass; the code and its pinning
tests were already the authority.

#### Inter-engine CER cross-validation

Item (b) of the stability question, a second OCR run with a different engine as cross-validation of
the headline CER. Item (a), run-to-run stability of the pipeline, was measured with E100, and its
result sits in the `stability` block of `docs/data/cer_statistics.json`. The measurement method,
the reference choice and the extraction rules are fixed in
[cer-methodology.md](cer-methodology.md). The run consumes API calls and is therefore
operator-gated.

Done when a second engine has read the reference documents, the paired difference against the
delivered layer is reported with its interval, and the statistics JSON carries the result under the
recorded seed.

#### Remaining tail documents

The CER tail is structural. It is not a failure of character recognition. The documents whose tail
traces to a doubled-page reading order, 760 and 1440, stay facsimile-verified curation cases.
Machine reordering of the corpus was refuted empirically (E99) and is banned on every path, so
W19 is read as a suspect signal for text or zones.
Targeted per-page re-reading is the pattern E96 and E98 established and stays operator-gated per
page.

Done when both documents are curated page by page against the facsimile, or the operator records
that they stay as they are.

#### Ratio heuristic residue

`scripts/eval/evaluate_ocr.py` still derives a scope mismatch from the ratio of reference to
pipeline page-break counts. The published statistics no longer use it, since
`cer_statistics_runner.py` returns a neutral scope. Either the residue goes, or its diagnostic role
is documented where the metric is defined.

Done when the heuristic has one documented purpose or no call site.

### Phase E, deferred tooling and infrastructure

The goal is the production side of the repository. Each item names the condition that opens it.

#### Dependency lock

`pyproject.toml` is the only manifest since the wave-3 tooling package; the accompanying `uv.lock`
is missing because uv is not installed on the working machine. CI materializes the dependency list
from `[project] dependencies` plus the `dev` extra and installs it with pip, so both gates run
without the lock.

Done when `uv lock` has produced a committed lock file and CI installs from it.

#### Configuration file

Engines are configured in `scripts/config.py` and `scripts/ocr/ocr_pipeline.py`. A YAML
configuration would move engine name, model and environment-variable names out of the code. The
draft in [infrastructure.md](infrastructure.md) still names Mistral as the default engine, which
the code resolves to Gemini, so the draft is rewritten before it is built.

Done when engine selection reads from one configuration file and every pipeline command behaves
unchanged.

#### Production fork, container image and its CI

The production repository at the University of Zurich is a fork of the development repository, and
three pieces belong to it. An OCI image built from a Containerfile, configured through environment
variables and carrying no secrets. A `.gitlab-ci.yml` that runs the same two gates as the GitHub
Actions workflow and additionally builds the image and pushes it to the GitLab registry. A defined
merge strategy for upstream changes from the development repository into the fork, which is the
mitigation of the fork-divergence risk recorded in [integration.md](integration.md).

Done when the fork builds its image in its own CI, both gates run there, and the merge strategy is
written down in [integration.md](integration.md).

#### Foreign-namespace serialization defect

`serialize_tei_fragment` drops the namespace declaration of a foreign-namespace element and returns
an unparsable fragment. No corpus impact is known, which is why it was recorded without being acted
on. The fix carries a test pinning a foreign-namespace child.

Done when the function round-trips a foreign-namespace element and the pinning test is green.

#### BCa aggregation kept as library code

`cer_statistics.py` carries a BCa implementation with its own tests and calls it in its own
aggregation functions, which the generator of the published statistics never uses; the published
intervals are percentile intervals throughout, and every aggregate names its own `ci_method`. The
label question was settled by moving the label (E122), and the implementation stays as library
code (E123). The item reopens only if a published aggregate needs bias correction.

Done when either the published generator calls it and the statistics are regenerated under the
recorded seed, or the code is removed with a register entry.

## Status tracker

Snapshot of 2026-08-21. States used here are done, built (the instrument exists, the run is
outstanding), open, and blocked-by with the named party.

| Milestone | State | Evidence |
|---|---|---|
| Pilot, layout scaling, PAGE-XML and METS | done | [project.md](project.md), delivered scope |
| TEI generation schema-valid | done | E102, `tests/test_tei_schema.py` |
| CER evaluation | done | `docs/data/cer_statistics.json`, [cer-methodology.md](cer-methodology.md) |
| Corpus handover to ZBZ | done | E66/E67, every stream `unverifiziert` as handover default |
| Entity layer to preview (M0 to M3) | done | E105 to E119, [verification.md](verification.md) |
| CER catalog corrections | done | [cer-methodology.md](cer-methodology.md), extraction rules |
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
| Deferred frontend findings N3, N6, N7, page strip, `aria-current` | open | `reports/2026-08-12_viewer-ui-analyse.md`, E123 residue |
| Layout editor inside the OpenSeadragon view | open | E58 facsimile view, E60 edit toggle |
| Inter-engine CER | open | stability item (b); item (a) measured with E100 |
| Tail documents 760 and 1440 | open | E91 classification, E99 refutation |
| Ratio heuristic residue | open | `scripts/eval/evaluate_ocr.py` |
| Dependency lock | blocked-by toolchain (uv not installed) | E123 |
| Configuration file | open | [infrastructure.md](infrastructure.md), planned configuration |
| Container image, GitLab CI, merge strategy | blocked-by the production fork | [integration.md](integration.md) |
| Foreign-namespace serialization defect | open | `serialize_tei_fragment` |
| BCa aggregation as library code | open, decision pending | E122 (label), E123 (code kept) |

## Open decisions and dependencies

Four questions sit with ZBZ, and two of them shape the entity layer.

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
  the matcher still skips figure contexts and reports caption candidates separately.
- Empty `speaker` elements stay curation slots (W17); the matcher never invents text.
- Adjective forms of names. The guideline excludes them, the references mark at least one. The
  automatic tiers exclude them and candidates go to the worklist.

Two further decisions belong to single milestones. Whether the `@resp`, `@cert` and `@source`
attributes travel from the preview layer into the delivered TEI falls before the stock run and is a
decision for ZBZ. The re-freeze of the reconstructed evaluation draw falls before the
population redraw and is the operator's.

Feedback from ZBZ is unavailable in this project phase, so open convention questions of the
entity layer fall to the operator; that rule and the verification of agent self-reports are
recorded in [governance.md](governance.md).

Hard ordering across the phases. Schema hardening and the lexicon audit precede the gold benchmark.
The fresh draw precedes any further rule work. The corpus dry run precedes the stock run. The
provenance log precedes both the extended `<revisionDesc>` and the viewer drawer. The round-trip
wrapper presupposes none of them and may be pulled forward.

## Deviations

The gates hold independently of the sequence, and a milestone closes on its done-when criterion
alone. Re-prioritisation is allowed when a blocked milestone would otherwise idle the work, and the
deviation is recorded with its reason in [journal.md](journal.md). Decisions taken along the way go
into [decisions.md](decisions.md) as register entries.

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
  ([integration.md](integration.md)).
- The double-page detection question was closed after the Masterfile check. The Masterfile carries
  no double-page column, no aspect ratio is computed anywhere, and the judgement stays with the
  layout model's prompt. The residue is the page-break ratio heuristic in `evaluate_ocr.py`, which
  Phase D resolves.
- The knowledge base was recut by function in the refactoring waves recorded from E120 onward. The
  plan carries the outstanding work of that recut and none of its history.
