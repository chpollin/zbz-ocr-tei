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
            case 'ab':
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
                // break="no" marks hyphenation (word continues); a <br> would split the word
                if (node.getAttribute('break') !== 'no') target.appendChild(document.createElement('br'));
                break;

            case 'div': {
                el = ZBZ.el('div', { cls: 'tei__div' });
                const dtype = node.getAttribute('type');
                if (dtype) el.setAttribute('data-type', dtype);
                renderChildren(node, el);
                target.appendChild(el);
                break;
            }

            case 'front':
            case 'back':
                el = ZBZ.el('div', { cls: 'tei__' + tag, attrs: { 'data-type': tag } });
                renderChildren(node, el);
                target.appendChild(el);
                break;

            case 'title': {
                const ttype = node.getAttribute('type');
                el = ZBZ.el('span', { cls: 'tei__title' + (ttype ? ' tei__title--' + ttype : '') });
                renderChildren(node, el);
                target.appendChild(el);
                break;
            }

            case 'persName':
            case 'orgName':
            case 'placeName':
            case 'name': {
                const ref = node.getAttribute('ref') || '';
                // data-ref keeps the identifier in the DOM: the entity mode resolves it
                // against data/entities.json instead of showing the native tooltip.
                const attrs = { title: tag + (ref ? ' · ' + ref : '') };
                if (ref) attrs['data-ref'] = ref;
                el = ZBZ.el('span', { cls: 'tei__entity tei__entity--' + tag.toLowerCase(), attrs });
                renderChildren(node, el);
                target.appendChild(el);
                break;
            }

            case 'bibl': {
                const ref = node.getAttribute('ref') || '';
                el = ZBZ.el('span', {
                    cls: 'tei__bibl',
                    attrs: ref ? { title: 'bibl · ' + ref, 'data-ref': ref } : { title: 'bibl' }
                });
                renderChildren(node, el);
                target.appendChild(el);
                break;
            }

            case 'listBibl':
                el = ZBZ.el('div', { cls: 'tei__listbibl' });
                renderChildren(node, el);
                target.appendChild(el);
                break;

            case 'ref': {
                const href = node.getAttribute('target') || '';
                if (/^https?:\/\//.test(href)) {
                    el = ZBZ.el('a', { cls: 'tei__ref', attrs: { href, target: '_blank', rel: 'noopener', title: href } });
                } else {
                    el = ZBZ.el('span', { cls: 'tei__ref', attrs: href ? { title: href } : {} });
                }
                renderChildren(node, el);
                target.appendChild(el);
                break;
            }

            case 'list':
                el = ZBZ.el('ul', { cls: 'tei__list' });
                renderChildren(node, el);
                target.appendChild(el);
                break;

            case 'item':
                el = ZBZ.el('li', { cls: 'tei__item' });
                renderChildren(node, el);
                target.appendChild(el);
                break;

            case 'table': {
                el = ZBZ.el('table', { cls: 'tei__table' });
                renderChildren(node, el);
                target.appendChild(el);
                break;
            }

            case 'row': {
                el = document.createElement('tr');
                renderChildren(node, el);
                target.appendChild(el);
                break;
            }

            case 'cell': {
                el = document.createElement('td');
                renderChildren(node, el);
                target.appendChild(el);
                break;
            }

            case 'gap': {
                const desc = node.querySelector && node.querySelector('desc');
                target.appendChild(ZBZ.el('span', {
                    cls: 'tei__gap', text: '[…]',
                    attrs: { title: 'gap' + (desc ? ' · ' + desc.textContent : '') }
                }));
                break;
            }

            case 'epigraph':
                el = ZBZ.el('div', { cls: 'tei__epigraph' });
                renderChildren(node, el);
                target.appendChild(el);
                break;

            case 'anchor':
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
                const lang = node.getAttribute('xml:lang') || '';
                el = ZBZ.el('span', { cls: 'tei__foreign', attrs: { lang, title: 'foreign' + (lang ? ' · ' + lang : '') } });
                renderChildren(node, el);
                target.appendChild(el);
                break;
            }

            case 'note': {
                const place = node.getAttribute('place');
                el = ZBZ.el('span', { cls: 'tei__note' + (place ? ' tei__note--' + place : '') });
                const n = node.getAttribute('n');
                if (n) el.appendChild(ZBZ.el('span', { cls: 'tei__note-n', text: n }));
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
                // Show the corrected reading; keep the original visible via tooltip
                const corr = node.querySelector('corr');
                const sic = node.querySelector('sic');
                if (corr) {
                    el = ZBZ.el('span', {
                        cls: 'tei__corr',
                        attrs: sic ? { title: 'sic: ' + sic.textContent } : {}
                    });
                    renderChildren(corr, el);
                    target.appendChild(el);
                } else {
                    renderChildren(node, target);
                }
                break;
            }

            case 'space':
                if (node.getAttribute('dim') === 'vertical') {
                    target.appendChild(ZBZ.el('div', { cls: 'tei__space' }));
                } else {
                    target.appendChild(document.createTextNode(' '));
                }
                break;

            case 'figure': {
                // The image itself is not embedded; show a placeholder + caption
                el = ZBZ.el('div', { cls: 'tei__figure' });
                el.appendChild(ZBZ.el('span', { cls: 'tei__figure-label', text: 'Figure' }));
                renderChildren(node, el);
                target.appendChild(el);
                break;
            }

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
        const wrap = ZBZ.el('div', { cls: 'tei' });
        const text = doc.querySelector('TEI > text') || doc.querySelector('text');
        if (text) {
            // front and back carry content in the reference/curated TEIs; render all three parts
            ['front', 'body', 'back'].forEach(part => {
                const partEl = text.querySelector(':scope > ' + part);
                if (partEl) renderNode(partEl, wrap);
            });
        } else {
            renderChildren(doc.querySelector('body') || doc.documentElement, wrap);
        }
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
