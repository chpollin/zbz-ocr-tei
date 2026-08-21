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
status: complete
language: en
version: 1.0
created: 2026-02-18
updated: 2026-08-21
authors: [Christopher Pollin]
related: [data, specification, pipeline, workflow, integration, plan, index]
---

# Project

LLM-supported OCR and TEI pipeline for the Jeanne Hersch papers (Nachlass) of the
Zentralbibliothek Zuerich.

## Data basis

The material is the digitized Hersch holdings of the ZBZ, delivered as PDF scans with an
Excel Masterfile as the coordination record, alongside a small set of hand-made reference
TEIs, the editorial guidelines and a Transkribus PAGE-XML export. The corpus is
predominantly French-language prose of the middle and late twentieth century, distributed
over journal articles, contributions to edited volumes and monographs. Its funnel, page
balance, genre and language distribution, the four document types, the pilot sample and the
known problem cases are described in [data.md](data.md), which owns every corpus figure.

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
and teiCrafter are in [integration.md](integration.md).

## What it is about

The mission is to turn scanned pages into schema-valid TEI that a curator can verify page by
page against the facsimile, so edition work starts from structured data rather than from
scans. Three commitments follow from that. The delivered TEI validates against the project
schema and carries its own provenance in the `revisionDesc`. Every published quality figure
rests on a stated method and is reproducible from a command. Every human verification step
is recorded per stream and travels with the object.

The corpus splits into four layout classes, from single-column prose over two-column journal
pages and long monographs to special cases such as historical print, interview transcripts
and illustrated books; each class routes to its own processing strategy. The classes and
their strategies are defined in [data.md](data.md), document types A to D, and the routing
that consumes them is in [pipeline.md](pipeline.md).

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
[infrastructure.md](infrastructure.md).

## Scope of functions

What the repository delivers today, by component.

| Component | Delivered function |
|---|---|
| Image extraction | page images per document at a configurable resolution (`scripts/edition/extract_pages.py`) |
| OCR | base text layer per page for every delivered PDF; Gemini is the resolved default engine, the Mistral path stays selectable as the reproducibility record of the delivered corpus (E64) |
| OCR post-correction | optional LLM post-correction (E17) and a Gemini correction variant on a sample (E29) |
| Layout analysis | Docling regions with bounding boxes plus Gemini quality assurance in `--mode auto` (E19/E20, E25/E26/E31) |
| PAGE-XML export | PAGE-XML per page with a METS wrapper, plus the Transkribus upload bundle (E13/E81) |
| Document classification | one-shot classification into the four document types, cached in `data/doc_metadata.json` (E27) |
| TEI generation | the unified pipeline of scaffold, model refinement, assembly and validation, schema-valid across the corpus (E32/E102) |
| TEI validation | RelaxNG plus the project rules R1 to R7, the warning rules and the ZBZ conformity rules; catalog owned by [specification.md](specification.md) |
| Entity layer | deterministic closed-world matcher against the curated ZBZ entity list, written read-only to a preview layer with per-page views in the viewer and the corpus overview `docs/entities.html`; the delivered TEI stays entity-free until an operator releases the stock run |
| Workflow status | three-level status per stream with human-only transitions, provenance history in the per-object manifest and deterministic projection into the TEI `revisionDesc` (E66/E67/E77) |
| Blank pages | safe blank pages detected per object and projected as `<pb type="blank"/>` (E63/E65) |
| Viewer | static single-page app with facsimile, OCR, TEI and layout side by side, layout and text editing, one save that writes into the working tree and the mirror, and per-stream export (E56/E58/E60/E72/E78/E79/E107) |
| Measurement | fidelity CER against the reference TEIs with bootstrap intervals, the quality proxy for documents without ground truth, and the corpus audit as the funnel gate |
| Delivery site | static GitHub Pages site with catalog, viewer, method page and entity overview, served from the generated mirror `docs/data/` |
| Continuous integration | GitHub Actions runs the linter and the full test suite on every push and pull request |

Open items and their conditions are in [plan.md](plan.md); the status tracker there holds
the current state per milestone.

## Delimitations

ZBZ owns the library-side steps of the edition. Alma cataloguing, Masterfile maintenance,
Swisscovery assignment, the header fields drawn from Alma (O8), the manual GND linking in
Oxygen and the final quality assurance before publication stay in ZBZ hands, as does the
interpretation of the editorial guidelines. The full division of responsibilities, the
acceptance criteria and the open input gaps are in [integration.md](integration.md).

Inside the repository three areas are bounded by design. Entity marks live in a read-only
preview layer until an operator releases the stock run. Document-level and per-character
curation decisions, meaning `front`, `back`, cross-page `anchor` and `unclear`, are made in
the viewer against the facsimile, with the reasons in [tei-mapping.md](tei-mapping.md).
Reading-order repair on flagged pages runs page-wise and facsimile-verified, because the
corpus-wide machine rollout was tested against the reference documents and refuted (E99).

## Licence

MIT, `LICENSE` at the repository root.

## References

- [data.md](data.md): corpus, delivery structure, reference corpus, problem cases
- [specification.md](specification.md): requirements, quality method, validation rules
- [pipeline.md](pipeline.md): the six stages, engines and routing
- [tei-mapping.md](tei-mapping.md): the markup rules of the delivered TEI
- [workflow.md](workflow.md): data flow, viewer, save path, round trip
- [integration.md](integration.md): ZBZ, Transkribus and teiCrafter contracts
- [plan.md](plan.md): open milestones, status tracker, open decisions
- [infrastructure.md](infrastructure.md): deployment, APIs, continuous integration
- `arbeitsbericht-v3.md`: the project report; measured values in `docs/data/cer_statistics.json`
- [decisions.md](decisions.md): the dated decision register
- [index.md](index.md): navigation and glossary
