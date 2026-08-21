"""Repair path of step 2 (scripts/tei/tei_step2) on synthetic malformed Gemini output.

Two layers. `fix_gemini_tei` is the pure post-processor over a TEI fragment: it unwraps
the wrappers Gemini invents, moves a late `<head>` back into running text and wraps loose
inline elements, and it must leave a fragment it cannot parse untouched instead of
mangling it. `process_page_step2` is the call path around it: it strips a markdown fence,
checks well-formedness and, when the answer is not well-formed, keeps the step-1 scaffold.

No API call happens: the client is a stub whose `generate_content` returns the prepared
answer, and the call count proves the dry run never reaches it.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from scripts.tei.tei_step2 import fix_gemini_tei, process_page_step2

SCAFFOLD = '<div type="text"><pb facs="#facs_1" n="1"/><p>Scaffold.</p></div>'
META = {"page_count": 2, "pub_form": "journalArticle", "lang": "fra", "type": "A",
        "title": "Testdokument", "author": "Hersch, Jeanne", "date": "1975"}


class _StubModels:
    def __init__(self, answer: str):
        self.answer = answer
        self.calls = 0

    def generate_content(self, **kwargs):
        self.calls += 1
        return SimpleNamespace(text=self.answer)


class _StubClient:
    """Stands in for the google.genai client; records whether it was called."""

    def __init__(self, answer: str):
        self.models = _StubModels(answer)


def _refine(answer: str, *, scaffold: str = SCAFFOLD, dry_run: bool = False):
    client = _StubClient(answer)
    result = process_page_step2(client, "TESTDOC", 1, scaffold, META, "essay", "",
                                dry_run=dry_run)
    return result, client.models.calls


# --- fix_gemini_tei: the repairs it performs --------------------------------

def test_ab_wrapper_around_paragraphs_is_unwrapped():
    assert fix_gemini_tei("<ab><p>Text.</p></ab>") == "<p>Text.</p>"


def test_paragraph_inside_head_becomes_the_head_itself():
    """The facs of the inner <p> moves onto the <head> instead of being lost."""
    out = fix_gemini_tei('<head><p facs="#facs_1_r_1">Titel</p></head>')
    assert out == '<head facs="#facs_1_r_1">Titel</head>'


def test_head_after_content_is_demoted_to_a_paragraph():
    out = fix_gemini_tei('<div type="text"><p>Text.</p><head>Zwischentitel</head></div>')
    assert "<head>" not in out
    assert out.count("<p>") == 2


def test_loose_inline_element_is_wrapped_in_a_paragraph():
    out = fix_gemini_tei('<div type="text"><hi rend="i">lose</hi></div>')
    assert '<p><hi rend="i">lose</hi></p>' in out


def test_unclosed_tag_is_returned_untouched():
    """A fragment that does not parse must survive unchanged, not half-repaired."""
    broken = "<p>Text ohne Ende"
    assert fix_gemini_tei(broken) == broken


def test_several_top_level_elements_survive_the_round_trip():
    """A fragment without a single root is legal input; the wrapper root is transparent."""
    assert fix_gemini_tei("<p>eins</p><p>zwei</p>") == "<p>eins</p><p>zwei</p>"


def test_foreign_namespace_loses_its_declaration():
    """Known defect: a fragment in a foreign namespace comes back with a dangling prefix.

    serialize_tei_fragment strips the wrapper root element, and with it the xmlns
    declaration the serializer put there, so the prefix has no binding any more. The
    test pins the current behaviour; repairing it belongs to the production code.
    """
    out = fix_gemini_tei('<div xmlns="http://example.org/other"><p>Text.</p></div>')
    assert out == "<ns1:div><ns1:p>Text.</ns1:p></ns1:div>"
    assert "xmlns" not in out


# --- process_page_step2: the call path around the repair --------------------

def test_markdown_fence_is_stripped_and_the_fragment_repaired():
    out, calls = _refine('```xml\n<ab><p facs="#facs_1_r_1">Text.</p></ab>\n```')
    assert calls == 1
    assert "```" not in out
    assert out == '<p facs="#facs_1_r_1">Text.</p>'


def test_malformed_answer_keeps_the_scaffold():
    """Not well-formed means the page keeps its step-1 scaffold, no half TEI is written."""
    out, calls = _refine("<p>Text ohne Ende")
    assert calls == 1
    assert "Text ohne Ende" not in out
    assert "<p>Scaffold.</p>" in out


def test_answer_without_a_single_root_is_accepted():
    out, _ = _refine("<p>eins</p><p>zwei</p>")
    assert out == "<p>eins</p><p>zwei</p>"


def test_dry_run_returns_the_scaffold_without_calling_the_model():
    out, calls = _refine("<p>never asked</p>", dry_run=True)
    assert calls == 0
    assert out == SCAFFOLD


@pytest.mark.parametrize("answer", ["", "   "])
def test_empty_answer_keeps_the_scaffold(answer):
    """An empty or whitespace-only answer must never replace the page with nothing.

    The well-formedness check wraps the answer in <root>, so an empty string would
    pass it; the guard in front of the check returns the repaired scaffold instead.
    """
    out, calls = _refine(answer)
    assert calls == 1
    assert out == fix_gemini_tei(SCAFFOLD)
