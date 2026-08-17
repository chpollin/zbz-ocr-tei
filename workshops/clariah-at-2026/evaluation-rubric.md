# Evaluationsrubrik

Die Rubrik vergleicht Transkription, offene Baseline, Schema-Lauf und Evidenzannotation. Jeder Punktwert bewertet eine beobachtbare Eigenschaft des Artefakts.

## Kriterien

| Kriterium | 2 Punkte | 1 Punkt | 0 Punkte |
|---|---|---|---|
| Bildbasierte Transkription | p003 und p004 sind als primäre multimodale Eingabe dokumentiert; Markdown dient erst dem Source-Check. | Eingaben sind dokumentiert, ihre Reihenfolge bleibt unklar. | Die Transkription wurde aus dem Markdown-Spiegel erzeugt. |
| Seitentreue | Transkription und Läufe 02/03 verwenden p003 und p004 vollständig; kein Beitrag wird stillschweigend ausgewählt. | Eine Randpassage fehlt ohne analytische Folge. | Hersch wird bereits vor Lauf 04 als Scope vorgegeben. |
| Analytische Segmenttreue | Lauf 04 beginnt mit der Hersch-Überschrift und endet vor der Illich-Überschrift. | Eine unkritische Randzeile liegt außerhalb des Segments. | Bandelier- oder Illich-Evidenz beantwortet die Forschungsfrage. |
| Offene Baseline | Prompt 02 erhält nur die vollständigen Seiten und enthält weder Beitragsscope, Forschungsfrage noch Schema, Themenliste oder Codebuchverweis. | Der Prompt enthält indirekte thematische oder strukturelle Lenkung. | Beitragsscope, Forschungsfrage, Schema oder kontrollierte Codes steuern die Baseline. |
| Strukturisolierung | Prompt 03 erhält dieselben vollständigen Seiten und das generische Schema; `research_question` dokumentiert `unspecified in this run`. | Einzelne fachliche Vorgaben bleiben implizit. | Beitragsscope, Forschungsfrage oder Codebuch steuern Lauf 03. |
| Scope-Kontamination als Befund | Die Outputs 02/03 machen die Vermischung benachbarter Beiträge sichtbar; Lauf 04 entfernt sie durch die explizite Grenze. | Der Vergleich dokumentiert die Vermischung nur teilweise. | Scope-Kontamination wird als Modellfehler behandelt oder im Lauf 04 übersehen. |
| Entity-Vertrag | Jede Entity enthält Surface, normalisiertes Label, Typ, Seite, Beleg und das geprüfte Kennungspaar. | Ein Feld ist unpräzise oder fehlt in Einzelfällen. | Entity-Angaben sind nicht auf Erwähnungen rückführbar. |
| Themenvertrag | Jede Themenannotation enthält ID, Label, Definition, Claim und Evidenz. | Definition oder Claim bleibt zu breit. | Thema und Claim sind nicht getrennt oder Evidenz fehlt. |
| Zitatgenauigkeit | Jedes Zitat ist auf der angegebenen Seite und im Source-Check-Text exakt auffindbar. | Kleine normalisierte Abweichungen sind dokumentiert. | Zitat ist erfunden, paraphrasiert oder der falschen Seite zugewiesen. |
| Evidenzstatus | `direct`, `indirect` und `ambiguous` werden gemäß ihrer semantischen Funktion verwendet. | Einzelne Statuswerte sind zu eindeutig oder zu unbestimmt. | Evidenzstatus fehlt oder fungiert als Sicherheitsskala. |
| Quellenprüfstatus | Modelloutputs beginnen `unchecked`; `source_checked` oder `source_mismatch` beruhen auf dokumentierter Quellenprüfung. | Der Prüfweg ist vorhanden, aber lückenhaft. | Das Modell erklärt seine eigene Ausgabe für source-checked. |
| Fachlicher Review | Modelloutputs beginnen `unreviewed`; `accepted` oder `rejected` beruhen auf fachlicher Entscheidung. | Entscheidung ist dokumentiert, aber nicht klar einer Rolle zugeordnet. | Quellenprüfung und fachliche Annahme werden vermischt. |
| Schema und Provenienz | JSON validiert; Modell, Datum, Promptdatei, lokaler Kontext und Nicht-Gemini-Status sind dokumentiert. | Ein Provenienzfeld ist inkonsistent. | Ausgabe ist nicht schemafähig oder gibt ihre Herkunft falsch an. |

Maximal sind 26 Punkte erreichbar.

## Interpretation

- 23 bis 26 Punkte: technisch und quellenbezogen für den Pilotvergleich geeignet
- 17 bis 22 Punkte: gezielte Quellen- oder Schema-Nachprüfung erforderlich
- 0 bis 16 Punkte: erneuter Lauf oder grundlegende Revision erforderlich

Die fachliche Annahme einzelner Claims erfolgt unabhängig von der technischen Punktzahl.

## Dokumentierter Vergleich der vier Läufe

Die folgende Tabelle trennt automatisch oder durch Artefaktinspektion messbare Eigenschaften von fachlichen Wertungen. `unreviewed` bedeutet, dass noch keine Entscheidung durch einen Critical Expert vorliegt.

| Eigenschaft | Lauf 01: Transkription | Lauf 02: offene Baseline | Lauf 03: Schema-Lauf | Lauf 04: Evidenzannotation |
|---|---|---|---|---|
| Primärer Input | zwei Faksimiles | vollständiger Output 01 | vollständiger Output 01 + generisches Schema | vollständiger Output 01 + Schema + Codebuch + Forschungsfrage + Segmentgrenze |
| Ausgabeformat | Markdown | Text | JSON | JSON |
| Dokumentierter Scope | vollständige Seiten p003–p004 | vollständige Seiten; drei Beitragsbereiche sichtbar | vollständige Seiten; drei Beitragsbereiche sichtbar | Hersch-Überschrift inklusive bis Illich-Überschrift exklusiv |
| Forschungsfrage im Lauf | nicht vorhanden | nicht vorhanden | `unspecified in this run` | exakte Forschungsfrage |
| Kontrollierte Codes | nicht vorhanden | nicht vorhanden | nicht vorhanden | fünf Codebuch-IDs |
| Exakte Belege mit korrekter Page-ID | nicht als Annotation anwendbar | 29/29 | 26/26 | 13/13 |
| Schema-Validierung | nicht anwendbar | nicht anwendbar | PASS | PASS |
| Scope-Kontamination | nicht anwendbar; vollständige Seiten sind beabsichtigt | Bandelier, Hersch und Illich nachgewiesen | Bandelier, Hersch und Illich nachgewiesen | 0 Bandelier-/Illich-Belege |
| Initialer Quellenprüfstatus | `unchecked` im Metadatenkopf | kein Statusschema | alle Annotationen `unchecked` | alle Annotationen `unchecked` |
| Initialer fachlicher Review | `unreviewed` im Metadatenkopf | `unreviewed`; keine fachliche Abnahme dokumentiert | alle Annotationen `unreviewed` | alle Annotationen `unreviewed` |

Die Tabelle bewertet technische Konsistenz und Quellenrückbindung. Themenauswahl, Claim-Formulierung und Evidenzstatus bleiben fachlich `unreviewed`.

## Critical-Expert-Gate

Für `political_neutrality` liegt der Vorschlag vor, `evidence_status: direct` als `indirect` zu klassifizieren. Der Rohoutput bleibt unverändert. Die Entscheidung wird erst nach fachlicher Prüfung in einem abgeleiteten Review-Artefakt dokumentiert.

## Ausschlussfehler

Eine Ausgabe wird unabhängig von der Punktzahl revidiert, wenn mindestens ein Befund vorliegt:

- Bandelier- oder Illich-Evidenz in Lauf 04
- falsche Seite oder nicht auffindbares Zitat
- ein Feld namens `confidence` oder eine abgeleitete Sicherheitsskala
- `source_checked` ohne dokumentierte Prüfung am Faksimile oder Kontrolltext
- `source_mismatch` zusammen mit `review_status: accepted`
- `accepted` oder `rejected` ohne fachliche Entscheidung
- strukturierter Modelloutput startet mit einem anderen Wert als `unchecked` und `unreviewed`
- Gemini wird als Modellquelle genannt, obwohl der Run eine lokale `gpt-5.6-sol`-Probe ist
- syntaktisch ungültiges oder schemawidriges JSON

## Prüfsequenz

1. Primärbilder, vollständige Seitengrenzen und Hersch-Segmentgrenzen getrennt prüfen.
2. Den Hersch-Abschnitt der Transkription zeilenweise gegen p003 und p004 lesen; Passagen außerhalb bleiben als unverifiziert kennzeichnen.
3. Jedes Entity-Zitat und jedes `exact_quote` aus Lauf 04 im source-checked Hersch-Kontrolltext suchen.
4. Seiten-IDs gegen das Manifest prüfen.
5. Statusdimensionen unabhängig beurteilen.
6. Baseline auf Beitragsscope, Forschungsfrage, Schema und versteckte Codebuchvorgaben prüfen; Lauf 03 getrennt auf fachliche Vorgaben prüfen.
7. JSON gegen das Schema validieren.
8. Negative Schemafälle für Confidence-Feld, alte Statuswerte, Zusatzfelder, falsche Seiten-ID, ungültiges Datum und die verbotene Kombination `source_mismatch`/`accepted` ausführen.
