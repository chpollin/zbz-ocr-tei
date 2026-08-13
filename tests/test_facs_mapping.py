"""Gate fuer die Textseite->Scanbild-Aufloesung des Viewer-Mirrors.

Doppelseitige Scans tragen mehr <pb> als Bilder, gestrippte Deckblaetter weniger.
Die sequenzielle Annahme "Textseite N = Bild N" ist dort falsch; massgeblich ist
<pb facs="#facs_N"> plus die <graphic url> der zugehoerigen <surface>.

Zwei Ebenen:
1. Synthetik (git-getrackt, CI): build_facs_map ueber konstruierten TEI-Bestand.
2. Realer Mirror (gitignore-unabhaengig, skippt wo nicht gespiegelt): der Sidecar
   docs/data/pages/{doc}/{doc}_facs.json der adjudizierten Faelle 1350 und 120.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.edition.generate_edition_data import (
    PAGES_DIR,
    build_facs_map,
    facs_anchors,
    write_facs_map,
)


def _tei(surfaces: str, pbs: str) -> str:
    """Minimaler TEI-Bestand: facsimile-Block plus body mit <pb>-Folge."""
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<TEI xmlns="http://www.tei-c.org/ns/1.0">\n'
        f"  <facsimile>\n{surfaces}  </facsimile>\n"
        f"  <text>\n    <body>\n{pbs}    </body>\n  </text>\n"
        "</TEI>\n"
    )


def _surfaces(doc_id: str, indices) -> str:
    return "".join(
        f'    <surface xml:id="facs_{i}" ulx="0" uly="0" lrx="9" lry="9">\n'
        f'      <graphic url="{doc_id}_p{i:03d}.png"/>\n'
        f"    </surface>\n"
        for i in indices
    )


def _pbs(anchors) -> str:
    out = []
    for a in anchors:
        out.append('      <pb n="[1]"/>\n' if a is None else f'      <pb facs="#facs_{a}" n="[1]"/>\n')
    return "".join(out)


def test_double_page_spread_maps_two_text_pages_to_one_scan():
    """Doc-1350-Muster: 6 <pb> auf 4 Scans (1,2,2,3,3,4)."""
    tei = _tei(_surfaces("1350", [1, 2, 3, 4]), _pbs([1, 2, 2, 3, 3, 4]))
    assert build_facs_map(tei) == {
        1: "1350_p001.png",
        2: "1350_p002.png",
        3: "1350_p002.png",
        4: "1350_p003.png",
        5: "1350_p003.png",
        6: "1350_p004.png",
    }


def test_stripped_cover_sheet_shifts_the_whole_document():
    """Erster Anker facs_2: Textseite 1 zeigt Scan 2, nicht das Deckblatt."""
    tei = _tei(_surfaces("2310", [2, 3]), _pbs([2, 3]))
    assert build_facs_map(tei) == {1: "2310_p002.png", 2: "2310_p003.png"}


def test_sequential_document_maps_identically():
    tei = _tei(_surfaces("777", [1, 2, 3]), _pbs([1, 2, 3]))
    assert build_facs_map(tei) == {1: "777_p001.png", 2: "777_p002.png", 3: "777_p003.png"}


def test_page_without_anchor_is_left_to_the_sequential_fallback():
    tei = _tei(_surfaces("777", [1, 2]), _pbs([1, None]))
    assert build_facs_map(tei) == {1: "777_p001.png"}
    assert facs_anchors(tei) == [1, None]


def test_anchor_without_surface_is_left_to_the_sequential_fallback():
    """Doc-130-Muster: ein <pb> verweist auf eine Surface, die es nicht gibt."""
    tei = _tei(_surfaces("130", [2, 3]), _pbs([2, 21, 3]))
    assert build_facs_map(tei) == {1: "130_p002.png", 3: "130_p003.png"}


def test_document_without_pb_yields_no_map():
    assert build_facs_map(_tei(_surfaces("777", [1]), "")) == {}


def test_write_facs_map_payload_and_removal(tmp_path: Path):
    """Sidecar-Vertrag: {doc_id, facs_image: {Textseite: Bilddatei}}, Stringschluessel."""
    tei = _tei(_surfaces("1350", [1, 2]), _pbs([1, 2, 2]))
    assert write_facs_map(tmp_path, "1350", tei) is True
    payload = json.loads((tmp_path / "1350_facs.json").read_text(encoding="utf-8"))
    assert payload == {
        "doc_id": "1350",
        "facs_image": {"1": "1350_p001.png", "2": "1350_p002.png", "3": "1350_p002.png"},
    }
    # Ein Dokument ohne aufloesbare Anker behaelt keinen veralteten Sidecar
    assert write_facs_map(tmp_path, "1350", _tei("", _pbs([None]))) is False
    assert not (tmp_path / "1350_facs.json").exists()


def test_write_facs_map_is_deterministic(tmp_path: Path):
    tei = _tei(_surfaces("120", [1, 2, 3]), _pbs([1, 2, 3, 3]))
    write_facs_map(tmp_path, "120", tei)
    first = (tmp_path / "120_facs.json").read_bytes()
    write_facs_map(tmp_path, "120", tei)
    assert (tmp_path / "120_facs.json").read_bytes() == first


# --- realer Mirror: die beiden faksimile-adjudizierten Faelle -------------------

_MIRROR_CASES = {
    "1350": {"5": "1350_p003.png", "6": "1350_p004.png"},
    "120": {"4": "120_p003.png", "11": "120_p010.png"},
}


@pytest.mark.parametrize("doc_id", sorted(_MIRROR_CASES))
def test_mirror_sidecar_matches_the_adjudicated_pages(doc_id: str):
    sidecar = PAGES_DIR / doc_id / f"{doc_id}_facs.json"
    if not sidecar.exists():
        pytest.skip(f"Mirror fuer {doc_id} nicht gespiegelt")
    payload = json.loads(sidecar.read_text(encoding="utf-8"))
    assert payload["doc_id"] == doc_id
    for page, image in _MIRROR_CASES[doc_id].items():
        assert payload["facs_image"][page] == image
