/**
 * ZBZ Edition – TEI Renderer
 * Renders TEI-XML as readable text with entity extraction.
 * Adapted from docs/tei-viewer.js for reading-optimized display.
 * Namespace: ZBZ.EditionTei (ES6+, IIFE)
 */
(function () {
    'use strict';

    const E = ZBZ.Edition;

    const state = {
        currentXml: null,
        mode: 'rendered',
        entities: { persons: [], orgs: [], places: [], works: [] }
    };

    // --- Render TEI XML into container ---
    function render(xml, container) {
        state.currentXml = xml;
        state.mode = 'rendered';
        container.innerHTML = '';

        if (!xml) {
            container.innerHTML = '<div class="ed-empty-state">Keine TEI-Daten fuer diese Seite.</div>';
            return;
        }

        const doc = E.parseXml(xml);
        if (!doc) {
            container.innerHTML = '<div class="ed-empty-state">XML-Parse-Fehler</div>';
            return;
        }

        state.entities = ZBZ.EntityUtils.extractEntities(doc);

        ZBZ.TeiRender.render(doc, container, renderOpts);
    }

    // --- Render XML view ---
    function renderXml(xml, container) {
        state.mode = 'xml';
        if (!xml) {
            container.innerHTML = '<div class="ed-empty-state">Keine TEI-Daten.</div>';
            return;
        }
        container.innerHTML = `<div class="ed-xml-view">${E.highlightXml(xml)}</div>`;
    }

    // --- Render options for unified TEI renderer ---
    const renderOpts = { cssPrefix: 'ed-tei-', lookupFn: E.lookupEntity };

    // --- Entity Sidebar (used by infrastruktur/tei-viewer.js, not by edition reader) ---
    function renderEntitySidebar(container) {
        container.innerHTML = '';

        const title = document.createElement('div');
        title.className = 'ed-entity-sidebar-title';
        title.innerHTML = 'Entitaeten <button class="ed-entity-close" id="entity-close" aria-label="Schliessen">&times;</button>';
        container.appendChild(title);

        renderGroup(container, 'Personen', 'persons');
        renderGroup(container, 'Organisationen', 'orgs');
        renderGroup(container, 'Orte', 'places');
        renderGroup(container, 'Werke', 'works');
    }

    function renderGroup(container, label, key) {
        const group = document.createElement('div');
        group.className = `ed-entity-group ed-entity-group-${key}`;

        const title = document.createElement('div');
        title.className = 'ed-entity-group-title';
        title.textContent = label;
        const entities = state.entities[key];
        if (entities.length) {
            const badge = document.createElement('span');
            badge.className = 'ed-entity-group-count';
            badge.textContent = entities.length;
            title.appendChild(badge);
        }
        group.appendChild(title);

        if (!entities.length) {
            const empty = document.createElement('div');
            empty.className = 'ed-entity-empty';
            empty.textContent = 'Keine';
            group.appendChild(empty);
        } else {
            entities.forEach((ent) => {
                const item = document.createElement('div');
                item.className = 'ed-entity-item';

                const all = ZBZ.EntityUtils.resolveAllLinks(ent.ref, E.lookupEntity);

                const name = document.createElement('span');
                name.className = 'ed-entity-item-name';
                name.textContent = all.label !== ent.ref ? all.label : ent.name;
                name.title = all.label !== ent.ref ? all.label : ent.name;
                item.appendChild(name);

                if (ent.count > 1) {
                    const cnt = document.createElement('span');
                    cnt.className = 'ed-entity-item-count';
                    cnt.textContent = ent.count;
                    item.appendChild(cnt);
                }

                // Resolution status indicator
                const statusIcon = document.createElement('span');
                if (all.links.length > 0) {
                    statusIcon.className = 'ed-entity-status ed-entity-resolved';
                    statusIcon.textContent = '\u2713';
                    statusIcon.title = 'Verifiziert';
                } else {
                    statusIcon.className = 'ed-entity-status ed-entity-unresolved';
                    statusIcon.textContent = '?';
                    statusIcon.title = 'Nicht aufgeloest';
                }
                item.appendChild(statusIcon);

                // All external links (WD + GND)
                all.links.forEach((lnk) => {
                    const a = document.createElement('a');
                    a.className = 'ed-entity-item-link';
                    a.textContent = lnk.type === 'wikidata' ? 'WD' : 'GND';
                    a.href = lnk.url;
                    a.target = '_blank';
                    a.title = lnk.type === 'wikidata' ? `Wikidata ${lnk.id}` : `GND ${lnk.id}`;
                    a.addEventListener('click', (e) => { e.stopPropagation(); });
                    item.appendChild(a);
                });

                // zbz-ID label (links to register)
                if (all.zbzId) {
                    const zbzLabel = document.createElement('a');
                    zbzLabel.className = 'ed-entity-item-zbzid';
                    zbzLabel.textContent = all.zbzId;
                    // Route to type-specific register page
                    const typeMap = { 'p': 'person', 'o': 'organization', 'l': 'place', 'w': 'work' };
                    const typeChar = (all.zbzId.match(/^zbz-([a-z])\./) || [])[1] || 'p';
                    const regType = typeMap[typeChar] || 'person';
                    zbzLabel.href = `register.html?type=${regType}&id=${encodeURIComponent(all.zbzId)}`;
                    zbzLabel.title = 'Im Register anzeigen';
                    zbzLabel.addEventListener('click', (e) => { e.stopPropagation(); });
                    item.appendChild(zbzLabel);
                }

                item.addEventListener('click', () => { scrollToEntity(ent.ref); });
                group.appendChild(item);
            });
        }

        container.appendChild(group);
    }

    function scrollToEntity(ref) {
        const elem = document.querySelector(`.ed-text-content [data-ref="${ref}"]`);
        if (!elem) return;
        elem.scrollIntoView({ behavior: 'smooth', block: 'center' });
        elem.classList.add('highlight-flash');
        setTimeout(() => { elem.classList.remove('highlight-flash'); }, 1100);
    }

    function getEntities() {
        return state.entities;
    }

    function hasEntities() {
        return state.entities.persons.length > 0 ||
               state.entities.orgs.length > 0 ||
               state.entities.places.length > 0 ||
               state.entities.works.length > 0;
    }

    if (ZBZ.log) ZBZ.log('EditionTei', 'ready');

    // --- Public API ---
    ZBZ.EditionTei = {
        render: render,
        renderXml: renderXml,
        renderEntitySidebar: renderEntitySidebar,
        getEntities: getEntities,
        hasEntities: hasEntities,
        scrollToEntity: scrollToEntity
    };
})();
