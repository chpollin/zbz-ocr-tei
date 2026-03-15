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
- **Frontend**: ES6+ JavaScript (const/let, arrow functions, template literals, IIFE wrappers), `ZBZ.*` / `TeiViewer.*` namespaces

## Commands

Operative Werkzeuge fuer den Promptotyping-Zyklus: `CLAUDE-COMMANDS.md`

Die Commands beschreiben ausfuehrbare Operationen (Diagnose, Textschicht, Layout,
TEI-Erzeugung, Entitaeten, Validierung), die im Zusammenspiel zwischen LLM und
Critical Expert in the Loop orchestriert werden. Jede Operation erzeugt
Qualitaetssignale, die den naechsten Schritt informieren.

Ausfuehrliche Methodik-Beschreibung: `Promptotyping-Tools.md`
Vollstaendige CLI-Referenz: `knowledge/PIPELINE.md` §CLI Commands.
