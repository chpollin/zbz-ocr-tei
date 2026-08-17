# CLARIAH-AT 2026: multimodale Quellenanalyse

Dieses Hands-on-Paket verbindet eine bildbasierte Transkription mit drei aufeinander aufbauenden Extraktionsläufen. Die Läufe machen sichtbar, wie Forschungsfrage, Datenstruktur und Codebuch das Ergebnis verändern.

## Forschungsfrage

`How does Jeanne Hersch define the institutional conditions under which schools can foster critical judgement?`

## Dokumentierter Pilotdatensatz

Der Pilot beginnt mit zwei vollständigen Seiten aus Dokument `1000`:

- Primäre Modelleingabe: `docs/images/1000/1000_p003.png` und `docs/images/1000/1000_p004.png`
- Scan-Seiten: `1000_p003` und `1000_p004`
- Gedruckte Seiten: 965 und 966
- Analytischer Start des Hersch-Segments: `L'ÉCOLE, LIEU DE RENCONTRE DE MÉMOIRE ET D'INVENTION`
- Analytisches Ende exklusiv: `POURQUOI IVAN ILLICH VEUT-IL DÉSCOLARISER LA SOCIÉTÉ ?`

Die Transkription sowie die Läufe 02 und 03 verwenden beide Seiten vollständig. Damit bleiben der vorangehende Bandelier-Text und der auf p004 beginnende Illich-Text zunächst im Input. Erst Lauf 04 setzt die Hersch-Grenze als explizite Forschungsentscheidung. [source-manifest.csv](source-manifest.csv) dokumentiert Bilder, Kontrolltexte, Seiten, Commit, Prüfsummen, Projektstatus und Rechtehinweis. Der Hersch-Kontrolltext ist source-checked; die außerhalb dieses Segments liegenden Passagen bleiben im Projektstatus `unverifiziert`.

## Ausführungsfolge

### 1. Multimodale Transkription

[prompts/01-transcription.txt](prompts/01-transcription.txt) wird zusammen mit den beiden Faksimiles an ein multimodales Modell übergeben. Die Bilder sind die primäre Eingabe. Die Markdown-Dateien unter `docs/data/pages/1000/` dürfen erst nach dem Bildlauf verwendet werden, um Textanker und Seitenzuordnung zu prüfen.

Ausgabe: vollständige Markdown-Transkription beider Seiten mit `source_check_status: unchecked` und `review_status: unreviewed`.

### 2. Offene Themenbaseline

[prompts/02-baseline-topics.txt](prompts/02-baseline-topics.txt) erhält ausschließlich die vollständige Seitentranskription. Der Lauf kennt weder Forschungsfrage noch Beitragsscope, Codebuch oder JSON-Schema.

Ausgabe: frei formulierte Entitäten und induktive Themen als lesbarer Text.

### 3. Schema-gestützte Themenextraktion

[prompts/03-schema-topics.txt](prompts/03-schema-topics.txt) erhält dieselbe vollständige Seitentranskription und [schema/annotation.schema.json](schema/annotation.schema.json). Eine Forschungsfrage, Beitragsgrenze und [codebook.md](codebook.md) werden nicht bereitgestellt. Der Lauf bildet weiterhin induktive Themen, muss sie nun aber in einen einheitlichen Datenvertrag schreiben.

Ausgabe: Entitäten und induktive Themen als valides JSON; `research_question` trägt den dokumentierten Platzhalter `unspecified in this run`.

### 4. Evidenzannotation

[prompts/04-evidence-annotation.txt](prompts/04-evidence-annotation.txt) erhält ebenfalls die vollständige Seitentranskription und führt erstmals die exakte Forschungsfrage, die Hersch-Segmentgrenze und [codebook.md](codebook.md) ein. Der Lauf zerlegt die Antwort in überprüfbare Claims. Jeder Claim erhält exakte Zitate, Seiten-IDs und getrennte Statusangaben für Evidenz, Quellenprüfung und fachliche Entscheidung.

Ausgabe: claim-orientierte Entitäten und Themen in demselben JSON-Schema.

### 5. Quellenprüfung und Vergleich

Die Rubrik in [evaluation-rubric.md](evaluation-rubric.md) prüft Scope-Kontamination, Segmentgrenzen, Entity-Felder, Themenpassung, exakte Zitate und Statusdisziplin. Sie enthält außerdem den ausgefüllten Vergleich aller vier Läufe. [examples/transcription-source-checked.md](examples/transcription-source-checked.md) ist der visuell geprüfte Hersch-Kontrolltext. [examples/annotation-example.json](examples/annotation-example.json) zeigt einen nachgelagerten Source-Check; es ist kein unveränderter Modelloutput. Pfad, SHA-256, Prüfaktivität und verantwortliche Rolle beider Referenzartefakte stehen in [source-manifest.csv](source-manifest.csv) und `provenance.json`.

## Gemeinsamer JSON-Vertrag

[schema/annotation.schema.json](schema/annotation.schema.json) verlangt auf oberster Ebene:

- `run_metadata`: Modell, Datum, Promptdatei und Ausführungskontext
- `entities`: benannte Entitäten mit Surface, normalisiertem Label, Typ, Seite, Beleg und optionaler Kennung
- `topic_annotations`: Themen oder Claims mit Definition, Aussage und Evidenz

Das Schema trägt den stabilen lokalen Identifier `urn:dhcraft:clariah-at-2026:annotation-schema:2.0`. `local_probe` und `gemini_output` sind reguläre Boolean-Provenienzfelder; ihre Werte beschreiben den jeweiligen Lauf und werden nicht durch das Schema vorgegeben.

Jede Entity und Themenannotation trennt drei Dimensionen:

- `evidence_status`: `direct | indirect | ambiguous`
- `source_check_status`: `unchecked | source_checked | source_mismatch`
- `review_status`: `unreviewed | accepted | rejected`

`research_question` ist ein Pflichtfeld, damit der Analysekontext jedes strukturierten Laufs sichtbar bleibt. Lauf 03 dokumentiert das Fehlen einer Forschungsfrage durch `unspecified in this run`; Lauf 04 enthält die exakte Forschungsfrage.

`direct` bezeichnet einen expliziten Beleg. `indirect` bezeichnet eine nachvollziehbare Synthese oder Interpretation. `ambiguous` bezeichnet konkurrierende oder noch unzureichende Zuordnungen.

`source_checked` bestätigt ausschließlich Textanker, exaktes Zitat und Seite. `source_mismatch` dokumentiert eine nicht auflösbare Abweichung zur Quelle. `accepted` und `rejected` sind fachliche Entscheidungen.

Eine Annotation mit `source_check_status: source_mismatch` darf nicht zugleich `review_status: accepted` tragen. Das Schema weist diese Kombination zurück.

Der Transkriptionsoutput sowie die strukturierten Modelloutputs 03 und 04 beginnen mit `unchecked` und `unreviewed`. Lauf 02 besitzt als offene Textbaseline keine Statusfelder. Das Schema enthält kein Confidence-Feld und weist zusätzliche Felder zurück.

## Dokumentierte lokale Modellprobe

`runs/gpt-5.6-sol-local-probe/` enthält eine lokale Probe vom 17. August 2026:

- Modell: `gpt-5.6-sol`
- Ausführung: lokale Codex-Probe
- Gemini-Output: nein
- Primäre Transkriptionsinputs: die echten Faksimiles p003 und p004
- Abfolge: Transkription, offene Textbaseline, induktiver Schema-Lauf, forschungsfragengeleitete Evidenzannotation

Die strukturierten Rohoutputs 03 und 04 beginnen mit den ungeprüften Statuswerten. Lauf 02 besitzt als offene Textbaseline keine Statusfelder. `comparison-and-corrections.md` dokumentiert die visuelle Prüfung und den Vergleich der drei Extraktionsmodi. `validation-report.md` hält maschinelle und manuelle Prüfungen fest. `provenance.json` dokumentiert Modell, Promptdateien, Prüfsummen, Inputs und Abhängigkeiten. `provenance-narrative.md` erklärt die Aktivitätskette, Verantwortungsgrenzen und Nachweislücken, ohne Rohoutputs zu wiederholen.

## Vollständiger Wiederholungsablauf

1. Repository-Anker und SHA-256 der beiden Bilder in `source-manifest.csv` prüfen.
2. Prompt 01 zusammen mit `docs/images/1000/1000_p003.png` und `docs/images/1000/1000_p004.png` an ein multimodales Modell übergeben. Den vollständigen Antwortkörper unverändert als Lauf-01-Output speichern.
3. Prompt 02 ausschließlich mit dem vollständigen Lauf-01-Output ausführen. Keine Forschungsfrage, Segmentgrenze, kein Schema und kein Codebuch ergänzen. Die Textantwort unverändert speichern.
4. Prompt 03 mit demselben vollständigen Lauf-01-Output und `schema/annotation.schema.json` ausführen. Weder eine fachliche Forschungsfrage oder Segmentgrenze noch ein Codebuch ergänzen. Die JSON-Antwort unverändert speichern.
5. Prompt 04 mit demselben vollständigen Lauf-01-Output, Schema und Codebuch ausführen. Forschungsfrage und Hersch-Segmentgrenze stammen aus dem Prompt. Die JSON-Antwort unverändert speichern.
6. Modellname, Datum, verfügbare Modellparameter sowie SHA-256 der Prompts und Outputs in `input/metadata.json` und `provenance.json` eintragen. Nicht exponierte Parameter und Request-/Response-Protokolle als nicht verfügbar dokumentieren; keine Werte rekonstruieren.
7. Den Hersch-Abschnitt gegen beide Faksimiles prüfen. Source-Check und fachlichen Review getrennt dokumentieren. Referenzartefakte mit Pfad, SHA-256, Aktivität und Prüfrolle an Manifest und Provenienz binden.
8. Die Gesamtsuite vom Repository-Root ausführen und den Bericht nur bei `ALL CHECKS PASS` aktualisieren.

## Validierung

Voraussetzung ist Python mit dem Paket `jsonschema`. Vom Repository-Root führt ein Befehl die JSON-, Schema-, Datums-, Zitat-, Segment-, Status-, Provenienz-, Manifest- und Negativtests aus:

```powershell
python workshops/clariah-at-2026/validate.py
```

Erwartete Schlusszeile: `ALL CHECKS PASS`. Die Validierung verwendet einen Format-Checker für echte Kalenderdaten. Sie prüft zusätzlich, dass Lauf 03 den Platzhalter und Lauf 04 die exakte Forschungsfrage enthält. Negative Tests erfassen alte Statuswerte, falsche Seiten-IDs, zusätzliche Confidence-Felder, unzulässige Zusatzfelder, ungültige Datumswerte und widersprüchliche Source-/Reviewstatus.

## Offene fachliche Entscheidung

Der Vorschlag, den Evidenzstatus von `political_neutrality` von `direct` auf `indirect` zu ändern, bleibt ein Critical-Expert-Gate. Der bytegetreue Rohoutput wird operativ nicht verändert.

## Rechte

Der Rechtestatus lautet `zu prüfen`. Öffentliche Erreichbarkeit im Projektviewer belegt keine freie Nachnutzung. Die Faksimiles und daraus abgeleitete Datensätze dürfen erst nach institutioneller Rechteklärung weitergegeben oder neu veröffentlicht werden.
