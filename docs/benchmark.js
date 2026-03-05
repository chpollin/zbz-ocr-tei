/**
 * ZBZ OCR Pipeline -- Benchmark Module
 * Namespace: ZBZ.Benchmark
 * Depends on: shared.js (ZBZ namespace)
 */
(function () {
    'use strict';

    var DATA = {
        timestamp: "2026-02-18",
        documents: [
            {
                id: "2310", desc: "Rezension (Karl Jaspers, Philosophie)",
                type: "A", lang: "FR", totalPages: 3,
                mistral: { pages: 3, chars: 8041, time: 5.6, spp: 1.87 },
                deepseek: { pages: 2, chars: 6597, available: [2, 3] }
            },
            {
                id: "1180", desc: "Jahresbericht SAGW 1975",
                type: "A", lang: "DE/FR", totalPages: 8,
                mistral: { pages: 8, chars: 20121, time: 6.37, spp: 0.8 },
                deepseek: { pages: 2, chars: 6070, available: [2, 3] }
            },
            {
                id: "290", desc: "L'Oeuvre de Karl Jaspers",
                type: "A", lang: "FR", totalPages: 5,
                mistral: { pages: 5, chars: 15148, time: 6.34, spp: 1.27 },
                deepseek: { pages: 2, chars: 5213, available: [1, 2] }
            }
        ]
    };

    function sum(arr, fn) {
        return arr.reduce(function (s, d) { return s + fn(d); }, 0);
    }

    function init() {
        ZBZ.$('#loading').classList.add('hidden');
        ZBZ.$('#app').classList.remove('hidden');

        renderBanner();
        renderMetrics();
        renderDocs();
        initEvents();
    }

    function renderBanner() {
        ZBZ.$('#info-banner').innerHTML =
            '<div class="info-banner">' +
            '<strong>Hinweis:</strong> DeepSeek wurde lokal (GPU) getestet und hat nur 2 Seiten pro Dokument verarbeitet. ' +
            'Mistral laeuft serverseitig und verarbeitet alle Seiten. Die Gesamtzeichenzahlen sind daher nicht direkt vergleichbar. ' +
            'Waehle unten Seiten mit <span class="hint-dot violet" style="display:inline-block;width:12px;height:3px;background:var(--accent-b);vertical-align:middle;border-radius:1px;"></span> violettem Rand, ' +
            'um beide Engines auf derselben Seite zu vergleichen.' +
            '</div>';
    }

    function renderMetrics() {
        var d = DATA.documents;
        var mPages = sum(d, function (x) { return x.mistral.pages; });
        var dPages = sum(d, function (x) { return x.deepseek.pages; });
        var avgSpp = (sum(d, function (x) { return x.mistral.spp; }) / d.length).toFixed(1);
        var totalTime = sum(d, function (x) { return x.mistral.time; }).toFixed(1);

        ZBZ.$('#metrics').innerHTML =
            '<div class="metric-card">' +
                '<div class="label">Getestete Dokumente</div>' +
                '<div class="value">' + d.length + ' <span class="dim">/ 15</span></div>' +
                '<div class="detail">Phase 1 -- alle Typ A</div>' +
            '</div>' +
            '<div class="metric-card">' +
                '<div class="label">Seitenabdeckung</div>' +
                '<div class="value"><span class="teal">' + mPages + '</span> <span class="dim">vs</span> <span class="violet">' + dPages + '</span></div>' +
                '<div class="detail">Mistral alle Seiten, DeepSeek je 2</div>' +
            '</div>' +
            '<div class="metric-card">' +
                '<div class="label">Mistral Geschwindigkeit</div>' +
                '<div class="value"><span class="teal">' + avgSpp + 's</span> <span class="dim">/ Seite</span></div>' +
                '<div class="detail">' + totalTime + 's gesamt (Cloud-API, kein GPU)</div>' +
            '</div>' +
            '<div class="metric-card">' +
                '<div class="label">DeepSeek Modus</div>' +
                '<div class="value"><span class="violet">Lokal</span></div>' +
                '<div class="detail">GPU, keine Zeitmessung verfuegbar</div>' +
            '</div>';
    }

    function renderDocs() {
        var container = ZBZ.$('#doc-list');

        DATA.documents.forEach(function (doc, idx) {
            var mPct = (doc.mistral.chars / (doc.mistral.chars + doc.deepseek.chars) * 100).toFixed(1);
            var dPct = (100 - parseFloat(mPct)).toFixed(1);
            var sharedStr = doc.deepseek.available.join(', ');

            var pageBtns = '';
            for (var p = 1; p <= doc.totalPages; p++) {
                var both = doc.deepseek.available.indexOf(p) !== -1;
                var isStart = (p === doc.deepseek.available[0]);
                pageBtns += '<button class="pg' + (both ? ' both' : '') + (isStart ? ' active' : '') + '" data-doc="' + doc.id + '" data-page="' + p + '">' + p + '</button>';
            }

            var card = document.createElement('div');
            card.className = 'card' + (idx === 0 ? ' open' : '');
            card.innerHTML =
                '<div class="card-header">' +
                    '<span class="title">' + doc.id + '.pdf -- ' + doc.desc + '</span>' +
                    '<div class="tags">' +
                        '<span class="tag">Typ ' + doc.type + '</span>' +
                        '<span class="tag">' + doc.lang + '</span>' +
                        '<span class="tag">' + doc.totalPages + ' S.</span>' +
                        '<span class="chevron">&#9662;</span>' +
                    '</div>' +
                '</div>' +
                '<div class="card-body">' +
                    '<div class="stats-grid">' +
                        '<div class="stats-panel">' +
                            '<h4 class="teal">Mistral Document AI 2512</h4>' +
                            '<div class="stat-row"><span class="sl">Seiten</span><span class="sv">' + doc.mistral.pages + ' / ' + doc.totalPages + '</span></div>' +
                            '<div class="stat-row"><span class="sl">Zeichen</span><span class="sv">' + ZBZ.fmtNum(doc.mistral.chars) + '</span></div>' +
                            '<div class="stat-row"><span class="sl">Zeit</span><span class="sv">' + doc.mistral.time + 's (' + doc.mistral.spp + 's/S.)</span></div>' +
                        '</div>' +
                        '<div class="stats-panel">' +
                            '<h4 class="violet">DeepSeek-OCR-2</h4>' +
                            '<div class="stat-row"><span class="sl">Seiten</span><span class="sv">' + doc.deepseek.pages + ' / ' + doc.totalPages + '</span></div>' +
                            '<div class="stat-row"><span class="sl">Zeichen</span><span class="sv">' + ZBZ.fmtNum(doc.deepseek.chars) + '</span></div>' +
                            '<div class="stat-row"><span class="sl">Vorhanden</span><span class="sv">S. ' + sharedStr + '</span></div>' +
                        '</div>' +
                    '</div>' +
                    '<div class="bar-wrap">' +
                        '<div class="bar-label">Zeichenvergleich (unterschiedliche Seitenzahl)</div>' +
                        '<div class="bar">' +
                            '<div class="bar-seg teal" style="width:' + mPct + '%">' + ZBZ.fmtNum(doc.mistral.chars) + '</div>' +
                            '<div class="bar-seg violet" style="width:' + dPct + '%">' + ZBZ.fmtNum(doc.deepseek.chars) + '</div>' +
                        '</div>' +
                        '<div class="bar-footer">' +
                            '<span>Mistral (' + doc.mistral.pages + ' S.)</span>' +
                            '<span>DeepSeek (' + doc.deepseek.pages + ' S.)</span>' +
                        '</div>' +
                    '</div>' +
                    '<div class="page-nav" data-doc="' + doc.id + '">' +
                        '<span class="label">Seite</span>' +
                        pageBtns +
                        '<span class="hint"><span class="hint-dot violet"></span> beide Engines</span>' +
                    '</div>' +
                    '<div class="preview" id="pv-' + doc.id + '">' +
                        '<div class="preview-col">' +
                            '<div class="preview-col-header">Faksimile</div>' +
                            '<div class="preview-col-body" id="img-' + doc.id + '">' +
                                '<img src="" alt="Scan" id="img-el-' + doc.id + '">' +
                            '</div>' +
                        '</div>' +
                        '<div class="preview-col">' +
                            '<div class="preview-col-header teal">Mistral OCR</div>' +
                            '<div class="preview-col-body"><pre id="mt-' + doc.id + '"></pre></div>' +
                        '</div>' +
                        '<div class="preview-col">' +
                            '<div class="preview-col-header violet">DeepSeek OCR</div>' +
                            '<div class="preview-col-body"><pre id="dt-' + doc.id + '"></pre></div>' +
                        '</div>' +
                    '</div>' +
                '</div>';
            container.appendChild(card);

            showPage(doc.id, doc.deepseek.available[0]);
        });
    }

    async function fetchText(path) {
        try {
            var r = await fetch(path);
            if (r.ok) return await r.text();
        } catch (e) { /* ignore */ }
        return null;
    }

    async function showPage(docId, page, btn) {
        if (btn) {
            var btns = btn.closest('.page-nav').querySelectorAll('.pg');
            btns.forEach(function (b) { b.classList.remove('active'); });
            btn.classList.add('active');
        }

        var pp = ZBZ.padPage(page);
        ZBZ.$('#img-el-' + docId).src = 'images/' + docId + '/' + docId + '_p' + pp + '.png';

        var mt = await fetchText('../output/mistral_results/' + docId + '_p' + page + '.md');
        var mEl = ZBZ.$('#mt-' + docId);
        mEl.textContent = mt || '';
        if (!mt) mEl.innerHTML = '<div class="empty-state">Keine Daten</div>';

        var dt = await fetchText('../output/ocr_results/' + docId + '_p' + page + '.md');
        var dEl = ZBZ.$('#dt-' + docId);
        dEl.textContent = dt || '';
        if (!dt) dEl.innerHTML = '<div class="empty-state">Seite nicht verarbeitet</div>';
    }

    function initEvents() {
        document.addEventListener('click', function (e) {
            var header = e.target.closest('.card-header');
            if (header) header.closest('.card').classList.toggle('open');
        });

        document.addEventListener('click', function (e) {
            var btn = e.target.closest('.pg[data-doc]');
            if (!btn) return;
            showPage(btn.getAttribute('data-doc'), parseInt(btn.getAttribute('data-page')), btn);
        });

        document.addEventListener('click', function (e) {
            var img = e.target.closest('.preview-col-body img');
            if (!img) return;
            ZBZ.$('#overlay-img').src = img.src;
            ZBZ.$('#overlay').classList.add('active');
        });

        ZBZ.$('#overlay').addEventListener('click', function () {
            this.classList.remove('active');
        });

        document.addEventListener('keydown', function (e) {
            if (e.key === 'Escape') ZBZ.$('#overlay').classList.remove('active');
        });
    }

    ZBZ.Benchmark = { init: init };
    init();
})();
