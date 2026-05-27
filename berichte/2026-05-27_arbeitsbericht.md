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

### Der Korpus als Trichter (verifiziert gegen die Primärquellen)

Die zentrale Kennzahl „wie groß ist der Korpus" ist keine einzelne Zahl, sondern ein Trichter über vier Quellen. Er wurde deterministisch aus den Primärdaten abgeleitet (ZBZ-Masterfile, gelieferte PDFs, Pipeline-Output):

| Stufe | Anzahl | Einheit / Quelle |
|---|---|---|
| Im Masterfile geführte Texte | **325** | Texte (ZBZ-Masterfile) |
| davon `digitalisiert = ja` | **289** | Texte (Masterfile) |
| davon als PDF geliefert | **286** | PDFs (`data/scans/`) |
| davon mit finalem TEI | **285** | Dokumente (`output/tei_final/`) |

Die in früheren Projektnotizen kursierende Zahl „289" ist also nicht die Textmenge, sondern der **Digitalisierungs-Zähler** der Masterfile. Drei digitalisierte Texte wurden nicht als PDF geliefert (`1745`, `1750`, `1970`) — ein offener Klärungspunkt mit der ZB. Ein geliefertes PDF (`10`) durchlief die Pipeline bisher nicht bis zum finalen TEI. Die Differenz zwischen den 325 Masterfile-Texten und den 314 öffentlich genannten ZB-Texten bleibt extern zu klären.

### Seitenumfang (vier verschiedene Zählungen)

„Seitenzahl" ist ebenfalls mehrdeutig; die vier Werte messen Verschiedenes und dürfen nicht vermischt werden:

| Definition | Anzahl | Einheit / Quelle |
|---|---|---|
| bibliografischer Umfang | **7.186** | Seiten der 325 Masterfile-Texte |
| physischer Umfang | **4.152** | Seiten der 286 gelieferten PDFs (`pypdfium2`) |
| OCR-verarbeitet | **4.117** | Per-Seite-Markdown (`output/mistral_results/`) |
| im finalen TEI | **4.115** | `<pb>`-Elemente in `output/tei_final/` |

Der bibliografische Umfang (7.186) bezieht sich auf den gesamten katalogisierten Bestand, der physische (4.152) nur auf die tatsächlich gelieferten PDFs.

### Heterogenität des Bestands

Sämtliche Dokumente lagen als Drucktexte vor, handschriftliches Material war nicht systematisch vertreten — es handelte sich um einen reinen OCR-Prozess. Der Bestand erstreckt sich über **1931–2010** mit Schwerpunkt in den 1970er/80er-Jahren (**193 Texte** in 1970–1989).

Gattungs- und Sprachverteilung sind hier **auf Text-Ebene laut Masterfile (n=325)** angegeben — sie beschreiben den katalogisierten Bestand, nicht die 286 verarbeiteten PDFs:

| Gattung (Masterfile) | Anzahl | Anteil |
|---|---|---|
| Zeitschriftenartikel | 159 | 49 % |
| Sammelbandbeiträge | 127 | 39 % |
| Monografien | 38 | 12 % |
| AV-Medium | 1 | <1 % |

| Sprache (Masterfile) | Anzahl | Anteil |
|---|---|---|
| Französisch | 215 | 66 % |
| Deutsch | 98 | 30 % |
| Englisch | 8 | 2 % |
| Italienisch | 2 | 1 % |
| mehrsprachig fr/de | 1 | <1 % |

Geminis automatische Klassifikation der 286 PDFs liefert erwartungsgemäß abweichende Verteilungen (etwa 149 Zeitschriftenartikel, 51 Bücher, 48 Sammelbandbeiträge; und deutlich mehr mehrsprachig klassifizierte Dokumente). Diese Abweichung ist kein Fehler, sondern Ausdruck zweier verschiedener Zähl-Universen (bibliografische Text-Ebene vs. PDF-Ebene) und unterschiedlicher Kategorienschemata. Für Metadaten ist die Masterfile die verlässlichere Quelle. Der hohe Französisch-Anteil hat konkrete Konsequenzen für die Pipeline: französische Typografie (Guillemets, Akzente, Ligaturen, Leerzeichen vor Interpunktion), französische Trennregeln, überwiegend französische Beispiele in den Prompts.

Der Arbeitszeitraum erstreckte sich von **Ende Januar bis Ende Mai 2026**, dokumentiert durch **178 Commits** (erster Commit 29.01.2026, letzter 26.05.2026; Schwerpunkt im März mit 110 Commits). Im April und Mai folgten die wissenschaftliche CER-Re-Evaluation, eine Frontend-Radikalkur und die Ablösung des agentenbasierten Screenings durch ein menschgesetztes Workflow-Status-Modell.

## Repository-Architektur

Das Projekt ist in einem GitHub-Repository organisiert mit funktional getrennten Bereichen.

Der Ordner `knowledge/` enthält zehn thematisch getrennte Markdown-Dokumente (Projekt, Pipeline, Entitäten, Qualität, Viewer, Infrastruktur, Methodik, Entscheidungen, Journal, Index) als lebende, über Prompts kuratierte Single Source of Truth. Hervorzuheben sind das chronologische Arbeitstagebuch `journal.md` und das Entscheidungsregister `decisions.md` (E1–E67).

Die Datenhaltung ist nach Quelle und Generierung klar getrennt:

- `data/` — **Eingangs- und Referenzdaten**: PDF-Scans, ZBZ-Masterfile (`projektsteuerung/Masterfile.xlsx`), das projektspezifische TEI-Schema (`schema/zbz_hersch.rng`), 25 ZBZ-Referenz-TEIs, Editionsrichtlinien.
- `output/` — **alle generierten Datenströme** (gitignored, nicht versioniert).
- `docs/` — das Frontend (GitHub Pages), ein **generierter Mirror** der Pipeline-Daten und die aus den PDFs erzeugten PNGs.

Der Ordner `scripts/` enthält **50 versionierte Python-Skripte**, die zu 100 Prozent von Claude Code generiert wurden; keines wurde manuell geschrieben oder im Detail inspiziert. Geprüft wurde das Endergebnis. Eine zentrale Konvention strukturiert den Datenfluss: `output/tei_final/{doc}_final.xml` ist die Single Source of Truth der Edition, `docs/data/pages/{doc}/` ein generierter Mirror, der nie direkt editiert wird.

## Pipeline-Schritte

### Schritt 1: PDF-zu-PNG-Konvertierung

Die PDF-Scans werden mit `pypdfium2` in PNG-Bilder zerlegt (`scripts/edition/extract_pages.py`, 300 dpi) und unter `docs/images/` abgelegt — Grundlage aller weiteren Schritte.

### Schritt 2: OCR

**DeepSeek-OCR-2** (3B-VLM, lokal auf GPU, ~1,6 s/Seite) dient als Development-Engine für die Dokumenttypen A und C; produktiv wurde es wegen hoher GPU-Last und Spaltenproblemen nicht eingesetzt. Production-Engine ist **Mistral Document AI** (`mistral-document-ai-2512`) über **Azure AI Foundry**: erkennt neben Text auch Tabellen und Listen, liefert Per-Seite-Markdown (~1,3 s/Seite), chunkt große Dokumente automatisch (eine von Claude Code eigenständig getroffene Entscheidung). Kosten für den gesamten Korpus: rund 6–15 USD.

Eine optionale OCR-Korrektur mit **Claude Haiku 4.5** lieferte inkonsistente Ergebnisse (bei guter Ausgangs-OCR mit CER < 5 % sogar leicht verschlechternd, gemessen +0,10 %) und ist daher optional, nicht Default. Für alle weiteren LLM-Schritte (Layout-QA, Klassifikation, OCR-Korrektur, TEI-Refinement, NER) wird einheitlich **Gemini 3.1 Flash-Lite** (`gemini-3.1-flash-lite-preview`) verwendet: stärkstes multimodales Modell seiner Preisklasse, schnell und günstig (0,25 USD / 1 M Input, 1,50 USD / 1 M Output).

### Schritt 3: Layout-Analyse

**Docling 2.75** (IBM Research, RT-DETR V2 Heron, 42,9 M Parameter, DocLayNet, mAP 0.699) erkennt 17 Blocktypen und wird bewusst nur für das Layout verwendet, nicht für OCR (RapidOCR hat FR-Encoding-Probleme). **Gemini 3.1 Flash-Lite** korrigiert die Docling-Ergebnisse ergänzend in drei Modi: `qa` (Korrektur + Quality-Score), `detect` (Neudetektion, Fallback für die ~15 % schwieriger Seiten) und `auto` (routet pro Seite). Beide Versionen bleiben erhalten — in den Digital Humanities ist Provenienz so wichtig wie Qualität. Verifiziert wird über SVG-Overlays im Frontend und gerenderte Overlay-PNGs. Polygon-Support wurde bewusst ausgeschlossen (sauber gesetzter Verlagsdruck, Rechtecke genügen).

### Schritt 4: PAGE-XML-Erzeugung

PAGE-XML wird deterministisch aus Layout-JSON und OCR-Text erzeugt (`page_xml_generator.py`), zusätzlich METS (Schema 2013-07-15 für coOCR/Transkribus). **Wichtig:** PAGE-XML ist **kein Zwischenschritt zum TEI** — das TEI wird direkt aus Layout-JSON und OCR-Markdown generiert; PAGE-XML ist ein paralleler Export für externe Systeme. Beide Formate leiten sich unabhängig aus denselben Quellen ab.

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

Die Layout-Analyse liefert bei Doppelseiten und komplexen Strukturen Fehler (durch zusätzliche Gemini-Calls erweiterbar). Die NER/Wikidata-Verknüpfung ist explorativ und nicht mit Precision/Recall gemessen. Die Run-zu-Run-Stabilität der nicht-deterministischen LLM-Stufen ist nicht quantifiziert. Drei digitalisierte Texte (`1745`, `1750`, `1970`) wurden nicht als PDF geliefert; ein geliefertes PDF (`10`) hat noch kein finales TEI; die Differenz 325 Masterfile-Texte vs. 314 öffentlich genannte ZB-Texte ist extern zu klären. Ein Header-Schema-Defekt (`<idno>` in `tei_final`) ist registriert. Der Round-Trip vom Viewer-Edit zurück in die Pipeline ist dokumentiert, aber nicht in einem Wrapper-Skript automatisiert.

Trotz dieser offenen Punkte demonstriert das Projekt, dass eine vollständige digitale Edition von PDF-Scans bis zum bearbeitbaren, schema-validen TEI-XML — inklusive quantitativ belegter Textqualität (Median-CER 1,83 %) und einem ehrlichen, menschzentrierten Qualitätsmodell — in wenigen Wochen mit Kosten knapp über 100 USD erzeugt werden kann, wenn die gesamte Pipeline LLM-gestützt und agentenbasiert aufgebaut wird.
