/**
 * ZBZ Edition – Editor Module
 * WYSIWYG editing of TEI-XML with contenteditable blocks.
 * Handles: editable rendering, DOM-to-XML serialization, save/load via API.
 * Namespace: ZBZ.EditionEditor (ES6+, IIFE)
 */
(function () {
    'use strict';

    const E = ZBZ.Edition;

    // Derive API base from current page URL (works on any port)
    const API_BASE = window.location.origin + '/api';

    const editorState = {
        active: false,
        dirty: false,
        serverAvailable: false,
        currentXml: null
    };

    // --- Server Detection ---
    function checkServer(callback) {
        // Only check on localhost — skip on GitHub Pages to avoid 404 noise
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

    // --- API Helpers ---
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

    // --- Fetch TEI via Server (curated priority) ---
    function fetchTeiFromServer(docId, page) {
        if (!editorState.serverAvailable) return Promise.resolve(null);
        return apiGet(`/tei/${docId}/page/${page}`)
            .then((data) => data)
            .catch(() => null);
    }

    // --- Editable Rendering ---
    function renderEditable(xml, container) {
        editorState.currentXml = xml;
        container.innerHTML = '';

        if (!xml) {
            container.innerHTML = '<div class="ed-empty-state">Keine TEI-Daten fuer diese Seite.</div>';
            return;
        }

        const doc = E.parseXml(xml);
        if (!doc) {
            container.innerHTML = '<div class="ed-empty-state">XML-Parse-Fehler</div>';
            return;
        }

        const body = doc.querySelector('body');
        if (!body) {
            container.innerHTML = '<div class="ed-empty-state">Kein &lt;body&gt; im TEI</div>';
            return;
        }

        renderNodeEditable(body, container);

        // Listen for input events on contenteditable elements
        container.addEventListener('input', () => {
            markDirty();
        });

        // Init block toolbar + entity handlers (container-level only)
        _initBlockToolbarListeners(container);
        _initEntityClickHandler(container);
        _initEntitySelectionHandler(container);
        // Document-level listeners: register only once
        _initDocumentListeners();
    }

    function renderNodeEditable(node, container) {
        if (node.nodeType === 3) {
            const t = node.textContent;
            if (t.trim()) container.appendChild(document.createTextNode(t));
            return;
        }
        if (node.nodeType !== 1) return;

        const tag = node.localName;

        // Skip metadata
        if (tag === 'teiHeader' || tag === 'facsimile') return;

        // Transparent containers
        if (tag === 'TEI' || tag === 'text' || tag === 'body' || tag === 'div' ||
            tag === 'front' || tag === 'back') {
            for (let i = 0; i < node.childNodes.length; i++) {
                renderNodeEditable(node.childNodes[i], container);
            }
            return;
        }

        let elem = null;

        if (tag === 'pb') {
            elem = document.createElement('div');
            elem.className = 'ed-tei-pb';
            elem.textContent = `-- Seite ${node.getAttribute('n') || '?'} --`;
            elem.setAttribute('data-tei-tag', 'pb');
            elem.setAttribute('data-n', node.getAttribute('n') || '');
            elem.setAttribute('data-facs', node.getAttribute('facs') || '');
            container.appendChild(elem);
            return;
        }

        if (tag === 'space') {
            elem = document.createElement('div');
            elem.className = 'ed-tei-space';
            elem.setAttribute('data-tei-tag', 'space');
            container.appendChild(elem);
            return;
        }

        if (tag === 'head') {
            elem = document.createElement('div');
            elem.className = 'ed-tei-head';
            elem.contentEditable = 'true';
            elem.setAttribute('data-tei-tag', 'head');
            elem.setAttribute('data-facs', node.getAttribute('facs') || '');
        } else if (tag === 'p') {
            elem = document.createElement('div');
            elem.className = 'ed-tei-p';
            elem.contentEditable = 'true';
            elem.setAttribute('data-tei-tag', 'p');
            elem.setAttribute('data-facs', node.getAttribute('facs') || '');
        } else if (tag === 'note') {
            elem = document.createElement('div');
            elem.className = 'ed-tei-note';
            elem.contentEditable = 'true';
            elem.setAttribute('data-tei-tag', 'note');
            elem.setAttribute('data-place', node.getAttribute('place') || 'foot');
            elem.setAttribute('data-n', node.getAttribute('n') || '');
            const nAttr = node.getAttribute('n');
            if (nAttr) {
                const lbl = document.createElement('span');
                lbl.className = 'ed-tei-note-label';
                lbl.contentEditable = 'false';
                lbl.textContent = `[${nAttr}]`;
                elem.appendChild(lbl);
            }
        } else if (tag === 'figure') {
            elem = document.createElement('div');
            elem.className = 'ed-tei-figure';
            elem.textContent = '[Abbildung]';
            elem.setAttribute('data-tei-tag', 'figure');
            container.appendChild(elem);
            return;
        } else if (tag === 'hi') {
            const rend = node.getAttribute('rendition') || '';
            if (rend === '#sup') {
                elem = document.createElement('sup');
            } else if (rend === '#sub') {
                elem = document.createElement('sub');
            } else {
                elem = document.createElement('span');
                const hiCls = { '#b': 'ed-tei-hi-bold', '#i': 'ed-tei-hi-italic', '#u': 'ed-tei-hi-underline', '#g': 'ed-tei-hi-spaced' };
                if (hiCls[rend]) elem.className = hiCls[rend];
            }
            elem.setAttribute('data-tei-tag', 'hi');
            elem.setAttribute('data-rendition', rend);
        } else if (tag === 'persName') {
            elem = _createEditableEntity(node, 'person');
        } else if (tag === 'orgName') {
            elem = _createEditableEntity(node, 'org');
        } else if (tag === 'placeName') {
            elem = _createEditableEntity(node, 'place');
        } else if (tag === 'bibl') {
            elem = _createEditableEntity(node, 'work');
        } else if (tag === 'lb') {
            container.appendChild(document.createElement('br'));
            return;
        } else if (tag === 'foreign') {
            elem = document.createElement('span');
            elem.className = 'ed-tei-foreign';
            elem.setAttribute('data-tei-tag', 'foreign');
            elem.setAttribute('data-lang', node.getAttribute('xml:lang') || '');
            elem.title = `Sprache: ${node.getAttribute('xml:lang') || '?'}`;
        } else if (tag === 'sp') {
            elem = document.createElement('div');
            elem.className = 'ed-tei-sp';
            elem.setAttribute('data-tei-tag', 'sp');
        } else if (tag === 'speaker') {
            elem = document.createElement('span');
            elem.className = 'ed-tei-speaker';
            elem.setAttribute('data-tei-tag', 'speaker');
        } else {
            // Unknown elements: render children transparently
            for (let i = 0; i < node.childNodes.length; i++) {
                renderNodeEditable(node.childNodes[i], container);
            }
            return;
        }

        if (elem) {
            for (let i = 0; i < node.childNodes.length; i++) {
                renderNodeEditable(node.childNodes[i], elem);
            }
            container.appendChild(elem);
        }
    }

    function _createEditableEntity(node, type) {
        const ref = node.getAttribute('ref') || node.getAttribute('corresp') || '';
        const span = document.createElement('span');
        span.className = `ed-tei-entity ed-tei-entity-${type}`;
        span.contentEditable = 'false';
        span.setAttribute('data-tei-tag', _entityTypeToTag(type));
        span.setAttribute('data-ref', ref);
        span.setAttribute('data-entity-type', type);
        span.title = _entityTypeLabel(type) + (ref ? ` (${ref})` : '');
        return span;
    }

    function _entityTypeToTag(type) {
        const map = { person: 'persName', org: 'orgName', place: 'placeName', work: 'bibl' };
        return map[type] || type;
    }

    function _entityTypeLabel(type) {
        const map = { person: 'Person', org: 'Organisation', place: 'Ort', work: 'Werk' };
        return map[type] || type;
    }

    // --- DOM-to-XML Serialization ---
    function serializeToXml(container) {
        const lines = [];
        _serializeChildren(container, lines, 0);
        return lines.join('\n');
    }

    function _serializeChildren(parent, lines, depth) {
        const children = parent.childNodes;
        for (let i = 0; i < children.length; i++) {
            _serializeNode(children[i], lines, depth);
        }
    }

    function _serializeNode(node, lines, depth) {
        const indent = _indent(depth);

        // Text node
        if (node.nodeType === 3) {
            const text = node.textContent;
            if (text.trim()) {
                lines.push(_xmlEsc(text));
            }
            return;
        }

        if (node.nodeType !== 1) return;

        const teiTag = node.getAttribute('data-tei-tag');

        // Skip tooltip spans (rendering artifacts)
        if (node.classList && node.classList.contains('ed-tei-entity-tip')) return;
        // Skip note labels
        if (node.classList && node.classList.contains('ed-tei-note-label')) return;

        // BR -> <lb/>
        if (node.tagName === 'BR') {
            lines.push(indent + '<lb/>');
            return;
        }

        // SUP / SUB
        if (node.tagName === 'SUP') {
            lines.push(`<hi rendition="#sup">${_innerXml(node)}</hi>`);
            return;
        }
        if (node.tagName === 'SUB') {
            lines.push(`<hi rendition="#sub">${_innerXml(node)}</hi>`);
            return;
        }

        if (!teiTag) {
            // Untagged element: serialize children
            _serializeChildren(node, lines, depth);
            return;
        }

        // Self-closing elements
        if (teiTag === 'pb') {
            let pbAttrs = '';
            if (node.getAttribute('data-facs')) pbAttrs += ` facs="${_xmlEsc(node.getAttribute('data-facs'))}"`;
            if (node.getAttribute('data-n')) pbAttrs += ` n="${_xmlEsc(node.getAttribute('data-n'))}"`;
            lines.push(`${indent}<pb${pbAttrs}/>`);
            return;
        }

        if (teiTag === 'space') {
            lines.push(indent + '<space/>');
            return;
        }

        if (teiTag === 'figure') {
            lines.push(indent + '<figure/>');
            return;
        }

        // Block elements
        const attrs = _buildAttrs(node, teiTag);
        const inner = _innerXml(node);

        if (teiTag === 'head' || teiTag === 'p' || teiTag === 'note' ||
            teiTag === 'sp' || teiTag === 'div') {
            lines.push(`${indent}<${teiTag}${attrs}>${inner}</${teiTag}>`);
            return;
        }

        // Inline elements
        lines.push(`<${teiTag}${attrs}>${inner}</${teiTag}>`);
    }

    function _buildAttrs(node, teiTag) {
        let attrs = '';

        if (teiTag === 'p' || teiTag === 'head') {
            const facs = node.getAttribute('data-facs');
            if (facs) attrs += ` facs="${_xmlEsc(facs)}"`;
        }

        if (teiTag === 'note') {
            const place = node.getAttribute('data-place');
            if (place) attrs += ` place="${_xmlEsc(place)}"`;
            const n = node.getAttribute('data-n');
            if (n) attrs += ` n="${_xmlEsc(n)}"`;
        }

        if (teiTag === 'hi') {
            const rendition = node.getAttribute('data-rendition');
            if (rendition) attrs += ` rendition="${_xmlEsc(rendition)}"`;
        }

        if (teiTag === 'persName' || teiTag === 'orgName' ||
            teiTag === 'placeName' || teiTag === 'bibl') {
            const ref = node.getAttribute('data-ref');
            if (ref) attrs += ` ref="${_xmlEsc(ref)}"`;
        }

        if (teiTag === 'foreign') {
            const lang = node.getAttribute('data-lang');
            if (lang) attrs += ` xml:lang="${_xmlEsc(lang)}"`;
        }

        return attrs;
    }

    function _innerXml(node) {
        const parts = [];
        for (let i = 0; i < node.childNodes.length; i++) {
            const child = node.childNodes[i];
            if (child.nodeType === 3) {
                parts.push(_xmlEsc(child.textContent));
            } else if (child.nodeType === 1) {
                // Skip tooltip spans and note labels
                if (child.classList && (child.classList.contains('ed-tei-entity-tip') ||
                    child.classList.contains('ed-tei-note-label'))) continue;

                const tag = child.getAttribute('data-tei-tag');
                if (child.tagName === 'BR') {
                    parts.push('<lb/>');
                } else if (child.tagName === 'SUP') {
                    parts.push(`<hi rendition="#sup">${_innerXml(child)}</hi>`);
                } else if (child.tagName === 'SUB') {
                    parts.push(`<hi rendition="#sub">${_innerXml(child)}</hi>`);
                } else if (tag) {
                    const attrs = _buildAttrs(child, tag);
                    if (tag === 'pb') {
                        parts.push(`<pb${attrs}/>`);
                    } else if (tag === 'space') {
                        parts.push('<space/>');
                    } else if (tag === 'figure') {
                        parts.push('<figure/>');
                    } else {
                        parts.push(`<${tag}${attrs}>${_innerXml(child)}</${tag}>`);
                    }
                } else {
                    parts.push(_innerXml(child));
                }
            }
        }
        return parts.join('');
    }

    function _xmlEsc(s) {
        if (!s) return '';
        return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
    }

    function _indent(depth) {
        let s = '';
        for (let i = 0; i < depth; i++) s += '  ';
        return s;
    }

    // --- XML Direct Editing ---
    function renderXmlEditable(xml, container) {
        editorState.currentXml = xml;
        container.innerHTML = '';

        const textarea = document.createElement('textarea');
        textarea.className = 'ed-xml-editor';
        textarea.value = xml || '';
        textarea.spellcheck = false;
        textarea.addEventListener('input', () => {
            markDirty();
        });
        container.appendChild(textarea);
    }

    function getXmlFromEditor(container) {
        const textarea = container.querySelector('.ed-xml-editor');
        if (textarea) return textarea.value;
        return null;
    }

    // --- Save ---
    function savePageXml(docId, page, container, xmlMode) {
        let xml;
        if (xmlMode) {
            xml = getXmlFromEditor(container);
        } else {
            xml = serializeToXml(container);
        }

        if (!xml) {
            showToast('Kein XML zum Speichern', 'error');
            return Promise.resolve(null);
        }

        return apiPut(`/tei/${docId}/page/${page}`, { xml: xml })
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

    // --- Dirty State ---
    function markDirty() {
        if (editorState.dirty) return;
        editorState.dirty = true;
        const btn = E.$('#save-btn');
        if (btn) {
            btn.disabled = false;
            btn.classList.add('ed-dirty');
        }
        const status = E.$('#save-status');
        if (status) status.textContent = 'Ungespeicherte Aenderungen';
    }

    function clearDirty() {
        editorState.dirty = false;
        const btn = E.$('#save-btn');
        if (btn) {
            btn.disabled = true;
            btn.classList.remove('ed-dirty');
        }
        const status = E.$('#save-status');
        if (status) status.textContent = '';
    }

    // --- Toast Notifications ---
    function showToast(message, type) {
        // Remove existing toast
        const existing = E.$('.ed-toast');
        if (existing) existing.remove();

        const toast = document.createElement('div');
        toast.className = `ed-toast ed-toast-${type || 'info'}`;
        toast.textContent = message;
        document.body.appendChild(toast);

        // Trigger reflow for animation
        toast.offsetHeight;
        toast.classList.add('ed-toast-visible');

        setTimeout(() => {
            toast.classList.remove('ed-toast-visible');
            setTimeout(() => { toast.remove(); }, 300);
        }, 3000);
    }

    // ================================================================
    // Phase 2: Block Toolbar — Typ-Wechsel, Split, Merge, Delete
    // ================================================================

    let blockToolbar = null;
    let activeBlock = null;

    function _createBlockToolbar() {
        if (blockToolbar) return blockToolbar;

        const tb = document.createElement('div');
        tb.className = 'ed-block-toolbar';
        tb.innerHTML =
            '<select class="ed-block-type-select" title="Block-Typ aendern">' +
                '<option value="p">Absatz (p)</option>' +
                '<option value="head">Ueberschrift (head)</option>' +
                '<option value="note">Fussnote (note)</option>' +
                '<option value="figure">Abbildung (figure)</option>' +
            '</select>' +
            '<span class="ed-block-separator"></span>' +
            '<button class="ed-block-btn ed-block-fmt" data-fmt="b" title="Fett (Ctrl+B)"><b>B</b></button>' +
            '<button class="ed-block-btn ed-block-fmt" data-fmt="i" title="Kursiv (Ctrl+I)"><i>I</i></button>' +
            '<button class="ed-block-btn ed-block-fmt" data-fmt="u" title="Unterstrichen (Ctrl+U)"><u>U</u></button>' +
            '<span class="ed-block-separator"></span>' +
            '<button class="ed-block-btn" data-action="split" title="Block teilen (am Cursor)">Teilen</button>' +
            '<button class="ed-block-btn" data-action="merge" title="Mit vorherigem Block zusammenfuegen">Zusammenfuegen</button>' +
            '<button class="ed-block-btn ed-block-btn-danger" data-action="delete" title="Block loeschen">Loeschen</button>';

        // Type change
        const sel = tb.querySelector('.ed-block-type-select');
        sel.addEventListener('change', () => {
            if (activeBlock) _changeBlockType(activeBlock, sel.value);
        });

        // Format buttons (B/I/U)
        const fmtBtns = Array.prototype.slice.call(tb.querySelectorAll('.ed-block-fmt'));
        fmtBtns.forEach((btn) => {
            btn.addEventListener('mousedown', (e) => { e.preventDefault(); });
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                _toggleInlineFormat(btn.getAttribute('data-fmt'));
            });
        });

        // Action buttons
        const btns = Array.prototype.slice.call(tb.querySelectorAll('.ed-block-btn:not(.ed-block-fmt)'));
        btns.forEach((btn) => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                const action = btn.getAttribute('data-action');
                if (!activeBlock) return;
                if (action === 'split') _splitBlock(activeBlock);
                else if (action === 'merge') _mergeBlock(activeBlock);
                else if (action === 'delete') _deleteBlock(activeBlock);
            });
        });

        document.body.appendChild(tb);
        blockToolbar = tb;
        return tb;
    }

    function _showBlockToolbar(block) {
        const tb = _createBlockToolbar();
        activeBlock = block;

        // Sync type selector
        const tag = block.getAttribute('data-tei-tag') || 'p';
        const sel = tb.querySelector('.ed-block-type-select');
        sel.value = tag;

        // Sync format button active states
        const fmtBtns = tb.querySelectorAll('.ed-block-fmt');
        const curSel = window.getSelection();
        const anchor = curSel && curSel.anchorNode ? curSel.anchorNode.parentElement : null;
        fmtBtns.forEach((btn) => {
            const fmt = btn.getAttribute('data-fmt');
            let isActive = false;
            let check = anchor;
            while (check && check !== block) {
                if (check.getAttribute && check.getAttribute('data-tei-tag') === 'hi' &&
                    check.getAttribute('data-rendition') === '#' + fmt) {
                    isActive = true;
                    break;
                }
                check = check.parentNode;
            }
            btn.classList.toggle('ed-block-fmt-active', isActive);
        });

        // Make visible first, then position (so offsetHeight is correct)
        tb.classList.add('ed-block-toolbar-visible');
        requestAnimationFrame(() => {
            const rect = block.getBoundingClientRect();
            const tbHeight = tb.offsetHeight || 32;
            tb.style.top = (window.scrollY + rect.top - tbHeight - 4) + 'px';
            tb.style.left = (window.scrollX + rect.left) + 'px';
        });
    }

    function _hideBlockToolbar() {
        if (blockToolbar) {
            blockToolbar.classList.remove('ed-block-toolbar-visible');
        }
        activeBlock = null;
    }

    function _changeBlockType(block, newTag) {
        const oldTag = block.getAttribute('data-tei-tag');
        if (oldTag === newTag) return;

        // CSS class mapping
        const classMap = {
            p: 'ed-tei-p',
            head: 'ed-tei-head',
            note: 'ed-tei-note',
            figure: 'ed-tei-figure'
        };

        // Remove old class, add new
        if (classMap[oldTag]) block.classList.remove(classMap[oldTag]);
        if (classMap[newTag]) block.classList.add(classMap[newTag]);

        block.setAttribute('data-tei-tag', newTag);

        // Figure: non-editable
        if (newTag === 'figure') {
            block.contentEditable = 'false';
            block.textContent = '[Abbildung]';
        } else if (oldTag === 'figure') {
            block.contentEditable = 'true';
            if (block.textContent === '[Abbildung]') block.textContent = '';
        }

        // Note: add/remove label
        if (newTag === 'note' && !block.getAttribute('data-place')) {
            block.setAttribute('data-place', 'foot');
        }

        markDirty();
        _showBlockToolbar(block);
    }

    function _splitBlock(block) {
        const sel = window.getSelection();
        if (!sel || sel.rangeCount === 0) {
            showToast('Cursor im Block platzieren zum Teilen', 'info');
            return;
        }

        const range = sel.getRangeAt(0);
        if (!block.contains(range.startContainer)) {
            showToast('Cursor muss im Block sein', 'info');
            return;
        }

        // Extract content after cursor into a new block
        const afterRange = document.createRange();
        afterRange.setStart(range.endContainer, range.endOffset);
        afterRange.setEnd(block, block.childNodes.length);
        const afterFrag = afterRange.extractContents();

        // Create new block with same type
        const newBlock = document.createElement('div');
        const tag = block.getAttribute('data-tei-tag') || 'p';
        newBlock.className = block.className;
        newBlock.contentEditable = 'true';
        newBlock.setAttribute('data-tei-tag', tag);
        if (block.getAttribute('data-facs')) newBlock.setAttribute('data-facs', '');
        newBlock.appendChild(afterFrag);

        // Insert after current block
        block.parentNode.insertBefore(newBlock, block.nextSibling);
        markDirty();
    }

    function _mergeBlock(block) {
        const prev = block.previousElementSibling;
        if (!prev || !prev.getAttribute('data-tei-tag')) {
            showToast('Kein vorheriger Block zum Zusammenfuegen', 'info');
            return;
        }

        // Move all children from current block into previous
        while (block.firstChild) {
            // Skip note labels
            if (block.firstChild.classList &&
                block.firstChild.classList.contains('ed-tei-note-label')) {
                block.removeChild(block.firstChild);
                continue;
            }
            prev.appendChild(block.firstChild);
        }
        block.parentNode.removeChild(block);
        _hideBlockToolbar();
        markDirty();
    }

    function _deleteBlock(block) {
        const text = (block.textContent || '').trim();
        const preview = text.length > 40 ? text.substring(0, 40) + '...' : text;
        if (preview && !window.confirm(`Block loeschen?\n\n"${preview}"`)) {
            return;
        }
        block.parentNode.removeChild(block);
        _hideBlockToolbar();
        markDirty();
    }

    // --- Inline Formatting (B / I / U) ---

    function _toggleInlineFormat(fmt) {
        const sel = window.getSelection();
        if (!sel || sel.isCollapsed || sel.rangeCount === 0) return;

        const range = sel.getRangeAt(0);
        const text = range.toString().trim();
        if (!text) return;

        // Check if already inside a <hi> with same rendition — toggle off
        let parentHi = range.startContainer.parentElement;
        while (parentHi && parentHi !== document.body) {
            if (parentHi.getAttribute('data-tei-tag') === 'hi' &&
                parentHi.getAttribute('data-rendition') === '#' + fmt) {
                const parent = parentHi.parentNode;
                while (parentHi.firstChild) {
                    parent.insertBefore(parentHi.firstChild, parentHi);
                }
                parent.removeChild(parentHi);
                parent.normalize();
                markDirty();
                return;
            }
            parentHi = parentHi.parentNode;
        }

        // Wrap selection in <hi> span
        const hiCls = { b: 'ed-tei-hi-bold', i: 'ed-tei-hi-italic', u: 'ed-tei-hi-underline' };
        const span = document.createElement('span');
        span.className = hiCls[fmt] || '';
        span.setAttribute('data-tei-tag', 'hi');
        span.setAttribute('data-rendition', '#' + fmt);

        try {
            range.surroundContents(span);
        } catch (ex) {
            const frag = range.extractContents();
            span.appendChild(frag);
            range.insertNode(span);
        }

        sel.removeAllRanges();
        markDirty();
    }

    // Attach block toolbar on focusin for editable blocks
    function _initBlockToolbarListeners(container) {
        container.addEventListener('focusin', (e) => {
            const target = e.target;
            if (target.contentEditable === 'true' && target.getAttribute('data-tei-tag')) {
                _showBlockToolbar(target);
            }
        });

        container.addEventListener('focusout', () => {
            // Delay hiding so toolbar clicks register
            setTimeout(() => {
                const active = document.activeElement;
                if (blockToolbar && blockToolbar.contains(active)) return;
                if (active && active.contentEditable === 'true' &&
                    active.getAttribute('data-tei-tag') &&
                    container.contains(active)) return;
                _hideBlockToolbar();
            }, 150);
        });
    }

    // ================================================================
    // Phase 3: Entity Tagging — Mark text, assign entity type
    // ================================================================

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
                e.preventDefault(); // Prevent losing selection
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

        // Check if inside an editable block
        const container = E.$('.ed-text-content');
        if (!container || !container.contains(range.commonAncestorContainer)) return;

        // Check if selection is already inside an entity span — change type instead
        const parentEntity = range.startContainer.parentElement;
        if (parentEntity && parentEntity.classList &&
            parentEntity.classList.contains('ed-tei-entity')) {
            _changeEntityType(parentEntity, type);
            return;
        }

        // Wrap selection in entity span
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
            // surroundContents fails if selection crosses element boundaries
            // Fallback: extract and wrap
            const frag = range.extractContents();
            span.appendChild(frag);
            range.insertNode(span);
        }

        sel.removeAllRanges();
        markDirty();
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
        markDirty();
    }

    function _removeEntityAtSelection() {
        const sel = window.getSelection();
        if (!sel || sel.rangeCount === 0) return;

        // Find entity span at cursor or selection
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
            showToast('Keine Entity am Cursor', 'info');
            return;
        }

        // Unwrap: replace span with its text content
        const parent = entitySpan.parentNode;
        while (entitySpan.firstChild) {
            parent.insertBefore(entitySpan.firstChild, entitySpan);
        }
        parent.removeChild(entitySpan);
        parent.normalize(); // Merge adjacent text nodes
        markDirty();
    }

    // Entity click handler — show popover for editing ref
    function _initEntityClickHandler(container) {
        container.addEventListener('click', (e) => {
            const entity = e.target.closest('.ed-tei-entity');
            if (!entity || !editorState.active) return;

            e.preventDefault();
            e.stopPropagation();
            _showEntityPopover(entity);
        });
    }

    // Entity reference popover with autocomplete
    let entityPopover = null;
    let _acTimer = null;  // autocomplete debounce timer

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

        // Autocomplete: search on input
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

        // Auto-search with entity text on open (if no ref yet)
        if (!ref && text.trim().length >= 2) {
            setTimeout(() => {
                _searchAutocomplete(text.trim(), type, acResults, input, entitySpan);
            }, 100);
        }

        // Focus input
        setTimeout(() => { input.focus(); input.select(); }, 50);

        // Save
        pop.querySelector('.ed-entity-popover-save').addEventListener('click', () => {
            _applyRef(entitySpan, type, input.value.trim());
            _hideEntityPopover();
        });

        // Cancel
        pop.querySelector('.ed-entity-popover-cancel').addEventListener('click', () => {
            _hideEntityPopover();
        });

        // Keyboard: Enter saves, Escape cancels, ArrowDown into results
        input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                // If autocomplete is visible and has an active item, pick it
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
        markDirty();
    }

    // --- Autocomplete: parallel search in Entity Index + Wikidata ---
    function _searchAutocomplete(query, entityType, resultsEl, input, entitySpan) {
        resultsEl.innerHTML = '<div class="ed-ac-loading">Suche...</div>';
        resultsEl.classList.add('ed-ac-results-visible');

        let localDone = false, wdDone = false;
        let localResults = [], wdResults = [];

        function renderAll() {
            if (!localDone || !wdDone) return;
            resultsEl.innerHTML = '';

            let hasResults = false;

            // Local Entity Index results first
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

            // Wikidata results
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

        // 1. Local Entity Index
        fetch(`${API_BASE}/entities/search?q=${encodeURIComponent(query)}&limit=5`)
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

        // 2. Wikidata search
        fetch(API_BASE + '/wikidata/search', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query: query, lang: 'de', limit: 5 })
        })
            .then((r) => r.ok ? r.json() : { results: [] })
            .then((data) => {
                wdResults = (data.results || []).map((r) => ({
                    label: r.label || r.id,
                    desc: r.description || '',
                    ref: r.id,  // e.g. Q123456
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

        // Hover highlight
        div.addEventListener('mouseenter', () => {
            const items = Array.prototype.slice.call(div.parentNode.querySelectorAll('.ed-ac-item'));
            for (let k = 0; k < items.length; k++) items[k].classList.remove('ed-ac-item-active');
            div.classList.add('ed-ac-item-active');
        });

        return div;
    }

    // Keyboard navigation in autocomplete results
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

    // Show entity toolbar on text selection (mouseup in edit mode)
    function _initEntitySelectionHandler(container) {
        container.addEventListener('mouseup', (e) => {
            if (!editorState.active) return;

            // Don't show if clicking on an entity (popover handles that)
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

    // Document-level listeners — registered ONCE, not per render
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

    // --- Public API ---
    ZBZ.EditionEditor = {
        checkServer: checkServer,
        fetchTeiFromServer: fetchTeiFromServer,
        renderEditable: renderEditable,
        renderXmlEditable: renderXmlEditable,
        serializeToXml: serializeToXml,
        savePageXml: savePageXml,
        toggleInlineFormat: _toggleInlineFormat,
        markDirty: markDirty,
        clearDirty: clearDirty,
        showToast: showToast,
        initBlockToolbar: _initBlockToolbarListeners,
        initEntityHandlers: function (container) {
            _initEntitySelectionHandler(container);
            _initEntityClickHandler(container);
        },
        state: editorState
    };
})();
