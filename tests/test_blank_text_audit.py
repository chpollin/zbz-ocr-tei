"""Tests fuer scripts.eval.blank_text_audit (Leerseiten-Text-Audit).

Synthetische Fixtures: ein Mini-Korpus aus TEI + Manifest + Layout-Mirror in tmp_path.
Geprueft werden die Schwellenkonstanten, die Markup-Bereinigung, die pb-Segmentierung,
die drei Klassen (empty / marginal / substantial), der Layout-Zweitkanal und die
Aggregation samt deterministischem JSON-Payload.
"""
import json

import pytest

from scripts.eval import blank_text_audit as bta
from tests.conftest import tei_doc

# --- Fixture-Bau ---------------------------------------------------------------

def _tei(pages):
    """TEI-Dokument mit einem <pb> je Eintrag von `pages` (Liste von Inhalts-Fragmenten)."""
    body = "\n".join(
        f'<pb n="{i + 1}" facs="#f{i + 1}"/>\n{content}' for i, content in enumerate(pages)
    )
    return tei_doc(body, xml_decl=True)


def _manifest(doc_id, blank_pages, page_count=None, with_pages_section=True):
    data = {
        "doc_id": doc_id,
        "page_count": page_count if page_count is not None else len(blank_pages),
        "streams": {"tei": {"source": "final", "status": "unverifiziert", "history": []}},
    }
    if with_pages_section:
        data["pages"] = {
            str(p): {
                "class": "blank",
                "source": "auto",
                "review": False,
                "evidence": {"ocr_len": 3, "ocr_reason": "len<=5", "docling_regions": 0},
            }
            for p in blank_pages
        }
    return data


def _write_doc(tei_dir, doc_id, pages, blank_pages, **manifest_kw):
    (tei_dir / f"{doc_id}_final.xml").write_text(_tei(pages), encoding="utf-8")
    (tei_dir / f"{doc_id}_manifest.json").write_text(
        json.dumps(_manifest(doc_id, blank_pages, **manifest_kw), ensure_ascii=False),
        encoding="utf-8",
    )


def _write_layout(mirror_dir, doc_id, page, num_regions):
    d = mirror_dir / str(doc_id)
    d.mkdir(parents=True, exist_ok=True)
    (d / f"{doc_id}_p{page:03d}_layout.json").write_text(
        json.dumps({"doc_id": doc_id, "page": page, "num_regions": num_regions, "regions": []}),
        encoding="utf-8",
    )


def _para(text):
    return f'<div type="text"><p facs="#r1">\n  {text}\n</p></div>'


LONG = "Initiation a la methode philosophique. " * 12   # deutlich ueber der Substanz-Schwelle
MEDIUM = "Seitenzahl 880 und ein kurzer Rest davon."     # zwischen den Schwellen
FILLER = "Diese Seite traegt regulaeren Fliesstext."     # ueber der Leer-Schwelle


@pytest.fixture()
def corpus(tmp_path):
    """Mini-Korpus mit allen relevanten Faellen."""
    tei_dir = tmp_path / "tei_final"
    mirror_dir = tmp_path / "pages"
    tei_dir.mkdir()
    mirror_dir.mkdir()

    # 10: blank-Seite 2 wirklich leer, blank-Seite 4 mit substanziellem Text (Fund)
    _write_doc(tei_dir, "10", [_para(FILLER), "", _para(FILLER), _para(LONG)],
               blank_pages=[2, 4], page_count=4)
    # 20: blank-Seite 2 marginal; Seite 3 nicht blank, aber ohne Text (Inverssignal)
    _write_doc(tei_dir, "20", [_para(FILLER), _para(MEDIUM), ""],
               blank_pages=[2], page_count=3)
    # 30: kein pages-Abschnitt im Manifest; Layout meldet Seite 2 als leer, TEI traegt Text
    _write_doc(tei_dir, "30", [_para(FILLER), _para(LONG)],
               blank_pages=[], page_count=2, with_pages_section=False)
    _write_layout(mirror_dir, "30", 1, 7)
    _write_layout(mirror_dir, "30", 2, 0)
    return {"tei_dir": tei_dir, "mirror_dir": mirror_dir}


# --- Konstanten und reine Funktionen -------------------------------------------

def test_threshold_constants_are_ordered_and_documented():
    assert bta.EMPTY_MAX_CHARS == 20
    assert bta.SUBSTANTIAL_MIN_CHARS == 200
    assert bta.EMPTY_MAX_CHARS < bta.SUBSTANTIAL_MIN_CHARS
    assert bta.SNIPPET_CHARS == 150


def test_classify_thresholds_at_the_boundaries():
    assert bta.classify(0) == "empty"
    assert bta.classify(bta.EMPTY_MAX_CHARS) == "empty"
    assert bta.classify(bta.EMPTY_MAX_CHARS + 1) == "marginal"
    assert bta.classify(bta.SUBSTANTIAL_MIN_CHARS - 1) == "marginal"
    assert bta.classify(bta.SUBSTANTIAL_MIN_CHARS) == "substantial"
    assert bta.classify(5000) == "substantial"


def test_strip_markup_removes_tags_comments_and_collapses_whitespace():
    frag = '<div type="text">\n  <p facs="#r1">Hallo   Welt</p>\n  <!-- Kommentar --></div>'
    assert bta.strip_markup(frag) == "Hallo Welt"
    assert bta.strip_markup("") == ""
    assert bta.strip_markup("   \n\t  ") == ""


def test_strip_markup_unescapes_entities_without_creating_tags():
    assert bta.strip_markup("<p>Punkt &amp; Komma</p>") == "Punkt & Komma"
    # Escapte spitze Klammern bleiben Text und werden nicht als Tag entfernt
    assert bta.strip_markup("<p>&lt;pb/&gt; im Text</p>") == "<pb/> im Text"


def test_facsimile_path_is_zero_padded():
    assert bta.facsimile_path("1520", 130) == "docs/images/1520/1520_p130.png"
    assert bta.facsimile_path("10", 2) == "docs/images/10/10_p002.png"


def test_page_texts_segments_by_pb_position_not_by_n_attribute():
    tei = (
        '<TEI xmlns="http://www.tei-c.org/ns/1.0"><text><body>'
        '<pb n="56"/><p>erste</p><pb n="57"/><p>zweite</p>'
        "</body></text></TEI>"
    )
    assert bta.page_texts(tei) == {1: "erste", 2: "zweite"}


def test_page_texts_without_pb_treats_body_as_single_page():
    tei = '<TEI xmlns="http://www.tei-c.org/ns/1.0"><text><body><p>nur eine</p></body></text></TEI>'
    assert bta.page_texts(tei) == {1: "nur eine"}


def test_page_texts_without_body_returns_empty_mapping():
    assert bta.page_texts("<TEI/>") == {}


def test_manifest_blank_pages_tolerates_missing_and_broken_keys():
    assert bta.manifest_blank_pages(None) == []
    assert bta.manifest_blank_pages({}) == []
    assert bta.manifest_blank_pages({"pages": []}) == []
    manifest = {"pages": {"3": {"class": "blank"}, "1": {"class": "blank"},
                          "5": {"class": "image_only"}, "x": {"class": "blank"},
                          "7": "kaputt"}}
    assert bta.manifest_blank_pages(manifest) == [1, 3]


# --- Dokument-Ebene ------------------------------------------------------------

def test_blank_page_without_text_is_classified_empty(corpus):
    doc = bta.audit_document("10", corpus["tei_dir"], corpus["mirror_dir"])
    assert doc["blank_pages"] == 2
    assert doc["by_class"]["empty"] == 1
    assert 2 not in [f["page"] for f in doc["findings"]]


def test_blank_page_with_substantial_text_is_a_finding_with_snippet_and_facsimile(corpus):
    doc = bta.audit_document("10", corpus["tei_dir"], corpus["mirror_dir"])
    finding = next(f for f in doc["findings"] if f["page"] == 4)
    assert finding["class"] == "substantial"
    assert finding["signal"] == "manifest"
    assert finding["chars"] >= bta.SUBSTANTIAL_MIN_CHARS
    assert len(finding["snippet"]) <= bta.SNIPPET_CHARS
    assert finding["snippet"].startswith("Initiation")
    assert finding["facsimile"] == "docs/images/10/10_p004.png"
    assert doc["by_class"]["substantial"] == 1


def test_blank_page_with_marginal_text_is_reported_as_marginal(corpus):
    doc = bta.audit_document("20", corpus["tei_dir"], corpus["mirror_dir"])
    finding = next(f for f in doc["findings"] if f["page"] == 2)
    assert finding["class"] == "marginal"
    assert doc["by_class"] == {"empty": 0, "marginal": 1, "substantial": 0}


def test_non_blank_page_without_text_is_reported_as_inverse_signal(corpus):
    doc = bta.audit_document("20", corpus["tei_dir"], corpus["mirror_dir"])
    assert doc["non_blank_empty_pages"] == [3]


def test_missing_pages_section_is_tolerated(corpus):
    doc = bta.audit_document("30", corpus["tei_dir"], corpus["mirror_dir"])
    assert doc["blank_pages"] == 0
    assert doc["error"] is None


def test_layout_zero_regions_with_text_is_a_second_channel_finding(corpus):
    doc = bta.audit_document("30", corpus["tei_dir"], corpus["mirror_dir"])
    finding = next(f for f in doc["findings"] if f["signal"] == "layout")
    assert finding["page"] == 2
    assert finding["class"] == "substantial"
    assert finding["facsimile"] == "docs/images/30/30_p002.png"
    # Die Seite mit Regionen ist kein Fund
    assert [f["page"] for f in doc["findings"] if f["signal"] == "layout"] == [2]


def test_layout_channel_ignores_pages_already_flagged_by_the_manifest(corpus):
    _write_layout(corpus["mirror_dir"], "10", 4, 0)
    doc = bta.audit_document("10", corpus["tei_dir"], corpus["mirror_dir"])
    page4 = [f for f in doc["findings"] if f["page"] == 4]
    assert len(page4) == 1
    assert page4[0]["signal"] == "manifest"


def test_blank_page_beyond_the_pb_count_is_reported_as_missing(tmp_path):
    tei_dir = tmp_path / "tei_final"
    tei_dir.mkdir()
    _write_doc(tei_dir, "40", [_para("eins")], blank_pages=[9], page_count=9)
    doc = bta.audit_document("40", tei_dir, tmp_path / "pages")
    assert doc["blank_pages_missing_in_tei"] == [9]


def test_missing_manifest_is_tolerated(tmp_path):
    tei_dir = tmp_path / "tei_final"
    tei_dir.mkdir()
    (tei_dir / "50_final.xml").write_text(_tei([_para("eins")]), encoding="utf-8")
    doc = bta.audit_document("50", tei_dir, tmp_path / "pages")
    assert doc["manifest_found"] is False
    assert doc["blank_pages"] == 0


# --- Aggregation und Report ----------------------------------------------------

def test_corpus_aggregation_sums_blank_pages_and_classes(corpus):
    summary = bta.audit_corpus(corpus["tei_dir"], corpus["mirror_dir"])
    assert summary["total_docs"] == 3
    assert summary["totals"]["blank_pages"] == 3
    assert summary["totals"]["by_class"] == {"empty": 1, "marginal": 1, "substantial": 1}
    assert summary["totals"]["layout_findings"] == 1
    assert summary["totals"]["non_blank_empty_pages"] == 1
    assert summary["totals"]["docs_with_findings"] == 3


def test_top_findings_are_ordered_by_char_count(corpus):
    summary = bta.audit_corpus(corpus["tei_dir"], corpus["mirror_dir"])
    top = bta.top_findings(summary, limit=5)
    assert [f["doc_id"] for f in top][:2] == ["10", "30"] or [f["chars"] for f in top] == sorted(
        [f["chars"] for f in top], reverse=True)
    assert all(top[i]["chars"] >= top[i + 1]["chars"] for i in range(len(top) - 1))


def test_payload_is_deterministic_and_timestamp_free(corpus):
    a = bta.build_payload(bta.audit_corpus(corpus["tei_dir"], corpus["mirror_dir"]))
    b = bta.build_payload(bta.audit_corpus(corpus["tei_dir"], corpus["mirror_dir"]))
    assert json.dumps(a, ensure_ascii=False, sort_keys=False) == json.dumps(
        b, ensure_ascii=False, sort_keys=False)
    assert list(a["documents"]) == ["10", "20", "30"]
    assert not _keys_matching(a, ("generated", "timestamp", "date", "elapsed", "run_at"))
    assert a["thresholds"] == {"empty_max_chars": 20, "substantial_min_chars": 200}


def _keys_matching(node, banned):
    """Alle Schluessel im Payload, die einen Zeitstempel-Namen tragen."""
    hits = []
    if isinstance(node, dict):
        for key, value in node.items():
            if any(b in str(key).lower() for b in banned):
                hits.append(key)
            hits.extend(_keys_matching(value, banned))
    elif isinstance(node, list):
        for item in node:
            hits.extend(_keys_matching(item, banned))
    return hits


def test_inspect_page_returns_the_full_picture_for_one_page(corpus):
    info = bta.inspect_page("10", 4, corpus["tei_dir"], corpus["mirror_dir"])
    assert info["manifest_blank"] is True
    assert info["class"] == "substantial"
    assert info["chars"] >= bta.SUBSTANTIAL_MIN_CHARS
    assert info["facsimile"] == "docs/images/10/10_p004.png"

    info30 = bta.inspect_page("30", 2, corpus["tei_dir"], corpus["mirror_dir"])
    assert info30["manifest_blank"] is False
    assert info30["docling_regions"] == 0

    missing = bta.inspect_page("10", 99, corpus["tei_dir"], corpus["mirror_dir"])
    assert missing["in_tei"] is False
