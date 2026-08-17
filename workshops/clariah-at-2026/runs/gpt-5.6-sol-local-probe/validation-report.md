# Validierungsbericht

## Gegenstand

Validiert wurde die korrigierte lokale `gpt-5.6-sol`-Probe vom 17. August 2026. Repository-Anker ist `1115ed24cbaf97a64093d9b0e839271b60a2d950`. Die Antworten 02, 03 und 04 wurden nach der Korrektur der Promptarchitektur neu erzeugt und ohne Code-Fences oder redaktionelle Normalisierung gespeichert. Die Probe ist kein Gemini-Output.

Die Laufzeit stellte Temperatur, `top_p`, Seed und Reasoning-Effort nicht bereit. Diese Parameter sind in `input/metadata.json` und `provenance.json` explizit als nicht verfügbar und mit `null` dokumentiert.

## Reproduzierbare Prüfung

Vom Repository-Root:

```powershell
python workshops/clariah-at-2026/validate.py
```

Gesamtergebnis: `ALL CHECKS PASS`.

## Prompt- und Scope-Vertrag

- Prompt 01 transkribiert p003 und p004 vollständig: PASS
- Bandelier-, Hersch- und Illich-Bereich sind im vollständigen Output vorhanden: PASS
- Prompt 02 erhält ausschließlich die vollständige Transkription; exakte Forschungsfrage, Schema, Codebuch und Segmentanker fehlen: PASS
- Prompt 03 erhält vollständige Transkription und generisches Schema; exakte Forschungsfrage, Codebuch und Segmentanker fehlen: PASS
- Prompt 03 dokumentiert `research_question: unspecified in this run`: PASS
- Prompt 04 enthält exakte Forschungsfrage, Hersch-Start, Illich-Endanker, Codebuch, Schema und getrennte Statusregeln: PASS
- Schema hardcodiert weder Forschungsfrage noch analytischen Dataset-Scope: PASS

Die Outputs 02 und 03 enthalten erwartungsgemäß Themen und Entitäten aus angrenzenden Beiträgen. Der Test bestätigt Bandelier, Hersch und Illich als beobachtbare Scope-Kontamination. Output 04 enthält keine Belege oder Entitäten aus Bandelier-, Oury-, Illich-, Verne- oder `Orientations`-Passagen.

## JSON und Schema

- Schema nach Draft 2020-12 syntaktisch und strukturell gültig: PASS
- `examples/annotation-example.json`: PASS
- `03-schema-topics-output.json`: PASS
- `04-evidence-annotation-output.json`: PASS
- `input/metadata.json`: PASS
- `provenance.json`: PASS

Lauf 02 ist vertragsgemäß eine offene Textantwort und wird nicht gegen das JSON-Schema validiert.

## Zitat- und Seitenprüfung

Alle Belege wurden als exakte Zeichenfolgen innerhalb des jeweils angegebenen Seitenabschnitts gesucht:

- offene Baseline 02 gegen vollständige Seitentranskription: 29 Belege, PASS
- strukturierter Lauf 03 gegen vollständige Seitentranskription: 26 Entity- und Themenbelege, PASS
- forschungsfragengeleiteter Lauf 04 gegen source-checked Hersch-Kontrolltext: 13 Entity- und Themenbelege, PASS
- falsche Page-ID-Zuordnungen: 0
- Bandelier- oder Illich-Evidenz in Lauf 04: 0

Der source-checked Kontrolltext umfasst nur den Hersch-Beitrag. Bandelier- und Illich-Passagen bleiben mit Projektstatus `unverifiziert` dokumentiert.

## Forschungsfrage, Codes und Statusachsen

- Lauf 03: generischer Full-Page-Dataset-Identifier und RQ-Platzhalter: PASS
- Lauf 04: exakte Forschungsfrage: PASS
- Lauf 04: genau die fünf Codebuch-IDs `school_as_encounter`, `memory_for_judgement`, `pedagogical_invention`, `social_compensation`, `political_neutrality`: PASS
- `evidence_status`: ausschließlich `direct | indirect | ambiguous`: PASS
- `source_check_status` in Rohoutputs 03/04: ausschließlich `unchecked`: PASS
- `review_status` in Rohoutputs 03/04: ausschließlich `unreviewed`: PASS
- Feld `confidence`: nicht vorhanden, PASS

Lauf 02 besitzt als offene Textbaseline keine Schema- oder Statusfelder.

## Negative Schemafälle

Das Schema weist neun kontrollierte Mutationen zurück:

1. zusätzliches Feld `confidence`;
2. alter Evidenzstatus `supported`;
3. alter Quellenprüfstatus `verified`;
4. alter Reviewstatus `verified`;
5. falsche Page-ID `1000_p005`;
6. nicht erlaubtes Zusatzfeld auf Topic-Ebene;
7. String-Identifier bei `identifier_source: null`;
8. leeres Forschungsfragenfeld;
9. leeres Dataset-Feld.

Ergebnis: 9/9 PASS.

## Hashes, Manifest und Provenienz

- SHA-256 aller vier Promptdateien stimmt in `input/metadata.json` und `provenance.json`: PASS
- SHA-256 aller vier Rohoutputs stimmt in beiden Provenienzdokumenten: PASS
- beide Bildpfade und Kontrolltextpfade vorhanden: PASS
- Bild- und Kontrolltextprüfsummen stimmen mit `source-manifest.csv` überein: PASS
- Manifest-Commit entspricht dem geprüften Git-Anker: PASS
- `annotation_input_scope: full-page`: PASS
- `hersch_reference_status: source_checked`: PASS
- `outside_hersch_status: unverifiziert`: PASS
- Rechtestatus `zu prüfen` und Rights Note vorhanden: PASS
- README verweist konsistent auf Progression, Scope-Kontamination, Statusdifferenz und Artefakte: PASS

## Ergebnis

Das Paket bildet die vier didaktischen Stufen konsistent ab: vollständige multimodale Transkription, offene beitragsübergreifende Baseline, generische JSON-Strukturierung und forschungsfragengeleitete Hersch-Annotation. Schema, Daten, Quellenbelege, Segmentgrenze, Statusachsen und Provenienz sind maschinell geprüft. Die Rechteklärung und der fachliche Review der Claims bleiben offen.
