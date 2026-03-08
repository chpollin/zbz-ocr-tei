/**
 * ZBZ Edition – Reader Module
 * Faksimile + TEI side-by-side reader with page navigation,
 * zoom, font toggle, entity sidebar, XML view.
 * Namespace: ZBZ.EditionReader (ES5, IIFE)
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
        serif: true,
        entitiesVisible: false,
        xmlMode: false,
        editMode: false,
        docMeta: null,
        splitRatio: 50
    };

    // --- Init ---
    function init() {
        state.docId = E.sanitizeDocId(E.getParam('doc'));
        state.page = parseInt(E.getParam('page'), 10) || 1;

        if (!state.docId) {
            E.$('.ed-reader').innerHTML = '<div class="ed-empty-state">Kein Dokument angegeben. <a href="catalog.html">Zum Katalog</a></div>';
            return;
        }

        // Catalog + Entity Index parallel laden
        Promise.all([E.loadCatalog(), E.loadEntityIndex()]).then(function (results) {
            var catalog = results[0];
            if (!catalog) return;

            // Find document in catalog
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
            initEditor();
            showPage(state.page);
        });
    }

    // --- Editor Init ---
    function initEditor() {
        if (typeof ZBZ.EditionEditor === 'undefined') return;
        var Ed = ZBZ.EditionEditor;
        Ed.checkServer(function (available) {
            var editBtn = E.$('#edit-toggle');
            if (editBtn && available) {
                editBtn.style.display = '';
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

        // Set document title
        document.title = title + ' – Nachlass Jeanne Hersch';

        var headerEl = E.$('.ed-reader-title');
        if (headerEl) {
            headerEl.innerHTML = '<a href="catalog.html" style="color:var(--ed-text-muted);margin-right:0.5em" title="Zurueck zum Katalog">&larr;</a>' + E.esc(title);
        }

        var metaEl = E.$('.ed-reader-meta');
        if (metaEl) {
            var parts = [];
            if (m.author) parts.push(E.esc(m.author));
            if (m.date) parts.push(E.esc(m.date));
            if (m.type && m.type !== '-') parts.push('<span class="ed-badge ed-badge-type">' + E.esc(E.TYPE_LABELS[m.type] || m.type) + '</span>');
            if (m.lang) parts.push('<span class="ed-badge ed-badge-lang">' + E.esc(m.lang) + '</span>');
            if (m.page_count) parts.push(m.page_count + ' Seiten');
            if (m.demo) parts.push('<span class="ed-badge ed-badge-demo">Demo</span>');
            metaEl.innerHTML = parts.join(' &middot; ');
        }

        // Load curation status badge (only when server available)
        loadCurationStatus();
    }

    // --- Curation Status ---
    function loadCurationStatus() {
        var Ed = typeof ZBZ.EditionEditor !== 'undefined' ? ZBZ.EditionEditor : null;
        if (!Ed || !Ed.state.serverAvailable) return;

        fetch(window.location.origin + '/api/tei/' + state.docId + '/status')
            .then(function (r) { return r.ok ? r.json() : null; })
            .then(function (meta) {
                if (!meta || meta.status === 'pipeline') return;
                renderCurationBadge(meta);
            })
            .catch(function () {});
    }

    function renderCurationBadge(meta) {
        var metaEl = E.$('.ed-reader-meta');
        if (!metaEl) return;

        var statusLabels = {
            draft: 'Entwurf',
            in_review: 'In Pruefung',
            approved: 'Freigegeben'
        };
        var statusClass = {
            draft: 'ed-badge-curation-draft',
            in_review: 'ed-badge-curation-review',
            approved: 'ed-badge-curation-approved'
        };

        var label = statusLabels[meta.status] || meta.status;
        var cls = statusClass[meta.status] || 'ed-badge-curation-draft';

        var badge = document.createElement('span');
        badge.className = 'ed-badge ' + cls;
        badge.textContent = label;
        badge.title = 'Kurations-Status';
        metaEl.appendChild(document.createTextNode(' '));
        metaEl.appendChild(badge);
    }

    // --- Toolbar ---
    function bindToolbar() {
        var prevBtn = E.$('#page-prev');
        var nextBtn = E.$('#page-next');

        if (prevBtn) prevBtn.addEventListener('click', function () { changePage(-1); });
        if (nextBtn) nextBtn.addEventListener('click', function () { changePage(1); });

        // Font toggle
        var fontBtn = E.$('#font-toggle');
        if (fontBtn) {
            fontBtn.addEventListener('click', function () {
                state.serif = !state.serif;
                var panel = E.$('.ed-panel-text');
                if (panel) {
                    panel.classList.toggle('ed-tei-serif', state.serif);
                }
                fontBtn.innerHTML = state.serif ? '<span style="font-family:serif">Aa</span>' : '<span style="font-family:sans-serif">Aa</span>';
                fontBtn.title = state.serif ? 'Sans-Serif Schrift' : 'Serif Schrift';
                fontBtn.classList.toggle('active', !state.serif);
            });
        }

        // Entity toggle
        var entityBtn = E.$('#entity-toggle');
        if (entityBtn) {
            entityBtn.addEventListener('click', function () {
                toggleEntities();
            });
        }

        // Delegate entity-close click (avoids re-binding on every render)
        var sidebar = E.$('.ed-entity-sidebar');
        if (sidebar) {
            sidebar.addEventListener('click', function (e) {
                if (e.target.id === 'entity-close' || e.target.closest('#entity-close')) {
                    toggleEntities();
                }
            });
        }

        // XML toggle
        var xmlBtn = E.$('#xml-toggle');
        if (xmlBtn) {
            xmlBtn.addEventListener('click', function () {
                state.xmlMode = !state.xmlMode;
                xmlBtn.classList.toggle('active', state.xmlMode);
                showPage(state.page);
            });
        }

        // Zoom
        var zoomInBtn = E.$('#zoom-in');
        var zoomOutBtn = E.$('#zoom-out');
        var zoomReset = E.$('#zoom-reset');

        if (zoomInBtn) zoomInBtn.addEventListener('click', function () { setZoom(state.zoom + 25); });
        if (zoomOutBtn) zoomOutBtn.addEventListener('click', function () { setZoom(state.zoom - 25); });
        if (zoomReset) zoomReset.addEventListener('click', function () { setZoom(100); });

        // Edit toggle
        var editBtn = E.$('#edit-toggle');
        if (editBtn) {
            editBtn.addEventListener('click', function () {
                toggleEditMode();
            });
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
            validateBtn.addEventListener('click', function () {
                validateCurrentPage();
            });
        }

        // Keyboard navigation + Ctrl+S
        document.addEventListener('keydown', function (e) {
            // Ctrl+S: Save
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

        // Unsaved changes warning
        window.addEventListener('beforeunload', function (e) {
            if (typeof ZBZ.EditionEditor !== 'undefined' && ZBZ.EditionEditor.state.dirty) {
                e.preventDefault();
                e.returnValue = '';
            }
        });
    }

    function toggleEntities() {
        state.entitiesVisible = !state.entitiesVisible;
        var sidebar = E.$('.ed-entity-sidebar');
        var entityBtn = E.$('#entity-toggle');
        if (sidebar) {
            sidebar.classList.toggle('active', state.entitiesVisible);
            if (state.entitiesVisible) {
                T.renderEntitySidebar(sidebar);
            }
        }
        if (entityBtn) entityBtn.classList.toggle('active', state.entitiesVisible);
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
        loadFaksimile();
        loadTei();
    }

    function updatePageIndicator() {
        var indicator = E.$('#page-indicator');
        if (indicator) {
            indicator.textContent = state.page + ' / ' + state.totalPages;
        }

        var prevBtn = E.$('#page-prev');
        var nextBtn = E.$('#page-next');
        if (prevBtn) prevBtn.disabled = state.page <= 1;
        if (nextBtn) nextBtn.disabled = state.page >= state.totalPages;
    }

    // --- Faksimile ---
    function loadFaksimile() {
        var panel = E.$('.ed-panel-faksimile');
        if (!panel) return;

        var src = E.imagePath(state.docId, state.page);
        var title = state.docMeta ? state.docMeta.title || '' : '';
        var alt = E.esc(title) + ' – Seite ' + state.page;

        panel.innerHTML = '<img src="' + src + '" alt="' + alt + '" style="width:' + state.zoom + '%;opacity:0;transition:opacity 0.3s ease">';

        var img = panel.querySelector('img');
        if (img) {
            img.addEventListener('load', function () {
                img.style.opacity = '1';
            });
            img.addEventListener('error', function () {
                panel.innerHTML = '<div class="ed-empty-state">Bild nicht verfuegbar<br><small style="color:var(--ed-text-muted)">Nur Demo-Dokumente haben Bilder auf GitHub Pages</small></div>';
            });
        }
    }

    // --- TEI ---
    function loadTei() {
        var container = E.$('.ed-text-content');
        if (!container) return;

        container.innerHTML = '<div class="ed-skeleton ed-skeleton-block" style="height:400px"></div>';

        var Ed = typeof ZBZ.EditionEditor !== 'undefined' ? ZBZ.EditionEditor : null;

        // Try server first (curated priority), then static fallback
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

            // Update entity sidebar if visible
            if (state.entitiesVisible) {
                var sidebar = E.$('.ed-entity-sidebar');
                if (sidebar) T.renderEntitySidebar(sidebar);
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

        // Get current XML from editor
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

        // Wrap in minimal TEI document for RelaxNG validation
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
                    _showValidationPanel(null);
                } else {
                    var errCount = result.errors ? result.errors.length : 0;
                    Ed.showToast(errCount + ' Validierungsfehler', 'error');
                    _showValidationPanel(result.errors);
                }
            })
            .catch(function (err) {
                Ed.showToast('Validierung fehlgeschlagen: ' + (err.detail || err.message || ''), 'error');
            });
    }

    function _showValidationPanel(errors) {
        // Remove existing panel
        var existing = E.$('.ed-validation-panel');
        if (existing) existing.remove();

        if (!errors || errors.length === 0) return;

        var panel = document.createElement('div');
        panel.className = 'ed-validation-panel';
        panel.innerHTML = '<div class="ed-validation-header">' +
            '<strong>Validierungsfehler (' + errors.length + ')</strong>' +
            '<button class="ed-validation-close" title="Schliessen">&times;</button>' +
            '</div>';

        var list = document.createElement('div');
        list.className = 'ed-validation-list';
        for (var i = 0; i < errors.length; i++) {
            var err = errors[i];
            var msg = typeof err === 'string' ? err : (err.message || JSON.stringify(err));
            var item = document.createElement('div');
            item.className = 'ed-validation-item';
            item.textContent = msg;
            list.appendChild(item);
        }
        panel.appendChild(list);

        // Insert below toolbar
        var toolbar = E.$('.ed-reader-toolbar');
        if (toolbar && toolbar.parentNode) {
            toolbar.parentNode.insertBefore(panel, toolbar.nextSibling);
        } else {
            document.body.appendChild(panel);
        }

        panel.querySelector('.ed-validation-close').addEventListener('click', function () {
            panel.remove();
        });
    }

    // --- Zoom ---
    function setZoom(z) {
        state.zoom = Math.max(25, Math.min(300, z));
        var img = E.$('.ed-panel-faksimile img');
        if (img) img.style.width = state.zoom + '%';

        var label = E.$('#zoom-label');
        if (label) label.textContent = state.zoom + '%';
    }

    // --- Draggable Divider ---
    function initDivider() {
        var divider = E.$('.ed-panel-divider');
        var panels = E.$('.ed-reader-panels');
        if (!divider || !panels) return;

        var leftPanel = E.$('.ed-panel-faksimile');
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

    // --- Public API ---
    ZBZ.EditionReader = {
        showPage: showPage,
        setZoom: setZoom
    };
})();
