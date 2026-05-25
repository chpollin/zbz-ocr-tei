/**
 * download.js — Datei-Download-Trigger
 *
 * Bietet Inhalte als Download an. Persistenz erfolgt manuell durch den Nutzer
 * (kein Server-Backend).
 *
 * Namespace: ZBZ.Download
 */
(function () {
    'use strict';

    /**
     * Loest einen Browser-Download aus.
     * @param {string} filename
     * @param {string} content
     * @param {string} mime
     */
    function trigger(filename, content, mime) {
        const blob = new Blob([content], { type: mime || 'text/plain;charset=utf-8' });
        const url = URL.createObjectURL(blob);
        const a = ZBZ.el('a', { attrs: { href: url, download: filename } });
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        setTimeout(() => URL.revokeObjectURL(url), 1000);
        ZBZ.log('Download', filename + ' (' + (content.length / 1024).toFixed(1) + ' KB)');
    }

    /**
     * Speichert Layout-Regions als JSON.
     */
    function layout(doc, page, regions, sourceMeta) {
        const out = Object.assign({}, sourceMeta || {}, {
            regions: regions,
            curated: true,
            curated_at: new Date().toISOString()
        });
        const fname = `${doc}_p${ZBZ.padPage(page)}_layout_curated.json`;
        trigger(fname, JSON.stringify(out, null, 2), 'application/json;charset=utf-8');
    }

    /**
     * Speichert OCR/Transkription als Markdown.
     */
    function text(doc, page, content) {
        const fname = `${doc}_p${page}_curated.md`;
        trigger(fname, content, 'text/markdown;charset=utf-8');
    }

    /**
     * Speichert TEI als XML.
     */
    function tei(doc, content, suffix) {
        const fname = `${doc}${suffix ? '_' + suffix : '_curated'}.xml`;
        trigger(fname, content, 'application/xml;charset=utf-8');
    }

    ZBZ.Download = { trigger, layout, text, tei };
    ZBZ.log('Download', 'ready');
})();
