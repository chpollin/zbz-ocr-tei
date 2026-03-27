/**
 * ZBZ Edition – Reader Module (Rewrite)
 * Faksimile viewer (pan/zoom/rotate) + TEI text panel.
 * Namespace: ZBZ.EditionReader (ES6+, IIFE)
 */
(function () {
    'use strict';

    var E = ZBZ.Edition;
    var T = ZBZ.EditionTei;

    var state = {
        docId: null,
        page: 1,
        totalPages: 0,
        zoom: 100,
        rotation: 0,
        xmlMode: false,
        editMode: false,
        docMeta: null,
        panX: 0, panY: 0,
        isPanning: false,
        panStartX: 0, panStartY: 0,
        panStartPanX: 0, panStartPanY: 0
    };

    function init() {
        state.docId = E.sanitizeDocId(E.getParam('doc'));
        state.page = parseInt(E.getParam('page'), 10) || 1;

        if (!state.docId) {
            E.$('.ed-reader').innerHTML = '<div class="ed-empty-state">Kein Dokument angegeben. <a href="catalog.html">Zum Katalog</a></div>';
            return;
        }

        Promise.all([E.loadCatalog(), E.loadEntityIndex()]).then(function (results) {
            var catalog = results[0];
            if (!catalog) return;

            var docs = catalog.documents || [];
            for (var i = 0; i < docs.length; i++) {
                if (docs[i].id === state.docId) { state.docMeta = docs[i]; break; }
            }

            if (!state.docMeta) {
                E.$('.ed-reader').innerHTML = '<div class="ed-empty-state">Dokument ' + E.esc(state.docId) + ' nicht gefunden. <a href="catalog.html">Zum Katalog</a></div>';
                return;
            }

            state.totalPages = state.docMeta.page_count || 1;
            if (state.page > state.totalPages) state.page = 1;

            renderHeader();
            loadRevisionDesc();
            renderPageThumbs();
            bindControls();
            initDivider();
            initViewer();
            initEditor();
            showPage(state.page);

            ZBZ.log('Reader', 'Doc ' + state.docId + ' | S.' + state.page + '/' + state.totalPages);
        });
    }

    // --- Revision History ---
    function loadRevisionDesc() {
        E.fetchFullTei(state.docId).then(function (xml) {
            var changes = E.extractRevisionDesc(xml);
            if (!changes || !changes.length) return;
            var panel = E.$('#revision-panel');
            var timeline = E.$('#revision-timeline');
            var toggle = E.$('#revision-toggle');
            if (!panel || !timeline) return;
            panel.style.display = '';
            var html = changes.map(function (ch) {
                var statusAttr = ch.status ? ' data-status="' + E.esc(ch.status) + '"' : '';
                return '<div class="ed-revision-entry">' +
                    '<span class="ed-revision-date">' + E.esc(ch.when) + '</span>' +
                    '<span class="ed-revision-who">' + E.esc(ch.who) + '</span>' +
                    (ch.status ? '<span class="ed-revision-status"' + statusAttr + '>' + E.esc(ch.status) + '</span>' : '') +
                    '<span class="ed-revision-text">' + E.esc(ch.text) + '</span>' +
                    '</div>';
            }).join('');
            timeline.innerHTML = html;
            if (toggle) {
                toggle.addEventListener('click', function () {
                    var expanded = panel.classList.toggle('open');
                    toggle.setAttribute('aria-expanded', expanded);
                });
            }
        });
    }

    // --- Editor integration ---
    function initEditor() {
        if (typeof ZBZ.EditionEditor === 'undefined') return;
        var Ed = ZBZ.EditionEditor;
        Ed.checkServer(function (available) {
            var toolbar = E.$('#edit-toolbar');
            if (toolbar && available) toolbar.classList.remove('ed-hidden');
        });
    }

    function toggleEditMode() {
        var Ed = ZBZ.EditionEditor;
        state.editMode = !state.editMode;
        Ed.state.active = state.editMode;
        var reader = E.$('.ed-reader');
        var editBtn = E.$('#edit-toggle');
        if (reader) reader.classList.toggle('ed-edit-mode', state.editMode);
        if (editBtn) editBtn.classList.toggle('active', state.editMode);
        if (!state.editMode) Ed.clearDirty();
        showPage(state.page);
    }

    // --- Header ---
    function renderHeader() {
        var m = state.docMeta;
        var title = m.title || 'Dokument ' + m.id;
        document.title = title + ' \u2013 Nachlass Jeanne Hersch';

        var titleEl = E.$('.ed-reader-title');
        if (titleEl) titleEl.textContent = title;

        var metaEl = E.$('#reader-meta');
        if (metaEl) {
            var html = '';
            if (m.author) html += '<span>' + E.esc(m.author) + '</span>';
            if (m.date) html += '<span>' + E.esc(m.date) + '</span>';
            if (m.type && m.type !== '-') html += '<span class="ed-badge ed-badge-type">' + E.esc(E.TYPE_LABELS[m.type] || m.type) + '</span>';
            if (m.lang) html += '<span class="ed-badge ed-badge-lang">' + E.esc(m.lang) + '</span>';
            if (m.page_count) html += '<span>' + m.page_count + ' S.</span>';
            if (m.screening) html += E.screeningBadgeHtml(m.screening);
            if (m.curation && m.curation !== 'uncurated') html += E.curationBadgeHtml(m.curation);
            metaEl.innerHTML = html;
        }
    }

    // --- Page Thumbnails ---
    function renderPageThumbs() {
        var container = E.$('#page-thumbs');
        if (!container || state.totalPages <= 1) return;
        var html = '';
        for (var i = 1; i <= state.totalPages; i++) {
            html += '<button class="' + (i === state.page ? 'active' : '') + '" data-page="' + i + '" title="Seite ' + i + '">' + i + '</button>';
        }
        container.innerHTML = html;
        container.addEventListener('click', function (e) {
            var btn = e.target.closest('button');
            if (!btn) return;
            var pg = parseInt(btn.getAttribute('data-page'), 10);
            if (pg && pg !== state.page) showPage(pg);
        });
    }

    function updatePageThumbs() {
        E.$$('#page-thumbs button').forEach(function (btn) {
            btn.classList.toggle('active', parseInt(btn.getAttribute('data-page'), 10) === state.page);
        });
    }

    // --- Controls ---
    function bindControls() {
        var prevBtn = E.$('#page-prev'), nextBtn = E.$('#page-next');
        if (prevBtn) prevBtn.addEventListener('click', function () { changePage(-1); });
        if (nextBtn) nextBtn.addEventListener('click', function () { changePage(1); });

        // Text/XML toggle
        var textTab = E.$('#view-text'), xmlTab = E.$('#view-xml');
        if (textTab) textTab.addEventListener('click', function () {
            if (!state.xmlMode) return;
            state.xmlMode = false;
            textTab.classList.add('active'); textTab.setAttribute('aria-pressed', 'true');
            if (xmlTab) { xmlTab.classList.remove('active'); xmlTab.setAttribute('aria-pressed', 'false'); }
            showPage(state.page);
        });
        if (xmlTab) xmlTab.addEventListener('click', function () {
            if (state.xmlMode) return;
            state.xmlMode = true;
            xmlTab.classList.add('active'); xmlTab.setAttribute('aria-pressed', 'true');
            if (textTab) { textTab.classList.remove('active'); textTab.setAttribute('aria-pressed', 'false'); }
            showPage(state.page);
        });

        // Zoom & Rotate
        var zoomIn = E.$('#zoom-in'), zoomOut = E.$('#zoom-out');
        var zoomReset = E.$('#zoom-reset'), zoomFit = E.$('#zoom-fit');
        var rotateBtn = E.$('#rotate-btn');
        if (zoomIn) zoomIn.addEventListener('click', function () { setZoom(state.zoom + 25); });
        if (zoomOut) zoomOut.addEventListener('click', function () { setZoom(state.zoom - 25); });
        if (zoomReset) zoomReset.addEventListener('click', function () { setZoom(100); resetPan(); });
        if (zoomFit) zoomFit.addEventListener('click', function () { fitToWidth(); });
        if (rotateBtn) rotateBtn.addEventListener('click', function () { rotate(); });

        // Edit
        var editBtn = E.$('#edit-toggle');
        if (editBtn) editBtn.addEventListener('click', function () { toggleEditMode(); });
        var saveBtn = E.$('#save-btn');
        if (saveBtn) saveBtn.addEventListener('click', function () {
            if (typeof ZBZ.EditionEditor !== 'undefined') {
                ZBZ.EditionEditor.savePageXml(state.docId, state.page, E.$('.ed-text-content'), state.xmlMode);
            }
        });
        var validateBtn = E.$('#validate-btn');
        if (validateBtn) validateBtn.addEventListener('click', function () { validateCurrentPage(); });

        // Keyboard
        document.addEventListener('keydown', function (e) {
            if ((e.ctrlKey || e.metaKey) && e.key === 's' && state.editMode) {
                e.preventDefault();
                if (typeof ZBZ.EditionEditor !== 'undefined' && ZBZ.EditionEditor.state.dirty) {
                    ZBZ.EditionEditor.savePageXml(state.docId, state.page, E.$('.ed-text-content'), state.xmlMode);
                }
                return;
            }
            if ((e.ctrlKey || e.metaKey) && state.editMode && e.target.contentEditable === 'true') {
                var fmt = null;
                if (e.key === 'b') fmt = 'b'; else if (e.key === 'i') fmt = 'i'; else if (e.key === 'u') fmt = 'u';
                if (fmt && typeof ZBZ.EditionEditor !== 'undefined') {
                    e.preventDefault(); ZBZ.EditionEditor.toggleInlineFormat(fmt); return;
                }
            }
            if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA' || e.target.contentEditable === 'true') return;
            if (e.key === 'ArrowLeft') { e.preventDefault(); changePage(-1); }
            else if (e.key === 'ArrowRight') { e.preventDefault(); changePage(1); }
        });

        window.addEventListener('beforeunload', function (e) {
            if (typeof ZBZ.EditionEditor !== 'undefined' && ZBZ.EditionEditor.state.dirty) {
                e.preventDefault(); e.returnValue = '';
            }
        });
    }

    // --- Page Navigation ---
    function changePage(delta) {
        var p = state.page + delta;
        if (p < 1 || p > state.totalPages) return;
        showPage(p);
    }

    function showPage(page) {
        state.page = page;
        E.setParams({ doc: state.docId, page: page });
        updatePageIndicator();
        updatePageThumbs();
        state.rotation = 0;
        resetPan();
        loadFaksimile();
        loadTei();
    }

    function updatePageIndicator() {
        var ind = E.$('#page-indicator');
        if (ind) ind.textContent = state.page + ' / ' + state.totalPages;
        var prev = E.$('#page-prev'), next = E.$('#page-next');
        if (prev) prev.disabled = state.page <= 1;
        if (next) next.disabled = state.page >= state.totalPages;
    }

    // --- Faksimile Viewer ---
    function initViewer() {
        var vp = E.$('#faks-viewport');
        if (!vp) return;

        vp.addEventListener('wheel', function (e) {
            e.preventDefault();
            setZoom(state.zoom + (e.deltaY > 0 ? -15 : 15));
        }, { passive: false });

        vp.addEventListener('mousedown', function (e) {
            if (e.button !== 0) return;
            if (!vp.querySelector('img')) return;
            e.preventDefault();
            state.isPanning = true;
            state.panStartX = e.clientX; state.panStartY = e.clientY;
            state.panStartPanX = state.panX; state.panStartPanY = state.panY;
        });
        document.addEventListener('mousemove', function (e) {
            if (!state.isPanning) return;
            state.panX = state.panStartPanX + (e.clientX - state.panStartX);
            state.panY = state.panStartPanY + (e.clientY - state.panStartY);
            applyTransform();
        });
        document.addEventListener('mouseup', function () { state.isPanning = false; });

        vp.addEventListener('dblclick', function () {
            if (state.zoom >= 200) { setZoom(100); resetPan(); } else { setZoom(200); }
        });
    }

    function applyTransform() {
        var img = E.$('#faks-viewport img');
        if (!img) return;
        img.style.transform = 'translate(' + state.panX + 'px,' + state.panY + 'px) rotate(' + state.rotation + 'deg)';
    }

    function resetPan() { state.panX = 0; state.panY = 0; applyTransform(); }

    function rotate() {
        state.rotation = (state.rotation + 90) % 360;
        applyTransform();
    }

    function fitToWidth() {
        var vp = E.$('#faks-viewport');
        var img = vp ? vp.querySelector('img') : null;
        if (!img || !img.naturalWidth) return;
        var fit = Math.round(((vp.clientWidth - 32) / img.naturalWidth) * 100);
        setZoom(Math.max(25, Math.min(300, fit)));
        resetPan();
    }

    function setZoom(z) {
        state.zoom = Math.max(25, Math.min(300, z));
        var img = E.$('#faks-viewport img');
        if (img) img.style.width = state.zoom + '%';
        var label = E.$('#zoom-label');
        if (label) label.textContent = state.zoom + '%';
    }

    // --- Load Faksimile ---
    function loadFaksimile() {
        var vp = E.$('#faks-viewport');
        if (!vp) return;
        var src = E.imagePath(state.docId, state.page);
        var alt = E.esc(state.docMeta.title || '') + ' \u2013 Seite ' + state.page;
        vp.innerHTML = '<img src="' + src + '" alt="' + alt + '" style="width:' + state.zoom + '%;opacity:0;transition:opacity 0.3s ease">';
        var img = vp.querySelector('img');
        if (img) {
            img.addEventListener('load', function () { img.style.opacity = '1'; applyTransform(); });
            img.addEventListener('error', function () {
                vp.innerHTML = '<div class="ed-empty-state">Bild nicht verfuegbar<br><small class="ed-text-muted">Nur Demo-Dokumente haben Bilder auf GitHub Pages</small></div>';
            });
        }
    }

    // --- Load TEI ---
    function loadTei() {
        var container = E.$('.ed-text-content');
        if (!container) return;
        container.innerHTML = '<div class="ed-skeleton ed-skeleton-block" style="height:400px"></div>';

        var Ed = typeof ZBZ.EditionEditor !== 'undefined' ? ZBZ.EditionEditor : null;
        var promise;
        if (Ed && Ed.state.serverAvailable) {
            promise = Ed.fetchTeiFromServer(state.docId, state.page).then(function (data) {
                if (data && data.xml) return data.xml;
                return E.fetchTei(state.docId, state.page);
            });
        } else {
            promise = E.fetchTei(state.docId, state.page);
        }

        promise.then(function (xml) {
            if (state.editMode && Ed) {
                if (state.xmlMode) Ed.renderXmlEditable(xml, container);
                else Ed.renderEditable(xml, container);
                Ed.clearDirty();
            } else if (state.xmlMode) {
                T.renderXml(xml, container);
            } else {
                T.render(xml, container);
            }
        });
    }

    // --- Validation ---
    function validateCurrentPage() {
        var Ed = typeof ZBZ.EditionEditor !== 'undefined' ? ZBZ.EditionEditor : null;
        if (!Ed || !Ed.state.serverAvailable) { Ed.showToast('Server nicht erreichbar', 'error'); return; }
        var container = E.$('.ed-text-content');
        var xml;
        if (state.xmlMode) { var ta = container.querySelector('.ed-xml-editor'); xml = ta ? ta.value : null; }
        else { xml = Ed.serializeToXml(container); }
        if (!xml) { Ed.showToast('Kein XML zum Validieren', 'error'); return; }
        Ed.showToast('Validiere...', 'info');
        var fullXml = xml;
        if (xml.indexOf('<TEI') === -1) {
            fullXml = '<?xml version="1.0" encoding="UTF-8"?>\n<TEI xmlns="http://www.tei-c.org/ns/1.0">\n' +
                '<teiHeader><fileDesc><titleStmt><title>V</title></titleStmt><publicationStmt><p>V</p></publicationStmt><sourceDesc><p>V</p></sourceDesc></fileDesc></teiHeader>\n' +
                '<text><body>' + xml + '</body></text>\n</TEI>';
        }
        fetch(window.location.origin + '/api/tei/' + state.docId + '/validate-page', {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ xml: fullXml })
        }).then(function (r) { return r.json(); }).then(function (result) {
            if (result.valid) Ed.showToast('TEI ist valide (RelaxNG)', 'success');
            else Ed.showToast((result.errors ? result.errors.length : 0) + ' Validierungsfehler', 'error');
        }).catch(function (err) { Ed.showToast('Fehler: ' + (err.message || ''), 'error'); });
    }

    // --- Divider ---
    function initDivider() {
        var divider = E.$('.ed-panel-divider'), panels = E.$('.ed-reader-panels');
        if (!divider || !panels) return;
        var left = E.$('#faks-panel'), right = E.$('.ed-panel-text');
        if (!left || !right) return;
        var dragging = false;
        divider.addEventListener('mousedown', function (e) {
            e.preventDefault(); dragging = true;
            divider.classList.add('dragging');
            document.body.style.cursor = 'col-resize'; document.body.style.userSelect = 'none';
        });
        document.addEventListener('mousemove', function (e) {
            if (!dragging) return;
            var rect = panels.getBoundingClientRect();
            var pct = Math.max(15, Math.min(85, ((e.clientX - rect.left) / rect.width) * 100));
            left.style.flex = '0 0 ' + pct + '%'; right.style.flex = '0 0 ' + (100 - pct) + '%';
        });
        function stop() {
            if (!dragging) return; dragging = false;
            divider.classList.remove('dragging');
            document.body.style.cursor = ''; document.body.style.userSelect = '';
        }
        document.addEventListener('mouseup', stop);
        window.addEventListener('blur', stop);
    }

    // --- Init ---
    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
    else init();

    ZBZ.EditionReader = { showPage: showPage, setZoom: setZoom };
})();
