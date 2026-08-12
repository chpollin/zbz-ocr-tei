"""Deterministic entity candidate search on delivered TEI-XML (analysis only).

Design plan and rule catalogue: knowledge/entity-integration.md (sections "Target
model" and "Matching method"). This module has no write path and never calls a
language model; ids always come from the curated list.

Two public functions:

    build_lexicon(entities_path, cache_path, legacy_path=None) -> dict
        Merges the curated list `data/entities/all_entities.json`, the lobid cache
        `data/entities/gnd_cache.json` (name variants, optional) and the legacy
        mention index `output/gnd_analysis/gnd_entities.json` (optional) into one
        lexicon. Entries without a label are skipped, so are entries whose cache
        answer is 404 (defective GND id).

    find_candidates(xml_string, lexicon) -> list[dict]
        Reports mentions as raw character spans of the input string. Every candidate
        carries gid, category, surface, start, end, tier, rule, context.
        Hard invariants: xml_string[start:end] == surface, candidates sorted by
        start and free of overlap, spans only inside <text>, and the surface carries
        no markup other than <lb/> tags.

Search model. The scan runs on a normalized projection of the raw string: markup
contributes nothing, `<lb break="no"/>` joins a broken word, a plain `<lb/>` counts
as one space, whitespace collapses to a single space, and character references are
decoded. Every normalized character keeps the raw offsets it came from, so a match
maps back to an exact byte span whose slice is the surface. Excluded zones emit a
sentinel character instead of their text, which blocks any match from running across
them.

Deliberate simplifications (upgrade path in the milestones M3 to M5):

- A match that crosses non-lb markup is reported truncated to its first text part
  with rule "crosses-markup" and tier 2, instead of being dropped; the worklist keeps
  the position that way. Truncation to an empty part drops the candidate.
- A form that several entities share becomes tier 2 with the rule suffix
  ":ambiguous"; the reported gid is the lexicographically first one, the judge stage
  resolves the alternatives from the lexicon.
- Person labels without a forename (mononyms such as "Platon") reach no tier-1 rule;
  they enter the surname index and can only surface as tier 2.
- The speaker rule compares the slot text verbatim (after stripping surrounding
  punctuation). Honorific prefixes ("Mlle Hersch") therefore fall through to the
  general surname rules; whether ZBZ wants the honorific inside the element is an
  open modelling point.
- Single-token work titles need at least three characters to enter the lexicon at
  all, otherwise the worklist fills with noise.
- A surname taken from a cache or legacy variant enters the surname index only when
  it passes the same distinctiveness test the org-token rule states (at least four
  characters, capitalized). Curated headwords are registered unguarded, so the test
  only filters variant artifacts, the transliteration fragments lobid carries
  ("Ma, Kesi" for Marx, "Big, abbe" for Voltaire). Forename-shaped variants
  ("Pierre") pass it and stay as tier-2 noise for the judge stage.
"""

from __future__ import annotations

import html
import json
import re
from bisect import bisect_left, bisect_right
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

SENTINEL = "\x00"
CONTEXT_RADIUS = 40
MIN_TOKEN_LEN = 4
MIN_SHORT_TITLE_LEN = 3

TIER_BY_RULE = {
    "full-name": 1,
    "variant-full-name": 1,
    "initial-surname": 1,
    "anchored-surname": 1,
    "org-name": 1,
    "org-variant": 1,
    "org-token": 1,
    "work-title": 1,
    "work-variant": 1,
    "speaker": 1,
    "bare-surname": 2,
    "ambiguous-surname": 2,
    "short-title": 2,
    "crosses-markup": 2,
}

PLAIN_BIBL_SUFFIX = ":in-plain-bibl"
AMBIGUOUS_SUFFIX = ":ambiguous"

_CATEGORY_BY_LIST = {"persons": "person", "organisations": "organisation", "works": "work"}
_LABEL_FIELD = {"persons": "name", "organisations": "orgName", "works": "title"}
_LEGACY_KEY = {"persons": "persons", "organisations": "organizations", "works": "works"}

# Adjective derivations of a name are never candidates (Freudschen); longest first.
_ADJECTIVE_SUFFIXES = ("schem", "schen", "scher", "sches", "sche")

_TOKEN_RE = re.compile(r"<!--.*?-->|<\?.*?\?>|<![^>]*>|</?[A-Za-z][^>]*>", re.DOTALL)
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


# --- lexicon ----------------------------------------------------------------------


def build_lexicon(
    entities_path: Path | str,
    cache_path: Path | str,
    legacy_path: Path | str | None = None,
) -> dict:
    """Build the matching lexicon from list, GND cache and legacy mention index.

    The list is a trust boundary and must exist; cache and legacy index are optional
    and simply contribute fewer name forms when missing. The returned dict carries
    `entries` (gid -> record), `forms` (form string -> owners), `by_first_word`
    (first word -> forms, longest first), `surnames` (surname -> gids), `skipped`
    (counters) and `sources` (provenance).
    """
    entities = _read_json(entities_path, required=True) or {}
    cache = _read_json(cache_path) or {}
    cache_entries = cache.get("entries", {}) if isinstance(cache, dict) else {}
    legacy_names = _legacy_names(_read_json(legacy_path)) if legacy_path else {}

    forms: dict[str, list[tuple[str, str, str]]] = {}
    surnames: dict[str, set[str]] = {}
    entries: dict[str, dict] = {}
    skipped = {"no_label": 0, "gnd_404": 0, "short_org_token": 0, "duplicate_gid": 0}

    for list_key, category in _CATEGORY_BY_LIST.items():
        for raw in entities.get(list_key, []) or []:
            gid = str(raw.get("GND_id") or "").strip()
            label = _collapse(str(raw.get(_LABEL_FIELD[list_key]) or ""))
            if not gid or not label:
                skipped["no_label"] += 1
                continue
            cached = cache_entries.get(gid) or cache_entries.get(_normalize_gid(gid)) or {}
            if cached.get("http_status") == 404:
                skipped["gnd_404"] += 1
                continue
            if gid in entries:
                skipped["duplicate_gid"] += 1
                continue
            entries[gid] = {
                "gid": gid,
                "category": category,
                "label": label,
                "author_gnd_id": str(raw.get("author_gnd_id") or "") or None,
            }
            variants = _variants(cached, legacy_names.get(_normalize_gid(gid), ()))
            if category == "person":
                _add_person(forms, surnames, gid, label, variants)
            elif category == "organisation":
                _add_org(forms, gid, label, variants, skipped)
            else:
                _add_work(forms, gid, label, variants)

    by_first_word: dict[str, list[str]] = {}
    for form in forms:
        by_first_word.setdefault(_first_word(form), []).append(form)
    for bucket in by_first_word.values():
        bucket.sort(key=lambda form: (-len(form), form))

    return {
        "entries": entries,
        "forms": {form: tuple(sorted(owners)) for form, owners in forms.items()},
        "by_first_word": {word: tuple(bucket) for word, bucket in by_first_word.items()},
        "surnames": {name: tuple(sorted(gids)) for name, gids in surnames.items()},
        "skipped": skipped,
        "sources": {
            "entities": str(entities_path),
            "cache": str(cache_path),
            "legacy": str(legacy_path) if legacy_path else None,
            "cache_retrieved": cache.get("retrieved") if isinstance(cache, dict) else None,
        },
    }


def _read_json(path: Path | str | None, required: bool = False) -> dict | None:
    if path is None:
        return None
    file_path = Path(path)
    if not file_path.exists():
        if required:
            raise FileNotFoundError(f"entity list not found: {file_path}")
        return None
    return json.loads(file_path.read_text(encoding="utf-8"))


def _legacy_names(legacy: dict | None) -> dict[str, tuple[str, ...]]:
    """Invert the legacy index into normalized gid -> name forms."""
    if not legacy:
        return {}
    out: dict[str, list[str]] = {}
    for legacy_key in _LEGACY_KEY.values():
        for raw_gid, payload in (legacy.get(legacy_key) or {}).items():
            names = payload.get("names") if isinstance(payload, dict) else None
            if not names:
                continue
            out.setdefault(_normalize_gid(str(raw_gid)), []).extend(str(n) for n in names)
    return {gid: tuple(names) for gid, names in out.items()}


def _variants(cached: dict, legacy: tuple[str, ...]) -> tuple[str, ...]:
    """Name forms beyond the headword, deduplicated and whitespace-normalized."""
    raw = [cached.get("preferred_name"), *(cached.get("variant_names") or []), *legacy]
    seen: dict[str, None] = {}
    for value in raw:
        form = _collapse(str(value or ""))
        if form:
            seen.setdefault(form, None)
    return tuple(seen)


def _normalize_gid(gid: str) -> str:
    """Drop the GND check character so the legacy index (without it) joins."""
    return gid.split("-", 1)[0].strip()


def _add_form(
    forms: dict[str, list[tuple[str, str, str]]],
    form: str,
    gid: str,
    category: str,
    rule: str,
) -> None:
    form = _collapse(form)
    if not form or not _first_word(form):
        return
    owners = forms.setdefault(form, [])
    if any(owner[0] == gid for owner in owners):
        return
    owners.append((gid, category, rule))


def _split_person_label(label: str) -> tuple[str, str]:
    """Split a headword into (surname, forenames); inverted form wins."""
    if "," in label:
        surname, _, forenames = label.partition(",")
        return surname.strip(), _collapse(forenames)
    tokens = label.split()
    if len(tokens) == 1:
        return tokens[0], ""
    return tokens[-1], " ".join(tokens[:-1])


def _add_person(
    forms: dict[str, list[tuple[str, str, str]]],
    surnames: dict[str, set[str]],
    gid: str,
    label: str,
    variants: tuple[str, ...],
) -> None:
    surname, forenames = _split_person_label(label)
    if surname:
        surnames.setdefault(surname, set()).add(gid)
    if surname and forenames:
        _add_form(forms, f"{forenames} {surname}", gid, "person", "full-name")
        _add_form(forms, label, gid, "person", "full-name")
        initial = forenames[0]
        if initial.isalpha():
            _add_form(forms, f"{initial}. {surname}", gid, "person", "initial-surname")
    for variant in variants:
        _add_person_variant(forms, surnames, gid, variant)


def _add_person_variant(
    forms: dict[str, list[tuple[str, str, str]]],
    surnames: dict[str, set[str]],
    gid: str,
    variant: str,
) -> None:
    if "," in variant:
        surname, forenames = _split_person_label(variant)
        if _is_distinctive_token(surname):
            surnames.setdefault(surname, set()).add(gid)
        if surname and forenames:
            _add_form(forms, f"{forenames} {surname}", gid, "person", "variant-full-name")
            _add_form(forms, variant, gid, "person", "variant-full-name")
        return
    tokens = variant.split()
    if len(tokens) >= 2:
        _add_form(forms, variant, gid, "person", "variant-full-name")
    elif tokens and _is_distinctive_token(tokens[0]):
        surnames.setdefault(tokens[0], set()).add(gid)


def _add_org(
    forms: dict[str, list[tuple[str, str, str]]],
    gid: str,
    label: str,
    variants: tuple[str, ...],
    skipped: dict[str, int],
) -> None:
    for index, form in enumerate((label, *variants)):
        rule = "org-name" if index == 0 else "org-variant"
        tokens = form.split()
        if len(tokens) >= 2:
            _add_form(forms, form, gid, "organisation", rule)
        elif tokens and _is_distinctive_token(tokens[0]):
            _add_form(forms, tokens[0], gid, "organisation", "org-token")
        else:
            skipped["short_org_token"] += 1


def _is_distinctive_token(token: str) -> bool:
    """One-token names carry a mention only when long enough and capitalized."""
    return len(token) >= MIN_TOKEN_LEN and (token[0].isupper() or token.isupper())


def _add_work(
    forms: dict[str, list[tuple[str, str, str]]],
    gid: str,
    label: str,
    variants: tuple[str, ...],
) -> None:
    for index, form in enumerate((label, *variants)):
        rule = "work-title" if index == 0 else "work-variant"
        tokens = form.split()
        if len(tokens) >= 2:
            _add_form(forms, form, gid, "work", rule)
        elif tokens and len(tokens[0]) >= MIN_SHORT_TITLE_LEN:
            _add_form(forms, tokens[0], gid, "work", "short-title")


# --- zones ------------------------------------------------------------------------


def _scan_zones(xml: str) -> _Zones:
    """Collect the content ranges of text, excluded zones, plain bibl and speaker."""
    text: list[Span] = []
    excluded: list[Span] = []
    plain_bibl: list[Span] = []
    speakers: list[Span] = []
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
                text, excluded, plain_bibl, speakers,
            )
            continue
        if token.endswith("/>"):
            continue
        attrs = _parse_attrs(token) if name in _TRACKED_TAGS else {}
        stack.append((name, attrs, match.end()))

    return _Zones(
        text=_merge(text),
        excluded=_merge(excluded),
        plain_bibl=_merge(plain_bibl),
        speakers=tuple(sorted(speakers)),
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
) -> None:
    if start > end:
        return
    if name == "text":
        text.append((start, end))
    elif name in ("figure", "persName", "orgName"):
        excluded.append((start, end))
    elif name == "div" and attrs.get("type") == "bibliography":
        excluded.append((start, end))
    elif name == "bibl":
        (excluded if attrs.get("ref") else plain_bibl).append((start, end))
    elif name == "speaker":
        speakers.append((start, end))


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


def find_candidates(xml_string: str, lexicon: dict) -> list[dict]:
    """Report entity mention candidates as raw character spans of `xml_string`."""
    if "by_first_word" not in lexicon or "surnames" not in lexicon:
        raise ValueError("lexicon must be the return value of build_lexicon()")
    zones = _scan_zones(xml_string)
    norm = _normalize(xml_string, zones)
    speaker_hits = _speaker_hits(norm, zones, lexicon)
    # Anchors count document-wide (operator decision 2026-08-12): the first pass
    # collects the tier-1 person gids, the second applies them everywhere, so a
    # bare surname BEFORE the first full-name mention anchors as well.
    first_pass = _scan(xml_string, norm, zones, lexicon, speaker_hits)
    anchors = {c["gid"] for c in first_pass if c["tier"] == 1 and c["category"] == "person"}
    if not anchors:
        return first_pass
    return _scan(xml_string, norm, zones, lexicon, speaker_hits, anchors)


def _scan(
    xml: str,
    norm: _Norm,
    zones: _Zones,
    lexicon: dict,
    speaker_hits: dict[int, tuple],
    seed_anchors: set[str] | None = None,
) -> list[dict]:
    """Left-to-right pass; `seed_anchors` carries the document-wide tier-1 anchors."""
    text = norm.text
    out: list[dict] = []
    anchored: set[str] = set(seed_anchors or ())
    pos = 0
    while pos < len(text):
        if not _is_word(text[pos]) or (pos > 0 and _is_word(text[pos - 1])):
            pos += 1
            continue
        hit = speaker_hits.get(pos) or _match_at(text, pos, lexicon, anchored)
        if hit is None:
            pos = _word_end(text, pos)
            continue
        candidate, resume = _build_candidate(xml, norm, zones, hit)
        if candidate is not None:
            out.append(candidate)
            if candidate["tier"] == 1:
                anchored.add(candidate["gid"])
        pos = max(resume, pos + 1)
    return out


def _match_at(text: str, pos: int, lexicon: dict, anchored: set[str]) -> tuple | None:
    """Longest lexicon form at `pos`, else the surname fallback."""
    word = text[pos:_word_end(text, pos)]
    for form in lexicon["by_first_word"].get(word, ()):
        end = _try_form(text, pos, form)
        if end is None:
            continue
        owners = lexicon["forms"][form]
        gid, category, rule = owners[0]
        if len(owners) > 1:
            return (pos, end, gid, category, rule + AMBIGUOUS_SUFFIX, 2)
        return (pos, end, gid, category, rule, TIER_BY_RULE[rule])
    return _surname_at(text, pos, word, lexicon, anchored)


def _try_form(text: str, pos: int, form: str) -> int | None:
    end = pos + len(form)
    if text[pos:end] != form:
        return None
    if not _is_word(form[-1]):
        return end
    return _extend_or_reject(text, end)


def _extend_or_reject(text: str, end: int) -> int | None:
    """Apply the word-boundary, genitive and adjective rules behind a match."""
    for suffix in _ADJECTIVE_SUFFIXES:
        after = end + len(suffix)
        if text.startswith(suffix, end) and not _is_word_at(text, after):
            return None
    if text.startswith("s", end):
        return end + 1 if not _is_word_at(text, end + 1) else None
    return None if _is_word_at(text, end) else end


def _surname_at(
    text: str,
    pos: int,
    word: str,
    lexicon: dict,
    anchored: set[str],
) -> tuple | None:
    surnames = lexicon["surnames"]
    if word in surnames:
        key = word
    elif word.endswith("s") and word[:-1] in surnames:
        key = word[:-1]
    else:
        return None
    end = pos + len(word)
    gids = surnames[key]
    in_document = [gid for gid in gids if gid in anchored]
    if len(in_document) == 1:
        return (pos, end, in_document[0], "person", "anchored-surname", 1)
    if len(in_document) > 1:
        return (pos, end, in_document[0], "person", "ambiguous-surname", 2)
    return (pos, end, gids[0], "person", "bare-surname", 2)


def _speaker_hits(norm: _Norm, zones: _Zones, lexicon: dict) -> dict[int, tuple]:
    """Speaker slots whose verbatim text is a full name or a known surname."""
    hits: dict[int, tuple] = {}
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
        persons = [owner for owner in lexicon["forms"].get(label, ()) if owner[1] == "person"]
        if persons:
            hits[start] = (start, end, persons[0][0], "person", "speaker", _tier(len(persons)))
            continue
        gids = lexicon["surnames"].get(label)
        if gids:
            hits[start] = (start, end, gids[0], "person", "speaker", _tier(len(gids)))
    return hits


def _tier(owner_count: int) -> int:
    return 1 if owner_count == 1 else 2


def _build_candidate(
    xml: str,
    norm: _Norm,
    zones: _Zones,
    hit: tuple,
) -> tuple[dict | None, int]:
    """Map a normalized hit back to raw offsets and apply the zone downgrades."""
    n_start, n_end, gid, category, rule, tier = hit
    raw_start = norm.starts[n_start]
    raw_end = norm.ends[n_end - 1]
    surface = xml[raw_start:raw_end]
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
        "gid": gid,
        "category": category,
        "surface": surface,
        "start": raw_start,
        "end": raw_end,
        "tier": tier,
        "rule": rule,
        "context": _context(norm.text, n_start, n_end),
    }
    return candidate, max(bisect_right(norm.ends, raw_end), n_start + 1)


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


# --- small text helpers -----------------------------------------------------------


def _collapse(value: str) -> str:
    return " ".join(value.split())


def _first_word(form: str) -> str:
    """Leading run of word characters; empty when the form cannot be reached by the scan."""
    return form[:_word_end(form, 0)]


def _word_end(text: str, pos: int) -> int:
    end = pos
    while end < len(text) and _is_word(text[end]):
        end += 1
    return end


def _is_word(char: str) -> bool:
    return char.isalnum()


def _is_word_at(text: str, pos: int) -> bool:
    return pos < len(text) and _is_word(text[pos])
