"""Tests fuer scripts/tei/tei_pb_folio.py -- Bestandskorrektur der Druckfolio im pb@n.

Nagelt den Kontrakt der Operator-Entscheidung 2026-07-07 fest: Footer- und
interpolierte Folios werden geklammert, Offset-Ableitung nur bei stabiler Konsistenz,
Fallback bleibt die ungeklammerte Scan-Nummer, printed_folio-Docs werden nur geklammert
(nicht verrechnet), Echo-Absaetze fallen nur bei exakter Uebereinstimmung. Der Schreibpfad
ist idempotent, der dry-run schreibt nichts. Integrationsproben laufen gegen die echten
tei_final-Dokumente 570/110/2330/30.
"""

import pytest

from scripts.config import TEI_FINAL_DIR
from scripts.tei.tei_pb_folio import (
    OFFSET_CONSISTENCY_MIN,
    OFFSET_MIN_FOOTER_PAGES,
    bracket,
    compute_offset,
    folio_content,
    is_blank_pb,
    n_value,
    offset_is_stable,
    process_doc,
    resolve_page_folio,
    rewrite_body,
    set_pb_n,
    strip_echo_paragraphs,
)

# ---------------------------------------------------------------------------
# folio_content / bracket / set_pb_n / is_blank_pb / n_value
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("raw,expected", [
    ("249", "249"),
    ("[249]", "249"),
    (" [ 249 ] ", "249"),
    ("[7.14]", "7.14"),
    ("7.14", "7.14"),
    ("iv", None),
    ("", None),
    (None, None),
])
def test_folio_content(raw, expected):
    assert folio_content(raw) == expected


def test_bracket():
    assert bracket("249") == "[249]"
    assert bracket("7.14") == "[7.14]"


def test_set_pb_n_replaces_existing():
    assert set_pb_n('<pb facs="#facs_2" n="2" />', "[248]") == '<pb facs="#facs_2" n="[248]" />'


def test_set_pb_n_preserves_blank_type():
    out = set_pb_n('<pb facs="#f" n="2" type="blank" />', "[5]")
    assert 'n="[5]"' in out and 'type="blank"' in out


def test_set_pb_n_does_not_touch_facs():
    # das 'n' innerhalb von facs/anderen Attributen darf nicht getroffen werden
    out = set_pb_n('<pb facs="#facs_1" n="1" />', "[3]")
    assert out == '<pb facs="#facs_1" n="[3]" />'


def test_is_blank_and_n_value():
    assert is_blank_pb('<pb facs="#f" n="2" type="blank" />') is True
    assert is_blank_pb('<pb facs="#f" n="2" />') is False
    assert n_value('<pb facs="#f" n="248" />') == "248"


# ---------------------------------------------------------------------------
# resolve_page_folio: Signalprioritaet + Klammerregel
# ---------------------------------------------------------------------------

def test_footer_folio_is_bracketed():
    new_n, source, num = resolve_page_folio(
        page=2, blank=False, footer="248", interp={}, offset=None,
        offset_ok=False, current_n="2", printed_folio_doc=False)
    assert (new_n, source, num) == ("[248]", "footer", "248")


def test_interpolated_folio_is_bracketed():
    new_n, source, num = resolve_page_folio(
        page=3, blank=False, footer=None, interp={3: 249}, offset=None,
        offset_ok=False, current_n="3", printed_folio_doc=False)
    assert (new_n, source, num) == ("[249]", "interpolation", "249")


def test_offset_folio_only_when_stable():
    # stabil: Offset 2 -> Seite 14 wird [12]
    new_n, source, num = resolve_page_folio(
        page=14, blank=False, footer=None, interp={}, offset=2,
        offset_ok=True, current_n="14", printed_folio_doc=False)
    assert (new_n, source, num) == ("[12]", "offset", "12")


def test_offset_not_applied_when_unstable():
    new_n, source, num = resolve_page_folio(
        page=14, blank=False, footer=None, interp={}, offset=2,
        offset_ok=False, current_n="14", printed_folio_doc=False)
    assert (new_n, source, num) == ("14", "fallback", None)


def test_offset_negative_folio_falls_back():
    # Frontmatter: Scan-Position 1 minus Offset 2 = -1 -> keine Ableitung
    new_n, source, num = resolve_page_folio(
        page=1, blank=False, footer=None, interp={}, offset=2,
        offset_ok=True, current_n="1", printed_folio_doc=False)
    assert (new_n, source, num) == ("1", "fallback", None)


def test_fallback_stays_unbracketed():
    new_n, source, num = resolve_page_folio(
        page=1, blank=False, footer=None, interp={}, offset=None,
        offset_ok=False, current_n="1", printed_folio_doc=False)
    assert (new_n, source, num) == ("1", "fallback", None)


def test_priority_footer_over_interpolation_over_offset():
    # Footer schlaegt alles
    assert resolve_page_folio(5, False, "3", {5: 99}, 2, True, "5", False)[1] == "footer"
    # Interpolation schlaegt Offset
    assert resolve_page_folio(5, False, None, {5: 3}, 2, True, "5", False)[1] == "interpolation"


def test_printed_folio_doc_brackets_existing_not_recomputed():
    new_n, source, num = resolve_page_folio(
        page=2, blank=False, footer=None, interp={}, offset=None,
        offset_ok=False, current_n="224", printed_folio_doc=True)
    assert (new_n, source, num) == ("[224]", "existing_folio", "224")


def test_printed_folio_doc_dot_notation():
    assert resolve_page_folio(2, False, None, {}, None, False, "7.14", True)[0] == "[7.14]"


def test_rerun_keeps_scan_fallback_unbracketed():
    # Wiederholungslauf: Dokument traegt schon Klammern, ungeklammerte Werte sind
    # Scan-Fallbacks des ersten Laufs und duerfen nicht zu Druckfolios werden
    new_n, source, num = resolve_page_folio(
        page=1, blank=False, footer=None, interp={}, offset=None,
        offset_ok=False, current_n="1", printed_folio_doc=True, doc_has_brackets=True)
    assert (new_n, source, num) == ("1", "fallback", None)


def test_rerun_rebrackets_bracketed_idempotent():
    new_n, source, num = resolve_page_folio(
        page=2, blank=False, footer=None, interp={}, offset=None,
        offset_ok=False, current_n="[248]", printed_folio_doc=True, doc_has_brackets=True)
    assert (new_n, source, num) == ("[248]", "existing_folio", "248")


def test_blank_page_bracketed_only_when_interpolable():
    new_n, source, num = resolve_page_folio(
        page=3, blank=True, footer=None, interp={3: 5}, offset=None,
        offset_ok=False, current_n="3", printed_folio_doc=False)
    assert (new_n, source, num) == ("[5]", "interpolation", "5")


def test_blank_page_no_footer_no_offset():
    # Blank: weder Footer noch Offset, ohne Interpolation unveraendert
    new_n, source, num = resolve_page_folio(
        page=3, blank=True, footer="99", interp={}, offset=2,
        offset_ok=True, current_n="3", printed_folio_doc=False)
    assert (new_n, source, num) == ("3", "fallback", None)


# ---------------------------------------------------------------------------
# compute_offset / offset_is_stable
# ---------------------------------------------------------------------------

def test_compute_offset_consistent():
    lp = {14: ["12"], 17: ["15"], 18: ["16"], 21: ["19"]}
    mode, cons, pages = compute_offset(lp)
    assert (mode, cons, pages) == (2, 1.0, 4)


def test_compute_offset_mixed_lowers_consistency():
    lp = {14: ["12"], 17: ["15"], 18: ["16"], 30: ["1"]}  # letzte Seite Offset 29
    mode, cons, pages = compute_offset(lp)
    assert mode == 2 and pages == 4 and cons == pytest.approx(0.75)


def test_compute_offset_empty():
    assert compute_offset({}) == (None, 0.0, 0)
    assert compute_offset({5: ["7", "9"]}) == (None, 0.0, 0)  # keine Einzel-Footer-Seite


def test_offset_is_stable_threshold():
    assert offset_is_stable(0.99, 104) is True
    assert offset_is_stable(1.0, OFFSET_MIN_FOOTER_PAGES) is True
    assert offset_is_stable(1.0, OFFSET_MIN_FOOTER_PAGES - 1) is False  # zu wenig Beleg
    assert offset_is_stable(OFFSET_CONSISTENCY_MIN - 0.01, 100) is False  # zu inkonsistent


# ---------------------------------------------------------------------------
# strip_echo_paragraphs: nur exakte Uebereinstimmung
# ---------------------------------------------------------------------------

def test_echo_removed_on_exact_match():
    chunk = "<p>248</p><p>Fliesstext</p>"
    new, removed, healed = strip_echo_paragraphs(chunk, "248")
    assert (removed, healed) == (1, 0) and new == "<p>Fliesstext</p>"


def test_echo_whitespace_tolerant():
    new, removed, _ = strip_echo_paragraphs("<p> 7 </p>", "7")
    assert removed == 1 and new == ""


def test_echo_not_removed_on_partial_match():
    assert strip_echo_paragraphs("<p>248 und mehr</p>", "248") == ("<p>248 und mehr</p>", 0, 0)
    assert strip_echo_paragraphs("<p>1248</p>", "248") == ("<p>1248</p>", 0, 0)


def test_echo_noop_without_folio():
    assert strip_echo_paragraphs("<p>7</p>", None) == ("<p>7</p>", 0, 0)


def test_echo_in_sp_removes_whole_block():
    # Schema verlangt ein <p> im <sp>: das Echo-<p> allein zu entfernen hinterlaesst
    # einen invaliden Rest-Rahmen (Korpus-Defekt 2330/2400/2540/3180, Lauf 2026-07-07)
    chunk = '<sp>\n  <speaker />\n  <p>\n    17\n  </p>\n</sp><p>Fliesstext</p>'
    new, removed, healed = strip_echo_paragraphs(chunk, "17")
    assert (removed, healed) == (1, 0)
    assert "<sp>" not in new and new.strip() == "<p>Fliesstext</p>"


def test_echo_in_sp_with_named_speaker_untouched():
    chunk = "<sp><speaker>G.D.K.</speaker><p>17</p></sp>"
    assert strip_echo_paragraphs(chunk, "17") == (chunk, 0, 0)


def test_orphaned_empty_sp_healed_even_without_folio():
    chunk = "<p>Text</p><sp>\n  <speaker />\n  \n</sp>"
    new, removed, healed = strip_echo_paragraphs(chunk, None)
    assert (removed, healed) == (0, 1)
    assert new.strip() == "<p>Text</p>"


# ---------------------------------------------------------------------------
# rewrite_body: Idempotenz des Schreibpfads (Fixture)
# ---------------------------------------------------------------------------

_FIXTURE_BODY = (
    '<head>Titel</head>'
    '<pb facs="#facs_1" n="1" /><p>Deckblatt</p>'
    '<pb facs="#facs_2" n="2" /><p>248</p><p>Text zwei</p>'
    '<pb facs="#facs_3" n="3" /><p>249</p><p>Text drei</p>'
)


def test_rewrite_body_brackets_footer_and_interpolation():
    new_body, report = rewrite_body(
        _FIXTURE_BODY, detected_str={2: "248"}, interp={3: 249},
        offset=None, offset_ok=False, printed_folio_doc=False, strip_echo=True)
    assert 'n="[248]"' in new_body and 'n="[249]"' in new_body
    assert 'n="1"' in new_body  # Fallback bleibt ungeklammert
    assert report["echo"] == 2  # <p>248</p> und <p>249</p> entfernt
    assert report["source_counts"]["footer"] == 1
    assert report["source_counts"]["interpolation"] == 1
    assert report["source_counts"]["fallback"] == 1


def test_rewrite_body_is_idempotent():
    kwargs = {"detected_str": {2: "248"}, "interp": {3: 249},
              "offset": None, "offset_ok": False, "printed_folio_doc": False,
              "strip_echo": True}
    once, _ = rewrite_body(_FIXTURE_BODY, **kwargs)
    twice, _ = rewrite_body(once, **kwargs)
    assert once == twice  # zweiter Lauf byte-identisch, keine [[...]]


def test_rewrite_body_preserves_prefix_before_first_pb():
    new_body, _ = rewrite_body(
        _FIXTURE_BODY, detected_str={}, interp={}, offset=None,
        offset_ok=False, printed_folio_doc=False, strip_echo=False)
    assert new_body.startswith("<head>Titel</head>")


# ---------------------------------------------------------------------------
# Integration gegen die echten tei_final-Dokumente (dry-run schreibt nichts)
# ---------------------------------------------------------------------------

def _require(doc_id):
    path = TEI_FINAL_DIR / f"{doc_id}_final.xml"
    if not path.exists():
        pytest.skip(f"tei_final/{doc_id}_final.xml fehlt")
    return path


@pytest.mark.requires_corpus
def test_dry_run_writes_nothing():
    path = _require("30")
    before = path.read_bytes()
    process_doc("30", dry_run=True, strip_echo=True)
    assert path.read_bytes() == before


# Die Integrationstests asserten den AUSGELIEFERTEN Zustand nach dem Bestandslauf
# vom 2026-07-07 (pb@n geklammert) plus Idempotenz: ein erneuter Lauf schlaegt keine
# pb@n-Aenderung mehr vor. Vor dem Lauf asserteten sie die damaligen Vorschlaege.

def _final_text(doc_id):
    return (TEI_FINAL_DIR / f"{doc_id}_final.xml").read_text(encoding="utf-8")


@pytest.mark.requires_corpus
def test_570_footer_interpolation_fallback():
    _require("570")
    text = _final_text("570")
    assert 'n="[248]"' in text  # Footer-Folio, geklammert
    assert 'n="[249]"' in text  # interpoliert, geklammert
    assert 'n="1"' in text      # Fallback bleibt ungeklammerte Scan-Nummer
    r = process_doc("570", dry_run=True, strip_echo=True)
    assert r["changes"] == []


@pytest.mark.requires_corpus
def test_110_offset_two():
    _require("110")
    # Offset 2: Scanseite 5 traegt Druckseite [3]
    assert 'n="[3]"' in _final_text("110")
    r = process_doc("110", dry_run=True, strip_echo=False)
    assert r["changes"] == []


@pytest.mark.requires_corpus
def test_2330_printed_seven_on_scan_eleven():
    _require("2330")
    assert 'n="[7]"' in _final_text("2330")  # Druckseite 7 auf Scanseite 11
    r = process_doc("2330", dry_run=True, strip_echo=True)
    assert r["changes"] == []


@pytest.mark.requires_corpus
def test_30_printed_folio_bracketed_not_recomputed():
    _require("30")
    r = process_doc("30", dry_run=True, strip_echo=True)
    assert r["class"] == "printed_folio"
    assert r["changes"] == []
    text = _final_text("30")
    for folio in ("[224]", "[226]", "[229]"):
        assert f'n="{folio}"' in text
