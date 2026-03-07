"""Shared fixtures fuer zbz-ocr-tei Tests."""

import json
import pytest
from pathlib import Path


@pytest.fixture
def project_root():
    """Projekt-Root-Verzeichnis."""
    return Path(__file__).parent.parent


@pytest.fixture
def data_dir(project_root):
    """data/ Verzeichnis."""
    return project_root / "data"


@pytest.fixture
def tmp_json(tmp_path):
    """Erzeugt eine temporaere JSON-Datei."""
    def _create(data, name="test.json"):
        path = tmp_path / name
        path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        return path
    return _create
