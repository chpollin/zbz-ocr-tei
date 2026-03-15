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

## Konventionen

- Dokument-IDs: `{DOC_ID}` (z.B. 2310, 1440, 100)
- Outputs: `output/`-Unterverzeichnisse
- `--dry-run`: Vorschau ohne API-Kosten
- `--force`: Alles neu (inkl. Gemini-Calls)
- `--reassemble`: Nur Step 1+3 neu, Step 2 aus Cache (kostenlos)
