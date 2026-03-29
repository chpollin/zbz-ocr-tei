/**
 * ZBZ Edition Editor — Save, Dirty State, Toast
 * Depends on: editor-api.js (ZBZ.EditionEditor._api, .state)
 */
(function () {
    'use strict';

    const E = ZBZ.Edition;
    const state = ZBZ.EditionEditor.state;
    const api = ZBZ.EditionEditor._api;

    function markDirty() {
        if (state.dirty) return;
        state.dirty = true;
        const btn = E.$('#save-btn');
        if (btn) {
            btn.disabled = false;
            btn.classList.add('ed-dirty');
        }
        const status = E.$('#save-status');
        if (status) status.textContent = 'Ungespeicherte Aenderungen';
    }

    function clearDirty() {
        state.dirty = false;
        const btn = E.$('#save-btn');
        if (btn) {
            btn.disabled = true;
            btn.classList.remove('ed-dirty');
        }
        const status = E.$('#save-status');
        if (status) status.textContent = '';
    }

    function showToast(message, type) {
        const existing = E.$('.ed-toast');
        if (existing) existing.remove();

        const toast = document.createElement('div');
        toast.className = `ed-toast ed-toast-${type || 'info'}`;
        toast.textContent = message;
        document.body.appendChild(toast);

        toast.offsetHeight;
        toast.classList.add('ed-toast-visible');

        setTimeout(() => {
            toast.classList.remove('ed-toast-visible');
            setTimeout(() => { toast.remove(); }, 300);
        }, 3000);
    }

    function savePageXml(docId, page, container, xmlMode) {
        const serialize = ZBZ.EditionEditor._serialize;
        let xml;
        if (xmlMode) {
            xml = serialize.getXmlFromEditor(container);
        } else {
            xml = serialize.serializeToXml(container);
        }

        if (!xml) {
            showToast('Kein XML zum Speichern', 'error');
            return Promise.resolve(null);
        }

        return api.apiPut(`/tei/${docId}/page/${page}`, { xml: xml })
            .then((result) => {
                clearDirty();
                showToast(`Seite ${page} gespeichert`, 'success');
                return result;
            })
            .catch((err) => {
                const msg = err.detail ? (typeof err.detail === 'string' ? err.detail : err.detail.message || 'Fehler') : 'Speichern fehlgeschlagen';
                showToast(msg, 'error');
                return null;
            });
    }

    ZBZ.EditionEditor._save = { markDirty, clearDirty, showToast, savePageXml };
})();
