"""Tests fuer den Zeichen-Lint (scripts.eval.char_lint_audit)."""

from scripts.eval.char_lint_audit import find_issues, lint_text_nodes
from tests.conftest import tei_doc, tei_header


def _tei(body_inner: str, lang_ident: str | None = None) -> str:
    lang_block = (
        f'<profileDesc><langUsage><language ident="{lang_ident}" /></langUsage></profileDesc>'
        if lang_ident
        else ""
    )
    # the header title carries all four signals; they must NOT be counted
    header = tei_header("d'Alembert «quote» mot ! text¬", extra=lang_block)
    return tei_doc(body_inner, header=header)


def test_straight_apostrophe_between_letters():
    nodes = ["l'auteur defend"]
    res = lint_text_nodes(nodes)
    assert res["straight_apostrophe"]["count"] == 1


def test_apostrophe_not_between_letters_ignored():
    # apostrophe at edge or next to digit/space is not the guideline violation
    nodes = ["'quote' 5'6 word "]
    res = lint_text_nodes(nodes)
    assert res["straight_apostrophe"]["count"] == 0


def test_curly_apostrophe_is_fine():
    nodes = ["l’auteur"]  # U+2019 is the required form
    res = lint_text_nodes(nodes)
    assert res["straight_apostrophe"]["count"] == 0


def test_guillemets_both_directions():
    nodes = ["«La theorie» ainsi «autre»"]
    res = lint_text_nodes(nodes)
    assert res["guillemets"]["count"] == 4


def test_space_before_punctuation_incl_nbsp():
    nodes = ["mot : autre ; fin ! quoi ? oui . non , stop"]
    res = lint_text_nodes(nodes)
    assert res["space_before_punct"]["count"] == 6
    nodes_nbsp = ["mot : suite"]
    assert lint_text_nodes(nodes_nbsp)["space_before_punct"]["count"] == 1


def test_hyphenation_residue():
    nodes = ["Silben¬trennung und wei¬ter"]
    res = lint_text_nodes(nodes)
    assert res["hyphenation_residue"]["count"] == 2


def test_body_only_header_and_attributes_ignored():
    # body text node carries exactly one of each; header + facs attribute must not count
    body = (
        '<div><pb n="1" facs="#f1"/>'
        "<p>l'auteur «mot» fin : ende¬</p></div>"
    )
    res = find_issues(_tei(body))
    assert res["straight_apostrophe"]["count"] == 1
    assert res["guillemets"]["count"] == 2
    assert res["space_before_punct"]["count"] == 1
    assert res["hyphenation_residue"]["count"] == 1


def test_examples_captured_and_capped():
    nodes = ["l'un l'autre l'encore l'ici l'la"]
    res = lint_text_nodes(nodes, max_examples=2)
    assert res["straight_apostrophe"]["count"] == 5
    assert len(res["straight_apostrophe"]["examples"]) == 2


# --- language-aware space-before-punctuation split (French calibration 2026-07-07) ---


def test_french_high_punct_plain_space_is_space_type():
    # French context: plain U+0020 before ; : ? ! » is a wrong space TYPE, not an
    # extra character; it is reported in the soft class space_type, not the sharp one.
    nodes = ["mot : autre ; fin ! quoi ? clos »"]
    res = lint_text_nodes(nodes, french_context=True)
    assert res["space_type"]["count"] == 5
    assert res["space_before_punct"]["count"] == 0


def test_french_narrow_or_nbsp_before_high_punct_is_clean():
    # correct French typography already uses a (narrow) no-break space -> no finding
    nodes = ["mot : autre ; fin !"]
    res = lint_text_nodes(nodes, french_context=True)
    assert res["space_type"]["count"] == 0
    assert res["space_before_punct"]["count"] == 0


def test_french_space_before_period_and_comma_stays_sharp():
    # . and , never take a French space; a space there is a real extra character
    nodes = ["oui . non , stop"]
    res = lint_text_nodes(nodes, french_context=True)
    assert res["space_before_punct"]["count"] == 2
    assert res["space_type"]["count"] == 0


def test_non_french_high_punct_stays_sharp():
    # outside French context the historic behaviour is unchanged
    nodes = ["mot : autre ; fin ! quoi ?"]
    res = lint_text_nodes(nodes, french_context=False)
    assert res["space_before_punct"]["count"] == 4
    assert res["space_type"]["count"] == 0


def test_non_french_default_matches_legacy_counts():
    # default (no language flag) must reproduce the legacy sharp counts exactly
    nodes = ["mot : autre ; fin ! quoi ? oui . non , stop"]
    res = lint_text_nodes(nodes)
    assert res["space_before_punct"]["count"] == 6
    assert res["space_type"]["count"] == 0


def test_language_detected_from_langusage_french():
    body = "<div><p>mot : suite</p></div>"
    res = find_issues(_tei(body, lang_ident="fra"))
    assert res["space_type"]["count"] == 1
    assert res["space_before_punct"]["count"] == 0


def test_language_detected_from_langusage_german():
    body = "<div><p>Wort : Satz</p></div>"
    res = find_issues(_tei(body, lang_ident="deu"))
    assert res["space_before_punct"]["count"] == 1
    assert res["space_type"]["count"] == 0


def test_multilingual_document_with_french_counts_as_french():
    # a doc listing several languages including French is treated as French context
    header = ("<teiHeader><profileDesc><langUsage>"
              '<language ident="deu" /><language ident="fra" />'
              "</langUsage></profileDesc></teiHeader>")
    tei = tei_doc("<p>mot : suite</p>", header=header)
    res = find_issues(tei)
    assert res["space_type"]["count"] == 1


def test_apostrophe_invariant_under_french_reinterpretation():
    # the apostrophe finding must not shift when the doc is French
    nodes = ["l'auteur defend l'idee"]
    assert lint_text_nodes(nodes, french_context=True)["straight_apostrophe"]["count"] == 2
    assert lint_text_nodes(nodes, french_context=False)["straight_apostrophe"]["count"] == 2
