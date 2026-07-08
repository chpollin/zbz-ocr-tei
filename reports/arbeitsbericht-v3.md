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

* v3, 07.07.2026; v2, 07.07.2026; v1, 27.05.2026
* AI-Unterstützung: Claude Opus 4.7, Opus 4.8, Fable 5, Claude Code

Gegenüber der Erstfassung von v3 sind nachgetragen: die Ergebniszahlen der zwei letzten Bestandskorrektur-Läufe (Seitenzahlen, Fußnoten-Demotion), die finale Warnungsbilanz der Validierung, die adjudizierte und inzwischen behobene Doppelseiten-Reparatur des Dokuments 30, die empirische Widerlegung der maschinellen Lesereihenfolge-Umstellung und die Run-zu-Run-Stabilitätsmessung. Alle im Text genannten Werte sind gemessen.

## 1 Projektkontext und Zielsetzung

Dieser Bericht dokumentiert ein Experiment im Rahmen der digitalen Neuauflage der Schriften von Jeanne Hersch, einem Projekt der Zentralbibliothek Zürich (ZBZ).[^1] Herschs philosophisches Werk ist mehrsprachig, überwiegend französisch und deutsch, und verstreut überliefert. Mehrsprachigkeit und heterogene Drucküberlieferung sind damit die beiden bestimmenden Anforderungen an die Pipeline.

Parallel zum etablierten ZBZ-Workflow wurde dieselbe Strecke ein zweites Mal durchlaufen, diesmal agentenbasiert über Large Language Models (LLMs) und Vision-Language Models (VLMs). Leitfrage ist, ob ein solcher Ansatz den etablierten Workflow in Textqualität und Aufwand erreicht. Die Vergleichsgrundlage stammt aus derselben Parallelführung, denn die manuell über Transkribus erstellten Referenz-TEIs dienen dem Experiment als Ground Truth (siehe 6.1).

Gegenstand ist eine Pipeline, die ausgehend von PDF-Scans TEI-XML im DTA-Basisformat erzeugt und in einem zugehörigen Webinterface anzeigbar und kuratierbar macht. Das DTA-Basisformat ist ein TEI-Subset für die einheitliche Auszeichnung digitalisierter Drucktexte.[^2] Das Vorhaben liefert editionsfertige Daten samt Kurationswerkzeug; die Edition selbst entsteht stromabwärts bei der ZBZ, und der maschinelle Ausgangszustand aller Datenströme heißt darum bewusst unverifiziert. Die Pipeline simuliert die Digitalisierung ausgehend von den PDFs und erzeugt Transkription, Layouterkennung und TEI-XML durchgängig über LLMs und VLMs. Pipeline wie Webinterface entstehen durch Promptotyping,[^3] eine Context-Engineering-Arbeitsweise zur Erzeugung von Forschungsartefakten aus Forschungsdaten und Forschungskontexten.[^4] Die Codeerzeugung erfolgte vollständig innerhalb von Claude Code mit den jeweils aktuellen Opus-Modellen über mehrere Sessions hinweg;[^5] der Erzeugungsprozess ist über die Commit-Historie des offen vorliegenden Repositorys nachvollziehbar.[^6]

## 2 Datengrundlage

Am Beginn der Pipeline stehen zwei von der ZBZ gelieferte Bestandteile, die PDF-Scans der digitalisierten Texte und das Masterfile mit den zugehörigen Metadaten. Diese Lieferung bildet die Ausgangslage; der katalogische Gesamtbestand und seine bibliothekarische Erschließung bleiben außer Betracht.

Das Masterfile ist die Katalog- und Steuerungstabelle der ZBZ und enthält zwei Arten von Information. Die bibliografischen Stammdaten umfassen ID, MMSID, Gattung, Jahr, Titel, Seitenzahl, Signatur und Sprache. Die Workflow-Spalten halten den Bearbeitungsstand im ZB-Prozess fest, etwa digitalisiert, Kontrolle Metadaten, korrigiert und ausgezeichnet.

Der Weg vom Masterfile zum verarbeiteten Korpus ist ein vierstufiger Trichter, den das Audit-Skript `corpus_audit` reproduzierbar aus den Primärquellen ableitet. Von 325 im Masterfile gelisteten Texten sind 289 digitalisiert, davon 286 als PDF geliefert (nicht geliefert: 1745, 1750, 1970) und davon 285 mit finalem TEI versehen (das gelieferte PDF ohne TEI ist Dokument 10, siehe 6.3).

| Stand | Anzahl |
| :---- | :---- |
| gelieferte Dokumente | 286 |
| davon mit finalem TEI | 285 |
| physische Seiten | 4.152 |

Die Verteilungen nach Dokumenttyp und Sprache beziehen sich auf den Lieferstand von 286 Dokumenten. Die gelieferten Dokumente sind durchweg Drucktexte; handschriftliches Material ist nicht systematisch vertreten, sodass es sich um einen reinen OCR-Prozess handelt. Der Bestand erstreckt sich über die Jahre 1931 bis 1998.

| Dokumenttyp | Anzahl | Anteil |
| :---- | :---- | :---- |
| Zeitschriftenartikel | 146 | 51 % |
| Sammelbandbeiträge | 116 | 41 % |
| Monografien | 24 | 8 % |

| Sprache | Anzahl | Anteil |
| :---- | :---- | :---- |
| Französisch | 203 | 71 % |
| Deutsch | 72 | 25 % |
| Englisch | 7 | 2 % |
| Italienisch | 2 | 1 % |
| mehrsprachig fr/de | 1 | < 1 % |
| ohne Angabe | 1 | < 1 % |

## 3 Repository-Architektur

Der Ordner `knowledge/` ist ein Promptotyping-Vault, eine an eine Obsidian-Forschungsvault angelehnte, in Claude Code erzeugte und kuratierte Wissensbasis in Markdown, die das Projektwissen abbildet und über den Projektverlauf iterativ wächst; einzelne Dokumente entstehen, wachsen oder werden zusammengeführt. Leitprinzip ist die Single Source of Truth. Jeder Fakt steht in genau einem Dokument, auf das die übrigen verweisen. Hervorzuheben sind das chronologische Arbeitstagebuch `journal.md` als beschreibende Schicht neben der Git-Historie und das durchnummerierte Entscheidungsregister `decisions.md`, das zum Berichtszeitpunkt 97 datierte Entscheidungen samt verworfenen Alternativen führt.

Der Ordner `data/` enthält Eingangs- und Referenzdaten und trennt Geliefertes von projektseitig Erzeugtem. Unter `data/source/` liegen die von der ZB gelieferten Startdaten, also die PDF-Scans, die manuell über Transkribus erstellten Referenz-TEIs samt zugehörigen PAGE-XML-Exporten, das Masterfile und die Editionsrichtlinien. Daneben stehen projektseitig erstellte Referenzdaten, das projektspezifische TEI-Schema `data/schema/zbz_hersch.rng` und der Ordner `data/curated_tei/`, der für handverifizierte Editions-TEIs reserviert ist und zum Berichtszeitpunkt leer ist, weil die menschliche Verifikation planmäßig bei der ZBZ liegt. Die per LLM erzeugte Dokumentklassifikation liegt in `doc_metadata.json`, damit sie nicht bei jedem Pipeline-Lauf neu berechnet wird.

Der Ordner `output/` enthält alle generierten Datenströme (OCR, Layout, PAGE-XML, TEI) und ist bewusst nicht versioniert. Der Ordner `scripts/` enthält die von Claude Code generierte Python-Pipeline, nach Domäne in Unterpakete gegliedert (`ocr`, `layout`, `tei`, `eval`, `edition`, `core`); die einzelnen Skripte sind in Anhang A aufgeführt. Die Reproduzierbarkeit der Evaluation sichern die `pytest`-Suiten unter `tests/`, darunter die in 6.1 genannte Statistik-Library; die Gesamtsuite läuft als CI-Gate bei jedem Push.

Der Ordner `docs/` ist für GitHub Pages konfiguriert und enthält das Frontend, einen Mirror der Pipeline-Daten und die aus den PDFs erzeugten PNGs. Da GitHub Pages ohne Backend nur statische Dateien ausliefert, liegen die Editionsdaten dort als generierter Per-Seiten-Mirror unter `docs/data/pages/{doc}/`, der den Großteil der versionierten Dateien ausmacht. Ein Skript zerlegt das finale TEI seitenweise und legt je Seite eine Datei für TEI, OCR-Text und Layout ab. Der Mirror deckt alle 285 Dokumente ab; nur die Faksimile-Bilder bleiben außerhalb einiger Demonstrationsdokumente lokal. Verbindliche Quelle ist das TEI unter `output/tei_final/{doc}_final.xml`, aus dem der Mirror nach jeder Änderung neu erzeugt wird, etwa nach einem erneuten Pipeline-Lauf oder einer im Viewer kuratierten und zurückgespielten Bearbeitung. Ein Edit am Mirror ginge beim nächsten Lauf verloren. Diese Trennung von verbindlicher Editionsablage und Anzeige-Spiegel gilt für alle folgenden Abschnitte.

## 4 Die Pipeline

Die Pipeline überführt PDF-Scans in TEI-XML. Je Dokument entstehen drei Datenströme, ein OCR-Datenstrom mit dem erkannten Text, ein Layout-Datenstrom mit der Seitenstruktur und als edierte Fassung der daraus abgeleitete TEI-Datenstrom, ein DTA-konformes, die Textstrukturen (Überschriften, Absätze, Seiten- und Zeilenumbrüche) abbildendes TEI-XML. Die Verarbeitung ist durchgängig defensiv ausgelegt, sodass eine fehlschlagende Einzelkorrektur die Eingabe unverändert weiterreicht, statt den Lauf abzubrechen.

### Vom Scan zum Seitenbild

Zu Beginn werden die PDF-Scans seitenweise in Einzelbilder zerlegt, auf denen die nachfolgenden Stufen aufsetzen.

### Texterkennung

Produktiv erfolgt die Texterkennung mit Mistral Document AI[^7] über Azure AI Foundry. Das Modell erfasst neben Fließtext auch Tabellen und Listen und liefert seitenweises Markdown; große Dokumente werden automatisch aufgeteilt, eine von Claude Code eigenständig getroffene Entscheidung. Steht dieser Zugang nicht zur Verfügung, kann ersatzweise ein multimodales Gemini-Modell dieselbe Aufgabe übernehmen, ohne dass sich für die Folgestufen etwas ändert. Eine optionale, sprachmodellgestützte Nachkorrektur ist verfügbar, aber nicht standardmäßig aktiv, weil sie bei bereits guter Ausgangsqualität keinen Mehrwert bringt; wo eine korrigierte Fassung vorliegt, wird sie der Rohfassung vorgezogen.

### Layoutanalyse

Die Strukturerkennung verbindet Docling[^8] mit einem nachgeschalteten Gemini-Schritt. Docling liefert die Basisstruktur (Regionen mit Position), Gemini prüft die Labels und ergänzt fehlende Regionen. Im automatischen Modus bewertet ein Maß für die Flächenabdeckung jede Seite. Ist die Abdeckung zu gering, erkennt Gemini das Layout direkt vom Scan komplett neu und ersetzt das Docling-Ergebnis, statt es nur zu korrigieren. Docling-Fassung und Gemini-Fassung bleiben als zwei getrennte Dateien erhalten, sodass nachvollziehbar bleibt, welche Erkennung von welcher Engine stammt.

### Austauschformate

Aus dem Layout- und dem OCR-Datenstrom werden zusätzlich PAGE-XML[^9] und ein METS-Manifest[^10] erzeugt, Austauschformate für externe Bearbeitungs- und Archivsysteme. Sie entstehen aus denselben Quellen wie das TEI, ohne dessen Vorstufe zu sein, denn das TEI wird unmittelbar aus Layout und Text gebildet.

### TEI-Erzeugung

Die TEI-Erzeugung verbindet regelbasierte und sprachmodellgestützte Arbeit in drei Stufen, denen nachgelagerte deterministische Korrekturschritte folgen.

Die erste Stufe baut aus dem OCR- und dem Layout-Datenstrom ein deterministisches Grundgerüst. Textabschnitte werden den Layoutregionen zugeordnet, in Überschriften, Absätze, Fußnoten und vergleichbare Strukturen übersetzt und mit Seiten- und Zeilenmarken versehen. Die Blockreihenfolge folgt dabei einer spalten- und bandbewussten kanonischen Lesereihenfolge, die Doppelseiten und Mehrspalter korrekt serialisiert; die frühere reine Sortierung nach vertikaler Position hatte auf zweispaltigen Layouts die Spalten verschränkt. Gedruckte Seitenzahlen werden aus den Fußzeilen-Regionen der Layoutanalyse gelesen und in das Attribut `pb@n` übernommen; wo keine Fußzeile erkennbar ist, füllt eine dokumentweite Interpolation aus konsistenten Nachbarseiten die Lücke, und erschlossene Zahlen stehen wie in den ZBZ-Referenzen in eckigen Klammern. Text aus gefilterten Randregionen, etwa die Seitenzahl selbst oder Bibliotheks-Deckblattzeilen, bleibt aus dem Fließtext ausgeschlossen.

Die zweite Stufe legt das Seitenbild zusammen mit dem Gerüst und dem erkannten Text einem multimodalen Modell vor und erzeugt eine strukturell angereicherte Fassung. Da modellgenerierte Auszeichnung systematische Eigenheiten aufweist, schließt sich eine korrigierende Nachbearbeitung an, die häufige Struktur- und Schemaverstöße automatisch bereinigt. Schlägt die Verfeinerung fehl, wird das deterministische Gerüst unverändert weitergereicht.

Die dritte Stufe verbindet die Einzelseiten zu einem Gesamtdokument, zieht seitenweise entstandene Gliederungseinheiten zusammen und wendet einen zweiten Satz dokumentweiter Konformitätskorrekturen an, darunter die Vereinheitlichung der Gliederungstypen, die Vergabe von Bild-Identifikatoren und die Normalisierung fremdsprachiger Auszeichnung.

Auf das ausgelieferte Korpus wirken schließlich nachgelagerte deterministische Marker-Schritte, die jeweils mit Backup arbeiten, idempotent sind und über ein Audit vorher und nachher vermessen werden. Zu ihnen gehören die Leerseiten-Markierung, die Projektion des Bearbeitungsstatus in die Versionsbeschreibung, die Verknüpfung jeder Faksimile-Seite mit ihrer Bilddatei sowie die in 6.4 beschriebenen Bestandskorrekturen.

### Validierung

Das erzeugte TEI wird mehrstufig geprüft. Die erste Stufe validiert gegen das projektspezifische RelaxNG-Schema `zbz_hersch.rng`, das auf dem DTA-Basisformat aufbaut und um die verbindlichen ZBZ-Editionsrichtlinien ergänzt ist. Die zweite Stufe setzt projekteigene Regeln blockierend durch (R1 bis R7), etwa den Dokumenttyp, die Präsenz von Header und Body und gültige Gliederungstypen. Informative Hinweise (W1 bis W19) markieren prüfenswerte Stellen wie leere Sprecher-Slots oder Abweichungen von der kanonischen Lesereihenfolge, ohne die Gültigkeit zu blockieren. Eine dritte Ebene prüft die ZBZ-Konformitätsregeln, die ein RelaxNG nicht ausdrücken kann, etwa das Rendering-Vokabular und die Form der Seitenumbrüche; die Entitätsregeln dieser Ebene werden erst auf kuratiertem, inline-GND-annotiertem Output scharf, weil das gelieferte Korpus bewusst entitätsfrei ist. Die quantitativen Ergebnisse stehen in 6.1.

### Bearbeitungsstatus

Die drei Datenströme sind nach der maschinellen Erzeugung zunächst nicht verifiziert, also vorhanden, aber fachlich noch nicht geprüft. Den Prüfstand hält ein menschgesetzter Bearbeitungsstatus fest, getrennt für jeden der drei Ströme. Jeder Strom nimmt einen von drei Werten an, unverifiziert, in Arbeit oder verifiziert, die im Webinterface als dreistufige Ampel erscheinen (neutral, gelb, grün) und per Klick weitergeschaltet werden. Jeder Wechsel wird in einer dokumentbezogenen Begleitdatei festgehalten, dem Manifest, einer JSON-Datei je Dokument, und zwar als fortlaufende Liste der einzelnen Schritte mit Zeitpunkt, Bearbeiterkürzel sowie Vor- und Folgestatus, sodass eine vollständige Bearbeitungsspur entsteht. Bei der Übergabe an die ZB werden diese Einträge deterministisch und idempotent in die TEI-Versionsbeschreibung (`<revisionDesc>`) des Dokuments projiziert, sodass die Bearbeitungsgeschichte mit dem ausgelieferten Dokument selbst reist.

## 5 Webinterface und Kuration

Das Webinterface ist ein im Browser laufendes, auf GitHub Pages gehostetes Werkzeug zur Überprüfung und Kuration der Pipeline-Ergebnisse ([https://chpollin.github.io/zbz-ocr-tei/](https://chpollin.github.io/zbz-ocr-tei/)). Den Kern bildet der Pipeline-Viewer (`docs/viewer.html`), eine Single-Page-App ohne Backend und ohne Build-Schritt, die ihre Inhalte aus dem in der Repository-Architektur beschriebenen Per-Seiten-Mirror lädt, einer pro Dokument und Seite vorab erzeugten Datenablage (aufbereiteter OCR-Text, Layout-Regionen und das aus dem finalen TEI herausgelöste Seiten-TEI), die das gesamte Korpus ohne Server bereitstellt. Der Viewer bildet eine Bild-Text-Synopse. Faksimile und zugehöriger Text stehen nebeneinander, sodass beide Seite für Seite verglichen werden können. Das Faksimile wird im Ansichtsmodus über OpenSeadragon dargestellt[^11] und erlaubt stufenloses Zoomen, Verschieben und Drehen, mit den erkannten Layout-Regionen als Overlay. Der Textbereich ist zwischen drei Quellen umschaltbar, dem aufbereiteten OCR-Rohtext, der gerenderten TEI-Fassung, also dem aus dem TEI-XML erzeugten formatierten Lesetext, und dem TEI-XML-Quelltext selbst. Leerseiten erkennt der Viewer vorab, bevorzugt am TEI-Marker `<pb type="blank"/>`, ersatzweise über eine Textregel auf dem OCR-Ergebnis, und kennzeichnet sie als solche, statt fehlerhafte Regionen oder OCR-Artefakte anzuzeigen.

Daneben stehen weitere, direkt aufrufbare Seiten:

- [Korpus-Übersicht](https://chpollin.github.io/zbz-ocr-tei/) mit sortierbarer Tabelle, Workflow-Ampeln und Filtern über Strom und Status
- [Methode](https://chpollin.github.io/zbz-ocr-tei/methode.html) als statische Seite mit Headline-CER, stratifizierten Werten, Literaturvergleich und Limitations
- [About](https://chpollin.github.io/zbz-ocr-tei/about.html)
- [Impressum](https://chpollin.github.io/zbz-ocr-tei/impressum.html)

Die Kuration ist in den Viewer integriert und kommt ohne separaten Server aus. Layout und Text tragen je einen eigenen, unabhängigen Bearbeitungsschalter. Beim Wechsel in den Layout-Editor löst die Faksimile-Anzeige OpenSeadragon durch eine einfache, bearbeitbare Overlay-Ebene ab; darin lassen sich Regionen-Boxen auswählen, verschieben, skalieren, neu aufziehen und löschen, ihr Typ ändern und ihre Lesereihenfolge per Ziehen ordnen. Die Boxen werden als bildrelative Prozentkoordinaten geführt (0 bis 100, bezogen auf die in der Layout-Analyse festgehaltenen Seitendimensionen), sodass sie zoom- und auflösungsunabhängig deckungsgleich auf Faksimile und Overlay liegen; der Editor korrigiert die von der maschinellen Layout-Analyse vorgeschlagenen Boxen und setzt ihre fachliche Richtigkeit gerade nicht voraus. Der Transkriptions-Editor schaltet die jeweils angezeigte Textquelle auf direkt editierbar, wobei strukturelle Eingriffe dem XML-Modus vorbehalten sind, da die gerenderte Ansicht beim Editieren nur den Text und nicht die Auszeichnung zurückgibt.

Ein einziger Speichern-Button persistiert alle ungesicherten Ströme auf einmal (Layout, Text/TEI, Manifest). In Chromium-Browsern schreibt der Viewer über die File System Access API direkt in den lokalen Arbeitsbaum des Repositorys; wo diese Schnittstelle fehlt, fällt er auf den Datei-Download zurück. Jede Speicherung legt die Nutzlast doppelt ab, kanonisch nach `output/`, wo die Pipeline sie tatsächlich konsumiert, und in den Mirror `docs/data/`, sodass der server-lose Viewer den gespeicherten Stand nach einem Neuladen anzeigt. In einem konkreten Durchlauf korrigiert eine Kuratorin im Layout-Editor von Dokument 570 die Regionen einer Seite und speichert; der Viewer schreibt das Layout-JSON nach `output/layout/570/` und in den Mirror; der Aufruf `python -m scripts.tei.tei_unified --doc 570 --reassemble` baut anschließend das finale TEI aus dem korrigierten Layout neu, wobei kuratierte Seiten je einen Modell-Aufruf kosten und unveränderte Seiten aus dem Cache kommen. Dieser bewusst server-lose Schnitt vermeidet Backend-Betrieb und Mehrnutzer-Konflikte; der Re-Lauf bleibt ein manueller Schritt. (Ausblick: Dieser Schritt ließe sich über die GitHub-Plattform schließen, etwa indem ein Commit der gespeicherten Datei einen GitHub-Actions-Lauf auslöst, der `--reassemble` ausführt und das regenerierte TEI samt Mirror zurückschreibt.)

Der Bearbeitungsstatus je Strom (siehe Abschnitt 4) wird im Viewer per Klick auf die Status-Ampel weitergeschaltet und spiegelt sich in der Korpus-Übersicht; das erste Aktivieren eines Bearbeitungsschalters setzt den betroffenen Strom automatisch von unverifiziert auf in Arbeit, und solange Änderungen nicht gespeichert sind, warnt das Interface beim Verlassen der Seite. Der leitende Gedanke ist, dass die Edition selbst zum Kurationswerkzeug wird. Die Editorinnen und Editoren arbeiten direkt in der Edition und bessern die Fehler der Pipeline aus; die Vertrautheit mit den Texten wächst dabei mit.

Ergänzend wurden 79 sichere Leerseiten in 15 Dokumenten erkannt und als `<pb type="blank"/>` in die finalen TEI projiziert. Als sicher gilt eine Seite nur, wenn zwei unabhängige Signale übereinstimmen. Der OCR-Text ist praktisch leer (höchstens fünf Zeichen, kein alphanumerisches Zeichen oder lediglich ein Blank-Page-Marker) und die Docling-Layout-Analyse findet null Regionen. Nur bei Übereinstimmung wird der Marker gesetzt; widersprechen sich die Signale, wird die Seite zum manuellen Review markiert statt projiziert (im aktuellen Korpus trat kein solcher Konflikt auf). Für den Export stehen Per-Strom-Einzeldownloads in einem Export-Menü bereit; ein ZIP-Bündelexport auf JSZip-Basis ist entworfen und noch nicht eingebunden.

## 6 Qualität und methodologische Einordnung

Die Qualität der Pipeline wird auf zwei Wegen geprüft. Die Zeichenfehlerrate (Character Error Rate, CER) misst die Texttreue gegen die manuell erstellten Referenz-TEIs; sie trägt die Abschnitte 6.1 bis 6.3. Da die Referenzen nur 25 der 285 Dokumente abdecken und die CER weder Richtlinienkonformität noch Strukturqualität erfasst, beschreibt Abschnitt 6.4 die Qualitätssicherung jenseits der CER, eine dreistufige Architektur aus deterministischer Validierung, agentischer Verifikation am Faksimile und menschlicher Adjudikation.

### 6.1 Vergleichsmethodik gegen die Referenz-TEIs

#### Was die CER misst und wie sie hier definiert ist

Die CER ist der Anteil der Zeichen im Referenztext, die im erzeugten Text abweichen. Sie ist definiert als die Levenshtein-Distanz zwischen Referenz und Hypothese, geteilt durch die Zeichenzahl der Referenz.

Die Levenshtein-Distanz ist die minimale Anzahl an Einzelzeichen-Operationen (Einfügung, Löschung, Ersetzung), um die Hypothese in die Referenz zu überführen.[^12] Diese Operationen ergeben sich aus der Distanzberechnung selbst. Die Überführungsrichtung (Hypothese zu Referenz) ist im gesamten Kapitel einheitlich, sodass die Benennung der Operationstypen über alle Beispiele konsistent bleibt; die Distanz selbst ist richtungsunabhängig. Implementiert ist sie über `rapidfuzz.distance.Levenshtein`.

Aggregationseinheit ist das Dokument. Das Korpus-Bootstrap-Verfahren (n = 25 Referenz-TEIs, B = 10 000, Seed 42, Bootstrap auf Dokumentebene) liefert daraus Mittelwert und 95-%-Vertrauensbereich. Zur Einordnung der Werte dient die Transkribus-Konvention, nach der unter 2 % als publikationsreif, 2 bis 5 % als forschungstauglich und 5 bis 10 % als brauchbar für Volltextsuche gilt.[^12] Eine hohe CER bedeutet dabei nicht zwingend schlechte Texterkennung; sie kann ebenso aus fehlerhafter Lesereihenfolge bei komplexem Layout folgen[^12] oder daraus, dass Mistral Document AI ein generelles, nicht auf historische Schrift spezialisiertes Modell ist. Die Berechnung selbst ist ein einzelner Funktionsaufruf;[^13] die methodische Substanz liegt in der Aufbereitung der beiden Texte und in der Wahl der Referenz.

#### Gegen welche Referenz gemessen wird

Die CER misst die Abweichung von einer gewählten Referenz und trifft damit keine Aussage über objektive Korrektheit. Bei TEI-Ground-Truth ist deshalb vorab festzulegen, welche Lesart die Referenz bildet, denn TEI hält an mehreren Stellen zwei konkurrierende Fassungen desselben Textes vor. Zwei Elementpaare sind relevant. `<sic>` / `<corr>` kennzeichnet eine überlieferte fehlerhafte Form gegenüber einer editorischen Korrektur. `<abbr>` / `<expan>` kennzeichnet eine Abkürzung gegenüber ihrer Auflösung. Der Unterschied ist, dass `<expan>` Text enthält, der nie physisch auf der Vorlage stand (die Auflösung von „Dr." zu „Doctor"), während `<corr>` eine plausible Lesetextvariante ist, die sich von `<sic>` meist nur um wenige Zeichen unterscheidet.

Das Experiment misst gegen die edierte, kuratierte Zielfassung. Bei `<sic>` / `<corr>` wird die korrigierte Form `<corr>` gewählt (Regel E3). Das Paar `<abbr>` / `<expan>` kommt in den 25 Referenz-TEIs nicht vor, und die Pipeline erzeugt es nicht; die Extraktion führt deshalb keine Sonderregel dafür. Sollte künftige Ground Truth das Paar einführen, wäre die Extraktion um eine `<choice>`-analoge Auflösung zu erweitern, da der generische Rekursionspfad andernfalls beide Fassungen hintereinander extrahieren würde.

Die Wahl der kuratierten Zielfassung hat eine messbare Konsequenz, die Beispiel 5 in 6.2 zeigt. Enthält die Referenz selbst einen Transkriptionsfehler, zählt eine korrektere Erkennung als Differenz. Solche Fälle erhöhen die gemessene CER, sind kein Pipeline-Fehler und begrenzen das mit dieser Methodik Erreichbare; Abschnitt 6.4 katalogisiert die bekannten Fehler der Referenzen systematisch.

#### Zerlegung der Fehler in Fidelity und Scope

Die Editieroperationen werden in zwei Kategorien zerlegt, die unterschiedliche Fehlerursachen trennen. Fidelity erfasst echte Erkennungsfehler und bildet das Maß für die Lesequalität im engeren Sinn; hierunter fallen Substitutionen (gezählt als Länge des größeren Blocks), sämtliche Löschungen und Einfügungen unterhalb der Schwelle. Scope erfasst zusammenhängende Einfügungen ab einer Schwelle von 50 Zeichen (`SCOPE_BLOCK_MIN` in `scripts/eval/evaluate_ocr.py`), die typischerweise aus Textbestandteilen stammen, welche die Pipeline erfasst, die selektiv transkribierte Referenz aber nicht enthält, etwa Mastheads, Autorzeilen oder Editionsmetadaten. Erkennungsfehler sind sie in der Regel nicht. Die Fidelity-CER wertet nur die erste Kategorie, die Volltext-CER schließt den Scope-Anteil als Diagnosegröße ein. Beide Kategorien summieren sich zeichengenau zur Levenshtein-Distanz; ein Regressionstest schreibt diese Summenidentität fest. Da die Fidelity-Werte von der Schwelle abhängen, nennt jede Zitation die Schwelle mit, eine Regel, die aus der unabhängigen Gegenprobe in 6.4 hervorgegangen ist.

#### TEI-Extraktion

Vor dem Vergleich wird aus jedem TEI in `extract_text_for_comparison()` ein Vergleichstext erzeugt. Dieselbe Funktion verarbeitet beide Seiten, das Referenz-TEI wie das aus der Pipeline erzeugte TEI, damit gemessene Differenzen ausschließlich aus dem Textinhalt stammen und nicht aus einer ungleichen Behandlung der Seiten.

| Nr. | Regel | Effekt |
| :---- | :---- | :---- |
| E1 | XML-Parser über `xml.etree.ElementTree`, Namensraum-Präfixe entfernen | `{tei}p` wird zu `p` |
| E2 | nur Inhalt unterhalb von `<body>` | `<teiHeader>`, `<front>`, `<back>` werden ignoriert |
| E3 | `<choice><sic>X</sic><corr>Y</corr></choice>` wird zu `<corr>` | bei Schreibvariante gilt die kuratierte Lesart |
| E4 | `<choice>` ohne `<corr>`, nur `<sic>` wird zu `<sic>` | Fallback |
| E5 | `<note place="foot">…</note>` ausgeschlossen (Default) | separat edierte Fußnoten würden den Fließtext-Vergleich verzerren; via `include_footnotes=True` einschaltbar |
| E6 | `<lb/>` ohne `break="no"` wird zu einem Leerzeichen | Druck-Zeilenumbruch ist eine Wortgrenze |
| E7 | `<lb break="no"/>` wird zu keinem Zeichen | getrenntes Wort wird zusammengezogen (Hu + manismus wird zu Humanismus) |
| E8 | `<pb/>` wird zu zwei Zeilenumbrüchen `\n\n` | Seitengrenze bleibt erkennbar |
| E9 | alle übrigen Elemente (`<hi>`, `<persName>`, `<bibl>`, `<title>`, `<head>`, `<p>`, `<div>` …) rekursiv als Innentext | Markup wird transparent: `<hi>Wort</hi>` wird zu Wort |
| E10 | Attributwerte werden nicht übernommen | Seitenzahlen aus `<pb n="223"/>`, GND-IDs aus `ref`-Attributen erscheinen nicht im Vergleich |
| E11 | XML-Tails werden beim Eltern-Element angehängt | korrekte Reihenfolge bei `<p>Wort1<hi>Wort2</hi>Wort3</p>` |
| E12 | bei XML-Parse-Fehler Regex-Fallback `re.sub(r'<[^>]+>', '', content)` | sichert die Auswertung gegen einzelne nicht wohlgeformte TEIs, damit eine fehlerhafte Datei den Korpuslauf nicht abbricht |

#### Normalisierung

Nach der Extraktion durchläuft der Text `normalize_for_comparison()`, ebenfalls beidseitig identisch. Die Regeln vereinheitlichen typografische Varianten, die keine inhaltlichen Unterschiede sind.

| Nr. | Regel | Mapping |
| :---- | :---- | :---- |
| N1 / N2 | französische Guillemets zu ASCII `"` | « (U+00AB), » (U+00BB) |
| N3 | deutsches unteres Anführungszeichen zu ASCII `"` | „ (U+201E) |
| N4 / N5 | spitze Anführungszeichen zu ASCII `'` | ‹ (U+2039), › (U+203A) |
| N6 / N7 | Backtick, Akut zu ASCII `'` | ` (U+0060), ´ (U+00B4) |
| N8 bis N12 | Hyphen, geschützter Bindestrich, Halbgeviert-, Geviert-, Ziffernstrich zu ASCII `-` | U+2010, U+2011, U+2013, U+2014, U+2012 |
| N13 | weicher Trennstrich entfernen | U+00AD |
| N14 | Leerzeichen vor `; : ? !` entfernen (frz. Typografie) | `re.sub(r' +([;:?!])', r'\1', text)` |
| N15 | mehrfacher Whitespace zu einem Leerzeichen | `re.sub(r'\s+', ' ', text)` |
| N16 bis N19 | englische Anführungszeichen und Apostrophe zu ASCII `"` / `'` | U+201C, U+201D, U+2018, U+2019 |
| N20 | Whitespace am Anfang und Ende entfernen | `strip()` |
| N21 | Unicode-Normalform NFC | `unicodedata.normalize('NFC', text)` |

Bewusst nicht normalisiert werden Groß- und Kleinschreibung, Diakritika, Satzzeichen, die Unterscheidung von ß und ss sowie Zahlen, da diese substantielle und keine typografischen Differenzen sind. Der case-sensitive Default folgt der Werkzeugpraxis von dinglehopper[^14] und jiwer, die Lowercasing als Opt-in führen; eine optionale case-insensitive Sekundärmetrik existiert (`casefold=True`). Die Erhaltung von Akzenten wird über eine eigene Metrik (HCPR) getrennt geprüft.[^15] Die inzwischen erfolgte Apostroph-Normalisierung des ausgelieferten Korpus (6.4) ist für die CER neutral, weil N16 bis N19 beide Apostrophformen auf dasselbe ASCII-Zeichen abbilden.

#### Verifikation der Messmethodik

Diese Verifikation betrifft die Korrektheit der CER-Messung und ist von der in Abschnitt 4 beschriebenen TEI-Schemavalidierung zu unterscheiden. Sie ruht auf vier Schichten. Erstens 18 handgerechnete Regressionstests (`tests/test_cer_extraction.py`), die unabhängig vom Korpus-Ergebnis das Verhalten festschreiben, darunter die kanonische Formel, Case-Sensitivität, das Unterbleiben von Trimming, die `<choice>`-Auflösung, die Normalisierung und die Zerlegung in Fidelity und Scope samt zeichengenauer Summenkontrolle. Zweitens die Vereinheitlichung der zuvor drei separaten CER-Implementierungen (`benchmark_cer`, `cer_statistics_full`, `tei_validator --compare-ref`) auf gemeinsame kanonische Funktionen, sodass alle drei Pfade für dasselbe Dokument dieselbe Zahl liefern. Drittens der Abgleich der Konventionen mit externen Standards: Nenner als Distanz durch Referenzlänge (Transkribus), NFC-Normalisierung als Grapheme-Cluster-Definition (OCR-D),[^16] case-sensitiver Default (jiwer und allgemeine Werkzeugpraxis; OCR-D sieht das Ignorieren der Groß- und Kleinschreibung nur in einer eigenen Letter-Accuracy-Metrik vor), Volltextvergleich ohne Alignment-Trimming (dinglehopper)[^14] sowie der paired Bootstrap für Deltas (Du 2025).[^17] Viertens eine unabhängige Gegenprobe, die alle publizierten Werte ohne Repository-Code reproduziert hat (6.4). Die Vergleichbarkeit von CER-Werten zwischen verschiedenen Werkzeugen ist allerdings selbst bei nominell gleicher Metrik begrenzt, unter anderem weil bereits die Umwandlung strukturierter Ground Truth in Vergleichstext bei nicht berücksichtigter Lesereihenfolge zur Fehlerquelle wird; die hier dokumentierten Extraktions- und Normalisierungsregeln sind die projektinterne Festlegung dieser Transformation.

#### Quantitative Schemavalidierung

Alle 285 finalen TEI validieren gegen `zbz_hersch.rng`, mit null blockierenden Verstößen gegen die Projektregeln R1 bis R7. Informativ verblieben vor den Bestandsläufen 255 warnungstragende Dokumente (Stand 07.07.2026), dominiert von zwei bewussten Kurationssignalen, den leeren Sprecher-Slots in Interview-Dokumenten (W17) und den Seiten mit nicht-kanonischer Lesereihenfolge im noch nicht regenerierten Bestand (W19). Beide markieren Arbeitsvorrat und keinen Schemaverstoß. Die Schema- und Header-Prüfungen laufen zusätzlich als `pytest`-Gates bei jedem Push.

Nach den beiden Bestandsläufen (6.4) validieren unverändert alle 285 Dokumente fehlerfrei. Die finale Warnungsbilanz umfasst 2 018 informative Vorkommen in 256 Dokumenten und wird weiterhin von den zwei Kurationssignalen getragen, den leeren Sprecher-Slots der Interview-Dokumente (W17, 830 Vorkommen in 15 Dokumenten) und der Lesereihenfolge-Worklist (W19, 827 Seiten in 214 Dokumenten). Die übrigen Klassen sind kleinere Konformitäts-Worklists zur div- und figure-Konvention (W15 mit 73, W16 mit 144 Vorkommen) sowie Einzelbefunde im ein- bis niedrigen zweistelligen Bereich.

### 6.2 Fünf Beispiele aus unterschiedlichen Dokumenttypen

Jedes Beispiel nennt Doc-ID, Layout-Typ und Sprache, stellt eine Referenzstelle der zugehörigen Pipeline-Stelle gegenüber, identifiziert die Differenzen, verweist auf die anwendbaren Regeln und gibt die lokale CER an.

#### Beispiel 1: Dokument 130 (Typ A, Französisch, Sammelbandbeitrag), Titel im Versalsatz

Referenz (`data/source/reference_tei/130.xml`):

```xml
<head>
  <title type="main">L'école de nos périls</title>
  <title type="sub">Le problème de l'élite ouvrière</title>
</head>
```

Nach Extraktion (E2, E6, E9): `L'école de nos périls Le problème de l'élite ouvrière`

OCR (`output/mistral_results/130_p3.md`): `L'ÉCOLE DE NOS PÉRILS LE PROBLÈME DE L'ÉLITE OUVRIÈRE`

Die kasusbehafteten Buchstaben unterscheiden sich durchgängig in der Groß- und Kleinschreibung und zählen als Substitutionen; Leerzeichen und Apostrophe bleiben gleich. Die Levenshtein-Distanz beträgt exakt 41, die Zählbasis 53 Zeichen einschließlich Leerzeichen und Apostrophen, die lokale CER 41/53 ≈ 77 %. Versalsatz wird nicht normalisiert (siehe 6.1), da er eine Schreibvariante ist. Im Gesamtdokument verdünnt sich der Effekt, denn der Titel umfasst 53 Zeichen, die Zählbasis des Dokuments 24 382 Referenzzeichen; die Dokument-CER bleibt einstellig.

#### Beispiel 2: Dokument 1060 (Typ A, Deutsch), `<choice>` und Schweizer gegen deutsche Orthografie

Referenz (`data/source/reference_tei/1060.xml`):

```xml
<p>Wenn ich diesen Preis nicht <choice><sic>gnügend</sic><corr>genügend</corr></choice> verdient habe, ist er …</p>
```

Nach Extraktion (E3, nur `<corr>`): `Wenn ich diesen Preis nicht genügend verdient habe, ist er …`

OCR (`output/mistral_results/1060_p3.md`): `Wenn ich diesen Preis nicht gnügend verdient habe, ist er …`

Differenz: „gnügend" gegen „genügend", eine Einfügung des e. Lokale CER auf dem Wort: 1/8 ≈ 12,5 %. Zweite Stelle: „Füssen" (Referenz, Schweizer Orthografie, 6 Zeichen) gegen „Füßen" (OCR, deutsche Orthografie, 5 Zeichen); die Distanz beträgt 2, da ein s durch ß ersetzt und das zweite s gelöscht wird. Lokale CER: 2/6 ≈ 33 %. Regel E3 extrahiert die kuratierte Form korrekt; die ss/ß-Differenz wird als substantielle orthografische Differenz nicht normalisiert.

#### Beispiel 3: Dokument 2530 (Typ B, Französisch, Zeitschriftenartikel), Guillemets, Striche, französische Interpunktion

Referenz (`data/source/reference_tei/2530.xml`):

```xml
<p>… c'est Israël – ses habitants, et non pas moi – qui aura à les courir.</p>
```

Nach Extraktion und Normalisierung (N10): `… c'est Israël - ses habitants, et non pas moi - qui aura à les courir.`

Das OCR schreibt einen Geviertstrich statt des Halbgeviertstrichs; nach N11 ist die Stelle identisch zur Referenz, Differenz 0. Zweite Stelle, der französische Doppelpunktabstand: „un premier principe:" gegen „un premier principe :"; N14 entfernt das Leerzeichen, danach Differenz 0. Dritte Stelle, Masthead und Autorzeile (`LA SITUATION D'ISRAËL`, `JEANNE HERSCH`): rund 35 Zeichen, die in der Referenz fehlen; da unter der 50-Zeichen-Schwelle, zählen sie als Fidelity-Einfügungen (lokale Last etwa 35/2 800 ≈ 1,2 %). In den Scope-Topf fielen sie erst ab 50 zusammenhängenden Zeichen. N10/N11 und N14 eliminieren typografische Unterschiede; Editionsmetadaten am Seitenrand werden hingegen als echte Differenz mitgemessen.

#### Beispiel 4: Dokument 1330 (Typ D, Französisch/Deutsch, Monografie), transparentes Markup

Referenz (`data/source/reference_tei/1330.xml`):

```xml
<p><persName ref="GND:118583530">Jacques Monod</persName>, par exemple, a publié un livre célèbre,
   et que je trouve admi<lb break="no"/>rable, intitulé
   <bibl ref="GND:4678418-4"><hi rendition="#i">Le hasard et la nécessité</hi></bibl>.</p>
```

Nach Extraktion (E7 fügt admirable zusammen, E9 behält nur den Innentext, E10 ignoriert das `ref`-Attribut): `Jacques Monod, par exemple, a publié un livre célèbre, et que je trouve admirable, intitulé Le hasard et la nécessité.`

Der OCR-Text vor der TEI-Generierung ist identisch, trägt jedoch Markdown-Sterne um den Buchtitel (`*Le hasard et la nécessité*`), also zwei Einfügungen. Im End-to-End-Vergleich (Pipeline-TEI gegen Referenz-TEI) wird `*Titel*` zu `<hi rendition="#i">Titel</hi>`, das E9 auf beiden Seiten entfernt; die Texte sind dann identisch, Differenz 0. Die Pipeline darf typografische Auszeichnung frei umsetzen, ohne CER-Strafe; GND-Identifikatoren in `ref`-Attributen berührt der Vergleich nicht (E10).

#### Beispiel 5: Dokument 1440 (Typ B, Deutsch, Monografie), fehlerbehaftete Referenz

Referenz (`data/source/reference_tei/1440.xml`):

```xml
<p>… 25. Kongreß der KPdSU, 5. Februar 1976, "lnforma<lb break="no"/>tionsbulletin" Nr. 6/7, 1976, Wien.</p>
```

Nach Extraktion (E7): `… 25. Kongreß der KPdSU, 5. Februar 1976, "lnformationsbulletin" Nr. 6/7, 1976, Wien.` Die Referenz enthält ein kleines l statt eines großen I in „lnformationsbulletin", eine in der Transkribus-Referenz nicht korrigierte Verwechslung von Klein-l und Groß-I.

Das OCR schreibt Guillemets und ein korrektes „Informationsbulletin". Nach N1/N2 sind die Anführungszeichen gleich; es bleibt „lnformationsbulletin" gegen „Informationsbulletin", eine Substitution l zu I. Lokale CER auf dem Wort: 1/20 = 5 %, gezählt gegen die Pipeline, obwohl sie hier die korrekte Form liefert (Annahme: Der Eigenname lautet „Informationsbulletin"; markierte Inferenz, hohe Konfidenz). Das Beispiel zeigt, dass die CER die Differenz zur Referenz misst; die Referenz ist Ground Truth per Definition und zugleich selbst eine fehlerbehaftete Transkription. Solche Fälle erhöhen die gemessene CER, ohne ein Pipeline-Versagen zu sein, und begrenzen das Erreichbare. Der Fehlerbestand der Referenzen ist inzwischen systematisch katalogisiert (6.4).

### 6.3 Korpus-Ergebnis und Datenlage

Headline-Resultat des aktuellen Korpus (n = 25, Seed 42, B = 10 000, Stand der Werte 2026-07-07 nach den Bestandsläufen und der Doppelseiten-Reparatur des Dokuments 30 (6.4)). Die Fidelity-CER, die echte Lese- und Auslassungsfehler ohne selektiv transkribierten Begleittext erfasst (Scope-Schwelle 50 Zeichen), liegt bei einem Median von 1,28 % (95-%-CI [1,06 %; 2,50 %]) und einem Mittel von 2,08 % (95-%-CI [1,51 %; 2,73 %]). Die Volltext-CER als Diagnosegröße, die den Pipeline-Mehrtext gegenüber den selektiv transkribierten Referenzen einschließt, liegt bei einem Median von 9,59 % und einem Mittel von 18,36 %; der Scope-Anteil allein beträgt im Mittel 16,28 %. Nach Transkribus-Konvention liegt der Median der Fidelity-CER im Bereich publikationsreif, der Mittelwert im Bereich forschungstauglich. Der paired Bootstrap gegen die Roh-OCR zeigt den Pipeline-Gewinn auf Dokumentebene, mit 17 von 25 Dokumenten verbessert und 8 verschlechtert.

Der Weg zu diesen Werten ist selbst Teil des Ergebnisses. Die erste Messung wies ein Fidelity-Mittel von 4,26 % aus. Die Fehleranalyse der Ausreißer führte auf einen Generator-Defekt, die Überdetektion von Fußnoten, bei der Haupttext in ausgeschlossene `<note>`-Elemente geriet und in der Messung als Löschung zählte. Eine referenzverifizierte Demotion, die einen Block nur dann in den Fließtext zurückführt, wenn ein zusammenhängender Lauf von mindestens 150 Zeichen seines Textes im Referenz-Body nachweisbar ist, senkte das Mittel dokumentiert über 3,99 % auf 2,71 %; die Bestandsläufe vom 07.07.2026, vor allem die Entfernung der Seitenzahl-Echos und die urteilsgesteuerte Demotion (6.4), senkten es weiter auf 2,50 %, und die Reparatur der verlorenen Doppelseiten-Hälfte des Dokuments 30 (6.4) auf 2,08 %. Jede Stufe dieses Verlaufs ist im Entscheidungsregister mit Datum und Methode festgehalten; eine Fortsetzung dieser Reparatur für Dokumente ohne Referenzabdeckung beschreibt 6.4.

Die Reproduktion erfolgt über `python -m scripts.eval.cer_statistics_full --seed 42 --bootstrap-n 10000`; das Ergebnis liegt versioniert als `docs/data/cer_statistics.json` vor, die Methodik in `knowledge/specification.md` und `knowledge/cer-methodology.md`, der Forschungsstandvergleich in `knowledge/literature-comparison.md`.

Auf der Datenseite gilt der in Abschnitt 2 beschriebene Trichter. Von den 286 gelieferten Dokumenten besitzen 285 ein finales TEI; das gelieferte PDF ohne finales TEI (Dokument 10) ist registriert und extern zu klären. Die früher offene Differenz zwischen Masterfile-Texten und geliefertem Bestand ist durch das Korpus-Audit aufgeklärt und reproduzierbar belegt.

#### Werte je Dokument

Die folgende Tabelle schlüsselt alle 25 gemessenen Dokumente nach Fidelity-CER auf und ordnet jedem erhöhten Wert seine Hauptursache zu. Die Streuung stammt aus drei strukturellen Mustern; die Zeichenerkennung selbst trägt sie nicht.

- Mehrtext gegen selektive Referenzen (Scope, kein Fehler)
- Fehlklassifikation von Fließtext als Fußnote (für die demotierten Dokumente behoben)
- Lesereihenfolge-Verdachtssignal auf Doppelseiten, das überwiegend korrupte Zonen-Zuordnungen über korrektem Text markiert (6.4)

Die vollständige Drei-Zahlen-Zerlegung je Dokument liegt in `docs/data/cer_statistics.json`.

| Doc | Typ | Sprache | Fidelity % | Hauptursache |
| :---- | :---- | :---- | ----: | :---- |
| 1440 | B | DE | 5,87 | Scope plus fehlerbehaftete Referenz |
| 760 | D | FR | 5,87 | Doppelseite, verlorene Bildunterschriften und unsegmentierte Paginierung, gegenprobenverifiziert (E91); die Lesereihenfolge selbst hält am Faksimile |
| 300 | D | FR | 5,00 | Scope plus Zusatzseiten |
| 1410 | B | FR | 4,24 | Scope plus Zusatzseiten |
| 130 | A | FR | 2,93 | nahezu sauber |
| 1910 | B | DE | 2,81 | Rest durch die urteilsgesteuerte Demotion beseitigt (E94) |
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
| 30 | A | FR | 0,90 | repariert, verlorene linke Hälfte der Doppelseite 1 ergänzt, Zonen korrigiert (E97/E98) |
| 100 | A | FR | 0,85 | sauber |
| 570 | A | FR | 0,79 | Scope (extrem) |
| 2635 | A | DE | 0,73 | sauber |
| 830 | D | FR | 0,69 | sauber |
| 580 | A | FR | 0,30 | Scope (extrem) |

#### Einordnung in den Forschungsstand

Print-kalibriert gelesen liegt der Fidelity-Median von 1,28 % zwischen dem besten spezialisierten Druck-Stack (Transkribus mit LLM-Nachkorrektur, 0,84 %; Crosilla et al. 2025) und Transkribus allein (3,67 %), solide für historischen Druck, aber nicht an der Spitze; das technische Optimum erreichen nur die besten Einzeldokumente (0,3 bis 0,8 %). Die Transkribus-Bewertungsbänder stammen primär aus der Handschriftenerkennung und setzen die Latte niedriger, als eine reine Druck-OCR-Aufgabe es rechtfertigt.

| Quelle | Verfahren | Sprache | CER |
| :---- | :---- | :---- | :---- |
| Crosilla et al. 2025 | Transkribus Print M1 + Gemini 2.0 Flash Nachkorrektur | deu (Fraktur) | 0,84 % |
| Crosilla et al. 2025 | Gemini 2.0 Flash zero-shot | deu | 1,27 % |
| Crosilla et al. 2025 | Transkribus Print M1 allein | deu | 3,67 % |
| Crosilla et al. 2025 | GPT-4o direkt | deu | 6,31 % |
| Levchenko 2025 | Gemini 2.5 Pro | rus (18. Jh.) | 3,36 % |
| Levchenko 2025 | Gemini 2.5 Flash | rus | 4,94 % |
| Levchenko 2025 | traditionelle OCR | rus | 21–45 % |
| Transkribus-Dokumentation | Richtwert | allgemein | 0,5–2 % |

Kein Eintrag ist ein Like-for-like-Benchmark; die Vergleichbarkeitsdimensionen je Eintrag stehen maschinenlesbar in `docs/data/cer_statistics.json` und ausführlich in `knowledge/literature-comparison.md`.

#### Korpusweite Plausibilitätsschätzung und Sprach-Audit

Für die 260 Dokumente ohne Ground Truth dient die Dictionary Hit Rate als Proxy, der Anteil der OCR-Wörter, die in französischen und deutschen Wörterbüchern stehen (nach Stroebel et al. 2022). Der Median liegt bei 97,7 %, 92 % der Dokumente erreichen mindestens 90 % Trefferquote, und die Ausreißer unter 75 % sind korrekt klassifizierte fremdsprachige Dokumente. Der zusammengesetzte Schätzer des Proxys generalisiert statistisch nicht (negatives LOOCV-R², siehe Abschnitt 7), weshalb der korpusweite Wert eine Plausibilitätsschranke bleibt und keine Messung ist. Ein Nebenbefund des Sprach-Audits ist, dass 284 der 285 Dokumente korrekt sprachklassifiziert sind; drei Etiketten wurden dabei korrigiert.

#### Grenzen der Messung

Die bekannten Grenzen sind mit den Werten offengelegt. Ground Truth existiert nur für 25 Dokumente, sodass Korpusaussagen Schätzungen bleiben. Das Referenz-Subset weicht auf der Zeichenmenge signifikant vom Korpus ab (Kolmogorov-Smirnov-Test auf `n_chars` mit p = 0,0139, `comparable=false`), während die vier weiteren Variablen (Sprache, Layout-Typ, Publikationsform, Seitenzahl) vergleichbar sind; die Abweichung ist in der JSON offen deklariert. Die CER misst zudem gegen eine selbst fehlerbehaftete Transkribus-Referenz (Beispiel 5) und ist damit eine Obergrenze der wahren Fehlerrate; der Fehlerbestand der Referenzen ist in `knowledge/ground-truth-map.md` systematisch katalogisiert. Die Run-zu-Run-Varianz der nicht-deterministischen LLM-Stufe ist vernachlässigbar (Abschnitt 7), und die frequenzbasierte HCPR-Adaption unterschätzt Substitutionen.

### 6.4 Qualitätssicherung jenseits der CER

Die CER beantwortet die Frage nach der Texttreue für die 25 referenzgedeckten Dokumente. Für das ganze Korpus und für die Richtlinienkonformität braucht es andere Instrumente. Das Projekt organisiert sie in einer dreistufigen Architektur, die strikt trennt, welches Verfahren welche Aussage treffen darf.

Die erste Ebene ist die deterministische Validierung, also Schema, Projektregeln, Konformitätsregeln und eine Familie von Audits, die reproduzierbar zählen und flaggen. Die zweite Ebene ist die agentische Verifikation. KI-Agenten prüfen stratifizierte Stichproben am Faksimile und liefern evidenzgebundene Befunde, je Seite mit Fundstelle, wörtlichem Beleg und Schweregrad. Diese Befunde sind Verdachtsurteile und werden nie als Korrektheitsnachweis gewertet. Die dritte Ebene ist die menschliche Adjudikation; ausschließlich sie vergibt den Status verifiziert. Diese Trennung ist eine Lehre aus dem Projektverlauf. Ein früheres agentenbasiertes Qualitäts-Screening hatte das gesamte Korpus als geprüft markiert, ohne dass ein Mensch beteiligt war, und wurde deshalb abgeschafft; seine Einträge wurden aus den ausgelieferten Dokumenten entfernt.

Auf der Audit-Ebene vermessen fünf Werkzeuge die Richtlinienkonformität korpusweit, mit folgendem Stand vor den Bestandskorrekturen: Die Zeichennormalisierung war die größte Lücke (88 978 gerade Apostrophe zwischen Buchstaben in 241 Dokumenten, daneben Guillemet- und Leerzeichenklassen, von denen sich die Leerzeichenklasse auf französischen Seiten überwiegend als korrekte Typografie und damit als umzudeutende Audit-Klasse erwies). Die gedruckte Paginierung fehlte breit (224 Dokumente führten in `pb@n` die Scan-Position, 18 die Druckfolio, 9 gemischt). Das OCR-Kursivsignal überlebt die Pipeline nahezu vollständig (18 betroffene Seiten in 12 Dokumenten); die Hauptursache fehlender `<hi>`-Auszeichnung liegt in der OCR-Engine selbst, weshalb eine bildbasierte Nacherkennung per LLM geprüft und verworfen wurde, da sie nicht deterministisch wäre und das Präzedenzmuster der Fußnoten-Überdetektion wiederholen würde. Die Relationenintegrität ist nahezu sauber. Ein fünftes Audit adressiert die Fußnoten-Überdetektion für Dokumente ohne Referenzabdeckung und fand 63 Kandidaten-Noten in 26 Dokumenten.

Auf der Verifikationsebene wurden alle 63 Kandidaten am Faksimile geprüft, mit klarem Ergebnis. 59 sind laufender Haupttext, der fälschlich als Fußnote gerahmt wurde, 2 sind abgesetzte Zitate, 2 sind echte Fußnoten (Audit-Falsch-Positive). Auf 39 der Seiten zeigt sich ein Rollentausch, denn die echte Fußnote der Seite liegt als gewöhnlicher Absatz mit ihrem Originalmarker im Body, während der Haupttext den Fußnotenrahmen erhielt. Eine Kalibrierungsrunde über weitere stratifizierte Seiten ergab zudem, dass das Lesereihenfolge-Warnsignal als Prädiktor für tatsächlich falsche Reihenfolge schwach ist (5 von 6 geprüften Verdachtsseiten waren korrekt), beim Hinsehen aber andere reale Defekte zutage fördert, etwa still fallengelassene Nicht-Artikel-Blöcke auf Zeitschriftenseiten und eine geleakte Modell-Absage im Text eines Dokuments, deren Ursache eine Wiederholungsschleife der Basis-OCR ist (inzwischen durch eine Einzelseiten-Reparatur ersetzt, siehe Abschnitt 7).

Eine unabhängige Gegenprobe hat die publizierten CER-Werte von außen reproduziert, ohne Code aus dem Repository, mit eigenständig implementierter Extraktion und Normalisierung, einer zweiten Levenshtein-Engine und eigener Aggregation. Alle Headline- und Einzelwerte wurden exakt bestätigt; die inhaltliche Klassifikation der größten Fehlerblöcke ergab, dass echter Textverlust die Ausnahme ist und Apparat-Einfügungen unter der Scope-Schwelle sowie Konventionsdivergenzen der Referenz die Fidelity-Werte nach oben treiben, ohne Erkennungsfehler zu sein.

Die Ground Truth selbst wurde vollständig inventarisiert. Die 25 Referenz-TEIs sind in den tragenden Körper-Konventionen richtlinienkonform, tragen aber korpusweit einen Transkribus-Stub als Header und einen eigenen, inzwischen katalogisierten Fehlerbestand, darunter Normdaten-Präfix-Drift, Migrationsreste und eine nicht wohlgeformte Datei (1520.xml, drei überkreuzte Element-Verschachtelungen). Für diese Datei liegt eine reparierte Kopie samt Änderungsnachweis vor; die Meldung an die ZBZ ist vorbereitet. Landkarte und Ausnahmekatalog stehen im Referenzdokument `knowledge/ground-truth-map.md`.

Aus Audits und Verifikation folgen die Bestandskorrekturen, ausgeführt als nachgelagerte deterministische Läufe auf dem ausgelieferten Korpus, jeweils mit Backup, idempotent und mit Audit-Messung vorher und nachher, also vollständig reversibel und überprüfbar. Ratifiziert sind drei Festlegungen: `pb@n` trägt die gedruckte Seitenzahl in eckigen Klammern, wie es die Referenzen durchgängig tun, mit der Scan-Nummer als ehrlichem Fallback ohne sicheres Signal; korrigiert wird hybrid, sichere Klassen maschinell und unsichere als Kurations-Worklists; die Verifikationstiefe ist die gezielte Adjudikation bekannter Konflikte samt Ergänzungsstichproben. Der erste Lauf ist vollzogen. Die Apostroph-Normalisierung senkte die betroffene Audit-Klasse von 88 978 Vorkommen auf null, bei unverändert grüner Schema-, Header- und Validator-Prüfung. Die zwei Folgeläufe, die Umstellung auf die Druckfolio (nach Vorschau: 1 753 Seiten aus Fußzeilen-Erkennung, 1 033 aus Interpolation, 151 aus stabilem Offset, 970 verbleibende Scan-Nummern, dazu 1 212 zu entfernende Seitenzahl-Echo-Absätze) und die urteilsgesteuerte Fußnoten-Demotion (59 Rückführungen, 2 Zitat-Überführungen, 19 Marker-Promotionen), sind gebaut und im Trockenlauf verifiziert worden.

Beide Folgeläufe sind am 07.07.2026 vollzogen und haben die Vorschauwerte exakt reproduziert. Der Druckfolio-Lauf erreicht 114 Dokumente mit vollständiger und 120 mit teilweiser Druckfolio-Abdeckung; 51 Dokumente bleiben beim Scan-Nummern-Fallback. Der Demotion-Lauf verarbeitete alle 63 Urteile ohne Rest, mit 59 Rückführungen in den Fließtext, 2 Zitat-Überführungen, 2 belassenen echten Fußnoten und 19 Marker-Promotionen in 26 Dokumenten. Der Erstlauf legte einen Werkzeugdefekt offen, der in vier Interview-Dokumenten 14 leere Sprecher-Rahmen hinterließ und deren Schema-Validität brach; der Defekt wurde im Werkzeug behoben (Entscheidungsregister E95), die Heilung erfolgte durch einen idempotenten Wiederholungslauf, der nachweislich ausschließlich diese 14 Rahmen entfernte und korpusweit keine Seitenzahl veränderte. Die Nachher-Audits bestätigen die Wirkung. Das Paginierungs-Audit klassifiziert nun 204 Dokumente als Druckfolio, 37 als Scan-Sequenz, 10 als gemischt und 34 als unbestimmt (vorher 18 Druckfolio); das Fußnoten-Audit findet statt 63 noch 3 Kandidaten, davon die 2 am Faksimile bestätigten echten Fußnoten und einen neuen Grenzfall für die Kurations-Worklist; die Apostroph-Klasse bleibt bei null. Schema, Projektregeln und pytest-Gates sind nach beiden Läufen unverändert grün, und die CER-Neumessung ergab die in 6.3 ausgewiesene Verbesserung, da die entfernten Echo-Absätze zuvor als Einfügungen zählten.

Die Einordnung des Dokuments 30 ist adjudiziert und der scheinbare Widerspruch der beiden Prüfungen aufgelöst. Die Gegenprobe klassifizierte den CER-Ausreißer als echten Textverlust auf Doppelseiten; die Faksimile-Kalibrierung fand auf den von ihr geprüften Doppelseiten vollständigen Text und deutete auf ein reines Alignment-Problem. Beide Befunde stimmen, denn die drei fehlenden Blöcke (540, 451 und 194 normalisierte Zeichen der kanonischen Alignierung) liegen sämtlich auf der linken Hälfte der ersten Doppelseite (Druckseite [222]), die die Kalibrierungsstichprobe (facs 2 bis 4) nicht umfasste. Am Faksimile ist der Text vollständig lesbar; im ausgelieferten TEI und in sämtlichen OCR-Datenströmen fehlt er. Der Ausreißer ist damit echter Erkennungsverlust einer Doppelseiten-Hälfte, den eine Lesereihenfolge-Korrektur nicht beheben kann; Die Reparatur ist inzwischen vollzogen: die gut lesbare Doppelseite wurde nach dem Muster des Dokuments 1520 neu gelesen und am Faksimile verifiziert, die drei verlorenen Absätze wurden samt ehrlicher Faksimile-Zonen ergänzt, zwei nachweislich falsche Zonen-Boxen korrigiert und die Seitenzahl auf die Druckfolio [222] gehoben. Die Fidelity-CER des Dokuments fiel von 11,59 % auf 0,90 %, womit das Korpus-Maximum verschwindet (Register E98).

Die geplante maschinelle Umstellung der Lesereihenfolge ist dagegen empirisch widerlegt und verworfen (Register E99). Der Reassembly-Weg war bereits gesperrt, weil er die Bestandskorrekturen und Hand-Reparaturen zurückdrehen würde; als Ersatz wurde ein test-first gebautes In-Place-Werkzeug erprobt, das robuste Verdachtsseiten byte-schonend in die geometrisch kanonische Ordnung bringt. Die CER-geschützte Probe an Kopien aller 25 Referenzdokumente ergab null Verbesserungen und neun Verschlechterungen bis zu 40 Prozentpunkten. Die Ursachenprüfung zeigt: der ausgelieferte Text der beanstandeten Seiten ist überwiegend korrekt, korrupt ist die Zuordnung der Blöcke zu ihren Faksimile-Zonen, sodass die geometrisch abgeleitete Ordnung verifizierten Text zerstören würde. Das deckt sich mit der Kalibrierungsrunde, in der fünf von sechs geprüften Verdachtsseiten korrekt lasen. Das Lesereihenfolge-Warnsignal ist seither als Text- oder Zonen-Verdachtssignal deklariert, seine Auflösung Kurationsarbeit am Faksimile; das Werkzeug bleibt als Dry-Run-Instrument samt dokumentiertem Beweisweg erhalten.

Ehrlich benannt bleibt das Restrisiko dieser Architektur. Die Audits sehen nur, wonach sie suchen; fehlklassifizierte Noten unterhalb der Audit-Schwelle, durch den Rollentausch verlorene echte Fußnoten außerhalb der Kandidatenmenge und die uneinheitliche Auszeichnung fremdsprachiger Passagen (nur 30 der 285 Dokumente tragen überhaupt `<foreign>`) sind quantifiziert oder als Untergrenze belegt, aber nicht behoben. Der erreichbare Anspruch der maschinellen Seite ist, dass alle bekannten Fehlklassen benannt und vermessen sind, die verifizierten deterministisch und reversibel korrigiert werden und der Rest als Arbeitsvorrat in die menschliche Kuration geht.

## 7 Grenzen und mögliche Weiterführung

Mehrere Aspekte sind unvollständig geblieben oder bewusst nicht bearbeitet worden. Die folgende Liste fasst beide zusammen, von Schwächen des Vorhandenen bis zu Schritten, die ein Anschlussvorhaben unternehmen könnte.

- Die semantische Anreicherung über Named Entity Recognition und Entity Linking wurde nach einer frühen Erprobung bewusst aus der Pipeline entfernt; das gelieferte Korpus ist entitätsfrei. Die verbindliche Zielform ist inline-GND-Auszeichnung an der Nennstelle, vorgesehen als nachgelagerte Kurationsaufgabe in einem eigenen Annotationswerkzeug; die dafür nötigen Konformitätsregeln sind bereits implementiert und werden auf diesem Output scharf. Identifikator-Zuordnung erfolgt dabei grundsätzlich über deterministische Normdaten-Abfragen und nie über ein Sprachmodell.
- Die Lesereihenfolge auf Doppelseiten und Mehrspaltern ist generatorseitig behoben (spalten- und bandbewusste Permutation, regressionsgetestet). Für den ausgelieferten Bestand ist die maschinelle Umstellung empirisch widerlegt und verworfen (6.4, Register E99); die Verdachtsseiten tragen überwiegend korrekten Text mit korrupter Zonen-Zuordnung und gehen als triagierte Worklist in die Faksimile-Kuration.
- Die Run-zu-Run-Stabilität der nicht-deterministischen LLM-Stufe ist pilotgemessen (5 stratifizierte Referenzdokumente mal 3 volle Läufe mit dem Produktionsmodell, Register E100). Die Fidelity-CER streut je Dokument um 0,00 bis 0,13 Prozentpunkte (Standardabweichung, Mittel 0,04); die Verfeinerungsstufe ist in ihrer Textwirkung praktisch deterministisch. Nebenbefund: frische Neugenerierungen erreichen die Qualität des kuratierten Bestands nicht, was den Ausschluss der Korpus-Neugenerierung (6.4) unabhängig stützt.
- Der Qualitäts-Proxy auf Basis der Dictionary Hit Rate generalisiert statistisch nicht (LOOCV-R² unter null) und wird deshalb nur als Plausibilitätsschranke geführt, nie als Messung.[^18]
- Auf der Datenseite bleiben extern zu klären die drei nicht gelieferten Texte (1745, 1750, 1970) und das gelieferte PDF ohne finales TEI (Dokument 10). Beide registrierten Einzeldefekte sind behoben. Die Seite mit geleakter Modell-Absage infolge degenerierter Basis-OCR (Dokument 1520, Seite 70) trägt nach einer Einzelseiten-Reparatur eine ehrliche Teiltranskription mit markierten unleserlichen Stellen; die Volltranskription braucht einen besseren Scan. Der adjudizierte Textverlust der ersten Doppelseite des Dokuments 30 ist durch dieselbe gezielte Nachbearbeitung behoben (6.4, Register E98).
- Die Auszeichnung fremdsprachiger Passagen ist uneinheitlich; ein deterministischer Wendungs-Detektor belegt mindestens 27 Dokumente mit unmarkierten Latein- oder Griechisch-Passagen, und der Sprachcode für Deutsch ist gemischt kodiert. Beides ist Kurationsvorrat mit vorhandener Werkzeugbasis.
- Der Round-Trip vom Viewer-Edit zurück in die Pipeline ist implementiert (Direktschreiben in den Arbeitsbaum, doppelte Ablage, Re-Lauf per Kommando), der Re-Lauf selbst bleibt ein manueller Schritt; der GitHub-Actions-Ausblick aus Abschnitt 5 würde ihn schließen.

## Anhang A: Skripte der Pipeline

Aufruf jeweils als Modul (`python -m scripts.<paket>.<modul>`); das Inventar wird in `scripts/README.md` gepflegt.

Vom Scan zum Seitenbild

- `edition/extract_pages.py` zerlegt die PDF-Scans seitenweise in PNG-Bilder, die zugleich als Faksimile und als Eingang für Texterkennung und Layout dienen.

Texterkennung

- `ocr/ocr_pipeline.py` steuert die Texterkennung und ruft je Dokument Mistral (Basis-Engine) oder Gemini (Opt-in) auf; Docling liefert ausschließlich Layout und keinen Text.
- `ocr/gemini_ocr_correct.py` liefert Ersatz- und Korrektur-OCR mit Gemini in zwei Varianten, nur aus Text oder zusätzlich mit dem Scan-Bild.
- `ocr/llm_postprocess.py` korrigiert den OCR-Text optional nach.
- `ocr/classify_docs.py` bestimmt aus den ersten Seiten per Gemini die Dokument-Metadaten wie Sprache, Typ, Titel, Autor und Datum.
- `core/loaders.py` legt fest, welcher OCR-Datenstrom Vorrang hat, und ermittelt die zu verarbeitenden Seiten.

Layoutanalyse

- `layout/run_layout_analysis.py` führt Docling lokal auf den Seitenbildern aus und schreibt pro Seite ein Layout-JSON.
- `layout/run_layout_cloud.py` erbringt dieselbe Layout-Analyse über eine docling-serve-Instanz statt lokal.
- `layout/layout_qa_gemini.py` korrigiert das Layout (QA), erkennt es neu (Detect) oder entscheidet je Seite automatisch zwischen beidem (Auto), jeweils mit Gemini.
- `layout/generate_layout_overlays.py` zeichnet die erkannten Regionen zur visuellen Kontrolle auf die Scans, auf Wunsch als Docling-gegen-Gemini-Vergleich.

Austauschformate

- `layout/page_xml_generator.py` erzeugt aus Layout-JSON und OCR-Markdown PAGE-XML (Schemaversion 2013-07-15).
- `layout/mets_generator.py` erzeugt das zugehörige METS-Manifest und wird vom PAGE-XML-Generator mitaufgerufen.
- `edition/transkribus_export.py` und `edition/transkribus_upload.py` bündeln PAGE-XML für den Transkribus-Round-Trip und laden es per REST in eine Collection.

TEI-Erzeugung

- `tei/tei_unified.py` orchestriert die drei TEI-Stufen, also Grundgerüst, Verfeinerung und Zusammenführung, samt Validierungsaufruf.
- `tei/tei_step1.py` baut das regelbasierte, deterministische TEI-Grundgerüst aus Text und Layout, inklusive kanonischer Lesereihenfolge, Druckseitenzahl-Erkennung mit dokumentweiter Interpolation und Ausschluss der Filterregion-Echos.
- `tei/tei_step2.py` verfeinert das Gerüst multimodal mit Gemini und bereinigt anschließend häufige Modellfehler.
- `tei/tei_step3.py` fügt die Seitenfragmente zum Gesamtdokument zusammen und wendet dokumentweite Konformitätskorrekturen an.
- `tei/tei_generator.py`, `tei/tei_mapping_prompt.py` und `tei/tei_xml_utils.py` liefern geteilte Bausteine, nämlich die Markdown-zu-TEI-Konvertierung, die Mapping-Tabelle für den Gemini-Prompt und die XML-Hilfsfunktionen samt Lesereihenfolge-Permutation.
- `tei/pb_split.py` segmentiert finale TEI byte-identisch an den Seitenumbrüchen, die geteilte Grundlage für Mirror und seitenweise Audits.

Validierung und Audits

- `tei/tei_validator.py` validiert gegen das RelaxNG-Schema und die Projektregeln, meldet informative Warnungen und prüft die ZBZ-Konformitätsregeln.
- `eval/benchmark_cer.py`, `eval/cer_statistics_full.py` und `eval/evaluate_ocr.py` bilden die CER-Messstrecke auf gemeinsamen kanonischen Funktionen.
- `eval/quality_proxy.py` liefert die Dictionary-Hit-Rate als Plausibilitätsschranke.
- `eval/completeness_check.py` prüft die Seitenvollständigkeit je Dokument und verrechnet dabei aufgetrennte Doppelseiten und Bibliotheks-Deckblätter deterministisch.
- `eval/corpus_audit.py` leitet die Korpus-Kennzahlen reproduzierbar aus den Primärquellen ab und flaggt Abweichungen zur Knowledge-Base.
- `eval/structure_audit.py` vergleicht die Pipeline-TEIs strukturell mit den 25 Referenzen.
- `eval/reading_order_audit.py` trianguliert die Lesereihenfolge-Verdachtsseiten in robust und fragil.
- `eval/char_lint_audit.py`, `eval/pb_number_audit.py`, `eval/hi_preservation_audit.py`, `eval/relation_integrity_audit.py` und `eval/body_note_audit.py` vermessen die Richtlinienkonformität (Zeichennormalisierung, Paginierungssemantik, Kursivsignal, Relationen, Fußnoten-Fehlklassifikation).
- `eval/audit_common.py` liefert den Audits die geteilte TEI-Erkennung und das Report-Gerüst.

Bestandskorrekturen (reversibel, mit Backup)

- `tei/tei_blank_marker.py` überträgt die erkannten Leerseiten als `<pb type="blank"/>` in das finale TEI.
- `tei/tei_status_marker.py` projiziert die Bearbeitungs-History idempotent als `<change>` in die Versionsbeschreibung.
- `tei/tei_surface_graphic.py` verknüpft jede Faksimile-Seite mit ihrer Bilddatei.
- `tei/tei_footnote_demote.py` führt referenzverifizierte Fußnoten-Fehlklassifikationen in den Fließtext zurück.
- `tei/tei_char_normalize.py` normalisiert die Apostroph-Klasse mit derselben Definition, die das Audit misst.
- `tei/tei_pb_folio.py` stellt `pb@n` auf die geklammerte Druckfolio um und entfernt Seitenzahl-Echo-Absätze.
- `tei/tei_body_note_demote.py` setzt die faksimile-verifizierten Urteile zur Fußnoten-Fehlklassifikation um, inklusive der Rückführung vertauschter echter Fußnoten.
- `tei/tei_reassemble_preview.py` baut den von der Lesereihenfolge-Umstellung betroffenen Bestand reversibel in eine Vorschau, ohne das ausgelieferte TEI zu berühren.
- `tei/marker_common.py` liefert den Marker-Läufen das geteilte Trockenlauf- und Backup-Gerüst.

Bearbeitungsstatus und Viewer-Daten

- `edition/page_manifest.py` erzeugt je Objekt das Manifest mit Workflow-Status und Bearbeitungs-History pro Datenstrom und markiert sichere Leerseiten.
- `edition/generate_edition_data.py` erzeugt den Katalog und den Per-Seiten-Mirror für das Webinterface.

[^1]: Zentralbibliothek Zürich. „Jeanne Hersch: Digitale Neuauflage der Schriften". [https://www.zb.uzh.ch/de/jeanne-hersch-digitale-neuauflage-der-schriften](https://www.zb.uzh.ch/de/jeanne-hersch-digitale-neuauflage-der-schriften).

[^2]: Deutsches Textarchiv. „DTA-Basisformat". [https://www.deutschestextarchiv.de/doku/basisformat](https://www.deutschestextarchiv.de/doku/basisformat).

[^3]: [https://dhcraft.org/Promptotyping](https://dhcraft.org/Promptotyping/)

[^4]: Pollin, Christopher. „Promptotyping: Zwischen Vibe Coding, Vibe Research und Context Engineering". L.I.S.A. Wissenschaftsportal Gerda Henkel Stiftung, 17. Januar 2026. [https://lisa.gerda-henkel-stiftung.de/digitale_geschichte_pollin](https://lisa.gerda-henkel-stiftung.de/digitale_geschichte_pollin).

[^5]: Claude Code, Dokumentation. [https://code.claude.com/docs/en/overview](https://code.claude.com/docs/en/overview).

[^6]: Repository: [https://github.com/chpollin/zbz-ocr-tei](https://github.com/chpollin/zbz-ocr-tei).

[^7]: Mistral AI. „Document AI" (OCR- und Dokumentverarbeitungs-API). [https://mistral.ai/news/mistral-ocr](https://mistral.ai/news/mistral-ocr).

[^8]: Livathinos, Nikolaos, Christoph Auer, Maksym Lysak u. a. „Docling: An Efficient Open-Source Toolkit for AI-driven Document Conversion". IBM Research, arXiv:2501.17887, 2025. [https://arxiv.org/abs/2501.17887](https://arxiv.org/abs/2501.17887). Software: [https://github.com/docling-project/docling](https://github.com/docling-project/docling).

[^9]: PAGE (Page Analysis and Ground-truth Elements), Schemaversion 2013-07-15, Namespace `http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15`. Spezifikation: Pletschacher, Stefan und Apostolos Antonacopoulos. „The PAGE (Page Analysis and Ground-Truth Elements) Format Framework". In: Proceedings of the 20th International Conference on Pattern Recognition (ICPR), 2010, S. 257–260. PRImA Research Lab: [https://www.primaresearch.org/tools/PAGELibraries](https://www.primaresearch.org/tools/PAGELibraries).

[^10]: Metadata Encoding and Transmission Standard (METS). Library of Congress, Network Development and MARC Standards Office. [https://www.loc.gov/standards/mets/](https://www.loc.gov/standards/mets/).

[^11]: OpenSeadragon, quelloffener Bildbetrachter für hochauflösende Zoombilder, Version 5.0.1. [https://openseadragon.github.io/](https://openseadragon.github.io/).

[^12]: Transkribus. „Character Error Rate (CER) Explained". [https://www.transkribus.org/character-error-rate-cer-explained](https://www.transkribus.org/character-error-rate-cer-explained) (Definition, Berechnung über die Levenshtein-Editierdistanz, Bewertungsschwellen, Layoutkomplexität als CER-Faktor).

[^13]: jiwer. [https://github.com/jitsi/jiwer](https://github.com/jitsi/jiwer) (Funktionsschnittstelle zur CER-Berechnung).

[^14]: dinglehopper, OCR-Evaluationswerkzeug der OCR-D-Initiative. [https://github.com/qurator-spk/dinglehopper](https://github.com/qurator-spk/dinglehopper).

[^15]: Levchenko, Maria. 2025. arXiv:2510.06743 (frequenzbasierte HCPR-Adaption zur Diakritika-Erhaltung).

[^16]: OCR-D. „Quality Assurance in OCR-D". [https://ocr-d.de/en/spec/ocrd_eval](https://ocr-d.de/en/spec/ocrd_eval) (CER-Definition, Unicode-Normalisierung NFC, Grapheme-Cluster, Letter Accuracy als eigene, noch nicht genutzte Metrik).

[^17]: Du, W. 2025. „When +1% Is Not Enough: A Paired Bootstrap Protocol for Evaluating Small Improvements". arXiv:2511.19794.

[^18]: Nach dem Ansatz von Stroebel et al. 2022 (Dictionary-basierte OCR-Qualitätsschätzung); die projektinterne Prüfung ergab ein negatives LOOCV-R² des zusammengesetzten Schätzers.
