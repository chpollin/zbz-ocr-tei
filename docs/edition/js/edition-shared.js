/**
 * ZBZ Edition – Shared Module
 * Navigation, Dark Mode, Data Loading, Utilities, Card Rendering.
 * Namespace: ZBZ.Edition (ES5, IIFE)
 */
(function () {
    'use strict';

    // --- Ensure ZBZ namespace ---
    window.ZBZ = window.ZBZ || {};

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
        var u = new URLSearchParams(window.location.search);
        Object.keys(obj).forEach(function (k) {
            if (obj[k] == null) u.delete(k); else u.set(k, obj[k]);
        });
        var s = u.toString();
        history.replaceState(null, '', window.location.pathname + (s ? '?' + s : ''));
    }

    /** Sanitize doc ID: only digits allowed. */
    function sanitizeDocId(id) {
        if (!id) return null;
        var clean = String(id).replace(/[^0-9]/g, '');
        return clean || null;
    }

    // --- XML helpers ---
    function parseXml(xml) {
        if (!xml) return null;
        try {
            var clean = xml.replace(/\s+xmlns\s*=\s*"[^"]*"/g, '');
            var doc = new DOMParser().parseFromString(clean, 'text/xml');
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
        var n = parseInt(p, 10);
        if (isNaN(n) || n < 0) return '000';
        return ('00' + n).slice(-3);
    }

    // --- Catalog Data ---
    var _catalogCache = null;

    function loadCatalog() {
        if (_catalogCache) return Promise.resolve(_catalogCache);
        return fetch('data/catalog.json')
            .then(function (r) { return r.json(); })
            .then(function (data) { _catalogCache = data; return data; })
            .catch(function () {
                console.error('Edition: catalog.json nicht geladen');
                return null;
            });
    }

    // --- Dark Mode ---
    var ICON_SUN = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="5"/><path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/></svg>';
    var ICON_MOON = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>';

    function initDarkMode() {
        var saved = localStorage.getItem('ed-dark-mode');
        if (saved === 'true' || (saved === null && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
            document.body.classList.add('dark');
        }
        updateDarkToggleLabel();
    }

    function toggleDarkMode() {
        document.body.classList.toggle('dark');
        localStorage.setItem('ed-dark-mode', document.body.classList.contains('dark'));
        updateDarkToggleLabel();
    }

    function updateDarkToggleLabel() {
        var btn = $('#dark-toggle');
        if (!btn) return;
        var isDark = document.body.classList.contains('dark');
        btn.innerHTML = (isDark ? ICON_SUN + ' Hell' : ICON_MOON + ' Dunkel');
        btn.setAttribute('aria-label', isDark ? 'Helles Design aktivieren' : 'Dunkles Design aktivieren');
    }

    // --- Navigation (generated from JS to avoid HTML duplication) ---
    var NAV_ITEMS = [
        { href: 'index.html', label: 'Start' },
        { href: 'catalog.html', label: 'Katalog' },
        { href: 'reader.html', label: 'Leseansicht' },
        { href: 'about.html', label: 'Projekt' }
    ];
    var ICON_HAMBURGER = '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 12h18M3 6h18M3 18h18"/></svg>';

    function renderNav() {
        var target = $('#ed-nav-slot');
        if (!target) return;

        var path = window.location.pathname;
        var links = NAV_ITEMS.map(function (item) {
            var active = path.indexOf(item.href) > -1 ? ' class="active"' : '';
            return '<li><a href="' + item.href + '"' + active + '>' + item.label + '</a></li>';
        }).join('');

        target.innerHTML =
            '<div class="ed-nav-inner">' +
            '<a href="index.html" class="ed-nav-brand">Nachlass Hersch</a>' +
            '<button class="ed-nav-hamburger" id="nav-hamburger" aria-label="Navigation" aria-expanded="false" aria-controls="ed-nav-links">' + ICON_HAMBURGER + '</button>' +
            '<ul class="ed-nav-links" id="ed-nav-links">' + links +
            '<li><button class="ed-nav-toggle" id="dark-toggle" aria-label="Dunkles Design aktivieren"></button></li>' +
            '</ul></div>';
    }

    function renderFooter() {
        var target = $('#ed-footer-slot');
        if (!target) return;
        target.innerHTML =
            '<div class="ed-footer-links">' +
            '<a href="index.html">Startseite</a>' +
            '<a href="catalog.html">Katalog</a>' +
            '<a href="about.html">Projekt</a>' +
            '<a href="../index.html">Pipeline-Dashboard</a>' +
            '</div>' +
            '<p>Zentralbibliothek Zuerich &middot; DHCraft &middot; 2026</p>';
    }

    function initNav() {
        var hamburger = $('#nav-hamburger');
        var links = $('#ed-nav-links');
        if (hamburger && links) {
            hamburger.addEventListener('click', function () {
                var open = links.classList.toggle('open');
                hamburger.setAttribute('aria-expanded', String(open));
            });
        }

        var darkBtn = $('#dark-toggle');
        if (darkBtn) {
            darkBtn.addEventListener('click', toggleDarkMode);
        }
    }

    // --- Entity Index (Reconciliation-verifiziert) ---
    var _entityIndexCache = null;

    function loadEntityIndex() {
        if (_entityIndexCache) return Promise.resolve(_entityIndexCache);
        return fetch('../data/entity_index.json')
            .then(function (r) { return r.json(); })
            .then(function (data) { _entityIndexCache = data; return data; })
            .catch(function () {
                console.warn('Edition: entity_index.json nicht geladen');
                _entityIndexCache = {};
                return {};
            });
    }

    function lookupEntity(ref) {
        if (!_entityIndexCache || !ref) return null;
        // #zbz-p.1 -> zbz-p.1
        var id = ref.charAt(0) === '#' ? ref.slice(1) : ref;
        return _entityIndexCache[id] || null;
    }

    // --- Image/TEI Paths ---
    function imagePath(docId, page) {
        return '../images/' + docId + '/' + docId + '_p' + padPage(page) + '.png';
    }

    function fetchTei(docId, page) {
        var paths = [
            '../data/examples/' + docId + '/' + docId + '_p' + page + '.xml',
            '../../output/tei/' + docId + '_p' + page + '.xml'
        ];
        return _fetchFirstOk(paths);
    }

    function _fetchFirstOk(urls) {
        if (!urls.length) return Promise.resolve(null);
        return fetch(urls[0]).then(function (r) {
            if (r.ok) return r.text();
            return _fetchFirstOk(urls.slice(1));
        }).catch(function () {
            return _fetchFirstOk(urls.slice(1));
        });
    }

    // --- Debounce ---
    function debounce(fn, ms) {
        var timer;
        return function () {
            var args = arguments;
            var ctx = this;
            clearTimeout(timer);
            timer = setTimeout(function () { fn.apply(ctx, args); }, ms);
        };
    }

    // --- Card Rendering (shared between landing + catalog) ---
    function buildCardHtml(doc, opts) {
        var docId = doc.id;
        var title = doc.title || 'Dokument ' + docId;
        var imgSrc = imagePath(docId, 1);
        var placeholder = '<div class=\'ed-card-img-placeholder\'>Dok. ' + esc(docId) + '</div>';

        var html = '<a href="reader.html?doc=' + esc(docId) + '" class="ed-card">';
        html += '<img class="ed-card-img" src="' + imgSrc + '" alt="' + esc(title) + '" loading="lazy" onerror="this.outerHTML=\'' + placeholder.replace(/'/g, "\\'") + '\'">';
        html += '<div class="ed-card-body">';
        html += '<div class="ed-card-title">' + esc(title) + '</div>';
        html += '<p class="ed-card-meta">';
        if (doc.author) html += esc(doc.author);
        if (doc.date) html += (doc.author ? ' &middot; ' : '') + esc(doc.date);
        if (opts && opts.showPages && doc.page_count) html += ' &middot; ' + doc.page_count + ' S.';
        html += '</p>';
        html += '<span class="ed-badge ed-badge-type">' + esc(TYPE_LABELS[doc.type] || doc.type) + '</span>';
        if (doc.lang) html += ' <span class="ed-badge ed-badge-lang">' + esc(doc.lang) + '</span>';
        if (doc.entity_count) html += ' <span class="ed-badge ed-badge-ner" title="' + doc.entity_count + ' Entitaeten">' + doc.entity_count + ' Ent.</span>';
        if (doc.demo) html += ' <span class="ed-badge ed-badge-demo">Demo</span>';
        html += '</div></a>';
        return html;
    }

    // --- Labels ---
    var LANG_LABELS = {
        'FR': 'Franzoesisch', 'DE': 'Deutsch', 'EN': 'Englisch',
        'IT': 'Italienisch', 'DE/FR': 'Deutsch/Franz.', '?': 'Unbestimmt',
        'ES': 'Spanisch', 'PT': 'Portugiesisch', 'NL': 'Niederlaendisch',
        'PL': 'Polnisch', 'HU': 'Ungarisch', 'EL': 'Griechisch',
        'LA': 'Latein', 'RU': 'Russisch', 'SV': 'Schwedisch',
        '-': 'Unbekannt'
    };
    var TYPE_LABELS = {
        'A': 'Einspaltig', 'B': 'Zweispaltig',
        'C': 'Monografie', 'D': 'Spezialformat', '-': 'Unklassifiziert'
    };
    var PUB_FORM_LABELS = {
        'journalArticle': 'Zeitschriftenartikel', 'book': 'Buch',
        'bookSection': 'Buchkapitel', 'encyclopedia': 'Lexikonartikel',
        'brochure': 'Broschure', 'interview': 'Interview',
        'anthology': 'Anthologie', 'other': 'Sonstige'
    };

    // --- Init ---
    function init() {
        renderNav();
        renderFooter();
        initDarkMode();
        initNav();
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
        toggleDarkMode: toggleDarkMode,
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
