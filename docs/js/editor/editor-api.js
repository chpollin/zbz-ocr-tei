/**
 * ZBZ Edition Editor — API & State
 * Creates ZBZ.EditionEditor namespace, shared state, server detection, API helpers.
 * Must load FIRST (before other editor modules).
 */
(function () {
    'use strict';

    const E = ZBZ.Edition;
    const API_BASE = window.location.origin + '/api';

    const editorState = {
        active: false,
        dirty: false,
        serverAvailable: false,
        currentXml: null
    };

    function checkServer(callback) {
        const host = window.location.hostname;
        if (host !== 'localhost' && host !== '127.0.0.1') {
            editorState.serverAvailable = false;
            if (callback) callback(false);
            return;
        }
        fetch(API_BASE + '/health', { method: 'GET' })
            .then((r) => {
                editorState.serverAvailable = r.ok;
                if (ZBZ.log) ZBZ.log('Editor', r.ok ? `Server erreichbar (${API_BASE})` : 'Kein Curation Server auf diesem Port');
                if (callback) callback(r.ok);
            })
            .catch(() => {
                editorState.serverAvailable = false;
                if (ZBZ.log) ZBZ.log('Editor', 'Kein Curation Server (read-only Modus)');
                if (callback) callback(false);
            });
    }

    function apiGet(path) {
        return fetch(API_BASE + path).then((r) => {
            if (!r.ok) throw new Error(`API Error: ${r.status}`);
            return r.json();
        });
    }

    function apiPut(path, body) {
        return fetch(API_BASE + path, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body)
        }).then((r) => {
            if (!r.ok) return r.json().then((err) => { throw err; });
            return r.json();
        });
    }

    function fetchTeiFromServer(docId, page) {
        if (!editorState.serverAvailable) return Promise.resolve(null);
        return apiGet(`/tei/${docId}/page/${page}`)
            .then((data) => data)
            .catch(() => null);
    }

    // Create namespace — other modules extend this
    ZBZ.EditionEditor = {
        state: editorState,
        _api: { checkServer, apiGet, apiPut, fetchTeiFromServer, API_BASE }
    };
})();
