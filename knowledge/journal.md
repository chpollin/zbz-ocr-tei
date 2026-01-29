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
  - [Pipeline.md](Pipeline.md) – Technische Architektur, Risikoanalyse
- Inhalte aus README.md, DOCX und DTA-Basisformat in TEI-Mapping.md integriert
- Quelldokumente (README.md, DOCX) gelöscht – alle Informationen im Wissensordner
- Materialanalyse.md entfernt – Inhalte vollständig in Detaildokumente überführt

**9. OCR-Tool-Dokumentation erstellt**
- [DeepSeek-OCR-2-Setup.md](DeepSeek-OCR-2-Setup.md) – Lokale GPU-Installation
- [Docling-Setup.md](Docling-Setup.md) – Lokale GPU-Installation

**10. DeepSeek-OCR-2 Installation und erster Test**
- Python venv mit PyTorch CUDA 12.4 eingerichtet
- DeepSeek-OCR-2 Modell (3B Parameter) geladen
- Testskript `scripts/test_deepseek_ocr.py` erstellt
- Erster Test mit 2530.pdf (2 Seiten, französisch)
- **Ergebnis:** Texterkennung sehr gut (>99%), aber **Spalten-Lesereihenfolge falsch** bei zweispaltigem Layout

**11. Layout-Analyse aller 15 Pilot-PDFs**
- Erste 2 Seiten von allen PDFs extrahiert (`output/layout_samples/`)
- Visuelle Analyse durchgeführt
- 4 Dokumenttypen identifiziert:
  - **Typ A (einspaltig):** 2310, 1180, 130, 290, 1410, 1060 – Standard-OCR funktioniert
  - **Typ B (zweispaltig):** 2530, 890, 3040, 1440 – Layout-Problem identifiziert
  - **Typ C (Monografien):** 40, 1520 – Viele Seiten, Chunking nötig
  - **Typ D (Spezial):** 90, 830, 1330 – Historischer Druck, Bildband, etc.

**12. Testplan erstellt**
- [Testplan-OCR.md](Testplan-OCR.md) – Systematische Evaluation aller Dokumenttypen
- 4 Testphasen definiert: Baseline → Zweispaltig → Spezial → Monografien
- Lösungsansätze für Spalten-Problem dokumentiert

**13. Testskript für alle Dokumenttypen**
- `scripts/test_all_pdfs.py` – Automatisierte Tests gemäß Testplan
- Unterstützt phasenweises Testen (`--phase phase1/phase2/phase3/phase4/all`)
- Speichert Ergebnisse als JSON in `output/evaluation/`
- `.gitignore` erweitert um Python-Artefakte, Output, Claude-Konfiguration

### Erkenntnisse

| Aspekt | Bewertung |
|--------|-----------|
| Transkriptionsrichtlinien | Sehr detailliert, gut dokumentiert |
| TEI-Konsistenz | Hoch, klare Muster erkennbar |
| Automatisierbarkeit Grundstruktur | Hoch |
| Automatisierbarkeit GND-Verknüpfung | Niedrig (externes System nötig) |
| Texttypen-Vielfalt | Mittel (Essays, Rezensionen, Lexikon, Interviews) |
| Sprachvielfalt | Französisch dominant, auch Deutsch |

### Offene Analysen

- [x] PDF-Scans visuell analysieren (Layouts, Qualität) ✅
- [ ] GND-IDs aus Referenz-TEI extrahieren
- [ ] Konkrete TEI-Beispiele für Randfälle dokumentieren
- [x] OCR-Qualität von DeepSeek-OCR-2 testen (erster Test) ✅

### Offene Fragen

- [ ] Wie lösen wir das Spalten-Problem bei Typ B?
- [ ] Docling als Alternative für Layout-Analyse?
- [ ] Wie wird GND-Lookup integriert?
- [ ] Aufwandsschätzung für Offerte

### Nächste Schritte

1. **Testplan Phase 1 durchführen**: Baseline-Tests für einspaltige Dokumente
2. **Spalten-Problem lösen**: Prompt-Varianten oder Docling testen
3. **Evaluationsmatrix ausfüllen**: Qualitätsmetriken pro Dokumenttyp
4. **Produktions-Pipeline ableiten**: Basierend auf Testergebnissen

---

## Dokumentenregister

### Wissensdokumente (`knowledge/`)

| Dokument | Beschreibung |
|----------|--------------|
| [Quellenanalyse.md](Quellenanalyse.md) | Korpus, Sprachen, Pilot-Dateien |
| [TEI-Mapping.md](TEI-Mapping.md) | Transformationsregeln, Normalisierung |
| [GND-Strategie.md](GND-Strategie.md) | Entitätenverknüpfung |
| [Pipeline.md](Pipeline.md) | Technische Architektur, Risikoanalyse |
| [Workflow Diagramm Hersch.md](Workflow%20Diagramm%20Hersch.md) | Bestehender ZBZ-Prozess |
| [DeepSeek-OCR-2-Setup.md](DeepSeek-OCR-2-Setup.md) | Lokale Installation DeepSeek-OCR-2 |
| [Docling-Setup.md](Docling-Setup.md) | Lokale Installation Docling |
| [Testplan-OCR.md](Testplan-OCR.md) | Systematischer OCR-Testplan |
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
