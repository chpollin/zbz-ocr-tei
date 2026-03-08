/**
 * ZBZ OCR Pipeline -- Shared Utilities
 * Namespace: window.ZBZ
 */
(function () {
    'use strict';

    var _data = null;
    var _textCache = {};

    /**
     * Generic fetch with fallback candidates and caching.
     * @param {string} cacheKey  - unique key for _textCache
     * @param {string[]} candidates - URLs to try in order
     * @param {string} parseAs   - 'text' or 'json'
     * @returns {Promise<*>}
     */
    function _fetchWithFallbacks(cacheKey, candidates, parseAs) {
        if (_textCache[cacheKey] !== undefined) return Promise.resolve(_textCache[cacheKey]);

        return (async function () {
            for (var i = 0; i < candidates.length; i++) {
                try {
                    var r = await fetch(candidates[i]);
                    if (r.ok) {
                        var result = parseAs === 'json' ? await r.json() : await r.text();
                        _textCache[cacheKey] = result;
                        return result;
                    }
                } catch (e) { /* ignore */ }
            }
            _textCache[cacheKey] = null;
            return null;
        })();
    }

    var ZBZ = {
        // ---- Data Loading ----
        loadData: async function() {
            if (_data) return _data;
            var r = await fetch('data/dashboard.json');
            if (!r.ok) throw new Error('dashboard.json nicht gefunden');
            _data = await r.json();
            return _data;
        },

        // ---- Text Fetching (OCR pages) ----
        fetchPageText: function (source, docId, page) {
            var paths = {
                mistral: '../output/mistral_results/' + docId + '_p' + page + '.md',
                deepseek: '../output/ocr_results/' + docId + '_p' + page + '.md',
                llm_corrected: '../output/llm_corrected_c/' + docId + '_p' + page + '.md',
                gemini_corrected: '../output/gemini_corrected_a/' + docId + '_p' + page + '.md',
            };
            var path = paths[source];
            if (!path) return Promise.resolve(null);

            var candidates = [path];
            if (source === 'mistral') {
                candidates.push('data/examples/' + docId + '/' + docId + '_p' + page + '.md');
            }
            return _fetchWithFallbacks(source + '/' + docId + '/' + page, candidates, 'text');
        },

        // ---- Layout Data Fetching (Gemini first, Docling fallback) ----
        fetchLayoutData: function (docId, page) {
            var padded = String(page).padStart(3, '0');
            var base = docId + '_p' + padded;
            var candidates = [
                '../output/layout/' + docId + '/' + base + '_layout_gemini.json',
                'data/examples/' + docId + '/' + base + '_layout_gemini.json',
                '../output/layout/' + docId + '/' + base + '_layout.json',
                'data/examples/' + docId + '/' + base + '_layout.json',
            ];
            return _fetchWithFallbacks('layout/' + docId + '/' + page, candidates, 'json');
        },

        // ---- TEI Fetching ----
        fetchPageTei: function (docId, page) {
            var candidates = [
                '../output/tei/' + docId + '_p' + page + '.xml',
                '../output/tei_xml/' + docId + '_p' + page + '.xml',
                'data/examples/' + docId + '/' + docId + '_p' + page + '.xml',
            ];
            return _fetchWithFallbacks('tei/' + docId + '/' + page, candidates, 'text');
        },

        // ---- PAGE-XML Fetching ----
        fetchPageXml: function (docId, page) {
            var padded = String(page).padStart(3, '0');
            var candidates = [
                '../output/page_xml/' + docId + '/page/' + docId + '_p' + padded + '.xml',
            ];
            return _fetchWithFallbacks('page_xml/' + docId + '/' + page, candidates, 'text');
        },

        // ---- METS Fetching (document-level, cached per doc) ----
        fetchMetsXml: function (docId) {
            var candidates = [
                '../output/page_xml/' + docId + '/mets.xml',
            ];
            return _fetchWithFallbacks('mets/' + docId, candidates, 'text');
        },

        // ---- Reference TEI Fetching (per-page extraction from whole-document XML) ----
        fetchRefTeiPage: async function(docId, page) {
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

        // ---- XML Parsing ----
        parseXml: function (xml) {
            var cleaned = xml
                .replace(/\s+xmlns(:\w+)?\s*=\s*["'][^"']*["']/g, '')
                .replace(/\s+xsi:\w+\s*=\s*["'][^"']*["']/g, '');
            var doc = new DOMParser().parseFromString(cleaned, 'text/xml');
            if (doc.querySelector('parsererror')) return null;
            return doc;
        },

        // ---- XML Syntax Highlighting ----
        highlightXml: function (xml) {
            var s = xml
                .replace(/&/g, '&amp;')
                .replace(/</g, '&lt;')
                .replace(/>/g, '&gt;');
            s = s.replace(
                /(&lt;\?xml[^?]*\?&gt;)/g,
                '<span class="xml-decl">$1</span>'
            );
            s = s.replace(
                /(&lt;!--[\s\S]*?--&gt;)/g,
                '<span class="xml-comment">$1</span>'
            );
            s = s.replace(
                /(&lt;\/?)(\w[\w:-]*)([\s\S]*?)(\/?)(&gt;)/g,
                function (m, open, tagName, attrs, slash, close) {
                    var result = '<span class="xml-tag">' + open + tagName + '</span>';
                    if (attrs) {
                        result += attrs.replace(
                            /([\w:-]+)="([^"]*?)"/g,
                            '<span class="xml-attr-name">$1</span>=<span class="xml-attr-value">"$2"</span>'
                        );
                    }
                    result += '<span class="xml-tag">' + slash + close + '</span>';
                    return result;
                }
            );
            return s;
        },

        // ---- Layout Region Colors ----
        LAYOUT_COLORS: {
            zb_heading:   { stroke: '#dc2626', fill: 'rgba(220,38,38,0.12)',  label: 'Heading' },
            zb_paragraph: { stroke: '#6b7280', fill: 'rgba(107,114,128,0.08)', label: 'Absatz' },
            footnote:     { stroke: '#2563eb', fill: 'rgba(37,99,235,0.12)',  label: 'Fussnote' },
            caption:      { stroke: '#d97706', fill: 'rgba(217,119,6,0.12)',  label: 'Caption' },
            _filter:      { stroke: '#9ca3af', fill: 'rgba(156,163,175,0.06)', label: 'Filter' },
            _skip:        { stroke: '#a855f7', fill: 'rgba(168,85,247,0.08)', label: 'Skip' },
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

        padPage: function (page) {
            return String(page).padStart(3, '0');
        },

        imagePath: function (docId, page) {
            return 'images/' + docId + '/' + docId + '_p' + ZBZ.padPage(page) + '.png';
        },

        // ---- Publication Form Labels (shared) ----
        PUB_FORM_LABELS: {
            journalArticle: 'Artikel',
            book: 'Buch',
            bookSection: 'Buchkapitel',
            encyclopedia: 'Lexikon',
            brochure: 'Broschure',
            interview: 'Interview',
            anthology: 'Sammelband',
            other: 'Andere',
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
            { key: 'gemini_corrected', label: 'GEM', title: 'Gemini OCR-Korrektur' },
            { key: 'layout', label: 'LAY', title: 'Layout-Analyse (Docling)' },
            { key: 'tei', label: 'TEI', title: 'TEI-XML generiert' },
            { key: 'evaluation', label: 'EVAL', title: 'CER/WER Evaluation' },
            { key: 'page_xml', label: 'PAGE', title: 'PAGE-XML Export' },
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
            if (pipelineStatus.gemini_corrected) html += '<span class="tag amber">GEM</span>';
            return html || '<span class="tag">-</span>';
        },

        // ---- Entity Index (for resolving #zbz-* refs) ----
        _entityIndex: null,

        loadEntityIndex: function () {
            if (ZBZ._entityIndex) return Promise.resolve(ZBZ._entityIndex);
            return fetch('data/entity_index.json')
                .then(function (r) { return r.json(); })
                .then(function (data) { ZBZ._entityIndex = data; return data; })
                .catch(function () {
                    ZBZ._entityIndex = {};
                    return {};
                });
        },

        lookupEntity: function (ref) {
            if (!ZBZ._entityIndex || !ref) return null;
            var id = ref.charAt(0) === '#' ? ref.slice(1) : ref;
            return ZBZ._entityIndex[id] || null;
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
