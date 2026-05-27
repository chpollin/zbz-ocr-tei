/**
 * tei-render.js — TEI-XML → DOM
 *
 * Rendert ein TEI-XML-Dokument als lesbaren Text in ein Container-Element.
 * Verwendet die .tei__* CSS-Klassen aus viewer.css.
 *
 * Namespace: ZBZ.TeiRender
 */
(function () {
    'use strict';

    const HI_MAP = {
        '#b': 'tei__hi--b', '#i': 'tei__hi--i', '#u': 'tei__hi--u',
        '#g': 'tei__hi--g', '#k': 'tei__hi--k'
    };

    /**
     * Rekursiv ein TEI-XML-Element rendern.
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
                // Bilder werden im Viewer nicht eingebunden.
                break;

            case 'teiHeader':
            case 'facsimile':
                // Metadaten/Faksimile-Block uebersprungen.
                break;

            default:
                // Fallback: Kinder direkt rendern.
                renderChildren(node, target);
        }
    }

    function renderChildren(node, target) {
        for (let i = 0; i < node.childNodes.length; i++) {
            renderNode(node.childNodes[i], target);
        }
    }

    /**
     * Hauptfunktion: TEI-XML als String oder Doc in einen Container rendern.
     * @param {string|Document} xml
     * @param {HTMLElement} container
     */
    function render(xml, container) {
        container.innerHTML = '';
        const doc = (typeof xml === 'string') ? ZBZ.parseXml(xml) : xml;
        if (!doc) {
            container.appendChild(ZBZ.el('div', { cls: 'empty', text: 'TEI nicht parsbar.' }));
            return;
        }
        const body = doc.querySelector('text > body') || doc.querySelector('body') || doc.documentElement;
        const wrap = ZBZ.el('div', { cls: 'tei' });
        renderChildren(body, wrap);
        container.appendChild(wrap);
    }

    /**
     * XML-Quelltext mit Syntax-Highlighting in den Container schreiben.
     */
    function renderXml(xml, container) {
        container.innerHTML = '';
        const pre = ZBZ.el('pre', { cls: 'xml-view', html: ZBZ.highlightXml(xml || '') });
        container.appendChild(pre);
    }

    ZBZ.TeiRender = { render, renderXml };
    ZBZ.log('TeiRender', 'ready');
})();
