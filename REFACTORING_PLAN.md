# Refactoring Plan: TEI Pipeline (tei_unified.py, tei_validator.py, tei_mapping_prompt.py)

Erstellt: 2026-03-07 | Status: Umgesetzt (2026-03-07)
Kontext: Nach Production Run (E32) organisch gewachsener Code mit 1233 Zeilen in tei_unified.py.

---

## Ziele

- Wartbarkeit und Lesbarkeit verbessern
- Bugs fixen (XPath in Validator)
- God-Functions aufbrechen
- DRY-Violations beseitigen
- Testbarkeit erhoehen
- Keine funktionalen Aenderungen (gleicher Output)

---

## Phase 1: Kritische Bugs (sofort)

### 1.1 XPath-Bugs in tei_validator.py fixen
**Dateien:** `scripts/tei/tei_validator.py`
**Problem:** R6 (L165), R7 (L175), R8 (L185) verwenden `f".\{{{TEI_NS}}}"` statt `f".//{{{TEI_NS}}}"`. Die Regeln finden moeglicherweise keine Elemente und melden falsche VALID-Ergebnisse.
**Fix:** Alle drei XPath-Ausdruecke korrigieren zu `f".//{{{TEI_NS}}}..."`.
**Test:** Validierung auf Pilot-Docs (2310, 1440, 2530) vor und nach Fix vergleichen.
**Aufwand:** 5 min

### 1.2 Dead Code entfernen (tei_mapping_prompt.py)
**Dateien:** `scripts/tei/tei_mapping_prompt.py`
**Problem:** L291-292: `if genre == "debate" and "debate" not in GENRE_RULES` ist toter Code (debate existiert in GENRE_RULES).
**Fix:** Zeilen entfernen.
**Aufwand:** 2 min

---

## Phase 2: Shared Constants extrahieren

### 2.1 TEI_NS in config.py zentralisieren
**Dateien:** `scripts/config.py`, `scripts/tei/tei_unified.py`, `scripts/tei/tei_validator.py`
**Problem:** `TEI_NS = "http://www.tei-c.org/ns/1.0"` ist in tei_unified.py (L530, L904) und tei_validator.py (L22) separat definiert.
**Fix:** `TEI_NS` in `config.py` definieren, ueberall importieren.

### 2.2 Speaker-Regex als Konstante
**Dateien:** `scripts/tei/tei_unified.py`
**Problem:** Speaker-Erkennungs-Regex (L295 und L345) ist fast identisch, aber leicht unterschiedlich.
**Fix:** Eine `SPEAKER_PATTERN` Konstante am Modulanfang definieren, an beiden Stellen verwenden.

### 2.3 VALID_DIV_TYPES teilen
**Dateien:** `scripts/tei/tei_validator.py`, `scripts/config.py`
**Problem:** Valid div types (L143-147) sind in der Funktion hardcoded.
**Fix:** Nach `config.py` verschieben, damit tei_unified.py dieselben Typen verwenden kann.

### 2.4 TEI_ALL_URL und Schema-Timeout in config.py
**Dateien:** `scripts/tei/tei_validator.py`, `scripts/config.py`
**Problem:** URL (L23) hardcoded, kein Timeout beim Download (L40).
**Fix:** URL und TIMEOUT in config.py, `urlretrieve` durch `urllib.request.urlopen` mit Timeout ersetzen.

---

## Phase 3: fix_gemini_tei() aufbrechen (God-Function)

### 3.1 Regex-Fixes extrahieren
**Dateien:** `scripts/tei/tei_unified.py`
**Problem:** fix_gemini_tei() (L475-545) mischt 3 verschiedene Strategien: Regex-Fixes, ET-Parsing, Entity-Annotation.
**Fix:** Neue Funktion `_fix_simple_patterns(xml: str) -> str` fuer:
- Fix -1: ab-Unwrap (L483-493)
- Fix 0: head-in-speaker (L496-502)
- Fix 1: head-p-Flatten (L505-515)

### 3.2 Struktur-Fixes extrahieren
**Dateien:** `scripts/tei/tei_unified.py`
**Fix:** Neue Funktion `_fix_structural_issues(xml: str) -> str` fuer:
- Fix 2: head-after-content (L534-545)
- Fix 2b: epigraph-after-content (L542-548)
- Fix 3: sp-mixed-split (L547-608)
- Fix 3b: inline-in-div-wrap (L617-647)

### 3.3 fix_gemini_tei() wird Orchestrator
**Fix:** Reduziert auf:
```python
def fix_gemini_tei(xml: str) -> str:
    xml = _fix_simple_patterns(xml)
    xml = _fix_structural_issues(xml)
    xml = reannotate_entities(xml)
    return xml
```
**Aufwand:** 30 min
**Test:** Alle 3 Pilot-Docs muessen identischen Output liefern wie vor Refactoring.

---

## Phase 4: Duplizierte Wrapping-Logik zusammenfuehren

### 4.1 Shared Utility: _wrap_orphan_groups()
**Dateien:** `scripts/tei/tei_unified.py`
**Problem:** `_fix_orphaned_body_children()` (L900-961) und Fix 3 in fix_gemini_tei() verwenden fast identische Logik: Kinder iterieren, zusammenhaengende Gruppen sammeln, in Container einwickeln.
**Fix:** Shared Utility extrahieren:
```python
def _wrap_orphan_groups(
    container: ET.Element,
    is_orphan: Callable[[ET.Element], bool],
    make_wrapper: Callable[[], ET.Element],
) -> None:
```
Beide Stellen rufen diese Utility auf.
**Aufwand:** 20 min

### 4.2 XML-Namespace-Handling vereinheitlichen
**Problem:** fix_gemini_tei() verwendet root-Wrapper + Strip-Regex (L536-542), _fix_orphaned_body_children() verwendet ET.tostring mit xml_declaration (L624).
**Fix:** Einheitliche Hilfsfunktion `_parse_tei_fragment(xml)` und `_serialize_tei_fragment(root)`.
**Aufwand:** 15 min

---

## Phase 5: process_page_step1() aufbrechen

### 5.1 Facsimile-Berechnung extrahieren
**Dateien:** `scripts/tei/tei_unified.py`
**Problem:** L267-281 (Koordinaten-Konvertierung) ist in process_page_step1() eingebettet.
**Fix:** Neue Funktion `_compute_facsimile_zones(matched, layout, page) -> dict`.

### 5.2 TEI-Body-Fragment-Builder extrahieren
**Problem:** L289-410 (120 Zeilen) baut das TEI-Fragment mit verschachtelter Logik (Interview-Detection, Entity-Wrapping, Tag-Auswahl).
**Fix:** Neue Funktion `_build_tei_body(matched, page, genre, is_interview) -> str`.

### 5.3 Interview-Speaker-Erkennung extrahieren
**Problem:** `_is_interview_turn()` (L290-311) ist eine innere Funktion in process_page_step1().
**Fix:** Auf Modulebene verschieben (ist bereits ohne Closure-Variablen).

**Aufwand Phase 5:** 30 min
**Ergebnis:** process_page_step1() wird ~30 Zeilen (Orchestrator).

---

## Phase 6: Error Handling verbessern

### 6.1 Silent Exception in load_layout_gemini() fixen
**Dateien:** `scripts/tei/tei_unified.py`
**Problem:** L104-105: `except Exception: pass` verschluckt JSON-Decode-Fehler und File-I/O-Fehler ohne Logging.
**Fix:** `except (json.JSONDecodeError, OSError) as e: print(f"WARNUNG: {e}")`.

### 6.2 Gemini-Fehler differenzieren
**Problem:** L585-595: Jeder Gemini-Fehler fuehrt zum stillen Fallback auf Scaffold. Kein Unterschied zwischen API-Key-Fehler, Rate-Limit, Netzwerk-Fehler, Parse-Fehler.
**Fix:** Spezifische Exception-Handling:
- API-Key/Auth-Fehler -> Abbruch mit Fehlermeldung
- Rate-Limit -> Retry mit Backoff (existiert bereits als sleep)
- Netzwerk-Fehler -> Retry (1x)
- Parse-Fehler -> Fallback auf Scaffold + Warning

### 6.3 Imports in tei_validator.py aufraumen
**Problem:** lxml-Import in Funktionen statt am Modulanfang (L38, 61, 101, 103, 219).
**Fix:** Top-Level-Import mit try/except und klarer Fehlermeldung wenn lxml fehlt.

**Aufwand Phase 6:** 20 min

---

## Phase 7: Kleine Verbesserungen

### 7.1 Variablennamen verbessern
**Problem:** Einbuchstabige Namen: `m` (matched), `b` (bbox), `c` (child) in Schleifen.
**Fix:** `matched_item`, `bbox`, `child_elem`.

### 7.2 KNOWN_ENTITIES Struktur verbessern
**Dateien:** `scripts/config.py`
**Problem:** Name->GND hat Duplikate ("Jaspers" + "Karl Jaspers" -> gleiche GND). Dedup-Logik in tei_mapping_prompt.py (L248-252) noetig.
**Fix:** Optional -- GND-first Struktur mit Alias-Listen. Niedrige Prioritaet.

### 7.3 Lazy-Import Pattern modernisieren
**Problem:** Mutable global `_layout_qa_module` (L64-72).
**Fix:** `@functools.lru_cache(maxsize=1)` statt globalem State.

---

## Ausfuehrungsreihenfolge

```
Phase 1 (Bugs)           ██  5 min    -- sofort, keine Risiken
Phase 2 (Constants)      ████  15 min -- einfach, klare Verbesserung
Phase 3 (fix_gemini)     ██████  30 min -- groesster Impact
Phase 4 (Wrapping DRY)   █████  20 min -- haengt von Phase 3 ab
Phase 5 (step1 aufbrech) ██████  30 min -- unabhaengig von Phase 3/4
Phase 6 (Error Handling) ████  20 min -- unabhaengig
Phase 7 (Kleinkram)      ███  10 min  -- am Ende
                         ─────────────
                         Total: ~2.5h
```

## Validierungsstrategie

Vor jedem Refactoring-Schritt:
1. Pilot-Docs (2310, 2530, 1440) durch Pipeline laufen lassen
2. Output-XMLs speichern als Referenz
3. Nach Refactoring: `diff` gegen Referenz -- muss identisch sein
4. Validation: alle 3 muessen VALID bleiben

## Nicht im Scope

- Keine neuen Features
- Keine Aenderung der CLI-Argumente
- Keine Aenderung des Output-Formats
- Keine Aenderung der Gemini-Prompts
- Unit-Tests schreiben (eigenes Ticket)
