# Arbeitsjournal ZBZ-OCR-TEI

## Projektübersicht

**Auftraggeber:** Zentralbibliothek Zürich
**Projekt:** LLM-gestützte OCR und TEI-Auszeichnung für die digitale Edition der Schriften von Jeanne Hersch
**Status:** Materialanalyse abgeschlossen, Offerte in Vorbereitung

---

## 2026-01-29 | Materialanalyse

### Durchgeführte Arbeiten

**1. Projektstruktur angelegt**
- Repository-Struktur gesichtet
- Ordner identifiziert: `data/`, `knowledge/`
- Vorhandene Materialien katalogisiert

**2. Anforderungsdokumente gelesen**
- [LLM-gestützte OCR und TEI-Auszeichnung für die Zentralbibliothek Zürich.md](LLM-gestützte%20OCR%20und%20TEI-Auszeichnung%20für%20die%20Zentralbibliothek%20Zürich.md) - Projektkontext und Scope
- [Workflow Diagramm Hersch.md](Workflow%20Diagramm%20Hersch.md) - Bestehender ZBZ-Workflow
- `data/README.md` - Detaillierte Transkriptionsrichtlinien (525 Zeilen)

**3. TEI-Referenzdateien analysiert**
- 3 Dateien im Hauptordner: 100.xml, 30.xml, 560.xml
- 16 Dateien im Pilot-Ordner (davon 1 "in Arbeit")
- Stichprobenanalyse durchgeführt für:
  - 100.xml (französischer Essay über Karl Jaspers)
  - 30.xml (französischer Essay "L'obstacle du langage")
  - 560.xml (Rezension)
  - 2310.xml (Rezension)
  - 130.xml (Essay "L'école de nos périls")
  - 890.xml (deutscher Vortrag mit Front-Matter)
  - 3040.xml (Lexikonartikel über Jaspers)

**4. PDF-Bestand erfasst**
- 15 PDF-Dateien im data/scans/-Ordner
- Größenspektrum: 80 KB bis 42 MB
- Größte Dateien: 1520.pdf (42 MB), 40.pdf (39 MB) - vermutlich Monografien

**5. Analysedokument erstellt**
- [Materialanalyse ZBZ-OCR-TEI.md](Materialanalyse%20ZBZ-OCR-TEI.md)
- Enthält: Transkriptionsregeln, TEI-Elementinventar, Dokumentklassifikation, kritische Punkte, Empfehlungen

**6. .gitignore konfiguriert**
- PDFs und XMLs bleiben lokal (nicht im Repository)
- Schützt urheberrechtlich geschütztes Material

**7. Ordnerstruktur reorganisiert**
- `data/` neu strukturiert mit semantischen Unterordnern:
  - `data/richtlinien/` – DTA-Basisformat als Referenzdokument
  - `data/projektsteuerung/` – Operative Daten (Masterfile.xlsx)
  - `data/referenz-tei/` – Gold-Standard TEI-Beispiele (vormals finalized_no_header/)
  - `data/scans/` – Quelldigitalisate (vormals PDFs/)
- Trennung zwischen `knowledge/` (synthetisiertes Wissen) und `data/` (Rohdaten) dokumentiert
- Automatisierbarkeits-Spalte aus Materialanalyse entfernt (war subjektive Einschätzung ohne Quellenangabe)

**8. Wissensdokumente konsolidiert**
- Materialanalyse.md aufgeteilt in Detaildokumente:
  - [Quellenanalyse.md](Quellenanalyse.md) – Korpus, Sprachen, Pilot-Dateien
  - [TEI-Mapping.md](TEI-Mapping.md) – Transformationsregeln, Normalisierung, Elementinventar
  - [GND-Strategie.md](GND-Strategie.md) – Entitätenverknüpfung
  - [Pipeline.md](Pipeline.md) – Technische Architektur
- Inhalte aus README.md, DOCX und DTA-Basisformat in TEI-Mapping.md integriert
- Quelldokumente (README.md, DOCX) gelöscht – alle Informationen im Wissensordner

### Erkenntnisse

| Aspekt | Bewertung |
|--------|-----------|
| Transkriptionsrichtlinien | Sehr detailliert, gut dokumentiert |
| TEI-Konsistenz | Hoch, klare Muster erkennbar |
| Automatisierbarkeit Grundstruktur | Hoch |
| Automatisierbarkeit GND-Verknüpfung | Niedrig (externes System nötig) |
| Texttypen-Vielfalt | Mittel (Essays, Rezensionen, Lexikon, Interviews) |
| Sprachvielfalt | Französisch dominant, auch Deutsch |

### Offene Fragen

- [ ] Welche LLM-Kombination für OCR und Strukturierung?
- [ ] Wie wird GND-Lookup integriert?
- [ ] Qualitätsmetriken für Evaluation definieren
- [ ] Aufwandsschätzung für Offerte

### Nächste Schritte

1. **PDF-Sichtung**: Stichproben visuell prüfen (Bildqualität, Layout-Komplexität)
2. **PoC-Scope definieren**: Welche Dokumente für ersten Test?
3. **Pipeline-Prototyp**: Erste Tests mit Vision-LLM
4. **Offerte erstellen**: Basierend auf Analyseergebnissen

---

## Dokumentenregister

### Wissensdokumente (`knowledge/`)

| Dokument | Beschreibung |
|----------|--------------|
| [Materialanalyse ZBZ-OCR-TEI.md](Materialanalyse%20ZBZ-OCR-TEI.md) | Übersicht und Zusammenfassung |
| [Quellenanalyse.md](Quellenanalyse.md) | Korpus, Sprachen, Pilot-Dateien |
| [TEI-Mapping.md](TEI-Mapping.md) | Transformationsregeln, Normalisierung |
| [GND-Strategie.md](GND-Strategie.md) | Entitätenverknüpfung |
| [Pipeline.md](Pipeline.md) | Technische Architektur |
| [Workflow Diagramm Hersch.md](Workflow%20Diagramm%20Hersch.md) | Bestehender ZBZ-Prozess |
| [journal.md](journal.md) | Dieses Dokument |

### Datendokumente (`data/`)

| Ordner | Inhalt |
|--------|--------|
| `data/richtlinien/` | DTA-Basisformat (Referenz) |
| `data/projektsteuerung/` | Masterfile.xlsx |
| `data/referenz-tei/` | Gold-Standard TEI-Beispiele |
| `data/scans/` | PDF-Quelldigitalisate |

---

*Letzte Aktualisierung: 29.01.2026*
