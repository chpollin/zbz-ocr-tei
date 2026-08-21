---
title: "Integration: ZBZ, Transkribus, teiCrafter"
project:
  name: zbz-ocr-tei
  repository: https://github.com/chpollin/zbz-ocr-tei.git
method:
  name: Promptotyping
  url: https://dhcraft.org/Promptotyping/
template:
  name: Vorlage Integration
  version: 0.1
  url: https://dhcraft.org/Promptotyping/promptotyping-document/integration
counterpart: [ZBZ, Transkribus, teiCrafter]
direction: bidirectional
status: complete
language: en
version: 1.0
created: 2026-08-21
updated: 2026-08-21
authors: [Christopher Pollin]
related: [project, pipeline, workflow, tei-mapping, specification, plan, decisions]
---

# Integration: ZBZ, Transkribus, teiCrafter

This document holds the contracts between the pipeline of this repository and the three
systems it exchanges data with. Each contract has one side that owns it. This repository
owns the delivered TEI in `output/tei_final/` and the PAGE-XML bundle it builds for
Transkribus. ZBZ owns the editorial guidelines, the Masterfile, the reference TEIs and the
review of the delivery schema. The teiCrafter documentation owns the teiCrafter annotation
model, while the ZBZ rules prevail wherever the two disagree (O26/E88).

## Data flow

Every stream enters or leaves through a directory; no live service call connects the
counterparts. The pipeline stages that produce these streams are described in
[pipeline.md](pipeline.md), the end-to-end movement in [workflow.md](workflow.md).

### ZBZ

Inbound, as immutable input under `data/source/`, arrive the PDF scans, the Masterfile
(Excel) as the coordination record of the edition project, the reference TEIs, the
editorial guidelines, and a Transkribus PAGE-XML export of the objects ZBZ has already
worked on. The material side of these inputs is described in [data.md](data.md).

Outbound go the final TEI documents in `output/tei_final/`, each with its per-object
manifest, and the production state on the GitLab fork.

Edition production at ZBZ runs in three parallel tracks, and the pipeline enters the first
of them.

1. Transcription, from digitized images through Transkribus to GitLab, Oxygen and back to
   GitLab.
2. Metadata, from digitized images through Alma and the Masterfile to Swisscovery and the
   TEI header.
3. Correction loop, from Oxygen as PDF to external reviewers and back into Oxygen.

The Masterfile coordinates all three tracks. Almost every step is manual, the Transkribus
process is not standardized, external corrections travel as PDF rather than as XML, and
GND linking happens by hand in Oxygen. Since E21 the pipeline replaces or complements
three steps of the transcription track.

| Existing step at ZBZ | Replaced by the pipeline |
|---|---|
| Transkribus OCR | batch OCR over the delivered PDFs |
| Manual Transkribus export | automatic PAGE-XML export |
| Oxygen TEI markup | automatic TEI transformation |

The systems the tracks run on stay in ZBZ hands.

| System | Function | Format |
|---|---|---|
| Transkribus | OCR/HTR plus transcription | not standardized |
| Masterfile | workflow plus status | Excel |
| GitLab | TEI versioning | XML |
| Oxygen | TEI markup plus transformation | XML |
| Alma | cataloguing plus metadata | catalogue data |
| Swisscovery | discovery | catalogue data |
| GND | authority-data linking | identifiers |

The fork model carries the production state.

| Aspect | Details |
|---|---|
| Development repository | GitHub, `chpollin/zbz-ocr-tei` |
| Production repository | GitLab University of Zurich (fork) |
| Merge direction | GitHub to GitLab, upstream updates |
| Fork adjustments | API keys, endpoints, ZBZ-specific configuration |

### Transkribus

The working direction is outbound. Stage 4 writes standard PAGE-XML into
`output/page_xml/{doc}/page/`; `scripts/edition/transkribus_export.py` assembles it with
the page images into a bundle under `output/transkribus_upload/` (gitignored), and
`scripts/edition/transkribus_upload.py` sends the bundle to a Transkribus collection
(E81). This is the reverse of the viewer round trip, where curated edits come into the
pipeline.

The inbound PAGE-XML export ZBZ delivered has a single consumer, the export script, which
reads directory names from it to recognize the objects ZBZ already holds. No geometric or
structural comparison consumes it.

### teiCrafter

The handover is a manual file open. A curator opens a final TEI in teiCrafter and
annotates it there; no export bridge writes into teiCrafter and no import bridge reads its
output back into the pipeline. The only trace of teiCrafter in the code is a comment in
`scripts/tei/zbz_conformity.py` recording that the entity rules Z1 to Z4 and Z8 apply to
curated teiCrafter output, while the delivered stock is entity-free.

## Exchange format

### ZBZ

TEI P5 constrained by the project schema `data/schema/zbz_hersch.rng`. Every final TEI
carries a `<revisionDesc>` with the pipeline status (E42). `output/tei_final/{doc}_final.xml`
is the single source of truth of the delivered data (E43); `docs/data/` is a generated
mirror and is never edited directly. The element and attribute contract, including the
`<revisionDesc>` shape and the character normalizations, lives in
[tei-mapping.md](tei-mapping.md).

At the handover step `tei_status_marker.py` projects the per-stream workflow history from
the manifest into the `<revisionDesc>` as `<change>` entries (E66) and removes the stale
entries of the abolished agent screening. The status vocabulary and its semantics are
owned by [workflow.md](workflow.md), section Workflow Status per Stream. `unverifiziert`
is the handover default and states that the pipeline produced the stream deterministically
and that no human has released it. The neutral default follows from the pipeline producing
OCR, layout and TEI for every document, so the value describes the delivery state (E67).

### Transkribus

PAGE 2013-07-15, one folder per document, the image at the top level and the PAGE-XML of
the same base name in a `page/` subfolder.

```
{doc}/
  {doc}_p001.png          # image at top level
  page/{doc}_p001.xml     # PAGE-XML with matching name
```

The dialect is compatible out of the box, with `TextRegion`, `Coords`, `TextLine`,
`TextEquiv` and `ReadingOrder` plus `custom` structure types. The pipeline PAGE carries
line polygons and no baselines, which is sufficient for import, display and structure;
only HTR model training in Transkribus needs baselines, and the ZBZ originals carry them.
The pipeline images are 1240x1754 (150 dpi), the ZBZ originals 2479x3508 (300 dpi); each
state is internally consistent.

The upload runs over the legacy TrpServer REST API at `transkribus.eu/TrpServer/rest`,
with `POST /auth/login`, then `POST /uploads?collId=` carrying a JSON manifest with
`md.title` and `pageList`, then `PUT /uploads/{id}` with image and XML per page. Verified
on 2026-06-08, the legacy API writes correctly into a collection on the current platform
at `app.transkribus.org`; login and collection share the readcoop account. Authentication
uses the environment variables `TRANSKRIBUS_USER`, `TRANSKRIBUS_PASSWORD` and
`TRANSKRIBUS_COLLECTION`, never values in code, repository or `.env`.

### teiCrafter

TEI with inline GND markup at the mention site, every mention carrying `ref="GND:..."`.
The delivery model admits persons, organisations and works, and excludes a standOff
register, places, events and identifiers from GeoNames or Wikidata (E88). The full target
model, the provenance attributes and the tier rules are in
[tei-mapping.md](tei-mapping.md).

## Responsibilities

### ZBZ

ZBZ owns Alma cataloguing, Masterfile maintenance, Swisscovery assignment, the TEI header
fields drawn from Alma, the manual GND linking in Oxygen, and the final quality assurance
in Oxygen before publication. ZBZ also owns the editorial guidelines and their
interpretation, so every question about what the guidelines require is decided there.

### Transkribus

The platform side belongs to ZBZ, which holds the account and the target collection. This
repository owns the bundle it produces and the upload run it triggers.

### teiCrafter

teiCrafter owns its annotation model and its documentation. This repository owns the TEI
that goes in and the conformity rules that judge what comes back.

## Acceptance criteria

### ZBZ

A delivered document is accepted when it validates against `data/schema/zbz_hersch.rng`,
carries a `<revisionDesc>` with the pipeline status, and carries the projected workflow
history at handover. The gates that enforce this and the way they are run are in
[testing.md](testing.md); the requirement view is in [specification.md](specification.md).

### Transkribus

Before a bundle is uploaded, the export verifies for every page that the PNG pixel
dimensions match the declared `imageWidth` and `imageHeight`, so that coordinates stay
aligned; pages without an image or with dimension drift are reported instead of being
copied silently. The export runs over the PAGE-XML rather than over the images, so pages
without layout, blank pages among them, stay out of the bundle. An upload run is preceded
by `--dry-run`, which checks login and collection access, and by `--doc` on a single test
object.

### teiCrafter

Epic D of [specification.md](specification.md) states the acceptance from the annotator
side, a TEI stable enough for control and inline-GND annotation. The entity rules Z1 to Z4
and Z8 of `zbz_conformity.py` turn sharp on curated teiCrafter output, while Z5
(renderings) and Z6 (`pb facs/n`) already apply to the delivered stock.

## Open points and input gaps

### ZBZ

- O8, header metadata from Alma including the MMSID. The editorial guidelines demand these
  fields, and the decision of 2026-06-08 places them in the ZBZ domain outside the
  OCR/layout/TEI pipeline. A projection was built with E69, removed with E76 and rejected
  again with E83. Open with ZBZ is who pulls from Alma and which fields. While it is open,
  most delivered headers carry an empty container title by intent.
- O13, TEI editorial details such as subject headings. The guidelines call the point
  unsettled. Until it is decided the headers stay without subject headings, which blocks
  no pipeline step.
- The reference TEI of document 1520 is not well-formed, with three structurally identical
  crossed `item`/`p` nestings. The repair swaps the closing-tag order at each spot and
  leaves the text content unchanged, and the corrected copy
  `output/1520_reference_fixed.xml` parses cleanly. The original stays untouched as the
  ZBZ source datum and the correction goes to ZBZ as a proposal; pending is only the
  ZBZ-side repair of the reference file.
- R5, fork divergence between DHCraft and ZBZ, is open because the merge strategy for
  upstream changes into the GitLab fork is undefined and `.gitlab-ci.yml` does not exist.
  The item is tracked in [plan.md](plan.md).

### Transkribus

R7, PAGE-XML incompatibility, is partly resolved by E23 and E81. The schema version, the
id scheme `{NNNN}_p{NNN}` and the image format are settled; `@type` and `@custom` remain
unverifiable, because the delivered TextRegions came empty and offer nothing to compare
against.

### teiCrafter

- No export or import bridge exists, so the handover stays a manual file open until one
  side builds a bridge.
- The teiCrafter output-model switch to the inline-GND delivery model is pending, and Epic
  D stays cross-lane until it happens.
- O27, the ZBZ README contradicts itself on captions. The register section says entities
  in captions are not tagged, while the figures example tags an `<orgName ref="GND:...">`
  inside a `<figure>`. The open question is whether the ban covers the caption `<head>` or
  the whole `<figure>` block including its explanatory `<p>`. ZBZ decides. The rule is
  deliberately not machine-enforced while the contradiction stands, and it has no effect
  on the entity-free delivered stock.

## Corrections and pitfalls

Uploading the reference objects again creates duplicates. Every upload run creates new
documents and the API performs no deduplication, which is why `--reference` exists as a
separate selection and why a full run is preceded by a single test object.

The reference TEIs are partial transcriptions with an empty header and local flaws, so
reference-based checks measure against a ground truth that is guideline-true in the body
and locally defective elsewhere. The exception catalog in [data.md](data.md) belongs in
every scoring logic that consumes them.

The GND prefix and the `corresp`/`ref` split of the reference TEIs drift from the delivery
model, which matters for the teiCrafter lane. The reference practice serves as a model
only after normalization.

The resolution difference between the pipeline images and the ZBZ originals is deliberate.
Each state is internally consistent, so a bundle must never carry images of one resolution
with coordinates computed on the other.

Credentials for Transkribus live in environment variables and nowhere else. The variable
names are documented, the values never appear in code, repository, documentation or
`.env`.

## Authoritative documents

- [pipeline.md](pipeline.md): stages, engines and the PAGE-XML production
- [workflow.md](workflow.md): end-to-end data flow, viewer, persistence, status per stream
- [tei-mapping.md](tei-mapping.md): the TEI element and attribute contract, entity target model
- [specification.md](specification.md): requirements, epics, sources of authority
- [data.md](data.md): delivered input material, reference corpus, exception catalog
- [testing.md](testing.md): the gates that enforce the delivery contract
- [plan.md](plan.md): open decisions and deferred items
- [decisions.md](decisions.md): dated rationale for E21, E42, E43, E66, E81 and E88
- [infrastructure.md](infrastructure.md): deployment, GitHub Pages, GitLab CI state
- [../CLAUDE.md](../CLAUDE.md): the CLI reference for export and upload, and the security rule

## Re-entry context

The ZBZ contract is live and running. The pipeline delivers final TEI that validates
against the project schema, and the items still open there are editorial questions for ZBZ
rather than pipeline work. The Transkribus contract is built and verified end to end, with
one test object uploaded successfully; a full run is an operator decision. The teiCrafter
contract is specified and not yet exercised, because the annotation model on the
teiCrafter side has not switched to inline GND and no bridge exists in either direction.

Anyone resuming this lane reads [specification.md](specification.md) for what the delivery
must satisfy, [tei-mapping.md](tei-mapping.md) for how the markup is shaped, and
[plan.md](plan.md) for what is deferred and who decides it.
