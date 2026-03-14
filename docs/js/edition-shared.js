/**
 * ZBZ Edition – Shared Module
 * Navigation, Data Loading, Utilities, Card Rendering.
 * Namespace: ZBZ.Edition (ES6+, IIFE)
 */
(function () {
    'use strict';

    // --- Ensure ZBZ namespace + log ---
    window.ZBZ = window.ZBZ || {};
    const _logStyles = 'color:#1e3a5f;font-weight:600';
    function _log(mod, msg) { console.log(`%c[ZBZ:${mod}]%c ${msg}`, _logStyles, ''); }
    if (!ZBZ.log) ZBZ.log = _log;

    // --- DOM helpers ---
    function $(sel, ctx) { return (ctx || document).querySelector(sel); }
    function $$(sel, ctx) { return Array.prototype.slice.call((ctx || document).querySelectorAll(sel)); }

    function esc(s) {
        if (!s) return '';
        return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
    }

    function fmtNum(n) {
        if (n == null) return '-';
        return String(n).replace(/\B(?=(\d{3})+(?!\d))/g, '.');
    }

    function getParam(key) { return new URLSearchParams(window.location.search).get(key); }

    function setParams(obj) {
        const u = new URLSearchParams(window.location.search);
        Object.keys(obj).forEach((k) => {
            if (obj[k] == null) u.delete(k); else u.set(k, obj[k]);
        });
        const s = u.toString();
        history.replaceState(null, '', window.location.pathname + (s ? `?${s}` : ''));
    }

    /** Sanitize doc ID: only digits allowed. */
    function sanitizeDocId(id) {
        if (!id) return null;
        const clean = String(id).replace(/[^0-9]/g, '');
        return clean || null;
    }

    // --- XML helpers ---
    function parseXml(xml) {
        if (!xml) return null;
        try {
            const clean = xml.replace(/\s+xmlns\s*=\s*"[^"]*"/g, '');
            const doc = new DOMParser().parseFromString(clean, 'text/xml');
            if (doc.querySelector('parsererror')) return null;
            return doc;
        } catch (e) {
            return null;
        }
    }

    function highlightXml(xml) {
        return esc(xml)
            .replace(/(&lt;\?[\s\S]*?\?&gt;)/g, '<span class="xml-decl">$1</span>')
            .replace(/(&lt;!--[\s\S]*?--&gt;)/g, '<span class="xml-comment">$1</span>')
            .replace(/(&lt;\/?)([\w:.-]+)/g, '$1<span class="xml-tag">$2</span>')
            .replace(/([\w:.-]+)(=)(&quot;[^&]*&quot;)/g,
                '<span class="xml-attr-name">$1</span>$2<span class="xml-attr-value">$3</span>');
    }

    function padPage(p) {
        const n = parseInt(p, 10);
        if (isNaN(n) || n < 0) return '000';
        return ('00' + n).slice(-3);
    }

    // --- Catalog Data ---
    let _catalogCache = null;

    function loadCatalog() {
        if (_catalogCache) return Promise.resolve(_catalogCache);
        return fetch('data/catalog.json')
            .then((r) => r.json())
            .then((data) => {
                _catalogCache = data;
                const docs = data.documents ? data.documents.length : 0;
                _log('Catalog', `${docs} Dokumente geladen`);
                return data;
            })
            .catch(() => {
                _log('Catalog', 'FEHLER: catalog.json nicht geladen');
                return null;
            });
    }

    // --- Navigation (generated from JS to avoid HTML duplication) ---
    const NAV_ITEMS = [
        { href: 'index.html', label: 'Start' },
        { href: 'catalog.html', label: 'Katalog' },
        { href: 'reader.html', label: 'Leseansicht' },
        { href: 'about.html', label: 'Projekt' },
        { href: 'infrastruktur/index.html', label: 'Epist. Infrastruktur' }
    ];
    const ICON_HAMBURGER = '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 12h18M3 6h18M3 18h18"/></svg>';

    function renderNav() {
        const target = $('#ed-nav-slot');
        if (!target) return;

        const path = window.location.pathname;
        const isInfra = path.indexOf('/infrastruktur/') > -1;
        // Fix hrefs for infrastruktur pages (prefix ../)
        const hrefPrefix = isInfra ? '../' : '';
        const links = NAV_ITEMS.map((item) => {
            const href = hrefPrefix + item.href;
            let active = false;
            if (item.href.indexOf('infrastruktur/') === 0) {
                active = isInfra;
            } else if (!isInfra) {
                active = path.indexOf(item.href) > -1 && item.href !== 'index.html';
                if (item.href === 'index.html') {
                    active = path.match(/\/index\.html$/) !== null || path.match(/\/docs\/?$/) !== null;
                }
            }
            return `<li><a href="${href}"${active ? ' class="active"' : ''}>${item.label}</a></li>`;
        }).join('');

        target.innerHTML =
            `<div class="ed-nav-inner">` +
            `<a href="${hrefPrefix}index.html" class="ed-nav-brand">Nachlass Hersch</a>` +
            `<button class="ed-nav-hamburger" id="nav-hamburger" aria-label="Navigation" aria-expanded="false" aria-controls="ed-nav-links">${ICON_HAMBURGER}</button>` +
            `<ul class="ed-nav-links" id="ed-nav-links">${links}</ul></div>`;
    }

    function renderFooter() {
        const target = $('#ed-footer-slot');
        if (!target) return;
        const isInfra = window.location.pathname.indexOf('/infrastruktur/') > -1;
        const p = isInfra ? '../' : '';
        target.innerHTML =
            `<div class="ed-footer-links">` +
            `<a href="${p}index.html">Startseite</a>` +
            `<a href="${p}catalog.html">Katalog</a>` +
            `<a href="${p}about.html">Projekt</a>` +
            `<a href="${p}infrastruktur/index.html">Epist. Infrastruktur</a>` +
            `</div>` +
            `<p>Zentralbibliothek Zuerich &middot; DHCraft &middot; 2026</p>`;
    }

    function initNav() {
        const hamburger = $('#nav-hamburger');
        const links = $('#ed-nav-links');
        if (hamburger && links) {
            hamburger.addEventListener('click', () => {
                const open = links.classList.toggle('open');
                hamburger.setAttribute('aria-expanded', String(open));
            });
        }
    }

    // --- Entity Index (Reconciliation-verifiziert) ---
    let _entityIndexCache = null;

    function loadEntityIndex() {
        if (_entityIndexCache) return Promise.resolve(_entityIndexCache);
        return fetch('data/entity_index.json')
            .then((r) => r.json())
            .then((data) => {
                _entityIndexCache = data;
                _log('EntityIndex', `${Object.keys(data).length} Entitaeten geladen`);
                return data;
            })
            .catch(() => {
                _log('EntityIndex', 'nicht verfuegbar (optional)');
                _entityIndexCache = {};
                return {};
            });
    }

    function lookupEntity(ref) {
        if (!_entityIndexCache || !ref) return null;
        // #zbz-p.1 -> zbz-p.1
        const id = ref.charAt(0) === '#' ? ref.slice(1) : ref;
        return _entityIndexCache[id] || null;
    }

    // --- Image/TEI Paths ---
    function imagePath(docId, page) {
        return `images/${docId}/${docId}_p${padPage(page)}.png`;
    }

    function fetchTei(docId, page) {
        const paths = [
            `data/examples/${docId}/${docId}_p${page}.xml`,
            `../output/tei/${docId}_p${page}.xml`
        ];
        return _fetchFirstOk(paths);
    }

    function _fetchFirstOk(urls) {
        if (!urls.length) return Promise.resolve(null);
        return fetch(urls[0]).then((r) => {
            if (r.ok) return r.text();
            return _fetchFirstOk(urls.slice(1));
        }).catch(() => _fetchFirstOk(urls.slice(1)));
    }

    // --- Debounce ---
    function debounce(fn, ms) {
        let timer;
        return function () {
            const args = arguments;
            const ctx = this;
            clearTimeout(timer);
            timer = setTimeout(function () { fn.apply(ctx, args); }, ms);
        };
    }

    // --- Card Rendering (shared between landing + catalog) ---
    function buildCardHtml(doc, opts) {
        const docId = doc.id;
        const title = doc.title || `Dokument ${docId}`;
        const imgSrc = imagePath(docId, 1);
        const placeholder = `<div class='ed-card-img-placeholder'>Dok. ${esc(docId)}</div>`;

        let html = `<a href="reader.html?doc=${esc(docId)}" class="ed-card">`;
        html += `<img class="ed-card-img" src="${imgSrc}" alt="${esc(title)}" loading="lazy" onerror="this.outerHTML='${placeholder.replace(/'/g, "\\'")}'">`;
        html += '<div class="ed-card-body">';
        html += `<div class="ed-card-title">${esc(title)}</div>`;
        html += '<p class="ed-card-meta">';
        if (doc.author) html += esc(doc.author);
        if (doc.date) html += (doc.author ? ' &middot; ' : '') + esc(doc.date);
        if (opts && opts.showPages && doc.page_count) html += ` &middot; ${doc.page_count} S.`;
        html += '</p>';
        html += `<span class="ed-badge ed-badge-type">${esc(TYPE_LABELS[doc.type] || doc.type)}</span>`;
        if (doc.lang) html += ` <span class="ed-badge ed-badge-lang">${esc(doc.lang)}</span>`;
        if (doc.entity_count) html += ` <span class="ed-badge ed-badge-ner" title="${doc.entity_count} Entitaeten">${doc.entity_count} Ent.</span>`;
        if (doc.demo) html += ' <span class="ed-badge ed-badge-demo">Demo</span>';
        html += '</div></a>';
        return html;
    }

    // --- Labels ---
    const LANG_LABELS = {
        'FR': 'Franzoesisch', 'DE': 'Deutsch', 'EN': 'Englisch',
        'IT': 'Italienisch', 'DE/FR': 'Deutsch/Franz.', '?': 'Unbestimmt',
        'ES': 'Spanisch', 'PT': 'Portugiesisch', 'NL': 'Niederlaendisch',
        'PL': 'Polnisch', 'HU': 'Ungarisch', 'EL': 'Griechisch',
        'LA': 'Latein', 'RU': 'Russisch', 'SV': 'Schwedisch',
        '-': 'Unbekannt'
    };
    const TYPE_LABELS = {
        'A': 'Einspaltig', 'B': 'Zweispaltig',
        'C': 'Monografie', 'D': 'Spezialformat', '-': 'Unklassifiziert'
    };
    const PUB_FORM_LABELS = {
        'journalArticle': 'Zeitschriftenartikel', 'book': 'Buch',
        'bookSection': 'Buchkapitel', 'encyclopedia': 'Lexikonartikel',
        'brochure': 'Broschure', 'interview': 'Interview',
        'anthology': 'Anthologie', 'other': 'Sonstige'
    };

    // --- Init ---
    function init() {
        renderNav();
        renderFooter();
        initNav();
        const page = window.location.pathname.split('/').pop() || 'index.html';
        _log('Edition', `${page} | nav + footer ready`);
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    // --- Public API ---
    ZBZ.Edition = {
        $: $,
        $$: $$,
        esc: esc,
        fmtNum: fmtNum,
        getParam: getParam,
        setParams: setParams,
        sanitizeDocId: sanitizeDocId,
        parseXml: parseXml,
        highlightXml: highlightXml,
        padPage: padPage,
        loadCatalog: loadCatalog,
        imagePath: imagePath,
        fetchTei: fetchTei,
        loadEntityIndex: loadEntityIndex,
        lookupEntity: lookupEntity,
        debounce: debounce,
        buildCardHtml: buildCardHtml,
        LANG_LABELS: LANG_LABELS,
        TYPE_LABELS: TYPE_LABELS,
        PUB_FORM_LABELS: PUB_FORM_LABELS
    };
})();
