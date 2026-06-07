/**
 * fs-access.js — Direkt-Schreiben in den Working Tree (File System Access API)
 *
 * Alternative zu ZBZ.Download: schreibt kuratierte Dateien direkt in den vom Nutzer
 * einmal freigegebenen Repo-Ordner, statt sie als Download anzubieten. Damit entfaellt
 * das manuelle Ablegen. Anschliessend regeneriert ein Pipeline-Lauf das TEI:
 *
 *   python -m scripts.tei.tei_unified --doc {DOC} --reassemble ; \
 *   python -m scripts.edition.generate_edition_data --mirror-only
 *
 * Verfuegbar nur in Chromium (showDirectoryPicker) und im secure context (localhost
 * oder HTTPS). Wo nicht verfuegbar, bleibt ZBZ.Download der Pfad (Fallback in viewer.js).
 * Der Verzeichnis-Handle wird in IndexedDB persistiert (structured-cloneable; in
 * localStorage nicht serialisierbar). Schreibrecht muss pro Sitzung per Geste re-granted
 * werden -- daher bleibt der Verbinden-Button sichtbar.
 *
 * Zielpfade (kanonisch, an die Backend-Konsumenten in scripts/core/loaders.py angelehnt):
 *   Layout   -> output/layout/{doc}/{doc}_p{NNN}_layout_curated.json
 *   OCR/Text -> output/ocr_curated/{doc}_p{N}.md
 *   Manifest -> output/tei_final/{doc}_manifest.json
 *   TEI      -> output/tei_final/{doc}_final.xml   (ueberschreibt die Single Source of Truth)
 *
 * Mirror-Pfade (zusaetzlich): Der server-lose Viewer laeuft mit Docroot=docs/ und liest beim
 * Reload AUSSCHLIESSLICH aus docs/data/ -- output/ ist von dort nicht erreichbar. Damit
 * 'Speichern' die Kuration sofort (ohne Backend-Lauf) auch nach einem Reload zeigt, schreibt
 * jede Funktion die identische Nutzlast zusaetzlich in den Mirror:
 *   Layout   -> docs/data/pages/{doc}/{doc}_p{NNN}_layout_curated.json  (fetchLayout liest curated zuerst)
 *   OCR/Text -> docs/data/pages/{doc}/{doc}_p{N}.md                     (Viewer-Quelle 'mistral')
 *   Manifest -> docs/data/manifests/{doc}_manifest.json                (Viewer + Katalog-Statusspalte)
 *   TEI      -> docs/data/pages/{doc}/{doc}_final.xml                   (Per-Seiten-TEI erst nach --reassemble)
 * Ein spaeterer `generate_edition_data --mirror-only` reproduziert exakt dieselben Mirror-Dateien.
 *
 * Namespace: ZBZ.FsAccess
 */
(function () {
    'use strict';

    const available = typeof window.showDirectoryPicker === 'function';

    const state = {
        root: null,        // FileSystemDirectoryHandle des Repo-Roots
        connected: false
    };

    // ---- IndexedDB: kleiner Promise-Wrapper fuer einen einzigen Handle ----
    const IDB_NAME = 'zbz-fs';
    const IDB_STORE = 'handles';
    const IDB_KEY = 'repoRoot';

    function idbOpen() {
        return new Promise((resolve, reject) => {
            if (!window.indexedDB) { reject(new Error('IndexedDB nicht verfuegbar')); return; }
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
        if (!handle || !handle.queryPermission) return true; // aeltere Impl: optimistisch
        const opts = { mode: 'readwrite' };
        if (await handle.queryPermission(opts) === 'granted') return true;
        if (request && await handle.requestPermission(opts) === 'granted') return true;
        return false;
    }

    // ---- Ordner-Plausibilitaet ----
    async function hasChild(handle, name) {
        try { await handle.getDirectoryHandle(name); return true; }
        catch (e) { return false; }
    }
    /** Heuristik: ist das der Projekt-Wurzelordner? (docs/ + scripts/ sind git-getrackt). */
    async function looksLikeRepoRoot(handle) {
        return (await hasChild(handle, 'docs')) || (await hasChild(handle, 'scripts'));
    }

    // ---- Verbindung ----

    /** Beim Laden: persistierten Handle wiederherstellen (ohne Permission-Prompt). */
    async function init() {
        if (!available) return;
        const handle = await idbGet(IDB_KEY);
        if (!handle) return;
        // queryPermission OHNE request (kein Gesture-Kontext beim Laden)
        if (await ensurePermission(handle, false)) {
            state.root = handle;
            state.connected = true;
            ZBZ.log('FsAccess', 'Repo-Ordner wiederverbunden: ' + (handle.name || '?'));
        } else {
            state.root = handle; // Handle behalten, Permission muss per Klick re-granted werden
        }
    }

    /** Per User-Geste: Repo-Ordner waehlen und Schreibrecht erteilen. */
    async function connect() {
        if (!available) { ZBZ.toast('Direkt-Speichern wird von diesem Browser nicht unterstuetzt', 'warn'); return false; }
        try {
            // Falls ein Handle existiert, zuerst dort Permission anfragen (kein erneuter Picker)
            if (state.root && await ensurePermission(state.root, true)) {
                state.connected = true;
                ZBZ.log('FsAccess', 'Schreibrecht erteilt: ' + (state.root.name || '?'));
                return true;
            }
            const handle = await window.showDirectoryPicker({ mode: 'readwrite', id: 'zbz-repo' });
            if (!(await ensurePermission(handle, true))) {
                ZBZ.toast('Kein Schreibrecht erteilt', 'warn');
                return false;
            }
            state.root = handle;
            state.connected = true;
            await idbPut(IDB_KEY, handle);
            ZBZ.log('FsAccess', 'Repo-Ordner verbunden: ' + (handle.name || '?'));
            if (!(await looksLikeRepoRoot(handle))) {
                ZBZ.toast('Achtung: "' + (handle.name || '?') + '" sieht nicht nach dem Projekt-Ordner aus (erwartet zbz-ocr-tei mit docs/ und scripts/). Ggf. neu verbinden.', 'warn');
            }
            return true;
        } catch (err) {
            if (err && err.name === 'AbortError') return false; // Nutzer hat Picker abgebrochen
            ZBZ.log('FsAccess', 'connect-Fehler: ' + (err && err.message));
            ZBZ.toast('Verbinden fehlgeschlagen: ' + (err && err.message), 'error');
            return false;
        }
    }

    async function disconnect() {
        state.root = null;
        state.connected = false;
        await idbDel(IDB_KEY);
        ZBZ.log('FsAccess', 'Repo-Ordner getrennt');
    }

    function isConnected() { return state.connected && !!state.root; }

    // ---- Schreiben ----

    /** Schreibt content nach relPath (relativ zum Repo-Root); legt Verzeichnisse an. */
    async function writeFile(relPath, content) {
        if (!isConnected()) throw new Error('nicht verbunden');
        // Permission ggf. erneut sicherstellen (Geste vorhanden: aktiver Speicher-Klick)
        if (!(await ensurePermission(state.root, true))) throw new Error('Schreibrecht entzogen');
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
        ZBZ.log('FsAccess', 'geschrieben: ' + relPath + ' (' + (content.length / 1024).toFixed(1) + ' KB)');
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
        await writeFile(layoutMirrorPath(doc, page), json);  // Mirror -> Viewer-Reload
        return canonical;
    }

    async function writeText(doc, page, content) {
        const canonical = await writeFile(`output/ocr_curated/${doc}_p${page}.md`, content);
        await writeFile(`docs/data/pages/${doc}/${doc}_p${page}.md`, content);  // Mirror -> Viewer-Reload
        return canonical;
    }

    async function writeTei(doc, xml) {
        const canonical = await writeFile(`output/tei_final/${doc}_final.xml`, xml);
        await writeFile(`docs/data/pages/${doc}/${doc}_final.xml`, xml);  // Mirror (Final; Per-Seite erst nach --reassemble)
        return canonical;
    }

    async function writeManifest(doc, manifestObj) {
        const json = JSON.stringify(manifestObj, null, 2);
        const canonical = await writeFile(`output/tei_final/${doc}_manifest.json`, json);
        await writeFile(`docs/data/manifests/${doc}_manifest.json`, json);  // Mirror -> Viewer + Katalog
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
    ZBZ.log('FsAccess', 'ready' + (available ? '' : ' (nicht unterstuetzt)'));
})();
