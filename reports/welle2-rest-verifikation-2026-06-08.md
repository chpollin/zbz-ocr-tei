# Welle 2 (Rest): evidenz-gegruendete Verifikation + ein sicherer Fix — 2026-06-08

**Lane:** zbz · TEI-Konformitaet / CER-Qualitaet · **Branch:** cc3/session-2026-06-07
**Methode:** dynamischer Workflow, 10 Agenten (5 Fixes x Recherche + adversarische Verifikation),
read-only gegen die 25 ZBZ-Referenz-TEIs + Editionsrichtlinien + Generator-Code. Jede Regel musste
aus der Ground Truth belegt werden; wo die Evidenz fehlt, ist die Klassifikation `needs_zbz` /
`risks_guessing` — kein erratener Transform.

## Ausgangsfrage

Ist „Welle 2 (Rest)" (note-footnote-inline-anchor, note-footnote-n, lb-break-no-hyphenation,
review-bibl-in-head, pb-blank-page) ein Satz blind anwendbarer Generator-Fixes?

## Befund: genau ein sicherer Fix, drei Diagnose-Faelle, eine ZBZ-Frage

| Fix | Klassifikation | Aktion |
|---|---|---|
| **note-footnote-n** (fuehrenden #sup-Marker aus dem Notentext entfernen) | **deterministic_safe** | **umgesetzt** (s.u.) |
| note-footnote-inline-anchor | risks_guessing | nur W19-Diagnose (kein Transform) |
| lb-break-no-hyphenation | risks_guessing | nur W19-Diagnose (kein Transform) |
| review-bibl-in-head | risks_guessing | nur W19-Diagnose (kein Transform) |
| pb-blank-page | needs_zbz | ZBZ-Entscheid noetig (s.u.) |

Das deckt sich unabhaengig mit der Einschaetzung der parallelen TEI-Struktur-Lane
(„Welle-2-Rest = kein sicherer Fix mehr"): vier der fuenf Items sind Kuration / Diagnose / ZBZ,
nicht deterministisch reparierbar. Der eine Unterschied: das Entfernen des redundanten
Fussnoten-Markers IST sauber belegbar und wurde umgesetzt.

---

## 1. Umgesetzt: fuehrenden #sup-Fussnoten-Marker entfernen

**Regel (Editionsrichtlinie Z.354):** Das hochgestellte Fussnotenzeichen wird NICHT als Zeichen im
Notentext wiedergegeben, sondern ausschliesslich ueber @n modelliert. **Belegt:** in den 25
Referenz-TEIs oeffnet keine einzige `<note place="foot">` mit einem fuehrenden
`<hi rendition="#sup">`-Marker; alle tragen die Marke nur via @n (z.B. 290.xml, 130.xml, 560.xml).

**Defekt:** vier Pipeline-Docs tragen den Marker als Literal im Body, z.B.
`<note place="foot" n="1"><lb/><hi rendition="#sup">1</hi> K. Jaspers ...`. Verifiziert auf der
Platte: **16 Notes in 4 Docs** (110: 13, 130/1140/1500: je 1), @n bereits korrekt gesetzt.

**Werkzeug:** [scripts/tei/tei_footnote_marker_strip.py](../scripts/tei/tei_footnote_marker_strip.py)
— eigenstaendiger, idempotenter Post-Pass auf `tei_final` (Backup + Mirror), im Muster von
`tei_footnote_demote.py`. Entfernt den Marker nur als ERSTES signifikantes Kind (hoechstens hinter
einem fuehrenden `<lb/>`), Marke <= 3 Zeichen, nur `place="foot"`; @n defensiv nur falls fehlend.
Mitten-im-Text-Hochstellungen (Exponenten, Ordinalia) bleiben unberuehrt.

**Verifikation:** 7 Unit-Tests (`tests/test_footnote_marker_strip.py`), Idempotenz-Recheck = 0,
alle 4 Docs nach Anwendung schema- und regel-valide (0/0 Fehler). Aendert die CER NICHT
(Fussnoten sind vom Vergleich ausgeschlossen, E5) — reiner Konformitaets-Gewinn. Voll reversibel
(Backup `output/_backup_pre_marker_strip/`).

**Warum standalone statt im Generator (tei_step3):** der Generator wird parallel von der
TEI-Struktur-Lane bearbeitet (uncommitted). Der Post-Pass auf `tei_final` (gitignored) ist
kollisionsfrei und nach einer Neugenerierung deterministisch re-applizierbar. Die Integration in
`tei_step1/_build_tei_body` (Marker gar nicht erst emittieren) bleibt der Lane offen — Spec unten.

---

## 2. Drei Diagnose-Faelle (kein Transform — Struktur nicht ableitbar)

Fuer diese drei ist die Soll-Form aus der GT belegt, aber die zur Umsetzung noetige Information
steht NICHT im Pipeline-Output. Ein Transform wuerde raten. Risikoarm ist je eine nicht-mutierende
Validator-Warnung **W19** ({line, message, rule}-Muster, lxml `getparent()`), die den Fall fuer die
menschliche ZBZ-Redaktion sichtbar macht. Diese Warnungen gehoeren in `tei_validator.py` (parallel
gehalten) und sind hier als anwendungsfertige Specs uebergeben:

- **note-footnote-inline-anchor:** GT setzt `<note place="foot">` INLINE am Bezugswort in `<p>`/`<bibl>`;
  die Pipeline setzt sie als Block-Kind von `<div>` (250/251). Die Bezugs-Wortposition fehlt fuer
  243/251 Notes (96.8 %) — nur 8 haben einen eindeutig per @n matchbaren Marker. Relozierung =
  Raten. W19 meldet block-positionierte Fussnoten; Verankerung gehoert in die ZBZ-Redaktion (Oxygen).
- **lb-break-no-hyphenation:** echte Silbentrennung wird als `<lb break="no"/>` kodiert. Die sichere
  Teilmenge (Bindestrich am Zeilenende + kleinbuchstabige Fortsetzung) erzeugt
  `tei_step1.insert_line_breaks` bereits (≈1264/1265 GT-konform). Die 51 ASCII-Rest-Faelle sind
  ueberwiegend KEINE Trennung (Preise `30.-`, Komposita `chef-doeuvre`, Spiegelstriche) — blindes
  `break="no"` wuerde Editionsdaten beschaedigen. W19 (nur ASCII-Bindestrich) meldet zur Handpruefung.
  *(Korrektur an der Recherche: GT hat 2075 `break="no"` / 9 `break="yes"` — nicht „3038/17" — und in
  9 Faellen behaelt die GT den Bindestrich UND setzt `break="no"`, was die Strich-Loeschung als
  nicht-deterministisch zusaetzlich belegt.)*
- **review-bibl-in-head:** GT zeichnet in `<div type="review">` den bibliografischen Datensatz als
  `<bibl ref="GND:...">` im `<head>` aus. Im Pipeline-Output ist der `<head>` in 3/4 Faellen NICHT
  der Datensatz (Zeitschriftentitel, Rubrik-Banner, fehlt). GND-Verlinkung ist per LLM verboten
  (deterministischer Authority-Lookup, [[feedback_no_llm_for_id_linking]]); die Titelspanne ist nicht
  deterministisch trennbar. W19 meldet review-divs ohne `<bibl>` im `<head>` als Kurations-Slot.

---

## 3. pb-blank-page: ZBZ-Entscheid (mit Schema-Beweis)

Die Editionsrichtlinie (Z.208-210) schreibt fuer Leerseiten ein schlichtes `<pb facs n/>` OHNE type
plus `<p>[Leer]</p>` vor. Der Generator (`tei_blank_marker.py`) setzt stattdessen `type="blank"`
(79 Vorkommen / 15 Docs) und laesst `<p>[Leer]</p>` weg. **Dispositiver Schema-Test (lxml + RelaxNG):**
ein blind eingefuegtes `<p>[Leer]</p>` macht `110_final.xml` **INVALID** („Did not expect element div
there"), `2330_final.xml` bleibt valide — derselbe naive Insert ist kontextabhaengig mal gueltig, mal
schema-brechend. Ein deterministischer Fix ist damit ausgeschlossen, bis ZBZ klaert: (a) `type="blank"`
behalten ja/nein, (b) `<p>[Leer]</p>` zwingend ja/nein, (c) falls ja — jede Leerseite in eigenem `<div>`.

---

## 4. Uebergabe

- **Umgesetzt (mein Scope):** `tei_footnote_marker_strip.py` + Tests, 16 Notes/4 Docs, schema-valide,
  reversibel, Mirror aktualisiert.
- **An die TEI-Struktur-Lane (gehaltene Dateien):** drei W19-Diagnosen in `tei_validator.py` (Specs oben);
  optional die Generator-Integration des Marker-Strips in `tei_step1._build_tei_body`.
- **An ZBZ:** pb-blank-page-Konvention (a/b/c oben); plus die bereits offenen Punkte (graphic url vs.
  @facs, MMSID-Header, `reference_tei/1520.xml` ist kaputtes XML).
- **Nicht zu tun:** kein Relozierungs-Transform, kein blindes `<bibl>`-Wickeln, kein blinder
  `break="no"`-Pass, kein blindes `<p>[Leer]</p>` — alle vier wuerden Struktur erraten.
