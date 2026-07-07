"""Gemeinsame <pb>-Seitensegmentierung fuer assemblierte TEI-Dokumente.

Single Source of Truth fuer die Regel **"Seitenzahl = 1-basierte sequenzielle
Position des <pb>-Elements im <body>"** (NICHT das n-Attribut -- etliche Docs
tragen dort die originale Journal-Pagination, z. B. n="56"). Die Seitenzahl
muss zu den Bilddateinamen 1,2,3... passen.

Konsumenten:
  - scripts/edition/generate_edition_data.py  (Per-Seiten-Mirror-Splitter)
  - scripts/tei/tei_blank_marker.py            (Leerseiten-Marker)

Beide Konsumenten muessen PB_RE/BODY_INNER_RE und iter_page_spans() teilen; eine
eigene, abweichende Segmentierung wuerde Marker auf der falschen Seite platzieren
(stiller Off-by-Page-Bug).
"""

import re
from dataclasses import dataclass
from typing import List

# <pb ... /> oder <pb ...> -- verlangt ein Whitespace nach "pb" (schliesst z. B.
# <pba> aus). Identische Regex fuer beide Konsumenten.
PB_RE = re.compile(r"<pb\s[^>]*/?>")
# Innerer <body>-Inhalt (greedy DOTALL; ein body pro Dokument).
BODY_INNER_RE = re.compile(r"<body[^>]*>(.*?)</body>", re.DOTALL)


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


def iter_page_spans(body_inner: str) -> List[PageSpan]:
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
