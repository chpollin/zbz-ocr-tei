"""Direct unit tests for the project rules of scripts/tei/tei_validator.py.

Pins the semantics of ``_check_project_rules`` (errors R1-R7, warnings W1-W18) on
synthetic documents. The rules were previously exercised only through the corpus
parametrization over ``output/tei_final``, which is gitignored and therefore absent on a
fresh clone; these fixtures hold the same contract without any repo data.

Scope notes: W8-W10 do not exist in the rule catalog (the numbering skips them), and W19
(reading order, E99) is already covered by ``tests/test_tei_validator.py``. Each rule gets
one firing fixture and one silent counter-fixture that carries the same construct in its
correct form; a firing fixture may incidentally trigger other rules, so the assertions are
membership assertions on the rule under test.
"""

from __future__ import annotations

import pytest
from lxml import etree as _etree

from scripts.config import TEI_SCHEMA_PATH
from scripts.tei.tei_validator import _check_project_rules

_NS = 'xmlns="http://www.tei-c.org/ns/1.0"'

HEADER = (
    "<teiHeader><fileDesc>"
    '<titleStmt><title type="main">Titre</title><author>Hersch, Jeanne</author></titleStmt>'
    '<publicationStmt><publisher>ZBZ / DHCraft</publisher>'
    '<idno type="docID">9999</idno></publicationStmt>'
    '<sourceDesc><biblStruct type="journalArticle">'
    "<analytic><title>Titre</title><author>Hersch, Jeanne</author></analytic>"
    "<monogr><title/><imprint><date>1975</date></imprint></monogr>"
    "</biblStruct></sourceDesc>"
    "</fileDesc>"
    '<profileDesc><langUsage><language ident="fra"/></langUsage></profileDesc>'
    "</teiHeader>"
)

FACSIMILE = (
    '<facsimile><surface xml:id="facs_1" ulx="0" uly="0" lrx="1000" lry="1500">'
    '<graphic url="9999_p001.png"/>'
    "</surface></facsimile>"
)

# Long enough that the page stays above the W5 threshold of 50 characters.
PAGE_TEXT = "Un paragraphe assez long pour que la page ne compte pas comme vide."
BODY = (
    '<div type="text"><pb facs="#facs_1" n="1"/>'
    f'<p>{PAGE_TEXT}<lb n="N001"/>suite du paragraphe.</p>'
    "</div>"
)


def _doc(body: str = BODY, *, header: str = HEADER, facsimile: str = FACSIMILE,
         root_attrs: str = ' type="naegeli"', back: str = "") -> str:
    """A minimal document that is silent on every rule; the keywords break one thing."""
    return (f"<TEI {_NS}{root_attrs}>{header}{facsimile}"
            f"<text><body>{body}</body>{back}</text></TEI>")


def _rules(xml: str) -> list[str]:
    """All rule ids the validator reports for a document, errors and warnings together."""
    root = _etree.fromstring(xml.encode("utf-8"))
    errors, warnings = _check_project_rules(root)
    return [f["rule"] for f in errors] + [f["rule"] for f in warnings]


# (label, rule, firing document, silent counter-document)
RULE_FIXTURES = [
    (
        "R1-root-type",
        "R1",
        _doc(root_attrs=""),
        _doc(),
    ),
    (
        "R2-header-missing",
        "R2",
        _doc(header=""),
        _doc(),
    ),
    (
        "R3-body-missing",
        "R3",
        f"<TEI {_NS} type=\"naegeli\">{HEADER}{FACSIMILE}</TEI>",
        _doc(),
    ),
    (
        "R4-no-div",
        "R4",
        _doc(body=f'<pb facs="#facs_1" n="1"/><p>{PAGE_TEXT}</p>'),
        _doc(),
    ),
    (
        "R5-unknown-type",
        "R5",
        _doc(body=f'<div type="chapitre"><pb facs="#facs_1" n="1"/><p>{PAGE_TEXT}</p></div>'),
        _doc(body=f'<div type="text"><pb facs="#facs_1" n="1"/><p>{PAGE_TEXT}</p></div>'),
    ),
    (
        "R5-no-type-no-n",
        "R5",
        _doc(body=f'<div><pb facs="#facs_1" n="1"/><p>{PAGE_TEXT}</p></div>'),
        _doc(body=f'<div n="1"><pb facs="#facs_1" n="1"/><p>{PAGE_TEXT}</p></div>'),
    ),
    (
        "R6-note-without-place",
        "R6",
        _doc(body=f'<div type="text"><pb facs="#facs_1" n="1"/><p>{PAGE_TEXT}</p>'
                  '<note n="1" xml:id="fn1-1">Une note.</note></div>'),
        _doc(body=f'<div type="text"><pb facs="#facs_1" n="1"/><p>{PAGE_TEXT}</p>'
                  '<note place="foot" n="1" xml:id="fn1-1">Une note.</note></div>'),
    ),
    (
        "R7-figure-in-p",
        "R7",
        _doc(body=f'<div type="text"><pb facs="#facs_1" n="1"/>'
                  f'<p>{PAGE_TEXT}<figure xml:id="fig1"><head>Legende</head></figure></p></div>'),
        _doc(body=f'<div type="text"><pb facs="#facs_1" n="1"/><p>{PAGE_TEXT}</p>'
                  '<figure xml:id="fig1"><head>Legende</head></figure></div>'),
    ),
    (
        "W1-undetermined-language",
        "W1",
        _doc(header=HEADER.replace('ident="fra"', 'ident="und"')),
        _doc(),
    ),
    (
        "W2-empty-title",
        "W2",
        _doc(header=HEADER.replace('<title type="main">Titre</title>', '<title type="main"/>')),
        _doc(),
    ),
    (
        "W3-surface-pb-mismatch",
        "W3",
        _doc(body=f'<div type="text"><pb facs="#facs_1" n="1"/><p>{PAGE_TEXT}</p>'
                  f'<pb facs="#facs_2" n="2"/><p>{PAGE_TEXT}</p></div>'),
        _doc(),
    ),
    (
        "W4-empty-div",
        "W4",
        _doc(body=f'<div type="text"><pb facs="#facs_1" n="1"/><p>{PAGE_TEXT}</p></div>'
                  '<div type="bibliography"></div>'),
        _doc(),
    ),
    (
        "W5-thin-page",
        "W5",
        _doc(body='<div type="text"><pb facs="#facs_1" n="1"/><p>Bref.<lb n="N001"/></p></div>'),
        _doc(),
    ),
    (
        "W6-no-line-breaks",
        "W6",
        _doc(body=f'<div type="text"><pb facs="#facs_1" n="1"/><p>{PAGE_TEXT}</p></div>'),
        _doc(),
    ),
    (
        "W7-graphic-without-url",
        "W7",
        _doc(facsimile=FACSIMILE.replace('url="9999_p001.png"', 'url="unknown"')),
        _doc(),
    ),
    (
        "W11-repeated-top-level-n",
        "W11",
        _doc(body='<div n="1"><pb facs="#facs_1" n="1"/><p>' + PAGE_TEXT + "</p></div>"
                  + '<div n="1"><p>a</p></div>' * 3),
        _doc(body='<div n="1"><pb facs="#facs_1" n="1"/><p>' + PAGE_TEXT + "</p></div>"
                  + "".join(f'<div n="{i}"><p>a</p></div>' for i in (2, 3, 4))),
    ),
    (
        "W12-footnote-without-n",
        "W12",
        _doc(body=f'<div type="text"><pb facs="#facs_1" n="1"/><p>{PAGE_TEXT}</p>'
                  '<note place="foot" xml:id="fn1-1">Une note.</note></div>'),
        _doc(body=f'<div type="text"><pb facs="#facs_1" n="1"/><p>{PAGE_TEXT}</p>'
                  '<note place="foot" n="1" xml:id="fn1-1">Une note.</note></div>'),
    ),
    (
        "W13-footnote-id-pattern",
        "W13",
        _doc(body=f'<div type="text"><pb facs="#facs_1" n="1"/><p>{PAGE_TEXT}</p>'
                  '<note place="foot" n="1" xml:id="note-eins">Une note.</note></div>'),
        _doc(body=f'<div type="text"><pb facs="#facs_1" n="1"/><p>{PAGE_TEXT}</p>'
                  '<note place="foot" n="1" xml:id="fn1-1">Une note.</note></div>'),
    ),
    (
        "W14-back-div-type",
        "W14",
        _doc(back='<back><div type="review"><p>Anhang.</p></div></back>'),
        _doc(back='<back><div type="translation"><p>Anhang.</p></div></back>'),
    ),
    (
        "W15-div-type-and-n",
        "W15",
        _doc(body=f'<div type="review" n="1"><pb facs="#facs_1" n="1"/><p>{PAGE_TEXT}</p></div>'),
        _doc(body=f'<div type="review"><pb facs="#facs_1" n="1"/><p>{PAGE_TEXT}</p></div>'),
    ),
    (
        "W16-figure-without-id",
        "W16",
        _doc(body=f'<div type="text"><pb facs="#facs_1" n="1"/><p>{PAGE_TEXT}</p>'
                  "<figure><head>Legende</head></figure></div>"),
        _doc(body=f'<div type="text"><pb facs="#facs_1" n="1"/><p>{PAGE_TEXT}</p>'
                  '<figure xml:id="fig1"><head>Legende</head></figure></div>'),
    ),
    (
        "W17-empty-speaker",
        "W17",
        _doc(body='<div type="interview"><pb facs="#facs_1" n="1"/>'
                  f"<sp><speaker/><p>{PAGE_TEXT}</p></sp></div>"),
        _doc(body='<div type="interview"><pb facs="#facs_1" n="1"/>'
                  f"<sp><speaker>Hersch</speaker><p>{PAGE_TEXT}</p></sp></div>"),
    ),
    (
        "W18-foreign-lang-not-normalized",
        "W18",
        _doc(body=f'<div type="text"><pb facs="#facs_1" n="1"/>'
                  f'<p>{PAGE_TEXT} <foreign xml:lang="fr">liberte</foreign></p></div>'),
        _doc(body=f'<div type="text"><pb facs="#facs_1" n="1"/>'
                  f'<p>{PAGE_TEXT} <foreign xml:lang="fra">liberte</foreign></p></div>'),
    ),
]

_IDS = [label for label, _, _, _ in RULE_FIXTURES]


@pytest.mark.parametrize("rule,firing", [(r, f) for _, r, f, _ in RULE_FIXTURES], ids=_IDS)
def test_each_rule_fires(rule, firing):
    """Every rule fires on the document that breaks exactly its constraint."""
    assert rule in _rules(firing), f"{rule} should fire"


@pytest.mark.parametrize("rule,counter", [(r, c) for _, r, _, c in RULE_FIXTURES], ids=_IDS)
def test_each_rule_silent_on_counter_fixture(rule, counter):
    """The same construct in its correct form leaves the rule silent."""
    assert rule not in _rules(counter), f"{rule} should stay silent"


def test_minimal_document_triggers_no_rule_at_all():
    """The minimal document is clean: no error rule and no warning rule fires."""
    assert _rules(_doc()) == []


def test_minimal_document_is_schema_valid():
    """The same minimal document validates against the delivery schema zbz_hersch.rng."""
    schema = _etree.RelaxNG(_etree.parse(str(TEI_SCHEMA_PATH)))
    doc = _etree.fromstring(_doc().encode("utf-8"))
    assert schema.validate(doc), str(schema.error_log)


def test_error_rules_are_reported_as_errors_not_warnings():
    """R rules block delivery, so they must land in the error list, not among the warnings."""
    root = _etree.fromstring(_doc(root_attrs="").encode("utf-8"))
    errors, warnings = _check_project_rules(root)
    assert "R1" in [e["rule"] for e in errors]
    assert "R1" not in [w["rule"] for w in warnings]


def test_warning_rules_are_reported_as_warnings_not_errors():
    """W rules are curation signals and must never make a document invalid."""
    root = _etree.fromstring(
        _doc(header=HEADER.replace('ident="fra"', 'ident="und"')).encode("utf-8")
    )
    errors, warnings = _check_project_rules(root)
    assert "W1" in [w["rule"] for w in warnings]
    assert errors == []


def test_every_finding_carries_a_line_number_field():
    """Report and HTML renderer address findings by line; the field is part of the contract."""
    root = _etree.fromstring(_doc(root_attrs="").encode("utf-8"))
    errors, warnings = _check_project_rules(root)
    for finding in errors + warnings:
        assert "line" in finding
        assert isinstance(finding["line"], int)
