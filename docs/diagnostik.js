/**
 * diagnostik.js — OCR-Diagnostik-Dashboard (Lane 2)
 *
 * Laedt docs/data/diagnostik_ocr.json und rendert:
 * 1. CER-Heatmap (24 Docs)
 * 2. Konfusionsmatrix (Top-30 Substitutionen)
 * 3. Baseline-Vergleich (Balkendiagramm)
 * 4. Pipeline-Effekt (Dot-Plot Canvas)
 * 5. Outlier-Diagnose (Detail-Cards)
 */
;(function () {
    'use strict';

    const DATA_URL = 'data/diagnostik_ocr.json';

    // --- Helpers ---
    const $ = (sel, ctx) => (ctx || document).querySelector(sel);
    const $$ = (sel, ctx) => [...(ctx || document).querySelectorAll(sel)];
    const pct = (v) => v != null ? (v * 100).toFixed(1) + '%' : '?';
    const pp = (v) => v != null ? (v > 0 ? '+' : '') + (v * 100).toFixed(2) + 'pp' : '?';

    function cerClass(cer) {
        if (cer < 0.03) return 'cer-green';
        if (cer < 0.05) return 'cer-yellow';
        if (cer < 0.15) return 'cer-orange';
        return 'cer-red';
    }

    function confColor(count, maxCount) {
        const t = Math.min(count / maxCount, 1);
        const r = Math.round(255 - t * 50);
        const g = Math.round(255 - t * 180);
        const b = Math.round(255 - t * 180);
        return `rgb(${r},${g},${b})`;
    }

    // --- Tabs ---
    function initTabs() {
        $$('.diag-tab').forEach((btn) => {
            btn.addEventListener('click', () => {
                $$('.diag-tab').forEach((b) => b.classList.remove('active'));
                $$('.diag-panel').forEach((p) => p.classList.remove('active'));
                btn.classList.add('active');
                const panel = $('#panel-' + btn.dataset.tab);
                if (panel) panel.classList.add('active');
            });
        });
    }

    // --- Metrics ---
    function renderMetrics(data) {
        const s = data.summary.post_normfix;
        const el = $('#metrics');
        const cards = [
            { value: s.total_documents, label: 'Dokumente', cls: '' },
            { value: pct(s.avg_cer), label: 'Mean CER', cls: s.avg_cer < 0.05 ? 'good' : s.avg_cer < 0.10 ? 'warn' : 'bad' },
            { value: pct(s.median_cer), label: 'Median CER', cls: s.median_cer < 0.05 ? 'good' : 'warn' },
            { value: pp(data.summary.normalization_effect.mean_cer_delta), label: 'Norm-Fix Delta', cls: 'good' },
        ];
        el.innerHTML = cards.map((c) =>
            `<div class="metric-card${c.cls ? ' ' + c.cls : ''}">
                <div class="metric-value">${c.value}</div>
                <div class="metric-label">${c.label}</div>
            </div>`
        ).join('');
    }

    // --- CER Heatmap ---
    function renderHeatmap(data) {
        const container = $('#heatmap');
        const sortEl = $('#heatmap-sort');
        const docs = Object.entries(data.per_doc).map(([id, d]) => ({ id, ...d }));

        const sortOptions = [
            { key: 'cer', label: 'CER' },
            { key: 'type', label: 'Typ' },
            { key: 'lang', label: 'Sprache' },
        ];

        let currentSort = 'cer';

        function render() {
            const sorted = [...docs].sort((a, b) => {
                if (currentSort === 'cer') return b.cer - a.cer;
                if (currentSort === 'type') return (a.metadata.type || '').localeCompare(b.metadata.type || '') || a.cer - b.cer;
                return (a.metadata.language || '').localeCompare(b.metadata.language || '') || a.cer - b.cer;
            });

            container.innerHTML = sorted.map((d) =>
                `<div class="heatmap-cell ${cerClass(d.cer)}" title="Doc ${d.id}: CER ${pct(d.cer)}">
                    <div class="doc-id">${d.id}</div>
                    <div class="cer-val">${pct(d.cer)}</div>
                    <div class="meta">${d.metadata.type || '?'} / ${d.metadata.language || '?'}</div>
                </div>`
            ).join('');
        }

        sortEl.innerHTML = sortOptions.map((o) =>
            `<button class="sort-btn${o.key === currentSort ? ' active' : ''}" data-sort="${o.key}">${o.label}</button>`
        ).join('');

        sortEl.addEventListener('click', (e) => {
            const btn = e.target.closest('.sort-btn');
            if (!btn) return;
            currentSort = btn.dataset.sort;
            $$('.sort-btn', sortEl).forEach((b) => b.classList.toggle('active', b.dataset.sort === currentSort));
            render();
        });

        render();
    }

    // --- Konfusionsmatrix ---
    function renderConfusion(data) {
        const cm = data.confusion_matrix;
        const grid = $('#confusion-grid');
        const summary = $('#conf-summary');

        summary.textContent = `${cm.totals.substitutions} Substitutionen, ${cm.totals.insertions} Insertions, ${cm.totals.deletions} Deletions`;

        const top30 = cm.substitutions.slice(0, 30);
        const maxCount = top30.length > 0 ? top30[0].count : 1;

        grid.innerHTML = top30.map((s) =>
            `<div class="conf-cell" style="background:${confColor(s.count, maxCount)}"
                  title="${s.ref_name} -> ${s.hyp_name} (${s.ref_codepoint} -> ${s.hyp_codepoint})">
                <div class="pair">${escChar(s.ref_char)} &rarr; ${escChar(s.hyp_char)}</div>
                <div class="count">${s.count}x</div>
                <div class="count">${s.ref_codepoint}</div>
            </div>`
        ).join('');

        // Insertions / Deletions
        const renderList = (items, el) => {
            const top = items.slice(0, 20);
            el.innerHTML = top.map((it) =>
                `<div style="display:flex;gap:8px;font-family:'JetBrains Mono',monospace;font-size:.85rem;padding:2px 0">
                    <span style="width:40px;text-align:right;font-weight:600">${it.count}x</span>
                    <span>${escChar(it.char)}</span>
                    <span style="color:#888">${it.codepoint} ${it.name}</span>
                </div>`
            ).join('');
        };
        renderList(cm.insertions, $('#insertions-list'));
        renderList(cm.deletions, $('#deletions-list'));
    }

    function escChar(c) {
        if (!c) return '\u2205';
        if (c === ' ') return '\u2423';
        if (c === '\n') return '\u21b5';
        if (c === '\t') return '\u21e5';
        const cp = c.codePointAt(0);
        if (cp < 0x20 || (cp >= 0x7f && cp <= 0x9f)) return `\\u${cp.toString(16).padStart(4, '0')}`;
        return c.replace(/</g, '&lt;').replace(/>/g, '&gt;');
    }

    // --- Baseline-Vergleich ---
    function renderBaseline(data) {
        const items = data.baseline_comparison;
        const chart = $('#baseline-chart');
        const summary = $('#baseline-summary');

        const meanDelta = items.reduce((s, i) => s + (i.cer_delta || 0), 0) / items.length;
        summary.textContent = `Mittleres Delta: ${pp(meanDelta)} (negativ = Verbesserung durch symmetrische Normalisierung)`;

        const maxCer = Math.max(...items.map((i) => Math.max(i.cer_before || 0, i.cer_after || 0)));
        const scale = maxCer > 0 ? 100 / maxCer : 100;

        const sorted = [...items].sort((a, b) => (a.cer_delta || 0) - (b.cer_delta || 0));

        chart.innerHTML = sorted.map((i) => {
            const bw = (i.cer_before || 0) * scale;
            const aw = (i.cer_after || 0) * scale;
            return `<div class="bar-row">
                <div class="bar-label">${i.doc_id}</div>
                <div class="bar-track">
                    <div class="bar-fill before" style="width:${bw}%"></div>
                    <div class="bar-fill after" style="width:${aw}%"></div>
                </div>
                <div class="bar-value">${pct(i.cer_before)} &rarr; ${pct(i.cer_after)}</div>
            </div>`;
        }).join('');
    }

    // --- Pipeline-Effekt Dot-Plot ---
    function renderPipelineEffect(data) {
        const canvas = $('#dot-canvas');
        const ctx = canvas.getContext('2d');
        const items = data.pipeline_effect.filter((e) => e.ocr_baseline_cer != null);

        const summaryEl = $('#pipeline-summary');
        const improved = items.filter((e) => e.improved).length;
        const worsened = items.filter((e) => e.improved === false).length;
        summaryEl.textContent = `${improved} verbessert, ${worsened} verschlechtert (Punkte unter Diagonale = Pipeline hilft)`;

        const dpr = window.devicePixelRatio || 1;
        const rect = canvas.parentElement.getBoundingClientRect();
        canvas.width = rect.width * dpr;
        canvas.height = rect.height * dpr;
        canvas.style.width = rect.width + 'px';
        canvas.style.height = rect.height + 'px';
        ctx.scale(dpr, dpr);

        const w = rect.width;
        const h = rect.height;
        const pad = { top: 20, right: 20, bottom: 40, left: 55 };
        const pw = w - pad.left - pad.right;
        const ph = h - pad.top - pad.bottom;

        const maxVal = Math.max(0.40, ...items.map((e) => Math.max(e.ocr_baseline_cer, e.end_to_end_cer)));

        const xScale = (v) => pad.left + (v / maxVal) * pw;
        const yScale = (v) => pad.top + ph - (v / maxVal) * ph;

        // Grid
        ctx.strokeStyle = '#e0e0e0';
        ctx.lineWidth = 0.5;
        for (let t = 0; t <= maxVal; t += 0.05) {
            ctx.beginPath();
            ctx.moveTo(pad.left, yScale(t));
            ctx.lineTo(w - pad.right, yScale(t));
            ctx.stroke();
            ctx.beginPath();
            ctx.moveTo(xScale(t), pad.top);
            ctx.lineTo(xScale(t), h - pad.bottom);
            ctx.stroke();
        }

        // Diagonal (y = x)
        ctx.strokeStyle = '#bbb';
        ctx.lineWidth = 1;
        ctx.setLineDash([5, 3]);
        ctx.beginPath();
        ctx.moveTo(xScale(0), yScale(0));
        ctx.lineTo(xScale(maxVal), yScale(maxVal));
        ctx.stroke();
        ctx.setLineDash([]);

        // Axis labels
        ctx.fillStyle = '#666';
        ctx.font = '12px Jost, sans-serif';
        ctx.textAlign = 'center';
        for (let t = 0; t <= maxVal; t += 0.10) {
            ctx.fillText((t * 100).toFixed(0) + '%', xScale(t), h - pad.bottom + 16);
        }
        ctx.textAlign = 'right';
        for (let t = 0; t <= maxVal; t += 0.10) {
            ctx.fillText((t * 100).toFixed(0) + '%', pad.left - 6, yScale(t) + 4);
        }
        ctx.textAlign = 'center';
        ctx.font = '13px Jost, sans-serif';
        ctx.fillText('OCR-Baseline CER', w / 2, h - 2);
        ctx.save();
        ctx.translate(14, h / 2);
        ctx.rotate(-Math.PI / 2);
        ctx.fillText('End-to-End CER', 0, 0);
        ctx.restore();

        // Dots
        items.forEach((e) => {
            const x = xScale(e.ocr_baseline_cer);
            const y = yScale(e.end_to_end_cer);
            const improved = e.end_to_end_cer < e.ocr_baseline_cer;
            ctx.beginPath();
            ctx.arc(x, y, 6, 0, Math.PI * 2);
            ctx.fillStyle = improved ? '#66bb6a' : '#ef5350';
            ctx.fill();
            ctx.strokeStyle = '#fff';
            ctx.lineWidth = 1.5;
            ctx.stroke();

            ctx.fillStyle = '#333';
            ctx.font = '10px JetBrains Mono, monospace';
            ctx.textAlign = 'center';
            ctx.fillText(e.doc_id, x, y - 10);
        });

        // Legend
        const legend = $('#dot-legend');
        legend.innerHTML = `
            <div class="dot-legend-item"><div class="dot-legend-color" style="background:#66bb6a"></div> Pipeline verbessert</div>
            <div class="dot-legend-item"><div class="dot-legend-color" style="background:#ef5350"></div> Pipeline verschlechtert</div>
            <div class="dot-legend-item"><div class="dot-legend-color" style="background:#bbb;width:20px;height:2px;border-radius:0"></div> Diagonale (kein Effekt)</div>
        `;
    }

    // --- Outlier Cards ---
    function renderOutliers(data) {
        const container = $('#outlier-cards');
        const outliers = data.outlier_diagnosis;

        const badgeClass = { source_ocr_quality: 'badge-source', layout_alignment: 'badge-layout', mixed: 'badge-mixed' };
        const badgeLabel = { source_ocr_quality: 'OCR-Qualitaet', layout_alignment: 'Layout', mixed: 'Mixed', ocr_hallucination: 'Halluzination' };

        container.innerHTML = Object.entries(outliers).map(([id, o]) => {
            const cats = Object.entries(o.error_categories || {})
                .filter(([, v]) => v.count > 0)
                .sort((a, b) => b[1].cer_contribution - a[1].cer_contribution);

            return `<div class="outlier-card">
                <div class="outlier-header">
                    <div class="outlier-title">Doc ${id} (${o.metadata.type || '?'} / ${o.metadata.language || '?'})</div>
                    <span class="outlier-badge ${badgeClass[o.primary_cause] || 'badge-mixed'}">${badgeLabel[o.primary_cause] || o.primary_cause}</span>
                </div>
                <div class="outlier-metrics">
                    <div class="outlier-metric"><div class="val">${pct(o.cer_end_to_end)}</div><div class="lbl">End-to-End CER</div></div>
                    <div class="outlier-metric"><div class="val">${o.ocr_baseline_cer != null ? pct(o.ocr_baseline_cer) : '?'}</div><div class="lbl">OCR-Baseline CER</div></div>
                    <div class="outlier-metric"><div class="val">${o.pipeline_delta != null ? pp(o.pipeline_delta) : '?'}</div><div class="lbl">Pipeline-Delta</div></div>
                </div>
                <p style="margin:.8rem 0 .5rem;font-size:.9rem">${o.explanation}</p>
                <details><summary style="cursor:pointer;font-size:.85rem">Fehlerkategorien</summary>
                    <table style="width:100%;font-size:.8rem;margin-top:.5rem;border-collapse:collapse">
                        <tr style="background:#f5f5f5"><th style="text-align:left;padding:4px">Kategorie</th><th>Anzahl</th><th>CER-Beitrag</th></tr>
                        ${cats.map(([cat, v]) => `<tr><td style="padding:4px">${cat}</td><td style="text-align:center">${v.count}</td><td style="text-align:center">${pct(v.cer_contribution)}</td></tr>`).join('')}
                    </table>
                </details>
            </div>`;
        }).join('');
    }

    // ===================================================================
    // TEI-Qualitaet Tab (Lane 1)
    // ===================================================================
    const TEI_DATA_URL = 'data/diagnostik_tei.json';

    function renderTeiMetrics(data) {
        const s = data.summary;
        const el = $('#tei-metrics');
        if (!el) return;
        const cards = [
            { value: s.total, label: 'Dokumente', cls: '' },
            { value: s.valid, label: 'Valid', cls: s.valid === s.total ? 'good' : 'warn' },
            { value: s.invalid, label: 'Invalid', cls: s.invalid === 0 ? 'good' : 'bad' },
            { value: s.valid_pct + '%', label: 'Valid Rate', cls: s.valid_pct === 100 ? 'good' : 'warn' },
            { value: s.with_warnings, label: 'Mit Warnings', cls: s.with_warnings > 0 ? 'warn' : 'good' },
        ];
        el.innerHTML = cards.map((c) =>
            `<div class="metric-card${c.cls ? ' ' + c.cls : ''}"><div class="metric-value">${c.value}</div><div class="metric-label">${c.label}</div></div>`
        ).join('');
    }

    function renderTeiErrorTable(data) {
        const tbody = document.querySelector('#tei-error-table tbody');
        if (!tbody) return;
        const rows = (data.error_frequency_before_fix || []).map((e) => {
            const statusClass = e.fix_status === 'gefixt' ? 'badge-gefixt'
                : e.fix_status === 'offen' ? 'badge-offen' : 'badge-ignoriert';
            return `<tr>
                <td><code>${e.type}</code></td>
                <td class="num">${e.count}</td>
                <td><span class="badge ${statusClass}">${e.fix_status}</span></td>
                <td>${e.description}</td>
            </tr>`;
        });
        tbody.innerHTML = rows.join('');
    }

    function renderTeiFixHistory(data) {
        const container = $('#tei-fix-history');
        if (!container || !data.fix_history) return;
        const html = data.fix_history.map((fix) => {
            const beforePct = Math.round(fix.docs_before / data.summary.total * 100);
            const afterPct = Math.round(fix.docs_after / data.summary.total * 100);
            return `<div class="outlier-card">
                <div class="outlier-header">
                    <span class="outlier-title">${fix.id}: ${fix.type}</span>
                    <span class="outlier-badge badge-gefixt">${fix.docs_fixed} Docs gefixt</span>
                </div>
                <p style="font-size:.9rem;margin:.5rem 0">${fix.description}</p>
                <div class="fix-bar">
                    <span class="fix-bar-label">Vorher</span>
                    <div class="fix-bar-track">
                        <div class="fix-bar-fill before" style="width:${beforePct}%"></div>
                    </div>
                    <span class="fix-bar-value">${fix.docs_before}/${data.summary.total} valid</span>
                </div>
                <div class="fix-bar">
                    <span class="fix-bar-label">Nachher</span>
                    <div class="fix-bar-track">
                        <div class="fix-bar-fill after" style="width:${afterPct}%"></div>
                    </div>
                    <span class="fix-bar-value">${fix.docs_after}/${data.summary.total} valid</span>
                </div>
                <details style="margin-top:.5rem"><summary style="cursor:pointer;font-size:.85rem">Locations</summary>
                    <ul style="font-size:.8rem;font-family:'JetBrains Mono',monospace">${fix.locations.map((l) => `<li>${l}</li>`).join('')}</ul>
                </details>
            </div>`;
        });
        container.innerHTML = html.join('');
    }

    function renderTeiWarningTable(data) {
        const tbody = document.querySelector('#tei-warning-table tbody');
        if (!tbody) return;
        const rows = (data.warning_frequency || []).map((w) =>
            `<tr><td><code>${w.rule}</code></td><td class="num">${w.count}</td><td>${w.description}</td></tr>`
        );
        tbody.innerHTML = rows.join('');
    }

    function renderTeiRefTable(data) {
        const ref = data.reference_tei_validation;
        if (!ref) return;

        const metricsEl = $('#tei-ref-metrics');
        if (metricsEl) {
            metricsEl.innerHTML = [
                { value: ref.total, label: 'Referenz-TEIs', cls: '' },
                { value: ref.valid, label: 'Valid', cls: 'good' },
                { value: ref.invalid, label: 'Invalid', cls: ref.invalid > 0 ? 'warn' : 'good' },
            ].map((c) =>
                `<div class="metric-card${c.cls ? ' ' + c.cls : ''}"><div class="metric-value">${c.value}</div><div class="metric-label">${c.label}</div></div>`
            ).join('');
        }

        const tbody = document.querySelector('#tei-ref-table tbody');
        if (!tbody) return;
        const docs = ref.docs || {};
        const rows = Object.entries(docs)
            .sort(([a], [b]) => parseInt(a) - parseInt(b))
            .map(([id, r]) => {
                const status = r.valid ? 'valid' : 'invalid';
                const badge = r.valid ? 'badge-valid' : 'badge-invalid';
                const details = (r.errors || []).slice(0, 3)
                    .map((e) => `<div style="font-size:.8rem;font-family:'JetBrains Mono',monospace;color:#b71c1c">L${e.line}: ${e.message}</div>`)
                    .join('');
                return `<tr>
                    <td>${id}</td>
                    <td><span class="badge ${badge}">${status.toUpperCase()}</span></td>
                    <td class="num">${r.error_count || 0}</td>
                    <td>${details || '-'}</td>
                </tr>`;
            });
        tbody.innerHTML = rows.join('');
    }

    function renderTeiDocTable(data) {
        const tbody = document.querySelector('#tei-doc-table tbody');
        if (!tbody) return;
        const docs = data.per_doc || {};

        let allRows = Object.entries(docs)
            .sort(([a], [b]) => parseInt(a) - parseInt(b))
            .map(([id, d]) => ({
                id: parseInt(id),
                idStr: id,
                valid: d.valid,
                errors: (d.schema_errors || 0) + (d.project_errors || 0),
                warningCount: d.warning_count || 0,
                warnings: (d.warnings || []).join(', ') || '-',
            }));

        const searchEl = $('#tei-filter-search');
        const statusEl = $('#tei-filter-status');

        const renderRows = () => {
            const q = (searchEl ? searchEl.value : '').trim();
            const sf = statusEl ? statusEl.value : '';
            const filtered = allRows.filter((r) => {
                if (q && !r.idStr.includes(q)) return false;
                if (sf === 'valid' && !r.valid) return false;
                if (sf === 'invalid' && r.valid) return false;
                if (sf === 'warnings' && r.warningCount === 0) return false;
                return true;
            });
            tbody.innerHTML = filtered.map((r) => {
                const badge = r.valid ? 'badge-valid' : 'badge-invalid';
                const status = r.valid ? 'VALID' : 'INVALID';
                return `<tr>
                    <td><a href="viewer.html?doc=${r.idStr}" style="text-decoration:none;color:inherit;font-weight:600">${r.idStr}</a></td>
                    <td><span class="badge ${badge}">${status}</span></td>
                    <td class="num">${r.errors}</td>
                    <td class="num">${r.warningCount}</td>
                    <td><code style="font-size:.8rem">${r.warnings}</code></td>
                </tr>`;
            }).join('');
        };

        if (searchEl) searchEl.addEventListener('input', renderRows);
        if (statusEl) statusEl.addEventListener('change', renderRows);

        // Sortable headers
        $$('#tei-doc-table th.sortable').forEach((th) => {
            th.addEventListener('click', () => {
                const key = th.dataset.sort;
                const asc = th.classList.toggle('asc');
                allRows.sort((a, b) => {
                    const va = key === 'status' ? (a.valid ? 1 : 0) : a[key];
                    const vb = key === 'status' ? (b.valid ? 1 : 0) : b[key];
                    return asc ? va - vb : vb - va;
                });
                renderRows();
            });
        });

        renderRows();
    }

    async function initTeiQuality() {
        try {
            const resp = await fetch(TEI_DATA_URL);
            if (!resp.ok) { console.warn('TEI diagnostik data not available'); return; }
            const data = await resp.json();
            renderTeiMetrics(data);
            renderTeiErrorTable(data);
            renderTeiFixHistory(data);
            renderTeiWarningTable(data);
            renderTeiRefTable(data);
            renderTeiDocTable(data);
        } catch (err) {
            console.warn('TEI quality tab: ' + err.message);
        }
    }

    // --- Init ---
    async function init() {
        try {
            const resp = await fetch(DATA_URL);
            if (!resp.ok) throw new Error('HTTP ' + resp.status);
            const data = await resp.json();

            $('#loading').classList.add('hidden');
            $('#app').classList.remove('hidden');

            initTabs();
            renderMetrics(data);
            renderHeatmap(data);
            renderConfusion(data);
            renderBaseline(data);
            renderPipelineEffect(data);
            renderOutliers(data);

            // TEI Quality (independent data source)
            initTeiQuality();
        } catch (err) {
            $('#loading').textContent = 'Fehler beim Laden: ' + err.message;
            console.error(err);
        }
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
