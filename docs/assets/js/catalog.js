/**
 * catalog.js — Korpus-Uebersicht (docs/index.html)
 *
 * Liest data/catalog.json und rendert:
 * - Such-/Filter-Bar (Sprache, Typ, Form, Stream, Status)
 * - Tabelle mit Title/Autor/Datum/Lang/Typ/Form/Seiten/Workflow
 *   Spaltenheader sind klickbar fuer Sortierung.
 *
 * Workflow-Statuswerte pro Strom: unverifiziert | in_arbeit | verifiziert (E77)
 *
 * Namespace: ZBZ.Catalog (initialisiert von DOMContentLoaded)
 */
(function () {
    'use strict';
    const $ = ZBZ.$;
    const $$ = ZBZ.$$;

    // ---- Konfiguration ----
    const STREAMS         = ['ocr', 'layout', 'tei'];
    const STREAM_LABEL    = { ocr: 'OCR', layout: 'Layout', tei: 'TEI-XML' };
    const STATUS_LABEL    = {
        unverifiziert: 'unverifiziert',
        in_arbeit:     'in Arbeit',
        verifiziert:   'verifiziert'
    };
    // Map alter Status-Werte (offen, bearbeitet, fertig) auf neue.
    const STATUS_LEGACY = { offen: 'unverifiziert', bearbeitet: 'in_arbeit', fertig: 'verifiziert' };
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
            refs.rows.innerHTML = '<div class="doc-table__empty">catalog.json nicht gefunden. <code>python -m scripts.edition.generate_edition_data</code></div>';
            return;
        }
        state.catalog = data;
        state.docs = data.documents || data.docs || [];

        populateFilters();
        applyUrlState();
        bindEvents();
        applyFilters();
        renderSortIndicators();

        const gen = data.generated ? new Date(data.generated).toLocaleDateString('de-CH') : '';
        refs.generated.textContent = gen ? `Generiert ${gen}` : '';
        ZBZ.log('Catalog', 'init done, ' + state.docs.length + ' docs');
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

    // ============================================================ Filter-Befuellung ============================================================

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

    // Der Strom-Filter grenzt nur ein, AUF WELCHEN Strom sich ein gewaehlter Status
    // bezieht. Ohne Status ist er wirkungslos -> bis dahin deaktivieren (und einen
    // verwaisten ?stream= aus der URL raeumen), damit er nicht aktiv wirkt ohne Effekt.
    function syncStreamControl() {
        const hasStatus = !!state.filters.status;
        refs.filterStream.disabled = !hasStatus;
        refs.filterStream.title = hasStatus
            ? 'Strom, auf den sich der Status bezieht'
            : 'Erst einen Status waehlen, dann den Strom eingrenzen';
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
                    // Leere Datumswerte (88/285) immer ans Ende, unabhaengig von der Richtung.
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
            // Default-Richtung: id/pages/date numerisch absteigend macht selten Sinn,
            // Text-Felder beginnen mit asc; pages beginnt mit desc (viele zuerst).
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
            refs.rows.innerHTML = '<div class="doc-table__empty">Keine Dokumente fuer diese Filter.</div>';
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
            ? total + ' Dokumente'
            : n + ' von ' + total + ' Dokumenten';
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
                `<span class="col-title__name">${ZBZ.esc(d.title || 'Dokument ' + d.id)}</span>`
        });

        const author = ZBZ.el('div', { cls: 'col-author', text: d.author || '—' });
        const date   = ZBZ.el('div', { cls: 'col-date',   text: d.date || '' });
        const lang   = ZBZ.el('div', { cls: 'col-lang',   text: d.lang || '—' });
        const type   = ZBZ.el('div', { cls: 'col-type',   text: d.type || '—' });
        const form   = ZBZ.el('div', { cls: 'col-form',   text: formLabel });
        const pages  = ZBZ.el('div', { cls: 'col-pages',  text: String(d.page_count || '—') });

        // Workflow: drei Ampel-Zeilen (Dot + Label). Status im Tooltip.
        const workflow = ZBZ.el('div', {
            cls: 'col-workflow',
            attrs: { 'aria-label': workflowAriaLabel(d) }
        });
        STREAMS.forEach(s => {
            const st = streamStatus(d, s);
            const sm = (d.streams || {})[s] || {};
            let tip;
            if (st === 'unverifiziert') {
                tip = STREAM_LABEL[s] + ': Pipeline-Output existiert, noch nicht menschlich verifiziert';
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

    // ============================================================ URL-State ============================================================

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

        // Klickbare Spalten-Sortierung
        $$('.col-sort').forEach(btn => {
            btn.addEventListener('click', () => toggleSort(btn.getAttribute('data-sort')));
        });
    }

    ZBZ.Catalog = { init, state };
    document.addEventListener('DOMContentLoaded', init);
})();
