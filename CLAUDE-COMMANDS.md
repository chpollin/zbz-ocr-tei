# Claude Commands

Operative Werkzeuge fuer den Promptotyping-Zyklus. Jede Operation erzeugt
Qualitaetssignale, die den naechsten Schritt informieren. Der Critical Expert
in the Loop entscheidet.

Ausfuehrliche Beschreibung der Methodik: `Promptotyping-Tools.md`

---

## Diagnose

```bash
python -m scripts.tei.tei_validator --doc {DOC_ID}           # TEI-Validierung
python -m scripts.tei.tei_validator --all --html-report       # Korpus-Report
python -m scripts.tei.tei_validator --compare-ref             # Referenz-Vergleich (11 Docs)
python -m scripts.ner.ner_evaluate --doc {DOC_ID}             # NER-Abdeckung
python scripts/evaluate_ocr.py --all                          # OCR-Metriken
```

## Textschicht

```bash
python scripts/ocr_pipeline.py -i data/scans/{DOC_ID}.pdf -e mistral   # OCR
python -m scripts.gemini_ocr_correct --doc {DOC_ID} --variant B         # Gemini-Korrektur
python -m scripts.gemini_ocr_correct --doc {DOC_ID} --dry-run           # Vorschau
```

## Layout

```bash
python -m scripts.run_layout_analysis --doc {DOC_ID}                    # Docling
python -m scripts.layout_qa_gemini --doc {DOC_ID}                       # Gemini QA
python -m scripts.layout_qa_gemini --mode detect --doc {DOC_ID}         # Neudetektion
python -m scripts.generate_layout_overlays --doc {DOC_ID} --compare     # Overlay
```

## TEI erzeugen

```bash
python -m scripts.tei.tei_unified --doc {DOC_ID}                        # Standard (3 Stufen)
python -m scripts.tei.tei_unified --doc {DOC_ID} --step 1               # Nur Scaffold (kostenlos)
python -m scripts.tei.tei_unified --doc {DOC_ID} --reassemble           # Re-Assembly (kostenlos)
python -m scripts.tei.tei_unified --doc {DOC_ID} --force                # Alles neu (inkl. Gemini)
python -m scripts.tei.tei_unified --doc {DOC_ID} --dry-run              # Prompt-Vorschau
python -m scripts.tei.tei_unified --all --reassemble --ner              # Korpus Re-Assembly
```

## Entitaeten

```bash
python -m scripts.ner.ner_extract --doc {DOC_ID}                        # Extraktion
python -m scripts.ner.wikidata_linker --doc {DOC_ID}                    # Wikidata
python -m scripts.ner.ner_inject_tei --doc {DOC_ID} --validate          # Injektion
python -m scripts.ner.entity_index --merge-all                          # Index zusammenfuehren
python -m scripts.ner.entity_index --stats                              # Statistiken
```

## Validierung (Qualitaetsgate)

```bash
python -m scripts.tei.tei_validator --doc {DOC_ID}                      # Einzeldokument
python -m scripts.tei.tei_validator --all --report                      # JSON-Report
python -m scripts.tei.tei_validator --all --html-report                 # HTML-Report
```

## Quality Screening (Pre-Curation)

Agent-Based Quality Screening: Claude Code prueft jedes Dokument durch
7 Schichten. Das ist ein Agent-Prozess, kein einzelner CLI-Befehl.
Der Agent verwendet die unten gelisteten Tools (Artifacts) gemaess
dem Arbeitszyklus (Command).

**Schichten:**
1. Scan-Qualitaet (visuell: Layout-Overlay pruefen)
2. OCR-Treue (TEI-Text gegen Scan vergleichen)
3. Layout-Korrektheit (Regionen, Reihenfolge)
4. TEI-Struktur (Validator)
5. Referenz-Vergleich (wo ZBZ-Referenz vorliegt)
6. Entity-Plausibilitaet (Typen, Konflikte)
7. Gesamtkohaerenz (liest sich das als Edition?)

**Tools (Artifacts, die der Agent aufruft):**
```bash
python -m scripts.tei.tei_validator --doc {DOC_ID}                      # Schicht 4
python -m scripts.tei.tei_validator --compare-ref --doc {DOC_ID}        # Schicht 5
python -m scripts.tei.tei_screening_prep                                # Batch-Manifest erzeugen
python -m scripts.tei.tei_add_revision --all                            # revisionDesc in alle TEIs
python -m scripts.tei.tei_quality_pass --all                            # Automatischer Pre-Check
python -m scripts.tei.screening_prompt --batch {N}                      # Agent-Prompt generieren
# Schicht 1-3, 6-7: Visuelle Pruefung durch Agent (Scan + TEI lesen)
```

**Output:**
```
output/tei_final/{DOC_ID}_final.xml       # Finales TEI mit revisionDesc
output/tei_final/{DOC_ID}_review.json     # Befund pro Dokument
output/tei_final/screening_manifest.json  # Batch-Zuweisungen (4 Tiers)
```

**Ergebnis (285/285):** 210 APPROVED (74%), 43 WITH_NOTES (15%), 32 NEEDS_REVIEW (11%).

**Additivitaet:** `output/tei_unified/` bleibt unveraendert.
Finale TEIs mit `<revisionDesc>` liegen in `output/tei_final/`.

## Visuelle Artefakte

```bash
python scripts/extract_pages.py --pdf {DOC_ID}.pdf --dpi 300            # Seitenbilder
python -m scripts.generate_layout_overlays --doc {DOC_ID} --compare     # Layout-Overlay
python -m scripts.generate_dashboard_data                                # Dashboard
```

---

## Arbeitszyklus

1. **Diagnose** -- Validierung laufen lassen, Qualitaetssignale lesen
2. **Exploration** -- Entscheiden: Textschicht, Struktur oder Annotation?
3. **Ausfuehrung** -- Tool aufrufen (bei API-Kosten: --dry-run zuerst)
4. **Re-Validierung** -- Erneut validieren, Verbesserung bestaetigen
5. **Eskalation** -- Bei neuem Fehlertyp: Skript vorschlagen, Expert entscheidet

## Dreischichtung: Command / Artifact / Tool

- **Command**: Die Entscheidungsregel ("nach jeder Korrektur validieren")
- **Artifact**: Das materielle Werkzeug im Repo (`tei_validator.py`)
- **Tool**: Der konkrete Aufruf (`python -m scripts.tei.tei_validator --doc 290`)

Commands stehen in diesem Dokument (Arbeitszyklus oben).
Artifacts stehen im Repo (Scripts, Indizes, Reports).
Tools sind die CLI-Befehle in den Abschnitten oben.

## Konventionen

- Dokument-IDs: `{DOC_ID}` (z.B. 2310, 1440, 100)
- Outputs: `output/`-Unterverzeichnisse
- `--dry-run`: Vorschau ohne API-Kosten
- `--force`: Alles neu (inkl. Gemini-Calls)
- `--reassemble`: Nur Step 1+3 neu, Step 2 aus Cache (kostenlos)
