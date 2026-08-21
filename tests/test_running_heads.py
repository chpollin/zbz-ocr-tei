"""Direct tests for the running-head detection core (scripts/tei/running_heads.py).

The module is consumed by two sides: `scripts.eval.running_head_audit` measures it against
the adjudicated ground truth, and `scripts.tei.entity_matcher` calls `head_spans` to hold
in-zone candidates out of tier 1 (E105). The audit tests cover the detection rules; this
module pins the core API the matcher depends on, the page segmentation with its absolute
offsets, the head window, the raw spans and the zone lookup, on synthetic TEI.
"""

from scripts.tei.running_heads import (
    MAX_HEAD_SEGMENTS,
    MIN_RECURRENCE,
    detect_document,
    head_spans,
    head_window,
    normalize_head,
    page_candidates,
    zone_lookup,
)

TEI_NS = "http://www.tei-c.org/ns/1.0"

BODY_TEXT = ("<p>Ein eigener Absatz dieser Seite, der sich nirgends sonst im Dokument "
             "wiederholt und lang genug ist, um kein Kolumnentitel zu sein.</p>")


def _tei(pages: list[str]) -> str:
    body = "".join(f'<pb facs="#f{i}" n="{i}" />{content}'
                   for i, content in enumerate(pages, start=1))
    return (f'<TEI xmlns="{TEI_NS}"><teiHeader/><text><body><div n="1">{body}</div>'
            "</body></text></TEI>")


def _head_page(number: int) -> str:
    """A page whose first line is the recurring head, followed by unique body prose."""
    return f"<p>{number}</p><head>Jeanne Hersch</head>{BODY_TEXT}"


# ---------------------------------------------------------------------------
# Normalization
# ---------------------------------------------------------------------------

def test_normalize_drops_inline_markup_and_folds_diacritics():
    assert normalize_head("<hi rend='i'>L'Être</hi> et") == "l'etre et"


def test_normalize_strips_leading_and_trailing_folio_digits():
    assert normalize_head("  12  Jeanne Hersch  13. ") == "jeanne hersch"


def test_normalize_of_pure_furniture_is_empty():
    assert normalize_head("<lb/> 42 . ") == ""


# ---------------------------------------------------------------------------
# Head window
# ---------------------------------------------------------------------------

def test_head_window_offsets_point_into_the_source_string():
    xml = "<p>12</p><head>Jeanne Hersch</head><p>Rest</p>"
    window = head_window(xml, 0, len(xml))
    first = window[0]
    assert xml[first["start"]:first["end"]] == "Jeanne Hersch"
    assert first["parent"] == "head"
    assert first["form"] == "jeanne hersch"
    assert first["position"] == 0


def test_head_window_skips_number_only_segments_without_consuming_a_slot():
    xml = "<p>12</p><head>Jeanne Hersch</head><p>Erster Absatz</p><p>Zweiter Absatz</p>"
    forms = [segment["form"] for segment in head_window(xml, 0, len(xml))]
    assert forms == ["jeanne hersch", "erster absatz"]


def test_head_window_is_capped_at_max_head_segments():
    xml = "".join(f"<p>Segment Nummer {i}</p>" for i in range(MAX_HEAD_SEGMENTS + 3))
    assert len(head_window(xml, 0, len(xml))) == MAX_HEAD_SEGMENTS


def test_inline_markup_stays_inside_one_segment():
    xml = "<head>Jeanne <hi rend='i'>Hersch</hi></head>"
    window = head_window(xml, 0, len(xml))
    assert [segment["form"] for segment in window] == ["jeanne hersch"]
    assert window[0]["text"] == "Jeanne Hersch"


# ---------------------------------------------------------------------------
# Page candidates
# ---------------------------------------------------------------------------

def test_page_candidates_counts_page_breaks_and_groups_by_form():
    xml = _tei([_head_page(n) for n in range(1, MIN_RECURRENCE + 1)])
    pages, by_form = page_candidates(xml)
    assert pages == MIN_RECURRENCE
    assert sorted(o["page"] for o in by_form["jeanne hersch"]) == list(
        range(1, MIN_RECURRENCE + 1))


def test_page_candidates_offsets_resolve_in_the_full_document_string():
    xml = _tei([_head_page(n) for n in range(1, MIN_RECURRENCE + 1)])
    _, by_form = page_candidates(xml)
    for occurrence in by_form["jeanne hersch"]:
        assert xml[occurrence["start"]:occurrence["end"]] == "Jeanne Hersch"


def test_page_candidates_ignores_speaker_labels_at_a_page_start():
    xml = _tei([f"<sp><speaker>Jeanne Hersch</speaker>{BODY_TEXT}</sp>"
                for _ in range(MIN_RECURRENCE)])
    _, by_form = page_candidates(xml)
    assert "jeanne hersch" not in by_form


def test_document_without_body_yields_nothing():
    assert page_candidates("<TEI><teiHeader/></TEI>") == (0, {})


# ---------------------------------------------------------------------------
# Detection and spans
# ---------------------------------------------------------------------------

def test_recurring_head_becomes_a_primary_pattern():
    xml = _tei([_head_page(n) for n in range(1, MIN_RECURRENCE + 1)])
    result = detect_document(xml)
    assert result["pages"] == MIN_RECURRENCE
    assert [p["form"] for p in result["patterns"]] == ["jeanne hersch"]
    pattern = result["patterns"][0]
    assert pattern["kind"] == "primary"
    assert pattern["parent_elements"] == ["head"]
    assert len(pattern["zones"]) == MIN_RECURRENCE


def test_two_pages_stay_below_the_recurrence_threshold():
    xml = _tei([_head_page(1), _head_page(2)])
    assert detect_document(xml)["patterns"] == []
    assert head_spans(xml) == ()


def test_head_spans_are_sorted_and_match_the_zones():
    xml = _tei([_head_page(n) for n in range(1, MIN_RECURRENCE + 2)])
    spans = head_spans(xml)
    assert list(spans) == sorted(spans)
    assert {xml[start:end] for start, end in spans} == {"Jeanne Hersch"}


def test_zone_lookup_resolves_only_offsets_inside_a_zone():
    xml = _tei([_head_page(n) for n in range(1, MIN_RECURRENCE + 1)])
    document = dict(detect_document(xml), doc="2310")
    resolve = zone_lookup([document])
    start, end = head_spans(xml)[0]

    assert resolve("2310", start)["form"] == "jeanne hersch"
    assert resolve("2310", end - 1)["kind"] == "primary"
    assert resolve("2310", end) is None
    assert resolve("2310", start - 1) is None
    assert resolve("unknown", start) is None
