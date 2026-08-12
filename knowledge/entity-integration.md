---
title: Entity Integration
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
updated: 2026-08-12
tags: [zbz-ocr-tei, entities, gnd, design-plan]
related: [specification, decisions, ground-truth-map, pipeline, journal]
authors: [Christopher Pollin]
---

# Entity Integration

How the curated GND entity list becomes inline entity markup in the delivered TEI
corpus. This document holds the whole workflow: data, rules, instruments, milestones,
verification. Decisions taken on the way receive E entries in
[decisions.md](decisions.md); session history lives in [journal.md](journal.md).
Convention function: freehand design plan, because the template catalogue holds no plan
template.

## Goal

Every mention of a listed entity in the delivered TEI gets an inline GND reference. The
quality is measured before anything touches the stock. The text itself never changes by
a single character.

## Input data

- The curated entity list `data/entities/all_entities.json` (git-tracked). Three
  categories: persons, organisations, works; every entry has a GND id. The list is an
  external export; no repo tool produces its format. The intake audit `entity_lint`
  reports its defects and excludes them from matching; fixing them belongs to the
  producing tool. One defect class only the API lookup exposes: ids that are formally
  plausible but unknown to the GND, typically DNB catalog numbers mistaken for GND ids.
- The GND cache `data/entities/gnd_cache.json` (git-tracked, dated), built by
  `fetch_gnd_variants` with one lobid-GND lookup per id. It supplies the name variants
  that bridge transliteration gaps (the list says "Sacharov", the text says "Sacharow"),
  translated work titles, life dates, entity types, and Wikidata QIDs. Defective ids
  answer 404, so the same pass validates the list.
- The legacy mention index `output/gnd_analysis/gnd_entities.json` (pre-E71 remnant)
  contributes surface forms attested in 18 reference TEIs. Its ids lack the GND check
  character and are normalized before joining.

Every data channel, present or future, is its own trust boundary and passes three
steps before its forms may match, an intake lint, a shape-class review of the forms
it contributes, and a pilot round. Which tier a form may serve follows from the
form's own distinctiveness; the authority of the source never lifts a form class
into tier 1. The lobid variants set the precedent, since `variantName` mixes
transliterations, translations, pseudonyms, inverted forms and abbreviations, and
only the shape-based filters in the matcher make the usable subset explicit.

## Target model

The binding convention is the ZBZ inline GND model (E88), as the 25 reference TEIs show
it: `persName`, `orgName`, and `bibl` with `ref="GND:..."` directly at the mention,
again at every repetition. No register, no places, no foreign ids, no `@key`. The
surface form in the text stays untouched; the tool only wraps existing characters.

Detail rules, settled against the reference corpus and by operator decision:

- `bibl` wraps an existing `<hi rendition="#i">`; the italics stay inside.
- For works, only the title is marked, also in footnotes; imprint stays outside the
  element. Wider citation spans occurring in the references stay manual curation.
- Footnote citations do get GND refs. Only `bibl` inside `div type="bibliography"`
  stays without a ref (conformity rule Z1).
- Nesting is permitted (operator decision 2026-08-12): a `persName` with its own ref
  may stand inside a `bibl`; validated against `zbz_hersch.rng`. The references never
  nest, so the gold benchmark scores correct nesting as neutral.
- Existing entity elements without `@ref` are enriched with the attribute in place,
  only where the tier rules verify the assignment (operator decision 2026-08-12).
- Particles stay outside the element (`d'` before a name); the whole inflected word
  goes inside; an element boundary never splits a word. Genitive endings belong to the
  surface, a trailing apostrophe does not.
- Names run across line breaks, including mid-word breaks with `break="no"`; matching
  runs on lb-normalized text.
- Interview speakers follow the reference pattern `speaker > persName@ref`, colon
  outside the element.
- The stock run documents itself in the header: one dated `<change>` entry per run in
  `revisionDesc` (E42 convention, idempotent, pattern of `tei_status_marker`). Preview
  files carry no header entry; their provenance is the pilot report.

Open modelling points, owned outside this plan:

- Image captions: the ZBZ guideline contradicts itself (O27). The matcher skips figure
  contexts and reports caption candidates separately; ZBZ decides.
- Empty `speaker` elements stay curation slots (W17); the matcher never invents text.
- Adjective forms of names: the guideline excludes them, the references mark at least
  one. The automatic tiers exclude them; candidates go to the worklist; the
  contradiction goes to ZBZ.
- Whether bylines and running headers naming the author are marked (all-caps title-page
  mentions are currently not found, matching is case-sensitive).

## Matching method: three tiers

The list holds no mention positions, so finding mentions is the core work. One
principle binds every tier: a language model never assigns ids. Candidates and their
GND ids come from the list; a model may only pick among presented candidates and must
be able to answer "none of them" (E62; lesson from E66: no checker certifies itself).

1. Tier one, automatic: full names (also inverted, also across line breaks), full-name
   variants from the GND cache, initial plus unambiguous surname, distinctive
   organisation names and multi-word work titles, speaker slots, and bare surnames with
   a document anchor. The anchor counts document-wide (operator decision 2026-08-12): a
   full-name tier-1 mention of the entity anywhere in the document anchors every bare
   occurrence of that surname, also before the full name, provided exactly one anchored
   entity carries the surname there.
2. Tier two, judge: ambiguous hits (bare surnames without anchor or colliding with
   common words, single-word titles, candidates inside plain `bibl`, markup-crossing
   hits). A calibrated model chooses between the deterministic candidates; verdicts are
   persisted as files and sampled by humans.
3. Tier three, worklist: what no rule can find (allusions, badly OCRed names) goes to
   human curation. Whether this tier is delivery scope at all is decided by the gold
   measurement.

The tier borders are empirical: a rule that produces errors on the gold standard moves
down one tier. A form class whose candidate set systematically misses the true bearer
never enters tier 2 either; a judge that only sees wrong candidates is invited to pick
one, so such mentions go straight to tier 3 (in the pilot's initials case, "J. H."
meant the interviewee, whose record carries no initials variant, while the one
presented candidate was the wrong person). Mentions of entities outside the list are out of
scope (closed world, E71 lesson); an optional frequency report of unmatched
capitalized candidates is diagnosis only.

## Instruments

Built, each with its pytest suite:

- `scripts/tei/fetch_gnd_variants.py` builds the cache; parser pinned against lobid
  format drift; the committed cache carries a shape-contract test.
- `scripts/eval/entity_lint.py` audits the list offline (labels, id syntax, duplicates,
  DNB links, author resolution) and against the cache (404s, name and type
  consistency); the known real-stock defects are pinned as tests.
- `scripts/tei/entity_matcher.py` builds the lexicon (headwords, inverted forms, cache
  variants, legacy surface forms) and finds candidates with exact offsets. Exclusion
  zones: everything outside `text`, figures, bibliography divs, already marked
  elements. Contract: candidates are offset-verified, non-overlapping, and may embed at
  most `lb` tags. Variant-derived surnames pass a distinctiveness filter, because raw
  lobid variants contribute noise tokens. Variants made only of dotted initials
  ("J. H." for Pestalozzi) never enter the full-name channel; the pilot evaluation
  showed such a variant claiming every "J. H." of an interview for the wrong person
  (doc 1220). More listed entities carry initials variants of this kind; the planned
  lexicon audit reports the current set.
- `scripts/tei/tei_entity_preview.py` wraps tier 1 into `output/entity_preview/` and
  proves per document: RelaxNG-valid against `zbz_hersch.rng`, text of the `text`
  subtree character-identical, byte-identical outside the insertions (bytes in, bytes
  out; stripping the wrappers restores the original). It refuses to write into
  `output/tei_final` and reports JSON plus HTML.

Planned:

- `scripts/eval/entity_lexicon_audit.py` (before M4): groups every form the built
  lexicon would match by shape class (dotted initials, single tokens at the length
  floor, all-caps forms, forms with digits, non-Latin scripts) with counts and
  examples, so the operator approves or bans whole classes instead of chasing single
  forms; rerun after every cache refresh. A second, independent layer before the
  corpus dry-run (M6) is an adversarial agent review of the built lexicon, searching
  for forms that would strike in ordinary prose; agent findings are proposals, and
  class decisions stay with the deterministic shape rules.
- `scripts/eval/entity_gold_benchmark.py` (M4): precision and recall against the
  reference TEIs, dev on the 18 previously indexed documents, one frozen-rules
  measurement on the 7 held-out ones, scope-restricted to shared text; per-mention
  error lists; evidence JSON versioned under `docs/data/`.
- `scripts/eval/entity_audit.py` (M6/M7): before-and-after measurement of the stock.
- `scripts/tei/tei_entity_marker.py` (M7): the operator-gated stock tool on
  `marker_common` (dry-run, backup, byte-splice inside `text`, idempotent,
  `revisionDesc` entry).

## Pilot

Panel of ten documents, gold half 1060, 100, 290, 1440, 890 (reference TEIs exist),
transfer half 1350, 1360, 2030, 1220, 3090 (Italian, English, interview, and the
documented ambiguity classes; type D and encyclopedia deliberately uncovered, 760 and
3040 as swap candidates). Result state and counts live in
`output/entity_preview/entity_pilot_report.json` and `.html`.

What the pilot established: the whole chain runs; every panel preview is schema-valid
and text-invariant; the anchor rule visibly reproduces the reference convention (one
full name, repeated bare surnames); the worklist collects exactly the predicted hard
cases (pre-anchor surnames before the rule was widened, short titles, mononyms, noun
homonyms). The pilot also surfaced the document-wide anchor question that the operator
then decided.

An independent evaluation wave (ten per-document evaluators, gold compared against
reference markup, transfer checked against text and facsimile; three adversarial
verifiers over all findings; one completeness critic) provides the semantic check the
unit tests cannot, since tests and code share their author's blind spots. The
reference-less transfer half stays in every evaluation round on purpose: the wave's
one systematic tier-1 finding (the initials variant, doc 1220) sat in an interview no
gold document resembles, and the gold half alone would have missed it.

## Verification

Four layers, ordered by what each proves:

1. Gold measurement (M4) delivers the trustable precision and recall numbers.
2. Judge calibration (M5) on ambiguities the references already resolve, including
   repeat-run stability.
3. Sampled verification beyond gold: seeded, stratified samples judged adversarially by
   independent agents with facsimile access; verdicts persisted, aggregated by script;
   the rule of three sets sample sizes; disagreement escalates to the operator.
4. Technical gates: byte-identical text extraction over the whole corpus before and
   after, deterministic CER reproduction, schema gate, conformity rules Z1 to Z4 and
   Z8, idempotence proof, full pytest suite. Gold tests self-skip where the local-only
   reference data is absent.

## Schema hardening (planned, before M4)

`persName@ref` and `orgName@ref` already enforce the `GND:` pattern. Two gaps: tighten
`bibl@ref` to the same pattern, and remove the unconstrained `@ref` from the unused
`rs`. `placeName` stays (Z3 forbids it; zero corpus usage). Gate: all delivered TEI and
the valid references stay schema-valid; own commit and register entry, since the schema
is the delivery's format authority (E102).

## Milestones

Each milestone ends with one coherent commit on main, pushed, plus a journal entry.
Nothing before M7 touches `tei_final`.

| Milestone | Content | Done when |
|---|---|---|
| M0 | Design plan recorded; entity list versioned under `data/entities/` | committed |
| M1 | GND cache and `entity_lint` | cache reproducible, lint pins the known defects, tests green |
| M2 | Matcher and preview runner | tier logic and hard-case fixtures green, no write path |
| M3 | Pilot on the ten-document panel plus independent evaluation wave | previews schema-valid and text-invariant, evaluation findings adjudicated, journal entry |
| M4 | Gold benchmark | frozen-rules measurement on the held-out references; evidence JSON under `docs/data/` |
| M5 | Judge calibration | accuracy and stability measured on gold-resolved ambiguities |
| M6 | Corpus dry-run | full change preview and distribution report reviewed by the operator |
| M7 | Stock run | operator-released marker run, gates green, mirror regenerated, register entry |

## Open operator decisions

1. Works in tier one, or worklist-only in the first stock wave (proposal: persons and
   organisations first; the pilot wraps multi-word titles, which informs the decision).
2. Curation channel for tiers two and three (viewer, teiCrafter, or verdict files).
3. Role of `editor_reviewed` (proposal: report field, no gate function).
