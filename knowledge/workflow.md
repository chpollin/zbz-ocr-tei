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
updated: 2026-08-26
authors: [Christopher Pollin]
related: [index, project, pipeline, tei-mapping, specification, verification, decisions]
absorbed: [design (Vorlage Design 0.2)]
---

# Workflow + Data Flow

This document follows the data from the source PDF to the curated TEI as the system is
built today. It describes the flow between the stages, the format each stage produces,
the viewer with its editors, the persistence model, the provenance record, and the design
rationale by which the UI turns that data into visual signal. Pipeline stages and engines are in
[pipeline.md](pipeline.md), the markup rules in [tei-mapping.md](tei-mapping.md), and the
architecture decisions together with the planned extensions in
[decisions.md](decisions.md), decision register and plan section. Token values live in
`docs/assets/css/tokens.css`, which is their only authority; the design section names
roles and rules.

## Data Flow Diagram

```
PDF
 |
 v
Images (PNG 150 dpi)
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
            (pipeline re-run --reassemble rebuilds output/tei_unified/{doc}/{doc}_final.xml
             from the curated files; promoting it into output/tei_final/ is a separate step)
```

TEI is generated directly from layout JSON plus OCR Markdown (E22); PAGE-XML runs beside
that path as an export for coOCR and Transkribus. Reading PAGE-XML as a station on the way
to TEI is a recurring misreading. The same clarification with its generating scripts is in
[pipeline.md](pipeline.md), overview section.

## Data Formats per Stage

| Stage | Format | Main path | Source |
|---|---|---|---|
| Source PDF | PDF | `data/source/pdf/{doc}.pdf` | ZBZ delivery (E23) |
| Facsimile | PNG at `WEB_DPI` = 150 dpi (`--dpi` overrides) | `docs/images/{doc}/{doc}_pNNN.png` | `scripts/edition/extract_pages.py` |
| Doc metadata | JSON | `data/doc_metadata.json` | `scripts/ocr/classify_docs.py` (Gemini, E27) |
| OCR (base text layer) | Markdown per page | `output/mistral_results/{doc}_pN.md` | `scripts/ocr/ocr_pipeline.py` |
| OCR (Gemini A/B) | Markdown, corrected | `output/gemini_corrected_a/`, `_b/` | `scripts/ocr/gemini_ocr_correct.py` (E29) |
| Layout (Docling) | JSON, bbox in % | `output/layout/{doc}/{doc}_pNNN_layout.json` | `scripts/layout/run_layout_analysis.py` or `run_layout_cloud.py` |
| Layout QA (Gemini) | JSON | `output/layout/{doc}/{doc}_pNNN_layout_gemini.json` | `scripts/layout/layout_qa_gemini.py` (E25/E26) |
| Overlay PNG | PNG | `output/layout/{doc}/{doc}_pNNN_overlay_gemini.png`, with `--compare` also `_overlay_compare.png` | `scripts/layout/generate_layout_overlays.py` |
| PAGE-XML | XML 2013-07-15 | `output/page_xml/{doc}/page/{doc}_pNNN.xml` | `scripts/layout/page_xml_generator.py` (E13) |
| METS | XML | `output/page_xml/{doc}/mets.xml` | `scripts/layout/mets_generator.py` |
| TEI scaffold (Step 1) | XML per page, rule-based | `output/tei_unified/{doc}/{doc}_pNNN_scaffold.xml` | `scripts/tei/tei_step1.py` |
| TEI Gemini (Step 2) | XML per page, LLM-refined | `output/tei_unified/{doc}/{doc}_pNNN_refined.xml` | `scripts/tei/tei_step2.py` |
| TEI assembly (Step 3) | XML, whole document | `output/tei_unified/{doc}/{doc}_final.xml` | `scripts/tei/tei_step3.py` |
| TEI final (delivered) | XML with `<revisionDesc>` | `output/tei_final/{doc}_final.xml` | the assembly promoted into `tei_final/`; the `<revisionDesc>` is written by `scripts/tei/tei_status_marker.py` (E42, E43, E66) |
| Per-object manifest | JSON (workflow status + history per stream) | `output/tei_final/{doc}_manifest.json` | `scripts/edition/page_manifest.py` (E65/E66) |
| TEI final (frontend) | XML | `docs/data/pages/{doc}/{doc}_final.xml` | `scripts/edition/generate_edition_data.py` |
| TEI per page (frontend) | XML (split via `<pb>`) | `docs/data/pages/{doc}/{doc}_pN.xml` | ditto (E57) |
| Catalog (frontend) | JSON | `docs/data/catalog.json` | ditto |
| Thumbnails (frontend) | JPG 140x200 q70 | `docs/data/thumbs/{doc}.jpg` | ditto |
| Curated TEI | XML | `data/curated_tei/` | manual; the folder is reserved for hand-verified TEI and currently holds only `.gitkeep` |

## The Viewer

The viewer is the internal web UI for inspecting and curating the pipeline results, the
OCR text, the layout and the TEI. Since E56 it stands in place of the earlier public
edition site, the curation editor and the separate diagnostics and CER dashboards. It
serves the quality assurance of those three results, the manual correction by a human in
the loop, and the demonstration to ZBZ. The viewer shows the delivered data layer, which
is the Mistral OCR text; the engine comparison that used to live here sits outside the
viewer since E64, in the CER benchmark and on the method page (E62). The public reading
edition is ZBZ's own step through Oxygen and Alma.

### Pages and Modes

The site consists of six pages.

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
item carries the active state. In layout editing a second toolbar appears inside the
document bar with the region tools, an add and a delete button, the region type
dropdown, four number fields for the bounding box of the selected region in percent,
and the region count. Page navigation sits in the facsimile panel header and consists of
a previous and a next button around an editable page-number field that also shows the
page total (E78); the arrow keys page, Home and End jump to the first and last page. The
facsimile renderer in view mode is OpenSeadragon (E58, pan, zoom and rotate). Polygon
support is deliberately excluded (E59), because rectangles suffice for the Hersch print
material. The layout editor works on the static `<img>` overlay; wiring it to the
OpenSeadragon coordinate system is tracked in [decisions.md](decisions.md), plan section.

Both menus are keyboard operable. Opening a menu moves focus to its first item, arrow
keys move focus within the roving tabindex, Home and End jump to the ends, and Escape
closes the menu and returns focus to the trigger. The dialog that explains the
working-tree connection is a native `<dialog>` opened with `showModal`. Every page
carries a skip link that stays screen-reader-only until it takes focus and then becomes
visible chrome. The reasoning behind these choices is in the design section, interaction
patterns.

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
│       ├── core.js                  # DOM, URL, fetch + path resolver, fold, XML helpers, cache, toast, event bus, markdown renderer
│       ├── viewer-state.js          # shared ZBZ.Viewer.state, DOM refs, page cache, asset bookkeeping
│       ├── viewer-entities.js       # entity preview, candidate marking, mention popover
│       ├── viewer-status.js         # workflow status per stream, manifest history, identity chip
│       ├── viewer-persist.js        # save, export, repo folder connection
│       ├── viewer-page.js           # facsimile, layout overlay, text panel, view and edit modes
│       ├── viewer.js                # viewer shell: init, doc selection, dropdowns, event wiring
│       ├── catalog.js               # corpus overview: loading, search, filters (language, type, form, stream x status, E66), sorting
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
│   ├── entity_overview.json     # entity overview for entities.html (per listed entity and per document, totals, adjudicated quality, provenance)
│   ├── thumbs/{doc}.jpg         # catalog thumbnails
│   └── pages/                   # per-page mirror: layout JSONs, Mistral OCR, per-page TEI, whole final TEI, {doc}_facs.json (page to scan image), entity preview + worklist
├── images/{doc}/{doc}_pNNN.png  # facsimiles (gitignored apart from the demo documents)
└── .nojekyll                    # GitHub Pages serves the tree as is
```

All JS modules are IIFEs in the `ZBZ.*` namespace; no npm/build pipeline. The
viewer is six such modules loaded as classic scripts in that relative order,
`viewer-state.js` first because it creates the namespace, the shell
`viewer.js` last because it wires the events. They share the mutable
`ZBZ.Viewer.state` and reach each other through `ZBZ.Viewer`, resolved at call
time so the load order stays the only ordering constraint. State changes several
modules react to travel as `ZBZ.bus` events, `doc:changed` (the status module
loads the manifest), `page:changed` (the entity module drops its popover),
`dirty:changed` (the persistence module re-renders the Save button) and
`entity-mode:changed` (the page module re-syncs the two dropdowns).

OpenSeadragon 5.0.1 for the facsimile in view mode (E58) and the three web font families
are served from `docs/assets/` with their license texts, so every page loads from its own
origin; [pipeline.md](pipeline.md), deployment section, owns that decision and its
reasoning.

The style layer is the Hersch design system. `tokens.css` is the authority for every
value, `base.css` carries the component layer and `viewer.css` and `catalog.css` the
app-specific code; the rationale behind the palette, typography and signal rules is in
the design section below.

The corpus overview reads the workflow status of all documents from
`docs/data/manifest_index.json`, which the mirror step of
`generate_edition_data.py` writes as the `streams` block of every manifest under
its document id. A deploy without the file falls back to reading the manifests
one by one, so an older mirror still shows correct traffic lights.

Deployment of the viewer (GitHub Pages, local server, facsimile hosting limits) is
described in [pipeline.md](pipeline.md), deployment section.

### Layout Editor

| Operation | Interaction |
|---|---|
| select region | click |
| move region | drag |
| resize region | drag a corner handle (NW/NE/SW/SE) |
| set the bbox numerically | the four percent fields X, Y, W, H in the toolbar |
| change region type | dropdown in the toolbar (Heading/Paragraph/Footnote/Caption/Filter/Skip) |
| add region | toolbar add button, then draw on empty facsimile area |
| delete region | Delete or Backspace key, or the toolbar button |
| change reading order | drag and drop in the region list below the facsimile |

Pointer events cover mouse, touch and pen. Arrow keys nudge the selected region by one
percent, five with Shift held; Escape cancels a region being drawn and otherwise clears
the selection. Coordinates are percentages from 0 to 100 relative to the image, which is
the layout JSON format (`bbox.x_pct/y_pct/w_pct/h_pct`).

Region types map onto the pipeline `zbz_tag` vocabulary, and their colours come from the
status colours of `docs/assets/css/tokens.css`; the reasoning behind the colour roles is
in the design section, visualization logic.

| `zbz_tag` | Label | Colour |
|---|---|---|
| `zb_heading` | Heading | brick red |
| `zb_paragraph` | Paragraph | anthracite |
| `footnote` | Footnote | Prussian blue |
| `caption` | Caption | olive green |
| `_filter` | Filter (remove) | gray, dashed |
| `_skip` | Skip | light gray, dotted |

### Transcription Editor

The transcription editor switches the text panel to `contenteditable` and exposes it to
screen readers as a multiline textbox. Since E107 the Edit menu offers two text targets
beside layout.

| Target | Format | What is edited |
|---|---|---|
| OCR | Markdown | raw OCR text of the page |
| XML | TEI-XML with syntax highlighting, whole document | raw XML including tags and attributes; saving replaces `{doc}_final.xml` as a whole (E72), guarded against incomplete and ill-formed TEI content |

The annotated reading view stays read-only, so wording and structure changes run through
XML mode.

Changes are collected debounced and marked unsaved, and the shared "Save" button persists
them together with layout and status (persistence section). Per-stream single files are
available via the "Export" dropdown (E78).

### Blank Pages (E63/E65/E67)

Cover, backing, and carbon-copy pages yield junk OCR only, and the Gemini
layout QA hallucinates phantom regions there (Docling correctly reports
zero). The safe blank class lives in the per-object manifest
(`page_manifest`, OCR rule + Docling=0) and is projected into the final TEI
as `<pb type="blank"/>` by `tei_blank_marker.py` (E65). Detection in the
viewer (`detectBlankPage` in `viewer-page.js`) reads that marker from the
per-page TEI as the primary source; only pages without TEI fall back to the
OCR heuristic `ZBZ.isBlankPageText` (trimmed text of at most 5 characters or
without letters/digits). The marking truth therefore lives in the TEI and
the manifest; the viewer only projects it. On a blank page the region count
is replaced by the label "Blank page, no text", the text panel shows the same
quiet notice instead of the OCR junk, and no region boxes are drawn.
The decisions behind this are E63, E65 and E67 in [decisions.md](decisions.md).

### Workflow Status per Stream (E66/E67/E77)

The workflow status replaces the abolished agent screening (E66; none of the
earlier "APPROVED" labels came from a human). Each data stream (`ocr`, `layout`,
`tei`) carries one of three values. The stored values are German and invariant;
the UI translates the display labels only.

| Status (data value) | Meaning | UI traffic light |
|---|---|---|
| `unverifiziert` | pipeline output exists, no human has verified (default) | neutral/gray |
| `in_arbeit` | at least one human review/correction begun, not released | yellow |
| `verifiziert` | human-checked and released, edition-ready | green |

Red stays reserved for a future explicit problem or reject status. The default
is neutral because the pipeline produces OCR, layout and TEI deterministically
for every document, so "present, unverified" describes a handover state and
raises no alarm (E67). Status is set in the viewer via the status pills in the
document bar (OCR, Layout, TEI, and Entities wherever an entity preview exists);
a click cycles forward through the three values. The editor identity (initials)
sits as a chip next to the Save button and goes into the manifest history
(`{at, by, from, to, note}`), which is the provenance record of the human editing
steps. The first real change in an editor auto-transitions the matching stream from
`unverifiziert` to `in_arbeit` with the note `auto: first edit in viewer`;
deliberate transitions, for example to `verifiziert`, happen via the pill.

`page_manifest.py` creates the fourth stream `entities` only where an entity
preview exists, and keeps it once created. It carries the same three values and
states the review state of the read-only preview layer (entity layer section).
The delivered TEI has no entity markup, so `tei_status_marker.py` projects
`ocr`, `layout` and `tei` alone into the `<revisionDesc>`. That projection
runs at ZBZ handover, writes the history deterministically as `<change>` entries,
backs the file up first and removes stale agent-screening entries; its XML shape is
in [tei-mapping.md](tei-mapping.md), revision description section. The data model and the
commands are in CLAUDE.md, per-object manifest section, the decisions in
[decisions.md](decisions.md) E66 and E77.

### Entity Layer (read-only)

The viewer shows the GND entity markup of a document as a read-only inspection
layer. Since E107 the annotated reading view is the default for every document;
`viewer.html?doc={DOC_ID}&entities=0` opts out (the flag lives in
`viewer-state.js`, the URL parameter is read in `viewer.js`). The layer sits
outside every edit and save path, and the preview generator leaves
`output/tei_final/` untouched. The annotated reading view itself carries no edit
entry point, because the transcription editor reads its rendered text only;
choosing OCR or XML in the Edit menu switches the panel to that source first, so
every editing mode stays reachable while entity mode is on.

The viewer reads the layer from the generated mirror.
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
For a marked mention the popover closes with provenance and rule rows read from `@resp`
and `@source`, which `tei-render.js` carries into the DOM as data attributes. Role labels
distinguish deterministic matching, AI-agent review, AI-agent annotation, independent LLM
review and editorial verification. The viewer does not infer a certainty level from these
activities (E131). What the roles assert, which tier produced a mark and which rules bind
the markup is in [tei-mapping.md](tei-mapping.md), entities section. Candidates the
renderer cannot place inline stay visible as a list above the text, so the page shows the
complete worklist either way.

The third, agentic phase remains outside the browser save path. An AI harness opens a
packet produced by `entity_agent_context.py`, which binds the page image, transcription,
TEI page, schema, guidelines and the page's candidate identities by SHA-256. The agent may
inspect those inputs, call the schema validator and request an independent LLM judgment.
`entity_agent_review.py` then checks the structured response against the closed candidate
set and writes a separate full-document preview plus the run record. The delivered TEI and
the viewer mirror change only through later operator-released paths.

Wherever an entity preview exists, `page_manifest` adds a fourth stream
`entities` to the per-object manifest; its status pill sits next to OCR, Layout
and TEI in the doc subbar and carries the same three status values as the
pipeline streams (workflow status section). The markup rules and the target model are
in [tei-mapping.md](tei-mapping.md), the instrument inventory of the stage in
[pipeline.md](pipeline.md), the measured precision and recall in
[verification.md](verification.md), and the open milestones in
[decisions.md](decisions.md), plan section.

The corpus-wide complement is the overview page `docs/entities.html`, built as
a completeness instrument for the developer question "do we have every listed
entity". The primary view aggregates per listed entity, including every list
entry without a single corpus mention (sorted first by default), with
auto-marked against review counts, the review classes as tooltip chips, the
documents each entity occurs in, and, where the entity appears only as the other
possible bearer of an ambiguous surface, a note counting those mentions (E117).
The secondary view aggregates per document with the same class chips. Annotation path
is carried by the two-colour bar (auto-marked against review), the corpus totals
appear in a bar of the same grammar above the list, and every row links into the
viewer's annotated reading view. Above the list a quality strip projects the agent-reviewed
sample from the verdict store, precision with its confidence interval, the raw
recall status counts, the second-judgment agreement, and a provenance line naming
the scan digest and the list size (E117); every rate stands next to its sample
size, because the sample is evidence about the corpus rather than a corpus-wide
fact. The page reads `docs/data/entity_overview.json`, generated
deterministically by `scripts/entity/generate_entity_overview.py` from the corpus
scan and the curated list; the closed-world gate
`tests/test_entity_ref_invariant.py` covers its ids like every other mirror file.
On operator feedback the page carries neither stat cards nor introductory explainer
copy nor a workflow-status dot, and the definitions of the review classes live in
tooltips.

## Persistence in the Viewer

The viewer (`docs/viewer.html`) is a static single-page app without a backend. A single
"Save" button writes changes directly into the repo clone through the File System Access
API on Chromium, or hands them over as a file download where that API is missing, and it
writes the same payload into the viewer mirror at the same time, so a reload shows the
saved state (E72/E78/E79).

### Read Path (read-only)

The viewer loads static files exclusively. The path resolver in
`docs/assets/js/core.js` uses a two-level fallback chain:

```
1. data/pages/{doc}/{doc}_pN.{ext}   (frontend mirror, whole corpus; docroot is docs/)
2. ../output/{stage}/...             (local fallback for engines outside the mirror)
```

This makes the viewer work on GitHub Pages for the entire corpus. Locally,
Gemini A/B and LLM correction are additionally reachable.

### Save Mechanism (one Save Writes to Repo + Mirror)

A single save button secures all unsaved streams at once, layout, text or TEI, and the
manifest with its workflow status (`saveAll()` in `viewer-persist.js`). The write path is
the File System Access API (`ZBZ.FsAccess`, Chromium); without it, the file download takes
over (`ZBZ.Download`, Firefox/Safari). Every save action writes the identical payload to
two places, canonically to `output/` for pipeline consumption and to the mirror
`docs/data/` for the viewer reload (E79).

| Stream | Canonical (`output/`) | Mirror (`docs/data/`) | Module |
|---|---|---|---|
| Layout | `layout/{doc}/{doc}_p{NNN}_layout_curated.json` | `pages/{doc}/{doc}_p{NNN}_layout_curated.json` | `ZBZ.FsAccess.writeLayout()` |
| Text | `ocr_curated/{doc}_p{N}.md` | `pages/{doc}/{doc}_p{N}.md` | `ZBZ.FsAccess.writeText()` |
| Manifest | `tei_final/{doc}_manifest.json` | `manifests/{doc}_manifest.json` | `ZBZ.FsAccess.writeManifest()` |
| TEI | `tei_final/{doc}_final.xml` | `pages/{doc}/{doc}_final.xml` | `ZBZ.FsAccess.writeTei()` |

On first save the viewer asks once for the repo root folder (first-run info
modal explaining which folder and what gets written), keeps the directory
handle in IndexedDB, and re-requests write permission per session by user
gesture (browser trust model). The plausibility check `looksLikeRepoRoot` warns on a wrong
folder choice, accepting a folder that contains `docs/` or `scripts/`. When the download
fallback takes over, the save message says so explicitly rather than reporting a repo
write. The pipeline reads the curated files with the same precedence the viewer probes
(E79), since `load_layout_gemini` prefers curated over gemini over docling and
`OCR_CURATED_DIR` is the first element of `_OCR_DIRS` (`scripts/core/loaders.py`).
`generate_edition_data --mirror-only` reproduces exactly the same mirror files, so there
is no drift.

Ctrl+S triggers the same save while an editor field holds the focus. Individual export per
stream remains available via the "Export" dropdown (`ZBZ.Download.*`, E78).

Several properties follow from that design. Write permission is granted per session by a
user gesture, so a save always happens under an explicit browser grant. The browser state
is the truth for an open document, and where two people edit the same document in
parallel the later save wins. XML mode loads the whole document, because the per-page
splits in the mirror are produced by `--reassemble`. Two guards in `saveAll()` protect the
source of truth, one refusing content without a `<teiHeader>` and a closing `</TEI>`, the
other refusing XML that is not well-formed; the offending edit stays unsaved in the editor.
A direct TEI-XML edit therefore replaces the source of truth as a whole, and a later
`--reassemble` regenerates the page splits from it. The wrapper that would run the pipeline
steps after a save is planned in [decisions.md](decisions.md), plan section, round-trip
wrapper.

### Round Trip from User Edit to Regenerated TEI

Complete procedure when a user has corrected a layout region:

1. The user activates layout editing in the viewer and corrects a bounding box.
2. Clicking "Save" writes `{doc}_p{NNN}_layout_curated.json` canonically to `output/layout/{doc}/` and to the mirror `docs/data/pages/{doc}/` (E78/E79). On the first save the viewer asks once for the repo folder. A reload shows the state immediately.
3. Pipeline re-run with the curated layout data as input.
   ```bash
   python -m scripts.tei.tei_unified --doc {ID} --reassemble
   ```
   This is the run that actually consumes the files saved in step 2. What `--reassemble` redoes and how it uses the Gemini Step 2 cache is described in [methodology.md](methodology.md), conventions section. The run writes `output/tei_unified/{ID}/{ID}_final.xml`; promoting that file into `output/tei_final/` is a separate step done by hand. For the curating user the consequence is that Gemini re-derives the text of every re-refined page, so a saved OCR correction acts as a suggestion and does not pass through verbatim. Word-exact text changes go through the TEI-XML mode instead, which writes `output/tei_final/{doc}_final.xml` directly and deterministically and bypasses the pipeline.
4. Projection of the workflow status into the `<revisionDesc>`.
   ```bash
   python -m scripts.tei.tei_status_marker --doc {ID}
   ```
   This carries the human-set status per stream from the manifest into the TEI header (E66) and is the step run at ZBZ handover.
5. Validation.
   ```bash
   python -m scripts.tei.tei_validator --doc {ID}
   ```
6. Regeneration of the frontend data.
   ```bash
   python -m scripts.edition.generate_edition_data --mirror-only
   ```
   This updates `docs/data/pages/{doc}/`, including `{doc}_final.xml`.

Steps 3 to 6 are run by hand today. A wrapper command that chains them is planned in
[decisions.md](decisions.md), plan section, round-trip wrapper.

## Design

This section holds the rationale of the Hersch design system, the shape of its token and
component layer, the interaction patterns of the inspection and curation UI, and the rules
by which the UI turns data into visual signal. The viewer mechanics these rules apply to
are in the viewer and persistence sections above.

### Design stance

The corpus is francophone philosophical print from the twentieth century, and the UI is a
working surface for people who read that print at the facsimile. The design system takes
its cue from the material rather than from a generic application palette. Surfaces are warm
paper tones and text is a warm anthracite that reads as printer's ink, so no pure black and
no pure white appear anywhere. The base font is a humanist serif from the francophone
typographic tradition, headings sit in a geometric sans as a formal counterpoint, and the
type scale is a minor third, which gives fine differentiation without loud size jumps.

Colour is restrained, and every coloured element carries meaning. Three accents exist, a
brick red as the primary, a Prussian blue as the secondary and an olive green as the
tertiary, plus a warm ochre for the middle state of the workflow traffic light and for
signals that ask for review. An accent colours an emphasis or a status indicator and never
fills a surface, because a filled accent surface competes with the facsimile and with the
text panel, the two things the user is actually looking at. The theme is fixed to light
through `color-scheme: light` in the token catalogue, so a system set to dark mode leaves
the surfaces as they are; the working surface stays paper-analogous and the scans are read
against a light ground.

Restraint extends to the information layer. Numbers sit inside functional elements such as
a bar, a status dot or a result line, and explanation arrives on demand through a tooltip
or a folded legend. Stat cards and introductory explainer paragraphs stay out of the pages,
as the entity overview page records for itself (entity layer section).

### Design system

Values live in `docs/assets/css/tokens.css` as custom properties under the `--h-*` prefix.
Component CSS consumes those properties and never writes a colour, radius, spacing step or
font stack literally. The catalogue is grouped into palette, text colours, borders and
shadows, status colours for the layout region types, typography including the font stacks
and the type scale, spacing steps on a four-pixel grid, layout dimensions with radii,
shadows and transition timings, and a small viewer-specific group. A `color-scheme: light`
declaration closes the catalogue and holds the light theme even when the operating system
asks for dark mode.

The component layer sits in `docs/assets/css/base.css` and covers the reset, document and
heading typography, links, inline code, the screen-reader and skip-link utilities, buttons
with primary, ghost, icon and small variants, form inputs, badges with ok, warn and info
variants, cards, toasts with ok, warn and error variants, the site header and footer chrome,
the prose layout of the static pages, the scrollbar styling, and the reduced-motion block.
Page-specific CSS builds on top,
`viewer.css` for the viewer shell, facsimile overlay, TEI rendering and editor UI,
`catalog.css` for the corpus overview, `entity-overview.css` for the entity page. For a new
component the first question is whether a token or a `base.css` component already covers it.

Three web font families carry the system, each with a defined role. The humanist serif is
the reading font of body text and of the rendered TEI. The geometric sans carries headings
and UI chrome. A monospaced family carries code, XML source and identifier strings. All
three are vendored under `docs/assets/fonts/` as WOFF2 in the latin and latin-ext subsets
with their licence texts, declared in `docs/assets/css/fonts.css`, which contributes only
the `@font-face` rules while the font stacks stay in the token catalogue. The reasoning for
vendoring instead of linking a font host is in [pipeline.md](pipeline.md), deployment
section, third-party resources.

### Interaction patterns

Every pattern below is plain DOM work against tokens, since the viewer carries no build
pipeline and no backend (architecture section).

One document bar carries the identity of the open document, the workflow status pills per
data stream, the editor identity chip and the save control, and the text panel header
carries two dropdown menus instead of scattered panel controls. Concentrating the controls
this way replaced the earlier per-panel toggles, and a checked menu item now carries the
active state. What the two menus offer is in the pages and modes section.

The keyboard behaviour of the menus and of the working-tree dialog follows platform
primitives wherever they exist, so modality, backdrop, focus containment and Escape come
from the native `<dialog>` element (pages and modes section). Hand-rolled equivalents are
avoided for the same reason. A viewer who asks the system for less motion gets the same
states without transitions or animations.

A status pill states the workflow status of one stream and cycles forward through the
status values on click (workflow status section). An entity mark acts as a button and
opens a popover (entity layer section). The design job of that popover is to keep an
undecided position visibly undecided. A held-back candidate therefore carries the reason
for the reserve and the origin of the matched name form, while a mark the matcher actually
set closes with the provenance rows naming who asserted it, how certain the assertion is,
and which rule produced the hit.

Layout editing works by direct manipulation on the facsimile, and persistence is one
shared Save button for all unsaved streams plus an Export dropdown for per-stream single
files; the operations are in the layout editor section, the write paths in the persistence
section.

### Visualization logic

The UI has four places where data becomes colour, and each uses the same token set.

Layout regions are drawn on the facsimile as rectangles coloured by region type, which maps
onto the pipeline tag vocabulary. The two non-content classes, filter and skip, take grey
with a dashed and a dotted border, so a region marked for removal is distinguishable from a
real zone without reading its label. The mapping table is in the layout editor section.

Workflow status is a dot, in the catalog table as a small dot per stream and in the viewer
as the dot inside the status pill. The unverified default is a muted grey, because pipeline
output exists for every document and its unverified state describes the handover; the
in-progress state is the warm ochre and the verified state the olive green, and red stays
unassigned for a future explicit problem state (workflow status section). The catalog
additionally carries a hollow outlined dot for the UI-only value `ausstehend` ("pending"),
which it shows for a document whose entity stream does not exist in the manifest yet; the
data model knows the three stored values only.

Entity categories are distinguished by accent, persons in Prussian blue, organisations in
olive green and works in brick red, and the review class of a mention takes the ochre.
Annotation path on the entity overview page is carried by a two-colour stacked bar, auto-marked
against review, with the corpus totals sitting on the same bar above the list, so a document
row and the corpus aggregate are read with the same visual grammar.

Inside the rendered TEI a signal is drawn as a border or a subtle background. Filled blocks
stay out of the reading view. The entity colouring hangs on the annotated reading view and
is therefore independent of the markup toggle. The toggle adds the editorial layer,
foreign-language spans in olive green with a dotted underline, editorial corrections in
brick red with a dashed one, footnotes and bibliographic references in their own quiet
marks, and it shows the legend that names them; unclear passages keep a faint ochre ground
in every view and gain a dotted underline under the toggle. The method page presents its
quality figures as tables, which keeps the numbers copyable and spares the site a chart
that would have to be regenerated with every measurement.

### Connection to the action layer

CLAUDE.md, section Design, carries the imperative form of what this section argues, meaning
the short rules an agent generating UI code has to follow. Those imperatives are the action
layer and stay there; this section holds the reasoning behind them.

`docs/assets/css/tokens.css` is the value authority. A concrete colour, radius, spacing
step, font stack or type-scale step is read from that file; this section names roles and
rules. A changed value is edited in the token catalogue and propagates through the
component layer; a changed rationale is edited here.

## Provenance

### revisionDesc and Per-Object Manifest

| Store | Content | Where |
|---|---|---|
| `<revisionDesc>` in the TEI header (E42) | `<change>` elements, one for the pipeline run with its version and date, one summary per stream for the projected workflow status (E66) | every final TEI in `output/tei_final/` |
| `{doc}_manifest.json` (E65/E66) | workflow status per stream (`ocr`/`layout`/`tei`, plus `entities` wherever an entity preview exists) + history `[{at, by, from, to, note}]` + exception pages (blank pages) | `output/tei_final/` |
| Git log | file and code change history | repo |

The machine-readable editing log per object, the roll-back it would allow and the
self-contained `_complete.xml` that would carry the log inside the TEI are planned in
[decisions.md](decisions.md), plan section, phase B. The facsimile side of that plan is
delivered already, since the generator writes `<facsimile>` with one surface per page and
body elements carry `@facs` ([tei-mapping.md](tei-mapping.md), facsimile binding).

## References

- [pipeline.md](pipeline.md): pipeline stages, engines, entity stage, viewer deployment, vendored assets, CI
- [tei-mapping.md](tei-mapping.md): markup rulebook, revision description, entity target model
- [project.md](project.md): corpus, delivery tree, entity input data (data section); ZBZ, Transkribus and teiCrafter contracts (integration section)
- [specification.md](specification.md): requirements, quality method, validation rule catalog
- [verification.md](verification.md): measured entity precision and recall, quality assurance
- [decisions.md](decisions.md): decision register; planned provenance log, `_complete.xml`, export and viewer work (plan section)
- [methodology.md](methodology.md): Promptotyping, verification cascade, `--reassemble` conventions, CER measurement method
- [journal.md](journal.md): chronological session history
- [index.md](index.md): navigation + key concepts
