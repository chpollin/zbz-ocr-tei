"""Deterministic detection of running heads (Kolumnentitel) at page starts.

Operator convention E105 keeps running heads out of the entity layer: the author name
or work title printed as page furniture on every page is not a mention of the person or
the work. This module is the shared detection core. `scripts.eval.running_head_audit`
validates it against the facsimile-adjudicated ground truth; `scripts.tei.entity_matcher`
consumes `head_spans` to hold in-zone candidates out of tier 1. Nothing here writes TEI.

Detection, applied per document to a delivered TEI string:

  1. Page starts are the `<pb>` positions inside `<body>`, taken from the shared
     segmentation of scripts.tei.pb_split (read only), so the page numbering matches the
     rest of the pipeline.
  2. The head window of a page is its first MAX_HEAD_SEGMENTS non-empty segments. A
     segment ends at every line or block tag (`<lb/>`, `<p>`, `<head>`, ...); inline
     markup stays inside it. Whitespace-only and pure-number segments are skipped without
     consuming a slot of the window, because the printed folio often stands alone in its
     own line ahead of the head.
  3. A segment is normalized for recurrence: inline markup dropped, whitespace collapsed,
     apostrophe variants unified, diacritics folded (the same OCR word appears with and
     without accents across the corpus), casefolded, leading and trailing digits and
     punctuation stripped -- the printed page number rides along with the head and varies
     per page.
  4. A normalized form recurring on MIN_RECURRENCE distinct pages of the document is a
     head pattern. Alternating verso/recto heads (author on one side, work title on the
     other) need no separate rule at this step: each of the two forms still recurs on its
     own half of the pages. In a short document that halving can push the counterpart
     below the threshold, so inside a document that already carries a primary pattern a
     second form recurring on MIN_COMPANION_RECURRENCE pages is accepted as its companion.
  5. A one-off segment that contains a primary form as a whole word and stays within
     CONTAINS_LENGTH_FACTOR of its length is accepted too; OCR merges the folio or the
     author prefix into the head line on single pages.

Speaker labels are excluded: `<speaker>` is a structural element of the recorded
discussions, and the speaker name at a page start is a real mention rather than page
furniture.
"""

from __future__ import annotations

import re
import unicodedata
from bisect import bisect_right
from collections import defaultdict

from scripts.tei.pb_split import BODY_INNER_RE, PB_RE

# Detection constants. Calibrated against the 25 facsimile-adjudicated running-head marks
# of data/entities/mention_verdicts.json; every value is deliberately on the conservative
# side, because a false alarm costs a real entity mention while a miss only leaves a head
# unsuppressed.
MAX_HEAD_SEGMENTS = 2       # head window: first non-empty segments of a page
MIN_HEAD_CHARS = 2          # below this a normalized form is noise
MAX_HEAD_CHARS = 80         # a head line is short; body prose is not
MIN_RECURRENCE = 3          # distinct pages carrying the form -> primary pattern
MIN_COMPANION_RECURRENCE = 2  # alternating counterpart in a document with a primary
CONTAINS_LENGTH_FACTOR = 2.0  # a merged head variant stays close to the primary length

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

APOSTROPHES = {0x2018: "'", 0x2019: "'", 0x201B: "'", 0x02BC: "'", 0x00B4: "'", 0x0060: "'"}


# ---------------------------------------------------------------------------
# Normalization and page segmentation
# ---------------------------------------------------------------------------

def normalize_head(raw: str) -> str:
    """Recurrence key of a page-start segment; empty when nothing but furniture is left."""
    text = " ".join(TAG_RE.sub(" ", raw).split())
    text = text.translate(APOSTROPHES)
    text = "".join(c for c in unicodedata.normalize("NFD", text)
                   if not unicodedata.combining(c))
    text = text.casefold()
    text = re.sub(r"^[\W\d_]+", "", text)
    text = re.sub(r"[\W\d_]+$", "", text)
    return " ".join(text.split())


def head_window(xml_text: str, lo: int, hi: int) -> list[dict]:
    """The first MAX_HEAD_SEGMENTS non-empty segments of the page span [lo, hi).

    Offsets are absolute in `xml_text`, so a zone can be looked up against the mark
    offsets of the entity wave, which index the same stream.
    """
    raw: list[tuple[int, int, str]] = []
    cursor, stack = lo, []
    for match in TAG_RE.finditer(xml_text, lo, hi):
        name = match.group(2)
        if name in INLINE_TAGS:
            continue
        if match.start() > cursor:
            raw.append((cursor, match.start(), stack[-1] if stack else ""))
        if match.group(1) == "/":
            if stack and stack[-1] == name:
                stack.pop()
        elif not match.group(0).rstrip().endswith("/>"):
            stack.append(name)
        cursor = match.end()
    if hi > cursor:
        raw.append((cursor, hi, stack[-1] if stack else ""))

    window = []
    for start, end, parent in raw:
        form = normalize_head(xml_text[start:end])
        if not form:
            continue
        window.append({"start": start, "end": end, "form": form, "parent": parent,
                       "position": len(window),
                       "text": " ".join(TAG_RE.sub(" ", xml_text[start:end]).split())})
        if len(window) >= MAX_HEAD_SEGMENTS:
            break
    return window


def page_candidates(xml_text: str) -> tuple[int, dict[str, list[dict]]]:
    """(page count, normalized form -> its page-start occurrences) for one document."""
    body = BODY_INNER_RE.search(xml_text)
    if not body:
        return 0, {}
    base, inner = body.start(1), body.group(1)
    breaks = list(PB_RE.finditer(inner))
    by_form: dict[str, list[dict]] = defaultdict(list)
    for index, pb in enumerate(breaks):
        end = breaks[index + 1].start() if index + 1 < len(breaks) else len(inner)
        for segment in head_window(xml_text, base + pb.end(), base + end):
            if segment["parent"] in EXCLUDED_PARENT_TAGS:
                continue
            if not MIN_HEAD_CHARS <= len(segment["form"]) <= MAX_HEAD_CHARS:
                continue
            by_form[segment["form"]].append(dict(segment, page=index + 1))
    return len(breaks), dict(by_form)


# ---------------------------------------------------------------------------
# Detection
# ---------------------------------------------------------------------------

def _pages_of(occurrences: list[dict]) -> set[int]:
    return {occurrence["page"] for occurrence in occurrences}


def _accept(by_form: dict[str, list[dict]]) -> dict[str, str]:
    """Accepted forms mapped to the rule that accepted them, applied in a fixed order."""
    accepted = {form: "primary" for form, occurrences in by_form.items()
                if len(_pages_of(occurrences)) >= MIN_RECURRENCE}
    if not accepted:
        return accepted
    primary = sorted(accepted)
    for form, occurrences in by_form.items():
        if form not in accepted and len(_pages_of(occurrences)) >= MIN_COMPANION_RECURRENCE:
            accepted[form] = "companion"
    for form in sorted(by_form):
        if form in accepted:
            continue
        for base in primary:
            if len(form) <= CONTAINS_LENGTH_FACTOR * len(base) and re.search(
                    r"(?:^|\W)" + re.escape(base) + r"(?:\W|$)", form):
                accepted[form] = "contains"
                break
    return accepted


def _parity(pages: list[int]) -> str:
    """Page parity of a pattern; an alternating verso/recto head lands on one side."""
    remainders = {page % 2 for page in pages}
    if len(remainders) > 1:
        return "mixed"
    return "odd" if remainders == {1} else "even"


def detect_document(xml_text: str) -> dict:
    """Head patterns of one document, ordered by normalized form."""
    page_count, by_form = page_candidates(xml_text)
    accepted = _accept(by_form)
    patterns = []
    for form in sorted(accepted):
        occurrences = sorted(by_form[form], key=lambda o: (o["page"], o["start"]))
        pages = sorted(_pages_of(occurrences))
        patterns.append({
            "form": form,
            "kind": accepted[form],
            "pages": pages,
            "page_parity": _parity(pages),
            "segment_positions": sorted({o["position"] for o in occurrences}),
            "parent_elements": sorted({o["parent"] for o in occurrences}),
            "zones": [{"page": o["page"], "start": o["start"], "end": o["end"],
                       "text": o["text"]} for o in occurrences],
        })
    return {"pages": page_count, "patterns": patterns}


def head_spans(xml_text: str) -> tuple[tuple[int, int], ...]:
    """Sorted raw-offset spans of every running-head zone of one document."""
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
