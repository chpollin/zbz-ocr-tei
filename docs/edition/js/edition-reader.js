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
            showPage(state.page);
        });
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

        // Keyboard navigation
        document.addEventListener('keydown', function (e) {
            if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
            if (e.key === 'ArrowLeft') { e.preventDefault(); changePage(-1); }
            else if (e.key === 'ArrowRight') { e.preventDefault(); changePage(1); }
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

        E.fetchTei(state.docId, state.page).then(function (xml) {
            if (state.xmlMode) {
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
