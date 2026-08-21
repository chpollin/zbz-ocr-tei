"""Tests for scripts/entity/entity_verdict_guard.py.

Synthetic store and scan fixtures only; the classification table of the module
docstring drives the cases one by one. The real store (300 marks, 67 recall
mentions) is exercised end to end by the CLI run, not here.
"""

from __future__ import annotations

import json

from scripts.entity import entity_verdict_guard as vg

DIGEST = "a" * 64


def _mark(verdict, start=10, end=16, doc="1", gid="g1", surface="Hersch",
          text_sha256=DIGEST, page=1):
    return {"doc": doc, "page": page, "gid": gid, "surface": surface,
            "verdict": verdict, "start": start, "end": end,
            "text_sha256": text_sha256}


def _cand(tier, start=10, end=16, doc="1", gid="g1", surface="Hersch",
          rule="full-name", page=1):
    return {"doc": doc, "page": page, "gid": gid, "surface": surface,
            "tier": tier, "rule": rule, "start": start, "end": end}


def _classify(mark, candidates, digests=None):
    return vg.classify_mark(
        mark, vg._span_index(candidates), vg._doc_index(candidates),
        digests if digests is not None else {"1": DIGEST},
    )


# --- adjudicated marks ------------------------------------------------------------


def test_correct_mark_still_tier1_is_kept():
    cls, current = _classify(_mark("correct"), [_cand(1)])
    assert cls == "kept_tier1"
    assert current["rule"] == "full-name"


def test_correct_mark_now_tier2_is_a_move_not_a_violation():
    cls, _ = _classify(_mark("correct"), [_cand(2, rule="full-name:running-head")])
    assert cls == "moved_to_worklist"
    assert cls not in vg.MARK_VIOLATIONS | vg.RECALL_VIOLATIONS


def test_correct_mark_with_widened_span_still_counts_as_kept():
    cls, current = _classify(_mark("correct"), [_cand(1, start=4, end=16)])
    assert cls == "kept_tier1_span_changed"
    assert current["start"] == 4


def test_correct_mark_gone_is_a_violation():
    cls, _ = _classify(_mark("correct"), [])
    assert cls == "missing"
    assert cls in vg.MARK_VIOLATIONS


def test_wrong_entity_gone_or_demoted_is_repaired():
    assert _classify(_mark("wrong_entity"), [])[0] == "gone"
    assert _classify(_mark("wrong_entity"), [_cand(2)])[0] == "demoted"


def test_wrong_entity_still_tier1_is_a_violation():
    cls, _ = _classify(_mark("wrong_entity"), [_cand(1)])
    assert cls == "still_tier1"
    assert cls in vg.MARK_VIOLATIONS


def test_wrong_span_replaced_by_a_different_span_is_a_repair():
    # the Loyola case: the wrong short span gave way to the full name span
    cls, current = _classify(_mark("wrong_span"), [_cand(1, start=2, end=16)])
    assert cls == "span_changed"
    assert current["start"] == 2


def test_undecidable_marks_are_skipped():
    assert _classify(_mark("undecidable"), [_cand(1)])[0] == "skipped_undecidable"


def test_changed_text_shields_the_mark_from_span_comparison():
    cls, _ = _classify(_mark("correct"), [], digests={"1": "b" * 64})
    assert cls == "text_changed"
    assert cls not in vg.MARK_VIOLATIONS | vg.RECALL_VIOLATIONS


# --- facsimile-read recall mentions ----------------------------------------------


def _recall(status, surface="HERSCH", doc="1", page=1, gid="g1"):
    return {"doc": doc, "page": page, "gid": gid, "surface": surface, "status": status}


def _classify_recall(mention, candidates):
    return vg.classify_recall(mention, vg._page_index(candidates))


def test_missed_mention_found_now_reports_the_tier():
    cands = [_cand(1, surface="Jeanne Hersch")]
    cls, current = _classify_recall(_recall("missed"), cands)
    assert cls == "now_tier1"
    assert current["surface"] == "Jeanne Hersch"


def test_missed_mention_surface_matches_case_insensitively_and_by_containment():
    cls, _ = _classify_recall(_recall("missed", surface="HERSCH"),
                              [_cand(2, surface="Hersch")])
    assert cls == "now_worklist"


def test_missed_mention_still_missing_is_the_open_gap_list():
    cls, _ = _classify_recall(_recall("missed"), [])
    assert cls == "still_missing"
    assert cls not in vg.MARK_VIOLATIONS | vg.RECALL_VIOLATIONS


def test_adjudicated_hit_that_vanished_is_a_violation():
    cls, _ = _classify_recall(_recall("hit"), [])
    assert cls == "lost"
    assert cls in vg.RECALL_VIOLATIONS


def test_worklist_mention_may_stay_or_upgrade():
    assert _classify_recall(_recall("on_worklist"), [_cand(2)])[0] == "still_listed"
    assert _classify_recall(_recall("on_worklist"), [_cand(1)])[0] == "upgraded_tier1"


# --- report ----------------------------------------------------------------------


def _store():
    return {
        "marks": [_mark("correct"), _mark("wrong_entity", gid="g2", start=30, end=36),
                  _mark("undecidable", start=50, end=56)],
        "recall_mentions": [_recall("missed"), _recall("hit", surface="Hersch")],
    }


def _cands():
    return [_cand(1), _cand(1, gid="g2", start=30, end=36)]


def test_guard_report_counts_and_collects_violations():
    report = vg.guard_report(_store(), _cands(), {"1": DIGEST})
    assert report["summary"]["marks"] == {
        "kept_tier1": 1, "skipped_undecidable": 1, "still_tier1": 1}
    assert report["summary"]["recall"] == {"kept_tier1": 1, "now_tier1": 1}
    assert report["summary"]["violations"] == 1
    assert report["violations"][0]["class"] == "still_tier1"


def test_guard_report_is_deterministic():
    a = vg.guard_report(_store(), _cands(), {"1": DIGEST})
    b = vg.guard_report(_store(), _cands(), {"1": DIGEST})
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)
