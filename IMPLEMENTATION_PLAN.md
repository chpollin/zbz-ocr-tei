# Implementationsplan: Repository-Refactoring

Erstellt: 2026-03-07 | Basiert auf: REFACTORING_PLAN.md

---

## Uebersicht

8 Milestones, sequenziell abarbeitbar. Jeder Milestone hat ein klares Abnahmekriterium.

```
M1  Test-Baseline          ████  Sicherheitsnetz schaffen
M2  Config entflechten      ██  Daten raus aus Code
M3  Shared Infra (DRY)     ███  Gemini-Client + dotenv + CLI
M4  Modul-Reorganisation  █████  Pipeline-Struktur im Dateisystem
M5  God-Files aufbrechen   ████  4 Dateien >800 LOC splitten
M6  Fehlerbehandlung        ██  Silent exceptions eliminieren
M7  Frontend aufraemen     ███  CSS splitten, JS konsolidieren
M8  Dokumentation           █  Knowledge-Base + CLAUDE.md aktualisieren
```

---

## M1: Test-Baseline

**Ziel:** Regressionstests, die beweisen, dass spaetere Aenderungen den Output nicht veraendern.

### Aufgaben

| # | Aufgabe | Dateien | Pruefung |
|---|---------|---------|----------|
| 1.1 | `tests/` Verzeichnis + `conftest.py` anlegen | `tests/__init__.py`, `tests/conftest.py` | `pytest --collect-only` findet 0 Fehler |
| 1.2 | `test_config.py`: Pfade konsistent, Konstanten nicht leer | `tests/test_config.py` | pytest gruen |
| 1.3 | `test_utils.py`: `load_json`, `write_json`, `extract_page_num`, `discover_doc_ids` | `tests/test_utils.py` | pytest gruen |
| 1.4 | `test_tei_inline.py`: `md_to_tei_inline`, `split_paragraphs`, `annotate_entities` | `tests/test_tei_inline.py` | pytest gruen |
| 1.5 | `test_postprocess.py`: `normalize_text`, `dehyphenate`, `clean_markdown` | `tests/test_postprocess.py` | pytest gruen |

### Abnahmekriterium
```bash
pytest tests/ -v   # >= 20 Tests, alle gruen
```

### Nicht enthalten
- Golden-File-Tests (brauchen Pipeline-Output, der nicht im Repo liegt)
- API-abhaengige Tests (Gemini, Anthropic)

---

## M2: Config entflechten

**Ziel:** `config.py` enthaelt nur Code-Konfiguration. Daten liegen in JSON-Dateien.

### Aufgaben

| # | Aufgabe | Vorher | Nachher |
|---|---------|--------|---------|
| 2.1 | TESTPLAN nach JSON | `config.py:128-164` (36 LOC Python-Dict) | `data/testplan.json` + 1 Zeile Loader in `config.py` |
| 2.2 | KNOWN_ENTITIES nach JSON | `config.py:167-179` (13 LOC Python-Dict) | `data/known_entities.json` + 1 Zeile Loader |
| 2.3 | `config.py` in Sektionen ordnen | Unsortiert, 189 LOC | Kommentarsektionen: Pfade / TEI / OCR / Layout |

### Abnahmekriterium
```bash
pytest tests/test_config.py -v           # Alle config-Tests gruen
python -c "from scripts.config import TESTPLAN; print(len(TESTPLAN))"  # 4 Phasen
python -c "from scripts.config import KNOWN_ENTITIES; print(len(KNOWN_ENTITIES))"  # 11 Entities
```

### Betroffene Imports (keine Aenderung noetig)
Alle bestehenden `from scripts.config import TESTPLAN` funktionieren weiter -- nur die Datenquelle aendert sich.

---

## M3: Shared Infra (DRY)

**Ziel:** Gemini-Client, dotenv-Loading und CLI-Argumente existieren nur noch einmal.

### Aufgaben

| # | Aufgabe | Eliminiert | Neue Datei |
|---|---------|-----------|------------|
| 3.1 | `gemini_client.py`: `get_client()` + `call_gemini()` | 4x API-Key-Loading, 4x Retry-Logik, 3x warnings.filterwarnings | `scripts/gemini_client.py` |
| 3.2 | `utils.py`: `load_env()` um dotenv erweitern | 6x `from dotenv import load_dotenv; load_dotenv()` | `scripts/utils.py` (erweitert) |
| 3.3 | `cli.py`: `add_doc_args()` + `resolve_doc_ids()` | 10x identische argparse-Bloecke | `scripts/cli.py` |
| 3.4 | Alle Scripts auf shared Infra umstellen | Boilerplate in jedem Script | 6 Dateien anpassen |

### Detailplan 3.1 -- gemini_client.py

```python
# scripts/gemini_client.py
"""Zentraler Gemini-API-Client."""

def get_client() -> genai.Client:
    """API-Key aus Environment, klare Fehlermeldung wenn fehlend."""

def call_gemini(client, model, contents, config=None, retries=3, base_delay=15):
    """API-Call mit Rate-Limit-Retry und spezifischem Exception-Handling."""
```

**Umzustellende Dateien:**
1. `scripts/gemini_ocr_correct.py` -- Zeilen 38-39, 56-57 entfallen
2. `scripts/layout_qa_gemini.py` -- Zeilen 29, 42, 44-45 entfallen
3. `scripts/tei/tei_gemini.py` -- Zeilen 28, 43-44 entfallen
4. `scripts/tei/tei_unified.py` -- Zeilen 32-34, 53 entfallen

### Detailplan 3.3 -- cli.py

```python
# scripts/cli.py
"""Shared CLI-Argumente fuer Pipeline-Scripts."""

def add_doc_args(parser):
    """--doc, --sample, --all, --phase, --force, --dry-run"""

def resolve_doc_ids(args, sample_ids=None, discover_fn=None) -> list[str]:
    """Einheitliche Aufloesung von Doc-IDs aus CLI-Argumenten."""
```

### Abnahmekriterium
```bash
pytest tests/ -v                                    # Bestehende Tests gruen
python -c "from scripts.gemini_client import get_client, call_gemini"  # Import OK
python -c "from scripts.cli import add_doc_args, resolve_doc_ids"      # Import OK
grep -r "load_dotenv()" scripts/ | wc -l            # 0 (nur noch in utils.py)
grep -r "sys.path.insert" scripts/ | wc -l          # noch 6 (werden in M4 entfernt)
```

---

## M4: Modul-Reorganisation

**Ziel:** `scripts/` spiegelt die 7-Stage-Pipeline wider. Jedes Script liegt im richtigen Submodul.

### Aufgaben

| # | Script (alt) | Modul (neu) | Aktion |
|---|-------------|-------------|--------|
| 4.1 | `ocr_pipeline.py` | `scripts/ocr/pipeline.py` | git mv + Imports anpassen |
| 4.2 | `gemini_ocr_correct.py` | `scripts/ocr/gemini_correct.py` | git mv + Imports |
| 4.3 | `llm_postprocess.py` | `scripts/ocr/llm_postprocess.py` | git mv + Imports |
| 4.4 | `extract_pages.py` | `scripts/ocr/extract_pages.py` | git mv + Imports |
| 4.5 | `run_layout_analysis.py` | `scripts/layout/analysis.py` | git mv + Imports |
| 4.6 | `run_layout_cloud.py` | `scripts/layout/cloud.py` | git mv + Imports |
| 4.7 | `layout_qa_gemini.py` | `scripts/layout/qa_gemini.py` | git mv + Imports |
| 4.8 | `generate_layout_overlays.py` | `scripts/layout/overlays.py` | git mv + Imports |
| 4.9 | `evaluate_ocr.py` | `scripts/eval/evaluate.py` | git mv + Imports |
| 4.10 | `generate_dashboard_data.py` | `scripts/eval/dashboard.py` | git mv + Imports |
| 4.11 | `test_all_pdfs.py` | `scripts/eval/test_pdfs.py` | git mv + Imports |
| 4.12 | `classify_docs.py` | `scripts/metadata/classify.py` | git mv + Imports |
| 4.13 | `extract_gnd.py` | `scripts/metadata/extract_gnd.py` | git mv + Imports |
| 4.14 | `generate_edition_data.py` | `scripts/metadata/edition.py` | git mv + Imports |
| 4.15 | `tei_*.py` Prefixe entfernen | `scripts/tei/{generator,unified,gemini,validator,mapping_prompt}.py` | git mv |
| 4.16 | `__init__.py` fuer neue Module | `scripts/ocr/__init__.py`, `scripts/eval/__init__.py`, `scripts/metadata/__init__.py` | Neu anlegen |
| 4.17 | `sys.path.insert` entfernen | 6 Dateien | Zeilen loeschen |
| 4.18 | Cross-Module-Imports aktualisieren | Alle Dateien die `from scripts.layout_qa_gemini` etc. importieren | grep + fix |

### Import-Mapping (vollstaendig)

```
from scripts.ocr_pipeline       -> from scripts.ocr.pipeline
from scripts.gemini_ocr_correct -> from scripts.ocr.gemini_correct
from scripts.llm_postprocess    -> from scripts.ocr.llm_postprocess
from scripts.layout_qa_gemini   -> from scripts.layout.qa_gemini
from scripts.evaluate_ocr       -> from scripts.eval.evaluate
from scripts.classify_docs      -> from scripts.metadata.classify
from scripts.extract_gnd        -> from scripts.metadata.extract_gnd
from scripts.generate_dashboard_data -> from scripts.eval.dashboard
from scripts.generate_edition_data   -> from scripts.metadata.edition
from scripts.generate_layout_overlays -> from scripts.layout.overlays
from scripts.run_layout_analysis -> from scripts.layout.analysis
from scripts.run_layout_cloud    -> from scripts.layout.cloud
from scripts.extract_pages       -> from scripts.ocr.extract_pages
from scripts.test_all_pdfs       -> from scripts.eval.test_pdfs
from scripts.tei.tei_generator   -> from scripts.tei.generator
from scripts.tei.tei_unified     -> from scripts.tei.unified
from scripts.tei.tei_gemini      -> from scripts.tei.gemini
from scripts.tei.tei_validator   -> from scripts.tei.validator
from scripts.tei.tei_mapping_prompt -> from scripts.tei.mapping_prompt
```

### CLI-Mapping

```bash
# Alt                                    -> Neu
python -m scripts.gemini_ocr_correct     -> python -m scripts.ocr.gemini_correct
python -m scripts.llm_postprocess        -> python -m scripts.ocr.llm_postprocess
python -m scripts.run_layout_analysis    -> python -m scripts.layout.analysis
python -m scripts.run_layout_cloud       -> python -m scripts.layout.cloud
python -m scripts.layout_qa_gemini       -> python -m scripts.layout.qa_gemini
python -m scripts.generate_layout_overlays -> python -m scripts.layout.overlays
python -m scripts.tei.tei_generator      -> python -m scripts.tei.generator
python -m scripts.tei.tei_unified        -> python -m scripts.tei.unified
python -m scripts.tei.tei_gemini         -> python -m scripts.tei.gemini
python -m scripts.tei.tei_validator      -> python -m scripts.tei.validator
python scripts/evaluate_ocr.py           -> python -m scripts.eval.evaluate
python -m scripts.generate_dashboard_data -> python -m scripts.eval.dashboard
python -m scripts.classify_docs          -> python -m scripts.metadata.classify
python -m scripts.generate_edition_data  -> python -m scripts.metadata.edition
```

### Abnahmekriterium
```bash
pytest tests/ -v                                     # Alle Tests gruen
ls scripts/*.py | grep -v config | grep -v utils | grep -v cli | grep -v gemini_client  # Nur 4 Dateien
find scripts/ -name "__init__.py" | wc -l            # >= 7
grep -r "sys.path.insert" scripts/ | wc -l           # 0
python -m scripts.tei.unified --help                 # CLI funktioniert
python -m scripts.eval.evaluate --help               # CLI funktioniert
python -m scripts.ocr.gemini_correct --help          # CLI funktioniert
```

---

## M5: God-Files aufbrechen

**Ziel:** Keine Datei ueber 600 LOC. Klare Verantwortlichkeiten pro Modul.

### Aufgaben

| # | Datei (LOC) | Extraktion | Neue Datei (LOC) | Restgroesse |
|---|-------------|-----------|-----------------|-------------|
| 5.1 | `eval/evaluate.py` (1017) | `extract_text_from_tei`, `extract_pages_from_tei`, `normalize_text` | `eval/text_extraction.py` (~140) | ~880 |
| 5.2 | `eval/evaluate.py` (880) | `generate_report` (HTML-Generierung) | `eval/html_report.py` (~350) | ~530 |
| 5.3 | `layout/qa_gemini.py` (823) | Prompt-Hints + `build_doc_hints` + `infer_genre` | `layout/prompts.py` (~200) | ~620 |
| 5.4 | `layout/qa_gemini.py` (620) | `ensure_overlay()` | `layout/overlays.py` (erweitern, ~50) | ~570 |
| 5.5 | `tei/unified.py` (1230) | `process_page_step1` -> `_compute_facsimile_zones` + `_build_tei_body` extrahieren | Selbe Datei, aufgeteilt | ~1100 |
| 5.6 | `tei/unified.py` (1100) | `_is_interview_turn()` auf Modulebene | Selbe Datei | ~1080 |

### Abnahmekriterium
```bash
wc -l scripts/eval/evaluate.py          # <= 550
wc -l scripts/layout/qa_gemini.py       # <= 600
wc -l scripts/tei/unified.py            # <= 1100
pytest tests/ -v                        # Alle Tests gruen
```

---

## M6: Fehlerbehandlung

**Ziel:** Keine `except Exception: pass` mehr. Einheitliche Log-Praefixe.

### Aufgaben

| # | Aufgabe | Datei | Aenderung |
|---|---------|-------|-----------|
| 6.1 | `except Exception: pass` -> spezifisch + log | `layout/qa_gemini.py:55` | `except (json.JSONDecodeError, OSError) as e: print(f"  WARNUNG: {e}")` |
| 6.2 | Gemini-Fehler differenzieren | `tei/gemini.py` | Auth-Fehler -> Abbruch, Rate-Limit -> Retry, Parse -> Fallback |
| 6.3 | lxml-Import aufraemen | `tei/validator.py` | Top-Level-Import mit try/except |
| 6.4 | Log-Praefixe vereinheitlichen | Alle Scripts | `OK:` / `WARNUNG:` / `FEHLER:` / `SKIP:` |

### Abnahmekriterium
```bash
grep -r "except Exception:" scripts/ | grep "pass" | wc -l   # 0
grep -r "except Exception:" scripts/ | wc -l                 # 0 oder nur mit Logging
pytest tests/ -v                                              # Alle Tests gruen
```

---

## M7: Frontend aufraemen

**Ziel:** CSS modularisiert, JS konsolidiert.

### Aufgaben

| # | Aufgabe | Vorher | Nachher |
|---|---------|--------|---------|
| 7.1 | CSS-Variablen extrahieren | `shared.css` Zeile 1-60 | `docs/css/variables.css` |
| 7.2 | Base-Styles extrahieren | `shared.css` Reset + Typography | `docs/css/base.css` |
| 7.3 | Komponenten-Styles extrahieren | `shared.css` Cards/Tabs/Badges | `docs/css/components.css` |
| 7.4 | View-spezifische Styles extrahieren | `shared.css` Viewer/Dashboard/Benchmark | `docs/css/dashboard.css`, `docs/css/viewer.css` |
| 7.5 | `shared.css` als Aggregator | 34KB Monolith | `@import` Aggregator (~10 Zeilen) |
| 7.6 | HTML-Dateien aktualisieren | `<link href="shared.css">` | Bleibt gleich (Aggregator) |

### Abnahmekriterium
```
docs/index.html     # Laedt korrekt im Browser
docs/viewer.html    # Laedt korrekt im Browser
docs/benchmark.html # Laedt korrekt im Browser
wc -l docs/css/*.css | tail -1  # ~900 Zeilen total (statt 900 in einer Datei)
```

---

## M8: Dokumentation

**Ziel:** Knowledge-Base und CLAUDE.md spiegeln die neue Struktur wider.

### Aufgaben

| # | Aufgabe | Datei |
|---|---------|-------|
| 8.1 | CLI-Referenz aktualisieren | `knowledge/PIPELINE.md` |
| 8.2 | Verzeichnisstruktur aktualisieren | `knowledge/INDEX.md` |
| 8.3 | CLAUDE.md Commands-Sektion aktualisieren | `CLAUDE.md` |
| 8.4 | JOURNAL.md Session-Eintrag | `knowledge/JOURNAL.md` |
| 8.5 | README.md Quick-Start aktualisieren | `README.md` |
| 8.6 | Alten REFACTORING_PLAN.md archivieren | Umbenennen oder Status "Abgeschlossen" |

### Abnahmekriterium
```bash
grep "scripts.tei.tei_unified" knowledge/PIPELINE.md | wc -l   # 0 (alter Pfad)
grep "scripts.tei.unified" knowledge/PIPELINE.md | wc -l       # >= 1 (neuer Pfad)
```

---

## Abhaengigkeitsgraph

```
M1 (Tests)
 |
 +---> M2 (Config) --------+
 |                          |
 +---> M3 (Shared Infra) --+---> M4 (Reorganisation) ---> M5 (God-Files) ---> M6 (Fehler)
 |                          |
 +---> M7 (Frontend) ------+---> M8 (Dokumentation)
```

**Kritischer Pfad:** M1 -> M3 -> M4 -> M5 -> M6 -> M8
**Parallel moeglich:** M2 || M3 || M7 (alle nach M1)

---

## Risikomatrix

| Milestone | Risiko | Mitigation |
|-----------|--------|------------|
| M1 Tests | Niedrig | Nur neue Dateien, kein bestehender Code betroffen |
| M2 Config | Niedrig | Interface bleibt gleich, nur Datenquelle aendert sich |
| M3 Shared Infra | Mittel | Gemini-Client muss alle 4 Varianten abdecken |
| M4 Reorganisation | **Hoch** | Bricht alle Imports + CLI-Pfade. Tests aus M1 als Sicherheitsnetz |
| M5 God-Files | Mittel | Funktions-Grenzen muessen sauber sein |
| M6 Fehler | Niedrig | Kleine, isolierte Aenderungen |
| M7 Frontend | Niedrig | CSS @import ist abwaertskompatibel |
| M8 Doku | Niedrig | Keine Code-Aenderungen |

---

## Commit-Strategie

Ein Commit pro abgeschlossener Aufgabe (nicht pro Milestone). Beispiel fuer M4:

```
git commit -m "M4.1: ocr_pipeline.py -> scripts/ocr/pipeline.py"
git commit -m "M4.2: gemini_ocr_correct.py -> scripts/ocr/gemini_correct.py"
...
git commit -m "M4.17: sys.path.insert entfernt (6 Dateien)"
git commit -m "M4.18: Cross-Module-Imports aktualisiert"
```

Vorteil: Jeder Commit ist einzeln revertierbar.
