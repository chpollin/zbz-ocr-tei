#!/usr/bin/env python3
"""
Extract GND IDs from reference TEI files.

Creates a seed list of known entities for GND lookup.
"""

import sys
import re
import json
from pathlib import Path
from collections import defaultdict
from lxml import etree

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# TEI namespace
TEI_NS = "http://www.tei-c.org/ns/1.0"
NSMAP = {"tei": TEI_NS}


def extract_gnd_from_file(xml_path: Path) -> dict:
    """
    Extract all GND references from a TEI file.

    Returns dict with:
    - persons: list of (name, gnd_id)
    - organizations: list of (name, gnd_id)
    - works: list of (name, gnd_id)
    """
    result = {
        "file": xml_path.name,
        "persons": [],
        "organizations": [],
        "works": [],
        "other": []
    }

    try:
        tree = etree.parse(str(xml_path))
        root = tree.getroot()

        # Find persName with ref attribute containing GND
        for elem in root.iter():
            # Remove namespace prefix for easier matching
            tag = elem.tag.replace(f"{{{TEI_NS}}}", "")
            ref = elem.get("ref", "")
            corresp = elem.get("corresp", "")

            # Check for GND reference
            gnd_match = re.search(r"GND:(\d+)", ref) or re.search(r"GND:(\d+)", corresp)

            if gnd_match:
                gnd_id = gnd_match.group(1)
                text = "".join(elem.itertext()).strip()

                if tag == "persName":
                    result["persons"].append({"name": text, "gnd": gnd_id})
                elif tag == "orgName":
                    result["organizations"].append({"name": text, "gnd": gnd_id})
                elif tag in ("bibl", "title"):
                    result["works"].append({"name": text, "gnd": gnd_id})
                else:
                    result["other"].append({"tag": tag, "name": text, "gnd": gnd_id})

    except Exception as e:
        result["error"] = str(e)

    return result


def deduplicate_entities(all_results: list) -> dict:
    """
    Deduplicate and aggregate entities across all files.
    """
    persons = defaultdict(lambda: {"names": set(), "count": 0, "files": set()})
    organizations = defaultdict(lambda: {"names": set(), "count": 0, "files": set()})
    works = defaultdict(lambda: {"names": set(), "count": 0, "files": set()})

    for result in all_results:
        filename = result["file"]

        for p in result.get("persons", []):
            gnd = p["gnd"]
            persons[gnd]["names"].add(p["name"])
            persons[gnd]["count"] += 1
            persons[gnd]["files"].add(filename)

        for o in result.get("organizations", []):
            gnd = o["gnd"]
            organizations[gnd]["names"].add(o["name"])
            organizations[gnd]["count"] += 1
            organizations[gnd]["files"].add(filename)

        for w in result.get("works", []):
            gnd = w["gnd"]
            works[gnd]["names"].add(w["name"])
            works[gnd]["count"] += 1
            works[gnd]["files"].add(filename)

    # Convert sets to lists for JSON serialization
    def convert(d):
        return {
            gnd: {
                "names": list(data["names"]),
                "count": data["count"],
                "files": list(data["files"])
            }
            for gnd, data in d.items()
        }

    return {
        "persons": convert(persons),
        "organizations": convert(organizations),
        "works": convert(works)
    }


def main():
    print("=" * 60)
    print("GND Extraction from Reference TEI Files")
    print("=" * 60)

    # Find all TEI files
    tei_dir = PROJECT_ROOT / "data" / "referenz-tei"
    xml_files = list(tei_dir.glob("**/*.xml"))

    print(f"\nFound {len(xml_files)} TEI files")

    # Extract GND from each file
    all_results = []

    for xml_path in xml_files:
        print(f"  Processing: {xml_path.name}")
        result = extract_gnd_from_file(xml_path)
        all_results.append(result)

        # Summary per file
        n_pers = len(result.get("persons", []))
        n_org = len(result.get("organizations", []))
        n_work = len(result.get("works", []))

        if n_pers + n_org + n_work > 0:
            print(f"    -> {n_pers} persons, {n_org} orgs, {n_work} works")

    # Deduplicate
    print("\n" + "=" * 60)
    print("Aggregating unique entities...")
    print("=" * 60)

    aggregated = deduplicate_entities(all_results)

    # Summary
    print(f"\nUnique entities found:")
    print(f"  Persons:       {len(aggregated['persons'])}")
    print(f"  Organizations: {len(aggregated['organizations'])}")
    print(f"  Works:         {len(aggregated['works'])}")

    # Save results
    output_dir = PROJECT_ROOT / "output" / "gnd_analysis"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save detailed results
    detail_file = output_dir / "gnd_by_file.json"
    with open(detail_file, "w", encoding="utf-8") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)
    print(f"\nDetailed results: {detail_file}")

    # Save aggregated results
    agg_file = output_dir / "gnd_entities.json"
    with open(agg_file, "w", encoding="utf-8") as f:
        json.dump(aggregated, f, ensure_ascii=False, indent=2)
    print(f"Aggregated entities: {agg_file}")

    # Save human-readable summary
    summary_file = output_dir / "gnd_summary.md"
    with open(summary_file, "w", encoding="utf-8") as f:
        f.write("# GND Entities Summary\n\n")
        f.write(f"Extracted from {len(xml_files)} TEI reference files.\n\n")

        f.write("## Persons\n\n")
        f.write("| GND ID | Names | Count |\n")
        f.write("|--------|-------|-------|\n")
        for gnd, data in sorted(aggregated["persons"].items(), key=lambda x: -x[1]["count"]):
            names = ", ".join(data["names"][:3])
            if len(data["names"]) > 3:
                names += "..."
            f.write(f"| {gnd} | {names} | {data['count']} |\n")

        f.write("\n## Organizations\n\n")
        f.write("| GND ID | Names | Count |\n")
        f.write("|--------|-------|-------|\n")
        for gnd, data in sorted(aggregated["organizations"].items(), key=lambda x: -x[1]["count"]):
            names = ", ".join(data["names"][:3])
            f.write(f"| {gnd} | {names} | {data['count']} |\n")

        f.write("\n## Works\n\n")
        f.write("| GND ID | Names | Count |\n")
        f.write("|--------|-------|-------|\n")
        for gnd, data in sorted(aggregated["works"].items(), key=lambda x: -x[1]["count"]):
            names = ", ".join(data["names"][:3])
            if len(data["names"]) > 3:
                names += "..."
            f.write(f"| {gnd} | {names} | {data['count']} |\n")

    print(f"Summary: {summary_file}")

    print("\n" + "=" * 60)
    print("Done!")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
