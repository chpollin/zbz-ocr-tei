---
type: knowledge
created: 2026-03-05
updated: 2026-03-05
tags: [zbz-ocr-tei, learnings, patterns, pitfalls]
status: active
---

# Learnings

Technical insights and patterns from 26 experiments (E1-E26). Not what we decided ([DECISIONS](DECISIONS.md)) or what we did ([JOURNAL](JOURNAL.md)), but what we **learned**.

**Dependencies:** Cross-cutting — distills from all documents.

---

## OCR

### Model selection matters less than pipeline design

- DeepSeek (local, 3B) and Mistral (Azure API) produce similar CER (94-97% vs 93.58%)
- The bigger difference comes from **pre/post-processing**: layout-aware chunking, page matching, header/footer filtering
- Takeaway: Invest in pipeline quality, not model shopping

### LLM post-correction is a double-edged sword (E17)

- **Helps** at CER >10%: fixes garbled text, merged words
- **Hurts** at CER <5%: "corrects" correct proper names, French accents, archaic spellings
- Takeaway: LLM correction is optional, not default. Only apply where baseline OCR is poor

### Cost is negligible

- 330 pages OCR + LLM correction = ~$1.55
- Projection 7,200 pages full pipeline: ~$35
- Gemini Layout QA+Detect for 4,152 pages: ~$3-4
- Takeaway: API costs are not a constraint — developer time is the bottleneck

### French text breaks some OCR engines (E2)

- Docling's built-in RapidOCR: `e` becomes `O` in French text
- Solution: Use Docling only for layout, OCR separately via Mistral/DeepSeek
- Takeaway: Always test with the actual corpus language, not just English benchmarks

---

## Layout Analysis

### Coverage-based quality scoring works well

- Simple heuristic: bbox coverage as % of page area
- Thresholds: good (>30%), warning (15-30%), bad (<15%), empty (0 regions)
- Result: 75% good, 10% warning, 12% bad, 3% empty
- Takeaway: You don't need ML for quality classification — coverage percentage is a strong proxy

### Landscape/multi-column pages are the hard cases

- Portrait pages: ~86% good
- Landscape pages: ~64% bad — Docling struggles with wide formats
- Multi-column encyclopedias: fragmented boxes, missed columns
- Takeaway: Build separate strategies for standard vs. difficult pages (auto-routing)

### Hybrid approach beats single-engine (E19, E25, E26)

- Docling alone: 75% good
- Docling + Gemini QA: fixes labels on good pages (headers, footers, page numbers)
- Docling + Gemini Detect: re-detects layout on bad pages from scratch
- Auto mode routes by quality — best of both worlds
- Takeaway: Use the right tool for the right quality level, don't force one engine to do everything

### Vision LLMs can do layout detection (E26)

- Gemini Flash Lite with Structured Output returns usable bounding boxes (`box_2d` 0-1000 grid)
- Quality comparable to specialized models on bad pages
- Limitation: rightmost column missed on very wide landscape pages
- Limitation: photo/figure detection unreliable
- Takeaway: Vision LLMs are viable layout detectors for fallback, not yet for primary detection

---

## Gemini API

### Flash Lite is dramatically cheaper with same quality (E26)

- Initial tests showed cheaper models match expensive ones on layout tasks
- Cost: Flash Lite $0.25/1M input (production choice)
- Takeaway: Always benchmark the cheapest model first — "bigger" does not mean "better" for structured tasks

### `thought_signature` warnings are harmless but noisy

- Flash Lite returns `thought_signature` parts in responses
- SDK warns: "non-text parts in the response"
- Workaround: `PYTHONWARNINGS=ignore` or `warnings.filterwarnings` in code
- Does not affect result quality
- Takeaway: Suppress known warnings early, they drown real errors in batch runs

### Structured Output is essential for layout tasks

- Without `response_schema`: inconsistent JSON, missing fields, hallucinated keys
- With `response_schema`: reliable, parseable output every time
- Takeaway: Always use Structured Output when you need machine-readable results from LLMs

### Resume capability is non-negotiable for batch processing

- 4,152 pages at ~5s/page = ~5.5h total runtime
- Network errors, rate limits, API outages are guaranteed over hours
- Skip-existing pattern (`if file exists: skip`) enables safe restarts
- Takeaway: Every batch script must be idempotent and resume-capable

---

## TEI / Pipeline Architecture

### Page matching is harder than expected (E16, E18)

- TEI page numbers != PDF page numbers (cover pages, blanks, inserts)
- Fixed offset drifts across a document
- Solution: content-based matching (text similarity between OCR and TEI)
- Takeaway: Never assume page numbers are reliable — always match by content

### Monographs behave differently from articles

- Articles (1-10 pages): global alignment works
- Monographs (50-250 pages): need page-by-page comparison
- CER varies dramatically: monographs 2.65%, articles 6-22%
- Takeaway: Design for the hardest case (monographs), not the average case

### Keep both versions (epistemic infrastructure, E25)

- Docling layout = `_layout.json`, Gemini correction = `_layout_gemini.json`
- Never overwrite the original — corrections are interpretive, not ground truth
- Viewer shows both layers with toggle
- Takeaway: In digital humanities, preserving provenance is as important as improving quality

---

## Development Patterns

### Windows encoding bites in batch processing

- Python print() with Unicode characters fails in Windows console
- `\u2014`, `\u2019` etc. cause UnicodeEncodeError in batch output
- Solution: ASCII-only in print statements, or `PYTHONIOENCODING=utf-8`
- Takeaway: Test batch output on the target OS, not just in IDE

### Single Source of Truth prevents documentation drift

- 14 knowledge files with cross-references
- Each fact lives in exactly one document
- Example: CER results only in TESTPLAN.md, referenced from ENGINES.md
- Takeaway: Duplication is the enemy — it always diverges eventually

### Auto-routing by quality is a powerful pattern

- Instead of: run everything through the same pipeline
- Better: classify input quality, route to appropriate processing
- Applied: Docling quality -> Gemini QA (good pages) vs Detect (bad pages)
- Generalizable: could apply to OCR engine selection, post-processing intensity
- Takeaway: Quality-aware routing reduces cost and improves results simultaneously

---

## References

- [DECISIONS](DECISIONS.md) for what was decided (E1-E26)
- [JOURNAL](JOURNAL.md) for chronological work log
- [ENGINES](ENGINES.md) for engine details and benchmarks
- [TESTPLAN](TESTPLAN.md) for quality metrics

---

*Created: 2026-03-05 | Updated: 2026-03-05*
