/**
 * ZBZ Edition – Editor Module
 * WYSIWYG editing of TEI-XML with contenteditable blocks.
 * Handles: editable rendering, DOM-to-XML serialization, save/load via API.
 * Namespace: ZBZ.EditionEditor (ES5, IIFE)
 */
(function () {
    'use strict';

    var E = ZBZ.Edition;

    // Derive API base from current page URL (works on any port)
    var API_BASE = window.location.origin + '/api';

    var editorState = {
        active: false,
        dirty: false,
        serverAvailable: false,
        currentXml: null
    };

    // --- Server Detection ---
    function checkServer(callback) {
        fetch(API_BASE + '/health', { method: 'GET' })
            .then(function (r) {
                editorState.serverAvailable = r.ok;
                if (callback) callback(r.ok);
            })
            .catch(function () {
                editorState.serverAvailable = false;
                if (callback) callback(false);
            });
    }

    // --- API Helpers ---
    function apiGet(path) {
        return fetch(API_BASE + path).then(function (r) {
            if (!r.ok) throw new Error('API Error: ' + r.status);
            return r.json();
        });
    }

    function apiPut(path, body) {
        return fetch(API_BASE + path, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body)
        }).then(function (r) {
            if (!r.ok) return r.json().then(function (err) { throw err; });
            return r.json();
        });
    }

    // --- Fetch TEI via Server (curated priority) ---
    function fetchTeiFromServer(docId, page) {
        if (!editorState.serverAvailable) return Promise.resolve(null);
        return apiGet('/tei/' + docId + '/page/' + page)
            .then(function (data) { return data; })
            .catch(function () { return null; });
    }

    // --- Editable Rendering ---
    function renderEditable(xml, container) {
        editorState.currentXml = xml;
        container.innerHTML = '';

        if (!xml) {
            container.innerHTML = '<div class="ed-empty-state">Keine TEI-Daten fuer diese Seite.</div>';
            return;
        }

        var doc = E.parseXml(xml);
        if (!doc) {
            container.innerHTML = '<div class="ed-empty-state">XML-Parse-Fehler</div>';
            return;
        }

        var body = doc.querySelector('body');
        if (!body) {
            container.innerHTML = '<div class="ed-empty-state">Kein &lt;body&gt; im TEI</div>';
            return;
        }

        renderNodeEditable(body, container);

        // Listen for input events on contenteditable elements
        container.addEventListener('input', function () {
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
        var i;
        if (node.nodeType === 3) {
            var t = node.textContent;
            if (t.trim()) container.appendChild(document.createTextNode(t));
            return;
        }
        if (node.nodeType !== 1) return;

        var tag = node.localName;

        // Skip metadata
        if (tag === 'teiHeader' || tag === 'facsimile') return;

        // Transparent containers
        if (tag === 'TEI' || tag === 'text' || tag === 'body' || tag === 'div' ||
            tag === 'front' || tag === 'back') {
            for (i = 0; i < node.childNodes.length; i++) {
                renderNodeEditable(node.childNodes[i], container);
            }
            return;
        }

        var elem = null;

        if (tag === 'pb') {
            elem = document.createElement('div');
            elem.className = 'ed-tei-pb';
            elem.textContent = '-- Seite ' + (node.getAttribute('n') || '?') + ' --';
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
            var nAttr = node.getAttribute('n');
            if (nAttr) {
                var lbl = document.createElement('span');
                lbl.className = 'ed-tei-note-label';
                lbl.contentEditable = 'false';
                lbl.textContent = '[' + nAttr + ']';
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
            var rend = node.getAttribute('rendition') || '';
            if (rend === '#sup') {
                elem = document.createElement('sup');
            } else if (rend === '#sub') {
                elem = document.createElement('sub');
            } else {
                elem = document.createElement('span');
                var hiCls = { '#b': 'ed-tei-hi-bold', '#i': 'ed-tei-hi-italic', '#u': 'ed-tei-hi-underline', '#g': 'ed-tei-hi-spaced' };
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
            elem.title = 'Sprache: ' + (node.getAttribute('xml:lang') || '?');
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
            for (i = 0; i < node.childNodes.length; i++) {
                renderNodeEditable(node.childNodes[i], container);
            }
            return;
        }

        if (elem) {
            for (i = 0; i < node.childNodes.length; i++) {
                renderNodeEditable(node.childNodes[i], elem);
            }
            container.appendChild(elem);
        }
    }

    function _createEditableEntity(node, type) {
        var ref = node.getAttribute('ref') || node.getAttribute('corresp') || '';
        var span = document.createElement('span');
        span.className = 'ed-tei-entity ed-tei-entity-' + type;
        span.contentEditable = 'false';
        span.setAttribute('data-tei-tag', _entityTypeToTag(type));
        span.setAttribute('data-ref', ref);
        span.setAttribute('data-entity-type', type);
        span.title = _entityTypeLabel(type) + (ref ? ' (' + ref + ')' : '');
        return span;
    }

    function _entityTypeToTag(type) {
        var map = { person: 'persName', org: 'orgName', place: 'placeName', work: 'bibl' };
        return map[type] || type;
    }

    function _entityTypeLabel(type) {
        var map = { person: 'Person', org: 'Organisation', place: 'Ort', work: 'Werk' };
        return map[type] || type;
    }

    // --- DOM-to-XML Serialization ---
    function serializeToXml(container) {
        var lines = [];
        _serializeChildren(container, lines, 0);
        return lines.join('\n');
    }

    function _serializeChildren(parent, lines, depth) {
        var children = parent.childNodes;
        for (var i = 0; i < children.length; i++) {
            _serializeNode(children[i], lines, depth);
        }
    }

    function _serializeNode(node, lines, depth) {
        var indent = _indent(depth);

        // Text node
        if (node.nodeType === 3) {
            var text = node.textContent;
            if (text.trim()) {
                lines.push(_xmlEsc(text));
            }
            return;
        }

        if (node.nodeType !== 1) return;

        var teiTag = node.getAttribute('data-tei-tag');

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
            lines.push('<hi rendition="#sup">' + _innerXml(node) + '</hi>');
            return;
        }
        if (node.tagName === 'SUB') {
            lines.push('<hi rendition="#sub">' + _innerXml(node) + '</hi>');
            return;
        }

        if (!teiTag) {
            // Untagged element: serialize children
            _serializeChildren(node, lines, depth);
            return;
        }

        // Self-closing elements
        if (teiTag === 'pb') {
            var pbAttrs = '';
            if (node.getAttribute('data-facs')) pbAttrs += ' facs="' + _xmlEsc(node.getAttribute('data-facs')) + '"';
            if (node.getAttribute('data-n')) pbAttrs += ' n="' + _xmlEsc(node.getAttribute('data-n')) + '"';
            lines.push(indent + '<pb' + pbAttrs + '/>');
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
        var attrs = _buildAttrs(node, teiTag);
        var inner = _innerXml(node);

        if (teiTag === 'head' || teiTag === 'p' || teiTag === 'note' ||
            teiTag === 'sp' || teiTag === 'div') {
            lines.push(indent + '<' + teiTag + attrs + '>' + inner + '</' + teiTag + '>');
            return;
        }

        // Inline elements
        lines.push('<' + teiTag + attrs + '>' + inner + '</' + teiTag + '>');
    }

    function _buildAttrs(node, teiTag) {
        var attrs = '';

        if (teiTag === 'p' || teiTag === 'head') {
            var facs = node.getAttribute('data-facs');
            if (facs) attrs += ' facs="' + _xmlEsc(facs) + '"';
        }

        if (teiTag === 'note') {
            var place = node.getAttribute('data-place');
            if (place) attrs += ' place="' + _xmlEsc(place) + '"';
            var n = node.getAttribute('data-n');
            if (n) attrs += ' n="' + _xmlEsc(n) + '"';
        }

        if (teiTag === 'hi') {
            var rendition = node.getAttribute('data-rendition');
            if (rendition) attrs += ' rendition="' + _xmlEsc(rendition) + '"';
        }

        if (teiTag === 'persName' || teiTag === 'orgName' ||
            teiTag === 'placeName' || teiTag === 'bibl') {
            var ref = node.getAttribute('data-ref');
            if (ref) attrs += ' ref="' + _xmlEsc(ref) + '"';
        }

        if (teiTag === 'foreign') {
            var lang = node.getAttribute('data-lang');
            if (lang) attrs += ' xml:lang="' + _xmlEsc(lang) + '"';
        }

        return attrs;
    }

    function _innerXml(node) {
        var parts = [];
        for (var i = 0; i < node.childNodes.length; i++) {
            var child = node.childNodes[i];
            if (child.nodeType === 3) {
                parts.push(_xmlEsc(child.textContent));
            } else if (child.nodeType === 1) {
                // Skip tooltip spans and note labels
                if (child.classList && (child.classList.contains('ed-tei-entity-tip') ||
                    child.classList.contains('ed-tei-note-label'))) continue;

                var tag = child.getAttribute('data-tei-tag');
                if (child.tagName === 'BR') {
                    parts.push('<lb/>');
                } else if (child.tagName === 'SUP') {
                    parts.push('<hi rendition="#sup">' + _innerXml(child) + '</hi>');
                } else if (child.tagName === 'SUB') {
                    parts.push('<hi rendition="#sub">' + _innerXml(child) + '</hi>');
                } else if (tag) {
                    var attrs = _buildAttrs(child, tag);
                    if (tag === 'pb') {
                        parts.push('<pb' + attrs + '/>');
                    } else if (tag === 'space') {
                        parts.push('<space/>');
                    } else if (tag === 'figure') {
                        parts.push('<figure/>');
                    } else {
                        parts.push('<' + tag + attrs + '>' + _innerXml(child) + '</' + tag + '>');
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
        var s = '';
        for (var i = 0; i < depth; i++) s += '  ';
        return s;
    }

    // --- XML Direct Editing ---
    function renderXmlEditable(xml, container) {
        editorState.currentXml = xml;
        container.innerHTML = '';

        var textarea = document.createElement('textarea');
        textarea.className = 'ed-xml-editor';
        textarea.value = xml || '';
        textarea.spellcheck = false;
        textarea.addEventListener('input', function () {
            markDirty();
        });
        container.appendChild(textarea);
    }

    function getXmlFromEditor(container) {
        var textarea = container.querySelector('.ed-xml-editor');
        if (textarea) return textarea.value;
        return null;
    }

    // --- Save ---
    function savePageXml(docId, page, container, xmlMode) {
        var xml;
        if (xmlMode) {
            xml = getXmlFromEditor(container);
        } else {
            xml = serializeToXml(container);
        }

        if (!xml) {
            showToast('Kein XML zum Speichern', 'error');
            return Promise.resolve(null);
        }

        return apiPut('/tei/' + docId + '/page/' + page, { xml: xml })
            .then(function (result) {
                clearDirty();
                showToast('Seite ' + page + ' gespeichert', 'success');
                return result;
            })
            .catch(function (err) {
                var msg = err.detail ? (typeof err.detail === 'string' ? err.detail : err.detail.message || 'Fehler') : 'Speichern fehlgeschlagen';
                showToast(msg, 'error');
                return null;
            });
    }

    // --- Dirty State ---
    function markDirty() {
        if (editorState.dirty) return;
        editorState.dirty = true;
        var btn = E.$('#save-btn');
        if (btn) {
            btn.disabled = false;
            btn.classList.add('ed-dirty');
        }
        var status = E.$('#save-status');
        if (status) status.textContent = 'Ungespeicherte Aenderungen';
    }

    function clearDirty() {
        editorState.dirty = false;
        var btn = E.$('#save-btn');
        if (btn) {
            btn.disabled = true;
            btn.classList.remove('ed-dirty');
        }
        var status = E.$('#save-status');
        if (status) status.textContent = '';
    }

    // --- Toast Notifications ---
    function showToast(message, type) {
        // Remove existing toast
        var existing = E.$('.ed-toast');
        if (existing) existing.remove();

        var toast = document.createElement('div');
        toast.className = 'ed-toast ed-toast-' + (type || 'info');
        toast.textContent = message;
        document.body.appendChild(toast);

        // Trigger reflow for animation
        toast.offsetHeight;
        toast.classList.add('ed-toast-visible');

        setTimeout(function () {
            toast.classList.remove('ed-toast-visible');
            setTimeout(function () { toast.remove(); }, 300);
        }, 3000);
    }

    // ================================================================
    // Phase 2: Block Toolbar — Typ-Wechsel, Split, Merge, Delete
    // ================================================================

    var blockToolbar = null;
    var activeBlock = null;

    function _createBlockToolbar() {
        if (blockToolbar) return blockToolbar;

        var tb = document.createElement('div');
        tb.className = 'ed-block-toolbar';
        tb.innerHTML =
            '<select class="ed-block-type-select" title="Block-Typ aendern">' +
                '<option value="p">Absatz (p)</option>' +
                '<option value="head">Ueberschrift (head)</option>' +
                '<option value="note">Fussnote (note)</option>' +
                '<option value="figure">Abbildung (figure)</option>' +
            '</select>' +
            '<button class="ed-block-btn" data-action="split" title="Block teilen (am Cursor)">Teilen</button>' +
            '<button class="ed-block-btn" data-action="merge" title="Mit vorherigem Block zusammenfuegen">Zusammenfuegen</button>' +
            '<button class="ed-block-btn ed-block-btn-danger" data-action="delete" title="Block loeschen">Loeschen</button>';

        // Type change
        var sel = tb.querySelector('.ed-block-type-select');
        sel.addEventListener('change', function () {
            if (activeBlock) _changeBlockType(activeBlock, sel.value);
        });

        // Action buttons
        var btns = Array.prototype.slice.call(tb.querySelectorAll('.ed-block-btn'));
        for (var bi = 0; bi < btns.length; bi++) {
            (function (btn) {
                btn.addEventListener('click', function (e) {
                    e.preventDefault();
                    e.stopPropagation();
                    var action = btn.getAttribute('data-action');
                    if (!activeBlock) return;
                    if (action === 'split') _splitBlock(activeBlock);
                    else if (action === 'merge') _mergeBlock(activeBlock);
                    else if (action === 'delete') _deleteBlock(activeBlock);
                });
            })(btns[bi]);
        }

        document.body.appendChild(tb);
        blockToolbar = tb;
        return tb;
    }

    function _showBlockToolbar(block) {
        var tb = _createBlockToolbar();
        activeBlock = block;

        // Sync type selector
        var tag = block.getAttribute('data-tei-tag') || 'p';
        var sel = tb.querySelector('.ed-block-type-select');
        sel.value = tag;

        // Make visible first, then position (so offsetHeight is correct)
        tb.classList.add('ed-block-toolbar-visible');
        requestAnimationFrame(function () {
            var rect = block.getBoundingClientRect();
            var tbHeight = tb.offsetHeight || 32;
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
        var oldTag = block.getAttribute('data-tei-tag');
        if (oldTag === newTag) return;

        // CSS class mapping
        var classMap = {
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
        var sel = window.getSelection();
        if (!sel || sel.rangeCount === 0) {
            showToast('Cursor im Block platzieren zum Teilen', 'info');
            return;
        }

        var range = sel.getRangeAt(0);
        if (!block.contains(range.startContainer)) {
            showToast('Cursor muss im Block sein', 'info');
            return;
        }

        // Extract content after cursor into a new block
        var afterRange = document.createRange();
        afterRange.setStart(range.endContainer, range.endOffset);
        afterRange.setEnd(block, block.childNodes.length);
        var afterFrag = afterRange.extractContents();

        // Create new block with same type
        var newBlock = document.createElement('div');
        var tag = block.getAttribute('data-tei-tag') || 'p';
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
        var prev = block.previousElementSibling;
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
        var text = (block.textContent || '').trim();
        var preview = text.length > 40 ? text.substring(0, 40) + '...' : text;
        if (preview && !window.confirm('Block loeschen?\n\n"' + preview + '"')) {
            return;
        }
        block.parentNode.removeChild(block);
        _hideBlockToolbar();
        markDirty();
    }

    // Attach block toolbar on focusin for editable blocks
    function _initBlockToolbarListeners(container) {
        container.addEventListener('focusin', function (e) {
            var target = e.target;
            if (target.contentEditable === 'true' && target.getAttribute('data-tei-tag')) {
                _showBlockToolbar(target);
            }
        });

        container.addEventListener('focusout', function (e) {
            // Delay hiding so toolbar clicks register
            setTimeout(function () {
                var active = document.activeElement;
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

    var entityToolbar = null;

    function _createEntityToolbar() {
        if (entityToolbar) return entityToolbar;

        var tb = document.createElement('div');
        tb.className = 'ed-entity-toolbar';
        tb.innerHTML =
            '<button class="ed-entity-tag-btn ed-entity-tag-person" data-type="person" title="Person">Person</button>' +
            '<button class="ed-entity-tag-btn ed-entity-tag-org" data-type="org" title="Organisation">Org</button>' +
            '<button class="ed-entity-tag-btn ed-entity-tag-place" data-type="place" title="Ort">Ort</button>' +
            '<button class="ed-entity-tag-btn ed-entity-tag-work" data-type="work" title="Werk">Werk</button>' +
            '<button class="ed-entity-tag-btn ed-entity-tag-remove" data-type="remove" title="Entity entfernen">X</button>';

        var tagBtns = Array.prototype.slice.call(tb.querySelectorAll('.ed-entity-tag-btn'));
        for (var ti = 0; ti < tagBtns.length; ti++) {
            (function (btn) {
                btn.addEventListener('mousedown', function (e) {
                    e.preventDefault(); // Prevent losing selection
                });
                btn.addEventListener('click', function (e) {
                    e.preventDefault();
                    var type = btn.getAttribute('data-type');
                    if (type === 'remove') {
                        _removeEntityAtSelection();
                    } else {
                        _tagSelectionAsEntity(type);
                    }
                    _hideEntityToolbar();
                });
            })(tagBtns[ti]);
        }

        document.body.appendChild(tb);
        entityToolbar = tb;
        return tb;
    }

    function _showEntityToolbar(x, y) {
        var tb = _createEntityToolbar();
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
        var sel = window.getSelection();
        if (!sel || sel.isCollapsed || sel.rangeCount === 0) return;

        var range = sel.getRangeAt(0);
        var text = range.toString().trim();
        if (!text) return;

        // Check if inside an editable block
        var container = E.$('.ed-text-content');
        if (!container || !container.contains(range.commonAncestorContainer)) return;

        // Check if selection is already inside an entity span — change type instead
        var parentEntity = range.startContainer.parentElement;
        if (parentEntity && parentEntity.classList &&
            parentEntity.classList.contains('ed-tei-entity')) {
            _changeEntityType(parentEntity, type);
            return;
        }

        // Wrap selection in entity span
        var span = document.createElement('span');
        span.className = 'ed-tei-entity ed-tei-entity-' + type;
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
            var frag = range.extractContents();
            span.appendChild(frag);
            range.insertNode(span);
        }

        sel.removeAllRanges();
        markDirty();
    }

    function _changeEntityType(entitySpan, newType) {
        var oldType = entitySpan.getAttribute('data-entity-type');
        if (oldType === newType) return;

        entitySpan.classList.remove('ed-tei-entity-' + oldType);
        entitySpan.classList.add('ed-tei-entity-' + newType);
        entitySpan.setAttribute('data-tei-tag', _entityTypeToTag(newType));
        entitySpan.setAttribute('data-entity-type', newType);
        entitySpan.title = _entityTypeLabel(newType) +
            (entitySpan.getAttribute('data-ref') ? ' (' + entitySpan.getAttribute('data-ref') + ')' : '');
        markDirty();
    }

    function _removeEntityAtSelection() {
        var sel = window.getSelection();
        if (!sel || sel.rangeCount === 0) return;

        // Find entity span at cursor or selection
        var node = sel.anchorNode;
        var entitySpan = null;
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
        var parent = entitySpan.parentNode;
        while (entitySpan.firstChild) {
            parent.insertBefore(entitySpan.firstChild, entitySpan);
        }
        parent.removeChild(entitySpan);
        parent.normalize(); // Merge adjacent text nodes
        markDirty();
    }

    // Entity click handler — show popover for editing ref
    function _initEntityClickHandler(container) {
        container.addEventListener('click', function (e) {
            var entity = e.target.closest('.ed-tei-entity');
            if (!entity || !editorState.active) return;

            e.preventDefault();
            e.stopPropagation();
            _showEntityPopover(entity);
        });
    }

    // Entity reference popover with autocomplete
    var entityPopover = null;
    var _acTimer = null;  // autocomplete debounce timer

    function _showEntityPopover(entitySpan) {
        _hideEntityPopover();

        var pop = document.createElement('div');
        pop.className = 'ed-entity-popover';

        var type = entitySpan.getAttribute('data-entity-type') || 'person';
        var ref = entitySpan.getAttribute('data-ref') || '';
        var text = entitySpan.textContent;

        pop.innerHTML =
            '<div class="ed-entity-popover-header">' +
                '<strong>' + E.esc(text) + '</strong>' +
                '<span class="ed-badge ed-badge-type">' + E.esc(_entityTypeLabel(type).toUpperCase()) + '</span>' +
            '</div>' +
            '<div class="ed-entity-popover-body">' +
                '<label>Referenz (ref):</label>' +
                '<div class="ed-ac-wrap">' +
                    '<input type="text" class="ed-entity-ref-input" value="' + E.esc(ref) + '" placeholder="Suche oder GND/Wikidata-ID..." autocomplete="off">' +
                    '<div class="ed-ac-results"></div>' +
                '</div>' +
                '<div class="ed-entity-popover-actions">' +
                    '<button class="ed-entity-popover-btn ed-entity-popover-save">Uebernehmen</button>' +
                    '<button class="ed-entity-popover-btn ed-entity-popover-cancel">Abbrechen</button>' +
                '</div>' +
            '</div>';

        var rect = entitySpan.getBoundingClientRect();
        pop.style.top = (window.scrollY + rect.bottom + 4) + 'px';
        pop.style.left = (window.scrollX + rect.left) + 'px';

        document.body.appendChild(pop);
        entityPopover = pop;

        var input = pop.querySelector('.ed-entity-ref-input');
        var acResults = pop.querySelector('.ed-ac-results');

        // Autocomplete: search on input
        input.addEventListener('input', function () {
            var q = input.value.trim();
            if (q.length < 2) {
                acResults.innerHTML = '';
                acResults.classList.remove('ed-ac-results-visible');
                return;
            }
            if (_acTimer) clearTimeout(_acTimer);
            _acTimer = setTimeout(function () {
                _searchAutocomplete(q, type, acResults, input, entitySpan);
            }, 250);
        });

        // Auto-search with entity text on open (if no ref yet)
        if (!ref && text.trim().length >= 2) {
            setTimeout(function () {
                _searchAutocomplete(text.trim(), type, acResults, input, entitySpan);
            }, 100);
        }

        // Focus input
        setTimeout(function () { input.focus(); input.select(); }, 50);

        // Save
        pop.querySelector('.ed-entity-popover-save').addEventListener('click', function () {
            _applyRef(entitySpan, type, input.value.trim());
            _hideEntityPopover();
        });

        // Cancel
        pop.querySelector('.ed-entity-popover-cancel').addEventListener('click', function () {
            _hideEntityPopover();
        });

        // Keyboard: Enter saves, Escape cancels, ArrowDown into results
        input.addEventListener('keydown', function (e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                // If autocomplete is visible and has an active item, pick it
                var active = acResults.querySelector('.ed-ac-item-active');
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
            (refValue ? ' (' + refValue + ')' : '');
        markDirty();
    }

    // --- Autocomplete: parallel search in Entity Index + Wikidata ---
    function _searchAutocomplete(query, entityType, resultsEl, input, entitySpan) {
        resultsEl.innerHTML = '<div class="ed-ac-loading">Suche...</div>';
        resultsEl.classList.add('ed-ac-results-visible');

        var localDone = false, wdDone = false;
        var localResults = [], wdResults = [];

        function renderAll() {
            if (!localDone || !wdDone) return;
            resultsEl.innerHTML = '';

            var hasResults = false;

            // Local Entity Index results first
            if (localResults.length > 0) {
                var hdr = document.createElement('div');
                hdr.className = 'ed-ac-section-header';
                hdr.textContent = 'Entity Index';
                resultsEl.appendChild(hdr);
                hasResults = true;

                for (var i = 0; i < localResults.length; i++) {
                    resultsEl.appendChild(_createAcItem(localResults[i], input, entitySpan, entityType));
                }
            }

            // Wikidata results
            if (wdResults.length > 0) {
                var hdr2 = document.createElement('div');
                hdr2.className = 'ed-ac-section-header';
                hdr2.textContent = 'Wikidata';
                resultsEl.appendChild(hdr2);
                hasResults = true;

                for (var j = 0; j < wdResults.length; j++) {
                    resultsEl.appendChild(_createAcItem(wdResults[j], input, entitySpan, entityType));
                }
            }

            if (!hasResults) {
                resultsEl.innerHTML = '<div class="ed-ac-empty">Keine Treffer</div>';
            }

            resultsEl.classList.toggle('ed-ac-results-visible', hasResults || !localDone || !wdDone);
        }

        // 1. Local Entity Index
        fetch(API_BASE + '/entities/search?q=' + encodeURIComponent(query) + '&limit=5')
            .then(function (r) { return r.ok ? r.json() : { results: [] }; })
            .then(function (data) {
                localResults = (data.results || []).map(function (r) {
                    var refParts = [];
                    if (r.gnd) refParts.push('GND:' + r.gnd);
                    if (r.wikidata) refParts.push(r.wikidata);
                    return {
                        label: r.name || r.id,
                        desc: (r.type ? r.type : '') + (refParts.length ? ' — ' + refParts.join(', ') : ''),
                        ref: refParts[0] || r.id,
                        source: 'index'
                    };
                });
            })
            .catch(function () { localResults = []; })
            .then(function () { localDone = true; renderAll(); });

        // 2. Wikidata search
        fetch(API_BASE + '/wikidata/search', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query: query, lang: 'de', limit: 5 })
        })
            .then(function (r) { return r.ok ? r.json() : { results: [] }; })
            .then(function (data) {
                wdResults = (data.results || []).map(function (r) {
                    return {
                        label: r.label || r.id,
                        desc: r.description || '',
                        ref: r.id,  // e.g. Q123456
                        url: r.url || '',
                        source: 'wikidata'
                    };
                });
            })
            .catch(function () { wdResults = []; })
            .then(function () { wdDone = true; renderAll(); });
    }

    function _createAcItem(item, input, entitySpan, entityType) {
        var div = document.createElement('div');
        div.className = 'ed-ac-item';
        div.innerHTML =
            '<span class="ed-ac-item-label">' + E.esc(item.label) + '</span>' +
            '<span class="ed-ac-item-ref">' + E.esc(item.ref) + '</span>' +
            (item.desc ? '<span class="ed-ac-item-desc">' + E.esc(item.desc) + '</span>' : '');

        div.addEventListener('click', function (e) {
            e.preventDefault();
            e.stopPropagation();
            input.value = item.ref;
            _applyRef(entitySpan, entityType, item.ref);
            _hideEntityPopover();
        });

        // Hover highlight
        div.addEventListener('mouseenter', function () {
            var items = Array.prototype.slice.call(div.parentNode.querySelectorAll('.ed-ac-item'));
            for (var k = 0; k < items.length; k++) items[k].classList.remove('ed-ac-item-active');
            div.classList.add('ed-ac-item-active');
        });

        return div;
    }

    // Keyboard navigation in autocomplete results
    function _acNavigate(resultsEl, dir) {
        var items = Array.prototype.slice.call(resultsEl.querySelectorAll('.ed-ac-item'));
        if (items.length === 0) return;

        var activeIdx = -1;
        for (var i = 0; i < items.length; i++) {
            if (items[i].classList.contains('ed-ac-item-active')) {
                activeIdx = i;
                items[i].classList.remove('ed-ac-item-active');
                break;
            }
        }

        var newIdx = activeIdx + dir;
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
        container.addEventListener('mouseup', function (e) {
            if (!editorState.active) return;

            // Don't show if clicking on an entity (popover handles that)
            if (e.target.closest('.ed-tei-entity')) return;

            var sel = window.getSelection();
            if (!sel || sel.isCollapsed) {
                _hideEntityToolbar();
                return;
            }

            var text = sel.toString().trim();
            if (!text || text.length < 2) {
                _hideEntityToolbar();
                return;
            }

            var range = sel.getRangeAt(0);
            var rect = range.getBoundingClientRect();
            _showEntityToolbar(
                window.scrollX + rect.left + rect.width / 2 - 80,
                window.scrollY + rect.top
            );
        });
    }

    // Document-level listeners — registered ONCE, not per render
    var _docListenersInitialized = false;
    function _initDocumentListeners() {
        if (_docListenersInitialized) return;
        _docListenersInitialized = true;

        document.addEventListener('mousedown', function (e) {
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
