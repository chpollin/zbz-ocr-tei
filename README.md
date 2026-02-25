# ZBZ-OCR-TEI

LLM-gestuetzte OCR- und TEI-Pipeline fuer die Jeanne-Hersch-Edition der Zentralbibliothek Zuerich.

## Was macht dieses Repo?

Vollautomatische End-to-End-Pipeline fuer 289 Texte (7.200 Seiten) aus dem Nachlass von Jeanne Hersch:

```
PDF-Scans --> Bilder --> OCR --> Layout --> PAGE-XML --> NER/GND --> TEI-XML
              (PNG)    (Mistral)  (Docling)              (Haiku)    (DTA-Basisformat)
```

**Scope:** Volle Pipeline PDF zu TEI-XML (OCR + Layout + PAGE-XML + NER/GND + TEI-Transformation).

## Ordnerstruktur

```
zbz-ocr-tei/
  knowledge/          # 12 Projektdokumente (Single Source of Truth)
  scripts/            # Python-Skripte (OCR, Layout, TEI, Evaluation)
    config.py         # Zentrale Konfiguration
    ocr_pipeline.py   # OCR mit Mistral/DeepSeek
    llm_postprocess.py  # LLM-Nachkorrektur (Haiku 4.5)
    run_layout_analysis.py  # Layout-Analyse (Docling)
    evaluate_ocr.py   # CER/WER-Evaluation
    tei/              # TEI-XML Generator
    postprocess/      # Deterministisches Post-Processing
  data/               # Quelldaten (nicht versioniert)
    scans/            # PDF-Digitalisate
    referenz-tei/     # Referenz-TEI fuer Evaluation
  output/             # Generierte Daten (nicht versioniert)
  docs/               # Benchmark-UI, QS-Viewer
  .env.example        # Vorlage fuer API-Keys
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

# OCR mit Mistral (ohne GPU, braucht .env)
python -m scripts.ocr_pipeline -i data/scans/2310.pdf -e mistral

# LLM-Nachkorrektur (braucht ANTHROPIC_API_KEY)
python -m scripts.llm_postprocess --phase phase1

# Evaluation (ohne GPU)
python -m scripts.evaluate_ocr --all
```

## OCR-Qualitaet

| Engine | Phase 1-3 (10 Docs) | Genauigkeit |
|--------|---------------------|-------------|
| Mistral Document AI | CER 5.87% | 94.14% |
| + LLM-Korrektur (Haiku 4.5) | CER 5.55% | 94.45% |

## OCR-Engines

| Engine | Zugang | Einsatz |
|--------|--------|---------|
| Mistral Document AI 2512 | Azure AI Foundry | Produktions-Engine |
| DeepSeek-OCR-2 | Lokal (GPU) | Entwicklung |
| Claude Haiku 4.5 | Anthropic API | LLM-Nachkorrektur |

## Dokumentation

| Thema | Datei |
|-------|-------|
| Aktueller Stand | [knowledge/JOURNAL.md](knowledge/JOURNAL.md) |
| Pipeline | [knowledge/PIPELINE.md](knowledge/PIPELINE.md) |
| OCR-Engines | [knowledge/OCR-ENGINES.md](knowledge/OCR-ENGINES.md) |
| Testplan & Ergebnisse | [knowledge/TESTPLAN.md](knowledge/TESTPLAN.md) |
| Dashboard & QA-Viewer | [docs/index.html](docs/index.html) |
| Alle Docs (Index) | [knowledge/INDEX.md](knowledge/INDEX.md) |

## Team

Projekt der Zentralbibliothek Zuerich (ZBZ) in Zusammenarbeit mit DHCraft.

---

*Stand: 25.02.2026*
