"""Tests fuer scripts/edition/generate_entity_preview_data.py.

Nagelt die drei Vertraege des Entity-Mirrors fest:

1. Seiten-Split: dieselbe Seitennummern-Konvention wie der TEI-Mirror (1-basierte
   pb-Position, NICHT das n-Attribut) -- eine Abweichung wuerde die Entity-Seite neben
   das falsche Faksimile legen.
2. Worklist-Seitenzuordnung: Report-Offsets zeigen auf das QUELLDOKUMENT, die
   Preview-Datei traegt zusaetzlich die Tier-1-Wrapper. Die Verschiebung wird aus dem
   Report berechnet und gegen den Preview-Text verifiziert.
3. entities.json: Form des Nachschlagewerks, das das Viewer-Popover aufloest.

Die Mini-Previews sind synthetisch (Randfaelle wie Journal-Pagination im n-Attribut sind
im Korpus nicht isoliert greifbar), werden aber mit dem echten ``apply_candidates`` des
Preview-Laeufers erzeugt, damit Fixture und Pipeline dieselbe Wrapper-Mechanik benutzen.
Die GND-Ids stammen aus data/entities/all_entities.json.
"""

from __future__ import annotations

import json
import re

import pytest

from scripts.edition.generate_entity_preview_data import (
    WORKLIST_FIELDS,
    build_entities_index,
    life_dates,
    page_of,
    pb_offsets,
    plain_text,
    run,
    worklist_pages,
    write_doc,
)
from scripts.tei.tei_entity_preview import apply_candidates

DOC_ID = "9999"

SOURCE = (
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    '<TEI xmlns="http://www.tei-c.org/ns/1.0">\n'
    "  <teiHeader><fileDesc><titleStmt><title>Mini</title></titleStmt></fileDesc></teiHeader>\n"
    "  <text><body>\n"
    '    <pb n="56" facs="#f1"/><p>Seite eins nennt Karl Jaspers und Corneille.</p>\n'
    '    <pb n="57" facs="#f2"/><p>Seite zwei nennt die UNESCO und Hitler.</p>\n'
    "  </body></text>\n"
    "</TEI>\n"
)

# (surface, gid, category, rule, tier); ids aus data/entities/all_entities.json
MENTIONS = [
    ("Karl Jaspers", "118557106", "person", "full-name", 1),
    ("Corneille", "118522175", "person", "bare-surname", 2),
    ("UNESCO", "2023755-8", "organisation", "org-token", 1),
    ("Hitler", "118551655", "person", "bare-surname", 2),
]

_WRAPPER_RE = re.compile(r"</?(?:persName|orgName|bibl)(?=[\s>])[^>]*>")


def _candidate(source: str, surface: str, gid: str, category: str, rule: str, tier: int,
               nth: int = 1, alternatives=(), matched_form=None,
               form_source: str = "headword", evidence=None) -> dict:
    start = -1
    for _ in range(nth):
        start = source.index(surface, start + 1)
    candidate = {
        "gid": gid,
        "category": category,
        "surface": surface,
        "start": start,
        "end": start + len(surface),
        "tier": tier,
        "rule": rule,
        "alternatives": list(alternatives),
        "matched_form": surface if matched_form is None else matched_form,
        "form_source": form_source,
        "context": f"... {surface} ...",
    }
    if evidence is not None:
        candidate["evidence"] = evidence
    return candidate


def _doc_result(source: str = SOURCE) -> dict:
    candidates = [_candidate(source, *m) for m in MENTIONS]
    for candidate in candidates:
        # a bare surname comes from the surname index, not from a form of its own
        if candidate["rule"] == "bare-surname":
            candidate["form_source"] = "surname-index"
    return {
        "doc": DOC_ID,
        "wrapped": [c for c in candidates if c["tier"] == 1],
        "worklist": [c for c in candidates if c["tier"] == 2],
    }


def _preview_xml(source: str = SOURCE) -> str:
    result = _doc_result(source)
    return apply_candidates(source, result["wrapped"] + result["worklist"])


@pytest.fixture
def preview_dir(tmp_path):
    """Preview directory as tei_entity_preview leaves it: one XML plus the pilot report."""
    directory = tmp_path / "entity_preview"
    directory.mkdir()
    (directory / f"{DOC_ID}_final.xml").write_bytes(_preview_xml().encode("utf-8"))
    report = {"documents": [_doc_result()], "totals": {"documents": 1}}
    (directory / "entity_pilot_report.json").write_text(
        json.dumps(report, ensure_ascii=False), encoding="utf-8"
    )
    return directory


@pytest.fixture
def entity_sources(tmp_path):
    """Minimal curated list plus GND cache, in the real file shapes."""
    entities_path = tmp_path / "all_entities.json"
    cache_path = tmp_path / "gnd_cache.json"
    entities_path.write_text(json.dumps({
        "persons": [
            {"GND_id": "118557106", "name": "Jaspers, Karl"},
            {"GND_id": "118522175", "name": "Corneille, Pierre"},
        ],
        "organisations": [{"GND_id": "2023755-8", "orgName": "UNESCO"}],
        "works": [{"GND_id": "4558181-2", "title": "Allgemeine Psychopathologie",
                   "author_gnd_id": "118557106"}],
    }, ensure_ascii=False), encoding="utf-8")
    cache_path.write_text(json.dumps({
        "retrieved": "2026-08-12",
        "entries": {
            "118557106": {"http_status": 200, "preferred_name": "Jaspers, Karl",
                          "date_of_birth": "1883-02-23", "date_of_death": "1969-02-26"},
            "118522175": {"http_status": 200, "preferred_name": "Corneille, Pierre",
                          "date_of_birth": "1606-06-06", "date_of_death": "1684-10-01"},
            "2023755-8": {"http_status": 200, "preferred_name": "UNESCO"},
            "4558181-2": {"http_status": 200, "preferred_name": "Allgemeine Psychopathologie"},
        },
    }, ensure_ascii=False), encoding="utf-8")
    return entities_path, cache_path


# --- Offsets und Seiten ---------------------------------------------------------------


def test_pb_offsets_point_at_the_pb_tags():
    preview = _preview_xml()
    offsets = pb_offsets(preview)
    assert len(offsets) == 2
    assert all(preview.startswith("<pb ", offset) for offset in offsets)


def test_pb_offsets_empty_without_body():
    assert pb_offsets("<TEI><teiHeader/></TEI>") == []


def test_page_of_clamps_content_before_the_first_pb():
    assert page_of([100, 200], 5) == 1
    assert page_of([100, 200], 150) == 1
    assert page_of([100, 200], 200) == 2


# --- Worklist -------------------------------------------------------------------------


def test_worklist_survives_the_header_responsibility_declarations():
    """The respStmt block sits in front of the body, so every body offset moves with it.

    The preview runner records that shift; without it every worklist entry of a
    document that declares a responsibility would be dropped as stale.
    """
    from scripts.tei.tei_entity_preview import insert_resp_stmts

    statements = [("resp-entity-matcher", "Automatic entity matching")]
    preview = insert_resp_stmts(_preview_xml(), statements)
    result = _doc_result()
    shift = len(preview) - len(_preview_xml())
    assert shift > 0

    pages, stale = worklist_pages({**result, "header_shift": shift}, preview)
    assert stale == 0
    assert [e["surface"] for e in pages["1"]] == ["Corneille"]
    assert [e["surface"] for e in pages["2"]] == ["Hitler"]


def test_worklist_grouped_by_page_over_shifted_offsets():
    pages, stale = worklist_pages(_doc_result(), _preview_xml())
    assert stale == 0
    # Seitenzahl folgt der pb-Position, nicht dem n-Attribut (56/57)
    assert sorted(pages) == ["1", "2"]
    assert [e["surface"] for e in pages["1"]] == ["Corneille"]
    assert [e["surface"] for e in pages["2"]] == ["Hitler"]


def test_worklist_entries_carry_exactly_the_viewer_fields():
    pages, _ = worklist_pages(_doc_result(), _preview_xml())
    entry = pages["1"][0]
    assert tuple(entry) == (*WORKLIST_FIELDS, "text", "occurrence")
    assert entry["gid"] == "118522175"
    assert entry["rule"] == "bare-surname"
    assert entry["alternatives"] == []
    assert entry["matched_form"] == "Corneille"
    assert entry["form_source"] == "surname-index"


def test_worklist_entry_carries_the_alternatives_and_the_variant_it_came_from():
    """Ambiguity and provenance must reach the popover, not stop at the report."""
    source = SOURCE.replace("Corneille", "Jaspers")
    cand = _candidate(source, "Jaspers", "117085391", "person", "bare-surname:ambiguous", 2,
                      alternatives=("117085391", "118557106"),
                      matched_form="Mayer, Gertrud", form_source="cache-variant")
    pages, stale = worklist_pages({"doc": DOC_ID, "wrapped": [], "worklist": [cand]}, source)
    entry = pages["1"][0]
    assert stale == 0
    assert entry["alternatives"] == ["117085391", "118557106"]
    assert entry["matched_form"] == "Mayer, Gertrud"
    assert entry["form_source"] == "cache-variant"


def test_worklist_entry_of_a_one_word_title_carries_its_evidence():
    source = SOURCE.replace("Corneille", "Bibel")
    cand = _candidate(source, "Bibel", "4006406-2", "work", "short-title", 2,
                      evidence="none")
    pages, _ = worklist_pages({"doc": DOC_ID, "wrapped": [], "worklist": [cand]}, source)
    assert pages["1"][0]["evidence"] == "none"


def test_worklist_entry_without_evidence_omits_the_field():
    pages, _ = worklist_pages(_doc_result(), _preview_xml())
    assert "evidence" not in pages["1"][0]


# --- Inline-Verortung (occurrence) ----------------------------------------------------


def test_plain_text_strips_markup_and_decodes_entities():
    assert plain_text('a <hi rendition="#i">b</hi>&amp;c<lb/>d') == "a b&cd"


def test_plain_text_normalizes_line_ends_like_the_xml_parser():
    """Die Dateien tragen CRLF, der geparste DOM nur LF; sonst zaehlt der Viewer anders."""
    assert plain_text("eins\r\nzwei\rdrei") == "eins\nzwei\ndrei"


def test_entries_carry_the_dom_text_and_the_first_occurrence():
    pages, _ = worklist_pages(_doc_result(), _preview_xml())
    entry = pages["1"][0]
    assert entry["text"] == "Corneille"
    assert entry["occurrence"] == 1


def test_occurrence_counts_earlier_hits_on_the_same_page():
    """Die Seite nennt den Namen dreimal; markiert wird das dritte Vorkommen."""
    source = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<TEI xmlns="http://www.tei-c.org/ns/1.0">\n'
        "  <text><body>\n"
        '    <pb n="1" facs="#f1"/><p>Hitler und Hitler, dann <hi rendition="#i">Hitler</hi>.</p>\n'
        '    <pb n="2" facs="#f2"/><p>Auf Seite zwei erneut Hitler.</p>\n'
        "  </body></text>\n"
        "</TEI>\n"
    )
    third = _candidate(source, "Hitler", "118551655", "person", "bare-surname", 2, nth=3)
    page_two = _candidate(source, "Hitler", "118551655", "person", "bare-surname", 2, nth=4)
    result = {"doc": DOC_ID, "wrapped": [], "worklist": [third, page_two]}

    pages, stale = worklist_pages(result, source)
    assert stale == 0
    assert pages["1"][0]["occurrence"] == 3
    # Die Zaehlung ist seitenlokal, nicht dokumentweit
    assert pages["2"][0]["occurrence"] == 1


def test_occurrence_survives_the_tier1_wrappers():
    """Der Wrapper eines Tier-1-Treffers darf die Zaehlung nicht verschieben."""
    result = _doc_result()
    preview = _preview_xml()
    pages, _ = worklist_pages(result, preview)
    assert pages["2"][0]["text"] == "Hitler"
    assert pages["2"][0]["occurrence"] == 1


def test_entry_before_the_first_pb_has_no_occurrence():
    """Inhalt vor dem ersten <pb> steht in keiner Seiten-Datei, also nicht verortbar."""
    source = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<TEI xmlns="http://www.tei-c.org/ns/1.0">\n'
        "  <text><body>\n"
        "    <head>Vorspann mit Corneille</head>\n"
        '    <pb n="1" facs="#f1"/><p>Seite eins.</p>\n'
        "  </body></text>\n"
        "</TEI>\n"
    )
    cand = _candidate(source, "Corneille", "118522175", "person", "bare-surname", 2)
    pages, stale = worklist_pages({"doc": DOC_ID, "wrapped": [], "worklist": [cand]}, source)
    assert stale == 0
    assert pages["1"][0]["occurrence"] is None


def test_worklist_drops_entries_whose_offsets_no_longer_match():
    # Report veraltet gegenueber der Preview-Datei: lieber verlieren als falsch einsortieren.
    result = _doc_result()
    result["worklist"][0]["start"] += 7
    result["worklist"][0]["end"] += 7
    pages, stale = worklist_pages(result, _preview_xml())
    assert stale == 1
    assert [e["surface"] for entries in pages.values() for e in entries] == ["Hitler"]


def test_worklist_maps_through_crlf_preview_files(tmp_path):
    """Die gelieferten TEI tragen CRLF; Textmodus-Lesen wuerde sie kollabieren und
    saemtliche Report-Offsets verschieben (alle Eintraege faelschlich 'stale')."""
    source = SOURCE.replace("\n", "\r\n")
    preview_path = tmp_path / "preview.xml"
    preview_path.write_bytes(_preview_xml(source).encode("utf-8"))

    stats = write_doc(DOC_ID, preview_path, _doc_result(source), tmp_path / "pages")
    assert stats["stale"] == 0
    assert stats["unplaced"] == 0
    worklist = json.loads(
        (tmp_path / "pages" / DOC_ID / f"{DOC_ID}_entity_worklist.json").read_text(encoding="utf-8")
    )
    assert [e["surface"] for e in worklist["pages"]["2"]] == ["Hitler"]
    assert worklist["pages"]["2"][0]["occurrence"] == 1


# --- Seiten-Split ---------------------------------------------------------------------


def test_split_writes_one_entity_file_per_page(tmp_path):
    preview_path = tmp_path / f"{DOC_ID}_final.xml"
    preview_path.write_bytes(_preview_xml().encode("utf-8"))
    stats = write_doc(DOC_ID, preview_path, _doc_result(), tmp_path / "pages")

    doc_dir = tmp_path / "pages" / DOC_ID
    page1 = (doc_dir / f"{DOC_ID}_entity_p1.xml").read_text(encoding="utf-8")
    page2 = (doc_dir / f"{DOC_ID}_entity_p2.xml").read_text(encoding="utf-8")
    assert stats["pages"] == 2
    assert not (doc_dir / f"{DOC_ID}_entity_p3.xml").exists()
    assert '<persName ref="GND:118557106" source="full-name"' in page1
    assert "Karl Jaspers</persName>" in page1
    assert "UNESCO" not in page1
    assert '<orgName ref="GND:2023755-8" source="org-token"' in page2
    assert "UNESCO</orgName>" in page2
    assert page1.startswith("<?xml") and "<body>" in page1


def test_entity_pages_align_with_the_tei_mirror_pages(tmp_path):
    """Entity page N must be the mirror page N plus the wrappers, nothing else."""
    from scripts.edition.generate_edition_data import _extract_pages_from_final

    source_path = tmp_path / f"{DOC_ID}_final.xml"
    source_path.write_bytes(SOURCE.encode("utf-8"))
    mirror_pages = _extract_pages_from_final(source_path)

    preview_path = tmp_path / "preview.xml"
    preview_path.write_bytes(_preview_xml().encode("utf-8"))
    write_doc(DOC_ID, preview_path, _doc_result(), tmp_path / "pages")

    doc_dir = tmp_path / "pages" / DOC_ID
    for page_number, mirror_xml in mirror_pages.items():
        entity_xml = (doc_dir / f"{DOC_ID}_entity_p{page_number}.xml").read_text(encoding="utf-8")
        assert _WRAPPER_RE.sub("", entity_xml) == mirror_xml


# --- entities.json --------------------------------------------------------------------


def test_entities_index_shape(entity_sources):
    entities_path, cache_path = entity_sources
    index = build_entities_index(entities_path, cache_path)

    assert index["118557106"] == {
        "label": "Jaspers, Karl",
        "category": "person",
        "dates": "1883-1969",
        "lobid": "https://lobid.org/gnd/118557106",
    }
    assert index["2023755-8"]["category"] == "organisation"
    assert index["2023755-8"]["dates"] is None
    assert index["4558181-2"]["category"] == "work"


def test_entities_index_skips_ids_the_gnd_does_not_know(entity_sources, tmp_path):
    entities_path, cache_path = entity_sources
    cache = json.loads(cache_path.read_text(encoding="utf-8"))
    cache["entries"]["118522175"] = {"http_status": 404}
    cache_path.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")

    index = build_entities_index(entities_path, cache_path)
    assert "118522175" not in index
    assert "118557106" in index


def test_life_dates_handles_partial_records():
    assert life_dates({"date_of_birth": "1883-02-23", "date_of_death": None}) == "1883-"
    assert life_dates({}) is None


# --- Lauf -----------------------------------------------------------------------------


def test_run_writes_mirror_and_index(preview_dir, entity_sources, tmp_path):
    entities_path, cache_path = entity_sources
    pages_dir = tmp_path / "pages"
    index_path = tmp_path / "entities.json"

    stats = run(preview_dir, pages_dir, index_path, entities_path, cache_path)

    assert stats["docs"] == [DOC_ID] and stats["pages"] == 2 and stats["stale"] == 0
    worklist = json.loads(
        (pages_dir / DOC_ID / f"{DOC_ID}_entity_worklist.json").read_text(encoding="utf-8")
    )
    assert worklist["doc"] == DOC_ID
    assert sorted(worklist["pages"]) == ["1", "2"]
    assert json.loads(index_path.read_text(encoding="utf-8"))["118557106"]["label"] == "Jaspers, Karl"


def test_run_is_idempotent(preview_dir, entity_sources, tmp_path):
    entities_path, cache_path = entity_sources
    pages_dir = tmp_path / "pages"
    index_path = tmp_path / "entities.json"

    run(preview_dir, pages_dir, index_path, entities_path, cache_path)
    first = {p.name: p.read_bytes() for p in sorted((pages_dir / DOC_ID).iterdir())}
    first["entities.json"] = index_path.read_bytes()

    run(preview_dir, pages_dir, index_path, entities_path, cache_path)
    second = {p.name: p.read_bytes() for p in sorted((pages_dir / DOC_ID).iterdir())}
    second["entities.json"] = index_path.read_bytes()

    assert first == second


def test_run_filters_by_doc_ids(preview_dir, entity_sources, tmp_path):
    entities_path, cache_path = entity_sources
    pages_dir = tmp_path / "pages"
    stats = run(preview_dir, pages_dir, tmp_path / "entities.json",
                entities_path, cache_path, doc_ids=["1234"])
    assert stats["docs"] == []
    assert not pages_dir.exists() or not (pages_dir / DOC_ID).exists()


def test_run_fails_fast_without_report(tmp_path, entity_sources):
    entities_path, cache_path = entity_sources
    with pytest.raises(FileNotFoundError):
        run(tmp_path / "empty", tmp_path / "pages", tmp_path / "entities.json",
            entities_path, cache_path)


def test_run_skips_documents_without_preview_file(preview_dir, entity_sources, tmp_path):
    entities_path, cache_path = entity_sources
    (preview_dir / f"{DOC_ID}_final.xml").unlink()
    stats = run(preview_dir, tmp_path / "pages", tmp_path / "entities.json",
                entities_path, cache_path)
    assert stats["skipped"] == [DOC_ID]
    assert stats["docs"] == []
