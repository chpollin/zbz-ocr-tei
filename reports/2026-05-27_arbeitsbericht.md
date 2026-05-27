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

## Pipeline-Schritte

### Schritt 1: PDF-zu-PNG-Konvertierung

Die PDF-Scans werden mit `pypdfium2` in PNG-Bilder zerlegt (`scripts/edition/extract_pages.py`, 300 dpi) und unter `docs/images/` abgelegt — Grundlage aller weiteren Schritte.

### Schritt 2: OCR

**DeepSeek-OCR-2** (3B-VLM, lokal auf GPU, ~1,6 s/Seite) dient als Development-Engine für die Dokumenttypen A und C; produktiv wurde es wegen hoher GPU-Last und Spaltenproblemen nicht eingesetzt. Production-Engine ist **Mistral Document AI** (`mistral-document-ai-2512`) über **Azure AI Foundry**: erkennt neben Text auch Tabellen und Listen, liefert Per-Seite-Markdown (~1,3 s/Seite), chunkt große Dokumente automatisch (eine von Claude Code eigenständig getroffene Entscheidung).

Eine optionale OCR-Korrektur mit **Claude Haiku 4.5** lieferte inkonsistente Ergebnisse (bei guter Ausgangs-OCR mit CER < 5 % sogar leicht verschlechternd, gemessen +0,10 %) und ist daher optional, nicht Default. Für alle weiteren LLM-Schritte (Layout-QA, Klassifikation, OCR-Korrektur, TEI-Refinement, NER) wird einheitlich **Gemini 3.1 Flash-Lite** (`gemini-3.1-flash-lite-preview`) verwendet: starkes multimodales Modell, schnell und für den Einsatz gut geeignet.

### Schritt 3: Layout-Analyse

**Docling 2.75** (IBM Research, RT-DETR V2 Heron, 42,9 M Parameter, DocLayNet, mAP 0.699) erkennt 17 Blocktypen und wird bewusst nur für das Layout verwendet, nicht für OCR (RapidOCR hat FR-Encoding-Probleme). **Gemini 3.1 Flash-Lite** korrigiert die Docling-Ergebnisse ergänzend in drei Modi: `qa` (Korrektur + Quality-Score), `detect` (Neudetektion, Fallback für die ~15 % schwieriger Seiten) und `auto` (routet pro Seite). Beide Versionen bleiben erhalten — in den Digital Humanities ist Provenienz so wichtig wie Qualität. Verifiziert wird über SVG-Overlays im Frontend und gerenderte Overlay-PNGs. Polygon-Support wurde bewusst ausgeschlossen (sauber gesetzter Verlagsdruck, Rechtecke genügen).

### Schritt 4: PAGE-XML-Erzeugung

PAGE-XML wird deterministisch aus Layout-JSON und OCR-Text erzeugt (`scripts/layout/page_xml_generator.py`), zusätzlich METS (Schema 2013-07-15 für coOCR/Transkribus). **Wichtig:** PAGE-XML ist **kein Zwischenschritt zum TEI** — das TEI wird direkt aus Layout-JSON und OCR-Markdown generiert; PAGE-XML ist ein paralleler Export für externe Systeme. Beide Formate leiten sich unabhängig aus denselben Quellen ab.

### Schritt 5: Named Entity Recognition und Wikidata-Verknüpfung

Die NER erfolgt seitenweise mit Gemini 3.1 Flash-Lite für sechs Entitätstypen (Personen, Orte, Datum, Organisationen, Events, Werke). Ein Entity Store dedupliziert Schreibvarianten; daraus entstehen Indizes für Personen, Organisationen, Orte und Werke. Der Korpus umfasst rund 11.685 Entitäten / 26.197 Mentions über 285 Dokumente; der Index zählt etwa 4.504 Einträge, von denen rund 47 % mit Wikidata/GND verlinkt sind (Stand laut Knowledge-Base; noch nicht gegen die Primärartefakte re-auditiert). Eine methodische Festlegung ist zentral: **Entity-ID-Linking erfolgt ausschließlich deterministisch über APIs, niemals per LLM**. Die Verknüpfung mit dem TEI folgt der Dual-Attribut-Strategie: `ref="GND:…"` (primär) plus `corresp="#zbz-{typ}.{N}"` (interne ID). Eine Precision/Recall-Messung der NER steht aus.

### Schritt 6: TEI-XML-Erzeugung

Vier Stufen: (1) regelbasiertes Scaffold, (2) Gemini-Call pro Seite für algorithmisch schwierige Aufgaben, (3) Assembly zu einem TEI-Dokument plus Post-Assembly-Fixes, (4) Validierung. Validiert wird gegen das **projektspezifische RelaxNG-Schema `zbz_hersch.rng`** (TEI P5 v4.10.2, 551 Definitionen, aus ODD generiert), das auf dem DTA-Basisformat aufbaut und durch die verbindlichen ZBZ-Editionsrichtlinien ergänzt wird. Ergebnis: 285/285 Dokumente schema-valide, 29 informative Warnings (ein bekannter Header-Schema-Defekt im `tei_final`-`<idno>` ist als offener Punkt registriert).

### Schritt 7: Workflow-Status pro Datenstrom (ersetzt das frühere Agent-Screening)

Ursprünglich war als letzter Schritt ein agentenbasiertes 7-Schichten-Quality-Screening vorgesehen; der Lauf über alle 285 Dokumente ergab 242 „APPROVED" und 43 „WITH_NOTES". Dieses Verfahren wurde im Mai **bewusst abgeschafft**. Der ausschlaggebende Befund: kein einziger „APPROVED"-Status kam von einem Menschen — der Agent zertifizierte sich selbst, mit eingebauter Ignorier-Liste und ohne fachliche Bewertung. Das Etikett war gegenüber der ZB epistemisch irreführend.

An seine Stelle tritt ein **menschgesetzter Workflow-Status pro Datenstrom**. Für jeden Strom (OCR, Layout, TEI) gilt einer von vier Werten: `unverifiziert` (Default für alle 285 Dokumente), `in_arbeit`, `bearbeitet`, `fertig`. Der Status wird im Viewer gesetzt, mit voller Provenienz-History in einem Pro-Objekt-Manifest persistiert und bei der ZB-Übergabe deterministisch in den `<revisionDesc>` projiziert. Im UI ist die Logik als Ampel umgesetzt: gelb = vorhanden, aber nicht freigegeben; grün = fertig; rot reserviert für einen künftigen Problem-Status. Das Reframing folgt der Einsicht, dass die Pipeline OCR/Layout/TEI deterministisch für alle Dokumente produziert — der ehrliche Default ist „vorhanden, unverifiziert", nicht „nichts da". Stand 26.05.2026 stehen alle 285 Dokumente in allen drei Strömen auf `unverifiziert` — der ehrliche Ausgangsanker für die fachliche Kuration.

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
