# Claude Code Regeln

## Arbeitsweise

1. **Journal führen**: Jede Session in `knowledge/journal.md` dokumentieren
2. **Wissen im knowledge/-Ordner**: Nicht in CLAUDE.md duplizieren
3. **Output nicht versionieren**: Generierte Dateien gehören in `output/`
4. **Tests vor Änderungen**: Evaluation laufen lassen, Metriken vergleichen

## Projektwissen lesen

| Thema | Datei |
|-------|-------|
| Aktueller Stand | `knowledge/journal.md` |
| Dokumenttypen & Testplan | `knowledge/Testplan-OCR.md` |
| OCR-Fehler & Post-Processing | `knowledge/Pipeline.md` |
| TEI-Regeln | `knowledge/TEI-Mapping.md` |
| Quellen & Korpus | `knowledge/Quellenanalyse.md` |

## Code-Konventionen

- **Windows-Encoding**: Keine Unicode-Sonderzeichen (→, ✓, ✗) in Print-Statements
- **Pfade**: Absolute Pfade oder pathlib verwenden
- **Ausgabe**: JSON für Daten, HTML für Reports

## Befehle

```bash
# OCR-Tests (GPU erforderlich)
python scripts/test_all_pdfs.py --phase phase1

# Evaluation (ohne GPU)
python scripts/evaluate_ocr.py --all

# Post-Processing (ohne GPU)
python -m scripts.postprocess.pipeline
```

## Entscheidungshilfen

- **Neue Erkenntnis?** → In passendes knowledge/-Dokument eintragen
- **Neuer Test?** → Testplan-OCR.md aktualisieren
- **Session beenden?** → Journal aktualisieren, ggf. committen
