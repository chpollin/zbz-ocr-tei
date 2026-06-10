#!/usr/bin/env python
"""Assemble Transkribus-compatible upload bundles from pipeline PAGE-XML + page images.

Transkribus liest beim Upload zu jedem Bild eine gleichnamige PAGE-XML aus einem
`page/`-Unterordner ein. Ein Ordner = ein Dokument. Dieses Skript baut genau diese
Struktur aus `output/page_xml/{doc}/page/` (PAGE-XML) + `docs/images/{doc}/` (PNG):

    output/transkribus_upload/
        {doc}/
            {doc}_p001.png
            {doc}_p002.png
            page/
                {doc}_p001.xml
                {doc}_p002.xml

Die PAGE-XML ist Standard-PAGE 2013-07-15 (TextRegion/Coords/TextLine/TextEquiv/
ReadingOrder) und damit Transkribus-kompatibel. Die PNG-Pixelmasse stimmen mit den in
der PAGE-XML deklarierten imageWidth/imageHeight ueberein (Koordinaten sind alignt);
das Skript verifiziert das pro Seite und meldet Abweichungen, statt sie still zu kopieren.

Hinweis: Die Pipeline-PAGE-XML traegt Zeilen-Polygone (Coords), aber keine Baselines.
Fuer Import, Anzeige und Strukturueberblick reicht das; nur HTR-*Training* braucht Baselines.

Aufrufe:
    python -m scripts.edition.transkribus_export --sample              # stratifiziert (~18)
    python -m scripts.edition.transkribus_export --sample -n 12        # andere Groesse
    python -m scripts.edition.transkribus_export --doc 100 130 40      # explizit
    python -m scripts.edition.transkribus_export --reference           # 24 ZBZ-Overlap-Docs
    python -m scripts.edition.transkribus_export --all                 # kompletter Korpus
    python -m scripts.edition.transkribus_export --sample --zip        # + ein .zip je Dok
    python -m scripts.edition.transkribus_export --sample --dry-run    # nur Auswahl zeigen
"""
import argparse
import json
import shutil
import struct
import sys
import zipfile
from collections import defaultdict
from pathlib import Path
import xml.etree.ElementTree as ET

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")  # Katalog-Titel enthalten Unicode

ROOT = Path(__file__).resolve().parents[2]
PAGE_XML_DIR = ROOT / "output" / "page_xml"
IMAGES_DIR = ROOT / "docs" / "images"
CATALOG = ROOT / "docs" / "data" / "catalog.json"
DEFAULT_OUT = ROOT / "output" / "transkribus_upload"
PAGE_NS = "{http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15}"

# Objekte, die ZBZ bereits selbst in Transkribus haben (Collection "Jeanne Hersch").
REFERENCE_DOCS = sorted(
    p.name for p in (ROOT / "data" / "source" / "transkribus_page_xml").iterdir()
    if p.is_dir()
) if (ROOT / "data" / "source" / "transkribus_page_xml").is_dir() else []

BUCKETS = ["xs", "s", "m", "l", "xl", "xxl"]
LANGS = ["FR", "DE", "DE_FR", "EN", "IT", "MULTI"]


def id_key(doc_id):
    """Sortier-Schluessel: numerisch wo moeglich, sonst lexikalisch."""
    return (0, int(doc_id)) if doc_id.isdigit() else (1, doc_id)


def page_bucket(pages):
    if pages <= 2:
        return "xs"
    if pages <= 5:
        return "s"
    if pages <= 10:
        return "m"
    if pages <= 20:
        return "l"
    if pages <= 60:
        return "xl"
    return "xxl"


def lang_group(raw):
    norm = (raw or "").upper()
    for a, b in (("FRA", "FR"), ("DEU", "DE"), ("ENG", "EN"), ("ITA", "IT"), ("SPA", "ES")):
        norm = norm.replace(a, b)
    parts = {p for p in norm.replace("/", " ").split() if p}
    if len(parts) >= 3:
        return "MULTI"
    if parts == {"FR"}:
        return "FR"
    if parts == {"DE"}:
        return "DE"
    if parts == {"EN"}:
        return "EN"
    if parts == {"IT"}:
        return "IT"
    if parts == {"DE", "FR"}:
        return "DE_FR"
    return "OTHER"


def png_size(path):
    """(width, height) aus dem PNG-Header, ohne Pillow-Abhaengigkeit."""
    with open(path, "rb") as fh:
        head = fh.read(24)
    if head[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    return struct.unpack(">II", head[16:24])


def xml_page_decl(path):
    """(imageFilename, width, height) aus dem <Page>-Element."""
    page = ET.parse(path).getroot().find(PAGE_NS + "Page")
    if page is None:
        return None
    return (
        page.get("imageFilename"),
        int(page.get("imageWidth", 0)),
        int(page.get("imageHeight", 0)),
    )


def available_docs():
    """Doc-IDs mit PAGE-XML-Verzeichnis (Bilder pro Seite werden beim Assembly geprueft)."""
    return sorted(
        (p.name for p in PAGE_XML_DIR.iterdir()
         if p.is_dir() and (p / "page").is_dir()),
        key=id_key,
    )


def load_catalog():
    if not CATALOG.exists():
        return {}
    docs = json.loads(CATALOG.read_text(encoding="utf-8")).get("documents", [])
    return {d["id"]: d for d in docs}


def stratified_sample(n):
    """Deterministische Stichprobe: deckt zuerst jeden Seiten-Bucket, dann jede
    Sprachgruppe ab, fuellt dann ueber die groessten Zellen auf. Innerhalb einer
    Zelle wird der Median (nach Seitenzahl, dann ID) gewaehlt."""
    catalog = load_catalog()
    avail = set(available_docs())
    cells = defaultdict(list)
    for doc_id in sorted(avail, key=id_key):
        meta = catalog.get(doc_id, {})
        pages = meta.get("page_count") or len(list((PAGE_XML_DIR / doc_id / "page").glob("*.xml")))
        cells[(page_bucket(pages), lang_group(meta.get("lang")))].append((doc_id, pages))
    for key in cells:
        cells[key].sort(key=lambda t: (t[1], id_key(t[0])))

    used, picked = set(), []

    def take(candidates):
        rem = [c for c in candidates if c[0] not in used]
        if not rem:
            return None
        doc_id = rem[len(rem) // 2][0]  # Median-Vertreter
        used.add(doc_id)
        picked.append(doc_id)
        return doc_id

    # Pass 1: jeden Seiten-Bucket abdecken (groesste Zelle des Buckets).
    for bucket in BUCKETS:
        opts = sorted(((k, v) for k, v in cells.items() if k[0] == bucket),
                      key=lambda kv: -len(kv[1]))
        if opts:
            take(opts[0][1])

    # Pass 2: jede Sprachgruppe abdecken.
    covered = {lang_group(catalog.get(d, {}).get("lang")) for d in picked}
    for lang in LANGS:
        if lang in covered:
            continue
        opts = sorted(((k, v) for k, v in cells.items() if k[1] == lang),
                      key=lambda kv: -len(kv[1]))
        if opts:
            if take(opts[0][1]):
                covered.add(lang)

    # Pass 3: auffuellen ueber die groessten Zellen (Round-Robin).
    ordered = sorted(cells.items(), key=lambda kv: (-len(kv[1]), kv[0]))
    while len(picked) < n:
        progressed = False
        for _key, candidates in ordered:
            if len(picked) >= n:
                break
            if take(candidates):
                progressed = True
        if not progressed:
            break
    return sorted(picked, key=id_key)


def assemble(doc_id, out_dir, make_zip):
    src_pages = sorted((PAGE_XML_DIR / doc_id / "page").glob(f"{doc_id}_p*.xml"),
                       key=lambda p: p.name)
    dst = out_dir / doc_id
    (dst / "page").mkdir(parents=True, exist_ok=True)
    stats = {"pages": 0, "missing_img": 0, "dim_mismatch": 0, "warnings": []}

    for xml_path in src_pages:
        decl = xml_page_decl(xml_path)
        if not decl or not decl[0]:
            stats["warnings"].append(f"{xml_path.name}: kein <Page imageFilename>")
            continue
        img_name, decl_w, decl_h = decl
        img_path = IMAGES_DIR / doc_id / img_name
        if not img_path.exists():
            stats["missing_img"] += 1
            stats["warnings"].append(f"{xml_path.name}: Bild fehlt ({img_name})")
            continue
        real = png_size(img_path)
        if real and (real[0] != decl_w or real[1] != decl_h):
            stats["dim_mismatch"] += 1
            stats["warnings"].append(
                f"{img_name}: Bildmass {real[0]}x{real[1]} != PAGE-XML {decl_w}x{decl_h} "
                "(Koordinaten waeren misaligned) -> uebersprungen")
            continue
        shutil.copy2(img_path, dst / img_name)
        shutil.copy2(xml_path, dst / "page" / xml_path.name)
        stats["pages"] += 1

    if make_zip and stats["pages"]:
        zip_path = out_dir / f"{doc_id}.zip"
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for f in sorted(dst.rglob("*")):
                if f.is_file():
                    zf.write(f, f.relative_to(out_dir))
        stats["zip"] = zip_path.name
    return stats


def write_readme(out_dir, selection, catalog):
    lines = [
        "# Transkribus-Upload — Pipeline-PAGE-XML",
        "",
        "Pro Objekt ein Ordner: Seitenbilder (PNG) oben, gleichnamige PAGE-XML im",
        "`page/`-Unterordner. Upload pro Objekt (ein Ordner = ein Dokument):",
        "",
        "1. app.transkribus.org -> Collection -> Upload -> Ordner `{doc}/` waehlen.",
        "2. Transkribus liest die `page/`-XML als Layout + Transkription der Seiten ein.",
        "",
        "PAGE-Dialekt: Standard PAGE 2013-07-15, mit Coords/TextLine/TextEquiv/ReadingOrder.",
        "Ohne Baselines (nur fuer HTR-Training noetig). Bildmasse == PAGE-XML-Angaben.",
        "",
        f"Objekte: {len(selection)}",
        "",
        "| Objekt | Seiten | Sprache | Titel |",
        "|--------|-------:|---------|-------|",
    ]
    for doc_id in selection:
        meta = catalog.get(doc_id, {})
        title = (meta.get("title") or "").replace("|", "/")[:60]
        lines.append(f"| {doc_id} | {meta.get('page_count','?')} | "
                     f"{meta.get('lang','?')} | {title} |")
    (out_dir / "_README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description="Transkribus-Upload-Bundles bauen")
    grp = ap.add_mutually_exclusive_group(required=True)
    grp.add_argument("--sample", action="store_true", help="stratifizierte Stichprobe")
    grp.add_argument("--all", action="store_true", help="kompletter Korpus")
    grp.add_argument("--reference", action="store_true", help="24 ZBZ-Overlap-Objekte")
    grp.add_argument("--doc", nargs="+", metavar="ID", help="explizite Doc-IDs")
    ap.add_argument("-n", type=int, default=18, help="Stichprobengroesse (default 18)")
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT, help="Zielverzeichnis")
    ap.add_argument("--zip", action="store_true", help="zusaetzlich je ein .zip pro Objekt")
    ap.add_argument("--dry-run", action="store_true", help="nur Auswahl zeigen, nichts schreiben")
    args = ap.parse_args()

    avail = set(available_docs())
    if args.sample:
        selection = stratified_sample(args.n)
    elif args.all:
        selection = sorted(avail, key=id_key)
    elif args.reference:
        selection = [d for d in REFERENCE_DOCS if d in avail]
    else:
        selection = [d for d in args.doc if d in avail]
        missing = [d for d in args.doc if d not in avail]
        if missing:
            print(f"WARN: ohne PAGE-XML, uebersprungen: {', '.join(missing)}")
    if not selection:
        print("Keine Objekte ausgewaehlt.")
        return 1

    catalog = load_catalog()
    print(f"Auswahl ({len(selection)} Objekte):")
    for doc_id in selection:
        meta = catalog.get(doc_id, {})
        print(f"  {doc_id:>5}  {str(meta.get('page_count','?')):>3} S.  "
              f"{str(meta.get('lang','?')):<14} {(meta.get('title') or '')[:54]}")

    if args.dry_run:
        print("\n[dry-run] nichts geschrieben.")
        return 0

    args.out.mkdir(parents=True, exist_ok=True)
    total_pages = total_warn = 0
    for doc_id in selection:
        st = assemble(doc_id, args.out, args.zip)
        total_pages += st["pages"]
        total_warn += len(st["warnings"])
        flag = "" if not st["warnings"] else f"  [!] {len(st['warnings'])} Hinweis(e)"
        zinfo = f"  zip={st['zip']}" if st.get("zip") else ""
        print(f"  {doc_id:>5}: {st['pages']:>3} Seiten kopiert{zinfo}{flag}")
        for w in st["warnings"]:
            print(f"        - {w}")

    write_readme(args.out, selection, catalog)
    with open(args.out / "_selection.json", "w", encoding="utf-8") as f:
        json.dump(
            {"selection": selection, "pages": total_pages},
            f,
            ensure_ascii=False, indent=2,
        )
    print(f"\nFertig: {len(selection)} Objekte, {total_pages} Seiten -> {args.out}")
    if total_warn:
        print(f"{total_warn} Hinweis(e) gesamt (siehe oben).")
    print("Upload: app.transkribus.org -> Collection -> Upload -> je Objekt-Ordner waehlen.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
