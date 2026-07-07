/**
 * transcription-editor.js - Text correction (OCR + TEI + XML)
 *
 * Switches the text panel to `contenteditable` and collects changes.
 * - OCR mode: edits the Markdown text directly
 * - TEI mode (rendered): edits the textContent of the rendered blocks and does
 *   not serialize back; use XML mode for structural changes
 * - XML mode: edits the raw TEI-XML
 *
 * Namespace: ZBZ.TranscriptionEditor
 */
(function () {
    'use strict';

    const $ = ZBZ.$;
    const $$ = ZBZ.$$;

    const state = {
        container: null,
        source: null,         // ocr | tei | xml
        onChange: null,
        originalText: null,
        bound: false
    };

    let _onInput;

    /**
     * Attach the editor to a container.
     * @param {HTMLElement} container
     * @param {string} source - 'ocr' | 'tei' | 'xml'
     * @param {Function} onChange - (newContent) => void
     */
    function attach(container, source, onChange) {
        detach(container);
        state.container = container;
        state.source = source;
        state.onChange = onChange || (() => {});

        // Determine edit target (the inner .text / .tei / pre.xml-view)
        const editTarget = pickEditTarget(container, source);
        if (!editTarget) {
            ZBZ.warn('TranscriptionEditor', 'No editable element found for source=' + source);
            return;
        }

        editTarget.setAttribute('contenteditable', 'true');
        editTarget.setAttribute('spellcheck', source === 'xml' ? 'false' : 'true');
        // expose as multiline textbox to screen readers
        editTarget.setAttribute('role', 'textbox');
        editTarget.setAttribute('aria-multiline', 'true');
        editTarget.setAttribute('aria-label', 'Text editor (' + source.toUpperCase() + ')');
        editTarget.style.minHeight = '60vh';

        state.originalText = readContent(editTarget, source);

        _onInput = ZBZ.debounce(() => {
            const newContent = readContent(editTarget, source);
            state.onChange(newContent);
        }, 250);

        editTarget.addEventListener('input', _onInput);
        editTarget._zbzEditTarget = true;

        // Ctrl+Z works natively via contenteditable. Tab inserts spaces (prevents focus loss).
        editTarget.addEventListener('keydown', tabHandler);

        state.bound = true;
        ZBZ.toast('Edit mode: ' + source.toUpperCase(), 'info');
        ZBZ.log('TranscriptionEditor', 'attached (' + source + ')');
    }

    function detach(container) {
        // Drop any pending debounced commit: it would otherwise fire after a
        // source/tab switch and attribute the edit to the wrong stream.
        if (_onInput && _onInput.cancel) _onInput.cancel();
        const c = container || state.container;
        if (!c) return;
        const targets = $$('[contenteditable="true"]', c);
        targets.forEach(t => {
            t.removeAttribute('contenteditable');
            t.removeAttribute('spellcheck');
            t.removeAttribute('role');
            t.removeAttribute('aria-multiline');
            t.removeAttribute('aria-label');
            t.style.minHeight = '';
            if (_onInput) t.removeEventListener('input', _onInput);
            t.removeEventListener('keydown', tabHandler);
            delete t._zbzEditTarget;
        });
        state.container = null;
        state.source = null;
        state.onChange = null;
        state.originalText = null;
        state.bound = false;
    }

    function pickEditTarget(container, source) {
        if (source === 'xml') return $('.xml-view', container);
        if (source === 'tei') return $('.tei', container);
        if (source === 'ocr') return $('.text', container);
        return null;
    }

    function readContent(target, source) {
        if (source === 'xml') {
            // Extract XML code from <pre> (innerText returns plain text with line breaks)
            return target.innerText;
        }
        if (source === 'ocr') {
            return target.innerText;
        }
        // tei: textContent of the whole edition. TEI structure is lost here;
        // signal this in the UI via distinct styling. Use XML mode for structural changes.
        return target.innerText;
    }

    function tabHandler(e) {
        if (e.key !== 'Tab') return;
        e.preventDefault();
        const sel = window.getSelection();
        if (!sel.rangeCount) return;
        const range = sel.getRangeAt(0);
        range.deleteContents();
        range.insertNode(document.createTextNode('  '));
        range.collapse(false);
    }

    ZBZ.TranscriptionEditor = { attach, detach };
    ZBZ.log('TranscriptionEditor', 'ready');
})();
