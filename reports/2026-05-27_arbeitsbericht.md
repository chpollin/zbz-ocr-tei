Arbeitsbericht: LLM-gestützte OCR- und TEI-Pipeline für die digitale Edition der Schriften von Jeanne Hersch
Dr. Christopher Pollin, Digital Humanities Craft OG

v1. 27.05.2026 (WORK IN PROGRESS)
AI-Unterstützung: Claude Opus 4.7, Claude Code
1. Projektkontext und Zielsetzung
Dieser Bericht dokumentiert ein Experiment im Rahmen der digitalen Neuauflage der Schriften von Jeanne Hersch, einem Projekt der Zentralbibliothek Zürich (ZBZ).1 Herschs philosophisches Werk liegt mehrsprachig, überwiegend französisch und deutsch, und in verstreuter Überlieferung vor und macht damit Mehrsprachigkeit und heterogene Drucküberlieferung zu den beiden bestimmenden Anforderungen an die Pipeline. Parallel zum etablierten Workflow der ZBZ von der Digitalisierung zur digitalen Edition wurde derselbe Ablauf ein zweites Mal durchgeführt, vollständig gestützt auf Large Language Models (LLMs), agentenbasiert und werkzeuggestützt, mit der Frage, ob ein solcher Ansatz den etablierten Workflow in Textqualität und Aufwand erreicht.

Gegenstand des Experiments ist eine Pipeline, die ausgehend von PDF-Scans TEI-XML im DTA-Basisformat erzeugt und in einem zugehörigen Webinterface anzeigbar und kuratierbar macht. Das DTA-Basisformat ist ein TEI-Subset für die einheitliche Auszeichnung digitalisierter Drucktexte.2 Die Pipeline simuliert die Digitalisierung ausgehend von den PDFs, erzeugt Transkription, Layouterkennung und TEI-XML jedoch durchgängig über LLMs und Vision-Language Models (VLMs). Aus der Parallelführung zum etablierten Workflow stammt zugleich die spätere Vergleichsgrundlage, denn die 25 manuell über Transkribus erstellten Referenz-TEIs des etablierten Strangs dienen dem Experiment als Ground Truth.

Nahezu alle Verarbeitungsschritte laufen über LLMs, und Pipeline wie Webinterface entstehen durch Promptotyping, eine Context Engineering Arbeitsweise zur Erzeugung von Forschungsartefakten aus Forschungsdaten und Forschungskontexten.3 Die Codeerzeugung erfolgte vollständig innerhalb von Claude Code (Max-Subscription) mit den jeweils aktuellen Opus-Modellen (4.5 bis 4.7), über mehrere Sessions hinweg.4 Der gesamte Erzeugungsprozess ist über die Commit-Historie des offen vorliegenden Projektrepositorys nachvollziehbar.5

2. Datengrundlage
Am Beginn der Pipeline stehen zwei von der ZBZ gelieferte Bestandteile, die PDF-Scans der digitalisierten Texte und das Masterfile mit den zugehörigen Metadaten. Diese Lieferung bildet die Ausgangslage des Experiments; der katalogische Gesamtbestand und seine bibliothekarische Erschließung bleiben außer Betracht. Der folgende Abschnitt beschreibt zuerst das Masterfile als Metadatenquelle und dann den Umfang der gelieferten Scans.

Das Masterfile ist die Katalog- und Steuerungstabelle der ZBZ. Es enthält zwei Arten von Information. Die bibliografischen Stammdaten umfassen ID, MMSID, Gattung, Jahr, Titel, Seitenzahl, Signatur und Sprache. Die Workflow-Spalten halten den Bearbeitungsstand im ZB-Prozess fest, etwa digitalisiert, Kontrolle Metadaten, korrigiert und ausgezeichnet.

Das Experiment arbeitet ausschließlich mit den von der ZBZ gelieferten PDF-Scans.

Stand	Anzahl
gelieferte Dokumente	286
davon mit finalem TEI	285
physische Seiten	4.152
Die gelieferten Dokumente sind durchweg Drucktexte, handschriftliches Material ist nicht systematisch vertreten, sodass es sich um einen reinen OCR-Prozess handelt. Der Bestand erstreckt sich über die Jahre 1931 bis 1998, davon 168 Dokumente aus den Jahren 1970 bis 1989. Nach Dokumenttyp und Sprache verteilt er sich wie folgt.

Dokumenttyp	Anzahl	Anteil
Zeitschriftenartikel	146	51 %
Sammelbandbeiträge	116	41 %
Monografien	24	8 %
Sprache	Anzahl	Anteil
Französisch	203	71 %
Deutsch	72	25 %
Englisch	7	2 %
Italienisch	2	1 %
mehrsprachig fr/de	1	< 1 %
ohne Angabe	1	< 1 %
3. Repository-Architektur
Der Ordner knowledge/ ist ein Promptotyping Vault, eine an eine Obsidian-Forschungsvault angelehnte, mit Claude Opus in Claude Code erzeugte und kuratierte Wissensbasis in Markdown, die das Projektwissen abbildet und über den Projektverlauf iterativ wächst; einzelne Dokumente entstehen, wachsen oder werden zusammengeführt. Leitprinzip ist die Single Source of Truth, jeder Fakt steht in genau einem Dokument, auf das die übrigen verweisen. Hervorzuheben sind das chronologische Arbeitstagebuch journal.md als beschreibende Schicht neben der Git-Historie und das durchnummerierte Entscheidungsregister decisions.md.

Der Ordner data/ enthält Eingangs- und Referenzdaten und trennt dabei Geliefertes von projektseitig Erzeugtem. Unter data/source/ liegen die von der ZB gelieferten Startdaten, mit denen das Experiment beginnt, die PDF-Scans, die 25 manuell über Transkribus erstellten Referenz-TEIs (die Ground Truth der Evaluation), die zugehörigen Transkribus-PAGE-XML-Exporte, das Masterfile und die Editionsrichtlinien. Daneben stehen projektseitig erstellte Referenzdaten, das projektspezifische TEI-Schema schema/zbz_hersch.rng, die Entitäts-Indizes und die im Viewer kuratierten Editions-TEIs (curated_tei/). Die per LLM erzeugte Dokumentklassifikation ist in doc_metadata.json gespeichert, damit sie nicht bei jedem Pipeline-Lauf neu berechnet wird.

Der Ordner output/ enthält alle generierten Datenströme (OCR, Layout, PAGE-XML, TEI) und ist bewusst nicht versioniert. Der Ordner scripts/ enthält die Python-Pipeline, vollständig von Claude Code generiert und nach Domäne in Unterpakete gegliedert:

ocr — Texterkennung über Mistral Document AI, PDF-zu-PNG-Konvertierung
layout — Layout-Analyse mit Docling und Gemini-QA, PAGE-XML-Erzeugung
ner — Entitätserkennung und Verknüpfung mit Wikidata und GND
tei — vierstufige TEI-Erzeugung und Schema-Validierung
eval — CER-Messung, Bootstrap-Statistik und Proxy-Metriken
edition — Export, Objekt-Manifeste und Workflow-Status
core — geteilte Infrastruktur, daneben die Konfiguration config.py und die Hilfsfunktionen utils.py auf der Paketwurzel
Die Reproduzierbarkeit der Evaluation sichern die pytest-Suiten unter tests/, darunter die in Abschnitt 6.1 genannte Statistik-Library.

Der Ordner docs/ ist für GitHub Pages konfiguriert und enthält das Frontend, eine Kopie der Pipeline-Daten und die aus den PDFs erzeugten PNGs. Da GitHub Pages ohne Backend nur statische Dateien ausliefert, liegen die Editionsdaten dort als generierte Kopie unter docs/data/pages/{doc}/, die den Großteil der versionierten Dateien ausmacht. Editiert wird nicht diese Kopie, sondern das TEI unter output/tei_final/{doc}_final.xml, aus dem die Kopie nach jeder Änderung neu erzeugt wird (etwa nach einem erneuten Pipeline-Lauf oder einer im Viewer kuratierten und zurückgespielten Bearbeitung); ein Edit an der Kopie ginge beim nächsten Lauf verloren.

4. Die Pipeline
Die Pipeline überführt PDF-Scans in TEI-XML. Je Dokument entstehen drei Datenströme, ein OCR-Datenstrom mit dem erkannten Text, ein Layout-Datenstrom mit der Seitenstruktur und der daraus abgeleitete TEI-XML-Datenstrom mit der edierten Fassung.

Vom Scan zum Seitenbild
Zu Beginn werden die PDF-Scans seitenweise in Einzelbilder zerlegt, auf denen die nachfolgenden Stufen aufsetzen.

Texterkennung
Produktiv erfolgt die Texterkennung mit Mistral Document AI über Azure AI Foundry. Das Modell erfasst neben Fließtext auch Tabellen und Listen und liefert seitenweises Markdown; große Dokumente werden automatisch aufgeteilt, eine von Claude Code eigenständig getroffene Entscheidung. Steht dieser Zugang nicht zur Verfügung, kann ersatzweise ein multimodales Gemini-Modell dieselbe Aufgabe übernehmen, ohne dass sich für die Folgestufen etwas ändert. Eine optionale, sprachmodellgestützte Nachkorrektur ist verfügbar, aber nicht standardmäßig aktiv, weil sie bei bereits guter Ausgangsqualität keinen Mehrwert bringt; wo eine korrigierte Fassung vorliegt, wird sie der Rohfassung vorgezogen.

Layoutanalyse
Die Strukturerkennung verbindet Docling mit einem nachgeschalteten Korrekturschritt durch Gemini. Docling liefert dabei allein die Seitenstruktur, nicht den Text. Der Korrekturschritt prüft, ergänzt oder erkennt das Layout neu und bemisst den Aufwand pro Seite an einem abgeleiteten Qualitätsmaß, sodass die aufwendige Neudetektion nur dort greift, wo die erste Erkennung schwach blieb. Beide Layoutfassungen, die ursprüngliche und die korrigierte, bleiben erhalten, damit nachvollziehbar bleibt, welche Region von Docling und welche von Gemini stammt.

Austauschformate
Aus dem Layout- und dem OCR-Datenstrom wird zusätzlich PAGE-XML samt METS-Manifest erzeugt, ein Austauschformat im Transkribus-Standard für externe Bearbeitungs- und Archivsysteme. Es entsteht aus denselben Quellen wie das TEI, ist aber keine Vorstufe davon, denn das TEI wird unmittelbar aus Layout und Text gebildet.

Entitäten und Normdaten
Personen, Orte, Organisationen und weitere Entitätstypen werden seitenweise sprachmodellgestützt erkannt und über Schreibvarianten hinweg zu dokumentübergreifenden Registern zusammengeführt. Die Erkennung der Namen übernimmt dabei das Sprachmodell; die Verknüpfung mit Normdaten-Kennungen erfolgt dagegen ausschließlich deterministisch über Abfragen externer Normdaten- und Wissensdienste, niemals durch ein Sprachmodell. Im TEI-XML-Datenstrom werden Entitäten doppelt ausgezeichnet, mit einer externen Normdaten-Referenz und einer projektinternen Kennung, sodass sie sowohl im Bibliotheks- und Normdatenraum als auch innerhalb der Edition eindeutig adressierbar bleiben.

TEI-Erzeugung
Die TEI-Erzeugung verbindet regelbasierte und sprachmodellgestützte Arbeit. Zunächst entsteht aus dem OCR- und dem Layout-Datenstrom ein deterministisches Grundgerüst. Textabschnitte werden den Layoutregionen nach ihrer Position zugeordnet, in Überschriften, Absätze, Fußnoten und vergleichbare Strukturen übersetzt und mit Seiten- und Zeilenmarken versehen. Dabei werden auch die typografischen Vereinheitlichungen gemäß den Editionsrichtlinien sowie die Auflösung getrennter Wörter berücksichtigt. Auf dieses Gerüst setzt ein verfeinernder Schritt auf, der das Seitenbild zusammen mit dem Gerüst und dem erkannten Text einem multimodalen Modell vorlegt und so eine strukturell angereicherte Fassung erzeugt. Da modellgenerierte Auszeichnung systematische Eigenheiten aufweist, schließt sich eine korrigierende Nachbearbeitung an, die häufige Struktur- und Schemaverstöße automatisch bereinigt. In der abschließenden Zusammenführung werden die Einzelseiten zu einem Gesamtdokument verbunden, seitenweise entstandene Gliederungseinheiten zusammengezogen und ein zweiter Satz dokumentweiter Korrekturen angewandt. Die Verarbeitung ist durchgängig defensiv ausgelegt, sodass eine fehlschlagende Einzelkorrektur die Eingabe unverändert weiterreicht, statt den Lauf abzubrechen.

Validierung
Das erzeugte TEI wird zweistufig geprüft, zum einen gegen das projektspezifische RelaxNG-Schema (zbz_hersch.rng), das auf dem DTA-Basisformat aufbaut und um die verbindlichen ZBZ-Editionsrichtlinien ergänzt ist, zum anderen gegen projekteigene Regeln, die strukturelle Mindestanforderungen blockierend durchsetzen. Ergänzend markieren informative Hinweise prüfenswerte Stellen, ohne die Gültigkeit zu blockieren. Die quantitativen Validierungsergebnisse stehen im Abschnitt zur Qualitätsevaluation. Zu unterscheiden ist dabei die finale, ausgelieferte Editionsablage als verbindliche Quelle der Edition von der daraus erzeugten Anzeige-Kopie des Webinterfaces, die nicht direkt bearbeitet wird.

Bearbeitungsstatus statt Selbstzertifizierung
Ursprünglich war als Abschluss ein agentenbasiertes Quality-Screening vorgesehen. Es wurde bewusst abgeschafft, weil kein einziger seiner Freigabe-Status von einem Menschen stammte. Der Agent zertifizierte sich selbst. An seine Stelle tritt ein menschgesetzter Workflow-Status pro Datenstrom. Für den OCR-, den Layout- und den TEI-XML-Datenstrom gilt jeweils einer von vier Werten zwischen „unverifiziert" und „fertig". Der Status wird im Webinterface gesetzt, mit voller Provenienz in einem objektbezogenen Manifest gehalten und bei der Übergabe an die ZB in die Versionsbeschreibung des Dokuments übernommen. Hintergrund ist, dass die Pipeline alle drei Datenströme für jedes Dokument deterministisch produziert; der ehrliche Ausgangspunkt ist daher „vorhanden, aber fachlich noch nicht verifiziert", nicht eine maschinelle Freigabe.

Skripte
Die zu den obigen Schritten gehörenden Skripte, Aufruf jeweils als Modul (python -m scripts.<paket>.<modul>).

Vom Scan zum Seitenbild

scripts/edition/extract_pages.py zerlegt die PDF-Scans seitenweise in PNG-Bilder, die zugleich als Faksimile und als Eingang für Texterkennung und Layout dienen.
Texterkennung

scripts/ocr/ocr_pipeline.py steuert die Texterkennung und ruft je nach Dokumenttyp Mistral, Docling oder Gemini auf.
scripts/ocr/gemini_ocr_correct.py liefert Ersatz- und Korrektur-OCR mit Gemini in zwei Varianten, nur aus Text oder zusätzlich mit dem Scan-Bild.
scripts/ocr/llm_postprocess.py korrigiert den OCR-Text optional mit Claude Haiku nach.
scripts/ocr/ocr_dedup.py entfernt OCR-Halluzinationen wie Wiederholungs-Loops und Zeichen-Artefakte.
scripts/ocr/classify_docs.py bestimmt aus den ersten Seiten per Gemini die Dokument-Metadaten wie Sprache, Typ, Titel, Autor und Datum.
scripts/core/loaders.py legt fest, welcher OCR-Datenstrom Vorrang hat, und ermittelt die zu verarbeitenden Seiten.
Layoutanalyse

scripts/layout/run_layout_analysis.py führt Docling lokal auf den Seitenbildern aus und schreibt pro Seite ein Layout-JSON.
scripts/layout/run_layout_cloud.py erbringt dieselbe Layout-Analyse über eine docling-serve-Instanz statt lokal.
scripts/layout/layout_qa_gemini.py korrigiert das Layout (QA), erkennt es neu (Detect) oder entscheidet je Seite automatisch zwischen beidem (Auto), jeweils mit Gemini.
scripts/layout/generate_layout_overlays.py zeichnet die erkannten Regionen zur visuellen Kontrolle auf die Scans, auf Wunsch als Docling-gegen-Gemini-Vergleich.
Austauschformate

scripts/layout/page_xml_generator.py erzeugt aus Layout-JSON und OCR-Markdown PAGE-XML im Transkribus-Schema (2013-07-15).
scripts/layout/mets_generator.py erzeugt das zugehörige METS-Manifest und wird vom PAGE-XML-Generator mitaufgerufen.
Entitäten und Normdaten

scripts/ner/ner_extract.py erkennt mit Gemini je Seite die Named Entities und legt sie pro Seite und je Dokument ab.
scripts/ner/entity_store.py fasst die Seitentreffer zu einem deduplizierten Register pro Dokument zusammen.
scripts/ner/entity_index.py führt die Dokument-Register zum korpusweiten Index zusammen, vergibt projektinterne Kennungen und hält die Wikidata-Zuordnung.
scripts/ner/wikidata_linker.py gleicht die Entitäten rein deterministisch über die Wikidata-API ab, ohne Sprachmodell.
scripts/ner/ner_inject_tei.py schreibt die erkannten und verknüpften Entitäten als Auszeichnung in das TEI.
TEI-Erzeugung

scripts/tei/tei_unified.py orchestriert die vier TEI-Stufen, also Grundgerüst, Verfeinerung, Zusammenführung und Validierung.
scripts/tei/tei_step1.py baut das regelbasierte, deterministische TEI-Grundgerüst aus Text und Layout.
scripts/tei/tei_step2.py verfeinert das Gerüst multimodal mit Gemini und bereinigt anschließend häufige Modellfehler.
scripts/tei/tei_step3.py fügt die Seitenfragmente zum Gesamtdokument zusammen, also Header, Faksimile und Body, und wendet dokumentweite Korrekturen an.
scripts/tei/tei_generator.py, scripts/tei/tei_mapping_prompt.py und scripts/tei/tei_xml_utils.py liefern geteilte Bausteine, nämlich die Markdown-zu-TEI-Konvertierung, die Mapping-Tabelle für den Gemini-Prompt und die XML-Hilfsfunktionen.
Validierung

scripts/tei/tei_validator.py validiert gegen das RelaxNG-Schema und die Projektregeln und meldet zusätzlich informative Warnungen.
Bearbeitungsstatus

scripts/edition/page_manifest.py erzeugt je Objekt das Manifest mit Workflow-Status und Bearbeitungs-History pro Datenstrom und markiert sichere Leerseiten.
scripts/tei/tei_status_marker.py projiziert die Bearbeitungs-History bei der ZB-Übergabe als <change> in die Versionsbeschreibung und entfernt dabei die irreführenden Agent-Screening-Einträge.
scripts/tei/tei_blank_marker.py überträgt die erkannten Leerseiten als <pb type="blank"/> in das finale TEI.
5. Webinterface und Kuration
Das Webinterface ist als epistemische Infrastruktur angelegt, ein im Browser laufendes, auf GitHub Pages gehostetes Werkzeug zur Überprüfung und Validierung der Pipeline-Ergebnisse. Den Kern bildet der Pipeline-Viewer (docs/viewer.html), eine Single-Page-App ohne Backend. Er stellt das Faksimile dem OCR- und dem TEI-Ergebnis gegenüber, zeigt die erkannten Layout-Regionen als Overlay und annotierte Entitäten mit Verlinkungen zu Wikidata und GND. Das Faksimile wird über OpenSeadragon gerendert (Pan, Zoom, Rotate). Daneben stehen eine Korpus-Übersicht mit sortierbarer Tabelle, Workflow-Ampeln und Filter über Strom und Status, eine statische Methode-Seite mit Headline-CER, stratifizierten Werten, Literatur-Vergleich und Limitations, eine About-Seite und ein Impressum. Über einen Per-Seiten-Mirror sind Layout-, OCR- und TEI-Daten für alle 285 Dokumente auf GitHub Pages verfügbar, nur die Faksimile-Bilder bleiben außerhalb einiger Demo-Dokumente lokal. Diese Verifikations-Milestones sind nicht nur für menschliche Reviewer gebaut, sondern auch für multimodale Agents, die sich Overlay-Bilder und Dokumente eigenständig ansehen können.

Die Kuration ist in den Viewer integriert, ohne separaten Server. Jedes Panel trägt einen eigenen Edit-Toggle für Layout und für Text. Im Layout-Editor lassen sich Regionen-Boxen verschieben, skalieren, hinzufügen, löschen und in der Lesereihenfolge per Drag ordnen, im Transkriptions-Editor lässt sich der Text direkt bearbeiten, formatieren und mit Entitäten aus dem internen Register annotieren; eine RelaxNG-Validierung ist im Browser möglich. Die Persistenz erfolgt ausschließlich als Datei-Download, editierte Layout-JSONs, Transkriptionen oder das Objekt-Manifest werden heruntergeladen und manuell im Repository abgelegt, ein erneuter Pipeline-Lauf (--reassemble) regeneriert daraus das TEI. Das erste Aktivieren eines Edit-Toggles setzt den zugehörigen Strom automatisch von unverifiziert auf in_arbeit. Der leitende Gedanke ist, dass die Edition selbst zum Kurationswerkzeug wird; die Editorinnen und Editoren arbeiten direkt in der Edition, lernen dabei mehr über die Texte und bessern die Fehler der Pipeline aus. Ergänzend wurden 79 sichere Leerseiten in 15 Dokumenten cross-validiert erkannt (OCR-Regel plus Docling-Gegensignal) und als <pb type="blank"/> in die finalen TEI projiziert; ein Export-Modul auf JSZip-Basis erlaubt Per-Dokument- und Bulk-Export der Datenströme als ZIP.

6. Qualität und methodologische Einordnung
6.1 Quantitative Textqualität
Die Qualitätsbeurteilung der Textschicht ruht auf einer quantitativen Evaluation der End-to-End Character Error Rate, gemessen als Pipeline-TEI gegen die 25 manuell über Transkribus erstellten ZBZ-Referenz-TEIs. Die zentralen Werte sind ein Mean von 4,10 % (95 %-CI [2,01 %; 6,75 %]) und ein Median von 1,83 % (95 %-CI [0,84 %; 5,14 %]) bei n = 19 nach Scope-Bereinigung. Gegenüber roher Mistral-OCR (Mean 18,93 %) verbessert die Pipeline die CER im Paired-Test um 14,83 Prozentpunkte (p = 0,0004); die Stufen Layout-QA, TEI-Generierung und Post-Processing liefern also messbaren Mehrwert. Die Erhaltungsrate diakritischer Zeichen liegt bei rund 99 %.

Methodisch werden BCa-Bootstrap-Konfidenzintervalle (B = 10.000, fester Seed) verwendet, dazu ein Paired-Bootstrap für den Vergleich End-to-End gegen OCR-only und eine Selektionsbias-Diagnostik (Chi-Square, KS). Die Aggregation erfolgt auf Dokument-Ebene, ein content-aligned Vergleich macht die Messung immun gegen Seitennummerierungs-Drift. Eine Statistik-Library mit 55 Unit-Tests sichert die Reproduzierbarkeit. Zur Einordnung dienen zwei Werte aus der Vergleichsliteratur, die nicht selbst gemessen, sondern übernommen sind, Transkribus allein mit 3,67 % und Gemini 2.5 Pro zero-shot mit 3,36 %.6 Der eigene Median von 1,83 % liegt im Bereich des State of the Art für historischen Druck und unterschreitet beide Vergleichswerte. Für die übrigen Dokumente ohne Ground Truth dient ein Proxy auf Basis der Dictionary Hit Rate als Plausibilitätsschranke (Median 97,7 %).

6.2 Methodologische Verortung und die Selbstanwendung des Audit-Prinzips
Das Projekt lässt sich methodologisch zwischen Agentic Engineering, Agentic Coding und Promptotyping verorten. Die Bezeichnung Vibe Coding trifft nicht zu, da das Vorgehen strukturiert war. Das gesamte Projekt wurde mit Claude Code umgesetzt, alle 50 Python-Skripte sind generiert, keines wurde manuell geschrieben oder im Detail inspiziert, die Validierung erfolgte am Endergebnis. Nicht explizit vorgegebene Entscheidungen wie der Chunking-Mechanismus für große PDFs wurden eigenständig getroffen und dokumentiert.

Das Repository als Ganzes, Wissensordner, Promptotyping-Workflow, Skripte, Kontextwissen und Webinterfaces, ist eine epistemische Infrastruktur, die iterative Verifikation ermöglicht, für menschliche Akteure ebenso wie für die Agents. Die Verifikations-Milestones liegen bewusst in etablierten Datenformaten vor (PNG, JSON, PAGE-XML, TEI-XML), sodass sie für menschliche wie maschinelle Prüfung zugänglich und mit anderen Systemen interoperabel sind. Die Ablösung des selbstzertifizierenden Agent-Screenings durch menschgesetzte Stromstatus markiert die Grenze maschineller Verifikation explizit. Agents prüfen Konsistenz und Schemata, fachliche Richtigkeit garantiert erst die menschliche Kuration; das Status-Modell macht diesen Übergang im Datenmodell sichtbar, statt ihn hinter einem irreführenden „APPROVED" zu verbergen.

Eine Lehre dieser Iteration betrifft die Infrastruktur selbst. Das mehrstufige Prüfverfahren, das das Projekt auf die Pipeline-Ergebnisse anwendet, muss auch auf die eigenen Metadaten angewendet werden. Die Korpus-Kennzahlen wurden lange als handgepflegter Fließtext in der Knowledge-Base geführt und wichen mit der Zeit von den Primärquellen ab, vor allem durch unbemerkte Vermischung der Zähl-Einheiten (Text-Ebene, PDF-Ebene, Seiten). Für diesen Bericht wurden sie aus den Primärquellen neu abgeleitet und in ein reproduzierbares Audit-Artefakt überführt (scripts/eval/corpus_audit.py mit Ausgabe nach output/corpus_audit.json), das jede Zahl an ein Tripel aus Quelle, Einheit und Extraktion bindet und Abweichungen zur Knowledge-Base automatisch flaggt. Das Abweichen der eigenen Metadaten war damit eine Verletzung genau des Prinzips deterministischer Ableitung, das das Projekt für seine Editionsdaten beansprucht.

6.3 Grenzen und offene Punkte
Mehrere Aspekte bleiben offen. Die Layout-Analyse liefert bei Doppelseiten und komplexen Strukturen fehlerhafte Ergebnisse, ist aber durch zusätzliche Gemini-Calls erweiterbar. Die NER- und Wikidata-Verknüpfung ist explorativ und nicht mit Precision und Recall gemessen, der Verlinkungsgrad ist noch nicht gegen die Primärartefakte re-auditiert. Die Run-zu-Run-Stabilität der nicht-deterministischen LLM-Stufen ist nicht quantifiziert. Der Proxy auf Basis der Dictionary Hit Rate generalisiert statistisch nicht (LOOCV-R² unter 0). Auf der Datenseite bleiben die drei nicht gelieferten Texte (1745, 1750, 1970), das gelieferte PDF ohne finales TEI (10) und die Differenz zwischen 325 Masterfile-Texten und 314 öffentlich genannten ZB-Texten extern zu klären. Der aktuelle Header-Generator im Code erzeugt einen ärmeren teiHeader, als in den finalen TEI ausgeliefert wird, dort stehen unter anderem ein <idno type="docID"> und ein biblStruct, die der Generator nicht schreibt, sodass ein erneuter Pipeline-Lauf den reicheren Header regressieren würde; diese Divergenz ist registriert. Der Round-Trip vom Viewer-Edit zurück in die Pipeline ist dokumentiert, aber nicht in einem Wrapper-Skript automatisiert, er beruht auf Konvention statt auf Mechanismus.

7. Fazit
Das Experiment beantwortet seine Ausgangsfrage in zwei Richtungen. In Textqualität und Aufwand erreicht der LLM-gestützte Ansatz den etablierten Workflow und unterschreitet im Median dessen Referenzwerte; ein vollständiger Durchlauf von den PDF-Scans bis zum bearbeitbaren, schema-validen TEI-XML im DTA-Basisformat entstand in wenigen Wochen zu Kosten knapp über 100 USD, vollständig LLM-gestützt und agentenbasiert. In der fachlichen Freigabe erreicht der Ansatz den etablierten Workflow ausdrücklich nicht von selbst. Die Pipeline produziert vorhandene, aber unverifizierte Datenströme, deren editionsreife Qualität erst die menschliche Kuration herstellt. Genau diese Grenze macht das menschzentrierte Status-Modell sichtbar, statt sie zu verdecken. Das Experiment zeigt damit weniger einen Ersatz des etablierten Workflows als eine drastische Verschiebung des Aufwands, weg von der Erzeugung und hin zur fachlichen Prüfung.

Footnotes
Zentralbibliothek Zürich. „Jeanne Hersch: Digitale Neuauflage der Schriften". https://www.zb.uzh.ch/de/jeanne-hersch-digitale-neuauflage-der-schriften. ↩

Deutsches Textarchiv. „DTA-Basisformat". https://www.deutschestextarchiv.de/doku/basisformat. ↩

Pollin, Christopher. „Promptotyping: Zwischen Vibe Coding, Vibe Research und Context Engineering". L.I.S.A. WISSENSCHAFTSPORTAL GERDA HENKEL STIFTUNG, 17. Januar 2026. https://lisa.gerda-henkel-stiftung.de/digitale_geschichte_pollin. ↩

Claude Code, Dokumentation. https://code.claude.com/docs/en/overview. ↩

Repository: https://github.com/chpollin/zbz-ocr-tei. ↩

Vergleichswerte aus der Literatur, nicht im Rahmen dieses Experiments gemessen. Quelle vor Veröffentlichung zu ergänzen. ↩