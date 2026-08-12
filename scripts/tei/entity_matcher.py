"""Deterministic entity candidate search on delivered TEI-XML (analysis only).

Design plan and rule catalogue: knowledge/entity-integration.md (sections "Target
model" and "Matching method"). This module has no write path and never calls a
language model; ids always come from the curated list.

Two public functions:

    build_lexicon(entities_path, cache_path, legacy_path=None, review_path=None) -> dict
        Merges the curated list `data/entities/all_entities.json`, the lobid cache
        `data/entities/gnd_cache.json` (name variants, optional) and the legacy
        mention index `data/entities/legacy_mentions.json` (optional) into one
        lexicon. Entries without a label are skipped, so are entries whose cache
        answer is 404 (defective GND id).

    find_candidates(xml_string, lexicon, author_labels=()) -> list[dict]
        Reports mentions as raw character spans of the input string. Every candidate
        carries gid, category, surface, start, end, tier, rule, alternatives,
        matched_form, form_source, context; one-word work titles additionally carry
        evidence. Hard invariants: xml_string[start:end] == surface, candidates sorted
        by start and free of overlap, spans only inside <text>, and the surface carries
        no markup other than <lb/> tags. `author_labels` holds the labels of the
        document's own author (Masterfile metadata); all-caps and case-deviating hits
        on that entity are skipped, because bylines, running headers and signatures
        stay unmarked.

        alternatives   every listed id the matched form or surname belongs to, sorted
                       and including the reported gid. Empty for an unambiguous
                       candidate, so a filled list always means "undecided" and never
                       lets a single bearer read as the found entity. Length is never
                       one.
        matched_form   the lexicon form that produced the hit. For a surname hit that
                       is the form which registered the surname ("Mayer, Gertrud"
                       behind a hit on "Mayer"), not the surname itself.
        form_source    which channel the form came from: "headword" (curated label and
                       everything derived from it), "cache-variant" (GND cache),
                       "legacy" (legacy mention index), "surname-index" (the bare
                       surname of a curated headword).
        evidence       one-word work titles only: "typographic" when the setting
                       corroborates the title reading, "none" otherwise (see below).

Search model. The scan runs on a normalized projection of the raw string: markup
contributes nothing, `<lb break="no"/>` joins a broken word, a plain `<lb/>` counts
as one space, whitespace collapses to a single space, and character references are
decoded. Every normalized character keeps the raw offsets it came from, so a match
maps back to an exact byte span whose slice is the surface. Excluded zones emit a
sentinel character instead of their text, which blocks any match from running across
them. The apparatus zone (E-Periodica cover sheet, photo credit lines) is excluded
as well, so library apparatus never carries entity markup. A superscript digit counts
as a separator rather than a word character, so a name that carries a footnote marker
("Nietzsche" with a superscript two) keeps the boundary it has in front of a comma.

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
  ":suspect" (a property of the context), then ":in-plain-bibl" (a property of the
  position).
- Four derived-form channels close the recall gaps of the facsimile-adjudicated
  evaluation. Each registers a further spelling of a form the entity already carries,
  and each is worklist-only: the suffix sits on the lexicon rule, which fixes the tier
  at 2 (`_form_tier`); the speaker rule ignores such forms; and a spelling the lexicon
  already reads at tier 1, a surname or a tier-1 base form, is left untouched.
    * ":acronym-case", an all-caps one-token organisation of at least MIN_ACRONYM_LEN
      letters also matches its capitalized spelling ("l'Unesco" beside "UNESCO");
    * ":qualifier-strip", a form with a trailing parenthetical qualifier also matches
      without it ("Le populaire (Zeitung, Paris)" as "Le populaire"). The head passes
      the distinctiveness test of the org-token rule, because the channel also produces
      ordinary German words ("Bund" out of a disambiguated organisation name);
    * ":place-adjective", a two-token organisation whose second token stands in
      PLACE_ADJECTIVES also matches the inverted German form ("Universitaet Genf"
      reached through "Genfer Universitaet"); the table is static and small, no
      morphology is generated;
    * ":initials", a person headword also matches its dotted initials ("K.J." and
      "K. J." for "Jaspers, Karl"), which is how interview transcripts label the
      speaker. Initials several persons share become a multi-owner candidate.
  The channels read the forms that were actually registered, so every earlier gate
  binds them as well; a cache form the variant review rejected has no derived form.
- Person labels without a forename (mononyms such as "Platon") reach no tier-1 rule;
  they enter the surname index and can only surface as tier 2.
- The speaker rule compares the slot text verbatim (after stripping surrounding
  punctuation). Honorific prefixes ("Mlle Hersch") therefore fall through to the
  general surname rules; whether ZBZ wants the honorific inside the element is an
  open modelling point.
- Single-token work titles need at least three characters to enter the lexicon at
  all, otherwise the worklist fills with noise. Every such candidate carries the
  typographic pre-sorting `evidence`: "typographic" when the span sits completely
  inside an `hi`, when quotation marks or guillemets enclose it directly, or when a
  possessive stands right in front of it (POSSESSIVES), else "none". Both stay tier 2
  and no class is dropped; the field is the measurement basis for that decision.
- A surname taken from a cache or legacy variant enters the surname index only when
  it passes the same distinctiveness test the org-token rule states (at least four
  characters, capitalized). Curated headwords are registered unguarded, so the test
  only filters variant artifacts, the transliteration fragments lobid carries
  ("Ma, Kesi" for Marx, "Big, abbe" for Voltaire). Forename-shaped variants
  ("Pierre") pass it and stay as tier-2 noise for the judge stage.
- Variants made only of dotted initials ("J. H." for Pestalozzi) never enter the
  full-name channel; as tier-1 forms they would claim unrelated initials
  document-wide (the doc-1220 pilot finding). The initials of a headword reach the
  worklist through the ":initials" channel and nothing beyond it.
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
    * all-caps person surfaces stay with the caps channel and its byline exception,
      and a case-deviating writing of the document author's own name is skipped like an
      all-caps one, the corpus setting bylines as "Jeanne HERSCH".
"""

from __future__ import annotations

import html
import json
import re
import unicodedata
from bisect import bisect_left, bisect_right
from collections.abc import Iterator
from dataclasses import dataclass, replace
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

# Derived-form channels. Each one registers a further spelling of a form the entity
# already carries; the suffix sits on the lexicon rule itself, which makes every such
# form tier 2 by construction (_form_tier), so no channel here can auto-mark.
ACRONYM_CASE_SUFFIX = ":acronym-case"
QUALIFIER_SUFFIX = ":qualifier-strip"
PLACE_ADJECTIVE_SUFFIX = ":place-adjective"
INITIALS_SUFFIX = ":initials"

MIN_ACRONYM_LEN = 4

# Place adjectives of the adjectival inversion ("Universitaet Genf" reached through
# "Genfer Universitaet"). A static table rather than generative morphology; Lausanne
# has no German adjective and therefore no entry. Keys are compared in NFC, because
# the curated list carries its umlauts decomposed.
PLACE_ADJECTIVES = {
    "Genf": "Genfer",
    "Zürich": "Zürcher",
    "Basel": "Basler",
    "Bern": "Berner",
    "Luzern": "Luzerner",
}

# Where the matched form comes from. "surname-index" is the curated headword's bare
# surname, which is an index entry rather than a form of its own; a surname taken from
# a variant reports that variant instead ("Mayer, Gertrud" behind a hit on "Mayer").
FORM_SOURCES = ("headword", "cache-variant", "legacy", "surname-index")

EVIDENCE_TYPOGRAPHIC = "typographic"
EVIDENCE_NONE = "none"

# Typographic evidence of a one-word work title: quotation marks of every shape the
# corpus carries, and the possessives that mark a following noun as a titled work.
QUOTE_CHARS = frozenset("\"'«»‹›‚“”„‘’")
POSSESSIVES = frozenset({
    "sa", "son", "ses", "seine", "seiner", "his", "her", "sua", "suo",
})

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
_QUALIFIER_RE = re.compile(r"^(.*?)\s*\([^()]*\)$")
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


# --- lexicon ----------------------------------------------------------------------


def build_lexicon(
    entities_path: Path | str,
    cache_path: Path | str,
    legacy_path: Path | str | None = None,
    review_path: Path | str | None = None,
) -> dict:
    """Build the matching lexicon from list, GND cache and legacy mention index.

    The list is a trust boundary and must exist; cache and legacy index are optional
    and simply contribute fewer name forms when missing. The returned dict carries
    `entries` (gid -> record), `forms` (form string -> owners as
    (gid, category, rule, source)), `by_first_word` (first word -> forms, longest
    first), `lower_by_first_word` (the same index lowercased and reduced to the
    multi-token forms, which is the case-tolerant channel), `surnames` (surname ->
    gids), `surname_forms` (surname -> gid -> (form, source), the provenance of every
    surname entry), the all-caps indexes
    `caps_forms` / `caps_by_first_word` / `caps_surnames` / `caps_surname_forms`,
    `legacy_demoted` (the (gid, form) pairs the bearer's record does not corroborate),
    `review_suspect` (the (gid, form) pairs the variant review holds back at tier 2),
    `skipped` (counters) and `sources` (the input paths).

    The derived-form channels run as a second pass over the finished base lexicon, so
    they see every entity and displace none; their catalogue is in the module docstring.

    `review_path` names the operator-gated variant_review.json: a cache form with the
    verdict `reject` never enters the lexicon (neither as full form nor via the surname
    index), a `suspect` form enters but yields tier-2 candidates only, and a cache form
    the review does not know counts as suspect until the next review run. The review
    binds only the cache channel; curated headwords and legacy forms pass unfiltered.
    """
    entities = _read_json(entities_path, required=True) or {}
    cache = _read_json(cache_path) or {}
    cache_entries = cache.get("entries", {}) if isinstance(cache, dict) else {}
    legacy_index = legacy_names(_read_json(legacy_path)) if legacy_path else {}
    review = _read_json(review_path) if review_path else None

    forms: dict[str, list[tuple[str, str, str, str]]] = {}
    surnames: dict[str, set[str]] = {}
    surname_forms: dict[str, dict[str, tuple[str, str]]] = {}
    entries: dict[str, dict] = {}
    legacy_demoted: list[tuple[str, str]] = []
    review_suspect: set[tuple[str, str]] = set()
    skipped = {"no_label": 0, "gnd_404": 0, "short_org_token": 0, "duplicate_gid": 0,
               "review_reject": 0}

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
            suspect_variants: tuple[tuple[str, str], ...] = ()
            if review is not None:
                variants, suspect_variants = _filter_reviewed(
                    review, gid, category, variants, skipped
                )
            if category == "person":
                _add_person(forms, surnames, surname_forms, gid, label, variants)
            elif category == "organisation":
                _add_org(forms, gid, label, variants, skipped)
            else:
                _add_work(forms, gid, label, variants)
            for form, source in suspect_variants:
                added = _capture_added(forms, gid, lambda: _add_suspect_variant(
                    forms, surnames, surname_forms, gid, category, label, form, source,
                    skipped,
                ))
                for new_form in added:
                    review_suspect.add((gid, new_form))
                    upper = new_form.upper()
                    if (category == "person" and len(new_form.split()) >= 2
                            and len(upper) == len(new_form)):
                        review_suspect.add((gid, upper))
            for form in demoted:
                legacy_demoted.append((gid, form))
                _add_legacy_form(forms, gid, category, form)

    for gid, entry in entries.items():
        _add_derived(forms, surnames, gid, entry["category"], entry["label"])

    caps_forms = _caps_index(forms)
    return {
        "entries": entries,
        "forms": {form: tuple(sorted(owners)) for form, owners in forms.items()},
        "by_first_word": _first_word_index(forms),
        "lower_by_first_word": _first_word_index(forms, fold=True),
        "surnames": {name: tuple(sorted(gids)) for name, gids in surnames.items()},
        "surname_forms": surname_forms,
        "caps_forms": {form: tuple(sorted(owners)) for form, owners in caps_forms.items()},
        "caps_by_first_word": _first_word_index(caps_forms),
        "caps_surnames": _caps_surnames(surnames),
        "caps_surname_forms": _caps_surname_forms(surname_forms),
        "legacy_demoted": tuple(legacy_demoted),
        "review_suspect": frozenset(review_suspect),
        "skipped": skipped,
        "sources": {
            "entities": str(entities_path),
            "cache": str(cache_path),
            "legacy": str(legacy_path) if legacy_path else None,
            "review": str(review_path) if review is not None else None,
            "cache_retrieved": cache.get("retrieved") if isinstance(cache, dict) else None,
        },
    }


_REVIEW_LIST_KEY = {"person": "persons", "organisation": "organisations", "work": "works"}


def _filter_reviewed(
    review: dict,
    gid: str,
    category: str,
    variants: tuple[tuple[str, str], ...],
    skipped: dict[str, int],
) -> tuple[tuple[tuple[str, str], ...], tuple[tuple[str, str], ...]]:
    """Split the cache channel by verdict: reject drops, suspect (or unreviewed) demotes."""
    verdicts = ((review.get(_REVIEW_LIST_KEY[category]) or {}).get(gid) or {}).get(
        "verdicts"
    ) or {}
    kept: list[tuple[str, str]] = []
    suspect: list[tuple[str, str]] = []
    for form, source in variants:
        if source != "cache-variant":
            kept.append((form, source))
            continue
        verdict = (verdicts.get(form) or {}).get("verdict")
        if verdict == "reject":
            skipped["review_reject"] += 1
        elif verdict == "approve":
            kept.append((form, source))
        else:
            suspect.append((form, source))
    return tuple(kept), tuple(suspect)


def _add_suspect_variant(
    forms: dict[str, list[tuple[str, str, str, str]]],
    surnames: dict[str, set[str]],
    surname_forms: dict[str, dict[str, tuple[str, str]]],
    gid: str,
    category: str,
    label: str,
    form: str,
    source: str,
    skipped: dict[str, int],
) -> None:
    """Register one suspect cache form through the regular per-category derivation."""
    if category == "person":
        _add_person_variant(forms, surnames, surname_forms, gid, form, source)
    elif category == "organisation":
        _add_org(forms, gid, label, ((form, source),), skipped)
    else:
        _add_work(forms, gid, label, ((form, source),))


def _capture_added(
    forms: dict[str, list[tuple[str, str, str, str]]],
    gid: str,
    adder,
) -> list[str]:
    """Forms `adder` newly registers for `gid`; owner dedup makes re-adds invisible."""
    before = {form for form, owners in forms.items() if any(o[0] == gid for o in owners)}
    adder()
    return [
        form
        for form, owners in forms.items()
        if form not in before and any(o[0] == gid for o in owners)
    ]


def _first_word_index(forms: dict[str, list], fold: bool = False) -> dict[str, tuple[str, ...]]:
    """First word -> the forms starting with it, longest first (the scan tries in order).

    With `fold` the key is lowercased and only the forms of at least two tokens enter,
    which is the index of the case-tolerant channel.
    """
    buckets: dict[str, list[str]] = {}
    for form in forms:
        if fold and len(form.split()) < 2:
            continue
        word = _first_word(form)
        buckets.setdefault(word.lower() if fold else word, []).append(form)
    return {
        word: tuple(sorted(bucket, key=lambda form: (-len(form), form)))
        for word, bucket in buckets.items()
    }


def _caps_index(forms: dict[str, list[tuple[str, str, str, str]]]) -> dict[str, list]:
    """All-caps projection of the person full names (at least two tokens)."""
    caps: dict[str, list[tuple[str, str, str, str]]] = {}
    for form, owners in forms.items():
        upper = form.upper()
        if len(upper) != len(form) or len(form.split()) < 2:
            continue
        for gid, category, rule, source in owners:
            if category == "person" and rule in ("full-name", "variant-full-name"):
                _add_form(caps, upper, gid, category, "caps-full-name", source)
    return caps


def _caps_surnames(surnames: dict[str, set[str]]) -> dict[str, tuple[str, ...]]:
    caps: dict[str, set[str]] = {}
    for surname, gids in surnames.items():
        upper = surname.upper()
        if len(upper) == len(surname) and len(upper) > 1:
            caps.setdefault(upper, set()).update(gids)
    return {name: tuple(sorted(gids)) for name, gids in caps.items()}


def _caps_surname_forms(
    surname_forms: dict[str, dict[str, tuple[str, str]]],
) -> dict[str, dict[str, tuple[str, str]]]:
    """Provenance of the all-caps surnames, taken from the mixed-case entries."""
    caps: dict[str, dict[str, tuple[str, str]]] = {}
    for surname, origins in surname_forms.items():
        upper = surname.upper()
        if len(upper) == len(surname) and len(upper) > 1:
            for gid, origin in origins.items():
                caps.setdefault(upper, {}).setdefault(gid, origin)
    return caps


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


def _variants(cached: dict, extra: tuple[str, ...] = ()) -> tuple[tuple[str, str], ...]:
    """(form, source) pairs beyond the headword; the first source of a form wins."""
    seen: dict[str, str] = {}
    for value in [cached.get("preferred_name"), *(cached.get("variant_names") or [])]:
        form = _collapse(str(value or ""))
        if form:
            seen.setdefault(form, "cache-variant")
    for value in extra:
        form = _collapse(str(value or ""))
        if form:
            seen.setdefault(form, "legacy")
    return tuple(seen.items())


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
    forms: dict[str, list[tuple[str, str, str, str]]],
    gid: str,
    category: str,
    form: str,
) -> None:
    """Register a demoted legacy form: tier-2 candidate source, never a surname."""
    tokens = form.split()
    if len(tokens) == 1 and not _is_distinctive_token(tokens[0]):
        return
    _add_form(forms, form, gid, category, "legacy-form", "legacy")


def _add_form(
    forms: dict[str, list[tuple[str, str, str, str]]],
    form: str,
    gid: str,
    category: str,
    rule: str,
    source: str,
) -> None:
    form = _collapse(form)
    if not form or not _first_word(form):
        return
    owners = forms.setdefault(form, [])
    if any(owner[0] == gid for owner in owners):
        return
    owners.append((gid, category, rule, source))


def _register_surname(
    surnames: dict[str, set[str]],
    surname_forms: dict[str, dict[str, tuple[str, str]]],
    surname: str,
    gid: str,
    form: str,
    source: str,
) -> None:
    """Add a surname to the index and remember the form that put it there."""
    surnames.setdefault(surname, set()).add(gid)
    surname_forms.setdefault(surname, {}).setdefault(gid, (form, source))


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
    forms: dict[str, list[tuple[str, str, str, str]]],
    surnames: dict[str, set[str]],
    surname_forms: dict[str, dict[str, tuple[str, str]]],
    gid: str,
    label: str,
    variants: tuple[tuple[str, str], ...],
) -> None:
    surname, forenames = _split_person_label(label)
    if surname:
        _register_surname(surnames, surname_forms, surname, gid, surname, "surname-index")
    if surname and forenames:
        _add_form(forms, f"{forenames} {surname}", gid, "person", "full-name", "headword")
        _add_form(forms, label, gid, "person", "full-name", "headword")
        initial = forenames[0]
        if initial.isalpha():
            _add_form(forms, f"{initial}. {surname}", gid, "person", "initial-surname",
                      "headword")
    for variant, source in variants:
        _add_person_variant(forms, surnames, surname_forms, gid, variant, source)


def _add_person_variant(
    forms: dict[str, list[tuple[str, str, str, str]]],
    surnames: dict[str, set[str]],
    surname_forms: dict[str, dict[str, tuple[str, str]]],
    gid: str,
    variant: str,
    source: str,
) -> None:
    if "," in variant:
        surname, forenames = _split_person_label(variant)
        if _is_distinctive_token(surname) and not _is_initials_only(surname):
            _register_surname(surnames, surname_forms, surname, gid, variant, source)
        if surname and forenames and not _is_initials_only(f"{forenames} {surname}"):
            _add_form(forms, f"{forenames} {surname}", gid, "person", "variant-full-name",
                      source)
            _add_form(forms, variant, gid, "person", "variant-full-name", source)
        return
    tokens = variant.split()
    if _is_initials_only(variant):
        return
    if len(tokens) >= 2:
        _add_form(forms, variant, gid, "person", "variant-full-name", source)
    elif tokens and _is_distinctive_token(tokens[0]):
        _register_surname(surnames, surname_forms, tokens[0], gid, variant, source)


def _add_org(
    forms: dict[str, list[tuple[str, str, str, str]]],
    gid: str,
    label: str,
    variants: tuple[tuple[str, str], ...],
    skipped: dict[str, int],
) -> None:
    for rule, form, source in _labelled_forms(label, variants, "org-name", "org-variant"):
        tokens = form.split()
        if len(tokens) >= 2:
            _add_form(forms, form, gid, "organisation", rule, source)
        elif tokens and _is_distinctive_token(tokens[0]):
            _add_form(forms, tokens[0], gid, "organisation", "org-token", source)
        else:
            skipped["short_org_token"] += 1


def _labelled_forms(
    label: str,
    variants: tuple[tuple[str, str], ...],
    head_rule: str,
    variant_rule: str,
) -> Iterator[tuple[str, str, str]]:
    """(rule, form, source) for the headword and every variant of an org or work."""
    yield head_rule, label, "headword"
    for form, source in variants:
        yield variant_rule, form, source


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
    forms: dict[str, list[tuple[str, str, str, str]]],
    gid: str,
    label: str,
    variants: tuple[tuple[str, str], ...],
) -> None:
    for rule, form, source in _labelled_forms(label, variants, "work-title", "work-variant"):
        tokens = form.split()
        if len(tokens) >= 2:
            _add_form(forms, form, gid, "work", rule, source)
        elif tokens and len(tokens[0]) >= MIN_SHORT_TITLE_LEN:
            _add_form(forms, tokens[0], gid, "work", "short-title", source)


# --- derived forms (worklist-only recall channels) ---------------------------------


def _add_derived(
    forms: dict[str, list[tuple[str, str, str, str]]],
    surnames: dict[str, set[str]],
    gid: str,
    category: str,
    label: str,
) -> None:
    """Register the derived spellings of one entity; every one of them is tier 2.

    The channels read the forms the entity already registered instead of its raw
    inputs, which keeps them behind every earlier gate: a cache form the variant review
    rejected never entered `forms`, so it cannot return through a derived form either.
    The pass runs after the base forms of the whole list, so a derived form neither
    shadows a listed spelling (the owner dedup in `_add_form` keeps the first
    registration) nor displaces a reading that can reach tier 1 (`_reaches_tier1`).
    """
    for form, rule, source in _own_forms(forms, gid):
        for derived, suffix in _derived_forms(form, category):
            if not _reaches_tier1(forms, surnames, derived):
                _add_form(forms, derived, gid, category, rule + suffix, source)
    for derived in _initials_forms(label, category):
        if not _reaches_tier1(forms, surnames, derived):
            _add_form(forms, derived, gid, category, "full-name" + INITIALS_SUFFIX,
                      "headword")


def _reaches_tier1(
    forms: dict[str, list[tuple[str, str, str, str]]],
    surnames: dict[str, set[str]],
    form: str,
) -> bool:
    """True when the lexicon already reads `form` at tier 1, so no channel may take it.

    A surname counts, because an anchor lifts it to tier 1 inside a document. The
    derived channels add recall on the worklist and must never cost an auto-mark, and
    the scan prefers the form index over the surname index.
    """
    if form in surnames:
        return True
    return any(_form_tier(rule) == 1 for _, _, rule, _ in forms.get(form, ()))


def _own_forms(
    forms: dict[str, list[tuple[str, str, str, str]]],
    gid: str,
) -> list[tuple[str, str, str]]:
    """(form, rule, source) of the base forms one entity owns; derived ones excluded."""
    out: list[tuple[str, str, str]] = []
    for form, owners in forms.items():
        for owner_gid, _, rule, source in owners:
            if owner_gid == gid and ":" not in rule:
                out.append((form, rule, source))
                break
    return out


def _derived_forms(form: str, category: str) -> Iterator[tuple[str, str]]:
    """(derived form, rule suffix) of the shape-driven channels of one form.

    Acronym case: an all-caps single-token organisation also matches its capitalized
    spelling, the corpus writing "l'Unesco" beside "UNESCO". Qualifier strip: a form
    with a trailing parenthetical also matches without it ("Le Populaire (Paris)" as
    "Le Populaire"). Place adjective: a two-token organisation whose second token is a
    listed place also matches the inverted German form ("Genfer Universitaet").
    """
    tokens = form.split()
    if (category == "organisation" and len(tokens) == 1 and form.isalpha()
            and form.isupper() and len(form) >= MIN_ACRONYM_LEN):
        yield form.capitalize(), ACRONYM_CASE_SUFFIX
    head = _strip_qualifier(form)
    if head:
        yield head, QUALIFIER_SUFFIX
    if category == "organisation" and len(tokens) == 2:
        adjective = PLACE_ADJECTIVES.get(unicodedata.normalize("NFC", tokens[1]))
        if adjective:
            yield f"{adjective} {tokens[0]}", PLACE_ADJECTIVE_SUFFIX


def _strip_qualifier(form: str) -> str:
    """Head of a form with a trailing parenthetical qualifier, else the empty string.

    The head has to pass the distinctiveness test of the org-token rule, because the
    channel also produces ordinary German words ("Bund" out of the disambiguated
    organisation name); that those reach the worklist and nothing else is what makes
    the channel acceptable.
    """
    match = _QUALIFIER_RE.match(form)
    if match is None:
        return ""
    head = match.group(1).strip()
    if len(head) < MIN_TOKEN_LEN or not any(char.isupper() for char in head):
        return ""
    return head


def _initials_forms(label: str, category: str) -> tuple[str, ...]:
    """Dotted initials of a person headword ("Jaspers, Karl" -> "K.J." and "K. J.").

    Interview transcripts label the speaker with initials, which is the mention class
    this channel reaches. Both spellings stay tier 2: initials claim unrelated
    positions document-wide far too easily (the doc-1220 finding), and a pair several
    persons share simply becomes a multi-owner worklist candidate.
    """
    if category != "person":
        return ()
    surname, forenames = _split_person_label(label)
    if not (surname and forenames and surname[0].isalpha() and forenames[0].isalpha()):
        return ()
    initials = f"{forenames[0].upper()}.{surname[0].upper()}."
    return (initials, initials.replace(".", ". ", 1))


# --- zones ------------------------------------------------------------------------


def _scan_zones(xml: str) -> _Zones:
    """Collect the content ranges of text, excluded zones, plain bibl and speaker."""
    text: list[Span] = []
    excluded: list[Span] = []
    plain_bibl: list[Span] = []
    speakers: list[Span] = []
    paragraphs: list[Span] = []
    emphasis: list[Span] = []
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
                text, excluded, plain_bibl, speakers, paragraphs, emphasis,
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
    required = ("by_first_word", "lower_by_first_word", "surnames", "caps_by_first_word")
    if any(key not in lexicon for key in required):
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
    speaker_hits: dict[int, _Hit],
    seed_anchors: set[str] | None = None,
    lowercase_words: frozenset[str] = frozenset(),
    author_gids: frozenset[str] = frozenset(),
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
        if hit.gid in author_gids and (hit.rule.startswith("caps-") or hit.case_tolerant):
            pos = max(hit.end, pos + 1)
            continue
        if _base_rule(hit.rule) in _SUSPECT_RULES and _is_suspect(
            xml, norm, hit, lexicon, lowercase_words
        ):
            hit = replace(hit, rule=hit.rule + SUSPECT_SUFFIX, tier=2)
        if hit.tier == 1 and (hit.gid, hit.matched_form) in review_suspect:
            hit = replace(hit, rule=hit.rule + SUSPECT_SUFFIX, tier=2)
        candidate, resume = _build_candidate(xml, norm, zones, hit)
        if candidate is not None:
            out.append(candidate)
            if candidate["tier"] == 1:
                anchored.add(candidate["gid"])
        pos = max(resume, pos + 1)
    return out


def _base_rule(rule: str) -> str:
    """The rule without its suffixes (derived channel, :ambiguous, :suspect, position)."""
    return rule.split(":", 1)[0]


def _form_tier(rule: str) -> int:
    """Tier of a lexicon rule; a derived channel carries a suffix and stays worklist."""
    base, suffix, _ = rule.partition(":")
    return 2 if suffix else TIER_BY_RULE[base]


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
    raw_start, raw_end = norm.starts[n_start], norm.ends[n_end - 1]
    if xml[max(raw_start - 1, 0):raw_start] == "-" or xml[raw_end:raw_end + 1] == "-":
        return True
    if _unknown_capital_before(text, n_start, n_end, lexicon):
        return True
    # A genitive name is followed by its head noun, and German capitalizes every
    # noun, so the trailing signal would fire on every correct genitive mention.
    genitive = word.endswith("s") and word[:-1] in lexicon["surnames"]
    return not genitive and _unknown_capital_after(text, n_start, n_end, lexicon)


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
        # The all-caps writing of a person name belongs to the caps channel, which
        # carries the byline exception of the document author.
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
    """Mark a hit that only letter case separates from its form, and weigh its case."""
    hit = replace(hit, case_tolerant=True)
    if _is_lowercase_writing(segment, form):
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
    then ":suspect" (a property of the context), then ":in-plain-bibl" (a property of
    the position). Rules that already name the ambiguity in their base keep it.
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
    if _base_rule(rule) == "short-title":
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
    """Word character of the scan; a superscript footnote digit separates instead.

    The corpus glues footnote markers to the word they annotate, and a name in front of
    one must end where the marker starts, exactly as it does in front of a comma. The
    numeric-other category holds the superscripts and is therefore no word character.
    """
    return char.isalnum() and (char.isalpha() or unicodedata.category(char) != "No")


def _is_word_at(text: str, pos: int) -> bool:
    return pos < len(text) and _is_word(text[pos])
