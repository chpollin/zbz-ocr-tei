---
title: Final Work Report
type: report
project:
  name: zbz-ocr-tei
  repository: https://github.com/chpollin/zbz-ocr-tei.git
method:
  name: Promptotyping
  url: https://dhcraft.org/Promptotyping/
status: snapshot
language: en
created: 2026-05-27
updated: 2026-07-07
tags: [zbz-ocr-tei, report, delivery, cer, validation]
related: [specification, project, pipeline, workflow, decisions]
---

# Work Report: an LLM-Supported OCR and TEI Pipeline for the Digital Edition of the Writings of Jeanne Hersch

Digital Humanities Craft OG (DHCraft), project lead

* v2, 2026-07-07 (v1: 2026-05-27); this version consolidates the dated
  interim reports of June 2026 (footnote curation, conformity audit waves 1
  and 2, structure audit, frontend gap analysis) into one document
* AI support: Claude Code with the current Anthropic models

As a dated snapshot this report deliberately carries concrete figures; each
one names its generating source and is reproducible from it.

## 1. Project Context and Objective

This report documents an experiment within the digital re-edition of the
writings of Jeanne Hersch, a project of the Zentralbibliothek Zurich
(ZBZ).[^1] Hersch's philosophical work is multilingual, predominantly French
and German, and dispersed in its transmission. Multilingualism and a
heterogeneous print tradition are therefore the two defining requirements on
the pipeline.

In parallel to the established ZBZ workflow from digitization to digital
edition, the same route was traversed a second time, fully supported by
large language models (LLMs) and vision-language models (VLMs), agent-based
and tool-supported. The guiding question is whether such an approach reaches
the established workflow in text quality and effort. The parallel run also
supplies the basis of comparison: the reference TEIs of the established
strand, created manually via Transkribus, serve the experiment as ground
truth (section 6.1).

The subject is a pipeline that, starting from PDF scans, produces TEI-XML in
the DTA base format and makes it inspectable and curatable in an
accompanying web interface. The DTA base format is a TEI subset for the
uniform markup of digitized printed texts.[^2] The pipeline simulates
digitization from the PDFs but produces transcription, layout recognition,
and TEI-XML throughout via LLMs and VLMs. Pipeline and web interface emerge
through Promptotyping, a context-engineering practice for producing research
artifacts from research data and research contexts.[^3] Code generation took
place entirely inside Claude Code across many sessions;[^4] the production
process is traceable through the commit history of the openly available
repository.[^5]

## 2. Data Basis

At the start of the pipeline stand two components delivered by ZBZ, the PDF
scans of the digitized texts and the master file with the associated
metadata. This delivery forms the starting position; the full catalog
holdings and their library-side description remain out of scope.

The master file is ZBZ's catalog and steering table and contains two kinds
of information. The bibliographic master data cover ID, MMSID, genre, year,
title, page count, shelfmark, and language. The workflow columns record the
processing state in the ZB process, such as digitized, metadata checked,
corrected, and marked up.

The following volumes were delivered and processed (guarded by
`scripts/eval/corpus_audit.py`).

| State | Count |
| :---- | :---- |
| delivered documents | 286 |
| of which with final TEI | 285 |
| physical pages | 4,152 |

The distributions by document type and language refer to the delivery state
of 286 documents; the one document without a final TEI is noted in 6.3. The
delivered documents are printed texts throughout; handwritten material is
not systematically represented, so this is a pure OCR process. The holdings
span the years 1931 to 1998.

| Document type | Count | Share |
| :---- | :---- | :---- |
| journal articles | 146 | 51% |
| contributions to edited volumes | 116 | 41% |
| monographs | 24 | 8% |

| Language | Count | Share |
| :---- | :---- | :---- |
| French | 203 | 71% |
| German | 72 | 25% |
| English | 7 | 2% |
| Italian | 2 | 1% |
| multilingual fr/de | 1 | under 1% |
| unspecified | 1 | under 1% |

## 3. Repository Architecture

The folder `knowledge/` is a Promptotyping vault, a Markdown knowledge base
modeled on an Obsidian research vault, produced and curated inside Claude
Code, which maps the project knowledge and grows iteratively over the
project's course; individual documents emerge, grow, or are merged. The
guiding principle is the single source of truth: every fact stands in
exactly one document to which the others refer. Worth highlighting are the
chronological work journal `journal.md` as a descriptive layer beside the
git history, the numbered decision register `decisions.md`, and the
consolidated requirement view `specification.md`.

The folder `data/` holds input and reference data and separates the
delivered from the project-built. Under `data/source/` lie the starting data
delivered by the ZB: the PDF scans, the reference TEIs created manually via
Transkribus together with their PAGE-XML exports, the master file, and the
editorial guidelines. Beside them stand project-built reference data: the
project-specific TEI schema `data/schema/zbz_hersch.rng` and the folder
`curated_tei/`, reserved for hand-verified edition TEIs and empty until a
document has been verified by a domain expert. The LLM-produced document
classification lies in `doc_metadata.json` so it is not recomputed on every
pipeline run.

The folder `output/` holds all generated data streams (OCR, layout,
PAGE-XML, TEI) and is deliberately unversioned. The folder `scripts/` holds
the Python pipeline generated by Claude Code, grouped by domain into
subpackages (`ocr`, `layout`, `tei`, `eval`, `edition`, `core`); the
individual scripts are listed in appendix A. Reproducibility of the
evaluation is secured by the pytest suites under `tests/`, among them the
statistics library named in 6.1.

The folder `docs/` is configured for GitHub Pages and holds the frontend, a
mirror of the pipeline data, and the PNGs produced from the PDFs. Since
GitHub Pages serves only static files without a backend, the edition data
lies there as a generated per-page mirror under `docs/data/pages/{doc}/`,
which makes up the majority of the versioned files: a script splits the
final TEI page by page and stores one file per page for TEI, OCR text, and
layout. The mirror covers all 285 documents; only the facsimile images stay
local apart from a few demonstration documents. The binding source is not
this mirror but the TEI under `output/tei_final/{doc}_final.xml`, from which
the mirror is regenerated after every change, for instance after a renewed
pipeline run or an edit curated in the viewer and folded back. An edit made
on the mirror would be lost on the next run. This separation of binding
edition storage and display mirror holds for all following sections.

## 4. The Pipeline

The pipeline transfers PDF scans into TEI-XML. Per document three data
streams emerge: an OCR stream with the recognized text, a layout stream with
the page structure, and the TEI-XML stream derived from them with the edited
version. Processing is defensively designed throughout, so a failing
individual correction passes the input on unchanged instead of aborting the
run.

### From Scan to Page Image

At the start the PDF scans are split page by page into individual images on
which the subsequent stages operate.

### Text Recognition

Productively, text recognition runs on Mistral Document AI[^6] via Azure AI
Foundry. The model captures tables and lists beside running text and
delivers per-page Markdown; large documents are split automatically, a
decision Claude Code took on its own. Where this access is unavailable, a
multimodal Gemini model can take over the same task without any change for
the subsequent stages. An optional LLM-supported post-correction is
available but not active by default, because it adds no value on already
good input quality; where a corrected version exists, it takes precedence
over the raw one.

### Layout Analysis

Structure recognition combines Docling[^7] with a downstream Gemini step.
Docling supplies only the page structure, that is regions with position, not
the text. The Gemini step works in three modes. QA checks and complements
the Docling regions, Detect recognizes the layout anew directly from the
page image, and Auto switches to the replacing re-detection only when
Docling coverage is too weak. Both layout versions, Docling's and Gemini's,
are kept as separate files, so it stays traceable which region came from
which engine.

### Interchange Formats

From the layout and OCR streams, PAGE-XML[^8] is additionally produced and
from it a METS manifest[^9], interchange formats for external processing and
archival systems. The PAGE-XML arises from the same sources as the TEI
without being its precursor, for the TEI is formed directly from layout and
text.

### TEI Generation

TEI generation combines rule-based and LLM-supported work. First, a
deterministic scaffold emerges from the OCR and layout streams. Text
sections are assigned to layout regions by position, translated into
headings, paragraphs, footnotes, and comparable structures, and furnished
with page and line marks. The typographic unifications required by the
editorial guidelines and the resolution of hyphenated words are applied in
the process. Onto this scaffold a refining step builds, which presents the
page image together with the scaffold and the recognized text to a
multimodal model and so produces a structurally enriched version. Since
model-generated markup shows systematic idiosyncrasies, a correcting
post-processing follows that automatically cleans up frequent structure and
schema violations. In the concluding assembly the individual pages are
joined into one whole document, page-wise structural units are merged, and a
second set of document-wide corrections is applied.

### Validation

The produced TEI is checked in three layers: against the project-specific
RelaxNG schema `zbz_hersch.rng`, which builds on the DTA base format and is
extended by the binding ZBZ editorial guidelines; against project rules that
enforce structural minimum requirements blockingly (R1-R7); and against the
guideline rules a schema cannot express (`zbz_conformity.py`, Z1-Z8, inline
GND model). Informative warnings (W1-W19) additionally mark spots worth
checking without blocking validity. The rule catalog is specified in
`knowledge/specification.md`. The quantitative results as of this report:

| Check | Result |
| :---- | :---- |
| schema validity (`tei_final` against `zbz_hersch.rng`) | 285/285 valid (since E68; before the schema extension the delivered layer stood at 0/285) |
| blocking project rules R1-R7 | fulfilled corpus-wide |
| ZBZ conformity Z1-Z8 | 285/285 conform, 0 violations, 0 advisories; the entity rules Z1-Z4/Z8 turn sharp only on curated inline-GND output, since the delivered TEI is entity-free (E71) |
| documents with at least one warning | 145 on `tei_final` (the delivered layer), 121 on the intermediate `tei_unified`; the difference stems from post-assembly markers |
| reference TEIs against the project schema | 17/25 valid; the 8 invalid ones use elements deliberately excluded from the project schema, no pipeline defect |

The conformity audit of June 2026 (two waves) added the warning rules
W15-W18 and fixed the corresponding markup classes corpus-wide (div type
and n exclusivity, figure xml:id, head lemma, title main, foreign language
normalization, E84); the structure audit compares pipeline TEI against the
25 ground-truth structures as a pure diagnosis without gate (E84).

### Processing Status Instead of Self-Certification

For each document the pipeline produces three things: the recognized text
(OCR), the page structure (layout), and a DTA-conformant, simple TEI-XML
mapping the text structures (headings, paragraphs, footnotes, page and line
breaks). After machine generation these three data streams are initially
unverified, present but not yet checked by a domain expert. A human-set
processing status records the state of checking, separately for each of the
three streams. Each stream takes one of three values, unverified, in
progress, or verified, which appear in the web interface as a three-step
traffic light (neutral, yellow, green) and are advanced by click. Every
change is recorded in a document-level companion file, the manifest, one
JSON file per document, as a running list of the individual steps with
timestamp, editor initials, and previous and following status, so that a
complete processing trail emerges. At handover to the ZB these entries are
projected into the TEI revision description (`<revisionDesc>`) of the
document, so the processing history travels with the delivered document
itself. An earlier agent-based screening that labeled documents "APPROVED"
without any human involvement was abolished for exactly this reason (E66);
its labels made no statement about scholarly quality.

## 5. Web Interface and Curation

The web interface is a browser-based tool hosted on GitHub Pages for
checking and curating the pipeline results
([https://chpollin.github.io/zbz-ocr-tei/](https://chpollin.github.io/zbz-ocr-tei/)).
Its core is the pipeline viewer (`docs/viewer.html`), a single-page app
without backend and without build step, which loads its content from the
per-page mirror described in the repository architecture, a data store
produced in advance per document and page (prepared OCR text, layout
regions, and the page TEI split out of the final TEI) that serves the whole
corpus without a server. The viewer forms an image-text synopsis: facsimile
and associated text stand side by side so both can be compared page by page.
In view mode the facsimile renders through OpenSeadragon[^10] and allows
continuous zooming, panning, and rotating, with the recognized layout
regions as an overlay. The text area switches between three sources, the
prepared raw OCR text, the rendered TEI version, that is the formatted
reading text produced from the TEI-XML, and the TEI-XML source itself. Blank
pages are recognized up front, preferentially from the TEI marker
`<pb type="blank"/>`, alternatively via a text rule on the OCR result, and
are labeled as such instead of showing faulty regions or OCR artifacts.

Beside it stand four further directly reachable pages:

- corpus overview, a sortable table with workflow traffic lights and filters
  over stream and status
- method page, static, with the headline CER, stratified values, literature
  comparison, and limitations
- about page
- legal notice

Curation is integrated into the viewer and works without a separate server:
the browser holds no server state and uploads nothing; all changes stay
local and are saved only on click. Layout and text each carry their own
independent edit toggle. On switching into the layout editor the facsimile
display replaces OpenSeadragon with a simple editable overlay layer; in it,
region boxes can be selected, moved, resized, drawn anew, and deleted, their
type changed (six types: heading, paragraph, footnote, caption, filter,
skip) and their reading order arranged by dragging. The boxes are kept as
image-relative percentage coordinates (0-100, relative to the page
dimensions recorded in the layout analysis), so they lie congruently on
facsimile and overlay independent of zoom and resolution; the editor
corrects the boxes proposed by the machine layout analysis and precisely
does not presuppose their scholarly correctness.

The transcription editor makes the currently displayed text source directly
editable, with structural interventions reserved for the XML mode, since the
rendered view returns only the text and not the markup when editing. A
single save button secures all open streams at once, each twice: canonically
into the `output/` tree (layout to `output/layout/`, the curated text to
`output/ocr_curated/`, object manifest and final TEI to `output/tei_final/`)
and mirrored into the display mirror under `docs/data/`, so a reload shows
the state immediately. Writing goes through the File System Access API of
Chromium browsers directly into the local clone of the repository, the
working tree; where this interface is missing, a file download steps in as
the fallback level. Nothing is uploaded. The object manifest is the
per-document JSON holding workflow status and blank pages per data stream.
This deliberately server-less cut avoids backend operation and multi-user
conflicts. Saving does not replace the pipeline run, however: for a curated
layout or text version to enter the TEI, a renewed run (`--reassemble`)
regenerates the document, whose result is then lifted into the delivered
layer `output/tei_final/` and mirrored. This round trip of saving and
re-running still rests on convention rather than mechanism. (Outlook: it
could be closed in the future via the GitHub platform, for instance a commit
triggering a GitHub Actions run that executes `--reassemble` and writes the
regenerated TEI and mirror back.) Each data stream carries a three-step
status (unverified, in progress, verified) advanced by click in the viewer
and mirrored in the traffic lights of the corpus overview; the first
activation of an edit toggle automatically moves the affected stream from
unverified to in progress, and while changes are unsaved the interface warns
on leaving the page. The guiding idea is that the edition itself becomes the
curation tool: the editors work directly in the edition, learn more about
the texts in the process, and mend the pipeline's errors.

In addition, 79 safe blank pages in 15 documents were recognized and
projected into the final TEIs as `<pb type="blank"/>`. A page counts as safe
only when two independent signals agree: the OCR text is practically empty
(at most five characters, no alphanumeric character, or merely a blank-page
marker) and the Docling layout analysis finds zero regions. Only on
agreement is the marker set; where the signals contradict each other the
page is flagged for manual review instead of projected (no such conflict
occurred in the current corpus). Per-stream single export (layout, text,
TEI, manifest) is available from the viewer's export dropdown; a
JSZip-based ZIP bundle for per-document and bulk export is designed (E61)
but not yet implemented.

A frontend gap analysis across the DHCraft edition ecosystem (June 2026)
audited the viewer against its user stories; all high and medium findings
were fixed in the same wave (among them a save guard against partial TEI
overwrites, honest fallback messaging, keyboard operability of the layout
editor, focus management, a go-to-page navigation), while four low-severity
findings remain deliberately deferred until after the ZBZ acceptance. The
open findings live as frontend requirements in
`knowledge/specification.md`.

## 6. Quality and Methodological Contextualization

The quality of the pipeline is measured via the character error rate (CER)
against the manually created reference TEIs. Section 6.1 develops the
comparison methodology from the definition of the measure through the
question of which reference is measured against to the extraction,
normalization, and verification rules. Section 6.2 substantiates the rules
on five real documents. Section 6.3 reports the corpus result and the
remaining data situation.

### 6.1 Comparison Methodology Against the Reference TEIs

#### What the CER Measures and How It Is Defined Here

The CER is the share of characters in the reference text that deviate in the
produced text. It is defined as the Levenshtein distance between reference
and hypothesis, divided by the character count of the reference.

The Levenshtein distance is the minimal number of single-character
operations (insertion, deletion, substitution) needed to transfer the
hypothesis into the reference.[^11] These operations are not prescribed but
result from the distance computation. The transfer direction (hypothesis to
reference) is uniform throughout this chapter, so the naming of operation
types stays consistent across all examples; the distance itself is
direction-independent. It is implemented via
`rapidfuzz.distance.Levenshtein`.

The aggregation unit is the document, not the page. The corpus bootstrap
procedure (n = 25 reference TEIs, B = 10,000, seed 42, BCa confidence
interval) derives mean and 95% confidence range from it. For orientation the
Transkribus convention grades below 2% as publication-ready, 2 to 5% as
research-usable, and 5 to 10% as usable for full-text search.[^12] A high
CER does not necessarily mean poor text recognition; it can equally follow
from faulty reading order on complex layout[^13] or from Mistral Document AI
being a general model not specialized on historical type. The computation
itself is a single function call;[^14] the methodological substance lies in
the preparation of the two texts and in the choice of reference.

#### Which Reference Is Measured Against

The CER measures deviation from a chosen reference, not objective
correctness. With TEI ground truth it must therefore be fixed in advance
which reading forms the reference, for TEI keeps two competing versions of
the same text in several places. Two element pairs are relevant.
`<sic>`/`<corr>` marks a transmitted faulty form against an editorial
correction. `<abbr>`/`<expan>` marks an abbreviation against its expansion.
The difference is that `<expan>` contains text that never physically stood
on the source (the expansion of "Dr." to "Doctor"), while `<corr>` is a
plausible reading-text variant that usually differs from `<sic>` by only a
few characters.

The experiment measures against the edited, curated target version. With
`<sic>`/`<corr>` the corrected form `<corr>` is chosen (rule E3).

The element pair `<abbr>`/`<expan>` does not occur in the reference TEIs of
the corpus; their `<choice>` constructs are `<sic>`/`<corr>` throughout, so
only rule E3 applies to the comparison. `extract_text_for_comparison()`
contains no dedicated handling of this pair; a future occurrence would fall
under the generic rule E9 and would then need separate regulation.

This choice has a measurable consequence that example 5 in 6.2 shows: where
the reference itself contains a transcription error, a more correct
recognition counts as a difference. Such cases raise the measured CER, are
no pipeline error, and bound what this methodology can reach.

#### Decomposing Errors into Fidelity and Scope

The edit operations are decomposed into two categories that separate
different error causes. Fidelity captures real recognition errors, that is
substitutions, deletions, and small insertions, and forms the measure of
reading quality in the narrow sense. Scope captures large insertions from a
threshold of 50 characters, which typically stem not from recognition errors
but from text components the pipeline captures that the selectively
transcribed reference does not contain, such as mastheads, author lines, or
edition metadata. The fidelity CER evaluates only the first category; the
full-text CER includes the scope share as a diagnostic quantity. Both
categories sum character-exactly to the Levenshtein distance.

This assignment is confirmed at the code: `SCOPE_BLOCK_MIN = 50` in
`classify_edit_operations()`; substitutions, deletions, and insertions under
50 characters count toward fidelity, insertions of 50 characters and more
toward scope.

#### TEI Extraction

Before the comparison, a comparison text is produced from each TEI in
`extract_text_for_comparison()`. The same function processes both sides, the
reference TEI and the pipeline-produced TEI, so measured differences stem
exclusively from text content and not from unequal treatment of the sides.

| No. | Rule | Effect |
| :---- | :---- | :---- |
| E1 | XML parser via `xml.etree.ElementTree`, strip namespace prefixes | `{tei}p` becomes `p` |
| E2 | only content below `<body>` | `<teiHeader>`, `<front>`, `<back>` are ignored |
| E3 | `<choice><sic>X</sic><corr>Y</corr></choice>` yields only `<corr>` | the curated reading holds for spelling variants |
| E4 | `<choice>` without `<corr>`, only `<sic>` yields `<sic>` | fallback |
| E5 | `<note place="foot">...</note>` excluded (default) | separately edited footnotes would distort the running-text comparison; switchable via `include_footnotes=True` |
| E6 | `<lb/>` without `break="no"` yields one space | a print line break is a word boundary |
| E7 | `<lb break="no"/>` yields no character | a hyphenated word is joined (Hu + manismus becomes Humanismus) |
| E8 | `<pb/>` yields two line breaks `\n\n` | the page boundary stays recognizable |
| E9 | all remaining elements (`<hi>`, `<persName>`, `<bibl>`, `<title>`, `<head>`, `<p>`, `<div>` ...) yield inner text recursively | markup becomes transparent: `<hi>Wort</hi>` becomes Wort |
| E10 | attribute values are not taken over | page numbers from `<pb n="223"/>` and GND IDs from `ref` attributes do not appear in the comparison |
| E11 | XML tails are appended at the parent element | correct order for `<p>Wort1<hi>Wort2</hi>Wort3</p>` |
| E12 | on XML parse error, regex fallback `re.sub(r'<[^>]+>', '', content)` | secures the evaluation against single non-well-formed TEIs so one faulty file does not abort the corpus run |

#### Normalization

After extraction the text passes `normalize_for_comparison()`, likewise
identical on both sides. The rules unify typographic variants that are not
substantive differences.

| No. | Rule | Mapping |
| :---- | :---- | :---- |
| N1 / N2 | French guillemets to ASCII `"` | U+00AB, U+00BB |
| N3 | German low quotation mark to ASCII `"` | U+201E |
| N4 / N5 | single angle quotation marks to ASCII `'` | U+2039, U+203A |
| N6 / N7 | backtick, acute to ASCII `'` | U+0060, U+00B4 |
| N8-N12 | hyphen, non-breaking hyphen, en dash, em dash, figure dash to ASCII `-` | U+2010, U+2011, U+2013, U+2014, U+2012 |
| N13 | remove soft hyphen | U+00AD to '' |
| N14 | remove space before `; : ? !` (French typography) | `re.sub(r' +([;:?!])', r'\1', text)` |
| N15 | multiple whitespace to one space | `re.sub(r'\s+', ' ', text)` |
| N16-N19 | English quotation marks and apostrophes to ASCII `"` / `'` | U+201C, U+201D, U+2018, U+2019 |
| N20 | strip leading/trailing whitespace | `strip()` |
| N21 | Unicode normal form NFC | `unicodedata.normalize('NFC', text)` |

Deliberately not normalized are upper and lower case, diacritics,
punctuation, the distinction of ss and eszett, and numbers, since these are
substantive and not typographic differences. The case-sensitive default
follows the tool practice of dinglehopper[^15] and jiwer, which carry
lowercasing as opt-in; an optional case-insensitive secondary metric exists
(`casefold=True`). The preservation of accents is checked separately via its
own metric (HCPR).

#### Verification of the Measurement Methodology

This verification concerns the correctness of the CER measurement and is to
be distinguished from the TEI schema validation described in the validation
section. It rests on three layers. First, 18 hand-computed regression tests
(`tests/test_cer_extraction.py`) that pin the behavior independently of the
corpus result, among them the canonical formula, case sensitivity, the
absence of trimming, the `<choice>` resolution, the normalization, and the
decomposition into fidelity and scope including the character-exact sum
check. Second, the unification of the previously three separate CER
implementations (`benchmark_cer`, `cer_statistics_full`,
`tei_validator --compare-ref`) onto shared canonical functions since
decision E70, so all three paths yield the same number for the same
document. Third, the alignment of the conventions with external standards:
denominator as distance over reference length (Transkribus), NFC
normalization as the grapheme-cluster definition (OCR-D),[^16]
case-sensitive default (jiwer and general tool practice; OCR-D provides
case-ignoring only in a dedicated letter-accuracy metric), full-text
comparison without alignment trimming (dinglehopper),[^17] and the paired
bootstrap with BCa confidence interval for deltas (Du 2025).[^18] The
comparability of CER values between different tools remains limited even
under a nominally identical metric, among other reasons because already the
transformation of structured ground truth into comparison text becomes an
error source when reading order is not considered; the extraction and
normalization rules documented here are the project-internal fixation of
that transformation.

### 6.2 Five Examples from Different Document Types

Each example names document ID, layout type, and language, sets a reference
passage against the corresponding pipeline passage, identifies the
differences, points to the applicable rules, and classifies the local
effect.

#### Example 1, doc 130 (type A, French, journal article): title in capitals

Reference (`data/source/reference_tei/130.xml`):

```xml
<head>
  <title type="main">L'école de nos périls</title>
  <title type="sub">Le problème de l'élite ouvrière</title>
</head>
```

After extraction (E2, E6, E9): `L'école de nos périls Le problème de l'élite ouvrière`

OCR (`output/mistral_results/130_p3.md`): `L'ÉCOLE DE NOS PÉRILS LE PROBLÈME DE L'ÉLITE OUVRIÈRE`

The case-bearing letters differ throughout in capitalization and count as
substitutions; spaces and apostrophes stay equal. Capital setting is not
normalized (see 6.1), since it is a spelling variant. In the whole document
the effect dilutes: the title spans 54 characters, the full text roughly
33,000. The document CER stays in single digits.

#### Example 2, doc 1060 (type A, German): `<choice>` and Swiss versus German orthography

Reference (`data/source/reference_tei/1060.xml`):

```xml
<p>Wenn ich diesen Preis nicht <choice><sic>gnügend</sic><corr>genügend</corr></choice> verdient habe, ist er ...</p>
```

After extraction (E3, only `<corr>`): `Wenn ich diesen Preis nicht genügend verdient habe, ist er ...`

OCR (`output/mistral_results/1060_p3.md`): `Wenn ich diesen Preis nicht gnügend verdient habe, ist er ...`

Difference: "gnügend" against "genügend", one insertion of the e. Local CER
on the word: 1/8, about 12.5%. A second passage sets "Füssen" (reference,
Swiss orthography, 6 characters) against "Füßen" (OCR, German orthography, 5
characters); the distance is 2, one s replaced by eszett and the second s
deleted. Local CER: 2/6, about 33%. Rule E3 extracts the curated form
correctly; the ss/eszett difference is not normalized, being a substantive
orthographic difference.

#### Example 3, doc 2530 (type B, French, journal article): guillemets, dashes, French punctuation

Reference (`data/source/reference_tei/2530.xml`):

```xml
<p>... c'est Israël – ses habitants, et non pas moi – qui aura à les courir.</p>
```

After extraction and normalization (N10): `... c'est Israël - ses habitants, et non pas moi - qui aura à les courir.`

The OCR carries an em dash instead of the en dash; after N11 it is identical
to the reference, difference 0. A second passage concerns French colon
spacing: "un premier principe:" against "un premier principe :"; N14 removes
the space, difference 0 afterwards. A third passage, masthead and author
line (`LA SITUATION D'ISRAËL`, `JEANNE HERSCH`), spans roughly 35 characters
missing in the reference; being under the 50-character threshold they count
as fidelity insertions, not scope (local load roughly 35/2,800, about 1.2%).
N10/N11 and N14 eliminate typographic differences; edition metadata at the
page margin, by contrast, is measured as a real difference.

#### Example 4, doc 1330 (type D, French/German, monograph): transparent markup

Reference (`data/source/reference_tei/1330.xml`):

```xml
<p><persName ref="GND:118583530">Jacques Monod</persName>, par exemple, a publié un livre célèbre,
   et que je trouve admi<lb break="no"/>rable, intitulé
   <bibl ref="GND:4678418-4"><hi rendition="#i">Le hasard et la nécessité</hi></bibl>.</p>
```

After extraction (E7 joins admirable, E9 keeps only the inner text, E10
ignores the `ref` attribute): `Jacques Monod, par exemple, a publié un livre
célèbre, et que je trouve admirable, intitulé Le hasard et la nécessité.`

The OCR text before TEI generation is identical but carries Markdown
asterisks around the book title (`*Le hasard et la nécessité*`), two
insertions. In the end-to-end comparison (pipeline TEI against reference
TEI) `*Titel*` becomes `<hi rendition="#i">Titel</hi>`, which E9 removes on
both sides; the texts are then identical, difference 0. The pipeline may
realize typographic markup freely (`*...*` versus `<hi>...</hi>`) without a
CER penalty; GND identifiers in `ref` attributes are untouched by the
comparison (E10).

#### Example 5, doc 1440 (type B, German, monograph): a faulty reference

Reference (`data/source/reference_tei/1440.xml`):

```xml
<p>... 25. Kongreß der KPdSU, 5. Februar 1976, "lnforma<lb break="no"/>tionsbulletin" Nr. 6/7, 1976, Wien.</p>
```

After extraction (E7): `... 25. Kongreß der KPdSU, 5. Februar 1976,
"lnformationsbulletin" Nr. 6/7, 1976, Wien.` The reference contains a
lowercase l instead of a capital I in "lnformationsbulletin", an uncorrected
confusion of small l and capital I in the Transkribus reference.

The OCR delivers guillemets and the correct "Informationsbulletin". After
N1/N2 the quotation marks are equal; what remains is "lnformationsbulletin"
against "Informationsbulletin", one substitution l to I. Local CER on the
word: 1/20, that is 5%, counted against the pipeline although it delivers
the correct form here (assumption: the proper name reads
"Informationsbulletin"; marked inference, high confidence). The example
shows that the CER measures difference from the reference, not objective
correctness; the reference is ground truth by definition but itself a
fallible transcription. Such cases raise the measured CER without being a
pipeline failure and bound what is reachable.

### 6.3 Corpus Result and Data Situation

Headline result of the current corpus (n = 25, seed 42, B = 10,000, state of
the 2026-06-08 statistics run, reproducible via
`python -m scripts.eval.cer_statistics_full --seed 42 --bootstrap-n 10000`):

| Metric | Mean | Median | 95% CI (mean) | Measures |
| :---- | ----: | ----: | :---- | :---- |
| fidelity CER (primary) | 2.71% | 1.40% | [1.77%, 3.82%] | real OCR and transcription fidelity (micro average 2.13%) |
| full-text CER (diagnosis) | 18.94% | 12.13% | [10.26%, 30.09%] | full divergence including surplus text; no quality measure |
| scope rate (surplus text) | 16.23% | 7.06% | | pipeline text beyond the selective reference; no error |

These values are to be read print-calibrated: the Transkribus quality bands
(under 2% publication-ready, 2 to 5% research-usable) stem primarily from
handwriting recognition practice and flatter a pure print OCR task where the
bar sits higher. Decisive is therefore the comparison with the print OCR
literature below: the fidelity median of 1.40% lies between the best
specialized print stack (Transkribus with LLM post-correction, 0.84%;
Crosilla et al. 2025) and Transkribus alone (3.67%), solid for historical
print but not at the top; the technical optimum is reached only by the best
individual documents (0.3 to 0.8%). In addition the CER measures against a
Transkribus reference that is itself fallible (example 5, doc 1440) and is
therefore an upper bound of the true error rate.

The independent counter-check of 2026-07-03 (E91 in
[decisions.md](decisions.md)) concretized this upper-bound character with two
cause classes. Apparatus insertions under 50 characters, such as running
titles, page numbers, and imprint lines, are transcribed faithfully by the
pipeline but omitted by the selective reference, so they count toward
fidelity although no recognition error occurred. The reference also
normalizes capitalized titles to lowercase (doc 100, facsimile-verified),
which penalizes the rendering of the pipeline that stays closer to the
printed image. Genuine text loss is the exception across the corpus; the
true character recognition performance therefore lies below the cited
values.

The end-to-end pipeline beats raw Mistral OCR by 9.45 percentage points of
fidelity CER (paired bootstrap, p = 0.013, n = 25, significant at alpha =
0.05). An earlier figure of -14.83 pp (p = 0.0004) was an artifact of the
old trimmed, lowercased comparison and is retracted.

An independent counter-check (2026-07-03) reproduced every headline and
per-document value of this section exactly, without importing any repo code
(extraction re-implemented from the specification, python-Levenshtein as a
second engine, own aggregation, secondary metrics, facsimile spot checks).
Details and measured values are in
[cer-gegenprobe-2026-07-03.md](../reports/cer-gegenprobe-2026-07-03.md); the
counter-check scripts live in the paper repo (DHCraft/promptotyping-paper,
`verification/`). See E91 in [decisions.md](decisions.md).

Two corrections shaped the current state. First, a duplicated OCR text
block in document 30 was removed manually, lowering its fidelity CER from
18.25% to 11.59%; an automatic block deduplication does not exist in the
pipeline, so this one correction is manual while the remaining 24 documents
are pure pipeline output. Second, a reference-verified footnote demotion
(2026-06-08): five documents carried running text wrongly as
`<note place="foot">` (Gemini layout QA over-detects footnote regions);
since the comparison excludes footnotes (rule E5), this text counted as
deletions and inflated their CER. Verified against the ZBZ reference (the
text stands in its body there), the blocks were demoted to `<p>`,
evidence-based rather than guessed; the discriminator is that a footnote
counts as verified running text when a contiguous run of at least 150
characters of its text occurs in the body of the reference (`MIN_MATCH` in
`tei_footnote_demote.py`). Beyond the five demoted documents, 6 candidates were
held back as reference-verified genuine footnotes, 11 remain for manual
checking, and 1 is a page number.

| Doc | Blocks | Fidelity before | after |
| :---- | :---- | ----: | ----: |
| 290 | 2 | 17.7% | 2.6% |
| 1910 | 1 | 16.4% | 7.7% |
| 90 | 1 | 7.6% | 1.4% |
| 40 | 1 | 1.6% | 1.2% |
| 1520 | 9 | 3.6% | 2.1% |

The following table breaks all 25 measured documents down by fidelity CER
and assigns each elevated value its main cause. It substantiates that the
spread does not stem from character recognition but from three structural
patterns: surplus text against selective references (scope, no error),
misclassification of running text as footnote (fixed for the demoted
documents), and scrambled reading order on double pages. The documents
marked clean show the recognition quality on simple layout with a complete
reference. The full three-number decomposition per document is in
`docs/data/cer_statistics.json`.

| Doc | Type | Lang | Fidelity % | Main cause |
| :---- | :---- | :---- | ----: | :---- |
| 30 | A | FR | 11.59 | double page: genuine text loss, counter-check-verified; reordering alone does not recover it (E91) |
| 1910 | B | DE | 7.70 | residue after footnote demotion + scope |
| 760 | D | FR | 5.87 | double page: lost picture captions and unsegmented pagination, counter-check-verified (E91); reading order itself holds at the facsimile |
| 1440 | B | DE | 5.87 | scope + faulty reference |
| 300 | D | FR | 5.05 | scope + extra pages |
| 1410 | B | FR | 4.24 | scope + extra pages |
| 130 | A | FR | 2.94 | nearly clean |
| 560 | A | FR | 2.61 | clean |
| 290 | A | FR | 2.60 | fixed by footnote demotion |
| 2310 | A | FR | 2.46 | scope (JSTOR cover) |
| 1520 | C | FR | 2.10 | extra pages; footnote demotion applied |
| 2530 | B | FR | 1.83 | clean |
| 90 | A | DE | 1.40 | fixed by footnote demotion |
| 890 | B | DE | 1.37 | scope |
| 40 | C | FR | 1.20 | clean; footnote demotion applied |
| 1060 | A | DE | 1.14 | scope |
| 1180 | A | FR | 1.12 | clean |
| 3040 | B | FR | 1.09 | scope (footnotes) |
| 3020 | B | DE | 1.06 | clean |
| 1330 | D | FR | 1.03 | scope |
| 570 | A | FR | 0.93 | scope (extreme) |
| 100 | A | FR | 0.85 | clean |
| 2635 | A | DE | 0.76 | clean |
| 830 | D | FR | 0.75 | clean |
| 580 | A | FR | 0.30 | scope (extreme) |

For the 260 documents without ground truth, the dictionary hit rate serves
as a proxy (share of OCR words found in FR/DE dictionaries, after Stroebel
et al. 2022): median 97.7%, with 92% of the documents at or above 90% hit
rate; the outliers below 75% are correctly classified foreign-language
documents. The proxy's composite estimator does not generalize (negative
LOOCV R^2), so the corpus-wide figure is a plausibility bound, not a
measurement. A side finding of the language audit: 284 of 285 documents were
correctly language-classified; three labels were corrected.

Comparison with the state of research on printed historical documents:

| Source | Method | Language | CER |
| :---- | :---- | :---- | :---- |
| Crosilla et al. 2025 | Transkribus Print M1 + Gemini 2.0 Flash post-correction | deu (Fraktur) | 0.84% |
| Crosilla et al. 2025 | Gemini 2.0 Flash zero-shot | deu | 1.27% |
| Crosilla et al. 2025 | Transkribus Print M1 alone | deu | 3.67% |
| Crosilla et al. 2025 | GPT-4o direct | deu | 6.31% |
| Levchenko 2025 | Gemini 2.5 Pro | rus (18th c.) | 3.36% |
| Levchenko 2025 | Gemini 2.5 Flash | rus | 4.94% |
| Levchenko 2025 | traditional OCR | rus | 21-45% |
| Transkribus documentation | guide value | general | 0.5-2% |

Known limitations of the measurement, disclosed with the values: ground
truth exists for 25 documents only, so corpus statements are estimates; the
reference subset deviates significantly in character volume
(Kolmogorov-Smirnov p = 0.041, disclosed in the JSON); the four
normalization regimes differ little because the comparison pipeline already
normalizes symmetrically; the run-to-run variance of the non-deterministic
LLM stages is not yet quantified (the stability measurement, 5 documents
times 3 runs, is released and executes at the workstation); the HCPR
adaption is frequency-based and underestimates substitutions.

On the data side it remains on record that of the 286 delivered documents,
285 possess a final TEI. The delivered PDF without a final TEI (document 10)
is registered and to be clarified externally. To be distinguished from it
are three texts listed in the master file but not delivered (1745, 1750,
1970) and the still open difference between the master-file texts and the
publicly named ZB texts.

## 7. Reading Order: Diagnosis and Prepared Rollout (E90)

The one substantive pipeline defect still visible in the delivered TEI is
the reading order on two-column and double-page layouts: the assembly
sorted regions by vertical position alone, so columns interleave. The fix is
built and test-covered (a column- and band-aware permutation: full-width
blocks form horizontal bands, columns split at a gap of more than 12% of
the x-center spread), and the validator warning W19 scopes the legacy
deviations. The triage (`reading_order_audit`, state 2026-07-07) marks 831
affected pages in 216 documents, of which 557 are robustly auto-correctable
and 274 fragile; the reversible corpus-wide preview
(`tei_reassemble_preview`, report in `reports/m3-reassemble-preview.md`)
reduces the flagged pages from 831 to 39, setting 188 documents to zero. Of
the 39 residual pages, 35 are OCR/layout count mismatches and 4 are column
edge cases; both classes need facsimile review. Rewriting the delivered
corpus is operator-gated (M3) and executes at the workstation, since the
full data set lives only there.

## 8. Limits and Possible Continuation

Several aspects remained incomplete or were deliberately left aside. The
following table gathers the problems identified in the project compactly in
one place, with per-finding status.

| # | Problem | Affected | Cause | Status |
| :---- | :---- | :---- | :---- | :---- |
| 1 | OCR duplication (a text block captured twice) | doc 30 | Mistral repeated a paragraph | fixed manually (fidelity 18.25 to 11.59%); no automatic deduplication stage exists |
| 2 | scrambled reading order on double pages and columns | W19 worklist, prominently 30, 760 | landscape scans and column layouts; the old assembly sorted by y position only | fix built and previewed (E90); corpus rollout operator-gated (M3), residue of 39 pages to facsimile review (section 7) |
| 3 | running text wrongly marked as footnote | 290, 1910, 90, 40, 1520 | Gemini layout QA over-detects footnote regions; the text falls out of the fidelity comparison (rule E5) | largely fixed by reference-verified demotion (2026-06-08); 11 candidates remain for manual checking; an automatic demote stays unsafe because genuine long footnotes exist |
| 4 | scope: surplus text against selective references | for example 570, 580, 2310, 300, 3040 | the reference TEIs are partial transcriptions; the pipeline additionally captures covers, front matter, neighboring articles | no defect; disclosed as a diagnostic quantity via the fidelity/scope separation |
| 5 | faulty reference | 1440 | the Transkribus ground truth itself contains a transcription error; the more correct pipeline is penalized | not fixable (ground truth by definition; example 5) |
| 6 | CER thresholds HTR-calibrated | methodology | the Transkribus quality bands stem from handwriting recognition and flatter a print OCR task | fixed (print-calibrated framing; comparison with print OCR literature) |
| 7 | header schema defect in `<idno>` | final TEIs | the ODD subset had omitted standard TEI header elements | fixed (schema extension E68; delivery contract test-gated, E69) |

Beyond that, open or deliberately left aside:

- Semantic enrichment via named entity recognition and linking was
  implemented and then removed (E71): only a small fraction of tagged
  mentions carried a real GND ID, so the linking, the actual editorial
  value, was not deliverable. The delivered TEI is entity-free; the ZBZ
  material decides for inline GND markup at the point of mention (E88), and
  the entity gate turns sharp on curated teiCrafter output.
- Header enrichment from Alma (project ID, MMSID, publication form) is ZBZ
  domain (E76, open item O8); most delivered headers therefore carry an
  empty container title.
- The run-to-run stability of the non-deterministic LLM stages is not yet
  quantified; the measurement is released and executes at the workstation.
- The dictionary-hit-rate proxy does not generalize statistically (LOOCV
  R^2 below 0) and stays a plausibility bound.
- On the data side, the three undelivered texts (1745, 1750, 1970), the
  delivered PDF without final TEI (10), and the difference between
  master-file texts and the publicly named ZB texts remain to be clarified
  externally.
- The round trip from viewer edit back into the pipeline is documented but
  not automated in a wrapper script; it rests on convention rather than
  mechanism.
- The TEI handover to teiCrafter for control and inline-GND annotation is
  prepared (test plan of June 2026); it awaits the teiCrafter output-model
  switch from standOff to inline GND.

## Appendix A: Pipeline Scripts

Invoked as modules (`python -m scripts.<package>.<module>`). The complete
inventory with one-line descriptions is `scripts/README.md`.

From scan to page image:

- `scripts/edition/extract_pages.py` splits the PDF scans page by page into
  PNG images that serve both as facsimile and as input for text recognition
  and layout.

Text recognition:

- `scripts/ocr/ocr_pipeline.py` steers text recognition and calls Mistral
  (base engine) or Gemini (opt-in) per document; Docling contributes layout
  only, no text (E75).
- `scripts/ocr/gemini_ocr_correct.py` supplies replacement and correction
  OCR with Gemini in two variants, text-only or additionally with the scan
  image.
- `scripts/ocr/llm_postprocess.py` optionally post-corrects the OCR text
  with Claude Haiku.
- `scripts/ocr/classify_docs.py` derives the document metadata such as
  language, type, title, author, and date from the first pages via Gemini.
- `scripts/core/loaders.py` fixes which OCR stream takes precedence and
  determines the pages to process.

Layout analysis:

- `scripts/layout/run_layout_analysis.py` runs Docling locally on the page
  images and writes one layout JSON per page.
- `scripts/layout/run_layout_cloud.py` performs the same layout analysis
  via a docling-serve instance instead of locally.
- `scripts/layout/layout_qa_gemini.py` corrects the layout (QA), recognizes
  it anew (Detect), or decides automatically per page between the two
  (Auto), each with Gemini.
- `scripts/layout/generate_layout_overlays.py` draws the recognized regions
  onto the scans for visual checking, on request as a Docling-versus-Gemini
  comparison.

Interchange formats:

- `scripts/layout/page_xml_generator.py` produces PAGE-XML (schema version
  2013-07-15) from layout JSON and OCR Markdown.
- `scripts/layout/mets_generator.py` produces the associated METS manifest
  and is co-invoked by the PAGE-XML generator.
- `scripts/edition/transkribus_export.py` and
  `scripts/edition/transkribus_upload.py` bundle the PAGE-XML for the
  Transkribus round trip and upload it via REST.

TEI generation:

- `scripts/tei/tei_unified.py` orchestrates the TEI stages, scaffold,
  refinement, assembly, and validation.
- `scripts/tei/tei_step1.py` builds the rule-based deterministic TEI
  scaffold from text and layout and sorts the page regions by the canonical
  column- and band-aware reading-order permutation (E90).
- `scripts/tei/tei_step2.py` refines the scaffold multimodally with Gemini
  and then cleans up frequent model errors.
- `scripts/tei/tei_step3.py` joins the page fragments into the whole
  document, header, facsimile, and body, and applies document-wide
  corrections and conformity passes (div merge, figure IDs, title-main,
  foreign-language normalization).
- `scripts/tei/tei_generator.py`, `scripts/tei/tei_mapping_prompt.py`, and
  `scripts/tei/tei_xml_utils.py` supply shared building blocks, the
  Markdown-to-TEI conversion, the mapping table for the Gemini prompt, and
  the XML helpers.
- `scripts/tei/tei_footnote_demote.py` demotes reference-verified footnote
  blocks to paragraphs (section 6.3);
  `scripts/tei/tei_footnote_marker_strip.py` strips leading footnote
  markers from notes, keeping the number in `@n` only.
- `scripts/tei/tei_surface_graphic.py` writes the page image reference as
  `<graphic>` into every facsimile surface (E89);
  `scripts/tei/pb_split.py` holds the shared page-segmentation rule (page =
  sequential `<pb>` position).

Validation and evaluation:

- `scripts/tei/tei_validator.py` validates against the RelaxNG schema and
  the project rules and additionally reports informative warnings.
- `scripts/tei/zbz_conformity.py` checks the guideline rules Z1-Z8 beyond
  the schema.
- `scripts/eval/benchmark_cer.py`, `scripts/eval/cer_statistics_full.py`,
  and `scripts/eval/evaluate_ocr.py` compute the CER metrics of section 6.
- `scripts/eval/quality_proxy.py` computes the dictionary hit rate proxy.
- `scripts/eval/structure_audit.py` compares pipeline TEI structure against
  the ground truth (diagnosis, no gate).
- `scripts/eval/reading_order_audit.py` triages the W19 pages
  robust/fragile; `scripts/tei/tei_reassemble_preview.py` produces the
  reversible M3 preview (section 7).
- `scripts/eval/corpus_audit.py` derives the corpus figures reproducibly
  from the primary sources and flags deviations from the knowledge base.

Processing status:

- `scripts/edition/page_manifest.py` produces the per-object manifest with
  workflow status and processing history per data stream and marks safe
  blank pages.
- `scripts/tei/tei_status_marker.py` projects the processing history as
  `<change>` into the revision description at ZB handover and removes the
  misleading agent-screening entries in doing so.
- `scripts/tei/tei_blank_marker.py` transfers the recognized blank pages as
  `<pb type="blank"/>` into the final TEI.

Frontend data:

- `scripts/edition/generate_edition_data.py` produces the catalog, the
  search index, the thumbnails, and the per-page mirror under `docs/data/`.

## Appendix B: Ground-Truth Map and Known Reference Deviations

All 25 reference TEIs (`data/source/reference_tei/`) were read in full against
the editorial guidelines on 2026-07-07 (three parallel readers). This appendix
records which guideline phenomenon is attested where and which known deviations
every reference-based check (CER benchmark, `structure_audit`, `--compare-ref`)
must treat as expected rather than as pipeline error.

Concordance finding. The body coding of the references follows the guidelines
in the load-bearing conventions (genre div types, page breaks with bracketed
supplied numbers, hyphenation including the page-break rule, the footnote ID
scheme `fn{page}-{no}`, the inline GND entity model, the rendition
vocabulary). Two restrictions hold corpus-wide: no reference fulfils the
header requirement (all carry the raw Transkribus export stub instead of the
ALMA citation with MMSID and publication form, so header comparisons against
the references are meaningless), and all carry the undocumented root attribute
`type="naegeli"`. The subfolder `Pilot/` is a superseded precursor; the main
set emerged from it by migrating work references from `corresp="GND:…"` to
`ref="GND:…"`, with document 560 as the overlooked migration rest.

Phenomenon map (best exemplars):

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

Never attested in the ground truth and therefore not validatable against it:
marginalia (`note place="right/left"`), multi-page footnotes with
`@next`/`@prev`, `unclear`, `gap`, the div types `conversation` and
`dedication`, the renditions `#sub` and `#k`. For these only the guideline
itself applies.

Known deviations of the ground truth (the exception catalog):

1. Header stub instead of ALMA header, all 25 (see above).
2. Root `type="naegeli"`, all 25; in 2310 with a whitespace defect.
3. Foreign-language practice split between document groups: correct
   `foreign xml:lang` in one group (300, 2635, 3020, 90), italics-only
   marking in another (1060, 1180, 1520); 1910 carries the literal
   placeholder `xml:lang="[fre]"`.
4. `break="yes"` as an undocumented, partly wrong value (1060, 1330, 2530,
   30, 3040, 890).
5. Only `rendition="#i"` is broadly realized; `#u`/`#b`/`#g`/`#sup` occur in
   one document each, `#sub`/`#k` never.
6. `rend="italic"`/`"bold"`/`"superscript"` instead of `rendition="#…"`:
   2530, 1180 (mixed within one paragraph), 1410, 3040.
7. GND references without the `GND:` prefix: 290, 1330, 1520, 3040 (there
   also one persName without any `ref`); `corresp` instead of `ref` on work
   `bibl`: 100, 30, 560.
8. Adjectivized person names tagged against the guideline's own rule: 1910.
9. One footnote without `xml:id` beside correctly tagged siblings: 290.
10. Entities inside picture captions despite the explicit ban: 760
    (systematic).
11. Data hygiene singletons: doubled uncorrected `choice` text (1910),
    trailing slash in `graphic` URLs (760, 2635, 830), a line-region ID as
    page `facs` (830), whitespace in a page number (560), `@n` on `p`
    instead of `lb` (90), `pb` without `facs` (1910, 3020), `pb` inside a
    paragraph (1060, 1440), lowercase line numbering with leading space
    (130), author credit in the text body (1410).
12. 3020 types a panel discussion as `interview` where the guideline
    reserves `conversation`; spoken exchange is coded as `sp` in 3020 but as
    a dash `list` in 300.

Reference 1520 is not well-formed: three structurally identical crossed
`item`/`p` nestings (around lines 6936, 6979, 6995; the parser reveals them
only one at a time). The repair swaps the closing-tag order to
`</p></item>` at each spot, leaving the text content unchanged; the corrected
copy `output/1520_reference_fixed.xml` parses cleanly. The original stays
untouched as ZBZ source datum; the correction goes to ZBZ as a proposal, and
after adoption the document returns to the 25-document benchmark.

Consequences. Reference-based checks measure against a ground truth that is
guideline-true in the body, empty in the header, and locally flawed; the
exception catalog above belongs in every scoring logic. The phenomena the
ground truth never shows can only be checked against guideline plus
facsimile. The GND prefix and `corresp`/`ref` drift matters for future
entity work (teiCrafter lane): the reference practice serves as a model only
after normalization.

[^1]: Zentralbibliothek Zurich. "Jeanne Hersch: Digitale Neuauflage der Schriften". [https://www.zb.uzh.ch/de/jeanne-hersch-digitale-neuauflage-der-schriften](https://www.zb.uzh.ch/de/jeanne-hersch-digitale-neuauflage-der-schriften).

[^2]: Deutsches Textarchiv. "DTA-Basisformat". [https://www.deutschestextarchiv.de/doku/basisformat](https://www.deutschestextarchiv.de/doku/basisformat).

[^3]: Pollin, Christopher. "Promptotyping: Zwischen Vibe Coding, Vibe Research und Context Engineering". L.I.S.A. Wissenschaftsportal Gerda Henkel Stiftung, 2026-01-17. [https://lisa.gerda-henkel-stiftung.de/digitale_geschichte_pollin](https://lisa.gerda-henkel-stiftung.de/digitale_geschichte_pollin).

[^4]: Claude Code, documentation. [https://code.claude.com/docs/en/overview](https://code.claude.com/docs/en/overview).

[^5]: Repository: [https://github.com/chpollin/zbz-ocr-tei](https://github.com/chpollin/zbz-ocr-tei).

[^6]: Mistral AI. "Document AI" (OCR and document processing API). [https://mistral.ai/news/mistral-ocr](https://mistral.ai/news/mistral-ocr).

[^7]: Livathinos, Nikolaos, Christoph Auer, Maksym Lysak et al. "Docling: An Efficient Open-Source Toolkit for AI-driven Document Conversion". IBM Research, arXiv:2501.17887, 2025. [https://arxiv.org/abs/2501.17887](https://arxiv.org/abs/2501.17887). Software: [https://github.com/docling-project/docling](https://github.com/docling-project/docling).

[^8]: PAGE (Page Analysis and Ground-truth Elements), schema version 2013-07-15. Specification: Pletschacher, Stefan and Apostolos Antonacopoulos. "The PAGE (Page Analysis and Ground-Truth Elements) Format Framework". Proceedings of the 20th International Conference on Pattern Recognition (ICPR), 2010, pp. 257-260. PRImA Research Lab: [https://www.primaresearch.org/tools/PAGELibraries](https://www.primaresearch.org/tools/PAGELibraries).

[^9]: Metadata Encoding and Transmission Standard (METS). Library of Congress, Network Development and MARC Standards Office. [https://www.loc.gov/standards/mets/](https://www.loc.gov/standards/mets/).

[^10]: OpenSeadragon, open-source viewer for high-resolution zoomable images, version 5.0.1. [https://openseadragon.github.io/](https://openseadragon.github.io/).

[^11]: Transkribus, "Character Error Rate (CER) Explained". [https://www.transkribus.org/character-error-rate-cer-explained](https://www.transkribus.org/character-error-rate-cer-explained).

[^12]: Transkribus, "Character Error Rate (CER) Explained", evaluation thresholds. Same URL as note 11.

[^13]: Transkribus, "Character Error Rate (CER) Explained", layout complexity as a CER factor. Same URL as note 11.

[^14]: jiwer. [https://github.com/jitsi/jiwer](https://github.com/jitsi/jiwer) (function interface for CER computation).

[^15]: dinglehopper, OCR evaluation tool of the OCR-D initiative. [https://github.com/qurator-spk/dinglehopper](https://github.com/qurator-spk/dinglehopper).

[^16]: OCR-D, "Quality Assurance in OCR-D: Metrics". [https://ocr-d.de/en/spec/ocrd_eval.html](https://ocr-d.de/en/spec/ocrd_eval.html).

[^17]: dinglehopper. Same URL as note 15.

[^18]: Du, W. 2025, "When +1% Is Not Enough: A Paired Bootstrap Protocol for Evaluating Small Improvements". arXiv:2511.19794. Basis of the paired-bootstrap protocol; further methodological sources: Levchenko 2025, arXiv:2510.06743 (HCPR); Crosilla, Klic, Colavizza 2025, arXiv:2503.15195 (LLM-HTR benchmarks); Kanerva and Ledins 2025, arXiv:2502.01205 (language dependence of LLM post-correction).
