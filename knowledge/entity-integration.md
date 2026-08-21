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
updated: 2026-08-21
tags: [zbz-ocr-tei, entities, gnd, design-plan]
related: [specification, decisions, ground-truth-map, pipeline, entity-evaluation, journal]
authors: [Christopher Pollin]
---

# Entity Integration

How the curated GND entity list becomes inline entity markup in the delivered TEI
corpus. This document holds the whole workflow: data, rules, instruments, milestones,
verification. The sampling measurement of the built layer, its protocol and the record
of its executed run live in [entity-evaluation.md](entity-evaluation.md). Decisions
taken on the way receive E entries in
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
- The legacy mention index `data/entities/legacy_mentions.json` (pre-E71 remnant, moved
  under `data/entities/` with the fix package so a fresh clone builds the same lexicon)
  contributes surface forms attested in 18 reference TEIs. Its ids lack the GND check
  character and are normalized before joining. A form its bearer's own GND record does
  not corroborate reaches tier 2 only.

- The marking policy `data/entities/marking_policy.json` (git-tracked) holds the operator
  decisions about what may be marked, deliberately apart from the entity list, which is
  an external export and may be replaced wholesale. It is validated on load
  (`parse_marking_policy`), reaches the matcher as `lexicon["policy"]`, and a gid it names
  that the list does not carry is an error rather than a silent skip. Two decisions live
  there, both taken on the evidence tables of 2026-08-13 (E119). `anchor_free_surnames`
  releases a surname from the document-anchor requirement, for exactly the keys the entry
  names, so nothing derived from a released key inherits the release and every demotion
  suffix keeps its effect. `work_titles` takes a generic title out of the marking scope
  entirely (`drop_from_scope`, a lexicon matter, the forms never enter) or binds it to the
  typographic evidence of the one-word-title channel (`require_typographic_corroboration`,
  a matcher matter). `held_out_surnames` records what was considered and deliberately not
  released, so the reasoning survives.

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
  element. Title-only binds even where a reference wraps the wider citation span
  including imprint (operator decision 2026-08-12, prompted by reference 290); the
  gold benchmark scores such reference spans as neutral, and wider spans stay manual
  curation.
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
- All-caps mentions are in scope (operator direction 2026-08-12). A full name in
  capitals matches through its own rule. Mentions of the corpus author are marked
  like every other listed entity, in bylines and signatures as well (operator
  decision E108); the earlier byline exception is removed. The references leave the
  author byline mostly unmarked (reference 1060), which the gold benchmark counts
  apart as author deviations rather than plain false positives.
- Page apparatus follows the operator convention of 2026-08-12. Running heads stay
  outside the marking scope, because such a line repeats the document or section title
  as page furniture instead of naming an entity in the text. Title pages, organisation
  names in bylines and picture captions carry marks, because they state provenance with
  research value. The suppression is deterministic and active in the matcher (E108):
  the shared detection core `scripts/tei/running_heads.py` locates the recurring
  page-head zones, and every candidate inside one is demoted to the worklist with the
  `:running-head` suffix, so nothing in a head zone auto-marks while the mark stays
  visible for curation; a demoted full name keeps its document-wide anchor power. The
  convention reading of the measured precision is computed by the running-head audit
  ([entity-evaluation.md](entity-evaluation.md)).
- Library apparatus is out of scope. E-Periodica cover sheets and photo-credit lines
  are never matched (apparatus zone). Cover-sheet text leaves the delivered TEI
  altogether (operator decision 2026-08-12), through an operator-gated marker run in
  the E94 pattern that keeps the page break with a type marker, so pagination,
  facsimile links, completeness gate and Transkribus round trip survive; the corpus
  scan names the affected documents.
- The stock run documents itself in the header, one dated `<change>` entry per run in
  `revisionDesc` (E42 convention, idempotent, pattern of `tei_status_marker`). Preview
  files carry no `revisionDesc` entry; their header declares the responsibilities their
  own marks point to (section "Mark provenance and verification state"), and the
  run-level account of a preview pass stays in the pilot report.

Open modelling points, owned outside this plan:

- Image captions: the ZBZ guideline contradicts itself (O27). The operator convention
  of 2026-08-12 puts captions in scope; the matcher still skips figure contexts and
  reports caption candidates separately, so the figure zone is widened once ZBZ
  confirms the reading.
- Empty `speaker` elements stay curation slots (W17); the matcher never invents text.
- Adjective forms of names: the guideline excludes them, the references mark at least
  one. The automatic tiers exclude them; candidates go to the worklist; the
  contradiction goes to ZBZ.
- Hyphen compounds ("Karl-Jaspers-Symposium", "Hersch-Vortrag"): the references leave
  them unmarked, the tool currently decides them inconsistently. The suspicion signal
  parks them on the worklist until ZBZ decides.

## Mark provenance and verification state

Every mark the preview layer writes carries its own provenance and verification state, so
the annotation stays auditable outside this pipeline and a later pass can tell a settled
mark from an open one. Three things stay separate and are never merged into one value.

Provenance says who asserted the mark. It sits in `@resp` as a pointer to a `respStmt` of
the preview `teiHeader`. Two responsibilities exist today. `resp-entity-matcher` is the
deterministic closed-world matcher, named together with a short digest over the
rule-bearing modules, so the rule state behind a mark is identifiable rather than merely
dated. `resp-entity-adjudication` is the facsimile adjudication of the evaluation wave,
named with the wave's snapshot. A document declares only the responsibilities its own
marks point to. Nothing is declared for a model judge, because no producer writes such
marks, and a declaration without a producer would assert a provenance nothing carries.

Verification state says whether a human checked the mark and against what. It sits in
`@cert` and takes only the tokens the schema names, `high`, `medium`, `low`, `unknown`. A
mark whose adjudicated judgment reads correct is `high`, a mark the matcher asserted
without a human judgment is `medium`. A mark whose adjudicated judgment reads wrong is not
written at all, and the verdict guard reports such a mark as a violation
([entity-evaluation.md](entity-evaluation.md)). The tokens `low` and `unknown` stay
unassigned until a producer needs them.

Measured reliability is a property of the rule class. The individual mark never carries
it. Precision per category and per rule family comes from the adjudicated sample and is
reported there, next to its sample size. A model-produced confidence number never enters
the data at all. The schema would accept a numeric `@cert`, so the ban is a project rule
rather than a format constraint. A number invites reading a calibrated probability where
none was measured, and it blurs the one distinction the attribute exists for, whether a
human looked at this mention.

The rule that produced the mark travels with it in `@source`, so the reason for a mark is
readable in the file without the report beside it. Among the candidate attributes only
`@source` is legal on all three wrapped elements; `@evidence` validates on `persName` and
`orgName` and fails on `bibl`, and `@ana` is absent from `zbz_hersch.rng` altogether.

The verdict store `data/entities/mention_verdicts.json` remains the source of truth of the
judgments, and the attributes are a regenerable projection of it. The projection reuses
the classification of the verdict guard and inherits its honesty about drift. A judgment
binds the bytes it was made on, so a document whose sha256 fingerprint has moved since the
adjudication (guard class `text_changed`) falls back to `medium` throughout instead of
claiming a verification its current text no longer supports. The same fallback holds where
the adjudicated span or the adjudicated entity is no longer what the matcher would write.

The attributes exist in the preview layer only. Whether they belong in the delivered TEI
is part of the stock run (M7) and a decision for the library.

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
down one tier. Measuring in a deterministic system acts class-wise, which is what makes
the method economical. An adjudicated single case becomes a rule class, and the corpus
effect of that class is counted against the frozen scan snapshot before the rule is
adopted, so the operator decides on a change whose reach is already quantified.
A form class whose candidate set systematically misses the true bearer
never enters tier 2 either; a judge that only sees wrong candidates is invited to pick
one, so such mentions go straight to tier 3 (in the pilot's initials case, "J. H."
meant the interviewee, whose record carries no initials variant, while the one
presented candidate was the wrong person). Mentions of entities outside the list are out of
scope (closed world, E71 lesson); `entity_unlisted_scan` reports the name-shaped
surfaces outside the list as proposals for ZBZ, diagnosis only.

### Derived form channels

Tier two grows through derived spellings of forms the list and the cache already carry.
Five shape-driven channels register such spellings. An all-caps one-token organisation
also matches its capitalized spelling ("l'Unesco" beside "UNESCO"); a form with a
trailing parenthetical qualifier also matches its head ("Le populaire" out of "Le
populaire (Zeitung, Paris)"); a two-token organisation whose second token stands in a
static table of places also matches the inverted German adjective form ("Genfer
Universität" for the listed "Universität Genf"); a person headword also matches its
dotted initials, the form interview transcripts use in the speaker slot; a one-token
work title joins each of its own multi-word forms as "Title. Subtitle", so the full
printed title reaches the worklist as one span instead of a truncated auto-wrap of the
subtitle (the adjudicated wrong span of the Nietzsche monograph). Word
boundaries treat a superscript digit as a separator, so a name carrying a footnote
marker keeps the boundary it has on the page.

### Adjudicated precision guards (E109)

Every wrong_entity and wrong_span case the facsimile adjudication confirmed is answered
by a deterministic guard, each pinned as a regression fixture. A hyphen directly at the
span border demotes the hit as part of a compound ("UNESCO-Kommission"); the citation
title-slot frames demote a full name that follows an author-initial pattern ("Salamun
K., Karl Jaspers, Munich, 1985") or precedes an editor abbreviation ("Karl Jaspers, éd.
P.A. Schilpp"); an eponymous institution word in front of a full name demotes it
("Fondation Karl Jaspers"); an undated parenthetical behind a surname demotes it
("Augustin (de Malègue)", while "Jaspers (1883-1969)" keeps its tier); the lowercased
incipit of a case-tolerant work title demotes it ("die Mauer" against the listed "Die
Mauer"). Two repairs correct the span instead of the tier: the internal particle bridge
reads "Saint Ignace de Loyola" as one mention, and the subtitle-join channel covers the
full printed "Title. Subtitle". Demotion always means worklist, never a silent drop,
and every signal is grown from adjudicated cases only. Title-position names in citation
lines without a deterministic frame stay tier 1 and belong to the judge stage. One
recall exception is decided: the calendar formula "avant J.-C." never enters the
lexicon, because the abbreviation would fire on every date while naming no mention.

Every derived spelling enters as a tier-2 worklist candidate, so the channels raise
what an operator gets to see while the automatic marks stay as the base rules set them.
The channels read the forms that were actually registered, so every earlier gate binds
them too, and a cache form the variant review rejected has no derived form. The place
table is static and small, and no morphology is generated. The channels answer the rule
gaps that the recall reading of the executed evaluation named
([entity-evaluation.md](entity-evaluation.md)).

## Instruments

Built, each with its pytest suite:

- `scripts/tei/fetch_gnd_variants.py` builds the cache; parser pinned against lobid
  format drift; the committed cache carries a shape-contract test.
- `scripts/eval/entity_lint.py` audits the list offline (labels, id syntax, duplicates,
  DNB links, author resolution) and against the cache (404s, name and type
  consistency); the known real-stock defects are pinned as tests.
- `scripts/tei/entity_lexicon.py` builds the lexicon (headwords, inverted forms, cache
  variants, legacy surface forms, derived-form channels);
  `scripts/tei/entity_matcher.py` finds candidates with exact offsets and re-exports
  the lexicon API, so both read as one module from the outside. Exclusion
  zones: everything outside `text`, figures, bibliography divs, already marked
  elements. Running-head zones demote instead of excluding (`:running-head`, tier 2).
  Contract: candidates are offset-verified, non-overlapping, and may embed at
  most `lb` tags. Variant-derived surnames pass a distinctiveness filter, because raw
  lobid variants contribute noise tokens. Variants made only of dotted initials
  ("J. H." for Pestalozzi) never enter the full-name channel; the pilot evaluation
  showed such a variant claiming every "J. H." of an interview for the wrong person
  (doc 1220). More listed entities carry initials variants of this kind; the planned
  lexicon audit reports the current set.
- `data/entities/variant_review.json` is the operator-gated verdict file over every
  cache-derived name form (approve / suspect / reject, with reason). A model audit
  produced the first full pass; the operator worklist of all suspect and reject
  forms lands in `output/audits/variant_review_report.md`. `build_lexicon` consumes
  the file deterministically: reject never enters the lexicon (neither as full form
  nor via the surname index), suspect yields tier-2 candidates only, and a cache
  form the review does not know counts as suspect until the next review run.
  Headwords of the curated list and legacy forms stay outside the review's reach.
  Removing junk bearers also disambiguates real mentions, so a review pass can raise
  tier 1 while shrinking the total. Tests: `tests/test_variant_review.py` plus the
  review section of `tests/test_entity_matcher.py`.
- `scripts/tei/tei_entity_preview.py` wraps tier 1 into `output/entity_preview/` and
  proves per document: RelaxNG-valid against `zbz_hersch.rng`, text of the `text`
  subtree character-identical, byte-identical outside the insertions (bytes in, bytes
  out; stripping the wrappers and the header declarations restores the original). Every
  written mark carries `@resp`, `@cert` and `@source` under the vocabulary of the section
  "Mark provenance and verification state", and the verification state is read from the
  verdict store through the classification of `entity_verdict_guard`. It refuses to write
  into `output/tei_final` and reports JSON.
- `scripts/eval/entity_corpus_scan.py` dumps every candidate corpus-wide read-only,
  with rule, tier, page and context, plus distribution views (per document, per rule, per
  entity) and invariant checks (no tier-1 form on the function-word list, none adjacent
  to a hyphen). The snapshot is diffable, so a rule change shows its exact corpus effect
  before it binds; a frozen copy of the snapshot is what an adjudication wave draws from.
- `scripts/eval/entity_gold_benchmark.py` measures precision and recall against the ZBZ
  reference TEIs, scope-restricted to shared text, with per-mention error lists; the
  report lands in `output/audits/entity_gold_benchmark.json`. Facsimile classification
  of its deviations established that the references serve as a trend indicator, which
  is why the truth standard of the entity layer is the facsimile-adjudicated sample
  ([entity-evaluation.md](entity-evaluation.md)). Read per category, the trend orders the
  classes consistently, persons highest, organisations in the middle, works lowest by a
  wide margin, and the overall tier-1 figure stays well below the facsimile-adjudicated
  precision. About half of the counted deviations are convention differences rather than
  errors, above all the corpus author in bylines, which the references leave unmarked. The
  weak work class is the empirical backing for keeping works on the worklist in the first
  stock wave; the current figures live in `output/audits/entity_gold_benchmark.json`.
- `scripts/eval/build_mention_verdicts.py` builds `data/entities/mention_verdicts.json`,
  the persistence layer of the human and adjudicated judgments. A record is keyed by
  (doc, page, surface, gid, occurrence), where the occurrence index counts over the full
  tier-1 candidate population of the frozen scan snapshot the sample was drawn from
  (never the live scan, whose population moves with every rule change), and it
  carries the verdict, its reason, the offsets, the drawing wave and a sha256
  fingerprint of the delivered TEI it was judged on. A later text change (re-OCR,
  correction run, stock correction) moves the fingerprint and marks the affected records
  stale for re-adjudication, so a verified mention stays verified exactly as long as its
  text holds. The build reads its inputs read-only, produces byte-identical output on a
  rerun, and reports a deviation from the adjudicated distribution instead of adjusting
  it.
- `scripts/tei/running_heads.py` is the shared running-head detection core (the
  recurring normalized page-head line, verso/recto companions, merged one-off
  variants). The matcher consumes its zones for the `:running-head` demotion;
  `scripts/eval/running_head_audit.py` validates the detection against the
  adjudicated ground truth, counts the corpus suppression scope on the scan snapshot
  and computes the convention reading of the adjudicated precision
  (`convention_precision`, seeded percentile bootstrap).
- `scripts/eval/entity_risk_ranking.py` is the instrument of the false-positive hunt. It
  scores every tier-1 mark of the scan snapshot with additive deterministic features
  (form from a variant channel, case-tolerant rule, single-token surface, short surface,
  work category, surname shared with another listed person, plus a state the tier rules
  exclude) and sorts the corpus into three strata under
  `output/audits/fp_hunt/risk_ranking.json`, so a wave buys its checked cases where a
  false positive is most likely. The binding wave protocol sits beside the ranking as
  `PROTOCOL.md`, versioned as `reports/2026-08-12_fp-hunt-protokoll.md`. Score and
  features order the queue; the facsimile decides the verdict, and a confirmed false
  positive is fixed at the variant review or as a matcher rule guard.
- `tests/test_entity_ref_invariant.py` proves the closed world on the shipped artifacts.
  Every GND id that reaches the viewer through the generated mirror, the `ref="GND:..."`
  values of the preview pages together with `gid` and the ambiguity set `alternatives`
  of the worklists, is compared as a raw string against the curated list. The comparison
  is exact, so a formatting drift fails as loudly as an unknown id, and the gate has
  teeth on a fresh clone because the mirror is git-tracked.
- `scripts/tei/tei_cover_strip.py` (operator-gated, E94 pattern) removes E-Periodica
  cover-sheet text from the delivered TEI and keeps the page break with a type marker;
  the corpus-wide run is executed, report in `output/audits/cover_strip_report.json`.
- The viewer entity stream: `scripts/edition/generate_entity_preview_data.py` splits the
  previews per page into the generated mirror, and the viewer shows them read-only under
  `viewer.html?doc={DOC_ID}&entities=1` as a markup layer with category colors, a
  popover per mention and a per-page worklist panel, so wrappings are verified next to
  the facsimile.

Planned:

- `scripts/eval/entity_lexicon_audit.py` (before M4): groups every form the built
  lexicon would match by shape class (dotted initials, single tokens at the length
  floor, all-caps forms, forms with digits, non-Latin scripts) with counts and
  examples, so the operator approves or bans whole classes instead of chasing single
  forms; rerun after every cache refresh. A second, independent layer before the
  corpus dry-run (M6) is an adversarial agent review of the built lexicon, searching
  for forms that would strike in ordinary prose; agent findings are proposals, and
  class decisions stay with the deterministic shape rules.
- The frozen-rules gold measurement (M4): one run of `entity_gold_benchmark` on the
  held-out references with the rules frozen, evidence JSON versioned under `docs/data/`.
  The held-out set is drawn along the distribution of gold mentions rather than by
  document count; the densest reference (1520) is measured separately, it carries a
  large share of the gold, a known file defect, and the anchor-collision case the panel
  never saw.
- `scripts/eval/entity_audit.py` (M6/M7): before-and-after measurement of the stock.
- `scripts/tei/tei_entity_marker.py` (M7): the operator-gated stock tool on
  `marker_common` (dry-run, backup, byte-splice inside `text`, idempotent,
  `revisionDesc` entry). One design condition binds the milestone, that the marker reuses
  the wrapping and checking logic of the preview instead of growing a second copy of it.
  `apply_candidates`, `mark_attributes`,
  `hi_envelope`, the text-invariance check and the schema check move out of
  `tei_entity_preview.py` into a shared module both consume, so preview and stock run
  provably produce the same wrapping. A second implementation of this logic would be the
  first real occasion for a refactor of the layer.

## Pilot

Panel of ten documents, gold half 1060, 100, 290, 1440, 890 (reference TEIs exist),
transfer half 1350, 1360, 2030, 1220, 3090 (Italian, English, interview, and the
documented ambiguity classes; type D and encyclopedia deliberately uncovered, 760 and
3040 as swap candidates). Result state and counts live in
`output/entity_preview/entity_pilot_report.json`; the reading surface is the entity
overview page `docs/entities.html`.

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

The completed wave (2026-08-12) confirmed the precision of person full names and
surfaced a second systematic defect class, work-title spans that include imprint or
trailing punctuation or wrap inside an existing `hi`. The critic ran the matcher
read-only over the whole corpus and found what ten per-document evaluators could
not: homograph surnames in German prose (the conjunction "Weil", forename collisions
such as "Thomas Höpker"), a poisoned legacy pairing ("Jérémie" filed as a Jaspers
form while the reference marks the prophet), the anchor collision in the densest
gold document (both Jaspers spouses anchored, every bare surname undecided), and the
volume concentration of the future stock run on the author and her main subject.
Method lessons from the wave: evaluation panels are drawn by impact and class
coverage (top-wrap documents, excluded-zone classes, German prose), never by
document count alone; every wave starts by checking that the artifacts under review
match the code state; evaluator schemas separate genuinely lost mentions from
mentions sitting on the worklist; and every agent claim is verified against the
material before it is acted on.

## Fix package (pilot outcome, build order)

Each step test-first, the real corpus findings frozen as regression fixtures; after
the package, the preview rerun and the corpus scan diff close M3.

1. Legacy demotion: legacy forms feed tier 2 only, and `entity_lint` gains a pairing
   check that every variant is corroborated by its bearer's GND record (the Jérémie
   pairing is the pinned must-find case). The legacy index moves under
   `data/entities/` so a fresh clone builds the same lexicon.
2. Work spans: candidate surfaces never end in punctuation; a `bibl` around the full
   content of an existing `hi` wraps the `hi` from outside.
3. Homograph suspicion: a bare or anchored surname drops to the worklist on any
   deterministic signal (lowercase twin in the same document, function-word list,
   adjacent hyphen, adjacent unknown capitalized word).
4. Caps rule: all-caps full names match; mentions of the document's own author in
   bylines and running headers were skipped via the Masterfile author (this byline
   exception was removed again with E108; the zone suppression covers running heads).
5. Apparatus zone: cover sheets and photo-credit lines are never matched; the
   operator-gated cover strip run removes cover text from the delivered TEI.
6. Adjective forms become worklist candidates; a single-word work title that shadows
   a listed surname ("Nietzsche") presents both candidates.

The package is built; the corpus scan snapshot and the regenerated previews carry it.
The derived form channels stand on top of it as the growth path of tier two.

## Verification

Four layers, ordered by what each proves:

1. Gold measurement (M4) delivers the trustable precision and recall numbers.
2. Judge calibration (M5) on ambiguities the references already resolve, including
   repeat-run stability.
3. Sampled verification beyond gold: seeded, stratified samples judged adversarially by
   independent agents with facsimile access; verdicts persisted, aggregated by script;
   disagreement escalates to the operator. The method, the binding adjudication protocol
   and the record of the executed run live in
   [entity-evaluation.md](entity-evaluation.md); the judgments themselves land in the
   mention verdict store, and the risk ranking supplies the second, risk-ordered draw
   over the same mark population.
4. Technical gates: byte-identical text extraction over the whole corpus before and
   after, deterministic CER reproduction, schema gate, conformity rules Z1 to Z4 and
   Z8, idempotence proof, the closed-world invariant over every id in the shipped
   mirror, full pytest suite. Gold tests self-skip where the local-only reference data
   is absent.

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
| M7 | Stock run | operator-released marker run, gates green, mirror regenerated, register entry, `docs/methode.html` extended by an entity-quality paragraph pointing to [entity-evaluation.md](entity-evaluation.md) |

State on 2026-08-13: M0 to M3 are reached, the pilot and the independent evaluation wave
included. The preview has since left the ten-document panel: it runs over every delivered
document, each one schema-valid and text-invariant, and every wrapped mark carries its
provenance and verification state (E118). The marking policy of E119 is in force, so the
auto-marked layer now covers the released canonical surnames and the worklist no longer
carries the generic titles taken out of scope. That growth of the auto-marked layer is
also a measurement obligation, because the released marks appear in no earlier draw
([entity-evaluation.md](entity-evaluation.md), population validity). Beyond the pilot the sampling measurement of
[entity-evaluation.md](entity-evaluation.md) has run once over the whole delivered
corpus, its judgments are persisted in the verdict store, and the consequences that need
no convention decision are implemented, the derived channels, the invariant gate and the
risk ranking. The running-head suppression is active in the matcher and the author
convention is decided (E108); scan, previews, mirror and audits carry that state. M4 has
its instrument and a report; the milestone closes with the frozen-rules run on the
held-out references and its evidence under `docs/data/`. M5 to M7 stand open, and
`tei_final` carries no entity markup.

## Open operator decisions

1. Works in tier one, or worklist-only in the first stock wave (proposal: persons and
   organisations first; every confirmed span error of the pilot evaluation sits in
   the work class, which strengthens the proposal).
2. Curation channel for tiers two and three (proposal: the viewer entity stream,
   read-only first, confirm/reject actions writing verdict files later).
3. Role of `editor_reviewed` (proposal: report field, no gate function).
4. Hyphen compounds (see the open modelling points; ZBZ feedback is not available in
   this phase, so the operator decides when the worklist evidence suffices).

Decided 2026-08-12 (operator): title-only for works binds even against wider
reference spans; all-caps mentions are in scope; cover sheets leave the delivered
TEI; apparatus zones are out of matching scope; running heads stay outside the
marking scope, while title pages, organisation names in bylines and picture captions
are marked.

Decided 2026-08-13 (operator, E108): mentions of the corpus author are marked like
every other listed entity, in bylines and signatures as well; the byline exception is
removed. ZBZ feedback is not available in this project phase, so open convention
questions of the entity layer fall to the operator.

Decided 2026-08-13 (operator, E119): canonical surnames are released from the document
anchor, generic work titles are dropped from scope or bound to typographic corroboration,
both through the marking policy. One surname stayed held out, because person and work
reading are not locally separable there.

Decided 2026-08-13 (operator): entities the corpus names frequently while the curated
list omits them are admitted by the project itself, annotated, and marked in the data as
an addition from outside that list. The provenance vocabulary carries the distinction, a
third responsibility declaration for the proposal channel with `cert="low"`, and a
reference only once an identification is confirmed; the admission dossier with textual
evidence and deterministic lobid lookups is the open work item.

Settled by the reference corpus 2026-08-13: a person-name span coextensive with the
title of a cited work denotes the work, not the person. In 190 citations of the 25
reference TEIs not one carries a marked person name, which closes one of the two open
adjudication disputes without a convention decision.
