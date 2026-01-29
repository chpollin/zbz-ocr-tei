# Materialanalyse ZBZ-OCR-TEI

## 1. Zusammenfassung

Das Projekt umfasst die digitale Edition von ca. 286 Texten der Philosophin Jeanne Hersch. Die Transkriptionsrichtlinien sind detailliert dokumentiert und orientieren sich am DTA-Basisformat. Die TEI-Referenzdateien zeigen konsistente Muster. Die Hauptherausforderung für einen LLM-Ansatz liegt in der semantischen Auszeichnung (Personen, Organisationen, Werke mit GND-Verknüpfung) sowie in der korrekten Strukturerkennung bei komplexen Layouts. Die Automatisierbarkeit ist grundsätzlich hoch, erfordert aber Nachbearbeitung für Normdatenverknüpfungen.

---

## 2. Transkriptionsregeln

### 2.1 Zeichenebene

| Regel | Beschreibung |
|-------|--------------|
| ß-Erhaltung | ß wird als ß transkribiert (U+00DF) |
| Gedankenstriche | Normalisierung zu Halbgeviertstrich (–) |
| Trennstriche | Normalisierung zu Viertelgeviertstrich (‐) |
| Anführungszeichen | Doppelt: "..." / Einfach: '...' |
| Apostrophe | Unicode U+2019 (') |
| Leerzeichen vor Satzzeichen | Löschen vor : ; ? ! |
| Aufzählungstrennungen | Normalisierung zu Schrägstrich (Zürich/Bern/Basel) |

### 2.2 Wortebene

| Regel | Beschreibung |
|-------|--------------|
| Silbentrennung | Entfernen am Zeilenende, `<lb break="no"/>` setzen |
| Druckfehlerkorrektur | `<choice><sic>...</sic><corr>...</corr></choice>` |
| Sprachwechsel | `<foreign xml:lang="[ISO 639-3]">` |

### 2.3 Strukturebene

| Regel | Beschreibung |
|-------|--------------|
| Absätze | `<p>` ohne Einrückungsauszeichnung |
| Überschriften | `<head>` mit verschachtelten `<title>` |
| Kapitelstruktur | `<div n="1">`, `<div n="2">`, etc. |
| Listen | `<list><item>` mit manueller Nummerierung |
| Tabellen | `<table><row><cell>` |
| Vertikaler Abstand | `<space dim="vertical"/>` |

### 2.4 Seitenstruktur

| Regel | Beschreibung |
|-------|--------------|
| Seitenumbrüche | `<pb facs="#f[Nr]" n="[Seitenzahl]"/>` |
| Zeilenumbrüche | `<lb facs="..." n="..."/>` |
| Fehlende Seitenzahlen | In eckigen Klammern: n="[42]" |
| Kolumnentitel | Nicht erfassen |

### 2.5 Semantische Auszeichnung

| Regel | Beschreibung |
|-------|--------------|
| Personen | `<persName ref="GND:...">` |
| Organisationen | `<orgName ref="GND:...">` |
| Werke | `<bibl corresp="GND:...">` |
| Mehrfachnennungen | Jede Nennung wird referenziert |

### 2.6 Spezielle Texttypen

| Texttyp | Struktur |
|---------|----------|
| Reviews | `<div type="review">` mit `<bibl>` im `<head>` |
| Interviews | `<div type="interview">` mit `<sp><speaker>` |
| Gesprächsrunden | `<div type="conversation">` |
| Lexikonartikel | `<div type="entry">` mit `<head type="lemma">` |

### 2.7 Fussnoten

| Regel | Beschreibung |
|-------|--------------|
| Positionierung | `<note place="foot" n="..." xml:id="fn[Seite]-[Nr]">` |
| Mehrseitige Fussnoten | Verkettung via `@next` und `@prev` |

### 2.8 Renderings

| Rendering | TEI-Auszeichnung |
|-----------|------------------|
| Fett | `<hi rendition="#b">` |
| Kursiv | `<hi rendition="#i">` |
| Unterstrichen | `<hi rendition="#u">` |
| Gesperrt | `<hi rendition="#g">` |
| Hochgestellt | `<hi rendition="#sup">` |
| Tiefgestellt | `<hi rendition="#sub">` |

---

## 3. TEI-Elementinventar

| Element | Attribute | Verwendung |
|---------|-----------|------------|
| `<TEI>` | xmlns, type="naegeli" | Wurzelelement |
| `<teiHeader>` | - | Metadaten (wird später per Skript befüllt) |
| `<text>` | - | Textcontainer |
| `<front>` | - | Redaktionelle Hinweise, Entstehungskontext |
| `<body>` | - | Haupttext |
| `<back>` | - | Übersetzungs-/Nachdruckhinweise |
| `<div>` | n, type | Strukturierung (n=1,2,3 oder type=review/interview/entry) |
| `<pb>` | facs, n | Seitenumbruch |
| `<lb>` | facs, n, break | Zeilenumbruch |
| `<head>` | type | Überschriften |
| `<title>` | type (main/sub) | Titel |
| `<p>` | facs | Absatz |
| `<hi>` | rendition | Hervorhebungen |
| `<persName>` | ref | Personennamen mit GND |
| `<orgName>` | ref | Organisationen mit GND |
| `<bibl>` | corresp | Werkverweise mit GND |
| `<note>` | place, n, xml:id, next, prev | Fussnoten |
| `<foreign>` | xml:lang | Sprachwechsel |
| `<space>` | dim | Vertikaler Abstand |
| `<list>`, `<item>` | - | Listen |
| `<table>`, `<row>`, `<cell>` | - | Tabellen |
| `<figure>`, `<graphic>` | xml:id, url | Abbildungen |
| `<choice>`, `<sic>`, `<corr>` | - | Druckfehlerkorrektur |
| `<sp>`, `<speaker>` | type | Redebeiträge (Interviews) |

---

## 4. Dokumentklassifikation

| Datei | Größe (MB) | Sprache | Texttyp | Komplexität |
|-------|------------|---------|---------|-------------|
| 40.pdf | 39.0 | FR | Monografie | Hoch (umfangreich) |
| 1520.pdf | 42.1 | ? | Monografie | Hoch (umfangreich) |
| 890.pdf | 9.7 | DE | Vortrag mit Front | Mittel |
| 3040.pdf | 5.2 | FR | Lexikonartikel | Mittel-Hoch |
| 1060.pdf | 2.6 | ? | ? | Mittel |
| 1330.pdf | 1.5 | ? | ? | Mittel |
| 1440.pdf | 1.3 | ? | ? | Mittel |
| 830.pdf | 1.1 | ? | ? | Mittel |
| 2310.pdf | 0.8 | FR | Rezension | Niedrig |
| 90.pdf | 0.7 | ? | ? | Niedrig |
| 290.pdf | 0.6 | ? | ? | Niedrig |
| 130.pdf | 0.5 | FR | Essay | Mittel |
| 1410.pdf | 0.4 | ? | ? | Niedrig |
| 1180.pdf | 0.3 | ? | ? | Niedrig |
| 2530.pdf | 0.08 | ? | ? | Niedrig |

**Sprachen im Korpus:** Französisch (dominant), Deutsch, vermutlich weitere.

---

## 5. Kritische Punkte

### 5.1 Hohe Risiken

1. **GND-Verknüpfung**: Jede Person, Organisation und jedes Werk muss mit GND-ID versehen werden. Dies erfordert externe Lookups und kann nicht rein automatisiert werden.

2. **Mehrseitige Fussnoten**: Die Verkettung über `@next/@prev` erfordert Kontextwissen über Seitengrenzen hinweg.

3. **Strukturerkennung bei komplexen Layouts**: Besonders bei Lexikonartikeln (verschachtelte `<div>`) und Interviews (`<sp>`-Struktur).

### 5.2 Mittlere Risiken

4. **Druckfehlererkennung**: Erfordert sprachliches Verständnis und Kontextwissen.

5. **Vertikale Abstände**: `<space dim="vertical"/>` ist schwer automatisch zu erkennen.

6. **Konsistente div-Nummerierung**: Die korrekte Verschachtelungstiefe (n="1", n="2", n="3") muss strukturell korrekt sein.

7. **Unterscheidung semantischer vs. typografischer Hervorhebungen**: Nur semantisch relevante Hervorhebungen sollen übernommen werden.

### 5.3 Niedrige Risiken

8. **Zeichennormalisierung**: Gut automatisierbar mit Regex/Postprocessing.

9. **Silbentrennung**: Muster gut erkennbar.

10. **Grundstruktur (pb, lb, p)**: Standardaufgabe für Vision-LLMs.

---

## 6. Empfehlungen

### 6.1 Pipeline-Architektur

```
PDF → Vision-LLM (OCR + Basisstruktur) → TEI-Grundgerüst
                                              ↓
                                    Postprocessing (Normalisierung)
                                              ↓
                                    NER + GND-Lookup (Personen, Orte, Werke)
                                              ↓
                                    Validierung gegen Schema
                                              ↓
                                    Manuelle Nachbearbeitung (QS)
```

### 6.2 Priorisierung für PoC

**Phase 1 (einfach):**
- Kleine PDFs (2310, 2530, 1180)
- Einfache Texttypen (Essays, Rezensionen)
- Fokus auf: OCR-Qualität, Grundstruktur (pb, lb, p, div), Renderings

**Phase 2 (mittel):**
- Mittlere PDFs (130, 290, 90)
- Fussnoten, Listen
- Sprachwechsel

**Phase 3 (komplex):**
- Lexikonartikel (3040)
- Interviews/Gesprächsrunden (890)
- GND-Integration

### 6.3 Qualitätsmetriken

1. **Zeichengenauigkeit**: Vergleich mit Referenz-XMLs (Character Error Rate)
2. **Strukturgenauigkeit**: Korrekte Element-Hierarchie (div-Verschachtelung)
3. **Entitätenerkennung**: Precision/Recall für persName, orgName, bibl
4. **GND-Korrektheit**: Anteil korrekter GND-Zuordnungen

### 6.4 Mehrwert des LLM-Ansatzes

- **Geschwindigkeit**: Schnellere Ersttranskription als manueller Transkribus-Workflow
- **Konsistenz**: Einheitliche Anwendung der Normalisierungsregeln
- **Skalierbarkeit**: 286 Texte parallel verarbeitbar
- **Strukturerkennung**: LLMs können Texttypen (Review, Interview) erkennen

### 6.5 Grenzen des LLM-Ansatzes

- GND-Verknüpfung erfordert externes System
- Komplexe Fussnoten-Verkettung braucht Speziallogik
- Finale QS bleibt manuell notwendig

---

*Erstellt: 29.01.2026*
