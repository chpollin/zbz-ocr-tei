---
title: "Methodology: Epistemic Infrastructure and Promptotyping"
project:
  name: zbz-ocr-tei
  repository: https://github.com/chpollin/zbz-ocr-tei.git
method:
  name: Promptotyping
  url: https://dhcraft.org/Promptotyping/
template:
  name: Vorlage Domänenwissen
  version: 0.2
  url: https://dhcraft.org/Promptotyping/promptotyping-document/domain-knowledge
status: complete
language: en
version: 1.0
created: 2026-03-15
updated: 2026-08-21
authors: [Christopher Pollin]
related: [governance, verification, pipeline, workflow, specification]
---

# Methodology

Epistemic infrastructure, verification cascade, Critical Expert in the Loop, and the
operative Promptotyping cycle.

## Epistemic Infrastructure

Agent reliability does not scale with model capability alone but with the quality of the
epistemic infrastructure in which the model operates (evidenced by SWE-bench vs. SWE-bench
Pro, ~60 percentage points difference with identical models).

For agents the repository is not a storage location but their primary interface. Three
properties must hold:

- Readability: every artifact has a documented purpose ([CLAUDE.md](../CLAUDE.md), knowledge
  docs); new artifacts must be reflected there (maintenance duty).
- Consistency: paths, naming, and data formats follow uniform conventions. What was learned
  on one document holds for all.
- State transparency: the processing state of every object is machine-queryable (JSON
  reports, `<revisionDesc>` in the TEI header).

## Verification Cascade

Four levels, ordered economically (cheap first, expensive last):

1. Automatic: schema validation, Python tests. Binary, fast, filters obvious errors.
2. Contextual: an LLM checks content plausibility against the project context. Graded result
   (plausible/questionable/implausible).
3. Visual: facsimile comparison by a vision-capable agent or LLM-as-judge. A different
   modality means epistemic diversity.
4. Domain: domain expertise, not delegable. The edition scholar decides on ambiguities.

The operative effect is that each level reduces the case set for the next. Domain expertise
is focused on its highest-value area of application (asymmetric amplification).

## Operative Cycle (Promptotyping)

Five steps, iterative (aligned with ReAct's thought-action-observation loop):

1. Diagnosis: the agent determines the state via diagnostic artifacts (read the validation
   report). Act on findings, not on assumptions.
2. Exploration: prioritize the corrective measure by the largest quality gain. Structural
   errors before reference errors before formatting.
3. Execution: the agent invokes an artifact. Where API costs arise, use `--dry-run` and
   check back.
4. Re-validation: run the diagnosis again, compare before and after. Every unverified change
   is a hypothesis, not an improvement.
5. Escalation: after a defined number of iterations or on stagnation, hand the problem to the
   right expert in the loop.

Termination conditions are a maximum of 2-3 cycles per document, a stagnation indicator, and
error-pattern detection.

## Critical Expert in the Loop

Several roles with separated competencies prevent circular validation (anchoring effect,
evidenced by Schroeder et al. 2025):

- DH developer: process configuration (prompts, scripts, thresholds). Does not interact with
  scholarly content.
- Edition scholar: scholarly assessment of the results. Did not configure the process.
- Project management: prioritization and acceptance.

The core principle is that the person who produced a result (or whose agent produced it) is
not the same person who reviews it scholarly. This section owns the scholarly role model,
while the wave roles of the multi-agent process, the guardrails an agent receives verbatim
and the authority to accept a self-report belong to [governance.md](governance.md).

## Three-Layer Model: Command / Artifact / Tool

| Layer | What | Example |
|---|---|---|
| Command | decision rule (when, under which conditions) | "Validate after every TEI correction" |
| Artifact | material tool (versioned, maintainable) | `tei_validator.py`, `corpus_audit.py`, [CLAUDE.md](../CLAUDE.md) |
| Tool | concrete invocation by the agent | `python -m scripts.tei.tei_validator --doc 290` |

Commands without artifacts stay abstract. Artifacts without commands lie unused. Tools
without commands are ad-hoc actions. Only the interplay of all three layers produces the
cyclic, quality-assured work process.

Artifacts are fed-back output, at once a result of the process and input for the next cycle.
The epistemic infrastructure grows reactively on quality signals.

## Operative Tools (CLI)

The complete CLI reference lives in the project constitution [CLAUDE.md](../CLAUDE.md),
section Commands, which is the single source of truth for every command and every flag.
What belongs here is the order in which those commands are used, the operative cycle above
applied to the artifacts.

Diagnosis opens every cycle. The state is read from a diagnostic artifact, in the standard
case from the corpus validation report of the TEI validator; an assumed state never starts
a cycle. Exploration ranks the findings by expected quality gain, structural defects before
reference deviations before formatting. Execution invokes one artifact against the selected
case and runs as a dry run first wherever API calls or writes into `output/tei_final/` are
involved. Re-validation repeats the diagnostic step and compares the state before and
after, because only that comparison shows whether the change improved anything. Escalation
hands the case to the expert in the loop once the iteration cap or a stagnation indicator
is reached, which for the delivered corpus means page-wise, facsimile-verified curation in
the viewer.

Every step produces or transforms a knowledge artifact and emits machine-readable quality
signals. The statistics artifact `docs/data/cer_statistics.json` is the deterministic
example of such a signal.

## Conventions

- Document IDs follow the pattern `{DOC_ID}` (e.g. 2310, 2530, 1440).
- Outputs go to `output/` subdirectories (gitignored, except `data/curated_tei/`).
- `--dry-run` is available on every tool that calls an API or writes into `output/tei_final/`.
  It reports the intended change without carrying it out and is the mandatory first run
  before batch operations and before the stock corrections.
- `--force` discards cached results and recomputes them, the paid stages included. It is
  sensible only after an actual upstream change.
- A changed step-2 prompt requires invalidating the step-2 cache by hand, because `--force`
  does not regenerate it (lesson L5 of [journal.md](journal.md)).
- `--reassemble` redoes the rule-based stages of `tei_unified`, the step-1 scaffold built
  from the curated OCR and layout and the step-3 assembly, and reuses the Gemini step-2
  cache. Pages without newer curation need no API call. Pages whose curated OCR or layout is
  newer than the cache are selectively re-refined with one Gemini call each, because step 3
  would otherwise assemble from the stale cache and the curation would never reach the final
  TEI. That refinement re-derives the text, so a corrected OCR line reaches the final TEI as a
  suggestion and may be reworded. A word-exact change is made in the viewer's TEI-XML mode,
  which writes `output/tei_final/{DOC_ID}_final.xml` directly and deterministically. `--force` re-refines the whole document instead of selected pages.

## Literature

- Yang et al. (2024). *SWE-agent: Agent-Computer Interfaces.* NeurIPS 2024. Scaffolding beats model capability.
- Kamoi et al. (2024). *When Can LLMs Actually Correct Their Own Mistakes?* TACL. Self-correction needs external feedback.
- Schroeder, Roy, Kabbara (2025). *Just Put a Human in the Loop?* Findings of ACL. Anchoring effect with LLM suggestions.
- Yao et al. (2023). *ReAct: Synergizing Reasoning and Acting.* ICLR 2023. Thought-action-observation loop.
- He et al. (2026). *Speed at the Cost of Quality.* MSR 2026. Speed without infrastructure creates technical debt.
- Zhang et al. (2025/2026). *Agentic Context Engineering (ACE).* arXiv. Accumulated context knowledge compensates model capability.

## References

- [pipeline.md](pipeline.md): technical pipeline architecture
- [workflow.md](workflow.md): the viewer as verification environment, the workflow status per stream
- [governance.md](governance.md): the multi-agent wave pattern, guardrails and role authority
- [verification.md](verification.md): the verification chain behind the published claims
- [specification.md](specification.md): quality method and validation rules
- [CLAUDE.md](../CLAUDE.md): project rules, complete CLI reference
