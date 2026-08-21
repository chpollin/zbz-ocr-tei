"""Gemeinsame <pb>-Seitensegmentierung fuer assemblierte TEI-Dokumente.

Single Source of Truth fuer die Regel **"Seitenzahl = 1-basierte sequenzielle
Position des <pb>-Elements im <body>"** (NICHT das n-Attribut -- etliche Docs
tragen dort die originale Journal-Pagination, z. B. n="56"). Die Seitenzahl
muss zu den Bilddateinamen 1,2,3... passen.

Konsumenten:
  - scripts/edition/generate_edition_data.py  (Per-Seiten-Mirror-Splitter)
  - scripts/tei/tei_blank_marker.py            (Leerseiten-Marker)
  - scripts/tei/tei_footnote_demote.py + tei_footnote_marker_strip.py
  - scripts/entity/generate_entity_preview_data.py

Beide Konsumenten muessen PB_RE/BODY_INNER_RE und iter_page_spans() teilen; eine
eigene, abweichende Segmentierung wuerde Marker auf der falschen Seite platzieren
(stiller Off-by-Page-Bug).
"""

import re
from dataclasses import dataclass
from pathlib import Path

# <pb ... /> oder <pb ...> -- verlangt ein Whitespace nach "pb" (schliesst z. B.
# <pba> aus). Identische Regex fuer beide Konsumenten.
PB_RE = re.compile(r"<pb\s[^>]*/?>")
# Innerer <body>-Inhalt (greedy DOTALL; ein body pro Dokument).
BODY_INNER_RE = re.compile(r"<body[^>]*>(.*?)</body>", re.DOTALL)
# Default-Namespace-Deklaration; die Seitenfragmente tragen ihren eigenen Envelope.
NS_RE = re.compile(r'\s+xmlns\s*=\s*"[^"]*"')
# Oeffnende/schliessende <div>-Tags (self-closing ausgenommen).
_DIV_TAG_RE = re.compile(r'<div\b[^>]*?(?<!/)>|</div\s*>')


@dataclass(frozen=True)
class PageSpan:
    """Eine Seite: ein <pb>-Tag plus folgender Inhalt bis zum naechsten <pb>.

    Alle Offsets beziehen sich auf den uebergebenen body_inner-String.
    """
    page: int           # 1-basierte sequenzielle Position
    pb_tag: str         # der gematchte <pb ...>-Tag (group(0))
    pb_start: int       # Offset des pb-Tags
    content_start: int  # Offset direkt nach dem pb-Tag
    content_end: int    # Offset des naechsten pb-Tags bzw. len(body_inner)


def iter_page_spans(body_inner: str) -> list[PageSpan]:
    """Seiten-Spans eines <body>-Inhalts in Dokumentreihenfolge.

    Gibt eine leere Liste zurueck, wenn kein <pb> vorhanden ist -- der
    'ganzes Dokument = eine Seite'-Fall wird vom Aufrufer behandelt (die beiden
    Konsumenten tun das unterschiedlich).
    """
    matches = list(PB_RE.finditer(body_inner))
    spans = []
    for i, m in enumerate(matches):
        nxt = matches[i + 1].start() if i + 1 < len(matches) else len(body_inner)
        spans.append(PageSpan(page=i + 1, pb_tag=m.group(0),
                              pb_start=m.start(), content_start=m.end(),
                              content_end=nxt))
    return spans


def _balance_divs(chunk: str) -> str:
    """Ergaenzt fehlende <div>-Klammern eines Seiten-Chunks.

    Ein Seiten-Chunk schneidet mitten durch die div-Hierarchie: er kann mit
    Schluss-Tags beginnen (Ende eines auf der Vorseite geoeffneten div) und mit
    offenen div enden. Erst nach dem Ausgleich beider Seiten ist das Fragment
    standalone wohlgeformt (core.js parst strikt als text/xml).
    """
    stack = 0
    leading_closes = 0
    for m in _DIV_TAG_RE.finditer(chunk):
        if m.group().startswith("</"):
            if stack > 0:
                stack -= 1
            else:
                leading_closes += 1
        else:
            stack += 1
    return ("<div>" * leading_closes) + chunk + ("</div>" * stack)


def _wrap_page(body_xml: str) -> str:
    """Umschliesst einen Seiten-Body mit minimalem TEI-Envelope."""
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<TEI xmlns="http://www.tei-c.org/ns/1.0">\n'
        '  <text>\n'
        f'    {body_xml}\n'
        '  </text>\n'
        '</TEI>\n'
    )


def extract_pages_from_final(final_path: Path) -> dict:
    """Splittet ein assembliertes TEI-Dokument in einzelne Seiten-Bodies.

    Seitenzahl = sequenzielle Position der <pb>-Elemente (1-basiert), NICHT
    das n-Attribut -- denn etliche Docs (z. B. 100) tragen die originale
    Journal-Pagination im n-Attribut (n="56"), wir brauchen aber 1,2,3...
    passend zu den Bilddateinamen.

    Returns: {page_number: xml_string} (mit minimalem TEI-Envelope).
    """
    try:
        raw = final_path.read_text(encoding="utf-8")
    except OSError:
        return {}

    clean = NS_RE.sub("", raw)

    # Body extrahieren
    body_match = BODY_INNER_RE.search(clean)
    if not body_match:
        return {}
    body_inner = body_match.group(1)

    spans = iter_page_spans(body_inner)
    if not spans:
        return {1: _wrap_page(f"<body>{body_inner}</body>")}

    pages = {}
    for span in spans:
        # Chunk inkl. pb-Tag (Seitenanfang) bis zum naechsten pb
        chunk = _balance_divs(body_inner[span.pb_start:span.content_end])
        pages[span.page] = _wrap_page(f"<body>{chunk}</body>")
    return pages
