/**
 * ZBZ Core — Shared Foundation Layer
 * Canonical utilities used by both Edition and Infrastructure pages.
 * Loaded FIRST on every page, before edition-shared.js / infra-shared.js.
 *
 * Provides: DOM helpers, URL state, XML utils, fetch helpers, formatting,
 *           debounce, throttleRAF, logging, entity index, labels, Cache, toast.
 *
 * Namespace: window.ZBZ (merged non-destructively)
 */
(function () {
    'use strict';

    const _prev = window.ZBZ || {};
    const ZBZ = {};

    // ---- Logging ----
    const _logStyles = 'color:#2C2825;font-weight:600';
    ZBZ.log = function (mod, msg) {
        console.log('%c[ZBZ:' + mod + ']%c ' + msg, _logStyles, '');
    };

    // ---- DOM Helpers ----
    ZBZ.$ = function (sel, ctx) { return (ctx || document).querySelector(sel); };
    ZBZ.$$ = function (sel, ctx) { return Array.prototype.slice.call((ctx || document).querySelectorAll(sel)); };

    ZBZ.esc = function (s) {
        if (s == null) return '';
        return String(s)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;');
    };

    // ---- URL State ----
    ZBZ.getParam = function (key) {
        return new URLSearchParams(window.location.search).get(key);
    };

    ZBZ.setParams = function (obj) {
        const u = new URLSearchParams(window.location.search);
        Object.keys(obj).forEach(function (k) {
            if (obj[k] == null) u.delete(k); else u.set(k, obj[k]);
        });
        const s = u.toString();
        history.replaceState(null, '', window.location.pathname + (s ? '?' + s : ''));
    };

    // Convenience single-key setter
    ZBZ.setParam = function (key, value) {
        const o = {};
        o[key] = value;
        ZBZ.setParams(o);
    };

    ZBZ.sanitizeDocId = function (id) {
        if (!id) return null;
        const clean = String(id).replace(/[^0-9]/g, '');
        return clean || null;
    };

    // ---- Auto-detect base path ----
    ZBZ._basePath = window.location.pathname.indexOf('/infrastruktur/') > -1 ? '../' : '';

    // ---- XML Helpers ----
    ZBZ.parseXml = function (xml) {
        if (!xml) return null;
        try {
            const cleaned = xml
                .replace(/\s+xmlns(:\w+)?\s*=\s*["'][^"']*["']/g, '')
                .replace(/\s+xsi:\w+\s*=\s*["'][^"']*["']/g, '');
            const doc = new DOMParser().parseFromString(cleaned, 'text/xml');
            if (doc.querySelector('parsererror')) return null;
            return doc;
        } catch (e) { return null; }
    };

    ZBZ.highlightXml = function (xml) {
        let s = ZBZ.esc(xml);
        s = s.replace(/(&lt;\?[\s\S]*?\?&gt;)/g, '<span class="xml-decl">$1</span>');
        s = s.replace(/(&lt;!--[\s\S]*?--&gt;)/g, '<span class="xml-comment">$1</span>');
        s = s.replace(
            /(&lt;\/?)([\w:.-]+)/g,
            '$1<span class="xml-tag">$2</span>'
        );
        s = s.replace(
            /([\w:.-]+)(=)(&quot;[^&]*&quot;)/g,
            '<span class="xml-attr-name">$1</span>$2<span class="xml-attr-value">$3</span>'
        );
        return s;
    };

    // ---- Formatting ----
    ZBZ.fmtNum = function (n) {
        if (n == null) return '-';
        return String(n).replace(/\B(?=(\d{3})+(?!\d))/g, '.');
    };

    ZBZ.fmtPct = function (v, decimals) {
        if (v == null) return '-';
        return (v * 100).toFixed(decimals != null ? decimals : 1) + '%';
    };

    ZBZ.formatDate = function (isoStr) {
        if (!isoStr) return '-';
        return isoStr.replace('T', ' ').slice(0, 19);
    };

    ZBZ.padPage = function (p) {
        const n = parseInt(p, 10);
        if (isNaN(n) || n < 0) return '000';
        return ('00' + n).slice(-3);
    };

    ZBZ.imagePath = function (docId, page) {
        return ZBZ._basePath + 'images/' + docId + '/' + docId + '_p' + ZBZ.padPage(page) + '.png';
    };

    // ---- Fetch Utilities ----
    ZBZ.fetchFirstOk = function (urls) {
        if (!urls || !urls.length) return Promise.resolve(null);
        return fetch(urls[0]).then(function (r) {
            if (r.ok) return r.text();
            return ZBZ.fetchFirstOk(urls.slice(1));
        }).catch(function () { return ZBZ.fetchFirstOk(urls.slice(1)); });
    };

    ZBZ.fetchJSON = function (path) {
        return fetch(path)
            .then(function (r) { if (!r.ok) return null; return r.json(); })
            .catch(function () { return null; });
    };

    // ---- Debounce / Throttle ----
    ZBZ.debounce = function (fn, ms) {
        let timer;
        return function () {
            const args = arguments, ctx = this;
            clearTimeout(timer);
            timer = setTimeout(function () { fn.apply(ctx, args); }, ms);
        };
    };

    ZBZ.throttleRAF = function (fn) {
        let scheduled = false;
        return function () {
            if (scheduled) return;
            scheduled = true;
            const args = arguments, ctx = this;
            requestAnimationFrame(function () {
                scheduled = false;
                fn.apply(ctx, args);
            });
        };
    };

    // ---- Toast Notifications ----
    ZBZ.toast = function (message, type) {
        type = type || 'info';
        let container = document.getElementById('zbz-toast-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'zbz-toast-container';
            container.style.cssText = 'position:fixed;top:70px;right:20px;z-index:10000;display:flex;flex-direction:column;gap:8px;pointer-events:none;';
            document.body.appendChild(container);
        }
        const el = document.createElement('div');
        el.className = 'ed-toast ed-toast-' + type;
        el.textContent = message;
        container.appendChild(el);
        requestAnimationFrame(function () { el.classList.add('ed-toast-visible'); });
        setTimeout(function () {
            el.classList.remove('ed-toast-visible');
            setTimeout(function () { el.remove(); }, 300);
        }, 3000);
    };

    // ---- LRU Cache ----
    ZBZ.Cache = function (options) {
        options = options || {};
        this._maxSize = options.maxSize || 100;
        this._map = new Map();
    };
    ZBZ.Cache.prototype.get = function (key) {
        if (!this._map.has(key)) return undefined;
        const val = this._map.get(key);
        // Move to end (most recently used)
        this._map.delete(key);
        this._map.set(key, val);
        return val;
    };
    ZBZ.Cache.prototype.set = function (key, value) {
        if (this._map.has(key)) this._map.delete(key);
        this._map.set(key, value);
        if (this._map.size > this._maxSize) {
            // Evict oldest (first entry)
            const oldest = this._map.keys().next().value;
            this._map.delete(oldest);
        }
    };
    ZBZ.Cache.prototype.has = function (key) { return this._map.has(key); };
    ZBZ.Cache.prototype.delete = function (key) { return this._map.delete(key); };
    ZBZ.Cache.prototype.clear = function () { this._map.clear(); };
    ZBZ.Cache.prototype.size = function () { return this._map.size; };

    // ---- Entity Index ----
    let _entityIndexCache = null;

    ZBZ.loadEntityIndex = function () {
        if (_entityIndexCache) return Promise.resolve(_entityIndexCache);
        return fetch(ZBZ._basePath + 'data/entity_index.json')
            .then(function (r) { return r.json(); })
            .then(function (data) {
                _entityIndexCache = data;
                ZBZ.log('EntityIndex', Object.keys(data).length + ' Entitaeten geladen');
                return data;
            })
            .catch(function () {
                ZBZ.log('EntityIndex', 'nicht verfuegbar (optional)');
                _entityIndexCache = {};
                return {};
            });
    };

    ZBZ.lookupEntity = function (ref) {
        if (!_entityIndexCache || !ref) return null;
        const id = ref.charAt(0) === '#' ? ref.slice(1) : ref;
        return _entityIndexCache[id] || null;
    };

    // ---- Shared Labels ----
    ZBZ.PUB_FORM_LABELS = {
        journalArticle: 'Zeitschriftenartikel', book: 'Buch',
        bookSection: 'Buchkapitel', encyclopedia: 'Lexikonartikel',
        brochure: 'Broschure', interview: 'Interview',
        anthology: 'Anthologie', other: 'Sonstige'
    };

    // ---- Table Sorting ----
    ZBZ.makeSortable = function (tableEl) {
        if (!tableEl) return;
        const headers = ZBZ.$$('th.sortable', tableEl);
        const tbody = ZBZ.$('tbody', tableEl);
        if (!headers.length || !tbody) return;
        let sortCol = null, sortAsc = true;
        headers.forEach(function (th) {
            th.addEventListener('click', function () {
                const col = th.cellIndex;
                if (sortCol === col) sortAsc = !sortAsc;
                else { sortCol = col; sortAsc = true; }
                headers.forEach(function (h) { h.classList.remove('sort-asc', 'sort-desc'); });
                th.classList.add(sortAsc ? 'sort-asc' : 'sort-desc');
                const rows = Array.prototype.slice.call(tbody.rows);
                rows.sort(function (a, b) {
                    const aEl = a.cells[col], bEl = b.cells[col];
                    if (!aEl || !bEl) return 0;
                    const aK = aEl.dataset.sort != null ? aEl.dataset.sort : aEl.textContent.trim();
                    const bK = bEl.dataset.sort != null ? bEl.dataset.sort : bEl.textContent.trim();
                    const aN = parseFloat(aK), bN = parseFloat(bK);
                    if (!isNaN(aN) && !isNaN(bN)) return sortAsc ? aN - bN : bN - aN;
                    return sortAsc ? aK.localeCompare(bK) : bK.localeCompare(aK);
                });
                rows.forEach(function (r) { tbody.appendChild(r); });
            });
        });
    };

    // ---- Merge into namespace (non-destructive) ----
    window.ZBZ = ZBZ;
    if (_prev) {
        Object.keys(_prev).forEach(function (k) {
            if (!(k in ZBZ)) ZBZ[k] = _prev[k];
        });
    }
    ZBZ.log('Core', 'zbz-core.js ready | basePath="' + (ZBZ._basePath || '.') + '"');
})();
