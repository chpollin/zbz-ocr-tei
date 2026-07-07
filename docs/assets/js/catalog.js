/**
 * catalog.js — Corpus overview (docs/index.html)
 *
 * Reads data/catalog.json and renders:
 * - Search/filter bar (language, type, form, stream, status)
 * - Table with title/author/date/lang/type/form/pages/workflow.
 *   Column headers are clickable for sorting.
 *
 * Workflow status values per stream: unverifiziert | in_arbeit | verifiziert (E77)
 *
 * Namespace: ZBZ.Catalog (initialized by DOMContentLoaded)
 */
(function () {
    'use strict';
    const $ = ZBZ.$;
    const $$ = ZBZ.$$;

    // ---- Configuration ----
    const STREAMS         = ['ocr', 'layout', 'tei'];
    const STREAM_LABEL    = { ocr: 'OCR', layout: 'Layout', tei: 'TEI-XML' };
    const STATUS_LABEL    = {
        unverifiziert: 'unverified',
        in_arbeit:     'in progress',
        verifiziert:   'verified'
    };
    // Map legacy status values (offen, bearbeitet, fertig) to current ones.
    const STATUS_LEGACY = { offen: 'unverifiziert', bearbeitet: 'in_arbeit', fertig: 'verifiziert' };
    const FORM_LABEL = {
        journalArticle: 'Journal article',
        book:           'Monograph',
        bookSection:    'Book chapter',
        encyclopedia:   'Encyclopedia article',
        brochure:       'Brochure',
        interview:      'Interview',
        anthology:      'Anthology',
        other:          'Other'
    };
    // Layout type (Masterfile): same labels as the type filter options
    const TYPE_LABEL = {
        A: 'Single-column',
        B: 'Two-column',
        C: 'Monograph',
        D: 'Special'
    };

    // ---- State ----
    const state = {
        catalog: null,
        docs: [],
        filtered: [],
        filters: { query: '', lang: '', type: '', form: '', stream: '', status: '' },
        sort: 'id-asc'
    };

    const refs = {
        search:         $('#search'),
        filterLang:     $('#filter-lang'),
        filterType:     $('#filter-type'),
        filterForm:     $('#filter-form'),
        filterStream:   $('#filter-stream'),
        filterStatus:   $('#filter-status'),
        filterReset:    $('#filter-reset'),
        head:           $('#doc-head'),
        rows:           $('#doc-rows'),
        count:          $('#result-count'),
        generated:      $('#generated-info')
    };

    // ============================================================ Init ============================================================

    async function init() {
        const data = await ZBZ.fetchJSON('data/catalog.json');
        if (!data) {
            refs.rows.innerHTML = '<div class="doc-table__empty">catalog.json not found. <code>python -m scripts.edition.generate_edition_data</code></div>';
            return;
        }
        state.catalog = data;
        state.docs = data.documents || data.docs || [];

        populateFilters();
        applyUrlState();
        bindEvents();
        applyFilters();
        renderSortIndicators();

        const gen = data.generated ? new Date(data.generated).toLocaleDateString('en-GB') : '';
        refs.generated.textContent = gen ? `Generated ${gen}` : '';
        ZBZ.log('Catalog', 'init done, ' + state.docs.length + ' docs');

        refreshWorkflowFromManifests();
    }

    // catalog.json is an aggregate that lags behind viewer saves; the manifest
    // mirror is written immediately. Prefer it so the workflow dots are fresh.
    async function refreshWorkflowFromManifests() {
        const BATCH = 24;
        let changed = 0;
        for (let i = 0; i < state.docs.length; i += BATCH) {
            await Promise.all(state.docs.slice(i, i + BATCH).map(async d => {
                const m = await ZBZ.fetchJSON('data/manifests/' + encodeURIComponent(d.id) + '_manifest.json');
                if (m && m.streams && JSON.stringify(m.streams) !== JSON.stringify(d.streams || {})) {
                    d.streams = m.streams;
                    changed++;
                }
            }));
        }
        if (changed) {
            applyFilters();
            ZBZ.log('Catalog', 'workflow refreshed from manifests (' + changed + ' docs)');
        }
    }

    // ============================================================ Helpers ============================================================

    function streamStatus(d, stream) {
        const s = (d.streams || {})[stream];
        let v = s && s.status;
        if (STATUS_LEGACY[v]) v = STATUS_LEGACY[v];
        return STATUS_LABEL[v] ? v : 'unverifiziert';
    }

    function workflowAriaLabel(d) {
        return 'Workflow ' + STREAMS.map(s =>
            STREAM_LABEL[s] + ' ' + STATUS_LABEL[streamStatus(d, s)]
        ).join(', ');
    }

    // ============================================================ Filter population ============================================================

    function populateFilters() {
        const langs = new Set();
        const forms = new Set();
        state.docs.forEach(d => {
            if (d.lang) langs.add(d.lang);
            if (d.pub_form) forms.add(d.pub_form);
        });

        [...langs].sort().forEach(l => {
            refs.filterLang.appendChild(ZBZ.el('option', { attrs: { value: l }, text: l }));
        });
        [...forms].sort().forEach(f => {
            refs.filterForm.appendChild(ZBZ.el('option', {
                attrs: { value: f },
                text: FORM_LABEL[f] || f
            }));
        });
    }

    // ============================================================ Filter + Sort ============================================================

    // The stream filter only narrows WHICH stream a selected status applies to.
    // Without a status it has no effect, so disable it (and clear an orphaned ?stream=
    // from the URL) to prevent it from appearing active with no visible result.
    function syncStreamControl() {
        const hasStatus = !!state.filters.status;
        refs.filterStream.disabled = !hasStatus;
        refs.filterStream.title = hasStatus
            ? 'Stream the status applies to'
            : 'Choose a status first, then narrow by stream';
        if (!hasStatus && state.filters.stream) {
            state.filters.stream = '';
            refs.filterStream.value = '';
        }
    }

    function applyFilters() {
        syncStreamControl();
        const q = state.filters.query.trim().toLowerCase();
        const fStream = state.filters.stream;
        const fStatus = state.filters.status;

        state.filtered = state.docs.filter(d => {
            if (state.filters.lang && d.lang !== state.filters.lang) return false;
            if (state.filters.type && d.type !== state.filters.type) return false;
            if (state.filters.form && d.pub_form !== state.filters.form) return false;

            if (fStream && fStatus) {
                if (streamStatus(d, fStream) !== fStatus) return false;
            } else if (fStatus) {
                if (!STREAMS.some(s => streamStatus(d, s) === fStatus)) return false;
            }

            if (q) {
                const hay = (d.id + ' ' + (d.title || '') + ' ' + (d.author || '') + ' ' + (d.desc || '')).toLowerCase();
                if (!hay.includes(q)) return false;
            }
            return true;
        });

        sortFiltered();
        renderRows();
        syncUrlState();
    }

    function sortFiltered() {
        const [field, dir] = state.sort.split('-');
        const mul = dir === 'desc' ? -1 : 1;
        state.filtered.sort((a, b) => {
            let av, bv;
            switch (field) {
                case 'id':     av = parseInt(a.id, 10); bv = parseInt(b.id, 10); break;
                case 'title':  av = (a.title || '').toLowerCase(); bv = (b.title || '').toLowerCase(); break;
                case 'author': av = (a.author || '').toLowerCase(); bv = (b.author || '').toLowerCase(); break;
                case 'date': {
                    av = a.date || ''; bv = b.date || '';
                    // Empty date values always sort last, regardless of direction.
                    if (!av && !bv) return 0;
                    if (!av) return 1;
                    if (!bv) return -1;
                    break;
                }
                case 'lang':   av = a.lang || ''; bv = b.lang || ''; break;
                case 'type':   av = a.type || ''; bv = b.type || ''; break;
                case 'form':   av = a.pub_form || ''; bv = b.pub_form || ''; break;
                case 'pages':  av = a.page_count || 0; bv = b.page_count || 0; break;
                default:       av = parseInt(a.id, 10); bv = parseInt(b.id, 10);
            }
            if (av < bv) return -1 * mul;
            if (av > bv) return  1 * mul;
            return 0;
        });
    }

    function toggleSort(field) {
        const [curField, curDir] = state.sort.split('-');
        if (curField === field) {
            state.sort = field + '-' + (curDir === 'asc' ? 'desc' : 'asc');
        } else {
            // Default direction: pages starts descending (most pages first); text fields start ascending.
            const defaultDir = (field === 'pages') ? 'desc' : 'asc';
            state.sort = field + '-' + defaultDir;
        }
        renderSortIndicators();
        applyFilters();
    }

    function renderSortIndicators() {
        const [field, dir] = state.sort.split('-');
        $$('.col-sort').forEach(btn => {
            const sf = btn.getAttribute('data-sort');
            if (sf === field) {
                btn.setAttribute('aria-sort', dir === 'desc' ? 'descending' : 'ascending');
            } else {
                btn.removeAttribute('aria-sort');
            }
        });
    }

    // ============================================================ Render ============================================================

    function renderRows() {
        updateCount();
        refs.rows.innerHTML = '';
        if (state.filtered.length === 0) {
            refs.rows.innerHTML = '<div class="doc-table__empty">No documents match these filters.</div>';
            return;
        }
        const frag = document.createDocumentFragment();
        state.filtered.forEach(d => frag.appendChild(rowFor(d)));
        refs.rows.appendChild(frag);
    }

    function updateCount() {
        if (!refs.count) return;
        const n = state.filtered.length;
        const total = state.docs.length;
        refs.count.textContent = (n === total)
            ? total + ' documents'
            : n + ' of ' + total + ' documents';
    }

    function rowFor(d) {
        const formLabel = FORM_LABEL[d.pub_form] || d.pub_form || '—';

        const a = ZBZ.el('a', {
            cls: 'doc-table__row',
            attrs: {
                href: `viewer.html?doc=${encodeURIComponent(d.id)}&page=1`,
                title: d.desc ? d.desc.slice(0, 240) : ''
            }
        });

        // Thumbnail
        const thumb = ZBZ.el('div', { cls: 'col-thumb' });
        const img = ZBZ.el('img', {
            attrs: {
                src: `data/thumbs/${d.id}.jpg`,
                alt: 'Thumbnail ' + d.id,
                loading: 'lazy'
            }
        });
        img.onerror = () => {
            thumb.innerHTML = `<span class="col-thumb__placeholder">${ZBZ.esc(d.id)}</span>`;
        };
        thumb.appendChild(img);

        const title = ZBZ.el('div', {
            cls: 'col-title',
            html:
                `<span class="col-title__id">${ZBZ.esc(d.id)}</span>` +
                `<span class="col-title__name">${ZBZ.esc(d.title || 'Document ' + d.id)}</span>`
        });

        const author = ZBZ.el('div', { cls: 'col-author', text: d.author || '—' });
        const date   = ZBZ.el('div', { cls: 'col-date',   text: d.date || '' });
        const lang   = ZBZ.el('div', { cls: 'col-lang',   text: d.lang || '—' });
        const type   = ZBZ.el('div', {
            cls: 'col-type',
            text: TYPE_LABEL[d.type] || d.type || '—',
            attrs: d.type ? { title: 'Layout type ' + d.type } : {}
        });
        const form   = ZBZ.el('div', { cls: 'col-form',   text: formLabel });
        const pages  = ZBZ.el('div', { cls: 'col-pages',  text: String(d.page_count || '—') });

        // Workflow: three traffic-light rows (dot + label). Status shown in tooltip.
        const workflow = ZBZ.el('div', {
            cls: 'col-workflow',
            attrs: { 'aria-label': workflowAriaLabel(d) }
        });
        STREAMS.forEach(s => {
            const st = streamStatus(d, s);
            const sm = (d.streams || {})[s] || {};
            let tip;
            if (st === 'unverifiziert') {
                tip = STREAM_LABEL[s] + ': pipeline output exists, not yet verified by a human';
            } else {
                tip = STREAM_LABEL[s] + ': ' + STATUS_LABEL[st]
                    + (sm.last_by ? ' · ' + sm.last_by : '')
                    + (sm.last_at ? ' · ' + sm.last_at.slice(0, 10) : '');
            }
            const row = ZBZ.el('div', {
                cls: 'col-workflow__row',
                attrs: { title: tip },
                html:
                    `<span class="col-workflow__dot col-workflow__dot--${st}"></span>` +
                    `<span class="col-workflow__label">${STREAM_LABEL[s]}</span>`
            });
            workflow.appendChild(row);
        });

        [thumb, title, author, date, lang, type, form, pages, workflow].forEach(el => a.appendChild(el));
        return a;
    }

    // ============================================================ URL state ============================================================

    function applyUrlState() {
        const q  = ZBZ.getParam('q')       || '';
        const l  = ZBZ.getParam('lang')    || '';
        const t  = ZBZ.getParam('type')    || '';
        const f  = ZBZ.getParam('form')    || '';
        const sm = ZBZ.getParam('stream')  || '';
        const st = ZBZ.getParam('status')  || '';
        const so = ZBZ.getParam('sort')    || 'id-asc';

        state.filters.query  = q;
        state.filters.lang   = l;
        state.filters.type   = t;
        state.filters.form   = f;
        state.filters.stream = sm;
        state.filters.status = st;
        state.sort           = so;

        refs.search.value       = q;
        refs.filterLang.value   = l;
        refs.filterType.value   = t;
        refs.filterForm.value   = f;
        refs.filterStream.value = sm;
        refs.filterStatus.value = st;
    }

    function syncUrlState() {
        ZBZ.setParams({
            q:      state.filters.query  || null,
            lang:   state.filters.lang   || null,
            type:   state.filters.type   || null,
            form:   state.filters.form   || null,
            stream: state.filters.stream || null,
            status: state.filters.status || null,
            sort:   state.sort !== 'id-asc' ? state.sort : null
        });
    }

    // ============================================================ Events ============================================================

    function bindEvents() {
        refs.search.addEventListener('input', ZBZ.debounce(e => {
            state.filters.query = e.target.value;
            applyFilters();
        }, 200));

        [
            ['filterLang',   'lang'],
            ['filterType',   'type'],
            ['filterForm',   'form'],
            ['filterStream', 'stream'],
            ['filterStatus', 'status']
        ].forEach(([ref, key]) => {
            refs[ref].addEventListener('change', e => {
                state.filters[key] = e.target.value;
                applyFilters();
            });
        });

        refs.filterReset.addEventListener('click', () => {
            state.filters = { query: '', lang: '', type: '', form: '', stream: '', status: '' };
            refs.search.value = '';
            refs.filterLang.value = '';
            refs.filterType.value = '';
            refs.filterForm.value = '';
            refs.filterStream.value = '';
            refs.filterStatus.value = '';
            applyFilters();
        });

        // Clickable column sorting
        $$('.col-sort').forEach(btn => {
            btn.addEventListener('click', () => toggleSort(btn.getAttribute('data-sort')));
        });
    }

    ZBZ.Catalog = { init, state };
    document.addEventListener('DOMContentLoaded', init);
})();
