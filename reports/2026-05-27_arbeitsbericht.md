# Arbeitsbericht: LLM-gestützte OCR- und TEI-Pipeline für die digitale Edition der Schriften von Jeanne Hersch

Dr. Christopher Pollin, Digital Humanities Craft OG

* v1.1, 30.05.2026 (v1: 27.05.2026)  
* AI-Unterstützung: Claude Opus 4.7 / 4.8, Claude Code

## **Projektkontext und Zielsetzung**

Dieser Bericht dokumentiert ein Experiment im Rahmen der digitalen Neuauflage der Schriften von Jeanne Hersch, einem Projekt der Zentralbibliothek Zürich (ZBZ).[^1] Herschs philosophisches Werk ist mehrsprachig, überwiegend französisch und deutsch, und verstreut überliefert. Mehrsprachigkeit und heterogene Drucküberlieferung sind damit die beiden bestimmenden Anforderungen an die Pipeline.

Parallel zum etablierten Workflow der ZBZ von der Digitalisierung zur digitalen Edition wurde dieselbe Strecke ein zweites Mal durchlaufen, vollständig gestützt auf Large Language Models (LLMs) und Vision-Language Models (VLMs), agentenbasiert und werkzeuggestützt. Leitfrage ist, ob ein solcher Ansatz den etablierten Workflow in der Textqualität erreicht. Aus der Parallelführung stammt zugleich die Vergleichsgrundlage: Die manuell über Transkribus erstellten Referenz-TEIs des etablierten Strangs dienen dem Experiment als Ground Truth (siehe 6.1).

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

Die Strukturerkennung verbindet **Docling**[^7] mit einem nachgeschalteten Korrekturschritt durch Gemini. Docling liefert dabei allein die Seitenstruktur, nicht den Text. Der Korrekturschritt prüft, ergänzt oder erkennt das Layout neu und bemisst den Aufwand pro Seite an einem abgeleiteten Qualitätsmaß, sodass die aufwendige Neudetektion nur dort greift, wo die erste Erkennung schwach blieb. Beide Layoutfassungen, die ursprüngliche und die korrigierte, bleiben erhalten, damit nachvollziehbar bleibt, welche Region von Docling und welche von Gemini stammt.

### **Austauschformate**

Aus dem Layout- und dem OCR-Datenstrom werden zusätzlich PAGE-XML[^8] und ein METS-Manifest[^9] erzeugt, Austauschformate für externe Bearbeitungs- und Archivsysteme. Sie entstehen aus denselben Quellen wie das TEI, ohne dessen Vorstufe zu sein, denn das TEI wird unmittelbar aus Layout und Text gebildet.

### **TEI-Erzeugung**

Die TEI-Erzeugung verbindet regelbasierte und sprachmodellgestützte Arbeit. Zunächst entsteht aus dem OCR- und dem Layout-Datenstrom ein deterministisches Grundgerüst. Textabschnitte werden den Layoutregionen nach ihrer Position zugeordnet, in Überschriften, Absätze, Fußnoten und vergleichbare Strukturen übersetzt und mit Seiten- und Zeilenmarken versehen. Dabei werden auch die typografischen Vereinheitlichungen gemäß den Editionsrichtlinien sowie die Auflösung getrennter Wörter berücksichtigt. Auf dieses Gerüst setzt ein verfeinernder Schritt auf, der das Seitenbild zusammen mit dem Gerüst und dem erkannten Text einem multimodalen Modell vorlegt und so eine strukturell angereicherte Fassung erzeugt. Da modellgenerierte Auszeichnung systematische Eigenheiten aufweist, schließt sich eine korrigierende Nachbearbeitung an, die häufige Struktur- und Schemaverstöße automatisch bereinigt. In der abschließenden Zusammenführung werden die Einzelseiten zu einem Gesamtdokument verbunden, seitenweise entstandene Gliederungseinheiten zusammengezogen und ein zweiter Satz dokumentweiter Korrekturen angewandt.

### **Validierung**

Das erzeugte TEI wird zweistufig geprüft, zum einen gegen das projektspezifische RelaxNG-Schema `zbz_hersch.rng`, das auf dem DTA-Basisformat aufbaut und um die verbindlichen ZBZ-Editionsrichtlinien ergänzt ist, zum anderen gegen projekteigene Regeln, die strukturelle Mindestanforderungen blockierend durchsetzen. Ergänzend markieren informative Hinweise prüfenswerte Stellen, ohne die Gültigkeit zu blockieren. Die quantitativen Validierungsergebnisse stehen in 6.1.

### **Bearbeitungsstatus statt Selbstzertifizierung**

Ursprünglich war als Abschluss ein agentenbasiertes Quality-Screening vorgesehen. Es wurde bewusst abgeschafft, weil kein einziger seiner Freigabe-Status von einem Menschen stammte; der Agent zertifizierte sich selbst. An seine Stelle tritt ein menschgesetzter Workflow-Status pro Datenstrom. Für den OCR-, den Layout- und den TEI-Datenstrom gilt jeweils einer von vier Werten zwischen „unverifiziert" und „fertig". Der Status wird im Webinterface gesetzt, mit voller Provenienz in einem objektbezogenen Manifest gehalten und bei der Übergabe an die ZB in die Versionsbeschreibung des Dokuments übernommen. Hintergrund ist, dass die Pipeline alle drei Datenströme für jedes Dokument erzeugt, unabhängig von ihrer fachlichen Qualität. Der ehrliche Ausgangspunkt ist daher „vorhanden, aber fachlich noch nicht verifiziert".

## **5\. Webinterface und Kuration**

Das Webinterface ist ein im Browser laufendes, auf GitHub Pages gehostetes Werkzeug zur Überprüfung und Kuration der Pipeline-Ergebnisse ([https://chpollin.github.io/zbz-ocr-tei/](https://chpollin.github.io/zbz-ocr-tei/)). Den Kern bildet der Pipeline-Viewer (`docs/viewer.html`), eine Single-Page-App ohne Backend und ohne Build-Schritt, die ihre Inhalte aus dem in der Repository-Architektur beschriebenen Per-Seiten-Mirror lädt — einer pro Dokument und Seite vorab erzeugten Datenablage (aufbereiteter OCR-Text, Layout-Regionen und das aus dem finalen TEI herausgelöste Seiten-TEI), die das gesamte Korpus ohne Server bereitstellt. Der Viewer bildet eine Bild-Text-Synopse: Faksimile und zugehöriger Text stehen nebeneinander, sodass beide Seite für Seite verglichen werden können. Das Faksimile wird im Ansichtsmodus über *OpenSeadragon* dargestellt[^10] und erlaubt stufenloses Zoomen, Verschieben und Drehen, mit den erkannten Layout-Regionen als Overlay. Der Textbereich ist zwischen drei Quellen umschaltbar, dem aufbereiteten OCR-Rohtext, der gerenderten TEI-Fassung, also dem aus dem TEI-XML erzeugten formatierten Lesetext, und dem TEI-XML-Quelltext selbst. Leerseiten erkennt der Viewer vorab, bevorzugt am TEI-Marker `<pb type="blank"/>`, ersatzweise über eine Textregel auf dem OCR-Ergebnis, und kennzeichnet sie als solche, statt fehlerhafte Regionen oder OCR-Artefakte anzuzeigen.

Daneben stehen vier weitere, direkt aufrufbare Seiten:

- [Korpus-Übersicht](https://chpollin.github.io/zbz-ocr-tei/) — sortierbare Tabelle mit Workflow-Ampeln und Filtern über Strom und Status  
- [Methode](https://chpollin.github.io/zbz-ocr-tei/methode.html) — statische Seite mit Headline-CER, stratifizierten Werten, Literaturvergleich und Limitations  
- [About](https://chpollin.github.io/zbz-ocr-tei/about.html)  
- [Impressum](https://chpollin.github.io/zbz-ocr-tei/impressum.html)

Die **Kuration** ist in den Viewer integriert und kommt ohne separaten Server aus: Der Browser hält keinen Server-Zustand und schreibt nichts automatisch ins Repository zurück; Änderungen verbleiben lokal und werden entweder als Datei-Download exportiert oder, in Chromium, über die File System Access API direkt in den Working Tree geschrieben (siehe unten). Layout und Text tragen je einen eigenen, unabhängigen Bearbeitungsschalter. Beim Wechsel in den Layout-Editor löst die Faksimile-Anzeige OpenSeadragon durch eine einfache, bearbeitbare Overlay-Ebene ab; darin lassen sich Regionen-Boxen auswählen, verschieben, skalieren, neu aufziehen und löschen, ihr Typ ändern und ihre Lesereihenfolge per Ziehen ordnen. Die Boxen werden als bildrelative Prozentkoordinaten (0–100, bezogen auf die in der Layout-Analyse festgehaltenen Seitendimensionen) geführt, sodass sie zoom- und auflösungsunabhängig deckungsgleich auf Faksimile und Overlay liegen; der Editor korrigiert die von der maschinellen Layout-Analyse vorgeschlagenen Boxen und setzt ihre fachliche Richtigkeit gerade nicht voraus.

Der **Transkriptions-Editor** schaltet die jeweils angezeigte Textquelle auf direkt editierbar, wobei strukturelle Eingriffe dem XML-Modus vorbehalten sind, da die gerenderte Ansicht beim Editieren nur den Text und nicht die Auszeichnung zurückgibt. Die Persistenz erfolgt als Datei-Download oder, in Chromium, als Direkt-Schreiben in den Working Tree über die File System Access API: Editierte Layout-JSONs, Transkriptionen oder das Objekt-Manifest — die Pro-Dokument-JSON, die Workflow-Status und Leerseiten je Datenstrom hält — werden abgelegt, woraus ein erneuter Pipeline-Lauf (`--reassemble`) das TEI regeneriert; nur Seiten mit neuer Kuration durchlaufen das Gemini-Refinement erneut, und wortgenaue Textänderungen schreibt der XML-Modus direkt in das finale TEI. Dieser bewusst server-lose Schnitt verlagert das Zurückschreiben auf die bearbeitende Person; er vermeidet Backend-Betrieb und Mehrnutzer-Konflikte, erfordert aber den manuellen Round-Trip aus Download, Ablage und Re-Lauf. (Ausblick: Dieser Round-Trip ließe sich künftig über die GitHub-Plattform schließen, etwa indem ein Commit der exportierten Datei einen GitHub-Actions-Lauf auslöst, der `--reassemble` ausführt und das regenerierte TEI samt Mirror zurückschreibt.) Jeder Datenstrom trägt einen Status mit vier Stufen (unverifiziert, in Arbeit, bearbeitet, fertig), der im Viewer per Klick weitergeschaltet wird und sich in den Ampeln der Korpus-Übersicht spiegelt; das erste Aktivieren eines Bearbeitungsschalters setzt den betroffenen Strom automatisch von unverifiziert auf in Arbeit, und solange Änderungen nicht heruntergeladen sind, warnt das Interface beim Verlassen der Seite. Der leitende Gedanke ist, dass die Edition selbst zum Kurationswerkzeug wird: Die Editorinnen und Editoren arbeiten direkt in der Edition, lernen dabei mehr über die Texte und bessern die Fehler der Pipeline aus.

Ergänzend wurden 79 sichere Leerseiten in 15 Dokumenten erkannt und als `<pb type="blank"/>` in die finalen TEI projiziert. Als sicher gilt eine Seite nur, wenn zwei unabhängige Signale übereinstimmen: Der OCR-Text ist praktisch leer (höchstens fünf Zeichen, kein alphanumerisches Zeichen oder lediglich ein „Blank Page"-Marker) und die Docling-Layout-Analyse findet null Regionen. Nur bei Übereinstimmung wird der Marker gesetzt; widersprechen sich die Signale — Text leer, aber Docling erkennt Regionen —, wird die Seite zum manuellen Review markiert statt projiziert (im aktuellen Korpus trat kein solcher Konflikt auf). Ein geplantes Export-Modul auf JSZip-Basis soll Per-Dokument- und Bulk-Export der Datenströme als ZIP erlauben (zum Berichtszeitpunkt noch nicht im Code eingebunden).

## **6\. Qualität und methodologische Einordnung**

### **6.1 Quantitative Textqualität**

Die Qualitätsbeurteilung der Textschicht ruht auf einer quantitativen Evaluation der End-to-End-Character-Error-Rate, gemessen als Pipeline-TEI gegen die manuell über Transkribus erstellten ZBZ-Referenz-TEIs. Eine zentrale Einsicht prägt die Messung: Die Referenz-TEIs sind selektive Teiltranskriptionen, während die Pipeline vielerorts vollständiger ist, sodass eine naive Volltext-CER diese Vollständigkeit fälschlich als Fehler zählte. Die CER wird daher in zwei Anteile zerlegt, eine Fidelity-CER für echte Fehler (Substitutionen, kleine Ein- und Auslassungen sowie alle größeren Auslassungen) und eine Scope-Rate für großen Pipeline-Mehrtext gegenüber der Referenz, der kein Fehler ist. Maßgeblich ist die Fidelity-CER über alle 25 Referenzdokumente mit einem Mean von 4,26 % (95-%-CI \[2,39 %; 6,48 %\]) und einem Median von 1,83 %; nach den Transkribus-Qualitätsbändern (unter 2 % exzellent, 2–5 % gut) ist der Median exzellent, der Mean gut. Ein Paired-Test gegen die reine Mistral-OCR ergibt einen Pipeline-Mehrwert von −7,90 Prozentpunkten, der bei n \= 25 jedoch nicht signifikant ist (p \= 0,07); die frühere Angabe von −14,83 Prozentpunkten (p \= 0,0004) war ein Artefakt des getrimmten Vergleichs und ist zurückgezogen. Alle Werte rechnen über alle 25 Referenzen; eine frühere scope-bereinigte Subset-Auswahl (n \= 19) wurde entfernt, da sie keinem reproduzierbaren Kriterium folgte. Die Erhaltungsrate diakritischer Zeichen liegt bei rund 99 %.

Methodisch werden BCa-Bootstrap-Konfidenzintervalle verwendet, die bei kleiner und schiefer Stichprobe genauer sind als normalverteilungsbasierte Intervalle, mit festem Seed zur Reproduzierbarkeit, dazu ein Paired-Bootstrap für den Vergleich End-to-End gegen OCR-only und eine Selektionsbias-Diagnostik (Chi-Square, Kolmogorov-Smirnov). Die Aggregation erfolgt auf Dokument-Ebene, der Vergleich case-sensitiv und mit globaler Volltext-Levenshtein-Distanz ohne deflationäres Alignment-Trimming. Goldene Regressionstests (`tests/test_cer_extraction.py`, 18 Tests) sichern den Berechnungsvertrag, und die Konformität wurde extern gegen OCR-D, dinglehopper, Transkribus, jiwer und Singh 2025 geprüft.

Zur Einordnung dienen zwei aus der Vergleichsliteratur übernommene Werte, Transkribus allein mit 3,67 % und Gemini 2.5 Pro zero-shot mit 3,36 %.[^11] Der eigene Fidelity-Median von 1,83 % liegt im Bereich des State of the Art für historischen Druck und unterschreitet beide Vergleichswerte. Für die übrigen Dokumente ohne Ground Truth dient ein Proxy auf Basis der Dictionary Hit Rate als Plausibilitätsschranke (Median 97,7 %).

### **6.2 Methodologische Verortung und die Selbstanwendung des Audit-Prinzips**

Der Bericht verwendet *epistemische Infrastruktur* als Arbeitsbegriff. Er bezeichnet die Gesamtheit der Strukturen, die ein LLM-gestützter, generativer Erzeugungsprozess um sich herum aufbaut, um seine Ergebnisse nachvollziehbar, überprüfbar und stabil zu halten. Wo Transkription, Layout und TEI nicht-deterministisch entstehen, treten an die Stelle des verlässlichen Einzelschritts verlässliche Strukturen, die jeden Stand dokumentieren, versionieren und gegen frühere Stände wie gegen formale Maße prüfbar machen. Im vorliegenden Projekt umfasst diese Infrastruktur das versionierte GitHub-Repository mit seiner Commit-Historie als lückenlose Erzeugungsspur, das Repository als geordnete Ablage von Code und Daten, die `pytest`\-Suiten als ausführbare Verifikation, das chronologische Arbeitstagebuch `journal.md`, die kuratierten Dokumente im `knowledge/`\-Ordner, das Webinterface samt Viewer als Werkzeug der menschlichen Inspektion und Kuration sowie die Character Error Rate als formale Metrik, die die Textqualität gegen die Ground Truth messbar macht. Diese Strukturen tragen nicht zum Ergebnis selbst bei, sondern zu der Gewissheit, mit der sich über das Ergebnis urteilen lässt.

Die Verifikations-Milestones liegen bewusst in etablierten Datenformaten vor (PNG, JSON, PAGE-XML, TEI-XML), sodass sie für menschliche wie maschinelle Prüfung zugänglich und mit anderen Systemen interoperabel sind; multimodale Agents können sich Overlay-Bilder und Dokumente eigenständig ansehen. Die Ablösung des selbstzertifizierenden Agent-Screenings durch menschgesetzte Stromstatus markiert die Grenze maschineller Verifikation explizit. Agents prüfen Konsistenz und Schemata, fachliche Richtigkeit garantiert erst die menschliche Kuration; das Status-Modell macht diesen Übergang im Datenmodell sichtbar, statt ihn hinter einem irreführenden „APPROVED" zu verbergen.

Methodologisch lässt sich das Projekt zwischen *Agentic Engineering*, *Agentic Coding* und *Promptotyping* verorten. Die Bezeichnung *Vibe Coding* trifft nicht zu, da das Vorgehen strukturiert war. Alle Python-Skripte sind mit Claude Code generiert, keines wurde manuell geschrieben oder im Detail inspiziert; die Validierung erfolgte am Endergebnis. Nicht explizit vorgegebene Entscheidungen wie der Chunking-Mechanismus für große PDFs wurden eigenständig getroffen und dokumentiert.

Eine Lehre dieser Iteration betrifft die Infrastruktur selbst. Die Verifikationskaskade, die das Projekt auf die Pipeline-Ergebnisse anwendet, muss auch auf die eigenen Metadaten angewendet werden. Die Korpus-Kennzahlen lebten lange als handgepflegte Prosa in der Knowledge-Base und drifteten, vor allem durch unbemerkte Vermischung der Zähl-Einheiten (Text-Ebene, PDF-Ebene, Seiten). Für diesen Bericht wurden sie aus den Primärquellen neu abgeleitet und in ein reproduzierbares Audit-Artefakt überführt (`scripts/eval/corpus_audit.py` mit Ausgabe nach `output/corpus_audit.json`), das jede Zahl an ein Tripel aus Quelle, Einheit und Extraktion bindet und Abweichungen zur Knowledge-Base automatisch flaggt. Die Drift der eigenen Metadaten verletzte damit genau das Prinzip deterministischer Ableitung, das das Projekt für seine Editionsdaten beansprucht.

### **6.3 Grenzen und mögliche Weiterführung**

Mehrere Aspekte sind unvollständig geblieben oder bewusst nicht bearbeitet worden. Die folgende Liste fasst beide zusammen, von Schwächen des Vorhandenen bis zu Schritten, die ein Anschlussvorhaben unternehmen könnte.

- Die semantische Anreicherung über Named Entity Recognition und Named Entity Linking, also die Erkennung von Personen, Orten und Organisationen und ihre Verknüpfung mit Normdaten wie GND und Wikidata, wurde nicht durchgeführt und ist nicht Gegenstand dieses Berichts. Sie wäre ein naheliegender nächster Schritt.  
- Die Layout-Analyse liefert bei Doppelseiten und komplexen Strukturen fehlerhafte Ergebnisse, ist aber durch zusätzliche Gemini-Calls erweiterbar.  
- Die Run-zu-Run-Stabilität der nicht-deterministischen LLM-Stufen ist nicht quantifiziert.  
- Der Proxy auf Basis der Dictionary Hit Rate generalisiert statistisch nicht (LOOCV-R² unter 0).  
- Auf der Datenseite bleiben extern zu klären die drei nicht gelieferten Texte (1745, 1750, 1970), das gelieferte PDF ohne finales TEI (10) sowie die Differenz zwischen den Masterfile-Texten und den öffentlich genannten ZB-Texten.  
- Der Header-Schema-Defekt im `<idno>` der finalen TEI ist registriert.  
- Der Round-Trip vom Viewer-Edit zurück in die Pipeline ist dokumentiert, aber nicht in einem Wrapper-Skript automatisiert; er beruht auf Konvention statt auf Mechanismus.

## **Anhang A: Skripte der Pipeline**

Aufruf jeweils als Modul (`python -m scripts.<paket>.<modul>`).

**Vom Scan zum Seitenbild**

- `scripts/edition/extract_pages.py` zerlegt die PDF-Scans seitenweise in PNG-Bilder, die zugleich als Faksimile und als Eingang für Texterkennung und Layout dienen.

**Texterkennung**

- `scripts/ocr/ocr_pipeline.py` steuert die Texterkennung mit Mistral als Basis oder optional Gemini-Vision-OCR (`-e gemini`).  
- `scripts/ocr/gemini_ocr_correct.py` liefert Ersatz- und Korrektur-OCR mit Gemini in zwei Varianten, nur aus Text oder zusätzlich mit dem Scan-Bild.  
- `scripts/ocr/llm_postprocess.py` korrigiert den OCR-Text optional mit Claude Haiku nach.  
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

- `scripts/eval/corpus_audit.py` leitet die Korpus-Kennzahlen reproduzierbar aus den Primärquellen ab und flaggt Abweichungen zur Knowledge-Base.

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

[^11]: Vergleichswerte aus der Literatur, nicht im Rahmen dieses Experiments gemessen. Transkribus Print M1 (allein), deutsch, 3,67 %: Crosilla, Klic und Colavizza 2025, arXiv:2503.15195. Gemini 2.5 Pro zero-shot, russisch (18. Jh.), 3,36 %: Levchenko 2025, arXiv:2510.06743.