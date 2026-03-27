/**
 * ZBZ TEI Render — Unified TEI Node Renderer
 * Configurable via options: cssPrefix, lookupFn.
 * Replaces duplicated renderNode logic in edition-tei.js and infra-tei-viewer.js.
 *
 * Depends on: zbz-core.js, entity-utils.js
 * Namespace: ZBZ.TeiRender
 */
(function () {
    'use strict';

    /**
     * Recursively render a TEI XML node into a DOM container.
     * @param {Node} node - XML node to render
     * @param {HTMLElement} container - target DOM container
     * @param {Object} opts - { cssPrefix: 'ed-tei-'|'tei-', lookupFn: fn }
     */
    function renderNode(node, container, opts) {
        if (node.nodeType === 3) {
            const t = node.textContent;
            if (t.trim()) container.appendChild(document.createTextNode(t));
            return;
        }
        if (node.nodeType !== 1) return;

        const tag = node.localName;
        const pfx = opts.cssPrefix;

        // Skip metadata
        if (tag === 'teiHeader' || tag === 'facsimile') return;

        // Transparent containers
        if (tag === 'TEI' || tag === 'text' || tag === 'body' || tag === 'div' ||
            tag === 'front' || tag === 'back') {
            renderChildren(node, container, opts);
            return;
        }

        let elem = null;

        if (tag === 'pb') {
            elem = document.createElement('div');
            elem.className = pfx + 'pb';
            elem.textContent = '-- Seite ' + (node.getAttribute('n') || '?') + ' --';
            container.appendChild(elem);
            return;
        }

        if (tag === 'space') {
            elem = document.createElement('div');
            elem.className = pfx + 'space';
            container.appendChild(elem);
            return;
        }

        if (tag === 'head') {
            elem = document.createElement('div');
            elem.className = pfx + 'head';
        } else if (tag === 'p') {
            elem = document.createElement('div');
            elem.className = pfx + 'p';
        } else if (tag === 'note') {
            elem = document.createElement('div');
            elem.className = pfx + 'note';
            const nAttr = node.getAttribute('n');
            if (nAttr) {
                const lbl = document.createElement('span');
                lbl.className = pfx + 'note-label';
                lbl.textContent = '[' + nAttr + ']';
                elem.appendChild(lbl);
            }
        } else if (tag === 'figure') {
            elem = document.createElement('div');
            elem.className = pfx + 'figure';
            elem.textContent = '[Abbildung]';
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
                const hiCls = {
                    '#b': pfx + 'hi-bold',
                    '#i': pfx + 'hi-italic',
                    '#u': pfx + 'hi-underline',
                    '#g': pfx + 'hi-spaced'
                };
                if (hiCls[rend]) elem.className = hiCls[rend];
            }
        } else if (tag === 'persName') {
            elem = ZBZ.EntityUtils.createEntitySpan(node, 'person', node.getAttribute('ref'), pfx + 'entity', opts.lookupFn);
        } else if (tag === 'orgName') {
            elem = ZBZ.EntityUtils.createEntitySpan(node, 'org', node.getAttribute('ref'), pfx + 'entity', opts.lookupFn);
        } else if (tag === 'placeName') {
            elem = ZBZ.EntityUtils.createEntitySpan(node, 'place', node.getAttribute('ref'), pfx + 'entity', opts.lookupFn);
        } else if (tag === 'bibl') {
            elem = ZBZ.EntityUtils.createEntitySpan(node, 'work', node.getAttribute('ref') || node.getAttribute('corresp'), pfx + 'entity', opts.lookupFn);
        } else if (tag === 'lb') {
            container.appendChild(document.createElement('br'));
            return;
        } else if (tag === 'foreign') {
            elem = document.createElement('span');
            const lang = node.getAttribute('xml:lang') || '?';
            elem.className = pfx + 'foreign';
            elem.setAttribute('data-lang', lang);
            elem.title = 'Sprache: ' + lang;
            // Edition adds a lang label; infra keeps it simple
            if (pfx === 'ed-tei-') {
                const langLbl = document.createElement('span');
                langLbl.className = 'ed-lang-label';
                langLbl.textContent = lang.toUpperCase();
                elem.appendChild(langLbl);
            }
        } else if (tag === 'sp') {
            elem = document.createElement('div');
            elem.className = pfx + 'sp';
        } else if (tag === 'speaker') {
            elem = document.createElement('span');
            elem.className = pfx + 'speaker';
        } else {
            // Unknown elements: render children transparently
            renderChildren(node, container, opts);
            return;
        }

        if (elem) {
            renderChildren(node, elem, opts);
            container.appendChild(elem);
        }
    }

    function renderChildren(node, container, opts) {
        for (let i = 0; i < node.childNodes.length; i++) {
            renderNode(node.childNodes[i], container, opts);
        }
    }

    /**
     * Render a full TEI XML document body into a container.
     * @param {Document} xmlDoc - parsed XML document
     * @param {HTMLElement} container - target DOM container
     * @param {Object} opts - { cssPrefix, lookupFn }
     */
    function render(xmlDoc, container, opts) {
        const body = xmlDoc.querySelector('body');
        if (!body) {
            container.innerHTML = '<div class="' + (opts.cssPrefix || '') + 'empty-state">Kein &lt;body&gt; im TEI</div>';
            return;
        }
        renderNode(body, container, opts);
    }

    ZBZ.TeiRender = {
        render: render,
        renderNode: renderNode
    };

    ZBZ.log('TeiRender', 'zbz-tei-render.js ready');
})();
