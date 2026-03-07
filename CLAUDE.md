# Claude Code Rules

## Workflow

1. **Keep a journal**: Document every session in `knowledge/JOURNAL.md`
2. **Knowledge in the knowledge/ folder**: Do not duplicate in CLAUDE.md
3. **Do not version output**: Generated files belong in `output/`
4. **Test before changes**: Run evaluation, compare metrics
5. **Single Source of Truth**: Keep each fact in one place only, use cross-references

## Project Knowledge

Entry point: `knowledge/INDEX.md` — Navigation, document matrix, dependencies, key concepts.

## Security

- **NEVER read `.env`**: The `.env` file contains API keys and must under no circumstances be read, displayed, or included in output
- **No secrets in code or docs**: API keys, tokens, and passwords belong exclusively in environment variables

## Code Conventions

- **Windows encoding**: No Unicode special characters in print statements
- **Paths**: Use absolute paths or pathlib
- **Output**: JSON for data, HTML for reports
- **Frontend**: ES5 JavaScript (var, IIFE, no arrow functions), `ZBZ.*` / `TeiViewer.*` namespaces

## Commands

Complete CLI reference: `knowledge/PIPELINE.md` §CLI Commands.

```bash
# Most common commands (no GPU)
python -m scripts.tei.tei_unified --all           # Unified TEI Pipeline (Production)
python -m scripts.tei.tei_validator --all --report # TEI Validation (RelaxNG)
python scripts/evaluate_ocr.py --all              # Evaluation
python -m scripts.generate_dashboard_data         # Dashboard data

# NER Pipeline (Phase 3)
python -m scripts.ner.ner_extract --doc 2310      # NER extraction (single doc)
python -m scripts.ner.ner_extract --all           # NER extraction (all docs)
python -m scripts.ner.entity_index --stats        # Entity Index statistics
python -m scripts.ner.entity_index --merge-all    # Merge all stores into index
python -m scripts.ner.wikidata_linker --doc 2310  # Wikidata reconciliation
python -m scripts.ner.ner_inject_tei --doc 2310   # TEI entity injection

# GPU required
python -m scripts.run_layout_analysis             # Layout analysis (Docling)
```
