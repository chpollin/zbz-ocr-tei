---
title: CER Measurement Methodology
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
status: reviewed
language: en
version: 1.0
created: 2026-07-07
updated: 2026-08-21
authors: [Christopher Pollin]
related: [specification, data, verification, decisions, testing]
---

# CER Measurement Methodology

Reference document for the character error rate (CER) measurement of the pipeline
against the 25 manually created reference TEIs. It fixes the definition of the
measure, the choice of reference, the fidelity/scope decomposition, and the
extraction and normalization rules that turn structured TEI into comparison text.
It also places the resulting values in the print-OCR state of
research. The consolidated requirement view is in
[specification.md](specification.md), quality-measurement section; the measured
values live in `docs/data/cer_statistics.json` (deterministically regenerable,
seed 42) and are reported in `arbeitsbericht-v3.md`, section 6.3. This document
carries the detailed method behind those values. The verification chain behind
the published values, from the hand-computed regression tests to the independent
counter-check, is in [verification.md](verification.md).

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

The aggregation unit is the document. A pagewise CER breaks as soon as the page
numbering of reference and pipeline drifts apart, so the evaluation aligns on
content and stays immune to that drift (lesson L7 of [journal.md](journal.md)).
The corpus bootstrap procedure (n = 25 reference TEIs, B = 10,000, seed 42,
document-level percentile bootstrap) derives mean and 95% confidence range from
it; the interval method is stated exactly in
[verification.md](verification.md). For orientation the Transkribus
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
[data.md](data.md), exception catalog of the reference corpus.

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
| E8 | `<pb/>` yields two line breaks `\n\n`, which rule N15 collapses to one space | the page boundary leaves no marker in the comparison text |
| E9 | all remaining elements (`<hi>`, `<persName>`, `<bibl>`, `<title>`, `<head>`, `<p>`, `<div>` ...) yield inner text recursively | markup becomes transparent: `<hi>Wort</hi>` becomes Wort |
| E10 | attribute values are not taken over | page numbers from `<pb n="223"/>` and GND IDs from `ref` attributes do not appear in the comparison |
| E11 | XML tails are appended at the parent element | correct order for `<p>Wort1<hi>Wort2</hi>Wort3</p>` |
| E12 | on XML parse error, regex fallback `re.sub(r'<[^>]+>', '', content)` | secures the evaluation against single non-well-formed TEIs so one faulty file does not abort the corpus run |

Two entries of this catalog are read wrongly if taken on their own. Rule E8 emits
two line breaks at a page boundary and rule N15 of the normalization then pulls
every whitespace run onto one space, so the comparison text carries no page
marker; `tests/test_cer_extraction.py::TestExtractionRules::test_page_break_collapses_to_a_single_space`
pins that behaviour. Running heads have no exclusion rule, so the text of `<fw>`
falls under E9 and enters the comparison text like the text of any other element;
`tests/test_cer_extraction.py::TestExtractionRules::test_forme_work_is_included_not_excluded`
pins that. Rule E5 excludes footnotes, and it is the only content exclusion below
`<body>`.

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

## State of research (print OCR)

This section places the pipeline's fidelity CER in the research on OCR of printed
historical documents. The pipeline's own headline values stay in
`docs/data/cer_statistics.json`.

### Where the pipeline sits

The pipeline's fidelity median (n = 25, canonical value in
`docs/data/cer_statistics.json`) lies between the best specialized print stack
(Transkribus with LLM post-correction, 0.84%; Greif et al. 2025) and Transkribus
alone (3.67%). That is solid for historical print without reaching the top of the
field; only the strongest individual documents of the corpus reach the range of
the best literature values. The comparison reads print-calibrated, since the
Transkribus quality bands quoted above stem primarily from handwriting
recognition practice and set the bar lower than a pure print OCR task warrants.

### Comparison table

| Source | Method | Language | CER |
| :---- | :---- | :---- | :---- |
| Greif et al. 2025 | Transkribus Print M1 + Gemini 2.0 Flash post-correction | deu (mostly Fraktur) | 0.84% |
| Greif et al. 2025 | Gemini 2.0 Flash zero-shot | deu (mostly Fraktur) | 1.27% |
| Greif et al. 2025 | Transkribus Print M1 alone | deu (mostly Fraktur) | 3.67% |
| Greif et al. 2025 | GPT-4o direct | deu (mostly Fraktur) | 6.31% |
| Kanerva and Ledins 2025 | GPT-4o LLM-as-judge (no ground truth) | multilingual historical | 6.30% |
| Levchenko 2025 | Gemini 2.5 Pro | rus (18th c.) | 3.36% |
| Levchenko 2025 | Gemini 2.5 Flash | rus | 4.94% |
| Levchenko 2025 | traditional OCR | rus | 21-45% |
| Transkribus documentation | guide value | general | 0.5-2% |

### Comparability caveats

No entry is a like-for-like benchmark; each differs from the Hersch corpus in at
least one dimension. The machine-readable comparability flags in
`docs/data/cer_statistics.json` (block `comparison_lit`) record these dimensions
per entry.

- Greif et al. 2025 (arXiv:2504.00414): German-language address books 1754-1870,
  predominantly Fraktur with one Antiqua source, a different corpus, and in the
  leading row a multimodal post-correction. This is the lower bound of the state
  of research and the most demanding reference point; comparability partial
  (script, corpus, method). These four rows are the print-OCR comparison values
  of this document.
- Kanerva and Ledins 2025 (arXiv:2502.01205): GPT-4o-class, no-ground-truth
  evaluation. Methodologically related to the dictionary-hit-rate proxy but on
  different corpora; comparability partial (method, corpus).
- Levchenko 2025 (LM4DH 2025 workshop at RANLP 2025, Varna, pages 75-85, DOI
  10.26615/978-954-452-106-6-007; preprint arXiv:2510.06743): Russian,
  18th-century Civil Font, which is not like-for-like with French and German
  Antiqua, so comparability is false on language, script and corpus. It is also
  the source of the frequency-based HCPR adaption used for diacritic
  preservation.
- The Transkribus guide value is a general orientation band and no measured
  corpus result.

Why CER values stay of limited comparability between tools even under a nominally identical
metric is stated in [verification.md](verification.md), novelty claims section; the extraction
and normalization rules documented above are the project-internal fixation of the
ground-truth-to-text transformation that section names as the error source.

## Related

- [specification.md](specification.md): the consolidated quality-measurement requirement
- [data.md](data.md): the reference corpus, its exception catalog and the defects that bound the measurement
- [verification.md](verification.md): the verification chain behind the published values
- [testing.md](testing.md): the automated gates that pin the extraction and normalization rules
- [decisions.md](decisions.md): dated provenance (E70, E73, E80, E85, E91, E103)
