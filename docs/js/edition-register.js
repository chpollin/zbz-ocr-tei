/**
 * ZBZ Edition – Register Module
 * Per-type entity register with faceted filters, search, table/card views.
 * Type is determined by data-register-type attribute on <body>.
 * Namespace: ZBZ.EditionRegister (ES6+, IIFE)
 */
(function () {
    'use strict';

    const E = ZBZ.Edition;
    const $ = E.$;
    const $$ = E.$$;
    const _log = (msg) => console.log(`[ZBZ:Register] ${msg}`);

    // Read entity type from <body data-register-type="person|organization|place|work">
    const PAGE_TYPE = document.body.dataset.registerType;
    if (!PAGE_TYPE) {
        _log('Kein data-register-type auf <body> gefunden, Abbruch.');
        return;
    }

    const state = {
        data: null,
        entities: [],      // only entities of PAGE_TYPE
        filtered: [],
        catalog: null,
        view: 'table',
        sortKey: 'name',
        sortAsc: true,
        searchIndex: null,
        searchQuery: '',
        expandedId: null
    };

    const filters = {
        resolution: [],
        occurrence: []
    };

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

    // --- Init ---

    function init() {
        Promise.all([E.loadEntityRegister(), E.loadCatalog()])
            .then(([registerData, catalogData]) => {
                if (!registerData) {
                    $('#register-results').innerHTML = '<p>Register-Daten nicht verfuegbar.</p>';
                    return;
                }
                state.data = registerData;
                // Filter to only this page's type right away
                state.entities = registerData.entities.filter((e) => e.type === PAGE_TYPE);
                state.catalog = catalogData;
                _log(`${state.entities.length} ${TYPE_LABELS[PAGE_TYPE]} geladen (von ${registerData.entities.length} gesamt)`);

                readUrlState();
                initSearchIndex();
                renderTypeStats();
                renderFilters();
                bindEvents();
                applyFilters();
            });
    }

    // --- URL State ---

    function readUrlState() {
        const q = E.getParam('q');
        if (q) {
            state.searchQuery = q;
            const searchEl = $('#register-search');
            if (searchEl) searchEl.value = q;
        }
        const sort = E.getParam('sort');
        if (sort) {
            if (sort.charAt(0) === '-') {
                state.sortKey = sort.slice(1);
                state.sortAsc = false;
            } else {
                state.sortKey = sort;
                state.sortAsc = true;
            }
            const sortEl = $('#register-sort');
            if (sortEl) sortEl.value = sort;
        }
        const view = E.getParam('view');
        if (view === 'cards' || view === 'table') {
            state.view = view;
        }
    }

    function syncUrlState() {
        const params = {};
        if (state.searchQuery) params.q = state.searchQuery;
        const sortVal = (state.sortAsc ? '' : '-') + state.sortKey;
        if (sortVal !== 'name') params.sort = sortVal;
        if (state.view !== 'table') params.view = state.view;
        if (state.expandedId) params.id = state.expandedId;
        E.setParams(params);
    }

    // --- Search Index ---

    function initSearchIndex() {
        state.searchIndex = new MiniSearch({
            fields: ['name', 'variantStr', 'id'],
            storeFields: ['id'],
            searchOptions: {
                boost: { name: 3, variantStr: 1, id: 1 },
                fuzzy: 0.2,
                prefix: true
            }
        });
        const docs = state.entities.map((ent, i) => ({
            _msId: i,
            id: ent.id,
            name: ent.name,
            variantStr: (ent.variants || []).join(' ')
        }));
        state.searchIndex.addAll(docs);
        _log(`MiniSearch: ${docs.length} ${TYPE_LABELS[PAGE_TYPE]} indexiert`);
    }

    // --- Type Stats ---

    function renderTypeStats() {
        const summ = state.data && state.data.summary ? state.data.summary.by_type : null;
        const container = $('#register-type-stats');
        if (!container) return;

        if (summ && summ[PAGE_TYPE]) {
            const s = summ[PAGE_TYPE];
            container.innerHTML = `<span>${E.fmtNum(s.total)} ${TYPE_LABELS[PAGE_TYPE]}</span> · <span>${E.fmtNum(s.with_wikidata)} Wikidata</span> · <span>${E.fmtNum(s.with_gnd)} GND</span> · <span>${E.fmtNum(s.with_docs)} in Docs</span>`;
        } else {
            const total = state.entities.length;
            const wd = state.entities.filter((e) => e.wikidata_qid).length;
            const gnd = state.entities.filter((e) => e.gnd_id).length;
            container.innerHTML = `<span>${E.fmtNum(total)} Eintraege</span> · <span>${E.fmtNum(wd)} Wikidata</span> · <span>${E.fmtNum(gnd)} GND</span>`;
        }
    }

    // --- Filters ---

    function renderFilters() {
        const resCont = $('#filter-resolution');
        if (resCont) {
            resCont.innerHTML = [
                { val: 'wikidata', label: 'Mit Wikidata' },
                { val: 'gnd', label: 'Mit GND' },
                { val: 'none', label: 'Nicht aufgeloest' }
            ].map((f) =>
                `<label class="ed-filter-label"><input type="checkbox" name="resolution" value="${f.val}"> ${f.label}</label>`
            ).join('');
        }

        const occCont = $('#filter-occurrence');
        if (occCont) {
            occCont.innerHTML = [
                { val: 'with_docs', label: 'In Dokumenten' },
                { val: 'without_docs', label: 'Ohne Dokumente' }
            ].map((f) =>
                `<label class="ed-filter-label"><input type="checkbox" name="occurrence" value="${f.val}"> ${f.label}</label>`
            ).join('');
        }
    }

    function readFilters() {
        filters.resolution = Array.from($$('input[name="resolution"]:checked')).map((el) => el.value);
        filters.occurrence = Array.from($$('input[name="occurrence"]:checked')).map((el) => el.value);
    }

    // --- Apply Filters ---

    function applyFilters() {
        readFilters();
        let list = state.entities;

        // Search
        if (state.searchQuery.trim()) {
            const results = state.searchIndex.search(state.searchQuery.trim());
            const matchIds = new Set(results.map((r) => r.id));
            list = list.filter((e) => matchIds.has(e.id));
        }

        // Resolution filter
        if (filters.resolution.length > 0) {
            list = list.filter((e) => {
                if (filters.resolution.includes('wikidata') && e.wikidata_qid) return true;
                if (filters.resolution.includes('gnd') && e.gnd_id) return true;
                if (filters.resolution.includes('none') && !e.wikidata_qid && !e.gnd_id) return true;
                return false;
            });
        }

        // Occurrence filter
        if (filters.occurrence.length > 0 && filters.occurrence.length < 2) {
            if (filters.occurrence.includes('with_docs')) {
                list = list.filter((e) => e.doc_count > 0);
            } else {
                list = list.filter((e) => e.doc_count === 0);
            }
        }

        // Sort
        list = sortEntities(list);

        state.filtered = list;
        renderResults();
        syncUrlState();
    }

    function sortEntities(list) {
        const key = state.sortKey;
        const dir = state.sortAsc ? 1 : -1;
        return [...list].sort((a, b) => {
            let va = a[key];
            let vb = b[key];
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
        const container = $('#register-results');
        const countEl = $('#result-count');
        if (countEl) {
            countEl.textContent = `${E.fmtNum(state.filtered.length)} von ${E.fmtNum(state.entities.length)} ${TYPE_LABELS[PAGE_TYPE]}`;
        }

        if (state.view === 'table') {
            renderTable(container);
        } else {
            renderCards(container);
        }

        // Auto-expand from URL
        const expandId = E.getParam('id');
        if (expandId && !state.expandedId) {
            state.expandedId = expandId;
            expandDetail(expandId);
        }
    }

    // --- Table View ---

    function renderTable(container) {
        const sortIcon = (key) => {
            if (state.sortKey !== key) return '<span class="sort-icon" style="opacity:0.3">&#9650;</span>';
            return state.sortAsc ? '<span class="sort-icon">&#9650;</span>' : '<span class="sort-icon">&#9660;</span>';
        };

        let html = `<div class="ed-table-wrap"><table class="ed-table ed-register-table">
            <thead><tr>
                <th data-sort="name">Name ${sortIcon('name')}</th>
                <th data-sort="doc_count" style="width:60px;text-align:right">Dok. ${sortIcon('doc_count')}</th>
                <th data-sort="mention_count" style="width:60px;text-align:right">Erw. ${sortIcon('mention_count')}</th>
                <th style="width:80px">Links</th>
                <th style="width:80px">ID</th>
            </tr></thead><tbody>`;

        state.filtered.forEach((ent) => {
            const expanded = state.expandedId === ent.id;
            const links = buildLinkBadges(ent);
            const varCount = (ent.variants || []).length;

            html += `<tr class="ed-register-row${expanded ? ' expanded' : ''}" data-id="${E.esc(ent.id)}">
                <td><strong>${E.esc(ent.name)}</strong>${varCount > 0 ? ` <span class="ed-text-muted">(${varCount})</span>` : ''}${ent.contexts && ent.contexts.length > 0 ? '<div class="ed-register-context-preview">' + E.esc(ent.contexts[0].length > 100 ? ent.contexts[0].substring(0, 97) + '...' : ent.contexts[0]) + '</div>' : ''}</td>
                <td style="text-align:right">${ent.doc_count}</td>
                <td style="text-align:right">${ent.mention_count}</td>
                <td>${links}</td>
                <td><span class="ed-entity-item-zbzid">${E.esc(ent.id)}</span></td>
            </tr>`;

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

        let html = '<div class="ed-catalog-cards">';
        state.filtered.forEach((ent) => {
            const links = buildLinkBadges(ent);
            const varCount = (ent.variants || []).length;
            html += `<div class="ed-card ed-register-card ed-register-card-${ent.type}" data-id="${E.esc(ent.id)}">
                <div class="ed-card-body">
                    <div class="ed-card-title">${E.esc(ent.name)}</div>
                    <div class="ed-card-meta">
                        <span class="ed-entity-dot ed-entity-dot-${ent.type}"></span>
                        ${E.esc(TYPE_SINGULAR[ent.type] || ent.type)}
                        ${varCount > 0 ? ` &middot; ${varCount} Varianten` : ''}
                    </div>
                    <div class="ed-card-stats">
                        ${ent.doc_count > 0 ? `<span>${ent.doc_count} Dok.</span>` : ''}
                        ${ent.mention_count > 0 ? `<span>${ent.mention_count} Erw.</span>` : ''}
                    </div>
                    <div class="ed-card-links">${links} <span class="ed-entity-item-zbzid">${E.esc(ent.id)}</span></div>
                </div>
            </div>`;
        });
        html += '</div>';

        // Detail expansion (if any)
        if (state.expandedId) {
            const ent = state.entities.find((e) => e.id === state.expandedId);
            if (ent) {
                html += `<div class="ed-register-detail" id="register-detail">${buildDetailContent(ent)}</div>`;
            }
        }

        container.innerHTML = html;
        bindCardEvents();
    }

    // --- Link Badges ---

    function buildLinkBadges(ent) {
        let html = '';
        if (ent.wikidata_qid) {
            html += `<a class="ed-entity-item-link" href="${E.esc(ent.wikidata_url)}" target="_blank" title="Wikidata ${ent.wikidata_qid}" onclick="event.stopPropagation()">WD</a> `;
        }
        if (ent.gnd_id) {
            const gndNum = ent.gnd_id.replace('GND:', '');
            html += `<a class="ed-entity-item-link" href="https://lobid.org/gnd/${E.esc(gndNum)}" target="_blank" title="GND ${gndNum}" onclick="event.stopPropagation()">GND</a>`;
        }
        if (!ent.wikidata_qid && !ent.gnd_id) {
            html += '<span class="ed-text-muted" style="font-size:0.75rem">–</span>';
        }
        return html;
    }

    // --- Detail Expansion ---

    function buildDetailRow(ent, colspan) {
        return `<tr class="ed-register-detail-row" data-detail-id="${E.esc(ent.id)}"><td colspan="${colspan}"><div class="ed-register-detail">${buildDetailContent(ent)}</div></td></tr>`;
    }

    function buildDetailContent(ent) {
        let html = '<div class="ed-register-detail-grid">';

        // Variants
        const variants = (ent.variants || []).filter((v) => v && v !== ent.name);
        if (variants.length > 0) {
            const shown = variants.slice(0, 10);
            html += '<div class="ed-register-detail-section"><h4>Namensvarianten</h4><div class="ed-register-variants">';
            shown.forEach((v) => { html += `<span class="ed-badge">${E.esc(v)}</span> `; });
            if (variants.length > 10) {
                html += `<span class="ed-text-muted">und ${variants.length - 10} weitere</span>`;
            }
            html += '</div></div>';
        }

        // Documents
        if (ent.doc_ids && ent.doc_ids.length > 0) {
            html += '<div class="ed-register-detail-section"><h4>Vorkommnisse in Dokumenten</h4><div class="ed-register-doc-links">';
            const docs = ent.doc_ids.slice(0, 20);
            docs.forEach((docId) => {
                const title = lookupDocTitle(docId);
                const shortTitle = title.length > 40 ? title.substring(0, 37) + '...' : title;
                html += `<a class="ed-register-doc-link" href="reader.html?doc=${E.esc(docId)}" title="${E.esc(title)}">${E.esc(docId)} – ${E.esc(shortTitle)}</a> `;
            });
            if (ent.doc_ids.length > 20) {
                html += `<span class="ed-text-muted">und ${ent.doc_ids.length - 20} weitere</span>`;
            }
            html += '</div></div>';
        }

        // Contexts
        if (ent.contexts && ent.contexts.length > 0) {
            html += '<div class="ed-register-detail-section"><h4>Kontextbeispiele</h4>';
            ent.contexts.forEach((ctx) => {
                const truncated = ctx.length > 200 ? ctx.slice(0, 200) + '...' : ctx;
                html += `<blockquote class="ed-register-context">${E.esc(truncated)}</blockquote>`;
            });
            html += '</div>';
        }

        // External links
        html += '<div class="ed-register-detail-section"><h4>Externe Verknuepfungen</h4><div class="ed-register-ext-links">';
        if (ent.wikidata_qid) {
            html += `<a class="ed-btn ed-btn-sm" href="${E.esc(ent.wikidata_url)}" target="_blank">Wikidata: ${E.esc(ent.wikidata_qid)}</a> `;
        }
        if (ent.gnd_id) {
            const gndNum = ent.gnd_id.replace('GND:', '');
            html += `<a class="ed-btn ed-btn-sm" href="https://lobid.org/gnd/${E.esc(gndNum)}" target="_blank">GND: ${E.esc(gndNum)}</a> `;
        }
        if (!ent.wikidata_qid && !ent.gnd_id) {
            html += '<span class="ed-text-muted">Keine externen IDs vorhanden</span>';
        }
        html += '</div></div>';

        html += '</div>';
        return html;
    }

    function lookupDocTitle(docId) {
        if (!state.catalog || !state.catalog.documents) return `Dokument ${docId}`;
        const doc = state.catalog.documents.find((d) => d.id === docId);
        return doc ? (doc.title || `Dokument ${docId}`) : `Dokument ${docId}`;
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
        // Search
        const searchEl = $('#register-search');
        if (searchEl) {
            searchEl.addEventListener('input', E.debounce(() => {
                state.searchQuery = searchEl.value;
                state.expandedId = null;
                applyFilters();
            }, 200));
        }

        // Sort
        const sortEl = $('#register-sort');
        if (sortEl) {
            sortEl.addEventListener('change', () => {
                const val = sortEl.value;
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
        $$('.ed-view-btn').forEach((btn) => {
            btn.addEventListener('click', () => {
                state.view = btn.dataset.view;
                $$('.ed-view-btn').forEach((b) => b.classList.remove('active'));
                btn.classList.add('active');
                renderResults();
                syncUrlState();
            });
        });

        // Filter checkboxes
        $$('#filter-resolution input, #filter-occurrence input').forEach((cb) => {
            cb.addEventListener('change', () => {
                state.expandedId = null;
                applyFilters();
            });
        });
    }

    function bindTableEvents() {
        $$('.ed-register-row').forEach((row) => {
            row.addEventListener('click', () => {
                expandDetail(row.dataset.id);
            });
            row.style.cursor = 'pointer';
        });

        // Sortable headers
        $$('.ed-register-table th[data-sort]').forEach((th) => {
            th.style.cursor = 'pointer';
            th.addEventListener('click', () => {
                const key = th.dataset.sort;
                if (state.sortKey === key) {
                    state.sortAsc = !state.sortAsc;
                } else {
                    state.sortKey = key;
                    state.sortAsc = key === 'name';
                }
                const sortEl = $('#register-sort');
                if (sortEl) sortEl.value = (state.sortAsc ? '' : '-') + key;
                applyFilters();
            });
        });
    }

    function bindCardEvents() {
        $$('.ed-register-card').forEach((card) => {
            card.style.cursor = 'pointer';
            card.addEventListener('click', () => {
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

    ZBZ.EditionRegister = { init: init };
})();
