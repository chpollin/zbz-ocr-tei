---
type: knowledge
created: 2026-01-29
updated: 2026-02-18
tags: [zbz-ocr-tei, testplan, evaluation, metriken]
status: active
---

# Testplan

Systematische OCR-Evaluation aller Dokumenttypen. Single Source für Testphasen, Metriken und Ergebnisse.

**Abhängigkeiten:** [QUELLENANALYSE](QUELLENANALYSE.md) (Pilotdateien, Dokumenttypen), [OCR-ENGINES](OCR-ENGINES.md) (Engine-Auswahl)

---

## Ziel

1. Layout-spezifische Probleme identifizieren
2. Dokumenttyp-abhängige Verarbeitungsstrategien entwickeln
3. Qualitätsmetriken pro Dokumenttyp etablieren

---

## Testphasen

Pilotdateien und Dokumenttypen: Siehe [QUELLENANALYSE](QUELLENANALYSE.md) §Pilotdateien.

### Phase 1: Baseline (Typ A - einspaltig)

**Ziel:** OCR-Grundqualität validieren

| Schritt | PDF | Seiten | Test |
|---------|-----|--------|------|
| 1.1 | 2310 | 2-3 | Französischer Text, Akzente |
| 1.2 | 1180 | 2 | Deutscher Text, Fließtext |
| 1.3 | 290 | 1 | Französischer Essay |

**Status:** Abgeschlossen (DeepSeek + Mistral)

### Phase 2: Layout-Herausforderungen (Typ B - zweispaltig)

**Ziel:** Spalten-Lesereihenfolge testen

| Schritt | PDF | Seiten | Test |
|---------|-----|--------|------|
| 2.1 | 2530 | 1-2 | Spalten korrekt? |
| 2.2 | 890 | 2 | Zweispaltig + kleine Schrift |
| 2.3 | 3040 | 1 | Lexikon: Spalten + Fußnoten |
| 2.4 | 2530 | 1-2 | Gemini 3 Agentic Vision Test |

**Bekanntes Problem:** 2530 hat falsche Spaltenreihenfolge bei DeepSeek.

**Drei Lösungsansätze:** Siehe [DECISIONS](DECISIONS.md) O10.

**Status:** Mistral OCR abgeschlossen, Gemini ausstehend

### Phase 3: Spezialformate (Typ D)

**Ziel:** Randfälle identifizieren

| Schritt | PDF | Seiten | Test |
|---------|-----|--------|------|
| 3.1 | 90 | 2 | Historischer Druck (1944) |
| 3.2 | 1440 | 1-2 | Interview-Dialog erkennen |
| 3.3 | 830 | 1 | Bildband: Text neben Bild |
| 3.4 | 1330 | 1-2 | Sammelband-Struktur |

**Status:** Mistral OCR abgeschlossen

### Phase 4: Monografien (Typ C)

**Ziel:** Skalierbarkeit testen

| Schritt | PDF | Seiten | Test |
|---------|-----|--------|------|
| 4.1 | 40 | 5-6 | Roman-Fließtext |
| 4.2 | 1520 | 3-4 | Monografie-Inhalt |

**Status:** Mistral OCR abgeschlossen, CER-Evaluation eingeschraenkt (Alignment-Problem bei langen Texten)

---

## Ergebnisse

### Evaluationsmatrix: Mistral Document AI 2512 (18.02.2026)

| PDF | Typ | CER | WER | Genauigkeit | Status | Anmerkung |
|-----|-----|-----|-----|-------------|--------|-----------|
| 2310 | A | 7.00% | 22.04% | 93.00% | Akzeptabel | JSTOR-Cover verzerrt Alignment |
| 1180 | A | 3.12% | 10.45% | 96.88% | OK | Jahresbericht, sehr gut |
| 290 | A | 18.07% | 28.17% | 81.93% | Problematisch | Scan-Qualitaet? |
| 2530 | B | 3.96% | 17.06% | 96.04% | OK | Zweispaltig, gut erkannt |
| 890 | B | 5.96% | 12.80% | 94.04% | Akzeptabel | Lehrerzeitung |
| 3040 | B | 9.02% | 22.73% | 90.98% | Akzeptabel | Lexikon mit Fussnoten |
| 90 | D | 1.21% | 8.92% | 98.79% | OK | Historisch 1944, exzellent |
| 1440 | D | 3.71% | 12.69% | 96.29% | OK | Interview/Dialog |
| 830 | D | 4.00% | 17.46% | 96.00% | OK | Bildband |
| 1330 | D | 2.60% | 11.42% | 97.40% | OK | Sammelband |
| 40 | C | - | - | - | n/a | Alignment bei 156 Seiten unzuverlaessig |
| 1520 | C | - | - | - | n/a | Alignment bei 142 Seiten unzuverlaessig |

**Durchschnitt Phase 1-3 (10 Docs): CER 5.87%, Genauigkeit 94.14%**

| Phase | Avg CER | Avg WER | Avg Genauigkeit |
|-------|---------|---------|-----------------|
| Phase 1 (Typ A) | 9.40% | 20.22% | 90.60% |
| Phase 2 (Typ B) | 6.31% | 17.53% | 93.69% |
| Phase 3 (Typ D) | 2.88% | 12.62% | 97.12% |
| Phase 4 (Typ C) | n/a | n/a | n/a |

### Evaluationsmatrix: LLM-Nachkorrektur Haiku 4.5 (19.02.2026)

Variante C (Few-Shot), Phase 1-3:

| Phase | Mistral CER | LLM CER | Delta |
|-------|-------------|---------|-------|
| Phase 1 (A) | 9.40% | 8.43% | -0.97 |
| Phase 2 (B) | 6.31% | 6.34% | +0.03 |
| Phase 3 (D) | 2.88% | 2.72% | -0.16 |
| **Gesamt** | **5.87%** | **5.55%** | **-0.32 (5.5% relativ)** |

Drei Varianten getestet: A (5.47%), B (5.59%), C (5.55%). Variante C als Default (bester CER/Kosten-Tradeoff).

### Evaluationsmatrix: DeepSeek-OCR-2 (lokal, nur Phase 1)

| PDF | Typ | CER | WER | Genauigkeit | Status | Anmerkung |
|-----|-----|-----|-----|-------------|--------|-----------|
| 2310 | A | 2.67% | 16.61% | 97.33% | OK | Nur 2 Seiten getestet |
| 1180 | A | 4.89% | 13.29% | 95.11% | OK | Nur 2 Seiten getestet |
| 290 | A | 9.21% | 19.53% | 90.79% | OK | Nur 2 Seiten getestet |

Hinweis: DeepSeek-Ergebnisse basieren auf 2 Testseiten pro Doc, Mistral auf allen Seiten.

### Bewertungsskala

- **OK:** CER < 5% (Zeichengenauigkeit > 95%)
- **Akzeptabel:** CER 5-15% (manuell korrigierbar)
- **Problematisch:** CER > 15% oder strukturelle Fehler (LAYOUT)

### Metriken

- **CER** (Character Error Rate): Anteil falscher Zeichen
- **WER** (Word Error Rate): Anteil falscher Wörter
- **Genauigkeit**: 100% - CER

---

## CLI-Befehle

```bash
# OCR mit Mistral (ohne GPU, braucht .env)
python -m scripts.ocr_pipeline -i data/scans/2310.pdf -e mistral -o output/mistral_results

# Evaluation: Mistral, alle Phasen
python -m scripts.evaluate_ocr --phase all --ocr-dir output/mistral_results --engine mistral

# Evaluation: Einzelne Phase
python -m scripts.evaluate_ocr --phase phase1 --ocr-dir output/mistral_results --engine mistral

# Evaluation: DeepSeek Vergleich
python -m scripts.evaluate_ocr --all --ocr-dir output/ocr_results --engine deepseek

# OCR-Tests nach Phase mit DeepSeek (GPU erforderlich)
python scripts/test_all_pdfs.py --phase phase1
```

---

## Naechste Schritte

1. [x] Testskript `test_all_pdfs.py` erstellen
2. [x] Phase 1 durchfuehren (DeepSeek Baseline)
3. [x] Evaluationsskript `evaluate_ocr.py` erstellen
4. [x] Mistral Document AI auf Phase 1 testen (`test_mistral_ocr.py`)
5. [x] Benchmark-UI erstellen (`docs/benchmark.html`)
6. [x] CER/WER fuer Mistral gegen Referenz-TEI berechnen
7. [x] Phase 2-4 mit Mistral durchfuehren
8. [x] Evaluationsmatrix vervollstaendigen (Phase 1-3)
9. [ ] Doc 290 untersuchen: Warum CER 18%? Scan-Qualitaet pruefen
10. [ ] Phase 4 Evaluation: Seitenweisen Vergleich implementieren
11. [ ] Gemini 3 Flash auf Typ B (2530) testen
12. [ ] Empfehlung fuer Produktions-Pipeline ableiten

---

## Referenzen

- [QUELLENANALYSE](QUELLENANALYSE.md) für Pilotdateien und Dokumenttypen
- [OCR-ENGINES](OCR-ENGINES.md) für Engine-spezifische Informationen
- [DECISIONS](DECISIONS.md) O10 für Spalten-Lösungsansätze

---

*Erstellt: 2026-01-29 | Aktualisiert: 2026-02-19 (LLM-Korrektur Haiku 4.5 hinzugefuegt)*
