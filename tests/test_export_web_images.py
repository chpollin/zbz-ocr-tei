"""Web image export: PNG page images -> JPEG mirror with identical names, idempotent."""

from pathlib import Path

import pytest
from PIL import Image

from scripts.edition.export_web_images import export_doc, jpeg_name


def _make_doc(root: Path, doc_id: str, pages: int) -> Path:
    d = root / doc_id
    d.mkdir(parents=True)
    for i in range(1, pages + 1):
        Image.new("RGB", (40, 60), (200, 180, 150)).save(d / f"{doc_id}_p{i:03d}.png")
    return d


def test_jpeg_name_keeps_stem():
    assert jpeg_name("2310_p007.png") == "2310_p007.jpg"


def test_export_writes_jpeg_per_page(tmp_path: Path):
    src = tmp_path / "images"
    out = tmp_path / "web"
    _make_doc(src, "2310", 3)
    result = export_doc("2310", src, out, quality=80, force=False)
    assert result["written"] == 3 and result["skipped"] == 0
    files = sorted(p.name for p in (out / "2310").iterdir())
    assert files == ["2310_p001.jpg", "2310_p002.jpg", "2310_p003.jpg"]
    with Image.open(out / "2310" / "2310_p001.jpg") as im:
        assert im.format == "JPEG" and im.size == (40, 60)


def test_export_skips_existing_unless_forced(tmp_path: Path):
    src = tmp_path / "images"
    out = tmp_path / "web"
    _make_doc(src, "1000", 2)
    export_doc("1000", src, out, quality=80, force=False)
    again = export_doc("1000", src, out, quality=80, force=False)
    assert again["written"] == 0 and again["skipped"] == 2
    forced = export_doc("1000", src, out, quality=80, force=True)
    assert forced["written"] == 2


def test_export_missing_doc_raises(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        export_doc("9999", tmp_path / "images", tmp_path / "web", quality=80, force=False)
