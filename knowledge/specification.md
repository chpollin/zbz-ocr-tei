---
title: Specification
project:
  name: zbz-ocr-tei
  repository: https://github.com/chpollin/zbz-ocr-tei.git
method:
  name: Promptotyping
  url: https://dhcraft.org/Promptotyping/
template:
  name: Vorlage Specification
  version: 0.3
  url: https://dhcraft.org/Promptotyping/promptotyping-document/specification
status: complete
language: en
version: 1.0
created: 2026-07-07
updated: 2026-08-26
authors: [Christopher Pollin]
related: [project, tei-mapping, pipeline, workflow, verification, decisions]
---

# Specification

What the system must do and how fulfillment is checked. This document consolidates the
normative requirements that were previously spread across the constitution (CLAUDE.md),
the decision register, the editorial guidelines and the schema. The register
[decisions.md](decisions.md) keeps the dated provenance of every decision; this document
states the current binding requirement and points to the register entry. On conflict, the
newest ratified register entry wins and this document is updated to match.

## Sources of authority

1. ZBZ editorial guidelines (`data/source/guidelines/`, immutable input; E49).
2. Project schema `data/schema/zbz_hersch.rng` (E48/E49, extended E68), the formal
   contract every delivered TEI must satisfy.
3. Decision register [decisions.md](decisions.md), with the dated rationale and the
   rejected alternatives.
4. This document, the consolidated requirement view.

## System requirements

- R-OCR: every delivered PDF page receives OCR text from the base text layer engine;
  alternative engines produce benchmark artifacts only (E64). Which engine holds that
  role, and how the delivered corpus is reproduced, is stated in
  [pipeline.md](pipeline.md), deployment section.
- R-LAYOUT: every page receives a layout analysis (regions with bounding boxes) from
  Docling with Gemini QA (E19/E20, E25/E26/E31).
- R-PAGE-XML: PAGE-XML plus METS is generated as a parallel export for the Transkribus
  round trip (E13, E81). The TEI generator reads layout and OCR directly (E22), so this
  export stays outside the TEI path.
- R-TEI: each document has exactly one final TEI in `output/tei_final/`, the single
  source of truth of the delivered data (E43), produced by the unified pipeline
  (E22/E32) and mirrored, never hand-edited in the mirror.
- R-SCHEMA: every final TEI validates against `zbz_hersch.rng`; test-gated (E68).
- R-CONFORMITY: the ZBZ conformity rules Z1 to Z6 and Z8 hold corpus-wide; the entity
  rules Z1 to Z4 and Z8 become sharp only on curated inline-GND output (E88; lesson L14).
- R-READING-ORDER: generated block order follows the canonical column- and band-aware
  reading order (E90). Validator warning W19 scopes legacy deviations in the delivered
  corpus; machine reordering of that corpus was tested against the 25 references and
  refuted (E99, no document improved and nine degraded), so flagged pages are corrected
  page-wise and facsimile-verified through `tei_reading_order_fix`.
- R-STATUS: every document carries a per-stream workflow status
  (`unverifiziert` | `in_arbeit` | `verifiziert`; E66/E67/E77) whose transitions are
  human-only, with provenance history in the per-object manifest and deterministic
  projection into the TEI `<revisionDesc>` at handover (E66).
- R-BLANK: safe blank pages are marked as `<pb type="blank"/>` (E63/E65).
- R-PBN: `pb@n` carries the printed page number in square brackets where footer
  detection, interpolation, or a stable scan-to-print offset supports it; pages
  without a reliable signal keep the unbracketed scan number (E94, ratified
  2026-07-07; applied corpus-wide by `tei_pb_folio`, executed with E94/E95, backup
  in `output/_backup_pre_pb_folio/`).
- R-PERSISTENCE: every viewer save writes the payload canonically to `output/` and
  mirrors it to `docs/data/`, so both the pipeline and the server-less viewer see the
  same state (E72/E78/E79).
- R-HEADER: header enrichment from Alma is ZBZ domain (E76, O8); the pipeline states in
  the header only what its own sources support.
- R-ENTITY: entity markup comes from a deterministic closed-world matcher against the
  curated ZBZ entity list and is written read-only to `output/entity_preview/`;
  `output/tei_final/` stays entity-free until an operator releases the stock run (M7).
  The world is closed by decision, so only identifiers present in the curated list can
  reach a mark, and an unlisted name travels through the proposal channel instead of
  becoming markup. Which surfaces are eligible for a mark, which tier a hit belongs to and
  which zones are excluded is the marking scope defined in
  [tei-mapping.md](tei-mapping.md), which owns the entity target model together with the
  `ref` pattern and the attribute vocabulary. Every preview mark carries `@resp` and
  `@source`. The former distinguishes deterministic matching, agent review, agent
  annotation, independent LLM review and person-bound editorial verification; the latter
  names the producing matcher rule. Entity marks carry no `@cert` because an ordinal token
  does not identify the evidence path (E105-E131). Agentic promotion remains a preview-only
  operation, accepts only GND identifiers supplied in the bound candidate set, preserves
  text byte-equivalence and must validate against the project schema.

## Quality measurement

The quality measure for the delivered text is the fidelity CER against the 25
ground-truth reference TEIs, calibrated against the print-OCR literature (E80), since the
corpus is print and the Transkribus quality bands come from HTR practice. The method is
binding since the correctness wave (E70/E73) and is defined in full in
[methodology.md](methodology.md), CER measurement section, which owns the CER formula, the
decomposition of edit operations into fidelity and scope with its threshold, the TEI
extraction rules and the normalization regimes. The requirements this document holds are
the following.

- Every published CER value rests on a document-level full-text comparison against
  the reference and is decomposed into a fidelity share and a scope share. Pipeline
  text beyond the selective reference transcription therefore appears as its own
  share and leaves the fidelity figure untouched.
- Every published point estimate carries a confidence interval from a percentile
  bootstrap with the document as the resampling block, B=10000 and seed 42, because
  the CER distribution is skewed. The pipeline gain over raw OCR uses a paired
  bootstrap on per-document deltas (Du 2025, arXiv:2511.19794).
- Four normalization regimes (`raw`, `nfc`, `nfc_hyphen`, `nfc_hyphen_case`) and a
  frequency-based HCPR adaption for diacritic preservation (Levchenko 2025,
  arXiv:2510.06743) are published in parallel.
- Selection-bias diagnostics (chi-square and Kolmogorov-Smirnov tests of the
  reference subset against the corpus) are published alongside the values, and
  the known deviation in character volume is disclosed with them.
- Corpus-wide, the dictionary hit rate (`quality_proxy`, after Stroebel et
  al. 2022) is a plausibility bound. Its composite estimator does not
  generalize (negative LOOCV R^2), so every display labels it an estimate.
- LLM stability, the run-to-run variance of the non-deterministic OCR and
  refinement stages, is measured (5 docs x 3 runs, E100); the `stability` block of
  `docs/data/cer_statistics.json` carries the per-document spread and reads
  `status: measured`.

Every published figure names its method. The measured values live,
deterministically regenerable with seed 42, in `docs/data/cer_statistics.json`
(rendered by `docs/methode.html`) and are reported in `docs/project-report.md`. How every
published claim was verified, and which findings stayed open, is in
[verification.md](verification.md).

## Validation rule catalog

`tei_validator` applies three rule layers to `output/tei_final/`, the source of truth. The
first two run in the default pass, the third under `--conformity`.

1. Blocking errors R1 to R7, the RelaxNG schema plus the project rules. R1 root
   `type="naegeli"`, R2 teiHeader present, R3 body present, R4 at least one div,
   R5 div `@type` from the valid set and every div carrying `@type` or `@n`, R6
   note with `@place`, R7 no `<figure>` inside `<p>`.
2. Warnings, informative curation signals that never block, numbered W1 to W7
   and W11 to W19. W1 language code "und", W2 empty title or author, W3
   facsimile/pb mismatch, W4 empty div, W5 text volume below 50 chars/page, W6
   missing lb, W7 graphic without url, W11 too many top-level divs sharing the
   same `@n`, W12 footnote without `@n`, W13 footnote xml:id pattern, W14
   back/div types, W15 div with `@type` and `@n` (exclusive), W16 figure without
   xml:id, W17 empty speaker (curation slot), W18 foreign `@xml:lang` not
   normalized to ISO 639-2/T, W19 page reading order not canonical (E90).
3. ZBZ conformity (`zbz_conformity.py`, inline-GND model, E88), the guideline
   rules a RelaxNG cannot express.

| Rule | Requirement | Severity |
|---|---|---|
| Z1 | entity `@ref` must be `GND:...` | violation |
| Z2 | no foreign authority file (GeoNames/Wikidata) | violation |
| Z3 | no places/events as entities, only person/organization/work | violation |
| Z4 | no standOff register, no `<name ref>` mention (inline GND) | violation |
| Z5 | rendering vocabulary only from `{#b,#i,#u,#g,#sup,#sub,#k}` | violation |
| Z6 | `<pb>` with `@facs` and `@n` | violation |
| Z8 | entity without GND reference = curation gap | advisory |

The entity rules Z1 to Z4 and Z8 turn sharp only on curated inline-GND output,
because the delivered corpus is entity-free (lesson L14); Z5 and Z6 bind on the
real corpus today. One guideline self-contradiction (entity markup inside
captions) is an open ZBZ question (O27).

One class of defect stays below this catalog. Footnotes that the generator turned into body
text outside the verified candidate set, and body text demoted to a note below the
verification threshold, are a standing curation risk that no rule flags; the evidence and
the verification history of the demotion runs are in [verification.md](verification.md).

## Gates

| Gate | Check | Requirement |
|---|---|---|
| Schema | `pytest tests/test_tei_schema.py` | R-SCHEMA |
| ZBZ conformity | `pytest tests/test_zbz_conformity.py`, `tei_validator --conformity` | R-CONFORMITY |
| Validator warnings | `tei_validator --all` (non-blocking curation signals) | R-TEI, R-READING-ORDER |
| Corpus audit | `python -m scripts.eval.corpus_audit` (funnel + drift check) | corpus claims |
| Reading-order evidence | `reading_order_audit` (triage), `tei_reading_order_fix` (page-wise instrument, dry-run default); the machine rollout was refuted and its preview instrument removed in the 2026-08 refactoring, evidence in [decisions.md](decisions.md) E99 | W19 curation basis |
| Full suite | `python -m pytest` (CI gate on every push) | all of the above |

What the full suite guarantees, which part of it survives a fresh clone and which classes
of defect it deliberately leaves uncovered, is described in
[verification.md](verification.md), quality assurance section. The invocations stay in
[CLAUDE.md](../CLAUDE.md).

## Epics and user stories

- Epic A, delivery, is done. As ZBZ, I receive schema-valid TEI plus OCR, layout, and
  PAGE-XML for every delivered PDF, so edition work starts from data instead of scans.
  Content verification is tracked per stream under R-STATUS and is ZBZ's task.
- Epic B, curation. As a ZBZ curator, I open a document in the viewer, see facsimile,
  layout, text, and TEI side by side, correct layout or text, save once, and the status
  pill records my verification step with provenance. The stories are correcting the
  reading order on flagged pages (W19 worklist), resolving empty speaker slots (W17),
  confirming blank pages and reviewing the residual reading-order pages at the facsimile.
- Epic C, reading-order curation (E99). The corpus-wide machine rollout was tested and
  refuted, so as a ZBZ curator I work the W19 worklist page by page at the facsimile and
  release each verified fix through `tei_reading_order_fix`; the gates of the table above
  must stay green.
- Epic D, teiCrafter handover. As an annotator, I receive TEI stable enough for control
  and inline-GND annotation in teiCrafter; the entity gate Z1 to Z4 turns sharp on that
  output. The epic runs cross-lane and awaits the teiCrafter output-model switch; the
  handover contract and its open points are in [project.md](project.md), integration
  section.
- Epic E, measurement. As the project lead, I can cite the fidelity CER with a variance
  band, the run-to-run stability of the pipeline being measured (E100), and reproduce
  every published figure from a command.

## Scope

The pipeline delivers four streams per object, the OCR text layer, the layout analysis with
its PAGE-XML export, the final TEI in `output/tei_final/`, and the read-only entity preview.
What the delivered TEI asserts derives from the OCR and layout streams and answers to the
schema and the rule catalog above. Three decisions bound that scope and assign the
remainder.

- Header enrichment from Alma, including the MMSID (O8), and editorial subject headings
  (O13) belong to ZBZ (E76). The contract is in [project.md](project.md), integration
  section, the decision state in [decisions.md](decisions.md), plan section.
- Entity markup lives in the preview layer. Writing marks into the delivered TEI is the
  operator-gated stock run, planned as M7 in [decisions.md](decisions.md), plan section.
- `front`, `back`, cross-page `anchor` and `unclear` are set during curation in the viewer
  against the facsimile (E83), because their source signals are either document-level or
  per-character judgments the page-wise generator cannot make. The markup rule and the
  reason per case are in [tei-mapping.md](tei-mapping.md).

Forward-looking requirements, the open frontend findings and the milestones behind them are
in [decisions.md](decisions.md), plan section.
