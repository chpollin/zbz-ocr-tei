# Fussnoten-Kuration: verschobener Fliesstext vs. echte Fussnoten

**Datum:** 2026-06-08 · **Lane:** zbz · CER · **Status:** evidenzbasierte Worklist

## Problem in einem Satz

Der KI-TEI-Schritt (Gemini, Stufe 6) zeichnet manchen **Fliesstext faelschlich als
`<note place="foot">` aus**. Da der CER-Vergleich Fussnoten ausschliesst (E5), faellt dieser
Text aus dem Vergleich und zaehlt als Loeschung -- das treibt die CER der betroffenen Objekte
nach oben, und es ist zugleich falsch ausgeliefertes TEI.

## Diskriminator (professionell, nicht geraten)

Kein Layout-Tag trennt echt/falsch sauber: die Docling-Basis **uebersieht** echte Fussnoten
(Doc 40: 0 statt 1, Doc 1520: 7 statt 38), Gemini **ueber-detektiert** (Doc 290: 4 statt 2).
Laenge/Prosa trennt ebenfalls nicht (echte Fussnoten sind 250-779 Zeichen lang).

**Verlaessliches Signal = die menschliche ZBZ-Referenz.** `extract_text_for_comparison` liefert
den Referenztext *ohne* Fussnoten. Steht der Text einer angeblichen Fussnote im **Body** der
Referenz, ist er beweisbar Fliesstext -> Demotion ist verifiziert, nicht geraten.

## Korpus-Bilanz (alle `<note place="foot">`)

| Klasse | Anzahl | Aktion |
|---|---|---|
| KEIN Eingriff: Quellenangabe `(Philosophie, I, p. 27)` | 26 | bleibt Fussnote |
| KEIN Eingriff: kurz | 8 | bleibt Fussnote |
| DEMOTE referenz-verifiziert -- **angewandt (alle)** | 14 Bloecke / 5 Docs | erledigt (s.u.) |
| PRUEFEN (nicht im Ref-Body) | 11 | Handentscheid + Bild |
| PAGENUM (reine Zahl) | 1 | Seitenzahl, keine Fussnote |

## A. Bereits angewandt (referenz-verifiziert, klar, hoher Hebel)

Note -> `<p>` in `output/tei_final/`, gegen Schema validiert, Mirror regeneriert.

| Doc | xml:id | Laenge | Fidelity vorher | nachher |
|---|---|---|---|---|
| 290 | fn3-1 + fn4-1 | 1352 + 685 | 17,7 % | 2,6 % |
| 1910 | fn4-3 | 912 | 16,4 % | 7,7 % |
| 90 | fn6-1 | 609 | 7,6 % | 1,4 % |
| 40 | fn10-1 | 743 | 1,6 % | 1,2 % |
| 1520 | fn81-2 u.a. (9) | 233-779 | 3,6 % | 2,1 % |

Korpus-Fidelity-Mittel **3,99 % -> 2,71 %**, Median **1,83 % -> 1,40 %**, micro 2,13 %
(BCa-CI [1,77 %, 3,82 %], kanonischer cer_statistics_full-Lauf 2026-06-08).
40 + 1520 wurden auf Operator-Anweisung („setze alles um", 2026-06-08) per `--include-hold`
angewandt -- referenz-verifiziert und **voll reversibel** (Backup, idempotentes Tool, Git).

## B. Referenz-verifiziert -- angewandt (vormals zurueckgehalten; ZBZ-Bestaetigung offen)

Doc 40 (1 Block) und 1520 (9 Bloecke) waren referenz-verifiziert, aber editorisch heikel
(1520 = Jaspers-Anthologie mit plausibel echten langen Zitat-Fussnoten). Auf Operator-Anweisung
„setze alles um" (2026-06-08) per `tei_footnote_demote --apply --include-hold` angewandt, beide
schema-valide. **Voll reversibel:** Backup unter `output/_backup_pre_footnote_demote/`, idempotentes
Tool, Git. Fuer ZBZ bleibt der Body/Fussnote-Entscheid zu bestaetigen; bei Ablehnung Rueckbau aus
dem Backup. Das `>=150`-Zeichen-Schiebefenster fand in 1520 **9** statt der frueher per
Erste-120-Check geschaetzten 5 Bloecke (es erkennt auch Bloecke mit OCR-Rauschen am Anfang).

## C. Pruefen (nicht im Ref-Body -- echte Fussnote ODER ausserhalb des Referenz-Ausschnitts)

Hier fehlt die Evidenz: entweder echte Fussnote (dann bleiben) oder Mehrtext ausserhalb der
selektiven Referenz (dann kein Fehler). Braucht Bildansicht.

| Doc | n | Laenge | Textanfang |
|---|---|---|---|
| 290 | 2 | 311 | 1. Die geistige Situation der Zeit, Verlag W. de Gruyter, Berlin, 1931... (wirkt wie echte bibliografische Fussnote) |
| 1910 | 1 | 470 | Eine Introspektion, die "wissenschaftlich" sein wollte... (100-Zeichen-Fenster traf den Ref-Body, aber strenger 200+-Test scheiterte -> bewusst NICHT demoted, koennte echte Fussnote sein) |
| 1180 | 1 | 156 | Ce n'est pas, je crois, un hasard si le terme de "loi"... |
| 1440 | 1 | 335 | "Das ist der Siegeszug der Vernunft, der Gerechtigkeit..." |
| 1520 | 1 | 233 | Telle est la passion de l'existence... |
| 1520 | 1 | 317 | L'englobant, c'est ce en quoi tout etre est pour nous... |
| 1520 | 1 | 350 | Mais dans la mesure ou nul homme n'est purement... |
| 1520 | 1 | 779 | Lorsqu'on cherche a la transmettre, la verite suscite... |
| 3040 | 1 | 732 | Si les themes et les objets de Nicole, ses theses... |
| 3040 | 2 | 406 | - Les Essais de morale, dont sont tirees la plupart des citations... |

## D. Seitenzahl als Fussnote

| Doc | n | Inhalt | Aktion |
|---|---|---|---|
| 1910 | 2 | `253` | Druck-Seitenzahl, keine Fussnote -- entfernen oder als `<pb n="253"/>` fuehren (CER-Wirkung ~0) |

## Methode reproduzierbar

```python
# extract_text_for_comparison(ref) liefert Body OHNE Fussnoten (E5).
# Eine <note place=foot> ist verifizierter Fliesstext, wenn die ersten 120 Zeichen
# ihres Textes im Referenz-Body vorkommen.
inref = len(note_text) >= 120 and note_text[:120] in reference_body_text
```
