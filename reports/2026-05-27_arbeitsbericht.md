# Arbeitsbericht: LLM-gestützte OCR- und TEI-Pipeline für die digitale Edition der Schriften von Jeanne Hersch

Dr. Christopher Pollin, Digital Humanities Craft OG

* v1, 27.05.2026  
* AI-Unterstützung: Claude Opus 4.7, Claude Code

## **Projektkontext und Zielsetzung**

Dieser Bericht dokumentiert ein Experiment im Rahmen der digitalen Neuauflage der Schriften von Jeanne Hersch, einem Projekt der Zentralbibliothek Zürich (ZBZ).[^1] Herschs philosophisches Werk ist mehrsprachig, überwiegend französisch und deutsch, und verstreut überliefert. Mehrsprachigkeit und heterogene Drucküberlieferung sind damit die beiden bestimmenden Anforderungen an die Pipeline.

Parallel zum etablierten Workflow der ZBZ von der Digitalisierung zur digitalen Edition wurde dieselbe Strecke ein zweites Mal durchlaufen, vollständig gestützt auf Large Language Models (LLMs) und Vision-Language Models (VLMs), agentenbasiert und werkzeuggestützt. Leitfrage ist, ob ein solcher Ansatz den etablierten Workflow in Textqualität und Aufwand erreicht. Aus der Parallelführung stammt zugleich die Vergleichsgrundlage: Die manuell über Transkribus erstellten Referenz-TEIs des etablierten Strangs dienen dem Experiment als Ground Truth (siehe 6.1).

Gegenstand ist eine Pipeline, die ausgehend von PDF-Scans TEI-XML im DTA-Basisformat erzeugt und in einem zugehörigen Webinterface anzeigbar und kuratierbar macht. Das DTA-Basisformat ist ein TEI-Subset für die einheitliche Auszeichnung digitalisierter Drucktexte.[^2] Die Pipeline simuliert die Digitalisierung ausgehend von den PDFs, erzeugt Transkription, Layouterkennung und TEI-XML jedoch durchgängig über LLMs und VLMs. Pipeline wie Webinterface entstehen durch *Promptotyping*, eine Context-Engineering-Arbeitsweise zur Erzeugung von Forschungsartefakten aus Forschungsdaten und Forschungskontexten.[^3] Die Codeerzeugung erfolgte vollständig innerhalb von *Claude Code* mit den jeweils aktuellen Opus-Modellen über mehrere Sessions hinweg;[^4] der Erzeugungsprozess ist über die Commit-Historie des offen vorliegenden Repositorys nachvollziehbar.[^5]

## **Datengrundlage**

Am Beginn der Pipeline stehen zwei von der ZBZ gelieferte Bestandteile, die PDF-Scans der digitalisierten Texte und das Masterfile mit den zugehörigen Metadaten. Diese Lieferung bildet die Ausgangslage; der katalogische Gesamtbestand und seine bibliothekarische Erschließung bleiben außer Betracht.

Das Masterfile ist die Katalog- und Steuerungstabelle der ZBZ und enthält zwei Arten von Information. Die bibliografischen Stammdaten umfassen ID, MMSID, Gattung, Jahr, Titel, Seitenzahl, Signatur und Sprache. Die Workflow-Spalten halten den Bearbeitungsstand im ZB-Prozess fest, etwa digitalisiert, Kontrolle Metadaten, korrigiert und ausgezeichnet.

Die folgenden Mengen wurden geliefert und verarbeitet.

| Stand | Anzahl |
| :---- | :---- |
| gelieferte Dokumente | 286 |
| davon mit finalem TEI | 285 |
| physische Seiten | 4.152 |

Die Verteilungen nach Dokumenttyp und Sprache beziehen sich auf den Lieferstand von 286 Dokumenten; das eine Dokument ohne finales TEI ist in 6.3 vermerkt. Die gelieferten Dokumente sind durchweg Drucktexte; handschriftliches Material ist nicht systematisch vertreten, sodass es sich um einen reinen OCR-Prozess handelt. Der Bestand erstreckt sich über die Jahre 1931 bis 1998\.

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
| mehrsprachig fr/de | 1 | \< 1 % |
| ohne Angabe | 1 | \< 1 % |

## **Repository-Architektur**

Der Ordner `knowledge/` ist ein Promptotyping-Vault, eine an eine Obsidian-Forschungsvault angelehnte, in Claude Code erzeugte und kuratierte Wissensbasis in Markdown, die das Projektwissen abbildet und über den Projektverlauf iterativ wächst; einzelne Dokumente entstehen, wachsen oder werden zusammengeführt. Leitprinzip ist die Single Source of Truth: Jeder Fakt steht in genau einem Dokument, auf das die übrigen verweisen. Hervorzuheben sind das chronologische Arbeitstagebuch `journal.md` als beschreibende Schicht neben der Git-Historie und das durchnummerierte Entscheidungsregister `decisions.md`.

Der Ordner `data/` enthält Eingangs- und Referenzdaten und trennt Geliefertes von projektseitig Erzeugtem. Unter `data/source/` liegen die von der ZB gelieferten Startdaten: die PDF-Scans, die manuell über Transkribus erstellten Referenz-TEIs samt zugehörigen PAGE-XML-Exporten, das Masterfile und die Editionsrichtlinien. Daneben stehen projektseitig erstellte Referenzdaten: das projektspezifische TEI-Schema `schema/zbz_hersch.rng` und die im Viewer kuratierten Editions-TEIs (`curated_tei/`). Die per LLM erzeugte Dokumentklassifikation liegt in `doc_metadata.json`, damit sie nicht bei jedem Pipeline-Lauf neu berechnet wird.

Der Ordner `output/` enthält alle generierten Datenströme (OCR, Layout, PAGE-XML, TEI) und ist bewusst nicht versioniert. Der Ordner `scripts/` enthält die von Claude Code generierte Python-Pipeline, nach Domäne in Unterpakete gegliedert (`ocr`, `layout`, `tei`, `eval`, `edition`, `core`); die einzelnen Skripte sind in Anhang A aufgeführt. Die Reproduzierbarkeit der Evaluation sichern die `pytest`\-Suiten unter `tests/`, darunter die in 6.1 genannte Statistik-Library.

Der Ordner `docs/` ist für GitHub Pages konfiguriert und enthält das Frontend, einen Mirror der Pipeline-Daten und die aus den PDFs erzeugten PNGs. Da GitHub Pages ohne Backend nur statische Dateien ausliefert, liegen die Editionsdaten dort als generierter Per-Seiten-Mirror unter `docs/data/pages/{doc}/`, der den Großteil der versionierten Dateien ausmacht: Ein Skript zerlegt das finale TEI seitenweise und legt je Seite eine Datei für TEI, OCR-Text und Layout ab. Der Mirror deckt alle 285 Dokumente ab; nur die Faksimile-Bilder bleiben außerhalb einiger Demonstrationsdokumente lokal. Verbindliche Quelle ist nicht dieser Mirror, sondern das TEI unter `output/tei_final/{doc}_final.xml`, aus dem der Mirror nach jeder Änderung neu erzeugt wird, etwa nach einem erneuten Pipeline-Lauf oder einer im Viewer kuratierten und zurückgespielten Bearbeitung. Ein Edit am Mirror ginge beim nächsten Lauf verloren. Diese Trennung von verbindlicher Editionsablage und Anzeige-Spiegel gilt für alle folgenden Abschnitte.

## **Die Pipeline**

Die Pipeline überführt PDF-Scans in TEI-XML. Je Dokument entstehen drei Datenströme: ein OCR-Datenstrom mit dem erkannten Text, ein Layout-Datenstrom mit der Seitenstruktur und der daraus abgeleitete TEI-XML-Datenstrom mit der edierten Fassung. Die Verarbeitung ist durchgängig defensiv ausgelegt, sodass eine fehlschlagende Einzelkorrektur die Eingabe unverändert weiterreicht, statt den Lauf abzubrechen.

### **Vom Scan zum Seitenbild**

Zu Beginn werden die PDF-Scans seitenweise in Einzelbilder zerlegt, auf denen die nachfolgenden Stufen aufsetzen.

### **Texterkennung**

Produktiv erfolgt die Texterkennung mit **Mistral Document AI**[^6] über Azure AI Foundry. Das Modell erfasst neben Fließtext auch Tabellen und Listen und liefert seitenweises Markdown; große Dokumente werden automatisch aufgeteilt, eine von Claude Code eigenständig getroffene Entscheidung. Steht dieser Zugang nicht zur Verfügung, kann ersatzweise ein multimodales **Gemini**\-Modell dieselbe Aufgabe übernehmen, ohne dass sich für die Folgestufen etwas ändert. Eine optionale, sprachmodellgestützte Nachkorrektur ist verfügbar, aber nicht standardmäßig aktiv, weil sie bei bereits guter Ausgangsqualität keinen Mehrwert bringt; wo eine korrigierte Fassung vorliegt, wird sie der Rohfassung vorgezogen.

### **Layoutanalyse**

Die Strukturerkennung verbindet **Docling**[^7] mit einem nachgeschalteten Schritt durch Gemini. Docling liefert dabei allein die Seitenstruktur, also Regionen mit Position, nicht den Text. Der Gemini-Schritt arbeitet in drei Betriebsarten. QA prüft und ergänzt die Docling-Regionen, Detect erkennt das Layout direkt vom Seitenbild neu, und Auto schaltet nur bei zu schwacher Docling-Abdeckung auf die ersetzende Neudetektion. Beide Layoutfassungen, die von Docling und die von Gemini, bleiben als getrennte Dateien erhalten, sodass nachvollziehbar bleibt, welche Region von welcher Engine stammt.

### **Austauschformate**

Aus dem Layout- und dem OCR-Datenstrom wird zusätzlich PAGE-XML[^8] erzeugt und daraus ein METS-Manifest[^9], Austauschformate für externe Bearbeitungs- und Archivsysteme. Das PAGE-XML entsteht aus denselben Quellen wie das TEI, ohne dessen Vorstufe zu sein, denn das TEI wird unmittelbar aus Layout und Text gebildet.

### **TEI-Erzeugung**

Die TEI-Erzeugung verbindet regelbasierte und sprachmodellgestützte Arbeit. Zunächst entsteht aus dem OCR- und dem Layout-Datenstrom ein deterministisches Grundgerüst. Textabschnitte werden den Layoutregionen nach ihrer Position zugeordnet, in Überschriften, Absätze, Fußnoten und vergleichbare Strukturen übersetzt und mit Seiten- und Zeilenmarken versehen. Dabei werden auch die typografischen Vereinheitlichungen gemäß den Editionsrichtlinien sowie die Auflösung getrennter Wörter berücksichtigt. Auf dieses Gerüst setzt ein verfeinernder Schritt auf, der das Seitenbild zusammen mit dem Gerüst und dem erkannten Text einem multimodalen Modell vorlegt und so eine strukturell angereicherte Fassung erzeugt. Da modellgenerierte Auszeichnung systematische Eigenheiten aufweist, schließt sich eine korrigierende Nachbearbeitung an, die häufige Struktur- und Schemaverstöße automatisch bereinigt. In der abschließenden Zusammenführung werden die Einzelseiten zu einem Gesamtdokument verbunden, seitenweise entstandene Gliederungseinheiten zusammengezogen und ein zweiter Satz dokumentweiter Korrekturen angewandt.

### **Validierung**

Das erzeugte TEI wird zweistufig geprüft, zum einen gegen das projektspezifische RelaxNG-Schema `zbz_hersch.rng`, das auf dem DTA-Basisformat aufbaut und um die verbindlichen ZBZ-Editionsrichtlinien ergänzt ist, zum anderen gegen projekteigene Regeln, die strukturelle Mindestanforderungen blockierend durchsetzen. Ergänzend markieren informative Hinweise prüfenswerte Stellen, ohne die Gültigkeit zu blockieren. Die quantitativen Validierungsergebnisse stehen in 6.1.

### **Bearbeitungsstatus statt Selbstzertifizierung**

Die Pipeline erzeugt für jedes Dokument drei Dinge: den erkannten Text (OCR), die Seitenstruktur (Layout) und ein DTA-konformes, einfaches, die Textstrukturen abbildendes TEI-XML (Überschriften, Absätze, Fußnoten, Seiten- und Zeilenumbrüche). Diese drei Datenströme sind nach der maschinellen Erzeugung zunächst nicht verifiziert, also vorhanden, aber fachlich noch nicht geprüft. Den Prüfstand hält ein menschgesetzter Bearbeitungsstatus fest, getrennt für jeden der drei Ströme. Jeder Strom nimmt einen von drei Werten an, unverifiziert, in Arbeit oder verifiziert, die im Webinterface als dreistufige Ampel erscheinen (neutral, gelb, grün) und per Klick weitergeschaltet werden. Jeder Wechsel wird in einer dokumentbezogenen Begleitdatei festgehalten, dem Manifest, einer JSON-Datei je Dokument, und zwar als fortlaufende Liste der einzelnen Schritte mit Zeitpunkt, Bearbeiterkürzel sowie Vor- und Folgestatus, sodass eine vollständige Bearbeitungsspur entsteht. Bei der Übergabe an die ZB werden diese Einträge in die TEI-Versionsbeschreibung (\<revisionDesc\>) des Dokuments übernommen, sodass die Bearbeitungsgeschichte mit dem ausgelieferten Dokument selbst reist.

## **5\. Webinterface und Kuration**

Das Webinterface ist ein im Browser laufendes, auf GitHub Pages gehostetes Werkzeug zur Überprüfung und Kuration der Pipeline-Ergebnisse ([https://chpollin.github.io/zbz-ocr-tei/](https://chpollin.github.io/zbz-ocr-tei/)). Den Kern bildet der Pipeline-Viewer (`docs/viewer.html`), eine Single-Page-App ohne Backend und ohne Build-Schritt, die ihre Inhalte aus dem in der Repository-Architektur beschriebenen Per-Seiten-Mirror lädt — einer pro Dokument und Seite vorab erzeugten Datenablage (aufbereiteter OCR-Text, Layout-Regionen und das aus dem finalen TEI herausgelöste Seiten-TEI), die das gesamte Korpus ohne Server bereitstellt. Der Viewer bildet eine Bild-Text-Synopse: Faksimile und zugehöriger Text stehen nebeneinander, sodass beide Seite für Seite verglichen werden können. Das Faksimile wird im Ansichtsmodus über *OpenSeadragon* dargestellt[^10] und erlaubt stufenloses Zoomen, Verschieben und Drehen, mit den erkannten Layout-Regionen als Overlay. Der Textbereich ist zwischen drei Quellen umschaltbar, dem aufbereiteten OCR-Rohtext, der gerenderten TEI-Fassung, also dem aus dem TEI-XML erzeugten formatierten Lesetext, und dem TEI-XML-Quelltext selbst. Leerseiten erkennt der Viewer vorab, bevorzugt am TEI-Marker `<pb type="blank"/>`, ersatzweise über eine Textregel auf dem OCR-Ergebnis, und kennzeichnet sie als solche, statt fehlerhafte Regionen oder OCR-Artefakte anzuzeigen.

Daneben stehen vier weitere, direkt aufrufbare Seiten:

- [Korpus-Übersicht](https://chpollin.github.io/zbz-ocr-tei/) — sortierbare Tabelle mit Workflow-Ampeln und Filtern über Strom und Status  
- [Methode](https://chpollin.github.io/zbz-ocr-tei/methode.html) — statische Seite mit Headline-CER, stratifizierten Werten, Literaturvergleich und Limitations  
- [About](https://chpollin.github.io/zbz-ocr-tei/about.html)  
- [Impressum](https://chpollin.github.io/zbz-ocr-tei/impressum.html)

Die **Kuration** ist in den Viewer integriert und kommt ohne separaten Server aus: Der Browser hält keinen Server-Zustand und lädt nichts hoch; alle Änderungen bleiben lokal und werden erst auf Klick gespeichert (siehe unten). Layout und Text tragen je einen eigenen, unabhängigen Bearbeitungsschalter. Beim Wechsel in den Layout-Editor löst die Faksimile-Anzeige OpenSeadragon durch eine einfache, bearbeitbare Overlay-Ebene ab; darin lassen sich Regionen-Boxen auswählen, verschieben, skalieren, neu aufziehen und löschen, ihr Typ ändern (sechs Typen: Heading, Paragraph, Fussnote, Caption, Filter, Skip) und ihre Lesereihenfolge per Ziehen ordnen. Die Boxen werden als bildrelative Prozentkoordinaten (0–100, bezogen auf die in der Layout-Analyse festgehaltenen Seitendimensionen) geführt, sodass sie zoom- und auflösungsunabhängig deckungsgleich auf Faksimile und Overlay liegen; der Editor korrigiert die von der maschinellen Layout-Analyse vorgeschlagenen Boxen und setzt ihre fachliche Richtigkeit gerade nicht voraus.

Der **Transkriptions-Editor** schaltet die jeweils angezeigte Textquelle auf direkt editierbar, wobei strukturelle Eingriffe dem XML-Modus vorbehalten sind, da die gerenderte Ansicht beim Editieren nur den Text und nicht die Auszeichnung zurückgibt. Ein einziger Speichern-Knopf sichert alle offenen Ströme zugleich, und zwar jeweils doppelt: kanonisch in den `output/`-Baum (Layout nach `output/layout/`, der kuratierte Text nach `output/ocr_curated/`, Objekt-Manifest und finales TEI nach `output/tei_final/`) und gespiegelt in den Anzeige-Mirror unter `docs/data/`, damit ein Reload den Stand sofort zeigt. Geschrieben wird über die File System Access API der Chromium-Browser direkt in den lokalen Klon des Repositories, den Working Tree; wo diese Schnittstelle fehlt, tritt ein Datei-Download als Rückfallebene an ihre Stelle. Nichts wird hochgeladen. Das Objekt-Manifest ist die Pro-Dokument-JSON, die Workflow-Status und Leerseiten je Datenstrom hält. Dieser bewusst server-lose Schnitt vermeidet Backend-Betrieb und Mehrnutzer-Konflikte. Die Speicherung ersetzt aber nicht den Pipeline-Lauf: Damit eine kuratierte Layout- oder Textfassung in das TEI eingeht, regeneriert ein erneuter Lauf (`--reassemble`) das Dokument, dessen Ergebnis anschließend in die ausgelieferte Schicht `output/tei_final/` gehoben und in den Mirror gespiegelt wird. Dieser Round-Trip aus Speichern und Re-Lauf beruht weiterhin auf Konvention statt auf einem Mechanismus. (Ausblick: Er ließe sich künftig über die GitHub-Plattform schließen, etwa indem ein Commit einen GitHub-Actions-Lauf auslöst, der `--reassemble` ausführt und das regenerierte TEI samt Mirror zurückschreibt.) Jeder Datenstrom trägt einen Status mit drei Stufen (unverifiziert, in Arbeit, verifiziert), der im Viewer per Klick weitergeschaltet wird und sich in den Ampeln der Korpus-Übersicht spiegelt; das erste Aktivieren eines Bearbeitungsschalters setzt den betroffenen Strom automatisch von unverifiziert auf in Arbeit, und solange Änderungen nicht gespeichert sind, warnt das Interface beim Verlassen der Seite. Der leitende Gedanke ist, dass die Edition selbst zum Kurationswerkzeug wird: Die Editorinnen und Editoren arbeiten direkt in der Edition, lernen dabei mehr über die Texte und bessern die Fehler der Pipeline aus.

Ergänzend wurden 79 sichere Leerseiten in 15 Dokumenten erkannt und als `<pb type="blank"/>` in die finalen TEI projiziert. Als sicher gilt eine Seite nur, wenn zwei unabhängige Signale übereinstimmen: Der OCR-Text ist praktisch leer (höchstens fünf Zeichen, kein alphanumerisches Zeichen oder lediglich ein „Blank Page"-Marker) und die Docling-Layout-Analyse findet null Regionen. Nur bei Übereinstimmung wird der Marker gesetzt; widersprechen sich die Signale — Text leer, aber Docling erkennt Regionen —, wird die Seite zum manuellen Review markiert statt projiziert (im aktuellen Korpus trat kein solcher Konflikt auf). Ein Export-Modul auf JSZip-Basis erlaubt Per-Dokument- und Bulk-Export der Datenströme als ZIP.

## **6\. Qualität und methodologische Einordnung**

Die Qualität der Pipeline wird über die Zeichenfehlerrate (Character Error Rate, CER) gegen die manuell erstellten Referenz-TEIs gemessen. Abschnitt 6.1 entwickelt die Vergleichsmethodik von der Definition der Kennzahl über die Frage, gegen welche Referenz gemessen wird, bis zu den Extraktions-, Normalisierungs- und Verifikationsregeln. Abschnitt 6.2 belegt die Regeln an fünf realen Dokumenten. Abschnitt 6.3 berichtet das Korpus-Ergebnis und die verbleibende Datenlage.

### **6.1 Vergleichsmethodik gegen die Referenz-TEIs**

#### Was die CER misst und wie sie hier definiert ist

Die CER ist der Anteil der Zeichen im Referenztext, die im erzeugten Text abweichen. Sie ist definiert als die Levenshtein-Distanz zwischen Referenz und Hypothese, geteilt durch die Zeichenzahl der Referenz.

Die Levenshtein-Distanz ist die minimale Anzahl an Einzelzeichen-Operationen (Einfügung, Löschung, Ersetzung), um die Hypothese in die Referenz zu überführen.[^11] Diese Operationen werden nicht vorgegeben, sondern ergeben sich aus der Distanzberechnung. Die Überführungsrichtung (Hypothese zu Referenz) ist im gesamten Kapitel einheitlich, sodass die Benennung der Operationstypen über alle Beispiele konsistent bleibt; die Distanz selbst ist richtungsunabhängig. Implementiert ist sie über `rapidfuzz.distance.Levenshtein`.

Aggregationseinheit ist das Dokument, nicht die Seite. Das Korpus-Bootstrap-Verfahren (n \= 25 Referenz-TEIs, B \= 10 000, Seed 42, BCa-Konfidenzintervall) liefert daraus Mittelwert und 95-%-Vertrauensbereich. Zur Einordnung der Werte dient die Transkribus-Konvention, nach der unter 2 % als publikationsreif, 2 bis 5 % als forschungstauglich und 5 bis 10 % als brauchbar für Volltextsuche gilt.[^12] Eine hohe CER bedeutet dabei nicht zwingend schlechte Texterkennung; sie kann ebenso aus fehlerhafter Lesereihenfolge bei komplexem Layout folgen[^13] oder daraus, dass Mistral Document AI ein generelles, nicht auf historische Schrift spezialisiertes Modell ist. Die Berechnung selbst ist ein einzelner Funktionsaufruf;[^14] die methodische Substanz liegt in der Aufbereitung der beiden Texte und in der Wahl der Referenz.

#### Gegen welche Referenz gemessen wird

Die CER misst die Abweichung von einer gewählten Referenz, nicht objektive Korrektheit. Bei TEI-Ground-Truth ist deshalb vorab festzulegen, welche Lesart die Referenz bildet, denn TEI hält an mehreren Stellen zwei konkurrierende Fassungen desselben Textes vor. Zwei Elementpaare sind relevant. `<sic>` / `<corr>` kennzeichnet eine überlieferte fehlerhafte Form gegenüber einer editorischen Korrektur. `<abbr>` / `<expan>` kennzeichnet eine Abkürzung gegenüber ihrer Auflösung. Der Unterschied ist, dass `<expan>` Text enthält, der nie physisch auf der Vorlage stand (die Auflösung von „Dr." zu „Doctor"), während `<corr>` eine plausible Lesetextvariante ist, die sich von `<sic>` meist nur um wenige Zeichen unterscheidet.

Das Experiment misst gegen die edierte, kuratierte Zielfassung. Bei `<sic>` / `<corr>` wird die korrigierte Form `<corr>` gewählt (Regel E3).

Das Elementpaar `<abbr>` / `<expan>` kommt in den Referenz-TEIs des Korpus nicht vor; ihre `<choice>`-Konstrukte sind durchgängig `<sic>` / `<corr>`, sodass für den Vergleich allein Regel E3 greift. `extract_text_for_comparison()` enthält keine eigene Behandlung dieses Paars; ein künftiges Auftreten fiele unter die generische Regel E9 und wäre dann gesondert zu regeln.

Diese Wahl hat eine messbare Konsequenz, die Beispiel 5 in 6.2 zeigt: Enthält die Referenz selbst einen Transkriptionsfehler, zählt eine korrektere Erkennung als Differenz. Solche Fälle erhöhen die gemessene CER, sind kein Pipeline-Fehler und begrenzen das mit dieser Methodik Erreichbare.

#### Zerlegung der Fehler in Fidelity und Scope

Die Editieroperationen werden in zwei Kategorien zerlegt, die unterschiedliche Fehlerursachen trennen. **Fidelity** erfasst echte Erkennungsfehler, also Substitutionen, Löschungen und kleine Einfügungen, und bildet das Maß für die Lesequalität im engeren Sinn. **Scope** erfasst große Einfügungen ab einer Schwelle von 50 Zeichen, die typischerweise nicht aus Erkennungsfehlern stammen, sondern aus Textbestandteilen, welche die Pipeline erfasst, die selektiv transkribierte Referenz aber nicht enthält, etwa Mastheads, Autorzeilen oder Editionsmetadaten. Die **Fidelity-CER** wertet nur die erste Kategorie, die **Volltext-CER** schließt den Scope-Anteil als Diagnosegröße ein. Beide Kategorien summieren sich zeichengenau zur Levenshtein-Distanz.

Diese Zuordnung ist am Code bestätigt: `SCOPE_BLOCK_MIN = 50` in `classify_edit_operations()`; Ersetzungen, Löschungen und Einfügungen unter 50 Zeichen zählen zur Fidelity, Einfügungen ab 50 Zeichen zum Scope. Beide Töpfe summieren sich zeichengenau zur Levenshtein-Distanz.

#### TEI-Extraktion

Vor dem Vergleich wird aus jedem TEI in `extract_text_for_comparison()` ein Vergleichstext erzeugt. Dieselbe Funktion verarbeitet beide Seiten, das Referenz-TEI wie das aus der Pipeline erzeugte TEI, damit gemessene Differenzen ausschließlich aus dem Textinhalt stammen und nicht aus einer ungleichen Behandlung der Seiten.

| Nr. | Regel | Effekt |
| :---- | :---- | :---- |
| E1 | XML-Parser über `xml.etree.ElementTree`, Namensraum-Präfixe entfernen | `{tei}p` wird zu `p` |
| E2 | nur Inhalt unterhalb von `<body>` | `<teiHeader>`, `<front>`, `<back>` werden ignoriert |
| E3 | `<choice><sic>X</sic><corr>Y</corr></choice>` → nur `<corr>` | bei Schreibvariante gilt die kuratierte Lesart |
| E4 | `<choice>` ohne `<corr>`, nur `<sic>` → `<sic>` | Fallback |
| E5 | `<note place="foot">…</note>` → ausgeschlossen (Default) | separat edierte Fußnoten würden den Fließtext-Vergleich verzerren; via `include_footnotes=True` einschaltbar |
| E6 | `<lb/>` ohne `break="no"` → ein Leerzeichen | Druck-Zeilenumbruch ist eine Wortgrenze |
| E7 | `<lb break="no"/>` → kein Zeichen | getrenntes Wort wird zusammengezogen (Hu \+ manismus → Humanismus) |
| E8 | `<pb/>` → zwei Zeilenumbrüche `\n\n` | Seitengrenze bleibt erkennbar |
| E9 | alle übrigen Elemente (`<hi>`, `<persName>`, `<bibl>`, `<title>`, `<head>`, `<p>`, `<div>` …) → rekursiv Innentext | Markup wird transparent: `<hi>Wort</hi>` → Wort |
| E10 | Attributwerte werden nicht übernommen | Seitenzahlen aus `<pb n="223"/>`, GND-IDs aus `ref`\-Attributen erscheinen nicht im Vergleich |
| E11 | XML-Tails werden beim Eltern-Element angehängt | korrekte Reihenfolge bei `<p>Wort1<hi>Wort2</hi>Wort3</p>` |
| E12 | bei XML-Parse-Fehler Regex-Fallback `re.sub(r'<[^>]+>', '', content)` | sichert die Auswertung gegen einzelne nicht wohlgeformte TEIs, damit eine fehlerhafte Datei den Korpuslauf nicht abbricht |

#### Normalisierung

Nach der Extraktion durchläuft der Text `normalize_for_comparison()`, ebenfalls beidseitig identisch. Die Regeln vereinheitlichen typografische Varianten, die keine inhaltlichen Unterschiede sind.

| Nr. | Regel | Mapping |
| :---- | :---- | :---- |
| N1 / N2 | französische Guillemets → ASCII `"` | « (U+00AB), » (U+00BB) |
| N3 | deutsches unteres Anführungszeichen → ASCII `"` | „ (U+201E) |
| N4 / N5 | spitze Anführungszeichen → ASCII `'` | ‹ (U+2039), › (U+203A) |
| N6 / N7 | Backtick, Akut → ASCII `'` | \` (U+0060), ´ (U+00B4) |
| N8–N12 | Hyphen, geschützter Bindestrich, Halbgeviert-, Geviert-, Ziffernstrich → ASCII `-` | U+2010, U+2011, U+2013, U+2014, U+2012 |
| N13 | weicher Trennstrich entfernen | U+00AD → '' |
| N14 | Leerzeichen vor `; : ? !` entfernen (frz. Typografie) | `re.sub(r' +([;:?!])', r'\1', text)` |
| N15 | mehrfacher Whitespace → ein Leerzeichen | `re.sub(r'\s+', ' ', text)` |
| N16–N19 | englische Anführungszeichen und Apostrophe → ASCII `"` / `'` | U+201C, U+201D, U+2018, U+2019 |
| N20 | Whitespace am Anfang/Ende entfernen | `strip()` |
| N21 | Unicode-Normalform NFC | `unicodedata.normalize('NFC', text)` |

Bewusst nicht normalisiert werden Groß- und Kleinschreibung, Diakritika, Satzzeichen, die Unterscheidung von ß und ss sowie Zahlen, da diese substantielle und keine typografischen Differenzen sind. Der case-sensitive Default folgt der Werkzeugpraxis von dinglehopper[^15] und jiwer, die Lowercasing als Opt-in führen; eine optionale case-insensitive Sekundärmetrik existiert (`casefold=True`). Die Erhaltung von Akzenten wird über eine eigene Metrik (HCPR) getrennt geprüft.

#### Verifikation der Messmethodik

Diese Verifikation betrifft die Korrektheit der CER-Messung und ist von der in Abschnitt „Validierung" beschriebenen TEI-Schemavalidierung zu unterscheiden. Sie ruht auf drei Schichten. Erstens 18 handgerechnete Regressionstests (`tests/test_cer_extraction.py`), die unabhängig vom Korpus-Ergebnis das Verhalten festschreiben, darunter die kanonische Formel, Case-Sensitivität, das Unterbleiben von Trimming, die `<choice>`\-Auflösung, die Normalisierung und die Zerlegung in Fidelity und Scope samt zeichengenauer Summenkontrolle. Zweitens die Vereinheitlichung der zuvor drei separaten CER-Implementierungen (`benchmark_cer`, `cer_statistics_full`, `tei_validator --compare-ref`) auf gemeinsame kanonische Funktionen seit Entscheidung E70, sodass alle drei Pfade für dasselbe Dokument dieselbe Zahl liefern. Drittens der Abgleich der Konventionen mit externen Standards: Nenner als Distanz durch Referenzlänge (Transkribus), NFC-Normalisierung als Grapheme-Cluster-Definition (OCR-D),[^16] case-sensitiver Default (jiwer und allgemeine Werkzeugpraxis; OCR-D sieht das Ignorieren der Groß-/Kleinschreibung nur in einer eigenen Letter-Accuracy-Metrik vor), Volltextvergleich ohne Alignment-Trimming (dinglehopper)[^17] sowie der paired multi-seed Bootstrap mit BCa-Konfidenzintervall für Deltas (Singh 2025\).[^18] Die Vergleichbarkeit von CER-Werten zwischen verschiedenen Werkzeugen ist allerdings selbst bei nominell gleicher Metrik begrenzt, unter anderem weil bereits die Umwandlung strukturierter Ground Truth in Vergleichstext bei nicht berücksichtigter Lesereihenfolge zur Fehlerquelle wird; die hier dokumentierten Extraktions- und Normalisierungsregeln sind die projektinterne Festlegung dieser Transformation.

**\[KLÄRUNG IM REPOSITORY — quantitative Schemavalidierung\]** Der Validierungsabschnitt des Berichts verweist auf „quantitative Validierungsergebnisse in 6.1". Einzutragen sind die Kennzahlen der TEI-Validierung gegen `zbz_hersch.rng` und die Projektregeln: Wie viele der 285 finalen TEI sind schemavalide, wie viele blockierende Regelverstöße bzw. informative Hinweise verbleiben, und auf welchem Stand? Diese Zahlen liegen weder im CER-Material noch im bisherigen Berichtstext vor.

### **6.2 Fünf Beispiele aus unterschiedlichen Dokumenttypen**

Jedes Beispiel nennt Doc-ID, Layout-Typ und Sprache, stellt eine Referenzstelle der zugehörigen Pipeline-Stelle gegenüber, identifiziert die Differenzen, verweist auf die anwendbaren Regeln und gibt die lokale CER an.

#### Beispiel 1 — Doc 130 (Typ A, Französisch, Zeitschriftenartikel): Titel im Versalsatz

Referenz (`data/source/referenz-tei/130.xml:28-31`):

\<head\>

  \<title type="main"\>L'école de nos périls\</title\>

  \<title type="sub"\>Le problème de l'élite ouvrière\</title\>

\</head\>

Nach Extraktion (E2, E6, E9): `L'école de nos périls Le problème de l'élite ouvrière`

OCR (`output/mistral_results/130_p3.md:1-3`): `L'ÉCOLE DE NOS PÉRILS LE PROBLÈME DE L'ÉLITE OUVRIÈRE`

Die kasusbehafteten Buchstaben unterscheiden sich durchgängig in der Groß-/Kleinschreibung und zählen als Substitutionen; Leerzeichen und Apostroph bleiben gleich. Versalsatz wird nicht normalisiert (siehe 6.1), da er eine Schreibvariante ist.

**\[KLÄRUNG IM REPOSITORY — Zählung Beispiel 1\]** Die im Quellmaterial genannte lokale CER „41 Substitutionen / 54 Zeichen ≈ 76 %" ist nachzurechnen und die Zählbasis anzugeben (Zeichenzahl mit oder ohne Leerzeichen). Die Zahl muss als publiziertes Beispiel exakt stimmen.

Im Gesamtdokument verdünnt sich der Effekt: Der Titel umfasst 54 Zeichen, der Volltext rund 33 000\. Die Dokument-CER bleibt einstellig.

#### Beispiel 2 — Doc 1060 (Typ A, Deutsch): `<choice>` und Schweizer vs. deutsche Orthografie

Referenz (`data/source/referenz-tei/1060.xml:56`):

\<p\>Wenn ich diesen Preis nicht \<choice\>\<sic\>gnügend\</sic\>\<corr\>genügend\</corr\>\</choice\> verdient habe, ist er …\</p\>

Nach Extraktion (E3, nur `<corr>`): `Wenn ich diesen Preis nicht genügend verdient habe, ist er …`

OCR (`output/mistral_results/1060_p3.md:9`): `Wenn ich diesen Preis nicht gnügend verdient habe, ist er …`

Differenz: „gnügend" gegen „genügend", eine Einfügung des e. Lokale CER auf dem Wort: 1/8 ≈ 12,5 %. Zweite Stelle (TEI-Zeile 46): „Füssen" (Referenz, Schweizer Orthografie, 6 Zeichen) gegen „Füßen" (OCR, deutsche Orthografie, 5 Zeichen); die Distanz beträgt 2, da ein s durch ß ersetzt und das zweite s gelöscht wird. Lokale CER: 2/6 ≈ 33 %. Regel E3 extrahiert die kuratierte Form korrekt; die ss/ß-Differenz wird als substantielle orthografische Differenz nicht normalisiert.

#### Beispiel 3 — Doc 2530 (Typ B, Französisch, Zeitschriftenartikel): Guillemets, Striche, französische Interpunktion

Referenz (`data/source/referenz-tei/2530.xml:35-36`):

\<p\>… c'est Israël – ses habitants, et non pas moi – qui aura à les courir.\</p\>

Nach Extraktion und Normalisierung (N10): `… c'est Israël - ses habitants, et non pas moi - qui aura à les courir.`

OCR (`output/mistral_results/2530_p1.md:7`): mit Geviertstrich (—) statt Halbgeviertstrich; nach N11 identisch zur Referenz, Differenz 0\. Zweite Stelle, französischer Doppelpunktabstand (TEI-Zeile 38 gegen OCR-Zeile 9): „un premier principe:" gegen „un premier principe :"; N14 entfernt das Leerzeichen, danach Differenz 0\. Dritte Stelle, Masthead und Autor (`LA SITUATION D'ISRAËL`, `JEANNE HERSCH`): rund 35 Zeichen, die in der Referenz fehlen; da unter der 50-Zeichen-Schwelle, zählen sie als Fidelity-Einfügungen, nicht als Scope (lokale Last etwa 35/2 800 ≈ 1,2 %). N10/N11 und N14 eliminieren typografische Unterschiede; Editionsmetadaten am Seitenrand werden hingegen als echte Differenz mitgemessen.

#### Beispiel 4 — Doc 1330 (Typ D, Französisch/Deutsch, Monografie): transparentes Markup

Referenz (`data/source/referenz-tei/1330.xml:74`):

\<p\>\<persName ref="GND:118583530"\>Jacques Monod\</persName\>, par exemple, a publié un livre célèbre,

   et que je trouve admi\<lb break="no"/\>rable, intitulé

   \<bibl ref="GND:4678418-4"\>\<hi rendition="\#i"\>Le hasard et la nécessité\</hi\>\</bibl\>.\</p\>

Nach Extraktion (E7 fügt admirable zusammen, E9 behält nur den Innentext, E10 ignoriert das `ref`\-Attribut): `Jacques Monod, par exemple, a publié un livre célèbre, et que je trouve admirable, intitulé Le hasard et la nécessité.`

Der OCR-Text vor der TEI-Generierung ist identisch, trägt jedoch Markdown-Sterne um den Buchtitel (`*Le hasard et la nécessité*`), also zwei Einfügungen. Im End-to-End-Vergleich (Pipeline-TEI gegen Referenz-TEI) wird `*Titel*` zu `<hi rendition="#i">Titel</hi>`, das E9 auf beiden Seiten entfernt; die Texte sind dann identisch, Differenz 0\. Die Pipeline darf typografische Auszeichnung frei umsetzen (`*…*` ↔ `<hi>…</hi>`), ohne CER-Strafe; GND-Identifikatoren in `ref`\-Attributen berührt der Vergleich nicht (E10).

#### Beispiel 5 — Doc 1440 (Typ B, Deutsch, Monografie): fehlerbehaftete Referenz

Referenz (`data/source/referenz-tei/1440.xml:41-43`):

\<p\>… 25\. Kongreß der KPdSU, 5\. Februar 1976, "lnforma\<lb break="no"/\>tionsbulletin" Nr. 6/7, 1976, Wien.\</p\>

Nach Extraktion (E7): `… 25. Kongreß der KPdSU, 5. Februar 1976, "lnformationsbulletin" Nr. 6/7, 1976, Wien.` Die Referenz enthält ein kleines l statt eines großen I in „lnformationsbulletin", eine in der Transkribus-Referenz nicht korrigierte Verwechslung von Klein-l und Groß-I.

OCR (`output/mistral_results/1440_p1.md:12`): mit Guillemets und korrektem „Informationsbulletin". Nach N1/N2 sind die Anführungszeichen gleich; es bleibt „lnformationsbulletin" gegen „Informationsbulletin", eine Substitution l → I. Lokale CER auf dem Wort: 1/20 \= 5 %, gezählt gegen die Pipeline, obwohl sie hier die korrekte Form liefert (Annahme: Der Eigenname lautet „Informationsbulletin"; markierte Inferenz, hohe Konfidenz). Das Beispiel zeigt, dass die CER die Differenz zur Referenz misst, nicht objektive Korrektheit; die Referenz ist Ground Truth per Definition, aber selbst eine fehlerbehaftete Transkription. Solche Fälle erhöhen die gemessene CER, ohne ein Pipeline-Versagen zu sein, und begrenzen das Erreichbare.

### **6.3 Korpus-Ergebnis und Datenlage**

Headline-Resultat des aktuellen Korpus (n \= 25, Seed 42, B \= 10 000, Stand 2026-06-08): Die Fidelity-CER, die echte Lese- und Auslassungsfehler ohne selektiv transkribierten Begleittext erfasst, liegt bei einem Median von 1,83 % und einem Mittel von 3,99 % (95-%-CI \[2,36 %; 5,96 %\]). Die Volltext-CER als Diagnosegröße, die den Pipeline-Mehrtext gegenüber den selektiv transkribierten Referenzen einschließt, liegt bei einem Median von 12,29 % und einem Mittel von 20,22 %. Diese Werte sind print-kalibriert einzuordnen: Die Transkribus-Qualitätsbänder (unter 2 Prozent „publikationsreif", 2 bis 5 Prozent „forschungstauglich") stammen primär aus der HTR-Praxis der Handschriftenerkennung und schmeicheln einer reinen Druck-OCR-Aufgabe, bei der die Messlatte höher liegt. Maßgeblich ist daher der Vergleich mit der Print-OCR-Literatur: Der Fidelity-Median von 1,83 Prozent liegt zwischen dem besten spezialisierten Stack (Transkribus mit LLM-Nachkorrektur, 0,84 Prozent; Crosilla et al. 2025) und Transkribus allein (3,67 Prozent) — solide für historischen Druck, aber nicht an der Spitze; das technische Optimum erreichen nur die besten Einzeldokumente (0,3 bis 0,8 Prozent). Hinzu kommt, dass die CER gegen eine selbst fehlerbehaftete Transkribus-Referenz misst (Beispiel 5, Doc 1440) und damit eine Obergrenze der wahren Fehlerrate ist. Die Reproduktion erfolgt über `python -m scripts.eval.cer_statistics_full --seed 42 --bootstrap-n 10000`; Methodikdetails in `knowledge/quality.md`.

Gegenüber dem ersten Korpuslauf (Mittel 4,26 %) ist der Mittelwert leicht gesunken, weil bei Dokument 30 eine OCR-Duplikation (ein doppelt erfasster Textblock) entfernt wurde; das senkte dessen Fidelity-CER von 18,25 % auf 11,59 %. Der Median bleibt unverändert robust bei 1,83 %.

Die folgende Aufstellung schlüsselt alle 25 gemessenen Dokumente nach Fidelity-CER auf und ordnet jeder erhöhten CER ihre Hauptursache zu. Sie belegt, dass die Streuung nicht aus der Zeichenerkennung stammt, sondern aus drei strukturellen Mustern: Mehrtext gegenüber selektiven Referenzen (Scope, kein Fehler), Fehlklassifikation von Fließtext als Fußnote sowie verwürfelter Lesereihenfolge bei Doppelseiten. Die acht als „sauber“ markierten Dokumente (Volltext etwa gleich Fidelity, Scope null) zeigen die Erkennungsqualität bei einfachem Layout und vollständiger Referenz.

| Doc | Typ | Spr | Fidelity % | Volltext % | Scope % | Hauptursache |
| :---- | :---- | :---- | ----: | ----: | ----: | :---- |
| 290 | A | FR | 17,72 | 24,78 | 7,06 | Body-als-Fußnote (Gemini) |
| 1910 | B | DE | 16,43 | 38,80 | 22,37 | Scope + Body-als-Fußnote |
| 30 | A | FR | 11,59 | 12,13 | 0,54 | Lesereihenfolge (Doppelseite) |
| 90 | A | DE | 7,59 | 28,86 | 21,28 | Scope + Extra-Seiten + Fußnote |
| 1440 | B | DE | 5,87 | 16,95 | 11,07 | Scope + fehlerhafte Referenz |
| 760 | D | FR | 5,87 | 7,05 | 1,17 | Lesereihenfolge (Doppelseite) |
| 300 | D | FR | 5,05 | 31,63 | 26,58 | Scope + Extra-Seiten |
| 1410 | B | FR | 4,24 | 21,91 | 17,68 | Scope + Extra-Seiten |
| 1520 | C | FR | 3,61 | 5,97 | 2,37 | Extra-Seiten |
| 130 | A | FR | 2,94 | 2,94 | 0,00 | nahezu sauber |
| 560 | A | FR | 2,61 | 2,61 | 0,00 | sauber |
| 2310 | A | FR | 2,46 | 64,96 | 62,50 | Scope (JSTOR-Cover) |
| 2530 | B | FR | 1,83 | 1,83 | 0,00 | sauber |
| 40 | C | FR | 1,58 | 1,82 | 0,24 | sauber |
| 890 | B | DE | 1,37 | 13,81 | 12,43 | Scope |
| 1060 | A | DE | 1,14 | 12,29 | 11,15 | Scope |
| 1180 | A | FR | 1,12 | 2,42 | 1,30 | sauber |
| 3040 | B | FR | 1,09 | 24,15 | 23,06 | Scope (Fußnoten) |
| 3020 | B | DE | 1,06 | 1,55 | 0,49 | sauber |
| 1330 | D | FR | 1,03 | 13,13 | 12,10 | Scope |
| 570 | A | FR | 0,93 | 113,28 | 112,36 | Scope (extrem) |
| 100 | A | FR | 0,85 | 0,85 | 0,00 | sauber |
| 2635 | A | DE | 0,76 | 0,76 | 0,00 | sauber |
| 830 | D | FR | 0,75 | 1,49 | 0,74 | sauber |
| 580 | A | FR | 0,30 | 59,57 | 59,27 | Scope (extrem) |


Auf der Datenseite bleibt festzuhalten, dass von den 286 gelieferten Dokumenten 285 ein finales TEI besitzen. Das gelieferte PDF ohne finales TEI (Dokument 10\) ist registriert und extern zu klären. Davon zu unterscheiden sind drei im Masterfile gelistete, aber nicht gelieferte Texte (1745, 1750, 1970\) sowie die noch offene Differenz zwischen den Masterfile-Texten und den öffentlich genannten ZB-Texten. Diese Punkte sind in Abschnitt 7 als Grenzen zusammengeführt.

### **7 Grenzen und mögliche Weiterführung**

Mehrere Aspekte sind unvollständig geblieben oder bewusst nicht bearbeitet worden. Die folgende Liste fasst beide zusammen, von Schwächen des Vorhandenen bis zu Schritten, die ein Anschlussvorhaben unternehmen könnte.

Die folgende Übersicht bündelt die im Projekt identifizierten Probleme kompakt an einer Stelle, mit Status je Befund. Zwei der Defekte (2 und 3) sind echte Pipeline-Mängel, die sowohl die ausgelieferte TEI als auch die gemessene CER betreffen; Posten 4 ist kein Fehler, sondern eine Eigenschaft der selektiven Referenzen.

| # | Problem | Betroffen | Ursache | Status |
| :---- | :---- | :---- | :---- | :---- |
| 1 | OCR-Duplikation (doppelt erfasster Textblock) | Dok 30 | Mistral wiederholte einen Absatz | behoben (Dedup; Fidelity 18,25 zu 11,59 %) |
| 2 | Verwürfelte Lesereihenfolge bei Doppelseiten | 30, 760 | Querformat-Scans (ein Bild = zwei Seiten); der Region-Matcher sortiert nur nach y-Position und ignoriert x, daher verschränken sich linke und rechte Seite | offen (Code: x-bewusste Sortierung der Regionen) |
| 3 | Fließtext fälschlich als Fußnote ausgezeichnet | 290, 1910, 90 | Geminis Layout-QA über-detektiert Fußnoten-Regionen; der Text wandert in `<note place="foot">` und fällt aus dem Fidelity-Vergleich (Regel E5) | offen (Layout-Prompt schärfen + Kuration; ein automatischer Demote ist unsicher, weil 1520, 40 und 3040 echte lange Fußnoten führen) |
| 4 | Scope: Mehrtext gegenüber selektiver Referenz | 570, 580, 2310, 300, 3040, 890, 1060, 1330 | Die Referenz-TEIs sind Teiltranskriptionen; die Pipeline erfasst Cover, Titelei, Nachbarbeiträge und Fußnoten zusätzlich | kein Defekt; durch die Fidelity/Scope-Trennung als Diagnosegröße ausgewiesen |
| 5 | Fehlerhafte Referenz | 1440 | Die Transkribus-Ground-Truth enthält selbst einen Transkriptionsfehler, die korrektere Pipeline wird bestraft | nicht behebbar (Ground Truth per Definition; siehe Beispiel 5) |
| 6 | CER-Schwellen HTR-kalibriert | Methodik | Die Transkribus-Qualitätsbänder stammen aus der Handschriftenerkennung und schmeicheln einer Druck-OCR-Aufgabe | behoben (print-kalibriert eingeordnet; Vergleich mit Print-OCR-Literatur) |
| 7 | Header-Schema-Defekt im `<idno>` | finale TEI | registriert | offen |

Darüber hinaus offen oder bewusst ausgespart:

- Die semantische Anreicherung über Named Entity Recognition und Named Entity Linking, also die Erkennung von Personen, Orten und Organisationen und ihre Verknüpfung mit Normdaten wie GND und Wikidata, wurde nicht durchgeführt und ist nicht Gegenstand dieses Berichts. Sie wäre ein naheliegender nächster Schritt.  
- Die Run-zu-Run-Stabilität der nicht-deterministischen LLM-Stufen ist nicht quantifiziert.  
- Der Proxy auf Basis der Dictionary Hit Rate generalisiert statistisch nicht (LOOCV-R² unter 0).  
- Auf der Datenseite bleiben extern zu klären die drei nicht gelieferten Texte (1745, 1750, 1970), das gelieferte PDF ohne finales TEI (10) sowie die Differenz zwischen den Masterfile-Texten und den öffentlich genannten ZB-Texten.  
- Der Round-Trip vom Viewer-Edit zurück in die Pipeline ist dokumentiert, aber nicht in einem Wrapper-Skript automatisiert; er beruht auf Konvention statt auf Mechanismus.

## **Anhang A: Skripte der Pipeline**

Aufruf jeweils als Modul (`python -m scripts.<paket>.<modul>`).

**Vom Scan zum Seitenbild**

- `scripts/edition/extract_pages.py` zerlegt die PDF-Scans seitenweise in PNG-Bilder, die zugleich als Faksimile und als Eingang für Texterkennung und Layout dienen.

**Texterkennung**

- `scripts/ocr/ocr_pipeline.py` steuert die Texterkennung und ruft je nach Dokumenttyp Mistral, Docling oder Gemini auf.  
- `scripts/ocr/gemini_ocr_correct.py` liefert Ersatz- und Korrektur-OCR mit Gemini in zwei Varianten, nur aus Text oder zusätzlich mit dem Scan-Bild.  
- `scripts/ocr/llm_postprocess.py` korrigiert den OCR-Text optional mit Claude Haiku nach.  
- `scripts/ocr/ocr_dedup.py` entfernt OCR-Halluzinationen wie Wiederholungs-Loops und Zeichen-Artefakte.  
- `scripts/ocr/classify_docs.py` bestimmt aus den ersten Seiten per Gemini die Dokument-Metadaten wie Sprache, Typ, Titel, Autor und Datum.  
- `scripts/core/loaders.py` legt fest, welcher OCR-Datenstrom Vorrang hat, und ermittelt die zu verarbeitenden Seiten.

**Layoutanalyse**

- `scripts/layout/run_layout_analysis.py` führt Docling lokal auf den Seitenbildern aus und schreibt pro Seite ein Layout-JSON.  
- `scripts/layout/run_layout_cloud.py` erbringt dieselbe Layout-Analyse über eine docling-serve-Instanz statt lokal.  
- `scripts/layout/layout_qa_gemini.py` korrigiert das Layout (QA), erkennt es neu (Detect) oder entscheidet je Seite automatisch zwischen beidem (Auto), jeweils mit Gemini.  
- `scripts/layout/generate_layout_overlays.py` zeichnet die erkannten Regionen zur visuellen Kontrolle auf die Scans, auf Wunsch als Docling-gegen-Gemini-Vergleich.

**Austauschformate**

- `scripts/layout/page_xml_generator.py` erzeugt aus Layout-JSON und OCR-Markdown PAGE-XML (Schemaversion 2013-07-15).  
- `scripts/layout/mets_generator.py` erzeugt das zugehörige METS-Manifest und wird vom PAGE-XML-Generator mitaufgerufen.

**TEI-Erzeugung**

- `scripts/tei/tei_unified.py` orchestriert die vier TEI-Stufen, also Grundgerüst, Verfeinerung, Zusammenführung und Validierung.  
- `scripts/tei/tei_step1.py` baut das regelbasierte, deterministische TEI-Grundgerüst aus Text und Layout.  
- `scripts/tei/tei_step2.py` verfeinert das Gerüst multimodal mit Gemini und bereinigt anschließend häufige Modellfehler.  
- `scripts/tei/tei_step3.py` fügt die Seitenfragmente zum Gesamtdokument zusammen, also Header, Faksimile und Body, und wendet dokumentweite Korrekturen an.  
- `scripts/tei/tei_generator.py`, `scripts/tei/tei_mapping_prompt.py` und `scripts/tei/tei_xml_utils.py` liefern geteilte Bausteine, nämlich die Markdown-zu-TEI-Konvertierung, die Mapping-Tabelle für den Gemini-Prompt und die XML-Hilfsfunktionen.

**Validierung**

- `scripts/tei/tei_validator.py` validiert gegen das RelaxNG-Schema und die Projektregeln und meldet zusätzlich informative Warnungen.

**Bearbeitungsstatus**

- `scripts/edition/page_manifest.py` erzeugt je Objekt das Manifest mit Workflow-Status und Bearbeitungs-History pro Datenstrom und markiert sichere Leerseiten.  
- `scripts/tei/tei_status_marker.py` projiziert die Bearbeitungs-History bei der ZB-Übergabe als `<change>` in die Versionsbeschreibung und entfernt dabei die irreführenden Agent-Screening-Einträge.  
- `scripts/tei/tei_blank_marker.py` überträgt die erkannten Leerseiten als `<pb type="blank"/>` in das finale TEI.

**Audit**

- `scripts/corpus_audit.py` leitet die Korpus-Kennzahlen reproduzierbar aus den Primärquellen ab und flaggt Abweichungen zur Knowledge-Base.

[^1]: Zentralbibliothek Zürich. „Jeanne Hersch: Digitale Neuauflage der Schriften". [https://www.zb.uzh.ch/de/jeanne-hersch-digitale-neuauflage-der-schriften](https://www.zb.uzh.ch/de/jeanne-hersch-digitale-neuauflage-der-schriften).

[^2]: Deutsches Textarchiv. „DTA-Basisformat". [https://www.deutschestextarchiv.de/doku/basisformat](https://www.deutschestextarchiv.de/doku/basisformat).

[^3]: Pollin, Christopher. „Promptotyping: Zwischen Vibe Coding, Vibe Research und Context Engineering". L.I.S.A. Wissenschaftsportal Gerda Henkel Stiftung, 17\. Januar 2026\. [https://lisa.gerda-henkel-stiftung.de/digitale\_geschichte\_pollin](https://lisa.gerda-henkel-stiftung.de/digitale_geschichte_pollin).

[^4]: Claude Code, Dokumentation. [https://code.claude.com/docs/en/overview](https://code.claude.com/docs/en/overview).

[^5]: Repository: [https://github.com/chpollin/zbz-ocr-tei](https://github.com/chpollin/zbz-ocr-tei).

[^6]: Mistral AI. „Document AI" (OCR- und Dokumentverarbeitungs-API). [https://mistral.ai/news/mistral-ocr](https://mistral.ai/news/mistral-ocr).

[^7]: Livathinos, Nikolaos, Christoph Auer, Maksym Lysak u. a. „Docling: An Efficient Open-Source Toolkit for AI-driven Document Conversion". IBM Research, arXiv:2501.17887, 2025\. [https://arxiv.org/abs/2501.17887](https://arxiv.org/abs/2501.17887). Software: [https://github.com/docling-project/docling](https://github.com/docling-project/docling).

[^8]: PAGE (Page Analysis and Ground-truth Elements), Schemaversion 2013-07-15, Namespace `http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15`. Spezifikation: Pletschacher, Stefan und Apostolos Antonacopoulos. „The PAGE (Page Analysis and Ground-Truth Elements) Format Framework". In: Proceedings of the 20th International Conference on Pattern Recognition (ICPR), 2010, S. 257–260. PRImA Research Lab: [https://www.primaresearch.org/tools/PAGELibraries](https://www.primaresearch.org/tools/PAGELibraries).

[^9]: Metadata Encoding and Transmission Standard (METS). Library of Congress, Network Development and MARC Standards Office. [https://www.loc.gov/standards/mets/](https://www.loc.gov/standards/mets/).

[^10]: OpenSeadragon, quelloffener Bildbetrachter für hochauflösende Zoombilder, Version 5.0.1. [https://openseadragon.github.io/](https://openseadragon.github.io/).

[^11]: Transkribus, *Character Error Rate (CER) Explained*. [https://www.transkribus.org/character-error-rate-cer-explained](https://www.transkribus.org/character-error-rate-cer-explained) (Definition, Berechnung über die Levenshtein-Editierdistanz, Bewertungsschwellen, Layoutkomplexität als CER-Faktor).

[^12]: Transkribus, *Character Error Rate (CER) Explained*. [https://www.transkribus.org/character-error-rate-cer-explained](https://www.transkribus.org/character-error-rate-cer-explained) (Definition, Berechnung über die Levenshtein-Editierdistanz, Bewertungsschwellen, Layoutkomplexität als CER-Faktor).

[^13]: Transkribus, *Character Error Rate (CER) Explained*. [https://www.transkribus.org/character-error-rate-cer-explained](https://www.transkribus.org/character-error-rate-cer-explained) (Definition, Berechnung über die Levenshtein-Editierdistanz, Bewertungsschwellen, Layoutkomplexität als CER-Faktor).

[^14]: `jiwer`. [https://github.com/jitsi/jiwer](https://github.com/jitsi/jiwer) (Funktionsschnittstelle zur CER-Berechnung).

[^15]: dinglehopper, OCR-Evaluationswerkzeug der OCR-D-Initiative. [https://github.com/qurator-spk/dinglehopper](https://github.com/qurator-spk/dinglehopper).

[^16]: OCR-D, *OCR-D Evaluation und Metriken*. [https://ocr-d.de/en/spec/ocrd\_eval](https://ocr-d.de/en/spec/ocrd_eval). \[KLÄRUNG: exakte URL/Abschnitt am Standard verifizieren.\]

[^17]: dinglehopper, OCR-Evaluationswerkzeug der OCR-D-Initiative. [https://github.com/qurator-spk/dinglehopper](https://github.com/qurator-spk/dinglehopper).

[^18]: Singh, \[Vorname\], u. a. (2025). arXiv:2511.19794. \[KLÄRUNG: vollständige Autor- und Titelangabe am Preprint ergänzen.\]