---
title: CER Measurement Methodology
type: knowledge
project:
  name: zbz-ocr-tei
  repository: https://github.com/chpollin/zbz-ocr-tei.git
method:
  name: Promptotyping
  url: https://dhcraft.org/Promptotyping/
status: reviewed
language: en
created: 2026-07-07
updated: 2026-08-21
tags: [zbz-ocr-tei, cer, methodology, evaluation]
related: [specification, ground-truth-map, literature-comparison, decisions]
authors: [Christopher Pollin]
---

# CER Measurement Methodology

Reference document for the character error rate (CER) measurement of the pipeline
against the 25 manually created reference TEIs. It fixes the definition of the
measure, the choice of reference, the fidelity/scope decomposition, and the
extraction and normalization rules that turn structured TEI into comparison text.
The consolidated requirement view is in [specification.md](specification.md),
quality-measurement section; the measured values live in
`docs/data/cer_statistics.json` (deterministically regenerable, seed 42) and are
reported in `arbeitsbericht-v3.md`, section 6.3. This document carries the
detailed method behind those values.

## What the CER Measures and How It Is Defined Here

The CER is the share of characters in the reference text that deviate in the
produced text. It is defined as the Levenshtein distance between reference and
hypothesis, divided by the character count of the reference.

The Levenshtein distance is the minimal number of single-character operations
(insertion, deletion, substitution) needed to transfer the hypothesis into the
reference. These operations are not prescribed but result from the distance
computation. The transfer direction (hypothesis to reference) is uniform
throughout, so the naming of operation types stays consistent across all
examples; the distance itself is direction-independent. It is implemented via
`rapidfuzz.distance.Levenshtein`.

The aggregation unit is the document, not the page. The corpus bootstrap
procedure (n = 25 reference TEIs, B = 10,000, seed 42, document-level percentile
bootstrap) derives mean and 95% confidence range from it; the interval method is
stated exactly in the verification section below. For orientation the Transkribus
convention grades below 2% as publication-ready, 2 to 5% as research-usable, and
5 to 10% as usable for full-text search. A high CER does not necessarily mean
poor text recognition; it can equally follow from faulty reading order on complex
layout or from Mistral Document AI being a general model not specialized on
historical type. The computation itself is a single function call; the
methodological substance lies in the preparation of the two texts and in the
choice of reference.

## Which Reference Is Measured Against

The CER measures deviation from a chosen reference, not objective correctness.
With TEI ground truth it must therefore be fixed in advance which reading forms
the reference, for TEI keeps two competing versions of the same text in several
places. Two element pairs are relevant. `<sic>`/`<corr>` marks a transmitted
faulty form against an editorial correction. `<abbr>`/`<expan>` marks an
abbreviation against its expansion. The difference is that `<expan>` contains
text that never physically stood on the source (the expansion of "Dr." to
"Doctor"), while `<corr>` is a plausible reading-text variant that usually differs
from `<sic>` by only a few characters.

The experiment measures against the edited, curated target version. With
`<sic>`/`<corr>` the corrected form `<corr>` is chosen (rule E3).

The element pair `<abbr>`/`<expan>` does not occur in the reference TEIs of the
corpus; their `<choice>` constructs are `<sic>`/`<corr>` throughout, so only rule
E3 applies to the comparison. `extract_text_for_comparison()` contains no
dedicated handling of this pair; a future occurrence would fall under the generic
rule E9 and would then need separate regulation.

This choice has a measurable consequence: where the reference itself contains a
transcription error, a more correct recognition counts as a difference. Such
cases raise the measured CER, are no pipeline error, and bound what this
methodology can reach. The known reference defects are catalogued in
[ground-truth-map.md](ground-truth-map.md).

## Decomposing Errors into Fidelity and Scope

The edit operations are decomposed into two categories that separate different
error causes. Fidelity captures real recognition errors, that is substitutions,
deletions, and small insertions, and forms the measure of reading quality in the
narrow sense. Scope captures large insertions from a threshold of 50 characters,
which typically stem not from recognition errors but from text components the
pipeline captures that the selectively transcribed reference does not contain,
such as mastheads, author lines, or edition metadata. The fidelity CER evaluates
only the first category; the full-text CER includes the scope share as a
diagnostic quantity. Both categories sum character-exactly to the Levenshtein
distance.

This assignment is confirmed at the code: `SCOPE_BLOCK_MIN = 50` in
`classify_edit_operations()`; substitutions, deletions, and insertions under 50
characters count toward fidelity, insertions of 50 characters and more toward
scope. Because the fidelity values depend on this threshold, every citation names
the threshold with them, a rule that arose from the independent counter-check.

## TEI Extraction

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

## Normalization

After extraction the text passes `normalize_for_comparison()`, likewise identical
on both sides. The rules unify typographic variants that are not substantive
differences.

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

Deliberately not normalized are upper and lower case, diacritics, punctuation, the
distinction of ss and eszett, and numbers, since these are substantive and not
typographic differences. The case-sensitive default follows the tool practice of
dinglehopper and jiwer, which carry lowercasing as opt-in; an optional
case-insensitive secondary metric exists (`casefold=True`). The preservation of
accents is checked separately via its own metric (HCPR).

## Verification of the Measurement Methodology

This verification concerns the correctness of the CER measurement and is to be
distinguished from the TEI schema validation. It rests on four layers.

First, the hand-computed regression tests in `tests/test_cer_extraction.py`, which pin
the behavior independently of the corpus result, among them the canonical formula,
case sensitivity, the absence of trimming, the `<choice>` resolution, the
normalization, and the decomposition into fidelity and scope including the
character-exact sum check.

Second, the unification of the previously three separate CER implementations
(`benchmark_cer`, `cer_statistics_full`, `tei_validator --compare-ref`) onto
shared canonical functions since decision E70, so all three paths yield the same
number for the same document.

Third, the alignment of the conventions with external standards: denominator as
distance over reference length (Transkribus), NFC normalization as the
grapheme-cluster definition (OCR-D), case-sensitive default (jiwer and general
tool practice; OCR-D provides case-ignoring only in a dedicated letter-accuracy
metric), full-text comparison without alignment trimming (dinglehopper), and the
paired bootstrap with confidence interval for deltas (Du 2025).

Fourth, an independent counter-check of 2026-07-03 that reproduced every headline
and per-document value without importing any repo code (extraction re-implemented
from the specification, python-Levenshtein as a second engine, own aggregation,
secondary metrics, facsimile spot checks). Details in
`reports/cer-gegenprobe-2026-07-03.md`; see E91 in [decisions.md](decisions.md).

The interval method behind the published values is the document-level block percentile
bootstrap. `cer_statistics_full.py` resamples documents with replacement, one value per
document so the block is the document, with B = 10,000 and seed 42, and reads the 2.5th and
97.5th percentile of the resampled means and medians (`doc_level_bootstrap`, `_agg_block`);
every aggregate in `docs/data/cer_statistics.json` names this in its own `ci_method` field.
The paired comparison of the end-to-end pipeline against OCR-only runs on the per-document
differences of the fidelity CER, which keeps both sides scope-neutral, and reports the mean
difference, a percentile interval and a two-sided bootstrap p-value taken as the share of
resamples that change sign (`paired_bootstrap_diff` in `cer_statistics.py`,
`build_paired_test` in `cer_statistics_full.py`). One label contradicts this. The library
`cer_statistics.py` carries a BCa implementation `bca_ci` with its own tests and calls it in
its own aggregation functions `aggregate_overall` and `aggregate_strata`, which the
published pipeline does not use; the generator of the published statistics,
`cer_statistics_full.py`, never calls it, so the computed intervals are percentile
intervals throughout. The field `meta.bootstrap_method` of the published JSON still claims
BCa; that label is stale, and whether the generator moves to BCa or the label moves to
percentile is an open operator decision recorded in the register (E120).

The comparability of CER values between different tools remains limited even under
a nominally identical metric, among other reasons because already the
transformation of structured ground truth into comparison text becomes an error
source when reading order is not considered; the extraction and normalization
rules documented here are the project-internal fixation of that transformation.

## Related

- [specification.md](specification.md): the consolidated quality-measurement requirement
- [ground-truth-map.md](ground-truth-map.md): the reference defects that bound the measurement
- [literature-comparison.md](literature-comparison.md): where the fidelity CER sits in the print-OCR state of research
- [decisions.md](decisions.md): dated provenance (E70, E73, E80, E85, E91)
