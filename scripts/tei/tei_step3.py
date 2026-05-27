"""
Step 3: Document Assembly.

Kombiniert Seiten-TEI-Fragmente zu komplettem TEI-Dokument.
Erzeugt teiHeader, facsimile, body und wendet Post-Assembly-Fixes an.

Wird aufgerufen von: tei_unified.py (Orchestrierung).
"""

import re
import xml.etree.ElementTree as ET

from xml.sax.saxutils import escape as xml_escape

from scripts.config import TEI_NS
from scripts.tei.tei_xml_utils import make_element, wrap_orphan_groups


# ---------------------------------------------------------------------------
# Language Parsing
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# teiHeader + facsimile
# ---------------------------------------------------------------------------

# Sprach-Code-Normalisierung auf ISO-639-2/B 3-Letter. doc_metadata liefert
# meist schon 3-Letter (fra, deu), teils 2-Letter (fr/de) oder mehrsprachig (fra/deu).
_LANG_2TO3 = {"fr": "fra", "de": "deu", "en": "eng", "it": "ita"}


def _language_idents(lang_raw) -> list:
    """Zerlegt einen Sprach-String in normalisierte 3-Letter-Codes.

    'fra' -> ['fra']; 'fra/deu' -> ['fra', 'deu']; 'fr' -> ['fra'];
    '' / '?' / unbekannt -> ['und']. Reihenfolge erhalten, Duplikate raus.
    """
    if not lang_raw:
        return ["und"]
    out = []
    for tok in re.split(r"[\/,;\s]+", str(lang_raw).strip()):
        if not tok:
            continue
        t = tok.lower()
        if len(t) == 3 and t.isalpha():
            code = t
        else:
            code = _LANG_2TO3.get(t, "und")
        if code not in out:
            out.append(code)
    return out or ["und"]


def build_tei_header(doc_id: str, metadata: dict) -> str:
    """Erzeugt den teiHeader passend zum ausgelieferten Datenvertrag (E68-Schema).

    Erzeugt:
    - <idno type="docID"> im publicationStmt (+ <idno type="MMSID"> aus
      metadata["mmsid"], falls vorhanden -- Masterfile-Norm-ID, O8)
    - <biblStruct type={pub_form}> im sourceDesc mit <analytic> (title/author)
      + <monogr>/<imprint>/<date>
    - <profileDesc>/<langUsage> mit je einem <language ident=...> pro Sprachcode

    Das <revisionDesc> wird hier NICHT erzeugt -- tei_add_revision.py (Pipeline-Zeile)
    und tei_status_marker.py (Strom-Status, E66) projizieren es nachgelagert.

    Vorher liess diese Funktion idno/biblStruct/langUsage weg ("docID als Kommentar",
    "immer <bibl>"), war damit aermer als das ausgelieferte tei_final -- ein
    tei_unified-Neulauf regressierte jeden Header (verlor idno + biblStruct). Jetzt
    deckungsgleich mit dem Liefer-Vertrag.
    """
    title = xml_escape(metadata.get("title") or doc_id)
    author = xml_escape(metadata.get("author") or "Jeanne Hersch")
    date = xml_escape(metadata.get("date") or "")
    pub_form = xml_escape(metadata.get("pub_form") or "other")
    mmsid = metadata.get("mmsid")
    lang_idents = _language_idents(metadata.get("lang") or metadata.get("language"))

    lines = []
    lines.append("  <teiHeader>")
    lines.append("    <fileDesc>")
    lines.append("      <titleStmt>")
    lines.append(f'        <title type="main">{title}</title>')
    lines.append(f"        <author>{author}</author>")
    lines.append("      </titleStmt>")
    lines.append("      <publicationStmt>")
    lines.append("        <publisher>ZBZ / DHCraft</publisher>")
    lines.append(f'        <idno type="docID">{xml_escape(str(doc_id))}</idno>')
    if mmsid:
        lines.append(f'        <idno type="MMSID">{xml_escape(str(mmsid))}</idno>')
    lines.append("      </publicationStmt>")
    lines.append("      <sourceDesc>")
    lines.append(f'        <biblStruct type="{pub_form}">')
    lines.append("          <analytic>")
    lines.append(f"            <title>{title}</title>")
    lines.append(f"            <author>{author}</author>")
    lines.append("          </analytic>")
    lines.append("          <monogr>")
    lines.append("            <title />")
    if date:
        lines.append("            <imprint>")
        lines.append(f"              <date>{date}</date>")
        lines.append("            </imprint>")
    else:
        lines.append("            <imprint />")
    lines.append("          </monogr>")
    lines.append("        </biblStruct>")
    lines.append("      </sourceDesc>")
    lines.append("    </fileDesc>")
    lines.append("    <profileDesc>")
    lines.append("      <langUsage>")
    for ident in lang_idents:
        lines.append(f'        <language ident="{ident}" />')
    lines.append("      </langUsage>")
    lines.append("    </profileDesc>")
    lines.append("  </teiHeader>")

    return "\n".join(lines)


def build_facsimile(page_facsimiles: dict[int, dict], page_teis: dict[int, str] = None) -> str:
    """Erzeugt <facsimile> Element aus gesammelten Seitendaten.

    Erzeugt eine <surface> fuer jede Seite die im body vorkommt (via page_teis),
    auch wenn keine Layout-Zones vorhanden sind. So stimmen pb- und surface-Anzahl ueberein.
    """
    # Alle Seiten die eine surface brauchen (aus body-pages oder facsimile-keys)
    all_pages = set(page_facsimiles.keys())
    if page_teis:
        all_pages.update(page_teis.keys())

    if not all_pages:
        return ""

    lines = ["  <facsimile>"]
    for page_num in sorted(all_pages):
        facs = page_facsimiles.get(page_num)
        img_w = facs.get("image_width", 0) if facs else 0
        img_h = facs.get("image_height", 0) if facs else 0
        zones = facs.get("zones", []) if facs else []

        if zones:
            lines.append(
                f'    <surface xml:id="facs_{page_num}" ulx="0" uly="0" '
                f'lrx="{img_w}" lry="{img_h}">'
            )
            for z in zones:
                lines.append(
                    f'      <zone xml:id="{z["zone_id"]}" '
                    f'ulx="{z["ulx"]}" uly="{z["uly"]}" '
                    f'lrx="{z["lrx"]}" lry="{z["lry"]}"/>'
                )
            lines.append("    </surface>")
        else:
            # Leere surface mit graphic-Platzhalter (surface braucht min. 1 Kind)
            lines.append(
                f'    <surface xml:id="facs_{page_num}" ulx="0" uly="0" '
                f'lrx="{img_w}" lry="{img_h}">'
            )
            lines.append(
                f'      <graphic url="{page_num}.png"/>'
            )
            lines.append("    </surface>")

    lines.append("  </facsimile>")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Document Assembly
# ---------------------------------------------------------------------------

def assemble_document(
    doc_id: str,
    page_teis: dict[int, str],
    metadata: dict,
    page_facsimiles: dict[int, dict],
) -> str:
    """Step 3: Kombiniert Seiten-TEI-Fragmente zu komplettem Dokument."""
    lines = []
    lines.append('<?xml version="1.0" encoding="UTF-8"?>')
    lines.append('<TEI xmlns="http://www.tei-c.org/ns/1.0" type="naegeli">')

    # teiHeader
    lines.append(build_tei_header(doc_id, metadata))

    # facsimile (page_teis uebergeben fuer pb/surface-Synchronisation)
    facs = build_facsimile(page_facsimiles, page_teis)
    if facs:
        lines.append(facs)

    # text/body
    lines.append("  <text>")
    lines.append("    <body>")

    for page_num in sorted(page_teis.keys()):
        fragment = page_teis[page_num]
        if fragment.strip():
            lines.append(fragment)

    lines.append("    </body>")
    lines.append("  </text>")
    lines.append("</TEI>")

    result = "\n".join(lines)

    # Post-Assembly Fix: Seiten-divs zu Dokument-divs mergen
    genre = metadata.get("genre") or metadata.get("pub_form")
    result = _merge_page_divs(result, genre)

    # Post-Assembly Fix: verwaiste <p>/<figure>/<note> direkt in <body>
    # (ausserhalb <div>) in <div type="text"> einwickeln
    result = _fix_orphaned_body_children(result)

    # Post-Assembly Fix: Schema-Verletzungen nach Assembly korrigieren
    result = _fix_post_assembly_schema(result)

    # Post-Assembly Fix: Heuristische <lb/> fuer Absaetze ohne Zeilenumbrueche
    result = _inject_heuristic_lb(result)

    return result


# ---------------------------------------------------------------------------
# Post-Assembly: div-Merge (Seiten -> Dokument)
# ---------------------------------------------------------------------------

# Genre -> div type Mapping
_GENRE_TO_DIV_TYPE = {
    "review": "review",
    "interview": "interview",
    "speech": "speech",
    "conference": "conference",
    "letter": "letter",
    "editorial": "editorial",
    "preface": "preface",
    "debate": "conversation",
    "encyclopedia": "entry",
}


def _merge_page_divs(xml_text: str, genre: str = None) -> str:
    """Mergt aufeinanderfolgende Seiten-divs mit gleichem n zu einem Dokument-div.

    Step 1 erzeugt pro Seite ein <div n="1">. Dieses Post-Assembly-Fix
    fuegt aufeinanderfolgende divs mit gleichem n-Attribut zusammen, sodass
    ein Dokument typischerweise 1 top-level div hat (wie die ZBZ-Referenz-TEIs).

    Divs mit unterschiedlichem type werden NICHT gemergt (z.B. type="text" +
    type="interview" bleiben getrennt).
    """
    try:
        ET.register_namespace("", TEI_NS)
        root = ET.fromstring(xml_text)

        body = root.find(f".//{{{TEI_NS}}}body")
        if body is None:
            return xml_text

        children = list(body)
        div_tag = f"{{{TEI_NS}}}div"

        # Sammle Gruppen von aufeinanderfolgenden divs mit gleichem n + type
        groups = []
        current_group = []
        for child in children:
            if child.tag == div_tag:
                child_n = child.get("n", "")
                child_type = child.get("type", "")
                if current_group:
                    prev = current_group[-1]
                    prev_n = prev.get("n", "")
                    prev_type = prev.get("type", "")
                    if child_n == prev_n and child_type == prev_type:
                        current_group.append(child)
                    else:
                        groups.append(current_group)
                        current_group = [child]
                else:
                    current_group.append(child)
            else:
                if current_group:
                    groups.append(current_group)
                    current_group = []
                groups.append([child])
        if current_group:
            groups.append(current_group)

        # Merge: Jede Gruppe von divs mit gleichem n/type -> ein div
        body.clear()
        body.text = "\n"
        for group in groups:
            if len(group) == 1:
                body.append(group[0])
            elif group[0].tag == div_tag:
                # Merge: Alle Kinder der Folge-divs in den ersten div verschieben
                target = group[0]
                for source in group[1:]:
                    # Alle Kinder (pb, p, head, note, ...) verschieben
                    for child in list(source):
                        target.append(child)
                    # Tail-Text des source-div anhaengen
                    if source.tail and source.tail.strip():
                        last = list(target)[-1] if list(target) else None
                        if last is not None:
                            last.tail = (last.tail or "") + source.tail
                body.append(target)
            else:
                for item in group:
                    body.append(item)

        # Genre-type auf den aeussersten div setzen (wenn noch kein type)
        if genre:
            div_type = _GENRE_TO_DIV_TYPE.get(genre)
            if div_type:
                top_divs = body.findall(div_tag)
                for div in top_divs:
                    if not div.get("type"):
                        div.set("type", div_type)

        return ET.tostring(root, encoding="unicode", xml_declaration=True)
    except Exception:
        return xml_text


# ---------------------------------------------------------------------------
# Post-Assembly Schema Fixes
# ---------------------------------------------------------------------------

def _fix_post_assembly_schema(xml_text: str) -> str:
    """Post-Assembly-Fixes fuer RelaxNG-Schema-Verletzungen.

    Fix A:  <graphic> ohne url-Attribut -> url="unknown" hinzufuegen
    Fix B:  <p> innerhalb <head> -> Inhalt entpacken (Text beibehalten)
    Fix C:  <head> nach Content in <div> -> zu <p> konvertieren
    Fix D2: <figure> innerhalb <p> -> herausloesen
    Fix D:  <epigraph> nach Content in <div> -> entpacken
    Fix E:  Doppelte <pb> mit identischem facs -> Duplikat entfernen (W3)
    Fix F:  Leere <div> ohne Textinhalt -> entfernen (W4)
    Fix G:  <figure><graphic url='unknown'> ohne Content -> entfernen (W7)
    """
    try:
        ET.register_namespace("", TEI_NS)
        tree = ET.fromstring(xml_text)

        # Fix A: <graphic> ohne url -> url="unknown"
        for graphic in tree.iter(f"{{{TEI_NS}}}graphic"):
            if not graphic.get("url"):
                graphic.set("url", "unknown")

        # Fix B: <p> innerhalb <head> -> Inhalt als Text in <head>
        for head in list(tree.iter(f"{{{TEI_NS}}}head")):
            ps_in_head = head.findall(f"{{{TEI_NS}}}p")
            if not ps_in_head:
                continue
            for p in ps_in_head:
                # p-Inhalt (Text + Kinder) vor dem <p> einfuegen
                idx = list(head).index(p)
                p_text = p.text or ""
                p_children = list(p)
                # Text vor dem p anhaengen
                if idx == 0:
                    head.text = (head.text or "") + p_text
                else:
                    prev = list(head)[idx - 1]
                    prev.tail = (prev.tail or "") + p_text
                # Kinder des <p> nach oben verschieben
                for j, child in enumerate(p_children):
                    head.insert(idx + j, child)
                # Tail des <p> an letztes verschobenes Kind oder head.text
                p_tail = p.tail or ""
                if p_children:
                    last = p_children[-1]
                    last.tail = (last.tail or "") + p_tail
                elif idx == 0:
                    head.text = (head.text or "") + p_tail
                else:
                    prev = list(head)[idx - 1]
                    prev.tail = (prev.tail or "") + p_tail
                head.remove(p)

        # Fix C: <head> nach Content in <div> -> zu <p> konvertieren
        # TEI verlangt <head> nur am Anfang eines div (vor Content).
        # Nach dem div-Merge koennen Seiten-Headers mitten im div stehen.
        for div in list(tree.iter(f"{{{TEI_NS}}}div")):
            children = list(div)
            seen_content = False
            for child in children:
                tag = child.tag.replace(f"{{{TEI_NS}}}", "")
                if tag in ("pb",):
                    continue
                if tag == "head" and seen_content:
                    child.tag = f"{{{TEI_NS}}}p"
                elif tag != "head":
                    seen_content = True

        # Fix D2: <figure> innerhalb <p> -> herausloesen (Richtlinie: eigenstaendige Bloecke)
        for p in list(tree.iter(f"{{{TEI_NS}}}p")):
            figures_in_p = p.findall(f"{{{TEI_NS}}}figure")
            if not figures_in_p:
                continue
            parent = None
            for candidate in tree.iter():
                if p in list(candidate):
                    parent = candidate
                    break
            if parent is None:
                continue
            p_idx = list(parent).index(p)
            for fig in figures_in_p:
                p.remove(fig)
                p_idx += 1
                parent.insert(p_idx, fig)

        # Fix D: <epigraph> nach Content in <div> -> entpacken
        for div in list(tree.iter(f"{{{TEI_NS}}}div")):
            children = list(div)
            any_content = False
            for child in children:
                tag = child.tag.replace(f"{{{TEI_NS}}}", "")
                if tag == "epigraph" and any_content:
                    idx = list(div).index(child)
                    inner = list(child)
                    # Epigraph-Text an erstes Kind oder als eigenes <p>
                    epi_text = (child.text or "").strip()
                    div.remove(child)
                    for j, ic in enumerate(inner):
                        div.insert(idx + j, ic)
                elif tag not in ("pb", "head"):
                    any_content = True

        # Fix E: Doppelte <pb> mit identischem facs entfernen (W3)
        # Nur wenn es mehr pbs als surfaces gibt (Ueberschuss).
        body = tree.find(f".//{{{TEI_NS}}}body")
        if body is not None:
            pb_tag = f"{{{TEI_NS}}}pb"
            surface_tag = f"{{{TEI_NS}}}surface"
            n_surfaces = len(list(tree.iter(surface_tag)))
            all_pbs = list(body.iter(pb_tag))
            if len(all_pbs) > n_surfaces:
                seen_facs = set()
                for pb in all_pbs:
                    facs = pb.get("facs", "")
                    if facs in seen_facs:
                        parent = None
                        for candidate in tree.iter():
                            if pb in list(candidate):
                                parent = candidate
                                break
                        if parent is not None:
                            parent.remove(pb)
                    else:
                        seen_facs.add(facs)

        # Fix F: Leere <div> ohne Textinhalt entfernen (W4)
        for div in list(tree.iter(f"{{{TEI_NS}}}div")):
            text_content = "".join(div.itertext()).strip()
            if not text_content:
                parent = None
                for candidate in tree.iter():
                    if div in list(candidate):
                        parent = candidate
                        break
                if parent is not None:
                    parent.remove(div)

        # Fix G: <figure> mit nur <graphic url="unknown"> und ohne
        # sinnvollen Inhalt -> entfernen (W7)
        for figure in list(tree.iter(f"{{{TEI_NS}}}figure")):
            graphics = figure.findall(f"{{{TEI_NS}}}graphic")
            all_unknown = all(
                g.get("url", "") == "unknown" for g in graphics
            )
            # figure hat nur graphics mit unknown url und keinen Text
            fig_text = "".join(figure.itertext()).strip()
            if graphics and all_unknown and not fig_text:
                parent = None
                for candidate in tree.iter():
                    if figure in list(candidate):
                        parent = candidate
                        break
                if parent is not None:
                    parent.remove(figure)

        return ET.tostring(tree, encoding="unicode", xml_declaration=True)
    except Exception:
        return xml_text


# ---------------------------------------------------------------------------
# Post-Assembly: Heuristische <lb/> Injection
# ---------------------------------------------------------------------------

_AVG_LINE_CHARS = 60  # Durchschnittliche Zeilenlaenge historischer Druck


def _inject_heuristic_lb(xml_text: str) -> str:
    """Fuegt heuristische <lb/> in lange Absaetze ein, die keine haben.

    Greift NUR wenn ein <p> keinen einzigen <lb/> enthaelt und der
    Textinhalt laenger als _AVG_LINE_CHARS ist. Bestehende lb bleiben
    vollstaendig erhalten (Non-Regression).
    """
    try:
        ET.register_namespace("", TEI_NS)
        tree = ET.fromstring(xml_text)

        lb_tag = f"{{{TEI_NS}}}lb"
        p_tag = f"{{{TEI_NS}}}p"

        for p_elem in list(tree.iter(p_tag)):
            # Skip wenn bereits lb vorhanden
            if p_elem.find(lb_tag) is not None:
                continue

            # Gesamttext des Absatzes
            full_text = "".join(p_elem.itertext())
            if len(full_text) < _AVG_LINE_CHARS * 1.5:
                continue

            # lb-Positionen berechnen (alle ~60 Zeichen, an Wortgrenzen)
            _insert_lb_into_element(p_elem, lb_tag)

        return ET.tostring(tree, encoding="unicode", xml_declaration=True)
    except Exception:
        return xml_text


def _insert_lb_into_element(elem, lb_tag: str) -> None:
    """Fuegt <lb/> in ein Element ein, indem Textknoten an Wortgrenzen
    aufgespalten werden (~60 Zeichen pro Zeile)."""
    # Sammle alle Textknoten: elem.text + (child.tail fuer jedes Kind)
    # Wir muessen lb in die Textknoten einfuegen.

    # Strategie: elem.text aufteilen, dann jedes child.tail aufteilen
    lb_counter = [0]

    def _split_text(text):
        """Teilt Text an Wortgrenzen in Zeilen auf."""
        if not text or len(text) < _AVG_LINE_CHARS:
            return [text] if text else []
        parts = []
        pos = 0
        while pos < len(text):
            end = min(pos + _AVG_LINE_CHARS, len(text))
            if end < len(text):
                # Suche letztes Leerzeichen vor end
                space = text.rfind(" ", pos, end)
                if space > pos:
                    end = space + 1
            parts.append(text[pos:end])
            pos = end
        return parts

    def _make_lb():
        lb_counter[0] += 1
        lb = ET.Element(lb_tag)
        lb.set("n", f"N{lb_counter[0]:03d}")
        lb.tail = ""
        return lb

    # 1. elem.text aufteilen
    if elem.text and len(elem.text) >= _AVG_LINE_CHARS:
        parts = _split_text(elem.text)
        if len(parts) > 1:
            elem.text = parts[0]
            # Vor dem ersten Kind (oder am Ende) lb + Rest einfuegen
            insert_pos = 0
            for part in parts[1:]:
                lb = _make_lb()
                lb.tail = part
                elem.insert(insert_pos, lb)
                insert_pos += 1

    # 2. child.tail aufteilen
    children = list(elem)
    for i, child in enumerate(children):
        if child.tag == lb_tag:
            continue
        if child.tail and len(child.tail) >= _AVG_LINE_CHARS:
            parts = _split_text(child.tail)
            if len(parts) > 1:
                child.tail = parts[0]
                parent_children = list(elem)
                child_idx = parent_children.index(child)
                insert_pos = child_idx + 1
                for part in parts[1:]:
                    lb = _make_lb()
                    lb.tail = part
                    elem.insert(insert_pos, lb)
                    insert_pos += 1


def _fix_orphaned_body_children(xml_text: str) -> str:
    """Wickelt verwaiste Block-Elemente in <body> und <div> in Sub-<div> ein.

    TEI-Regel: wenn ein <div> oder <body> bereits <div>-Kinder hat,
    duerfen keine <p>/<figure>/<note>/<sp> etc. als Geschwister stehen.
    Diese werden in <div type='text'> eingewickelt.
    """
    try:
        ET.register_namespace("", TEI_NS)
        tree = ET.fromstring(xml_text)

        block_tags = {"p", "figure", "note", "sp", "epigraph", "lg",
                      "table", "list", "ab", "bibl", "head"}

        # Fix fuer body UND alle divs
        containers = [tree.find(f".//{{{TEI_NS}}}body")]
        containers.extend(tree.iter(f"{{{TEI_NS}}}div"))

        for container in containers:
            if container is None:
                continue
            children = list(container)

            has_div = any(c.tag == f"{{{TEI_NS}}}div" for c in children)
            has_blocks = any(
                c.tag.replace(f"{{{TEI_NS}}}", "") in block_tags
                for c in children
            )

            if not (has_div and has_blocks):
                continue

            def _make_text_div():
                div = make_element(f"{{{TEI_NS}}}div", tail="\n", type="text")
                div.text = "\n"
                return div

            wrap_orphan_groups(
                container,
                is_orphan=lambda c: c.tag.replace(f"{{{TEI_NS}}}", "") in block_tags,
                make_wrapper=_make_text_div,
            )

        return ET.tostring(tree, encoding="unicode", xml_declaration=True)
    except Exception:
        return xml_text
