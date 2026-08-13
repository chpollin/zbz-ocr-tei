/* Entity overview: completeness and certainty instrument over the annotation layer.
   Primary view aggregates per listed entity (zero-mention entries first, the
   "do we have all" check); secondary view aggregates per document.
   Data: data/entity_overview.json + data/catalog.json (titles). Read-only;
   all text reaches the DOM via textContent, icons are built as SVG nodes.
   Every icon, chip, count and bar segment carries its explanation as a title
   attribute; where an icon carries information no adjacent text repeats, it also
   carries an accessible name. */

window.ZBZ = window.ZBZ || {};

ZBZ.EntityOverview = (() => {
  'use strict';

  const state = {
    view: 'entities',      // 'entities' | 'documents'
    entityRows: [],
    byGid: {},             // gid -> entity row, built once after load
    docRows: [],
    classes: [],
    titles: {},            // doc id -> {title, author, date}
    query: '',
    sort: { entities: 'zero', documents: 'id' },
    filter: { entities: 'all', documents: 'all' },
  };

  const CATEGORY_LABELS = {
    person: 'Person', organisation: 'Organisation', work: 'Work',
  };

  const TIPS = {
    auto: 'Auto-marked mentions are tier 1 of the matcher, the layer the adjudicated '
      + 'precision covers.',
    review: 'Review candidates are tier 2, held on the worklist until a human or a '
      + 'calibrated judge decides them.',
    mentions: 'Every candidate the corpus scan reports, auto-marked plus review.',
    ambiguity: 'An ambiguous surface names every listed entity that could carry it. '
      + 'The overview counts a mention for the reported bearer only, so these '
      + 'mentions are missing from the counts of the other possible bearers.',
    found: 'Curated list entries with at least one reported mention. The remainder '
      + 'is either absent from the corpus or hidden behind an ambiguous surface.',
    sample: 'Facsimile-adjudicated sample of the annotation layer, drawn seeded and '
      + 'stratified (method in knowledge/entity-evaluation.md). It measures the drawn '
      + 'cases, it does not count the corpus.',
  };

  const SORTS = {
    entities: [
      ['zero', 'Sort: Fewest mentions first'],
      ['mentions', 'Sort: Most mentions'],
      ['name', 'Sort: Name'],
      ['docs', 'Sort: Most documents'],
    ],
    documents: [
      ['id', 'Sort: Document ID'],
      ['mentions', 'Sort: Most mentions'],
      ['reviewshare', 'Sort: Highest review share'],
      ['auto', 'Sort: Most auto-marked'],
    ],
  };

  const FILTERS = {
    entities: [
      ['all', 'All listed entities'],
      ['none', 'Without any mention'],
      ['noauto', 'Review-only (never auto-marked)'],
      ['person', 'Persons'],
      ['organisation', 'Organisations'],
      ['work', 'Works'],
    ],
    documents: [
      ['all', 'All documents'],
      ['review', 'With review candidates'],
      ['none', 'Without mentions'],
    ],
  };

  const el = (tag, className, text) => {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = text;
    return node;
  };

  // ------------------------------------------------------------ icons
  /* Monochrome 16x16 glyphs drawn in currentColor. Shape carries the distinction,
     colour never does it alone. Each entry is a list of [tag, attributes]. */

  const SVG_NS = 'http://www.w3.org/2000/svg';
  const FILLED = { fill: 'currentColor', stroke: 'none' };

  const ICONS = {
    person: [['circle', { cx: 8, cy: 5.4, r: 2.6 }],
             ['path', { d: 'M3 13.6c0-2.6 2.2-4.4 5-4.4s5 1.8 5 4.4' }]],
    organisation: [['path', { d: 'M2.5 13.5h11' }],
                   ['path', { d: 'M4 13.5V6l4-2.6L12 6v7.5' }],
                   ['path', { d: 'M7 13.5v-3.2h2v3.2' }]],
    work: [['path', { d: 'M8 4.4C6.6 3.3 5 2.9 3.2 3.1v8.6c1.8-.2 3.4.2 4.8 1.3' }],
           ['path', { d: 'M8 4.4c1.4-1.1 3-1.5 4.8-1.3v8.6c-1.8-.2-3.4.2-4.8 1.3' }],
           ['path', { d: 'M8 4.4V13' }]],
    ambiguous: [['path', { d: 'M8 13.6V8.6' }], ['path', { d: 'M8 8.6 4.6 5.2' }],
                ['path', { d: 'M8 8.6 11.4 5.2' }],
                ['circle', Object.assign({ cx: 4.2, cy: 4, r: 1.3 }, FILLED)],
                ['circle', Object.assign({ cx: 11.8, cy: 4, r: 1.3 }, FILLED)]],
    suspect: [['path', { d: 'M4 14V2.6' }],
              ['path', { d: 'M4 3.4h7.6L10 5.9l1.6 2.5H4' }]],
    unanchored: [['path', { d: 'M7 9 4.8 11.2a2.5 2.5 0 0 1-3.5-3.5L3.5 5.5' }],
                 ['path', { d: 'M9 7l2.2-2.2a2.5 2.5 0 0 1 3.5 3.5L12.5 10.5' }]],
    running_head: [['rect', { x: 3, y: 2.5, width: 10, height: 11, rx: 1 }],
                   ['rect', Object.assign({ x: 5, y: 4.4, width: 6, height: 1.5,
                                            rx: 0.7 }, FILLED)],
                   ['path', { d: 'M5 8.6h6M5 11h4' }]],
    bibliography: [['path', { d: 'M6.6 2.6H4v10.8h2.6' }],
                   ['path', { d: 'M9.4 2.6H12v10.8H9.4' }]],
    figure: [['rect', { x: 2.5, y: 3.5, width: 11, height: 9, rx: 1 }],
             ['circle', Object.assign({ cx: 6, cy: 6.8, r: 1.1 }, FILLED)],
             ['path', { d: 'M3.2 11.6 6.6 8.6l2.4 2 2-1.6 2.3 2' }]],
    derived: [['path', { d: 'M3 4h3.6c2.2 0 3.4 1.3 3.4 3.5V11' }],
              ['path', { d: 'M7.6 9 10 11.6 12.4 9' }]],
    markup: [['path', { d: 'M6 3.4 2.6 8 6 12.6' }],
             ['path', { d: 'M10 3.4 13.4 8 10 12.6' }]],
    short_title: [['path', { d: 'M8.6 2.6H13.4V7.4L7.4 13.4 2.6 8.6z' }],
                  ['circle', Object.assign({ cx: 10.9, cy: 5.1, r: 1 }, FILLED)]],
    other: [['circle', Object.assign({ cx: 4, cy: 8, r: 1.2 }, FILLED)],
            ['circle', Object.assign({ cx: 8, cy: 8, r: 1.2 }, FILLED)],
            ['circle', Object.assign({ cx: 12, cy: 8, r: 1.2 }, FILLED)]],
    marked: [['circle', { cx: 8, cy: 8, r: 5.2 }],
             ['circle', Object.assign({ cx: 8, cy: 8, r: 1.9 }, FILLED)]],
    worklist: [['circle', { cx: 7, cy: 7, r: 4.2 }],
               ['path', { d: 'M10.1 10.1 14 14' }]],
    sample: [['rect', { x: 3.5, y: 3, width: 9, height: 10.5, rx: 1 }],
             ['path', { d: 'M6 6.4h4M6 9h4M6 11.6h2.4' }]],
    precision: [['circle', { cx: 8, cy: 8, r: 5.4 }],
                ['circle', { cx: 8, cy: 8, r: 2.4 }],
                ['circle', Object.assign({ cx: 8, cy: 8, r: 0.9 }, FILLED)]],
    recall: [['path', { d: 'M2.6 3.6h10.8L9.2 8.8v4.2l-2.4 1.2V8.8z' }]],
    agreement: [['circle', { cx: 6.2, cy: 8, r: 3.7 }],
                ['circle', { cx: 9.8, cy: 8, r: 3.7 }]],
  };

  const icon = (name, accessibleName) => {
    const svg = document.createElementNS(SVG_NS, 'svg');
    svg.setAttribute('class', `eo-icon eo-icon--${name}`);
    svg.setAttribute('viewBox', '0 0 16 16');
    svg.setAttribute('fill', 'none');
    svg.setAttribute('stroke', 'currentColor');
    svg.setAttribute('stroke-width', '1.4');
    svg.setAttribute('stroke-linecap', 'round');
    svg.setAttribute('stroke-linejoin', 'round');
    if (accessibleName) {
      svg.setAttribute('role', 'img');
      const title = document.createElementNS(SVG_NS, 'title');
      title.textContent = accessibleName;
      svg.appendChild(title);
    } else {
      svg.setAttribute('aria-hidden', 'true');
    }
    (ICONS[name] || ICONS.other).forEach(([tag, attrs]) => {
      const shape = document.createElementNS(SVG_NS, tag);
      Object.entries(attrs).forEach(([key, value]) => {
        shape.setAttribute(key, String(value));
      });
      svg.appendChild(shape);
    });
    return svg;
  };

  /* An explainer that is reachable by keyboard: the title shows on hover, the
     accessible name carries the same sentence for assistive technology. */
  const explain = (node, tip, { focusable = false } = {}) => {
    node.title = tip;
    if (focusable) {
      node.tabIndex = 0;
      node.setAttribute('role', 'img');
      node.setAttribute('aria-label', `${node.textContent}. ${tip}`);
    }
    return node;
  };

  const num = (value) => value.toLocaleString('en-GB');

  const percent = (rate) => `${(rate * 100).toFixed(1)} %`;

  const fold = (value) => (value || '')
    .normalize('NFD').replace(/[̀-ͯ]/g, '')
    .toLowerCase()
    .replace(/ä/g, 'ae').replace(/ö/g, 'oe')
    .replace(/ü/g, 'ue').replace(/ß/g, 'ss');

  // ------------------------------------------------------------ data loading

  const load = async () => {
    const [overview, catalog] = await Promise.all([
      fetch('data/entity_overview.json').then((r) => r.json()),
      fetch('data/catalog.json').then((r) => r.json()),
    ]);
    state.classes = overview.classes;
    catalog.documents.forEach((doc) => {
      state.titles[doc.id] = { title: doc.title || '', author: doc.author || '',
                               date: doc.date || '' };
    });
    state.entityRows = Object.entries(overview.entities).map(([gid, e]) => ({
      gid,
      label: e.label,
      category: e.category,
      auto: e.auto,
      review: e.review,
      total: e.auto + e.review,
      classes: e.classes || {},
      altOnly: e.alternative_only || 0,
      docs: e.docs,
      ndocs: Object.keys(e.docs).length,
      search: fold(`${gid} ${e.label}`),
    }));
    state.byGid = Object.fromEntries(state.entityRows.map((row) => [row.gid, row]));
    state.docRows = catalog.documents.map((doc) => {
      const record = overview.documents[doc.id] ||
        { auto: 0, review: 0, classes: {}, entities: [] };
      return {
        id: doc.id,
        title: doc.title || '',
        author: doc.author || '',
        date: doc.date || '',
        auto: record.auto,
        review: record.review,
        total: record.auto + record.review,
        classes: record.classes || {},
        entities: record.entities || [],
        search: fold(`${doc.id} ${doc.title} ${doc.author}`),
      };
    });
    renderCorpusBar(overview.totals);
    renderQuality(overview.quality || {}, overview.provenance || {});
    render();
  };

  // ------------------------------------------------------------ corpus bar

  const renderCorpusBar = (totals) => {
    const total = totals.mentions;
    const autoSeg = document.getElementById('eo-corpus-auto');
    const reviewSeg = document.getElementById('eo-corpus-review');
    if (total) {
      autoSeg.style.width = `${(totals.auto / total) * 100}%`;
      reviewSeg.style.width = `${(totals.review / total) * 100}%`;
    }
    autoSeg.title = `${num(totals.auto)} auto-marked mentions. ${TIPS.auto}`;
    reviewSeg.title = `${num(totals.review)} review candidates. ${TIPS.review}`;
    document.getElementById('eo-corpus-bar').setAttribute('aria-label',
      `${num(totals.auto)} auto-marked and ${num(totals.review)} review mentions`);

    const totalLabel = document.getElementById('eo-corpus-total');
    totalLabel.textContent = `${num(total)} mentions in ${num(totals.documents)} `
      + 'documents';
    explain(totalLabel, `${TIPS.mentions} ${num(totals.ambiguous_mentions)} of them `
      + 'name more than one possible bearer of the surface.', { focusable: true });

    const legend = (chipId, labelId, iconName, text, tip) => {
      document.getElementById(labelId).textContent = text;
      const chip = document.getElementById(chipId);
      chip.prepend(icon(iconName));
      explain(chip, tip, { focusable: true });
    };
    legend('eo-legend-auto', 'eo-corpus-label-auto', 'marked',
           `${num(totals.auto)} auto-marked`, TIPS.auto);
    legend('eo-legend-review', 'eo-corpus-label-review', 'worklist',
           `${num(totals.review)} review candidates`, TIPS.review);

    const found = document.getElementById('eo-corpus-found');
    found.textContent = `${totals.entities_found} of ${totals.listed_entities} `
      + 'listed entities found';
    found.className = 'badge '
      + (totals.entities_found === totals.listed_entities ? 'badge--ok' : 'badge--warn');
    explain(found, `${TIPS.found} ${totals.entities_alternative_only} of the `
      + 'unmatched entries appear only as an alternative bearer of an ambiguous '
      + 'surface.', { focusable: true });
  };

  // ------------------------------------------------------------ quality strip

  const qualityItem = (iconName, text, tip) => {
    const item = el('span', 'eo-quality__item');
    item.appendChild(icon(iconName));
    item.appendChild(el('span', '', text));
    return explain(item, tip, { focusable: true });
  };

  const renderQuality = (quality, provenance) => {
    const strip = document.getElementById('eo-quality');
    strip.textContent = '';
    const precision = quality.precision;
    const recall = quality.recall;
    if (!precision || !recall) return;

    strip.appendChild(qualityItem('sample',
      `Adjudicated sample ${quality.snapshot}`,
      `${TIPS.sample} Scan snapshot ${(provenance.scan_sha256 || '').slice(0, 12)}, `
      + `${num(provenance.scan_candidates || 0)} candidates over `
      + `${provenance.listed_entities || 0} listed entities.`));

    const ci = precision.ci95
      ? `, CI ${(precision.ci95[0] * 100).toFixed(1)} to `
        + `${(precision.ci95[1] * 100).toFixed(1)}` : '';
    strip.appendChild(qualityItem('precision',
      `Precision ${percent(precision.rate)} on ${precision.decidable} `
      + `of ${precision.n} drawn marks${ci}`,
      `${precision.correct} of ${precision.decidable} decidable marks were judged `
      + `correct at the facsimile; ${precision.distribution.undecidable || 0} `
      + 'undecidable marks stay out of numerator and denominator. The interval is a '
      + `${precision.ci_method}. The rate holds for the drawn marks, the corpus is `
      + 'not counted.'));

    const status = recall.status || {};
    strip.appendChild(qualityItem('recall',
      `Recall ${status.hit || 0} marked of ${recall.mentions} mentions read`,
      'Exhaustive reading of the drawn recall pages against the curated list found '
      + `${status.hit || 0} marked, ${status.on_worklist || 0} on the worklist and `
      + `${status.missed || 0} missed. Coverage (marked or on the worklist) `
      + `${percent(recall.coverage_hit_or_worklist)}. `
      + `${recall.pages_with_mentions} of the drawn pages carried a mention.`));

    const agreement = quality.agreement || {};
    if (agreement.n) {
      const cases = (agreement.disagreements || [])
        .map((d) => `${d.case} ${d.surface} (${d.verdict} against ${d.second_verdict})`)
        .join('; ');
      strip.appendChild(qualityItem('agreement',
        `Second judgment ${agreement.agree} of ${agreement.n} agree`,
        'Blind second adjudication of a subsample; raw agreement '
        + `${percent(agreement.rate)}. `
        + (cases ? `The judgments differed on ${cases}.`
                 : 'No judgment differed.')));
    }
  };

  // ------------------------------------------------------------ filtering + sorting

  const visibleEntityRows = () => {
    let rows = state.entityRows;
    if (state.query) rows = rows.filter((r) => r.search.includes(state.query));
    const filter = state.filter.entities;
    if (filter === 'none') rows = rows.filter((r) => r.total === 0);
    if (filter === 'noauto') rows = rows.filter((r) => r.auto === 0 && r.review > 0);
    if (['person', 'organisation', 'work'].includes(filter)) {
      rows = rows.filter((r) => r.category === filter);
    }
    const byLabel = (a, b) => a.label.localeCompare(b.label, 'de');
    const sorters = {
      zero: (a, b) => a.total - b.total || byLabel(a, b),
      mentions: (a, b) => b.total - a.total || byLabel(a, b),
      name: byLabel,
      docs: (a, b) => b.ndocs - a.ndocs || byLabel(a, b),
    };
    return [...rows].sort(sorters[state.sort.entities] || sorters.zero);
  };

  const visibleDocRows = () => {
    let rows = state.docRows;
    if (state.query) rows = rows.filter((r) => r.search.includes(state.query));
    const filter = state.filter.documents;
    if (filter === 'review') rows = rows.filter((r) => r.review > 0);
    if (filter === 'none') rows = rows.filter((r) => r.total === 0);
    const share = (r) => (r.total ? r.review / r.total : -1);
    const sorters = {
      id: (a, b) => Number(a.id) - Number(b.id),
      mentions: (a, b) => b.total - a.total || Number(a.id) - Number(b.id),
      reviewshare: (a, b) => share(b) - share(a) || b.review - a.review,
      auto: (a, b) => b.auto - a.auto || Number(a.id) - Number(b.id),
    };
    return [...rows].sort(sorters[state.sort.documents] || sorters.id);
  };

  // ------------------------------------------------------------ rendering

  const render = () => {
    const list = document.getElementById('eo-list');
    list.textContent = '';
    const fragment = document.createDocumentFragment();
    if (state.view === 'entities') {
      const rows = visibleEntityRows();
      const zero = rows.filter((r) => r.total === 0);
      const alt = zero.filter((r) => r.altOnly > 0).length;
      const count = document.getElementById('eo-result-count');
      count.textContent = `${rows.length} of ${state.entityRows.length} entities`
        + (zero.length ? ` · ${zero.length} without any mention` : '')
        + (alt ? ` (${alt} only as alternative)` : '');
      count.title = zero.length
        ? 'Entries without a reported mention are the completeness signal; those '
          + `named only as an alternative bearer are counted apart. ${TIPS.ambiguity}`
        : 'Every listed entity in the current filter carries a reported mention.';
      rows.forEach((row) => fragment.appendChild(renderEntity(row)));
      if (!rows.length) fragment.appendChild(emptyNote());
    } else {
      const rows = visibleDocRows();
      document.getElementById('eo-result-count').textContent =
        `${rows.length} of ${state.docRows.length} documents`;
      rows.forEach((row) => fragment.appendChild(renderDoc(row)));
      if (!rows.length) fragment.appendChild(emptyNote());
    }
    list.appendChild(fragment);
  };

  const emptyNote = () => el('p', 'eo-empty', 'Nothing matches the current filter.');

  const renderBar = (auto, review) => {
    const total = auto + review;
    const bar = el('span', 'eo-bar');
    bar.setAttribute('role', 'img');
    bar.setAttribute('aria-label', total
      ? `${auto} auto-marked, ${review} review` : 'no mentions');
    bar.title = total
      ? `Certainty split of ${num(total)} mentions: ${num(auto)} auto-marked, `
        + `${num(review)} on review.`
      : 'No mention reports this entity.';
    if (total) {
      const autoSeg = el('span', 'eo-bar__auto');
      autoSeg.style.width = `${(auto / total) * 100}%`;
      autoSeg.title = `${num(auto)} auto-marked. ${TIPS.auto}`;
      const reviewSeg = el('span', 'eo-bar__review');
      reviewSeg.style.width = `${(review / total) * 100}%`;
      reviewSeg.title = `${num(review)} review candidates. ${TIPS.review}`;
      bar.appendChild(autoSeg);
      bar.appendChild(reviewSeg);
    }
    return bar;
  };

  const counts = (auto, review) => {
    const span = el('span', 'eo-doc__counts');
    span.appendChild(el('strong', '', String(auto)));
    span.appendChild(document.createTextNode(' auto · '));
    span.appendChild(el('em', '', String(review)));
    span.appendChild(document.createTextNode(' review'));
    span.title = `${num(auto)} auto-marked, ${num(review)} on review. ${TIPS.auto} `
      + TIPS.review;
    return span;
  };

  /* Review class breakdown, the same chips in the entity and the document view. */
  const classChips = (classes) => {
    const chips = el('div', 'eo-chips');
    state.classes.forEach((cls) => {
      const count = classes[cls.key];
      if (!count) return;
      const chip = el('span', 'eo-chip');
      chip.appendChild(icon(cls.key));
      chip.appendChild(el('span', '', `${cls.label} ${count}`));
      explain(chip, `${cls.label} (${count} review candidates). `
        + cls.description.charAt(0).toUpperCase() + cls.description.slice(1) + '.',
        { focusable: true });
      chips.appendChild(chip);
    });
    return chips;
  };

  const categoryIcon = (category) => icon(category, CATEGORY_LABELS[category]
    || 'Unknown category');

  // --- entity view

  const renderEntity = (row) => {
    const details = el('details', 'eo-doc');
    const summary = el('summary', 'eo-doc__summary eo-doc__summary--entity');

    const name = el('span', 'eo-doc__title');
    name.appendChild(categoryIcon(row.category));
    name.appendChild(document.createTextNode(row.label));
    const gid = el('span', 'eo-doc__meta', ` ${row.gid}`);
    gid.title = `GND identifier of this list entry (${CATEGORY_LABELS[row.category]
      || 'entry'}).`;
    name.appendChild(gid);
    summary.appendChild(name);

    summary.appendChild(reachLabel(row));
    summary.appendChild(counts(row.auto, row.review));
    summary.appendChild(renderBar(row.auto, row.review));

    details.appendChild(summary);
    details.addEventListener('toggle', () => {
      if (details.open && !details.dataset.rendered) {
        details.appendChild(renderEntityBody(row));
        details.dataset.rendered = '1';
      }
    });
    return details;
  };

  /* An entity with no reported mention may still be a possible bearer of an
     ambiguous surface, so "not found" is only said where nothing names it. */
  const reachLabel = (row) => {
    if (row.ndocs) {
      const label = el('span', 'eo-doc__meta',
                       `${row.ndocs} doc${row.ndocs === 1 ? '' : 's'}`);
      return explain(label, `Reported in ${row.ndocs} document`
        + `${row.ndocs === 1 ? '' : 's'} of the corpus scan.`);
    }
    if (row.altOnly) {
      const label = el('span', 'eo-doc__meta eo-doc__meta--alt', 'only as alternative');
      label.prepend(icon('ambiguous'));
      return explain(label, `No mention reports this entity, but ${row.altOnly} `
        + `mention${row.altOnly === 1 ? '' : 's'} name it as a possible bearer of an `
        + `ambiguous surface. ${TIPS.ambiguity}`);
    }
    return explain(el('span', 'eo-doc__meta', 'not found'),
                   'No candidate of the corpus scan names this list entry, neither as '
                   + 'the reported bearer nor as an alternative.');
  };

  const ambiguityNote = (row) => {
    const note = el('p', 'eo-note');
    note.appendChild(icon('ambiguous'));
    note.appendChild(el('span', '', `Named as a possible bearer in ${row.altOnly} `
      + `further mention${row.altOnly === 1 ? '' : 's'}, where another listed entity `
      + 'is the reported bearer.'));
    return explain(note, TIPS.ambiguity);
  };

  const renderEntityBody = (row) => {
    const body = el('div', 'eo-doc__body');
    const facts = el('p', 'eo-facts');
    facts.appendChild(icon(row.category));
    facts.appendChild(el('span', '', CATEGORY_LABELS[row.category] || 'Unknown'));
    facts.appendChild(el('span', 'eo-doc__id', row.gid));
    body.appendChild(facts);
    if (row.altOnly) body.appendChild(ambiguityNote(row));
    if (row.review) body.appendChild(classChips(row.classes));

    const docIds = Object.keys(row.docs);
    if (!docIds.length) {
      body.appendChild(el('p', 'eo-empty',
        'No mention found in the corpus (list entry unmatched).'));
      return body;
    }
    const table = el('table', 'eo-table');
    const head = el('thead');
    const headRow = el('tr');
    ['Document', 'Auto', 'Review', ''].forEach((label, i) => {
      const th = el('th', i === 1 || i === 2 ? 'eo-num' : '', label);
      th.scope = 'col';
      if (i === 1) th.title = TIPS.auto;
      if (i === 2) th.title = TIPS.review;
      headRow.appendChild(th);
    });
    head.appendChild(headRow);
    table.appendChild(head);
    const tbody = el('tbody');
    docIds.forEach((docId) => {
      const [auto, review] = row.docs[docId];
      const info = state.titles[docId] || {};
      const tr = el('tr');
      const cell = el('td');
      cell.appendChild(el('span', 'eo-doc__id', docId));
      cell.appendChild(document.createTextNode(`  ${info.title || ''}`));
      tr.appendChild(cell);
      tr.appendChild(el('td', 'eo-num', String(auto)));
      tr.appendChild(el('td', 'eo-num', String(review)));
      const linkCell = el('td', 'eo-num');
      const link = el('a', '', 'open');
      link.href = `viewer.html?doc=${encodeURIComponent(docId)}`;
      linkCell.appendChild(link);
      tr.appendChild(linkCell);
      tbody.appendChild(tr);
    });
    table.appendChild(tbody);
    body.appendChild(table);
    return body;
  };

  // --- document view

  const renderDoc = (row) => {
    const details = el('details', 'eo-doc');
    const summary = el('summary', 'eo-doc__summary');
    summary.appendChild(el('span', 'eo-doc__id', row.id));

    const title = el('span', 'eo-doc__title', row.title);
    const meta = [row.author, row.date].filter(Boolean).join(', ');
    if (meta) title.appendChild(el('span', 'eo-doc__meta', ` ${meta}`));
    summary.appendChild(title);

    summary.appendChild(counts(row.auto, row.review));
    summary.appendChild(renderBar(row.auto, row.review));

    details.appendChild(summary);
    details.addEventListener('toggle', () => {
      if (details.open && !details.dataset.rendered) {
        details.appendChild(renderDocBody(row));
        details.dataset.rendered = '1';
      }
    });
    return details;
  };

  const renderDocBody = (row) => {
    const body = el('div', 'eo-doc__body');

    if (row.review > 0) body.appendChild(classChips(row.classes));

    if (row.entities.length) {
      body.appendChild(renderDocEntityTable(row));
    } else {
      body.appendChild(el('p', 'eo-empty', 'No entity mentions found.'));
    }

    const actions = el('p', 'eo-doc__actions');
    const link = el('a', 'btn btn--ghost', 'Open in the viewer');
    link.href = `viewer.html?doc=${encodeURIComponent(row.id)}`;
    actions.appendChild(link);
    body.appendChild(actions);
    return body;
  };

  const renderDocEntityTable = (row) => {
    const table = el('table', 'eo-table');
    const head = el('thead');
    const headRow = el('tr');
    ['Entity', 'Auto', 'Review', 'Review classes'].forEach((label, i) => {
      const th = el('th', i === 1 || i === 2 ? 'eo-num' : '', label);
      th.scope = 'col';
      if (i === 1) th.title = TIPS.auto;
      if (i === 2) th.title = TIPS.review;
      headRow.appendChild(th);
    });
    head.appendChild(headRow);
    table.appendChild(head);
    const tbody = el('tbody');
    row.entities.forEach((entity) => {
      const info = state.byGid[entity.gid] || {};
      const tr = el('tr');
      const name = el('td');
      name.appendChild(categoryIcon(info.category || 'other'));
      name.appendChild(document.createTextNode(info.label || entity.gid));
      tr.appendChild(name);
      tr.appendChild(el('td', 'eo-num', String(entity.auto)));
      tr.appendChild(el('td', 'eo-num', String(entity.review)));
      const cell = el('td');
      cell.appendChild(classChips(entity.classes));
      tr.appendChild(cell);
      tbody.appendChild(tr);
    });
    table.appendChild(tbody);
    return table;
  };

  // ------------------------------------------------------------ wiring

  const fillSelect = (select, options, current) => {
    select.textContent = '';
    options.forEach(([value, label]) => {
      const option = el('option', '', label);
      option.value = value;
      select.appendChild(option);
    });
    select.value = current;
  };

  const applyView = () => {
    const isEntities = state.view === 'entities';
    document.getElementById('eo-view-entities')
      .setAttribute('aria-pressed', String(isEntities));
    document.getElementById('eo-view-documents')
      .setAttribute('aria-pressed', String(!isEntities));
    document.getElementById('eo-search').placeholder = isEntities
      ? 'Search by name or GND id…' : 'Search by ID, title, author…';
    fillSelect(document.getElementById('eo-sort'), SORTS[state.view],
               state.sort[state.view]);
    fillSelect(document.getElementById('eo-filter'), FILTERS[state.view],
               state.filter[state.view]);
    render();
  };

  const init = () => {
    document.getElementById('eo-view-entities').addEventListener('click', () => {
      state.view = 'entities';
      applyView();
    });
    document.getElementById('eo-view-documents').addEventListener('click', () => {
      state.view = 'documents';
      applyView();
    });
    document.getElementById('eo-search').addEventListener('input', (event) => {
      state.query = fold(event.target.value.trim());
      render();
    });
    document.getElementById('eo-sort').addEventListener('change', (event) => {
      state.sort[state.view] = event.target.value;
      render();
    });
    document.getElementById('eo-filter').addEventListener('change', (event) => {
      state.filter[state.view] = event.target.value;
      render();
    });
    load().then(applyView).catch((error) => {
      document.getElementById('eo-list').textContent =
        `Data could not be loaded (${error.message}). `
        + 'The page needs the generated files under data/.';
    });
  };

  document.addEventListener('DOMContentLoaded', init);
  return { init };
})();
