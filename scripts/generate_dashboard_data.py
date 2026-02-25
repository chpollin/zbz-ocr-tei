"""
Generiert docs/data/dashboard.json aus allen Pipeline-Datenquellen.

Idempotent — kann jederzeit erneut ausgefuehrt werden.
Fehlende Datenquellen werden graceful behandelt (Felder werden null).

Usage:
    python scripts/generate_dashboard_data.py
"""

import json
from datetime import datetime
from pathlib import Path

from scripts.config import (
    PROJECT_ROOT,
    TESTPLAN,
    DOCS_DIR,
    IMAGES_DIR,
    MISTRAL_RESULTS_DIR,
    EVALUATION_DIR,
    OUTPUT_DIR,
)


# --- Alle 15 Pilot-Dokumente mit Metadaten ---
# Vereinigt config.py TESTPLAN + die 3 Docs ohne Phase (130, 1060, 1410)
ALL_DOCS = {
    "2310": {"type": "A", "lang": "FR", "desc": "Rezension", "phase": "phase1"},
    "1180": {"type": "A", "lang": "DE/FR", "desc": "Jahresbericht", "phase": "phase1"},
    "290":  {"type": "A", "lang": "FR", "desc": "Essay", "phase": "phase1"},
    "130":  {"type": "A", "lang": "FR", "desc": "Zeitschrift", "phase": None},
    "1410": {"type": "A", "lang": "DE/FR", "desc": "Beitrag", "phase": None},
    "1060": {"type": "A", "lang": "DE", "desc": "Broschure", "phase": None},
    "2530": {"type": "B", "lang": "FR", "desc": "Zweispaltig", "phase": "phase2"},
    "890":  {"type": "B", "lang": "DE", "desc": "Lehrerzeitung", "phase": "phase2"},
    "3040": {"type": "B", "lang": "FR", "desc": "Lexikon", "phase": "phase2"},
    "40":   {"type": "C", "lang": "FR", "desc": "Roman", "phase": "phase4"},
    "1520": {"type": "C", "lang": "?", "desc": "Monografie", "phase": "phase4"},
    "90":   {"type": "D", "lang": "DE", "desc": "Hist. Druck", "phase": "phase3"},
    "830":  {"type": "D", "lang": "FR", "desc": "Bildband", "phase": "phase3"},
    "1440": {"type": "D", "lang": "DE", "desc": "Interview", "phase": "phase3"},
    "1330": {"type": "D", "lang": "FR", "desc": "Sammelband", "phase": "phase3"},
}

# DeepSeek CER/WER aus TESTPLAN (kein JSON vorhanden)
DEEPSEEK_METRICS = {
    "2310": {"cer": 0.0267, "wer": 0.1661, "pages": 2, "chars": 6597, "available_pages": [2, 3]},
    "1180": {"cer": 0.0489, "wer": 0.1329, "pages": 2, "chars": 6070, "available_pages": [2, 3]},
    "290":  {"cer": 0.0921, "wer": 0.1953, "pages": 2, "chars": 5213, "available_pages": [1, 2]},
}

# Mistral CER aus Evaluation (seitenweise fuer >10 TEI-Seiten, global sonst)
MISTRAL_CER = {
    "2310": 0.0700, "1180": 0.0312, "290": 0.1807,
    "2530": 0.0396, "890": 0.0596, "3040": 0.0902,
    "90": 0.0121, "1440": 0.0371, "830": 0.0400, "1330": 0.0260,
    "1060": 0.2260, "130": 0.0413, "1410": 0.0558,
    "40": 0.0257, "1520": 0.0273,
}

# Mistral Benchmark-Daten (aus benchmark.html DATA)
MISTRAL_BENCHMARK = {
    "2310": {"pages": 3, "chars": 8041, "time": 5.6, "spp": 1.87},
    "1180": {"pages": 8, "chars": 20121, "time": 6.37, "spp": 0.80},
    "290":  {"pages": 5, "chars": 15148, "time": 6.34, "spp": 1.27},
}


def load_json(path: Path):
    """Laedt JSON oder gibt None zurueck."""
    if not path.exists():
        print(f"  [SKIP] {path.name} nicht gefunden")
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        print(f"  [WARN] {path.name}: {e}")
        return None


def build_documents(images_manifest, eval_data, llm_manifest):
    """Baut pro-Dokument-Daten aus allen Quellen zusammen."""
    documents = {}

    # Index der Bild-Manifeste
    img_index = {}
    if images_manifest:
        for entry in images_manifest:
            img_index[entry["doc_id"]] = entry

    # Evaluation-Daten
    eval_docs = {}
    if eval_data and "documents" in eval_data:
        eval_docs = eval_data["documents"]

    # LLM-Manifest Docs
    llm_docs = {}
    if llm_manifest and "documents" in llm_manifest:
        for doc_stat in llm_manifest["documents"]:
            llm_docs[doc_stat["doc_id"]] = doc_stat

    for doc_id, meta in ALL_DOCS.items():
        doc = {
            "doc_id": doc_id,
            "type": meta["type"],
            "lang": meta["lang"],
            "desc": meta["desc"],
            "phase": meta["phase"],
            "page_count": 0,
            "pages": [],
            "pipeline_status": compute_pipeline_status(doc_id),
            "evaluation": None,
            "mistral_cer": MISTRAL_CER.get(doc_id),
            "mistral_stats": MISTRAL_BENCHMARK.get(doc_id),
            "deepseek_stats": DEEPSEEK_METRICS.get(doc_id),
            "llm_stats": None,
        }

        # Seiten aus Bild-Manifest
        if doc_id in img_index:
            img_data = img_index[doc_id]
            doc["page_count"] = img_data["page_count"]
            doc["pages"] = img_data.get("pages", [])

        # Evaluation (CER/WER aus LLM-C Evaluation)
        if doc_id in eval_docs:
            ev = eval_docs[doc_id]
            doc["evaluation"] = {
                "cer_llm": round(ev.get("cer", 0), 6),
                "wer_llm": round(ev.get("wer", 0), 6),
                "ref_chars": ev.get("ref_chars", 0),
                "ocr_chars": ev.get("ocr_chars", 0),
                "status": ev.get("status", "OK"),
            }

        # LLM-Korrektur Stats
        if doc_id in llm_docs:
            ls = llm_docs[doc_id]
            doc["llm_stats"] = {
                "pages_processed": ls.get("processed", 0),
                "input_tokens": ls.get("input_tokens", 0),
                "output_tokens": ls.get("output_tokens", 0),
            }

        documents[doc_id] = doc

    return documents


def compute_pipeline_status(doc_id: str) -> dict:
    """Prueft Datei-Existenz fuer jede Pipeline-Stufe."""
    return {
        "images": (IMAGES_DIR / doc_id).is_dir(),
        "ocr_mistral": any(MISTRAL_RESULTS_DIR.glob(f"{doc_id}_p*.md")),
        "ocr_deepseek": any((OUTPUT_DIR / "ocr_results").glob(f"{doc_id}_p*.md")),
        "llm_corrected": any((OUTPUT_DIR / "llm_corrected_c").glob(f"{doc_id}_p*.md")),
        "evaluation": doc_id in (load_eval_doc_ids() or []),
        "export": (OUTPUT_DIR / "export" / doc_id).is_dir(),
    }


_eval_doc_ids_cache = None


def load_eval_doc_ids():
    """Cached: Welche Docs haben Evaluation-Daten?"""
    global _eval_doc_ids_cache
    if _eval_doc_ids_cache is not None:
        return _eval_doc_ids_cache
    eval_path = EVALUATION_DIR / "evaluation_results.json"
    data = load_json(eval_path)
    if data and "documents" in data:
        _eval_doc_ids_cache = list(data["documents"].keys())
    else:
        _eval_doc_ids_cache = []
    return _eval_doc_ids_cache


def build_pipeline_summary(documents: dict, llm_manifest) -> dict:
    """Berechnet Aggregate aus den Dokumentdaten."""
    docs_with_ocr = sum(1 for d in documents.values() if d["pipeline_status"]["ocr_mistral"])
    docs_with_llm = sum(1 for d in documents.values() if d["pipeline_status"]["llm_corrected"])
    docs_with_eval = sum(1 for d in documents.values() if d["pipeline_status"]["evaluation"])

    # CER-Durchschnitte (nur evaluierte Docs)
    cer_llm_values = [d["evaluation"]["cer_llm"] for d in documents.values() if d["evaluation"]]
    cer_mistral_values = [d["mistral_cer"] for d in documents.values() if d["mistral_cer"] is not None]

    avg_cer_llm = sum(cer_llm_values) / len(cer_llm_values) if cer_llm_values else None
    avg_cer_mistral = sum(cer_mistral_values) / len(cer_mistral_values) if cer_mistral_values else None

    total_pages = sum(d["page_count"] for d in documents.values())

    # LLM-Kosten
    llm_totals = {}
    if llm_manifest and "totals" in llm_manifest:
        llm_totals = llm_manifest["totals"]

    return {
        "ocr_engine": "Mistral Document AI 2512",
        "llm_model": "Claude Haiku 4.5",
        "llm_variant": "C (Few-Shot)",
        "pilot_docs": len(documents),
        "pilot_pages": total_pages,
        "docs_with_ocr": docs_with_ocr,
        "docs_with_llm": docs_with_llm,
        "docs_with_eval": docs_with_eval,
        "avg_cer_mistral": round(avg_cer_mistral, 6) if avg_cer_mistral else None,
        "avg_cer_llm": round(avg_cer_llm, 6) if avg_cer_llm else None,
        "total_llm_cost_usd": llm_totals.get("cost_usd"),
        "total_llm_tokens_in": llm_totals.get("input_tokens"),
        "total_llm_tokens_out": llm_totals.get("output_tokens"),
    }


def build_phases(documents: dict) -> list:
    """Phase-Level Aggregation."""
    phase_defs = [
        {"id": "phase1", "name": "Baseline (einspaltig)", "doc_type": "A"},
        {"id": "phase2", "name": "Zweispaltig", "doc_type": "B"},
        {"id": "phase3", "name": "Spezialformate", "doc_type": "D"},
        {"id": "phase4", "name": "Monografien", "doc_type": "C"},
    ]

    phases = []
    for pdef in phase_defs:
        phase_docs = [d for d in documents.values() if d["phase"] == pdef["id"]]
        doc_ids = [d["doc_id"] for d in phase_docs]

        cer_mistral = [d["mistral_cer"] for d in phase_docs if d["mistral_cer"] is not None]
        cer_llm = [d["evaluation"]["cer_llm"] for d in phase_docs if d["evaluation"]]

        phases.append({
            "id": pdef["id"],
            "name": pdef["name"],
            "doc_type": pdef["doc_type"],
            "doc_ids": doc_ids,
            "status": "completed" if all(d["pipeline_status"]["ocr_mistral"] for d in phase_docs) else "partial",
            "avg_cer_mistral": round(sum(cer_mistral) / len(cer_mistral), 6) if cer_mistral else None,
            "avg_cer_llm": round(sum(cer_llm) / len(cer_llm), 6) if cer_llm else None,
        })

    return phases


def main():
    print("Dashboard-Daten generieren...")
    print(f"  Projekt-Root: {PROJECT_ROOT}")

    # Datenquellen laden
    print("\nDatenquellen laden:")
    images_manifest = load_json(DOCS_DIR / "images" / "manifest.json")
    eval_data = load_json(EVALUATION_DIR / "evaluation_results.json")
    llm_manifest = load_json(OUTPUT_DIR / "llm_corrected_c" / "manifest.json")

    # Dokumente zusammenfuehren
    print("\nDokumente zusammenfuehren...")
    documents = build_documents(images_manifest, eval_data, llm_manifest)

    # Dashboard-JSON bauen
    data = {
        "generated": datetime.now().isoformat(timespec="seconds"),
        "generator": "scripts/generate_dashboard_data.py",
        "project": {
            "title": "Jeanne Hersch Edition",
            "client": "Zentralbibliothek Zuerich",
            "contractor": "DHCraft",
            "corpus_total": 289,
            "corpus_pages": 7200,
        },
        "pipeline_summary": build_pipeline_summary(documents, llm_manifest),
        "phases": build_phases(documents),
        "documents": documents,
        "benchmark": {
            "timestamp": "2026-02-18",
            "note": "DeepSeek nur 2 Seiten pro Dokument (lokal, GPU), Mistral alle Seiten (Cloud API)",
            "documents": ["2310", "1180", "290"],
        },
    }

    # Schreiben
    output_path = DOCS_DIR / "data" / "dashboard.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    # Summary
    print(f"\nDashboard-Daten geschrieben: {output_path}")
    print(f"  Dokumente: {len(documents)}")
    print(f"  Mit OCR: {data['pipeline_summary']['docs_with_ocr']}")
    print(f"  Mit LLM: {data['pipeline_summary']['docs_with_llm']}")
    print(f"  Mit Eval: {data['pipeline_summary']['docs_with_eval']}")
    avg_cer = data["pipeline_summary"]["avg_cer_llm"]
    if avg_cer:
        print(f"  Avg CER (LLM): {avg_cer*100:.2f}%")


if __name__ == "__main__":
    main()
