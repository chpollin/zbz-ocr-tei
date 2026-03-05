/**
 * ZBZ OCR Pipeline -- PAGE-XML Viewer Module
 * Handles PAGE-XML region rendering, XML syntax highlighting, and METS display.
 * Depends on: shared.js (ZBZ namespace)
 */
(function () {
    'use strict';

    var pageState = {
        mode: 'regions',
        currentXml: null,
        docId: null,
        page: null,
        regionsDone: false,
        xmlDone: false,
        metsDone: false
    };

    // ---- Tab Switching ----
    function switchPageMode(mode) {
        pageState.mode = mode;
        ZBZ.$$('.page-tab').forEach(function (tab) {
            tab.classList.toggle('active', tab.getAttribute('data-mode') === mode);
        });
        ZBZ.$('#page-regions').classList.toggle('hidden', mode !== 'regions');
        ZBZ.$('#page-xml-view').classList.toggle('hidden', mode !== 'xml');
        ZBZ.$('#page-mets-view').classList.toggle('hidden', mode !== 'mets');

        if (mode === 'regions' && !pageState.regionsDone && pageState.currentXml) {
            renderRegions(pageState.currentXml);
        } else if (mode === 'xml' && !pageState.xmlDone && pageState.currentXml) {
            renderPageXml(pageState.currentXml);
        } else if (mode === 'mets' && !pageState.metsDone) {
            loadMets(pageState.docId);
        }
    }

    // ---- Load PAGE-XML Data ----
    async function loadPage(docId, page) {
        pageState.docId = docId;
        pageState.page = page;
        pageState.regionsDone = false;
        pageState.xmlDone = false;
        pageState.metsDone = false;
        pageState.currentXml = null;

        ZBZ.$('#page-regions').innerHTML = '<div class="empty-state">Lade...</div>';

        var xml = await ZBZ.fetchPageXml(docId, page);
        pageState.currentXml = xml;

        if (!xml) {
            ZBZ.$('#page-regions').innerHTML =
                '<div class="empty-state">Keine PAGE-XML-Daten fuer diese Seite.</div>';
            ZBZ.$('#page-xml-code').textContent = '';
            return;
        }

        if (pageState.mode === 'regions') {
            renderRegions(xml);
        } else if (pageState.mode === 'xml') {
            renderPageXml(xml);
        } else if (pageState.mode === 'mets') {
            loadMets(docId);
        }
    }

    function parsePageXml(xml) {
        return ZBZ.parseXml(xml);
    }

    function extractStructureType(customAttr) {
        var m = customAttr ? customAttr.match(/structure\s*\{type:(\w+);\}/) : null;
        return m ? m[1] : 'unknown';
    }

    function parseCoordsPoints(pointsStr) {
        if (!pointsStr) return null;
        var parts = pointsStr.split(/\s+/);
        var xs = [];
        var ys = [];
        for (var i = 0; i < parts.length; i++) {
            var pair = parts[i].split(',');
            xs.push(parseInt(pair[0]));
            ys.push(parseInt(pair[1]));
        }
        var minX = Math.min.apply(null, xs);
        var minY = Math.min.apply(null, ys);
        var maxX = Math.max.apply(null, xs);
        var maxY = Math.max.apply(null, ys);
        return { x: minX, y: minY, w: maxX - minX, h: maxY - minY };
    }

    var REGION_TYPE_INFO = {
        heading:   { label: 'Heading',   cls: 'page-region-heading' },
        paragraph: { label: 'Absatz',    cls: 'page-region-paragraph' },
        footnote:  { label: 'Fussnote',  cls: 'page-region-footnote' },
        caption:   { label: 'Caption',   cls: 'page-region-caption' },
        unknown:   { label: 'Unbekannt', cls: 'page-region-unknown' }
    };

    // ---- Rendered "Regionen" View ----
    function renderRegions(xml) {
        var container = ZBZ.$('#page-regions');
        container.innerHTML = '';
        pageState.regionsDone = true;

        var doc = parsePageXml(xml);
        if (!doc) {
            container.innerHTML = '<div class="empty-state">XML-Parse-Fehler</div>';
            return;
        }

        var pageEl = doc.querySelector('Page');
        if (!pageEl) {
            container.innerHTML = '<div class="empty-state">Kein &lt;Page&gt; Element</div>';
            return;
        }

        var imgW = parseInt(pageEl.getAttribute('imageWidth')) || 0;
        var imgH = parseInt(pageEl.getAttribute('imageHeight')) || 0;

        var metaHtml = '<div class="page-meta">' +
            '<span class="page-meta-item">' +
            '<span class="info-label">Bild</span> ' +
            ZBZ.esc(pageEl.getAttribute('imageFilename') || '') +
            '</span>' +
            '<span class="page-meta-item">' +
            '<span class="info-label">Groesse</span> ' +
            imgW + ' x ' + imgH + ' px' +
            '</span>' +
            '</div>';
        container.innerHTML = metaHtml;

        var regions = doc.querySelectorAll('TextRegion');
        if (regions.length === 0) {
            container.innerHTML += '<div class="empty-state">Keine TextRegions</div>';
            return;
        }

        var summary = document.createElement('div');
        summary.className = 'page-region-summary';
        summary.textContent = regions.length + ' Regionen';
        container.appendChild(summary);

        for (var i = 0; i < regions.length; i++) {
            var region = regions[i];
            var regId = region.getAttribute('id') || '';
            var customAttr = region.getAttribute('custom') || '';
            var structType = extractStructureType(customAttr);
            var typeInfo = REGION_TYPE_INFO[structType] || REGION_TYPE_INFO.unknown;

            var coordsEl = region.querySelector('Coords');
            var bbox = coordsEl ? parseCoordsPoints(coordsEl.getAttribute('points')) : null;

            var textLine = region.querySelector('TextLine TextEquiv Unicode');
            var text = textLine ? textLine.textContent.trim() : '';

            var card = document.createElement('div');
            card.className = 'page-region-card ' + typeInfo.cls;

            var header = '<div class="page-region-header">' +
                '<span class="page-region-index">#' + (i + 1) + '</span>' +
                '<span class="page-region-type">' + typeInfo.label + '</span>' +
                '<span class="page-region-id">' + ZBZ.esc(regId) + '</span>';
            if (bbox) {
                header += '<span class="page-region-coords">' +
                    bbox.x + ',' + bbox.y + ' ' + bbox.w + 'x' + bbox.h +
                    '</span>';
            }
            header += '</div>';

            var body = '';
            if (text) {
                var preview = text.length > 120 ? text.substring(0, 120) + '...' : text;
                body = '<div class="page-region-text">' + ZBZ.esc(preview) + '</div>';
            } else {
                body = '<div class="page-region-text page-region-empty">(kein Text)</div>';
            }

            card.innerHTML = header + body;
            container.appendChild(card);
        }
    }

    // ---- XML View ----
    function renderPageXml(xml) {
        pageState.xmlDone = true;
        ZBZ.$('#page-xml-code').innerHTML = ZBZ.highlightXml(xml);
    }

    // ---- METS View ----
    async function loadMets(docId) {
        pageState.metsDone = true;
        var metsContainer = ZBZ.$('#page-mets-code');
        metsContainer.innerHTML = '<span style="color:var(--text-muted)">Lade METS...</span>';

        var metsXml = await ZBZ.fetchMetsXml(docId);
        if (metsXml) {
            metsContainer.innerHTML = ZBZ.highlightXml(metsXml);
        } else {
            metsContainer.innerHTML =
                '<span style="color:var(--text-muted);font-style:italic">Keine METS-Datei vorhanden.</span>';
        }
    }

    // ---- Init ----
    function init() {
        ZBZ.$$('.page-tab').forEach(function (tab) {
            tab.addEventListener('click', function () {
                switchPageMode(tab.getAttribute('data-mode'));
            });
        });
    }

    init();

    // ---- Public API ----
    ZBZ.PageViewer = {
        loadPage: loadPage,
        switchMode: switchPageMode
    };
})();
