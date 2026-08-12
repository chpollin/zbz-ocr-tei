---
title: Knowledge Base zbz-ocr-tei
type: moc
project:
  name: zbz-ocr-tei
  repository: https://github.com/chpollin/zbz-ocr-tei.git
method:
  name: Promptotyping
  url: https://dhcraft.org/Promptotyping/
status: complete
created: 2026-01-29
updated: 2026-07-31
tags: [zbz-ocr-tei, index, navigation]
template:
  name: Vorlage Index
  version: 0.2
  url: https://dhcraft.org/Promptotyping/promptotyping-document/index
authors: [Christopher Pollin]
---

# Knowledge Base zbz-ocr-tei

Documentation of the LLM-supported OCR and TEI pipeline for the Jeanne Hersch edition (Zentralbibliothek Zuerich).

This knowledge base was consolidated on 2026-04-27 and restructured on
2026-07-07: quality.md, viewer.md, and frontend-gaps.md were dissolved into
specification.md (normative method, rules, open requirements), workflow.md
(viewer, editors, persistence), and the final report (measured values; today
[arbeitsbericht-v3.md](arbeitsbericht-v3.md)). The
principle is a single source of truth per domain, one file per topic.

---

## Documents

| Document | Answers |
|---|---|
| [project.md](project.md) | What is the project? Commission, corpus funnel + page balance (generated via corpus_audit), ZBZ workflow, status |
| [specification.md](specification.md) | What must the system do? Requirements, quality measurement method, validation rule catalog (R/W/Z), gates, epics + user stories, open frontend requirements |
| [pipeline.md](pipeline.md) | How is the pipeline built? Stages PDF -> TEI, engines (Mistral, Docling, Gemini), TEI mapping (ZBZ Hersch schema), round-trip section |
| [workflow.md](workflow.md) | How does the end-to-end data flow run? Data-flow diagram, data formats per stage, the viewer (pages, modes, editors, blank pages, workflow status, design system), save mechanism, round trip from edit to regenerated TEI, provenance concept, planned `_complete.xml` variant, roadmap |
| [ecosystem-synthesis.md](ecosystem-synthesis.md) | Overall picture of the three projects (zbz / szd-htr / teiCrafter): setup + gates + critical path, per-project pipeline/status, ALL user stories, integration + image gap, methodology, frontend gap survey, open points, SSoT assignment |
| [infrastructure.md](infrastructure.md) | How is it deployed? Azure, Mistral Document AI, Podman, GitLab Uni Zuerich, CI/CD, viewer deployment (GitHub Pages) |
| [methodology.md](methodology.md) | How do we work? Epistemic infrastructure, verification cascade, Critical Expert in the Loop, three-layer model, operational CLI |
| [decisions.md](decisions.md) | What has been decided? Decision register (E entries up to E104), open points (O8/O13/O27 with ZBZ, O18 DHCraft; O25/O26 closed), risks |
| [cer-methodology.md](cer-methodology.md) | How is the CER measured? Definition, choice of reference, fidelity/scope decomposition, extraction rules E1-E12, normalization N1-N21, verification of the measurement |
| [literature-comparison.md](literature-comparison.md) | How good is it against the state of research? Print-OCR comparison table and comparability caveats |
| [ground-truth-map.md](ground-truth-map.md) | What do the 25 reference TEIs contain and where do they deviate? Phenomenon map and exception catalog (former Appendix B) |
| [entity-integration.md](entity-integration.md) | How do GND entities get into the delivered TEI? Design plan: input data, target-model rules, three-tier matching, milestones M0-M7, verification |
| [arbeitsbericht-v3.md](arbeitsbericht-v3.md) | The project report (German, client-facing): headline CER, per-document breakdown, corpus proxy, stock corrections, limits, outlook; canonical values in `docs/data/cer_statistics.json` |
| [journal.md](journal.md) | What was done when? Compact session overview (since Jan 2026), recurring patterns |

Constitution + commands: [CLAUDE.md](../CLAUDE.md) (top level, project-wide rules).

---

## Convention Functions

Each document carries one function of the [Convention Knowledge Documents](https://dhcraft.org/Promptotyping/_content/konvention.md) of the Promptotyping method. Where a catalogue template carries the function, the document names it in its `template` frontmatter field and the table gives it here; where the catalogue holds no template, the document is freehand and the reason stands in the last column. A reasoned gap is a design decision, not an omission. The mapping was recorded post hoc (E104); no document was renamed, moved, or rewritten for it.

| Document | Function | Template or reason for freehand |
|---|---|---|
| [index.md](index.md) | Navigation | Vorlage Index |
| [project.md](project.md) | Charter (with Material: corpus funnel and page balance) | Vorlage Projekt-Wissensdokument |
| [specification.md](specification.md) | Specification (requirements, rule catalog, epics and user stories) | Vorlage Specification |
| [pipeline.md](pipeline.md) | Architecture (stages, engines, TEI mapping) | Vorlage Architecture |
| [workflow.md](workflow.md) | Architecture (end-to-end data flow, viewer, persistence, provenance) | Vorlage Architecture |
| [infrastructure.md](infrastructure.md) | Architecture (deployment, CI/CD) | Vorlage Architecture |
| [journal.md](journal.md) | Provenance | Vorlage Journal |
| [arbeitsbericht-v3.md](arbeitsbericht-v3.md) | Reporting (client-facing) | Vorlage Report |
| [decisions.md](decisions.md) | Decision record, split out of Specification | freehand: the catalogue carries decisions as a section of the specification and holds no template for a standing register |
| [cer-methodology.md](cer-methodology.md) | Domain Knowledge (CER measurement method) | freehand: the convention names this function in OCR projects as one without a template |
| [ground-truth-map.md](ground-truth-map.md) | Material (specialisation: reference corpus and deviation catalog) | freehand: a deviation catalog, not the corpus description the Datengrundlage template structures |
| [literature-comparison.md](literature-comparison.md) | Domain Knowledge (print-OCR state of research) | freehand: no function in the catalogue |
| [entity-integration.md](entity-integration.md) | Specification (design plan for the entity-integration epic) | freehand: a forward-looking design plan, the catalogue holds no plan template |
| [methodology.md](methodology.md) | Working method of the project | freehand: describes the way of working, not the scholarly domain, so Domänenwissen does not carry |
| [ecosystem-synthesis.md](ecosystem-synthesis.md) | Cross-project overall picture | freehand: a survey without the bilateral delivery contract that triggers the Integration function |

The action layer lies in the repository root as [CLAUDE.md](../CLAUDE.md), per convention outside `knowledge/`.

---

## Dependencies

```
project (vision, corpus, ZBZ context)
   |
   +-- specification (requirements, quality method, rule catalog, epics)
   |      +-- cer-methodology (CER measurement method in detail)
   |      +-- literature-comparison (print-OCR state of research)
   |      +-- ground-truth-map (the 25 references + exception catalog)
   |      `-- entity-integration (GND entity integration design plan)
   |
   +-- pipeline (stages: PDF -> TEI)
   |      `-- infrastructure (Azure, Podman, CI/CD, viewer deployment)
   |
   +-- workflow (end-to-end data flow + viewer + save + round trip + provenance)
   |
   `-- methodology (Promptotyping + verification cascade)

ecosystem-synthesis: cross-project view (zbz / szd-htr / teiCrafter)
decisions: cross-cutting, decision register
journal: chronological, compact overview
```

---

## Key Concepts

| Term | Definition | Source |
|---|---|---|
| 6-Stage Pipeline | images -> OCR -> layout -> PAGE-XML -> TEI-XML -> evaluation | [pipeline.md](pipeline.md) |
| Document types A-D | single-column / two-column / monograph / special | [project.md](project.md) |
| `zbz_hersch.rng` (E48/E49, extended E68) | project-specific RelaxNG schema for the delivered TEI, the single format authority (E102); active state = ZBZ review template (`data/source/zbz-lieferung-2026-06-21/`) + E68 header elements. Markup model inline GND (E88): `persName`/`orgName`/`bibl` with `ref="GND:..."` at the point of mention, no standOff register | [pipeline.md](pipeline.md), [decisions.md §E88](decisions.md) |
| Hybrid pipeline | Docling layout + LLM-OCR text | [pipeline.md](pipeline.md) |
| Unified TEI Pipeline (E32) | scaffold + Gemini refinement + assembly + validation | [pipeline.md](pipeline.md) |
| Agent-based quality screening (E41, deprecated E66) | 7-layer pre-curation, review JSON per doc; abolished as a quality signal because no human was involved; legacy retained as `_screening_legacy.json` | [decisions.md §E66](decisions.md) |
| Workflow status per stream (E66/E67/E77) | unverifiziert \| in_arbeit \| verifiziert per OCR/layout/TEI (three levels since E77), in the manifest with provenance history, projectable into `<revisionDesc>`. Traffic light: grey=unverifiziert, yellow=in_arbeit, green=verifiziert, red reserved | [workflow.md](workflow.md) |
| Traffic-light reframing (E67) + three-level collapse (E77) | "Pipeline output EXISTS, it is merely unverified"; hence status `offen` renamed to `unverifiziert` and the red default reading abandoned (E67); E77 merges `bearbeitet`+`fertig` into `verifiziert`, one colour per level | [decisions.md §E77](decisions.md) |
| Fidelity CER (E70/E73/E80/E85) | headline quality measure across the 25 reference docs: full-text Levenshtein, edit operations decomposed into fidelity and scope, print-calibrated | [cer-methodology.md](cer-methodology.md) (method), `docs/data/cer_statistics.json` + [arbeitsbericht-v3.md](arbeitsbericht-v3.md) (values) |
| CER statistics (E54) | BCa bootstrap CIs, paired E2E vs OCR-only, HCPR | [specification.md](specification.md) |
| Quality proxy | dictionary hit rate for docs without ground truth; plausibility bound, not a measurement | [specification.md](specification.md) |
| Validation rule catalog | blocking R1-R7, warnings W1-W19, ZBZ conformity Z1-Z8 (inline GND) | [specification.md](specification.md) |
| Reading order / W19 / M3 (E90) | column- and band-aware canonical order; W19 scopes legacy deviations; reversible preview built, corpus rollout operator-gated | [decisions.md §E90](decisions.md), [arbeitsbericht-v3.md](arbeitsbericht-v3.md) |
| revisionDesc (E42) | pipeline + workflow status in the TEI header, travels with the document | [pipeline.md](pipeline.md) |
| `output/tei_final/` (E43) | single source of truth of the delivered TEI data | [pipeline.md](pipeline.md) |
| Verification cascade | 4 levels: automatic / contextual / visual / domain-expert | [methodology.md](methodology.md) |
| Three-layer model | Command (rule) / Artifact (tool) / Tool (invocation) | [methodology.md](methodology.md) |
| Pipeline viewer (E56) | single-page app with facsimile + OCR + TEI + layout/transcription editor; one "Save" -> directly into repo + mirror (E78/E79) | [workflow.md](workflow.md) |
| Hersch Design System | anthracite + brick red + EB Garamond + Jost, `--h-*` tokens | [workflow.md](workflow.md), `docs/assets/css/tokens.css` |
| OpenSeadragon facsimile (E58) | facsimile renderer in view mode with pan/zoom/rotate, loaded via CDN | [workflow.md](workflow.md) |
| Mode edit toggle per panel (E60) | one edit toggle each on the facsimile and text panel (E78), active = anthracite; no global mode bar; page navigation in the facsimile header | [workflow.md](workflow.md) |
| Viewer = Mistral data state (E64) | no OCR source switcher in the viewer; alternative engines (Gemini/LLM) are benchmark-only; doc subbar + toolbar merged | [workflow.md](workflow.md) |
| Export dropdown (E78) | single download per stream (layout/text/TEI/manifest) implemented as a dropdown; JSZip complete/bulk export (E61) still planned, not yet wired into the code | [workflow.md](workflow.md) |
| Method page (E62) | `docs/methode.html` with headline CER, stratified values, limitations, literature comparison (static) | [workflow.md](workflow.md) |
| End-to-end workflow | data flow + save mechanism + round trip + provenance concept + planned `_complete.xml` variant | [workflow.md](workflow.md) |
| Round trip | user edit -> "Save" (directly into repo + mirror, E78/E79) -> `tei_unified --reassemble` -> regenerated TEI | [workflow.md](workflow.md), [pipeline.md §Round-Trip](pipeline.md) |
| Transkribus export (E81) | pipeline PAGE-XML -> bundle (`transkribus_export`) -> REST upload into a collection (`transkribus_upload`); reverse direction of the round trip, auth via env vars | [pipeline.md §Transkribus Export](pipeline.md) |
| Provenance per object (planned) | `{doc}_provenance.json` with full edit history (AI + human), shown in the viewer as a drawer | [workflow.md](workflow.md) |
| `_complete.xml` (planned) | self-contained TEI with `<facsimile>` + `<zone>` + `@facs` + extended `<revisionDesc>` | [workflow.md](workflow.md) |

---

## Quick Start

1. Understand the project: [project.md](project.md), commission, corpus, participants
2. Understand the requirements: [specification.md](specification.md), what the system must do and how it is checked
3. Understand the pipeline: [pipeline.md](pipeline.md), 6 stages + engines + TEI mapping
4. Quality state: [arbeitsbericht-v3.md](arbeitsbericht-v3.md) (the report) and `docs/data/cer_statistics.json` (canonical values); method in [cer-methodology.md](cer-methodology.md)
5. Corpus overview: `docs/index.html`, per-document status + catalog
6. Status: [decisions.md](decisions.md), what is decided, what is blocking
7. Latest session: [journal.md](journal.md), compact session overview

---

## Maintenance

- New fact? Insert it into exactly one document, reference it from the others.
- New decision? Record it in [decisions.md](decisions.md).
- End of session? Add a line to [journal.md](journal.md).
- Duplication found? Remove it immediately, insert a cross-reference.
- Content lives in exactly one document; on overlap, one document keeps the definition and the other links to it.

---

*Consolidated on 2026-04-27; restructured on 2026-07-07 (specification + final report added; quality/viewer/frontend-gaps dissolved)*
