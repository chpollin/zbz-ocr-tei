"""
TEI Mapping Table Prompt: Systematische Transformationsregeln fuer Gemini.

Erzeugt den Mapping-Table-Prompt fuer Step 2 (Gemini Refinement) der
Unified TEI Pipeline. Kein Few-Shot-Prompting -- stattdessen eine
vollstaendige Tabelle aller Phaenomen-zu-TEI-Zuordnungen.

Quellen: data/source/guidelines/Editionsrichtlinien_ZBZ.md (verbindlich)
         + knowledge/pipeline.md, Abschnitt "TEI-Mapping" (DTA-Basisformat + ZBZ-Anpassungen)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


# ---------------------------------------------------------------------------
# Mapping Table (7 Sections)
# ---------------------------------------------------------------------------

MAPPING_TABLE = r"""
=== TEI TRANSFORMATION MAPPING TABLE ===
(DTA-Basisformat + ZBZ Jeanne Hersch Edition)

You MUST follow these rules EXACTLY. Each row defines how a phenomenon
maps to a TEI element with specific attributes.

SCOPE OF THIS STEP (important): You refine ONE page at a time and return a single
<div> body fragment (see OUTPUT FORMAT at the end). Therefore document-level and
cross-page structures are NOT your job and are added later during human curation:
  - <front>/<back> (dedications, editorial intros, translation/reprint notices)
    -> built at document assembly from the Masterfile, not per page
  - cross-page <anchor> for double-page figures -> needs both pages, set in curation
  - <unclear> -> requires per-character judgement against the image, set in curation
The rows describing these below document the TARGET edition format for reference;
do NOT emit <front>, <back>, cross-page <anchor> or <unclear> in your per-page output.

--- SECTION 1: DOCUMENT STRUCTURE ---

| Phenomenon | TEI Element | Attributes | Rules |
|---|---|---|---|
| Main section | <div> | n="1" | One per document. Contains all body content. |
| Sub-section (chapter) | <div> | n="2" | Inside div n="1". New heading = new div n="2". |
| Sub-sub-section | <div> | n="3" | Inside div n="2". Rare. |
| Review document | <div> | type="review" | Replaces div n="1" when genre=review. Heading contains <bibl>. |
| Interview document | <div> | type="interview" | Contains <sp> elements for speaker turns. |
| Panel discussion | <div> | type="conversation" | Like interview but multiple speakers. |
| Encyclopedia entry | <div> | type="entry" | Heading has type="lemma". Sub-sections as div n="2". |
| Bibliography section | <div> | type="bibliography" | Contains <listBibl> with <bibl> entries. |
| Editorial text | <ab> | type="redactional" hand="xy" | Text NOT by Jeanne Hersch. |
| Page break | <pb/> | facs="#facs_{P}" n="{printed_num}" | INSIDE <div>, at start of page content. n="[N]" if number not printed. |
| Paragraph | <p> | facs="#facs_{P}_r_{N}" | Standard text block. Keep existing facs references. |
| Heading | <head> | (none) | Contains text. May contain <title>. |
| Document title | <title> | type="main" | Inside <head>. For the document's main title. |
| Subtitle | <title> | type="sub" | Inside <head>, after main title. |
| Epigraph/motto | <epigraph> | (none) | Quoted block before main content (e.g. motto in interviews). Contains <p>. |
| Footnote | <note> | place="foot" n="{num}" xml:id="fn{page}-{N}" | At text location of marker. Content = footnote text. |
| Multi-page footnote start | <note> | + next="#fn{page+1}-{N}a" | Note continues on next page. Close before <pb/>. |
| Multi-page footnote cont | <note> | xml:id="fn{page}-{N}a" prev="#fn{page-1}-{N}" | Continuation. No n= attribute. |
| Figure/illustration | <figure> | (xml:id="fig{N}") | Standalone block. NOT inside <p>. |
| Figure caption | <head> | (none) | Inside <figure>. |
| List | <list> | (none) | Contains <item> elements. |
| List item | <item> | (none) | Inside <list>. Numbering in text, not attribute. |
| Table | <table> | (none) | Contains <row>/<cell>. |
| Vertical space | <space/> | dim="vertical" | Larger gap between paragraphs. |
| Front matter | <front> | (none) | Editorial notes, dedications, context. Inside <text>, before <body>. |
| Front dedication | <div> | type="dedication" | Inside <front>. Dedication text in <p>. |
| Back matter | <back> | (none) | Translations, reprints. Inside <text>, after <body>. |
| Translation notice | <div> | type="translation" | Inside <back>. MLA citation + Swisscovery link as <ref target="...">. |
| Reprint notice | <div> | type="reprint" | Inside <back>. MLA citation + Swisscovery link. |
| Other edition notice | <div> | type="otherEdition" | Inside <back>. MLA citation + Swisscovery link. |
| Empty page | <p> | (none) | Content is literally "[Leer]". After <pb/> of the empty page. |
| Marginalia right | <note> | place="right" | Right margin note. After the line it appears next to. |
| Marginalia left | <note> | place="left" | Left margin note. Before the line it appears next to. |

--- SECTION 2: LINE-LEVEL MARKUP ---

| Phenomenon | TEI Element | Attributes | Rules |
|---|---|---|---|
| Line break | <lb/> | facs="..." n="N001" | Every visible line break. Counter resets to N001 within each <p>, <head>, <note>. |
| Hyphenated line break | <lb/> | break="no" | Word split across lines. REMOVE the hyphen character. |
| Cross-page hyphenation | (none) | | Do NOT use break="no" across page breaks. Keep hyphen as-is. |

IMPORTANT: Verify line break positions against the scanned image. The scaffold
may have approximate line breaks from OCR -- correct them based on what you
see in the image.

--- SECTION 3: INLINE FORMATTING ---

| Phenomenon | TEI Element | Attributes | Rules |
|---|---|---|---|
| Bold text | <hi> | rendition="#b" | Verify from image. |
| Italic text | <hi> | rendition="#i" | Verify from image. Often = emphasis, foreign title, or work title. |
| Underlined text | <hi> | rendition="#u" | Rare. Verify from image. |
| Letter-spaced text | <hi> | rendition="#g" | German emphasis convention (gesperrt). |
| Small caps | <hi> | rendition="#k" | Kapitaelchen. |
| Superscript | <hi> | rendition="#sup" | Footnote markers, ordinals. |
| Subscript | <hi> | rendition="#sub" | Chemical formulas. Rare. |

IMPORTANT: Only encode SEMANTICALLY RELEVANT highlighting, not purely
typographic features used solely for heading decoration.

--- SECTION 4: LANGUAGE SWITCHES ---

| Phenomenon | TEI Element | Attributes | Rules |
|---|---|---|---|
| Text in different language | <foreign> | xml:lang="{code}" | Mark passages NOT in the document's main language. |

Language codes (ISO 639-3): fra=French, deu=German, eng=English, ita=Italian, lat=Latin.

Only tag SUBSTANTIAL language switches (phrases, sentences), not individual
foreign words that are commonly used (e.g. "a priori" in French text).

--- SECTION 5: CORRECTIONS & UNCLEAR ---

| Phenomenon | TEI Element | Attributes | Rules |
|---|---|---|---|
| Non-obvious print error | <choice> | (none) | Contains <sic> + <corr>. |
| Error in original | <sic> | (none) | Inside <choice>. The incorrect text. |
| Corrected form | <corr> | (none) | Inside <choice>. The correct text. |
| Unclear reading | <unclear> | cert="high" or "low" | Text hard to read due to physical damage or faint print. |

NOTE: Obvious errors are silently corrected in the OCR text.
Use <choice>/<sic>/<corr> ONLY for non-obvious errors where both readings
should be preserved (e.g. missing accent: Eclairement vs Eclairement).
Use <unclear> when characters are hard to read (damaged, faint). Optional @cert for confidence.

--- SECTION 6: SPEECH ACTS (interviews, debates) ---

| Phenomenon | TEI Element | Attributes | Rules |
|---|---|---|---|
| Speaker turn | <sp> | (none) | Contains <speaker> + one or more <p>. |
| Speaker name | <speaker> | (none) | Contains the speaker's name. |

How to detect speakers: Bold or CAPS text followed by colon, or a clear
question-answer pattern. Each speaker turn = one <sp> block.

--- SECTION 7: OMISSIONS ---

Do NOT include these in the TEI output:

| Omit | Reason |
|---|---|
| Title pages | Metadata only (except monographs) |
| Running headers/footers | Layout artifacts (_filter regions) |
| Blurb texts | Not content |
| CV of Jeanne Hersch | Metadata only |
| Authorship notices | "von Jeanne Hersch" = metadata only |
| Decorative elements | Not content |
| JSTOR cover pages | Metadata only |
""".strip()


# ---------------------------------------------------------------------------
# Genre-Conditional Rules
# ---------------------------------------------------------------------------

GENRE_RULES = {
    "review": """
GENRE-SPECIFIC RULES (Review):
- Outer div: type="review" (NOT n="1")
- <head> contains <bibl> with full bibliographic entry
  (author, title in <hi rendition="#i">, publisher, date, pages)
- Review body follows as <p> elements
""",

    "interview": """
GENRE-SPECIFIC RULES (Interview):
- Outer div wraps content: type="interview"
- Introductory text or epigraph before Q&A may use <epigraph> or <p>
- Each speaker turn: <sp><speaker>Name:</speaker><p>...</p></sp>
- <sp> can be further specified: type="question" or type="answer"
- Speaker identification: bold/CAPS name before colon, or clear Q&A pattern
- A single <sp> can span a page break (<pb/> inside the <p> of an <sp>)
""",

    "debate": """
GENRE-SPECIFIC RULES (Panel Discussion / Debate):
- Outer div: type="conversation"
- Multiple speakers, each turn as <sp><speaker>...</speaker><p>...</p></sp>
- Moderator turns may have type="moderation" on <sp>
""",

    "encyclopedia": """
GENRE-SPECIFIC RULES (Encyclopedia Entry):
- Outer div: type="entry"
- <head type="lemma"> for the entry heading (e.g. "JASPERS, Karl, 1883-1969")
- Sub-sections as div n="2" with <head> (Leben, Philosophie, etc.)
- Bibliography in <div type="bibliography"><listBibl><bibl>...</bibl></listBibl></div>
""",

    "speech": """
GENRE-SPECIFIC RULES (Speech / Lecture):
- Standard div n="1" structure
- May have introductory context (<epigraph> or editorial <ab>)
- Often has no sub-sections -- continuous prose
""",

    "conference": """
GENRE-SPECIFIC RULES (Conference Contribution):
- Standard div n="1" structure
- May reference other speakers or panel context
- Footnotes common for academic references
""",

    "preface": """
GENRE-SPECIFIC RULES (Preface / Foreword):
- Consider using <front> if this is an editorial introduction
- If by Jeanne Hersch: standard div n="1"
- If by someone else: <ab type="redactional" hand="xy">
""",

    "letter": """
GENRE-SPECIFIC RULES (Letter):
- Standard div n="1" structure
- May have date/place header
- Salutation and closing as separate <p> elements
""",

    "newspaper": """
GENRE-SPECIFIC RULES (Newspaper Article):
- Standard div n="1" structure
- May have editorial framing text: <ab type="redactional">
- Running headers are filtered (_filter)
""",

    "editorial": """
GENRE-SPECIFIC RULES (Editorial):
- Standard div n="1" structure
- If not by Jeanne Hersch: use <ab type="redactional" hand="xy">
""",
}


# ---------------------------------------------------------------------------
# Prompt Builder
# ---------------------------------------------------------------------------

def build_mapping_prompt(doc_context: dict) -> str:
    """Baut den vollstaendigen Mapping-Table-Prompt fuer Gemini Refinement.

    Args:
        doc_context: {
            "doc_id": str,
            "page_num": int,
            "total_pages": int,
            "genre": str | None,
            "pub_form": str,
            "main_lang": str,        # ISO 639-3
            "layout_type": str,      # A/B/C/D
            "title": str,
            "author": str,
            "date": str,
            "doc_hints": str,        # from build_doc_hints()
        }

    Returns:
        Complete prompt string for Gemini refinement.
    """
    genre = doc_context.get("genre")
    main_lang = doc_context.get("main_lang", "und")
    doc_hints = doc_context.get("doc_hints", "")

    # Genre-spezifische Regeln
    genre_block = ""
    if genre and genre in GENRE_RULES:
        genre_block = "\n" + GENRE_RULES[genre]

    prompt = f"""You are a TEI-XML refiner for the Jeanne Hersch Edition (ZBZ Zurich).
You follow the DTA-Basisformat with project-specific adaptations.

You receive a RULE-BASED TEI scaffold that needs semantic enrichment.
Compare it against the scanned page image and the original OCR text.

TASK: Refine the TEI scaffold by applying the mapping table below.
- PRESERVE all text content exactly as in the scaffold
- Do NOT invent or add text that is not in the OCR
- Only modify XML markup (add/change/remove elements and attributes)
- Output must be well-formed XML

{MAPPING_TABLE}
{genre_block}

DOCUMENT CONTEXT:
- Document {doc_context.get("doc_id", "?")}, Page {doc_context.get("page_num", "?")} of {doc_context.get("total_pages", "?")}
- Title: {doc_context.get("title", "unknown")}
- Author: {doc_context.get("author", "unknown")}
- Date: {doc_context.get("date", "unknown")}
- Main language: {main_lang}
- Layout type: {doc_context.get("layout_type", "A")}
- Publication form: {doc_context.get("pub_form", "other")}
- Genre: {genre or "standard article"}
{doc_hints}

REFINEMENT PRIORITIES (in this order):
1. VERIFY and correct <lb/> positions against the scanned image
2. ADD break="no" where words are hyphenated across lines (remove the hyphen)
3. DETECT language switches: <foreign xml:lang="..."> for non-{main_lang} passages
4. VERIFY <hi> formatting against the image (italic, bold)
5. CORRECT div hierarchy and types if the scaffold got them wrong
6. ADD <choice><sic>...<corr>...</choice> for non-obvious print errors
7. For interviews/debates: EVERY speaker turn MUST be wrapped in <sp><speaker>. Tag ALL turns, not just the first few
8. For reviews: wrap bibliographic heading in <bibl> inside <head>

OUTPUT FORMAT:
- Return ONLY the refined TEI body fragment
- No <?xml?> declaration, no <TEI> root, no <teiHeader>, no <facsimile>
- Must be well-formed XML
- Start with <div ...> and end with </div>"""

    return prompt


def build_refinement_input(scaffold_xml: str, ocr_text: str) -> str:
    """Baut den Input-Block fuer den Gemini-Call (Scaffold + OCR).

    Args:
        scaffold_xml: TEI-XML Fragment aus Step 1
        ocr_text: Originaler OCR-Markdown-Text

    Returns:
        Formatierter Input-String fuer den Prompt.
    """
    return f"""
RULE-BASED TEI SCAFFOLD (to refine):
```xml
{scaffold_xml}
```

ORIGINAL OCR TEXT (markdown):
```
{ocr_text}
```"""
