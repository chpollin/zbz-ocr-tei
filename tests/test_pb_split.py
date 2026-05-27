"""Tests fuer scripts/tei/pb_split.py -- die gemeinsame <pb>-Seitensegmentierung.

Nagelt den Vertrag fest, den frueher zwei Dateien per Kommentar synchron hielten
(generate_edition_data.py + tei_blank_marker.py): Seitenzahl = 1-basierte
sequenzielle pb-Position, NICHT das n-Attribut; Chunk-Grenzen liegen an den
pb-Matches. Drift hier wuerde Leerseiten-Marker auf der falschen Seite platzieren.
"""

from scripts.tei.pb_split import PB_RE, BODY_INNER_RE, iter_page_spans


def test_no_pb_returns_empty():
    assert iter_page_spans("<div><p>nur Text, kein pb</p></div>") == []


def test_page_is_sequential_position_not_n_attribute():
    # n-Attribute tragen Journal-Pagination (56,57); Seiten muessen 1,2,3 sein.
    body = '<pb n="56" facs="#f1"/><p>a</p><pb n="57" facs="#f2"/><p>b</p>'
    spans = iter_page_spans(body)
    assert [s.page for s in spans] == [1, 2]


def test_content_excludes_pb_tag_and_spans_to_next():
    body = '<pb facs="#f1"/><p>eins</p><pb facs="#f2"/><p>zwei</p>'
    spans = iter_page_spans(body)
    assert body[spans[0].content_start:spans[0].content_end] == "<p>eins</p>"
    assert body[spans[1].content_start:spans[1].content_end] == "<p>zwei</p>"


def test_pb_inclusive_slice_starts_at_pb():
    body = '<pb facs="#f1"/><p>eins</p><pb facs="#f2"/><p>zwei</p>'
    spans = iter_page_spans(body)
    # pb-inklusiver Chunk (Mirror-Splitter) beginnt mit dem pb-Tag
    chunk0 = body[spans[0].pb_start:spans[0].content_end]
    assert chunk0 == '<pb facs="#f1"/><p>eins</p>'
    assert spans[0].pb_tag == '<pb facs="#f1"/>'


def test_prefix_before_first_pb_is_recoverable():
    # tei_blank_marker bewahrt body_inner[:spans[0].pb_start]
    body = '<head>Titel</head><pb facs="#f1"/><p>eins</p>'
    spans = iter_page_spans(body)
    assert body[:spans[0].pb_start] == "<head>Titel</head>"


def test_last_page_runs_to_end():
    body = '<pb facs="#f1"/><p>eins</p><pb facs="#f2"/><p>letztes</p>'
    spans = iter_page_spans(body)
    assert spans[-1].content_end == len(body)


def test_pb_re_requires_whitespace_after_pb():
    # schliesst hypothetische Elemente wie <pba> aus; echte pb haben immer Attribute
    assert PB_RE.search("<pb facs='x'/>") is not None
    assert PB_RE.search("<pban/>") is None


def test_body_inner_re_extracts_body_content():
    raw = '<text><body><pb facs="#f1"/><p>x</p></body></text>'
    m = BODY_INNER_RE.search(raw)
    assert m.group(1) == '<pb facs="#f1"/><p>x</p>'


def test_reassembly_round_trips_for_blank_marker_pattern():
    # Reproduziert das tei_blank_marker-Reassembly: prefix + sum(pb_tag + content) == body_inner
    body = '<head>T</head><pb facs="#f1"/><p>a</p><pb facs="#f2"/><p>b</p>'
    spans = iter_page_spans(body)
    out = body[:spans[0].pb_start]
    for s in spans:
        out += s.pb_tag + body[s.content_start:s.content_end]
    assert out == body
