/**
 * ZBZ Edition – Shared Module (Rewrite)
 * Navigation, Data Loading, Utilities, Card Rendering.
 * Depends on zbz-core.js (loaded first).
 * Namespace: ZBZ.Edition (ES6+, IIFE)
 */
(function () {
    'use strict';

    window.ZBZ = window.ZBZ || {};

    // --- Delegate to ZBZ core (zbz-core.js) ---
    var _log = ZBZ.log || function (mod, msg) { console.log('[ZBZ:' + mod + '] ' + msg); };
    var $ = ZBZ.$ || function (sel, ctx) { return (ctx || document).querySelector(sel); };
    var $$ = ZBZ.$$ || function (sel, ctx) { return Array.prototype.slice.call((ctx || document).querySelectorAll(sel)); };
    var esc = ZBZ.esc || function (s) { return s == null ? '' : String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;'); };
    var fmtNum = ZBZ.fmtNum || function (n) { return n == null ? '-' : String(n).replace(/\B(?=(\d{3})+(?!\d))/g, '.'); };
    var getParam = ZBZ.getParam || function (key) { return new URLSearchParams(window.location.search).get(key); };
    var setParams = ZBZ.setParams || function () {};
    var sanitizeDocId = ZBZ.sanitizeDocId || function (id) { if (!id) return null; var c = String(id).replace(/[^0-9]/g, ''); return c || null; };
    var parseXml = ZBZ.parseXml || function (xml) { return null; };
    var highlightXml = ZBZ.highlightXml || function (xml) { return esc(xml); };
    var padPage = ZBZ.padPage || function (p) { return ('00' + parseInt(p, 10)).slice(-3); };
    var debounce = ZBZ.debounce || function (fn, ms) { var t; return function () { var a = arguments, c = this; clearTimeout(t); t = setTimeout(function () { fn.apply(c, a); }, ms); }; };

    // --- Catalog Data ---
    var _catalogCache = null;

    function loadCatalog() {
        if (_catalogCache) return Promise.resolve(_catalogCache);
        return fetch('data/catalog.json')
            .then(function (r) { return r.json(); })
            .then(function (data) {
                _catalogCache = data;
                _log('Catalog', (data.documents ? data.documents.length : 0) + ' Dokumente geladen');
                return data;
            })
            .catch(function () {
                _log('Catalog', 'FEHLER: catalog.json nicht geladen');
                return null;
            });
    }

    // --- Entity Index (delegated to zbz-core.js) ---
    var loadEntityIndex = ZBZ.loadEntityIndex || function () { return Promise.resolve({}); };
    var lookupEntity = ZBZ.lookupEntity || function () { return null; };

    var _registerCache = null;
    function loadEntityRegister() {
        if (_registerCache) return Promise.resolve(_registerCache);
        return fetch('data/entity_register.json')
            .then(function (r) { return r.json(); })
            .then(function (data) {
                _registerCache = data;
                _log('EntityRegister', data.entities.length + ' Eintraege geladen');
                return data;
            })
            .catch(function () {
                _log('EntityRegister', 'nicht verfuegbar');
                return null;
            });
    }

    // --- Full-Text Search ---
    var _searchIndexCache = null;

    function loadSearchIndex() {
        if (_searchIndexCache) return Promise.resolve(_searchIndexCache);
        return fetch('data/search_index.json')
            .then(function (r) { return r.json(); })
            .then(function (data) {
                _searchIndexCache = data;
                _log('SearchIndex', data.length + ' Dokumente geladen');
                return data;
            })
            .catch(function () {
                _log('SearchIndex', 'nicht verfuegbar');
                _searchIndexCache = [];
                return [];
            });
    }

    function createFullTextSearchIndex(docs) {
        if (typeof MiniSearch === 'undefined' || !docs || !docs.length) return null;
        try {
            var idx = new MiniSearch({
                fields: ['title', 'text', 'entitiesStr'],
                storeFields: ['id', 'title', 'text'],
                searchOptions: { boost: { title: 5, entitiesStr: 2, text: 1 }, fuzzy: 0.2, prefix: true }
            });
            idx.addAll(docs.map(function (d) {
                return { id: d.id, title: d.title || '', text: d.text || '', entitiesStr: (d.entities || []).join(' ') };
            }));
            return idx;
        } catch (e) {
            console.warn('Full-text search index failed:', e);
            return null;
        }
    }

    function extractSnippet(text, query, contextChars) {
        if (!text || !query) return '';
        contextChars = contextChars || 120;
        var lower = text.toLowerCase();
        var qLower = query.toLowerCase().split(/\s+/)[0];
        var pos = lower.indexOf(qLower);
        if (pos === -1) return text.substring(0, contextChars * 2) + '...';
        var start = Math.max(0, pos - contextChars);
        var end = Math.min(text.length, pos + qLower.length + contextChars);
        var snippet = (start > 0 ? '...' : '') + text.substring(start, end) + (end < text.length ? '...' : '');
        var escaped = qLower.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
        snippet = snippet.replace(new RegExp('(' + escaped + ')', 'gi'), '<mark>$1</mark>');
        return snippet;
    }

    // --- Image/TEI Paths (delegated to zbz-core.js) ---
    var imagePath = ZBZ.imagePath;

    // --- Full-document TEI cache ---
    var _fullTeiCache = {};

    function fetchFullTei(docId) {
        if (_fullTeiCache[docId]) return Promise.resolve(_fullTeiCache[docId]);
        var paths = [
            'data/tei/' + docId + '_final.xml',
            'data/examples/' + docId + '/' + docId + '_final.xml',
            '../output/tei_final/' + docId + '_final.xml'
        ];
        return _fetchFirstOk(paths).then(function (xml) {
            if (xml) _fullTeiCache[docId] = xml;
            return xml;
        });
    }

    function extractPageFromFull(xml, page) {
        if (!xml) return null;
        var clean = xml.replace(/\s+xmlns\s*=\s*"[^"]*"/g, '');
        var bodyStart = clean.indexOf('<body');
        var bodyEnd = clean.lastIndexOf('</body>');
        if (bodyStart === -1 || bodyEnd === -1) return null;
        var bodyContent = clean.substring(bodyStart, bodyEnd + 7);

        var pbRegex = /<pb\s[^>]*?n="(\d+)"[^>]*?(?:\/>|><\/pb>)/g;
        var pbPositions = [];
        var m;
        while ((m = pbRegex.exec(bodyContent)) !== null) {
            pbPositions.push({ n: parseInt(m[1], 10), pos: m.index, end: m.index + m[0].length });
        }
        if (!pbPositions.length) return page === 1 ? bodyContent : null;

        var targetIdx = -1;
        for (var i = 0; i < pbPositions.length; i++) {
            if (pbPositions[i].n === page) { targetIdx = i; break; }
        }
        if (targetIdx === -1) return null;

        var segStart = pbPositions[targetIdx].pos;
        var segEnd;
        if (targetIdx + 1 < pbPositions.length) {
            segEnd = pbPositions[targetIdx + 1].pos;
        } else {
            var closeBody = bodyContent.lastIndexOf('</body>');
            segEnd = closeBody > segStart ? closeBody : bodyContent.length;
        }

        var segment = bodyContent.substring(segStart, segEnd);
        var tags = ['div', 'p', 'note', 'head', 'hi', 'foreign', 'sp'];
        tags.forEach(function (tag) {
            var opens = (segment.match(new RegExp('<' + tag + '[\\s>]', 'g')) || []).length;
            var closes = (segment.match(new RegExp('</' + tag + '>', 'g')) || []).length;
            if (opens > closes) {
                for (var j = 0; j < opens - closes; j++) segment += '</' + tag + '>';
            } else if (closes > opens) {
                for (var j = 0; j < closes - opens; j++) segment = '<' + tag + '>' + segment;
            }
        });
        return '<body>' + segment + '</body>';
    }

    function extractRevisionDesc(xml) {
        if (!xml) return null;
        var clean = xml.replace(/\s+xmlns\s*=\s*"[^"]*"/g, '');
        var doc = new DOMParser().parseFromString(clean, 'text/xml');
        if (doc.querySelector('parsererror')) return null;
        var revDesc = doc.querySelector('revisionDesc');
        if (!revDesc) return null;
        var changes = Array.prototype.slice.call(revDesc.querySelectorAll('change'));
        return changes.map(function (ch) {
            return {
                when: ch.getAttribute('when') || '',
                who: ch.getAttribute('who') || '',
                status: ch.getAttribute('status') || '',
                text: (ch.textContent || '').trim()
            };
        });
    }

    function fetchTei(docId, page) {
        return fetchFullTei(docId).then(function (fullXml) {
            if (fullXml) {
                var pageXml = extractPageFromFull(fullXml, page);
                if (pageXml) return pageXml;
            }
            var paths = [
                'data/examples/' + docId + '/' + docId + '_p' + page + '.xml',
                '../output/tei/' + docId + '_p' + page + '.xml'
            ];
            return _fetchFirstOk(paths);
        });
    }

    // --- Fetch (delegated to zbz-core.js) ---
    var _fetchFirstOk = ZBZ.fetchFirstOk || function () { return Promise.resolve(null); };

    // --- Labels ---
    var LANG_LABELS = {
        'FR': 'Franzoesisch', 'DE': 'Deutsch', 'EN': 'Englisch',
        'IT': 'Italienisch', 'DE/FR': 'Deutsch/Franz.', '?': 'Unbestimmt',
        'ES': 'Spanisch', 'PT': 'Portugiesisch', 'NL': 'Niederlaendisch',
        'PL': 'Polnisch', 'HU': 'Ungarisch', 'EL': 'Griechisch',
        'LA': 'Latein', 'RU': 'Russisch', 'SV': 'Schwedisch', '-': 'Unbekannt'
    };
    var TYPE_LABELS = {
        'A': 'Einspaltig', 'B': 'Zweispaltig',
        'C': 'Monografie', 'D': 'Spezialformat', '-': 'Unklassifiziert'
    };
    var PUB_FORM_LABELS = ZBZ.PUB_FORM_LABELS;
    var SCREENING_LABELS = {
        'APPROVED': 'LLM genehmigt',
        'APPROVED_WITH_NOTES': 'Mit Anmerkungen',
        'NEEDS_REVIEW': 'Pruefung noetig',
        'NOT_SCREENED': 'Nicht gescreent'
    };
    var SCREENING_CLASSES = {
        'APPROVED': 'ed-badge-screening-approved',
        'APPROVED_WITH_NOTES': 'ed-badge-screening-notes',
        'NEEDS_REVIEW': 'ed-badge-screening-review',
        'NOT_SCREENED': 'ed-badge-screening-none'
    };
    var CURATION_LABELS = {
        'uncurated': 'Nicht kuratiert', 'draft': 'Entwurf',
        'in_progress': 'In Bearbeitung', 'in_review': 'In Pruefung',
        'editor_approved': 'Editor freigegeben'
    };
    var CURATION_CLASSES = {
        'uncurated': 'ed-badge-curation-uncurated', 'draft': 'ed-badge-curation-draft',
        'in_progress': 'ed-badge-curation-progress', 'in_review': 'ed-badge-curation-review',
        'editor_approved': 'ed-badge-curation-approved'
    };

    function screeningBadgeHtml(status) {
        if (!status) return '';
        var label = SCREENING_LABELS[status] || status;
        var cls = SCREENING_CLASSES[status] || 'ed-badge-screening-none';
        return '<span class="ed-badge ' + cls + '">' + esc(label) + '</span>';
    }

    function curationBadgeHtml(status) {
        if (!status || status === 'pipeline') return '';
        var label = CURATION_LABELS[status] || status;
        var cls = CURATION_CLASSES[status] || 'ed-badge-curation-uncurated';
        return '<span class="ed-badge ' + cls + '">' + esc(label) + '</span>';
    }

    // --- Card Rendering ---
    function buildCardHtml(doc, opts) {
        var docId = doc.id;
        var title = doc.title || 'Dokument ' + docId;
        var imgSrc = imagePath(docId, 1);
        var placeholder = "<div class='ed-card-img-placeholder'>Dok. " + esc(docId) + "</div>";

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
        if (doc.screening) html += ' ' + screeningBadgeHtml(doc.screening);
        if (doc.curation && doc.curation !== 'uncurated') html += ' ' + curationBadgeHtml(doc.curation);
        if (doc.desc) {
            var descText = doc.desc.length > 120 ? doc.desc.substring(0, 117) + '...' : doc.desc;
            html += '<p class="ed-card-desc">' + esc(descText) + '</p>';
        }
        html += '</div></a>';
        return html;
    }

    // --- Navigation ---
    var NAV_ITEMS = [
        { href: 'index.html', label: 'Start' },
        { label: 'Edition', children: [
            { href: 'catalog.html', label: 'Katalog' },
            { href: 'register.html', label: 'Register' }
        ]},
        { label: 'Epistemische Infrastruktur', children: [
            { href: 'infrastruktur/index.html', label: 'Dashboard' },
            { href: 'infrastruktur/viewer.html', label: 'Viewer' },
            { href: 'infrastruktur/diagnostik.html', label: 'Diagnostik' },
            { href: 'infrastruktur/cer.html', label: 'CER' }
        ]},
        { href: 'about.html', label: 'Projekt' }
    ];
    var ICON_HAMBURGER = '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 12h18M3 6h18M3 18h18"/></svg>';

    function renderNav() {
        var target = $('#ed-nav-slot');
        if (!target) return;
        var path = window.location.pathname;
        var isInfra = path.indexOf('/infrastruktur/') > -1;
        var hrefPrefix = isInfra ? '../' : '';

        var links = NAV_ITEMS.map(function (item) {
            if (item.children) {
                var _isChildActive = function (c) {
                    if (c.href.indexOf('infrastruktur/') === 0) {
                        var sub = c.href.replace('infrastruktur/', '');
                        return isInfra && path.indexOf(sub) > -1;
                    }
                    return !isInfra && path.indexOf(c.href) > -1;
                };
                var childActive = item.children.some(_isChildActive);
                // reader.html gehoert zur Edition
                if (!childActive && !isInfra && path.indexOf('reader.html') > -1 && item.label === 'Edition') childActive = true;
                var childLinks = item.children.map(function (child) {
                    var href = hrefPrefix + child.href;
                    var active = _isChildActive(child);
                    return '<li><a href="' + href + '"' + (active ? ' class="active"' : '') + '>' + child.label + '</a></li>';
                }).join('');
                return '<li class="ed-nav-dropdown">' +
                    '<button class="ed-nav-dropdown-toggle' + (childActive ? ' active' : '') + '" aria-expanded="false">' + item.label + ' <svg class="ed-nav-chevron" width="10" height="6" viewBox="0 0 10 6"><path d="M1 1l4 4 4-4" fill="none" stroke="currentColor" stroke-width="1.5"/></svg></button>' +
                    '<ul class="ed-nav-dropdown-menu">' + childLinks + '</ul></li>';
            }
            var href = hrefPrefix + item.href;
            var active = false;
            if (item.href.indexOf('infrastruktur/') === 0) {
                var subPage = item.href.replace('infrastruktur/', '');
                active = isInfra && path.indexOf(subPage) > -1;
            } else if (!isInfra) {
                active = path.indexOf(item.href) > -1 && item.href !== 'index.html';
                if (item.href === 'index.html') {
                    active = /\/index\.html$/.test(path) || /\/docs\/?$/.test(path);
                }
            }
            return '<li><a href="' + href + '"' + (active ? ' class="active"' : '') + '>' + item.label + '</a></li>';
        }).join('');

        target.innerHTML =
            '<div class="ed-nav-inner">' +
            '<a href="' + hrefPrefix + 'index.html" class="ed-nav-brand">Nachlass Hersch</a>' +
            '<button class="ed-nav-hamburger" id="nav-hamburger" aria-label="Navigation" aria-expanded="false" aria-controls="ed-nav-links">' + ICON_HAMBURGER + '</button>' +
            '<ul class="ed-nav-links" id="ed-nav-links">' + links + '</ul></div>';
    }

    function renderFooter() {
        var target = $('#ed-footer-slot');
        if (!target) return;
        var isInfra = window.location.pathname.indexOf('/infrastruktur/') > -1;
        var p = isInfra ? '../' : '';
        target.innerHTML =
            '<div class="ed-footer-links">' +
            '<a href="' + p + 'index.html">Start</a>' +
            '<a href="' + p + 'catalog.html">Katalog</a>' +
            '<a href="' + p + 'register.html">Register</a>' +
            '<a href="' + p + 'infrastruktur/index.html">Dashboard</a>' +
            '<a href="' + p + 'infrastruktur/viewer.html">Viewer</a>' +
            '<a href="' + p + 'infrastruktur/diagnostik.html">Diagnostik</a>' +
            '<a href="' + p + 'about.html">Projekt</a>' +
            '</div>' +
            '<p class="ed-footer-disclaimer">Experimentelle Promptotyping-Edition &mdash; KI-gestuetzte Texterzeugung in laufender Kuration. ' +
            '<a href="' + p + 'about.html#promptotyping">Methodik</a></p>' +
            '<p>Zentralbibliothek Zuerich &middot; DHCraft &middot; 2026</p>';
    }

    function renderDisclaimer() {
        var nav = $('#ed-nav-slot');
        if (!nav) return;
        var isInfra = window.location.pathname.indexOf('/infrastruktur/') > -1;
        var p = isInfra ? '../' : '';
        var banner = document.createElement('div');
        banner.className = 'ed-disclaimer-banner';
        banner.setAttribute('role', 'status');
        banner.innerHTML =
            '<div class="ed-disclaimer-banner-inner">' +
            '<span class="ed-disclaimer-badge">Experimentell</span>' +
            '<span class="ed-disclaimer-text">' +
            'Promptotyping-Edition &mdash; Alle Texte wurden KI-gestuetzt erzeugt und befinden sich in laufender Kuration. ' +
            '<a href="' + p + 'about.html#promptotyping">Zur Methodik</a>' +
            '</span></div>';
        nav.insertAdjacentElement('afterend', banner);
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
        $$('.ed-nav-dropdown-toggle').forEach(function (btn) {
            btn.addEventListener('click', function (e) {
                e.stopPropagation();
                var li = btn.closest('.ed-nav-dropdown');
                var wasOpen = li.classList.contains('open');
                $$('.ed-nav-dropdown.open').forEach(function (d) {
                    d.classList.remove('open');
                    d.querySelector('.ed-nav-dropdown-toggle').setAttribute('aria-expanded', 'false');
                });
                if (!wasOpen) {
                    li.classList.add('open');
                    btn.setAttribute('aria-expanded', 'true');
                }
            });
        });
        document.addEventListener('click', function () {
            $$('.ed-nav-dropdown.open').forEach(function (d) {
                d.classList.remove('open');
                d.querySelector('.ed-nav-dropdown-toggle').setAttribute('aria-expanded', 'false');
            });
        });
    }

    // --- Init ---
    function init() {
        renderNav();
        renderDisclaimer();
        renderFooter();
        initNav();
        var page = window.location.pathname.split('/').pop() || 'index.html';
        _log('Edition', page + ' | nav + footer ready');
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    // --- Public API (full backward compat with edition-tei.js) ---
    ZBZ.Edition = {
        $: $, $$: $$, esc: esc, fmtNum: fmtNum,
        getParam: getParam, setParams: setParams, sanitizeDocId: sanitizeDocId,
        parseXml: parseXml, highlightXml: highlightXml, padPage: padPage,
        loadCatalog: loadCatalog,
        loadSearchIndex: loadSearchIndex,
        createFullTextSearchIndex: createFullTextSearchIndex,
        extractSnippet: extractSnippet,
        imagePath: imagePath,
        fetchTei: fetchTei, fetchFullTei: fetchFullTei,
        extractPageFromFull: extractPageFromFull,
        extractRevisionDesc: extractRevisionDesc,
        loadEntityIndex: loadEntityIndex,
        loadEntityRegister: loadEntityRegister,
        lookupEntity: lookupEntity,
        debounce: debounce,
        buildCardHtml: buildCardHtml,
        LANG_LABELS: LANG_LABELS, TYPE_LABELS: TYPE_LABELS, PUB_FORM_LABELS: PUB_FORM_LABELS,
        SCREENING_LABELS: SCREENING_LABELS, SCREENING_CLASSES: SCREENING_CLASSES,
        CURATION_LABELS: CURATION_LABELS, CURATION_CLASSES: CURATION_CLASSES,
        screeningBadgeHtml: screeningBadgeHtml, curationBadgeHtml: curationBadgeHtml
    };
})();
