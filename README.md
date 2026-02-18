# ZBZ-OCR-TEI

LLM-gestuetzte OCR-Pipeline fuer die Jeanne-Hersch-Edition der Zentralbibliothek Zuerich.

## Was macht dieses Repo?

Automatisierte OCR-Verarbeitung von 289 Texten (7.200 Seiten) aus dem Nachlass von Jeanne Hersch:

```
PDF-Scans --> Layout-Analyse --> OCR --> LLM-Korrektur --> Post-Processing --> Markdown + Bilder
                                                                                    |
                                                                                    v
                                                                          coOCR/HTR (Korrektur)
                                                                                    |
                                                                                    v
                                                                          teiCrafter (TEI + GND)
```

**Scope:** PDF zu korrigiertem Markdown. TEI-Transformation und GND-Verknuepfung finden downstream in [coOCR/HTR](https://github.com/DHCraft/co-ocr-htr) und [teiCrafter](https://github.com/DHCraft/teiCrafter) statt.

## Ordnerstruktur

```
zbz-ocr-tei/
  knowledge/          # 12 Projektdokumente (Single Source of Truth)
  scripts/            # Python-Skripte (OCR, Evaluation, Post-Processing)
    config.py         # Zentrale Konfiguration
    ocr_pipeline.py   # OCR mit Mistral/DeepSeek
    llm_postprocess.py  # LLM-Nachkorrektur (Haiku 4.5)
    evaluate_ocr.py   # CER/WER-Evaluation
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
| Aktueller Stand | [knowledge/journal.md](knowledge/journal.md) |
| Architektur | [knowledge/ARCHITEKTUR.md](knowledge/ARCHITEKTUR.md) |
| OCR-Engines | [knowledge/OCR-ENGINES.md](knowledge/OCR-ENGINES.md) |
| Testplan & Ergebnisse | [knowledge/TESTPLAN.md](knowledge/TESTPLAN.md) |
| Alle Docs (Index) | [knowledge/INDEX.md](knowledge/INDEX.md) |

## Team

Projekt der Zentralbibliothek Zuerich (ZBZ) in Zusammenarbeit mit DHCraft.

---

*Stand: 19.02.2026*
