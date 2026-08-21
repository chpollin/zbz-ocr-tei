---
title: Workflow + Data Flow
project:
  name: zbz-ocr-tei
  repository: https://github.com/chpollin/zbz-ocr-tei.git
method:
  name: Promptotyping
  url: https://dhcraft.org/Promptotyping/
template:
  name: Vorlage Architecture
  version: 0.3
  url: https://dhcraft.org/Promptotyping/promptotyping-document/architecture
status: complete
language: en
version: 1.0
created: 2026-05-25
updated: 2026-08-21
authors: [Christopher Pollin]
related: [pipeline, design, tei-mapping, data, specification, plan, integration, infrastructure]
---

# Workflow + Data Flow

End to end from PDF to curated TEI. This document describes the data flow between the
stages, the format each stage produces, the viewer with its editors, the persistence
model and the provenance record as they are built today. Pipeline stages and engines are
in [pipeline.md](pipeline.md), the markup rules in [tei-mapping.md](tei-mapping.md), the
design rationale of the UI in [design.md](design.md), the architecture decisions in
[decisions.md](decisions.md), and the planned extensions in [plan.md](plan.md).

## Data Flow Diagram

```
PDF
 |
 v
Images (PNG 300 dpi)
 |
 +------------------------------------------+
 v                                          v
OCR (Mistral / Gemini-corrected)           Layout (Docling + Gemini QA)
 |                                          |
 |   +--------------------------------------+
 |   |                                      |
 |   v                                      v
 |   PAGE-XML (rule-based)                  |
 |   = parallel export                      |
 |   for coOCR compatibility                |
 |   NOT TEI input                          |
 |                                          |
 |                                          v
 +--------> TEI-XML (Unified: scaffold + Gemini refinement + assembly)
            |
            v
            output/tei_final/{doc}_final.xml + {doc}_manifest.json
            (workflow status per stream, E66/E67; replaces the former agent screening)
            |
            v
            docs/data/pages/{doc}/ (generated mirror, incl. {doc}_final.xml)
            |
            v
            Viewer (inspection + correction)
            |
            v
            "Save" -> output/ (canonical, pipeline) + docs/data/ (mirror, reload), E78/E79
            |
            v
            (pipeline re-run --reassemble folds the curation into the final TEI)
```

The TEI comes directly from layout JSON plus OCR Markdown (E22, a recurring misreading), while PAGE-XML runs beside it as an export for coOCR and Transkribus; the
clarification with its generating scripts is in [pipeline.md](pipeline.md), overview
section.

## Data Formats per Stage

| Stage | Format | Main path | Source |
|---|---|---|---|
| Source PDF | PDF | `data/source/pdf/{doc}.pdf` | ZBZ delivery (E23) |
| Facsimile | PNG 300 dpi | `docs/images/{doc}/{doc}_pNNN.png` | `scripts/edition/extract_pages.py` |
| Doc metadata | JSON | `data/doc_metadata.json` | `scripts/ocr/classify_docs.py` (Gemini, E27) |
| OCR (base text layer) | Markdown per page | `output/mistral_results/{doc}_pN.md` | `scripts/ocr/ocr_pipeline.py` |
| OCR (Gemini A/B) | Markdown, corrected | `output/gemini_corrected_a/`, `_b/` | `scripts/ocr/gemini_ocr_correct.py` (E29) |
| Layout (Docling) | JSON, bbox in % | `output/layout/{doc}/{doc}_pNNN_layout.json` | `scripts/layout/run_layout_analysis.py` or `run_layout_cloud.py` |
| Layout QA (Gemini) | JSON | `output/layout/{doc}/{doc}_pNNN_layout_gemini.json` | `scripts/layout/layout_qa_gemini.py` (E25/E26) |
| Overlay PNG | PNG | `output/overlay/{doc}/...` | `scripts/layout/generate_layout_overlays.py` |
| PAGE-XML | XML 2013-07-15 | `output/page_xml/{doc}/{doc}_pNNN.xml` | `scripts/layout/page_xml_generator.py` (E13) |
| METS | XML | `output/page_xml/{doc}/mets.xml` | `scripts/layout/mets_generator.py` |
| TEI scaffold (Step 1) | XML, rule-based | `output/tei_unified/{doc}_step1.xml` | `scripts/tei/tei_step1.py` |
| TEI Gemini (Step 2) | XML, LLM-refined | `output/tei_unified/{doc}_step2.xml` | `scripts/tei/tei_step2.py` |
| TEI assembly (Step 3) | XML, post-processed | `output/tei_unified/{doc}.xml` | `scripts/tei/tei_step3.py` |
| TEI final | XML with `<revisionDesc>` | `output/tei_final/{doc}_final.xml` | `scripts/tei/tei_status_marker.py` (E42, E43, E66) |
| Per-object manifest | JSON (workflow status + history per stream) | `output/tei_final/{doc}_manifest.json` | `scripts/edition/page_manifest.py` (E65/E66) |
| TEI final (frontend) | XML | `docs/data/pages/{doc}/{doc}_final.xml` | `scripts/edition/generate_edition_data.py` |
| TEI per page (frontend) | XML (split via `<pb>`) | `docs/data/pages/{doc}/{doc}_pN.xml` | ditto (E57) |
| Catalog (frontend) | JSON | `docs/data/catalog.json` | ditto |
| Thumbnails (frontend) | JPG 140x200 q70 | `docs/data/thumbs/{doc}.jpg` | ditto |
| Curated TEI | XML | `data/curated_tei/{doc}/` | manual (currently empty + `.gitkeep`) |

## The Viewer

Internal web UI for inspection and curation of the pipeline results (OCR, layout, TEI).
Since E56 it replaces the earlier public edition and the separate diagnostics and CER
dashboards. It serves the QA of the OCR, layout and TEI results, the manual correction by a
human in the loop, and the demonstration to ZBZ. The viewer shows the delivered data
layer, which is the Mistral OCR text; the engine comparison that used to live here sits
outside the viewer since E64 (CER benchmark plus the method page, E62). The public reading
edition is ZBZ's own step through Oxygen and Alma.

### Pages and Modes

Six pages:

| Page | Content |
|---|---|
| `index.html` | corpus overview: filterable and sortable document list with workflow status per stream (E66), status legend, search |
| `viewer.html` | document detail: facsimile + layout overlay left, transcription/TEI right, three views |
| `entities.html` | corpus-wide entity overview per listed entity and per document (entity layer section) |
| `methode.html` | CER method page: headline, stratified values, limitations, literature comparison (E62, static) |
| `about.html` | project page, points to the method page for quality detail |
| `impressum.html` | legal notice |

Since E107 the text panel header carries two dropdowns instead of scattered
panel controls. The View menu (`#view-menu`) selects what the panel shows and
holds the markup toggle:

| View | Content |
|---|---|
| Text (default) | annotated reading view: rendered TEI with GND entity marks and review candidates |
| OCR | raw OCR text of the page (Mistral) |
| XML | TEI-XML source, the current page by default, the whole document on request |
| Markup highlights | menu toggle that highlights foreign text, footnotes and editorial interventions and shows the legend |

The Edit menu (`#edit-menu`) switches the editing modes:

| Mode | Editable | Persistence |
|---|---|---|
| Layout | regions on the facsimile (bbox, type, order) | "Save" (all streams at once, persistence section) |
| OCR | raw OCR text of the page | "Save" (all streams at once, persistence section) |
| XML | TEI-XML source of the whole document | "Save" (all streams at once, persistence section) |

The two menus replace the per-panel edit toggles of E60/E78; a checked menu
item carries the active state. In layout editing a second toolbar appears with
region tools (add region, delete, type dropdown). Page navigation (prev / page info
/ next, plus a go-to-page field and Home/End keys) sits in the facsimile
panel header next to the region count (E78). The facsimile renderer in view
mode is OpenSeadragon (E58, pan + zoom + rotate); polygon support is
deliberately excluded (E59), rectangles suffice for the Hersch print
material. The layout editor works on the static `<img>` overlay; wiring it to the
OpenSeadragon coordinate system is tracked in [plan.md](plan.md).

### Architecture

```
docs/
├── index.html                   # corpus overview
├── viewer.html                  # document detail, 3 views (E107)
├── entities.html                # corpus-wide entity overview
├── methode.html                 # CER method page (static)
├── about.html                   # project page
├── impressum.html               # legal notice
├── assets/
│   ├── css/
│   │   ├── tokens.css               # Hersch design tokens (--h-*)
│   │   ├── fonts.css                # @font-face of the three vendored families
│   │   ├── base.css                 # reset, typography, buttons, badges, skip link, reduced motion
│   │   ├── viewer.css               # viewer shell, facsimile overlay, TEI render, editor UI
│   │   ├── catalog.css              # corpus overview: status bar, filters, doc table
│   │   └── entity-overview.css      # entity overview page
│   ├── fonts/                       # EB Garamond, Jost, JetBrains Mono as WOFF2 + OFL texts
│   ├── vendor/
│   │   └── openseadragon/           # OpenSeadragon 5.0.1 build + button sprites + BSD-3 license
│   └── js/
│       ├── core.js                  # DOM, URL, fetch, fold, cache, toast, event bus, markdown renderer
│       ├── viewer-state.js          # shared ZBZ.Viewer.state, DOM refs, page cache, asset bookkeeping
│       ├── viewer-entities.js       # entity preview, candidate marking, mention popover
│       ├── viewer-status.js         # workflow status per stream, manifest history, identity chip
│       ├── viewer-persist.js        # save, export, repo folder connection
│       ├── viewer-page.js           # facsimile, layout overlay, text panel, view and edit modes
│       ├── viewer.js                # viewer shell: init, doc selection, dropdowns, event wiring
│       ├── catalog.js               # corpus overview: loading, filters (stream x status, E66), sorting
│       ├── tei-render.js            # TEI-XML -> DOM
│       ├── layout-editor.js         # bbox drag/resize/add/delete + reading order
│       ├── transcription-editor.js  # OCR/TEI/XML with contenteditable
│       ├── fs-access.js             # direct write into the working tree (File System Access API, E72)
│       ├── download.js              # file download (JSON/MD/XML)
│       └── entity-overview.js       # entity overview page
├── data/                        # generated via scripts/edition/generate_edition_data.py (and the entity generators)
│   ├── catalog.json             # doc list with streams.{ocr,layout,tei,entities}.{status,last_at,last_by}
│   ├── manifests/{doc}_manifest.json  # mirror of the per-object manifests (workflow + history + blank pages, E66)
│   ├── manifest_index.json      # the `streams` block of every manifest in one file
│   ├── cer_statistics.json      # published CER statistics (versioned evidence, seed 42)
│   ├── entities.json            # entity lookup (gid -> label, category, dates, lobid link)
│   ├── entity_overview.json     # per-document entity overview for entities.html
│   ├── thumbs/{doc}.jpg         # catalog thumbnails
│   └── pages/                   # per-page mirror: layout JSONs + Mistral OCR + per-page TEI + entity preview
├── images/{doc}/{doc}_pNNN.png  # facsimiles (gitignored apart from the demo documents)
└── .nojekyll                    # GitHub Pages serves the tree as is
```

All JS modules are IIFEs in the `ZBZ.*` namespace; no npm/build pipeline. The
viewer is six such modules loaded as classic scripts in the order of the tree
above, `viewer-state.js` first because it creates the namespace, the shell
`viewer.js` last because it wires the events. They share the mutable
`ZBZ.Viewer.state` and reach each other through `ZBZ.Viewer`, resolved at call
time so the load order stays the only ordering constraint. State changes several
modules react to travel as `ZBZ.bus` events, `doc:changed` (the status module
loads the manifest), `page:changed` (the entity module drops its popover),
`dirty:changed` (the persistence module re-renders the Save button) and
`entity-mode:changed` (the page module re-syncs the two dropdowns).

OpenSeadragon 5.0.1 for the facsimile in view mode (E58) and the three web font families
are served from `docs/assets/` with their license texts, so every page loads from its own
origin; [infrastructure.md](infrastructure.md) owns that decision and its reasoning.

The style layer is the Hersch design system. `tokens.css` is the authority for every
value, `base.css` carries the component layer and `viewer.css` and `catalog.css` the
app-specific code; the rationale behind the palette, typography and signal rules is in
[design.md](design.md).

The corpus overview reads the workflow status of all documents from
`docs/data/manifest_index.json`, which the mirror step of
`generate_edition_data.py` writes as the `streams` block of every manifest under
its document id. A deploy without the file falls back to reading the manifests
one by one, so an older mirror still shows correct traffic lights.

Deployment of the viewer (GitHub Pages, local server, facsimile hosting limits) is
described in [infrastructure.md](infrastructure.md), viewer deployment section.

### Layout Editor

| Operation | Interaction |
|---|---|
| select region | click |
| move region | drag |
| resize region | drag a corner handle (NW/NE/SW/SE) |
| change region type | dropdown in the toolbar (Heading/Paragraph/Footnote/Caption/Filter/Skip) |
| add region | toolbar add button, then draw on empty facsimile area |
| delete region | Delete key or toolbar button |
| change reading order | drag and drop in the region list below the facsimile |

Pointer events cover mouse, touch, and pen; arrow keys nudge the selected
region (1%, Shift 5%). Coordinates are percentages (0-100) relative to the
image, compatible with the layout JSON format
(`bbox.x_pct/y_pct/w_pct/h_pct`).

Region types map onto the pipeline `zbz_tag` vocabulary, and their colours come from the
status colours of `docs/assets/css/tokens.css`; the reasoning behind the colour roles is
in [design.md](design.md).

| `zbz_tag` | Label | Colour |
|---|---|---|
| `zb_heading` | Heading | brick red |
| `zb_paragraph` | Paragraph | anthracite |
| `footnote` | Footnote | Prussian blue |
| `caption` | Caption | olive green |
| `_filter` | Filter (remove) | gray, dashed |
| `_skip` | Skip | light gray, dotted |

### Transcription Editor

Edits the text panel via `contenteditable` (with textbox ARIA roles). Since
E107 the Edit menu offers two text targets beside layout:

| Target | Format | What is edited |
|---|---|---|
| OCR | Markdown | raw OCR text of the page |
| XML | TEI-XML with syntax highlighting, whole document | raw XML including tags and attributes; saving replaces `{doc}_final.xml` as a whole (E72), a guard refuses incomplete TEI content |

The annotated reading view stays read-only; wording and structure changes run
through XML mode.

Changes are collected debounced and marked unsaved; the shared "Save" button
persists them together with layout and status (persistence section). Per-stream single
files are available via the "Export" dropdown (E78).

### Blank Pages (E63/E65/E67)

Cover, backing, and carbon-copy pages yield junk OCR only, and the Gemini
layout QA hallucinates phantom regions there (Docling correctly reports
zero). The safe blank class lives in the per-object manifest
(`page_manifest`, OCR rule + Docling=0) and is projected into the final TEI
as `<pb type="blank"/>` by `tei_blank_marker.py` (E65). Detection in the
viewer (`detectBlankPage` in `viewer.js`) reads that marker from the
per-page TEI as the primary source; only pages without TEI fall back to the
OCR heuristic `ZBZ.isBlankPageText` (trimmed text of at most 5 characters or
without letters/digits). The marking truth therefore lives in the TEI and
the manifest; the viewer only projects it. On blank pages the facsimile
header and the text panel show a quiet blank-page notice and phantom boxes
are suppressed. Details: [decisions.md](decisions.md) E63/E65/E67.

### Workflow Status per Stream (E66/E67/E77)

Replaces the abolished agent screening (E66; none of the earlier "APPROVED"
labels came from a human). Three status values per data stream (`ocr`,
`layout`, `tei`); the stored data values are German and invariant, the UI
translates only the display labels:

| Status (data value) | Meaning | UI traffic light |
|---|---|---|
| `unverifiziert` | pipeline output exists, no human has verified (default) | neutral/gray |
| `in_arbeit` | at least one human review/correction begun, not released | yellow |
| `verifiziert` | human-checked and released, edition-ready | green |

Red stays reserved for a future explicit problem/reject status. The default
is neutral because the pipeline produces OCR/layout/TEI deterministically
for every document; "present, unverified" is not an alarm (E67). Status is
set in the viewer via the status pills in the document bar (OCR, Layout,
TEI, and Entities wherever an entity preview exists); a click cycles forward
through the three values. The editor identity (initials) sits as a chip next
to the Save button and goes into the manifest history (`{at, by, from,
to}`), which is the provenance record of the human editing steps. The first
real change in an editor auto-transitions the matching stream from
`unverifiziert` to `in_arbeit`; deliberate transitions (for example to
`verifiziert`) happen via the pill.

`page_manifest.py` creates the fourth stream `entities` only where an entity
preview exists, and keeps it once created. It carries the same three values,
but it states the review state of the read-only preview layer rather than of
the delivered TEI (entity layer section), which is why `tei_status_marker.py`
projects only `ocr`, `layout` and `tei` into the `<revisionDesc>`. That projection
runs at ZBZ handover, writes the history deterministically as `<change>` entries,
backs the file up first and removes stale agent-screening entries; its XML shape is
in [tei-mapping.md](tei-mapping.md), revision description section. Data model and
commands: CLAUDE.md, per-object manifest section; decisions E66/E77.

### Entity Layer (read-only)

The viewer shows the GND entity markup of a document as a read-only inspection
layer. Since E107 the annotated reading view is the default for every document;
`viewer.html?doc={DOC_ID}&entities=0` opts out (`viewer.js`, state default and
URL read). The layer sits outside every edit and
save path; the preview path leaves `output/tei_final/` untouched, and in entity
mode the text editors stay locked (layout editing remains available).

The data come from the generated mirror.
`scripts/entity/generate_entity_preview_data.py` reads the previews in
`output/entity_preview/` read-only and writes per document
`docs/data/pages/{doc}/{doc}_entity_p{N}.xml`, the preview split per page with
the same splitter the TEI mirror uses, so an entity page sits next to the same
facsimile as `{doc}_pN.xml`. Beside it lands
`docs/data/pages/{doc}/{doc}_entity_worklist.json` with the tier-2 candidates
grouped per page. Corpus-wide the generator writes the lookup
`docs/data/entities.json` (label, category, life dates, lobid link per GND id),
which the viewer resolves `ref="GND:..."` against; the ids come exclusively from
the curated entity list. A page without an entity preview falls back to the
pipeline TEI, so navigation stays intact.

On an entity page the legend splits into the three GND categories (persons,
organisations, works) plus a chip for the candidates. Marked mentions act as
buttons, and the popover carries label, category, life dates, and the link to
lobid.org. Tier-2 candidates are marked inline as well and open the same
popover, which additionally names the reason the tool held back ("For review")
and the origin of the matched name form; where several listed bearers carry the
form, the popover lists all of them, so the position stays visibly undecided.
For a mark the matcher set, the popover closes with three provenance rows read from
the mention itself, `@resp`, `@cert` and `@source`, which `tei-render.js` carries into
the DOM as data attributes (E118). What those attributes assert, which tier produced a
mark and which rules bind the markup is in [tei-mapping.md](tei-mapping.md), entities
section. Candidates the renderer cannot place inline stay visible as a list above the
text, so the page shows the complete worklist either way.

Wherever an entity preview exists, `page_manifest` adds a fourth stream
`entities` to the per-object manifest; its status pill sits next to OCR, Layout
and TEI in the doc subbar and carries the same three status values as the
pipeline streams (workflow status section). The markup rules and the target model are
in [tei-mapping.md](tei-mapping.md), the instrument inventory of the stage in
[pipeline.md](pipeline.md), the measured precision and recall in
[verification.md](verification.md), and the open milestones in [plan.md](plan.md).

The corpus-wide complement is the overview page `docs/entities.html`, built as
a completeness instrument for the developer question "do we have every listed
entity". The primary view aggregates per listed entity, including every list
entry without a single corpus mention (sorted first by default), with
auto-marked against review counts and the documents each entity occurs in; the
secondary view aggregates per document with the review classes as tooltip
chips. Certainty is carried by the two-color bar (auto-marked against review),
the corpus totals sit on the same bar above the list, and every row links into
the viewer's annotated reading view. The page reads
`docs/data/entity_overview.json`, generated deterministically by
`scripts/entity/generate_entity_overview.py` from the corpus scan and the
curated list; the closed-world gate covers its ids like every other mirror
file. Deliberately absent after operator feedback: stat cards, intro copy,
class-definition prose (tooltips instead), the workflow-status dot, and the
adjudicated evaluation sample, which is measurement evidence rather than a
record of the operator's own review.

## Persistence in the Viewer

The viewer (`docs/viewer.html`) is a static single-page app without a
backend. A single "Save" button writes changes directly into the repo clone
(File System Access API, Chromium) or as a file download (fallback) and mirrors them
at the same time into the viewer mirror, so that a reload shows the state (E72/E78/E79).

### Read Path (read-only)

The viewer loads static files exclusively. The path resolver in
`docs/assets/js/core.js` uses a two-level fallback chain:

```
1. docs/data/pages/{doc}/{doc}_pN.{ext}   (frontend mirror, whole corpus)
2. ../output/{stage}/...                  (local fallback for engines not in the mirror)
```

This makes the viewer work on GitHub Pages for the entire corpus. Locally,
Gemini A/B and LLM correction are additionally reachable.

### Save Mechanism (one Save Writes to Repo + Mirror)

A single save button secures all unsaved streams at once (layout, text/TEI,
manifest with workflow status; `saveAll()` in `viewer.js`). The write path is the File System Access
API (`ZBZ.FsAccess`, Chromium); without it, the file download takes over (`ZBZ.Download`,
Firefox/Safari). Every save action writes the identical payload to two places,
canonically to `output/` (pipeline consumption) and to the mirror `docs/data/` (viewer reload, E79):

| Stream | Canonical (`output/`) | Mirror (`docs/data/`) | Module |
|---|---|---|---|
| Layout | `layout/{doc}/{doc}_p{NNN}_layout_curated.json` | `pages/{doc}/{doc}_p{NNN}_layout_curated.json` | `ZBZ.FsAccess.writeLayout()` |
| Text | `ocr_curated/{doc}_p{N}.md` | `pages/{doc}/{doc}_p{N}.md` | `ZBZ.FsAccess.writeText()` |
| Manifest | `tei_final/{doc}_manifest.json` | `manifests/{doc}_manifest.json` | `ZBZ.FsAccess.writeManifest()` |
| TEI | `tei_final/{doc}_final.xml` | `pages/{doc}/{doc}_final.xml` | `ZBZ.FsAccess.writeTei()` |

On first save the viewer asks once for the repo root folder (first-run info
modal explaining which folder and what gets written), keeps the directory
handle in IndexedDB, and re-requests write permission per session by user
gesture (browser trust model). A plausibility check (`looksLikeRepoRoot`:
`docs/` plus `scripts/` present) warns on a wrong folder choice. If the
download fallback kicks in, the save message says so explicitly instead of
pretending a repo write. Pipeline precedence: `load_layout_gemini` reads
curated > gemini > docling, and `OCR_CURATED_DIR` is the first element in
`_OCR_DIRS` (`scripts/core/loaders.py`); the viewer probes the same order
(E79). `generate_edition_data --mirror-only` reproduces exactly the same
mirror files, so there is no drift.

Individual export per stream remains available via the "Export" dropdown (`ZBZ.Download.*`, E78).

Three properties follow from that design. Write permission is granted per session by a
user gesture, so a save always happens under an explicit browser grant. The browser state
is the truth for an open document, and where two people edit the same document in
parallel the later save wins. XML mode loads the whole document, because the per-page
splits in the mirror are produced by `--reassemble`, and a guard in `saveAll()` refuses
content without a `teiHeader` or `TEI` root; a direct TEI-XML edit therefore replaces the
source of truth as a whole and a later `--reassemble` regenerates the page splits from it.
The wrapper that would run the pipeline steps after a save is planned in
[plan.md](plan.md), round-trip wrapper.

### Round Trip from User Edit to Regenerated TEI

Complete procedure when a user has corrected a layout region:

1. Edit in the viewer: the user activates the layout edit toggle and corrects a bbox.
2. Save: clicking "Save" writes `{doc}_p{NNN}_layout_curated.json` directly to `output/layout/{doc}/` (canonical) AND to the mirror `docs/data/pages/{doc}/` (E78/E79); the first time, the viewer asks once for the repo folder. A reload shows the state immediately.
3. Pipeline re-run with curated layout data as input:
   ```bash
   python -m scripts.tei.tei_unified --doc {ID} --reassemble
   ```
   This is the run that actually consumes the files saved in step 2; what `--reassemble` redoes and how it uses the Gemini Step 2 cache is described in [methodology.md](methodology.md), conventions section. The consequence for the curating user is that Gemini re-derives the text of every re-refined page, so a saved OCR correction acts as a suggestion and does not pass through verbatim. For word-exact text changes use the TEI-XML mode instead; it writes `output/tei_final/{doc}_final.xml` directly and deterministically, bypassing the pipeline.
4. revisionDesc update:
   ```bash
   python -m scripts.tei.tei_status_marker --doc {ID}
   ```
   Projects the human-set workflow status per stream from the manifest into the `<revisionDesc>` (E66); this is the step run at ZBZ handover.
5. Validation:
   ```bash
   python -m scripts.tei.tei_validator --doc {ID}
   ```
6. Regenerate frontend data:
   ```bash
   python -m scripts.edition.generate_edition_data --mirror-only
   ```
   Updates `docs/data/pages/{doc}/` (incl. `{doc}_final.xml`).

Steps 3 to 6 are run by hand today. A wrapper command that chains them is planned in
[plan.md](plan.md), round-trip wrapper.

## Provenance

### revisionDesc and Per-Object Manifest

| Store | Content | Where |
|---|---|---|
| `<revisionDesc>` in the TEI header (E42) | `<change>` elements: pipeline stages + versions + projected workflow status (E66) + date | every final TEI in `output/tei_final/` |
| `{doc}_manifest.json` (E65/E66) | workflow status per stream (`ocr`/`layout`/`tei`, plus `entities` wherever an entity preview exists) + history `[{at, by, from, to, note}]` + exception pages (blank pages) | `output/tei_final/` |
| Git log | file and code change history | repo |

The machine-readable editing log per object, the roll-back it would allow and the
self-contained `_complete.xml` that would carry the log inside the TEI are planned in
[plan.md](plan.md), phase B. The facsimile side of that plan is delivered already, since
the generator writes `<facsimile>` with one surface per page and body elements carry
`@facs` ([tei-mapping.md](tei-mapping.md), facsimile binding).

## References

- [pipeline.md](pipeline.md): pipeline stages, engines, entity stage
- [tei-mapping.md](tei-mapping.md): markup rulebook, revision description, entity target model
- [design.md](design.md): rationale of the Hersch design system and the UI signal rules
- [data.md](data.md): corpus, delivery tree, entity input data
- [specification.md](specification.md): requirements, quality method, validation rule catalog
- [plan.md](plan.md): planned provenance log, `_complete.xml`, export and viewer work
- [integration.md](integration.md): ZBZ, Transkribus and teiCrafter contracts
- [infrastructure.md](infrastructure.md): viewer deployment, vendored assets, CI
- [cer-methodology.md](cer-methodology.md): CER measurement method
- [decisions.md](decisions.md): decision register
- [methodology.md](methodology.md): Promptotyping, verification cascade, `--reassemble` conventions
- [journal.md](journal.md): chronological session history
- [index.md](index.md): navigation + key concepts
