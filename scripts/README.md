# Scripts

Python-Skripte für die OCR-Pipeline.

## Übersicht

| Skript | Zweck | GPU |
|--------|-------|-----|
| `test_all_pdfs.py` | Haupt-OCR-Tests nach Phasen | Ja |
| `test_deepseek_ocr.py` | DeepSeek-OCR Einzeltest | Ja |
| `test_docling.py` | Docling-OCR Test (Spalten) | Nein |
| `test_column_prompt.py` | Prompt-Varianten für Spalten | Ja |
| `evaluate_ocr.py` | CER/WER-Evaluation mit HTML-Report | Nein |
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

*Aktualisiert: 29.01.2026*
