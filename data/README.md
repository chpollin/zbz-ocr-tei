# Source Data

This directory contains the input data for the project.
**Not versioned** (in .gitignore) -- provided by ZBZ.

## Structure

```
data/
├── scans/                    # 286 PDF scans (data delivery Feb 2026)
│   └── *.pdf                 # Named by project ID (e.g. 2310.pdf)
│
├── referenz-tei/             # 25 reference TEI files (ZBZ-annotated, DTA base format)
│   └── *.xml                 # Named by project ID (e.g. 2310.xml)
│
├── page-xml-transkribus/     # 24 Transkribus exports (PAGE-XML schema 2013-07-15)
│   └── {doc_id}/             # One folder per document
│       ├── mets.xml          # METS-Manifest
│       ├── metadata.xml      # Transkribus metadata
│       └── page/             # PAGE-XML per page (empty, no text)
│           └── *.xml
│
├── richtlinien/              # ZBZ project guidelines
│   ├── dta_basisformat_komplett.md           # DTA reference
│   └── Page-xml-Export Einstellungen.jpg     # Transkribus export settings
│
└── projektsteuerung/         # ZBZ project data (not yet delivered/copied)
    └── *.xlsx                # Work lists
```

## Data Delivery

**HerschStandFeb (Feb 2026):** 286 PDFs, 25 TEI-XMLs, 24 PAGE-XML exports.
Documented in [QUELLENANALYSE](../knowledge/QUELLENANALYSE.md) §Data Delivery and [DECISIONS](../knowledge/DECISIONS.md) E23.

| Category | Count | Source |
|----------|-------|--------|
| PDFs with TEI + PAGE-XML | 24 | ZBZ Transkribus (Collection 1886177) |
| PDFs without annotation | 262 | ZBZ Digitization |
| TEI-XMLs | 25 | Finished annotations (1 XML without corresponding PDF) |

## Note

The `data/` directory is excluded from Git to avoid versioning sensitive data and large files.
