/**
 * diagnostik.js — Pipeline-Diagnostik UI (Lane 3 Ownership)
 *
 * Laedt drei JSON-Quellen:
 *   - diagnostik_ocr.json  (Lane 2)
 *   - diagnostik_tei.json  (Lane 1)
 *   - diagnostik_log.json  (alle Lanes)
 *
 * 4 Tabs: Uebersicht | OCR-Qualitaet | TEI-Qualitaet | Aktivitaet
 */
;(function () {
    'use strict';

    var OCR_URL = '../data/diagnostik_ocr.json';
    var TEI_URL = '../data/diagnostik_tei.json';
    var LOG_URL = '../data/diagnostik_log.json';

    // --- Helpers ---
    function $(sel) { return document.querySelector(sel); }
    function $$(sel) { return Array.prototype.slice.call(document.querySelectorAll(sel)); }
    function esc(s) { return s == null ? '' : String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }
    function pct(v, d) { return v == null ? '—' : (v * 100).toFixed(d || 1) + '%'; }
    function num(v) { return v == null ? '—' : Number(v).toLocaleString('de-CH'); }
    function empty(msg) { return '<div class="diag-empty">' + esc(msg || 'Daten ausstehend') + '</div>'; }

    function cerClass(v) {
        if (v == null) return '';
        if (v < 0.01) return 'diag-excellent';
        if (v <= 0.03) return 'diag-good';
        if (v <= 0.05) return 'diag-ok';
        if (v <= 0.15) return 'diag-warn';
        return 'diag-bad';
    }

    function cerCell(v) {
        if (v == null) return '<span class="diag-cer-cell">—</span>';
        return '<span class="diag-cer-cell ' + cerClass(v) + '">' + pct(v) + '</span>';
    }

    function statusBadge(status) {
        var map = {
            'geloest': 'diag-badge-ok', 'fixed': 'diag-badge-ok',
            'blocked_on_ner': 'diag-badge-blocked', 'blocked': 'diag-badge-blocked',
            'false_positive': 'diag-badge-fp', 'false-positive': 'diag-badge-fp',
            'analyse_pending': 'diag-badge-pending', 'ner_miss': 'diag-badge-pending',
            'open': 'diag-badge-error'
        };
        var cls = map[status] || 'diag-badge-fp';
        var labels = {
            'blocked_on_ner': 'blocked', 'false_positive': 'false-positive',
            'analyse_pending': 'analyse', 'ner_miss': 'NER-Miss'
        };
        return '<span class="diag-badge ' + cls + '">' + esc(labels[status] || status) + '</span>';
    }

    function laneBadge(lane) {
        var cls = { 'tei': 'diag-badge-l1', 'ocr': 'diag-badge-l2', 'edition': 'diag-badge-l3' };
        var labels = { 'tei': 'L1', 'ocr': 'L2', 'edition': 'L3' };
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

    // --- Sortable Table ---
    function makeSortable(tableId, rows, renderFn) {
        var table = $('#' + tableId);
        if (!table) return;
        var state = { col: null, asc: true };
        var headers = Array.prototype.slice.call(table.querySelectorAll('th.sortable'));

        headers.forEach(function (th) {
            th.addEventListener('click', function () {
                var col = th.getAttribute('data-col');
                if (state.col === col) { state.asc = !state.asc; }
                else { state.col = col; state.asc = true; }
                headers.forEach(function (h) { h.classList.remove('sort-asc', 'sort-desc'); });
                th.classList.add(state.asc ? 'sort-asc' : 'sort-desc');
                rows.sort(function (a, b) {
                    var va = a[col], vb = b[col];
                    if (va == null) return 1;
                    if (vb == null) return -1;
                    if (typeof va === 'number') return state.asc ? va - vb : vb - va;
                    return state.asc ? String(va).localeCompare(String(vb)) : String(vb).localeCompare(String(va));
                });
                renderFn(rows);
            });
        });
    }

    // --- Fetch helper ---
    function fetchJson(url) {
        return fetch(url).then(function (r) {
            if (!r.ok) return null;
            return r.json();
        }).catch(function () { return null; });
    }

    // =====================================================================
    // Tab: Uebersicht
    // =====================================================================
    function renderOverview(ocr, tei, log) {
        var el = $('#ov-metrics');
        if (!el) return;

        var cards = [];
        // Median CER
        var medCer = ocr && ocr.summary && ocr.summary.post_normfix
            ? ocr.summary.post_normfix.median_cer : null;
        cards.push({ val: medCer != null ? pct(medCer) : '—', lbl: 'Median CER',
                     cls: medCer != null ? (medCer < 0.05 ? 'good' : medCer < 0.1 ? 'warn' : 'bad') : '' });
        // Schema-valide
        var teiValid = tei && tei.summary ? tei.summary.valid : null;
        var teiTotal = tei && tei.summary ? tei.summary.total : null;
        cards.push({ val: teiValid != null ? teiValid + '/' + teiTotal : '—', lbl: 'Schema-valide',
                     cls: teiValid === teiTotal ? 'good' : 'warn' });
        // Entities (from corpus_stats)
        var ents = tei && tei.corpus_stats && tei.corpus_stats.elements
            ? (tei.corpus_stats.elements.persName || 0) + (tei.corpus_stats.elements.orgName || 0)
              + (tei.corpus_stats.elements.placeName || 0) : null;
        cards.push({ val: ents != null ? num(ents) : '—', lbl: 'Entities' });
        // Docs im Katalog
        var totalDocs = tei && tei.corpus_stats ? tei.corpus_stats.total_docs : null;
        cards.push({ val: totalDocs != null ? num(totalDocs) : '—', lbl: 'Docs' });
        // Seiten
        var totalPages = tei && tei.corpus_stats ? tei.corpus_stats.total_pages : null;
        cards.push({ val: totalPages != null ? num(totalPages) : '—', lbl: 'Seiten' });

        el.innerHTML = cards.map(function (c) {
            return '<div class="diag-metric"><div class="diag-metric-val ' + (c.cls || '') + '">'
                + esc(c.val) + '</div><div class="diag-metric-lbl">' + esc(c.lbl) + '</div></div>';
        }).join('');

        // Validation Timeline
        renderValTimeline(tei);

        // Last Activity
        renderLastActivity(log);
    }

    function renderValTimeline(tei) {
        var el = $('#ov-val-timeline');
        if (!el) { return; }
        if (!tei || !tei.validation_timeline || !tei.validation_timeline.length) {
            el.innerHTML = empty(); return;
        }
        var steps = tei.validation_timeline;
        var maxVal = 0;
        steps.forEach(function (s) { maxVal = Math.max(maxVal, s.valid || 0, s.invalid || 0, s.warnings || 0); });
        if (maxVal === 0) maxVal = 1;

        el.innerHTML = '<div class="diag-timeline">' + steps.map(function (s) {
            var vh = Math.round(((s.valid || 0) / maxVal) * 70);
            var ih = Math.round(((s.invalid || 0) / maxVal) * 70);
            var wh = Math.round(((s.warnings || 0) / maxVal) * 70);
            return '<div class="diag-tl-step">'
                + '<div class="diag-tl-val">' + (s.valid || 0) + '</div>'
                + '<div class="diag-tl-bar valid" style="height:' + vh + 'px"></div>'
                + (ih > 0 ? '<div class="diag-tl-bar invalid" style="height:' + ih + 'px"></div>' : '')
                + (wh > 0 ? '<div class="diag-tl-bar warn" style="height:' + wh + 'px"></div>' : '')
                + '<div class="diag-tl-label">' + esc(s.label) + '</div>'
                + '</div>';
        }).join('') + '</div>';
    }

    function renderLastActivity(log) {
        var el = $('#ov-last-activity');
        if (!el) return;
        if (!log || !log.length) { el.innerHTML = empty('Kein Log vorhanden'); return; }
        var sorted = log.slice().sort(function (a, b) {
            return (b.timestamp || '').localeCompare(a.timestamp || '');
        });
        var last = sorted[0];
        var ts = (last.timestamp || '').replace('T', ' ').slice(0, 19);
        el.innerHTML = '<div class="diag-last-activity">'
            + '<span class="ts">' + ts + '</span>'
            + laneBadge(last.lane)
            + ' <strong>' + esc(last.action) + '</strong>'
            + (last.result_summary ? ' — ' + esc(last.result_summary) : '')
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
        var el = $('#ocr-metrics');
        if (!el || !ocr.summary) return;
        var s = ocr.summary.post_normfix || ocr.summary.pre_normfix || {};
        var cards = [
            { val: pct(s.avg_cer), lbl: 'Mean CER', cls: s.avg_cer < 0.05 ? 'good' : s.avg_cer < 0.1 ? 'warn' : 'bad' },
            { val: pct(s.median_cer), lbl: 'Median CER', cls: s.median_cer < 0.05 ? 'good' : 'warn' },
            { val: pct(s.std_cer), lbl: 'Std' },
            { val: pct(s.min_cer), lbl: 'Min', cls: 'good' },
            { val: pct(s.max_cer), lbl: 'Max', cls: s.max_cer > 0.15 ? 'bad' : 'warn' },
            { val: num(s.evaluated || s.total_documents), lbl: 'Evaluiert' }
        ];
        el.innerHTML = cards.map(function (c) {
            return '<div class="diag-metric"><div class="diag-metric-val ' + (c.cls || '') + '">'
                + esc(c.val) + '</div><div class="diag-metric-lbl">' + esc(c.lbl) + '</div></div>';
        }).join('');
    }

    function renderOcrDocTable(ocr) {
        var tbody = $('#ocr-doc-table tbody');
        if (!tbody) return;

        // Merge per_doc + pipeline_effect + baseline_comparison
        var rows = [];
        var pe = {};
        if (ocr.pipeline_effect) {
            ocr.pipeline_effect.forEach(function (d) { pe[d.doc_id] = d; });
        }
        var bc = {};
        if (ocr.baseline_comparison) {
            ocr.baseline_comparison.forEach(function (d) { bc[d.doc_id] = d; });
        }

        // Build rows from baseline_comparison (has all evaluated docs)
        var source = ocr.baseline_comparison || [];
        source.forEach(function (d) {
            var p = pe[d.doc_id] || {};
            rows.push({
                doc_id: d.doc_id,
                cer: d.cer_after != null ? d.cer_after : d.cer_before,
                wer: d.wer_after != null ? d.wer_after : d.wer_before,
                language: d.language || '?',
                type: d.type || '-',
                scope: d.scope_status || 'full',
                delta: p.delta != null ? p.delta : null
            });
        });

        function render(data) {
            tbody.innerHTML = data.map(function (r) {
                var deltaStr = r.delta != null
                    ? '<span style="color:' + (r.delta < 0 ? 'var(--ed-success)' : 'var(--ed-error)') + '">'
                      + (r.delta < 0 ? '' : '+') + pct(r.delta) + '</span>' : '—';
                return '<tr>'
                    + '<td>' + esc(r.doc_id) + '</td>'
                    + '<td>' + cerCell(r.cer) + '</td>'
                    + '<td class="num">' + pct(r.wer) + '</td>'
                    + '<td>' + esc(r.language) + '</td>'
                    + '<td>' + esc(r.type) + '</td>'
                    + '<td>' + esc(r.scope) + '</td>'
                    + '<td class="num">' + deltaStr + '</td>'
                    + '</tr>';
            }).join('');
        }

        render(rows);
        makeSortable('ocr-doc-table', rows, render);
    }

    function renderOcrStrat(ocr) {
        var el = $('#ocr-strat');
        if (!el) return;

        // Build stratification from baseline_comparison
        var bc = ocr.baseline_comparison || [];
        if (!bc.length) { el.innerHTML = empty(); return; }

        var byLang = {}, byType = {};
        bc.forEach(function (d) {
            var cer = d.cer_after != null ? d.cer_after : d.cer_before;
            var lang = d.language || '?';
            var type = d.type || '-';
            if (!byLang[lang]) byLang[lang] = { n: 0, sum: 0 };
            byLang[lang].n++; byLang[lang].sum += cer;
            if (!byType[type]) byType[type] = { n: 0, sum: 0 };
            byType[type].n++; byType[type].sum += cer;
        });

        function miniTable(title, data) {
            var html = '<div class="diag-stat-panel"><div class="diag-stat-title">' + esc(title) + '</div>'
                + '<table class="diag-table"><thead><tr><th>Gruppe</th><th class="num">n</th><th class="num">Mean CER</th></tr></thead><tbody>';
            Object.keys(data).sort().forEach(function (k) {
                var avg = data[k].sum / data[k].n;
                html += '<tr><td>' + esc(k) + '</td><td class="num">' + data[k].n + '</td><td class="num">' + cerCell(avg) + '</td></tr>';
            });
            return html + '</tbody></table></div>';
        }

        el.innerHTML = miniTable('Nach Sprache', byLang) + miniTable('Nach Layout-Typ', byType);
    }

    function renderOcrConfusion(ocr) {
        var tbody = $('#ocr-conf-table tbody');
        if (!tbody) return;
        if (!ocr.confusion_matrix || !ocr.confusion_matrix.substitutions) {
            tbody.innerHTML = '<tr><td colspan="3">' + empty() + '</td></tr>'; return;
        }
        var top10 = ocr.confusion_matrix.substitutions.slice(0, 10);
        tbody.innerHTML = top10.map(function (s) {
            return '<tr><td class="num">' + escChar(s.ref_char) + '</td>'
                + '<td class="num">' + escChar(s.hyp_char) + '</td>'
                + '<td class="num">' + num(s.count) + '</td></tr>';
        }).join('');
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
        var el = $('#tei-metrics');
        if (!el || !tei.summary) return;
        var s = tei.summary;
        var cards = [
            { val: num(s.total), lbl: 'Dokumente' },
            { val: num(s.valid), lbl: 'Valid', cls: s.valid === s.total ? 'good' : 'warn' },
            { val: num(s.invalid), lbl: 'Invalid', cls: s.invalid === 0 ? 'good' : 'bad' },
            { val: num(s.with_warnings), lbl: 'Mit Warnings', cls: s.with_warnings === 0 ? 'good' : 'warn' }
        ];
        el.innerHTML = cards.map(function (c) {
            return '<div class="diag-metric"><div class="diag-metric-val ' + (c.cls || '') + '">'
                + esc(c.val) + '</div><div class="diag-metric-lbl">' + esc(c.lbl) + '</div></div>';
        }).join('');
    }

    function renderTeiWarnings(tei) {
        var tbody = $('#tei-warn-table tbody');
        if (!tbody) return;
        if (!tei.warnings_current || !tei.warnings_current.length) {
            tbody.innerHTML = '<tr><td colspan="5">' + empty('Keine Warnings') + '</td></tr>'; return;
        }
        tbody.innerHTML = tei.warnings_current.map(function (w) {
            var docs = w.docs ? w.docs.slice(0, 5).join(', ') + (w.docs.length > 5 ? ' ...' : '') : '—';
            return '<tr><td><strong>' + esc(w.code) + '</strong></td>'
                + '<td class="num">' + num(w.count) + '</td>'
                + '<td>' + statusBadge(w.status) + '</td>'
                + '<td>' + esc(docs) + '</td>'
                + '<td>' + esc(w.description) + '</td></tr>';
        }).join('');
    }

    function renderTeiElements(tei) {
        var tbody = $('#tei-elem-table tbody');
        if (!tbody) return;
        if (!tei.corpus_stats || !tei.corpus_stats.elements) {
            tbody.innerHTML = '<tr><td colspan="2">' + empty() + '</td></tr>'; return;
        }
        var elems = tei.corpus_stats.elements;
        var sorted = Object.keys(elems).sort(function (a, b) { return elems[b] - elems[a]; });
        tbody.innerHTML = sorted.map(function (k) {
            return '<tr><td>&lt;' + esc(k) + '&gt;</td><td class="num">' + num(elems[k]) + '</td></tr>';
        }).join('');
    }

    function renderTeiW10(tei) {
        var tbody = $('#tei-w10-table tbody');
        if (!tbody) return;
        if (!tei.w10_analysis || !tei.w10_analysis.length) {
            tbody.innerHTML = '<tr><td colspan="6">' + empty() + '</td></tr>'; return;
        }
        tbody.innerHTML = tei.w10_analysis.map(function (w) {
            return '<tr><td>' + esc(w.doc_id) + '</td>'
                + '<td class="num">' + num(w.text_length) + '</td>'
                + '<td class="num">' + num(w.persName_count) + '</td>'
                + '<td class="num">' + num(w.orgName_count) + '</td>'
                + '<td class="num">' + num(w.placeName_count) + '</td>'
                + '<td>' + statusBadge(w.assessment) + '</td></tr>';
        }).join('');
    }

    // =====================================================================
    // Tab: Aktivitaet (Log)
    // =====================================================================
    var _logEntries = [];

    function renderLog(log) {
        _logEntries = log || [];
        initLogFilters();
        renderLogEntries('all');
    }

    function initLogFilters() {
        var filters = $$('.diag-log-filter');
        filters.forEach(function (btn) {
            btn.addEventListener('click', function () {
                filters.forEach(function (b) { b.classList.remove('active'); });
                btn.classList.add('active');
                renderLogEntries(btn.getAttribute('data-lane'));
            });
        });
    }

    function renderLogEntries(lane) {
        var el = $('#log-content');
        if (!el) return;
        if (!_logEntries.length) { el.innerHTML = empty('Noch keine Log-Eintraege'); return; }

        var filtered = lane === 'all' ? _logEntries : _logEntries.filter(function (e) {
            return e.lane === lane;
        });

        var sorted = filtered.slice().sort(function (a, b) {
            return (b.timestamp || '').localeCompare(a.timestamp || '');
        });

        if (!sorted.length) { el.innerHTML = empty('Keine Eintraege fuer diesen Filter'); return; }

        el.innerHTML = sorted.map(function (e) {
            var ts = (e.timestamp || '').replace('T', ' ').slice(0, 19);
            return '<div class="diag-log-entry">'
                + '<span class="diag-log-ts">' + ts + '</span>'
                + laneBadge(e.lane)
                + '<span class="diag-log-action">' + esc(e.action) + '</span>'
                + '<span class="diag-log-result">' + esc(e.result_summary || e.details || '') + '</span>'
                + '</div>';
        }).join('');
    }

    // =====================================================================
    // Tabs + Init
    // =====================================================================
    function initTabs() {
        $$('.diag-tab').forEach(function (btn) {
            btn.addEventListener('click', function () {
                $$('.diag-tab').forEach(function (b) { b.classList.remove('active'); });
                $$('.diag-panel').forEach(function (p) { p.classList.remove('active'); });
                btn.classList.add('active');
                var panel = $('#panel-' + btn.getAttribute('data-tab'));
                if (panel) panel.classList.add('active');
            });
        });
    }

    async function init() {
        try {
            var results = await Promise.all([fetchJson(OCR_URL), fetchJson(TEI_URL), fetchJson(LOG_URL)]);
            var ocr = results[0], tei = results[1], log = results[2];

            $('#loading').classList.add('hidden');
            $('#app').classList.remove('hidden');

            initTabs();
            renderOverview(ocr, tei, log);
            renderOcr(ocr);
            renderTei(tei);
            renderLog(log);
        } catch (err) {
            $('#loading').textContent = 'Fehler beim Laden: ' + err.message;
            console.error(err);
        }
    }

    // Public namespace
    window.ZBZ = window.ZBZ || {};
    window.ZBZ.Diagnostik = { init: init };

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
