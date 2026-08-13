/* Entity overview: completeness instrument over the annotation layer.
   Primary view aggregates per listed entity (zero-mention entries first, the
   "do we have all" check); secondary view aggregates per document.
   Data: data/entity_overview.json + data/catalog.json (titles). Read-only;
   all text reaches the DOM via textContent. */

window.ZBZ = window.ZBZ || {};

ZBZ.EntityOverview = (() => {
  'use strict';

  const state = {
    view: 'entities',      // 'entities' | 'documents'
    entityRows: [],
    docRows: [],
    classes: [],
    titles: {},            // doc id -> {title, author, date}
    query: '',
    sort: { entities: 'zero', documents: 'id' },
    filter: { entities: 'all', documents: 'all' },
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
      docs: e.docs,
      ndocs: Object.keys(e.docs).length,
      search: fold(`${gid} ${e.label}`),
    }));
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
    render();
  };

  // ------------------------------------------------------------ corpus bar

  const renderCorpusBar = (totals) => {
    const total = totals.auto + totals.review;
    if (total) {
      document.getElementById('eo-corpus-auto').style.width =
        `${(totals.auto / total) * 100}%`;
      document.getElementById('eo-corpus-review').style.width =
        `${(totals.review / total) * 100}%`;
    }
    document.getElementById('eo-corpus-bar').setAttribute('aria-label',
      `${totals.auto.toLocaleString('en-GB')} auto-marked and `
      + `${totals.review.toLocaleString('en-GB')} review mentions`);
    document.getElementById('eo-corpus-label-auto').textContent =
      `${totals.auto.toLocaleString('en-GB')} auto-marked`;
    document.getElementById('eo-corpus-label-review').textContent =
      `${totals.review.toLocaleString('en-GB')} review candidates`;
    const found = document.getElementById('eo-corpus-found');
    found.textContent = `${totals.entities_found} of ${totals.listed_entities} `
      + 'listed entities found';
    found.className = 'badge '
      + (totals.entities_found === totals.listed_entities ? 'badge--ok' : 'badge--warn');
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
      const zero = rows.filter((r) => r.total === 0).length;
      document.getElementById('eo-result-count').textContent =
        `${rows.length} of ${state.entityRows.length} entities`
        + (zero ? ` · ${zero} without any mention` : '');
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
    if (total) {
      const autoSeg = el('span', 'eo-bar__auto');
      autoSeg.style.width = `${(auto / total) * 100}%`;
      const reviewSeg = el('span', 'eo-bar__review');
      reviewSeg.style.width = `${(review / total) * 100}%`;
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
    return span;
  };

  // --- entity view

  const renderEntity = (row) => {
    const details = el('details', 'eo-doc');
    const summary = el('summary', 'eo-doc__summary eo-doc__summary--entity');

    const name = el('span', 'eo-doc__title');
    name.appendChild(el('span', `eo-dot eo-dot--${row.category}`));
    name.appendChild(document.createTextNode(row.label));
    name.appendChild(el('span', 'eo-doc__meta', ` ${row.gid}`));
    summary.appendChild(name);

    summary.appendChild(el('span', 'eo-doc__meta',
      row.ndocs ? `${row.ndocs} doc${row.ndocs === 1 ? '' : 's'}` : 'not found'));
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

  const renderEntityBody = (row) => {
    const body = el('div', 'eo-doc__body');
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

    if (row.review > 0) {
      const chips = el('div', 'eo-chips');
      state.classes.forEach((cls) => {
        const count = row.classes[cls.key];
        if (!count) return;
        const chip = el('span', 'eo-chip', `${cls.label} × ${count}`);
        chip.title = cls.description;
        chips.appendChild(chip);
      });
      body.appendChild(chips);
    }

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
    const byGid = {};
    state.entityRows.forEach((e) => { byGid[e.gid] = e; });
    const table = el('table', 'eo-table');
    const head = el('thead');
    const headRow = el('tr');
    ['Entity', 'Auto', 'Review', 'Review classes'].forEach((label, i) => {
      const th = el('th', i === 1 || i === 2 ? 'eo-num' : '', label);
      th.scope = 'col';
      headRow.appendChild(th);
    });
    head.appendChild(headRow);
    table.appendChild(head);
    const tbody = el('tbody');
    row.entities.forEach((entity) => {
      const info = byGid[entity.gid] || {};
      const tr = el('tr');
      const name = el('td');
      name.appendChild(el('span', `eo-dot eo-dot--${info.category || 'unknown'}`));
      name.appendChild(document.createTextNode(info.label || entity.gid));
      tr.appendChild(name);
      tr.appendChild(el('td', 'eo-num', String(entity.auto)));
      tr.appendChild(el('td', 'eo-num', String(entity.review)));
      const classes = state.classes
        .filter((cls) => entity.classes[cls.key])
        .map((cls) => `${cls.label} × ${entity.classes[cls.key]}`)
        .join(', ');
      tr.appendChild(el('td', '', classes));
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
