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
| DEMOTE referenz-verifiziert -- **bereits angewandt** | 3 | erledigt (s.u.) |
| DEMOTE referenz-verifiziert -- **zurueckgehalten** | 6 | ZBZ-Freigabe |
| PRUEFEN (nicht im Ref-Body) | 11 | Handentscheid + Bild |
| PAGENUM (reine Zahl) | 1 | Seitenzahl, keine Fussnote |

## A. Bereits angewandt (referenz-verifiziert, klar, hoher Hebel)

Note -> `<p>` in `output/tei_final/`, gegen Schema validiert, Mirror regeneriert.

| Doc | xml:id | Laenge | Fidelity vorher | nachher |
|---|---|---|---|---|
| 290 | fn3-1 + fn4-1 | 1352 + 685 | 17,7 % | 2,6 % |
| 1910 | fn4-3 | 912 | 16,4 % | 7,7 % |
| 90 | fn6-1 | 609 | 7,6 % | 1,4 % |

Korpus-Fidelity-Mittel **3,99 % -> 2,79 %**, Median **1,83 % -> 1,58 %**, micro 2,70 %.
(290 fn4-1 wurde per strengem 200+-Zeichen-Treffer im Ref-Body nachverifiziert; der Erste-120-
Zeichen-Check hatte ihn nur wegen OCR-Rauschen am Blockanfang verfehlt.)

## B. Referenz-verifiziert, aber zurueckgehalten (ZBZ-Freigabe noetig)

Die Referenz fuehrt diese Bloecke als Body -- aber Doc 40 und 1520 enthalten **plausibel echte
lange Zitat-Fussnoten**, die die Referenz nur eingeebnet haben koennte. Editorischer Entscheid
liegt bei ZBZ. Demotion aller sechs senkt den Korpus-Mittelwert weiter auf ~2,9 % (1520:
3,6 -> 2,7 %, 40: 1,6 -> 1,2 %).

| Doc | n | Laenge | Textanfang |
|---|---|---|---|
| 40 | 1 | 743 | On me rappelait sans cesse hors de cette contemplation... |
| 1520 | 1 | 263 | Chaque mode de l'englobant en indique un autre... |
| 1520 | 1 | 536 | De l'etre du monde, par une rupture (es durchbrechend)... |
| 1520 | 1 | 538 | La philosophie, contrairement a la foi revelee... |
| 1520 | 2 | 557 | L'idee qu'une philosophie universelle est en train de naitre... |
| 1520 | 2 | 657 | La communication au sens de la vie avec autrui... |

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
