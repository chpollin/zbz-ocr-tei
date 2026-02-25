# Scripts

Python-Skripte für die OCR-Pipeline.

## Übersicht

| Skript | Zweck | GPU |
|--------|-------|-----|
| `ocr_pipeline.py` | OCR mit Mistral/DeepSeek/Docling | Ja (DeepSeek) |
| `test_all_pdfs.py` | Haupt-OCR-Tests nach Phasen | Ja |
| `llm_postprocess.py` | LLM-Nachkorrektur (Claude Haiku 4.5) | Nein |
| `evaluate_ocr.py` | CER/WER-Evaluation mit HTML-Report | Nein |
| `generate_dashboard_data.py` | Dashboard-Daten generieren | Nein |
| `extract_pages.py` | PDF zu Seitenbildern (PNG) | Nein |
| `extract_gnd.py` | GND-IDs aus Referenz-TEI extrahieren | Nein |

## Verwendung

```bash
# OCR-Tests durchführen (GPU erforderlich)
python scripts/test_all_pdfs.py --phase phase1

# Evaluation (ohne GPU)
python scripts/evaluate_ocr.py --all

# GND-Extraktion
python scripts/extract_gnd.py
```

## Postprocess-Modul

```
postprocess/
├── __init__.py
├── clean_markdown.py   # Markdown-Syntax entfernen
├── dehyphenate.py      # Silbentrennung auflösen
├── normalize.py        # Zeichen normalisieren
└── pipeline.py         # Kombinierte Pipeline
```

Verwendung:
```python
from scripts.postprocess import process_text
clean = process_text(raw_ocr_output)
```

---

*Aktualisiert: 25.02.2026*
