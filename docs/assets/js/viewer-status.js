/**
 * viewer-status.js - Workflow status per stream (E66) and the editor identity chip
 *
 * Reads the per-object manifest of the current document, renders one status pill per
 * stream, and records every status change with initials and timestamp in the manifest
 * history. The save path in viewer-persist.js writes it back.
 *
 * Namespace: ZBZ.Viewer
 */
(function () {
    'use strict';

    const V = ZBZ.Viewer;
    const state = V.state;
    const refs  = V.refs;
    const { STATUS_CYCLE, STATUS_LABEL, STATUS_LEGACY, STREAM_LABEL,
            STREAMS, ENTITY_STREAM, manifestStreams } = V;

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
        ZBZ.bus.emit('dirty:changed');
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

    Object.assign(ZBZ.Viewer, {
        loadManifest,
        renderStatusPills,
        setStreamStatus,
        cycleStatus,
        autoStartArbeit,
        getAuthor,
        currentAuthor,
        renderIdentity,
        startIdentityEdit,
        commitIdentityEdit,
        cancelIdentityEdit,
    });

    // A new document brings its own manifest; the load is not awaited by the caller.
    ZBZ.bus.on('doc:changed', (docId) => loadManifest(docId));
})();
