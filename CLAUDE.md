# Claude Code Regeln

## Arbeitsweise

1. **Journal fuehren**: Jede Session in `knowledge/JOURNAL.md` dokumentieren
2. **Wissen im knowledge/-Ordner**: Nicht in CLAUDE.md duplizieren
3. **Output nicht versionieren**: Generierte Dateien gehoeren in `output/`
4. **Tests vor Aenderungen**: Evaluation laufen lassen, Metriken vergleichen
5. **Single Source of Truth**: Jeden Fakt nur an einer Stelle fuehren, Querverweise setzen

## Projektwissen

Einstieg: `knowledge/INDEX.md` — Navigation, Dokumentmatrix, Abhaengigkeiten, Kernbegriffe.

## Sicherheit

- **NIEMALS `.env` lesen**: Die `.env`-Datei enthaelt API-Keys und darf unter keinen Umstaenden gelesen, angezeigt oder in den Output aufgenommen werden
- **Keine Secrets in Code oder Docs**: API-Keys, Tokens und Passwoerter gehoeren ausschliesslich in Umgebungsvariablen

## Code-Konventionen

- **Windows-Encoding**: Keine Unicode-Sonderzeichen in Print-Statements
- **Pfade**: Absolute Pfade oder pathlib verwenden
- **Ausgabe**: JSON fuer Daten, HTML fuer Reports
- **Frontend**: ES5 JavaScript (var, IIFE, keine Arrow-Functions), `ZBZ.*` / `TeiViewer.*` Namespaces

## Befehle

Vollstaendige CLI-Referenz: `knowledge/PIPELINE.md` §CLI-Befehle.

```bash
# Haeufigste Befehle (ohne GPU)
python -m scripts.tei.tei_generator              # TEI-XML generieren
python scripts/evaluate_ocr.py --all             # Evaluation
python -m scripts.generate_dashboard_data        # Dashboard-Daten

# GPU erforderlich
python -m scripts.run_layout_analysis            # Layout-Analyse (Docling)
```
