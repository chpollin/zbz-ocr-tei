"""Tests for the entity corpus digest (scripts.eval.entity_corpus_digest)."""

from scripts.eval.entity_corpus_digest import build_digest


def _cand(doc, gid, surface, rule, tier, context="ctx"):
    return {
        "doc": doc, "gid": gid, "category": "person", "surface": surface,
        "start": 0, "end": 1, "tier": tier, "rule": rule, "context": context,
    }


SCAN = {
    "totals": {"tier1": 4, "tier2": 3, "candidates": 7},
    "candidates": [
        _cand("100", "118557106", "Jaspers", "anchored-surname", 1, "la philosophie de Jaspers"),
        _cand("290", "118557106", "Jaspers", "anchored-surname", 1),
        _cand("100", "118557106", "Karl Jaspers", "full-name", 1),
        _cand("890", "5157117-3", "UNESCO", "org-token", 1),
        _cand("100", "4558181-2", "Psychopathologie", "short-title", 2),
        _cand("290", "118594893", "Platon", "bare-surname", 2),
        _cand("290", "118594893", "Platon", "bare-surname", 2),
    ],
}

LABELS = {"118557106": "Jaspers, Karl", "5157117-3": "UNESCO", "118594893": "Plato"}


def test_tier1_groups_by_entity_ordered_by_volume():
    digest = build_digest(SCAN, LABELS)
    jaspers = digest.index("Jaspers, Karl (118557106) | 3 hits in 2 docs")
    unesco = digest.index("UNESCO (5157117-3) | 1 hits in 1 docs")
    assert jaspers < unesco


def test_surface_lines_carry_rule_count_and_context():
    digest = build_digest(SCAN, LABELS)
    assert "- `Jaspers` | anchored-surname | 2x in 2 docs" in digest
    assert "la philosophie de Jaspers" in digest


def test_tier2_groups_by_rule_with_owner_labels():
    digest = build_digest(SCAN, LABELS)
    assert "### bare-surname | 2 candidates, 1 distinct surfaces" in digest
    assert "- `Platon` | 2x in 1 docs | Plato" in digest


def test_unknown_label_falls_back():
    digest = build_digest(SCAN, {})
    assert "(label unknown) (118557106)" in digest


def test_digest_is_deterministic():
    assert build_digest(SCAN, LABELS) == build_digest(SCAN, LABELS)
