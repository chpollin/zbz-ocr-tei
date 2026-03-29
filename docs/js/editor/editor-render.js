/**
 * ZBZ Edition Editor — Editable TEI Rendering (XML -> DOM)
 * Depends on: editor-save.js (markDirty), editor-block-toolbar.js, editor-entity.js
 */
(function () {
    'use strict';

    const E = ZBZ.Edition;
    const state = ZBZ.EditionEditor.state;
    const save = ZBZ.EditionEditor._save;
    const blocks = ZBZ.EditionEditor._blocks;
    const entities = ZBZ.EditionEditor._entities;

    function _createEditableEntity(node, type) {
        const ref = node.getAttribute('ref') || node.getAttribute('corresp') || '';
        const span = document.createElement('span');
        span.className = `ed-tei-entity ed-tei-entity-${type}`;
        span.contentEditable = 'false';
        span.setAttribute('data-tei-tag', entities.entityTypeToTag(type));
        span.setAttribute('data-ref', ref);
        span.setAttribute('data-entity-type', type);
        span.title = entities.entityTypeLabel(type) + (ref ? ` (${ref})` : '');
        return span;
    }

    function renderNodeEditable(node, container) {
        if (node.nodeType === 3) {
            const t = node.textContent;
            if (t.trim()) container.appendChild(document.createTextNode(t));
            return;
        }
        if (node.nodeType !== 1) return;

        const tag = node.localName;

        if (tag === 'teiHeader' || tag === 'facsimile') return;

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

    function renderEditable(xml, container) {
        state.currentXml = xml;
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

        container.addEventListener('input', () => {
            save.markDirty();
        });

        blocks.initBlockToolbarListeners(container);
        entities.initEntityHandlers(container);
        entities.initDocumentListeners();
    }

    ZBZ.EditionEditor._render = { renderEditable, renderNodeEditable };
})();
