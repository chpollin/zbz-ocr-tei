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

**Status:** Abgeschlossen

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

**Status:** Ausstehend

### Phase 3: Spezialformate (Typ D)

**Ziel:** Randfälle identifizieren

| Schritt | PDF | Seiten | Test |
|---------|-----|--------|------|
| 3.1 | 90 | 2 | Historischer Druck (1944) |
| 3.2 | 1440 | 1-2 | Interview-Dialog erkennen |
| 3.3 | 830 | 1 | Bildband: Text neben Bild |
| 3.4 | 1330 | 1-2 | Sammelband-Struktur |

**Status:** Ausstehend

### Phase 4: Monografien (Typ C)

**Ziel:** Skalierbarkeit testen

| Schritt | PDF | Seiten | Test |
|---------|-----|--------|------|
| 4.1 | 40 | 5-6 | Roman-Fließtext |
| 4.2 | 1520 | 3-4 | Monografie-Inhalt |

**Status:** Ausstehend

---

## Ergebnisse

### Evaluationsmatrix

| PDF | Typ | CER | WER | Genauigkeit | Status | Anmerkung |
|-----|-----|-----|-----|-------------|--------|-----------|
| 2310 | A | 2.67% | 16.61% | 97.33% | OK | Rezension, sehr gut |
| 1180 | A | 4.89% | 13.29% | 95.11% | OK | Jahresbericht, gut |
| 290 | A | 9.21% | 19.53% | 90.79% | OK | Comptes Rendus |
| 130 | A | ? | ? | ? | - | Ausstehend |
| 1410 | A | ? | ? | ? | - | Ausstehend |
| 1060 | A | ? | ? | ? | - | Ausstehend |
| 2530 | B | ~0% | ~0% | ~99% | LAYOUT | Spaltenreihenfolge falsch |
| 890 | B | ? | ? | ? | - | Ausstehend |
| 3040 | B | ? | ? | ? | - | Ausstehend |
| 40 | C | ? | ? | ? | - | Ausstehend |
| 1520 | C | ? | ? | ? | - | Ausstehend |
| 90 | D | ? | ? | ? | - | Ausstehend |
| 830 | D | ? | ? | ? | - | Ausstehend |
| 1440 | D | ? | ? | ? | - | Ausstehend |
| 1330 | D | ? | ? | ? | - | Ausstehend |

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
# OCR-Tests nach Phase (GPU erforderlich)
python scripts/test_all_pdfs.py --phase phase1

# Evaluation (ohne GPU)
python scripts/evaluate_ocr.py --all

# Prompt-Varianten testen (Phase 2)
python scripts/test_column_prompt.py
```

---

## Nächste Schritte

1. [x] Testskript `test_all_pdfs.py` erstellen
2. [x] Phase 1 durchführen (Baseline)
3. [x] Evaluationsskript `evaluate_ocr.py` erstellen
4. [ ] Phase 2 mit verschiedenen Lösungsansätzen testen
5. [ ] Phase 3-4 durchführen
6. [ ] Evaluationsmatrix vervollständigen
7. [ ] Empfehlung für Produktions-Pipeline ableiten

---

## Referenzen

- [QUELLENANALYSE](QUELLENANALYSE.md) für Pilotdateien und Dokumenttypen
- [OCR-ENGINES](OCR-ENGINES.md) für Engine-spezifische Informationen
- [DECISIONS](DECISIONS.md) O10 für Spalten-Lösungsansätze

---

*Erstellt: 2026-01-29 | Aktualisiert: 2026-02-18*
