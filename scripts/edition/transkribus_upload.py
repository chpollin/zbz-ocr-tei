#!/usr/bin/env python
"""Upload assembled Transkribus-Bundles via REST-API in eine Collection.

Liest die von `transkribus_export.py` gebauten Bundles
(`output/transkribus_upload/{doc}/` mit Bildern + `page/`-XML) und laedt jedes
Objekt als EIN Dokument in eine Transkribus-Collection.

Auth ausschliesslich ueber Umgebungsvariablen (Passwort NIE im Code/Repo/.env, das
von Agenten gelesen wird; NIE im Chat):

    # PowerShell:
    $env:TRANSKRIBUS_USER       = "du@example.org"
    $env:TRANSKRIBUS_PASSWORD   = "..."
    $env:TRANSKRIBUS_COLLECTION = "2426839"   # optional, sonst --collection

Protokoll (Legacy TrpServer REST, https://transkribus.eu/TrpServer/rest):
    POST /auth/login  (user, pw)              -> sessionId
    POST /uploads?collId={id}  (JSON-Manifest: md.title + pageList.pages[]) -> uploadId
    PUT  /uploads/{uploadId}   (multipart img + xml, eine Seite je PUT)
TrpServer ingestiert den Upload nach Eingang aller Dateien asynchron in die Collection.

Wichtig: Jeder Lauf legt NEUE Dokumente an (kein Dedup). Vor dem ersten echten Lauf
`--dry-run` (prueft Login + Collection-Zugriff, lokale Vollstaendigkeit) und dann
`--limit 1` (ein Objekt testweise), bevor der Rest folgt.

    python -m scripts.edition.transkribus_upload --dry-run
    python -m scripts.edition.transkribus_upload --doc 1500
    python -m scripts.edition.transkribus_upload --limit 1
    python -m scripts.edition.transkribus_upload                 # ganzes Bundle
"""
import argparse
import contextlib
import os
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import requests

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE = "https://transkribus.eu/TrpServer/rest"
ROOT = Path(__file__).resolve().parents[2]
DEFAULT_BUNDLE = ROOT / "output" / "transkribus_upload"
IMG_EXT = (".png", ".jpg", ".jpeg", ".tif", ".tiff")


def _find_text(xml_bytes, tag):
    """Ersten Wert eines Tags aus einer XML-Antwort ziehen (namespace-tolerant)."""
    root = ET.fromstring(xml_bytes)
    for el in root.iter():
        if el.tag.rsplit("}", 1)[-1] == tag and el.text:
            return el.text.strip()
    return None


def login(session, user, pw):
    r = session.post(f"{BASE}/auth/login", data={"user": user, "pw": pw}, timeout=60)
    if r.status_code == 401:
        raise SystemExit("Login abgelehnt (401). Pruefe TRANSKRIBUS_USER/PASSWORD "
                         "oder nutze einen Account mit REST-Zugang.")
    r.raise_for_status()
    sid = _find_text(r.content, "sessionId")
    if not sid:
        raise SystemExit("Login ok, aber keine sessionId in der Antwort gefunden.")
    session.cookies.set("JSESSIONID", sid)
    return sid


def verify_collection(session, coll):
    """Liest die Dokumentliste der Collection -> bestaetigt Zugriff + ID."""
    r = session.get(f"{BASE}/collections/{coll}/list", timeout=60)
    if r.status_code in (401, 403):
        raise SystemExit(f"Kein Zugriff auf Collection {coll} ({r.status_code}). "
                         "Gehoert sie dem Account und stimmt die ID?")
    r.raise_for_status()
    try:
        return len(r.json())
    except ValueError:
        return None  # Antwort war XML; Zugriff trotzdem ok


def collect_pages(doc_dir):
    """[(img_path, xml_path_or_None, pageNr)] sortiert nach Bilddateiname."""
    images = sorted((p for p in doc_dir.iterdir()
                     if p.is_file() and p.suffix.lower() in IMG_EXT),
                    key=lambda p: p.name)
    page_dir = doc_dir / "page"
    pages = []
    for n, img in enumerate(images, start=1):
        xml = page_dir / f"{img.stem}.xml"
        pages.append((img, xml if xml.exists() else None, n))
    return pages


def create_upload(session, coll, title, pages):
    manifest = {
        "md": {"title": title},
        "pageList": {"pages": [
            {"fileName": img.name, "pageNr": n,
             **({"pageXmlName": xml.name} if xml else {})}
            for img, xml, n in pages
        ]},
    }
    r = session.post(f"{BASE}/uploads", params={"collId": coll}, json=manifest,
                     headers={"Content-Type": "application/json"}, timeout=120)
    r.raise_for_status()
    uid = _find_text(r.content, "uploadId")
    if not uid:
        raise SystemExit(f"Upload angelegt, aber keine uploadId erkannt:\n{r.text[:500]}")
    return uid


def put_page(session, uid, img, xml):
    # ExitStack closes both handles even if the second open() fails
    with contextlib.ExitStack() as stack:
        files = {"img": (img.name, stack.enter_context(open(img, "rb")), "application/octet-stream")}
        if xml:
            files["xml"] = (xml.name, stack.enter_context(open(xml, "rb")), "application/octet-stream")
        r = session.put(f"{BASE}/uploads/{uid}", files=files, timeout=300)
        r.raise_for_status()


def upload_doc(session, coll, doc_dir, dry_run):
    title = doc_dir.name
    pages = collect_pages(doc_dir)
    n_img = len(pages)
    n_xml = sum(1 for _i, x, _n in pages if x)
    if not pages:
        print(f"  {title:>5}: keine Bilder -> uebersprungen")
        return False
    note = "" if n_xml == n_img else f"  [!] {n_img - n_xml} Seite(n) ohne PAGE-XML"
    if dry_run:
        print(f"  {title:>5}: wuerde {n_img} Seiten hochladen ({n_xml} mit XML){note}")
        return True
    uid = create_upload(session, coll, title, pages)
    for img, xml, n in pages:
        put_page(session, uid, img, xml)
        print(f"    {title} p{n:03d}: {img.name}{' + xml' if xml else ''}", flush=True)
    print(f"  {title:>5}: uploadId={uid}, {n_img} Seiten gesendet{note}")
    return True


def main():
    ap = argparse.ArgumentParser(description="Transkribus-Bundle hochladen (REST)")
    ap.add_argument("--bundle", type=Path, default=DEFAULT_BUNDLE,
                    help="Bundle-Verzeichnis (default output/transkribus_upload)")
    ap.add_argument("--collection", default=os.environ.get("TRANSKRIBUS_COLLECTION"),
                    help="Collection-ID (oder env TRANSKRIBUS_COLLECTION)")
    ap.add_argument("--doc", nargs="+", metavar="ID", help="nur diese Objekt-Ordner")
    ap.add_argument("--limit", type=int, help="nur die ersten N Objekte")
    ap.add_argument("--dry-run", action="store_true",
                    help="Login + Collection-Zugriff pruefen, Plan zeigen, nichts hochladen")
    args = ap.parse_args()

    if not args.bundle.is_dir():
        raise SystemExit(f"Bundle nicht gefunden: {args.bundle}\n"
                         "Erst: python -m scripts.edition.transkribus_export --sample")
    if not args.collection:
        raise SystemExit("Keine Collection-ID (--collection oder TRANSKRIBUS_COLLECTION).")

    doc_dirs = sorted((p for p in args.bundle.iterdir()
                       if p.is_dir() and not p.name.startswith("_")),
                      key=lambda p: (0, int(p.name)) if p.name.isdigit() else (1, p.name))
    if args.doc:
        wanted = set(args.doc)
        doc_dirs = [d for d in doc_dirs if d.name in wanted]
    if args.limit:
        doc_dirs = doc_dirs[:args.limit]
    if not doc_dirs:
        raise SystemExit("Keine passenden Objekt-Ordner im Bundle.")

    user = os.environ.get("TRANSKRIBUS_USER")
    pw = os.environ.get("TRANSKRIBUS_PASSWORD")
    session = requests.Session()

    if user and pw:
        login(session, user, pw)
        n = verify_collection(session, args.collection)
        extra = f" ({n} Dok. bereits drin)" if isinstance(n, int) else ""
        print(f"Auth ok. Collection {args.collection} erreichbar{extra}.")
    elif args.dry_run:
        print("Hinweis: TRANSKRIBUS_USER/PASSWORD nicht gesetzt -> nur lokaler Plan, "
              "kein Login/Collection-Check.")
    else:
        raise SystemExit("TRANSKRIBUS_USER/PASSWORD nicht gesetzt. Setze sie als "
                         "Umgebungsvariablen (siehe Skript-Kopf).")

    print(f"\n{'[dry-run] ' if args.dry_run else ''}Objekte: {len(doc_dirs)} aus {args.bundle}")
    done = 0
    for d in doc_dirs:
        if upload_doc(session, args.collection, d, args.dry_run):
            done += 1
    print(f"\n{'Geplant' if args.dry_run else 'Hochgeladen'}: {done}/{len(doc_dirs)} Objekte.")
    if not args.dry_run and done:
        print("Transkribus ingestiert die Uploads asynchron; die Dokumente erscheinen "
              "in Kuerze in der Collection (app.transkribus.org).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
