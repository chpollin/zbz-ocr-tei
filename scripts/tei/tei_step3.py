"""
Step 3: Document Assembly.

Kombiniert Seiten-TEI-Fragmente zu komplettem TEI-Dokument.
Erzeugt teiHeader, facsimile, body und wendet Post-Assembly-Fixes an.

Wird aufgerufen von: tei_unified.py (Orchestrierung).
"""

import xml.etree.ElementTree as ET

from xml.sax.saxutils import escape as xml_escape

from scripts.config import TEI_NS
from scripts.tei.tei_xml_utils import make_element, wrap_orphan_groups


# ---------------------------------------------------------------------------
# teiHeader + facsimile
# ---------------------------------------------------------------------------

def build_tei_header(doc_id: str, metadata: dict) -> str:
    """Erzeugt teiHeader mit biblStruct aus Metadaten."""
    title = xml_escape(metadata.get("title") or doc_id)
    author = xml_escape(metadata.get("author") or "Jeanne Hersch")
    date = xml_escape(metadata.get("date") or "")
    desc = xml_escape(metadata.get("desc") or "")
    pub_form = metadata.get("pub_form", "other")

    lang = metadata.get("lang", "und")
    if len(lang) != 3 or not lang.isalpha():
        lang_map = {"FR": "fra", "DE": "deu", "DE/FR": "fra", "?": "und"}
        lang = lang_map.get(lang, "und")

    lines = []
    lines.append("  <teiHeader>")
    lines.append("    <fileDesc>")
    lines.append("      <titleStmt>")
    lines.append(f'        <title type="main">{title}</title>')
    lines.append(f"        <author>{author}</author>")
    lines.append("      </titleStmt>")
    lines.append("      <publicationStmt>")
    lines.append("        <publisher>ZBZ / DHCraft</publisher>")
    lines.append(f'        <idno type="docID">{doc_id}</idno>')
    lines.append("      </publicationStmt>")
    lines.append("      <sourceDesc>")

    # biblStruct statt einfacher bibl
    if pub_form in ("journalArticle", "bookSection"):
        lines.append(f'        <biblStruct type="{pub_form}">')
        lines.append("          <analytic>")
        lines.append(f'            <title>{title}</title>')
        lines.append(f"            <author>{author}</author>")
        lines.append("          </analytic>")
        lines.append("          <monogr>")
        lines.append("            <title/>")
        lines.append("            <imprint>")
        lines.append(f"              <date>{date or 'unknown'}</date>")
        lines.append("            </imprint>")
        lines.append("          </monogr>")
        lines.append("        </biblStruct>")
    else:
        lines.append("        <bibl>")
        lines.append(f"          <title>{title}</title>")
        lines.append(f"          <author>{author}</author>")
        if date:
            lines.append(f"          <date>{date}</date>")
        lines.append("        </bibl>")

    lines.append("      </sourceDesc>")
    lines.append("    </fileDesc>")
    lines.append("    <profileDesc>")
    lines.append("      <langUsage>")
    lines.append(f'        <language ident="{lang}"/>')
    lines.append("      </langUsage>")
    lines.append("    </profileDesc>")
    lines.append("  </teiHeader>")

    return "\n".join(lines)


def build_facsimile(page_facsimiles: dict[int, dict]) -> str:
    """Erzeugt <facsimile> Element aus gesammelten Seitendaten."""
    if not page_facsimiles:
        return ""

    lines = ["  <facsimile>"]
    for page_num in sorted(page_facsimiles.keys()):
        facs = page_facsimiles[page_num]
        if not facs or not facs.get("zones"):
            continue
        img_w = facs.get("image_width", 0)
        img_h = facs.get("image_height", 0)
        lines.append(
            f'    <surface xml:id="facs_{page_num}" ulx="0" uly="0" '
            f'lrx="{img_w}" lry="{img_h}">'
        )
        for z in facs["zones"]:
            lines.append(
                f'      <zone xml:id="{z["zone_id"]}" '
                f'ulx="{z["ulx"]}" uly="{z["uly"]}" '
                f'lrx="{z["lrx"]}" lry="{z["lry"]}"/>'
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

    # facsimile
    facs = build_facsimile(page_facsimiles)
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

    # Post-Assembly Fix: verwaiste <p>/<figure>/<note> direkt in <body>
    # (ausserhalb <div>) in <div type="text"> einwickeln
    result = _fix_orphaned_body_children(result)

    # Post-Assembly Fix: Schema-Verletzungen nach Assembly korrigieren
    result = _fix_post_assembly_schema(result)

    return result


# ---------------------------------------------------------------------------
# Post-Assembly Schema Fixes
# ---------------------------------------------------------------------------

def _fix_post_assembly_schema(xml_text: str) -> str:
    """Post-Assembly-Fixes fuer RelaxNG-Schema-Verletzungen.

    Fix A: <graphic> ohne url-Attribut -> url="unknown" hinzufuegen
    Fix B: <p> innerhalb <head> -> Inhalt entpacken (Text beibehalten)
    Fix C: <epigraph> nach Content in <div> -> Inhalt entpacken (divTop-Regel)
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

        # Fix C: <epigraph> nach Content in <div> -> entpacken
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

        return ET.tostring(tree, encoding="unicode", xml_declaration=True)
    except Exception:
        return xml_text


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
                      "table", "list", "ab", "bibl"}

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
