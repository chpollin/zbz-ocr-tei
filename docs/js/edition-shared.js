/**
 * ZBZ Edition – Shared Module
 * Navigation, Data Loading, Utilities, Card Rendering.
 * Namespace: ZBZ.Edition (ES6+, IIFE)
 */
(function () {
    'use strict';

    // --- Ensure ZBZ namespace + log ---
    window.ZBZ = window.ZBZ || {};
    const _logStyles = 'color:#2C2825;font-weight:600';
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
        { label: 'Register', children: [
            { href: 'register-personen.html', label: 'Personen' },
            { href: 'register-organisationen.html', label: 'Organisationen' },
            { href: 'register-orte.html', label: 'Orte' },
            { href: 'register-werke.html', label: 'Werke' }
        ]},
        { href: 'about.html', label: 'Projekt' },
        { href: 'infrastruktur/index.html', label: 'Promptotyping-Artefakte' }
    ];
    const ICON_HAMBURGER = '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 12h18M3 6h18M3 18h18"/></svg>';

    function renderNav() {
        const target = $('#ed-nav-slot');
        if (!target) return;

        const path = window.location.pathname;
        const isInfra = path.indexOf('/infrastruktur/') > -1;
        const hrefPrefix = isInfra ? '../' : '';

        const links = NAV_ITEMS.map((item) => {
            // Dropdown item (has children)
            if (item.children) {
                const childActive = item.children.some((c) => !isInfra && path.indexOf(c.href) > -1);
                const childLinks = item.children.map((child) => {
                    const href = hrefPrefix + child.href;
                    const active = !isInfra && path.indexOf(child.href) > -1;
                    return `<li><a href="${href}"${active ? ' class="active"' : ''}>${child.label}</a></li>`;
                }).join('');
                return `<li class="ed-nav-dropdown">` +
                    `<button class="ed-nav-dropdown-toggle${childActive ? ' active' : ''}" aria-expanded="false">${item.label} <svg class="ed-nav-chevron" width="10" height="6" viewBox="0 0 10 6"><path d="M1 1l4 4 4-4" fill="none" stroke="currentColor" stroke-width="1.5"/></svg></button>` +
                    `<ul class="ed-nav-dropdown-menu">${childLinks}</ul></li>`;
            }
            // Regular item
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
            `<a href="${p}register-personen.html">Personen</a>` +
            `<a href="${p}register-organisationen.html">Organisationen</a>` +
            `<a href="${p}register-orte.html">Orte</a>` +
            `<a href="${p}register-werke.html">Werke</a>` +
            `<a href="${p}about.html">Projekt</a>` +
            `<a href="${p}infrastruktur/index.html">Promptotyping-Artefakte</a>` +
            `</div>` +
            `<p class="ed-footer-disclaimer">Experimentelle Promptotyping-Edition &mdash; KI-gestuetzte Texterzeugung in laufender Kuration. ` +
            `<a href="${p}about.html#promptotyping">Methodik</a></p>` +
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

        // Dropdown toggles
        $$('.ed-nav-dropdown-toggle').forEach((btn) => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const li = btn.closest('.ed-nav-dropdown');
                const wasOpen = li.classList.contains('open');
                // Close all other dropdowns
                $$('.ed-nav-dropdown.open').forEach((d) => {
                    d.classList.remove('open');
                    d.querySelector('.ed-nav-dropdown-toggle').setAttribute('aria-expanded', 'false');
                });
                if (!wasOpen) {
                    li.classList.add('open');
                    btn.setAttribute('aria-expanded', 'true');
                }
            });
        });

        // Close dropdown on outside click
        document.addEventListener('click', () => {
            $$('.ed-nav-dropdown.open').forEach((d) => {
                d.classList.remove('open');
                d.querySelector('.ed-nav-dropdown-toggle').setAttribute('aria-expanded', 'false');
            });
        });
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

    let _registerCache = null;
    function loadEntityRegister() {
        if (_registerCache) return Promise.resolve(_registerCache);
        return fetch('data/entity_register.json')
            .then((r) => r.json())
            .then((data) => {
                _registerCache = data;
                _log('EntityRegister', `${data.entities.length} Eintraege geladen`);
                return data;
            })
            .catch(() => {
                _log('EntityRegister', 'nicht verfuegbar');
                return null;
            });
    }

    // --- Full-Text Search Index ---
    let _searchIndexCache = null;

    function loadSearchIndex() {
        if (_searchIndexCache) return Promise.resolve(_searchIndexCache);
        return fetch('data/search_index.json')
            .then((r) => r.json())
            .then((data) => {
                _searchIndexCache = data;
                _log('SearchIndex', `${data.length} Dokumente geladen`);
                return data;
            })
            .catch(() => {
                _log('SearchIndex', 'nicht verfuegbar');
                _searchIndexCache = [];
                return [];
            });
    }

    function createFullTextSearchIndex(docs) {
        if (typeof MiniSearch === 'undefined' || !docs || !docs.length) return null;
        try {
            const idx = new MiniSearch({
                fields: ['title', 'text', 'entitiesStr'],
                storeFields: ['id', 'title', 'text'],
                searchOptions: {
                    boost: { title: 5, entitiesStr: 2, text: 1 },
                    fuzzy: 0.2,
                    prefix: true
                }
            });
            idx.addAll(docs.map((d) => ({
                id: d.id,
                title: d.title || '',
                text: d.text || '',
                entitiesStr: (d.entities || []).join(' ')
            })));
            return idx;
        } catch (e) {
            console.warn('Full-text search index failed:', e);
            return null;
        }
    }

    function extractSnippet(text, query, contextChars) {
        if (!text || !query) return '';
        contextChars = contextChars || 120;
        const lower = text.toLowerCase();
        const qLower = query.toLowerCase().split(/\s+/)[0]; // first word
        const pos = lower.indexOf(qLower);
        if (pos === -1) return text.substring(0, contextChars * 2) + '...';
        const start = Math.max(0, pos - contextChars);
        const end = Math.min(text.length, pos + qLower.length + contextChars);
        let snippet = (start > 0 ? '...' : '') + text.substring(start, end) + (end < text.length ? '...' : '');
        // Wrap match in <mark>
        const escaped = qLower.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
        snippet = snippet.replace(new RegExp('(' + escaped + ')', 'gi'), '<mark>$1</mark>');
        return snippet;
    }

    // --- Image/TEI Paths ---
    function imagePath(docId, page) {
        return `images/${docId}/${docId}_p${padPage(page)}.png`;
    }

    // --- Full-document TEI cache (avoids re-fetch on page navigation) ---
    const _fullTeiCache = {};

    function fetchFullTei(docId) {
        if (_fullTeiCache[docId]) return Promise.resolve(_fullTeiCache[docId]);
        const paths = [
            `data/tei/${docId}_final.xml`,
            `data/examples/${docId}/${docId}_final.xml`,
            `../output/tei_final/${docId}_final.xml`
        ];
        return _fetchFirstOk(paths).then((xml) => {
            if (xml) _fullTeiCache[docId] = xml;
            return xml;
        });
    }

    function extractPageFromFull(xml, page) {
        if (!xml) return null;
        // Work on the raw XML string (not DOM-serialized) for consistent <pb/> format
        const clean = xml.replace(/\s+xmlns\s*=\s*"[^"]*"/g, '');

        // Find <body> content
        const bodyStart = clean.indexOf('<body');
        const bodyEnd = clean.lastIndexOf('</body>');
        if (bodyStart === -1 || bodyEnd === -1) return null;
        const bodyContent = clean.substring(bodyStart, bodyEnd + 7); // includes <body>...</body>

        // Find all <pb> positions — match both <pb .../> and <pb ...></pb>
        const pbRegex = /<pb\s[^>]*?n="(\d+)"[^>]*?(?:\/>|><\/pb>)/g;
        const pbPositions = [];
        let m;
        while ((m = pbRegex.exec(bodyContent)) !== null) {
            pbPositions.push({ n: parseInt(m[1], 10), pos: m.index, end: m.index + m[0].length });
        }

        if (!pbPositions.length) {
            return page === 1 ? bodyContent : null;
        }

        // Find the target page
        let targetIdx = -1;
        for (let i = 0; i < pbPositions.length; i++) {
            if (pbPositions[i].n === page) {
                targetIdx = i;
                break;
            }
        }
        if (targetIdx === -1) return null;

        const segStart = pbPositions[targetIdx].pos;
        let segEnd;
        if (targetIdx + 1 < pbPositions.length) {
            segEnd = pbPositions[targetIdx + 1].pos;
        } else {
            // Last page: until </body>
            const closeBody = bodyContent.lastIndexOf('</body>');
            segEnd = closeBody > segStart ? closeBody : bodyContent.length;
        }

        // Extract segment
        let segment = bodyContent.substring(segStart, segEnd);

        // Fix unclosed/unmatched tags: count opening and closing div/p/note tags
        // and add missing closers/openers to make valid XML
        const tags = ['div', 'p', 'note', 'head', 'hi', 'foreign', 'sp'];
        tags.forEach((tag) => {
            const opens = (segment.match(new RegExp('<' + tag + '[\\s>]', 'g')) || []).length;
            const closes = (segment.match(new RegExp('</' + tag + '>', 'g')) || []).length;
            if (opens > closes) {
                // Add missing closers at end
                for (let j = 0; j < opens - closes; j++) segment += '</' + tag + '>';
            } else if (closes > opens) {
                // Add missing openers at start
                for (let j = 0; j < closes - opens; j++) segment = '<' + tag + '>' + segment;
            }
        });

        return '<body>' + segment + '</body>';
    }

    function extractRevisionDesc(xml) {
        if (!xml) return null;
        const clean = xml.replace(/\s+xmlns\s*=\s*"[^"]*"/g, '');
        const doc = new DOMParser().parseFromString(clean, 'text/xml');
        if (doc.querySelector('parsererror')) return null;

        const revDesc = doc.querySelector('revisionDesc');
        if (!revDesc) return null;

        const changes = Array.prototype.slice.call(revDesc.querySelectorAll('change'));
        return changes.map((ch) => ({
            when: ch.getAttribute('when') || '',
            who: ch.getAttribute('who') || '',
            status: ch.getAttribute('status') || '',
            text: (ch.textContent || '').trim()
        }));
    }

    function fetchTei(docId, page) {
        // Strategy: full document first (cached), extract page; fallback to old page-level
        return fetchFullTei(docId).then((fullXml) => {
            if (fullXml) {
                const pageXml = extractPageFromFull(fullXml, page);
                if (pageXml) return pageXml;
            }
            // Fallback: old page-level paths
            const paths = [
                `data/examples/${docId}/${docId}_p${page}.xml`,
                `../output/tei/${docId}_p${page}.xml`
            ];
            return _fetchFirstOk(paths);
        });
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
        if (doc.screening) html += ' ' + screeningBadgeHtml(doc.screening);
        if (doc.curation && doc.curation !== 'uncurated') html += ' ' + curationBadgeHtml(doc.curation);
        if (doc.desc) {
            var descText = doc.desc.length > 120 ? doc.desc.substring(0, 117) + '...' : doc.desc;
            html += '<p class="ed-card-desc">' + esc(descText) + '</p>';
        }
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

    // --- Screening + Curation Labels (Single Source of Truth) ---
    const SCREENING_LABELS = {
        'APPROVED': 'LLM genehmigt',
        'APPROVED_WITH_NOTES': 'Mit Anmerkungen',
        'NEEDS_REVIEW': 'Pruefung noetig',
        'NOT_SCREENED': 'Nicht gescreent'
    };
    const SCREENING_CLASSES = {
        'APPROVED': 'ed-badge-screening-approved',
        'APPROVED_WITH_NOTES': 'ed-badge-screening-notes',
        'NEEDS_REVIEW': 'ed-badge-screening-review',
        'NOT_SCREENED': 'ed-badge-screening-none'
    };
    const CURATION_LABELS = {
        'uncurated': 'Nicht kuratiert',
        'draft': 'Entwurf',
        'in_progress': 'In Bearbeitung',
        'in_review': 'In Pruefung',
        'editor_approved': 'Editor freigegeben'
    };
    const CURATION_CLASSES = {
        'uncurated': 'ed-badge-curation-uncurated',
        'draft': 'ed-badge-curation-draft',
        'in_progress': 'ed-badge-curation-progress',
        'in_review': 'ed-badge-curation-review',
        'editor_approved': 'ed-badge-curation-approved'
    };

    function screeningBadgeHtml(status) {
        if (!status) return '';
        const label = SCREENING_LABELS[status] || status;
        const cls = SCREENING_CLASSES[status] || 'ed-badge-screening-none';
        return `<span class="ed-badge ${cls}">${esc(label)}</span>`;
    }

    function curationBadgeHtml(status) {
        if (!status || status === 'pipeline') return '';
        const label = CURATION_LABELS[status] || status;
        const cls = CURATION_CLASSES[status] || 'ed-badge-curation-uncurated';
        return `<span class="ed-badge ${cls}">${esc(label)}</span>`;
    }

    function renderDisclaimer() {
        const nav = $('#ed-nav-slot');
        if (!nav) return;
        const isInfra = window.location.pathname.indexOf('/infrastruktur/') > -1;
        const p = isInfra ? '../' : '';
        const banner = document.createElement('div');
        banner.className = 'ed-disclaimer-banner';
        banner.setAttribute('role', 'status');
        banner.innerHTML =
            `<div class="ed-disclaimer-banner-inner">` +
            `<span class="ed-disclaimer-badge">` +
            `<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M8 1a2 2 0 0 1 2 2v4a2 2 0 1 1-4 0V3a2 2 0 0 1 2-2zm-3.5 9.5A3.5 3.5 0 0 0 8 14a3.5 3.5 0 0 0 3.5-3.5V9H12v1.5a4.5 4.5 0 1 1-9 0V9h1.5v1.5z"/></svg>` +
            `Experimentell</span>` +
            `<span class="ed-disclaimer-text">` +
            `Promptotyping-Edition — Alle Texte wurden KI-gestuetzt erzeugt und befinden sich in laufender Kuration. ` +
            `<a href="${p}about.html#promptotyping">Zur Methodik</a>` +
            `</span></div>`;
        nav.insertAdjacentElement('afterend', banner);
    }

    // --- Init ---
    function init() {
        renderNav();
        renderDisclaimer();
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
        loadSearchIndex: loadSearchIndex,
        createFullTextSearchIndex: createFullTextSearchIndex,
        extractSnippet: extractSnippet,
        imagePath: imagePath,
        fetchTei: fetchTei,
        fetchFullTei: fetchFullTei,
        extractPageFromFull: extractPageFromFull,
        extractRevisionDesc: extractRevisionDesc,
        loadEntityIndex: loadEntityIndex,
        loadEntityRegister: loadEntityRegister,
        lookupEntity: lookupEntity,
        debounce: debounce,
        buildCardHtml: buildCardHtml,
        LANG_LABELS: LANG_LABELS,
        TYPE_LABELS: TYPE_LABELS,
        PUB_FORM_LABELS: PUB_FORM_LABELS,
        SCREENING_LABELS: SCREENING_LABELS,
        SCREENING_CLASSES: SCREENING_CLASSES,
        CURATION_LABELS: CURATION_LABELS,
        CURATION_CLASSES: CURATION_CLASSES,
        screeningBadgeHtml: screeningBadgeHtml,
        curationBadgeHtml: curationBadgeHtml
    };
})();
