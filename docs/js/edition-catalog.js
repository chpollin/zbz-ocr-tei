/**
 * ZBZ Edition – Catalog Module
 * Document catalog with faceted filters, search, table/card views.
 * Namespace: ZBZ.EditionCatalog (ES6+, IIFE)
 */
(function () {
    'use strict';

    const E = ZBZ.Edition;

    const state = {
        catalog: null,
        documents: [],
        filtered: [],
        view: 'table',
        sortKey: 'id',
        sortAsc: true,
        searchIndex: null,
        searchQuery: '',
        fullTextIndex: null,
        searchSnippets: {},
        curationStatuses: {},
        serverAvailable: false
    };

    const filters = {
        types: [],
        langs: [],
        forms: [],
        screening: [],
        dateFrom: '',
        dateTo: ''
    };

    // Screening/Curation labels from shared module
    const SCREENING_LABELS = E.SCREENING_LABELS;
    const SCREENING_CLASSES = E.SCREENING_CLASSES;

    // --- Init ---
    function init() {
        Promise.all([E.loadCatalog(), E.loadSearchIndex()]).then((results) => {
            const catalog = results[0];
            const searchData = results[1];
            if (!catalog) return;
            state.catalog = catalog;
            state.documents = catalog.documents || [];
            state.filtered = state.documents.slice();

            // Full-text index
            if (searchData && searchData.length) {
                state.fullTextIndex = E.createFullTextSearchIndex(searchData);
                state._searchData = searchData;
            }

            initSearchIndex();
            renderFilters();
            bindEvents();
            readUrlFilters();
            applyFilters();
            _checkCurationServer();

            ZBZ.log('Catalog', `${state.documents.length} Docs | Meta-Search: ${state.searchIndex ? 'aktiv' : 'aus'} | Volltext: ${state.fullTextIndex ? 'aktiv' : 'aus'}`);
        });
    }

    // --- URL Parameter Pre-filtering ---
    function readUrlFilters() {
        const q = E.getParam('q');
        if (q) {
            state.searchQuery = q;
            const searchInput = E.$('#catalog-search');
            if (searchInput) searchInput.value = q;
        }
        ['type', 'lang', 'form', 'screening'].forEach((param) => {
            const val = E.getParam(param);
            if (val) {
                const cb = E.$(`input[name="${param}"][value="${val}"]`);
                if (cb) cb.checked = true;
            }
        });
        const view = E.getParam('view');
        if (view && (view === 'table' || view === 'cards' || view === 'gallery')) {
            state.view = view;
            E.$$('.ed-view-btn').forEach((b) => { b.classList.toggle('active', b.getAttribute('data-view') === view); });
        }
        updateFilterState();
    }

    // --- MiniSearch ---
    function initSearchIndex() {
        if (typeof MiniSearch === 'undefined') return;
        try {
            state.searchIndex = new MiniSearch({
                fields: ['title', 'author', 'desc', 'id'],
                storeFields: ['id'],
                searchOptions: {
                    boost: { title: 3, author: 2, id: 1 },
                    fuzzy: 0.2,
                    prefix: true
                }
            });
            state.searchIndex.addAll(state.documents.map((d) => ({
                id: d.id,
                title: d.title || '',
                author: d.author || '',
                desc: d.desc || ''
            })));
        } catch (e) {
            console.warn('MiniSearch init failed, falling back to simple search:', e);
            state.searchIndex = null;
        }
    }

    // --- Filter Rendering ---
    function renderFilters() {
        const catalog = state.catalog;
        if (!catalog) return;

        // Types
        const typeContainer = E.$('#filter-types');
        if (typeContainer) {
            const types = catalog.corpus && catalog.corpus.types ? catalog.corpus.types : {};
            renderCheckboxGroup(typeContainer, types, 'type', E.TYPE_LABELS);
        }

        // Languages
        const langContainer = E.$('#filter-langs');
        if (langContainer) {
            const langs = catalog.corpus && catalog.corpus.languages ? catalog.corpus.languages : {};
            // Show top 6 languages only
            const sorted = Object.keys(langs).sort((a, b) => langs[b] - langs[a]);
            const top = {};
            sorted.slice(0, 6).forEach((k) => { top[k] = langs[k]; });
            renderCheckboxGroup(langContainer, top, 'lang', E.LANG_LABELS);
        }

        // Forms
        const formContainer = E.$('#filter-forms');
        if (formContainer) {
            const forms = catalog.corpus && catalog.corpus.forms ? catalog.corpus.forms : {};
            renderCheckboxGroup(formContainer, forms, 'form', E.PUB_FORM_LABELS);
        }

        // Screening
        const screenContainer = E.$('#filter-screening');
        if (screenContainer && catalog.corpus && catalog.corpus.screening) {
            renderCheckboxGroup(screenContainer, catalog.corpus.screening, 'screening', SCREENING_LABELS);
        }
    }

    function renderCheckboxGroup(container, counts, prefix, labels) {
        container.innerHTML = '';
        Object.keys(counts).forEach((key) => {
            const label = document.createElement('label');
            label.className = 'ed-filter-label';

            const cb = document.createElement('input');
            cb.type = 'checkbox';
            cb.value = key;
            cb.name = prefix;
            cb.addEventListener('change', () => {
                updateFilterState();
                applyFilters();
            });

            const text = document.createTextNode(' ' + ((labels && labels[key]) || key));
            const count = document.createElement('span');
            count.className = 'ed-filter-count';
            count.textContent = counts[key];

            label.appendChild(cb);
            label.appendChild(text);
            label.appendChild(count);
            container.appendChild(label);
        });
    }

    // --- Events ---
    function bindEvents() {
        // Search input
        const searchInput = E.$('#catalog-search');
        if (searchInput) {
            searchInput.addEventListener('input', E.debounce(function () {
                state.searchQuery = searchInput.value.trim();
                applyFilters();
            }, 200));
        }

        // View toggle
        E.$$('.ed-view-btn').forEach((btn) => {
            btn.addEventListener('click', () => {
                state.view = btn.getAttribute('data-view');
                E.$$('.ed-view-btn').forEach((b) => { b.classList.toggle('active', b === btn); });
                renderResults();
            });
        });

        // Sort select
        const sortSelect = E.$('#catalog-sort');
        if (sortSelect) {
            sortSelect.addEventListener('change', () => {
                const val = sortSelect.value;
                if (val.charAt(0) === '-') {
                    state.sortKey = val.substring(1);
                    state.sortAsc = false;
                } else {
                    state.sortKey = val;
                    state.sortAsc = true;
                }
                applyFilters();
            });
        }

        // Date range
        const dateFrom = E.$('#filter-date-from');
        const dateTo = E.$('#filter-date-to');
        if (dateFrom) dateFrom.addEventListener('input', E.debounce(function () {
            filters.dateFrom = dateFrom.value;
            applyFilters();
        }, 300));
        if (dateTo) dateTo.addEventListener('input', E.debounce(function () {
            filters.dateTo = dateTo.value;
            applyFilters();
        }, 300));
    }

    // --- Filter Logic ---
    function updateFilterState() {
        filters.types = getCheckedValues('type');
        filters.langs = getCheckedValues('lang');
        filters.forms = getCheckedValues('form');
        filters.screening = getCheckedValues('screening');
    }

    function getCheckedValues(name) {
        return E.$$(`input[name="${name}"]:checked`).map((cb) => cb.value);
    }

    function applyFilters() {
        let docs = state.documents;
        state.searchSnippets = {};

        // Search: merge metadata + full-text results
        if (state.searchQuery) {
            const metaIds = {};
            const fullIds = {};

            // Metadata search
            if (state.searchIndex) {
                state.searchIndex.search(state.searchQuery).forEach((r) => { metaIds[r.id] = true; });
            }
            // Full-text search (with snippets)
            if (state.fullTextIndex) {
                const textMap = {};
                if (state._searchData) {
                    state._searchData.forEach((d) => { textMap[d.id] = d.text || ''; });
                }
                state.fullTextIndex.search(state.searchQuery, { limit: 100 }).forEach((r) => {
                    fullIds[r.id] = true;
                    if (textMap[r.id]) {
                        state.searchSnippets[r.id] = E.extractSnippet(textMap[r.id], state.searchQuery);
                    }
                });
            }
            // Fallback: simple string match
            const q = state.searchQuery.toLowerCase();
            docs = docs.filter((d) => {
                if (metaIds[d.id] || fullIds[d.id]) return true;
                return (d.title && d.title.toLowerCase().indexOf(q) > -1) ||
                       (d.author && d.author.toLowerCase().indexOf(q) > -1) ||
                       (d.id.indexOf(q) > -1) ||
                       (d.desc && d.desc.toLowerCase().indexOf(q) > -1);
            });
        }

        // Type filter
        if (filters.types.length) {
            docs = docs.filter((d) => filters.types.indexOf(d.type) > -1);
        }

        // Language filter
        if (filters.langs.length) {
            docs = docs.filter((d) => filters.langs.indexOf(d.lang) > -1);
        }

        // Form filter
        if (filters.forms.length) {
            docs = docs.filter((d) => filters.forms.indexOf(d.pub_form) > -1);
        }

        // Screening filter
        if (filters.screening.length) {
            docs = docs.filter((d) => {
                const s = d.screening || 'NOT_SCREENED';
                return filters.screening.indexOf(s) > -1;
            });
        }

        // Date range
        if (filters.dateFrom) {
            docs = docs.filter((d) => d.date && d.date >= filters.dateFrom);
        }
        if (filters.dateTo) {
            docs = docs.filter((d) => d.date && d.date <= filters.dateTo);
        }

        // Sort
        docs = docs.slice().sort((a, b) => {
            const va = getSortValue(a, state.sortKey);
            const vb = getSortValue(b, state.sortKey);
            if (va < vb) return state.sortAsc ? -1 : 1;
            if (va > vb) return state.sortAsc ? 1 : -1;
            return 0;
        });

        state.filtered = docs;
        syncUrlState();
        renderResults();
    }

    function syncUrlState() {
        const params = {};
        if (state.searchQuery) params.q = state.searchQuery;
        if (filters.types.length === 1) params.type = filters.types[0];
        if (filters.langs.length === 1) params.lang = filters.langs[0];
        if (filters.forms.length === 1) params.form = filters.forms[0];
        if (filters.screening.length === 1) params.screening = filters.screening[0];
        if (state.view !== 'table') params.view = state.view;
        E.setParams(params);
    }

    function getSortValue(doc, key) {
        if (key === 'id') return parseInt(doc.id, 10);
        if (key === 'pages') return doc.page_count || 0;
        if (key === 'screening') return doc.screening || 'Z_NONE';
        const v = doc[key];
        return v ? String(v).toLowerCase() : '';
    }

    function _screeningBadgeHtml(doc) {
        return ' ' + E.screeningBadgeHtml(doc.screening);
    }

    // --- Rendering ---
    function renderResults() {
        updateResultCount();
        if (state.view === 'gallery') {
            renderGallery();
        } else if (state.view === 'cards') {
            renderCards();
        } else {
            renderTable();
        }
    }

    function updateResultCount() {
        const countEl = E.$('#result-count');
        if (countEl) {
            countEl.textContent = `Zeige ${state.filtered.length} von ${state.documents.length} Dokumenten`;
        }
    }

    function renderTable() {
        const container = E.$('#catalog-results');
        if (!container) return;

        const cols = [
            { key: 'id', label: 'ID' },
            { key: 'title', label: 'Titel' },
            { key: 'author', label: 'Autor' },
            { key: 'date', label: 'Datum' },
            { key: 'type', label: 'Typ' },
            { key: 'lang', label: 'Sprache' },
            { key: 'pages', label: 'Seiten' },
            { key: 'screening', label: 'Screening' }
        ];
        let html = '<div class="ed-table-wrap"><table class="ed-table">';
        html += '<thead><tr>';
        cols.forEach((c) => {
            const sorted = state.sortKey === c.key;
            const arrow = sorted ? (state.sortAsc ? ' &#9650;' : ' &#9660;') : ' <span class="sort-icon">&#9650;</span>';
            html += `<th data-sort="${c.key}"${sorted ? ' class="sorted"' : ''}>${c.label}${arrow}</th>`;
        });
        html += '</tr></thead><tbody>';

        state.filtered.forEach((d) => {
            html += `<tr onclick="window.location.href='reader.html?doc=${E.esc(d.id)}'" tabindex="0">`;
            html += `<td class="td-id">${E.esc(d.id)}`;
            if (d.demo) html += ' <span class="ed-badge ed-badge-demo">Demo</span>';
            html += _curationBadgeHtml(d.id);
            html += '</td>';
            html += `<td class="td-title">${E.esc(d.title || '-')}`;
            if (state.searchSnippets[d.id]) html += `<div class="ed-search-snippet">${state.searchSnippets[d.id]}</div>`;
            html += '</td>';
            html += `<td>${E.esc(d.author || '-')}</td>`;
            html += `<td>${E.esc(d.date || '-')}</td>`;
            html += `<td><span class="ed-badge ed-badge-type">${E.esc(d.type)}</span></td>`;
            html += `<td>${E.esc(d.lang)}</td>`;
            html += `<td>${d.page_count || '-'}</td>`;
            html += `<td>${_screeningBadgeHtml(d)}</td>`;
            html += '</tr>';
        });

        html += '</tbody></table></div>';
        container.innerHTML = html;

        // Table header sort click
        E.$$('.ed-table th[data-sort]').forEach((th) => {
            th.addEventListener('click', () => {
                const key = th.getAttribute('data-sort');
                if (state.sortKey === key) {
                    state.sortAsc = !state.sortAsc;
                } else {
                    state.sortKey = key;
                    state.sortAsc = true;
                }
                // Sync dropdown
                const sel = E.$('#catalog-sort');
                if (sel) sel.value = (state.sortAsc ? '' : '-') + key;
                applyFilters();
            });
        });

        // Keyboard nav for rows
        E.$$('.ed-table tbody tr').forEach((tr) => {
            tr.addEventListener('keydown', (e) => {
                if (e.key === 'Enter') tr.click();
            });
        });
    }

    function renderCards() {
        const container = E.$('#catalog-results');
        if (!container) return;

        let html = '<div class="ed-catalog-cards">';
        state.filtered.forEach((d) => {
            html += E.buildCardHtml(d, { showPages: true });
        });
        html += '</div>';
        container.innerHTML = html;
    }

    function renderGallery() {
        const container = E.$('#catalog-results');
        if (!container) return;

        let html = '<div class="ed-catalog-gallery">';
        state.filtered.forEach((d) => {
            const imgSrc = E.imagePath(d.id, 1);
            const title = d.title || 'Dokument ' + d.id;
            const placeholder = `<div class="ed-gallery-item-placeholder">Dok. ${E.esc(d.id)}</div>`;
            html += `<a href="reader.html?doc=${E.esc(d.id)}" class="ed-gallery-item">`;
            html += `<img src="${imgSrc}" alt="${E.esc(title)}" loading="lazy" onerror="this.outerHTML='${placeholder.replace(/'/g, "\\'")}'">`;
            html += '<div class="ed-gallery-item-overlay">';
            html += `<div class="ed-gallery-item-title">${E.esc(title)}</div>`;
            html += `<div class="ed-gallery-item-meta">${E.esc(d.id)} &middot; ${d.page_count || '?'} S.${_screeningBadgeHtml(d)}</div>`;
            html += '</div></a>';
        });
        html += '</div>';
        container.innerHTML = html;
    }

    // --- Curation Status (Phase 4) ---
    function _checkCurationServer() {
        const apiBase = window.location.origin + '/api';
        fetch(apiBase + '/health', { method: 'GET' })
            .then((r) => {
                if (!r.ok) return;
                state.serverAvailable = true;
                // Load statuses for all visible docs (batched)
                _loadCurationStatuses();
            })
            .catch(() => {});
    }

    function _loadCurationStatuses() {
        if (!state.serverAvailable) return;
        const apiBase = window.location.origin + '/api';
        const docs = state.documents;
        let pending = 0;
        const maxConcurrent = 10;
        let changed = false;
        let renderTimer = null;

        // Debounced re-render: at most once per 500ms
        function scheduleRender() {
            if (renderTimer) return;
            renderTimer = setTimeout(() => {
                renderTimer = null;
                if (changed) {
                    changed = false;
                    renderResults();
                }
            }, 500);
        }

        function loadNext(i) {
            if (i >= docs.length) {
                // Final render for any remaining changes
                if (changed) renderResults();
                return;
            }
            if (pending >= maxConcurrent) {
                setTimeout(() => { loadNext(i); }, 50);
                return;
            }
            pending++;
            fetch(`${apiBase}/tei/${docs[i].id}/status`)
                .then((r) => r.ok ? r.json() : null)
                .then((meta) => {
                    pending--;
                    if (meta && meta.status && meta.status !== 'pipeline') {
                        state.curationStatuses[docs[i].id] = meta.status;
                        changed = true;
                        scheduleRender();
                    }
                    loadNext(i + 1);
                })
                .catch(() => {
                    pending--;
                    loadNext(i + 1);
                });
        }
        loadNext(0);
    }

    function _curationBadgeHtml(docId) {
        const status = state.curationStatuses[docId];
        if (!status) return '';
        return ' ' + E.curationBadgeHtml(status);
    }

    // --- Auto-init ---
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    ZBZ.EditionCatalog = { applyFilters: applyFilters };
})();
