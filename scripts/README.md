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
| `core/` | geteilte Loader | `loaders.py` (OCR/Layout-Discovery), `masterfile.py` (Masterfile/MMSID-Lookup, E69) |
| `ocr/` | Textschicht | `ocr_pipeline` (Mistral-Basis + opt-in Gemini-Vision-OCR `-e gemini`), `gemini_ocr_correct`, `llm_postprocess` (Haiku, optional E17), `classify_docs` (Gemini-Metadaten) |
| `layout/` | Layout + Export | `run_layout_analysis` (Docling lokal), `run_layout_cloud` (docling-serve), `layout_qa_gemini` (QA/Detect/Auto), `generate_layout_overlays`, `page_xml_generator` + `mets_generator` |
| `tei/` | TEI-Erzeugung | `tei_unified` (Orchestrator), `tei_step1/2/3` (Scaffold/Gemini/Assembly), `pb_split` (`<pb>`-Segmentierung, E69), `tei_generator`, `tei_mapping_prompt`, `tei_xml_utils`, `tei_validator`, `tei_add_revision`, `tei_blank_marker`, `tei_status_marker` (E66) |
| `eval/` | Qualitaet | `evaluate_ocr` (CER/WER-Engine), `eval_report` (HTML), `benchmark_cer`, `cer_statistics` + `_runner` + `_full` (BCa/Paired/HCPR), `quality_proxy`, `completeness_check`, `corpus_audit` |
| `edition/` | Frontend-Daten | `generate_edition_data` (Katalog + Mirror), `page_manifest` (Pro-Objekt-Manifest), `extract_pages` (PDF -> PNG) |

## Haeufige Einstiegspunkte

```bash
python scripts/ocr/ocr_pipeline.py -i data/source/pdf/{ID}.pdf -e mistral   # OCR
python -m scripts.layout.run_layout_analysis --doc {ID}                # Layout
python -m scripts.tei.tei_unified --doc {ID}                           # TEI (3 Stufen: Scaffold/Gemini/Assembly)
python -m scripts.tei.tei_validator --all --html-report                # Validierung
python -m scripts.eval.corpus_audit                                    # Korpus-Audit
python -m scripts.edition.generate_edition_data                        # Viewer-Daten
```

## Tests

```bash
python -m pytest tests/ -q
```

Gates pro Domaene:

- `test_cer_statistics.py` — Statistik-Primitiven (BCa/Paired/HCPR), 55 Tests
- `test_corpus_audit.py` — Korpus-Invarianten + Vollstaendigkeits-Gate, 24 Tests
- `test_cer_extraction.py` — OCR-/CER-Textextraktion
- `test_tei_schema.py` — `tei_final` gegen `zbz_hersch.rng` (E68)
- `test_tei_header.py` — teiHeader-Liefer-Vertrag (idno + biblStruct + langUsage + MMSID, E69)
- `test_tei_validator.py` — Referenz-CER in Prozent (O24/E69)
- `test_pb_split.py` — `<pb>`-Segmentierung byte-identisch (E69)
- `test_scripts_health.py` — Syntax + interne Imports aller `scripts/`

## Konventionen

- Aufruf als Modul (`python -m scripts.<paket>.<modul>`), absolute Imports
  `from scripts.<paket>.<modul> import ...`.
- Generierte Daten gehoeren nach `output/` (gitignored), nie nach `scripts/`.
- **Mit E66 entfernt:** das Agent-Screening (`tei_quality_pass`, `tei_screening_prep`,
  `screening_prompt`) -- ersetzt durch menschgesetzten Workflow-Status
  (`tei.tei_status_marker`), siehe [../knowledge/quality.md](../knowledge/quality.md).

---

*Aktualisiert: 2026-05-27 (Domaenen-Reorg: `scripts.<paket>.<modul>`)*
