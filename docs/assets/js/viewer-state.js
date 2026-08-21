/**
 * viewer-state.js - Shared viewer state, DOM refs, asset bookkeeping
 *
 * First module of the viewer. Creates the ZBZ.Viewer namespace with the mutable
 * `state` every other viewer module reads and writes, the DOM refs, the page cache,
 * and the catalog-driven decision which mirror files are worth fetching.
 *
 * Namespace: ZBZ.Viewer
 */
(function () {
    'use strict';

    const $  = ZBZ.$;
    const $$ = ZBZ.$$;

    window.ZBZ.Viewer = {};

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

    // Vendored OpenSeadragon build under docs/assets/vendor/ (no third-party requests).
    const OSD_PREFIX = 'assets/vendor/openseadragon/images/';

    // Entity layer (generated mirror, written by scripts/entity/generate_entity_preview_data.py)
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

    Object.assign(ZBZ.Viewer, {
        state,
        refs,
        cache,
        STATUS_CYCLE,
        STATUS_LABEL,
        STATUS_LEGACY,
        STREAM_LABEL,
        STREAMS,
        ENTITY_STREAM,
        manifestStreams,
        OSD_PREFIX,
        ENTITY_INDEX_PATH,
        entityPagePath,
        entityWorklistPath,
        facsMapPath,
        ENTITY_CATEGORY_LABEL,
        ENTITY_MENTION_SEL,
        ENTITY_POP_SEL,
        INJECTED_TEXT_SEL,
        assetKnown,
        candidates,
        curatedLocally,
        noteCuratedLocally,
    });
})();
