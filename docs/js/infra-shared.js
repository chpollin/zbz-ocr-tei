/**
 * ZBZ OCR Pipeline -- Shared Utilities
 * Namespace: window.ZBZ
 */
(function () {
    'use strict';

    // Auto-detect base path when loaded from infrastruktur/ subdirectory
    const _basePath = window.location.pathname.indexOf('/infrastruktur/') > -1 ? '../' : '';

    let _data = null;
    const _textCache = {};

    /**
     * Generic fetch with fallback candidates and caching.
     * @param {string} cacheKey  - unique key for _textCache
     * @param {string[]} candidates - URLs to try in order
     * @param {string} parseAs   - 'text' or 'json'
     * @returns {Promise<*>}
     */
    function _fetchWithFallbacks(cacheKey, candidates, parseAs) {
        if (_textCache[cacheKey] !== undefined) return Promise.resolve(_textCache[cacheKey]);

        return (async () => {
            for (let i = 0; i < candidates.length; i++) {
                try {
                    const r = await fetch(candidates[i]);
                    if (r.ok) {
                        const result = parseAs === 'json' ? await r.json() : await r.text();
                        _textCache[cacheKey] = result;
                        return result;
                    }
                } catch (e) { /* ignore */ }
            }
            _textCache[cacheKey] = null;
            return null;
        })();
    }

    const ZBZ = {
        _basePath: _basePath,

        // ---- Data Loading ----
        loadData: async function() {
            if (_data) return _data;
            const r = await fetch(_basePath + 'data/dashboard.json');
            if (!r.ok) throw new Error('dashboard.json nicht gefunden');
            _data = await r.json();
            return _data;
        },

        // ---- Text Fetching (OCR pages) ----
        fetchPageText: function (source, docId, page) {
            const paths = {
                mistral: `${_basePath}../output/mistral_results/${docId}_p${page}.md`,
                deepseek: `${_basePath}../output/ocr_results/${docId}_p${page}.md`,
                llm_corrected: `${_basePath}../output/llm_corrected_c/${docId}_p${page}.md`,
                gemini_corrected: `${_basePath}../output/gemini_corrected_a/${docId}_p${page}.md`,
            };
            const path = paths[source];
            if (!path) return Promise.resolve(null);

            const candidates = [path];
            if (source === 'mistral') {
                candidates.push(`${_basePath}data/examples/${docId}/${docId}_p${page}.md`);
            }
            return _fetchWithFallbacks(source + '/' + docId + '/' + page, candidates, 'text');
        },

        // ---- Layout Data Fetching (Gemini first, Docling fallback) ----
        fetchLayoutData: function (docId, page) {
            const padded = String(page).padStart(3, '0');
            const base = docId + '_p' + padded;
            const candidates = [
                `${_basePath}../output/layout/${docId}/${base}_layout_gemini.json`,
                `${_basePath}data/examples/${docId}/${base}_layout_gemini.json`,
                `${_basePath}../output/layout/${docId}/${base}_layout.json`,
                `${_basePath}data/examples/${docId}/${base}_layout.json`,
            ];
            return _fetchWithFallbacks('layout/' + docId + '/' + page, candidates, 'json');
        },

        // ---- TEI Fetching ----
        fetchPageTei: function (docId, page) {
            const candidates = [
                `${_basePath}../output/tei/${docId}_p${page}.xml`,
                `${_basePath}../output/tei_xml/${docId}_p${page}.xml`,
                `${_basePath}data/examples/${docId}/${docId}_p${page}.xml`,
            ];
            return _fetchWithFallbacks('tei/' + docId + '/' + page, candidates, 'text');
        },

        // ---- PAGE-XML Fetching ----
        fetchPageXml: function (docId, page) {
            const padded = String(page).padStart(3, '0');
            const candidates = [
                `${_basePath}../output/page_xml/${docId}/page/${docId}_p${padded}.xml`,
            ];
            return _fetchWithFallbacks('page_xml/' + docId + '/' + page, candidates, 'text');
        },

        // ---- METS Fetching (document-level, cached per doc) ----
        fetchMetsXml: function (docId) {
            const candidates = [
                `${_basePath}../output/page_xml/${docId}/mets.xml`,
            ];
            return _fetchWithFallbacks('mets/' + docId, candidates, 'text');
        },

        // ---- Reference TEI Fetching (per-page extraction from whole-document XML) ----
        fetchRefTeiPage: async function(docId, page) {
            const key = 'ref-tei/' + docId + '/' + page;
            if (_textCache[key] !== undefined) return _textCache[key];

            // Cache the whole document under a separate key
            const docKey = 'ref-tei-doc/' + docId;
            let docXml = _textCache[docKey];

            if (docXml === undefined) {
                const refPaths = [
                    `${_basePath}../data/referenz-tei/Pilot/${docId}.xml`,
                    `${_basePath}../data/referenz-tei/${docId}.xml`,
                ];
                docXml = null;
                for (let j = 0; j < refPaths.length; j++) {
                    try {
                        const r = await fetch(refPaths[j]);
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
                const parser = new DOMParser();
                const doc = parser.parseFromString(docXml, 'text/xml');
                const pbs = doc.querySelectorAll('pb');
                let targetPb = null;
                let targetIdx = -1;

                for (let i = 0; i < pbs.length; i++) {
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
                const nextPb = targetIdx + 1 < pbs.length ? pbs[targetIdx + 1] : null;
                const serializer = new XMLSerializer();
                let result = serializer.serializeToString(targetPb) + '\n';
                let node = targetPb.nextSibling;

                while (node && node !== nextPb) {
                    if (node.nodeType === 1 || (node.nodeType === 3 && node.textContent.trim())) {
                        result += serializer.serializeToString(node) + '\n';
                    }
                    node = node.nextSibling;
                }

                // Wrap in minimal TEI structure
                const pageXml = `<?xml version="1.0" encoding="UTF-8"?>
<TEI xmlns="http://www.tei-c.org/ns/1.0">
<text><body><div n="1">
${result}</div></body></text>
</TEI>`;

                _textCache[key] = pageXml;
                return pageXml;
            } catch (e) {
                _textCache[key] = null;
                return null;
            }
        },

        // ---- XML: parseXml, highlightXml delegated to zbz-core.js ----

        // ---- Layout Region Colors ----
        LAYOUT_COLORS: {
            zb_heading:   { stroke: '#dc2626', fill: 'rgba(220,38,38,0.12)',  label: 'Heading' },
            zb_paragraph: { stroke: '#6b7280', fill: 'rgba(107,114,128,0.08)', label: 'Absatz' },
            footnote:     { stroke: '#2563eb', fill: 'rgba(37,99,235,0.12)',  label: 'Fussnote' },
            caption:      { stroke: '#d97706', fill: 'rgba(217,119,6,0.12)',  label: 'Caption' },
            _filter:      { stroke: '#9ca3af', fill: 'rgba(156,163,175,0.06)', label: 'Filter' },
            _skip:        { stroke: '#a855f7', fill: 'rgba(168,85,247,0.08)', label: 'Skip' },
        },

        // ---- Formatting, imagePath, padPage, PUB_FORM_LABELS: delegated to zbz-core.js ----

        // ---- CER Status ----
        cerBadge: function (cer) {
            if (cer == null) return '<span class="tag">n/a</span>';
            const pct = cer * 100;
            if (pct <= 3) return '<span class="badge-ok">' + pct.toFixed(1) + '%</span>';
            if (pct <= 7) return '<span class="badge-pending">' + pct.toFixed(1) + '%</span>';
            return '<span class="badge-error">' + pct.toFixed(1) + '%</span>';
        },

        // ---- DOM Helpers (delegated to zbz-core.js) ----
        // $, $$, esc are provided by ZBZ core

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
            const steps = ZBZ.PIPELINE_STEPS;
            const cls = compact ? 'pipeline-steps compact' : 'pipeline-steps';
            let html = '<div class="' + cls + '">';
            steps.forEach((s) => {
                if (s.composite) {
                    const anyDone = s.composite.some((k) => status[k]);
                    const done = anyDone ? ' done' : '';
                    let dots = '';
                    if (!compact) {
                        if (status.ocr_mistral) dots += '<span class="engine-dot teal" title="Mistral"></span>';
                        if (status.ocr_deepseek) dots += '<span class="engine-dot violet" title="DeepSeek"></span>';
                    }
                    html += '<div class="pipeline-step' + done + '" title="' + s.title + '">' + s.label + dots + '</div>';
                } else {
                    const done = status[s.key] ? ' done' : '';
                    html += '<div class="pipeline-step' + done + '" title="' + s.title + '">' + s.label + '</div>';
                }
            });
            html += '</div>';
            return html;
        },

        // ---- Engine Badges ----
        engineBadges: function (pipelineStatus) {
            let html = '';
            if (pipelineStatus.ocr_mistral) html += '<span class="tag teal">M</span>';
            if (pipelineStatus.ocr_deepseek) html += '<span class="tag violet">DS</span>';
            if (pipelineStatus.llm_corrected) html += '<span class="tag blue">LLM</span>';
            if (pipelineStatus.gemini_corrected) html += '<span class="tag amber">GEM</span>';
            return html || '<span class="tag">-</span>';
        },

        // ---- Entity Index, URL State, Logging: delegated to zbz-core.js ----
    };

    // Merge infra-specific properties into the existing ZBZ namespace
    // (zbz-core.js and edition-shared.js are already loaded)
    const _prev = window.ZBZ || {};
    Object.keys(ZBZ).forEach((k) => { _prev[k] = ZBZ[k]; });
    window.ZBZ = _prev;
    _prev.log('Infra', 'infra-shared.js ready | basePath="' + (_basePath || '.') + '"');
})();
