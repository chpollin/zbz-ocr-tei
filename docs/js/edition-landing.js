/**
 * ZBZ Edition – Landing Page Module (Rewrite)
 * Discovery Hub: metrics, corpus overview, screening, hero search.
 * Namespace: ZBZ.EditionLanding (ES6+, IIFE)
 */
(function () {
    'use strict';

    var E = ZBZ.Edition;
    var _fullTextIndex = null;
    var _searchData = null;

    function init() {
        Promise.all([E.loadCatalog(), E.loadSearchIndex()]).then(function (results) {
            var catalog = results[0];
            _searchData = results[1];
            if (!catalog) return;

            renderMetrics(catalog);
            renderScreeningCompact(catalog);
            renderCategoryChips(catalog);
            initHeroSearch();

            ZBZ.log('Landing', 'Discovery Hub | ' + ((catalog.documents || []).length) + ' Docs');
        });
    }

    // --- Hero Metrics ---
    function renderMetrics(catalog) {
        var ed = catalog.edition || {};
        var docs = catalog.documents || [];

        // Sum entity_count across all documents
        var totalEntities = 0;
        for (var i = 0; i < docs.length; i++) {
            totalEntities += (docs[i].entity_count || 0);
        }

        // Count distinct types
        var types = catalog.corpus && catalog.corpus.types ? Object.keys(catalog.corpus.types).length : 4;

        var targets = {
            'metric-docs': E.fmtNum(ed.total_docs || docs.length),
            'metric-pages': E.fmtNum(ed.total_pages || 4117),
            'metric-entities': E.fmtNum(totalEntities),
            'metric-types': String(types)
        };
        Object.keys(targets).forEach(function (id) {
            var el = E.$('#' + id);
            if (!el) return;
            var target = targets[id];
            if (/^\d/.test(target)) {
                animateValue(el, target);
            } else {
                el.textContent = target;
            }
        });
    }

    function animateValue(el, target) {
        var raw = parseInt(target.replace(/\./g, ''), 10);
        if (isNaN(raw) || raw === 0) { el.textContent = target; return; }
        var duration = 800;
        var start = performance.now();
        function step(now) {
            var pct = Math.min((now - start) / duration, 1);
            pct = 1 - Math.pow(1 - pct, 3); // ease-out cubic
            el.textContent = E.fmtNum(Math.round(raw * pct));
            if (pct < 1) requestAnimationFrame(step);
            else el.textContent = target;
        }
        requestAnimationFrame(step);
    }

    // --- Screening Compact ---
    function renderScreeningCompact(catalog) {
        var container = E.$('#screening-overview');
        if (!container) return;
        var counts = (catalog.corpus && catalog.corpus.screening) || {};

        var items = [
            { key: 'APPROVED', label: 'Genehmigt', cls: 'approved' },
            { key: 'APPROVED_WITH_NOTES', label: 'Mit Anm.', cls: 'notes' },
            { key: 'NEEDS_REVIEW', label: 'Pruefung', cls: 'review' },
            { key: 'NOT_SCREENED', label: 'Offen', cls: 'none' }
        ];

        var html = '';
        var total = 0;
        var done = 0;
        items.forEach(function (item) {
            var n = counts[item.key] || 0;
            total += n;
            if (item.key === 'APPROVED' || item.key === 'APPROVED_WITH_NOTES') done += n;
            html += '<a href="catalog.html?screening=' + item.key + '" class="ed-screening-chip ed-screening-chip--' + item.cls + '">';
            html += '<span class="ed-screening-chip-num">' + n + '</span> ';
            html += '<span class="ed-screening-chip-label">' + E.esc(item.label) + '</span>';
            html += '</a>';
        });
        container.innerHTML = html;

        // LLM Screening progress
        var progress = E.$('#screening-progress');
        if (progress && total > 0) {
            var pct = Math.round((done / total) * 100);
            var bar = progress.querySelector('.ed-screening-progress-bar');
            if (bar) setTimeout(function () { bar.style.width = pct + '%'; }, 100);
            var pctLabel = E.$('#screening-pct');
            if (pctLabel) pctLabel.textContent = done + '/' + total + ' (' + pct + '%)';
        }

        // Editor curation progress
        var curProgress = E.$('#curation-progress');
        if (curProgress && total > 0) {
            var curBar = curProgress.querySelector('.ed-screening-progress-bar');
            var curCounts = (catalog.corpus && catalog.corpus.curation) || {};
            var editorDone = (curCounts['editor_approved'] || 0) + (curCounts['approved'] || 0);
            var curPct = Math.round((editorDone / total) * 100);
            if (curBar) setTimeout(function () { curBar.style.width = curPct + '%'; }, 100);
            var curPctLabel = E.$('#curation-pct');
            if (curPctLabel) curPctLabel.textContent = editorDone + '/' + total + ' (' + curPct + '%)';
        }
    }

    // --- Category Chips ---
    function renderCategoryChips(catalog) {
        var container = E.$('#category-tiles');
        if (!container) return;
        var corpus = catalog.corpus || {};
        var html = '';

        if (corpus.types) {
            html += '<div class="ed-chip-group"><span class="ed-chip-group-label">Dokumenttyp</span>';
            Object.keys(corpus.types).forEach(function (key) {
                html += '<a href="catalog.html?type=' + E.esc(key) + '" class="ed-chip">' +
                    E.esc(E.TYPE_LABELS[key] || key) +
                    ' <span class="ed-chip-count">' + corpus.types[key] + '</span></a>';
            });
            html += '</div>';
        }

        if (corpus.languages) {
            var sorted = Object.keys(corpus.languages).sort(function (a, b) { return corpus.languages[b] - corpus.languages[a]; });
            html += '<div class="ed-chip-group"><span class="ed-chip-group-label">Sprache</span>';
            sorted.slice(0, 8).forEach(function (key) {
                html += '<a href="catalog.html?lang=' + E.esc(key) + '" class="ed-chip">' +
                    E.esc(E.LANG_LABELS[key] || key) +
                    ' <span class="ed-chip-count">' + corpus.languages[key] + '</span></a>';
            });
            html += '</div>';
        }

        if (corpus.forms) {
            html += '<div class="ed-chip-group"><span class="ed-chip-group-label">Form</span>';
            Object.keys(corpus.forms).forEach(function (key) {
                html += '<a href="catalog.html?form=' + E.esc(key) + '" class="ed-chip">' +
                    E.esc(E.PUB_FORM_LABELS[key] || key) +
                    ' <span class="ed-chip-count">' + corpus.forms[key] + '</span></a>';
            });
            html += '</div>';
        }

        container.innerHTML = html;
    }

    // --- Hero Search ---
    function initHeroSearch() {
        if (_searchData && _searchData.length) {
            _fullTextIndex = E.createFullTextSearchIndex(_searchData);
        }

        var input = E.$('#hero-search');
        var btn = E.$('#hero-search-btn');
        var sugContainer = E.$('#search-suggestions');
        if (!input) return;

        function doSearch() {
            var q = input.value.trim();
            if (q) window.location.href = 'catalog.html?q=' + encodeURIComponent(q);
        }

        if (btn) btn.addEventListener('click', doSearch);
        input.addEventListener('keydown', function (e) {
            if (e.key === 'Enter') { e.preventDefault(); doSearch(); }
            if (e.key === 'Escape' && sugContainer) sugContainer.innerHTML = '';
        });

        input.addEventListener('input', E.debounce(function () {
            var q = input.value.trim();
            if (!sugContainer) return;
            if (!q || q.length < 2 || !_fullTextIndex) { sugContainer.innerHTML = ''; input.setAttribute('aria-expanded', 'false'); return; }

            var results = _fullTextIndex.search(q, { limit: 5 });
            if (!results.length) { sugContainer.innerHTML = ''; input.setAttribute('aria-expanded', 'false'); return; }

            var textMap = {};
            if (_searchData) _searchData.forEach(function (d) { textMap[d.id] = d.text || ''; });

            var html = '<div class="ed-search-suggestions-list">';
            results.forEach(function (r) {
                var snippet = E.extractSnippet(textMap[r.id] || '', q);
                html += '<a href="reader.html?doc=' + E.esc(r.id) + '" class="ed-search-suggestion">';
                html += '<div class="ed-search-suggestion-title">' + E.esc(r.title || 'Dok. ' + r.id) + '</div>';
                if (snippet) html += '<div class="ed-search-suggestion-snippet">' + snippet + '</div>';
                html += '</a>';
            });
            html += '</div>';
            sugContainer.innerHTML = html;
            input.setAttribute('aria-expanded', 'true');
        }, 200));

        document.addEventListener('click', function (e) {
            if (sugContainer && !sugContainer.contains(e.target) && e.target !== input) {
                sugContainer.innerHTML = '';
                input.setAttribute('aria-expanded', 'false');
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
