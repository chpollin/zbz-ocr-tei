"""Tests for the METS manifest generator (scripts/layout/mets_generator.py).

The METS file is the Transkribus-facing manifest of the PAGE-XML export: the file
sequence, the fileGrp nesting, the structMap order and the xlink hrefs are the contract
the upload relies on. The tests pin that output shape on a synthetic page set, so a
change to the element construction cannot pass unnoticed.
"""

from lxml import etree

from scripts.layout import mets_generator
from scripts.layout.mets_generator import METS_NS, XLINK_NS, generate_mets, write_mets

PAGES = ["2310_p001.xml", "2310_p002.xml", "2310_p003.xml"]


def _find_all(root, local_name):
    return root.findall(f".//{{{METS_NS}}}{local_name}")


def test_root_carries_label_and_profile():
    root = generate_mets("2310", PAGES)
    assert root.tag == f"{{{METS_NS}}}mets"
    assert root.get("LABEL") == "2310"
    assert root.get("PROFILE") == "zbz-ocr-tei"


def test_header_names_the_generating_agent():
    root = generate_mets("2310", PAGES)
    hdr = root.find(f"{{{METS_NS}}}metsHdr")
    assert hdr.get("CREATEDATE") == hdr.get("LASTMODDATE")
    agent = hdr.find(f"{{{METS_NS}}}agent")
    assert (agent.get("ROLE"), agent.get("TYPE")) == ("CREATOR", "ORGANIZATION")
    assert agent.find(f"{{{METS_NS}}}name").text == "zbz-ocr-tei"


def test_file_section_nests_pagexml_group_inside_master():
    root = generate_mets("2310", PAGES)
    master = root.find(f"{{{METS_NS}}}fileSec/{{{METS_NS}}}fileGrp")
    assert master.get("ID") == "MASTER"
    page_grp = master.find(f"{{{METS_NS}}}fileGrp")
    assert page_grp.get("ID") == "PAGEXML"
    assert len(page_grp) == len(PAGES)


def test_files_are_numbered_from_one_and_link_into_the_page_folder():
    root = generate_mets("2310", PAGES)
    files = _find_all(root, "file")
    assert [f.get("ID") for f in files] == ["PAGEXML_1", "PAGEXML_2", "PAGEXML_3"]
    assert [f.get("SEQ") for f in files] == ["1", "2", "3"]
    assert {f.get("MIMETYPE") for f in files} == {"application/xml"}
    hrefs = [f.find(f"{{{METS_NS}}}FLocat").get(f"{{{XLINK_NS}}}href") for f in files]
    assert hrefs == [f"page/{name}" for name in PAGES]
    locat = files[0].find(f"{{{METS_NS}}}FLocat")
    assert (locat.get("LOCTYPE"), locat.get("OTHERLOCTYPE")) == ("OTHER", "FILE")
    assert locat.get(f"{{{XLINK_NS}}}type") == "simple"


def test_struct_map_orders_single_pages_and_points_at_the_files():
    root = generate_mets("2310", PAGES)
    struct_map = root.find(f"{{{METS_NS}}}structMap")
    assert (struct_map.get("ID"), struct_map.get("TYPE")) == ("STRUCT_MAP", "MANUSCRIPT")
    doc_div = struct_map.find(f"{{{METS_NS}}}div")
    assert doc_div.get("ID") == "DOC_DIV"
    page_divs = doc_div.findall(f"{{{METS_NS}}}div")
    assert [d.get("ORDER") for d in page_divs] == ["1", "2", "3"]
    assert {d.get("TYPE") for d in page_divs} == {"SINGLE_PAGE"}
    areas = [d.find(f"{{{METS_NS}}}fptr/{{{METS_NS}}}area") for d in page_divs]
    assert [a.get("FILEID") for a in areas] == ["PAGEXML_1", "PAGEXML_2", "PAGEXML_3"]


def test_empty_page_list_yields_a_manifest_without_files():
    root = generate_mets("2310", [])
    assert _find_all(root, "file") == []
    assert root.find(f"{{{METS_NS}}}structMap/{{{METS_NS}}}div").find(
        f"{{{METS_NS}}}div") is None


def _page_dir(tmp_path, names):
    page_dir = tmp_path / "2310" / "page"
    page_dir.mkdir(parents=True)
    for name in names:
        (page_dir / name).write_text("<PcGts/>", encoding="utf-8")
    return tmp_path / "2310"


def test_write_mets_collects_and_sorts_the_page_files(tmp_path):
    base = _page_dir(tmp_path, ["2310_p002.xml", "2310_p001.xml", "notes.xml"])

    path = write_mets("2310", page_xml_dir=base)

    assert path == base / "mets.xml"
    root = etree.parse(str(path)).getroot()
    hrefs = [f.find(f"{{{METS_NS}}}FLocat").get(f"{{{XLINK_NS}}}href")
             for f in _find_all(root, "file")]
    assert hrefs == ["page/2310_p001.xml", "page/2310_p002.xml"]


def test_write_mets_declares_utf8(tmp_path):
    base = _page_dir(tmp_path, ["2310_p001.xml"])
    path = write_mets("2310", page_xml_dir=base)
    assert path.read_bytes().startswith(b"<?xml version='1.0' encoding='UTF-8'?>")


def test_write_mets_returns_none_without_page_folder(tmp_path):
    assert write_mets("2310", page_xml_dir=tmp_path / "2310") is None


def test_write_mets_returns_none_when_no_page_file_matches(tmp_path):
    base = _page_dir(tmp_path, ["notes.xml"])
    assert write_mets("2310", page_xml_dir=base) is None


def test_write_mets_defaults_to_the_configured_page_xml_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(mets_generator, "PAGE_XML_DIR", tmp_path)
    _page_dir(tmp_path, ["2310_p001.xml"])
    assert write_mets("2310") == tmp_path / "2310" / "mets.xml"
