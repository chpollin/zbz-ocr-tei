---
title: TEI Mapping
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
created: 2026-08-21
updated: 2026-08-26
authors: [Christopher Pollin]
related: [specification, pipeline, project, verification, decisions]
---

# TEI Mapping

The markup rulebook of the project. It states how a source text becomes TEI-XML, which
phenomena the transcription encodes and how, which elements and attributes the delivered
corpus uses, what the header and the schema declare, and which conventions hold across
every document. The pipeline stages and the instruments that apply these rules are in
[pipeline.md](pipeline.md), the consolidated requirement view is in
[specification.md](specification.md), and the dated rationale of each rule is in
[decisions.md](decisions.md).

## Rationale

Two authorities govern the markup. The binding ZBZ editorial guidelines
(`data/source/guidelines/Editionsrichtlinien_ZBZ.md`) say what an edition of this corpus
encodes, and the project schema `data/schema/zbz_hersch.rng` (TEI P5 v4.10.2 subset) is
the single format authority every delivered file must satisfy. Both have been binding
since E48/E49. An earlier DTA-Basisformat conformity claim was tested against the official
DTA schema and dropped (E102); the guidelines keep their own DTA reference, documented in
[data/source/guidelines/README.md](../data/source/guidelines/README.md).

Four principles carry the whole mapping.

1. The delivered text is a reading text that follows the printed original.
2. Persons, organisations and works are annotated so the indexes can be built from the
   text.
3. Normalization stays inside the defined character rules; every other feature of the
   source keeps its shape.
4. The project schema is the single format authority.

The binding entity convention is the inline GND model (E88), as the reference TEIs show
it. A reference sits directly at the mention and is repeated at every repetition, with no
register, no places, no foreign identifiers and no `@key`. The surface form in the text
stays untouched, so a marking tool only wraps characters that already exist.

Curation replaces automation wherever a structure spans more than the page the generator
sees. Step 2 of the pipeline produces one `<div>` body fragment per page, so
document-level and cross-page structures do not emerge on their own and are set during
curation in the viewer (rule of 2026-06-08). The scope statement belongs to
[specification.md](specification.md); the reasons per case are the following.

- `<front>` and `<back>` are document level. The end-matter source in the Masterfile
  column "Anmerkungen" is free text and partly internal reference, so it is not a
  reliable citation and an automatic build would produce wrong TEI. End-matter citation
  per MLA 9 plus the Swisscovery link stays with curation.
- A cross-page `<anchor>` for a double-page figure needs both pages and is too rare and
  too error-prone to automate.
- `<unclear>` is a per-character judgment against the scan image and belongs to curation
  alone.
- `<epigraph>` is adopted where the model places it at the start of a `<div>`; a
  misplaced motto is unpacked by `tei_step2._fix_structural_issues`.

How often each phenomenon is attested in the reference corpus is recorded in
[project.md](project.md), data section, phenomenon map.

## Phenomena and their treatment

### Document structure

```xml
<?xml version="1.0" encoding="UTF-8"?>
<TEI xmlns="http://www.tei-c.org/ns/1.0" type="naegeli">
  <teiHeader><!-- from doc_metadata.json via build_tei_header; Alma metadata (MMSID) = ZBZ domain, O8 --></teiHeader>
  <text>
    <front><!-- optional: prefaces, dedications --></front>
    <body>
      <div n="1">
        <pb facs="#facs_1" n="1"/>  <!-- first pb is the first child of div n="1" -->
        <!-- main structure -->
      </div>
    </body>
    <back><!-- optional: translations, reprints --></back>
  </text>
</TEI>
```

| Level | Element | Use |
|---|---|---|
| 1 | `<div n="1">` | main chapter |
| 2 | `<div n="2">` | subchapter |
| 3 | `<div n="3">` | section |

`<pb>` sits inside `<div>`.

### Page structure and page breaks

```xml
<pb facs="#facs_1" n="1"/>
<pb facs="#facs_2" n="2"/>
<pb facs="#facs_3" n="[3]"/>  <!-- page number not printed -->
```

`@facs` references the digitized image, `@n` carries the page number. A page break stands
at the start of its page, so the first page break of a document is the first child of
`<div n="1">`. Square brackets mark a number the page itself does not show, so the edition
supplies it. The delivered stock is lifted to that form by the operator-gated correction
`tei_pb_folio`, which brackets a derived printed folio and leaves the running scan number
unbracketed where no folio can be derived safely.

Line breaks are preserved at the data level and hidden in the frontend. A paragraph that
reaches document assembly without a single `<lb>` and whose text runs past one and a half
column widths receives line breaks at word boundaries, computed against a fixed column
width of sixty characters; a paragraph that already carries line information keeps it
unchanged.

### Character normalization

These rules shape the delivered text at production time. The separate N-rules that make
two texts comparable at measurement time live in
[methodology.md](methodology.md), CER measurement section and never touch the data.

| Source characters | Target character | Unicode | Rule |
|---|---|---|---|
| dashes and list dashes, ranges | en dash `–` | U+2013 | all horizontal strokes except hyphenation and compound hyphens |
| hyphenation and compound hyphens | hyphen `‐` | U+2010 | word breaks, compounds |
| double quotation marks, guillemets included | `"` | U+0022 | straight quote |
| single quotation marks | `'` | U+0027 | straight quote |
| apostrophe between letters | `’` | U+2019 | `l’homme` |
| non-representable characters | `~` | U+007E | placeholder |

Spaces before `:`, `;`, `?`, `!` and quotation marks are deleted. In a French-language
document the typographic convention keeps a narrow no-break space (U+202F) in those
positions and before the closing guillemet, which `char_lint_audit` measures as a
space-type finding instead of an extra character. Enumerations written with dashes are
normalized to `/` (Zürich/Bern/Basel). Retained are `ß` (U+00DF), brackets as in the
original, accents and ligatures. In the delivered stock the safe apostrophe class is
corrected by `tei_char_normalize`, which reuses the regex of `char_lint_audit` so that
measurement and correction cover exactly the same class; the guillemet class is measured
and left in place, because only the apostrophe class was released for a stock run.

### Highlighting

| Rendering | TEI | Example |
|---|---|---|
| Bold | `<hi rendition="#b">` | `<hi rendition="#b">wichtig</hi>` |
| Italic | `<hi rendition="#i">` | `<hi rendition="#i">Philosophie</hi>` |
| Underline | `<hi rendition="#u">` | |
| Spaced | `<hi rendition="#g">` | |
| Small caps | `<hi rendition="#k">` | |
| Superscript | `<hi rendition="#sup">` | |
| Subscript | `<hi rendition="#sub">` | |

Only semantically relevant highlighting is encoded.

### Special structures

- Language switch, `<foreign xml:lang="deu">...</foreign>` with ISO 639-3 codes (`fra`,
  `deu`, `eng`, `ita`, `lat`).
- Footnotes, `<note place="foot" n="1" xml:id="fn{page}-{no}">...</note>`, with `@next`
  and `@prev` where a note spans pages.
- Printing errors, `<choice><sic>...</sic><corr>...</corr></choice>`.
- Illegible passages, `<unclear cert="high|low">...</unclear>`.
- Marginal notes, `<note place="left|right">...</note>`.
- Blank pages, a page break followed by `<p>[Leer]</p>`.

### Figures

```xml
<figure xml:id="fig1">
  <graphic url="..\..\images\fig1.tif"/>
  <head>[optional]</head>
  <p>[optional explanation]</p>
</figure>
```

The `xml:id` sits on `<figure>` and is numbered sequentially; `<graphic>` carries none.
A `<figure>` is always a standalone block and never appears inside `<p>`. A double-page
figure marks its span with `<anchor xml:id="figN-start"/>` and `<anchor xml:id="figN-end"/>`.

### Special document types

- `<div type="review">` with `<bibl>` in the `<head>`
- `<div type="interview">` with `<sp>` and `<speaker>`
- `<div type="conversation">` for panel discussions
- `<div type="entry">` for encyclopedia entries, with `<head type="lemma">`, a
  `<div type="bibliography">` and `<listBibl>`
- `<ab type="redactional" hand="xy">` for redactional texts that the corpus author did not write

A text belonging to none of these genres carries the generic `<div type="text">`, the
value E47 put in place of the earlier `essay`. The complete set of admitted values lives
in `VALID_DIV_TYPES` ([scripts/config.py](../scripts/config.py)), which the validator
rule R5 enforces.

Paratexts use `<front>` with `editorial` and `dedication`, and `<back>` with
`translation`, `reprint` and `otherEdition`. Citations in `<back>` follow MLA 9 and carry
the Swisscovery permalink as `<ref target="...">`.

### Omissions

The reading text leaves the following out of the transcription.

| Omission | Note |
|---|---|
| Title pages | except for monographs |
| Curriculum vitae | even when placed in front |
| Running heads | |
| Blurbs | |
| Author attribution | the author line appears only in the header |
| Initials | left unannotated in the text |
| Multi-column layout | the text runs on across a column break, and the `<p>` the zoning generates there is dropped |

Library apparatus is left out on the same ground. E-Periodica cover sheets leave the
delivered TEI altogether (operator decision 2026-08-12), through the operator-gated marker run
`tei_cover_strip`. It removes the page content and keeps the page break with
`type="cover"`, so pagination, facsimile links, the completeness gate and the Transkribus
round trip survive. Detection is deterministic and demands at least three of the four
E-Periodica field lines between the first and the second page break; a partial hit is
reported and never changed, because genuine title pages and foreign delivery sheets sit
in that class.

### Entities

The delivered corpus under `output/tei_final/` carries no entity markup today. The
controlled entity layer writes read-only previews, and the stock run into the delivery is
operator-gated (see [decisions.md](decisions.md), plan section). The rules below are the
target model, which the previews realize for every rule that has a producer today.

Detail rules of the inline model, settled against the reference corpus and by operator
decision, hold as follows.

- `bibl` wraps an existing `<hi>` element whose whole content is the title, so the
  emphasis stays inside the reference.
- For works only the title is marked, in footnotes as well; the imprint stays outside the
  element. Title-only binding holds even where a reference wraps the wider citation span
  including imprint, and wider spans stay manual curation.
- Footnote citations receive references. Only `bibl` inside `div type="bibliography"`
  stays without one, which the ZBZ guidelines set in their encyclopedia-entry section and
  the matcher realizes by excluding that zone from the scan.
- Nesting is permitted, so a `persName` with its own reference may stand inside a `bibl`;
  this validates against `zbz_hersch.rng`.
- Existing entity elements without `@ref` are enriched with the attribute in place, only
  where the tier rules verify the assignment. This rule waits for its producer, since the
  matcher treats an existing `persName` or `orgName` as an excluded zone.
- Particles stay outside the element and the whole inflected word goes inside; an element
  boundary never splits a word. Genitive endings belong to the surface, a trailing
  apostrophe does not.
- Names run across line breaks, including mid-word breaks with `break="no"`, so matching
  runs on line-break-normalized text.
- Interview speakers follow the reference pattern `speaker > persName@ref`, with the
  colon outside the element.
- All-caps mentions are in scope, and a full name in capitals matches through its own
  rule. Mentions of the corpus author are marked like every other listed entity, in
  bylines and signatures as well (E108).
- A stock run documents itself in the header with one dated `<change>` per run in
  `revisionDesc`, idempotent, in the E42 convention. Preview files carry no `revisionDesc`
  entry; their header declares the responsibilities their own marks point to.

Every mark carries activity provenance in `@resp` and no entity mark carries `@cert`
(E131, which corrects E118). Certainty tokens collapse unlike evidence paths into an
ordinal scale whose values do not say what happened. Responsibility pointers retain that
distinction. The preview declares only the roles its own marks use in `respStmt` elements
inside `titleStmt`:

- `resp-entity-matcher` records deterministic closed-world matching and names
  `scripts/entity/entity_matcher.py` together with a digest over the rule-bearing modules.
- `resp-entity-agent-review` records the existing facsimile-based evaluation judgment as
  machine review. It never asserts editorial verification.
- `resp-entity-agent-annotation` records a context-aware selection or promotion made by an
  AI agent through a bound context packet.
- `resp-entity-llm-judge` records an independent LLM review whose run differs from the
  producing agent run.
- `resp-entity-editor-verification` records a person-bound editorial verification.

The detailed run record stays in `output/entity_agent_review/{run_id}.json`, where context
hashes, harness, model, prompt digest, tool calls, evidence references and an optional judge
record remain machine-readable. The current schema offers `respStmt` but no `appInfo` or
`application`, so the TEI carries compact role pointers and readable declarations. Measured
reliability remains a property of the evaluated rule class and is reported with its sample
size in [verification.md](verification.md).

The producing matcher rule travels in `@source`; image, transcription and guideline
evidence stay in the bound context packet rather than overloading the rule attribute. Among
the candidate attributes only `@source` is legal on all three wrapped elements, since
`@evidence` validates on `persName` and `orgName` and fails on `bibl`, and `@ana` is absent
from the schema altogether.

The verdict store `data/entities/mention_verdicts.json` stays the source of truth of the
evaluation judgments, and the `resp-entity-agent-review` pointer is a regenerable
projection. A judgment binds the bytes it was made on. If the document digest, span or
entity has changed, that review role disappears from the mark; the matcher provenance
remains. A wrong-entity or not-in-source judgment still has to leave tier one, and the
verdict guard fails while it stands there.

Finding mentions runs in three tiers, and one principle binds every tier, that a language
model never assigns identifiers. Candidates and their GND identifiers come from the
curated list, and a model may only pick among presented candidates and must be able to
answer that none of them fits (E62).

1. Tier one, automatic. Full names including inverted and line-break-crossing forms,
   full-name variants from the GND cache, initial plus unambiguous surname, distinctive
   organisation names, multi-word work titles, speaker slots, speaker initials at the
   label position resolved by a document anchor or by list-unique initials of at least
   three letters (E128), and bare surnames with a document anchor.
2. Tier two, contextual decision. Ambiguous hits such as bare surnames without anchor or
   colliding with common words, single-word titles, candidates inside plain `bibl`, and markup-crossing
   hits. `entity_agent_context.py` binds the facsimile, transcription, TEI page, schema,
   guidelines and candidate identities into one packet. `entity_agent_review.py` accepts
   structured decisions, permits only supplied identifiers, writes a separate preview and
   validates schema and text invariance. A calibrated independent judge may contribute its
   own role, while M5 still carries no calibration run ([decisions.md](decisions.md), plan
   section).
3. Tier three, worklist. What no rule can find, such as allusions and badly recognized
   names, goes to human curation.

The anchor rule counts document-wide. A full-name tier-1 mention of an entity anywhere in
the document anchors every bare occurrence of that surname, also before the full name,
provided exactly one anchored entity carries the surname there. A form class whose
candidate set systematically misses the true bearer never enters tier 2, because a judge
that only sees wrong candidates is invited to pick one; such mentions go straight to tier
three. Mentions of entities outside the list are out of scope by the closed-world rule;
`entity_unlisted_scan` reports name-shaped surfaces outside the list as proposals, as
diagnosis only.

Shape-driven channels let tier two grow through derived spellings of forms the list and
the cache already carry. An all-caps one-token organisation also matches its
capitalized spelling; a form with a trailing parenthetical qualifier also matches its head;
a two-token organisation whose second token stands in a static table of places also matches
the inverted German adjective form; a person headword also matches its dotted initials, the
form interview transcripts use in the speaker slot, with a hyphenated surname abbreviated
part by part; and a one-token work title joins each of its own multi-word forms as "Title.
Subtitle", so a full printed title reaches the worklist as one span. Word boundaries treat
a superscript digit as a separator, so a name carrying a footnote marker keeps the boundary
it has on the page. Every derived spelling enters as a tier-2 worklist candidate, so the
channels raise what an operator gets to see while the automatic marks stay as the base
rules set them. The one lift out of a derived channel is the speaker-initials rule (E128):
an initials form in a `speaker` slot or as the first word of a paragraph followed by a dash
or colon becomes tier 1 when exactly one bearer is anchored in the document, or when the
initials carry at least three letters and one bearer on the list; the same initials in
running prose keep the worklist reading. The channels read the forms that were
actually registered, so every earlier gate binds them too, and a cache form the variant
review rejected has no derived form.

Adjudicated precision guards (E109) answer every confirmed wrong-entity and wrong-span case
with a deterministic rule, each pinned as a regression fixture. A hyphen directly at the
span border demotes the hit as part of a compound. The citation title-slot frames demote a
full name that follows an author-initial pattern or precedes an editor abbreviation. An
eponymous institution word in front of a full name demotes it. An undated parenthetical
behind a surname demotes it, while a life-dates parenthetical keeps its tier. The
lowercased incipit of a case-tolerant work title demotes it. Two repairs correct the span
instead of the tier, the internal particle bridge that reads a multi-part name as one
mention, and the subtitle-join channel. Demotion always means worklist and never a silent
drop, and every signal is grown from adjudicated cases only. Title-position names in
citation lines without a deterministic frame stay tier one and belong to the judge stage.
One recall exception is decided, the calendar abbreviation for dates before the common era,
which never enters the lexicon because it would fire on every date while naming no mention.

Which surnames and generic titles the matcher may mark at all is an operator decision in
`data/entities/marking_policy.json` (E119), kept apart from the curated list because that
list is an external export and may be replaced wholesale. Named surnames are released from
the anchor requirement for exactly the keys their entry names, under the rule id
`anchor-free-surname`; a released hit anchors nothing itself and every demotion suffix
keeps its effect. Generic titles either leave the marking scope or are bound to
typographic corroboration. A surname the operator weighed and did not release stays in
`held_out_surnames`, which records the decision without changing what the matcher does.
The policy is a trust boundary, validated on load, and a key absent from the entity list
is an error rather than a silent skip.

Page apparatus follows the operator convention of 2026-08-12. Running heads stay outside
the marking scope, because such a line repeats the document or section title as page
furniture instead of naming an entity in the text. Title pages and organisation names in
bylines carry marks, because they state provenance with research value; picture captions
are in scope by the same convention, and their candidates reach the worklist while O27 is
open. The suppression is deterministic and active in the matcher (E108). The shared
detection core `scripts/entity/running_heads.py` locates the recurring page-head zones, and
every candidate inside one is demoted to the worklist with the `:running-head` suffix, so
nothing in a head zone auto-marks while the mark stays visible for curation. A demoted full
name keeps its document-wide anchor power, because the head still names the document's
subject. Library apparatus is out of scope entirely, and E-Periodica cover sheets and
photo-credit lines are never matched.

Whether the provenance attributes belong in the delivered TEI is part of the stock run and
a decision for the library ([decisions.md](decisions.md), plan section).

### Facsimile binding

The generator produces the facsimile block itself (E89). Every page receives a `<surface>`
with pixel coordinates in `@ulx @uly @lrx @lry`, a `<graphic url>` as its first child (the
schema requires `graphic` before `zone`), and one `<zone>` per layout region with its own
pixel box. The page break carries `<pb facs="#facs_N" n="..."/>` following the ZBZ
editorial guidelines, corpus-wide. The address scheme uses the relative filename
`{doc_id}_p{NNN}.png`, physically under `docs/images/{doc_id}/` and sequential to `facs_N`,
which makes the reference resolve in a self-contained way. Production sits in
`build_facsimile` ([tei_step3.py](../scripts/tei/tei_step3.py)); the already delivered
stock is brought to the same state without an OCR re-run by the post step
[tei_surface_graphic.py](../scripts/tei/tei_surface_graphic.py). This resolves
[decisions.md](decisions.md) O25 and replaces a blank-page placeholder that pointed to a
non-existent file. ZBZ prescribes the `<pb facs>` form for page images and does not demand
a surface `<graphic>`; the `<graphic>` makes the reference resolvable and supersedes a
hard-coded demo path in a downstream editor.

### Revision description

Every final TEI carries `<revisionDesc>` directly before `</teiHeader>`. The first
`<change>` records the pipeline generation. After it, `tei_status_marker.py` projects the
per-object manifest into the header (E66), writing one `<change n="{stream}">` per history
entry and then one summary `<change n="{stream}-summary">` per stream with the current
status. Projected are the three pipeline streams `ocr`, `layout` and `tei`; the `entities`
stream stays out, because it describes the preview layer rather than the delivered TEI.

```xml
<revisionDesc>
  <change when="2026-03-15" who="pipeline">TEI generated (Unified Pipeline v1, Gemini + RelaxNG)</change>
  <change status="unverifiziert" n="ocr-summary">OCR-Strom (Stand): unverifiziert</change>
  <change status="unverifiziert" n="layout-summary">LAYOUT-Strom (Stand): unverifiziert</change>
  <change status="unverifiziert" n="tei-summary">TEI-Strom (Stand): unverifiziert</change>
</revisionDesc>
```

The `@status` attribute carries the manifest value verbatim, and the same run removes the
`<change>` entries of the abolished agent screening. What the three status values mean, how
the viewer displays them and where the history comes from is in
[workflow.md](workflow.md), workflow status section.

## Mapping tables

Element inventory of the delivered TEI.

| Element | Attributes | Use |
|---|---|---|
| `<TEI>` | `xmlns`, `type="naegeli"` | root |
| `<teiHeader>` | | metadata |
| `<text>`, `<front>`, `<body>`, `<back>` | | containers |
| `<div>` | `n`, `type` | structural |
| `<pb>` | `facs`, `n`, `type` | page break, with `type` for blank and cover pages |
| `<lb>` | `facs`, `n`, `break` | line break |
| `<head>` | `type` | heading |
| `<title>` | `type` (main/sub) | title |
| `<p>` | `facs` | paragraph |
| `<hi>` | `rendition` | highlighting |
| `<bibl>` | `corresp` | bibliographic entries in `<listBibl>` and in a review `<head>` |
| `<note>` | `place`, `n`, `xml:id`, `next`, `prev` | footnote and marginal note |
| `<foreign>` | `xml:lang` | language switch |
| `<space>` | `dim` | spacing |
| `<list>`, `<item>`, `<table>`, `<row>`, `<cell>` | | lists and tables |
| `<figure>` | `xml:id` | figure |
| `<graphic>` | `url`, `facs` | image reference |
| `<choice>`, `<sic>`, `<corr>` | | printing errors |
| `<sp>`, `<speaker>` | `type` | speech act |
| `<listBibl>` | | bibliography |
| `<ab>` | `type`, `hand` | redactional block |
| `<unclear>` | `cert` | illegible passage |
| `<anchor>` | `xml:id` | double-page images |
| `<ref>` | `target` | external reference |
| `<facsimile>`, `<surface>`, `<zone>` | `xml:id`, `ulx`, `uly`, `lrx`, `lry` | page image binding |
| `<revisionDesc>`, `<change>` | `who`, `when`, `status`, `n` | revision status |

Entity elements of the preview layer, which the delivered corpus does not yet carry.

| Element | Attributes | Use |
|---|---|---|
| `<persName>` | `ref`, `resp`, `source` | person mention with GND reference |
| `<orgName>` | `ref`, `resp`, `source` | organisation mention with GND reference |
| `<bibl>` | `ref`, `resp`, `source` | work mention with GND reference, title span only |
| `<respStmt>` | `xml:id` | responsibility declaration in the preview header |

## Header and schema declarations

The delivered header follows the delivery contract that E68 and E69 fixed, and
`build_tei_header` ([tei_step3.py](../scripts/tei/tei_step3.py)) produces it congruently,
so a regeneration cannot regress an already delivered header. The contract demands
`<idno type="docID">` in the `publicationStmt`, a `<biblStruct type="{pub_form}">` in the
`sourceDesc` carrying `<analytic>` with title and author plus `<monogr>` with an
`<imprint>` that holds the `<date>` where the metadata knows one, and a
`<profileDesc>/<langUsage>` with one `<language ident="...">` per language code. The
requirement itself is owned by [specification.md](specification.md) (R-SCHEMA, R-TEI); the
test gates that hold it are described in [verification.md](verification.md), quality
assurance section. `build_tei_header` never emits `<revisionDesc>`; the status marker
projects it afterwards.

Catalogue metadata from Alma, in particular the MMSID, stays outside the pipeline header
and remains ZBZ domain (O8 in [decisions.md](decisions.md), plan section).

The RelaxNG declarations that govern the entity attributes were read off
`data/schema/zbz_hersch.rng` directly. Since E127 all four name-bearing elements declare
`@ref` inline with the pattern `GND:[0-9A-Za-z\-]+`, so the closed world of the entity
layer is a format constraint and no longer only a test over the mirror.

- `persName` and `orgName` carry the pattern as the ZBZ template delivered it.
- `bibl` carries the same pattern on `@ref` (E127) and keeps the template's pattern on
  `@corresp` as well as `@key` from `att.canonical`; the ZBZ guideline and the reference
  corpus write `bibl@ref`, and `@corresp` appears in the references only twice.
- `rs` carries the pattern on `@ref` (E127) and keeps `@role`, `@nymRef` and `@key`;
  neither the corpus nor the references use the element.
- `placeName` inherits the template's unconstrained `@ref`, untouched because Z3 forbids
  the element and nothing uses it.

The hardening is a pure narrowing, so every file valid under the project schema stays
valid under the ZBZ check template. The guard that holds it is described in
[verification.md](verification.md), quality assurance section; the decision is E127 in
[decisions.md](decisions.md).

## Unresolved phenomena

Hyphen compounds built from a listed name have no settled rule. The reference TEIs leave
them unmarked, the guideline gives no direction, and the tool decides them inconsistently,
so a suspicion signal parks them on the worklist until the library decides.

Image captions are unresolved at the guideline level, because the ZBZ guideline
contradicts itself (O27), banning entities in captions in its index section while its own
figure example carries an `orgName` in one. The operator convention of 2026-08-12 puts
captions in scope, while the matcher scans a figure zone and demotes every candidate
inside it to the worklist with the `:in-figure` suffix, so a caption mention stays a
proposal until ZBZ confirms the reading. Both items are tracked in
[decisions.md](decisions.md), plan section.

## Conventions for the whole project

Every parallel data stream of an object follows the identifier convention
`{doc_id}_p{N}`, so OCR text, layout JSON, page image, PAGE-XML and per-page TEI of the
same page carry the same key. The page image file is `{doc_id}_p{NNN}.png` with a
zero-padded number.

The `xml:id` schemes in use are `facs_N` for a surface, the layout zone identifier for a
zone, `fn{page}-{no}` for a footnote, `figN` for a figure with `figN-start` and `figN-end`
for its anchors, and the `resp-entity-*` vocabulary in the entities section for the
responsibility declarations of the preview and agent-review layers.

Language codes follow ISO 639-3. A multilingual value from the Masterfile is parsed into
one `<language>` element per code, because a compound value such as "fra/deu" otherwise
decays to `und` (journal lesson L8).

Facsimile and page breaks stay in sync. Every page that appears in the body receives a
`<surface>`, including pages without layout zones, which get an empty surface, so the
count of page breaks and the count of surfaces agree (journal lesson L9).
