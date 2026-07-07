---
title: "Methodology: Epistemic Infrastructure and Promptotyping"
type: knowledge
project:
  name: zbz-ocr-tei
  repository: https://github.com/chpollin/zbz-ocr-tei.git
method:
  name: Promptotyping
  url: https://dhcraft.org/Promptotyping/
status: complete
created: 2026-03-15
updated: 2026-07-07
dependencies: [pipeline, viewer]
source: "papers/Paper.md (workshop contribution DHd/DH, DHCraft & ZBZ)"
---

# Methodology

Epistemic infrastructure, verification cascade, Critical Expert in the Loop, and the
operative Promptotyping cycle. Unifies the former `METHODIK.md` and `PROMPTOTYPING.md`.

---

## Epistemic Infrastructure

Agent reliability does not scale with model capability alone but with the quality of the
epistemic infrastructure in which the model operates (evidenced by SWE-bench vs. SWE-bench
Pro, ~60 percentage points difference with identical models).

For agents the repository is not a storage location but their primary interface. Three
properties must hold:

- Readability: every artifact has a documented purpose ([CLAUDE.md](../CLAUDE.md), knowledge
  docs); new artifacts must be reflected there (maintenance duty).
- Consistency: paths, naming, and data formats follow uniform conventions. What was learned
  on one document holds for all.
- State transparency: the processing state of every object is machine-queryable (JSON
  reports, `<revisionDesc>` in the TEI header).

---

## Verification Cascade

Four levels, ordered economically (cheap first, expensive last):

1. Automatic: schema validation, Python tests. Binary, fast, filters obvious errors.
2. Contextual: an LLM checks content plausibility against the project context. Graded result
   (plausible/questionable/implausible).
3. Visual: facsimile comparison by a vision-capable agent or LLM-as-judge. A different
   modality means epistemic diversity.
4. Domain: domain expertise, not delegable. The edition scholar decides on ambiguities.

The operative effect is that each level reduces the case set for the next. Domain expertise
is focused on its highest-value area of application (asymmetric amplification).

---

## Operative Cycle (Promptotyping)

Five steps, iterative (aligned with ReAct's thought-action-observation loop):

1. Diagnosis: the agent determines the state via diagnostic artifacts (read the validation
   report). Act on findings, not on assumptions.
2. Exploration: prioritize the corrective measure by the largest quality gain. Structural
   errors before reference errors before formatting.
3. Execution: the agent invokes an artifact. Where API costs arise, use `--dry-run` and
   check back.
4. Re-validation: run the diagnosis again, compare before and after. Every unverified change
   is a hypothesis, not an improvement.
5. Escalation: after a defined number of iterations or on stagnation, hand the problem to the
   right expert in the loop.

Termination conditions are a maximum of 2-3 cycles per document, a stagnation indicator, and
error-pattern detection.

---

## Critical Expert in the Loop

Several roles with separated competencies prevent circular validation (anchoring effect,
evidenced by Schroeder et al. 2025):

- DH developer: process configuration (prompts, scripts, thresholds). Does not interact with
  scholarly content.
- Edition scholar: scholarly assessment of the results. Did not configure the process.
- Project management: prioritization and acceptance.

The core principle is that the person who produced a result (or whose agent produced it) is
not the same person who reviews it scholarly.

---

## Three-Layer Model: Command / Artifact / Tool

| Layer | What | Example |
|---|---|---|
| Command | decision rule (when, under which conditions) | "Validate after every TEI correction" |
| Artifact | material tool (versioned, maintainable) | `tei_validator.py`, `corpus_audit.py`, [CLAUDE.md](../CLAUDE.md) |
| Tool | concrete invocation by the agent | `python -m scripts.tei.tei_validator --doc 290` |

Commands without artifacts stay abstract. Artifacts without commands lie unused. Tools
without commands are ad-hoc actions. Only the interplay of all three layers produces the
cyclic, quality-assured work process.

Artifacts are fed-back output, at once a result of the process and input for the next cycle.
The epistemic infrastructure grows reactively on quality signals.

---

## Quality Assurance: from Agent Screening to Workflow Status (E66)

Originally an agent-based 7-layer screening lived here (285 docs, 242 APPROVED / 43
WITH_NOTES). It was abolished with E66; no human had granted the "APPROVED" labels, the
agent certified itself with a built-in ignore list, and the label was misleading toward ZBZ.

The replacement is a human-set workflow status per stream (`unverifiziert | in_arbeit |
verifiziert` for each of OCR/layout/TEI, three levels since E77), set in the viewer, with a
provenance history in the per-object manifest and a projection into the `<revisionDesc>`.
The verification cascade remains the principle; only the domain level is now explicitly
human instead of agentic. Details in [workflow.md](workflow.md), workflow status section.

---

## Operative Tools (CLI)

CLI operations along the pipeline stages. Every operation produces or transforms a knowledge
artifact and generates machine-readable quality signals.

The complete CLI reference lives in the project-internal [CLAUDE.md](../CLAUDE.md) §Commands.
The list below is the methodically ordered selection (diagnosis -> correction ->
re-validation).

### 1. Diagnosis: determine the state

```bash
python -m scripts.tei.tei_validator --doc {DOC_ID}            # TEI validation
python -m scripts.tei.tei_validator --all --html-report        # corpus report
python -m scripts.tei.tei_validator --compare-ref              # reference comparison (25 ZBZ reference TEIs)
python -m scripts.eval.evaluate_ocr --all                           # OCR metrics
python -m scripts.eval.quality_proxy --all --html                   # quality proxy (hit rate)
python -m scripts.eval.completeness_check --html                    # completeness check (pages)
python -m scripts.eval.benchmark_cer --all --html                   # CER benchmark (25 GT docs)
python -m scripts.eval.cer_statistics_full --seed 42 --bootstrap-n 10000  # scientific CER statistics
python -m pytest tests/test_cer_statistics.py -q               # 55 tests for the statistics library
```

The output is `docs/data/cer_statistics.json` (deterministic; the HTML dashboard that
formerly existed alongside it was abolished with E56, the data remains available as JSON).

### 2. Improve the text layer

```bash
python scripts/ocr/ocr_pipeline.py -i data/source/pdf/{DOC_ID}.pdf -e mistral   # base OCR
python -m scripts.ocr.gemini_ocr_correct --doc {DOC_ID} --variant B         # Gemini multimodal
python -m scripts.ocr.gemini_ocr_correct --doc {DOC_ID} --dry-run           # preview
```

### 3. Layout

```bash
python -m scripts.layout.run_layout_analysis --doc {DOC_ID}                    # Docling
python -m scripts.layout.layout_qa_gemini --doc {DOC_ID}                       # Gemini QA
python -m scripts.layout.layout_qa_gemini --mode detect --doc {DOC_ID}         # re-detection
python -m scripts.layout.generate_layout_overlays --doc {DOC_ID} --compare     # overlay
```

### 4. Generate TEI

```bash
python -m scripts.tei.tei_unified --doc {DOC_ID}                        # standard (3 steps)
python -m scripts.tei.tei_unified --doc {DOC_ID} --step 1               # scaffold only (no API call)
python -m scripts.tei.tei_unified --doc {DOC_ID} --reassemble           # re-assembly (Gemini cache; curated pages 1 call each)
python -m scripts.tei.tei_unified --doc {DOC_ID} --force                # everything anew (incl. Gemini)
python -m scripts.tei.tei_unified --doc {DOC_ID} --dry-run              # prompt preview
python -m scripts.tei.tei_unified --all --reassemble                    # corpus re-assembly
```

### 5. Validation (quality gate)

```bash
python -m scripts.tei.tei_validator --doc {DOC_ID}                      # single document
python -m scripts.tei.tei_validator --all --report                      # JSON report
python -m scripts.tei.tei_validator --all --html-report                 # HTML report
```

### 6. Workflow status (replaces agent screening, E66)

The agent screening is abolished. Status is set by humans in the viewer; the CLI covers
validation and status projection:

```bash
python -m scripts.tei.tei_validator --doc {DOC_ID}                      # RelaxNG + project rules
python -m scripts.tei.tei_validator --compare-ref --doc {DOC_ID}        # against ZBZ reference
python -m scripts.tei.tei_add_revision --all                            # write revisionDesc
python -m scripts.tei.tei_status_marker                                 # workflow history -> revisionDesc (ZBZ handover)
```

The output is `output/tei_final/{DOC_ID}_final.xml` plus `{DOC_ID}_manifest.json` (workflow
status + history).

### 7. Visual artifacts

```bash
python scripts/edition/extract_pages.py --pdf {DOC_ID}.pdf --dpi 300            # page images
python -m scripts.layout.generate_layout_overlays --doc {DOC_ID} --compare     # layout overlay
```

---

## Conventions

- Document IDs follow the pattern `{DOC_ID}` (e.g. 2310, 2530, 1440).
- Outputs go to `output/` subdirectories (gitignored, except `data/curated_tei/`).
- `--dry-run` is available on all API-using tools. Use it before batch operations that incur
  API calls.
- `--force` overwrites cached results. Only sensible after actual upstream changes.
- `--reassemble` applies the rule-based fixes (step 1 scaffold + step 3 assembly) and uses
  the Gemini step 2 cache; only pages with newer curated OCR/layout are selectively
  re-refined (1 Gemini call each) so the curation reaches the final TEI. `--force` re-refines
  the whole document.

---

## Literature

- Yang et al. (2024). *SWE-agent: Agent-Computer Interfaces.* NeurIPS 2024. Scaffolding beats model capability.
- Kamoi et al. (2024). *When Can LLMs Actually Correct Their Own Mistakes?* TACL. Self-correction needs external feedback.
- Schroeder, Roy, Kabbara (2025). *Just Put a Human in the Loop?* Findings of ACL. Anchoring effect with LLM suggestions.
- Yao et al. (2023). *ReAct: Synergizing Reasoning and Acting.* ICLR 2023. Thought-action-observation loop.
- He et al. (2026). *Speed at the Cost of Quality.* MSR 2026. Speed without infrastructure creates technical debt.
- Zhang et al. (2025/2026). *Agentic Context Engineering (ACE).* arXiv. Accumulated context knowledge compensates model capability.

---

## References

- [pipeline.md](pipeline.md): technical pipeline architecture
- [workflow.md](workflow.md): the viewer as verification environment
- [specification.md](specification.md): quality method and validation rules
- [CLAUDE.md](../CLAUDE.md): project rules, complete CLI reference
