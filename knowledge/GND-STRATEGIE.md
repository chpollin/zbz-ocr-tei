---
type: knowledge
created: 2026-01-29
updated: 2026-02-25
tags: [zbz-ocr-tei, gnd, ner, entity-linking]
status: active
---

# GND-Strategie

Strategie für Named Entity Recognition und GND-Verknüpfung im Hersch-Editionsprojekt.

> **Scope:** Seit der Scope-Erweiterung (E21) fuehrt zbz-ocr-tei NER + GND-Verknuepfung selbst durch (Phase 2 in [PLAN.md](../PLAN.md)). Implementierung: `scripts/ner/ner_pipeline.py` + `gnd_linker.py`. GND-Seed (75 Entitaeten) als Grundlage.

**Abhängigkeiten:** [TEI-MAPPING](TEI-MAPPING.md)

**Offene Fragen:** Siehe [DECISIONS](DECISIONS.md).

---

## Übersicht

Die Registererschließung ist ein zentrales Editionsziel. Alle Personen, Organisationen und Werke sollen mit GND-IDs (Gemeinsame Normdatei) verknüpft werden.

### Entitätstypen

| Typ | TEI-Element | Attribut | Beispiel |
|-----|-------------|----------|----------|
| Person | `<persName>` | `ref="GND:..."` | `<persName ref="GND:118557106">Karl Jaspers</persName>` |
| Organisation | `<orgName>` | `ref="GND:..."` | `<orgName ref="GND:...">UNESCO</orgName>` |
| Werk | `<bibl>` | `corresp="GND:..."` | `<bibl corresp="GND:4343581-6">Philosophie</bibl>` |

### Grundregel

**Jede Nennung wird verlinkt**, auch bei Wiederholung im selben Dokument.

**Ausnahme:** Keine Auszeichnung in Bildunterschriften.

---

## Pipeline-Position

Die GND-Verknüpfung ist der komplexeste Schritt und erfordert externe Ressourcen:

```
OCR → TEI-Grundstruktur → NER → GND-Lookup → Validierung → Manuelle QS
                          ↑
                    Dieser Schritt
```

### Optionen für die Implementierung

| Ansatz | Beschreibung | Vor-/Nachteile |
|--------|--------------|----------------|
| **Integriert** | LLM führt NER + GND-Lookup in einem Schritt durch | Einfacher Prompt, aber GND-Halluzinationen möglich |
| **Zweistufig** | 1. LLM markiert Entitäten, 2. Separater GND-Lookup | Kontrollierter, aber aufwendiger |
| **Nachgelagert** | TEI ohne GND erzeugen, GND-Verknüpfung separat | Entkoppelt, manuelle QS einfacher |

**Empfehlung für PoC:** Nachgelagerter Ansatz – TEI-Struktur zuerst validieren, GND-Verknüpfung als separaten Schritt.

---

## NER (Named Entity Recognition)

### Zu erkennende Entitäten

| Entität | Erkennungsmerkmale | Schwierigkeit |
|---------|-------------------|---------------|
| **Personen** | Großschreibung, Vor-/Nachname, Titel (Dr., Prof.) | Mittel |
| **Organisationen** | Großschreibung, Akronyme (UNESCO, UNO) | Mittel |
| **Werke** | Kursivierung, Anführungszeichen, "sein Buch X" | Hoch |

### Herausforderungen

1. **Mehrsprachigkeit**: 66% Französisch, 30% Deutsch – unterschiedliche Namenskonventionen
2. **Historische Varianten**: Namensschreibweisen können variieren
3. **Kontextabhängigkeit**: "Jaspers" kann Person oder Werk (Possessiv: "Jaspers' Philosophie") sein
4. **Pronomina**: "Er sagte..." – keine Verknüpfung bei Pronomen

---

## GND-Lookup

### GND-API

Die GND bietet eine REST-API für Abfragen:

```
https://lobid.org/gnd/search?q=Karl+Jaspers&format=json
```

### Disambiguierung

| Problem | Beispiel | Lösungsansatz |
|---------|----------|---------------|
| **Namensgleichheit** | Mehrere "Martin Heidegger" in GND | Lebensdaten, Beruf als Filter |
| **Namensvarianten** | "J. Hersch" vs. "Jeanne Hersch" | Alias-Suche in GND |
| **Unbekannte Personen** | Lokale Figuren ohne GND-Eintrag | Markieren für manuelle Bearbeitung |

### Entitäten im Kontext Jeanne Hersch

Erwartete häufige Entitäten (basierend auf Werk und Biografie):

| Person | GND-ID | Relevanz |
|--------|--------|----------|
| Karl Jaspers | 118557106 | Lehrer, häufige Referenz |
| Martin Heidegger | 118547798 | Philosophischer Kontext |
| Hannah Arendt | 118502751 | Zeitgenossin |
| Jean-Paul Sartre | 118605895 | Existenzialismus |
| UNESCO | (Körperschaft) | Arbeitgeber 1966–1968 |

---

## Entitätsquellen

### Vorhandene Quellen

| Quelle | Beschreibung | Status |
|--------|--------------|--------|
| **TEI-Referenzdateien** | 25 XMLs mit GND-Verknüpfungen (E23: Datenlieferung Feb 2026) | 18 extrahiert, 7 neue verfuegbar |
| **Masterfile.xlsx** | Bibliografische Metadaten | Keine Entitätsliste |
| **Alma/Swisscovery** | Nachlass-Katalog | Möglicherweise verknüpfte Normdaten |

### Extrahierte GND-Entitäten (29.01.2026)

**Skript:** `scripts/extract_gnd.py`
**Ausgabe:** `output/gnd_analysis/`

| Typ | Anzahl | Häufigste |
|-----|--------|-----------|
| Personen | 41 | Karl Jaspers (90x), GND:118557106 |
| Organisationen | 10 | O.L.P. (4x), UNESCO (2x) |
| Werke | 24 | Philosophie (3x), Die geistige Situation der Zeit (3x) |

**Top-5 Personen:**

| GND-ID | Name | Vorkommen |
|--------|------|-----------|
| 118557106 | Karl Jaspers | 90 |
| 118815679 | Jeanne Hersch | 24 |
| 1145431410 | (Interviewer) | 23 |
| 118509578 | Bergson | 8 |
| 118562002 | Kierkegaard | 7 |

Diese Liste dient als **Seed** für den GND-Lookup.

---

## Implementierungsoptionen

### Option A: Prompt-basiert (LLM)

```
Identifiziere alle Personen, Organisationen und Werke im Text.
Für jede Entität:
1. Markiere mit dem entsprechenden TEI-Element
2. Suche die GND-ID (falls bekannt)
3. Wenn unsicher, markiere mit ref="GND:???"
```

**Risiko:** LLM könnte GND-IDs halluzinieren.

### Option B: Zweistufig

**Stufe 1 (LLM):**
```xml
<persName>Karl Jaspers</persName>  <!-- ohne ref -->
```

**Stufe 2 (Script):**
- Extrahiere alle markierten Entitäten
- Lookup gegen GND-API
- Füge `ref`-Attribute hinzu
- Markiere Unsicherheiten für manuelle Review

### Option C: Nachgelagert (empfohlen für PoC)

1. TEI-Erzeugung **ohne** GND-Verknüpfung
2. Separate NER auf dem TEI-Output
3. GND-Lookup mit Validierung
4. Manuelle Review für Unsicherheiten

---

## Qualitätssicherung

### Metriken

| Metrik | Beschreibung |
|--------|--------------|
| **Precision** | Anteil korrekter GND-Verknüpfungen an allen Verknüpfungen |
| **Recall** | Anteil gefundener Entitäten an allen tatsächlichen Entitäten |
| **Disambiguierungsrate** | Anteil eindeutig zugeordneter GND-IDs |

### Fehlerklassen

| Fehlertyp | Beispiel | Schwere |
|-----------|----------|---------|
| **Falsche GND-ID** | Falscher "Martin Müller" verknüpft | Hoch |
| **Fehlende Entität** | Person nicht erkannt | Mittel |
| **Halluzinierte GND-ID** | GND-ID existiert nicht | Hoch |
| **Fehlende Verknüpfung** | Person erkannt, aber ohne GND | Niedrig |

---

## Offene Fragen

- ~~Wie viele einzigartige GND-IDs sind bereits in den Referenz-TEIs?~~ → 75 Entitäten
- Welcher Anteil der Entitäten hat überhaupt einen GND-Eintrag?
- Soll im PoC GND-Verknüpfung getestet werden oder erst später?
- Wie umgehen mit Entitäten ohne GND-Eintrag? (Lokale ID? Freilassen?)

---

## Nächste Schritte

1. [x] GND-IDs aus Referenz-TEI extrahieren
2. [x] Häufigkeitsanalyse der Entitäten
3. [ ] GND-API-Anbindung prototypisch testen (lobid.org) -- Phase 2
4. [x] Entscheidung: NER + GND jetzt in zbz-ocr-tei (E21 ueberholt E5/E12)

---

## Referenzen

- [TEI-MAPPING](TEI-MAPPING.md) für TEI-Elementspezifikation
- [QUELLENANALYSE](QUELLENANALYSE.md) für Korpus und Sprachen
- [PIPELINE](PIPELINE.md) für Pipeline-Position
- [DECISIONS](DECISIONS.md) O11-O12 für offene GND-Fragen

---

*Erstellt: 2026-01-29 | Aktualisiert: 2026-02-27 (25 statt 18 TEI-Referenzdateien nach E23)*
