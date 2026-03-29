/**
 * ZBZ Edition Editor — Block Toolbar (Typ-Wechsel, Split, Merge, Delete, Inline Format)
 * Depends on: editor-save.js (markDirty, showToast)
 */
(function () {
    'use strict';

    const save = ZBZ.EditionEditor._save;

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

        const sel = tb.querySelector('.ed-block-type-select');
        sel.addEventListener('change', () => {
            if (activeBlock) _changeBlockType(activeBlock, sel.value);
        });

        const fmtBtns = Array.prototype.slice.call(tb.querySelectorAll('.ed-block-fmt'));
        fmtBtns.forEach((btn) => {
            btn.addEventListener('mousedown', (e) => { e.preventDefault(); });
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                _toggleInlineFormat(btn.getAttribute('data-fmt'));
            });
        });

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

        const tag = block.getAttribute('data-tei-tag') || 'p';
        const sel = tb.querySelector('.ed-block-type-select');
        sel.value = tag;

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

        const classMap = {
            p: 'ed-tei-p',
            head: 'ed-tei-head',
            note: 'ed-tei-note',
            figure: 'ed-tei-figure'
        };

        if (classMap[oldTag]) block.classList.remove(classMap[oldTag]);
        if (classMap[newTag]) block.classList.add(classMap[newTag]);

        block.setAttribute('data-tei-tag', newTag);

        if (newTag === 'figure') {
            block.contentEditable = 'false';
            block.textContent = '[Abbildung]';
        } else if (oldTag === 'figure') {
            block.contentEditable = 'true';
            if (block.textContent === '[Abbildung]') block.textContent = '';
        }

        if (newTag === 'note' && !block.getAttribute('data-place')) {
            block.setAttribute('data-place', 'foot');
        }

        save.markDirty();
        _showBlockToolbar(block);
    }

    function _splitBlock(block) {
        const sel = window.getSelection();
        if (!sel || sel.rangeCount === 0) {
            save.showToast('Cursor im Block platzieren zum Teilen', 'info');
            return;
        }

        const range = sel.getRangeAt(0);
        if (!block.contains(range.startContainer)) {
            save.showToast('Cursor muss im Block sein', 'info');
            return;
        }

        const afterRange = document.createRange();
        afterRange.setStart(range.endContainer, range.endOffset);
        afterRange.setEnd(block, block.childNodes.length);
        const afterFrag = afterRange.extractContents();

        const newBlock = document.createElement('div');
        const tag = block.getAttribute('data-tei-tag') || 'p';
        newBlock.className = block.className;
        newBlock.contentEditable = 'true';
        newBlock.setAttribute('data-tei-tag', tag);
        if (block.getAttribute('data-facs')) newBlock.setAttribute('data-facs', '');
        newBlock.appendChild(afterFrag);

        block.parentNode.insertBefore(newBlock, block.nextSibling);
        save.markDirty();
    }

    function _mergeBlock(block) {
        const prev = block.previousElementSibling;
        if (!prev || !prev.getAttribute('data-tei-tag')) {
            save.showToast('Kein vorheriger Block zum Zusammenfuegen', 'info');
            return;
        }

        while (block.firstChild) {
            if (block.firstChild.classList &&
                block.firstChild.classList.contains('ed-tei-note-label')) {
                block.removeChild(block.firstChild);
                continue;
            }
            prev.appendChild(block.firstChild);
        }
        block.parentNode.removeChild(block);
        _hideBlockToolbar();
        save.markDirty();
    }

    function _deleteBlock(block) {
        const text = (block.textContent || '').trim();
        const preview = text.length > 40 ? text.substring(0, 40) + '...' : text;
        if (preview && !window.confirm(`Block loeschen?\n\n"${preview}"`)) {
            return;
        }
        block.parentNode.removeChild(block);
        _hideBlockToolbar();
        save.markDirty();
    }

    function _toggleInlineFormat(fmt) {
        const sel = window.getSelection();
        if (!sel || sel.isCollapsed || sel.rangeCount === 0) return;

        const range = sel.getRangeAt(0);
        const text = range.toString().trim();
        if (!text) return;

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
                save.markDirty();
                return;
            }
            parentHi = parentHi.parentNode;
        }

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
        save.markDirty();
    }

    function _initBlockToolbarListeners(container) {
        container.addEventListener('focusin', (e) => {
            const target = e.target;
            if (target.contentEditable === 'true' && target.getAttribute('data-tei-tag')) {
                _showBlockToolbar(target);
            }
        });

        container.addEventListener('focusout', () => {
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

    ZBZ.EditionEditor._blocks = {
        initBlockToolbarListeners: _initBlockToolbarListeners,
        toggleInlineFormat: _toggleInlineFormat
    };
})();
