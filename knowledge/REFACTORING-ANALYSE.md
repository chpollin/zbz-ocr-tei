# Repository-Analyse & Refactoring-Plan

Erstellt: 2026-03-07 | Kontext: Ganzheitliche Analyse des zbz-ocr-tei Repositories

---

## 1. Projekt-Status: Zusammenfassung

**Reife: ~95% Production-Ready**

| Komponente | Status | Bemerkung |
|-----------|--------|-----------|
| Image Extraction | DONE | 4.152 PNGs |
| Dokumentklassifikation | DONE | 286/286 (Gemini) |
| OCR (Mistral) | DONE | 285/286, CER 6.42% |
| Layout (Docling + Gemini QA) | DONE | 4.152 Seiten, 14.708 Korrekturen |
| PAGE-XML + METS | DONE | 4.091 + 286 Dateien |
| TEI Pipeline (Unified) | PRODUCTION | 22/23 VALID, E32 |
| Digitale Edition | DONE | 4 Demo-Docs live |
| Dashboard + Evaluation | DONE | HTML + JSON |
| NER + GND | PENDING | Phase 3, blockiert M3 |

**Was gut laeuft:**
- Pipeline funktioniert end-to-end fuer 286 Dokumente
- Kosten minimal (~$70-80 fuer alles)
- Gute Dokumentation in knowledge/
- Frontend sauber in ES5, keine Inline-Scripts
- config.py als zentrale Konfiguration vorhanden

**Was problematisch ist:**
- Mehrere grosse Dateien (>800 Zeilen) mit God-Functions
- Signifikante Code-Duplikation (Python + JavaScript)
- Keine automatisierten Tests (nur 1 test_all_pdfs.py)
- Inkonsistente Fehlerbehandlung
- Magic Numbers verstreut im Code
- Metadata-Caching in 3 Dateien unterschiedlich implementiert

---

## 2. Refactoring-Bereiche: Uebersicht

### A. Python-Backend (Hoch-Prioritaet)

| # | Bereich | Dateien | Impact | Aufwand |
|---|---------|---------|--------|---------|
| A1 | God-Functions aufbrechen | evaluate_ocr.py, gemini_ocr_correct.py, layout_qa_gemini.py | Hoch | Mittel |
| A2 | Code-Duplikation eliminieren | 6+ Dateien | Hoch | Mittel |
| A3 | Shared Utilities extrahieren | Neu: scripts/core/ | Hoch | Gering |
| A4 | Magic Numbers zentralisieren | evaluate_ocr.py, gemini_ocr_correct.py, llm_postprocess.py | Mittel | Gering |
| A5 | Fehlerbehandlung vereinheitlichen | Alle API-Scripts | Mittel | Mittel |
| A6 | Import-Struktur bereinigen | tei_generator.py, utils.py | Gering | Gering |

### B. JavaScript-Frontend (Mittel-Prioritaet)

| # | Bereich | Dateien | Impact | Aufwand |
|---|---------|---------|--------|---------|
| B1 | TEI-Rendering deduplizieren | tei-viewer.js + edition-tei.js | Hoch | Mittel |
| B2 | Shared Utilities zusammenfuehren | shared.js + edition-shared.js | Mittel | Gering |
| B3 | Entity-Sidebar deduplizieren | tei-viewer.js + edition-tei.js | Mittel | Gering |

### C. Testbarkeit (Hoch-Prioritaet, aber eigenes Ticket)

| # | Bereich | Impact | Aufwand |
|---|---------|--------|---------|
| C1 | Unit-Tests fuer Kernfunktionen | Hoch | Hoch |
| C2 | Integration-Tests fuer Pipeline | Hoch | Hoch |

### D. Architektur (Niedrig-Prioritaet, langfristig)

| # | Bereich | Impact | Aufwand |
|---|---------|--------|---------|
| D1 | Config-Validierung | Gering | Gering |
| D2 | Logging statt print() | Mittel | Mittel |
| D3 | Type Hints vervollstaendigen | Gering | Mittel |

---

## 3. Detaillierter Refactoring-Plan

### A1: God-Functions aufbrechen

**evaluate_ocr.py (1.017 Zeilen) -- Groesste Baustelle**

| Funktion | Zeilen | Problem | Loesung |
|----------|--------|---------|---------|
| `generate_html_report()` | 274 | HTML-String manuell gebaut, keine Trennung von Daten und Darstellung | Aufteilen: `_build_summary_html()`, `_build_doc_section_html()`, `_build_diff_html()` |
| `evaluate_document_pagewise()` | 112 | 4 Ebenen Verschachtelung, Laden + Matching + Metriken gemischt | Aufteilen: `_load_page_files()`, `_match_pages_to_ref()`, `_compute_page_metrics()` |
| `find_best_alignment()` | 92 | Komplexe Suchalgorithmik mit verschachtelten Schleifen | Aufteilen: `_find_ref_in_ocr()`, `_find_ocr_in_ref()`, `_align_by_word_match()` |

**Begruendung:** evaluate_ocr.py ist das Herzstueck der Qualitaetssicherung. Wenn wir neue Metriken oder Formate brauchen, ist es aktuell extrem schwer, den Code zu erweitern.

**gemini_ocr_correct.py (811 Zeilen)**

| Funktion | Zeilen | Loesung |
|----------|--------|---------|
| `process_document()` | 103 | Aufteilen: `_analyze_page()`, `_correct_page()`, `_save_results()` |
| `build_analysis_prompt()` | 74 | Template-Pattern statt String-Concatenation |

**layout_qa_gemini.py (823 Zeilen)**

| Funktion | Zeilen | Loesung |
|----------|--------|---------|
| `qa_page()` | 149 | Aufteilen: `_prepare_qa_input()`, `_call_gemini_qa()`, `_apply_qa_corrections()` |
| `detect_page()` | 103 | Aufteilen: `_prepare_detect_input()`, `_call_gemini_detect()`, `_parse_detect_response()` |

---

### A2: Code-Duplikation eliminieren

**Duplikat 1: Metadata-Caching (3 Implementierungen)**

```
gemini_ocr_correct.py  -> _metadata_cache = None + Funktion
llm_postprocess.py     -> _metadata_cache = None + Funktion
layout_qa_gemini.py    -> _doc_metadata = json.load() auf Modul-Ebene
```

**Loesung:** Eine Funktion in `scripts/utils.py`:
```python
@functools.lru_cache(maxsize=1)
def load_doc_metadata() -> dict:
    path = DOC_METADATA_JSON
    return json.loads(path.read_text(encoding="utf-8"))
```
Alle 3 Dateien importieren `load_doc_metadata()`.

**Duplikat 2: Seiten-Datei-Suche (4+ Implementierungen)**

Wiederholtes Pattern:
```python
glob(f"{doc_id}_p*.md")  # + Regex fuer Seitennummer
```

Existiert in: evaluate_ocr.py, gemini_ocr_correct.py, ocr_pipeline.py, layout_qa_gemini.py

**Loesung:** Utility-Funktion in `scripts/utils.py`:
```python
def find_page_files(directory: Path, doc_id: str, suffix: str = ".md") -> list[tuple[int, Path]]:
    """Findet Seiten-Dateien und gibt sortierte (page_nr, path) Tupel zurueck."""
```

**Duplikat 3: Bounding-Box-Konvertierung (3 Implementierungen)**

```
layout/__init__.py       -> to_pixel_pct()
layout_qa_gemini.py      -> gemini_box_to_pct()
run_layout_analysis.py   -> manuelle bbox-Berechnungen
```

**Loesung:** Konsolidieren in `scripts/layout/__init__.py` als einzige Quelle.

---

### A3: Shared Utilities extrahieren

Neues Modul `scripts/core/` (oder direkt in `scripts/utils.py` erweitern):

```
scripts/utils.py (erweitert):
  + load_doc_metadata()      -- cached Metadata-Laden
  + find_page_files()        -- Seiten-Datei-Suche
  + extract_page_number()    -- Seitennummer aus Dateiname
  + safe_json_load()         -- JSON laden mit Fehlerbehandlung
```

**Begruendung:** Diese 4 Funktionen werden in 8+ Dateien gebraucht. Jede spart 5-15 Zeilen pro Verwendung und eliminiert Inkonsistenzen.

---

### A4: Magic Numbers zentralisieren

**In config.py aufnehmen:**

```python
# --- Evaluation Thresholds ---
CER_HIGH_ERROR_THRESHOLD = 0.05
CER_CRITICAL_ERROR_THRESHOLD = 0.10
ALIGNMENT_WINDOW_SIZE = 100
ALIGNMENT_CONTEXT_CHARS = 20
MIN_WORD_LENGTH_FOR_ALIGNMENT = 8
AUTO_PAGEWISE_MIN_PAGES = 10

# --- API Limits ---
MAX_CORRECTIONS_PER_PAGE = 50
MAX_CLASSIFICATION_PAGES = 5
LLM_MAX_TOKENS = 4096

# --- Cost Tracking ---
GEMINI_FLASH_INPUT_COST = 0.80 / 1_000_000
GEMINI_FLASH_OUTPUT_COST = 4.00 / 1_000_000
```

**Begruendung:** Aktuell sind diese Werte in Funktions-Bodies versteckt. Wenn sich ein API-Preis aendert oder ein Threshold angepasst werden soll, muss man grep ueber das ganze Repo laufen lassen.

---

### A5: Fehlerbehandlung vereinheitlichen

**Aktueller Zustand:**
- `classify_docs.py`: `except Exception` → print + continue
- `llm_postprocess.py`: Spezifische Exceptions fuer API-Calls
- `layout_qa_gemini.py`: Silent `return None` bei Fehlern
- `ocr_pipeline.py`: `raise_for_status()` ohne try-catch → Crash
- `gemini_ocr_correct.py`: Generic Exception → partial results

**Loesung: Einheitliches Pattern fuer API-Aufrufe:**

```python
# In scripts/utils.py:
def call_api_with_retry(fn, max_retries=2, backoff=2.0):
    """Ruft fn() auf mit Retry fuer Netzwerk/Rate-Limit-Fehler.

    Raises:
        AuthenticationError: Bei API-Key-Fehlern (kein Retry)
        APIError: Bei persistenten Fehlern nach max_retries
    """
```

Schrittweise einfuehren:
1. Zuerst in einem Script testen (z.B. classify_docs.py)
2. Dann auf die anderen ausrollen

---

### A6: Import-Struktur bereinigen

**Problem:** `tei_generator.py` verwendet `sys.path.insert(0, ...)` Hack.

**Loesung:**
- Alle Scripts als Package ausfuehren: `python -m scripts.tei.tei_generator`
- `sys.path.insert` entfernen
- Relative Imports innerhalb von Packages nutzen

**Problem:** `utils.py` hat dynamischen Import in `get_phase_doc_ids()`.

**Loesung:** Zirkulaere Abhaengigkeit aufloesen -- Phase-Doc-IDs gehoeren in config.py, nicht in utils.py.

---

### B1: TEI-Rendering deduplizieren (Frontend)

**~500 Zeilen duplizierter Code zwischen Dashboard und Edition:**

| Komponente | tei-viewer.js | edition-tei.js | Zeilen dupliziert |
|-----------|---------------|----------------|-------------------|
| TEI Node Rendering | renderTeiNode() (132 Z.) | renderNode() (106 Z.) | ~120 |
| Entity Extraction | extractEntities() (90 Z.) | Inline (98 Z.) | ~100 |
| Entity Sidebar | renderEntitySidebar() | renderEntitySidebar() | ~80 |
| XML Parsing | In shared.js | In edition-shared.js | ~40 |
| Hilfsfunktionen | $(), $$(), esc(), padPage() | $(), $$(), esc(), padPage() | ~20 |

**Loesung:** Neues `docs/tei-core.js` erstellen:

```javascript
// docs/tei-core.js -- Shared TEI rendering (ES5)
(function() {
    'use strict';
    window.ZBZ = window.ZBZ || {};
    window.ZBZ.TeiCore = {
        renderNode: function(node, opts) { /* ... */ },
        extractEntities: function(xmlDoc) { /* ... */ },
        renderEntitySidebar: function(entities, container) { /* ... */ }
    };
})();
```

Beide Viewer importieren `tei-core.js` und rufen `ZBZ.TeiCore.*` auf.

**Begruendung:** Jede Aenderung am TEI-Rendering muss aktuell an 2 Stellen gemacht werden. Bei der kommenden NER/GND-Integration (Phase 3) werden die Entity-Funktionen erweitert -- das muss genau 1x passieren.

---

### B2: Shared Utilities zusammenfuehren (Frontend)

**Duplizierte Funktionen:**

| Funktion | shared.js | edition-shared.js |
|----------|-----------|-------------------|
| `$()` / `$$()` | Zeile 278-279 | Zeile 13-14 |
| `parseXml()` | Zeile 186-195 | Zeile 45-55 |
| `highlightXml()` | Zeile 197-224 | Zeile 57-64 |
| `fmtNum()` | Zeile 270-271 | Zeile 23-24 |
| `padPage()` | Zeile 273-274 | Zeile 26-27 |
| `esc()` | Zeile 276-277 | Zeile 29-30 |

**Loesung:** `edition-shared.js` importiert `shared.js` und nutzt `ZBZ.$()`, `ZBZ.parseXml()` etc. direkt, statt eigene Kopien zu definieren.

**Begruendung:** 6 identische Funktionen in 2 Dateien. Einfach zu beheben, eliminiert eine Fehlerquelle.

---

## 4. Priorisierte Umsetzungsreihenfolge

```
Prioritaet 1 -- Quick Wins (1-2h, hoher Impact)
═══════════════════════════════════════════════
A3  Shared Utilities in utils.py          30 min   Basis fuer alles Weitere
A4  Magic Numbers → config.py             30 min   Sofort sichtbare Verbesserung
B2  Frontend: Shared Utilities merge      30 min   Einfachster Frontend-Fix

Prioritaet 2 -- Kern-Refactoring (3-4h, hoechster Impact)
═══════════════════════════════════════════════════════════
A2  Code-Duplikation eliminieren          60 min   Haengt von A3 ab
A1  evaluate_ocr.py aufbrechen            90 min   Groesste/komplexeste Datei
B1  TEI-Rendering deduplizieren           60 min   Kritisch vor NER/GND

Prioritaet 3 -- Robustheit (2h, mittlerer Impact)
══════════════════════════════════════════════════
A5  Fehlerbehandlung vereinheitlichen     60 min   Stabilitaet
A6  Import-Struktur bereinigen            30 min   Saubere Abhaengigkeiten

Prioritaet 4 -- Langfristig (eigene Tickets)
═════════════════════════════════════════════
C1  Unit-Tests                            4-8h     Erst nach Refactoring sinnvoll
C2  Integration-Tests                     4-8h     Pipeline-Absicherung
D2  Logging statt print()                 2h       Erleichtert Debugging
D3  Type Hints vervollstaendigen          2h       IDE-Support
```

---

## 5. Ehrliche Einschaetzung: Was ist realistisch?

### Sofort umsetzbar (diese Session):
- **A3 + A4**: Shared Utilities + Magic Numbers → config.py
- **B2**: Frontend-Duplikation der Hilfsfunktionen

### In 1-2 weiteren Sessions umsetzbar:
- **A2**: Metadata-Cache + Page-File-Suche deduplizieren
- **A1**: evaluate_ocr.py aufbrechen (groesster Brocken)
- **B1**: tei-core.js extrahieren

### Was ich NICHT empfehle jetzt zu tun:
1. **Komplettes Logging-Framework einfuehren** -- Overkill fuer ein Pipeline-Projekt, print() reicht
2. **100% Type-Hint-Coverage** -- Aufwand-Nutzen-Verhaeltnis schlecht bei Scripts die funktionieren
3. **Abstrakte API-Client-Klasse** -- Jeder API-Aufruf (Gemini, Mistral, Anthropic) hat eigene Eigenheiten, eine Abstraktion wuerde mehr schaden als nutzen
4. **Konfiguration in YAML/TOML auslagern** -- config.py ist gut genug, externes Config-Format wuerde Komplexitaet ohne Nutzen hinzufuegen
5. **Frontend auf ES6+ migrieren** -- Explizite Projektanforderung ist ES5

### Was den groessten Hebel hat:
1. **A2 (Duplikation)** eliminiert die meisten Fehlerquellen
2. **B1 (TEI-Core)** ist kritisch fuer die NER/GND-Phase, die als naechstes kommt
3. **A1 (evaluate_ocr.py)** macht das wichtigste QA-Tool erweiterbar

---

## 6. Risiken und Mitigierung

| Risiko | Wahrscheinlichkeit | Mitigierung |
|--------|-------------------|-------------|
| Refactoring aendert Output | Mittel | Vor/Nachher-Diff auf Pilot-Docs (2310, 2530, 1440) |
| Import-Aenderungen brechen CLI | Gering | Jeden CLI-Befehl nach Aenderung testen |
| Frontend-Merge bricht Edition | Gering | Browser-Test auf allen 4 Seiten |
| Zeitaufwand unterschaetzt | Mittel | Priorisiert arbeiten, Quick Wins zuerst |

---

## 7. Zusammenfassung

Das Projekt ist **reif und funktional** -- der Code hat seine Aufgabe erfuellt. Die Refactoring-Beduerfnisse kommen nicht aus akuten Problemen, sondern aus der Vorbereitung auf:

1. **NER/GND-Integration (Phase 3)** -- braucht saubere TEI-Rendering und Entity-Handling
2. **Production Run fuer 286 Docs** -- braucht robuste Fehlerbehandlung
3. **Wartbarkeit** -- wenn jemand anderes den Code anfassen muss

Der bereits umgesetzte TEI-Refactoring-Plan (REFACTORING_PLAN.md) war ein guter erster Schritt. Dieser Plan hier geht breiter und deckt das gesamte Repository ab.
