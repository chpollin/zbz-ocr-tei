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
    // E60 (2026-05-25): mode -> imageEdit + textEdit (zwei unabhaengige Edit-States).
    const state = {
        catalog: null,
        doc: null,
        page: 1,
        textSource: 'ocr',    // ocr | tei | xml
        ocrSource: 'mistral',
        layout: null,
        teiXml: null,
        osdViewer: null,      // OpenSeadragon-Instanz (nur wenn !imageEdit aktiv)
        imageEdit: false,     // Faksimile-Edit-Toggle: aktiviert Layout-Editor (img + Eigenbau-Overlay)
        textEdit: false,      // Text-Edit-Toggle: aktiviert Transcription-Editor fuer aktive Quelle
        _currentText: null,
        _currentEditedText: null,
        _isBlank: false       // Leerseite (Vorsatz/Rueckseite/Durchschlag) — kein echter Text
    };

    const OSD_PREFIX = 'https://cdn.jsdelivr.net/npm/openseadragon@5.0.1/build/openseadragon/images/';

    const cache = new ZBZ.Cache(40);

    // ---- DOM-Refs ----
    const refs = {
        subbar:         $('#doc-subbar'),
        docMeta:        $('#doc-meta'),
        pageInfo:       $('#page-info'),
        btnPrev:        $('#btn-prev'),
        btnNext:        $('#btn-next'),
        btnImageEdit:   $('#btn-image-edit'),
        btnTextEdit:    $('#btn-text-edit'),
        textSourceBtns: $$('.mode-btn[data-text-source]'),
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
        renderDocMeta(doc);

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

        // Leerseite vorab bestimmen (aus Mistral-Basis-OCR), damit Faksimile UND Text
        // konsistent reagieren: keine Phantom-Regionen, kein OCR-Muell.
        state._isBlank = await detectBlankPage(doc.id, page);

        await renderFacsimile();
        await renderTextPanel();
    }

    async function detectBlankPage(doc, page) {
        const ck = 'blank:' + doc + ':' + page;
        if (cache.has(ck)) return cache.get(ck);
        const res = await ZBZ.fetchFirstOk(ZBZ.path.ocr('mistral', doc, page));
        const blank = res ? ZBZ.isBlankPageText(res.text) : false;
        cache.set(ck, blank);
        return blank;
    }

    async function renderFacsimile() {
        // Alten OSD-Viewer immer destroyen vor Re-Render
        destroyOsd();
        refs.imageBody.innerHTML = '';

        if (state.imageEdit) {
            await renderFacsimileImg();
        } else {
            await renderFacsimileOsd();
        }
    }

    function destroyOsd() {
        if (state.osdViewer) {
            try { state.osdViewer.destroy(); } catch (e) { /* ignore */ }
            state.osdViewer = null;
        }
    }

    // ---- OSD-Variante (View-Modus, pan + zoom) ----
    async function renderFacsimileOsd() {
        const doc = state.doc, page = state.page;
        refs.imageBody.classList.add('panel__body--canvas');

        const container = ZBZ.el('div', { cls: 'facsimile-osd', attrs: { id: 'osd-container' } });
        refs.imageBody.appendChild(container);

        // Layout vorab laden, Overlays werden nach OSD-'open' angehaengt
        const layout = await fetchLayout(doc.id, page);
        state.layout = layout;
        // Leerseite: Phantom-Regionen (Gemini halluziniert Kaesten in den Durchschlag)
        // nicht zeichnen und die irrefuehrende Zahl durch 'Leerseite' ersetzen.
        if (state._isBlank) {
            refs.regionCount.textContent = 'Leerseite';
        } else {
            refs.regionCount.textContent = (layout && layout.regions)
                ? layout.regions.length + ' Regionen'
                : 'keine Layout-Daten';
        }

        const imgUrl = ZBZ.path.image(doc.id, page);
        state.osdViewer = OpenSeadragon({
            element: container,
            tileSources: { type: 'image', url: imgUrl },
            prefixUrl: OSD_PREFIX,
            showNavigator: false,
            showRotationControl: true,
            showFullPageControl: false,
            showHomeControl: true,
            showZoomControl: true,
            gestureSettingsMouse: { clickToZoom: false, scrollToZoom: true },
            minZoomLevel: 0.5,
            maxZoomPixelRatio: 6,
            visibilityRatio: 0.8,
            constrainDuringPan: true,
            animationTime: 0.5,
            navigationControlAnchor: OpenSeadragon.ControlAnchor ? OpenSeadragon.ControlAnchor.TOP_LEFT : undefined
        });

        state.osdViewer.addHandler('open', () => {
            if (!state._isBlank && layout && layout.regions) addOsdOverlays(state.osdViewer, layout.regions);
        });

        state.osdViewer.addHandler('open-failed', () => {
            refs.imageBody.innerHTML =
                '<div class="empty">Faksimile nicht verfuegbar fuer Seite ' + page +
                '<br><code style="font-size:0.85em">' + ZBZ.esc(imgUrl) + '</code></div>';
        });
    }

    function addOsdOverlays(viewer, regions) {
        const tiledImage = viewer.world.getItemAt(0);
        if (!tiledImage) return;
        const cs = tiledImage.getContentSize();
        regions.forEach((r, idx) => {
            if (!r.bbox) return;
            const div = ZBZ.el('div', {
                cls: 'region ' + ZBZ.regionTypeCls(r.zbz_tag),
                attrs: { 'data-region-idx': idx, title: r.text || ZBZ.regionTypeLabel(r.zbz_tag) }
            });
            const loc = viewer.viewport.imageToViewportRectangle(
                r.bbox.x_pct / 100 * cs.x,
                r.bbox.y_pct / 100 * cs.y,
                r.bbox.w_pct / 100 * cs.x,
                r.bbox.h_pct / 100 * cs.y
            );
            viewer.addOverlay({ element: div, location: loc });
        });
    }

    // ---- Img-Variante (Layout-Edit-Modus, statisch, mit altem Editor) ----
    async function renderFacsimileImg() {
        const doc = state.doc, page = state.page;
        refs.imageBody.classList.remove('panel__body--canvas');

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

        if (state.imageEdit && ZBZ.LayoutEditor) {
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

    function textPanelTitle() {
        if (state.textSource === 'tei') return 'TEI · gerendert';
        if (state.textSource === 'xml') return 'TEI · XML';
        return 'OCR · ' + state.ocrSource;
    }

    async function renderTextPanel() {
        const doc = state.doc, page = state.page;

        // Leerseite: ruhiger Hinweis statt OCR-Muell ('.', '^{}[]', leere Tabelle).
        // Im Text-Edit-Modus normal rendern, damit der Rohtext bei Bedarf bereinigt werden kann.
        if (state._isBlank && !state.textEdit) {
            refs.textTitle.textContent = textPanelTitle();
            refs.textBody.innerHTML = '';
            refs.textBody.appendChild(ZBZ.el('div', {
                cls: 'empty empty--blank-page', text: 'Leerseite — kein Text'
            }));
            state._currentText = null;
            return;
        }

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
        // Im Text-Edit-Modus erwartet der Editor den Markdown-Rohtext im DOM.
        // Sonst wird Markdown -> HTML gerendert fuer Lesbarkeit.
        if (state.textEdit) {
            const div = ZBZ.el('div', { cls: 'text text--raw', text });
            refs.textBody.appendChild(div);
        } else {
            const html = ZBZ.renderMarkdown(text || '');
            const div = ZBZ.el('div', { cls: 'text', html });
            refs.textBody.appendChild(div);
        }
        ensureTextEditableState();
    }

    function renderDocMeta(doc) {
        const meta = refs.docMeta;
        meta.innerHTML = '';
        const parts = [];
        const idSpan = ZBZ.el('span', { cls: 'meta-item meta-item--id' });
        idSpan.appendChild(ZBZ.el('strong', { text: String(doc.id) }));
        parts.push(idSpan);
        if (doc.title)  parts.push(ZBZ.el('span', { cls: 'meta-item meta-item--title', text: doc.title }));
        if (doc.author) parts.push(ZBZ.el('span', { cls: 'meta-item', text: doc.author }));
        if (doc.lang)   parts.push(ZBZ.el('span', { cls: 'meta-item', text: doc.lang }));
        parts.push(ZBZ.el('span', { cls: 'meta-item', text: 'Typ ' + (doc.type || '—') }));
        parts.push(ZBZ.el('span', { cls: 'meta-item', text: (doc.page_count || '?') + ' S.' }));
        parts.forEach((node, i) => {
            if (i > 0) meta.appendChild(ZBZ.el('span', { cls: 'sep', text: '·' }));
            meta.appendChild(node);
        });
        if (doc.screening) {
            const badge = ZBZ.el('span', {
                cls: 'badge badge--screening badge--' + String(doc.screening).toLowerCase().replace(/[^a-z0-9]+/g, '-'),
                text: doc.screening
            });
            meta.appendChild(badge);
        }
    }

    function ensureTextEditableState() {
        if (state.textEdit && ZBZ.TranscriptionEditor) {
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

    // ============================================================ Edit-Toggles (E60) ============================================================

    function setImageEdit(on) {
        const prev = state.imageEdit;
        state.imageEdit = !!on;
        refs.btnImageEdit.setAttribute('aria-pressed', state.imageEdit ? 'true' : 'false');

        // Layout-Toolbar toggle (zeigt + Region, Loeschen, Typ-Selector)
        refs.layoutToolbar.classList.toggle('hidden', !state.imageEdit);

        if (prev !== state.imageEdit) {
            // Editor immer detachen vor Re-Render (greift auf altes DOM zu)
            if (ZBZ.LayoutEditor) ZBZ.LayoutEditor.detach();
            // Faksimile-Variante wechselt: OSD (view) <-> img (edit). renderFacsimileImg() attached Editor.
            renderFacsimile();
        }
    }

    function setTextEdit(on) {
        const prev = state.textEdit;
        state.textEdit = !!on;
        refs.btnTextEdit.setAttribute('aria-pressed', state.textEdit ? 'true' : 'false');

        if (prev === state.textEdit) return;

        // Editor immer detachen bevor Mode-Wechsel; ensureTextEditableState() re-attached wenn noetig
        if (ZBZ.TranscriptionEditor) ZBZ.TranscriptionEditor.detach(refs.textBody);

        // OCR-Panel rendering wechselt: gerenderter Markdown <-> Rohtext.
        // renderTextPanel() deckt Leerseite (Hinweis) und Edit/Lese-Modus konsistent ab.
        if (state.textSource === 'ocr') {
            renderTextPanel();
        } else {
            ensureTextEditableState();
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

        refs.btnImageEdit.addEventListener('click', () => setImageEdit(!state.imageEdit));
        refs.btnTextEdit.addEventListener('click', () => setTextEdit(!state.textEdit));
        refs.textSourceBtns.forEach(b => b.addEventListener('click', () => setTextSource(b.getAttribute('data-text-source'))));

        refs.btnDlLayout.addEventListener('click', downloadLayout);
        refs.btnDlText.addEventListener('click', downloadText);
        refs.btnDlTei.addEventListener('click', downloadTei);
    }

    ZBZ.Viewer = { init, state };
    document.addEventListener('DOMContentLoaded', init);
})();
