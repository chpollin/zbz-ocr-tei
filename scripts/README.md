# Scripts

Python scripts for the OCR pipeline.

## Overview

| Script | Purpose | GPU |
|--------|---------|-----|
| `config.py` | Central configuration (paths, model settings) | No |
| `utils.py` | Shared utility functions | No |
| `ocr_pipeline.py` | OCR with Mistral/DeepSeek/Docling | Yes (DeepSeek) |
| `test_all_pdfs.py` | Main OCR tests by phase | Yes |
| `llm_postprocess.py` | LLM post-correction (Claude Haiku 4.5) | No |
| `run_layout_analysis.py` | Layout analysis (Docling) + overlay PNGs | Yes (Docling) |
| `tei/tei_generator.py` | TEI-XML from layout JSON + OCR Markdown | No |
| `evaluate_ocr.py` | CER/WER evaluation with HTML report | No |
| `extract_pages.py` | PDF to page images (PNG) | No |
| `extract_gnd.py` | Extract GND IDs from reference TEI | No |

## Usage

```bash
# Run OCR tests (GPU required)
python scripts/test_all_pdfs.py --phase phase1

# Evaluation (no GPU)
python scripts/evaluate_ocr.py --all

# GND extraction
python scripts/extract_gnd.py
```

---

*Updated: 2026-05-25*
