"""Tests for scripts/tei/tei_reading_order_fix.py (M3 in-place reading-order fix).

The tool permutes region blocks inside tei_final page chunks by byte splice. The
tests pin the contract: robust non-canonical pages become canonical, fragile and
structurally unmappable pages stay byte-identical, moved blocks survive verbatim,
a second run is a no-op, and the real run backs up the pre-state.
"""

import json

import pytest

from scripts.eval.reading_order_audit import audit_document
from scripts.tei import marker_common
from scripts.tei import tei_reading_order_fix as rof


# --- synthetic TEI builder -------------------------------------------------
# Surface is 1000x1000, so zone pixel coords equal pct*10. Canonical order for
# the standard geometry: wide head band first, then left column, then right.

_HEAD = ("facs_1_r_1", (80, 50, 920, 120))
_RIGHT = ("facs_1_r_2", (550, 200, 850, 380))
_LEFT = ("facs_1_r_3", (100, 200, 400, 380))


def make_tei(body_inner, zones=(_HEAD, _RIGHT, _LEFT)):
    zone_xml = "\n".join(
        f'      <zone xml:id="{zid}" ulx="{ulx}" uly="{uly}" lrx="{lrx}" lry="{lry}"/>'
        for zid, (ulx, uly, lrx, lry) in zones
    )
    return f"""<TEI xmlns="http://www.tei-c.org/ns/1.0">
  <facsimile>
    <surface xml:id="facs_1" ulx="0" uly="0" lrx="1000" lry="1000">
{zone_xml}
    </surface>
  </facsimile>
  <text><body>
<pb facs="#facs_1" n="[5]"/>
{body_inner}</body></text>
</TEI>"""


_INVERTED_BODY = """  <p facs="#facs_1_r_1">Kopf</p>
  <p facs="#facs_1_r_2">rechts</p>
  <p facs="#facs_1_r_3">links</p>
"""


@pytest.fixture
def corpus(tmp_path, monkeypatch):
    """Isolated tei_final dir + tool paths; returns a writer/runner helper."""
    final_dir = tmp_path / "tei_final"
    final_dir.mkdir()
    monkeypatch.setattr(marker_common, "TEI_FINAL_DIR", final_dir)
    monkeypatch.setattr(rof, "BACKUP_DIR", tmp_path / "_backup")
    monkeypatch.setattr(rof, "REPORT_PATH", tmp_path / "audits" / "run.json")

    class Corpus:
        dir = final_dir
        backup = tmp_path / "_backup"
        report_path = tmp_path / "audits" / "run.json"

        def write(self, doc_id, text):
            (final_dir / f"{doc_id}_final.xml").write_text(text, encoding="utf-8")

        def read(self, doc_id):
            return (final_dir / f"{doc_id}_final.xml").read_text(encoding="utf-8")

        def run(self, dry_run=False, only_doc=None):
            return rof.run(only_doc=only_doc, dry_run=dry_run)

        def report(self):
            return json.loads(self.report_path.read_text(encoding="utf-8"))

    return Corpus()


# --- fixing ---------------------------------------------------------------

def test_inverted_two_column_becomes_canonical(corpus):
    corpus.write("100", make_tei(_INVERTED_BODY))
    summary = corpus.run()
    assert summary["pages_fixed"] == 1
    fixed = corpus.read("100")
    assert fixed.index("facs_1_r_3") < fixed.index('<p facs="#facs_1_r_2">')
    # W19 view: the audit no longer flags the page
    per_page, err = audit_document(corpus.dir / "100_final.xml")
    assert err is None and per_page == []


def test_lb_duplicate_refs_ride_inside_their_block(corpus):
    body = (
        '  <p facs="#facs_1_r_1">Kopf</p>\n'
        '  <p facs="#facs_1_r_2"><lb facs="#facs_1_r_2" n="N001"/>rechts '
        '<lb facs="#facs_1_r_2" n="N002"/>zeile2</p>\n'
        '  <p facs="#facs_1_r_3"><lb facs="#facs_1_r_3" n="N001"/>links</p>\n'
    )
    corpus.write("110", make_tei(body))
    assert corpus.run()["pages_fixed"] == 1
    fixed = corpus.read("110")
    # the lb stays inside its p, and the page is canonical afterwards
    assert '<p facs="#facs_1_r_2"><lb facs="#facs_1_r_2" n="N001"/>rechts ' in fixed
    per_page, err = audit_document(corpus.dir / "110_final.xml")
    assert err is None and per_page == []


def test_single_wrapping_div_is_descended(corpus):
    body = '  <div type="text">\n' + _INVERTED_BODY + "  </div>\n"
    corpus.write("120", make_tei(body))
    assert corpus.run()["pages_fixed"] == 1
    fixed = corpus.read("120")
    assert fixed.index("facs_1_r_3") < fixed.index('<p facs="#facs_1_r_2">')
    assert fixed.count('<div type="text">') == 1


def test_moved_block_bytes_survive_verbatim(corpus):
    payload = "l’esprit <note place=\"foot\">demotiert «Zitat»</note> Ende"
    body = (
        '  <p facs="#facs_1_r_1">Kopf</p>\n'
        f'  <p facs="#facs_1_r_2">{payload}</p>\n'
        '  <p facs="#facs_1_r_3">links</p>\n'
    )
    corpus.write("130", make_tei(body))
    corpus.run()
    assert f'<p facs="#facs_1_r_2">{payload}</p>' in corpus.read("130")


# --- skipping -------------------------------------------------------------

def test_fragile_page_untouched(corpus):
    # width-borderline geometry (w=61% block): classify_page says fragil
    zones = [
        ("facs_1_r_1", (70, 60, 890, 140)),
        ("facs_1_r_2", (680, 120, 880, 200)),
        ("facs_1_r_3", (140, 140, 270, 220)),
        ("facs_1_r_4", (70, 240, 680, 320)),
        ("facs_1_r_5", (640, 500, 880, 580)),
    ]
    body = "".join(f'  <p facs="#{z}">B</p>\n' for z, _ in zones)
    corpus.write("200", make_tei(body, zones=zones))
    before = corpus.read("200")
    summary = corpus.run()
    assert summary["pages_fixed"] == 0
    assert corpus.read("200") == before
    assert corpus.report()["documents"]["200"]["skips"]["fragile"] == ["1"]


def test_facsless_block_between_regions_is_skipped(corpus):
    body = (
        '  <p facs="#facs_1_r_1">Kopf</p>\n'
        '  <p facs="#facs_1_r_2">rechts</p>\n'
        "  <p>dazwischen ohne facs</p>\n"
        '  <p facs="#facs_1_r_3">links</p>\n'
    )
    corpus.write("210", make_tei(body))
    before = corpus.read("210")
    summary = corpus.run()
    assert summary["pages_fixed"] == 0
    assert corpus.read("210") == before
    assert corpus.report()["documents"]["210"]["skips"]["interleaved_block"] == ["1"]


def test_sp_wrapped_regions_are_skipped(corpus):
    body = (
        "  <sp><speaker>A</speaker>\n"
        '    <p facs="#facs_1_r_1">Kopf</p>\n'
        '    <p facs="#facs_1_r_2">rechts</p>\n'
        '    <p facs="#facs_1_r_3">links</p>\n'
        "  </sp>\n"
    )
    corpus.write("220", make_tei(body))
    before = corpus.read("220")
    corpus.run()
    assert corpus.read("220") == before
    assert corpus.report()["documents"]["220"]["skips"]["unmappable_structure"] == ["1"]


def test_nested_foreign_region_ref_is_skipped(corpus):
    body = (
        '  <p facs="#facs_1_r_1">Kopf</p>\n'
        '  <p facs="#facs_1_r_2">rechts <lb facs="#facs_1_r_3" n="N001"/>fremd</p>\n'
        '  <p facs="#facs_1_r_3">links</p>\n'
    )
    corpus.write("230", make_tei(body))
    before = corpus.read("230")
    corpus.run()
    assert corpus.read("230") == before
    assert corpus.report()["documents"]["230"]["skips"]["nested_foreign_region"] == ["1"]


def test_canonical_page_untouched(corpus):
    body = (
        '  <p facs="#facs_1_r_1">Kopf</p>\n'
        '  <p facs="#facs_1_r_3">links</p>\n'
        '  <p facs="#facs_1_r_2">rechts</p>\n'
    )
    corpus.write("240", make_tei(body))
    before = corpus.read("240")
    summary = corpus.run()
    assert summary["pages_fixed"] == 0
    assert corpus.read("240") == before


# --- run contract -----------------------------------------------------------

def test_idempotent_second_run(corpus):
    corpus.write("300", make_tei(_INVERTED_BODY))
    corpus.run()
    once = corpus.read("300")
    summary = corpus.run()
    assert summary["pages_fixed"] == 0 and summary["docs_changed"] == 0
    assert corpus.read("300") == once


def test_dry_run_writes_nothing_but_reports(corpus):
    corpus.write("310", make_tei(_INVERTED_BODY))
    before = corpus.read("310")
    summary = corpus.run(dry_run=True)
    assert summary["pages_fixed"] == 1
    assert corpus.read("310") == before
    assert not corpus.backup.exists()
    assert corpus.report()["dry_run"] is True


def test_real_run_backs_up_pre_state(corpus):
    corpus.write("320", make_tei(_INVERTED_BODY))
    before = corpus.read("320")
    corpus.run()
    assert (corpus.backup / "320_final.xml").read_text(encoding="utf-8") == before
    assert corpus.read("320") != before
