---
title: Knowledge Base zbz-ocr-tei
project:
  name: zbz-ocr-tei
  repository: https://github.com/chpollin/zbz-ocr-tei.git
method:
  name: Promptotyping
  url: https://dhcraft.org/Promptotyping/
template:
  name: Vorlage Index
  version: 0.2
  url: https://dhcraft.org/Promptotyping/promptotyping-document/index
status: complete
language: en
version: 1.0
created: 2026-01-29
updated: 2026-08-26
authors: [Christopher Pollin]
related: [project, specification, tei-mapping, pipeline, workflow, methodology, verification, decisions, journal]
---

# Knowledge Base zbz-ocr-tei

Entry point of the knowledge base. It names the ten documents, assigns each its functions of
the Promptotyping convention, gives reading paths by task and holds the glossary of the terms
the documents use. The project constitution with the operative rules and the full CLI
reference is [CLAUDE.md](../CLAUDE.md) in the repository root.

## Documents

| Document | Answers | Functions carried (templates) |
|---|---|---|
| [project.md](project.md) | What is the project, what material does it work on, and what are the contracts at its borders? Commission, context, standards, scope of functions, delimitations; the corpus funnel (generator-bound), genres and languages, document types A to D, the pilot sample, the delivery structure under `data/`, the entity input data, the reference corpus with its phenomenon map and exception catalog, known problem cases; the integration with ZBZ, Transkribus and teiCrafter (data flow, exchange formats, responsibilities, acceptance criteria, open points) | Charter (Vorlage Projekt-Wissensdokument 0.2); Data (Vorlage Datengrundlage 0.2); Integration (Vorlage Integration 0.1) |
| [specification.md](specification.md) | What must the system do and how is it checked? Sources of authority, system requirements, quality measurement, validation rule catalog (R/W/Z), gates, epics and user stories, scope | Specification (Vorlage Specification 0.3) |
| [tei-mapping.md](tei-mapping.md) | How is the delivered TEI encoded? The markup rulebook (structure, character normalization, page structure, highlighting, special structures, figures, omissions, revisionDesc, element inventory, facsimile binding) and the entity target model (ref pattern, role-based `@resp` provenance, matcher-rule `@source`, three tiers and anchor rule, derived forms, precision guards, marking policy), header and schema declarations, conventions for the whole project | Domain Knowledge, markup rulebook (Vorlage Domänenwissen 0.2) |
| [pipeline.md](pipeline.md) | How is it built and run? Stages PDF to TEI, engines, the TEI mapping stage, the entity preview stage with its instruments, ZBZ structural tags, model APIs and credentials, CI, production fork, local development, viewer deployment with the online demo, third-party-free delivery | Architecture, stages (Vorlage Architecture 0.3); Infrastructure (Vorlage Architecture 0.3) |
| [workflow.md](workflow.md) | How does the data flow end to end and how does a curator work? Data flow diagram, data formats per stage, the viewer (pages and modes, architecture, layout editor, transcription editor, blank pages, workflow status per stream, entity layer), persistence (read path, save mechanism, round trip), provenance as built, the Hersch design system (stance, system, interaction patterns, visualization logic, action-layer coupling) | Architecture, data flow and viewer (Vorlage Architecture 0.3); Design (Vorlage Design 0.2) |
| [methodology.md](methodology.md) | How do we work, how do we measure, who decides? Epistemic infrastructure, verification cascade, operative cycle, Critical Expert in the Loop, three-layer model, conventions; the CER measurement method (definition, reference, fidelity and scope, extraction rules E1 to E12, normalization N1 to N21, print-OCR state of research); governance (authority and decisions, sources and their status, wave pattern, guardrails, verification of agent results, roles, parallel instances) | Domain Knowledge, method layer (Vorlage Domänenwissen 0.2); CER methodology (Vorlage Domänenwissen 0.2); Governance (no catalogue template) |
| [verification.md](verification.md) | What is guaranteed, and do the outward claims hold? Quality assurance (test strategy, guarantees, acceptance, deliberately unchecked classes, how to run, anchor strategy, components, state), the verification of the CER headline, the entity precision and recall and the corpus completeness (problems, verdict vocabulary, chains, anti-anchoring, finding register, open findings, limits), and the appendix with the adjudication protocol, the evaluation result, the CER counter-check and the false-positive hunt protocol | Verification (Vorlage Verification 0.1); Testing, quality assurance (Vorlage Testing 0.2) |
| [decisions.md](decisions.md) | What is decided, and what comes next? The register E1 onward (table for E1 to E63, detail entries from E64) and the plan (target state, phases and milestones with done-when criteria, status tracker, open decisions and dependencies, deviations) | Decision record (no catalogue template); Plan (Vorlage Plan 0.2) |
| [journal.md](journal.md) | What was done when? Format contract, the current entries, the compact archive of sessions 1 to 96, the lessons, and the archive of the full entries of sessions 69 to 96 | Provenance (Vorlage Journal 0.2) |
| [index.md](index.md) | This document | Navigation (Vorlage Index 0.2) |

The client report [project-report.md](../docs/project-report.md) carries the Reporting
function (Vorlage Report 0.2, German). It is a dated snapshot, lives with the static site
under `docs/` and stands outside the ten. Its measured values come from
`docs/data/cer_statistics.json`.

## Reading paths

Each path names the documents to read for one task, in the order they are needed.

- For a first contact, read project.md with its charter and delimitations, then
  specification.md, then the scope-of-functions section of project.md and the plan section
  of decisions.md for what is delivered and what is open.
- To work on the pipeline or on a script, take the stage and its engines from pipeline.md,
  the markup the generator must produce from tei-mapping.md, the meaning of `--dry-run`,
  `--force` and `--reassemble` from the conventions section of methodology.md, the exact
  invocation from the CLI reference in CLAUDE.md, and the gate that must stay green from
  the quality assurance section of verification.md.
- To work on the viewer or the site, take the viewer, its persistence and the design from
  workflow.md, the design imperatives from CLAUDE.md, the viewer deployment and the
  third-party-free delivery from pipeline.md, and the deferred frontend findings from the
  plan section of decisions.md.
- To measure or report quality, take the measurement method from the CER section of
  methodology.md, the finding register and the appendix from verification.md, the values
  from `docs/data/cer_statistics.json`, and the reference corpus with its exception catalog
  from the data section of project.md.
- To work on the entity layer, take the target model and its rules from tei-mapping.md, the
  instruments of the entity stage from pipeline.md, the sampling method, the adjudication
  protocol and the results from verification.md, the milestones M4 to M7 and the open
  operator questions from the plan section of decisions.md, and the entity input data from
  project.md.
- To decide or to plan, read the register and the plan in decisions.md, the last entries of
  journal.md, and the governance section of methodology.md, which states who decides what
  and how agents are run and verified.
- To run agents, take the wave pattern, the verbatim guardrails and the verification of
  self-reports from the governance section of methodology.md, the binding adjudication and
  false-positive hunt protocols from the appendix of verification.md, and the security
  rules from CLAUDE.md.

## Convention

The base follows the Promptotyping convention for knowledge folders. Ten documents carry all
functions the project triggers. Where a document carries more than one function, each
function is a top-level section, the `template` block names the dominant function and the
`absorbed` field lists the others, one string per function. Where the dominant function has
no catalogue template, the block stays absent, as in decisions.md.

Every document carries the core keys `title`, `project`, `method`, `status`, `language`,
`version`, `created`, `updated`, `authors` and `related`, all of them non-empty. The keys
`type`, `tags`, `dependencies` and `source` are excluded. `status` takes one of `idea`,
`draft`, `stub`, `complete`, `reviewed`, `archived`, `active` and `snapshot`. The schema
`version` is identical across the ten. A `template` block carries `name`, `version` and a
`url` under `https://dhcraft.org/Promptotyping/promptotyping-document/`. Every entry of
`related` names an existing document of the base, and every relative link outside code
fences resolves. `tests/test_knowledge_frontmatter.py` pins all of this together with the
document set and the absence of horizontal rules, so the convention runs as a gate in CI.

Every fact lives in exactly one section and is referenced from elsewhere. On overlap, one
section keeps the definition and the other points to it. A new fact goes into the section
that owns the function, a new decision into the register of decisions.md, an open one into
its plan section. Each session ends with a journal entry; once more than five full entries
stand, the oldest move verbatim into the journal's archive of full entries and leave one
compact line each in its compact archive. Durable sections carry no volatile quantities and
name no third-party persons. Dated holdings are exempt because there the figure is the
point, which covers the register entries, the journal entries with their archive, the
verification appendix and the corpus funnel table bound to its generator. Generated mirrors
under `docs/data/` are never edited by hand.

## Terms

| Term | Definition | Source |
|---|---|---|
| 6-stage pipeline | images, OCR, layout, PAGE-XML, TEI-XML, evaluation | [pipeline.md](pipeline.md) |
| Document types A to D | single-column, two-column, monograph, special | [project.md](project.md), data section |
| `zbz_hersch.rng` (E48/E49, extended E68) | project-specific RelaxNG schema for the delivered TEI, the single format authority (E102); active state is the ZBZ review template plus the E68 header elements; markup model inline GND (E88), where `persName`, `orgName` and `bibl` carry the GND reference at the point of mention and no standOff register exists | [tei-mapping.md](tei-mapping.md), [specification.md](specification.md) |
| Hybrid pipeline | Docling layout plus LLM-OCR text | [pipeline.md](pipeline.md) |
| Unified TEI pipeline (E32) | scaffold, Gemini refinement, assembly, validation | [pipeline.md](pipeline.md) |
| Workflow status per stream (E66/E67/E77) | `unverifiziert`, `in_arbeit`, `verifiziert` per OCR, layout, TEI (and entities in the preview layer), in the per-object manifest with provenance history, projected into `<revisionDesc>`; traffic light grey, yellow, green, red reserved | [workflow.md](workflow.md), workflow status section |
| Traffic-light reframing (E67) and three-level collapse (E77) | pipeline output exists for every document and its unverified state is the handover default; `offen` became `unverifiziert`, `bearbeitet` and `fertig` merged into `verifiziert` | [decisions.md](decisions.md) E67, E77 |
| Fidelity CER (E70/E73/E80/E85) | headline quality measure over the 25 reference documents: full-text Levenshtein, edit operations decomposed into fidelity and scope, print-calibrated | [methodology.md](methodology.md), CER measurement section; values in `docs/data/cer_statistics.json` |
| CER statistics (E54) | document-level percentile bootstrap intervals, paired end-to-end versus OCR-only, HCPR | [methodology.md](methodology.md), CER measurement section; [specification.md](specification.md) |
| Quality proxy | dictionary hit rate for documents without ground truth; a plausibility bound | [specification.md](specification.md) |
| Validation rule catalog | blocking R1 to R7, warnings W1 to W7 and W11 to W19, ZBZ conformity Z1 to Z6 and Z8 | [specification.md](specification.md) |
| Entity layer (closed world, E105 onward) | deterministic matcher against the curated ZBZ entity list, preview-only; `output/tei_final/` stays entity-free until the operator-released stock run | [tei-mapping.md](tei-mapping.md) (rules), [pipeline.md](pipeline.md) (instruments), [decisions.md](decisions.md) plan section (milestones) |
| Mark provenance and marking policy (E118/E119/E131) | every preview mark carries role-based `@resp` and matcher-rule `@source`, with no entity `@cert`; agent annotation, independent LLM review and person-bound editorial verification remain distinct activities; operator marking decisions live in `data/entities/marking_policy.json`, facsimile-reviewed judgments in the mention verdict store | [tei-mapping.md](tei-mapping.md), [verification.md](verification.md) |
| Reading order and W19 (E90/E99) | column- and band-aware canonical order; W19 scopes the legacy deviations; machine reordering was refuted against the references (E99), so correction is page-wise and facsimile-verified | [decisions.md](decisions.md) E90, E99; [specification.md](specification.md) |
| revisionDesc (E42) | pipeline and workflow status in the TEI header, travels with the document | [tei-mapping.md](tei-mapping.md) |
| `output/tei_final/` (E43) | single source of truth of the delivered TEI data; `docs/data/` is its generated mirror | [specification.md](specification.md), [workflow.md](workflow.md) |
| Verification cascade | automatic, contextual, visual, domain-expert | [methodology.md](methodology.md) |
| Three-layer model | Command (rule), Artifact (tool), Tool (invocation) | [methodology.md](methodology.md) |
| Wave pattern | parallel build agents on exclusive file sets, verbatim guardrails, independent verifiers, self-reports verified against disk before a commit | [methodology.md](methodology.md), governance section |
| Pipeline viewer (E56, reduced E107) | single-page app with facsimile, OCR, TEI, layout and transcription editors; one document bar with View and Edit menus; one Save writes into the repository and the mirror (E78/E79) | [workflow.md](workflow.md) |
| Hersch design system | warm paper and ink, accents for status and emphasis, `--h-*` tokens as the only values, vendored fonts | [workflow.md](workflow.md), design section; `docs/assets/css/tokens.css` |
| OpenSeadragon facsimile (E58) | facsimile renderer in view mode with pan, zoom and rotate, vendored since E122 | [workflow.md](workflow.md) |
| Export dropdown (E78) | single download per stream; the JSZip bundle export (E61) is planned | [workflow.md](workflow.md), [decisions.md](decisions.md) plan section |
| Method page (E62) | `docs/methode.html` with headline CER, stratified values, limitations and the literature comparison | [workflow.md](workflow.md) |
| Round trip | user edit, Save into repository and mirror, `tei_unified --reassemble`, regenerated TEI | [workflow.md](workflow.md), round-trip section |
| Transkribus export (E81) | pipeline PAGE-XML as a bundle and REST upload into a collection, the reverse direction of the round trip | [project.md](project.md), integration section |
| Provenance log and `_complete.xml` (planned) | `{doc}_provenance.json` with the full edit history and a self-contained TEI with extended `<revisionDesc>`; the facsimile side is delivered (E89) | [decisions.md](decisions.md) plan section; [tei-mapping.md](tei-mapping.md) |
| Adjudication protocol | the binding instructions of the entity evaluation wave, kept verbatim as a dated holding | [verification.md](verification.md), appendix |
