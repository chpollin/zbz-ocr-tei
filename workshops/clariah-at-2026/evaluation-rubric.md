# Evaluationsrubrik

Diese Rubrik trennt maschinenprüfbare Artefakteigenschaften von fachlichen Entscheidungen. Ein maschinelles Kriterium erhält `1`, wenn die im Validator definierte Bedingung vollständig erfüllt ist, sonst `0`. `nicht anwendbar` geht nicht in die Summe ein. Die Punktzahl bewertet technische Konsistenz und Quellenrückbindung; sie ist keine Bewertung der wissenschaftlichen Qualität.

## Lauf 01: vollständige Transkription

| ID | Maschinenprüfbares Kriterium | Befund | Wert |
|---|---|---|---:|
| 01-A | Prompt fordert die vollständigen sichtbaren Seiten und keine analytische Beitragsauswahl. | erfüllt | 1 |
| 01-B | Output enthält die Page-Marker `1000_p003` und `1000_p004`. | erfüllt | 1 |
| 01-C | Bandelier-, Hersch- und Illich-Marker sind im vollständigen Output vorhanden. | erfüllt | 1 |
| 01-D | Metadatenkopf initialisiert `source_check_status: unchecked` und `review_status: unreviewed`. | erfüllt | 1 |
| 01-E | Prompt- und Output-SHA-256 stimmen mit Metadaten und Provenienz überein. | erfüllt | 1 |

**Summe Lauf 01: 5/5**

## Lauf 02: offene Textbaseline

| ID | Maschinenprüfbares Kriterium | Befund | Wert |
|---|---|---|---:|
| 02-A | Prompt enthält weder exakte Forschungsfrage, Schema- oder Codebuchpfad noch Segmentanker. | erfüllt | 1 |
| 02-B | Output ist eine Textantwort und kein JSON-Objekt. | erfüllt | 1 |
| 02-C | Bandelier, Hersch und Illich sind als vollständiger Seitenscope nachweisbar. | erfüllt | 1 |
| 02-D | Alle extrahierten Belege sind auf der angegebenen Seite exakt auffindbar. | 29/29 | 1 |
| 02-E | Prompt- und Output-SHA-256 stimmen mit Metadaten und Provenienz überein. | erfüllt | 1 |

**Summe Lauf 02: 5/5**

## Lauf 03: generischer Schema-Lauf

| ID | Maschinenprüfbares Kriterium | Befund | Wert |
|---|---|---|---:|
| 03-A | Prompt enthält Schema, aber keine exakte Forschungsfrage, keinen Codebuchpfad und keine Segmentanker. | erfüllt | 1 |
| 03-B | JSON validiert gegen das aktuelle Schema. | erfüllt | 1 |
| 03-C | `research_question` ist `unspecified in this run`; `dataset_id` bezeichnet die vollständigen Seiten. | erfüllt | 1 |
| 03-D | Alle Entity- und Themenbelege sind auf der angegebenen Seite exakt auffindbar. | 26/26 | 1 |
| 03-E | Alle Annotationen starten mit `unchecked` und `unreviewed`. | erfüllt | 1 |
| 03-F | Prompt- und Output-SHA-256 stimmen mit Metadaten und Provenienz überein. | erfüllt | 1 |

**Summe Lauf 03: 6/6**

## Lauf 04: forschungsfragengeleitete Evidenzannotation

| ID | Maschinenprüfbares Kriterium | Befund | Wert |
|---|---|---|---:|
| 04-A | Prompt enthält exakte Forschungsfrage, Hersch-Start, Illich-Endanker, Schema und Codebuch. | erfüllt | 1 |
| 04-B | JSON validiert gegen das aktuelle Schema. | erfüllt | 1 |
| 04-C | Forschungsfrage und Hersch-Dataset-Identifier entsprechen dem Vertrag. | erfüllt | 1 |
| 04-D | Output enthält genau die fünf im Codebuch benannten Topic-IDs. | 5/5 | 1 |
| 04-E | Alle Entity- und Themenbelege sind im agentisch verifizierten Hersch-Referenztext auf der angegebenen Seite auffindbar. | 13/13 | 1 |
| 04-F | Bandelier-, Oury-, Illich-, Verne- und `Orientations`-Belege fehlen im Output. | 0 Kontaminationen | 1 |
| 04-G | Alle Annotationen starten mit `unchecked` und `unreviewed`. | erfüllt | 1 |
| 04-H | Prompt- und Output-SHA-256 stimmen mit Metadaten und Provenienz überein. | erfüllt | 1 |

**Summe Lauf 04: 8/8**

## Nicht bewertete fachliche Kriterien

| Gegenstand | Status | Gate |
|---|---|---|
| Formulierung und analytischer Scope der Forschungsfrage | `unreviewed` | `research_question` |
| Definitionen, Ein- und Ausschlussregeln sowie Anker der fünf Codes | `unreviewed` | `codebook` |
| Quellenstatus und fachliche Annahme der Musterannotation | `unreviewed` | `sample_annotation` |
| Didaktische Funktion der vollständigen Seiten in Lauf 02/03 und der Hersch-Grenze in Lauf 04 | `unreviewed` | `didactic_scope_boundary` |
| Evidenzstatus von `political_neutrality`; Vorschlag `indirect`, Rohwert `direct` | `unreviewed` | `political_neutrality_evidence_status` |
| Angemessenheit der übrigen Themen, Claims und Evidenzstatus | `unreviewed` | fachliche Prüfung erforderlich |

Die fünf benannten Gates sind maschinenlesbar in [critical-expert-gates.json](critical-expert-gates.json) serialisiert. Fachliche Kriterien erhalten vor ihrer Abnahme keine Punkte.

## Fail-closed-Regeln

Eine strukturierte Annotation ist schemawidrig, wenn mindestens eine der folgenden Bedingungen vorliegt:

- falsche Page-ID oder nicht erlaubtes Zusatzfeld;
- `confidence` oder eine abgeleitete Sicherheitsskala;
- nicht erlaubter Evidenz-, Quellenprüf- oder Reviewstatus;
- `accepted` oder `rejected` bei einem anderen Quellenprüfstatus als `source_checked`;
- ungültiges Kalenderdatum;
- ein nicht-Boolean-Wert in `local_probe` oder `gemini_output`.

Ein Artefakt bleibt fachlich `unreviewed`, bis das zugehörige Gate durch einen Critical Expert entschieden wurde. Die agentische visuelle und automatisierte Prüfung begründet keinen menschlichen `source_checked`-Status.

## Reproduzierbare Prüfung

```powershell
python workshops/clariah-at-2026/validate.py
```

Die im Dokument eingetragenen Einzelwerte und Summen sind nur gültig, wenn der Validator mit `ALL CHECKS PASS` endet.
