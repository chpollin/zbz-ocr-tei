---
type: knowledge
created: 2026-01-29
updated: 2026-03-26
tags: [zbz-ocr-tei, gnd, ner, entity-linking, wikidata]
status: active
---

# Entity Linking Strategy (NER + GND)

Strategy for Named Entity Recognition and entity linking in the Hersch edition project. Since E50: **Dual-Attribut-Strategie** -- GND als primaere Referenz im TEI-Output (wie Editionsrichtlinien), interne IDs (zbz-p.N) als Arbeits-Referenz in `corresp`. Entity Index bleibt Single Source of Truth.

> **Scope:** zbz-ocr-tei performs NER + entity linking (Phase 3 in [PLAN.md](PLAN.md)). Implementation: `scripts/ner/ner_extract.py` (Gemini NER) + `entity_index.py` (TEI indices) + `wikidata_linker.py` (Wikidata API). Entity Index (`data/entities/`) as foundation.

**Dependencies:** [TEI-MAPPING](TEI-MAPPING.md)

**Open questions:** See [DECISIONS](DECISIONS.md).

---

## Overview

Index compilation is a central editorial goal. All persons, organizations, places, and works shall be identified and linked. Dual-Attribut-Strategie (E50): GND in `ref`, interne ID in `corresp`.

### Entity Types (6)

| Type | TEI Element | ref (GND) | corresp (intern) | Example |
|------|-------------|-----------|-------------------|---------|
| Person | `<persName>` | `ref="GND:118557106"` | `corresp="#zbz-p.1"` | `<persName ref="GND:118557106" corresp="#zbz-p.1">Karl Jaspers</persName>` |
| Organization | `<orgName>` | `ref="GND:1010450-1"` | `corresp="#zbz-o.5"` | `<orgName ref="GND:1010450-1" corresp="#zbz-o.5">UNESCO</orgName>` |
| Place | `<placeName>` | `ref="GND:..."` | `corresp="#zbz-l.1"` | `<placeName corresp="#zbz-l.1">Paris</placeName>` |
| Work | `<bibl>` | `ref="GND:..."` | `corresp="#zbz-w.3"` | `<bibl ref="GND:1088036961" corresp="#zbz-w.3">Philosophie</bibl>` |
| Event | `<name type="event">` | `ref="GND:..."` | `corresp="#zbz-e.1"` | `<name type="event" corresp="#zbz-e.1">Mai 68</name>` |
| Date | `<date>` | — | — | `<date when="1947">1947</date>` |

### ID Hierarchy (E50)

1. **GND-ID** (ref): Primaere Referenz im TEI-Output, nur wenn im Entity Index vorhanden
2. **Internal ID** (corresp): Immer vorhanden, verweist auf Entity Index
3. **Wikidata QID**: Im Entity Index gespeichert (corresp-Attribut im Index), nicht im TEI-Attribut

### Entity Index (TEI-XML)

```
data/entities/
  person_index.xml    # <listPerson> mit <person xml:id="zbz-p.1" corresp="https://www.wikidata.org/wiki/Q123559">
  org_index.xml       # <listOrg>
  place_index.xml     # <listPlace>
  work_index.xml      # <listBibl>
```

Jeder Eintrag hat: `xml:id` (interne ID), optionales `corresp` (Wikidata-URL), `type="main"` + `type="variant"` Namensvarianten fuer String-Matching.

### Basic Rule

**Every mention is linked**, even when repeated within the same document.

**Exceptions (Editionsrichtlinien):**
- No markup in image captions (`<figure>/<p>`)
- No markup in `<div type="bibliography">/<listBibl>` (Lexikonartikel)
- Adjektivierte Personennamen (z.B. "kantien") werden nicht ausgezeichnet

---

## Pipeline Position

GND linking is the most complex step and requires external resources:

```
OCR → TEI base structure → NER → GND lookup → Validation → Manual QA
                           ↑
                     This step
```

### Implementation Options

| Approach | Description | Pros/Cons |
|----------|-------------|-----------|
| **Integrated** | LLM performs NER + GND lookup in a single step | Simpler prompt, but GND hallucinations possible |
| **Two-stage** | 1. LLM marks entities, 2. Separate GND lookup | More controlled, but more effort |
| **Post-hoc** | Generate TEI without GND, link GND separately | Decoupled, manual QA easier |

**Recommendation for PoC:** Post-hoc approach — validate TEI structure first, GND linking as a separate step.

---

## NER (Named Entity Recognition)

### Entities to Recognize

| Entity | Recognition Features | Difficulty |
|--------|---------------------|------------|
| **Persons** | Capitalization, first/last name, titles (Dr., Prof.) | Medium |
| **Organizations** | Capitalization, acronyms (UNESCO, UNO) | Medium |
| **Works** | Italicization, quotation marks, "his book X" | High |

### Challenges

1. **Multilingualism**: Mehrheitlich Franzoesisch (siehe [QUELLENANALYSE](QUELLENANALYSE.md) §Language Distribution) — different naming conventions
2. **Historical variants**: Name spellings may vary
3. **Context dependency**: "Jaspers" can be a person or a work (possessive: "Jaspers' Philosophie")
4. **Pronouns**: "He said..." — no linking for pronouns

---

## GND Lookup

### GND API

The GND provides a REST API for queries:

```
https://lobid.org/gnd/search?q=Karl+Jaspers&format=json
```

### Disambiguation

| Problem | Example | Solution Approach |
|---------|---------|-------------------|
| **Name collision** | Multiple "Martin Heidegger" in GND | Life dates, profession as filter |
| **Name variants** | "J. Hersch" vs. "Jeanne Hersch" | Alias search in GND |
| **Unknown persons** | Local figures without GND entry | Flag for manual processing |

### Entities in the Jeanne Hersch Context

Expected frequent entities (based on her work and biography):

| Person | GND-ID | Relevance |
|--------|--------|-----------|
| Karl Jaspers | 118557106 | Teacher, frequent reference |
| Martin Heidegger | 118547798 | Philosophical context |
| Hannah Arendt | 118502751 | Contemporary |
| Jean-Paul Sartre | 118605895 | Existentialism |
| UNESCO | (Corporate body) | Employer 1966–1968 |

---

## Entity Sources

### Available Sources

| Source | Description | Status |
|--------|-------------|--------|
| **TEI reference files** | 25 XMLs with GND links (E23: data delivery Feb 2026) | 25 TEI-XMLs available (E23); 18 extracted so far, 7 remaining to extract |
| **Masterfile.xlsx** | Bibliographic metadata | No entity list |
| **Alma/Swisscovery** | Nachlass catalog | Possibly linked authority data |

### Extracted GND Entities (29.01.2026)

**Script:** (deleted, superseded by NER Pipeline E34)
**Output:** `output/gnd_analysis/` (historical)

| Type | Count | Most Frequent |
|------|-------|---------------|
| Persons | 41 | Karl Jaspers (90x), GND:118557106 |
| Organizations | 10 | O.L.P. (4x), UNESCO (2x) |
| Works | 24 | Philosophie (3x), Die geistige Situation der Zeit (3x) |

**Top 5 Persons:**

| GND-ID | Name | Occurrences |
|--------|------|-------------|
| 118557106 | Karl Jaspers | 90 |
| 118815679 | Jeanne Hersch | 24 |
| 1145431410 | (Interviewer) | 23 |
| 118509578 | Bergson | 8 |
| 118562002 | Kierkegaard | 7 |

This list serves as the **seed** for the GND lookup.

---

## Implementation Options

### Option A: Prompt-based (LLM)

```
Identifiziere alle Personen, Organisationen und Werke im Text.
Für jede Entität:
1. Markiere mit dem entsprechenden TEI-Element
2. Suche die GND-ID (falls bekannt)
3. Wenn unsicher, markiere mit ref="GND:???"
```

**Risk:** LLM could hallucinate GND-IDs.

### Option B: Two-stage

**Stage 1 (LLM):**
```xml
<persName>Karl Jaspers</persName>  <!-- ohne ref -->
```

**Stage 2 (Script):**
- Extract all marked entities
- Lookup against GND API
- Add `ref` attributes
- Flag uncertainties for manual review

### Option C: Post-hoc (recommended for PoC)

1. TEI generation **without** GND linking
2. Separate NER on the TEI output
3. GND lookup with validation
4. Manual review for uncertainties

---

## Quality Assurance

### Metrics

| Metric | Description |
|--------|-------------|
| **Precision** | Share of correct GND links among all links |
| **Recall** | Share of found entities among all actual entities |
| **Disambiguation rate** | Share of unambiguously assigned GND-IDs |

### Error Classes

| Error Type | Example | Severity |
|------------|---------|----------|
| **Wrong GND-ID** | Wrong "Martin Mueller" linked | High |
| **Missing entity** | Person not recognized | Medium |
| **Hallucinated GND-ID** | GND-ID does not exist | High |
| **Missing link** | Person recognized but without GND | Low |

---

## Open Questions

- ~~How many unique GND-IDs are already in the reference TEIs?~~ → 75 entities
- What share of entities actually have a GND entry?
- Should GND linking be tested in the PoC or only later?
- How to handle entities without a GND entry? (Local ID? Leave blank?)

---

## Next Steps

1. [x] Extract GND-IDs from reference TEIs
2. [x] Frequency analysis of entities
3. [ ] Prototype GND API integration (lobid.org) — Phase 2
4. [x] Decision: NER + GND now in zbz-ocr-tei (E21 supersedes E5/E12)

---

## References

- [TEI-MAPPING](TEI-MAPPING.md) for TEI element specification
- [QUELLENANALYSE](QUELLENANALYSE.md) for corpus and languages
- [PIPELINE](PIPELINE.md) for pipeline position
- [DECISIONS](DECISIONS.md) O11 for open GND questions

---

*Created: 2026-01-29 | Updated: 2026-02-27 (25 instead of 18 TEI reference files after E23)*
