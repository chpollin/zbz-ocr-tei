"""ZBZ-Konformitaetspruefung: das Inline-GND-Auszeichnungsmodell (E88).

Ergaenzt den Schema- und Projektregel-Validator (`tei_validator.py`) um die Regeln
der ZBZ-Editionsrichtlinie, die ein RelaxNG nicht ausdruecken kann, weil sie an
Inhalt und Kontext haengen. Maßgebliche Referenz: die uebergebene ZBZ-README
(`data/source/zbz-lieferung-2026-06-21/README.md`, byte-identisch zum Arbeits-
exemplar `data/source/guidelines/Editionsrichtlinien_ZBZ.md`, E49).

Modell (E88, order Forschungsleitstelle 2026-06-21): Personen, Organisationen und
Werke werden **inline an der Erwaehnungsstelle** ausgezeichnet, jede Nennung mit
``ref="GND:..."``; kein standOff-Register, keine Orte/Events, keine GeoNames/Wikidata.

Schweregrade:
  - ``violation``  bricht das Liefermodell (z.B. fremde Normdatei, Register, Ort als Entitaet)
  - ``advisory``   editorialer Hinweis (z.B. Entitaet noch ohne GND-Verweis = Kurationsluecke)

Der ausgelieferte Bestand ist seit E71 entitaetenfrei; die entitaetsbezogenen Regeln
(Z1-Z4, Z8) greifen also erst auf kuratierten teiCrafter-Output. Z5 (Renderings) und
Z6 (``pb facs/n``) gelten auf dem realen Bestand. Datenvertrag exakt aus der README.

Bewusst nicht als Regel kodiert: "Entitaeten in Bildunterschriften werden nicht
ausgezeichnet" (README §Registereintraege). Die README widerspricht sich hier selbst,
ihr eigenes §Abbildungen-Beispiel zeichnet eine ``<orgName ref="GND:...">`` in einer
``<figure>`` aus. Als ZBZ-Rueckfrage offen (klaerung-zbz-ocr-tei.md), nicht maschinell
erzwungen.
"""

from __future__ import annotations

import re

TEI_NS = "http://www.tei-c.org/ns/1.0"
XML_ID = "{http://www.w3.org/XML/1998/namespace}id"

# ZBZ-README: Normdaten ausschliesslich GND; Schema-Pattern GND:[0-9A-Za-z\-]+
_GND_RE = re.compile(r"^GND:[0-9A-Za-z\-]+$")
# ZBZ-README §Renderings: zulaessige rendition-Werte
_RENDITION_OK = {"#b", "#i", "#u", "#g", "#sup", "#sub", "#k"}
# Normdaten-Typen, die die README ausschliesst (nur GND)
_FOREIGN_AUTHORITY = {"GeoNames", "Wikidata"}


def _q(tag: str) -> str:
    return f"{{{TEI_NS}}}{tag}"


def _local(el) -> str:
    return el.tag.rsplit("}", 1)[-1] if isinstance(el.tag, str) else ""


def _in_bibliography(el) -> bool:
    """True, wenn el in einem <div type="bibliography"> steht (README §Lexikonartikel:
    dort bewusst <bibl> ohne GND)."""
    parent = el.getparent()
    while parent is not None:
        if _local(parent) == "div" and parent.get("type") == "bibliography":
            return True
        parent = parent.getparent()
    return False


def check_conformity(root) -> list[dict]:
    """Prueft eine TEI-Wurzel gegen das ZBZ-Inline-GND-Modell.

    Returns:
        Liste von Findings ``{"rule", "severity", "message", "line"}``.
    """
    findings: list[dict] = []

    def add(rule, severity, el, message):
        findings.append({
            "rule": rule,
            "severity": severity,
            "line": (getattr(el, "sourceline", 0) or 0),
            "message": message,
        })

    # Z4: kein standOff-Register, keine generische <name ref>-Mention (Inline-GND, kein Register)
    for so in root.findall(f".//{_q('standOff')}"):
        add("Z4", "violation", so, "<standOff>-Register -- ZBZ verlangt Inline-GND, kein Register")
    for nm in root.findall(f".//{_q('name')}"):
        if nm.get("ref"):
            add("Z4", "violation", nm,
                f'<name ref="{nm.get("ref")}"> -- Inline-Mention statt persName/orgName/bibl')

    # Z2: fremde Normdatei (GeoNames/Wikidata) -- ZBZ erlaubt nur GND
    for idno in root.findall(f".//{_q('idno')}"):
        if idno.get("type") in _FOREIGN_AUTHORITY:
            add("Z2", "violation", idno,
                f'<idno type="{idno.get("type")}"> -- ZBZ-Normdaten ausschliesslich GND')

    # Z3: Ort/Event als Entitaet -- ZBZ zeichnet nur Person/Organisation/Werk aus
    for pn in root.findall(f".//{_q('placeName')}"):
        add("Z3", "violation", pn, "<placeName> -- ZBZ zeichnet keine Orte aus (nur Person/Org/Werk)")
    for ev in root.findall(f".//{_q('event')}"):
        add("Z3", "violation", ev, "<event> -- ZBZ zeichnet keine Ereignisse aus (nur Person/Org/Werk)")

    # Z1/Z8: Entitaets-Auszeichnung persName/orgName
    for tag in ("persName", "orgName"):
        for el in root.findall(f".//{_q(tag)}"):
            ref = el.get("ref")
            if ref is None:
                add("Z8", "advisory", el, f"<{tag}> ohne @ref (Entitaet noch nicht mit GND verknuepft)")
            elif not _GND_RE.match(ref):
                add("Z1", "violation", el, f'<{tag} ref="{ref}"> -- @ref entspricht nicht GND:...')

    # bibl: Werk-Entitaet mit GND, ausser in <div type="bibliography"> (dort bewusst ohne GND)
    for el in root.findall(f".//{_q('bibl')}"):
        ref = el.get("ref")
        if _in_bibliography(el):
            continue  # README §Lexikonartikel: Bibliographie-Eintraege ohne GND, korrekt
        if ref is not None and not _GND_RE.match(ref):
            add("Z1", "violation", el, f'<bibl ref="{ref}"> -- @ref entspricht nicht GND:...')

    # Z5: Rendering-Vokabular (README §Renderings)
    for hi in root.findall(f".//{_q('hi')}"):
        rend = hi.get("rendition")
        if rend is not None and rend not in _RENDITION_OK:
            add("Z5", "violation", hi,
                f'<hi rendition="{rend}"> -- nicht im ZBZ-Satz {{#b,#i,#u,#g,#sup,#sub,#k}}')

    # Z6: Seitenumbruch mit Faksimile-Verweis und Seitenzahl (README §Seitenumbrueche)
    for pb in root.findall(f".//{_q('pb')}"):
        if pb.get("facs") is None:
            add("Z6", "violation", pb, "<pb> ohne @facs -- Faksimile-Verweis fehlt")
        if pb.get("n") is None:
            add("Z6", "violation", pb, "<pb> ohne @n -- Seitenzahl fehlt")

    return findings


# ZBZ-Regel -> README-Abschnitt, fuer Report und Doku
RULE_LABELS = {
    "Z1": "Entitaets-@ref nicht GND (README §Registereintraege)",
    "Z2": "fremde Normdatei GeoNames/Wikidata (README §Registereintraege, §TEI-Header)",
    "Z3": "Ort/Event als Entitaet (README: nur Person/Org/Werk)",
    "Z4": "standOff-Register / <name ref> (README: Inline-GND, kein Register)",
    "Z5": "Rendering ausserhalb des ZBZ-Satzes (README §Renderings)",
    "Z6": "<pb> ohne @facs/@n (README §Seitenumbrueche)",
    "Z8": "Entitaet ohne GND-Verweis -- Kurationsluecke (advisory)",
}
