---
type: knowledge
created: 2026-01-29
updated: 2026-02-25
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

**Status:** Abgeschlossen (Mistral OCR + seitenweiser Vergleich)

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
| 40 | C | 2.57% | 10.76% | 97.43% | OK | Seitenweiser Vergleich (147 TEI-Seiten) |
| 1520 | C | 2.73% | 15.20% | 97.27% | OK | Seitenweiser Vergleich (116 TEI-Seiten, Offset +8) |
| 1060 | A | 22.60% | 27.88% | 77.40% | Problematisch | Alignment-Problem bei 6-seitigem PDF |
| 130 | A | 4.13% | 16.11% | 95.87% | OK | Seitenweise (16 TEI-Seiten), Deckblatt korrekt ignoriert |
| 1410 | A | 5.58% | 13.83% | 94.42% | Akzeptabel | Zweisprachig DE/FR |

**Durchschnitt Phase 1-3 (10 Docs): CER 5.87%, Genauigkeit 94.14%**
**Durchschnitt Phase 4 (2 Docs): CER 2.65%, Genauigkeit 97.35%**
**Durchschnitt alle 15 Docs: CER 6.42%, Genauigkeit 93.58%**

**Dashboard:** Ergebnisse visuell aufbereitet in `docs/index.html` (Metrikkarten, CER-Vergleichsbalken, Dokumentkatalog mit Engine-Filter).

| Phase | Avg CER | Avg WER | Avg Genauigkeit |
|-------|---------|---------|-----------------|
| Phase 1 (Typ A) | 9.40% | 20.22% | 90.60% |
| Phase 2 (Typ B) | 6.31% | 17.53% | 93.69% |
| Phase 3 (Typ D) | 2.88% | 12.62% | 97.12% |
| Phase 4 (Typ C) | 2.65% | 12.98% | 97.35% |

### Evaluationsmatrix: LLM-Nachkorrektur Haiku 4.5 (19.02.2026)

Variante C (Few-Shot), alle 15 Docs:

| Phase | Mistral CER | LLM CER | Delta |
|-------|-------------|---------|-------|
| Phase 1 (A) | 9.40% | 8.43% | -0.97 |
| Phase 2 (B) | 6.31% | 6.34% | +0.03 |
| Phase 3 (D) | 2.88% | 2.72% | -0.16 |
| Phase 4 (C) | 2.65% | 2.70% | +0.05 |
| **Gesamt (15 Docs)** | **6.42%** | **6.52%** | **+0.10** |

Drei Varianten getestet (Phase 1-3): A (5.47%), B (5.59%), C (5.55%). Variante C als Default (bester CER/Kosten-Tradeoff).

Hinweis: LLM-Korrektur verbessert Docs mit hohem CER, verschlechtert leicht bei gutem OCR (Phase 2, 4).

### Evaluationsmatrix: DeepSeek-OCR-2 (lokal, nur Phase 1)

| PDF | Typ | CER | WER | Genauigkeit | Status | Anmerkung |
|-----|-----|-----|-----|-------------|--------|-----------|
| 2310 | A | 2.67% | 16.61% | 97.33% | OK | Nur 2 Seiten getestet |
| 1180 | A | 4.89% | 13.29% | 95.11% | OK | Nur 2 Seiten getestet |
| 290 | A | 9.21% | 19.53% | 90.79% | OK | Nur 2 Seiten getestet |

Hinweis: DeepSeek-Ergebnisse basieren auf 2 Testseiten pro Doc, Mistral auf allen Seiten.

### Layout-Analyse: Docling 2.75 (25.02.2026)

8/15 Docs analysiert (7 Docs brauchen GPU: 2530, 290, 3040, 40, 830, 890, 90).

| Doc | Typ | Seiten | Regionen | Heading-Erkennung | Absatz-Segmentierung | Probleme |
|-----|-----|--------|----------|-------------------|----------------------|----------|
| 1180 | A | 8 | 55 | Sehr gut (Titel, Thesen) | Gut, aber Ueberlappungen auf p2 | Einzeiler-Fragmente, Seitenzahlen als text |
| 2310 | A | 3 | 27 | Gut | Gut | Keine |
| 130 | A | 18 | 67 | Gut | Gut | Keine |
| 1410 | A | 6 | 65 | Sehr gut (Zweispaltig) | Gut, Spalten korrekt getrennt | Keine |
| 1060 | A | 8 | 36 | OK | OK | Wenige Regionen |
| 1330 | D | 6 | 56 | Gut | Gut | Keine |
| 1440 | D | 5 | 59 | Gut | Gut | Keine |
| 1520 | C | 132/142 | ~900 | OK | OK | Analyse abgebrochen (10 Seiten fehlen) |

**Bekannte Probleme:**
1. **Ueberlappende Regionen:** Einzeiler (h_pct <3%) ueberlappen mit groesseren Bloecken (z.B. 1180 p2)
2. **Seitenzahlen:** Docling erkennt Seitenzahlen (217-220) als `text` statt `page_footer` — Heuristik noetig
3. **Fehlende Fussnoten:** Kein `footnote`-Label in den Stichproben gesehen (evtl. bei Docs mit Fussnoten anders)

**Post-Processing (O21):** 3 Heuristiken geplant: Overlap-Filter, Einzeiler-Merge, Seitenzahl-Erkennung.

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
10. [x] Phase 4 Evaluation: Seitenweisen Vergleich implementieren
11. [x] OCR + LLM + Eval fuer alle 15 Pilot-Dokumente abgeschlossen
12. [ ] Gemini 3 Flash auf Typ B (2530) testen
13. [ ] Doc 1060 untersuchen: CER 22.6% trotz Typ A — Alignment-Problem
14. [ ] Empfehlung fuer Produktions-Pipeline ableiten
15. [x] Layout-Analyse: 8/15 Docs mit Docling analysiert + Overlay-PNGs erzeugt
16. [ ] Layout-Post-Processing implementieren (O21: Overlap, Einzeiler, Seitenzahlen)
17. [ ] Layout-Analyse fuer restliche 7 Docs (braucht GPU)
18. [ ] Fussnoten-Erkennung pruefen (Doc 3040 = Lexikon mit Fussnoten)

---

## Referenzen

- [QUELLENANALYSE](QUELLENANALYSE.md) für Pilotdateien und Dokumenttypen
- [OCR-ENGINES](OCR-ENGINES.md) für Engine-spezifische Informationen
- [DECISIONS](DECISIONS.md) O10 für Spalten-Lösungsansätze

---

*Erstellt: 2026-01-29 | Aktualisiert: 2026-02-25 (Layout-Analyse 8/15 Docs + QA-Ergebnisse)*
