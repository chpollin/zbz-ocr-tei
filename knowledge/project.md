---
title: Project
project:
  name: zbz-ocr-tei
  repository: https://github.com/chpollin/zbz-ocr-tei.git
method:
  name: Promptotyping
  url: https://dhcraft.org/Promptotyping/
template:
  name: Vorlage Projekt-Wissensdokument
  version: 0.2
  url: https://dhcraft.org/Promptotyping/promptotyping-document/project
absorbed: [data (Vorlage Datengrundlage 0.2), integration (Vorlage Integration 0.1)]
status: complete
language: en
version: 1.0
created: 2026-02-18
updated: 2026-08-21
authors: [Christopher Pollin]
related: [index, specification, tei-mapping, pipeline, workflow, methodology, verification, decisions]
---

# Project

LLM-supported OCR and TEI pipeline for the Jeanne Hersch papers (Nachlass) of the
Zentralbibliothek Zuerich. The charter below states the commission, the standards and the
delivered scope. The Data section carries the material, from corpus and sources through the
input model to limits and biases. The contracts with the systems the pipeline exchanges data
with are in the Integration section.

## Overarching context

The Zentralbibliothek Zuerich commissioned DHCraft on 14.02.2026 with automated OCR and TEI
annotation of the Hersch papers. Since the coordination meeting of 25.02.2026 (E21) the
repository covers the whole pipeline path from page image over OCR and layout analysis to
PAGE-XML and TEI-XML, while ZBZ keeps Transkribus running in parallel as a second source.
Project management sits with DHCraft, the editorial authority with the ZBZ project team.

The repository is a tool. It produces edition-ready data and the instruments that let a
curator verify and correct that data; the edition itself is built downstream at ZBZ in
Oxygen, GitLab and Alma. Every delivered stream therefore starts at the workflow status
`unverifiziert`, which states that pipeline output exists and awaits the scholarly
verification that belongs to ZBZ (E66/E67). The counterpart contracts with ZBZ, Transkribus
and teiCrafter are in the Integration section below.

## What it is about

The mission is to turn scanned pages into schema-valid TEI that a curator can verify page by
page against the facsimile, so edition work starts from structured data. Three commitments
follow from that. The delivered TEI validates against the project schema and carries its own
provenance in the `revisionDesc`. Every published quality figure rests on a stated method and
is reproducible from a command. Every human verification step is recorded per stream and
travels with the object.

The corpus splits into four layout classes, from single-column prose over two-column journal
pages and long monographs to special cases such as historical print, interview transcripts
and illustrated books; each class routes to its own processing strategy. The classes and
their strategies are defined in the Data section below, document types A to D, and the
routing that consumes them is in [pipeline.md](pipeline.md).

## Standards

- TEI P5 as the delivery format, in the inline-GND markup model of the ZBZ editorial
  guidelines (E88).
- The ZBZ editorial guidelines in `data/source/guidelines/` as the editorial authority; they
  are immutable input and their interpretation belongs to ZBZ.
- `data/schema/zbz_hersch.rng` as the single format authority for delivered TEI (E48/E49,
  extended E68, sole authority since E102). Every final document validates against it under a
  test gate.
- PAGE-XML with a METS wrapper as the parallel export format for the Transkribus round trip
  (E13/E81).
- GND identifiers as the authority-data vocabulary, resolved through the lobid API for the
  variant cache of the entity layer.

The consolidated requirement view over these authorities is
[specification.md](specification.md).

## Technical implementation

The six-stage pipeline, its engines and the markup rules it applies are in
[pipeline.md](pipeline.md) and [tei-mapping.md](tei-mapping.md). The end-to-end data flow,
the viewer, the save path and the round trip are in [workflow.md](workflow.md). Deployment,
API access, continuous integration and the static delivery are in
[pipeline.md](pipeline.md), deployment section.

## Scope of functions

What the repository delivers today, by component.

| Component | Delivered function |
|---|---|
| Image extraction | page images per document at a configurable resolution (`scripts/edition/extract_pages.py`) |
| OCR | base text layer per page for every delivered PDF; `--engine auto` resolves to Gemini, while the Mistral path that produced the delivered corpus stays selectable as its reproducibility record (E6) |
| OCR post-correction | optional LLM post-correction (E17) and a Gemini correction variant on a sample (E29) |
| Layout analysis | Docling regions with bounding boxes plus Gemini quality assurance in `--mode auto` (E19/E20, E25/E26/E31) |
| PAGE-XML export | PAGE-XML per page with a METS wrapper, plus the Transkribus upload bundle (E13/E81) |
| Document classification | one-shot classification into the four document types, cached in `data/doc_metadata.json` (E27) |
| TEI generation | the unified pipeline of scaffold, model refinement, assembly and validation, schema-valid across the corpus (E32/E102) |
| TEI validation | RelaxNG plus the project rules R1 to R7, the warning rules and the ZBZ conformity rules; catalog owned by [specification.md](specification.md) |
| Entity layer | deterministic closed-world matcher against the curated ZBZ entity list; its marks land in a read-only preview layer with per-page views in the viewer and the corpus overview `docs/entities.html`, and the delivered TEI stays entity-free until an operator releases the stock run |
| Workflow status | three-level status per stream with human-only transitions, provenance history in the per-object manifest and deterministic projection into the TEI `revisionDesc` (E66/E67/E77) |
| Blank pages | safe blank pages detected per object and projected as `<pb type="blank"/>` (E63/E65) |
| Viewer | static single-page app with facsimile, OCR, TEI and layout side by side, layout and text editing, one save that writes into the working tree and the mirror, and per-stream export (E56/E58/E60/E72/E78/E79/E107) |
| Measurement | fidelity CER against the reference TEIs with bootstrap intervals, the quality proxy for documents without ground truth, and the corpus audit as the funnel gate |
| Delivery site | static GitHub Pages site with catalog, viewer, method page and entity overview, served from the generated mirror `docs/data/` |
| Continuous integration | GitHub Actions runs the linter and the full test suite on every push and pull request |

Open items and their conditions are in [decisions.md](decisions.md), plan section; the status
tracker there holds the current state per milestone.

## Delimitations

ZBZ owns the library-side steps of the edition. The division of responsibilities, the
acceptance criteria and the open input gaps are in the Integration section below.

Inside the repository three areas are bounded by design. Entity marks live in a read-only
preview layer until an operator releases the stock run. Document-level and per-character
curation decisions, meaning `front`, `back`, cross-page `anchor` and `unclear`, are made in
the viewer against the facsimile, with the reasons in [tei-mapping.md](tei-mapping.md).
Reading-order repair on flagged pages runs page-wise and facsimile-verified, because the
corpus-wide machine rollout was tested against the reference documents and refuted (E99).

## Licence

MIT, `LICENSE` at the repository root.

## Data

This section carries the material of the project. It states what the corpus is, where every
input comes from and under which versioning rule it lives, how the delivered and the
project-built data are structured, and which limits and biases bound what may be inferred
from it.
What the pipeline does with the material is in [pipeline.md](pipeline.md), and the claims
measured on it are checked in [verification.md](verification.md).

### Subject

The material is the printed work of Jeanne Hersch, held as papers (Nachlass) at the
Zentralbibliothek Zuerich. It covers journal articles, contributions to edited volumes and
monographs from the 1930s to the late 1990s, written predominantly in French, with a substantial
German share and single texts in English and Italian. The philosophical, political and
pedagogical writing of one author across six decades is the subject; the pipeline treats each
catalogued text as one object.

#### Corpus funnel and page balance

All figures in this subsection and in the following one (genres, languages, period) are generated via `python -m scripts.eval.corpus_audit` (artifact
`output/corpus_audit.json` / `.md`, every figure bound to a `(source, unit, extraction)` triple);
regenerate on change, do not maintain by hand. As of 2026-05-27.

The corpus funnel runs 325 Masterfile texts -> 289 digitized -> 286 delivered as PDF -> 285 with
final TEI. The figure "289" reads off the Masterfile's `digitalisiert` counter, which counts in a
different unit from the text level. 3 digitized texts are without PDF delivery, namely `1745`,
`1750`, `1970`; 1 PDF is without final TEI, namely `10`.

Page counts come in four units that must never be mixed:

| Unit | Value | Source |
|---|---|---|
| bibliographic | 7,186 | Masterfile (text level, n=325) |
| physical | 4,152 | delivered PDFs (pypdfium2) |
| processed (OCR) | 4,122 | pipeline (volatile on re-OCR) |
| processed (TEI `<pb>`) | 4,115 | final TEI |

Median 6 pages/text, maximum 588 (Masterfile, bibliographic).

#### Genres, languages, period (delivered documents, n=286)

The authoritative view is the delivered one, the Masterfile metadata of the 286 PDFs; the
catalogued total holdings describe a larger set that the pipeline never saw. Period 1931-1998,
with 168 texts from the 1970s and 1980s.

| Genre (`PublForm`) | n | Share |
|---|---|---|
| Journal articles (`journalArticle`) | 146 | 51% |
| Edited volume contributions (`bookSection`) | 116 | 41% |
| Monographs (`book`) | 24 | 8% |

| Language | n | Share |
|---|---|---|
| French | 203 | 71% |
| German | 72 | 25% |
| English | 7 | 2% |
| Italian | 2 | <1% |
| bilingual fr/de | 1 | <1% |
| not specified | 1 | <1% |

> For comparison, the catalogue level (n=325, entire recorded holdings) shows genre `journalArticle` 159 / `bookSection` 127 / `book` 38 / AV medium 1; language fr 215 / de 98 / en 8 / it 2 / fr-de 1 / not specified 1; period 1931-2010, 193 in the 1970s/80s.

#### Document types A to D

Every object carries a type that decides how it is read. The classification is a property of the
material and steers the processing strategy.

| Type | Layout | Strategy |
|---|---|---|
| A | single-column | direct OCR |
| B | two-column (journals, encyclopedias) | layout analysis + OCR per region (Docling + Gemini) |
| C | monograph (100+ pages) | OCR + chunking, page-by-page comparison (E16) |
| D | special (historical, interview, illustrated book) | case by case |

#### Pilot sample

Fifteen delivered PDFs form the frozen pilot set that prompt development and manual inspection
work against. The set spans all four document types, both main languages, the page-length range
from two pages to a full monograph, and the layout peculiarities the corpus is known to carry.

| File | Pages | Language | Type | Genre | Peculiarity |
|---|---|---|---|---|---|
| 2310.pdf | 3 | FR | A | review | JSTOR cover |
| 1180.pdf | 8 | DE/FR | A | annual report | title page |
| 130.pdf | 18 | FR | A | journal article | cover page |
| 290.pdf | 5 | FR | A | Comptes Rendus | essay |
| 1410.pdf | 6 | DE/FR | A | contribution | bilingual, partly two-column |
| 1060.pdf | 8 | DE | A | brochure | speech |
| 2530.pdf | 2 | FR | B | article | two-column |
| 890.pdf | 7 | DE | B | teachers' journal | small print |
| 3040.pdf | 9 | FR | B | encyclopedia | footnotes |
| 40.pdf | 156 | FR | C | novel | handwritten notes |
| 1520.pdf | 142 | FR | C | monograph | long |
| 90.pdf | 6 | DE | D | historical print | 1944 |
| 830.pdf | 2 | FR | D | illustrated book | little text |
| 1440.pdf | 5 | DE | D | interview | dialogue format |
| 1330.pdf | 6 | FR | D | edited volume | preface |

### Sources

Two categories of material meet in `data/` and follow different versioning rules. The ZB delivery
under `data/source/` is immutable input, produced by the library and never written back to.
Everything else in `data/` is project-built authority, git-tracked, and maintained here.

#### ZB delivery

The delivery "HerschStandFeb" (February 2026, E23) carries the scans and everything ZBZ had
produced on them at that date.

| Category | Location | Origin |
|---|---|---|
| PDF scans | `data/source/pdf/` | ZBZ digitization, named by project ID (`2310.pdf`) |
| Reference / gold TEI | `data/source/reference_tei/` | ZBZ Transkribus, finished annotations |
| PAGE-XML exports | `data/source/transkribus_page_xml/` | ZBZ Transkribus, one folder per object |
| Catalogue and steering | `data/source/masterfile/Masterfile.xlsx` | ZBZ Alma / swisscovery plus project workflow |
| Editorial guidelines | `data/source/guidelines/` | ZBZ, the binding markup rules |

The Masterfile is the gold source for counts and for language and genre metadata. Its sheet
carries the object ID, MMSID, publication form, year, title, bibliographic reference, page count,
shelf mark, location, language and the ZBZ-side workflow columns; `corpus_audit` reads it for
every catalogue-level figure. Where the Gemini document classification and the Masterfile
disagree on language, the Masterfile decides.

The editorial guidelines are the single source of truth for the markup rules and feed, among
other things, `VALID_DIV_TYPES` in `scripts/config.py`. They refer to the DTA-Basisformat and
document their deviations from it; the format authority for project output is
`data/schema/zbz_hersch.rng` (E102).

A second, dated delivery lies under `data/source/zbz-lieferung-2026-06-21/` and is git-tracked. It
holds the fuller current version of the ZBZ editorial guidelines and the matching ZBZ RelaxNG
template, secured unchanged from a transient inbox. It serves as a reference; the active schema
stays `data/schema/zbz_hersch.rng`, which is exactly that template plus the header elements the
pipeline regularly produces, `revisionDesc`/`change`, `langUsage`, `idno` in the
`publicationStmt` and `monogr`/`imprint` (E68/E88). The template alone declares those elements
`notAllowed` and would invalidate the delivered stock. One contradiction inside the ZBZ material
remains open, since the guidelines demand ID, MMSID and publication form in the header while the
template forbids `idno` in the `publicationStmt`; it goes back to ZBZ as O8, see the Integration
section below.

The reference TEIs need a description of their own. They are the 25 objects ZBZ annotated in
Transkribus, and they are the only ground truth the project has. Three parallel readers read them
in full against the editorial guidelines on 2026-07-07 (E92). Their body coding follows the
guidelines in the load-bearing conventions, that is genre div types, page breaks with bracketed
supplied numbers, hyphenation including the page-break rule, the footnote ID scheme
`fn{page}-{no}`, the inline GND entity model and the rendition vocabulary. The concordance finding
on their header layer belongs to the verification of the measurement and lives in
[verification.md](verification.md); what the material attests and where
it deviates is in Limits and Examples below.

#### Project authority

| Artifact | Path | Role |
|---|---|---|
| Project schema | `data/schema/zbz_hersch.rng` | format authority for all delivered TEI (E102) |
| Curated TEI | `data/curated_tei/` | reserved for hand-verified TEI, currently empty |
| Curated entity list | `data/entities/all_entities.json` | closed world of markable entities, external export |
| GND variant cache | `data/entities/gnd_cache.json` | name variants and metadata per GND id, dated |
| Variant review | `data/entities/variant_review.json` | operator verdicts over every cache-derived form |
| Legacy mention index | `data/entities/legacy_mentions.json` | surface forms attested in reference TEIs |
| Marking policy | `data/entities/marking_policy.json` | operator decisions about what may be marked |
| Mention verdict store | `data/entities/mention_verdicts.json` | adjudicated per-mention judgments, snapshot-bound |
| Document classification | `data/doc_metadata.json` | generated Gemini classification, committed cache |

The curated entity list is an external export and no repo tool produces its format, so defects in
it are reported by the intake audit and fixed at the producing tool. One defect class shows up
only in the API lookup, ids that are formally plausible yet unknown to the GND, typically
catalogue numbers mistaken for GND ids. The legacy mention index is a remnant of the removed LLM
entity phase, kept because it contributes surface forms attested in reference TEIs; its ids lack
the GND check character and are normalized before joining. The marking policy is held apart from
the entity list deliberately, because the list may be replaced wholesale while the policy records
decisions taken on evidence.

### Model

#### Object and stream naming

An object is one catalogued text, identified by its numeric project ID, and it carries several
parallel data streams. Every per-page artifact of every stream follows the convention
`{doc_id}_p{N}`, so a page of one stream resolves to the same page of every other. The final TEI
of an object lives at `output/tei_final/{doc}_final.xml` and is the single source of truth of the
delivered data (E43); beside it sits `{doc}_manifest.json`, the annotation slot that carries
workflow status and history per stream plus the exception pages. Which format each stage produces
and where it is written is in [workflow.md](workflow.md), data formats section; the mirror under
`docs/data/` is generated and never edited by hand.

#### Delivery tree

```
data/
├── source/                       # ZBZ delivery, immutable input
│   ├── pdf/                      # PDF scans, named by project ID             [gitignored]
│   ├── reference_tei/            # Transkribus reference/gold TEI (.xml)      [gitignored]
│   ├── transkribus_page_xml/     # Transkribus PAGE-XML, one folder per doc   [gitignored]
│   ├── masterfile/               # Masterfile.xlsx (catalogue + steering)     [gitignored]
│   ├── guidelines/               # editorial guidelines (text + DTA link)     [tracked]
│   └── zbz-lieferung-2026-06-21/ # dated reference snapshot: guidelines + rng [tracked]
│
├── schema/                       # zbz_hersch.rng, the format authority       [tracked]
├── curated_tei/                  # reserved for human-verified TEI (empty)    [tracked]
├── entities/                     # entity list, GND cache, variant review,
│                                 # marking policy, legacy index, verdicts     [tracked]
└── doc_metadata.json             # generated Gemini classification cache      [tracked]
```

`source/` is excluded from Git because of size and sensitivity. A fresh clone therefore carries
the project authority and the classification cache while the raw delivery has to come from ZBZ;
the test suite marks which parts depend on the delivered corpus, see
[verification.md](verification.md), quality assurance section.

#### Entity input model

The entity list has three categories, persons, organisations and works, and every entry carries a
GND id. A person entry carries `GND_id`, `name`, `lifetime`, `description`, `listBibl` and
`editor_reviewed`; an organisation entry carries `GND_id`, `orgName`, `listBibl` and
`editor_reviewed`; a work entry carries `GND_id`, `title`, `author_gnd_id`, `listBibl` and
`editor_reviewed`. An entry of any category may add an optional `variants` field, the operator
channel for a corpus spelling the GND norm form does not carry; each of its strings runs through
the form derivation of its category and takes the tier its own shape earns. The list defines the
closed world, so a name absent from it is never marked.

The GND cache keys its entries by id and records `http_status`, `preferred_name`, `variant_names`,
`types`, `date_of_birth`, `date_of_death` and the Wikidata QID, with the retrieval date and the
lobid source pattern at the top level. Variants bridge the transliteration gap between the list
form and the printed form, translated work titles and inverted forms. Defective ids answer 404, so
the same pass validates the list.

The variant review holds a verdict per cache-derived form, `approve`, `suspect` or `reject`, with
a reason. The lexicon builder consumes it deterministically, a rejected form never enters, a
suspect form yields lower-tier candidates only, and a form the review does not know counts as
suspect until the next review pass. Curated headwords, curated variants and legacy forms stay
outside its reach.

The marking policy carries two decision families, both taken on the evidence tables of 2026-08-13
(E119). `anchor_free_surnames` releases a surname from the document-anchor requirement for exactly
the keys the entry names, so nothing derived from a released key inherits the release and every
demotion suffix keeps its effect. `work_titles` either takes a generic title out of the marking
scope entirely (`drop_from_scope`, a lexicon matter) or binds it to typographic evidence
(`require_typographic_corroboration`, a matcher matter). `held_out_surnames` records what was
considered and deliberately held back, so the reasoning survives. The policy is validated on load
and a gid it names that the list does not carry raises an error. How the
matcher consumes all of this is in [tei-mapping.md](tei-mapping.md) and
[pipeline.md](pipeline.md).

### Limits

#### The reference corpus is selectively transcribed

The 25 reference TEIs transcribe the reading text and leave out material the pipeline captures,
such as mastheads, author lines and edition metadata. A naive full-text comparison therefore
charges the pipeline for being more complete than its reference; the measurement separates that
share out, see [methodology.md](methodology.md), CER measurement section. Where the reference
itself carries a transcription error, a more correct recognition counts as a difference and
raises the measured value.

#### Exception catalog of the reference corpus

Every reference-based check (CER benchmark, `structure_audit`, `--compare-ref`) must treat the
following as expected material properties. The numbering is load-bearing, because scripts cite
individual entries by number.

1. Header stub instead of ALMA header, all 25.
2. Root `type="naegeli"`, all 25; in 130 and 2310 with a whitespace defect (`type= "naegeli"`).
3. Foreign-language practice split between document groups: correct `foreign xml:lang` in one
   group (300, 2635, 3020, 90), italics-only marking in another (1060, 1180, 1520); 1910 carries
   the literal placeholder `xml:lang="[fre]"`.
4. `break="yes"` as an undocumented, partly wrong value (1060, 1330, 2530, 30, 3040, 890).
5. Only `rendition="#i"` is broadly realized; `#u`/`#b`/`#g`/`#sup` occur in one document each,
   `#sub`/`#k` never.
6. `rend="italic"`/`"bold"`/`"superscript"` instead of `rendition="#…"`: 2530, 1180 (mixed within
   one paragraph), 1410, 3040.
7. GND references without the `GND:` prefix: 290, 1330, 1520, 3040 (there also one persName
   without any `ref`); `corresp` instead of `ref` on work `bibl`: 100, 30, 560.
8. Adjectivized person names tagged against the guideline's own rule: 1910.
9. One footnote without `xml:id` beside correctly tagged siblings: 290.
10. Entities inside picture captions despite the explicit ban: 760 (systematic).
11. Data hygiene singletons: doubled uncorrected `choice` text (1910), trailing slash in `graphic`
    URLs (760, 2635, 830), a line-region ID as page `facs` (830), whitespace in a page number
    (560), `@n` on `p` instead of `lb` (90), `pb` without `facs` (300 throughout, 1910, 3020),
    `pb` inside a paragraph (1060 and 1440 repeatedly, 90 and 1410 once each), lowercase line
    numbering with leading space (130), author credit in the text body (1410).
12. 3020 types a panel discussion as `interview` where the guideline reserves `conversation`;
    spoken exchange is coded as `sp` in 3020 and as a dash `list` in 300.

Reference 1520 is not well-formed. Three structurally identical crossed `item`/`p` nestings sit
around lines 6936, 6979 and 6995, and the parser reveals them only one at a time. The original
stays untouched as the ZBZ source datum. The document is measured inside the 25-document benchmark
either way, because the text extraction falls back on a parse error to the regex rule E12 of the
extraction catalog in [methodology.md](methodology.md). The repair proposal that goes back to ZBZ
is a contract point, see the Integration section below.

#### Phenomena the ground truth never shows

Marginalia (`note place="right/left"`), multi-page footnotes with `@next`/`@prev`, `unclear`,
`gap`, the div types `conversation` and `dedication`, and the renditions `#sub` and `#k` are
attested in no reference. They can be checked against guideline and facsimile only. The
document-level and cross-page structures are thin as well, because they come from curation rather
than from the generator; `front` occurs in six documents (890, 1060, 1180, 1410, 2635, 3020),
`back` in five (40, 300, 830, 1410, 1520), a cross-page `anchor` in one (760), `epigraph` in one
(1440), and `unclear` in none. Why the pipeline leaves these structures to curation is in
[tei-mapping.md](tei-mapping.md).

#### Known problem cases

Material properties that cost accuracy in specific documents. The rule that flags the first row
corpus-wide is the validator warning W19, owned by [specification.md](specification.md),
validation rule catalog.

| Problem | Affected documents | Approach |
|---|---|---|
| Two-column reading order | large majority of the delivered corpus (audit), focal points incl. 810/1520/2360/760 | Docling and Gemini detect; `reading_order_audit` triages robust against fragile; machine reorder refuted (E99), facsimile-verified page-wise curation via `tei_reading_order_fix` |
| Cross-page footnotes | 3040 | `@next`/`@prev` |
| Interview speaker changes | 1440 | pattern recognition |
| Historical print | 90 | test both OCR engines |
| Handwritten annotations | 40 | open |

Newspaper layouts fail systematically, with many small zones per page and OCR hallucinations
(journal lesson L15). They form a small share of the corpus.

### Authority data and links

GND ids are the only entity identifiers the material carries, and the binding markup convention
puts them inline at the mention (E88), as the reference TEIs attest. The project resolves them
through lobid (`https://lobid.org/gnd/{id}.json`), which also yields the Wikidata QID per entity.
The lookup is deterministic; entity identity is never inferred by a language model.

The catalogue side of the authority data stays with ZBZ. Header metadata from Alma, that is ID,
MMSID and publication form, is ZBZ domain and deliberately absent from the pipeline. The editorial
guidelines demand these fields while the pipeline does not produce them, which is open question O8
in [decisions.md](decisions.md) and a contract point in the Integration section below.
Swisscovery links occur inside reference TEIs in back matter and are reference-side data.

The ZBZ editorial guidelines are the authority for the markup vocabulary itself. The delivered
copy under `data/source/guidelines/` and the fuller copy in the June 2026 snapshot are both
tracked; the reading of the guidelines the generator implements is in
[tei-mapping.md](tei-mapping.md).

### Biases

- Language skew towards French. Roughly seven in ten delivered texts are French, which makes
  French typography (guillemets, accents, ligatures, spaces before punctuation) and French
  hyphenation the dominant case, and prompt examples are predominantly French for the same reason.
  A measured value over the whole corpus is therefore largely a statement about French print.
- Genre skew towards journal articles and edited-volume contributions. Monographs are few and
  long, so page-weighted and document-weighted views of the same corpus differ substantially.
- Period concentration in the 1970s and 1980s, which carries the print technology and the
  typographic conventions of those decades into every aggregate.
- The reference corpus attests body-level phenomena densely and document-level structures thinly,
  so reference-based checks are sharp on paragraph and line phenomena and weak on front matter,
  back matter and cross-page structures.
- The Gemini document classification overestimates multilingualism, which is why the Masterfile
  decides the language field.

### Provenance per value

| Artifact | Produced by | Method |
|---|---|---|
| `data/doc_metadata.json` | `python -m scripts.ocr.classify_docs` | one-shot Gemini classification per PDF, committed as a cache (E27) |
| `data/entities/gnd_cache.json` | `python -m scripts.entity.fetch_gnd_variants` | one lobid-GND lookup per id, deterministic, dated |
| `data/entities/mention_verdicts.json` | `python -m scripts.entity.build_mention_verdicts` | folds the facsimile-adjudicated case files into one store, keyed per mention |
| `data/entities/variant_review.json` | model audit under an operator gate | verdict per cache-derived form, worklist under `output/audits/` |
| `data/entities/marking_policy.json` | operator | decisions taken on evidence tables, validated on load |
| `data/entities/all_entities.json` | ZBZ | external export, no repo tool produces its format |
| `data/source/*` | ZBZ | delivered, never written back to |

The verdict store is bound to a per-document fingerprint over the final TEI, so any re-OCR,
correction run or stock correction marks its records stale. Without that binding a changed text
would displace the stored offsets silently.

Every data channel, present or future, is its own trust boundary and passes three steps before its
forms may match, namely an intake lint, a shape-class review of the forms it contributes and a
pilot round. Which tier a form may serve follows from the form's own distinctiveness; the
authority of a source never lifts a form class into a higher tier. The lobid variants set the
precedent, since `variantName` mixes transliterations, translations, pseudonyms, inverted forms
and abbreviations, and only the shape-based filters in the matcher make the usable subset
explicit.

### Relation to the external source

The ZB delivery serves as input throughout. Nothing in the pipeline writes into `data/source/`, no
correction travels back into a delivered file, and the source of truth for the scans, the
reference annotations and the catalogue remains with ZBZ. Where the project finds a defect in
delivered data, the finding travels as a proposal and the corrected copy lives outside
`data/source/`, as with the 1520 well-formedness repair.

The Masterfile is the gold source for every catalogue-level statement, including counts, language
and genre. The project derives its figures from it through `corpus_audit`, and where a
project-side classification contradicts it, the Masterfile wins.

Everything else in `data/` is project authority. The schema, the entity channels and the
classification cache are maintained here, git-tracked, and regenerable from their named commands.
The delivered TEI itself lives under `output/tei_final/` and stays outside `data/`.

### Workflow

Material enters in four steps.

1. Delivery. ZBZ hands over scans, reference annotations, PAGE-XML exports, the Masterfile and the
   editorial guidelines; the files land under `data/source/` unchanged.
2. Funnel. `python -m scripts.eval.corpus_audit` reconciles the Masterfile, the delivered PDFs, the
   OCR results and the final TEI into one funnel and holds the figures this document carries
   against the computed ones, reporting every metric as OK or DRIFT. The corpus-bound tests in
   `tests/test_corpus_audit.py` guard the funnel invariants and pin the known completeness gap, so
   a silent document loss becomes a test failure.
3. Classification. `python -m scripts.ocr.classify_docs` assigns the document type per object into
   the committed cache, which steers the layout and OCR strategy per type.
4. Processing. The stages from image extraction to final TEI are described in
   [pipeline.md](pipeline.md); the streams they produce and the paths they write are in
   [workflow.md](workflow.md).

The entity channels enter separately. The list arrives as an export, `fetch_gnd_variants` builds
the cache and validates the ids against lobid in the same pass, `entity_lint` audits list, cache,
legacy pairing and policy, and only reviewed forms reach the matcher.

### Examples

The phenomenon map names, per guideline phenomenon, the reference documents that show it most
clearly. It is the lookup for anyone who needs an attested instance of a markup construct.

| Phenomenon | Best evidence |
|---|---|
| Lexicon entry (`div type="entry"`, `head type="lemma"`, `bibliography` with `listBibl`) | 3040 |
| Review (`div type="review"`, head as `bibl` with GND) | 2310, 570; 560 with footnote in the review head |
| Interview (`sp`/`speaker`, speaker with GND persName) | 3020, 1440 |
| Double page (two `pb` sharing one `facs`, distinct `n`) | 760, 30, 2635 |
| Figures (`figure` with `xml:id` and `graphic`; `anchor` start/end pairs only in 760) | 760, 2635, 830 |
| Footnotes (`note place="foot"`, `@n`, `xml:id` per scheme) | 290, 130, 560 |
| Title structure (`title type="main"` plus several `sub`, persName in title) | 1060, 290, 100, 40 |
| Hyphenation across the page break | 1910 |
| Supplied page number `n="[…]"` | 290, 30, 3020, 90, 40, 760 |
| Dot-notation page numbers (`7.15`, `3.32`) | 760, 830 |
| `front` (editorial preface) | 890, 1410, 2635 |
| `back` (`translation` with MLA + Swisscovery `ref`, `reprint`, `otherEdition`) | 40, 1520, 300, 830 |
| `foreign xml:lang` (correct 3-letter codes) | 3020, 300, 90, 2635 |
| Renditions | `#i` throughout; `#u` 1060; `#b` 890; `#g` 90; `#sup` 3040 |
| `choice/sic/corr` | 1180, 2310, 3020, 570 |
| Entity density (persName/orgName/bibl with GND) | 580, 1330, 2635, 1910 |
| Lists, dialogue as `list` | 890, 2530, 1330, 300 |
| Table (`table/row/cell`), deep div nesting | only 1520 |
| `epigraph`, `div type="text"` (both outside the guideline catalog) | 1440 |

## Integration

This section holds the contracts between the pipeline of this repository and the three
systems it exchanges data with, ZBZ, Transkribus and teiCrafter; data moves in both
directions across them. Each contract has one side that owns it. This repository owns the
delivered TEI in `output/tei_final/` and the PAGE-XML bundle it builds for Transkribus. ZBZ
owns the editorial guidelines, the Masterfile, the reference TEIs and the review of the
delivery schema. The teiCrafter documentation owns the teiCrafter annotation model, while
the ZBZ rules prevail wherever the two disagree (O26/E88).

### Data flow

Every stream enters or leaves through a directory; no live service call connects the
counterparts. The pipeline stages that produce these streams are described in
[pipeline.md](pipeline.md), the end-to-end movement in [workflow.md](workflow.md).

#### ZBZ

Inbound, as immutable input under `data/source/`, arrive the PDF scans, the Masterfile
(Excel) as the coordination record of the edition project, the reference TEIs, the
editorial guidelines, and a Transkribus PAGE-XML export of the objects ZBZ has already
worked on. The material side of these inputs is described in the Data section above.

Outbound go the final TEI documents in `output/tei_final/`, each with its per-object
manifest, and the production state on the GitLab fork.

Edition production at ZBZ runs in three parallel tracks, and the pipeline enters the first
of them.

1. Transcription, from digitized images through Transkribus to GitLab, Oxygen and back to
   GitLab.
2. Metadata, from digitized images through Alma and the Masterfile to Swisscovery and the
   TEI header.
3. Correction loop, from Oxygen as PDF to external reviewers and back into Oxygen.

The Masterfile coordinates all three tracks. Almost every step there is manual; the
Transkribus process is not standardized, external corrections travel as PDF rather than as
XML, and GND linking happens by hand in Oxygen. Since E21 the pipeline replaces or
complements three steps of the transcription track.

| Existing step at ZBZ | Replaced by the pipeline |
|---|---|
| Transkribus OCR | batch OCR over the delivered PDFs |
| Manual Transkribus export | automatic PAGE-XML export |
| Oxygen TEI markup | automatic TEI transformation |

The systems the tracks run on stay in ZBZ hands.

| System | Function | Format |
|---|---|---|
| Transkribus | OCR/HTR plus transcription | not standardized |
| Masterfile | workflow plus status | Excel |
| GitLab | TEI versioning | XML |
| Oxygen | TEI markup plus transformation | XML |
| Alma | cataloguing plus metadata | catalogue data |
| Swisscovery | discovery | catalogue data |
| GND | authority-data linking | identifiers |

The fork model carries the production state.

| Aspect | Details |
|---|---|
| Development repository | GitHub, `chpollin/zbz-ocr-tei` |
| Production repository | GitLab University of Zurich (fork) |
| Merge direction | GitHub to GitLab, upstream updates |
| Fork adjustments | API keys, endpoints, ZBZ-specific configuration |

#### Transkribus

The working direction is outbound. Stage 4 writes standard PAGE-XML into
`output/page_xml/{doc}/page/`; `scripts/edition/transkribus_export.py` assembles it with
the page images into a bundle under `output/transkribus_upload/` (gitignored), and
`scripts/edition/transkribus_upload.py` sends the bundle to a Transkribus collection
(E81). This is the reverse of the viewer round trip, where curated edits come into the
pipeline.

The inbound PAGE-XML export ZBZ delivered has a single consumer, the export script, which
reads directory names from it to recognize the objects ZBZ already holds. No geometric or
structural comparison consumes it.

#### teiCrafter

The handover is a manual file open. A curator opens a final TEI in teiCrafter and
annotates it there; no export bridge writes into teiCrafter and no import bridge reads its
output back into the pipeline. The only trace of teiCrafter in the code is a comment in
`scripts/tei/zbz_conformity.py` recording that the entity rules Z1 to Z4 and Z8 apply to
curated teiCrafter output, while the delivered stock is entity-free.

### Exchange format

#### ZBZ

TEI P5 constrained by the project schema `data/schema/zbz_hersch.rng`. Every final TEI
carries a `<revisionDesc>` with the pipeline status (E42). `output/tei_final/{doc}_final.xml`
is the single source of truth of the delivered data (E43); `docs/data/` is a generated
mirror and is never edited directly. The element and attribute contract, including the
`<revisionDesc>` shape and the character normalizations, lives in
[tei-mapping.md](tei-mapping.md).

At the handover step `tei_status_marker.py` projects the per-stream workflow history from
the manifest into the `<revisionDesc>` as `<change>` entries (E66) and removes the stale
entries of the abolished agent screening. The status vocabulary and its semantics are
owned by [workflow.md](workflow.md), section Workflow Status per Stream. `unverifiziert`
is the handover default and states that the pipeline produced the stream deterministically
and that no human has released it. The neutral default follows from the pipeline producing
OCR, layout and TEI for every document, so the value describes the delivery state (E67).

#### Transkribus

PAGE 2013-07-15, one folder per document, the image at the top level and the PAGE-XML of
the same base name in a `page/` subfolder.

```
{doc}/
  {doc}_p001.png          # image at top level
  page/{doc}_p001.xml     # PAGE-XML with matching name
```

The dialect is compatible out of the box, with `TextRegion`, `Coords`, `TextLine`,
`TextEquiv` and `ReadingOrder` plus `custom` structure types. The pipeline PAGE carries
line polygons and no baselines, which is sufficient for import, display and structure;
only HTR model training in Transkribus needs baselines, and the ZBZ originals carry them.
The pipeline images measure about 1240x1754 pixels (150 dpi, the exact value follows the page),
the ZBZ originals 2479x3508 (300 dpi); each state is internally consistent.

The upload runs over the legacy TrpServer REST API at `transkribus.eu/TrpServer/rest`,
with `POST /auth/login`, then `POST /uploads?collId=` carrying a JSON manifest with
`md.title` and `pageList`, then `PUT /uploads/{id}` with image and XML per page. Verified
on 2026-06-08, the legacy API writes correctly into a collection on the current platform
at `app.transkribus.org`; login and collection share the readcoop account. Authentication
uses the environment variables `TRANSKRIBUS_USER`, `TRANSKRIBUS_PASSWORD` and
`TRANSKRIBUS_COLLECTION`, never values in code, repository or `.env`.

#### teiCrafter

TEI with inline GND markup at the mention site, every mention carrying `ref="GND:..."`.
The delivery model admits persons, organisations and works, and excludes a standOff
register, places, events and identifiers from GeoNames or Wikidata (E88). The full target
model, the provenance attributes and the tier rules are in
[tei-mapping.md](tei-mapping.md).

### Responsibilities

#### ZBZ

ZBZ owns Alma cataloguing, Masterfile maintenance, Swisscovery assignment, the TEI header
fields drawn from Alma, the manual GND linking in Oxygen, and the final quality assurance
in Oxygen before publication. ZBZ also owns the editorial guidelines and their
interpretation, so every question about what the guidelines require is decided there.

#### Transkribus

The platform side belongs to ZBZ, which holds the account and the target collection. This
repository owns the bundle it produces and the upload run it triggers.

#### teiCrafter

teiCrafter owns its annotation model and its documentation. This repository owns the TEI
that goes in and the conformity rules that judge what comes back.

### Acceptance criteria

#### ZBZ

A delivered document is accepted when it validates against `data/schema/zbz_hersch.rng`,
carries a `<revisionDesc>` with the pipeline status, and carries the projected workflow
history at handover. The gates that enforce this and the way they are run are in
[verification.md](verification.md), quality assurance section; the requirement view is in
[specification.md](specification.md).

#### Transkribus

Before a bundle is uploaded, the export verifies for every page that the PNG pixel
dimensions match the declared `imageWidth` and `imageHeight`, so that coordinates stay
aligned; pages without an image or with dimension drift are reported instead of being
copied silently. The export runs over the PAGE-XML rather than over the images, so pages
without layout, blank pages among them, stay out of the bundle. An upload run is preceded
by `--dry-run`, which checks login and collection access, and by `--doc` on a single test
object.

#### teiCrafter

Epic D of [specification.md](specification.md) states the acceptance from the annotator
side, a TEI stable enough for control and inline-GND annotation. The entity rules Z1 to Z4
and Z8 of `zbz_conformity.py` turn sharp on curated teiCrafter output, while Z5
(renderings) and Z6 (`pb facs/n`) already apply to the delivered stock.

### Open points and input gaps

#### ZBZ

- O8, header metadata from Alma including the MMSID. The editorial guidelines demand these
  fields, and the decision of 2026-06-08 places them in the ZBZ domain outside the
  OCR/layout/TEI pipeline. A projection was built with E69, removed with E76 and rejected
  again with E83. Open with ZBZ is who pulls from Alma and which fields. While it is open,
  most delivered headers carry an empty container title by intent.
- O13, TEI editorial details such as subject headings. The guidelines call the point
  unsettled. Until it is decided the headers stay without subject headings, which blocks
  no pipeline step.
- The reference TEI of document 1520 is not well-formed, with three structurally identical
  crossed `item`/`p` nestings. The repair swaps the closing-tag order at each spot and
  leaves the text content unchanged, and the corrected copy
  `output/1520_reference_fixed.xml` parses cleanly. The original stays untouched as the
  ZBZ source datum and the correction goes to ZBZ as a proposal; pending is only the
  ZBZ-side repair of the reference file.
- R5, fork divergence between DHCraft and ZBZ, is open because the merge strategy for
  upstream changes into the GitLab fork is undefined and `.gitlab-ci.yml` does not exist.
  The item is tracked in [decisions.md](decisions.md), plan section.

#### Transkribus

R7, PAGE-XML incompatibility, is partly resolved by E23 and E81. The schema version, the
id scheme `{NNNN}_p{NNN}` and the image format are settled. The delivered TextRegions carry
no `@type` attribute; they hold the reading order and, on many regions, a structure type
inside `@custom`, in the same `readingOrder {index:n;} structure {type:x;}` form the
pipeline writes. Their type vocabulary is the wider one, since it also uses `page-number`
and `header`, which the pipeline mapping `ZBZ_TO_PAGE_TYPE` in `scripts/config.py` never
emits. Open is whether the two vocabularies have to be aligned for re-import.

#### teiCrafter

- No export or import bridge exists, so the handover stays a manual file open until one
  side builds a bridge.
- The teiCrafter output-model switch to the inline-GND delivery model is pending, and Epic
  D stays cross-lane until it happens.
- O27, the ZBZ editorial guidelines contradict themselves on captions. The register section says entities
  in captions are not tagged, while the figures example tags an `<orgName ref="GND:...">`
  inside a `<figure>`. The open question is whether the ban covers the caption `<head>` or
  the whole `<figure>` block including its explanatory `<p>`. ZBZ decides. The rule is
  deliberately not machine-enforced while the contradiction stands, and it has no effect
  on the entity-free delivered stock.

### Corrections and pitfalls

Selection for the export runs by `--sample` (stratified over page count and language),
`--all`, `--reference` (the objects ZBZ already holds in its own Transkribus collection) or
`--doc`.

Uploading the reference objects again creates duplicates. Every upload run creates new
documents and the API performs no deduplication, which is why `--reference` exists as a
separate selection and why a full run is preceded by a single test object.

Reference-based checks measure against a ground truth that is guideline-true in the body and
locally defective elsewhere, because the reference TEIs are partial transcriptions with an
empty header and local flaws. The exception catalog in the Data section above belongs in
every scoring logic that consumes them.

The GND prefix and the `corresp`/`ref` split of the reference TEIs drift from the delivery
model, which matters for the teiCrafter lane. The reference practice serves as a model
only after normalization.

The resolution difference between the pipeline images and the ZBZ originals is deliberate.
Each state is internally consistent, so a bundle must never carry images of one resolution
with coordinates computed on the other.

Credentials for Transkribus live in environment variables and nowhere else. The variable
names are documented, the values never appear in code, repository, documentation or
`.env`.

### Authoritative documents

- [pipeline.md](pipeline.md): stages, engines, the PAGE-XML production, and in its
  deployment section GitHub Pages and the GitLab CI state
- [workflow.md](workflow.md): end-to-end data flow, viewer, persistence, status per stream
- [tei-mapping.md](tei-mapping.md): the TEI element and attribute contract, entity target model
- [specification.md](specification.md): requirements, epics, sources of authority
- The Data section above: delivered input material, reference corpus, exception catalog
- [verification.md](verification.md), quality assurance section: the gates that enforce the
  delivery contract
- [decisions.md](decisions.md): dated rationale for E21, E42, E43, E66, E81 and E88, and in
  its plan section the open decisions and deferred items
- [../CLAUDE.md](../CLAUDE.md): the CLI reference for export and upload, and the security rule

### Re-entry context

The ZBZ contract is live and running. The pipeline delivers final TEI that validates
against the project schema, and the items still open there are editorial questions for ZBZ
rather than pipeline work. The Transkribus contract is built and verified end to end, with
one test object uploaded successfully; a full run is an operator decision. The teiCrafter
contract is specified and not yet exercised, because the annotation model on the
teiCrafter side has not switched to inline GND and no bridge exists in either direction.

Anyone resuming this lane reads [specification.md](specification.md) for what the delivery
must satisfy, [tei-mapping.md](tei-mapping.md) for how the markup is shaped, and
[decisions.md](decisions.md), plan section, for what is deferred and who decides it.

## References

- [index.md](index.md): navigation and glossary
- [specification.md](specification.md): requirements, quality method, validation rules
- [pipeline.md](pipeline.md): the six stages, engines, routing and deployment
- [tei-mapping.md](tei-mapping.md): the markup rules of the delivered TEI
- [workflow.md](workflow.md): data flow, viewer, save path, round trip, design system
- [methodology.md](methodology.md): Promptotyping, governance, CER measurement method
- [verification.md](verification.md): quality assurance and the verification of the claims
- [decisions.md](decisions.md): the dated decision register and the open milestones
- `docs/project-report.md`: the client report, a dated snapshot; measured values in `docs/data/cer_statistics.json`
