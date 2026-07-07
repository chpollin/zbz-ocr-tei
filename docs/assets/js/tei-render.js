/**
 * tei-render.js — TEI-XML → DOM
 *
 * Renders a TEI-XML document as readable text into a container element.
 * Uses the .tei__* CSS classes from viewer.css.
 *
 * Namespace: ZBZ.TeiRender
 */
(function () {
    'use strict';

    const HI_MAP = {
        '#b': 'tei__hi--b', '#i': 'tei__hi--i', '#u': 'tei__hi--u',
        '#g': 'tei__hi--g', '#k': 'tei__hi--k',
        '#sup': 'tei__hi--sup', '#sub': 'tei__hi--sub'
    };

    /**
     * Recursively render a TEI-XML element.
     * @param {Node} node
     * @param {HTMLElement} target
     */
    function renderNode(node, target) {
        if (node.nodeType === Node.TEXT_NODE) {
            const t = node.textContent;
            if (t.trim() || /^\s+$/.test(t)) target.appendChild(document.createTextNode(t));
            return;
        }
        if (node.nodeType !== Node.ELEMENT_NODE) return;

        const tag = node.tagName;
        let el;

        switch (tag) {
            case 'head':
                el = ZBZ.el('div', { cls: 'tei__head' });
                renderChildren(node, el);
                target.appendChild(el);
                break;

            case 'p':
                el = ZBZ.el('p', { cls: 'tei__p' });
                renderChildren(node, el);
                target.appendChild(el);
                break;

            case 'pb': {
                const n = node.getAttribute('n') || '?';
                target.appendChild(ZBZ.el('div', { cls: 'tei__pb', text: n }));
                break;
            }

            case 'lb':
                target.appendChild(document.createElement('br'));
                break;

            case 'hi': {
                const rend = node.getAttribute('rendition') || '';
                const cls = HI_MAP[rend] || '';
                el = ZBZ.el('span', { cls: cls || 'tei__hi' });
                renderChildren(node, el);
                target.appendChild(el);
                break;
            }

            case 'foreign': {
                el = ZBZ.el('span', { cls: 'tei__foreign', attrs: { lang: node.getAttribute('xml:lang') || '' } });
                renderChildren(node, el);
                target.appendChild(el);
                break;
            }

            case 'note': {
                el = ZBZ.el('span', { cls: 'tei__note' });
                renderChildren(node, el);
                target.appendChild(el);
                break;
            }

            case 'sp': {
                el = ZBZ.el('div', { cls: 'tei__sp' });
                renderChildren(node, el);
                target.appendChild(el);
                break;
            }

            case 'speaker': {
                el = ZBZ.el('span', { cls: 'tei__speaker' });
                renderChildren(node, el);
                target.appendChild(el);
                el.appendChild(document.createTextNode(' '));
                break;
            }

            case 'unclear': {
                el = ZBZ.el('span', { cls: 'tei__unclear', attrs: { title: 'unclear' + (node.getAttribute('cert') ? ' (' + node.getAttribute('cert') + ')' : '') } });
                renderChildren(node, el);
                target.appendChild(el);
                break;
            }

            case 'choice': {
                const corr = node.querySelector('corr');
                if (corr) renderChildren(corr, target);
                else renderChildren(node, target);
                break;
            }

            case 'space':
                target.appendChild(document.createTextNode(' '));
                break;

            case 'figure':
            case 'graphic':
                // Images are not embedded in the viewer.
                break;

            case 'teiHeader':
            case 'facsimile':
                // Metadata/facsimile block skipped.
                break;

            default:
                // Fallback: render children directly.
                renderChildren(node, target);
        }
    }

    function renderChildren(node, target) {
        for (let i = 0; i < node.childNodes.length; i++) {
            renderNode(node.childNodes[i], target);
        }
    }

    /**
     * Main function: render TEI-XML as a string or Document into a container.
     * @param {string|Document} xml
     * @param {HTMLElement} container
     */
    function render(xml, container) {
        container.innerHTML = '';
        const doc = (typeof xml === 'string') ? ZBZ.parseXml(xml) : xml;
        if (!doc) {
            container.appendChild(ZBZ.el('div', { cls: 'empty', text: 'TEI could not be parsed.' }));
            return;
        }
        const body = doc.querySelector('text > body') || doc.querySelector('body') || doc.documentElement;
        const wrap = ZBZ.el('div', { cls: 'tei' });
        renderChildren(body, wrap);
        container.appendChild(wrap);
    }

    /**
     * Write XML source with syntax highlighting into the container.
     */
    function renderXml(xml, container) {
        container.innerHTML = '';
        const pre = ZBZ.el('pre', { cls: 'xml-view', html: ZBZ.highlightXml(xml || '') });
        container.appendChild(pre);
    }

    ZBZ.TeiRender = { render, renderXml };
    ZBZ.log('TeiRender', 'ready');
})();
