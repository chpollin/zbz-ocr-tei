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

| Datei | Seiten | Sprache | Typ | Texttyp | Besonderheit |
|-------|--------|---------|-----|---------|--------------|
| 2310.pdf | 3 | FR | A | Rezension | JSTOR-Metadaten |
| 1180.pdf | 8 | DE/FR | A | Jahresbericht | Titelblatt |
| 130.pdf | 18 | FR | A | Zeitschrift | Deckblatt |
| 290.pdf | 5 | FR | A | Comptes Rendus | Essay |
| 1410.pdf | 6 | DE/FR | A | Beitrag | Zweisprachig |
| 1060.pdf | 8 | DE | A | Broschüre | Rede |
| 2530.pdf | 2 | FR | B | Artikel | Zweispaltig |
| 890.pdf | 7 | DE | B | Lehrerzeitung | Kleine Schrift |
| 3040.pdf | 9 | FR | B | Lexikon | Fußnoten |
| 40.pdf | 156 | FR | C | Roman | Handschrift-Notizen |
| 1520.pdf | 142 | ? | C | Monografie | Lang |
| 90.pdf | 6 | DE | D | Hist. Druck | 1944 |
| 830.pdf | 2 | FR | D | Bildband | Wenig Text |
| 1440.pdf | 5 | DE | D | Interview | Dialog-Format |
| 1330.pdf | 6 | FR | D | Sammelband | Vorwort |

### Testphasen

Siehe [Testplan-OCR.md](Testplan-OCR.md) für Details und Ergebnisse.

| Phase | Typ | Status | Ergebnis |
|-------|-----|--------|----------|
| 1 | A (einspaltig) | Abgeschlossen | 94.4% Genauigkeit |
| 2 | B (zweispaltig) | Blockiert | Spalten-Problem |
| 3 | D (Spezial) | Ausstehend | GPU nötig |
| 4 | C (Monografien) | Ausstehend | GPU nötig |

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

- Handschriftliche Annotationen in 40.pdf – wie behandeln?
- 1520.pdf Sprache unbekannt – bei nächstem Test prüfen

---

*Aktualisiert: 29.01.2026*
