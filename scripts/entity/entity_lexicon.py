"""Lexicon construction for the deterministic entity search (analysis only).

Design plan and rule catalogue: knowledge/tei-mapping.md (sections "Target
model" and "Matching method"). The module reads the curated entity list, the lobid GND
cache and the legacy mention index; it never calls a language model, and ids always
come from the curated list. The scan that consumes the lexicon is
scripts.entity.entity_matcher, which re-exports `build_lexicon`.

Two public functions:

    build_lexicon(entities_path, cache_path, legacy_path=None, review_path=None,
                  policy_path=None) -> dict
        Merges the curated list `data/entities/all_entities.json`, the lobid cache
        `data/entities/gnd_cache.json` (name variants, optional) and the legacy
        mention index `data/entities/legacy_mentions.json` (optional) into one
        lexicon. Entries without a label are skipped, so are entries whose cache
        answer is 404 (defective GND id).

    load_marking_policy(path, listed_gids) -> dict
        Reads and validates the operator marking decisions
        `data/entities/marking_policy.json`. The file is the single load point of the
        policy; `build_lexicon` carries the parsed result in `lexicon["policy"]`, so
        every consumer of the lexicon reads the same decisions.

Deliberate simplifications (upgrade path in the milestones M3 to M5):

- Five derived-form channels close gaps of the facsimile-adjudicated
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
    * ":subtitle-join", a one-token work title joins each of its own multi-word
      forms as "Title. Subtitle" ("Nietzsche. Einfuehrung in das Verstaendnis
      seines Philosophierens"), so the full printed title reaches the worklist as
      one span instead of a truncated tier-1 wrap of the subtitle (doc 650).
  The channels read the forms that were actually registered, so every earlier gate
  binds them as well; a cache form the variant review rejected has no derived form.
- Person labels without a forename (mononyms such as "Platon") reach no tier-1 rule;
  they enter the surname index and can only surface as tier 2.
- Single-token work titles need at least three characters to enter the lexicon at
  all, otherwise the worklist fills with noise. The typographic pre-sorting of the
  candidates they produce is the scan's `evidence` field.
- A surname taken from a cache or legacy variant enters the surname index only when
  it passes the same distinctiveness test the org-token rule states (at least four
  characters, capitalized). Curated headwords and curated variants are registered
  unguarded, so the test only filters variant artifacts, the transliteration fragments
  lobid carries ("Ma, Kesi" for Marx, "Big, abbe" for Voltaire). Forename-shaped
  variants ("Pierre") pass it and stay as tier-2 noise for the judge stage.
- The optional `variants` field of a list entry is the operator's channel for a corpus
  spelling the GND norm form does not carry ("Kolumbus" for "Colombo, Cristoforo").
  Every string runs through the form derivation of its category headword and takes the
  tier its own shape earns; the field itself lifts nothing into tier 1.
- Variants made only of dotted initials ("J. H." for Pestalozzi) never enter the
  full-name channel; as tier-1 forms they would claim unrelated initials
  document-wide (the doc-1220 pilot finding). The initials of a headword reach the
  worklist through the ":initials" channel and nothing beyond it.
- The operator marking policy binds two entity-level decisions. A work in
  `work_titles.drop_from_scope` registers no form at all, so its title produces no
  candidate in any tier, while the entry stays in `entries` and keeps its label for
  the reports; a surface another entity also carries stays reachable through that
  entity ("Nietzsche" as the listed surname). The anchor release
  (`anchor_free_surnames`) and the corroboration requirement
  (`work_titles.require_typographic_corroboration`) are positional and therefore
  matcher rules; the lexicon only carries them in `lexicon["policy"]`.
- A legacy surface form that its bearer's own record does not corroborate stays a
  candidate source but reaches only tier 2, with the rule "legacy-form", and never
  enters the surname index. The legacy index was harvested from the gold references,
  so its uncorroborated pairings would both leak gold into tier 1 and carry the
  known poisoning ("Jérémie" filed under Jaspers). Corroboration is the shared
  predicate `legacy_form_is_covered`, which `entity_lint` reports as warnings.
"""

from __future__ import annotations

import json
import re
import unicodedata
from collections.abc import Iterator
from pathlib import Path

MIN_TOKEN_LEN = 4
MIN_SHORT_TITLE_LEN = 3

# A bare surname the operator released from the anchor requirement; its own rule id, so
# the released population stays countable in every downstream report.
ANCHOR_FREE_RULE = "anchor-free-surname"

TIER_BY_RULE = {
    "full-name": 1,
    "variant-full-name": 1,
    "initial-surname": 1,
    "anchored-surname": 1,
    ANCHOR_FREE_RULE: 1,
    "caps-full-name": 1,
    "org-name": 1,
    "org-variant": 1,
    "org-token": 1,
    "work-title": 1,
    "work-variant": 1,
    "speaker": 1,
    "speaker-initials": 1,
    "bare-surname": 2,
    "ambiguous-surname": 2,
    "caps-surname": 2,
    "short-title": 2,
    "crosses-markup": 2,
    "legacy-form": 2,
    "adjective-form": 2,
}

# Derived-form channels. Each one registers a further spelling of a form the entity
# already carries; the suffix sits on the lexicon rule itself, which makes every such
# form tier 2 by construction (_form_tier), so no channel here can auto-mark.
ACRONYM_CASE_SUFFIX = ":acronym-case"
QUALIFIER_SUFFIX = ":qualifier-strip"
PLACE_ADJECTIVE_SUFFIX = ":place-adjective"
INITIALS_SUFFIX = ":initials"
SUBTITLE_JOIN_SUFFIX = ":subtitle-join"

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
# "curated-variant" is the operator-registered corpus spelling of a list entry.
CURATED_SOURCE = "curated-variant"
FORM_SOURCES = ("headword", CURATED_SOURCE, "cache-variant", "legacy", "surname-index")

_CATEGORY_BY_LIST = {"persons": "person", "organisations": "organisation", "works": "work"}
_LABEL_FIELD = {"persons": "name", "organisations": "orgName", "works": "title"}
_LEGACY_KEY = {"persons": "persons", "organisations": "organizations", "works": "works"}

_WORD_RUN_RE = re.compile(r"\w+")
_QUALIFIER_RE = re.compile(r"^(.*?)\s*\([^()]*\)$")


def _form_tier(rule: str) -> int:
    """Tier of a lexicon rule; a derived channel carries a suffix and stays worklist."""
    base, suffix, _ = rule.partition(":")
    return 2 if suffix else TIER_BY_RULE[base]


# --- operator marking policy (data/entities/marking_policy.json) --------------------

POLICY_ANCHOR_FREE = "anchor_free_surnames"
POLICY_HELD_OUT = "held_out_surnames"
POLICY_WORK_TITLES = "work_titles"
POLICY_DROP = "drop_from_scope"
POLICY_CORROBORATE = "require_typographic_corroboration"

# Documentation fields of the curated file. Every other key has to be a known bucket,
# so a mistyped bucket name fails loudly instead of releasing nothing in silence.
POLICY_NOTE_FIELDS = ("note", "decided")

EMPTY_POLICY = {
    "source": None,
    "decided": None,
    "anchor_free": {},
    "held_out": frozenset(),
    "drop_from_scope": frozenset(),
    "require_corroboration": frozenset(),
}


def load_marking_policy(path: Path | str, listed_gids) -> dict:
    """Read and validate the operator marking decisions; the single load point."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return parse_marking_policy(data, listed_gids, source=str(path))


def parse_marking_policy(data, listed_gids, source: str = "") -> dict:
    """Validate the marking decisions and project them for lexicon and matcher.

    The file is a trust boundary: an unknown bucket name, a malformed entry, a gid the
    curated list does not carry, or a gid in two buckets raises ValueError instead of
    binding a decision nobody can read back. `anchor_free` maps a surname key to the
    gids released for exactly that key; nothing is derived from a key.
    """
    where = f"marking policy {source}".strip()
    if not isinstance(data, dict):
        raise ValueError(f"{where}: policy must be a JSON object")
    _reject_unknown(data, (POLICY_ANCHOR_FREE, POLICY_HELD_OUT, POLICY_WORK_TITLES,
                           *POLICY_NOTE_FIELDS), where)
    works = data.get(POLICY_WORK_TITLES) or {}
    if not isinstance(works, dict):
        raise ValueError(f"{where}: {POLICY_WORK_TITLES} must be a JSON object")
    _reject_unknown(works, (POLICY_DROP, POLICY_CORROBORATE), f"{where} {POLICY_WORK_TITLES}")

    listed = {str(gid) for gid in listed_gids}
    seen: dict[str, str] = {}
    anchor_free: dict[str, set[str]] = {}
    for entry in _policy_entries(data, POLICY_ANCHOR_FREE, where):
        gid = _policy_gid(entry, POLICY_ANCHOR_FREE, listed, seen, where)
        keys = entry.get("keys")
        if not isinstance(keys, list) or not keys:
            raise ValueError(f"{where}: entry {gid} needs keys as a non-empty list")
        for raw in keys:
            key = _collapse(raw) if isinstance(raw, str) else ""
            if not key:
                raise ValueError(f"{where}: entry {gid} has an empty key in keys")
            anchor_free.setdefault(key, set()).add(gid)
    held_out = _policy_gids(data, POLICY_HELD_OUT, listed, seen, where)
    drop = _policy_gids(works, POLICY_DROP, listed, seen, f"{where} {POLICY_WORK_TITLES}")
    corroborate = _policy_gids(works, POLICY_CORROBORATE, listed, seen,
                               f"{where} {POLICY_WORK_TITLES}")
    return {
        "source": source or None,
        "decided": data.get("decided"),
        "anchor_free": {key: frozenset(gids) for key, gids in anchor_free.items()},
        "held_out": held_out,
        "drop_from_scope": drop,
        "require_corroboration": corroborate,
    }


def _reject_unknown(data: dict, known: tuple[str, ...], where: str) -> None:
    unknown = sorted(set(data) - set(known))
    if unknown:
        raise ValueError(f"{where}: unknown key(s) {', '.join(unknown)}")


def _policy_entries(data: dict, bucket: str, where: str) -> list[dict]:
    entries = data.get(bucket)
    if entries is None:
        return []
    if not isinstance(entries, list) or not all(isinstance(e, dict) for e in entries):
        raise ValueError(f"{where}: {bucket} must be a list of objects")
    return entries


def _policy_gid(entry: dict, bucket: str, listed: set[str], seen: dict[str, str],
                where: str) -> str:
    gid = entry.get("gid")
    if not isinstance(gid, str) or not gid.strip():
        raise ValueError(f"{where}: {bucket} carries an entry without a gid")
    gid = gid.strip()
    if gid not in listed:
        raise ValueError(f"{where}: gid {gid} is absent from the curated entity list")
    if gid in seen:
        prior = seen[gid]
        place = f"twice in {bucket}" if prior == bucket else f"in {prior} and in {bucket}"
        raise ValueError(f"{where}: gid {gid} stands {place}")
    seen[gid] = bucket
    return gid


def _policy_gids(data: dict, bucket: str, listed: set[str], seen: dict[str, str],
                 where: str) -> frozenset[str]:
    return frozenset(
        _policy_gid(entry, bucket, listed, seen, where)
        for entry in _policy_entries(data, bucket, where)
    )


def listed_gids(entities: dict) -> set[str]:
    """Every GND id the curated list carries, whatever the entry's other defects."""
    return {
        str(raw.get("GND_id")).strip()
        for list_key in _CATEGORY_BY_LIST
        for raw in entities.get(list_key, []) or []
        if str(raw.get("GND_id") or "").strip()
    }


def build_lexicon(
    entities_path: Path | str,
    cache_path: Path | str,
    legacy_path: Path | str | None = None,
    review_path: Path | str | None = None,
    policy_path: Path | str | None = None,
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
    `policy` (the validated operator marking decisions), `skipped` (counters) and
    `sources` (the input paths).

    The derived-form channels run as a second pass over the finished base lexicon, so
    they see every entity and displace none; their catalogue is in the module docstring.

    `policy_path` names the operator marking decisions marking_policy.json. It is
    validated on load (`parse_marking_policy`), reaches the matcher as
    `lexicon["policy"]`, and drops the forms of every work the operator took out of the
    marking scope. Without it the lexicon carries EMPTY_POLICY and nothing changes.

    `review_path` names the operator-gated variant_review.json: a cache form with the
    verdict `reject` never enters the lexicon (neither as full form nor via the surname
    index), a `suspect` form enters but yields tier-2 candidates only, and a cache form
    the review does not know counts as suspect until the next review run. The review
    binds only the cache channel; curated headwords, curated variants and legacy forms
    pass unfiltered.
    """
    entities = _read_json(entities_path, required=True) or {}
    cache = _read_json(cache_path) or {}
    cache_entries = cache.get("entries", {}) if isinstance(cache, dict) else {}
    legacy_index = legacy_names(_read_json(legacy_path)) if legacy_path else {}
    review = _read_json(review_path) if review_path else None
    policy = (EMPTY_POLICY if policy_path is None
              else load_marking_policy(policy_path, listed_gids(entities)))
    out_of_scope = policy["drop_from_scope"]

    forms: dict[str, list[tuple[str, str, str, str]]] = {}
    surnames: dict[str, set[str]] = {}
    surname_forms: dict[str, dict[str, tuple[str, str]]] = {}
    entries: dict[str, dict] = {}
    legacy_demoted: list[tuple[str, str]] = []
    review_suspect: set[tuple[str, str]] = set()
    skipped = {"no_label": 0, "gnd_404": 0, "short_org_token": 0, "duplicate_gid": 0,
               "review_reject": 0, "policy_out_of_scope": 0}

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
            if gid in out_of_scope:
                # The entry stays known (label, closed-world id) and registers no form.
                skipped["policy_out_of_scope"] += 1
                continue
            legacy = legacy_index.get(normalize_gid(gid), ())
            corroborated, demoted = _split_legacy(legacy, label, cached)
            variants = _variants(cached, _curated_variants(raw), corroborated)
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
                # _capture_added calls the closure at once, so the loop names cannot drift.
                added = _capture_added(forms, gid, lambda: _add_suspect_variant(
                    forms, surnames, surname_forms, gid, category, label, form, source,  # noqa: B023
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
        if gid not in out_of_scope:
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
        "policy": policy,
        "skipped": skipped,
        "sources": {
            "entities": str(entities_path),
            "cache": str(cache_path),
            "legacy": str(legacy_path) if legacy_path else None,
            "review": str(review_path) if review is not None else None,
            "policy": policy["source"],
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
    raw_verdicts = ((review.get(_REVIEW_LIST_KEY[category]) or {}).get(gid) or {}).get(
        "verdicts"
    ) or {}
    # Review keys are cache forms as written; fold them like every registered form.
    verdicts = {_collapse(key): value for key, value in raw_verdicts.items()}
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


def _curated_variants(raw: dict) -> tuple[str, ...]:
    """The `variants` field of one list entry; a malformed field contributes nothing.

    The field is a trust boundary like every other input channel: `entity_lint` reports
    its defects, the build reads only what is usable.
    """
    value = raw.get("variants")
    return _dedup(value) if isinstance(value, list) else ()


def _variants(
    cached: dict,
    curated: tuple[str, ...] = (),
    extra: tuple[str, ...] = (),
) -> tuple[tuple[str, str], ...]:
    """(form, source) pairs beyond the headword; the first source of a form wins.

    Curated strings come first, so a form the list and the cache both carry counts as
    curated and stays outside the reach of the variant review.
    """
    seen: dict[str, str] = {}
    for value in curated:
        form = _collapse(str(value or ""))
        if form:
            seen.setdefault(form, CURATED_SOURCE)
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
    """Register one variant form of a person.

    The distinctiveness guard on the surname index filters variant artifacts of the
    cache and legacy channels; a curated string is operator authority and enters
    unguarded, exactly like a curated one-token headword. The initials guard binds
    every channel, because initials claim unrelated positions document-wide.
    """
    curated = source == CURATED_SOURCE
    if "," in variant:
        surname, forenames = _split_person_label(variant)
        if ((curated or _is_distinctive_token(surname))
                and not _is_initials_only(surname)):
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
    elif tokens and (curated or _is_distinctive_token(tokens[0])):
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
    own = _own_forms(forms, gid)
    for form, rule, source in own:
        for derived, suffix in _derived_forms(form, category):
            if not _reaches_tier1(forms, surnames, derived):
                _add_form(forms, derived, gid, category, rule + suffix, source)
    for derived in _initials_forms(label, category):
        if not _reaches_tier1(forms, surnames, derived):
            _add_form(forms, derived, gid, category, "full-name" + INITIALS_SUFFIX,
                      "headword")
    # Subtitle join: a one-token work title printed as "Title. Subtitle" (doc 650,
    # "Nietzsche. Einfuehrung in das Verstaendnis seines Philosophierens"). The
    # joined form outranks the subtitle-only variant by length, so the full printed
    # title reaches the worklist as one span instead of a truncated tier-1 wrap.
    if category == "work":
        singles = [form for form, _, _ in own if len(form.split()) == 1]
        multis = [(form, source) for form, _, source in own if len(form.split()) > 1]
        for short in singles:
            for long_form, source in multis:
                joined = f"{short}. {long_form}"
                if not _reaches_tier1(forms, surnames, joined):
                    _add_form(forms, joined, gid, category,
                              "work-title" + SUBTITLE_JOIN_SUFFIX, source)


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
    this channel reaches. Both spellings stay tier 2 in the lexicon: initials claim
    unrelated positions document-wide far too easily (the doc-1220 finding), and a pair
    several persons share simply becomes a multi-owner worklist candidate. Only the
    matcher's speaker-position rule lifts them (entity_matcher._speaker_initials).
    """
    if category != "person":
        return ()
    surname, forenames = _split_person_label(label)
    if not (surname and forenames and surname[0].isalpha() and forenames[0].isalpha()):
        return ()
    initial = forenames[0].upper()
    forms = [f"{initial}.{surname[0].upper()}."]
    # A hyphenated surname also abbreviates part by part ("G.D.K." for Dufour-Kowalska).
    parts = [part for part in surname.split("-") if part[:1].isalpha()]
    if len(parts) > 1:
        forms.append("".join(f"{letter}." for letter in [initial, *(p[0].upper() for p in parts)]))
    return tuple(form for compact in forms for form in (compact, compact.replace(".", ". ").rstrip()))


# --- small text helpers -----------------------------------------------------------


def _collapse(value: str) -> str:
    """One-space form with the typographic apostrophe folded to ASCII.

    E94 normalized the corpus text to U+2019 while list and cache carry U+0027;
    both sides fold at registration so a French elision matches either way. The
    scan projection folds identically (entity_matcher._normalize).
    """
    return " ".join(value.replace(chr(0x2019), "'").split())


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
