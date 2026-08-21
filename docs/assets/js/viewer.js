/**
 * viewer.js - Viewer shell: init, document selection, dropdown menus, event wiring
 *
 * Last module of the viewer. Resolves ?doc= against the catalog, hands the document to
 * the page, entity and status modules, and owns the panel dropdowns and the global
 * key bindings.
 *
 * Module load order: viewer-state, viewer-entities, viewer-status, viewer-persist,
 * viewer-page, viewer. Cross-module calls go through ZBZ.Viewer; state changes that
 * several modules react to travel as ZBZ.bus events (doc:changed, page:changed,
 * dirty:changed, entity-mode:changed).
 *
 * Namespace: ZBZ.Viewer
 */
(function () {
    'use strict';

    const $$ = ZBZ.$$;
    const V = ZBZ.Viewer;
    const state = V.state;
    const refs  = V.refs;
    const { ENTITY_POP_SEL, ENTITY_STREAM } = V;

    // Sibling modules, resolved through ZBZ.Viewer at call time (load order independent).
    const updateEntityUi        = (...a) => V.updateEntityUi(...a);
    const loadEntityAssets      = (...a) => V.loadEntityAssets(...a);
    const showEntityPopover     = (...a) => V.showEntityPopover(...a);
    const closeEntityPopover    = (...a) => V.closeEntityPopover(...a);
    const renderIdentity        = (...a) => V.renderIdentity(...a);
    const renderStatusPills     = (...a) => V.renderStatusPills(...a);
    const cycleStatus           = (...a) => V.cycleStatus(...a);
    const startIdentityEdit     = (...a) => V.startIdentityEdit(...a);
    const commitIdentityEdit    = (...a) => V.commitIdentityEdit(...a);
    const cancelIdentityEdit    = (...a) => V.cancelIdentityEdit(...a);
    const renderSaveState       = (...a) => V.renderSaveState(...a);
    const saveAll               = (...a) => V.saveAll(...a);
    const exportLayout          = (...a) => V.exportLayout(...a);
    const exportText            = (...a) => V.exportText(...a);
    const exportTei             = (...a) => V.exportTei(...a);
    const exportManifest        = (...a) => V.exportManifest(...a);
    const loadPage              = (...a) => V.loadPage(...a);
    const loadFacsMap           = (...a) => V.loadFacsMap(...a);
    const renderDocMeta         = (...a) => V.renderDocMeta(...a);
    const textPageCount         = (...a) => V.textPageCount(...a);
    const syncPageInput         = (...a) => V.syncPageInput(...a);
    const gotoPage              = (...a) => V.gotoPage(...a);
    const setView               = (...a) => V.setView(...a);
    const toggleMarkupHighlight = (...a) => V.toggleMarkupHighlight(...a);
    const toggleEditMode        = (...a) => V.toggleEditMode(...a);

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
        ZBZ.bus.emit('doc:changed', doc.id);

        // Facsimile mapping: must be known before the first page renders an image
        await loadFacsMap(doc.id);

        // Entity layer: must be known before the first text render decides its source
        await loadEntityAssets(doc.id);

        await loadPage();
    }

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

    // Roving tabindex: a menu is one tab stop, the arrow keys move inside it.
    function menuItems(menu) {
        return $$('.menu__item', menu).filter(i => !i.disabled && !i.hidden);
    }

    function focusMenuItem(menu, index) {
        const items = menuItems(menu);
        if (!items.length) return;
        const at = (index + items.length) % items.length;
        items.forEach((i, k) => i.setAttribute('tabindex', k === at ? '0' : '-1'));
        items[at].focus();
    }

    function moveMenuFocus(menu, delta) {
        const items = menuItems(menu);
        const at = items.indexOf(document.activeElement);
        focusMenuItem(menu, at < 0 ? 0 : at + delta);
    }

    function onMenuKeydown(e) {
        if (!openMenu) return false;
        const menu = openMenu.menu;
        if (e.key === 'ArrowDown')      { e.preventDefault(); moveMenuFocus(menu, 1); return true; }
        if (e.key === 'ArrowUp')        { e.preventDefault(); moveMenuFocus(menu, -1); return true; }
        if (e.key === 'Home')           { e.preventDefault(); focusMenuItem(menu, 0); return true; }
        if (e.key === 'End')            { e.preventDefault(); focusMenuItem(menu, menuItems(menu).length - 1); return true; }
        return false;
    }

    function openDropdown(btn, menu) {
        closeDropdown();
        menu.hidden = false;
        positionDropdown(btn, menu, menu.classList.contains('menu--right') ? 'right' : 'left');
        btn.setAttribute('aria-expanded', 'true');
        openMenu = { btn: btn, menu: menu };
        focusMenuItem(menu, 0);
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
            if (openMenu && onMenuKeydown(e)) return;
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

        // Escape on the native dialog resolves the connect promise as a cancel.
        if (refs.fsaInfo && refs.fsaInfo.showModal) {
            refs.fsaInfo.addEventListener('cancel', () => ZBZ.Viewer.cancelFsaInfo());
        }

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

    Object.assign(ZBZ.Viewer, {
        init,
        positionDropdown,
        openDropdown,
        closeDropdown,
        toggleDropdown,
    });

    document.addEventListener('DOMContentLoaded', init);
})();
