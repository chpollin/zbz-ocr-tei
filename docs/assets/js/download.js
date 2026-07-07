/**
 * download.js - File download trigger
 *
 * Offers content as a download. Persistence is manual (no server backend).
 *
 * Namespace: ZBZ.Download
 */
(function () {
    'use strict';

    /**
     * Trigger a browser download.
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
     * Save layout regions as JSON.
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
     * Save OCR/transcription as Markdown. Canonical name without suffix so the file
     * is read directly by the loader (scripts/core/loaders.py, highest priority)
     * when placed manually in output/ocr_curated/.
     */
    function text(doc, page, content) {
        const fname = `${doc}_p${page}.md`;
        trigger(fname, content, 'text/markdown;charset=utf-8');
    }

    /**
     * Save TEI as XML.
     */
    function tei(doc, content, suffix) {
        const fname = `${doc}${suffix ? '_' + suffix : '_curated'}.xml`;
        trigger(fname, content, 'application/xml;charset=utf-8');
    }

    /**
     * Save the per-object manifest (workflow status + history + blank pages) as JSON.
     * The file must be copied manually to output/tei_final/{doc}_manifest.json;
     * then run `python -m scripts.generate_edition_data --mirror-only` to update the mirror.
     */
    function manifest(doc, manifestObj) {
        const fname = `${doc}_manifest.json`;
        trigger(fname, JSON.stringify(manifestObj, null, 2), 'application/json;charset=utf-8');
    }

    ZBZ.Download = { trigger, layout, text, tei, manifest };
    ZBZ.log('Download', 'ready');
})();
