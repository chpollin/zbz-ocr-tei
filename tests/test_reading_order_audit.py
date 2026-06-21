"""Tests fuer das Lesereihenfolge-Audit (scripts/eval/reading_order_audit) und die
Schwellwert-Override-Parameter von reading_order_permutation."""

from scripts.eval.reading_order_audit import audit_document, classify_page
from scripts.tei.tei_xml_utils import (
    COLUMN_GAP_PCT,
    WIDE_REGION_W_PCT,
    reading_order_permutation,
)


def bb(x, y, w, h=8.0):
    return {"x_pct": x, "y_pct": y, "w_pct": w, "h_pct": h}


# --- reading_order_permutation: Override-Parameter sind verhaltenswahrend ---

def test_default_kwargs_equal_module_constants():
    page = [bb(8, 5, 84), bb(55, 20, 30), bb(10, 20, 30), bb(55, 40, 30), bb(10, 40, 30)]
    assert reading_order_permutation(page) == reading_order_permutation(
        page, wide_w_pct=WIDE_REGION_W_PCT, column_gap_pct=COLUMN_GAP_PCT
    )


def test_wide_threshold_override_changes_banding():
    # Ein Block mit w=61 ist bei WIDE=60 vollbreit, bei WIDE=65 eine Spalte -> andere Ordnung.
    page = [bb(7, 6, 82), bb(68, 12, 20), bb(14, 14, 13), bb(7, 24, 61), bb(64, 50, 24)]
    at60 = reading_order_permutation(page, wide_w_pct=60.0)
    at65 = reading_order_permutation(page, wide_w_pct=65.0)
    assert at60 != at65


# --- classify_page: None | robust | fragil ---

def test_single_column_is_unaffected():
    # Eine Spalte, bereits oben-nach-unten: der Fix laesst die Seite unveraendert.
    page = [bb(10, 10, 40), bb(10, 30, 40), bb(10, 50, 40)]
    assert classify_page(page) is None


def test_canonical_two_column_is_unaffected():
    # Schon links-vor-rechts geliefert -> keine Umsortierung.
    page = [bb(8, 5, 84), bb(10, 20, 30), bb(10, 40, 30), bb(55, 20, 30), bb(55, 40, 30)]
    assert classify_page(page) is None


def test_clean_two_column_swap_is_robust():
    # Rechte Spalte vor linker geliefert; Breiten/Abstaende weit von den Schwellen -> robust.
    page = [bb(8, 5, 84), bb(55, 20, 30), bb(10, 20, 30), bb(55, 40, 30), bb(10, 40, 30)]
    assert classify_page(page) == "robust"


def test_width_borderline_is_fragile():
    # 760-artig: Block w=61 knapp ueber der 60%-Schwelle -> Umsortierung kippt unter Perturbation.
    page = [bb(7, 6, 82), bb(68, 12, 20), bb(14, 14, 13), bb(7, 24, 61), bb(64, 50, 24)]
    assert classify_page(page) == "fragil"


def test_gap_borderline_is_fragile():
    # Zwei schmale Bloecke mit Mitten-Abstand ~14, nahe der 12%-Gutter-Schwelle; bei GAP+3
    # verschmelzen sie zu einer Spalte und kippen die Ordnung.
    page = [bb(8, 5, 84), bb(24, 20, 20), bb(10, 40, 20)]
    assert classify_page(page) == "fragil"


# --- audit_document: Verdrahtung mit iter_page_zone_bboxes ueber echtes TEI ---

_TEI_TWO_COLUMN_INVERTED = """<TEI xmlns="http://www.tei-c.org/ns/1.0">
  <facsimile>
    <surface xml:id="facs_1" ulx="0" uly="0" lrx="1000" lry="1000">
      <zone xml:id="facs_1_r_1" ulx="80" uly="50" lrx="920" lry="120"/>
      <zone xml:id="facs_1_r_2" ulx="550" uly="200" lrx="850" lry="380"/>
      <zone xml:id="facs_1_r_3" ulx="100" uly="200" lrx="400" lry="380"/>
    </surface>
  </facsimile>
  <text><body>
    <p facs="#facs_1_r_1">Kopf</p>
    <p facs="#facs_1_r_2">rechts</p>
    <p facs="#facs_1_r_3">links</p>
  </body></text>
</TEI>"""


def test_audit_document_flags_inverted_columns(tmp_path):
    f = tmp_path / "999_final.xml"
    f.write_text(_TEI_TWO_COLUMN_INVERTED, encoding="utf-8")
    per_page, err = audit_document(f)
    assert err is None
    assert per_page == [("1", "robust")]


def test_audit_document_handles_malformed_xml(tmp_path):
    f = tmp_path / "998_final.xml"
    f.write_text("<TEI><unclosed>", encoding="utf-8")
    per_page, err = audit_document(f)
    assert per_page == []
    assert err is not None
