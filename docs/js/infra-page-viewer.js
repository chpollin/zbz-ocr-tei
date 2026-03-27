/**
 * ZBZ OCR Pipeline -- PAGE-XML Viewer Module
 * Handles PAGE-XML region rendering, XML syntax highlighting, and METS display.
 * Depends on: shared.js (ZBZ namespace)
 */
(function () {
    'use strict';

    const pageState = {
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
        ZBZ.$$('.page-tab').forEach((tab) => {
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

        const xml = await ZBZ.fetchPageXml(docId, page);
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
        const m = customAttr ? customAttr.match(/structure\s*\{type:(\w+);\}/) : null;
        return m ? m[1] : 'unknown';
    }

    function parseCoordsPoints(pointsStr) {
        if (!pointsStr) return null;
        const parts = pointsStr.split(/\s+/);
        const xs = [];
        const ys = [];
        for (let i = 0; i < parts.length; i++) {
            const pair = parts[i].split(',');
            xs.push(parseInt(pair[0]));
            ys.push(parseInt(pair[1]));
        }
        const minX = Math.min.apply(null, xs);
        const minY = Math.min.apply(null, ys);
        const maxX = Math.max.apply(null, xs);
        const maxY = Math.max.apply(null, ys);
        return { x: minX, y: minY, w: maxX - minX, h: maxY - minY };
    }

    const REGION_TYPE_INFO = {
        heading:   { label: 'Heading',   cls: 'page-region-heading' },
        paragraph: { label: 'Absatz',    cls: 'page-region-paragraph' },
        footnote:  { label: 'Fussnote',  cls: 'page-region-footnote' },
        caption:   { label: 'Caption',   cls: 'page-region-caption' },
        unknown:   { label: 'Unbekannt', cls: 'page-region-unknown' }
    };

    // ---- Rendered "Regionen" View ----
    function renderRegions(xml) {
        const container = ZBZ.$('#page-regions');
        container.innerHTML = '';
        pageState.regionsDone = true;

        const doc = parsePageXml(xml);
        if (!doc) {
            container.innerHTML = '<div class="empty-state">XML-Parse-Fehler</div>';
            return;
        }

        const pageEl = doc.querySelector('Page');
        if (!pageEl) {
            container.innerHTML = '<div class="empty-state">Kein &lt;Page&gt; Element</div>';
            return;
        }

        const imgW = parseInt(pageEl.getAttribute('imageWidth')) || 0;
        const imgH = parseInt(pageEl.getAttribute('imageHeight')) || 0;

        const metaHtml = `<div class="page-meta">` +
            `<span class="page-meta-item">` +
            `<span class="info-label">Bild</span> ` +
            ZBZ.esc(pageEl.getAttribute('imageFilename') || '') +
            `</span>` +
            `<span class="page-meta-item">` +
            `<span class="info-label">Groesse</span> ` +
            `${imgW} x ${imgH} px` +
            `</span>` +
            `</div>`;
        container.innerHTML = metaHtml;

        const regions = doc.querySelectorAll('TextRegion');
        if (regions.length === 0) {
            container.innerHTML += '<div class="empty-state">Keine TextRegions</div>';
            return;
        }

        const summary = document.createElement('div');
        summary.className = 'page-region-summary';
        summary.textContent = regions.length + ' Regionen';
        container.appendChild(summary);

        for (let i = 0; i < regions.length; i++) {
            const region = regions[i];
            const regId = region.getAttribute('id') || '';
            const customAttr = region.getAttribute('custom') || '';
            const structType = extractStructureType(customAttr);
            const typeInfo = REGION_TYPE_INFO[structType] || REGION_TYPE_INFO.unknown;

            const coordsEl = region.querySelector('Coords');
            const bbox = coordsEl ? parseCoordsPoints(coordsEl.getAttribute('points')) : null;

            const textLine = region.querySelector('TextLine TextEquiv Unicode');
            const text = textLine ? textLine.textContent.trim() : '';

            const card = document.createElement('div');
            card.className = 'page-region-card ' + typeInfo.cls;

            let header = `<div class="page-region-header">` +
                `<span class="page-region-index">#${i + 1}</span>` +
                `<span class="page-region-type">${typeInfo.label}</span>` +
                `<span class="page-region-id">${ZBZ.esc(regId)}</span>`;
            if (bbox) {
                header += `<span class="page-region-coords">` +
                    `${bbox.x},${bbox.y} ${bbox.w}x${bbox.h}` +
                    `</span>`;
            }
            header += '</div>';

            let body = '';
            if (text) {
                const preview = text.length > 120 ? text.substring(0, 120) + '...' : text;
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
        const metsContainer = ZBZ.$('#page-mets-code');
        metsContainer.innerHTML = '<span style="color:var(--text-muted)">Lade METS...</span>';

        const metsXml = await ZBZ.fetchMetsXml(docId);
        if (metsXml) {
            metsContainer.innerHTML = ZBZ.highlightXml(metsXml);
        } else {
            metsContainer.innerHTML =
                '<span style="color:var(--text-muted);font-style:italic">Keine METS-Datei vorhanden.</span>';
        }
    }

    // ---- Init ----
    function init() {
        ZBZ.$$('.page-tab').forEach((tab) => {
            tab.addEventListener('click', () => {
                switchPageMode(tab.getAttribute('data-mode'));
            });
        });
    }

    init();

    ZBZ.log('PageViewer', 'ready (regions/xml/mets)');

    // ---- Public API ----
    ZBZ.PageViewer = {
        loadPage: loadPage,
        switchMode: switchPageMode
    };
})();
