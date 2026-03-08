/**
 * ZBZ Edition – Catalog Module
 * Document catalog with faceted filters, search, table/card views.
 * Namespace: ZBZ.EditionCatalog (ES5, IIFE)
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
        curationStatuses: {},
        serverAvailable: false
    };

    var filters = {
        types: [],
        langs: [],
        forms: [],
        dateFrom: '',
        dateTo: ''
    };

    // --- Init ---
    function init() {
        E.loadCatalog().then(function (catalog) {
            if (!catalog) return;
            state.catalog = catalog;
            state.documents = catalog.documents || [];
            state.filtered = state.documents.slice();

            initSearchIndex();
            renderFilters();
            bindEvents();
            applyFilters();
            _checkCurationServer();
        });
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
            state.searchIndex.addAll(state.documents.map(function (d) {
                return {
                    id: d.id,
                    title: d.title || '',
                    author: d.author || '',
                    desc: d.desc || ''
                };
            }));
        } catch (e) {
            console.warn('MiniSearch init failed, falling back to simple search:', e);
            state.searchIndex = null;
        }
    }

    // --- Filter Rendering ---
    function renderFilters() {
        var catalog = state.catalog;
        if (!catalog) return;

        // Types
        var typeContainer = E.$('#filter-types');
        if (typeContainer) {
            var types = catalog.corpus && catalog.corpus.types ? catalog.corpus.types : {};
            renderCheckboxGroup(typeContainer, types, 'type', E.TYPE_LABELS);
        }

        // Languages
        var langContainer = E.$('#filter-langs');
        if (langContainer) {
            var langs = catalog.corpus && catalog.corpus.languages ? catalog.corpus.languages : {};
            // Show top 6 languages only
            var sorted = Object.keys(langs).sort(function (a, b) { return langs[b] - langs[a]; });
            var top = {};
            sorted.slice(0, 6).forEach(function (k) { top[k] = langs[k]; });
            renderCheckboxGroup(langContainer, top, 'lang', E.LANG_LABELS);
        }

        // Forms
        var formContainer = E.$('#filter-forms');
        if (formContainer) {
            var forms = catalog.corpus && catalog.corpus.forms ? catalog.corpus.forms : {};
            renderCheckboxGroup(formContainer, forms, 'form', E.PUB_FORM_LABELS);
        }
    }

    function renderCheckboxGroup(container, counts, prefix, labels) {
        container.innerHTML = '';
        Object.keys(counts).forEach(function (key) {
            var label = document.createElement('label');
            label.className = 'ed-filter-label';

            var cb = document.createElement('input');
            cb.type = 'checkbox';
            cb.value = key;
            cb.name = prefix;
            cb.addEventListener('change', function () {
                updateFilterState();
                applyFilters();
            });

            var text = document.createTextNode(' ' + ((labels && labels[key]) || key));
            var count = document.createElement('span');
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
        var searchInput = E.$('#catalog-search');
        if (searchInput) {
            searchInput.addEventListener('input', E.debounce(function () {
                state.searchQuery = searchInput.value.trim();
                applyFilters();
            }, 200));
        }

        // View toggle
        E.$$('.ed-view-btn').forEach(function (btn) {
            btn.addEventListener('click', function () {
                state.view = btn.getAttribute('data-view');
                E.$$('.ed-view-btn').forEach(function (b) { b.classList.toggle('active', b === btn); });
                renderResults();
            });
        });

        // Sort select
        var sortSelect = E.$('#catalog-sort');
        if (sortSelect) {
            sortSelect.addEventListener('change', function () {
                var val = sortSelect.value;
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
        var dateFrom = E.$('#filter-date-from');
        var dateTo = E.$('#filter-date-to');
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
    }

    function getCheckedValues(name) {
        return E.$$('input[name="' + name + '"]:checked').map(function (cb) { return cb.value; });
    }

    function applyFilters() {
        var docs = state.documents;

        // Search
        if (state.searchQuery && state.searchIndex) {
            var results = state.searchIndex.search(state.searchQuery);
            var ids = {};
            results.forEach(function (r) { ids[r.id] = true; });
            docs = docs.filter(function (d) { return ids[d.id]; });
        } else if (state.searchQuery) {
            var q = state.searchQuery.toLowerCase();
            docs = docs.filter(function (d) {
                return (d.title && d.title.toLowerCase().indexOf(q) > -1) ||
                       (d.author && d.author.toLowerCase().indexOf(q) > -1) ||
                       (d.id.indexOf(q) > -1) ||
                       (d.desc && d.desc.toLowerCase().indexOf(q) > -1);
            });
        }

        // Type filter
        if (filters.types.length) {
            docs = docs.filter(function (d) { return filters.types.indexOf(d.type) > -1; });
        }

        // Language filter
        if (filters.langs.length) {
            docs = docs.filter(function (d) { return filters.langs.indexOf(d.lang) > -1; });
        }

        // Form filter
        if (filters.forms.length) {
            docs = docs.filter(function (d) { return filters.forms.indexOf(d.pub_form) > -1; });
        }

        // Date range
        if (filters.dateFrom) {
            docs = docs.filter(function (d) { return d.date && d.date >= filters.dateFrom; });
        }
        if (filters.dateTo) {
            docs = docs.filter(function (d) { return d.date && d.date <= filters.dateTo; });
        }

        // Sort
        docs = docs.slice().sort(function (a, b) {
            var va = getSortValue(a, state.sortKey);
            var vb = getSortValue(b, state.sortKey);
            if (va < vb) return state.sortAsc ? -1 : 1;
            if (va > vb) return state.sortAsc ? 1 : -1;
            return 0;
        });

        state.filtered = docs;
        renderResults();
    }

    function getSortValue(doc, key) {
        if (key === 'id') return parseInt(doc.id, 10);
        if (key === 'pages') return doc.page_count || 0;
        var v = doc[key];
        return v ? String(v).toLowerCase() : '';
    }

    // --- Rendering ---
    function renderResults() {
        updateResultCount();
        if (state.view === 'cards') {
            renderCards();
        } else {
            renderTable();
        }
    }

    function updateResultCount() {
        var countEl = E.$('#result-count');
        if (countEl) {
            countEl.textContent = 'Zeige ' + state.filtered.length + ' von ' + state.documents.length + ' Dokumenten';
        }
    }

    function renderTable() {
        var container = E.$('#catalog-results');
        if (!container) return;

        var cols = [
            { key: 'id', label: 'ID' },
            { key: 'title', label: 'Titel' },
            { key: 'author', label: 'Autor' },
            { key: 'date', label: 'Datum' },
            { key: 'type', label: 'Typ' },
            { key: 'lang', label: 'Sprache' },
            { key: 'pages', label: 'Seiten' }
        ];
        var html = '<div class="ed-table-wrap"><table class="ed-table">';
        html += '<thead><tr>';
        cols.forEach(function (c) {
            var sorted = state.sortKey === c.key;
            var arrow = sorted ? (state.sortAsc ? ' &#9650;' : ' &#9660;') : ' <span class="sort-icon">&#9650;</span>';
            html += '<th data-sort="' + c.key + '"' + (sorted ? ' class="sorted"' : '') + '>' + c.label + arrow + '</th>';
        });
        html += '</tr></thead><tbody>';

        state.filtered.forEach(function (d) {
            html += '<tr onclick="window.location.href=\'reader.html?doc=' + E.esc(d.id) + '\'" tabindex="0">';
            html += '<td class="td-id">' + E.esc(d.id);
            if (d.demo) html += ' <span class="ed-badge ed-badge-demo">Demo</span>';
            html += _curationBadgeHtml(d.id);
            html += '</td>';
            html += '<td class="td-title">' + E.esc(d.title || '-') + '</td>';
            html += '<td>' + E.esc(d.author || '-') + '</td>';
            html += '<td>' + E.esc(d.date || '-') + '</td>';
            html += '<td><span class="ed-badge ed-badge-type">' + E.esc(d.type) + '</span></td>';
            html += '<td>' + E.esc(d.lang) + '</td>';
            html += '<td>' + (d.page_count || '-') + '</td>';
            html += '</tr>';
        });

        html += '</tbody></table></div>';
        container.innerHTML = html;

        // Table header sort click
        E.$$('.ed-table th[data-sort]').forEach(function (th) {
            th.addEventListener('click', function () {
                var key = th.getAttribute('data-sort');
                if (state.sortKey === key) {
                    state.sortAsc = !state.sortAsc;
                } else {
                    state.sortKey = key;
                    state.sortAsc = true;
                }
                // Sync dropdown
                var sel = E.$('#catalog-sort');
                if (sel) sel.value = (state.sortAsc ? '' : '-') + key;
                applyFilters();
            });
        });

        // Keyboard nav for rows
        E.$$('.ed-table tbody tr').forEach(function (tr) {
            tr.addEventListener('keydown', function (e) {
                if (e.key === 'Enter') tr.click();
            });
        });
    }

    function renderCards() {
        var container = E.$('#catalog-results');
        if (!container) return;

        var html = '<div class="ed-catalog-cards">';
        state.filtered.forEach(function (d) {
            html += E.buildCardHtml(d, { showPages: true });
        });
        html += '</div>';
        container.innerHTML = html;
    }

    // --- Curation Status (Phase 4) ---
    function _checkCurationServer() {
        var apiBase = window.location.origin + '/api';
        fetch(apiBase + '/health', { method: 'GET' })
            .then(function (r) {
                if (!r.ok) return;
                state.serverAvailable = true;
                // Load statuses for all visible docs (batched)
                _loadCurationStatuses();
            })
            .catch(function () {});
    }

    function _loadCurationStatuses() {
        if (!state.serverAvailable) return;
        var apiBase = window.location.origin + '/api';
        var docs = state.documents;
        var pending = 0;
        var maxConcurrent = 10;
        var changed = false;
        var renderTimer = null;

        // Debounced re-render: at most once per 500ms
        function scheduleRender() {
            if (renderTimer) return;
            renderTimer = setTimeout(function () {
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
                setTimeout(function () { loadNext(i); }, 50);
                return;
            }
            pending++;
            fetch(apiBase + '/tei/' + docs[i].id + '/status')
                .then(function (r) { return r.ok ? r.json() : null; })
                .then(function (meta) {
                    pending--;
                    if (meta && meta.status && meta.status !== 'pipeline') {
                        state.curationStatuses[docs[i].id] = meta.status;
                        changed = true;
                        scheduleRender();
                    }
                    loadNext(i + 1);
                })
                .catch(function () {
                    pending--;
                    loadNext(i + 1);
                });
        }
        loadNext(0);
    }

    function _curationBadgeHtml(docId) {
        var status = state.curationStatuses[docId];
        if (!status) return '';
        var labels = { draft: 'Entwurf', in_review: 'Pruefung', approved: 'Freigegeben' };
        var classes = { draft: 'ed-badge-curation-draft', in_review: 'ed-badge-curation-review', approved: 'ed-badge-curation-approved' };
        return ' <span class="ed-badge ' + (classes[status] || '') + '">' + E.esc(labels[status] || status) + '</span>';
    }

    // --- Auto-init ---
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    ZBZ.EditionCatalog = { applyFilters: applyFilters };
})();
