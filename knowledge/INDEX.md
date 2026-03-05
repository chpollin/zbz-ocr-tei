---
type: moc
created: 2026-01-29
updated: 2026-03-05
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
| [PLAN](PLAN.md) | What are the implementation phases? | Development | PROJEKT, PIPELINE |

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

PLAN      <-- implementation phases, depends on PROJEKT + PIPELINE
DECISIONS <-- cross-cutting, collects from all docs
JOURNAL   <-- chronological, references all docs
```

---

## Key Concepts

| Term | Definition | Document |
|------|-----------|----------|
| Pipeline | Full end-to-end pipeline: PDF -> TEI-XML (7 stages) | [PROJEKT](PROJEKT.md) |
| 7-Stage Pipeline | Images -> OCR -> Layout -> PAGE-XML -> NER/GND -> TEI-XML -> Evaluation | [PIPELINE](PIPELINE.md) |
| Document Types A-D | Single-column, Two-column, Monograph, Special | [QUELLENANALYSE](QUELLENANALYSE.md) |
| DTA-Basisformat | TEI base schema with ZBZ customizations | [TEI-MAPPING](TEI-MAPPING.md) |
| NER + GND | Named Entity Recognition + GND linking (Phase 2) | [GND-STRATEGIE](GND-STRATEGIE.md) |
| CER / WER | Character Error Rate / Word Error Rate | [TESTPLAN](TESTPLAN.md) |
| Hybrid Pipeline | Docling (Layout) + LLM-OCR (Text) combined | [PIPELINE](PIPELINE.md) |
| PAGE-XML | Intermediate format for Layout+OCR (Schema 2013-07-15) | [PIPELINE](PIPELINE.md) |
| Dashboard | QA UI with metrics, engine comparison, and document catalog | [PIPELINE](PIPELINE.md) |
| METS-XML | Multi-page manifest for PAGE-XML packages | [PIPELINE](PIPELINE.md) |
| TEI Generator | Layout-JSON + OCR -> page-level TEI-XML (DTA-Basisformat) | [PIPELINE](PIPELINE.md) |
| docling-serve (E24) | Layout analysis via REST API (Docker), no local GPU needed | [PIPELINE](PIPELINE.md) |
| Gemini Layout QA (E25) | Vision-based correction of Docling layout results, both versions preserved | [PIPELINE](PIPELINE.md) |
| Gemini Layout Detect (E26) | Full re-detection for bad pages via Gemini Vision, 3 modes (qa/detect/auto) | [PIPELINE](PIPELINE.md) |
| Gemini Classify (Stage 1a) | Visual classification of all 286 docs (type, language, pub_form, title, author) | [PIPELINE](PIPELINE.md) |
| doc_metadata.json | Central metadata file from Gemini classification, TEI-mappable | [PIPELINE](PIPELINE.md) |
| Online-Demo (E28) | 4 DEMO docs on GitHub Pages with fallback paths in shared.js | [PIPELINE](PIPELINE.md) |

---

## Quick Start

1. **Understand the project:** [PROJEKT](PROJEKT.md) -- Scope, milestones, team
2. **Understand the pipeline:** [PIPELINE](PIPELINE.md) -- the 7-stage pipeline (PDF -> TEI-XML)
3. **Know the material:** [QUELLENANALYSE](QUELLENANALYSE.md) -- 289 texts, 4 document types
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
+-- DECISIONS.md          # Decided + Open items (prioritized)
+-- ZBZ-WORKFLOW.md       # ZBZ editorial workflow + integration points
+-- JOURNAL.md            # Chronological work journal
+-- PLAN.md               # Implementation plan (phases 0-5)
```

---

## Maintenance

- **New fact?** Add to exactly one document, cross-reference from others
- **New decision?** Document in [DECISIONS](DECISIONS.md)
- **End session?** Update [JOURNAL](JOURNAL.md)
- **Duplication found?** Eliminate immediately, add cross-reference

---

*Created: 2026-01-29 | Updated: 2026-03-05*
