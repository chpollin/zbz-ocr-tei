---
title: Testplan ZBZ → teiCrafter (Demo-Gate)
project: zbz-ocr-tei
method: Promptotyping
created: 2026-06-07
updated: 2026-06-07
language: de
related: [oekosystem-synthese, ../../ResearchTools/teiCrafter/knowledge/testing]
---

# Was müssen wir alles testen? — ZBZ→teiCrafter, Demo-Gate

Bezug: Erfolgskriterium aus `goals.md` — je ein reales ZBZ- und
SZD-Objekt end-to-end im Browser (öffnen → zeilenweise korrigieren → Person/Ort/Werk mit Normdaten
annotieren → byte-treu speichern). Dieser Plan deckt die **ZBZ-Hälfte** ab.

Spalten: **Jetzt?** (sofort testbar ✓ / blockiert ✗ / nur synthetisch ⚠) · Beleg/Tool.

---

## T1 — Bild-Kette (`<graphic>`, M2.4→M2.2)
| # | Test | Jetzt? | Tool/Beleg |
|---|---|---|---|
| 1.1 | Injiziertes `<graphic>` validiert gegen `zbz_hersch.rng` | ✓ | `tei_validator --doc` (Schema def. Z.3518) |
| 1.2 | Surface→Bild-Mapping korrekt (contiguous: 1000/1330/1540) | ✓ | surfaces vs `ls docs/images` |
| 1.3 | **Edge Case 2310** (facs_2/3, `p001` Waise ohne Surface) korrekt behandelt | ✓ | iterieren über `<surface>`, `K` aus xml:id |
| 1.4 | Alle Seiten-URLs der Demo-Docs liefern HTTP 200 | ✓ | `curl -I …github.io/…/<id>_p{KKK}.png` |
| 1.5 | Cross-Origin: Bild rendert in teiCrafter (andere Pages-Origin) | ✗ (M2.2) | OSD `type:'image'` + `<img>` |
| 1.6 | Nach Injektion Round-Trip nur um `<graphic>`-Zeilen verändert | ✓ | `diff` SoT vs injiziert |

## T2 — Verlustfreiheit (Kern-Invariante, H4)
| # | Test | Jetzt? | Tool |
|---|---|---|---|
| 2.1 | Öffnen+Speichern unverändert = byte-identisch (285+) | ✓ | `node test/tools/roundtrip_sweep.mjs` (294/294) |
| 2.2 | Eine Zeile editieren → nur dieser Offset ändert sich | ✓ | `edit_fidelity.mjs` |
| 2.3 | Re-Run nach **jeder** Änderung (Regression) | ✓ | M4.3, CI |
| 2.4 | Annotierte Datei byte-clean durch `tei-document/standoff.js` | ✗ (M3) | M4.4 |

## T3 — Laden & Struktur (M1.1/M2.1)
| # | Test | Jetzt? | Tool |
|---|---|---|---|
| 3.1 | Alle 285 laden, 0 Parse-Fehler | ✓ | `node test/tools/hersch_loadability.mjs` (285/285) |
| 3.2 | Folio-Zahl = pb/surface-Zahl; Zellen-/Zonen-Zahl plausibel | ✓ | Loadability-Report |
| 3.3 | Leerseiten `<pb type="blank"/>` laden ohne Crash | ✓ | Docs mit blank-Marker |
| 3.4 | Große Docs (Monografien, hunderte Seiten) laden performant | ✓ | tier4-Monografien |

## T4 — Element-Rendering (M2.3) — die sechs + Struktur
| Element | im ZBZ-Korpus | Jetzt? | Test-Doc |
|---|---|---|---|
| `hi` | 140 Docs | ✓ | 2310 (16×), 1000 |
| `foreign` | 29 Docs | ✓ | 2310 (`quer zur Zeit`) |
| `note` | 86 Docs | ✓ | 1000, 2310 |
| `figure` | 52 Docs | ✓ | 1000 (2×) |
| `choice` | **6 Docs** | ✓ | **110**, 1240, 1420, 1490, 1500, 1510 |
| `unclear` | **0 Docs** | ⚠ | **nicht im ZBZ-Korpus** → synthetisch o. N/A |

> Befund: `unclear` ist korpus-weit nie ausgezeichnet → auf realem ZBZ-Material nicht prüfbar. Ehrlich
> als „nicht abgedeckt (ZBZ)" melden; falls nötig, synthetisches Testdoc (teiCrafter-Testsuite).
> Auch testen: `<lb>`/`@n`, mehrspaltige Layouts, Sonderzeichen (FR-Akzente, „«»").

## T5 — Faksimile / Zonen-Verknüpfung (F.1)
| # | Test | Jetzt? |
|---|---|---|
| 5.1 | Klick Zeile → Zone hervorgehoben (und umgekehrt), `@facs` bidirektional | teilw. (Highlight ja, Bild ✗ bis M2.2) |
| 5.2 | Zonen-Pixelkoordinaten decken sich mit dem Bild | ✗ (M2.2) |
| 5.3 | Seite mit Bild aber ohne Zonen (Waise 2310 p001) bricht nicht | ✗ (M2.2) |

## T6 — Annotation / standOff (H3, Demo-Gate-Kern)
| # | Test | Jetzt? |
|---|---|---|
| 6.1 | Person/Org/Event anlegen, umbenennen, löschen | ✓ (vorhanden) |
| 6.2 | **Ort** (`place`/`placeName`) anlegen | ✗ (M3.1) |
| 6.3 | **Werk** (`title`/`bibl`) anlegen | ✗ (M3.2) |
| 6.4 | Normdaten-`@ref` (GND/GeoNames/Wikidata) auf alle Typen | ✗ (M3.3) |
| 6.5 | Mention-Linking `<name ref="#id">` auf neue Typen | ✗ (M3.4) |
| 6.6 | ZBZ-TEI hat seit E71 KEINE Entitäten → frisch annotieren, dann byte-clean speichern | ✗ (M3/M4.4) |

## T7 — Speichern / Persistenz (H2-Risiken aus frontend-gaps)
| # | Test | Jetzt? |
|---|---|---|
| 7.1 | File System Access (Chromium) schreibt in-place | ✓ |
| 7.2 | Download-Fallback: „Gespeichert" darf NICHT lügen (H2) | ✓ |
| 7.3 | TEI-XML-Edit überschreibt NICHT das ganze `_final.xml` (H1, aus Code abgeleitet, **unreproduziert**) | ✓ — **Priorität** |

## T8 — Deployment / Browser
| # | Test | Jetzt? |
|---|---|---|
| 8.1 | teiCrafter-Origin lädt zbz-Bilder cross-origin (kein mixed-content/CORS-Block) | ✗ (M2.2) |
| 8.2 | Performance großer Editionen | teilw. |

## T9 — A11y / UX (sekundär, frontend-gaps H3-H5)
Layout-Editor tastaturbedienbar (heute nur Maus) · QA-Seitennavigation für ~4.100 Seiten · Modal-Fokus-Trap.

---

## Was JETZT erledigt werden kann (Liste + Begründung)
1. **`<graphic>`-Injektion als non-destruktives Demo-Artefakt** (4 Docs in neuen Ordner, SoT unberührt).
   *Begründung:* macht T1.1/1.6 und (sobald M2.2) die ganze Bildkette testbar, ohne die gitignorete
   SoT `output/tei_final/` zu riskieren. Der *dauerhafte* Einbau gehört in die TEI-Generierung
   (sonst überschreibt `generate_edition_data.py` den Mirror) — das ist eine separate Pipeline-Entscheidung.
2. **Schema-Validierung der Injektion** (T1.1). *Begründung:* bevor M2.2 gegen reale
   Dateien baut, muss feststehen, dass `<graphic>` im `<surface>` valide ist.
3. **Render-Check-Docset festzurren** (110 für `choice`; synthetisch/N/A für `unclear`). *Begründung:*
   sonst bleibt die M2.3-Abdeckung lückenhaft und unehrlich.
4. **zbz-Doku-Widersprüche fixen** (README E-Zähler „E1–E76"→E79; `pipeline.md`/`methodik.md` 4→3 Status).
   *Begründung:* Wissenspflege (H6/M6.3); reine Doku, kein Code-Risiko.
5. **Live-Render-Check (M2.3)** — sobald M2.2 steht. *Begründung:* braucht Browser + Bild-Support;
   liefert die ausgefüllte T4/T5-Tabelle.

## Zwei ehrliche „können-wir-nicht-testen"
- **`unclear`** ist im ZBZ-Korpus nirgends ausgezeichnet (0 Docs).
- **„Bild sichtbar"** bei geöffneten Dateien bleibt blockiert bis **M2.2**.

## Re-runnable Belege
`grep -rl "<choice" output/tei_final/*.xml` (6) · `grep -rl "<unclear" …` (0) ·
`grep -n "graphic" data/schema/zbz_hersch.rng` (Z.3518) ·
`node test/tools/{roundtrip_sweep,hersch_loadability}.mjs` (teiCrafter).
