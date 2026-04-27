/**
 * CER-Werkbank Dashboard
 * Namespace: ZBZ.CerDashboard
 * Konsumiert: docs/data/cer_statistics.json (Fallback: cer_statistics.mock.json)
 * Plot-Strategie: vanilla SVG, kein externes Lib.
 * Schema-Quelle: CLAUDES-WORKING-SESSION.md Forschungsplan v2 §6 + C3-Wireframe
 */
(function () {
    'use strict';

    const NS = 'http://www.w3.org/2000/svg';
    const STRATA_ORDER = ['fra', 'deu', 'ita'];
    const LANG_LABEL = { fra: 'Franzoesisch', deu: 'Deutsch', ita: 'Italienisch' };
    const LAYOUT_ORDER = ['A', 'B', 'C', 'D'];
    const ERR_LABEL = {
        diacritics: 'Diakritik', substitution: 'Substitution', punctuation: 'Interpunktion',
        whitespace: 'Whitespace', deletion: 'Loeschung', insertion: 'Einfuegung', case: 'Gross/Klein'
    };
    const ERR_COLOR_TOKENS = [
        '--h-accent-teal', '--h-accent-violet', '--h-accent-blue',
        '--h-accent-amber', '--h-warning', '--h-error', '--h-neutral'
    ];

    const CD = {};

    // ---- Helpers ----
    const $ = (s, c) => (c || document).querySelector(s);
    const $$ = (s, c) => Array.prototype.slice.call((c || document).querySelectorAll(s));
    const fmtPct = (v, d) => (v == null || isNaN(v)) ? '–' : (v * 100).toFixed(d == null ? 2 : d) + '%';
    const fmtCI = (lo, hi, d) => `[${fmtPct(lo, d)}, ${fmtPct(hi, d)}]`;
    const fmtNum = (v) => v == null ? '–' : (typeof v === 'number' ? v.toLocaleString('de-CH') : String(v));
    const esc = (s) => String(s == null ? '' : s).replace(/[&<>"']/g, m => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[m]));

    function svg(w, h) {
        const el = document.createElementNS(NS, 'svg');
        el.setAttribute('viewBox', `0 0 ${w} ${h}`);
        el.setAttribute('preserveAspectRatio', 'xMidYMid meet');
        return el;
    }
    function el(tag, attrs, text) {
        const e = document.createElementNS(NS, tag);
        if (attrs) for (const k in attrs) e.setAttribute(k, attrs[k]);
        if (text != null) e.textContent = text;
        return e;
    }
    function clear(node) { while (node.firstChild) node.removeChild(node.firstChild); }

    /**
     * CI-Whisker-Helper: vertikaler Stem mit zwei Caps + Mittel-Punkt.
     * Erzwingt CIs ueberall, wo ein Punktschaetzer sichtbar ist.
     */
    function drawCIBar(parent, xLo, xMid, xHi, y, capH) {
        const cap = capH || 6;
        parent.appendChild(el('line', { x1: xLo, x2: xHi, y1: y, y2: y, class: 'cer-svg-ci-line' }));
        parent.appendChild(el('line', { x1: xLo, x2: xLo, y1: y - cap, y2: y + cap, class: 'cer-svg-ci-cap' }));
        parent.appendChild(el('line', { x1: xHi, x2: xHi, y1: y - cap, y2: y + cap, class: 'cer-svg-ci-cap' }));
        parent.appendChild(el('circle', { cx: xMid, cy: y, r: 4, class: 'cer-svg-ci-point' }));
    }

    function xScale(domain, range) {
        const [d0, d1] = domain, [r0, r1] = range;
        return v => r0 + (v - d0) / (d1 - d0) * (r1 - r0);
    }

    function ticks(min, max, n) {
        const step = (max - min) / n;
        const out = [];
        for (let i = 0; i <= n; i++) out.push(min + i * step);
        return out;
    }

    // ---- Loader (echt zuerst, Mock als Fallback) ----
    CD.load = async function () {
        const isInfra = window.location.pathname.indexOf('/infrastruktur/') > -1;
        const base = isInfra ? '../data/' : 'data/';
        const candidates = [base + 'cer_statistics.json', base + 'cer_statistics.mock.json'];
        for (const url of candidates) {
            try {
                const r = await fetch(url);
                if (r.ok) {
                    const data = await r.json();
                    return { data: CD.normalize(data), url };
                }
            } catch (e) { /* try next */ }
        }
        throw new Error('Keine CER-Statistik gefunden (weder cer_statistics.json noch .mock.json)');
    };

    /**
     * Normalisiert C2-Schema v0.3 in interne Render-Shape.
     * Adapter, kein Rewrite (siehe CLAUDES-WORKING-SESSION C1-Vorgabe).
     * Idempotent: bereits normalisierte Daten werden durchgereicht.
     */
    CD.normalize = function (raw) {
        const n = Object.assign({}, raw);

        // corpus.excluded (array of {doc_id, reason}) -> exclusion_reasons map
        if (n.corpus && Array.isArray(n.corpus.excluded) && !n.corpus.exclusion_reasons) {
            const reasons = {};
            n.corpus.excluded.forEach(e => { reasons[e.doc_id] = e.reason; });
            n.corpus = Object.assign({}, n.corpus, { exclusion_reasons: reasons });
        }

        // multi_norm.results -> flat map
        if (n.multi_norm && n.multi_norm.results && !n.multi_norm.raw) {
            n.multi_norm = Object.assign({}, n.multi_norm.results);
        }

        // error_categories: v0.3 -> {count, share}-Objekte
        if (n.error_categories && n.error_categories.absolute_counts) {
            const ac = n.error_categories.absolute_counts;
            const total = Object.values(ac).reduce((a, b) => a + b, 0) || 1;
            const ec = {};
            Object.keys(ac).forEach(k => { ec[k] = { count: ac[k], share: ac[k] / total }; });
            n.error_categories = ec;
        }

        // domain_metrics.diacritic_preservation_rate.by_language: count -> freq
        if (n.domain_metrics && n.domain_metrics.diacritic_preservation_rate) {
            const dpr = n.domain_metrics.diacritic_preservation_rate;
            if (dpr.by_language) {
                const fixed = {};
                Object.keys(dpr.by_language).forEach(k => {
                    const o = dpr.by_language[k];
                    fixed[k] = Object.assign({}, o);
                    if (o.expected_count != null && o.expected_freq == null && o.observed_count != null) {
                        const total = o.observed_count > 0 ? o.observed_count / Math.max(o.rate || 1, 1e-9) : 0;
                        // fallback display: just keep counts visible
                        fixed[k].expected_freq = o.expected_count > 0 && total > 0 ? o.expected_count / total : null;
                        fixed[k].observed_freq = o.observed_count > 0 && total > 0 ? o.observed_count / total : null;
                    }
                });
                n.domain_metrics = Object.assign({}, n.domain_metrics, {
                    diacritic_preservation_rate: Object.assign({}, dpr, { by_language: fixed })
                });
            }
        }

        // overall.ocr_only.status === 'deferred' -> render placeholder
        // (kein Reshape, nur Erkennung; renderOverall pruefte bereits status implizit)

        // paired_test.p_bootstrap_two_sided -> p_bootstrap
        if (n.paired_test && n.paired_test.p_bootstrap_two_sided != null && n.paired_test.p_bootstrap == null) {
            n.paired_test = Object.assign({}, n.paired_test, { p_bootstrap: n.paired_test.p_bootstrap_two_sided });
        }
        if (n.paired_test && !n.paired_test.interpretation) {
            const pt = n.paired_test;
            n.paired_test = Object.assign({}, pt, {
                interpretation: `Paired Bootstrap: ${pt.n_better}/${pt.n_better + pt.n_worse + pt.n_unchanged} Docs verbessert, p=${(pt.p_bootstrap || 0).toFixed(3)}.`
            });
        }

        // proxies.corpus_estimate: total_ci95 als primaer, sonst inner
        if (n.proxies && n.proxies.corpus_estimate) {
            const ce = n.proxies.corpus_estimate;
            if (!ce.estimated_mean_ci95) {
                ce.estimated_mean_ci95 = ce.estimated_mean_total_ci95 || ce.estimated_mean_inner_ci95 || null;
            }
        }

        // proxies.validation_n19.per_proxy -> validation_n19 flat (composite eingeschoben)
        if (n.proxies && n.proxies.validation_n19 && n.proxies.validation_n19.per_proxy) {
            const v = n.proxies.validation_n19;
            const flat = Object.assign({}, v.per_proxy);
            flat.composite = v.composite ? Object.assign({
                r2: v.composite.loocv_r2 != null ? v.composite.loocv_r2 : v.composite.in_sample_r2
            }, v.composite) : null;
            n.proxies = Object.assign({}, n.proxies, { validation_n19: flat });
        }

        // selection_bias.tests array -> nichts zu tun (renderLimitations nutzt nur .interpretation)

        // ===== Reales C1-Output (cer_statistics.py) — zusaetzliche Differenzen =====

        // strata.<group>.<key>.n_docs -> n
        if (n.strata) {
            const fixedStrata = {};
            Object.keys(n.strata).forEach(group => {
                const grp = n.strata[group];
                const fixedGrp = {};
                Object.keys(grp).forEach(key => {
                    const o = Object.assign({}, grp[key]);
                    if (o.n_docs != null && o.n == null) o.n = o.n_docs;
                    fixedGrp[key] = o;
                });
                fixedStrata[group] = fixedGrp;
            });
            n.strata = fixedStrata;
        }

        // overall.end_to_end.n_docs -> n
        if (n.overall) {
            ['end_to_end', 'ocr_only', 'end_to_end_all'].forEach(k => {
                if (n.overall[k] && n.overall[k].n_docs != null && n.overall[k].n == null) {
                    n.overall[k] = Object.assign({}, n.overall[k], { n: n.overall[k].n_docs });
                }
            });
        }

        // per_doc[].cer -> cer_end_to_end
        if (Array.isArray(n.per_doc)) {
            n.per_doc = n.per_doc.map(d => {
                const o = Object.assign({}, d);
                if (o.cer != null && o.cer_end_to_end == null) o.cer_end_to_end = o.cer;
                if (o.cer_end_to_end == null && o.cer_by_regime && o.cer_by_regime.nfc_hyphen_case != null) {
                    o.cer_end_to_end = o.cer_by_regime.nfc_hyphen_case;
                }
                return o;
            });
        }

        // comparison_lit[].language -> lang
        if (Array.isArray(n.comparison_lit)) {
            n.comparison_lit = n.comparison_lit.map(c => {
                const o = Object.assign({}, c);
                if (o.language && !o.lang) o.lang = o.language;
                if (o.comparable === true) o.comparable = 'true';
                if (o.comparable === false) o.comparable = 'false';
                return o;
            });
        }

        // domain_metrics.diacritic_preservation_rate flat ohne by_language
        // Echte Shape: {fra: {n_docs, mean_rate, median_rate, min_rate}, deu: {...}}
        // Erwartete Shape: {by_language: {fra: {expected_freq, observed_freq, rate, rate_ci95}}}
        if (n.domain_metrics && n.domain_metrics.diacritic_preservation_rate) {
            const dpr = n.domain_metrics.diacritic_preservation_rate;
            if (!dpr.by_language) {
                const isFlat = Object.keys(dpr).some(k => dpr[k] && (dpr[k].mean_rate != null || dpr[k].n_docs != null));
                if (isFlat) {
                    const fixed = {};
                    Object.keys(dpr).forEach(k => {
                        const o = dpr[k];
                        if (o && typeof o === 'object' && (o.mean_rate != null || o.median_rate != null)) {
                            fixed[k] = {
                                rate: o.mean_rate != null ? o.mean_rate : o.median_rate,
                                rate_ci95: o.min_rate != null && o.mean_rate != null ? [o.min_rate, 1] : null,
                                expected_freq: null,
                                observed_freq: null,
                                _n_docs: o.n_docs
                            };
                        }
                    });
                    n.domain_metrics = {
                        diacritic_preservation_rate: {
                            by_language: fixed,
                            method_ref: dpr.method_ref || 'Per-Doc-Mean der Diakritik-Erhaltungsrate (C1-Run, n je Sprache).'
                        }
                    };
                }
            }
        }

        // proxies.status === 'open' (whole section deferred)
        // -> kein Reshape, renderProxies erkennt das

        // error_categories: {} empty -> renderErrCat erkennt das

        return n;
    };

    // ---- Sektionen-Renderer ----
    CD.renderMetaBar = function (meta, corpus, sourceUrl) {
        const bar = $('#cer-meta-bar');
        if (!bar) return;
        const isMock = sourceUrl.indexOf('.mock.') > -1;
        bar.innerHTML = [
            `<span><strong>n</strong> ${corpus.n_evaluated}/${corpus.n_with_ground_truth} (Korpus ${corpus.n_total})</span>`,
            `<span><strong>tool</strong> ${esc(meta.tool_version)}</span>`,
            `<span><strong>git</strong> ${esc(meta.git_sha || '–')}</span>`,
            `<span><strong>seed</strong> ${meta.seed}</span>`,
            `<span><strong>B</strong> ${fmtNum(meta.bootstrap_n)}</span>`,
            `<span><strong>generiert</strong> ${esc((meta.generated_at || '').slice(0, 10))}</span>`,
            isMock ? `<span style="color:var(--h-warning)"><strong>Quelle</strong> MOCK</span>` : ''
        ].filter(Boolean).join('');
        if (isMock) {
            const banner = $('#cer-mock-banner');
            if (banner) banner.hidden = false;
        }
    };

    CD.renderLimitations = function (data) {
        const c = data.corpus || {}, sb = data.selection_bias || {}, st = data.stability || {}, dr = data.drift_check || null;
        const excluded = c.n_excluded != null ? c.n_excluded : 0;
        $('#cer-lim-sample').textContent =
            `Direkter CER auf n=${c.n_evaluated} von ${c.n_with_ground_truth} Referenz-Docs` +
            (excluded > 0 ? ` (${excluded} wegen Scope-Mismatch ausgeschlossen)` : '') + '. ' +
            `Korpus umfasst n=${c.n_total} Docs — Aussagen darueber siehe Proxy-Schaetzung unten.`;
        const biasNotComparable = sb.comparable_overall === false;
        const biasPrefix = biasNotComparable ? '<strong style="color:var(--h-error)">NICHT vergleichbar:</strong> ' : '';
        $('#cer-lim-bias').innerHTML = biasPrefix + esc(sb.interpretation || '–');
        if (st.status === 'open') {
            $('#cer-lim-stability').innerHTML = `<strong>Nicht gemessen.</strong> ${esc(st.reason || '')}`;
        } else if (st.status === 'measured') {
            $('#cer-lim-stability').textContent = `Stabilitaet ueber Re-Runs gemessen (siehe Sektion unten).`;
        } else {
            $('#cer-lim-stability').textContent = '–';
        }
        $('#cer-lim-likeforlike').textContent =
            'Forschungsvergleich nur eingeschraenkt direkt: Sprachen, Korpora, Eval-Protokolle differieren. Vergleichbarkeit pro Quelle visuell ausgewiesen.';

        // Drift-Check anhaengen wenn vorhanden
        if (dr && dr.status) {
            const driftCard = $('#cer-lim-stability').parentElement;
            if (driftCard && !$('#cer-drift-info')) {
                const dInfo = document.createElement('p');
                dInfo.id = 'cer-drift-info';
                dInfo.style.marginTop = '0.5rem';
                dInfo.style.fontSize = 'var(--h-xs)';
                dInfo.style.color = 'var(--h-text-muted)';
                const driftLabel = dr.status === 'minor' ? 'minor' : dr.status === 'stale' ? '<strong style="color:var(--h-error)">stale</strong>' : esc(dr.status);
                dInfo.innerHTML = `<em>Drift-Check ggue. Snapshot ${esc((dr.snapshot_generated || '').slice(0, 10))}: ${driftLabel}, ${dr.n_docs_diverged || 0} Doc(s) > ${dr.threshold_pp || 5}pp Abweichung.</em>`;
                driftCard.appendChild(dInfo);
            }
        }

        const list = $('#cer-excluded-list');
        list.innerHTML = '';
        const reasons = c.exclusion_reasons || {};
        const ids = Object.keys(reasons);
        if (!ids.length) {
            list.innerHTML = '<li class="ed-hint">Keine Ausschluesse in dieser Iteration.</li>';
        } else {
            ids.forEach(id => {
                const li = document.createElement('li');
                li.innerHTML = `<strong>${esc(id)}</strong> ${esc(reasons[id])}`;
                list.appendChild(li);
            });
        }
    };

    CD.renderOverall = function (overall) {
        const buildPanel = (key, panelId) => {
            const o = overall[key];
            const panel = $('#' + panelId);
            clear(panel);
            if (!o) {
                panel.innerHTML = '<p class="ed-hint">Nicht verfuegbar.</p>';
                return;
            }
            if (o.status === 'deferred') {
                panel.innerHTML = `<div class="cer-stability-open"><strong>DEFERRED</strong> ${esc(o.reason || 'Nicht in dieser Iteration gemessen.')}</div>`;
                return;
            }
            const grid = document.createElement('div');
            grid.className = 'cer-overall-stats';
            grid.innerHTML = `
                <div class="cer-stat-block">
                    <div class="cer-stat-label">Mean CER (n=${o.n})</div>
                    <div class="cer-stat-value">${fmtPct(o.mean, 2)}</div>
                    <div class="cer-stat-ci">95% CI ${fmtCI(o.mean_ci95[0], o.mean_ci95[1], 2)}</div>
                </div>
                <div class="cer-stat-block">
                    <div class="cer-stat-label">Median CER</div>
                    <div class="cer-stat-value">${fmtPct(o.median, 2)}</div>
                    <div class="cer-stat-ci">95% CI ${fmtCI(o.median_ci95[0], o.median_ci95[1], 2)}</div>
                </div>
                <div class="cer-stat-block">
                    <div class="cer-stat-label">Spannweite</div>
                    <div class="cer-stat-value">${fmtPct(o.min, 2)} – ${fmtPct(o.max, 2)}</div>
                    <div class="cer-stat-ci">Q1=${fmtPct(o.q1, 2)} · Q3=${fmtPct(o.q3, 2)}</div>
                </div>`;
            panel.appendChild(grid);
            if (o.note) {
                const p = document.createElement('p');
                p.className = 'cer-method-tag';
                p.textContent = o.note;
                panel.appendChild(p);
            }
        };
        buildPanel('end_to_end', 'cer-overall-end-to-end');
        buildPanel('ocr_only', 'cer-overall-ocr-only');
        const m = overall.end_to_end || overall.ocr_only;
        $('#cer-overall-method').textContent = m ? `CI-Methode: ${m.ci_method}` : '';

        $$('.cer-overall-tab').forEach(btn => {
            btn.addEventListener('click', () => {
                $$('.cer-overall-tab').forEach(b => {
                    b.classList.toggle('active', b === btn);
                    b.setAttribute('aria-selected', b === btn ? 'true' : 'false');
                });
                $$('.cer-overall-panel').forEach(p => {
                    const targetId = btn.dataset.tab === 'end_to_end' ? 'cer-overall-end-to-end' : 'cer-overall-ocr-only';
                    p.classList.toggle('active', p.id === targetId);
                    p.hidden = p.id !== targetId;
                });
            });
        });
    };

    CD.renderHistogram = function (perDoc) {
        const wrap = $('#cer-plot-histogram');
        clear(wrap);
        const values = perDoc.map(d => d.cer_end_to_end).filter(v => v != null);
        if (!values.length) return;
        const maxV = Math.max(...values);
        const nBins = 10;
        const binW = maxV / nBins;
        const counts = new Array(nBins).fill(0);
        values.forEach(v => {
            const i = Math.min(nBins - 1, Math.floor(v / binW));
            counts[i]++;
        });
        const W = 720, H = 240, ml = 50, mr = 20, mt = 16, mb = 40;
        const innerW = W - ml - mr, innerH = H - mt - mb;
        const maxC = Math.max(...counts);
        const x = xScale([0, maxV], [ml, ml + innerW]);
        const yScale = c => mt + innerH - (c / maxC) * innerH;

        const s = svg(W, H);
        // Achsen
        s.appendChild(el('line', { x1: ml, x2: ml + innerW, y1: mt + innerH, y2: mt + innerH, class: 'cer-svg-axis' }));
        s.appendChild(el('line', { x1: ml, x2: ml, y1: mt, y2: mt + innerH, class: 'cer-svg-axis' }));
        // Y-Ticks
        for (let i = 0; i <= 4; i++) {
            const c = (maxC / 4) * i;
            const yy = yScale(c);
            s.appendChild(el('line', { x1: ml, x2: ml + innerW, y1: yy, y2: yy, class: 'cer-svg-grid' }));
            s.appendChild(el('text', { x: ml - 6, y: yy + 4, 'text-anchor': 'end', class: 'cer-svg-tick-text' }, Math.round(c).toString()));
        }
        // Bars
        counts.forEach((c, i) => {
            const x0 = x(i * binW), x1 = x((i + 1) * binW);
            const y = yScale(c);
            s.appendChild(el('rect', {
                x: x0 + 1, y: y, width: Math.max(1, x1 - x0 - 2), height: mt + innerH - y,
                class: 'cer-svg-bar'
            }));
        });
        // X-Ticks (CER-Werte)
        ticks(0, maxV, 5).forEach(v => {
            const xx = x(v);
            s.appendChild(el('line', { x1: xx, x2: xx, y1: mt + innerH, y2: mt + innerH + 4, class: 'cer-svg-axis' }));
            s.appendChild(el('text', { x: xx, y: mt + innerH + 18, 'text-anchor': 'middle', class: 'cer-svg-tick-text' }, fmtPct(v, 1)));
        });
        // Achsenbeschriftung
        s.appendChild(el('text', { x: ml + innerW / 2, y: H - 4, 'text-anchor': 'middle', class: 'cer-svg-label' }, 'CER (Per-Doc)'));
        s.appendChild(el('text', { x: 12, y: mt + innerH / 2, 'text-anchor': 'middle', class: 'cer-svg-label', transform: `rotate(-90 12 ${mt + innerH / 2})` }, 'Anzahl Docs'));
        wrap.appendChild(s);
    };

    CD.renderBoxplot = function (perDoc) {
        const wrap = $('#cer-plot-boxplot');
        clear(wrap);
        const values = perDoc.map(d => ({ doc: d.doc_id, v: d.cer_end_to_end })).filter(d => d.v != null).sort((a, b) => a.v - b.v);
        if (!values.length) return;
        const vs = values.map(d => d.v);
        const q = (arr, p) => {
            const i = (arr.length - 1) * p;
            const lo = Math.floor(i), hi = Math.ceil(i);
            return arr[lo] + (arr[hi] - arr[lo]) * (i - lo);
        };
        const q1 = q(vs, 0.25), med = q(vs, 0.5), q3 = q(vs, 0.75);
        const iqr = q3 - q1;
        const wLo = Math.max(vs[0], q1 - 1.5 * iqr);
        const wHi = Math.min(vs[vs.length - 1], q3 + 1.5 * iqr);
        const outliers = values.filter(d => d.v < wLo || d.v > wHi);
        const maxV = Math.max(...vs);

        const W = 720, H = 100, ml = 50, mr = 20, mt = 16, mb = 30;
        const innerW = W - ml - mr;
        const x = xScale([0, maxV], [ml, ml + innerW]);
        const cy = mt + (H - mt - mb) / 2;
        const boxH = 28;

        const s = svg(W, H);
        s.appendChild(el('line', { x1: ml, x2: ml + innerW, y1: H - mb + 4, y2: H - mb + 4, class: 'cer-svg-axis' }));
        ticks(0, maxV, 5).forEach(v => {
            const xx = x(v);
            s.appendChild(el('text', { x: xx, y: H - mb + 20, 'text-anchor': 'middle', class: 'cer-svg-tick-text' }, fmtPct(v, 1)));
        });
        // Whisker
        s.appendChild(el('line', { x1: x(wLo), x2: x(wHi), y1: cy, y2: cy, class: 'cer-svg-ci-line' }));
        s.appendChild(el('line', { x1: x(wLo), x2: x(wLo), y1: cy - 8, y2: cy + 8, class: 'cer-svg-ci-cap' }));
        s.appendChild(el('line', { x1: x(wHi), x2: x(wHi), y1: cy - 8, y2: cy + 8, class: 'cer-svg-ci-cap' }));
        // Box
        s.appendChild(el('rect', { x: x(q1), y: cy - boxH / 2, width: x(q3) - x(q1), height: boxH, class: 'cer-svg-bar', 'fill-opacity': 0.5, stroke: 'currentColor', 'stroke-width': 1 }));
        // Median
        s.appendChild(el('line', { x1: x(med), x2: x(med), y1: cy - boxH / 2, y2: cy + boxH / 2, class: 'cer-svg-ci-line', 'stroke-width': 2 }));
        // Outliers
        outliers.forEach(o => {
            const c = el('circle', { cx: x(o.v), cy: cy, r: 4, class: 'cer-svg-outlier' });
            const t = document.createElementNS(NS, 'title');
            t.textContent = `Doc ${o.doc}: ${fmtPct(o.v, 2)}`;
            c.appendChild(t);
            s.appendChild(c);
        });
        wrap.appendChild(s);
    };

    CD.renderForest = function (containerId, stratum, overallMean, orderHint) {
        const wrap = $('#' + containerId);
        clear(wrap);
        const keys = orderHint ? orderHint.filter(k => stratum[k]) : Object.keys(stratum);
        // Append any keys not in orderHint
        Object.keys(stratum).forEach(k => { if (!keys.includes(k)) keys.push(k); });
        if (!keys.length) return;
        const allHi = keys.flatMap(k => [stratum[k].mean_ci95[1], stratum[k].mean]);
        const maxV = Math.max(...allHi, overallMean) * 1.1;

        const rowH = 32;
        const W = 720, mlA = 110, mr = 50, mt = 20, mb = 30;
        const H = mt + keys.length * rowH + mb;
        const innerW = W - mlA - mr;
        const x = xScale([0, maxV], [mlA, mlA + innerW]);

        const s = svg(W, H);
        // Reference line (Overall Mean)
        s.appendChild(el('line', { x1: x(overallMean), x2: x(overallMean), y1: mt, y2: mt + keys.length * rowH, class: 'cer-svg-ref-line' }));
        s.appendChild(el('text', { x: x(overallMean), y: mt - 6, 'text-anchor': 'middle', class: 'cer-svg-annot' }, `Overall ${fmtPct(overallMean, 2)}`));
        // Rows
        keys.forEach((k, i) => {
            const y = mt + i * rowH + rowH / 2;
            const lbl = LANG_LABEL[k] || k;
            s.appendChild(el('text', { x: mlA - 8, y: y + 4, 'text-anchor': 'end', class: 'cer-svg-label' }, lbl));
            const st = stratum[k];
            drawCIBar(s, x(st.mean_ci95[0]), x(st.mean), x(st.mean_ci95[1]), y, 5);
            s.appendChild(el('text', { x: mlA + innerW + 6, y: y + 4, 'text-anchor': 'start', class: 'cer-svg-annot' }, `n=${st.n}`));
        });
        // X-Achse
        s.appendChild(el('line', { x1: mlA, x2: mlA + innerW, y1: mt + keys.length * rowH + 4, y2: mt + keys.length * rowH + 4, class: 'cer-svg-axis' }));
        ticks(0, maxV, 5).forEach(v => {
            const xx = x(v);
            s.appendChild(el('text', { x: xx, y: mt + keys.length * rowH + 22, 'text-anchor': 'middle', class: 'cer-svg-tick-text' }, fmtPct(v, 1)));
        });
        wrap.appendChild(s);
    };

    CD.renderMultiNorm = function (mn) {
        const tbody = $('#cer-multinorm-table tbody');
        tbody.innerHTML = '';
        const keys = Object.keys(mn);
        keys.forEach(k => {
            const o = mn[k];
            const tr = document.createElement('tr');
            tr.innerHTML = `<td><code>${esc(k)}</code></td>` +
                `<td class="num">${fmtPct(o.mean, 2)} <span class="cer-stat-ci">${fmtCI(o.mean_ci95[0], o.mean_ci95[1], 2)}</span></td>` +
                `<td class="num">${fmtPct(o.median, 2)} <span class="cer-stat-ci">${fmtCI(o.median_ci95[0], o.median_ci95[1], 2)}</span></td>`;
            tbody.appendChild(tr);
        });

        // Slope-Chart
        const wrap = $('#cer-plot-multinorm');
        clear(wrap);
        const W = 720, H = 220, ml = 50, mr = 80, mt = 16, mb = 50;
        const innerW = W - ml - mr, innerH = H - mt - mb;
        const xs = keys.map((_, i) => ml + (i / Math.max(1, keys.length - 1)) * innerW);
        const allV = keys.flatMap(k => [mn[k].mean_ci95[0], mn[k].mean_ci95[1]]);
        const maxV = Math.max(...allV) * 1.05;
        const yScale = v => mt + innerH - (v / maxV) * innerH;

        const s = svg(W, H);
        s.appendChild(el('line', { x1: ml, x2: ml + innerW, y1: mt + innerH, y2: mt + innerH, class: 'cer-svg-axis' }));
        for (let i = 0; i <= 4; i++) {
            const v = (maxV / 4) * i;
            const yy = yScale(v);
            s.appendChild(el('line', { x1: ml, x2: ml + innerW, y1: yy, y2: yy, class: 'cer-svg-grid' }));
            s.appendChild(el('text', { x: ml - 6, y: yy + 4, 'text-anchor': 'end', class: 'cer-svg-tick-text' }, fmtPct(v, 1)));
        }
        // Mean-Linie verbinden
        const path = keys.map((k, i) => `${i === 0 ? 'M' : 'L'} ${xs[i]} ${yScale(mn[k].mean)}`).join(' ');
        s.appendChild(el('path', { d: path, fill: 'none', stroke: 'currentColor', 'stroke-width': 1.5, 'stroke-opacity': 0.5 }));
        // CI + Punkt + Label
        keys.forEach((k, i) => {
            const o = mn[k];
            drawCIBar(s, xs[i] - 0, xs[i], xs[i] + 0, yScale(o.mean), 0); // nur Punkt
            // vertikale CI-Linie
            s.appendChild(el('line', { x1: xs[i], x2: xs[i], y1: yScale(o.mean_ci95[0]), y2: yScale(o.mean_ci95[1]), class: 'cer-svg-ci-line' }));
            s.appendChild(el('line', { x1: xs[i] - 5, x2: xs[i] + 5, y1: yScale(o.mean_ci95[0]), y2: yScale(o.mean_ci95[0]), class: 'cer-svg-ci-cap' }));
            s.appendChild(el('line', { x1: xs[i] - 5, x2: xs[i] + 5, y1: yScale(o.mean_ci95[1]), y2: yScale(o.mean_ci95[1]), class: 'cer-svg-ci-cap' }));
            s.appendChild(el('circle', { cx: xs[i], cy: yScale(o.mean), r: 5, class: 'cer-svg-ci-point' }));
            s.appendChild(el('text', { x: xs[i], y: mt + innerH + 16, 'text-anchor': 'middle', class: 'cer-svg-tick-text' }, k));
            s.appendChild(el('text', { x: xs[i], y: mt + innerH + 32, 'text-anchor': 'middle', class: 'cer-svg-annot' }, fmtPct(o.mean, 2)));
        });
        wrap.appendChild(s);
    };

    CD.renderPaired = function (pt) {
        if (pt.status === 'deferred') {
            $('#cer-paired-bar').innerHTML = '';
            $('#cer-paired-stats').innerHTML = `<div class="cer-stability-open"><strong>DEFERRED</strong> ${esc(pt.reason || 'Paired Test in dieser Iteration nicht moeglich.')}</div>`;
            $('#cer-paired-interp').textContent = '';
            return;
        }
        const total = pt.n_better + pt.n_worse + pt.n_unchanged;
        const bar = $('#cer-paired-bar');
        bar.innerHTML = '';
        const segs = [
            { cls: 'cer-paired-seg-better', n: pt.n_better, lbl: `${pt.n_better} besser` },
            { cls: 'cer-paired-seg-unchanged', n: pt.n_unchanged, lbl: `${pt.n_unchanged} unveraendert` },
            { cls: 'cer-paired-seg-worse', n: pt.n_worse, lbl: `${pt.n_worse} schlechter` }
        ];
        segs.forEach(s => {
            const div = document.createElement('div');
            div.className = 'cer-paired-seg ' + s.cls;
            div.style.flex = String(s.n / total);
            div.title = s.lbl;
            if (s.n > 0) div.textContent = s.lbl;
            bar.appendChild(div);
        });
        const stats = $('#cer-paired-stats');
        stats.innerHTML = `
            <div><span class="lbl">Mean Diff</span>${fmtPct(pt.mean_diff, 2)}</div>
            <div><span class="lbl">95% CI</span>${fmtCI(pt.mean_diff_ci95[0], pt.mean_diff_ci95[1], 2)}</div>
            <div><span class="lbl">p (bootstrap)</span>${pt.p_bootstrap.toFixed(3)}</div>`;
        $('#cer-paired-interp').textContent = pt.interpretation;
    };

    CD.renderDomain = function (dm) {
        const tbody = $('#cer-domain-table tbody');
        tbody.innerHTML = '';
        const lr = dm && dm.diacritic_preservation_rate && dm.diacritic_preservation_rate.by_language;
        if (!lr || !Object.keys(lr).length) {
            tbody.innerHTML = '<tr><td colspan="4" class="ed-hint">Diakritik-Erhaltungsrate nicht verfuegbar in dieser Iteration.</td></tr>';
            $('#cer-domain-method').textContent = '';
            return;
        }
        Object.keys(lr).forEach(k => {
            const o = lr[k];
            const tr = document.createElement('tr');
            const ci = o.rate_ci95 ? ` <span class="cer-stat-ci">${fmtCI(o.rate_ci95[0], o.rate_ci95[1], 1)}</span>` : '';
            const expected = o.expected_freq != null ? fmtPct(o.expected_freq, 1) : (o._n_docs != null ? `n=${o._n_docs}` : '–');
            const observed = o.observed_freq != null ? fmtPct(o.observed_freq, 1) : '–';
            tr.innerHTML = `<td>${esc(LANG_LABEL[k] || k)}</td>` +
                `<td class="num">${expected}</td>` +
                `<td class="num">${observed}</td>` +
                `<td class="num">${fmtPct(o.rate, 1)}${ci}</td>`;
            tbody.appendChild(tr);
        });
        $('#cer-domain-method').textContent = dm.diacritic_preservation_rate.method_ref || '';
    };

    CD.renderErrCat = function (ec) {
        const tbody = $('#cer-errcat-table tbody');
        tbody.innerHTML = '';
        const wrap = $('#cer-errcat-donut');
        clear(wrap);
        const keys = Object.keys(ec || {}).filter(k => ec[k] && ec[k].count != null).sort((a, b) => ec[b].count - ec[a].count);
        if (!keys.length) {
            tbody.innerHTML = '<tr><td colspan="3" class="ed-hint">Keine aggregierten Fehlerkategorien vorhanden in dieser Iteration.</td></tr>';
            wrap.innerHTML = '<p class="ed-hint">Pro-Doc Top-3 sind in der Per-Doc-Tabelle sichtbar.</p>';
            return;
        }
        keys.forEach((k, i) => {
            const tr = document.createElement('tr');
            const swatch = `<span style="display:inline-block;width:12px;height:12px;border-radius:2px;vertical-align:middle;margin-right:6px;background:var(${ERR_COLOR_TOKENS[i % ERR_COLOR_TOKENS.length]})"></span>`;
            tr.innerHTML = `<td>${swatch}${esc(ERR_LABEL[k] || k)}</td>` +
                `<td class="num">${fmtNum(ec[k].count)}</td>` +
                `<td class="num">${fmtPct(ec[k].share, 1)}</td>`;
            tbody.appendChild(tr);
        });

        // Donut (wrap bereits oben gecleart)
        const W = 320, H = 320, cx = W / 2, cy = H / 2, r = 130, ri = 70;
        const total = keys.reduce((a, k) => a + ec[k].count, 0);
        let acc = 0;
        const s = svg(W, H);
        keys.forEach((k, i) => {
            const v = ec[k].count;
            const a0 = (acc / total) * Math.PI * 2 - Math.PI / 2;
            const a1 = ((acc + v) / total) * Math.PI * 2 - Math.PI / 2;
            acc += v;
            const x0 = cx + r * Math.cos(a0), y0 = cy + r * Math.sin(a0);
            const x1 = cx + r * Math.cos(a1), y1 = cy + r * Math.sin(a1);
            const x2 = cx + ri * Math.cos(a1), y2 = cy + ri * Math.sin(a1);
            const x3 = cx + ri * Math.cos(a0), y3 = cy + ri * Math.sin(a0);
            const large = (a1 - a0) > Math.PI ? 1 : 0;
            const d = `M ${x0} ${y0} A ${r} ${r} 0 ${large} 1 ${x1} ${y1} L ${x2} ${y2} A ${ri} ${ri} 0 ${large} 0 ${x3} ${y3} Z`;
            const path = el('path', { d, fill: `var(${ERR_COLOR_TOKENS[i % ERR_COLOR_TOKENS.length]})`, stroke: 'var(--h-bg)', 'stroke-width': 1 });
            const t = document.createElementNS(NS, 'title');
            t.textContent = `${ERR_LABEL[k] || k}: ${ec[k].count} (${fmtPct(ec[k].share, 1)})`;
            path.appendChild(t);
            s.appendChild(path);
        });
        // Center text
        s.appendChild(el('text', { x: cx, y: cy - 4, 'text-anchor': 'middle', class: 'cer-svg-label' }, fmtNum(total)));
        s.appendChild(el('text', { x: cx, y: cy + 14, 'text-anchor': 'middle', class: 'cer-svg-annot' }, 'Fehler total'));
        wrap.appendChild(s);
    };

    CD.renderPerDoc = function (rows) {
        const tbody = $('#cer-perdoc-table tbody');
        tbody.innerHTML = '';
        rows.forEach(r => {
            const delta = (r.cer_end_to_end != null && r.cer_ocr_only != null) ? (r.cer_end_to_end - r.cer_ocr_only) : null;
            const top3 = (r.top_3_error_categories || [])
                .map(t => `${ERR_LABEL[t.category] || t.category} ${fmtPct(t.share, 0)}`).join(', ');
            const tr = document.createElement('tr');
            tr.dataset.doc = r.doc_id;
            tr.innerHTML = `
                <td><strong>${esc(r.doc_id)}</strong></td>
                <td class="num" data-sort="${r.cer_end_to_end ?? ''}">${fmtPct(r.cer_end_to_end, 2)}</td>
                <td class="num" data-sort="${r.cer_ocr_only ?? ''}">${fmtPct(r.cer_ocr_only, 2)}</td>
                <td class="num" data-sort="${delta ?? ''}">${delta == null ? '–' : (delta >= 0 ? '+' : '') + fmtPct(delta, 2)}</td>
                <td class="num" data-sort="${r.n_ref_chars ?? 0}">${fmtNum(r.n_ref_chars)}</td>
                <td>${esc(r.language)}</td>
                <td>${esc(r.layout_type)}</td>
                <td>${esc(r.pub_form)}</td>
                <td>${esc(r.scope_status)}</td>
                <td class="cer-perdoc-top3">${top3}</td>`;
            tr.addEventListener('click', () => CD.openDrilldown(r));
            tbody.appendChild(tr);
        });
        const tbl = $('#cer-perdoc-table');
        if (window.ZBZ && window.ZBZ.makeSortable) window.ZBZ.makeSortable(tbl);
    };

    CD.openDrilldown = function (row) {
        const sheet = $('#cer-drilldown');
        $('#cer-drilldown-title').textContent = `Doc ${row.doc_id}`;
        const body = $('#cer-drilldown-body');
        body.className = 'cer-drilldown-body';
        const top3 = (row.top_3_error_categories || []).map(t =>
            `<dt>${esc(ERR_LABEL[t.category] || t.category)}</dt><dd>${t.count} Fehler · ${fmtPct(t.share, 1)} der Top-3</dd>`).join('');
        body.innerHTML = `
            <dl>
                <dt>CER End-to-End</dt><dd>${fmtPct(row.cer_end_to_end, 2)}</dd>
                <dt>CER OCR-only</dt><dd>${fmtPct(row.cer_ocr_only, 2)}</dd>
                <dt>Referenz-Zeichen</dt><dd>${fmtNum(row.n_ref_chars)}</dd>
                <dt>Sprache</dt><dd>${esc(row.language)}</dd>
                <dt>Layout-Typ</dt><dd>${esc(row.layout_type)}</dd>
                <dt>Publikationsform</dt><dd>${esc(row.pub_form)}</dd>
                <dt>Scope</dt><dd>${esc(row.scope_status)}</dd>
            </dl>
            <h4 style="font-family:var(--h-font-heading);font-size:var(--h-sm);margin:var(--h-space-md) 0 var(--h-space-xs);">Top-3-Fehlerkategorien</h4>
            <dl>${top3}</dl>`;
        sheet.hidden = false;
    };

    CD.bindDrilldownClose = function () {
        $('#cer-drilldown-close').addEventListener('click', () => { $('#cer-drilldown').hidden = true; });
        document.addEventListener('keydown', e => {
            if (e.key === 'Escape' && !$('#cer-drilldown').hidden) $('#cer-drilldown').hidden = true;
        });
    };

    CD.renderLit = function (lit, refMean, refCi) {
        const wrap = $('#cer-lit-bars');
        clear(wrap);
        const items = lit.filter(l => l.cer != null).slice().sort((a, b) => a.cer - b.cer);
        if (!items.length) { wrap.innerHTML = '<p class="ed-hint">Keine vergleichbaren Eintraege.</p>'; return; }
        const allV = items.map(i => i.cer).concat([refCi[1]]);
        const maxV = Math.max(...allV) * 1.1;
        const rowH = 38, ml = 200, mr = 50, mt = 14, mb = 30;
        const W = 760;
        const H = mt + items.length * rowH + mb;
        const innerW = W - ml - mr;
        const x = xScale([0, maxV], [ml, ml + innerW]);

        const s = svg(W, H);
        // Reference Band + Line (ZBZ Pipeline)
        s.appendChild(el('rect', { x: x(refCi[0]), y: mt, width: x(refCi[1]) - x(refCi[0]), height: items.length * rowH, class: 'cer-svg-ref-band' }));
        s.appendChild(el('line', { x1: x(refMean), x2: x(refMean), y1: mt, y2: mt + items.length * rowH, class: 'cer-svg-ref-line' }));
        s.appendChild(el('text', { x: x(refMean), y: mt - 2, 'text-anchor': 'middle', class: 'cer-svg-annot' }, `ZBZ ${fmtPct(refMean, 2)}`));

        items.forEach((it, i) => {
            const y = mt + i * rowH + rowH / 2;
            const cls = it.comparable === 'true' || it.comparable === true ? 'cer-svg-lit-bar-true'
                : it.comparable === 'partial' ? 'cer-svg-lit-bar-partial' : 'cer-svg-lit-bar-false';
            s.appendChild(el('text', { x: ml - 8, y: y - 2, 'text-anchor': 'end', class: 'cer-svg-label' }, it.source));
            s.appendChild(el('text', { x: ml - 8, y: y + 12, 'text-anchor': 'end', class: 'cer-svg-annot' }, it.lang));
            const rect = el('rect', { x: ml, y: y - 12, width: x(it.cer) - ml, height: 24, class: cls });
            const t = document.createElementNS(NS, 'title');
            t.textContent = `${it.source} · ${it.method} · CER ${fmtPct(it.cer, 2)}\n${it.caveat}`;
            rect.appendChild(t);
            s.appendChild(rect);
            s.appendChild(el('text', { x: x(it.cer) + 6, y: y + 4, 'text-anchor': 'start', class: 'cer-svg-annot' }, fmtPct(it.cer, 2)));
        });
        // X-Achse
        s.appendChild(el('line', { x1: ml, x2: ml + innerW, y1: mt + items.length * rowH + 4, y2: mt + items.length * rowH + 4, class: 'cer-svg-axis' }));
        ticks(0, maxV, 5).forEach(v => {
            const xx = x(v);
            s.appendChild(el('text', { x: xx, y: mt + items.length * rowH + 22, 'text-anchor': 'middle', class: 'cer-svg-tick-text' }, fmtPct(v, 1)));
        });
        wrap.appendChild(s);

        // Legende
        $('#cer-lit-legend').innerHTML = `
            <span class="cer-lit-legend-item"><span class="cer-lit-legend-swatch cer-lit-legend-swatch-true"></span>like-for-like</span>
            <span class="cer-lit-legend-item"><span class="cer-lit-legend-swatch cer-lit-legend-swatch-partial"></span>teilweise vergleichbar</span>
            <span class="cer-lit-legend-item"><span class="cer-lit-legend-swatch cer-lit-legend-swatch-false"></span>nicht vergleichbar</span>`;
    };

    CD.renderStability = function (st) {
        const c = $('#cer-stability-content');
        if (st.status === 'open') {
            c.innerHTML = `<div class="cer-stability-open"><strong>OFFEN</strong> ${esc(st.reason)}</div>`;
            return;
        }
        c.innerHTML = `<p class="ed-hint">Stabilitaet gemessen ueber ${st.n_runs} Re-Runs auf ${st.n_docs} Docs.</p>`;
        // Per-Doc-Std: optional, render falls Daten da
        if (st.per_doc_std) {
            const ul = document.createElement('ul');
            Object.keys(st.per_doc_std).forEach(d => {
                const li = document.createElement('li');
                li.innerHTML = `<code>${esc(d)}</code>: σ=${fmtPct(st.per_doc_std[d], 3)}`;
                ul.appendChild(li);
            });
            c.appendChild(ul);
        }
        if (st.interpretation) {
            const p = document.createElement('p');
            p.textContent = st.interpretation;
            c.appendChild(p);
        }
    };

    CD.renderProxies = function (px) {
        // Whole section deferred?
        if (!px || px.status === 'open' || px.status === 'deferred' || (!px.validation_n19 && !px.corpus_estimate && !px.definitions)) {
            const sec = $('#cer-sec-proxies');
            sec.innerHTML = `
                <div class="cer-proxies-banner"><strong>SCHAETZUNG</strong> n=285 — Track in eigener Iteration</div>
                <h2 class="ed-section">Korpus-weite Proxy-Schaetzung</h2>
                <div class="cer-stability-open"><strong>${esc(px && px.status ? px.status.toUpperCase() : 'PENDING')}</strong> ${esc(px && px.reason ? px.reason : 'Proxy-Framework folgt in eigener Iteration.')}</div>`;
            return;
        }
        // Validierungs-Tabelle
        const tbody = $('#cer-proxy-validation-table tbody');
        tbody.innerHTML = '';
        const v = px.validation_n19;
        Object.keys(v).filter(k => k !== 'composite').forEach(k => {
            const o = v[k];
            const w = (v.composite && v.composite.weights && v.composite.weights[k] != null) ? v.composite.weights[k] : null;
            const tr = document.createElement('tr');
            tr.innerHTML = `<td><code>${esc(k)}</code></td>` +
                `<td class="num">${o.pearson != null ? o.pearson.toFixed(2) : '–'}</td>` +
                `<td class="num">${o.spearman != null ? o.spearman.toFixed(2) : '–'}</td>` +
                `<td class="num">${o.p != null ? o.p.toFixed(4) : '–'}</td>` +
                `<td class="num">${w != null ? w.toFixed(2) : '–'}</td>`;
            tbody.appendChild(tr);
        });
        if (v.composite) {
            $('#cer-proxy-r2').innerHTML = `Composite-Score Validierung: <strong>R² = ${v.composite.r2.toFixed(2)}</strong> (${esc(v.composite.method || '')})`;
        }

        // Verteilungs-Plot
        const wrap = $('#cer-proxy-distribution');
        clear(wrap);
        const ce = px.corpus_estimate;
        if (ce && ce.estimated_distribution) {
            const dist = ce.estimated_distribution;
            const labels = dist.buckets || dist.bucket_edges_cer.slice(0, -1).map((_, i) => `${dist.bucket_edges_cer[i]}-${dist.bucket_edges_cer[i + 1]}`);
            const counts = dist.counts;
            const W = 720, H = 220, ml = 50, mr = 20, mt = 16, mb = 50;
            const innerW = W - ml - mr, innerH = H - mt - mb;
            const maxC = Math.max(...counts);
            const barW = innerW / counts.length;
            const yScale = c => mt + innerH - (c / maxC) * innerH;

            const s = svg(W, H);
            s.appendChild(el('line', { x1: ml, x2: ml + innerW, y1: mt + innerH, y2: mt + innerH, class: 'cer-svg-axis' }));
            for (let i = 0; i <= 4; i++) {
                const c = (maxC / 4) * i;
                const yy = yScale(c);
                s.appendChild(el('line', { x1: ml, x2: ml + innerW, y1: yy, y2: yy, class: 'cer-svg-grid' }));
                s.appendChild(el('text', { x: ml - 6, y: yy + 4, 'text-anchor': 'end', class: 'cer-svg-tick-text' }, Math.round(c).toString()));
            }
            counts.forEach((c, i) => {
                const x0 = ml + i * barW;
                const y = yScale(c);
                s.appendChild(el('rect', { x: x0 + 2, y: y, width: barW - 4, height: mt + innerH - y, class: 'cer-svg-bar-alt' }));
                s.appendChild(el('text', { x: x0 + barW / 2, y: y - 4, 'text-anchor': 'middle', class: 'cer-svg-annot' }, String(c)));
                s.appendChild(el('text', { x: x0 + barW / 2, y: mt + innerH + 16, 'text-anchor': 'middle', class: 'cer-svg-tick-text' }, labels[i]));
            });
            // Mean-Linie
            if (ce.estimated_mean_cer != null) {
                // Map mean to bin position (linear search)
                const edges = dist.bucket_edges_cer;
                let binIdx = 0;
                for (let i = 0; i < edges.length - 1; i++) if (ce.estimated_mean_cer >= edges[i] && ce.estimated_mean_cer < edges[i + 1]) binIdx = i;
                const xMean = ml + (binIdx + 0.5) * barW;
                s.appendChild(el('line', { x1: xMean, x2: xMean, y1: mt, y2: mt + innerH, class: 'cer-svg-ref-line' }));
                s.appendChild(el('text', { x: xMean, y: mt - 2, 'text-anchor': 'middle', class: 'cer-svg-annot' }, `Mean ${fmtPct(ce.estimated_mean_cer, 2)}`));
            }
            wrap.appendChild(s);
        }

        if (ce && ce.caveat) $('#cer-proxy-caveat').textContent = ce.caveat;

        // Definitionen
        const dl = $('#cer-proxy-defs-list');
        dl.innerHTML = '';
        if (px.definitions) {
            Object.keys(px.definitions).forEach(k => {
                const dt = document.createElement('dt'); dt.textContent = k;
                const dd = document.createElement('dd'); dd.textContent = px.definitions[k];
                dl.appendChild(dt); dl.appendChild(dd);
            });
        }
    };

    CD.renderMeta = function (meta) {
        const grid = $('#cer-meta-grid');
        const items = [
            { l: 'tool_version', v: meta.tool_version },
            { l: 'git_sha', v: meta.git_sha },
            { l: 'generated_at', v: meta.generated_at },
            { l: 'seed', v: meta.seed },
            { l: 'bootstrap_n', v: meta.bootstrap_n },
            { l: 'alignment', v: meta.alignment_algo },
            { l: 'normalization_steps', v: (meta.normalization_steps || []).join(' → ') }
        ];
        grid.innerHTML = items.map(i =>
            `<div class="cer-meta-item"><span class="cer-meta-item-label">${esc(i.l)}</span><span class="cer-meta-item-value">${esc(i.v)}</span></div>`
        ).join('');
    };

    // ---- Main ----
    CD.init = async function () {
        try {
            const { data, url } = await CD.load();
            $('#cer-loading').hidden = true;
            $('#cer-app').hidden = false;

            CD.renderMetaBar(data.meta, data.corpus, url);
            CD.renderLimitations(data);
            CD.renderOverall(data.overall);
            CD.renderHistogram(data.per_doc);
            CD.renderBoxplot(data.per_doc);
            const refOverall = data.overall.end_to_end || data.overall.ocr_only || { mean: 0, mean_ci95: [0, 0] };
            CD.renderForest('cer-forest-language', data.strata.language, refOverall.mean, STRATA_ORDER);
            CD.renderForest('cer-forest-layout', data.strata.layout_type, refOverall.mean, LAYOUT_ORDER);
            CD.renderForest('cer-forest-pubform', data.strata.pub_form, refOverall.mean, null);
            CD.renderMultiNorm(data.multi_norm);
            CD.renderPaired(data.paired_test);
            CD.renderDomain(data.domain_metrics);
            CD.renderErrCat(data.error_categories);
            CD.renderPerDoc(data.per_doc);
            CD.bindDrilldownClose();
            CD.renderLit(data.comparison_lit, refOverall.mean, refOverall.mean_ci95);
            CD.renderStability(data.stability);
            CD.renderProxies(data.proxies);
            CD.renderMeta(data.meta);
        } catch (err) {
            $('#cer-loading').hidden = true;
            const e = $('#cer-error');
            e.hidden = false;
            e.textContent = 'Fehler beim Laden: ' + (err && err.message ? err.message : String(err));
            console.error('[CerDashboard]', err);
        }
    };

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', CD.init);
    } else {
        CD.init();
    }

    window.ZBZ = window.ZBZ || {};
    window.ZBZ.CerDashboard = CD;
})();
