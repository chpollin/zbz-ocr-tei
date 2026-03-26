/**
 * ZBZ Edition – Shared Module
 * Navigation, Data Loading, Utilities.
 * Namespace: ZBZ.Shared (ES6+, IIFE)
 */
(function () {
    'use strict';

    window.ZBZ = window.ZBZ || {};
    const _logStyles = 'color:#2C2825;font-weight:600';
    function _log(mod, msg) { console.log(`%c[ZBZ:${mod}]%c ${msg}`, _logStyles, ''); }
    if (!ZBZ.log) ZBZ.log = _log;

    // --- DOM helpers ---
    const $ = (sel, ctx) => (ctx || document).querySelector(sel);
    const $$ = (sel, ctx) => [...(ctx || document).querySelectorAll(sel)];

    function esc(s) {
        if (s == null) return '';
        return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
    }

    // --- Formatting ---
    function formatNumber(n) {
        if (n == null) return '\u2014';
        return String(n).replace(/\B(?=(\d{3})+(?!\d))/g, '.');
    }

    function formatPercent(v, decimals) {
        if (v == null) return '\u2014';
        return (v * 100).toFixed(decimals != null ? decimals : 1) + '%';
    }

    function formatDate(isoStr) {
        if (!isoStr) return '\u2014';
        return isoStr.replace('T', ' ').slice(0, 19);
    }

    // --- URL Parameters ---
    function getParam(key) {
        return new URLSearchParams(window.location.search).get(key);
    }

    function setParam(key, value) {
        const u = new URLSearchParams(window.location.search);
        if (value == null) u.delete(key); else u.set(key, value);
        const s = u.toString();
        history.replaceState(null, '', window.location.pathname + (s ? `?${s}` : ''));
    }

    // --- Data Loaders ---
    function fetchJSON(path) {
        return fetch(path)
            .then(r => { if (!r.ok) return null; return r.json(); })
            .catch(() => null);
    }

    function fetchTEI(docId) {
        const clean = String(docId).replace(/[^0-9]/g, '');
        if (!clean) return Promise.resolve(null);
        const isInfra = window.location.pathname.indexOf('/infrastruktur/') > -1;
        const prefix = isInfra ? '../' : '';
        const paths = [
            `${prefix}data/tei/${clean}_final.xml`,
            `${prefix}data/examples/${clean}/${clean}_final.xml`
        ];
        return _fetchFirstOk(paths);
    }

    function _fetchFirstOk(urls) {
        if (!urls.length) return Promise.resolve(null);
        return fetch(urls[0]).then(r => {
            if (r.ok) return r.text();
            return _fetchFirstOk(urls.slice(1));
        }).catch(() => _fetchFirstOk(urls.slice(1)));
    }

    // --- Table Sorting ---
    function makeSortable(tableEl) {
        if (!tableEl) return;
        const headers = $$('th.sortable', tableEl);
        const tbody = $('tbody', tableEl);
        if (!headers.length || !tbody) return;

        let sortCol = null;
        let sortAsc = true;

        headers.forEach(th => {
            th.addEventListener('click', () => {
                const col = th.cellIndex;
                if (sortCol === col) { sortAsc = !sortAsc; }
                else { sortCol = col; sortAsc = true; }

                headers.forEach(h => h.classList.remove('sort-asc', 'sort-desc'));
                th.classList.add(sortAsc ? 'sort-asc' : 'sort-desc');

                const rows = [...tbody.rows];
                rows.sort((a, b) => {
                    const aEl = a.cells[col];
                    const bEl = b.cells[col];
                    if (!aEl || !bEl) return 0;
                    const aKey = aEl.dataset.sort != null ? aEl.dataset.sort : aEl.textContent.trim();
                    const bKey = bEl.dataset.sort != null ? bEl.dataset.sort : bEl.textContent.trim();
                    const aNum = parseFloat(aKey);
                    const bNum = parseFloat(bKey);
                    if (!isNaN(aNum) && !isNaN(bNum)) {
                        return sortAsc ? aNum - bNum : bNum - aNum;
                    }
                    return sortAsc ? aKey.localeCompare(bKey) : bKey.localeCompare(aKey);
                });
                rows.forEach(r => tbody.appendChild(r));
            });
        });
    }

    // --- Navigation ---
    const NAV_ITEMS = [
        { label: 'Start', href: 'index.html' },
        { label: 'Katalog', href: 'catalog.html' },
        { label: 'Register', href: 'register.html' },
        { label: 'Diagnostik', href: 'infrastruktur/diagnostik.html' },
        { label: 'Viewer', href: 'infrastruktur/viewer.html' }
    ];

    const ICON_HAMBURGER = '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 12h18M3 6h18M3 18h18"/></svg>';

    function renderNav() {
        const target = $('#ed-nav-slot');
        if (!target) return;

        const path = window.location.pathname;
        const isInfra = path.indexOf('/infrastruktur/') > -1;
        const hrefPrefix = isInfra ? '../' : '';

        const links = NAV_ITEMS.map(item => {
            const href = hrefPrefix + item.href;
            let active = false;
            if (item.href.indexOf('infrastruktur/') === 0) {
                // Active if the current path matches this infra item
                const itemFile = item.href.split('/').pop();
                active = isInfra && path.indexOf(itemFile) > -1;
            } else if (!isInfra) {
                if (item.href === 'index.html') {
                    active = /\/index\.html$/.test(path) || /\/docs\/?$/.test(path);
                } else {
                    active = path.indexOf(item.href) > -1;
                }
            }
            return `<li><a href="${href}"${active ? ' class="active"' : ''}>${item.label}</a></li>`;
        }).join('');

        target.innerHTML =
            `<div class="ed-nav-inner">` +
            `<a href="${hrefPrefix}index.html" class="ed-nav-brand">Nachlass Hersch</a>` +
            `<button class="ed-nav-hamburger" id="nav-hamburger" aria-label="Navigation" aria-expanded="false">${ICON_HAMBURGER}</button>` +
            `<ul class="ed-nav-links" id="ed-nav-links">${links}</ul></div>`;
    }

    // --- Banner ---
    function renderBanner() {
        const slot = $('#ed-banner-slot');
        if (!slot) return;
        const isInfra = window.location.pathname.indexOf('/infrastruktur/') > -1;
        const p = isInfra ? '../' : '';
        slot.innerHTML =
            `<div class="ed-banner-inner">` +
            `<span class="ed-banner-badge">Experimentell</span>` +
            `<span>Promptotyping-Edition &mdash; KI-gestuetzte Texterzeugung in laufender Kuration. ` +
            `<a href="${p}about.html#promptotyping">Zur Methodik</a></span></div>`;
    }

    // --- Footer ---
    function renderFooter() {
        const target = $('#ed-footer-slot');
        if (!target) return;
        const isInfra = window.location.pathname.indexOf('/infrastruktur/') > -1;
        const p = isInfra ? '../' : '';
        target.innerHTML =
            `<div class="ed-footer-links">` +
            `<a href="${p}index.html">Startseite</a>` +
            `<a href="${p}catalog.html">Katalog</a>` +
            `<a href="${p}register.html">Register</a>` +
            `<a href="${p}about.html">Projekt</a>` +
            `<a href="${p}infrastruktur/diagnostik.html">Diagnostik</a>` +
            `</div>` +
            `<p class="ed-footer-disclaimer">Experimentelle Promptotyping-Edition &mdash; KI-gestuetzte Texterzeugung in laufender Kuration. ` +
            `<a href="${p}about.html#promptotyping">Methodik</a></p>` +
            `<p>Zentralbibliothek Zuerich &middot; DHCraft &middot; 2026</p>`;
    }

    // --- Init Navigation Interactions ---
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

    // --- Boot ---
    function init() {
        renderNav();
        renderBanner();
        renderFooter();
        initNav();
        const page = window.location.pathname.split('/').pop() || 'index.html';
        _log('Shared', `${page} | nav + banner + footer ready`);
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    // --- Public API ---
    ZBZ.Shared = {
        $, $$, esc,
        formatNumber, formatPercent, formatDate,
        getParam, setParam,
        fetchJSON, fetchTEI,
        makeSortable,
        NAV_ITEMS
    };
})();
