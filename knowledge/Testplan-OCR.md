# Testplan: OCR-Evaluation aller Dokumenttypen

## Ziel

Systematische Evaluation der OCR-Qualität für alle 15 Pilot-PDFs, um:
1. Layout-spezifische Probleme zu identifizieren
2. Dokumenttyp-abhängige Verarbeitungsstrategien zu entwickeln
3. Qualitätsmetriken pro Dokumenttyp zu etablieren

---

## Dokumenttypen-Klassifikation

### Typ A: Einspaltig, einfach
| PDF | Seiten | Sprache | Besonderheit |
|-----|--------|---------|--------------|
| 2310 | 3 | FR | JSTOR-Metadaten-Seite |
| 1180 | 8 | DE/FR | Jahresbericht, Titelblatt |
| 130 | 18 | FR | Zeitschrift mit Deckblatt |
| 290 | 5 | FR | Comptes Rendus |
| 1410 | 6 | DE/FR | Zweisprachiges Titelblatt |
| 1060 | 8 | DE | Broschüre/Rede |

### Typ B: Zweispaltig
| PDF | Seiten | Sprache | Besonderheit |
|-----|--------|---------|--------------|
| 2530 | 2 | FR | Zeitschriftenartikel |
| 890 | 7 | DE | Lehrerzeitung, kleiner Text |
| 3040 | 9 | FR | Lexikon mit Fußnoten |

### Typ C: Monografien
| PDF | Seiten | Sprache | Besonderheit |
|-----|--------|---------|--------------|
| 40 | 156 | FR | Roman, handschriftliche Notizen |
| 1520 | 142 | ? | Monografie |

### Typ D: Spezialformate
| PDF | Seiten | Sprache | Besonderheit |
|-----|--------|---------|--------------|
| 90 | 6 | DE | Historischer Druck (1944) |
| 830 | 2 | FR | Bildband mit wenig Text |
| 1440 | 5 | DE | Interview/Dialog-Format |
| 1330 | 6 | FR | Sammelband mit Vorwort |

---

## Testphasen

### Phase 1: Baseline (Typ A - einspaltig)
**Ziel:** OCR-Grundqualität validieren

| Schritt | PDF | Test | Erwartung |
|---------|-----|------|-----------|
| 1.1 | 2310 | OCR Seite 2-3 | Französischer Text, Akzente |
| 1.2 | 1180 | OCR Seite 2 | Deutscher Text, Fließtext |
| 1.3 | 290 | OCR Seite 1 | Französischer Essay |

**Metriken:**
- [ ] Zeichengenauigkeit (Akzente, Sonderzeichen)
- [ ] Absatzerkennung
- [ ] Silbentrennung erkannt

---

### Phase 2: Layout-Herausforderungen (Typ B - zweispaltig)
**Ziel:** Spalten-Lesereihenfolge testen

| Schritt | PDF | Test | Erwartung |
|---------|-----|------|-----------|
| 2.1 | 2530 | OCR beide Seiten | Spalten korrekt? (bereits getestet: NEIN) |
| 2.2 | 890 | OCR Seite 2 | Zweispaltig + kleine Schrift |
| 2.3 | 3040 | OCR Seite 1 | Lexikon: Spalten + Fussnoten |

**Metriken:**
- [ ] Spalten-Lesereihenfolge korrekt?
- [ ] Fussnoten erkannt und positioniert?
- [ ] Text vollständig?

**Bekanntes Problem:** 2530 hat falsche Spaltenreihenfolge

**Drei Lösungsansätze testen:**

| Ansatz | Methode | Aufwand |
|--------|---------|---------|
| A | Docling Layout + DeepSeek pro Region | Mittel |
| B | Gemini 3 Agentic Vision (Auto-Crop) | Gering |
| C | DeepSeek mit Prompt-Anpassung | Gering |

**NEU: Gemini 3 Agentic Vision Test (2.4)**
- PDF an Gemini 3 Flash mit Code-Execution senden
- Erwartung: Modell erkennt Spalten, croppt automatisch, liest korrekt
- Vergleich: Qualität vs. DeepSeek, Kosten vs. Docling-Pipeline

---

### Phase 3: Spezialformate (Typ D)
**Ziel:** Randfälle identifizieren

| Schritt | PDF | Test | Erwartung |
|---------|-----|------|-----------|
| 3.1 | 90 | OCR Seite 2 | Historischer Druck (1944) |
| 3.2 | 1440 | OCR Seite 1-2 | Interview-Dialog erkennen |
| 3.3 | 830 | OCR Seite 1 | Bildband: Text neben Bild |
| 3.4 | 1330 | OCR Seite 1-2 | Sammelband-Struktur |

**Metriken:**
- [ ] Dialog-Sprecher erkannt?
- [ ] Text-Bild-Trennung korrekt?
- [ ] Historische Schrift lesbar?

---

### Phase 4: Monografien (Typ C)
**Ziel:** Skalierbarkeit testen

| Schritt | PDF | Test | Erwartung |
|---------|-----|------|-----------|
| 4.1 | 40 | OCR Seite 5-6 | Roman-Fließtext |
| 4.2 | 1520 | OCR Seite 3-4 | Monografie-Inhalt |

**Metriken:**
- [ ] Konsistenz über mehrere Seiten
- [ ] Handschriftliche Notizen ignoriert/erkannt?

---

## Evaluationsmatrix

Nach Abschluss aller Tests:

| PDF | Typ | CER | WER | Genauigkeit | Status | Anmerkung |
|-----|-----|-----|-----|-------------|--------|-----------|
| 2310 | A | 2.67% | 16.61% | 97.33% | OK | Rezension, sehr gut |
| 1180 | A | 4.89% | 13.29% | 95.11% | OK | Jahresbericht, gut |
| 130 | A | ? | ? | ? | - | |
| 290 | A | 9.21% | 19.53% | 90.79% | OK | Comptes Rendus |
| 1410 | A | ? | ? | ? | - | |
| 1060 | A | ? | ? | ? | - | |
| 2530 | B | ~0% | ~0% | ~99% | LAYOUT | Spaltenreihenfolge falsch |
| 890 | B | ? | ? | ? | - | |
| 3040 | B | ? | ? | ? | - | |
| 40 | C | ? | ? | ? | - | |
| 1520 | C | ? | ? | ? | - | |
| 90 | D | ? | ? | ? | - | |
| 830 | D | ? | ? | ? | - | |
| 1440 | D | ? | ? | ? | - | |
| 1330 | D | ? | ? | ? | - | |

**Bewertungsskala:**
- OK: CER < 5% (Zeichengenauigkeit > 95%)
- Akzeptabel: CER 5-15% (manuell korrigierbar)
- Problematisch: CER > 15% oder strukturelle Fehler (LAYOUT)

**Metriken:**
- **CER** (Character Error Rate): Anteil falscher Zeichen
- **WER** (Word Error Rate): Anteil falscher Wörter
- **Genauigkeit**: 100% - CER

---

## Technische Umsetzung

### Testskript erweitern

```python
# scripts/test_all_pdfs.py

TESTPLAN = {
    # Phase 1: Einspaltig
    "phase1": [
        {"pdf": "2310.pdf", "pages": [2, 3], "type": "A"},
        {"pdf": "1180.pdf", "pages": [2], "type": "A"},
        {"pdf": "290.pdf", "pages": [1], "type": "A"},
    ],
    # Phase 2: Zweispaltig
    "phase2": [
        {"pdf": "2530.pdf", "pages": [1, 2], "type": "B"},
        {"pdf": "890.pdf", "pages": [2], "type": "B"},
        {"pdf": "3040.pdf", "pages": [1], "type": "B"},
    ],
    # Phase 3: Spezialformate
    "phase3": [
        {"pdf": "90.pdf", "pages": [2], "type": "D"},
        {"pdf": "1440.pdf", "pages": [1, 2], "type": "D"},
        {"pdf": "830.pdf", "pages": [1], "type": "D"},
        {"pdf": "1330.pdf", "pages": [1, 2], "type": "D"},
    ],
    # Phase 4: Monografien
    "phase4": [
        {"pdf": "40.pdf", "pages": [5, 6], "type": "C"},
        {"pdf": "1520.pdf", "pages": [3, 4], "type": "C"},
    ],
}
```

### Ausgabestruktur

```
output/
├── ocr_results/
│   ├── 2310_p2.md
│   ├── 2310_p3.md
│   ├── 1180_p2.md
│   └── ...
├── evaluation/
│   ├── phase1_report.md
│   ├── phase2_report.md
│   └── summary.md
└── layout_samples/
    └── (bereits erstellt)
```

---

## Lösungsansätze für bekannte Probleme

### Problem: Zweispaltige Layouts (2530, 890, 3040)

**Option A: Prompt-Anpassung**
```
Prompt: "This is a two-column document. Read the left column completely first,
then the right column. Convert to markdown."
```

**Option B: Layout-Segmentierung vorschalten**
- Docling für Layout-Analyse nutzen
- Spalten einzeln an DeepSeek-OCR übergeben

**Option C: Post-Processing mit LLM**
- OCR-Output an Claude/GPT übergeben
- Anweisung: "Korrigiere die Lesereihenfolge basierend auf dem Kontext"

**Option D: Alternative OCR (Docling)**
- Docling hat eingebaute Layout-Analyse
- Vergleichstest durchführen

---

## Nächste Schritte

1. [x] Testskript `test_all_pdfs.py` erstellen ✅
2. [x] Phase 1 durchführen (Baseline) ✅
3. [x] Evaluationsskript `evaluate_ocr.py` erstellen ✅
4. [ ] Phase 2 mit verschiedenen Prompt-Varianten testen
5. [ ] Docling als Alternative für Typ B evaluieren
6. [ ] Phase 3-4 durchführen
7. [ ] Evaluationsmatrix vervollständigen
8. [ ] Empfehlung für Produktions-Pipeline ableiten

---

## Zeitplan

| Phase | Aufwand | Abhängigkeit |
|-------|---------|--------------|
| Testskript erstellen | ~ | - |
| Phase 1 (Baseline) | ~ | Skript |
| Phase 2 (Zweispaltig) | ~ | Phase 1 |
| Phase 3 (Spezial) | ~ | Phase 1 |
| Phase 4 (Monografien) | ~ | Phase 1 |
| Auswertung & Empfehlung | ~ | Alle Phasen |

---

*Erstellt: 29.01.2026*
