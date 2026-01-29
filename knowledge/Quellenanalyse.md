# Quellenanalyse

Analyse der PDF-Quelldigitalisate für das Hersch-Editionsprojekt.

---

## Korpusübersicht

| Aspekt | Wert |
|--------|------|
| Gesamteinträge Masterfile | 327 |
| Davon ausgeschieden (Übersetzungen/Nachdrucke) | 38 |
| Effektiver Korpusumfang | 289 Texte |
| Gesamtseitenzahl | ca. 7.200 Seiten |
| Median pro Text | 6 Seiten |
| Maximum | 588 Seiten |
| Zeitraum | 1931–2010 |
| Schwerpunkt | 1970er/1980er Jahre (191 Texte) |

---

## Publikationsformen

| Gattung | Anzahl | Anteil |
|---------|--------|--------|
| Zeitschriftenartikel (journalArticle) | 159 | 49% |
| Sammelbandbeiträge (bookSection) | 127 | 39% |
| Monografien (book) | 38 | 12% |
| AV-Medium | 1 | <1% |

Die Dominanz kurzer Artikel (Median 6 Seiten) ermöglicht schnelle Iterationen im PoC. Die 38 Monografien (bis 588 Seiten) erfordern möglicherweise eine andere Verarbeitungsstrategie (Chunking, mehrstufige Verarbeitung).

---

## Sprachverteilung

| Sprache | Anzahl | Anteil |
|---------|--------|--------|
| Französisch | 215 | 66% |
| Deutsch | 98 | 30% |
| Englisch | 8 | 2% |
| Italienisch | 2 | 1% |
| Zweisprachig (fr/de) | 1 | <1% |

### Implikationen für die Pipeline

Die französische Dominanz (66%) hat Konsequenzen für:

1. **OCR**: Französische Typografie (Guillemets «», Akzente é è ê ë, Ligaturen œ æ)
2. **Silbentrennung**: Französische Trennregeln unterscheiden sich von deutschen
3. **Normalisierung**: Leerzeichen vor `:;?!` müssen entfernt werden (französische Konvention)
4. **Prompt-Design**: Beispiele im Prompt sollten primär französisch sein

---

## Bearbeitungsstand (aus Masterfile)

| Phase | Anzahl | Anteil |
|-------|--------|--------|
| Digitalisiert | 289 | 88% |
| Korrigiert | 122 | 37% |
| TEI-ausgezeichnet | 21 | 6% |
| Publiziert | 0 | 0% |

Der Engpass liegt bei der TEI-Auszeichnung (nur 6% abgeschlossen). Hier kann LLM-Unterstützung den größten Mehrwert bieten.

---

## Pilot-Dateien (15 PDFs)

Die folgenden PDFs stehen für den PoC zur Verfügung:

| Datei | Größe | Sprache | Texttyp | Komplexität |
|-------|-------|---------|---------|-------------|
| 40.pdf | 39.0 MB | FR | Monografie | Hoch |
| 1520.pdf | 42.1 MB | ? | Monografie | Hoch |
| 890.pdf | 9.7 MB | DE | Vortrag mit Front | Mittel |
| 3040.pdf | 5.2 MB | FR | Lexikonartikel | Mittel-Hoch |
| 1060.pdf | 2.6 MB | ? | ? | Mittel |
| 1330.pdf | 1.5 MB | ? | ? | Mittel |
| 1440.pdf | 1.3 MB | ? | ? | Mittel |
| 830.pdf | 1.1 MB | ? | ? | Mittel |
| 2310.pdf | 0.8 MB | FR | Rezension | Niedrig |
| 90.pdf | 0.7 MB | ? | ? | Niedrig |
| 290.pdf | 0.6 MB | ? | ? | Niedrig |
| 130.pdf | 0.5 MB | FR | Essay | Mittel |
| 1410.pdf | 0.4 MB | ? | ? | Niedrig |
| 1180.pdf | 0.3 MB | ? | ? | Niedrig |
| 2530.pdf | 0.08 MB | ? | ? | Niedrig |

### Testphasen

Siehe [Testplan-OCR.md](Testplan-OCR.md) für aktuelle Phasen:
- Phase 1: Typ A (einspaltig) - **abgeschlossen**
- Phase 2: Typ B (zweispaltig) - ausstehend
- Phase 3: Typ D (Spezial) - ausstehend
- Phase 4: Typ C (Monografien) - ausstehend

---

## Layout-Typen (analysiert)

Basierend auf visueller Analyse aller 15 Pilot-PDFs:

| Typ | Layout | PDFs | OCR-Strategie |
|-----|--------|------|---------------|
| A | Einspaltig | 2310, 1180, 130, 290, 1410, 1060 | Standard DeepSeek |
| B | Zweispaltig | 2530, 890, 3040 | Docling oder Prompt-Tuning |
| C | Monografie | 40, 1520 | Chunking nötig |
| D | Spezial | 90, 830, 1330, 1440 | Einzelfallprüfung |

**Details siehe [Testplan-OCR.md](Testplan-OCR.md)**

---

## Typografie

### Französische Besonderheiten (relevant für OCR)

| Zeichen | Beispiel | OCR-Fehlerrisiko |
|---------|----------|------------------|
| Guillemets | « » | Oft als " " erkannt |
| Ligaturen | œ (cœur) | Meist korrekt |
| Akzente | é è ê ë | Gelegentlich Fehler |
| Apostroph | l'homme | U+2019 vs U+0027 |

### Schriftqualität (beobachtet)

- Neuere Drucke (1950+): Gut lesbar
- Historischer Druck 90.pdf (1944): Leicht eingeschränkt

---

## Scan-Qualität (beobachtet)

Basierend auf Layout-Sample-Extraktion (`output/layout_samples/`):

| Aspekt | Bewertung |
|--------|-----------|
| Auflösung | Ausreichend für OCR |
| Kontrast | Gut bis sehr gut |
| Verzerrungen | Minimal |
| Vollständigkeit | Keine fehlenden Seiten erkannt |

---

## Identifizierte Problemfälle

| Problem | Betroffene PDFs | Lösungsansatz |
|---------|-----------------|---------------|
| Zweispaltige Lesereihenfolge | 2530, 890, 3040 | Docling oder Prompt |
| Seitenübergreifende Fußnoten | 3040 | `@next/@prev` Verkettung |
| Interview-Sprecherwechsel | 1440 | Muster-Erkennung |
| Historischer Druck | 90 | Beide OCR-Engines testen |

---

## Offene Fragen

- Welche PDFs enthalten Tabellen? (3040 hat Lexikon-Struktur)
- Handschriftliche Annotationen in 40.pdf (Monografie)?

---

*Aktualisiert: 29.01.2026*
