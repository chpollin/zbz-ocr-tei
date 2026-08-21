/**
 * viewer-page.js - Page rendering: facsimile, layout overlay, text panel, edit modes
 *
 * Loads one page of the current document into both panels: the facsimile with its
 * layout regions on the left, the chosen text view on the right. Owns the view and
 * edit dropdown state and the page navigation.
 *
 * Namespace: ZBZ.Viewer
 */
(function () {
    'use strict';

    const $  = ZBZ.$;
    const $$ = ZBZ.$$;
    const V = ZBZ.Viewer;
    const state = V.state;
    const refs  = V.refs;
    const cache = V.cache;
    const { OSD_PREFIX, facsMapPath, candidates } = V;

    // Sibling modules, resolved through ZBZ.Viewer at call time (load order independent).
    const closeDropdown          = (...a) => V.closeDropdown(...a);
    const confirmLeavePage       = (...a) => V.confirmLeavePage(...a);
    const autoStartArbeit        = (...a) => V.autoStartArbeit(...a);
    const loadEntityPage         = (...a) => V.loadEntityPage(...a);
    const decorateEntityMentions = (...a) => V.decorateEntityMentions(...a);
    const markWorklistCandidates = (...a) => V.markWorklistCandidates(...a);
    const worklistEntries        = (...a) => V.worklistEntries(...a);
    const renderUnplacedWorklist = (...a) => V.renderUnplacedWorklist(...a);
    const closeEntityPopover     = (...a) => V.closeEntityPopover(...a);

    // ---- Panel dropdowns ----
    // A view is a combination of text source, markup highlighting and entity mode; the
    // dropdown names the combination, the state fields below it stay the ones the
    // separate buttons drove.
    const VIEW_LABEL = { text: 'Text', ocr: 'OCR', xml: 'XML' };
    const EDIT_LABEL = { layout: 'Layout', ocr: 'OCR', xml: 'XML' };
    const CARET = ' ▾';
    // Menu tooltips as authored in the markup; entity mode swaps some for a hint.
    const VIEW_TITLES = {};
    refs.viewItems.forEach(i => { VIEW_TITLES[i.getAttribute('data-view')] = i.title; });
    const EDIT_TITLES = {};
    refs.editItems.forEach(i => { EDIT_TITLES[i.getAttribute('data-edit')] = i.title; });
    // Region count of the current page: shown in the layout toolbar, and in the tooltip
    // of the layout entry so it stays reachable while reading.
    let regionCountText = '';

    // Only the newest page load may render (rapid paging overlaps async fetches)
    let pageLoadSeq = 0;

    async function loadPage() {
        if (!state.doc) return;
        const seq = ++pageLoadSeq;
        const doc = state.doc, page = state.page;
        // Page change: layout/text are per-page, so the dirty state of the old page
        // expires (manifest dirty persists as it is per-document).
        state.layoutDirty = false;
        state.textDirty = false;
        state._currentEditedText = null;
        ZBZ.bus.emit('dirty:changed');
        syncPageInput();
        refs.btnPrev.disabled = page <= 1;
        refs.btnNext.disabled = page >= textPageCount();
        ZBZ.setParams({ page });
        ZBZ.bus.emit('page:changed', page);

        // Detect blank page upfront (from Mistral base OCR) so facsimile AND text
        // respond consistently: no phantom regions, no OCR garbage.
        state._isBlank = await detectBlankPage(doc.id, page);
        if (seq !== pageLoadSeq) return;

        await renderFacsimile();
        if (seq !== pageLoadSeq) return;
        await renderTextPanel();
    }

    async function detectBlankPage(doc, page) {
        // E63 step 3: primarily read the <pb type="blank"/> marker from the per-page TEI
        // (deterministic, projected by the corpus script). Falls back to the
        // OCR heuristic (isBlankPageText) if the per-page TEI is missing.
        const ck = 'blank:' + doc + ':' + page;
        if (cache.has(ck)) return cache.get(ck);
        let blank = false;
        const tei = await loadTeiPage(doc, page);
        if (tei) {
            blank = /<pb\b[^>]*\btype\s*=\s*"blank"/i.test(tei);
        } else {
            const res = await ZBZ.fetchFirstOk(candidates('ocr', page, ZBZ.path.ocr('mistral', doc, page)));
            blank = res ? ZBZ.isBlankPageText(res.text) : false;
        }
        cache.set(ck, blank);
        return blank;
    }

    // The count lives in the layout toolbar (visible while editing) and in the tooltip of
    // the layout entry, so it stays readable in view mode.
    function setRegionCount(text) {
        regionCountText = text || '';
        if (refs.regionCount) refs.regionCount.textContent = regionCountText;
        updateEditButtons();
    }

    // The generator resolves pb@facs against the <surface>/<graphic> of the final TEI and
    // writes the result per document. A missing sidecar, or a page missing from it, keeps
    // the sequential convention of ZBZ.path.image.
    async function loadFacsMap(docId) {
        const j = await ZBZ.fetchJSON(facsMapPath(docId));
        state.facsMap = (j && j.facs_image) || null;
    }

    function facsImageUrl(docId, page) {
        const name = state.facsMap && state.facsMap[String(page)];
        return name ? ZBZ.path.imageFile(docId, name) : ZBZ.path.image(docId, page);
    }

    // Paging runs over text pages. `page_count` in the catalog counts scans, so a document
    // with double-page spreads would cut its last text pages off the navigation.
    function textPageCount() {
        const fromCatalog = (state.doc && state.doc.page_count) || 1;
        if (!state.facsMap) return fromCatalog;
        const pages = Object.keys(state.facsMap).map(Number).filter(n => !isNaN(n));
        return Math.max(fromCatalog, pages.length ? Math.max.apply(null, pages) : 0);
    }

    async function renderFacsimile() {
        // Always destroy the old OSD viewer before re-rendering
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

    // ---- OSD variant (view mode, pan + zoom) ----
    async function renderFacsimileOsd() {
        const doc = state.doc, page = state.page;
        refs.imageBody.classList.add('panel__body--canvas');

        const container = ZBZ.el('div', { cls: 'facsimile-osd', attrs: { id: 'osd-container' } });
        refs.imageBody.appendChild(container);

        // Loading hint: OSD loads the full (often several MB) PNG untiled and decodes it
        // before the first render, so without a hint the panel would stay blank for seconds.
        // Removed on 'open' (success) or replaced by an error message on 'open-failed'.
        const loading = ZBZ.el('div', { cls: 'facsimile-loading', text: 'Loading facsimile...' });
        refs.imageBody.appendChild(loading);

        // Load layout upfront; overlays are attached after OSD 'open'
        const layout = await fetchLayout(doc.id, page);
        if (state.doc !== doc || state.page !== page || state.imageEdit) return; // race guard
        state.layout = layout;
        // Blank page: do not draw phantom regions (Gemini hallucinates boxes on carbon copies)
        // and replace the misleading count with a blank-page label.
        if (state._isBlank) {
            setRegionCount('Blank page, no text');
        } else {
            setRegionCount((layout && layout.regions)
                ? layout.regions.length + ' regions'
                : 'no layout data');
        }

        const imgUrl = facsImageUrl(doc.id, page);
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

        // handlers must not touch a newer viewer instance after rapid paging
        const viewer = state.osdViewer;
        viewer.addHandler('open', () => {
            if (state.osdViewer !== viewer) return;
            loading.remove();
            if (!state._isBlank && layout && layout.regions) addOsdOverlays(viewer, layout.regions);
        });

        viewer.addHandler('open-failed', () => {
            if (state.osdViewer !== viewer) return;
            destroyOsd(); // before innerHTML, else canvas + listeners leak
            refs.imageBody.innerHTML =
                '<div class="empty">Facsimile not available for page ' + page +
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

    // ---- Img variant (layout edit mode, static, with custom editor) ----
    async function renderFacsimileImg() {
        const doc = state.doc, page = state.page;
        refs.imageBody.classList.remove('panel__body--canvas');

        const facs = ZBZ.el('div', { cls: 'facsimile' });
        const imgUrl = facsImageUrl(doc.id, page);
        const img = ZBZ.el('img', {
            cls: 'facsimile__img',
            attrs: { src: imgUrl, alt: 'Facsimile page ' + page, loading: 'eager' }
        });
        img.addEventListener('error', () => {
            refs.imageBody.innerHTML =
                '<div class="empty">Facsimile not available for page ' + page +
                '<br><code style="font-size:0.85em">' + ZBZ.esc(imgUrl) + '</code></div>';
        });

        const overlay = ZBZ.el('div', { cls: 'facsimile__overlay', attrs: { id: 'layout-overlay' } });
        facs.appendChild(img);
        facs.appendChild(overlay);
        refs.imageBody.appendChild(facs);

        const layout = await fetchLayout(doc.id, page);
        if (state.doc !== doc || state.page !== page || !state.imageEdit) return;
        state.layout = layout;
        if (layout && layout.regions) {
            setRegionCount(layout.regions.length + ' regions');
            renderRegionOverlay(overlay, layout.regions);
        } else {
            setRegionCount('no layout data');
        }

        if (state.imageEdit && ZBZ.LayoutEditor) {
            ZBZ.LayoutEditor.attach(overlay, layout, onLayoutChanged);
        }
    }

    async function fetchLayout(doc, page) {
        const ck = 'layout:' + doc + ':' + page;
        if (cache.has(ck)) return cache.get(ck);
        const j = await ZBZ.fetchFirstJsonOk(candidates('layout_curated', page, ZBZ.path.layoutCurated(doc, page)))
              || await ZBZ.fetchFirstJsonOk(candidates('layout_gemini', page, ZBZ.path.layoutGemini(doc, page)))
              || await ZBZ.fetchFirstJsonOk(candidates('layout', page, ZBZ.path.layoutDocling(doc, page)));
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
        setRegionCount(regions.length + ' regions (edited)');
        state.layoutDirty = true;
        ZBZ.bus.emit('dirty:changed');
        // E66: first real layout change -> set stream to in_arbeit
        autoStartArbeit('layout');
    }

    // ============================================================ Text panel ============================================================

    async function renderTextPanel() {
        const doc = state.doc, page = state.page;
        const src = state.textSource;
        state.entityPage = false;
        closeEntityPopover(false);
        // True once doc/page/source changed mid-fetch -- a stale response must not render.
        const stale = () => (state.doc !== doc || state.page !== page || state.textSource !== src);

        // Blank page: show a quiet notice instead of OCR garbage ('.', '^{}[]', empty table).
        // In text edit mode render normally so the raw text can be cleaned if needed.
        // XML mode is exempt (it shows the TEI source, blank or not).
        if (state._isBlank && !state.textEdit && state.textSource !== 'xml') {
            refs.textBody.innerHTML = '';
            refs.textBody.appendChild(ZBZ.el('div', {
                cls: 'empty empty--blank-page', text: 'Blank page, no text'
            }));
            state._currentText = null;
            return;
        }

        refs.textBody.innerHTML = '<div class="empty">Loading...</div>';

        if (state.textSource === 'ocr') {
            const res = await ZBZ.fetchFirstOk(candidates('ocr', page, ZBZ.path.ocr(state.ocrSource, doc.id, page)));
            if (stale()) return;
            if (!res) {
                renderLoadError('No OCR data for ' + state.ocrSource + ' / page ' + page);
                state._currentText = null;
                return;
            }
            state._currentText = res.text;
            renderOcrText(res.text);
        }
        else if (state.textSource === 'tei') {
            // Entity mode takes the entity preview as the TEI source of this view; a page
            // without one (404) falls back to the pipeline TEI.
            let xml = null;
            if (state.entityMode && state.entityAvailable) {
                xml = await loadEntityPage(doc.id, page);
                if (stale()) return;
                state.entityPage = xml != null;
            }
            if (!xml) {
                xml = await loadTeiPage(doc.id, page);
                if (stale()) return;
            }
            if (!xml) {
                renderLoadError('No TEI for page ' + page);
                return;
            }
            // The entity preview is never a save source; keep the pipeline TEI in state.
            if (!state.entityPage) state.teiXml = xml;
            ZBZ.TeiRender.render(xml, refs.textBody);
            // Mark before the legend is built: its candidate count reads the DOM.
            let unplaced = [];
            if (state.entityPage) {
                decorateEntityMentions();
                unplaced = markWorklistCandidates(page);
            } else if (state.entityMode) {
                state.entityCandidates = worklistEntries(page);
                unplaced = state.entityCandidates.slice();
            }
            applyTeiMarkup();
            if (state.entityMode) renderUnplacedWorklist(unplaced);
        }
        else if (state.textSource === 'xml') {
            // Default scope is the current page slice. The final TEI of a large document
            // approaches a megabyte and rendering it on every open froze the panel, so the
            // full document is loaded on request only. It stays the ONLY editable scope:
            // saving overwrites {doc}_final.xml as a whole (E72), so an edited page slice
            // would destroy the rest of the document.
            const full = state.xmlScope === 'full';
            const xml = full ? await loadTeiFinal(doc.id) : await loadTeiPage(doc.id, page);
            if (stale()) return;
            if (!xml) {
                renderLoadError(full ? 'No final TEI for document ' + doc.id : 'No TEI for page ' + page);
                renderXmlScopeBar(0);
                return;
            }
            if (full) state.teiXml = xml;
            ZBZ.TeiRender.renderXml(xml, refs.textBody);
            renderXmlScopeBar(xml.length);
            if (full) ensureTextEditableState();
        }
    }

    // Names the active XML scope and switches it. The page slice is read-only; the full
    // document carries the editor and the save path.
    function renderXmlScopeBar(chars) {
        const full = state.xmlScope === 'full';
        const bar = ZBZ.el('div', { cls: 'xml-scope' });
        const size = chars ? ' · ' + Math.max(1, Math.round(chars / 1024)) + ' KB' : '';
        bar.appendChild(ZBZ.el('span', {
            cls: 'xml-scope__label',
            text: (full ? 'Full document' : 'Page ' + state.page + ' only') + size
        }));
        bar.appendChild(ZBZ.el('button', {
            cls: 'btn btn--sm',
            text: full ? 'Show current page' : 'Load full document',
            attrs: {
                title: full
                    ? 'Back to the page slice: loads fast and stays read-only.'
                    : 'Load the complete final TEI. Required for XML editing; very large documents render without syntax highlighting.'
            },
            on: { click: () => setXmlScope(full ? 'page' : 'full') }
        }));
        if (!full) bar.appendChild(ZBZ.el('span', { cls: 'xml-scope__hint', text: 'read-only' }));
        refs.textBody.insertBefore(bar, refs.textBody.firstChild);
    }

    // Leaving the full scope also leaves edit mode: the editor must never hold a page slice,
    // whose save would replace the whole final TEI.
    function setXmlScope(scope) {
        if (state.xmlScope === scope) return;
        if (scope !== 'full' && state.textDirty) {
            if (!window.confirm('Unsaved TEI changes will be lost when leaving the full document view. Continue?')) return;
            state.textDirty = false;
            state._currentEditedText = null;
            ZBZ.bus.emit('dirty:changed');
        }
        if (scope !== 'full' && state.textEdit) {
            state.textEdit = false;
            updateEditButtons();
        }
        if (ZBZ.TranscriptionEditor) ZBZ.TranscriptionEditor.detach(refs.textBody);
        state.xmlScope = scope;
        renderTextPanel();
    }

    // Failed loads: name the cause (missing file vs network) and offer a retry.
    function renderLoadError(what) {
        const cause = (ZBZ.lastFetchError === 'network')
            ? 'Network error, check connection.'
            : 'File not found (404).';
        refs.textBody.innerHTML = '';
        const box = ZBZ.el('div', { cls: 'empty' });
        box.appendChild(ZBZ.el('div', { text: what + '. ' + cause }));
        box.appendChild(ZBZ.el('button', {
            cls: 'btn btn--sm empty__retry',
            text: 'Retry',
            on: { click: () => renderTextPanel() }
        }));
        refs.textBody.appendChild(box);
    }

    function renderOcrText(text) {
        refs.textBody.innerHTML = '';
        // In text edit mode the editor expects the raw Markdown in the DOM.
        // Otherwise Markdown is rendered to HTML for readability.
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
        parts.push(ZBZ.el('span', { cls: 'meta-item', text: 'Type ' + (doc.type || '—') }));
        parts.push(ZBZ.el('span', { cls: 'meta-item', text: (doc.page_count || '?') + ' pp.' }));
        parts.forEach((node, i) => {
            if (i > 0) meta.appendChild(ZBZ.el('span', { cls: 'sep', text: '·' }));
            meta.appendChild(node);
        });
        // E66: screening badge replaced by the workflow status pills next to this meta row.
    }

    function ensureTextEditableState() {
        // Entity mode is strictly read-only: the editor never attaches to the entity file.
        if (state.entityMode) return;
        // The XML editor attaches to the full document only: its save writes the whole
        // {doc}_final.xml, so a page slice under the cursor would drop the rest.
        if (state.textSource === 'xml' && state.xmlScope !== 'full') return;
        if (state.textEdit && ZBZ.TranscriptionEditor) {
            // Bind the stream at attach time: a debounced commit may fire after
            // state.textSource already changed (tab switch mid-debounce).
            const src = state.textSource;
            ZBZ.TranscriptionEditor.attach(refs.textBody, src, (newContent) => {
                state._currentEditedText = newContent;
                state.textDirty = true;
                ZBZ.bus.emit('dirty:changed');
                // E66: first real text change -> set corresponding stream to in_arbeit
                autoStartArbeit(src === 'ocr' ? 'ocr' : 'tei');
            });
        }
    }

    async function loadTeiPage(doc, page) {
        const ck = 'tei:' + doc + ':' + page;
        if (cache.has(ck)) return cache.get(ck);
        const res = await ZBZ.fetchFirstOk(candidates('tei', page, ZBZ.path.teiPage(doc, page)));
        const xml = res ? res.text : null;
        if (xml != null) cache.set(ck, xml); // never cache failures, retry must refetch
        return xml;
    }

    async function loadTeiFinal(doc) {
        const ck = 'tei-final:' + doc;
        if (cache.has(ck)) return cache.get(ck);
        const res = await ZBZ.fetchFirstOk(candidates('final', 0, ZBZ.path.teiFinal(doc)));
        const xml = res ? res.text : null;
        if (xml != null) cache.set(ck, xml);
        return xml;
    }

    // ============================================================ Edit toggles (E60) ============================================================

    function setImageEdit(on) {
        const prev = state.imageEdit;
        state.imageEdit = !!on;
        updateEditButtons();

        // Layout toolbar toggle (shows: add region, delete, type selector)
        refs.layoutToolbar.classList.toggle('hidden', !state.imageEdit);

        if (prev !== state.imageEdit) {
            // Always detach editor before re-rendering (it holds references to the old DOM)
            if (ZBZ.LayoutEditor) ZBZ.LayoutEditor.detach();
            // Facsimile variant switches: OSD (view) <-> img (edit). renderFacsimileImg() attaches the editor.
            renderFacsimile();
            // Note: the status transition unverifiziert -> in_arbeit happens only on the FIRST
            // real region change (onLayoutChanged), not on opening the editor.
        }
    }

    // ---- Markup mode (rendered view): annotation highlighting + legend ----
    // Label / selector / legend-dot modifier; counts come from the rendered DOM.
    // Entity mode splits the generic entity row into the three GND categories.
    const ENTITY_LEGEND = [
        ['Persons',       '.tei__entity--persname[data-ref]', 'person'],
        ['Organisations', '.tei__entity--orgname[data-ref]',  'org'],
        ['Works',         '.tei__bibl[data-ref]',             'work'],
        ['For review',    '.entity-cand',                     'cand']
    ];

    const MARKUP_LEGEND = [
        ['Entities',   '.tei__entity',  'entity'],
        ['Foreign',    '.tei__foreign', 'foreign'],
        ['Footnotes',  '.tei__note',    'note'],
        ['Editorial',  '.tei__corr',    'corr'],
        ['Unclear',    '.tei__unclear', 'unclear'],
        ['Figures',    '.tei__figure',  'figure'],
        ['Links',      '.tei__ref',     'ref'],
        ['Sections',   '.tei__div[data-type]:not([data-type="text"]), .tei__front, .tei__back', 'div']
    ];

    function applyTeiMarkup() {
        syncViewUi();
        const old = refs.textBody.querySelector('.tei-legend');
        if (old) old.remove();
        const wrap = refs.textBody.querySelector('.tei');
        if (!wrap || state.textSource !== 'tei') return;
        wrap.classList.toggle('tei--markup', state.teiMarkup);
        // Category colors of the entity layer hold independently of the markup toggle.
        wrap.classList.toggle('tei--entities', state.entityPage);
        if (!state.teiMarkup && !state.entityPage) return;
        const rows = state.entityPage
            ? ENTITY_LEGEND.concat(MARKUP_LEGEND.filter(row => row[2] !== 'entity'))
            : MARKUP_LEGEND;
        const legend = ZBZ.el('div', { cls: 'tei-legend' });
        let any = false;
        rows.forEach(([label, sel, mod]) => {
            const n = wrap.querySelectorAll(sel).length;
            if (!n) return;
            any = true;
            const chip = ZBZ.el('span', { cls: 'tei-legend__chip tei-legend__chip--' + mod });
            chip.appendChild(ZBZ.el('span', { cls: 'tei-legend__dot' }));
            chip.appendChild(document.createTextNode(label + ' ' + n));
            legend.appendChild(chip);
        });
        if (!any) legend.appendChild(ZBZ.el('span', { cls: 'tei-legend__empty', text: 'No annotations on this page' }));
        refs.textBody.insertBefore(legend, wrap);
    }

    // ---- View dropdown: text source + markup highlighting + entity mode in one control ----

    function currentView() {
        if (state.textSource === 'ocr') return 'ocr';
        if (state.textSource === 'xml') return 'xml';
        return 'text';
    }

    function syncViewUi() {
        const view = currentView();
        if (refs.btnViewMenu) refs.btnViewMenu.textContent = 'View: ' + VIEW_LABEL[view] + CARET;
        refs.viewItems.forEach(item => {
            const v = item.getAttribute('data-view');
            const active = (v === view);
            item.setAttribute('aria-checked', active ? 'true' : 'false');
            item.classList.toggle('menu__item--on', active);
        });
        if (refs.viewToggleMarkup) {
            refs.viewToggleMarkup.setAttribute('aria-checked', state.teiMarkup ? 'true' : 'false');
            refs.viewToggleMarkup.classList.toggle('menu__item--on', state.teiMarkup);
            refs.viewToggleMarkup.disabled = (view !== 'text');
        }
    }

    // Text is the annotated reading view (entity layer on wherever a preview exists);
    // OCR and XML are the specialized source views.
    function setView(view) {
        closeDropdown();
        if (!VIEW_LABEL[view] || view === currentView()) return;
        if (view === 'text') {
            if (state.entityAvailable && !state.entityMode) { setEntityMode(true); syncViewUi(); return; }
            if (state.textSource !== 'tei') setTextSource('tei');
            syncViewUi();
            return;
        }
        const src = (view === 'ocr') ? 'ocr' : 'xml';
        if (src !== state.textSource) setTextSource(src);
        syncViewUi();
    }

    function toggleMarkupHighlight() {
        closeDropdown();
        state.teiMarkup = !state.teiMarkup;
        applyTeiMarkup();
        syncViewUi();
    }

    // ---- Edit dropdown: layout (facsimile), OCR text, TEI-XML ----
    // The rendered TEI view has no edit entry point: it cannot be round-tripped
    // (transcription-editor reads innerText only), save/export take TEI edits
    // exclusively from XML mode.

    function editActive(kind) {
        return (kind === 'layout') ? state.imageEdit : (state.textEdit && state.textSource === kind);
    }

    // Every editing mode is reachable; picking OCR or XML switches the panel to that
    // source first (the annotated reading view itself is never editable).
    function editBlockedReason() {
        return '';
    }

    function updateEditButtons() {
        const on = [];
        refs.editItems.forEach(item => {
            const kind = item.getAttribute('data-edit');
            const active = editActive(kind);
            const blocked = editBlockedReason(kind);
            const hint = (kind === 'layout' && regionCountText) ? ' · ' + regionCountText : '';
            item.setAttribute('aria-checked', active ? 'true' : 'false');
            item.classList.toggle('menu__item--on', active);
            item.disabled = !!blocked;
            item.title = blocked || (EDIT_TITLES[kind] + hint);
            if (active) on.push(EDIT_LABEL[kind]);
        });
        if (!refs.btnEditMenu) return;
        refs.btnEditMenu.textContent = (on.length ? 'Edit: ' + on.join(', ') : 'Edit') + CARET;
        refs.btnEditMenu.classList.toggle('menu-btn--on', on.length > 0);
    }

    function toggleEditMode(kind) {
        closeDropdown();
        if (kind === 'layout') setImageEdit(!state.imageEdit);
        else toggleEdit(kind);
    }

    function toggleEdit(src) {
        if (state.textEdit && state.textSource === src) { setTextEdit(false); return; }
        if (state.textSource !== src && !setTextSource(src)) return; // user kept unsaved edits
        // XML edits are persisted as the whole final TEI (E72), so editing needs the full
        // scope. Load it first; the render callback attaches the editor.
        if (src === 'xml' && state.xmlScope !== 'full') {
            state.xmlScope = 'full';
            state.textEdit = true;
            updateEditButtons();
            ZBZ.toast('XML editing loads the full document.', 'info');
            renderTextPanel();
            return;
        }
        setTextEdit(true);
    }

    function setTextEdit(on) {
        const prev = state.textEdit;
        state.textEdit = !!on;
        updateEditButtons();

        if (prev === state.textEdit) return;

        // Always detach editor before mode switch; ensureTextEditableState() re-attaches when needed
        if (ZBZ.TranscriptionEditor) ZBZ.TranscriptionEditor.detach(refs.textBody);

        // OCR panel rendering switches: rendered Markdown <-> raw text.
        // renderTextPanel() handles blank page (notice) and edit/read mode consistently.
        if (state.textSource === 'ocr') {
            renderTextPanel();
        } else {
            ensureTextEditableState();
        }
        // Note: the status transition unverifiziert -> in_arbeit happens only on the FIRST
        // real text change (onChange in ensureTextEditableState), not on opening.
    }

    // Returns false only when the user cancels the unsaved-changes confirm.
    function setTextSource(src) {
        if (src === state.textSource) return true;
        // Text edits are per source; switching drops them (mirrors confirmLeavePage)
        if (state.textDirty) {
            if (!window.confirm('Unsaved text changes will be lost when switching the text source. Switch anyway?')) return false;
            state.textDirty = false;
            state._currentEditedText = null;
            ZBZ.bus.emit('dirty:changed');
        }
        // Switching the view exits edit mode; re-render below shows the read view
        if (state.textEdit) {
            state.textEdit = false;
            updateEditButtons();
        }
        // Detach before re-render: cancels pending debounced commits of the old source
        if (ZBZ.TranscriptionEditor) ZBZ.TranscriptionEditor.detach(refs.textBody);
        state.textSource = src;
        applyTeiMarkup();   // dropdown label; the render callback re-applies highlighting
        renderTextPanel();
        return true;
    }

    function gotoPage(n) {
        if (!state.doc) return;
        const max = textPageCount();
        const target = Math.min(max, Math.max(1, n));
        if (target === state.page) return;
        if (!confirmLeavePage()) return;
        state.page = target;
        loadPage();
    }

    // The pager number is the jump field: it always shows the current page, typed input
    // that is not a page number is discarded when the field is left.
    function syncPageInput() {
        if (refs.pageGoto) refs.pageGoto.value = state.doc ? String(state.page) : '';
        if (refs.pageTotal) refs.pageTotal.textContent = '/ ' + (state.doc ? textPageCount() : '?');
    }

    Object.assign(ZBZ.Viewer, {
        loadPage,
        detectBlankPage,
        setRegionCount,
        loadFacsMap,
        facsImageUrl,
        textPageCount,
        renderFacsimile,
        fetchLayout,
        renderTextPanel,
        setXmlScope,
        renderDocMeta,
        ensureTextEditableState,
        loadTeiPage,
        loadTeiFinal,
        setImageEdit,
        applyTeiMarkup,
        currentView,
        syncViewUi,
        setView,
        toggleMarkupHighlight,
        updateEditButtons,
        toggleEditMode,
        setTextEdit,
        setTextSource,
        gotoPage,
        syncPageInput,
    });

    // Entity mode changes what the view and edit dropdowns may offer.
    ZBZ.bus.on('entity-mode:changed', () => { syncViewUi(); updateEditButtons(); });
})();
