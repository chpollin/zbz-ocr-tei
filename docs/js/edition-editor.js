/**
 * ZBZ Edition – Editor Module (Orchestrator)
 * Loads sub-modules and exposes unified public API.
 *
 * Requires (in order):
 *   editor/editor-api.js        — state, server detection, API helpers
 *   editor/editor-save.js       — markDirty, clearDirty, showToast, savePageXml
 *   editor/editor-serialize.js  — serializeToXml, renderXmlEditable, getXmlFromEditor
 *   editor/editor-block-toolbar.js — block editing (type, split, merge, delete, B/I/U)
 *   editor/editor-entity.js     — entity tagging, popover, autocomplete
 *   editor/editor-render.js     — renderEditable (XML -> editable DOM)
 *
 * Namespace: ZBZ.EditionEditor (ES6+, IIFE)
 */
(function () {
    'use strict';

    const api = ZBZ.EditionEditor._api;
    const save = ZBZ.EditionEditor._save;
    const serialize = ZBZ.EditionEditor._serialize;
    const blocks = ZBZ.EditionEditor._blocks;
    const entities = ZBZ.EditionEditor._entities;
    const render = ZBZ.EditionEditor._render;

    // Expose backward-compatible public API
    Object.assign(ZBZ.EditionEditor, {
        checkServer: api.checkServer,
        fetchTeiFromServer: api.fetchTeiFromServer,
        renderEditable: render.renderEditable,
        renderXmlEditable: serialize.renderXmlEditable,
        serializeToXml: serialize.serializeToXml,
        savePageXml: save.savePageXml,
        toggleInlineFormat: blocks.toggleInlineFormat,
        markDirty: save.markDirty,
        clearDirty: save.clearDirty,
        showToast: save.showToast,
        initBlockToolbar: blocks.initBlockToolbarListeners,
        initEntityHandlers: entities.initEntityHandlers
    });
})();
