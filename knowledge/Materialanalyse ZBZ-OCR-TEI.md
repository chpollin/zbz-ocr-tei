# Materialanalyse ZBZ-OCR-TEI

Übersicht und Zusammenfassung der Analysedokumente für das Hersch-Editionsprojekt.

---

## Zusammenfassung

Das Projekt umfasst die digitale Edition von ca. 289 Texten der Philosophin Jeanne Hersch (1910–2000). Die Transkriptionsrichtlinien orientieren sich am DTA-Basisformat. Der LLM-gestützte Ansatz soll die bestehende Transkribus-Pipeline ergänzen oder teilweise ersetzen.

### Eckdaten

| Aspekt | Wert |
|--------|------|
| Korpusumfang | 289 Texte (ca. 7.200 Seiten) |
| Sprachen | 66% Französisch, 30% Deutsch, 4% andere |
| Bearbeitungsstand | 6% TEI-ausgezeichnet |
| Engpass | TEI-Auszeichnung (manuell in Oxygen) |

### Hauptherausforderungen

1. **GND-Verknüpfung** – Erfordert externe Lookups, kann nicht vollautomatisiert werden
2. **Strukturerkennung** – Komplexe Layouts (Lexikon, Interview)
3. **Mehrseitige Fußnoten** – Verkettung über Seitengrenzen

---

## Detaildokumente

| Dokument | Fokus | Inhalt |
|----------|-------|--------|
| [Quellenanalyse.md](Quellenanalyse.md) | Input | PDF-Scans, Korpus, Sprachen, Layouts, Scan-Qualität |
| [TEI-Mapping.md](TEI-Mapping.md) | Transformation | Regeln Text → TEI, Normalisierung, Elementinventar |
| [GND-Strategie.md](GND-Strategie.md) | Semantik | NER, GND-Lookup, Disambiguierung |
| [Pipeline.md](Pipeline.md) | Technik | OCR-Optionen, LLM-Auswahl, Architektur, Kosten |

---

## Kritische Punkte

### Hohe Risiken

| Risiko | Beschreibung | Detaildokument |
|--------|--------------|----------------|
| GND-Verknüpfung | Externe Lookups, Disambiguierung | [GND-Strategie.md](GND-Strategie.md) |
| Mehrseitige Fußnoten | @next/@prev-Verkettung | [TEI-Mapping.md](TEI-Mapping.md) |
| Komplexe Layouts | Lexikon, Interview, Tabellen | [Quellenanalyse.md](Quellenanalyse.md) |

### Mittlere Risiken

| Risiko | Beschreibung | Detaildokument |
|--------|--------------|----------------|
| Druckfehlererkennung | Sprachverständnis erforderlich | [TEI-Mapping.md](TEI-Mapping.md) |
| Strukturhierarchie | div n="1/2/3" korrekt verschachteln | [TEI-Mapping.md](TEI-Mapping.md) |
| Semantische Hervorhebungen | Nur relevante auszeichnen | [TEI-Mapping.md](TEI-Mapping.md) |

### Niedrige Risiken

| Risiko | Beschreibung | Detaildokument |
|--------|--------------|----------------|
| Zeichennormalisierung | Regelbasiert automatisierbar | [TEI-Mapping.md](TEI-Mapping.md) |
| Grundstruktur (pb, lb, p) | Standardaufgabe | [Pipeline.md](Pipeline.md) |

---

## Empfehlungen

### Pipeline-Ansatz

```
PDF → OCR (Markdown) → LLM (TEI) → Validierung → [GND nachgelagert]
```

Details: [Pipeline.md](Pipeline.md)

### PoC-Priorisierung

| Phase | Dokumente | Fokus |
|-------|-----------|-------|
| 1 | 2310, 2530, 1180 | OCR-Qualität, Grundstruktur |
| 2 | 130, 290, 90 | Fußnoten, Sprachwechsel |
| 3 | 3040, 890 | Lexikon, Interview, GND |

### Mehrwert des LLM-Ansatzes

- Schnellere Ersttranskription als Transkribus-Workflow
- Konsistente Normalisierung
- Skalierbarkeit (289 Texte parallel)
- Dokumenttyp-Erkennung (Review, Interview, etc.)

### Grenzen

- GND-Verknüpfung erfordert externes System
- Komplexe Fußnoten-Verkettung braucht Speziallogik
- Finale QS bleibt manuell notwendig

---

## Offene Analysen

*TODO: Noch zu erledigen*

- [ ] PDF-Scans visuell analysieren (Layouts, Qualität)
- [ ] GND-IDs aus Referenz-TEI extrahieren
- [ ] Konkrete TEI-Beispiele für Randfälle dokumentieren
- [ ] OCR-Qualität von DeepSeek-OCR-2 / Docling testen

---

*Erstellt: 29.01.2026*
