"""Tests for the evaluation sampler (scripts/entity/entity_eval_sample).

The sampler draws the two reproducible samples of the entity evaluation workflow
(knowledge/verification.md, section "1. Draw"): 300 tier-1 marks stratified by
category and rule family, and 40 pages stratified by layout type and language.

All fixtures are synthetic: a mini scan, a mini catalog and two mini TEIs in tmp_path.
No test reads the real corpus scan, which is volatile by design; the corpus run is an
operator step outside the suite. GND ids in the fixtures are placeholders.
"""

from __future__ import annotations

import hashlib
import json

import pytest

from scripts.entity.entity_eval_sample import (
    PRECISION_MIN_PER_CELL,
    RECALL_MIN_PER_CELL,
    allocate,
    facsimile_path,
    main,
    page_of_offset,
    page_starts,
    run,
)

# --- fixtures ---------------------------------------------------------------

_TEI_TEMPLATE = (
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    '<TEI xmlns="http://www.tei-c.org/ns/1.0"><teiHeader><fileDesc/></teiHeader>'
    '<text><body><div type="text">'
    '<pb n="1" facs="p1"/><p>Karl Jaspers schrieb ueber die Existenz.</p>'
    '<pb n="2" facs="p2"/><p>Jeanne Hersch antwortete in Genf.</p>'
    "</div></body></text></TEI>"
)


def _candidate(doc: str, surface: str, start: int, *, tier: int = 1,
               category: str = "person", rule: str = "full-name",
               gid: str = "TEST-0001") -> dict:
    return {
        "doc": doc,
        "gid": gid,
        "category": category,
        "surface": surface,
        "start": start,
        "end": start + len(surface),
        "tier": tier,
        "rule": rule,
        "alternatives": [],
        "matched_form": surface,
        "form_source": "headword",
        "context": f"... {surface} ...",
    }


def _scan_payload() -> dict:
    """A scan with three categories, two rule families each and both tiers.

    Cell sizes are deliberately lopsided so proportionality is observable, and one
    cell holds a single candidate so the minimum-coverage cap is exercised.
    """
    first = _TEI_TEMPLATE.index("Karl Jaspers")
    second = _TEI_TEMPLATE.index("Jeanne Hersch")
    candidates: list[dict] = []
    for i in range(60):
        candidates.append(_candidate("100", "Karl Jaspers", first,
                                     category="person", rule="full-name",
                                     gid=f"TEST-{i:04d}"))
    for i in range(12):
        candidates.append(_candidate("110", "Jeanne Hersch", second,
                                     category="person", rule="anchored-surname:suspect",
                                     gid=f"TEST-1{i:03d}"))
    for i in range(8):
        candidates.append(_candidate("100", "Karl Jaspers", first,
                                     category="work", rule="work-variant:ambiguous",
                                     gid=f"TEST-2{i:03d}"))
    candidates.append(_candidate("110", "Jeanne Hersch", second,
                                 category="organisation", rule="org-token",
                                 gid="TEST-3000"))
    # tier 2 is worklist material and must never be drawn
    for i in range(30):
        candidates.append(_candidate("100", "Karl Jaspers", first, tier=2,
                                     category="person", rule="bare-surname",
                                     gid=f"TEST-4{i:03d}"))
    return {
        "generated_from": {"code": "entity_matcher"},
        "totals": {"tier1": 81, "tier2": 30, "candidates": len(candidates)},
        "candidates": candidates,
    }


def _catalog_payload() -> dict:
    documents = [
        {"id": "100", "type": "A", "lang": "FR", "page_count": 40},
        {"id": "110", "type": "A", "lang": "FR", "page_count": 20},
        {"id": "120", "type": "B", "lang": "DE", "page_count": 10},
        {"id": "130", "type": "C", "lang": "DE/FR", "page_count": 4},
        {"id": "140", "type": "D", "lang": "IT", "page_count": 2},
    ]
    return {"generator": "test", "documents": documents}


@pytest.fixture()
def env(tmp_path):
    """Scan, catalog and two mini TEIs on disk; returns the paths as a dict."""
    scan = tmp_path / "entity_corpus_scan.json"
    scan.write_text(json.dumps(_scan_payload(), ensure_ascii=False), encoding="utf-8")
    catalog = tmp_path / "catalog.json"
    catalog.write_text(json.dumps(_catalog_payload(), ensure_ascii=False), encoding="utf-8")
    tei_dir = tmp_path / "tei_final"
    tei_dir.mkdir()
    for doc in ("100", "110"):
        (tei_dir / f"{doc}_final.xml").write_text(_TEI_TEMPLATE, encoding="utf-8")
    return {"scan": scan, "catalog": catalog, "tei_dir": tei_dir,
            "out": tmp_path / "eval_sample"}


def _run(env, **kwargs):
    params = {"scan_path": env["scan"], "catalog_path": env["catalog"],
              "out_dir": env["out"], "tei_dir": env["tei_dir"],
              "precision_n": 30, "recall_pages": 12}
    params.update(kwargs)
    return run(**params)


def _read(out_dir, name):
    return json.loads((out_dir / name).read_text(encoding="utf-8"))


# --- allocation -------------------------------------------------------------


def test_allocate_gives_every_cell_the_minimum():
    alloc = allocate({"big": 100, "small": 4, "tiny": 1}, total=30, minimum=3)
    assert alloc["small"] >= 3
    assert alloc["tiny"] == 1  # fewer than the minimum available: take all
    assert sum(alloc.values()) == 30


def test_allocate_is_roughly_proportional():
    alloc = allocate({"big": 900, "mid": 90, "small": 10}, total=100, minimum=3)
    assert sum(alloc.values()) == 100
    assert alloc["big"] > alloc["mid"] > alloc["small"]
    assert alloc["big"] > 70


def test_allocate_never_exceeds_availability():
    alloc = allocate({"a": 2, "b": 3}, total=50, minimum=3)
    assert alloc == {"a": 2, "b": 3}


# --- page assignment --------------------------------------------------------


def test_page_of_offset_maps_across_two_pb():
    starts = page_starts(_TEI_TEMPLATE)
    assert len(starts) == 2
    before = _TEI_TEMPLATE.index("<teiHeader")
    first = _TEI_TEMPLATE.index("Karl Jaspers")
    second = _TEI_TEMPLATE.index("Jeanne Hersch")
    assert page_of_offset(starts, before) == 1
    assert page_of_offset(starts, first) == 1
    assert page_of_offset(starts, second) == 2


def test_facsimile_path_is_zero_padded():
    assert facsimile_path("100", 7) == "docs/images/100/100_p007.png"
    assert facsimile_path("20", 208) == "docs/images/20/20_p208.png"


# --- precision sample -------------------------------------------------------


def test_precision_cases_carry_the_full_schema(env):
    _run(env)
    cases = _read(env["out"], "precision_cases.json")
    assert len(cases) == 30
    assert cases[0]["case_id"] == "p001"
    assert [c["case_id"] for c in cases] == [f"p{i:03d}" for i in range(1, 31)]
    expected = {"case_id", "doc", "page", "surface", "start", "end", "gid", "category",
                "rule", "matched_form", "form_source", "context", "facsimile",
                "verdict", "reason"}
    for case in cases:
        assert set(case) == expected
        assert case["verdict"] is None and case["reason"] is None
        assert case["page"] == (1 if case["doc"] == "100" else 2)
        assert case["facsimile"] == facsimile_path(case["doc"], case["page"])


def test_precision_draws_tier1_only(env):
    _run(env)
    cases = _read(env["out"], "precision_cases.json")
    drawn = {c["gid"] for c in cases}
    assert not any(gid.startswith("TEST-4") for gid in drawn)  # tier 2 gids
    assert len(drawn) == len(cases)  # no candidate drawn twice


def test_precision_strata_respect_the_minimum(env):
    manifest = _run(env)
    strata = {tuple(row["cell"]): row for row in manifest["precision"]["strata"]}
    assert set(strata) == {("person", "full-name"), ("person", "anchored-surname"),
                           ("work", "work-variant"), ("organisation", "org-token")}
    assert strata[("organisation", "org-token")]["drawn"] == 1  # only one available
    assert strata[("work", "work-variant")]["drawn"] >= PRECISION_MIN_PER_CELL
    assert strata[("person", "full-name")]["drawn"] > strata[("person", "anchored-surname")]["drawn"]
    assert sum(row["drawn"] for row in manifest["precision"]["strata"]) == 30


def test_precision_page_is_null_without_final_tei(env):
    payload = _scan_payload()
    payload["candidates"].append(_candidate("999", "Karl Jaspers", 10,
                                            category="work", rule="work-title",
                                            gid="TEST-9999"))
    env["scan"].write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    manifest = _run(env)
    cases = _read(env["out"], "precision_cases.json")
    orphan = [c for c in cases if c["doc"] == "999"]
    assert orphan and orphan[0]["page"] is None and orphan[0]["facsimile"] is None
    assert manifest["precision"]["without_page"] == len(orphan)


# --- recall sample ----------------------------------------------------------


def test_recall_pages_cover_every_cell(env):
    manifest = _run(env)
    pages = _read(env["out"], "recall_pages.json")
    assert len(pages) == 12
    assert [p["case_id"] for p in pages] == [f"r{i:03d}" for i in range(1, 13)]
    expected = {"case_id", "doc", "page", "facsimile", "lang", "layout_type", "mentions"}
    for page in pages:
        assert set(page) == expected
        assert page["mentions"] is None
        assert page["facsimile"] == facsimile_path(page["doc"], page["page"])
    strata = {tuple(row["cell"]): row for row in manifest["recall"]["strata"]}
    assert set(strata) == {("A", "FR"), ("B", "DE"), ("C", "DE/FR"), ("D", "IT")}
    assert all(row["drawn"] >= RECALL_MIN_PER_CELL for row in strata.values())
    assert strata[("A", "FR")]["drawn"] > strata[("D", "IT")]["drawn"]


def test_recall_pages_stay_inside_the_document(env):
    _run(env)
    pages = _read(env["out"], "recall_pages.json")
    limits = {d["id"]: d["page_count"] for d in _catalog_payload()["documents"]}
    for page in pages:
        assert 1 <= page["page"] <= limits[page["doc"]]
    assert len({(p["doc"], p["page"]) for p in pages}) == len(pages)


def test_recall_carries_catalog_metadata(env):
    _run(env)
    pages = _read(env["out"], "recall_pages.json")
    meta = {d["id"]: d for d in _catalog_payload()["documents"]}
    for page in pages:
        assert page["lang"] == meta[page["doc"]]["lang"]
        assert page["layout_type"] == meta[page["doc"]]["type"]


# --- manifest, determinism, side effects ------------------------------------


def test_manifest_documents_seed_sources_and_strata(env):
    manifest = _run(env)
    assert manifest["seed"] == 42
    scan = manifest["sources"]["scan"]
    assert scan["candidates"] == 111 and scan["tier1"] == 81
    assert scan["modified"] and scan["size_bytes"] > 0
    catalog = manifest["sources"]["catalog"]
    assert catalog["documents"] == 5 and catalog["pages"] == 76
    assert manifest["precision"]["requested"] == 30
    assert manifest["precision"]["drawn"] == 30
    for row in manifest["precision"]["strata"]:
        assert set(row) == {"cell", "available", "drawn"}
    for row in manifest["recall"]["strata"]:
        assert set(row) == {"cell", "available_pages", "available_docs", "drawn"}
    assert (env["out"] / "sample_manifest.json").exists()


def test_run_is_deterministic(env, tmp_path):
    _run(env)
    first = {name: (env["out"] / name).read_bytes()
             for name in ("precision_cases.json", "recall_pages.json",
                          "sample_manifest.json")}
    second_dir = tmp_path / "again"
    _run(env, out_dir=second_dir)
    for name, payload in first.items():
        assert (second_dir / name).read_bytes() == payload


def test_seed_changes_the_draw(env, tmp_path):
    _run(env)
    base = _read(env["out"], "precision_cases.json")
    other_dir = tmp_path / "seed7"
    _run(env, out_dir=other_dir, seed=7)
    other = json.loads((other_dir / "precision_cases.json").read_text(encoding="utf-8"))
    assert [c["gid"] for c in base] != [c["gid"] for c in other]


def test_out_dir_is_created_and_sources_untouched(env):
    digests = {p: hashlib.sha256(p.read_bytes()).hexdigest()
               for p in (env["scan"], env["catalog"],
                         env["tei_dir"] / "100_final.xml")}
    assert not env["out"].exists()
    _run(env)
    assert env["out"].is_dir()
    for path, digest in digests.items():
        assert hashlib.sha256(path.read_bytes()).hexdigest() == digest


def test_cli_writes_the_three_files(env, capsys):
    exit_code = main([
        "--scan", str(env["scan"]),
        "--catalog", str(env["catalog"]),
        "--out", str(env["out"]),
        "--precision-n", "10",
        "--recall-pages", "5",
        "--tei-dir", str(env["tei_dir"]),
    ])
    assert exit_code == 0
    assert len(_read(env["out"], "precision_cases.json")) == 10
    assert len(_read(env["out"], "recall_pages.json")) == 5
    out = capsys.readouterr().out
    assert out.encode("ascii", "strict")  # ASCII-safe console output
