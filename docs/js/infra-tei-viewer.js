/**
 * ZBZ OCR Pipeline – TEI Viewer Module
 * Handles TEI rendering, syntax highlighting, diff view, and entity navigation.
 * Depends on: shared.js (ZBZ namespace)
 */
(function () {
    'use strict';

    const teiState = {
        mode: 'rendered',
        entitiesVisible: false,
        currentXml: null,
        docId: null,
        page: null,
        renderedDone: false,
        xmlDone: false,
        diffDone: false,
        entities: { persons: [], orgs: [], places: [], works: [] }
    };

    // ---- Tab Switching ----
    function switchTeiMode(mode) {
        teiState.mode = mode;
        ZBZ.$$('.tei-tab').forEach((tab) => {
            tab.classList.toggle('active', tab.getAttribute('data-mode') === mode);
        });
        ZBZ.$('#tei-rendered').classList.toggle('hidden', mode !== 'rendered');
        ZBZ.$('#tei-xml-view').classList.toggle('hidden', mode !== 'xml');
        ZBZ.$('#tei-diff-view').classList.toggle('hidden', mode !== 'diff');

        if (!teiState.currentXml) return;
        if (mode === 'rendered' && !teiState.renderedDone) {
            renderTeiView(teiState.currentXml);
        } else if (mode === 'xml' && !teiState.xmlDone) {
            renderTeiXml(teiState.currentXml);
        } else if (mode === 'diff' && !teiState.diffDone) {
            renderTeiDiff(teiState.currentXml, teiState.docId, teiState.page);
        }
    }

    // ---- Load TEI Data ----
    async function loadTei(docId, page) {
        teiState.docId = docId;
        teiState.page = page;

        // Reset lazy flags
        teiState.renderedDone = false;
        teiState.xmlDone = false;
        teiState.diffDone = false;
        teiState.currentXml = null;

        ZBZ.$('#tei-rendered').innerHTML = '<div class="empty-state">Lade...</div>';

        const xml = await ZBZ.fetchPageTei(docId, page);
        teiState.currentXml = xml;

        if (!xml) {
            ZBZ.$('#tei-rendered').innerHTML = '<div class="empty-state">Keine TEI-Daten fuer diese Seite.</div>';
            ZBZ.$('#tei-xml-code').textContent = '';
            ZBZ.$('#diff-generated').innerHTML = '<div class="empty-state">Keine TEI-Daten.</div>';
            return;
        }

        // Render active mode
        if (teiState.mode === 'rendered') {
            renderTeiView(xml);
        } else if (teiState.mode === 'xml') {
            renderTeiXml(xml);
        } else if (teiState.mode === 'diff') {
            renderTeiDiff(xml, docId, page);
        }
    }

    function parseTeiXml(xml) {
        return ZBZ.parseXml(xml);
    }

    // ---- Rendered View ----
    function renderTeiView(xml) {
        const container = ZBZ.$('#tei-rendered');
        container.innerHTML = '';
        teiState.renderedDone = true;

        const doc = parseTeiXml(xml);
        if (!doc) {
            container.innerHTML = '<div class="empty-state">XML-Parse-Fehler</div>';
            return;
        }

        teiState.entities = ZBZ.EntityUtils.extractEntities(doc);

        const body = doc.querySelector('body');
        if (!body) {
            container.innerHTML = '<div class="empty-state">Kein &lt;body&gt; im TEI</div>';
            return;
        }

        renderTeiNode(body, container);
        if (teiState.entitiesVisible) renderEntitySidebar();
    }

    // Render options for unified TEI renderer
    const renderOpts = { cssPrefix: 'tei-', lookupFn: ZBZ.lookupEntity };

    // Delegate to unified renderer (backward-compat wrapper)
    function renderTeiNode(node, container) {
        ZBZ.TeiRender.renderNode(node, container, renderOpts);
    }

    // ---- XML Syntax Highlighting ----
    function renderTeiXml(xml) {
        teiState.xmlDone = true;
        ZBZ.$('#tei-xml-code').innerHTML = ZBZ.highlightXml(xml);
    }

    // ---- Diff View ----
    function renderTeiDiff(xml, docId, page) {
        teiState.diffDone = true;
        const genContainer = ZBZ.$('#diff-generated');
        const refContainer = ZBZ.$('#diff-reference');

        genContainer.innerHTML = `<pre>${ZBZ.highlightXml(xml)}</pre>`;
        refContainer.innerHTML = '<div class="empty-state">Lade Referenz...</div>';

        ZBZ.fetchRefTeiPage(docId, page).then((refXml) => {
            if (refXml) {
                refContainer.innerHTML = `<pre>${ZBZ.highlightXml(refXml)}</pre>`;
            } else {
                refContainer.innerHTML = '<div class="empty-state">Keine Referenz-TEI fuer dieses Dokument.</div>';
            }
        });
    }

    // ---- Entity Sidebar ----
    function toggleEntitySidebar() {
        teiState.entitiesVisible = !teiState.entitiesVisible;
        ZBZ.$('#tei-entity-sidebar').classList.toggle('active', teiState.entitiesVisible);
        ZBZ.$('#entity-toggle').classList.toggle('active', teiState.entitiesVisible);
        if (teiState.entitiesVisible) renderEntitySidebar();
    }

    function renderEntitySidebar() {
        renderEntityGroup('#entity-group-persons', teiState.entities.persons);
        renderEntityGroup('#entity-group-orgs', teiState.entities.orgs);
        renderEntityGroup('#entity-group-places', teiState.entities.places);
        renderEntityGroup('#entity-group-works', teiState.entities.works);
    }

    function renderEntityGroup(selector, entities) {
        const list = ZBZ.$(selector + ' .entity-group-items');
        if (!list) return;
        list.innerHTML = '';
        if (entities.length === 0) {
            list.innerHTML = '<div style="font-size:0.7rem;color:var(--text-muted);padding:2px 0">Keine</div>';
            return;
        }
        entities.forEach((ent) => {
            const item = document.createElement('div');
            item.className = 'entity-item';

            const all = ZBZ.EntityUtils.resolveAllLinks(ent.ref, ZBZ.lookupEntity);

            const name = document.createElement('span');
            name.className = 'entity-item-name';
            name.textContent = all.label !== ent.ref ? all.label : ent.name;
            name.title = all.label !== ent.ref ? all.label : ent.name;
            item.appendChild(name);

            if (ent.count > 1) {
                const cnt = document.createElement('span');
                cnt.className = 'entity-item-count';
                cnt.textContent = ent.count;
                item.appendChild(cnt);
            }

            // Resolution status
            const statusIcon = document.createElement('span');
            if (all.links.length > 0) {
                statusIcon.className = 'entity-item-status entity-resolved';
                statusIcon.textContent = '\u2713';
                statusIcon.title = 'Verifiziert';
            } else {
                statusIcon.className = 'entity-item-status entity-unresolved';
                statusIcon.textContent = '?';
                statusIcon.title = 'Nicht aufgeloest';
            }
            item.appendChild(statusIcon);

            // All external links (WD + GND)
            all.links.forEach((lnk) => {
                const a = document.createElement('a');
                a.className = 'entity-item-link';
                a.textContent = lnk.type === 'wikidata' ? 'WD' : 'GND';
                a.href = lnk.url;
                a.target = '_blank';
                a.title = lnk.type === 'wikidata' ? `Wikidata ${lnk.id}` : `GND ${lnk.id}`;
                a.addEventListener('click', (e) => { e.stopPropagation(); });
                item.appendChild(a);
            });

            // zbz-ID label
            if (all.zbzId) {
                const zbzLabel = document.createElement('span');
                zbzLabel.className = 'entity-item-zbzid';
                zbzLabel.textContent = all.zbzId;
                item.appendChild(zbzLabel);
            }

            item.addEventListener('click', () => { scrollToEntity(ent.ref); });
            list.appendChild(item);
        });
    }

    function scrollToEntity(ref) {
        const elem = ZBZ.$(`#tei-rendered [data-ref="${ref}"]`);
        if (!elem) return;
        // Switch to rendered mode if not there
        if (teiState.mode !== 'rendered') switchTeiMode('rendered');
        elem.scrollIntoView({ behavior: 'smooth', block: 'center' });
        elem.classList.add('highlight-flash');
        setTimeout(() => { elem.classList.remove('highlight-flash'); }, 1100);
    }

    // ---- Init: Bind event listeners ----
    function init() {
        ZBZ.$$('.tei-tab').forEach((tab) => {
            tab.addEventListener('click', () => {
                switchTeiMode(tab.getAttribute('data-mode'));
            });
        });

        ZBZ.$('#entity-toggle').addEventListener('click', () => { toggleEntitySidebar(); });
        ZBZ.$('#entity-close').addEventListener('click', () => { toggleEntitySidebar(); });
    }

    // Auto-init when script loads (DOM is ready since script is at bottom of body)
    init();

    ZBZ.log('TeiViewer', 'ready (rendered/xml/diff)');

    // ---- Public API ----
    ZBZ.TeiViewer = {
        loadTei: loadTei,
        switchMode: switchTeiMode,
        toggleEntitySidebar: toggleEntitySidebar
    };
})();
