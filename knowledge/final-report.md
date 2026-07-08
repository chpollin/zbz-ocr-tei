---
title: Final Report (superseded)
type: report
project:
  name: zbz-ocr-tei
  repository: https://github.com/chpollin/zbz-ocr-tei.git
method:
  name: Promptotyping
  url: https://dhcraft.org/Promptotyping/
status: archived
language: en
created: 2026-05-27
updated: 2026-07-08
tags: [zbz-ocr-tei, report, superseded]
related: [specification, cer-methodology, literature-comparison, ground-truth-map]
---

# Final Report (superseded)

This document is no longer the project report. The single project report is the
German `reports/arbeitsbericht-v3.md`, the client-facing work report for the
Zentralbibliothek Zurich. On 2026-07-08 the parallel English `final-report.md` was
retired: its findings that lived only here were folded into the report, and its
detailed material was split into standalone reference documents under `knowledge/`.

Where the content went:

- The report: [`reports/arbeitsbericht-v3.md`](../reports/arbeitsbericht-v3.md).
  Headline CER, per-document breakdown, literature comparison, corpus proxy,
  language audit, examples, limits, and outlook.
- CER measurement method (definition, choice of reference, fidelity/scope,
  extraction rules E1-E12, normalization N1-N21, verification of the measurement):
  [cer-methodology.md](cer-methodology.md).
- Print-OCR state of research and comparability caveats:
  [literature-comparison.md](literature-comparison.md).
- Ground-truth map and reference exception catalog (former Appendix B):
  [ground-truth-map.md](ground-truth-map.md).
- Canonical measured values, deterministically regenerable (seed 42):
  `docs/data/cer_statistics.json`.

The consolidated requirement view remains [specification.md](specification.md);
the dated decision provenance remains [decisions.md](decisions.md).
