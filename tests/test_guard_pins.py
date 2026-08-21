"""Two guards that the mutation audit of 2026-08-21 found pinned on one side only.

Both are thresholds whose lower side is tested elsewhere while the deciding side is not,
so a mutation of the comparison would pass the suite:

1. ``scripts.entity.entity_matcher.COVER_FIELD_MIN`` decides whether the first page of an
   E-Periodica scan counts as a library cover sheet and is therefore excluded from entity
   matching. ``tests/test_entity_matcher.py`` pins two fields (too few) and all four
   (enough); the boundary itself, exactly the minimum, was open.
2. ``scripts.eval.cer_statistics.paired_bootstrap_diff`` reports a two-sided p-value built
   by doubling the one-sided resample share. ``tests/test_cer_statistics.py`` pins the
   direction (small p for a clear effect, large p for none) but not the doubling, so a
   dropped factor of two would go unnoticed. The function exposes only the two-sided value;
   the doubling is pinned through its arithmetic consequence instead of by rebuilding the
   resampling in the test.
"""

from __future__ import annotations

import json

import pytest

from scripts.entity import entity_matcher as em
from scripts.eval.cer_statistics import paired_bootstrap_diff

# --- (a) cover sheet field threshold ---------------------------------------------

TEI_HEAD = (
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    '<TEI xmlns="http://www.tei-c.org/ns/1.0">\n'
    "<teiHeader><fileDesc><titleStmt><title>Test</title></titleStmt></fileDesc></teiHeader>\n"
)


def _tei(body: str) -> str:
    return TEI_HEAD + f"<text><body>{body}</body></text>\n</TEI>\n"


@pytest.fixture
def lex(tmp_path):
    """Minimal closed-world lexicon: one person and one organisation, no GND cache."""
    entities = tmp_path / "all_entities.json"
    entities.write_text(json.dumps({
        "persons": [{"GND_id": "118557106", "name": "Jaspers, Karl",
                     "listBibl": [], "editor_reviewed": False}],
        "organisations": [{"GND_id": "5157117-3", "orgName": "UNESCO",
                           "listBibl": [], "editor_reviewed": False}],
        "works": [],
    }), encoding="utf-8")
    return em.build_lexicon(entities, tmp_path / "no_cache.json")


# The four field lines of an E-Periodica cover sheet, in the order they are printed.
FIELD_LINES = [
    "Zeitschrift: Schweizerische Lehrerzeitung",
    "Herausgeber: Verein",
    "Band: 105",
    "Heft: 3",
]
# A mention inside the candidate cover zone and one outside it; the second shows the
# matcher ran at all, so an empty first-page result means exclusion and not a dead run.
INSIDE = "Ein Vortrag von Karl Jaspers ist angekuendigt."
OUTSIDE = "Die UNESCO tagte in Paris im Jahr 1961."


def _cover_page(field_count: int) -> str:
    """First page with `field_count` field lines plus a name, second page with a mention."""
    fields = "".join(f"<p>{line}</p>" for line in FIELD_LINES[:field_count])
    return _tei(f'<pb n="1"/>{fields}<p>{INSIDE}</p>'
                f'<pb n="2"/><p>{OUTSIDE}</p>')


def _surfaces(xml: str, lex) -> list[str]:
    return [c["surface"] for c in em.find_candidates(xml, lex)]


def test_exactly_the_minimum_number_of_cover_fields_is_a_cover_sheet(lex):
    """Three field lines, the threshold COVER_FIELD_MIN, already exclude the first page."""
    assert _surfaces(_cover_page(3), lex) == ["UNESCO"]


def test_one_field_above_the_minimum_is_still_a_cover_sheet(lex):
    """The threshold is a lower bound: a fourth field line does not undo the exclusion."""
    assert _surfaces(_cover_page(4), lex) == ["UNESCO"]


def test_one_field_below_the_minimum_leaves_the_page_matched(lex):
    """Two field lines are ordinary text; the name on that page stays a candidate."""
    assert _surfaces(_cover_page(2), lex) == ["Karl Jaspers", "UNESCO"]


def test_cover_sheet_zone_ends_at_the_second_page_break(lex):
    """Only the first page is apparatus; a field-shaped line later in the text is not."""
    fields = "".join(f"<p>{line}</p>" for line in FIELD_LINES[:3])
    xml = _tei(f'<pb n="1"/>{fields}'
               f'<pb n="2"/><p>{FIELD_LINES[0]}</p><p>{INSIDE}</p>')
    assert _surfaces(xml, lex) == ["Karl Jaspers"]


# --- (b) two-sided p-value of the paired bootstrap --------------------------------

# The resample share is a multiple of 1/n_resamples, so a doubled share lands on an even
# multiple. Scaling the reported p by n_resamples therefore has to give an even integer;
# an undoubled (one-sided) value would land on odd multiples as well.
_RESAMPLES = 1000
_MODERATE_DIFFS = [0.0, 0.01, -0.005, 0.02, 0.001, 0.03, -0.002, 0.015]


def _scaled(p: float) -> float:
    return p * _RESAMPLES


def test_zero_effect_yields_a_p_value_of_exactly_one():
    """A point estimate of zero means a one-sided share of 0.5, doubled and capped at 1."""
    result = paired_bootstrap_diff([0.0] * 8, n_resamples=_RESAMPLES, seed=42)
    assert result["mean_diff"] == 0.0
    assert result["p_two_sided"] == 1.0


def test_symmetric_differences_around_zero_yield_a_p_value_of_one():
    """Differences that cancel exactly are the no-effect case, whatever their spread."""
    result = paired_bootstrap_diff([-0.02, -0.01, 0.01, 0.02],
                                   n_resamples=_RESAMPLES, seed=42)
    assert result["p_two_sided"] == 1.0
    assert result["ci_low"] < 0 < result["ci_high"]


def test_two_sided_p_is_the_doubled_resample_share():
    """A moderate effect: the reported p sits on an even multiple of 1/n_resamples."""
    result = paired_bootstrap_diff(_MODERATE_DIFFS, n_resamples=_RESAMPLES, seed=42)
    p = result["p_two_sided"]
    assert 0.0 < p < 1.0
    assert _scaled(p) == pytest.approx(round(_scaled(p)))
    assert round(_scaled(p)) % 2 == 0


def test_the_doubled_share_is_the_reported_significance_level():
    """The doubling is not cosmetic: the same data one-sided would read half as extreme."""
    p = paired_bootstrap_diff(_MODERATE_DIFFS, n_resamples=_RESAMPLES, seed=42)["p_two_sided"]
    assert p == pytest.approx(0.024)


def test_sign_of_the_effect_does_not_change_the_p_value():
    """Negating every difference mirrors the resamples; the branch for a negative point
    estimate must report the same significance as the positive one."""
    positive = paired_bootstrap_diff(_MODERATE_DIFFS, n_resamples=_RESAMPLES, seed=42)
    negative = paired_bootstrap_diff([-d for d in _MODERATE_DIFFS],
                                     n_resamples=_RESAMPLES, seed=42)
    assert negative["mean_diff"] == -positive["mean_diff"]
    assert negative["p_two_sided"] == positive["p_two_sided"]


@pytest.mark.parametrize("diffs", [
    [0.0] * 8,
    [-1.0] * 7 + [10.0],
    [-1.0] * 8 + [9.0, 9.0],
    _MODERATE_DIFFS,
    [0.05] * 6 + [0.04, 0.06],
])
def test_p_value_stays_a_probability(diffs):
    """The doubling is capped: a skewed difference distribution must not report p above 1."""
    p = paired_bootstrap_diff(diffs, n_resamples=_RESAMPLES, seed=42)["p_two_sided"]
    assert 0.0 <= p <= 1.0
