---
title: Ground-Truth Map and Reference Deviations
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
updated: 2026-08-21
tags: [zbz-ocr-tei, ground-truth, reference, tei]
related: [cer-methodology, specification, decisions]
authors: [Christopher Pollin]
---

# Ground-Truth Map and Reference Deviations

Reference document for the 25 reference TEIs (`data/source/reference_tei/`), read
in full against the editorial guidelines on 2026-07-07 (three parallel readers).
It records which guideline phenomenon is attested where and which known deviations
every reference-based check (CER benchmark, `structure_audit`, `--compare-ref`)
must treat as expected rather than as pipeline error. The measurement method that
consumes this map is in [cer-methodology.md](cer-methodology.md); provenance is
E85 in [decisions.md](decisions.md).

## Concordance Finding

The body coding of the references follows the guidelines in the load-bearing
conventions (genre div types, page breaks with bracketed supplied numbers,
hyphenation including the page-break rule, the footnote ID scheme
`fn{page}-{no}`, the inline GND entity model, the rendition vocabulary). Two
restrictions hold corpus-wide: no reference fulfils the header requirement (all
carry the raw Transkribus export stub instead of the ALMA citation with MMSID and
publication form, so header comparisons against the references are meaningless),
and all carry the undocumented root attribute `type="naegeli"`. The subfolder
`Pilot/` is a superseded precursor; the main set emerged from it by migrating work
references from `corresp="GND:…"` to `ref="GND:…"`, with document 560 as the
overlooked migration rest.

## Phenomenon Map (Best Exemplars)

| Phenomenon | Best evidence |
|---|---|
| Lexicon entry (`div type="entry"`, `head type="lemma"`, `bibliography` with `listBibl`) | 3040 |
| Review (`div type="review"`, head as `bibl` with GND) | 2310, 570; 560 with footnote in the review head |
| Interview (`sp`/`speaker`, speaker with GND persName) | 3020, 1440 |
| Double page (two `pb` sharing one `facs`, distinct `n`) | 760, 30, 2635 |
| Figures (`figure` with `xml:id`, `graphic`, `anchor` start/end pairs) | 760, 2635, 830 |
| Footnotes (`note place="foot"`, `@n`, `xml:id` per scheme) | 290, 130, 560 |
| Title structure (`title type="main"` plus several `sub`, persName in title) | 1060, 290, 100, 40 |
| Hyphenation across the page break | 1910 |
| Supplied page number `n="[…]"` | 290, 30, 3020, 90, 40, 760 |
| Dot-notation page numbers (`7.15`, `3.32`) | 760, 830 |
| `front` (editorial preface) | 890, 1410, 2635 |
| `back` (`translation` with MLA + Swisscovery `ref`, `reprint`, `otherEdition`) | 40, 1520, 300, 830 |
| `foreign xml:lang` (correct 3-letter codes) | 3020, 300, 90, 2635 |
| Renditions | `#i` throughout; `#u` 1060; `#b` 890; `#g` 90; `#sup` 3040 |
| `choice/sic/corr` | 1180, 2310, 3020, 570 |
| Entity density (persName/orgName/bibl with GND) | 580, 1330, 2635, 1910 |
| Lists, dialogue as `list` | 890, 2530, 1330, 300 |
| Table (`table/row/cell`), deep div nesting | only 1520 |
| `epigraph`, `div type="text"` (both outside the guideline catalog) | 1440 |

Never attested in the ground truth and therefore not validatable against it:
marginalia (`note place="right/left"`), multi-page footnotes with `@next`/`@prev`,
`unclear`, `gap`, the div types `conversation` and `dedication`, the renditions
`#sub` and `#k`. For these only the guideline itself applies.

## Known Deviations of the Ground Truth (Exception Catalog)

1. Header stub instead of ALMA header, all 25 (see above).
2. Root `type="naegeli"`, all 25; in 2310 with a whitespace defect.
3. Foreign-language practice split between document groups: correct
   `foreign xml:lang` in one group (300, 2635, 3020, 90), italics-only marking in
   another (1060, 1180, 1520); 1910 carries the literal placeholder
   `xml:lang="[fre]"`.
4. `break="yes"` as an undocumented, partly wrong value (1060, 1330, 2530, 30,
   3040, 890).
5. Only `rendition="#i"` is broadly realized; `#u`/`#b`/`#g`/`#sup` occur in one
   document each, `#sub`/`#k` never.
6. `rend="italic"`/`"bold"`/`"superscript"` instead of `rendition="#…"`: 2530,
   1180 (mixed within one paragraph), 1410, 3040.
7. GND references without the `GND:` prefix: 290, 1330, 1520, 3040 (there also one
   persName without any `ref`); `corresp` instead of `ref` on work `bibl`: 100,
   30, 560.
8. Adjectivized person names tagged against the guideline's own rule: 1910.
9. One footnote without `xml:id` beside correctly tagged siblings: 290.
10. Entities inside picture captions despite the explicit ban: 760 (systematic).
11. Data hygiene singletons: doubled uncorrected `choice` text (1910), trailing
    slash in `graphic` URLs (760, 2635, 830), a line-region ID as page `facs`
    (830), whitespace in a page number (560), `@n` on `p` instead of `lb` (90),
    `pb` without `facs` (1910, 3020), `pb` inside a paragraph (1060, 1440),
    lowercase line numbering with leading space (130), author credit in the text
    body (1410).
12. 3020 types a panel discussion as `interview` where the guideline reserves
    `conversation`; spoken exchange is coded as `sp` in 3020 but as a dash `list`
    in 300.

Reference 1520 is not well-formed: three structurally identical crossed
`item`/`p` nestings (around lines 6936, 6979, 6995; the parser reveals them only
one at a time). The repair swaps the closing-tag order to `</p></item>` at each
spot, leaving the text content unchanged; the corrected copy
`output/1520_reference_fixed.xml` parses cleanly. The original stays untouched as
the ZBZ source datum, and the correction goes to ZBZ as a proposal. The document is
measured inside the 25-document benchmark either way, because the text extraction
falls back to the regex rule E12 on a parse error; pending is only the ZBZ-side
repair of the reference file.

## Consequences

Reference-based checks measure against a ground truth that is guideline-true in
the body, empty in the header, and locally flawed; the exception catalog above
belongs in every scoring logic. The phenomena the ground truth never shows can
only be checked against guideline plus facsimile. The GND prefix and
`corresp`/`ref` drift matters for future entity work (teiCrafter lane): the
reference practice serves as a model only after normalization.

## Related

- [cer-methodology.md](cer-methodology.md): the measurement that consumes this map
- [specification.md](specification.md): the conformity rules and the reference-schema relation
- [decisions.md](decisions.md): E85 ground-truth map and E88 inline-GND model
