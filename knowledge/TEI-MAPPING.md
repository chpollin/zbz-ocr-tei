---
type: knowledge
created: 2026-01-29
updated: 2026-02-27
tags: [zbz-ocr-tei, tei, dta, mapping, transformation]
status: active
---

# TEI Mapping

Transformation rules from source text to TEI-XML following the DTA-Basisformat with project-specific adaptations.

> **Scope:** Since the scope expansion (25.02.2026), zbz-ocr-tei performs the TEI transformation itself (Phase 3 in [PLAN.md](PLAN.md)). This document is the implementation reference for `scripts/tei/tei_generator.py`. The rules apply to the entire pipeline.

**Dependencies:** [QUELLENANALYSE](QUELLENANALYSE.md)

**Sources:**
- `data/richtlinien/README.md` -- Project guidelines ZBZ
- `data/richtlinien/dta_basisformat_komplett.md` -- DTA reference
- `data/richtlinien/Auszeichnungsrichtlinien Hersch INTERN.docx` -- Internal guidelines

**Open Questions:** See [DECISIONS](DECISIONS.md).

---

## Core Principles

1. **Character-faithful reading text** with index annotation
2. **DTA-Basisformat** as foundation with project-specific adaptations
3. **Normalization** of certain characters (no diplomatic transcription)
4. **Every entity is linked**, even on repeated mention
5. **Source-faithful transcription** -- original text is preserved

---

## Document Structure

### Basic Skeleton

```xml
<?xml version='1.0' encoding='UTF-8'?>
<TEI xmlns='http://www.tei-c.org/ns/1.0' type="naegeli">
  <teiHeader>
    <!-- populated by script from ALMA -->
    <!-- contains: internal project ID, MMSID, PubForm (book, bookSection, journalArticle) -->
  </teiHeader>
  <text>
    <front><!-- optional: prefaces, context of origin --></front>
    <body>
      <pb facs="#f0001" n="1"/>  <!-- first page number BEFORE div n="1" -->
      <div n="1"><!-- main structure --></div>
    </body>
    <back><!-- optional: translation/reprint notes --></back>
  </text>
</TEI>
```

### Hierarchical Structure

| Level | Element | Usage |
|-------|---------|-------|
| 1 | `<div n="1">` | Main chapter |
| 2 | `<div n="2">` | Sub-chapter |
| 3 | `<div n="3">` | Section |

**Important:** `<pb>` elements are placed **inside** the `<div>` elements.

### Complete Structure Example

```xml
<text>
  <body>
    <div n="1">
      <pb facs="#f0001" n="1"/>
      <head>
        <title type="main">Temps alternés</title>
        <title type="sub">roman</title>
      </head>

      <div n="2">
        <head>Kapitel 1</head>

        <div n="3">
          <head>Unterkapitel 1.1</head>
          <p>Es geht hier um Philosophie</p>
        </div>

        <div n="3">
          <head>Unterkapitel 1.2</head>
          <p>Es geht hier genauer gesagt um die Philosophie von Jeanne Hersch</p>
        </div>
      </div>
    </div>
  </body>
</text>
```

---

## Character Normalization

> **Warning -- Open Question:** Should characters be normalized or preserved as in the source? Especially regarding French typographic conventions. Expert opinion (Baehler) pending.

### General Principle

According to internal guidelines (DOCX), **source fidelity** applies -- characters are rendered as they appear in the original:

| Element | Treatment |
|---------|-----------|
| ss (sharp S) | Transcribe as-is (U+00DF) |
| Horizontal dashes | As in source (em dashes, bullet dashes, range dashes, hyphens) |
| Brackets | As in source |
| Quotation marks | As in source |
| Heading typography | As in source |

### Normalization for LLM Pipeline

The README.md additionally defines normalization rules that may be relevant for **automated processing**:

| Source Character | Target Character | Unicode | Rule |
|------------------|------------------|---------|------|
| Hyphen-minus (-) | En dash (--) | U+2013 | Em dashes, bullet dashes, range dashes |
| Hyphen-minus (-) | Quarter-em dash (‐) | U+2010 | Hyphens and compound words |
| Straight double quotes (") | Typographic ("") | U+201C/U+201D | Double: "Double quotation marks" |
| Straight single quotes (') | Typographic ('') | U+2018/U+2019 | Single: 'Single quotation marks' |
| Apostrophe (') | Right single quotation mark (') | U+2019 | l'homme → l'homme |

**Clarification needed:** These rules must be coordinated with the team, as they may conflict with source fidelity.

### Whitespace

| Context | Rule |
|---------|------|
| Before `:` `;` `?` `!` | Delete |
| Enumerations with dashes | Normalize to `/` (Zuerich/Bern/Basel) |

### Special Characters

| Character | Treatment |
|-----------|-----------|
| ss | Preserve (U+00DF) |
| Ligatures (oe, ae) | Preserve |
| Accents (e, e, e, e, a, a, u, u, c, i, i, o) | Preserve |
| Brackets | As in source |

---

## Page Structure

### Page Break

```xml
<pb facs="#f0001" n="1"/>
<pb facs="#f0002" n="2"/>
<pb facs="#f0003" n="[3]"/>  <!-- page number not printed -->
```

| Attribute | Meaning | Format |
|-----------|---------|--------|
| `facs` | Reference to digitized image | `#f` + digitization number |
| `n` | Printed page number | Number or `[Number]` if missing |

**Rules:**
- Page numbers are **always rendered at the beginning of the page**
- The **first page number precedes `<div n="1">`**
- Page numbers are **not followed by a line/page break**
- Special features (ornaments, brackets around numbers) are not rendered

### Line Break

```xml
<lb facs="#facs_2_l_24" n="N001"/>
<lb facs="#facs_2_l_25" n="N002" break="no"/>  <!-- hyphenation -->
```

| Attribute | Meaning |
|-----------|---------|
| `facs` | Reference to line in Transkribus |
| `n` | Line number (N001, N002, ...) |
| `break="no"` | Word was hyphenated |

**Note:** Line breaks are preserved at the data level (`<lb>`), but are not displayed in the frontend.

### Hyphenation

**Source text:**
```
philo-
sophie
```

**TEI:**
```xml
philo<lb break="no"/>sophie
```

**Rules:**
- End-of-line hyphenation is **removed**
- The hyphenation character (NOT SIGN) is **deleted**
- `<lb break="no"/>` is placed **without a preceding space**
- For hyphenation across a **page break**: No `<lb break="no"/>`, replace NOT SIGN with hyphen (‐)

---

## Text Structure

### Paragraphs

```xml
<p facs="#facs_2_r_2">
  Text des Absatzes...
</p>
```

**Rules:**
- Paragraph structure is taken from the source
- First-line indentation is **not** encoded
- Markers for larger paragraph breaks (asterisks, rules) are **not** rendered

### Vertical Spacing

```xml
<space dim="vertical"/>
```

For larger gaps between paragraphs.

### Headings

```xml
<head>
  <title type="main">Haupttitel</title>
  <title type="sub">Untertitel</title>
</head>
```

**Rules:**
- Headings are tagged with `<head>`
- Typographic peculiarities of headings are **not** represented

### Lists

```xml
<list>
  <head>[optional: list title]</head>
  <item>1. [content of first list item]</item>
  <item>2. [content of second list item]</item>
  <item>[n]. [content of nth list item]</item>
</list>
```

**Important:** Numbering is realized **at the text level**, not as an attribute.

### Tables

```xml
<table>
  <head>[optional: table title]</head>
  <row>
    <cell>[table cell text]</cell>
    <cell>[table cell text]</cell>
  </row>
</table>
```

---

## Highlighting

| Rendering | TEI | Example |
|-----------|-----|---------|
| Bold | `<hi rendition="#b">` | `<hi rendition="#b">wichtig</hi>` |
| Italic | `<hi rendition="#i">` | `<hi rendition="#i">Philosophie</hi>` |
| Underlined | `<hi rendition="#u">` | `<hi rendition="#u">beachte</hi>` |
| Letter-spaced | `<hi rendition="#g">` | `<hi rendition="#g">Hervorhebung</hi>` |
| Superscript | `<hi rendition="#sup">` | `<hi rendition="#sup">1</hi>` |
| Subscript | `<hi rendition="#sub">` | `<hi rendition="#sub">2</hi>` |

**Important:** Only **semantically relevant** highlighting is encoded, not purely typographic features (e.g. small caps in headings).

---

## Language Switches

```xml
<foreign xml:lang="deu">deutscher Text</foreign>
<foreign xml:lang="eng">English text</foreign>
<foreign xml:lang="lat">Lorem ipsum</foreign>
```

Language codes follow **ISO 639-3**:

| Code | Language |
|------|----------|
| `fra` | French |
| `deu` | German |
| `eng` | English |
| `ita` | Italian |
| `lat` | Latin |

---

## Footnotes

### Simple Footnote

```xml
<p>
  Tel est le thème développé par Karl Jaspers dans son ouvrage
  La Foi philosophique
  <note place="foot" n="1" xml:id="fn125-1">
    Der philosophische Glaube, Piper Verlag, München, 1948.
  </note>
</p>
```

| Attribute | Meaning | Format |
|-----------|---------|--------|
| `place="foot"` | Footnote at page bottom | Constant |
| `n` | Original footnote number as printed | Number/character |
| `xml:id` | Unique ID | `fn[page number]-[number]` |

**Rules:**
- `<note>` is placed **directly at the text location** of the footnote marker
- The footnote marker itself is **not** rendered as a character
- The physical position at the page bottom is encoded via `@place="foot"`

### Multi-Page Footnote

```xml
<!-- page 125 -->
<note place="foot" n="1" xml:id="fn125-1" next="#fn126-1a">
  Beginning of footnote...
</note>
<lb/>

<pb facs="#f0126" n="126"/>

<!-- following page text to end -->

<note place="foot" xml:id="fn126-1a" prev="#fn125-1">
  ...continuation of footnote.
</note>
<lb/>
```

**Rules:**
- `<note>` is **closed before the page break**
- The continuation is captured where it appears in the text (usually at the page bottom)
- Linked via `@xml:id`, `@next`, and `@prev`

---

## Print Error Correction

```xml
<choice>
  <sic>Eclairement</sic>
  <corr>Éclairement</corr>
</choice>
```

**Internal guideline (DOCX):** Obvious print errors are **silently corrected**.

> **Note:** This means that `<choice>/<sic>/<corr>` may only be used for non-obvious errors. Clarification required.

---

## Index Entries (Entities)

### General Rule

**Every mention is referenced**, even on repetition. All `ref` attributes refer to the GND.

**Exceptions:**
- Entities in image captions are **not** annotated
- Avoid "nested" tagging where possible (e.g. person inside a work title)

### Persons

```xml
<persName ref="GND:118815679">Hersch</persName>
```

**Note (DOCX):** Family name and given names are **not** distinguished -- only `<persName>` without subdivision.

### Organizations

```xml
<orgName ref="GND:1010450-1">Universität Genf</orgName>
```

### Works

```xml
<bibl corresp="GND:1088036961">L'être et la forme</bibl>
```

**Note (DOCX):** `<bibl/>` for bibliographic references.

---

## Special Document Types

### Review

```xml
<div type="review">
  <head>
    <bibl corresp="GND:xxxx">
      Karl Jaspers,
      Philosophie, trad. de Jeanne Hersch
      avec la collaboration d'Irène Kruse et de Jeanne Etoré, Paris,
      Ed. Springer-Verlag, 26, rue des Carmes, 75005 Paris, 1986,
      relié, 17 × 25, 822 p.
    </bibl>
  </head>
  <p>Review text...</p>
</div>
```

### Editorial Introductions / Afterwords

```xml
<ab type="redactional" hand="xy">
  An unsere Leser: Das folgende Interview wurde im Frühjahr 1975 schriftlich geführt.
</ab>
```

**Note (DOCX):** Editorial texts not authored by Jeanne Hersch are tagged with `<ab type="redactional" hand="xy">`.

### Info Boxes and Marginalia

Info boxes, fact boxes, or other marginalia **not authored by Jeanne Hersch** (e.g. "An unsere Leser") are only included if they have a **substantive connection to the main text**. The info box may be appended at the end of the text and marked as third-party text.

### Interview

```xml
<div type="interview">
  <head>Interview mit <persName ref="GND:118815679">Jeanne Hersch</persName> über Freiheit</head>

  <p>Das folgende Interview wurde im Frühjahr 1975 schriftlich geführt. Die Fragen stellte
     <persName ref="GND:123456789">Hans Meier</persName>.
  </p>

  <sp>
    <speaker><persName ref="GND:123456789">Hans Meier</persName>:</speaker>
    <p>Wie würden Sie Freiheit in einem Satz definieren?</p>
  </sp>

  <sp>
    <speaker><persName ref="GND:118815679">Jeanne Hersch</persName>:</speaker>
    <p>Freiheit bedeutet, das zu wollen, was man als richtig erkannt hat.</p>
  </sp>
</div>
```

**Note:** `<sp>` can be further specified via `@type` (e.g. `@type="question"` or `@type="answer"`).

### Panel Discussion

```xml
<div type="conversation">
  <head>Gesprächsrunde zum Thema „Freiheit"</head>

  <sp>
    <speaker><persName ref="GND:118815679">Hans Meier</persName>:</speaker>
    <p>Vielen Dank, dass Sie heute alle gekommen sind.</p>
  </sp>

  <sp>
    <speaker><persName ref="GND:118815679">Anna Müller</persName>:</speaker>
    <p>Gern geschehen.</p>
  </sp>
</div>
```

### Encyclopedia Entry

```xml
<div type="entry">
  <head type="lemma">JASPERS, Karl, 1883–1969</head>

  <p>Einleitender Überblick über Person und Bedeutung ...</p>

  <div n="2">
    <head>Leben</head>
    <p>...</p>
  </div>

  <div n="2">
    <head>Philosophie</head>
    <p>...</p>
  </div>

  <div type="bibliography">
    <head>Literatur</head>
    <listBibl>
      <bibl>...</bibl>
      <bibl>...</bibl>
    </listBibl>
  </div>
</div>
```

**Important:**
- Bibliography is placed in `<div type="bibliography">` with `<listBibl>`
- Entries are tagged with `<bibl>`, but **without GND linking**
- Additional entities (persons, organizations) in bibliographies are **not** annotated

---

## Paratexts

### Front Matter

```xml
<text>
  <front>
    <div type="editorial">
      <head>Vortrag an der Pestalozzifeier 1970 der Sektion Bern</head>
      <p>...</p>
    </div>
  </front>

  <body>
    <div n="1">
      <!-- main text begins here -->
    </div>
  </body>
</text>
```

**Usage:** Forewords, editorial notes, introductory comments, context of origin.

### Back Matter

```xml
<body>
  ...
</body>

<back>
  <div type="translation">
    <head>Übersetzungen</head>
    <p>Eine französische Übersetzung des Textes findet sich auf S. 52–55.</p>
  </div>
  <div type="reprint">
    <p>Nachdruck erschienen in: [bibliografische Angaben]</p>
  </div>
</back>
```

**Possible phrasings:**
- "French translation published in: [...]"
- "Reprint published in: [...]"
- "Also published in: [...]"

---

## Figures

```xml
<figure>
  <graphic xml:id="fig1" url="..\..\images\fig1.tif"/>
  <head>[optional: figure title]</head>
  <p>[optional: explanation of figure in text]</p>
</figure>
```

**Rules:**
- IDs are sequential: fig1, fig2, fig3...
- `<figure>` is tagged **as a standalone block**, not inside `<p>`
- Images are only included if **essential** for understanding the text
- Storage location: `images/` directory

---

## Omissions

The following elements are **not** transcribed:

| Omission | Note |
|----------|------|
| Title pages | Except for monographs |
| Curriculum vitae of Jeanne Hersch | Even if appended before the text |
| Running headers | - |
| Blurb texts | - |
| Authorship notices | "von Jeanne Hersch" only in metadata |
| Initials | Not annotated |
| Multi-column layout | Not reproduced as such |
| Third-party marginal texts | Only if substantively relevant |

**For multi-column layouts:** No paragraph break is inserted at column breaks; the `<p>` generated by Transkribus is deleted.

---

## TEI Element Inventory

| Element | Attributes | Usage |
|---------|------------|-------|
| `<TEI>` | xmlns, type="naegeli" | Root element |
| `<teiHeader>` | - | Metadata (from ALMA via script) |
| `<text>` | - | Text container |
| `<front>` | - | Front paratexts |
| `<body>` | - | Main text |
| `<back>` | - | Back paratexts |
| `<div>` | n, type | Structural division |
| `<pb>` | facs, n | Page break |
| `<lb>` | facs, n, break | Line break |
| `<head>` | type | Heading |
| `<title>` | type (main/sub) | Title |
| `<p>` | facs | Paragraph |
| `<hi>` | rendition | Highlighting |
| `<persName>` | ref | Person with GND |
| `<orgName>` | ref | Organization with GND |
| `<bibl>` | corresp | Work with GND |
| `<note>` | place, n, xml:id, next, prev | Footnote |
| `<foreign>` | xml:lang | Language switch |
| `<space>` | dim | Spacing |
| `<list>` | - | List |
| `<item>` | - | List item |
| `<table>` | - | Table |
| `<row>` | - | Table row |
| `<cell>` | - | Table cell |
| `<figure>` | xml:id | Figure |
| `<graphic>` | xml:id, url | Image reference |
| `<choice>` | - | Correction container |
| `<sic>` | - | Error in original |
| `<corr>` | - | Corrected form |
| `<sp>` | type | Speech act |
| `<speaker>` | - | Speaker name |
| `<listBibl>` | - | Bibliographic list |
| `<ab>` | type, hand | Anonymous block (editorial texts) |

---

## Transkribus Preparation

Text capture is performed in Transkribus:

### OCR
- Model: **Print M1**
- Followed by complete manual correction

### Footnotes in Transkribus (DOCX)
- A **separate text region** is drawn around the footnote
- The footnote is **moved to the end of all text regions**

### Paragraphs in Transkribus (DOCX)
- Larger paragraph breaks are marked with **(vertical)**

### Structural Tags in Transkribus
- `footnote`
- `heading`
- `page-number`
- `caption` (for image captions)

### Renderings in Transkribus
- `bold`
- `italic`
- `strikethrough`
- `underlined`
- `subscript`
- `superscript`

### Textual Tags (under discussion)
- `div`
- `organization`
- `person`
- `sic`
- `speech`
- `unclear`
- `work`

---

## Facsimile Coordinates (optional)

With Gemini 3 Agentic Vision, precise bounding-box coordinates for text regions can be generated. This enables linking between TEI text and digitized image positions.

### Basic Structure

```xml
<TEI>
  <facsimile>
    <surface xml:id="f0001" ulx="0" uly="0" lrx="3683" lry="4224">
      <zone xml:id="p1_col1" ulx="100" uly="200" lrx="1800" lry="4000"/>
      <zone xml:id="p1_col2" ulx="1850" uly="200" lrx="3600" lry="4000"/>
    </surface>
  </facsimile>
  <text>
    <body>
      <div n="1">
        <pb facs="#f0001" n="1"/>
        <p facs="#p1_col1">Text der linken Spalte...</p>
        <p facs="#p1_col2">Text der rechten Spalte...</p>
      </div>
    </body>
  </text>
</TEI>
```

### Attributes

| Element | Attribute | Meaning |
|---------|-----------|---------|
| `<surface>` | ulx, uly, lrx, lry | Full image coordinates (upper-left, lower-right) |
| `<zone>` | ulx, uly, lrx, lry | Text region coordinates |
| `<zone>` | xml:id | Unique ID for linking with `@facs` |

### Coordinate Format

Gemini 3 Agentic Vision returns coordinates in `xywh` format (x, y, width, height). Conversion:

```
ulx = x
uly = y
lrx = x + width
lry = y + height
```

### Benefits

| Aspect | Benefit |
|--------|---------|
| Scholarly | Precise image-text linking |
| IIIF-compatible | Coordinates can be used for IIIF annotations |
| Quality assurance | Visual verification of OCR alignment |

**Note:** Facsimile coordinates are optional and increase effort. Recommended for particularly important documents or two-column layouts.

---

## Open Questions

### From Internal Guidelines (DOCX Comments)

These questions were flagged in the internal document and require clarification with expert Baehler:

1. **Normalization vs. source fidelity:** Should textual features be standardized or preserved from the source? Especially regarding French typographic conventions.

2. **Heading typography:** Same question as for normalizations.

3. **Metadata integration:** Is it possible to pull metadata from Alma and the ID from the spreadsheet? (MMSIDs in Excel spreadsheet)

### Further Open Items

- [ ] Keywords: Who creates them? Do they go in the header? *(DOCX: section empty)*
- [ ] div-type values for front matter: editorial, context, preface, introduction, sourceNote?
- [ ] div-type values for back matter: translation, reprint, publication, bibliography, commentary?
- [ ] GND work records in back matter?
- [ ] Systematic use of textual tags in Transkribus?

---

## Document Metadata

| Source | Last Modified | Author |
|--------|---------------|--------|
| README.md | -- | ZBZ |
| dta_basisformat_komplett.md | -- | DTA |
| Auszeichnungsrichtlinien Hersch INTERN.docx | 2025-06-25 | Marc Zobrist (Revision 74) |

**Contributors (DOCX):** Sharon Rom, Elias Kreyenbuehl, Marc Zobrist

---

## References

- [QUELLENANALYSE](QUELLENANALYSE.md) for corpus and document types
- [GND-STRATEGIE](GND-STRATEGIE.md) for entity linking
- [PIPELINE](PIPELINE.md) for pipeline integration
- [DECISIONS](DECISIONS.md) for open TEI questions

---

*Created: 2026-01-29 | Updated: 2026-02-27*
