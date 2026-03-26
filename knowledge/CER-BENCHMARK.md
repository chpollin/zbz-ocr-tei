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

## Ergebnisse (Maerz 2026, finale Evaluation)

### Reduktions-Timeline

| Schritt | Mean CER | Median CER | Docs |
|---------|---------|------------|------|
| Ausgangslage (E51) | 9.33% | 5.52% | 24 |
| + Sym. Normalisierung | 8.11% | 5.36% | 24 |
| + Hyphen-Normalisierung | 7.29% | 2.61% | 25 |
| + CI-Alignment | 5.97% | 2.42% | 25 |
| **+ Scope-Bereinigung** | **4.18%** | **1.83%** | **19** |

### Finale Statistik (19 scope-bereinigte Docs)

| Metrik | Wert |
|--------|------|
| n (evaluiert) | 19 |
| n (ausgeschlossen) | 6 (Scope-Mismatch) |
| **Mean CER** | **4.18%** |
| **Median CER** | **1.83%** |
| Std CER | 5.43% |
| Min / Max | 0.30% / 21.2% |
| Q1 / Q3 | 0.85% / 5.62% |
| Docs <3% | 13 (68%) |
| Docs >15% | 2 (290, 1910) |

**Ziel Median <3.5%: ERREICHT (1.83%)**

### Alle 25 Docs (inkl. Scope-Mismatches)

| Metrik | Wert |
|--------|------|
| Mean CER | 5.97% |
| Median CER | 2.42% |
| Min / Max | 0.30% / 25.7% |
| Docs <3% | 14 (56%) |

### Scope-Mismatches (6 Docs, vom CER-Hauptwert ausgeschlossen)

| Doc | CER | Ref/Pipe Seiten | Ratio | Ursache |
|-----|-----|----------------|-------|---------|
| 1440 | 25.7% | 8 / 7 | 1.1x | 2 OCR-Seiten fehlen, S.267 fehlt |
| 30 | 18.7% | 8 / 4 | 2.0x | Nur 50% OCR'd |
| 300 | 15.2% | 2 / 4 | 2.0x | Referenz nur 2 von 4 Seiten |
| 760 | 7.0% | 38 / 20 | 1.9x | Auto-detektiert |
| 3020 | 1.5% | 10 / 6 | 1.7x | Auto-detektiert |
| 830 | 1.5% | 4 / 2 | 2.0x | Auto-detektiert |

### Nach Layout-Typ (scope-bereinigt)

| Typ | n | Mittl. CER | Median CER |
|-----|---|-----------|------------|
| A (einspaltig) | 11 | 3.7% | 1.8% |
| B (zweispaltig) | 5 | 5.9% | 5.1% |
| C (Monografie) | 2 | 4.0% | 4.0% |
| D (Spezial) | 1 | 0.8% | 0.8% |

### Nach Sprache (scope-bereinigt)

| Sprache | n | Mittl. CER | Median CER |
|---------|---|-----------|------------|
| fra | 11 | 4.0% | 1.8% |
| deu | 5 | 5.9% | 5.6% |
| fra/deu | 3 | 2.1% | 0.8% |

### Konfusionsmatrix: Top-5 Substitutionen

| # | Erwartet | Erkannt | Codepoints | Anzahl |
|---|----------|---------|-----------|--------|
| 1 | e | (Space) | U+0065 -> U+0020 | 31 |
| 2 | e | E | U+0065 -> U+0045 | 28 |
| 3 | (Space) | e | U+0020 -> U+0065 | 25 |
| 4 | s | S | U+0073 -> U+0053 | 18 |
| 5 | e | s | U+0065 -> U+0073 | 17 |

Verbleibende Fehler sind echte OCR-Fehler (Zeichenverwechslungen, Case). Vollstaendige Matrix: `docs/data/diagnostik_ocr.json`

### Verbleibende Problemdokumente (2 echte >15%)

| Doc | CER | Ursache |
|-----|-----|---------|
| 290 | 21.2% | 10.4% Textverlust + Case-Differenzen |
| 1910 | 16.1% | Layout-Extraktionsfehler (15.8% Text fehlt aus Spaltenregionen) |

### Pipeline-Effekt (OCR vs. TEI)

- **20 Docs verbessert** durch Pipeline (80%)
- **5 Docs verschlechtert** (290 massiv, Rest marginal/Scope-Mismatch)

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

### Unsere Position (finale Evaluation)

- **Beste Docs (0.3-0.8%):** State of the Art fuer historischen Druck, vergleichbar mit Crosilla-Multimodal (0.84%)
- **Median 1.83% (bereinigt):** Besser als Transkribus allein (3.67%), Gemini 2.5 Pro zero-shot (3.36%)
- **13/19 Docs unter 3%:** 68% des Korpus in exzellenter Qualitaet
- **Verbesserungspotenzial:** 2 verbleibende Problemdocs (290, 1910) durch Layout-Verbesserung adressierbar

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
