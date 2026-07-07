"""Tests fuer die Step-1-Chrome-Projektion in scripts.tei.tei_step1.

Sichert zwei belegte Defekte ab (siehe Task-Kontext / journal):

Defekt A (Seitenzahl): die Druckseitenzahl steht in einer _filter-Fusszeilen-Region
(z.B. 570 Seite 2: Region "248"); <pb> bekam bisher die laufende Scan-Nummer. detect_page_number
projiziert die gedruckte Zahl, drop_filter_echoes entfernt den zugehoerigen OCR-Absatz.

Defekt B (Filter-Leck): match_paragraphs_to_regions entfernt _filter/_skip-Regionen, laesst die
zugehoerigen OCR-Absaetze aber stehen; sie werden positionsbasiert falschen Regionen zugeordnet
oder als bbox-loser Ueberhang angehaengt (570 Seite 1: acht E-Periodica-Deckblattzeilen).
drop_filter_echoes verwirft die Absaetze vor dem Matching.

Die Region-/Absatz-Fixtures sind aus den echten 570-Daten extrahiert
(output/layout/570/570_p00{1,2}_layout_gemini.json + output/mistral_results/570_p{1,2}.md),
klein gehalten. Ein zusaetzlicher Integrationstest laeuft gegen die echten Dateien, falls
vorhanden (output/ ist gitignored, daher skip-if-missing).
"""
from pathlib import Path

import pytest

from scripts.tei.tei_generator import split_paragraphs
from scripts.tei.tei_step1 import (
    detect_page_number,
    drop_filter_echoes,
    interpolate_document_pb,
    process_page_step1,
)

REPO_ROOT = Path(__file__).resolve().parent.parent


# --- Fixtures aus 570 Seite 1 (Deckblatt, acht _filter-Regionen) ---------------

P1_FILTER_REGIONS = [
    {"zbz_tag": "_filter", "text": "Zeitschrift:"},
    {"zbz_tag": "_filter", "text": "Studia philosophica : Schweizerische Zeitschrift für Philosophie = Revue suisse de philosophie = Rivista svizzera della filosofia = Swiss journal of philosophy"},
    {"zbz_tag": "_filter", "text": "Herausgeber:"},
    {"zbz_tag": "_filter", "text": "Schweizerische Philosophische Gesellschaft 21 (1961)"},
    {"zbz_tag": "_filter", "text": "Band:"},
    {"zbz_tag": "_filter", "text": "Buchbesprechung: Besprechungen = Comptes rendus"},
    {"zbz_tag": "_filter", "text": "Download PDF: 24.02.2025"},
    {"zbz_tag": "_filter", "text": "ETH-Bibliothek Zürich, E-Periodica; https://www.e-periodica.ch"},
]

P1_RELEVANT_REGIONS = [
    {"zbz_tag": "zb_heading", "text": "Nutzungsbedingungen"},
    {"zbz_tag": "zb_paragraph", "text": "Die ETH-Bibliothek ist die Anbieterin ..."},
    {"zbz_tag": "zb_heading", "text": "Conditions d'utilisation"},
    {"zbz_tag": "zb_paragraph", "text": "L'ETH Library est le fournisseur ..."},
    {"zbz_tag": "zb_heading", "text": "Terms of use"},
    {"zbz_tag": "zb_paragraph", "text": "The ETH Library is the provider ..."},
]

P1_PARAGRAPHS = [
    "Zeitschrift: Studia philosophica : Schweizerische Zeitschrift für Philosophie = Revue suisse de philosophie = Rivista svizzera della filosofia = Swiss journal of philosophy",
    "Herausgeber: Schweizerische Philosophische Gesellschaft",
    "Band: 21 (1961)",
    "Buchbesprechung: Besprechungen = Comptes rendus",
    "## Nutzungsbedingungen",
    "Die ETH-Bibliothek ist die Anbieterin der digitalisierten Zeitschriften. Sie besitzt keine Urheberrechte an den Zeitschriften und ist nicht verantwortlich für deren Inhalte. Die Rechte liegen in der Regel bei den Herausgebern beziehungsweise den externen Rechteinhabern. Siehe Rechtliche Hinweise.",
    "## Conditions d'utilisation",
    "L'ETH Library est le fournisseur des revues numérisées. Elle ne détient aucun droit d'auteur sur les revues et n'est pas responsable de leur contenu. En règle générale, les droits sont détenus par les éditeurs ou les détenteurs de droits externes. Voir Informations légales.",
    "## Terms of use",
    "The ETH Library is the provider of the digitised journals. It does not own any copyrights to the journals and is not responsible for their content. The rights usually lie with the publishers or the external rights holders. See Legal notice.",
    "Download PDF: 24.02.2025",
    "ETH-Bibliothek Zürich, E-Periodica, https://www.e-periodica.ch",
]

# Fixtures aus 570 Seite 2 (Fusszeile "248" + Fliesstext)
P2_REGIONS = [
    {"zbz_tag": "zb_paragraph", "text": "L'évidence phénoménologique renvoie ..."},
    {"zbz_tag": "zb_paragraph", "text": "Telle est la thèse générale ..."},
    {"zbz_tag": "zb_paragraph", "text": "Fernand Brunner"},
    {"zbz_tag": "zb_heading", "text": "Jean-Pierre Leyvraz: Le Temple et le Dieu ..."},
    {"zbz_tag": "zb_paragraph", "text": "Le livre de J.-P. Leyvraz ..."},
    {"zbz_tag": "zb_paragraph", "text": "Malgré sa frappante originalité ..."},
    {"zbz_tag": "_filter", "text": "248"},
]


# --- detect_page_number --------------------------------------------------------

def test_detect_page_number_from_footer():
    assert detect_page_number(P2_REGIONS) == "248"


def test_detect_page_number_none_on_cover_sheet():
    # Deckblatt: kein _filter mit reiner Seitenzahl -> Fallback (Scan-Nummer) durch Aufrufer
    assert detect_page_number(P1_FILTER_REGIONS + P1_RELEVANT_REGIONS) is None


@pytest.mark.parametrize(
    "text,expected",
    [
        ("248", "248"),
        ("[249]", "249"),
        (" 12 ", "12"),
        ("7.14", "7.14"),
        ("[7.14]", "7.14"),
    ],
)
def test_detect_page_number_notations(text, expected):
    assert detect_page_number([{"zbz_tag": "_filter", "text": text}]) == expected


def test_detect_page_number_ignores_non_filter_and_prose():
    regions = [
        {"zbz_tag": "zb_paragraph", "text": "42"},          # nicht _filter
        {"zbz_tag": "_filter", "text": "Studia philosophica 21"},  # keine reine Zahl
    ]
    assert detect_page_number(regions) is None


# --- drop_filter_echoes --------------------------------------------------------

def test_drop_filter_echoes_removes_cover_sheet_lines():
    kept = drop_filter_echoes(P1_PARAGRAPHS, P1_FILTER_REGIONS + P1_RELEVANT_REGIONS)
    # Genau die sechs echten Regionen (drei headings + drei Absaetze) bleiben.
    assert len(kept) == 6
    assert kept == [
        P1_PARAGRAPHS[4], P1_PARAGRAPHS[5], P1_PARAGRAPHS[6],
        P1_PARAGRAPHS[7], P1_PARAGRAPHS[8], P1_PARAGRAPHS[9],
    ]
    # Keine der acht Deckblatt-Zeilen ueberlebt (Absatz-Identitaet, nicht Substring:
    # der echte Fliesstext enthaelt "Zeitschriften" und "ETH-Bibliothek").
    for leaked in (P1_PARAGRAPHS[0], P1_PARAGRAPHS[1], P1_PARAGRAPHS[2],
                   P1_PARAGRAPHS[3], P1_PARAGRAPHS[10], P1_PARAGRAPHS[11]):
        assert leaked not in kept


def test_drop_filter_echoes_removes_page_number_paragraph():
    paras = [
        "L'évidence phénoménologique renvoie à l'ego transcendantal.",
        "Malgré sa frappante originalité, il s'enracine dans la tradition.",
        "248",
    ]
    kept = drop_filter_echoes(paras, P2_REGIONS)
    assert "248" not in kept
    assert len(kept) == 2


def test_drop_filter_echoes_keeps_body_reusing_metadata_word():
    # "ETH-Bibliothek" kommt auch im Fusszeilen-Filter vor; ein echter Absatz, der das Wort
    # nur nebenbei nutzt, darf NICHT verworfen werden (konservative Kalibrierung).
    body = ("Die ETH-Bibliothek ist die Anbieterin der digitalisierten Zeitschriften. "
            "Sie besitzt keine Urheberrechte an den Zeitschriften.")
    kept = drop_filter_echoes([body], P1_FILTER_REGIONS)
    assert kept == [body]


def test_drop_filter_echoes_no_filter_regions_is_identity():
    paras = ["a paragraph", "another one"]
    assert drop_filter_echoes(paras, P1_RELEVANT_REGIONS) == paras


# --- interpolate_document_pb (dokumentweiter Interpolations-Pass) --------------
# Forward-verankerte Konsistenzregel: eine Luecke wird nur gefuellt, wenn ein linker
# Anker existiert und (falls auch ein rechter Anker existiert) beide denselben Wert
# stuetzen. Rueckwaertige Extrapolation (nur rechter Anker) fuellt NICHT -- Frontmatter
# vor der ersten gedruckten Zahl (Deckblatt) bleibt Scan-Nummer-Fallback.


def test_interpolate_fills_gap_between_two_detected():
    # 248 auf p2, 250 auf p4, Luecke p3 -> eindeutig 249.
    result = interpolate_document_pb({2: 248, 4: 250}, [1, 2, 3, 4])
    assert result[3] == 249
    # p1 hat keinen linken Anker -> keine Rueckwaerts-Extrapolation.
    assert 1 not in result
    # Erkannte Seiten bleiben unberuehrt (nur Luecken landen im Ergebnis).
    assert 2 not in result and 4 not in result


def test_interpolate_rejects_inconsistent_neighbors():
    # 248 auf p2, 251 auf p4, eine Luecke p3: vorwaerts 249, rueckwaerts 250 ->
    # widerspruechlich -> NICHT interpolieren.
    result = interpolate_document_pb({2: 248, 4: 251}, [1, 2, 3, 4])
    assert 3 not in result


def test_interpolate_edge_without_support_stays_fallback():
    # Kein einziger erkannter Anker -> nichts wird gefuellt.
    assert interpolate_document_pb({}, [1, 2, 3]) == {}


def test_interpolate_forward_extrapolation_single_left_anchor():
    # 570-Form: 248 auf p2, p3 ohne Fusszeile, kein rechter Anker -> Folgewert 249.
    result = interpolate_document_pb({2: 248}, [1, 2, 3])
    assert result == {3: 249}
    # p1 (Deckblatt, vor der ersten Zahl) bekommt keine erschlossene Nummer.
    assert 1 not in result


# --- Integration gegen echte 570-Daten (skip-if-missing, output/ gitignored) ---

def _has_570_page(page: int) -> bool:
    md = REPO_ROOT / "output" / "mistral_results" / f"570_p{page}.md"
    layout = REPO_ROOT / "output" / "layout" / "570" / f"570_p{page:03d}_layout_gemini.json"
    return md.exists() and layout.exists()


@pytest.mark.skipif(not _has_570_page(2), reason="output/570 nicht vorhanden (gitignored)")
def test_process_page_step1_570_p2_uses_printed_page_number():
    fragment, _ = process_page_step1("570", 2, metadata={}, genre="review")
    assert 'n="248"' in fragment
    assert 'n="2"' not in fragment
    # Die Seitenzahl leckt nicht mehr als eigener Absatz.
    assert "<p" in fragment and ">\n          248\n" not in fragment


@pytest.mark.skipif(not _has_570_page(3), reason="output/570 nicht vorhanden (gitignored)")
def test_process_page_step1_570_p3_interpolates_printed_number():
    # p3 hat keine Fusszeilen-Region; der Wert wird aus p2 (248) forward-erschlossen.
    # Referenzkonvention: erschlossene Zahlen stehen in eckigen Klammern.
    fragment, _ = process_page_step1("570", 3, metadata={}, genre="review")
    assert 'n="[249]"' in fragment
    assert 'n="3"' not in fragment


@pytest.mark.skipif(not _has_570_page(1), reason="output/570 nicht vorhanden (gitignored)")
def test_process_page_step1_570_p1_drops_cover_sheet():
    fragment, _ = process_page_step1("570", 1, metadata={}, genre="review")
    assert "Zeitschrift" not in fragment
    assert "e-periodica" not in fragment
    assert "Download PDF" not in fragment
    # Deckblatt hat keine gedruckte Seitenzahl -> Scan-Nummer bleibt Fallback.
    assert 'n="1"' in fragment
