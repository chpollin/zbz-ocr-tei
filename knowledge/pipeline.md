---
title: Pipeline
type: knowledge
project:
  name: zbz-ocr-tei
  repository: https://github.com/chpollin/zbz-ocr-tei.git
method:
  name: Promptotyping
  url: https://dhcraft.org/Promptotyping/
status: complete
created: 2026-01-29
updated: 2026-07-07
tags: [zbz-ocr-tei, pipeline, ocr, layout, tei, engines]
---

# Pipeline

Data flow from PDF to TEI-XML: stages, scripts, engines, TEI mapping. Since the scope
expansion (25.02.2026, E21) zbz-ocr-tei covers the entire path.

CLI reference and operational tools: [methodology.md §Commands](methodology.md).
Status per stage: [project.md](project.md).
Complete end-to-end workflow with round-trip logic, save mechanism, and
provenance concept: [workflow.md](workflow.md).

---

## Overview

```
PDF
 |
 v
Images (extract_pages.py)
 |
 +------------------------------+
 v                              v
OCR (Mistral)                  Layout (Docling + Gemini QA)
 |                              |
 |                              +--> PAGE-XML (page_xml_generator.py)
 |                              |    = parallel export for coOCR
 |                              |    NOT TEI input (E22)
 |                              |
 +------------------------------+--> TEI-XML (tei_unified.py)
                                     |
                                     v
                                     Workflow status per stream (E66, human-set)
                                     |
                                     v
                                     Evaluation + Viewer
```

Important (E22, often misunderstood): PAGE-XML is NOT an intermediate step
toward TEI. TEI is generated DIRECTLY from layout JSON + OCR Markdown via
`scripts/tei/tei_unified.py`. PAGE-XML is produced in parallel as an export for
coOCR / Transkribus (E13). Both derive independently from layout JSON + OCR.

| Stage | Task | Script | Output | Status |
|---|---|---|---|---|
| 1 | PDF -> PNG | `scripts/edition/extract_pages.py` | PNG (`docs/images/`) | Production |
| 1a | Document classification (Gemini) | `scripts/ocr/classify_docs.py` | `data/doc_metadata.json` + `output/classification/` | Production (full corpus, E27) |
| 2 | OCR | `scripts/ocr/ocr_pipeline.py` (`-e mistral` base, `-e gemini` opt-in vision OCR) | page Markdown (`output/mistral_results/`) | Production |
| 2a | LLM post-correction (optional) | `scripts/ocr/llm_postprocess.py` | `output/llm_corrected_c/` | Production, E17: optional |
| 2b | Gemini OCR correction (optional) | `scripts/ocr/gemini_ocr_correct.py` | `output/gemini_corrected_a/` / `_b/` | Sample (E29) |
| 3 | Layout analysis | `scripts/layout/run_layout_analysis.py` (local GPU) or `run_layout_cloud.py` (docling-serve) | regions + bbox (`output/layout/`) | Production |
| 3a | Layout QA/detect (Gemini) | `scripts/layout/layout_qa_gemini.py --mode {qa\|detect\|auto}` | `_layout_gemini.json` | Production (E25/E26/E31) |
| 3b | Overlay generator | `scripts/layout/generate_layout_overlays.py` | PNGs + side-by-side compare | Production |
| 4 | PAGE-XML + METS | `scripts/layout/page_xml_generator.py` + `mets_generator.py` | `output/page_xml/` | Production |
| 5 | TEI-XML (rule-based) | `scripts/tei/tei_generator.py` | `output/tei/` | Production |
| 5b | Unified TEI Pipeline (E32) | `scripts/tei/tei_unified.py` | `output/tei_unified/` | Production (full corpus) |
| 5b+ | Post-assembly fixes | `tei_step3.py` | fixes E/F/G + heuristic lb injection | Production (Session 34) |
| 5c | TEI validation | `scripts/tei/tei_validator.py` | JSON + HTML report | schema-valid across the delivered corpus (gate: `tests/test_tei_schema.py`); warnings informative (rule catalog in [specification.md](specification.md), current tallies via `python -m scripts.tei.tei_validator --all --report`) |
| 6 | Evaluation | `scripts/eval/evaluate_ocr.py` + `benchmark_cer.py` + `cer_statistics_full.py` | `output/evaluation/` + `docs/data/cer_statistics.json` | Production |

Manual curation (E56): takes place in the pipeline viewer (`docs/viewer.html`) with
layout and transcription editor. A single save writes canonically to `output/` and to
the `docs/data/` mirror (File System Access API, download fallback, E72/E78/E79).
Details: [workflow.md](workflow.md), viewer and persistence sections.
Previously (E36) a FastAPI curation server ran at localhost:8000; it has been retired.

Quality assurance (E66): the former agent screening is abolished (no human had granted
the "APPROVED" statuses; the agent certified itself). Replacement: a human-set
workflow status per stream (`unverifiziert | in_arbeit | verifiziert` for each of OCR/layout/TEI, three levels since E77),
set in the viewer, with history in the per-object manifest and projection into the `<revisionDesc>`. Status
distribution: see the manifests (`python -m scripts.edition.page_manifest --dry-run`). Details: [workflow.md](workflow.md), workflow status section.

---

## Engines

Active engines in two roles. Model choice matters less than pipeline design:
pipeline investments pay off (chunking,
page matching, quality routing). API costs are negligible.
LLM post-correction hurts at CER <5% (E17).

### Mistral Document AI: OCR Production

| Aspect | Details |
|---|---|
| Model | `mistral-document-ai-2512` on Azure AI Foundry (serverless API) |
| Role | primary OCR engine for ZBZ production |
| Speed | ~1.3 s/page |
| Output | per-page Markdown (`output/mistral_results/{doc_id}_p{N}.md`) |
| Languages | 36 (de, fr, en, es, it, ...) |
| Endpoint | `https://<deployment>.<region>.models.ai.azure.com/v1/ocr` |
| Limit | 30 pages/request, 30 MB max (pipeline splits automatically) |

Setup notes and error diagnosis: [infrastructure.md](infrastructure.md) §Azure.

### Docling 2.75: Layout Primary

| Aspect | Details |
|---|---|
| Model | RT-DETR V2 Heron (42.9M, IBM Research, DocLayNet) |
| Role | primary layout engine (layout only, no OCR; RapidOCR has FR encoding problems) |
| Speed | ~5 s/page (RTX 4060 GPU), ~27 s/page (CPU / docling-serve) |
| Detection | 17 block types (Title, Section-header, Text, Footnote, Caption, Page-header/footer, Picture, Table, Formula, ...) |
| API | `scripts/layout/run_layout_cloud.py` -> docling-serve (Docker, IBM official) |

Coverage-based quality scoring is a strong proxy for layout quality; no ML needed.
Landscape/multi-column pages are the hard cases (~64% bad vs. ~14% portrait).

### Gemini 3.1 Flash Lite: Layout QA + Detect + Refinement

| Aspect | Details |
|---|---|
| Model | `gemini-3.1-flash-lite-preview` |
| Roles | layout correction, layout detect (fallback for Docling failures, ~15%), document classification, OCR correction, vision OCR (opt-in `-e gemini`, exception replacement for Mistral, writes to `output/mistral_results/`), TEI refinement |
| SDK | `google-genai` |

3 modes in `layout_qa_gemini.py`:
- `--mode qa`: overlay PNG + layout JSON to Gemini, labels corrected, false positives removed, quality score 0-100
- `--mode detect`: full re-detection with `box_2d` coordinates (0-1000 scale -> x_pct/y_pct/w_pct/h_pct)
- `--mode auto`: routes per page via `compute_page_quality()` (detect for bad/empty, qa for good/warning)

Structured outputs via `response_schema`. Both versions are kept (`_layout.json` + `_layout_gemini.json`); in DH, provenance is as important as quality.

### Architecture Decision (E19/E20)

Requirements: structural detection, bbox, FR/DE, PAGE-XML 2013-07-15.
Evaluated (25.02.2026): Gemini, Claude, Mistral (for layout), Docling, Surya, Kraken, Azure Document Intelligence.

Decision: Docling + Gemini hybrid. Docling is the best open-source bbox engine (mAP 0.699, 17 classes, free, CPU-capable).
Gemini serves as QA validator and detect fallback. Claude is not used for layout (no bbox) but valuable for TEI. Mistral remains the text engine.

Fallback: Kraken (native PAGE-XML, historical FR). `ocr-fileformat` (UB Mannheim) converts
between 30+ formats (hOCR, PAGE-XML, ALTO, TEI).

---

## TEI Mapping (DTA-Basisformat + ZBZ Adaptations)

Transformation rules from the source text to TEI-XML following DTA-Basisformat with
project-specific extensions. Binding since E48/E49 (2026-03-26).

Sources:
- `data/source/guidelines/Editionsrichtlinien_ZBZ.md`: the binding editorial guidelines (Editionsrichtlinien)
- DTA-Basisformat: external standard, linked in [data/source/guidelines/README.md](../data/source/guidelines/README.md) (deutschestextarchiv.de)
- `data/schema/zbz_hersch.rng`: project-specific RelaxNG schema (TEI P5 v4.10.2)

### Core Principles

1. Reading-text transcription true to the original, with index annotation
2. DTA-Basisformat as foundation plus project-specific adaptations
3. Defined normalizations (no diplomatic transcription)
4. Transcription faithful to the source

### Document Structure

```xml
<?xml version='1.0' encoding='UTF-8'?>
<TEI xmlns='http://www.tei-c.org/ns/1.0' type="naegeli">
  <teiHeader><!-- from doc_metadata.json via build_tei_header; Alma metadata (MMSID) = ZBZ domain, O8 --></teiHeader>
  <text>
    <front><!-- optional: prefaces, dedications --></front>
    <body>
      <pb facs="#f0001" n="1"/>  <!-- first pb BEFORE div n="1" -->
      <div n="1"><!-- main structure --></div>
    </body>
    <back><!-- optional: translations, reprints --></back>
  </text>
</TEI>
```

| Level | Element | Use |
|---|---|---|
| 1 | `<div n="1">` | main chapter |
| 2 | `<div n="2">` | subchapter |
| 3 | `<div n="3">` | section |

`<pb>` sits inside `<div>`.

### Character Normalization (E49, binding)

| Source characters | Target character | Unicode | Rule |
|---|---|---|---|
| dashes and list dashes, ranges | en dash `–` | U+2013 | all horizontal strokes except hyphenation/compound hyphens |
| hyphenation/compound hyphens | hyphen `‐` | U+2010 | word breaks, compounds |
| quotation marks | `“`/`”` | U+201C / U+201D | typographic |
| single quotation marks | `‘`/`’` | U+2018 / U+2019 | typographic |
| apostrophes | `’` | U+2019 | `l'homme` |
| non-representable characters | `~` (tilde) | U+007E | placeholder |

Whitespace: delete spaces before `:`, `;`, `?`, `!` and quotation marks. Normalize
enumerations with dashes to `/` (Zuerich/Bern/Basel). Retained: `ß` (U+00DF),
brackets as in the original, accents, ligatures.

### Page Structure

```xml
<pb facs="#f0001" n="1"/>
<pb facs="#f0002" n="2"/>
<pb facs="#f0003" n="[3]"/>  <!-- page number not printed -->
```

- `facs` = reference to the digitized image (`#f` + digitization number)
- `n` = printed page number, `[number]` when the number is missing
- pb stands at the start of the page; the first pb comes BEFORE `<div n="1">`

Line breaks (`<lb>`) are preserved at the data level (not shown in the frontend).
Heuristic lb injection (Fix-002, Session 34): ~60 characters at word boundaries.

### Highlighting

| Rendering | TEI | Example |
|---|---|---|
| Bold | `<hi rendition="#b">` | `<hi rendition="#b">wichtig</hi>` |
| Italic | `<hi rendition="#i">` | `<hi rendition="#i">Philosophie</hi>` |
| Underline | `<hi rendition="#u">` | |
| Spaced | `<hi rendition="#g">` | |
| Small caps | `<hi rendition="#k">` | |
| Superscript | `<hi rendition="#sup">` | |
| Subscript | `<hi rendition="#sub">` | |

Only semantically relevant highlighting is encoded.

### Special Structures

- Language switch: `<foreign xml:lang="deu">...</foreign>` (ISO 639-3: `fra`, `deu`, `eng`, `ita`, `lat`)
- Footnotes: `<note place="foot" n="1" xml:id="fn{Seite}-{Nr}">...</note>` with `next`/`prev` when spanning pages
- Printing errors: `<choice><sic>Eclairement</sic><corr>Eclairement</corr></choice>`
- Illegible passages: `<unclear cert="high\|low">...</unclear>`
- Marginal notes: `<note place="left\|right">...</note>`
- Blank pages: `<pb .../><p>[Leer]</p>`

### Entities

Named entity markup was removed with E71 (2026-05-27) (see [decisions.md](decisions.md)):
the linking was not functional in the delivered TEI (~2.6% of mentions with a real
GND ID, the rest `GND:unknown` or internal IDs). `<persName>`, `<orgName>`, `<placeName>` are no
longer tagged. `<bibl>` remains exclusively as a bibliographic structure (literature lists
in `<listBibl>`, review citation in the `<head>`), without `ref`/`corresp`.

### Curation instead of Automation: front/back/anchor/unclear (as of 2026-06-08)

The pipeline produces one `<div>` body fragment per page (Step 2, OUTPUT FORMAT in
`tei_mapping_prompt.py`). Document-level and cross-page structures therefore do
NOT emerge automatically; they are set during curation (viewer). Rationale per case (with
frequency in the 25 reference TEIs):

- `<front>`/`<back>` (dedication, editorial notes; translation/reprint/otherEdition;
  front 6/25, back 5/25): document level. The end-matter source in the Masterfile (column
  "Anmerkungen") is free text ("deutsche Uebersetzung: ID 320", partly only internal
  references), not a reliable citation, hence deliberately no auto-build (it would produce wrong TEI).
  End-matter citation per MLA 9 plus Swisscovery link remains with ZBZ/curation.
- Cross-page `<anchor>` (double-page figure, 1/25): needs both pages,
  too rare and too error-prone for automation.
- `<unclear>` (0/25): a per-character judgment against the scan image; curation only.
- `<epigraph>` (1/25): adopted when the AI places it at the div start; a
  misplaced motto is unpacked by `tei_step2._fix_structural_issues`.

### Special Document Types

- `<div type="review">` with `<bibl>` in the `<head>`
- `<div type="interview">` with `<sp>/<speaker>` (E47: `essay` -> `text`)
- `<div type="conversation">` for panel discussions
- `<div type="entry">` for encyclopedia entries, with `<div type="bibliography">/<listBibl>`
- `<ab type="redactional" hand="xy">` for redactional texts (not by Hersch)

Paratexts: `<front>` (`editorial`, `dedication`), `<back>` (`translation`, `reprint`, `otherEdition`).
Citation in `<back>` per MLA 9, with Swisscovery permalink as `<ref target="...">`.

### Figures

```xml
<figure xml:id="fig1">
  <graphic url="..\..\images\fig1.tif"/>
  <head>[optional]</head>
  <p>[optional explanation]</p>
</figure>
```

- `xml:id` on `<figure>` (not `<graphic>`), sequential
- `<figure>` is always a standalone block, never inside `<p>`
- double-page figures: `<anchor xml:id="figN-start/end"/>` marks the span

### Omissions

| Omission | Note |
|---|---|
| Title pages | except for monographs |
| Curriculum vitae | even when placed in front |
| Running heads | - |
| Blurbs | - |
| Author attribution | "von Jeanne Hersch" only in the header |
| Initials | not annotated |
| Multi-column layout | not reproduced as such |

### revisionDesc (Workflow Status, E66/E77)

Every final TEI in `output/tei_final/` contains `<revisionDesc>` directly before `</teiHeader>`.
The first `<change>` records the pipeline generation; after that follows one summary `<change>`
per stream (OCR/layout/TEI) with the human-set workflow status. Projected from the manifest
into the header by `tei_status_marker.py` (E66):

```xml
<revisionDesc>
  <change when="2026-03-15" who="pipeline">TEI generated (Unified Pipeline v1, Gemini + RelaxNG)</change>
  <change status="unverifiziert" n="ocr-summary">OCR-Strom (Stand): unverifiziert</change>
  <change status="unverifiziert" n="layout-summary">LAYOUT-Strom (Stand): unverifiziert</change>
  <change status="unverifiziert" n="tei-summary">TEI-Strom (Stand): unverifiziert</change>
</revisionDesc>
```

Status values (three levels since E77): `unverifiziert` | `in_arbeit` | `verifiziert`. The former
agent screening (status values `APPROVED`/`NEEDS_REVIEW`/...) was abolished with E66; no human
had granted those "APPROVED" statuses. All streams start `unverifiziert` as the handover default. The viewer shows the status as a traffic-light pill.

### Element Inventory

| Element | Attributes | Use |
|---|---|---|
| `<TEI>` | `xmlns`, `type="naegeli"` | root |
| `<teiHeader>` | - | metadata |
| `<text>`, `<front>`, `<body>`, `<back>` | - | containers |
| `<div>` | `n`, `type` | structural |
| `<pb>` | `facs`, `n` | page break |
| `<lb>` | `facs`, `n`, `break` | line break |
| `<head>` | `type` | heading |
| `<title>` | `type` (main/sub) | title |
| `<p>` | `facs` | paragraph |
| `<hi>` | `rendition` | highlighting |
| `<bibl>` | - | bibliographic entries (`<listBibl>`, review `<head>`); no entity refs since E71 |
| `<note>` | `place`, `n`, `xml:id`, `next`, `prev` | footnote/marginal note |
| `<foreign>` | `xml:lang` | language switch |
| `<space>` | `dim` | spacing |
| `<list>`, `<item>`, `<table>`, `<row>`, `<cell>` | - | lists + tables |
| `<figure>` | `xml:id` | figure |
| `<graphic>` | `xml:id`, `url` | image reference |
| `<choice>`, `<sic>`, `<corr>` | - | printing errors |
| `<sp>`, `<speaker>` | `type` | speech act |
| `<listBibl>` | - | bibliography |
| `<ab>` | `type`, `hand` | redactional block |
| `<unclear>` | `cert` | illegible passage |
| `<anchor>` | `xml:id` | double-page images |
| `<ref>` | `target` | external reference |
| `<revisionDesc>`, `<change>` | `who`, `when`, `status` | revision status |

### Facsimile Binding (E89, 2026-06-21, ZBZ-conformant)

The generator itself produces `<facsimile>`, `<surface ulx uly lrx lry>`, `<zone>` with
pixel coordinates and the complete `@facs` binding line<->zone. The page break carries
`<pb facs="#facs_N" n="Seitenzahl"/>` (ZBZ editorial guidelines, whole corpus). So that this
reference resolves to the image in a self-contained way, every `<surface>` carries a `<graphic url>`
as its first child (the schema requires graphic before zone). Address scheme: relative filename
`{doc_id}_p{NNN}.png` (physically in `docs/images/{doc_id}/`, sequential to `facs_N`). Produced
directly in `build_facsimile` ([tei_step3.py](../scripts/tei/tei_step3.py)); the already
delivered stock is brought to the same state without an OCR re-run by the post step
[tei_surface_graphic.py](../scripts/tei/tei_surface_graphic.py).
Resolves [[O25]] and replaces the faulty blank-page placeholder `{seite}.png` (it pointed to
a non-existent file). ZBZ prescribes the `<pb facs>` form for page images, not
necessarily a surface `<graphic>`; the `<graphic>` makes the reference resolvable and
supersedes teiCrafter's hard-coded demo path.

---

## Implementation Phases

| Phase | Content | Status |
|---|---|---|
| 0 | Pilot: layout eval + OCR + TEI on 15 docs | Done |
| 1 | Scale layout: Docling + Gemini QA on the full corpus | Done |
| 2 | PAGE-XML generator + METS | Done (full corpus) |
| 3 | NER + Wikidata linking | Removed (E71, 2026-05-27) |
| 4 | TEI-XML with PAGE-XML | Done (schema-valid, gate-tested) |
| 5 | Extended evaluation (CER benchmark) | Done, see `reports/arbeitsbericht-v3.md` and [cer-methodology.md](cer-methodology.md) |
| 6 | Production run + scholarly curation | In progress: full corpus generated, workflow status `unverifiziert` (E66), curation open |

Cross-cutting (parallel to phases 3-6): pipeline viewer with edit mode, see [workflow.md](workflow.md). The earlier public reading edition (E33) and the curation editor (E36) were retired with E56.

### Sub-Project: CER Improvement

Systematic OCR quality improvement through iterative experimentation and benchmarking.
Method: see [specification.md](specification.md) and [cer-methodology.md](cer-methodology.md); measured values: `docs/data/cer_statistics.json`. Tools: `scripts/eval/benchmark_cer.py`,
`scripts/eval/cer_statistics.py`, `scripts/eval/cer_statistics_full.py`. Phases 0-4 with success metrics
(phase 1 target median <5%, phase 2 target median <4%).

---

## ZBZ Structural Tags (Docling -> ZBZ -> PAGE-XML)

| Docling | ZBZ | PAGE-XML |
|---|---|---|
| Title, Section-header | `zb_heading` | heading |
| Text, Paragraph, List-item, Table, Formula | `zb_paragraph` | paragraph |
| Footnote | `footnote` | footnote |
| Caption | `caption` | caption |
| Page-header, Page-footer | `_filter` | (removed) |
| Picture, Figure | `_skip` | - |

---

## Online Demo (E28)

The full pipeline output (`output/`) is gitignored and only available locally. For the online demo
(GitHub Pages) 4 representative documents are committed:

| Doc | Type | Language | Pages | Note |
|---|---|---|---|---|
| 2310 | A | FR | 3 | journal article, JSTOR cover |
| 1000 | B | FR | 4 | two-column |
| 1330 | D | DE/FR | 6 | bilingual anthology |
| 1540 | C | DE | 8 | German monograph |

With E57 (per-page mirror), layout, OCR, and TEI data for the whole corpus additionally
live in `docs/data/pages/`; the viewer therefore works on GitHub Pages for the entire
corpus, only facsimile images are missing outside the 4 DEMO docs (image delivery
local-only, 4 GB).

---

## Manual Edits Back into the Pipeline (Round Trip)

The viewer writes curation (layout, OCR text, workflow status) directly into the
working tree (File System Access API, E72/E78) and mirrors it to `docs/data/`
(E79); `tei_unified --reassemble` actually consumes the curated files and
selectively re-refines the changed pages (1 Gemini call each). Complete procedure
including save mechanism, step sequence, provenance concept, and the planned
`_complete.xml` variant: [workflow.md §Round Trip](workflow.md).

Data: scan images in `docs/images/{doc_id}/`, OCR/layout/TEI in `docs/data/examples/{doc_id}/`.
`core.js` path resolver with a three-level fallback chain: `data/pages/` -> `data/examples/{doc_id}/`
-> `../output/...` (E57).

---

## Transkribus Export

PAGE-XML round trip (E81). The PAGE-XML produced in stage 4 (`output/page_xml/{doc}/page/`)
is standard PAGE 2013-07-15 and can be played back to Transkribus losslessly, as layout
plus transcription, for manual post-correction or HTR model training. This is the reverse
direction of the viewer round trip above: there, edits come in; here, pipeline layout goes out.

### Folder Convention

Transkribus reads, for each image, a PAGE-XML of the same name from a
`page/` subfolder; one folder = one document:

```
{doc}/
  {doc}_p001.png          # image at top level
  page/{doc}_p001.xml     # PAGE-XML with matching name
```

`scripts/edition/transkribus_export.py` builds this structure from `output/page_xml/` +
`docs/images/{doc}/` into `output/transkribus_upload/` (gitignored). Selection: `--sample`
(stratified over page count x language), `--all`, `--reference` (the 24 objects that
ZBZ already has in its own Transkribus collection), `--doc`. For each page it verifies
that the PNG pixel dimensions match the declared `imageWidth`/`imageHeight`
(coordinates aligned); pages without an image or with dimension drift are reported instead
of silently copied. The export runs over the PAGE-XML, not over the images; pages without
layout (e.g. blank pages) stay out.

### Dialect

Compatible out of the box (TextRegion/Coords/TextLine/TextEquiv/
ReadingOrder + `custom` structure types). Limitation: the pipeline PAGE carries
line polygons but no baselines; for import, display, and structure that is sufficient,
only HTR training in Transkribus needs baselines (the ZBZ originals have them). The
pipeline images are 1240x1754 (150 dpi), the ZBZ originals 2479x3508 (300 dpi); each
state is internally consistent.

### Upload via API

`scripts/edition/transkribus_upload.py` uploads the built bundles
via the legacy TrpServer REST API (`transkribus.eu/TrpServer/rest`): `POST /auth/login`
-> `POST /uploads?collId=` (JSON manifest with `md.title` + `pageList`) -> `PUT
/uploads/{id}` (image + XML per page). Verified 2026-06-08: the legacy API writes
correctly into a collection on the new platform (app.transkribus.org); login and
collection share the readcoop account. Auth exclusively via environment variables
(`TRANSKRIBUS_USER`/`TRANSKRIBUS_PASSWORD`/`TRANSKRIBUS_COLLECTION`), never in code/repo/.env.
Every run creates new documents (no dedup); before a full upload run `--dry-run`
(checks login + access) and `--doc {ID}` (one test object). CLI:
[CLAUDE.md §Transkribus Export / Upload](../CLAUDE.md).

---

## References

- [methodology.md](methodology.md): operational tools, CLI reference, work cycle
- [specification.md](specification.md): quality method + validation rule catalog
- [workflow.md](workflow.md): viewer with layout and transcription editor, persistence
- [infrastructure.md](infrastructure.md): Azure, Podman, CI/CD
- [decisions.md](decisions.md): decision register
