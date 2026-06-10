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
        _isBlank: false,      // Leerseite (Vorsatz/Rueckseite/Durchschlag) — kein echter Text
        manifest: null,       // E66: Pro-Objekt-Manifest mit streams.{ocr,layout,tei}.{status,history}
        manifestDirty: false, // ungespeicherte Status-Aenderungen
        dirtyStreams: new Set(), // welche Stroeme seit dem letzten Speichern geaendert wurden
        layoutDirty: false,   // ungespeicherte Layout-Aenderung (aktuelle Seite)
        textDirty: false      // ungespeicherte Text-Aenderung (aktuelle Seite)
    };

    // E77: Workflow-Status pro Strom, drei Stufen -- unverifiziert -> in_arbeit -> verifiziert -> unverifiziert
    // `unverifiziert` heisst: Pipeline-Output existiert, kein Mensch hat verifiziert (neutral/grau).
    // `in_arbeit` = in Bearbeitung (gelb). `verifiziert` = menschlich freigegeben (gruen).
    // Rot bleibt reserviert fuer einen spaeteren expliziten Problem-Status.
    const STATUS_CYCLE = ['unverifiziert', 'in_arbeit', 'verifiziert'];
    const STATUS_LABEL = {
        unverifiziert: 'unverifiziert',
        in_arbeit:     'in Arbeit',
        verifiziert:   'verifiziert'
    };
    // Legacy-Mapping fuer aeltere Manifeste/Mirror (offen, bearbeitet, fertig)
    const STATUS_LEGACY = { offen: 'unverifiziert', bearbeitet: 'in_arbeit', fertig: 'verifiziert' };
    const STREAM_LABEL = { ocr: 'OCR', layout: 'Layout', tei: 'TEI-XML' };

    const OSD_PREFIX = 'https://cdn.jsdelivr.net/npm/openseadragon@5.0.1/build/openseadragon/images/';

    const cache = new ZBZ.Cache(40);

    // ---- DOM-Refs ----
    const refs = {
        subbar:         $('#doc-subbar'),
        docMeta:        $('#doc-meta'),
        pageInfo:       $('#page-info'),
        btnPrev:        $('#btn-prev'),
        btnNext:        $('#btn-next'),
        pageGoto:       $('#page-goto'),
        btnImageEdit:   $('#btn-image-edit'),
        btnTextEdit:    $('#btn-text-edit'),
        textSourceBtns: $$('.mode-btn[data-text-source]'),
        imageBody:      $('#image-body'),
        textBody:       $('#text-body'),
        textTitle:      $('#text-panel-title'),
        regionCount:    $('#region-count'),
        layoutToolbar:  $('#layout-toolbar'),
        // Speichern + Export-Dropdown + Identitaets-Chip
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
        // E66: Workflow-Status-Controls
        statusOcr:      $('#status-ocr'),
        statusLayout:   $('#status-layout'),
        statusTei:      $('#status-tei'),
        statusHint:     $('#status-hint')
    };

    // ============================================================ Init ============================================================

    async function init() {
        bindEvents();

        renderIdentity();
        // Persistierten Repo-Ordner wiederherstellen (File System Access)
        if (ZBZ.FsAccess) { await ZBZ.FsAccess.init(); }

        const urlDoc = ZBZ.getParam('doc');
        if (!urlDoc) {
            renderNoDoc();
            return;
        }

        const data = await ZBZ.fetchJSON('data/catalog.json');
        if (!data) {
            renderError('catalog.json nicht gefunden. <code>python -m scripts.edition.generate_edition_data</code>');
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
        state.manifest = null;
        state.manifestDirty = false;
        ZBZ.setParams({ doc: doc.id, page: state.page });
        document.title = (doc.title ? doc.title.slice(0, 60) + ' — ' : '') + 'Hersch Pipeline-Viewer';

        // Sub-Bar zeigen + befuellen
        refs.subbar.hidden = false;
        renderDocMeta(doc);

        // Buttons enablen
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

        // E66: Manifest fuer Workflow-Status laden (parallel zu Seitenrendering)
        loadManifest(doc.id);

        await loadPage();
    }

    // ============================================================ Workflow-Status (E66) ============================================================

    async function loadManifest(docId) {
        const m = await ZBZ.fetchJSON('data/manifests/' + encodeURIComponent(docId) + '_manifest.json');
        if (m && m.streams) {
            // Legacy-Status-Werte migrieren (v2 -> v3)
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
            // Fallback: synthetisches Manifest, falls Mirror nicht aktuell (defensiv)
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

    // Kuerzel aus dem Identitaets-Chip (localStorage). KEIN blockierendes prompt().
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
            // Klassen aktualisieren (alte Status-Klassen wegnehmen)
            btn.className = 'status-pill status-pill--' + status + (state.dirtyStreams.has(stream) ? ' status-pill--dirty' : '');
            const sm = (state.manifest && state.manifest.streams && state.manifest.streams[stream]) || {};
            const history = sm.history || [];
            const last = history.length ? history[history.length - 1] : null;
            const baseLine = (status === 'unverifiziert')
                ? STREAM_LABEL[stream] + ': Pipeline-Output existiert, noch nicht menschlich verifiziert'
                : STREAM_LABEL[stream] + ': ' + STATUS_LABEL[status];
            btn.title = baseLine
                + (last ? '\nzuletzt: ' + last.to + ' · ' + (last.by || '?') + ' · ' + (last.at || '').slice(0, 16) : '')
                + '\nKlick wechselt: unverifiziert -> in Arbeit -> verifiziert';
            // announce the current status, not just "set status" (a11y)
            btn.setAttribute('aria-label', STREAM_LABEL[stream] + '-Status: ' + STATUS_LABEL[status] + ' (Klick wechselt)');
            btn.innerHTML =
                '<span class="status-pill__stream">' + STREAM_LABEL[stream] + '</span>'
                + '<span class="status-pill__dot"></span>'
                + '<span class="status-pill__label">' + STATUS_LABEL[status] + '</span>';
        });
        refs.btnDlManifest.disabled = !state.manifest;
        refs.statusHint.textContent = state.manifestDirty
            ? 'ungespeicherter Status · Speichern'
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
        s.history.push({
            at: new Date().toISOString(),
            by: (opts && opts.by) || getAuthor(),
            from: from,
            to: newStatus,
            note: (opts && opts.note) || null
        });
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
        // Beim ersten Touch eines Edit-Toggles: unverifiziert -> in_arbeit
        if (!state.manifest) return;
        if (streamStatus(stream) === 'unverifiziert') {
            setStreamStatus(stream, 'in_arbeit', { note: 'auto: Edit-Toggle aktiviert' });
        }
    }

    // ============================================================ Identitaets-Chip (Kuerzel) ============================================================

    let identityCancelling = false; // ESC bricht ab, ohne dass das Blur-Commit speichert

    function currentAuthor() {
        return (window.localStorage && localStorage.getItem('zbz.workflow.by')) || '';
    }
    function renderIdentity() {
        if (!refs.identityWho) return;
        const v = currentAuthor();
        refs.identityWho.textContent = v || 'Kuerzel';
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
        refs.identityInput.hidden = true;
        refs.btnIdentity.hidden = false;
        renderIdentity();
    }
    function cancelIdentityEdit() {
        identityCancelling = true;
        refs.identityInput.hidden = true;
        refs.btnIdentity.hidden = false;
    }

    // ============================================================ Speichern (alle Stroeme direkt ins Repo) ============================================================

    // Schreibt direkt in den verbundenen Repo-Ordner; faellt pro Datei auf Download
    // zurueck, wenn nicht verbunden oder der Schreibzugriff scheitert. Ohne eigenen Toast
    // (saveAll meldet gesammelt).
    async function persistSilent(fsWrite, dlFallback) {
        // Auf Chromium (File System Access verfuegbar) wird ausschliesslich direkt ins Repo
        // geschrieben; saveAll hat die Verbindung vorher sichergestellt. Ein Schreibfehler
        // propagiert nach saveAll und wird dort sichtbar gemeldet -- KEIN stiller Download,
        // der sonst verwirrende Dateien im Downloads-Ordner ablegt. Der Download bleibt nur
        // der Weg, wenn die API gar nicht verfuegbar ist (Nicht-Chromium-Browser).
        if (ZBZ.FsAccess && ZBZ.FsAccess.available) {
            await fsWrite();
            return true;
        }
        dlFallback();
        return false;
    }

    function renderSaveState() {
        // Was ist ungespeichert? (zugleich Grundlage fuer den zustandsabhaengigen Tooltip)
        const parts = [];
        if (state.layoutDirty) parts.push('Layout S.' + state.page);
        if (state.textDirty)   parts.push((state.textSource === 'xml' || state.textSource === 'tei') ? 'TEI' : 'Text S.' + state.page);
        if (state.manifestDirty) parts.push('Status');
        const dirty = parts.length > 0;
        if (!refs.btnSave) return;
        refs.btnSave.disabled = !state.doc || !dirty;
        refs.btnSave.classList.toggle('btn--dirty', dirty);
        if (!dirty) {
            refs.btnSave.title = 'Nichts zu speichern. Bearbeite Layout, Text oder Workflow-Status, dann wird gespeichert.';
        } else {
            const target = (ZBZ.FsAccess && ZBZ.FsAccess.available)
                ? (ZBZ.FsAccess.isConnected() ? 'direkt ins Repo' : 'ins Repo (fragt einmal nach dem Ordner)')
                : 'als Download';
            refs.btnSave.title = 'Speichert ' + target + ': ' + parts.join(', ');
        }
    }

    // Vor einem Seitenwechsel pruefen: Layout/Text-Edits sind per-Seite und gingen beim
    // Wechsel verloren. Manifest-Dirty ist per-Dokument und ueberlebt die Navigation,
    // blockiert sie also nicht. Gibt true zurueck, wenn der Wechsel erfolgen darf.
    function confirmLeavePage() {
        if (!state.layoutDirty && !state.textDirty) return true;
        return window.confirm('Ungespeicherte Aenderungen auf dieser Seite gehen verloren. Trotzdem wechseln?');
    }

    // "Speichern" = alle ungespeicherten Stroeme als ein Akt: Layout (Seite), Text (Seite,
    // OCR oder TEI je nach Quelle) und das Manifest (Workflow-Status + Provenienz). Jeder
    // Strom landet an seiner richtigen Stelle im Repo. Kein Download (ausser Fallback).
    async function saveAll() {
        if (!state.doc) return;
        const dl = state.layoutDirty && state.layout && Array.isArray(state.layout.regions);
        const dt = state.textDirty;
        const dm = state.manifestDirty;
        if (!dl && !dt && !dm) { ZBZ.toast('Nichts zu speichern', 'warn'); return; }

        // Direkt-Speichern: Auf Chromium MUSS ein Repo-Ordner verbunden sein. Ist er es nicht,
        // einmal verbinden (mit Erst-Info). Klappt das nicht (Nutzer bricht ab oder erteilt kein
        // Schreibrecht), brechen wir mit klarer Meldung ab, statt die Datei still in den
        // Downloads-Ordner zu legen. Die Stroeme bleiben ungespeichert, nichts geht verloren;
        // ein erneuter Klick (oder Export -> Download) ist moeglich.
        if (ZBZ.FsAccess && ZBZ.FsAccess.available && !ZBZ.FsAccess.isConnected()) {
            await connectWithInfo();
            if (!ZBZ.FsAccess.isConnected()) {
                ZBZ.toast('Nicht gespeichert: Repo-Ordner nicht verbunden oder kein Schreibrecht erteilt. Ordner "zbz-ocr-tei" verbinden und erneut Speichern (oder ueber Export herunterladen).', 'warn');
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
                if (refs.regionCount) refs.regionCount.textContent = state.layout.regions.length + ' Regionen';
                saved.push('Layout S.' + state.page);
            }
            if (dt) {
                const content = (state._currentEditedText != null) ? state._currentEditedText : state._currentText;
                if (content == null) {
                    state.textDirty = false;
                } else {
                    const isTei = (state.textSource === 'xml' || state.textSource === 'tei');
                    if (isTei) {
                        // writeTei replaces the whole SoT file -- only accept a complete TEI document
                        if (content.indexOf('<teiHeader') === -1 || content.indexOf('</TEI>') === -1) {
                            ZBZ.toast('TEI nicht gespeichert: Inhalt ist kein vollstaendiges TEI-Dokument (teiHeader/TEI-Wurzel fehlt). Edit bleibt ungespeichert erhalten.', 'err');
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
                        saved.push('Text S.' + state.page);
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
            ZBZ.toast('Speichern fehlgeschlagen: ' + (err && err.message), 'err');
        }

        renderStatusPills();
        renderSaveState();
        if (saved.length) {
            // a download is not a repo write -- be explicit about it (H2)
            if (downloaded) {
                ZBZ.toast('Download erzeugt (Dateien manuell ins Repo legen): ' + saved.join(', '), 'warn');
            } else {
                ZBZ.toast('Gespeichert (Repo): ' + saved.join(', '), 'ok');
            }
        }
    }

    // ============================================================ Export-Dropdown (Einzel-Download) ============================================================

    function exportLayout() {
        if (!state.doc || !state.layout) { ZBZ.toast('Keine Layout-Daten', 'warn'); return; }
        ZBZ.Download.layout(state.doc.id, state.page, state.layout.regions, layoutSourceMeta());
        closeExportMenu();
    }
    function exportText() {
        if (!state.doc) return;
        const content = (state._currentEditedText != null) ? state._currentEditedText : state._currentText;
        if (!content) { ZBZ.toast('Kein Text geladen', 'warn'); return; }
        ZBZ.Download.text(state.doc.id, state.page, content);
        closeExportMenu();
    }
    async function exportTei() {
        if (!state.doc) return;
        let xml = state._currentEditedText;
        if (!xml || state.textSource !== 'xml') xml = await loadTeiFinal(state.doc.id);
        if (!xml) { ZBZ.toast('Kein TEI verfuegbar', 'warn'); return; }
        ZBZ.Download.tei(state.doc.id, xml, 'curated');
        closeExportMenu();
    }
    function exportManifest() {
        if (!state.manifest) { ZBZ.toast('Kein Manifest geladen', 'warn'); return; }
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

    // ============================================================ Repo-Ordner (File System Access) ============================================================

    // Einmalige Info beim ersten Verbinden: erklaert WELCHEN Ordner waehlen + WAS passiert,
    // bevor der native Ordner-Dialog aufgeht. Danach gemerkt (localStorage).
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
    // modal a11y: focus restore target + document-level key handler (ESC, Tab trap)
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

    // ============================================================ Page laden ============================================================

    // Only the newest page load may render (rapid paging overlaps async fetches)
    let pageLoadSeq = 0;

    async function loadPage() {
        if (!state.doc) return;
        const seq = ++pageLoadSeq;
        const doc = state.doc, page = state.page;
        // Seitenwechsel: Layout/Text sind per-Seite -> Dirty-Zustand der alten Seite
        // verfaellt (Manifest-Dirty bleibt, da per-Dokument).
        state.layoutDirty = false;
        state.textDirty = false;
        state._currentEditedText = null;
        renderSaveState();
        refs.pageInfo.textContent = page + ' / ' + (doc.page_count || '?');
        refs.btnPrev.disabled = page <= 1;
        refs.btnNext.disabled = page >= (doc.page_count || 1);
        ZBZ.setParams({ page });

        // Leerseite vorab bestimmen (aus Mistral-Basis-OCR), damit Faksimile UND Text
        // konsistent reagieren: keine Phantom-Regionen, kein OCR-Muell.
        state._isBlank = await detectBlankPage(doc.id, page);
        if (seq !== pageLoadSeq) return;

        await renderFacsimile();
        if (seq !== pageLoadSeq) return;
        await renderTextPanel();
    }

    async function detectBlankPage(doc, page) {
        // E63 Schritt 3: primaer den <pb type="blank"/>-Marker aus der per-Seiten-TEI
        // lesen (deterministisch, vom Korpus-Skript projiziert). Fallback auf die
        // OCR-Heuristik (isBlankPageText), falls die per-Seiten-TEI fehlt.
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

        // Lade-Hinweis: OSD laedt das komplette (oft mehrere MB grosse) PNG ungetilet und
        // dekodiert es vor der ersten Darstellung -> ohne Hinweis bliebe das Panel sekundenlang
        // leer. Wird bei 'open' (Erfolg) bzw. 'open-failed' (Fehler ersetzt innerHTML) entfernt.
        const loading = ZBZ.el('div', { cls: 'facsimile-loading', text: 'Lade Faksimile…' });
        refs.imageBody.appendChild(loading);

        // Layout vorab laden, Overlays werden nach OSD-'open' angehaengt
        const layout = await fetchLayout(doc.id, page);
        if (state.doc !== doc || state.page !== page || state.imageEdit) return; // race guard
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
        if (state.doc !== doc || state.page !== page || !state.imageEdit) return;
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
        refs.regionCount.textContent = regions.length + ' Regionen (geaendert)';
        state.layoutDirty = true;
        renderSaveState();
        // E66: erste echte Layout-Aenderung -> Strom auf in_arbeit
        autoStartArbeit('layout');
    }

    // ============================================================ Text-Panel ============================================================

    function textPanelTitle() {
        if (state.textSource === 'tei') return 'TEI · gerendert';
        if (state.textSource === 'xml') return 'TEI · XML (Gesamtdokument)';
        return 'OCR · ' + state.ocrSource;
    }

    async function renderTextPanel() {
        const doc = state.doc, page = state.page;
        const src = state.textSource;
        // True once doc/page/source changed mid-fetch -- a stale response must not render.
        const stale = () => (state.doc !== doc || state.page !== page || state.textSource !== src);

        // Leerseite: ruhiger Hinweis statt OCR-Muell ('.', '^{}[]', leere Tabelle).
        // Im Text-Edit-Modus normal rendern, damit der Rohtext bei Bedarf bereinigt
        // werden kann. XML mode is exempt (shows the whole document).
        if (state._isBlank && !state.textEdit && state.textSource !== 'xml') {
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
            if (stale()) return;
            if (!res) {
                renderLoadError('Keine OCR-Daten fuer ' + state.ocrSource + ' / Seite ' + page);
                state._currentText = null;
                return;
            }
            state._currentText = res.text;
            renderOcrText(res.text);
        }
        else if (state.textSource === 'tei') {
            refs.textTitle.textContent = 'TEI · gerendert';
            const xml = await loadTeiPage(doc.id, page);
            if (stale()) return;
            if (!xml) {
                renderLoadError('Kein TEI fuer Seite ' + page);
                return;
            }
            state.teiXml = xml;
            ZBZ.TeiRender.render(xml, refs.textBody);
            ensureTextEditableState();
        }
        else if (state.textSource === 'xml') {
            // Must load the FULL final TEI: saving overwrites {doc}_final.xml as a
            // whole (E72). Loading a single page here would destroy the rest on save.
            refs.textTitle.textContent = 'TEI · XML (Gesamtdokument)';
            const xml = await loadTeiFinal(doc.id);
            if (stale()) return;
            if (!xml) {
                renderLoadError('Kein finales TEI fuer Dokument ' + doc.id);
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
            ? 'Netzwerkfehler — Verbindung pruefen.'
            : 'Datei nicht vorhanden (404).';
        refs.textBody.innerHTML = '';
        const box = ZBZ.el('div', { cls: 'empty' });
        box.appendChild(ZBZ.el('div', { text: what + '. ' + cause }));
        box.appendChild(ZBZ.el('button', {
            cls: 'btn btn--sm empty__retry',
            text: 'Erneut versuchen',
            on: { click: () => renderTextPanel() }
        }));
        refs.textBody.appendChild(box);
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
        // E66: Screening-Badge wurde durch Workflow-Status-Pills (zweite Subbar-Zeile) abgeloest.
    }

    function ensureTextEditableState() {
        if (state.textEdit && ZBZ.TranscriptionEditor) {
            ZBZ.TranscriptionEditor.attach(refs.textBody, state.textSource, (newContent) => {
                state._currentEditedText = newContent;
                state.textDirty = true;
                renderSaveState();
                // E66: erste echte Text-Aenderung -> zugehoerigen Strom auf in_arbeit
                autoStartArbeit(state.textSource === 'ocr' ? 'ocr' : 'tei');
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
            // Hinweis: Der Status-Uebergang offen -> in_arbeit erfolgt erst bei der ERSTEN
            // echten Region-Aenderung (onLayoutChanged), nicht schon beim Oeffnen des Editors.
        }
    }

    function setTextEdit(on) {
        const prev = state.textEdit;
        state.textEdit = !!on;
        refs.btnTextEdit.setAttribute('aria-pressed', state.textEdit ? 'true' : 'false');

        if (prev === state.textEdit) return;

        // Editor immer detachen bevor Mode-Wechsel; ensureTextEditableState() re-attached wenn noetig
        if (ZBZ.TranscriptionEditor) ZBZ.TranscriptionEditor.detach(refs.textBody);

        // TEI-Bearbeitung nur im XML-Modus: die gerenderte TEI laesst sich nicht zurueck-
        // serialisieren (transcription-editor liest nur innerText) und Speichern/Export nehmen
        // TEI-Edits ausschliesslich aus dem XML-Modus mit. Wuerde man hier auf der gerenderten
        // TEI editieren, gingen die Aenderungen beim Speichern verloren. Daher beim
        // Aktivieren von Text-Edit auf gerenderter TEI auf die XML-Quelle umschalten.
        if (state.textEdit && state.textSource === 'tei') {
            ZBZ.toast('TEI-Bearbeitung im XML-Modus (gerendert ist Lese-Ansicht)', 'info');
            setTextSource('xml');   // rendert XML + ensureTextEditableState() attached den Editor
            return;
        }

        // OCR-Panel rendering wechselt: gerenderter Markdown <-> Rohtext.
        // renderTextPanel() deckt Leerseite (Hinweis) und Edit/Lese-Modus konsistent ab.
        if (state.textSource === 'ocr') {
            renderTextPanel();
        } else {
            ensureTextEditableState();
        }
        // Hinweis: Der Status-Uebergang offen -> in_arbeit erfolgt erst bei der ERSTEN
        // echten Text-Aenderung (onChange in ensureTextEditableState), nicht beim Oeffnen.
    }

    function setTextSource(src) {
        state.textSource = src;
        refs.textSourceBtns.forEach(b => b.setAttribute('aria-pressed', b.getAttribute('data-text-source') === src ? 'true' : 'false'));
        renderTextPanel();
    }

    // ============================================================ Speichern (Direkt-Schreiben oder Download) ============================================================

    // Wenn ein Repo-Ordner verbunden ist (File System Access API), direkt in den Working
    // Tree schreiben; sonst (oder bei Schreibfehler) auf ZBZ.Download zurueckfallen.
    function layoutSourceMeta() {
        return {
            source: 'curated',
            original_source: state.layout.source || 'gemini',
            // Bildgroesse mitschreiben, damit die kuratierte JSON selbsttragend ist
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
            if (e.target.matches('input, textarea, select, [contenteditable="true"]')) return;
            if (e.key === 'ArrowLeft')       refs.btnPrev.click();
            else if (e.key === 'ArrowRight') refs.btnNext.click();
            else if (e.key === 'Home')       { e.preventDefault(); gotoPage(1); }
            else if (e.key === 'End')        { e.preventDefault(); gotoPage(state.doc ? (state.doc.page_count || 1) : 1); }
        });

        refs.btnImageEdit.addEventListener('click', () => setImageEdit(!state.imageEdit));
        refs.btnTextEdit.addEventListener('click', () => setTextEdit(!state.textEdit));
        refs.textSourceBtns.forEach(b => b.addEventListener('click', () => setTextSource(b.getAttribute('data-text-source'))));

        // Speichern (alle Stroeme direkt ins Repo) + Export-Dropdown (Einzel-Download)
        if (refs.btnSave) refs.btnSave.addEventListener('click', saveAll);
        if (refs.btnExportMenu) refs.btnExportMenu.addEventListener('click', (e) => { e.stopPropagation(); toggleExportMenu(); });
        refs.btnDlLayout.addEventListener('click', exportLayout);
        refs.btnDlText.addEventListener('click', exportText);
        refs.btnDlTei.addEventListener('click', exportTei);
        refs.btnDlManifest.addEventListener('click', exportManifest);

        // Identitaets-Chip (Kuerzel): Klick -> Inline-Feld; Enter/Blur speichert, ESC bricht ab.
        if (refs.btnIdentity) refs.btnIdentity.addEventListener('click', startIdentityEdit);
        if (refs.identityInput) {
            refs.identityInput.addEventListener('blur', commitIdentityEdit);
            refs.identityInput.addEventListener('keydown', (e) => {
                if (e.key === 'Enter') { e.preventDefault(); refs.identityInput.blur(); }
                else if (e.key === 'Escape') { e.preventDefault(); cancelIdentityEdit(); }
            });
        }

        // E66: Status-Pills klick = naechster Status (Cycle)
        refs.statusOcr.addEventListener('click', () => cycleStatus('ocr'));
        refs.statusLayout.addEventListener('click', () => cycleStatus('layout'));
        refs.statusTei.addEventListener('click', () => cycleStatus('tei'));

        // Warnen vor Verlassen mit ungespeicherten Status-Aenderungen
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
