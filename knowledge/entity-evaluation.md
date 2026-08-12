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

## Roles

- Agents: pre-adjudication of drawn cases, exhaustive page reading, statistics runs.
- Operator: spot-checks, tie-breaking, acceptance of the report, gate decision.
- ZBZ: spec questions (what counts as a mention in their editorial practice) and
  list extensions from the recall causes.

## Standing layer after the measurement

The sample says how much trust the unverified mass deserves; the per-document
verification stays where it is: a document's entity stream counts as done only when a
human sets its workflow status to `verifiziert` in the viewer. The sampling method
calibrates the default; the status pill records the human decision per object.
