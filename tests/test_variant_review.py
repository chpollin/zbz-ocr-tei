"""Tests for the reviewed GND variant forms (data/entities/variant_review.json).

The review is committed data, not generated at test time, so the suite runs against
the real file and the real cache: every form the cache contributes to the matcher
lexicon carries exactly one verdict, and no verdict invents a form.
"""

import json

import pytest

from scripts.config import DATA_DIR
from scripts.entity.entity_matcher import _collapse

CACHE_FILE = DATA_DIR / "entities" / "gnd_cache.json"
REVIEW_FILE = DATA_DIR / "entities" / "variant_review.json"
CATEGORIES = ("persons", "organisations", "works")
VERDICTS = ("approve", "suspect", "reject")
CATEGORY_LABEL = {"persons": "name", "organisations": "orgName", "works": "title"}

# The whole module runs against the committed review and cache files.
pytestmark = pytest.mark.requires_mirror


def _load(path):
    if not path.exists():
        pytest.skip(f"{path.name} not built")
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def review():
    return _load(REVIEW_FILE)


@pytest.fixture(scope="module")
def cache():
    return _load(CACHE_FILE)


def cache_forms(entry):
    """The forms one cache entry contributes, in the order entity_matcher takes them."""
    forms = []
    for value in [entry.get("preferred_name"), *(entry.get("variant_names") or [])]:
        form = _collapse(str(value or ""))
        if form and form not in forms:
            forms.append(form)
    return forms


def reviewed_forms(review):
    """Verdict keys in registration identity: folded like every lexicon form (E111)."""
    for category in CATEGORIES:
        for gid, bucket in review[category].items():
            for form, entry in bucket["verdicts"].items():
                yield category, gid, _collapse(form), entry


def test_top_level_shape():
    review = _load(REVIEW_FILE)
    assert set(review) == {"reviewed", "source_cache_retrieved", "scope",
                           "verdict_values", *CATEGORIES}
    assert set(review["verdict_values"]) == set(VERDICTS)
    assert review["reviewed"]
    for category in CATEGORIES:
        assert isinstance(review[category], dict)


def test_source_cache_retrieved_matches_the_cache(review, cache):
    assert review["source_cache_retrieved"] == cache["retrieved"]


def test_every_verdict_is_a_known_value_with_a_reason(review):
    for _category, gid, form, entry in reviewed_forms(review):
        assert set(entry) == {"verdict", "reason"}, (gid, form)
        assert entry["verdict"] in VERDICTS, (gid, form)
        assert isinstance(entry["reason"], str), (gid, form)
        assert entry["reason"].strip(), (gid, form)


def test_every_reviewed_form_exists_in_the_cache(review, cache):
    entries = cache["entries"]
    for _category, gid, form, _entry in reviewed_forms(review):
        assert gid in entries, gid
        assert form in cache_forms(entries[gid]), (gid, form)


def test_every_cache_form_carries_exactly_one_verdict(review, cache):
    reviewed = {}
    for _category, gid, form, _entry in reviewed_forms(review):
        assert (gid, form) not in reviewed, (gid, form)
        reviewed[(gid, form)] = True
    for gid, entry in cache["entries"].items():
        if entry.get("http_status") != 200:
            continue
        for form in cache_forms(entry):
            assert (gid, form) in reviewed, (gid, form)


def test_defective_gnd_ids_are_not_reviewed(review, cache):
    """A 404 entry contributes nothing to the lexicon, so it carries no verdict."""
    dead = {gid for gid, entry in cache["entries"].items()
            if entry.get("http_status") != 200}
    assert dead
    reviewed_ids = {gid for _c, gid, _f, _e in reviewed_forms(review)}
    assert not (dead & reviewed_ids)


def test_bearers_are_filed_under_their_curated_category(review):
    entities = _load(DATA_DIR / "entities" / "all_entities.json")
    for category in CATEGORIES:
        listed = {str(raw.get("GND_id") or "").strip() for raw in entities[category]}
        for gid, bucket in review[category].items():
            assert gid in listed, (category, gid)
            assert "headword" in bucket
            assert isinstance(bucket["verdicts"], dict)
            assert bucket["verdicts"], gid


def test_initials_only_forms_are_rejected(review):
    """The class the matcher drops deterministically must not be approved."""
    from scripts.entity.entity_matcher import _is_initials_only

    for _category, gid, form, entry in reviewed_forms(review):
        if _is_initials_only(form.replace(",", " ")):
            assert entry["verdict"] == "reject", (gid, form)


def test_known_damage_cases_are_not_approved(review):
    """The two cases that produced false hits in operation stay out of tier 1."""
    pestalozzi = review["persons"]["118592912"]["verdicts"]
    assert pestalozzi["J. H."] == {"verdict": "reject",
                                   "reason": "initials-only (already filtered)"}
    assert pestalozzi["J.H."]["verdict"] == "reject"
    assert review["persons"]["118557394"]["verdicts"]["Jérémie"]["verdict"] == "suspect"
