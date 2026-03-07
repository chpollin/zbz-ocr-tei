# Refactoring-Plan: Gesamtprojekt zbz-ocr-tei

Erstellt: 2026-03-07 | Status: Entwurf
Vorgaenger: TEI-Pipeline-Refactoring (Session 15, abgeschlossen)

---

## Ehrliche Bestandsaufnahme

### Was gut funktioniert

Das Projekt hat in 15 Sessions eine beeindruckende Pipeline aufgebaut: 286 Dokumente, 7 Pipeline-Stages, multi-Engine OCR mit Gemini-Korrektur, Layout-Analyse, TEI-Generierung und ein funktionierendes Dashboard. Die Knowledge-Base ist vorbildlich strukturiert. `config.py` und `utils.py` als zentrale Module sind ein solides Fundament. Die TEI-Submodule (`tei/`, `layout/`, `postprocess/`) zeigen, dass die richtige Richtung erkannt wurde.

### Was problematisch ist

Das Projekt ist organisch gewachsen -- Session fuer Session wurden Features hinzugefuegt, ohne die Architektur regelmaessig anzupassen. Das Ergebnis ist ein System, das **funktioniert, aber schwer wartbar ist**. Konkret:

**1. Flache Script-Struktur ohne klare Verantwortung**
15 Python-Dateien liegen direkt in `scripts/` ohne erkennbare Gruppierung. Ein Entwickler, der das Projekt zum ersten Mal sieht, muss jede Datei oeffnen, um zu verstehen, welche Pipeline-Stage sie bedient. Es gibt keine Modul-Grenzen -- alles importiert alles.

**2. God-Files**
4 Dateien haben jeweils 800--1230 Zeilen:
- `tei_unified.py` (1230 LOC) -- TEI-Pipeline mit Scaffold, Gemini-Refinement, Assembly, Validation
- `evaluate_ocr.py` (1017 LOC) -- Evaluation, Metriken, HTML-Report, Dashboard-Export
- `layout_qa_gemini.py` (823 LOC) -- Gemini-QA, Detect-Mode, Overlay-Generierung, Prompt-Hints
- `gemini_ocr_correct.py` (811 LOC) -- OCR-Korrektur in 2 Schritten mit Manifest-Tracking

Jede dieser Dateien hat 2--4 verschiedene Verantwortlichkeiten, die in einer einzigen `main()` orchestriert werden.

**3. Duplizierte Infrastruktur-Patterns**
Das gleiche Boilerplate wiederholt sich in fast jedem Script:

| Pattern | Vorkommen | Problem |
|---------|-----------|---------|
| `from dotenv import load_dotenv; load_dotenv()` | 6 Dateien | Inkonsistent -- manche nutzen `utils.load_env()`, manche `dotenv` direkt |
| `sys.path.insert(0, ...)` | 6 Dateien | Hack, der noetig ist, weil kein sauberes Package existiert |
| `_api_key = os.environ.get("GEMINI_API_KEY", "") or GEMINI_API_KEY` | 4 Dateien | Copy-paste, inkonsistente API-Key-Aufloesung |
| `warnings.filterwarnings("ignore", ...)` | 3 Dateien | Identischer Code |
| `argparse` mit `--doc`, `--sample`, `--all`, `--force`, `--dry-run` | 10+ Dateien | Identische CLI-Argumente, unterschiedlich implementiert |

**4. config.py ist eine Muellhalde**
189 Zeilen, die voellig unterschiedliche Dinge mischen:
- Pfad-Konstanten (sinnvoll)
- OCR-Modellnamen und Prompts
- Testplan-Daten (129--164) -- gehoeren in eine Datendatei
- Entity-Daten (`KNOWN_ENTITIES`) -- gehoeren in eine Datendatei
- Farbkonstanten fuer Overlay-Rendering
- Dokumenttyp-Mappings

**5. Frontend ohne Struktur**
`docs/` enthaelt:
- `shared.css` (34.634 Bytes!) -- ein einziges, monolithisches CSS
- `shared.js` (14.375 Bytes) -- Utility-Namespace
- 5 weitere JS-Dateien (dashboard, benchmark, viewer, page-viewer, tei-viewer)
- `edition/` als separate App mit eigenem CSS/JS
- Alles flach im selben Verzeichnis

**6. Keine Tests**
`pytest` steht in `requirements.txt`, aber es gibt keinen einzigen Unit-Test. `test_all_pdfs.py` ist kein Test -- es ist ein Skript, das alle PDFs auf Lesbarkeit prueft. Ohne Tests ist jedes Refactoring ein Blindflug.

**7. Zirkulaere Import-Abhaengigkeiten**
`tei_unified.py` importiert aus `tei_generator.py` (5 Funktionen) und aus `layout_qa_gemini.py` (ueber lazy import). `tei_gemini.py` importiert ebenfalls aus `layout_qa_gemini.py` und `tei_generator.py`. Diese Spaghetti-Abhaengigkeiten machen isoliertes Testen unmoeglich.

**8. Inkonsistente Fehlerbehandlung**
- `except Exception: pass` (layout_qa_gemini.py:55, tei_unified.py:105) -- verschluckt alle Fehler
- Manche Funktionen geben `None` zurueck, manche `{}`, manche `[]`
- Keine einheitliche Logging-Strategie (print vs. nichts)

---

## Refactoring-Ziele (priorisiert)

1. **Wartbarkeit**: Ein neuer Entwickler versteht die Struktur in 10 Minuten
2. **Testbarkeit**: Kernlogik kann isoliert getestet werden
3. **DRY**: Boilerplate-Code existiert nur einmal
4. **Robustheit**: Fehler werden sichtbar, nicht verschluckt
5. **Erweiterbarkeit**: Neue Pipeline-Stages lassen sich sauber einfuegen

**Explizit NICHT im Scope:**
- Neue Features
- Aenderung der Gemini/LLM-Prompts
- Aenderung der Output-Formate
- Python-Packaging (pyproject.toml)
- Performance-Optimierung

---

## Phase 1: Test-Baseline erstellen (Voraussetzung fuer alles)

### Warum zuerst?
Ohne Tests ist Refactoring reines Gluecksspiel. Wir brauchen mindestens Regressionstests, die beweisen, dass der Output nach dem Refactoring identisch ist.

### 1.1 Snapshot-Tests fuer Pipeline-Output

```
tests/
  __init__.py
  conftest.py              # Shared fixtures (project_root, data_dir, etc.)
  test_config.py           # config.py: Pfade existieren, Konstanten konsistent
  test_utils.py            # utils.py: load_json, write_json, extract_page_num, etc.
  test_tei_inline.py       # md_to_tei_inline, split_paragraphs, annotate_entities
  test_normalize.py        # normalize_text, postprocess-Module
```

**Aufwand:** 1h
**Impact:** Ohne diese Phase ist kein sicheres Refactoring moeglich.

### 1.2 Golden-File-Tests fuer TEI-Output

Fuer die 3 Pilot-Docs (2310, 2530, 1440) den aktuellen TEI-Output als "golden files" speichern. Nach jedem Refactoring-Schritt: Diff gegen Golden Files.

```
tests/golden/
  2310_tei_unified.xml
  2530_tei_unified.xml
  1440_tei_unified.xml
```

**Aufwand:** 30 min
**Impact:** Beweist, dass Refactoring den Output nicht veraendert.

---

## Phase 2: config.py entflechten

### Warum?
config.py ist die meistimportierte Datei (20+ Imports quer durchs Projekt). Wenn diese Datei sauber ist, profitiert alles andere.

### 2.1 Testplan-Daten externalisieren

**Vorher** (config.py:128--164): 36 Zeilen Python-Dict im Code.
**Nachher:** `data/testplan.json` -- Datendatei, die von `config.py` geladen wird.

```python
# config.py
TESTPLAN = json.loads((DATA_DIR / "testplan.json").read_text(encoding="utf-8"))
```

**Begruendung:** Testplan-Daten sind keine Code-Konfiguration. Sie aendern sich unabhaengig vom Code (neue Pilot-Docs, neue Phasen). Als JSON-Datei koennen sie auch von anderen Tools gelesen werden.

### 2.2 KNOWN_ENTITIES externalisieren

**Vorher** (config.py:167--179): Python-Dict im Code.
**Nachher:** `data/known_entities.json`

**Begruendung:** Entity-Daten wachsen im Laufe des Projekts. Als JSON-Datei koennen sie von Editoren oder NER-Tools direkt gepflegt werden.

### 2.3 config.py in Sektionen ordnen

Klare Trennung durch Kommentarsektionen:
1. Pfade (Verzeichnisse)
2. TEI-Konstanten (Namespace, Schema, etc.)
3. OCR-Konfiguration (Modelle, Timeouts)
4. Layout-Konfiguration (Farben, Mappings)

**Aufwand Phase 2:** 45 min
**Risiko:** Gering -- nur Daten werden verschoben, Interfaces bleiben gleich.

---

## Phase 3: Gemini-Client extrahieren (DRY)

### Warum?
4 Dateien (gemini_ocr_correct, layout_qa_gemini, tei_gemini, tei_unified) implementieren alle denselben Gemini-API-Aufruf: API-Key laden, Client erstellen, Rate-Limit-Handling, Retry-Logik. Das sind 4 Kopien derselben 20--30 Zeilen.

### 3.1 Shared Gemini Client

```python
# scripts/gemini_client.py
"""Zentraler Gemini-API-Client mit Retry-Logik und Rate-Limit-Handling."""

import os
import time
import warnings

warnings.filterwarnings("ignore", message=".*non-text parts.*thought_signature.*")

from google import genai


def get_client() -> genai.Client:
    """Erstellt Gemini-Client mit API-Key aus Environment."""
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY nicht gesetzt")
    return genai.Client(api_key=api_key)


def call_gemini(client, model, contents, config=None, retries=3, base_delay=15):
    """Gemini-API-Call mit Rate-Limit-Retry."""
    for attempt in range(retries):
        try:
            return client.models.generate_content(
                model=model, contents=contents, config=config
            )
        except Exception as e:
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                delay = base_delay * (attempt + 1)
                print(f"  Rate limit, warte {delay}s...")
                time.sleep(delay)
            else:
                raise
    raise RuntimeError(f"Gemini-API nach {retries} Versuchen fehlgeschlagen")
```

### 3.2 dotenv-Loading zentralisieren

Statt 6x `from dotenv import load_dotenv; load_dotenv()`:

```python
# scripts/utils.py -- load_env() erweitern
def load_env():
    """Laedt .env-Datei ins Environment."""
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        # Fallback: manuelles Parsen (bestehender Code)
        ...
```

Alle Scripts rufen `load_env()` in ihrer `main()` auf -- nicht auf Modul-Ebene.

**Aufwand Phase 3:** 1h
**Impact:** Eliminiert ~120 Zeilen duplizierter Code. Macht API-Key-Handling konsistent und testbar.

---

## Phase 4: Scripts in Submodule reorganisieren

### Warum?
Die flache Struktur von `scripts/` spiegelt nicht die 7-Stage-Pipeline wider. Ein Entwickler muss die gesamte Codebasis lesen, um zu verstehen, welches Script zu welcher Stage gehoert.

### 4.1 Neue Verzeichnisstruktur

```
scripts/
  __init__.py
  config.py                    # Zentrale Konfiguration (bereinigt)
  utils.py                     # Shared Utilities
  gemini_client.py             # Gemini-API-Client (neu, Phase 3)
  cli.py                       # Shared CLI-Utilities (neu, Phase 5)
  ocr/                         # === Stage 1+2: OCR + Korrektur ===
    __init__.py
    pipeline.py                # <- ocr_pipeline.py
    gemini_correct.py          # <- gemini_ocr_correct.py
    llm_postprocess.py         # <- llm_postprocess.py
    extract_pages.py           # <- extract_pages.py
  layout/                      # === Stage 3+4: Layout ===
    __init__.py                # (bestehend, erweitert)
    analysis.py                # <- run_layout_analysis.py
    cloud.py                   # <- run_layout_cloud.py
    qa_gemini.py               # <- layout_qa_gemini.py
    overlays.py                # <- generate_layout_overlays.py
    page_xml_generator.py      # (bestehend)
    mets_generator.py          # (bestehend)
  tei/                         # === Stage 5+6: TEI ===
    __init__.py                # (bestehend)
    generator.py               # <- tei_generator.py (Rename)
    unified.py                 # <- tei_unified.py (Rename)
    gemini.py                  # <- tei_gemini.py (Rename)
    validator.py               # <- tei_validator.py (Rename)
    mapping_prompt.py          # <- tei_mapping_prompt.py (Rename)
  postprocess/                 # (bestehend, unveraendert)
    __init__.py
    clean_markdown.py
    dehyphenate.py
    normalize.py
    pipeline.py
  eval/                        # === Evaluation + Dashboard ===
    __init__.py
    evaluate.py                # <- evaluate_ocr.py
    dashboard.py               # <- generate_dashboard_data.py
    test_pdfs.py               # <- test_all_pdfs.py
  metadata/                    # === Klassifikation + Metadaten ===
    __init__.py
    classify.py                # <- classify_docs.py
    extract_gnd.py             # <- extract_gnd.py
    edition.py                 # <- generate_edition_data.py
  experiments/                 # (bestehend, unveraendert)
    layout_eval.py
```

### 4.2 Import-Aktualisierung

Alle Imports muessen angepasst werden, z.B.:
```python
# Vorher:
from scripts.layout_qa_gemini import build_doc_hints
# Nachher:
from scripts.layout.qa_gemini import build_doc_hints
```

### 4.3 CLI-Aufrufe aktualisieren

```bash
# Vorher:
python -m scripts.gemini_ocr_correct --doc 2310
# Nachher:
python -m scripts.ocr.gemini_correct --doc 2310
```

Dokumentation in `knowledge/PIPELINE.md` entsprechend aktualisieren.

### 4.4 sys.path-Hacks entfernen

Nach der Reorganisation werden alle `sys.path.insert(0, ...)` Zeilen entfernt (6 Vorkommen). Die Package-Struktur mit `__init__.py` macht sie ueberfluessig, solange Scripts von der Projekt-Root aus aufgerufen werden.

**Aufwand Phase 4:** 2h
**Risiko:** Hoch -- bricht alle bestehenden CLI-Aufrufe. Deshalb erst NACH Phase 1 (Tests).
**Impact:** Groesster einzelner Verbesserungsschritt. Macht die Pipeline-Architektur im Dateisystem sichtbar.

---

## Phase 5: CLI-Boilerplate konsolidieren

### Warum?
10+ Scripts implementieren dieselben argparse-Argumente (`--doc`, `--sample`, `--all`, `--force`, `--dry-run`, `--phase`) mit leicht unterschiedlicher Logik. Jedes neue Script kopiert den Boilerplate-Block eines anderen.

### 5.1 Shared CLI Module

```python
# scripts/cli.py
"""Shared CLI-Argument-Definitionen fuer Pipeline-Scripts."""

import argparse

def add_doc_args(parser: argparse.ArgumentParser):
    """Fuegt Standard-Dokument-Argumente hinzu."""
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--doc", help="Einzelnes Dokument (ID)")
    group.add_argument("--sample", action="store_true", help="Pilot-Docs")
    group.add_argument("--all", action="store_true", help="Alle Dokumente")
    group.add_argument("--phase", help="TESTPLAN-Phase")
    parser.add_argument("--force", action="store_true", help="Cache ueberschreiben")
    parser.add_argument("--dry-run", action="store_true", help="Nur anzeigen")

def resolve_doc_ids(args, sample_ids=None, discover_fn=None) -> list[str]:
    """Loest --doc/--sample/--all/--phase zu Doc-ID-Liste auf."""
    ...
```

**Aufwand:** 45 min
**Impact:** Eliminiert ~150 Zeilen duplizierter argparse-Code. Garantiert konsistente CLI-Interfaces.

---

## Phase 6: God-Files aufbrechen

### Warum?
4 Dateien mit 800+ Zeilen haben jeweils mehrere Verantwortlichkeiten. Das macht Code-Review schwierig, erhoeht die kognitive Last, und macht isoliertes Testen unmoeglich.

### 6.1 evaluate_ocr.py (1017 LOC) aufteilen

| Funktion | LOC | Neues Modul |
|----------|-----|-------------|
| `extract_text_from_tei`, `extract_pages_from_tei`, `normalize_text` | ~140 | `scripts/eval/text_extraction.py` |
| `compute_cer`, `compute_wer`, `compare_*` | ~200 | bleibt in `evaluate.py` |
| `generate_report` (HTML-Generierung) | ~350 | `scripts/eval/html_report.py` |
| `generate_evaluation_report` (Seiten-Evaluierung) | ~200 | bleibt in `evaluate.py` |
| `main()` + argparse | ~130 | bleibt in `evaluate.py` |

**Ergebnis:** `evaluate.py` sinkt von 1017 auf ~530 LOC.

### 6.2 layout_qa_gemini.py (823 LOC) aufteilen

| Funktion | LOC | Neues Modul |
|----------|-----|-------------|
| Prompt-Hints (LAYOUT_TYPE_HINTS, PUB_FORM_HINTS, etc.) | ~120 | `scripts/layout/prompts.py` |
| `build_doc_hints()`, `infer_genre()` | ~80 | `scripts/layout/prompts.py` |
| `ensure_overlay()` | ~50 | `scripts/layout/overlays.py` (existiert) |
| QA/Detect-Logik | ~400 | bleibt in `qa_gemini.py` |
| `main()` + argparse | ~170 | bleibt in `qa_gemini.py` |

**Ergebnis:** `qa_gemini.py` sinkt von 823 auf ~570 LOC. Prompt-Daten sind sauber getrennt.

### 6.3 gemini_ocr_correct.py (811 LOC) -- bleibt vorerst

Dieses Script ist zwar lang, aber hat eine klare lineare Struktur (Analyse -> Korrektur -> Manifest). Es profitiert hauptsaechlich von Phase 3 (Gemini-Client) und Phase 5 (CLI-Boilerplate), die es um ~80 LOC kuerzen.

### 6.4 tei_unified.py (1230 LOC) -- bereits teilrefactored

Das TEI-Pipeline-Refactoring aus Session 15 hat die groebsten Probleme behoben. Verbleibende Verbesserungen:
- `process_page_step1()` ist immer noch 120+ Zeilen -> Facsimile-Builder und Body-Builder extrahieren
- Lazy-Import von layout_qa_gemini loest sich durch Phase 4 (korrekte Modulstruktur)

**Aufwand Phase 6:** 2.5h
**Impact:** Halbiert die kognitive Last der groessten Dateien. Macht Code-Review moeglich.

---

## Phase 7: Fehlerbehandlung vereinheitlichen

### Warum?
Stille Fehler (`except Exception: pass`) sind das gefaehrlichste Anti-Pattern im Projekt. Sie verbergen Bugs, die erst in der Produktion sichtbar werden -- wenn ein Dokument ploetzlich falschen TEI-Output liefert und niemand weiss warum.

### 7.1 `except Exception: pass` eliminieren

**3 Vorkommen:**
1. `layout_qa_gemini.py:55` -- `_doc_metadata`-Loading: JSON-Fehler wird verschluckt
2. `tei_unified.py:105` -- Layout-Loading (bereits gefixt im TEI-Refactoring)
3. `tei_gemini.py` -- Gemini API-Fehler

**Fix:** Spezifische Exceptions fangen, immer loggen:
```python
except (json.JSONDecodeError, OSError) as e:
    print(f"  WARNUNG: {e}")
```

### 7.2 Logging-Konvention einfuehren

Kein `logging`-Framework (Overhead fuer dieses Projekt uebertrieben), aber konsistente print-Praefixe:

```
OK:   "  OK: TEI generiert fuer 2310_p001"
WARN: "  WARNUNG: Layout fehlt fuer 2310_p003"
ERR:  "  FEHLER: Gemini API-Key nicht gesetzt"
SKIP: "  SKIP: 2310_p001 existiert bereits (--force zum Ueberschreiben)"
```

**Aufwand Phase 7:** 1h
**Impact:** Bugs werden sichtbar statt verschluckt. Debugging wird moeglich.

---

## Phase 8: Frontend aufraemen

### Warum?
`shared.css` mit 34.634 Bytes ist fuer ein internes Tool-Dashboard uebermaessig gross. Die Datei enthaelt Styles fuer Dashboard, Viewer, Benchmark, Edition -- alles in einem File. Ein Entwickler, der nur den Viewer anpassen will, muss durch 900+ CSS-Zeilen scrollen.

### 8.1 CSS in logische Dateien aufteilen

```
docs/
  css/
    variables.css          # CSS Custom Properties (:root)
    base.css               # Reset, Typography, Layout-Primitives
    components.css         # Cards, Tabs, Badges, Tables
    dashboard.css          # Dashboard-spezifisch
    viewer.css             # Viewer-spezifisch (PAGE-XML, TEI)
    benchmark.css          # Benchmark-spezifisch
  shared.css               # @import-Aggregator (Abwaertskompatibilitaet)
```

### 8.2 JS-Dateien konsolidieren

- `shared.js` (ZBZ-Namespace) bleibt zentral
- `viewer.js` + `page-viewer.js` + `tei-viewer.js` -> eventuell zusammenfuehren, da sie alle denselben Viewer-State teilen

### 8.3 Edition bleibt separat

`docs/edition/` hat ein eigenes Design-System (`ZBZ.Edition`). Das ist richtig so -- es ist eine andere Zielgruppe (Endnutzer vs. Entwickler).

**Aufwand Phase 8:** 1.5h
**Impact:** Mittel. Kein funktionaler Gewinn, aber deutlich bessere Wartbarkeit der Frontends.

---

## Ausfuehrungsreihenfolge und Abhaengigkeiten

```
Phase 1 (Tests)         ████████  1.5h   -- MUSS zuerst, Voraussetzung fuer alles
Phase 2 (Config)        █████  45m       -- unabhaengig, niedriges Risiko
Phase 3 (Gemini-Client) ██████  1h       -- unabhaengig, hohes DRY-Potenzial
Phase 5 (CLI)           █████  45m       -- unabhaengig, parallel zu Phase 2/3
Phase 4 (Reorganisation)████████████  2h -- haengt von Phase 1 ab (Tests als Sicherheitsnetz)
Phase 6 (God-Files)     ██████████  2.5h -- nach Phase 4 (neue Modulstruktur)
Phase 7 (Fehler)        ██████  1h       -- nach Phase 6
Phase 8 (Frontend)      ████████  1.5h   -- unabhaengig, kann parallel
                        ─────────────────
                        Total: ~11h
```

**Kritischer Pfad:** Phase 1 -> Phase 4 -> Phase 6 -> Phase 7

**Parallelisierbar:**
- Phase 2 + Phase 3 + Phase 5 (alle unabhaengig)
- Phase 8 (unabhaengig vom Backend)

---

## Validierungsstrategie

### Nach jeder Phase:
1. Golden-File-Diff: TEI-Output fuer Pilot-Docs muss identisch sein
2. `python -m pytest tests/` muss gruen sein
3. CLI-Smoke-Test: `python -m scripts.tei.tei_unified --doc 2310 --dry-run`
4. Dashboard: `docs/index.html` muss noch laden

### Am Ende:
1. Alle 11 Pipeline-Stages einmal durchlaufen (Dry-Run)
2. Knowledge-Base aktualisieren (`PIPELINE.md` CLI-Referenz)
3. `JOURNAL.md` dokumentieren

---

## Was dieses Refactoring NICHT loest

- **Keine End-to-End-Tests**: Die Pipeline braucht Gemini-API-Keys und GPU. Echte Integrationstests erfordern Mocking oder eine Test-Umgebung.
- **Kein Packaging**: Ohne `pyproject.toml` bleibt `sys.path`-abhaengiges Ausfuehren von der Projekt-Root noetig (aber die `sys.path.insert`-Hacks verschwinden).
- **Keine Typannotationen**: Das Projekt nutzt `dict | None`-Syntax, aber keine umfassenden Type Hints. Das waere ein separates Refactoring.
- **Kein Linting/Formatting**: Kein `ruff`/`black` konfiguriert. Wuerde helfen, ist aber ein separater Schritt.

---

## Warum dieser Plan das Projekt verbessert

### 1. Architektur wird sichtbar
Die 7-Stage-Pipeline (PDF -> Images -> OCR -> Layout -> PAGE-XML -> TEI -> Eval) wird direkt im Dateisystem ablesbar. Heute muss man `knowledge/PIPELINE.md` lesen, um zu verstehen welches Script wozu gehoert. Nach dem Refactoring sagt die Verzeichnisstruktur alles.

### 2. Onboarding wird moeglich
Ein neuer Entwickler kann heute nicht in das Projekt einsteigen, ohne jemanden zu fragen. Nach dem Refactoring: `scripts/ocr/` fuer OCR, `scripts/tei/` fuer TEI, `scripts/eval/` fuer Evaluation. Selbsterklaerend.

### 3. Aenderungen werden sicher
Heute ist jede Aenderung an `tei_unified.py` riskant, weil 1230 Zeilen betroffen sind und es keine Tests gibt. Nach dem Refactoring: kleinere Module mit Tests, aenderungsfreundlich.

### 4. DRY reduziert Fehlerquellen
120+ Zeilen duplizierter Gemini-Client-Code bedeuten 4 Stellen, an denen Retry-Logik oder API-Key-Handling inkonsistent sein kann. Nach dem Refactoring: eine Stelle, eine Wahrheit.

### 5. Fehler werden sichtbar
`except Exception: pass` ist der schlimmste Feind der Datenqualitaet. Wenn ein Layout-JSON defekt ist, muss das sichtbar sein -- nicht stillschweigend uebergangen.

### 6. Kein Big-Bang
Jede Phase ist einzeln ausfuehrbar und testbar. Wenn nach Phase 4 etwas schiefgeht, kann man dorthin zurueckrollen. Das Projekt bleibt durchgehend funktionsfaehig.
