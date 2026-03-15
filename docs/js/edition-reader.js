/**
 * ZBZ Edition – Reader Module
 * Faksimile + TEI side-by-side reader with page navigation,
 * zoom, font toggle, entity sidebar, XML view.
 * Namespace: ZBZ.EditionReader (ES6+, IIFE)
 */
(function () {
    'use strict';

    const E = ZBZ.Edition;
    const T = ZBZ.EditionTei;

    const state = {
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
        Promise.all([E.loadCatalog(), E.loadEntityIndex()]).then((results) => {
            const catalog = results[0];
            if (!catalog) return;

            // Find document in catalog
            const docs = catalog.documents || [];
            for (let i = 0; i < docs.length; i++) {
                if (docs[i].id === state.docId) {
                    state.docMeta = docs[i];
                    break;
                }
            }

            if (!state.docMeta) {
                E.$('.ed-reader').innerHTML = `<div class="ed-empty-state">Dokument ${E.esc(state.docId)} nicht gefunden. <a href="catalog.html">Zum Katalog</a></div>`;
                return;
            }

            state.totalPages = state.docMeta.page_count || 1;
            if (state.page > state.totalPages) state.page = 1;

            renderHeader();
            bindToolbar();
            initDivider();
            initEditor();
            showPage(state.page);
            loadRevisionDesc();

            ZBZ.log('Reader', `Doc ${state.docId} | S.${state.page}/${state.totalPages} | Entities: ${state.docMeta.entity_count || 0}`);
        });
    }

    // --- Editor Init ---
    function initEditor() {
        if (typeof ZBZ.EditionEditor === 'undefined') return;
        const Ed = ZBZ.EditionEditor;
        Ed.checkServer((available) => {
            const editBtn = E.$('#edit-toggle');
            if (editBtn && available) {
                editBtn.style.display = '';
            }
        });
    }

    function toggleEditMode() {
        const Ed = ZBZ.EditionEditor;
        state.editMode = !state.editMode;
        Ed.state.active = state.editMode;

        const reader = E.$('.ed-reader');
        const editBtn = E.$('#edit-toggle');
        if (reader) reader.classList.toggle('ed-edit-mode', state.editMode);
        if (editBtn) editBtn.classList.toggle('active', state.editMode);

        if (!state.editMode) {
            Ed.clearDirty();
        }

        showPage(state.page);
    }

    // --- Header ---
    function renderHeader() {
        const m = state.docMeta;
        const title = m.title || 'Dokument ' + m.id;

        // Set document title
        document.title = title + ' – Nachlass Jeanne Hersch';

        const headerEl = E.$('.ed-reader-title');
        if (headerEl) {
            headerEl.innerHTML = '<a href="catalog.html" style="color:var(--ed-text-muted);margin-right:0.5em" title="Zurueck zum Katalog">&larr;</a>' + E.esc(title);
        }

        const metaEl = E.$('.ed-reader-meta');
        if (metaEl) {
            const parts = [];
            if (m.author) parts.push(E.esc(m.author));
            if (m.date) parts.push(E.esc(m.date));
            if (m.type && m.type !== '-') parts.push('<span class="ed-badge ed-badge-type">' + E.esc(E.TYPE_LABELS[m.type] || m.type) + '</span>');
            if (m.lang) parts.push('<span class="ed-badge ed-badge-lang">' + E.esc(m.lang) + '</span>');
            if (m.page_count) parts.push(m.page_count + ' Seiten');
            if (m.demo) parts.push('<span class="ed-badge ed-badge-demo">Demo</span>');
            if (m.screening) {
                parts.push(E.screeningBadgeHtml(m.screening));
            }
            metaEl.innerHTML = parts.join(' &middot; ');
        }

        // Load curation status badge (only when server available)
        loadCurationStatus();
    }

    // --- Curation Status ---
    function loadCurationStatus() {
        const Ed = typeof ZBZ.EditionEditor !== 'undefined' ? ZBZ.EditionEditor : null;
        if (!Ed || !Ed.state.serverAvailable) return;

        fetch(window.location.origin + '/api/tei/' + state.docId + '/status')
            .then((r) => r.ok ? r.json() : null)
            .then((meta) => {
                if (!meta || meta.status === 'pipeline') return;
                renderCurationBadge(meta);
            })
            .catch(() => {});
    }

    function renderCurationBadge(meta) {
        const metaEl = E.$('.ed-reader-meta');
        if (!metaEl) return;
        const badgeHtml = E.curationBadgeHtml(meta.status);
        if (!badgeHtml) return;
        const span = document.createElement('span');
        span.innerHTML = ' ' + badgeHtml;
        metaEl.appendChild(span);
    }

    // --- Revision History ---
    function loadRevisionDesc() {
        E.fetchFullTei(state.docId).then((xml) => {
            if (!xml) return;
            const changes = E.extractRevisionDesc(xml);
            if (changes && changes.length) {
                renderRevisionPanel(changes);
            }
        });
    }

    function renderRevisionPanel(changes) {
        const toolbar = E.$('.ed-reader-toolbar');
        if (!toolbar) return;

        // Remove existing panel
        const existing = E.$('.ed-revision-panel');
        if (existing) existing.remove();

        const panel = document.createElement('div');
        panel.className = 'ed-revision-panel';

        // Latest status for summary
        const lastChange = changes[changes.length - 1];
        const statusText = lastChange.status ? ` \u2014 ${lastChange.status}` : '';

        panel.innerHTML =
            `<button class="ed-revision-toggle" aria-expanded="false">` +
            `<span>Revisionsgeschichte (${changes.length})${E.esc(statusText)}</span>` +
            `<span class="ed-chevron">&#9660;</span></button>` +
            `<div class="ed-revision-timeline"></div>`;

        const timeline = panel.querySelector('.ed-revision-timeline');
        changes.forEach((ch) => {
            const entry = document.createElement('div');
            entry.className = 'ed-revision-entry';
            let statusHtml = '';
            if (ch.status) {
                statusHtml = ` <span class="ed-revision-status" data-status="${E.esc(ch.status)}">${E.esc(ch.status)}</span>`;
            }
            entry.innerHTML =
                `<span class="ed-revision-date">${E.esc(ch.when)}</span>` +
                `<span class="ed-revision-who">${E.esc(ch.who)}</span>` +
                `<span class="ed-revision-text">${E.esc(ch.text)}${statusHtml}</span>`;
            timeline.appendChild(entry);
        });

        // Toggle
        const toggle = panel.querySelector('.ed-revision-toggle');
        toggle.addEventListener('click', () => {
            const open = panel.classList.toggle('open');
            toggle.setAttribute('aria-expanded', String(open));
        });

        // Auto-expand for NEEDS_REVIEW
        if (lastChange.status === 'NEEDS_REVIEW') {
            panel.classList.add('open');
            toggle.setAttribute('aria-expanded', 'true');
        }

        toolbar.after(panel);

        // Page thumbnails strip
        renderPageThumbs();
    }

    function renderPageThumbs() {
        if (!state.totalPages || state.totalPages <= 1) return;
        const toolbar = E.$('.ed-reader-toolbar');
        if (!toolbar) return;

        // Remove existing
        const existing = E.$('.ed-page-thumbs');
        if (existing) existing.remove();

        const strip = document.createElement('div');
        strip.className = 'ed-page-thumbs';
        for (let i = 1; i <= state.totalPages; i++) {
            const thumb = document.createElement('button');
            thumb.className = 'ed-page-thumb' + (i === state.page ? ' active' : '');
            thumb.textContent = i;
            thumb.title = `Seite ${i}`;
            thumb.addEventListener('click', () => { showPage(i); });
            strip.appendChild(thumb);
        }

        // Insert after revision panel if present, else after toolbar
        const revPanel = E.$('.ed-revision-panel');
        if (revPanel) {
            revPanel.after(strip);
        } else {
            toolbar.after(strip);
        }
    }

    // --- Toolbar ---
    function bindToolbar() {
        const prevBtn = E.$('#page-prev');
        const nextBtn = E.$('#page-next');

        if (prevBtn) { prevBtn.title = 'Vorherige Seite (Pfeiltaste links)'; prevBtn.addEventListener('click', () => { changePage(-1); }); }
        if (nextBtn) { nextBtn.title = 'Naechste Seite (Pfeiltaste rechts)'; nextBtn.addEventListener('click', () => { changePage(1); }); }

        // Font toggle
        const fontBtn = E.$('#font-toggle');
        if (fontBtn) {
            fontBtn.addEventListener('click', () => {
                state.serif = !state.serif;
                const panel = E.$('.ed-panel-text');
                if (panel) {
                    panel.classList.toggle('ed-tei-serif', state.serif);
                }
                fontBtn.innerHTML = state.serif ? '<span style="font-family:serif">Aa</span>' : '<span style="font-family:sans-serif">Aa</span>';
                fontBtn.title = state.serif ? 'Sans-Serif Schrift' : 'Serif Schrift';
                fontBtn.classList.toggle('active', !state.serif);
            });
        }

        // Entity toggle
        const entityBtn = E.$('#entity-toggle');
        if (entityBtn) {
            entityBtn.addEventListener('click', () => {
                toggleEntities();
            });
        }

        // Delegate entity-close click (avoids re-binding on every render)
        const sidebar = E.$('.ed-entity-sidebar');
        if (sidebar) {
            sidebar.addEventListener('click', (e) => {
                if (e.target.id === 'entity-close' || e.target.closest('#entity-close')) {
                    toggleEntities();
                }
            });
        }

        // XML toggle
        const xmlBtn = E.$('#xml-toggle');
        if (xmlBtn) {
            xmlBtn.addEventListener('click', () => {
                state.xmlMode = !state.xmlMode;
                xmlBtn.classList.toggle('active', state.xmlMode);
                showPage(state.page);
            });
        }

        // Zoom
        const zoomInBtn = E.$('#zoom-in');
        const zoomOutBtn = E.$('#zoom-out');
        const zoomReset = E.$('#zoom-reset');

        if (zoomInBtn) zoomInBtn.addEventListener('click', () => { setZoom(state.zoom + 25); });
        if (zoomOutBtn) zoomOutBtn.addEventListener('click', () => { setZoom(state.zoom - 25); });
        if (zoomReset) zoomReset.addEventListener('click', () => { setZoom(100); });

        // Edit toggle
        const editBtn = E.$('#edit-toggle');
        if (editBtn) {
            editBtn.addEventListener('click', () => {
                toggleEditMode();
            });
        }

        // Save button
        const saveBtn = E.$('#save-btn');
        if (saveBtn) {
            saveBtn.addEventListener('click', () => {
                if (typeof ZBZ.EditionEditor !== 'undefined') {
                    const container = E.$('.ed-text-content');
                    ZBZ.EditionEditor.savePageXml(state.docId, state.page, container, state.xmlMode);
                }
            });
        }

        // Validate button
        const validateBtn = E.$('#validate-btn');
        if (validateBtn) {
            validateBtn.addEventListener('click', () => {
                validateCurrentPage();
            });
        }

        // Keyboard navigation + Ctrl+S
        document.addEventListener('keydown', (e) => {
            // Ctrl+S: Save
            if ((e.ctrlKey || e.metaKey) && e.key === 's' && state.editMode) {
                e.preventDefault();
                if (typeof ZBZ.EditionEditor !== 'undefined' && ZBZ.EditionEditor.state.dirty) {
                    const container = E.$('.ed-text-content');
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
        window.addEventListener('beforeunload', (e) => {
            if (typeof ZBZ.EditionEditor !== 'undefined' && ZBZ.EditionEditor.state.dirty) {
                e.preventDefault();
                e.returnValue = '';
            }
        });
    }

    function toggleEntities() {
        state.entitiesVisible = !state.entitiesVisible;
        const sidebar = E.$('.ed-entity-sidebar');
        const entityBtn = E.$('#entity-toggle');
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
        const newPage = state.page + delta;
        if (newPage < 1 || newPage > state.totalPages) return;
        showPage(newPage);
    }

    function showPage(page) {
        state.page = page;
        E.setParams({ doc: state.docId, page: page });
        updatePageIndicator();
        updatePageThumbs();
        loadFaksimile();
        loadTei();
    }

    function updatePageThumbs() {
        E.$$('.ed-page-thumb').forEach((t) => {
            t.classList.toggle('active', parseInt(t.textContent, 10) === state.page);
        });
    }

    function updatePageIndicator() {
        const indicator = E.$('#page-indicator');
        if (indicator) {
            indicator.textContent = state.page + ' / ' + state.totalPages;
        }

        const prevBtn = E.$('#page-prev');
        const nextBtn = E.$('#page-next');
        if (prevBtn) prevBtn.disabled = state.page <= 1;
        if (nextBtn) nextBtn.disabled = state.page >= state.totalPages;
    }

    // --- Faksimile ---
    function loadFaksimile() {
        const panel = E.$('.ed-panel-faksimile');
        if (!panel) return;

        const src = E.imagePath(state.docId, state.page);
        const title = state.docMeta ? state.docMeta.title || '' : '';
        const alt = E.esc(title) + ' – Seite ' + state.page;

        panel.innerHTML = `<img src="${src}" alt="${alt}" style="width:${state.zoom}%;opacity:0;transition:opacity 0.3s ease">`;

        const img = panel.querySelector('img');
        if (img) {
            img.addEventListener('load', () => {
                img.style.opacity = '1';
            });
            img.addEventListener('error', () => {
                panel.innerHTML = '<div class="ed-empty-state">Bild nicht verfuegbar<br><small style="color:var(--ed-text-muted)">Nur Demo-Dokumente haben Bilder auf GitHub Pages</small></div>';
            });
        }
    }

    // --- TEI ---
    function loadTei() {
        const container = E.$('.ed-text-content');
        if (!container) return;

        container.innerHTML = '<div class="ed-skeleton ed-skeleton-block" style="height:400px"></div>';

        const Ed = typeof ZBZ.EditionEditor !== 'undefined' ? ZBZ.EditionEditor : null;

        // Try server first (curated priority), then static fallback
        let teiPromise;
        if (Ed && Ed.state.serverAvailable) {
            teiPromise = Ed.fetchTeiFromServer(state.docId, state.page)
                .then((data) => {
                    if (data && data.xml) return data.xml;
                    return E.fetchTei(state.docId, state.page);
                });
        } else {
            teiPromise = E.fetchTei(state.docId, state.page);
        }

        teiPromise.then((xml) => {
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
                const sidebar = E.$('.ed-entity-sidebar');
                if (sidebar) T.renderEntitySidebar(sidebar);
            }
        });
    }

    // --- Validation ---
    function validateCurrentPage() {
        const Ed = typeof ZBZ.EditionEditor !== 'undefined' ? ZBZ.EditionEditor : null;
        if (!Ed || !Ed.state.serverAvailable) {
            Ed.showToast('Server nicht erreichbar', 'error');
            return;
        }

        // Get current XML from editor
        const container = E.$('.ed-text-content');
        let xml;
        if (state.xmlMode) {
            const textarea = container.querySelector('.ed-xml-editor');
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
        let fullXml = xml;
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
            .then((r) => r.json())
            .then((result) => {
                if (result.valid) {
                    Ed.showToast('TEI ist valide (RelaxNG)', 'success');
                    _showValidationPanel(null);
                } else {
                    const errCount = result.errors ? result.errors.length : 0;
                    Ed.showToast(errCount + ' Validierungsfehler', 'error');
                    _showValidationPanel(result.errors);
                }
            })
            .catch((err) => {
                Ed.showToast('Validierung fehlgeschlagen: ' + (err.detail || err.message || ''), 'error');
            });
    }

    function _showValidationPanel(errors) {
        // Remove existing panel
        const existing = E.$('.ed-validation-panel');
        if (existing) existing.remove();

        if (!errors || errors.length === 0) return;

        const panel = document.createElement('div');
        panel.className = 'ed-validation-panel';
        panel.innerHTML = '<div class="ed-validation-header">' +
            '<strong>Validierungsfehler (' + errors.length + ')</strong>' +
            '<button class="ed-validation-close" title="Schliessen">&times;</button>' +
            '</div>';

        const list = document.createElement('div');
        list.className = 'ed-validation-list';
        for (let i = 0; i < errors.length; i++) {
            const err = errors[i];
            const msg = typeof err === 'string' ? err : (err.message || JSON.stringify(err));
            const item = document.createElement('div');
            item.className = 'ed-validation-item';
            item.textContent = msg;
            list.appendChild(item);
        }
        panel.appendChild(list);

        // Insert below toolbar
        const toolbar = E.$('.ed-reader-toolbar');
        if (toolbar && toolbar.parentNode) {
            toolbar.parentNode.insertBefore(panel, toolbar.nextSibling);
        } else {
            document.body.appendChild(panel);
        }

        panel.querySelector('.ed-validation-close').addEventListener('click', () => {
            panel.remove();
        });
    }

    // --- Zoom ---
    function setZoom(z) {
        state.zoom = Math.max(25, Math.min(300, z));
        const img = E.$('.ed-panel-faksimile img');
        if (img) img.style.width = state.zoom + '%';

        const label = E.$('#zoom-label');
        if (label) label.textContent = state.zoom + '%';
    }

    // --- Draggable Divider ---
    function initDivider() {
        const divider = E.$('.ed-panel-divider');
        const panels = E.$('.ed-reader-panels');
        if (!divider || !panels) return;

        const leftPanel = E.$('.ed-panel-faksimile');
        const rightPanel = E.$('.ed-panel-text');
        if (!leftPanel || !rightPanel) return;

        let dragging = false;

        divider.addEventListener('mousedown', (e) => {
            e.preventDefault();
            dragging = true;
            divider.classList.add('dragging');
            document.body.style.cursor = 'col-resize';
            document.body.style.userSelect = 'none';
        });

        document.addEventListener('mousemove', (e) => {
            if (!dragging) return;
            const rect = panels.getBoundingClientRect();
            let pct = ((e.clientX - rect.left) / rect.width) * 100;
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
