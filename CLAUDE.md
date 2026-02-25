# Claude Code Regeln

## Arbeitsweise

1. **Journal führen**: Jede Session in `knowledge/JOURNAL.md` dokumentieren
2. **Wissen im knowledge/-Ordner**: Nicht in CLAUDE.md duplizieren
3. **Output nicht versionieren**: Generierte Dateien gehören in `output/`
4. **Tests vor Änderungen**: Evaluation laufen lassen, Metriken vergleichen
5. **Single Source of Truth**: Jeden Fakt nur an einer Stelle führen, Querverweise setzen

## Projektwissen lesen

| Thema | Datei |
|-------|-------|
| Navigation (Start hier) | `knowledge/INDEX.md` |
| Ökosystem & Meilensteine | `knowledge/PROJEKT.md` |
| Pipeline-Architektur | `knowledge/ARCHITEKTUR.md` |
| Korpus & Dokumenttypen | `knowledge/QUELLENANALYSE.md` |
| OCR-Engines | `knowledge/OCR-ENGINES.md` |
| TEI-Regeln | `knowledge/TEI-MAPPING.md` |
| GND & NER | `knowledge/GND-STRATEGIE.md` |
| Testphasen & Ergebnisse | `knowledge/TESTPLAN.md` |
| Azure, Podman, CI/CD | `knowledge/INFRASTRUKTUR.md` |
| Entscheidungen & Offenes | `knowledge/DECISIONS.md` |
| ZBZ-Redaktionsworkflow | `knowledge/ZBZ-WORKFLOW.md` |
| Arbeitsjournal | `knowledge/JOURNAL.md` |

## Sicherheit

- **NIEMALS `.env` lesen**: Die `.env`-Datei enthaelt API-Keys und darf unter keinen Umstaenden gelesen, angezeigt oder in den Output aufgenommen werden
- **Keine Secrets in Code oder Docs**: API-Keys, Tokens und Passwoerter gehoeren ausschliesslich in Umgebungsvariablen

## Code-Konventionen

- **Windows-Encoding**: Keine Unicode-Sonderzeichen in Print-Statements
- **Pfade**: Absolute Pfade oder pathlib verwenden
- **Ausgabe**: JSON fuer Daten, HTML fuer Reports

## Befehle

```bash
# OCR-Tests (GPU erforderlich)
python scripts/test_all_pdfs.py --phase phase1

# Evaluation (ohne GPU)
python scripts/evaluate_ocr.py --all

# Post-Processing (ohne GPU)
python -m scripts.postprocess.pipeline

# Dashboard-Daten generieren (ohne GPU)
python -m scripts.generate_dashboard_data
```

## Entscheidungshilfen

- **Neuer Fakt?** → In genau ein knowledge/-Dokument eintragen, andere verweisen
- **Neue Entscheidung?** → In DECISIONS.md dokumentieren
- **Neuer Test?** → TESTPLAN.md aktualisieren
- **Session beenden?** → JOURNAL.md aktualisieren
