---
title: Governance
project:
  name: zbz-ocr-tei
  repository: https://github.com/chpollin/zbz-ocr-tei.git
method:
  name: Promptotyping
  url: https://dhcraft.org/Promptotyping/
status: complete
language: en
version: 1.0
created: 2026-08-12
updated: 2026-08-21
authors: [Christopher Pollin]
related: [methodology, verification, testing, journal, decisions, plan]
---

# Governance

Who decides what in this project, and how multi-agent work is run so that its results are
verifiable. The scholarly role model with its separated competencies lives in
[methodology.md](methodology.md), section Critical Expert in the Loop; this document holds
the wave roles, the authority to release and to commit, and the rules that make an agent
report count as evidence. The claims that verification produces are recorded in
[verification.md](verification.md).

## Authority and decisions

The operator releases waves, decides contested cases, and gates every write into the
delivered stock. Stock corrections on `output/tei_final/` run only on an explicit operator
release, always with a dry run first and always reversible through their backup (E94).
Merges, tags and releases stay operator-gated. Agents never commit and never push; the
orchestrator commits after verification.

ZBZ decides the editorial and cataloguing questions, which cover the guidelines and their
interpretation, the header metadata drawn from Alma, subject headings, and the caption
contradiction of the ZBZ README (O8, O13, O27 in [decisions.md](decisions.md)). ZBZ also
answers what counts as a mention in its editorial practice and supplies list extensions
that recall causes reveal. Because ZBZ feedback is not available in this project phase, the
open convention questions of the entity layer fall to the operator, who decided them on
the record from 2026-08-12 onward (E105, E108, E119).

DHCraft carries project management, which sets priorities and accepts results, and the
development side, which configures the process. The separation matters because the party
that produced a result does not review it scholarly.

## Sources and their status

Every fact has exactly one owner document, and other documents point to it. The same rule
holds for data. `output/tei_final/` is the single source of truth of the delivered TEI
(E43) and `docs/data/` is a generated mirror that is never edited directly; a change to the
source is followed by a regeneration of the mirror.

[decisions.md](decisions.md) is the register of dated decisions and holds the rationale and
the rejected alternatives; [journal.md](journal.md) holds the course of the sessions. A
claim about why something is the way it is belongs in one of the two. Code comments and
durable knowledge documents carry no second version of it.

The working files of a wave, the protocol files, the frozen samples and the per-agent
result files, live under the gitignored `output/` tree and are handed to agents by path.
They are the state that survives a context window, so anything that matters is written to
a file rather than kept in a conversation. Model judgments that shall have lasting effect
are written into versioned verdict files and consumed deterministically afterwards, so no
live model call sits on the critical path of a reproducible run.

## The wave pattern

Work is released in waves of parallel agents, each wave following the same contract.

1. One agent, one bounded task, one disjoint file scope. Agents in the same wave never
   share writable files; shared inputs are read-only. Where many agents write the same kind
   of result, each writes its own file into a collection directory and the orchestrator
   merges, which is how the adjudication verdicts were produced.
2. Specification before delegation. The task prompt names the goal, the concrete file
   scope, the verification the agent must run itself, and the report format. For repetitive
   waves the shared rules move into a protocol file in the repository and every prompt
   binds the agent to it; the prompt then carries only the per-agent range and output path.
3. Guardrails travel verbatim. Security and scope rules are copied into every prompt or
   into the binding protocol file, never paraphrased.
4. Subagents run on an explicitly named strong model, and the orchestrator never lets its
   own model be inherited implicitly. Delegation stays flat, so agents do not spawn agents.

## Guardrails

The standing set is passed into every agent prompt word for word. Never read `.env`, no
secrets in code or docs, no Grokipedia, no LLM-based identifier assignment, no cost
figures, ASCII-safe prints on Windows, never touch files held by another instance, no
writes outside the named file set, no commits, no pushes, no git state changes, no
subagents.

A wave that runs scripts names an allowlist of the scripts it may run, and anything that
writes under `output/audits/eval_sample*` or `data/` is excluded by name. The rule comes
from an incident in wave 3 of the repository refactoring (E123), where a smoke-test run of
the evaluation sampler overwrote a frozen draw that the adjudication protocol had declared
untouchable. The draw was reconstructed from two frozen inputs and the tracked data was
restored, but the reconstruction is not the original file set, and a deliberate re-freeze
remains an operator decision. The prohibition had stood in the protocol file already, so
each wave now enumerates its executable surface in the prompt itself.

## Verification of agent results

An agent self-report counts as unverified until it is checked against the real file state.
The orchestrator re-runs the decisive checks itself, test suites, file existence, the
counts in the produced JSON, before integrating or committing anything. Adversarial
verification is used where findings are cheap to claim and expensive to trust, so
independent verifier agents try to refute findings before they enter the record.

Each wave of the refactoring closed with two independent verifiers, one over code and one
over documents, and the orchestrator spot-checked at least three claims per report against
the disk before committing (E120 to E123). The code side re-ran the full test suite, the
linter, the command reference and the mirror regeneration; the document side checked that
every relative link resolves, that no removed statement lost its owner, and that no new
volatile quantity entered a durable document. The gates themselves are described in
[testing.md](testing.md).

Every wave also starts by checking that the artifacts under review match the current code
state, because an audit of a stale artifact produces findings that were already fixed.

## Roles

- Orchestrator, the main instance, decomposes the work, writes protocol files, launches
  waves, verifies, merges, commits per package, and keeps the journal and the decision
  register.
- Build agents implement one bounded change test-first inside their file scope.
- Analysis agents run read-only investigations and write only into report directories.
- Adjudication agents judge drawn cases against the source, the facsimile, under a fixed
  verdict scheme; a designated second adjudicator works blind so that inter-annotator
  agreement can be measured.
- Verifier agents check a finished wave against the disk and try to refute its reports.
- The operator releases waves, spot-checks, breaks ties, accepts reports, and gates every
  stock write.
- ZBZ answers specification questions from editorial practice and supplies list extensions.

## Parallel instances

Several instances work in the same tree at the same time. Before an edit, `git status` plus
verification against the real file state is mandatory, and a conflict of the kind "file
modified since read" is the signal to step back rather than to force the write (L12). A
file another instance holds stays untouched until that instance has committed, which is why
a document under an uncommitted foreign diff is excluded from a wave by name in the
guardrails. A tree with foreign modifications is not committed wholesale; staging names
explicit paths.

## What made the pattern work

The corpus-scale evaluation waves became reliable only after three ingredients were in
place, and they are the transferable core. A frozen, seeded sample lets agents judge a
fixed set, so results merge without coordination. A written verdict scheme with exactly one
value per case keeps agents from drifting into free-form prose. Per-agent output files
avoid write conflicts and keep every judgment attributable. The three apply wherever many
agents assess many items, independent of the domain.

Two further lessons come from the entity waves. Evaluation panels are drawn by impact and
class coverage, top-wrap documents, excluded-zone classes, German prose; a draw by document
count alone misses the classes that matter. Evaluator schemas separate a genuinely lost mention from a mention that sits
on the worklist, because a schema that conflates them produces a number nobody can act on.

## Known limits

Agent self-reports overstate completion under ambiguity, so verification against disk is
not optional. Long waves outlive a context window, so all state that matters lives in
files, in samples, protocols and verdicts; conversation alone holds none of it. Permission
boundaries differ per environment, so an agent may be unable to perform an operator-gated
action the orchestrator predicted it could, and the wave design has to tolerate that by
letting the agent report and hand back instead of working around the boundary.
