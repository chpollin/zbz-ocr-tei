---
type: knowledge
created: 2026-01-29
updated: 2026-02-27
tags: [zbz-ocr-tei, testplan, evaluation, metrics]
status: active
---

# Test Plan

Systematic OCR evaluation across all document types. Single source of truth for test phases, metrics, and results.

**Dependencies:** [QUELLENANALYSE](QUELLENANALYSE.md) (pilot files, document types), [OCR-ENGINES](OCR-ENGINES.md) (engine selection)

---

## Goal

1. Identify layout-specific problems
2. Develop document-type-dependent processing strategies
3. Establish quality metrics per document type

---

## Test Phases

Pilot files and document types: See [QUELLENANALYSE](QUELLENANALYSE.md) §Pilot Files.

### Phase 1: Baseline (Type A - single-column)

**Goal:** Validate OCR baseline quality

| Step | PDF | Pages | Test |
|------|-----|-------|------|
| 1.1 | 2310 | 2-3 | French text, accents |
| 1.2 | 1180 | 2 | German text, continuous prose |
| 1.3 | 290 | 1 | French essay |

**Status:** Completed (DeepSeek + Mistral)

### Phase 2: Layout Challenges (Type B - two-column)

**Goal:** Test column reading order

| Step | PDF | Pages | Test |
|------|-----|-------|------|
| 2.1 | 2530 | 1-2 | Columns correct? |
| 2.2 | 890 | 2 | Two-column + small font |
| 2.3 | 3040 | 1 | Lexicon: columns + footnotes |
| 2.4 | 2530 | 1-2 | Gemini 3 Agentic Vision test |

**Known issue:** 2530 has incorrect column order with DeepSeek.

**Three solution approaches:** See [DECISIONS](DECISIONS.md) O10.

**Status:** Mistral OCR completed, Gemini pending

### Phase 3: Special Formats (Type D)

**Goal:** Identify edge cases

| Step | PDF | Pages | Test |
|------|-----|-------|------|
| 3.1 | 90 | 2 | Historical print (1944) |
| 3.2 | 1440 | 1-2 | Detect interview/dialogue |
| 3.3 | 830 | 1 | Photo book: text next to image |
| 3.4 | 1330 | 1-2 | Anthology structure |

**Status:** Mistral OCR completed

### Phase 4: Monographs (Type C)

**Goal:** Test scalability

| Step | PDF | Pages | Test |
|------|-----|-------|------|
| 4.1 | 40 | 5-6 | Novel continuous prose |
| 4.2 | 1520 | 3-4 | Monograph content |

**Status:** Completed (Mistral OCR + page-by-page comparison)

---

## Results

### Evaluation Matrix: Mistral Document AI 2512 (18.02.2026)

| PDF | Type | CER | WER | Accuracy | Status | Notes |
|-----|------|-----|-----|----------|--------|-------|
| 2310 | A | 7.00% | 22.04% | 93.00% | Acceptable | JSTOR cover distorts alignment |
| 1180 | A | 3.12% | 10.45% | 96.88% | OK | Annual report, very good |
| 290 | A | 18.07% | 28.17% | 81.93% | Problematic | Scan quality? |
| 2530 | B | 3.96% | 17.06% | 96.04% | OK | Two-column, well recognized |
| 890 | B | 5.96% | 12.80% | 94.04% | Acceptable | Teacher newspaper |
| 3040 | B | 9.02% | 22.73% | 90.98% | Acceptable | Lexicon with footnotes |
| 90 | D | 1.21% | 8.92% | 98.79% | OK | Historical 1944, excellent |
| 1440 | D | 3.71% | 12.69% | 96.29% | OK | Interview/dialogue |
| 830 | D | 4.00% | 17.46% | 96.00% | OK | Photo book |
| 1330 | D | 2.60% | 11.42% | 97.40% | OK | Anthology |
| 40 | C | 2.57% | 10.76% | 97.43% | OK | Page-by-page comparison (147 TEI pages) |
| 1520 | C | 2.73% | 15.20% | 97.27% | OK | Page-by-page comparison (116 TEI pages, offset +8) |
| 1060 | A | 22.60% | 27.88% | 77.40% | Problematic | Alignment issue with 6-page PDF |
| 130 | A | 4.13% | 16.11% | 95.87% | OK | Page-by-page (16 TEI pages), cover page correctly ignored |
| 1410 | A | 5.58% | 13.83% | 94.42% | Acceptable | Bilingual DE/FR |

**Average Phase 1-3 (10 Docs): CER 5.87%, Accuracy 94.14%**
**Average Phase 4 (2 Docs): CER 2.65%, Accuracy 97.35%**
**Average all 15 Docs: CER 6.42%, Accuracy 93.58%**

**Dashboard:** Results visually presented in `docs/index.html` (metric cards, CER comparison bars, document catalog with engine filter).

| Phase | Avg CER | Avg WER | Avg Accuracy |
|-------|---------|---------|--------------|
| Phase 1 (Type A) | 9.40% | 20.22% | 90.60% |
| Phase 2 (Type B) | 6.31% | 17.53% | 93.69% |
| Phase 3 (Type D) | 2.88% | 12.62% | 97.12% |
| Phase 4 (Type C) | 2.65% | 12.98% | 97.35% |

### Evaluation Matrix: LLM Post-Correction Haiku 4.5 (19.02.2026)

Variant C (Few-Shot), all 15 Docs:

| Phase | Mistral CER | LLM CER | Delta |
|-------|-------------|---------|-------|
| Phase 1 (A) | 9.40% | 8.43% | -0.97 |
| Phase 2 (B) | 6.31% | 6.34% | +0.03 |
| Phase 3 (D) | 2.88% | 2.72% | -0.16 |
| Phase 4 (C) | 2.65% | 2.70% | +0.05 |
| **Total (15 Docs)** | **6.42%** | **6.52%** | **+0.10** |

Three variants tested (Phase 1-3): A (5.47%), B (5.59%), C (5.55%). Variant C as default (best CER/cost tradeoff).

Note: LLM correction improves docs with high CER, slightly degrades results for good OCR (Phase 2, 4).

### Evaluation Matrix: DeepSeek-OCR-2 (local, Phase 1 only)

| PDF | Type | CER | WER | Accuracy | Status | Notes |
|-----|------|-----|-----|----------|--------|-------|
| 2310 | A | 2.67% | 16.61% | 97.33% | OK | Only 2 pages tested |
| 1180 | A | 4.89% | 13.29% | 95.11% | OK | Only 2 pages tested |
| 290 | A | 9.21% | 19.53% | 90.79% | OK | Only 2 pages tested |

Note: DeepSeek results are based on 2 test pages per doc, Mistral on all pages.

### Layout Analysis: Docling 2.75 (25.02.2026)

8/15 docs analyzed (7 docs need GPU: 2530, 290, 3040, 40, 830, 890, 90).

| Doc | Type | Pages | Regions | Heading Detection | Paragraph Segmentation | Issues |
|-----|------|-------|---------|-------------------|------------------------|--------|
| 1180 | A | 8 | 55 | Very good (title, theses) | Good, but overlaps on p2 | Single-line fragments, page numbers as text |
| 2310 | A | 3 | 27 | Good | Good | None |
| 130 | A | 18 | 67 | Good | Good | None |
| 1410 | A | 6 | 65 | Very good (two-column) | Good, columns correctly separated | None |
| 1060 | A | 8 | 36 | OK | OK | Few regions |
| 1330 | D | 6 | 56 | Good | Good | None |
| 1440 | D | 5 | 59 | Good | Good | None |
| 1520 | C | 132/142 | ~900 | OK | OK | Analysis aborted (10 pages missing) |

**Known Issues:**
1. **Overlapping regions:** Single-line items (h_pct <3%) overlap with larger blocks (e.g. 1180 p2)
2. **Page numbers:** Docling recognizes page numbers (217-220) as `text` instead of `page_footer` — heuristic needed
3. **Missing footnotes:** No `footnote` label seen in samples (may differ for docs with footnotes)

**Post-Processing (O21):** 3 heuristics planned: overlap filter, single-line merge, page number detection.

### Rating Scale

- **OK:** CER < 5% (character accuracy > 95%)
- **Acceptable:** CER 5-15% (manually correctable)
- **Problematic:** CER > 15% or structural errors (LAYOUT)

### Metrics

- **CER** (Character Error Rate): proportion of incorrect characters
- **WER** (Word Error Rate): proportion of incorrect words
- **Accuracy**: 100% - CER

---

## CLI Commands

```bash
# OCR with Mistral (no GPU, requires .env)
python -m scripts.ocr_pipeline -i data/scans/2310.pdf -e mistral -o output/mistral_results

# Evaluation: Mistral, all phases
python -m scripts.evaluate_ocr --phase all --ocr-dir output/mistral_results --engine mistral

# Evaluation: Single phase
python -m scripts.evaluate_ocr --phase phase1 --ocr-dir output/mistral_results --engine mistral

# Evaluation: DeepSeek comparison
python -m scripts.evaluate_ocr --all --ocr-dir output/ocr_results --engine deepseek

# OCR tests by phase with DeepSeek (GPU required)
python scripts/test_all_pdfs.py --phase phase1
```

---

## Next Steps

1. [x] Create test script `test_all_pdfs.py`
2. [x] Run Phase 1 (DeepSeek baseline)
3. [x] Create evaluation script `evaluate_ocr.py`
4. [x] Test Mistral Document AI on Phase 1 (`test_mistral_ocr.py`)
5. [x] Create benchmark UI (`docs/benchmark.html`)
6. [x] Calculate CER/WER for Mistral against reference TEI
7. [x] Run Phase 2-4 with Mistral
8. [x] Complete evaluation matrix (Phase 1-3)
9. [ ] Investigate Doc 290: Why CER 18%? Check scan quality
10. [x] Phase 4 evaluation: Implement page-by-page comparison
11. [x] OCR + LLM + eval for all 15 pilot documents completed
12. [ ] Test Gemini 3 Flash on Type B (2530)
13. [ ] Investigate Doc 1060: CER 22.6% despite Type A — alignment issue
14. [ ] Derive recommendation for production pipeline
15. [x] Layout analysis: 8/15 docs analyzed with Docling + overlay PNGs generated
16. [ ] Implement layout post-processing (O21: overlap, single-line, page numbers)
17. [ ] Layout analysis for remaining 7 docs (needs GPU)
18. [ ] Check footnote detection (Doc 3040 = lexicon with footnotes)

---

## References

- [QUELLENANALYSE](QUELLENANALYSE.md) for pilot files and document types
- [OCR-ENGINES](OCR-ENGINES.md) for engine-specific information
- [DECISIONS](DECISIONS.md) O10 for column solution approaches

---

*Created: 2026-01-29 | Updated: 2026-02-27 (Layout analysis 8/15 docs + QA results)*
