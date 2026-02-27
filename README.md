# ZBZ-OCR-TEI

LLM-gestuetzte OCR- und TEI-Pipeline fuer die Jeanne-Hersch-Edition der Zentralbibliothek Zuerich.

## Was macht dieses Repo?

Vollautomatische End-to-End-Pipeline fuer 289 Texte (7.200 Seiten) aus dem Nachlass von Jeanne Hersch:

```
PDF-Scans --> Bilder --> OCR --> Layout --> PAGE-XML --> NER/GND --> TEI-XML
              (PNG)    (Mistral)  (Docling)              (Haiku)    (DTA-Basisformat)
```

## Pilotstand (26.02.2026)

15 Pilot-Dokumente (383 Seiten) verarbeitet:

| Komponente | Status | Ergebnis |
|------------|--------|----------|
| Bildextraktion | 15/15 Docs | 383 Seitenbilder (PNG) |
| OCR (Mistral) | 15/15 Docs | CER 6.42%, Genauigkeit 93.58% |
| LLM-Nachkorrektur | 15/15 Docs | Optional (E17), Haiku 4.5 Variante C |
| Layout-Analyse | 8/15 Docs | Docling 2.75, BBox + Regionen (7 Docs brauchen GPU) |
| TEI-XML | 15/15 Docs | 383 TEI-XML Dateien (DTA-Basisformat, E22) |
| Evaluation | 15/15 Docs | CER/WER pro Seite + Dashboard |

### OCR-Qualitaet nach Dokumenttyp

| Typ | Beschreibung | Mistral CER | Genauigkeit |
|-----|-------------|-------------|-------------|
| A | Einspaltig | 9.40% | 90.60% |
| B | Zweispaltig | 6.31% | 93.69% |
| C | Monografie | 2.65% | 97.35% |
| D | Spezialformat | 2.88% | 97.12% |

### Naechste Schritte

Layout-Post-Processing (O21) → PAGE-XML-Generator (Phase 1) → NER+GND (Phase 2) → TEI erweitern (Phase 3) → Produktionslauf (289 Docs). Details: [PLAN.md](PLAN.md).

## Ordnerstruktur

```
zbz-ocr-tei/
  knowledge/              # 12 Projektdokumente (Single Source of Truth)
  scripts/                # Python-Pipeline
    config.py             # Zentrale Konfiguration
    ocr_pipeline.py       # OCR (Mistral/DeepSeek)
    llm_postprocess.py    # LLM-Nachkorrektur (Haiku 4.5)
    run_layout_analysis.py  # Layout-Analyse (Docling)
    evaluate_ocr.py       # CER/WER-Evaluation
    generate_dashboard_data.py  # Dashboard-Daten
    tei/                  # TEI-XML Generator
    postprocess/          # Deterministisches Post-Processing
  docs/                   # Dashboard + QA-Viewer
    index.html            # Dashboard: Metriken, Dokumentkatalog, CER-Vergleich
    viewer.html           # 3-Panel Viewer: Faksimile + OCR + TEI
    tei-viewer.js         # TEI-Rendering: Gerenderte Ansicht, Diff, Entities
    shared.css / shared.js  # Design System + Shared Utilities
    data/dashboard.json   # Generierte Datenbasis
  data/                   # Quelldaten (nicht versioniert)
    scans/                # 286 PDF-Digitalisate
    referenz-tei/         # 25 Referenz-TEI (ZBZ-annotiert)
    page-xml-transkribus/ # 24 Transkribus-Exporte (PAGE-XML)
  output/                 # Generierte Daten (nicht versioniert)
  PLAN.md                 # Implementierungsplan (Phasen 0-5)
  .env.example            # Vorlage fuer API-Keys
```

## Schnellstart

```bash
# Umgebung einrichten
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -r requirements.txt

# API-Keys konfigurieren
cp .env.example .env
# Werte in .env eintragen (Mistral, Anthropic)

# OCR mit Mistral (ohne GPU)
python -m scripts.ocr_pipeline -i data/scans/2310.pdf -e mistral

# Layout-Analyse (GPU fuer Docling)
python -m scripts.run_layout_analysis --doc 2310

# TEI-XML generieren (ohne GPU)
python -m scripts.tei.tei_generator --doc 2310

# Evaluation (ohne GPU)
python scripts/evaluate_ocr.py --all

# Dashboard-Daten generieren
python -m scripts.generate_dashboard_data
```

Vollstaendige CLI-Referenz: [knowledge/PIPELINE.md](knowledge/PIPELINE.md) §CLI-Befehle.

## OCR-Engines

| Engine | Zugang | Einsatz |
|--------|--------|---------|
| Mistral Document AI 2512 | Azure AI Foundry | Produktions-OCR |
| DeepSeek-OCR-2 | Lokal (GPU) | Entwicklung |
| Claude Haiku 4.5 | Anthropic API | LLM-Nachkorrektur (optional) |
| Docling 2.75 | Lokal (CPU/GPU) | Layout-Analyse (BBox + Regionen) |

## Dashboard + Viewer

Das QA-Dashboard (`docs/index.html`) zeigt Pipeline-Status, CER-Vergleich und filterbaren Dokumentkatalog. Der Viewer (`docs/viewer.html`) bietet:

- **3-Panel Layout:** Faksimile + OCR-Text + TEI-XML nebeneinander
- **TEI-Viewer:** Gerenderte Ansicht, XML mit Syntax-Highlighting, Referenz-Diff
- **Entity-Sidebar:** Personen/Organisationen/Werke mit GND-Links
- **Layout-Overlay:** SVG-BBox-Visualisierung ueber dem Faksimile
- **Keyboard-Shortcuts:** 1/2/3 (OCR-Source), T (TEI), L (Layout), R/X/V (TEI-Modus), E (Entities)

## Dokumentation

| Thema | Datei |
|-------|-------|
| **Navigation (Start hier)** | [knowledge/INDEX.md](knowledge/INDEX.md) |
| Projekt + Meilensteine | [knowledge/PROJEKT.md](knowledge/PROJEKT.md) |
| Pipeline (7 Stufen) | [knowledge/PIPELINE.md](knowledge/PIPELINE.md) |
| Implementierungsplan | [PLAN.md](PLAN.md) |
| Entscheidungen + Offenes | [knowledge/DECISIONS.md](knowledge/DECISIONS.md) |
| Testplan + Ergebnisse | [knowledge/TESTPLAN.md](knowledge/TESTPLAN.md) |
| TEI-Regeln | [knowledge/TEI-MAPPING.md](knowledge/TEI-MAPPING.md) |
| OCR-Engines | [knowledge/OCR-ENGINES.md](knowledge/OCR-ENGINES.md) |
| Arbeitsjournal | [knowledge/JOURNAL.md](knowledge/JOURNAL.md) |

## Team

Projekt der Zentralbibliothek Zuerich (ZBZ) in Zusammenarbeit mit DHCraft.

---

*Stand: 27.02.2026*
