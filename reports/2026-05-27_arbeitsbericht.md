---
type: bericht
created: 2026-05-27
snapshot_of: 3fbf6cdd
status: snapshot
zahlen_quelle: output/corpus_audit.json
---

> **Stand-Snapshot zu Commit `3fbf6cdd` (2026-05-27).** Geht bewusst irgendwann veraltet.
> Live-Korpuszahlen: `python -m scripts.eval.corpus_audit`. Laufendes Projektwissen: `knowledge/`.
> Alle Mengenangaben tragen ihre Zaehl-Einheit (Texte / PDFs / Seiten-physisch / Seiten-verarbeitet),
> weil die Vermischung dieser Einheiten die Hauptquelle frueherer Zahlen-Drift war.

# Arbeitsbericht: LLM-basierte OCR- und TEI-Pipeline für die digitale Neuauflage der Schriften von Jeanne Hersch

## Projektkontext und Datengrundlage

Die Zentralbibliothek Zürich (ZB) baut seit einigen Jahren den Forschungsservice „Digital Text Production" auf, dessen Ziel es ist, aus digitalisierten Beständen maschinenlesbare Texte nach TEI-Standard zu erzeugen und frei zugänglich zu machen. Die Entwicklung dieses Services wird anhand von zwei Pilotbeständen vorangetrieben, darunter das Teilprojekt „Jeanne Hersch: digitale Neuauflage der Schriften". Die bearbeiteten Texte sollen über sources-online.org veröffentlicht werden.

Jeanne Hersch (1910–2000) zählt zu den bedeutendsten Schweizer Philosophinnen des 20. Jahrhunderts. Neben Hannah Arendt war sie Meisterschülerin von Karl Jaspers, dessen Werk sie durch Übersetzungen ins Französische bekannt machte. Sie verstand sich nicht nur als Akademikerin, sondern auch als politische Publizistin und setzte sich wiederholt für Menschenrechte ein, unter anderem als Direktorin der Abteilung Philosophie der UNESCO (1966–1968, 1970–1972). Ihre Schriften sind fast ausschließlich in ihren Erstpublikationen verfügbar und wurden oft von Institutionen und Verlagen publiziert, die nicht mehr existieren. Nach Angaben der ZB umfasst die Edition rund 314 Texte verschiedener Gattungen.

Gegenstand dieses Arbeitsberichts ist die technische Umsetzung einer vollständig LLM-gestützten Pipeline, die ausgehend von PDF-Scans über mehrere Verarbeitungsstufen TEI-XML-Dokumente erzeugt, welche in einem Webinterface als digitale Edition angezeigt und von Editorinnen und Editoren weiterbearbeitet werden können.

### Das Masterfile: Katalog- und Steuerungstabelle der ZB

Ausgangs- und Steuerungsquelle des Projekts ist das von der ZB gepflegte **Masterfile** (`data/source/masterfile/Masterfile.xlsx`) — eine Tabelle, die den katalogisierten Bestand der Hersch-Edition führt und zugleich den Bearbeitungsfortschritt protokolliert. Pro Text enthält sie zwei Arten von Information:

- **Bibliografische Stammdaten** (autoritativ): interne `ID`, Bibliotheks-ID `MMSID` (swisscovery/Alma), Gattung (`PublForm`), `Jahr`, `Titel`, `Bibliografische Angaben`, `Anzahl Seiten`, `Signatur`, `Standort` und `Sprache`.
- **Workflow-Status der ZB**: `digitalisiert`, `Bestellstatus`, `Kontrolle Metadaten`, `Korrektur durch JHG`, `korrigiert (und retourniert)`, `ausgezeichnet`, `publiziert` sowie ein Freitextfeld `Anmerkungen` (etwa Hinweise auf Übersetzungen und Nachdrucke).

Das Masterfile ist damit die **verlässlichste Metadatenquelle** des Projekts: Titel, Jahr, Gattung und Sprache liegen hier in kuratierter Form vor, während sie in der Pipeline sonst nur als automatische Klassifikation (`doc_metadata.json`, Gemini) anfallen. Die `MMSID` ist dabei kein projektinterner Identifikator, sondern der Datensatz-Schlüssel im Bibliothekskatalog (Ex Libris Alma / swisscovery); sie dient als auflösbarer Anker zur Verknüpfung mit Bibliotheks- und Normdaten — allerdings nur dort, wo sie gesetzt ist: 211 der 286 gelieferten Dokumente (74 %) tragen eine MMSID, für die übrigen 75 fehlt dieser Anker (typischerweise Einzelartikel und Beiträge, die nicht als eigener Katalogdatensatz erschlossen sind). Die *interne*, lückenlose Identifikation aller 286 Dokumente leistet hingegen die fortlaufende `ID` der Masterfile, die in jedem erzeugten TEI als `<idno type="docID">` steht. Die fehlende MMSID ist damit keine Identifikations-, sondern eine Katalog-Verknüpfungslücke.

### Umfang des bearbeiteten Korpus

Das Masterfile katalogisiert den Gesamtbestand der Edition; für die Pipeline maßgeblich sind die **tatsächlich als PDF gelieferten Dokumente**. Alle folgenden Kennzahlen beziehen sich ausschließlich auf diese gelieferten Daten:

| Kennzahl | Anzahl | Quelle |
|---|---|---|
| gelieferte Dokumente (PDF) | **286** | `data/source/pdf/` |
| davon mit finalem TEI | **285** | `output/tei_final/` |

Ein geliefertes PDF (`10`) durchlief die Pipeline bislang nicht bis zum finalen TEI und bleibt als offener Verarbeitungspunkt vermerkt. Alle 286 gelieferten Dokumente sind im Masterfile katalogisiert; ihre Metadaten stehen damit vollständig zur Verfügung.

Der Seitenumfang wird auf drei Ebenen gemessen, die Verschiedenes bezeichnen und nicht vermischt werden dürfen:

| Definition | Anzahl | Einheit / Quelle |
|---|---|---|
| physischer Umfang | **4.152** | Seiten der 286 PDFs (`pypdfium2`) |
| OCR-verarbeitet | **4.117** | Per-Seite-Markdown (`output/mistral_results/`) |
| im finalen TEI | **4.115** | `<pb>`-Elemente in `output/tei_final/` |

Die Differenz von 35 Seiten zwischen physischem Umfang (4.152) und OCR-Verarbeitung (4.117) entspricht exakt dem noch nicht prozessierten PDF `10`; die verbleibenden zwei Seiten zwischen OCR und TEI stammen aus Seitengrenzen-Artefakten der TEI-Assembly (einzelne Seiten werden zusammengezogen oder geteilt).

### Gattungen, Sprachen, Zeitraum

Sämtliche Dokumente lagen als Drucktexte vor, handschriftliches Material war nicht systematisch vertreten — es handelte sich um einen reinen OCR-Prozess. Der bearbeitete Bestand erstreckt sich über **1931–1998** mit deutlichem Schwerpunkt in den 1970er/80er-Jahren (**168 der 286 Dokumente** in 1970–1989).

Gattungs- und Sprachverteilung sind hier **laut Masterfile für die 286 gelieferten Dokumente** angegeben:

| Gattung | Anzahl | Anteil |
|---|---|---|
| Zeitschriftenartikel | 146 | 51 % |
| Sammelbandbeiträge | 116 | 41 % |
| Monografien | 24 | 8 % |

| Sprache | Anzahl | Anteil |
|---|---|---|
| Französisch | 203 | 71 % |
| Deutsch | 72 | 25 % |
| Englisch | 7 | 2 % |
| Italienisch | 2 | <1 % |
| mehrsprachig fr/de | 1 | <1 % |
| ohne Angabe | 1 | <1 % |

Geminis automatische Klassifikation derselben 286 PDFs weicht erwartungsgemäß ab (etwa 149 Zeitschriftenartikel, 51 Bücher, 48 Sammelbandbeiträge sowie deutlich mehr mehrsprachig klassifizierte Dokumente), weil sie ein anderes Kategorienschema auf der PDF-Ebene anlegt. Für Metadaten bleibt das Masterfile die verlässlichere Quelle. Der hohe Französisch-Anteil hat konkrete Konsequenzen für die Pipeline: französische Typografie (Guillemets, Akzente, Ligaturen, Leerzeichen vor Interpunktion), französische Trennregeln und überwiegend französische Beispiele in den Prompts.

Der Arbeitszeitraum erstreckte sich von **Ende Januar bis Ende Mai 2026**, dokumentiert durch **178 Commits** (erster Commit 29.01.2026, letzter 26.05.2026; Schwerpunkt im März mit 110 Commits). Im April und Mai folgten die wissenschaftliche CER-Re-Evaluation, eine Frontend-Radikalkur und die Ablösung des agentenbasierten Screenings durch ein menschgesetztes Workflow-Status-Modell.

## Repository-Architektur

Das Projekt ist in einem öffentlichen GitHub-Repository organisiert, dessen Verzeichnisse die Eingangsdaten, den Code, die generierten Daten und das Frontend voneinander trennen.

Der Ordner `knowledge/` ist ein Promptotyping Vault, eine an eine Research-Obsidian-Vault angelehnte, KI-erzeugte und expertenkuratierte Wissensbasis in Markdown, die das gesamte Projektwissen möglichst kompakt, präzise und klar abbildet. Sie wird über den Projektverlauf iterativ weiterentwickelt; einzelne Dokumente entstehen, wachsen oder werden zusammengeführt. Leitprinzip ist die Single Source of Truth: Jeder Fakt steht in genau einem Dokument, auf das die übrigen verweisen. Hervorzuheben sind das chronologische Arbeitstagebuch `journal.md` als beschreibende Schicht neben der Git-Historie und das durchnummerierte Entscheidungsregister `decisions.md`.

Der Ordner `data/` enthält die Eingangs- und Referenzdaten. Unter `data/source/` liegen die von der ZB gelieferten Startdaten, mit denen das Experiment beginnt: die PDF-Scans (`pdf/`), die 25 manuell über Transkribus erstellten Referenz-TEIs (`reference_tei/`), die Transkribus-PAGE-XML-Exporte (`transkribus_page_xml/`), das Masterfile (`masterfile/`) und die Editionsrichtlinien (`guidelines/`). Daneben liegen projektseitig erstellte Referenzdaten: das projektspezifische TEI-Schema (`schema/zbz_hersch.rng`), die Entitäts-Indizes (`entities/`) und die kuratierten Gold-TEIs (`curated_tei/`); die generierte Dokumentklassifikation (`doc_metadata.json`) liegt als Cache bei.

Der Ordner `output/` enthält alle generierten Datenströme (OCR, Layout, PAGE-XML, TEI) und ist bewusst nicht versioniert. Der Ordner `scripts/` enthält die Python-Pipeline, 50 versionierte Dateien, nach Domäne in die Pakete `ocr`, `layout`, `ner`, `tei`, `eval`, `edition` und `core` gruppiert, ergänzt um die zentrale Konfiguration `config.py` und geteilte Hilfsfunktionen `utils.py`. Sämtlicher Code wurde von Claude Code generiert; kein Skript wurde manuell geschrieben oder im Detail inspiziert, geprüft wurde jeweils das Endergebnis.

Der Ordner `docs/` ist für GitHub Pages konfiguriert und enthält das Frontend, einen generierten Mirror der Pipeline-Daten und die aus den PDFs erzeugten PNGs. Der Mirror macht den Großteil der versionierten Dateien aus und ermöglicht das Backend-lose Hosting auf GitHub Pages. Eine zentrale Konvention strukturiert den Datenfluss: `output/tei_final/{doc}_final.xml` ist die Single Source of Truth der Edition, `docs/data/pages/{doc}/` ist ein generierter Mirror, der nie direkt editiert, sondern nach Änderungen an der Quelle neu erzeugt wird.

```
zbz-ocr-tei/
  knowledge/              Promptotyping Vault: iterativ kuratiertes Projektwissen (Markdown)
  data/                   Eingangs- und Referenzdaten
    source/               von der ZB gelieferte Startdaten
      pdf/                PDF-Scans
      reference_tei/      Referenz-TEIs (Transkribus)
      transkribus_page_xml/   Transkribus-PAGE-XML-Exporte
      masterfile/         Masterfile.xlsx (Metadaten + Steuerung)
      guidelines/         Editionsrichtlinien
    schema/               zbz_hersch.rng (TEI-Schema)
    entities/             Entitäts-Indizes (Person, Organisation, Ort, Werk)
    curated_tei/          kuratierte Gold-TEIs
    doc_metadata.json     generierte Dokumentklassifikation (Cache)
  scripts/                Python-Pipeline, nach Domäne gruppiert
    ocr/ layout/ ner/ tei/ eval/ edition/ core/
    config.py             zentrale Konfiguration
    utils.py              geteilte Hilfsfunktionen
  output/                 alle generierten Datenströme (nicht versioniert)
  docs/                   Frontend + generierter Mirror (GitHub Pages)
    *.html  css/  js/     Frontend
    data/                 generierter Mirror der Pipeline-Daten
    images/               aus PDFs erzeugte PNGs
  tests/                  pytest-Suites
  reports/                Arbeitsberichte
```

## Die Pipeline

Die Pipeline überführt PDF-Scans in TEI-XML. Sie ist dabei nicht als einzelne durchgehende Kette organisiert, sondern als Bündel paralleler Datenströme je Dokument: Aus jedem Objekt entstehen nebeneinander ein Textstrom, ein Layoutstrom und daraus abgeleitet ein TEI-Strom. Die zu verarbeitende Menge wird nicht aus einer zentralen Liste bezogen, sondern aus dem Vorhandensein der Texterkennungs-Dateien abgeleitet. Daraus folgt eine grundlegende Eigenschaft des Systems: Solange für ein Dokument keine vollständige Texterkennung vorliegt, ist es für die nachgelagerten Stufen nur in dem Umfang sichtbar, in dem Erkennungsergebnisse existieren.

### Vom Scan zum Seitenbild

Zu Beginn werden die PDF-Scans seitenweise in Einzelbilder zerlegt (`scripts/edition/extract_pages.py`). Diese Bilder sind die gemeinsame Grundlage aller weiteren Stufen.

### Texterkennung

Produktiv erfolgt die Texterkennung mit **Mistral Document AI** über **Azure AI Foundry**: Das Modell erfasst neben Fließtext auch Tabellen und Listen und liefert seitenweises Markdown; große Dokumente werden automatisch aufgeteilt — eine von Claude Code eigenständig getroffene Entscheidung. Steht dieser Zugang nicht zur Verfügung, kann ersatzweise ein multimodales **Gemini**-Modell dieselbe Aufgabe übernehmen; es schreibt sein Ergebnis in dasselbe Format und Verzeichnis, sodass die nachgelagerten Stufen unverändert weiterarbeiten. Eine optionale, sprachmodellgestützte Nachkorrektur ist verfügbar, aber nicht standardmäßig aktiv, weil sie bei bereits guter Ausgangsqualität keinen Mehrwert bringt. Liegt für eine Seite eine korrigierte Fassung vor, wird sie der Rohfassung automatisch vorgezogen.

### Layoutanalyse

Die Strukturerkennung verbindet **Docling** mit einem nachgeschalteten Korrekturschritt durch **Gemini**. Docling wird bewusst nur für das Layout eingesetzt, nicht für die Texterkennung. Der Korrekturschritt prüft, ergänzt oder erkennt das Layout neu und bemisst den Aufwand pro Seite an einem abgeleiteten Qualitätsmaß, sodass die aufwendige Neudetektion nur dort greift, wo die erste Erkennung schwach blieb. Beide Layoutfassungen — die ursprüngliche und die korrigierte — bleiben erhalten, damit die Herkunft der Daten nachvollziehbar bleibt.

### Austauschformate

Aus Layout und Text wird zusätzlich PAGE-XML samt METS erzeugt. Dieser Export ist kein Zwischenschritt der TEI-Erzeugung, sondern für externe Systeme bestimmt; das TEI leitet sich unabhängig davon direkt aus Layout und Text ab. Beide Formate gehen auf dieselben Quellen zurück, ohne voneinander abzuhängen.

### Entitäten und Normdaten

Personen, Orte, Organisationen und weitere Entitätstypen werden seitenweise sprachmodellgestützt erkannt und über Schreibvarianten hinweg zu dokumentübergreifenden Registern zusammengeführt. Methodisch ist eine Trennung festgelegt: Die Erkennung der Namen übernimmt das Sprachmodell, die Verknüpfung mit Normdaten-Kennungen erfolgt dagegen ausschließlich deterministisch über Abfragen externer Normdaten- und Wissensdienste, niemals durch ein Sprachmodell. Im TEI werden Entitäten doppelt ausgezeichnet — mit einer externen Normdaten-Referenz und einer projektinternen Kennung —, sodass sie sowohl im Bibliotheks- und Normdatenraum als auch innerhalb der Edition eindeutig adressierbar bleiben.

### TEI-Erzeugung

Die TEI-Erzeugung verbindet regelbasierte und sprachmodellgestützte Arbeit. Zunächst entsteht aus Text und Layout ein deterministisches Grundgerüst: Textabschnitte werden den Layoutregionen nach ihrer Position zugeordnet, in Überschriften, Absätze, Fußnoten und vergleichbare Strukturen übersetzt und mit Seiten- und Zeilenmarken versehen; dabei werden auch die typografischen Vereinheitlichungen gemäß den Editionsrichtlinien sowie die Auflösung getrennter Wörter berücksichtigt. Auf dieses Gerüst setzt ein verfeinernder Schritt auf, der das Seitenbild zusammen mit dem Gerüst und dem erkannten Text einem multimodalen Modell vorlegt und so eine strukturell angereicherte Fassung erzeugt. Da modellgenerierte Auszeichnung systematische Eigenheiten aufweist, schließt sich eine korrigierende Nachbearbeitung an, die häufige Struktur- und Schemaverstöße automatisch bereinigt. In der abschließenden Zusammenführung werden die Einzelseiten zu einem Gesamtdokument verbunden, seitenweise entstandene Gliederungseinheiten zusammengezogen und ein zweiter Satz dokumentweiter Korrekturen angewandt. Durchgängig ist die Verarbeitung defensiv ausgelegt: Schlägt eine einzelne Korrektur fehl, wird die Eingabe unverändert weitergereicht, statt den Lauf abzubrechen.

### Validierung

Das erzeugte TEI wird zweistufig geprüft. Zum einen gegen das projektspezifische, auf dem DTA-Basisformat aufbauende und um die verbindlichen ZBZ-Editionsrichtlinien ergänzte RelaxNG-Schema (`zbz_hersch.rng`); zum anderen gegen projekteigene Regeln, die strukturelle Mindestanforderungen blockierend durchsetzen. Ergänzend markieren informative Hinweise prüfenswerte Stellen, ohne die Gültigkeit zu blockieren. Die quantitativen Validierungsergebnisse werden im Abschnitt zur Qualitätsevaluation berichtet. Zu unterscheiden ist dabei die finale, ausgelieferte Editionsablage als verbindliche Quelle der Edition von dem daraus erzeugten Anzeige-Spiegel des Webinterfaces, der nicht direkt bearbeitet wird.

### Bearbeitungsstatus statt Selbstzertifizierung

Ursprünglich war als Abschluss ein agentenbasiertes Quality-Screening vorgesehen. Es wurde bewusst abgeschafft, weil kein einziger seiner Freigabe-Status von einem Menschen stammte — der Agent zertifizierte sich selbst. An seine Stelle tritt ein menschgesetzter Workflow-Status pro Datenstrom: Für Text, Layout und TEI gilt jeweils einer von vier Werten zwischen „unverifiziert" und „fertig". Der Status wird im Webinterface gesetzt, mit voller Provenienz in einem objektbezogenen Manifest gehalten und bei der Übergabe an die ZB in die Versionsbeschreibung des Dokuments übernommen. Das Modell folgt der Einsicht, dass die Pipeline Text, Layout und TEI für alle Dokumente deterministisch produziert — der ehrliche Ausgangspunkt ist daher „vorhanden, aber fachlich noch nicht verifiziert", nicht eine maschinelle Freigabe.

## Qualitätsevaluation

Die Qualitätsbeurteilung der Textschicht ruht auf einer wissenschaftlich fundierten, quantitativen Evaluation (End-to-End-CER, Pipeline-TEI gegen 25 manuell via Transkribus erstellte ZBZ-Referenz-TEIs):

- **End-to-End-CER: Mean 4,10 % (95 %-CI [2,01 %; 6,75 %]), Median 1,83 % ([0,84 %; 5,14 %])**, n = 19 (scope-bereinigt).
- Gegenüber roher Mistral-OCR (Mean 18,93 %) verbessert die Pipeline um **−14,83 pp im Paired-Test (p = 0,0004)**.
- Erhaltungsrate diakritischer Zeichen (HCPR) rund 99 %.

Methodisch: BCa-Bootstrap-CIs (B = 10.000, Seed = 42), Paired-Bootstrap, Selektionsbias-Diagnostik, content-aligned Vergleich (immun gegen Seitennummerierungs-Drift), 55 Unit-Tests. Der Median von 1,83 % liegt im Bereich des State of the Art für historischen Druck und übertrifft Transkribus allein (3,67 %) wie Gemini 2.5 Pro zero-shot (3,36 %). Für die übrigen Dokumente dient ein Dictionary-Hit-Rate-Proxy als Plausibilitätsschranke (Median 97,7 %). Die TEI-Schema-Validierung bestätigt 285/285 valide Dokumente. Ehrlich dokumentierte Grenzen: NER-Precision/Recall ungemessen, Run-zu-Run-Varianz des LLM-Non-Determinismus ungemessen, der Proxy generalisiert statistisch nicht.

## Webinterface als Verifikationsinstrument

Das als „epistemische Infrastruktur" verstandene Webinterface wurde im April radikal reduziert (von neun HTML-Seiten und 23 JS-Modulen auf eine schlanke Basis; frühere mehrseitige Lese-Edition mit Register, Diagnostik-Seite und CER-Dashboard ersatzlos abgeschafft). Den Kern bildet der **Pipeline-Viewer** (`docs/viewer.html`), eine Single-Page-App ohne Backend: Faksimile gegen OCR und TEI, Layout-Regionen als Overlay, annotierte Entitäten mit Wikidata-/GND-Links. Das Faksimile wird im Anzeige-Modus über **OpenSeadragon 5.0.1** gerendert (Pan/Zoom/Rotate). Daneben stehen eine Korpus-Übersicht mit Workflow-Ampeln, eine statische Methode-Seite, eine About-Seite und ein Impressum. Über einen Per-Seiten-Mirror sind Layout-, OCR- und TEI-Daten für alle 285 Dokumente auf GitHub Pages verfügbar; nur die Faksimile-Bilder bleiben außerhalb einiger Demo-Dokumente lokal.

## Curation: Die Edition als Bearbeitungswerkzeug

Der frühere FastAPI-Curation-Server wurde abgeschafft. An seine Stelle tritt ein in den Viewer integrierter Bearbeitungsmodus ohne Backend: pro Panel ein Edit-Toggle („Layout" / „Text"). Der Layout-Editor erlaubt Verschieben, Skalieren, Hinzufügen, Löschen und Reading-Order-Drag von Regionen; der Transkriptions-Editor das direkte Bearbeiten, Formatieren und Annotieren von Entitäten aus dem internen Register, mit RelaxNG-Validierung im Browser. Persistenz erfolgt ausschließlich als Datei-Download mit manueller Ablage und Pipeline-Re-Lauf (`--reassemble`). Das erste Aktivieren eines Edit-Toggles setzt den zugehörigen Strom automatisch auf `in_arbeit`. Der Gedanke: Die Edition selbst wird zum Kurationswerkzeug. Ergänzend wurden 79 sichere Leerseiten (15 Dokumente) cross-validiert erkannt und als `<pb type="blank"/>` markiert; ein JSZip-Export-Modul erlaubt Per-Dokument- und Bulk-Export.

## Methodologische Reflexion

### Einordnung

Das Projekt wurde vollständig mit Claude Code umgesetzt; alle 50 Python-Skripte sind generiert, keines manuell geschrieben oder im Detail inspiziert. „Vibe Coding" ist als Bezeichnung zu radikal; treffender ist eine Einordnung zwischen Agentic Engineering, Agentic Coding und Promptotyping. Nicht vorgegebene Entscheidungen (z. B. das PDF-Chunking) wurden eigenständig getroffen und dokumentiert.

### Epistemische Infrastruktur

Das Repository als Ganzes — Wissensordner, Promptotyping-Workflow, Skripte, Kontextwissen, Webinterfaces — ist eine epistemische Infrastruktur, die iterative Verifikation ermöglicht, für Menschen wie für Agents. Die Ablösung des selbstzertifizierenden Agent-Screenings durch menschgesetzte Stromstatus markiert die Grenze maschineller Verifikation explizit: Agents prüfen Konsistenz und Schemata, fachliche Richtigkeit garantiert erst die menschliche Kuration.

Eine wichtige Lehre dieser Iteration betrifft die Infrastruktur selbst: Die Verifikationskaskade, die das Projekt auf Pipeline-Ergebnisse anwendet, muss auch auf seine **eigenen Metadaten** angewendet werden. Die Korpus-Kennzahlen lebten lange als handgepflegte Prosa in der Knowledge-Base und drifteten — vor allem durch unbemerkte Vermischung der Zähl-Einheiten (Text-Ebene vs. PDF-Ebene vs. Seiten). Sie wurden für diesen Bericht aus den Primärquellen neu abgeleitet und in ein reproduzierbares Audit-Artefakt überführt (`scripts/eval/corpus_audit.py` → `output/corpus_audit.json`), das jede Zahl an ein Tripel (Quelle, Einheit, Extraktion) bindet und Abweichungen zur Knowledge-Base automatisch flaggt.

### Offene Punkte und Einschränkungen

Die Layout-Analyse liefert bei Doppelseiten und komplexen Strukturen Fehler (durch zusätzliche Gemini-Calls erweiterbar). Die NER/Wikidata-Verknüpfung ist explorativ und nicht mit Precision/Recall gemessen. Die Run-zu-Run-Stabilität der nicht-deterministischen LLM-Stufen ist nicht quantifiziert. Ein geliefertes PDF (`10`) hat noch kein finales TEI. Ein Header-Schema-Defekt (`<idno>` in `tei_final`) ist registriert. Der Round-Trip vom Viewer-Edit zurück in die Pipeline ist dokumentiert, aber nicht in einem Wrapper-Skript automatisiert.

Trotz dieser offenen Punkte demonstriert das Projekt, dass eine vollständige digitale Edition von PDF-Scans bis zum bearbeitbaren, schema-validen TEI-XML — inklusive quantitativ belegter Textqualität (Median-CER 1,83 %) und einem ehrlichen, menschzentrierten Qualitätsmodell — in wenigen Wochen erzeugt werden kann, wenn die gesamte Pipeline LLM-gestützt und agentenbasiert aufgebaut wird.
