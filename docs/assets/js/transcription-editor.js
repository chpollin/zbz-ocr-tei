/**
 * transcription-editor.js — Text-Korrektur (OCR + TEI + XML)
 *
 * Schaltet das Text-Panel auf `contenteditable` und sammelt Aenderungen.
 * - OCR-Modus: editiert den Markdown-Text direkt
 * - TEI-Modus (rendered): editiert die textContent der gerenderten Bloecke und
 *   serialisiert nicht zurueck — fuer Strukturaenderungen wird der XML-Modus
 *   empfohlen
 * - XML-Modus: editiert das rohe TEI-XML
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
     * Editor an einem Container befestigen.
     * @param {HTMLElement} container
     * @param {string} source - 'ocr' | 'tei' | 'xml'
     * @param {Function} onChange - (newContent) => void
     */
    function attach(container, source, onChange) {
        detach(container);
        state.container = container;
        state.source = source;
        state.onChange = onChange || (() => {});

        // Editor-Ziel ermitteln (das innere .text / .tei / pre.xml-view)
        const editTarget = pickEditTarget(container, source);
        if (!editTarget) {
            ZBZ.warn('TranscriptionEditor', 'Kein editierbares Element gefunden fuer source=' + source);
            return;
        }

        editTarget.setAttribute('contenteditable', 'true');
        editTarget.setAttribute('spellcheck', source === 'xml' ? 'false' : 'true');
        editTarget.style.minHeight = '60vh';

        state.originalText = readContent(editTarget, source);

        _onInput = ZBZ.debounce(() => {
            const newContent = readContent(editTarget, source);
            state.onChange(newContent);
        }, 250);

        editTarget.addEventListener('input', _onInput);
        editTarget._zbzEditTarget = true;

        // Tastatur-Hinweis: Ctrl+Z funktioniert via contenteditable nativ.
        // Tab-Taste insertet Spaces (verhindert Fokus-Verlust)
        editTarget.addEventListener('keydown', tabHandler);

        state.bound = true;
        ZBZ.toast('Edit-Modus: ' + source.toUpperCase(), 'info');
        ZBZ.log('TranscriptionEditor', 'attached (' + source + ')');
    }

    function detach(container) {
        const c = container || state.container;
        if (!c) return;
        const targets = $$('[contenteditable="true"]', c);
        targets.forEach(t => {
            t.removeAttribute('contenteditable');
            t.removeAttribute('spellcheck');
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
            // XML-Code aus dem <pre> extrahieren (innerText liefert Plain-Text mit Zeilenumbruechen)
            return target.innerText;
        }
        if (source === 'ocr') {
            return target.innerText;
        }
        // tei: textContent der ganzen Edition. Achtung: TEI-Struktur geht hier verloren —
        // Hinweis im UI durch unterschiedliches Styling abdecken; bei tatsaechlichen
        // Strukturaenderungen sollte der XML-Modus genutzt werden.
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
