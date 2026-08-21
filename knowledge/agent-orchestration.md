---
title: Agent Orchestration Workflow
type: knowledge
project:
  name: zbz-ocr-tei
  repository: https://github.com/chpollin/zbz-ocr-tei.git
method:
  name: Promptotyping
  url: https://dhcraft.org/Promptotyping/
status: active
language: en
created: 2026-08-12
updated: 2026-08-21
tags: [zbz-ocr-tei, agents, orchestration, verification, methodology]
related: [methodology, entity-evaluation, entity-integration]
authors: [Christopher Pollin]
---

# Agent Orchestration Workflow

How this project runs multi-agent work so that results are verifiable and the pattern
transfers to other projects. The methodological frame (Command / Artifact / Tool,
verification cascade) lives in [methodology.md](methodology.md); this document holds
the orchestration layer above it, distilled from the build and evaluation waves of
the entity integration (journal, session 93).

## The wave pattern

Work is released in waves of parallel agents, each wave following the same contract:

1. One agent, one bounded task, one disjoint file scope. Agents in the same wave
   never share writable files; shared inputs are read-only. Where many agents write
   the same kind of result, each writes its own file into a collection directory
   and the orchestrator merges (the adjudication verdicts are the model case).
2. Specification before delegation. The task prompt names the goal, the concrete
   file scope, the verification the agent must run itself, and the report format.
   For repetitive waves the shared rules move into a protocol file in the repo
   (`ADJUDICATION.md` pattern) and every prompt binds the agent to it; the prompt
   then only carries the per-agent range and output path.
3. Guardrails travel verbatim. Security and scope rules are copied into every
   prompt or into the binding protocol file, never paraphrased. Standing set here:
   never read `.env`, no secrets in code or docs, no Grokipedia, no LLM-based id
   assignment, no cost figures, ASCII-safe prints on Windows, never touch files
   held by other instances, no commits and no subagents from within an agent.
4. Model policy: subagents run on an explicitly named strong model; the
   orchestrator never lets its own model be inherited implicitly. Delegation stays
   flat, agents do not spawn agents.

## Verification of agent results

An agent's self-report counts as unverified until checked against the real file
state. The orchestrator re-runs the decisive checks itself (test suites, file
existence, counts in the produced JSON) before integrating or committing anything.
Adversarial verification is used where findings are cheap to claim and expensive to
trust: independent verifier agents try to refute findings before they enter the
record. Model judgments that shall have lasting effect are written into versioned
verdict files and consumed deterministically afterwards (variant review pattern), so
no live model call sits on the critical path of a reproducible run.

## Roles

- Orchestrator (main instance): decomposes work, writes protocol files, launches
  waves, verifies, merges, commits per package, keeps journal and decision register.
- Build agents: implement one bounded change test-first inside their file scope.
- Analysis agents: read-only investigations that write only into report directories.
- Adjudication agents: judge drawn cases against the source (facsimile) under a
  fixed verdict scheme; a designated second adjudicator works blind for the
  inter-annotator agreement.
- Operator: releases waves, decides contested cases, gates every stock write.

## What made the pattern work here

The corpus-scale evaluation waves only became reliable after three ingredients were
in place, and they are the transferable core: a frozen, seeded sample (agents judge
a fixed set, so results merge without coordination), a written verdict scheme with
exactly one value per case (agents cannot drift into free-form prose), and per-agent
output files (no write conflicts, every judgment attributable). The same three
ingredients apply wherever many agents assess many items, independent of the domain.

## Known limits

Agent self-reports overstate completion under ambiguity; verification against disk
is not optional. Long waves outlive one context window, so all state that matters
must live in files (samples, protocols, verdicts), never only in conversation.
Permission boundaries differ per environment; an agent may be unable to perform an
operator-gated action the orchestrator predicted it could, and the wave design must
tolerate that (report and hand back instead of working around).
