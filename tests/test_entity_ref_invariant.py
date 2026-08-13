"""Closed-world gate for the entity mirror: no id outside the curated list.

The entity layer rests on the claim that a hallucinated GND id is impossible, because
every mark comes from matching against the curated list data/entities/all_entities.json.
So far that claim was a property of the generator, checked only where a test exercised
the generator itself. This module checks it on the shipped artifacts instead: every id
that reaches the viewer through the mirror under docs/data/pages/ is compared, as a raw
string, against the curated list.

Two surfaces carry ids into the mirror:

1. ``ref="GND:<id>"`` on the tier-1 wrappers in ``{doc}_entity_p{N}.xml``
2. ``gid`` and the ambiguity set ``alternatives`` on the tier-2 entries in
   ``{doc}_entity_worklist.json``, which the viewer popover resolves

The comparison is exact. A mismatch that is mere formatting (surrounding whitespace, a
differently cased prefix) breaks the lookup in the viewer just as an unknown id does, so
nothing is normalized before the membership test; a formatting drift has to surface as a
failure and be fixed at the generator.

The mirror is git-tracked, so the gate has teeth on a clone. It skips only where the
mirror was never generated.
"""

from __future__ import annotations

import json
import re
from collections.abc import Iterator
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
ENTITIES = REPO / "data" / "entities" / "all_entities.json"
PAGES_DIR = REPO / "docs" / "data" / "pages"

CATEGORIES = ("persons", "organisations", "works")
GND_PREFIX = "GND:"
# @ref carries the pointer; the mirror writes it with double quotes throughout
REF_RE = re.compile(r'\bref="([^"]*)"')
MAX_LISTED = 50


# --- extraction ----------------------------------------------------------


def _ref_values(xml: str) -> list[str]:
    """Every raw ``ref`` attribute value of a preview page."""
    return REF_RE.findall(xml)


def _pointers(value: str) -> list[str]:
    """TEI @ref may hold several whitespace-separated pointers."""
    return value.split()


def _iter_gids(node: object, path: str = "$") -> Iterator[tuple[str, object]]:
    """Yield (json path, value) for every id-bearing field of a worklist, deep.

    Values are yielded untyped: a gid that is not a string is a violation to report,
    not a case to filter away.
    """
    if isinstance(node, dict):
        for key, value in node.items():
            here = f"{path}.{key}"
            if key == "gid":
                yield here, value
            elif key == "alternatives" and isinstance(value, list):
                for index, alternative in enumerate(value):
                    yield f"{here}[{index}]", alternative
            yield from _iter_gids(value, here)
    elif isinstance(node, list):
        for index, item in enumerate(node):
            yield from _iter_gids(item, f"{path}[{index}]")


def _allowed_gids() -> set[str]:
    if not ENTITIES.exists():
        pytest.skip("curated entity list not available")
    data = json.loads(ENTITIES.read_text(encoding="utf-8"))
    return {
        entry["GND_id"]
        for category in CATEGORIES
        for entry in data.get(category, [])
        if isinstance(entry.get("GND_id"), str)
    }


def _preview_files() -> list[Path]:
    files = sorted(PAGES_DIR.glob("*/*_entity_p*.xml"))
    if not files:
        pytest.skip("entity preview mirror not generated")
    return files


def _worklist_files() -> list[Path]:
    files = sorted(PAGES_DIR.glob("*/*_entity_worklist.json"))
    if not files:
        pytest.skip("entity preview mirror not generated")
    return files


def _message(kind: str, violations: list[tuple[Path, object, str]]) -> str:
    head = f"{len(violations)} {kind} outside data/entities/all_entities.json:"
    lines = [
        f"  {path.relative_to(REPO).as_posix()}: {value!r} ({note})"
        for path, value, note in violations[:MAX_LISTED]
    ]
    if len(violations) > MAX_LISTED:
        lines.append(f"  ... and {len(violations) - MAX_LISTED} more")
    return "\n".join([head, *lines])


# --- extraction, on synthetic input --------------------------------------


def test_ref_values_read_every_wrapper_and_ignore_plain_markup():
    xml = (
        '<p><persName ref="GND:118557106">Karl Jaspers</persName> und die '
        '<orgName ref="GND:2023755-8">UNESCO</orgName>, dazu '
        '<bibl ref="GND:4558181-2">Psychopathologie</bibl>; '
        '<hi rendition="#i">kursiv</hi> traegt keinen Verweis.</p>'
    )
    assert _ref_values(xml) == ["GND:118557106", "GND:2023755-8", "GND:4558181-2"]


def test_pointers_split_a_multi_valued_ref():
    assert _pointers("GND:118557106 GND:118522175") == ["GND:118557106", "GND:118522175"]


def test_iter_gids_finds_gid_and_alternatives_at_any_depth():
    worklist = {
        "doc": "9999",
        "pages": {
            "1": [{"gid": "118557106", "alternatives": []}],
            "2": [{"gid": "117085391", "alternatives": ["117085391", "118557106"]}],
        },
    }
    found = dict(_iter_gids(worklist))
    assert found["$.pages.1[0].gid"] == "118557106"
    assert found["$.pages.2[0].alternatives[1]"] == "118557106"
    assert len(found) == 4


def test_iter_gids_keeps_a_non_string_gid_visible():
    assert list(_iter_gids({"gid": None})) == [("$.gid", None)]


# --- the curated list ----------------------------------------------------


def test_allowed_gids_cover_all_three_categories():
    """Pins the field name: a renamed GND_id would empty the set and flag everything."""
    data = json.loads(ENTITIES.read_text(encoding="utf-8")) if ENTITIES.exists() else {}
    if not data:
        pytest.skip("curated entity list not available")
    for category in CATEGORIES:
        ids = [e.get("GND_id") for e in data.get(category, [])]
        assert ids and all(isinstance(gid, str) and gid for gid in ids), category


# --- the mirror ----------------------------------------------------------


def test_preview_refs_point_into_the_curated_list():
    allowed = _allowed_gids()
    violations: list[tuple[Path, object, str]] = []
    seen: set[str] = set()

    for path in _preview_files():
        for value in _ref_values(path.read_text(encoding="utf-8")):
            for pointer in _pointers(value):
                if not pointer.startswith(GND_PREFIX):
                    violations.append((path, pointer, "no GND: prefix"))
                    continue
                gid = pointer[len(GND_PREFIX):]
                seen.add(gid)
                if gid not in allowed:
                    violations.append((path, gid, "unknown id"))

    assert seen, "no ref in the entity previews - the gate would prove nothing"
    assert not violations, _message("preview ref value(s)", violations)


def test_worklist_gids_point_into_the_curated_list():
    """Covers the tier-2 gid and every id of its alternatives set."""
    allowed = _allowed_gids()
    violations: list[tuple[Path, object, str]] = []
    seen: set[object] = set()

    for path in _worklist_files():
        worklist = json.loads(path.read_text(encoding="utf-8"))
        for location, gid in _iter_gids(worklist):
            seen.add(gid)
            if not isinstance(gid, str) or gid not in allowed:
                violations.append((path, gid, location))

    assert seen, "no gid in the entity worklists - the gate would prove nothing"
    assert not violations, _message("worklist gid value(s)", violations)


def test_overview_gids_point_into_the_curated_list():
    """Covers the entity section keys and every per-document gid of the overview."""
    overview_path = REPO / "docs" / "data" / "entity_overview.json"
    if not overview_path.exists():
        pytest.skip("entity overview mirror not generated")
    allowed = _allowed_gids()
    overview = json.loads(overview_path.read_text(encoding="utf-8"))
    violations: list[tuple[Path, object, str]] = []
    seen: set[object] = set()

    for gid in overview.get("entities", {}):
        seen.add(gid)
        if gid not in allowed:
            violations.append((overview_path, gid, f"$.entities.{gid}"))
    for doc_id, record in overview.get("documents", {}).items():
        for index, entity in enumerate(record.get("entities", [])):
            gid = entity.get("gid")
            seen.add(gid)
            if not isinstance(gid, str) or gid not in allowed:
                violations.append((overview_path, gid,
                                   f"$.documents.{doc_id}.entities[{index}]"))

    assert seen, "no gid in the entity overview - the gate would prove nothing"
    assert not violations, _message("overview gid value(s)", violations)
