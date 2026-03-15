# Promptotyping-Tools.md

## Operative Werkzeuge der epistemischen Infrastruktur

**Kontext.** Dieses Dokument beschreibt die ausfuehrbaren Operationen, die innerhalb des Promptotyping-Interface fuer dieses digitale Editionsprojekt zur Verfuegung stehen. Jede Operation produziert oder transformiert ein Wissensartefakt (OCR-Text, Layoutdaten, TEI-XML, Entitaetsindex) und erzeugt dabei maschinenlesbare Qualitaetssignale, die den naechsten Schritt im Promptotyping-Zyklus informieren.

**Aufgabe.** TEI-XML-Dokumente validieren, ueberpruefen, korrigieren und erweitern, bis sie die aus dem Projektkontext heraus bestmoegliche Qualitaetsstufe erreichen.

**Methodische Einbettung.** Die Tools werden nicht autonom ausgefuehrt, sondern im Zusammenspiel zwischen menschlicher Urteilskompetenz und LLM-gestuetzter Verarbeitung orchestriert. Der Promptotyping-Zyklus bestimmt, wann welches Tool sinnvoll ist. Das LLM interpretiert Qualitaetssignale und schlaegt Folgeaktionen vor. Der Critical Expert in the Loop entscheidet.

---

## 1. Diagnose

Zustand eines Dokuments ermitteln, bevor Entscheidungen getroffen werden.

```bash
# TEI-Validierung (strukturelle Fehler, Konsistenz)
python -m scripts.tei.tei_validator --doc {DOC_ID}

# NER-Abdeckung und Konsistenz
python -m scripts.ner.ner_evaluate --doc {DOC_ID}

# OCR-Qualitaetsmetriken
python scripts/evaluate_ocr.py --phase phase1 --engine mistral
python -m scripts.evaluate_ocr --all --ocr-dir output/gemini_corrected_a

# Dokumentklassifikation pruefen
python -m scripts.classify_docs --doc {DOC_ID}
```

**Output.** JSON-Reports und Metriken, die als Qualitaetssignale in den Promptotyping-Zyklus zurueckfliessen.

## 2. Textschicht verbessern

Die OCR-Grundlage korrigieren, auf der alle weiteren Annotationsschichten aufbauen.

```bash
# Basis-OCR
python scripts/ocr_pipeline.py -i data/scans/{DOC_ID}.pdf -e mistral

# LLM-Postkorrektur (Claude)
python -m scripts.llm_postprocess --phase phase1 --variant C

# Multimodale Korrektur (Gemini, vergleicht Text gegen Scan)
python -m scripts.gemini_ocr_correct --doc {DOC_ID} --variant B

# Vorschau ohne API-Kosten
python -m scripts.gemini_ocr_correct --doc {DOC_ID} --dry-run
```

## 3. Layoutanalyse und -qualitaet

Sicherstellen, dass die physische Struktur der Quelle (Spalten, Ueberschriften, Marginalien, Tabellen) korrekt erfasst ist.

```bash
# Layouterkennung (lokal oder Cloud-Fallback)
python -m scripts.run_layout_analysis --doc {DOC_ID}
python -m scripts.run_layout_cloud --doc {DOC_ID}

# Gemini-basierte Layout-QA
python -m scripts.layout_qa_gemini --doc {DOC_ID}

# Vollstaendige Neuerkennung bei QA-Problemen
python -m scripts.layout_qa_gemini --mode detect --doc {DOC_ID}

# Visuelle Overlays fuer menschliche Pruefung
python -m scripts.generate_layout_overlays --doc {DOC_ID} --compare
```

## 4. TEI-XML erzeugen und verfeinern

Das Kernartefakt der Edition aufbauen oder neu aufbauen.

```bash
# Unified Pipeline (3 Stufen, regelbasiert + Gemini + Assembly)
python -m scripts.tei.tei_unified --doc {DOC_ID}

# Nur regelbasiertes Scaffold (keine API-Kosten, fuer strukturelles Debugging)
python -m scripts.tei.tei_unified --doc {DOC_ID} --step 1

# Re-Assembly mit allen Fixes (Step 2 aus Cache, kostenlos)
python -m scripts.tei.tei_unified --doc {DOC_ID} --reassemble

# Neuaufbau bei geaenderten Upstream-Daten (inkl. Gemini-Calls)
python -m scripts.tei.tei_unified --doc {DOC_ID} --force

# Prompt-Vorschau
python -m scripts.tei.tei_unified --doc {DOC_ID} --dry-run

# Referenz-Vergleich gegen ZBZ-Referenz-TEI
python -m scripts.tei.tei_validator --compare-ref
```

## 5. Entitaeten extrahieren, verknuepfen, injizieren

Named Entities erkennen, gegen Wikidata abgleichen und in die TEI-Struktur einbetten.

```bash
# Extraktion
python -m scripts.ner.ner_extract --doc {DOC_ID}

# Wikidata-Reconciliation
python -m scripts.ner.wikidata_linker --doc {DOC_ID}

# Injektion in TEI-XML (mit Validierung)
python -m scripts.ner.ner_inject_tei --doc {DOC_ID} --validate

# Korpusweite Konsistenz
python -m scripts.ner.entity_index --merge-all
python -m scripts.ner.entity_index --report
```

## 6. Validierung (Qualitaetsgate)

Maschinenlesbare Bestaetigung, dass eine Korrekturmassnahme tatsaechlich verbessert hat.

```bash
# Einzeldokument
python -m scripts.tei.tei_validator --doc {DOC_ID}

# Korpusweit mit Report
python -m scripts.tei.tei_validator --all --report
python -m scripts.tei.tei_validator --all --html-report
```

## 7. Agent-Based Quality Screening (Pre-Curation)

Agentengestuetztes Screening aller TEI-Dokumente durch ein 7-Schichten-Protokoll.
Kein einzelner CLI-Befehl, sondern ein orchestrierter Agent-Prozess.

```bash
# Vorbereitung: Batch-Manifest erzeugen (4 Tiers nach Seitenzahl)
python -m scripts.tei.tei_screening_prep

# Agent-Prompt fuer einen Batch generieren
python -m scripts.tei.screening_prompt --batch {N}

# revisionDesc mit Screening-Status in alle finalen TEIs injizieren
python -m scripts.tei.tei_add_revision --all

# Automatischer Pre-Check (Header, Struktur, Entity-Zaehlung)
python -m scripts.tei.tei_quality_pass --all
```

**Schichten des Protokolls:**
1. Scan-Qualitaet (visuell: Layout-Overlay pruefen)
2. OCR-Treue (Layout-JSON-Text gegen TEI vergleichen)
3. Layout-Korrektheit (Regionen, Reihenfolge, Typen)
4. TEI-Struktur (Validator: RelaxNG + Projektregeln)
5. Referenz-Vergleich (wo ZBZ-Referenz-TEI vorliegt)
6. Entity-Plausibilitaet (Typen, Konflikte, Verteilung)
7. Gesamtkohaerenz (liest sich das als Edition?)

**Output:** `output/tei_final/{DOC_ID}_review.json` (Befund pro Dokument),
`output/tei_final/{DOC_ID}_final.xml` (TEI mit revisionDesc im Header).

**Ergebnis (285/285 Docs):** 210 APPROVED (74%), 43 WITH_NOTES (15%), 32 NEEDS_REVIEW (11%).

**Positionierung:** Pre-Curation Triage — sortiert, wo menschliche Aufmerksamkeit noetig ist. Kein Ersatz fuer fachliche Kuration.

## 8. Visuelle Artefakte fuer den Expert in the Loop

Ausgaben, die nicht maschinell, sondern durch menschliche Inspektion bewertet werden.

```bash
# Seitenbilder aus Scans
python scripts/extract_pages.py --pdf {DOC_ID}.pdf --dpi 300

# Layout-Overlays (Docling vs. Gemini)
python -m scripts.generate_layout_overlays --doc {DOC_ID} --compare

# Dashboard-Daten fuer Projektuberblick
python -m scripts.generate_dashboard_data
```

---

## Arbeitszyklus

Der typische Revisionszyklus innerhalb des Promptotyping-Interface folgt einem Muster.

**Diagnose.** Validierung und Evaluation laufen lassen. Die Reports liefern Qualitaetssignale, die das LLM interpretiert und als priorisierte Fehlerliste aufbereitet.

**Exploration.** Gemeinsam mit dem LLM entscheiden, welche Korrekturmassnahme den groessten Qualitaetsgewinn verspricht. Dabei abwaegen, ob das Problem in der Textschicht (OCR), der Strukturschicht (Layout) oder der Annotationsschicht (NER, TEI-Encoding) liegt.

**Ausfuehrung.** Das gewaehlte Tool aufrufen. Bei Operationen mit API-Kosten oder destruktivem Potenzial (--force) vorher --dry-run nutzen und das Ergebnis mit dem Expert in the Loop besprechen.

**Re-Validierung.** Nach jeder Korrektur erneut validieren. Den neuen Report gegen den vorherigen vergleichen, um Verbesserung zu bestaetigen und Regressionen auszuschliessen.

**Eskalation.** Wenn ein Fehlertyp auftritt, fuer den kein bestehendes Tool eine Loesung bietet, beschreibt das LLM das Fehlermuster, schlaegt ein neues Skript oder eine Pipeline-Erweiterung vor und legt den Entwurf dem Expert in the Loop zur Freigabe vor.

---

## Konventionen

Dokument-IDs folgen dem Muster `{DOC_ID}` (z.B. 2310, 2530, 1440). Alle Outputs landen in `output/`-Unterverzeichnissen. `--dry-run` steht bei allen API-nutzenden Tools zur Verfuegung und sollte vor kostenpflichtigen Batch-Operationen verwendet werden. `--force` ueberschreibt gecachte Ergebnisse und ist nur sinnvoll, wenn sich Upstream-Daten tatsaechlich veraendert haben. `--reassemble` wendet alle Fixes an ohne Gemini-Calls (Step 2 aus Cache).
