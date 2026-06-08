# TEI-Struktur-Audit + Implementierung — 2026-06-08

**Lane:** CC3 (zbz-ocr-tei, TEI). **Branch:** cc3/session-2026-06-07.
**Ausgangsfrage:** Erzeugt die Pipeline für alle Objekte die richtige TEI-Struktur?
Wo weicht sie von den 25 ZBZ-Vergleichsdateien ab — und was davon ist ein echter Defekt?

---

## 1. Was implementiert wurde

### Neues Werkzeug: `scripts/eval/structure_audit.py`
Vergleicht die strukturellen TEI-Bausteine (pb, note, figure/graphic, div@type,
front/back, anchor …) je Objekt: Pipeline (`output/tei_final`) gegen Ground Truth
(`data/source/reference_tei`), für die 25 Objekte, bei denen beides vorliegt.

```
python -m scripts.eval.structure_audit                 # Tabelle + Summen
python -m scripts.eval.structure_audit --doc 760       # ein Objekt
python -m scripts.eval.structure_audit --json PFAD     # JSON-Report
```

Bewusst **nur Diagnose, kein Pass/Fail-Gate**: Die 25 Referenzdateien sind
Teiltranskriptionen — reine Zähl-Deltas beweisen keinen Fehler. Ein Hart-Gate auf
Zählgleichheit wäre falsch. Schicht-2 des geplanten Test-Gerüsts ist damit ein
Diagnose-Tool, das automatisch mitwächst, wenn mehr Referenzdateien dazukommen.

### Bereits vorhanden (kein Duplikat gebaut)
- **Schicht-1-Gate** (alle 285 schema- + regelvalide): `test_tei_schema.py::test_final_doc_valid`.
- **Korpus-Gesundheit heute:** 285/285 valide, 0 Fehler, 14 mit Warnungen
  (Validator über `tei_unified`, 7,8 s).

---

## 2. Befund: die Struktur ist gesund, die Abweichungen sind erklärbar

Audit über 24 vergleichbare Objekte (1520 übersprungen, s. u.):

| Baustein | Ground Truth | Pipeline | Delta | Bewertung |
|---|---|---|---|---|
| pb | 314 | 302 | −12 | Teiltranskription / Doppelseiten (760, 30) |
| note | 11 | 17 | +6 | Fußnoten-Überdetektion, aber durch Teil-GT verfälscht |
| figure | 36 | 38 | +2 | gleichwertig |
| graphic | 36 | 6 | −30 | **andere Methode**, kein Defekt (s. u.) |
| front | 6 | 0 | −6 | bewusste Kuration |
| back | 4 | 0 | −4 | bewusste Kuration |
| anchor | 10 | 0 | −10 | bewusste Kuration |
| div | 104 | 104 | 0 | gleich |

**Kein einziger großer Unterschied ist ein blind reparierbarer Bug.** Jeder hat eine
erklärbare Ursache:

- **graphic −30:** Die Referenz verknüpft Abbildungen über `<graphic url="*.tif"/>`
  (eingebettete Bilddatei), die Pipeline über `@facs` (Verweis auf Faksimile-Zonen).
  Beides ist gültiges TEI — andere Methode, keine fehlende Abbildung.
- **front/back/anchor:** in der Pipeline absichtlich nicht automatisch erzeugt
  (Kuration); ohnehin selten in der Ground Truth.
- **note +6:** Streut auf 1910 (+3), 3040 (+3), je +1 in mehreren. Durch die
  Teiltranskription der Referenz nicht sicher als „Überdetektion" beweisbar; in
  1520/40/3040 gibt es echte Fußnoten. Nicht sicher auto-fixbar — Einzelfall-Sichtung nötig.
- **pb −12:** Konzentriert in 760 (38→20) und 30 (8→4): Doppelseiten / Lesereihenfolge,
  zusätzlich Umfang der Teiltranskription. Einzelfall.

### Datenbefund (nicht Pipeline)
`data/source/reference_tei/1520.xml` ist **nicht wohlgeformtes XML** (mismatched tag,
Zeile 6936). Das ist eine Referenzdatei der ZBZ, kein Pipeline-Output. An ZBZ melden.

---

## 3. Eine belegte, redaktionelle Empfehlung: `div type="text"`

`div @type` in Pipeline vs. Ground Truth:

```
Pipeline:      text 54 | (none/n) 33 | interview 10 | review 5 | speech 1 | entry 1
Ground Truth:  (none/n) 90 | review 4 | translation 3 | interview 2 | otherEdition 1
               | reprint 1 | text 1 | entry 1 | bibliography 1
```

**Beleg aus den Editionsrichtlinien (`Editionsrichtlinien_ZBZ.md`):**
- Z. 147: „Kapitel und Unterkapitel … als eigene Einheiten: `<div n="1">`, `<div n="2">`."
  → generische Gliederung läuft über **`@n` (nummeriert)**.
- Die `@type`-Werte sind **abschließend aufgezählt** (review, interview, conversation,
  entry, bibliography, translation, reprint, otherEdition, dedication, foreign, editorial).
- **`type="text"` kommt in den Richtlinien nicht vor.**

**Ursache im Code:** Regel **R5** im Validator verbietet `div` ohne `type` *oder* `n`.
`_fix_orphaned_body_children` (tei_step3.py) wickelt lose Blöcke deshalb in
`<div type="text">`. config.py vermerkt `type="text"` selbst als „nicht in Richtlinien".

**Empfehlung (nicht eigenmächtig ausgeführt — betrifft 285 ausgelieferte Dateien + die
teiCrafter-Lane):** Auto-Wrapper auf `<div n="…">` umstellen (richtlinienkonform, erfüllt
R5 weiterhin) und `text` aus den erlaubten Typen entfernen. Das Gleiche gilt für die
pipeline-eigenen, nicht-aufgezählten Typen `speech`, `redactional`, `conference`, `letter`,
`preface`, `sub-section`. **Operator-Entscheidung**, weil es das ausgelieferte Korpus ändert
und eine Neugenerierung aller Objekte erfordert.

---

## 4. Status der ursprünglichen Plan-Phasen

- **A — Doku-Drift:** erledigt (revisionDesc, toter Verweis, Scope-Notiz, ALMA-Kommentar,
  Docstring, Validator-Kommentar).
- **B/C — Header-Metadaten / Nachspann:** bewusst verworfen (ZBZ-Domäne, O8).
- **D — front/anchor/unclear ehrlich:** in Prompt/Doku als Kuration gekennzeichnet.
- **E — Test-Gerüst:** Schicht 1 existierte bereits (Schema-Gate); Schicht 2 jetzt als
  `structure_audit.py` gebaut.

## 5. Offen / Operator

- Migration `type="text"` → `n` über das Korpus (redaktionelle Freigabe + Neugenerierung).
- `1520.xml` (Ground Truth) ist kaputt — an ZBZ melden.
- 14 Validator-Warnungen: überwiegend by-design (W3/W6/W10); Aufschlüsselung auf Wunsch.
- Spec-Konflikt MMSID im Header (Richtlinien fordern ihn, Pipeline liefert ihn bewusst nicht)
  — mit ZBZ klären.
