"""Deterministic entity candidate search on delivered TEI-XML (analysis only).

Design plan and rule catalogue: knowledge/entity-integration.md (sections "Target
model" and "Matching method"). This module has no write path and never calls a
language model; ids always come from the curated list.

Two public functions:

    build_lexicon(entities_path, cache_path, legacy_path=None, review_path=None) -> dict
        Re-exported from scripts.tei.entity_lexicon, which builds the lexicon out of
        curated list, GND cache, legacy mention index and variant review, and
        documents the form channels behind it.

    find_candidates(xml_string, lexicon) -> list[dict]
        Reports mentions as raw character spans of the input string. Every candidate
        carries gid, category, surface, start, end, tier, rule, alternatives,
        matched_form, form_source, context; one-word work titles additionally carry
        evidence. Hard invariants: xml_string[start:end] == surface, candidates sorted
        by start and free of overlap, spans only inside <text>, and the surface carries
        no markup other than <lb/> tags. Running-head zones (the recurring page-head
        line, detected by scripts.tei.running_heads) demote their candidates to tier 2
        with the ":running-head" suffix, so page furniture never auto-marks (E105); a
        demoted full name keeps its anchor power, because the head still names the
        document's subject. Figure zones work the same way with the ":in-figure"
        suffix: a plate catalogue keeps its whole provenance apparatus in the captions,
        so the zone is scanned instead of excluded, and the machine asserts nothing
        inside it. The document's own author is matched like every other listed entity
        (operator decision E108); there is no byline exception.

        alternatives   every listed id the matched form or surname belongs to, sorted
                       and including the reported gid. Empty for an unambiguous
                       candidate, so a filled list always means "undecided" and never
                       lets a single bearer read as the found entity. Length is never
                       one.
        matched_form   the lexicon form that produced the hit. For a surname hit that
                       is the form which registered the surname ("Mayer, Gertrud"
                       behind a hit on "Mayer"), not the surname itself.
        form_source    which channel the form came from: "headword" (curated label and
                       everything derived from it), "curated-variant" (the operator's
                       `variants` field of the curated list), "cache-variant" (GND
                       cache), "legacy" (legacy mention index), "surname-index" (the
                       bare surname of a curated headword).
        evidence       one-word work titles only: "typographic" when the setting
                       corroborates the title reading, "none" otherwise (see below).

Search model. The scan runs on a normalized projection of the raw string: markup
contributes nothing, `<lb break="no"/>` joins a broken word, a plain `<lb/>` counts
as one space, whitespace collapses to a single space, and character references are
decoded. Every normalized character keeps the raw offsets it came from, so a match
maps back to an exact byte span whose slice is the surface. Excluded zones emit a
sentinel character instead of their text, which blocks any match from running across
them. The apparatus zone (E-Periodica cover sheet, photo credit lines) is excluded
as well, so library apparatus never carries entity markup. A `<figure>` is no excluded
zone; its caption text takes part in the scan and reaches the worklist through the
":in-figure" demotion. A superscript digit counts as a separator rather than a word
character, so a name that carries a footnote marker ("Nietzsche" with a superscript
two) keeps the boundary it has in front of a comma.

Deliberate simplifications (upgrade path in the milestones M3 to M5):

- A match that crosses non-lb markup is reported truncated to its first text part
  with rule "crosses-markup" and tier 2, instead of being dropped; the worklist keeps
  the position that way. Truncation to an empty part drops the candidate.
- A form that several entities share becomes tier 2 with the rule suffix
  ":ambiguous"; the reported gid is the lexicographically first one and every bearer
  stands in `alternatives`, so the judge stage sees the whole set and no report can
  present one bearer as the decision. The two rules that an anchor decides keep their
  reported id without the suffix and list the bearers all the same: "anchored-surname"
  (exactly one bearer mentioned in full in the document) and "ambiguous-surname"
  (several of them, which the rule name already says).
- Suffix order is fixed and stackable: base rule, then the derived-channel suffix (a
  property of the lexicon form), then ":ambiguous" (a property of the lexicon), then
  ":suspect" (a property of the context), then ":in-plain-bibl" and ":in-figure" (both
  properties of the position), then ":running-head" (a property of the page position,
  appended last).
- Five derived-form channels close gaps of the facsimile-adjudicated evaluation. They
  are worklist-only by construction and catalogued in scripts.tei.entity_lexicon; the
  scan reads them as a lexicon rule that carries a suffix.
- The adjudicated precision guards (E109) demote a tier-1 hit to the worklist on the
  deterministic signals of the confirmed error classes of the 2026-08-12 evaluation:
  a hyphen directly at the span border (compound, "UNESCO-Kommission"), a citation
  title-slot frame (after "Salamun K.,", before ", éd."), an eponymous institution
  word in front of a full name ("Fondation Karl Jaspers"), an undated parenthetical
  behind a surname ("Augustin (de Malègue)"), and the lowercased incipit of a
  case-tolerant work title ("die Mauer"). An internal particle bridges a person form
  to its own surname instead ("Saint Ignace de Loyola" as one span). Every signal is
  grown from adjudicated cases only, never by guessing.
- The speaker rule compares the slot text verbatim (after stripping surrounding
  punctuation). Honorific prefixes ("Mlle Hersch") therefore fall through to the
  general surname rules; whether ZBZ wants the honorific inside the element is an
  open modelling point.
- Every one-word work title candidate carries the typographic pre-sorting `evidence`:
  "typographic" when the span sits completely inside an `hi`, when quotation marks or
  guillemets enclose it directly, or when a possessive stands right in front of it
  (POSSESSIVES), else "none". Both stay tier 2 and no class is dropped; the field is
  the measurement basis for that decision. The minimum length such a title needs to
  enter the lexicon at all is a lexicon rule (scripts.tei.entity_lexicon).
- A bare or anchored surname drops to tier 2 with the rule suffix ":suspect" on any
  homograph signal: a lowercase twin of the word in the same document, membership in
  FUNCTION_WORDS, an adjacent hyphen, or an adjacent unknown capitalized word. The
  last signal is noisy in German, where every noun is capitalized; it is suppressed
  behind a genitive surface ("Herschs Werk"), before a sentence-initial word and
  behind an honorific ("Mlle Hersch", HONORIFICS). Beyond that it is suppressed only
  when the word pair itself is a listed form. A neighbour that merely starts some
  listed form corroborates nothing, because every listed forename would then clear the
  homograph next to it ("Hans Mayer", where the surname comes from the GND variant
  "Mayer, Gertrud" of another person, kept its tier while "Hans" stood in the lexicon).
  Full-name rules (full-name, variant-full-name, initial-surname) ignore the signals.
- Adjective derivations ("Freudschen", "freudien") are reported over their stem with
  the rule "adjective-form" and tier 2, span covering the whole inflected word. The
  guideline excludes them and the references mark at least one, so the contradiction
  goes to ZBZ over the worklist instead of being decided by a silent drop.
- A single-word work title that shadows a listed surname ("Nietzsche") is reported
  with the AMBIGUOUS suffix, so the judge stage resolves both readings from the
  lexicon; the surname fallback stays reachable through `lexicon["surnames"]`.
- All-caps full names of persons match through "caps-full-name" (tier 1), single
  all-caps surnames through "caps-surname" (tier 2). Forms whose uppercase changes
  length (the German sharp s) carry no caps form, because the offset mapping assumes
  equal length.
- A form of at least two tokens also matches when only letter case differs; the corpus
  sets "La Foi philosophique" where the GND cache carries "La foi philosophique". Such
  a hit keeps the rule, the tier and the matched_form of the exact hit of that form, so
  it needs no rule id of its own; a case difference between matched_form and surface is
  what identifies it. Everything else stays exact, diacritics, punctuation and
  whitespace alike. One-token forms are excluded, because there the collision with
  ordinary vocabulary is the known failure mode ("Philosophie" as a title). Two limits
  keep that failure mode from returning at phrase level:
    * a capitalized form written all in lower case drops to tier 2 with the ":suspect"
      suffix, because "le capital" and "les grands philosophes" are ordinary prose far
      more often than they are the listed titles;
    * all-caps person surfaces stay with the caps channel and its own rule id, so a
      caps mention is recognizable in every downstream report.
"""

from __future__ import annotations

import html
import re
from bisect import bisect_left, bisect_right
from collections.abc import Iterator
from dataclasses import dataclass, replace

# The lexicon side lives in entity_lexicon; the names it owns stay importable from
# here, which is the import surface of the pipeline scripts and the test suite.
# The `X as X` form marks the names only re-exported, unused inside this module.
from scripts.tei.entity_lexicon import (
    _WORD_RUN_RE,
    FORM_SOURCES as FORM_SOURCES,
    MIN_TOKEN_LEN as MIN_TOKEN_LEN,
    PLACE_ADJECTIVES as PLACE_ADJECTIVES,
    TIER_BY_RULE,
    _collapse as _collapse,
    _form_tier,
    _is_initials_only as _is_initials_only,
    _is_word,
    _is_word_at,
    _word_end,
    build_lexicon as build_lexicon,
    legacy_form_is_covered as legacy_form_is_covered,
    legacy_names as legacy_names,
    normalize_gid as normalize_gid,
)
from scripts.tei.running_heads import head_spans

SENTINEL = "\x00"
CONTEXT_RADIUS = 40

PLAIN_BIBL_SUFFIX = ":in-plain-bibl"
AMBIGUOUS_SUFFIX = ":ambiguous"
SUSPECT_SUFFIX = ":suspect"
IN_FIGURE_SUFFIX = ":in-figure"
RUNNING_HEAD_SUFFIX = ":running-head"

# Tier-1 person rules the citation-frame, container and particle logic applies to.
_PERSON_FULL_RULES = frozenset({
    "full-name", "variant-full-name", "caps-full-name", "initial-surname",
})

# Eponymous-institution words directly in front of a full name ("Fondation Karl
# Jaspers", doc 1830): the name denotes the institution. Attested member plus its
# direct paradigm; grown from adjudicated cases only, never by guessing.
ORG_CONTAINERS = frozenset({"Fondation", "Stiftung", "Foundation", "Fondazione"})

# Citation frames of the adjudicated bibliography errors (E109): a full name in the
# title slot of a citation follows the author-initial pattern ("Salamun K., Karl
# Jaspers, Munich, 1985") or precedes an editor abbreviation ("Karl Jaspers, éd.
# P.A. Schilpp"). Both demote to the worklist; author-position names in citations
# ("Monique Saint-Hélier, Annalen, 1944") match neither frame and keep their tier.
_AUTHOR_SLOT_RE = re.compile(r"[A-ZÀ-Þ]\S* [A-ZÀ-Þ]\.(?: ?[A-ZÀ-Þ]\.)*, $")
_EDITOR_AFTER_RE = re.compile(r", (?:éd|ed|hrsg|Hrsg|Hg)\.")

# Internal name particle bridging a person form to its own surname ("Saint Ignace
# de Loyola", doc 2330). Attested particle plus its direct paradigm.
_PARTICLE_RE = re.compile(r" (?:de|von|van) (\w+)")

# A bare parenthetical directly after a surname ("Augustin (de Malègue)", doc 110)
# reads as a work or qualifier; a dated one ("Jaspers (1883-1969)") corroborates
# the person and keeps its tier.
_PAREN_AFTER_RE = re.compile(r" ?\(([^)]{0,60})\)")

_WORD_BEFORE_RE = re.compile(r"(\S+) $")

EVIDENCE_TYPOGRAPHIC = "typographic"
EVIDENCE_NONE = "none"

# Typographic evidence of a one-word work title: quotation marks of every shape the
# corpus carries, and the possessives that mark a following noun as a titled work.
QUOTE_CHARS = frozenset("\"'«»‹›‚“”„‘’")  # noqa: RUF001
POSSESSIVES = frozenset({
    "sa", "son", "ses", "seine", "seiner", "his", "her", "sua", "suo",
})

# Surnames that are also ordinary German words. Only collisions attested in the
# corpus belong here ("weil" the conjunction, "Wahl" the election); the list grows
# with the corpus scan, never by guessing.
FUNCTION_WORDS = frozenset({"weil", "wahl"})

# Honorifics and functions in front of a name. They corroborate the name reading, so
# they are no doubt signal; without them the corpus scan drowns the real forename
# collisions in "Frau Hersch" and "Mlle Hersch". Members are attested in the corpus,
# plus the direct paradigm of an attested one.
HONORIFICS = frozenset({
    "dr", "frau", "fräulein", "herr", "herrn", "madame", "mademoiselle", "miss",
    "mister", "mlle", "mme", "monsieur", "mr", "mrs", "nationalrat", "pfarrer",
    "prof", "professor", "signor", "signora", "signorina", "sir",
})

# Only these two rules carry the homograph check; full names are distinctive enough.
_SUSPECT_RULES = frozenset({"bare-surname", "anchored-surname"})

# A word behind one of these is capitalized by position, which is no name signal.
_SENTENCE_END = frozenset(".!?:;" + SENTINEL)

# E-Periodica cover sheet: the field lines of the first page, and the photo credit
# lines that follow the same apparatus logic.
COVER_FIELDS = ("Zeitschrift:", "Herausgeber:", "Band:", "Heft:")
COVER_FIELD_MIN = 3
CREDIT_PREFIXES = ("Porträts:", "Fotos:")

# Adjective derivations of a name (Freudschen, freudien, nietzschiano); longest
# first, so the longer ending wins over its own prefix.
_ADJECTIVE_SUFFIXES = (
    "iennes", "ienne", "schem", "schen", "scher", "sches",
    "iens", "iano", "iana", "iani", "iane", "sche", "ien", "ian",
)

_TOKEN_RE = re.compile(r"<!--.*?-->|<\?.*?\?>|<![^>]*>|</?[A-Za-z][^>]*>", re.DOTALL)
_PB_RE = re.compile(r"<pb\b[^>]*/?>", re.DOTALL)
_TAG_RE = re.compile(r"<[^>]*>")
_NAME_RE = re.compile(r"^</?([A-Za-z][\w.:-]*)")
_ATTR_RE = re.compile(r"([\w.:-]+)\s*=\s*(\"([^\"]*)\"|'([^']*)')")
_ENTITY_RE = re.compile(r"&(?:#[0-9]+|#[xX][0-9a-fA-F]+|[A-Za-z][A-Za-z0-9]*);")
_LB_RE = re.compile(r"<lb\b[^>]*/?>", re.DOTALL)
_TRAILING_MARKUP_RE = re.compile(r"(?:\s|<lb\b[^>]*/?>)+$", re.DOTALL)

_TRACKED_TAGS = frozenset({"text", "figure", "div", "persName", "orgName", "bibl", "speaker"})

Span = tuple[int, int]


@dataclass(frozen=True)
class _Zones:
    """Raw-offset content ranges that steer the scan."""

    text: tuple[Span, ...]
    excluded: tuple[Span, ...]
    plain_bibl: tuple[Span, ...]
    speakers: tuple[Span, ...]
    emphasis: tuple[Span, ...]
    figures: tuple[Span, ...] = ()
    running_heads: tuple[Span, ...] = ()


@dataclass(frozen=True)
class _Hit:
    """One match on the normalized text, before it is mapped back to raw offsets."""

    start: int
    end: int
    gid: str
    category: str
    rule: str
    tier: int
    alternatives: tuple[str, ...] = ()
    matched_form: str = ""
    form_source: str = "headword"
    case_tolerant: bool = False


@dataclass(frozen=True)
class _Norm:
    """Normalized text plus the raw span every character came from."""

    text: str
    starts: tuple[int, ...]
    ends: tuple[int, ...]


# --- public helpers ---------------------------------------------------------------


def iter_tags(fragment: str) -> Iterator[str]:
    """Yield the markup tokens of a raw XML fragment (used to check surfaces)."""
    for match in _TAG_RE.finditer(fragment):
        yield match.group(0)


# --- zones ------------------------------------------------------------------------


def _scan_zones(xml: str) -> _Zones:
    """Collect the content ranges of text, excluded zones, plain bibl, speaker, figure."""
    text: list[Span] = []
    excluded: list[Span] = []
    plain_bibl: list[Span] = []
    speakers: list[Span] = []
    paragraphs: list[Span] = []
    emphasis: list[Span] = []
    figures: list[Span] = []
    stack: list[tuple[str, dict[str, str], int]] = []

    for match in _TOKEN_RE.finditer(xml):
        token = match.group(0)
        if token.startswith(("<!", "<?")):
            continue
        name_match = _NAME_RE.match(token)
        if name_match is None:
            continue
        name = name_match.group(1)
        if token.startswith("</"):
            index = _find_open(stack, name)
            if index is None:
                continue
            open_name, attrs, content_start = stack[index]
            del stack[index:]
            _record_zone(
                open_name, attrs, content_start, match.start(),
                text, excluded, plain_bibl, speakers, paragraphs, emphasis, figures,
            )
            continue
        if token.endswith("/>"):
            continue
        attrs = _parse_attrs(token) if name in _TRACKED_TAGS else {}
        stack.append((name, attrs, match.end()))

    text_spans = _merge(text)
    excluded.extend(_apparatus_zones(xml, text_spans, paragraphs))
    return _Zones(
        text=text_spans,
        excluded=_merge(excluded),
        plain_bibl=_merge(plain_bibl),
        speakers=tuple(sorted(speakers)),
        emphasis=tuple(sorted(emphasis)),
        figures=_merge(figures),
    )


def _record_zone(
    name: str,
    attrs: dict[str, str],
    start: int,
    end: int,
    text: list[Span],
    excluded: list[Span],
    plain_bibl: list[Span],
    speakers: list[Span],
    paragraphs: list[Span],
    emphasis: list[Span],
    figures: list[Span],
) -> None:
    if start > end:
        return
    if name == "text":
        text.append((start, end))
    elif name == "figure":
        figures.append((start, end))
    elif name in ("persName", "orgName"):  # noqa: SIM114
        excluded.append((start, end))
    elif name == "div" and attrs.get("type") == "bibliography":
        excluded.append((start, end))
    elif name == "bibl":
        (excluded if attrs.get("ref") else plain_bibl).append((start, end))
    elif name == "speaker":
        speakers.append((start, end))
    elif name == "p":
        paragraphs.append((start, end))
    elif name == "hi":
        emphasis.append((start, end))


def _apparatus_zones(
    xml: str,
    text_spans: tuple[Span, ...],
    paragraphs: list[Span],
) -> list[Span]:
    """Library apparatus: E-Periodica cover sheet and photo credit paragraphs.

    The cover sheet is the range between the first and the second page break of the
    text; carrying at least COVER_FIELD_MIN of the four field lines identifies it.
    A document with a single page break has no second break to stop at, so the range
    runs to the end of the text.
    """
    zones: list[Span] = []
    for text_start, text_end in text_spans:
        breaks = list(_PB_RE.finditer(xml, text_start, text_end))
        if not breaks:
            continue
        start = breaks[0].end()
        end = breaks[1].start() if len(breaks) > 1 else text_end
        content = _plain_text(xml[start:end])
        if sum(1 for field in COVER_FIELDS if field in content) >= COVER_FIELD_MIN:
            zones.append((start, end))
    for start, end in paragraphs:
        if _plain_text(xml[start:end]).lstrip().startswith(CREDIT_PREFIXES):
            zones.append((start, end))
    return zones


def _plain_text(fragment: str) -> str:
    """Tag-free, entity-decoded content of a raw fragment (zone detection only)."""
    return html.unescape(_TAG_RE.sub(" ", fragment))


def _find_open(stack: list[tuple[str, dict[str, str], int]], name: str) -> int | None:
    for index in range(len(stack) - 1, -1, -1):
        if stack[index][0] == name:
            return index
    return None


def _parse_attrs(token: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for match in _ATTR_RE.finditer(token):
        out[match.group(1)] = match.group(3) if match.group(3) is not None else match.group(4)
    return out


def _merge(spans: list[Span]) -> tuple[Span, ...]:
    """Sort and fuse overlapping or nested ranges into disjoint ones."""
    out: list[Span] = []
    for start, end in sorted(spans):
        if out and start <= out[-1][1]:
            out[-1] = (out[-1][0], max(out[-1][1], end))
        else:
            out.append((start, end))
    return tuple(out)


def _in_spans(pos: int, spans: tuple[Span, ...]) -> bool:
    for start, end in spans:
        if pos < start:
            return False
        if pos < end:
            return True
    return False


# --- normalization ----------------------------------------------------------------


def _normalize(xml: str, zones: _Zones) -> _Norm:
    """Project the raw string onto matchable text, keeping raw offsets per character."""
    chars: list[str] = []
    starts: list[int] = []
    ends: list[int] = []
    state = {"pending_ws": -1, "suppress": False}

    def active(pos: int) -> bool:
        return _in_spans(pos, zones.text) and not _in_spans(pos, zones.excluded)

    def add_char(char: str, raw_start: int, raw_end: int) -> None:
        if char == chr(0x2019):
            # fold the typographic apostrophe like the lexicon does (_collapse)
            char = "'"
        if char.isspace():
            if not state["suppress"] and state["pending_ws"] < 0:
                state["pending_ws"] = raw_start
            return
        state["suppress"] = False
        if state["pending_ws"] >= 0:
            if chars:
                chars.append(" ")
                starts.append(state["pending_ws"])
                ends.append(state["pending_ws"] + 1)
            state["pending_ws"] = -1
        chars.append(char)
        starts.append(raw_start)
        ends.append(raw_end)

    def add_run(run: str, base: int) -> None:
        pos = 0
        for match in _ENTITY_RE.finditer(run):
            for offset, char in enumerate(run[pos:match.start()], start=pos):
                add_char(char, base + offset, base + offset + 1)
            for char in html.unescape(match.group(0)):
                add_char(char, base + match.start(), base + match.end())
            pos = match.end()
        for offset, char in enumerate(run[pos:], start=pos):
            add_char(char, base + offset, base + offset + 1)

    def add_sentinel(at: int) -> None:
        state["pending_ws"] = -1
        state["suppress"] = False
        if chars and chars[-1] != SENTINEL:
            chars.append(SENTINEL)
            starts.append(at)
            ends.append(at)

    def handle_gap(run: str, base: int) -> None:
        if active(base):
            add_run(run, base)
        else:
            add_sentinel(base)

    pos = 0
    for match in _TOKEN_RE.finditer(xml):
        handle_gap(xml[pos:match.start()], pos)
        token = match.group(0)
        if _LB_RE.fullmatch(token) and active(match.start()):
            if _parse_attrs(token).get("break") == "no":
                state["pending_ws"] = -1
                state["suppress"] = True
            else:
                state["suppress"] = False
                if state["pending_ws"] < 0:
                    state["pending_ws"] = match.start()
        pos = match.end()
    handle_gap(xml[pos:], pos)

    return _Norm(text="".join(chars), starts=tuple(starts), ends=tuple(ends))


# --- matching ---------------------------------------------------------------------


def find_candidates(
    xml_string: str,
    lexicon: dict,
) -> list[dict]:
    """Report entity mention candidates as raw character spans of `xml_string`."""
    required = ("by_first_word", "lower_by_first_word", "surnames", "caps_by_first_word")
    if any(key not in lexicon for key in required):
        raise ValueError("lexicon must be the return value of build_lexicon()")
    zones = replace(_scan_zones(xml_string), running_heads=head_spans(xml_string))
    norm = _normalize(xml_string, zones)
    speaker_hits = _speaker_hits(norm, zones, lexicon)
    lowercase_words = _lowercase_words(norm.text)
    # Anchors count document-wide (operator decision 2026-08-12): the first pass
    # collects the tier-1 person gids, the second applies them everywhere, so a
    # bare surname BEFORE the first full-name mention anchors as well.
    first_pass = _scan(xml_string, norm, zones, lexicon, speaker_hits,
                       lowercase_words=lowercase_words)
    anchors = _anchor_gids(first_pass)
    if not anchors:
        return first_pass
    return _scan(xml_string, norm, zones, lexicon, speaker_hits, anchors,
                 lowercase_words)


def _lowercase_words(text: str) -> frozenset[str]:
    """Folded words the document writes in lower case (homograph signal a)."""
    return frozenset(
        word.casefold() for word in _WORD_RUN_RE.findall(text) if word[:1].islower()
    )


def _anchor_gids(candidates: list[dict]) -> set[str]:
    """Person gids that anchor bare surnames document-wide.

    A zone demotion keeps its anchor power: the running head still names the
    document's subject and a figure caption still names the person it shows, only the
    mark itself leaves tier 1 (E105). Every other demotion (ambiguity, suspicion,
    plain bibl) loses it as before.
    """
    return {
        c["gid"] for c in candidates
        if c["category"] == "person"
        and (c["tier"] == 1 or _tier1_before_zone_demotion(c["rule"]))
    }


def _tier1_before_zone_demotion(rule: str) -> bool:
    """True when only the position suffixes separate the rule from tier 1."""
    for suffix in (RUNNING_HEAD_SUFFIX, IN_FIGURE_SUFFIX):
        if rule.endswith(suffix):
            rule = rule[:-len(suffix)]
    return ":" not in rule and TIER_BY_RULE.get(rule) == 1


def _scan(
    xml: str,
    norm: _Norm,
    zones: _Zones,
    lexicon: dict,
    speaker_hits: dict[int, _Hit],
    seed_anchors: set[str] | None = None,
    lowercase_words: frozenset[str] = frozenset(),
) -> list[dict]:
    """Left-to-right pass; `seed_anchors` carries the document-wide tier-1 anchors."""
    text = norm.text
    out: list[dict] = []
    anchored: set[str] = set(seed_anchors or ())
    review_suspect = lexicon.get("review_suspect") or frozenset()
    pos = 0
    while pos < len(text):
        if not _is_word(text[pos]) or (pos > 0 and _is_word(text[pos - 1])):
            pos += 1
            continue
        hit = speaker_hits.get(pos) or _match_at(text, pos, lexicon, anchored)
        if hit is None:
            pos = _word_end(text, pos)
            continue
        if hit.tier == 1:
            hit = _bridge_particle_surname(text, hit, lexicon)
        if base_rule(hit.rule) in _SUSPECT_RULES and _is_suspect(
            xml, norm, hit, lexicon, lowercase_words
        ):
            hit = replace(hit, rule=hit.rule + SUSPECT_SUFFIX, tier=2)
        if hit.tier == 1 and _tier1_guard(xml, norm, hit):
            hit = replace(hit, rule=hit.rule + SUSPECT_SUFFIX, tier=2)
        if hit.tier == 1 and (hit.gid, hit.matched_form) in review_suspect:
            hit = replace(hit, rule=hit.rule + SUSPECT_SUFFIX, tier=2)
        candidate, resume = _build_candidate(xml, norm, zones, hit)
        if candidate is not None:
            # Position demotions in the documented suffix order: the figure zone
            # (a property of the block) before the running head (of the page). Both
            # read the tier the rules produced, so the anchor survives the demotion.
            anchor_tier = candidate["tier"]
            if _in_spans(candidate["start"], zones.figures):
                candidate["rule"] += IN_FIGURE_SUFFIX
                candidate["tier"] = 2
            if _in_spans(candidate["start"], zones.running_heads):
                candidate["rule"] += RUNNING_HEAD_SUFFIX
                candidate["tier"] = 2
            out.append(candidate)
            if anchor_tier == 1:
                anchored.add(candidate["gid"])
        pos = max(resume, pos + 1)
    return out


def base_rule(rule: str) -> str:
    """The rule without its suffixes (derived channel, :ambiguous, :suspect, position)."""
    return rule.split(":", 1)[0]


# Established import name of the suffix split (scripts.eval.entity_eval_sample).
_base_rule = base_rule


# --- homograph suspicion ----------------------------------------------------------


def _is_suspect(
    xml: str,
    norm: _Norm,
    hit: _Hit,
    lexicon: dict,
    lowercase_words: frozenset[str],
) -> bool:
    """Deterministic signals that a surname hit is a homograph, not a mention."""
    n_start, n_end = hit.start, hit.end
    text = norm.text
    word = text[n_start:n_end]
    folded = word.casefold()
    if folded in lowercase_words or folded in FUNCTION_WORDS:
        return True
    if _hyphen_adjacent(xml, norm, hit):
        return True
    if _paren_without_digit_after(text, n_end):
        return True
    if _unknown_capital_before(text, n_start, n_end, lexicon):
        return True
    # A genitive name is followed by its head noun, and German capitalizes every
    # noun, so the trailing signal would fire on every correct genitive mention.
    genitive = word.endswith("s") and word[:-1] in lexicon["surnames"]
    return not genitive and _unknown_capital_after(text, n_start, n_end, lexicon)


def _hyphen_adjacent(xml: str, norm: _Norm, hit: _Hit) -> bool:
    """A hyphen directly at the span border makes the hit part of a compound.

    The adjudicated cases are "UNESCO-Kommission" (docs 2450/2680), where the token
    names only part of the printed organisation; hyphens inside a listed form
    ("Saint-Hélier") sit inside the span and never trigger this.
    """
    raw_start, raw_end = norm.starts[hit.start], norm.ends[hit.end - 1]
    return (xml[max(raw_start - 1, 0):raw_start] == "-"
            or xml[raw_end:raw_end + 1] == "-")


def _paren_without_digit_after(text: str, n_end: int) -> bool:
    """A bare parenthetical right after the surname reads as a work or qualifier.

    The adjudicated case is "d'Augustin (de Malègue)" (doc 110), the novel's title;
    a dated parenthesis ("Jaspers (1883-1969)") corroborates the person instead.
    """
    match = _PAREN_AFTER_RE.match(text, n_end)
    return bool(match) and not any(char.isdigit() for char in match.group(1))


def _tier1_guard(xml: str, norm: _Norm, hit: _Hit) -> bool:
    """Tier-1 demotions from the adjudicated error classes of the evaluation (E109).

    The compound signal binds every tier-1 rule; the citation frames and the
    institution container bind the person full-name rules, whose confirmed errors
    all name a work or an institution rather than the person.
    """
    if _hyphen_adjacent(xml, norm, hit):
        return True
    if hit.category != "person" or base_rule(hit.rule) not in _PERSON_FULL_RULES:
        return False
    text = norm.text
    if _EDITOR_AFTER_RE.match(text, hit.end):
        return True
    tail = text[max(0, hit.start - 40):hit.start]
    if _AUTHOR_SLOT_RE.search(tail):
        return True
    before = _WORD_BEFORE_RE.search(tail)
    return bool(before) and before.group(1) in ORG_CONTAINERS


def _bridge_particle_surname(text: str, hit: _Hit, lexicon: dict) -> _Hit:
    """Extend a person full-name hit across an internal particle to its own surname.

    The corpus prints "Saint Ignace de Loyola" as one mention; without the bridge
    the scan reports the leading form and the trailing surname as two spans (the
    adjudicated wrong_span of doc 2330). Only the hit's own entity may continue the
    name, so "Karl Jaspers de Marcel" never merges.
    """
    if hit.category != "person" or base_rule(hit.rule) not in _PERSON_FULL_RULES:
        return hit
    match = _PARTICLE_RE.match(text, hit.end)
    if match is None:
        return hit
    word = match.group(1)
    key = word[:-1] if word.endswith("s") and word[:-1] in lexicon["surnames"] else word
    if hit.gid not in lexicon["surnames"].get(key, ()):
        return hit
    return replace(hit, end=match.end())


def _unknown_capital_before(text: str, n_start: int, n_end: int, lexicon: dict) -> bool:
    if n_start == 0 or text[n_start - 1] != " ":
        return False
    end = n_start - 1
    start = end
    while start > 0 and _is_word(text[start - 1]):
        start -= 1
    if start == end or _starts_sentence(text, start):
        return False
    word = text[start:end]
    if word.casefold() in HONORIFICS or not word[:1].isupper():
        return False
    return not _is_known_form(text[start:n_end], lexicon)


def _unknown_capital_after(text: str, n_start: int, n_end: int, lexicon: dict) -> bool:
    if text[n_end:n_end + 1] != " ":
        return False
    start = n_end + 1
    end = _word_end(text, start)
    if start >= end or not text[start:start + 1].isupper():
        return False
    return not _is_known_form(text[n_start:end], lexicon)


def _starts_sentence(text: str, pos: int) -> bool:
    """True when the word at `pos` is capitalized by position, not by being a name."""
    index = pos - 1
    while index >= 0 and text[index] == " ":
        index -= 1
    return index < 0 or text[index] in _SENTENCE_END


def _is_known_form(pair: str, lexicon: dict) -> bool:
    """True when the two-word span is itself a lexicon form.

    Only the pair suppresses the neighbour signal. A neighbour that merely starts some
    listed form is no corroboration: every listed forename ("Hans") would otherwise
    clear the homograph next to it (the "Hans Mayer" finding of the frontend
    evaluation, where the surname came from the GND variant "Mayer, Gertrud").
    """
    return pair in lexicon["forms"] or pair in lexicon["caps_forms"]


def _match_at(text: str, pos: int, lexicon: dict, anchored: set[str]) -> _Hit | None:
    """Lexicon form at `pos`: exact, then caps, then case-tolerant, else the surname."""
    word = text[pos:_word_end(text, pos)]
    hit = _form_hit(text, pos, lexicon, lexicon["by_first_word"].get(word, ()))
    if hit is not None:
        return hit
    caps = _caps_at(text, pos, word, lexicon)
    if caps is not None:
        return caps
    hit = _form_hit(
        text, pos, lexicon,
        lexicon["lower_by_first_word"].get(word.lower(), ()), ignore_case=True,
    )
    if hit is not None:
        return hit
    return _surname_at(text, pos, word, lexicon, anchored)


def _form_hit(
    text: str,
    pos: int,
    lexicon: dict,
    forms: tuple[str, ...],
    ignore_case: bool = False,
) -> _Hit | None:
    """Longest form of `forms` that matches at `pos`, with its own rule and tier."""
    for form in forms:
        result = _try_form(text, pos, form, ignore_case)
        if result is None:
            continue
        end, kind = result
        owners = lexicon["forms"][form]
        gid, category, rule, source = owners[0]
        # The all-caps writing of a person name belongs to the caps channel and
        # keeps its own rule id there.
        if ignore_case and category == "person" and text[pos:end].isupper():
            continue
        # A one-word title such as "Nietzsche" can also be a listed surname; reporting
        # the title alone would hide the person reading, so both bearers are named.
        bearers = _bearers(owners, lexicon["surnames"].get(form, ()))
        if kind == "adjective":
            rule, tier = "adjective-form", 2
        else:
            tier = _form_tier(rule)
        hit = _hit(pos, end, gid, category, rule, tier, bearers, form, source)
        segment = text[pos:pos + len(form)]
        return hit if segment == form else _case_tolerant(hit, segment, form)
    return None


def _case_tolerant(hit: _Hit, segment: str, form: str) -> _Hit:
    """Mark a hit that only letter case separates from its form, and weigh its case.

    A lowercased incipit ("die Mauer" for the listed "Die Mauer", doc 1060) is
    ordinary prose exactly like the fully lowercased writing: a title mention keeps
    its capitalized first word in this corpus. Works only, because German inflects
    the leading adjective of an organisation name in running prose ("deutscher
    Gewerkschaftsbund"), which is a genuine mention.
    """
    hit = replace(hit, case_tolerant=True)
    if _is_lowercase_writing(segment, form) or (
        hit.category == "work" and segment[:1].islower() and form[:1].isupper()
    ):
        return replace(hit, rule=hit.rule + SUSPECT_SUFFIX, tier=2)
    return hit


def _is_lowercase_writing(segment: str, form: str) -> bool:
    """True when a capitalized form appears as an all-lowercase run of words.

    A title or name mention keeps at least one capital in this corpus, so the
    all-lowercase writing of a listed title is ordinary vocabulary rather than a
    mention ("le capital", "les grands philosophes").
    """
    return any(char.isupper() for char in form) and not any(
        char.isupper() for char in segment
    )


def _bearers(owners: tuple, shadowed: tuple[str, ...] = ()) -> tuple[str, ...]:
    """Every listed id a form belongs to, deduplicated and in stable (sorted) order."""
    return tuple(sorted({owner[0] for owner in owners} | set(shadowed)))


def _hit(
    start: int,
    end: int,
    gid: str,
    category: str,
    rule: str,
    tier: int,
    bearers: tuple[str, ...],
    matched_form: str,
    source: str,
) -> _Hit:
    """Build a hit; several bearers make it ambiguous, which is always tier 2.

    Suffix order is fixed: base rule, then ":ambiguous" (a property of the lexicon),
    then ":suspect" (a property of the context), then ":in-plain-bibl" and ":in-figure"
    (both properties of the position), then ":running-head" (a property of the page
    position). Rules that already name the ambiguity in their base keep it.
    """
    if len(bearers) <= 1:
        return _Hit(start, end, gid, category, rule, tier, (), matched_form, source)
    return _Hit(start, end, gid, category, rule + AMBIGUOUS_SUFFIX, 2, bearers,
                matched_form, source)


def _try_form(text: str, pos: int, form: str, ignore_case: bool = False) -> tuple[int, str] | None:
    end = pos + len(form)
    segment = text[pos:end]
    if segment != form and not (ignore_case and segment.lower() == form.lower()):
        return None
    if not _is_word(form[-1]):
        return end, "plain"
    return _extend_or_reject(text, end)


def _extend_or_reject(text: str, end: int) -> tuple[int, str] | None:
    """Word boundary behind a match: plain end, genitive s, or adjective derivation."""
    for suffix in _ADJECTIVE_SUFFIXES:
        after = end + len(suffix)
        if text.startswith(suffix, end) and not _is_word_at(text, after):
            return after, "adjective"
    if text.startswith("s", end):
        return (end + 1, "genitive") if not _is_word_at(text, end + 1) else None
    return None if _is_word_at(text, end) else (end, "plain")


def _caps_at(text: str, pos: int, word: str, lexicon: dict) -> _Hit | None:
    """All-caps full name of a person; the caps index holds the uppercased forms."""
    if len(word) < 2 or not word.isupper():
        return None
    for form in lexicon["caps_by_first_word"].get(word, ()):
        end = pos + len(form)
        if text[pos:end] != form or _is_word_at(text, end):
            continue
        owners = lexicon["caps_forms"][form]
        gid, category, rule, source = owners[0]
        return _hit(pos, end, gid, category, rule, TIER_BY_RULE[rule],
                    _bearers(owners), form, source)
    return None


def _surname_at(
    text: str,
    pos: int,
    word: str,
    lexicon: dict,
    anchored: set[str],
) -> _Hit | None:
    surnames = lexicon["surnames"]
    end = pos + len(word)
    if word in surnames:
        key = word
    elif word.endswith("s") and word[:-1] in surnames:
        key = word[:-1]
    else:
        return _derived_surname_at(text, pos, word, lexicon)
    gids = surnames[key]
    in_document = [gid for gid in gids if gid in anchored]
    # An anchor decides among the bearers, so those two rules keep their reported id
    # without the ambiguity suffix; the alternatives stay visible either way.
    if len(in_document) == 1:
        return _surname_hit(pos, end, in_document[0], "anchored-surname", 1, key, gids, lexicon)
    if len(in_document) > 1:
        return _surname_hit(pos, end, in_document[0], "ambiguous-surname", 2, key, gids, lexicon)
    return _hit(pos, end, gids[0], "person", "bare-surname", 2, gids,
                *_surname_origin(lexicon, "surname_forms", key, gids[0]))


def _surname_hit(
    pos: int,
    end: int,
    gid: str,
    rule: str,
    tier: int,
    key: str,
    gids: tuple[str, ...],
    lexicon: dict,
) -> _Hit:
    """Surname hit whose id the anchor rule already decided (no ambiguity suffix)."""
    matched_form, source = _surname_origin(lexicon, "surname_forms", key, gid)
    return _Hit(pos, end, gid, "person", rule, tier,
                gids if len(gids) > 1 else (), matched_form, source)


def _surname_origin(lexicon: dict, index: str, key: str, gid: str) -> tuple[str, str]:
    """(form, source) that put a surname into the index; the key itself is the fallback."""
    return lexicon.get(index, {}).get(key, {}).get(gid, (key, "surname-index"))


def _derived_surname_at(text: str, pos: int, word: str, lexicon: dict) -> _Hit | None:
    """Adjective derivation or all-caps writing of a listed surname; both tier 2."""
    end = pos + len(word)
    stem = _adjective_stem(word, lexicon["surnames"])
    if stem is not None:
        gids = lexicon["surnames"][stem]
        return _hit(pos, end, gids[0], "person", "adjective-form", 2, gids,
                    *_surname_origin(lexicon, "surname_forms", stem, gids[0]))
    if len(word) > 1 and word.isupper():
        gids = lexicon["caps_surnames"].get(word)
        if gids:
            return _hit(pos, end, gids[0], "person", "caps-surname", 2, gids,
                        *_surname_origin(lexicon, "caps_surname_forms", word, gids[0]))
    return None


def _adjective_stem(word: str, surnames: dict[str, tuple[str, ...]]) -> str | None:
    for suffix in _ADJECTIVE_SUFFIXES:
        if len(word) > len(suffix) and word.endswith(suffix) and word[:-len(suffix)] in surnames:
            return word[:-len(suffix)]
    return None


def _speaker_hits(norm: _Norm, zones: _Zones, lexicon: dict) -> dict[int, _Hit]:
    """Speaker slots whose verbatim text is a full name or a known surname."""
    hits: dict[int, _Hit] = {}
    for raw_start, raw_end in zones.speakers:
        start = bisect_left(norm.starts, raw_start)
        end = bisect_left(norm.starts, raw_end)
        while start < end and not _is_word(norm.text[start]):
            start += 1
        while end > start and not _is_word(norm.text[end - 1]):
            end -= 1
        if start >= end:
            continue
        label = norm.text[start:end]
        if SENTINEL in label:
            continue
        # The speaker rule is tier 1, so only base forms may reach it; a derived
        # spelling falls through to the surname index and stays on the worklist.
        persons = [
            owner for owner in lexicon["forms"].get(label, ())
            if owner[1] == "person" and ":" not in owner[2]
        ]
        if persons:
            hits[start] = _hit(start, end, persons[0][0], "person", "speaker", 1,
                               _bearers(tuple(persons)), label, persons[0][3])
            continue
        gids = lexicon["surnames"].get(label)
        if gids:
            hits[start] = _hit(start, end, gids[0], "person", "speaker", 1, gids,
                               *_surname_origin(lexicon, "surname_forms", label, gids[0]))
    return hits


def _build_candidate(
    xml: str,
    norm: _Norm,
    zones: _Zones,
    hit: _Hit,
) -> tuple[dict | None, int]:
    """Map a normalized hit back to raw offsets and apply the zone downgrades."""
    n_start, n_end = hit.start, hit.end
    raw_start = norm.starts[n_start]
    raw_end = norm.ends[n_end - 1]
    surface = xml[raw_start:raw_end]
    rule, tier = hit.rule, hit.tier
    first_part = _first_text_part(surface)
    if first_part is not None:
        if not first_part:
            return None, n_end
        raw_end = raw_start + len(first_part)
        surface = first_part
        rule, tier = "crosses-markup", 2
    if _in_spans(raw_start, zones.plain_bibl):
        rule += PLAIN_BIBL_SUFFIX
        tier = 2
    candidate = {
        "gid": hit.gid,
        "category": hit.category,
        "surface": surface,
        "start": raw_start,
        "end": raw_end,
        "tier": tier,
        "rule": rule,
        "alternatives": list(hit.alternatives),
        "matched_form": hit.matched_form,
        "form_source": hit.form_source,
    }
    if base_rule(rule) == "short-title":
        candidate["evidence"] = _title_evidence(norm, zones, hit, raw_start, raw_end)
    candidate["context"] = _context(norm.text, n_start, n_end)
    return candidate, max(bisect_right(norm.ends, raw_end), n_start + 1)


def _title_evidence(
    norm: _Norm,
    zones: _Zones,
    hit: _Hit,
    raw_start: int,
    raw_end: int,
) -> str:
    """Typographic pre-sorting of a one-word work title.

    A single word is a title only by its setting, so three signals count as evidence:
    the span sits completely inside an `hi` element, quotation marks or guillemets
    enclose it directly, or a possessive stands right in front of it. Everything else
    is reported without evidence and stays a candidate for the judge stage; the class
    is not dropped, the measurement decides that.
    """
    text = norm.text
    start, end = hit.start, hit.end
    if any(zone[0] <= raw_start and raw_end <= zone[1] for zone in zones.emphasis):
        return EVIDENCE_TYPOGRAPHIC
    before = text[start - 1:start] if start else ""
    after = text[end:end + 1]
    if before in QUOTE_CHARS and after in QUOTE_CHARS:
        return EVIDENCE_TYPOGRAPHIC
    return EVIDENCE_TYPOGRAPHIC if _follows_possessive(text, start) else EVIDENCE_NONE


def _follows_possessive(text: str, pos: int) -> bool:
    """True when the word directly in front of `pos` is a possessive pronoun."""
    if pos == 0 or text[pos - 1] != " ":
        return False
    end = pos - 1
    start = end
    while start > 0 and _is_word(text[start - 1]):
        start -= 1
    return start < end and text[start:end].casefold() in POSSESSIVES


def _first_text_part(surface: str) -> str | None:
    """None when only lb markup is embedded, else the part before the foreign tag."""
    for match in _TAG_RE.finditer(surface):
        if _LB_RE.fullmatch(match.group(0)):
            continue
        return _TRAILING_MARKUP_RE.sub("", surface[:match.start()])
    return None


def _context(text: str, n_start: int, n_end: int) -> str:
    window = text[max(0, n_start - CONTEXT_RADIUS):n_end + CONTEXT_RADIUS]
    return " ".join(window.replace(SENTINEL, " ").split())
