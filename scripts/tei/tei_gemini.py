"""
Gemini Vision TEI Generator: Overlay-Bild + OCR + Layout -> TEI-XML.

Default: 1 Gemini-Call pro Seite -> komplettes TEI-Fragment (Struktur + Inline).
Optional: --refine (2. Call pro Seite) und --consolidate (Dokument-Level API-Call).

Usage:
    python -m scripts.tei.tei_gemini --doc 2310              # Ein Dokument (1 Call/Seite)
    python -m scripts.tei.tei_gemini --doc 2310 --evaluate    # Mit Referenz-Vergleich
    python -m scripts.tei.tei_gemini --sample                 # 3 Pilot-Docs
    python -m scripts.tei.tei_gemini --all                    # Alle 286 Docs
    python -m scripts.tei.tei_gemini --doc 2310 --refine      # + Anreicherungs-Pass
    python -m scripts.tei.tei_gemini --doc 2310 --consolidate # + Dokument-Konsolidierung
    python -m scripts.tei.tei_gemini --force                  # Cache ueberschreiben
    python -m scripts.tei.tei_gemini --dry-run                # Nur Prompts zeigen
"""

import argparse
import json
import os
import re
import sys
import time
import warnings
from pathlib import Path
from xml.etree import ElementTree as ET

warnings.filterwarnings("ignore", message=".*non-text parts.*thought_signature.*")

from dotenv import load_dotenv
from PIL import Image

from scripts.config import (
    DOC_METADATA_PATH, GEMINI_API_KEY, GEMINI_MODEL, IMAGES_DIR,
    KNOWN_ENTITIES, LAYOUT_DIR, REFERENZ_TEI_DIR, TEI_GEMINI_DIR,
)
from scripts.layout_qa_gemini import build_doc_hints, ensure_overlay, infer_genre
from scripts.tei.tei_generator import (
    get_document_metadata, load_layout, load_ocr_text,
)
from scripts.utils import discover_doc_ids, load_json, write_json

load_dotenv()
_api_key = os.environ.get("GEMINI_API_KEY", "") or GEMINI_API_KEY

# Sample-Docs: je ein Typ (A/Review, B/Artikel, D/Interview)
SAMPLE_DOC_IDS = ["2310", "2530", "1440"]

# ---- Referenz-TEI Snippets (Few-Shot) ----

REF_SNIPPET_REVIEW = """\
<div type="review">
  <pb facs="#facs_2" n="566"/>
  <head><bibl ref="GND:4343581-6"><lb facs="#facs_2_l_24" n="N001"/>Karl Jaspers, <hi rendition="#i">Philosophie</hi>,
    trad. de Jeanne Hersch, Paris, Ed. Springer-Verlag, 1986, 822 p.</bibl>
  </head>
  <p facs="#facs_2_r_2">
    <lb facs="#facs_2_l" n="N001"/><persName ref="GND:118557106">Karl Jaspers</persName> n'a pas encore
    vraiment trouve sa place en France. Il faut <lb facs="#facs_2_l_1" n="N002"
    />donc se feliciter que la traduction francaise du premier de ses deux
    principaux <lb facs="#facs_2_l_2" n="N003"/>ouvrages proprement philosophiques ait
    <lb facs="#facs_2_l_3" n="N004"/>ete enfin publiee.</p>
</div>"""

REF_SNIPPET_ARTICLE = """\
<div n="1">
  <pb facs="#facs_2" n="1788"/>
  <head><title type="main">
    <lb facs="#facs_2_l_1" n="N001"/>Die Demokratisierung
    <lb facs="#facs_2_l_2" n="N002"/>der Schule
  </title></head>
  <p facs="#facs_2_r_3">
    <lb facs="#facs_2_l_4" n="N001"/>Meine Damen und Herren, <lb facs="#facs_2_l_5"
    n="N002"/>Wir haben jetzt alle so dringende Probleme, dass <lb facs="#facs_2_l_7"
    n="N003"/>wir eigentlich sehr viel Zeit brauchen wuerden.
    <orgName ref="GND:1010450-1">Universitaet Genf</orgName>.</p>
</div>"""

REF_SNIPPET_INTERVIEW = """\
<div type="interview">
  <sp>
    <speaker><persName ref="GND:1145431410"/></speaker>
    <p facs="#facs_1_r_4">
      <lb facs="#facs_1_l_24" n="N001"/> Wird die Freiheit zum Luxus?
    </p>
  </sp>
  <sp>
    <speaker><persName ref="GND:118815679"/></speaker>
    <p facs="#facs_1_r_5">
      <lb facs="#facs_1_l_7" n="N001"/> Sie koennen doch nicht ernstlich eine
      solche Fra<lb facs="#facs_1_l_8" n="N002" break="no"/>ge stellen?!</p>
  </sp>
</div>"""

REF_SNIPPETS = {
    "review": REF_SNIPPET_REVIEW,
    "interview": REF_SNIPPET_INTERVIEW,
    "debate": REF_SNIPPET_INTERVIEW,
    "default": REF_SNIPPET_ARTICLE,
}

# ---- Gemini Client ----


def get_client():
    """Gemini Client erstellen."""
    from google import genai
    if not _api_key:
        print("FEHLER: GEMINI_API_KEY nicht gesetzt.")
        sys.exit(1)
    return genai.Client(api_key=_api_key)


# ---- Genre-Erkennung ----


def get_genre(doc_id):
    """Genre fuer ein Dokument bestimmen."""
    meta = _load_doc_meta(doc_id)
    if not meta:
        return "article"
    pub_form = meta.get("pub_form", "")
    desc = meta.get("description", "")
    genre = infer_genre(desc, pub_form)
    return genre or "article"


def _load_doc_meta(doc_id):
    """Metadata fuer ein Dokument laden."""
    if not DOC_METADATA_PATH.exists():
        return None
    raw = load_json(DOC_METADATA_PATH)
    if not raw:
        return None
    docs = raw.get("documents", raw)
    return docs.get(str(doc_id))


# ---- Single-Call Prompt (Default) ----

MAIN_PROMPT_TEMPLATE = """\
You are a TEI-XML encoder for the Jeanne Hersch Edition (ZBZ Zurich).
Convert this scanned page into COMPLETE TEI-XML body content following DTA-Basisformat.

IMAGE: Shows the scanned page with colored layout overlay (bounding boxes).

DOCUMENT CONTEXT:
- Doc: {doc_id}, Page {page_num} of {total_pages}
- Title: {title}
- Author: {author}
- Language: {language}
- Date: {date}
- Publication form: {pub_form}
{doc_hints}

STRUCTURAL RULES:
1. Use <div n="1"> for main section, <div n="2"> for sub-sections
2. For reviews: use <div type="review">
3. For interviews: use <div type="interview"> with <sp><speaker>Name</speaker><p>text</p></sp>
4. <pb facs="#facs_{{page}}" n="{{page_num}}"/> goes INSIDE <div>, at the start
5. <head> for headings, with <title type="main"> if it's the document title
6. <p facs="#facs_{{page}}_r_{{N}}"> for paragraphs, linked to layout regions
7. <note place="foot" n="..." xml:id="fn{{page}}-{{N}}"> for footnotes
8. <figure> for images/captions
9. FILTER OUT: page headers, page footers, running headers (zbz_tag = _filter)

INLINE MARKUP RULES:
10. <lb facs="#facs_{{page}}_l_{{N}}" n="N001"/> for LINE BREAKS -- look at the image to see where lines break.
    Reset numbering (N001, N002, ...) within each <p>, <head>, or <note>.
11. <lb ... break="no"/> for HYPHENATION (word split across lines, remove the hyphen).
12. <hi rendition="#i"> for ITALIC text (verify from image -- italic is slanted).
13. <hi rendition="#b"> for BOLD text (verify from image).
14. <persName ref="GND:..."> for PERSONS. Known entities:
{known_entities}
    For unknown persons use ref="GND:unknown".
15. <orgName ref="GND:..."> for ORGANIZATIONS (ref="GND:unknown" if unknown).
16. <bibl corresp="GND:..."> for WORK REFERENCES in review headings.
17. <foreign xml:lang="deu/fra/eng/ita/lat"> for LANGUAGE SWITCHES (main language: {main_lang}).
18. <choice><sic>wrong</sic><corr>correct</corr></choice> for obvious PRINT/OCR ERRORS.

LAYOUT REGIONS (JSON):
{layout_json}

OCR TEXT (Markdown):
{ocr_text}

{prev_context}

REFERENCE EXAMPLE:
{ref_snippet}

OUTPUT RULES:
- Output ONLY the TEI <body> content for this page (no teiHeader, no <?xml?>)
- Start with <pb .../> then structural elements
- Region IDs in facs attributes must match the layout region order (r_1, r_2, ...)
- Must be well-formed XML
- Do NOT invent text. Use the OCR text exactly as provided."""


def build_main_prompt(doc_id, page_num, total_pages, ocr_text, layout, prev_context=""):
    """Haupt-Prompt zusammenbauen (Single-Call)."""
    meta = get_document_metadata(str(doc_id)) or {}
    doc_hints = build_doc_hints(doc_id)

    # Layout-Regionen als JSON (nur relevante Felder)
    regions = layout.get("regions", []) if layout else []
    layout_summary = []
    for i, r in enumerate(regions):
        layout_summary.append({
            "id": i + 1,
            "label": r.get("label", "text"),
            "zbz_tag": r.get("zbz_tag", "zb_paragraph"),
            "text_preview": (r.get("text", "") or "")[:80],
            "bbox": r.get("bbox"),
        })
    layout_json = json.dumps(layout_summary, indent=2, ensure_ascii=False)

    # Genre -> Referenz-Snippet
    genre = get_genre(doc_id)
    ref_snippet = REF_SNIPPETS.get(genre, REF_SNIPPETS["default"])

    # Known entities als kompakten String
    entities_str = "\n".join(
        f"    {name}: {gnd}" for name, gnd in sorted(KNOWN_ENTITIES.items())
    )

    # Sprache
    main_lang = meta.get("lang", "und")

    prev_ctx = ""
    if prev_context:
        prev_ctx = f"PREVIOUS PAGE CONTEXT (last paragraph):\n{prev_context[:300]}"

    return MAIN_PROMPT_TEMPLATE.format(
        doc_id=doc_id,
        page_num=page_num,
        total_pages=total_pages,
        title=meta.get("title") or doc_id,
        author=meta.get("author") or "Jeanne Hersch",
        language=meta.get("lang", "und"),
        date=meta.get("date") or "unknown",
        pub_form=meta.get("pub_form", "other"),
        doc_hints=doc_hints,
        layout_json=layout_json,
        ocr_text=ocr_text[:4000],
        prev_context=prev_ctx,
        ref_snippet=ref_snippet,
        known_entities=entities_str,
        main_lang=main_lang,
    )


def process_page(client, doc_id, page_num, total_pages, overlay_img,
                 ocr_text, layout, prev_context="", force=False, dry_run=False):
    """Hauptverarbeitung: 1 Gemini-Call pro Seite -> komplettes TEI-Fragment."""
    padded = str(page_num).zfill(3)
    out_dir = TEI_GEMINI_DIR / str(doc_id)
    out_path = out_dir / f"{doc_id}_p{padded}.xml"

    if out_path.exists() and not force:
        print(f"  SKIP: {out_path.name}")
        return out_path.read_text(encoding="utf-8")

    prompt = build_main_prompt(doc_id, page_num, total_pages, ocr_text, layout, prev_context)

    if dry_run:
        print(f"\n{'='*40} Doc {doc_id} Page {page_num} {'='*40}")
        print(prompt[:2000])
        print("...")
        return None

    image = Image.open(overlay_img)

    t0 = time.time()
    try:
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=[image, prompt],
        )
        elapsed = time.time() - t0
        result_xml = response.text.strip()
    except Exception as e:
        elapsed = time.time() - t0
        print(f"  FEHLER: {doc_id}_p{padded}: {e} ({elapsed:.1f}s)")
        return None

    # XML-Codeblock entfernen falls vorhanden
    result_xml = re.sub(r'^```xml\s*', '', result_xml)
    result_xml = re.sub(r'\s*```$', '', result_xml)

    # XML-Validierung
    try:
        ET.fromstring(f"<root>{result_xml}</root>")
    except ET.ParseError as e:
        print(f"  WARN: XML nicht valide fuer {doc_id}_p{padded}: {e}")

    out_dir.mkdir(parents=True, exist_ok=True)
    out_path.write_text(result_xml, encoding="utf-8")
    print(f"  OK: {out_path.name} ({elapsed:.1f}s, {len(result_xml)} chars)")
    return result_xml


# ---- Optional: Refine-Pass (2. Call) ----

REFINE_PROMPT_TEMPLATE = """\
You are a TEI-XML quality reviewer for the Jeanne Hersch Edition (DTA-Basisformat).
Review and improve this TEI page fragment. Fix any issues.

PAGE IMAGE: [overlay image attached -- verify line breaks, formatting, entities]

CURRENT TEI:
{current_tei}

CHECK AND FIX:
1. Line breaks (<lb/>): verify against image. Every visible line break needs an <lb/>.
2. Hyphenation: verify <lb break="no"/> where words split across lines.
3. Italic/Bold: verify <hi rendition="#i/#b"> against image.
4. Entities: tag ALL person/organization mentions (even repeated ones).
   Known: {known_entities_short}
5. Language switches: <foreign xml:lang="..."> for non-{main_lang} passages.
6. Structure: correct div/p/head/note hierarchy.

RULES:
- PRESERVE the text content exactly
- Fix markup errors, add missing markup
- Must produce well-formed XML
- Output the corrected TEI fragment only (no code fences)

REFERENCE:
{ref_snippet}"""


def process_page_refine(client, doc_id, page_num, overlay_img, current_tei,
                        force=False, dry_run=False):
    """Optionaler Refine-Pass: 2. Call fuer Qualitaetsverbesserung."""
    padded = str(page_num).zfill(3)
    out_dir = TEI_GEMINI_DIR / str(doc_id)
    out_path = out_dir / f"{doc_id}_p{padded}_refined.xml"

    if out_path.exists() and not force:
        print(f"  SKIP refine: {out_path.name}")
        return out_path.read_text(encoding="utf-8")

    meta = get_document_metadata(str(doc_id)) or {}
    main_lang = meta.get("lang", "und")
    genre = get_genre(doc_id)
    ref_snippet = REF_SNIPPETS.get(genre, REF_SNIPPETS["default"])

    entities_short = ", ".join(f"{n}={g}" for n, g in list(KNOWN_ENTITIES.items())[:10])

    prompt = REFINE_PROMPT_TEMPLATE.format(
        current_tei=current_tei[:6000],
        known_entities_short=entities_short,
        main_lang=main_lang,
        ref_snippet=ref_snippet,
    )

    if dry_run:
        print(f"\n{'='*40} REFINE Doc {doc_id} Page {page_num} {'='*40}")
        print(prompt[:1500])
        return None

    image = Image.open(overlay_img)

    t0 = time.time()
    try:
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=[image, prompt],
        )
        elapsed = time.time() - t0
        result_xml = response.text.strip()
    except Exception as e:
        elapsed = time.time() - t0
        print(f"  FEHLER refine: {doc_id}_p{padded}: {e} ({elapsed:.1f}s)")
        return None

    result_xml = re.sub(r'^```xml\s*', '', result_xml)
    result_xml = re.sub(r'\s*```$', '', result_xml)

    try:
        ET.fromstring(f"<root>{result_xml}</root>")
    except ET.ParseError as e:
        print(f"  WARN refine: XML nicht valide fuer {doc_id}_p{padded}: {e}")

    out_dir.mkdir(parents=True, exist_ok=True)
    out_path.write_text(result_xml, encoding="utf-8")
    print(f"  OK refine: {out_path.name} ({elapsed:.1f}s, {len(result_xml)} chars)")
    return result_xml


# ---- Optional: Consolidate-Pass (Dokument-Level) ----

CONSOLIDATE_PROMPT_TEMPLATE = """\
You are a TEI-XML validator for the Jeanne Hersch Edition (DTA-Basisformat).
Consolidate these per-page TEI fragments into a complete, valid TEI document.

DOCUMENT METADATA:
- Doc ID: {doc_id}
- Title: {title}
- Author: {author}
- Language: {language} (ISO 639-3)
- Date: {date}
- Publication form: {pub_form}

PER-PAGE TEI FRAGMENTS:
{page_teis}

CONSOLIDATION TASKS:
1. Wrap in complete TEI document: <?xml?>, <TEI type="naegeli">, <teiHeader>, <text>/<body>
2. teiHeader: <titleStmt> with title and author, <publicationStmt> publisher="ZBZ / DHCraft",
   <sourceDesc> with date and description, <profileDesc> with <langUsage>/<language ident="..."/>
3. Multi-page footnotes: if a <note> ends mid-sentence on the next page,
   link with @xml:id, @next, @prev
4. Cross-page hyphenation: ensure <lb break="no"/> at page boundaries
5. Entity consistency: if a person is tagged once, ensure ALL mentions are tagged
6. Merge page fragments into continuous <div> structure (remove duplicate div wrappers)
7. <pb/> must be inside <div>, not between divs

OUTPUT: Complete, valid TEI-XML document. Must parse as well-formed XML.
Do NOT add any text outside the XML. Do NOT use ```xml code fences."""


def assemble_document(doc_id, page_teis):
    """Lokales Zusammenbauen ohne API-Call: teiHeader + Seiten-TEIs."""
    meta = get_document_metadata(str(doc_id)) or {}
    title = meta.get("title") or doc_id
    author = meta.get("author") or "Jeanne Hersch"
    lang = meta.get("lang", "und")
    date = meta.get("date") or "unknown"

    # Sprach-Mapping
    if len(lang) == 2:
        lang_map = {"FR": "fra", "DE": "deu", "EN": "eng"}
        lang = lang_map.get(lang.upper(), "und")

    # Seiten zusammenfuegen
    body_content = ""
    for page_num in sorted(page_teis.keys()):
        body_content += f"\n{page_teis[page_num]}\n"

    tei = f"""<?xml version='1.0' encoding='UTF-8'?>
<TEI xmlns='http://www.tei-c.org/ns/1.0' type="naegeli">
  <teiHeader>
    <fileDesc>
      <titleStmt>
        <title type='main'>{title}</title>
        <author>{author}</author>
      </titleStmt>
      <publicationStmt>
        <publisher>ZBZ / DHCraft</publisher>
      </publicationStmt>
      <sourceDesc>
        <bibl>
          <date>{date}</date>
        </bibl>
      </sourceDesc>
    </fileDesc>
    <profileDesc>
      <langUsage>
        <language ident="{lang}"/>
      </langUsage>
    </profileDesc>
  </teiHeader>
  <text>
    <body>
{body_content}
    </body>
  </text>
</TEI>"""

    out_dir = TEI_GEMINI_DIR / str(doc_id)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{doc_id}_final.xml"
    out_path.write_text(tei, encoding="utf-8")
    print(f"  Assembled: {out_path.name} ({len(tei)} chars)")
    return tei


def consolidate_document(client, doc_id, page_teis, force=False, dry_run=False):
    """Optionaler Consolidate-Pass: API-Call fuer Dokument-Level Konsolidierung."""
    out_dir = TEI_GEMINI_DIR / str(doc_id)
    out_path = out_dir / f"{doc_id}_final.xml"

    if out_path.exists() and not force:
        print(f"  SKIP consolidate: {out_path.name}")
        return out_path.read_text(encoding="utf-8")

    meta = get_document_metadata(str(doc_id)) or {}
    lang_raw = meta.get("lang", "und")
    if len(lang_raw) == 2:
        lang_map = {"FR": "fra", "DE": "deu", "EN": "eng"}
        lang_raw = lang_map.get(lang_raw.upper(), "und")

    pages_text = ""
    for page_num, tei in sorted(page_teis.items()):
        pages_text += f"\n<!-- PAGE {page_num} -->\n{tei}\n"

    prompt = CONSOLIDATE_PROMPT_TEMPLATE.format(
        doc_id=doc_id,
        title=meta.get("title") or doc_id,
        author=meta.get("author") or "Jeanne Hersch",
        language=lang_raw,
        date=meta.get("date") or "unknown",
        pub_form=meta.get("pub_form", "other"),
        page_teis=pages_text[:12000],
    )

    if dry_run:
        print(f"\n{'='*40} CONSOLIDATE Doc {doc_id} {'='*40}")
        print(prompt[:2000])
        return None

    t0 = time.time()
    try:
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=[prompt],
        )
        elapsed = time.time() - t0
        result_xml = response.text.strip()
    except Exception as e:
        elapsed = time.time() - t0
        print(f"  FEHLER consolidate: {doc_id}: {e} ({elapsed:.1f}s)")
        return None

    result_xml = re.sub(r'^```xml\s*', '', result_xml)
    result_xml = re.sub(r'\s*```$', '', result_xml)

    valid = True
    try:
        ET.fromstring(result_xml)
    except ET.ParseError as e:
        print(f"  WARN consolidate: XML nicht valide fuer {doc_id}: {e}")
        valid = False

    out_dir.mkdir(parents=True, exist_ok=True)
    out_path.write_text(result_xml, encoding="utf-8")
    status = "OK" if valid else "WARN (invalid XML)"
    print(f"  {status} consolidate: {out_path.name} ({elapsed:.1f}s, {len(result_xml)} chars)")
    return result_xml


# ---- Evaluation ----


def evaluate_against_reference(doc_id, generated_tei):
    """Vergleicht generiertes TEI mit Referenz-TEI."""
    ref_path = REFERENZ_TEI_DIR / f"{doc_id}.xml"
    if not ref_path.exists():
        print(f"  Keine Referenz-TEI fuer Doc {doc_id}")
        return None

    ref_tei = ref_path.read_text(encoding="utf-8")

    def extract_text(xml_str):
        try:
            xml_str = re.sub(r'\sxmlns=["\'][^"\']*["\']', '', xml_str)
            root = ET.fromstring(xml_str)
            return " ".join(root.itertext()).strip()
        except ET.ParseError:
            return ""

    ref_text = extract_text(ref_tei)
    gen_text = extract_text(generated_tei)

    if not ref_text:
        return None

    def count_elements(xml_str):
        counts = {}
        for tag in ["persName", "orgName", "bibl", "note", "hi", "foreign",
                     "choice", "lb", "div", "head", "sp", "speaker"]:
            counts[tag] = len(re.findall(f"<{tag}[\\s/>]", xml_str))
        return counts

    ref_counts = count_elements(ref_tei)
    gen_counts = count_elements(generated_tei)

    eval_result = {
        "doc_id": doc_id,
        "ref_text_length": len(ref_text),
        "gen_text_length": len(gen_text),
        "ref_element_counts": ref_counts,
        "gen_element_counts": gen_counts,
        "element_comparison": {},
    }

    for tag in ref_counts:
        ref_c = ref_counts[tag]
        gen_c = gen_counts[tag]
        if ref_c > 0:
            recall = min(gen_c / ref_c, 1.0)
        else:
            recall = 1.0 if gen_c == 0 else 0.0
        eval_result["element_comparison"][tag] = {
            "reference": ref_c,
            "generated": gen_c,
            "recall": round(recall, 3),
        }

    eval_path = TEI_GEMINI_DIR / str(doc_id) / f"{doc_id}_eval.json"
    write_json(eval_path, eval_result)

    print(f"\n  Evaluation Doc {doc_id}:")
    print(f"    Text: Ref {len(ref_text)} chars, Gen {len(gen_text)} chars")
    for tag, comp in eval_result["element_comparison"].items():
        if comp["reference"] > 0 or comp["generated"] > 0:
            print(f"    <{tag}>: Ref={comp['reference']}, Gen={comp['generated']}, Recall={comp['recall']}")

    return eval_result


# ---- Dokument-Orchestrierung ----


def discover_pages(doc_id):
    """Findet alle Seiten eines Dokuments (aus OCR-Dateien)."""
    pages = set()
    from scripts.config import (
        GEMINI_CORRECTED_A_DIR, GEMINI_CORRECTED_B_DIR,
        LLM_CORRECTED_C_DIR, MISTRAL_RESULTS_DIR,
    )
    for base_dir in [GEMINI_CORRECTED_B_DIR, GEMINI_CORRECTED_A_DIR,
                     LLM_CORRECTED_C_DIR, MISTRAL_RESULTS_DIR]:
        if base_dir.exists():
            for f in base_dir.glob(f"{doc_id}_p*.md"):
                match = re.search(r'_p(\d+)\.md$', f.name)
                if match:
                    pages.add(int(match.group(1)))
    return sorted(pages)


def process_document(client, doc_id, force=False, refine=False,
                     consolidate=False, evaluate=False, dry_run=False):
    """Verarbeitung eines Dokuments."""
    pages = discover_pages(doc_id)
    if not pages:
        print(f"  Keine OCR-Daten fuer Doc {doc_id}")
        return None

    total_pages = len(pages)
    genre = get_genre(doc_id)
    meta = get_document_metadata(str(doc_id)) or {}

    print(f"\n{'='*60}")
    print(f"Gemini TEI fuer Doc {doc_id}: {total_pages} Seiten, Genre={genre}")
    print(f"  Title: {meta.get('title', '?')}")
    print(f"  Lang: {meta.get('lang', '?')}, Type: {meta.get('type', '?')}, Form: {meta.get('pub_form', '?')}")
    mode_str = "1 Call/Seite"
    if refine:
        mode_str += " + Refine"
    if consolidate:
        mode_str += " + Consolidate"
    print(f"  Mode: {mode_str}")

    t0_doc = time.time()
    page_teis = {}
    prev_context = ""

    # ---- Hauptverarbeitung: 1 Call pro Seite ----
    print(f"\n  --- TEI Generation ({total_pages} Seiten) ---")
    for page_num in pages:
        padded = str(page_num).zfill(3)

        ocr_text = load_ocr_text(str(doc_id), page_num)
        if not ocr_text:
            print(f"  SKIP: Kein OCR fuer p{padded}")
            continue

        layout = load_layout(str(doc_id), page_num)

        overlay_path = ensure_overlay(str(doc_id), padded)
        if not overlay_path:
            overlay_path = IMAGES_DIR / str(doc_id) / f"{doc_id}_p{padded}.png"
            if not overlay_path.exists():
                print(f"  SKIP: Kein Bild fuer p{padded}")
                continue

        result = process_page(
            client, doc_id, page_num, total_pages,
            overlay_path, ocr_text, layout, prev_context,
            force=force, dry_run=dry_run,
        )
        if result:
            page_teis[page_num] = result
            last_p = re.findall(r'<p[^>]*>([^<]+)', result)
            prev_context = last_p[-1][:200] if last_p else ""

    # ---- Optional: Refine (2. Call pro Seite) ----
    if refine and page_teis:
        print(f"\n  --- Refine ({len(page_teis)} Seiten) ---")
        for page_num, current_tei in sorted(page_teis.items()):
            padded = str(page_num).zfill(3)

            overlay_path = ensure_overlay(str(doc_id), padded)
            if not overlay_path:
                overlay_path = IMAGES_DIR / str(doc_id) / f"{doc_id}_p{padded}.png"
                if not overlay_path.exists():
                    continue

            refined = process_page_refine(
                client, doc_id, page_num, overlay_path, current_tei,
                force=force, dry_run=dry_run,
            )
            if refined:
                page_teis[page_num] = refined

    # ---- Dokument zusammenbauen ----
    final_tei = None
    if page_teis and not dry_run:
        if consolidate:
            print(f"\n  --- Consolidate (API-Call) ---")
            final_tei = consolidate_document(
                client, doc_id, page_teis,
                force=force, dry_run=dry_run,
            )
        else:
            final_tei = assemble_document(doc_id, page_teis)

    # ---- Manifest ----
    elapsed_doc = time.time() - t0_doc
    manifest = {
        "doc_id": doc_id,
        "genre": genre,
        "total_pages": total_pages,
        "pages_processed": len(page_teis),
        "refine": refine,
        "consolidate": consolidate,
        "has_final": final_tei is not None,
        "elapsed_seconds": round(elapsed_doc, 1),
        "model": GEMINI_MODEL,
    }
    manifest_path = TEI_GEMINI_DIR / str(doc_id) / f"{doc_id}_manifest.json"
    if not dry_run:
        write_json(manifest_path, manifest)

    print(f"\n  Fertig: Doc {doc_id} ({elapsed_doc:.1f}s)")

    # ---- Evaluation ----
    if evaluate and final_tei:
        evaluate_against_reference(doc_id, final_tei)

    return manifest


# ---- CLI ----


def main():
    parser = argparse.ArgumentParser(description="Gemini Vision TEI Generator")
    parser.add_argument("--doc", type=str, help="Einzelnes Dokument (doc_id)")
    parser.add_argument("--sample", action="store_true", help="3 Pilot-Docs (2310, 2530, 1440)")
    parser.add_argument("--all", action="store_true", help="Alle Dokumente")
    parser.add_argument("--force", action="store_true", help="Cache ueberschreiben")
    parser.add_argument("--evaluate", action="store_true", help="Mit Referenz-TEI vergleichen")
    parser.add_argument("--dry-run", action="store_true", help="Nur Prompts zeigen")
    parser.add_argument("--refine", action="store_true",
                        help="Optionaler 2. Call pro Seite (Qualitaetsverbesserung)")
    parser.add_argument("--consolidate", action="store_true",
                        help="Optionaler API-Call fuer Dokument-Konsolidierung")
    args = parser.parse_args()

    client = None
    if not args.dry_run:
        client = get_client()

    if args.doc:
        doc_ids = [args.doc]
    elif args.sample:
        doc_ids = SAMPLE_DOC_IDS
    elif args.all:
        doc_ids = discover_doc_ids(IMAGES_DIR)
    else:
        parser.print_help()
        return

    mode = "1 Call/Seite"
    if args.refine:
        mode += " + Refine"
    if args.consolidate:
        mode += " + Consolidate"

    print(f"Gemini TEI Generator: {len(doc_ids)} Dokumente")
    print(f"Mode: {mode}")
    print(f"Model: {GEMINI_MODEL}")
    print(f"Output: {TEI_GEMINI_DIR}")

    results = []
    for doc_id in doc_ids:
        r = process_document(
            client, doc_id,
            force=args.force,
            refine=args.refine,
            consolidate=args.consolidate,
            evaluate=args.evaluate,
            dry_run=args.dry_run,
        )
        if r:
            results.append(r)

    if results:
        total_pages = sum(r.get("total_pages", 0) for r in results)
        total_time = sum(r.get("elapsed_seconds", 0) for r in results)
        print(f"\n{'='*60}")
        print(f"FERTIG: {len(results)} Dokumente, {total_pages} Seiten, {total_time:.1f}s")


if __name__ == "__main__":
    main()
