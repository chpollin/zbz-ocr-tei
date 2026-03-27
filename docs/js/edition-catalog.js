/**
 * ZBZ Edition – Catalog Module (Rewrite)
 * Document catalog with faceted filters, search, table/card/gallery views.
 * Namespace: ZBZ.EditionCatalog (ES6+, IIFE)
 */
(function () {
    'use strict';

    var E = ZBZ.Edition;

    var state = {
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
        _searchData: null,
        curationStatuses: {},
        serverAvailable: false
    };

    var filters = {
        types: [], langs: [], forms: [], screening: [],
        dateFrom: '', dateTo: ''
    };

    // --- Init ---
    function init() {
        Promise.all([E.loadCatalog(), E.loadSearchIndex()]).then(function (results) {
            var catalog = results[0];
            var searchData = results[1];
            if (!catalog) return;
            state.catalog = catalog;
            state.documents = catalog.documents || [];
            state.filtered = state.documents.slice();

            if (searchData && searchData.length) {
                state.fullTextIndex = E.createFullTextSearchIndex(searchData);
                state._searchData = searchData;
            }

            initSearchIndex();
            renderFilters();
            bindEvents();
            readUrlFilters();
            applyFilters();
            checkCurationServer();

            ZBZ.log('Catalog', state.documents.length + ' Docs | Volltext: ' + (state.fullTextIndex ? 'aktiv' : 'aus'));
        });
    }

    // --- URL pre-filter ---
    function readUrlFilters() {
        var q = E.getParam('q');
        if (q) {
            state.searchQuery = q;
            var input = E.$('#catalog-search');
            if (input) input.value = q;
        }
        ['type', 'lang', 'form', 'screening'].forEach(function (param) {
            var val = E.getParam(param);
            if (val) {
                var cb = E.$('input[name="' + param + '"][value="' + val + '"]');
                if (cb) cb.checked = true;
            }
        });
        var view = E.getParam('view');
        if (view && (view === 'table' || view === 'cards' || view === 'gallery')) {
            state.view = view;
            E.$$('.ed-view-btn').forEach(function (b) {
                var isActive = b.getAttribute('data-view') === view;
                b.classList.toggle('active', isActive);
                b.setAttribute('aria-pressed', String(isActive));
            });
        }
        updateFilterState();
    }

    // --- MiniSearch (metadata) ---
    function initSearchIndex() {
        if (typeof MiniSearch === 'undefined') return;
        try {
            state.searchIndex = new MiniSearch({
                fields: ['title', 'author', 'desc', 'id'],
                storeFields: ['id'],
                searchOptions: { boost: { title: 3, author: 2, id: 1 }, fuzzy: 0.2, prefix: true }
            });
            state.searchIndex.addAll(state.documents.map(function (d) {
                return { id: d.id, title: d.title || '', author: d.author || '', desc: d.desc || '' };
            }));
        } catch (e) {
            state.searchIndex = null;
        }
    }

    // --- Filter Rendering ---
    function renderFilters() {
        var catalog = state.catalog;
        if (!catalog) return;

        var typeContainer = E.$('#filter-types');
        if (typeContainer && catalog.corpus && catalog.corpus.types) {
            renderCheckboxGroup(typeContainer, catalog.corpus.types, 'type', E.TYPE_LABELS);
        }

        var langContainer = E.$('#filter-langs');
        if (langContainer && catalog.corpus && catalog.corpus.languages) {
            var langs = catalog.corpus.languages;
            var sorted = Object.keys(langs).sort(function (a, b) { return langs[b] - langs[a]; });
            var top = {};
            sorted.slice(0, 6).forEach(function (k) { top[k] = langs[k]; });
            renderCheckboxGroup(langContainer, top, 'lang', E.LANG_LABELS);
        }

        var formContainer = E.$('#filter-forms');
        if (formContainer && catalog.corpus && catalog.corpus.forms) {
            renderCheckboxGroup(formContainer, catalog.corpus.forms, 'form', E.PUB_FORM_LABELS);
        }

        var screenContainer = E.$('#filter-screening');
        if (screenContainer && catalog.corpus && catalog.corpus.screening) {
            renderCheckboxGroup(screenContainer, catalog.corpus.screening, 'screening', E.SCREENING_LABELS);
        }
    }

    function renderCheckboxGroup(container, counts, prefix, labels) {
        container.innerHTML = '';
        Object.keys(counts).forEach(function (key) {
            var label = document.createElement('label');
            label.className = 'ed-filter-label';
            var cb = document.createElement('input');
            cb.type = 'checkbox'; cb.value = key; cb.name = prefix;
            cb.addEventListener('change', function () { updateFilterState(); applyFilters(); });
            var text = document.createTextNode(' ' + ((labels && labels[key]) || key));
            var count = document.createElement('span');
            count.className = 'ed-filter-count'; count.textContent = counts[key];
            label.appendChild(cb); label.appendChild(text); label.appendChild(count);
            container.appendChild(label);
        });
    }

    // --- Events ---
    function bindEvents() {
        var searchInput = E.$('#catalog-search');
        if (searchInput) {
            searchInput.addEventListener('input', E.debounce(function () {
                state.searchQuery = searchInput.value.trim();
                applyFilters();
            }, 200));
        }

        E.$$('.ed-view-btn').forEach(function (btn) {
            btn.addEventListener('click', function () {
                state.view = btn.getAttribute('data-view');
                E.$$('.ed-view-btn').forEach(function (b) {
                    b.classList.toggle('active', b === btn);
                    b.setAttribute('aria-pressed', String(b === btn));
                });
                renderResults();
            });
        });

        var sortSelect = E.$('#catalog-sort');
        if (sortSelect) {
            sortSelect.addEventListener('change', function () {
                var val = sortSelect.value;
                if (val.charAt(0) === '-') { state.sortKey = val.substring(1); state.sortAsc = false; }
                else { state.sortKey = val; state.sortAsc = true; }
                applyFilters();
            });
        }

        var dateFrom = E.$('#filter-date-from');
        var dateTo = E.$('#filter-date-to');
        if (dateFrom) dateFrom.addEventListener('input', E.debounce(function () { filters.dateFrom = dateFrom.value; applyFilters(); }, 300));
        if (dateTo) dateTo.addEventListener('input', E.debounce(function () { filters.dateTo = dateTo.value; applyFilters(); }, 300));
    }

    // --- Filter Logic ---
    function updateFilterState() {
        filters.types = getCheckedValues('type');
        filters.langs = getCheckedValues('lang');
        filters.forms = getCheckedValues('form');
        filters.screening = getCheckedValues('screening');
    }

    function getCheckedValues(name) {
        return E.$$('input[name="' + name + '"]:checked').map(function (cb) { return cb.value; });
    }

    function applyFilters() {
        var docs = state.documents;
        state.searchSnippets = {};

        if (state.searchQuery) {
            var metaIds = {}, fullIds = {};
            if (state.searchIndex) {
                state.searchIndex.search(state.searchQuery).forEach(function (r) { metaIds[r.id] = true; });
            }
            if (state.fullTextIndex) {
                var textMap = {};
                if (state._searchData) state._searchData.forEach(function (d) { textMap[d.id] = d.text || ''; });
                state.fullTextIndex.search(state.searchQuery, { limit: 100 }).forEach(function (r) {
                    fullIds[r.id] = true;
                    if (textMap[r.id]) state.searchSnippets[r.id] = E.extractSnippet(textMap[r.id], state.searchQuery);
                });
            }
            var q = state.searchQuery.toLowerCase();
            docs = docs.filter(function (d) {
                if (metaIds[d.id] || fullIds[d.id]) return true;
                return (d.title && d.title.toLowerCase().indexOf(q) > -1) ||
                       (d.author && d.author.toLowerCase().indexOf(q) > -1) ||
                       (d.id.indexOf(q) > -1) ||
                       (d.desc && d.desc.toLowerCase().indexOf(q) > -1);
            });
        }

        if (filters.types.length) docs = docs.filter(function (d) { return filters.types.indexOf(d.type) > -1; });
        if (filters.langs.length) docs = docs.filter(function (d) { return filters.langs.indexOf(d.lang) > -1; });
        if (filters.forms.length) docs = docs.filter(function (d) { return filters.forms.indexOf(d.pub_form) > -1; });
        if (filters.screening.length) docs = docs.filter(function (d) { return filters.screening.indexOf(d.screening || 'NOT_SCREENED') > -1; });
        if (filters.dateFrom) docs = docs.filter(function (d) { return d.date && d.date >= filters.dateFrom; });
        if (filters.dateTo) docs = docs.filter(function (d) { return d.date && d.date <= filters.dateTo; });

        docs = docs.slice().sort(function (a, b) {
            var va = getSortValue(a, state.sortKey), vb = getSortValue(b, state.sortKey);
            if (va < vb) return state.sortAsc ? -1 : 1;
            if (va > vb) return state.sortAsc ? 1 : -1;
            return 0;
        });

        state.filtered = docs;
        syncUrlState();
        renderResults();
    }

    function syncUrlState() {
        var params = {};
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
        var v = doc[key];
        return v ? String(v).toLowerCase() : '';
    }

    // --- Rendering ---
    function renderResults() {
        updateResultCount();
        if (state.view === 'gallery') renderGallery();
        else if (state.view === 'cards') renderCards();
        else renderTable();
    }

    function updateResultCount() {
        var el = E.$('#result-count');
        if (el) el.textContent = 'Zeige ' + state.filtered.length + ' von ' + state.documents.length + ' Dokumenten';
    }

    function renderTable() {
        var container = E.$('#catalog-results');
        if (!container) return;

        var cols = [
            { key: 'id', label: 'ID' }, { key: 'title', label: 'Titel' },
            { key: 'author', label: 'Autor' }, { key: 'date', label: 'Datum' },
            { key: 'type', label: 'Typ' }, { key: 'lang', label: 'Sprache' },
            { key: 'pages', label: 'Seiten' }, { key: 'screening', label: 'Screening' }
        ];

        var html = '<div class="ed-table-wrap"><table class="ed-table"><thead><tr>';
        cols.forEach(function (c) {
            var sorted = state.sortKey === c.key;
            var arrow = sorted ? (state.sortAsc ? ' &#9650;' : ' &#9660;') : ' <span class="sort-icon">&#9650;</span>';
            html += '<th data-sort="' + c.key + '"' + (sorted ? ' class="sorted"' : '') + '>' + c.label + arrow + '</th>';
        });
        html += '</tr></thead><tbody>';

        state.filtered.forEach(function (d) {
            var curBadge = getCurationBadgeHtml(d);
            html += '<tr onclick="window.location.href=\'reader.html?doc=' + E.esc(d.id) + '\'" tabindex="0">';
            html += '<td class="td-id">' + E.esc(d.id) + curBadge + '</td>';
            html += '<td class="td-title">' + E.esc(d.title || '-');
            if (state.searchSnippets[d.id]) html += '<div class="ed-search-snippet">' + state.searchSnippets[d.id] + '</div>';
            html += '</td>';
            html += '<td>' + E.esc(d.author || '-') + '</td>';
            html += '<td>' + E.esc(d.date || '-') + '</td>';
            html += '<td><span class="ed-badge ed-badge-type">' + E.esc(d.type) + '</span></td>';
            html += '<td>' + E.esc(d.lang) + '</td>';
            html += '<td>' + (d.page_count || '-') + '</td>';
            html += '<td>' + E.screeningBadgeHtml(d.screening) + '</td>';
            html += '</tr>';
        });

        html += '</tbody></table></div>';
        container.innerHTML = html;

        // Table header sort
        E.$$('.ed-table th[data-sort]').forEach(function (th) {
            th.addEventListener('click', function () {
                var key = th.getAttribute('data-sort');
                if (state.sortKey === key) state.sortAsc = !state.sortAsc;
                else { state.sortKey = key; state.sortAsc = true; }
                var sel = E.$('#catalog-sort');
                if (sel) sel.value = (state.sortAsc ? '' : '-') + key;
                applyFilters();
            });
        });

        // Keyboard nav
        E.$$('.ed-table tbody tr').forEach(function (tr) {
            tr.addEventListener('keydown', function (e) { if (e.key === 'Enter') tr.click(); });
        });
    }

    function renderCards() {
        var container = E.$('#catalog-results');
        if (!container) return;
        var html = '<div class="ed-catalog-cards">';
        state.filtered.forEach(function (d) { html += E.buildCardHtml(d, { showPages: true }); });
        html += '</div>';
        container.innerHTML = html;
    }

    function renderGallery() {
        var container = E.$('#catalog-results');
        if (!container) return;
        var html = '<div class="ed-catalog-gallery">';
        state.filtered.forEach(function (d) {
            var imgSrc = E.imagePath(d.id, 1);
            var title = d.title || 'Dokument ' + d.id;
            var placeholder = '<div class="ed-gallery-item-placeholder">Dok. ' + E.esc(d.id) + '</div>';
            html += '<a href="reader.html?doc=' + E.esc(d.id) + '" class="ed-gallery-item">';
            html += '<img src="' + imgSrc + '" alt="' + E.esc(title) + '" loading="lazy" onerror="this.outerHTML=\'' + placeholder.replace(/'/g, "\\'") + '\'">';
            html += '<div class="ed-gallery-item-overlay">';
            html += '<div class="ed-gallery-item-title">' + E.esc(title) + '</div>';
            html += '<div class="ed-gallery-item-meta">' + E.esc(d.id) + ' &middot; ' + (d.page_count || '?') + ' S. ' + E.screeningBadgeHtml(d.screening) + '</div>';
            html += '</div></a>';
        });
        html += '</div>';
        container.innerHTML = html;
    }

    // --- Curation (Phase 4, localhost only) ---
    function checkCurationServer() {
        var host = window.location.hostname;
        if (host !== 'localhost' && host !== '127.0.0.1') return;
        fetch(window.location.origin + '/api/health', { method: 'GET' })
            .then(function (r) { if (r.ok) { state.serverAvailable = true; loadCurationStatuses(); } })
            .catch(function () {});
    }

    function loadCurationStatuses() {
        if (!state.serverAvailable) return;
        var apiBase = window.location.origin + '/api';
        var docs = state.documents;
        var pending = 0, maxC = 10, changed = false, timer = null;

        function scheduleRender() {
            if (timer) return;
            timer = setTimeout(function () { timer = null; if (changed) { changed = false; renderResults(); } }, 500);
        }

        function loadNext(i) {
            if (i >= docs.length) { if (changed) renderResults(); return; }
            if (pending >= maxC) { setTimeout(function () { loadNext(i); }, 50); return; }
            pending++;
            fetch(apiBase + '/tei/' + docs[i].id + '/status')
                .then(function (r) { return r.ok ? r.json() : null; })
                .then(function (meta) {
                    pending--;
                    if (meta && meta.status && meta.status !== 'pipeline') {
                        state.curationStatuses[docs[i].id] = meta.status;
                        changed = true; scheduleRender();
                    }
                    loadNext(i + 1);
                })
                .catch(function () { pending--; loadNext(i + 1); });
        }
        loadNext(0);
    }

    function getCurationBadgeHtml(doc) {
        var status = state.curationStatuses[doc.id] || doc.curation;
        if (!status || status === 'uncurated') return '';
        return ' ' + E.curationBadgeHtml(status);
    }

    // --- Auto-init ---
    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
    else init();

    ZBZ.EditionCatalog = { applyFilters: applyFilters };
})();
