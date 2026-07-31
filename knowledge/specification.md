---
title: Specification
type: knowledge
project:
  name: zbz-ocr-tei
  repository: https://github.com/chpollin/zbz-ocr-tei.git
method:
  name: Promptotyping
  url: https://dhcraft.org/Promptotyping/
status: draft
language: en
created: 2026-07-07
updated: 2026-07-07
tags: [zbz-ocr-tei, specification, requirements, epics]
related: [decisions, project, pipeline, workflow, cer-methodology]
template:
  name: Vorlage Specification
  version: 0.3
  url: https://dhcraft.org/Promptotyping/promptotyping-document/specification
authors: [Christopher Pollin]
---

# Specification

What the system must do and how fulfillment is checked. This document consolidates the
normative requirements that previously lived distributed across the constitution
(CLAUDE.md), the decision register, the editorial guidelines, and the schema. The register
[decisions.md](decisions.md) keeps the dated provenance of every decision; this document
states the current binding requirement and points to the register entry. On conflict, the
newest ratified register entry wins and this document is updated to match.

## Sources of authority

1. ZBZ editorial guidelines (`data/source/guidelines/`, immutable input; E49).
2. Project schema `data/schema/zbz_hersch.rng` (E48/E49, extended E68): the formal
   contract every delivered TEI must satisfy.
3. Decision register [decisions.md](decisions.md): dated rationale and rejected
   alternatives.
4. This document: the consolidated requirement view.

## System requirements

- R-OCR: every delivered PDF page receives OCR text from the production engine
  (Mistral Document AI); alternative engines are benchmark-only (E64).
- R-LAYOUT: every page receives a layout analysis (regions with bounding boxes) from
  Docling with Gemini QA (E19/E20, E25/E26/E31).
- R-PAGE-XML: PAGE-XML plus METS is generated as a parallel export for the Transkribus
  round trip (E13, E81); it is never the TEI input.
- R-TEI: each document has exactly one final TEI in `output/tei_final/`, the single
  source of truth of the delivered data (E43), produced by the unified pipeline
  (E22/E32) and mirrored, never hand-edited in the mirror.
- R-SCHEMA: every final TEI validates against `zbz_hersch.rng`; test-gated (E68).
- R-CONFORMITY: the ZBZ conformity rules Z1-Z8 hold corpus-wide; the entity rules Z1-Z4
  become sharp only on curated inline-GND output (E88; lesson L14).
- R-READING-ORDER: generated block order follows the canonical column- and band-aware
  reading order (E90). Validator warning W19 scopes legacy deviations in the delivered
  corpus; rewriting that corpus is operator-gated (M3), and the residual pages that
  resist automatic correction go to facsimile review.
- R-STATUS: every document carries a per-stream workflow status
  (`unverifiziert` | `in_arbeit` | `verifiziert`; E66/E67/E77) whose transitions are
  human-only, with provenance history in the per-object manifest and deterministic
  projection into the TEI `<revisionDesc>` at handover (E66).
- R-BLANK: safe blank pages are marked as `<pb type="blank"/>` (E63/E65).
- R-PBN: `pb@n` carries the printed page number in square brackets where footer
  detection, interpolation, or a stable scan-to-print offset supports it; pages
  without a reliable signal keep the unbracketed scan number (E94, ratified
  2026-07-07; corpus application via `tei_pb_folio`, run operator-gated).
- R-PERSISTENCE: every viewer save writes the payload canonically to `output/` and
  mirrors it to `docs/data/`, so both the pipeline and the server-less viewer see the
  same state (E72/E78/E79).
- R-HEADER: header enrichment from Alma is ZBZ domain (E76, O8); the pipeline does not
  fabricate catalog metadata.

## Quality measurement

The quality measure for the delivered text is the fidelity CER against the 25
ground-truth reference TEIs, calibrated against print-OCR literature rather than
HTR quality bands (E80). The method is binding since the correctness wave
(E70/E73):

- CER = `Levenshtein(reference, hypothesis) / max(1, |reference|)`;
  document-level full-text comparison, no alignment trimming, case-sensitive,
  NFC-normalized.
- Every edit operation is classified (`classify_edit_operations`):
  substitutions, small indels, and all deletions count as fidelity errors;
  insertions of at least 50 characters count as scope, that is pipeline text
  beyond the selective reference transcription. The asymmetry is deliberate,
  being more complete than the reference is no error. Identity:
  `cer_fidelity + scope_insertion_rate = cer` (full text).
- Confidence intervals: BCa bootstrap, B=10000, seed 42, the document as the
  resampling unit (CER distributions are skewed). The pipeline gain over raw
  OCR uses a paired bootstrap on per-document deltas (Du 2025,
  arXiv:2511.19794).
- Published in parallel: four normalization regimes (raw / nfc / nfc_hyphen /
  nfc_hyphen_case) and a frequency-based HCPR adaption for diacritic
  preservation (Levchenko 2025, arXiv:2510.06743).
- Selection-bias diagnostics (chi-square and KS tests of the reference subset
  against the corpus) are published alongside the values; the known deviation
  in character volume is disclosed, not hidden.
- Corpus-wide, the dictionary hit rate (`quality_proxy`, after Stroebel et
  al. 2022) is a plausibility bound, not a measurement; its composite
  estimator does not generalize (negative LOOCV R^2) and is labeled as an
  estimate wherever shown.
- LLM stability (run-to-run variance of the non-deterministic Mistral and
  Gemini stages) is released for measurement and executes at the workstation
  (5 docs x 3 runs; see [decisions.md](decisions.md)).

No figure is published without its method. The detailed measurement method is in
[cer-methodology.md](cer-methodology.md). The measured values live,
deterministically regenerable with seed 42, in `docs/data/cer_statistics.json`
(rendered by `docs/methode.html`) and are reported in
`arbeitsbericht-v3.md`, section 6.3.

## Validation rule catalog

`tei_validator` enforces three layers on `output/tei_final/` (the SoT):

1. Blocking errors R1-R7 (RelaxNG plus project rules): R1 `type="naegeli"`,
   R2 teiHeader present, R3 body present, R4 at least one div, R5 valid div
   types, R6 note place, R7 entity ref format.
2. Warnings W1-W19 (informative curation signals, never blocking): W1
   language code "und", W2 empty title/author, W3 facsimile/pb mismatch, W4
   empty div, W5 text volume below 50 chars/page, W6 missing lb, W7 graphic
   without url, W11 too many identical top-level divs, W12 footnote n, W13
   footnote xml:id pattern, W14 back/div types, W15 div with type AND n
   (exclusive), W16 figure without xml:id, W17 empty speaker (curation slot,
   E71), W18 foreign xml:lang not normalized, W19 page reading order not
   canonical (E90). W8-W10 are retired since E71, the delivered TEI is
   entity-free.
3. ZBZ conformity (`zbz_conformity.py`, inline-GND model, E88), guideline
   rules a RelaxNG cannot express:

| Rule | Requirement | Severity |
|---|---|---|
| Z1 | entity `@ref` must be `GND:...` | violation |
| Z2 | no foreign authority file (GeoNames/Wikidata) | violation |
| Z3 | no places/events as entities, only person/organization/work | violation |
| Z4 | no standOff register, no `<name ref>` mention (inline GND) | violation |
| Z5 | rendering vocabulary only from `{#b,#i,#u,#g,#sup,#sub,#k}` | violation |
| Z6 | `<pb>` with `@facs` and `@n` | violation |
| Z8 | entity without GND reference = curation gap | advisory |

The entity rules Z1-Z4 and Z8 turn sharp only on curated inline-GND output,
because the delivered corpus is entity-free since E71 (lesson L14); Z5 and Z6
bind on the real corpus today. One guideline self-contradiction (entity
markup inside captions) is an open ZBZ question (O27).

## Gates

| Gate | Check | Requirement |
|---|---|---|
| Schema | `pytest tests/test_tei_schema.py` | R-SCHEMA |
| ZBZ conformity | `pytest tests/test_zbz_conformity.py`, `tei_validator --conformity` | R-CONFORMITY |
| Validator warnings | `tei_validator --all` (non-blocking curation signals W1-W19) | R-TEI, R-READING-ORDER |
| Corpus audit | `python -m scripts.eval.corpus_audit` (funnel + drift check) | corpus claims |
| Reading-order evidence | `reading_order_audit` (triage), `tei_reassemble_preview` (reversible dry run, report in `reports/m3-reassemble-preview.md`) | M3 decision basis |
| Full suite | `python -m pytest` (CI gate on every push) | all of the above |

## Epics and user stories

- Epic A, delivery (done): as ZBZ, I receive schema-valid TEI plus OCR, layout, and
  PAGE-XML for every delivered PDF, so edition work starts from data instead of scans.
  Verification of content is tracked per stream and is ZBZ's task (M5).
- Epic B, curation: as a ZBZ curator, I open a document in the viewer, see facsimile,
  layout, text, and TEI side by side, correct layout or text, save once, and the status
  pill records my verification step with provenance. Stories: correct reading order on
  flagged pages (W19 worklist); resolve empty speaker slots (W17); confirm blank pages;
  review the M3 residual pages at the facsimile.
- Epic C, reading-order rollout (M3, operator-gated): as the operator, I approve the
  corpus regeneration after accepting the dry run, so the delivered TEI carries the
  canonical reading order; the gates of the table above must stay green.
- Epic D, teiCrafter handover: as an annotator, I receive TEI stable enough for control
  and inline-GND annotation in teiCrafter; the entity gate Z1-Z4 turns sharp on that
  output. Cross-lane, awaits the teiCrafter output-model switch.
- Epic E, measurement: as the project lead, I can cite the fidelity CER with a variance
  band (stability measurement, gated by API cost) and reproduce every published figure
  from a command.

## Open requirements

- O8 header metadata from Alma, O13 subject headings, O27 caption contradiction: with
  ZBZ (see [decisions.md](decisions.md)).
- Footnote overdetection (E82 defect a): resolved for the reference-covered blocks by
  the verified demotion E85 (documents 290, 1910, 90, 40, 1520). The reference-less
  remainder was quantified by `body_note_audit` and facsimile-verified case by case
  (verdicts persisted in `output/audits/body_note_verdicts.json`); the correction runs
  via `tei_body_note_demote` (E94, operator-gated). Below-threshold notes and genuine
  footnotes lost to the role swap outside the candidate set remain a curation risk.

### Frontend requirements (deferred until after ZBZ acceptance)

Finding IDs from the dated gap analysis (surveyed 2026-06-07; the H and M
findings were fixed 2026-06-10, provenance in `arbeitsbericht-v3.md`, section 5):

- N1: no multi-select/bulk export in the catalog; the ZIP bundle (JSZip) of
  roadmap E61 is not yet integrated, only per-stream single export exists.
- N3: OpenSeadragon loads an untiled full PNG and re-instantiates on every
  page switch; fix via tiling/DZI or neighbor preload.
- N6: the mobile catalog (below 1000px) hides date/language/type/form/pages
  entirely; keep at least date and type.
- N7: the contrast of `--h-text-muted` sits below WCAG AA for small text;
  restrict the token to auxiliary text.
- Page strip with per-page status markers as QA navigation (follow-up idea
  from the go-to-page fix).
- Provenance panel in the viewer, built on the planned `provenance.json`
  (see [workflow.md](workflow.md), provenance section).

A fresh corpus-wide frontend gap analysis is planned at the workstation
after the push; new findings land here.

## Non-requirements

Explicitly out of scope: NER and entity linking in pipeline output (removed, E71);
automatic `front`/`back`/`anchor`/`unclear` markup (E83); MMSID projection into headers
(E76); monetary figures and third-party personal names anywhere in the documentation
(constitution).
