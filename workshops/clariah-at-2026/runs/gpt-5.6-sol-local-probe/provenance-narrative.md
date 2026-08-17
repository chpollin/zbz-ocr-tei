# Provenienz-Narrativ

## Gegenstand

Die lokale Probe dokumentiert eine vierstufige Verarbeitung zweier Faksimileseiten: vollständige multimodale Transkription, offene Themenbaseline, generische JSON-Strukturierung und forschungsfragengeleitete Evidenzannotation. Die Rohoutputs bleiben eigenständige Artefakte. Dieses Dokument beschreibt ihre Beziehungen und wiederholt ihren Inhalt nicht.

## Aktivitätskette

1. `01-transcription.txt` wurde mit den beiden Bilddateien als primären Inputs ausgeführt. Der gespeicherte Output umfasst die vollständigen Seiten p003 und p004.
2. `02-baseline-topics.txt` erhielt ausschließlich diese vollständige Transkription. Der Textoutput zeigt die thematische Vermischung der angrenzenden Beiträge als beobachtbaren Scope-Befund.
3. `03-schema-topics.txt` erhielt dieselbe Transkription und den generischen Strukturvertrag. Der JSON-Output strukturiert den vollständigen Seitenscope; eine fachliche Forschungsfrage und ein Codebuch waren in diesem Lauf nicht verfügbar.
4. `04-evidence-annotation.txt` erhielt zusätzlich die exakte Forschungsfrage, das Codebuch und die Hersch-Segmentgrenze. Der JSON-Output enthält ausschließlich Evidenz aus diesem Segment.
5. Ein `gpt-5.6-sol`-Agent sichtete beide Faksimiles, verglich Hersch-Textanker und Segmentgrenzen und führte automatisierte Zeichenfolgen- und Page-ID-Prüfungen aus. Das Ergebnis ist `examples/transcription-agent-verified.md`. Diese Vorprüfung ist kein personengebundener menschlicher Source-Review.
6. `examples/annotation-example.json` überträgt die agentisch geprüften Anker auf ein strukturiertes Muster. Seine Quellenprüfstatus bleiben `unchecked`; seine Claims bleiben fachlich `unreviewed`.

## Verantwortungsgrenzen

Die Modellläufe erzeugen Vorschläge und initialisieren `source_check_status: unchecked` sowie `review_status: unreviewed`. Die Rolle `gpt-5.6-sol_agentic_checker` beschreibt die tatsächlich ausgeführte visuelle und automatisierte Vorprüfung. Sie erfüllt die im Codebuch verlangte menschliche Prüfung nicht. Eine fachliche Annahme oder Ablehnung von Claims liegt bei einem Critical Expert und ist in der Probe nicht erfolgt.

Das Schema erlaubt `review_status: accepted` oder `review_status: rejected` ausschließlich zusammen mit `source_check_status: source_checked`. Bei `unchecked` und `source_mismatch` bleibt der Reviewstatus `unreviewed`.

## Dokumentierte Abweichungen

Der agentisch verifizierte Hersch-Referenztext dokumentiert die Bildlesung `contrebalance` gegenüber `contrebalancé` im Repo-Markdown. Im unverifizierten Bandelier-Bereich enthält der rohe Transkriptionsoutput `inadaption scolaire`; der Faksimilebefund deutet auf `inadaptation scolaire`. Diese zweite Abweichung wird nicht im Rohoutput korrigiert, weil der Antwortkörper bytegetreu erhalten bleibt und der Bandelier-Bereich außerhalb der agentischen Detailprüfung liegt.

## Offene Critical-Expert-Gates

`critical-expert-gates.json` serialisiert fünf noch unentschiedene Gegenstände: Forschungsfrage, Codebuch, Musterannotation, didaktische Scopegrenze und Evidenzstatus von `political_neutrality`. Das Forschungsfragen-Gate hält zusätzlich den ungeklärten Zusammenhang zwischen der Einleitung als Exposé von Jeanne Hersch und der sichtbaren Schlusssignatur `Jean Fluck.` fest. Für `political_neutrality` liegt der Vorschlag vor, `evidence_status` von `direct` auf `indirect` zu ändern, weil der Claim die institutionelle Funktion der Neutralität interpretiert. Der gespeicherte Rohoutput bleibt bei `direct`.

## Nachweisgrenzen

Die lokale Laufzeit stellte Temperatur, `top_p`, Seed und Reasoning-Effort nicht bereit. Request-ID, Response-ID, API-Protokoll, Transportmetadaten und vollständige Request-/Response-Envelopes wurden ebenfalls nicht exponiert und werden nicht rekonstruiert. Für Schema und Codebuch existiert kein separat archivierter Byte-Snapshot der ursprünglichen Request-Envelopes; `provenance.json` bindet deshalb den aktuellen validierten Vertragsstand über SHA-256 und kennzeichnet die fehlenden Generation-Snapshots ausdrücklich. Nachgewiesen sind die gespeicherten Prompt- und Outputdateien über SHA-256, die angegebenen lokalen Inputs, der Repository-Anker sowie die reproduzierbaren Schema-, Zitat-, Segment- und Statustests.

Die Bandelier- und Illich-Passagen bleiben `unverifiziert`. Die institutionelle Rechteklärung und der fachliche Review der Claims sind offen.
