/**
 * ZBZ OCR Pipeline -- Dashboard Module
 * Namespace: ZBZ.Dashboard
 * Depends on: shared.js (ZBZ namespace)
 */
(function () {
    'use strict';

    let data = null;

    async function init() {
        try {
            data = await ZBZ.loadData();
        } catch (e) {
            ZBZ.$('#loading').textContent = 'Fehler: dashboard.json nicht gefunden. Bitte python -m scripts.generate_dashboard_data ausfuehren.';
            ZBZ.log('Dashboard', 'FEHLER: dashboard.json nicht geladen');
            return;
        }

        ZBZ.$('#loading').classList.add('hidden');
        ZBZ.$('#app').classList.remove('hidden');

        renderMetrics();
        renderPhaseSummary();
        renderCatalog();
        initFilters();

        const s = data.pipeline_summary;
        ZBZ.log('Dashboard', `${s.total_docs} Docs | ${s.total_pages} Seiten | CER ${s.avg_cer_mistral != null ? (s.avg_cer_mistral * 100).toFixed(1) + '%' : 'n/a'}`);
    }

    // ---- A) Metriken ----
    function renderMetrics() {
        const s = data.pipeline_summary;

        ZBZ.$('#metrics').innerHTML =
            metricCard('Korpus',
                `${s.total_docs} Dokumente`,
                `${ZBZ.fmtNum(s.total_pages)} Seiten, ${s.docs_classified} klassifiziert`) +
            metricCard('OCR (Mistral)',
                `<span class="teal">${s.docs_with_ocr}</span> <span class="dim">/ ${s.total_docs}</span>`,
                'Mistral Document AI') +
            metricCard('Layout',
                `${s.docs_with_layout} <span class="dim">/ ${s.total_docs}</span>`,
                'Docling + Gemini QA') +
            metricCard('CER (Fehlerrate)',
                s.avg_cer_mistral != null ? `<span class="teal">${ZBZ.fmtPct(s.avg_cer_mistral)}</span>` : '-',
                `${s.pilot_docs} Pilot-Docs evaluiert`);
    }

    function metricCard(label, value, detail) {
        return `<div class="metric-card">` +
            `<div class="label">${label}</div>` +
            `<div class="value">${value}</div>` +
            `<div class="detail">${detail}</div>` +
            `</div>`;
    }

    // ---- B) Korpus-Uebersicht ----
    function renderPhaseSummary() {
        const c = data.corpus_overview;
        if (!c) { ZBZ.$('#phase-summary').innerHTML = ''; return; }

        const TYPE_LABELS = { A: 'Einspaltig', B: 'Zweispaltig', C: 'Monografie', D: 'Spezial', '-': 'Offen' };
        const FORM_LABELS = Object.assign({}, ZBZ.PUB_FORM_LABELS, { '-': 'Offen' });

        function distCard(title, dist, labels) {
            let html = `<div class="metric-card"><div class="label">${title}</div>`;
            const entries = Object.keys(dist);
            entries.forEach((key) => {
                const label = labels ? (labels[key] || key) : key;
                const count = dist[key];
                html += `<div class="dist-row">` +
                    `<span>${label}</span>` +
                    `<span style="font-weight:600">${count}</span></div>`;
            });
            html += '</div>';
            return html;
        }

        let html = '<div class="metric-grid grid-3col">';
        html += distCard('Layout-Typen', c.types, TYPE_LABELS);
        html += distCard('Sprachen', c.languages, null);
        html += distCard('Publikationsformen', c.forms, FORM_LABELS);
        html += '</div>';

        ZBZ.$('#phase-summary').innerHTML = html;
    }

    // ---- C) Dokumentkatalog ----
    function renderCatalog() {
        const docs = data.documents;
        const ids = Object.keys(docs).sort((a, b) => {
            const da = DEMO_DOCS[a] ? 0 : 1;
            const db = DEMO_DOCS[b] ? 0 : 1;
            if (da !== db) return da - db;
            const pa = docs[a].type !== '-' ? 0 : 1;
            const pb = docs[b].type !== '-' ? 0 : 1;
            if (pa !== pb) return pa - pb;
            return parseInt(a) - parseInt(b);
        });

        let html = '<div class="doc-table-wrap"><table class="doc-table"><thead><tr>' +
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

        ids.forEach((id) => {
            html += catalogRow(docs[id]);
        });

        html += '</tbody></table></div>';
        ZBZ.$('#doc-catalog').innerHTML = html;
    }

    const PUB_FORM_LABELS = ZBZ.PUB_FORM_LABELS;

    const DEMO_DOCS = { '2310': true, '1000': true, '1330': true, '1540': true };

    function catalogRow(d) {
        const cerMistral = d.mistral_cer != null ? ZBZ.cerBadge(d.mistral_cer) : '<span class="tag">-</span>';

        const engines = [];
        if (d.pipeline_status.ocr_mistral) engines.push('mistral');
        if (d.pipeline_status.ocr_deepseek) engines.push('deepseek');
        if (d.pipeline_status.llm_corrected) engines.push('llm');

        let titleDesc = '';
        if (d.title) {
            titleDesc = `<strong>${ZBZ.esc(d.title)}</strong>`;
            if (d.desc) titleDesc += `<br><span class="text-muted-sm">${ZBZ.esc(d.desc)}</span>`;
        } else {
            titleDesc = d.desc || '';
        }

        const formLabel = PUB_FORM_LABELS[d.pub_form] || d.pub_form || '-';

        const demoBadge = DEMO_DOCS[d.doc_id] ? ' <span class="demo-badge">DEMO</span>' : '';

        return `<tr data-id="${d.doc_id}" data-type="${d.type}" data-lang="${d.lang}" data-status="${docStatusKey(d)}" data-engines="${engines.join(',')}">` +
            `<td><strong>${d.doc_id}</strong>${demoBadge}</td>` +
            `<td>${titleDesc}</td>` +
            `<td><span class="tag">${d.type}</span></td>` +
            `<td>${d.lang}</td>` +
            `<td>${formLabel}</td>` +
            `<td>${d.page_count}</td>` +
            `<td>${ZBZ.renderPipelineStatus(d.pipeline_status)}</td>` +
            `<td><div class="engine-badges">${ZBZ.engineBadges(d.pipeline_status)}</div></td>` +
            `<td>${cerMistral}</td>` +
            `<td><a href="viewer.html?doc=${d.doc_id}">Viewer</a></td>` +
            `</tr>`;
    }

    function docStatusKey(d) {
        if (d.pipeline_status.evaluation) return 'complete';
        if (d.pipeline_status.ocr_mistral || d.pipeline_status.layout || d.pipeline_status.tei) return 'partial';
        return 'pending';
    }

    function initFilters() {
        const search = ZBZ.$('#filter-search');
        const type = ZBZ.$('#filter-type');
        const lang = ZBZ.$('#filter-lang');
        const status = ZBZ.$('#filter-status');
        const engine = ZBZ.$('#filter-engine');
        const rows = ZBZ.$$('#catalog-body tr');

        function apply() {
            const q = search.value.toLowerCase();
            const t = type.value;
            const l = lang.value;
            const s = status.value;
            const eng = engine.value;

            rows.forEach((row) => {
                const rowType = row.getAttribute('data-type');
                const rowLang = row.getAttribute('data-lang') || '';
                const rowStatus = row.getAttribute('data-status');
                const rowEngines = row.getAttribute('data-engines') || '';
                const text = row.textContent.toLowerCase();

                let show = true;
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
