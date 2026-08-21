"""
Goldene Regressionstests fuer die CER-Textschicht (Extraktion + Alignment + Norm).

Diese Tests sichern den CER-VERTRAG (siehe scripts/eval/evaluate_ocr.py Modul-Doku)
mit handberechneten Werten ab -- unabhaengig vom konkreten Korpus-Ergebnis. Sie sind
die eigentliche Korrektheits-Garantie: jede kuenftige Pipeline-Aenderung, die die
CER-Semantik still verschiebt (Lowercasing, Trimming, Footnote-Handling, choice,
NFC), bricht hier.

Verifiziert gegen die Konventionen von OCR-D, dinglehopper, Transkribus, jiwer.
"""

from __future__ import annotations

import pytest

from scripts.eval.evaluate_ocr import (
    calculate_cer,
    categorize_errors,
    classify_edit_operations,
    evaluate_tei_vs_tei,
    extract_text_for_comparison,
    find_differences,
)
from tests.conftest import tei_doc, tei_header

# --------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------- #

TEI_NS = "http://www.tei-c.org/ns/1.0"


def _tei(body_inner: str) -> str:
    """Minimales, valide-genug TEI mit dem gegebenen body-Inhalt."""
    return tei_doc(body_inner, header="<teiHeader/>", xml_decl=True)


def _write(tmp_path, name: str, body_inner: str):
    p = tmp_path / name
    p.write_text(_tei(body_inner), encoding="utf-8")
    return p


# --------------------------------------------------------------------- #
# 1. Formel / Identitaet
# --------------------------------------------------------------------- #

class TestCanonicalFormula:
    def test_identical_is_zero(self, tmp_path):
        f = _write(tmp_path, "a.xml", "<p>alpha beta gamma delta</p>")
        t = extract_text_for_comparison(f)
        assert calculate_cer(t, t) == 0.0

    def test_known_substitution_ratio(self, tmp_path):
        # ref = 10 Zeichen, 2 Substitutionen -> CER = 0.2
        ref = extract_text_for_comparison(_write(tmp_path, "r.xml", "<p>abcdefghij</p>"))
        hyp = extract_text_for_comparison(_write(tmp_path, "h.xml", "<p>abcXefghiY</p>"))
        assert ref == "abcdefghij"
        assert calculate_cer(ref, hyp) == pytest.approx(0.2)


# --------------------------------------------------------------------- #
# 2. Case-Sensitivitaet (der zentrale Fix: kein pauschales lower())
# --------------------------------------------------------------------- #

class TestCaseSensitivity:
    def test_case_difference_counts_when_sensitive(self, tmp_path):
        # "Freiheit" vs "freiheit": 1 Edit / 8 Zeichen = 0.125 (PRIMAER, case-sensitiv)
        rp = _write(tmp_path, "r.xml", "<p>Freiheit</p>")
        hp = _write(tmp_path, "h.xml", "<p>freiheit</p>")
        ref = extract_text_for_comparison(rp)            # case-sensitiv
        hyp = extract_text_for_comparison(hp)
        assert ref == "Freiheit"
        assert calculate_cer(ref, hyp) == pytest.approx(0.125)

    def test_case_difference_vanishes_when_casefolded(self, tmp_path):
        # Dieselbe Differenz, case-insensitiv (Sekundaer) -> 0.0
        rp = _write(tmp_path, "r.xml", "<p>Freiheit</p>")
        hp = _write(tmp_path, "h.xml", "<p>freiheit</p>")
        ref = extract_text_for_comparison(rp, casefold=True)
        hyp = extract_text_for_comparison(hp, casefold=True)
        assert ref == "freiheit"
        assert calculate_cer(ref, hyp) == 0.0

    def test_eszett_casefold(self, tmp_path):
        # casefold ist Unicode-korrekt: "STRASSE" == "straße"
        rp = _write(tmp_path, "r.xml", "<p>STRASSE</p>")
        hp = _write(tmp_path, "h.xml", "<p>straße</p>")
        ref = extract_text_for_comparison(rp, casefold=True)
        hyp = extract_text_for_comparison(hp, casefold=True)
        assert calculate_cer(ref, hyp) == 0.0


# --------------------------------------------------------------------- #
# 3. KEIN Trimming: Extra-Hypothesen-Text zaehlt als Insertions
# --------------------------------------------------------------------- #

class TestNoTrimming:
    def test_extra_hypothesis_text_counts(self, tmp_path):
        # ref ~ N Zeichen, hyp = ref + grosser Extra-Block.
        words = " ".join(
            ["alpha", "beta", "gamma", "delta", "epsilon", "zeta", "eta", "theta",
             "iota", "kappa", "lambda", "mu", "nu", "xi", "omicron", "pi", "rho",
             "sigma", "tau", "upsilon", "phi", "chi", "psi", "omega"]
        )
        extra = " " + ("ZZZ " * 25).strip()  # ~100 Extra-Zeichen am Ende
        ref_path = tmp_path / "1.xml"
        pipe_path = tmp_path / "1_final.xml"
        ref_path.write_text(_tei(f"<p>{words}</p>"), encoding="utf-8")
        pipe_path.write_text(_tei(f"<p>{words}{extra}</p>"), encoding="utf-8")

        res = evaluate_tei_vs_tei("1", tmp_path, tmp_path)
        assert res["status"] == "OK"

        ref_len = res["ref_chars"]
        # Primaer-CER spiegelt die Insertions wider (Extra-Block NICHT weggetrimmt).
        assert res["cer"] == pytest.approx(len(extra) / ref_len, abs=0.02)
        # Das alte Alignment-Trimming HAETTE den Extra-Block versteckt:
        # die Diagnose-Zahl ist deutlich kleiner als die ehrliche Primaer-CER.
        assert res["cer_aligned_legacy"] < res["cer"]

    def test_high_cer_stays_ok_not_mismatch(self, tmp_path):
        # Voellig verschiedener Text: CER hoch, aber Status bleibt OK (kein Ausschluss).
        ref_path = tmp_path / "2.xml"
        pipe_path = tmp_path / "2_final.xml"
        ref_path.write_text(_tei("<p>" + ("aaaa " * 30).strip() + "</p>"), encoding="utf-8")
        pipe_path.write_text(_tei("<p>" + ("bbbb " * 30).strip() + "</p>"), encoding="utf-8")
        res = evaluate_tei_vs_tei("2", tmp_path, tmp_path)
        assert res["status"] == "OK"
        assert res["cer"] > 0.5
        assert res["high_cer"] is True


# --------------------------------------------------------------------- #
# 4. <choice> -> nur <corr>; Fussnoten exkludiert
# --------------------------------------------------------------------- #

class TestChoiceAndFootnotes:
    def test_choice_uses_corr_only(self, tmp_path):
        f = _write(tmp_path, "c.xml",
                   "<p>Das ist <choice><sic>falsh</sic><corr>falsch</corr></choice> hier.</p>")
        t = extract_text_for_comparison(f)
        assert "falsch" in t
        assert "falsh" not in t  # sic darf NICHT im Vergleichstext stehen

    def test_footnote_excluded_by_default(self, tmp_path):
        body = '<p>Haupttext.<note place="foot">Fussnoteninhalt.</note> Weiter.</p>'
        f = _write(tmp_path, "fn.xml", body)
        without = extract_text_for_comparison(f, include_footnotes=False)
        withfn = extract_text_for_comparison(f, include_footnotes=True)
        assert "Fussnoteninhalt" not in without
        assert "Fussnoteninhalt" in withfn
        assert len(withfn) > len(without)


# --------------------------------------------------------------------- #
# 5. Unicode-Normalisierung (NFC, Bindestriche, Guillemets) -- symmetrisch
# --------------------------------------------------------------------- #

class TestNormalization:
    def test_nfc_combining_diacritic_equals_precomposed(self, tmp_path):
        # "cafe" + combining acute  ==  praekomponiertes "café"
        decomposed = _write(tmp_path, "d.xml", "<p>café</p>")
        precomposed = _write(tmp_path, "p.xml", "<p>café</p>")
        a = extract_text_for_comparison(decomposed)
        b = extract_text_for_comparison(precomposed)
        assert a == b
        assert calculate_cer(a, b) == 0.0

    def test_dash_variants_normalized(self, tmp_path):
        # En-Dash vs ASCII-Hyphen -> kein Fehler
        a = extract_text_for_comparison(_write(tmp_path, "a.xml", "<p>wohl–sein</p>"))
        b = extract_text_for_comparison(_write(tmp_path, "b.xml", "<p>wohl-sein</p>"))
        assert calculate_cer(a, b) == 0.0

    def test_guillemets_normalized(self, tmp_path):
        a = extract_text_for_comparison(_write(tmp_path, "a.xml", "<p>«mot»</p>"))
        b = extract_text_for_comparison(_write(tmp_path, "b.xml", '<p>"mot"</p>'))
        assert calculate_cer(a, b) == 0.0


# --------------------------------------------------------------------- #
# 6. Fehlerkategorien summieren zur tatsaechlichen Editierdistanz (editops)
# --------------------------------------------------------------------- #

class TestEditOperationDecomposition:
    """fidelity (echte Fehler) vs scope (Pipeline-Mehrtext), asymmetrisch."""

    def test_substitution_is_fidelity_not_scope(self):
        ref = "alpha beta gamma delta"
        hyp = "alpha beXa gamma delta"  # 1 Substitution
        c = classify_edit_operations(ref, hyp)
        assert c["scope_insertion_distance"] == 0
        assert c["fidelity_distance"] == 1
        assert c["cer_fidelity"] == pytest.approx(c["cer"])

    def test_large_insertion_is_scope_not_fidelity(self):
        ref = "der eigentliche artikel text steht hier in der referenz drin"
        hyp = ref + " " + ("X" * 80)  # 80-Zeichen-Block = Pipeline-Mehrtext
        c = classify_edit_operations(ref, hyp)
        assert c["scope_insertion_distance"] >= 80
        assert c["fidelity_distance"] <= 1  # nur das Leerzeichen evtl.
        # Die volle CER ist hoch, die Fidelity-CER ~0.
        assert c["cer"] > 1.0
        assert c["cer_fidelity"] < 0.05

    def test_deletion_counts_as_fidelity_error(self):
        # Pipeline VERPASST einen ganzen Block -> echtes Versaeumnis, KEIN scope.
        ref = "anfang " + ("Y" * 80) + " ende"
        hyp = "anfang  ende"
        c = classify_edit_operations(ref, hyp)
        assert c["scope_insertion_distance"] == 0
        assert c["fidelity_distance"] >= 80

    def test_small_insertion_is_fidelity(self):
        ref = "alpha beta gamma"
        hyp = "alpha beta gammaX"  # 1 spurioses Zeichen
        c = classify_edit_operations(ref, hyp)
        assert c["scope_insertion_distance"] == 0
        assert c["fidelity_distance"] == 1

    def test_decomposition_is_additive_and_matches_calculate_cer(self):
        ref = "ein laengerer referenztext mit etwas inhalt zum vergleichen hier"
        hyp = "ein laengrer referenztext " + ("Z" * 70) + " mit etwas inhalt zum vergliechen hier"
        c = classify_edit_operations(ref, hyp)
        # cer == calculate_cer (gleiche Levenshtein-Distanz / N)
        assert c["cer"] == pytest.approx(calculate_cer(ref, hyp))
        # additiv: fidelity + scope == total
        assert c["fidelity_distance"] + c["scope_insertion_distance"] == c["total_distance"]
        assert c["cer_fidelity"] + c["scope_insertion_rate"] == pytest.approx(c["cer"])


class TestErrorCategoriesSumToDistance:
    def test_category_char_distance_sums_to_levenshtein(self, tmp_path):
        ref = "der schnelle braune fuchs springt ueber den faulen hund"
        hyp = "der schnelle braune fux sprint ueber den faulen hund"
        from rapidfuzz.distance import Levenshtein
        true_dist = Levenshtein.distance(ref, hyp)
        diffs = find_differences(ref, hyp)
        cats = categorize_errors(diffs, len(ref))
        summed = sum(c["char_distance"] for c in cats.values())
        # editops-basierte Blockdistanzen (max(len_ref,len_hyp) je Block) summieren
        # exakt zur Levenshtein-Distanz.
        assert summed == true_dist


# --------------------------------------------------------------------- #
# 7. Extraktionsregeln E1-E12 (knowledge/methodology.md (CER measurement section), Tabelle)
# --------------------------------------------------------------------- #

class TestExtractionRules:
    """Je eine direkte Pruefung pro Regel der Extraktionstabelle."""

    def test_namespace_prefix_is_stripped(self, tmp_path):
        """E1: der TEI-Namespace verschwindet, die Elementinhalte bleiben."""
        f = _write(tmp_path, "ns.xml", "<p>alpha</p>")
        assert extract_text_for_comparison(f) == "alpha"

    def test_only_body_is_read(self, tmp_path):
        """E2: teiHeader, front und back liefern keinen Vergleichstext."""
        path = tmp_path / "b.xml"
        path.write_text(
            tei_doc(
                "<p>Haupttext.</p>",
                header=tei_header("HEADERTITEL"),
            ).replace("<body>", "<front><p>FRONTTEXT</p></front><body>")
            .replace("</body>", "</body><back><p>BACKTEXT</p></back>"),
            encoding="utf-8",
        )
        text = extract_text_for_comparison(path)
        assert text == "Haupttext."

    def test_choice_without_corr_falls_back_to_sic(self, tmp_path):
        """E4: fehlt <corr>, liefert <choice> die ueberlieferte Form <sic>."""
        f = _write(tmp_path, "sic.xml",
                   "<p>Das <choice><sic>falsh</sic></choice> hier.</p>")
        assert extract_text_for_comparison(f) == "Das falsh hier."

    def test_line_break_becomes_one_space(self, tmp_path):
        """E6: <lb/> ohne break-Attribut ist eine Wortgrenze."""
        f = _write(tmp_path, "lb.xml", "<p>eins<lb/>zwei</p>")
        assert extract_text_for_comparison(f) == "eins zwei"

    def test_hyphenation_break_joins_the_word(self, tmp_path):
        """E7: <lb break="no"/> liefert kein Zeichen, das Wort wird zusammengesetzt."""
        f = _write(tmp_path, "lbno.xml", '<p>Hu<lb break="no"/>manismus</p>')
        assert extract_text_for_comparison(f) == "Humanismus"

    def test_page_break_collapses_to_a_single_space(self, tmp_path):
        """E8 + N15: <pb/> setzt zwei Umbrueche, die Normalisierung macht ein Leerzeichen daraus.

        Die Regeltabelle nennt als Wirkung von E8 "die Seitengrenze bleibt erkennbar";
        im Vergleichstext ist sie es nicht mehr, weil N15 jede Whitespace-Folge auf ein
        Leerzeichen zieht. Der Test haelt das tatsaechliche Verhalten fest.
        """
        f = _write(tmp_path, "pb.xml", '<p>a</p><pb n="2"/><p>b</p>')
        assert extract_text_for_comparison(f) == "a b"

    def test_markup_is_transparent(self, tmp_path):
        """E9: <hi> und die uebrigen Elemente liefern ihren Innentext ohne Markup."""
        f = _write(tmp_path, "hi.xml", '<p>ein <hi rend="i">Wort</hi> hier</p>')
        assert extract_text_for_comparison(f) == "ein Wort hier"

    def test_forme_work_is_included_not_excluded(self, tmp_path):
        """E9 auch fuer <fw>: der Kolumnentitel steht im Vergleichstext.

        Es gibt keine fw-Ausnahmeregel; <fw> faellt unter E9 wie jedes andere Element.
        """
        f = _write(tmp_path, "fw.xml", '<p>Text.</p><fw type="head">KOLUMNENTITEL</fw>')
        assert extract_text_for_comparison(f) == "Text.KOLUMNENTITEL"

    def test_attribute_values_never_appear(self, tmp_path):
        """E10: pb@n und ref-Attribute liefern keinen Vergleichstext."""
        f = _write(tmp_path, "attr.xml",
                   '<p rend="italic">a</p><pb n="223"/>'
                   '<p><persName ref="GND:118815679">N</persName></p>')
        text = extract_text_for_comparison(f)
        assert "223" not in text and "GND" not in text and "italic" not in text
        assert text == "a N"

    def test_tail_text_keeps_the_order(self, tmp_path):
        """E11: der Tail eines Kindelements steht hinter dessen Inhalt."""
        f = _write(tmp_path, "tail.xml", "<p>Wort1<hi>Wort2</hi>Wort3</p>")
        assert extract_text_for_comparison(f) == "Wort1Wort2Wort3"

    def test_parse_error_falls_back_to_tag_stripping(self, tmp_path):
        """E12: ein nicht wohlgeformtes TEI liefert den tag-befreiten Rohtext."""
        f = tmp_path / "broken.xml"
        f.write_text('<TEI xmlns="' + TEI_NS + '"><text><body><p>kaputt<p>'
                     "</body></text></TEI>", encoding="utf-8")
        assert extract_text_for_comparison(f) == "kaputt"

    def test_whitespace_runs_collapse(self, tmp_path):
        """N15: Mehrfach-Whitespace und Zeilenumbrueche werden zu einem Leerzeichen."""
        f = _write(tmp_path, "ws.xml", "<p>a   b\n\n  c</p>")
        assert extract_text_for_comparison(f) == "a b c"

    def test_blank_page_contributes_no_text(self, tmp_path):
        """Leerseite: ein <pb type="blank"/> ohne Inhalt bringt kein Zeichen ein."""
        with_blank = _write(tmp_path, "blank.xml",
                            '<p>a</p><pb n="2" type="blank"/><pb n="3"/><p>c</p>')
        without = _write(tmp_path, "noblank.xml", '<p>a</p><pb n="3"/><p>c</p>')
        assert extract_text_for_comparison(with_blank) == extract_text_for_comparison(without)
        assert extract_text_for_comparison(with_blank) == "a c"
