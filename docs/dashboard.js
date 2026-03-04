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
        var docs = data.documents;
        var ids = Object.keys(docs);
        var cM = ids.filter(function (id) { return docs[id].pipeline_status.ocr_mistral; }).length;
        var cD = ids.filter(function (id) { return docs[id].pipeline_status.ocr_deepseek; }).length;
        var cL = ids.filter(function (id) { return docs[id].pipeline_status.llm_corrected; }).length;
        var cLayout = ids.filter(function (id) { return docs[id].pipeline_status.layout; }).length;
        var cTei = ids.filter(function (id) { return docs[id].pipeline_status.tei; }).length;

        ZBZ.$('#metrics').innerHTML =
            metricCard('Korpus', s.total_docs + ' Dokumente', ZBZ.fmtNum(s.total_pages) + ' Seiten, ' + s.pilot_docs + ' Pilot-Docs') +
            metricCard('OCR', '<span class="teal">' + cM + '</span> <span class="dim">/ ' + s.total_docs + '</span>',
                '<span style="color:var(--accent-a)">' + cM + ' Mistral</span>, ' +
                '<span style="color:var(--accent-b)">' + cD + ' DeepSeek</span>, ' +
                '<span style="color:var(--accent-c)">' + cL + ' LLM</span>') +
            metricCard('Layout + TEI', cLayout + ' Layout <span class="dim">/ ' + s.total_docs + '</span>', cTei + ' TEI generiert') +
            metricCard('Genauigkeit (CER)', '<span class="blue">' + ZBZ.fmtPct(s.avg_cer_mistral) + '</span>', 'Mistral (Pilot, ' + s.pilot_docs + ' Docs)');
    }

    function metricCard(label, value, detail) {
        return '<div class="metric-card">' +
            '<div class="label">' + label + '</div>' +
            '<div class="value">' + value + '</div>' +
            '<div class="detail">' + detail + '</div>' +
            '</div>';
    }

    // ---- B) Phasen-Uebersicht ----
    function renderPhaseSummary() {
        var phases = data.phases;
        var html = '<div class="metric-grid" style="grid-template-columns:repeat(' + phases.length + ',1fr)">';

        phases.forEach(function (p) {
            var cerM = p.avg_cer_mistral != null ? ZBZ.fmtPct(p.avg_cer_mistral) : '-';
            var cerL = p.avg_cer_llm != null ? ZBZ.fmtPct(p.avg_cer_llm) : '-';
            var statusTag = p.status === 'completed' ? '<span class="badge-ok">Abgeschlossen</span>' : '<span class="badge-pending">Teilweise</span>';

            html += '<div class="metric-card">' +
                '<div class="label">' + p.name + ' (Typ ' + p.doc_type + ')</div>' +
                '<div class="value" style="font-size:1rem">' +
                    '<span class="teal">' + cerM + '</span>' +
                    ' <span class="dim" style="font-size:0.8rem">&#8594;</span> ' +
                    '<span class="blue">' + cerL + '</span>' +
                '</div>' +
                '<div class="detail">' +
                    p.doc_ids.length + ' Dokumente ' + statusTag +
                '</div>' +
                '</div>';
        });

        html += '</div>';
        ZBZ.$('#phase-summary').innerHTML = html;
    }

    // ---- C) Dokumentkatalog ----
    function renderCatalog() {
        var docs = data.documents;
        var ids = Object.keys(docs).sort(function (a, b) {
            var pa = docs[a].type !== '-' ? 0 : 1;
            var pb = docs[b].type !== '-' ? 0 : 1;
            if (pa !== pb) return pa - pb;
            return parseInt(a) - parseInt(b);
        });

        var html = '<div class="doc-table-wrap"><table class="doc-table"><thead><tr>' +
            '<th>ID</th>' +
            '<th>Beschreibung</th>' +
            '<th>Typ</th>' +
            '<th>Sprache</th>' +
            '<th>Seiten</th>' +
            '<th>Pipeline</th>' +
            '<th>Engines</th>' +
            '<th>CER (Mistral)</th>' +
            '<th>CER (DS)</th>' +
            '<th>CER (LLM)</th>' +
            '<th></th>' +
            '</tr></thead><tbody id="catalog-body">';

        ids.forEach(function (id) {
            html += catalogRow(docs[id]);
        });

        html += '</tbody></table></div>';
        ZBZ.$('#doc-catalog').innerHTML = html;
    }

    function catalogRow(d) {
        var cerMistral = d.mistral_cer != null ? ZBZ.cerBadge(d.mistral_cer) : '<span class="tag">-</span>';
        var cerDs = d.deepseek_stats ? ZBZ.cerBadge(d.deepseek_stats.cer) : '<span class="tag">-</span>';
        var cerLlm = d.evaluation ? ZBZ.cerBadge(d.evaluation.cer_llm) : '<span class="tag">-</span>';

        var engines = [];
        if (d.pipeline_status.ocr_mistral) engines.push('mistral');
        if (d.pipeline_status.ocr_deepseek) engines.push('deepseek');
        if (d.pipeline_status.llm_corrected) engines.push('llm');

        return '<tr data-id="' + d.doc_id + '" data-type="' + d.type + '" data-status="' + docStatusKey(d) + '" data-engines="' + engines.join(',') + '">' +
            '<td><strong>' + d.doc_id + '</strong></td>' +
            '<td>' + d.desc + '</td>' +
            '<td><span class="tag">' + d.type + '</span></td>' +
            '<td>' + d.lang + '</td>' +
            '<td>' + d.page_count + '</td>' +
            '<td>' + ZBZ.renderPipelineStatus(d.pipeline_status) + '</td>' +
            '<td><div class="engine-badges">' + ZBZ.engineBadges(d.pipeline_status) + '</div></td>' +
            '<td>' + cerMistral + '</td>' +
            '<td>' + cerDs + '</td>' +
            '<td>' + cerLlm + '</td>' +
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
        var status = ZBZ.$('#filter-status');
        var engine = ZBZ.$('#filter-engine');

        function apply() {
            var q = search.value.toLowerCase();
            var t = type.value;
            var s = status.value;
            var eng = engine.value;
            var rows = ZBZ.$$('#catalog-body tr');

            rows.forEach(function (row) {
                var rowType = row.getAttribute('data-type');
                var rowStatus = row.getAttribute('data-status');
                var rowEngines = row.getAttribute('data-engines') || '';
                var text = row.textContent.toLowerCase();

                var show = true;
                if (q && text.indexOf(q) === -1) show = false;
                if (t && rowType !== t) show = false;
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
        status.addEventListener('change', apply);
        engine.addEventListener('change', apply);
    }

    ZBZ.Dashboard = { init: init };
    init();
})();
