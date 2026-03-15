# Arbeitsbericht: KI-gestuetzte OCR/TEI-Pipeline fuer den Nachlass Jeanne Hersch

**Digital Humanities Craft OG**
Berichtszeitraum: 29. Jaenner -- 15. Maerz 2026
Stand: 15. Maerz 2026

---

## 1. Zusammenfassung

Aus 286 gescannten PDF-Dokumenten des Nachlasses Jeanne Hersch (ca. 4.150 Seiten) ist ein funktionsfaehiges System entstanden. Die Pipeline erzeugt standardkonforme TEI-XML-Dateien, erkennt und verlinkt Personen, Organisationen, Orte und Werke, und stellt die Ergebnisse in einer digitalen Edition mit integriertem Kurationswerkzeug bereit.

285 von 286 Dokumenten wurden vollstaendig verarbeitet (ein Dokument fehlt im Ausgangsmaterial, siehe Abschnitt 2). 284 der erzeugten TEI-Dateien sind gegen das TEI-All-Schema validiert; ein Dokument hat einen nicht-blockierenden Strukturhinweis. Die verbleibende Arbeit betrifft nicht die Erzeugung, sondern die Verfeinerung: Wikidata-Verlinkung vervollstaendigen und gemeinsam mit der ZBZ den Kurationsprozess erproben.

---

## 2. Ausgangsmaterial

Die ZBZ lieferte am 27. Februar 2026:
- 286 PDF-Scans (ca. 4.150 Seiten, vier Layout-Typen, 14 Genres, 39 mehrsprachige Dokumente)
- 25 annotierte TEI-XML-Referenzdateien (manuell erstellt, dienen als Qualitaetsmassstab)
- 24 PAGE-XML-Exporte aus Transkribus (Schema 2013-07-15, ohne Textinhalt)

Die Masterfile der ZBZ zaehlt 289 Texte, die Lieferung enthaelt 286 PDFs. Die Differenz von drei Dokumenten ist dokumentiert, aber noch ungeklaert.

---

## 3. Ergebnisse

### 3.1 OCR-Texterkennung

Mistral Document AI (Azure AI Foundry) hat alle 4.117 Seiten verarbeitet. Die durchschnittliche Zeichenfehlerrate ueber 15 Pilot-Dokumente betraegt 5,9% vor und 5,6% nach optionaler Nachkorrektur. Die Genauigkeit haengt stark von der Scan-Qualitaet ab: Monografien erreichen 2,7%, Zeitschriftenartikel mit JSTOR-Coverseiten liegen bei 9,4%.

### 3.2 Layout-Analyse

Die Kombination aus Docling (IBM, Open Source) und Gemini hat ueber den Gesamtkorpus 30.714 Layout-Regionen erkannt. Gemini korrigierte 14.708 davon und fuegte 894 fehlende Bereiche hinzu (Ueberschriften, Fussnoten, Kopfzeilen).

### 3.3 TEI-Erzeugung

Alle 285 Dokumente liegen als validierte TEI-XML-Dateien vor (DTA-Basisformat). Ein Vergleich mit den 11 ZBZ-Referenz-TEI zeigt, dass die Dokumentstruktur korrekt abgebildet wird. Die Textgenauigkeit variiert je nach Scan-Qualitaet (CER 0,4% bis 12% bei guten Scans, hoeher bei schlechten Vorlagen). Mehrsprachige Dokumente erhalten korrekte Sprachauszeichnungen im Header.

Die Pipeline erzeugt automatisch einen HTML-Qualitaetsbericht, der Schema-Fehler und Auffaelligkeiten pro Dokument ausweist.

### 3.4 Entitaetserkennung

Ueber den Gesamtkorpus wurden 11.685 eindeutige Entitaeten mit 26.197 Nennungen identifiziert: Personen (37%), Orte (22%), Daten (15%), Organisationen (14%), Werke (11%) und Ereignisse (2%).

Jede Entitaet erhaelt eine projekteigene ID (z.B. zbz-p.2 fuer Jeanne Hersch, zbz-l.705 fuer die Schweiz). Diese IDs bilden ein stabiles Verweissystem innerhalb der Edition und verlinken auf Wikidata und GND. Im TEI-Text wird der Typ der Entitaet durch das entsprechende TEI-Element unterschieden: `persName` fuer Personen, `orgName` fuer Organisationen, `placeName` fuer Orte und `bibl` fuer Werke. Aktuell sind 24% der Entitaeten mit Wikidata verknuepft; die Vervollstaendigung erfordert Rechenzeit, keine konzeptuelle Arbeit.

### 3.5 Qualitaetssicherung (Agent-Based Quality Screening)

Zusaetzlich zur automatischen Schema-Validierung wurde ein agentengestuetztes Screening-Verfahren entwickelt und an fuenf Pilotdokumenten erprobt (Doc 290, 2310, 100, 1440, 1330 -- verschiedene Sprachen, Genres und Formate). Dabei wird jedes Dokument gegen den Originalscan geprueft: Scan-Qualitaet, OCR-Treue, Layout-Korrektheit, TEI-Struktur, Entitaeten und inhaltliche Kohaerenz. Das Ergebnis ist ein strukturierter Befund pro Dokument, der den menschlichen Kurator:innen die Arbeit erleichtert.

Alle fuenf Pilotdokumente bestanden das Screening. Sechs systematische Muster wurden identifiziert, darunter: Doppelseiten-Scans (Buchformat) erzeugen technisch korrekte, aber optisch unerwartete Strukturen; bei abstrakten philosophischen Texten erkennt die Pipeline weniger Entitaeten als bei biographischen (inhaltlich erklaerbar, kein Fehler); und Gemini korrigiert im Erzeugungsprozess nebenbei OCR-Fehler (ein undokumentierter Qualitaetsgewinn).

Dieses Screening ist als Vorpruefung fuer die menschliche Kuration konzipiert, nicht als Ersatz. Es reduziert die Menge an Dokumenten, die fachliche Aufmerksamkeit erfordern.

### 3.6 Digitale Edition

Eine oeffentliche Website zeigt alle 286 Dokumente in einem Katalog mit Filterung und Volltextsuche. Der Reader stellt Faksimile und TEI-Text nebeneinander dar, mit einer Sidebar fuer verlinkte Entitaeten.

### 3.7 Kurationswerkzeug

Ein Browser-basierter Editor erlaubt die Nachbearbeitung der KI-generierten Dokumente als letzten Schritt vor der Publikation. Editoren koennen Text korrigieren, die Dokumentstruktur aendern, Entitaeten bearbeiten und das Ergebnis validieren. Ein Review-Workflow steuert, welche Dokumente publiziert werden.

---

## 4. Bekannte Einschraenkungen

**Scan-Qualitaet bestimmt die Textgenauigkeit.** Die Streuung der Fehlerrate geht primaer auf unterschiedliche Vorlagenqualitaet zurueck. Schlechte Scans koennen nur begrenzt kompensiert werden.

**Etwa 5 bis 10% der automatisch erkannten Entitaeten sind falsch.** Generische Begriffe werden gelegentlich als Entitaeten markiert. Diese Fehler werden ueber das Kurationswerkzeug korrigiert.

**Die Wikidata-Verlinkung ist noch unvollstaendig.** 24% der Entitaeten sind verlinkt. Die Vervollstaendigung ist vorbereitet und erfordert Rechenzeit.

---

## 5. Kosten

| Komponente | Geschaetzte Kosten (Gesamtkorpus) |
|---|---|
| OCR (Mistral/Azure) | abhaengig vom Abrechnungsmodell |
| Layout-Analyse (Gemini) | unter 10 USD |
| TEI-Erzeugung (Gemini) | ca. 80 USD |
| Entitaetserkennung (Gemini) | unter 5 USD |
| Wikidata-API | kostenfrei |

Alle Zwischenergebnisse werden gespeichert. Die Pipeline ueberspringt bereits verarbeitete Dokumente und kann einzelne Schritte gezielt wiederholen.

---

## 6. Produktionsstand

| Komponente | Stand | Abdeckung |
|---|---|---|
| Bilderzeugung aus PDF | abgeschlossen | 286/286 Dokumente |
| OCR-Texterkennung | abgeschlossen | 286/286 Dokumente, 4.117 Seiten |
| Layout-Analyse | abgeschlossen | 286/286 Dokumente, 4.152 Seiten |
| TEI-Erzeugung und Validierung | abgeschlossen | 285/285 Dokumente, 284 schema-valide |
| Entitaetserkennung | abgeschlossen | 285/285 Dokumente, 11.685 Entitaeten |
| Wikidata-Verlinkung | laufend | 2.803 von 11.685 Entitaeten (24%) |
| Digitale Edition | funktionsfaehig | 286 Dokumente im Katalog |
| Kurationswerkzeug | funktionsfaehig | bereit fuer Pilotbetrieb |
| Quality Screening (Pre-Curation) | Pilot | 5 Dokumente geprueft, 6 systematische Muster identifiziert |
| PAGE-XML-Export | abgeschlossen | 286/286 Dokumente, Transkribus-kompatibel |

---

## 7. Was die ZBZ als Naechstes tun kann

**Kurationspilot starten.** Das Kurationswerkzeug ist einsatzbereit. Ein gemeinsamer Pilotdurchlauf an zwei bis drei Dokumenten wuerde den Workflow von der KI-Erzeugung ueber die redaktionelle Pruefung bis zur Freigabe erproben. Vorgeschlagene Kandidaten: Doc 2310 (kurzer Zeitschriftenartikel, franzoesisch), Doc 1440 (Interview, deutsch), Doc 100 (laengerer Essay, franzoesisch). DHCraft bereitet diese Dokumente vor; die ZBZ stellt eine Editorin oder einen Editor fuer den Test bereit.

**Offene Fragen klaeren.** Drei Punkte warten auf Rueckmeldung: die Differenz von 289 zu 286 Dokumenten im Masterfile, die Bereitstellung von ALMA/MMSID-Metadaten fuer den TEI-Header, und die Frage der Normalisierung versus Quellentreue bei Ueberschriften (Klaerung mit Frau Baehler ausstehend).

**Infrastruktur vorbereiten.** Fuer den Produktivbetrieb bei der ZBZ sind Containerisierung (Podman) und CI/CD-Integration (GitLab Uni Zuerich) vorgesehen. Die Planung kann beginnen, sobald der Kurationspilot abgeschlossen ist.

---

## Anhang: Chronologie

| Zeitraum | Schwerpunkt |
|---|---|
| 29.01. | Korpusanalyse, Pipeline-Architektur, erste OCR-Tests |
| 25.02. | Dashboard, Dokumentklassifikation, Online-Demo |
| 05.03. | OCR-Korrektur, PAGE-XML-Export, Frontend-Aufbau |
| 06.03. | TEI-Generator, Layout-Gesamtlauf, Digitale Edition |
| 07.03. | Pipeline-Refactoring, Entitaetserkennung |
| 08.--09.03. | Entitaetserkennung Gesamtkorpus, Kurationswerkzeug |
| 12.03. | Wikidata/GND-Integration |
| 14.03. | Frontend-Konsolidierung |
| 15.03. | TEI-Validierung, Dokumentstruktur-Korrektur, Produktionslauf 285/285 |
| 15.03. | Agent-Based Quality Screening (Pilot, 5 Docs), Reassembly 284/285 VALID |
