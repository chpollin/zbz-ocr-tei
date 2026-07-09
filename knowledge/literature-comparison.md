---
title: Literature Comparison (Print OCR State of Research)
type: knowledge
project:
  name: zbz-ocr-tei
  repository: https://github.com/chpollin/zbz-ocr-tei.git
method:
  name: Promptotyping
  url: https://dhcraft.org/Promptotyping/
status: reviewed
language: en
created: 2026-07-07
updated: 2026-07-09
tags: [zbz-ocr-tei, cer, literature, benchmark]
related: [cer-methodology, specification, decisions]
---

# Literature Comparison (Print OCR State of Research)

Reference document that places the pipeline's fidelity CER in the state of
research on OCR of printed historical documents. It carries the comparison table
and the comparability caveats that a report can only reference in compact form.
The pipeline's own headline values are in `docs/data/cer_statistics.json` and are
reported in `arbeitsbericht-v3.md`, section 6.3; the measurement method is
in [cer-methodology.md](cer-methodology.md).

## Where the Pipeline Sits

The fidelity median of 1.28% (n = 25, canonical value from
`docs/data/cer_statistics.json`) lies between the best specialized print stack
(Transkribus with LLM post-correction, 0.84%; Greif et al. 2025) and
Transkribus alone (3.67%). That is solid for historical print but not at the top;
the technical optimum is reached only by the best individual documents (0.3 to
0.8%). The comparison reads print-calibrated, since the Transkribus quality bands
(under 2% publication-ready, 2 to 5% research-usable) stem primarily from
handwriting recognition practice and set the bar lower than a pure print OCR task
warrants.

## Comparison Table

| Source | Method | Language | CER |
| :---- | :---- | :---- | :---- |
| Greif et al. 2025 | Transkribus Print M1 + Gemini 2.0 Flash post-correction | deu (mostly Fraktur) | 0.84% |
| Greif et al. 2025 | Gemini 2.0 Flash zero-shot | deu (mostly Fraktur) | 1.27% |
| Greif et al. 2025 | Transkribus Print M1 alone | deu (mostly Fraktur) | 3.67% |
| Greif et al. 2025 | GPT-4o direct | deu (mostly Fraktur) | 6.31% |
| Kanerva and Ledins 2025 | GPT-4o LLM-as-judge (no ground truth) | multilingual historical | 6.30% |
| Levchenko 2025 | Gemini 2.5 Pro | rus (18th c.) | 3.36% |
| Levchenko 2025 | Gemini 2.5 Flash | rus | 4.94% |
| Levchenko 2025 | traditional OCR | rus | 21-45% |
| Transkribus documentation | guide value | general | 0.5-2% |

## Comparability Caveats

No entry is a like-for-like benchmark; each differs from the Hersch corpus in at
least one dimension. The machine-readable comparability flags in
`docs/data/cer_statistics.json` (block `comparison_lit`) record these dimensions
per entry.

- Greif et al. 2025 (arXiv:2504.00414): German-language address books 1754-1870,
  predominantly Fraktur with one Antiqua source, a different corpus, and in the
  leading row a multimodal post-correction. This is the lower bound of the
  state of research and the most demanding reference point; comparability partial
  (script, corpus, method). The values were previously misattributed here to
  Crosilla, Klic, Colavizza 2025 (arXiv:2503.15195), an HTR benchmark that does
  not contain them; corrected 2026-07-09 (see decisions.md).
- Kanerva and Ledins 2025 (arXiv:2502.01205): GPT-4o-class, no-ground-truth
  evaluation. Methodologically related to the dictionary-hit-rate proxy but on
  different corpora; comparability partial (method, corpus).
- Levchenko 2025 (arXiv:2510.06743): Russian, 18th-century Civil Font, not
  like-for-like with French and German Antiqua; comparability false (language,
  script, corpus). Also the source of the frequency-based HCPR adaption used for
  diacritic preservation. A peer-reviewed version appeared in the LM4DH 2025
  workshop at RANLP 2025 (Varna, pages 75-85, DOI 10.26615/978-954-452-106-6-007).
- The Transkribus guide value is a general orientation band, not a measured
  corpus result.

## Related

- [cer-methodology.md](cer-methodology.md): how the pipeline's own CER is measured
- [specification.md](specification.md): the quality-measurement requirement and print calibration (E80)
- [decisions.md](decisions.md): E80 print calibration, E91 counter-check
