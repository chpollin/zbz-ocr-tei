"""
Shared Data Loaders: OCR-Text, Layout, Dokument-Discovery.

Kanonische Implementierung fuer load_ocr_text, discover_pages,
discover_documents, load_layout_gemini, skip_jstor_cover.
Wird importiert von: tei_generator, tei_unified u.a.
"""

import json
import re

from scripts.config import (
    GEMINI_CORRECTED_A_DIR,
    GEMINI_CORRECTED_B_DIR,
    LAYOUT_DIR,
    LLM_CORRECTED_C_DIR,
    MISTRAL_RESULTS_DIR,
    OCR_CURATED_DIR,
)

# OCR-Prioritaet: menschlich kuratiert zuerst, dann beste Korrektur, dann Basis-OCR.
# OCR_CURATED_DIR wird vom Viewer per File System Access API direkt beschrieben
# (Direkt-Schreiben-Loop) und muss daher Vorrang vor allen Engine-Outputs haben.
#
# OCR_SOURCES ist die EINZIGE kanonische Quelle der OCR-Reihenfolge. Alle Konsumenten
# (auch der PAGE-XML-Generator via load_ocr_text_with_source) leiten sich hieraus ab,
# damit die Kette nicht an zwei Stellen getrennt driftet. Das Label dient der
# Provenienz-Angabe (z.B. @source im PAGE-XML).
OCR_SOURCES: list[tuple] = [
    (OCR_CURATED_DIR, "curated"),
    (GEMINI_CORRECTED_B_DIR, "gemini-b"),
    (GEMINI_CORRECTED_A_DIR, "gemini-a"),
    (LLM_CORRECTED_C_DIR, "llm-c"),
    (MISTRAL_RESULTS_DIR, "mistral"),
]
_OCR_DIRS = [d for d, _ in OCR_SOURCES]


def load_ocr_text(doc_id: str, page: int) -> str | None:
    """Laedt OCR-Text: kuratiert > Gemini B > Gemini A > LLM C > Mistral."""
    for base_dir in _OCR_DIRS:
        path = base_dir / f"{doc_id}_p{page}.md"
        if path.exists():
            return path.read_text(encoding="utf-8")
    return None


def load_ocr_text_with_source(doc_id: str, page: int) -> tuple:
    """Wie load_ocr_text, gibt zusaetzlich das Quell-Label zurueck.

    Returns: (text, source_label) oder (None, None). Nutzt dieselbe kanonische
    Reihenfolge wie load_ocr_text (OCR_SOURCES, kuratiert zuerst) -- so kann der
    PAGE-XML-Generator die Provenienz angeben, ohne die Kette zu duplizieren.
    """
    for base_dir, label in OCR_SOURCES:
        path = base_dir / f"{doc_id}_p{page}.md"
        if path.exists():
            return path.read_text(encoding="utf-8"), label
    return None, None


def discover_pages(doc_id: str) -> list[int]:
    """Findet alle verfuegbaren Seiten (aus OCR-Dateien)."""
    pages = set()
    for base_dir in _OCR_DIRS:
        if base_dir.exists():
            for f in base_dir.glob(f"{doc_id}_p*.md"):
                match = re.search(r'_p(\d+)\.md$', f.name)
                if match:
                    pages.add(int(match.group(1)))
    return sorted(pages)


def discover_documents() -> list[str]:
    """Findet alle Dokumente mit OCR-Daten."""
    doc_ids = set()
    for base_dir in _OCR_DIRS:
        if base_dir.exists():
            for f in base_dir.glob("*_p*.md"):
                match = re.match(r'(\d+)_p\d+\.md$', f.name)
                if match:
                    doc_ids.add(match.group(1))
    return sorted(doc_ids)


def discover_layout_pages(doc_id: str) -> list[int]:
    """Findet Seiten MIT Layout-Daten (Layout-scoped, aus *_layout.json).

    Unterschied zu discover_pages (OCR-scoped, aus .md): PAGE-XML/Overlays brauchen
    Layout-Regionen, also wird hier ueber die Layout-JSON discovered.
    """
    pages = set()
    layout_path = LAYOUT_DIR / doc_id
    if layout_path.exists():
        for f in layout_path.glob(f"{doc_id}_p*_layout.json"):
            match = re.search(r'_p(\d+)_layout\.json$', f.name)
            if match:
                pages.add(int(match.group(1)))
    return sorted(pages)


def discover_layout_documents() -> list[str]:
    """Findet Dokumente MIT Layout-Daten (digit-benannte Unterordner von LAYOUT_DIR).

    Layout-scoped Gegenstueck zu discover_documents (OCR-scoped). Kanonische Quelle
    fuer page_xml_generator und generate_layout_overlays.
    """
    doc_ids = set()
    if LAYOUT_DIR.exists():
        for d in LAYOUT_DIR.iterdir():
            if d.is_dir() and d.name.isdigit():
                doc_ids.add(d.name)
    return sorted(doc_ids, key=lambda x: int(x))


def load_layout_gemini(doc_id: str, page: int) -> dict | None:
    """Laedt Gemini-korrigiertes Layout-JSON, Fallback auf Docling.

    Gemini-JSON hat evtl. kein image_width/image_height -- wird aus
    Docling-JSON ergaenzt falls vorhanden.
    """
    padded = str(page).zfill(3)
    curated_path = LAYOUT_DIR / doc_id / f"{doc_id}_p{padded}_layout_curated.json"
    gemini_path = LAYOUT_DIR / doc_id / f"{doc_id}_p{padded}_layout_gemini.json"
    docling_path = LAYOUT_DIR / doc_id / f"{doc_id}_p{padded}_layout.json"

    # Prioritaet: menschlich kuratiert (Viewer-Direktschreiben) > Gemini > Docling
    layout = None
    if curated_path.exists():
        layout = json.loads(curated_path.read_text(encoding="utf-8"))
    elif gemini_path.exists():
        layout = json.loads(gemini_path.read_text(encoding="utf-8"))
    elif docling_path.exists():
        layout = json.loads(docling_path.read_text(encoding="utf-8"))

    if layout is None:
        return None

    # Bildgroesse ergaenzen falls fehlend (aus Docling-JSON)
    if not layout.get("image_width") and docling_path.exists():
        try:
            docling = json.loads(docling_path.read_text(encoding="utf-8"))
            layout["image_width"] = docling.get("image_width", 0)
            layout["image_height"] = docling.get("image_height", 0)
        except (json.JSONDecodeError, OSError) as e:
            print(f"  WARNUNG: Docling-Fallback fuer Bildgroesse fehlgeschlagen: {e}")

    return layout


def skip_jstor_cover(pages: list[int], metadata: dict) -> list[int]:
    """Entfernt JSTOR-Coverseite (Seite 1) falls has_jstor_cover."""
    if metadata and metadata.get("has_jstor_cover"):
        return [p for p in pages if p != 1]
    return pages
