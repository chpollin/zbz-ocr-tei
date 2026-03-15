"""
TEI Screening Prep: Erzeugt Batch-Manifest fuer Agent-Based Quality Screening.

Teilt 285 Docs in 4 Tiers + Batches ein basierend auf Seitenzahl und Komplexitaet.
Sammelt vorberechnete Daten (Metadaten, Validierung, Referenz-Verfuegbarkeit).

Aufruf:
    python -m scripts.tei.tei_screening_prep
"""

import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from scripts.config import TEI_UNIFIED_DIR, REFERENZ_TEI_DIR

PROJECT_ROOT = Path(__file__).parent.parent.parent
TEI_FINAL_DIR = PROJECT_ROOT / "output" / "tei_final"
LAYOUT_DIR = PROJECT_ROOT / "output" / "layout"
DOC_METADATA_PATH = PROJECT_ROOT / "data" / "doc_metadata.json"

# Tier config: (max_pages, docs_per_batch, pages_to_inspect_description)
TIERS = {
    1: {"max_pages": 3, "batch_size": 10, "inspect": "all pages"},
    2: {"max_pages": 8, "batch_size": 7, "inspect": "first + middle"},
    3: {"max_pages": 20, "batch_size": 4, "inspect": "first + middle + last"},
    4: {"max_pages": 9999, "batch_size": 2, "inspect": "first + 1/3 + 2/3"},
}


def get_doc_ids_with_tei():
    """Doc-IDs die ein finales TEI haben."""
    ids = []
    for d in TEI_UNIFIED_DIR.iterdir():
        if d.is_dir() and (d / f"{d.name}_final.xml").exists():
            ids.append(d.name)
    return sorted(ids, key=lambda x: int(x))


def get_overlay_pages(doc_id):
    """Welche Overlay-PNGs existieren fuer ein Doc?"""
    layout_dir = LAYOUT_DIR / doc_id
    if not layout_dir.exists():
        return []
    pages = []
    for f in sorted(layout_dir.iterdir()):
        if f.name.endswith("_overlay.png") and "_compare" not in f.name and "_gemini" not in f.name:
            # Extract page number from filename like 290_p001_overlay.png
            parts = f.stem.split("_p")
            if len(parts) >= 2:
                page_str = parts[1].split("_")[0]
                try:
                    pages.append(int(page_str))
                except ValueError:
                    pass
    return pages


def get_pages_to_inspect(page_count, available_pages, tier):
    """Bestimmt welche Seiten der Agent anschauen soll."""
    if not available_pages:
        return []

    if tier == 1:
        # Alle Seiten
        return available_pages

    if tier == 2:
        # Erste + Mitte
        first = available_pages[0]
        mid_idx = len(available_pages) // 2
        mid = available_pages[mid_idx]
        return sorted(set([first, mid]))

    if tier == 3:
        # Erste + Mitte + Letzte
        first = available_pages[0]
        mid = available_pages[len(available_pages) // 2]
        last = available_pages[-1]
        return sorted(set([first, mid, last]))

    # Tier 4: Erste + 1/3 + 2/3
    first = available_pages[0]
    third = available_pages[len(available_pages) // 3]
    two_third = available_pages[2 * len(available_pages) // 3]
    return sorted(set([first, third, two_third]))


def assign_tier(page_count):
    """Weist ein Doc einem Tier zu."""
    if page_count <= 3:
        return 1
    elif page_count <= 8:
        return 2
    elif page_count <= 20:
        return 3
    else:
        return 4


def main():
    # Load metadata
    with open(DOC_METADATA_PATH, encoding="utf-8") as f:
        raw = json.load(f)
    doc_meta = raw.get("documents", raw)

    # Get all doc IDs with TEI
    doc_ids = get_doc_ids_with_tei()
    print(f"Docs mit TEI: {len(doc_ids)}")

    # Reference TEIs
    ref_ids = set()
    if REFERENZ_TEI_DIR.exists():
        for f in REFERENZ_TEI_DIR.iterdir():
            if f.suffix == ".xml":
                ref_ids.add(f.stem)
    print(f"Referenz-TEIs: {len(ref_ids)}")

    # Assign tiers and collect doc info
    docs_by_tier = {1: [], 2: [], 3: [], 4: []}

    for doc_id in doc_ids:
        meta = doc_meta.get(doc_id, {})
        page_count = meta.get("page_count", 0) or 0
        tier = assign_tier(page_count)

        available_pages = get_overlay_pages(doc_id)
        pages_to_inspect = get_pages_to_inspect(page_count, available_pages, tier)

        doc_info = {
            "doc_id": doc_id,
            "tier": tier,
            "page_count": page_count,
            "language": meta.get("language", "und"),
            "layout_type": meta.get("layout_type", "?"),
            "pub_form": meta.get("pub_form", "?"),
            "title": meta.get("title", "?"),
            "has_reference": doc_id in ref_ids,
            "overlay_pages_available": len(available_pages),
            "pages_to_inspect": pages_to_inspect,
        }
        docs_by_tier[tier].append(doc_info)

    # Print tier summary
    for tier_num, docs in docs_by_tier.items():
        cfg = TIERS[tier_num]
        print(f"Tier {tier_num} ({cfg['inspect']}): {len(docs)} docs, "
              f"batch_size={cfg['batch_size']}, "
              f"batches={math.ceil(len(docs) / cfg['batch_size'])}")

    # Create batches
    batches = []
    batch_num = 0
    for tier_num in [1, 2, 3, 4]:
        cfg = TIERS[tier_num]
        tier_docs = docs_by_tier[tier_num]
        for i in range(0, len(tier_docs), cfg["batch_size"]):
            batch_num += 1
            batch_docs = tier_docs[i:i + cfg["batch_size"]]
            batches.append({
                "batch_id": batch_num,
                "tier": tier_num,
                "inspect_strategy": cfg["inspect"],
                "docs": batch_docs,
            })

    print(f"\nTotal batches: {batch_num}")
    total_docs = sum(len(b["docs"]) for b in batches)
    print(f"Total docs in batches: {total_docs}")

    # Write manifest
    manifest = {
        "generated": "2026-03-15",
        "method": "Agent-Based Quality Screening v2",
        "total_docs": total_docs,
        "total_batches": batch_num,
        "tier_summary": {
            str(t): {
                "docs": len(docs_by_tier[t]),
                "batch_size": TIERS[t]["batch_size"],
                "batches": math.ceil(len(docs_by_tier[t]) / TIERS[t]["batch_size"]),
                "inspect": TIERS[t]["inspect"],
            }
            for t in [1, 2, 3, 4]
        },
        "reference_docs": sorted(list(ref_ids & set(doc_ids))),
        "batches": batches,
    }

    TEI_FINAL_DIR.mkdir(parents=True, exist_ok=True)
    manifest_path = TEI_FINAL_DIR / "screening_manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    print(f"\nManifest: {manifest_path}")


if __name__ == "__main__":
    main()
