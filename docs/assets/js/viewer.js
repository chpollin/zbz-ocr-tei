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
        textSource: 'tei',    // ocr | tei | xml
        // XML view scope: 'page' shows the current page slice (read-only, cheap),
        // 'full' the whole final TEI. Only 'full' may be edited, because writeTei
        // replaces {doc}_final.xml as a whole (E72).
        xmlScope: 'page',     // page | full
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
        entityMode: false,      // annotated reading view; on by default (?entities=0 opts out)
        entityAvailable: false, // an entity preview exists for the current document
        entityWorklist: null,   // {doc, pages: {N: [{gid, category, surface, text, occurrence,
                                //                rule, alternatives, matched_form, form_source,
                                //                evidence?, context}]}}
        entityPage: false,      // the current page is rendered from the entity preview
        entityCandidates: [],   // worklist entries of the current page (popover lookup)
        facsMap: null           // text page -> scan image name (generated {doc}_facs.json)
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
    const STREAM_LABEL = { ocr: 'OCR', layout: 'Layout', tei: 'TEI-XML', entities: 'Entities' };
    // Every document carries the three pipeline streams; `entities` exists only where an
    // entity preview does (page_manifest creates it), so its pill stays hidden otherwise.
    const STREAMS = ['ocr', 'layout', 'tei'];
    const ENTITY_STREAM = 'entities';
    // Streams of the loaded manifest, in pill order.
    const manifestStreams = () => {
        const present = state.manifest && state.manifest.streams;
        return (present && present[ENTITY_STREAM]) ? STREAMS.concat(ENTITY_STREAM) : STREAMS.slice();
    };

    const OSD_PREFIX = 'https://cdn.jsdelivr.net/npm/openseadragon@5.0.1/build/openseadragon/images/';

    // Entity layer (generated mirror, written by scripts/edition/generate_entity_preview_data.py)
    const ENTITY_INDEX_PATH = 'data/entities.json';
    const entityPagePath     = (doc, page) => 'data/pages/' + doc + '/' + doc + '_entity_p' + page + '.xml';
    const entityWorklistPath = (doc) => 'data/pages/' + doc + '/' + doc + '_entity_worklist.json';
    // Text page -> scan image, generated from pb@facs. Double-page scans carry more text
    // pages than images, stripped cover sheets fewer, so the sequential convention
    // "text page N = image N" breaks there.
    const facsMapPath = (doc) => 'data/pages/' + doc + '/' + doc + '_facs.json';
    const ENTITY_CATEGORY_LABEL = { person: 'Person', organisation: 'Organisation', work: 'Work' };
    const ENTITY_MENTION_SEL = '.tei__entity[data-ref], .tei__bibl[data-ref]';
    // Candidates (worklist) are shown inline as well; both open the same popover.
    const ENTITY_POP_SEL = ENTITY_MENTION_SEL + ', .entity-cand';
    // Text the renderer injects (page number, note number, figure label, gap) is not TEI
    // text and must not shift the occurrence count the generator computed.
    const INJECTED_TEXT_SEL = '.tei__pb, .tei__note-n, .tei__figure-label, .tei__gap';

    // Why the tool held back: the matcher rule in plain German. Unknown keys stay raw.
    const WORKLIST_RULE_LABEL = {
        'bare-surname':     'Nachname ohne Vollnennung',
        'anchored-surname': 'Nachname mit Vollnennung im Dokument',
        'short-title':      'Einwort-Titel, mehrdeutig',
        'legacy-form':      'Form aus Altindex, ungesichert',
        'adjective-form':   'Adjektivform',
        'caps-surname':     'Versalien-Nachname',
        'ambiguous-surname': 'Nachname, mehrere Träger',
        'crosses-markup':   'Nennung läuft über Markup hinweg',
        'speaker':          'Sprecherzeile'
    };
    const WORKLIST_RULE_SUFFIX = {
        'ambiguous':    'mehrere Kandidaten',
        'suspect':      'Homographen-Verdacht',
        'in-plain-bibl': 'in unreferenziertem bibl'
    };
    // Where the matched name form came from (matcher field form_source).
    const ENTITY_FORM_SOURCE_LABEL = {
        'headword':      'Lexikonform',
        'cache-variant': 'GND-Variante',
        'legacy':        'Altindex-Form',
        'surname-index': 'Nachnamen-Index'
    };
    // Typographic pre-sorting of one-word work titles (matcher field evidence).
    const ENTITY_EVIDENCE_LABEL = {
        'typographic': 'Einwort-Titel mit typographischem Beleg',
        'none':        'Einwort-Titel ohne typographischen Beleg (vermutlich Fachwort)'
    };

    function worklistRuleLabel(rule) {
        const parts = String(rule || '').split(':');
        const base = WORKLIST_RULE_LABEL[parts[0]] || parts[0] || 'unbekannte Regel';
        const extra = parts.slice(1).map(s => WORKLIST_RULE_SUFFIX[s] || s).filter(Boolean);
        return extra.length ? base + ' (' + extra.join(', ') + ')' : base;
    }

    // The check line of a candidate: a one-word title is judged by its typography,
    // everything else by the rule that found it.
    function candidateCheckLabel(entry) {
        return ENTITY_EVIDENCE_LABEL[entry.evidence] || worklistRuleLabel(entry.rule);
    }

    // Provenance of the hit: which listed form matched, and from which data channel.
    function candidateOriginLabel(entry) {
        if (!entry.matched_form) return '';
        const source = ENTITY_FORM_SOURCE_LABEL[entry.form_source] || entry.form_source;
        return source ? 'gefunden über ' + source + ': ' + entry.matched_form : '';
    }

    function candidateAlternatives(entry) {
        return (entry && Array.isArray(entry.alternatives)) ? entry.alternatives : [];
    }

    const cache = new ZBZ.Cache(40);

    // ---- Asset existence ----
    // The catalog entry carries `assets`: which mirror files generate_edition_data really
    // wrote for this document, as page lists ("*" = pages 1..page_count, else "1-9,12") or
    // a flag for document-wide files. Asking only for listed files keeps the browser console
    // free of 404 probes. A catalog without the field degrades to the previous probing.
    const ASSET_ALL = '*';
    const assetPages = new Map(); // 'doc:kind' -> Set of page numbers
    // '../output/...' resolves only when the repo root is the docroot (viewer under /docs/).
    // With docroot=docs/ (server-less viewer, GitHub Pages) it leaves the served tree and
    // can never be anything but 404.
    const OUTPUT_REACHABLE = location.pathname.indexOf('/docs/') !== -1;

    function assetPageSet(docId, kind, spec) {
        const key = docId + ':' + kind;
        let set = assetPages.get(key);
        if (!set) {
            set = new Set();
            spec.split(',').forEach(part => {
                const m = /^(\d+)(?:-(\d+))?$/.exec(part.trim());
                if (!m) return;
                const from = parseInt(m[1], 10);
                const to = m[2] ? parseInt(m[2], 10) : from;
                for (let p = from; p <= to; p++) set.add(p);
            });
            assetPages.set(key, set);
        }
        return set;
    }

    // true/false where the catalog knows the stream, null where it predates `assets`.
    function assetKnown(kind, page) {
        const doc = state.doc;
        const assets = doc && doc.assets;
        if (!assets) return null;
        const spec = assets[kind];
        if (spec === undefined) return false;
        if (spec === true) return true;
        if (spec === ASSET_ALL) return page >= 1 && page <= (doc.page_count || 0);
        return assetPageSet(doc.id, kind, spec).has(page);
    }

    // Layout curations this browser saved after the catalog was generated: they are not in
    // `assets` until the next generator run, so they are remembered here to keep the save
    // round trip intact.
    const CURATED_KEY = 'zbz.viewer.curated';
    const curatedLocal = new Set((() => {
        try { return JSON.parse(localStorage.getItem(CURATED_KEY)) || []; } catch (e) { return []; }
    })());
    const curatedLocally = (docId, page) => curatedLocal.has(docId + ':' + page);
    function noteCuratedLocally(docId, page) {
        curatedLocal.add(docId + ':' + page);
        try { localStorage.setItem(CURATED_KEY, JSON.stringify([...curatedLocal])); } catch (e) { /* storage off */ }
    }

    // Keeps the URLs that can resolve: mirror files the catalog lists, and ../output paths
    // only where they lie inside the served tree. An empty list means "do not fetch".
    function candidates(kind, page, urls) {
        const mirror = assetKnown(kind, page) !== false
            || (kind === 'layout_curated' && state.doc && curatedLocally(state.doc.id, page));
        return urls.filter(u => (u.indexOf('../') === 0) ? OUTPUT_REACHABLE : mirror);
    }

    // ---- DOM refs ----
    const refs = {
        subbar:         $('#doc-subbar'),
        docMeta:        $('#doc-meta'),
        btnPrev:        $('#btn-prev'),
        btnNext:        $('#btn-next'),
        pageGoto:       $('#page-goto'),
        pageTotal:      $('#page-total'),
        // Panel chrome: one dropdown for the view, one for the edit mode
        btnViewMenu:    $('#btn-view-menu'),
        viewMenu:       $('#view-menu'),
        viewItems:      $$('#view-menu .menu__item[data-view]'),
        viewToggleMarkup: $('#view-menu .menu__item[data-view-toggle="markup"]'),
        btnEditMenu:    $('#btn-edit-menu'),
        editMenu:       $('#edit-menu'),
        editItems:      $$('#edit-menu .menu__item[data-edit]'),
        imageBody:      $('#image-body'),
        textBody:       $('#text-body'),
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
        statusEntities: $('#status-entities'),
        statusHint:     $('#status-hint')
    };

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

    // ============================================================ Init ============================================================

    async function init() {
        bindEvents();
        updateEntityUi();

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

        state.entityMode = ZBZ.getParam('entities') !== '0';
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
        state.xmlScope = 'page';
        state.manifest = null;
        state.manifestDirty = false;
        state.facsMap = null;
        ZBZ.setParams({ doc: doc.id, page: state.page });
        document.title = (doc.title ? doc.title.slice(0, 60) + ' — ' : '') + 'Hersch Pipeline Viewer';

        // Show and populate sub-bar
        refs.subbar.hidden = false;
        renderDocMeta(doc);

        // Enable buttons
        refs.btnPrev.disabled = state.page <= 1;
        refs.btnNext.disabled = state.page >= textPageCount();
        if (refs.pageGoto) refs.pageGoto.disabled = false;
        syncPageInput();
        refs.btnDlLayout.disabled = false;
        refs.btnDlText.disabled = false;
        refs.btnDlTei.disabled = false;
        if (refs.btnExportMenu) refs.btnExportMenu.disabled = false;
        renderSaveState();

        // E66: load manifest for workflow status (parallel to page rendering)
        loadManifest(doc.id);

        // Facsimile mapping: must be known before the first page renders an image
        await loadFacsMap(doc.id);

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
        // Documents without an entity preview are not asked for one (catalog `assets`).
        const worklist = assetKnown('entity_worklist', 0) !== false
            ? await ZBZ.fetchJSON(entityWorklistPath(docId))
            : null;
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
            // The entity layer is a TEI reading view.
            state.textSource = 'tei';
        }
        updateEntityUi();
    }

    async function loadEntityPage(doc, page) {
        const ck = 'entity:' + doc + ':' + page;
        if (cache.has(ck)) return cache.get(ck);
        // Pages without an entity preview stay usable: null falls back to the pipeline TEI
        const res = await ZBZ.fetchFirstOk(candidates('entity', page, [entityPagePath(doc, page)]));
        const xml = res ? res.text : null;
        if (xml != null) cache.set(ck, xml);
        return xml;
    }

    // Availability of the entity view and the read-only lock it puts on the text editors
    // are both read by the two dropdowns.
    function updateEntityUi() {
        syncViewUi();
        updateEditButtons();
    }

    function setEntityMode(on) {
        const next = !!on;
        if (next === state.entityMode) return;
        if (next && !state.entityAvailable) return;
        state.entityMode = next;
        closeEntityPopover(false);
        if (next && state.textSource !== 'tei') {
            // setTextSource confirms unsaved edits, leaves edit mode and re-renders
            if (!setTextSource('tei')) { state.entityMode = false; updateEntityUi(); return; }
            ZBZ.setParams({ entities: null });
            updateEntityUi();
            return;
        }
        ZBZ.setParams({ entities: next ? null : 0 });
        updateEntityUi();
        renderTextPanel();
    }

    // Surfaces can carry <lb/> tags (names broken across lines); the worklist shows text.
    function plainSurface(surface) {
        return String(surface || '').replace(/<lb\b[^>]*>/g, ' ').replace(/\s+/g, ' ').trim();
    }

    function worklistEntries(page) {
        const pages = state.entityWorklist && state.entityWorklist.pages;
        return (pages && pages[String(page)]) || [];
    }

    function entryText(entry) {
        return entry.text || plainSurface(entry.surface);
    }

    // Candidates are marked in the rendered text itself: the generator says which
    // occurrence of the surface it means, the walker finds it. Whatever cannot be placed
    // is returned and stays visible as a list, so nothing is lost silently.
    function markWorklistCandidates(page) {
        const entries = worklistEntries(page);
        state.entityCandidates = entries;
        const wrap = refs.textBody.querySelector('.tei');
        if (!wrap) return entries.slice();
        const unplaced = [];
        entries.forEach((entry, index) => {
            const span = entry.occurrence
                ? markOccurrence(wrap, entryText(entry), entry.occurrence, index)
                : null;
            if (!span) unplaced.push(entry);
        });
        return unplaced;
    }

    function textNodesOf(root) {
        const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, {
            acceptNode: (node) => (node.parentElement && node.parentElement.closest(INJECTED_TEXT_SEL))
                ? NodeFilter.FILTER_REJECT
                : NodeFilter.FILTER_ACCEPT
        });
        const nodes = [];
        let node;
        while ((node = walker.nextNode())) nodes.push(node);
        return nodes;
    }

    function markOccurrence(root, text, occurrence, index) {
        if (!text) return null;
        const nodes = textNodesOf(root);
        const offsets = [];
        let acc = '';
        nodes.forEach(node => { offsets.push(acc.length); acc += node.nodeValue; });

        // non-overlapping scan, the same convention the generator counted with
        let at = -1, from = 0;
        for (let i = 0; i < occurrence; i++) {
            at = acc.indexOf(text, from);
            if (at < 0) return null;
            from = at + text.length;
        }
        const end = at + text.length;
        const nodeIndex = offsets.findIndex((start, i) => at >= start && at < start + nodes[i].nodeValue.length);
        if (nodeIndex < 0) return null;
        // A hit crossing element boundaries (e.g. an lb inside the name) cannot be wrapped
        // safely; the entry falls back to the list.
        if (end > offsets[nodeIndex] + nodes[nodeIndex].nodeValue.length) return null;

        const entry = state.entityCandidates[index] || {};
        const span = ZBZ.el('span', {
            cls: 'entity-cand',
            attrs: {
                'data-cand-index': String(index),
                role: 'button',
                tabindex: '0',
                'aria-label': text + ', Kandidat: ' + worklistRuleLabel(entry.rule)
            }
        });
        const range = document.createRange();
        range.setStart(nodes[nodeIndex], at - offsets[nodeIndex]);
        range.setEnd(nodes[nodeIndex], end - offsets[nodeIndex]);
        try { range.surroundContents(span); } catch (e) { return null; }
        return span;
    }

    // Only what could not be placed inline; the page count itself sits in the legend.
    function renderUnplacedWorklist(unplaced) {
        const old = refs.textBody.querySelector('.entity-worklist');
        if (old) old.remove();
        if (!unplaced.length) return;
        const box = ZBZ.el('aside', {
            cls: 'entity-worklist', attrs: { 'aria-label': 'Worklist entries without a position in the text' }
        });
        box.appendChild(ZBZ.el('div', {
            cls: 'entity-worklist__title', text: 'Nicht im Text verortet · ' + unplaced.length
        }));
        const list = ZBZ.el('ul', { cls: 'entity-worklist__list' });
        unplaced.forEach(entry => {
            const li = ZBZ.el('li', { cls: 'entity-worklist__item' });
            li.appendChild(ZBZ.el('span', { cls: 'entity-worklist__surface', text: entryText(entry) }));
            li.appendChild(ZBZ.el('span', {
                cls: 'entity-worklist__rule', text: worklistRuleLabel(entry.rule)
            }));
            li.appendChild(ZBZ.el('span', { cls: 'entity-worklist__context', text: entry.context || '' }));
            list.appendChild(li);
        });
        box.appendChild(list);
        const wrap = refs.textBody.querySelector('.tei');
        refs.textBody.insertBefore(box, wrap || refs.textBody.firstChild);
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

    // One row per bearer of an undecided candidate: label from the entity lookup,
    // id as the lobid link. No bearer is singled out.
    function entityAlternativeRow(gid) {
        const rec = (entityIndex && entityIndex[gid]) || null;
        const row = ZBZ.el('div', { cls: 'entity-pop__gid' });
        row.appendChild(ZBZ.el('span', {
            text: (rec ? rec.label : 'nicht in der kuratierten Liste') + ' · '
        }));
        row.appendChild(ZBZ.el('a', {
            cls: 'entity-pop__link', text: 'GND ' + gid,
            attrs: {
                href: (rec && rec.lobid) || 'https://lobid.org/gnd/' + encodeURIComponent(gid),
                target: '_blank', rel: 'noopener'
            }
        }));
        return row;
    }

    function showEntityPopover(el) {
        const candidate = el.classList.contains('entity-cand')
            ? (state.entityCandidates[Number(el.getAttribute('data-cand-index'))] || null)
            : null;
        const gid = candidate ? String(candidate.gid || '') : entityGid(el);
        const rec = (entityIndex && entityIndex[gid]) || null;
        // Several bearers mean the position is undecided; showing one of them as the
        // found entity is exactly the misreading this popover has to avoid.
        const alternatives = candidateAlternatives(candidate);
        const undecided = alternatives.length > 1;
        const pop = ensureEntityPopover();
        pop.className = 'entity-pop' + (candidate ? ' entity-pop--cand' : '');
        pop.innerHTML = '';
        pop.appendChild(ZBZ.el('button', {
            cls: 'entity-pop__close', html: '&times;',
            attrs: { type: 'button', 'aria-label': 'Close' },
            on: { click: () => closeEntityPopover(true) }
        }));
        pop.appendChild(ZBZ.el('div', {
            cls: 'entity-pop__label',
            text: (!undecided && rec) ? rec.label : el.textContent.trim()
        }));
        const meta = [];
        if (undecided) {
            meta.push(alternatives.length + ' Kandidaten');
        } else {
            if (rec && rec.category) meta.push(ENTITY_CATEGORY_LABEL[rec.category] || rec.category);
            if (rec && rec.dates) meta.push(rec.dates);
            if (!rec) meta.push('not in the curated entity list');
        }
        pop.appendChild(ZBZ.el('div', { cls: 'entity-pop__meta', text: meta.join(' · ') }));
        if (candidate) {
            // Provenance in plain words: why the tool did not set this annotation,
            // and which listed name form produced the hit.
            pop.appendChild(ZBZ.el('div', {
                cls: 'entity-pop__note',
                text: 'Zur Prüfung: ' + candidateCheckLabel(candidate)
            }));
            const origin = candidateOriginLabel(candidate);
            if (origin) pop.appendChild(ZBZ.el('div', { cls: 'entity-pop__meta', text: origin }));
        }
        if (undecided) {
            alternatives.forEach(alt => pop.appendChild(entityAlternativeRow(alt)));
        } else {
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
        if (e.target.closest && e.target.closest(ENTITY_POP_SEL)) return;
        closeEntityPopover(false);
    }

    // ============================================================ Workflow status (E66) ============================================================

    async function loadManifest(docId) {
        const m = await ZBZ.fetchJSON('data/manifests/' + encodeURIComponent(docId) + '_manifest.json');
        if (m && m.streams) {
            // Migrate legacy status values (v2 -> v3)
            Object.keys(m.streams).forEach(s => {
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
        const present = manifestStreams();
        STREAMS.concat(ENTITY_STREAM).forEach(stream => {
            const btn = refs['status' + stream.charAt(0).toUpperCase() + stream.slice(1)];
            if (!btn) return;
            btn.hidden = present.indexOf(stream) < 0;
            if (btn.hidden) return;
            btn.disabled = !enable;
            const status = streamStatus(stream);
            // Update classes (remove old status classes)
            btn.className = 'status-pill status-pill--' + status + (state.dirtyStreams.has(stream) ? ' status-pill--dirty' : '');
            const sm = (state.manifest && state.manifest.streams && state.manifest.streams[stream]) || {};
            const history = sm.history || [];
            const last = history.length ? history[history.length - 1] : null;
            // The compact pill shows stream name + colored dot only; the status word and
            // the handover meaning of `unverifiziert` live in the tooltip.
            const baseLine = STREAM_LABEL[stream] + ': ' + STATUS_LABEL[status]
                + (status === 'unverifiziert' ? ' (pipeline output exists, not yet human-verified)' : '');
            btn.title = baseLine
                + (last ? '\nlast: ' + last.to + ' · ' + (last.by || '?') + ' · ' + (last.at || '').slice(0, 16) : '')
                + '\nClick cycles: unverified -> in progress -> verified';
            // announce the current status, not just "set status" (a11y)
            btn.setAttribute('aria-label', STREAM_LABEL[stream] + ' status: ' + STATUS_LABEL[status] + ' (click to cycle)');
            btn.innerHTML =
                '<span class="status-pill__stream">' + STREAM_LABEL[stream] + '</span>'
                + '<span class="status-pill__dot"></span>';
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
                if (await persistSilent(
                    () => ZBZ.FsAccess.writeLayout(state.doc.id, state.page, state.layout.regions, meta),
                    () => ZBZ.Download.layout(state.doc.id, state.page, state.layout.regions, meta)
                )) {
                    noteCuratedLocally(state.doc.id, state.page); // catalog learns it on the next generator run
                } else {
                    downloaded = true;
                }
                state.layoutDirty = false;
                setRegionCount(state.layout.regions.length + ' regions');
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
        closeDropdown();
    }
    function exportText() {
        if (!state.doc) return;
        const content = (state._currentEditedText != null) ? state._currentEditedText : state._currentText;
        if (!content) { ZBZ.toast('No text loaded', 'warn'); return; }
        ZBZ.Download.text(state.doc.id, state.page, content);
        closeDropdown();
    }
    async function exportTei() {
        if (!state.doc) return;
        let xml = state._currentEditedText;
        // Only a full-scope XML edit is a complete document; anything else exports the file.
        if (!xml || state.textSource !== 'xml' || state.xmlScope !== 'full') {
            xml = await loadTeiFinal(state.doc.id);
        }
        if (!xml) { ZBZ.toast('No TEI available', 'warn'); return; }
        ZBZ.Download.tei(state.doc.id, xml, 'curated');
        closeDropdown();
    }
    function exportManifest() {
        if (!state.manifest) { ZBZ.toast('No manifest loaded', 'warn'); return; }
        ZBZ.Download.manifest(state.doc.id, state.manifest);
        closeDropdown();
    }

    // ============================================================ Dropdown menus (export, view, edit) ============================================================

    // One open menu at a time; outside click and Escape close it. The menus are
    // position:fixed, so a panel with overflow:hidden cannot clip them; the price is
    // placing them by hand and closing them on resize.
    let openMenu = null;   // { btn, menu }

    function positionDropdown(btn, menu, align) {
        const r = btn.getBoundingClientRect();
        menu.style.visibility = 'hidden';
        menu.style.left = '0px';
        menu.style.top = '0px';
        const w = menu.offsetWidth;
        const raw = (align === 'right') ? (r.right - w) : r.left;
        menu.style.left = Math.max(8, Math.min(raw, window.innerWidth - w - 8)) + 'px';
        menu.style.top = (r.bottom + 4) + 'px';
        menu.style.visibility = '';
    }

    function openDropdown(btn, menu) {
        closeDropdown();
        menu.hidden = false;
        positionDropdown(btn, menu, menu.classList.contains('menu--right') ? 'right' : 'left');
        btn.setAttribute('aria-expanded', 'true');
        openMenu = { btn: btn, menu: menu };
        setTimeout(() => document.addEventListener('click', onDocClickForMenu), 0);
    }

    function closeDropdown(restoreFocus) {
        document.removeEventListener('click', onDocClickForMenu);
        if (!openMenu) return;
        openMenu.menu.hidden = true;
        openMenu.btn.setAttribute('aria-expanded', 'false');
        if (restoreFocus) openMenu.btn.focus();
        openMenu = null;
    }

    function toggleDropdown(btn, menu) {
        if (menu.hidden) openDropdown(btn, menu); else closeDropdown();
    }

    function onDocClickForMenu(e) {
        if (!openMenu) return;
        if (openMenu.menu.contains(e.target) || e.target === openMenu.btn) return;
        closeDropdown();
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
        syncPageInput();
        refs.btnPrev.disabled = page <= 1;
        refs.btnNext.disabled = page >= textPageCount();
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
        return name ? 'images/' + docId + '/' + name : ZBZ.path.image(docId, page);
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
        renderSaveState();
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
            renderSaveState();
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
                renderSaveState();
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
        ['Zur Prüfung',   '.entity-cand',                     'cand']
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
        applyTeiMarkup();   // dropdown label; the render callback re-applies highlighting
        renderTextPanel();
        return true;
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

    function bindEvents() {
        refs.btnPrev.addEventListener('click', () => gotoPage(state.page - 1));
        refs.btnNext.addEventListener('click', () => gotoPage(state.page + 1));
        if (refs.pageGoto) {
            refs.pageGoto.addEventListener('focus', () => refs.pageGoto.select());
            refs.pageGoto.addEventListener('blur', syncPageInput);
            refs.pageGoto.addEventListener('keydown', (e) => {
                if (e.key !== 'Enter' && e.key !== 'Escape') return;
                e.preventDefault();
                const n = (e.key === 'Enter') ? parseInt(refs.pageGoto.value, 10) : NaN;
                if (!isNaN(n)) gotoPage(n);
                syncPageInput();   // invalid input and a cancelled jump revert
                refs.pageGoto.blur();
            });
        }

        document.addEventListener('keydown', (e) => {
            // Ctrl+S saves even while an editor field has focus
            if ((e.ctrlKey || e.metaKey) && (e.key === 's' || e.key === 'S')) {
                e.preventDefault();
                if (refs.btnSave && !refs.btnSave.disabled) saveAll();
                return;
            }
            if (e.key === 'Escape' && openMenu) {
                e.preventDefault();
                closeDropdown(true);
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
            else if (e.key === 'End')        { e.preventDefault(); gotoPage(state.doc ? textPageCount() : 1); }
        });

        // View + edit dropdowns (same handlers as the buttons they replace)
        if (refs.btnViewMenu) refs.btnViewMenu.addEventListener('click', (e) => {
            e.stopPropagation();
            toggleDropdown(refs.btnViewMenu, refs.viewMenu);
        });
        refs.viewItems.forEach(item =>
            item.addEventListener('click', () => setView(item.getAttribute('data-view'))));
        if (refs.viewToggleMarkup) refs.viewToggleMarkup.addEventListener('click', toggleMarkupHighlight);
        if (refs.btnEditMenu) refs.btnEditMenu.addEventListener('click', (e) => {
            e.stopPropagation();
            toggleDropdown(refs.btnEditMenu, refs.editMenu);
        });
        refs.editItems.forEach(item =>
            item.addEventListener('click', () => toggleEditMode(item.getAttribute('data-edit'))));

        // Entity mentions open the popover (click and keyboard); delegated, the text panel
        // is re-rendered on every page change.
        refs.textBody.addEventListener('click', (e) => {
            if (!state.entityMode || !state.entityPage || !e.target.closest) return;
            const el = e.target.closest(ENTITY_POP_SEL);
            if (!el) return;
            e.preventDefault();
            showEntityPopover(el);
        });
        refs.textBody.addEventListener('keydown', (e) => {
            if (!state.entityMode || !state.entityPage) return;
            if (e.key !== 'Enter' && e.key !== ' ') return;
            const el = e.target.closest && e.target.closest(ENTITY_POP_SEL);
            if (!el) return;
            e.preventDefault();
            showEntityPopover(el);
        });
        refs.textBody.addEventListener('scroll', () => closeEntityPopover(false), { passive: true });
        // The menus are placed by hand, so a resize invalidates their position.
        window.addEventListener('resize', () => { closeEntityPopover(false); closeDropdown(); });

        // Save (all streams directly to repo) + Export dropdown (single-file download)
        if (refs.btnSave) refs.btnSave.addEventListener('click', saveAll);
        if (refs.btnExportMenu) refs.btnExportMenu.addEventListener('click', (e) => {
            e.stopPropagation();
            toggleDropdown(refs.btnExportMenu, refs.exportMenu);
        });
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
        if (refs.statusEntities) refs.statusEntities.addEventListener('click', () => cycleStatus(ENTITY_STREAM));

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
