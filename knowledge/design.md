---
title: Design
project:
  name: zbz-ocr-tei
  repository: https://github.com/chpollin/zbz-ocr-tei.git
method:
  name: Promptotyping
  url: https://dhcraft.org/Promptotyping/
template:
  name: Vorlage Design
  version: 0.2
  url: https://dhcraft.org/Promptotyping/promptotyping-document/design
status: complete
language: en
version: 1.0
created: 2026-08-21
updated: 2026-08-21
authors: [Christopher Pollin]
related: [workflow, infrastructure, specification]
---

# Design

This document holds the rationale of the Hersch design system, the shape of its token and
component layer, the interaction patterns of the inspection and curation UI, and the rules
by which the UI turns data into visual signal. Token values live in
`docs/assets/css/tokens.css`, which is their only authority; what the viewer does with a
saved change or a status transition is described in [workflow.md](workflow.md).

## Design stance

The corpus is francophone philosophical print from the twentieth century, and the UI is a
working surface for people who read that print at the facsimile. The design system takes
its cue from the material rather than from a generic application palette. Surfaces are warm
paper tones and text is a warm anthracite that reads as printer's ink, so no pure black and
no pure white appear anywhere. The base font is a humanist serif from the francophone
typographic tradition, headings sit in a geometric sans as a formal counterpoint, and the
type scale is a minor third, which gives fine differentiation without loud size jumps.

Colour is restrained and carries meaning rather than decoration. Three accents exist, a
brick red as the primary, a Prussian blue as the secondary and an olive green as the
tertiary, plus a warm ochre for the middle state of the workflow traffic light and for
signals that ask for review. An accent marks an accent or a status indicator; it never
fills a surface, because a filled accent surface competes with the facsimile and with the
text panel, which are the two things the user is actually looking at. The theme is fixed to
light through `color-scheme: light` in the token catalogue, so a system set to dark mode
does not flip the surfaces; the working surface is paper-analogous and the scans are read
against a light ground.

Restraint extends to the information layer. Numbers ride in functional elements such as a bar,
a status dot or a result line, and explanation arrives on demand through a tooltip or a
folded legend. Stat cards and introductory explainer paragraphs stay out of the pages. The entity
overview page states this explicitly in its own comments, where stat cards, intro copy and
class-definition prose are named as deliberately absent after operator feedback.

## Design system

Values live in `docs/assets/css/tokens.css` as custom properties under the `--h-*` prefix.
Component CSS consumes those properties and never writes a colour, radius, spacing step or
font stack literally. The catalogue is grouped into palette, text colours, borders and
shadows, status colours for the layout region types, typography including the font stacks
and the type scale, spacing steps, layout dimensions, and a small
viewer-specific group. A block at the end forces the light theme even when the operating
system asks for dark mode.

The component layer sits in `docs/assets/css/base.css` and covers the reset, document and
heading typography, links, inline code, the screen-reader and skip-link utilities, buttons
with primary, ghost, icon and small variants, form inputs, badges with ok, warn and info
variants, cards, toasts with ok, warn and error variants, the site header and footer chrome,
the scrollbar styling, and the reduced-motion block. Page-specific CSS builds on top,
`viewer.css` for the viewer shell, facsimile overlay, TEI rendering and editor UI,
`catalog.css` for the corpus overview, `entity-overview.css` for the entity page. For a new
component the first question is whether a token or a `base.css` component already covers it.

Three web font families carry the system, each with a defined role. The humanist serif is
the reading font of body text and of the rendered TEI. The geometric sans carries headings
and UI chrome. A monospaced family carries code, XML source and identifier strings. All
three are vendored under `docs/assets/fonts/` as WOFF2 in the latin and latin-ext subsets
with their licence texts, declared in `docs/assets/css/fonts.css`, which contributes only
the `@font-face` rules while the font stacks stay in the token catalogue. The reasoning for
vendoring instead of linking a font host is in [infrastructure.md](infrastructure.md),
third-party resources section.

## Interaction patterns

The viewer is a static single-page app without a backend, built as IIFE modules in the
`ZBZ.*` namespace with no build pipeline, so every pattern below is plain DOM work against
tokens.

One document bar carries the identity of the open document, the workflow status pills per
data stream, the editor identity chip and the save control. The text panel header carries
two dropdown menus instead of scattered panel controls, a View menu that selects what the
panel shows and holds the markup-highlight toggle, and an Edit menu that switches the
editing target. A checked menu item carries the active state, which replaced the earlier
per-panel toggles. Page navigation sits in the facsimile panel header next to the region
count.

Both menus are keyboard operable. Opening a menu moves focus to its first item, arrow keys
move focus within the roving tabindex, Home and End jump to the ends, and Escape closes and
returns focus to the trigger. The dialog that explains the working-tree connection is a
native `<dialog>` opened with `showModal`, so modality, backdrop, focus containment and
Escape come from the platform rather than from hand-rolled code. Every page carries a skip
link that stays screen-reader-only until it takes focus and then becomes visible chrome. A
viewer who asks the system for less motion gets no transitions and no animations while the
states themselves stay, arriving without movement.

A status pill states the workflow status of one stream and cycles forward through the
status values on click; the traffic-light mapping and the meaning of each value are in
[workflow.md](workflow.md), workflow status section. An entity mark acts as a button and
opens a popover carrying label, category, life dates and the authority-file link; for a
mark the matcher actually set, the popover closes with three provenance rows read from the
mention itself, who asserted it, how certain the assertion is, and which rule produced the
hit. A candidate the tool held back opens the same popover with the reason for the reserve
and the origin of the matched name form, so an undecided position stays visibly undecided.

Layout editing works by direct manipulation on the facsimile, click to select, drag to move,
corner handles to resize, a toolbar dropdown for the region type, and drag and drop in the
region list for the reading order. Pointer events cover mouse, touch and pen, and arrow keys
nudge the selected region. Persistence is one shared Save button for all unsaved streams
plus an Export dropdown for per-stream single files; what a save writes and where is in
[workflow.md](workflow.md), persistence section.

## Visualization logic

The UI has four places where data becomes colour, and each uses the same token set.

Layout regions are drawn on the facsimile as rectangles coloured by region type, which maps
onto the pipeline tag vocabulary. Headings take the brick red, paragraphs the anthracite,
footnotes the Prussian blue, captions the olive green, and the two non-content classes,
filter and skip, take grey with a dashed and a dotted border, so a region marked for removal
is distinguishable from a real zone without reading its label. The mapping table is in
[workflow.md](workflow.md), layout editor section.

Workflow status is a dot, in the catalog table as a small dot per stream and in the viewer
as the dot inside the status pill. The unverified default is a muted grey rather than red,
because pipeline output exists for every document and its unverified state is a handover
default rather than an alarm; the in-progress state is the warm ochre and the verified state
the olive green. Red stays unassigned and is reserved for a future explicit problem state.
The catalog additionally carries a hollow outlined dot for a UI-only fourth token that has
no counterpart in the data model.

Entity categories are distinguished by accent, persons in Prussian blue, organisations in
olive green, works in brick red, while the review class of a mention rides on the ochre.
Certainty on the entity overview page is carried by a two-colour stacked bar, auto-marked
against review, with the corpus totals sitting on the same bar above the list, so a document
row and the corpus aggregate are read with the same visual grammar.

Inside the rendered TEI, signal is a border or a subtle background rather than a fill. The
entity colouring hangs on the annotated reading view and is therefore independent of the
markup toggle. The toggle adds the editorial layer, foreign-language spans in olive green
with a dotted underline, editorial corrections in brick red with a dashed one, footnotes
and bibliographic references in their own quiet marks, and it shows the legend that names
them; unclear passages keep a faint ochre ground in every view and gain a dotted underline
under the toggle. The method page presents its quality figures as tables rather than as
chart components, which keeps the numbers copyable and avoids a chart that would have to be
regenerated with every measurement.

## Connection to the action layer

CLAUDE.md, section Design, carries the imperative form of what this document argues, meaning
the short rules an agent generating UI code has to follow. Those imperatives are the action
layer and stay there; this document holds the reasoning behind them and CLAUDE.md the
imperatives.

`docs/assets/css/tokens.css` is the value authority. A concrete colour, radius, spacing
step, font stack or type-scale step is read from that file; this document names roles and
rules. A changed value is edited in the token catalogue and
propagates through the component layer; a changed rationale is edited in this document.
