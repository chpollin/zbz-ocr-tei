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
