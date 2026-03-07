---
type: knowledge
created: 2026-01-29
updated: 2026-02-27
tags: [zbz-ocr-tei, corpus, document-types, pilot]
status: active
---

# Source Analysis

Analysis of the PDF source digitizations for the Jeanne Hersch edition project. Single source of truth for corpus data, document types, and pilot files.

**Dependencies:** None (foundational document)

---

## Corpus Overview

| Aspect | Value |
|--------|-------|
| Total entries in Masterfile | 327 |
| Excluded (translations/reprints) | 38 |
| Effective corpus size | 286 texts (Masterfile lists 289; 3 missing — see [DECISIONS](DECISIONS.md) O22) |
| Total page count | approx. 7,200 pages |
| Median per text | 6 pages |
| Maximum | 588 pages |
| Time period | 1931-2010 |
| Focus | 1970s/1980s (191 texts) |

---

## Publication Types

| Genre | Count | Share |
|-------|-------|-------|
| Journal articles (journalArticle) | 159 | 49% |
| Edited volume contributions (bookSection) | 127 | 39% |
| Monographs (book) | 38 | 12% |
| Audiovisual medium | 1 | <1% |

The dominance of short articles (median 6 pages) enables fast iterations in the PoC. The 38 monographs (up to 588 pages) require chunking strategies.

---

## Language Distribution

| Language | Count | Share |
|----------|-------|-------|
| French | 215 | 66% |
| German | 98 | 30% |
| English | 8 | 2% |
| Italian | 2 | 1% |
| Bilingual (fr/de) | 1 | <1% |

### Implications for the Pipeline

1. **OCR**: French typography (guillemets, accents, ligatures)
2. **Hyphenation**: French hyphenation rules differ from German ones
3. **Normalization**: Remove spaces before `:;?!` (French convention)
4. **Prompt design**: Examples primarily in French

---

## Processing Status

### Masterfile (Survey Jan 2026)

| Phase | Count | Share |
|-------|-------|-------|
| Digitized | 289 | 88% |
| Corrected | 122 | 37% |
| TEI-annotated | 21 | 6% |
| Published | 0 | 0% |

### Data Delivery Feb 2026 (E23)

| Category | Count | Notes |
|----------|-------|-------|
| PDFs with completed TEI annotation | 24 | + PAGE-XML export (Transkribus, schema 2013, empty) |
| Completed TEI-XMLs | 25 | 890 + 1520 have XML, but PDF in different folder |
| PDFs without annotation | 262 | Not yet processed |
| **Total delivered** | **286 PDFs** | Masterfile counts 289 — 3 discrepancy unresolved (→ [DECISIONS](DECISIONS.md) O22) |

**PAGE-XML detail:** 24 Transkribus exports contain **302 pages total** (all empty — no TextRegions). Largest: Doc 40 (156 pages), Doc 760 (20), Doc 130 (18), Doc 3040 (10). Most documents have 3-8 pages.

The bottleneck is TEI annotation. This is where the LLM pipeline provides the greatest added value.

---

## Document Types (A-D)

Classification of all documents into 4 types with different pipeline strategies.

| Type | Layout | Description | Pipeline Strategy |
|------|--------|-------------|-------------------|
| **A** | Single-column | Standard running text | OCR direct (DeepSeek/Mistral) |
| **B** | Two-column | Journals, encyclopedias | Layout analysis + OCR per region, or Gemini Agentic Vision |
| **C** | Monograph | Long texts (100+ pages) | OCR + chunking |
| **D** | Special | Historical prints, interviews, illustrated books | Case-by-case treatment |

---

## Pilot Files (15 PDFs)

Single source of truth for all pilot PDF metadata. Other documents reference this section.

| File | Pages | Language | Type | Text Genre | Special Feature |
|------|-------|----------|------|------------|-----------------|
| 2310.pdf | 3 | FR | A | Review | JSTOR metadata |
| 1180.pdf | 8 | DE/FR | A | Annual report | Title page |
| 130.pdf | 18 | FR | A | Journal article | Cover page |
| 290.pdf | 5 | FR | A | Comptes Rendus | Essay |
| 1410.pdf | 6 | DE/FR | A | Contribution | Bilingual, partly two-column (p5) |
| 1060.pdf | 8 | DE | A | Brochure | Speech |
| 2530.pdf | 2 | FR | B | Article | Two-column |
| 890.pdf | 7 | DE | B | Teachers' journal | Small font |
| 3040.pdf | 9 | FR | B | Encyclopedia | Footnotes |
| 40.pdf | 156 | FR | C | Novel | Handwritten notes |
| 1520.pdf | 142 | FR | C | Monograph | Long |
| 90.pdf | 6 | DE | D | Historical print | 1944 |
| 830.pdf | 2 | FR | D | Illustrated book | Little text |
| 1440.pdf | 5 | DE | D | Interview | Dialogue format |
| 1330.pdf | 6 | FR | D | Edited volume | Foreword |

---

## Identified Problem Cases

| Problem | Affected PDFs | Solution Approach |
|---------|---------------|-------------------|
| Two-column reading order | 2530, 890, 3040 | Docling Layout or Gemini Agentic Vision |
| Cross-page footnotes | 3040 | `@next/@prev` chaining |
| Interview speaker changes | 1440 | Pattern recognition |
| Historical print | 90 | Test both OCR engines |
| Handwritten annotations | 40 | Still open |
| ~~Language unknown~~ | ~~1520~~ | Resolved: French (25.02.2026) |

---

## Typography

### French Particularities (Relevant for OCR)

| Character | Example | OCR Error Risk |
|-----------|---------|----------------|
| Guillemets | << >> | Often recognized as " " |
| Ligatures | oe (coeur) | Usually correct |
| Accents | e e e e | Occasional errors |
| Apostrophe | l'homme | U+2019 vs U+0027 |

### Print Quality

- Newer prints (1950+): Easily readable
- Historical print 90.pdf (1944): Slightly limited

### Scan Quality

| Aspect | Assessment |
|--------|------------|
| Resolution | Sufficient for OCR |
| Contrast | Good to very good |
| Distortions | Minimal |
| Completeness | No missing pages detected |

---

## References

- [TESTPLAN](TESTPLAN.md) for OCR test results per pilot file
- [ENGINES](ENGINES.md) for engine selection per document type
- [PIPELINE](PIPELINE.md) for pipeline strategies

---

*Created: 2026-01-29 | Updated: 2026-02-27 (Data delivery E23: 286 PDFs, 25 TEI-XMLs)*
