/**
 * ZBZ OCR Pipeline -- Document Viewer Module
 * Namespace: ZBZ.Viewer
 * Depends on: shared.js (ZBZ namespace), tei-viewer.js (TeiViewer namespace)
 */
(function () {
    'use strict';

    var state = {
        docId: null,
        page: 1,
        totalPages: 0,
        source: 'mistral',
        zoom: 100,
        docData: null,
        hasDeepseek: false,
        hasLlm: false,
        layoutVisible: false,
        layoutSource: 'docling',
        teiVisible: false,
    };

    var sourceLabels = {
        mistral: 'Mistral OCR',
        llm_corrected: 'LLM-korrigiert (Claude Haiku 4.5)',
        gemini_corrected: 'Gemini-korrigiert (Flash Lite)',
        deepseek: 'DeepSeek OCR',
    };

    // DOM refs
    var docTitle = ZBZ.$('#doc-title');
    var pageInfo = ZBZ.$('#page-info');
    var pageImage = ZBZ.$('#page-image');
    var ocrText = ZBZ.$('#ocr-text');
    var prevBtn = ZBZ.$('#prev-btn');
    var nextBtn = ZBZ.$('#next-btn');
    var textLabel = ZBZ.$('#text-panel-label');

    async function init() {
        state.docId = ZBZ.getParam('doc');
        state.source = ZBZ.getParam('source') || 'mistral';
        state.page = parseInt(ZBZ.getParam('page')) || 1;

        if (!state.docId) {
            window.location.href = 'index.html';
            return;
        }

        try {
            var data = await ZBZ.loadData();
            state.docData = data.documents[state.docId];

            if (!state.docData) {
                alert('Dokument ' + state.docId + ' nicht gefunden.');
                window.location.href = 'index.html';
                return;
            }

            state.totalPages = state.docData.page_count;
            state.hasDeepseek = state.docData.deepseek_stats != null;
            state.hasLlm = state.docData.pipeline_status.llm_corrected;

            docTitle.textContent = state.docId + '.pdf \u2014 ' + state.docData.desc;

            // Show/hide source buttons
            state.hasGemini = state.docData.pipeline_status.gemini_corrected;
            if (state.hasGemini) {
                ZBZ.$('#btn-gemini').style.display = '';
            }
            if (state.hasDeepseek) {
                ZBZ.$('#btn-deepseek').style.display = '';
            }

            renderDocInfo();
            updateSourceToggle();

            // Layout automatisch aktivieren wenn Daten vorhanden
            if (state.docData.pipeline_status && state.docData.pipeline_status.layout) {
                state.layoutVisible = true;
                layoutToggle.classList.add('active');
                layoutOverlay.classList.add('active');
            }

            showPage(state.page);

        } catch (e) {
            docTitle.textContent = 'Fehler beim Laden';
        }
    }

    var PUB_FORM_LABELS = ZBZ.PUB_FORM_LABELS;

    // ---- Document Info Bar ----
    function renderDocInfo() {
        var d = state.docData;
        var html = '';

        // Title & Author (from Gemini classification)
        if (d.title) {
            html += '<div class="doc-info-section">' +
                '<span class="info-label">Titel</span>' +
                '<span class="info-value">' + ZBZ.esc(d.title) + '</span></div>';
        }
        if (d.author) {
            html += '<div class="doc-info-section">' +
                '<span class="info-label">Autor</span>' +
                '<span class="info-value">' + ZBZ.esc(d.author) + '</span></div>';
        }
        if (d.title || d.author) {
            html += '<div class="info-divider"></div>';
        }

        // Type & Language (with pub_form)
        var formLabel = PUB_FORM_LABELS[d.pub_form] || d.pub_form || '';
        html += '<div class="doc-info-section">' +
            '<span class="info-label">Typ / Sprache</span>' +
            '<span class="info-value"><span class="tag">' + d.type + '</span> ' + d.lang +
            (formLabel ? ' / ' + formLabel : '') + '</span>' +
            '</div>';

        // Date
        if (d.date) {
            html += '<div class="doc-info-section">' +
                '<span class="info-label">Datum</span>' +
                '<span class="info-value">' + d.date + '</span></div>';
        }

        html += '<div class="info-divider"></div>';

        // Pages
        html += '<div class="doc-info-section">' +
            '<span class="info-label">Seiten</span>' +
            '<span class="info-value">' + d.page_count + '</span>' +
            '</div>';

        // Phase
        if (d.phase) {
            html += '<div class="doc-info-section">' +
                '<span class="info-label">Testphase</span>' +
                '<span class="info-value">' + d.phase + '</span>' +
                '</div>';
        }

        html += '<div class="info-divider"></div>';

        // Pipeline Status
        html += '<div class="doc-info-section">' +
            '<span class="info-label">Pipeline</span>' +
            '<span class="info-value">' + ZBZ.renderPipelineStatus(d.pipeline_status) + '</span>' +
            '</div>';

        html += '<div class="info-divider"></div>';

        // Engines
        html += '<div class="doc-info-section">' +
            '<span class="info-label">Engines</span>' +
            '<span class="info-value"><span class="engine-badges">' + ZBZ.engineBadges(d.pipeline_status) + '</span></span>' +
            '</div>';

        html += '<div class="info-divider"></div>';

        // CER Bars
        var cerM = d.mistral_cer;
        var cerL = d.evaluation ? d.evaluation.cer_llm : null;
        var cerG = d.gemini_cer || null;
        var cerD = d.deepseek_stats ? d.deepseek_stats.cer : null;

        if (cerM != null || cerL != null || cerG != null || cerD != null) {
            var maxCer = Math.max(cerM || 0, cerL || 0, cerG || 0, cerD || 0, 0.01);
            var scale = 100 / (maxCer * 1.3);

            html += '<div class="doc-info-section">' +
                '<span class="info-label">CER Vergleich</span>' +
                '<div class="cer-mini-bars">';

            if (cerM != null) {
                html += '<div class="cer-mini-bar">' +
                    '<span class="bar-label">Mistral</span>' +
                    '<div class="bar-track"><div class="bar-fill teal" style="width:' + Math.max(cerM * scale, 3) + '%"></div></div>' +
                    '<span class="bar-val" style="color:var(--accent-a)">' + ZBZ.fmtPct(cerM, 1) + '</span>' +
                    '</div>';
            }

            if (cerL != null) {
                var delta = cerM != null ? cerL - cerM : null;
                var deltaHtml = '';
                if (delta != null) {
                    var cls = delta < 0 ? 'positive' : (delta > 0 ? 'negative' : '');
                    var sign = delta < 0 ? '' : '+';
                    deltaHtml = '<span class="improvement ' + cls + '">' + sign + (delta * 100).toFixed(1) + '</span>';
                }
                html += '<div class="cer-mini-bar">' +
                    '<span class="bar-label">LLM</span>' +
                    '<div class="bar-track"><div class="bar-fill blue" style="width:' + Math.max(cerL * scale, 3) + '%"></div></div>' +
                    '<span class="bar-val" style="color:var(--accent-c)">' + ZBZ.fmtPct(cerL, 1) + deltaHtml + '</span>' +
                    '</div>';
            }

            if (cerG != null) {
                var deltaG = cerM != null ? cerG - cerM : null;
                var deltaGHtml = '';
                if (deltaG != null) {
                    var clsG = deltaG < 0 ? 'positive' : (deltaG > 0 ? 'negative' : '');
                    var signG = deltaG < 0 ? '' : '+';
                    deltaGHtml = '<span class="improvement ' + clsG + '">' + signG + (deltaG * 100).toFixed(1) + '</span>';
                }
                html += '<div class="cer-mini-bar">' +
                    '<span class="bar-label">Gemini</span>' +
                    '<div class="bar-track"><div class="bar-fill" style="width:' + Math.max(cerG * scale, 3) + '%;background:#f59e0b"></div></div>' +
                    '<span class="bar-val" style="color:#f59e0b">' + ZBZ.fmtPct(cerG, 1) + deltaGHtml + '</span>' +
                    '</div>';
            }

            if (cerD != null) {
                html += '<div class="cer-mini-bar">' +
                    '<span class="bar-label">DeepS.</span>' +
                    '<div class="bar-track"><div class="bar-fill violet" style="width:' + Math.max(cerD * scale, 3) + '%"></div></div>' +
                    '<span class="bar-val" style="color:var(--accent-b)">' + ZBZ.fmtPct(cerD, 1) + '</span>' +
                    '</div>';
            }

            html += '</div></div>';

            html += '<div class="info-divider"></div>';
        }

        // WER
        if (d.evaluation) {
            html += '<div class="doc-info-section">' +
                '<span class="info-label">WER (LLM)</span>' +
                '<span class="info-value">' + ZBZ.fmtPct(d.evaluation.wer_llm) + '</span>' +
                '</div>';

            html += '<div class="doc-info-section">' +
                '<span class="info-label">Ref. Zeichen</span>' +
                '<span class="info-value">' + ZBZ.fmtNum(d.evaluation.ref_chars) + '</span>' +
                '</div>';
        }

        // LLM Stats
        if (d.llm_stats) {
            html += '<div class="info-divider"></div>';
            html += '<div class="doc-info-section">' +
                '<span class="info-label">LLM Tokens</span>' +
                '<span class="info-value">' + ZBZ.fmtNum(d.llm_stats.input_tokens + d.llm_stats.output_tokens) + '</span>' +
                '</div>';
        }

        // DeepSeek info
        if (d.deepseek_stats) {
            html += '<div class="info-divider"></div>';
            html += '<div class="doc-info-section">' +
                '<span class="info-label">DeepSeek</span>' +
                '<span class="info-value">' + d.deepseek_stats.pages + ' S. / ' + ZBZ.fmtNum(d.deepseek_stats.chars) + ' Zeichen</span>' +
                '</div>';
        }

        ZBZ.$('#doc-info-inner').innerHTML = html;
    }

    // ---- Layout Overlay ----
    var layoutOverlay = ZBZ.$('#layout-overlay');
    var layoutToggle = ZBZ.$('#layout-toggle');
    var imageWrapper = ZBZ.$('#image-wrapper');

    function toggleLayout() {
        state.layoutVisible = !state.layoutVisible;
        layoutToggle.classList.toggle('active', state.layoutVisible);

        if (state.layoutVisible) {
            renderLayout();
            layoutOverlay.classList.add('active');
        } else {
            layoutOverlay.innerHTML = '';
            layoutOverlay.classList.remove('active');
        }
    }

    async function renderLayout() {
        if (!state.layoutVisible) return;

        var data = await ZBZ.fetchLayoutData(state.docId, state.page, state.layoutSource);

        layoutOverlay.innerHTML = '';

        if (!data || !data.regions || data.regions.length === 0) {
            return;
        }

        layoutOverlay.setAttribute('viewBox', '0 0 100 100');

        var colors = ZBZ.LAYOUT_COLORS;
        var defaultColor = { stroke: '#6b7280', fill: 'rgba(107,114,128,0.08)', label: '?' };

        var isGemini = state.layoutSource === 'gemini';

        data.regions.forEach(function (region) {
            if (!region.bbox) return;

            var b = region.bbox;
            var color = colors[region.zbz_tag] || defaultColor;
            var changed = isGemini && region.changed;

            var rect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
            rect.setAttribute('x', b.x_pct);
            rect.setAttribute('y', b.y_pct);
            rect.setAttribute('width', b.w_pct);
            rect.setAttribute('height', b.h_pct);
            rect.setAttribute('rx', '0.1');

            if (changed) {
                rect.setAttribute('fill', 'rgba(234,179,8,0.15)');
                rect.setAttribute('stroke', '#eab308');
                rect.setAttribute('stroke-width', '0.3');
                rect.setAttribute('stroke-dasharray', '0.8 0.4');
            } else {
                rect.setAttribute('fill', color.fill);
                rect.setAttribute('stroke', color.stroke);
                rect.setAttribute('stroke-width', '0.15');
            }

            var tooltipText = color.label + ': ' + (region.text || '').substring(0, 80);
            if (changed && region.change_reason) {
                tooltipText += '\n--- Gemini: ' + region.change_reason;
            }
            var title = document.createElementNS('http://www.w3.org/2000/svg', 'title');
            title.textContent = tooltipText;
            rect.appendChild(title);

            layoutOverlay.appendChild(rect);

            var labelText = color.label;
            if (changed) labelText = '* ' + labelText;

            var text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
            text.setAttribute('x', String(b.x_pct + 0.3));
            text.setAttribute('y', String(b.y_pct + 1.2));
            text.setAttribute('fill', changed ? '#eab308' : color.stroke);
            text.setAttribute('font-size', '1');
            text.textContent = labelText;
            layoutOverlay.appendChild(text);
        });
    }

    layoutToggle.addEventListener('click', function () { toggleLayout(); });

    // ---- Layout Source Toggle ----
    var layoutSourceSelect = ZBZ.$('#layout-source');
    layoutSourceSelect.addEventListener('change', function () {
        state.layoutSource = layoutSourceSelect.value;
        if (state.layoutVisible) {
            renderLayout();
        }
    });

    // ---- TEI Panel ----
    var teiPanel = ZBZ.$('#tei-panel');
    var teiToggle = ZBZ.$('#tei-toggle');
    var divider2 = ZBZ.$('#divider2');

    function toggleTei() {
        state.teiVisible = !state.teiVisible;
        teiToggle.classList.toggle('active', state.teiVisible);

        if (state.teiVisible) {
            teiPanel.style.display = '';
            divider2.style.display = '';
            ZBZ.$('#image-panel').style.flex = '1 1 0';
            ZBZ.$('#text-panel').style.flex = '1 1 0';
            teiPanel.style.flex = '1 1 0';
            TeiViewer.loadTei(state.docId, state.page);
        } else {
            teiPanel.style.display = 'none';
            divider2.style.display = 'none';
            ZBZ.$('#image-panel').style.flex = '1';
            ZBZ.$('#text-panel').style.flex = '1';
        }
    }

    teiToggle.addEventListener('click', function () { toggleTei(); });

    // ---- Info Toggle ----
    ZBZ.$('#info-toggle').addEventListener('click', function () {
        ZBZ.$('#doc-info-bar').classList.toggle('collapsed');
    });

    // ---- Source Toggle ----
    function updateSourceToggle() {
        var btns = ZBZ.$$('#source-toggle .source-btn');
        btns.forEach(function (btn) {
            btn.classList.remove('active');
            if (btn.getAttribute('data-source') === state.source) {
                btn.classList.add('active');
            }
        });
        textLabel.textContent = sourceLabels[state.source] || 'OCR-Text';
    }

    ZBZ.$$('#source-toggle .source-btn').forEach(function (btn) {
        btn.addEventListener('click', function () {
            state.source = btn.getAttribute('data-source');
            updateSourceToggle();
            loadText();
            ZBZ.setParams({ source: state.source });
        });
    });

    // ---- Page Navigation ----
    async function showPage(page) {
        if (page < 1 || page > state.totalPages) return;
        state.page = page;

        pageImage.src = ZBZ.imagePath(state.docId, page);
        pageImage.style.width = state.zoom + '%';
        imageWrapper.style.width = state.zoom + '%';

        await loadText();
        renderLayout();
        if (state.teiVisible) TeiViewer.loadTei(state.docId, state.page);

        pageInfo.textContent = page + ' / ' + state.totalPages;
        prevBtn.disabled = page <= 1;
        nextBtn.disabled = page >= state.totalPages;

        ZBZ.setParams({ doc: state.docId, page: page, source: state.source });
    }

    async function loadText() {
        ocrText.textContent = 'Lade...';
        var text = await ZBZ.fetchPageText(state.source, state.docId, state.page);
        if (text) {
            ocrText.textContent = text;
        } else {
            ocrText.innerHTML = '<span style="color:var(--text-muted);font-style:italic">Keine Daten fuer diese Quelle/Seite vorhanden.</span>';
        }
    }

    prevBtn.addEventListener('click', function () { showPage(state.page - 1); });
    nextBtn.addEventListener('click', function () { showPage(state.page + 1); });

    // ---- Zoom ----
    ZBZ.$('#zoom-in').addEventListener('click', function () {
        state.zoom = Math.min(300, state.zoom + 25);
        pageImage.style.width = state.zoom + '%';
        imageWrapper.style.width = state.zoom + '%';
        ZBZ.$('#zoom-reset').textContent = state.zoom + '%';
    });

    ZBZ.$('#zoom-out').addEventListener('click', function () {
        state.zoom = Math.max(25, state.zoom - 25);
        pageImage.style.width = state.zoom + '%';
        imageWrapper.style.width = state.zoom + '%';
        ZBZ.$('#zoom-reset').textContent = state.zoom + '%';
    });

    ZBZ.$('#zoom-reset').addEventListener('click', function () {
        state.zoom = 100;
        pageImage.style.width = '100%';
        imageWrapper.style.width = '100%';
        ZBZ.$('#zoom-reset').textContent = '100%';
    });

    // ---- Resizable Dividers ----
    var divider = ZBZ.$('#divider');
    var activeDivider = null;

    divider.addEventListener('mousedown', function () { activeDivider = 1; });
    divider2.addEventListener('mousedown', function () { activeDivider = 2; });

    document.addEventListener('mousemove', function (e) {
        if (!activeDivider) return;
        var layout = ZBZ.$('.viewer-area');
        var totalW = layout.offsetWidth;
        var pct = (e.clientX / totalW) * 100;

        if (activeDivider === 1) {
            var minLeft = state.teiVisible ? 15 : 20;
            var maxLeft = state.teiVisible ? 60 : 80;
            pct = Math.max(minLeft, Math.min(maxLeft, pct));
            ZBZ.$('#image-panel').style.flex = '0 0 ' + pct + '%';
            if (state.teiVisible) {
                var rest = 100 - pct;
                ZBZ.$('#text-panel').style.flex = '0 0 ' + (rest / 2) + '%';
                teiPanel.style.flex = '0 0 ' + (rest / 2) + '%';
            } else {
                ZBZ.$('#text-panel').style.flex = '0 0 ' + (100 - pct) + '%';
            }
        } else if (activeDivider === 2 && state.teiVisible) {
            var imageRect = ZBZ.$('#image-panel').getBoundingClientRect();
            var imageEnd = ((imageRect.right + 4) / totalW) * 100;
            pct = Math.max(imageEnd + 10, Math.min(90, pct));
            ZBZ.$('#text-panel').style.flex = '0 0 ' + (pct - imageEnd) + '%';
            teiPanel.style.flex = '0 0 ' + (100 - pct) + '%';
        }
    });
    document.addEventListener('mouseup', function () { activeDivider = null; });

    ZBZ.Viewer = { init: init, showPage: showPage };
    init();
})();
