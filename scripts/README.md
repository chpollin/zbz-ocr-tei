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
| `generate_dashboard_data.py` | Generate dashboard data | No |
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

## Postprocess Module

```
postprocess/
├── __init__.py
├── clean_markdown.py   # Remove Markdown syntax
├── dehyphenate.py      # Resolve hyphenation
├── normalize.py        # Normalize characters
└── pipeline.py         # Combined pipeline
```

Usage:
```python
from scripts.postprocess import process_text
clean = process_text(raw_ocr_output)
```

---

*Updated: 2026-02-27*
