---
type: moc
created: 2026-01-29
updated: 2026-03-26
tags: [zbz-ocr-tei, index, navigation]
status: active
---

# Knowledge Base — ZBZ-OCR-TEI

Documentation for the LLM-powered OCR and TEI pipeline of the Jeanne Hersch Edition (Zentralbibliothek Zuerich).

---

## Document Matrix

| Document | Answers | Audience | Dependencies |
|----------|---------|----------|--------------|
| [PROJEKT](PROJEKT.md) | What is the project? Pipeline scope and milestones | All | — |
| [PIPELINE](PIPELINE.md) | How is the pipeline technically structured? | Development | PROJEKT |
| [QUELLENANALYSE](QUELLENANALYSE.md) | What is the material? Which document types exist? | All | — |
| [ENGINES](ENGINES.md) | Which OCR and layout tools are used? | Development | PIPELINE |
| [TEI-MAPPING](TEI-MAPPING.md) | Which TEI rules apply? | Development, Edition | QUELLENANALYSE |
| [GND-STRATEGIE](GND-STRATEGIE.md) | How does entity linking work? | Development, Edition | TEI-MAPPING |
| [TESTPLAN](TESTPLAN.md) | How is quality measured? What are the results? | Development, QA | QUELLENANALYSE, ENGINES |
| [INFRASTRUKTUR](INFRASTRUKTUR.md) | How is deployment done? Azure, Podman, CI/CD? | Development, Ops | PIPELINE |
| [DECISIONS](DECISIONS.md) | What is decided? What is open? | All | All |
| [ZBZ-WORKFLOW](ZBZ-WORKFLOW.md) | How does ZBZ work editorially? | All | — |
| [JOURNAL](JOURNAL.md) | What was done when? | All | — |
| [EDITION](EDITION.md) | How does the digital edition work? Architecture, Design System | Development, Edition | PIPELINE |
| [CURATION](CURATION.md) | How does the Curation Editor work? Server, API, Editor | Development, Edition | EDITION, GND-STRATEGIE |
| [CER-BENCHMARK](CER-BENCHMARK.md) | How good is the OCR? End-to-End CER, research context | Development, QA | TESTPLAN, ENGINES, CER-METHODIK |
| [CER-METHODIK](CER-METHODIK.md) | Wie wird CER wissenschaftlich fundiert ermittelt? Bootstrap, Selektionsbias, HCPR, Limitations | Development, QA, Forschung | CER-BENCHMARK, TESTPLAN |
| [QUALITY-PROXY](QUALITY-PROXY.md) | Corpus-wide OCR quality without ground truth, language audit | Development, QA | CER-BENCHMARK, PIPELINE |
| [TEI-QUALITY](TEI-QUALITY.md) | Are TEIs schema-valid? Warnings, fix history, diagnostics | Development, QA | PIPELINE, TEI-MAPPING |
| [JOURNAL-ARCHIVE](JOURNAL-ARCHIVE.md) | Arbeitsjournal Sessions 1–26 (Archiv) | Alle | JOURNAL |
| [PROMPTOTYPING](PROMPTOTYPING.md) | Operative Werkzeuge der epistemischen Infrastruktur, CLI-Referenz | Development | PIPELINE |
| [METHODIK](METHODIK.md) | Epistemische Infrastruktur, Verifikationskaskade, Dreischichtung | All | PROMPTOTYPING, PIPELINE |
| [PLAN](PLAN.md) | What are the implementation phases? | Development | PROJEKT, PIPELINE |
| [WIKIDATA-WORKFLOW](WIKIDATA-WORKFLOW.md) | Konkreter Linking-Workflow: Priorisierung, Matching, Review | Development, Edition | GND-STRATEGIE, PLAN |

---

## Dependencies

```
PROJEKT (Vision, Ecosystem)
    |
    +-->  PIPELINE (7-Stage Pipeline: PDF -> TEI-XML)
    |        +-->  ENGINES (DeepSeek, Mistral, Gemini, Docling)
    |        +-->  INFRASTRUKTUR (Azure, Podman, CI/CD)
    |        +-->  TESTPLAN (Phases, Metrics)
    |
    +-->  QUELLENANALYSE (Corpus, Document Types, Pilot Files)
    |        +-->  TEI-MAPPING (DTA-Basisformat, Rules)
    |        |        +-->  GND-STRATEGIE (NER, Entity Linking)
    |        +-->  TESTPLAN (Single Source for Results)
    |
    +-->  ZBZ-WORKFLOW (Editorial Context)

EDITION   <-- digital edition (read + curate), depends on PIPELINE
    +-->  CURATION (edit mode, server, API)

PLAN          <-- implementation phases, depends on PROJEKT + PIPELINE
PROMPTOTYPING <-- operative Werkzeuge + CLI-Referenz
METHODIK      <-- epistemische Infrastruktur (destilliert aus Paper)
DECISIONS     <-- cross-cutting, collects from all docs
JOURNAL       <-- chronological, references all docs
```

---

## Key Concepts

| Term | Definition | Document |
|------|-----------|----------|
| Pipeline | Full end-to-end pipeline: PDF -> TEI-XML (7 stages) | [PROJEKT](PROJEKT.md) |
| 7-Stage Pipeline | Images -> OCR -> Layout -> PAGE-XML -> NER/GND -> TEI-XML -> Evaluation | [PIPELINE](PIPELINE.md) |
| Document Types A-D | Single-column, Two-column, Monograph, Special | [QUELLENANALYSE](QUELLENANALYSE.md) |
| DTA-Basisformat | TEI base schema with ZBZ customizations | [TEI-MAPPING](TEI-MAPPING.md) |
| NER + Wikidata | Named Entity Recognition + Wikidata linking (Phase 3, E34) | [GND-STRATEGIE](GND-STRATEGIE.md) |
| Entity Index | TEI-XML Indices (`data/entities/`) with internal IDs (zbz-p.N) + Wikidata QIDs | [GND-STRATEGIE](GND-STRATEGIE.md) |
| CER / WER | Character Error Rate / Word Error Rate | [TESTPLAN](TESTPLAN.md) |
| Hybrid Pipeline | Docling (Layout) + LLM-OCR (Text) combined | [PIPELINE](PIPELINE.md) |
| PAGE-XML | Intermediate format for Layout+OCR (Schema 2013-07-15) | [PIPELINE](PIPELINE.md) |
| Dashboard | QA UI with metrics, engine comparison, and document catalog | [PIPELINE](PIPELINE.md) |
| METS-XML | Multi-page manifest for PAGE-XML packages | [PIPELINE](PIPELINE.md) |
| TEI Generator | Layout-JSON + OCR -> page-level TEI-XML (DTA-Basisformat) | [PIPELINE](PIPELINE.md) |
| docling-serve (E24) | Layout analysis via REST API (Docker), no local GPU needed | [PIPELINE](PIPELINE.md) |
| Gemini Layout QA (E25) | Vision-based correction of Docling layout results, both versions preserved | [PIPELINE](PIPELINE.md) |
| Gemini Layout Detect (E26) | Full re-detection for bad pages via Gemini Vision, 3 modes (qa/detect/auto) | [PIPELINE](PIPELINE.md) |
| Gemini Classify (Stage 1a) | Visual classification of all 285 docs (type, language, pub_form, title, author) | [PIPELINE](PIPELINE.md) |
| doc_metadata.json | Central metadata file from Gemini classification, TEI-mappable | [PIPELINE](PIPELINE.md) |
| Online-Demo (E28) | 4 DEMO docs on GitHub Pages with fallback paths in shared.js | [PIPELINE](PIPELINE.md) |
| Gemini Vision TEI (E30) | 3-Pass TEI pipeline with overlay PNGs: Structure -> Enrichment -> Validation | [PIPELINE](PIPELINE.md) |
| Document-type-specific Prompts (E30) | 4-level hint system (layout type, pub_form, genre, language) for layout + TEI prompts | [PIPELINE](PIPELINE.md) |
| Genre Inference | Automatic classification into 14 genres via keyword matching on description text | [PIPELINE](PIPELINE.md) |
| Layout Full Run (E31) | Complete Gemini QA/Detect on 285 docs (3,992 pages, 14,708 corrections, avg score 72.7) | [PIPELINE](PIPELINE.md) |
| Layout Overlay Generator (E31) | Batch PNG generation with changed-highlighting + Docling-vs-Gemini side-by-side compare | [PIPELINE](PIPELINE.md) |
| changes_summary (E31) | Per-page label transition logging in layout_gemini.json, aggregated in summary_gemini.json | [PIPELINE](PIPELINE.md) |
| Digitale Edition (E33) | Lese-Edition + Kurations-Editor in einem System. `docs/`, `ZBZ.Edition` Namespace | [EDITION](EDITION.md), [CURATION](CURATION.md) |
| Curation Editor (E36) | Edit-Modus der Edition: WYSIWYG, Entity-Kuration, Review-Workflow, FastAPI Server | [CURATION](CURATION.md) |
| NER Pipeline (E34) | Post-hoc NER via Gemini Flash Lite (6 types), TEI-XML Entity Index, Wikidata Reconciliation, TEI Injection | [PIPELINE](PIPELINE.md) |
| Agent-Based Quality Screening (E41) | Agentengestuetztes Pre-Curation: 7-Schichten-Review (Scan, OCR, Layout, Struktur, Referenz, Entities, Kohaerenz). Output: Review-JSON + Sweep-Summary | [PLAN](PLAN.md) |
| Entity-Stopwort-Erweiterung (E45) | 20 neue Stopwoerter gegen systematische False Positives (Mensch, Est, Homme, Zeit etc.) | [PIPELINE](PIPELINE.md) |
| OCR-Deduplizierung (E46) | `scripts/ocr_dedup.py`: Deterministische Entfernung von Token-Loops, Barcode-Artefakten, Jahrzahl-Wiederholungen | [PIPELINE](PIPELINE.md) |
| zbz_hersch.rng (E48/E49) | Projektspezifisches RelaxNG-Schema (TEI P5 v4.10.2), ref-Pattern erweitert fuer GND + #zbz-IDs | [TEI-QUALITY](TEI-QUALITY.md) |
| Dual-Attribut-Strategie (E50) | Entity-Refs: `ref="GND:{id}"` (primaer) + `corresp="#zbz-{typ}.{N}"` (intern) | [TEI-MAPPING](TEI-MAPPING.md) |
| CER-Benchmark (E51) | End-to-End TEI-vs-TEI Evaluation: Mean 4.18%, Median 1.83% (scope-bereinigt, 19 Docs) | [CER-BENCHMARK](CER-BENCHMARK.md) |
| CER-Statistik (E54) | Wissenschaftliche CER-Re-Evaluation 2026-04: Mean 4.10% [2.01,6.75]%, Median 1.83% [0.84,5.14]% mit BCa-CIs, paired vs OCR-only −14.83pp p=0.0004, HCPR ~99%, Selektionsbias n_chars p=0.041 (NOT comparable) | [CER-METHODIK](CER-METHODIK.md), [CER-BENCHMARK](CER-BENCHMARK.md) |
| CER-Dashboard (E55) | Interaktives Frontend `docs/infrastruktur/cer.html` mit 12 Sektionen, vanilla SVG, Limitations-Panel sticky, Lit-Vergleich mit comparable-Enum, Proxy-Schaetzung visuell abgegrenzt | `docs/infrastruktur/cer.html` |
| Quality Proxy (E53) | Corpus-wide OCR quality: Median Hit Rate 97.7%, 92% >=90%, Sprach-Audit 99.6% korrekt | [QUALITY-PROXY](QUALITY-PROXY.md) |
| TEI-Diagnostik | Schema-Validierung, Warning-Tracking, Diagnostik-UI (`docs/infrastruktur/diagnostik.html`) | [TEI-QUALITY](TEI-QUALITY.md) |

---

## Quick Start

1. **Understand the project:** [PROJEKT](PROJEKT.md) -- Scope, milestones, team
2. **Understand the pipeline:** [PIPELINE](PIPELINE.md) -- the 7-stage pipeline (PDF -> TEI-XML)
3. **Know the material:** [QUELLENANALYSE](QUELLENANALYSE.md) -- 285 documents, 4 document types
4. **View the dashboard:** `docs/index.html` -- Metrics, engine comparison, pipeline status
5. **Check status:** [DECISIONS](DECISIONS.md) -- what is decided, what is blocking?
6. **Last session:** [JOURNAL](JOURNAL.md) -- chronological work log

---

## Directory Structure

```
knowledge/
+-- INDEX.md              # This index (MOC)
+-- PROJEKT.md            # Vision, ecosystem, milestones
+-- PIPELINE.md           # Technical pipeline documentation
+-- QUELLENANALYSE.md     # Corpus, document types, pilot files
+-- ENGINES.md            # OCR + Layout engines: Mistral, DeepSeek, Docling, Gemini
+-- TEI-MAPPING.md        # TEI transformation rules
+-- GND-STRATEGIE.md      # NER + Entity Linking
+-- TESTPLAN.md           # Test phases, metrics, results
+-- INFRASTRUKTUR.md      # Azure, Podman, GitLab, CI/CD
+-- EDITION.md            # Digital edition (architecture, data, pages)
+-- DESIGN.md             # Hersch Design System (tokens, Seuil, Etonnement, Dark Mode)
+-- CURATION.md           # Curation editor (server, API, editing)
+-- DECISIONS.md          # Decided + Open items (prioritized)
+-- ZBZ-WORKFLOW.md       # ZBZ editorial workflow + integration points
+-- JOURNAL.md            # Chronological work journal
+-- JOURNAL-ARCHIVE.md    # Arbeitsjournal Sessions 1-26 (Archiv)
+-- PROMPTOTYPING.md       # Operative Werkzeuge, CLI-Referenz, Arbeitszyklus
+-- METHODIK.md            # Epistemische Infrastruktur, Verifikationskaskade
+-- QUALITY-PROXY.md        # OCR quality proxy (dictionary hit rate, language audit)
+-- PLAN.md                # Implementation plan (phases 0-6 + cross-cutting)
```

---

## Maintenance

- **New fact?** Add to exactly one document, cross-reference from others
- **New decision?** Document in [DECISIONS](DECISIONS.md)
- **End session?** Update [JOURNAL](JOURNAL.md)
- **Duplication found?** Eliminate immediately, add cross-reference

---

*Created: 2026-01-29 | Updated: 2026-03-26*
