"""Tests for the deterministic running-head detector (scripts.eval.running_head_audit).

The detector is a measurement instrument: it locates the page-furniture zones at page
starts so a later suppression step can decide about them. These tests pin the detection
contract on synthetic TEI (recurrence with varying page numbers, alternating verso/recto
heads, a document without heads, a repeated body phrase away from the page start) and the
aggregation contract of the audit report.
"""

import hashlib
import json

import pytest

from scripts.eval.running_head_audit import (
    CONTAINS_LENGTH_FACTOR,
    MAX_HEAD_CHARS,
    MAX_HEAD_SEGMENTS,
    MIN_COMPANION_RECURRENCE,
    MIN_RECURRENCE,
    audit_corpus,
    build_report,
    detect_document,
    normalize_head,
    zone_lookup,
)

TEI_NS = "http://www.tei-c.org/ns/1.0"


def _tei(pages: list[str]) -> str:
    """A minimal final TEI whose body carries one <pb> per entry of `pages`."""
    body = "".join(f'<pb facs="#facs_{i}" n="{i}" />{content}'
                   for i, content in enumerate(pages, start=1))
    return (f'<TEI xmlns="{TEI_NS}"><teiHeader><fileDesc><titleStmt>'
            "<title>Fixture</title></titleStmt></fileDesc></teiHeader>"
            f'<text><body><div n="1">{body}</div></body></text></TEI>')


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


def test_alternating_verso_recto_heads_are_both_detected():
    # verso carries the author on pages 1/3/5, recto the work title on pages 2/4
    pages = []
    for i in range(5):
        head = "Jeanne Hersch" if i % 2 == 0 else "Karl Jaspers: il non possesso"
        pages.append(f"<p>{head}</p>{_body(i)}")
    patterns = detect_document(_tei(pages))["patterns"]
    assert _forms(patterns) == {"jeanne hersch", "karl jaspers: il non possesso"}
    verso = _pattern(patterns, "jeanne hersch")
    recto = _pattern(patterns, "karl jaspers: il non possesso")
    assert verso["kind"] == "primary" and verso["pages"] == [1, 3, 5]
    assert verso["page_parity"] == "odd"
    # the alternating counterpart clears only the companion threshold
    assert len(recto["pages"]) == MIN_COMPANION_RECURRENCE
    assert recto["kind"] == "companion"
    assert recto["page_parity"] == "even"


def test_companion_rule_needs_an_established_head_in_the_same_document():
    # two forms twice each, none of them primary -> the document shows no head at all
    pages = [f"<p>{'Alpha Beta' if i % 2 == 0 else 'Gamma Delta'}</p>{_body(i)}"
             for i in range(4)]
    assert detect_document(_tei(pages))["patterns"] == []


def test_document_without_heads_yields_no_pattern():
    assert detect_document(_tei([_body(i) for i in range(6)]))["patterns"] == []


def test_repeated_body_phrase_away_from_the_page_start_is_not_a_head():
    ordinals = ["premiere", "deuxieme", "troisieme", "quatrieme", "cinquieme"]
    pages = [(f"<p>Ouverture {word} singuliere</p>"
              f"<p>Ligne {word} egalement singuliere</p>"
              "<p>Phrase de corps repetee</p>") for word in ordinals]
    patterns = detect_document(_tei(pages))["patterns"]
    assert "phrase de corps repetee" not in _forms(patterns)


def test_head_at_the_second_segment_is_detected_but_not_beyond():
    assert MAX_HEAD_SEGMENTS == 2
    pages = [f"<p>Titre singulier {word}</p><p>Jeanne Hersch</p>{_body(i)}"
             for i, word in enumerate(["alpha", "beta", "gamma", "delta"])]
    patterns = detect_document(_tei(pages))["patterns"]
    assert _forms(patterns) == {"jeanne hersch"}
    assert _pattern(patterns, "jeanne hersch")["segment_positions"] == [1]


def test_empty_and_pure_number_segments_do_not_consume_the_head_window():
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


def test_a_long_line_merely_containing_a_head_form_is_not_detected():
    head = "Le combat de dragon"
    long_line = f"{head} " + "et la suite du raisonnement continue encore ici"
    assert len(long_line) > CONTAINS_LENGTH_FACTOR * len(head)
    pages = [f"<p>{head}</p>{_body(i)}" for i in range(4)]
    pages.append(f"<p>{long_line}</p>{_body(9)}")
    patterns = detect_document(_tei(pages))["patterns"]
    assert normalize_head(long_line) not in _forms(patterns)


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


def test_build_report_flags_ground_truth_offset_drift(corpus):
    tmp_path, with_head, _ = corpus
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
