# TEI-Konformitaets-Audit + Welle-1-Implementierung — 2026-06-08

**Lane:** zbz · TEI-Struktur. **Branch:** cc3/session-2026-06-07.
**Ziel:** Pipeline erzeugt richtlinienkonforme TEI-Struktur fuer alle Objekte.

Dieser Bericht ersetzt auf dem Punkt `type="text"` die fruehere Annahme aus
`reports/tei-struktur-audit-2026-06-08.md` (siehe unten).

---

## 1. Audit (Workflow, 126 Agenten, adversarisch verifiziert)

Die Editionsrichtlinien wurden in 62 einzeln pruefbare Strukturregeln zerlegt, jede gegen
Pipeline-Output UND Generator-Code geprueft und adversarisch verifiziert (echter Verstoss vs.
Kuration vs. Teiltranskriptions-Artefakt vs. gleichwertiger Mechanismus). Ergebnis:

- **18 real_fixable** (echte, im Generator behebbare Verstoesse)
- 16 conformant, 14 curation (bewusster Scope), 1 gt_artifact, mehrere equivalent_valid

**Korrektur:** `div type="text"` ist KEIN Verstoss (Orphan-Wrapper, gleichwertig + schema-valide).
Die zaehl-basierte Erstanalyse hatte es faelschlich als richtlinienwidrig markiert.

## 2. Welle 1 — IMPLEMENTIERT + GETESTET (540 Suite gruen, keine Neugenerierung)

| Fix | Was | Datei | Wirkung |
|---|---|---|---|
| div-n-vs-type-exclusive | `@n` von jedem `<div>` mit `@type` entfernen | `_fix_div_n_type_exclusive` (tei_step3.py) | 73 BOTH-divs |
| figure-xmlid | fortlaufende `xml:id="figN"` fuer jede `<figure>` | `_assign_figure_ids` (tei_step3.py) | 0/52 -> alle |
| head-type-lemma | erste Ueberschrift bei Lexikonartikeln = `head type="lemma"` | tei_step1.py | 2 Docs (900, 3040) |

Plus Validator-Warnungen (nicht-blockierend, machen Defekte sichtbar + verhindern Rueckfall):
W15 (div type+n), W16 (figure ohne xml:id), W17 (leerer speaker).
Tests: `tests/test_tei_conformance.py` (8 neue, synthetisch/CI-faehig).

Verifiziert an echten Dateien (in-memory, nichts geschrieben): 1440 (2 BOTH-divs -> 0, 1 figure
-> id), 760 (31 figures -> figN), 140 (4 BOTH-divs -> 0). Validator feuert W15:2/W16:1/W17:23
auf 1440, Dokument bleibt valide.

## 3. Verfeinerung sp-speaker-p (groesster Defekt, NICHT blind gefixt)

62% der `<sp>` tragen leeres `<speaker/>`. Aber: GT 1440 kodiert Sprecher als
`<speaker><persName ref="GND:..."/>` (alternierend) — das GND-Linking ist mit E71 bewusst aus
der Pipeline. Bei anonymen Q/A-Interviews (kein Sprecher-Label im Scan) ist das leere
`<speaker/>` daher ein **Kurations-Slot** (Benennung stromabwaerts), kein reiner Bug. Nur
bold-beschriftete Interviews sind deterministisch fixbar. Braucht Scope-Entscheidung.

## 2b. Welle 2 — TEILWEISE IMPLEMENTIERT (543 Suite gruen, keine Neugenerierung)

| Fix | Was | Datei | Wirkung |
|---|---|---|---|
| title-main-sub | erste Dokument-`<head>` in `<title type="main">` wickeln | `_wrap_first_title` (tei_step3.py) | 207 Docs |
| foreign-lang | `<foreign xml:lang>` auf 639-2/B normalisieren (de->deu, fre->fra) | `_normalize_foreign_lang` (tei_step3.py) | gemischte Codes in 5+ Docs |

Plus Validator-Warnung W18 (foreign-Sprachcode nicht normalisiert). Tests in
`tests/test_tei_conformance.py`. Verifiziert in-memory: 1330/1180 erhalten Titel-Wrapping,
`de`->`deu` korpusweit vereinheitlicht (grc/lat erhalten), bereits-betitelte Heads uebersprungen.
title-main bewusst dokumentweit (erste head), nicht pro Seite -> genau ein Werktitel.

## 4. Offene Wellen (priorisiert, je konkrete Generator-Aenderung im Audit)

- **Welle 2 (Rest)**: note-footnote-inline-anchor (82%, Marker-Relokation), note-footnote-n
  (#sup-Marker, 12 Docs), lb-break-no-hyphenation (114 Faelle), review-bibl-in-head,
  pb-blank-page (`<p>[Leer]</p>`, type=blank mit ZBZ klaeren).
- **Welle 3** (mittlerer Aufwand, Re-Reassembly): table-row-cell (20 Docs), omit-titlepage-cv
  (62 Docs) + omit-author-byline (35 Docs, VORSICHT False Positives), omit-multicolumn,
  pb-n-supplied-brackets, space-vertical.
- **Welle 4** (riskant, zuletzt): div-chapter-units (Kapitel-Segmentierung; zuerst Validator-Warnung
  bauen + Streuung messen, dann erst Merge umstellen).

## 5. Operator-Entscheidungen

1. **Korpus-Neugenerierung freigeben** — Welle-1-Fixes wirken erst nach `tei_unified --all
   --reassemble` + `generate_edition_data`. ABER: andere Lanes kuratieren gerade tei_final/docs
   (Fussnoten 1910/290/90). Neugenerierung wuerde das ueberschreiben. -> Timing + Abstimmung.
2. **Welche Wellen umsetzen** — Welle 2 als Naechstes? (gleiche Methode: Code + Test, ohne Regen.)
3. **sp-speaker-p Scope** — leeres `<speaker/>` als Kurations-Slot akzeptieren (konsistent E71),
   oder Namen aus bold-Labels extrahieren? (GND-Form unerreichbar fuer die Pipeline.)
4. **Mit ZBZ klaeren:** type="blank" (valide, nicht in Richtlinien); MMSID im Header; graphic url
   vs. @facs (Richtlinie MUSS); 1520.xml ist kaputtes XML.

## 6. Was bewusst NICHT geaendert wird
Entitaeten/GND (E71); front/back/anchor/unclear (Kuration); graphic url (keine per-Abbildung-Pfade);
dedication/foreign-div (Vakuum/Disjunktion erfuellt).


## 7. Code-Review der Welle-1/2-Aenderungen (2026-06-08)

Unabhaengige Review (Multi-Agent-Workflow, 7 Finder-Angles, adversarisch verifiziert, 39 Agenten):
32 Kandidaten -> 3 verschiedene CONFIRMED-Befunde (Rest Duplikate). Zwei behoben, einer als
beabsichtigt dokumentiert, ein vierter als Vorbestands-Befund an den Operator.

Behoben:
1. `_wrap_first_title` waehlte den ersten `<head>` via `body.iter('head')` -- das steigt rekursiv
   auch in `<figure>` ab. Eine Bildunterschrift (`<figure><head>...`) vor der ersten Struktur-
   Ueberschrift waere faelschlich zum Werktitel gewickelt worden. Fix: nur Heads, deren Eltern
   `<div>`/`<body>` sind (Eltern-Map, da ElementTree keine Eltern-Zeiger hat). Regressionstest
   `test_title_skips_figure_caption`.
2. `_normalize_foreign_lang` und Validator-W18 hatten nicht deckungsgleiche Code-Mengen: der Pass
   hob nur {fr,de,en,it} + {fre,ger,dut,gre}, W18 meldete jeden Nicht-3-Letter-Code. Ein 2-Letter-
   Code ausserhalb der vier (es/la/pt) blieb dauerhaft gemeldet, ohne dass ein Re-Lauf ihn raeumen
   konnte; der Validator hielt zudem eine zweite, von Hand zu pflegende Kopie des Varianten-Satzes.
   Fix: eine gemeinsame Quelle `normalize_lang_code` in `tei_xml_utils` (2->3 + B->T + BCP-47-Region-
   Subtag), die BEIDE Seiten speist -- W18 meldet jetzt genau, was der Pass aendern wuerde. Tests
   `test_foreign_lang_extended_codes`, `test_foreign_lang_unknown_unchanged`,
   `test_normalize_lang_code_contract`.

Als beabsichtigt dokumentiert (kein Fix):
3. `_assign_figure_ids` ueberschreibt vorhandene xml:id bedingungslos. Das ist der Zweck:
   dokumentweite fortlaufende `fig1..figN` wie in der ZBZ-Referenz (760: fig3..fig35), statt der
   bedeutungslosen Pipeline-ids. Die Review fand keinen Pfad, auf dem eine kuratierte semantische
   figure-id mit Querverweis durch `assemble_document` laeuft (NER/Linking ist mit E71 entfernt,
   figure-ids sind keine Kurations-Flaeche). Ein Guard wuerde die beabsichtigte Neunummerierung
   aushebeln.

Vorbestands-Befund (NICHT Teil dieser Aenderungen, an Operator):
4. Genre-Tabelle inkonsistent: `tei_step1` bildet `debate` auf `type="interview"` ab,
   `tei_step3._GENRE_TO_DIV_TYPE` auf `"conversation"`; `_merge_page_divs` setzt den Typ nur, wenn
   keiner da ist, daher bleibt `debate` -> `"interview"` und der `"conversation"`-Zweig ist tot.
   Aendert die ausgelieferte div@type-Semantik -> Richtlinien-/Operator-Entscheidung, nicht
   eigenmaechtig (ausserhalb des Konformitaets-Scopes dieser Sitzung).

Suite nach den Fixes: 554 gruen. 15-Doc-Stichprobe weiterhin schema+regel-valide. Die in der
Stichprobe geraeumten Sprachcodes waren `de`->`deu` (deckte alt wie neu ab); die eigentliche
Luecke (2-Letter es/la/pt) ist durch die neuen Unit-Tests belegt, nicht in der Stichprobe.


## 8. Welle-2-Klassifikation gegen echte Daten (2026-06-08, Workflow + Messung)

Multi-Agent-Workflow (5 Investigatoren, je ein Item, grounded in GT + tei_final + Generator),
danach eine eigene Korpus-Messung. Ergebnis: KEIN Welle-2-Rest-Item ist aktuell ein sicherer
deterministischer Fix. Nichts umgesetzt -- bewusst, kein Versaeumnis.

| Item | Klasse | Grund / Befund |
|---|---|---|
| note-footnote-inline-anchor (82%) | COLLISION | Inline-Verankerung ist in Step 1 nicht ableitbar (Anker-Position fehlt im OCR-Text). Beruehrt aktive Fussnoten-Lane (`tei_footnote_demote.py`) + CER. Architektur-/Team-Entscheidung. |
| note-footnote-n (seiten-lokal vs dokumentweit) | COLLISION | Deterministisch ableitbar (dokumentweite Neunummerierung), ABER beruehrt Fussnoten-Lane + HOLD-Docs (1520/40) und die Konvention (seiten-lokal vs dokumentweit) ist ungeklaert. Konkreter Datenbefund: 1520 hat 20x `n="1"` (seiten-lokal, xml:id bleibt eindeutig). ZBZ-Konventions-Entscheidung noetig. |
| lb-break-no-hyphenation (114) | NON-DEFEKT | Korpus-Messung: echte nicht-aufgeloeste Silbentrennung (Bindestrich vor `<lb>` ohne `break="no"` + Kleinbuchstaben-Fortsetzung) = **0 Faelle**. Die 51 Bindestrich-vor-`<lb>`-Treffer sind Preis-/Zahlnotation + Komposita (`chef-d'oeuvre`, `Fr. 30.-`). Die 301 `<lb>`-gefolgt-von-Strich sind Listenpunkte/Seitenzahlen/Dialogstriche -- keine Silbentrennung. Kein sicherer Fix, keine sinnvolle Warnung (W19 verworfen: feuert 0x oder auf Nicht-Defekten). |
| review-bibl-in-head | CURATION_SLOT | `<bibl>` des rezensierten Werks erfordert freies Bibliographie-Parsen + GND (mit E71 aus der Pipeline). Nicht deterministisch ableitbar (analog sp-speaker). GT-Beleg: 2310/560 kodieren `<head><bibl ref="GND:...">`, Pipeline fragmentiert in `<head>`+`<p>`. |
| pb-blank-page | ZBZ_BLOCKED | Widerspruch belegt: Richtlinien (Editionsrichtlinien_ZBZ.md ~Z.208-210) + GT 1520 schreiben `<pb n=".."/><p>[Leer]</p>`. Die Pipeline (`tei_blank_marker.py`, [[E63]]) entfernt `<p>[Leer]</p>` und setzt `<pb type="blank"/>` -- weder Richtlinie noch Alternative. ZBZ muss entscheiden: Richtlinie auf `type="blank"` aktualisieren ODER Pipeline auf `<p>[Leer]</p>` zuruecknehmen. |

Fazit: Die deterministisch-sichere Konformitaets-Flaeche ist mit Welle 1 + dem umgesetzten Teil
von Welle 2 (div-n/type, figure-xmlid, head-lemma, title-main, foreign-lang) ausgeschoepft. Der
Rest sind Operator-/ZBZ-/Architektur-Entscheidungen oder Kurations-Slots, kein blind reparierbarer
Generator-Bug.
