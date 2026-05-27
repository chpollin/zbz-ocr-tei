"""
Gemeinsame Hilfsfunktionen fuer das zbz-ocr-tei Projekt.

Konsolidiert: pdf_to_images, check_gpu, load_env.
"""

import json
import os
import re
from pathlib import Path

from scripts.config import PROJECT_ROOT, DEFAULT_DPI


def load_env():
    """Laedt .env-Datei ins Environment (falls vorhanden)."""
    env_file = PROJECT_ROOT / ".env"
    if not env_file.exists():
        return

    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


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
        image_path = output_dir / f"{pdf_path.stem}_p{page_num+1:03d}.png"
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
