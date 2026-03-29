/**
 * ZBZ Edition Editor — DOM-to-XML Serialization
 * Depends on: editor-api.js (ZBZ.EditionEditor), editor-save.js (markDirty)
 */
(function () {
    'use strict';

    const state = ZBZ.EditionEditor.state;
    const save = ZBZ.EditionEditor._save;

    function _xmlEsc(s) {
        if (!s) return '';
        return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
    }

    function _indent(depth) {
        let s = '';
        for (let i = 0; i < depth; i++) s += '  ';
        return s;
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

    function _serializeNode(node, lines, depth) {
        const indent = _indent(depth);

        if (node.nodeType === 3) {
            const text = node.textContent;
            if (text.trim()) {
                lines.push(_xmlEsc(text));
            }
            return;
        }

        if (node.nodeType !== 1) return;

        const teiTag = node.getAttribute('data-tei-tag');

        if (node.classList && node.classList.contains('ed-tei-entity-tip')) return;
        if (node.classList && node.classList.contains('ed-tei-note-label')) return;

        if (node.tagName === 'BR') {
            lines.push(indent + '<lb/>');
            return;
        }

        if (node.tagName === 'SUP') {
            lines.push(`<hi rendition="#sup">${_innerXml(node)}</hi>`);
            return;
        }
        if (node.tagName === 'SUB') {
            lines.push(`<hi rendition="#sub">${_innerXml(node)}</hi>`);
            return;
        }

        if (!teiTag) {
            _serializeChildren(node, lines, depth);
            return;
        }

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

        const attrs = _buildAttrs(node, teiTag);
        const inner = _innerXml(node);

        if (teiTag === 'head' || teiTag === 'p' || teiTag === 'note' ||
            teiTag === 'sp' || teiTag === 'div') {
            lines.push(`${indent}<${teiTag}${attrs}>${inner}</${teiTag}>`);
            return;
        }

        lines.push(`<${teiTag}${attrs}>${inner}</${teiTag}>`);
    }

    function _serializeChildren(parent, lines, depth) {
        const children = parent.childNodes;
        for (let i = 0; i < children.length; i++) {
            _serializeNode(children[i], lines, depth);
        }
    }

    function serializeToXml(container) {
        const lines = [];
        _serializeChildren(container, lines, 0);
        return lines.join('\n');
    }

    function renderXmlEditable(xml, container) {
        state.currentXml = xml;
        container.innerHTML = '';

        const textarea = document.createElement('textarea');
        textarea.className = 'ed-xml-editor';
        textarea.value = xml || '';
        textarea.spellcheck = false;
        textarea.addEventListener('input', () => {
            save.markDirty();
        });
        container.appendChild(textarea);
    }

    function getXmlFromEditor(container) {
        const textarea = container.querySelector('.ed-xml-editor');
        if (textarea) return textarea.value;
        return null;
    }

    ZBZ.EditionEditor._serialize = { serializeToXml, renderXmlEditable, getXmlFromEditor };
})();
