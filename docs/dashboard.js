/**
 * ZBZ OCR Pipeline -- Dashboard Module
 * Namespace: ZBZ.Dashboard
 * Depends on: shared.js (ZBZ namespace)
 */
(function () {
    'use strict';

    var data = null;

    async function init() {
        try {
            data = await ZBZ.loadData();
        } catch (e) {
            ZBZ.$('#loading').textContent = 'Fehler: dashboard.json nicht gefunden. Bitte python -m scripts.generate_dashboard_data ausfuehren.';
            return;
        }

        ZBZ.$('#loading').style.display = 'none';
        ZBZ.$('#app').style.display = 'block';

        renderMetrics();
        renderPhaseSummary();
        renderCatalog();
        initFilters();
    }

    // ---- A) Metriken ----
    function renderMetrics() {
        var s = data.pipeline_summary;

        ZBZ.$('#metrics').innerHTML =
            metricCard('Korpus',
                s.total_docs + ' Dokumente',
                ZBZ.fmtNum(s.total_pages) + ' Seiten, ' + s.docs_classified + ' klassifiziert') +
            metricCard('OCR (Mistral)',
                '<span class="teal">' + s.docs_with_ocr + '</span> <span class="dim">/ ' + s.total_docs + '</span>',
                'Mistral Document AI') +
            metricCard('Layout',
                s.docs_with_layout + ' <span class="dim">/ ' + s.total_docs + '</span>',
                'Docling + Gemini QA') +
            metricCard('CER (Fehlerrate)',
                s.avg_cer_mistral != null ? '<span class="teal">' + ZBZ.fmtPct(s.avg_cer_mistral) + '</span>' : '-',
                s.pilot_docs + ' Pilot-Docs evaluiert');
    }

    function metricCard(label, value, detail) {
        return '<div class="metric-card">' +
            '<div class="label">' + label + '</div>' +
            '<div class="value">' + value + '</div>' +
            '<div class="detail">' + detail + '</div>' +
            '</div>';
    }

    // ---- B) Korpus-Uebersicht ----
    function renderPhaseSummary() {
        var c = data.corpus_overview;
        if (!c) { ZBZ.$('#phase-summary').innerHTML = ''; return; }

        var TYPE_LABELS = { A: 'Einspaltig', B: 'Zweispaltig', C: 'Monografie', D: 'Spezial', '-': 'Offen' };
        var FORM_LABELS = Object.assign({}, ZBZ.PUB_FORM_LABELS, { '-': 'Offen' });

        function distCard(title, dist, labels) {
            var html = '<div class="metric-card"><div class="label">' + title + '</div>';
            var entries = Object.keys(dist);
            entries.forEach(function (key) {
                var label = labels ? (labels[key] || key) : key;
                var count = dist[key];
                html += '<div style="display:flex;justify-content:space-between;padding:2px 0;font-size:0.85rem">' +
                    '<span>' + label + '</span>' +
                    '<span style="font-weight:600">' + count + '</span></div>';
            });
            html += '</div>';
            return html;
        }

        var html = '<div class="metric-grid" style="grid-template-columns:repeat(3,1fr)">';
        html += distCard('Layout-Typen', c.types, TYPE_LABELS);
        html += distCard('Sprachen', c.languages, null);
        html += distCard('Publikationsformen', c.forms, FORM_LABELS);
        html += '</div>';

        ZBZ.$('#phase-summary').innerHTML = html;
    }

    // ---- C) Dokumentkatalog ----
    function renderCatalog() {
        var docs = data.documents;
        var ids = Object.keys(docs).sort(function (a, b) {
            var da = DEMO_DOCS[a] ? 0 : 1;
            var db = DEMO_DOCS[b] ? 0 : 1;
            if (da !== db) return da - db;
            var pa = docs[a].type !== '-' ? 0 : 1;
            var pb = docs[b].type !== '-' ? 0 : 1;
            if (pa !== pb) return pa - pb;
            return parseInt(a) - parseInt(b);
        });

        var html = '<div class="doc-table-wrap"><table class="doc-table"><thead><tr>' +
            '<th>ID</th>' +
            '<th>Titel / Beschreibung</th>' +
            '<th>Typ</th>' +
            '<th>Sprache</th>' +
            '<th>Form</th>' +
            '<th>Seiten</th>' +
            '<th>Pipeline</th>' +
            '<th>Engines</th>' +
            '<th>CER (Mistral)</th>' +
            '<th></th>' +
            '</tr></thead><tbody id="catalog-body">';

        ids.forEach(function (id) {
            html += catalogRow(docs[id]);
        });

        html += '</tbody></table></div>';
        ZBZ.$('#doc-catalog').innerHTML = html;
    }

    var PUB_FORM_LABELS = ZBZ.PUB_FORM_LABELS;

    var DEMO_DOCS = { '2310': true, '1000': true, '1330': true, '1540': true };

    function catalogRow(d) {
        var cerMistral = d.mistral_cer != null ? ZBZ.cerBadge(d.mistral_cer) : '<span class="tag">-</span>';

        var engines = [];
        if (d.pipeline_status.ocr_mistral) engines.push('mistral');
        if (d.pipeline_status.ocr_deepseek) engines.push('deepseek');
        if (d.pipeline_status.llm_corrected) engines.push('llm');

        var titleDesc = '';
        if (d.title) {
            titleDesc = '<strong>' + ZBZ.esc(d.title) + '</strong>';
            if (d.desc) titleDesc += '<br><span style="color:var(--text-muted);font-size:0.75rem">' + ZBZ.esc(d.desc) + '</span>';
        } else {
            titleDesc = d.desc || '';
        }

        var formLabel = PUB_FORM_LABELS[d.pub_form] || d.pub_form || '-';

        var demoBadge = DEMO_DOCS[d.doc_id] ? ' <span class="demo-badge">DEMO</span>' : '';

        return '<tr data-id="' + d.doc_id + '" data-type="' + d.type + '" data-lang="' + d.lang + '" data-status="' + docStatusKey(d) + '" data-engines="' + engines.join(',') + '">' +
            '<td><strong>' + d.doc_id + '</strong>' + demoBadge + '</td>' +
            '<td>' + titleDesc + '</td>' +
            '<td><span class="tag">' + d.type + '</span></td>' +
            '<td>' + d.lang + '</td>' +
            '<td>' + formLabel + '</td>' +
            '<td>' + d.page_count + '</td>' +
            '<td>' + ZBZ.renderPipelineStatus(d.pipeline_status) + '</td>' +
            '<td><div class="engine-badges">' + ZBZ.engineBadges(d.pipeline_status) + '</div></td>' +
            '<td>' + cerMistral + '</td>' +
            '<td><a href="viewer.html?doc=' + d.doc_id + '">Viewer</a></td>' +
            '</tr>';
    }

    function docStatusKey(d) {
        if (d.pipeline_status.evaluation) return 'complete';
        if (d.pipeline_status.ocr_mistral || d.pipeline_status.layout || d.pipeline_status.tei) return 'partial';
        return 'pending';
    }

    function initFilters() {
        var search = ZBZ.$('#filter-search');
        var type = ZBZ.$('#filter-type');
        var lang = ZBZ.$('#filter-lang');
        var status = ZBZ.$('#filter-status');
        var engine = ZBZ.$('#filter-engine');

        function apply() {
            var q = search.value.toLowerCase();
            var t = type.value;
            var l = lang.value;
            var s = status.value;
            var eng = engine.value;
            var rows = ZBZ.$$('#catalog-body tr');

            rows.forEach(function (row) {
                var rowType = row.getAttribute('data-type');
                var rowLang = row.getAttribute('data-lang') || '';
                var rowStatus = row.getAttribute('data-status');
                var rowEngines = row.getAttribute('data-engines') || '';
                var text = row.textContent.toLowerCase();

                var show = true;
                if (q && text.indexOf(q) === -1) show = false;
                if (t && rowType !== t) show = false;
                if (l && rowLang.indexOf(l) === -1) show = false;
                if (s === 'pilot') {
                    if (rowType === '-') show = false;
                } else if (s && rowStatus !== s) {
                    show = false;
                }
                if (eng && rowEngines.indexOf(eng) === -1) show = false;

                row.style.display = show ? '' : 'none';
            });
        }

        search.addEventListener('input', apply);
        type.addEventListener('change', apply);
        lang.addEventListener('change', apply);
        status.addEventListener('change', apply);
        engine.addEventListener('change', apply);
    }

    ZBZ.Dashboard = { init: init };
    init();
})();
