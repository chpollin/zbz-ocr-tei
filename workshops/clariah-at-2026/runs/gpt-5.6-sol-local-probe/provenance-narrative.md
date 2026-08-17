# Provenienz-Narrativ

## Gegenstand

Die lokale Probe dokumentiert eine vierstufige Verarbeitung zweier Faksimileseiten: vollständige multimodale Transkription, offene Themenbaseline, generische JSON-Strukturierung und forschungsfragengeleitete Evidenzannotation. Die Rohoutputs bleiben eigenständige Artefakte. Dieses Dokument beschreibt ihre Beziehungen und wiederholt ihren Inhalt nicht.

## Aktivitätskette

1. `01-transcription.txt` wurde mit den beiden Bilddateien als primären Inputs ausgeführt. Der gespeicherte Output umfasst die vollständigen Seiten p003 und p004.
2. `02-baseline-topics.txt` erhielt ausschließlich diese vollständige Transkription. Der Textoutput zeigt die thematische Vermischung der angrenzenden Beiträge als beobachtbaren Scope-Befund.
3. `03-schema-topics.txt` erhielt dieselbe Transkription und den generischen Strukturvertrag. Der JSON-Output strukturiert den vollständigen Seitenscope; eine fachliche Forschungsfrage und ein Codebuch waren in diesem Lauf nicht verfügbar.
4. `04-evidence-annotation.txt` erhielt zusätzlich die exakte Forschungsfrage, das Codebuch und die Hersch-Segmentgrenze. Der JSON-Output enthält ausschließlich Evidenz aus diesem Segment.
5. Ein menschlicher Source-Review prüfte Hersch-Textanker, Seitenzuordnung und Segmentgrenzen an den Faksimiles. Das Ergebnis ist `examples/transcription-source-checked.md`.
6. `examples/annotation-example.json` überträgt den Source-Check auf ein Muster strukturierter Annotationen. Seine Claims bleiben fachlich `unreviewed`.

## Verantwortungsgrenzen

Die Modellläufe erzeugen Vorschläge und initialisieren `source_check_status: unchecked` sowie `review_status: unreviewed`. Die Rolle `human_source_reviewer` verantwortet ausschließlich den Abgleich von Wortlaut, Seite und Segment. Eine fachliche Annahme oder Ablehnung von Claims liegt bei einem Critical Expert und ist in der Probe nicht erfolgt.

Das Schema verhindert die Kombination `source_check_status: source_mismatch` mit `review_status: accepted`. Damit kann ein nachgewiesener Quellenwiderspruch nicht zugleich als fachlich angenommene Annotation gespeichert werden.

## Dokumentierte Abweichungen

Der Hersch-Kontrolltext dokumentiert die Bildlesung `contrebalance` gegenüber `contrebalancé` im Repo-Markdown. Im unverifizierten Bandelier-Bereich enthält der rohe Transkriptionsoutput `inadaption scolaire`; der Faksimilebefund deutet auf `inadaptation scolaire`. Diese zweite Abweichung wird nicht im Rohoutput korrigiert, weil der Antwortkörper bytegetreu erhalten bleibt und der Bandelier-Bereich außerhalb des abgeschlossenen Source-Checks liegt.

## Offenes Critical-Expert-Gate

Für die Annotation `political_neutrality` liegt der Vorschlag vor, `evidence_status` von `direct` auf `indirect` zu ändern, weil der Claim die institutionelle Funktion der Neutralität interpretiert. Der gespeicherte Rohoutput bleibt bei `direct`. Die Entscheidung erfordert fachliche Abnahme und wird nicht durch eine operative Korrektur vorweggenommen.

## Nachweisgrenzen

Die lokale Laufzeit stellte Temperatur, `top_p`, Seed und Reasoning-Effort nicht bereit. Request-ID, Response-ID, API-Protokoll, Transportmetadaten und vollständige Request-/Response-Envelopes wurden ebenfalls nicht exponiert und werden nicht rekonstruiert. Nachgewiesen sind die gespeicherten Prompt- und Outputdateien über SHA-256, die angegebenen lokalen Inputs, der Repository-Anker sowie die reproduzierbaren Schema-, Zitat-, Segment- und Statustests.

Die Bandelier- und Illich-Passagen bleiben `unverifiziert`. Die institutionelle Rechteklärung und der fachliche Review der Claims sind offen.
