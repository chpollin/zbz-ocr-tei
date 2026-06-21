---
title: Arbeitsjournal
type: journal
project:
  name: zbz-ocr-tei
  repository: https://github.com/chpollin/zbz-ocr-tei.git
method:
  name: Promptotyping
  url: https://dhcraft.org/Promptotyping/
status: draft
language: de
created: 2026-01-29
updated: 2026-06-10
tags: [zbz-ocr-tei, journal]
template:
  name: Vorlage Journal
  version: 0.2
  url: https://dhcraft.org/Promptotyping/promptotyping-document/journal
related: [decisions, index]
---

# Arbeitsjournal

Chronologische Entwicklungsgeschichte des Projekts, neueste Eintraege zuerst. Das Journal
verdichtet je Sitzung Anlass, Verlauf, Entscheidungen und Stand. Es ist weder Git-Log noch
Sitzungsprotokoll: einzelne Commits stehen in der Git-History, Entscheidungs-Begruendungen
im Register [decisions.md](decisions.md).

## Format-Kontrakt

Jeder Eintrag wird am Sitzungsende geschrieben; beim Wiedereinstieg wird zuerst der oberste
Eintrag gelesen. Neue Eintraege stehen immer direkt unter der Ueberschrift "Eintraege".
Bestehende Eintraege werden nie nachtraeglich geaendert; Korrekturen sind neue Eintraege
mit Verweis auf den alten.

Feste Feldreihenfolge pro Eintrag: **Anlass** (1 Satz: warum diese Arbeit jetzt),
**Ziel** (1 Satz), **Verlauf** (1 bis 4 Absaetze, mit Belegstellen), **Entscheidungen**
(je Punkt: was, warum, verworfene Alternative; Registernummer falls vorhanden),
**Stand** (1 Absatz, allein lesbar; optional Commit-Hash als Savepoint),
**Naechste Schritte** (nummeriert), **Dead Ends** (optional, mit Begruendung).
Pflichtfelder: Anlass, Ziel, Verlauf, Stand, Naechste Schritte.

Formregeln: formell und projektbezogen; Fachbegriffe und Abkuerzungen beim ersten
Auftreten im Eintrag erklaeren; Zahlen mit Bezugsgroesse. Nicht hinein gehoeren:
Spezifikation (gehoert in [decisions.md](decisions.md) bzw. die Fach-Docs), Code-Diffs
und Commit-Texte, stundengenaue Protokolle, Selbstbewertungen, Notizen ueber die Pflege
der Dokumentation selbst, Personennamen (Rollen und Organisationen verwenden).

Die Sitzungen 1 bis 68 stehen unveraendert im Kompakt-Archiv weiter unten (eine Zeile
pro Sitzung); ab Sitzung 69 gilt die Eintragsstruktur der Vorlage Journal v0.2.

## Eintraege

### 2026-06-21 Sitzung 72: Unabhaengige Verifikation der ZBZ-Lieferung + Konsolidierungsbericht an die Forschungsleitstelle

**Anlass.** Nach Abschluss der Order (Sitzung 71) war der ausgelieferte Bestand unabhaengig
nachzupruefen und der Stand vollstaendig an die Forschungsleitstelle zu berichten, inklusive
des fuer die Vault-Session bestimmten Wissens-Deltas.

**Ziel.** Die drei Konformitaets-Gates auf dem realen Bestand reproduzieren und die Reichweite
des Konformitaets-Gates praezise benennen.

**Verlauf.** Die drei Pruefungen wurden direkt auf `output/tei_final` (285 Dateien) ausgefuehrt:
Schema plus Projektregeln (`tei_validator --all --dir output/tei_final`) 285 valide / 0 invalide /
145 mit nicht-blockierender Warnung; ZBZ-Konformitaet (`--conformity`) 285 konform / 0 Verletzungen;
die committeten Gates `test_tei_schema.py` und `test_zbz_conformity.py` zusammen 583 passed. Befund
zur Reichweite: der Bestand traegt 0 Dateien mit `ref="GND:"`, 6 nackte `<persName>` und 400 `<bibl>`
(ueberwiegend Abbildungs- und Quellenverweise, keine Normdaten-Verknuepfung). Die entitaetsbezogenen
Konformitaetsregeln (Z1-Z4) laufen also auf einem authority-freien Korpus leer; das Gate wird erst
scharf, sobald kuratierte Inline-GND-Dokumente durchlaufen.

**Stand.** Lieferbestand unabhaengig verifiziert, Ergebnis deckt sich mit den committeten Tests aus
Sitzung 71. An die Forschungsleitstelle berichtet: handoff bereinigt (Vor-Order-Staende entfernt) und
um das Vault-Wissens-Delta ergaenzt (Inline-GND ersetzt standOff in den Vault-Dokumenten,
teiCrafter-Atom-Korrektur, Entscheidungen A/B und E87 als aufgeloest). Keine offenen Gates, Lane ruht.

**Naechste Schritte.**
1. teiCrafter-Ausgabemodell auf Inline-GND umstellen (lane teicrafter-editor); danach den
   Konformitaets-Gate erstmals auf kuratierten Output anwenden.
2. ZBZ-Rueckfragen O27 (Bildunterschrift-Widerspruch), O13 (Schlagworte), O8 (Header-Metadaten)
   ueber den Operator klaeren.

### 2026-06-21 Sitzung 71: ZBZ-Order umgesetzt -- Inline-GND-Schema (E88), Konformitaetspruefung, Seitenbild-Anbindung (E89)

**Anlass.** Die Forschungsleitstelle hat das uebergebene ZBZ-Material ausgewertet und drei
Aufgaben erteilt (order-zbz-ocr-tei.md): das Auszeichnungsmodell auf die ZBZ-Editionsregeln
festlegen, die ZBZ-Konformitaet des ausgelieferten Bestands nachweisen, und die Seitenbild-
Anbindung nach ZBZ-Regeln erzeugen. Korrigiert Sitzung 70, in der das standOff-Modell (E87)
gebaut wurde, bevor das ZBZ-Material vorlag.

**Ziel.** Die drei Auftragspunkte umsetzen und je gegen committete Artefakte verifizieren,
Inline-GND als maßgebliches Liefermodell verankern.

**Verlauf.** (1) Modell: Der vollstaendige Schema-Diff zeigte, dass das aktive Schema die
ZBZ-Pruefvorlage plus E68 plus E87 ist; jede Diff-Zeile ist ein E68- oder E87-Element plus drei
`@ref`-Pattern-Stellen. Der ausgelieferte Bestand ist seit E71 entitaetenfrei (kein standOff,
kein `#zbz-`, kein `<name>`), das Entfernen von E87 daher risikolos. E87 zurueckgenommen, die
`@ref`-Pattern auf GND-only verengt; aktives Schema jetzt exakt ZBZ-Pruefvorlage + E68
(Restdiff nur noch E68, verifiziert). 285/285 weiterhin valide, standOff-Guard-Test neu. (2)
Konformitaet: Befund, dass das alte Richtlinien-Arbeitsexemplar (E49) byte-identisch zur neuen
ZBZ-README ist und der Validator viele Editionsregeln schon als R/W-Regeln kodiert. Ergaenzt um
die Inline-GND-Modellregeln, die ein RelaxNG nicht ausdruecken kann (Normdaten nur GND, nur
Person/Org/Werk, Rendering-Vokabular, `pb facs/n`), als `zbz_conformity.py` mit
`--conformity`-Modus. 285/285 konform, 0 Verletzungen. (3) Seitenbild: Befund, dass `<pb facs>`
die bindende Form ist (alle 285), das Surface-`<graphic>` aber fehlte bzw. der Leerseiten-
Platzhalter `{N}.png` auf eine nicht existente Datei zeigte. Jede Surface bekommt nun `<graphic
url="{doc_id}_p{NNN}.png"/>` als erstes Kind; alle 4108 referenzierten Bilder existieren.

Nebenbefunde als ZBZ-Rueckfragen festgehalten: die ZBZ-README widerspricht sich bei
Bildunterschriften (O27); der Header-Widerspruch (idno gefordert, Schema verbot es) wird durch
E68 aufgeloest (vgl. O8).

**Entscheidungen.** E88 (Inline-GND als Liefermodell, standOff aus Schema entfernt; verworfen:
rohe Uebernahme der ZBZ-Vorlage, weil ihr die E68-Kopf-Elemente fehlen und alle 285 invalidieren
wuerden). E89 (`<graphic>` als erstes Surface-Kind, Adressschema `{doc_id}_p{NNN}.png`; verworfen:
absolute GitHub-Pages-URL und IIIF, da Hosting offen und ein relativer Pfad die ZBZ-Vorgabe ist).
O26 geschlossen, O25 geschlossen, O27 eroeffnet.

**Stand.** Alle drei Auftragspunkte umgesetzt, gegen committete Tests verifiziert: Schema-Gate
(Inline-GND-Positivtest + standOff-Guard), `test_zbz_conformity.py` (285/285 konform),
`test_tei_surface_graphic.py` (Surface-Graphics + Korpus). Volle Suite gruen. Drei Commits auf
main (per order: alles in main, keine eigenen Branches): E88-Schema, Task-2-Konformitaet,
E89-Seitenbild. Lane entblockt, keine offenen Gates.

**Naechste Schritte.**
1. teiCrafter-Ausgabemodell an Inline-GND angleichen (Delta an die Forschungsleitstelle gemeldet,
   beruehrt lane teicrafter-editor).
2. ZBZ-Rueckfragen klaeren: Bildunterschrift-Widerspruch (O27), Schlagworte (O13), Header-
   Metadaten aus Alma (O8).
3. Optional: E84-Strukturfixes per Korpus-Neugenerierung ausrollen (Koordination mit den
   Kurations-Lanes).

### 2026-06-21 Sitzung 70: Schema-Erweiterung teiCrafter-standOff (E87) + Faksimile-Befund + Warnungs-Angleichung

**Anlass.** Im Kurations-Editor teiCrafter annotierte ZBZ-Dokumente waren gegen ihr
eigenes Schema invalide, weil das ODD-Subset (E48) das `standOff`-Register und das
generische `<name>` weggelassen hatte; `{id}_final.xml` ist aber teiCrafters natives Format.

**Ziel.** Das Schema so erweitern, dass kuratierte Dokumente schemavalide werden, die
Entscheidung dokumentieren, den finalen TEI-Bestand regressionspruefen und die
Wissensdokumente auf einen konsistenten, verifizierten Stand bringen.

**Verlauf.** Datenvertrag aus `ResearchTools/teiCrafter` (`docs/js/editor/standoff.js`)
erhoben: `standOff` mit `listPerson`/`listPlace`/`listOrg`/`listEvent`/`listBibl`,
Entitaeten mit Namens-Element plus `<idno>`-Normdaten und `resp="#ai"`, editoriale
`<note target>`, `<respStmt>` mit `<name>AI</name>`, In-Text-Mentions `<name ref>`. Schema
nach Muster E68 minimal erweitert: `standOff` an `model.resource` gehaengt, `name` an
`model.nameLike.agent` (deckt in einem Zug Inline-Mentions und den respStmt-Namen), elf
neue Element-Defines plus ein dediziertes standOff-Werkregister, weil das geteilte
ODD-reduzierte `bibl` weder `<title>` noch `@resp` zulaesst und unangetastet bleibt.
`@resp`/`@ref`/`@target` reiten auf vorhandenen Attribut-Klassen. Verifiziert: synthetisches
kuratiertes Dokument valide, alle 285 `tei_final` weiterhin valide (keine Regression), neues
git-getracktes Schema-Gate, Suite gruen. Faksimile geprueft: der Generator erzeugt
`surface`/`zone`/`@facs` selbst und vollstaendig, nur der Surface->Bild-Zeiger `<graphic>`
fehlt im Normalfall (`build_facsimile`, `tei_step3.py`). Warnungszahlen quer durch quality/
pipeline/projekt angeglichen.

**Entscheidungen.** E87 (Schema-Erweiterung teiCrafter-standOff, Begruendung in
[decisions.md](decisions.md)). O25 eroeffnet: Faksimile-`<graphic>` pipeline-seitig erzeugen,
URL-Schema und SoT-Regeneration operator-gated. Warnungs-Divergenz aufgeloest: 15 aktive
Warn-Regeln (W1-W7, W11-W18; W8-W10 seit E71 entfallen) gegenueber 121 Dokumenten mit
mindestens einer Warnung auf `tei_unified` -- zwei Groessen, vorher unter einem Wort vermengt.

**Stand.** Schema erweitert und kompiliert, Schema-Gate 288 gruen. Wissensdokumente
(decisions, quality, pipeline, projekt, oekosystem-synthese, index) konsistent und gegen
den gemessenen Stand verifiziert. Branch `chore/frontmatter-migration`.

**Naechste Schritte.**
1. Operator-Entscheidung zu [decisions.md O25] (URL-Schema fuer Surface-`<graphic>`).
2. Bei Zustimmung: `build_facsimile` um `<graphic>` als erstes Surface-Kind erweitern, alle
   285 `tei_final` regenerieren, Schema-Gate erneut.

### 2026-06-10 Sitzung 69: Repository-Audit mit Umsetzungswelle (E86)

**Anlass.** Vor der ZBZ-Abnahme sollte das gesamte Repository begutachtet werden
(Code, Prozesse, Dokumentation), einschliesslich bekannter Fehler im Viewer-Frontend.

**Ziel.** Alle verifizierten Befunde in einem Durchgang beheben und die Wissensbasis
redundanzfrei auf den tatsaechlichen Projektstand bringen.

**Verlauf.** Im Viewer wurde das Datenverlust-Risiko des XML-Modus behoben: Der Modus
lud bisher nur die Einzelseite, waehrend der Speichern-Knopf das Gesamtdokument
`output/tei_final/{doc}_final.xml` ueberschreibt; jetzt laedt er das Gesamtdokument,
und ein Save-Guard weist unvollstaendige TEI-Inhalte ab. Dazu kamen die uebrigen
Befunde der Frontend-Gap-Analyse vom 2026-06-07: ein "Gehe zu Seite"-Feld mit
Tastaturnavigation, aktuelle Status-Ampeln im Katalog (der Katalog laedt die
Pro-Objekt-Manifeste nach und korrigiert damit das veraltete Aggregat), klare
Fehlermeldungen mit Wiederholen-Knopf, Fokus-Fuehrung im Modal sowie
Bedienbarkeit von Layout-Editor und Text-Editor per Tastatur und Screenreader.

Auf Prozessseite prueft seither ein GitHub-Actions-Workflow die komplette Testsuite
bei jedem Push und Pull Request; `requirements.txt` wurde fuer frische Umgebungen
lauffaehig gemacht (fehlende Pakete ergaenzt, sechs ungenutzte entfernt), und zwei
Transkribus-Skripte schliessen ihre Dateihandles jetzt auch im Fehlerfall.

In der Dokumentation wurden die veralteten CER-Kennzahlen site-weit auf den kanonischen
Stand gezogen (Fidelity-CER Mean 2,71 %, Median 1,40 %, ueber alle 25 Referenzdokumente);
das Entscheidungsregister fuehrt die Eintraege ab E64 als Unterkapitel mit Begruendung
und Datum; die Roadmap in workflow.md trennt Erledigtes von Offenem in verstaendlicher
Sprache; Zustaendigkeiten sind als Rollen statt Personennamen notiert.

**Entscheidungen.**
- Der XML-Modus zeigt und speichert das Gesamtdokument (E86). Die Alternative, weiter
  die Einzelseite zu zeigen und das Speichern zu sperren, wurde verworfen, weil der
  Gesamtdokument-Weg dem Design der Speicherarchitektur (E72) entspricht und Kuration
  ohne Umweg erlaubt.
- Die vier verbliebenen Frontend-Befunde N1/N3/N6/N7 (Komfort, kein Fehlerrisiko)
  werden bis nach der ZBZ-Abnahme zurueckgestellt, damit der Stand fuer die Abnahme
  stabil bleibt.
- `data/curated_tei/` wird als vorgesehen fuer kuenftig von Hand verifizierte TEI und
  derzeit leer deklariert. Die bisherige Bezeichnung als Gold-Standard wurde verworfen,
  weil noch keines der 285 Dokumente fachlich verifiziert ist.

**Stand.** Testsuite 563 gruen, 285/285 Dokumente schema-valide, alle H- und M-Befunde
der Gap-Analyse behoben, Wissensbasis konsistent mit dem Repo-Stand. Erste inhaltliche
Kurationsschritte ueber den Viewer liegen vor: In den Dokumenten 3200 und 760 wurden
Werktitel als `<bibl>` ausgezeichnet (kanonisch in `tei_final`, Mirror konsistent).
Offen bleiben die zurueckgestellten N-Befunde sowie die fachliche Verifikation der
Inhalte (855 von 855 Datenstroemen stehen auf `unverifiziert`). Savepoint: Commits
52fd7733 bis 6a73478f auf `cc3/session-2026-06-07`.

**Naechste Schritte.**
1. Render-Check der TEI-Daten in der teiCrafter-Integration nach Testplan T1-T9
   (`reports/test-plan-zbz-teicrafter-2026-06-07.md`).
2. Fachliche Kuration im Viewer beginnen (Status-Pills, Strom fuer Strom).
3. Nach der ZBZ-Abnahme die zurueckgestellten Befunde N1/N3/N6/N7 umsetzen.

---

## Kompakt-Archiv (Sitzungen 1 bis 68)

Eine Zeile pro Sitzung, neueste zuerst. Begruendungen im
[Entscheidungsregister](decisions.md), Details in der Git-History.

### Juni 2026 — Abnahme-Vorbereitung

| # | Datum | Thema |
|---|---|---|
| 68 | 2026-06-08 | Doc-30-Bereinigung und Tail-Analyse (E82): ein dupliziertes OCR-Blockpaar entfernt (Fidelity-CER 18,25 -> 11,59 %). Die Analyse der verbliebenen Ausreisser zeigt strukturelle Ursachen (Fussnoten-Ueberdetektion, Scope-Differenzen, Doppelseiten), keine Schwaechen der Zeichenerkennung. Korpus-Mean 4,26 -> 3,99 % konsistent publiziert. |
| 67 | 2026-06-08 | Transkribus-Export/Upload (E81): Pipeline-PAGE-XML rueckspielbar nach Transkribus (`edition.transkribus_export` baut Bundles, `edition.transkribus_upload` laedt via REST in eine Collection). Stichprobe 18 Docs gebaut, Doc 1500 in der Plattform verifiziert; Auth nur via Env-Vars. |
| 66 | 2026-06-08 | CER-Einordnung print-kalibriert (E80): da der Korpus aus Druckseiten besteht, ist der Vergleich mit Handschriften-Benchmarks unangemessen; die Bewertung wurde am Print-Literaturvergleich ausgerichtet und wertende Zuschreibungen entfernt. Geaendert: quality.md, methode.html, Arbeitsbericht. |
| 65 | 2026-06-07 | M2.4 Bild-URL-Schema + ZBZ-Testplan fuer die teiCrafter-Integration: Bildregel pro `<surface xml:id="facs_K">` ist `{id}_p{KKK}.png` mit K = Scan-Position (nicht `@n`; Edge Case 2310 beachten), Deployment live verifiziert (GitHub Pages, kein IIIF), Demo-Objekt 1540 gewaehlt. Erstellt: `reports/bericht-m2-2026-06-07.md` + Testplan T1-T9. |
| 64 | 2026-06-07 | Frontend-Gap-Analyse ueber 6 Frontends (live + statisch): Hersch-HOCH-Befunde H1 (TEI-XML-Edit kann `_final.xml` ueberschreiben) bis H5 (Modal ohne Fokus-Trap), Token-Disziplin bestaetigt. Neues Knowledge-Doc [frontend-gaps.md](frontend-gaps.md) als SSoT + datierter Bericht in `reports/`. |
| 63 | 2026-06-07 | Viewer-Kuration: ein Speichern-Knopf (E78) + Mirror-Write-Fix (E79). Gespeicherte Korrekturen verschwanden nach dem Seiten-Reload, weil der Viewer nur aus `docs/data/` liest, E72 aber nur nach `output/` schrieb; seitdem spiegelt jeder Speichervorgang die identische Nutzlast in beide Ablagen, der Viewer liest kuratierte Daten zuerst. Einzel-Downloads im Export-Dropdown. |
| 62 | 2026-06-07 | Workflow-Status von vier auf drei Stufen kollabiert (E77): `unverifiziert\|in_arbeit\|verifiziert`, eine Farbe je Stufe (grau/gelb/gruen), rot reserviert. Backend + Frontend + CSS umgestellt, neues Gate `test_workflow_status.py`, Suite 525 gruen; keine Mirror-Regeneration noetig (alle 285 Docs standen auf `unverifiziert`). |
| 61 | 2026-06-03 | Abnahme-Tiefenanalyse + Repo-Hygiene + MMSID-Entfernung (E76): Korpus-Invarianten am realen Datenbestand verifiziert (524 Tests gruen, 285/285 schema-valide, 0 Drift), Abnahme-Befunde dokumentiert (855 Stroeme `unverifiziert`, 195 leere Container-Titel, Doc 10 unvollstaendig). Die Projektion der Alma-Katalognummer (MMSID) in den TEI-Header wurde nach Vorlage des Spezifikations-Konflikts entfernt, da Katalog-Metadaten in der ZBZ-Domaene liegen (O8); Root-README abnahmetauglich neu gefasst. |

### Mai 2026 — Viewer-Datenversorgung + Deploy-Vorbereitung + Edition-Uplift

| # | Datum | Thema |
|---|---|---|
| 60 | 2026-05-27 | Frontend-UI-Review aller 5 `docs/`-Seiten + Quick-Wins: blockierendes `window.prompt()` fuers Bearbeiter-Kuerzel durch Inline-Feld ersetzt, Statuswechsel erst bei echter Aenderung statt beim Oeffnen, Dirty-Marker pro Strom, Mobile-/Filter-/Sortier-Fixes, JS-Cache-Versionierung (`?v=`). Bewusst offen gelassen: toter Panel-Divider, TEI-gerendert-Edit ohne Speicherpfad, Umlaut-Transliteration der UI-Chrome, fragmentierte Sprachfilter. |
| 59 | 2026-05-27 | Repository-Aufraeum-Welle W1-W5 (10 Commits): Doku-Drift + tote NER-Reste + Hex-zu-Token bereinigt, OCR-Quellen auf `loaders.OCR_SOURCES` vereinheitlicht, inkohaerente CER-Scope-Ausschlussliste entfernt (alle Metriken n=25, Fidelity 4,26/1,83 bleibt exakt, E73), Schematron dokumentiert statt gebaut (E74), `ocr_dedup` + DoclingOCR-Engine entfernt (E75). Suite 524 gruen. |
| 58 | 2026-05-27 | Direkt-Schreiben-Loop fuer die Viewer-Kuration (E72): `ZBZ.FsAccess` schreibt per File System Access API in den freigegebenen Repo-Ordner (Chromium, Download-Fallback), und `loaders.py` konsumiert kuratierte Layout-/OCR-Dateien real in `--reassemble`. Gate `test_curated_loaders.py`. |
| 57 | 2026-05-27 | Doku-Korrektheits-Welle: alle Markdown-Docs gegen den realen Repo-Stand auditiert (Entscheidungs-Zaehler, Agent-Screening-Reste in workflow.md, fehlende Artefakte, Test-Inventar) und parallel zu E70/E71 nachgezogen. Kein Commit (gemischter Tree). |
| 56 | 2026-05-27 | NER/Entity-Linking vollstaendig entfernt (E71): nur ~2,6 % der ~30.500 Erwaehnungen trugen echte GND-IDs, die Verlinkung war nie lieferfaehig. Code, Daten und Frontend-Anteile entfernt, deterministischer Tag-Strip ueber alle 285 TEI, 285/285 schema-valide. |
| 55 | 2026-05-27 | CER-Methodik tief geprueft + korrigiert (E70): ZBZ-Referenzen sind selektive Teiltranskriptionen, das alte Alignment-Trimming verbarg das. Neue Fidelity/Scope-Zerlegung, Headline Fidelity Mean 4,26 %/Median 1,83 % ueber alle 25 Docs, drei CER-Pfade vereinheitlicht, Paired-Test korrigiert. 18 goldene Tests, Suite 507 gruen. |
| 54 | 2026-05-27 | Hygiene + Korrektheits-Welle (E69): stiller Validator-CER-Importfehler behoben, `<pb>`-Splitter-Duplikat zu `pb_split.py` zusammengefuehrt (byte-identisch ueber alle 285 Finals verifiziert), `build_tei_header` auf den Liefer-Vertrag gehoben (idno + biblStruct + langUsage). Suite 503 gruen. |
| 53 | 2026-05-27 | Schema-Regression entdeckt + behoben (E68): die ausgelieferte Schicht `tei_final` wurde nie batch-validiert und stand bei 0/285 valide (teiHeader-Elemente fehlten im ODD-Subset). Schema ergaenzt, 285/285 valide, neues Gate `test_tei_schema.py`. |
| 52 | 2026-05-26 | E66-Abschluss: `tei_status_marker` ueber alle 285 Docs (285 irrefuehrende Agent-Screening-Eintraege raus, 855 ehrliche Workflow-Eintraege rein), 4 Commits gepusht, Frontend-Audit mit 15 priorisierten Befunden, tote Screening-Badges entfernt. |
| 51 | 2026-05-26 | Catalog-UI-Refactor + Ampel-Reframing (E67): Status `offen` umbenannt in `unverifiziert` (Pipeline-Output existiert, ist nur ungeprueft), rot reserviert; Filter, Spalten-Sortierung und Workflow-Spalte ueberarbeitet, Footer + Impressum site-weit konsistent. |
| 50 | 2026-05-26 | Agent-Screening abgeschafft, Workflow-Status pro Strom eingefuehrt (E66): menschengesetzte Statuswerte je Datenstrom mit Provenienz-History im Pro-Objekt-Manifest; Catalog + Viewer umgestellt, `tei_status_marker` projiziert die History in den `<revisionDesc>`. |
| 49 | 2026-05-26 | Leerseiten-Manifest + TEI-Marker (E63 Phase 2; E65): `page_manifest.py` detektiert deterministisch 79 Leerseiten in 15 Docs (OCR-Regel + Docling=0, cross-validiert, 0 Konflikte), `tei_blank_marker.py` projiziert `<pb type="blank"/>` und leert Junk-Bodies. 0 Schema-Regression. |
| 48 | 2026-05-26 | Viewer-UI verdichtet (E64): totes OCR-Engine-Dropdown entfernt (Viewer = ausgelieferte Edition = Mistral), Doc-Subbar + Toolbar fusioniert, Edit-Toggles heissen "Layout"/"Text". |
| 47 | 2026-05-26 | Viewer-Live-Review + Leerseiten-Welle (E63): Leerseiten zeigten OCR-Muell + Phantom-Regionen; Blank-Handling im Viewer gebaut und Architektur entschieden: Pro-Objekt-Manifest als SSoT fuer Seiten-Fakten, TEI-Marker als Projektion daraus. |
| 46 | 2026-05-26 | Methode-Seite `docs/methode.html` als schlanke Nachfolgerin des abgeschafften CER-Dashboards (E62): Headline-CER, Stratifizierung, Literaturvergleich, Limitations, Werkzeug-Doku. |
| 45 | 2026-05-25 | Edition-Uplift-Welle gestartet (E58-E61): OpenSeadragon 5.0.1 als Faksimile-Renderer, Polygone explizit ausgeschlossen (Druck-Korpus), Edit-Toggle pro Panel statt globaler Mode-Leiste, Export-Modul mit JSZip geplant. |
| 44 | 2026-05-25 | Befund-Fixes + Konsistenz-Refactoring: TEI-Doppelkodierung `&amp;amp;` behoben, Knowledge-Drift nach E56/E57 bereinigt, `<pb>`-Splitter balanciert jetzt `<div>`-Grenzen. Alle 4970 ausgelieferten XML wohlgeformt (vorher 327 nicht). |
| 43 | 2026-05-25 | Viewer auf vollen Korpus erweitert (E57): Mirror-Generator fuer alle 285 Docs (8083 Layout-, 4117 OCR-, 4115 TEI-Seiten via `<pb>`-Splitting), dreistufiger Pfad-Resolver, GitHub-Pages-tauglich. Bildlieferung bleibt lokal. |

### April 2026 — Frontend-Radikalkur + Wissenschaftliche CER-Re-Evaluation

| # | Datum | Thema |
|---|---|---|
| 42 | 2026-04-27 | Knowledge-Konsolidierung (25 auf 10 Docs) + Frontend-Radikalreduktion: Edition, Diagnostik, CER-Dashboard und Curation Editor abgeschafft, neue Single-Page-App `docs/viewer.html` (Faksimile + OCR/TEI + Layout-/Transkriptions-Editor). 9 auf 1 HTML, 23 auf 6 JS, CSS minus 84 %. E56. |
| 41 | 2026-04-27 | CER wissenschaftlich fundiert: BCa-Bootstrap-CIs (B=10000, Seed=42), Paired-Test E2E vs OCR-only, Selektionsbias ehrlich geflaggt, Pagewise-vs-Global-Artefakt diagnostiziert und in [quality.md](quality.md) dokumentiert. E54/E55. |

### Maerz 2026 — Pipeline-Konsolidierung + Edition

| # | Datum | Thema |
|---|---|---|
| 40 | 2026-03-27 | Frontend-Refactoring Phase 1+2: CSS-Token-Konsolidierung, HTML-Semantik (Skip-Nav, ARIA), JS-Foundation-Layer (`zbz-core.js`), Unified TEI Renderer. |
| 39 | 2026-03-26 | OCR-Diagnostik Abschluss: 6 Scope-Mismatches identifiziert; bereinigte Statistik n=19 Mean 4.18% / Median 1.83%. |
| 38 | 2026-03-26 | Diagnostik-UI Rewrite: 4 Tabs, ZBZ.Diagnostik-Namespace, Search-Index 279→285 (XML-Parsing-Fix). |
| 37 | 2026-03-26 | Diagnostik-Datenproduktion: W10-Tiefenanalyse, Corpus-Statistik (285 Docs / 4.108 Seiten), Validierungs-Timeline. |
| 36 | 2026-03-26 | Edition-Sync Fortsetzung: Log-Tab, Seitenzaehlung 383→4.117. |
| 35 | 2026-03-26 | Edition-Synchronisation: Katalog 15→285 Docs, Wikidata-Resume-Flag, revisionDesc im Reader. |
| 34 | 2026-03-26 | TEI-Qualitaet: ref-Pattern in `zbz_hersch.rng` erweitert (GND + #zbz), 285/285 schema-valide. Heuristische lb-Injection (10.635 lb in 46 Docs), Post-Assembly-Fixes W3/W4/W7. |
| 33 | 2026-03-26 | OCR-Diagnostik + Eval-Optimierung: Symmetrische Normalisierung, Hyphen, CI-Alignment. Mean CER 9.33%→5.97%, Median 5.52%→2.42%. |
| 32 | 2026-03-26 | End-to-End CER Benchmark (E51): TEI-vs-TEI Eval, `benchmark_cer.py`, Median 5.5%. Sub-Projekt CER-Verbesserung definiert. |
| 31 | 2026-03-26 | Neues Schema `zbz_hersch.rng` + verbindliche Editionsrichtlinien ZBZ eingearbeitet (18 Dateien). E48/E49/E50 (Dual-Attribut). |
| 30 | 2026-03-15 | Hersch Design-System: Migration auf Anthrazit+Ziegelrot+EB Garamond+Jost. Zweistufige CSS-Tokens (`--h-*` / `--ed-*`). Hersch-Komponenten (Seuil, Etonnement, Polyphonie). |
| 29 | 2026-03-15 | NEEDS_REVIEW 32→0: 20 neue Entity-Stopwoerter (E45), Strukturfixes, OCR-Dedup `ocr_dedup.py` (E46). Finalstand 242 APPROVED / 43 WITH_NOTES / 0 NEEDS_REVIEW. |
| 28 | 2026-03-15 | Edition Frontend Refactoring: Discovery Hub, Volltextsuche, Galerie, Screening + Curation Workflow getrennt, 5 Curation-States. |
| 27 | 2026-03-15 | Agent-Based Quality Screening Rollout 285/285 (58 Batches, 4 Tiers): 210 APPROVED, 43 WITH_NOTES, 32 NEEDS_REVIEW. revisionDesc-Standard etabliert (E42), `output/tei_final/` als Single Source of Truth (E43). |
| 26 | 2026-03-15 | TEI Validation Quality Gate refactored: 2-Ebenen (Errors/Warnings), W1-W11, HTML-Report. Entity-Tagging typkorrekt mit internen IDs. div-Merge. `--reassemble` Flag. 284/285 VALID. |
| 25 | 2026-03-14 | Frontend-Konsolidierung: Edition nach `docs/`, Pipeline-UI nach `docs/infrastruktur/`. ES5→ES6+ in 13 JS-Dateien. |
| 24 | 2026-03-12 | Viewer-Erweiterung: WD/zbz-ID Support, GND-0%-Bug behoben (`entity_index.py` schrieb GND nie ins TEI-XML — Fix + Cache-Backfill, 0%→21.7%). |
| 23 | 2026-03-09 | NER Completion + TEI Entity Injection: 285 Docs, 11.685 Entities, 26.197 Mentions. Wikidata-Linking gestartet. |
| 22 | 2026-03-09 | Knowledge-Refactoring: EDITION + CURATION getrennt. NER Production Run 285 Docs, 4.100 Index-Eintraege. |
| 19-21 | 2026-03-08–09 | Curation Editor Phasen 2-5: Block-Toolbar, Entity-Kuration mit Autocomplete, Review-Workflow (3 Status), TEI-Validierung. `data/tei_curated/` als git-tracked Gold-Standard. |
| 17-18 | 2026-03-08 | tei_unified Refactoring (Orchestrator ~1100→~70 Z.). NER-Robustheit (Diakritik, Retry, Surname-Matching). NER Production Phase 1 (7 Qualitaetsverbesserungen, E35). |
| 14-16 | 2026-03-06–07 | Unified TEI Pipeline (E32): 4 Stufen (Scaffold + Gemini + Assembly + Validation). NER Pipeline (E34): Gemini Flash Lite, 6 Entity-Typen, Wikidata-Reconciliation. |
| 12-13 | 2026-03-06 | Gemini Vision TEI (E30, superseded). Dokumenttyp-spezifische Prompts (4-Ebenen). Layout-QA Full Run E31 (14.708 Korrekturen). |
| 11 | 2026-03-05 | Gemini-Dokumentklassifikation (E27, Stage 1a). Online-Demo (E28). Gemini OCR-Korrektur Stage 2b (E29). |
| 9-10 | 2026-03-03–04 | docling-serve API (E24), Gemini Layout QA + Detect (E25/E26): 3 Modi (qa/detect/auto). |

### Februar 2026 — Pipeline-Aufbau

| # | Datum | Thema |
|---|---|---|
| 7-8 | 2026-02-25–27 | Scope-Expansion (E21): Full Pipeline (OCR + Layout + PAGE-XML + NER/GND + TEI). Pilot 15 Docs, page-by-page Comparison (E16/E18). Data Delivery E23 (286 PDFs, 25 TEI-XMLs). |
| 4-6 | 2026-02-14–20 | Mistral OCR 3 als Production Engine (E6). Azure-Integration. PAGE-XML + METS Export (E13, Schema 2013-07-15). Dashboard-Redesign (E15). |
| 1-3 | 2026-01-29–02-14 | Initiale Quellenanalyse: 286 PDFs, 4 Dokumenttypen (A-D), Sprachverteilung FR 66% / DE 30%. Hybrid Pipeline-Entscheidung (E1): Docling Layout + LLM-OCR Text. |

Aeltere Detail-Eintraege im Git-Verlauf erhalten.

---

## Learnings

Aus den Sessions destillierte Beobachtungen, die fuer kuenftige Arbeit relevant bleiben:

- **L1** Validierung muss actionable sein. False-Positive-Quote >50% macht Reports nutzlos. Jede Warning braucht eine konkrete Aktion.
- **L2** Entity-Typ darf nicht verloren gehen. `annotate_entities()` braucht `(tag, id)` aus dem Index, nicht nur Namen.
- **L3** Stopwort-Filter ist essenziell. Gattungsbegriffe (Mensch, Gott, Wahl) erzeugen ohne Filter ~30% False Positives.
- **L4** Seiten-Fragmente zu Dokument-Struktur mergen. ZBZ-Referenz hat 1 top-level div. Post-Assembly-Merge ist deterministisch und kostenlos.
- **L5** Step-2-Cache invalidieren bei Prompt-Aenderungen. `--force` regeneriert nicht den Step-2-Cache.
- **L6** LLM-NER hat ~5-10% False Positives. Inhaerent. Loesung: Curation Editor, nicht Code-Fix.
- **L7** Page-Numbering-Drift macht Pagewise-CER unbrauchbar. Content-aligned Eval (`evaluate_tei_vs_tei`) ist immun.
- **L8** Mehrsprachige Codes korrekt parsen. "fra/deu" zerfaellt sonst zu "und". Betrifft ~40 Docs.
- **L9** facsimile/pb synchron halten. Leere surfaces fuer Seiten ohne Layout-Zones.
- **L10** Interne IDs (zbz-p/o/l/w.N) als primaere Referenz. GND in `ref`, intern in `corresp` (Dual-Attribut, E50).
- **L11** Eine server-lose Persistenz hat zwei Wahrheiten: den kanonischen Konsum-Ort (`output/`, Pipeline) und den Lese-Ort des Frontends (`docs/data/`-Mirror). Wer nur in den ersten schreibt, speichert real, aber unsichtbar fuer den Kuratierenden.
- **L12** Bei parallelen Instanzen im selben Tree sind `git status` + Verifikation gegen den realen Dateistand Pflicht; ein "file modified since read"-Konflikt ist das Signal zum Zuruecktreten, nicht zum Erzwingen.
- **L13** Eine Prosa-Zahl ("285/285 valide") ist kein Beleg. Die ausgelieferte SSoT braucht ein automatisiertes Gate, keine Behauptung.
- **L14** Ein gruenes Konformitaets-Gate ist nur so scharf wie der Bestand, ueber den es laeuft. "285/285 konform" heisst auf dem entitaetenfreien `tei_final` "keine Verletzung", nicht "Entitaeten korrekt GND-ausgezeichnet"; die entitaetsbezogenen Regeln (Z1-Z4) greifen erst nach der Inline-GND-Kuration durch teiCrafter.
- **P7** Gattungsbegriffe im Entity-Index erzeugen False Positives in ~30% der Docs.
- **P8** Zeitungslayouts versagen systematisch (>40 Zones, OCR-Halluzinationen). ~3% des Korpus.
- **P10** Tier-2-Docs (4-8 Seiten) haben 85%+ APPROVED-Rate, Tier-1 (1-3 Seiten) nur 40%.

<!--
Eintrags-Template zum Kopieren (neuen Eintrag direkt unter "## Eintraege" einfuegen):

### YYYY-MM-DD Sitzung N: Sitzungstitel

**Anlass.** [Ein Satz: warum diese Arbeit jetzt.]

**Ziel.** [Ein Satz: was am Ende stehen sollte.]

**Verlauf.** [Ein bis vier Absaetze. Was tatsaechlich geschah, mit Belegstellen.
Fachbegriffe beim ersten Auftreten erklaeren.]

**Entscheidungen.**
- [Was, warum, verworfene Alternative. Registernummer falls vorhanden.]

**Stand.** [Ein Absatz, allein lesbar: was steht, was ist offen.
Optional Commit-Hash als Savepoint.]

**Naechste Schritte.**
1. [Konkret genug als Sitzungseinstieg.]

**Dead Ends.** [Optional: versucht und verworfen, mit Begruendung.]
-->
