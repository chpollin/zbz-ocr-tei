/**
 * ZBZ Edition – Landing Page Module
 * Loads catalog data and renders featured docs + corpus stats.
 * Namespace: ZBZ.EditionLanding (ES5, IIFE)
 */
(function () {
    'use strict';

    var E = ZBZ.Edition;

    function init() {
        E.loadCatalog().then(function (catalog) {
            if (!catalog) return;
            renderMetrics(catalog);
            renderFeatured(catalog);
            renderCorpusStats(catalog);
        });
    }

    // --- Hero Metrics ---
    function renderMetrics(catalog) {
        var ed = catalog.edition || {};
        var targets = {
            'metric-docs': E.fmtNum(ed.total_docs || 286),
            'metric-pages': E.fmtNum(ed.total_pages || 4152),
            'metric-langs': (ed.languages || 8) + '+',
            'metric-period': ed.date_range || '1926-2000'
        };

        Object.keys(targets).forEach(function (id) {
            var el = E.$('#' + id);
            if (!el) return;
            var target = targets[id];
            // Animate numbers
            if (typeof target === 'string' && /^\d/.test(target)) {
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
            // ease-out
            pct = 1 - Math.pow(1 - pct, 3);
            var val = Math.round(raw * pct);
            el.textContent = E.fmtNum(val);
            if (pct < 1) requestAnimationFrame(step);
            else el.textContent = target;
        }
        requestAnimationFrame(step);
    }

    // --- Featured Documents ---
    function renderFeatured(catalog) {
        var grid = E.$('#featured-grid');
        if (!grid) return;

        var featured = catalog.featured || [];
        var docs = catalog.documents || [];
        var html = '';

        featured.forEach(function (docId) {
            var doc = null;
            for (var i = 0; i < docs.length; i++) {
                if (docs[i].id === docId) { doc = docs[i]; break; }
            }
            if (!doc) return;
            html += E.buildCardHtml(doc, { showPages: true });
        });

        grid.innerHTML = html;
    }

    // --- Corpus Statistics ---
    function renderCorpusStats(catalog) {
        var corpus = catalog.corpus || {};

        // Language bars
        var langContainer = E.$('#stats-languages');
        if (langContainer && corpus.languages) {
            var langs = corpus.languages;
            var total = 0;
            Object.keys(langs).forEach(function (k) { total += langs[k]; });

            var sorted = Object.keys(langs).sort(function (a, b) { return langs[b] - langs[a]; });
            var html = '';
            sorted.forEach(function (key) {
                var pct = Math.round((langs[key] / total) * 100);
                var label = E.LANG_LABELS[key] || key;
                html += '<div class="ed-bar-row">';
                html += '<span class="ed-bar-label">' + E.esc(label) + '</span>';
                html += '<div class="ed-bar-track"><div class="ed-bar-fill" style="width:' + pct + '%"></div></div>';
                html += '<span class="ed-bar-value">' + langs[key] + '</span>';
                html += '</div>';
            });
            langContainer.innerHTML = html;
        }

        // Type pills
        var typeContainer = E.$('#stats-types');
        if (typeContainer && corpus.types) {
            var types = corpus.types;
            var html2 = '';
            Object.keys(types).forEach(function (key) {
                var label = E.TYPE_LABELS[key] || key;
                html2 += '<span class="ed-pill">' + E.esc(label) + ': ' + types[key] + '</span>';
            });
            typeContainer.innerHTML = html2;
        }

        // Form list
        var formContainer = E.$('#stats-forms');
        if (formContainer && corpus.forms) {
            var forms = corpus.forms;
            var html3 = '';
            Object.keys(forms).forEach(function (key) {
                var label = E.PUB_FORM_LABELS[key] || key;
                html3 += '<span class="ed-pill">' + E.esc(label) + ': ' + forms[key] + '</span>';
            });
            formContainer.innerHTML = html3;
        }
    }

    // --- Auto-init ---
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    ZBZ.EditionLanding = {};
})();
