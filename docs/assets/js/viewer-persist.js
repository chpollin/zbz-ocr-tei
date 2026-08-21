/**
 * viewer-persist.js - Save, export and the repo folder connection
 *
 * One Save writes every unsaved stream at once: layout and text of the current page,
 * and the manifest with the workflow status. Writes go into the working tree through
 * the File System Access API, or fall back to a download per file.
 *
 * Namespace: ZBZ.Viewer
 */
(function () {
    'use strict';

    const V = ZBZ.Viewer;
    const state = V.state;
    const refs  = V.refs;
    const cache = V.cache;
    const { noteCuratedLocally } = V;

    // Sibling modules, resolved through ZBZ.Viewer at call time (load order independent).
    const closeDropdown     = (...a) => V.closeDropdown(...a);
    const renderStatusPills = (...a) => V.renderStatusPills(...a);
    const currentAuthor     = (...a) => V.currentAuthor(...a);
    const startIdentityEdit = (...a) => V.startIdentityEdit(...a);
    const setRegionCount    = (...a) => V.setRegionCount(...a);
    const loadTeiFinal      = (...a) => V.loadTeiFinal(...a);

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
    // Native <dialog>: modality, the backdrop, focus containment and Escape come from
    // the platform, so the only thing left is routing Escape to the cancel path.
    let fsaInfoCancelled = null;

    function showFsaInfo(onGo, onCancel) {
        if (!refs.fsaInfo || !refs.fsaInfo.showModal) { onGo(); return; }
        if (refs.fsaInfoGo) refs.fsaInfoGo.onclick = onGo;
        if (refs.fsaInfoCancel) refs.fsaInfoCancel.onclick = onCancel;
        fsaInfoCancelled = onCancel;
        refs.fsaInfo.showModal();
        if (refs.fsaInfoGo) refs.fsaInfoGo.focus();
    }

    function hideFsaInfo() {
        fsaInfoCancelled = null;
        if (refs.fsaInfo && refs.fsaInfo.open) refs.fsaInfo.close();
    }

    // Escape on the native dialog resolves the connect promise as a cancel.
    function cancelFsaInfo() {
        const cancel = fsaInfoCancelled;
        fsaInfoCancelled = null;
        if (cancel) cancel();
    }

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

    Object.assign(ZBZ.Viewer, {
        persistSilent,
        renderSaveState,
        confirmLeavePage,
        saveAll,
        exportLayout,
        exportText,
        exportTei,
        exportManifest,
        connectWithInfo,
        showFsaInfo,
        hideFsaInfo,
        cancelFsaInfo,
        layoutSourceMeta,
    });

    // Every dirty flag change re-renders the Save button and its tooltip.
    ZBZ.bus.on('dirty:changed', () => renderSaveState());
})();
