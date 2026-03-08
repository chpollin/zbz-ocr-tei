"""
Curation Server: FastAPI-Backend fuer TEI-XML Kuration.

Serviert die Digitale Edition + API-Endpoints zum Laden, Speichern
und Validieren von kuratiertem TEI-XML.

Aufruf:
    python -m scripts.server.curation_server
    python -m scripts.server.curation_server --port 9000
"""

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from xml.etree import ElementTree as ET

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.config import (
    DOCS_DIR,
    TEI_CURATED_DIR,
    TEI_NER_DIR,
    TEI_UNIFIED_DIR,
)

EXAMPLES_DIR = DOCS_DIR / "data" / "examples"

app = FastAPI(title="ZBZ Curation Server", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Pydantic Models
# ---------------------------------------------------------------------------

class SavePageRequest(BaseModel):
    xml: str


class StatusUpdate(BaseModel):
    status: str  # draft, in_review, approved


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _sanitize_doc_id(doc_id: str) -> str:
    clean = "".join(c for c in doc_id if c.isdigit())
    if not clean:
        raise HTTPException(status_code=400, detail="Ungueltige doc_id")
    return clean


def _pad_page(page: int) -> str:
    return str(page).zfill(3)


def _find_page_tei(doc_id: str, page: int) -> tuple:
    """Findet Seiten-TEI mit Prioritaet: kuratiert > NER > unified > examples."""
    padded = _pad_page(page)

    # 1. Kuratiert
    curated = TEI_CURATED_DIR / doc_id / f"{doc_id}_p{padded}.xml"
    if curated.exists():
        return curated.read_text(encoding="utf-8"), "curated"

    # 2. Beispiele (Demo-Docs auf GitHub Pages)
    examples = DOCS_DIR / "data" / "examples" / doc_id / f"{doc_id}_p{page}.xml"
    if examples.exists():
        return examples.read_text(encoding="utf-8"), "examples"

    # 3. NER-angereichert (Seiten-Level existiert nicht einzeln, aber final.xml schon)
    # 4. Unified pipeline (ebenso nur final.xml)
    # Fuer Seiten-Level-Zugriff: extrahieren wir aus final.xml
    for source_dir, source_name in [
        (TEI_NER_DIR / doc_id, "ner"),
        (TEI_UNIFIED_DIR / doc_id, "unified"),
    ]:
        final = source_dir / f"{doc_id}_final.xml"
        if final.exists():
            xml = _extract_page_from_final(final, page)
            if xml:
                return xml, source_name

    return None, None


def _extract_page_from_final(final_path: Path, page: int) -> str:
    """Extrahiert eine einzelne Seite aus einem assemblierten TEI-Dokument."""
    try:
        content = final_path.read_text(encoding="utf-8")
        # Einfache Strategie: Body-Inhalt zurueckgeben
        # Fuer den Editor genuegt der gesamte Body als Seiten-Kontext
        # (spaeter kann man per <pb> splitten)
        body_match = re.search(r"<body[^>]*>(.*?)</body>", content, re.DOTALL)
        if body_match:
            return body_match.group(0)
    except Exception:
        pass
    return None


def _load_curation_meta(doc_id: str) -> dict:
    meta_path = TEI_CURATED_DIR / doc_id / f"{doc_id}_curation.json"
    if meta_path.exists():
        return json.loads(meta_path.read_text(encoding="utf-8"))
    return {
        "doc_id": doc_id,
        "status": "pipeline",
        "pages": {},
        "history": [],
    }


def _save_curation_meta(doc_id: str, meta: dict):
    doc_dir = TEI_CURATED_DIR / doc_id
    doc_dir.mkdir(parents=True, exist_ok=True)
    meta_path = doc_dir / f"{doc_id}_curation.json"
    meta_path.write_text(
        json.dumps(meta, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def _validate_xml_wellformed(xml: str) -> list:
    """Prueft XML-Wohlgeformtheit. Gibt Liste von Fehlern zurueck."""
    errors = []
    try:
        ET.fromstring(xml.encode("utf-8"))
    except ET.ParseError as e:
        errors.append({"message": str(e), "type": "parse_error"})
    return errors


# ---------------------------------------------------------------------------
# API Endpoints
# ---------------------------------------------------------------------------

@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "curated_dir": str(TEI_CURATED_DIR),
        "docs_dir": str(DOCS_DIR),
    }


@app.get("/api/tei/{doc_id}/page/{page}")
def get_page_tei(doc_id: str, page: int):
    doc_id = _sanitize_doc_id(doc_id)
    xml, source = _find_page_tei(doc_id, page)
    if xml is None:
        raise HTTPException(status_code=404, detail=f"Seite {page} nicht gefunden")
    return {"xml": xml, "source": source, "doc_id": doc_id, "page": page}


@app.put("/api/tei/{doc_id}/page/{page}")
def save_page_tei(doc_id: str, page: int, body: SavePageRequest):
    doc_id = _sanitize_doc_id(doc_id)

    # XML-Wohlgeformtheit pruefen
    errors = _validate_xml_wellformed(body.xml)
    if errors:
        raise HTTPException(status_code=422, detail={
            "message": "XML nicht wohlgeformt",
            "errors": errors,
        })

    # Speichern
    doc_dir = TEI_CURATED_DIR / doc_id
    doc_dir.mkdir(parents=True, exist_ok=True)
    padded = _pad_page(page)
    page_path = doc_dir / f"{doc_id}_p{padded}.xml"
    page_path.write_text(body.xml, encoding="utf-8")

    # Kurations-Metadaten aktualisieren
    meta = _load_curation_meta(doc_id)
    now = datetime.now().isoformat(timespec="seconds")
    meta["status"] = "draft"
    meta["pages"][str(page)] = {"status": "edited", "last_modified": now}
    meta["history"].append({
        "timestamp": now,
        "action": "page_saved",
        "page": page,
    })
    _save_curation_meta(doc_id, meta)

    # Optionale Validierung
    validation = None
    try:
        from scripts.tei.tei_validator import validate_relaxng
        validation = validate_relaxng(body.xml)
    except Exception:
        pass

    return {
        "status": "saved",
        "path": str(page_path),
        "page": page,
        "validation": validation,
    }


class ValidatePageRequest(BaseModel):
    xml: str


@app.post("/api/tei/{doc_id}/validate")
def validate_document(doc_id: str):
    doc_id = _sanitize_doc_id(doc_id)
    doc_dir = TEI_CURATED_DIR / doc_id
    final_path = doc_dir / f"{doc_id}_final.xml"

    if not final_path.exists():
        raise HTTPException(status_code=404, detail="Kein finales TEI gefunden")

    try:
        from scripts.tei.tei_validator import validate_tei_file
        result = validate_tei_file(final_path)
        return result
    except ImportError:
        raise HTTPException(status_code=500, detail="tei_validator nicht verfuegbar")


@app.post("/api/tei/{doc_id}/validate-page")
def validate_page_xml(doc_id: str, body: ValidatePageRequest):
    """Validiert ein XML-Fragment gegen RelaxNG (TEI All)."""
    import tempfile

    doc_id = _sanitize_doc_id(doc_id)

    # 1. Wohlgeformtheit
    wf_errors = _validate_xml_wellformed(body.xml)
    if wf_errors:
        return {"valid": False, "errors": wf_errors}

    # 2. RelaxNG via temp file
    try:
        from scripts.config import TEI_SCHEMA_PATH
        from scripts.tei.tei_validator import validate_relaxng

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".xml", encoding="utf-8", delete=False
        ) as tmp:
            tmp.write(body.xml)
            tmp_path = Path(tmp.name)

        errors = validate_relaxng(tmp_path, TEI_SCHEMA_PATH)
        tmp_path.unlink(missing_ok=True)

        return {"valid": len(errors) == 0, "errors": errors}
    except Exception as e:
        return {"valid": False, "errors": [{"message": str(e), "type": "validator_error"}]}


@app.post("/api/tei/{doc_id}/assemble")
def assemble_doc(doc_id: str):
    doc_id = _sanitize_doc_id(doc_id)
    doc_dir = TEI_CURATED_DIR / doc_id

    if not doc_dir.exists():
        raise HTTPException(status_code=404, detail="Kein kuratiertes Verzeichnis")

    # Alle Seiten-XMLs sammeln
    page_files = sorted(doc_dir.glob(f"{doc_id}_p*.xml"))
    if not page_files:
        raise HTTPException(status_code=404, detail="Keine kuratierten Seiten")

    page_teis = {}
    for pf in page_files:
        m = re.search(r"_p(\d+)\.xml$", pf.name)
        if m:
            page_num = int(m.group(1))
            page_teis[page_num] = pf.read_text(encoding="utf-8")

    try:
        from scripts.tei.tei_generator import get_document_metadata
        from scripts.tei.tei_step3 import assemble_document
        metadata = get_document_metadata(doc_id) or {}
        final_xml = assemble_document(doc_id, page_teis, metadata, {})
        final_path = doc_dir / f"{doc_id}_final.xml"
        final_path.write_text(final_xml, encoding="utf-8")

        meta = _load_curation_meta(doc_id)
        now = datetime.now().isoformat(timespec="seconds")
        meta["history"].append({
            "timestamp": now,
            "action": "assembled",
            "pages": len(page_teis),
        })
        _save_curation_meta(doc_id, meta)

        return {
            "status": "assembled",
            "path": str(final_path),
            "pages": len(page_teis),
            "size": len(final_xml),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/tei/{doc_id}/status")
def get_status(doc_id: str):
    doc_id = _sanitize_doc_id(doc_id)
    return _load_curation_meta(doc_id)


@app.put("/api/tei/{doc_id}/status")
def update_status(doc_id: str, body: StatusUpdate):
    doc_id = _sanitize_doc_id(doc_id)
    valid_statuses = {"pipeline", "draft", "in_review", "approved"}
    if body.status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Ungueltiger Status: {body.status}")

    meta = _load_curation_meta(doc_id)
    meta["status"] = body.status
    now = datetime.now().isoformat(timespec="seconds")
    meta["history"].append({
        "timestamp": now,
        "action": "status_changed",
        "new_status": body.status,
    })
    _save_curation_meta(doc_id, meta)
    return meta


# ---------------------------------------------------------------------------
# Publish Endpoint — kuratiertes TEI nach docs/data/examples/ kopieren
# ---------------------------------------------------------------------------

@app.post("/api/tei/{doc_id}/publish")
def publish_document(doc_id: str):
    """Kopiert kuratierte Seiten-XMLs nach docs/data/examples/ fuer GitHub Pages."""
    import shutil
    doc_id = _sanitize_doc_id(doc_id)
    meta = _load_curation_meta(doc_id)
    if meta.get("status") != "approved":
        raise HTTPException(
            status_code=400,
            detail="Nur freigegebene Dokumente (status=approved) koennen publiziert werden",
        )

    src_dir = TEI_CURATED_DIR / doc_id
    if not src_dir.exists():
        raise HTTPException(status_code=404, detail="Kein kuratiertes Verzeichnis")

    page_files = sorted(src_dir.glob(f"{doc_id}_p*.xml"))
    if not page_files:
        raise HTTPException(status_code=404, detail="Keine kuratierten Seiten")

    dst_dir = EXAMPLES_DIR / doc_id
    dst_dir.mkdir(parents=True, exist_ok=True)

    published = []
    for pf in page_files:
        # Umbenennen: {doc_id}_p001.xml -> {doc_id}_p1.xml (examples-Konvention)
        m = re.search(r"_p(\d+)\.xml$", pf.name)
        if m:
            page_num = int(m.group(1))
            dst_name = f"{doc_id}_p{page_num}.xml"
            dst_path = dst_dir / dst_name
            shutil.copy2(str(pf), str(dst_path))
            published.append(dst_name)

    # Final-XML auch kopieren
    final_src = src_dir / f"{doc_id}_final.xml"
    if final_src.exists():
        shutil.copy2(str(final_src), str(dst_dir / f"{doc_id}_final.xml"))
        published.append(f"{doc_id}_final.xml")

    meta["history"].append({
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "action": "published",
        "files": len(published),
    })
    _save_curation_meta(doc_id, meta)

    return {
        "status": "published",
        "destination": str(dst_dir),
        "files": published,
    }


# ---------------------------------------------------------------------------
# Entity / Wikidata Endpoints (Phase 3)
# ---------------------------------------------------------------------------

class WikidataSearchRequest(BaseModel):
    query: str
    lang: str = "de"
    limit: int = 5


@app.post("/api/wikidata/search")
def wikidata_search(body: WikidataSearchRequest):
    """Proxy fuer Wikidata API (umgeht CORS im Browser)."""
    import requests as http_requests
    try:
        resp = http_requests.get(
            "https://www.wikidata.org/w/api.php",
            params={
                "action": "wbsearchentities",
                "search": body.query,
                "language": body.lang,
                "limit": body.limit,
                "format": "json",
            },
            headers={"User-Agent": "zbz-ocr-tei/1.0 (Curation Editor)"},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        results = []
        for item in data.get("search", []):
            results.append({
                "id": item.get("id"),
                "label": item.get("label"),
                "description": item.get("description", ""),
                "url": item.get("concepturi", ""),
            })
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@app.get("/api/entities/search")
def entity_index_search(q: str = "", limit: int = 10):
    """Durchsucht den lokalen Entity Index."""
    try:
        from scripts.ner.entity_index import EntityIndex
        index = EntityIndex()
        index.load_all()
        results = []
        q_lower = q.lower()
        for eid, entry in index.entries.items():
            # IndexEntry is a dataclass — use attribute access
            name = getattr(entry, "main_name", "") or ""
            variants = getattr(entry, "variants", []) or []
            # Match against main name, variants, or ID
            match = q_lower in name.lower() or q_lower in eid.lower()
            if not match:
                for v in variants:
                    if q_lower in v.lower():
                        match = True
                        break
            if match:
                results.append({
                    "id": eid,
                    "name": name,
                    "type": getattr(entry, "entity_type", ""),
                    "wikidata": getattr(entry, "wikidata_qid", "") or "",
                    "gnd": getattr(entry, "gnd_id", "") or "",
                })
                if len(results) >= limit:
                    break
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# Static File Serving (Edition Frontend)
# ---------------------------------------------------------------------------

# Mount edition assets
app.mount("/edition", StaticFiles(directory=str(DOCS_DIR / "edition"), html=True), name="edition")
app.mount("/images", StaticFiles(directory=str(DOCS_DIR / "images")), name="images")
app.mount("/data", StaticFiles(directory=str(DOCS_DIR / "data")), name="data")

# Serve entity-utils.js from docs root
@app.get("/entity-utils.js")
def serve_entity_utils():
    path = DOCS_DIR / "entity-utils.js"
    if path.exists():
        return HTMLResponse(
            content=path.read_text(encoding="utf-8"),
            media_type="application/javascript",
        )
    raise HTTPException(status_code=404)


# Root redirect
@app.get("/")
def root_redirect():
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/edition/reader.html")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="ZBZ Curation Server")
    parser.add_argument("--port", type=int, default=8000, help="Port (default: 8000)")
    parser.add_argument("--host", default="127.0.0.1", help="Host (default: 127.0.0.1)")
    args = parser.parse_args()

    import uvicorn

    print(f"=== ZBZ Curation Server ===")
    print(f"  Edition: http://{args.host}:{args.port}/edition/reader.html")
    print(f"  API:     http://{args.host}:{args.port}/api/health")
    print(f"  Curated: {TEI_CURATED_DIR}")
    print()

    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
