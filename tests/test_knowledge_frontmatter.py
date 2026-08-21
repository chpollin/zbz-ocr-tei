"""Gate for the knowledge base: ten documents, one frontmatter contract, resolvable links.

Pins the Promptotyping convention checklist (knowledge/index.md, section Convention)
so a document added, renamed or left with a dangling pointer fails in CI instead of
surfacing in the next audit.
"""

from __future__ import annotations

import re
from datetime import date
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
KNOWLEDGE = ROOT / "knowledge"

# The ten carriers of the knowledge base; the client report lives under docs/.
CARRIERS = {
    "index.md",
    "project.md",
    "specification.md",
    "tei-mapping.md",
    "pipeline.md",
    "workflow.md",
    "methodology.md",
    "verification.md",
    "decisions.md",
    "journal.md",
}

CORE_KEYS = {"title", "project", "method", "status", "language", "version", "created", "updated", "authors", "related"}
FORBIDDEN_KEYS = {"type", "tags", "dependencies", "source"}
STATUS_VOCAB = {"idea", "draft", "stub", "complete", "reviewed", "archived", "active", "snapshot"}
TEMPLATE_URL_PREFIX = "https://dhcraft.org/Promptotyping/promptotyping-document/"
LINK_RE = re.compile(r"\]\(([^)\s]+)\)")
FENCE_RE = re.compile(r"^```.*?^```", re.M | re.S)


def _frontmatter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    assert text.startswith("---\n"), f"{path.name}: no frontmatter"
    end = text.index("\n---", 4)
    data = yaml.safe_load(text[4:end])
    assert isinstance(data, dict), f"{path.name}: frontmatter is not a mapping"
    return data


def _docs() -> list[Path]:
    return sorted(KNOWLEDGE.glob("*.md"))


def test_exactly_the_ten_carriers_exist():
    names = {p.name for p in _docs()}
    assert names == CARRIERS, f"unexpected set: extra={names - CARRIERS}, missing={CARRIERS - names}"


@pytest.mark.parametrize("path", _docs(), ids=lambda p: p.name)
def test_core_frontmatter(path: Path):
    fm = _frontmatter(path)
    missing = CORE_KEYS - fm.keys()
    assert not missing, f"{path.name}: missing {sorted(missing)}"
    forbidden = FORBIDDEN_KEYS & fm.keys()
    assert not forbidden, f"{path.name}: forbidden keys {sorted(forbidden)}"
    assert fm["project"].get("name") == "zbz-ocr-tei"
    assert str(fm["project"].get("repository", "")).startswith("https://github.com/")
    assert fm["method"].get("name") == "Promptotyping"
    assert fm["status"] in STATUS_VOCAB, f"{path.name}: status {fm['status']!r}"
    assert fm["language"] in {"en", "de"}
    assert isinstance(fm["created"], date) and isinstance(fm["updated"], date)
    assert fm["created"] <= fm["updated"]
    assert isinstance(fm["authors"], list) and fm["authors"]
    assert isinstance(fm["related"], list) and fm["related"]
    for key, value in fm.items():
        assert value not in (None, "", [], {}), f"{path.name}: empty field {key}"


def test_schema_version_is_repo_wide():
    versions = {p.name: str(_frontmatter(p)["version"]) for p in _docs()}
    assert len(set(versions.values())) == 1, versions


@pytest.mark.parametrize("path", _docs(), ids=lambda p: p.name)
def test_template_block_shape(path: Path):
    fm = _frontmatter(path)
    template = fm.get("template")
    if template is None:
        return
    assert {"name", "version", "url"} <= template.keys(), f"{path.name}: template keys {sorted(template)}"
    assert str(template["url"]).startswith(TEMPLATE_URL_PREFIX), f"{path.name}: {template['url']}"
    absorbed = fm.get("absorbed")
    if absorbed is not None:
        assert isinstance(absorbed, list) and all(isinstance(a, str) for a in absorbed)


@pytest.mark.parametrize("path", _docs(), ids=lambda p: p.name)
def test_related_entries_name_existing_documents(path: Path):
    for name in _frontmatter(path)["related"]:
        assert (KNOWLEDGE / f"{name}.md").exists(), f"{path.name}: related {name}"


@pytest.mark.parametrize("path", _docs(), ids=lambda p: p.name)
def test_relative_links_resolve(path: Path):
    body = FENCE_RE.sub("", path.read_text(encoding="utf-8"))
    broken = []
    for target in LINK_RE.findall(body):
        if target.startswith(("http://", "https://", "mailto:", "#")):
            continue
        rel = target.split("#", 1)[0]
        if not rel:
            continue
        if not (path.parent / rel).exists():
            broken.append(target)
    assert not broken, f"{path.name}: {broken}"


def test_no_horizontal_rules_outside_frontmatter():
    offenders = {}
    for path in _docs():
        lines = path.read_text(encoding="utf-8").splitlines()
        fences = [i for i, line in enumerate(lines) if line.strip() == "---"]
        # The first two fences close the frontmatter; any later one is a horizontal rule.
        extra = [i + 1 for i in fences[2:]]
        if extra:
            offenders[path.name] = extra
    assert not offenders, offenders
