"""
Shared XML Utilities fuer TEI-Pipeline.

Wird importiert von: tei_step2.py, tei_step3.py.
"""

import re
import xml.etree.ElementTree as ET

from scripts.config import TEI_NS


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
