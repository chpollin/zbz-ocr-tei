"""Tests fuer die pb-n-Plausibilitaet (scripts.eval.pb_number_audit)."""

import json
import xml.etree.ElementTree as ET

from scripts.eval.pb_number_audit import (
    analyze_body,
    classification_summary,
    classify_document,
    compare_layout_to_pb,
    is_scan_sequence,
    read_layout_page_numbers,
)
from tests.conftest import tei_doc


def _root(body_inner: str):
    return ET.fromstring(tei_doc(body_inner, header="<teiHeader/>"))


def test_scan_sequence_detection():
    assert is_scan_sequence(["1", "2", "3"]) is True
    assert is_scan_sequence(["1", "2", "4"]) is False
    assert is_scan_sequence(["248", "249"]) is False
    assert is_scan_sequence([]) is False


def test_pb_ns_extracted_in_order():
    root = _root('<div><pb n="1"/><p>a</p><pb n="248"/><p>b</p></div>')
    res = analyze_body(root)
    assert res["pb_ns"] == ["1", "248"]


def test_digit_paragraphs_with_page_position():
    # page 2 carries a pure-number paragraph "248" (real print page number)
    root = _root('<div><pb n="1"/><p>text</p><pb n="2"/><p>248</p></div>')
    res = analyze_body(root)
    assert res["digit_paragraphs"] == [{"page": 2, "value": "248"}]


def test_digit_paragraph_dot_notation_and_split_number():
    root = _root('<div><pb n="1"/><p>7.14</p><p>24<lb/>8</p><p>real text</p></div>')
    res = analyze_body(root)
    values = [d["value"] for d in res["digit_paragraphs"]]
    assert values == ["7.14", "248"]


def test_non_digit_paragraph_ignored():
    root = _root('<div><pb n="1"/><p>Band 21 (1961)</p></div>')
    assert analyze_body(root)["digit_paragraphs"] == []


def test_compare_layout_to_pb_reports_mismatch():
    # sequential page 2 -> pb @n="2"; layout footer says "248" -> mismatch
    pb_ns = ["1", "2", "3"]
    layout = {2: ["248"], 3: ["249"]}
    mism = compare_layout_to_pb(pb_ns, layout)
    assert {"page": 2, "layout_number": "248", "pb_n": "2"} in mism
    assert {"page": 3, "layout_number": "249", "pb_n": "3"} in mism


def test_compare_layout_no_mismatch_when_equal():
    assert compare_layout_to_pb(["248", "249"], {1: ["248"], 2: ["249"]}) == []


def test_read_layout_page_numbers(tmp_path):
    doc_dir = tmp_path / "570"
    doc_dir.mkdir()
    payload = {
        "regions": [
            {"zbz_tag": "zb_paragraph", "text": "long body text here", "label": "text"},
            {"zbz_tag": "_filter", "text": "248", "label": "page_footer"},
        ]
    }
    (doc_dir / "570_p002_layout_gemini.json").write_text(
        json.dumps(payload), encoding="utf-8"
    )
    res = read_layout_page_numbers(doc_dir)
    assert res == {2: ["248"]}


# --- classification of pb@n semantics -------------------------------------

def test_classify_scan_sequence():
    res = classify_document([str(i) for i in range(1, 11)])
    assert res["class"] == "scan_sequence"
    assert res["bracket"] == "unbracketed"


def test_classify_printed_folio_ascending_non_scan():
    # pb@n is a clean ascending pagination far from the scan position 1..N
    res = classify_document(["100", "101", "102", "103", "104"])
    assert res["class"] == "printed_folio"


def test_classify_printed_folio_by_layout_footer_match():
    # non-monotonic, low scan-match, but pb@n equals the layout footer number
    res = classify_document(
        ["12", "9", "15"], {1: ["12"], 2: ["9"], 3: ["15"]}
    )
    assert res["class"] == "printed_folio"
    assert res["signals"]["footer_match_ratio"] == 1.0


def test_classify_mixed_scan_with_wild_intrusions():
    res = classify_document(["1", "2", "3", "704", "705", "6", "7", "8"])
    assert res["class"] == "mixed"
    assert res["signals"]["wild_count"] >= 2


def test_classify_undetermined_too_short():
    res = classify_document(["1", "2"])
    assert res["class"] == "undetermined"


def test_classify_undetermined_blank_heavy():
    res = classify_document([None, None, None, "x"])
    assert res["class"] == "undetermined"


def test_classify_bracketed_is_orthogonal():
    res = classify_document(["[1]", "[2]", "[3]", "[4]"])
    assert res["bracket"] == "bracketed"
    assert res["class"] == "scan_sequence"


# --- known corpus cases (hardcoded pb@n, no file IO) -----------------------

def test_known_case_460_scan_sequence():
    assert classify_document([str(i) for i in range(1, 19)])["class"] == "scan_sequence"


def test_known_case_30_printed_folio():
    assert classify_document(["1", "224", "226", "229"])["class"] == "printed_folio"


def test_known_case_1240_mixed():
    pb = ["1", "2", "3", "704", "705", "6", "7", "8", "709", "10", "11", "12", "13", "14", "15"]
    assert classify_document(pb)["class"] == "mixed"


def test_classification_summary_counts():
    docs = {
        "a": {"classification": {"class": "scan_sequence", "bracket": "unbracketed"}},
        "b": {"classification": {"class": "printed_folio", "bracket": "unbracketed"}},
        "c": {"classification": {"class": "scan_sequence", "bracket": "bracketed"}},
    }
    summ = classification_summary(docs)
    assert summ["by_class"]["scan_sequence"] == 2
    assert summ["by_class"]["printed_folio"] == 1
    assert summ["by_bracket"]["bracketed"] == 1
