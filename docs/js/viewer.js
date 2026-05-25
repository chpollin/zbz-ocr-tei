/**
 * viewer.js — Orchestrator
 *
 * Verantwortlich fuer:
 *  - Doc-Liste in der Sidebar (Filter, Suche, Selektion)
 *  - Seitennavigation
 *  - Mode-Switching (view / layout / text)
 *  - Daten-Loader (catalog, layout, OCR, TEI)
 *  - Synchronisation zwischen Faksimile und Text-Panel
 *
 * Namespace: ZBZ.Viewer
 */
(function () {
    'use strict';

    const $ = ZBZ.$;
    const $$ = ZBZ.$$;

    // ---- State ----
    const state = {
        catalog: null,        // catalog.json
        filteredDocs: [],     // gefilterte Doc-Liste fuer Sidebar
        doc: null,            // aktuell ausgewaehltes Doc-Objekt
        page: 1,
        mode: 'view',         // view | layout | text
        textSource: 'ocr',    // ocr | tei | xml
        ocrSource: 'mistral',
        layout: null,         // { regions: [...], _meta }
        teiXml: null,         // string
        filters: { types: new Set(), demoOnly: false, query: '' }
    };

    const cache = new ZBZ.Cache(40);

    // ---- DOM-Refs ----
    const refs = {
        docList:        $('#doc-list'),
        docCount:       $('#doc-count'),
        docSearch:      $('#doc-search'),
        docMeta:        $('#doc-meta'),
        chipFilters:    $$('.filter-chip'),
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
        await loadCatalog();

        // URL-State (?doc=2310&page=2)
        const urlDoc = ZBZ.getParam('doc');
        const urlPage = parseInt(ZBZ.getParam('page'), 10);
        if (urlDoc && state.catalog) {
            const d = findDoc(urlDoc);
            if (d) {
                await selectDoc(d, isNaN(urlPage) ? 1 : urlPage);
            }
        }

        ZBZ.log('Viewer', 'init done');
    }

    // ============================================================ Catalog ============================================================

    async function loadCatalog() {
        const data = await ZBZ.fetchJSON('data/catalog.json');
        if (!data) {
            refs.docList.innerHTML = '<div class="empty">catalog.json nicht gefunden. <code>python -m scripts.generate_edition_data</code></div>';
            return;
        }
        state.catalog = data;
        applyFilters();
    }

    function findDoc(id) {
        if (!state.catalog) return null;
        const list = state.catalog.docs || state.catalog.documents || [];
        return list.find(d => String(d.id) === String(id)) || null;
    }

    function applyFilters() {
        if (!state.catalog) return;
        const all = state.catalog.docs || state.catalog.documents || [];
        const q = state.filters.query.trim().toLowerCase();
        state.filteredDocs = all.filter(d => {
            if (state.filters.types.size > 0 && !state.filters.types.has(d.type)) return false;
            if (state.filters.demoOnly && !d.demo) return false;
            if (q) {
                const hay = (d.id + ' ' + (d.title || '') + ' ' + (d.author || '')).toLowerCase();
                if (!hay.includes(q)) return false;
            }
            return true;
        });
        renderDocList();
    }

    function renderDocList() {
        refs.docList.innerHTML = '';
        if (state.filteredDocs.length === 0) {
            refs.docList.innerHTML = '<div class="empty">Keine Dokumente.</div>';
            refs.docCount.textContent = '0 / ' + ((state.catalog.docs || []).length || 0);
            return;
        }
        const frag = document.createDocumentFragment();
        state.filteredDocs.forEach(d => {
            const isActive = state.doc && state.doc.id === d.id;
            const item = ZBZ.el('button', {
                cls: 'doc-item',
                attrs: { 'data-doc-id': d.id, 'aria-current': isActive ? 'true' : 'false', type: 'button' },
                html: `<div><span class="doc-item__id">${ZBZ.esc(d.id)}</span><span class="doc-item__title">${ZBZ.esc(d.title || '—')}</span></div>` +
                      `<div class="doc-item__meta">${ZBZ.esc(d.lang || '')} · ${ZBZ.esc(d.type || '')} · ${d.page_count || '?'} S.${d.demo ? ' · <span class="badge badge--info">DEMO</span>' : ''}</div>`,
                on: { click: () => selectDoc(d) }
            });
            frag.appendChild(item);
        });
        refs.docList.appendChild(frag);
        refs.docCount.textContent = state.filteredDocs.length + ' / ' + ((state.catalog.docs || []).length || 0);
    }

    // ============================================================ Doc selektieren ============================================================

    async function selectDoc(doc, startPage) {
        state.doc = doc;
        state.page = startPage || 1;
        state.layout = null;
        state.teiXml = null;
        ZBZ.setParams({ doc: doc.id, page: state.page });

        // Doc-Meta im Header
        refs.docMeta.innerHTML =
            `<strong>${ZBZ.esc(doc.id)}</strong> · ${ZBZ.esc(doc.title || '')} · ${ZBZ.esc(doc.author || '—')} · ${ZBZ.esc(doc.lang || '')} · Typ ${ZBZ.esc(doc.type || '')} · ${doc.page_count || '?'} S.` +
            (doc.screening ? ` · <span class="badge badge--info">${ZBZ.esc(doc.screening)}</span>` : '');

        // Doc-Liste aktiv-Status
        $$('.doc-item', refs.docList).forEach(b => b.setAttribute('aria-current', b.getAttribute('data-doc-id') === doc.id ? 'true' : 'false'));

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

        // Faksimile + Layout
        await renderFacsimile();
        // Text-Panel (gemaess textSource)
        await renderTextPanel();
    }

    async function renderFacsimile() {
        const doc = state.doc, page = state.page;
        refs.imageBody.innerHTML = '';

        const facs = ZBZ.el('div', { cls: 'facsimile' });
        const img = ZBZ.el('img', {
            cls: 'facsimile__img',
            attrs: { src: ZBZ.path.image(doc.id, page), alt: 'Faksimile Seite ' + page }
        });
        img.addEventListener('error', () => {
            refs.imageBody.innerHTML = '<div class="empty">Faksimile nicht verfuegbar. (' + ZBZ.path.image(doc.id, page) + ')</div>';
        });

        const overlay = ZBZ.el('div', { cls: 'facsimile__overlay', attrs: { id: 'layout-overlay' } });
        facs.appendChild(img);
        facs.appendChild(overlay);
        refs.imageBody.appendChild(facs);

        // Layout laden (Gemini > Docling)
        const layout = await fetchLayout(doc.id, page);
        state.layout = layout;
        if (layout && layout.regions) {
            refs.regionCount.textContent = layout.regions.length + ' Regionen';
            renderRegionOverlay(overlay, layout.regions);
        } else {
            refs.regionCount.textContent = 'keine Layout-Daten';
        }

        // Editor-Modus aktivieren, wenn nötig
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
        // Re-Render Overlay (Editor laeuft separat, behandelt Drag-Visualisierung)
    }

    // ============================================================ Text-Panel ============================================================

    async function renderTextPanel() {
        const doc = state.doc, page = state.page;
        refs.textBody.innerHTML = '<div class="empty">Lade…</div>';

        if (state.textSource === 'ocr') {
            refs.textTitle.textContent = 'OCR · ' + state.ocrSource;
            const urls = ZBZ.path.ocr(state.ocrSource, doc.id, page);
            const res = await ZBZ.fetchFirstOk(urls);
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
        // Aktiviert contenteditable im Text-Editor-Modus
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
        // Wenn aktuell XML-Modus + editierter Text vorhanden: den nutzen.
        let xml = state._currentEditedText;
        if (!xml || state.textSource !== 'xml') {
            // sonst Final-TEI laden
            xml = await loadTeiFinal(state.doc.id);
        }
        if (!xml) { ZBZ.toast('Kein TEI verfuegbar', 'warn'); return; }
        ZBZ.Download.tei(state.doc.id, xml, 'curated');
    }

    // ============================================================ Events ============================================================

    function bindEvents() {
        // Page-Nav
        refs.btnPrev.addEventListener('click', () => { state.page = Math.max(1, state.page - 1); loadPage(); });
        refs.btnNext.addEventListener('click', () => {
            const max = state.doc ? (state.doc.page_count || 1) : 1;
            state.page = Math.min(max, state.page + 1);
            loadPage();
        });
        document.addEventListener('keydown', (e) => {
            if (e.target.matches('input, textarea, [contenteditable="true"]')) return;
            if (e.key === 'ArrowLeft') refs.btnPrev.click();
            else if (e.key === 'ArrowRight') refs.btnNext.click();
        });

        // Sidebar
        refs.docSearch.addEventListener('input', ZBZ.debounce((e) => {
            state.filters.query = e.target.value;
            applyFilters();
        }, 200));
        refs.chipFilters.forEach(chip => {
            chip.addEventListener('click', () => {
                const pressed = chip.getAttribute('aria-pressed') === 'true';
                chip.setAttribute('aria-pressed', pressed ? 'false' : 'true');
                if (chip.dataset.type) {
                    if (pressed) state.filters.types.delete(chip.dataset.type);
                    else state.filters.types.add(chip.dataset.type);
                } else if (chip.dataset.demo) {
                    state.filters.demoOnly = !pressed;
                }
                applyFilters();
            });
        });

        // Mode
        refs.modeBtns.forEach(b => b.addEventListener('click', () => setMode(b.getAttribute('data-mode'))));
        refs.textSourceBtns.forEach(b => b.addEventListener('click', () => setTextSource(b.getAttribute('data-text-source'))));

        // OCR-Source
        refs.ocrSourceSel.addEventListener('change', () => {
            state.ocrSource = refs.ocrSourceSel.value;
            if (state.textSource === 'ocr') renderTextPanel();
        });

        // Downloads
        refs.btnDlLayout.addEventListener('click', downloadLayout);
        refs.btnDlText.addEventListener('click', downloadText);
        refs.btnDlTei.addEventListener('click', downloadTei);
    }

    ZBZ.Viewer = { init, state };
    document.addEventListener('DOMContentLoaded', init);
})();
