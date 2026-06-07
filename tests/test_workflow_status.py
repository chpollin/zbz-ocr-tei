"""Workflow-Status-Vertrag (E77): drei Stufen + Migration alter Werte.

Sichert ab, dass der Kollaps von vier auf drei Stufen (unverifiziert | in_arbeit |
verifiziert) konsistent bleibt und alte Manifeste (offen/bearbeitet/fertig) korrekt
auf die neuen Werte gemappt werden, ohne Status oder History zu verlieren.
"""

from scripts.edition import page_manifest as pm


def test_valid_status_has_three_stages():
    assert pm.VALID_STATUS == ("unverifiziert", "in_arbeit", "verifiziert")
    assert pm.DEFAULT_STATUS == "unverifiziert"


def test_status_migration_maps_old_to_new():
    assert pm.STATUS_MIGRATION["offen"] == "unverifiziert"
    assert pm.STATUS_MIGRATION["bearbeitet"] == "in_arbeit"
    assert pm.STATUS_MIGRATION["fertig"] == "verifiziert"


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
