"""Shared builders and markers for the test suite.

The builders here replace fixture code that stood in near-identical copies across the
test files: the TEI skeleton, the delivery-shaped teiHeader, the layout bbox and the
entity lexicon fixtures. Every builder stays a plain function so the test modules can
call it at import time (parametrization and module-level constants need that); only
`pytest_configure` is pytest machinery.

Two markers make the clone blind spot visible: `requires_corpus` for tests that run over
the gitignored delivered corpus under `output/`, `requires_mirror` for tests that read
tracked repository data (the `docs/data` mirror, the curated entity snapshots under
`data/entities`) instead of synthetic fixtures.
"""

from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
TEI_NS = "http://www.tei-c.org/ns/1.0"

# The delivered corpus, shared by the three suites that parametrize over it. A module
# constant rather than a fixture, because parametrization is resolved at collection time
# and a fixture value is not available then.
FINAL_DIR = REPO / "output" / "tei_final"
FINAL_DOCS = sorted(FINAL_DIR.glob("*_final.xml")) if FINAL_DIR.exists() else []
FINAL_IDS = [p.name for p in FINAL_DOCS]

XML_DECL = '<?xml version="1.0" encoding="UTF-8"?>\n'


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "requires_corpus: needs the gitignored delivered corpus under output/ "
        "(skips on a fresh clone)",
    )
    config.addinivalue_line(
        "markers",
        "requires_mirror: reads tracked repository data (docs/data mirror, "
        "data/entities snapshots) rather than synthetic fixtures",
    )


# --- TEI skeleton -----------------------------------------------------------


def tei_doc(body_inner: str = "", *, header: str = "", facsimile: str = "",
            root_attrs: str = "", text_attrs: str = "", xml_decl: bool = False) -> str:
    """A TEI document string around `body_inner`.

    `header` and `facsimile` are raw fragments (empty means the element is absent),
    `root_attrs`/`text_attrs` are attribute strings for <TEI>/<text>.
    """
    decl = XML_DECL if xml_decl else ""
    attrs = f" {root_attrs.strip()}" if root_attrs else ""
    t_attrs = f" {text_attrs.strip()}" if text_attrs else ""
    facs = f"<facsimile>{facsimile}</facsimile>" if facsimile else ""
    return (
        f'{decl}<TEI xmlns="{TEI_NS}"{attrs}>{header}{facs}'
        f"<text{t_attrs}><body>{body_inner}</body></text></TEI>"
    )


def tei_header(title: str = "Fixture", extra: str = "") -> str:
    """Minimal teiHeader carrying a title; `extra` appends a sibling of <fileDesc>."""
    return (
        "<teiHeader><fileDesc><titleStmt>"
        f"<title>{title}</title>"
        f"</titleStmt></fileDesc>{extra}</teiHeader>"
    )


# The delivery contract of a produced teiHeader (E68/E69): docID as a real <idno>,
# <biblStruct> with analytic+monogr+imprint, <langUsage>, <revisionDesc>. Two changes,
# because the status projection writes the second shape.
DELIVERY_REVISION = (
    '<change when="2026-03-15" who="pipeline">TEI generated</change>'
    '<change status="unverifiziert" n="ocr-summary">OCR-Strom: unverifiziert</change>'
)


def delivery_header(revision: str = DELIVERY_REVISION) -> str:
    """teiHeader in the shape of a delivered TEI; schema-valid against zbz_hersch.rng."""
    return (
        "<teiHeader><fileDesc>"
        '<titleStmt><title type="main">Test</title><author>Hersch, Jeanne</author></titleStmt>'
        "<publicationStmt><publisher>ZBZ / DHCraft</publisher>"
        '<idno type="docID">9999</idno></publicationStmt>'
        '<sourceDesc><biblStruct type="journalArticle">'
        "<analytic><title>Test</title><author>Hersch, Jeanne</author></analytic>"
        "<monogr><title>Zeitschrift</title><imprint><date>1975</date></imprint></monogr>"
        "</biblStruct></sourceDesc>"
        "</fileDesc>"
        '<profileDesc><langUsage><language ident="fra"/></langUsage></profileDesc>'
        f"<revisionDesc>{revision}</revisionDesc>"
        "</teiHeader>"
    )


def delivery_doc(body_inner: str, *, revision: str = DELIVERY_REVISION,
                 text_attrs: str = "") -> str:
    """A delivery-shaped, schema-valid TEI document around `body_inner`."""
    return tei_doc(body_inner, header=delivery_header(revision),
                   root_attrs='type="naegeli"', text_attrs=text_attrs, xml_decl=True)


# --- layout ------------------------------------------------------------------


def bbox(x: float, y: float, w: float = 20.0, h: float = 8.0) -> dict:
    """A layout region bbox in page percent, as the reading-order helpers expect it."""
    return {"x_pct": x, "y_pct": y, "w_pct": w, "h_pct": h}


# --- entity lexicon fixtures --------------------------------------------------


def person_record(gid: str, name: str) -> dict:
    return {"GND_id": gid, "name": name, "listBibl": [], "editor_reviewed": False}


def org_record(gid: str, org_name: str) -> dict:
    return {"GND_id": gid, "orgName": org_name, "listBibl": [], "editor_reviewed": False}


def work_record(gid: str, title: str, author: str = "") -> dict:
    return {"GND_id": gid, "title": title, "author_gnd_id": author, "listBibl": []}


def gnd_cache_entry(preferred: str | None = None,
                    variants: tuple[str, ...] = ()) -> dict:
    return {
        "http_status": 200,
        "preferred_name": preferred,
        "variant_names": list(variants),
        "types": ["Person"],
        "date_of_birth": None,
        "date_of_death": None,
        "wikidata": None,
    }


def build_lexicon_dir(tmp_path, persons=(), orgs=(), works=(), cache=None, legacy=None,
                      review=None, policy=None):
    """Write the mini fixtures to tmp_path and build the lexicon from them."""
    from scripts.entity import entity_matcher as em

    entities_path = tmp_path / "all_entities.json"
    entities_path.write_text(
        json.dumps(
            {"persons": list(persons), "organisations": list(orgs), "works": list(works)},
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    cache_path = tmp_path / "gnd_cache.json"
    if cache is not None:
        cache_path.write_text(
            json.dumps(
                {"retrieved": "2026-08-12", "source_pattern": "test", "entries": cache},
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
    legacy_path = None
    if legacy is not None:
        legacy_path = tmp_path / "gnd_entities.json"
        legacy_path.write_text(json.dumps(legacy, ensure_ascii=False), encoding="utf-8")
    review_path = None
    if review is not None:
        review_path = tmp_path / "variant_review.json"
        review_path.write_text(json.dumps(review, ensure_ascii=False), encoding="utf-8")
    return em.build_lexicon(entities_path, cache_path, legacy_path,
                            review_path=review_path, policy_path=policy)
