# Arbeitsbericht: KI-gestuetzte OCR/TEI-Pipeline fuer den Nachlass Jeanne Hersch

**Digital Humanities Craft OG**
Berichtszeitraum: 29. Jaenner -- 15. Maerz 2026
Stand: 15. Maerz 2026

---

## 1. Zusammenfassung

Aus 286 gescannten PDF-Dokumenten des Nachlasses Jeanne Hersch (ca. 4.150 Seiten) ist ein funktionsfaehiges System entstanden. Die Pipeline erzeugt standardkonforme TEI-XML-Dateien, erkennt und verlinkt Personen, Organisationen, Orte und Werke, und stellt die Ergebnisse in einer digitalen Edition mit integriertem Kurationswerkzeug bereit.

285 von 286 Dokumenten wurden vollstaendig verarbeitet (ein Dokument fehlt im Ausgangsmaterial, siehe Abschnitt 2). Alle erzeugten TEI-Dateien sind gegen das TEI-All-Schema validiert. Die verbleibende Arbeit betrifft nicht die Erzeugung, sondern die Verfeinerung: Wikidata-Verlinkung der Entities vervollstaendigen und gemeinsam mit der ZBZ den Kurationsprozess erproben.

---

## 2. Ausgangsmaterial

Die ZBZ lieferte am 27. Februar 2026:
- 286 PDF-Scans (ca. 4.150 Seiten, vier Layout-Typen, 14 Genres, 39 mehrsprachige Dokumente)
- 25 annotierte TEI-XML-Referenzdateien (manuell erstellt, dienen als Qualitaetsmassstab)
- 24 PAGE-XML-Exporte aus Transkribus (Schema 2013-07-15, ohne Textinhalt)

Die Masterfile der ZBZ zaehlt 289 Texte, die Lieferung enthaelt 286 PDFs. Die Differenz von drei Dokumenten ist dokumentiert, aber noch ungeklaert.

---

## 3. Was wurde gebaut

### 3.1 OCR-Texterkennung

Mistral Document AI (Azure AI Foundry) hat den gesamten Korpus verarbeitet (4.117 Seiten). Die durchschnittliche Zeichenfehlerrate ueber 15 Pilot-Dokumente betraegt 5,9% vor und 5,6% nach optionaler LLM-Korrektur. Eine zusaetzliche Gemini-basierte Nachkorrektur bringt Verbesserungen bei franzoesischen Akzenten und JSTOR-Artefakten.

### 3.2 Layout-Analyse

Zwei Systeme arbeiten zusammen: Docling (IBM, Open Source) erkennt Regionen und Bounding Boxes, Gemini korrigiert Labels und detektiert fehlende Bereiche. Ueber den Gesamtkorpus wurden 30.714 Layout-Regionen erkannt, davon 14.708 durch Gemini korrigiert und 894 neu hinzugefuegt.

### 3.3 TEI-Erzeugung

Die Pipeline arbeitet in drei Stufen. Stufe 1 erzeugt regelbasiert ein TEI-Grundgeruest mit typkorrekten Entity-Tags und internen IDs. Stufe 2 verfeinert das Geruest mittels Gemini, gesteuert durch dokumenttypspezifische Regeln fuer 12 Genres. Stufe 3 setzt die Einzelseiten zum Gesamtdokument zusammen -- mit teiHeader, Faksimile-Verknuepfung und automatischem Zusammenfuehren der Seitenstrukturen zu einem zusammenhaengenden Dokument.

Alle 285 erzeugten TEI-Dateien sind gegen das RelaxNG-Schema TEI-All validiert. Die Validierung ist in die Pipeline integriert und erzeugt automatisch einen HTML-Qualitaetsbericht. Ein Referenz-Vergleich mit den 11 ZBZ-Referenz-TEI zeigt, dass die Dokumentstruktur (ein zusammenhaengender Textkoerper pro Dokument, wie in der Referenz) korrekt abgebildet wird. Die Textgenauigkeit variiert je nach Scan-Qualitaet (CER 0,4% bis 12% bei guten Scans, hoeher bei schlechten Vorlagen).

Mehrsprachige Dokumente erhalten korrekte Sprachauszeichnungen im Header (z.B. Franzoesisch und Deutsch als separate Eintraege statt einer pauschalen Kennzeichnung als "unbestimmt").

### 3.4 Entitaetserkennung und Verlinkung

Die Pipeline erkennt sechs Typen von Entitaeten: Personen, Organisationen, Orte, Werke, Ereignisse und Daten. Ueber den Gesamtkorpus wurden 11.685 eindeutige Entitaeten mit 26.197 Nennungen identifiziert.

Jede Entitaet erhaelt eine projekteigene ID (z.B. zbz-p.2 fuer Jeanne Hersch, zbz-l.705 fuer die Schweiz, zbz-o.6 fuer die Universitaet Genf). Diese IDs dienen als stabile Referenz innerhalb der Edition. Von dort aus verlinkt ein zentraler Entity-Index auf Wikidata und GND. Aktuell sind 24% der Entitaeten mit Wikidata-IDs verknuepft; die Vervollstaendigung erfordert laengere Batch-Laeufe gegen die Wikidata-API, ist aber technisch vorbereitet.

Im TEI-Text werden Entitaeten mit dem korrekten TEI-Element ausgezeichnet: Personen als persName, Organisationen als orgName, Orte als placeName, Werke als bibl -- jeweils mit Verweis auf die interne ID.

### 3.5 Digitale Edition

Eine oeffentliche Website zeigt alle 286 Dokumente in einem Katalog mit Filterung und Volltextsuche. Der Reader stellt Faksimile und TEI-Text nebeneinander dar, mit einer Sidebar fuer Entitaeten (Personen, Organisationen, Orte, Werke mit Links zu Wikidata und GND).

### 3.6 Kurationswerkzeug

Ein Browser-basierter Editor erlaubt die Nachbearbeitung der KI-generierten TEI-Dokumente als letzten Schritt vor der Publikation. Editoren koennen Text korrigieren, die Dokumentstruktur aendern, Entitaeten hinzufuegen oder korrigieren, und das Ergebnis gegen das TEI-Schema validieren. Ein Review-Workflow mit drei Stufen (Entwurf, Pruefung, Freigegeben) steuert, welche Dokumente publiziert werden.

---

## 4. Wesentliche Architekturentscheidungen

**Wikidata statt GND als primaeres ID-System.** Wikidata bietet breitere internationale Abdeckung, was fuer den ueberwiegend frankophonen Korpus entscheidend ist. GND-IDs werden ueber Wikidata ergaenzend nachgeschlagen.

**Gemini-Docling-Hybrid fuer die Layout-Analyse.** Docling liefert zuverlaessige Bounding Boxes, hat aber Schwaechen bei bestimmten Seitenformaten. Gemini korrigiert und ergaenzt. Die Kombination ist besser als jedes System allein.

**Regelbasierte Erzeugung plus KI-Verfeinerung.** Die TEI-Erzeugung kombiniert deterministische Regeln (reproduzierbar, kostenlos) mit Gemini-Verfeinerung (kontextsensitiv, kostet pro Seite). Das erlaubt iterative Verbesserung: Regelaenderungen koennen ohne erneute API-Aufrufe angewandt werden.

**Entitaetserkennung nach der TEI-Erzeugung, nicht waehrenddessen.** Das entkoppelt zwei verschiedene Qualitaetsanforderungen und erlaubt, beide unabhaengig zu verbessern.

---

## 5. Bekannte Einschraenkungen

**Scan-Qualitaet bestimmt die Textgenauigkeit.** Die CER-Streuung geht primaer auf unterschiedliche Vorlagenqualitaet zurueck. Schlechte Scans koennen durch KI-Korrektur nur begrenzt kompensiert werden.

**Die Entitaetserkennung hat eine False-Positive-Rate von 5 bis 10%.** Generische Begriffe werden gelegentlich als Entitaeten markiert. Das ist ein bekanntes Merkmal LLM-basierter Erkennung und wird ueber das Kurationswerkzeug korrigiert.

**Die Wikidata-Verlinkung ist noch unvollstaendig.** 24% der Entitaeten sind verlinkt. Die Vervollstaendigung ist technisch vorbereitet und erfordert Rechenzeit, keine konzeptuelle Arbeit.

---

## 6. Kosten

| Komponente | Geschaetzte Kosten (Gesamtkorpus) |
|---|---|
| OCR (Mistral/Azure) | abhaengig vom Abrechnungsmodell |
| Layout-QA (Gemini) | unter 10 USD |
| TEI-Erzeugung (Gemini) | ca. 80 USD |
| NER-Extraktion (Gemini) | unter 5 USD |
| Wikidata-API | kostenfrei |

Alle Zwischenergebnisse werden gespeichert. Die Pipeline ist resume-faehig und ueberspringt bereits verarbeitete Dokumente. Aenderungen an den Erzeugungsregeln koennen ohne erneute API-Aufrufe angewandt werden (Re-Assembly-Modus).

---

## 7. Produktionsstand

| Komponente | Stand | Abdeckung |
|---|---|---|
| Bilderzeugung aus PDF | abgeschlossen | 286/286 Dokumente |
| OCR-Texterkennung | abgeschlossen | 286/286 Dokumente, 4.117 Seiten |
| Layout-Analyse | abgeschlossen | 286/286 Dokumente, 4.152 Seiten |
| TEI-Erzeugung und Validierung | abgeschlossen | 285/285 Dokumente, schema-valide |
| Entitaetserkennung | abgeschlossen | 285/285 Dokumente, 11.685 Entitaeten |
| Wikidata-Verlinkung | laufend | 2.803 von 11.685 Entitaeten (24%) |
| Digitale Edition | funktionsfaehig | 286 Dokumente im Katalog |
| Kurationswerkzeug | funktionsfaehig | bereit fuer Pilotbetrieb |
| PAGE-XML-Export | abgeschlossen | 286/286 Dokumente, Transkribus-kompatibel |

---

## 8. Was die ZBZ als Naechstes tun kann

**Kurationspilot starten.** Das Kurationswerkzeug ist einsatzbereit. Ein gemeinsamer Pilotdurchlauf an zwei bis drei ausgewaehlten Dokumenten wuerde den Workflow von der KI-Erzeugung ueber die redaktionelle Pruefung bis zur Freigabe erproben. Kandidaten: Doc 2310 (kurzer Zeitschriftenartikel, franzoesisch), Doc 1440 (Interview, deutsch), Doc 100 (laengerer Essay, franzoesisch). DHCraft bereitet diese Dokumente vor; die ZBZ stellt eine Editorin oder einen Editor fuer den Test bereit.

**Offene Fragen klaeren.** Drei Punkte warten auf Rueckmeldung der ZBZ: die Differenz von 289 zu 286 Dokumenten im Masterfile, die Bereitstellung von ALMA/MMSID-Metadaten fuer den teiHeader, und die Frage der Normalisierung versus Quellentreue bei Ueberschriften (Klaerung mit Frau Baehler ausstehend).

**Infrastruktur vorbereiten.** Fuer den Produktivbetrieb bei der ZBZ sind Containerisierung (Podman) und CI/CD-Integration (GitLab Uni Zuerich) vorgesehen. Die Planung kann beginnen, sobald der Kurationspilot abgeschlossen ist.

---

## Anhang A: Chronologie

| Nr. | Datum | Schwerpunkt |
|---|---|---|
| 1 | 29.01. | Korpusanalyse, Pipeline-Architektur, erste OCR-Tests |
| 2--4 | 25.02. | Dashboard, Dokumentklassifikation, Online-Demo |
| 5--10 | 05.03. | OCR-Korrektur, PAGE-XML-Export, Frontend-Aufbau |
| 11--14 | 06.03. | TEI-Generator, Layout-Gesamtlauf, Digitale Edition |
| 15--16 | 07.03. | Pipeline-Refactoring, NER-Pipeline |
| 17--22 | 08.--09.03. | NER Scale-Up, Curation Editor, Entity Injection |
| 23 | 12.03. | Wikidata/GND-Integration, Bug-Fixes |
| 24 | 14.03. | Frontend-Konsolidierung |
| 26 | 15.03. | TEI-Validierung, Entity-Korrektur, Dokumentstruktur, Produktionslauf 285/285 |

## Anhang B: Wesentliche Entscheidungen

| ID | Entscheidung | Begruendung |
|---|---|---|
| E19 | Docling + Gemini Hybrid fuer Layout | Docling fuer Regionen, Gemini fuer Korrektur und Ergaenzung |
| E32 | Dreistufige TEI-Pipeline | Regelbasiert + KI-Verfeinerung + Assembly |
| E34 | Wikidata als primaere Entity-ID | Breitere Abdeckung als GND fuer frankophonen Korpus |
| E36 | Kurationswerkzeug mit Review-Workflow | Redaktionelle Pruefung als letzter Schritt vor Publikation |
| E37 | Zweistufige Validierung | Schema-Pruefung (blockierend) + Qualitaetswarnungen (informativ) |
| E38 | Typkorrekte Entity-Tags mit internen IDs | Personen, Organisationen, Orte, Werke korrekt unterschieden |
| E40 | Dokumentstruktur-Merge | Seitenweise Erzeugung, dokumentweise Zusammenfuehrung |
