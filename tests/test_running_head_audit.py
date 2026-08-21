"""Tests for the deterministic page-apparatus detector (scripts.entity.running_head_audit).

The detector is a measurement instrument: it locates the zones of the repeated page
apparatus (Kolumnentitel, running feet, delivery stamps) so a later suppression step can
decide about them. These tests pin the detection contract on synthetic TEI (recurrence with
varying page numbers, apparatus at the page end and in the page middle, the alternating
verso/recto pair, the share floor of a long document, and the two exemptions that keep an
opening-page byline in scope) and the aggregation contract of the audit report.
"""

import hashlib
import json

import pytest

from scripts.entity.running_head_audit import (
    CONTAINS_LENGTH_FACTOR,
    EDGE_SEGMENTS,
    MAX_HEAD_CHARS,
    MIN_ALTERNATION_PAGES,
    MIN_RECURRENCE,
    MIN_RECURRENCE_SHARE,
    audit_corpus,
    build_report,
    convention_precision,
    detect_document,
    is_running_head_mark,
    normalize_head,
    tagged_waves,
    zone_lookup,
)
from tests.conftest import tei_doc, tei_header


def _tei(pages: list[str]) -> str:
    """A minimal final TEI whose body carries one <pb> per entry of `pages`."""
    body = "".join(f'<pb facs="#facs_{i}" n="{i}" />{content}'
                   for i, content in enumerate(pages, start=1))
    return tei_doc(f'<div n="1">{body}</div>', header=tei_header())


def _body(page: int) -> str:
    """A body paragraph unique to a page, long enough to stay out of the head window."""
    return (f"<p>Le passage propre de la page {page} poursuit un raisonnement qui ne se "
            f"repete nulle part ailleurs dans ce document de test numero {page}.</p>")


def _forms(patterns) -> set[str]:
    return {p["form"] for p in patterns}


def _pattern(patterns, form):
    return next(p for p in patterns if p["form"] == form)


# ---------------------------------------------------------------------------
# Normalization
# ---------------------------------------------------------------------------

def test_normalize_collapses_whitespace_and_casefolds():
    assert normalize_head("  JEANNE   Hersch\n ") == "jeanne hersch"


def test_normalize_strips_leading_and_trailing_page_numbers():
    # the printed folio varies per page; the head itself must survive as one key
    assert normalize_head("148 [Mlle J. Hersch.]") == normalize_head("150 [Mlle J. Hersch.]")
    assert normalize_head("Hersch: Le combat 27") == "hersch: le combat"


def test_normalize_folds_diacritics_so_ocr_variants_share_one_key():
    assert normalize_head("IDÉOLOGIES ET RÉALITÉ") == normalize_head("IDEOLOGIES ET REALITE")
    assert normalize_head("IDÉOLOGIES ET RÉALITÉ") == "ideologies et realite"


def test_normalize_folds_apostrophe_variants():
    assert normalize_head("dell’essere") == normalize_head("dell'essere")


def test_normalize_drops_inline_markup_but_keeps_the_words():
    assert normalize_head('<hi rendition="#i">Jeanne</hi> Hersch') == "jeanne hersch"


def test_normalize_of_a_pure_page_number_is_empty():
    assert normalize_head("118") == ""


# ---------------------------------------------------------------------------
# Detection
# ---------------------------------------------------------------------------

def test_repeated_head_with_varying_page_numbers_is_detected():
    pages = [f"<p>{148 + 2 * i} [Mlle J. Hersch.]</p>{_body(i)}" for i in range(4)]
    result = detect_document(_tei(pages))
    assert result["pages"] == 4
    assert _forms(result["patterns"]) == {"mlle j. hersch"}
    pattern = _pattern(result["patterns"], "mlle j. hersch")
    assert pattern["kind"] == "primary"
    assert pattern["pages"] == [1, 2, 3, 4]
    assert len(pattern["zones"]) == 4


def test_recurrence_below_the_threshold_is_not_a_head():
    pages = [f"<p>Titre repete</p>{_body(i)}" for i in range(MIN_RECURRENCE - 1)]
    pages += [_body(9)]
    assert detect_document(_tei(pages))["patterns"] == []


def test_running_foot_at_the_page_end_is_detected():
    """The apparatus also arrives as the last paragraph of a page (doc 3190)."""
    pages = [f"{_body(i)}<p>Jaspers, University Youth</p>" for i in range(4)]
    pattern = _pattern(detect_document(_tei(pages))["patterns"],
                       "jaspers, university youth")
    assert pattern["pages"] == [1, 2, 3, 4]


def test_apparatus_spliced_into_the_page_middle_is_detected():
    """A scrambled reading order drops the head between two body paragraphs (doc 3070)."""
    pages = [f"{_body(i)}<p>Jeanne Hersch</p>{_body(i + 10)}" for i in range(4)]
    pattern = _pattern(detect_document(_tei(pages))["patterns"], "jeanne hersch")
    assert pattern["pages"] == [1, 2, 3, 4]


def test_alternating_verso_recto_pair_of_a_short_document_is_detected():
    """Halved by the alternation, neither form reaches the flat threshold (doc 2880)."""
    pages = []
    for i in range(4):
        head = "Von der Wirkung" if i % 2 == 0 else "Jeanne Hersch"
        pages.append(f"<p>{head}</p>{_body(i)}")
    patterns = detect_document(_tei(pages))["patterns"]
    assert _forms(patterns) == {"von der wirkung", "jeanne hersch"}
    verso = _pattern(patterns, "von der wirkung")
    recto = _pattern(patterns, "jeanne hersch")
    assert verso["kind"] == recto["kind"] == "alternating"
    assert len(verso["pages"]) == len(recto["pages"]) == MIN_ALTERNATION_PAGES
    assert verso["page_parity"] == "odd"
    assert recto["page_parity"] == "even"


def test_two_forms_on_the_same_pages_are_no_alternating_pair():
    # both forms stand on pages 1 and 3, so nothing alternates and nothing recurs enough
    pages = []
    for i in range(4):
        opening = "<p>Alpha Beta</p><p>Gamma Delta</p>" if i % 2 == 0 else ""
        pages.append(f"{opening}{_body(i)}")
    assert detect_document(_tei(pages))["patterns"] == []


def test_a_form_used_twice_on_a_page_is_content_there():
    """The page apparatus stands once per page; a second use is a mention of its own."""
    pages = [f"<p>Jeanne Hersch</p>{_body(i)}" for i in range(3)]
    pages.append(f"<p>Jeanne Hersch</p>{_body(9)}<p>Jeanne Hersch</p>")
    pattern = _pattern(detect_document(_tei(pages))["patterns"], "jeanne hersch")
    assert pattern["pages"] == [1, 2, 3]
    assert [e["page"] for e in pattern["exempt"]] == [4, 4]
    assert {e["reason"] for e in pattern["exempt"]} == {"repeated-on-page"}


def test_a_rare_form_in_a_long_document_stays_below_the_share_floor():
    """Three front-matter pages of a book are no running head (doc 20)."""
    pages = [f"<p>Jeanne Hersch</p>{_body(i)}" if i < 3 else _body(i) for i in range(80)]
    assert 80 * MIN_RECURRENCE_SHARE > MIN_RECURRENCE
    assert detect_document(_tei(pages))["patterns"] == []


def test_document_without_heads_yields_no_pattern():
    assert detect_document(_tei([_body(i) for i in range(6)]))["patterns"] == []


def test_empty_and_pure_number_segments_do_not_count_as_apparatus():
    pages = [f"<p>  </p><p>{100 + i}</p><p>Jeanne Hersch</p>{_body(i)}" for i in range(4)]
    patterns = detect_document(_tei(pages))["patterns"]
    assert _forms(patterns) == {"jeanne hersch"}
    assert _pattern(patterns, "jeanne hersch")["segment_positions"] == [0]


def test_long_recurring_page_opening_is_not_a_head():
    long_line = "A" + " wort" * MAX_HEAD_CHARS
    pages = [f"<p>{long_line}</p>{_body(i)}" for i in range(5)]
    assert detect_document(_tei(pages))["patterns"] == []


def test_speaker_label_at_the_page_start_is_not_a_head():
    pages = [(f"<sp><speaker>Jeanne Hersch</speaker>"
              f"<p>Replique propre a la page {i} du dialogue enregistre ici.</p></sp>")
             for i in range(5)]
    assert detect_document(_tei(pages))["patterns"] == []


def test_one_off_merged_variant_of_an_established_head_is_detected():
    # OCR glues the author prefix onto the title on a single page
    pages = [f"<p>Le combat de dragon</p>{_body(i)}" for i in range(4)]
    pages.append(f"<p>Hersch: Le combat de dragon</p>{_body(9)}")
    patterns = detect_document(_tei(pages))["patterns"]
    assert "hersch: le combat de dragon" in _forms(patterns)
    assert _pattern(patterns, "hersch: le combat de dragon")["kind"] == "contains"


def test_a_merged_variant_below_the_page_opening_is_exempt():
    """Further down the page the variant line is a signature, not the merged apparatus."""
    pages = [f"<p>Le combat de dragon</p>{_body(i)}" for i in range(4)]
    filler = "".join(_body(20 + i) for i in range(EDGE_SEGMENTS))
    pages.append(f"{filler}<p>Hersch: Le combat de dragon</p>")
    pattern = _pattern(detect_document(_tei(pages))["patterns"],
                       "hersch: le combat de dragon")
    assert pattern["zones"] == []
    assert [e["reason"] for e in pattern["exempt"]] == ["inner-variant"]


def test_a_long_line_merely_containing_a_head_form_is_not_detected():
    head = "Le combat de dragon"
    long_line = f"{head} " + "et la suite du raisonnement continue encore ici"
    assert len(long_line) > CONTAINS_LENGTH_FACTOR * len(head)
    pages = [f"<p>{head}</p>{_body(i)}" for i in range(4)]
    pages.append(f"<p>{long_line}</p>{_body(9)}")
    patterns = detect_document(_tei(pages))["patterns"]
    assert normalize_head(long_line) not in _forms(patterns)


# ---------------------------------------------------------------------------
# The opening page: a byline is no apparatus (E105/E108)
# ---------------------------------------------------------------------------

def test_a_byline_in_the_title_block_is_exempt():
    """<head> marks the title block of the opening page; its byline stays in scope."""
    opening = "<head>Jeanne Hersch</head><p>Le combat de dragon</p>"
    running = "<p>Jeanne Hersch</p><p>Le combat de dragon</p>"
    pages = [f"{opening}{_body(0)}"] + [f"{running}{_body(i)}" for i in range(1, 4)]
    pattern = _pattern(detect_document(_tei(pages))["patterns"], "jeanne hersch")
    assert pattern["pages"] == [2, 3, 4]
    assert [(e["page"], e["reason"]) for e in pattern["exempt"]] == [(1, "title-block")]


def test_a_byline_under_the_title_is_exempt_where_the_head_stands_alone():
    """Without a <head> the byline shows as the author following the title (doc 1830)."""
    pages = [f"<p>Philosophes critiques</p><p>Jeanne Hersch</p>{_body(0)}"]
    pages += [f"<p>Jeanne Hersch</p>{_body(i)}" for i in (1, 2)]
    pages += [f"<p>Jeanne Hersch</p>{_body(i)}<p>Philosophes critiques</p>"
              for i in (3, 4)]
    patterns = detect_document(_tei(pages))["patterns"]
    author = _pattern(patterns, "jeanne hersch")
    assert author["pages"] == [2, 3, 4, 5]
    assert [(e["page"], e["reason"]) for e in author["exempt"]] == [(1, "off-slot")]
    assert _pattern(patterns, "philosophes critiques")["pages"] == [1, 4, 5]


def test_the_head_keeps_its_zones_where_it_normally_follows_another_form():
    """A verso/recto pair merged into one line is apparatus on every page (doc 2030)."""
    pages = [f"<p>Jeanne Hersch</p><p>Karl Jaspers: il non possesso</p>{_body(i)}"
             for i in range(4)]
    pattern = _pattern(detect_document(_tei(pages))["patterns"],
                       "karl jaspers: il non possesso")
    assert pattern["pages"] == [1, 2, 3, 4]
    assert pattern["exempt"] == []


def test_zone_spans_index_the_raw_xml_stream():
    xml = _tei([f"<p>Jeanne Hersch</p>{_body(i)}" for i in range(4)])
    zone = detect_document(xml)["patterns"][0]["zones"][0]
    assert xml[zone["start"]:zone["end"]].strip() == "Jeanne Hersch"
    assert zone["text"] == "Jeanne Hersch"


def test_detection_is_stable_across_runs():
    xml = _tei([f"<p>{100 + i} Jeanne Hersch</p>{_body(i)}" for i in range(4)])
    assert json.dumps(detect_document(xml)) == json.dumps(detect_document(xml))


def test_document_without_body_is_tolerated():
    assert detect_document("<TEI><teiHeader /></TEI>") == {"pages": 0, "patterns": []}


# ---------------------------------------------------------------------------
# Zone lookup
# ---------------------------------------------------------------------------

def test_zone_lookup_resolves_doc_and_offset():
    xml = _tei([f"<p>Jeanne Hersch</p>{_body(i)}" for i in range(4)])
    documents = [dict(detect_document(xml), doc="42")]
    lookup = zone_lookup(documents)
    zone = documents[0]["patterns"][0]["zones"][0]
    assert lookup("42", zone["start"])["form"] == "jeanne hersch"
    assert lookup("42", zone["end"]) is None
    assert lookup("99", zone["start"]) is None


# ---------------------------------------------------------------------------
# Aggregation
# ---------------------------------------------------------------------------

@pytest.fixture
def corpus(tmp_path):
    """A two-document corpus on disk: one with a running head, one without."""
    with_head = _tei([f"<p>{100 + i} Jeanne Hersch</p>{_body(i)}" for i in range(4)])
    without_head = _tei([_body(i) for i in range(3)])
    (tmp_path / "10_final.xml").write_text(with_head, encoding="utf-8")
    (tmp_path / "20_final.xml").write_text(without_head, encoding="utf-8")
    return tmp_path, with_head, without_head


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def test_audit_corpus_reports_every_document_in_stable_order(corpus):
    tmp_path, _, _ = corpus
    documents = audit_corpus(tmp_path)
    assert [d["doc"] for d in documents] == ["10", "20"]
    assert documents[0]["patterns"] and documents[1]["patterns"] == []


def test_build_report_scores_recall_false_alarms_and_corpus_impact(corpus):
    tmp_path, with_head, without_head = corpus
    documents = audit_corpus(tmp_path)
    zone = documents[0]["patterns"][0]["zones"][0]
    body_offset = with_head.index("Le passage propre de la page 0")

    verdicts = {"marks": [
        # a true running-head mark, inside the zone -> recall hit
        {"doc": "10", "page": 1, "start": zone["start"] + 4, "end": zone["end"],
         "surface": "Jeanne Hersch", "verdict": "correct",
         "reason": "Running head of the printed page.", "text_sha256": _sha(with_head)},
        # a true running-head mark the detector misses -> recall miss
        {"doc": "10", "page": 1, "start": body_offset, "end": body_offset + 2,
         "surface": "Le", "verdict": "correct",
         "reason": "The running head intervenes, but this is body text.",
         "text_sha256": _sha(with_head)},
        # a body mark outside every zone -> neither hit nor false alarm
        {"doc": "20", "page": 1, "start": 5, "end": 7, "surface": "x",
         "verdict": "correct", "reason": "Body mention.", "text_sha256": _sha(without_head)},
        # a body mark inside a zone -> false alarm
        {"doc": "10", "page": 1, "start": zone["start"], "end": zone["end"],
         "surface": "Jeanne", "verdict": "correct", "reason": "Cover line.",
         "text_sha256": _sha(with_head)},
        # a rejected mark is out of scope for both counts
        {"doc": "10", "page": 1, "start": zone["start"], "end": zone["end"],
         "surface": "Jeanne", "verdict": "wrong_entity", "reason": "Wrong person.",
         "text_sha256": _sha(with_head)},
    ]}
    scan = {"candidates": [
        {"doc": "10", "start": zone["start"], "tier": 1},
        {"doc": "10", "start": body_offset, "tier": 1},
        {"doc": "20", "start": 5, "tier": 1},
        {"doc": "10", "start": zone["start"], "tier": 2},
    ]}

    report = build_report(documents, verdicts, scan, sources={})

    running_head = report["validation"]["running_head_marks"]
    assert running_head["total"] == 2
    assert running_head["detected"] == 1
    assert running_head["recall"] == 0.5
    assert [m["surface"] for m in running_head["misses"]] == ["Le"]

    other = report["validation"]["other_correct_marks"]
    assert other["total"] == 2
    assert other["in_zone"] == 1
    assert other["cases"][0]["surface"] == "Jeanne"
    assert other["cases"][0]["zone"]["form"] == "jeanne hersch"
    assert other["cases"][0]["reason"] == "Cover line."

    impact = report["corpus_impact"]
    assert impact["available"] is True
    assert impact["tier1_marks"] == 3
    assert impact["in_zone"] == 1
    assert impact["by_doc"] == {"10": 1}

    totals = report["totals"]
    assert totals["documents"] == 2
    assert totals["documents_with_heads"] == 1
    assert totals["zones"] == 4


def test_a_tagged_wave_is_read_by_its_tag_alone():
    """The newest wave names the apparatus both to assert and to deny a placement."""
    marks = [
        {"verdict": "wrong_entity", "source": {"wave": "w2"},
         "reason": "running head: the mark sits in the Kolumnentitel of page 160."},
        {"verdict": "correct", "source": {"wave": "w2"},
         "reason": "The mark sits on the signature, separate from the running head."},
        {"verdict": "correct", "source": {"wave": "w1"},
         "reason": "The running head of page 112 reads 'Jeanne Hersch'."},
    ]
    tagged = tagged_waves(marks)
    assert tagged == frozenset({"w2"})
    assert [is_running_head_mark(m, tagged) for m in marks] == [True, False, True]


def test_validation_pools_the_ground_truth_of_every_wave(corpus):
    """Detection is measured against every adjudicated wave, and the block names them."""
    tmp_path, with_head, _ = corpus
    documents = audit_corpus(tmp_path)
    zone = documents[0]["patterns"][0]["zones"][0]
    verdicts = {"snapshot": "2026-08-21", "marks": [
        {"doc": "10", "page": 1, "start": zone["start"] + 4, "end": zone["end"],
         "surface": "Jeanne Hersch", "verdict": "correct",
         "reason": "Running head of the printed page.", "text_sha256": _sha(with_head),
         "source": {"wave": "adjudication-2026-08-12"}},
        {"doc": "10", "page": 1, "start": zone["start"] + 4, "end": zone["end"],
         "surface": "Jeanne Hersch", "verdict": "correct",
         "reason": "Running head of the printed page.", "text_sha256": _sha(with_head),
         "source": {"wave": "adjudication-2026-08-21"}},
    ]}
    validation = build_report(documents, verdicts, None, sources={})["validation"]
    assert validation["snapshots"] == ["2026-08-12", "2026-08-21"]
    assert validation["running_head_marks"]["total"] == 2
    assert validation["running_head_marks"]["detected"] == 2


def test_build_report_flags_ground_truth_offset_drift(corpus):
    tmp_path, _, _ = corpus
    documents = audit_corpus(tmp_path)
    verdicts = {"marks": [
        {"doc": "10", "page": 1, "start": 0, "end": 1, "surface": "x", "verdict": "correct",
         "reason": "Running head.", "text_sha256": "0" * 64},
    ]}
    report = build_report(documents, verdicts, None, sources={})
    assert report["validation"]["tei_drift"] == ["10"]


def test_build_report_tolerates_a_missing_corpus_scan(corpus):
    tmp_path, _, _ = corpus
    report = build_report(audit_corpus(tmp_path), {"marks": []}, None, sources={})
    assert report["corpus_impact"]["available"] is False
    assert "reason" in report["corpus_impact"]


def test_build_report_tolerates_scan_candidates_without_a_page_field(corpus):
    tmp_path, _, _ = corpus
    documents = audit_corpus(tmp_path)
    zone = documents[0]["patterns"][0]["zones"][0]
    with_page = {"candidates": [{"doc": "10", "start": zone["start"], "tier": 1, "page": 1}]}
    without_page = {"candidates": [{"doc": "10", "start": zone["start"], "tier": 1}]}
    assert (build_report(documents, {"marks": []}, with_page, sources={})["corpus_impact"]
            == build_report(documents, {"marks": []}, without_page, sources={})["corpus_impact"])


def test_report_is_deterministic(corpus):
    tmp_path, _, _ = corpus
    documents = audit_corpus(tmp_path)
    first = json.dumps(build_report(documents, {"marks": []}, None, sources={}))
    second = json.dumps(build_report(audit_corpus(tmp_path), {"marks": []}, None, sources={}))
    assert first == second


# ---------------------------------------------------------------------------
# Convention reading of the adjudicated precision (E105)
# ---------------------------------------------------------------------------


def _in_zone_at_10(doc: str, offset: int):
    return {"form": "head"} if offset == 10 else None


def test_convention_precision_excludes_in_zone_marks():
    marks = [
        {"doc": "1", "start": 10, "verdict": "correct"},       # in zone -> out of scope
        {"doc": "1", "start": 500, "verdict": "correct"},
        {"doc": "1", "start": 600, "verdict": "wrong_entity"},
        {"doc": "1", "start": 700, "verdict": "undecidable"},  # never decidable
    ]
    result = convention_precision({"marks": marks}, _in_zone_at_10)
    assert result["marks_total"] == 4
    assert result["in_zone"] == 1
    assert result["in_scope_decidable"] == 2
    assert result["correct"] == 1
    assert result["precision"] == 0.5
    assert 0.0 <= result["ci95"][0] <= 0.5 <= result["ci95"][1] <= 1.0


def test_convention_precision_reads_the_newest_wave_only():
    """Two draws over different frozen scans are no common sample; the newest counts."""
    store = {"snapshot": "2026-08-21", "marks": [
        {"doc": "1", "start": 500, "verdict": "wrong_entity",
         "source": {"wave": "adjudication-2026-08-12"}},
        {"doc": "1", "start": 600, "verdict": "correct",
         "source": {"wave": "adjudication-2026-08-21"}},
        {"doc": "1", "start": 10, "verdict": "correct",
         "source": {"wave": "adjudication-2026-08-21"}},
    ]}
    result = convention_precision(store, _in_zone_at_10)
    assert result["snapshot"] == "2026-08-21"
    assert result["marks_total"] == 2
    assert result["in_zone"] == 1
    assert result["in_scope_decidable"] == 1
    assert result["precision"] == 1.0


def test_convention_precision_is_deterministic():
    marks = [{"doc": "1", "start": i * 100, "verdict": v}
             for i, v in enumerate(["correct"] * 8 + ["wrong_span"] * 2)]
    first = convention_precision({"marks": marks}, _in_zone_at_10)
    second = convention_precision({"marks": marks}, _in_zone_at_10)
    assert first == second


def test_convention_precision_without_verdicts_is_unavailable():
    result = convention_precision(None, _in_zone_at_10)
    assert result["available"] is False
    assert convention_precision({"marks": []}, _in_zone_at_10)["available"] is False


def test_convention_precision_appears_in_the_report(corpus):
    tmp_path, with_head, _ = corpus
    documents = audit_corpus(tmp_path)
    zone = documents[0]["patterns"][0]["zones"][0]
    verdicts = {"marks": [
        {"doc": "10", "page": 1, "start": zone["start"], "end": zone["end"],
         "surface": "Jeanne Hersch", "verdict": "correct",
         "reason": "Running head of the printed page.", "text_sha256": _sha(with_head)},
        {"doc": "20", "page": 1, "start": 5, "end": 7, "surface": "x",
         "verdict": "correct", "reason": "Body mention.", "text_sha256": _sha(with_head)},
    ]}
    report = build_report(documents, verdicts, None, sources={})
    reading = report["convention_precision"]
    assert reading["in_zone"] == 1
    assert reading["in_scope_decidable"] == 1
    assert reading["precision"] == 1.0
