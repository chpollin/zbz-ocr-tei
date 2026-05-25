/**
 * core.js — Foundation Layer
 *
 * DOM/URL/Fetch/Format helpers + Data-Path-Resolver.
 * Geladen als ERSTES Script.
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
    ZBZ.fmtNum = (n) => n == null ? '—' : String(n).replace(/\B(?=(\d{3})+(?!\d))/g, '.');
    ZBZ.fmtPct = (v, d) => v == null ? '—' : (v * 100).toFixed(d == null ? 1 : d) + '%';

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
    ZBZ.fetchText = (url) => fetch(url).then(r => r.ok ? r.text() : null).catch(() => null);
    ZBZ.fetchJSON = (url) => fetch(url).then(r => r.ok ? r.json() : null).catch(() => null);
    ZBZ.fetchFirstOk = async (urls) => {
        for (const u of urls) {
            const t = await ZBZ.fetchText(u);
            if (t != null) return { url: u, text: t };
        }
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
    // Primaer: data/pages/{doc}/  (gemirrort durch generate_edition_data.py, alle 285 Docs)
    // Fallback: ../output/...     (nur bei lokalem Server mit Projekt-Root als DocRoot,
    //                              fuer alternative OCR-Engines die nicht versioniert sind)
    const padded = (page) => ZBZ.padPage(page);
    ZBZ.path = {
        image: (doc, page) => `images/${doc}/${doc}_p${padded(page)}.png`,

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
            if (source === 'deepseek') {
                return [`../output/ocr_results/${doc}_p${page}.md`];
            }
            return [];
        },

        teiPage: (doc, page) => [
            `data/pages/${doc}/${doc}_p${page}.xml`,
            `../output/tei_unified/${doc}/${doc}_p${page}.xml`
        ],
        teiFinal: (doc) => [
            `data/tei/${doc}_final.xml`,
            `data/pages/${doc}/${doc}_final.xml`,
            `../output/tei_final/${doc}_final.xml`
        ]
    };

    // ---- Layout-Region-Konstanten ----
    ZBZ.REGION_TYPES = [
        { value: 'zb_heading',   label: 'Heading',   cls: 'region--heading' },
        { value: 'zb_paragraph', label: 'Paragraph', cls: 'region--paragraph' },
        { value: 'footnote',     label: 'Fussnote',  cls: 'region--footnote' },
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

    // ---- LRU Cache ----
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
        return function () {
            const args = arguments, ctx = this;
            clearTimeout(t);
            t = setTimeout(() => fn.apply(ctx, args), ms);
        };
    };

    // ---- Event-Bus (simpel) ----
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
