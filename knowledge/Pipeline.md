# Pipeline: OCR → Post-Processing → TEI

## Architektur

```
PDF → Docling+DeepSeek (Markdown) → Post-Processing → TEI-XML → Validierung → [GND]
      └─ output/ocr_results/       └─ output/clean/   └─ output/tei/
```

## Stufe 1: OCR

### Docling + DeepSeek-OCR-2 (kombiniert)

```
PDF → Docling (Layout-Analyse) → DeepSeek-OCR-2 (Text) → Strukturiertes Markdown
```

| Aspekt | Details |
|--------|---------|
| Layout | Docling (Spalten, Tabellen, Regionen) |
| OCR | DeepSeek-OCR-2 (3B VLM) |
| Output | Strukturiertes Markdown |
| Hardware | GPU mit 8+ GB VRAM |
| Skript | `scripts/ocr_pipeline.py` |

### Engine-Auswahl nach Dokumenttyp

| Typ | Beschreibung | Engine |
|-----|--------------|--------|
| A | Einspaltig | DeepSeek direkt |
| B | Zweispaltig | **Docling + DeepSeek** |
| C | Monografie | Docling + DeepSeek + Chunking |
| D | Spezial | Fallweise |

### OCR-Qualität (gemessen)

| Dokument | Typ | CER | Genauigkeit |
|----------|-----|-----|-------------|
| 2310 | Einspaltig | 2.67% | 97.33% |
| 1180 | Einspaltig | 4.89% | 95.11% |
| 290 | Einspaltig | 9.21% | 90.79% |
| 2530 | Zweispaltig | - | Docling testen |

**Bekannte OCR-Fehler:**
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

**Skript:** `scripts/transform_to_tei.py`
**Ansatz:** Regelbasiert (deterministisch), LLM nur für komplexe Strukturen

### Regelbasierte Transformation

| Input (Markdown) | Output (TEI) |
|------------------|--------------|
| Leere Zeile | `</p><p>` (Absatztrennung) |
| `# Überschrift` | `<head>` |
| Erster Absatz (Rezension) | `<head><bibl>` |
| Bekannte Namen | `<persName ref="GND:...">` |
| `*kursiv*` | `<hi rendition="#i">` |

### LLM nur für

- Komplexe Strukturerkennung (Interview-Dialog)
- NER (Named Entity Recognition)
- GND-Disambiguierung

---

## Stufe 4: Validierung

| Prüfung | Tool |
|---------|------|
| XML-Wohlgeformtheit | lxml |
| TEI P5 Schema | RelaxNG |
| Seitenzählung | Custom |
| GND-Format | Regex `ref="GND:\d+"` |

---

## CLI-Befehle

```bash
# OCR Pipeline (GPU erforderlich)
python scripts/ocr_pipeline.py --input data/scans/2310.pdf
python scripts/ocr_pipeline.py --all --engine auto

# TEI Transformation
python scripts/transform_to_tei.py --doc 2310 --type review --add-gnd

# Evaluation
python scripts/evaluate_ocr.py --all
```

---

## Risiken

| Risiko | Schwere | Mitigation |
|--------|---------|------------|
| Spalten-Reihenfolge (Typ B) | Hoch | Docling für Layout |
| Windows Symlink (Docling) | Mittel | Cloud-VM oder Developer Mode |
| GND-Verknüpfung | Hoch | Nachgelagert, lobid.org API |
| Historische Drucke | Mittel | Beide Engines testen |

---

## Offene Punkte

→ Siehe [journal.md](journal.md#offene-punkte)

---

*Aktualisiert: 29.01.2026*
