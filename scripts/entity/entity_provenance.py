"""Provenance vocabulary for inline GND entity annotations.

The entity layer records responsibility through ``@resp`` and the producing matcher rule
through ``@source``. It deliberately emits no ``@cert`` because matcher output, agentic
review, LLM review and editorial verification are activities with different provenance,
not points on one certainty scale. The responsibility declarations stay compatible with
the project RelaxNG schema, which has ``respStmt`` but no ``appInfo`` or ``application``.

The deterministic matcher always remains part of the provenance because every candidate
starts in its closed-world candidate set. Optional candidate fields add later activities:

``agent_reviewed``
    A facsimile-based evaluation wave reviewed an existing matcher assertion.
``agent_annotation_run``
    An AI agent selected or promoted the annotation in a recorded harness run.
``llm_judge_run``
    A separate LLM run reviewed the agentic annotation.
``editor_verification_ref``
    A person-bound editorial record verified the identification.

The detailed run metadata belongs in the machine-readable provenance artifact. The TEI
keeps compact pointers and a readable role declaration in its header.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from xml.sax.saxutils import escape

MATCHER_RESP_ID = "resp-entity-matcher"
AGENT_REVIEW_RESP_ID = "resp-entity-agent-review"
AGENT_ANNOTATION_RESP_ID = "resp-entity-agent-annotation"
LLM_JUDGE_RESP_ID = "resp-entity-llm-judge"
EDITOR_VERIFICATION_RESP_ID = "resp-entity-editor-verification"

RESP_ORG_DHCRAFT = "DHCraft"
RESP_ORG_ZBZ = "Zentralbibliothek Zürich"

RULE_MODULES = ("entity_matcher.py", "entity_lexicon.py", "running_heads.py")
_TITLESTMT_CLOSE_RE = re.compile(r"([ \t]*)</titleStmt>")


@dataclass(frozen=True)
class Responsibility:
    """One role declaration inserted into the TEI title statement."""

    xml_id: str
    text: str
    org_name: str


@lru_cache(maxsize=1)
def matcher_fingerprint(module_dir: Path | None = None) -> str:
    """Return a short digest over the rule-bearing matcher modules."""
    module_dir = module_dir or Path(__file__).parent
    digest = hashlib.sha256()
    for name in RULE_MODULES:
        digest.update((module_dir / name).read_bytes())
    return digest.hexdigest()[:12]


def candidate_responsibility_ids(candidate: dict) -> tuple[str, ...]:
    """Return the ordered activities that materially contributed to one mark."""
    ids = [MATCHER_RESP_ID]
    if candidate.get("agent_reviewed"):
        ids.append(AGENT_REVIEW_RESP_ID)
    if candidate.get("agent_annotation_run"):
        ids.append(AGENT_ANNOTATION_RESP_ID)
    if candidate.get("llm_judge_run"):
        ids.append(LLM_JUDGE_RESP_ID)
    if candidate.get("editor_verification_ref"):
        ids.append(EDITOR_VERIFICATION_RESP_ID)
    return tuple(ids)


def mark_attributes(candidate: dict) -> dict[str, str]:
    """Build the schema-valid attributes of one inline entity mark."""
    attributes = {"ref": f"GND:{candidate['gid']}"}
    if candidate.get("rule"):
        attributes["source"] = candidate["rule"]
    attributes["resp"] = " ".join(
        f"#{responsibility_id}"
        for responsibility_id in candidate_responsibility_ids(candidate)
    )
    return attributes


def _record_values(candidates: list[dict], field: str) -> list[str]:
    """Return stable distinct provenance record labels carried by candidates."""
    return sorted({str(candidate[field]).strip() for candidate in candidates
                   if str(candidate.get(field) or "").strip()})


def resp_statements(
    candidates: list[dict],
    agent_review_snapshot: str | None,
) -> list[Responsibility]:
    """Declare exactly the responsibilities referenced by the document's marks."""
    tier1 = [candidate for candidate in candidates if candidate.get("tier") == 1]
    if not tier1:
        return []

    statements = [Responsibility(
        MATCHER_RESP_ID,
        "Automatic entity matching, deterministic and closed-world "
        f"(scripts/entity/entity_matcher.py, rule set {matcher_fingerprint()})",
        RESP_ORG_DHCRAFT,
    )]
    if any(candidate.get("agent_reviewed") for candidate in tier1):
        snapshot = agent_review_snapshot or "unnamed"
        statements.append(Responsibility(
            AGENT_REVIEW_RESP_ID,
            "Agentic facsimile review of the entity evaluation sample, "
            f"wave {snapshot}; machine review without editorial verification",
            RESP_ORG_DHCRAFT,
        ))

    annotation_runs = _record_values(tier1, "agent_annotation_run")
    if annotation_runs:
        statements.append(Responsibility(
            AGENT_ANNOTATION_RESP_ID,
            "Context-aware entity annotation by an AI agent, "
            f"run {', '.join(annotation_runs)}",
            RESP_ORG_DHCRAFT,
        ))

    judge_runs = _record_values(tier1, "llm_judge_run")
    if judge_runs:
        statements.append(Responsibility(
            LLM_JUDGE_RESP_ID,
            "Independent LLM review of an agentic entity annotation, "
            f"run {', '.join(judge_runs)}",
            RESP_ORG_DHCRAFT,
        ))

    editor_records = _record_values(tier1, "editor_verification_ref")
    if editor_records:
        statements.append(Responsibility(
            EDITOR_VERIFICATION_RESP_ID,
            "Entity identification verified by an editor, "
            f"record {', '.join(editor_records)}",
            RESP_ORG_ZBZ,
        ))
    return statements


def insert_resp_stmts(xml_string: str, statements: list[Responsibility]) -> str:
    """Insert responsibility declarations into ``titleStmt`` idempotently."""
    match = _TITLESTMT_CLOSE_RE.search(xml_string)
    if match is None:
        return xml_string
    pending = [statement for statement in statements
               if f'<respStmt xml:id="{statement.xml_id}">' not in xml_string]
    if not pending:
        return xml_string
    at = match.start()
    block = xml_string[:at].endswith("\n")
    indent = match.group(1) + "  " if block else ""
    rendered = "".join(
        f'{indent}<respStmt xml:id="{statement.xml_id}">'
        f"<resp>{escape(statement.text)}</resp>"
        f"<orgName>{escape(statement.org_name)}</orgName></respStmt>"
        + ("\n" if block else "")
        for statement in pending
    )
    return xml_string[:at] + rendered + xml_string[at:]
