---
type: knowledge
created: 2026-01-29
updated: 2026-02-25
tags: [zbz-ocr-tei, korpus, dokumenttypen, pilot]
status: active
---

# Quellenanalyse

Analyse der PDF-Quelldigitalisate für das Hersch-Editionsprojekt. Single Source für Korpusdaten, Dokumenttypen und Pilotdateien.

**Abhängigkeiten:** Keine (Grundlagendokument)

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
| Zeitraum | 1931-2010 |
| Schwerpunkt | 1970er/1980er Jahre (191 Texte) |

---

## Publikationsformen

| Gattung | Anzahl | Anteil |
|---------|--------|--------|
| Zeitschriftenartikel (journalArticle) | 159 | 49% |
| Sammelbandbeiträge (bookSection) | 127 | 39% |
| Monografien (book) | 38 | 12% |
| AV-Medium | 1 | <1% |

Die Dominanz kurzer Artikel (Median 6 Seiten) ermöglicht schnelle Iterationen im PoC. Die 38 Monografien (bis 588 Seiten) erfordern Chunking-Strategien.

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

1. **OCR**: Französische Typografie (Guillemets, Akzente, Ligaturen)
2. **Silbentrennung**: Französische Trennregeln unterscheiden sich von deutschen
3. **Normalisierung**: Leerzeichen vor `:;?!` entfernen (frz. Konvention)
4. **Prompt-Design**: Beispiele primär französisch

---

## Bearbeitungsstand

### Masterfile (Erhebung Jan 2026)

| Phase | Anzahl | Anteil |
|-------|--------|--------|
| Digitalisiert | 289 | 88% |
| Korrigiert | 122 | 37% |
| TEI-ausgezeichnet | 21 | 6% |
| Publiziert | 0 | 0% |

### Datenlieferung Feb 2026 (E23)

| Kategorie | Anzahl | Bemerkung |
|-----------|--------|-----------|
| PDFs mit fertiger TEI-Annotation | 24 | + PAGE-XML-Export (Transkribus, Schema 2013, leer) |
| Fertige TEI-XMLs | 25 | 890 + 1520 haben XML, aber PDF in anderem Ordner |
| PDFs ohne Annotation | 262 | Noch nicht bearbeitet |
| **Gesamt geliefert** | **286 PDFs** | Masterfile zaehlt 289 — 3 Differenz ungeklaert |

Der Engpass liegt bei der TEI-Auszeichnung. Hier bietet die LLM-Pipeline den groessten Mehrwert.

---

## Dokumenttypen (A-D)

Klassifikation aller Dokumente in 4 Typen mit unterschiedlichen Pipeline-Strategien.

| Typ | Layout | Beschreibung | Pipeline-Strategie |
|-----|--------|-------------|-------------------|
| **A** | Einspaltig | Standard-Fließtext | OCR direkt (DeepSeek/Mistral) |
| **B** | Zweispaltig | Zeitschriften, Lexika | Layout-Analyse + OCR pro Region, oder Gemini Agentic Vision |
| **C** | Monografie | Lange Texte (100+ Seiten) | OCR + Chunking |
| **D** | Spezial | Historische Drucke, Interviews, Bildbände | Fallweise Behandlung |

---

## Pilotdateien (15 PDFs)

Single Source für alle Pilot-PDF-Metadaten. Andere Dokumente verweisen hierher.

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
| 1520.pdf | 142 | FR | C | Monografie | Lang |
| 90.pdf | 6 | DE | D | Hist. Druck | 1944 |
| 830.pdf | 2 | FR | D | Bildband | Wenig Text |
| 1440.pdf | 5 | DE | D | Interview | Dialog-Format |
| 1330.pdf | 6 | FR | D | Sammelband | Vorwort |

---

## Identifizierte Problemfälle

| Problem | Betroffene PDFs | Lösungsansatz |
|---------|-----------------|---------------|
| Zweispaltige Lesereihenfolge | 2530, 890, 3040 | Docling Layout oder Gemini Agentic Vision |
| Seitenübergreifende Fußnoten | 3040 | `@next/@prev` Verkettung |
| Interview-Sprecherwechsel | 1440 | Muster-Erkennung |
| Historischer Druck | 90 | Beide OCR-Engines testen |
| Handschriftliche Annotationen | 40 | Noch offen |
| ~~Sprache unbekannt~~ | ~~1520~~ | Geloest: Franzoesisch (25.02.2026) |

---

## Typografie

### Französische Besonderheiten (relevant für OCR)

| Zeichen | Beispiel | OCR-Fehlerrisiko |
|---------|----------|------------------|
| Guillemets | << >> | Oft als " " erkannt |
| Ligaturen | oe (coeur) | Meist korrekt |
| Akzente | e e e e | Gelegentlich Fehler |
| Apostroph | l'homme | U+2019 vs U+0027 |

### Schriftqualität

- Neuere Drucke (1950+): Gut lesbar
- Historischer Druck 90.pdf (1944): Leicht eingeschränkt

### Scan-Qualität

| Aspekt | Bewertung |
|--------|-----------|
| Auflösung | Ausreichend für OCR |
| Kontrast | Gut bis sehr gut |
| Verzerrungen | Minimal |
| Vollständigkeit | Keine fehlenden Seiten erkannt |

---

## Referenzen

- [TESTPLAN](TESTPLAN.md) für OCR-Testergebnisse pro Pilotdatei
- [OCR-ENGINES](OCR-ENGINES.md) für Engine-Auswahl pro Dokumenttyp
- [PIPELINE](PIPELINE.md) für Pipeline-Strategien

---

*Erstellt: 2026-01-29 | Aktualisiert: 2026-02-27 (Datenlieferung E23: 286 PDFs, 25 TEI-XMLs)*
