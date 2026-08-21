"""Projiziert den Seitenbild-Zeiger <graphic url> in jede <surface> der finalen TEI.

ZBZ-Editionsrichtlinie (order Forschungsleitstelle 2026-06-21, Punkt 3): die Seitenbild-
Anbindung folgt den ZBZ-Regeln. Der Seitenumbruch traegt bereits ``<pb facs="#facs_N" n=...>``
(alle 285, geprueft). Damit dieser Verweis selbst-enthaltend zum Bild aufloest, bekommt jede
``<surface xml:id="facs_N">`` als erstes Kind ein ``<graphic url>`` (Schema verlangt graphic vor
zone). Adressschema: relativer Dateiname ``{doc_id}_p{NNN}.png`` (real in ``docs/images/{doc_id}/``,
3-stellig, 1-basiert, sequenziell zu ``facs_N``).

Schliesst O25 und ersetzt den fehlerhaften Leerseiten-Platzhalter ``{N}.png`` (zeigte auf eine
nicht existente Datei), zonenbehaftete Surfaces hatten gar kein <graphic>. Die Pipeline erzeugt
das seit dem Fix in ``tei_step3.build_facsimile`` direkt; dieser Schritt bringt den bereits
ausgelieferten Bestand auf denselben Stand, ohne die OCR/Layout-Stufen neu zu fahren.

Idempotent (zweiter Lauf aendert nichts), Backup je Datei vor dem Schreiben.

Aufruf:
    python -m scripts.tei.tei_surface_graphic --dry-run     # nur Bericht, nichts schreiben
    python -m scripts.tei.tei_surface_graphic               # schreiben (mit Backup)
    python -m scripts.tei.tei_surface_graphic --doc 110     # einzelnes Dokument
"""

import argparse
import re
import shutil
from pathlib import Path

from scripts.config import IMAGES_DIR, OUTPUT_DIR, TEI_FINAL_DIR
from scripts.tei.tei_step3 import page_image_url

FINAL_DIR = TEI_FINAL_DIR
IMAGE_DIR = IMAGES_DIR
BACKUP_DIR = OUTPUT_DIR / "_backup_pre_surface_graphic"

# <surface xml:id="facs_N" ...> gefolgt von optionalem ersten <graphic .../>
_SURFACE_RE = re.compile(
    r'(<surface\s+xml:id="facs_(\d+)"[^>]*>)(\s*<graphic\b[^>]*/>)?'
)


def project_graphics(xml: str, doc_id: str) -> tuple[str, int, int]:
    """Setzt/korrigiert das <graphic url> als erstes Kind jeder <surface>.

    Returns: (neuer_xml, surfaces_total, surfaces_geaendert).
    """
    total = 0
    changed = 0

    def repl(m: re.Match) -> str:
        nonlocal total, changed
        total += 1
        open_tag = m.group(1)
        page_num = int(m.group(2))
        existing = m.group(3) or ""
        url = page_image_url(doc_id, page_num)
        new_block = f'{open_tag}\n      <graphic url="{url}"/>'
        # Vergleich gegen den vorhandenen ersten-Kind-Graphic (inkl. Whitespace normalisiert)
        if existing.strip() != f'<graphic url="{url}"/>':
            changed += 1
        return new_block

    new_xml = _SURFACE_RE.sub(repl, xml)
    return new_xml, total, changed


def _missing_images(doc_id: str, n_surfaces: int) -> list[str]:
    """Listet die erwarteten Seitenbilder, die im Bildordner fehlen (Diagnose, nicht blockierend)."""
    missing = []
    for page_num in range(1, n_surfaces + 1):
        img = IMAGE_DIR / doc_id / page_image_url(doc_id, page_num)
        if not img.exists():
            missing.append(img.name)
    return missing


def process_file(path: Path, dry_run: bool = False) -> dict:
    doc_id = path.name[: -len("_final.xml")]
    xml = path.read_text(encoding="utf-8")
    new_xml, total, changed = project_graphics(xml, doc_id)

    # Residual-Check: jede Surface traegt danach genau ein <graphic> als erstes Kind
    surfaces_with_graphic = len(re.findall(
        r'<surface\s+xml:id="facs_\d+"[^>]*>\s*<graphic\b', new_xml
    ))

    result = {
        "doc": doc_id,
        "surfaces": total,
        "changed": changed,
        "with_graphic": surfaces_with_graphic,
        "missing_images": _missing_images(doc_id, total),
        "written": False,
    }

    if not dry_run and changed:
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, BACKUP_DIR / path.name)
        path.write_text(new_xml, encoding="utf-8")
        result["written"] = True

    return result


def main():
    parser = argparse.ArgumentParser(
        description="Seitenbild-<graphic> in jede <surface> der finalen TEI projizieren (ZBZ, O25)"
    )
    parser.add_argument("--doc", help="Einzelnes Dokument")
    parser.add_argument("--dry-run", action="store_true", help="Nur Bericht, nichts schreiben")
    args = parser.parse_args()

    if args.doc:
        files = [FINAL_DIR / f"{args.doc}_final.xml"]
    else:
        files = sorted(FINAL_DIR.glob("*_final.xml"))

    total_changed = 0
    total_surfaces = 0
    docs_changed = 0
    missing_total = 0
    inconsistent = []

    for path in files:
        if not path.exists():
            print(f"Datei nicht gefunden: {path}")
            continue
        r = process_file(path, dry_run=args.dry_run)
        total_surfaces += r["surfaces"]
        total_changed += r["changed"]
        if r["changed"]:
            docs_changed += 1
        if r["with_graphic"] != r["surfaces"]:
            inconsistent.append((r["doc"], r["surfaces"], r["with_graphic"]))
        if r["missing_images"]:
            missing_total += len(r["missing_images"])

    mode = "DRY-RUN" if args.dry_run else "geschrieben"
    print(f"[{mode}] {len(files)} Dateien, {total_surfaces} Surfaces, "
          f"{total_changed} Graphics gesetzt/korrigiert in {docs_changed} Dokumenten")
    if inconsistent:
        print(f"  WARNUNG: {len(inconsistent)} Dokumente mit Surface ohne <graphic>:")
        for doc, s, g in inconsistent[:10]:
            print(f"    {doc}: {g}/{s}")
    if missing_total:
        print(f"  Hinweis: {missing_total} referenzierte Seitenbilder fehlen im Bildordner "
              f"(Diagnose, nicht blockierend)")


if __name__ == "__main__":
    main()
