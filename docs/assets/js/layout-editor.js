/**
 * layout-editor.js — Layout-Region-Editor
 *
 * Operationen:
 *  - BBox-Drag (Region verschieben)
 *  - BBox-Resize (Eckpunkte ziehen)
 *  - Region-Typ aendern (Dropdown im Toolbar)
 *  - Region hinzufuegen (Drag auf leere Faksimile-Flaeche)
 *  - Region loeschen (selektiert + Delete-Button/Taste)
 *  - Reading-Order aendern (Drag&Drop in Region-Liste rechts)
 *
 * Koordinaten sind Prozent (0-100) relativ zum Bild.
 * Onchange-Callback bekommt das neue `regions[]`-Array.
 *
 * Namespace: ZBZ.LayoutEditor
 */
(function () {
    'use strict';

    const $ = ZBZ.$;
    const $$ = ZBZ.$$;

    // ---- State ----
    const state = {
        overlay: null,        // .facsimile__overlay
        regions: [],          // Live-Liste (Referenz auf layout.regions)
        selectedIdx: null,
        onChange: null,
        mode: 'idle',         // idle | dragging | resizing | creating
        dragData: null
    };

    // ============================================================ Public ============================================================

    /**
     * Editor an einem Overlay-Element anhaengen.
     * @param {HTMLElement} overlay - .facsimile__overlay
     * @param {Object} layout - { regions: [...] }
     * @param {Function} onChange - (regions) => void
     */
    function attach(overlay, layout, onChange) {
        detach();
        if (!overlay || !layout || !layout.regions) return;
        state.overlay = overlay;
        state.regions = layout.regions;
        state.onChange = onChange || (() => {});
        state.selectedIdx = null;
        overlay.classList.add('editing');
        bindOverlayEvents();
        bindToolbar();
        renderRegionList();
        ZBZ.log('LayoutEditor', 'attached, ' + state.regions.length + ' regions');
    }

    function detach() {
        if (state.overlay) {
            state.overlay.classList.remove('editing');
            unbindOverlayEvents(state.overlay);
        }
        state.overlay = null;
        state.regions = [];
        state.selectedIdx = null;
        state.onChange = null;
        state.mode = 'idle';
        state.dragData = null;

        // Region-Liste im Image-Body wieder entfernen
        const list = document.querySelector('.region-list-container');
        if (list) list.remove();
    }

    // ============================================================ Selektion ============================================================

    function selectRegion(idx) {
        state.selectedIdx = idx;
        $$('.region', state.overlay).forEach((el, i) => {
            el.classList.toggle('region--selected', i === idx);
        });
        updateToolbarForSelection();
        highlightInRegionList(idx);
    }

    function updateToolbarForSelection() {
        const sel = document.getElementById('region-type');
        const del = document.getElementById('btn-region-delete');
        const coordIds = ['rc-x', 'rc-y', 'rc-w', 'rc-h'];
        const coordInputs = coordIds.map(id => document.getElementById(id));
        if (state.selectedIdx == null) {
            sel.disabled = true;
            del.disabled = true;
            coordInputs.forEach(inp => { if (inp) { inp.disabled = true; inp.value = ''; } });
            return;
        }
        sel.disabled = false;
        del.disabled = false;
        sel.value = state.regions[state.selectedIdx].zbz_tag || 'zb_paragraph';
        coordInputs.forEach(inp => { if (inp) inp.disabled = false; });
        updateCoordInputs(state.selectedIdx);
    }

    function updateCoordInputs(idx) {
        const r = state.regions[idx];
        if (!r || !r.bbox) return;
        const fmt = (v) => (Math.round(v * 100) / 100).toString();
        const rcx = document.getElementById('rc-x');
        const rcy = document.getElementById('rc-y');
        const rcw = document.getElementById('rc-w');
        const rch = document.getElementById('rc-h');
        // Nur ueberschreiben wenn nicht gerade im Input-Fokus (vermeidet Cursor-Reset waehrend des Tippens)
        if (rcx && document.activeElement !== rcx) rcx.value = fmt(r.bbox.x_pct);
        if (rcy && document.activeElement !== rcy) rcy.value = fmt(r.bbox.y_pct);
        if (rcw && document.activeElement !== rcw) rcw.value = fmt(r.bbox.w_pct);
        if (rch && document.activeElement !== rch) rch.value = fmt(r.bbox.h_pct);
    }

    // ============================================================ Overlay-Events ============================================================

    let _onMouseDown, _onMouseMove, _onMouseUp, _onKeyDown;

    function bindOverlayEvents() {
        _onMouseDown = (e) => {
            if (e.target.classList.contains('region__handle')) {
                startResize(e);
                return;
            }
            const regionEl = e.target.closest('.region');
            if (regionEl) {
                const idx = parseInt(regionEl.getAttribute('data-region-idx'), 10);
                selectRegion(idx);
                if (e.shiftKey || e.altKey) return; // Modifier = nur selektieren
                startDrag(e, idx);
            } else {
                // Klick ins Leere → Selektion aufheben oder neue Region anlegen
                if (state.mode === 'create-pending') {
                    startCreate(e);
                } else {
                    selectRegion(null);
                }
            }
        };
        _onMouseMove = (e) => {
            if (state.mode === 'dragging')  doDrag(e);
            else if (state.mode === 'resizing') doResize(e);
            else if (state.mode === 'creating') doCreate(e);
        };
        _onMouseUp = (e) => {
            if (state.mode === 'dragging' || state.mode === 'resizing' || state.mode === 'creating') {
                state.mode = 'idle';
                state.dragData = null;
                if (state.overlay) state.overlay.classList.remove('creating');
                state.onChange(state.regions);
                renderRegionList();
                redrawOverlay();
            }
        };
        _onKeyDown = (e) => {
            if (e.target.matches('input, textarea, [contenteditable="true"]')) return;
            if ((e.key === 'Delete' || e.key === 'Backspace') && state.selectedIdx != null) {
                e.preventDefault();
                deleteSelected();
            } else if (e.key === 'Escape') {
                if (state.mode === 'create-pending' || state.mode === 'creating') {
                    e.preventDefault();
                    // Falls schon angefangen zu zeichnen: die neu erzeugte Region wieder entfernen
                    if (state.mode === 'creating' && state.dragData) {
                        state.regions.splice(state.dragData.idx, 1);
                        state.selectedIdx = null;
                    }
                    state.mode = 'idle';
                    state.dragData = null;
                    if (state.overlay) state.overlay.classList.remove('creating');
                    redrawOverlay();
                    renderRegionList();
                    updateToolbarForSelection();
                    ZBZ.toast('Region-Erstellung abgebrochen', 'info');
                } else if (state.selectedIdx != null) {
                    selectRegion(null);
                }
            }
        };
        state.overlay.addEventListener('mousedown', _onMouseDown);
        document.addEventListener('mousemove', _onMouseMove);
        document.addEventListener('mouseup', _onMouseUp);
        document.addEventListener('keydown', _onKeyDown);
        redrawOverlay();
    }

    function unbindOverlayEvents(overlay) {
        if (_onMouseDown) overlay.removeEventListener('mousedown', _onMouseDown);
        document.removeEventListener('mousemove', _onMouseMove);
        document.removeEventListener('mouseup', _onMouseUp);
        document.removeEventListener('keydown', _onKeyDown);
    }

    // ============================================================ Drag ============================================================

    function pctOfEvent(e) {
        const rect = state.overlay.getBoundingClientRect();
        return {
            x: ((e.clientX - rect.left) / rect.width) * 100,
            y: ((e.clientY - rect.top) / rect.height) * 100,
            rect: rect
        };
    }

    function startDrag(e, idx) {
        state.mode = 'dragging';
        const p = pctOfEvent(e);
        const r = state.regions[idx];
        state.dragData = {
            idx: idx,
            startX: p.x, startY: p.y,
            origBbox: { x_pct: r.bbox.x_pct, y_pct: r.bbox.y_pct, w_pct: r.bbox.w_pct, h_pct: r.bbox.h_pct }
        };
        e.preventDefault();
    }

    function doDrag(e) {
        if (!state.dragData) return;
        const p = pctOfEvent(e);
        const dx = p.x - state.dragData.startX;
        const dy = p.y - state.dragData.startY;
        const r = state.regions[state.dragData.idx];
        r.bbox.x_pct = clamp(state.dragData.origBbox.x_pct + dx, 0, 100 - r.bbox.w_pct);
        r.bbox.y_pct = clamp(state.dragData.origBbox.y_pct + dy, 0, 100 - r.bbox.h_pct);
        applyRegionStyle(state.dragData.idx);
    }

    // ============================================================ Resize ============================================================

    function startResize(e) {
        const corner = e.target.getAttribute('data-corner');
        const regionEl = e.target.closest('.region');
        const idx = parseInt(regionEl.getAttribute('data-region-idx'), 10);
        state.mode = 'resizing';
        const r = state.regions[idx];
        state.dragData = {
            idx: idx, corner,
            startMouse: pctOfEvent(e),
            origBbox: { x_pct: r.bbox.x_pct, y_pct: r.bbox.y_pct, w_pct: r.bbox.w_pct, h_pct: r.bbox.h_pct }
        };
        e.preventDefault();
        e.stopPropagation();
    }

    function doResize(e) {
        if (!state.dragData) return;
        const p = pctOfEvent(e);
        const dx = p.x - state.dragData.startMouse.x;
        const dy = p.y - state.dragData.startMouse.y;
        const r = state.regions[state.dragData.idx];
        const o = state.dragData.origBbox;

        let x = o.x_pct, y = o.y_pct, w = o.w_pct, h = o.h_pct;
        switch (state.dragData.corner) {
            case 'nw': x = o.x_pct + dx; y = o.y_pct + dy; w = o.w_pct - dx; h = o.h_pct - dy; break;
            case 'ne': y = o.y_pct + dy;                  w = o.w_pct + dx; h = o.h_pct - dy; break;
            case 'sw': x = o.x_pct + dx;                  w = o.w_pct - dx; h = o.h_pct + dy; break;
            case 'se':                                    w = o.w_pct + dx; h = o.h_pct + dy; break;
        }
        // Minimum 1%
        if (w < 1) { w = 1; if (state.dragData.corner === 'nw' || state.dragData.corner === 'sw') x = o.x_pct + o.w_pct - 1; }
        if (h < 1) { h = 1; if (state.dragData.corner === 'nw' || state.dragData.corner === 'ne') y = o.y_pct + o.h_pct - 1; }
        r.bbox.x_pct = clamp(x, 0, 99);
        r.bbox.y_pct = clamp(y, 0, 99);
        r.bbox.w_pct = clamp(w, 1, 100 - r.bbox.x_pct);
        r.bbox.h_pct = clamp(h, 1, 100 - r.bbox.y_pct);
        applyRegionStyle(state.dragData.idx);
    }

    // ============================================================ Create ============================================================

    function startCreate(e) {
        state.mode = 'creating';
        const p = pctOfEvent(e);
        const newRegion = {
            label: 'paragraph',
            zbz_tag: 'zb_paragraph',
            text: '',
            bbox: { x_pct: p.x, y_pct: p.y, w_pct: 0, h_pct: 0 },
            curated: true
        };
        state.regions.push(newRegion);
        const idx = state.regions.length - 1;
        state.selectedIdx = idx;
        state.dragData = { idx, startX: p.x, startY: p.y };
        redrawOverlay();
        e.preventDefault();
    }

    function doCreate(e) {
        if (!state.dragData) return;
        const p = pctOfEvent(e);
        const r = state.regions[state.dragData.idx];
        const x0 = Math.min(state.dragData.startX, p.x);
        const y0 = Math.min(state.dragData.startY, p.y);
        const w  = Math.abs(p.x - state.dragData.startX);
        const h  = Math.abs(p.y - state.dragData.startY);
        r.bbox.x_pct = x0;
        r.bbox.y_pct = y0;
        r.bbox.w_pct = Math.max(w, 1);
        r.bbox.h_pct = Math.max(h, 1);
        applyRegionStyle(state.dragData.idx);
    }

    // ============================================================ Delete ============================================================

    function deleteSelected() {
        if (state.selectedIdx == null) return;
        state.regions.splice(state.selectedIdx, 1);
        state.selectedIdx = null;
        redrawOverlay();
        renderRegionList();
        updateToolbarForSelection();
        state.onChange(state.regions);
    }

    // ============================================================ Toolbar ============================================================

    function bindToolbar() {
        const sel = document.getElementById('region-type');
        const btnAdd = document.getElementById('btn-region-add');
        const btnDel = document.getElementById('btn-region-delete');

        // Type-Wechsel
        sel.onchange = () => {
            if (state.selectedIdx == null) return;
            state.regions[state.selectedIdx].zbz_tag = sel.value;
            state.regions[state.selectedIdx].curated = true;
            redrawOverlay();
            renderRegionList();
            state.onChange(state.regions);
        };

        // Region hinzufuegen (Mode "create-pending")
        btnAdd.onclick = () => {
            state.mode = 'create-pending';
            if (state.overlay) state.overlay.classList.add('creating');
            ZBZ.toast('Auf Faksimile ziehen, um Region zu erzeugen (ESC bricht ab)', 'info');
        };

        // Loeschen
        btnDel.onclick = () => deleteSelected();

        // Coord-Inputs (Live-Edit der selektierten Region)
        ['x', 'y', 'w', 'h'].forEach(key => {
            const inp = document.getElementById('rc-' + key);
            if (!inp) return;
            inp.oninput = () => {
                if (state.selectedIdx == null) return;
                const r = state.regions[state.selectedIdx];
                if (!r || !r.bbox) return;
                const val = parseFloat(inp.value);
                if (isNaN(val)) return;
                const clamped = clamp(val, 0, 100);
                const k = key + '_pct';
                r.bbox[k] = clamped;
                // Konsistenz erzwingen (x + w <= 100, y + h <= 100)
                if (key === 'x' || key === 'w') {
                    r.bbox.w_pct = clamp(r.bbox.w_pct, 0.5, 100 - r.bbox.x_pct);
                }
                if (key === 'y' || key === 'h') {
                    r.bbox.h_pct = clamp(r.bbox.h_pct, 0.5, 100 - r.bbox.y_pct);
                }
                applyRegionStyle(state.selectedIdx);
                renderRegionList();
                state.onChange(state.regions);
            };
        });
    }

    // ============================================================ Render ============================================================

    function redrawOverlay() {
        if (!state.overlay) return;
        state.overlay.innerHTML = '';
        state.regions.forEach((r, idx) => {
            if (!r.bbox) return;
            const cls = 'region ' + ZBZ.regionTypeCls(r.zbz_tag) + (idx === state.selectedIdx ? ' region--selected' : '');
            const el = ZBZ.el('div', {
                cls, attrs: { 'data-region-idx': idx, title: r.text || '' },
                style: {
                    left: r.bbox.x_pct + '%',
                    top: r.bbox.y_pct + '%',
                    width: r.bbox.w_pct + '%',
                    height: r.bbox.h_pct + '%'
                }
            });
            // Label oben links
            el.appendChild(ZBZ.el('span', { cls: 'region__label', text: '#' + (idx + 1) + ' ' + ZBZ.regionTypeLabel(r.zbz_tag) }));
            // Resize-Handles
            ['nw', 'ne', 'sw', 'se'].forEach(c => {
                el.appendChild(ZBZ.el('div', {
                    cls: 'region__handle region__handle--' + c,
                    attrs: { 'data-corner': c }
                }));
            });
            state.overlay.appendChild(el);
        });
    }

    function applyRegionStyle(idx) {
        const el = state.overlay.querySelector('.region[data-region-idx="' + idx + '"]');
        if (!el) return;
        const r = state.regions[idx];
        el.style.left   = r.bbox.x_pct + '%';
        el.style.top    = r.bbox.y_pct + '%';
        el.style.width  = r.bbox.w_pct + '%';
        el.style.height = r.bbox.h_pct + '%';
        if (idx === state.selectedIdx) updateCoordInputs(idx);
    }

    // ============================================================ Region-Liste (Reading-Order) ============================================================

    function renderRegionList() {
        // Liste in den Image-Body unter dem Faksimile haengen
        let container = document.querySelector('.region-list-container');
        if (!container) {
            container = ZBZ.el('div', { cls: 'region-list-container' });
            container.appendChild(ZBZ.el('h3', { cls: 'region-list-container__title', text: 'Reading-Order (Drag zum Verschieben, Klick selektiert)' }));
            const ul = ZBZ.el('ul', { cls: 'region-list' });
            container.appendChild(ul);
            const body = state.overlay && state.overlay.closest('.panel__body');
            if (body) body.appendChild(container);
        }
        const ul = container.querySelector('.region-list');
        ul.innerHTML = '';
        const fmt = (v) => (Math.round(v * 10) / 10).toString();
        state.regions.forEach((r, idx) => {
            const li = ZBZ.el('li', {
                cls: 'region-list__item' + (idx === state.selectedIdx ? ' region-list__item--selected' : ''),
                attrs: { draggable: 'true', 'data-idx': idx }
            });
            li.appendChild(ZBZ.el('span', { cls: 'region-list__index', text: '#' + (idx + 1) }));
            li.appendChild(ZBZ.el('span', { cls: 'region-list__label', text: (r.text || '').slice(0, 60) || '(kein Text)' }));
            li.appendChild(ZBZ.el('span', { cls: 'region-list__type', text: ZBZ.regionTypeLabel(r.zbz_tag) }));
            if (r.bbox) {
                li.appendChild(ZBZ.el('span', {
                    cls: 'region-list__bbox',
                    text: fmt(r.bbox.x_pct) + ' · ' + fmt(r.bbox.y_pct) + ' · ' + fmt(r.bbox.w_pct) + ' × ' + fmt(r.bbox.h_pct)
                }));
            }
            li.addEventListener('click', () => selectRegion(idx));
            li.addEventListener('dragstart', (e) => { li.classList.add('region-list__item--dragging'); e.dataTransfer.setData('text/plain', String(idx)); });
            li.addEventListener('dragend', () => li.classList.remove('region-list__item--dragging'));
            li.addEventListener('dragover', (e) => { e.preventDefault(); li.classList.add('region-list__item--over'); });
            li.addEventListener('dragleave', () => li.classList.remove('region-list__item--over'));
            li.addEventListener('drop', (e) => {
                e.preventDefault();
                li.classList.remove('region-list__item--over');
                const from = parseInt(e.dataTransfer.getData('text/plain'), 10);
                const to = idx;
                if (from === to || isNaN(from)) return;
                const [moved] = state.regions.splice(from, 1);
                state.regions.splice(to, 0, moved);
                state.selectedIdx = to;
                redrawOverlay();
                renderRegionList();
                state.onChange(state.regions);
            });
            ul.appendChild(li);
        });
    }

    function highlightInRegionList(idx) {
        $$('.region-list__item').forEach((li, i) => {
            li.classList.toggle('region-list__item--selected', i === idx);
        });
    }

    // ============================================================ Utility ============================================================

    function clamp(v, min, max) { return Math.max(min, Math.min(max, v)); }

    ZBZ.LayoutEditor = { attach, detach };
    ZBZ.log('LayoutEditor', 'ready');
})();
