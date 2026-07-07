"""Tests for the run-to-run stability pilot (scripts/eval/stability_pilot.py) and
the stability block loader in cer_statistics_full. The API-driven pilot run itself
is operator-gated; here the aggregation math and the artifact wiring are pinned."""

import json

from scripts.eval.stability_pilot import aggregate
from scripts.eval.cer_statistics_full import _load_stability_block


def test_aggregate_mean_std_range():
    res = aggregate({"570": [0.010, 0.012, 0.014], "830": [0.02, 0.02, 0.02]})
    d570 = res["per_doc"]["570"]
    assert abs(d570["mean"] - 0.012) < 1e-12
    assert abs(d570["std"] - 0.002) < 1e-12  # sample std of the arithmetic series
    assert abs(d570["range"] - 0.004) < 1e-12
    assert res["per_doc"]["830"]["std"] == 0.0
    assert res["summary"]["max_std"] == d570["std"]
    assert res["summary"]["max_range"] == d570["range"]


def test_aggregate_single_run_has_zero_std():
    res = aggregate({"890": [0.013]})
    assert res["per_doc"]["890"]["std"] == 0.0
    assert res["per_doc"]["890"]["range"] == 0.0


def test_stability_block_open_without_artifact(tmp_path, monkeypatch):
    import scripts.eval.cer_statistics_full as csf
    monkeypatch.setattr(csf, "PROJECT_ROOT", tmp_path)
    block = _load_stability_block()
    assert block["status"] == "open"
    assert block["per_doc_std"] is None


def test_stability_block_measured_from_artifact(tmp_path, monkeypatch):
    import scripts.eval.cer_statistics_full as csf
    monkeypatch.setattr(csf, "PROJECT_ROOT", tmp_path)
    audits = tmp_path / "output" / "audits"
    audits.mkdir(parents=True)
    (audits / "stability_pilot.json").write_text(json.dumps({
        "generated": "2026-07-07",
        "model": "test-model",
        "n_docs": 2,
        "n_runs": 3,
        "per_doc": {"570": {"cers": [0.01, 0.011, 0.012], "std": 0.001,
                            "mean": 0.011, "range": 0.002}},
        "summary": {"mean_std": 0.001, "max_std": 0.001, "max_range": 0.002},
    }), encoding="utf-8")
    block = _load_stability_block()
    assert block["status"] == "measured"
    assert block["n_runs"] == 3
    assert block["per_doc_std"] == {"570": 0.001}
    assert block["summary"]["max_std"] == 0.001
