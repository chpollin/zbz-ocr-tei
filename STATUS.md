# Status -- ZBZ-OCR-TEI

Letzte Aktualisierung: 2026-02-25, 20:00

## Abgeschlossen

- M0: Bildextraktion + QS-Viewer -- 383 Seitenbilder aus 15 Pilot-PDFs
- M1: OCR-Validierung -- 15 Dokumente evaluiert, Mistral CER 6,42%, LLM-Nachkorrektur CER 6,52%
- LLM-Nachkorrektur: 3 Varianten getestet (A/B/C), Variante C (Few-Shot) als Default
- Dashboard: Multi-Page Static UI mit Engine-Badges, CER-Vergleich, Viewer
- E19: Layout-Analyse-Recherche -- Docling + Gemini Hybrid empfohlen
- **E20: Phase 0 Docling-Evaluation bestanden** -- alle 4 Dokumenttypen korrekt, Spalten-Trennung Type B funktioniert
- Knowledge-Base: 13 Dokumente, alle aktuell (Scope-Erweiterung eingearbeitet)

## Aktuell laufend

- Phase 1: Layout + PAGE-XML implementieren
  - `scripts/layout/` Modul bauen (layout_analyzer, region_classifier, page_xml_generator, mets_generator)
  - `scripts/export_page_xml.py` -- **Deliverable fuer M2**

## Naechste Phasen

| Phase | Beschreibung | Status |
|-------|-------------|--------|
| Phase 1 | Layout + PAGE-XML-Generator | **Naechster Schritt** |
| Phase 2 | NER + GND-Verknuepfung | Ausstehend |
| Phase 3 | TEI-XML-Generator | Ausstehend |
| Phase 4 | Erweiterte Evaluation + Dashboard | Ausstehend |
| Phase 5 | Produktionslauf (289 Docs) | Ausstehend |

## Docling Phase 0 Evaluation (25.02.2026)

| Doc | Typ | Regionen | Zeit | Ergebnis |
|-----|-----|----------|------|----------|
| 1180 | A (einspaltig) | 9 | 3.3s | 2 headings, 7 text -- korrekt |
| 2530 | B (zweispaltig) | 12 | 2.5s | Spalten korrekt getrennt (L: x120-529, R: x560-969) |
| 40 | C (Monografie) | 3-6 | 0.4s | Textseiten korrekt, Bildseiten als picture |
| 90 | D (Historisch) | 6 | 0.5s | Titelseite korrekt erkannt |
| 1330 | D (Sammelband) | 14 | 0.7s | headings, text, list_items korrekt |

## OCR-Qualitaet (15 Pilotdokumente)

| Phase | Typ | Mistral CER | LLM CER | Bewertung |
|-------|-----|-------------|---------|-----------|
| 1 | A (Einspaltig) | 9,40% | 8,43% | LLM hilft |
| 2 | B (Zweispaltig) | 6,31% | 6,34% | LLM neutral |
| 3 | D (Spezial) | 2,88% | 2,72% | LLM hilft leicht |
| 4 | C (Monographie) | 2,65% | 2,70% | LLM schadet leicht |

## Blockierend

- Transkribus PAGE-XML Exportdatei von ZBZ anfordern (R7 -- Kompatibilitaet pruefen)
- Google API Key fuer Gemini (optional, nicht blockierend)
