---
type: knowledge
created: 2026-02-18
updated: 2026-03-06
tags: [zbz-ocr-tei, decisions, open, decided]
status: active
---

# Decisions

Consolidated register of all decisions and open questions in the project.

**Dependencies:** Cross-cutting — collects from all documents.

---

## Decided

| # | Decision | Rationale | Date | Document |
|---|----------|-----------|------|----------|
| E1 | Hybrid pipeline: Docling (layout) + LLM-OCR (text) | Layout analysis without OCR, OCR separately | 2026-01-29 | [PIPELINE](PIPELINE.md) |
| E2 | Docling only for layout, not for OCR | RapidOCR has encoding problems (e → O) with French text | 2026-01-29 | [ENGINES](ENGINES.md) |
| E3 | Deterministic first, LLM only for complex cases | Reproducible, cost-effective, debuggable | 2026-01-29 | [PIPELINE](PIPELINE.md) |
| E4 | 4 document types (A-D) classified | Different pipeline strategies needed | 2026-01-29 | [QUELLENANALYSE](QUELLENANALYSE.md) |
| E6 | Mistral OCR 3 as production engine | ZBZ has Azure access, no GPU required | 2026-02-14 | [ENGINES](ENGINES.md) |
| E7 | Quotation remains unchanged | Azure integration no additional effort | 2026-02-14 | [PROJEKT](PROJEKT.md) |
| E8 | Configurable API endpoints | Switch between local and Azure OCR | 2026-02-14 | [INFRASTRUKTUR](INFRASTRUKTUR.md) |
| E9 | Containerization with Podman | ZBZ does not use Docker, Podman is OCI-compatible | 2026-02-14 | [INFRASTRUKTUR](INFRASTRUKTUR.md) |
| E10 | Fork on GitLab Uni Zuerich | ZBZ runs its own instance | 2026-02-14 | [INFRASTRUKTUR](INFRASTRUKTUR.md) |
| E13 | Export as PAGE-XML + METS for coOCR | coOCR expects PAGE-XML (2013-07-15, Transkribus standard) + PNG, not Markdown | 2026-02-20 | [PIPELINE](PIPELINE.md) |
| E14 | Preserve Markdown formatting | coOCR stores text as-is in `<Unicode>`, formatting must not be removed | 2026-02-20 | [PIPELINE](PIPELINE.md) |
| E15 | Dashboard redesign: multi-page UI with shared CSS/JS | Unified design system, static JSON data basis, engine visibility, light theme | 2026-02-25 | [PIPELINE](PIPELINE.md) |
| E16 | Page-by-page comparison for monographs (>10 TEI pages) | Global alignment fails at 140+ pages; content matching resolves variable PDF/TEI offsets | 2026-02-25 | [PIPELINE](PIPELINE.md) |
| E17 | LLM correction optional, not default | Worsens docs with CER <5%; benefit only at CER >10% | 2026-02-25 | [PIPELINE](PIPELINE.md) |
| E18 | Content-based page matching instead of fixed offset | TEI facs numbers ≠ PDF page numbers (cover pages, blank pages); fixed offset drifts | 2026-02-25 | [PIPELINE](PIPELINE.md) |
| E19 | Layout analysis: Docling + Gemini hybrid | Docling (mAP 0.699, free, 17 classes) as primary; Gemini as optional validator (updated to 3.1 Flash Lite, see E25); Kraken as fallback | 2026-02-25 | [ENGINES](ENGINES.md) |
| E20 | Docling 2.75 confirmed as layout engine (Phase 0) | Type sample passed: all 4 document types correctly detected, column separation Type B works, 0.4-3.3s/page | 2026-02-25 | [ENGINES](ENGINES.md) |
| E21 | Scope expansion: full pipeline in zbz-ocr-tei | After meeting 25.02.: OCR + layout + PAGE-XML + NER/GND + TEI-XML. ZBZ keeps Transkribus in parallel | 2026-02-25 | [PLAN.md](PLAN.md) |
| E22 | TEI generator: directly from layout+OCR to TEI (without PAGE-XML) | Will be extended later when PAGE-XML/NER exist. Entity annotation from seed dict (KNOWN_ENTITIES) | 2026-02-25 | [PIPELINE](PIPELINE.md) |
| E23 | Data delivery Feb 2026: 286 PDFs + 25 TEI-XMLs + 24 PAGE-XML exports | PAGE-XML schema 2013-07-15. PAGE-XML pages empty (no text). Transkribus Collection-ID: 1886177 | 2026-02-27 | [QUELLENANALYSE](QUELLENANALYSE.md) |
| E24 | docling-serve API for layout analysis (no local GPU needed) | Docker container (`docling-serve-cpu`), same Docling RT-DETR V2 model, identical output format to `run_layout_analysis.py`. CPU ~27s/page, GPU Cloud Run ~28ms/page. Tested on Doc 2310 (3 pages, 24 regions). Optional Cloud Run deployment for production speed | 2026-03-03 | [PIPELINE](PIPELINE.md) |
| E25 | Gemini 3.1 Flash Lite as Layout QA validator | Overlay-PNG + Layout-JSON to Gemini Vision, corrected JSON back. Both versions preserved (epistemic infrastructure). Structured Output via `response_schema`. SDK: `google-genai`. Cost: ~$4 for 7,200 pages | 2026-03-03 | [PIPELINE](PIPELINE.md) |
| E26 | Gemini Layout Detect mode (3.1 Flash Lite) | Docling fails on ~15% of pages (bad+empty) (landscape, multi-column, dense). Detect mode sends raw scan to Gemini Vision, returns regions with `box_2d` coordinates. Three modes: `qa` (label fix), `detect` (full detection), `auto` (detect for bad, qa for good). Quality scoring routes pages automatically. Flash Lite equivalent quality at ~10x lower cost. Auto mode running on all 286 docs | 2026-03-04 | [PIPELINE](PIPELINE.md) |
| E27 | Gemini-basierte Dokumentklassifikation (Stage 1a) | 271/286 Docs ohne Metadaten. Heuristiken versagen (7/15 Pilot-Docs falsch). Gemini 3.1 Flash Lite analysiert erste 5 Seiten visuell, extrahiert language/pub_form/layout_type/title/author/date/description. Structured Output. 286/286 erfolgreich, 80% Typ-Match mit Pilot-Ground-Truth. doc_metadata.json als zentrale Quelle fuer Dashboard + teiHeader | 2026-03-05 | [PIPELINE](PIPELINE.md) |
| E28 | Online-Demo: 4 DEMO-Docs auf GitHub Pages | Vollstaendige Daten nur lokal (output/ gitignored). 4 Beispieldokumente (2310/A, 1000/B, 1330/D, 1540/C) unter docs/ committet: Bilder (docs/images/), OCR+Layout (docs/data/examples/). shared.js mit Fallback-Pfaden (primaer ../output/, Fallback data/examples/). Disclaimer-Banner + DEMO-Badges im Katalog | 2026-03-05 | [PIPELINE](PIPELINE.md) |
| E29 | Gemini OCR-Korrektur (Stage 2b) | Zwei-Schritt: Analyse (Structured JSON: Fehler identifizieren + begruenden) + Korrektur (Text anwenden). Zwei Varianten: A=text-only mit Metadaten-Kontext, B=multimodal mit Scan-Bild. Gemini 3.1 Flash Lite. Sample 5 Docs: Variante A avg CER 3.30% (Mistral 3.97%, -0.67pp), Variante B avg CER 3.45% (4 Docs, -0.52pp). Hauptgewinn bei Doc 2310 (7.00%->3.88%). Kosten: ~$1-3 fuer 4,152 Seiten. Viewer-Integration mit Toggle-Button + CER-Balken | 2026-03-05 | [PIPELINE](PIPELINE.md) |
| E30 | Gemini Vision TEI Generator + Dokumenttypspezifische Prompts | Neuer `tei_gemini.py` ersetzt regelbasierten `tei_generator.py`. Default: 1 Call/Seite (Struktur+Inline), optional --refine und --consolidate. Overlay-PNG als Schluesselinput. 4-Ebenen dokumenttypspezifische Prompts (Layout-Typ, Publikationsform, Genre, Sprache) in `layout_qa_gemini.py` und `tei_gemini.py`. 12 Genre-spezifische TEI-Prompts. Genre-Inference aus description via Keyword-Matching. Pilot Doc 2310: persName/bibl/lb/div Recall 1.0. Kosten: TBD nach Sample-Run (Flash Lite) | 2026-03-06 | [PIPELINE](PIPELINE.md) |
| E31 | Layout-QA Full Run + Overlay-Generator | Full re-run `--mode auto --force` auf 286 Docs: 3,992/4,152 Seiten (160 failed), 14,708 Korrekturen, 894 ADDED Regionen, avg Score 72.7. `changes_summary` Logging (Label-Transitions pro Seite, aggregiert in summary_gemini.json). Neues `generate_layout_overlays.py`: Batch-Overlay-PNGs mit Changed-Highlighting + Side-by-side Docling-vs-Gemini Compare (7,988 PNGs). Visuelle QA: Gemini klar besser als Docling allein (mehr Regionen, fehlende Headers/Headings/Footnotes erkannt, zweispaltige Layouts korrekt) | 2026-03-06 | [PIPELINE](PIPELINE.md) |
| E32 | Unified TEI Pipeline (Rule-Based Scaffold + Gemini Refinement) | 4-Stufen-Pipeline: Step 1 (enhanced rule-based TEI mit lb, head, note, semantic div), Step 2 (Gemini Refinement mit Mapping-Table-Prompt, 1 Call/Seite), Step 3 (Document Assembly mit teiHeader/facsimile/body), Step 4 (RelaxNG Validation). Mapping-Table-Prompt statt Few-Shot: 8 Sektionen + 10 Genre-Regeln. Post-Processing `fix_gemini_tei()` mit 6 Fix-Stufen fuer Gemini-Strukturfehler. Entity-Re-Annotation (`reannotate_entities()`) als tag-aware Post-Processing. Interview-Speaker-Erkennung in Step 1 Scaffold. Pilot: 2310 persName/bibl 1.0, 1440 speaker 0.76 lb 1.0 bibl 1.0. Alle 3 Docs RelaxNG-valide. Kosten Step 2: ~$17 fuer 286 Docs | 2026-03-06 | [PIPELINE](PIPELINE.md) |
| E33 | Digitale Edition (`docs/edition/`) | Oeffentliche statische Website neben dem internen Dashboard. 4 Seiten (Landing, Katalog, Reader, About), eigenes Design-System (Parchment/Navy/Gold, Dark Mode, 3 Breakpoints). `ZBZ.Edition` Namespace (ES5/IIFE). Reader: Faksimile+TEI nebeneinander, draggbarer Divider, Entitaeten-Sidebar, XML-Ansicht. Katalog: 286 Docs, MiniSearch, facettierte Filter. DRY-Refactoring: Nav/Footer JS-Slot-Pattern, `buildCardHtml()`, `sanitizeDocId()`, CSS-Klassen statt Inline-Styles. 12 Dateien, ~3.200 Zeilen | 2026-03-06 | [PIPELINE](PIPELINE.md) |

---

## Open Questions

| # | Question | Context | Blocks | Clarification by |
|---|----------|---------|--------|------------------|
| O6 | Normalization vs. source fidelity (incl. heading typography) | Clarification with expert Baehler pending | Phase 3 TEI | ZBZ |
| O8 | Metadata from ALMA/MMSID | MMSIDs needed for teiHeader | Phase 3 TEI | ZBZ |
| O9 | div-type values front/back matter | editorial, context, translation etc. | Phase 3 TEI | Own decision |
| O11 | Entities without GND entry | Local ID or leave empty? | Phase 2 NER | Own decision |
| O13 | TEI editorial details (subject headings, GND work records in back matter) | Who creates subject headings? Do they go in teiHeader? | Phase 3 TEI | ZBZ |
| O18 | Test multimodal LLM correction (scan image + OCR text) | Research shows <1% CER (arXiv:2504.00414); currently text only | Quality | Own test |
| ~~O21~~ | ~~Layout region post-processing~~ | Resolved by E25/E26: Gemini QA corrects labels, Detect re-detects bad pages. No manual heuristics needed | — | Closed |
| O22 | 289 vs. 286 PDF discrepancy | Masterfile counts 289 texts, E23 delivery contains 286. 3 missing unidentified | Clarification | ZBZ |

---

## Risks

| # | Risk | Impact | Mitigation | Status |
|---|------|--------|------------|--------|
| R2 | TEI complexity + schema incompatibility | High | Reference TEI as ground truth, incremental implementation, schema validation | Open |
| R3 | GND hallucinations | Medium | Seed dictionary + confidence threshold | Open |
| R5 | Fork divergence between DHCraft and ZBZ | Medium | Define merge strategy, CI-based tests | Open |
| R7 | Transkribus incompatibility PAGE-XML | High | Schema 2013-07-15, ID scheme `{NNNN}_p{NNN}`, JPG format. @type/@custom not verifiable (no TextRegions in export) | Partially clarified (E23) |
| R10 | NER quality on French (66% corpus) | Medium | Seed dictionary as first layer BEFORE LLM NER | Open |

---

## References

- [PROJEKT](PROJEKT.md) for milestones and status
- [PIPELINE](PIPELINE.md) for pipeline decisions
- [TEI-MAPPING](TEI-MAPPING.md) for open TEI questions (O6, O8-O9, O13)
- [JOURNAL](JOURNAL.md) for chronological decision history

---

*Created: 2026-02-18 | Updated: 2026-03-06*
