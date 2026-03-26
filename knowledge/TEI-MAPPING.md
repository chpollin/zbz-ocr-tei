---
type: knowledge
created: 2026-01-29
updated: 2026-03-26
tags: [zbz-ocr-tei, tei, dta, mapping, transformation]
status: active
---

# TEI Mapping

Transformation rules from source text to TEI-XML following the DTA-Basisformat with project-specific adaptations.

> **Scope:** Since the scope expansion (25.02.2026), zbz-ocr-tei performs the TEI transformation itself (Phase 3 in [PLAN.md](PLAN.md)). This document is the implementation reference for `scripts/tei/tei_generator.py`. The rules apply to the entire pipeline.

**Dependencies:** [QUELLENANALYSE](QUELLENANALYSE.md)

**Sources:**
- `data/richtlinien/Editionsrichtlinien_ZBZ.md` -- **Verbindliche Editionsrichtlinien** (von ZBZ, Stand 2026-03)
- `data/richtlinien/dta_basisformat_komplett.md` -- DTA reference
- `data/schema/zbz_hersch.rng` -- Projektspezifisches RelaxNG-Schema (aus ODD generiert, TEI P5 v4.10.2)

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

> **Entschieden (E49, 2026-03-26):** Verbindliche Regeln aus Editionsrichtlinien ZBZ. Grundsatz: vorlagengetreue Transkription mit definierten Normalisierungen.

### Normalisierungsregeln (verbindlich)

| Quellzeichen | Zielzeichen | Unicode | Regel |
|--------------|-------------|---------|-------|
| Gedankenstriche, Spiegelstriche, von-bis-Striche | Halbgeviertstrich (--) | U+2013 | Alle horizontalen Striche ausser Trenn-/Bindestriche |
| Trennstriche, Bindestriche | Viertelgeviertstrich (‐) | U+2010 | Worttrennungen und Komposita |
| Anführungszeichen (alle Varianten) | "Doppelt" | U+201C / U+201D | Normalisiert zu typografischen Zeichen |
| Einfache Anführungszeichen | 'Einfach' | U+2018 / U+2019 | Normalisiert zu typografischen Zeichen |
| Apostrophe (alle Varianten) | ' | U+2019 | l'homme → l'homme |
| Nicht darstellbare Zeichen | ~ (Tilde) | U+007E | Platzhalter |

### Whitespace-Regeln

| Kontext | Regel |
|---------|-------|
| Vor `:` `;` `?` `!` und Anführungszeichen | Leerzeichen loeschen |
| Aufzaehlungen mit Trennstrichen | Normalisieren zu `/` (Zuerich/Bern/Basel) |

### Beibehaltene Zeichen

| Zeichen | Behandlung |
|---------|-----------|
| ss (scharfes S) | Beibehalten (U+00DF) |
| Klammern | Wie in Vorlage |
| Akzente | Beibehalten |
| Ligaturen | Beibehalten |

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

### Empty Pages

```xml
<pb facs="#facs_9" n="12"/>
<p>[Leer]</p>
```

### Marginalia

```xml
<note place="right">[rechts vom Text stehende Marginalie]</note>
<note place="left">[links vom Text stehende Marginalie]</note>
```

Rechts stehende Marginalien werden unmittelbar **nach** der Zeile transkribiert, links stehende unmittelbar **vor** der Zeile. Falls Marginalien die Funktion von Ueberschriften uebernehmen, werden sie vor dem ersten Paragrafen des entsprechenden Kapitels platziert.

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
| Small caps | `<hi rendition="#k">` | `<hi rendition="#k">Kapitaelchen</hi>` |
| Superscript | `<hi rendition="#sup">` | `<hi rendition="#sup">1</hi>` |
| Subscript | `<hi rendition="#sub">` | `<hi rendition="#sub">2</hi>` |

**Important:** Only **semantically relevant** highlighting is encoded, not purely typographic features (e.g. formatting used solely for headings).

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

**Regel (Editionsrichtlinien):** Fehlerhafte Schreibweisen und offensichtliche Druckfehler werden mit `<choice>/<sic>/<corr>` korrigiert.

---

## Unleserliche Buchstaben und Passagen

```xml
<unclear>unleserliches Wort</unclear>
<unclear cert="high">wahrscheinlich richtig</unclear>
<unclear cert="low">sehr unsicher</unclear>
```

Schwer leserliche Zeichen oder Zeichenketten (z.B. durch physische Maengel der Vorlage, schwachen Druck) werden mit `<unclear>` umschlossen. Optional: `@cert` fuer Sicherheit der Lesung.

---

## Index Entries (Entities)

### General Rule

**Every mention is referenced**, even on repetition. Referenzierung folgt der Dual-Attribut-Strategie (E49):

- `ref="GND:{id}"` -- GND-ID als primaere Referenz (wie Editionsrichtlinien), nur wenn GND vorhanden
- `corresp="#zbz-p.N"` -- Interne ID als Platzhalter (immer vorhanden, verweist auf Entity Index)

**Exceptions:**
- Entities in image captions (`<figure>/<p>`) are **not** annotated
- Entities in `<div type="bibliography">/<listBibl>` (Lexikonartikel) are **not** annotated
- Adjektivierte Personennamen (z.B. "kantien", "hegelsche") are **not** annotated
- Avoid "nested" tagging where possible

### Persons

```xml
<persName ref="GND:118815679" corresp="#zbz-p.1">Hersch</persName>
```

Family name and given names are **not** distinguished -- only `<persName>` without subdivision.

### Organizations

```xml
<orgName ref="GND:1010450-1" corresp="#zbz-o.5">Universität Genf</orgName>
```

### Works

```xml
<bibl corresp="#zbz-w.3" ref="GND:1088036961">L'être et la forme</bibl>
```

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

**Usage:** Vorworte, redaktionelle Hinweise, einleitende Kommentare, Entstehungskontext. Unabhaengig von Platzierung im Originaltext.

### Widmungen

Widmungen stehen in `<front>`:

```xml
<front>
  <div type="dedication">
    <p>[Widmungstext]</p>
  </div>
</front>
```

### Back Matter

Angaben zu Uebersetzungen, Nachdrucken und weiteren Erscheinungsformen. Zulaessige `@type`-Werte: `translation`, `reprint`, `otherEdition`.

```xml
<back>
  <div type="translation">
    <head>Uebersetzung(en)</head>
    <p>MLA 9: Nachname, Vorname, translator. "Titel." Publikation, vol. X, no. Y, 1934, pp. 52-55.
       <ref target="https://swisscovery.slsp.ch/permalink/...">Link auf Swisscovery.</ref>
    </p>
  </div>

  <div type="reprint">
    <head>Nachdruck(e)</head>
    <p>MLA 9: Nachname, Vorname. "Titel." Sammelband, edited by Vorname Nachname, Verlag, 1978, pp. 101-118.
       <ref target="https://swisscovery.slsp.ch/permalink/...">Link auf Swisscovery.</ref>
    </p>
  </div>

  <div type="otherEdition">
    <p>MLA 9: Nachname, Vorname. "Titel." Zeitschrift, vol. X, no. Y, 1952, pp. 9-12.
       <ref target="https://swisscovery.slsp.ch/permalink/...">Link auf Swisscovery.</ref>
    </p>
  </div>
</back>
```

**Regeln:**
- Zitierung nach MLA, 9. Ausgabe
- Verlinkung ueber Swisscovery-Permalink als `<ref target="...">`
- Chronologisch nach Erscheinungsjahr aufsteigend
- Bei Uebersetzungen nur die erste Auflage
- Einfacher Fall (nur ein Hinweis): direkt als `<p>` in `<back>` ohne `<div>`

---

## Figures

```xml
<figure xml:id="fig1">
  <graphic url="..\..\images\fig1.tif"/>
  <head>[optional: Titel der Abbildung]</head>
  <p>[optional: Erlaeuterung zur Abbildung]</p>
</figure>
```

**Rules:**
- `xml:id` auf `<figure>` (nicht auf `<graphic>`), fortlaufend: fig1, fig2, fig3...
- `<figure>` ist **immer ein eigenstaendiger Block**, nicht innerhalb von `<p>`
- Bilder werden nur aufgenommen wenn fuer Textverstaendnis erforderlich
- Entitaeten in Bildunterschriften werden **nicht** ausgezeichnet

### Doppelseitige Abbildungen

Abbildungen ueber zwei Seiten werden mit `<anchor>` markiert:

```xml
<pb facs="#facs_6" n="7.22"/>
<anchor xml:id="fig8-start"/>
<figure xml:id="fig8">
  <graphic url="..\..\images\fig8.tif"/>
  <p>Bildunterschrift...</p>
</figure>
<pb facs="#facs_7" n="7.23"/>
<anchor xml:id="fig8-end"/>
```

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
| `<persName>` | ref, corresp | Person (ref=GND, corresp=interne ID) |
| `<orgName>` | ref, corresp | Organisation (ref=GND, corresp=interne ID) |
| `<placeName>` | ref, corresp | Ort (ref=GND, corresp=interne ID) |
| `<bibl>` | ref, corresp | Werk (ref=GND, corresp=interne ID) |
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
| `<unclear>` | cert | Unleserliche Passage (cert=high/low) |
| `<anchor>` | xml:id | Markierung fuer Doppelseiten-Bilder |
| `<ref>` | target | Verweis (z.B. Swisscovery-Permalink) |

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

### Geloest (durch Editionsrichtlinien 2026-03)

- [x] ~~Normalization vs. source fidelity~~ → Beantwortet: vorlagengetreu mit definierten Normalisierungen (siehe §Character Normalization)
- [x] ~~div-type values for front matter~~ → Beantwortet: editorial, dedication
- [x] ~~div-type values for back matter~~ → Beantwortet: translation, reprint, otherEdition
- [x] ~~Heading typography~~ → Beantwortet: typografische Besonderheiten werden nicht abgebildet
- [x] ~~Entity-Ref-Format~~ → Beantwortet: GND direkt + interne IDs in corresp

### Noch offen

- [ ] Keywords/Schlagworte: Wer erstellt diese? Kommen sie in den Header? *(Richtlinien: "in Abklaerung")*
- [ ] Metadata from ALMA/MMSID: MMSIDs fuer teiHeader (O8)
- [ ] Systematischer Einsatz von textual tags in Transkribus

---

## Document Metadata

| Source | Last Modified | Author |
|--------|---------------|--------|
| README.md | -- | ZBZ |
| dta_basisformat_komplett.md | -- | DTA |
| Auszeichnungsrichtlinien Hersch INTERN.docx | 2025-06-25 | Marc Zobrist (Revision 74) |

**Contributors (DOCX):** Sharon Rom, Elias Kreyenbuehl, Marc Zobrist

---

## revisionDesc (Quality Screening Status)

Jedes finale TEI in `output/tei_final/` enthaelt eine `<revisionDesc>` im teiHeader:

```xml
<revisionDesc>
  <change when="2026-03-15" who="pipeline">
    TEI generated (Unified Pipeline v1, Gemini + RelaxNG)
  </change>
  <change when="2026-03-15" who="agent-screening-v2" status="APPROVED_WITH_NOTES">
    Agent-Based Quality Screening (L1:ok L2:ok ... L7:ok). Findings...
  </change>
</revisionDesc>
```

**Attribute:**
- `when`: Datum der Aenderung
- `who`: `pipeline` | `quality-pass-auto` | `agent-screening-v2`
- `status`: `APPROVED` | `APPROVED_WITH_NOTES` | `NEEDS_REVIEW` | `NEEDS_REWORK`

**Konvention:** `<revisionDesc>` steht direkt vor `</teiHeader>`. Der juengste `<change>`-Eintrag bestimmt den aktuellen Status. Die Edition zeigt den Status als Badge an.

Script: `python -m scripts.tei.tei_add_revision --all`

---

## References

- [QUELLENANALYSE](QUELLENANALYSE.md) for corpus and document types
- [GND-STRATEGIE](GND-STRATEGIE.md) for entity linking
- [PIPELINE](PIPELINE.md) for pipeline integration
- [DECISIONS](DECISIONS.md) for open TEI questions

---

*Created: 2026-01-29 | Updated: 2026-03-26*
