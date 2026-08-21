# Claude Code Rules

Project constitution. Operative rules and conventions that apply at every pipeline step.

## Workflow

1. Keep the journal: document each session as an entry following journal template v0.2 in [knowledge/journal.md](knowledge/journal.md); newest entry at the very top of the entries section, with the fields Occasion / Goal / Course / Decisions / Status / Next steps (the format contract and a copyable entry template live in the journal itself). Sessions 1-68 remain unchanged in the compact archive.
2. Knowledge lives in `knowledge/`: do not duplicate it in CLAUDE.md. Single source of truth per fact.
3. Do not version output: generated files belong in `output/` (gitignored). Exceptions: `data/curated_tei/` (reserved for hand-verified TEI, currently empty) and the generated mirror `docs/data/`, versioned because it carries the GitHub Pages delivery.
4. Test before changing: run the evaluation, compare metrics.
5. Single source of truth: every fact lives in exactly one document. Other documents point to it via cross-reference.

## Knowledge Base

The entry point is [knowledge/index.md](knowledge/index.md), covering navigation, dependencies, and key concepts.

Thematically separated documents:

- [project.md](knowledge/project.md): mission, corpus, ZBZ workflow, status
- [specification.md](knowledge/specification.md): requirements, quality method, validation rule catalog, epics + user stories
- [pipeline.md](knowledge/pipeline.md): 6-stage pipeline, engines, TEI mapping
- [workflow.md](knowledge/workflow.md): end-to-end data flow, viewer + editors, save/round-trip, provenance
- [reports/2026-06-07_ecosystem-synthesis.md](reports/2026-06-07_ecosystem-synthesis.md): historical snapshot, overall picture of the three projects (zbz / szd-htr / teiCrafter) + frontend gap survey
- [infrastructure.md](knowledge/infrastructure.md): Azure, Podman, CI/CD, viewer deployment
- [methodology.md](knowledge/methodology.md): Promptotyping + epistemic infrastructure
- [decisions.md](knowledge/decisions.md): decision register
- [cer-methodology.md](knowledge/cer-methodology.md): CER measurement method (definition, reference choice, fidelity/scope, extraction and normalization rules, verification)
- [literature-comparison.md](knowledge/literature-comparison.md): print-OCR state of research and comparability caveats
- [ground-truth-map.md](knowledge/ground-truth-map.md): the 25 reference TEIs, phenomenon map and exception catalog
- [entity-integration.md](knowledge/entity-integration.md): design plan for the GND entity integration (input data, target model, three-tier matching, milestones, verification)
- [entity-evaluation.md](knowledge/entity-evaluation.md): sampling workflow for the entity layer (facsimile-adjudicated precision and recall, agreement check, statistics, consequences)
- [agent-orchestration.md](knowledge/agent-orchestration.md): multi-agent wave pattern (wave contract, protocol files, verdict schemes, verification of self-reports against disk)
- [arbeitsbericht-v3.md](knowledge/arbeitsbericht-v3.md): the project report (German, client-facing); measured values are in `docs/data/cer_statistics.json`
- [journal.md](knowledge/journal.md): chronological session overview
- [refactoring-plan.md](knowledge/refactoring-plan.md): temporary working plan of the 2026-08 repository refactoring, deleted at closure
- [index.md](knowledge/index.md): navigation + key concepts

## Security

- NEVER read `.env`: the `.env` file contains API keys and must under no circumstances be read, displayed, or included in output
- no secrets in code or docs: API keys, tokens, and passwords live exclusively in environment variables

## Code Conventions

- Code comments: English only, compact, and only where genuinely needed, for constraints the code itself cannot show. No explanations of the obvious, no origin or change notes (no "added 2026-06-10", no "fixes H1") in code; decision provenance belongs in [knowledge/decisions.md](knowledge/decisions.md) or the journal.
- No personal names in Markdown: in repo Markdown (knowledge/, README, reports/) use roles and organizations (ZBZ, DHCraft, project management). Jeanne Hersch as the subject of the corpus is exempt.
- No cost figures: do not name monetary amounts or budgets (USD/$/CHF/EUR) in docs, reports, or code. Operational hints such as `free`/`paid` (= no/one API call) are allowed, since they steer calls rather than quantify costs.
- Markdown style (prospective): in new repo Markdown no `**` bold as emphasis (a paragraph label becomes a heading of the appropriate level or running text) and no `&mdash;` or dash as a connector (use a comma, a semicolon, a colon before a list set on its own lines, or a separate sentence). This applies prospectively; existing text is not rewritten wholesale. Exception: the bold field labels of the journal template remain.
- No volatile quantities in durable documents: document and page counts, percentages, and test counts do not belong in durable Markdown documents (README, permanent knowledge/ docs); phrase them qualitatively and point to the generating source (`corpus_audit` for corpus counts, validator/audit for tallies, `docs/data/cer_statistics.json` for CER values). Fixed defining quantities remain (the 25 ground-truth reference TEIs, pinned library versions, dates, decision/warning identifiers, document IDs). Dated snapshot documents (journal.md entries, the decisions.md register, reports/) and generator-bound tables (e.g. project.md §Corpus) are exempt; there the number is the point.
- Windows encoding: no Unicode special characters in print statements
- Paths: absolute paths or `pathlib`
- Output: JSON for data, HTML for reports
- Frontend: ES6+ JavaScript (`const`/`let`, arrow functions, template literals, IIFE wrappers), `ZBZ.*` namespaces (viewer code under `ZBZ.Viewer`)
- Frontend dependencies: loaded at runtime via CDN, no npm/build pipeline:
  - OpenSeadragon 5.0.1 (jsDelivr): facsimile renderer in view mode (E58)
  - JSZip 3.10.1 (cdnjs): planned for the ZIP export module (E61), not yet included in the code

## Design

For UI or frontend generation, the token catalog `docs/assets/css/tokens.css` is the authority for values; the design rationale is in [knowledge/workflow.md](knowledge/workflow.md), Hersch Design System section. Imperative design principles:

- exclusively `--h-*` tokens, never hex values directly in component CSS
- accent colors (brick red, Prussian blue, olive green) apply to accents and status indicators, not to surfaces
- no pure black/white values; always the warm anthracite `--h-text` and the warm cream `--h-bg`
- for new components, first check whether an existing token or a component in `base.css` already covers it

The token catalog lives in `docs/assets/css/tokens.css`, base components in `docs/assets/css/base.css`, viewer-specific styles in `docs/assets/css/viewer.css`.

## Project Structure & Data Flow

### Directories (orientation)

- `data/`: input and reference data. `source/` = ZB delivery (immutable input, mostly gitignored) with `pdf/`, `reference_tei/`, `transkribus_page_xml/`, `masterfile/Masterfile.xlsx`, and `guidelines/` (editorial guidelines, Editionsrichtlinien). Project authority (git-tracked): `schema/zbz_hersch.rng`, `curated_tei/` (reserved for hand-verified TEI, currently empty) and `entities/` (curated entity list, GND variant cache, variant review, mention verdict store, legacy mention index `legacy_mentions.json`, operator marking policy). Generated: `doc_metadata.json` (Gemini cache)
- `scripts/`: pipeline + tools, grouped by domain into `ocr/`, `layout/`, `tei/`, `eval/`, `edition/`, `core/` (only `config.py` + `utils.py` top-level). Inventory: [scripts/README.md](scripts/README.md)
- `output/`: all generated data streams (gitignored, NOT versioned)
- `docs/`: static inspection/demo site (GitHub-Pages-ready) with HTML, `assets/` (`css/` + `js/`), `data/` (generated mirror), `images/`
- `knowledge/`: knowledge base, entry point [knowledge/index.md](knowledge/index.md)
- `tests/`: pytest suites

### Object = bundle of parallel data streams

An object (document) carries several streams, all following the `{doc_id}_p{N}` convention:

- OCR: `output/mistral_results/` (base); alternative engines: `output/ocr_results/`, `gemini_corrected_{a,b}/`, `llm_corrected_c/`
- Layout / PAGE-XML: `output/layout/` (Docling + Gemini, JSON) -> `output/page_xml/` (PAGE-XML + METS export)
- TEI: `output/tei_unified/` (pipeline output) -> `output/tei_final/` (final, delivered)
- Per-object metadata: `{doc_id}_manifest.json` (workflow status per stream + history + blank pages, E65/E66) next to the final TEI. Legacy: `_screening_legacy.json` (abolished agent screening, kept only as a diagnostic trace, gitignored).

Detailed stages, scripts, and engines are in [knowledge/pipeline.md](knowledge/pipeline.md).

### Source of truth -> generated mirror (binding)

- `output/tei_final/{doc}_final.xml` is the single source of truth of the delivered TEI data (E43). Only `tei_final/` is displayed. Every final TEI carries a `<revisionDesc>` with pipeline status (E42); at the ZBZ handover step the per-stream workflow status is projected from the manifest into the `<revisionDesc>` via `tei_status_marker.py` (E66).
- `docs/data/pages/{doc}/` is a GENERATED mirror; never edit it directly. It is produced by `scripts/edition/generate_edition_data.py` from per-page TEI (split from `tei_final`) + Mistral `.md` + layout JSON. After changes to the source, regenerate the mirror.
- `output/tei_unified/` is pipeline output (do not edit). Hand-verified TEIs are intended for `data/curated_tei/` (git-tracked); the folder is currently empty.

## Methodology

Three-layer split Command / Artifact / Tool; details in [knowledge/methodology.md](knowledge/methodology.md).

- Command = decision rule (when to do what)
- Artifact = material tool in the repo (script, index, report)
- Tool = a concrete invocation of an artifact by the agent

Verification cascade (ordered by economy): automatic -> contextual -> visual -> domain-expert.
Operative tools and the working cycle are in [knowledge/methodology.md](knowledge/methodology.md).

---

# Commands (CLI reference)

Operative tools for the Promptotyping cycle. Every operation produces quality signals
that inform the next step. The Critical Expert in the Loop decides.

The methodological embedding (diagnosis -> exploration -> execution -> re-validation -> escalation)
is described in [knowledge/methodology.md](knowledge/methodology.md), as are the conventions
for `--dry-run`, `--force`, and `--reassemble`.

## Diagnosis

```bash
python -m scripts.tei.tei_validator --doc {DOC_ID}             # TEI validation
python -m scripts.tei.tei_validator --all --html-report         # corpus report
python -m scripts.tei.tei_validator --compare-ref               # reference comparison (25 ZBZ reference TEIs)
python -m scripts.eval.evaluate_ocr --all                            # OCR metrics
python -m scripts.eval.quality_proxy --all --html                    # quality proxy (hit rate)
python -m scripts.eval.completeness_check --html                     # completeness check (pages)
python -m scripts.eval.benchmark_cer --all --html                    # CER benchmark (25 GT docs)
python -m scripts.eval.cer_statistics_full --seed 42 --bootstrap-n 10000  # scientific CER statistics (percentile bootstrap CIs, paired, HCPR)
python -m scripts.eval.corpus_audit                             # corpus audit: corpus funnel + drift check
python -m scripts.eval.structure_audit                          # structure audit: pipeline TEI vs 25 ground truth (diagnosis, no gate; E84)
python -m scripts.eval.reading_order_audit                      # W19 triage robust/fragile (E90; --worklist: fragile pages per document)
python -m scripts.tei.tei_reading_order_fix                     # W19 worklist instrument, dry-run default; corpus reorder empirically refuted (E99), --write only for facsimile-verified pages
python -m scripts.eval.stability_pilot --dry-run                # run-to-run stability pilot scope (real run: paid Step-2 calls, E100)
python -m scripts.eval.char_lint_audit                          # character normalization audit: apostrophes, guillemets, space classes (E92)
python -m scripts.eval.pb_number_audit                          # pb@n plausibility + per-document semantics classification (E92)
python -m scripts.eval.hi_preservation_audit                    # OCR emphasis signal survival into tei_final (E92/E93)
python -m scripts.eval.relation_integrity_audit                 # next/prev pairs, anchors, title-main, sp/speaker (E92)
python -m scripts.eval.body_note_audit                          # body-as-note candidates (footnote overdetection, E92)
python -m scripts.eval.blank_text_audit                         # hallucinated text on blank pages: manifest + Docling zero-region channel (diagnosis, no gate)
python -m scripts.eval.running_head_audit                       # running-head (Kolumnentitel) zones, validated against adjudicated marks (E105 follow-up, diagnosis)
python -m pytest tests/test_cer_statistics.py -q                # statistics library (bootstrap CIs, paired, HCPR)
python -m pytest tests/test_corpus_audit.py -q                  # corpus invariants + delivered distribution + completeness gate
python -m pytest tests/test_scripts_health.py -q                # script health: syntax + internal imports (all scripts/)
python -m pytest tests/test_tei_schema.py -q                    # schema gate: tei_final against zbz_hersch.rng (E68)
python -m pytest tests/test_tei_header.py -q                    # teiHeader delivery contract: idno + biblStruct + langUsage (E69)
python -m pytest tests/test_tei_validator.py -q                 # validator: reference CER in percent (O24/E69)
python -m pytest tests/test_pb_split.py -q                      # <pb> segmentation: pb_split.py byte-identical (E69)
python -m pytest tests/test_tei_conformance.py -q               # conformance fixes: div-n/type, figure-xmlid, head-lemma, title-main, foreign-lang (E84)
python -m pytest tests/test_reading_order.py tests/test_reading_order_audit.py tests/test_reading_order_fix.py -q  # reading order: permutation + W19 triage + in-place instrument (E90/E99)
python -m pytest tests/test_stability_pilot.py -q               # stability pilot: aggregation + statistics wiring (E100)
python -m pytest tests/test_char_lint_audit.py tests/test_pb_number_audit.py tests/test_hi_preservation_audit.py tests/test_relation_integrity_audit.py tests/test_body_note_audit.py -q  # guideline-conformity audits (E92)
python -m pytest tests/test_char_normalize.py tests/test_pb_folio.py tests/test_body_note_demote.py tests/test_marker_common.py tests/test_status_marker.py tests/test_completeness_check.py tests/test_step1_filter.py -q  # stock-correction tools + shared marker scaffolding + step-1 fixes (E92/E94)
```

The output `docs/data/cer_statistics.json` is versioned as evidence of the published CER values and deterministically regenerable with seed 42. The interactive CER dashboard was abolished with E56. The methodology is covered in [knowledge/specification.md](knowledge/specification.md), quality measurement section.

## Text layer

```bash
python scripts/ocr/ocr_pipeline.py -i data/source/pdf/{DOC_ID}.pdf -e mistral    # base OCR
python -m scripts.ocr.gemini_ocr_correct --doc {DOC_ID} --variant B          # Gemini correction
python -m scripts.ocr.gemini_ocr_correct --doc {DOC_ID} --dry-run            # preview
python -m scripts.ocr.classify_docs                                          # one-shot Gemini document classification -> data/doc_metadata.json (committed cache; rerun only to rebuild it)
```

## Layout

```bash
python -m scripts.layout.run_layout_analysis --doc {DOC_ID}                     # Docling
python -m scripts.layout.layout_qa_gemini --doc {DOC_ID}                        # Gemini QA
python -m scripts.layout.layout_qa_gemini --mode detect --doc {DOC_ID}          # re-detection
python -m scripts.layout.generate_layout_overlays --doc {DOC_ID} --compare      # overlay
```

## Generate TEI

```bash
python -m scripts.tei.tei_unified --doc {DOC_ID}                         # standard (3 stages)
python -m scripts.tei.tei_unified --doc {DOC_ID} --step 1                # scaffold only (free)
python -m scripts.tei.tei_unified --doc {DOC_ID} --reassemble            # re-assembly (Gemini cache; curated pages 1 call each)
python -m scripts.tei.tei_unified --doc {DOC_ID} --force                 # everything anew (incl. Gemini)
python -m scripts.tei.tei_unified --doc {DOC_ID} --dry-run               # prompt preview
python -m scripts.tei.tei_unified --all --reassemble                     # corpus re-assembly
```

## Validation (quality gate)

```bash
python -m scripts.tei.tei_validator --doc {DOC_ID}                       # single document
python -m scripts.tei.tei_validator --all --report                       # JSON report
python -m scripts.tei.tei_validator --all --html-report                  # HTML report
```

## Stock corrections (operator-gated, E94)

Reversible marker runs on `output/tei_final/`, each with backup, idempotent, and
audit-measured before/after. Always run `--dry-run` first; after a real run, re-run
the matching audit plus `tei_validator --all` and the pytest gates.

```bash
python -m scripts.tei.tei_char_normalize --dry-run               # apostrophe normalization preview
python -m scripts.tei.tei_char_normalize                         # run (backup: output/_backup_pre_char_normalize/)
python -m scripts.tei.tei_pb_folio --dry-run --strip-folio-echo  # printed-folio pb@n + footer-echo preview
python -m scripts.tei.tei_pb_folio --strip-folio-echo            # run (backup: output/_backup_pre_pb_folio/)
python -m scripts.tei.tei_body_note_demote --dry-run --promote-footnotes  # verdict-driven demotion preview
python -m scripts.tei.tei_body_note_demote --promote-footnotes   # run (backup: output/_backup_pre_body_note_demote/)
```

The demotion run consumes the facsimile-verified verdicts in
`output/audits/body_note_verdicts.json` (E94) and never touches notes judged genuine.

## Entity integration (M0-M3 reached, M4 instrument built, M5-M7 open; plan: knowledge/entity-integration.md)

The operator marking decisions live in `data/entities/marking_policy.json`, apart from the
curated list because that list is an external export. It is validated on load and reaches
the matcher through `build_lexicon(..., policy_path=...)`; the matcher-driving entity scripts
(`entity_lint`, `tei_entity_preview`, `entity_corpus_scan`, `entity_gold_benchmark`,
`entity_unlisted_scan`) take `--policy` and default to that file (E119).

```bash
python -m scripts.tei.fetch_gnd_variants                         # build/refresh the GND variant cache (lobid)
python -m scripts.eval.entity_lint                               # entity list + cache + legacy pairing + marking policy audit
python -m scripts.tei.tei_entity_preview --panel                 # preview over the 10 pilot documents (tei_final untouched)
python -m scripts.tei.tei_entity_preview --all                   # preview over the whole corpus; every mark carries @resp/@cert/@source (E118)
python -m scripts.eval.entity_corpus_scan                        # read-only corpus scan: candidates, distributions, invariants
python -m scripts.edition.generate_entity_preview_data           # viewer entity mirror (docs/data) from the previews
python -m scripts.edition.generate_entity_overview               # per-document entity overview (docs/entities.html) from the corpus scan
python -m scripts.tei.tei_cover_strip --dry-run                  # E-Periodica cover sheets: strip preview (real run operator-gated)
python -m scripts.eval.entity_gold_benchmark                     # M4: precision/recall against the 25 reference TEIs
python -m scripts.eval.entity_corpus_digest                      # tier-1 harvest as one context-window digest
python -m scripts.eval.entity_unlisted_scan                      # id-free proposal channel: name-shaped surfaces outside the list
python -m scripts.eval.entity_eval_sample --seed 42             # evaluation draw: 300 tier-1 marks + 40 pages, stratified, frozen (knowledge/entity-evaluation.md)
python -m scripts.eval.build_mention_verdicts                    # mention verdict store: adjudicated judgments -> data/entities/mention_verdicts.json (snapshot-bound, deterministic)
python -m scripts.eval.entity_verdict_guard                      # regression gate: adjudicated verdicts vs current scan, exit 1 on violations (E110)
python -m scripts.eval.entity_risk_ranking                       # rank tier-1 marks by FP risk -> output/audits/fp_hunt/ (wave protocol: PROTOCOL.md)
python -m pytest tests/test_entity_matcher.py tests/test_entity_lint.py tests/test_entity_regressions.py tests/test_entity_preview.py tests/test_entity_corpus_scan.py tests/test_generate_entity_preview_data.py tests/test_cover_strip.py tests/test_fetch_gnd_variants.py tests/test_mention_verdicts.py tests/test_entity_verdict_guard.py tests/test_entity_ref_invariant.py tests/test_entity_risk_ranking.py tests/test_entity_corpus_digest.py tests/test_entity_eval_sample.py tests/test_entity_gold_benchmark.py tests/test_entity_stream.py tests/test_entity_unlisted_scan.py tests/test_variant_review.py -q  # entity gates
```

The viewer shows the previews read-only via `viewer.html?doc={DOC_ID}&entities=1` or the viewer's view selection.

## Quality screening (deprecated, E66)

The agent-based 7-layer screening has been abolished since E66 (2026-05-26). None of the
285/285 "APPROVED" statuses came from a human; the agent certified itself with a built-in
ignore list (W3/W6/W10 as "normal"). Findings now live as `_screening_legacy.json`
(a pure diagnostic trace, not in the mirror). The replacement is the workflow status
per stream (see below).

Tools for validation remain:

```bash
python -m scripts.tei.tei_validator --doc {DOC_ID}                       # RelaxNG + project rules
python -m scripts.tei.tei_validator --compare-ref --doc {DOC_ID}         # against ZBZ reference
```

## Per-object manifest (blank pages + workflow status, E65/E66)

```bash
python -m scripts.edition.page_manifest                                          # all docs (idempotent: status+history preserved)
python -m scripts.edition.page_manifest --doc {DOC_ID}                           # single document
python -m scripts.edition.page_manifest --dry-run                                # report only, write nothing
python -m scripts.tei.tei_blank_marker --dry-run                         # blank-page marker: preview
python -m scripts.tei.tei_blank_marker                                   # write <pb type="blank"/> into tei_final (with backup)
python -m scripts.tei.tei_status_marker --dry-run                        # workflow history -> revisionDesc: preview
python -m scripts.tei.tei_status_marker                                  # write history as <change> into tei_final (with backup, ZBZ handover)
```

The per-object manifest `output/tei_final/{DOC_ID}_manifest.json` is the annotation slot per object:
- `streams.{ocr,layout,tei,entities}.status`: workflow status (unverifiziert | in_arbeit | verifiziert, three levels since E77). Traffic-light mapping in the UI: neutral/gray for `unverifiziert`, yellow for `in_arbeit`, green for `verifiziert`, red reserved for a future problem status.
- `streams.{ocr,layout,tei,entities}.history`: provenance of the human editing steps (the `entities` stream mirrors the preview layer, not the delivered TEI)
- `pages.{N}`: exception pages (currently only safe blank pages; OCR rule + Docling=0)

`page_manifest` automatically fills only engine descriptors and the safe `blank` class;
status/history are added exclusively by the viewer (click on the status pill) and survive
re-runs. `tei_blank_marker` projects blank pages as `<pb type="blank"/>`;
`tei_status_marker` deterministically projects the workflow history as `<change>` entries into the
`<revisionDesc>` and clears away the misleading agent-screening entries in the process. Afterwards
regenerate the mirror: `python -m scripts.edition.generate_edition_data --mirror-only`.
Details are in [knowledge/decisions.md](knowledge/decisions.md) E63/E65/E66.

## Viewer data

```bash
python -m scripts.edition.generate_edition_data                                  # catalog (data/catalog.json) + per-page mirror
```

The viewer (`docs/viewer.html`) is a static single-page app without a backend. A single "Save"
button persists all unsaved streams at once (layout, text/TEI, manifest, E78); writes go
directly into the working tree (File System Access API, Chromium) or fall back to a file download.
Every save action stores the payload twice: canonically to `output/` (really consumed by
`--reassemble`, E72) and into the mirror `docs/data/`, so the server-less viewer (docroot `docs/`)
shows the saved state after a reload (E79). Per-stream single downloads live in the "Export"
dropdown. See [knowledge/workflow.md](knowledge/workflow.md), persistence section.

## Visual artifacts

```bash
python scripts/edition/extract_pages.py --pdf {DOC_ID}.pdf --dpi 300             # page images
python -m scripts.layout.generate_layout_overlays --doc {DOC_ID} --compare      # layout overlay
```

## Transkribus export / upload (PAGE-XML round trip)

Pipeline PAGE-XML (`output/page_xml/`) goes back to Transkribus in two steps: first build the bundle,
then upload via REST. Concept and dialect details are in
[knowledge/pipeline.md §Transkribus Export](knowledge/pipeline.md).

```bash
python -m scripts.edition.transkribus_export --sample                            # stratified sample -> output/transkribus_upload/
python -m scripts.edition.transkribus_export --all                               # full corpus
python -m scripts.edition.transkribus_export --reference                         # the reference objects ZBZ already has in Transkribus
python -m scripts.edition.transkribus_export --doc {DOC_ID} [--zip]              # targeted (+ optionally one .zip per object)
```

The upload needs the login as environment variables (NEVER in code/repo/.env): `TRANSKRIBUS_USER`,
`TRANSKRIBUS_PASSWORD`, optionally `TRANSKRIBUS_COLLECTION`. Every run creates NEW documents
(no dedup); run `--dry-run` first, then upload one test object.

```bash
python -m scripts.edition.transkribus_upload --dry-run --collection {COLL}       # check login + collection access, upload nothing
python -m scripts.edition.transkribus_upload --doc {DOC_ID} --collection {COLL}  # upload one object as a test
python -m scripts.edition.transkribus_upload --collection {COLL}                 # upload the whole bundle
```

---

# Help

- `/help`: help on using Claude Code
- Feedback: https://github.com/anthropics/claude-code/issues
