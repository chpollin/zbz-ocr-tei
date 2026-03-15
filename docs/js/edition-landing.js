/**
 * ZBZ Edition – Landing Page Module (Discovery Hub)
 * Search bar, screening overview, category tiles, recent docs.
 * Namespace: ZBZ.EditionLanding (ES6+, IIFE)
 */
(function () {
    'use strict';

    const E = ZBZ.Edition;
    let _fullTextIndex = null;
    let _searchData = null;

    function init() {
        Promise.all([E.loadCatalog(), E.loadSearchIndex()]).then((results) => {
            const catalog = results[0];
            _searchData = results[1];
            if (!catalog) return;

            renderMetrics(catalog);
            renderScreeningOverview(catalog);
            renderCategoryTiles(catalog);
            renderRecentDocs(catalog);
            initHeroSearch();

            ZBZ.log('Landing', `Discovery Hub | ${(catalog.documents || []).length} Docs | Search: ${_searchData ? _searchData.length + ' indexiert' : 'aus'}`);
        });
    }

    // --- Hero Metrics (animated) ---
    function renderMetrics(catalog) {
        const ed = catalog.edition || {};
        const targets = {
            'metric-docs': E.fmtNum(ed.total_docs || 286),
            'metric-pages': E.fmtNum(ed.total_pages || 4152),
            'metric-langs': `${ed.languages || 8}+`,
            'metric-period': ed.date_range || '1926-2000'
        };
        Object.keys(targets).forEach((id) => {
            const el = E.$('#' + id);
            if (!el) return;
            const target = targets[id];
            if (typeof target === 'string' && /^\d/.test(target)) {
                animateValue(el, target);
            } else {
                el.textContent = target;
            }
        });
    }

    function animateValue(el, target) {
        const raw = parseInt(target.replace(/\./g, ''), 10);
        if (isNaN(raw) || raw === 0) { el.textContent = target; return; }
        const duration = 800;
        const start = performance.now();
        function step(now) {
            let pct = Math.min((now - start) / duration, 1);
            pct = 1 - Math.pow(1 - pct, 3);
            const val = Math.round(raw * pct);
            el.textContent = E.fmtNum(val);
            if (pct < 1) requestAnimationFrame(step);
            else el.textContent = target;
        }
        requestAnimationFrame(step);
    }

    // --- Screening Overview ---
    function renderScreeningOverview(catalog) {
        const container = E.$('#screening-overview');
        if (!container) return;
        const counts = (catalog.corpus && catalog.corpus.screening) || {};

        const items = [
            { key: 'APPROVED', label: E.SCREENING_LABELS['APPROVED'], cls: 'approved' },
            { key: 'APPROVED_WITH_NOTES', label: E.SCREENING_LABELS['APPROVED_WITH_NOTES'], cls: 'notes' },
            { key: 'NEEDS_REVIEW', label: E.SCREENING_LABELS['NEEDS_REVIEW'], cls: 'review' },
            { key: 'NOT_SCREENED', label: E.SCREENING_LABELS['NOT_SCREENED'], cls: 'none' }
        ];

        let html = '';
        let total = 0;
        let done = 0;
        items.forEach((item) => {
            const n = counts[item.key] || 0;
            total += n;
            if (item.key === 'APPROVED' || item.key === 'APPROVED_WITH_NOTES') done += n;
            html += `<a href="catalog.html?screening=${item.key}" class="ed-screening-card ed-screening-card--${item.cls}">`;
            html += `<div class="ed-screening-card-num">${n}</div>`;
            html += `<div class="ed-screening-card-label">${E.esc(item.label)}</div>`;
            html += '</a>';
        });
        container.innerHTML = html;

        // LLM Screening progress
        const progress = E.$('#screening-progress');
        if (progress && total > 0) {
            const pct = Math.round((done / total) * 100);
            const bar = progress.querySelector('.ed-screening-progress-bar');
            if (bar) setTimeout(() => { bar.style.width = pct + '%'; }, 100);
            const pctLabel = E.$('#screening-pct');
            if (pctLabel) pctLabel.textContent = `${done} / ${total} (${pct}%)`;
        }

        // Editor curation progress (currently 0 — placeholder for future)
        const curProgress = E.$('#curation-progress');
        if (curProgress && total > 0) {
            const curBar = curProgress.querySelector('.ed-screening-progress-bar');
            // Count editor_approved from curation workflow (not yet in catalog data)
            const curCounts = (catalog.corpus && catalog.corpus.curation) || {};
            const editorDone = (curCounts['editor_approved'] || 0) + (curCounts['approved'] || 0);
            const curPct = Math.round((editorDone / total) * 100);
            if (curBar) setTimeout(() => { curBar.style.width = curPct + '%'; }, 100);
            const curPctLabel = E.$('#curation-pct');
            if (curPctLabel) curPctLabel.textContent = `${editorDone} / ${total} (${curPct}%)`;
        }
    }

    // --- Category Tiles ---
    function renderCategoryTiles(catalog) {
        const container = E.$('#category-tiles');
        if (!container) return;
        const corpus = catalog.corpus || {};

        let html = '';

        // Document types
        if (corpus.types) {
            html += '<div class="ed-category-section"><h3>Dokumenttypen</h3><div class="ed-category-grid">';
            Object.keys(corpus.types).forEach((key) => {
                const label = E.TYPE_LABELS[key] || key;
                html += `<a href="catalog.html?type=${E.esc(key)}" class="ed-category-tile">${E.esc(label)} <span class="ed-category-tile-count">${corpus.types[key]}</span></a>`;
            });
            html += '</div></div>';
        }

        // Languages (top 8)
        if (corpus.languages) {
            const sorted = Object.keys(corpus.languages).sort((a, b) => corpus.languages[b] - corpus.languages[a]);
            html += '<div class="ed-category-section"><h3>Sprachen</h3><div class="ed-category-grid">';
            sorted.slice(0, 8).forEach((key) => {
                const label = E.LANG_LABELS[key] || key;
                html += `<a href="catalog.html?lang=${E.esc(key)}" class="ed-category-tile">${E.esc(label)} <span class="ed-category-tile-count">${corpus.languages[key]}</span></a>`;
            });
            html += '</div></div>';
        }

        // Publication forms
        if (corpus.forms) {
            html += '<div class="ed-category-section"><h3>Publikationsformen</h3><div class="ed-category-grid">';
            Object.keys(corpus.forms).forEach((key) => {
                const label = E.PUB_FORM_LABELS[key] || key;
                html += `<a href="catalog.html?form=${E.esc(key)}" class="ed-category-tile">${E.esc(label)} <span class="ed-category-tile-count">${corpus.forms[key]}</span></a>`;
            });
            html += '</div></div>';
        }

        container.innerHTML = html;
    }

    // --- Recent Documents (sorted by screening_date) ---
    function renderRecentDocs(catalog) {
        const grid = E.$('#recent-docs-grid');
        if (!grid) return;

        const docs = (catalog.documents || []).slice();
        // Sort by screening_date desc, then by featured
        const withDate = docs.filter((d) => d.screening_date).sort((a, b) => {
            if (a.screening_date > b.screening_date) return -1;
            if (a.screening_date < b.screening_date) return 1;
            return 0;
        });

        // Take up to 6 recently screened, supplement with featured
        let selected = withDate.slice(0, 6);
        if (selected.length < 4) {
            const featured = catalog.featured || [];
            const selectedIds = {};
            selected.forEach((d) => { selectedIds[d.id] = true; });
            for (let i = 0; i < docs.length && selected.length < 6; i++) {
                if (featured.indexOf(docs[i].id) > -1 && !selectedIds[docs[i].id]) {
                    selected.push(docs[i]);
                    selectedIds[docs[i].id] = true;
                }
            }
        }

        let html = '';
        selected.forEach((doc) => {
            html += E.buildCardHtml(doc, { showPages: true });
        });
        grid.innerHTML = html;
    }

    // --- Hero Search ---
    function initHeroSearch() {
        if (_searchData && _searchData.length) {
            _fullTextIndex = E.createFullTextSearchIndex(_searchData);
        }

        const input = E.$('#hero-search');
        const btn = E.$('#hero-search-btn');
        const sugContainer = E.$('#search-suggestions');
        if (!input) return;

        function doSearch() {
            const q = input.value.trim();
            if (q) {
                window.location.href = 'catalog.html?q=' + encodeURIComponent(q);
            }
        }

        if (btn) btn.addEventListener('click', doSearch);
        input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') { e.preventDefault(); doSearch(); }
            if (e.key === 'Escape' && sugContainer) { sugContainer.innerHTML = ''; }
        });

        input.addEventListener('input', E.debounce(function () {
            const q = input.value.trim();
            if (!sugContainer) return;
            if (!q || q.length < 2 || !_fullTextIndex) {
                sugContainer.innerHTML = '';
                return;
            }

            const results = _fullTextIndex.search(q, { limit: 5 });
            if (!results.length) {
                sugContainer.innerHTML = '';
                return;
            }

            // Build lookup for text snippets
            const textMap = {};
            if (_searchData) {
                _searchData.forEach((d) => { textMap[d.id] = d.text || ''; });
            }

            let html = '<div class="ed-search-suggestions-list">';
            results.forEach((r) => {
                const snippet = E.extractSnippet(textMap[r.id] || '', q);
                html += `<a href="reader.html?doc=${E.esc(r.id)}" class="ed-search-suggestion">`;
                html += `<div class="ed-search-suggestion-title">${E.esc(r.title || 'Dok. ' + r.id)}</div>`;
                if (snippet) {
                    html += `<div class="ed-search-suggestion-snippet">${snippet}</div>`;
                }
                html += '</a>';
            });
            html += '</div>';
            sugContainer.innerHTML = html;
        }, 200));

        // Close suggestions on outside click
        document.addEventListener('click', (e) => {
            if (sugContainer && !sugContainer.contains(e.target) && e.target !== input) {
                sugContainer.innerHTML = '';
            }
        });
    }

    // --- Auto-init ---
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    ZBZ.EditionLanding = {};
})();
