---
title: "Ecosystem Synthesis: Hersch / SZD / teiCrafter"
type: knowledge
project:
  name: zbz-ocr-tei
  repository: https://github.com/chpollin/zbz-ocr-tei.git
method:
  name: Promptotyping
  url: https://dhcraft.org/Promptotyping/
status: complete
created: 2026-06-07
updated: 2026-07-08
tags: [ecosystem, synthesis, zbz-ocr-tei, szd-htr, teicrafter]
authors: [Christopher Pollin]
---

Dated snapshot of 2026-06-07, moved from knowledge/ on 2026-08-21; superseded facts live in project.md, pipeline.md, workflow.md, methodology.md and the register.

# Ecosystem Synthesis: Hersch / SZD / teiCrafter

A condensed overall picture of the three edition projects, produced after a complete reading
of all knowledge documents of the three repos (~34 files) plus a live frontend analysis.
The single source of truth remains the respective home repo (see §10); this document
synthesizes, it does not duplicate. Point-in-time snapshot (2026-06-07); check `file:line`
and numeric claims against the code before use.

---

## 1. Setup

Three repos, one method (Promptotyping). The goal is to merge two independent HTR/OCR
pipelines in a single lossless editor (teiCrafter).

| Repo | Role / gate |
|---|---|
| `ResearchTools/teiCrafter` | editor/engine/annotation (G2), tests (G1.2/G4), converter reference (groundwork for G1.4b) |
| `szd-htr` | SZD batch converter Page-JSON -> TEI (G1.4b) |
| `DHCraft/zbz-ocr-tei` | frontend gap analysis ZBZ -> teiCrafter, Hersch first |

The shared stance is "machine-generated = unverified until a human checks it"; in teiCrafter
this is visible as the violet `--color-ai` marking, in zbz/szd as workflow/review status.

Critical path (all deliverables on disk still OPEN as of 2026-06-07):
```
ZBZ image URL schema ----------+
                               +-> teiCrafter: converter-reference.md + <graphic> support
mapping-independent scaffold --+        +-> szd: pipeline/export_tei.py done
```
teiCrafter is the bottleneck.

---

## 2. zbz-ocr-tei: Jeanne Hersch Pipeline

- Mandate: Zentralbibliothek Zuerich, contractor DHCraft, confirmed 2026-02-14.
  Estate of the philosopher Jeanne Hersch.
- Corpus: 325 cataloged -> 289 digitized -> 286 PDF -> 285 final TEI (doc 10 incomplete);
  page and language tallies reproducibly via `python -m scripts.eval.corpus_audit`
  (physical PDF pages and bibliographic Masterfile pages differ by source). Mainly FR,
  secondarily DE, 1931-1998, mostly journal articles and contributions to edited volumes.
- Delivery target: a high-quality, schema-valid dataset plus curation tool;
  ZBZ builds the edition downstream (Oxygen/Alma/Swisscovery). Pipeline finished and delivered;
  the scholarly verification is ZBZ's task, tracked via the workflow status (all streams
  `unverifiziert` as the handover default). ZBZ keeps Transkribus as a parallel source.
- 6-stage pipeline: PDF -> PNG (300 dpi) + Gemini classification -> Mistral Document AI 2512
  (Azure) OCR -> Docling 2.75 layout + Gemini QA -> PAGE-XML/METS (parallel export) -> Unified
  TEI (scaffold -> Gemini refinement -> assembly) -> evaluation.
  - Key clarification (E22): TEI is generated DIRECTLY from layout JSON + OCR markdown;
    PAGE-XML is NOT an intermediate step but a parallel export (for Transkribus/coOCR).
- TEI: `type="naegeli"`, RelaxNG `zbz_hersch.rng` (from ODD). Already contains
  `<facsimile>`/`<zone>` (absolute pixel coordinates). SoT = `output/tei_final/{doc}_final.xml`
  (E43); `docs/data/pages/` is a generated mirror (never edit directly). The per-object
  manifest carries workflow status plus history.
  Important: `{id}_final.xml` IS teiCrafter's native format; it opens directly, text editing
  without conversion.
- Quality (E70/E73/E85, SoT): the measured values live in [arbeitsbericht-v3.md](../knowledge/arbeitsbericht-v3.md)
  section 6 and `docs/data/cer_statistics.json` (reproducible via
  `python -m scripts.eval.cer_statistics_full --seed 42 --bootstrap-n 10000`); any citation
  of the fidelity values must name the scope threshold `SCOPE_BLOCK_MIN = 50` (E91).
  Full-text CER is a diagnostic only (ZBZ references are partial transcriptions); an earlier
  pipeline-gain headline was retracted as a trimming artifact. The whole delivered corpus is
  schema-valid (E68). The dictionary hit rate is an estimate; the proxy demonstrably does
  not generalize (LOOCV R^2 < 0).
- Workflow status (E66/E67/E77): per stream (OCR/layout/TEI) three levels
  `unverifiziert | in_arbeit | verifiziert`, traffic light gray/yellow/green, red reserved.
  Streams start `unverifiziert` as the handover default; current distribution via the
  per-object manifests.

---

## 3. szd-htr: Stefan Zweig Estate HTR

- Project: subproject of Stefan Zweig Digital; VLM HTR from facsimiles (Literaturarchiv
  Salzburg), image hosting GAMS (University of Graz). Generated entirely by Claude Code,
  DHCraft project management = domain decision-maker. CC-BY 4.0.
- Corpus: 2,107 objects, 18,719 scans, ~23.6 GB. 4 collections: lebensdokumente 127 /
  werke 169 / aufsatzablage 625 / korrespondenzen 1,186. DE 95.6%. 9 document prompt
  groups A-I.
- Pipeline: TEI context resolution (groups A-I) -> 4-layer prompt -> Gemini 3.1 Flash Lite VLM
  (t=0.1, chunking >20 images) -> quality signals/`needs_review` -> model consensus
  (`verify.py`) -> layout ensemble (Docling+Surya+Gemini) -> Page-JSON v0.2 -> PAGE-XML 2019 +
  METS/MODS -> viewer data. CLI entry point is
  `python pipeline/export_*.py <obj> -c <collection> [--all|--force|--dry-run]`.
- Page-JSON v0.2 = a JSON serialization of the PAGE-XML model (document -> pages -> regions ->
  text), coordinates optional (progressive enrichment). Schema `schemas/page-json-v0.2.json`.
  Limitation: only ~25 of ~2,103 objects have layout regions; the rest is text-only
  (`<lb>` + image).
- Verification, 4 tiers: 0 `gt_verified` (human on 3-model GT); 1 `approved` (human in the
  viewer); 2 `agent_verified` (Claude vision sub-agent); 3 needs_review/unreviewed (pipeline
  only). Current state: 0 real `gt_verified` (workflow ready, 15 objects defined), so all CER
  figures are estimates. VLM `confidence` is worthless (always "high"); Gemini almost never
  sets `[?]` markers, which devalues marker_density. The needs_review rate was calibrated
  from 63% to 19.4%.
- Evaluation (estimated, n=58): print/galley proof 99.6-99.9%, typescript 92-99.9%,
  Fraktur/newspaper 97-99.8%, handwriting 95-99.4%, tabular 75-99% (weakest). Error types:
  Fraktur long s -> f, Kurrent confusions, hallucination instead of `[?]`, table structure
  errors. No real CER against GT.
- Architecture trick: the same static viewer is both public read-only AND the local editorial
  workspace; only a running server (`/api/status`) unlocks edit/approve/rebuild.
- Specifics: supplies data to DIA-XAI/EQUALIS (PLUS grant 2026/27, UC3 expert correction);
  security threat model worked through; stats dashboard deliberately without a CER dashboard
  (only ~4.5% with CER).
- Status: transcription ~99% (~2,080/2,107), METS export ~2,074, teiCrafter TEI batch 2,030
  (0 errors); layout only ~25 objects (full batch ~7 days); real GT missing.

---

## 4. teiCrafter: Lossless TEI Editor

- Purpose: browser-based, lossless editor for arbitrary TEI. Open -> read folio by folio ->
  correct in the rendered text -> save back byte-identical (except what was edited).
  The motto "One workbench, two ways in" combines a deterministic editor path with an
  optional "New from text (LLM)" on-ramp.
- Tool boundary (binding, 2026-06-07): teiCrafter edits arbitrary TEI, so it is a tool.
  EditionCrafter is a separate, independent line that builds whole editions
  (display/apparatus/publication). It is a future project with no bearing on the Editopia
  talk (operator decision 2026-07-08); the convergence point demonstrated in the Editopia
  talk is teiCrafter (decision 2026-06-09). The static ZBZ/SZD viewers belong to their
  respective pipelines, not to teiCrafter. Mnemonic: teiCrafter creates and edits TEI,
  EditionCrafter creates the edition.
- Core mechanics: the raw string is canonical, every change is an offset splice on it,
  `serialize()` is byte-identical (DOM-free, no DOMParser/XMLSerializer when serializing).
  Granularity emerges from the document: word level with `<w xml:id>` (Wenzelsbibel),
  otherwise line level (Hersch). No project profile, no branching.
- TEI contract (generic, by local-name): `<pb>`=folio, `<lb>`/`<l>`=line, reading text ->
  editable cells, `<facsimile>/<surface>/<zone ulx uly lrx lry>` -> OpenSeadragon overlays,
  `@facs` = line<->zone bidirectional, `<standOff>/<note target>` = entities/apparatus.
  Anything not interpreted stays verbatim.
- Tech: client-only SPA, native ES6 modules, no build, GitHub Pages from `/docs`; 9 JS files;
  OpenSeadragon 5.0.1 (CDN); 6 LLM providers (keys in memory only). 3 layers:
  `tei-document.js` (offset core) -> `edition.js` (folios/lines/cells) -> `editor-app.js`
  (UI). Maturity: research preview.
- Validation is hybrid: live well-formedness plus structural integrity vs. the load baseline;
  offline RelaxNG (TEI All) plus Schematron (Python/lxml). MVP gate = well-formed AND L1 text
  fidelity AND L3 counts preserved; L2 schema counts only NEW errors relative to the input
  (non-gating).
- Tests: byte-identical round trip across all real files (Hersch corpus + SZD samples + synthetic);
  browser click-through confirmed 2026-06-04 (synthetic Wenzelsbibel). Real files only
  gitignored (license); only synthetic material is committed.
- Design: a research tool, not a consumer product; cream surfaces, serif reading text / sans
  UI / mono IDs, navy header plus gold accent, violet `--color-ai` (#6D4AB6) ONLY for LLM
  output. Tokens are the single source, no hex in components. Status encoded threefold
  (color+icon+position).

---

## 5. User Stories (all three projects)

### teiCrafter: EXPLICIT (`knowledge/user-stories.md`, "As a ... I want ... so that ...")

Status values are Built / Browser-check / Future.
- Editing: E.1 open locally without a server; E.2 page through folios; E.3 cell rendering
  word- or line-wise (emergent); E.4 correct word/line in place; E.5 save changes nothing
  untouched (byte-faithful); E.6 save-in-place or download (Browser-check).
- Facsimile: F.1 zones plus text<->zone highlight; F.2 real images with deep zoom (OpenSeadragon).
- Validation: V.1 live well-formedness/integrity; V.2 full schema validation (offline).
- LLM on-ramp: L.1 plaintext -> draft TEI in the editor; L.2 generated content clearly marked
  "unreviewed" (violet); L.3 API key in memory only; L.4 provider choice.
- Index/standOff: I.1 create/rename/delete person/org/event; I.2 link mention -> index
  (`<name ref="#id">`).
- Future: FU.1 apparatus/comment note authoring; FU.2 authority IDs in the UI; FU.3
  project-specific form views; FU.4 SZD Page-JSON -> TEI converter; FU.5 segmented loading of
  very large editions.

### zbz-ocr-tei: EXPLICIT 3 (viewer), rest derived

- US1 (explicit) project team: QA-check OCR/layout/TEI, review many pages quickly.
- US2 (explicit) ZBZ curator: edit layout/text/TEI and save reliably (human in the loop).
- US3 (explicit) project management: demonstrate results credibly to ZBZ.
- (derived) A DH developer configures the pipeline and generates quality signals; an edition
  scholar reviews the content and approves (role separation against circular validation); a
  ZBZ librarian supplies header metadata from Alma (O8); a curator writes corrections back
  via "Save" -> `--reassemble`.

### szd-htr: NONE explicit; derived from workflow/personas

- Expert: correct the transcription page by page against the facsimile; set tier status
  (approved/agent_verified/gt_verified); edits go directly into the pipeline JSON plus commit;
  steer progress via the progress bar.
- Triage role: filter by `needs_review` and see reasons (prioritize effort).
- Annotator: reproducible diplomatic transcription protocol (inter-annotator CER).
- DH researcher/archivist: aggregated quality metrics; METS/MODS plus PAGE-XML for the
  GAMS/DH stack.
- Operator: CLI batch (single/collection/`--all`, skip-if-exists, `--dry-run`).
- Paper reviewer: vault/journal/exports linked on the public site (check claims without
  cloning the repo).

---

## 6. Integration and Shared Concepts

```
ZBZ:  PDF -> Mistral OCR -> Docling layout -> Unified TEI -> {id}_final.xml ----+
                                                                                +-> teiCrafter (Open)
SZD:  images -> Gemini VLM -> [layout] -> Page-JSON v0.2 -> (export_tei) -------+
                                          +-> PAGE-XML / METS (archive, not editor)
```
- ZBZ -> editor: works TODAY for text (no converter needed; the teiCrafter bundle is doc 100s
  `_final.xml` plus a standOff demo). Markup model: the ZBZ material (2026-06-21) decides in
  favor of inline GND (`persName`/`orgName`/`bibl` with `ref="GND:..."` at the point of
  mention); the active schema has rejected the standOff register since E88 (guard test).
  teiCrafter so far produces standOff; its output model must be aligned to inline GND so that
  a curated document stays valid against `zbz_hersch.rng` (delta reported to the research
  coordination office).
- SZD -> editor: needs `export_tei.py` (blocked on the converter reference).
- Shared image gap: the editor shows the facsimile only with BOTH (imageUrl AND surface);
  imageUrl comes only from a hardcoded demo path (no `<graphic>` support). Fix (verified,
  decision [[decisions#O25|O25]]): write `<graphic url>` pipeline-side as the first
  `<surface>` child (the schema requires graphic before zone) plus `facsimile.js` reading
  `surface.graphic`. Lossless, generalizes; only the URL schema remains open.
- Status mapping: zbz workflow status <-> szd 4-tier review <-> teiCrafter violet AI marking.

---

## 7. Methodology (all three)

All three projects use Promptotyping on epistemic infrastructure. Agent reliability scales
with the quality of the repo as the agent interface (readability, consistency, state
transparency), not with model capability alone. The core is the verification cascade
(automatic -> contextual -> visual -> domain); each level shrinks the case set for the next,
and expensive domain expertise goes only to ambiguities. Critical Expert in the Loop
separates roles (the one who produces is not the one who verifies); this motivated zbz E66
(abolition of the self-certifying agent screening) and teiCrafter's "the human decides".
Epistemic asymmetry means LLMs produce plausible output but cannot judge it themselves, so
the deterministic core makes no probabilistic claims.

---

## 8. Findings: Frontend Gaps

Six frontends in the DHCraft edition ecosystem were surveyed 2026-06-07 by
live inspection plus static source analysis, measured against the same grid:

| Frontend | Purpose | Maturity | Most urgent gap |
|---|---|---|---|
| Hersch (`zbz-ocr-tei/docs`) | OCR/layout/TEI inspection + curation | near production | H and M findings fixed 2026-06-10; N1/N3/N6/N7 open, see [specification.md](../knowledge/specification.md) |
| szd-htr (`szd-htr/docs`) | VLM transcription viewer + review | near production (reference) | empty states vault/stats, deeplink nav |
| teiCrafter (`ResearchTools/teiCrafter`) | lossless TEI editor | advanced prototype | editor not responsive, a11y tabs/modal |
| SZD (`SZD/docs`) | ontology reference + graph | near production (docs) | D3 CDN without fallback, graph a11y |
| editionCrafter (`editionCrafter/docs`) | concept landing + mock | prototype/showcase | live markdown fetch breaks on Pages |
| agentic-edition-pipeline (`.../docs`) | forkable edition template | usable (template) | TEI download path 404 |

szd-htr is the reference implementation of the ecosystem (empty/error
states, `aria-sort`, `aria-live`, URL state, locally vendored dependencies,
local/remote capability detection); the other frontends should align with
it. The Hersch viewer's strength is complete token discipline (no hex/rgb
violations in component CSS, no pure black/white). Its remaining open
findings live as frontend requirements in
[specification.md](../knowledge/specification.md).

Cross-cutting patterns, ecosystem-wide:

1. Fragile external/relative `fetch` without error handling is the most
   frequent bug pattern (editionCrafter repo markdown, agentic-pipeline TEI
   outside `docs/`, SZD D3 CDN). On GitHub Pages this yields silent 404s;
   the remedy is a build copy into `docs/` or a fallback plus an `r.ok`
   check.
2. Accessibility of interactive visualizations (SVG graphs, facsimile
   overlays, clickable table rows) is the largest shared gap; keyboard
   access and text equivalents are missing.
3. CDN instead of local dependencies (OSD, D3, marked/hljs, Chart.js);
   szd-htr vendors locally, which increases robustness on Pages and offline.
4. Visual and language inconsistency between the frontends, relevant for
   the ZBZ demonstration and the DHCraft brand; candidate for shared design
   tokens.

Notes for future automated frontend tests: OpenSeadragon blocks
`Page.captureScreenshot` after click interactions (CDP timeout), so pause or
destroy OSD before capturing; live viewport resize is unreliable in the
automation tooling, verify responsive behavior from the CSS media queries
instead (the catalog switches to a card list at 1000px, the viewer to
stacked panels at 900px). Testing ZBZ files in teiCrafter plus the image URL
schema are still pending.

---

## 9. Open Points / Blockers / Contradictions

### Blockers / critical path

converter-reference.md and `<graphic>` support in teiCrafter are missing, so the SZD export
waits; the ZBZ image URL schema is pending (`docs/images/<id>/<id>_p00N.png` plus possibly
an IIIF counterpart).

### Open in zbz

M5 scholarly curation (streams still at the `unverifiziert` handover default); O8 header
metadata from Alma, many headers with an empty container/journal title (spec conflict with
the edition guidelines, deliberate per E76); O13 editorial details; O18 multimodal OCR correction untested;
containerization/CI-CD only drafted; facsimiles online for only 4 demo docs; LLM variance
unmeasured (`stability: open`).

### Open in szd

0 real GT; layout only ~25/2,000; some API errors in the werke batch.

### Open in teiCrafter (future)

Real IIIF tiles; apparatus/note authoring; authority IDs; Page-JSON -> TEI; raw XML source
view; in-browser full validate; segmented loading of large editions.

### Documentation contradictions / outdated (re-checked 2026-06-10)

- zbz: status levels (E77) and the E counter are updated across all docs (fixed 2026-06-10).
  Still open: the JSZip ZIP bundle (E61) is not integrated (single export exists).
  `data/curated_tei/` has been declared correctly since 2026-06-10 (intended for hand-verified
  TEI, currently empty; previously misleadingly labeled a gold standard).
- szd: object counts vary across documents (1319...2107; authoritative 2,107); model IDs
  ("Gemini 3.1 Flash Lite", "Claude Opus 4.6") and session dates sit in a projected 2026
  timeline; `teicrafter-integration.md` (06/2026) reactivates the TEI converter contract
  deleted in session 21 (newer document = valid); the README claim "METS planned" is
  outdated (implemented since session 25).
- teiCrafter: token prefix drift in the docs (`--tc-*` outdated, the code uses `--color-*`);
  the 2026-06-04 audit repaired among other things the never-defined
  `--color-ai`/`--radius-sm` (the AI violet had silently failed).

---

## 10. Sources and SSoT Mapping

| Domain | SSoT |
|---|---|
| Contracts, gates | `teiCrafter/knowledge/integration.md` (canonical) |
| zbz pipeline/workflow/quality/decisions | `zbz-ocr-tei/knowledge/{pipeline,workflow,specification,decisions,methodology,project}.md` |
| zbz viewer function / frontend requirements | `zbz-ocr-tei/knowledge/workflow.md` (viewer), `zbz-ocr-tei/knowledge/specification.md` (open findings) |
| szd pipeline/verification/data | `szd-htr/knowledge/{data-overview,verification-concept,htr-interchange-format,page-xml-mets-architecture,evaluation-results,annotation-protocol}.md` |
| teiCrafter spec/architecture/stories/tests | `teiCrafter/knowledge/{specification,architecture,user-stories,testing,design,data}.md` |

This document is a synthesis (point-in-time). In case of conflict the respective domain SSoT
prevails.
