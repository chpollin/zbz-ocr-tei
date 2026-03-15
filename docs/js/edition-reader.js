/**
 * ZBZ Edition – Reader Module
 * Faksimile + TEI side-by-side reader with professional image viewer,
 * page navigation, zoom, pan, rotation, text/xml toggle.
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
        splitRatio: 50,
        // Pan state
        panX: 0,
        panY: 0,
        isPanning: false,
        panStartX: 0,
        panStartY: 0,
        panStartPanX: 0,
        panStartPanY: 0
    };

    // --- Init ---
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
                if (docs[i].id === state.docId) {
                    state.docMeta = docs[i];
                    break;
                }
            }

            if (!state.docMeta) {
                E.$('.ed-reader').innerHTML = '<div class="ed-empty-state">Dokument ' + E.esc(state.docId) + ' nicht gefunden. <a href="catalog.html">Zum Katalog</a></div>';
                return;
            }

            state.totalPages = state.docMeta.page_count || 1;
            if (state.page > state.totalPages) state.page = 1;

            renderHeader();
            bindToolbar();
            initDivider();
            initFaksimileViewer();
            initEditor();
            showPage(state.page);
            loadRevisionDesc();

            ZBZ.log('Reader', 'Doc ' + state.docId + ' | S.' + state.page + '/' + state.totalPages);
        });
    }

    // --- Editor Init ---
    function initEditor() {
        if (typeof ZBZ.EditionEditor === 'undefined') return;
        var Ed = ZBZ.EditionEditor;
        Ed.checkServer(function (available) {
            var editBtn = E.$('#edit-toggle');
            if (editBtn && available) {
                editBtn.classList.remove('ed-hidden');
            }
            // Show curation hint when no server
            var hint = E.$('#curation-hint');
            if (hint && !available) {
                hint.classList.remove('ed-hidden');
            }
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

        if (!state.editMode) {
            Ed.clearDirty();
        }

        showPage(state.page);
    }

    // --- Header ---
    function renderHeader() {
        var m = state.docMeta;
        var title = m.title || 'Dokument ' + m.id;

        document.title = title + ' \u2013 Nachlass Jeanne Hersch';

        var headerEl = E.$('.ed-reader-title');
        if (headerEl) {
            headerEl.innerHTML = '<a href="catalog.html" class="ed-back-link" title="Zurueck zum Katalog">\u2190</a>' + E.esc(title);
        }

        var metaEl = E.$('.ed-reader-meta');
        if (metaEl) {
            var parts = [];
            if (m.author) parts.push(E.esc(m.author));
            if (m.date) parts.push(E.esc(m.date));
            if (m.type && m.type !== '-') parts.push('<span class="ed-badge ed-badge-type">' + E.esc(E.TYPE_LABELS[m.type] || m.type) + '</span>');
            if (m.lang) parts.push('<span class="ed-badge ed-badge-lang">' + E.esc(m.lang) + '</span>');
            if (m.page_count) parts.push(m.page_count + ' Seiten');
            if (m.screening) parts.push(E.screeningBadgeHtml(m.screening));
            if (m.curation && m.curation !== 'uncurated') parts.push(E.curationBadgeHtml(m.curation));
            metaEl.innerHTML = parts.join(' \u00B7 ');
        }
    }

    // --- Revision History ---
    function loadRevisionDesc() {
        E.fetchFullTei(state.docId).then(function (xml) {
            if (!xml) return;
            var changes = E.extractRevisionDesc(xml);
            if (changes && changes.length) {
                renderRevisionPanel(changes);
            }
        });
    }

    function renderRevisionPanel(changes) {
        var toolbar = E.$('.ed-reader-toolbar');
        if (!toolbar) return;

        var existing = E.$('.ed-revision-panel');
        if (existing) existing.remove();

        var panel = document.createElement('div');
        panel.className = 'ed-revision-panel';

        var lastChange = changes[changes.length - 1];
        var statusText = lastChange.status ? ' \u2014 ' + lastChange.status : '';

        panel.innerHTML =
            '<button class="ed-revision-toggle" aria-expanded="false">' +
            '<span>Revisionsgeschichte (' + changes.length + ')' + E.esc(statusText) + '</span>' +
            '<span class="ed-chevron">&#9660;</span></button>' +
            '<div class="ed-revision-timeline"></div>';

        var timeline = panel.querySelector('.ed-revision-timeline');
        changes.forEach(function (ch) {
            var entry = document.createElement('div');
            entry.className = 'ed-revision-entry';
            var statusHtml = '';
            if (ch.status) {
                statusHtml = ' <span class="ed-revision-status" data-status="' + E.esc(ch.status) + '">' + E.esc(ch.status) + '</span>';
            }
            entry.innerHTML =
                '<span class="ed-revision-date">' + E.esc(ch.when) + '</span>' +
                '<span class="ed-revision-who">' + E.esc(ch.who) + '</span>' +
                '<span class="ed-revision-text">' + E.esc(ch.text) + statusHtml + '</span>';
            timeline.appendChild(entry);
        });

        var toggle = panel.querySelector('.ed-revision-toggle');
        toggle.addEventListener('click', function () {
            var open = panel.classList.toggle('open');
            toggle.setAttribute('aria-expanded', String(open));
        });

        if (lastChange.status === 'NEEDS_REVIEW') {
            panel.classList.add('open');
            toggle.setAttribute('aria-expanded', 'true');
        }

        toolbar.after(panel);
        renderPageThumbs();
    }

    function renderPageThumbs() {
        if (!state.totalPages || state.totalPages <= 1) return;
        var toolbar = E.$('.ed-reader-toolbar');
        if (!toolbar) return;

        var existing = E.$('.ed-page-thumbs');
        if (existing) existing.remove();

        var strip = document.createElement('div');
        strip.className = 'ed-page-thumbs';
        for (var i = 1; i <= state.totalPages; i++) {
            var thumb = document.createElement('button');
            thumb.className = 'ed-page-thumb' + (i === state.page ? ' active' : '');
            thumb.textContent = i;
            thumb.title = 'Seite ' + i;
            (function (pg) {
                thumb.addEventListener('click', function () { showPage(pg); });
            })(i);
            strip.appendChild(thumb);
        }

        var revPanel = E.$('.ed-revision-panel');
        if (revPanel) {
            revPanel.after(strip);
        } else {
            toolbar.after(strip);
        }
    }

    // --- Toolbar ---
    function bindToolbar() {
        var prevBtn = E.$('#page-prev');
        var nextBtn = E.$('#page-next');

        if (prevBtn) prevBtn.addEventListener('click', function () { changePage(-1); });
        if (nextBtn) nextBtn.addEventListener('click', function () { changePage(1); });

        // View toggle: Text / XML (inside text panel)
        var textTab = E.$('#view-text');
        var xmlTab = E.$('#view-xml');
        if (textTab) {
            textTab.addEventListener('click', function () {
                if (!state.xmlMode) return;
                state.xmlMode = false;
                textTab.classList.add('active');
                if (xmlTab) xmlTab.classList.remove('active');
                showPage(state.page);
            });
        }
        if (xmlTab) {
            xmlTab.addEventListener('click', function () {
                if (state.xmlMode) return;
                state.xmlMode = true;
                xmlTab.classList.add('active');
                if (textTab) textTab.classList.remove('active');
                showPage(state.page);
            });
        }

        // Zoom
        var zoomInBtn = E.$('#zoom-in');
        var zoomOutBtn = E.$('#zoom-out');
        var zoomReset = E.$('#zoom-reset');
        var zoomFit = E.$('#zoom-fit');
        var rotateBtn = E.$('#rotate-btn');

        if (zoomInBtn) zoomInBtn.addEventListener('click', function () { setZoom(state.zoom + 25); });
        if (zoomOutBtn) zoomOutBtn.addEventListener('click', function () { setZoom(state.zoom - 25); });
        if (zoomReset) zoomReset.addEventListener('click', function () { setZoom(100); resetPan(); });
        if (zoomFit) zoomFit.addEventListener('click', function () { fitToWidth(); });
        if (rotateBtn) rotateBtn.addEventListener('click', function () { rotate(); });

        // Edit toggle
        var editBtn = E.$('#edit-toggle');
        if (editBtn) {
            editBtn.addEventListener('click', function () { toggleEditMode(); });
        }

        // Save button
        var saveBtn = E.$('#save-btn');
        if (saveBtn) {
            saveBtn.addEventListener('click', function () {
                if (typeof ZBZ.EditionEditor !== 'undefined') {
                    var container = E.$('.ed-text-content');
                    ZBZ.EditionEditor.savePageXml(state.docId, state.page, container, state.xmlMode);
                }
            });
        }

        // Validate button
        var validateBtn = E.$('#validate-btn');
        if (validateBtn) {
            validateBtn.addEventListener('click', function () { validateCurrentPage(); });
        }

        // Keyboard navigation
        document.addEventListener('keydown', function (e) {
            if ((e.ctrlKey || e.metaKey) && e.key === 's' && state.editMode) {
                e.preventDefault();
                if (typeof ZBZ.EditionEditor !== 'undefined' && ZBZ.EditionEditor.state.dirty) {
                    var container = E.$('.ed-text-content');
                    ZBZ.EditionEditor.savePageXml(state.docId, state.page, container, state.xmlMode);
                }
                return;
            }
            if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
            if (e.target.contentEditable === 'true') return;
            if (e.key === 'ArrowLeft') { e.preventDefault(); changePage(-1); }
            else if (e.key === 'ArrowRight') { e.preventDefault(); changePage(1); }
        });

        window.addEventListener('beforeunload', function (e) {
            if (typeof ZBZ.EditionEditor !== 'undefined' && ZBZ.EditionEditor.state.dirty) {
                e.preventDefault();
                e.returnValue = '';
            }
        });
    }

    // --- Page Navigation ---
    function changePage(delta) {
        var newPage = state.page + delta;
        if (newPage < 1 || newPage > state.totalPages) return;
        showPage(newPage);
    }

    function showPage(page) {
        state.page = page;
        E.setParams({ doc: state.docId, page: page });
        updatePageIndicator();
        updatePageThumbs();
        resetPan();
        loadFaksimile();
        loadTei();
    }

    function updatePageThumbs() {
        E.$$('.ed-page-thumb').forEach(function (t) {
            t.classList.toggle('active', parseInt(t.textContent, 10) === state.page);
        });
    }

    function updatePageIndicator() {
        var indicator = E.$('#page-indicator');
        if (indicator) indicator.textContent = state.page + ' / ' + state.totalPages;

        var prevBtn = E.$('#page-prev');
        var nextBtn = E.$('#page-next');
        if (prevBtn) prevBtn.disabled = state.page <= 1;
        if (nextBtn) nextBtn.disabled = state.page >= state.totalPages;
    }

    // --- Faksimile Viewer (Pan + Wheel Zoom + Rotation) ---
    function initFaksimileViewer() {
        var panel = E.$('#faks-panel');
        if (!panel) return;

        // Mouse wheel zoom
        panel.addEventListener('wheel', function (e) {
            e.preventDefault();
            var delta = e.deltaY > 0 ? -15 : 15;
            setZoom(state.zoom + delta);
        }, { passive: false });

        // Pan with mouse drag
        panel.addEventListener('mousedown', function (e) {
            if (e.button !== 0) return;
            var img = panel.querySelector('img');
            if (!img) return;
            e.preventDefault();
            state.isPanning = true;
            state.panStartX = e.clientX;
            state.panStartY = e.clientY;
            state.panStartPanX = state.panX;
            state.panStartPanY = state.panY;
            panel.style.cursor = 'grabbing';
        });

        document.addEventListener('mousemove', function (e) {
            if (!state.isPanning) return;
            state.panX = state.panStartPanX + (e.clientX - state.panStartX);
            state.panY = state.panStartPanY + (e.clientY - state.panStartY);
            applyTransform();
        });

        document.addEventListener('mouseup', function () {
            if (!state.isPanning) return;
            state.isPanning = false;
            var p = E.$('#faks-panel');
            if (p) p.style.cursor = '';
        });

        // Double-click zoom
        panel.addEventListener('dblclick', function () {
            if (state.zoom >= 200) {
                setZoom(100);
                resetPan();
            } else {
                setZoom(200);
            }
        });
    }

    function applyTransform() {
        var img = E.$('#faks-panel img');
        if (!img) return;
        img.style.transform = 'translate(' + state.panX + 'px, ' + state.panY + 'px) rotate(' + state.rotation + 'deg)';
    }

    function resetPan() {
        state.panX = 0;
        state.panY = 0;
        applyTransform();
    }

    function rotate() {
        state.rotation = (state.rotation + 90) % 360;
        applyTransform();
    }

    function fitToWidth() {
        var panel = E.$('#faks-panel');
        var img = panel ? panel.querySelector('img') : null;
        if (!img || !img.naturalWidth) return;
        var panelW = panel.clientWidth - 32; // padding
        var imgW = img.naturalWidth;
        var fitZoom = Math.round((panelW / imgW) * 100);
        setZoom(Math.max(25, Math.min(300, fitZoom)));
        resetPan();
    }

    // --- Faksimile ---
    function loadFaksimile() {
        var panel = E.$('#faks-panel');
        if (!panel) return;

        var src = E.imagePath(state.docId, state.page);
        var title = state.docMeta ? state.docMeta.title || '' : '';
        var alt = E.esc(title) + ' \u2013 Seite ' + state.page;

        panel.innerHTML = '<img src="' + src + '" alt="' + alt + '" style="width:' + state.zoom + '%;opacity:0;transition:opacity 0.3s ease;cursor:grab;transform-origin:center center">';

        var img = panel.querySelector('img');
        if (img) {
            img.addEventListener('load', function () {
                img.style.opacity = '1';
                applyTransform();
            });
            img.addEventListener('error', function () {
                panel.innerHTML = '<div class="ed-empty-state">Bild nicht verfuegbar<br><small class="ed-text-muted">Nur Demo-Dokumente haben Bilder auf GitHub Pages</small></div>';
            });
        }
    }

    // --- TEI ---
    function loadTei() {
        var container = E.$('.ed-text-content');
        if (!container) return;

        container.innerHTML = '<div class="ed-skeleton ed-skeleton-block" style="height:400px"></div>';

        var Ed = typeof ZBZ.EditionEditor !== 'undefined' ? ZBZ.EditionEditor : null;

        var teiPromise;
        if (Ed && Ed.state.serverAvailable) {
            teiPromise = Ed.fetchTeiFromServer(state.docId, state.page)
                .then(function (data) {
                    if (data && data.xml) return data.xml;
                    return E.fetchTei(state.docId, state.page);
                });
        } else {
            teiPromise = E.fetchTei(state.docId, state.page);
        }

        teiPromise.then(function (xml) {
            if (state.editMode && Ed) {
                if (state.xmlMode) {
                    Ed.renderXmlEditable(xml, container);
                } else {
                    Ed.renderEditable(xml, container);
                }
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
        if (!Ed || !Ed.state.serverAvailable) {
            Ed.showToast('Server nicht erreichbar', 'error');
            return;
        }

        var container = E.$('.ed-text-content');
        var xml;
        if (state.xmlMode) {
            var textarea = container.querySelector('.ed-xml-editor');
            xml = textarea ? textarea.value : null;
        } else {
            xml = Ed.serializeToXml(container);
        }

        if (!xml) {
            Ed.showToast('Kein XML zum Validieren', 'error');
            return;
        }

        Ed.showToast('Validiere...', 'info');

        var fullXml = xml;
        if (xml.indexOf('<TEI') === -1) {
            fullXml = '<?xml version="1.0" encoding="UTF-8"?>\n' +
                '<TEI xmlns="http://www.tei-c.org/ns/1.0">\n' +
                '<teiHeader><fileDesc><titleStmt><title>Validation</title></titleStmt>' +
                '<publicationStmt><p>Validation</p></publicationStmt>' +
                '<sourceDesc><p>Validation</p></sourceDesc></fileDesc></teiHeader>\n' +
                '<text><body>' + xml + '</body></text>\n</TEI>';
        }

        fetch(window.location.origin + '/api/tei/' + state.docId + '/validate-page', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ xml: fullXml })
        })
            .then(function (r) { return r.json(); })
            .then(function (result) {
                if (result.valid) {
                    Ed.showToast('TEI ist valide (RelaxNG)', 'success');
                } else {
                    var errCount = result.errors ? result.errors.length : 0;
                    Ed.showToast(errCount + ' Validierungsfehler', 'error');
                }
            })
            .catch(function (err) {
                Ed.showToast('Validierung fehlgeschlagen: ' + (err.detail || err.message || ''), 'error');
            });
    }

    // --- Zoom ---
    function setZoom(z) {
        state.zoom = Math.max(25, Math.min(300, z));
        var img = E.$('#faks-panel img');
        if (img) img.style.width = state.zoom + '%';

        var label = E.$('#zoom-label');
        if (label) label.textContent = state.zoom + '%';
    }

    // --- Draggable Divider ---
    function initDivider() {
        var divider = E.$('.ed-panel-divider');
        var panels = E.$('.ed-reader-panels');
        if (!divider || !panels) return;

        var leftPanel = E.$('#faks-panel');
        var rightPanel = E.$('.ed-panel-text');
        if (!leftPanel || !rightPanel) return;

        var dragging = false;

        divider.addEventListener('mousedown', function (e) {
            e.preventDefault();
            dragging = true;
            divider.classList.add('dragging');
            document.body.style.cursor = 'col-resize';
            document.body.style.userSelect = 'none';
        });

        document.addEventListener('mousemove', function (e) {
            if (!dragging) return;
            var rect = panels.getBoundingClientRect();
            var pct = ((e.clientX - rect.left) / rect.width) * 100;
            pct = Math.max(15, Math.min(85, pct));
            state.splitRatio = pct;
            leftPanel.style.flex = '0 0 ' + pct + '%';
            rightPanel.style.flex = '0 0 ' + (100 - pct) + '%';
        });

        function stopDrag() {
            if (!dragging) return;
            dragging = false;
            divider.classList.remove('dragging');
            document.body.style.cursor = '';
            document.body.style.userSelect = '';
        }

        document.addEventListener('mouseup', stopDrag);
        window.addEventListener('blur', stopDrag);
    }

    // --- Auto-init ---
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    ZBZ.EditionReader = {
        showPage: showPage,
        setZoom: setZoom
    };
})();
