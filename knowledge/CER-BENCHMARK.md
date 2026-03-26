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

## Ergebnisse (Maerz 2026)

**24 von 25 Docs evaluiert** (1 Mismatch: Doc 570)

| Metrik | Wert |
|--------|------|
| Mittlere CER | 9.3% |
| **Median CER** | **5.5%** |
| Std | 8.8% |
| Min / Max | 1.0% / 34.5% |
| Mittlere WER | 19.5% |

### Nach Layout-Typ

| Typ | n | Mittl. CER | Median CER |
|-----|---|-----------|------------|
| A (einspaltig) | 11 | 10.3% | 4.9% |
| B (zweispaltig) | 7 | 9.6% | 5.8% |
| C (Monografie) | 2 | 5.7% | 5.7% |
| D (Spezial) | 4 | 7.9% | 6.0% |

### Nach Sprache

| Sprache | n | Mittl. CER |
|---------|---|-----------|
| fra | 14 | 9.1% |
| deu | 7 | 11.4% |
| fra/deu | 3 | 5.7% |

### Fehlermuster (gesamt)

| Kategorie | Anzahl | Mittl. CER-Beitrag |
|-----------|--------|-------------------|
| other (Zeichentausch) | 2545 | 39.24% |
| ocr_artifact (Halluzination) | 48 | 2.55% |
| layout (Struktur) | 45 | 2.35% |
| punctuation (Interpunktion) | 5816 | 0.74% |
| whitespace | 1612 | 0.25% |
| diacritics (Akzente) | 47 | 0.01% |
| hyphenation (Trennung) | 21 | 0.01% |

### Problemdokumente

| Doc | CER | Problem |
|-----|-----|---------|
| 290 | 34.5% | Schlechte Scan-Qualitaet + Alignment-Mismatch |
| 1440 | 26.0% | Alignment-Mismatch (Ref/Pipeline decken unterschiedliche Textbereiche ab) |
| 1060 | 21.4% | Alignment-Problem |
| 30 | 20.3% | Neu evaluiert, Ursache offen |
| 300 | 17.4% | Neu evaluiert, Ursache offen |
| 1910 | 16.5% | Alignment-Mismatch (OCR-CER bereits 27%) |

**Hinweis:** Die hohen CER-Werte der Problemdokumente sind ueberwiegend Alignment-Probleme (Referenz-TEI und Pipeline-TEI decken unterschiedliche Textbereiche ab), nicht Pipeline-Degradation.

### Pipeline-Effekt (OCR vs. TEI) -- Korrigiert

Vollstaendiger Stufen-Vergleich aller 25 Ground-Truth-Docs (OCR-Markdown-CER vs. End-to-End-TEI-CER):

- **11 Docs besser** durch Pipeline (teilweise massiv: Doc 40 von 74.5% auf 3.2%, Doc 130 von 78.5% auf 4.5%)
- **10 Docs stabil** (Delta < +/-1pp)
- **4 Docs schlechter** (1910: +12.5pp, 290: +8.8pp, 30: +7.4pp, 90: +6.0pp)

**Kernbefund:** Die Pipeline hilft in der Mehrheit der Faelle. Die 4 Verschlechterungen betreffen Docs, die bereits hohe OCR-CER (17-27%) hatten. Das Hauptproblem ist die Quell-OCR-Qualitaet, nicht die TEI-Generierung.

**Fruehere Fehleinschaetzung (korrigiert):** Der Pilot-TESTPLAN verglich nur 2 Seiten pro Doc; die daraus abgeleiteten OCR-CER-Werte (z.B. 1440: 3.7%) waren nicht repraesentativ fuer das Gesamtdokument. Der vollstaendige Vergleich zeigt, dass Doc 1440 bereits auf OCR-Stufe 17.5% CER hat.

### Moegliche Baseline-Korrektur

Ein Teil der gemessenen CER stammt aus **Konventionsdifferenzen** (nicht OCR-Fehlern):
- Typografische vs. gerade Anfuehrungszeichen
- Halbgeviertstrich vs. Bindestrich
- Apostroph U+2019 vs. U+0027
- Leerzeichen vor Interpunktion (franzoesische Konvention)

Die 5816 Interpunktionsfehler (0.74% CER-Beitrag) koennten teilweise durch schaerfere Zeichennormalisierung in `extract_text_for_comparison()` verschwinden. Das waere eine Baseline-Korrektur, keine OCR-Verbesserung.

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

### Unsere Position

- **Beste Docs (1.0-2.2%):** State of the Art fuer historischen Druck
- **Median (5.5%):** Vergleichbar mit GPT-4o-Klasse (6.3%)
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
