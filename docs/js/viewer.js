/**
 * viewer.js — Pipeline-Viewer fuer ein einzelnes Dokument
 *
 * Verantwortlich fuer:
 *  - Doc-Metadaten aus catalog.json laden (per ?doc= URL-Parameter)
 *  - Seitennavigation (Prev/Next, Pfeiltasten)
 *  - Mode-Switching (view / layout / text)
 *  - Faksimile + Layout-Overlay (links)
 *  - Text-Panel (OCR/TEI/XML) rechts
 *  - Download-Aktionen
 *
 * Die Korpus-Uebersicht (Doc-Liste, Filter) liegt in docs/index.html.
 *
 * Namespace: ZBZ.Viewer
 */
(function () {
    'use strict';

    const $  = ZBZ.$;
    const $$ = ZBZ.$$;

    // ---- State ----
    const state = {
        catalog: null,
        doc: null,
        page: 1,
        mode: 'view',         // view | layout | text
        textSource: 'ocr',    // ocr | tei | xml
        ocrSource: 'mistral',
        layout: null,
        teiXml: null,
        _currentText: null,
        _currentEditedText: null
    };

    const cache = new ZBZ.Cache(40);

    // ---- DOM-Refs ----
    const refs = {
        subbar:         $('#doc-subbar'),
        docMeta:        $('#doc-meta'),
        pageInfo:       $('#page-info'),
        btnPrev:        $('#btn-prev'),
        btnNext:        $('#btn-next'),
        modeBtns:       $$('.mode-btn[data-mode]'),
        textSourceBtns: $$('.mode-btn[data-text-source]'),
        ocrSourceSel:   $('#ocr-source'),
        imageBody:      $('#image-body'),
        textBody:       $('#text-body'),
        textTitle:      $('#text-panel-title'),
        regionCount:    $('#region-count'),
        layoutToolbar:  $('#layout-toolbar'),
        btnDlLayout:    $('#btn-download-layout'),
        btnDlText:      $('#btn-download-text'),
        btnDlTei:       $('#btn-download-tei')
    };

    // ============================================================ Init ============================================================

    async function init() {
        bindEvents();

        const urlDoc = ZBZ.getParam('doc');
        if (!urlDoc) {
            renderNoDoc();
            return;
        }

        const data = await ZBZ.fetchJSON('data/catalog.json');
        if (!data) {
            renderError('catalog.json nicht gefunden. <code>python -m scripts.generate_edition_data</code>');
            return;
        }
        state.catalog = data;

        const list = data.documents || data.docs || [];
        const doc = list.find(d => String(d.id) === String(urlDoc));
        if (!doc) {
            renderError('Dokument <code>' + ZBZ.esc(urlDoc) + '</code> nicht im Katalog. <a href="index.html">Zurueck zum Korpus</a>');
            return;
        }

        const urlPage = parseInt(ZBZ.getParam('page'), 10);
        await selectDoc(doc, isNaN(urlPage) ? 1 : urlPage);
        ZBZ.log('Viewer', 'init done, doc ' + doc.id);
    }

    function renderNoDoc() {
        refs.imageBody.innerHTML =
            '<div class="empty">Kein Dokument ausgewaehlt. <a href="index.html">Zur Korpus-Uebersicht</a></div>';
        refs.textBody.innerHTML =
            '<div class="empty">—</div>';
    }

    function renderError(html) {
        refs.imageBody.innerHTML = '<div class="empty">' + html + '</div>';
        refs.textBody.innerHTML  = '<div class="empty">—</div>';
    }

    // ============================================================ Doc selektieren ============================================================

    async function selectDoc(doc, startPage) {
        state.doc = doc;
        state.page = startPage || 1;
        state.layout = null;
        state.teiXml = null;
        ZBZ.setParams({ doc: doc.id, page: state.page });
        document.title = (doc.title ? doc.title.slice(0, 60) + ' — ' : '') + 'Hersch Pipeline-Viewer';

        // Sub-Bar zeigen + befuellen
        refs.subbar.hidden = false;
        const metaParts = [
            `<strong>${ZBZ.esc(doc.id)}</strong>`,
            ZBZ.esc(doc.title || ''),
            ZBZ.esc(doc.author || ''),
            ZBZ.esc(doc.lang || ''),
            'Typ ' + ZBZ.esc(doc.type || '—'),
            (doc.page_count || '?') + ' S.'
        ].filter(Boolean);
        let metaHtml = metaParts.map(p => `<span>${p}</span>`).join('<span class="sep">&middot;</span>');
        if (doc.screening) {
            metaHtml += `<span class="sep">&middot;</span><span class="badge badge--info">${ZBZ.esc(doc.screening)}</span>`;
        }
        refs.docMeta.innerHTML = metaHtml;

        // Buttons enablen
        refs.btnPrev.disabled = state.page <= 1;
        refs.btnNext.disabled = state.page >= (doc.page_count || 1);
        refs.btnDlLayout.disabled = false;
        refs.btnDlText.disabled = false;
        refs.btnDlTei.disabled = false;

        await loadPage();
    }

    // ============================================================ Page laden ============================================================

    async function loadPage() {
        if (!state.doc) return;
        const doc = state.doc, page = state.page;
        refs.pageInfo.textContent = page + ' / ' + (doc.page_count || '?');
        refs.btnPrev.disabled = page <= 1;
        refs.btnNext.disabled = page >= (doc.page_count || 1);
        ZBZ.setParams({ page });

        await renderFacsimile();
        await renderTextPanel();
    }

    async function renderFacsimile() {
        const doc = state.doc, page = state.page;
        refs.imageBody.innerHTML = '';

        const facs = ZBZ.el('div', { cls: 'facsimile' });
        const img = ZBZ.el('img', {
            cls: 'facsimile__img',
            attrs: { src: ZBZ.path.image(doc.id, page), alt: 'Faksimile Seite ' + page, loading: 'eager' }
        });
        img.addEventListener('error', () => {
            refs.imageBody.innerHTML =
                '<div class="empty">Faksimile nicht verfuegbar fuer Seite ' + page +
                '<br><code style="font-size:0.85em">' + ZBZ.esc(ZBZ.path.image(doc.id, page)) + '</code></div>';
        });

        const overlay = ZBZ.el('div', { cls: 'facsimile__overlay', attrs: { id: 'layout-overlay' } });
        facs.appendChild(img);
        facs.appendChild(overlay);
        refs.imageBody.appendChild(facs);

        const layout = await fetchLayout(doc.id, page);
        state.layout = layout;
        if (layout && layout.regions) {
            refs.regionCount.textContent = layout.regions.length + ' Regionen';
            renderRegionOverlay(overlay, layout.regions);
        } else {
            refs.regionCount.textContent = 'keine Layout-Daten';
        }

        if (state.mode === 'layout' && ZBZ.LayoutEditor) {
            ZBZ.LayoutEditor.attach(overlay, layout, onLayoutChanged);
        }
    }

    async function fetchLayout(doc, page) {
        const ck = 'layout:' + doc + ':' + page;
        if (cache.has(ck)) return cache.get(ck);
        const j = await ZBZ.fetchFirstJsonOk(ZBZ.path.layoutGemini(doc, page))
              || await ZBZ.fetchFirstJsonOk(ZBZ.path.layoutDocling(doc, page));
        cache.set(ck, j);
        return j;
    }

    function renderRegionOverlay(overlay, regions) {
        overlay.innerHTML = '';
        regions.forEach((r, idx) => {
            if (!r.bbox) return;
            const b = r.bbox;
            const div = ZBZ.el('div', {
                cls: 'region ' + ZBZ.regionTypeCls(r.zbz_tag),
                attrs: { 'data-region-idx': idx, title: r.text || ZBZ.regionTypeLabel(r.zbz_tag) },
                style: {
                    left:   b.x_pct + '%',
                    top:    b.y_pct + '%',
                    width:  b.w_pct + '%',
                    height: b.h_pct + '%'
                }
            });
            overlay.appendChild(div);
        });
    }

    function onLayoutChanged(regions) {
        if (!state.layout) state.layout = { regions: [] };
        state.layout.regions = regions;
        refs.regionCount.textContent = regions.length + ' Regionen (geaendert)';
    }

    // ============================================================ Text-Panel ============================================================

    async function renderTextPanel() {
        const doc = state.doc, page = state.page;
        refs.textBody.innerHTML = '<div class="empty">Lade…</div>';

        if (state.textSource === 'ocr') {
            refs.textTitle.textContent = 'OCR · ' + state.ocrSource;
            const res = await ZBZ.fetchFirstOk(ZBZ.path.ocr(state.ocrSource, doc.id, page));
            if (!res) {
                refs.textBody.innerHTML = '<div class="empty">Keine OCR-Daten fuer ' + state.ocrSource + ' / Seite ' + page + '.</div>';
                state._currentText = null;
                return;
            }
            state._currentText = res.text;
            renderOcrText(res.text);
        }
        else if (state.textSource === 'tei') {
            refs.textTitle.textContent = 'TEI · gerendert';
            const xml = await loadTeiPage(doc.id, page);
            if (!xml) {
                refs.textBody.innerHTML = '<div class="empty">Kein TEI fuer Seite ' + page + '.</div>';
                return;
            }
            state.teiXml = xml;
            ZBZ.TeiRender.render(xml, refs.textBody);
            ensureTextEditableState();
        }
        else if (state.textSource === 'xml') {
            refs.textTitle.textContent = 'TEI · XML';
            const xml = await loadTeiPage(doc.id, page);
            if (!xml) {
                refs.textBody.innerHTML = '<div class="empty">Kein TEI fuer Seite ' + page + '.</div>';
                return;
            }
            state.teiXml = xml;
            ZBZ.TeiRender.renderXml(xml, refs.textBody);
            ensureTextEditableState();
        }
    }

    function renderOcrText(text) {
        refs.textBody.innerHTML = '';
        const div = ZBZ.el('div', { cls: 'text', text });
        refs.textBody.appendChild(div);
        ensureTextEditableState();
    }

    function ensureTextEditableState() {
        if (state.mode === 'text' && ZBZ.TranscriptionEditor) {
            ZBZ.TranscriptionEditor.attach(refs.textBody, state.textSource, (newContent) => {
                state._currentEditedText = newContent;
            });
        }
    }

    async function loadTeiPage(doc, page) {
        const ck = 'tei:' + doc + ':' + page;
        if (cache.has(ck)) return cache.get(ck);
        const res = await ZBZ.fetchFirstOk(ZBZ.path.teiPage(doc, page));
        const xml = res ? res.text : null;
        cache.set(ck, xml);
        return xml;
    }

    async function loadTeiFinal(doc) {
        const ck = 'tei-final:' + doc;
        if (cache.has(ck)) return cache.get(ck);
        const res = await ZBZ.fetchFirstOk(ZBZ.path.teiFinal(doc));
        const xml = res ? res.text : null;
        cache.set(ck, xml);
        return xml;
    }

    // ============================================================ Modes ============================================================

    function setMode(mode) {
        state.mode = mode;
        refs.modeBtns.forEach(b => b.setAttribute('aria-pressed', b.getAttribute('data-mode') === mode ? 'true' : 'false'));

        const overlay = $('#layout-overlay');
        if (mode === 'layout') {
            refs.layoutToolbar.classList.remove('hidden');
            if (overlay) overlay.classList.add('editing');
            if (ZBZ.LayoutEditor && state.layout) ZBZ.LayoutEditor.attach(overlay, state.layout, onLayoutChanged);
            if (ZBZ.TranscriptionEditor) ZBZ.TranscriptionEditor.detach(refs.textBody);
        } else if (mode === 'text') {
            refs.layoutToolbar.classList.add('hidden');
            if (overlay) overlay.classList.remove('editing');
            if (ZBZ.LayoutEditor) ZBZ.LayoutEditor.detach();
            ensureTextEditableState();
        } else {
            refs.layoutToolbar.classList.add('hidden');
            if (overlay) overlay.classList.remove('editing');
            if (ZBZ.LayoutEditor) ZBZ.LayoutEditor.detach();
            if (ZBZ.TranscriptionEditor) ZBZ.TranscriptionEditor.detach(refs.textBody);
        }
    }

    function setTextSource(src) {
        state.textSource = src;
        refs.textSourceBtns.forEach(b => b.setAttribute('aria-pressed', b.getAttribute('data-text-source') === src ? 'true' : 'false'));
        renderTextPanel();
    }

    // ============================================================ Downloads ============================================================

    function downloadLayout() {
        if (!state.doc || !state.layout) { ZBZ.toast('Keine Layout-Daten', 'warn'); return; }
        ZBZ.Download.layout(state.doc.id, state.page, state.layout.regions, {
            source: 'curated',
            original_source: state.layout.source || 'gemini'
        });
    }
    function downloadText() {
        if (!state.doc) return;
        const content = (state._currentEditedText != null) ? state._currentEditedText : state._currentText;
        if (!content) { ZBZ.toast('Kein Text geladen', 'warn'); return; }
        ZBZ.Download.text(state.doc.id, state.page, content);
    }
    async function downloadTei() {
        if (!state.doc) return;
        let xml = state._currentEditedText;
        if (!xml || state.textSource !== 'xml') {
            xml = await loadTeiFinal(state.doc.id);
        }
        if (!xml) { ZBZ.toast('Kein TEI verfuegbar', 'warn'); return; }
        ZBZ.Download.tei(state.doc.id, xml, 'curated');
    }

    // ============================================================ Events ============================================================

    function bindEvents() {
        refs.btnPrev.addEventListener('click', () => { state.page = Math.max(1, state.page - 1); loadPage(); });
        refs.btnNext.addEventListener('click', () => {
            const max = state.doc ? (state.doc.page_count || 1) : 1;
            state.page = Math.min(max, state.page + 1);
            loadPage();
        });

        document.addEventListener('keydown', (e) => {
            if (e.target.matches('input, textarea, select, [contenteditable="true"]')) return;
            if (e.key === 'ArrowLeft')      refs.btnPrev.click();
            else if (e.key === 'ArrowRight') refs.btnNext.click();
        });

        refs.modeBtns.forEach(b => b.addEventListener('click', () => setMode(b.getAttribute('data-mode'))));
        refs.textSourceBtns.forEach(b => b.addEventListener('click', () => setTextSource(b.getAttribute('data-text-source'))));

        refs.ocrSourceSel.addEventListener('change', () => {
            state.ocrSource = refs.ocrSourceSel.value;
            if (state.textSource === 'ocr') renderTextPanel();
        });

        refs.btnDlLayout.addEventListener('click', downloadLayout);
        refs.btnDlText.addEventListener('click', downloadText);
        refs.btnDlTei.addEventListener('click', downloadTei);
    }

    ZBZ.Viewer = { init, state };
    document.addEventListener('DOMContentLoaded', init);
})();
