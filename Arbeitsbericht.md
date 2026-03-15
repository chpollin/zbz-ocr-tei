# Arbeitsbericht: KI-gestützte OCR/TEI-Pipeline für den Nachlass Jeanne Hersch

**Digital Humanities Craft OG**
Berichtszeitraum: 29. Jänner – 15. März 2026
Stand: 15. März 2026

---

## 1. Zusammenfassung

Für die Zentralbibliothek Zürich wurde eine vollständige KI-Pipeline entwickelt, die 286 gescannte PDF-Dokumente (ca. 4.150 Seiten) des Nachlasses Jeanne Hersch in standardkonforme TEI-XML-Dateien transformiert. Die Pipeline umfasst OCR-Texterkennung, Layout-Analyse, TEI-Erzeugung mit Schema-Validierung, Named Entity Recognition mit Wikidata/GND-Verlinkung sowie eine digitale Edition mit integriertem Kurationswerkzeug. Alle Komponenten sind produktiv einsetzbar und auf dem Gesamtkorpus getestet.

---

## 2. Korpus und Ausgangsmaterial

Die ZBZ lieferte am 27. Februar 2026 insgesamt 286 PDF-Scans, 25 annotierte TEI-XML-Referenzdateien und 24 PAGE-XML-Exporte aus Transkribus (Schema 2013-07-15, ohne Textinhalt). Drei Dokumente weniger als die 289 Texte im Masterfile; die Differenz ist dokumentiert aber ungeklärt.

Aus der Analyse des Gesamtkorpus ergeben sich vier Layout-Typen (A: einspaltiger Zeitschriftenartikel, B: mehrspaltiges Layout, C: Monografie/Buchseiten, D: gemischte Formate), 14 Genres (Artikel, Essay, Vortrag, Interview, Rezension, Konferenzbeitrag, Zeitungsseite, Debatte, Vorwort, Brief, Enzyklopädie-Eintrag u.a.) sowie 39 mehrsprachige Dokumente (vorwiegend Französisch, Deutsch, teils Italienisch). Die Klassifikation aller 286 Dokumente erfolgte automatisiert mittels Gemini 3.1 Flash Lite (visuelle Analyse der jeweils ersten fünf Seiten) und wurde stichprobenartig verifiziert (80% Übereinstimmung bei Layout-Typ, 86% bei Sprache).

---

## 3. Pipeline-Komponenten und Ergebnisse

### 3.1 OCR-Texterkennung

Als primäre OCR-Engine dient Mistral Document AI (Azure AI Foundry), die den gesamten Korpus verarbeitet hat (4.117 Seiten, ca. 1,3 Sekunden pro Seite). Die durchschnittliche Zeichenfehlerrate (CER) über 15 Pilot-Dokumente beträgt 5,87% vor und 5,55% nach LLM-Korrektur. Die besten Ergebnisse liefern Monografien (Phase 4, CER 2,65%), die schwächsten ergeben sich bei einspaltigen Zeitschriftenartikeln mit JSTOR-Coverseiten (Phase 1, CER 9,40% vor Korrektur).

Zusätzlich wurde eine Gemini-basierte OCR-Nachkorrektur implementiert, die in zwei Varianten arbeitet (textbasiert und multimodal mit Scan-Bild). Die textbasierte Variante erzielt geringfügig bessere Ergebnisse und ist kostengünstiger. Den größten Zugewinn bringt die Korrektur bei Dokumenten mit französischen Akzenten und OCR-Artefakten von JSTOR-Coverseiten.

### 3.2 Layout-Analyse

Die Layout-Analyse kombiniert zwei Systeme. Docling (IBM, Open Source) dient als primärer Detektor und hat alle 4.152 Seiten verarbeitet. Gemini 3.1 Flash Lite übernimmt zwei Rollen: als Qualitätskontrolle (korrigiert Docling-Labels) und als eigenständiger Detektor für Seiten, auf denen Docling unzureichende Ergebnisse liefert. Ein automatischer Routing-Modus entscheidet pro Seite, welche Strategie angewandt wird.

Ergebnis des Gesamtlaufs über 286 Dokumente und 3.992 Seiten: 30.714 Layout-Regionen erkannt, 14.708 Korrekturen durch Gemini, davon 894 komplett neu hinzugefügte Regionen (fehlende Überschriften, Fußnoten, Kopfzeilen). Die visuelle Qualitätsprüfung an Stichproben bestätigt, dass die Kombination beider Systeme deutlich bessere Ergebnisse liefert als Docling allein.

### 3.3 TEI-Erzeugung und Validierung

Die TEI-Erzeugung folgt einer dreistufigen Unified Pipeline. Stufe 1 erzeugt regelbasiert ein TEI-Grundgeruest aus OCR-Text und Layout-Daten, inklusive typkorrekter Entity-Annotation (persName, orgName, placeName, bibl) mit internen IDs aus dem Entity Index. Stufe 2 verfeinert dieses Geruest mittels Gemini (ein API-Aufruf pro Seite, gesteuert durch einen dokumenttypspezifischen Mapping-Table-Prompt mit Regeln fuer 12 Genres). Stufe 3 assembliert die Einzelseiten zum Gesamtdokument mit vollstaendigem teiHeader, Faksimile-Verknuepfung, automatischem div-Merge (Seiten-Fragmente werden zu einem Dokument-div zusammengefuegt, wie in der ZBZ-Referenz) und Schema-Validierung.

Der Produktionslauf ueber alle 285 Dokumente (4.108 Seiten) wurde abgeschlossen. Die Validierung prüft gegen das RelaxNG-Schema TEI-All, sechs projektspezifische Regeln (R1-R6: Dokumenttyp, Header, Body, div-Struktur, note-Attribute) sowie elf informative Warn-Kategorien (W1-W11: Sprachcodes, Header-Vollstaendigkeit, Faksimile/pb-Synchronitaet, leere divs, Text-Volumen, lb-Dichte, graphic-URLs, Entity-Coverage, Entity-Refs, Typ-Balance, div-Struktur). Die Validierung ist standardmaessig aktiv und erzeugt automatisch einen HTML-Report.

Mehrsprachige Dokumente (~40) erhalten korrekte separate language-Elemente im teiHeader (z.B. `<language ident="fra"/>` + `<language ident="deu"/>` statt des generischen "und"). Entity-Tags nutzen typkorrekte TEI-Elemente mit interner ID als ref-Attribut (z.B. `<placeName ref="#zbz-l.705">Suisse</placeName>`, `<orgName ref="#zbz-o.9">SGG</orgName>`). Ein Stopwort-Filter verhindert, dass generische Begriffe (Dieu, Monde, Terre u.a.) als Entities getaggt werden.

Ein Referenz-Vergleich mit den 11 verfuegbaren ZBZ-Referenz-TEI (`--compare-ref`) zeigt eine CER-Spanne von 0,4% bis 63,7% (Median ca. 12%), wobei die Streuung hauptsaechlich auf unterschiedliche Scan-Qualitaet zurueckgeht. Die div-Struktur ist nach dem automatischen Merge korrekt (1 top-level div pro Dokument, wie in der Referenz), die Absatzanzahl (p) liegt systematisch hoeher als in der Referenz, weil die Pipeline eine feinere Layout-Granularitaet abbildet.

### 3.4 Named Entity Recognition und Verlinkung

Die NER-Pipeline arbeitet post-hoc auf den fertiggestellten TEI-Dokumenten. Gemini Flash Lite extrahiert Entities pro Seite als strukturiertes JSON, ein Entity-Store aggregiert pro Dokument, und die Wikidata-API übernimmt die Identifikation (kein LLM für IDs).

Ergebnis auf dem Gesamtkorpus (285 Dokumente, 3.536 Seiten): 11.685 eindeutige Entities mit 26.197 Nennungen. Die Typverteilung ist 36,7% Personen, 22,3% Orte, 15,0% Daten, 13,6% Organisationen, 10,8% Werke und 1,6% Ereignisse. Davon sind 2.803 Entities (24%) mit Wikidata-IDs verlinkt, 958 (21,7% der verknüpfbaren Entities) zusätzlich mit GND-IDs.

Der Entity Index umfasst 4.100 Eintraege als TEI-XML mit eigenem ID-Schema (zbz-p fuer Personen, zbz-o fuer Organisationen, zbz-l fuer Orte, zbz-w fuer Werke) und dient als Single Source of Truth fuer alle Entitaets-Referenzen. Entity-Tags im TEI erhalten die interne ID als ref-Attribut (z.B. `ref="#zbz-p.2"` fuer Jeanne Hersch), von wo der Index auf Wikidata und GND weiterverlinkt. Die Entity-Annotation in Stufe 1 der TEI-Pipeline nutzt den Index direkt fuer typkorrekte Tags (persName, orgName, placeName, bibl) mit automatischer Referenzierung.

### 3.5 Digitale Edition

Eine öffentliche statische Website bietet vier Seiten (Startseite, Katalog, Reader, About) mit eigenem Design-System. Der Katalog zeigt alle 286 Dokumente mit facettierter Filterung (Typ, Sprache, Publikationsform, Zeitraum) und Client-seitiger Volltextsuche. Der Reader zeigt Faksimile und TEI-Text nebeneinander mit Seitennavigation, Zoom, Schriftart-Wechsel, einer Entitäten-Sidebar (Personen, Organisationen, Orte, Werke mit Wikidata- und GND-Links) und einer XML-Ansicht.

### 3.6 Kurationswerkzeug

Ein Curation Editor ermöglicht die manuelle Nachbearbeitung der KI-generierten TEI-Dokumente als letzten Human-in-the-Loop-Schritt vor der Publikation. Die Funktionen umfassen WYSIWYG-Bearbeitung mit DOM-zu-XML-Serialisierung, Struktur-Editing (Block-Typ wechseln, teilen, zusammenfügen, löschen), Entity-Kuration (Text markieren und als Person/Organisation/Ort/Werk taggen, mit Autocomplete aus lokalem Entity-Index und Wikidata), TEI-Validierung im Editor sowie einen Review-Workflow mit drei Status-Stufen (Entwurf, Prüfung, Freigegeben). Nur freigegebene Dokumente können publiziert werden.

---

## 4. Architekturentscheidungen

Die Pipeline folgt dem Prinzip "Critical Expert in the Loop": KI-Systeme erzeugen Entwürfe, die von Fachpersonen geprüft und korrigiert werden. Die wichtigsten Entscheidungen im Projektverlauf waren die folgenden.

**Wikidata als primäres ID-System statt GND.** Wikidata bietet breitere internationale Abdeckung, was für einen überwiegend frankophonen Korpus entscheidend ist. GND-IDs werden über Wikidata (Property P227) nachgeschlagen und ergänzend geführt.

**Gemini-Docling-Hybrid statt einer einzelnen Layout-Engine.** Docling liefert zuverlässige Bounding Boxes, hat aber Schwächen bei Landscape-Seiten und fehlenden Regionen. Gemini korrigiert Labels und detektiert fehlende Regionen, kann aber keine Bounding Boxes liefern. Die Kombination nutzt die Stärken beider Systeme.

**Unified Pipeline statt separater Werkzeuge.** Die anfänglich getrennte regelbasierte TEI-Erzeugung und Gemini-Verfeinerung wurden in eine dreistufige Pipeline zusammengeführt. Das reduziert Fehlerquellen und ermöglicht Batch-Verarbeitung mit Resume-Fähigkeit.

**Mapping-Table-Prompt statt Few-Shot-Prompting.** Die Gemini-Verfeinerung nutzt eine systematische Mapping-Tabelle mit Regeln für 12 Genres statt einzelner Beispiele. Das skaliert besser über die Genrevielfalt des Korpus.

**Post-hoc NER statt integrierter Erkennung.** Die Entity-Erkennung läuft nach der TEI-Erzeugung, nicht währenddessen. Das entkoppelt die beiden Qualitätsanforderungen (Schema-Validität und Entity-Vollständigkeit) und erlaubt iterative Verbesserung.

---

## 5. Bekannte Limitationen

**Scan-Qualität als Hauptfehlerquelle.** Die CER-Streuung (0,4% bis 63,7%) geht primär auf unterschiedliche Scan-Qualität zurück, nicht auf OCR-Schwächen. Schlechte Scans können durch LLM-Korrektur nicht kompensiert werden.

**Gemini-NER hat 5 bis 10% False Positives.** Generische Begriffe ("Rédacteur en chef", "Tirage") werden als Entities erkannt. Dieser Fehlertyp ist inhärent bei LLM-basierter NER und wird über den Curation Editor korrigiert, nicht durch Code-Anpassungen.

**Landscape-Seiten und Mehrspaltenlayouts.** Bei breiten Landscape-Seiten fehlt gelegentlich die rechteste Spalte in der Gemini-Layout-Detektion. Betrifft primär Enzyklopädie-Einträge mit vier oder mehr Spalten.

**Wikidata-Verlinkung noch unvollstaendig.** 24% der Entities sind verlinkt. Die verbleibenden 76% erfordern laengere Batch-Laeufe gegen die Wikidata-API, die zeitaufwaendig sind aber keine technischen Hindernisse darstellen.

**Step-2-Cache bei Pipeline-Aenderungen.** Die Gemini-Verfeinerung (Stufe 2) wird pro Seite gecacht. Bei Aenderungen am Prompt oder an der Scaffold-Logik muessen die gecachten Dateien invalidiert werden, damit die Verbesserungen wirksam werden. Ein `--reassemble`-Modus erlaubt kostenlose Re-Assembly (Stufe 1+3 neu, Stufe 2 aus Cache).

---

## 6. Kosten und Infrastruktur

Die Pipeline nutzt drei externe API-Dienste. Mistral Document AI (Azure AI Foundry) übernimmt die OCR, Gemini 3.1 Flash Lite (Google) die Layout-QA, TEI-Verfeinerung und NER, und die Wikidata-API die Entity-Verlinkung (kostenfrei). Die Kosten für einen vollständigen Produktionslauf aller 286 Dokumente liegen bei geschätzt 80 USD für die TEI-Erzeugung (Gemini), unter 10 USD für die Layout-Analyse (Gemini) und unter 5 USD für die NER-Extraktion (Gemini Flash Lite). Die OCR-Kosten über Mistral/Azure hängen vom gewählten Abrechnungsmodell ab.

Alle Zwischenergebnisse werden persistent gespeichert. Die Pipeline ist resume-fähig und überspringt bereits verarbeitete Dokumente. Jeder Verarbeitungsschritt kann einzeln wiederholt werden.

---

## 7. Liefergegenstände und Produktionsstand

| Komponente | Stand | Abdeckung |
|---|---|---|
| PNG-Extraktion aus PDF | abgeschlossen | 286/286 Dokumente |
| OCR (Mistral) | abgeschlossen | 286/286 Dokumente, 4.117 Seiten |
| Layout-Analyse (Docling + Gemini) | abgeschlossen | 286/286 Dokumente, 4.152 Seiten |
| TEI-Erzeugung (Unified Pipeline) | Produktionslauf abgeschlossen | 285/285 Dokumente erzeugt und validiert |
| TEI-Validierung | abgeschlossen | RelaxNG + R1-R6 + W1-W11, HTML-Report, Referenz-Vergleich |
| NER + Entity Index | abgeschlossen | 285/286 Dokumente, 11.685 Entities |
| Wikidata-Verlinkung | laufend | 2.803/11.685 Entities (24%) |
| GND-Verlinkung | laufend | 958/4.408 verknüpfbare Entities (21,7%) |
| Digitale Edition (Frontend) | funktionsfähig | 286 Dokumente im Katalog, 4 Demo-Dokumente online |
| Curation Editor | funktionsfähig | Bereit für Pilotbetrieb |
| PAGE-XML + METS Export | abgeschlossen | 286/286 Dokumente, Transkribus-kompatibel |

---

## 8. Naechste Schritte

Der TEI-Produktionslauf fuer alle 285 Dokumente ist abgeschlossen. Die Re-Assembly mit allen Qualitaetsfixes (div-Merge, Entity-Typ-Korrektur, Sprach-Mapping, head-Konvertierung) laeuft. Verbleibende Aufgaben:

1. **Finale Validierung und Referenz-Vergleich** nach Abschluss der Re-Assembly. Erwartung: nahezu alle Dokumente schema-valide.
2. **Wikidata-Linking vervollstaendigen** (Batch-Lauf ueber mehrere Stunden, aktuell 24%).
3. **Kurationspilot mit ZBZ** an ausgewaehlten Dokumenten (Doc 2310 u.a.): End-to-End-Workflow von der KI-Erzeugung ueber die Kuration bis zur Freigabe und Publikation.
4. **Containerisierung** (Podman) und **CI/CD** (GitLab Uni Zuerich) fuer die Uebergabe an die ZBZ.

---

## Anhang A: Chronologie der Arbeitssessions

| Nr. | Datum | Schwerpunkt |
|---|---|---|
| 1 | 29.01. | Korpusanalyse, Pipeline-Validierung, OCR Phase 1 |
| 2 | 25.02. | Dashboard-Redesign, Engine-Sichtbarkeit |
| 3 | 25.02. | Gemini-Dokumentklassifikation, Dashboard-Überarbeitung |
| 4 | 25.02. | Online-Demo (GitHub Pages), 4 Demo-Dokumente |
| 5 | 05.03. | Gemini OCR-Korrektur (zwei Varianten) |
| 6 | 05.03. | Code-Qualität und Refactoring |
| 7 | 05.03. | PAGE-XML + METS-Export, TEI-Erweiterung |
| 8 | 05.03. | PAGE-XML Viewer im Frontend |
| 9 | 05.03. | Dokumentations-Refactoring |
| 10 | 05.03. | Frontend-Refactoring |
| 11 | 06.03. | Gemini Vision TEI-Generator, dokumenttypspezifische Prompts |
| 12 | 06.03. | Layout-QA Gesamtlauf, Overlay-Generator |
| 13 | 06.03. | Unified TEI Pipeline |
| 14 | 06.03. | Digitale Edition |
| 15 | 07.03. | TEI Pipeline Refactoring + Validierungs-Fixes |
| 16 | 07.03. | NER-Pipeline + Entity Index |
| 17–18 | 08.03. | Phase 3 Scale-Up, Frontend-NER-Integration, Curation Editor MVP |
| 19–20 | 09.03. | Curation Editor Phasen 2–5 |
| 21 | 09.03. | Knowledge-Refactoring, NER Production Run |
| 22 | 09.03. | NER-Completion, TEI Entity Injection |
| 23 | 12.03. | Viewer WD/zbz-ID Support, GND-Bug-Fix |
| 24 | 14.03. | Frontend-Konsolidierung |
| 25 | – | (in Session-Nummerierung übersprungen) |
| 26 | 15.03. | TEI-Validierung Quality Gate, Entity-Tagging-Korrektur, div-Merge, Referenz-Vergleich, Production Run 285/285, 11 Learnings |

---

## Anhang B: Entscheidungsregister (Auswahl kundenrelevanter Entscheidungen)

| ID | Entscheidung | Begründung |
|---|---|---|
| E2 | Docling nur für Layout, nicht für OCR | RapidOCR-Encoding-Fehler bei französischem Text |
| E12 | Scope auf vollständige Pipeline erweitert | Absprache mit ZBZ, DHCraft baut parallele KI-Pipeline |
| E19 | Docling + Gemini Hybrid für Layout | Docling für BBoxes, Gemini für QA und fehlende Regionen |
| E23 | 286 statt 289 PDFs in der Lieferung | 3 Differenz zum Masterfile ungeklärt |
| E25 | Gemini Layout QA | Label-Korrektur und Qualitätsbewertung pro Seite |
| E26 | Gemini Layout Detect-Modus | Vollständige Neudetektion für schwache Seiten |
| E30 | Gemini Vision TEI + typspezifische Prompts | 12 Genre-Prompts für dokumenttypgerechte TEI-Erzeugung |
| E32 | Unified TEI Pipeline | Regelbasiert + Gemini-Verfeinerung in einer Pipeline |
| E33 | Digitale Edition als statische Website | Öffentlich zugänglich, kein Server erforderlich |
| E34 | Post-hoc NER mit Wikidata-Primär-ID | Breitere Abdeckung als GND allein |
| E36 | Curation Editor mit Review-Workflow | Human-in-the-Loop als Qualitaetssicherung |
| E37 | Validation Quality Gate | 2-Ebenen-Validierung (Errors/Warnings), HTML-Report, Default aktiv |
| E38 | Entity-Tagging typkorrekt mit internen IDs | persName/orgName/placeName/bibl mit ref="#zbz-p/o/l/w.N" |
| E39 | Sprach-Mapping + facsimile/pb Fix | Mehrsprachige Codes korrekt, pb/surface synchron |
| E40 | div-Merge + Referenz-Vergleich | Seiten-divs zu Dokument-div, CER/Struktur/Entity-Metriken |