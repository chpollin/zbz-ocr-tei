# Adjudication protocol (entity evaluation, snapshot 2026-08-12)

Binding instructions for every adjudication agent. The sample is frozen; do not
regenerate it, do not rerun the corpus scan, do not modify any file outside
`output/audits/eval_sample/verdicts/`.

## Inputs

- Precision cases: `output/audits/eval_sample/precision_cases.json` (300 cases, p001..p300)
- Recall pages: `output/audits/eval_sample/recall_pages.json` (40 pages, r001..r040)
- Facsimile per case: `docs/images/{doc}/{doc}_p{NNN}.png` (open with the Read tool)
- Pipeline output per page: `docs/data/pages/{doc}/{doc}_entity_p{N}.xml` (tier-1 wraps)
  and `docs/data/pages/{doc}/{doc}_entity_worklist.json` (tier-2 entries, keyed by page)
- Page text: `docs/data/pages/{doc}/{doc}_p{N}.xml` (pipeline TEI of the page)
- Entity list: `data/entities/all_entities.json` (persons/organisations/works,
  headword `name`/`orgName`/`title`, id field `GND_id`)
- Name variants: `data/entities/gnd_cache.json` (entries keyed by gid)

## Precision verdicts (one per case)

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

Judge independently. Do not read any other agent's verdict file.

## Recall records (one list per page)

Read the page text and the facsimile side by side. Record EVERY mention of a listed
entity on that page (persons, organisations, works from `all_entities.json`,
including name variants from the cache and obvious inflected/genitive forms).
Ignore entities that are not on the list. A blank page yields an empty list.
The author of the corpus (Jeanne Hersch, gid 118815679) counts as a mention like
any other; record it where it appears in the page body (not in running headers).

For each mention, compare with the pipeline output of the same page:

- `hit`: wrapped in `{doc}_entity_p{N}.xml` with the right gid
- `on_worklist`: present in the worklist entries of that page
- `missed`: in neither

Every `missed` gets exactly one cause label:

- `lexicon_gap`: the surface form is not derivable from list + cache (missing variant)
- `rule_gap`: the form exists in the lexicon world but no matcher rule reaches it
  (unusual inflection, split, casing) - judge by plausibility and say why
- `ocr_corruption`: the page text is garbled at this position, the clean form never
  existed in the text stream

## Output format

Write ONLY to your assigned output file under `output/audits/eval_sample/verdicts/`.

Precision agents write a JSON list:
`[{"case_id": "p001", "verdict": "correct", "reason": "<one short English sentence>"}, ...]`

Recall agents write a JSON object:
`{"r001": {"doc": "...", "page": N, "mentions": [{"surface": "...", "gid": "...",
"status": "hit|on_worklist|missed", "cause": "<only when missed>",
"note": "<short English>"}]}, ...}`

Reasons and notes are English, compact, one sentence. Every case/page of your range
must appear exactly once. If an image file is missing, verdict `undecidable` with
the reason naming the missing path.

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
