# Pipeline: OCR → Post-Processing → TEI

## Architektur

```
PDF → OCR (Markdown) → Post-Processing → TEI-XML → Validierung → [GND]
      └─ output/ocr_results/  └─ output/clean/    └─ output/tei/
```

## Stufe 1: OCR

### DeepSeek-OCR-2 (primär)

| Aspekt | Details |
|--------|---------|
| Modell | `deepseek-ai/DeepSeek-OCR-2` |
| Prompt | `<image>\n<|grounding|>Convert the document to markdown.` |
| Hardware | GPU mit 16GB VRAM (RTX 4080) |
| Setup | Siehe `scripts/test_deepseek_ocr.py` |

### Docling (Alternative)

| Aspekt | Details |
|--------|---------|
| Repo | `DS4SD/docling` (IBM, 37k Stars) |
| Vorteil | Modulare Pipeline, Layout-Analyse |
| Nachteil | Noch nicht getestet |

### OCR-Qualität (gemessen)

| Dokument | Typ | CER | Genauigkeit |
|----------|-----|-----|-------------|
| 2310 | Einspaltig | 2.67% | 97.33% |
| 1180 | Einspaltig | 4.89% | 95.11% |
| 290 | Einspaltig | 9.21% | 90.79% |
| 2530 | Zweispaltig | - | LAYOUT-PROBLEM |

**Bekannte Fehler:**
- Anführungszeichen: `„"` statt `""`
- Einzelne Ziffern: `822` → `82`
- Lateinische Wendungen: `nunc` → `num`
- Gelegentlich Akzente: `é` → `e`

---

## Stufe 2: Post-Processing

**Implementiert in:** `scripts/postprocess/`

### Transformationen (Reihenfolge wichtig!)

| Schritt | Funktion | Beispiel |
|---------|----------|----------|
| 1. Markdown entfernen | `clean_markdown()` | `## Titel` → `Titel` |
| 2. Zeichen normalisieren | `normalize_text()` | `„"` → `""` |
| 3. Silbentrennung | `dehyphenate()` | `Wis- senschaft` → `Wissenschaft` |
| 4. Whitespace | (inline) | Mehrfache Leerzeilen → eine |

### Normalisierungsregeln

```python
NORMALIZE_MAP = {
    '„': '"', '"': '"', '»': '"', '«': '"',  # Anführungszeichen
    ''': "'", ''': "'",                       # Apostrophe
    '–': '-', '—': '-',                       # Gedankenstriche
    '\u00A0': ' ',                            # Non-breaking space
}
```

---

## Stufe 3: TEI-Transformation

**Status:** Noch nicht implementiert.

### Aufgaben

1. **Strukturerkennung:** Dokumenttyp (Essay, Rezension, Interview, Lexikon)
2. **Element-Mapping:** Markdown → TEI (siehe [TEI-Mapping.md](TEI-Mapping.md))
3. **Metadaten:** Seitenzahlen `<pb>`, Header

### Modellauswahl (für LLM-Ansatz)

| Modell | Input | Output | Kosten/Dok |
|--------|-------|--------|------------|
| Claude Haiku 4.5 | 0,80 USD/1M | 4,00 USD/1M | ~0,03 USD |
| Gemini 3 Flash | 0,50 USD/1M | 3,00 USD/1M | ~0,02 USD |

**Geschätzte Gesamtkosten (289 Dokumente):** 6-9 USD

---

## Validierung

| Prüfung | Tool |
|---------|------|
| XML-Wohlgeformtheit | lxml |
| TEI P5 Schema | RelaxNG |
| Seitenzählung | Custom |
| GND-Format | Regex `ref="GND:\d+"` |

---

## CLI-Befehle

```bash
# OCR (GPU erforderlich)
python scripts/test_all_pdfs.py --phase phase1

# Post-Processing
python -c "from scripts.postprocess import process_directory; ..."

# Evaluation
python scripts/evaluate_ocr.py --all
```

---

## Risiken

| Risiko | Schwere | Mitigation |
|--------|---------|------------|
| Spalten-Reihenfolge (Typ B) | Hoch | Docling testen, Prompt-Tuning |
| GND-Verknüpfung | Hoch | Nachgelagert, externe API |
| Mehrseitige Fußnoten | Mittel | Speziallogik |
| Historische Drucke | Mittel | Beide OCR-Engines testen |

---

## Offene Punkte

- [ ] Docling als Alternative evaluieren
- [ ] Spalten-Problem lösen
- [ ] TEI-Transformation implementieren
- [ ] GND-Lookup integrieren

---

*Aktualisiert: 29.01.2026*
