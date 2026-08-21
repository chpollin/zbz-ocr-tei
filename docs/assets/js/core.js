/**
 * core.js — Foundation Layer
 *
 * DOM/URL/Fetch/Format helpers + Data-Path-Resolver.
 * Loaded as the FIRST script.
 *
 * Namespace: window.ZBZ
 */
(function () {
    'use strict';

    const ZBZ = {};

    // ---- Logging ----
    ZBZ.log = (mod, msg) => console.log('%c[ZBZ:' + mod + ']%c ' + msg, 'color:#2C2825;font-weight:600', '');
    ZBZ.warn = (mod, msg) => console.warn('[ZBZ:' + mod + '] ' + msg);

    // ---- DOM ----
    ZBZ.$ = (sel, ctx) => (ctx || document).querySelector(sel);
    ZBZ.$$ = (sel, ctx) => Array.from((ctx || document).querySelectorAll(sel));

    ZBZ.el = (tag, opts) => {
        const e = document.createElement(tag);
        if (!opts) return e;
        if (opts.cls) e.className = opts.cls;
        if (opts.text) e.textContent = opts.text;
        if (opts.html) e.innerHTML = opts.html;
        if (opts.attrs) Object.keys(opts.attrs).forEach(k => e.setAttribute(k, opts.attrs[k]));
        if (opts.on) Object.keys(opts.on).forEach(ev => e.addEventListener(ev, opts.on[ev]));
        if (opts.style) Object.assign(e.style, opts.style);
        return e;
    };

    ZBZ.esc = (s) => {
        if (s == null) return '';
        return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
    };

    // ---- Search folding ----
    // Diacritic-insensitive comparison key for search haystacks and queries.
    // The NFD pass already resolves the umlauts to their base letters, so only the
    // sharp s needs an explicit pair.
    ZBZ.fold = (value) => (value == null ? '' : String(value))
        .toLowerCase()
        .normalize('NFD').replace(/[̀-ͯ]/g, '')
        .replace(/ß/g, 'ss');

    // ---- Markdown ----
    // Minimal renderer for OCR output (Mistral and similar engines deliver Markdown).
    // Supports: # / ## headings, **bold**, *italic*, paragraph blocks via blank lines;
    // strips image refs (the facsimile shows the original), decodes HTML entities.
    // Input is HTML-escaped first, then transformations run on the escaped representation.
    ZBZ.decodeEntities = (s) => {
        if (s == null) return '';
        return String(s)
            .replace(/&amp;/g, '&')
            .replace(/&lt;/g, '<')
            .replace(/&gt;/g, '>')
            .replace(/&quot;/g, '"')
            .replace(/&apos;/g, "'")
            .replace(/&#39;/g, "'")
            .replace(/&nbsp;/g, ' ');
    };
    ZBZ.renderMarkdown = (text) => {
        if (text == null || text === '') return '';
        // 1) Decode entities in the source text (e.g. '&amp;' -> '&') so the later
        //    escape pass produces a consistent representation.
        let src = ZBZ.decodeEntities(String(text));
        // 2) Remove image Markdown before escaping (![..](..) would otherwise stay visible).
        src = src.replace(/!\[[^\]]*\]\([^)]*\)/g, '');
        // 3) HTML-escape.
        let s = ZBZ.esc(src);
        // 4) Apply inline Markdown to the escaped string.
        s = s.replace(/\*\*([^*\n]+)\*\*/g, '<strong>$1</strong>');
        s = s.replace(/(^|[^*])\*([^*\n]+)\*(?!\*)/g, '$1<em>$2</em>');
        // 5) Assemble lines into blocks (## / # / paragraph).
        const lines = s.split(/\r?\n/);
        const out = [];
        let para = [];
        const flushPara = () => {
            if (!para.length) return;
            const joined = para.join(' ').trim();
            if (joined) out.push('<p>' + joined + '</p>');
            para = [];
        };
        for (const raw of lines) {
            const line = raw.trim();
            if (!line) { flushPara(); continue; }
            const h2 = line.match(/^##\s+(.+)$/);
            if (h2) { flushPara(); out.push('<h4>' + h2[1] + '</h4>'); continue; }
            const h1 = line.match(/^#\s+(.+)$/);
            if (h1) { flushPara(); out.push('<h3>' + h1[1] + '</h3>'); continue; }
            para.push(line);
        }
        flushPara();
        return out.join('\n');
    };

    // ---- Blank-page detection ----
    // End-paper, back-matter, and carbon-copy pages produce only garbage OCR ('.', '^{}[]',
    // a page number, or an empty table skeleton). Validated rule: blank when trimmed text
    // is <= 5 characters long OR contains no letters or digits. Source is always the
    // Mistral base OCR.
    ZBZ.isBlankPageText = (text) => {
        if (text == null) return false;                 // unknown -> do not treat as blank
        const s = String(text).trim();
        if (s.length <= 5) return true;                 // '.', '^{}[]', page numbers
        if (!/[A-Za-zÀ-ÿ0-9]/.test(s)) return true;     // punctuation only / empty table skeleton
        return false;
    };

    // ---- URL State ----
    ZBZ.getParam = (k) => new URLSearchParams(window.location.search).get(k);
    ZBZ.setParams = (obj) => {
        const u = new URLSearchParams(window.location.search);
        Object.keys(obj).forEach(k => obj[k] == null ? u.delete(k) : u.set(k, obj[k]));
        const s = u.toString();
        history.replaceState(null, '', window.location.pathname + (s ? '?' + s : ''));
    };

    // ---- Format ----
    ZBZ.padPage = (p) => {
        const n = parseInt(p, 10);
        return isNaN(n) || n < 0 ? '000' : ('00' + n).slice(-3);
    };

    // ---- XML ----
    ZBZ.parseXml = (xml) => {
        if (!xml) return null;
        try {
            const cleaned = xml
                .replace(/\s+xmlns(:\w+)?\s*=\s*["'][^"']*["']/g, '')
                .replace(/\s+xsi:\w+\s*=\s*["'][^"']*["']/g, '');
            const doc = new DOMParser().parseFromString(cleaned, 'text/xml');
            return doc.querySelector('parsererror') ? null : doc;
        } catch (e) { return null; }
    };

    // Well-formedness check on the RAW string (namespaces intact, so line/column
    // positions match what the user sees). Returns null when well-formed, otherwise
    // a short human-readable position string.
    ZBZ.xmlWellFormedError = (xml) => {
        try {
            const doc = new DOMParser().parseFromString(xml || '', 'text/xml');
            const err = doc.querySelector('parsererror');
            if (!err) return null;
            const m = (err.textContent || '').match(/line[ :]*(\d+)[^\d]*column[ :]*(\d+)/i);
            return m ? 'line ' + m[1] + ', column ' + m[2] : 'position unknown';
        } catch (e) { return 'position unknown'; }
    };

    ZBZ.highlightXml = (xml) => {
        let s = ZBZ.esc(xml);
        s = s.replace(/(&lt;\?[\s\S]*?\?&gt;)/g, '<span class="xml-decl">$1</span>');
        s = s.replace(/(&lt;!--[\s\S]*?--&gt;)/g, '<span class="xml-comment">$1</span>');
        s = s.replace(/(&lt;\/?)([\w:.-]+)/g, '$1<span class="xml-tag">$2</span>');
        s = s.replace(/([\w:.-]+)(=)(&quot;[^&]*&quot;)/g,
            '<span class="xml-attr-name">$1</span>$2<span class="xml-attr-value">$3</span>');
        return s;
    };

    // ---- Fetch ----
    // cache: 'no-cache' = always revalidate before using the browser copy (304 still possible,
    // caching is NOT disabled). Required for the local curation loop: Save overwrites the data
    // files (OCR/layout/manifest/TEI); without revalidation a reload would show the old cached
    // file and the edit would appear lost. Images (OSD tiles) do not go through these helpers
    // and keep normal caching.
    ZBZ.fetchText = (url) => fetch(url, { cache: 'no-cache' }).then(r => r.ok ? r.text() : null).catch(() => null);
    ZBZ.fetchJSON = (url) => fetch(url, { cache: 'no-cache' }).then(r => r.ok ? r.json() : null).catch(() => null);
    // 'missing' (HTTP error, e.g. 404) vs 'network' (fetch threw) -- consumed by error UI
    ZBZ.lastFetchError = null;
    const fetchTextDetailed = (url) => fetch(url, { cache: 'no-cache' })
        .then(r => r.ok ? r.text().then(t => ({ text: t, error: null })) : { text: null, error: 'missing' })
        .catch(() => ({ text: null, error: 'network' }));
    ZBZ.fetchFirstOk = async (urls) => {
        let network = false;
        for (const u of urls) {
            const r = await fetchTextDetailed(u);
            if (r.text != null) { ZBZ.lastFetchError = null; return { url: u, text: r.text }; }
            if (r.error === 'network') network = true;
        }
        ZBZ.lastFetchError = network ? 'network' : 'missing';
        return null;
    };
    ZBZ.fetchFirstJsonOk = async (urls) => {
        for (const u of urls) {
            const j = await ZBZ.fetchJSON(u);
            if (j != null) return j;
        }
        return null;
    };

    // ---- Data-Paths ----
    // Primary: data/pages/{doc}/  (mirrored by generate_edition_data.py for all docs)
    // Fallback: ../output/...     (only with a local server using the project root as docroot,
    //                              for alternative OCR engines that are not versioned)
    const padded = (page) => ZBZ.padPage(page);
    // Facsimiles live outside this repo (docs/images/ is gitignored beyond the demo set).
    // On GitHub Pages they come as JPEG from the public facsimile repo, locally as the PNGs.
    ZBZ.imageBase = location.hostname.endsWith('github.io')
        ? 'https://chpollin.github.io/zbz-hersch-images/' : '';
    const imageFile = (doc, name) => ZBZ.imageBase
        ? `${ZBZ.imageBase}${doc}/${name.replace(/\.png$/, '.jpg')}`
        : `images/${doc}/${name}`;
    ZBZ.path = {
        image: (doc, page) => imageFile(doc, `${doc}_p${padded(page)}.png`),
        imageFile,

        // Human-curated layout (written directly by the viewer) takes priority over
        // engine outputs, analogous to loaders.load_layout_gemini (curated > gemini > docling).
        layoutCurated: (doc, page) => [
            `data/pages/${doc}/${doc}_p${padded(page)}_layout_curated.json`,
            `../output/layout/${doc}/${doc}_p${padded(page)}_layout_curated.json`
        ],
        layoutGemini: (doc, page) => [
            `data/pages/${doc}/${doc}_p${padded(page)}_layout_gemini.json`,
            `../output/layout/${doc}/${doc}_p${padded(page)}_layout_gemini.json`
        ],
        layoutDocling: (doc, page) => [
            `data/pages/${doc}/${doc}_p${padded(page)}_layout.json`,
            `../output/layout/${doc}/${doc}_p${padded(page)}_layout.json`
        ],

        ocr: (source, doc, page) => {
            if (source === 'mistral') {
                return [
                    `data/pages/${doc}/${doc}_p${page}.md`,
                    `../output/mistral_results/${doc}_p${page}.md`
                ];
            }
            if (source === 'gemini_corrected_a' || source === 'gemini_corrected_b') {
                const variant = source.endsWith('_a') ? 'a' : 'b';
                return [`../output/gemini_corrected_${variant}/${doc}_p${page}.md`];
            }
            if (source === 'llm_corrected') {
                return [`../output/llm_corrected_c/${doc}_p${page}.md`];
            }
            return [];
        },

        teiPage: (doc, page) => [
            `data/pages/${doc}/${doc}_p${page}.xml`,
            `../output/tei_unified/${doc}/${doc}_p${page}.xml`
        ],
        teiFinal: (doc) => [
            `data/pages/${doc}/${doc}_final.xml`,
            `../output/tei_final/${doc}_final.xml`
        ]
    };

    // ---- Layout-region constants ----
    ZBZ.REGION_TYPES = [
        { value: 'zb_heading',   label: 'Heading',   cls: 'region--heading' },
        { value: 'zb_paragraph', label: 'Paragraph', cls: 'region--paragraph' },
        { value: 'footnote',     label: 'Footnote',  cls: 'region--footnote' },
        { value: 'caption',      label: 'Caption',   cls: 'region--caption' },
        { value: '_filter',      label: 'Filter',    cls: 'region--filter' },
        { value: '_skip',        label: 'Skip',      cls: 'region--skip' }
    ];
    ZBZ.regionTypeCls = (zbzTag) => {
        const t = ZBZ.REGION_TYPES.find(t => t.value === zbzTag);
        return t ? t.cls : 'region--unknown';
    };
    ZBZ.regionTypeLabel = (zbzTag) => {
        const t = ZBZ.REGION_TYPES.find(t => t.value === zbzTag);
        return t ? t.label : (zbzTag || '?');
    };

    // ---- Toast ----
    ZBZ.toast = (msg, type) => {
        let c = document.getElementById('zbz-toast-container');
        if (!c) {
            c = ZBZ.el('div', { attrs: { id: 'zbz-toast-container' } });
            document.body.appendChild(c);
        }
        const el = ZBZ.el('div', { cls: 'toast toast--' + (type || 'info'), text: msg });
        c.appendChild(el);
        requestAnimationFrame(() => el.classList.add('visible'));
        setTimeout(() => {
            el.classList.remove('visible');
            setTimeout(() => el.remove(), 250);
        }, 2800);
    };

    // ---- LRU cache ----
    ZBZ.Cache = class {
        constructor(maxSize) { this._max = maxSize || 50; this._m = new Map(); }
        get(k) {
            if (!this._m.has(k)) return undefined;
            const v = this._m.get(k);
            this._m.delete(k); this._m.set(k, v);
            return v;
        }
        set(k, v) {
            if (this._m.has(k)) this._m.delete(k);
            this._m.set(k, v);
            if (this._m.size > this._max) this._m.delete(this._m.keys().next().value);
        }
        has(k) { return this._m.has(k); }
    };

    // ---- Debounce ----
    ZBZ.debounce = (fn, ms) => {
        let t;
        const debounced = function () {
            const args = arguments, ctx = this;
            clearTimeout(t);
            t = setTimeout(() => fn.apply(ctx, args), ms);
        };
        // cancel: drop a pending call (editors must not commit after detach)
        debounced.cancel = () => clearTimeout(t);
        return debounced;
    };

    // ---- Event bus (simple) ----
    ZBZ.bus = (() => {
        const subs = new Map();
        return {
            on(evt, fn)    { if (!subs.has(evt)) subs.set(evt, []); subs.get(evt).push(fn); },
            emit(evt, arg) { (subs.get(evt) || []).forEach(fn => { try { fn(arg); } catch (e) { console.error(e); } }); }
        };
    })();

    window.ZBZ = ZBZ;
    ZBZ.log('Core', 'ready');
})();
