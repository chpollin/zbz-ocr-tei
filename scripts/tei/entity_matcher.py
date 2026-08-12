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

    find_candidates(xml_string, lexicon, author_labels=()) -> list[dict]
        Reports mentions as raw character spans of the input string. Every candidate
        carries gid, category, surface, start, end, tier, rule, context.
        Hard invariants: xml_string[start:end] == surface, candidates sorted by
        start and free of overlap, spans only inside <text>, and the surface carries
        no markup other than <lb/> tags. `author_labels` holds the labels of the
        document's own author (Masterfile metadata); all-caps hits on that entity are
        skipped, because bylines, running headers and signatures stay unmarked.

Search model. The scan runs on a normalized projection of the raw string: markup
contributes nothing, `<lb break="no"/>` joins a broken word, a plain `<lb/>` counts
as one space, whitespace collapses to a single space, and character references are
decoded. Every normalized character keeps the raw offsets it came from, so a match
maps back to an exact byte span whose slice is the surface. Excluded zones emit a
sentinel character instead of their text, which blocks any match from running across
them. The apparatus zone (E-Periodica cover sheet, photo credit lines) is excluded
as well, so library apparatus never carries entity markup.

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
- Variants made only of dotted initials ("J. H." for Pestalozzi) never enter the
  full-name channel; as tier-1 forms they would claim unrelated initials
  document-wide (the doc-1220 pilot finding). Such mentions stay tier 3.
- A legacy surface form that its bearer's own record does not corroborate stays a
  candidate source but reaches only tier 2, with the rule "legacy-form", and never
  enters the surname index. The legacy index was harvested from the gold references,
  so its uncorroborated pairings would both leak gold into tier 1 and carry the
  known poisoning ("Jérémie" filed under Jaspers). Corroboration is the shared
  predicate `legacy_form_is_covered`, which `entity_lint` reports as warnings.
- A bare or anchored surname drops to tier 2 with the rule suffix ":suspect" on any
  homograph signal: a lowercase twin of the word in the same document, membership in
  FUNCTION_WORDS, an adjacent hyphen, or an adjacent unknown capitalized word. The
  last signal is noisy in German, where every noun is capitalized; it is suppressed
  behind a genitive surface ("Herschs Werk"), before a sentence-initial word and
  behind an honorific ("Mlle Hersch", HONORIFICS).
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
"""

from __future__ import annotations

import html
import json
import re
import unicodedata
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
    "caps-full-name": 1,
    "org-name": 1,
    "org-variant": 1,
    "org-token": 1,
    "work-title": 1,
    "work-variant": 1,
    "speaker": 1,
    "bare-surname": 2,
    "ambiguous-surname": 2,
    "caps-surname": 2,
    "short-title": 2,
    "crosses-markup": 2,
    "legacy-form": 2,
    "adjective-form": 2,
}

PLAIN_BIBL_SUFFIX = ":in-plain-bibl"
AMBIGUOUS_SUFFIX = ":ambiguous"
SUSPECT_SUFFIX = ":suspect"

# Surnames that are also ordinary German words. Only collisions attested in the
# corpus belong here ("weil" the conjunction, "Wahl" the election); the list grows
# with the corpus scan, never by guessing.
FUNCTION_WORDS = frozenset({"weil", "wahl"})

# The corpus is the author's own estate, so her label is the default byline
# exception for caps matching. Upgrade path: per-document author from the Masterfile
# once documents by other authors enter the corpus.
CORPUS_AUTHOR_LABELS = ("Hersch, Jeanne",)

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

_CATEGORY_BY_LIST = {"persons": "person", "organisations": "organisation", "works": "work"}
_LABEL_FIELD = {"persons": "name", "organisations": "orgName", "works": "title"}
_LEGACY_KEY = {"persons": "persons", "organisations": "organizations", "works": "works"}

# Adjective derivations of a name (Freudschen, freudien, nietzschiano); longest
# first, so the longer ending wins over its own prefix.
_ADJECTIVE_SUFFIXES = (
    "iennes", "ienne", "schem", "schen", "scher", "sches",
    "iens", "iano", "iana", "iani", "iane", "sche", "ien", "ian",
)

_TOKEN_RE = re.compile(r"<!--.*?-->|<\?.*?\?>|<![^>]*>|</?[A-Za-z][^>]*>", re.DOTALL)
_PB_RE = re.compile(r"<pb\b[^>]*/?>", re.DOTALL)
_WORD_RUN_RE = re.compile(r"\w+")
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
    (first word -> forms, longest first), `surnames` (surname -> gids), the three
    all-caps indexes `caps_forms` / `caps_by_first_word` / `caps_surnames`,
    `legacy_demoted` (the (gid, form) pairs the bearer's record does not corroborate),
    `skipped` (counters) and `sources` (provenance).
    """
    entities = _read_json(entities_path, required=True) or {}
    cache = _read_json(cache_path) or {}
    cache_entries = cache.get("entries", {}) if isinstance(cache, dict) else {}
    legacy_index = legacy_names(_read_json(legacy_path)) if legacy_path else {}

    forms: dict[str, list[tuple[str, str, str]]] = {}
    surnames: dict[str, set[str]] = {}
    entries: dict[str, dict] = {}
    legacy_demoted: list[tuple[str, str]] = []
    skipped = {"no_label": 0, "gnd_404": 0, "short_org_token": 0, "duplicate_gid": 0}

    for list_key, category in _CATEGORY_BY_LIST.items():
        for raw in entities.get(list_key, []) or []:
            gid = str(raw.get("GND_id") or "").strip()
            label = _collapse(str(raw.get(_LABEL_FIELD[list_key]) or ""))
            if not gid or not label:
                skipped["no_label"] += 1
                continue
            cached = cache_entries.get(gid) or cache_entries.get(normalize_gid(gid)) or {}
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
            legacy = legacy_index.get(normalize_gid(gid), ())
            corroborated, demoted = _split_legacy(legacy, label, cached)
            variants = _variants(cached, corroborated)
            if category == "person":
                _add_person(forms, surnames, gid, label, variants)
            elif category == "organisation":
                _add_org(forms, gid, label, variants, skipped)
            else:
                _add_work(forms, gid, label, variants)
            for form in demoted:
                legacy_demoted.append((gid, form))
                _add_legacy_form(forms, gid, category, form)

    caps_forms = _caps_index(forms)
    return {
        "entries": entries,
        "forms": {form: tuple(sorted(owners)) for form, owners in forms.items()},
        "by_first_word": _first_word_index(forms),
        "surnames": {name: tuple(sorted(gids)) for name, gids in surnames.items()},
        "caps_forms": {form: tuple(sorted(owners)) for form, owners in caps_forms.items()},
        "caps_by_first_word": _first_word_index(caps_forms),
        "caps_surnames": _caps_surnames(surnames),
        "legacy_demoted": tuple(legacy_demoted),
        "skipped": skipped,
        "sources": {
            "entities": str(entities_path),
            "cache": str(cache_path),
            "legacy": str(legacy_path) if legacy_path else None,
            "cache_retrieved": cache.get("retrieved") if isinstance(cache, dict) else None,
        },
    }


def _first_word_index(forms: dict[str, list]) -> dict[str, tuple[str, ...]]:
    """First word -> the forms starting with it, longest first (the scan tries in order)."""
    buckets: dict[str, list[str]] = {}
    for form in forms:
        buckets.setdefault(_first_word(form), []).append(form)
    return {
        word: tuple(sorted(bucket, key=lambda form: (-len(form), form)))
        for word, bucket in buckets.items()
    }


def _caps_index(forms: dict[str, list[tuple[str, str, str]]]) -> dict[str, list]:
    """All-caps projection of the person full names (at least two tokens)."""
    caps: dict[str, list[tuple[str, str, str]]] = {}
    for form, owners in forms.items():
        upper = form.upper()
        if len(upper) != len(form) or len(form.split()) < 2:
            continue
        for gid, category, rule in owners:
            if category == "person" and rule in ("full-name", "variant-full-name"):
                _add_form(caps, upper, gid, category, "caps-full-name")
    return caps


def _caps_surnames(surnames: dict[str, set[str]]) -> dict[str, tuple[str, ...]]:
    caps: dict[str, set[str]] = {}
    for surname, gids in surnames.items():
        upper = surname.upper()
        if len(upper) == len(surname) and len(upper) > 1:
            caps.setdefault(upper, set()).update(gids)
    return {name: tuple(sorted(gids)) for name, gids in caps.items()}


def _read_json(path: Path | str | None, required: bool = False) -> dict | None:
    if path is None:
        return None
    file_path = Path(path)
    if not file_path.exists():
        if required:
            raise FileNotFoundError(f"entity list not found: {file_path}")
        return None
    return json.loads(file_path.read_text(encoding="utf-8"))


def legacy_names(legacy: dict | None) -> dict[str, tuple[str, ...]]:
    """Invert the legacy index into normalized gid -> name forms."""
    if not legacy:
        return {}
    out: dict[str, list[str]] = {}
    for legacy_key in _LEGACY_KEY.values():
        for raw_gid, payload in (legacy.get(legacy_key) or {}).items():
            names = payload.get("names") if isinstance(payload, dict) else None
            if not names:
                continue
            out.setdefault(normalize_gid(str(raw_gid)), []).extend(str(n) for n in names)
    return {gid: tuple(names) for gid, names in out.items()}


def _dedup(values) -> tuple[str, ...]:
    """Whitespace-normalized, order-preserving deduplication; empty forms drop out."""
    seen: dict[str, None] = {}
    for value in values:
        form = _collapse(str(value or ""))
        if form:
            seen.setdefault(form, None)
    return tuple(seen)


def _variants(cached: dict, extra: tuple[str, ...] = ()) -> tuple[str, ...]:
    """Name forms beyond the headword, deduplicated and whitespace-normalized."""
    return _dedup([cached.get("preferred_name"), *(cached.get("variant_names") or []), *extra])


def normalize_gid(gid: str) -> str:
    """Drop the GND check character so the legacy index (without it) joins."""
    return gid.split("-", 1)[0].strip()


def _fold(text: str) -> str:
    """Comparison form: diacritics removed, whitespace collapsed, case folded."""
    decomposed = unicodedata.normalize("NFKD", text)
    stripped = "".join(char for char in decomposed if not unicodedata.combining(char))
    return " ".join(stripped.split()).casefold()


def _fold_tokens(text: str) -> frozenset[str]:
    return frozenset(_WORD_RUN_RE.findall(_fold(text)))


def legacy_form_is_covered(form: str, label: str, cached: dict | None) -> bool:
    """True when the bearer's own record corroborates a legacy surface form.

    Corroboration means the folded form is a substring of the list label, the GND
    preferred name or one of its variants, or that its name tokens are a subset of
    one of those; the token test carries the reordered and all-caps forms the legacy
    index harvested from the references ("JASPERS Karl" for "Jaspers, Karl").
    Uncorroborated pairings are the poisoning class ("Jérémie" under Jaspers).
    """
    key = _fold(form)
    if not key:
        return True
    tokens = _fold_tokens(form)
    references = [label]
    if cached:
        references.append(str(cached.get("preferred_name") or ""))
        references.extend(str(value) for value in (cached.get("variant_names") or []))
    for reference in references:
        if not reference:
            continue
        if key in _fold(reference) or tokens <= _fold_tokens(reference):
            return True
    return False


def _split_legacy(
    legacy: tuple[str, ...],
    label: str,
    cached: dict,
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Split the legacy forms of one entity into corroborated and demoted ones."""
    corroborated, demoted = [], []
    for form in _dedup(legacy):
        target = corroborated if legacy_form_is_covered(form, label, cached) else demoted
        target.append(form)
    return tuple(corroborated), tuple(demoted)


def _add_legacy_form(
    forms: dict[str, list[tuple[str, str, str]]],
    gid: str,
    category: str,
    form: str,
) -> None:
    """Register a demoted legacy form: tier-2 candidate source, never a surname."""
    tokens = form.split()
    if len(tokens) == 1 and not _is_distinctive_token(tokens[0]):
        return
    _add_form(forms, form, gid, category, "legacy-form")


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
        if _is_distinctive_token(surname) and not _is_initials_only(surname):
            surnames.setdefault(surname, set()).add(gid)
        if surname and forenames and not _is_initials_only(f"{forenames} {surname}"):
            _add_form(forms, f"{forenames} {surname}", gid, "person", "variant-full-name")
            _add_form(forms, variant, gid, "person", "variant-full-name")
        return
    tokens = variant.split()
    if _is_initials_only(variant):
        return
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


_INITIAL_TOKEN_RE = re.compile(r"[^\W\d_]{1,2}\.|[^\W\d_]")


def _is_initials_only(form: str) -> bool:
    """True for forms made only of dotted initials or bare single letters.

    lobid carries such variants ("J. H." for Pestalozzi, "B. P." for Pascal); as
    full-name forms they would mislabel unrelated initials document-wide. Dotless
    two-letter words ("Mo Ti") are real transliterated name forms and stay.
    """
    tokens = form.replace(".", ". ").split()
    return bool(tokens) and all(_INITIAL_TOKEN_RE.fullmatch(t) for t in tokens)


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
    paragraphs: list[Span] = []
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
                text, excluded, plain_bibl, speakers, paragraphs,
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
    elif name == "p":
        paragraphs.append((start, end))


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
    author_labels: tuple[str, ...] = (),
) -> list[dict]:
    """Report entity mention candidates as raw character spans of `xml_string`."""
    if any(key not in lexicon for key in ("by_first_word", "surnames", "caps_by_first_word")):
        raise ValueError("lexicon must be the return value of build_lexicon()")
    zones = _scan_zones(xml_string)
    norm = _normalize(xml_string, zones)
    speaker_hits = _speaker_hits(norm, zones, lexicon)
    lowercase_words = _lowercase_words(norm.text)
    author_gids = _author_gids(lexicon, author_labels)
    # Anchors count document-wide (operator decision 2026-08-12): the first pass
    # collects the tier-1 person gids, the second applies them everywhere, so a
    # bare surname BEFORE the first full-name mention anchors as well.
    first_pass = _scan(xml_string, norm, zones, lexicon, speaker_hits,
                       lowercase_words=lowercase_words, author_gids=author_gids)
    anchors = {c["gid"] for c in first_pass if c["tier"] == 1 and c["category"] == "person"}
    if not anchors:
        return first_pass
    return _scan(xml_string, norm, zones, lexicon, speaker_hits, anchors,
                 lowercase_words, author_gids)


def _lowercase_words(text: str) -> frozenset[str]:
    """Folded words the document writes in lower case (homograph signal a)."""
    return frozenset(
        word.casefold() for word in _WORD_RUN_RE.findall(text) if word[:1].islower()
    )


def _author_gids(lexicon: dict, author_labels: tuple[str, ...]) -> frozenset[str]:
    """Listed entities that are the document's own author, matched by name tokens."""
    keys = {_fold_tokens(label) for label in author_labels if _fold_tokens(label)}
    if not keys:
        return frozenset()
    return frozenset(
        gid for gid, entry in lexicon["entries"].items()
        if _fold_tokens(entry["label"]) in keys
    )


def _scan(
    xml: str,
    norm: _Norm,
    zones: _Zones,
    lexicon: dict,
    speaker_hits: dict[int, tuple],
    seed_anchors: set[str] | None = None,
    lowercase_words: frozenset[str] = frozenset(),
    author_gids: frozenset[str] = frozenset(),
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
        if hit[4].startswith("caps-") and hit[2] in author_gids:
            pos = max(hit[1], pos + 1)
            continue
        if hit[4] in _SUSPECT_RULES and _is_suspect(xml, norm, hit, lexicon, lowercase_words):
            hit = (*hit[:4], hit[4] + SUSPECT_SUFFIX, 2)
        candidate, resume = _build_candidate(xml, norm, zones, hit)
        if candidate is not None:
            out.append(candidate)
            if candidate["tier"] == 1:
                anchored.add(candidate["gid"])
        pos = max(resume, pos + 1)
    return out


# --- homograph suspicion ----------------------------------------------------------


def _is_suspect(
    xml: str,
    norm: _Norm,
    hit: tuple,
    lexicon: dict,
    lowercase_words: frozenset[str],
) -> bool:
    """Deterministic signals that a surname hit is a homograph, not a mention."""
    n_start, n_end = hit[0], hit[1]
    text = norm.text
    word = text[n_start:n_end]
    folded = word.casefold()
    if folded in lowercase_words or folded in FUNCTION_WORDS:
        return True
    raw_start, raw_end = norm.starts[n_start], norm.ends[n_end - 1]
    if xml[max(raw_start - 1, 0):raw_start] == "-" or xml[raw_end:raw_end + 1] == "-":
        return True
    if _unknown_capital_before(text, n_start, lexicon):
        return True
    # A genitive name is followed by its head noun, and German capitalizes every
    # noun, so the trailing signal would fire on every correct genitive mention.
    genitive = word.endswith("s") and word[:-1] in lexicon["surnames"]
    return not genitive and _unknown_capital_after(text, n_end, lexicon)


def _unknown_capital_before(text: str, pos: int, lexicon: dict) -> bool:
    if pos == 0 or text[pos - 1] != " ":
        return False
    end = pos - 1
    start = end
    while start > 0 and _is_word(text[start - 1]):
        start -= 1
    if start == end or _starts_sentence(text, start):
        return False
    word = text[start:end]
    return word.casefold() not in HONORIFICS and _is_unknown_capital(word, lexicon)


def _unknown_capital_after(text: str, pos: int, lexicon: dict) -> bool:
    if text[pos:pos + 1] != " ":
        return False
    start = pos + 1
    end = _word_end(text, start)
    return start < end and _is_unknown_capital(text[start:end], lexicon)


def _starts_sentence(text: str, pos: int) -> bool:
    """True when the word at `pos` is capitalized by position, not by being a name."""
    index = pos - 1
    while index >= 0 and text[index] == " ":
        index -= 1
    return index < 0 or text[index] in _SENTENCE_END


def _is_unknown_capital(word: str, lexicon: dict) -> bool:
    if not word[:1].isupper():
        return False
    return not any(
        word in lexicon[index]
        for index in ("by_first_word", "surnames", "caps_by_first_word", "caps_surnames")
    )


def _match_at(text: str, pos: int, lexicon: dict, anchored: set[str]) -> tuple | None:
    """Longest lexicon form at `pos`, then the caps forms, else the surname fallback."""
    word = text[pos:_word_end(text, pos)]
    for form in lexicon["by_first_word"].get(word, ()):
        result = _try_form(text, pos, form)
        if result is None:
            continue
        end, kind = result
        owners = lexicon["forms"][form]
        gid, category, rule = owners[0]
        if kind == "adjective":
            return (pos, end, gid, category, "adjective-form", 2)
        if len(owners) > 1 or _shadows_a_surname(form, owners, lexicon):
            return (pos, end, gid, category, rule + AMBIGUOUS_SUFFIX, 2)
        return (pos, end, gid, category, rule, TIER_BY_RULE[rule])
    caps = _caps_at(text, pos, word, lexicon)
    if caps is not None:
        return caps
    return _surname_at(text, pos, word, lexicon, anchored)


def _shadows_a_surname(form: str, owners: tuple, lexicon: dict) -> bool:
    """True when a form (a one-word title such as "Nietzsche") is also a listed surname.

    Reporting only the form hit would hide the person reading, so the candidate goes
    to the judge stage with the AMBIGUOUS suffix; both readings stay reconstructible
    from `forms` and `surnames`.
    """
    shadowed = lexicon["surnames"].get(form, ())
    known = {owner[0] for owner in owners}
    return any(gid not in known for gid in shadowed)


def _try_form(text: str, pos: int, form: str) -> tuple[int, str] | None:
    end = pos + len(form)
    if text[pos:end] != form:
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


def _caps_at(text: str, pos: int, word: str, lexicon: dict) -> tuple | None:
    """All-caps full name of a person; the caps index holds the uppercased forms."""
    if len(word) < 2 or not word.isupper():
        return None
    for form in lexicon["caps_by_first_word"].get(word, ()):
        end = pos + len(form)
        if text[pos:end] != form or _is_word_at(text, end):
            continue
        owners = lexicon["caps_forms"][form]
        gid, category, rule = owners[0]
        if len(owners) > 1:
            return (pos, end, gid, category, rule + AMBIGUOUS_SUFFIX, 2)
        return (pos, end, gid, category, rule, TIER_BY_RULE[rule])
    return None


def _surname_at(
    text: str,
    pos: int,
    word: str,
    lexicon: dict,
    anchored: set[str],
) -> tuple | None:
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
    if len(in_document) == 1:
        return (pos, end, in_document[0], "person", "anchored-surname", 1)
    if len(in_document) > 1:
        return (pos, end, in_document[0], "person", "ambiguous-surname", 2)
    return (pos, end, gids[0], "person", "bare-surname", 2)


def _derived_surname_at(text: str, pos: int, word: str, lexicon: dict) -> tuple | None:
    """Adjective derivation or all-caps writing of a listed surname; both tier 2."""
    end = pos + len(word)
    stem = _adjective_stem(word, lexicon["surnames"])
    if stem is not None:
        return (pos, end, lexicon["surnames"][stem][0], "person", "adjective-form", 2)
    if len(word) > 1 and word.isupper():
        gids = lexicon["caps_surnames"].get(word)
        if gids:
            return (pos, end, gids[0], "person", "caps-surname", 2)
    return None


def _adjective_stem(word: str, surnames: dict[str, tuple[str, ...]]) -> str | None:
    for suffix in _ADJECTIVE_SUFFIXES:
        if len(word) > len(suffix) and word.endswith(suffix) and word[:-len(suffix)] in surnames:
            return word[:-len(suffix)]
    return None


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
