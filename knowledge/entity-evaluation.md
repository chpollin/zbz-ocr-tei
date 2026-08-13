# Entity Evaluation Workflow

Sampling-based measurement of the entity layer: is what we mark correct (precision),
and do we miss what should be marked (recall). Both are adjudicated at the facsimile,
independent of the 25 ZBZ reference TEIs. The references stay in use as a trend
indicator through `entity_gold_benchmark`, but they are partial and internally
inconsistent, so they cannot serve as the truth standard; the FP classification of
2026-08-12 showed that of 51 measured deviations only 2 were real pipeline errors.

Related documents: [entity-integration.md](entity-integration.md) (annotation spec,
rule catalog, instruments), [specification.md](specification.md) (quality method),
[cer-methodology.md](cer-methodology.md) (the same measurement discipline for the
text layer).

## What "correct" means here

The entity layer works with a closed world: only entities on the curated ZBZ list are
marked (E62). Correctness is therefore always correctness relative to the list and to
the annotation spec in entity-integration.md (scope zones, byline exception, nesting,
suffix contract). Names outside the list are the business of the proposal channel
(`entity_unlisted_scan`), whose quality is assessed separately. A tier-1 mark is
correct when the surface exists on the page, refers to exactly the linked entity, and
the span covers the mention as the spec defines it.

## The six phases

### 1. Draw

The instrument `scripts/eval/entity_eval_sample.py` draws two reproducible samples
(fixed seed 42, stratified, every draw documented in the output):

- Precision sample: 300 tier-1 marks out of the corpus scan, stratified by category
  (person, organisation, work) and rule family, so rare rules do not vanish behind
  frequent ones.
- Recall sample: 40 pages out of the delivered corpus, stratified by layout type and
  language, drawn from the page inventory of the catalog.

Output is one case file per drawn unit under `output/audits/eval_sample/`, carrying
everything an adjudicator needs: document, page, surface, offsets, linked entity,
rule, context excerpt, facsimile path.

### 2. Adjudicate precision

Every drawn mark receives a verdict at the facsimile with exactly one value:

- `correct`: surface on the page, identity right, span right
- `wrong_entity`: surface exists but refers to someone or something else
- `wrong_span`: right entity, wrong extent
- `not_in_source`: the OCR text differs from the page (the mark rests on a phantom)
- `undecidable`: the page does not decide it; goes to the operator

Parallel agents pre-adjudicate; the operator spot-checks a fixed share and decides
every `undecidable`. Each verdict carries a one-sentence reason and lands in the case
file, so the whole sample is re-checkable.

### 3. Adjudicate recall

Every drawn page is read exhaustively against the curated list: each mention of a
listed entity on that page is recorded by hand (agent-assisted, list side by side).
The record is compared with the pipeline output of the same page and each mention is
classed as:

- `hit`: marked tier 1
- `on_worklist`: held back tier 2, visible for curation
- `missed`: neither marked nor on the worklist

Every `missed` gets a cause label: lexicon gap (name form not derivable from list or
cache), rule gap (form present, matcher rule does not reach it), or OCR corruption.
The cause labels are the work list for systematic repair.

### 4. Agreement check

A subsample of 50 precision cases is adjudicated twice by independent adjudicators
who do not see each other's verdicts. The raw agreement rate is reported next to the
headline numbers; without it the measurement itself has unknown reliability. The
operator breaks ties.

### 5. Statistics

Precision and recall are reported with BCa bootstrap confidence intervals per stratum
and overall, reusing the statistics discipline of the CER measurement (seeded,
deterministic, regenerable). Results go to `output/audits/entity_eval_report.json`
plus a readable summary; headline numbers are quoted only with their intervals.

### 6. Consequences

The measurement feeds the system rather than only describing it:

- Every confirmed error becomes a pinned regression test (the existing pattern:
  Weil, the initials variant, the Jaspers homograph).
- Systematic causes become matcher rules, variant-review verdicts, or list proposals
  to ZBZ.
- The numbers gate the stock-marking decision: whether tier-1 marks are written into
  the delivered TEI corpus-wide is decided on measured precision, per category.

## Execution record (snapshot 2026-08-12)

The workflow above has run once, over the whole delivered corpus. The draw was seeded
(seed 42) and stratified as the first phase describes, 300 tier-1 marks for precision
and 40 pages for recall, frozen together with the corpus scan snapshot it was cut from
under `output/audits/eval_sample/`. Nine independent agents adjudicated at the
facsimile under the binding protocol `output/audits/eval_sample/ADJUDICATION.md`, six of
them on precision ranges, two reading the drawn pages exhaustively, one delivering the
blind second judgment on the agreement subsample of 50 precision cases. Every verdict
file was verified against disk before the aggregation.

Where the results live:

- `reports/2026-08-12_entity-eval-ergebnis.md`, the readable result of the snapshot,
  with the headline figures, their intervals, the error classes and the recall causes
- `output/audits/entity_eval_report.json`, the aggregate the statistics phase produces
- `output/audits/eval_sample/`, the raw evidence, sample manifest, case files, verdict
  files and the frozen scan the offsets index into
- `reports/2026-08-12_adjudication-protokoll.md`, the versioned copy of the protocol the
  wave was bound to

The verdict store `data/entities/mention_verdicts.json` is the durable sink of these
judgments. `scripts/eval/build_mention_verdicts.py` folds the loose case and verdict
files into one lookup keyed by (doc, page, surface, gid, occurrence), carrying the
verdict, its reason, the second judgment where one exists, and a sha256 fingerprint of
the delivered TEI the judgment was made on. A later text change moves the fingerprint
and marks the affected records stale, so a rerun re-adjudicates what actually changed
and keeps the rest. The store is described as the persistence layer of the architecture
in [entity-integration.md](entity-integration.md).

The even draw of the precision sample has a risk-ordered complement. The ranking
`scripts/eval/entity_risk_ranking.py` scores every tier-1 mark of the scan by
deterministic features and sorts the corpus into strata under
`output/audits/fp_hunt/risk_ranking.json`, so a hunting wave spends its adjudication
where a false positive is most likely; its protocol is versioned as
`reports/2026-08-12_fp-hunt-protokoll.md`. The seeded sample carries the statistical
statement about the whole mark population, and the ranking concentrates further
adjudication on its suspicious end.

The operator took a convention decision (2026-08-12) on the described part of the
result. Running heads stay outside the marking scope, while title pages, organisation
names in bylines and picture captions are marked. This settles the page-apparatus
question the executed run left open and makes a second, convention reading of precision
computable, precision over the marks the convention keeps in scope. The deterministic
running-head suppression is in place since 2026-08-13 (E108), and the reading is
computed by `scripts/eval/running_head_audit.py` into
`output/audits/running_head_audit.json` (block `convention_precision`): marks inside a
detected head zone leave numerator and denominator, `undecidable` verdicts stay
excluded exactly as in the protocol reading, and the interval is a seeded percentile
bootstrap. The computed reading lies within the interval of the protocol reading, so
the running heads were not inflating the published precision figure. One ground-truth
caveat is recorded: a single adjudicated mark counts as a running head only through
the keyword in its verdict reason while being body text (doc 2510), so the keyword
criterion reads detector recall as 24 of 25 without a real head being missed. A redraw
and a remeasurement still follow the repair wave, so a later run compares against the
same design.

A second convention decision followed on 2026-08-13 (E108): mentions of the corpus
author are marked like every other listed entity, in bylines and signatures as well.
The byline exception whose recall cost the executed run had recorded is removed, and
the recall gaps it caused become hits on a future redraw.

The consequence loop of phase 6 has run for the error side (E109): every confirmed
wrong_entity and wrong_span case of the snapshot is answered by a deterministic matcher
guard or span repair, each pinned as a regression fixture; the catalog lives in
[entity-integration.md](entity-integration.md), section "Adjudicated precision guards".
The rebind of the verdict-store build to the frozen scan snapshot belongs to the same
wave: the occurrence key counts over the frozen tier-1 population the sample was drawn
from, so the store reproduces byte-identically however the live rules move.

## Roles

- Agents: pre-adjudication of drawn cases, exhaustive page reading, statistics runs.
- Operator: spot-checks, tie-breaking, acceptance of the report, gate decision.
- ZBZ: spec questions (what counts as a mention in their editorial practice) and
  list extensions from the recall causes.

## Population validity of a measured rate

A measured rate describes the population the sample was drawn from, and nothing else. Any
rule change that moves marks into tier 1 creates a stratum the existing draw does not
cover, so the published precision stops describing the whole auto-marked layer even though
every sampled mark still holds. The first case of this kind is the anchor-free surname
release (E119), which lifts bare surnames of canonical authors into tier 1 without a
document anchor; those marks exist in no earlier draw.

The rule that follows: after such a change the rate is reported per stratum, the covered
one and the new one, until a supplementary draw over the new stratum has been adjudicated.
A single corpus-wide rate returns only when the draw covers the whole population again.
The same reasoning applies in reverse to a change that removes marks from tier 1, with the
difference that a shrinking population keeps its rate conservative rather than making it
too optimistic.

## Standing layer after the measurement

The sample says how much trust the unverified mass deserves; the per-document
verification stays where it is: a document's entity stream counts as done only when a
human sets its workflow status to `verifiziert` in the viewer. The sampling method
calibrates the default; the status pill records the human decision per object.
