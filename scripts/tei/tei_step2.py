"""
Step 2: Gemini Refinement.

Verfeinert das regelbasierte TEI-Scaffold (Step 1) via Gemini API.
Wendet anschliessend Post-Processing-Fixes auf haeufige Gemini-Fehler an.

Wird aufgerufen von: tei_unified.py (Orchestrierung).
"""

import re
import xml.etree.ElementTree as ET
from pathlib import Path

from scripts.config import (
    GEMINI_MODEL,
    IMAGES_DIR,
    LAYOUT_DIR,
    TEI_NS,
)
from scripts.core.loaders import load_ocr_text
from scripts.tei.tei_mapping_prompt import (
    build_mapping_prompt,
    build_refinement_input,
)
from scripts.tei.tei_xml_utils import (
    make_element,
    parse_tei_fragment,
    serialize_tei_fragment,
    wrap_orphan_groups,
)


# ---------------------------------------------------------------------------
# Overlay-Pfad
# ---------------------------------------------------------------------------

def get_overlay_path(doc_id: str, page: int) -> Path | None:
    """Findet das Overlay-PNG fuer eine Seite."""
    padded = str(page).zfill(3)
    overlay = LAYOUT_DIR / doc_id / f"{doc_id}_p{padded}_overlay_gemini.png"
    if overlay.exists():
        return overlay
    overlay = LAYOUT_DIR / doc_id / f"{doc_id}_p{padded}_overlay.png"
    if overlay.exists():
        return overlay
    # Fallback: Scan-Bild
    scan = IMAGES_DIR / doc_id / f"{doc_id}_p{padded}.png"
    if scan.exists():
        return scan
    return None


# ---------------------------------------------------------------------------
# Entity Re-Annotation
# ---------------------------------------------------------------------------

def reannotate_entities(xml_text: str) -> str:
    """Tag-aware Entity Re-Annotation: taggt fehlende bekannte Entities.

    Findet Entitaetsnamen im Text die NICHT bereits innerhalb eines
    Entity-Tags stehen und fuegt typkorrekte Tags mit interner ID hinzu.
    Laengere Namen zuerst (wie annotate_entities).
    """
    from scripts.tei.tei_mapping_prompt import _load_entity_entries
    entries = _load_entity_entries()
    sorted_names = sorted(entries.keys(), key=len, reverse=True)

    # Regex fuer bestehende Entity-Tags (persName, orgName, placeName, bibl)
    entity_tag_re = re.compile(
        r'(<(?:persName|orgName|placeName|bibl)[^>]*>.*?</(?:persName|orgName|placeName|bibl)>)',
        flags=re.DOTALL,
    )

    for name in sorted_names:
        tei_tag, xml_id = entries[name]
        tag = f'<{tei_tag} ref="#{xml_id}">{name}</{tei_tag}>'
        # Split an bestehenden Entity-Tags, annotiere nur in Zwischenraeumen
        parts = entity_tag_re.split(xml_text)
        new_parts = []
        for i, part in enumerate(parts):
            if i % 2 == 0:
                # Text ausserhalb bestehender Entity-Tags -> annotieren
                pattern = r'(?<!\w)' + re.escape(name) + r'(?!\w)'
                part = re.sub(pattern, tag, part)
            new_parts.append(part)
        xml_text = "".join(new_parts)

    return xml_text


# ---------------------------------------------------------------------------
# Gemini TEI Fixes
# ---------------------------------------------------------------------------

def _fix_simple_patterns(xml: str) -> str:
    """Regex-basierte Fixes fuer haeufige Gemini-TEI-Fehler.

    Fix -1: <ab> mit <p> darin -> entferne <ab>-Wrapper
    Fix 0:  <head> innerhalb <speaker> -> entferne <head>-Tags
    Fix 1:  <head><p ...>...</p></head> -> <head ...>...</head>
    """
    # Fix -1: <ab> mit <p> darin -> entferne <ab>-Wrapper, behalte Inhalt
    def _unwrap_ab(m):
        inner = m.group(1)
        if "<p" in inner or "<p>" in inner:
            return inner
        return m.group(0)

    xml = re.sub(r'<ab[^>]*>(.*?)</ab>', _unwrap_ab, xml, flags=re.DOTALL)

    # Fix 0: <head> innerhalb <speaker> -> entferne <head>-Tags
    xml = re.sub(
        r'<speaker>\s*<head[^>]*>(.*?)</head>\s*</speaker>',
        lambda m: f'<speaker>{m.group(1)}</speaker>',
        xml, flags=re.DOTALL,
    )

    # Fix 1: <head><p ...>...</p></head> -> <head ...>...</head>
    def _fix_head_with_p(match):
        head_attrs = match.group(1) or ""
        p_attrs = match.group(2) or ""
        content = match.group(3)
        if "facs=" not in head_attrs and "facs=" in p_attrs:
            head_attrs = head_attrs.rstrip() + " " + p_attrs.strip()
        return f"<head{head_attrs}>{content}</head>"

    xml = re.sub(
        r'<head([^>]*)>\s*<p([^>]*)>(.*?)</p>\s*</head>',
        _fix_head_with_p, xml, flags=re.DOTALL,
    )

    return xml


def _fix_structural_issues(xml: str) -> str:
    """ET-basierte Fixes fuer Strukturprobleme in Gemini-TEI.

    Fix 2:  <head> nach Content -> <p>
    Fix 2b: <epigraph> nach Content -> entpacken
    Fix 3:  <sp> gemischt mit <p>/<figure>/<epigraph> -> split in sub-divs
    Fix 3b: Lose Inline-Elemente in <div> -> in <p> einwickeln
    """
    root = parse_tei_fragment(xml)
    if root is None:
        return xml

    # Fix 2 + 2b: <head>/<epigraph> nach Content
    for div in root.iter(f"{{{TEI_NS}}}div"):
        children = list(div)
        any_content = False
        for child in children:
            tag = child.tag.replace(f"{{{TEI_NS}}}", "")
            if tag == "head" and any_content:
                child.tag = f"{{{TEI_NS}}}p"
            elif tag == "epigraph" and any_content:
                idx = list(div).index(child)
                inner = list(child)
                div.remove(child)
                for j, ic in enumerate(inner):
                    div.insert(idx + j, ic)
            elif tag in ("pb",):
                pass
            else:
                any_content = True

    # Fix 3: <sp> gemischt mit <p>/<figure>/<epigraph> -> split into sub-divs
    for div in list(root.iter(f"{{{TEI_NS}}}div")):
        children = list(div)
        has_sp = any(c.tag == f"{{{TEI_NS}}}sp" for c in children)
        has_pre_sp_content = False
        if has_sp:
            for c in children:
                tag = c.tag.replace(f"{{{TEI_NS}}}", "")
                if tag == "sp":
                    break
                if tag in ("p", "figure", "epigraph"):
                    has_pre_sp_content = True

        if has_sp and has_pre_sp_content:
            pre_sp = []
            sp_and_after = []
            found_sp = False
            pb_elem = None
            for c in children:
                tag = c.tag.replace(f"{{{TEI_NS}}}", "")
                if tag == "sp":
                    found_sp = True
                if tag == "pb" and not found_sp:
                    pb_elem = c
                    continue
                if not found_sp:
                    pre_sp.append(c)
                else:
                    sp_and_after.append(c)

            div_type = div.get("type", "text")
            for c in children:
                div.remove(c)
            if pb_elem is not None:
                div.append(pb_elem)
            if pre_sp:
                intro_div = ET.SubElement(div, f"{{{TEI_NS}}}div")
                intro_div.set("type", "text")
                for c in pre_sp:
                    intro_div.append(c)
            if sp_and_after:
                sp_div = ET.SubElement(div, f"{{{TEI_NS}}}div")
                sp_div.set("type", div_type)
                for c in sp_and_after:
                    sp_div.append(c)
            if div.get("type"):
                div.set("n", "1")
                del div.attrib["type"]

    # Fix 3b: Lose Inline-Elemente direkt in <div> -> in <p> einwickeln
    inline_tags = {"lb", "persName", "orgName", "placeName", "hi",
                   "foreign", "ref", "date", "num"}
    for div in list(root.iter(f"{{{TEI_NS}}}div")):
        wrap_orphan_groups(
            div,
            is_orphan=lambda child: child.tag.replace(f"{{{TEI_NS}}}", "") in inline_tags,
            make_wrapper=lambda: make_element(f"{{{TEI_NS}}}p", tail="\n"),
        )

    return serialize_tei_fragment(root)


def fix_gemini_tei(xml_fragment: str) -> str:
    """Korrigiert haeufige Gemini-TEI-Fehler (Orchestrator).

    Pipeline: Regex-Fixes -> Struktur-Fixes -> Entity Re-Annotation.
    """
    xml_fragment = _fix_simple_patterns(xml_fragment)
    xml_fragment = _fix_structural_issues(xml_fragment)
    xml_fragment = reannotate_entities(xml_fragment)
    return xml_fragment


# ---------------------------------------------------------------------------
# Step 2: Gemini Refinement
# ---------------------------------------------------------------------------

def process_page_step2(
    client,
    doc_id: str,
    page: int,
    scaffold_xml: str,
    metadata: dict,
    genre: str | None,
    doc_hints: str,
    dry_run: bool = False,
) -> str:
    """Step 2: Gemini Refinement einer Seite.

    Args:
        client: google.genai Client
        scaffold_xml: TEI-Fragment aus Step 1
        metadata: Dokument-Metadaten
        genre: Inferiertes Genre
        doc_hints: Dokumenttypspezifische Hints
        dry_run: Nur Prompt anzeigen, kein API-Call

    Returns:
        Angereichertes TEI-Fragment
    """
    ocr_text = load_ocr_text(doc_id, page) or ""
    total_pages = metadata.get("page_count", "?") if metadata else "?"

    doc_context = {
        "doc_id": doc_id,
        "page_num": page,
        "total_pages": total_pages,
        "genre": genre,
        "pub_form": metadata.get("pub_form", "other") if metadata else "other",
        "main_lang": metadata.get("lang", "und") if metadata else "und",
        "layout_type": metadata.get("type", "A") if metadata else "A",
        "title": metadata.get("title", doc_id) if metadata else doc_id,
        "author": metadata.get("author", "Jeanne Hersch") if metadata else "Jeanne Hersch",
        "date": metadata.get("date", "?") if metadata else "?",
        "doc_hints": doc_hints,
    }

    prompt = build_mapping_prompt(doc_context)
    input_block = build_refinement_input(scaffold_xml, ocr_text)
    full_prompt = prompt + "\n\n" + input_block

    if dry_run:
        print(f"  [DRY-RUN] Prompt fuer {doc_id} p{page}: {len(full_prompt)} chars")
        return scaffold_xml

    # Overlay-Bild laden
    overlay_path = get_overlay_path(doc_id, page)

    try:
        from google import genai
        from google.genai import types

        contents = []

        # Bild hinzufuegen falls vorhanden
        if overlay_path and overlay_path.exists():
            img_bytes = overlay_path.read_bytes()
            mime = "image/png"
            contents.append(types.Part.from_bytes(data=img_bytes, mime_type=mime))

        contents.append(types.Part.from_text(text=full_prompt))

        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=contents,
            config=types.GenerateContentConfig(
                temperature=0.1,
                max_output_tokens=8192,
            ),
        )

        result_text = response.text.strip()

        # XML-Bloecke extrahieren falls in Markdown-Fences
        xml_match = re.search(r'```xml\s*(.*?)\s*```', result_text, re.DOTALL)
        if xml_match:
            result_text = xml_match.group(1)

        # Well-formedness pruefen
        ET.fromstring(f"<root>{result_text}</root>")

        # Post-Processing: haeufige Gemini-Fehler korrigieren
        result_text = fix_gemini_tei(result_text)

        return result_text

    except ImportError as e:
        print(f"  FEHLER: google-genai nicht installiert: {e}")
        return scaffold_xml
    except ET.ParseError as e:
        print(f"  WARNUNG: Gemini-XML nicht wohlgeformt fuer {doc_id} p{page}: {e}")
        return fix_gemini_tei(scaffold_xml)
    except Exception as e:
        err_str = str(e).lower()
        if "api_key" in err_str or "auth" in err_str or "permission" in err_str:
            print(f"  FEHLER: Gemini-Auth-Fehler fuer {doc_id} p{page}: {e}")
            raise
        print(f"  WARNUNG: Gemini-Fehler fuer {doc_id} p{page}: {e}")
        return scaffold_xml
