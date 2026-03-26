---
type: knowledge
created: 2026-03-26
updated: 2026-03-26
tags: [zbz-ocr-tei, evaluation, cer, benchmark, ocr-quality]
status: active
---

# CER Benchmark

End-to-End Character Error Rate: Pipeline-TEI vs. ZBZ-Referenz-TEI (Transkribus Ground Truth).

**Dependencies:** [TESTPLAN](TESTPLAN.md) (Metriken-Definitionen), [ENGINES](ENGINES.md) (OCR-Modelle), [PIPELINE](PIPELINE.md) (Pipeline-Stufen)

---

## Methodik

- **Referenz:** 25 ZBZ-Referenz-TEIs (`data/referenz-tei/`), manuell erstellt via Transkribus
- **Hypothese:** Pipeline-TEIs (`output/tei_final/`), generiert durch OCR -> Layout -> TEI -> NER -> Screening
- **Vergleich:** Textextraktion aus beiden TEI-XMLs, `<choice>`-korrigiert, Fussnoten exkludiert, Unicode-NFC-normalisiert
- **Alignment:** Automatisch bei Laengendifferenz >5%
- **Mismatch-Erkennung:** CER >50% = Textabweichung (Doc aus Evaluation ausgeschlossen)
- **Werkzeug:** `scripts/benchmark_cer.py`, Funktionen in `scripts/evaluate_ocr.py`

---

## Ergebnisse (Maerz 2026, nach Normalisierungskorrektur)

**24 von 25 Docs evaluiert** (1 Mismatch: Doc 570)

| Metrik | Vor Normfix | Nach Normfix | Delta |
|--------|-------------|-------------|-------|
| Mittlere CER | 9.3% | **8.1%** | -1.2pp |
| **Median CER** | 5.5% | **5.4%** | -0.2pp |
| Std | 8.8% | 8.9% | +0.1pp |
| Min / Max | 1.0% / 34.5% | **0.8% / 33.5%** | |
| Mittlere WER | 19.5% | **12.9%** | **-6.6pp** |

**Normalisierungskorrektur (2026-03-26):** `normalize_for_comparison()` wendet Guillemet-, Anführungszeichen-, Gedankenstrich- und frz. Interpunktionsnormalisierung **symmetrisch** auf beide Seiten an. Kein Doc verschlechtert. 12/24 Docs jetzt unter 3% CER (vorher 4/24).

### Nach Layout-Typ

| Typ | n | Mittl. CER | Median CER |
|-----|---|-----------|------------|
| A (einspaltig) | 11 | 9.0% | 2.9% |
| B (zweispaltig) | 7 | 8.9% | 5.6% |
| C (Monografie) | 2 | 4.1% | 4.1% |
| D (Spezial) | 4 | 6.3% | 4.4% |

### Nach Sprache

| Sprache | n | Mittl. CER |
|---------|---|-----------|
| fra | 14 | 7.4% |
| deu | 7 | 11.1% |
| fra/deu | 3 | 4.3% |

### Konfusionsmatrix: Top-10 Substitutionen (nach Normalisierung)

| # | Erwartet | Erkannt | Codepoints | Anzahl |
|---|----------|---------|-----------|--------|
| 1 | (Hyphen) | - | U+2010 -> U+002D | 38 |
| 2 | e | (Space) | U+0065 -> U+0020 | 30 |
| 3 | (Space) | e | U+0020 -> U+0065 | 24 |
| 4 | (En-dash) | - | U+2013 -> U+002D | 23 |
| 5 | e | s | U+0065 -> U+0073 | 17 |

Vollstaendige Matrix (50 Paare): `docs/data/diagnostik_ocr.json`

### Problemdokumente

| Doc | CER | OCR-Baseline | Pipeline-Delta | Ursache |
|-----|-----|-------------|---------------|---------|
| 290 | 33.5% | 15.8% | +17.7pp | Alignment-Mismatch (Pipeline-TEI deutlich laenger) |
| 1440 | 25.7% | n/a | n/a | Alignment-Problem |
| 1060 | 21.4% | n/a | n/a | Alignment-Problem |
| 30 | 18.8% | 18.0% | +0.8pp | Marginal, OCR-Qualitaet bereits schlecht |
| 1910 | 16.1% | 26.4% | **-10.3pp** | Pipeline verbessert! |
| 300 | 15.4% | n/a | n/a | Ursache offen |

### Pipeline-Effekt (OCR vs. TEI) -- Aktualisiert nach Normfix

- **18 Docs verbessert** durch Pipeline
- **6 Docs verschlechtert** (290 massiv, Rest marginal)

**Kernbefund nach Normfix:** Pipeline hilft bei 75% der Docs. Doc 1910 und 90 (vorher als "verschlechtert" gemeldet) sind nach korrekter Normalisierung tatsaechlich Pipeline-Erfolge. Nur Doc 290 ist echter Ausreisser (Alignment).

---

## Einordnung: Forschungsliteratur (2025/2026)

### Benchmark-Referenzwerte (gedruckte historische Dokumente)

| Quelle | Methode | Sprache | CER |
|--------|---------|---------|-----|
| Crosilla et al. 2025 | Transkribus Print M1 + Gemini 2.0 Flash Post-Korrektur | deu (Fraktur) | **0.84%** |
| Crosilla et al. 2025 | Gemini 2.0 Flash direkt (zero-shot) | deu | 1.27% |
| Crosilla et al. 2025 | Transkribus Print M1 allein | deu | 3.67% |
| Crosilla et al. 2025 | GPT-4o direkt | deu | 6.31% |
| arxiv 2510.06743 | Gemini 2.5 Pro | rus (18. Jh.) | 3.36% |
| arxiv 2510.06743 | Gemini 2.5 Flash | rus | 4.94% |
| arxiv 2510.06743 | Claude 3.5 | rus | 6.79% |
| arxiv 2510.06743 | GPT-4o | rus | 9.23% |
| arxiv 2510.06743 | Traditionelles OCR | rus | 21-45% |
| Transkribus Doku | Richtwert gedruckter Text | allg. | 0.5-2% |

### Unsere Position (aktualisiert nach Normfix)

- **Beste Docs (0.8-1.5%):** State of the Art fuer historischen Druck
- **Median (5.4%):** Vergleichbar mit GPT-4o-Klasse (6.3%)
- **12/24 Docs unter 3%:** Grossteil des Korpus in guter Qualitaet
- **Verbesserungspotenzial:** Gemini 2.5 Pro erreicht 3.4% zero-shot; multimodale Post-Korrektur bis 0.84%

### Kernerkenntnisse aus der Literatur

1. **Multimodale Post-Korrektur** (Bild + OCR-Text an LLM) uebertrifft reine Text-Post-Korrektur deutlich (Crosilla et al.: 3.67% -> 0.84%)
2. **"No Free Lunches"** (Kanerva & Ledins 2025): LLM-Post-Korrektur funktioniert sprachabhaengig; bei Englisch gut, bei Finnisch nicht. Sprache muss separat evaluiert werden.
3. **Gemini-Modelle dominieren** aktuelle Benchmarks fuer historische Dokumente (2.5 Pro, 2.0 Flash)
4. **Post-Korrektur kann schaden** (arxiv 2510.06743): Bei bereits gutem OCR degradiert LLM-Korrektur die Ergebnisse -- bestaetigt unsere Erfahrung mit Haiku-Postkorrektur (+0.10%)
5. **Sprachhinweise verbessern OCR**: Explizite Sprachkonfiguration hilft bei multilingualen Korpora

---

## Sprachkonfiguration im Pipeline-Status

| Pipeline-Stufe | Sprache genutzt? | Details |
|---|---|---|
| Mistral OCR | Nein | Auto-Detect, kein Hint |
| Gemini OCR-Korrektur | Ja | `_lang_hint()` fuer Akzente/Umlaute |
| TEI-Generierung | Ja | `main_lang` fuer `<foreign>` Tagging |
| NER / Wikidata | Ja | Sprachpriorisierung |

---

## Proxy-Metriken (Docs ohne Ground Truth)

Fuer die ~260 Docs ohne Referenz-TEI: Proxy-Score aus Screening-Daten (`compute_proxy_quality()`):

| Bucket | Anzahl | Beschreibung |
|--------|--------|-------------|
| excellent | 90 | Proxy-Score >= 0.9 |
| good | 26 | 0.7-0.9 |
| fair | 154 | 0.4-0.7 (v1-Reviews, konservativ) |
| poor | 15 | < 0.4 |

---

## Wissenschaftliche Quellen

1. Crosilla, L. et al. (2025). "Multimodal LLMs for OCR, OCR Post-Correction, and Named Entity Recognition in Historical Documents." arXiv:2504.00414. https://arxiv.org/abs/2504.00414
2. Nosova, E. et al. (2025). "Evaluating LLMs for Historical Document OCR: A Methodological Framework for Digital Humanities." arXiv:2510.06743. https://arxiv.org/html/2510.06743
3. Kanerva, J. & Ledins, G. (2025). "OCR Error Post-Correction with LLMs in Historical Documents: No Free Lunches." In: RESOURCEFUL-2025, Tallinn. arXiv:2502.01205. https://arxiv.org/abs/2502.01205
4. Springer (2025). "Enhancing OCR in historical documents with complex layouts through machine learning." Int. J. Digit. Libr. https://link.springer.com/article/10.1007/s00799-025-00413-z
5. ACL Anthology (2025). "Post-OCR Correction of Historical German Periodicals." RESOURCEFUL-2025. https://aclanthology.org/2025.resourceful-1.26.pdf
6. Springer (2025). "Scrambled text: fine-tuning language models for OCR error correction using synthetic data." IJDAR. https://link.springer.com/article/10.1007/s10032-025-00522-0

---

*Erstellt: 2026-03-26*
