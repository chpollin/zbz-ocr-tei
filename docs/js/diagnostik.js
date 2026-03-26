/**
 * diagnostik.js — Pipeline-Diagnostik UI (Lane 3)
 *
 * Reads three JSON sources:
 *   - diagnostik_ocr.json  (Lane 2)
 *   - diagnostik_tei.json  (Lane 1)
 *   - diagnostik_log.json  (alle Lanes)
 *
 * 4 Tabs: Uebersicht | OCR-Qualitaet | TEI-Qualitaet | Aktivitaet
 */
;(function () {
    'use strict';

    const S = window.ZBZ && ZBZ.Shared ? ZBZ.Shared : {};
    const $ = S.$ || ((sel) => document.querySelector(sel));
    const $$ = S.$$ || ((sel) => [...document.querySelectorAll(sel)]);
    const esc = S.esc || ((s) => { if (s == null) return ''; return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); });
    const fmtNum = S.formatNumber || ((n) => n == null ? '\u2014' : Number(n).toLocaleString('de-CH'));
    const fmtPct = S.formatPercent || ((v, d) => v == null ? '\u2014' : (v * 100).toFixed(d || 1) + '%');
    const fmtDate = S.formatDate || ((s) => s ? s.replace('T', ' ').slice(0, 19) : '\u2014');
    const fetchJSON = S.fetchJSON || ((url) => fetch(url).then(r => r.ok ? r.json() : null).catch(() => null));

    const OCR_URL = '../data/diagnostik_ocr.json';
    const TEI_URL = '../data/diagnostik_tei.json';
    const LOG_URL = '../data/diagnostik_log.json';

    function empty(msg) { return '<div class="ed-empty">' + esc(msg || 'Daten ausstehend') + '</div>'; }

    function cerClass(v) {
        if (v == null) return '';
        if (v < 0.01) return 'diag-excellent';
        if (v <= 0.03) return 'diag-good';
        if (v <= 0.05) return 'diag-ok';
        if (v <= 0.15) return 'diag-warn';
        return 'diag-bad';
    }

    function cerCell(v) {
        if (v == null) return '<span class="diag-cer-cell">\u2014</span>';
        return '<span class="diag-cer-cell ' + cerClass(v) + '">' + fmtPct(v) + '</span>';
    }

    function statusBadge(status) {
        const map = {
            'geloest': 'diag-badge-ok', 'fixed': 'diag-badge-ok',
            'blocked_on_ner': 'diag-badge-blocked', 'blocked': 'diag-badge-blocked',
            'false_positive': 'diag-badge-fp', 'false-positive': 'diag-badge-fp',
            'analyse_pending': 'diag-badge-pending', 'ner_miss': 'diag-badge-pending',
            'open': 'diag-badge-error'
        };
        const labels = {
            'blocked_on_ner': 'blocked', 'false_positive': 'false-positive',
            'analyse_pending': 'analyse', 'ner_miss': 'NER-Miss'
        };
        const cls = map[status] || 'diag-badge-fp';
        return '<span class="ed-badge ' + cls + '">' + esc(labels[status] || status) + '</span>';
    }

    function laneBadge(lane) {
        const cls = { 'tei': 'diag-badge-l1', 'ocr': 'diag-badge-l2', 'edition': 'diag-badge-l3' };
        const labels = { 'tei': 'L1', 'ocr': 'L2', 'edition': 'L3' };
        return '<span class="diag-badge-lane ' + (cls[lane] || '') + '">' + (labels[lane] || lane || '?') + '</span>';
    }

    function escChar(c) {
        if (c === null || c === undefined) return 'NULL';
        if (c === ' ') return 'SPC';
        if (c === '\t') return 'TAB';
        if (c === '\n') return 'NL';
        if (c.charCodeAt(0) < 32) return 'U+' + c.charCodeAt(0).toString(16).toUpperCase().padStart(4, '0');
        return esc(c);
    }

    function metricCard(val, lbl, cls) {
        return '<div class="ed-metric"><div class="ed-metric-val ' + (cls || '') + '">'
            + esc(val) + '</div><div class="ed-metric-lbl">' + esc(lbl) + '</div></div>';
    }

    // =====================================================================
    // Tab: Uebersicht
    // =====================================================================
    function renderOverview(ocr, tei, log) {
        const el = $('#ov-metrics');
        if (!el) return;

        const cards = [];

        // Median CER
        const medCer = ocr && ocr.summary && ocr.summary.post_normfix
            ? ocr.summary.post_normfix.median_cer : null;
        cards.push(metricCard(
            medCer != null ? fmtPct(medCer) : '\u2014', 'Median CER',
            medCer != null ? (medCer < 0.05 ? 'good' : medCer < 0.1 ? 'warn' : 'bad') : ''));

        // Schema-valide
        const teiValid = tei && tei.summary ? tei.summary.valid : null;
        const teiTotal = tei && tei.summary ? tei.summary.total : null;
        cards.push(metricCard(
            teiValid != null ? teiValid + '/' + teiTotal : '\u2014', 'Schema-valide',
            teiValid === teiTotal ? 'good' : 'warn'));

        // Entities
        const elems = tei && tei.corpus_stats && tei.corpus_stats.elements;
        const ents = elems
            ? (elems.persName || 0) + (elems.orgName || 0) + (elems.placeName || 0) : null;
        cards.push(metricCard(ents != null ? fmtNum(ents) : '\u2014', 'Entities', ''));

        // Wikidata-Rate (optional key)
        const wdRate = tei && tei.corpus_stats && tei.corpus_stats.wikidata_rate;
        cards.push(metricCard(
            wdRate != null ? fmtPct(wdRate) : '\u2014', 'Wikidata-Rate',
            wdRate != null ? (wdRate > 0.5 ? 'good' : 'warn') : ''));

        // Docs
        const totalDocs = tei && tei.corpus_stats ? tei.corpus_stats.total_docs : null;
        cards.push(metricCard(totalDocs != null ? fmtNum(totalDocs) : '\u2014', 'Docs', ''));

        // Seiten
        const totalPages = tei && tei.corpus_stats ? tei.corpus_stats.total_pages : null;
        cards.push(metricCard(totalPages != null ? fmtNum(totalPages) : '\u2014', 'Seiten', ''));

        el.innerHTML = cards.join('');

        renderValTimeline(tei);
        renderCerTimeline(ocr);
        renderLastActivity(log);
    }

    function renderValTimeline(tei) {
        const el = $('#ov-val-timeline');
        if (!el) return;
        if (!tei || !tei.validation_timeline || !tei.validation_timeline.length) {
            el.innerHTML = empty(); return;
        }
        const steps = tei.validation_timeline;
        let maxVal = 0;
        steps.forEach(s => { maxVal = Math.max(maxVal, s.valid || 0, s.invalid || 0, s.warnings || 0); });
        if (maxVal === 0) maxVal = 1;

        el.innerHTML = '<div class="diag-timeline">' + steps.map(s => {
            const vh = Math.round(((s.valid || 0) / maxVal) * 70);
            const ih = Math.round(((s.invalid || 0) / maxVal) * 70);
            const wh = Math.round(((s.warnings || 0) / maxVal) * 70);
            return '<div class="diag-tl-step">'
                + '<div class="diag-tl-val">' + (s.valid || 0) + '</div>'
                + '<div class="diag-tl-bar valid" style="height:' + vh + 'px"></div>'
                + (ih > 0 ? '<div class="diag-tl-bar invalid" style="height:' + ih + 'px"></div>' : '')
                + (wh > 0 ? '<div class="diag-tl-bar warn" style="height:' + wh + 'px"></div>' : '')
                + '<div class="diag-tl-label">' + esc(s.label) + '</div>'
                + '</div>';
        }).join('') + '</div>';
    }

    function renderCerTimeline(ocr) {
        const el = $('#ov-cer-timeline');
        if (!el) return;
        if (!ocr || !ocr.reduction_timeline || !ocr.reduction_timeline.length) {
            el.innerHTML = empty(); return;
        }
        const steps = ocr.reduction_timeline;
        const html = steps.map((s, i) => {
            const arrow = i > 0 ? '<div class="diag-cer-arrow">\u2192</div>' : '';
            return arrow + '<div class="diag-cer-step">'
                + '<div class="diag-cer-step-label">' + esc(s.step) + '</div>'
                + '<div class="diag-cer-step-val">' + s.mean.toFixed(2) + '%</div>'
                + '<div class="diag-cer-step-sub">Median ' + s.median.toFixed(2) + '%</div>'
                + (s.note ? '<div class="diag-cer-step-sub">' + esc(s.note) + '</div>' : '')
                + '</div>';
        }).join('');
        el.innerHTML = '<div class="diag-cer-timeline">' + html + '</div>';
    }

    function renderLastActivity(log) {
        const el = $('#ov-last-activity');
        if (!el) return;
        if (!log || !log.length) { el.innerHTML = empty('Kein Log vorhanden'); return; }
        const sorted = log.slice().sort((a, b) => (b.timestamp || '').localeCompare(a.timestamp || ''));
        const last = sorted[0];
        el.innerHTML = '<div class="diag-last-activity">'
            + '<span class="ts">' + fmtDate(last.timestamp) + '</span>'
            + laneBadge(last.lane)
            + ' <strong>' + esc(last.action) + '</strong>'
            + (last.result_summary ? ' \u2014 ' + esc(last.result_summary) : '')
            + '</div>';
    }

    // =====================================================================
    // Tab: OCR-Qualitaet
    // =====================================================================
    function renderOcr(ocr) {
        if (!ocr) { $('#panel-ocr').innerHTML = empty(); return; }
        renderOcrMetrics(ocr);
        renderOcrDocTable(ocr);
        renderOcrStrat(ocr);
        renderOcrConfusion(ocr);
    }

    function renderOcrMetrics(ocr) {
        const el = $('#ocr-metrics');
        if (!el || !ocr.summary) return;
        const s = ocr.summary.post_normfix || ocr.summary.pre_normfix || {};
        el.innerHTML = [
            metricCard(fmtPct(s.avg_cer), 'Mean CER', s.avg_cer < 0.05 ? 'good' : s.avg_cer < 0.1 ? 'warn' : 'bad'),
            metricCard(fmtPct(s.median_cer), 'Median CER', s.median_cer < 0.05 ? 'good' : 'warn'),
            metricCard(fmtPct(s.std_cer), 'Std', ''),
            metricCard(fmtPct(s.min_cer), 'Min', 'good'),
            metricCard(fmtPct(s.max_cer), 'Max', s.max_cer > 0.15 ? 'bad' : 'warn'),
            metricCard(fmtNum(s.evaluated || s.total_documents), 'Evaluiert', '')
        ].join('');
    }

    function renderOcrDocTable(ocr) {
        const tbody = $('#ocr-doc-table tbody');
        if (!tbody) return;

        const pe = {};
        if (ocr.pipeline_effect) {
            ocr.pipeline_effect.forEach(d => { pe[d.doc_id] = d; });
        }

        const source = ocr.baseline_comparison || [];
        if (!source.length) { tbody.innerHTML = '<tr><td colspan="7">' + empty() + '</td></tr>'; return; }

        tbody.innerHTML = source.map(d => {
            const cer = d.cer_after != null ? d.cer_after : d.cer_before;
            const wer = d.wer_after != null ? d.wer_after : d.wer_before;
            const p = pe[d.doc_id] || {};
            const delta = p.delta != null ? p.delta : null;
            const deltaStr = delta != null
                ? '<span style="color:' + (delta < 0 ? 'var(--h-success)' : 'var(--h-error)') + '">'
                  + (delta < 0 ? '' : '+') + fmtPct(delta) + '</span>' : '\u2014';
            const scope = d.scope_status || 'full';
            return '<tr>'
                + '<td data-sort="' + esc(d.doc_id) + '">' + esc(d.doc_id) + '</td>'
                + '<td data-sort="' + (cer != null ? cer : 999) + '">' + cerCell(cer) + '</td>'
                + '<td class="num" data-sort="' + (wer != null ? wer : 999) + '">' + fmtPct(wer) + '</td>'
                + '<td>' + esc(d.language || '?') + '</td>'
                + '<td>' + esc(d.type || '-') + '</td>'
                + '<td>' + esc(scope) + '</td>'
                + '<td class="num" data-sort="' + (delta != null ? delta : 999) + '">' + deltaStr + '</td>'
                + '</tr>';
        }).join('');

        if (S.makeSortable) S.makeSortable($('#ocr-doc-table'));
    }

    function renderOcrStrat(ocr) {
        const el = $('#ocr-strat');
        if (!el) return;
        const bc = ocr.baseline_comparison || [];
        if (!bc.length) { el.innerHTML = empty(); return; }

        const byLang = {};
        const byType = {};
        bc.forEach(d => {
            const cer = d.cer_after != null ? d.cer_after : d.cer_before;
            const lang = d.language || '?';
            const type = d.type || '-';
            if (!byLang[lang]) byLang[lang] = { n: 0, sum: 0 };
            byLang[lang].n++; byLang[lang].sum += cer;
            if (!byType[type]) byType[type] = { n: 0, sum: 0 };
            byType[type].n++; byType[type].sum += cer;
        });

        function miniTable(title, data) {
            let html = '<div class="ed-stat-panel"><div class="ed-stat-title">' + esc(title) + '</div>'
                + '<table class="ed-table"><thead><tr><th>Gruppe</th><th class="num">n</th><th class="num">Mean CER</th></tr></thead><tbody>';
            Object.keys(data).sort().forEach(k => {
                const avg = data[k].sum / data[k].n;
                html += '<tr><td>' + esc(k) + '</td><td class="num">' + data[k].n + '</td><td class="num">' + cerCell(avg) + '</td></tr>';
            });
            return html + '</tbody></table></div>';
        }

        el.innerHTML = miniTable('Nach Sprache', byLang) + miniTable('Nach Layout-Typ', byType);
    }

    function renderOcrConfusion(ocr) {
        const tbody = $('#ocr-conf-table tbody');
        if (!tbody) return;
        if (!ocr.confusion_matrix || !ocr.confusion_matrix.substitutions) {
            tbody.innerHTML = '<tr><td colspan="3">' + empty() + '</td></tr>'; return;
        }
        const top10 = ocr.confusion_matrix.substitutions.slice(0, 10);
        tbody.innerHTML = top10.map(s =>
            '<tr><td class="num">' + escChar(s.ref_char) + '</td>'
            + '<td class="num">' + escChar(s.hyp_char) + '</td>'
            + '<td class="num">' + fmtNum(s.count) + '</td></tr>'
        ).join('');
    }

    // =====================================================================
    // Tab: TEI-Qualitaet
    // =====================================================================
    function renderTei(tei) {
        if (!tei) { $('#panel-tei').innerHTML = empty(); return; }
        renderTeiMetrics(tei);
        renderTeiWarnings(tei);
        renderTeiElements(tei);
        renderTeiW10(tei);
    }

    function renderTeiMetrics(tei) {
        const el = $('#tei-metrics');
        if (!el || !tei.summary) return;
        const s = tei.summary;
        el.innerHTML = [
            metricCard(fmtNum(s.total), 'Dokumente', ''),
            metricCard(fmtNum(s.valid), 'Valid', s.valid === s.total ? 'good' : 'warn'),
            metricCard(fmtNum(s.invalid), 'Invalid', s.invalid === 0 ? 'good' : 'bad'),
            metricCard(fmtNum(s.with_warnings), 'Mit Warnings', s.with_warnings === 0 ? 'good' : 'warn')
        ].join('');
    }

    function renderTeiWarnings(tei) {
        const tbody = $('#tei-warn-table tbody');
        if (!tbody) return;
        if (!tei.warnings_current || !tei.warnings_current.length) {
            tbody.innerHTML = '<tr><td colspan="5">' + empty('Keine Warnings') + '</td></tr>'; return;
        }
        tbody.innerHTML = tei.warnings_current.map(w => {
            const docs = w.docs ? w.docs.slice(0, 5).join(', ') + (w.docs.length > 5 ? ' ...' : '') : '\u2014';
            return '<tr><td><strong>' + esc(w.code) + '</strong></td>'
                + '<td class="num">' + fmtNum(w.count) + '</td>'
                + '<td>' + statusBadge(w.status) + '</td>'
                + '<td>' + esc(docs) + '</td>'
                + '<td>' + esc(w.description) + '</td></tr>';
        }).join('');
    }

    function renderTeiElements(tei) {
        const tbody = $('#tei-elem-table tbody');
        if (!tbody) return;
        if (!tei.corpus_stats || !tei.corpus_stats.elements) {
            tbody.innerHTML = '<tr><td colspan="2">' + empty() + '</td></tr>'; return;
        }
        const elems = tei.corpus_stats.elements;
        const sorted = Object.keys(elems).sort((a, b) => elems[b] - elems[a]);
        tbody.innerHTML = sorted.map(k =>
            '<tr><td>&lt;' + esc(k) + '&gt;</td><td class="num">' + fmtNum(elems[k]) + '</td></tr>'
        ).join('');
    }

    function renderTeiW10(tei) {
        const tbody = $('#tei-w10-table tbody');
        if (!tbody) return;
        if (!tei.w10_analysis || !tei.w10_analysis.length) {
            tbody.innerHTML = '<tr><td colspan="6">' + empty() + '</td></tr>'; return;
        }
        tbody.innerHTML = tei.w10_analysis.map(w =>
            '<tr><td>' + esc(w.doc_id) + '</td>'
            + '<td class="num">' + fmtNum(w.text_length) + '</td>'
            + '<td class="num">' + fmtNum(w.persName_count) + '</td>'
            + '<td class="num">' + fmtNum(w.orgName_count) + '</td>'
            + '<td class="num">' + fmtNum(w.placeName_count) + '</td>'
            + '<td>' + statusBadge(w.assessment) + '</td></tr>'
        ).join('');
    }

    // =====================================================================
    // Tab: Aktivitaet (Log)
    // =====================================================================
    let _logEntries = [];

    function renderLog(log) {
        _logEntries = log || [];
        initLogFilters();
        renderLogEntries('all');
    }

    function initLogFilters() {
        $$('.diag-log-filter').forEach(btn => {
            btn.addEventListener('click', () => {
                $$('.diag-log-filter').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                renderLogEntries(btn.getAttribute('data-lane'));
            });
        });
    }

    function renderLogEntries(lane) {
        const el = $('#log-content');
        if (!el) return;
        if (!_logEntries.length) { el.innerHTML = empty('Noch keine Log-Eintraege'); return; }

        const filtered = lane === 'all' ? _logEntries : _logEntries.filter(e => e.lane === lane);
        const sorted = filtered.slice().sort((a, b) => (b.timestamp || '').localeCompare(a.timestamp || ''));

        if (!sorted.length) { el.innerHTML = empty('Keine Eintraege fuer diesen Filter'); return; }

        el.innerHTML = sorted.map(e =>
            '<div class="diag-log-entry">'
            + '<span class="diag-log-ts">' + fmtDate(e.timestamp) + '</span>'
            + laneBadge(e.lane)
            + '<span class="diag-log-action">' + esc(e.action) + '</span>'
            + '<span class="diag-log-result">' + esc(e.result_summary || e.details || '') + '</span>'
            + '</div>'
        ).join('');
    }

    // =====================================================================
    // Tabs + Init
    // =====================================================================
    function initTabs() {
        $$('.ed-tab').forEach(btn => {
            btn.addEventListener('click', () => {
                $$('.ed-tab').forEach(b => b.classList.remove('active'));
                $$('.ed-tab-panel').forEach(p => p.classList.remove('active'));
                btn.classList.add('active');
                const panel = $('#panel-' + btn.getAttribute('data-tab'));
                if (panel) panel.classList.add('active');
            });
        });
    }

    async function init() {
        const loading = $('#loading');
        // file:// protocol: fetch() is blocked by CORS
        if (window.location.protocol === 'file:') {
            if (loading) loading.innerHTML =
                '<strong>Lokaler Betrieb</strong><br>' +
                'Die Diagnostik-Seite benoetigt einen lokalen Server.<br>' +
                '<code style="font-size:var(--h-sm);color:var(--h-text-muted)">' +
                'python -m http.server 8000 --directory docs</code>';
            return;
        }
        try {
            const [ocr, tei, log] = await Promise.all([
                fetchJSON(OCR_URL), fetchJSON(TEI_URL), fetchJSON(LOG_URL)
            ]);

            if (loading) loading.classList.add('hidden');
            $('#app').classList.remove('hidden');

            initTabs();
            renderOverview(ocr, tei, log);
            renderOcr(ocr);
            renderTei(tei);
            renderLog(log);
        } catch (err) {
            if (loading) loading.textContent = 'Fehler beim Laden: ' + err.message;
            console.error(err);
        }
    }

    window.ZBZ = window.ZBZ || {};
    ZBZ.Diagnostik = { init };

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
