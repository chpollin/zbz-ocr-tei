---
title: Project
type: knowledge
project:
  name: zbz-ocr-tei
  repository: https://github.com/chpollin/zbz-ocr-tei.git
method:
  name: Promptotyping
  url: https://dhcraft.org/Promptotyping/
status: complete
created: 2026-02-18
updated: 2026-07-07
tags: [zbz-ocr-tei, project, corpus, zbz, workflow]
---

# Project

LLM-supported OCR and TEI pipeline for the Jeanne Hersch papers (Nachlass) of the Zentralbibliothek Zuerich.

---

## Commission

| Aspect | Details |
|---|---|
| Client | Zentralbibliothek Zuerich (ZBZ) |
| Contractor | DHCraft |
| Subject | Automated OCR + TEI annotation for the Hersch papers |
| Confirmation | 14.02.2026 |
| Fee | unchanged |
| ZBZ contacts | ZBZ project team (contact persons documented internally) |
| Project lead | DHCraft |

Since the coordination meeting (25.02.2026, E21), zbz-ocr-tei covers the complete pipeline
path of OCR, layout, PAGE-XML, and TEI-XML. ZBZ keeps Transkribus in parallel as a second source.

---

## Corpus

All figures here are generated via `python -m scripts.eval.corpus_audit` (artifact
`output/corpus_audit.json` / `.md`, every figure bound to `(source, unit, extraction)`);
regenerate on change, do not maintain by hand. As of 2026-05-27.

The corpus funnel runs 325 Masterfile texts -> 289 digitized -> 286 delivered as PDF ->
285 with final TEI. The figure "289" is the Masterfile's `digitalisiert` counter, not
the number of texts. 3 digitized texts are without PDF delivery, namely `1745`, `1750`, `1970`;
1 PDF is without final TEI, namely `10`.

Page counts come in four units that must never be mixed:

| Unit | Value | Source |
|---|---|---|
| bibliographic | 7,186 | Masterfile (text level, n=325) |
| physical | 4,152 | delivered PDFs (pypdfium2) |
| processed (OCR) | 4,122 | pipeline (volatile on re-OCR) |
| processed (TEI `<pb>`) | 4,115 | final TEI |

Median 6 pages/text, maximum 588 (Masterfile, bibliographic).

### Genres, Languages, Period (delivered documents, n=286)

The delivered view is authoritative (Masterfile metadata of the 286 PDFs), not the
catalogued total holdings. Period 1931-1998, with 168 texts from the 1970s and 1980s.

| Genre (`PublForm`) | n | Share |
|---|---|---|
| Journal articles (`journalArticle`) | 146 | 51% |
| Edited volume contributions (`bookSection`) | 116 | 41% |
| Monographs (`book`) | 24 | 8% |

| Language | n | Share |
|---|---|---|
| French | 203 | 71% |
| German | 72 | 25% |
| English | 7 | 2% |
| Italian | 2 | <1% |
| bilingual fr/de | 1 | <1% |
| not specified | 1 | <1% |

Gemini's PDF classification (`doc_metadata.json`) overestimates multilingualism; for
metadata the Masterfile is authoritative. The consequence for the pipeline is French
typography (guillemets, accents, ligatures, spaces before punctuation), French
hyphenation rules, and predominantly French prompt examples.

> For comparison, the catalogue level (n=325, entire recorded holdings) shows genre `journalArticle` 159 / `bookSection` 127 / `book` 38 / AV medium 1; language fr 215 / de 98 / en 8 / it 2 / fr-de 1 / not specified 1; period 1931-2010, 193 in the 1970s/80s.

### Document Types A-D

| Type | Layout | Strategy |
|---|---|---|
| A | single-column | direct OCR (Mistral) |
| B | two-column (journals, encyclopedias) | layout analysis + OCR per region (Docling + Gemini) |
| C | monograph (100+ pages) | OCR + chunking, page-by-page comparison (E16) |
| D | special (historical, interview, illustrated book) | case by case |

### Pilot Files (15 PDFs)

| File | Pages | Language | Type | Genre | Peculiarity |
|---|---|---|---|---|---|
| 2310.pdf | 3 | FR | A | review | JSTOR cover |
| 1180.pdf | 8 | DE/FR | A | annual report | title page |
| 130.pdf | 18 | FR | A | journal article | cover page |
| 290.pdf | 5 | FR | A | Comptes Rendus | essay |
| 1410.pdf | 6 | DE/FR | A | contribution | bilingual, partly two-column |
| 1060.pdf | 8 | DE | A | brochure | speech |
| 2530.pdf | 2 | FR | B | article | two-column |
| 890.pdf | 7 | DE | B | teachers' journal | small print |
| 3040.pdf | 9 | FR | B | encyclopedia | footnotes |
| 40.pdf | 156 | FR | C | novel | handwritten notes |
| 1520.pdf | 142 | FR | C | monograph | long |
| 90.pdf | 6 | DE | D | historical print | 1944 |
| 830.pdf | 2 | FR | D | illustrated book | little text |
| 1440.pdf | 5 | DE | D | interview | dialogue format |
| 1330.pdf | 6 | FR | D | edited volume | preface |

### Data Delivery Feb 2026 (E23)

| Category | Count | Note |
|---|---|---|
| PDFs with complete TEI annotation | 24 | + PAGE-XML export (Transkribus, schema 2013, empty) |
| Complete TEI XMLs | 25 | 890 + 1520 have XML but PDF in a different folder |
| PDFs without annotation | 262 | not yet processed |

In the PAGE-XML detail, the 24 Transkribus exports contain 302 pages in total, all empty (no TextRegions). The bottleneck is TEI annotation; this is where the LLM pipeline adds the greatest value.

---

## Status

For current metrics (CER, file counts, validation) see the corpus overview `docs/index.html`,
the report `reports/arbeitsbericht-v3.md`, and the canonical values in `docs/data/cer_statistics.json`.

### Milestones

| # | Milestone | Success criterion | Status |
|---|---|---|---|
| M0 | Image extraction + QA viewer | images + viewer available | Done |
| M1 | OCR validated | >=93% accuracy for all types | Done |
| M2 | Layout + PAGE-XML | regions + bbox + PAGE-XML for all docs | Done |
| M3 | NER + Wikidata | recall >70%, linking >50% | Removed (E71, 2026-05-27; linking in the output not deliverable) |
| M4 | TEI-XML | DTA-conformant, schema-valid | Done (whole corpus valid against `zbz_hersch.rng`, gate `tests/test_tei_schema.py`) |
| M5 | Data handover to ZBZ | full corpus processed + delivered schema-valid; scholarly verification is a ZBZ task (tracked via workflow status) | Data delivered; all streams `unverifiziert` as handover default (E66/E67); scholarly curation lies with ZBZ |

> The identifier "M3" carries a second meaning. In the current substantive roadmap
> (journal session 74 ff., [decisions.md](decisions.md) E90) it designates the
> operator-gated delivery of the reading-order structure fix to the delivered corpus,
> not the removed NER milestone in this table. There the dry run is available
> (`reports/m3-reassemble-preview.md`); approval is pending.

### Component Status

| Component | Status | Details |
|---|---|---|
| Image extraction | Done | `scripts/edition/extract_pages.py` |
| OCR (Mistral) | Done | `scripts/ocr/ocr_pipeline.py` |
| LLM post-correction (Haiku) | Done, optional (E17) | `scripts/ocr/llm_postprocess.py`, harmful at CER <5% |
| Gemini OCR correction | Sample | `scripts/ocr/gemini_ocr_correct.py` (E29) |
| Layout (Docling) | Done | `scripts/layout/run_layout_analysis.py` |
| Layout QA (Gemini) | Done | `--mode auto` (E25/E26/E31) |
| PAGE-XML generator | Done | `page_xml_generator.py` + METS |
| Document classification | Done | `classify_docs.py` (E27) |
| NER + entity linking | Removed (E71) | removed from pipeline + output; linking was not deliverable |
| Unified TEI pipeline | Done | schema-valid across the corpus (E32) |
| TEI validator | Done | RelaxNG + 7 project rules (R1-R7) + 16 active warning rules (W1-W7, W11-W19; W15-W18 since E84, W19 reading order since E90) |
| Workflow status per stream (E66/E67) | Done (data model) | replaces agent screening; streams start `unverifiziert`, settable in the viewer, provenance in the manifest |
| Pipeline viewer (E56) | Done | `docs/viewer.html` single page with layout + transcription editor; persistence directly into repo + mirror (E72/E78/E79), download as fallback |
| Viewer edition uplift (May 2026) | largely implemented | Delivered: E58 (OSD facsimile), E60 (edit toggle per panel), E62 (method page), E63/E65 (blank-page manifest + TEI marker), E66/E67 (workflow status + traffic-light reframing + catalog refactor). Open: E61 (export module, JSZip; planned, not yet wired into the code), complete TEI (`<facsimile>`/`<zone>`) + provenance drawer (planned, separate pipeline wave), OSD layout editor integration, viewer.js module split. Open frontend findings: [specification.md](specification.md), frontend requirements |
| Workflow + provenance | Concept documented | [workflow.md](workflow.md) describes data flow, save mechanism, round trip, the `_complete.xml` and `provenance.json` concept |
| Containerization | Pending | Dockerfile/Podman |
| CI/CD | Partial | GitHub Actions active (pytest on push/PR, 2026-06-10); GitLab Uni Zuerich pending |

---

## ZBZ Workflow (Current State)

Context knowledge about the manual edition production at ZBZ, relevant for integration
points. The source is `WorkflowDiagramm_Hersch.pdf` (removed, fully absorbed into this document).

### Three Parallel Tracks

1. Transcription: digitized images -> Transkribus -> GitLab -> Oxygen -> GitLab
2. Metadata: digitized images -> Alma -> Masterfile -> Swisscovery -> TEI header
3. Correction loop: Oxygen -> PDF -> external reviewers -> Oxygen

The Masterfile (Excel) is the central coordination point.

### Systems

| System | Function | Format |
|---|---|---|
| Transkribus | OCR/HTR + transcription | not standardized |
| Masterfile | workflow + status | Excel |
| GitLab | TEI versioning | XML |
| Oxygen | TEI markup + transformation | XML |
| Alma | cataloguing + metadata | catalogue data |
| Swisscovery | discovery | catalogue data |
| GND | authority-data linking | IDs |

### Observations

- Almost all steps are manual.
- The Transkribus process is not standardized.
- The TEI header workflow from Alma does not yet exist ([decisions.md](decisions.md) O8).
- External corrections run via PDF, not directly on the XML.
- GND linking in Oxygen is manual.

### Integration with the AI Pipeline

Since E21, zbz-ocr-tei replaces or complements the following steps:

| Existing step | Replaced by |
|---|---|
| Transkribus OCR | batch OCR (Mistral) |
| Manual Transkribus export | automatic PAGE-XML export |
| Oxygen TEI markup | automatic TEI transformation |

### What Remains Manual

- Alma cataloguing (library-specific)
- Masterfile maintenance (coordination)
- Swisscovery assignment
- TEI header from Alma (workflow does not yet exist, O8)
- Final QA in Oxygen before publication

---

## Known Problem Cases

| Problem | Affected PDFs | Approach |
|---|---|---|
| Two-column reading order | large majority of the delivered corpus (audit), focal points incl. 810/1520/2360/760 | Docling + Gemini detect; column- and band-aware assembly order (E90), W19 checks the corpus; `scripts/eval/reading_order_audit` triages robust/fragile for the M3 view; delivery of M3 gated |
| Cross-page footnotes | 3040 | `@next/@prev` |
| Interview speaker changes | 1440 | pattern recognition |
| Historical print | 90 | test both OCR engines |
| Handwritten annotations | 40 | open |

---

## References

- [pipeline.md](pipeline.md): technical pipeline details
- [specification.md](specification.md): quality method and validation rules
- `reports/arbeitsbericht-v3.md`: the project report; measured values in `docs/data/cer_statistics.json`
- [cer-methodology.md](cer-methodology.md): CER measurement method
- [decisions.md](decisions.md): open points and decisions
- [infrastructure.md](infrastructure.md): deployment + APIs
