/**
 * catalog.js — Korpus-Uebersicht (docs/index.html)
 *
 * Liest data/catalog.json und rendert:
 * - Screening-Progress-Bar mit Legende
 * - Counts pro Publikationsform
 * - Such-/Filter-/Sortier-Bar
 * - Tabelle mit Thumbnails + Metadaten, Klick fuehrt in viewer.html
 *
 * Namespace: ZBZ.Catalog (initialisiert von DOMContentLoaded)
 */
(function () {
    'use strict';
    const $ = ZBZ.$;

    // ---- Konfiguration ----
    const SCREENING_ORDER  = ['APPROVED', 'APPROVED_WITH_NOTES', 'NEEDS_REVIEW', 'NOT_SCREENED'];
    const SCREENING_LABEL  = {
        APPROVED:           'Approved',
        APPROVED_WITH_NOTES:'With Notes',
        NEEDS_REVIEW:       'Needs Review',
        NOT_SCREENED:       'Nicht gescreent'
    };
    const SCREENING_CLASS  = {
        APPROVED:           'approved',
        APPROVED_WITH_NOTES:'with_notes',
        NEEDS_REVIEW:       'needs_review',
        NOT_SCREENED:       'not_screened'
    };
    const FORM_LABEL = {
        journalArticle: 'Zeitschriftenartikel',
        book:           'Monografie',
        bookSection:    'Buchkapitel',
        encyclopedia:   'Lexikonartikel',
        brochure:       'Broschuere',
        interview:      'Interview',
        anthology:      'Anthologie',
        other:          'Sonstige'
    };

    // ---- State ----
    const state = {
        catalog: null,
        docs: [],
        filtered: [],
        filters: { query: '', lang: '', type: '', form: '', screening: '' },
        sort: 'id-asc'
    };

    const refs = {
        progressBar:    $('#progress-bar'),
        progressLegend: $('#progress-legend'),
        countTotal:     $('#count-total'),
        countsSplit:    $('#counts-split'),
        search:         $('#search'),
        filterLang:     $('#filter-lang'),
        filterType:     $('#filter-type'),
        filterForm:     $('#filter-form'),
        filterScreening:$('#filter-screening'),
        filterReset:    $('#filter-reset'),
        sortSelect:     $('#sort'),
        hitsCount:      $('#hits-count'),
        rows:           $('#doc-rows'),
        generated:      $('#generated-info')
    };

    // ============================================================ Init ============================================================

    async function init() {
        const data = await ZBZ.fetchJSON('data/catalog.json');
        if (!data) {
            refs.rows.innerHTML = '<div class="doc-table__empty">catalog.json nicht gefunden. <code>python -m scripts.generate_edition_data</code></div>';
            return;
        }
        state.catalog = data;
        state.docs = data.documents || data.docs || [];

        renderStatusBar();
        populateFilters();
        applyUrlState();
        bindEvents();
        applyFilters();

        const gen = data.generated ? new Date(data.generated).toLocaleString('de-CH') : '';
        refs.generated.textContent = gen ? `Generiert ${gen}` : '';
        ZBZ.log('Catalog', 'init done, ' + state.docs.length + ' docs');
    }

    // ============================================================ Status-Bar ============================================================

    function renderStatusBar() {
        // Progress: pro Screening-Status
        const counts = {};
        SCREENING_ORDER.forEach(k => counts[k] = 0);
        state.docs.forEach(d => {
            const k = d.screening || 'NOT_SCREENED';
            counts[k] = (counts[k] || 0) + 1;
        });
        const total = state.docs.length;

        // Segmente
        refs.progressBar.innerHTML = '';
        SCREENING_ORDER.forEach(k => {
            if (!counts[k]) return;
            const seg = ZBZ.el('div', {
                cls: 'progress-bar__seg progress-bar__seg--' + SCREENING_CLASS[k],
                style: { flex: counts[k] + ' 1 0' },
                attrs: { title: SCREENING_LABEL[k] + ': ' + counts[k] }
            });
            refs.progressBar.appendChild(seg);
        });

        // Legende
        refs.progressLegend.innerHTML = '';
        SCREENING_ORDER.forEach(k => {
            const li = ZBZ.el('li', {
                html:
                    `<span class="progress-legend__dot" style="background:${segColor(k)}"></span>` +
                    `<span class="progress-legend__count">${counts[k]}</span>` +
                    `<span>${ZBZ.esc(SCREENING_LABEL[k])}</span>` +
                    `<span class="progress-legend__pct">${total ? Math.round((counts[k]/total)*100) : 0}%</span>`
            });
            refs.progressLegend.appendChild(li);
        });

        // Counts pro Pub-Form
        refs.countTotal.textContent = String(total);
        const formCounts = {};
        state.docs.forEach(d => {
            const f = d.pub_form || 'other';
            formCounts[f] = (formCounts[f] || 0) + 1;
        });
        refs.countsSplit.innerHTML = '';
        Object.entries(formCounts)
            .sort((a, b) => b[1] - a[1])
            .forEach(([form, n]) => {
                const label = FORM_LABEL[form] || form;
                const item = ZBZ.el('div', {
                    cls: 'counts-block__split-item',
                    html: `<span>${ZBZ.esc(label)}</span><strong>${n}</strong>`
                });
                refs.countsSplit.appendChild(item);
            });
    }

    function segColor(k) {
        // Werte aus tokens.css, hier nur fuer Legende-Dots inline
        const map = {
            APPROVED:           'var(--h-olivgruen)',
            APPROVED_WITH_NOTES:'var(--h-ziegelrot-light)',
            NEEDS_REVIEW:       'var(--h-ziegelrot)',
            NOT_SCREENED:       'var(--h-border-emphasis)'
        };
        return map[k] || 'var(--h-text-muted)';
    }

    // ============================================================ Filter-Befuellung ============================================================

    function populateFilters() {
        // Sprache aus Daten ableiten
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

    function applyFilters() {
        const q = state.filters.query.trim().toLowerCase();
        state.filtered = state.docs.filter(d => {
            if (state.filters.lang && d.lang !== state.filters.lang) return false;
            if (state.filters.type && d.type !== state.filters.type) return false;
            if (state.filters.form && d.pub_form !== state.filters.form) return false;
            if (state.filters.screening) {
                const s = d.screening || 'NOT_SCREENED';
                if (s !== state.filters.screening) return false;
            }
            if (q) {
                const hay = (d.id + ' ' + (d.title || '') + ' ' + (d.author || '') + ' ' + (d.desc || '')).toLowerCase();
                if (!hay.includes(q)) return false;
            }
            return true;
        });

        sortFiltered();
        renderRows();
        refs.hitsCount.textContent = state.filtered.length + ' / ' + state.docs.length;
        syncUrlState();
    }

    function sortFiltered() {
        const [field, dir] = state.sort.split('-');
        const mul = dir === 'desc' ? -1 : 1;
        state.filtered.sort((a, b) => {
            let av, bv;
            switch (field) {
                case 'id':    av = parseInt(a.id, 10); bv = parseInt(b.id, 10); break;
                case 'title': av = (a.title || '').toLowerCase(); bv = (b.title || '').toLowerCase(); break;
                case 'pages': av = a.page_count || 0; bv = b.page_count || 0; break;
                case 'date':  av = a.date || ''; bv = b.date || ''; break;
                default:      av = a.id; bv = b.id;
            }
            if (av < bv) return -1 * mul;
            if (av > bv) return  1 * mul;
            return 0;
        });
    }

    // ============================================================ Render ============================================================

    function renderRows() {
        refs.rows.innerHTML = '';
        if (state.filtered.length === 0) {
            refs.rows.innerHTML = '<div class="doc-table__empty">Keine Dokumente fuer diese Filter.</div>';
            return;
        }
        const frag = document.createDocumentFragment();
        state.filtered.forEach(d => frag.appendChild(rowFor(d)));
        refs.rows.appendChild(frag);
    }

    function rowFor(d) {
        const screening = d.screening || 'NOT_SCREENED';
        const cls = SCREENING_CLASS[screening];
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

        // Title-Cell
        const title = ZBZ.el('div', {
            cls: 'col-title',
            html:
                `<span class="col-title__id">${ZBZ.esc(d.id)}</span>` +
                `<span class="col-title__name">${ZBZ.esc(d.title || 'Dokument ' + d.id)}</span>`
        });

        // Meta-Cell
        const meta = ZBZ.el('div', {
            cls: 'col-meta',
            html:
                `<span class="col-meta__author">${ZBZ.esc(d.author || '—')}</span>` +
                `<span class="col-meta__date">${ZBZ.esc(d.date || '')}</span>`
        });

        const lang  = ZBZ.el('div', { cls: 'col-lang',  text: d.lang || '—' });
        const type  = ZBZ.el('div', { cls: 'col-type',  text: d.type || '—' });
        const form  = ZBZ.el('div', { cls: 'col-form',  text: formLabel });
        const pages = ZBZ.el('div', { cls: 'col-pages', text: String(d.page_count || '—') });

        const screen = ZBZ.el('div', { cls: 'col-screening' });
        screen.appendChild(ZBZ.el('span', {
            cls: 'badge-screening badge-screening--' + cls,
            text: SCREENING_LABEL[screening]
        }));

        [thumb, title, meta, lang, type, form, pages, screen].forEach(el => a.appendChild(el));
        return a;
    }

    // ============================================================ URL-State ============================================================

    function applyUrlState() {
        const q  = ZBZ.getParam('q')         || '';
        const l  = ZBZ.getParam('lang')      || '';
        const t  = ZBZ.getParam('type')      || '';
        const f  = ZBZ.getParam('form')      || '';
        const sc = ZBZ.getParam('screening') || '';
        const so = ZBZ.getParam('sort')      || 'id-asc';

        state.filters.query     = q;
        state.filters.lang      = l;
        state.filters.type      = t;
        state.filters.form      = f;
        state.filters.screening = sc;
        state.sort              = so;

        refs.search.value           = q;
        refs.filterLang.value       = l;
        refs.filterType.value       = t;
        refs.filterForm.value       = f;
        refs.filterScreening.value  = sc;
        refs.sortSelect.value       = so;
    }

    function syncUrlState() {
        ZBZ.setParams({
            q:         state.filters.query     || null,
            lang:      state.filters.lang      || null,
            type:      state.filters.type      || null,
            form:      state.filters.form      || null,
            screening: state.filters.screening || null,
            sort:      state.sort !== 'id-asc' ? state.sort : null
        });
    }

    // ============================================================ Events ============================================================

    function bindEvents() {
        refs.search.addEventListener('input', ZBZ.debounce(e => {
            state.filters.query = e.target.value;
            applyFilters();
        }, 200));

        [
            ['filterLang',      'lang'],
            ['filterType',      'type'],
            ['filterForm',      'form'],
            ['filterScreening', 'screening']
        ].forEach(([ref, key]) => {
            refs[ref].addEventListener('change', e => {
                state.filters[key] = e.target.value;
                applyFilters();
            });
        });

        refs.sortSelect.addEventListener('change', e => {
            state.sort = e.target.value;
            applyFilters();
        });

        refs.filterReset.addEventListener('click', () => {
            state.filters = { query: '', lang: '', type: '', form: '', screening: '' };
            state.sort = 'id-asc';
            refs.search.value = '';
            refs.filterLang.value = '';
            refs.filterType.value = '';
            refs.filterForm.value = '';
            refs.filterScreening.value = '';
            refs.sortSelect.value = 'id-asc';
            applyFilters();
        });
    }

    ZBZ.Catalog = { init, state };
    document.addEventListener('DOMContentLoaded', init);
})();
