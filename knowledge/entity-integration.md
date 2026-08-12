---
title: Entity Integration
type: knowledge
project:
  name: zbz-ocr-tei
  repository: https://github.com/chpollin/zbz-ocr-tei.git
method:
  name: Promptotyping
  url: https://dhcraft.org/Promptotyping/
status: draft
language: en
created: 2026-08-12
updated: 2026-08-12
tags: [zbz-ocr-tei, entities, gnd, design-plan]
related: [specification, decisions, ground-truth-map, pipeline, journal]
authors: [Christopher Pollin]
---

# Entity Integration

Design plan for bringing the curated GND entity list into the delivered TEI corpus. This
document is the starting point of the entity documentation. Decisions made during the
work get E entries in [decisions.md](decisions.md); sessions go to
[journal.md](journal.md). Convention function: freehand design plan, because the template
catalogue holds no plan template.

## Goal

Every mention of a listed entity in the delivered TEI gets an inline GND reference. The
quality is measured. The text itself never changes by a single character.

## Input data

Three sources:

- The curated entity list `all_entities.json` (target location `data/entities/`,
  git-tracked). Three categories: persons, organisations, works. Every entry has a GND
  id. The intake audit `entity_lint` reports the known defects and excludes them from
  matching; fixing them is the job of the tool that produced the file. The list carries
  an `editor_reviewed` flag whose role is an open decision.
- The lobid-GND API. One lookup per id, stored as a versioned cache with retrieval date
  (`data/entities/gnd_cache.json`). The cache supplies name variants (transliterations,
  translated titles, short forms), life dates, entity types, and Wikidata QIDs. The same
  pass validates the list, because defective ids answer with 404.
- The old mention index `output/gnd_analysis/gnd_entities.json`, left over from the
  removed NER stage (E71). It contributes name forms that actually occur in 18 reference
  TEIs. Its ids lack the GND check character; normalize them before joining.

## Target model

The binding convention is the ZBZ inline GND model (E88), as the 25 reference TEIs show
it: `persName`, `orgName`, and `bibl` with `ref="GND:..."` directly at the mention,
again at every repetition. No register, no places, no foreign ids, no `@key`. The text
stays as it is; the tool only wraps existing characters in tags.

Detail rules, checked against the reference corpus:

- `bibl` wraps an existing `<hi rendition="#i">`; the italics stay inside.
- For works, only the title is marked. Publisher and imprint stay outside the element,
  also in footnotes. The references sometimes mark wider spans; those stay manual
  curation. The automatic tiers mark titles only.
- Footnote citations do get GND refs. Only `bibl` inside `div type="bibliography"` stays
  without a ref (rule Z1).
- Nesting is allowed (operator decision 2026-08-12): a `persName` with its own ref may
  stand inside a `bibl`. This is valid against `zbz_hersch.rng`. The references never
  nest, so the gold benchmark counts correct nested markup as neutral, never as an error.
- Existing entity elements without `@ref` (today the plain `bibl` stock) get the
  attribute added in place, but only where the assignment is verified through the same
  tier rules (operator decision 2026-08-12). Their text stays untouched.
- Particles stay outside the element (`d'` before a name). The whole inflected word goes
  inside. An element boundary never splits a word.
- Names can run across line breaks, even inside a word (`break="no"`). Matching
  therefore runs on text with line breaks normalized away.
- Interview speakers follow the reference pattern `speaker > persName@ref`. The colon
  stays outside the name element.

Open modelling points, owned outside this plan:

- Image captions: the ZBZ guideline contradicts itself here (O27). The matcher skips
  captions and reports caption candidates separately. ZBZ decides; adding them later is
  a small follow-up run.
- Empty `speaker` elements stay curation slots (warning W17). The matcher never invents
  text; it only wraps names that are already there.
- Adjective forms of names: the guideline excludes them, but the references mark at
  least one. The automatic tiers mark noun forms only (name word plus a fixed list of
  genitive endings). Adjective candidates go to the worklist; the contradiction goes to
  ZBZ.
- Whether bylines and running headers naming the author are marked: the pilot checks
  this against the references.

## Matching method: three tiers

The list has no mention positions, so finding the mentions is the core work. One
principle binds every tier: a language model never assigns ids. Candidates and their GND
ids always come from the list. A model may only pick among presented candidates, and it
must be able to answer "none of them" (E62; lesson from E66: no checker certifies
itself).

1. Tier one, automatic. Clear hits are marked directly: full names (also inverted, also
   across line breaks), distinctive organisation names and work titles, initial plus
   unambiguous surname, a bare surname after a full-name mention of the same entity in
   the same document, speaker slots.
2. Tier two, judge. Ambiguous hits (bare surnames that collide with common words or with
   each other, short titles) go to a calibrated model. It only chooses between the
   deterministic candidates. Its verdicts are saved as files and checked by human
   samples.
3. Tier three, worklist. What no rule can find (allusions, badly OCRed names) goes on a
   list for human curation. Whether this tier is part of the delivery at all is decided
   by the gold measurement, because the references show what ZBZ itself marks.

The tier borders are empirical: a rule that makes errors on the gold standard moves down
one tier.

## Architecture

- `scripts/tei/fetch_gnd_variants.py`: lobid retrieval, writes the cache.
- `scripts/tei/entity_matcher.py`: lexicon and tier logic. Importable, analysis only.
- `scripts/tei/tei_entity_preview.py`: pilot runner. Writes to `output/entity_preview/`
  (model: `tei_reassemble_preview`).
- `scripts/tei/tei_entity_marker.py`: the later stock-run tool on `marker_common`
  (dry-run first, backup, byte-splice inside `text` only, idempotent, operator-gated).
- `scripts/eval/entity_lint.py`; later `entity_gold_benchmark.py` and `entity_audit.py`.
- `tests/test_entity_matcher.py` with the documented hard cases as fixtures.
- `data/entities/` holds list and cache. All run output stays under `output/`.

## Milestones

Each milestone ends with one coherent commit on main, pushed, plus a journal entry.
Decisions on the way get E entries. Nothing before M7 touches `tei_final`.

| Milestone | Content | Done when |
|---|---|---|
| M0 | Design plan recorded; entity list location fixed | this document committed, list versioned under `data/entities/` |
| M1 | GND cache and `entity_lint` | cache builds reproducibly, lint reports exactly the known defects, tests green |
| M2 | Matcher as analysis tool | tier logic works, hard-case fixtures green, no write path |
| M3 | Pilot on ten documents | preview files valid against the schema, report reviewed, findings in the journal |
| M4 | Gold benchmark | measured once on the held-out references with frozen rules; result JSON versioned under `docs/data/` |
| M5 | Judge calibration | accuracy and stability measured on ambiguities the gold already resolves |
| M6 | Corpus dry-run | full change preview and distribution report reviewed by the operator |
| M7 | Stock run | operator releases the marker run; gates green, mirror regenerated, register entry written |

Pilot panel (M3): gold half 1060, 100, 290, 1440, 890; transfer half 1350, 1360, 2030,
1220, 3090. The panel covers the corpus languages, the interview form, and the known
ambiguity classes. Type D and the encyclopedia form are deliberately not covered; 760
and 3040 are the swap candidates.

## Verification

Four layers, ordered by what each one can prove:

1. Gold measurement. Precision and recall against the reference TEIs. Rules are
   developed on the 18 documents the old index covers and measured once, with frozen
   rules, on the 7 held-out ones. The comparison only uses the text that reference and
   pipeline share (the same scope idea as the fidelity CER). The error lists name every
   wrong hit and every miss one by one.
2. Judge calibration. The model is tested on ambiguous cases the references already
   resolve, including how stable its answers are across repeated runs.
3. Sample checks beyond the gold. A script draws seeded, stratified samples. Independent
   agents check each sampled case against the facsimile, with the explicit task to
   refute it. Verdicts are saved; a script aggregates them; the rule of three sets the
   sample size. Disagreement goes to the operator.
4. Technical gates. Text extraction must be byte-identical over the whole corpus before
   and after. The CER statistics must reproduce deterministically. Schema gate,
   conformity rules Z1 to Z4 and Z8, idempotence proof (a second run finds nothing),
   full pytest suite. Gold tests skip themselves where the local-only reference data is
   missing.

## Open operator decisions

1. Location and versioning of the entity list (proposal: `data/entities/`, git-tracked).
2. Works in tier one, or worklist-only in the first wave (proposal: persons and
   organisations first).
3. Curation channel for tiers two and three (viewer, teiCrafter, or verdict files).
4. Role of `editor_reviewed` (proposal: report field, no gate function).
