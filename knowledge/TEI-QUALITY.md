---
type: knowledge
created: 2026-03-26
updated: 2026-03-26
tags: [zbz-ocr-tei, tei, validation, schema, quality]
status: active
---

# TEI-Qualitaet

Schema-Validierung der Pipeline-TEIs gegen `zbz_hersch.rng` (TEI P5 v4.10.2, projektspezifisch).

**Dependencies:** [PIPELINE](PIPELINE.md) (TEI-Stufen), [CER-BENCHMARK](CER-BENCHMARK.md) (OCR-Metriken)

---

## Aktueller Stand (Maerz 2026)

**285/285 Docs valide** gegen `zbz_hersch.rng` (nach Schema-Fix).

| Metrik | Wert |
|--------|------|
| Dokumente | 285 |
| Valid | 285 (100%) |
| Invalid | 0 |
| Mit Warnings | 82 |
| Schema | zbz_hersch.rng (TEI P5 v4.10.2) |

---

## Fix-Verlauf

### Fix-001: ref-Pattern (2026-03-26)

**Vorher:** 50 valid, 235 invalid
**Nachher:** 285 valid, 0 invalid

**Root Cause:** Schema erzwang `ref="GND:[0-9A-Za-z\-]+"`. Pipeline injiziert `ref="#zbz-p.NNN"` (projektinterne IDs). RelaxNG-Kaskade machte alle 235 Docs mit zbz-Refs komplett invalid (nicht nur das ref-Attribut).

**Fix:** ref-Pattern in `data/schema/zbz_hersch.rng` erweitert:
```
(GND:[0-9A-Za-z\-]+|#zbz-[a-z]+\.[0-9]+)
```
An 3 Stellen: `bibl/@corresp`, `orgName/@ref`, `persName/@ref`.

**Scheinbare Nebenfehler (Kaskaden-Artefakte):** Die 5 Docs mit idno/langUsage/biblStruct-Fehlern waren keine eigenstaendigen Fehler, sondern RelaxNG-Kaskaden. Nach dem ref-Fix sind auch diese Docs valide.

### Fix-002: Heuristische lb-Injection (2026-03-26)

**Vorher:** 46 Docs mit Warning W6 (keine `<lb/>` Elemente)
**Nachher:** 0 Docs mit W6, Warnings insgesamt 82 -> 37

**Root Cause:** Mistral OCR liefert Text ohne Zeilen-Umbrueche innerhalb von Absaetzen. `insert_line_breaks()` in tei_step1 braucht `\n` im Input. Nur 51 Docs hatten Step 2 (Gemini Refinement) durchlaufen, das lb injiziert.

**Fix:** Post-Assembly-Funktion `_inject_heuristic_lb()` in `scripts/tei/tei_step3.py`:
- Nur fuer `<p>` Elemente OHNE bestehende `<lb/>`
- Zeilenumbruch alle ~60 Zeichen an Wortgrenzen
- Non-Regression: Absaetze mit bestehenden lb werden nicht veraendert
- 10.635 lb-Elemente in 46 Docs injiziert

---

## Warnings (informativ, nicht blockierend)

| Regel | Docs | Beschreibung |
|-------|------|-------------|
| W9 | 17 | Entity-Tags ohne ref |
| W10 | 10 | Nur persName, keine orgName/placeName |
| W3 | 5 | facsimile/pb Mismatch |
| W11 | 2 | Zu viele top-level divs |
| W7 | 2 | graphic ohne url |
| W4 | 1 | Leere div-Elemente |

---

## Referenz-TEI Validierung

25 ZBZ-Referenz-TEIs (Transkribus Ground Truth) gegen `zbz_hersch.rng`:

**17/25 valide** (68%). 8 invalide Referenz-TEIs zeigen, wo das Schema strenger ist als ZBZs eigene Praxis.

### Abweichungen in Referenz-TEIs

| Fehlertyp | Docs | Details |
|-----------|------|---------|
| `<space>` ohne `<desc>` Child | 4 | 40, 290, 830, 1330 |
| `<back>` nicht erwartet | 4 | 40, 300, 830, 1520 |
| `<foreign>` nicht erwartet | 1 | 300 |
| body/div-Struktur | 2 | 1910, 3040 |

**Interpretation:** Die Referenz-TEIs sind manuell erstellt und verwenden Elemente, die im projektspezifischen Schema (absichtlich) ausgeschlossen sind. Kein Pipeline-Bug.

---

## Daten und Werkzeuge

| Artefakt | Pfad |
|----------|------|
| Schema | `data/schema/zbz_hersch.rng` |
| Validator | `scripts/tei/tei_validator.py` |
| Diagnostik-JSON | `docs/data/diagnostik_tei.json` |
| Diagnostik-Log | `docs/data/diagnostik_log.json` |
| Diagnostik-UI | `docs/infrastruktur/diagnostik.html` (Tab "TEI-Qualitaet") |
| Validation Report | `output/tei_unified/validation_report.json` / `.html` |

### CLI-Befehle

```bash
python -m scripts.tei.tei_validator --all --html-report   # Alle 285 Docs validieren
python -m scripts.tei.tei_validator --doc 2310             # Einzelnes Doc
python -m scripts.tei.tei_validator --compare-ref          # Referenz-Vergleich
```

---

*Erstellt: 2026-03-26*
