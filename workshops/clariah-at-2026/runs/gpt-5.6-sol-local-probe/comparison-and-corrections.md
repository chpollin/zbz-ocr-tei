# Vergleichs- und Korrekturprotokoll

## Run-Identität

- Modell: `gpt-5.6-sol`
- Datum: 2026-08-17
- Kontext: lokale Codex-Subagent-Probe
- Gemini-Output: nein
- Quellen-Repository-Anker: `1115ed24cbaf97a64093d9b0e839271b60a2d950`
- Modellparameter: von der lokalen Laufzeit nicht offengelegt
- Speicherung: Antwortkörper ohne Code-Fences oder redaktionelle Normalisierung bytegetreu in den Outputdateien

## Gemeinsamer Seiteneingang

Prompt 01 verwendet die Faksimiles `docs/images/1000/1000_p003.png` und `docs/images/1000/1000_p004.png` als primäre multimodale Eingabe. Die neue Transkription bewahrt die vollständigen Seiten. Sie enthält drei angrenzende Beitragsbereiche:

1. den auf p003 fortgesetzten Beitrag von M. Bandelier;
2. den Beitrag von Jeanne Hersch ab seiner Überschrift auf p003 bis zur Signatur `Jean Fluck.` auf p004;
3. den auf p004 beginnenden Beitrag zu Ivan Illich bis zum sichtbaren Seitenende.

Die Annotationsläufe 02, 03 und 04 erhalten dieselbe vollständige Transkription. Prompt 04 ist der erste Lauf, der den Hersch-Beitrag durch Start- und Endanker analytisch abgrenzt.

## Getrennte Prüfstatus

`examples/transcription-agent-verified.md` enthält ausschließlich den agentisch visuell und automatisiert geprüften Hersch-Abschnitt. Die Prüfung umfasste Faksimile-Sichtung, Zeichenfolgenabgleich, Page-IDs und Segmentgrenzen. Ein personengebundener menschlicher Source-Review wurde nicht ausgeführt; das Referenzobjekt trägt deshalb `source_check_status: unchecked`.

Der rohe vollständige Seitenoutput aus Prompt 01 trägt `unchecked`. Die Bandelier- und Illich-Passagen außerhalb des Hersch-Kontrolltexts bleiben entsprechend dem Projektstatus `unverifiziert`. Ihre Präsenz ist für den didaktischen Scope-Vergleich erforderlich; sie wird nicht als abgeschlossene Quellenprüfung ausgegeben.

Im Hersch-Abschnitt bleibt die dokumentierte Abweichung zwischen Repo-Markdown und Bildlesung bestehen:

| Stelle | Repo-Markdown | Bildlesung im Hersch-Kontrolltext | Entscheidung |
|---|---|---|---|
| p004, Vielfalt der Lehrpersonen | `contrebalancé` | `contrebalance` | agentische Bildlesung im Hersch-Referenztext dokumentiert; menschlicher Source-Review offen. |

Im außerhalb des Hersch-Segments liegenden Bandelier-Text enthält der bytegetreue Rohoutput `inadaption scolaire`. Der agentische Faksimilebefund deutet auf `inadaptation scolaire`. Die Stelle bleibt im Rohoutput unverändert; eine menschliche Prüfung ist offen.

## Vergleich der Extraktionsläufe

### Lauf 02: offene Textbaseline

Prompt 02 kennt weder Beitragsscope, Forschungsfrage, Codebuch noch Schema. Die Textantwort bildet deshalb Themen über alle drei Beitragsbereiche. `School as a disciplinary mass institution` verbindet beispielsweise Bandeliers Diagnose der Schulkaserne mit der auf p004 beginnenden Illich-Darstellung. Named Entities umfassen Personen und Institutionen aus allen sichtbaren Beiträgen.

Dieser Befund zeigt Scope-Kontamination als Folge eines nicht abgegrenzten Inputs. Er ist für den Vergleich erwünscht und wird nicht nachträglich aus dem Rohoutput entfernt.

### Lauf 03: generischer Strukturvertrag

Prompt 03 ergänzt ausschließlich `annotation.schema.json`. Das Schema erzwingt Felder, Datentypen, Seiten-IDs und getrennte Statusachsen, enthält aber keine Forschungsfrage, Beitragsgrenze oder kontrollierte Themenliste. `research_question` dokumentiert deshalb `unspecified in this run`; `dataset_id` bezeichnet die vollständigen Seiten.

Der JSON-Lauf strukturiert weiterhin beitragsübergreifende Themen. Das Schema erhöht technische Vergleichbarkeit, löst den analytischen Scope aber nicht selbstständig.

### Lauf 04: forschungsfragengeleitete Evidenzannotation

Prompt 04 ergänzt erstmals die exakte Forschungsfrage, die Hersch-Segmentgrenze und `codebook.md`. Der Output verwendet ausschließlich Hersch-Evidenz. Bandelier-, Illich-, Oury- und Verne-Passagen erscheinen weder als Entitäten noch als Themenbelege. Die fünf Codebuchthemen werden als Claim-Einheiten mit exakten Zitaten, Page-IDs sowie getrennten Evidenz-, Quellenprüf- und Reviewstatus ausgegeben.

## Modell- und Reviewstatus

Die JSON-Rohoutputs 03 und 04 beginnen vollständig mit `source_check_status: unchecked` und `review_status: unreviewed`. Lauf 02 ist eine offene Textbaseline und besitzt diese Schemafelder nicht. `examples/annotation-example.json` ist ein agentisch geprüftes Muster und bleibt ebenfalls `unchecked` und `unreviewed`. Eine fachliche Annahme oder Ablehnung der Claims ist in keinem Rohoutput vorweggenommen.

## Neu ausgeführte Antworten

Die Antworten 02, 03 und 04 wurden nach der Korrektur ihrer jeweiligen Prompts erneut mit `gpt-5.6-sol` erzeugt. Die Prompt-Prüfsummen und Output-Prüfsummen stehen in `input/metadata.json` und `provenance.json`. Temperatur, `top_p`, Seed und Reasoning-Effort waren in der lokalen Subagent-Laufzeit nicht verfügbar und sind deshalb als `null` dokumentiert.

Request-ID, Response-ID, Transportmetadaten und vollständige Request-/Response-Envelopes wurden von der Laufzeit nicht exponiert. Sie werden nicht rekonstruiert. `provenance-narrative.md` dokumentiert die Aktivitätskette und diese Nachweisgrenze, ohne die Rohoutputs zu duplizieren.

## Fachliche Gates

`critical-expert-gates.json` serialisiert die offenen Entscheidungen zu Forschungsfrage, Codebuch, Musterannotation, didaktischer Scopegrenze und `political_neutrality`. Für die letzte Annotation wurde vorgeschlagen, den Evidenzstatus `direct` als `indirect` zu klassifizieren. Alle fünf Gates bleiben `unreviewed`; der operative Korrekturlauf verändert den Rohoutput nicht.
