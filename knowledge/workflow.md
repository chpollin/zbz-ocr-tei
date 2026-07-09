---
title: Workflow + Data Flow
type: knowledge
project:
  name: zbz-ocr-tei
  repository: https://github.com/chpollin/zbz-ocr-tei.git
method:
  name: Promptotyping
  url: https://dhcraft.org/Promptotyping/
status: complete
created: 2026-05-25
updated: 2026-07-07
tags: [zbz-ocr-tei, workflow, dataflow, viewer, persistence, provenance, complete-tei, round-trip]
---

# Workflow + Data Flow

End to end: from PDF to curated TEI. Explains what actually works, what is
manual, what is still missing, and which extensions are planned. The viewer,
its editors, and the persistence model are described here (sections 3 and 4).
Cross-cutting documentation to [pipeline.md](pipeline.md) (stages) and
[decisions.md](decisions.md) (architecture decisions).

---

## 1. Data Flow Diagram

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

Key point (E22, often misunderstood): PAGE-XML is NOT an intermediate step
toward TEI. TEI is generated DIRECTLY from layout JSON + OCR Markdown via
`scripts/tei/tei_unified.py`. PAGE-XML is produced IN PARALLEL as an export for
coOCR / Transkribus (`scripts/layout/page_xml_generator.py`).

---

## 2. Data Formats per Stage

| Stage | Format | Main path | Source |
|---|---|---|---|
| Source PDF | PDF | `data/source/pdf/{doc}.pdf` | ZBZ delivery (E23) |
| Facsimile | PNG 300 dpi | `docs/images/{doc}/{doc}_pNNN.png` | `scripts/edition/extract_pages.py` |
| Doc metadata | JSON | `data/doc_metadata.json` | `scripts/ocr/classify_docs.py` (Gemini, E27) |
| OCR (Mistral) | Markdown per page | `output/mistral_results/{doc}_pN.md` | `scripts/ocr/ocr_pipeline.py` |
| OCR (Gemini A/B) | Markdown, corrected | `output/gemini_corrected_a/`, `_b/` | `scripts/ocr/gemini_ocr_correct.py` (E29) |
| Layout (Docling) | JSON, bbox in % | `output/layout/{doc}/{doc}_pNNN_layout.json` | `scripts/layout/run_layout_analysis.py` or `run_layout_cloud.py` |
| Layout QA (Gemini) | JSON | `output/layout/{doc}/{doc}_pNNN_layout_gemini.json` | `scripts/layout/layout_qa_gemini.py` (E25/E26) |
| Overlay PNG | PNG | `output/overlay/{doc}/...` | `scripts/layout/generate_layout_overlays.py` |
| PAGE-XML | XML 2013-07-15 | `output/page_xml/{doc}/{doc}_pNNN.xml` | `scripts/layout/page_xml_generator.py` (E13) |
| METS | XML | `output/page_xml/{doc}/mets.xml` | `scripts/layout/mets_generator.py` |
| TEI scaffold (Step 1) | XML, rule-based | `output/tei_unified/{doc}_step1.xml` | `scripts/tei/tei_step1.py` |
| TEI Gemini (Step 2) | XML, LLM-refined | `output/tei_unified/{doc}_step2.xml` | `scripts/tei/tei_step2.py` |
| TEI assembly (Step 3) | XML, post-processed | `output/tei_unified/{doc}.xml` | `scripts/tei/tei_step3.py` |
| TEI final | XML with `<revisionDesc>` | `output/tei_final/{doc}_final.xml` | `scripts/tei/tei_add_revision.py` + `tei_status_marker.py` (E42, E43, E66) |
| Per-object manifest | JSON (workflow status + history per stream) | `output/tei_final/{doc}_manifest.json` | `scripts/edition/page_manifest.py` (E65/E66) |
| Review JSON (legacy) | JSON (abolished 7-layer screening, diagnostic trace only) | `output/tei_final/{doc}_screening_legacy.json` | agent screening, deprecated E66 |
| TEI final (frontend) | XML | `docs/data/pages/{doc}/{doc}_final.xml` | `scripts/edition/generate_edition_data.py` |
| TEI per page (frontend) | XML (split via `<pb>`) | `docs/data/pages/{doc}/{doc}_pN.xml` | ditto (E57) |
| Catalog (frontend) | JSON | `docs/data/catalog.json` | ditto |
| Thumbnails (frontend) | JPG 140x200 q70 | `docs/data/thumbs/{doc}.jpg` | ditto |
| Curated TEI | XML | `data/curated_tei/{doc}/` | manual (currently empty + `.gitkeep`) |

---

## 3. The Viewer

Internal web UI for inspection and curation of the pipeline results (OCR,
layout, TEI). Since E56 it replaces the earlier public edition and the
separate diagnostics/CER dashboards. Three concrete purposes: QA of the
OCR/layout/TEI results, manual correction by a human in the loop, and
demonstration to ZBZ. The viewer shows the delivered data layer, which is
Mistral OCR; the engine comparison that used to live here sits outside the
viewer since E64 (CER benchmark plus the method page, E62). It is not a
public edition or reading frontend; ZBZ covers that via Oxygen/Alma.

### 3.1 Pages and Modes

Five pages:

| Page | Content |
|---|---|
| `index.html` | corpus overview: filterable and sortable document list with workflow status per stream (E66), status legend, search |
| `viewer.html` | document detail: facsimile + layout overlay left, transcription/TEI right, three modes |
| `methode.html` | CER method page: headline, stratified values, limitations, literature comparison (E62, static) |
| `about.html` | project page, points to the method page for quality detail |
| `impressum.html` | legal notice |

The viewer knows three modes:

| Mode | Editable | Purpose | Persistence |
|---|---|---|---|
| View | nothing | pure inspection (read-only) | none |
| Edit layout | layout overlay | correct regions (bbox, type, order) | "Save" (all streams at once, section 4) |
| Edit text | text panel | correct OCR text or TEI text/XML | "Save" (all streams at once, section 4) |

One edit toggle per panel header (E60): the facsimile panel carries the
layout toggle, the text panel the text toggle (E78); the active toggle is
filled anthracite (E64). In layout mode a second toolbar appears with region
tools (add region, delete, type dropdown). Page navigation (prev / page info
/ next, plus a go-to-page field and Home/End keys) sits in the facsimile
panel header next to the region count (E78). The facsimile renderer in view
mode is OpenSeadragon (E58, pan + zoom + rotate); polygon support is
deliberately excluded (E59), rectangles suffice for the Hersch print
material. The layout editor still uses the static `<img>` overlay; wiring
the editor to OSD coordinates is open.

### 3.2 Architecture

```
docs/
├── index.html                   # corpus overview
├── viewer.html                  # document detail, 3 modes
├── methode.html                 # CER method page (static)
├── about.html                   # project page
├── impressum.html               # legal notice
├── assets/
│   ├── css/
│   │   ├── tokens.css               # Hersch design tokens (--h-*)
│   │   ├── base.css                 # reset, typography, buttons, badges, tabs
│   │   ├── viewer.css               # viewer shell, facsimile overlay, TEI render, editor UI
│   │   └── catalog.css              # corpus overview: status bar, filters, doc table
│   └── js/
│       ├── core.js                  # DOM, URL, fetch, format, cache, toast, event bus, markdown renderer
│       ├── viewer.js                # viewer orchestrator: doc selection + mode switching
│       ├── catalog.js               # corpus overview: loading, filters (stream x status, E66), sorting
│       ├── tei-render.js            # TEI-XML -> DOM
│       ├── layout-editor.js         # bbox drag/resize/add/delete + reading order
│       ├── transcription-editor.js  # OCR/TEI/XML with contenteditable
│       ├── fs-access.js             # direct write into the working tree (File System Access API, E72)
│       └── download.js              # file download (JSON/MD/XML)
└── data/                        # generated via scripts/edition/generate_edition_data.py
    ├── catalog.json             # doc list with streams.{ocr,layout,tei}.{status,last_at,last_by}
    ├── manifests/{doc}.json     # mirror of the per-object manifests (workflow + history + blank pages, E66)
    ├── search_index.json        # full text for doc search
    ├── tei/                     # final TEIs (*_final.xml)
    ├── pages/                   # per-page mirror: layout JSONs + Mistral OCR + per-page TEI
    └── examples/                # legacy: 4 DEMO docs (backward compatibility)
```

All JS modules are IIFEs in the `ZBZ.*` namespace; no npm/build pipeline.
Runtime CDN dependency: OpenSeadragon 5.0.1 (jsDelivr) for the facsimile in
view mode (E58). JSZip 3.10.1 (cdnjs) is planned for the ZIP export module
(E61) but not yet included in the code.

### 3.3 Layout Editor

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

Region types, from the `tokens.css` status colors, compatible with the
pipeline `zbz_tag`:

| `zbz_tag` | Label | Color |
|---|---|---|
| `zb_heading` | Heading | brick red |
| `zb_paragraph` | Paragraph | anthracite |
| `footnote` | Footnote | Prussian blue |
| `caption` | Caption | olive green |
| `_filter` | Filter (remove) | gray, dashed |
| `_skip` | Skip | light gray, dotted |

### 3.4 Transcription Editor

Edits the active text panel via `contenteditable` (with textbox ARIA roles).
Three selectable sources:

| Source | Format | What is edited |
|---|---|---|
| OCR | Markdown | raw OCR text |
| TEI | rendered TEI (per page) | text content only (no structure; use XML mode for tags) |
| XML | TEI-XML with syntax highlighting, whole document | raw XML including tags and attributes; saving replaces `{doc}_final.xml` as a whole (E72), a guard refuses incomplete TEI content |

Changes are collected debounced and marked unsaved; the shared "Save" button
persists them together with layout and status (section 4). Per-stream single
files are available via the "Export" dropdown (E78).

### 3.5 Blank Pages (E63/E65/E67)

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

### 3.6 Workflow Status per Stream (E66/E67/E77)

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
set in the viewer via three pills (OCR / Layout / TEI) in the doc subbar;
a click cycles forward. The editor identity (initials) sits as a chip next
to the Save button and goes into the manifest history (`{at, by, from,
to}`). The first activation of an edit toggle auto-transitions the matching
stream from `unverifiziert` to `in_arbeit`; deliberate transitions (for
example to `verifiziert`) happen via the pill. At ZBZ handover
`tei_status_marker.py` projects the history deterministically as `<change>`
entries into the `<revisionDesc>` (backup first, removes stale
agent-screening entries). Data model and commands: CLAUDE.md, per-object
manifest section; decisions E66/E77.

### 3.7 Hersch Design System

The authority for token values is `docs/assets/css/tokens.css`; the
imperative design principles are in CLAUDE.md, Design section. Core
principles and their rationale:

| Decision | Rationale |
|---|---|
| EB Garamond (serif) as the base font | humanist tradition of the francophone world |
| Jost (geometric sans) for headings | formal clarity as a counterpoint |
| minor third (1.2) as the type scale | fine differentiation |
| no pure black/white | thinking in broken tones |
| brick red `#8B3A3A` as the primary accent | existential embodiment |
| Prussian blue `#2B4C7E` as the secondary accent | claim to universality |
| olive green `#6B7B5E` as the tertiary accent | natural composure |
| warm anthracite `#2C2825` instead of navy | materiality of printer's ink on paper |

`tokens.css` defines the Hersch values (`--h-*`); `base.css` builds the
component layer on top (`.btn`, `.badge`, `.card`, `.input`, `.tabs`,
`.toast`); `viewer.css` holds the app-specific layout code; `catalog.css`
the corpus overview. Accent colors mark accents and status indicators, never
surfaces.

Deployment of the viewer (GitHub Pages, local server, facsimile hosting
limits) is described in [infrastructure.md](infrastructure.md), viewer
deployment section.

---

## 4. Persistence in the Viewer

The viewer (`docs/viewer.html`) is a static single-page app without a
backend. The FastAPI curation server that used to exist was retired with E56/E57.
A single "Save" button writes changes directly into the repo clone
(File System Access API, Chromium) or as a file download (fallback) and mirrors them
at the same time into the viewer mirror, so that a reload shows the state (E72/E78/E79).

### 4.1 Read Path (read-only)

The viewer loads static files exclusively. The path resolver in
`docs/assets/js/core.js` uses a three-level fallback chain:

```
1. docs/data/pages/{doc}/{doc}_pN.{ext}   (frontend mirror, whole corpus)
2. docs/data/examples/{doc}/...           (legacy 4 DEMO docs, backward compatibility)
3. ../output/{stage}/...                  (local fallback for engines not in the mirror)
```

This makes the viewer work on GitHub Pages for the entire corpus. Locally,
Gemini A/B and LLM correction are additionally reachable.

### 4.2 Save Mechanism (one Save Writes to Repo + Mirror)

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

Known limitations, honestly stated:

- Write permission must be re-granted per session by user gesture (browser trust model, not a defect).
- No conflict detection for parallel edits (browser state == truth).
- Per-page TEI splits in the mirror only appear at `--reassemble`; a direct TEI-XML edit overwrites the SoT and is regenerated by a later `--reassemble`. XML mode therefore loads the whole document (never a single page), and a guard in `saveAll()` refuses content without a `teiHeader`/`TEI` root.
- A pipeline re-run (`tei_unified --reassemble`) must be triggered manually. The frontend cannot trigger it.

### 4.3 Round Trip from User Edit to Regenerated TEI

Complete procedure when a user has corrected a layout region:

1. Edit in the viewer: the user activates the layout edit toggle and corrects a bbox.
2. Save: clicking "Save" writes `{doc}_p{NNN}_layout_curated.json` directly to `output/layout/{doc}/` (canonical) AND to the mirror `docs/data/pages/{doc}/` (E78/E79); the first time, the viewer asks once for the repo folder. A reload shows the state immediately.
3. (No longer applies; no manual file drop, the edit already sits at the canonical location.)
4. Pipeline re-run with curated layout data as input:
   ```bash
   python -m scripts.tei.tei_unified --doc {ID} --reassemble
   ```
   The `--reassemble` flag redoes Step 1 (scaffold from curated OCR/layout) and Step 3 (assembly) and uses the Gemini Step 2 cache. Pages without new curation stay free of charge; pages with newer curated OCR/layout are selectively re-refined by Gemini (1 call each), so that the correction reaches the final TEI (otherwise Step 3 assembles from the stale cache, bypassing the curation). Important: Gemini re-derives the text in the process; an OCR correction is a suggestion, not a verbatim pass-through. For word-exact text changes use the TEI-XML mode; it writes `output/tei_final/{doc}_final.xml` directly, bypassing the pipeline (verbatim, deterministic).
5. revisionDesc update:
   ```bash
   python -m scripts.tei.tei_add_revision --doc {ID}
   ```
   Rewrites `<revisionDesc>` with the current pipeline run. The human-set workflow status per stream is projected from the manifest into the `<revisionDesc>` at ZBZ handover via `tei_status_marker.py` (E66).
6. Validation:
   ```bash
   python -m scripts.tei.tei_validator --doc {ID}
   ```
7. Regenerate frontend data:
   ```bash
   python -m scripts.edition.generate_edition_data --mirror-only
   ```
   Updates `docs/data/pages/{doc}/` (incl. `{doc}_final.xml`).

Current gap: steps 4-7 are not automated. There is no
"Apply Curated Edit" wrapper command. Such a convenience script (e.g.
`scripts/apply_curated.py --doc {ID}`) would be a sensible next step.

---

## 5. Provenance: Current vs. Planned

### 5.1 Current: revisionDesc + Per-Object Manifest

| Store | Content | Where |
|---|---|---|
| `<revisionDesc>` in the TEI header (E42) | `<change>` elements: pipeline stages + versions + projected workflow status (E66) + date | every final TEI in `output/tei_final/` |
| `{doc}_manifest.json` (E65/E66) | workflow status per stream (`ocr`/`layout`/`tei`) + history `[{at, by, from, to, note}]` + exception pages (blank pages) | `output/tei_final/` |
| `{doc}_screening_legacy.json` (legacy) | finding of the abolished 7-layer screening, diagnostic trace only (deprecated E66) | `output/tei_final/` (gitignored) |
| Git log | file and code change history | repo |

What is missing:

- Edit history per object (who/what/when of manual edits)
- AI agent audit trails with per-decision confidence (model, prompt version, confidence)
- Roll-back to an earlier edit state without git history
- Direct link region <-> body element (currently implicit via reading order)

### 5.2 Planned: `{doc}_provenance.json` per Object

A central editing log per document. Schema proposal:

```json
{
  "doc_id": "20",
  "current_state": {
    "layout_source": "gemini_corrected_v3.1+curated",
    "ocr_source": "mistral_2512",
    "tei_version": "1.4.2",
    "workflow_status": { "ocr": "unverifiziert", "layout": "in_arbeit", "tei": "unverifiziert" }
  },
  "history": [
    {
      "ts": "2026-02-14T09:23:00Z",
      "actor": "mistral-document-ai-2512",
      "kind": "ocr",
      "scope": "all pages",
      "ref": "output/mistral_results/20_p*.md"
    },
    {
      "ts": "2026-03-04T16:01:00Z",
      "actor": "gemini-3.1-flash-lite",
      "kind": "layout_qa",
      "scope": "all pages",
      "changes": 14,
      "ref": "output/layout/20_p*_layout_gemini.json"
    },
    {
      "ts": "2026-05-26T10:23:00Z",
      "actor": "human:ek",
      "kind": "workflow_status",
      "scope": "layout",
      "details": "unverifiziert -> in_arbeit",
      "ref": "output/tei_final/20_manifest.json"
    },
    {
      "ts": "2026-05-25T14:00:00Z",
      "actor": "human:chpollin",
      "kind": "layout_edit",
      "scope": "page 1",
      "details": "3 regions modified (bbox tweaks)",
      "ref": "output/layout/20_curated/20_p001_layout_curated.json"
    }
  ]
}
```

Properties:

- Single source of truth per object for the entire editing history
- Displayable in the viewer as a provenance drawer (stage 2.11 in the UI wave)
- Extensible for AI agent audit (model hash, prompt version, confidence)
- Roll-back: every action references a concrete file in `output/...`
- Machine-readable for reports, reviews, and archives

---

## 6. Planned: `_complete.xml`, a Self-Contained TEI

Currently `{doc}_final.xml` is a lean TEI without the layout apparatus. Layout
lives in parallel JSONs. For edition, archive, and ZBZ handover, a
self-contained TEI would be useful that carries all layout information via the
TEI standard apparatus.

### 6.1 TEI Standard for Embedded Layout

```xml
<facsimile>
  <surface n="1" ulx="0" uly="0" lrx="2480" lry="3508">
    <graphic url="../images/20/20_p001.png"/>
    <zone xml:id="z_20_p001_r1" ulx="93" uly="660" lrx="2347" lry="803" type="heading"/>
    <zone xml:id="z_20_p001_r2" ulx="184" uly="838" lrx="2231" lry="901" type="paragraph"/>
    <!-- ... further regions ... -->
  </surface>
</facsimile>

<text>
  <body>
    <div type="text">
      <head facs="#z_20_p001_r1">JEANNE HERSCH</head>
      <p facs="#z_20_p001_r2">L'illusion philosophique</p>
      <!-- ... -->
```

This makes every piece of text traceable back to the exact region in the facsimile,
the edition standard for digital TEI editions (eXist-db, TEI-Publisher, EVT,
FuD).

### 6.2 Two TEI Variants on Export

| Variant | Content | Use |
|---|---|---|
| `{doc}_final.xml` (today) | lean TEI, text structure only, with `<revisionDesc>` | remains as the compact reading variant |
| `{doc}_complete.xml` (planned) | TEI + `<facsimile>` + `<zone>` + `@facs` + extended `<revisionDesc>` with provenance items | edition standard, archive, export (E61), ZBZ handover |

`_complete.xml` becomes the default variant in the export module (E61); `_final.xml`
remains optional as the mini variant.

### 6.3 Linking Provenance and revisionDesc

In the `<revisionDesc>` of the `_complete.xml`, the items from
`{doc}_provenance.json` are entered one to one as `<change>` elements:

```xml
<revisionDesc>
  <change when="2026-02-14T09:23:00Z" who="#mistral-2512" type="ocr">
    OCR by Mistral Document AI 2512, all pages</change>
  <change when="2026-03-04T16:01:00Z" who="#gemini-3.1-flash-lite" type="layoutQA">
    Layout QA by Gemini, 14 corrections</change>
  <change when="2026-05-25T14:00:00Z" who="#person-chpollin" type="layoutEdit">
    Manual layout correction, page 1, 3 regions</change>
  <change when="2026-05-26T10:23:00Z" who="#person-ek" status="in_arbeit" n="layout">
    Workflow status layout: unverifiziert -&gt; in_arbeit (E66/E77)</change>
</revisionDesc>
```

Provenance thus lives inside the TEI, not in parallel next to it. Single
source of truth in exactly one file.

### 6.4 Implementation State

Parts of this plan are already realized in the delivered TEI: step 1
computes pixel zones per region, the assembly writes `<facsimile>` with one
surface per page (page-image reference per E89), and body elements carry
`@facs`. Open remain the machine-readable `provenance.json` (section 5.2)
and assembling the extended `<revisionDesc>` from it. Both stay a pipeline
package of their own, separate from the UI wave.

---

## 7. Roadmap (as of 2026-06-10)

### Done

- Knowledge refactoring: all knowledge docs and README consolidated, drift fixed (most recently 2026-06-10).
- Viewer condensed (E64): doc subbar and toolbar merged, OCR source switcher removed (the viewer shows the delivered Mistral layer), edit toggles for layout and text.
- Save loop closed (E72/E78/E79): one save button secures all streams, writes canonically to `output/` and to the `docs/data/` mirror; individual downloads in the export dropdown.
- Workflow status extended to three levels (E77) and the frontend findings of the gap analysis (H1 through H5, M series) fixed (2026-06-10).

### Open

- ZIP export per document (E61): all pipeline artifacts of an object as one download (JSZip), optionally collected from the corpus overview.
- Provenance extension of the pipeline: tie body elements to the layout zones via `@facs` and produce a machine-readable `provenance.json` (implementation state in section 6.4). A provenance panel in the viewer builds on this.
- Further expansion ideas for the corpus overview and about page (hero section, charts, print CSS) as well as the remaining frontend findings N1/N3/N6/N7 are deliberately deferred until after ZBZ acceptance.

The decisions of the uplift wave are documented as E58-E67 in [decisions.md](decisions.md);
open frontend findings in [specification.md](specification.md), frontend requirements section.

---

## 8. Known Drift / Action Items

The code and documentation drift items formerly listed here are fixed:
`generate_edition_data.py` treats the deleted `dashboard.json` as optional (`or {}`),
the `scripts/postprocess/` references were removed from README and project.md (the standalone
`scripts/ocr/llm_postprocess.py` is unaffected), and the pipeline diagrams show
PAGE-XML correctly as a parallel export (E22). Historical details in the git log.

What remains open: the manual round trip (steps 4-7 in section 4.3 are not automated in a wrapper)
and the planned pipeline wave (`_complete.xml` + `provenance.json`, sections 5 and 6).

---

## 9. References

- [pipeline.md](pipeline.md): pipeline stages, engines, TEI mapping
- [specification.md](specification.md): requirements, quality method, validation rule catalog, frontend requirements
- `arbeitsbericht-v3.md`: the project report (CER, proxy, validation state); [cer-methodology.md](cer-methodology.md): CER measurement method
- [decisions.md](decisions.md): decision register, open items
- [methodology.md](methodology.md): Promptotyping, verification cascade, three-layer model
- [journal.md](journal.md): chronological session history
- [index.md](index.md): navigation + key concepts
