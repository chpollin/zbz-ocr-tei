> Versioned copy of the false-positive hunt protocol; the operative file lives in `output/audits/fp_hunt/PROTOCOL.md`.

# False-positive hunt protocol (tier-1 entity marks, snapshot 2026-08-12)

Binding instructions for every agent of the false-positive hunt. The ranking is frozen;
do not regenerate it, do not rerun the corpus scan, do not modify any file outside
`output/audits/fp_hunt/verdicts/`.

The hunt adjudicates automatic tier-1 marks in risk order instead of sampling them
evenly. `scripts/eval/entity_risk_ranking.py` scores every tier-1 mark by additive
features and sorts the corpus into three strata, so the wave buys its checked cases
where a false positive is most likely.

## Inputs

- Ranked cases: `output/audits/fp_hunt/risk_ranking.json`, list `marks`, case ids
  `f0001`, `f0002`, ... in risk order; the highest stratum comes first, so a low case
  number is a high-risk case
- Facsimile per case: `docs/images/{doc}/{doc}_p{NNN}.png` (open with the Read tool);
  the case record carries the path as `facsimile`
- Page text: `docs/data/pages/{doc}/{doc}_p{N}.xml` (pipeline TEI of the page)
- Pipeline entity output per page: `docs/data/pages/{doc}/{doc}_entity_p{N}.xml`
  (tier-1 wraps) and `docs/data/pages/{doc}/{doc}_entity_worklist.json` (tier-2 entries)
- Entity list: `data/entities/all_entities.json` (persons/organisations/works, headword
  `name`/`orgName`/`title`, id field `GND_id`)
- Name variants: `data/entities/gnd_cache.json` (entries keyed by gid)

Every case record carries `doc`, `page`, `surface`, `gid`, `category`, `rule`, `score`,
`features` and the surrounding `context`. Score and features say why the case was drawn
forward; they are never evidence for a verdict. The facsimile decides, and the scoring
contract is documented inside the ranking under `feature_doc`.

## Assignment

Cases are handed out as contiguous ranges of the ranking, highest stratum first, 50 cases
per agent. Each agent writes exactly one file
`output/audits/fp_hunt/verdicts/fp_{first}_{last}.json`, named after its range, for
example `fp_f0001_f0050.json`. An agent never writes into another agent's file and never
reads another agent's verdicts.

## Verdicts (one per case)

Look at the facsimile page, locate the surface, decide exactly one verdict:

- `correct`: the surface is on the page and refers to exactly the linked entity
  (gid), and the span covers the mention.
- `wrong_entity`: the surface exists but refers to a different person,
  organisation or work, or to no entity at all (generic word, term, title of a
  section rather than the listed work).
- `wrong_span`: right entity, wrong extent (partial name, swallowed punctuation,
  split across unrelated words).
- `not_in_source`: the page does not carry this surface at the claimed position
  (OCR phantom).
- `undecidable`: the page does not decide it. Use sparingly and say why.

Special rule: documents 120 and 1350 carry more `pb` elements than physical pages
(duplicate facs references), so their page-to-image mapping is broken. Every case in
doc 120 or 1350 gets `undecidable` with reason "facsimile mapping defect (pb/page
mismatch, known data defect)". Do not try to guess the right image.

Surfaces may contain `<lb/>` (line break inside a name); on the page the name then
spans two lines. That is still `correct` if entity and extent are right.

A bare surname is `correct` only when the page context makes the linked bearer the one
meant. Where two listed persons share the surname and the page leaves the bearer open,
the verdict is `wrong_entity` when the linked gid is the wrong bearer and `undecidable`
when the page decides nothing.

Judge independently. Do not read any other agent's verdict file.

## Output format

Write ONLY to your assigned output file under `output/audits/fp_hunt/verdicts/`.

A JSON list, one object per case:
`[{"case_id": "f0001", "verdict": "correct", "reason": "<one short English sentence>"}, ...]`

Reasons are English, compact, one sentence. Every case of your range must appear exactly
once, in ascending case id. If an image file is missing, verdict `undecidable` with the
reason naming the missing path.

## Guardrails (verbatim, binding)

- "NEVER read `.env`: the `.env` file contains API keys and must under no circumstances be read, displayed, or included in output"
- "no secrets in code or docs: API keys, tokens, and passwords live exclusively in environment variables"
- "Grokipedia is never used as a source, in any context"
- "Entity-Linking (GND/Wikidata-IDs) niemals per LLM, nur deterministische API-Lookups" (you judge existing links and record gids already on the list; you never introduce new ids)
- "No cost figures"
- "Windows encoding: no Unicode special characters in print statements"
- knowledge/arbeitsbericht-v3.md must never be touched
- output/tei_final/, data/, docs/, scripts/, tests/ must never be written; write access is limited to your single output file
- no commits, no pushes, no subagents

## After the wave

A confirmed false positive is fixed at its root cause, either as a reject verdict on the
offending name form in `data/entities/variant_review.json` or as a rule guard in
`scripts/tei/entity_matcher.py`, followed by a rerun of the corpus scan and the ranking.
Hand-editing the TEI in `output/tei_final/` or the mirror in `docs/data/` is never the
fix; it removes the symptom and leaves the rule that produced it in place. Both root-cause
paths are operator-gated steps outside this wave.

The verdict files are the mention verdict store of the hunt. Confirmed-correct verdicts
stay there, joined to the ranking by `case_id`, and carry the checked state of a mark
into the next snapshot, so a rerun re-adjudicates only what the scan actually changed.
