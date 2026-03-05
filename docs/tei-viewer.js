/**
 * ZBZ OCR Pipeline – TEI Viewer Module
 * Handles TEI rendering, syntax highlighting, diff view, and entity navigation.
 * Depends on: shared.js (ZBZ namespace)
 */
(function () {
    'use strict';

    var teiState = {
        mode: 'rendered',
        entitiesVisible: false,
        currentXml: null,
        docId: null,
        page: null,
        renderedDone: false,
        xmlDone: false,
        diffDone: false,
        entities: { persons: [], orgs: [], works: [] }
    };

    // ---- Tab Switching ----
    function switchTeiMode(mode) {
        teiState.mode = mode;
        ZBZ.$$('.tei-tab').forEach(function (tab) {
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

        var xml = await ZBZ.fetchPageTei(docId, page);
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
        var container = ZBZ.$('#tei-rendered');
        container.innerHTML = '';
        teiState.renderedDone = true;

        var doc = parseTeiXml(xml);
        if (!doc) {
            container.innerHTML = '<div class="empty-state">XML-Parse-Fehler</div>';
            return;
        }

        extractEntities(doc);

        var body = doc.querySelector('body');
        if (!body) {
            container.innerHTML = '<div class="empty-state">Kein &lt;body&gt; im TEI</div>';
            return;
        }

        renderTeiNode(body, container);
        if (teiState.entitiesVisible) renderEntitySidebar();
    }

    function renderTeiNode(node, container) {
        var i;
        if (node.nodeType === 3) {
            var t = node.textContent;
            if (t.trim()) container.appendChild(document.createTextNode(t));
            return;
        }
        if (node.nodeType !== 1) return;

        var tag = node.localName;

        // Skip metadata sections
        if (tag === 'teiHeader' || tag === 'facsimile') return;

        // Transparent containers — just render children
        if (tag === 'TEI' || tag === 'text' || tag === 'body' || tag === 'div' || tag === 'front' || tag === 'back') {
            for (i = 0; i < node.childNodes.length; i++) {
                renderTeiNode(node.childNodes[i], container);
            }
            return;
        }

        var elem = null;

        if (tag === 'pb') {
            elem = document.createElement('div');
            elem.className = 'tei-pb';
            elem.textContent = '- Seite ' + (node.getAttribute('n') || '?') + ' -';
            container.appendChild(elem);
            return;
        }

        if (tag === 'space') {
            elem = document.createElement('div');
            elem.className = 'tei-space';
            container.appendChild(elem);
            return;
        }

        if (tag === 'head') {
            elem = document.createElement('div');
            elem.className = 'tei-head';
        } else if (tag === 'p') {
            elem = document.createElement('div');
            elem.className = 'tei-p';
        } else if (tag === 'note') {
            elem = document.createElement('div');
            elem.className = 'tei-note';
            var nAttr = node.getAttribute('n');
            if (nAttr) {
                var lbl = document.createElement('span');
                lbl.className = 'tei-note-label';
                lbl.textContent = '[' + nAttr + ']';
                elem.appendChild(lbl);
            }
        } else if (tag === 'figure') {
            elem = document.createElement('div');
            elem.className = 'tei-figure';
        } else if (tag === 'hi') {
            var rend = node.getAttribute('rendition') || '';
            elem = document.createElement('span');
            if (rend === '#b') {
                elem.style.fontWeight = '600';
            } else if (rend === '#i') {
                elem.style.fontStyle = 'italic';
            } else if (rend === '#u') {
                elem.style.textDecoration = 'underline';
            } else if (rend === '#sup') {
                elem = document.createElement('sup');
            } else if (rend === '#sub') {
                elem = document.createElement('sub');
            } else if (rend === '#g') {
                elem.style.letterSpacing = '0.15em';
            }
        } else if (tag === 'persName') {
            elem = createEntitySpan(node, 'person', node.getAttribute('ref'));
        } else if (tag === 'orgName') {
            elem = createEntitySpan(node, 'org', node.getAttribute('ref'));
        } else if (tag === 'bibl') {
            elem = createEntitySpan(node, 'work', node.getAttribute('corresp') || node.getAttribute('ref'));
        } else if (tag === 'lb') {
            container.appendChild(document.createElement('br'));
            return;
        } else if (tag === 'foreign') {
            elem = document.createElement('span');
            elem.style.fontStyle = 'italic';
            elem.title = 'Sprache: ' + (node.getAttribute('xml:lang') || '?');
        } else if (tag === 'sp') {
            elem = document.createElement('div');
            elem.className = 'tei-p';
            elem.style.marginLeft = 'var(--space-md)';
        } else if (tag === 'speaker') {
            elem = document.createElement('span');
            elem.style.fontWeight = '600';
        } else {
            // Unknown elements: render children transparently
            for (i = 0; i < node.childNodes.length; i++) {
                renderTeiNode(node.childNodes[i], container);
            }
            return;
        }

        if (elem) {
            for (i = 0; i < node.childNodes.length; i++) {
                renderTeiNode(node.childNodes[i], elem);
            }
            container.appendChild(elem);
        }
    }

    function createEntitySpan(node, type, ref) {
        var span = document.createElement('span');
        span.className = 'tei-entity tei-entity-' + type;
        if (ref) {
            span.setAttribute('data-ref', ref);
            span.addEventListener('click', function () {
                var gndId = ref.replace('GND:', '');
                window.open('https://lobid.org/gnd/' + gndId, '_blank');
            });
            var tip = document.createElement('span');
            tip.className = 'tei-entity-tip';
            tip.textContent = ref;
            span.appendChild(tip);
        }
        return span;
    }

    // ---- XML Syntax Highlighting ----
    function renderTeiXml(xml) {
        teiState.xmlDone = true;
        ZBZ.$('#tei-xml-code').innerHTML = ZBZ.highlightXml(xml);
    }

    // ---- Diff View ----
    function renderTeiDiff(xml, docId, page) {
        teiState.diffDone = true;
        var genContainer = ZBZ.$('#diff-generated');
        var refContainer = ZBZ.$('#diff-reference');

        genContainer.innerHTML = '<pre>' + ZBZ.highlightXml(xml) + '</pre>';
        refContainer.innerHTML = '<div class="empty-state">Lade Referenz...</div>';

        ZBZ.fetchRefTeiPage(docId, page).then(function (refXml) {
            if (refXml) {
                refContainer.innerHTML = '<pre>' + ZBZ.highlightXml(refXml) + '</pre>';
            } else {
                refContainer.innerHTML = '<div class="empty-state">Keine Referenz-TEI fuer dieses Dokument.</div>';
            }
        });
    }

    // ---- Entity Extraction ----
    function extractEntities(doc) {
        teiState.entities = { persons: [], orgs: [], works: [] };

        addEntitiesFromQuery(doc, 'persName[ref]', 'persons', 'ref');
        addEntitiesFromQuery(doc, 'orgName[ref]', 'orgs', 'ref');
        addEntitiesFromQuery(doc, 'bibl[corresp]', 'works', 'corresp');
    }

    function addEntitiesFromQuery(doc, selector, listKey, attrName) {
        var nodes = doc.querySelectorAll(selector);
        for (var i = 0; i < nodes.length; i++) {
            var name = nodes[i].textContent.trim();
            var ref = nodes[i].getAttribute(attrName);
            if (!name || !ref) continue;
            var found = false;
            for (var j = 0; j < teiState.entities[listKey].length; j++) {
                if (teiState.entities[listKey][j].ref === ref) {
                    teiState.entities[listKey][j].count++;
                    found = true;
                    break;
                }
            }
            if (!found) {
                teiState.entities[listKey].push({ name: name, ref: ref, count: 1 });
            }
        }
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
        renderEntityGroup('#entity-group-works', teiState.entities.works);
    }

    function renderEntityGroup(selector, entities) {
        var list = ZBZ.$(selector + ' .entity-group-items');
        if (!list) return;
        list.innerHTML = '';
        if (entities.length === 0) {
            list.innerHTML = '<div style="font-size:0.7rem;color:var(--text-muted);padding:2px 0">Keine</div>';
            return;
        }
        entities.forEach(function (ent) {
            var item = document.createElement('div');
            item.className = 'entity-item';

            var name = document.createElement('span');
            name.className = 'entity-item-name';
            name.textContent = ent.name;
            name.title = ent.name;
            item.appendChild(name);

            if (ent.count > 1) {
                var cnt = document.createElement('span');
                cnt.className = 'entity-item-count';
                cnt.textContent = ent.count;
                item.appendChild(cnt);
            }

            var gnd = document.createElement('a');
            gnd.className = 'entity-item-gnd';
            gnd.textContent = 'GND';
            gnd.href = 'https://lobid.org/gnd/' + ent.ref.replace('GND:', '');
            gnd.target = '_blank';
            gnd.title = ent.ref;
            gnd.addEventListener('click', function (e) { e.stopPropagation(); });
            item.appendChild(gnd);

            item.addEventListener('click', function () { scrollToEntity(ent.ref); });
            list.appendChild(item);
        });
    }

    function scrollToEntity(ref) {
        var elem = ZBZ.$('#tei-rendered [data-ref="' + ref + '"]');
        if (!elem) return;
        // Switch to rendered mode if not there
        if (teiState.mode !== 'rendered') switchTeiMode('rendered');
        elem.scrollIntoView({ behavior: 'smooth', block: 'center' });
        elem.classList.add('highlight-flash');
        setTimeout(function () { elem.classList.remove('highlight-flash'); }, 1100);
    }

    // ---- Init: Bind event listeners ----
    function init() {
        ZBZ.$$('.tei-tab').forEach(function (tab) {
            tab.addEventListener('click', function () {
                switchTeiMode(tab.getAttribute('data-mode'));
            });
        });

        ZBZ.$('#entity-toggle').addEventListener('click', function () { toggleEntitySidebar(); });
        ZBZ.$('#entity-close').addEventListener('click', function () { toggleEntitySidebar(); });
    }

    // Auto-init when script loads (DOM is ready since script is at bottom of body)
    init();

    // ---- Public API ----
    ZBZ.TeiViewer = {
        loadTei: loadTei,
        switchMode: switchTeiMode,
        toggleEntitySidebar: toggleEntitySidebar
    };
})();
