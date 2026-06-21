"""
Shared XML Utilities fuer TEI-Pipeline.

Wird importiert von: tei_step1.py, tei_step2.py, tei_step3.py, tei_generator.py,
tei_validator.py.
"""

import re
import xml.etree.ElementTree as ET

from scripts.config import TEI_NS


# ISO-639 Sprachcode-Normalisierung auf 639-2/T 3-Letter (Projektkonvention: fra/deu/nld/ell
# statt der B-Varianten fre/ger/dut/gre). EINZIGE Quelle der Wahrheit fuer die <foreign>-
# Normalisierung (tei_step3._normalize_foreign_lang) UND die Validator-Warnung W18 -- beide
# rufen normalize_lang_code, damit "was der Pass aendert" und "was W18 meldet" deckungsgleich
# sind. Der teiHeader-langUsage-Pfad (tei_step3._language_idents) bleibt bewusst getrennt
# (anderer Liefer-Vertrag, eigenes Test-Gate E69).
_LANG_B2T = {"fre": "fra", "ger": "deu", "dut": "nld", "gre": "ell"}
_LANG_2TO3_FOREIGN = {
    "fr": "fra", "de": "deu", "en": "eng", "it": "ita",
    "la": "lat", "es": "spa", "el": "ell", "nl": "nld",
    "pt": "por", "ru": "rus", "pl": "pol", "cs": "ces",
    "da": "dan", "sv": "swe", "fi": "fin", "hu": "hun",
    "ro": "ron", "tr": "tur", "ca": "cat",
}


def normalize_lang_code(raw):
    """Kanonische ISO-639-2/T 3-Letter-Form fuer einen xml:lang-Wert auf <foreign>.

    Behandelt Gross-/Kleinschreibung, eckige Klammern, B->T-Varianten (fre->fra), bekannte
    2-Letter-Codes (fr->fra, la->lat) und BCP-47-Region-Subtags (en-US -> eng). Liefert den
    Eingang UNVERAENDERT zurueck, wenn keine Normalisierung bekannt ist -- dadurch melden
    _normalize_foreign_lang und Validator-W18 exakt dieselbe Menge (kein un-raeumbarer Dauer-
    Warnhinweis fuer Codes, die der Pass ohnehin nicht heben koennte).
    """
    if not raw:
        return raw
    c = raw.strip().strip("[]").lower()
    primary = c.split("-")[0]
    if primary in _LANG_B2T:
        return _LANG_B2T[primary]
    if len(primary) == 2 and primary in _LANG_2TO3_FOREIGN:
        return _LANG_2TO3_FOREIGN[primary]
    if len(primary) == 3 and primary.isalpha():
        return primary
    return c if c != raw else raw


# ---------------------------------------------------------------------------
# Lesereihenfolge der Layout-Regionen (spalten- und bandbewusst)
# ---------------------------------------------------------------------------
# Die Layout-Erkennung liefert Regionen bereits linke-Spalte-zuerst, aber eine reine
# y-Sortierung verschraenkt die Spalten bei Zwei-Spalten- und Doppelseiten-Scans wieder
# (belegter Defekt, decisions.md: 30/760). Kanonisch ist eine spaltenbewusste Ordnung:
# vollbreite Bloecke (Titel, lebende Kolumnentitel) segmentieren die Seite in waagrechte
# Baender, innerhalb eines Bands liest man Spalte fuer Spalte links nach rechts, je Spalte
# oben nach unten. Eine einspaltige Seite hat ein Band und eine Spalte, das Ergebnis ist dann
# die alte y-Reihenfolge (keine Regression). Geteilt von tei_step1 (Live-Generierung),
# tei_generator (Legacy) und tei_validator (Warnung W19, vergleicht die ausgelieferte
# Reihenfolge gegen diese kanonische).

WIDE_REGION_W_PCT = 60.0   # ab dieser Breite spannt ein Block die Textflaeche, ist keine Spalte
COLUMN_GAP_PCT = 12.0      # x-Mitten-Abstand, der einen Spaltensteg (Gutter) markiert


def _bbox_centre_x(bbox: dict) -> float:
    return bbox["x_pct"] + bbox["w_pct"] / 2.0


def reading_order_permutation(bboxes: list[dict]) -> list[int]:
    """Original-Indizes der bboxes in kanonischer Lesereihenfolge.

    bboxes: Liste von {x_pct, y_pct, w_pct, h_pct} in Seitenprozent (0-100). Gibt die
    Eingangs-Indizes so umgeordnet zurueck, dass vollbreite Bloecke die Seite in waagrechte
    Baender teilen und innerhalb eines Bands Spalte fuer Spalte (links nach rechts), je Spalte
    oben nach unten gelesen wird. Eine einspaltige Seite ergibt die reine oben-nach-unten-
    Ordnung, identisch zur frueheren y-Sortierung. Rein und deterministisch; bei Gleichstand
    bleibt die Eingangsreihenfolge erhalten (stabil), damit Aufrufer sowohl umordnen als auch
    pruefen koennen, ob eine bestehende Reihenfolge bereits kanonisch ist (Identitaet).
    """
    n = len(bboxes)
    if n <= 1:
        return list(range(n))

    wide = sorted(
        (i for i in range(n) if bboxes[i]["w_pct"] >= WIDE_REGION_W_PCT),
        key=lambda i: (bboxes[i]["y_pct"], i),
    )
    narrow = [i for i in range(n) if bboxes[i]["w_pct"] < WIDE_REGION_W_PCT]

    def columns_ordered(members: list[int]) -> list[int]:
        if not members:
            return []
        members = sorted(members, key=lambda i: (_bbox_centre_x(bboxes[i]), i))
        cols = [[members[0]]]
        for i in members[1:]:
            if _bbox_centre_x(bboxes[i]) - _bbox_centre_x(bboxes[cols[-1][-1]]) > COLUMN_GAP_PCT:
                cols.append([i])
            else:
                cols[-1].append(i)
        out: list[int] = []
        for col in cols:
            out.extend(sorted(col, key=lambda i: (bboxes[i]["y_pct"], i)))
        return out

    order: list[int] = []
    prev_top = float("-inf")
    for w in wide:
        wy = bboxes[w]["y_pct"]
        order.extend(columns_ordered([i for i in narrow if prev_top <= bboxes[i]["y_pct"] < wy]))
        order.append(w)
        prev_top = wy
    order.extend(columns_ordered([i for i in narrow if bboxes[i]["y_pct"] >= prev_top]))
    return order


def make_element(tag: str, tail: str = None, **attribs):
    """Erzeugt ein ET.Element mit optionalem tail und Attributen."""
    elem = ET.Element(tag)
    if tail is not None:
        elem.tail = tail
    for k, v in attribs.items():
        elem.set(k, v)
    return elem


def wrap_orphan_groups(container, is_orphan, make_wrapper) -> None:
    """Wickelt zusammenhaengende Orphan-Kinder eines Containers in Wrapper ein.

    Args:
        container: ET.Element mit Kindern
        is_orphan: Callable(child) -> bool, ob Kind eingewickelt werden soll
        make_wrapper: Callable() -> ET.Element, erzeugt den Wrapper
    """
    children = list(container)
    groups = []
    current_group = []
    current_start = None
    for i, child in enumerate(children):
        if is_orphan(child):
            if current_start is None:
                current_start = i
            current_group.append(child)
        else:
            if current_group:
                groups.append((current_start, current_group))
                current_group = []
                current_start = None
    if current_group:
        groups.append((current_start, current_group))

    for start_idx, elems in reversed(groups):
        wrapper = make_wrapper()
        for e in elems:
            container.remove(e)
            wrapper.append(e)
        container.insert(start_idx, wrapper)


# ---------------------------------------------------------------------------
# TEI-Zeichennormalisierung (Editionsrichtlinien ZBZ, E49)
# ---------------------------------------------------------------------------

# Normalisierungsregeln fuer den TEI-Output (NICHT fuer OCR-Evaluation!).
# Zielzeichen sind spezifische Unicode-Zeichen gemaess Richtlinien.
_TEI_NORMALIZE_MAP = {
    # Gedankenstriche -> Halbgeviertstrich (U+2013)
    '\u2014': '\u2013',  # Em-dash -> En-dash
    # Trennstriche -> Viertelgeviertstrich (U+2010)
    # (Hyphen-minus bleibt Hyphen-minus in normalem Text,
    #  wird nur bei expliziten Trennstellen zu U+2010)

    # Anfuehrungszeichen normalisieren
    '\u201E': '\u201C',  # „ -> " (untere dt. -> obere engl.)
    '\u00AB': '\u201C',  # « -> "
    '\u00BB': '\u201D',  # » -> "
    '\u2039': '\u2018',  # ‹ -> '
    '\u203A': '\u2019',  # › -> '

    # Apostrophe -> Right single quotation mark (U+2019)
    '\u0060': '\u2019',  # ` -> '
    '\u00B4': '\u2019',  # ´ -> '
    '\u2018': '\u2019',  # ' -> ' (left single -> right single for apostrophe)

    # Leerzeichen normalisieren
    '\u00A0': ' ',       # Non-breaking space
    '\u2009': ' ',       # Thin space
    '\u200A': ' ',       # Hair space
    '\u202F': ' ',       # Narrow no-break space
}


def normalize_for_tei(text: str) -> str:
    """Normalisiert Text gemaess Editionsrichtlinien ZBZ fuer TEI-Output.

    Wendet die verbindlichen Zeichennormalisierungen an:
    - Gedankenstriche -> Halbgeviertstrich (U+2013)
    - Anfuehrungszeichen -> typografische Form
    - Apostrophe -> U+2019
    - Leerzeichen vor Interpunktion loeschen
    """
    for old, new in _TEI_NORMALIZE_MAP.items():
        text = text.replace(old, new)

    # Leerzeichen vor : ; ? ! loeschen (franzoesische Typografie)
    text = re.sub(r' +([;:?!])', r'\1', text)

    return text


def parse_tei_fragment(xml: str):
    """Parst ein TEI-Fragment in einen ET-Root mit Namespace-Wrapper.

    Returns:
        root Element oder None bei ParseError.
    """
    wrapped = f'<root xmlns="{TEI_NS}">{xml}</root>'
    try:
        return ET.fromstring(wrapped)
    except ET.ParseError:
        return None


def serialize_tei_fragment(root) -> str:
    """Serialisiert einen ET-Root zurueck zu TEI-Fragment-String."""
    ET.register_namespace("", TEI_NS)
    result = ET.tostring(root, encoding="unicode")
    result = re.sub(r'^<root[^>]*>', '', result)
    result = re.sub(r'</root>$', '', result)
    result = result.replace("ns0:", "").replace(":ns0", "")
    return result
