---
title: "Arbeitsbericht zbz-ocr-tei: LLM-gestützte OCR- und TEI-Pipeline für die digitale Edition der Schriften von Jeanne Hersch"
project:
  name: zbz-ocr-tei
  repository: https://github.com/chpollin/zbz-ocr-tei.git
method:
  name: Promptotyping
  url: https://dhcraft.org/Promptotyping/
template:
  name: Vorlage Report
  version: 0.1
  url: https://dhcraft.org/Promptotyping/promptotyping-document/report
status: complete
created: 2026-05-27
updated: 2026-07-08
audience:
  type: client
  name: Zentralbibliothek Zürich (ZBZ)
report-genre: abschlussbericht
authors: [Christopher Pollin]
---

# Arbeitsbericht: LLM-gestützte OCR- und TEI-Pipeline für die digitale Edition der Schriften von Jeanne Hersch

Dr. Christopher Pollin, Digital Humanities Craft OG

* v2, 09.07.2026; v1, 27.05.2026  
* AI-Unterstützung: Claude Opus 4.7, Opus 4.8, Fable 5, Claude Code

## **1 Projektkontext und Zielsetzung**

Dieser Bericht dokumentiert ein Experiment im Rahmen der digitalen Neuauflage der Schriften von Jeanne Hersch, einem Projekt der Zentralbibliothek Zürich (ZBZ).[^1] Herschs philosophisches Werk ist mehrsprachig, überwiegend französisch und deutsch, und verstreut überliefert. Der Bestand versammelt zudem unterschiedliche Layouts über verschiedene Dokumenttypen hinweg, von Zeitschriftenartikeln über Sammelbandbeiträge bis zu Monografien.

Parallel zum etablierten ZBZ-Workflow wurde dieselbe Strecke ein zweites Mal durchlaufen, diesmal agentenbasiert über Large Language Models (LLMs) und Vision-Language Models (VLMs). Leitfrage ist, ob ein solcher Ansatz den etablierten Workflow in Textqualität und Aufwand erreicht. Die Vergleichsgrundlage stammt aus derselben Parallelführung, denn die manuell über Transkribus erstellten Referenz-TEIs dienen dem Experiment als Ground Truth.

Gegenstand ist eine Pipeline, die ausgehend von PDF-Scans TEI-XML erzeugt und in einem zugehörigen Webinterface anzeigbar und kuratierbar macht. Als Zielformat dient ein projektspezifisches TEI-Schema, das sich aus den ZBZ-Editionsrichtlinien ableitet. Die Pipeline erzeugt Transkription, Layouterkennung und TEI-XML durchgängig über LLMs und VLMs und ist im doppelten Sinne agentenbasiert. Zum einen ist sie selbst durch ein agentisches System implementiert und in einem AI Harness[^2] weiterentwickelbar, zum anderen erlaubt sie das agentische Bearbeiten und Annotieren der Daten. Der verwendete AI Harness war Claude Code. Der so erzeugte Ausgangszustand aller Datenströme ist LLM-gestützt erzeugt und damit unverifiziert; das Vorhaben liefert zusammen mit dem Kurationswerkzeug jedoch eine Möglichkeit, diese Verifikation durchzuführen.

Pipeline wie Webinterface entstehen durch Promptotyping[^3], eine Context-Engineering-Arbeitsweise zur Erzeugung von Forschungsartefakten aus Forschungsdaten und Forschungskontexten.[^4] Die Codeerzeugung erfolgte vollständig innerhalb von Claude Code mit den jeweils aktuellen Opus-Modellen über mehrere Sessions hinweg;[^5] der Erzeugungsprozess ist über die Commit-Historie des offen vorliegenden Repositorys nachvollziehbar.[^6]

## **2 Datengrundlage**

Die Ausgangslage bildet die Lieferung der ZBZ, die PDF-Scans der Drucktexte, das Masterfile mit den zugehörigen Metadaten, die zugehörigen PAGE-XML-Exporte, die Editionsrichtlinien und die 25 manuell erstellten Referenz-TEIs (Transkription in Transkribus, TEI-Auszeichnung in Oxygen; siehe §3). Letztere sind selektive Teiltranskriptionen und dienen als Ground Truth (siehe 6.1), was jede spätere Zahleninterpretation prägt. Nicht Gegenstand sind der katalogische Gesamtbestand und seine bibliothekarische Erschließung.

Das Masterfile enthält zwei Arten von Information, die bibliografischen Stammdaten mit ID, MMSID, Gattung (`PublForm`), Jahr, Titel, Seitenzahl (`Anzahl Seiten`), Signatur und Sprache sowie die Workflow-Spalten, die den Bearbeitungsstand im ZB-Prozess festhalten, etwa digitalisiert, Kontrolle Metadaten, korrigiert und ausgezeichnet.

Die Datengrundlage des Berichts sind die 286 als PDF gelieferten Texte. Das Masterfile verzeichnet insgesamt 325 Texte; ein Teil davon ist nicht digitalisiert, und von den 289 digitalisierten fehlen drei in der PDF-Lieferung (1745, 1750, 1970). Für 285 der gelieferten PDFs liegt ein finales TEI vor; das eine Dokument ohne finales TEI ist Dokument 10 (siehe 6.3). Das Audit-Skript `corpus_audit` leitet diese Zahlen reproduzierbar aus Masterfile und Lieferung ab.

| Stand | Anzahl |
| :---- | ----: |
| im Masterfile gelistet | 325 |
| digitalisiert | 289 |
| als PDF geliefert | 286 |
| davon mit finalem TEI | 285 |
| physische Seiten der 286 PDFs | 4.152 |

Die Verteilungen nach Dokumenttyp und Sprache beziehen sich auf den Lieferstand von 286 Dokumenten. Die gelieferten Dokumente sind durchweg Drucktexte, handschriftliches Material ist nicht systematisch vertreten, sodass es sich um einen reinen OCR-Prozess handelt. Der Bestand erstreckt sich über die Jahre 1931 bis 1998\.

| Dokumenttyp | Anzahl | Anteil |
| :---- | ----: | ----: |
| Zeitschriftenartikel | 146 | 51 % |
| Sammelbandbeiträge | 116 | 41 % |
| Monografien | 24 | 8 % |

| Sprache | Anzahl | Anteil |
| :---- | ----: | ----: |
| Französisch | 203 | 71 % |
| Deutsch | 72 | 25 % |
| Englisch | 7 | 2 % |
| Italienisch | 2 | 1 % |
| mehrsprachig fr/de | 1 | \< 1 % |
| ohne Angabe | 1 | \< 1 % |

## **3 Repository-Architektur**

Der Ordner `knowledge/` ist ein Promptotyping-Vault, eine an eine Obsidian-Vault angelehnte, in Claude Code erzeugte und kuratierte Wissensbasis in Markdown, die das Projektwissen abbildet und über den Projektverlauf iterativ wächst; einzelne Dokumente entstehen, wachsen oder werden zusammengeführt. Weiters existiert ein chronologische Arbeitstagebuch `journal.md` als beschreibende Schicht neben der Git-Historie und das durchnummerierte Entscheidungsregister `decisions.md`. 

Der Ordner `data/` enthält Eingangs- und Referenzdaten und trennt Geliefertes von projektseitig Erzeugtem. Unter `data/source/` liegen die von der ZBZ gelieferten Startdaten, also die PDF-Scans, die manuell erstellten Referenz-TEIs samt zugehörigen PAGE-XML-Exporten, das Masterfile und die Editionsrichtlinien, dazu die versionierte Juni-Lieferung `zbz-lieferung-2026-06-21/` mit der aktuellen, vollständigen Fassung der Editionsrichtlinien, der zugehörigen ZBZ-Prüfvorlage (RelaxNG) und einem Provenienz-Dokument. Daneben stehen projektseitig erstellte Referenzdaten, das TEI-Schema `data/schema/zbz_hersch.rng`, das der ZBZ-Prüfvorlage samt den in E68 ergänzten Header-Elementen entspricht, und der Ordner `data/curated_tei/`, der für handverifizierte TEIs reserviert ist. Die per LLM erzeugte Dokumentklassifikation liegt in `doc_metadata.json`.

Der Ordner `output/` enthält alle generierten Datenströme (OCR, Layout, PAGE-XML, TEI) und ist bewusst nicht versioniert. Versionierung kann über Git hergestellt werden. Der Ordner `scripts/` enthält die von Claude Code generierte Python-Pipeline, nach Domäne in Unterpakete gegliedert (`ocr`, `layout`, `tei`, `eval`, `edition`, `core`); die einzelnen Skripte sind in Anhang A aufgeführt. Der Ordner `reports/` sammelt eigenständige Prüfberichte, die neben der laufenden Auswertung entstanden sind, darunter eine unabhängige Gegenprobe der CER-Messung ohne Rückgriff auf den Projektcode und den Verifikationsbericht zu den Kernaussagen dieses Berichts (siehe 6.4). Die automatischen Tests liegen unter `tests/`. Sie sichern ab, dass die Werkzeuge bei jeder Änderung korrekt weiterarbeiten, etwa dass die CER-Statistik richtig rechnet, dass jedes ausgelieferte TEI gegen das Schema gültig bleibt und dass alle Skripte lauffähig sind. Die vollständige Test-Suite läuft auf dem Arbeitsrechner, wo auch die Daten liegen. Auf GitHub wird derselbe Testbestand bei jeder Änderung automatisch ausgeführt; die Tests, die die lokalen Daten brauchen, überspringen sich dort selbst, und der verbleibende, datenunabhängige Teil dient als Sicherheitsnetz gegen Fehler im Code.

Der Ordner `docs/` ist für GitHub Pages konfiguriert und enthält das Frontend, einen Mirror der Pipeline-Daten und die aus den PDFs erzeugten PNGs. Da GitHub Pages ohne Backend nur statische Dateien ausliefert, liegen die Editionsdaten dort als generierter Per-Seiten-Mirror unter `docs/data/pages/{doc}/`, der den Großteil der versionierten Dateien ausmacht. Ein Skript zerlegt das finale TEI seitenweise und legt je Seite Dateien für TEI, OCR-Text und Layout ab, letzteres getrennt nach Docling und Gemini-QA; das vollständige `{doc}_final.xml` liegt im selben Ordner. Der Mirror deckt alle 285 Dokumente ab; nur die Faksimile-Bilder bleiben außerhalb einiger Demonstrationsdokumente lokal. Verbindliche Quelle ist das TEI unter `output/tei_final/{doc}_final.xml`, aus dem der Mirror nach jeder Änderung neu erzeugt wird, etwa nach einem erneuten Pipeline-Lauf oder einer im Viewer kuratierten und zurückgespielten Bearbeitung. Ein Edit am Mirror ginge beim nächsten Lauf verloren.

## **4 Die Pipeline**

Die Pipeline überführt PDF-Scans in TEI-XML. Je Dokument entstehen vier aufeinander aufbauende Informationsebenen. Die Bildebene liefert das seitenweise gerenderte Faksimile, die Grundlage aller weiteren Erkennung. Daraus entstehen zwei Basisströme, die OCR-Ebene mit dem erkannten Text und die Layout-Ebene mit der Seitenstruktur. Aus beiden wird die TEI-Ebene als strukturierte Zielfassung mit Überschriften, Absätzen sowie Seiten- und Zeilenumbrüchen gebildet. Die Verarbeitung ist durchgängig defensiv ausgelegt, sodass ein fehlschlagender Einzelschritt seine Eingabe unverändert weiterreicht, statt den Lauf abzubrechen.

Bild- und Basisströme entstehen in drei vorbereitenden Arbeitsschritten:

* Vorverarbeitung. Die PDF-Scans werden seitenweise in Einzelbilder zerlegt, auf denen die nachfolgenden Stufen aufsetzen.  
* Texterkennung. Produktiv erfolgt die Texterkennung mit Mistral Document AI[^7] über Azure AI Foundry. Das Modell erfasst neben Fließtext auch Tabellen und Listen und liefert seitenweises Markdown; weil die Schnittstelle je Anfrage nur eine begrenzte Seitenzahl annimmt, zerlegt die Pipeline große Dokumente automatisch in Teilstücke und fügt die Ergebnisse wieder zusammen. Steht dieser Zugang nicht zur Verfügung, übernimmt ersatzweise ein multimodales Gemini-Modell dieselbe Aufgabe und schreibt in dieselben Ausgabepfade, sodass sich für die Folgestufen nichts ändert. Eine optionale, sprachmodellgestützte Nachkorrektur ist vorhanden, aber standardmäßig abgeschaltet, weil sie in der Erprobung bei bereits guter Erkennungsqualität die Texte messbar verschlechterte; wo eine geprüfte korrigierte Fassung vorliegt, wird sie der Rohfassung vorgezogen.  
* Layoutanalyse. Die Strukturerkennung verbindet Docling[^8] mit einem nachgeschalteten Gemini-Schritt. Docling liefert die Basisstruktur, also Regionen mit Position und Typ, Gemini prüft die Labels und ergänzt fehlende Regionen. Im automatischen Modus wird je Seite gemessen, wie viel der Seitenfläche die erkannten Regionen abdecken. Bleibt die Abdeckung zu gering, erkennt Gemini das Layout direkt vom Scan vollständig neu und ersetzt das Docling-Ergebnis, statt es nur zu korrigieren. Docling-Fassung und Gemini-Fassung bleiben als zwei getrennte Dateien erhalten, sodass nachvollziehbar bleibt, welche Erkennung von welcher Engine stammt.

### **Austauschformate**

Aus dem Layout- und dem OCR-Datenstrom werden zusätzlich PAGE-XML[^9] und ein METS-Manifest[^10] erzeugt, Austauschformate für externe Bearbeitungs- und Archivsysteme wie Transkribus. Sie entstehen aus denselben Quellen wie das TEI, sind aber nicht dessen Vorstufe, denn das TEI wird unmittelbar aus Layout und Text gebildet.

### **TEI-Erzeugung**

Die TEI-Erzeugung verbindet regelbasierte und sprachmodellgestützte Arbeit in drei Stufen, denen deterministische Korrekturschritte nachgelagert sind. Im Repository entsprechen den Stufen die Module `scripts/tei/tei_step1.py` bis `tei_step3.py`, zusammengehalten vom Einstiegspunkt `tei_unified.py`; wer einen Schritt nachvollziehen will, findet ihn dort.

Die erste Stufe baut aus dem OCR- und dem Layout-Datenstrom ein deterministisches Grundgerüst. Textabschnitte werden den Layoutregionen zugeordnet, in Überschriften, Absätze, Fußnoten und vergleichbare Strukturen übersetzt und mit Seiten- und Zeilenmarken versehen. Die Blockreihenfolge folgt einer spalten- und bandbewussten kanonischen Lesereihenfolge, die Doppelseiten und Mehrspalter korrekt serialisiert; die frühere reine Sortierung nach vertikaler Position hatte auf zweispaltigen Layouts die Spalten verschränkt. Gedruckte Seitenzahlen werden aus den Fußzeilen-Regionen der Layoutanalyse gelesen und in das Attribut `pb@n` übernommen; wo keine Fußzeile erkennbar ist, füllt eine dokumentweite Interpolation aus konsistenten Nachbarseiten die Lücke, und erschlossene Zahlen stehen wie in den ZBZ-Referenzen in eckigen Klammern (Dokument 1000 trägt etwa auf einer fußzeilenlosen Seite den erschlossenen Wert `<pb n="[966]"/>`). Text aus gefilterten Randregionen, etwa die Seitenzahl selbst oder Bibliotheks-Deckblattzeilen, bleibt aus dem Fließtext ausgeschlossen.

Die zweite Stufe legt das Seitenbild zusammen mit dem Gerüst und dem erkannten Text einem multimodalen Modell vor und erzeugt eine strukturell angereicherte Fassung; der vollständige Arbeitsauftrag an das Modell steht in `scripts/tei/tei_mapping_prompt.py` und ist damit selbst versioniert und prüfbar. Da modellgenerierte Auszeichnung systematische Eigenheiten aufweist, schließt sich eine korrigierende Nachbearbeitung an, die häufige Struktur- und Schemaverstöße automatisch bereinigt. Schlägt die Verfeinerung fehl, wird das deterministische Gerüst unverändert weitergereicht.

Die dritte Stufe verbindet die Einzelseiten zu einem Gesamtdokument, zieht seitenweise entstandene Gliederungseinheiten zusammen und wendet einen zweiten Satz dokumentweiter Konformitätskorrekturen an, darunter die Vereinheitlichung der Gliederungstypen, die Vergabe von Bild-Identifikatoren und die Normalisierung fremdsprachiger Auszeichnung (aus einem uneinheitlichen Sprachcode wird durchgängig `<foreign xml:lang="fra">`).

Auf das ausgelieferte Korpus wirken schließlich nachgelagerte deterministische Marker-Schritte, die jeweils mit Backup arbeiten, idempotent sind und über ein Audit vorher und nachher vermessen werden. Zu ihnen gehören die Leerseiten-Markierung (`<pb type="blank"/>`), die Projektion des Bearbeitungsstatus in die Versionsbeschreibung, die Verknüpfung jeder Faksimile-Seite mit ihrer Bilddatei sowie die in 6.4 beschriebenen Bestandskorrekturen; die zugehörigen Werkzeuge liegen gesammelt unter `scripts/tei/`.

### **Validierung**

Das erzeugte TEI wird mehrstufig geprüft. Die erste Stufe validiert gegen das projektspezifische RelaxNG-Schema `zbz_hersch.rng`, das der ZBZ-Prüfvorlage samt den ergänzten Header-Elementen entspricht und damit die verbindlichen ZBZ-Editionsrichtlinien formalisiert. Die zweite Stufe setzt projekteigene Regeln blockierend durch (R1 bis R7); R1 verlangt etwa das Wurzelattribut `type="naegeli"`, das alle ZBZ-Referenz-TEIs tragen, weitere Regeln sichern die Präsenz von Header und Body und gültige Gliederungstypen. Informative Hinweise (W1 bis W19) markieren prüfenswerte Stellen, ohne die Gültigkeit zu blockieren; ein leerer Sprecher-Slot `<speaker/>` in einem Interview etwa ist gültig, wird aber als Kurationsplatz für die spätere Benennung gemeldet, ebenso jede Abweichung von der kanonischen Lesereihenfolge. Eine dritte Ebene prüft die ZBZ-Konformitätsregeln, die ein RelaxNG nicht ausdrücken kann, etwa das Rendering-Vokabular und die Form der Seitenumbrüche; die Entitätsregeln dieser Ebene werden erst auf kuratiertem, inline-GND-annotiertem Output scharf, weil das gelieferte Korpus bewusst entitätsfrei ist.

### **Bearbeitungsstatus**

Der Bearbeitungsstatus bezieht sich auf die drei aus der Bildebene erzeugten Ströme, OCR, Layout und TEI. Sie sind nach der maschinellen Erzeugung zunächst unverifiziert, also vorhanden, aber fachlich noch nicht geprüft. Den Prüfstand hält ein menschgesetzter Status fest, getrennt für jeden der drei Ströme. Jeder Strom nimmt einen von drei Werten an, unverifiziert, in Arbeit oder verifiziert, die im Webinterface als dreistufige Ampel erscheinen (neutral, gelb, grün) und per Klick weitergeschaltet werden. Jeder Wechsel wird in einer dokumentbezogenen Begleitdatei festgehalten, dem Manifest, einer JSON-Datei je Dokument, als fortlaufende Liste der einzelnen Schritte; ein Eintrag hat die Form

`{"at": "2026-06-07T11:16:23Z", "by": "Kürzel", "from": "unverifiziert", "to": "in_arbeit"}`

und hält Zeitpunkt, Bearbeiterkürzel sowie Vor- und Folgestatus fest, sodass eine vollständige Bearbeitungsspur entsteht. Bei der Übergabe an die ZBZ werden diese Einträge deterministisch und idempotent in die TEI-Versionsbeschreibung (`<revisionDesc>`) des Dokuments projiziert; aus dem Manifest-Eintrag wird dort

`<change when="2026-06-07T11:16:28Z" who="Kürzel" status="verifiziert" n="layout">LAYOUT-Strom: in Arbeit → verifiziert</change>`

sodass die Bearbeitungsgeschichte mit dem ausgelieferten Dokument selbst reist.

## **5 Webinterface und Kuration**

Das Webinterface ist ein im Browser laufendes, auf GitHub Pages gehostetes Werkzeug zur Überprüfung und Kuration der Pipeline-Ergebnisse ([https://chpollin.github.io/zbz-ocr-tei/](https://chpollin.github.io/zbz-ocr-tei/)). Den Kern bildet der Pipeline-Viewer (`docs/viewer.html`), eine Single-Page-App ohne Backend und ohne Build-Schritt. Ihre Inhalte lädt sie aus dem in der Repository-Architektur beschriebenen Per-Seiten-Mirror, einer pro Dokument und Seite vorab erzeugten Datenablage mit aufbereitetem OCR-Text, Layout-Regionen und dem aus dem finalen TEI herausgelösten Seiten-TEI; erzeugt wird der Mirror von `scripts/edition/generate_edition_data.py`, sodass das gesamte Korpus ohne Server bereitsteht. Der Viewer bildet eine Bild-Text-Synopse. Faksimile und zugehöriger Text stehen nebeneinander, sodass beide Seite für Seite verglichen werden können. Das Faksimile wird im Ansichtsmodus über OpenSeadragon dargestellt[^11] und erlaubt stufenloses Zoomen, Verschieben und Drehen, mit den erkannten Layout-Regionen als Overlay. Der Textbereich ist zwischen drei Quellen umschaltbar, dem aufbereiteten OCR-Rohtext, der gerenderten TEI-Fassung, also dem aus dem TEI-XML erzeugten formatierten Lesetext, und dem TEI-XML-Quelltext selbst. Leerseiten erkennt der Viewer vorab, bevorzugt am TEI-Marker `<pb type="blank"/>`, ersatzweise über eine Textregel auf dem OCR-Ergebnis, und kennzeichnet sie als solche, statt fehlerhafte Regionen oder OCR-Artefakte anzuzeigen.

Daneben stehen weitere, direkt aufrufbare Seiten:

- [Korpus-Übersicht](https://chpollin.github.io/zbz-ocr-tei/) mit sortierbarer Tabelle, Workflow-Ampeln und Filtern über Strom und Status  
- [Methode](https://chpollin.github.io/zbz-ocr-tei/methode.html) als statische Seite mit Headline-CER, stratifizierten Werten, Literaturvergleich und Limitations  
- [About](https://chpollin.github.io/zbz-ocr-tei/about.html)  
- [Impressum](https://chpollin.github.io/zbz-ocr-tei/impressum.html)

Die Kuration ist in den Viewer integriert und kommt ohne separaten Server aus. Im Repository liegen die Bausteine unter `docs/assets/js/`, der Viewer-Kern in `viewer.js`, der Layout-Editor in `layout-editor.js`, der Transkriptions-Editor in `transcription-editor.js` und die Speicherschicht in `fs-access.js`. Layout und Text tragen je einen eigenen, unabhängigen Bearbeitungsschalter. Beim Wechsel in den Layout-Editor löst die Faksimile-Anzeige OpenSeadragon durch eine einfache, bearbeitbare Overlay-Ebene ab; darin lassen sich Regionen-Boxen auswählen, verschieben, skalieren, neu aufziehen und löschen, ihr Typ ändern und ihre Lesereihenfolge per Ziehen ordnen. Die Boxen werden als bildrelative Prozentkoordinaten geführt (0 bis 100, bezogen auf die in der Layout-Analyse festgehaltenen Seitendimensionen), sodass sie zoom- und auflösungsunabhängig deckungsgleich auf Faksimile und Overlay liegen; der Editor ist das Werkzeug, mit dem die von der maschinellen Layout-Analyse vorgeschlagenen Boxen fachlich geprüft und korrigiert werden. Der Transkriptions-Editor bietet zwei Einstiege, das direkte Editieren des OCR-Rohtexts und das direkte Editieren des TEI-XML-Quelltexts. Die gerenderte TEI-Ansicht bleibt bewusst schreibgeschützt, weil ein Editieren des formatierten Lesetexts nur den Text ohne die Auszeichnung zurückgeben würde; strukturelle Eingriffe gehören daher in den XML-Modus.

Ein einziger Speichern-Button persistiert alle ungesicherten Ströme auf einmal (Layout, Text/TEI, Manifest). In Chromium-Browsern schreibt der Viewer über die File System Access API direkt in den lokalen Arbeitsbaum des Repositorys; wo diese Schnittstelle fehlt, fällt er auf den Datei-Download zurück. Jede Speicherung legt die Nutzlast doppelt ab, kanonisch nach `output/`, wo die Pipeline sie tatsächlich konsumiert, und in den Mirror `docs/data/`, sodass der server-lose Viewer den gespeicherten Stand nach einem Neuladen anzeigt. Ein konkreter Durchlauf sieht so aus: im Layout-Editor von Dokument 570 werden die Regionen einer Seite korrigiert und gespeichert; der Viewer schreibt das Layout-JSON nach `output/layout/570/` und in den Mirror; der Aufruf `python -m scripts.tei.tei_unified --doc 570 --reassemble` baut anschließend das finale TEI aus dem korrigierten Layout neu, wobei kuratierte Seiten je einen Modell-Aufruf kosten und unveränderte Seiten aus dem Cache kommen. Dieser bewusst server-lose Schnitt vermeidet Backend-Betrieb und Mehrnutzer-Konflikte; der Re-Lauf bleibt ein manueller Schritt. (Ausblick: Dieser Schritt ließe sich über die GitHub-Plattform schließen, etwa indem ein Commit der gespeicherten Datei einen GitHub-Actions-Lauf auslöst, der `--reassemble` ausführt und das regenerierte TEI samt Mirror zurückschreibt.)

Der Bearbeitungsstatus je Strom (siehe Abschnitt 4\) wird im Viewer per Klick auf die Status-Ampel weitergeschaltet und spiegelt sich in der Korpus-Übersicht. Die erste tatsächliche Änderung, etwa eine verschobene Box oder ein editiertes Zeichen, setzt den betroffenen Strom automatisch von unverifiziert auf in Arbeit; das bloße Öffnen eines Editors ändert den Status noch nicht. Solange Änderungen nicht gespeichert sind, warnt das Interface beim Verlassen der Seite. Der leitende Gedanke ist, dass die Ansicht der Daten selbst zum Kurationswerkzeug wird. Die Editorinnen und Editoren arbeiten direkt in der Darstellung, in der sie die Texte auch lesen und prüfen, und bessern die Fehler der Pipeline dort aus, wo sie sichtbar werden; die Vertrautheit mit den Texten wächst dabei mit.

Ergänzend wurden 79 sichere Leerseiten in 15 Dokumenten erkannt und als `<pb type="blank"/>` in die finalen TEI projiziert. Die Erkennung stützt sich auf zwei unabhängige Signale. Eine Textregel klassifiziert die Seite als leer, wenn der OCR-Text praktisch leer ist, das heißt höchstens fünf Zeichen umfasst, kein alphanumerisches Zeichen enthält oder lediglich aus einem Blank-Page-Vermerk der Texterkennung besteht. Die Docling-Layoutanalyse entscheidet über die Sicherheit dieser Einstufung. Findet sie null Regionen, gilt die Seite als sicher leer und der Marker wird gesetzt; findet sie dagegen Regionen, bleibt die Seite im Manifest mit einem Review-Flag zur manuellen Prüfung stehen und wird von der Projektion ausgenommen (im aktuellen Korpus trat kein solcher Konflikt auf). Für den Export stehen Per-Strom-Einzeldownloads in einem Export-Menü bereit; ein ZIP-Bündelexport auf JSZip-Basis ist entworfen und noch nicht eingebunden.

## **6 Qualität und methodologische Einordnung**

## **6 Qualität und methodologische Einordnung**

Die Qualität der Pipeline wird auf zwei Wegen geprüft. Die Zeichenfehlerrate (Character Error Rate, CER) misst die Texttreue gegen die manuell erstellten Referenz-TEIs; sie trägt die Abschnitte 6.1 bis 6.3. Da die Referenzen nur 25 der 285 Dokumente abdecken und die CER weder Richtlinienkonformität noch Strukturqualität erfasst, beschreibt Abschnitt 6.4 die Qualitätssicherung jenseits der CER, eine dreistufige Architektur aus deterministischer Validierung, agentischer Verifikation am Faksimile und menschlicher Adjudikation.

### **6.1 Vergleichsmethodik gegen die Referenz-TEIs**

#### Definition und Implementierung

Die CER ist der Anteil der Zeichen im Referenztext, die im erzeugten Text abweichen, definiert als Levenshtein-Distanz zwischen Referenz und Hypothese, geteilt durch die Zeichenzahl der Referenz. Die Levenshtein-Distanz ist die minimale Anzahl an Einzelzeichen-Operationen (Einfügung, Löschung, Ersetzung), um die eine Fassung in die andere zu überführen;[^12] implementiert ist sie über `rapidfuzz.distance.Levenshtein`. Aggregationseinheit ist das Dokument. Ein Bootstrap auf Dokumentebene (n \= 25, B \= 10 000, Seed 42\) liefert Mittelwert und 95-%-Vertrauensbereich. Zur Einordnung dient die Transkribus-Konvention, nach der unter 2 % als publikationsreif, 2 bis 5 % als forschungstauglich und 5 bis 10 % als brauchbar für Volltextsuche gilt.[^13] Eine hohe CER bedeutet dabei nicht zwingend schlechte Zeichenerkennung; sie kann ebenso aus fehlerhafter Lesereihenfolge bei komplexem Layout folgen[^14] oder daraus, dass Mistral Document AI ein generelles, nicht auf historische Schrift spezialisiertes Modell ist. Die Berechnung selbst ist ein einzelner Funktionsaufruf;[^15] die methodische Substanz liegt in der Aufbereitung der beiden Texte und in der Wahl der Referenz.

#### Gegen welche Referenz gemessen wird

Die CER misst die Abweichung von einer gewählten Referenz und trifft keine Aussage über objektive Korrektheit. Bei TEI-Ground-Truth ist deshalb vorab festzulegen, welche Lesart die Referenz bildet, denn TEI hält an mehreren Stellen zwei konkurrierende Fassungen desselben Textes vor. `<sic>` / `<corr>` kennzeichnet eine überlieferte fehlerhafte Form gegenüber der editorischen Korrektur; `<abbr>` / `<expan>` eine Abkürzung gegenüber ihrer Auflösung. Das Experiment misst gegen die kuratierte Zielfassung und wählt bei `<sic>` / `<corr>` die korrigierte Form (Regel E3). Das Paar `<abbr>` / `<expan>` kommt in den 25 Referenz-TEIs nicht vor und wird von der Pipeline nicht erzeugt; die Extraktion führt deshalb keine Sonderregel dafür und wäre bei künftiger Ground Truth mit diesem Paar um eine `<choice>`\-analoge Auflösung zu erweitern. Die Wahl der kuratierten Zielfassung hat eine messbare Konsequenz, die Beispiel 5 zeigt. Enthält die Referenz selbst einen Transkriptionsfehler, zählt eine korrektere Erkennung als Differenz; solche Fälle erhöhen die gemessene CER ohne Pipeline-Verschulden und begrenzen das mit dieser Methodik Erreichbare. Abschnitt 6.4 katalogisiert die bekannten Fehler der Referenzen.

#### Zerlegung in Fidelity und Scope

Die Editieroperationen werden in zwei Kategorien zerlegt, die unterschiedliche Ursachen trennen. Fidelity erfasst echte Erkennungsfehler, also Substitutionen (gezählt als Länge des größeren Blocks), sämtliche Löschungen und kleine Einfügungen; sie ist das Maß für die Lesequalität. Scope erfasst zusammenhängende Einfügungen ab einer Schwelle von 50 Zeichen (`SCOPE_BLOCK_MIN` in `scripts/eval/evaluate_ocr.py`), die typischerweise aus Textbestandteilen stammen, welche die Pipeline erfasst, die selektiv transkribierte Referenz aber nicht enthält, etwa Mastheads, Autorzeilen oder Editionsmetadaten. Die Fidelity-CER wertet nur die erste Kategorie; die Volltext-CER schließt den Scope-Anteil als Diagnosegröße ein. Beide Kategorien summieren sich zeichengenau zur Levenshtein-Distanz, ein Regressionstest schreibt diese Summenidentität fest. Da die Fidelity-Werte von der Schwelle abhängen, nennt jede Zitation die Schwelle mit; diese Regel ist aus der unabhängigen Gegenprobe (6.4) hervorgegangen.

#### TEI-Extraktion

Vor dem Vergleich erzeugt `extract_text_for_comparison()` aus jedem TEI einen Vergleichstext. Dieselbe Funktion verarbeitet beide Seiten, Referenz-TEI wie Pipeline-TEI, damit gemessene Differenzen ausschließlich aus dem Textinhalt stammen.

| Nr. | Regel | Effekt |
| :---- | :---- | :---- |
| E1 | XML-Parser über `xml.etree.ElementTree`, Namensraum-Präfixe entfernen | `{tei}p` wird zu `p` |
| E2 | nur Inhalt unterhalb von `<body>` | `<teiHeader>`, `<front>`, `<back>` werden ignoriert |
| E3 | `<choice><sic>X</sic><corr>Y</corr></choice>` wird zu `<corr>` | bei Schreibvariante gilt die kuratierte Lesart |
| E4 | `<choice>` ohne `<corr>`, nur `<sic>` wird zu `<sic>` | Fallback |
| E5 | `<note place="foot">…</note>` ausgeschlossen (Default) | separat edierte Fußnoten würden den Fließtext-Vergleich verzerren; via `include_footnotes=True` einschaltbar |
| E6 | `<lb/>` ohne `break="no"` wird zu einem Leerzeichen | Druck-Zeilenumbruch ist eine Wortgrenze |
| E7 | `<lb break="no"/>` wird zu keinem Zeichen | getrenntes Wort wird zusammengezogen (Hu \+ manismus wird zu Humanismus) |
| E8 | `<pb/>` wird zu zwei Zeilenumbrüchen `\n\n` | Seitengrenze bleibt erkennbar |
| E9 | alle übrigen Elemente (`<hi>`, `<persName>`, `<bibl>`, `<title>`, `<head>`, `<p>`, `<div>` …) rekursiv als Innentext | Markup wird transparent: `<hi>Wort</hi>` wird zu Wort |
| E10 | Attributwerte werden nicht übernommen | Seitenzahlen aus `<pb n="223"/>`, GND-IDs aus `ref`\-Attributen erscheinen nicht im Vergleich |
| E11 | XML-Tails werden beim Eltern-Element angehängt | korrekte Reihenfolge bei `<p>Wort1<hi>Wort2</hi>Wort3</p>` |
| E12 | bei XML-Parse-Fehler Regex-Fallback `re.sub(r'<[^>]+>', '', content)` | eine nicht wohlgeformte Datei bricht den Korpuslauf nicht ab |

#### Normalisierung

Nach der Extraktion durchläuft der Text `normalize_for_comparison()`, ebenfalls beidseitig identisch. Die Regeln vereinheitlichen typografische Varianten, die keine inhaltlichen Unterschiede sind.

| Nr. | Regel | Mapping |
| :---- | :---- | :---- |
| N1 / N2 | französische Guillemets zu ASCII `"` | « (U+00AB), » (U+00BB) |
| N3 | deutsches unteres Anführungszeichen zu ASCII `"` | „ (U+201E) |
| N4 / N5 | spitze Anführungszeichen zu ASCII `'` | ‹ (U+2039), › (U+203A) |
| N6 / N7 | Backtick, Akut zu ASCII `'` | \` (U+0060), ´ (U+00B4) |
| N8 bis N12 | Hyphen, geschützter Bindestrich, Halbgeviert-, Geviert-, Ziffernstrich zu ASCII `-` | U+2010, U+2011, U+2013, U+2014, U+2012 |
| N13 | weicher Trennstrich entfernen | U+00AD |
| N14 | Leerzeichen vor `; : ? !` entfernen (frz. Typografie) | `re.sub(r' +([;:?!])', r'\1', text)` |
| N15 | mehrfacher Whitespace zu einem Leerzeichen | `re.sub(r'\s+', ' ', text)` |
| N16 bis N19 | englische Anführungszeichen und Apostrophe zu ASCII `"` / `'` | U+201C, U+201D, U+2018, U+2019 |
| N20 | Whitespace am Anfang und Ende entfernen | `strip()` |
| N21 | Unicode-Normalform NFC | `unicodedata.normalize('NFC', text)` |

Bewusst nicht normalisiert werden Groß- und Kleinschreibung, Diakritika, Satzzeichen, die Unterscheidung von ß und ss sowie Zahlen, da dies substantielle Differenzen sind. Der case-sensitive Default folgt der Werkzeugpraxis von dinglehopper[^16] und jiwer, die Lowercasing als Opt-in führen; eine optionale case-insensitive Sekundärmetrik existiert (`casefold=True`). Die Erhaltung von Akzenten prüft eine eigene Metrik (HCPR) getrennt.[^17] Die inzwischen erfolgte Apostroph-Normalisierung des ausgelieferten Korpus (6.4) ist für die CER neutral, weil N16 bis N19 beide Apostrophformen auf dasselbe ASCII-Zeichen abbilden.

#### Verifikation der Messmethodik

Diese Verifikation betrifft die Korrektheit der CER-Messung selbst und ist von der TEI-Schemavalidierung (Abschnitt 4\) zu unterscheiden. Sie ruht auf vier Schichten. Erstens 18 handgerechnete Regressionstests (`tests/test_cer_extraction.py`), die unabhängig vom Korpus-Ergebnis die kanonische Formel, Case-Sensitivität, das Unterbleiben von Trimming, die `<choice>`\-Auflösung, die Normalisierung und die Fidelity/Scope-Zerlegung samt zeichengenauer Summenkontrolle festschreiben. Zweitens die Vereinheitlichung der zuvor drei separaten CER-Implementierungen (`benchmark_cer`, `cer_statistics_full`, `tei_validator --compare-ref`) auf gemeinsame kanonische Funktionen, sodass alle drei Pfade für dasselbe Dokument dieselbe Zahl liefern. Drittens der Abgleich der Konventionen mit externen Standards, dem Nenner als Referenzlänge (Transkribus), der NFC-Normalisierung (OCR-D),[^18] dem case-sensitiven Default (jiwer; OCR-D führt Case-Ignoranz nur als eigene Letter-Accuracy-Metrik), dem Volltextvergleich ohne Alignment-Trimming (dinglehopper)[^19] und dem paired Bootstrap für Deltas (Du 2025\).[^20] Viertens eine unabhängige Gegenprobe, die alle publizierten Werte ohne Repository-Code reproduziert hat (6.4). Die Vergleichbarkeit von CER-Werten zwischen Werkzeugen bleibt trotzdem begrenzt, unter anderem weil bereits die Umwandlung strukturierter Ground Truth in Vergleichstext zur Fehlerquelle wird; die dokumentierten Extraktions- und Normalisierungsregeln sind die projektinterne Festlegung dieser Transformation.

#### Quantitative Schemavalidierung

Alle 285 finalen TEI validieren gegen `zbz_hersch.rng`, mit null blockierenden Verstößen gegen die Projektregeln R1 bis R7; die Schema- und Header-Prüfungen laufen zusätzlich als pytest-Gates bei jedem Push. Die informative Warnungsbilanz nach den Bestandsläufen (6.4) umfasst 2 017 Vorkommen in 256 Dokumenten und wird von zwei bewussten Kurationssignalen getragen, den leeren Sprecher-Slots der Interview-Dokumente (W17, 830 Vorkommen in 15 Dokumenten) und der Lesereihenfolge-Worklist (W19, 826 Seiten in 214 Dokumenten). Beide markieren Arbeitsvorrat und keinen Schemaverstoß. Die übrigen Klassen sind kleinere Konformitäts-Worklists zur div- und figure-Konvention (W15 mit 73, W16 mit 144 Vorkommen) sowie Einzelbefunde im ein- bis niedrigen zweistelligen Bereich.

### **6.2 Fünf Beispiele aus unterschiedlichen Dokumenttypen**

Jedes Beispiel nennt Doc-ID, Layout-Typ und Sprache, stellt Referenz- und Pipeline-Stelle gegenüber, verweist auf die anwendbaren Regeln und gibt die lokale CER an.

#### Beispiel 1: Dokument 130 (Typ A, Französisch), Titel im Versalsatz

Referenz (`data/source/reference_tei/130.xml`):

\<head\>

  \<title type="main"\>L'école de nos périls\</title\>

  \<title type="sub"\>Le problème de l'élite ouvrière\</title\>

\</head\>

Nach Extraktion (E2, E6, E9): `L'école de nos périls Le problème de l'élite ouvrière`. Das OCR (`output/mistral_results/130_p3.md`) liefert denselben Titel durchgängig in Versalien. Jeder kasusbehaftete Buchstabe zählt als Substitution; unter den Vergleichsregeln (nach Apostroph-Normalisierung N16 bis N19) beträgt die Levenshtein-Distanz exakt 41 bei einer Zählbasis von 53 Zeichen, lokale CER 41/53 ≈ 77 %. Versalsatz wird als Schreibvariante bewusst nicht normalisiert (6.1). Im Gesamtdokument verdünnt sich der Effekt, denn die Zählbasis des Dokuments beträgt 24 382 Referenzzeichen; die Dokument-CER bleibt einstellig.

#### Beispiel 2: Dokument 1060 (Typ A, Deutsch), `<choice>` und Schweizer gegen deutsche Orthografie

Referenz (`data/source/reference_tei/1060.xml`):

\<p\>Wenn ich diesen Preis nicht \<choice\>\<sic\>gnügend\</sic\>\<corr\>genügend\</corr\>\</choice\> verdient habe, ist er …\</p\>

Regel E3 extrahiert die kuratierte Form „genügend"; das OCR schreibt „gnügend", eine Einfügung des e, lokale CER auf dem Wort 1/8 ≈ 12,5 %. Zweite Stelle im selben Dokument: Referenz „Füssen" (Schweizer Orthografie) gegen OCR „Füßen", Distanz 2 (s durch ß ersetzt, zweites s gelöscht), lokale CER 2/6 ≈ 33 %. Die ss/ß-Differenz wird als substantielle orthografische Differenz nicht normalisiert.

#### Beispiel 3: Dokument 2530 (Typ B, Französisch), Typografie und Editionsmetadaten

Die Referenz schreibt „c'est Israël – ses habitants, et non pas moi – qui aura à les courir" mit Halbgeviertstrichen, das OCR mit Geviertstrichen; nach N10/N11 ist die Stelle identisch, Differenz 0\. Bei der französischen Doppelpunkt-Typografie schreibt das OCR „un premier principe :" mit Leerzeichen vor dem Doppelpunkt, die Referenz „un premier principe:" ohne; N14 entfernt das Leerzeichen, Differenz 0\. Anders die Editionsmetadaten am Seitenkopf. Masthead und Autorzeile (`LA SITUATION D'ISRAËL`, `JEANNE HERSCH`) umfassen 34 Zeichen, die in der Referenz fehlen; da unter der 50-Zeichen-Schwelle, zählen sie als Fidelity-Einfügungen (lokale Last auf der Seite etwa 34/1 860 ≈ 1,8 %). Die Normalisierung eliminiert typografische Unterschiede; nicht transkribierte Randbestandteile unter der Scope-Schwelle werden hingegen als echte Differenz mitgemessen.

#### Beispiel 4: Dokument 1330 (Typ D, Französisch), transparentes Markup

Referenz (`data/source/reference_tei/1330.xml`):

\<p\>\<persName ref="GND:118583530"\>Jacques Monod\</persName\>, par exemple, a publié un livre célèbre,

   et que je trouve admi\<lb break="no"/\>rable, intitulé

   \<bibl ref="GND:4678418-4"\>\<hi rendition="\#i"\>Le hasard et la nécessité\</hi\>\</bibl\>.\</p\>

Nach Extraktion (E7 zieht „admirable" zusammen, E9 behält nur Innentext, E10 ignoriert die `ref`\-Attribute) bleibt der reine Satz. Das OCR trägt Markdown-Sterne um den Buchtitel (`*Le hasard et la nécessité*`); im End-to-End-Vergleich wird daraus im Pipeline-TEI `<hi rendition="#i">…</hi>`, das E9 auf beiden Seiten entfernt. Die Texte sind identisch, Differenz 0\. Die Pipeline darf typografische Auszeichnung frei umsetzen, ohne CER-Strafe; GND-Identifikatoren in Attributen berührt der Vergleich nicht.

#### Beispiel 5: Dokument 1440 (Typ B, Deutsch), fehlerbehaftete Referenz

Referenz (`data/source/reference_tei/1440.xml`):

\<p\>… 25\. Kongreß der KPdSU, 5\. Februar 1976, "lnforma\<lb break="no"/\>tionsbulletin" Nr. 6/7, 1976, Wien.\</p\>

Die Referenz enthält ein kleines l statt eines großen I in „lnformationsbulletin", eine in der Transkribus-Referenz nicht korrigierte Verwechslung. Das OCR schreibt Guillemets und ein korrektes „Informationsbulletin". Nach N1/N2 sind die Anführungszeichen gleich; es bleibt die Substitution l zu I, lokale CER auf dem Wort 1/20 \= 5 %, gezählt gegen die Pipeline, obwohl sie hier die korrekte Form liefert (Annahme: der Eigenname lautet „Informationsbulletin"; markierte Inferenz, hohe Konfidenz). Das Beispiel zeigt, dass die CER die Differenz zur Referenz misst und die Referenz selbst eine fehlerbehaftete Transkription ist. Der Fehlerbestand der Referenzen ist systematisch katalogisiert (6.4).

### **6.3 Korpus-Ergebnis und Datenlage**

Headline-Resultat des aktuellen Korpus (n \= 25, Seed 42, B \= 10 000, Stand der versionierten Regeneration 2026-07-08 nach den Bestandsläufen und der Doppelseiten-Reparatur des Dokuments 30, siehe 6.4). Die Fidelity-CER (Scope-Schwelle 50 Zeichen) liegt bei einem Median von 1,28 % (95-%-CI \[1,06; 2,50\]) und einem Mittel von 2,08 % (95-%-CI \[1,51; 2,73\]). Die Volltext-CER als Diagnosegröße, die den Pipeline-Mehrtext gegenüber den selektiv transkribierten Referenzen einschließt, liegt bei einem Median von 9,59 % und einem Mittel von 18,36 %; der Scope-Anteil allein beträgt im Mittel 16,28 %. Nach Transkribus-Konvention liegt der Median im Bereich publikationsreif, der Mittelwert im Bereich forschungstauglich. Der paired Bootstrap gegen die Roh-OCR zeigt den Pipeline-Gewinn auf Dokumentebene, mit 17 von 25 Dokumenten verbessert und 8 verschlechtert.

Der Weg zu diesen Werten ist selbst Teil des Ergebnisses. Die erste Messung wies ein Fidelity-Mittel von 4,26 % aus. Die Fehleranalyse der Ausreißer führte auf einen Generator-Defekt, die Überdetektion von Fußnoten, bei der Haupttext in ausgeschlossene `<note>`\-Elemente geriet und als Löschung zählte. Eine referenzverifizierte Demotion (Rückführung nur bei einem nachweisbaren zusammenhängenden Lauf von mindestens 150 Zeichen im Referenz-Body) senkte das Mittel über 3,99 % auf 2,71 %; die Bestandsläufe vom 07.07.2026 (vor allem Seitenzahl-Echos und urteilsgesteuerte Demotion, 6.4) senkten es auf 2,50 %, die Reparatur der verlorenen Doppelseiten-Hälfte des Dokuments 30 auf 2,08 %. Jede Stufe ist im Entscheidungsregister mit Datum und Methode festgehalten. Die Reproduktion erfolgt über `python -m scripts.eval.cer_statistics_full --seed 42 --bootstrap-n 10000`; das Ergebnis liegt versioniert als `docs/data/cer_statistics.json` vor, die Methodik in `knowledge/specification.md` und `knowledge/cer-methodology.md`.

Auf der Datenseite gilt der in Abschnitt 2 beschriebene Trichter. Von den 286 gelieferten Dokumenten besitzen 285 ein finales TEI; das gelieferte PDF ohne finales TEI (Dokument 10\) ist registriert und extern zu klären.

#### Werte je Dokument

Die Tabelle schlüsselt alle 25 gemessenen Dokumente nach Fidelity-CER auf und ordnet jedem erhöhten Wert seine Hauptursache zu. Die Streuung stammt aus drei strukturellen Mustern (Mehrtext gegen selektive Referenzen, Fußnoten-Fehlklassifikation, Doppelseiten-Defekte); die Zeichenerkennung selbst trägt sie nicht. Die vollständige Drei-Zahlen-Zerlegung je Dokument liegt in `docs/data/cer_statistics.json`.

| Doc | Typ | Sprache | Fidelity % | Hauptursache |
| :---- | :---- | :---- | ----: | :---- |
| 1440 | B | DE | 5,87 | Scope plus fehlerbehaftete Referenz |
| 760 | D | FR | 5,87 | Doppelseite, verlorene Bildunterschriften und unsegmentierte Paginierung, gegenprobenverifiziert; die Lesereihenfolge selbst hält am Faksimile |
| 300 | D | FR | 5,00 | Scope plus Zusatzseiten |
| 1410 | B | FR | 4,24 | Scope plus Zusatzseiten |
| 130 | A | FR | 2,93 | nahezu sauber |
| 1910 | B | DE | 2,82 | Rest durch die urteilsgesteuerte Demotion beseitigt |
| 290 | A | FR | 2,56 | durch Fußnoten-Demotion behoben |
| 560 | A | FR | 2,50 | sauber |
| 2310 | A | FR | 2,46 | Scope (JSTOR-Deckblatt) |
| 1520 | C | FR | 2,22 | Zusatzseiten; Fußnoten-Demotion angewandt |
| 2530 | B | FR | 1,83 | sauber |
| 890 | B | DE | 1,37 | Scope |
| 90 | A | DE | 1,28 | durch Fußnoten-Demotion behoben |
| 3040 | B | FR | 1,26 | Scope (Fußnoten) |
| 40 | C | FR | 1,20 | sauber; Fußnoten-Demotion angewandt |
| 1060 | A | DE | 1,14 | Scope |
| 1180 | A | FR | 1,08 | sauber |
| 3020 | B | DE | 1,06 | sauber |
| 1330 | D | FR | 1,03 | Scope |
| 30 | A | FR | 0,90 | repariert, verlorene linke Hälfte der Doppelseite 1 ergänzt, Zonen korrigiert |
| 100 | A | FR | 0,85 | sauber |
| 570 | A | FR | 0,79 | Scope (extrem) |
| 2635 | A | DE | 0,73 | sauber |
| 830 | D | FR | 0,69 | sauber |
| 580 | A | FR | 0,30 | Scope (extrem) |

#### Einordnung in den Forschungsstand

Print-kalibriert gelesen liegt der Fidelity-Median von 1,28 % zwischen dem besten spezialisierten Druck-Stack (Transkribus mit LLM-Nachkorrektur, 0,84 %) und Transkribus allein (3,67 %), solide für historischen Druck, aber nicht an der Spitze; das technische Optimum erreichen nur die besten Einzeldokumente (0,3 bis 0,8 %). Die Transkribus-Bewertungsbänder stammen primär aus der Handschriftenerkennung und setzen die Latte niedriger, als eine reine Druck-OCR-Aufgabe es rechtfertigt.

| Quelle | Verfahren | Sprache | CER |
| :---- | :---- | :---- | :---- |
| Crosilla et al. 2025 | Transkribus Print M1 \+ Gemini 2.0 Flash Nachkorrektur | deu (Fraktur) | 0,84 % |
| Crosilla et al. 2025 | Gemini 2.0 Flash zero-shot | deu | 1,27 % |
| Crosilla et al. 2025 | Transkribus Print M1 allein | deu | 3,67 % |
| Crosilla et al. 2025 | GPT-4o direkt | deu | 6,31 % |
| Levchenko 2025 | Gemini 2.5 Pro | rus (18. Jh.) | 3,36 % |
| Levchenko 2025 | Gemini 2.5 Flash | rus | 4,94 % |
| Levchenko 2025 | traditionelle OCR | rus | 21–45 % |
| Transkribus-Dokumentation | Richtwert | allgemein | 0,5–2 % |

Kein Eintrag ist ein Like-for-like-Benchmark; die Vergleichbarkeitsdimensionen je Eintrag stehen maschinenlesbar in `docs/data/cer_statistics.json` und ausführlich in `knowledge/literature-comparison.md`.

#### Korpusweite Plausibilitätsschätzung und Sprach-Audit

Für die 260 Dokumente ohne Ground Truth dient die Dictionary Hit Rate als Proxy, der Anteil der OCR-Wörter, die in französischen und deutschen Wörterbüchern stehen. Der Median liegt bei 97,7 %, 92 % der Dokumente erreichen mindestens 90 % Trefferquote, und die Ausreißer unter 75 % sind korrekt klassifizierte fremdsprachige Dokumente. Der zusammengesetzte Schätzer generalisiert statistisch nicht (negatives LOOCV-R²), weshalb der korpusweite Wert eine Plausibilitätsschranke bleibt und keine Messung ist. Ein Nebenbefund des Sprach-Audits: 284 der 285 Dokumente sind korrekt sprachklassifiziert, drei Etiketten wurden korrigiert.

#### Grenzen der Messung

Ground Truth existiert nur für 25 Dokumente, sodass Korpusaussagen Schätzungen bleiben. Das Referenz-Subset weicht auf der Zeichenmenge signifikant vom Korpus ab (Kolmogorov-Smirnov-Test auf `n_chars`, p \= 0,0139), während Sprache, Layout-Typ, Publikationsform und Seitenzahl vergleichbar sind; die Abweichung ist in der JSON offen deklariert. Die CER misst zudem gegen eine selbst fehlerbehaftete Referenz (Beispiel 5\) und ist damit eine Obergrenze der wahren Fehlerrate; der Fehlerbestand der Referenzen steht in `knowledge/ground-truth-map.md`. Die Run-zu-Run-Varianz der nicht-deterministischen LLM-Stufen ist im Pilot vernachlässigbar (5 Dokumente, je 3 Läufe, mittlere Streuung 0,04 Prozentpunkte), und die frequenzbasierte HCPR-Adaption unterschätzt Substitutionen.

### **6.4 Qualitätssicherung jenseits der CER**

Die CER beantwortet die Frage nach der Texttreue für die 25 referenzgedeckten Dokumente. Für das ganze Korpus und für die Richtlinienkonformität organisiert das Projekt eine dreistufige Architektur, die strikt trennt, welches Verfahren welche Aussage treffen darf. Die erste Ebene ist die deterministische Validierung (Schema, Projektregeln, Konformitätsregeln und eine Familie von Audits, die reproduzierbar zählen und flaggen). Die zweite Ebene ist die agentische Verifikation; KI-Agenten prüfen stratifizierte Stichproben am Faksimile und liefern evidenzgebundene Befunde mit Fundstelle, wörtlichem Beleg und Schweregrad. Diese Befunde sind Verdachtsurteile und werden nie als Korrektheitsnachweis gewertet. Die dritte Ebene ist die menschliche Adjudikation; ausschließlich sie vergibt den Status verifiziert. Diese Trennung ist eine Lehre aus dem Projektverlauf, denn ein früheres agentenbasiertes Qualitäts-Screening hatte das gesamte Korpus als geprüft markiert, ohne dass ein Mensch beteiligt war; es wurde abgeschafft und seine Einträge wurden aus den ausgelieferten Dokumenten entfernt.

Auf der Audit-Ebene vermessen fünf Werkzeuge die Richtlinienkonformität korpusweit. Der Stand vor den Bestandskorrekturen: die Zeichennormalisierung war die größte Lücke (88 978 gerade Apostrophe zwischen Buchstaben in 241 Dokumenten, daneben Guillemet- und Leerzeichenklassen, von denen sich die Leerzeichenklasse auf französischen Seiten überwiegend als korrekte Typografie erwies); die gedruckte Paginierung fehlte breit (224 Dokumente führten in `pb@n` die Scan-Position, 18 die Druckfolio, 9 gemischt); das OCR-Kursivsignal überlebt die Pipeline nahezu vollständig (18 betroffene Seiten in 12 Dokumenten, die Hauptursache fehlender `<hi>`\-Auszeichnung liegt in der OCR-Engine selbst, weshalb eine bildbasierte LLM-Nacherkennung geprüft und verworfen wurde); die Relationenintegrität ist nahezu sauber; das fünfte Audit fand 63 Fußnoten-Überdetektions-Kandidaten in 26 Dokumenten. Auf der Verifikationsebene wurden alle 63 Kandidaten am Faksimile geprüft, mit klarem Ergebnis. 59 sind laufender Haupttext im Fußnotenrahmen, 2 abgesetzte Zitate, 2 echte Fußnoten (Audit-Falsch-Positive). Bei 37 Kandidaten auf 35 Seiten zeigt sich ein Rollentausch, bei dem die echte Fußnote der Seite als gewöhnlicher Absatz im Body liegt, während der Haupttext den Fußnotenrahmen erhielt. Eine Kalibrierungsrunde über weitere stratifizierte Seiten ergab zudem, dass das Lesereihenfolge-Warnsignal als Prädiktor für tatsächlich falsche Reihenfolge schwach ist (5 von 6 geprüften Verdachtsseiten lasen korrekt), beim Hinsehen aber andere reale Defekte zutage fördert, etwa still fallengelassene Nicht-Artikel-Blöcke auf Zeitschriftenseiten und eine geleakte Modell-Absage im Text eines Dokuments, verursacht durch eine Wiederholungsschleife der Basis-OCR und inzwischen durch eine Einzelseiten-Reparatur ersetzt.

Eine unabhängige Gegenprobe hat die publizierten CER-Werte von außen reproduziert, ohne Code aus dem Repository, mit eigenständig implementierter Extraktion und Normalisierung, einer zweiten Levenshtein-Engine und eigener Aggregation. Alle damaligen Headline- und Einzelwerte wurden exakt bestätigt. Die inhaltliche Klassifikation der größten Fehlerblöcke ergab, dass echter Textverlust die Ausnahme ist und Apparat-Einfügungen unter der Scope-Schwelle sowie Konventionsdivergenzen der Referenz die Fidelity-Werte nach oben treiben, ohne Erkennungsfehler zu sein. Die Ground Truth selbst wurde vollständig inventarisiert. Die 25 Referenz-TEIs sind in den tragenden Körper-Konventionen richtlinienkonform, tragen aber korpusweit einen Transkribus-Stub als Header und einen eigenen, katalogisierten Fehlerbestand, darunter Normdaten-Präfix-Drift, Migrationsreste und eine nicht wohlgeformte Datei (1520.xml, drei überkreuzte Element-Verschachtelungen); für diese liegt eine reparierte Kopie samt Änderungsnachweis vor, die Meldung an die ZBZ ist vorbereitet. Landkarte und Ausnahmekatalog stehen in `knowledge/ground-truth-map.md`.

Aus Audits und Verifikation folgen die Bestandskorrekturen, nachgelagerte deterministische Läufe auf dem ausgelieferten Korpus, jeweils mit Backup, idempotent und mit Audit-Messung vorher und nachher, also vollständig reversibel und überprüfbar. Drei Festlegungen sind ratifiziert. `pb@n` trägt die gedruckte Seitenzahl in eckigen Klammern, wie es die Referenzen durchgängig tun, mit der Scan-Nummer als ehrlichem Fallback ohne sicheres Signal; korrigiert wird hybrid, sichere Klassen maschinell und unsichere als Kurations-Worklists; die Verifikationstiefe ist die gezielte Adjudikation bekannter Konflikte samt Ergänzungsstichproben. Alle drei Läufe sind am 07.07.2026 vollzogen und haben die Trockenlauf-Vorschauen exakt reproduziert. Die Apostroph-Normalisierung senkte die betroffene Audit-Klasse von 88 978 Vorkommen auf null. Der Druckfolio-Lauf stellte 1 753 Seiten aus Fußzeilen-Erkennung, 1 033 aus Interpolation und 151 aus stabilem Offset um, beließ 970 Scan-Nummern als Fallback und entfernte 1 212 Seitenzahl-Echo-Absätze; danach führen 114 Dokumente vollständige und 120 teilweise Druckfolio-Abdeckung, 51 bleiben beim Fallback. Die urteilsgesteuerte Demotion verarbeitete alle 63 Urteile ohne Rest (59 Rückführungen in den Fließtext, 2 Zitat-Überführungen, 2 belassene echte Fußnoten, 19 Marker-Promotionen in 26 Dokumenten). Der Erstlauf legte einen Werkzeugdefekt offen, der in vier Interview-Dokumenten 14 leere Sprecher-Rahmen hinterließ und deren Schema-Validität brach; der Defekt wurde im Werkzeug behoben, die Heilung erfolgte durch einen idempotenten Wiederholungslauf, der nachweislich ausschließlich diese 14 Rahmen entfernte. Die Nachher-Audits bestätigen die Wirkung. Das Paginierungs-Audit klassifiziert nun 204 Dokumente als Druckfolio, 37 als Scan-Sequenz, 10 als gemischt und 34 als unbestimmt (vorher 18 Druckfolio); das Fußnoten-Audit findet statt 63 noch 3 Kandidaten (die 2 bestätigten echten Fußnoten und einen neuen Grenzfall für die Worklist); die Apostroph-Klasse bleibt bei null. Schema, Projektregeln und pytest-Gates sind nach allen Läufen unverändert grün; die CER-Neumessung ergab die in 6.3 ausgewiesene Verbesserung, da die entfernten Echo-Absätze zuvor als Einfügungen zählten.

Die Einordnung des Dokuments 30 ist adjudiziert und der scheinbare Widerspruch zweier Prüfungen aufgelöst. Die Gegenprobe klassifizierte den CER-Ausreißer als echten Textverlust auf Doppelseiten; die Faksimile-Kalibrierung fand auf den von ihr geprüften Doppelseiten vollständigen Text. Beide Befunde stimmen, denn die drei fehlenden Blöcke (540, 451 und 194 normalisierte Zeichen) liegen sämtlich auf der linken Hälfte der ersten Doppelseite (Druckseite \[222\]), die die Kalibrierungsstichprobe nicht umfasste. Am Faksimile ist der Text vollständig lesbar; im ausgelieferten TEI und in sämtlichen OCR-Datenströmen fehlte er. Der Ausreißer war damit echter Erkennungsverlust einer Doppelseiten-Hälfte, den keine Lesereihenfolge-Korrektur beheben kann. Die Reparatur ist vollzogen; die gut lesbare Doppelseite wurde neu gelesen und am Faksimile verifiziert, die drei verlorenen Absätze wurden samt ehrlicher Faksimile-Zonen ergänzt, zwei nachweislich falsche Zonen-Boxen korrigiert und die Seitenzahl auf die Druckfolio \[222\] gehoben. Die Fidelity-CER des Dokuments fiel von 11,59 % auf 0,90 %, womit das Korpus-Maximum verschwindet.

Die geplante maschinelle Umstellung der Lesereihenfolge ist dagegen empirisch widerlegt und verworfen. Der Reassembly-Weg war bereits gesperrt, weil er die Bestandskorrekturen und Hand-Reparaturen zurückdrehen würde; als Ersatz wurde ein test-first gebautes In-Place-Werkzeug erprobt, das Verdachtsseiten byte-schonend in die geometrisch kanonische Ordnung bringt. Die CER-geschützte Probe an Kopien aller 25 Referenzdokumente ergab null Verbesserungen und neun Verschlechterungen bis zu 40 Prozentpunkten. Die Ursachenprüfung zeigt, dass der ausgelieferte Text der beanstandeten Seiten überwiegend korrekt ist und die Zuordnung der Blöcke zu ihren Faksimile-Zonen korrupt, sodass die geometrisch abgeleitete Ordnung verifizierten Text zerstören würde; das deckt sich mit der Kalibrierungsrunde. Das Lesereihenfolge-Warnsignal ist seither als Text- oder Zonen-Verdachtssignal deklariert, seine Auflösung Kurationsarbeit am Faksimile; das Werkzeug bleibt als Dry-Run-Instrument samt dokumentiertem Beweisweg erhalten.

Ehrlich benannt bleibt das Restrisiko dieser Architektur. Die Audits sehen nur, wonach sie suchen; fehlklassifizierte Noten unterhalb der Audit-Schwelle, durch den Rollentausch verlorene echte Fußnoten außerhalb der Kandidatenmenge und die uneinheitliche Auszeichnung fremdsprachiger Passagen (nur 30 der 285 Dokumente tragen überhaupt `<foreign>`) sind quantifiziert oder als Untergrenze belegt, aber nicht behoben. Der erreichbare Anspruch der maschinellen Seite ist, dass alle bekannten Fehlklassen benannt und vermessen sind, die verifizierten deterministisch und reversibel korrigiert werden und der Rest als Arbeitsvorrat in die menschliche Kuration geht.

## **7 Grenzen und mögliche Weiterführung**

Mehrere Aspekte sind unvollständig geblieben oder bewusst nicht bearbeitet worden. Die folgende Liste fasst beide zusammen, von Schwächen des Vorhandenen bis zu Schritten, die ein Anschlussvorhaben unternehmen könnte.

- Auf der Datenseite bleiben extern zu klären die drei digitalisierten, aber nicht als PDF gelieferten Texte (1745, 1750, 1970). Dokument 10 besitzt ein geliefertes PDF, aber noch kein finales TEI; die Nachverarbeitung (Neu-OCR der Seiten, anschließende Layout- und TEI-Stufen) ist vorbereitet und wartet auf die Freigabe des kostenpflichtigen Laufs. Die beiden registrierten Einzeldefekte sind behoben: die Seite mit geleakter Modell-Absage infolge degenerierter Basis-OCR (Dokument 1520, Seite 70\) trägt nach einer Einzelseiten-Reparatur eine ehrliche Teiltranskription mit markierten unleserlichen Stellen, die Volltranskription braucht einen besseren Scan; der adjudizierte Textverlust der ersten Doppelseite des Dokuments 30 ist durch dieselbe gezielte Nachbearbeitung behoben (6.4).  
- Die Lesereihenfolge auf Doppelseiten und Mehrspaltern ist generatorseitig behoben (spalten- und bandbewusste Permutation, regressionsgetestet). Für den ausgelieferten Bestand ist die maschinelle Umstellung empirisch widerlegt und verworfen (6.4); die Verdachtsseiten tragen überwiegend korrekten Text mit korrupter Zonen-Zuordnung und gehen als triagierte Worklist in die Faksimile-Kuration.  
- Die Auszeichnung fremdsprachiger Passagen ist uneinheitlich; ein deterministischer Wendungs-Detektor belegt mindestens 27 Dokumente mit unmarkierten Latein- oder Griechisch-Passagen, und der Sprachcode für Deutsch ist gemischt kodiert. Beides ist Kurationsvorrat mit vorhandener Werkzeugbasis.  
- Kursiv- und Sperrsatz erreichen das TEI nur lückenhaft, weil die Hauptursache in der OCR-Engine liegt, die das Hervorhebungssignal oft gar nicht liefert; was sie liefert, überlebt die Pipeline nahezu vollständig. Eine bildbasierte Nacherkennung per Sprachmodell wurde geprüft und verworfen, da sie nicht deterministisch wäre; die betroffenen Seiten sind auditiert und gehen in die Kuration.  
- Die semantische Anreicherung über Named Entity Recognition und Entity Linking wurde nach einer frühen Erprobung bewusst aus der Pipeline entfernt; das gelieferte Korpus ist entitätsfrei. Die verbindliche Zielform ist inline-GND-Auszeichnung an der Nennstelle, vorgesehen als nachgelagerte Kurationsaufgabe in einem eigenen Annotationswerkzeug; die dafür nötigen Konformitätsregeln sind bereits implementiert und werden auf diesem Output scharf. Die Identifikator-Zuordnung erfolgt dabei ausschließlich über deterministische Normdaten-Abfragen. Ein Sprachmodell kommt dafür nicht zum Einsatz.  
- Der Bearbeitungsstatus der drei Ströme steht bei der Übergabe überwiegend auf unverifiziert. Das ist der vorgesehene Ausgangspunkt: die fachliche Verifikation ist der nächste Schritt auf ZBZ-Seite, mit dem in Abschnitt 5 beschriebenen Werkzeug und der dort angelegten Bearbeitungsspur.  
- Die Run-zu-Run-Stabilität der nicht-deterministischen LLM-Stufe ist pilotgemessen (5 stratifizierte Referenzdokumente, je 3 Regenerationsläufe zu 20 Seiten in isolierte Verzeichnisse, mit dem Produktionsmodell). Die Fidelity-CER streut je Dokument um 0,00 bis 0,13 Prozentpunkte (Standardabweichung, Mittel 0,04); die Verfeinerungsstufe ist in ihrer Textwirkung praktisch deterministisch. Ein Nebenbefund des Piloten ist, dass frische Neugenerierungen in der absoluten Fidelity deutlich über dem ausgelieferten Bestand liegen, weil die finalen TEI akkumulierte Korrekturen tragen, die die Pipeline-Caches nicht reproduzieren; das stützt den Ausschluss der Korpus-Neugenerierung (6.4) unabhängig. Vergleichbar mit der Headline ist deshalb nur die Streuung innerhalb des Piloten.  
- Der Qualitäts-Proxy auf Basis der Dictionary Hit Rate generalisiert statistisch nicht (LOOCV-R² unter null) und wird deshalb ausschließlich als Plausibilitätsschranke geführt.[^21]  
- Der Round-Trip vom Viewer-Edit zurück in die Pipeline ist implementiert (Direktschreiben in den Arbeitsbaum, doppelte Ablage, Re-Lauf per Kommando), der Re-Lauf selbst bleibt ein manueller Schritt; der GitHub-Actions-Ausblick aus Abschnitt 5 würde ihn schließen.

# Anhang A: Skripte der Pipeline

Aufruf als Modul (`python -m scripts.<paket>.<modul>`); Inventar gepflegt in `scripts/README.md`.

## **Geteilte Basis**

- `config.py`: Pfade, Modellnamen, Konstanten.  
- `utils.py`: dateiübergreifende Hilfsfunktionen.  
- `core/loaders.py`: OCR-Datenstrom-Vorrang, Layout-Fund, Seitenauswahl (Text \+ Layout).

## **Vom Scan zum Seitenbild**

- `edition/extract_pages.py`: zerlegt PDFs seitenweise in PNG.

## **Texterkennung**

- `ocr/ocr_pipeline.py`: steuert die OCR (Mistral Basis, Gemini Opt-in).  
- `ocr/gemini_ocr_correct.py`: Ersatz- und Korrektur-OCR mit Gemini (zwei Varianten).  
- `ocr/llm_postprocess.py`: optionale OCR-Nachkorrektur (nicht standardmäßig aktiv).  
- `ocr/classify_docs.py`: Dokument-Metadaten (Sprache, Typ, Titel, Autor, Datum).

## **Layoutanalyse**

- `layout/run_layout_analysis.py`: Docling lokal, ein Layout-JSON je Seite.  
- `layout/run_layout_cloud.py`: dieselbe Analyse über docling-serve.  
- `layout/layout_qa_gemini.py`: Layout-QA, Neuerkennung und Auto-Modus mit Gemini.  
- `layout/generate_layout_overlays.py`: Regionen-Overlays zur Kontrolle (optional Docling gegen Gemini).

## **Austauschformate**

- `layout/page_xml_generator.py`: PAGE-XML (Schema 2013-07-15).  
- `layout/mets_generator.py`: METS-Manifest (vom PAGE-XML-Generator aufgerufen).  
- `edition/transkribus_export.py`, `edition/transkribus_upload.py`: PAGE-XML-Bündel und REST-Upload (Transkribus-Round-Trip).

## **TEI-Erzeugung**

- `tei/tei_unified.py`: orchestriert die drei TEI-Stufen samt Validierung.  
- `tei/tei_step1.py`: deterministisches Grundgerüst (kanonische Lesereihenfolge, Druckfolio-Erkennung, Filter-Echo-Ausschluss).  
- `tei/tei_step2.py`: multimodale Gemini-Verfeinerung plus Fehlerbereinigung.  
- `tei/tei_step3.py`: Seitenzusammenführung plus dokumentweite Konformitätskorrekturen.  
- `tei/tei_generator.py`, `tei/tei_mapping_prompt.py`, `tei/tei_xml_utils.py`: geteilte Bausteine (Markdown-zu-TEI, Mapping-Tabelle, XML-Hilfen samt Permutation).  
- `tei/pb_split.py`: byte-identische Segmentierung an Seitenumbrüchen (Basis für Mirror und Audits).

## **Validierung und Audits**

- `tei/tei_validator.py`: RelaxNG-Schema, Projektregeln, Warnungen, ZBZ-Konformität.  
- `tei/zbz_conformity.py`: Inline-GND-Konformitätsregeln (E88), die RelaxNG nicht ausdrückt.  
- `eval/benchmark_cer.py`, `eval/cer_statistics_full.py`, `eval/evaluate_ocr.py`: CER-Messstrecke auf gemeinsamen Funktionen.  
- `eval/cer_statistics.py`, `eval/cer_statistics_runner.py`: Statistik-Bibliothek (BCa, paired Bootstrap, HCPR) und deren Dateneinleser.  
- `eval/quality_proxy.py`: Dictionary-Hit-Rate als Plausibilitätsschranke.  
- `eval/eval_report.py`: HTML-Report der OCR-Auswertung.  
- `eval/completeness_check.py`: Seitenvollständigkeit (verrechnet Doppelseiten und Deckblätter).  
- `eval/corpus_audit.py`: Korpus-Kennzahlen aus den Primärquellen, Drift-Flag.  
- `eval/structure_audit.py`: struktureller Abgleich Pipeline-TEI gegen die 25 Referenzen.  
- `eval/reading_order_audit.py`: Lesereihenfolge-Triage robust gegen fragil.  
- `eval/char_lint_audit.py`, `eval/pb_number_audit.py`, `eval/hi_preservation_audit.py`, `eval/relation_integrity_audit.py`, `eval/body_note_audit.py`: Richtlinienkonformität (Zeichen, Paginierung, Kursivsignal, Relationen, Fußnoten).  
- `eval/stability_pilot.py`: Run-zu-Run-Streuung der LLM-Stufe (E100).  
- `eval/audit_common.py`: geteilte TEI-Erkennung und Report-Gerüst der Audits.

## **Bestandskorrekturen (reversibel, mit Backup)**

- `tei/tei_blank_marker.py`: Leerseiten als `<pb type="blank"/>`.  
- `tei/tei_status_marker.py`: Bearbeitungs-History als `<change>` in die Versionsbeschreibung.  
- `tei/tei_add_revision.py`: älterer Screening-Status-Injektor, abgelöst durch `tei_status_marker` (E66), nicht mehr aktiv.  
- `tei/tei_surface_graphic.py`: Faksimile-zu-Bild-Verknüpfung.  
- `tei/tei_footnote_demote.py`: referenzverifizierte Fußnoten zurück in den Fließtext.  
- `tei/tei_footnote_marker_strip.py`: entfernt redundante Fußnoten-Marker aus dem Notentext (E85).  
- `tei/tei_char_normalize.py`: Apostroph-Normalisierung.  
- `tei/tei_pb_folio.py`: `pb@n` auf geklammerte Druckfolio, entfernt Seitenzahl-Echos.  
- `tei/tei_body_note_demote.py`: setzt die faksimile-verifizierten Fußnoten-Urteile um.  
- `tei/tei_reading_order_fix.py`: Dry-Run-Instrument der W19-Worklist (Korpus-Reorder widerlegt, E99).  
- `tei/tei_reassemble_preview.py`: reversible Vorschau des Reorder-Bestands ohne Eingriff ins finale TEI.  
- `tei/marker_common.py`: geteiltes Trockenlauf- und Backup-Gerüst der Marker-Läufe.

## **Bearbeitungsstatus und Viewer-Daten**

- `edition/page_manifest.py`: Manifest je Objekt (Workflow-Status, History, sichere Leerseiten).  
- `edition/generate_edition_data.py`: Katalog und Per-Seiten-Mirror des Webinterface.

# Anhang B: Prompts der LLM-Stufen

Wörtlicher Stand: Commit `eca68d1a`, 09.07.2026; verbindliche Quelle ist die genannte Codestelle. B.1 hat den ausgelieferten Bestand geformt, B.2 ist abschaltbar vorgehalten und war nicht aktiv (produktive OCR über Mistral). Mit "(Auszug)" markierte Blöcke sind gekürzt.

## **B.1 Produktive Prompts**

### **Dokumentklassifikation (`ocr/classify_docs.py`, Gemini)**

Analyze this scanned document. These are the first pages of a document from the Jeanne Hersch archive (Zentralbibliothek Zuerich). Most documents are in French or German.

Extract the following metadata based ONLY on what is clearly visible:

\- language: ISO 639-3 code(s) (fra, deu, fra/deu, eng, ita, ...)

\- pub\_form: book, bookSection, journalArticle, encyclopedia, brochure, interview, anthology, other

\- layout\_type: A (single-column), B (two-column), C (monograph), D (special: photos, mixed, historical prints)

\- title / author / date: if clearly visible, else null (Jeanne Hersch may be author or subject)

\- description: one sentence

\- has\_jstor\_cover: true if first page is a JSTOR cover

\- num\_columns: 1 or 2

Report only what you can clearly determine. Use null for uncertain fields.

### **Layout-QA (`layout/layout_qa_gemini.py`, Gemini, Overlay-Bild \+ JSON) (Auszug)**

You review layout regions on scanned pages (Jeanne Hersch Edition, ZBZ Zurich, academic French/German texts).

INPUT: Overlay image with colored bounding boxes \+ JSON with regions.

LABEL MAPPING (enforce strictly):

  section\_header \-\> zb\_heading | text \-\> zb\_paragraph | footnote \-\> footnote

  caption \-\> caption | page\_header/page\_footer \-\> \_filter | picture \-\> \_skip

TASK 1 \- FIX WRONG LABELS: page numbers/running headers \-\> \_filter; headings/titles/bibl \-\> section\_header; bottom notes \-\> footnote; artifacts \-\> \_filter.

TASK 2 \- ADD MISSING REGIONS: bbox as page % (0-100); page\_header y 0-5, page\_footer y 88-100. CRITICAL for multi-column: check the rightmost 30% for uncovered text.

PICTURE DETECTION: photos/illustrations/logos/charts \-\> picture; framed empty areas \-\> \_filter; text in a frame stays text.

OUTPUT: return ALL regions; keep existing text and bbox exactly; change only label/zbz\_tag; score 0-100 (deduct 10 per wrong/missing label).

### **Layout-Neuerkennung (`layout/layout_qa_gemini.py`, Detect-Modus, Gemini, Scan-Bild) (Auszug)**

You are a document layout analysis expert for scanned pages from the Jeanne Hersch Edition (ZBZ Zurich, 20th century academic texts, primarily French/German).

Detect ALL text and structural regions; for each a bounding box and a label.

Labels: section\_header, text, footnote, caption, page\_header, page\_footer, picture, table, list\_item.

RULES: detect every region incl. small ones; tight boxes; multi-column \-\> each column separately; double-page/landscape \-\> scan the FULL width, the rightmost page is frequently missed (check x \> 60%); reading order top-to-bottom, left-to-right; do not merge or drop paragraphs; separate headings from body.

### **TEI-Verfeinerung (`tei/tei_step2.py` mit `tei/tei_mapping_prompt.py`, Gemini, Seitenbild \+ Gerüst \+ OCR) (Auszug)**

You are a TEI-XML refiner for the Jeanne Hersch Edition (ZBZ Zurich). Follow the project TEI schema (TEI P5 subset) and the ZBZ editorial guidelines.

You receive a RULE-BASED TEI scaffold; compare it against the scanned image and the OCR text and enrich it.

TASK: apply the mapping table. PRESERVE all text exactly; do NOT invent text; only modify XML markup; output well-formed XML.

REFINEMENT PRIORITIES: (1) verify \<lb/\> positions against the image; (2) break="no" for cross-line hyphenation (remove hyphen); (3) \<foreign xml:lang\> for language switches; (4) verify \<hi\> italic/bold; (5) correct div hierarchy/types; (6) \<choice\>\<sic\>/\<corr\> for non-obvious errors; (7) interviews: every turn in \<sp\>\<speaker\>; (8) reviews: bibliographic heading in \<bibl\>.

OUTPUT: only the refined TEI body fragment, no declaration/root/header, start with \<div ...\>, end with \</div\>.

Kern des Prompts ist die vollständige Mapping-Tabelle (7 Sektionen: Dokumentstruktur, Zeilen, Inline-Formatierung, Sprachwechsel, Korrekturen, Redebeiträge, Auslassungen) plus zehn genrespezifische Regelblöcke. Vollständiger Wortlaut: MAPPING\_TABLE und GENRE\_RULES in tei/tei\_mapping\_prompt.py.

## **B.2 Optionale Prompts (nicht im ausgelieferten Pfad aktiv)**

### **Gemini-Vision-OCR (`ocr/ocr_pipeline.py`, Ersatz-Engine)**

Transkribiere den Text dieser Buchseite vollstaendig und originalgetreu als Markdown.

\- Gib NUR den transkribierten Text aus, keine Kommentare, keine Code-Fences.  
\- Bewahre Originalsprache und \-orthographie, uebersetze nichts.  
\- Erhalte Absatzstruktur, Ueberschriften (Markdown-Headings), Fussnoten, Hervorhebungen.  
\- Unleserliche Stellen mit \[...\] markieren, nichts erfinden.  
\- Kein Text auf der Seite \-\> leere Antwort.

### **OCR-Korrektur (`ocr/gemini_ocr_correct.py`, Gemini, zwei Stufen) (Auszug)**

Stufe 1 (Analyse): "You are an OCR error detection specialist ..." Flagge nur echte OCR-Fehler (Zeichen, fehlende Akzente, rn-\>m, cl-\>d) und Plattform-Artefakte (JSTOR, e-periodica) als ocr\_artifact. 'original' muss exaktes Substring sein; max. 50 Korrekturen je Seite; keine gültigen Schreibvarianten flaggen. Variante B verifiziert jede Korrektur zusätzlich gegen das Scan-Bild. Vier Few-Shot-Beispiele im Code.

Stufe 2 (Anwendung): "You are a precise text editor. Apply ONLY the listed corrections ..." Nur high/medium anwenden, low überspringen; ocr\_artifact löschen; sonst zeichenidentisch; Markdown und Absätze erhalten; nur den korrigierten Text ausgeben.

Vollständiger Wortlaut: build\_analysis\_prompt und build\_correction\_prompt in ocr/gemini\_ocr\_correct.py.

### **OCR-Nachkorrektur (`ocr/llm_postprocess.py`, Anthropic, drei Erprobungsvarianten)**

Experiment mit drei System-Prompt-Varianten (A Baseline mit Analyse- und Korrekturblock, B schlank nur korrigierter Text, C Few-Shot mit echten Mistral-Fehlerbeispielen). Nicht standardmäßig aktiv. Wortlaut: \_prompt\_variant\_a/b/c in ocr/llm\_postprocess.py.  


[^1]:  Zentralbibliothek Zürich. „Jeanne Hersch: Digitale Neuauflage der Schriften". [https://www.zb.uzh.ch/de/jeanne-hersch-digitale-neuauflage-der-schriften](https://www.zb.uzh.ch/de/jeanne-hersch-digitale-neuauflage-der-schriften).

[^2]:  Ein AI Harness ist die Software-Schicht um ein Sprachmodell, die dessen Textausgaben über eine Schleife aus Modellaufruf, Aktion und Beobachtung in Werkzeugnutzung übersetzt und dabei Kontext, Prompts, State und Kontrollfluss verwaltet, sodass aus einem Textgenerator ein in einer Umgebung handlungsfähiger Agent wird.

[^3]:  [https://dhcraft.org/Promptotyping](https://dhcraft.org/Promptotyping/) und ein Videotutorial zu Promptotyping gibt es hier: [https://youtu.be/8sUe4Jkh3uQ](https://youtu.be/8sUe4Jkh3uQ).

[^4]: Pollin, Christopher. „Promptotyping: Zwischen Vibe Coding, Vibe Research und Context Engineering". L.I.S.A. Wissenschaftsportal Gerda Henkel Stiftung, 17\. Januar 2026\. [https://lisa.gerda-henkel-stiftung.de/digitale\_geschichte\_pollin](https://lisa.gerda-henkel-stiftung.de/digitale_geschichte_pollin).

[^5]:  Claude Code, Dokumentation. [https://code.claude.com/docs/en/overview](https://code.claude.com/docs/en/overview).

[^6]:  Repository: [https://github.com/chpollin/zbz-ocr-tei](https://github.com/chpollin/zbz-ocr-tei).

[^7]: Mistral AI. „Document AI" (OCR- und Dokumentverarbeitungs-API). [https://mistral.ai/news/mistral-ocr](https://mistral.ai/news/mistral-ocr).

[^8]: Livathinos, Nikolaos, Christoph Auer, Maksym Lysak u. a. „Docling: An Efficient Open-Source Toolkit for AI-driven Document Conversion". IBM Research, arXiv:2501.17887, 2025\. [https://arxiv.org/abs/2501.17887](https://arxiv.org/abs/2501.17887). Software: [https://github.com/docling-project/docling](https://github.com/docling-project/docling).

[^9]: PAGE (Page Analysis and Ground-truth Elements), Schemaversion 2013-07-15, Namespace `http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15`. Spezifikation: Pletschacher, Stefan und Apostolos Antonacopoulos. „The PAGE (Page Analysis and Ground-Truth Elements) Format Framework". In: Proceedings of the 20th International Conference on Pattern Recognition (ICPR), 2010, S. 257–260. PRImA Research Lab: [https://www.primaresearch.org/tools/PAGELibraries](https://www.primaresearch.org/tools/PAGELibraries).

[^10]: Metadata Encoding and Transmission Standard (METS). Library of Congress, Network Development and MARC Standards Office. [https://www.loc.gov/standards/mets/](https://www.loc.gov/standards/mets/).

[^11]: OpenSeadragon, quelloffener Bildbetrachter für hochauflösende Zoombilder, Version 5.0.1. [https://openseadragon.github.io/](https://openseadragon.github.io/).

[^12]: Transkribus. „Character Error Rate (CER) Explained". [https://www.transkribus.org/character-error-rate-cer-explained](https://www.transkribus.org/character-error-rate-cer-explained) (Definition, Berechnung über die Levenshtein-Editierdistanz, Bewertungsschwellen, Layoutkomplexität als CER-Faktor).

[^13]: Transkribus. „Character Error Rate (CER) Explained". [https://www.transkribus.org/character-error-rate-cer-explained](https://www.transkribus.org/character-error-rate-cer-explained) (Definition, Berechnung über die Levenshtein-Editierdistanz, Bewertungsschwellen, Layoutkomplexität als CER-Faktor).

[^14]: Transkribus. „Character Error Rate (CER) Explained". [https://www.transkribus.org/character-error-rate-cer-explained](https://www.transkribus.org/character-error-rate-cer-explained) (Definition, Berechnung über die Levenshtein-Editierdistanz, Bewertungsschwellen, Layoutkomplexität als CER-Faktor).

[^15]: jiwer. [https://github.com/jitsi/jiwer](https://github.com/jitsi/jiwer) (Funktionsschnittstelle zur CER-Berechnung).

[^16]: dinglehopper, OCR-Evaluationswerkzeug der OCR-D-Initiative. [https://github.com/qurator-spk/dinglehopper](https://github.com/qurator-spk/dinglehopper).

[^17]: Levchenko, Maria. 2025\. arXiv:2510.06743 (frequenzbasierte HCPR-Adaption zur Diakritika-Erhaltung).

[^18]: OCR-D. „Quality Assurance in OCR-D". [https://ocr-d.de/en/spec/ocrd\_eval](https://ocr-d.de/en/spec/ocrd_eval) (CER-Definition, Unicode-Normalisierung NFC, Grapheme-Cluster, Letter Accuracy als eigene, noch nicht genutzte Metrik).

[^19]: dinglehopper, OCR-Evaluationswerkzeug der OCR-D-Initiative. [https://github.com/qurator-spk/dinglehopper](https://github.com/qurator-spk/dinglehopper).

[^20]: Du, W. 2025\. „When \+1% Is Not Enough: A Paired Bootstrap Protocol for Evaluating Small Improvements". arXiv:2511.19794.

[^21]: Nach dem Ansatz von Stroebel et al. 2022 (Dictionary-basierte OCR-Qualitätsschätzung); die projektinterne Prüfung ergab ein negatives LOOCV-R² des zusammengesetzten Schätzers.