/**
 * ZBZ Edition Editor — Entity Tagging, Popover, Autocomplete
 * Depends on: editor-api.js (state, _api), editor-save.js (markDirty, showToast)
 */
(function () {
    'use strict';

    const E = ZBZ.Edition;
    const state = ZBZ.EditionEditor.state;
    const api = ZBZ.EditionEditor._api;
    const save = ZBZ.EditionEditor._save;

    function _entityTypeToTag(type) {
        const map = { person: 'persName', org: 'orgName', place: 'placeName', work: 'bibl' };
        return map[type] || type;
    }

    function _entityTypeLabel(type) {
        const map = { person: 'Person', org: 'Organisation', place: 'Ort', work: 'Werk' };
        return map[type] || type;
    }

    let entityToolbar = null;

    function _createEntityToolbar() {
        if (entityToolbar) return entityToolbar;

        const tb = document.createElement('div');
        tb.className = 'ed-entity-toolbar';
        tb.innerHTML =
            '<button class="ed-entity-tag-btn ed-entity-tag-person" data-type="person" title="Person">Person</button>' +
            '<button class="ed-entity-tag-btn ed-entity-tag-org" data-type="org" title="Organisation">Org</button>' +
            '<button class="ed-entity-tag-btn ed-entity-tag-place" data-type="place" title="Ort">Ort</button>' +
            '<button class="ed-entity-tag-btn ed-entity-tag-work" data-type="work" title="Werk">Werk</button>' +
            '<button class="ed-entity-tag-btn ed-entity-tag-remove" data-type="remove" title="Entity entfernen">X</button>';

        const tagBtns = Array.prototype.slice.call(tb.querySelectorAll('.ed-entity-tag-btn'));
        tagBtns.forEach((btn) => {
            btn.addEventListener('mousedown', (e) => {
                e.preventDefault();
            });
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                const type = btn.getAttribute('data-type');
                if (type === 'remove') {
                    _removeEntityAtSelection();
                } else {
                    _tagSelectionAsEntity(type);
                }
                _hideEntityToolbar();
            });
        });

        document.body.appendChild(tb);
        entityToolbar = tb;
        return tb;
    }

    function _showEntityToolbar(x, y) {
        const tb = _createEntityToolbar();
        tb.style.top = (y - tb.offsetHeight - 8) + 'px';
        tb.style.left = x + 'px';
        tb.classList.add('ed-entity-toolbar-visible');
    }

    function _hideEntityToolbar() {
        if (entityToolbar) {
            entityToolbar.classList.remove('ed-entity-toolbar-visible');
        }
    }

    function _tagSelectionAsEntity(type) {
        const sel = window.getSelection();
        if (!sel || sel.isCollapsed || sel.rangeCount === 0) return;

        const range = sel.getRangeAt(0);
        const text = range.toString().trim();
        if (!text) return;

        const container = E.$('.ed-text-content');
        if (!container || !container.contains(range.commonAncestorContainer)) return;

        const parentEntity = range.startContainer.parentElement;
        if (parentEntity && parentEntity.classList &&
            parentEntity.classList.contains('ed-tei-entity')) {
            _changeEntityType(parentEntity, type);
            return;
        }

        const span = document.createElement('span');
        span.className = `ed-tei-entity ed-tei-entity-${type}`;
        span.contentEditable = 'false';
        span.setAttribute('data-tei-tag', _entityTypeToTag(type));
        span.setAttribute('data-ref', '');
        span.setAttribute('data-entity-type', type);
        span.title = _entityTypeLabel(type);

        try {
            range.surroundContents(span);
        } catch (ex) {
            const frag = range.extractContents();
            span.appendChild(frag);
            range.insertNode(span);
        }

        sel.removeAllRanges();
        save.markDirty();
    }

    function _changeEntityType(entitySpan, newType) {
        const oldType = entitySpan.getAttribute('data-entity-type');
        if (oldType === newType) return;

        entitySpan.classList.remove(`ed-tei-entity-${oldType}`);
        entitySpan.classList.add(`ed-tei-entity-${newType}`);
        entitySpan.setAttribute('data-tei-tag', _entityTypeToTag(newType));
        entitySpan.setAttribute('data-entity-type', newType);
        entitySpan.title = _entityTypeLabel(newType) +
            (entitySpan.getAttribute('data-ref') ? ` (${entitySpan.getAttribute('data-ref')})` : '');
        save.markDirty();
    }

    function _removeEntityAtSelection() {
        const sel = window.getSelection();
        if (!sel || sel.rangeCount === 0) return;

        let node = sel.anchorNode;
        let entitySpan = null;
        while (node && node !== document.body) {
            if (node.nodeType === 1 && node.classList &&
                node.classList.contains('ed-tei-entity')) {
                entitySpan = node;
                break;
            }
            node = node.parentNode;
        }

        if (!entitySpan) {
            save.showToast('Keine Entity am Cursor', 'info');
            return;
        }

        const parent = entitySpan.parentNode;
        while (entitySpan.firstChild) {
            parent.insertBefore(entitySpan.firstChild, entitySpan);
        }
        parent.removeChild(entitySpan);
        parent.normalize();
        save.markDirty();
    }

    // Entity reference popover with autocomplete
    let entityPopover = null;
    let _acTimer = null;

    function _showEntityPopover(entitySpan) {
        _hideEntityPopover();

        const pop = document.createElement('div');
        pop.className = 'ed-entity-popover';

        const type = entitySpan.getAttribute('data-entity-type') || 'person';
        const ref = entitySpan.getAttribute('data-ref') || '';
        const text = entitySpan.textContent;

        pop.innerHTML =
            '<div class="ed-entity-popover-header">' +
                `<strong>${E.esc(text)}</strong>` +
                `<span class="ed-badge ed-badge-type">${E.esc(_entityTypeLabel(type).toUpperCase())}</span>` +
            '</div>' +
            '<div class="ed-entity-popover-body">' +
                '<label>Referenz (ref):</label>' +
                '<div class="ed-ac-wrap">' +
                    `<input type="text" class="ed-entity-ref-input" value="${E.esc(ref)}" placeholder="Suche oder GND/Wikidata-ID..." autocomplete="off">` +
                    '<div class="ed-ac-results"></div>' +
                '</div>' +
                '<div class="ed-entity-popover-actions">' +
                    '<button class="ed-entity-popover-btn ed-entity-popover-save">Uebernehmen</button>' +
                    '<button class="ed-entity-popover-btn ed-entity-popover-cancel">Abbrechen</button>' +
                '</div>' +
            '</div>';

        const rect = entitySpan.getBoundingClientRect();
        pop.style.top = (window.scrollY + rect.bottom + 4) + 'px';
        pop.style.left = (window.scrollX + rect.left) + 'px';

        document.body.appendChild(pop);
        entityPopover = pop;

        const input = pop.querySelector('.ed-entity-ref-input');
        const acResults = pop.querySelector('.ed-ac-results');

        input.addEventListener('input', () => {
            const q = input.value.trim();
            if (q.length < 2) {
                acResults.innerHTML = '';
                acResults.classList.remove('ed-ac-results-visible');
                return;
            }
            if (_acTimer) clearTimeout(_acTimer);
            _acTimer = setTimeout(() => {
                _searchAutocomplete(q, type, acResults, input, entitySpan);
            }, 250);
        });

        if (!ref && text.trim().length >= 2) {
            setTimeout(() => {
                _searchAutocomplete(text.trim(), type, acResults, input, entitySpan);
            }, 100);
        }

        setTimeout(() => { input.focus(); input.select(); }, 50);

        pop.querySelector('.ed-entity-popover-save').addEventListener('click', () => {
            _applyRef(entitySpan, type, input.value.trim());
            _hideEntityPopover();
        });

        pop.querySelector('.ed-entity-popover-cancel').addEventListener('click', () => {
            _hideEntityPopover();
        });

        input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                const active = acResults.querySelector('.ed-ac-item-active');
                if (active) {
                    active.click();
                } else {
                    _applyRef(entitySpan, type, input.value.trim());
                    _hideEntityPopover();
                }
            } else if (e.key === 'Escape') {
                _hideEntityPopover();
            } else if (e.key === 'ArrowDown') {
                e.preventDefault();
                _acNavigate(acResults, 1);
            } else if (e.key === 'ArrowUp') {
                e.preventDefault();
                _acNavigate(acResults, -1);
            }
        });
    }

    function _applyRef(entitySpan, type, refValue) {
        entitySpan.setAttribute('data-ref', refValue);
        entitySpan.title = _entityTypeLabel(type) +
            (refValue ? ` (${refValue})` : '');
        save.markDirty();
    }

    function _searchAutocomplete(query, entityType, resultsEl, input, entitySpan) {
        resultsEl.innerHTML = '<div class="ed-ac-loading">Suche...</div>';
        resultsEl.classList.add('ed-ac-results-visible');

        let localDone = false, wdDone = false;
        let localResults = [], wdResults = [];

        function renderAll() {
            if (!localDone || !wdDone) return;
            resultsEl.innerHTML = '';

            let hasResults = false;

            if (localResults.length > 0) {
                const hdr = document.createElement('div');
                hdr.className = 'ed-ac-section-header';
                hdr.textContent = 'Entity Index';
                resultsEl.appendChild(hdr);
                hasResults = true;

                for (let i = 0; i < localResults.length; i++) {
                    resultsEl.appendChild(_createAcItem(localResults[i], input, entitySpan, entityType));
                }
            }

            if (wdResults.length > 0) {
                const hdr2 = document.createElement('div');
                hdr2.className = 'ed-ac-section-header';
                hdr2.textContent = 'Wikidata';
                resultsEl.appendChild(hdr2);
                hasResults = true;

                for (let j = 0; j < wdResults.length; j++) {
                    resultsEl.appendChild(_createAcItem(wdResults[j], input, entitySpan, entityType));
                }
            }

            if (!hasResults) {
                resultsEl.innerHTML = '<div class="ed-ac-empty">Keine Treffer</div>';
            }

            resultsEl.classList.toggle('ed-ac-results-visible', hasResults || !localDone || !wdDone);
        }

        fetch(`${api.API_BASE}/entities/search?q=${encodeURIComponent(query)}&limit=5`)
            .then((r) => r.ok ? r.json() : { results: [] })
            .then((data) => {
                localResults = (data.results || []).map((r) => {
                    const extRefs = [];
                    if (r.gnd) extRefs.push(`GND:${r.gnd}`);
                    if (r.wikidata) extRefs.push(r.wikidata);
                    return {
                        label: r.name || r.id,
                        desc: r.id + (r.type ? ` (${r.type})` : '') + (extRefs.length ? ` — ${extRefs.join(', ')}` : ''),
                        ref: `#${r.id}`,
                        source: 'index'
                    };
                });
            })
            .catch(() => { localResults = []; })
            .then(() => { localDone = true; renderAll(); });

        fetch(api.API_BASE + '/wikidata/search', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query: query, lang: 'de', limit: 5 })
        })
            .then((r) => r.ok ? r.json() : { results: [] })
            .then((data) => {
                wdResults = (data.results || []).map((r) => ({
                    label: r.label || r.id,
                    desc: r.description || '',
                    ref: r.id,
                    url: r.url || '',
                    source: 'wikidata'
                }));
            })
            .catch(() => { wdResults = []; })
            .then(() => { wdDone = true; renderAll(); });
    }

    function _createAcItem(item, input, entitySpan, entityType) {
        const div = document.createElement('div');
        div.className = 'ed-ac-item';
        div.innerHTML =
            `<span class="ed-ac-item-label">${E.esc(item.label)}</span>` +
            `<span class="ed-ac-item-ref">${E.esc(item.ref)}</span>` +
            (item.desc ? `<span class="ed-ac-item-desc">${E.esc(item.desc)}</span>` : '');

        div.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            input.value = item.ref;
            _applyRef(entitySpan, entityType, item.ref);
            _hideEntityPopover();
        });

        div.addEventListener('mouseenter', () => {
            const items = Array.prototype.slice.call(div.parentNode.querySelectorAll('.ed-ac-item'));
            for (let k = 0; k < items.length; k++) items[k].classList.remove('ed-ac-item-active');
            div.classList.add('ed-ac-item-active');
        });

        return div;
    }

    function _acNavigate(resultsEl, dir) {
        const items = Array.prototype.slice.call(resultsEl.querySelectorAll('.ed-ac-item'));
        if (items.length === 0) return;

        let activeIdx = -1;
        for (let i = 0; i < items.length; i++) {
            if (items[i].classList.contains('ed-ac-item-active')) {
                activeIdx = i;
                items[i].classList.remove('ed-ac-item-active');
                break;
            }
        }

        let newIdx = activeIdx + dir;
        if (newIdx < 0) newIdx = items.length - 1;
        if (newIdx >= items.length) newIdx = 0;
        items[newIdx].classList.add('ed-ac-item-active');
        items[newIdx].scrollIntoView({ block: 'nearest' });
    }

    function _hideEntityPopover() {
        if (entityPopover) {
            entityPopover.remove();
            entityPopover = null;
        }
    }

    function _initEntityClickHandler(container) {
        container.addEventListener('click', (e) => {
            const entity = e.target.closest('.ed-tei-entity');
            if (!entity || !state.active) return;

            e.preventDefault();
            e.stopPropagation();
            _showEntityPopover(entity);
        });
    }

    function _initEntitySelectionHandler(container) {
        container.addEventListener('mouseup', (e) => {
            if (!state.active) return;

            if (e.target.closest('.ed-tei-entity')) return;

            const sel = window.getSelection();
            if (!sel || sel.isCollapsed) {
                _hideEntityToolbar();
                return;
            }

            const text = sel.toString().trim();
            if (!text || text.length < 2) {
                _hideEntityToolbar();
                return;
            }

            const range = sel.getRangeAt(0);
            const rect = range.getBoundingClientRect();
            _showEntityToolbar(
                window.scrollX + rect.left + rect.width / 2 - 80,
                window.scrollY + rect.top
            );
        });
    }

    let _docListenersInitialized = false;
    function _initDocumentListeners() {
        if (_docListenersInitialized) return;
        _docListenersInitialized = true;

        document.addEventListener('mousedown', (e) => {
            if (entityToolbar && !entityToolbar.contains(e.target)) {
                _hideEntityToolbar();
            }
            if (entityPopover && !entityPopover.contains(e.target) &&
                !e.target.closest('.ed-tei-entity')) {
                _hideEntityPopover();
            }
        });
    }

    ZBZ.EditionEditor._entities = {
        entityTypeToTag: _entityTypeToTag,
        entityTypeLabel: _entityTypeLabel,
        initEntityHandlers: function (container) {
            _initEntitySelectionHandler(container);
            _initEntityClickHandler(container);
        },
        initDocumentListeners: _initDocumentListeners
    };
})();
