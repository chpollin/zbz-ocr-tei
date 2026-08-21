# Data

Input and reference data. Two categories with different versioning rules:

- `source/`: delivered by ZBZ, immutable input ("what we started with").
  Mostly not versioned (in `.gitignore`); only the editorial guidelines (text) are tracked.
- everything else is project-built authority and git-tracked: schema, the reserved
  curated gold TEI folder, and a generated classification cache.

## Structure

```
data/
├── source/                      # ZBZ delivery -- immutable input
│   ├── pdf/                     # PDF scans, named by project ID (e.g. 2310.pdf)   [gitignored]
│   ├── reference_tei/           # Transkribus-made reference/gold TEI (.xml)        [gitignored]
│   ├── transkribus_page_xml/    # Transkribus PAGE-XML exports, one folder per doc  [gitignored]
│   ├── masterfile/              # Masterfile.xlsx (catalog + workflow steering)     [gitignored]
│   ├── guidelines/              # editorial guidelines (text + DTA link)            [tracked]
│   └── zbz-lieferung-2026-06-21/ # June delivery: guideline copy, ZBZ schema template, provenance record [tracked]
│
├── schema/                      # zbz_hersch.rng (project-specific TEI schema)      [tracked]
├── curated_tei/                 # reserved for human-verified TEI (currently empty)  [tracked]
├── entities/                    # curated entity list, GND variant cache, variant review, verdict store, marking policy [tracked]
└── doc_metadata.json            # GENERATED Gemini classification (committed cache)  [tracked]
```

## Source data (ZBZ delivery "HerschStandFeb", Feb 2026)

| Category | Location | Origin |
|---|---|---|
| PDF scans | `source/pdf/` | ZBZ digitization |
| Reference / gold TEI | `source/reference_tei/` | ZBZ Transkribus (Collection 1886177), finished annotations |
| PAGE-XML exports | `source/transkribus_page_xml/` | ZBZ Transkribus |
| Catalog + steering | `source/masterfile/Masterfile.xlsx` | ZBZ Alma / swisscovery + project workflow |
| Editorial guidelines | `source/guidelines/` | ZBZ (the guidelines reference the DTA-Basisformat with documented deviations; format authority is `schema/zbz_hersch.rng`, E102) |

Corpus counts are deliberately not recorded here. Quantities (delivered docs, pages,
languages, genres) live only in the generated audit artifact, bound to a
`(source, unit, extraction)` triple:

```bash
python -m scripts.eval.corpus_audit
```

See [knowledge/project.md](../knowledge/project.md), data section, for the funnel, the delivery tree and the entity input data, and
[knowledge/specification.md](../knowledge/specification.md) for the reference-TEI role
in the quality measurement.

## Note

`source/` is excluded from Git (sensitive / large files). A fresh clone therefore carries
the project-built authority (`schema/`), the reserved `curated_tei/` folder (empty until
documents are human-verified) and the classification cache, but not the raw ZBZ delivery.
