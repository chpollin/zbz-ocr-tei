"""
Gemeinsame Hilfsfunktionen fuer das zbz-ocr-tei Projekt.

Konsolidiert: pdf_to_images, check_gpu.
"""

import json
import re
from pathlib import Path

from scripts.config import DEFAULT_DPI


def check_gpu() -> dict:
    """
    Prueft GPU-Verfuegbarkeit.

    Returns:
        dict mit "available" (bool), optional "name" (str) und "vram_gb" (float)
    """
    try:
        import torch
        if torch.cuda.is_available():
            return {
                "available": True,
                "name": torch.cuda.get_device_name(0),
                "vram_gb": torch.cuda.get_device_properties(0).total_memory / 1024**3,
            }
    except ImportError:
        pass
    return {"available": False}


def pdf_to_images(pdf_path: Path, output_dir: Path, dpi: int = DEFAULT_DPI) -> list[Path]:
    """
    Konvertiert alle PDF-Seiten zu PNG-Bildern.

    Args:
        pdf_path: Pfad zur PDF-Datei
        output_dir: Verzeichnis fuer die Bilder
        dpi: Aufloesung (default: 300)

    Returns:
        Liste der erzeugten Bildpfade
    """
    import pypdfium2 as pdfium

    pdf = pdfium.PdfDocument(str(pdf_path))
    total = len(pdf)
    pdf.close()

    return pdf_to_images_pages(pdf_path, list(range(total)), output_dir, dpi)


def pdf_to_images_pages(
    pdf_path: Path, pages: list[int], output_dir: Path, dpi: int = DEFAULT_DPI
) -> list[Path]:
    """
    Konvertiert spezifische PDF-Seiten zu PNG-Bildern.

    Args:
        pdf_path: Pfad zur PDF-Datei
        pages: 0-basierte Seitenindizes
        output_dir: Verzeichnis fuer die Bilder
        dpi: Aufloesung (default: 300)

    Returns:
        Liste der erzeugten Bildpfade
    """
    import pypdfium2 as pdfium

    output_dir.mkdir(parents=True, exist_ok=True)
    pdf = pdfium.PdfDocument(str(pdf_path))
    image_paths = []

    for page_num in pages:
        if page_num >= len(pdf):
            print(f"    Warnung: Seite {page_num+1} existiert nicht (max: {len(pdf)})")
            continue

        bitmap = pdf[page_num].render(scale=dpi / 72)
        pil_image = bitmap.to_pil()
        image_path = output_dir / page_image_name(pdf_path.stem, page_num + 1)
        pil_image.save(str(image_path), "PNG")
        image_paths.append(image_path)

    pdf.close()
    return image_paths


def extract_page_num(filename: str) -> int:
    """Extrahiert Seitennummer aus Dateinamen wie '2310_p001.png' oder '2310_p1.md'.

    Returns:
        int: Seitennummer

    Raises:
        ValueError: Wenn kein Seitenmuster gefunden wird
    """
    m = re.search(r'_p(\d+)', str(filename))
    if not m:
        raise ValueError(f"Keine Seitennummer in: {filename}")
    return int(m.group(1))


# ---------------------------------------------------------------------------
# Seitenpfad-Namen: EINE Stelle fuer die (bewusst asymmetrische) Padding-Konvention.
# .md ist ungepaddet ({doc}_p1.md), Seitenbild/Layout-JSON 3-stellig ({doc}_p001.*).
# Module sollen diese Helfer nutzen statt die Konvention je Aufrufer neu zu bauen
# (Namens-Mismatch beim Laden war die haeufigste stille Falle).
# ---------------------------------------------------------------------------

def page_md_name(doc_id: str, page: int) -> str:
    """OCR-Markdown-Dateiname (ungepaddet): '2310_p7.md'."""
    return f"{doc_id}_p{page}.md"


def page_image_name(doc_id: str, page: int) -> str:
    """Seitenbild-Dateiname (3-stellig gepaddet): '2310_p007.png'."""
    return f"{doc_id}_p{page:03d}.png"


def page_layout_name(doc_id: str, page: int, variant: str = "") -> str:
    """Layout-JSON-Dateiname (3-stellig gepaddet). variant: '' | '_gemini' | '_curated'.

    page_layout_name('2310', 7)            -> '2310_p007_layout.json'
    page_layout_name('2310', 7, '_gemini') -> '2310_p007_layout_gemini.json'
    """
    return f"{doc_id}_p{page:03d}_layout{variant}.json"


def load_json(path: Path) -> dict | None:
    """Laedt JSON-Datei. Gibt None zurueck bei fehlenden/defekten Dateien."""
    path = Path(path)
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        print(f"  WARN: {path.name}: {e}")
        return None


def read_json_strict(path: Path):
    """Laedt JSON-Datei und laesst Fehler durchschlagen.

    Gegenstueck zu load_json: an einer Trust-Boundary, wo eine fehlende oder defekte
    Eingabedatei den Lauf beenden soll, statt still None weiterzureichen.
    """
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path: Path, data) -> None:
    """Schreibt JSON mit indent=2, ensure_ascii=False, utf-8."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def get_phase_doc_ids(phase: str) -> list[str]:
    """Gibt Dokument-IDs fuer eine TESTPLAN-Phase zurueck.

    Args:
        phase: 'phase1', 'phase2', ..., 'all'
    """
    from scripts.config import TESTPLAN

    if phase == "all":
        doc_ids = []
        for p in TESTPLAN.values():
            for t in p["tests"]:
                doc_id = t["pdf"].replace(".pdf", "")
                if doc_id not in doc_ids:
                    doc_ids.append(doc_id)
        return doc_ids

    if phase in TESTPLAN:
        return [t["pdf"].replace(".pdf", "") for t in TESTPLAN[phase]["tests"]]

    return []


def discover_doc_ids(base_dir: Path) -> list[str]:
    """Findet alle Doc-IDs (nicht-versteckte Unterverzeichnisse) in einem Verzeichnis."""
    base = Path(base_dir)
    if not base.exists():
        return []
    return sorted(
        d.name for d in base.iterdir()
        if d.is_dir() and not d.name.startswith(".")
    )
