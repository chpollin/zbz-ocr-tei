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
related: [cer-methodology, tei-mapping, data, testing, governance, plan, decisions, journal]
---

# Verification

This document holds the empirical claims the project carries outward, the evidence behind
each one, the procedure that produced that evidence, and what remains open. Lesson L13 of
[journal.md](journal.md) fixes the standard it works to. A figure written into prose, "285/285 valid" being the
original case, is no evidence, so every claim named here is bound to a regenerable artifact
or to an automated gate.

## Subject of verification

Three claims leave the repository and are therefore in scope.

The character error rate of the delivered text layer, measured against the reference corpus
and decomposed into fidelity and scope. The published values live in
`docs/data/cer_statistics.json`, deterministically regenerable with seed 42 through
`scripts.eval.cer_statistics_full`; the public method page and the client-facing project
report quote that file. Metric definition, extraction and normalization rules are in
[cer-methodology.md](cer-methodology.md).

The precision and recall of the entity preview layer, measured on a facsimile-adjudicated
sample of the closed-world marking. The published block is `quality` in
`docs/data/entity_overview.json`, rendered on the entities page; the readable result of the
executed run is `reports/2026-08-12_entity-eval-ergebnis.md`, the aggregate
`output/audits/entity_eval_report.json`. The marking rules the adjudication judges against
are in [tei-mapping.md](tei-mapping.md).

The completeness of the delivery, meaning that every catalogued and delivered scan reaches a
final TEI apart from a named and pinned exception, and that each document's page structure
reconciles with its physical scan. The instruments are `scripts.eval.corpus_audit` and
`scripts.eval.completeness_check`, the gate is `tests/test_corpus_audit.py`. The corpus
material itself is described in [data.md](data.md).

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

The entity adjudication uses a five-value ballot, one value per drawn mark, as the binding
protocol `reports/2026-08-12_adjudication-protokoll.md` defines it:

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
own aggregation, four secondary metrics and facsimile spot checks. The record is
`reports/cer-gegenprobe-2026-07-03.md`, the provenance E91.

Every stock repair that moves the number is verified against evidence before it is applied
and re-measured afterwards. The footnote demotion accepted a block only where a contiguous
stretch of at least 150 characters appears in the ground-truth body (E85); the doc-30
outlier was adjudicated at the facsimile before the targeted re-OCR (E97) and re-measured
after it (E98).

The stability pilot measures run-to-run variance of the refinement stage in isolated run
directories, without touching the production caches or the delivered TEI (E100). Its result
is the `stability` block of `docs/data/cer_statistics.json`.

The interval method behind every published aggregate is the document-level block percentile
bootstrap, seed 42, B = 10,000, resampling documents with replacement and reading the 2.5th
and 97.5th percentile; each aggregate names it in its own `ci_method` field. The paired
comparison against OCR-only runs on per-document differences of the fidelity CER and reports
a percentile interval with a two-sided bootstrap p-value. No BCa interval is computed for
any published value. The statistics library carries a BCa implementation that the publishing
generator never calls; the label in the published JSON was aligned to percentile in E122, and
the remaining library question is a register and planning item.

### The entity claim

The measurement runs in six phases, and the drawn sizes and results of the executed run are
in the register below.

1. Draw. `scripts/entity/entity_eval_sample.py` cuts two seeded samples from a frozen corpus
   scan, a precision sample of tier-1 marks stratified by category and rule family, and a
   recall sample of pages stratified by layout type and language. Every stratification cell
   enters the sample manifest with what was available and what was drawn. Output is one case
   file per drawn unit, carrying document, page, surface, offsets, linked entity, rule,
   context excerpt and facsimile path.
2. Adjudicate precision. Every drawn mark receives one of the five verdicts at the facsimile
   with a one-sentence reason, written into the case file, so the sample stays re-checkable.
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
   `scripts/entity/running_head_audit.py`; the stored field of the executed run is named
   `ci95_bootstrap_percentile_seed42`.
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
the knowledge base states. `tests/test_corpus_audit.py` pins four invariants over the real
data, namely that the funnel is monotonically decreasing, that no final TEI exists without a
source PDF, that every delivered scan is catalogued in the Masterfile, and that the known
completeness gap matches an exact document list, so a new loss and a silent closing of the
gap both fail the gate.
`scripts.eval.completeness_check` works per document, reconciling the expected physical page
count against the `pb` structure of the final TEI, with capped adjustments for page splits and
leading cover leaves so that a facsimile labelling issue does not masquerade as a missing
page, and classifies each document as OK, MINOR, WARNING or MISMATCH. What these gates run on
and how they are invoked is in [testing.md](testing.md).

## Anti-anchoring protocol

Adjudication is organized so that the judgment cannot lean on the artifact it judges.

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
file. The process side of this, the wave contract, the verbatim guardrails, the allowlist
rule for verification runs and the roles, is in [governance.md](governance.md).

## Novelty claims

Three claims of this project are comparative, and only the first reaches outside the
repository. The fidelity CER of the delivered corpus is set against published print-OCR
values; that comparison, its sources and its caveats live in
[cer-methodology.md](cer-methodology.md). The pipeline is compared against its own raw OCR in
a paired test over the same documents, which is internal and free of cross-tool
comparability problems. The entity layer is compared against the reference TEIs, which yields
a trend across the categories.

The comparability caveat for the first claim is substantive. CER values between different
tools stay limited in comparability even under a nominally identical metric, because already
the transformation of structured ground truth into comparison text is an error source when
reading order is not considered, and because the scope threshold of the fidelity
decomposition changes the value. Any citation names the threshold, the reference count and
the date, as the counter-check of 2026-07-03 established.

## Finding register

Dated findings, each with the file that carries its evidence. The decision provenance behind
them is the register in [decisions.md](decisions.md), the session-level record is [journal.md](journal.md).

2026-07-07, concordance of the reference corpus (three parallel readers, provenance E85).
The body coding of the references follows the editorial guidelines in the load-bearing
conventions, among them genre div types, bracketed supplied page numbers, the hyphenation
rule across page breaks, the footnote id scheme, the inline GND entity model and the
rendition vocabulary. Two restrictions hold corpus-wide. No reference fulfils the header
requirement, since all carry the raw Transkribus export stub instead of the ALMA citation, so
header comparisons against the references are meaningless. All carry the undocumented root
attribute `type="naegeli"`. The phenomenon map and the exception catalog derived from this
reading are in [data.md](data.md).

2026-07-03, independent CER counter-check (E91, `reports/cer-gegenprobe-2026-07-03.md`).
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
deterministic in its text effect. A side finding of the pilot is that the absolute fidelity
of fresh regenerations lies far above the delivered values, because the delivered TEI embodies accumulated
corrections the pipeline caches do not reproduce, so only the within-pilot spread is the
measurement. Evidence in the `stability` block of `docs/data/cer_statistics.json`.

2026-08-12, entity evaluation, executed run. Nine independent agents adjudicated at the
facsimile under the versioned protocol, six on precision ranges, two reading drawn pages
exhaustively, one delivering the blind second judgment; every verdict file was verified
against disk before aggregation. Precision over 293 decidable cases of 300 drawn marks is
0.952 with a seeded percentile interval of 0.925 to 0.976. Raw agreement on the 50 doubly
judged cases is 48 of 50, and both disagreements are documented and went to the operator.
Recall over 40 drawn pages covers 67 mentions of listed entities, of which 20 were marked and
17 stood on the worklist, giving a coverage of 0.552; of the 30 misses, 28 are rule gaps and
2 are lexicon gaps. Error classes and repair classes by yield are in
`reports/2026-08-12_entity-eval-ergebnis.md`, the aggregate in
`output/audits/entity_eval_report.json`, the raw evidence under `output/audits/eval_sample/`.

2026-08-13, convention reading of the precision figure (E105, E108). After the operator set
the page-apparatus convention, running heads left the marking scope and the second reading
became computable from the persisted verdicts without drawing again.
`scripts/entity/running_head_audit.py` computes it at 0.9511 over 266 in-scope decidable
cases, inside the interval of the protocol reading, so the running heads were not inflating
the published figure. One ground-truth caveat is recorded, since a single adjudicated mark
counts as a running head only through the keyword in its verdict reason while being body text
(doc 2510), so the keyword criterion reads detector recall as 24 of 25 without a real head being
missed.

2026-08-13, gold benchmark read as a trend. `scripts/entity/entity_gold_benchmark.py` measures
against the reference TEIs, scope-restricted to shared text. Facsimile classification of its
deviations showed that about half of them are convention differences rather than errors,
above all the corpus author in bylines, which the references leave unmarked. Read per
category the trend orders the classes consistently, persons highest, organisations in the
middle, works lowest by a wide margin, and the overall tier-1 figure stays well below the
facsimile-adjudicated precision. The weak work class is the empirical backing for keeping
works on the worklist in the first stock wave. After the guard wave the reference trend rose
to tier-1 precision 0.67 with recall and coverage unchanged, which is the expected signature
of pure false-positive removal (E109). The figure is the state at that date as the register
records it; `output/audits/entity_gold_benchmark.json` regenerates with every run and carries the
current trend.

2026-08-13, first verdict-guard run (E110), on the scan of the repaired state. All 279
adjudicated correct marks survive, 252 in tier 1 and 27 as legitimate moves to the worklist;
10 of 14 wrong marks are repaired, and the remaining 4 are text-side defects outside the
matcher's reach, an OCR phantom on a blank leaf, a hallucination loop and a generated speaker
duplication. Of the 30 adjudicated misses 27 now surface. The figures are the state at that date as E110
records it; `output/audits/verdict_guard_report.json` regenerates with every guard run.

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
the whole auto-marked layer even though every sampled mark still holds. Until a supplementary
draw over the new stratum is adjudicated, the rate is reported per stratum, the covered one
and the new one. A fresh draw over the current population together with a recall
remeasurement on newly read pages comes before further rule work, and
[plan.md](plan.md) carries it as a work item. The same reasoning applies in reverse to a
change that removes marks from tier 1, with the difference that a shrinking population keeps
its rate conservative.

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

The measured rates calibrate how much trust the unverified mass deserves. The decision per
object stays with the human, who sets a document's workflow status per stream in the viewer;
that standing layer is described in [workflow.md](workflow.md), section on the per-object
manifest and workflow status.

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
