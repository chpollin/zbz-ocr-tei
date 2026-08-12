/**
 * viewer.js — Pipeline viewer for a single document
 *
 * Responsible for:
 *  - Loading doc metadata from catalog.json (via ?doc= URL parameter)
 *  - Page navigation (Prev/Next, arrow keys)
 *  - Mode switching (view / layout / text)
 *  - Facsimile + layout overlay (left panel)
 *  - Text panel (OCR/TEI/XML) on the right
 *  - Download actions
 *
 * The corpus overview (doc list, filters) lives in docs/index.html.
 *
 * Namespace: ZBZ.Viewer
 */
(function () {
    'use strict';

    const $  = ZBZ.$;
    const $$ = ZBZ.$$;

    // ---- State ----
    // E60 (2026-05-25): mode -> imageEdit + textEdit (two independent edit states).
    const state = {
        catalog: null,
        doc: null,
        page: 1,
        textSource: 'ocr',    // ocr | tei | xml
        ocrSource: 'mistral',
        layout: null,
        teiXml: null,
        osdViewer: null,      // OpenSeadragon instance (only when !imageEdit is active)
        imageEdit: false,     // facsimile edit toggle: activates layout editor (img + custom overlay)
        textEdit: false,      // text edit toggle: activates transcription editor for active source
        _currentText: null,
        _currentEditedText: null,
        _isBlank: false,      // blank page (endpaper/verso/carbon copy), no real text
        manifest: null,       // E66: per-object manifest with streams.{ocr,layout,tei}.{status,history}
        manifestDirty: false, // unsaved status changes
        dirtyStreams: new Set(), // which streams have changed since the last save
        layoutDirty: false,   // unsaved layout change (current page)
        textDirty: false,     // unsaved text change (current page)
        teiMarkup: false,     // markup mode in the rendered view (annotation highlighting + legend)
        // Entity layer: strictly read-only inspection of the GND entity preview
        // (docs/data/pages/{doc}/{doc}_entity_p{N}.xml). No save path ever writes it.
        entityMode: false,      // toggle / ?entities=1
        entityAvailable: false, // an entity preview exists for the current document
        entityWorklist: null,   // {doc, pages: {N: [{gid, category, surface, rule, context}]}}
        entityPage: false       // the current page is rendered from the entity preview
    };

    // E77: workflow status per stream, three levels: unverifiziert -> in_arbeit -> verifiziert -> unverifiziert
    // `unverifiziert`: pipeline output exists, no human has verified it yet (neutral/gray).
    // `in_arbeit`: work in progress (yellow). `verifiziert`: human-approved (green).
    // Red is reserved for a future explicit problem status.
    const STATUS_CYCLE = ['unverifiziert', 'in_arbeit', 'verifiziert'];
    const STATUS_LABEL = {
        unverifiziert: 'unverified',
        in_arbeit:     'in progress',
        verifiziert:   'verified'
    };
    // Legacy mapping for older manifests/mirror (offen, bearbeitet, fertig)
    const STATUS_LEGACY = { offen: 'unverifiziert', bearbeitet: 'in_arbeit', fertig: 'verifiziert' };
    const STREAM_LABEL = { ocr: 'OCR', layout: 'Layout', tei: 'TEI-XML' };

    const OSD_PREFIX = 'https://cdn.jsdelivr.net/npm/openseadragon@5.0.1/build/openseadragon/images/';

    // Entity layer (generated mirror, written by scripts/edition/generate_entity_preview_data.py)
    const ENTITY_INDEX_PATH = 'data/entities.json';
    const entityPagePath     = (doc, page) => 'data/pages/' + doc + '/' + doc + '_entity_p' + page + '.xml';
    const entityWorklistPath = (doc) => 'data/pages/' + doc + '/' + doc + '_entity_worklist.json';
    const ENTITY_CATEGORY_LABEL = { person: 'Person', organisation: 'Organisation', work: 'Work' };
    const ENTITY_READONLY_HINT = 'Entity mode is read-only. Leave it to edit.';
    const ENTITY_MENTION_SEL = '.tei__entity[data-ref], .tei__bibl[data-ref]';

    const cache = new ZBZ.Cache(40);

    // ---- DOM refs ----
    const refs = {
        subbar:         $('#doc-subbar'),
        docMeta:        $('#doc-meta'),
        pageInfo:       $('#page-info'),
        btnPrev:        $('#btn-prev'),
        btnNext:        $('#btn-next'),
        pageGoto:       $('#page-goto'),
        btnImageEdit:   $('#btn-image-edit'),
        btnEditOcr:     $('#btn-edit-ocr'),
        btnEditXml:     $('#btn-edit-xml'),
        btnMarkup:      $('#btn-markup'),
        btnEntities:    $('#btn-entities'),
        textSourceBtns: $$('.mode-btn[data-text-source]'),
        imageBody:      $('#image-body'),
        textBody:       $('#text-body'),
        textTitle:      $('#text-panel-title'),
        regionCount:    $('#region-count'),
        layoutToolbar:  $('#layout-toolbar'),
        // Save + export dropdown + identity chip
        btnSave:        $('#btn-save'),
        btnExportMenu:  $('#btn-export-menu'),
        exportMenu:     $('#export-menu'),
        btnIdentity:    $('#btn-identity'),
        identityWho:    $('#identity-who'),
        identityInput:  $('#identity-input'),
        btnDlLayout:    $('#btn-download-layout'),
        btnDlText:      $('#btn-download-text'),
        btnDlTei:       $('#btn-download-tei'),
        btnDlManifest:  $('#btn-download-manifest'),
        fsaInfo:        $('#fsa-info'),
        fsaInfoGo:      $('#fsa-info-go'),
        fsaInfoCancel:  $('#fsa-info-cancel'),
        // E66: workflow status controls
        statusOcr:      $('#status-ocr'),
        statusLayout:   $('#status-layout'),
        statusTei:      $('#status-tei'),
        statusHint:     $('#status-hint')
    };

    // Original edit-button tooltips; entity mode swaps them for the read-only hint.
    const EDIT_TITLES = {
        ocr: refs.btnEditOcr ? refs.btnEditOcr.title : '',
        xml: refs.btnEditXml ? refs.btnEditXml.title : ''
    };

    // ============================================================ Init ============================================================

    async function init() {
        bindEvents();

        renderIdentity();
        // Restore persisted repo folder (File System Access)
        if (ZBZ.FsAccess) { await ZBZ.FsAccess.init(); }

        const urlDoc = ZBZ.getParam('doc');
        if (!urlDoc) {
            renderNoDoc();
            return;
        }

        const data = await ZBZ.fetchJSON('data/catalog.json');
        if (!data) {
            renderError('catalog.json not found. <code>python -m scripts.edition.generate_edition_data</code>');
            return;
        }
        state.catalog = data;

        const list = data.documents || data.docs || [];
        const doc = list.find(d => String(d.id) === String(urlDoc));
        if (!doc) {
            renderError('Document <code>' + ZBZ.esc(urlDoc) + '</code> not in catalog. <a href="index.html">Back to Corpus</a>');
            return;
        }

        state.entityMode = ZBZ.getParam('entities') === '1';
        const urlPage = parseInt(ZBZ.getParam('page'), 10);
        await selectDoc(doc, isNaN(urlPage) ? 1 : urlPage);
        ZBZ.log('Viewer', 'init done, doc ' + doc.id);
    }

    function renderNoDoc() {
        refs.imageBody.innerHTML =
            '<div class="empty">No document loaded. <a href="index.html">Back to Corpus</a></div>';
        refs.textBody.innerHTML =
            '<div class="empty">—</div>';
    }

    function renderError(html) {
        refs.imageBody.innerHTML = '<div class="empty">' + html + '</div>';
        refs.textBody.innerHTML  = '<div class="empty">—</div>';
    }

    // ============================================================ Doc selection ============================================================

    async function selectDoc(doc, startPage) {
        state.doc = doc;
        state.page = startPage || 1;
        state.layout = null;
        state.teiXml = null;
        state.manifest = null;
        state.manifestDirty = false;
        ZBZ.setParams({ doc: doc.id, page: state.page });
        document.title = (doc.title ? doc.title.slice(0, 60) + ' — ' : '') + 'Hersch Pipeline Viewer';

        // Show and populate sub-bar
        refs.subbar.hidden = false;
        renderDocMeta(doc);

        // Enable buttons
        refs.btnPrev.disabled = state.page <= 1;
        refs.btnNext.disabled = state.page >= (doc.page_count || 1);
        if (refs.pageGoto) {
            refs.pageGoto.disabled = false;
            refs.pageGoto.max = doc.page_count || 1;
        }
        refs.btnDlLayout.disabled = false;
        refs.btnDlText.disabled = false;
        refs.btnDlTei.disabled = false;
        if (refs.btnExportMenu) refs.btnExportMenu.disabled = false;
        renderSaveState();

        // E66: load manifest for workflow status (parallel to page rendering)
        loadManifest(doc.id);

        // Entity layer: must be known before the first text render decides its source
        await loadEntityAssets(doc.id);

        await loadPage();
    }

    // ============================================================ Entity layer (read-only) ============================================================

    // Worklist and lookup come from the generated mirror; a document without an entity
    // preview simply keeps the button disabled. The lookup is document-independent and
    // therefore fetched once per session.
    let entityIndex = null;

    async function loadEntityAssets(docId) {
        state.entityWorklist = null;
        state.entityAvailable = false;
        state.entityPage = false;
        const worklist = await ZBZ.fetchJSON(entityWorklistPath(docId));
        if (worklist) {
            state.entityWorklist = worklist;
            state.entityAvailable = true;
            if (!entityIndex) entityIndex = (await ZBZ.fetchJSON(ENTITY_INDEX_PATH)) || {};
        }
        if (state.entityMode && !state.entityAvailable) {
            state.entityMode = false;
            ZBZ.setParams({ entities: null });
            ZBZ.toast('No entity preview for this document', 'warn');
        }
        if (state.entityMode) {
            // The entity layer is a TEI reading view; markup highlighting belongs to it.
            state.textSource = 'tei';
            state.teiMarkup = true;
            syncTextSourceButtons();
        }
        updateEntityUi();
    }

    async function loadEntityPage(doc, page) {
        const ck = 'entity:' + doc + ':' + page;
        if (cache.has(ck)) return cache.get(ck);
        // fetchFirstOk turns a 404 into null (pages without an entity preview stay usable)
        const res = await ZBZ.fetchFirstOk([entityPagePath(doc, page)]);
        const xml = res ? res.text : null;
        if (xml != null) cache.set(ck, xml);
        return xml;
    }

    function updateEntityUi() {
        if (refs.btnEntities) {
            refs.btnEntities.disabled = !state.doc || !state.entityAvailable;
            refs.btnEntities.setAttribute('aria-pressed', state.entityMode ? 'true' : 'false');
            refs.btnEntities.title = state.entityAvailable
                ? 'GND entity preview of this document (read-only inspection layer)'
                : 'No entity preview generated for this document';
        }
        // Strictly read-only: no editor may attach while the entity file is on screen.
        const locked = state.entityMode;
        if (refs.btnEditOcr) {
            refs.btnEditOcr.disabled = locked;
            refs.btnEditOcr.title = locked ? ENTITY_READONLY_HINT : EDIT_TITLES.ocr;
        }
        if (refs.btnEditXml) {
            refs.btnEditXml.disabled = locked;
            refs.btnEditXml.title = locked ? ENTITY_READONLY_HINT : EDIT_TITLES.xml;
        }
    }

    function setEntityMode(on) {
        const next = !!on;
        if (next === state.entityMode) return;
        if (next && !state.entityAvailable) return;
        state.entityMode = next;
        closeEntityPopover(false);
        if (next) state.teiMarkup = true;
        if (next && state.textSource !== 'tei') {
            // setTextSource confirms unsaved edits, leaves edit mode and re-renders
            if (!setTextSource('tei')) { state.entityMode = false; updateEntityUi(); return; }
            ZBZ.setParams({ entities: 1 });
            updateEntityUi();
            return;
        }
        ZBZ.setParams({ entities: next ? 1 : null });
        updateEntityUi();
        renderTextPanel();
    }

    // Surfaces can carry <lb/> tags (names broken across lines); the worklist shows text.
    function plainSurface(surface) {
        return String(surface || '').replace(/<lb\b[^>]*>/g, ' ').replace(/\s+/g, ' ').trim();
    }

    function renderEntityWorklist(page) {
        const old = refs.textBody.querySelector('.entity-worklist');
        if (old) old.remove();
        const pages = state.entityWorklist && state.entityWorklist.pages;
        const entries = (pages && pages[String(page)]) || [];
        const box = ZBZ.el('aside', {
            cls: 'entity-worklist', attrs: { 'aria-label': 'Entity worklist of this page' }
        });
        box.appendChild(ZBZ.el('div', {
            cls: 'entity-worklist__title', text: 'Worklist p. ' + page + ' · ' + entries.length
        }));
        if (!entries.length) {
            box.appendChild(ZBZ.el('div', {
                cls: 'entity-worklist__empty', text: 'No candidate awaiting a decision on this page'
            }));
        } else {
            const list = ZBZ.el('ul', { cls: 'entity-worklist__list' });
            entries.forEach(entry => {
                const li = ZBZ.el('li', { cls: 'entity-worklist__item' });
                li.appendChild(ZBZ.el('span', {
                    cls: 'entity-worklist__surface', text: plainSurface(entry.surface)
                }));
                li.appendChild(ZBZ.el('span', { cls: 'entity-worklist__rule', text: entry.rule || '?' }));
                li.appendChild(ZBZ.el('span', {
                    cls: 'entity-worklist__context', text: entry.context || ''
                }));
                list.appendChild(li);
            });
            box.appendChild(list);
        }
        refs.textBody.insertBefore(box, refs.textBody.firstChild);
    }

    // Marked mentions become buttons: the popover carries id, category and lobid link,
    // which the native title tooltip cannot.
    function decorateEntityMentions() {
        const wrap = refs.textBody.querySelector('.tei');
        if (!wrap) return;
        $$(ENTITY_MENTION_SEL, wrap).forEach(el => {
            el.removeAttribute('title');
            el.setAttribute('role', 'button');
            el.setAttribute('tabindex', '0');
            const gid = entityGid(el);
            const rec = entityIndex && entityIndex[gid];
            el.setAttribute('aria-label',
                (rec ? rec.label : el.textContent.trim()) + ', GND ' + gid + ', show details');
        });
    }

    function entityGid(el) {
        return (el.getAttribute('data-ref') || '').replace(/^GND:/, '');
    }

    // ---- Popover ----
    let entityPopover = null;
    let entityPopoverTrigger = null;

    function ensureEntityPopover() {
        if (entityPopover) return entityPopover;
        entityPopover = ZBZ.el('div', {
            cls: 'entity-pop',
            attrs: { role: 'dialog', 'aria-label': 'Entity detail', tabindex: '-1', hidden: 'hidden' }
        });
        document.body.appendChild(entityPopover);
        return entityPopover;
    }

    function showEntityPopover(el) {
        const gid = entityGid(el);
        const rec = (entityIndex && entityIndex[gid]) || null;
        const pop = ensureEntityPopover();
        pop.innerHTML = '';
        pop.appendChild(ZBZ.el('button', {
            cls: 'entity-pop__close', html: '&times;',
            attrs: { type: 'button', 'aria-label': 'Close' },
            on: { click: () => closeEntityPopover(true) }
        }));
        pop.appendChild(ZBZ.el('div', {
            cls: 'entity-pop__label', text: rec ? rec.label : el.textContent.trim()
        }));
        const meta = [];
        if (rec && rec.category) meta.push(ENTITY_CATEGORY_LABEL[rec.category] || rec.category);
        if (rec && rec.dates) meta.push(rec.dates);
        if (!rec) meta.push('not in the curated entity list');
        pop.appendChild(ZBZ.el('div', { cls: 'entity-pop__meta', text: meta.join(' · ') }));
        pop.appendChild(ZBZ.el('div', { cls: 'entity-pop__gid', text: 'GND ' + (gid || '?') }));
        if (gid) {
            pop.appendChild(ZBZ.el('a', {
                cls: 'entity-pop__link', text: 'lobid.org',
                attrs: {
                    href: (rec && rec.lobid) || 'https://lobid.org/gnd/' + encodeURIComponent(gid),
                    target: '_blank', rel: 'noopener'
                }
            }));
        }
        pop.hidden = false;
        positionEntityPopover(pop, el);
        entityPopoverTrigger = el;
        pop.focus();
        setTimeout(() => document.addEventListener('click', onDocClickForPopover), 0);
    }

    function positionEntityPopover(pop, el) {
        const r = el.getBoundingClientRect();
        pop.style.visibility = 'hidden';
        pop.style.left = '0px';
        pop.style.top = '0px';
        const w = pop.offsetWidth, h = pop.offsetHeight;
        const left = Math.max(8, Math.min(r.left, window.innerWidth - w - 8));
        let top = r.bottom + 6;
        if (top + h > window.innerHeight - 8) top = Math.max(8, r.top - h - 6);
        pop.style.left = left + 'px';
        pop.style.top = top + 'px';
        pop.style.visibility = '';
    }

    function closeEntityPopover(restoreFocus) {
        document.removeEventListener('click', onDocClickForPopover);
        if (!entityPopover || entityPopover.hidden) { entityPopoverTrigger = null; return; }
        entityPopover.hidden = true;
        entityPopover.innerHTML = '';
        if (restoreFocus && entityPopoverTrigger && entityPopoverTrigger.isConnected) {
            entityPopoverTrigger.focus();
        }
        entityPopoverTrigger = null;
    }

    function onDocClickForPopover(e) {
        if (entityPopover && entityPopover.contains(e.target)) return;
        if (e.target.closest && e.target.closest(ENTITY_MENTION_SEL)) return;
        closeEntityPopover(false);
    }

    // ============================================================ Workflow status (E66) ============================================================

    async function loadManifest(docId) {
        const m = await ZBZ.fetchJSON('data/manifests/' + encodeURIComponent(docId) + '_manifest.json');
        if (m && m.streams) {
            // Migrate legacy status values (v2 -> v3)
            ['ocr', 'layout', 'tei'].forEach(s => {
                const stream = m.streams[s];
                if (stream && STATUS_LEGACY[stream.status]) {
                    stream.status = STATUS_LEGACY[stream.status];
                }
                if (stream && Array.isArray(stream.history)) {
                    stream.history.forEach(h => {
                        if (h.from && STATUS_LEGACY[h.from]) h.from = STATUS_LEGACY[h.from];
                        if (h.to   && STATUS_LEGACY[h.to])   h.to   = STATUS_LEGACY[h.to];
                    });
                }
            });
            state.manifest = m;
        } else {
            // Fallback: synthetic manifest if the mirror is out of date (defensive)
            state.manifest = {
                doc_id: docId,
                page_count: state.doc && state.doc.page_count,
                generated: new Date().toISOString().slice(0, 10),
                generator: 'viewer-fallback',
                streams: {
                    ocr:    { engine: 'mistral', status: 'unverifiziert', history: [] },
                    layout: { engines: ['docling', 'gemini'], status: 'unverifiziert', history: [] },
                    tei:    { source: 'final', status: 'unverifiziert', history: [] }
                },
                pages: {}
            };
        }
        renderStatusPills();
        refs.btnDlManifest.disabled = false;
    }

    // Initials from the identity chip (localStorage). No blocking prompt().
    function getAuthor() {
        const fromStore = (window.localStorage && localStorage.getItem('zbz.workflow.by')) || '';
        return fromStore || 'anonym';
    }

    function streamStatus(stream) {
        const s = state.manifest && state.manifest.streams && state.manifest.streams[stream];
        let v = s && s.status;
        if (STATUS_LEGACY[v]) v = STATUS_LEGACY[v];
        return STATUS_LABEL[v] ? v : 'unverifiziert';
    }

    function renderStatusPills() {
        const enable = !!state.manifest;
        ['ocr', 'layout', 'tei'].forEach(stream => {
            const btn = refs['status' + stream.charAt(0).toUpperCase() + stream.slice(1)];
            if (!btn) return;
            btn.disabled = !enable;
            const status = streamStatus(stream);
            // Update classes (remove old status classes)
            btn.className = 'status-pill status-pill--' + status + (state.dirtyStreams.has(stream) ? ' status-pill--dirty' : '');
            const sm = (state.manifest && state.manifest.streams && state.manifest.streams[stream]) || {};
            const history = sm.history || [];
            const last = history.length ? history[history.length - 1] : null;
            const baseLine = (status === 'unverifiziert')
                ? STREAM_LABEL[stream] + ': pipeline output exists, not yet human-verified'
                : STREAM_LABEL[stream] + ': ' + STATUS_LABEL[status];
            btn.title = baseLine
                + (last ? '\nlast: ' + last.to + ' · ' + (last.by || '?') + ' · ' + (last.at || '').slice(0, 16) : '')
                + '\nClick cycles: unverified -> in progress -> verified';
            // announce the current status, not just "set status" (a11y)
            btn.setAttribute('aria-label', STREAM_LABEL[stream] + ' status: ' + STATUS_LABEL[status] + ' (click to cycle)');
            btn.innerHTML =
                '<span class="status-pill__stream">' + STREAM_LABEL[stream] + '</span>'
                + '<span class="status-pill__dot"></span>'
                + '<span class="status-pill__label">' + STATUS_LABEL[status] + '</span>';
        });
        refs.btnDlManifest.disabled = !state.manifest;
        refs.statusHint.textContent = state.manifestDirty
            ? 'Unsaved status · Save'
            : '';
    }

    function setStreamStatus(stream, newStatus, opts) {
        if (!state.manifest) return;
        if (STATUS_CYCLE.indexOf(newStatus) < 0) return;
        const s = state.manifest.streams[stream];
        if (!s) return;
        const from = s.status || 'unverifiziert';
        if (from === newStatus) return;
        s.status = newStatus;
        if (!Array.isArray(s.history)) s.history = [];
        const entry = {
            at: new Date().toISOString(),
            by: (opts && opts.by) || getAuthor(),
            from: from,
            to: newStatus,
            note: (opts && opts.note) || null
        };
        s.history.push(entry);
        // Entries created before initials are set get backfilled on commitIdentityEdit
        if (entry.by === 'anonym') anonEntries.push(entry);
        state.manifestDirty = true;
        state.dirtyStreams.add(stream);
        renderStatusPills();
        renderSaveState();
    }

    function cycleStatus(stream) {
        if (!state.manifest) return;
        const cur = streamStatus(stream);
        const next = STATUS_CYCLE[(STATUS_CYCLE.indexOf(cur) + 1) % STATUS_CYCLE.length];
        setStreamStatus(stream, next);
    }

    function autoStartArbeit(stream) {
        // On the first real change in the editor: unverifiziert -> in_arbeit
        if (!state.manifest) return;
        if (streamStatus(stream) === 'unverifiziert') {
            setStreamStatus(stream, 'in_arbeit', { note: 'auto: first edit in viewer' });
        }
    }

    // ============================================================ Identity chip (Initials) ============================================================

    let identityCancelling = false; // ESC cancels without the blur handler committing
    // History entries created this session while no initials were set; backfilled once
    // initials arrive. Saved manifests are never rewritten (past provenance stays).
    const anonEntries = [];
    let identityPrompted = false;   // ask once per session, never block the save

    function currentAuthor() {
        return (window.localStorage && localStorage.getItem('zbz.workflow.by')) || '';
    }
    function renderIdentity() {
        if (!refs.identityWho) return;
        const v = currentAuthor();
        refs.identityWho.textContent = v || 'Initials';
        refs.btnIdentity.classList.toggle('identity-chip--empty', !v);
    }
    function startIdentityEdit() {
        refs.identityInput.value = currentAuthor();
        refs.btnIdentity.hidden = true;
        refs.identityInput.hidden = false;
        refs.identityInput.focus();
        refs.identityInput.select();
    }
    function commitIdentityEdit() {
        if (identityCancelling) { identityCancelling = false; return; }
        const v = refs.identityInput.value.trim();
        if (window.localStorage) {
            if (v) localStorage.setItem('zbz.workflow.by', v);
            else localStorage.removeItem('zbz.workflow.by');
        }
        if (v && anonEntries.length) {
            anonEntries.forEach(e => { if (e.by === 'anonym') e.by = v; });
            anonEntries.length = 0;
            renderStatusPills();   // pill tooltips show the last history entry
        }
        refs.identityInput.hidden = true;
        refs.btnIdentity.hidden = false;
        renderIdentity();
    }
    function cancelIdentityEdit() {
        identityCancelling = true;
        refs.identityInput.hidden = true;
        refs.btnIdentity.hidden = false;
    }

    // ============================================================ Save (all streams directly to repo) ============================================================

    // Writes directly to the connected repo folder; falls back per file to download
    // if not connected or if the write fails. No individual toast
    // (saveAll reports collectively).
    async function persistSilent(fsWrite, dlFallback) {
        // On Chromium (File System Access available) writes go exclusively to the repo;
        // saveAll has established the connection beforehand. A write error propagates
        // to saveAll and is reported visibly there -- NO silent download that would
        // deposit confusing files in the Downloads folder. Download is only the path
        // when the API is unavailable (non-Chromium browsers).
        if (ZBZ.FsAccess && ZBZ.FsAccess.available) {
            await fsWrite();
            return true;
        }
        dlFallback();
        return false;
    }

    function renderSaveState() {
        // What is unsaved? (also the basis for the state-dependent tooltip)
        const parts = [];
        if (state.layoutDirty) parts.push('Layout p.' + state.page);
        if (state.textDirty)   parts.push((state.textSource === 'xml' || state.textSource === 'tei') ? 'TEI' : 'Text p.' + state.page);
        if (state.manifestDirty) parts.push('Status');
        const dirty = parts.length > 0;
        if (!refs.btnSave) return;
        refs.btnSave.disabled = !state.doc || !dirty;
        refs.btnSave.classList.toggle('btn--dirty', dirty);
        if (!dirty) {
            refs.btnSave.title = 'Nothing to save. Edit layout, text, or workflow status first.';
        } else {
            const target = (ZBZ.FsAccess && ZBZ.FsAccess.available)
                ? (ZBZ.FsAccess.isConnected() ? 'directly to repo' : 'to repo (will ask for folder once)')
                : 'as download';
            refs.btnSave.title = 'Saves ' + target + ': ' + parts.join(', ');
        }
    }

    // Check before a page change: layout/text edits are per-page and are lost on navigation.
    // Manifest dirty is per-document and survives navigation, so it does not block it.
    // Returns true if the navigation may proceed.
    function confirmLeavePage() {
        if (!state.layoutDirty && !state.textDirty) return true;
        return window.confirm('Unsaved changes on this page will be lost. Navigate anyway?');
    }

    // Save = all unsaved streams as one action: layout (page), text (page, OCR or TEI
    // depending on source), and the manifest (workflow status + provenance). Each stream
    // goes to its correct location in the repo. No download (except fallback).
    async function saveAll() {
        if (!state.doc) return;
        const dl = state.layoutDirty && state.layout && Array.isArray(state.layout.regions);
        const dt = state.textDirty;
        const dm = state.manifestDirty;
        if (!dl && !dt && !dm) { ZBZ.toast('Nothing to save', 'warn'); return; }

        // Provenance: history entries carry the editor initials into the delivered
        // revisionDesc. Ask once when none are set; a second Save proceeds as "anonym".
        if (dm && !currentAuthor() && !identityPrompted) {
            identityPrompted = true;
            ZBZ.toast('No initials set: history entries will say "anonym". Enter initials (top right) or press Save again to keep "anonym".', 'warn');
            startIdentityEdit();
            return;
        }

        // Direct save: on Chromium a repo folder must be connected. If not,
        // connect once (with first-use info). If that fails (user cancels or denies
        // write access), abort with a clear message instead of silently depositing the
        // file in the Downloads folder. Streams remain unsaved, nothing is lost;
        // a second click (or Export -> Download) is possible.
        if (ZBZ.FsAccess && ZBZ.FsAccess.available && !ZBZ.FsAccess.isConnected()) {
            await connectWithInfo();
            if (!ZBZ.FsAccess.isConnected()) {
                ZBZ.toast('Not saved: repo folder not connected or write access denied. Connect the "zbz-ocr-tei" folder and try Save again (or use Export to download).', 'warn');
                return;
            }
        }

        const saved = [];
        let downloaded = false; // any stream fell back to download
        try {
            if (dl) {
                const meta = layoutSourceMeta();
                if (!(await persistSilent(
                    () => ZBZ.FsAccess.writeLayout(state.doc.id, state.page, state.layout.regions, meta),
                    () => ZBZ.Download.layout(state.doc.id, state.page, state.layout.regions, meta)
                ))) downloaded = true;
                state.layoutDirty = false;
                if (refs.regionCount) refs.regionCount.textContent = state.layout.regions.length + ' regions';
                saved.push('Layout p.' + state.page);
            }
            if (dt) {
                const content = (state._currentEditedText != null) ? state._currentEditedText : state._currentText;
                if (content == null) {
                    state.textDirty = false;
                } else {
                    const isTei = (state.textSource === 'xml' || state.textSource === 'tei');
                    if (isTei) {
                        // writeTei replaces the whole SoT file -- only accept a complete TEI document
                        const incomplete = content.indexOf('<teiHeader') === -1 || content.indexOf('</TEI>') === -1;
                        const wfError = incomplete ? null : ZBZ.xmlWellFormedError(content);
                        if (incomplete) {
                            ZBZ.toast('TEI not saved: content is not a complete TEI document (teiHeader/TEI root missing). Edit is retained unsaved.', 'err');
                        } else if (wfError) {
                            ZBZ.toast('TEI not saved: XML is not well-formed (' + wfError + '). Fix the markup in XML mode; the edit is retained unsaved.', 'err');
                        } else {
                            if (!(await persistSilent(
                                () => ZBZ.FsAccess.writeTei(state.doc.id, content),
                                () => ZBZ.Download.tei(state.doc.id, content, 'curated')
                            ))) downloaded = true;
                            cache.set('tei-final:' + state.doc.id, content);
                            state.textDirty = false;
                            saved.push('TEI');
                        }
                    } else {
                        if (!(await persistSilent(
                            () => ZBZ.FsAccess.writeText(state.doc.id, state.page, content),
                            () => ZBZ.Download.text(state.doc.id, state.page, content)
                        ))) downloaded = true;
                        state.textDirty = false;
                        saved.push('Text p.' + state.page);
                    }
                }
            }
            if (dm) {
                if (!(await persistSilent(
                    () => ZBZ.FsAccess.writeManifest(state.doc.id, state.manifest),
                    () => ZBZ.Download.manifest(state.doc.id, state.manifest)
                ))) downloaded = true;
                state.manifestDirty = false;
                state.dirtyStreams.clear();
                saved.push('Status');
            }
        } catch (err) {
            ZBZ.toast('Save failed: ' + (err && err.message), 'err');
        }

        renderStatusPills();
        renderSaveState();
        if (saved.length) {
            // a download is not a repo write -- be explicit about it (H2)
            if (downloaded) {
                ZBZ.toast('Download created (copy files to repo manually): ' + saved.join(', '), 'warn');
            } else {
                ZBZ.toast('Saved (repo): ' + saved.join(', '), 'ok');
            }
        }
    }

    // ============================================================ Export dropdown (single-file download) ============================================================

    function exportLayout() {
        if (!state.doc || !state.layout) { ZBZ.toast('No layout data', 'warn'); return; }
        ZBZ.Download.layout(state.doc.id, state.page, state.layout.regions, layoutSourceMeta());
        closeExportMenu();
    }
    function exportText() {
        if (!state.doc) return;
        const content = (state._currentEditedText != null) ? state._currentEditedText : state._currentText;
        if (!content) { ZBZ.toast('No text loaded', 'warn'); return; }
        ZBZ.Download.text(state.doc.id, state.page, content);
        closeExportMenu();
    }
    async function exportTei() {
        if (!state.doc) return;
        let xml = state._currentEditedText;
        if (!xml || state.textSource !== 'xml') xml = await loadTeiFinal(state.doc.id);
        if (!xml) { ZBZ.toast('No TEI available', 'warn'); return; }
        ZBZ.Download.tei(state.doc.id, xml, 'curated');
        closeExportMenu();
    }
    function exportManifest() {
        if (!state.manifest) { ZBZ.toast('No manifest loaded', 'warn'); return; }
        ZBZ.Download.manifest(state.doc.id, state.manifest);
        closeExportMenu();
    }

    function toggleExportMenu() {
        if (refs.exportMenu.hidden) openExportMenu(); else closeExportMenu();
    }
    function openExportMenu() {
        refs.exportMenu.hidden = false;
        refs.btnExportMenu.setAttribute('aria-expanded', 'true');
        setTimeout(() => document.addEventListener('click', onDocClickForMenu), 0);
    }
    function closeExportMenu() {
        if (!refs.exportMenu || refs.exportMenu.hidden) return;
        refs.exportMenu.hidden = true;
        refs.btnExportMenu.setAttribute('aria-expanded', 'false');
        document.removeEventListener('click', onDocClickForMenu);
    }
    function onDocClickForMenu(e) {
        if (!refs.exportMenu.contains(e.target) && e.target !== refs.btnExportMenu) closeExportMenu();
    }

    // ============================================================ Repo folder (File System Access) ============================================================

    // One-time info on first connect: explains WHICH folder to choose and WHAT happens
    // before the native folder dialog opens. Remembered afterwards (localStorage).
    function connectWithInfo() {
        return new Promise((resolve) => {
            if (!ZBZ.FsAccess || !ZBZ.FsAccess.available) { resolve(false); return; }
            const proceed = async () => {
                if (window.localStorage) localStorage.setItem('zbz.fsa.infoShown', '1');
                hideFsaInfo();
                const ok = await ZBZ.FsAccess.connect();
                resolve(ok);
            };
            const cancel = () => { hideFsaInfo(); resolve(false); };
            if (window.localStorage && localStorage.getItem('zbz.fsa.infoShown')) { proceed(); return; }
            showFsaInfo(proceed, cancel);
        });
    }
    // Modal a11y: focus restore target + document-level key handler (ESC, Tab trap)
    let fsaInfoPrevFocus = null;
    let fsaInfoKeydown = null;

    function showFsaInfo(onGo, onCancel) {
        if (!refs.fsaInfo) { onGo(); return; }
        if (refs.fsaInfoGo) refs.fsaInfoGo.onclick = onGo;
        if (refs.fsaInfoCancel) refs.fsaInfoCancel.onclick = onCancel;
        fsaInfoPrevFocus = document.activeElement;
        refs.fsaInfo.hidden = false;
        if (refs.fsaInfoGo) refs.fsaInfoGo.focus();
        fsaInfoKeydown = (e) => {
            if (e.key === 'Escape') { e.preventDefault(); onCancel(); return; }
            if (e.key === 'Tab') {
                // focus trap: the modal has exactly two buttons
                e.preventDefault();
                const next = (document.activeElement === refs.fsaInfoGo) ? refs.fsaInfoCancel : refs.fsaInfoGo;
                if (next) next.focus();
            }
        };
        document.addEventListener('keydown', fsaInfoKeydown);
    }
    function hideFsaInfo() {
        if (!refs.fsaInfo) return;
        refs.fsaInfo.hidden = true;
        if (fsaInfoKeydown) { document.removeEventListener('keydown', fsaInfoKeydown); fsaInfoKeydown = null; }
        if (fsaInfoPrevFocus && typeof fsaInfoPrevFocus.focus === 'function') fsaInfoPrevFocus.focus();
        fsaInfoPrevFocus = null;
    }

    // ============================================================ Page loading ============================================================

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
        renderSaveState();
        refs.pageInfo.textContent = page + ' / ' + (doc.page_count || '?');
        refs.btnPrev.disabled = page <= 1;
        refs.btnNext.disabled = page >= (doc.page_count || 1);
        ZBZ.setParams({ page });

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
            const res = await ZBZ.fetchFirstOk(ZBZ.path.ocr('mistral', doc, page));
            blank = res ? ZBZ.isBlankPageText(res.text) : false;
        }
        cache.set(ck, blank);
        return blank;
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
            refs.regionCount.textContent = 'Blank page, no text';
        } else {
            refs.regionCount.textContent = (layout && layout.regions)
                ? layout.regions.length + ' regions'
                : 'no layout data';
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
        const img = ZBZ.el('img', {
            cls: 'facsimile__img',
            attrs: { src: ZBZ.path.image(doc.id, page), alt: 'Facsimile page ' + page, loading: 'eager' }
        });
        img.addEventListener('error', () => {
            refs.imageBody.innerHTML =
                '<div class="empty">Facsimile not available for page ' + page +
                '<br><code style="font-size:0.85em">' + ZBZ.esc(ZBZ.path.image(doc.id, page)) + '</code></div>';
        });

        const overlay = ZBZ.el('div', { cls: 'facsimile__overlay', attrs: { id: 'layout-overlay' } });
        facs.appendChild(img);
        facs.appendChild(overlay);
        refs.imageBody.appendChild(facs);

        const layout = await fetchLayout(doc.id, page);
        if (state.doc !== doc || state.page !== page || !state.imageEdit) return;
        state.layout = layout;
        if (layout && layout.regions) {
            refs.regionCount.textContent = layout.regions.length + ' regions';
            renderRegionOverlay(overlay, layout.regions);
        } else {
            refs.regionCount.textContent = 'no layout data';
        }

        if (state.imageEdit && ZBZ.LayoutEditor) {
            ZBZ.LayoutEditor.attach(overlay, layout, onLayoutChanged);
        }
    }

    async function fetchLayout(doc, page) {
        const ck = 'layout:' + doc + ':' + page;
        if (cache.has(ck)) return cache.get(ck);
        const j = await ZBZ.fetchFirstJsonOk(ZBZ.path.layoutCurated(doc, page))
              || await ZBZ.fetchFirstJsonOk(ZBZ.path.layoutGemini(doc, page))
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
        refs.regionCount.textContent = regions.length + ' regions (edited)';
        state.layoutDirty = true;
        renderSaveState();
        // E66: first real layout change -> set stream to in_arbeit
        autoStartArbeit('layout');
    }

    // ============================================================ Text panel ============================================================

    function textPanelTitle() {
        if (state.textSource === 'tei') return state.entityPage ? 'TEI · entities (read-only)' : 'TEI · rendered';
        if (state.textSource === 'xml') return 'TEI · XML (full document)';
        return 'OCR · ' + state.ocrSource;
    }

    async function renderTextPanel() {
        const doc = state.doc, page = state.page;
        const src = state.textSource;
        state.entityPage = false;
        closeEntityPopover(false);
        // True once doc/page/source changed mid-fetch -- a stale response must not render.
        const stale = () => (state.doc !== doc || state.page !== page || state.textSource !== src);

        // Blank page: show a quiet notice instead of OCR garbage ('.', '^{}[]', empty table).
        // In text edit mode render normally so the raw text can be cleaned if needed.
        // XML mode is exempt (shows the whole document).
        if (state._isBlank && !state.textEdit && state.textSource !== 'xml') {
            refs.textTitle.textContent = textPanelTitle();
            refs.textBody.innerHTML = '';
            refs.textBody.appendChild(ZBZ.el('div', {
                cls: 'empty empty--blank-page', text: 'Blank page, no text'
            }));
            state._currentText = null;
            return;
        }

        refs.textBody.innerHTML = '<div class="empty">Loading...</div>';

        if (state.textSource === 'ocr') {
            refs.textTitle.textContent = 'OCR · ' + state.ocrSource;
            const res = await ZBZ.fetchFirstOk(ZBZ.path.ocr(state.ocrSource, doc.id, page));
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
            refs.textTitle.textContent = textPanelTitle();
            if (!xml) {
                renderLoadError('No TEI for page ' + page);
                return;
            }
            // The entity preview is never a save source; keep the pipeline TEI in state.
            if (!state.entityPage) state.teiXml = xml;
            ZBZ.TeiRender.render(xml, refs.textBody);
            applyTeiMarkup();
            if (state.entityMode) {
                if (state.entityPage) decorateEntityMentions();
                renderEntityWorklist(page);
            }
        }
        else if (state.textSource === 'xml') {
            // Must load the FULL final TEI: saving overwrites {doc}_final.xml as a
            // whole (E72). Loading a single page here would destroy the rest on save.
            refs.textTitle.textContent = 'TEI · XML (full document)';
            const xml = await loadTeiFinal(doc.id);
            if (stale()) return;
            if (!xml) {
                renderLoadError('No final TEI for document ' + doc.id);
                return;
            }
            state.teiXml = xml;
            ZBZ.TeiRender.renderXml(xml, refs.textBody);
            ensureTextEditableState();
        }
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
        // E66: screening badge replaced by workflow status pills (second subbar row).
    }

    function ensureTextEditableState() {
        // Entity mode is strictly read-only: the editor never attaches to the entity file.
        if (state.entityMode) return;
        if (state.textEdit && ZBZ.TranscriptionEditor) {
            // Bind the stream at attach time: a debounced commit may fire after
            // state.textSource already changed (tab switch mid-debounce).
            const src = state.textSource;
            ZBZ.TranscriptionEditor.attach(refs.textBody, src, (newContent) => {
                state._currentEditedText = newContent;
                state.textDirty = true;
                renderSaveState();
                // E66: first real text change -> set corresponding stream to in_arbeit
                autoStartArbeit(src === 'ocr' ? 'ocr' : 'tei');
            });
        }
    }

    async function loadTeiPage(doc, page) {
        const ck = 'tei:' + doc + ':' + page;
        if (cache.has(ck)) return cache.get(ck);
        const res = await ZBZ.fetchFirstOk(ZBZ.path.teiPage(doc, page));
        const xml = res ? res.text : null;
        if (xml != null) cache.set(ck, xml); // never cache failures, retry must refetch
        return xml;
    }

    async function loadTeiFinal(doc) {
        const ck = 'tei-final:' + doc;
        if (cache.has(ck)) return cache.get(ck);
        const res = await ZBZ.fetchFirstOk(ZBZ.path.teiFinal(doc));
        const xml = res ? res.text : null;
        if (xml != null) cache.set(ck, xml);
        return xml;
    }

    // ============================================================ Edit toggles (E60) ============================================================

    function setImageEdit(on) {
        const prev = state.imageEdit;
        state.imageEdit = !!on;
        refs.btnImageEdit.setAttribute('aria-pressed', state.imageEdit ? 'true' : 'false');

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
        ['Works',         '.tei__bibl[data-ref]',             'work']
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
        if (refs.btnMarkup) {
            refs.btnMarkup.disabled = state.textSource !== 'tei';
            refs.btnMarkup.setAttribute('aria-pressed', (state.textSource === 'tei' && state.teiMarkup) ? 'true' : 'false');
        }
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

    // Each edit button binds edit mode to its source (Edit OCR -> ocr, Edit XML -> xml).
    // The rendered TEI view has no edit entry point: it cannot be round-tripped
    // (transcription-editor reads innerText only), save/export take TEI edits
    // exclusively from XML mode.
    function updateEditButtons() {
        refs.btnEditOcr.setAttribute('aria-pressed', (state.textEdit && state.textSource === 'ocr') ? 'true' : 'false');
        refs.btnEditXml.setAttribute('aria-pressed', (state.textEdit && state.textSource === 'xml') ? 'true' : 'false');
    }

    function toggleEdit(src) {
        if (state.entityMode) { ZBZ.toast(ENTITY_READONLY_HINT, 'warn'); return; }
        if (state.textEdit && state.textSource === src) { setTextEdit(false); return; }
        if (state.textSource !== src && !setTextSource(src)) return; // user kept unsaved edits
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
            renderSaveState();
        }
        // Switching the view exits edit mode; re-render below shows the read view
        if (state.textEdit) {
            state.textEdit = false;
            updateEditButtons();
        }
        // Detach before re-render: cancels pending debounced commits of the old source
        if (ZBZ.TranscriptionEditor) ZBZ.TranscriptionEditor.detach(refs.textBody);
        state.textSource = src;
        syncTextSourceButtons();
        applyTeiMarkup();   // button enable state; the render callback re-applies highlighting
        renderTextPanel();
        return true;
    }

    function syncTextSourceButtons() {
        refs.textSourceBtns.forEach(b => b.setAttribute(
            'aria-pressed', b.getAttribute('data-text-source') === state.textSource ? 'true' : 'false'));
    }

    // ============================================================ Save (direct write or download) ============================================================

    // If a repo folder is connected (File System Access API), write directly to the working tree;
    // otherwise (or on write error) fall back to ZBZ.Download.
    function layoutSourceMeta() {
        return {
            source: 'curated',
            original_source: state.layout.source || 'gemini',
            // Record image dimensions so the curated JSON is self-contained
            image_width: state.layout.image_width || 0,
            image_height: state.layout.image_height || 0
        };
    }

    // ============================================================ Events ============================================================

    function gotoPage(n) {
        if (!state.doc) return;
        const max = state.doc.page_count || 1;
        const target = Math.min(max, Math.max(1, n));
        if (target === state.page) return;
        if (!confirmLeavePage()) return;
        state.page = target;
        loadPage();
    }

    function bindEvents() {
        refs.btnPrev.addEventListener('click', () => gotoPage(state.page - 1));
        refs.btnNext.addEventListener('click', () => gotoPage(state.page + 1));
        if (refs.pageGoto) {
            refs.pageGoto.addEventListener('keydown', (e) => {
                if (e.key !== 'Enter') return;
                e.preventDefault();
                const n = parseInt(refs.pageGoto.value, 10);
                if (!isNaN(n)) { gotoPage(n); refs.pageGoto.value = ''; refs.pageGoto.blur(); }
            });
        }

        document.addEventListener('keydown', (e) => {
            // Ctrl+S saves even while an editor field has focus
            if ((e.ctrlKey || e.metaKey) && (e.key === 's' || e.key === 'S')) {
                e.preventDefault();
                if (refs.btnSave && !refs.btnSave.disabled) saveAll();
                return;
            }
            if (e.key === 'Escape' && entityPopover && !entityPopover.hidden) {
                e.preventDefault();
                closeEntityPopover(true);
                return;
            }
            if (e.target.matches('input, textarea, select, [contenteditable="true"]')) return;
            if (e.key === 'ArrowLeft')       refs.btnPrev.click();
            else if (e.key === 'ArrowRight') refs.btnNext.click();
            else if (e.key === 'Home')       { e.preventDefault(); gotoPage(1); }
            else if (e.key === 'End')        { e.preventDefault(); gotoPage(state.doc ? (state.doc.page_count || 1) : 1); }
        });

        refs.btnImageEdit.addEventListener('click', () => setImageEdit(!state.imageEdit));
        refs.btnEditOcr.addEventListener('click', () => toggleEdit('ocr'));
        refs.btnEditXml.addEventListener('click', () => toggleEdit('xml'));
        if (refs.btnMarkup) refs.btnMarkup.addEventListener('click', () => {
            state.teiMarkup = !state.teiMarkup;
            applyTeiMarkup();
        });
        if (refs.btnEntities) refs.btnEntities.addEventListener('click', () => setEntityMode(!state.entityMode));

        // Entity mentions open the popover (click and keyboard); delegated, the text panel
        // is re-rendered on every page change.
        refs.textBody.addEventListener('click', (e) => {
            if (!state.entityMode || !state.entityPage || !e.target.closest) return;
            const el = e.target.closest(ENTITY_MENTION_SEL);
            if (!el) return;
            e.preventDefault();
            showEntityPopover(el);
        });
        refs.textBody.addEventListener('keydown', (e) => {
            if (!state.entityMode || !state.entityPage) return;
            if (e.key !== 'Enter' && e.key !== ' ') return;
            const el = e.target.closest && e.target.closest(ENTITY_MENTION_SEL);
            if (!el) return;
            e.preventDefault();
            showEntityPopover(el);
        });
        refs.textBody.addEventListener('scroll', () => closeEntityPopover(false), { passive: true });
        window.addEventListener('resize', () => closeEntityPopover(false));
        refs.textSourceBtns.forEach(b => b.addEventListener('click', () => setTextSource(b.getAttribute('data-text-source'))));

        // Save (all streams directly to repo) + Export dropdown (single-file download)
        if (refs.btnSave) refs.btnSave.addEventListener('click', saveAll);
        if (refs.btnExportMenu) refs.btnExportMenu.addEventListener('click', (e) => { e.stopPropagation(); toggleExportMenu(); });
        refs.btnDlLayout.addEventListener('click', exportLayout);
        refs.btnDlText.addEventListener('click', exportText);
        refs.btnDlTei.addEventListener('click', exportTei);
        refs.btnDlManifest.addEventListener('click', exportManifest);

        // Identity chip (Initials): click -> inline field; Enter/blur commits, ESC cancels.
        if (refs.btnIdentity) refs.btnIdentity.addEventListener('click', startIdentityEdit);
        if (refs.identityInput) {
            refs.identityInput.addEventListener('blur', commitIdentityEdit);
            refs.identityInput.addEventListener('keydown', (e) => {
                if (e.key === 'Enter') { e.preventDefault(); refs.identityInput.blur(); }
                else if (e.key === 'Escape') { e.preventDefault(); cancelIdentityEdit(); }
            });
        }

        // E66: status pill click = cycle to next status
        refs.statusOcr.addEventListener('click', () => cycleStatus('ocr'));
        refs.statusLayout.addEventListener('click', () => cycleStatus('layout'));
        refs.statusTei.addEventListener('click', () => cycleStatus('tei'));

        // Warn before leaving with unsaved status changes
        window.addEventListener('beforeunload', (e) => {
            if (state.manifestDirty || state.layoutDirty || state.textDirty) {
                e.preventDefault();
                e.returnValue = '';
                return '';
            }
        });
    }

    ZBZ.Viewer = { init, state };
    document.addEventListener('DOMContentLoaded', init);
})();
