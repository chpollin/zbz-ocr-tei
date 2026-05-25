# Claude Code Rules

Projekt-Konstitution. Operative Regeln und Konventionen, die bei jedem Pipeline-Schritt gelten.

## Workflow

1. **Journal fuehren:** Jede Sitzung dokumentieren in [knowledge/journal.md](knowledge/journal.md) — eine Zeile pro Sitzung, kompakter Ueberblick. Details ins Git-Log.
2. **Wissen in `knowledge/`:** nicht in CLAUDE.md duplizieren. Single Source of Truth pro Fakt.
3. **Output nicht versionieren:** generierte Dateien gehoeren in `output/` (gitignored). Ausnahme: `data/tei_curated/` (Gold-Standard).
4. **Vor Aenderungen testen:** Evaluierung laufen lassen, Metriken vergleichen.
5. **Single Source of Truth:** jeder Fakt steht in genau einem Dokument. Andere Dokumente verweisen via Cross-Reference.

## Knowledge Base

Einstiegspunkt: [knowledge/index.md](knowledge/index.md) — Navigation, Abhaengigkeiten, Schluesselkonzepte.

10 thematisch klar getrennte Dokumente:

- [projekt.md](knowledge/projekt.md) — Auftrag, Korpus, ZBZ-Workflow, Status
- [pipeline.md](knowledge/pipeline.md) — 7-Stufen-Pipeline, Engines, TEI-Mapping
- [entities.md](knowledge/entities.md) — NER + GND + Wikidata
- [quality.md](knowledge/quality.md) — CER + Validierung + Screening
- [viewer.md](knowledge/viewer.md) — Pipeline-Viewer (Faksimile + OCR + Layout + TEI + Editor)
- [infrastruktur.md](knowledge/infrastruktur.md) — Azure, Podman, CI/CD
- [methodik.md](knowledge/methodik.md) — Promptotyping + epistemische Infrastruktur
- [decisions.md](knowledge/decisions.md) — Entscheidungsregister
- [journal.md](knowledge/journal.md) — chronologischer Sitzungs-Ueberblick
- [index.md](knowledge/index.md) — Navigation + Schluesselkonzepte

## Security

- **NIEMALS `.env` lesen:** die `.env`-Datei enthaelt API-Keys und darf unter keinen Umstaenden gelesen, angezeigt oder in Ausgaben aufgenommen werden
- **keine Secrets in Code oder Doku:** API-Keys, Tokens und Passwoerter ausschliesslich in Environment-Variablen

## Code-Konventionen

- **Windows-Encoding:** keine Unicode-Sonderzeichen in Print-Statements
- **Pfade:** absolute Pfade oder `pathlib`
- **Output:** JSON fuer Daten, HTML fuer Reports
- **Frontend:** ES6+ JavaScript (`const`/`let`, Arrow-Functions, Template-Literals, IIFE-Wrappers), `ZBZ.*` / `TeiViewer.*` Namespaces

## Design

Bei UI- oder Frontend-Generierung ist [knowledge/viewer.md §Hersch Design-System](knowledge/viewer.md) die Wertequelle. Imperative Designprinzipien:

- ausschliesslich `--h-*`-Tokens, niemals Hex-Werte direkt im Komponenten-CSS
- Akzentfarben (Ziegelrot, Preussischblau, Olivgruen) gelten fuer Akzente und Status-Indikatoren, nicht fuer Flaechen
- keine reinen Schwarz/Weiss-Werte; immer den warmen Anthrazit `--h-text` und das warme Cream `--h-bg`
- bei neuen Komponenten zuerst pruefen, ob ein bestehender Token oder eine Komponente in `base.css` traegt

Token-Katalog: `docs/css/tokens.css`. Basis-Komponenten: `docs/css/base.css`. Viewer-spezifisch: `docs/css/viewer.css`.

## TEI-Datenfluss

- `output/tei_unified/` — Pipeline-Output (generierte TEIs, nicht editieren)
- `output/tei_final/` — gescreente, finale TEIs mit `<revisionDesc>` im Header (E43: Single Source of Truth fuer die Edition)
- Nur `tei_final/`-Dokumente werden in der Edition angezeigt
- Jedes finale TEI hat eine `<revisionDesc>` mit Pipeline- und Screening-Status (E42)
- Review-JSONs (`{DOC_ID}_review.json`) dokumentieren den Befund pro Dokument
- Kuratierte TEIs (Gold-Standard) liegen in `data/tei_curated/` (git-tracked)

## Methodik

Dreischichtung Command / Artifact / Tool — Details: [knowledge/methodik.md](knowledge/methodik.md).

- **Command** = Entscheidungsregel (wann was tun)
- **Artifact** = materielles Werkzeug im Repo (Script, Index, Report)
- **Tool** = konkreter Aufruf eines Artifacts durch den Agent

Verifikationskaskade (oekonomisch geordnet): automatisch → kontextuell → visuell → fachlich.
Operative Werkzeuge und Arbeitszyklus: [knowledge/methodik.md](knowledge/methodik.md).

---

# Commands (CLI-Referenz)

Operative Werkzeuge fuer den Promptotyping-Zyklus. Jede Operation erzeugt Qualitaetssignale,
die den naechsten Schritt informieren. Der Critical Expert in the Loop entscheidet.

Methodische Einbettung (Diagnose → Exploration → Ausfuehrung → Re-Validierung → Eskalation):
[knowledge/methodik.md](knowledge/methodik.md). Konventionen (`--dry-run`, `--force`, `--reassemble`): siehe dort.

## Diagnose

```bash
python -m scripts.tei.tei_validator --doc {DOC_ID}             # TEI-Validierung
python -m scripts.tei.tei_validator --all --html-report         # Korpus-Report
python -m scripts.tei.tei_validator --compare-ref               # Referenz-Vergleich (11 Docs)
python -m scripts.ner.ner_evaluate --doc {DOC_ID}               # NER-Abdeckung
python -m scripts.evaluate_ocr --all                            # OCR-Metriken
python -m scripts.quality_proxy --all --html                    # Quality Proxy (Hit Rate)
python -m scripts.completeness_check --html                     # Vollstaendigkeits-Check (Seiten)
python -m scripts.benchmark_cer --all --html                    # CER-Benchmark (25 GT-Docs)
python -m scripts.cer_statistics_full --seed 42 --bootstrap-n 10000  # wiss. CER-Statistik (BCa-CIs, Paired, HCPR)
python -m pytest tests/test_cer_statistics.py -q                # 55 Tests fuer Statistik-Library
```

Output `docs/data/cer_statistics.json` (regenerierbar, derzeit nicht eingecheckt). Das interaktive CER-Dashboard wurde mit E56 abgeschafft. Methodik: [knowledge/quality.md §CER-Methodik](knowledge/quality.md).

## Textschicht

```bash
python scripts/ocr_pipeline.py -i data/scans/{DOC_ID}.pdf -e mistral    # Basis-OCR
python -m scripts.gemini_ocr_correct --doc {DOC_ID} --variant B          # Gemini-Korrektur
python -m scripts.gemini_ocr_correct --doc {DOC_ID} --dry-run            # Vorschau
```

## Layout

```bash
python -m scripts.run_layout_analysis --doc {DOC_ID}                     # Docling
python -m scripts.layout_qa_gemini --doc {DOC_ID}                        # Gemini QA
python -m scripts.layout_qa_gemini --mode detect --doc {DOC_ID}          # Neudetektion
python -m scripts.generate_layout_overlays --doc {DOC_ID} --compare      # Overlay
```

## TEI erzeugen

```bash
python -m scripts.tei.tei_unified --doc {DOC_ID}                         # Standard (3 Stufen)
python -m scripts.tei.tei_unified --doc {DOC_ID} --step 1                # nur Scaffold (kostenlos)
python -m scripts.tei.tei_unified --doc {DOC_ID} --reassemble            # Re-Assembly (kostenlos)
python -m scripts.tei.tei_unified --doc {DOC_ID} --force                 # alles neu (inkl. Gemini)
python -m scripts.tei.tei_unified --doc {DOC_ID} --dry-run               # Prompt-Vorschau
python -m scripts.tei.tei_unified --all --reassemble --ner               # Korpus Re-Assembly
```

## Entitaeten

```bash
python -m scripts.ner.ner_extract --doc {DOC_ID}                         # Extraktion
python -m scripts.ner.wikidata_linker --doc {DOC_ID}                     # Wikidata
python -m scripts.ner.ner_inject_tei --doc {DOC_ID} --validate           # Injektion
python -m scripts.ner.entity_index --merge-all                           # Index zusammenfuehren
python -m scripts.ner.entity_index --stats                               # Statistiken
python -m scripts.ner.entity_index --diagnostics --export-csv output/evaluation/entity_review.csv  # CSV fuer Review
python -m scripts.ner.wikidata_linker --all --resume                     # Batch-Linking
```

## Validierung (Qualitaetsgate)

```bash
python -m scripts.tei.tei_validator --doc {DOC_ID}                       # Einzeldokument
python -m scripts.tei.tei_validator --all --report                       # JSON-Report
python -m scripts.tei.tei_validator --all --html-report                  # HTML-Report
```

## Quality Screening (Pre-Curation)

Agent-Prozess durch 7 Schichten (Scan, OCR, Layout, TEI-Struktur, Referenz, Entities, Kohaerenz).
Kein einzelner CLI-Befehl. Tools (Artifacts):

```bash
python -m scripts.tei.tei_validator --doc {DOC_ID}                       # Schicht 4
python -m scripts.tei.tei_validator --compare-ref --doc {DOC_ID}         # Schicht 5
python -m scripts.tei.tei_screening_prep                                 # Batch-Manifest erzeugen
python -m scripts.tei.tei_add_revision --all                             # revisionDesc in alle TEIs
python -m scripts.tei.tei_quality_pass --all                             # automatischer Pre-Check
python -m scripts.tei.screening_prompt --batch {N}                       # Agent-Prompt generieren
```

Output: `output/tei_final/{DOC_ID}_final.xml` + `{DOC_ID}_review.json` + `screening_manifest.json`.

Ergebnis (285/285 Docs): 242 APPROVED (85%), 43 WITH_NOTES (15%), 0 NEEDS_REVIEW (0%). Details: [knowledge/quality.md](knowledge/quality.md).

## Viewer-Daten

```bash
python -m scripts.generate_edition_data                                  # Katalog (data/catalog.json) + Entity-Index + Per-Seiten-Mirror
```

Der Viewer (`docs/viewer.html`) ist eine statische Single-Page-App ohne Backend. Editier-Aenderungen
werden als Datei-Download bereitgestellt; siehe [knowledge/viewer.md §Persistenz](knowledge/viewer.md).

## Visuelle Artefakte

```bash
python scripts/extract_pages.py --pdf {DOC_ID}.pdf --dpi 300             # Seitenbilder
python -m scripts.generate_layout_overlays --doc {DOC_ID} --compare      # Layout-Overlay
```

---

# Hilfe

- `/help` — Hilfe zur Verwendung von Claude Code
- Feedback: https://github.com/anthropics/claude-code/issues
