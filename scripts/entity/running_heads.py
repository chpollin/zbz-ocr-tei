"""Deterministic detection of the repeated page apparatus (Kolumnentitel, running feet).

Operator convention E105 keeps the page apparatus out of the entity layer: the author name
or work title printed as furniture on every page is not a mention of the person or the
work. E105/E108 keep the opposite case in scope: the byline of an opening page, a title
page and a caption are real mentions. This module is the shared detection core.
`scripts.entity.running_head_audit` validates it against the facsimile-adjudicated ground
truth; `scripts.entity.entity_matcher` consumes `head_spans` to hold in-zone candidates out
of tier 1. Nothing here writes TEI.

What separates apparatus from byline is repetition, never wording or capitalisation: the
apparatus repeats across the pages of a document, the byline stands once where a
contribution opens. Position is no criterion of acceptance, because the delivered TEI
carries the apparatus wherever the reading order dropped it, as the page's first block, as
its last one, or spliced into the middle of a sentence.

Detection, applied per document to a delivered TEI string:

  1. Page starts are the `<pb>` positions inside `<body>`, taken from the shared
     segmentation of scripts.core.pb_split (read only), so the page numbering matches the
     rest of the pipeline.
  2. A page is cut into segments at every line or block tag (`<lb/>`, `<p>`, `<head>`,
     ...); inline markup stays inside a segment. Whitespace-only and pure-number segments
     drop out, because the printed folio rides along with the apparatus and varies per
     page. A segment between MIN_HEAD_CHARS and MAX_HEAD_CHARS is an apparatus candidate:
     an apparatus line is short, body prose is not.
  3. A normalized form recurring alone on MIN_RECURRENCE distinct pages, and on at least
     MIN_RECURRENCE_SHARE of the document's pages, is a primary pattern. The share floor
     holds the front matter of a long book below the line: three title leaves of a
     two-hundred-page book repeat nothing.
  4. Where no form clears that threshold, two forms of pure opposite page parity covering
     at least ALTERNATION_COVERAGE of the document are accepted as an alternating
     verso/recto pair. In a short document the alternation halves every count, so the
     author on the versos and the title on the rectos would both stay below the floor.
  5. A one-off segment that contains a primary form as a whole word and stays within
     CONTAINS_LENGTH_FACTOR of its length is accepted too; OCR merges the folio or the
     author prefix into the apparatus line on single pages.

An accepted form is not apparatus in every one of its occurrences. Four exemptions release
an occurrence, each recorded with its reason:

  repeated-on-page  the apparatus stands once per page; a form used twice on a page is
                    content there, and that page carries no zone at all
  title-block       the occurrence sits in the leading block of a page that carries a
                    `<head>`, which is where the pipeline puts the title of a division
                    together with its byline
  off-slot          the occurrence follows another apparatus form on its page although the
                    form stands alone everywhere else; that is the byline printed under
                    the title on the opening page of a contribution
  inner-variant     a merged variant (rule 5) below the page opening is a quotation of
                    the apparatus line rather than the line itself

Speaker labels are excluded: `<speaker>` is a structural element of the recorded
discussions, and the speaker name is a real mention rather than page furniture.
"""

from __future__ import annotations

import math
import re
import unicodedata
from bisect import bisect_right
from collections import Counter, defaultdict

from scripts.core.pb_split import BODY_INNER_RE, PB_RE

# Detection constants. Calibrated against the facsimile-adjudicated marks of
# data/entities/mention_verdicts.json; every value is deliberately on the conservative
# side, because a false alarm costs a real entity mention while a miss only leaves an
# apparatus line unsuppressed.
MIN_HEAD_CHARS = 2          # below this a normalized form is noise
MAX_HEAD_CHARS = 80         # an apparatus line is short; body prose is not
MIN_RECURRENCE = 3          # distinct pages carrying the form -> primary pattern
MIN_RECURRENCE_SHARE = 0.05  # and at least this share of the document's pages
MIN_ALTERNATION_PAGES = 2   # pages per side of a verso/recto pair
ALTERNATION_COVERAGE = 0.5  # share of the document the pair has to cover
TITLE_BLOCK_SEGMENTS = 4    # leading segments a title block may span
EDGE_SEGMENTS = 3           # leading segments a merged variant may stand in
CONTAINS_LENGTH_FACTOR = 2.0  # a merged variant stays close to the primary length

TAG_RE = re.compile(r"<\s*(/?)\s*([A-Za-z][\w:.-]*)[^>]*>")

# Inline markup stays inside a segment; every other element ends one. The whitelist is the
# safe direction: an unknown element becomes a boundary rather than silently gluing two
# printed lines into one candidate.
INLINE_TAGS = frozenset({
    "hi", "foreign", "title", "sic", "corr", "choice", "orig", "reg", "unclear",
    "supplied", "add", "del", "ref", "persName", "name", "rs", "orgName", "placeName",
    "date", "abbr", "expan", "seg", "q", "emph", "gap", "space", "num", "g", "c",
})

# A speaker label is a structural element of the discussion transcripts, not page
# furniture; its name is a real mention even when it opens a page.
EXCLUDED_PARENT_TAGS = frozenset({"speaker"})

TITLE_ELEMENT = "head"

APOSTROPHES = {0x2018: "'", 0x2019: "'", 0x201B: "'", 0x02BC: "'", 0x00B4: "'", 0x0060: "'"}


# ---------------------------------------------------------------------------
# Normalization and page segmentation
# ---------------------------------------------------------------------------

def normalize_head(raw: str) -> str:
    """Recurrence key of a page segment; empty when nothing but furniture is left."""
    text = " ".join(TAG_RE.sub(" ", raw).split())
    text = text.translate(APOSTROPHES)
    text = "".join(c for c in unicodedata.normalize("NFD", text)
                   if not unicodedata.combining(c))
    text = text.casefold()
    text = re.sub(r"^[\W\d_]+", "", text)
    text = re.sub(r"[\W\d_]+$", "", text)
    return " ".join(text.split())


def page_segments(xml_text: str, lo: int, hi: int) -> list[dict]:
    """Every non-empty segment of the page span [lo, hi), in reading order.

    Offsets are absolute in `xml_text`, so a zone can be looked up against the mark
    offsets of the entity wave, which index the same stream.
    """
    raw: list[tuple[int, int, list[str]]] = []
    cursor, stack = lo, []
    for match in TAG_RE.finditer(xml_text, lo, hi):
        name = match.group(2)
        if name in INLINE_TAGS:
            continue
        if match.start() > cursor:
            raw.append((cursor, match.start(), list(stack)))
        if match.group(1) == "/":
            if stack and stack[-1] == name:
                stack.pop()
        elif not match.group(0).rstrip().endswith("/>"):
            stack.append(name)
        cursor = match.end()
    if hi > cursor:
        raw.append((cursor, hi, list(stack)))

    segments = []
    for start, end, chain in raw:
        form = normalize_head(xml_text[start:end])
        if not form:
            continue
        segments.append({
            "start": start, "end": end, "form": form,
            "parent": chain[-1] if chain else "",
            "in_head": TITLE_ELEMENT in chain,
            "short": MIN_HEAD_CHARS <= len(form) <= MAX_HEAD_CHARS,
            "text": " ".join(TAG_RE.sub(" ", xml_text[start:end]).split()),
        })
    for index, segment in enumerate(segments):
        segment["index"] = index
    return segments


def _pages(xml_text: str) -> dict[int, list[dict]]:
    """Page number -> its segments, for the body of one document."""
    body = BODY_INNER_RE.search(xml_text)
    if not body:
        return {}
    base, inner = body.start(1), body.group(1)
    breaks = list(PB_RE.finditer(inner))
    pages = {}
    for index, pb in enumerate(breaks):
        end = breaks[index + 1].start() if index + 1 < len(breaks) else len(inner)
        pages[index + 1] = page_segments(xml_text, base + pb.end(), base + end)
    return pages


def _candidates(pages: dict[int, list[dict]]) -> dict[str, list[dict]]:
    """Normalized form -> its apparatus-candidate occurrences across the document."""
    by_form: dict[str, list[dict]] = defaultdict(list)
    for page, segments in pages.items():
        for segment in segments:
            if segment["short"] and segment["parent"] not in EXCLUDED_PARENT_TAGS:
                by_form[segment["form"]].append(dict(segment, page=page))
    return dict(by_form)


def page_candidates(xml_text: str) -> tuple[int, dict[str, list[dict]]]:
    """(page count, normalized form -> its apparatus-candidate occurrences)."""
    pages = _pages(xml_text)
    return len(pages), _candidates(pages)


# ---------------------------------------------------------------------------
# Acceptance
# ---------------------------------------------------------------------------

def _solo_pages(occurrences: list[dict]) -> set[int]:
    """Pages carrying the form exactly once; the apparatus stands once per page."""
    counts = Counter(occurrence["page"] for occurrence in occurrences)
    return {page for page, count in counts.items() if count == 1}


def _required(page_count: int) -> int:
    return max(MIN_RECURRENCE, math.ceil(page_count * MIN_RECURRENCE_SHARE))


def _parity(pages) -> str:
    """Page parity of a pattern; an alternating verso/recto head lands on one side."""
    remainders = {page % 2 for page in pages}
    if not remainders:
        return "none"
    if len(remainders) > 1:
        return "mixed"
    return "odd" if remainders == {1} else "even"


def _alternating(solo: dict[str, set[int]], page_count: int) -> dict[str, str]:
    """Verso/recto pairs whose two sides together cover the document."""
    sides = sorted(form for form, pages in solo.items()
                   if len(pages) >= MIN_ALTERNATION_PAGES and _parity(pages) != "mixed")
    accepted: dict[str, str] = {}
    for position, verso in enumerate(sides):
        for recto in sides[position + 1:]:
            if _parity(solo[verso]) == _parity(solo[recto]):
                continue
            if len(solo[verso] | solo[recto]) >= page_count * ALTERNATION_COVERAGE:
                accepted[verso] = accepted[recto] = "alternating"
    return accepted


def _accept(by_form: dict[str, list[dict]], solo: dict[str, set[int]],
            page_count: int) -> dict[str, str]:
    """Accepted forms mapped to the rule that accepted them, applied in a fixed order."""
    required = _required(page_count)
    accepted = {form: "primary" for form, pages in solo.items() if len(pages) >= required}
    if not accepted:
        accepted = _alternating(solo, page_count)
    if not accepted:
        return accepted
    established = sorted(accepted)
    for form in sorted(by_form):
        if form in accepted:
            continue
        for base in established:
            if len(form) <= CONTAINS_LENGTH_FACTOR * len(base) and re.search(
                    r"(?:^|\W)" + re.escape(base) + r"(?:\W|$)", form):
                accepted[form] = "contains"
                break
    return accepted


# ---------------------------------------------------------------------------
# Exemptions: an accepted form is no apparatus in every one of its occurrences
# ---------------------------------------------------------------------------

def _title_block(segments: list[dict]) -> int:
    """Length of the leading block of a page that opens a division, else 0."""
    end = 0
    while end < len(segments) and segments[end]["short"] and end < TITLE_BLOCK_SEGMENTS:
        end += 1
    return end if any(segment["in_head"] for segment in segments[:end]) else 0


def _following_pages(pages: dict[int, list[dict]], by_form: dict[str, list[dict]],
                     accepted: dict[str, str]) -> dict[str, set[int]]:
    """Per form, the pages where it directly follows another apparatus form."""
    apparatus = {(occurrence["page"], occurrence["index"])
                 for form in accepted for occurrence in by_form[form]}
    following: dict[str, set[int]] = defaultdict(set)
    for form in accepted:
        for occurrence in by_form[form]:
            before = occurrence["index"] - 1
            if before < 0 or (occurrence["page"], before) not in apparatus:
                continue
            if pages[occurrence["page"]][before]["form"] != form:
                following[form].add(occurrence["page"])
    return following


def _exemption(occurrence: dict, kind: str, solo: set[int], title_block: int,
               following: set[int]) -> str | None:
    """Why this occurrence is no apparatus zone, or None when it is one."""
    if occurrence["page"] not in solo:
        return "repeated-on-page"
    if occurrence["index"] < title_block:
        return "title-block"
    if occurrence["page"] in following and len(following) * 2 < len(solo):
        return "off-slot"
    if kind == "contains" and occurrence["index"] >= EDGE_SEGMENTS:
        return "inner-variant"
    return None


# ---------------------------------------------------------------------------
# Detection
# ---------------------------------------------------------------------------

def _view(occurrence: dict, reason: str | None = None) -> dict:
    view = {"page": occurrence["page"], "start": occurrence["start"],
            "end": occurrence["end"], "text": occurrence["text"]}
    if reason is not None:
        view["reason"] = reason
    return view


def detect_document(xml_text: str) -> dict:
    """Apparatus patterns of one document, ordered by normalized form."""
    pages = _pages(xml_text)
    page_count, by_form = len(pages), _candidates(pages)
    solo = {form: _solo_pages(occurrences) for form, occurrences in by_form.items()}
    accepted = _accept(by_form, solo, page_count)
    following = _following_pages(pages, by_form, accepted)
    title_blocks = {page: _title_block(segments) for page, segments in pages.items()}

    patterns = []
    for form in sorted(accepted):
        kind = accepted[form]
        occurrences = sorted(by_form[form], key=lambda o: (o["page"], o["start"]))
        zones, exempt = [], []
        for occurrence in occurrences:
            reason = _exemption(occurrence, kind, solo[form],
                                title_blocks[occurrence["page"]], following[form])
            (exempt if reason else zones).append(_view(occurrence, reason))
        zone_pages = sorted({zone["page"] for zone in zones})
        patterns.append({
            "form": form,
            "kind": kind,
            "pages": zone_pages,
            "page_parity": _parity(zone_pages),
            "segment_positions": sorted({o["index"] for o in occurrences}),
            "parent_elements": sorted({o["parent"] for o in occurrences}),
            "zones": zones,
            "exempt": exempt,
        })
    return {"pages": page_count, "patterns": patterns}


def head_spans(xml_text: str) -> tuple[tuple[int, int], ...]:
    """Sorted raw-offset spans of every apparatus zone of one document."""
    return tuple(sorted(
        (zone["start"], zone["end"])
        for pattern in detect_document(xml_text)["patterns"]
        for zone in pattern["zones"]
    ))


# ---------------------------------------------------------------------------
# Zone lookup
# ---------------------------------------------------------------------------

def zone_lookup(documents: list[dict]):
    """(doc, offset) -> the zone containing the offset, or None."""
    index: dict[str, tuple[list[int], list[dict]]] = {}
    for document in documents:
        zones = [dict(zone, form=pattern["form"], kind=pattern["kind"])
                 for pattern in document["patterns"] for zone in pattern["zones"]]
        zones.sort(key=lambda z: z["start"])
        index[document["doc"]] = ([z["start"] for z in zones], zones)

    def resolve(doc: str, offset: int) -> dict | None:
        starts, zones = index.get(doc, ([], []))
        position = bisect_right(starts, offset) - 1
        if position < 0:
            return None
        zone = zones[position]
        return zone if zone["start"] <= offset < zone["end"] else None

    return resolve
