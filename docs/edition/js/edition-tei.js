/**
 * ZBZ Edition – TEI Renderer
 * Renders TEI-XML as readable text with entity extraction.
 * Adapted from docs/tei-viewer.js for reading-optimized display.
 * Namespace: ZBZ.EditionTei (ES5, IIFE)
 */
(function () {
    'use strict';

    var E = ZBZ.Edition;

    var state = {
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

        var doc = E.parseXml(xml);
        if (!doc) {
            container.innerHTML = '<div class="ed-empty-state">XML-Parse-Fehler</div>';
            return;
        }

        extractEntities(doc);

        var body = doc.querySelector('body');
        if (!body) {
            container.innerHTML = '<div class="ed-empty-state">Kein &lt;body&gt; im TEI</div>';
            return;
        }

        renderNode(body, container);
    }

    // --- Render XML view ---
    function renderXml(xml, container) {
        state.mode = 'xml';
        if (!xml) {
            container.innerHTML = '<div class="ed-empty-state">Keine TEI-Daten.</div>';
            return;
        }
        container.innerHTML = '<div class="ed-xml-view">' + E.highlightXml(xml) + '</div>';
    }

    // --- Recursive Node Renderer ---
    function renderNode(node, container) {
        var i;
        if (node.nodeType === 3) {
            var t = node.textContent;
            if (t.trim()) container.appendChild(document.createTextNode(t));
            return;
        }
        if (node.nodeType !== 1) return;

        var tag = node.localName;

        // Skip metadata
        if (tag === 'teiHeader' || tag === 'facsimile') return;

        // Transparent containers
        if (tag === 'TEI' || tag === 'text' || tag === 'body' || tag === 'div' ||
            tag === 'front' || tag === 'back') {
            for (i = 0; i < node.childNodes.length; i++) {
                renderNode(node.childNodes[i], container);
            }
            return;
        }

        var elem = null;

        if (tag === 'pb') {
            elem = document.createElement('div');
            elem.className = 'ed-tei-pb';
            elem.textContent = '-- Seite ' + (node.getAttribute('n') || '?') + ' --';
            container.appendChild(elem);
            return;
        }

        if (tag === 'space') {
            elem = document.createElement('div');
            elem.className = 'ed-tei-space';
            container.appendChild(elem);
            return;
        }

        if (tag === 'head') {
            elem = document.createElement('div');
            elem.className = 'ed-tei-head';
        } else if (tag === 'p') {
            elem = document.createElement('div');
            elem.className = 'ed-tei-p';
        } else if (tag === 'note') {
            elem = document.createElement('div');
            elem.className = 'ed-tei-note';
            var nAttr = node.getAttribute('n');
            if (nAttr) {
                var lbl = document.createElement('span');
                lbl.className = 'ed-tei-note-label';
                lbl.textContent = '[' + nAttr + ']';
                elem.appendChild(lbl);
            }
        } else if (tag === 'figure') {
            elem = document.createElement('div');
            elem.className = 'ed-tei-figure';
            elem.textContent = '[Abbildung]';
            container.appendChild(elem);
            return;
        } else if (tag === 'hi') {
            var rend = node.getAttribute('rendition') || '';
            if (rend === '#sup') {
                elem = document.createElement('sup');
            } else if (rend === '#sub') {
                elem = document.createElement('sub');
            } else {
                elem = document.createElement('span');
                var hiCls = { '#b': 'ed-tei-hi-bold', '#i': 'ed-tei-hi-italic', '#u': 'ed-tei-hi-underline', '#g': 'ed-tei-hi-spaced' };
                if (hiCls[rend]) elem.className = hiCls[rend];
            }
        } else if (tag === 'persName') {
            elem = createEntitySpan(node, 'person', node.getAttribute('ref'));
        } else if (tag === 'orgName') {
            elem = createEntitySpan(node, 'org', node.getAttribute('ref'));
        } else if (tag === 'placeName') {
            elem = createEntitySpan(node, 'place', node.getAttribute('ref'));
        } else if (tag === 'bibl') {
            elem = createEntitySpan(node, 'work', node.getAttribute('ref') || node.getAttribute('corresp'));
        } else if (tag === 'lb') {
            container.appendChild(document.createElement('br'));
            return;
        } else if (tag === 'foreign') {
            elem = document.createElement('span');
            elem.className = 'ed-tei-foreign';
            elem.title = 'Sprache: ' + (node.getAttribute('xml:lang') || '?');
        } else if (tag === 'sp') {
            elem = document.createElement('div');
            elem.className = 'ed-tei-sp';
        } else if (tag === 'speaker') {
            elem = document.createElement('span');
            elem.className = 'ed-tei-speaker';
        } else {
            for (i = 0; i < node.childNodes.length; i++) {
                renderNode(node.childNodes[i], container);
            }
            return;
        }

        if (elem) {
            for (i = 0; i < node.childNodes.length; i++) {
                renderNode(node.childNodes[i], elem);
            }
            container.appendChild(elem);
        }
    }

    // --- Ref Resolution ---
    function resolveEntityRef(ref) {
        if (!ref) return null;
        if (ref.indexOf('#zbz-') === 0) {
            return { type: 'index', id: ref.slice(1), label: ref, url: null };
        }
        if (ref.indexOf('WD:') === 0) {
            var qid = ref.replace('WD:', '');
            return { type: 'wikidata', id: qid, label: 'WD:' + qid,
                     url: 'https://www.wikidata.org/wiki/' + qid };
        }
        if (ref.indexOf('GND:') === 0) {
            var gndId = ref.replace('GND:', '');
            if (gndId !== 'unknown') {
                return { type: 'gnd', id: gndId, label: 'GND:' + gndId,
                         url: 'https://lobid.org/gnd/' + gndId };
            }
        }
        return null;
    }

    // --- Entity Span ---
    function createEntitySpan(node, type, ref) {
        var span = document.createElement('span');
        span.className = 'ed-tei-entity ed-tei-entity-' + type;
        if (ref) {
            span.setAttribute('data-ref', ref);
            var resolved = resolveEntityRef(ref);
            if (resolved && resolved.url) {
                span.addEventListener('click', function () {
                    window.open(resolved.url, '_blank');
                });
            }
            var tip = document.createElement('span');
            tip.className = 'ed-tei-entity-tip';
            tip.textContent = resolved ? resolved.label : ref;
            span.appendChild(tip);
        }
        return span;
    }

    // --- Entity Extraction ---
    function extractEntities(doc) {
        state.entities = { persons: [], orgs: [], places: [], works: [] };
        addFromQuery(doc, 'persName[ref]', 'persons', 'ref');
        addFromQuery(doc, 'orgName[ref]', 'orgs', 'ref');
        addFromQuery(doc, 'placeName[ref]', 'places', 'ref');
        addFromQuery(doc, 'bibl[ref]', 'works', 'ref');
        addFromQuery(doc, 'bibl[corresp]:not([ref])', 'works', 'corresp');
    }

    function addFromQuery(doc, selector, listKey, attrName) {
        var nodes = doc.querySelectorAll(selector);
        for (var i = 0; i < nodes.length; i++) {
            var name = nodes[i].textContent.trim();
            var ref = nodes[i].getAttribute(attrName);
            if (!name || !ref) continue;
            var found = false;
            for (var j = 0; j < state.entities[listKey].length; j++) {
                if (state.entities[listKey][j].ref === ref) {
                    state.entities[listKey][j].count++;
                    found = true;
                    break;
                }
            }
            if (!found) {
                state.entities[listKey].push({ name: name, ref: ref, count: 1 });
            }
        }
    }

    // --- Entity Sidebar ---
    function renderEntitySidebar(container) {
        container.innerHTML = '';

        var title = document.createElement('div');
        title.className = 'ed-entity-sidebar-title';
        title.innerHTML = 'Entitaeten <button class="ed-entity-close" id="entity-close" aria-label="Schliessen">&times;</button>';
        container.appendChild(title);

        renderGroup(container, 'Personen', 'persons');
        renderGroup(container, 'Organisationen', 'orgs');
        renderGroup(container, 'Orte', 'places');
        renderGroup(container, 'Werke', 'works');
    }

    function renderGroup(container, label, key) {
        var group = document.createElement('div');
        group.className = 'ed-entity-group ed-entity-group-' + key;

        var title = document.createElement('div');
        title.className = 'ed-entity-group-title';
        title.textContent = label;
        group.appendChild(title);

        var entities = state.entities[key];
        if (!entities.length) {
            var empty = document.createElement('div');
            empty.className = 'ed-entity-empty';
            empty.textContent = 'Keine';
            group.appendChild(empty);
        } else {
            entities.forEach(function (ent) {
                var item = document.createElement('div');
                item.className = 'ed-entity-item';

                var name = document.createElement('span');
                name.className = 'ed-entity-item-name';
                name.textContent = ent.name;
                name.title = ent.name;
                item.appendChild(name);

                if (ent.count > 1) {
                    var cnt = document.createElement('span');
                    cnt.className = 'ed-entity-item-count';
                    cnt.textContent = ent.count;
                    item.appendChild(cnt);
                }

                var resolved = resolveEntityRef(ent.ref);
                if (resolved && resolved.url) {
                    var link = document.createElement('a');
                    link.className = 'ed-entity-item-gnd';
                    link.textContent = resolved.type === 'wikidata' ? 'WD' : 'GND';
                    link.href = resolved.url;
                    link.target = '_blank';
                    link.title = resolved.label;
                    link.addEventListener('click', function (e) { e.stopPropagation(); });
                    item.appendChild(link);
                }

                item.addEventListener('click', function () { scrollToEntity(ent.ref); });
                group.appendChild(item);
            });
        }

        container.appendChild(group);
    }

    function scrollToEntity(ref) {
        var elem = document.querySelector('.ed-text-content [data-ref="' + ref + '"]');
        if (!elem) return;
        elem.scrollIntoView({ behavior: 'smooth', block: 'center' });
        elem.classList.add('highlight-flash');
        setTimeout(function () { elem.classList.remove('highlight-flash'); }, 1100);
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
