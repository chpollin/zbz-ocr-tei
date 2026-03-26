"""Produziert Daten fuer diagnostik_tei.json: W10-Analyse, Corpus-Statistik,
Timeline, Warning-Uebersicht."""

import json
import os
import re
from collections import Counter, defaultdict

from lxml import etree

TEI_NS = "http://www.tei-c.org/ns/1.0"

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEI_DIR = os.path.join(PROJECT_ROOT, "output", "tei_unified")
DIAG_PATH = os.path.join(PROJECT_ROOT, "docs", "data", "diagnostik_tei.json")
LOG_PATH = os.path.join(PROJECT_ROOT, "docs", "data", "diagnostik_log.json")
VAL_PATH = os.path.join(TEI_DIR, "validation_report.json")
META_PATH = os.path.join(PROJECT_ROOT, "data", "doc_metadata.json")

# Patterns for untagged organisations/places (FR/DE)
ORG_PAT = re.compile(
    r"\b(universit[eE\u00e9]|UNESCO|UNO|ONU|Acad[eE\u00e9]mie|Institut|"
    r"[Pp]arti|Soci[eE\u00e9]t[eE\u00e9]|Verlag|Verein|Stiftung|Kirche|"
    r"[EE\u00c9\u00e9]glise|[EE\u00c9\u00e9]cole|Facult[eE\u00e9]|Librairie|"
    r"Editions?|Biblioth[eE\u00e8]que|Mus[eE\u00e9]e|Conseil|"
    r"Assembl[eE\u00e9]e|Parlement|Bundesrat|Nationalrat|"
    r"Croix-Rouge|Nations?\s+Unies?|OTAN|NATO)\b",
    re.IGNORECASE,
)
PLACE_PAT = re.compile(
    r"\b(Gen[eE\u00e8]ve|Z[uU\u00fc]rich|Bern[e]?|Basel|Lausanne|Paris|"
    r"Berlin|Wien|London|Rom[ae]?|Moscou|New\s*York|"
    r"Suisse|Schweiz|France|Allemagne|Deutschland|"
    r"Europe|Am[eE\u00e9]rique|Asie|Afrique|Italie|"
    r"Angleterre|Espagne|Russie|Chine|Japon)\b",
    re.IGNORECASE,
)


def w10_analysis(w10_docs):
    results = []
    for doc_id in w10_docs:
        path = os.path.join(TEI_DIR, doc_id, f"{doc_id}_final.xml")
        tree = etree.parse(path)
        root = tree.getroot()
        body = root.find(f".//{{{TEI_NS}}}body")
        body_text = "".join(body.itertext()) if body is not None else ""

        counts = {}
        for tag in ("persName", "orgName", "placeName", "bibl"):
            counts[tag] = len(root.findall(f".//{{{TEI_NS}}}{tag}"))

        # Strip already-tagged text, then scan for untagged orgs/places
        raw_xml = etree.tostring(root, encoding="unicode")
        stripped = re.sub(
            r"<(persName|orgName|placeName|bibl)[^>]*>.*?</\1>",
            " ", raw_xml, flags=re.DOTALL,
        )
        plain = re.sub(r"<[^>]+>", " ", stripped)

        org_matches = sorted(set(m.group() for m in ORG_PAT.finditer(plain)))
        place_matches = sorted(set(m.group() for m in PLACE_PAT.finditer(plain)))
        has_untagged = bool(org_matches or place_matches)

        if has_untagged:
            assessment = "ner_miss"
        elif counts["orgName"] == 0 and counts["placeName"] == 0 and len(body_text) > 3000:
            assessment = "ner_miss"
        else:
            assessment = "content_explains"

        results.append({
            "doc_id": doc_id,
            "text_length": len(body_text),
            "persName_count": counts["persName"],
            "orgName_count": counts["orgName"],
            "placeName_count": counts["placeName"],
            "bibl_count": counts["bibl"],
            "has_untagged_orgs_places": has_untagged,
            "untagged_orgs": org_matches[:10],
            "untagged_places": place_matches[:10],
            "assessment": assessment,
        })
        print(f"  W10 {doc_id}: pers={counts['persName']} org={counts['orgName']} "
              f"place={counts['placeName']} | orgs={org_matches[:3]} "
              f"places={place_matches[:3]} -> {assessment}")
    return results


def corpus_statistics():
    with open(META_PATH, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    element_tags = [
        "p", "div", "head", "note", "lb", "persName", "orgName",
        "placeName", "bibl", "figure", "foreign", "hi",
    ]
    total_elements = Counter()
    total_pages = 0
    by_layout = defaultdict(lambda: {
        "n": 0, "total_entities": 0, "total_pages": 0, "max_div_depth": 0,
    })

    doc_count = 0
    for doc_dir in sorted(os.listdir(TEI_DIR)):
        final = os.path.join(TEI_DIR, doc_dir, f"{doc_dir}_final.xml")
        if not os.path.isfile(final):
            continue
        try:
            tree = etree.parse(final)
            root = tree.getroot()
        except Exception:
            continue

        doc_count += 1
        pbs = len(root.findall(f".//{{{TEI_NS}}}pb"))
        total_pages += pbs

        for tag in element_tags:
            total_elements[tag] += len(root.findall(f".//{{{TEI_NS}}}{tag}"))

        meta = metadata.get(doc_dir, {})
        layout = meta.get("layout_type", meta.get("doc_type", "-"))
        if not layout or layout == "unknown":
            layout = "-"
        by_layout[layout]["n"] += 1
        entity_count = sum(
            len(root.findall(f".//{{{TEI_NS}}}{t}"))
            for t in ("persName", "orgName", "placeName", "bibl")
        )
        by_layout[layout]["total_entities"] += entity_count
        by_layout[layout]["total_pages"] += pbs

        body = root.find(f".//{{{TEI_NS}}}body")
        if body is not None:
            dd = _div_depth(body)
            if dd > by_layout[layout]["max_div_depth"]:
                by_layout[layout]["max_div_depth"] = dd

    result = {
        "total_docs": doc_count,
        "total_pages": total_pages,
        "elements": dict(total_elements),
        "by_layout_type": {},
    }
    for lt, data in sorted(by_layout.items()):
        n = data["n"]
        result["by_layout_type"][lt] = {
            "n": n,
            "avg_entities": round(data["total_entities"] / n, 1) if n else 0,
            "avg_pages": round(data["total_pages"] / n, 1) if n else 0,
            "max_div_depth": data["max_div_depth"],
        }

    print(f"  Corpus: {doc_count} docs, {total_pages} pages")
    for tag, count in total_elements.most_common():
        print(f"    <{tag}>: {count}")
    return result


def _div_depth(elem, depth=0):
    max_d = depth
    for child in elem.findall(f"{{{TEI_NS}}}div"):
        max_d = max(max_d, _div_depth(child, depth + 1))
    return max_d


def validation_timeline():
    return [
        {"timestamp": "2026-03-26T16:00:00", "label": "Initial",
         "valid": 50, "invalid": 235, "warnings": 82},
        {"timestamp": "2026-03-26T17:00:00", "label": "Fix-001 Schema ref-Pattern",
         "valid": 285, "invalid": 0, "warnings": 82},
        {"timestamp": "2026-03-26T18:00:00", "label": "Fix-002 Heuristic lb",
         "valid": 285, "invalid": 0, "warnings": 37},
        {"timestamp": "2026-03-26T19:00:00", "label": "Fix-003 pb/div/figure",
         "valid": 285, "invalid": 0, "warnings": 29},
    ]


def warnings_current():
    with open(VAL_PATH, "r", encoding="utf-8") as f:
        val = json.load(f)

    by_rule = defaultdict(list)
    for doc_id, r in val["per_doc"].items():
        for w in r.get("warnings", []):
            by_rule[w.get("rule", "?")].append(int(doc_id))

    return [
        {
            "code": "W9", "count": len(by_rule.get("W9", [])),
            "status": "blocked_on_ner",
            "docs": sorted(by_rule.get("W9", [])),
            "description": "Entity-Tags ohne ref (NER-Re-Injection noetig)",
        },
        {
            "code": "W10", "count": len(by_rule.get("W10", [])),
            "status": "ner_miss",
            "docs": sorted(by_rule.get("W10", [])),
            "description": "Nur persName, 0 orgName/placeName (NER-Extraktionsproblem)",
        },
        {
            "code": "W11", "count": len(by_rule.get("W11", [])),
            "status": "false_positive",
            "docs": sorted(by_rule.get("W11", [])),
            "description": "Zu viele top-level divs (echte Anthologie-Struktur)",
        },
    ]


def main():
    from datetime import datetime

    print("=== W10-Tiefenanalyse ===")
    w10_docs = ["30", "50", "100", "910", "1270", "1360", "1370", "1380", "2180", "2310"]
    w10 = w10_analysis(w10_docs)

    print("\n=== Corpus-Statistik ===")
    stats = corpus_statistics()

    print("\n=== Validation Timeline ===")
    timeline = validation_timeline()
    for t in timeline:
        print(f"  {t['label']}: {t['valid']} valid, {t['invalid']} invalid, {t['warnings']} warnings")

    print("\n=== Warnings Current ===")
    wc = warnings_current()
    for w in wc:
        print(f"  {w['code']}: {w['count']} docs ({w['status']})")

    # Write to diagnostik_tei.json
    with open(DIAG_PATH, "r", encoding="utf-8") as f:
        diag = json.load(f)

    diag["w10_analysis"] = w10
    diag["corpus_stats"] = stats
    diag["validation_timeline"] = timeline
    diag["warnings_current"] = wc
    diag["timestamp"] = datetime.now().isoformat()

    with open(DIAG_PATH, "w", encoding="utf-8") as f:
        json.dump(diag, f, ensure_ascii=False, indent=2)

    # Append to diagnostik_log.json
    with open(LOG_PATH, "r", encoding="utf-8") as f:
        log = json.load(f)

    log.append({
        "timestamp": datetime.now().isoformat(),
        "lane": "tei",
        "action": "diagnostik_data_production",
        "docs_affected": 285,
        "result_summary": (
            f"Corpus: {stats['total_docs']} docs, {stats['total_pages']} pages. "
            f"W10: {sum(1 for w in w10 if w['assessment'] == 'ner_miss')}/10 ner_miss."
        ),
        "details": (
            "W10-Tiefenanalyse, Corpus-Statistik, Validierungs-Timeline, "
            "Warning-Uebersicht in diagnostik_tei.json geschrieben."
        ),
    })

    with open(LOG_PATH, "w", encoding="utf-8") as f:
        json.dump(log, f, ensure_ascii=False, indent=2)

    print("\ndiagnostik_tei.json + diagnostik_log.json aktualisiert")


if __name__ == "__main__":
    main()
