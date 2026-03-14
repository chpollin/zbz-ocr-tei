/**
 * ZBZ Edition – Landing Page Module
 * Loads catalog data and renders featured docs + corpus stats.
 * Namespace: ZBZ.EditionLanding (ES6+, IIFE)
 */
(function () {
    'use strict';

    const E = ZBZ.Edition;

    function init() {
        E.loadCatalog().then((catalog) => {
            if (!catalog) return;
            renderMetrics(catalog);
            renderFeatured(catalog);
            renderCorpusStats(catalog);
            const ed = catalog.edition || {};
            ZBZ.log('Landing', `${ed.total_docs || '?'} Docs | ${ed.total_pages || '?'} Seiten | ${(catalog.featured || []).length} Featured`);
        });
    }

    // --- Hero Metrics ---
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
            // Animate numbers
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
            // ease-out
            pct = 1 - Math.pow(1 - pct, 3);
            const val = Math.round(raw * pct);
            el.textContent = E.fmtNum(val);
            if (pct < 1) requestAnimationFrame(step);
            else el.textContent = target;
        }
        requestAnimationFrame(step);
    }

    // --- Featured Documents ---
    function renderFeatured(catalog) {
        const grid = E.$('#featured-grid');
        if (!grid) return;

        const featured = catalog.featured || [];
        const docs = catalog.documents || [];
        let html = '';

        featured.forEach((docId) => {
            let doc = null;
            for (let i = 0; i < docs.length; i++) {
                if (docs[i].id === docId) { doc = docs[i]; break; }
            }
            if (!doc) return;
            html += E.buildCardHtml(doc, { showPages: true });
        });

        grid.innerHTML = html;
    }

    // --- Corpus Statistics ---
    function renderCorpusStats(catalog) {
        const corpus = catalog.corpus || {};

        // Language bars
        const langContainer = E.$('#stats-languages');
        if (langContainer && corpus.languages) {
            const langs = corpus.languages;
            let total = 0;
            Object.keys(langs).forEach((k) => { total += langs[k]; });

            const sorted = Object.keys(langs).sort((a, b) => langs[b] - langs[a]);
            let html = '';
            sorted.forEach((key) => {
                const pct = Math.round((langs[key] / total) * 100);
                const label = E.LANG_LABELS[key] || key;
                html += '<div class="ed-bar-row">';
                html += `<span class="ed-bar-label">${E.esc(label)}</span>`;
                html += `<div class="ed-bar-track"><div class="ed-bar-fill" style="width:${pct}%"></div></div>`;
                html += `<span class="ed-bar-value">${langs[key]}</span>`;
                html += '</div>';
            });
            langContainer.innerHTML = html;
        }

        // Type pills
        const typeContainer = E.$('#stats-types');
        if (typeContainer && corpus.types) {
            const types = corpus.types;
            let html2 = '';
            Object.keys(types).forEach((key) => {
                const label = E.TYPE_LABELS[key] || key;
                html2 += `<span class="ed-pill">${E.esc(label)}: ${types[key]}</span>`;
            });
            typeContainer.innerHTML = html2;
        }

        // Form list
        const formContainer = E.$('#stats-forms');
        if (formContainer && corpus.forms) {
            const forms = corpus.forms;
            let html3 = '';
            Object.keys(forms).forEach((key) => {
                const label = E.PUB_FORM_LABELS[key] || key;
                html3 += `<span class="ed-pill">${E.esc(label)}: ${forms[key]}</span>`;
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
