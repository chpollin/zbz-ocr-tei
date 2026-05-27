# scripts/

Python-Pipeline der Jeanne-Hersch-Edition, nach Domaene in Subpackages gruppiert.
Alle Skripte sind von Claude Code generiert. Aufruf als Modul:
`python -m scripts.<paket>.<modul>`. Geteilte Konfiguration (`config.py`) und
Utilities (`utils.py`) liegen top-level.

CLI-Referenz mit Flags und Beispielen: [../CLAUDE.md](../CLAUDE.md) §Commands.
Pipeline-Stufen und Datenfluss: [../knowledge/pipeline.md](../knowledge/pipeline.md).

## Struktur

| Paket | Zweck | Schluessel-Module |
|---|---|---|
| *(top-level)* | geteilte Basis | `config.py` (Pfade, Modelle, Konstanten), `utils.py` |
| `core/` | geteilte Loader | `loaders.py` (OCR/Layout/Entity-Discovery) |
| `ocr/` | Textschicht | `ocr_pipeline` (Mistral/DeepSeek), `gemini_ocr_correct`, `llm_postprocess` (Haiku, optional E17), `ocr_dedup`, `classify_docs` (Gemini-Metadaten) |
| `layout/` | Layout + Export | `run_layout_analysis` (Docling lokal), `run_layout_cloud` (docling-serve), `layout_qa_gemini` (QA/Detect/Auto), `generate_layout_overlays`, `page_xml_generator` + `mets_generator` |
| `ner/` | Entitaeten | `ner_extract`, `entity_store`, `entity_index`, `wikidata_linker` (deterministisch, kein LLM-Linking), `ner_inject_tei`, `ner_evaluate` |
| `tei/` | TEI-Erzeugung | `tei_unified` (Orchestrator), `tei_step1/2/3` (Scaffold/Gemini/Assembly), `tei_generator`, `tei_mapping_prompt`, `tei_xml_utils`, `tei_validator`, `tei_add_revision`, `tei_blank_marker`, `tei_status_marker` (E66) |
| `eval/` | Qualitaet | `evaluate_ocr` (CER/WER-Engine), `eval_report` (HTML), `benchmark_cer`, `cer_statistics` + `_runner` + `_full` (BCa/Paired/HCPR), `quality_proxy`, `completeness_check`, `corpus_audit` |
| `edition/` | Frontend-Daten | `generate_edition_data` (Katalog + Mirror), `page_manifest` (Pro-Objekt-Manifest), `extract_pages` (PDF -> PNG) |

## Haeufige Einstiegspunkte

```bash
python scripts/ocr/ocr_pipeline.py -i data/source/pdf/{ID}.pdf -e mistral   # OCR
python -m scripts.layout.run_layout_analysis --doc {ID}                # Layout
python -m scripts.tei.tei_unified --doc {ID}                           # TEI (4 Stufen)
python -m scripts.tei.tei_validator --all --html-report                # Validierung
python -m scripts.eval.corpus_audit                                    # Korpus-Audit
python -m scripts.edition.generate_edition_data                        # Viewer-Daten
```

## Tests

```bash
python -m pytest tests/ -q
```

`tests/test_cer_statistics.py` (Statistik-Primitiven, 55 Tests) und
`tests/test_corpus_audit.py` (Korpus-Invarianten + Vollstaendigkeits-Gate, 22 Tests).

## Konventionen

- Aufruf als Modul (`python -m scripts.<paket>.<modul>`), absolute Imports
  `from scripts.<paket>.<modul> import ...`.
- Generierte Daten gehoeren nach `output/` (gitignored), nie nach `scripts/`.
- **Mit E66 entfernt:** das Agent-Screening (`tei_quality_pass`, `tei_screening_prep`,
  `screening_prompt`) -- ersetzt durch menschgesetzten Workflow-Status
  (`tei.tei_status_marker`), siehe [../knowledge/quality.md](../knowledge/quality.md).

---

*Aktualisiert: 2026-05-27 (Domaenen-Reorg: `scripts.<paket>.<modul>`)*
