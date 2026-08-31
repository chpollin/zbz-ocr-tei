---
title: Methodology
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
created: 2026-03-15
updated: 2026-08-26
authors: [Christopher Pollin]
related: [index, project, specification, pipeline, workflow, verification, decisions, journal]
absorbed:
  - cer-methodology (Vorlage Domänenwissen 0.2)
  - governance (no catalogue template)
---

# Methodology

This document carries three parts. The working method describes the epistemic infrastructure,
the verification cascade, the operative Promptotyping cycle, the Critical Expert in the Loop,
the three-layer model of command, artifact and tool, and the operative conventions. The CER
measurement method fixes how the pipeline is measured against the 25 manually created
reference TEIs, from the definition of the measure to the extraction and normalization rules.
Governance records who decides what and how multi-agent work is run so that its results are
verifiable.

## Epistemic Infrastructure

Agent reliability scales with the quality of the epistemic infrastructure the model
operates in. Model capability alone does not carry it; the gap between SWE-bench and
SWE-bench Pro reaches about 60 percentage points with identical models.

For agents the repository is the primary interface. Three properties must hold:

- Readability: every artifact has a documented purpose ([CLAUDE.md](../CLAUDE.md), knowledge
  docs); new artifacts must be reflected there (maintenance duty).
- Consistency: paths, naming, and data formats follow uniform conventions. What was learned
  on one document holds for all.
- State transparency: the processing state of every object is machine-queryable (JSON
  reports, `<revisionDesc>` in the TEI header).

## Verification Cascade

Four levels, ordered economically (cheap first, expensive last):

1. Automatic: schema validation, Python tests. Binary and fast, this level filters the
   obvious errors.
2. Contextual: an LLM checks content plausibility against the project context. Graded result
   (plausible/questionable/implausible).
3. Visual: facsimile comparison by a vision-capable agent or LLM-as-judge. A different
   modality means epistemic diversity.
4. Domain: expertise that cannot be delegated. The edition scholar decides on ambiguities.

The operative effect is that each level reduces the case set for the next. Domain expertise
is focused on its highest-value area of application (asymmetric amplification).

The entity workflow makes this cascade executable in three different loops. First, the
developer changes deterministic matching rules in response to inspected false positives
and missed forms; every run remains reproducible. Second, an AI agent receives a
SHA-256-bound packet containing facsimile, transcription, TEI page, candidate identities,
schema and guidelines. It may inspect the image, compare the two text representations,
validate the resulting TEI and request an independent LLM judgment. Its decision stays
inside the supplied GND candidate set and writes a separate preview with a run record.
Third, the edition scholar supplies person-bound verification for the cases that require
domain knowledge. The data records these activities as distinct responsibility roles;
ordinal certainty labels do not substitute for provenance.

## Operative Cycle (Promptotyping)

Five steps, iterative (aligned with ReAct's thought-action-observation loop):

1. Diagnosis: the agent determines the state via diagnostic artifacts (read the validation
   report), and the findings drive the step that follows.
2. Exploration: prioritize the corrective measure by the largest quality gain. Structural
   errors before reference errors before formatting.
3. Execution: the agent invokes an artifact, under the flag conventions stated below.
4. Re-validation: run the diagnosis again, compare before and after. A change stays a
   hypothesis until that comparison confirms it.
5. Escalation: after a defined number of iterations or on stagnation, hand the problem to the
   right expert in the loop.

Termination conditions are a maximum of 2-3 cycles per document, a stagnation indicator, and
error-pattern detection.

## Critical Expert in the Loop

Several roles with separated competencies prevent circular validation (anchoring effect,
evidenced by Schroeder et al. 2025):

- DH developer: process configuration (prompts, scripts, thresholds). Does not interact with
  scholarly content.
- Edition scholar: scholarly assessment of the results. Did not configure the process.
- Project management: prioritization and acceptance.

The core principle is that the person who produced a result (or whose agent produced it) is
not the same person who reviews it scholarly. This section owns the scholarly role model,
while the wave roles of the multi-agent process, the guardrails an agent receives verbatim
and the authority to accept a self-report belong to the Governance section below.

## Three-Layer Model: Command / Artifact / Tool

| Layer | What | Example |
|---|---|---|
| Command | decision rule (when, under which conditions) | "Validate after every TEI correction" |
| Artifact | material tool (versioned, maintainable) | `tei_validator.py`, `corpus_audit.py`, [CLAUDE.md](../CLAUDE.md) |
| Tool | concrete invocation by the agent | `python -m scripts.tei.tei_validator --doc 290` |

Each layer depends on the other two. A command without a matching artifact cannot be
executed. An artifact that no command calls for stays unused. An invocation that no command
governs is an ad-hoc action whose result nobody expects to reproduce.

Artifacts are fed-back output, at once a result of the process and input for the next cycle.
The epistemic infrastructure grows in reaction to the quality signals the artifacts emit.

## Operative Tools (CLI)

The complete CLI reference lives in the project constitution [CLAUDE.md](../CLAUDE.md),
section Commands, which is the single source of truth for every command and every flag.
What belongs here is the order in which those commands are used, the operative cycle above
applied to the artifacts.

Diagnosis opens every cycle. The state is read from a diagnostic artifact, in the standard
case from the corpus validation report of the TEI validator; an assumed state never starts
a cycle. Exploration ranks the findings by expected quality gain, structural defects before
reference deviations before formatting. Execution invokes one artifact against the selected
case, observing the flag conventions below. Re-validation repeats the diagnostic step and
compares the state before and after, because only that comparison shows whether the change
improved anything. Escalation hands the case to the expert in the loop once the iteration
cap or a stagnation indicator is reached, which for the delivered corpus means page-wise,
facsimile-verified curation in the viewer.

Every step produces or transforms a knowledge artifact and emits machine-readable quality
signals. The statistics artifact `docs/data/cer_statistics.json` is the deterministic
example of such a signal.

## Conventions

- Document IDs follow the pattern `{DOC_ID}` (e.g. 2310, 2530, 1440).
- Generated files go to `output/`, which is gitignored. Two holdings are versioned anyway,
  `data/curated_tei/` reserved for hand-verified TEI and the delivery mirror `docs/data/`.
- `--dry-run` reports the intended change without carrying it out. Every tool that writes
  into `output/tei_final/` carries the flag, as do `tei_unified` and the Transkribus upload,
  and it is the mandatory first run before batch operations and before the stock
  corrections.
- `--force` discards cached results and recomputes them, the paid stages included. It is
  sensible only after an actual upstream change.
- A changed step-2 prompt requires invalidating the cached refinements, because a default
  run and `--reassemble` both reuse the `_refined.xml` of a page and would assemble the old
  prompt's output. `--force` recomputes step 2 for the whole document (the subject of lesson
  L5 of [journal.md](journal.md)).
- `--reassemble` redoes the rule-based stages of `tei_unified`, the step-1 scaffold built
  from the curated OCR and layout and the step-3 assembly, and reuses the Gemini step-2
  cache. Pages without newer curation need no API call. Pages whose curated OCR or layout is
  newer than the cache are selectively re-refined with one Gemini call each, because step 3
  would otherwise assemble from the stale cache and the curation would never reach the final
  TEI. That refinement re-derives the text, so a corrected OCR line reaches the final TEI as a
  suggestion and may be reworded. A word-exact change is made in the viewer's TEI-XML mode,
  which writes `output/tei_final/{DOC_ID}_final.xml` directly and deterministically.
  `--force` re-refines the whole document instead of selected pages.

## CER measurement method

This part is the reference for the character error rate (CER) measurement of the
pipeline against the 25 manually created reference TEIs. It fixes the definition of the
measure, the choice of reference, the fidelity/scope decomposition, and the extraction
and normalization rules that turn structured TEI into comparison text. It also places
the resulting values in the print-OCR state of research. The consolidated requirement
view is in [specification.md](specification.md), quality-measurement section; the
measured values live in `docs/data/cer_statistics.json` (deterministically regenerable,
seed 42) and are reported in `docs/project-report.md`, section 6.3. This part carries the
detailed method behind those values. The verification chain behind the published values,
from the hand-computed regression tests to the independent counter-check, is in
[verification.md](verification.md).

### What the CER measures and how it is defined here

The CER is the share of characters in the reference text that deviate in the produced text.
It is defined as the Levenshtein distance between reference and hypothesis, divided by the
character count of the reference.

The Levenshtein distance is the minimal number of single-character operations (insertion,
deletion, substitution) needed to transform the reference into the hypothesis. The
computation derives these operations; nothing prescribes them. The direction is uniform
throughout, reference to hypothesis, as in `rapidfuzz.Levenshtein.opcodes(reference,
hypothesis)`, so an insertion is text the pipeline carries and the reference lacks, and a
deletion is reference text the pipeline missed. The distance itself is
direction-independent. `rapidfuzz.distance.Levenshtein` computes it, with a pure-Python
fallback when rapidfuzz is absent.

The aggregation unit is the document. A pagewise CER breaks as soon as the page
numbering of reference and pipeline drifts apart, so the evaluation aligns on content
and stays immune to that drift (lesson L7 of [journal.md](journal.md)). The corpus
bootstrap procedure (n = 25 reference TEIs, B = 10,000, seed 42, document-level
percentile bootstrap) derives mean and 95% confidence range from it; the interval method
is stated exactly in [verification.md](verification.md). For orientation the Transkribus
convention grades below 2% as publication-ready, 2 to 5% as research-usable, and 5 to
10% as usable for full-text search. A high CER does not necessarily mean poor text
recognition; it can equally follow from faulty reading order on complex layout or from
Mistral Document AI, the engine behind the delivered text layer, being a general model
without specialization on historical type. The computation itself is a single function
call; the methodological substance lies in the preparation of the two texts and in the
choice of reference.

### Which reference is measured against

The CER measures deviation from a chosen reference. It says nothing about objective
correctness. With TEI ground truth it must therefore be fixed in advance which reading
forms the reference, for TEI keeps two competing versions of the same text in several
places. Two element pairs are relevant. `<sic>`/`<corr>` marks a transmitted faulty form
against an editorial correction. `<abbr>`/`<expan>` marks an abbreviation against its
expansion. The difference is that `<expan>` contains text that never physically stood on
the source (the expansion of "Dr." to "Doctor"), while `<corr>` is a plausible
reading-text variant that usually differs from `<sic>` by only a few characters.

The experiment measures against the edited, curated target version. With `<sic>`/`<corr>`
the corrected form `<corr>` is chosen (rule E3).

The element pair `<abbr>`/`<expan>` does not occur in the reference TEIs of the corpus;
their `<choice>` constructs are `<sic>`/`<corr>` throughout, so only rule E3 applies to the
comparison. `extract_text_for_comparison()` contains no dedicated handling of this pair; a
future occurrence would fall under the generic rule E9 and would then need separate
regulation.

This choice has a measurable consequence. Where the reference itself contains a
transcription error, a more correct recognition counts as a difference. Such cases raise
the measured CER with no pipeline error behind them, and they bound what this
methodology can reach. The known reference defects are catalogued in
[project.md](project.md), data section, exception catalog of the reference corpus.

### Decomposing errors into fidelity and scope

The edit operations are decomposed into two categories that separate different error
causes. Fidelity captures real recognition errors, that is substitutions, deletions, and
small insertions, and forms the measure of reading quality in the narrow sense. Scope
captures large insertions from a threshold of 50 characters. These typically stem from
text components the pipeline captures that the selectively transcribed reference does
not contain, such as mastheads, author lines, or edition metadata. The fidelity CER
evaluates only the first category; the full-text CER includes the scope share as a
diagnostic quantity. Both categories sum character-exactly to the Levenshtein distance.

The code fixes this assignment. `SCOPE_BLOCK_MIN = 50` in `scripts/eval/evaluate_ocr.py`
is the default threshold of `classify_edit_operations()`; substitutions, deletions, and
insertions under 50 characters count toward fidelity, insertions of 50 characters and
more toward scope. Because the fidelity values depend on this threshold, every citation
names the threshold, the reference count and the date with them, a rule that arose from
the independent counter-check.

### TEI extraction

Before the comparison, a comparison text is produced from each TEI in
`extract_text_for_comparison()` of `scripts/eval/evaluate_ocr.py`. The same function
processes both sides, the reference TEI and the pipeline-produced TEI, so measured
differences stem exclusively from text content and not from unequal treatment of the
sides.

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

Two entries of this catalog are read wrongly if taken on their own. Rule E8 emits two line
breaks at a page boundary and rule N15 of the normalization then pulls every whitespace run
onto one space, so the comparison text carries no page marker;
`tests/test_cer_extraction.py::TestExtractionRules::test_page_break_collapses_to_a_single_space`
pins that behaviour. Running heads have no exclusion rule, so the text of `<fw>` falls under
E9 and enters the comparison text like the text of any other element;
`tests/test_cer_extraction.py::TestExtractionRules::test_forme_work_is_included_not_excluded`
pins that. Rule E5 excludes footnotes, and it is the only content exclusion below `<body>`.

### Normalization

After extraction the text passes `normalize_for_comparison()`, likewise identical on both
sides. The rules unify typographic variants that are not substantive differences.

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
distinction of ss and eszett, and numbers, because a deviation in any of them is a
deviation in the text itself. The case-sensitive default follows the tool practice of
dinglehopper and jiwer, which carry lowercasing as opt-in; an optional case-insensitive
secondary metric exists (`casefold=True`). The preservation of accents is checked
separately via its own metric (HCPR).

### State of research (print OCR)

This section places the pipeline's fidelity CER in the research on OCR of printed historical
documents. The pipeline's own headline values stay in `docs/data/cer_statistics.json`.

#### Where the pipeline sits

The pipeline's fidelity median (n = 25, canonical value in
`docs/data/cer_statistics.json`) lies between the best specialized print stack (Transkribus
with LLM post-correction, 0.84%; Greif et al. 2025) and Transkribus alone (3.67%). That is
solid for historical print without reaching the top of the field; only the strongest
individual documents of the corpus reach the range of the best literature values. The
comparison reads print-calibrated, since the Transkribus quality bands quoted above stem
primarily from handwriting recognition practice and set the bar lower than a pure print OCR
task warrants.

#### Comparison table

| Source | Method | Language | CER |
| :---- | :---- | :---- | :---- |
| Greif et al. 2025 | Transkribus Print M1 + Gemini 2.0 Flash post-correction | deu (mostly Fraktur) | 0.84% |
| Greif et al. 2025 | Gemini 2.0 Flash zero-shot | deu (mostly Fraktur) | 1.27% |
| Greif et al. 2025 | Transkribus Print M1 alone | deu (mostly Fraktur) | 3.67% |
| Greif et al. 2025 | GPT-4o direct | deu (mostly Fraktur) | 6.31% |
| Kanerva and Ledins 2025 | GPT-4o LLM-as-judge (no ground truth) | multilingual historical | 6.30% |
| Levchenko 2025 | Gemini 2.5 Pro | rus (18th c.) | 3.36% |
| Levchenko 2025 | Gemini 2.5 Flash | rus | 4.94% |
| Levchenko 2025 | traditional OCR | rus | 21.55-45.96% |
| Transkribus documentation | guide value | general | 0.5-2% |

#### Comparability caveats

No entry is a like-for-like benchmark; each differs from the Hersch corpus in at least one
dimension. The machine-readable comparability flags in `docs/data/cer_statistics.json`
(block `comparison_lit`) record these dimensions per entry.

- Greif et al. 2025 (arXiv:2504.00414) measured German-language address books
  1754-1870, predominantly Fraktur with one Antiqua source, and the leading row
  adds a multimodal post-correction. This is the lower bound of the state of
  research and the most demanding reference point, with comparability partial on
  script, corpus and method. These four rows are the print-OCR comparison values
  of this document.
- Kanerva and Ledins 2025 (arXiv:2502.01205) ran a GPT-4o-class evaluation without
  ground truth, methodologically related to the dictionary-hit-rate proxy and on
  different corpora, with comparability partial on method and corpus.
- Levchenko 2025 (LM4DH 2025 workshop at RANLP 2025, Varna, pages 75-85, DOI
  10.26615/978-954-452-106-6-007; preprint arXiv:2510.06743) measured Russian
  18th-century Civil Font, which is not like-for-like with French and German
  Antiqua, so comparability is false on language, script and corpus. That paper
  is also the source of the frequency-based HCPR adaption used for diacritic
  preservation.
- The Transkribus guide value is a general orientation band and carries no
  measured corpus result.

Why CER values stay of limited comparability between tools even under a nominally identical
metric is stated in [verification.md](verification.md), novelty claims section; the
extraction and normalization rules documented above are the project-internal fixation of the
ground-truth-to-text transformation that section names as the error source.

## Governance

This part records who decides what in this project and how multi-agent work is run so
that its results are verifiable. The scholarly role model with its separated
competencies lives in the Critical Expert in the Loop section above; this part holds the
wave roles, the authority to release and to commit, and the rules that make an agent
report count as evidence. The claims that verification produces are recorded in
[verification.md](verification.md).

### Authority and decisions

The operator releases waves, decides contested cases, and gates every write into the
delivered stock. Stock corrections on `output/tei_final/` run only on an explicit operator
release, always with a dry run first and always reversible through their backup (E94).
Merges, tags and releases stay operator-gated. Agents never commit and never push; the
orchestrator commits after verification.

ZBZ decides the editorial and cataloguing questions, which cover the guidelines and
their interpretation, the header metadata drawn from Alma, subject headings, and the
caption contradiction of the editorial guidelines (O8, O13, O27 in
[decisions.md](decisions.md)). ZBZ also answers what counts as a mention in its
editorial practice and supplies list extensions that recall causes reveal. Because ZBZ
feedback is not available in this project phase, the open convention questions of the
entity layer fall to the operator, who decided them on the record from 2026-08-12 onward
(E105, E108, E119).

DHCraft carries project management, which sets priorities and accepts results, and the
development side, which configures the process, under the separation of competencies stated
above.

### Sources and their status

Every fact has exactly one owner document, and other documents point to it. The same rule
holds for data. `output/tei_final/` is the single source of truth of the delivered TEI
(E43) and `docs/data/` is a generated mirror that is never edited directly; a change to the
source is followed by a regeneration of the mirror.

[decisions.md](decisions.md) is the register of dated decisions and holds the rationale and
the rejected alternatives; [journal.md](journal.md) holds the course of the sessions. A
claim about why something is the way it is belongs in one of the two. Code comments and
durable knowledge documents carry no second version of it.

The working files of a wave, the protocol files, the frozen samples and the per-agent
result files, live under the gitignored `output/` tree and are handed to agents by path.
They are the state that survives a context window, so anything that matters is written to
a file rather than kept in a conversation. Model judgments that shall have lasting effect
are written into versioned verdict files and consumed deterministically afterwards, so no
live model call sits on the critical path of a reproducible run.

### The wave pattern

Work is released in waves of parallel agents, each wave following the same contract.

1. One agent, one bounded task, one disjoint file scope. Agents in the same wave never
   share writable files; shared inputs are read-only. Where many agents write the same kind
   of result, each writes its own file into a collection directory and the orchestrator
   merges, which is how the adjudication verdicts were produced.
2. Specification before delegation. The task prompt names the goal, the concrete file
   scope, the verification the agent must run itself, and the report format. For repetitive
   waves the shared rules move into a protocol file in the repository and every prompt
   binds the agent to it; the prompt then carries only the per-agent range and output path.
3. Guardrails travel verbatim. Security and scope rules are copied into every prompt or
   into the binding protocol file, never paraphrased.
4. Subagents run on an explicitly named strong model, and the orchestrator never lets its
   own model be inherited implicitly. Delegation stays flat, so agents do not spawn agents.

### Guardrails

The standing set is passed into every agent prompt word for word. Never read `.env`, no
secrets in code or docs, no Grokipedia, no LLM-based identifier assignment, no cost
figures, ASCII-safe prints on Windows, never touch files held by another instance, no
writes outside the named file set, no commits, no pushes, no git state changes, no
subagents.

A wave that runs scripts names an allowlist of the scripts it may run, and anything that
writes under `output/audits/eval_sample*` or `data/` is excluded by name. The rule comes
from an incident in wave 3 of the repository refactoring (E123), where a smoke-test run of
the evaluation sampler overwrote a frozen draw that the adjudication protocol had declared
untouchable. The draw was reconstructed from two frozen inputs and the tracked data was
restored, but the reconstruction is not the original file set, and a deliberate re-freeze
remains an operator decision. The prohibition had stood in the protocol file already, so
each wave now enumerates its executable surface in the prompt itself.

### Verification of agent results

An agent self-report counts as unverified until it is checked against the real file state.
The orchestrator re-runs the decisive checks itself, test suites, file existence, the
counts in the produced JSON, before integrating or committing anything. Adversarial
verification is used where findings are cheap to claim and expensive to trust, so
independent verifier agents try to refute findings before they enter the record.

The refactoring waves closed with independent verification, waves 1 and 2 each with two
verifiers, one over the code side and one over the documents, and the orchestrator
checked the reports against the disk before committing (E120 to E124). The code side
re-ran the full test suite, the linter, the command reference and the mirror
regeneration; the document side checked that every relative link resolves, that no
removed statement lost its owner, and that no new volatile quantity entered a durable
document. The gates themselves are described in [verification.md](verification.md),
quality assurance section.

Every wave also starts by checking that the artifacts under review match the current code
state, because an audit of a stale artifact produces findings that were already fixed.

### Roles

- Orchestrator, the main instance, decomposes the work, writes protocol files, launches
  waves, verifies, merges, commits per package, and keeps the journal and the decision
  register.
- Build agents implement one bounded change test-first inside their file scope.
- Analysis agents run read-only investigations and write only into report directories.
- Adjudication agents judge drawn cases against the source, the facsimile, under a fixed
  verdict scheme; a designated second adjudicator works blind so that inter-annotator
  agreement can be measured.
- Verifier agents check a finished wave against the disk and try to refute its reports.
- The operator releases waves, spot-checks, breaks ties, accepts reports, and gates every
  stock write.
- ZBZ answers specification questions from editorial practice and supplies list extensions.

### Parallel instances

Several instances work in the same tree at the same time. Before an edit, `git status` plus
verification against the real file state is mandatory, and a conflict of the kind "file
modified since read" is the signal to step back rather than to force the write (L12). A
file another instance holds stays untouched until that instance has committed, which is why
a document under an uncommitted foreign diff is excluded from a wave by name in the
guardrails. A tree with foreign modifications is not committed wholesale; staging names
explicit paths.

### What made the pattern work

The corpus-scale evaluation waves became reliable only once three conditions held, and
those conditions are the transferable core. A frozen, seeded sample lets agents judge a
fixed set, so results merge without coordination. A written verdict scheme with exactly one
value per case keeps agents from drifting into free-form prose. Per-agent output files
avoid write conflicts and keep every judgment attributable. These three conditions apply
wherever many agents assess many items, independent of the domain.

Two further lessons come from the entity waves. Evaluation panels are drawn by impact and
class coverage, meaning top-wrap documents, excluded-zone classes and German prose, because
a draw by document count alone misses the classes that matter. Evaluator schemas separate a genuinely lost
mention from a mention that sits on the worklist, because a schema that conflates them
produces a number nobody can act on.

### Known limits

Agent self-reports overstate completion under ambiguity, so every self-report is checked
against the real file state. Long waves outlive a context window, so all state that
matters lives in files, in samples, protocols and verdicts. Permission boundaries differ
per environment, so an agent may be unable to perform an operator-gated action the
orchestrator predicted it could, and the wave design has to tolerate that by letting the
agent report and hand back instead of working around the boundary.

## Literature and references

### Literature

- Yang et al. (2024). *SWE-agent: Agent-Computer Interfaces.* NeurIPS 2024. Scaffolding beats model capability.
- Kamoi et al. (2024). *When Can LLMs Actually Correct Their Own Mistakes?* TACL. Self-correction needs external feedback.
- Schroeder, Roy, Kabbara (2025). *Just Put a Human in the Loop?* Findings of ACL. Anchoring effect with LLM suggestions.
- Yao et al. (2023). *ReAct: Synergizing Reasoning and Acting.* ICLR 2023. Thought-action-observation loop.
- He et al. (2026). *Speed at the Cost of Quality.* MSR 2026. Speed without infrastructure creates technical debt.
- Zhang et al. (2025/2026). *Agentic Context Engineering (ACE).* arXiv. Accumulated context knowledge compensates model capability.

The print-OCR comparison values of Greif et al., Kanerva and Ledins, and Levchenko are cited
with their identifiers in the comparability caveats above.

### Document references

- [project.md](project.md), data section: the reference corpus, its exception catalog and the defects that bound the measurement
- [specification.md](specification.md): quality method, validation rules and the consolidated quality-measurement requirement
- [pipeline.md](pipeline.md): technical pipeline architecture
- [workflow.md](workflow.md): the viewer as verification environment, the workflow status per stream
- [verification.md](verification.md): the verification chain behind the published claims, and in its quality assurance section the automated gates that pin the extraction and normalization rules
- [decisions.md](decisions.md): dated provenance (E70, E73, E80, E85, E91, E103)
- [journal.md](journal.md): the course of the sessions
- [CLAUDE.md](../CLAUDE.md): project rules, complete CLI reference
