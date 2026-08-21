"""Workflow-Status-Vertrag (E77): drei Stufen + Migration alter Werte.

Sichert ab, dass der Kollaps von vier auf drei Stufen (unverifiziert | in_arbeit |
verifiziert) konsistent bleibt und alte Manifeste (offen/bearbeitet/fertig) korrekt
auf die neuen Werte gemappt werden, ohne Status oder History zu verlieren.
"""

import re
from pathlib import Path

from scripts.edition import page_manifest as pm
from scripts.tei.tei_status_marker import STATUS_LABEL as MARKER_LABEL

JS_DIR = Path(__file__).resolve().parent.parent / "docs" / "assets" / "js"

_OBJECT_RE = r"const %s\s*=\s*\{(.*?)\}"
_ENTRY_RE = re.compile(r"(\w+)\s*:\s*'([^']*)'")


def _js_object(source: str, name: str) -> dict[str, str] | None:
    """The literal `const <name> = { key: 'value', ... }` of a viewer module."""
    m = re.search(_OBJECT_RE % name, source, re.S)
    return dict(_ENTRY_RE.findall(m.group(1))) if m else None


def test_status_tokens_agree_across_manifest_marker_and_viewer():
    """The three status tokens are one vocabulary in Python and in the viewer.

    page_manifest owns them, tei_status_marker projects them into <revisionDesc>, and
    the viewer JavaScript cycles and labels them. A token renamed in one layer without
    the others breaks the manifest round trip, so the agreement is the contract.
    """
    js = {f.name: f.read_text(encoding="utf-8") for f in sorted(JS_DIR.glob("*.js"))}

    cycle = re.search(r"const STATUS_CYCLE\s*=\s*\[(.*?)\]", js["viewer-state.js"], re.S)
    assert cycle, "viewer-state.js carries no STATUS_CYCLE"
    assert tuple(re.findall(r"'([^']+)'", cycle.group(1))) == pm.VALID_STATUS
    assert pm.VALID_STATUS[0] == pm.DEFAULT_STATUS  # the cycle starts at the default

    labelled = {name: _js_object(src, "STATUS_LABEL") for name, src in js.items()}
    assert any(labelled.values()), "no viewer module labels the status values"
    for name, labels in labelled.items():
        if labels is not None:
            assert set(pm.VALID_STATUS) <= set(labels), name

    legacy = {name: _js_object(src, "STATUS_LEGACY") for name, src in js.items()}
    assert any(legacy.values()), "no viewer module maps the legacy status values"
    for name, mapping in legacy.items():
        if mapping is not None:
            assert mapping == pm.STATUS_MIGRATION, name

    # The marker knows the current tokens plus the legacy ones it may still meet, and
    # projects a legacy value under the label of the value it migrates to.
    assert set(MARKER_LABEL) - set(pm.STATUS_MIGRATION) == set(pm.VALID_STATUS)
    for old, new in pm.STATUS_MIGRATION.items():
        if old in MARKER_LABEL:
            assert MARKER_LABEL[old] == MARKER_LABEL[new]


def test_migrate_streams_collapses_legacy_status():
    existing = {
        "ocr":    {"engine": "mistral", "status": "fertig", "history": []},
        "layout": {"engines": ["docling", "gemini"], "status": "bearbeitet", "history": []},
        "tei":    {"source": "final", "status": "offen", "history": []},
    }
    out = pm._migrate_streams(existing)
    assert out["ocr"]["status"] == "verifiziert"
    assert out["layout"]["status"] == "in_arbeit"
    assert out["tei"]["status"] == "unverifiziert"


def test_migrate_streams_preserves_and_migrates_history():
    existing = {
        "ocr": {
            "engine": "mistral",
            "status": "fertig",
            "history": [
                {"at": "2026-06-01T10:00:00Z", "by": "CP", "from": "unverifiziert", "to": "in_arbeit", "note": None},
                {"at": "2026-06-02T10:00:00Z", "by": "CP", "from": "bearbeitet", "to": "fertig", "note": None},
            ],
        },
        "layout": {"engines": ["docling", "gemini"], "status": "unverifiziert", "history": []},
        "tei":    {"source": "final", "status": "unverifiziert", "history": []},
    }
    out = pm._migrate_streams(existing)
    hist = out["ocr"]["history"]
    assert len(hist) == 2  # nichts verloren
    # from/to-Felder ebenfalls migriert
    assert hist[1]["from"] == "in_arbeit"   # war "bearbeitet"
    assert hist[1]["to"] == "verifiziert"   # war "fertig"


def test_unknown_status_falls_back_to_default():
    existing = {
        "ocr":    {"engine": "mistral", "status": "voellig_kaputt", "history": []},
        "layout": {"engines": ["docling", "gemini"], "status": "unverifiziert", "history": []},
        "tei":    {"source": "final", "status": "verifiziert", "history": []},
    }
    out = pm._migrate_streams(existing)
    assert out["ocr"]["status"] == pm.DEFAULT_STATUS
    assert out["tei"]["status"] == "verifiziert"  # neuer Wert bleibt gueltig
