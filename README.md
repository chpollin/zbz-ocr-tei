# ZBZ-OCR-TEI Pipeline

LLM-gestützte OCR- und TEI-Transformationspipeline für die Jeanne-Hersch-Edition der Zentralbibliothek Zürich.

## Projektziel

Automatisierte Verarbeitung von 289 Texten (7.200 Seiten) aus dem Nachlass von Jeanne Hersch:

```
PDF-Scans → OCR → Post-Processing → TEI-XML → GND-Verknüpfung
```

## Ordnerstruktur

```
zbz-ocr-tei/
├── knowledge/          # Projektdokumentation
│   ├── journal.md      # Arbeitsjournal (aktueller Stand)
│   ├── Projektplan.md  # Meilensteine & Aufwand
│   ├── Pipeline.md     # Technische Architektur
│   └── ...             # Weitere Docs (siehe knowledge/README.md)
│
├── scripts/            # Python-Skripte
│   ├── test_all_pdfs.py      # OCR-Tests
│   ├── evaluate_ocr.py       # CER/WER-Evaluation
│   ├── extract_gnd.py        # GND-Extraktion
│   └── postprocess/          # Text-Normalisierung
│
├── templates/          # TEI-Templates
│   └── tei_*.xml       # Für Essay, Review, Interview, Lexikon
│
├── data/               # Quelldaten (nicht versioniert)
│   ├── scans/          # PDF-Digitalisate
│   ├── referenz-tei/   # Annotierte Referenz-XMLs
│   └── richtlinien/    # ZBZ-Projektrichtlinien
│
└── output/             # Generierte Daten (nicht versioniert)
    ├── ocr_results/    # OCR-Markdown
    ├── clean/          # Post-processed Text
    └── evaluation/     # CER/WER-Reports
```

## Schnellstart

```bash
# Umgebung einrichten
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -r requirements.txt

# OCR-Tests (GPU erforderlich)
python scripts/test_all_pdfs.py --phase phase1

# Evaluation (ohne GPU)
python scripts/evaluate_ocr.py --all
```

## Aktueller Stand

| Komponente | Status |
|------------|--------|
| OCR Phase 1 (einspaltig) | 94.4% Genauigkeit |
| OCR Phase 2-4 | Blockiert (Spalten-Problem) |
| Post-Processing | Implementiert |
| TEI-Templates | 5 Templates erstellt |
| GND-Seed-Liste | 75 Entitäten extrahiert |

**Nächster Schritt:** Spalten-Problem lösen (Cloud-VM für Docling)

## Dokumentation

| Thema | Datei |
|-------|-------|
| Aktueller Stand | [knowledge/journal.md](knowledge/journal.md) |
| Projektplan | [knowledge/Projektplan.md](knowledge/Projektplan.md) |
| OCR-Testplan | [knowledge/Testplan-OCR.md](knowledge/Testplan-OCR.md) |
| TEI-Mapping | [knowledge/TEI-Mapping.md](knowledge/TEI-Mapping.md) |
| Alle Docs | [knowledge/README.md](knowledge/README.md) |

## Technologie

- **OCR:** DeepSeek-OCR-2 (3B VLM), Docling (Alternative)
- **TEI:** DTA-Basisformat mit ZBZ-Anpassungen
- **GND:** lobid.org API für Normdaten-Lookup
- **Evaluation:** CER/WER mit jiwer

## Team

Projekt der Zentralbibliothek Zürich (ZBZ) in Zusammenarbeit mit DHCraft.

---

*Stand: 29.01.2026*
