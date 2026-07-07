/**
 * fs-access.js — Direct write to the working tree (File System Access API)
 *
 * Alternative to ZBZ.Download: writes curated files directly into the repo folder
 * the user has granted access to once, instead of offering them as downloads. This
 * removes the need to place files manually. A subsequent pipeline run regenerates the TEI:
 *
 *   python -m scripts.tei.tei_unified --doc {DOC} --reassemble ; \
 *   python -m scripts.edition.generate_edition_data --mirror-only
 *
 * Available only in Chromium (showDirectoryPicker) and in a secure context (localhost
 * or HTTPS). Where unavailable, ZBZ.Download remains the path (fallback in viewer.js).
 * The directory handle is persisted in IndexedDB (structured-cloneable; not serializable
 * in localStorage). Write permission must be re-granted per session via a user gesture,
 * so the "Connect repo folder" button stays visible.
 *
 * Canonical target paths (aligned with the backend consumers in scripts/core/loaders.py):
 *   Layout   -> output/layout/{doc}/{doc}_p{NNN}_layout_curated.json
 *   OCR/Text -> output/ocr_curated/{doc}_p{N}.md
 *   Manifest -> output/tei_final/{doc}_manifest.json
 *   TEI      -> output/tei_final/{doc}_final.xml   (overwrites the single source of truth)
 *
 * Mirror paths (additional): the server-less viewer runs with docroot=docs/ and reads
 * exclusively from docs/data/ on reload -- output/ is not reachable from there. So that
 * "Save" shows the curated state immediately (without a backend run) even after a reload,
 * each function also writes the identical payload to the mirror:
 *   Layout   -> docs/data/pages/{doc}/{doc}_p{NNN}_layout_curated.json  (fetchLayout reads curated first)
 *   OCR/Text -> docs/data/pages/{doc}/{doc}_p{N}.md                     (viewer source 'mistral')
 *   Manifest -> docs/data/manifests/{doc}_manifest.json                 (viewer + catalog status column)
 *   TEI      -> docs/data/pages/{doc}/{doc}_final.xml                   (per-page TEI only after --reassemble)
 * A later `generate_edition_data --mirror-only` reproduces exactly the same mirror files.
 *
 * Namespace: ZBZ.FsAccess
 */
(function () {
    'use strict';

    const available = typeof window.showDirectoryPicker === 'function';

    const state = {
        root: null,        // FileSystemDirectoryHandle for the repo root
        connected: false
    };

    // ---- IndexedDB: minimal Promise wrapper for a single handle ----
    const IDB_NAME = 'zbz-fs';
    const IDB_STORE = 'handles';
    const IDB_KEY = 'repoRoot';

    function idbOpen() {
        return new Promise((resolve, reject) => {
            if (!window.indexedDB) { reject(new Error('IndexedDB not available')); return; }
            const req = indexedDB.open(IDB_NAME, 1);
            req.onupgradeneeded = () => req.result.createObjectStore(IDB_STORE);
            req.onsuccess = () => resolve(req.result);
            req.onerror = () => reject(req.error);
        });
    }

    function idbGet(key) {
        return idbOpen().then(db => new Promise((resolve, reject) => {
            const tx = db.transaction(IDB_STORE, 'readonly');
            const req = tx.objectStore(IDB_STORE).get(key);
            req.onsuccess = () => resolve(req.result);
            req.onerror = () => reject(req.error);
        })).catch(() => null);
    }

    function idbPut(key, val) {
        return idbOpen().then(db => new Promise((resolve, reject) => {
            const tx = db.transaction(IDB_STORE, 'readwrite');
            tx.objectStore(IDB_STORE).put(val, key);
            tx.oncomplete = () => resolve(true);
            tx.onerror = () => reject(tx.error);
        })).catch(() => false);
    }

    function idbDel(key) {
        return idbOpen().then(db => new Promise((resolve) => {
            const tx = db.transaction(IDB_STORE, 'readwrite');
            tx.objectStore(IDB_STORE).delete(key);
            tx.oncomplete = () => resolve(true);
            tx.onerror = () => resolve(false);
        })).catch(() => false);
    }

    // ---- Permission ----
    async function ensurePermission(handle, request) {
        if (!handle || !handle.queryPermission) return true; // older impl: optimistic
        const opts = { mode: 'readwrite' };
        if (await handle.queryPermission(opts) === 'granted') return true;
        if (request && await handle.requestPermission(opts) === 'granted') return true;
        return false;
    }

    // ---- Folder plausibility ----
    async function hasChild(handle, name) {
        try { await handle.getDirectoryHandle(name); return true; }
        catch (e) { return false; }
    }
    /** Heuristic: is this the project root folder? (docs/ + scripts/ are git-tracked). */
    async function looksLikeRepoRoot(handle) {
        return (await hasChild(handle, 'docs')) || (await hasChild(handle, 'scripts'));
    }

    // ---- Connection ----

    /** On load: restore a persisted handle (without a permission prompt). */
    async function init() {
        if (!available) return;
        const handle = await idbGet(IDB_KEY);
        if (!handle) return;
        // queryPermission WITHOUT request (no gesture context on load)
        if (await ensurePermission(handle, false)) {
            state.root = handle;
            state.connected = true;
            ZBZ.log('FsAccess', 'repo folder reconnected: ' + (handle.name || '?'));
        } else {
            state.root = handle; // keep handle, permission must be re-granted via click
        }
    }

    /** Via user gesture: choose the repo folder and grant write access. */
    async function connect() {
        if (!available) { ZBZ.toast('Direct save is not supported by this browser', 'warn'); return false; }
        try {
            // If a handle already exists, request permission there first (no new picker)
            if (state.root && await ensurePermission(state.root, true)) {
                state.connected = true;
                ZBZ.log('FsAccess', 'write access granted: ' + (state.root.name || '?'));
                return true;
            }
            const handle = await window.showDirectoryPicker({ mode: 'readwrite', id: 'zbz-repo' });
            if (!(await ensurePermission(handle, true))) {
                ZBZ.toast('Write access not granted', 'warn');
                return false;
            }
            state.root = handle;
            state.connected = true;
            await idbPut(IDB_KEY, handle);
            ZBZ.log('FsAccess', 'repo folder connected: ' + (handle.name || '?'));
            if (!(await looksLikeRepoRoot(handle))) {
                ZBZ.toast('Warning: "' + (handle.name || '?') + '" does not look like the project folder (expected zbz-ocr-tei with docs/ and scripts/). Reconnect if needed.', 'warn');
            }
            return true;
        } catch (err) {
            if (err && err.name === 'AbortError') return false; // user cancelled the picker
            ZBZ.log('FsAccess', 'connect error: ' + (err && err.message));
            ZBZ.toast('Connect failed: ' + (err && err.message), 'error');
            return false;
        }
    }

    async function disconnect() {
        state.root = null;
        state.connected = false;
        await idbDel(IDB_KEY);
        ZBZ.log('FsAccess', 'repo folder disconnected');
    }

    function isConnected() { return state.connected && !!state.root; }

    // ---- Write ----

    /** Writes content to relPath (relative to repo root), creating directories as needed. */
    async function writeFile(relPath, content) {
        if (!isConnected()) throw new Error('not connected');
        // Only CHECK write permission (queryPermission), do not request it: requestPermission
        // needs a fresh user gesture, which is already consumed after the folder dialog.
        // Permission was granted during connect (with gesture) -- checking it here is sufficient.
        if (!(await ensurePermission(state.root, false))) {
            throw new Error('write access not active -- reconnect the repo folder');
        }
        const segs = relPath.split('/').filter(Boolean);
        const fileName = segs.pop();
        let dir = state.root;
        for (const seg of segs) {
            dir = await dir.getDirectoryHandle(seg, { create: true });
        }
        const fileHandle = await dir.getFileHandle(fileName, { create: true });
        const writable = await fileHandle.createWritable();
        await writable.write(content);
        await writable.close();
        ZBZ.log('FsAccess', 'written: ' + relPath + ' (' + (content.length / 1024).toFixed(1) + ' KB)');
        return relPath;
    }

    function layoutPath(doc, page) {
        return `output/layout/${doc}/${doc}_p${ZBZ.padPage(page)}_layout_curated.json`;
    }
    function layoutMirrorPath(doc, page) {
        return `docs/data/pages/${doc}/${doc}_p${ZBZ.padPage(page)}_layout_curated.json`;
    }

    async function writeLayout(doc, page, regions, sourceMeta) {
        const out = Object.assign({}, sourceMeta || {}, {
            regions: regions,
            curated: true,
            curated_at: new Date().toISOString()
        });
        const json = JSON.stringify(out, null, 2);
        const canonical = await writeFile(layoutPath(doc, page), json);
        await writeFile(layoutMirrorPath(doc, page), json);  // Mirror -> viewer reload
        return canonical;
    }

    async function writeText(doc, page, content) {
        const canonical = await writeFile(`output/ocr_curated/${doc}_p${page}.md`, content);
        await writeFile(`docs/data/pages/${doc}/${doc}_p${page}.md`, content);  // Mirror -> viewer reload
        return canonical;
    }

    async function writeTei(doc, xml) {
        const canonical = await writeFile(`output/tei_final/${doc}_final.xml`, xml);
        await writeFile(`docs/data/pages/${doc}/${doc}_final.xml`, xml);  // Mirror (final; per-page only after --reassemble)
        return canonical;
    }

    async function writeManifest(doc, manifestObj) {
        const json = JSON.stringify(manifestObj, null, 2);
        const canonical = await writeFile(`output/tei_final/${doc}_manifest.json`, json);
        await writeFile(`docs/data/manifests/${doc}_manifest.json`, json);  // Mirror -> viewer + catalog
        return canonical;
    }

    ZBZ.FsAccess = {
        available,
        init,
        connect,
        disconnect,
        isConnected,
        rootName: () => (state.root && state.root.name) || null,
        writeLayout,
        writeText,
        writeTei,
        writeManifest
    };
    ZBZ.log('FsAccess', 'ready' + (available ? '' : ' (not supported)'));
})();
