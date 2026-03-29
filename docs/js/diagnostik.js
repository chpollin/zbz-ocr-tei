/**
 * diagnostik.js — Diagnostik-Werkbank UI
 *
 * Reads four JSON sources:
 *   - diagnostik_ocr.json    (Lane 2: CER, WER, Konfusion, Pipeline-Effekt)
 *   - diagnostik_tei.json    (Lane 1: Schema, Warnings, Corpus-Stats)
 *   - diagnostik_log.json    (alle Lanes: Aktivitaetslog)
 *   - diagnostik_corpus.json (konsolidiert: Proxy, Completeness, Quality-Buckets)
 *
 * 4 Tabs: Qualitaetslandschaft | CER-Werkbank | TEI & Vollstaendigkeit | Aktivitaet
 */
;(function () {
    'use strict';

    const E = (window.ZBZ && ZBZ.Edition) || (window.ZBZ && ZBZ.Shared) || {};
    const $ = E.$ || ((sel, ctx) => (ctx || document).querySelector(sel));
    const $$ = E.$$ || ((sel, ctx) => [...(ctx || document).querySelectorAll(sel)]);
    const esc = E.esc || ((s) => { if (s == null) return ''; return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); });
    const fmtNum = E.fmtNum || ((n) => n == null ? '\u2014' : Number(n).toLocaleString('de-CH'));
    const fmtPct = ((v, d) => v == null ? '\u2014' : (v * 100).toFixed(d || 1) + '%');
    const fmtDate = ((s) => s ? s.replace('T', ' ').slice(0, 19) : '\u2014');
    const fetchJSON = ((url) => fetch(url).then(r => r.ok ? r.json() : null).catch(() => null));

    const VIEWER_URL = 'viewer.html';

    function makeSortable(tableEl) {
        if (!tableEl) return;
        const headers = $$('th.sortable', tableEl);
        const tbody = $('tbody', tableEl);
        if (!headers.length || !tbody) return;
        let sortCol = null, sortAsc = true;
        headers.forEach(th => {
            th.addEventListener('click', () => {
                const col = th.cellIndex;
                if (sortCol === col) sortAsc = !sortAsc;
                else { sortCol = col; sortAsc = true; }
                headers.forEach(h => h.classList.remove('sort-asc', 'sort-desc'));
                th.classList.add(sortAsc ? 'sort-asc' : 'sort-desc');
                const rows = [...tbody.rows];
                rows.sort((a, b) => {
                    const aK = a.cells[col]?.dataset.sort ?? a.cells[col]?.textContent.trim() ?? '';
                    const bK = b.cells[col]?.dataset.sort ?? b.cells[col]?.textContent.trim() ?? '';
                    const aN = parseFloat(aK), bN = parseFloat(bK);
                    if (!isNaN(aN) && !isNaN(bN)) return sortAsc ? aN - bN : bN - aN;
                    return sortAsc ? aK.localeCompare(bK) : bK.localeCompare(aK);
                });
                rows.forEach(r => tbody.appendChild(r));
            });
        });
    }

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

    function hitRateCell(v) {
        if (v == null) return '<span class="diag-cer-cell">\u2014</span>';
        var cls = v >= 0.95 ? 'diag-excellent' : v >= 0.90 ? 'diag-good' : v >= 0.85 ? 'diag-ok' : v >= 0.75 ? 'diag-warn' : 'diag-bad';
        return '<span class="diag-cer-cell ' + cls + '">' + fmtPct(v) + '</span>';
    }

    function complBadge(status) {
        if (!status) return '\u2014';
        var cls = { 'OK': 'diag-compl-ok', 'MINOR': 'diag-compl-minor',
                    'WARNING': 'diag-compl-warning', 'MISMATCH': 'diag-compl-mismatch' };
        return '<span class="' + (cls[status] || '') + '">' + esc(status) + '</span>';
    }

    function statusBadge(status) {
        var map = {
            'geloest': 'diag-badge-ok', 'fixed': 'diag-badge-ok',
            'blocked_on_ner': 'diag-badge-blocked', 'blocked': 'diag-badge-blocked',
            'false_positive': 'diag-badge-fp', 'false-positive': 'diag-badge-fp',
            'analyse_pending': 'diag-badge-pending', 'ner_miss': 'diag-badge-pending',
            'open': 'diag-badge-error'
        };
        var labels = {
            'blocked_on_ner': 'blocked', 'false_positive': 'false-positive',
            'analyse_pending': 'analyse', 'ner_miss': 'NER-Miss'
        };
        return '<span class="ed-badge ' + (map[status] || 'diag-badge-fp') + '">' + esc(labels[status] || status) + '</span>';
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

    function metricCard(val, lbl, cls) {
        return '<div class="ed-metric"><div class="ed-metric-val ' + (cls || '') + '">'
            + esc(val) + '</div><div class="ed-metric-lbl">' + esc(lbl) + '</div></div>';
    }

    function viewerLink(docId) {
        return '<a class="diag-action-link" href="' + VIEWER_URL + '?doc=' + esc(docId) + '">Viewer</a>';
    }

    // =====================================================================
    // Tab 1: Qualitaetslandschaft
    // =====================================================================
    function renderLandscape(ocr, tei, log, corpus) {
        renderLandscapeMetrics(ocr, tei, corpus);
        renderCorpusMap(corpus);
        renderCerTimeline(ocr);
        renderLastActivity(log);
    }

    function renderLandscapeMetrics(ocr, tei, corpus) {
        var el = $('#ls-metrics');
        if (!el) return;
        var cards = [];

        // Median CER (GT)
        var medCer = ocr && ocr.summary && ocr.summary.scope_clean
            ? ocr.summary.scope_clean.median_cer : null;
        cards.push(metricCard(
            medCer != null ? fmtPct(medCer) : '\u2014', 'Median CER (GT)',
            medCer != null ? (medCer < 0.035 ? 'good' : medCer < 0.1 ? 'warn' : 'bad') : ''));

        // Proxy Hit Rate
        var proxyMed = corpus && corpus.summary ? corpus.summary.proxy_median : null;
        cards.push(metricCard(
            proxyMed != null ? fmtPct(proxyMed) : '\u2014', 'Proxy Hit Rate',
            proxyMed != null ? (proxyMed >= 0.95 ? 'good' : proxyMed >= 0.90 ? 'warn' : 'bad') : ''));

        // Schema
        var teiValid = tei && tei.summary ? tei.summary.valid : null;
        var teiTotal = tei && tei.summary ? tei.summary.total : null;
        cards.push(metricCard(
            teiValid != null ? teiValid + '/' + teiTotal : '\u2014', 'Schema-valide',
            teiValid === teiTotal ? 'good' : 'warn'));

        // Vollstaendigkeit
        var complOk = corpus && corpus.summary && corpus.summary.completeness
            ? (corpus.summary.completeness['OK'] || 0) : null;
        var complTotal = corpus && corpus.summary ? corpus.summary.total : null;
        cards.push(metricCard(
            complOk != null ? complOk + '/' + complTotal : '\u2014', 'Vollstaendig (OK)',
            complOk === complTotal ? 'good' : 'warn'));

        // Entities
        var elems = tei && tei.corpus_stats && tei.corpus_stats.elements;
        var ents = elems
            ? (elems.persName || 0) + (elems.orgName || 0) + (elems.placeName || 0) : null;
        cards.push(metricCard(ents != null ? fmtNum(ents) : '\u2014', 'Entities', ''));

        // Quality Buckets mini-bar
        var buckets = corpus && corpus.summary ? corpus.summary.quality_buckets : null;
        if (buckets) {
            var total = Object.values(buckets).reduce((a, b) => a + b, 0);
            var barHtml = '<div style="display:flex;height:8px;border-radius:4px;overflow:hidden;margin-top:4px">';
            var order = ['excellent', 'good', 'acceptable', 'check', 'outlier'];
            order.forEach(function(k) {
                if (buckets[k]) {
                    barHtml += '<div class="diag-bucket-' + k + '" style="flex:' + buckets[k] + '"'
                        + ' title="' + k + ': ' + buckets[k] + '"></div>';
                }
            });
            barHtml += '</div>';
            cards.push('<div class="ed-metric"><div class="ed-metric-val">'
                + total + '</div><div class="ed-metric-lbl">Docs gesamt</div>' + barHtml + '</div>');
        }

        el.innerHTML = cards.join('');
    }

    function renderCorpusMap(corpus) {
        var el = $('#ls-corpus-map');
        var legend = $('#ls-corpus-legend');
        var sub = $('#ls-corpus-sub');
        if (!el || !corpus || !corpus.docs) { if (el) el.innerHTML = empty(); return; }

        // Sort by hit_rate descending (best first)
        var entries = Object.entries(corpus.docs)
            .sort((a, b) => (b[1].proxy_hit_rate || 0) - (a[1].proxy_hit_rate || 0));

        if (sub) sub.textContent = '(' + entries.length + ' Dokumente, sortiert nach Proxy Hit Rate)';

        var html = entries.map(function(pair) {
            var id = pair[0], d = pair[1];
            var bucket = d.quality_bucket || 'unknown';
            var hr = d.proxy_hit_rate != null ? (d.proxy_hit_rate * 100).toFixed(1) + '%' : '?';
            var cer = d.cer != null ? ' CER ' + (d.cer * 100).toFixed(1) + '%' : '';
            var tip = 'Doc ' + id + ' | HR ' + hr + cer + ' | ' + (d.language || '?') + ' | ' + bucket;
            return '<div class="diag-corpus-bar diag-bucket-' + esc(bucket) + '">'
                + '<span class="diag-corpus-tip">' + esc(tip) + '</span></div>';
        }).join('');
        el.innerHTML = html;

        // Click handler
        el.querySelectorAll('.diag-corpus-bar').forEach(function(bar, i) {
            bar.addEventListener('click', function() {
                window.location.href = VIEWER_URL + '?doc=' + entries[i][0];
            });
        });

        // Legend
        if (legend) {
            var items = [
                ['excellent', '>= 95%', 'diag-bucket-excellent'],
                ['good', '90-95%', 'diag-bucket-good'],
                ['acceptable', '85-90%', 'diag-bucket-acceptable'],
                ['check', '75-85%', 'diag-bucket-check'],
                ['outlier', '< 75%', 'diag-bucket-outlier'],
            ];
            legend.innerHTML = items.map(function(it) {
                var count = corpus.summary.quality_buckets[it[0]] || 0;
                return '<span class="diag-legend-item">'
                    + '<span class="diag-legend-swatch ' + it[2] + '"></span>'
                    + it[0] + ' ' + it[1] + ' (' + count + ')</span>';
            }).join('');
        }
    }

    function renderCerTimeline(ocr) {
        var el = $('#ls-cer-timeline');
        if (!el) return;
        if (!ocr || !ocr.reduction_timeline || !ocr.reduction_timeline.length) {
            el.innerHTML = empty(); return;
        }
        var steps = ocr.reduction_timeline;
        var html = steps.map(function(s, i) {
            var arrow = i > 0 ? '<div class="diag-cer-arrow">\u2192</div>' : '';
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
        var el = $('#ls-last-activity');
        if (!el) return;
        if (!log || !log.length) { el.innerHTML = empty('Kein Log vorhanden'); return; }
        var sorted = log.slice().sort((a, b) => (b.timestamp || '').localeCompare(a.timestamp || ''));
        var last = sorted[0];
        el.innerHTML = '<div class="diag-last-activity">'
            + '<span class="ts">' + fmtDate(last.timestamp) + '</span>'
            + laneBadge(last.lane)
            + ' <strong>' + esc(last.action) + '</strong>'
            + (last.result_summary ? ' \u2014 ' + esc(last.result_summary) : '')
            + '</div>';
    }

    // =====================================================================
    // Tab 2: CER-Werkbank
    // =====================================================================
    function renderCer(ocr, corpus) {
        if (!ocr && !corpus) { $('#panel-cer').innerHTML = empty(); return; }
        renderCerGtMetrics(ocr);
        renderCerHistogram(ocr);
        renderCerDocTable(ocr, corpus);
        renderCerStrat(ocr);
        renderCerProxyMetrics(corpus);
        renderProxyHistogram(corpus);
        renderProxyProblemTable(corpus);
        renderCerConfusion(ocr);
        renderPipelineEffect(ocr);
    }

    function renderCerGtMetrics(ocr) {
        var el = $('#cer-gt-metrics');
        if (!el || !ocr || !ocr.summary) return;
        var s = ocr.summary.scope_clean || ocr.summary.post_normfix || {};
        el.innerHTML = [
            metricCard(fmtPct(s.mean_cer), 'Mean CER', s.mean_cer < 0.05 ? 'good' : s.mean_cer < 0.1 ? 'warn' : 'bad'),
            metricCard(fmtPct(s.median_cer), 'Median CER', s.median_cer < 0.035 ? 'good' : 'warn'),
            metricCard(fmtPct(s.std_cer), 'Std', ''),
            metricCard(fmtNum(s.docs_under_3pct), 'Docs < 3%', 'good'),
            metricCard(fmtNum(s.docs_over_15pct), 'Docs > 15%', s.docs_over_15pct > 0 ? 'bad' : 'good'),
            metricCard(fmtNum(s.n_evaluated), 'Evaluiert', '')
        ].join('');
    }

    function renderCerHistogram(ocr) {
        var el = $('#cer-histogram');
        if (!el) return;
        if (!ocr || !ocr.per_doc) { el.innerHTML = empty(); return; }

        var bins = [
            { label: '< 1%', min: 0, max: 0.01, color: 'var(--h-success)', count: 0 },
            { label: '1-3%', min: 0.01, max: 0.03, color: '#4ade80', count: 0 },
            { label: '3-5%', min: 0.03, max: 0.05, color: 'var(--h-warning)', count: 0 },
            { label: '5-10%', min: 0.05, max: 0.10, color: '#f97316', count: 0 },
            { label: '10-15%', min: 0.10, max: 0.15, color: '#ef4444', count: 0 },
            { label: '> 15%', min: 0.15, max: Infinity, color: '#991b1b', count: 0 },
        ];
        Object.values(ocr.per_doc).forEach(function(d) {
            if (d.cer == null) return;
            for (var i = 0; i < bins.length; i++) {
                if (d.cer >= bins[i].min && d.cer < bins[i].max) { bins[i].count++; break; }
            }
        });
        var maxCount = Math.max.apply(null, bins.map(function(b) { return b.count; })) || 1;

        el.innerHTML = bins.map(function(b) {
            var pct = Math.round((b.count / maxCount) * 100);
            return '<div class="diag-hist-row">'
                + '<span class="diag-hist-label">' + b.label + '</span>'
                + '<div class="diag-hist-bar-wrap"><div class="diag-hist-bar" style="width:'
                + pct + '%;background:' + b.color + '"></div></div>'
                + '<span class="diag-hist-count">' + b.count + '</span></div>';
        }).join('');
    }

    function renderCerDocTable(ocr, corpus) {
        var tbody = $('#cer-doc-table tbody');
        if (!tbody) return;

        var pe = {};
        if (ocr && ocr.pipeline_effect) {
            ocr.pipeline_effect.forEach(function(d) { pe[d.doc_id] = d; });
        }

        var source = (ocr && ocr.baseline_comparison) || [];
        if (!source.length) { tbody.innerHTML = '<tr><td colspan="9">' + empty() + '</td></tr>'; return; }

        var corpusDocs = (corpus && corpus.docs) || {};

        tbody.innerHTML = source.map(function(d) {
            var cer = d.cer_after != null ? d.cer_after : d.cer_before;
            var wer = d.wer_after != null ? d.wer_after : d.wer_before;
            var p = pe[d.doc_id] || {};
            var delta = p.delta != null ? p.delta : null;
            var deltaStr = delta != null
                ? '<span style="color:' + (delta < 0 ? 'var(--h-success)' : 'var(--h-error)') + '">'
                  + (delta < 0 ? '' : '+') + fmtPct(delta) + '</span>' : '\u2014';
            var scope = d.scope_status || 'full';
            var cd = corpusDocs[d.doc_id] || {};
            return '<tr data-doc="' + esc(d.doc_id) + '">'
                + '<td data-sort="' + esc(d.doc_id) + '">' + esc(d.doc_id) + '</td>'
                + '<td data-sort="' + (cer != null ? cer : 999) + '">' + cerCell(cer) + '</td>'
                + '<td class="num" data-sort="' + (wer != null ? wer : 999) + '">' + fmtPct(wer) + '</td>'
                + '<td data-sort="' + (cd.proxy_hit_rate != null ? cd.proxy_hit_rate : 0) + '">' + hitRateCell(cd.proxy_hit_rate) + '</td>'
                + '<td>' + esc(d.language || '?') + '</td>'
                + '<td>' + esc(d.type || '-') + '</td>'
                + '<td>' + esc(scope) + '</td>'
                + '<td class="num" data-sort="' + (delta != null ? delta : 999) + '">' + deltaStr + '</td>'
                + '<td>' + viewerLink(d.doc_id) + '</td>'
                + '</tr>';
        }).join('');

        makeSortable($('#cer-doc-table'));
        addRowClickHandlers($('#cer-doc-table'));
    }

    function renderCerStrat(ocr) {
        var el = $('#cer-strat');
        if (!el) return;
        var bc = (ocr && ocr.baseline_comparison) || [];
        if (!bc.length) { el.innerHTML = empty(); return; }

        var byLang = {};
        var byType = {};
        bc.forEach(function(d) {
            var cer = d.cer_after != null ? d.cer_after : d.cer_before;
            var lang = d.language || '?';
            var type = d.type || '-';
            if (!byLang[lang]) byLang[lang] = { n: 0, sum: 0 };
            byLang[lang].n++; byLang[lang].sum += cer;
            if (!byType[type]) byType[type] = { n: 0, sum: 0 };
            byType[type].n++; byType[type].sum += cer;
        });

        function miniTable(title, data) {
            var html = '<div class="ed-stat-panel"><div class="ed-stat-title">' + esc(title) + '</div>'
                + '<table class="ed-table"><thead><tr><th>Gruppe</th><th class="num">n</th><th class="num">Mean CER</th></tr></thead><tbody>';
            Object.keys(data).sort().forEach(function(k) {
                var avg = data[k].sum / data[k].n;
                html += '<tr><td>' + esc(k) + '</td><td class="num">' + data[k].n + '</td><td class="num">' + cerCell(avg) + '</td></tr>';
            });
            return html + '</tbody></table></div>';
        }

        el.innerHTML = miniTable('Nach Sprache', byLang) + miniTable('Nach Layout-Typ', byType);
    }

    function renderCerProxyMetrics(corpus) {
        var el = $('#cer-proxy-metrics');
        if (!el || !corpus || !corpus.summary) return;
        var s = corpus.summary;
        var bk = s.quality_buckets || {};
        el.innerHTML = [
            metricCard(s.proxy_median != null ? fmtPct(s.proxy_median) : '\u2014', 'Median Hit Rate',
                s.proxy_median >= 0.95 ? 'good' : s.proxy_median >= 0.90 ? 'warn' : 'bad'),
            metricCard(fmtNum(bk.excellent || 0), 'Docs >= 95%', 'good'),
            metricCard(fmtNum((bk.excellent || 0) + (bk.good || 0)), 'Docs >= 90%', ''),
            metricCard(fmtNum((bk.check || 0) + (bk.outlier || 0)), 'Ausreisser < 85%', (bk.check || 0) + (bk.outlier || 0) > 0 ? 'warn' : 'good'),
        ].join('');
    }

    function renderProxyHistogram(corpus) {
        var el = $('#proxy-histogram');
        if (!el || !corpus || !corpus.docs) { if (el) el.innerHTML = empty(); return; }

        var bins = [
            { label: '>= 95%', min: 0.95, max: Infinity, color: 'var(--h-success)', count: 0 },
            { label: '90-95%', min: 0.90, max: 0.95, color: '#4ade80', count: 0 },
            { label: '85-90%', min: 0.85, max: 0.90, color: 'var(--h-warning)', count: 0 },
            { label: '75-85%', min: 0.75, max: 0.85, color: '#f97316', count: 0 },
            { label: '< 75%', min: 0, max: 0.75, color: '#991b1b', count: 0 },
        ];
        Object.values(corpus.docs).forEach(function(d) {
            if (d.proxy_hit_rate == null) return;
            for (var i = 0; i < bins.length; i++) {
                if (d.proxy_hit_rate >= bins[i].min && d.proxy_hit_rate < bins[i].max) { bins[i].count++; break; }
            }
        });
        // Fix: last bin (>= 95%) is first but has max=Infinity, adjust logic
        // Re-sort bins to count correctly: iterate top-down
        bins = [
            { label: '>= 95%', count: 0, color: 'var(--h-success)' },
            { label: '90-95%', count: 0, color: '#4ade80' },
            { label: '85-90%', count: 0, color: 'var(--h-warning)' },
            { label: '75-85%', count: 0, color: '#f97316' },
            { label: '< 75%', count: 0, color: '#991b1b' },
        ];
        Object.values(corpus.docs).forEach(function(d) {
            var hr = d.proxy_hit_rate;
            if (hr == null) return;
            if (hr >= 0.95) bins[0].count++;
            else if (hr >= 0.90) bins[1].count++;
            else if (hr >= 0.85) bins[2].count++;
            else if (hr >= 0.75) bins[3].count++;
            else bins[4].count++;
        });
        var maxCount = Math.max.apply(null, bins.map(function(b) { return b.count; })) || 1;

        el.innerHTML = bins.map(function(b) {
            var pct = Math.round((b.count / maxCount) * 100);
            return '<div class="diag-hist-row">'
                + '<span class="diag-hist-label">' + b.label + '</span>'
                + '<div class="diag-hist-bar-wrap"><div class="diag-hist-bar" style="width:'
                + pct + '%;background:' + b.color + '"></div></div>'
                + '<span class="diag-hist-count">' + b.count + '</span></div>';
        }).join('');
    }

    function renderProxyProblemTable(corpus) {
        var tbody = $('#proxy-problem-table tbody');
        if (!tbody || !corpus || !corpus.docs) {
            if (tbody) tbody.innerHTML = '<tr><td colspan="6">' + empty() + '</td></tr>';
            return;
        }

        var problems = Object.entries(corpus.docs).filter(function(pair) {
            var d = pair[1];
            return (d.proxy_hit_rate != null && d.proxy_hit_rate < 0.90)
                || (d.completeness && d.completeness !== 'OK');
        }).sort(function(a, b) {
            return (a[1].proxy_hit_rate || 0) - (b[1].proxy_hit_rate || 0);
        });

        if (!problems.length) {
            tbody.innerHTML = '<tr><td colspan="6">' + empty('Keine Problemdokumente') + '</td></tr>';
            return;
        }

        tbody.innerHTML = problems.map(function(pair) {
            var id = pair[0], d = pair[1];
            return '<tr data-doc="' + esc(id) + '">'
                + '<td data-sort="' + esc(id) + '">' + esc(id) + '</td>'
                + '<td data-sort="' + (d.proxy_hit_rate || 0) + '">' + hitRateCell(d.proxy_hit_rate) + '</td>'
                + '<td>' + complBadge(d.completeness) + '</td>'
                + '<td>' + esc(d.language || '?') + '</td>'
                + '<td>' + esc(d.layout_type || '-') + '</td>'
                + '<td>' + viewerLink(id) + '</td>'
                + '</tr>';
        }).join('');

        makeSortable($('#proxy-problem-table'));
        addRowClickHandlers($('#proxy-problem-table'));
    }

    function renderCerConfusion(ocr) {
        var tbody = $('#cer-conf-table tbody');
        if (!tbody) return;
        if (!ocr || !ocr.confusion_matrix || !ocr.confusion_matrix.substitutions) {
            tbody.innerHTML = '<tr><td colspan="3">' + empty() + '</td></tr>'; return;
        }
        var top10 = ocr.confusion_matrix.substitutions.slice(0, 10);
        tbody.innerHTML = top10.map(function(s) {
            return '<tr><td class="num">' + escChar(s.ref_char) + '</td>'
                + '<td class="num">' + escChar(s.hyp_char) + '</td>'
                + '<td class="num">' + fmtNum(s.count) + '</td></tr>';
        }).join('');
    }

    function renderPipelineEffect(ocr) {
        var tbody = $('#cer-pipeline-table tbody');
        if (!tbody) return;
        if (!ocr || !ocr.pipeline_effect || !ocr.pipeline_effect.length) {
            tbody.innerHTML = '<tr><td colspan="6">' + empty() + '</td></tr>'; return;
        }
        tbody.innerHTML = ocr.pipeline_effect.map(function(e) {
            var delta = e.delta;
            var deltaStr = delta != null
                ? '<span style="color:' + (delta < 0 ? 'var(--h-success)' : 'var(--h-error)') + '">'
                  + (delta < 0 ? '' : '+') + fmtPct(delta) + '</span>' : '\u2014';
            return '<tr data-doc="' + esc(e.doc_id) + '">'
                + '<td data-sort="' + esc(e.doc_id) + '">' + esc(e.doc_id) + '</td>'
                + '<td data-sort="' + (e.ocr_baseline_cer || 999) + '">' + cerCell(e.ocr_baseline_cer) + '</td>'
                + '<td data-sort="' + (e.end_to_end_cer || 999) + '">' + cerCell(e.end_to_end_cer) + '</td>'
                + '<td class="num" data-sort="' + (delta != null ? delta : 999) + '">' + deltaStr + '</td>'
                + '<td>' + esc(e.language || '?') + '</td>'
                + '<td>' + esc(e.type || '-') + '</td>'
                + '</tr>';
        }).join('');

        makeSortable($('#cer-pipeline-table'));
        addRowClickHandlers($('#cer-pipeline-table'));
    }

    // =====================================================================
    // Tab 3: TEI & Vollstaendigkeit
    // =====================================================================
    function renderTei(tei, corpus) {
        if (!tei && !corpus) { $('#panel-tei').innerHTML = empty(); return; }
        renderTeiMetrics(tei);
        renderComplMetrics(corpus);
        renderComplTable(corpus);
        renderTeiWarnings(tei);
        renderTeiElements(tei);
        renderTeiW10(tei);
    }

    function renderTeiMetrics(tei) {
        var el = $('#tei-metrics');
        if (!el || !tei || !tei.summary) return;
        var s = tei.summary;
        el.innerHTML = [
            metricCard(fmtNum(s.total), 'Dokumente', ''),
            metricCard(fmtNum(s.valid), 'Valid', s.valid === s.total ? 'good' : 'warn'),
            metricCard(fmtNum(s.invalid), 'Invalid', s.invalid === 0 ? 'good' : 'bad'),
            metricCard(fmtNum(s.with_warnings), 'Mit Warnings', s.with_warnings === 0 ? 'good' : 'warn')
        ].join('');
    }

    function renderComplMetrics(corpus) {
        var el = $('#tei-compl-metrics');
        if (!el || !corpus || !corpus.summary || !corpus.summary.completeness) return;
        var c = corpus.summary.completeness;
        el.innerHTML = [
            metricCard(fmtNum(c['OK'] || 0), 'OK', 'good'),
            metricCard(fmtNum(c['MINOR'] || 0), 'Minor', c['MINOR'] ? '' : 'good'),
            metricCard(fmtNum(c['WARNING'] || 0), 'Warning', c['WARNING'] ? 'warn' : 'good'),
            metricCard(fmtNum(c['MISMATCH'] || 0), 'Mismatch', c['MISMATCH'] ? 'bad' : 'good'),
        ].join('');
    }

    function renderComplTable(corpus) {
        var tbody = $('#tei-compl-table tbody');
        if (!tbody || !corpus || !corpus.docs) {
            if (tbody) tbody.innerHTML = '<tr><td colspan="7">' + empty() + '</td></tr>';
            return;
        }

        var problems = Object.entries(corpus.docs).filter(function(pair) {
            var d = pair[1];
            return d.completeness && d.completeness !== 'OK';
        }).sort(function(a, b) {
            var order = { 'MISMATCH': 0, 'WARNING': 1, 'MINOR': 2 };
            return (order[a[1].completeness] || 9) - (order[b[1].completeness] || 9);
        });

        if (!problems.length) {
            tbody.innerHTML = '<tr><td colspan="7">' + empty('Alle Dokumente vollstaendig') + '</td></tr>';
            return;
        }

        tbody.innerHTML = problems.map(function(pair) {
            var id = pair[0], d = pair[1];
            return '<tr data-doc="' + esc(id) + '">'
                + '<td data-sort="' + esc(id) + '">' + esc(id) + '</td>'
                + '<td class="num" data-sort="' + (d.pages_expected || 0) + '">' + fmtNum(d.pages_expected) + '</td>'
                + '<td class="num" data-sort="' + (d.pages_actual || 0) + '">' + fmtNum(d.pages_actual) + '</td>'
                + '<td class="num" data-sort="' + (d.pages_empty || 0) + '">' + fmtNum(d.pages_empty) + '</td>'
                + '<td class="num" data-sort="' + (d.pages_thin || 0) + '">' + fmtNum(d.pages_thin) + '</td>'
                + '<td>' + complBadge(d.completeness) + '</td>'
                + '<td>' + viewerLink(id) + '</td>'
                + '</tr>';
        }).join('');

        makeSortable($('#tei-compl-table'));
        addRowClickHandlers($('#tei-compl-table'));
    }

    function renderTeiWarnings(tei) {
        var tbody = $('#tei-warn-table tbody');
        if (!tbody) return;
        if (!tei || !tei.warnings_current || !tei.warnings_current.length) {
            tbody.innerHTML = '<tr><td colspan="5">' + empty('Keine Warnings') + '</td></tr>'; return;
        }
        tbody.innerHTML = tei.warnings_current.map(function(w) {
            var docs = w.docs ? w.docs.slice(0, 5).join(', ') + (w.docs.length > 5 ? ' ...' : '') : '\u2014';
            return '<tr><td><strong>' + esc(w.code) + '</strong></td>'
                + '<td class="num">' + fmtNum(w.count) + '</td>'
                + '<td>' + statusBadge(w.status) + '</td>'
                + '<td>' + esc(docs) + '</td>'
                + '<td>' + esc(w.description) + '</td></tr>';
        }).join('');
    }

    function renderTeiElements(tei) {
        var tbody = $('#tei-elem-table tbody');
        if (!tbody) return;
        if (!tei || !tei.corpus_stats || !tei.corpus_stats.elements) {
            tbody.innerHTML = '<tr><td colspan="2">' + empty() + '</td></tr>'; return;
        }
        var elems = tei.corpus_stats.elements;
        var sorted = Object.keys(elems).sort(function(a, b) { return elems[b] - elems[a]; });
        tbody.innerHTML = sorted.map(function(k) {
            return '<tr><td>&lt;' + esc(k) + '&gt;</td><td class="num">' + fmtNum(elems[k]) + '</td></tr>';
        }).join('');
    }

    function renderTeiW10(tei) {
        var tbody = $('#tei-w10-table tbody');
        if (!tbody) return;
        if (!tei || !tei.w10_analysis || !tei.w10_analysis.length) {
            tbody.innerHTML = '<tr><td colspan="6">' + empty() + '</td></tr>'; return;
        }
        tbody.innerHTML = tei.w10_analysis.map(function(w) {
            return '<tr><td>' + esc(w.doc_id) + '</td>'
                + '<td class="num">' + fmtNum(w.text_length) + '</td>'
                + '<td class="num">' + fmtNum(w.persName_count) + '</td>'
                + '<td class="num">' + fmtNum(w.orgName_count) + '</td>'
                + '<td class="num">' + fmtNum(w.placeName_count) + '</td>'
                + '<td>' + statusBadge(w.assessment) + '</td></tr>';
        }).join('');
    }

    // =====================================================================
    // Tab 4: Aktivitaet (Log)
    // =====================================================================
    var _logEntries = [];

    function renderLog(log) {
        _logEntries = log || [];
        initLogFilters();
        renderLogEntries('all');
    }

    function initLogFilters() {
        $$('.diag-log-filter').forEach(function(btn) {
            btn.addEventListener('click', function() {
                $$('.diag-log-filter').forEach(function(b) { b.classList.remove('active'); });
                btn.classList.add('active');
                renderLogEntries(btn.getAttribute('data-lane'));
            });
        });
    }

    function renderLogEntries(lane) {
        var el = $('#log-content');
        if (!el) return;
        if (!_logEntries.length) { el.innerHTML = empty('Noch keine Log-Eintraege'); return; }

        var filtered = lane === 'all' ? _logEntries : _logEntries.filter(function(e) { return e.lane === lane; });
        var sorted = filtered.slice().sort(function(a, b) { return (b.timestamp || '').localeCompare(a.timestamp || ''); });

        if (!sorted.length) { el.innerHTML = empty('Keine Eintraege fuer diesen Filter'); return; }

        el.innerHTML = sorted.map(function(e) {
            return '<div class="diag-log-entry">'
                + '<span class="diag-log-ts">' + fmtDate(e.timestamp) + '</span>'
                + laneBadge(e.lane)
                + '<span class="diag-log-action">' + esc(e.action) + '</span>'
                + '<span class="diag-log-result">' + esc(e.result_summary || e.details || '') + '</span>'
                + '</div>';
        }).join('');
    }

    // =====================================================================
    // Shared: Row click handlers, Collapsible sections, Tabs, Init
    // =====================================================================
    function addRowClickHandlers(tableEl) {
        if (!tableEl) return;
        var tbody = $('tbody', tableEl);
        if (!tbody) return;
        tbody.querySelectorAll('tr[data-doc]').forEach(function(tr) {
            tr.addEventListener('click', function(e) {
                if (e.target.tagName === 'A') return;
                window.location.href = VIEWER_URL + '?doc=' + tr.dataset.doc;
            });
        });
    }

    function initCollapsible() {
        $$('.diag-collapsible').forEach(function(header) {
            header.addEventListener('click', function() {
                var target = header.getAttribute('data-target');
                var section = document.getElementById(target);
                if (!section) return;
                var isOpen = section.classList.contains('open');
                section.classList.toggle('open');
                header.classList.toggle('open');
            });
        });
    }

    function initTabs() {
        $$('.ed-tab').forEach(function(btn) {
            btn.addEventListener('click', function() {
                $$('.ed-tab').forEach(function(b) { b.classList.remove('active'); b.setAttribute('aria-selected', 'false'); });
                $$('.ed-tab-panel').forEach(function(p) { p.classList.remove('active'); });
                btn.classList.add('active');
                btn.setAttribute('aria-selected', 'true');
                var panel = $('#panel-' + btn.getAttribute('data-tab'));
                if (panel) panel.classList.add('active');
            });
        });
    }

    // =====================================================================
    // Tab 4: Entities
    // =====================================================================

    function renderEntities(ent) {
        if (!ent || !ent.summary) { $('#panel-entity').innerHTML = empty('Entity-Daten ausstehend'); return; }
        renderEntityMetrics(ent);
        renderEntityByType(ent);
        renderEntityByLanguage(ent);
        renderEntityUnlinked(ent);
    }

    function renderEntityMetrics(ent) {
        var s = ent.summary;
        var el = $('#ent-metrics');
        if (!el) return;
        el.innerHTML =
            metricCard(fmtNum(s.total), 'Index-Eintraege') +
            metricCard(fmtPct(s.linked_pct / 100), 'Verlinkt', s.linked_pct > 50 ? 'diag-good' : 'diag-warn') +
            metricCard(fmtNum(s.corpus_entities), 'Corpus-Entities') +
            metricCard(fmtNum(s.corpus_mentions), 'Mentions') +
            metricCard(fmtNum(s.corpus_documents), 'Dokumente');
    }

    function renderEntityByType(ent) {
        var el = $('#ent-by-type');
        if (!el || !ent.by_type) return;
        var types = Object.keys(ent.by_type).sort();
        var html = '';
        types.forEach(function(t) {
            var td = ent.by_type[t];
            var pct = td.linked_pct;
            var cls = pct >= 60 ? 'diag-good' : pct >= 40 ? 'diag-ok' : 'diag-warn';
            html += '<div style="margin:8px 0;display:flex;align-items:center;gap:8px">' +
                '<span style="width:100px;font-weight:600">' + esc(t) + '</span>' +
                '<span style="flex:1;height:20px;background:var(--h-bg-subtle);border-radius:4px;position:relative;overflow:hidden">' +
                '<span class="' + cls + '" style="position:absolute;left:0;top:0;height:100%;width:' + pct + '%;border-radius:4px"></span>' +
                '</span>' +
                '<span style="width:120px;text-align:right">' + td.linked + '/' + td.total + ' (' + pct + '%)</span>' +
                '</div>';
        });
        el.innerHTML = html;
    }

    function renderEntityByLanguage(ent) {
        var el = $('#ent-by-language');
        if (!el || !ent.by_language) return;
        var langs = Object.keys(ent.by_language).sort();
        var html = '<table class="ed-table"><thead><tr>' +
            '<th class="sortable">Sprache</th>' +
            '<th class="sortable">Docs</th>' +
            '<th class="sortable">Entities</th>' +
            '<th class="sortable">Mentions</th>' +
            '<th class="sortable">Dichte/Seite</th>' +
            '<th class="sortable">Resolution</th>' +
            '</tr></thead><tbody>';
        langs.forEach(function(lang) {
            var s = ent.by_language[lang];
            html += '<tr>' +
                '<td><strong>' + esc(lang) + '</strong></td>' +
                '<td>' + s.documents + '</td>' +
                '<td>' + fmtNum(s.total_entities) + '</td>' +
                '<td>' + fmtNum(s.total_mentions) + '</td>' +
                '<td>' + s.avg_density.toFixed(1) + '</td>' +
                '<td>' + hitRateCell(s.resolution_rate) + '</td>' +
                '</tr>';
        });
        html += '</tbody></table>';
        el.innerHTML = html;
        makeSortable(el.querySelector('.ed-table'));
    }

    function renderEntityUnlinked(ent) {
        var el = $('#ent-unlinked-table');
        if (!el || !ent.top_unlinked) return;
        var html = '<table class="ed-table"><thead><tr>' +
            '<th class="sortable">Name</th>' +
            '<th class="sortable">Typ</th>' +
            '<th class="sortable">Mentions</th>' +
            '<th class="sortable">Docs</th>' +
            '<th>ID</th>' +
            '</tr></thead><tbody>';
        ent.top_unlinked.forEach(function(e) {
            html += '<tr>' +
                '<td><strong>' + esc(e.main_name) + '</strong></td>' +
                '<td>' + esc(e.type) + '</td>' +
                '<td>' + fmtNum(e.mention_count) + '</td>' +
                '<td>' + e.docs_count + '</td>' +
                '<td style="color:var(--h-text-muted);font-size:var(--h-sm)">' + esc(e.xml_id) + '</td>' +
                '</tr>';
        });
        html += '</tbody></table>';
        el.innerHTML = html;
        makeSortable(el.querySelector('.ed-table'));
    }

    // =====================================================================
    // CER-Tab Erweiterung: Pagewise
    // =====================================================================

    function renderCerPagewise(ocr) {
        var pw = ocr && ocr.pagewise;
        if (!pw) return;

        // Metriken
        var el = $('#cer-pw-metrics');
        if (el) {
            var s = pw.outlier_summary;
            el.innerHTML =
                metricCard(fmtNum(s.total_pages), 'Seiten evaluiert') +
                metricCard(fmtNum(s.outlier_pages), 'Outlier (>10%)', s.outlier_pages > 10 ? 'diag-warn' : 'diag-ok') +
                metricCard(fmtPct(s.outlier_rate), 'Outlier-Rate');
        }

        // Outlier-Tabelle
        var tbl = $('#cer-pw-outlier-table');
        if (tbl && pw.top_outliers) {
            var tbody = tbl.querySelector('tbody');
            var html = '';
            pw.top_outliers.forEach(function(o) {
                html += '<tr>' +
                    '<td>' + viewerLink(o.doc_id) + ' <strong>' + esc(o.doc_id) + '</strong></td>' +
                    '<td>S.' + o.page + '</td>' +
                    '<td>' + cerCell(o.cer) + '</td>' +
                    '<td>' + fmtNum(o.ref_chars) + '</td>' +
                    '</tr>';
            });
            tbody.innerHTML = html;
            makeSortable(tbl);
        }
    }

    // =====================================================================

    async function init() {
        var loading = $('#loading');
        if (window.location.protocol === 'file:') {
            if (loading) loading.innerHTML =
                '<strong>Lokaler Betrieb</strong><br>' +
                'Die Diagnostik-Seite benoetigt einen lokalen Server.<br>' +
                '<code style="font-size:var(--h-sm);color:var(--h-text-muted)">' +
                'python -m http.server 8000 --directory docs</code>';
            return;
        }
        try {
            var [ocr, tei, log, corpus, entities] = await Promise.all([
                fetchJSON('../data/diagnostik_ocr.json'),
                fetchJSON('../data/diagnostik_tei.json'),
                fetchJSON('../data/diagnostik_log.json'),
                fetchJSON('../data/diagnostik_corpus.json'),
                fetchJSON('../data/diagnostik_entities.json').catch(function() { return null; }),
            ]);

            if (loading) loading.classList.add('hidden');
            $('#app').classList.remove('hidden');

            initTabs();
            initCollapsible();
            renderLandscape(ocr, tei, log, corpus);
            renderCer(ocr, corpus);
            renderCerPagewise(ocr);
            renderTei(tei, corpus);
            renderEntities(entities);
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
