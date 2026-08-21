"""Tests fuer scripts/tei/tei_cover_strip.py (Bestandskorrektur E-Periodica-Deckblatt).

Nagelt den Kontrakt der Operator-Entscheidung 2026-08-12 fest: ein Deckblatt liegt vor,
wenn der Inhalt zwischen erstem und zweitem <pb> mindestens drei der vier Feldzeilen
"Zeitschrift:", "Herausgeber:", "Band:", "Heft:" traegt. Teiltreffer bleiben unangetastet,
ein Ein-Seiten-Dokument wird nie gestrippt, die Seitenmarke bleibt als
<pb type="cover"/> erhalten, Folgeseiten sind textinvariant, der Schreibpfad ist
idempotent und legt ein Backup an, das Ergebnis bleibt RelaxNG-valide.

Alle Faelle laufen auf synthetischen Mini-TEI in tmp_path; der Bestand unter
output/tei_final wird von diesen Tests nicht angefasst.
"""

import json
import re

import pytest

from scripts.tei import tei_cover_strip as cs
from tests.conftest import tei_doc

WHEN = "2026-08-12"

_TAG_RE = re.compile(r"<[^>]+>")

_COVER_FIELDS_4 = (
    '<head facs="#facs_1_r_1">Zeitschrift: Studia philosophica</head>\n'
    '<p facs="#facs_1_r_2">Herausgeber: Schweizerische Philosophische Gesellschaft</p>\n'
    '<p facs="#facs_1_r_3">Band: 21 (1961)</p>\n'
    '<p facs="#facs_1_r_4">Heft: 4</p>\n'
    '<p facs="#facs_1_r_5">Nutzungsbedingungen</p>'
)
_COVER_FIELDS_3 = (
    '<p facs="#facs_1_r_1">Zeitschrift: Studia philosophica</p>\n'
    '<p facs="#facs_1_r_2">Herausgeber: Schweizerische Philosophische Gesellschaft</p>\n'
    '<p facs="#facs_1_r_3">Band: 21 (1961)</p>\n'
    '<p facs="#facs_1_r_4">Autor: Hersch, Jeanne</p>'
)
_COVER_FIELDS_2 = (
    '<p facs="#facs_1_r_1">Zeitschrift: Etudes pedagogiques</p>\n'
    '<p facs="#facs_1_r_2">Band: 41 (1950)</p>\n'
    '<p facs="#facs_1_r_3">Autor: Hersch, Jeanne</p>'
)

_PAGE_TWO = '<p facs="#facs_2_r_1">Erste Zeile des Artikels.</p>\n<p>Zweite Zeile.</p>'


def _tei(body_inner, revision=None):
    """Minimales, RelaxNG-valides TEI-Geruest mit vorgegebenem <body>-Inhalt."""
    revision = revision or (
        '<change when="2026-03-15" who="pipeline">TEI generated</change>'
    )
    header = (
        "<teiHeader><fileDesc>"
        "<titleStmt><title>Testdokument</title></titleStmt>"
        "<publicationStmt><p>ZBZ</p></publicationStmt>"
        "<sourceDesc><p>Testquelle</p></sourceDesc>"
        "</fileDesc>"
        f"<revisionDesc>{revision}</revisionDesc>"
        "</teiHeader>"
    )
    return tei_doc(f"\n{body_inner}\n", header=header, xml_decl=True)


def _flat_doc(cover, pages=2):
    """Deckblatt und Folgeseiten als direkte Kinder eines <div> (Muster Doc 570)."""
    parts = [f'<div type="review">\n<pb facs="#facs_1" n="1" />\n{cover}']
    for p in range(2, pages + 1):
        parts.append(f'<pb facs="#facs_{p}" n="{p}" />\n{_PAGE_TWO}')
    parts.append("</div>")
    return _tei("\n".join(parts))


def _nested_doc(cover):
    """Deckblatt in einem eigenen Unter-<div> (Muster Doc 1000)."""
    body = (
        '<div n="1">\n'
        '<pb facs="#facs_1" n="1" />\n'
        f'<div type="text">\n{cover}\n</div>\n'
        '<pb facs="#facs_2" n="2" />\n'
        f'<div type="text">\n{_PAGE_TWO}\n</div>\n'
        "</div>"
    )
    return _tei(body)


def _write(tmp_path, doc_id, raw):
    path = tmp_path / f"{doc_id}_final.xml"
    path.write_text(raw, encoding="utf-8")
    return path


def _visible(fragment):
    return re.sub(r"\s+", " ", _TAG_RE.sub("", fragment)).strip()


def _page_texts(raw):
    """Sichtbarer Text je <pb>-Seite (1-basiert), aus dem <body>-Inhalt."""
    from scripts.core.pb_split import BODY_INNER_RE, iter_page_spans

    inner = BODY_INNER_RE.search(raw).group(1)
    return {s.page: _visible(inner[s.content_start:s.content_end])
            for s in iter_page_spans(inner)}


# ---------------------------------------------------------------------------
# Erkennung: Feldzeilen
# ---------------------------------------------------------------------------

def test_detect_fields_finds_all_four():
    assert cs.detect_fields(_visible(_COVER_FIELDS_4)) == list(cs.FIELD_LABELS)


def test_detect_fields_three_is_enough():
    fields = cs.detect_fields(_visible(_COVER_FIELDS_3))
    assert len(fields) == cs.MIN_FIELDS
    assert cs.is_cover(fields) is True


def test_detect_fields_two_is_partial():
    fields = cs.detect_fields(_visible(_COVER_FIELDS_2))
    assert len(fields) == 2
    assert cs.is_cover(fields) is False


def test_detect_fields_ignores_label_inside_running_text():
    assert cs.detect_fields("Die Zeitschrift erschien 1961.") == []


# ---------------------------------------------------------------------------
# strip_page_content: nur unbalancierte div-Grenzen ueberleben
# ---------------------------------------------------------------------------

def test_strip_drops_balanced_content():
    new, kept = cs.strip_page_content("<p>Text</p><head>Titel</head>")
    assert kept == []
    assert _visible(new) == ""


def test_strip_drops_balanced_inner_div():
    new, kept = cs.strip_page_content('<div type="text"><p>Deckblatt</p></div>')
    assert kept == []
    assert "<div" not in new


def test_strip_keeps_unbalanced_div_boundaries():
    new, kept = cs.strip_page_content('<p>Deckblatt</p></div><div n="2">')
    assert kept == ["</div>", '<div n="2">']
    assert "<p>" not in new and "</div>" in new and '<div n="2">' in new


def test_strip_reports_unbalanced_non_div_boundary():
    # ein ueber die Seitengrenze laufender Absatz: keine sichere Loeschung
    _, kept = cs.strip_page_content("Rest des Absatzes</p><p>Neuer Absatz</p>")
    assert kept == ["</p>"]
    assert cs.boundaries_are_safe(kept) is False


# ---------------------------------------------------------------------------
# set_pb_type
# ---------------------------------------------------------------------------

def test_set_pb_type_adds_cover():
    new, changed, existing = cs.set_pb_type('<pb facs="#facs_1" n="1" />', "cover")
    assert changed is True and existing is None
    assert new == '<pb facs="#facs_1" n="1" type="cover" />'


def test_set_pb_type_is_idempotent():
    tag = '<pb facs="#facs_1" n="1" type="cover" />'
    new, changed, existing = cs.set_pb_type(tag, "cover")
    assert (new, changed, existing) == (tag, False, "cover")


def test_set_pb_type_reports_foreign_type():
    tag = '<pb facs="#facs_1" n="1" type="blank" />'
    new, changed, existing = cs.set_pb_type(tag, "cover")
    assert (new, changed, existing) == (tag, False, "blank")


# ---------------------------------------------------------------------------
# transform_document: Wirkung, Verweigerungen, Idempotenz
# ---------------------------------------------------------------------------

def test_four_field_cover_is_stripped():
    raw = _flat_doc(_COVER_FIELDS_4)
    new, report = cs.transform_document(raw, WHEN)
    assert report["class"] == "cover"
    assert report["action"] == "strip"
    assert report["field_count"] == 4
    assert report["changed"] is True
    assert "Zeitschrift:" not in new and "Nutzungsbedingungen" not in new


def test_three_field_cover_is_stripped():
    new, report = cs.transform_document(_flat_doc(_COVER_FIELDS_3), WHEN)
    assert report["action"] == "strip"
    assert "Herausgeber:" not in new


def test_nested_cover_div_is_removed_completely():
    new, report = cs.transform_document(_nested_doc(_COVER_FIELDS_4), WHEN)
    assert report["action"] == "strip"
    assert new.count("<div") == 2  # aeusseres div + div der zweiten Seite


def test_partial_document_is_untouched():
    raw = _flat_doc(_COVER_FIELDS_2)
    new, report = cs.transform_document(raw, WHEN)
    assert report["class"] == "partial"
    assert report["action"] == "none"
    assert report["changed"] is False
    assert new == raw


def test_single_page_document_is_never_stripped():
    raw = _flat_doc(_COVER_FIELDS_4, pages=1)
    new, report = cs.transform_document(raw, WHEN)
    assert report["class"] == "cover"
    assert report["action"] == "skip"
    assert report["reason"] == "single page document"
    assert new == raw


def test_pb_survives_with_type_cover():
    new, _ = cs.transform_document(_flat_doc(_COVER_FIELDS_4), WHEN)
    assert '<pb facs="#facs_1" n="1" type="cover" />' in new
    assert new.count("<pb ") == 2  # Seitenzahl unveraendert


def test_following_pages_are_text_invariant():
    raw = _flat_doc(_COVER_FIELDS_4, pages=3)
    new, _ = cs.transform_document(raw, WHEN)
    before, after = _page_texts(raw), _page_texts(new)
    assert after[1] == ""
    assert {p: after[p] for p in (2, 3)} == {p: before[p] for p in (2, 3)}


def test_transform_is_idempotent():
    once, r1 = cs.transform_document(_flat_doc(_COVER_FIELDS_4), WHEN)
    twice, r2 = cs.transform_document(once, WHEN)
    assert r1["changed"] is True
    assert r2["changed"] is False
    assert r2["class"] == "already_stripped"
    assert twice == once


def test_foreign_pb_type_is_refused():
    raw = _flat_doc(_COVER_FIELDS_4).replace(
        '<pb facs="#facs_1" n="1" />', '<pb facs="#facs_1" n="1" type="blank" />')
    new, report = cs.transform_document(raw, WHEN)
    assert report["action"] == "skip"
    assert "blank" in report["reason"]
    assert new == raw


def test_unsafe_boundary_is_refused():
    # Deckblatt-Absatz laeuft ueber die Seitengrenze: Loeschung waere Textverlust
    body = (
        '<div type="review">\n<pb facs="#facs_1" n="1" />\n'
        f"{_COVER_FIELDS_4}\n<p>Anfang eines Absatzes\n"
        '<pb facs="#facs_2" n="2" />\n Fortsetzung</p>\n</div>'
    )
    raw = _tei(body)
    new, report = cs.transform_document(raw, WHEN)
    assert report["action"] == "skip"
    assert report["reason"] == "unsafe page boundary"
    assert new == raw


def test_document_without_pb_reports_error():
    raw = _tei("<div><p>Zeitschrift: X</p><p>Herausgeber: Y</p><p>Band: 1</p></div>")
    new, report = cs.transform_document(raw, WHEN)
    assert report["error"] == "kein <pb>"
    assert new == raw


# ---------------------------------------------------------------------------
# revisionDesc
# ---------------------------------------------------------------------------

def test_run_change_is_added_once():
    new, _ = cs.transform_document(_flat_doc(_COVER_FIELDS_4), WHEN)
    assert new.count(f'n="{cs.CHANGE_N}"') == 1
    assert f'when="{WHEN}"' in new
    assert 'who="pipeline">TEI generated' in new  # bestehender Eintrag bleibt


def test_run_change_replaces_own_earlier_entry():
    raw = _flat_doc(_COVER_FIELDS_4)
    once, _ = cs.transform_document(raw, "2026-01-01")
    # kuenstlich erneut strippbar machen: Deckblatt zurueckspielen, alten Eintrag behalten
    replayed = once.replace(
        '<pb facs="#facs_1" n="1" type="cover" />',
        f'<pb facs="#facs_1" n="1" />\n{_COVER_FIELDS_4}')
    twice, report = cs.transform_document(replayed, WHEN)
    assert report["action"] == "strip"
    assert twice.count(f'n="{cs.CHANGE_N}"') == 1
    assert f'when="{WHEN}"' in twice and 'when="2026-01-01"' not in twice


def test_missing_revision_desc_is_tolerated():
    raw = _flat_doc(_COVER_FIELDS_4)
    raw = re.sub(r"<revisionDesc>.*?</revisionDesc>", "", raw, flags=re.DOTALL)
    _, report = cs.transform_document(raw, WHEN)
    assert report["action"] == "strip"
    assert report["change_entry"] is False


# ---------------------------------------------------------------------------
# Schema: das Ergebnis bleibt RelaxNG-valide
# ---------------------------------------------------------------------------

def _validator():
    v = cs.schema_validator()
    assert v is not None, "lxml und data/schema/zbz_hersch.rng sind Pflicht"
    return v


@pytest.mark.parametrize("builder", [_flat_doc, _nested_doc])
def test_result_is_schema_valid(builder):
    validate = _validator()
    raw = builder(_COVER_FIELDS_4)
    assert validate(raw) == []          # Ausgangsdokument valide
    new, _ = cs.transform_document(raw, WHEN)
    assert validate(new) == []          # Ergebnis valide


# ---------------------------------------------------------------------------
# process_file: dry-run, Backup, Validierungs-Gate
# ---------------------------------------------------------------------------

def test_dry_run_writes_nothing(tmp_path):
    raw = _flat_doc(_COVER_FIELDS_4)
    path = _write(tmp_path, "999", raw)
    backup = tmp_path / "_backup"
    report = cs.process_file(path, backup, write=False, when=WHEN)
    assert report["action"] == "strip"
    assert report["changed"] is True
    assert path.read_text(encoding="utf-8") == raw
    assert not backup.exists()


def test_real_run_writes_and_backs_up(tmp_path):
    raw = _flat_doc(_COVER_FIELDS_4)
    path = _write(tmp_path, "999", raw)
    backup = tmp_path / "_backup"
    report = cs.process_file(path, backup, write=True, when=WHEN)
    assert report["changed"] is True
    assert (backup / "999_final.xml").read_text(encoding="utf-8") == raw
    written = path.read_text(encoding="utf-8")
    assert "Zeitschrift:" not in written
    assert 'type="cover"' in written


def test_real_run_second_pass_changes_nothing(tmp_path):
    path = _write(tmp_path, "999", _flat_doc(_COVER_FIELDS_4))
    backup = tmp_path / "_backup"
    cs.process_file(path, backup, write=True, when=WHEN)
    after_first = path.read_bytes()
    report = cs.process_file(path, backup, write=True, when=WHEN)
    assert report["changed"] is False
    assert path.read_bytes() == after_first


def test_partial_document_is_not_written(tmp_path):
    raw = _flat_doc(_COVER_FIELDS_2)
    path = _write(tmp_path, "998", raw)
    backup = tmp_path / "_backup"
    report = cs.process_file(path, backup, write=True, when=WHEN)
    assert report["class"] == "partial"
    assert path.read_text(encoding="utf-8") == raw
    assert not backup.exists()


def test_invalid_result_leaves_file_untouched(tmp_path):
    raw = _flat_doc(_COVER_FIELDS_4)
    path = _write(tmp_path, "997", raw)
    backup = tmp_path / "_backup"
    report = cs.process_file(path, backup, write=True, when=WHEN,
                             validator=lambda _raw: ["line 1: erzwungener Fehler"])
    assert report["action"] == "failed"
    assert report["changed"] is False
    assert path.read_text(encoding="utf-8") == raw
    assert not backup.exists()


# ---------------------------------------------------------------------------
# run_corpus: Report und Summen
# ---------------------------------------------------------------------------

def test_run_corpus_report(tmp_path):
    final_dir = tmp_path / "tei_final"
    final_dir.mkdir()
    (final_dir / "10_final.xml").write_text(_flat_doc(_COVER_FIELDS_4), encoding="utf-8")
    (final_dir / "20_final.xml").write_text(_flat_doc(_COVER_FIELDS_2), encoding="utf-8")
    (final_dir / "30_final.xml").write_text(_flat_doc(_COVER_FIELDS_4, pages=1),
                                            encoding="utf-8")
    report_path = tmp_path / "audits" / "cover_strip_report.json"

    payload = cs.run_corpus(final_dir, tmp_path / "_backup", report_path,
                            write=False, when=WHEN)

    assert payload["corpus_totals"]["scanned"] == 3
    assert payload["candidates"] == ["10", "30"]
    assert payload["partial"] == ["20"]
    assert payload["stripped"] == ["10"]
    assert payload["skipped"] == ["30"]
    on_disk = json.loads(report_path.read_text(encoding="utf-8"))
    assert on_disk["mode"] == "dry-run"
    assert on_disk["documents"]["30"]["reason"] == "single page document"
