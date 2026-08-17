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

Die Rubrik in [evaluation-rubric.md](evaluation-rubric.md) prüft Scope-Kontamination, Segmentgrenzen, Entity-Felder, Themenpassung, exakte Zitate und Statusdisziplin. [examples/transcription-source-checked.md](examples/transcription-source-checked.md) ist der visuell geprüfte Hersch-Kontrolltext. [examples/annotation-example.json](examples/annotation-example.json) zeigt einen nachgelagerten Source-Check; es ist kein unveränderter Modelloutput.

## Gemeinsamer JSON-Vertrag

[schema/annotation.schema.json](schema/annotation.schema.json) verlangt auf oberster Ebene:

- `run_metadata`: Modell, Datum, Promptdatei und Ausführungskontext
- `entities`: benannte Entitäten mit Surface, normalisiertem Label, Typ, Seite, Beleg und optionaler Kennung
- `topic_annotations`: Themen oder Claims mit Definition, Aussage und Evidenz

Jede Entity und Themenannotation trennt drei Dimensionen:

- `evidence_status`: `direct | indirect | ambiguous`
- `source_check_status`: `unchecked | source_checked | source_mismatch`
- `review_status`: `unreviewed | accepted | rejected`

`research_question` ist ein Pflichtfeld, damit der Analysekontext jedes strukturierten Laufs sichtbar bleibt. Lauf 03 dokumentiert das Fehlen einer Forschungsfrage durch `unspecified in this run`; Lauf 04 enthält die exakte Forschungsfrage.

`direct` bezeichnet einen expliziten Beleg. `indirect` bezeichnet eine nachvollziehbare Synthese oder Interpretation. `ambiguous` bezeichnet konkurrierende oder noch unzureichende Zuordnungen.

`source_checked` bestätigt ausschließlich Textanker, exaktes Zitat und Seite. `source_mismatch` dokumentiert eine nicht auflösbare Abweichung zur Quelle. `accepted` und `rejected` sind fachliche Entscheidungen.

Alle Modelloutputs beginnen mit `unchecked` und `unreviewed`. Das Schema enthält kein Confidence-Feld und weist zusätzliche Felder zurück.

## Dokumentierte lokale Modellprobe

`runs/gpt-5.6-sol-local-probe/` enthält eine lokale Probe vom 17. August 2026:

- Modell: `gpt-5.6-sol`
- Ausführung: lokale Codex-Probe
- Gemini-Output: nein
- Primäre Transkriptionsinputs: die echten Faksimiles p003 und p004
- Abfolge: Transkription, offene Textbaseline, induktiver Schema-Lauf, forschungsfragengeleitete Evidenzannotation

Die strukturierten Rohoutputs 03 und 04 beginnen mit den ungeprüften Statuswerten. Lauf 02 besitzt als offene Textbaseline keine Statusfelder. `comparison-and-corrections.md` dokumentiert die visuelle Prüfung und den Vergleich der drei Extraktionsmodi. `validation-report.md` hält maschinelle und manuelle Prüfungen fest. `provenance.json` dokumentiert Modell, Promptdateien, Prüfsummen, Inputs und Abhängigkeiten.

## Validierung

Vom Repository-Root:

```powershell
python -m json.tool workshops/clariah-at-2026/schema/annotation.schema.json > $null
python -m json.tool workshops/clariah-at-2026/examples/annotation-example.json > $null
python -c "import json; from jsonschema import Draft202012Validator; s=json.load(open('workshops/clariah-at-2026/schema/annotation.schema.json', encoding='utf-8')); d=json.load(open('workshops/clariah-at-2026/examples/annotation-example.json', encoding='utf-8')); Draft202012Validator.check_schema(s); Draft202012Validator(s).validate(d); print('schema and example valid')"
```

Dasselbe Schema validiert die beiden JSON-Rohoutputs 03 und 04 im Run-Ordner. Die Validierung prüft zusätzlich, dass Lauf 03 den Platzhalter und Lauf 04 die exakte Forschungsfrage enthält. Negative Tests müssen alte Statuswerte, falsche Seiten-IDs, zusätzliche Confidence-Felder und unzulässige Zusatzfelder zurückweisen.

## Rechte

Der Rechtestatus lautet `zu prüfen`. Öffentliche Erreichbarkeit im Projektviewer belegt keine freie Nachnutzung. Die Faksimiles und daraus abgeleitete Datensätze dürfen erst nach institutioneller Rechteklärung weitergegeben oder neu veröffentlicht werden.
