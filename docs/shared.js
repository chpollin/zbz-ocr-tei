/**
 * ZBZ OCR Pipeline -- Shared Utilities
 * Namespace: window.ZBZ
 */
(function () {
    'use strict';

    var _data = null;
    var _textCache = {};

    var ZBZ = {
        // ---- Data Loading ----
        async loadData() {
            if (_data) return _data;
            var r = await fetch('data/dashboard.json');
            if (!r.ok) throw new Error('dashboard.json nicht gefunden');
            _data = await r.json();
            return _data;
        },

        getData() {
            return _data;
        },

        // ---- Text Fetching (OCR pages) ----
        async fetchPageText(source, docId, page) {
            var key = source + '/' + docId + '/' + page;
            if (_textCache[key] !== undefined) return _textCache[key];

            var paths = {
                mistral: '../output/mistral_results/' + docId + '_p' + page + '.md',
                deepseek: '../output/ocr_results/' + docId + '_p' + page + '.md',
                llm_corrected: '../output/llm_corrected_c/' + docId + '_p' + page + '.md',
            };

            var path = paths[source];
            if (!path) return null;

            var candidates = [path];
            if (source === 'mistral') {
                candidates.push('data/examples/' + docId + '/' + docId + '_p' + page + '.md');
            }

            for (var i = 0; i < candidates.length; i++) {
                try {
                    var r = await fetch(candidates[i]);
                    if (r.ok) {
                        var text = await r.text();
                        _textCache[key] = text;
                        return text;
                    }
                } catch (e) { /* ignore */ }
            }

            _textCache[key] = null;
            return null;
        },

        // ---- Layout Data Fetching ----
        // source: 'docling' (default) or 'gemini'
        async fetchLayoutData(docId, page, source) {
            source = source || 'docling';
            var key = 'layout/' + source + '/' + docId + '/' + page;
            if (_textCache[key] !== undefined) return _textCache[key];

            var padded = String(page).padStart(3, '0');
            var suffix = source === 'gemini' ? '_layout_gemini.json' : '_layout.json';
            var path = '../output/layout/' + docId + '/' + docId + '_p' + padded + suffix;
            var fallback = 'data/examples/' + docId + '/' + docId + '_p' + padded + suffix;

            var candidates = [path, fallback];
            for (var i = 0; i < candidates.length; i++) {
                try {
                    var r = await fetch(candidates[i]);
                    if (r.ok) {
                        var data = await r.json();
                        _textCache[key] = data;
                        return data;
                    }
                } catch (e) { /* ignore */ }
            }

            _textCache[key] = null;
            return null;
        },

        // ---- TEI Fetching ----
        async fetchPageTei(docId, page) {
            var key = 'tei/' + docId + '/' + page;
            if (_textCache[key] !== undefined) return _textCache[key];

            var paths = [
                '../output/tei/' + docId + '_p' + page + '.xml',
                '../output/tei_xml/' + docId + '_p' + page + '.xml',
                'data/examples/' + docId + '/' + docId + '_p' + page + '.xml',
            ];

            for (var i = 0; i < paths.length; i++) {
                try {
                    var r = await fetch(paths[i]);
                    if (r.ok) {
                        var text = await r.text();
                        _textCache[key] = text;
                        return text;
                    }
                } catch (e) { /* ignore */ }
            }

            _textCache[key] = null;
            return null;
        },

        // ---- Reference TEI Fetching (per-page extraction from whole-document XML) ----
        async fetchRefTeiPage(docId, page) {
            var key = 'ref-tei/' + docId + '/' + page;
            if (_textCache[key] !== undefined) return _textCache[key];

            // Cache the whole document under a separate key
            var docKey = 'ref-tei-doc/' + docId;
            var docXml = _textCache[docKey];

            if (docXml === undefined) {
                var refPaths = [
                    '../data/referenz-tei/Pilot/' + docId + '.xml',
                    '../data/referenz-tei/' + docId + '.xml',
                ];
                docXml = null;
                for (var j = 0; j < refPaths.length; j++) {
                    try {
                        var r = await fetch(refPaths[j]);
                        if (r.ok) {
                            docXml = await r.text();
                            break;
                        }
                    } catch (e) { /* ignore */ }
                }
                _textCache[docKey] = docXml;
            }

            if (!docXml) {
                _textCache[key] = null;
                return null;
            }

            // Parse and extract page content between <pb n="page"> and next <pb>
            try {
                var parser = new DOMParser();
                var doc = parser.parseFromString(docXml, 'text/xml');
                var pbs = doc.querySelectorAll('pb');
                var targetPb = null;
                var targetIdx = -1;

                for (var i = 0; i < pbs.length; i++) {
                    if (pbs[i].getAttribute('n') == page) {
                        targetPb = pbs[i];
                        targetIdx = i;
                        break;
                    }
                }

                if (!targetPb) {
                    _textCache[key] = null;
                    return null;
                }

                // Collect nodes between this pb and the next
                var nextPb = targetIdx + 1 < pbs.length ? pbs[targetIdx + 1] : null;
                var serializer = new XMLSerializer();
                var result = serializer.serializeToString(targetPb) + '\n';
                var node = targetPb.nextSibling;

                while (node && node !== nextPb) {
                    if (node.nodeType === 1 || (node.nodeType === 3 && node.textContent.trim())) {
                        result += serializer.serializeToString(node) + '\n';
                    }
                    node = node.nextSibling;
                }

                // Wrap in minimal TEI structure
                var pageXml = '<?xml version="1.0" encoding="UTF-8"?>\n' +
                    '<TEI xmlns="http://www.tei-c.org/ns/1.0">\n<text><body><div n="1">\n' +
                    result +
                    '</div></body></text>\n</TEI>';

                _textCache[key] = pageXml;
                return pageXml;
            } catch (e) {
                _textCache[key] = null;
                return null;
            }
        },

        // ---- Layout Region Colors ----
        LAYOUT_COLORS: {
            zb_heading:   { stroke: '#dc2626', fill: 'rgba(220,38,38,0.12)',  label: 'Heading' },
            zb_paragraph: { stroke: '#6b7280', fill: 'rgba(107,114,128,0.08)', label: 'Absatz' },
            footnote:     { stroke: '#2563eb', fill: 'rgba(37,99,235,0.12)',  label: 'Fussnote' },
            caption:      { stroke: '#d97706', fill: 'rgba(217,119,6,0.12)',  label: 'Caption' },
        },

        // ---- Formatting ----
        fmtNum: function (n) {
            if (n == null) return '-';
            return n.toLocaleString('de-DE');
        },

        fmtPct: function (n, decimals) {
            if (n == null) return '-';
            decimals = decimals != null ? decimals : 2;
            return (n * 100).toFixed(decimals) + '%';
        },

        fmtAccuracy: function (cer) {
            if (cer == null) return '-';
            return ((1 - cer) * 100).toFixed(2) + '%';
        },

        fmtCost: function (n) {
            if (n == null) return '-';
            return '$' + n.toFixed(2);
        },

        padPage: function (page) {
            return String(page).padStart(3, '0');
        },

        imagePath: function (docId, page) {
            return 'images/' + docId + '/' + docId + '_p' + ZBZ.padPage(page) + '.png';
        },

        // ---- CER Status ----
        cerBadge: function (cer) {
            if (cer == null) return '<span class="tag">n/a</span>';
            var pct = cer * 100;
            if (pct <= 3) return '<span class="badge-ok">' + pct.toFixed(1) + '%</span>';
            if (pct <= 7) return '<span class="badge-pending">' + pct.toFixed(1) + '%</span>';
            return '<span class="badge-error">' + pct.toFixed(1) + '%</span>';
        },

        // ---- DOM Helpers ----
        $: function (sel) { return document.querySelector(sel); },
        $$: function (sel) { return document.querySelectorAll(sel); },

        esc: function (s) {
            if (s == null) return '';
            var el = document.createElement('span');
            el.textContent = String(s);
            return el.innerHTML;
        },

        // ---- Pipeline Status Rendering ----
        PIPELINE_STEPS: [
            { key: 'images', label: 'IMG', title: 'Bilder extrahiert' },
            { key: 'ocr', label: 'OCR', title: 'OCR Engines', composite: ['ocr_mistral', 'ocr_deepseek'] },
            { key: 'llm_corrected', label: 'LLM', title: 'LLM-Korrektur' },
            { key: 'layout', label: 'LAY', title: 'Layout-Analyse (Docling)' },
            { key: 'tei', label: 'TEI', title: 'TEI-XML generiert' },
            { key: 'evaluation', label: 'EVAL', title: 'CER/WER Evaluation' },
            { key: 'export', label: 'EXP', title: 'PAGE-XML Export' },
        ],

        renderPipelineStatus: function (status, compact) {
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
        engineBadges: function (pipelineStatus) {
            var html = '';
            if (pipelineStatus.ocr_mistral) html += '<span class="tag teal">M</span>';
            if (pipelineStatus.ocr_deepseek) html += '<span class="tag violet">DS</span>';
            if (pipelineStatus.llm_corrected) html += '<span class="tag blue">LLM</span>';
            return html || '<span class="tag">-</span>';
        },

        // ---- URL State ----
        getParam: function (key) {
            return new URLSearchParams(window.location.search).get(key);
        },

        setParams: function (obj) {
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
