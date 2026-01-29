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

### Empfehlung für PoC-Reihenfolge

1. **Phase 1 (einfach)**: 2310.pdf, 2530.pdf, 1180.pdf – Kleine Dateien, einfache Struktur
2. **Phase 2 (mittel)**: 130.pdf, 290.pdf, 90.pdf – Mittlere Größe, Essays
3. **Phase 3 (komplex)**: 3040.pdf (Lexikon), 890.pdf (Vortrag mit Front)

---

## Layout-Typen

*TODO: Visuelle Analyse der PDF-Scans erforderlich*

Erwartete Varianten basierend auf Publikationsformen:

| Layout-Typ | Vorkommen | Herausforderung |
|------------|-----------|-----------------|
| Einspaltig (Fließtext) | Häufig | Niedrig |
| Zweispaltig | Zeitschriften | Mittel – Lesereihenfolge |
| Mit Fußnoten | Häufig | Mittel – Positionierung |
| Mit Marginalien | Selten? | Hoch – Zuordnung zum Text |
| Tabellen | Lexikonartikel | Mittel |
| Abbildungen | Vereinzelt | Mittel – figure/graphic |

---

## Typografie

*TODO: Visuelle Analyse der PDF-Scans erforderlich*

### Erwartete Schriftarten

| Zeitraum | Erwartete Schrift | OCR-Schwierigkeit |
|----------|-------------------|-------------------|
| 1931–1950 | Antiqua, evtl. ältere Satztypen | Mittel |
| 1950–1980 | Antiqua (Bleisatz) | Niedrig |
| 1980–2010 | Digitalsatz | Niedrig |

### Französische Typografie-Besonderheiten

- Guillemets: « » (nicht " ")
- Ligaturen: œ (cœur), æ (seltener)
- Akzente: é, è, ê, ë, à, â, ù, û, ç, î, ï, ô
- Apostroph: l'homme, d'abord (U+2019)

---

## Scan-Qualität

*TODO: Visuelle Analyse der PDF-Scans erforderlich*

Zu prüfende Aspekte:

- [ ] Auflösung (DPI)
- [ ] Kontrast (ausreichend für OCR?)
- [ ] Verzerrungen (Buchfalz, Perspektive)
- [ ] Flecken, Durchscheinen
- [ ] Vollständigkeit (fehlende Seiten?)

---

## Problemfälle

*TODO: Identifikation aus PDF-Analyse*

Potenzielle Problemkategorien:

1. **Seitenübergreifende Fußnoten**: Verkettung via `@next/@prev` erforderlich
2. **Komplexe Layouts**: Lexikonartikel mit verschachtelten Strukturen
3. **Interviews/Gesprächsrunden**: Sprecherwechsel erkennen
4. **Mehrsprachige Texte**: Sprachwechsel innerhalb eines Dokuments
5. **Druckfehler**: Erkennung erfordert sprachliches Verständnis

---

## Offene Fragen

- Wie variiert die Scan-Qualität über die Jahrzehnte?
- Gibt es systematische Layout-Unterschiede zwischen Zeitschriften und Sammelbänden?
- Welche PDFs enthalten Tabellen oder Abbildungen?
- Gibt es handschriftliche Annotationen in den Scans?

---

*Erstellt: 29.01.2026*
