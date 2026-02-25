/**
 * ZBZ OCR Pipeline – Shared Utilities
 * Namespace: window.ZBZ
 */
(function () {
    'use strict';

    let _data = null;
    const _textCache = {};

    const ZBZ = {
        // ---- Data Loading ----
        async loadData() {
            if (_data) return _data;
            const r = await fetch('data/dashboard.json');
            if (!r.ok) throw new Error('dashboard.json nicht gefunden');
            _data = await r.json();
            return _data;
        },

        getData() {
            return _data;
        },

        // ---- Text Fetching (OCR pages) ----
        async fetchPageText(source, docId, page) {
            const key = `${source}/${docId}/${page}`;
            if (_textCache[key] !== undefined) return _textCache[key];

            const paths = {
                mistral: `../output/mistral_results/${docId}_p${page}.md`,
                deepseek: `../output/ocr_results/${docId}_p${page}.md`,
                llm_corrected: `../output/llm_corrected_c/${docId}_p${page}.md`,
            };

            const path = paths[source];
            if (!path) return null;

            try {
                const r = await fetch(path);
                if (r.ok) {
                    const text = await r.text();
                    _textCache[key] = text;
                    return text;
                }
            } catch (e) { /* ignore */ }

            _textCache[key] = null;
            return null;
        },

        // ---- Formatting ----
        fmtNum(n) {
            if (n == null) return '-';
            return n.toLocaleString('de-DE');
        },

        fmtPct(n, decimals) {
            if (n == null) return '-';
            decimals = decimals != null ? decimals : 2;
            return (n * 100).toFixed(decimals) + '%';
        },

        fmtAccuracy(cer) {
            if (cer == null) return '-';
            return ((1 - cer) * 100).toFixed(2) + '%';
        },

        fmtCost(n) {
            if (n == null) return '-';
            return '$' + n.toFixed(2);
        },

        padPage(page) {
            return String(page).padStart(3, '0');
        },

        imagePath(docId, page) {
            return 'images/' + docId + '/' + docId + '_p' + ZBZ.padPage(page) + '.png';
        },

        // ---- CER Status ----
        cerBadge(cer) {
            if (cer == null) return '<span class="tag">n/a</span>';
            var pct = cer * 100;
            if (pct <= 3) return '<span class="badge-ok">' + pct.toFixed(1) + '%</span>';
            if (pct <= 7) return '<span class="badge-pending">' + pct.toFixed(1) + '%</span>';
            return '<span class="badge-error">' + pct.toFixed(1) + '%</span>';
        },

        // ---- DOM Helpers ----
        $(sel) { return document.querySelector(sel); },
        $$(sel) { return document.querySelectorAll(sel); },

        el(tag, attrs, children) {
            const e = document.createElement(tag);
            if (attrs) {
                Object.keys(attrs).forEach(function (k) {
                    if (k === 'text') e.textContent = attrs[k];
                    else if (k === 'html') e.innerHTML = attrs[k];
                    else if (k === 'on') {
                        Object.keys(attrs[k]).forEach(function (ev) {
                            e.addEventListener(ev, attrs[k][ev]);
                        });
                    } else e.setAttribute(k, attrs[k]);
                });
            }
            if (children) {
                children.forEach(function (c) {
                    if (typeof c === 'string') e.appendChild(document.createTextNode(c));
                    else if (c) e.appendChild(c);
                });
            }
            return e;
        },

        // ---- Pipeline Status Rendering ----
        PIPELINE_STEPS: [
            { key: 'images', label: 'IMG', title: 'Bilder extrahiert' },
            { key: 'ocr', label: 'OCR', title: 'OCR Engines', composite: ['ocr_mistral', 'ocr_deepseek'] },
            { key: 'llm_corrected', label: 'LLM', title: 'LLM-Korrektur' },
            { key: 'evaluation', label: 'EVAL', title: 'CER/WER Evaluation' },
            { key: 'export', label: 'EXP', title: 'PAGE-XML Export' },
        ],

        renderPipelineStatus(status, compact) {
            var steps = ZBZ.PIPELINE_STEPS;
            var cls = compact ? 'pipeline-steps compact' : 'pipeline-steps';
            var html = '<div class="' + cls + '">';
            steps.forEach(function (s) {
                if (s.composite) {
                    var anyDone = s.composite.some(function (k) { return status[k]; });
                    var done = anyDone ? ' done' : '';
                    var dots = '';
                    if (!compact) {
                        if (status.ocr_mistral) dots += '<span class="engine-dot teal" title="Mistral"></span>';
                        if (status.ocr_deepseek) dots += '<span class="engine-dot violet" title="DeepSeek"></span>';
                    }
                    html += '<div class="pipeline-step' + done + '" title="' + s.title + '">' + s.label + dots + '</div>';
                } else {
                    var done = status[s.key] ? ' done' : '';
                    html += '<div class="pipeline-step' + done + '" title="' + s.title + '">' + s.label + '</div>';
                }
            });
            html += '</div>';
            return html;
        },

        // ---- Engine Badges ----
        engineBadges(pipelineStatus) {
            var html = '';
            if (pipelineStatus.ocr_mistral) html += '<span class="tag teal">M</span>';
            if (pipelineStatus.ocr_deepseek) html += '<span class="tag violet">DS</span>';
            if (pipelineStatus.llm_corrected) html += '<span class="tag blue">LLM</span>';
            return html || '<span class="tag">-</span>';
        },

        // ---- Collapsible Cards ----
        initCollapsibles() {
            document.addEventListener('click', function (e) {
                var header = e.target.closest('.card-header');
                if (header) header.closest('.card').classList.toggle('open');
            });
        },

        // ---- Overlay / Zoom ----
        initOverlay() {
            var overlay = document.getElementById('overlay');
            if (!overlay) return;
            overlay.addEventListener('click', function () {
                overlay.classList.remove('active');
            });
            document.addEventListener('keydown', function (e) {
                if (e.key === 'Escape') overlay.classList.remove('active');
            });
        },

        zoom(src) {
            var img = document.getElementById('overlay-img');
            if (!img) return;
            img.src = src;
            document.getElementById('overlay').classList.add('active');
        },

        // ---- URL State ----
        getParam(key) {
            return new URLSearchParams(window.location.search).get(key);
        },

        setParams(obj) {
            var params = new URLSearchParams(window.location.search);
            Object.keys(obj).forEach(function (k) {
                if (obj[k] == null) params.delete(k);
                else params.set(k, obj[k]);
            });
            history.replaceState(null, '', '?' + params.toString());
        },
    };

    window.ZBZ = ZBZ;
})();
