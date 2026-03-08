"""
Shared Data Loaders: OCR-Text, Layout, Dokument-Discovery.

Kanonische Implementierung fuer load_ocr_text, discover_pages,
discover_documents, load_layout_gemini, skip_jstor_cover.
Wird importiert von: tei_generator, tei_unified, ner_extract u.a.
"""

import json
import re

from scripts.config import (
    ENTITIES_DIR,
    GEMINI_CORRECTED_A_DIR,
    GEMINI_CORRECTED_B_DIR,
    LAYOUT_DIR,
    LLM_CORRECTED_C_DIR,
    MISTRAL_RESULTS_DIR,
)

# OCR-Prioritaet: beste Korrektur zuerst
_OCR_DIRS = [
    GEMINI_CORRECTED_B_DIR,
    GEMINI_CORRECTED_A_DIR,
    LLM_CORRECTED_C_DIR,
    MISTRAL_RESULTS_DIR,
]


def load_ocr_text(doc_id: str, page: int) -> str | None:
    """Laedt OCR-Text: Gemini B > Gemini A > LLM C > Mistral."""
    for base_dir in _OCR_DIRS:
        path = base_dir / f"{doc_id}_p{page}.md"
        if path.exists():
            return path.read_text(encoding="utf-8")
    return None


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


def discover_entity_docs() -> list[str]:
    """Findet alle Dokumente mit Entity-Daten (ENTITIES_DIR)."""
    if not ENTITIES_DIR.exists():
        return []
    return sorted(
        d.name for d in ENTITIES_DIR.iterdir()
        if d.is_dir() and not d.name.startswith("_")
    )


def load_layout_gemini(doc_id: str, page: int) -> dict | None:
    """Laedt Gemini-korrigiertes Layout-JSON, Fallback auf Docling.

    Gemini-JSON hat evtl. kein image_width/image_height -- wird aus
    Docling-JSON ergaenzt falls vorhanden.
    """
    padded = str(page).zfill(3)
    gemini_path = LAYOUT_DIR / doc_id / f"{doc_id}_p{padded}_layout_gemini.json"
    docling_path = LAYOUT_DIR / doc_id / f"{doc_id}_p{padded}_layout.json"

    layout = None
    if gemini_path.exists():
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
