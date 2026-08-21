---
title: Data
project:
  name: zbz-ocr-tei
  repository: https://github.com/chpollin/zbz-ocr-tei.git
method:
  name: Promptotyping
  url: https://dhcraft.org/Promptotyping/
template:
  name: Vorlage Datengrundlage
  version: 0.2
  url: https://dhcraft.org/Promptotyping/promptotyping-document/data
status: complete
language: en
version: 1.0
created: 2026-08-21
updated: 2026-08-21
authors: [Christopher Pollin]
related: [project, specification, pipeline, tei-mapping, verification, integration]
---

# Data

This document carries the material of the project. It states what the corpus is, where every
input comes from and under which versioning rule it lives, how the delivered and the
project-built data are structured, and where the material stops carrying an inference. The
commission the material serves is in [project.md](project.md), what the pipeline does with it is
in [pipeline.md](pipeline.md), and the claims measured on it are checked in
[verification.md](verification.md).

## Subject

The material is the printed work of Jeanne Hersch, held as papers (Nachlass) at the
Zentralbibliothek Zuerich. It covers journal articles, contributions to edited volumes and
monographs from the 1930s to the late 1990s, written predominantly in French, with a substantial
German share and single texts in English and Italian. The philosophical, political and
pedagogical writing of one author across six decades is the subject; the pipeline treats each
catalogued text as one object.

### Corpus funnel and page balance

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

### Genres, languages, period (delivered documents, n=286)

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

### Document types A to D

Every object carries a type that decides how it is read. The classification is a property of the
material and steers the processing strategy.

| Type | Layout | Strategy |
|---|---|---|
| A | single-column | direct OCR |
| B | two-column (journals, encyclopedias) | layout analysis + OCR per region (Docling + Gemini) |
| C | monograph (100+ pages) | OCR + chunking, page-by-page comparison (E16) |
| D | special (historical, interview, illustrated book) | case by case |

### Pilot sample

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

## Sources

Two categories of material meet in `data/` and follow different versioning rules. The ZB delivery
under `data/source/` is immutable input, produced by the library and never written back to.
Everything else in `data/` is project-built authority, git-tracked, and maintained here.

### ZB delivery

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
stays `data/schema/zbz_hersch.rng`, because the ZBZ template omits header elements the delivery
contract requires. Reconciling the two schema versions is a contract point, see
[integration.md](integration.md).

The reference TEIs deserve their own reading. They are the 25 objects ZBZ annotated in
Transkribus, and they are the only ground truth the project has. Three parallel readers read them
in full against the editorial guidelines on 2026-07-07 (E85). Their body coding follows the
guidelines in the load-bearing conventions, that is genre div types, page breaks with bracketed
supplied numbers, hyphenation including the page-break rule, the footnote ID scheme
`fn{page}-{no}`, the inline GND entity model and the rendition vocabulary. The concordance finding
on their header layer belongs to the verification of the measurement and lives in
[verification.md](verification.md); what the material attests and where
it deviates is in Limits and Examples below.

### Project authority

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
it are reported by the intake audit and fixed at the producing tool. One defect class only the API
lookup exposes, ids that are formally plausible but unknown to the GND, typically catalogue
numbers mistaken for GND ids. The legacy mention index is a remnant of the removed LLM entity
phase, kept because it contributes surface forms attested in reference TEIs; its ids lack the GND
check character and are normalized before joining. The marking policy is held apart from the
entity list deliberately, because the list may be replaced wholesale while the policy records
decisions taken on evidence.

## Model

### Object and stream naming

An object is one catalogued text, identified by its numeric project ID, and it carries several
parallel data streams. Every per-page artifact of every stream follows the convention
`{doc_id}_p{N}`, so a page of one stream resolves to the same page of every other. The final TEI
of an object lives at `output/tei_final/{doc}_final.xml` and is the single source of truth of the
delivered data (E43); beside it sits `{doc}_manifest.json`, the annotation slot that carries
workflow status and history per stream plus the exception pages. Which format each stage produces
and where it is written is in [workflow.md](workflow.md), data formats section; the mirror under
`docs/data/` is generated and never edited by hand.

### Delivery tree

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
the test suite marks which parts depend on the delivered corpus, see [testing.md](testing.md).

### Entity input model

The entity list has three categories, persons, organisations and works, and every entry carries a
GND id. A person entry carries `GND_id`, `name`, `lifetime`, `description`, `listBibl` and
`editor_reviewed`; an organisation entry carries `GND_id`, `orgName`, `listBibl` and
`editor_reviewed`; a work entry carries `GND_id`, `title`, `author_gnd_id`, `listBibl` and
`editor_reviewed`. The list defines the closed world, so a name absent from it is never marked.

The GND cache keys its entries by id and records `http_status`, `preferred_name`, `variant_names`,
`types`, `date_of_birth`, `date_of_death` and the Wikidata QID, with the retrieval date and the
lobid source pattern at the top level. Variants bridge the transliteration gap between the list
form and the printed form, translated work titles and inverted forms. Defective ids answer 404, so
the same pass validates the list.

The variant review holds a verdict per cache-derived form, `approve`, `suspect` or `reject`, with
a reason. The lexicon builder consumes it deterministically, a rejected form never enters, a
suspect form yields lower-tier candidates only, and a form the review does not know counts as
suspect until the next review pass. Curated headwords and legacy forms stay outside its reach.

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

## Limits

### The reference corpus is selectively transcribed

The 25 reference TEIs transcribe the reading text and leave out material the pipeline captures,
such as mastheads, author lines and edition metadata. A naive full-text comparison therefore
charges the pipeline for being more complete than its reference; the measurement separates that
share out, see [cer-methodology.md](cer-methodology.md). Where the reference itself carries a
transcription error, a more correct recognition counts as a difference and raises the measured
value.

### Exception catalog of the reference corpus

Every reference-based check (CER benchmark, `structure_audit`, `--compare-ref`) must treat the
following as expected material properties. The numbering is load-bearing, because scripts cite
individual entries by number.

1. Header stub instead of ALMA header, all 25.
2. Root `type="naegeli"`, all 25; in 2310 with a whitespace defect.
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
    (560), `@n` on `p` instead of `lb` (90), `pb` without `facs` (1910, 3020), `pb` inside a
    paragraph (1060, 1440), lowercase line numbering with leading space (130), author credit in
    the text body (1410).
12. 3020 types a panel discussion as `interview` where the guideline reserves `conversation`;
    spoken exchange is coded as `sp` in 3020 and as a dash `list` in 300.

Reference 1520 is not well-formed. Three structurally identical crossed `item`/`p` nestings sit
around lines 6936, 6979 and 6995, and the parser reveals them only one at a time. The original
stays untouched as the ZBZ source datum. The document is measured inside the 25-document
benchmark either way, because the text extraction falls back to the regex rule E12 on a parse
error. The repair proposal that goes back to ZBZ is a contract point, see
[integration.md](integration.md).

### Phenomena the ground truth never shows

Marginalia (`note place="right/left"`), multi-page footnotes with `@next`/`@prev`, `unclear`,
`gap`, the div types `conversation` and `dedication`, and the renditions `#sub` and `#k` are
attested in no reference. They can be checked against guideline and facsimile only. The
document-level and cross-page structures are thin as well, because they come from curation rather
than from the generator; `front` occurs in six documents (890, 1060, 1180, 1410, 2635, 3020),
`back` in five (40, 300, 830, 1410, 1520), a cross-page `anchor` in one (760), `epigraph` in one
(1440), and `unclear` in none. Why the pipeline leaves these structures to curation is in
[tei-mapping.md](tei-mapping.md).

### Known problem cases

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

## Authority data and links

GND ids are the only entity identifiers the material carries, and the binding markup convention
puts them inline at the mention (E88), as the reference TEIs show it. The project resolves them
through lobid (`https://lobid.org/gnd/{id}.json`), which also yields the Wikidata QID per entity.
The lookup is deterministic; entity identity is never inferred by a language model.

The catalogue side of the authority data stays with ZBZ. Header metadata from Alma, that is ID,
MMSID and publication form, is ZBZ domain and deliberately absent from the pipeline. The editorial
guidelines demand these fields while the pipeline does not produce them, which is open question O8
in [decisions.md](decisions.md) and a contract point in [integration.md](integration.md).
Swisscovery links occur inside reference TEIs in back matter and are reference-side data.

The ZBZ editorial guidelines are the authority for the markup vocabulary itself. The delivered
copy under `data/source/guidelines/` and the fuller copy in the June 2026 snapshot are both
tracked; the reading of the guidelines the generator implements is in
[tei-mapping.md](tei-mapping.md).

## Biases

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

## Provenance per value

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
forms may match, an intake lint, a shape-class review of the forms it contributes, and a pilot
round. Which tier a form may serve follows from the form's own distinctiveness; the authority of a
source never lifts a form class into a higher tier. The lobid variants set the precedent, since
`variantName` mixes transliterations, translations, pseudonyms, inverted forms and abbreviations,
and only the shape-based filters in the matcher make the usable subset explicit.

## Relation to the external source

The ZB delivery is input and stays input. Nothing in the pipeline writes into `data/source/`, no
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

## Workflow

Material enters in four steps.

1. Delivery. ZBZ hands over scans, reference annotations, PAGE-XML exports, the Masterfile and the
   editorial guidelines; the files land under `data/source/` unchanged.
2. Funnel. `python -m scripts.eval.corpus_audit` reconciles the Masterfile, the delivered PDFs, the
   OCR results and the final TEI into one funnel, with a drift check against the figures this
   document carries, so a divergence between claim and disk surfaces as a test failure.
3. Classification. `python -m scripts.ocr.classify_docs` assigns the document type per object into
   the committed cache, which steers the layout and OCR strategy per type.
4. Processing. The stages from image extraction to final TEI are described in
   [pipeline.md](pipeline.md); the streams they produce and the paths they write are in
   [workflow.md](workflow.md).

The entity channels enter separately. The list arrives as an export, `fetch_gnd_variants` builds
the cache and validates the ids against lobid in the same pass, `entity_lint` audits list, cache,
legacy pairing and policy, and only reviewed forms reach the matcher.

## Examples

The phenomenon map names, per guideline phenomenon, the reference documents that show it most
clearly. It is the lookup for anyone who needs an attested instance of a markup construct.

| Phenomenon | Best evidence |
|---|---|
| Lexicon entry (`div type="entry"`, `head type="lemma"`, `bibliography` with `listBibl`) | 3040 |
| Review (`div type="review"`, head as `bibl` with GND) | 2310, 570; 560 with footnote in the review head |
| Interview (`sp`/`speaker`, speaker with GND persName) | 3020, 1440 |
| Double page (two `pb` sharing one `facs`, distinct `n`) | 760, 30, 2635 |
| Figures (`figure` with `xml:id`, `graphic`, `anchor` start/end pairs) | 760, 2635, 830 |
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
