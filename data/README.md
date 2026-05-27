# Data

Input and reference data. Two categories with different versioning rules:

- **`source/`** — delivered by ZBZ, immutable input ("what we started with").
  Mostly **not versioned** (in `.gitignore`); only the editorial guidelines (text) are tracked.
- **everything else** — project-built authority, **git-tracked**: schema and curated
  gold TEI. Plus a generated classification cache.

## Structure

```
data/
├── source/                      # ZBZ delivery -- immutable input
│   ├── pdf/                     # PDF scans, named by project ID (e.g. 2310.pdf)   [gitignored]
│   ├── reference_tei/           # Transkribus-made reference/gold TEI (.xml)        [gitignored]
│   ├── transkribus_page_xml/    # Transkribus PAGE-XML exports, one folder per doc  [gitignored]
│   ├── masterfile/              # Masterfile.xlsx (catalog + workflow steering)     [gitignored]
│   └── guidelines/              # editorial guidelines (text + DTA link)            [tracked]
│
├── schema/                      # zbz_hersch.rng (project-specific TEI schema)      [tracked]
├── curated_tei/                 # curated gold-standard TEI                          [tracked]
└── doc_metadata.json            # GENERATED Gemini classification (committed cache)  [tracked]
```

## Source data (ZBZ delivery "HerschStandFeb", Feb 2026)

| Category | Location | Origin |
|---|---|---|
| PDF scans | `source/pdf/` | ZBZ digitization |
| Reference / gold TEI | `source/reference_tei/` | ZBZ Transkribus (Collection 1886177), finished annotations |
| PAGE-XML exports | `source/transkribus_page_xml/` | ZBZ Transkribus |
| Catalog + steering | `source/masterfile/Masterfile.xlsx` | ZBZ Alma / swisscovery + project workflow |
| Editorial guidelines | `source/guidelines/` | ZBZ (DTA base format + ZBZ-specific deviations) |

**Corpus counts are deliberately not recorded here.** Quantities (delivered docs, pages,
languages, genres) live only in the generated audit artifact, bound to a
`(source, unit, extraction)` triple:

```bash
python -m scripts.eval.corpus_audit
```

See [knowledge/projekt.md](../knowledge/projekt.md) for the funnel and
[knowledge/quality.md](../knowledge/quality.md) for the reference-TEI role.

## Note

`source/` is excluded from Git (sensitive / large files). A fresh clone therefore carries
the project-built authority (`schema/`, `curated_tei/`) and the classification
cache, but not the raw ZBZ delivery.
