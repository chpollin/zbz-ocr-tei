/**
 * ZBZ Edition – Unified Register Module
 * Single-page entity register with type tabs, faceted filters, search,
 * table/card views, and detail expansion.
 * Namespace: ZBZ.Register (ES6+, IIFE)
 */
(function () {
    'use strict';

    const E = ZBZ.Edition;
    const $ = E.$;
    const $$ = E.$$;
    const _log = (msg) => console.log(`[ZBZ:Register] ${msg}`);

    const TYPES = ['person', 'organization', 'place', 'work'];

    const TYPE_LABELS = {
        person: 'Personen',
        organization: 'Organisationen',
        place: 'Orte',
        work: 'Werke'
    };

    const TYPE_SINGULAR = {
        person: 'Person',
        organization: 'Organisation',
        place: 'Ort',
        work: 'Werk'
    };

    const state = {
        data: null,
        allEntities: [],
        byType: {},          // { person: [...], organization: [...], ... }
        filtered: [],
        catalog: null,
        activeType: 'person',
        view: 'table',
        sortKey: 'name',
        sortAsc: true,
        searchIndices: {},    // MiniSearch per type
        searchQuery: '',
        expandedId: null
    };

    const filters = {
        resolution: [],
        occurrence: []
    };

    // --- Init ---

    function init() {
        Promise.all([E.loadEntityRegister(), E.loadCatalog()])
            .then(function (results) {
                var registerData = results[0];
                var catalogData = results[1];

                if (!registerData) {
                    $('#register-results').innerHTML = '<p>Register-Daten nicht verfuegbar.</p>';
                    return;
                }
                state.data = registerData;
                state.allEntities = registerData.entities;
                state.catalog = catalogData;

                // Group by type
                TYPES.forEach(function (t) {
                    state.byType[t] = state.allEntities.filter(function (e) { return e.type === t; });
                });

                readUrlState();
                renderTabCounts();
                initSearchIndices();
                renderTypeStats();
                bindEvents();
                applyFilters();

                _log(state.allEntities.length + ' Entities geladen, aktiv: ' + TYPE_LABELS[state.activeType]);
            });
    }

    // --- URL State ---

    // Infer entity type from zbz-ID prefix (zbz-p.* → person, zbz-o.* → organization, etc.)
    var ID_TYPE_MAP = { 'p': 'person', 'o': 'organization', 'l': 'place', 'w': 'work' };

    function readUrlState() {
        var type = E.getParam('type');
        if (type && TYPES.indexOf(type) > -1) {
            state.activeType = type;
        } else {
            // Auto-detect type from ?id= param (e.g. zbz-p.1 → person)
            var idParam = E.getParam('id');
            if (idParam) {
                var m = idParam.match(/^zbz-([a-z])\./);
                if (m && ID_TYPE_MAP[m[1]]) {
                    state.activeType = ID_TYPE_MAP[m[1]];
                }
            }
        }
        var q = E.getParam('q');
        if (q) {
            state.searchQuery = q;
            var searchEl = $('#register-search');
            if (searchEl) searchEl.value = q;
        }
        var sort = E.getParam('sort');
        if (sort) {
            if (sort.charAt(0) === '-') {
                state.sortKey = sort.slice(1);
                state.sortAsc = false;
            } else {
                state.sortKey = sort;
                state.sortAsc = true;
            }
            var sortEl = $('#register-sort');
            if (sortEl) sortEl.value = sort;
        }
        var view = E.getParam('view');
        if (view === 'cards' || view === 'table') {
            state.view = view;
        }
        var expandId = E.getParam('id');
        if (expandId) {
            state.expandedId = expandId;
        }

        // Sync tab visual
        $$('.ed-register-tab').forEach(function (tab) {
            tab.classList.toggle('active', tab.dataset.type === state.activeType);
            tab.setAttribute('aria-selected', String(tab.dataset.type === state.activeType));
        });

        // Sync view toggle
        $$('.ed-view-btn').forEach(function (btn) {
            var isActive = btn.dataset.view === state.view;
            btn.classList.toggle('active', isActive);
            btn.setAttribute('aria-pressed', String(isActive));
        });
    }

    function syncUrlState() {
        var params = { type: state.activeType !== 'person' ? state.activeType : null };
        if (state.searchQuery) params.q = state.searchQuery;
        var sortVal = (state.sortAsc ? '' : '-') + state.sortKey;
        if (sortVal !== 'name') params.sort = sortVal;
        if (state.view !== 'table') params.view = state.view;
        if (state.expandedId) params.id = state.expandedId;
        E.setParams(params);
    }

    // --- Tab Counts ---

    function renderTabCounts() {
        TYPES.forEach(function (t) {
            var el = $('#tab-count-' + t);
            if (el) el.textContent = state.byType[t].length;
        });
    }

    // --- Type Stats ---

    function renderTypeStats() {
        var summ = state.data && state.data.summary ? state.data.summary.by_type : null;
        var container = $('#register-type-stats');
        if (!container) return;

        var t = state.activeType;
        if (summ && summ[t]) {
            var s = summ[t];
            container.innerHTML =
                '<span>' + E.fmtNum(s.total) + ' ' + TYPE_LABELS[t] + '</span> &middot; ' +
                '<span>' + E.fmtNum(s.with_wikidata) + ' Wikidata</span> &middot; ' +
                '<span>' + E.fmtNum(s.with_gnd) + ' GND</span> &middot; ' +
                '<span>' + E.fmtNum(s.with_docs) + ' in Docs</span>';
        } else {
            var entities = state.byType[t];
            var wd = entities.filter(function (e) { return e.wikidata_qid; }).length;
            var gnd = entities.filter(function (e) { return e.gnd_id; }).length;
            container.innerHTML =
                '<span>' + E.fmtNum(entities.length) + ' Eintraege</span> &middot; ' +
                '<span>' + E.fmtNum(wd) + ' Wikidata</span> &middot; ' +
                '<span>' + E.fmtNum(gnd) + ' GND</span>';
        }
    }

    // --- Search Indices (one per type) ---

    function initSearchIndices() {
        TYPES.forEach(function (t) {
            var idx = new MiniSearch({
                fields: ['name', 'variantStr', 'id'],
                storeFields: ['id'],
                searchOptions: {
                    boost: { name: 3, variantStr: 1, id: 1 },
                    fuzzy: 0.2,
                    prefix: true
                }
            });
            var docs = state.byType[t].map(function (ent, i) {
                return {
                    _msId: i,
                    id: ent.id,
                    name: ent.name,
                    variantStr: (ent.variants || []).join(' ')
                };
            });
            idx.addAll(docs);
            state.searchIndices[t] = idx;
        });
        _log('MiniSearch: ' + TYPES.length + ' Indizes erstellt');
    }

    // --- Read Filters ---

    function readFilters() {
        filters.resolution = Array.from($$('input[name="resolution"]:checked')).map(function (el) { return el.value; });
        filters.occurrence = Array.from($$('input[name="occurrence"]:checked')).map(function (el) { return el.value; });
    }

    // --- Apply Filters ---

    function applyFilters() {
        readFilters();
        var list = state.byType[state.activeType];

        // Search
        if (state.searchQuery.trim()) {
            var results = state.searchIndices[state.activeType].search(state.searchQuery.trim());
            var matchIds = new Set(results.map(function (r) { return r.id; }));
            list = list.filter(function (e) { return matchIds.has(e.id); });
        }

        // Resolution filter
        if (filters.resolution.length > 0) {
            list = list.filter(function (e) {
                if (filters.resolution.indexOf('wikidata') > -1 && e.wikidata_qid) return true;
                if (filters.resolution.indexOf('gnd') > -1 && e.gnd_id) return true;
                if (filters.resolution.indexOf('none') > -1 && !e.wikidata_qid && !e.gnd_id) return true;
                return false;
            });
        }

        // Occurrence filter
        if (filters.occurrence.length > 0 && filters.occurrence.length < 2) {
            if (filters.occurrence.indexOf('with_docs') > -1) {
                list = list.filter(function (e) { return e.doc_count > 0; });
            } else {
                list = list.filter(function (e) { return e.doc_count === 0; });
            }
        }

        // Sort
        list = sortEntities(list);
        state.filtered = list;
        renderResults();
        syncUrlState();
    }

    function sortEntities(list) {
        var key = state.sortKey;
        var dir = state.sortAsc ? 1 : -1;
        return list.slice().sort(function (a, b) {
            var va = a[key];
            var vb = b[key];
            if (typeof va === 'string') {
                va = va.toLowerCase();
                vb = (vb || '').toLowerCase();
                return va.localeCompare(vb, 'de') * dir;
            }
            return ((va || 0) - (vb || 0)) * dir;
        });
    }

    // --- Render Results ---

    function renderResults() {
        var container = $('#register-results');
        var countEl = $('#result-count');
        var typeEntities = state.byType[state.activeType];
        if (countEl) {
            countEl.textContent = E.fmtNum(state.filtered.length) + ' von ' + E.fmtNum(typeEntities.length) + ' ' + TYPE_LABELS[state.activeType];
        }

        if (state.view === 'table') {
            renderTable(container);
        } else {
            renderCards(container);
        }
    }

    // --- Table View ---

    function renderTable(container) {
        var sortIcon = function (key) {
            if (state.sortKey !== key) return '<span class="sort-icon" style="opacity:0.3">&#9650;</span>';
            return state.sortAsc ? '<span class="sort-icon">&#9650;</span>' : '<span class="sort-icon">&#9660;</span>';
        };

        var html = '<div class="ed-table-wrap"><table class="ed-table ed-register-table">' +
            '<thead><tr>' +
            '<th data-sort="name">Name ' + sortIcon('name') + '</th>' +
            '<th data-sort="doc_count" style="width:60px;text-align:right">Dok. ' + sortIcon('doc_count') + '</th>' +
            '<th data-sort="mention_count" style="width:60px;text-align:right">Erw. ' + sortIcon('mention_count') + '</th>' +
            '<th style="width:80px">Links</th>' +
            '<th style="width:80px">ID</th>' +
            '</tr></thead><tbody>';

        state.filtered.forEach(function (ent) {
            var expanded = state.expandedId === ent.id;
            var links = buildLinkBadges(ent);
            var varCount = (ent.variants || []).length;
            var contextPreview = '';
            if (ent.contexts && ent.contexts.length > 0) {
                var ctx = ent.contexts[0];
                contextPreview = '<div class="ed-register-context-preview">' +
                    E.esc(ctx.length > 100 ? ctx.substring(0, 97) + '...' : ctx) + '</div>';
            }

            html += '<tr class="ed-register-row' + (expanded ? ' expanded' : '') + '" data-id="' + E.esc(ent.id) + '">' +
                '<td><strong>' + E.esc(ent.name) + '</strong>' +
                (varCount > 0 ? ' <span class="ed-text-muted">(' + varCount + ')</span>' : '') +
                contextPreview + '</td>' +
                '<td style="text-align:right">' + ent.doc_count + '</td>' +
                '<td style="text-align:right">' + ent.mention_count + '</td>' +
                '<td>' + links + '</td>' +
                '<td><span class="ed-entity-item-zbzid">' + E.esc(ent.id) + '</span></td>' +
                '</tr>';

            if (expanded) {
                html += buildDetailRow(ent, 5);
            }
        });

        html += '</tbody></table></div>';
        container.innerHTML = html;
        bindTableEvents();
    }

    // --- Card View ---

    function renderCards(container) {
        if (state.filtered.length === 0) {
            container.innerHTML = '<p class="ed-text-muted">Keine Eintraege gefunden.</p>';
            return;
        }

        var html = '<div class="ed-catalog-cards">';
        state.filtered.forEach(function (ent) {
            var links = buildLinkBadges(ent);
            var varCount = (ent.variants || []).length;
            html += '<div class="ed-card ed-register-card ed-register-card-' + ent.type + '" data-id="' + E.esc(ent.id) + '">' +
                '<div class="ed-card-body">' +
                '<div class="ed-card-title">' + E.esc(ent.name) + '</div>' +
                '<div class="ed-card-meta">' +
                '<span class="ed-entity-dot ed-entity-dot-' + ent.type + '"></span> ' +
                E.esc(TYPE_SINGULAR[ent.type] || ent.type) +
                (varCount > 0 ? ' &middot; ' + varCount + ' Varianten' : '') +
                '</div>' +
                '<div class="ed-card-stats">' +
                (ent.doc_count > 0 ? '<span>' + ent.doc_count + ' Dok.</span>' : '') +
                (ent.mention_count > 0 ? '<span>' + ent.mention_count + ' Erw.</span>' : '') +
                '</div>' +
                '<div class="ed-card-links">' + links + ' <span class="ed-entity-item-zbzid">' + E.esc(ent.id) + '</span></div>' +
                '</div></div>';
        });
        html += '</div>';

        // Detail expansion
        if (state.expandedId) {
            var ent = state.byType[state.activeType].find(function (e) { return e.id === state.expandedId; });
            if (ent) {
                html += '<div class="ed-register-detail" id="register-detail">' + buildDetailContent(ent) + '</div>';
            }
        }

        container.innerHTML = html;
        bindCardEvents();
    }

    // --- Link Badges ---

    function buildLinkBadges(ent) {
        var html = '';
        if (ent.wikidata_qid) {
            html += '<a class="ed-entity-item-link" href="' + E.esc(ent.wikidata_url) + '" target="_blank" title="Wikidata ' + ent.wikidata_qid + '" onclick="event.stopPropagation()">WD</a> ';
        }
        if (ent.gnd_id) {
            var gndNum = ent.gnd_id.replace('GND:', '');
            html += '<a class="ed-entity-item-link" href="https://lobid.org/gnd/' + E.esc(gndNum) + '" target="_blank" title="GND ' + gndNum + '" onclick="event.stopPropagation()">GND</a>';
        }
        if (!ent.wikidata_qid && !ent.gnd_id) {
            html += '<span class="ed-text-muted" style="font-size:0.75rem">-</span>';
        }
        return html;
    }

    // --- Detail Expansion ---

    function buildDetailRow(ent, colspan) {
        return '<tr class="ed-register-detail-row" data-detail-id="' + E.esc(ent.id) + '">' +
            '<td colspan="' + colspan + '"><div class="ed-register-detail">' +
            buildDetailContent(ent) + '</div></td></tr>';
    }

    function buildDetailContent(ent) {
        var html = '<div class="ed-register-detail-grid">';

        // Variants
        var variants = (ent.variants || []).filter(function (v) { return v && v !== ent.name; });
        if (variants.length > 0) {
            var shown = variants.slice(0, 10);
            html += '<div class="ed-register-detail-section"><h4>Namensvarianten</h4><div class="ed-register-variants">';
            shown.forEach(function (v) { html += '<span class="ed-badge">' + E.esc(v) + '</span> '; });
            if (variants.length > 10) {
                html += '<span class="ed-text-muted">und ' + (variants.length - 10) + ' weitere</span>';
            }
            html += '</div></div>';
        }

        // Documents
        if (ent.doc_ids && ent.doc_ids.length > 0) {
            html += '<div class="ed-register-detail-section"><h4>Vorkommnisse in Dokumenten</h4><div class="ed-register-doc-links">';
            var docs = ent.doc_ids.slice(0, 20);
            docs.forEach(function (docId) {
                var title = lookupDocTitle(docId);
                var shortTitle = title.length > 40 ? title.substring(0, 37) + '...' : title;
                html += '<a class="ed-register-doc-link" href="reader.html?doc=' + E.esc(docId) + '" title="' + E.esc(title) + '">' +
                    E.esc(docId) + ' - ' + E.esc(shortTitle) + '</a> ';
            });
            if (ent.doc_ids.length > 20) {
                html += '<span class="ed-text-muted">und ' + (ent.doc_ids.length - 20) + ' weitere</span>';
            }
            html += '</div></div>';
        }

        // Contexts
        if (ent.contexts && ent.contexts.length > 0) {
            html += '<div class="ed-register-detail-section"><h4>Kontextbeispiele</h4>';
            ent.contexts.forEach(function (ctx) {
                var truncated = ctx.length > 200 ? ctx.slice(0, 200) + '...' : ctx;
                html += '<blockquote class="ed-register-context">' + E.esc(truncated) + '</blockquote>';
            });
            html += '</div>';
        }

        // External links
        html += '<div class="ed-register-detail-section"><h4>Externe Verknuepfungen</h4><div class="ed-register-ext-links">';
        if (ent.wikidata_qid) {
            html += '<a class="ed-btn ed-btn-sm" href="' + E.esc(ent.wikidata_url) + '" target="_blank">Wikidata: ' + E.esc(ent.wikidata_qid) + '</a> ';
        }
        if (ent.gnd_id) {
            var gndNum = ent.gnd_id.replace('GND:', '');
            html += '<a class="ed-btn ed-btn-sm" href="https://lobid.org/gnd/' + E.esc(gndNum) + '" target="_blank">GND: ' + E.esc(gndNum) + '</a> ';
        }
        if (!ent.wikidata_qid && !ent.gnd_id) {
            html += '<span class="ed-text-muted">Keine externen IDs vorhanden</span>';
        }
        html += '</div></div>';

        html += '</div>';
        return html;
    }

    function lookupDocTitle(docId) {
        if (!state.catalog || !state.catalog.documents) return 'Dokument ' + docId;
        var doc = state.catalog.documents.find(function (d) { return d.id === docId; });
        return doc ? (doc.title || 'Dokument ' + docId) : 'Dokument ' + docId;
    }

    function expandDetail(entityId) {
        if (state.expandedId === entityId) {
            state.expandedId = null;
        } else {
            state.expandedId = entityId;
        }
        renderResults();
    }

    // --- Events ---

    function bindEvents() {
        // Tab switching
        $$('.ed-register-tab').forEach(function (tab) {
            tab.addEventListener('click', function () {
                state.activeType = tab.dataset.type;
                state.expandedId = null;

                $$('.ed-register-tab').forEach(function (t) {
                    t.classList.toggle('active', t.dataset.type === state.activeType);
                    t.setAttribute('aria-selected', String(t.dataset.type === state.activeType));
                });

                renderTypeStats();
                applyFilters();
            });
        });

        // Search
        var searchEl = $('#register-search');
        if (searchEl) {
            searchEl.addEventListener('input', E.debounce(function () {
                state.searchQuery = searchEl.value;
                state.expandedId = null;
                applyFilters();
            }, 200));
        }

        // Sort
        var sortEl = $('#register-sort');
        if (sortEl) {
            sortEl.addEventListener('change', function () {
                var val = sortEl.value;
                if (val.charAt(0) === '-') {
                    state.sortKey = val.slice(1);
                    state.sortAsc = false;
                } else {
                    state.sortKey = val;
                    state.sortAsc = true;
                }
                applyFilters();
            });
        }

        // View toggle
        $$('.ed-view-btn').forEach(function (btn) {
            btn.addEventListener('click', function () {
                state.view = btn.dataset.view;
                $$('.ed-view-btn').forEach(function (b) {
                    b.classList.remove('active');
                    b.setAttribute('aria-pressed', 'false');
                });
                btn.classList.add('active');
                btn.setAttribute('aria-pressed', 'true');
                renderResults();
                syncUrlState();
            });
        });

        // Filter checkboxes
        $$('#filter-resolution input, #filter-occurrence input').forEach(function (cb) {
            cb.addEventListener('change', function () {
                state.expandedId = null;
                applyFilters();
            });
        });
    }

    function bindTableEvents() {
        $$('.ed-register-row').forEach(function (row) {
            row.addEventListener('click', function () {
                expandDetail(row.dataset.id);
            });
            row.style.cursor = 'pointer';
        });

        // Sortable headers
        $$('.ed-register-table th[data-sort]').forEach(function (th) {
            th.style.cursor = 'pointer';
            th.addEventListener('click', function () {
                var key = th.dataset.sort;
                if (state.sortKey === key) {
                    state.sortAsc = !state.sortAsc;
                } else {
                    state.sortKey = key;
                    state.sortAsc = key === 'name';
                }
                var sortEl = $('#register-sort');
                if (sortEl) sortEl.value = (state.sortAsc ? '' : '-') + key;
                applyFilters();
            });
        });
    }

    function bindCardEvents() {
        $$('.ed-register-card').forEach(function (card) {
            card.style.cursor = 'pointer';
            card.addEventListener('click', function () {
                expandDetail(card.dataset.id);
            });
        });
    }

    // --- Startup ---

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    ZBZ.Register = { init: init };
})();
