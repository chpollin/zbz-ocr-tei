"""
Gemini-basierte Dokumentklassifikation (Stage 1a).

Sendet die ersten 5 Seiten jedes Dokuments an Gemini Vision
und extrahiert Metadaten: Sprache, Typ, Titel, Autor, Datum, etc.

Ergebnis: data/doc_metadata.json (kompakt, TEI-mappbar).
"""

import argparse
import json
import os
import sys
import time
import warnings
from datetime import UTC, datetime

from scripts.config import (
    CLASSIFICATION_DIR,
    DOC_METADATA_PATH,
    GEMINI_API_KEY,
    GEMINI_MODEL,
    IMAGES_DIR,
)
from scripts.utils import discover_doc_ids, load_json, write_json

# Gemini SDK warnings unterdruecken
warnings.filterwarnings("ignore", message=".*non-text parts.*thought_signature.*")

_api_key = os.environ.get("GEMINI_API_KEY", "") or GEMINI_API_KEY

MAX_PAGES = 5

CLASSIFY_SCHEMA = {
    "type": "object",
    "properties": {
        "language": {
            "type": "string",
            "description": "ISO 639-3 code(s) of main text: fra, deu, fra/deu, eng, ita, etc.",
        },
        "pub_form": {
            "type": "string",
            "enum": [
                "book", "bookSection", "journalArticle", "encyclopedia",
                "brochure", "interview", "anthology", "other",
            ],
        },
        "layout_type": {
            "type": "string",
            "enum": ["A", "B", "C", "D"],
            "description": "A=single-column, B=two-column, C=monograph(>50pp), D=special/mixed",
        },
        "title": {
            "type": "string",
            "nullable": True,
            "description": "Document title if visible on pages",
        },
        "author": {
            "type": "string",
            "nullable": True,
            "description": "Author name if visible",
        },
        "date": {
            "type": "string",
            "nullable": True,
            "description": "Publication year if determinable (e.g. 1986)",
        },
        "description": {
            "type": "string",
            "description": "One-sentence description of the document",
        },
        "has_jstor_cover": {"type": "boolean"},
        "num_columns": {
            "type": "string",
            "enum": ["1", "2"],
            "description": "Dominant number of text columns: 1 or 2",
        },
    },
    "required": [
        "language", "pub_form", "layout_type", "description",
        "has_jstor_cover", "num_columns",
    ],
}

PROMPT = """Analyze this scanned document. These are the first pages of a document from the Jeanne Hersch archive (Zentralbibliothek Zuerich). Most documents are in French or German.

Extract the following metadata based ONLY on what is clearly visible:

- language: ISO 639-3 code(s) of the main text language (fra, deu, fra/deu, eng, ita, etc.)
- pub_form: publication form (book, bookSection, journalArticle, encyclopedia, brochure, interview, anthology, other)
- layout_type: A (single-column text), B (two-column text), C (monograph, long book), D (special format: photos, mixed layouts, historical prints)
- title: the document title if visible (null if not clear)
- author: the author name if visible (null if not clear). Note: Jeanne Hersch is the archive owner, she may be author or subject.
- date: publication year if determinable from the document (null if not clear)
- description: one-sentence description of the document content/type
- has_jstor_cover: true if the first page is a JSTOR cover/metadata page
- num_columns: dominant number of text columns (1 or 2)

Report only what you can clearly determine. Use null for uncertain fields."""


def get_client():
    """Gemini Client erstellen."""
    from google import genai

    if not _api_key:
        print("FEHLER: GEMINI_API_KEY nicht gesetzt. Bitte in .env eintragen.")
        sys.exit(1)
    return genai.Client(api_key=_api_key)


def classify_document(client, doc_id, force=False):
    """Klassifiziert ein Dokument anhand der ersten Seiten."""
    from google.genai import types
    from PIL import Image

    # Skip-existing
    output_path = CLASSIFICATION_DIR / f"{doc_id}_classification.json"
    if output_path.exists() and not force:
        print(f"  SKIP: {doc_id} (bereits vorhanden)")
        return load_json(output_path)

    # Seiten-Bilder laden (erste 5)
    img_dir = IMAGES_DIR / doc_id
    if not img_dir.exists():
        print(f"  SKIP: {doc_id} (keine Bilder)")
        return None

    page_files = sorted(img_dir.glob(f"{doc_id}_p*.png"))[:MAX_PAGES]
    if not page_files:
        print(f"  SKIP: {doc_id} (keine PNGs)")
        return None

    images = []
    for pf in page_files:
        try:
            images.append(Image.open(pf))
        except Exception as e:
            print(f"  WARN: {pf.name}: {e}")

    if not images:
        return None

    # Gemini API Call
    contents = list(images) + [PROMPT]
    t0 = time.time()
    try:
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=contents,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=CLASSIFY_SCHEMA,
            ),
        )
        elapsed = time.time() - t0
        result = json.loads(response.text)
    except Exception as e:
        elapsed = time.time() - t0
        print(f"  FEHLER: {doc_id}: {e} ({elapsed:.1f}s)")
        return None

    # Metadaten anreichern
    result["doc_id"] = doc_id
    result["page_count"] = len(sorted(img_dir.glob(f"{doc_id}_p*.png")))
    result["pages_analyzed"] = len(page_files)
    result["elapsed_seconds"] = round(elapsed, 1)
    result["model"] = GEMINI_MODEL

    # Speichern
    CLASSIFICATION_DIR.mkdir(parents=True, exist_ok=True)
    write_json(output_path, result)

    print(f"  OK: {doc_id} -> {result.get('layout_type', '?')}/{result.get('language', '?')}"
          f" ({result.get('pub_form', '?')}) [{elapsed:.1f}s]")
    return result


def aggregate_metadata(results):
    """Aggregiert Ergebnisse in data/doc_metadata.json."""
    metadata = {
        "generated": datetime.now(UTC).isoformat(),
        "model": GEMINI_MODEL,
        "total_docs": len(results),
        "documents": {},
    }

    for r in results:
        if not r:
            continue
        doc_id = r["doc_id"]
        metadata["documents"][doc_id] = {
            "language": r.get("language", "und"),
            "pub_form": r.get("pub_form", "other"),
            "layout_type": r.get("layout_type", "A"),
            "title": r.get("title"),
            "author": r.get("author"),
            "date": r.get("date"),
            "description": r.get("description", ""),
            "has_jstor_cover": r.get("has_jstor_cover", False),
            "num_columns": int(r.get("num_columns", "1")),
            "page_count": r.get("page_count", 0),
        }

    write_json(DOC_METADATA_PATH, metadata)
    print(f"\nMetadaten geschrieben: {DOC_METADATA_PATH}")
    print(f"  Dokumente: {len(metadata['documents'])}")

    # Statistiken
    from collections import Counter
    types = Counter(d["layout_type"] for d in metadata["documents"].values())
    langs = Counter(d["language"] for d in metadata["documents"].values())
    forms = Counter(d["pub_form"] for d in metadata["documents"].values())
    print(f"  Typen: {dict(types.most_common())}")
    print(f"  Sprachen: {dict(langs.most_common())}")
    print(f"  Formen: {dict(forms.most_common())}")


def main():
    parser = argparse.ArgumentParser(description="Gemini-basierte Dokumentklassifikation")
    parser.add_argument("--doc", help="Einzelnes Dokument klassifizieren")
    parser.add_argument("--force", action="store_true", help="Cache ueberschreiben")
    args = parser.parse_args()

    client = get_client()

    # Docs bestimmen
    if args.doc:
        doc_ids = [args.doc]
    else:
        doc_ids = discover_doc_ids(IMAGES_DIR)

    if not doc_ids:
        print("Keine Dokumente gefunden.")
        return 1

    print("=" * 60)
    print(f"Dokumentklassifikation: {len(doc_ids)} Docs")
    print("=" * 60)

    # Existierende Metadaten laden (fuer inkrementelles Update)
    existing = load_json(DOC_METADATA_PATH) or {}
    existing_docs = existing.get("documents", {})

    results = []
    for i, doc_id in enumerate(doc_ids):
        print(f"\n[{i+1}/{len(doc_ids)}] {doc_id}")
        result = classify_document(client, doc_id, force=args.force)
        if result:
            results.append(result)
        elif doc_id in existing_docs:
            # Bestehendes Ergebnis beibehalten
            prev = existing_docs[doc_id].copy()
            prev["doc_id"] = doc_id
            results.append(prev)

    # Aggregieren
    aggregate_metadata(results)
    return 0


if __name__ == "__main__":
    sys.exit(main())
