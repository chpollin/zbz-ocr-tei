---
type: knowledge
created: 2026-01-29
updated: 2026-02-27
tags: [zbz-ocr-tei, zbz, workflow, transkribus, oxygen]
status: active
---

# ZBZ Workflow

Documentation of the existing editorial workflow at Zentralbibliothek Zuerich and the integration points with the automated pipeline.

**Dependencies:** None (context document)

---

## Existing Workflow (Manual)

The workflow consists of three parallel tracks:

1. **Transcription track**: Digitized material -> Transkribus -> GitLab -> Oxygen -> GitLab
2. **Metadata track**: Digitized material -> Alma -> Masterfile -> Swisscovery -> TEI header
3. **Correction loop**: Oxygen -> PDF -> External reviewers -> Oxygen

The **Masterfile (Excel)** serves as the central coordination hub.

---

## Transcription Track

1. **Digitized material** -> Scans of the source documents
2. **Transkribus** [???] -> Process is not standardized
3. **Export** from Transkribus as XML (manual, using TEI XML Export)
4. **GitLab** -> Deposit files (manual)
5. **Oxygen** -> Further XML markup (manual)
6. **GitLab** -> Deposit updated XML file (manual)

---

## Metadata Track

1. **Digitized material** -> Create catalog record in **Alma**
2. Prepare and enter metadata (manual)
3. Transfer Alma ID to the **Masterfile** (manual)
4. Add title to the special collection in **Swisscovery** (manual)
5. Metadata for TEI header from Alma -> **Workflow does not exist yet**

---

## Correction Loop

1. **Oxygen XML** -> Export as PDF, visually matching the scan (Oxygen Transformation)
2. **External reviewers** correct the PDF
3. Manual update of the XML in Oxygen

---

## Authority Data Linking

Persons, institutions, and works are manually linked with **GND IDs** in Oxygen.

---

## Systems

| System | Function | Format |
|--------|----------|--------|
| Transkribus | OCR/HTR and transcription | [???] - not standardized |
| Masterfile | Workflow management, status tracking | Excel |
| GitLab | Version control for TEI files | XML |
| Oxygen | TEI markup and transformation | XML |
| Alma | Cataloging and metadata | Catalog data |
| Swisscovery | Public discovery | Catalog data |
| GND | Authority data linking | IDs |

---

## Observations

- **Almost all steps are manual**
- The **Transkribus process is not standardized** (question marks in the diagram)
- The **TEI header workflow from Alma does not exist yet**
- External corrections are done via **PDF**, not directly on the XML
- Unclear whether XML on GitLab is **overwritten** or versioned

---

## Integration: Automated Pipeline

Since E21, zbz-ocr-tei handles the full pipeline (OCR -> Layout -> PAGE-XML -> NER/GND -> TEI-XML), replacing or augmenting the following steps in the existing workflow:

```
EXISTING (manual)                AUTOMATED (zbz-ocr-tei)
────────────────────────────────────────────────────────────────

Digitized material (PDF scans)   Digitized material (PDF scans)
        |                                |
  Transkribus [???]              ┌───────┴───────────────────┐
        |                        │ zbz-ocr-tei               │
  Manual Export                  │ (full pipeline)            │
        |                        │                            │
  GitLab (deposit XML)           │ OCR (Mistral/DeepSeek)    │
        |                        │   -> Layout (Docling)      │
  Oxygen (TEI markup)            │   -> PAGE-XML              │
        |                        │   -> NER/GND               │
  Oxygen (GND linking)           │   -> TEI-XML (DTA)         │
        |                        └───────┬───────────────────┘
  External correction loop               |
        |                        Final QA in Oxygen
  [Publication]                          |
                                 GitLab -> [Publication]
```

### Concrete Replacements

| Existing Step | Replaced By | Tool |
|---------------|-------------|------|
| Transkribus OCR | Batch OCR (Mistral/DeepSeek) | zbz-ocr-tei |
| Manual Transkribus export | Automatic PAGE-XML generation | zbz-ocr-tei |
| Oxygen basic TEI markup | Automatic TEI transformation | zbz-ocr-tei |
| Manual GND linking in Oxygen | NER + lobid.org API | zbz-ocr-tei |

### What Remains Manual

| Step | Reason |
|------|--------|
| Alma cataloging | Library-specific, no automation potential |
| Masterfile maintenance | Coordination task |
| Swisscovery assignment | Manual step |
| TEI header from Alma | Workflow does not exist yet (-> [DECISIONS](DECISIONS.md) O8) |
| Final QA in Oxygen | Last manual review before publication |

---

## QA Dashboard

In addition to the production workflow, an automatically generated dashboard is available (`docs/index.html`):

- Pipeline status for all 15 pilot documents
- CER comparison between engines (Mistral, DeepSeek, LLM-corrected)
- Document catalog with engine filter
- Viewer with facsimile-OCR comparison (`docs/viewer.html`)

The dashboard replaces `docs/benchmark.html` and serves as the central QA tool.

---

## References

- [PROJEKT](PROJEKT.md) for project scope and milestones
- [PIPELINE](PIPELINE.md) for technical pipeline details
- [DECISIONS](DECISIONS.md) O8 (Alma metadata)

---

*Source: WorkflowDiagramm_Hersch.pdf -- fully transferred, PDF deleted*
*Created: 2026-01-29 | Updated: 2026-02-27*
