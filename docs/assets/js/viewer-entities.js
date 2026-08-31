/**
 * viewer-entities.js - Entity layer of the viewer (read-only)
 *
 * Loads the generated entity preview of a document, marks the worklist candidates in
 * the rendered text, and drives the mention popover with label, category, GND link and
 * the provenance the TEI carries (@resp, @source, E118). No save path writes
 * this layer.
 *
 * Namespace: ZBZ.Viewer
 */
(function () {
    'use strict';

    const $$ = ZBZ.$$;
    const V = ZBZ.Viewer;
    const state = V.state;
    const refs  = V.refs;
    const cache = V.cache;
    const {
        ENTITY_INDEX_PATH, entityPagePath, entityWorklistPath,
        ENTITY_CATEGORY_LABEL, ENTITY_MENTION_SEL, ENTITY_POP_SEL, INJECTED_TEXT_SEL,
        assetKnown, candidates
    } = V;

    // Sibling modules, resolved through ZBZ.Viewer at call time (load order independent).
    const setTextSource   = (...a) => V.setTextSource(...a);
    const renderTextPanel = (...a) => V.renderTextPanel(...a);

    // Availability of the entity view and the read-only lock it puts on the text editors
    // are both read by the two dropdowns, which the page module owns.
    function updateEntityUi() {
        ZBZ.bus.emit('entity-mode:changed');
    }

    // Why the tool held back: the matcher rule in plain words. Unknown keys stay raw.
    const WORKLIST_RULE_LABEL = {
        'bare-surname':     'Surname without a full mention',
        'anchored-surname': 'Surname with a full mention in the document',
        'short-title':      'One-word title, ambiguous',
        'legacy-form':      'Form from the legacy index, unconfirmed',
        'adjective-form':   'Adjective form',
        'caps-surname':     'Surname in capitals',
        'ambiguous-surname': 'Surname, several bearers',
        'crosses-markup':   'Mention runs across markup',
        'speaker':          'Speaker line'
    };
    const WORKLIST_RULE_SUFFIX = {
        'ambiguous':    'several candidates',
        'suspect':      'suspected homograph',
        'in-plain-bibl': 'in an unreferenced bibl'
    };
    // Where the matched name form came from (matcher field form_source).
    const ENTITY_FORM_SOURCE_LABEL = {
        'headword':      'List headword',
        'cache-variant': 'GND variant',
        'legacy':        'Legacy index form',
        'surname-index': 'Surname index'
    };
    // Typographic pre-sorting of one-word work titles (matcher field evidence).
    const ENTITY_EVIDENCE_LABEL = {
        'typographic': 'One-word title with typographic evidence',
        'none':        'One-word title without typographic evidence (probably a technical term)'
    };

    function worklistRuleLabel(rule) {
        const parts = String(rule || '').split(':');
        const base = WORKLIST_RULE_LABEL[parts[0]] || parts[0] || 'unknown rule';
        const extra = parts.slice(1).map(s => WORKLIST_RULE_SUFFIX[s] || s).filter(Boolean);
        return extra.length ? base + ' (' + extra.join(', ') + ')' : base;
    }

    // The check line of a candidate: a one-word title is judged by its typography,
    // everything else by the rule that found it.
    function candidateCheckLabel(entry) {
        return ENTITY_EVIDENCE_LABEL[entry.evidence] || worklistRuleLabel(entry.rule);
    }

    // Provenance of the hit: which listed form matched, and from which data channel.
    function candidateOriginLabel(entry) {
        if (!entry.matched_form) return '';
        const source = ENTITY_FORM_SOURCE_LABEL[entry.form_source] || entry.form_source;
        return source ? 'matched via ' + source + ': ' + entry.matched_form : '';
    }

    // Provenance of a marked mention (E118): the TEI carries @resp and @source
    // on the mention itself, the renderer passes them through as data attributes.
    const ENTITY_RESP_LABEL = {
        'resp-entity-matcher':             'deterministic matcher',
        'resp-entity-agent-review':         'AI-agent review',
        'resp-entity-agent-annotation':     'AI-agent annotation',
        'resp-entity-llm-judge':            'independent LLM review',
        'resp-entity-editor-verification':  'editor verified'
    };

    function entityRespLabel(raw) {
        return String(raw || '').split(/\s+/)
            .map(t => t.replace(/^#/, ''))
            .filter(Boolean)
            .map(id => ENTITY_RESP_LABEL[id] || id)
            .join(', ');
    }

    function entityProvenanceRows(el) {
        return [
            ['Provenance', entityRespLabel(el.getAttribute('data-resp'))],
            ['Rule',       el.getAttribute('data-source') || '']
        ].filter(row => row[1]);
    }

    function renderEntityProvenance(pop, el) {
        const rows = entityProvenanceRows(el);
        if (!rows.length) return;
        const box = ZBZ.el('div', { cls: 'entity-pop__prov' });
        rows.forEach(([label, value]) => {
            const row = ZBZ.el('div', { cls: 'entity-pop__prov-row' });
            row.appendChild(ZBZ.el('span', { cls: 'entity-pop__prov-label', text: label }));
            row.appendChild(ZBZ.el('span', { cls: 'entity-pop__prov-value', text: value }));
            box.appendChild(row);
        });
        pop.appendChild(box);
    }

    function candidateAlternatives(entry) {
        return (entry && Array.isArray(entry.alternatives)) ? entry.alternatives : [];
    }

    // ============================================================ Entity layer (read-only) ============================================================

    // Worklist and lookup come from the generated mirror; a document without an entity
    // preview simply keeps the button disabled. The lookup is document-independent and
    // therefore fetched once per session.
    let entityIndex = null;

    async function loadEntityAssets(docId) {
        state.entityWorklist = null;
        state.entityAvailable = false;
        state.entityPage = false;
        // Documents without an entity preview are not asked for one (catalog `assets`).
        const worklist = assetKnown('entity_worklist', 0) !== false
            ? await ZBZ.fetchJSON(entityWorklistPath(docId))
            : null;
        if (worklist) {
            state.entityWorklist = worklist;
            state.entityAvailable = true;
            if (!entityIndex) entityIndex = (await ZBZ.fetchJSON(ENTITY_INDEX_PATH)) || {};
        }
        if (state.entityMode && !state.entityAvailable) {
            state.entityMode = false;
            ZBZ.setParams({ entities: null });
            ZBZ.toast('No entity preview for this document', 'warn');
        }
        if (state.entityMode) {
            // The entity layer is a TEI reading view.
            state.textSource = 'tei';
        }
        updateEntityUi();
    }

    async function loadEntityPage(doc, page) {
        const ck = 'entity:' + doc + ':' + page;
        if (cache.has(ck)) return cache.get(ck);
        // Pages without an entity preview stay usable: null falls back to the pipeline TEI
        const res = await ZBZ.fetchFirstOk(candidates('entity', page, [entityPagePath(doc, page)]));
        const xml = res ? res.text : null;
        if (xml != null) cache.set(ck, xml);
        return xml;
    }

    function setEntityMode(on) {
        const next = !!on;
        if (next === state.entityMode) return;
        if (next && !state.entityAvailable) return;
        state.entityMode = next;
        closeEntityPopover(false);
        if (next && state.textSource !== 'tei') {
            // setTextSource confirms unsaved edits, leaves edit mode and re-renders
            if (!setTextSource('tei')) { state.entityMode = false; updateEntityUi(); return; }
            ZBZ.setParams({ entities: null });
            updateEntityUi();
            return;
        }
        ZBZ.setParams({ entities: next ? null : 0 });
        updateEntityUi();
        renderTextPanel();
    }

    // Surfaces can carry <lb/> tags (names broken across lines); the worklist shows text.
    function plainSurface(surface) {
        return String(surface || '').replace(/<lb\b[^>]*>/g, ' ').replace(/\s+/g, ' ').trim();
    }

    function worklistEntries(page) {
        const pages = state.entityWorklist && state.entityWorklist.pages;
        return (pages && pages[String(page)]) || [];
    }

    function entryText(entry) {
        return entry.text || plainSurface(entry.surface);
    }

    // Candidates are marked in the rendered text itself: the generator says which
    // occurrence of the surface it means, the walker finds it. Whatever cannot be placed
    // is returned and stays visible as a list, so nothing is lost silently.
    function markWorklistCandidates(page) {
        const entries = worklistEntries(page);
        state.entityCandidates = entries;
        const wrap = refs.textBody.querySelector('.tei');
        if (!wrap) return entries.slice();
        const unplaced = [];
        entries.forEach((entry, index) => {
            const span = entry.occurrence
                ? markOccurrence(wrap, entryText(entry), entry.occurrence, index)
                : null;
            if (!span) unplaced.push(entry);
        });
        return unplaced;
    }

    function textNodesOf(root) {
        const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, {
            acceptNode: (node) => (node.parentElement && node.parentElement.closest(INJECTED_TEXT_SEL))
                ? NodeFilter.FILTER_REJECT
                : NodeFilter.FILTER_ACCEPT
        });
        const nodes = [];
        let node;
        while ((node = walker.nextNode())) nodes.push(node);
        return nodes;
    }

    function markOccurrence(root, text, occurrence, index) {
        if (!text) return null;
        const nodes = textNodesOf(root);
        const offsets = [];
        let acc = '';
        nodes.forEach(node => { offsets.push(acc.length); acc += node.nodeValue; });

        // non-overlapping scan, the same convention the generator counted with
        let at = -1, from = 0;
        for (let i = 0; i < occurrence; i++) {
            at = acc.indexOf(text, from);
            if (at < 0) return null;
            from = at + text.length;
        }
        const end = at + text.length;
        const nodeIndex = offsets.findIndex((start, i) => at >= start && at < start + nodes[i].nodeValue.length);
        if (nodeIndex < 0) return null;
        // A hit crossing element boundaries (e.g. an lb inside the name) cannot be wrapped
        // safely; the entry falls back to the list.
        if (end > offsets[nodeIndex] + nodes[nodeIndex].nodeValue.length) return null;

        const entry = state.entityCandidates[index] || {};
        const span = ZBZ.el('span', {
            cls: 'entity-cand',
            attrs: {
                'data-cand-index': String(index),
                role: 'button',
                tabindex: '0',
                'aria-label': text + ', review candidate: ' + worklistRuleLabel(entry.rule)
            }
        });
        const range = document.createRange();
        range.setStart(nodes[nodeIndex], at - offsets[nodeIndex]);
        range.setEnd(nodes[nodeIndex], end - offsets[nodeIndex]);
        try { range.surroundContents(span); } catch (e) { return null; }
        return span;
    }

    // Only what could not be placed inline; the page count itself sits in the legend.
    function renderUnplacedWorklist(unplaced) {
        const old = refs.textBody.querySelector('.entity-worklist');
        if (old) old.remove();
        if (!unplaced.length) return;
        const box = ZBZ.el('aside', {
            cls: 'entity-worklist', attrs: { 'aria-label': 'Worklist entries without a position in the text' }
        });
        box.appendChild(ZBZ.el('div', {
            cls: 'entity-worklist__title', text: 'Not located in the text · ' + unplaced.length
        }));
        const list = ZBZ.el('ul', { cls: 'entity-worklist__list' });
        unplaced.forEach(entry => {
            const li = ZBZ.el('li', { cls: 'entity-worklist__item' });
            li.appendChild(ZBZ.el('span', { cls: 'entity-worklist__surface', text: entryText(entry) }));
            li.appendChild(ZBZ.el('span', {
                cls: 'entity-worklist__rule', text: worklistRuleLabel(entry.rule)
            }));
            li.appendChild(ZBZ.el('span', { cls: 'entity-worklist__context', text: entry.context || '' }));
            list.appendChild(li);
        });
        box.appendChild(list);
        const wrap = refs.textBody.querySelector('.tei');
        refs.textBody.insertBefore(box, wrap || refs.textBody.firstChild);
    }

    // Marked mentions become buttons: the popover carries id, category and lobid link,
    // which the native title tooltip cannot.
    function decorateEntityMentions() {
        const wrap = refs.textBody.querySelector('.tei');
        if (!wrap) return;
        $$(ENTITY_MENTION_SEL, wrap).forEach(el => {
            el.removeAttribute('title');
            el.setAttribute('role', 'button');
            el.setAttribute('tabindex', '0');
            const gid = entityGid(el);
            const rec = entityIndex && entityIndex[gid];
            el.setAttribute('aria-label',
                (rec ? rec.label : el.textContent.trim()) + ', GND ' + gid + ', show details');
        });
    }

    function entityGid(el) {
        return (el.getAttribute('data-ref') || '').replace(/^GND:/, '');
    }

    // ---- Popover ----
    let entityPopover = null;
    let entityPopoverTrigger = null;

    function ensureEntityPopover() {
        if (entityPopover) return entityPopover;
        entityPopover = ZBZ.el('div', {
            cls: 'entity-pop',
            attrs: { role: 'dialog', 'aria-label': 'Entity detail', tabindex: '-1', hidden: 'hidden' }
        });
        document.body.appendChild(entityPopover);
        return entityPopover;
    }

    // One row per bearer of an undecided candidate: label from the entity lookup,
    // id as the lobid link. No bearer is singled out.
    function entityAlternativeRow(gid) {
        const rec = (entityIndex && entityIndex[gid]) || null;
        const row = ZBZ.el('div', { cls: 'entity-pop__gid' });
        row.appendChild(ZBZ.el('span', {
            text: (rec ? rec.label : 'not in the curated entity list') + ' · '
        }));
        row.appendChild(ZBZ.el('a', {
            cls: 'entity-pop__link', text: 'GND ' + gid,
            attrs: {
                href: (rec && rec.lobid) || 'https://lobid.org/gnd/' + encodeURIComponent(gid),
                target: '_blank', rel: 'noopener'
            }
        }));
        return row;
    }

    function showEntityPopover(el) {
        const candidate = el.classList.contains('entity-cand')
            ? (state.entityCandidates[Number(el.getAttribute('data-cand-index'))] || null)
            : null;
        const gid = candidate ? String(candidate.gid || '') : entityGid(el);
        const rec = (entityIndex && entityIndex[gid]) || null;
        // Several bearers mean the position is undecided; showing one of them as the
        // found entity is exactly the misreading this popover has to avoid.
        const alternatives = candidateAlternatives(candidate);
        const undecided = alternatives.length > 1;
        const pop = ensureEntityPopover();
        pop.className = 'entity-pop' + (candidate ? ' entity-pop--cand' : '');
        pop.innerHTML = '';
        pop.appendChild(ZBZ.el('button', {
            cls: 'entity-pop__close', html: '&times;',
            attrs: { type: 'button', 'aria-label': 'Close' },
            on: { click: () => closeEntityPopover(true) }
        }));
        pop.appendChild(ZBZ.el('div', {
            cls: 'entity-pop__label',
            text: (!undecided && rec) ? rec.label : el.textContent.trim()
        }));
        const meta = [];
        if (undecided) {
            meta.push(alternatives.length + ' candidates');
        } else {
            if (rec && rec.category) meta.push(ENTITY_CATEGORY_LABEL[rec.category] || rec.category);
            if (rec && rec.dates) meta.push(rec.dates);
            if (!rec) meta.push('not in the curated entity list');
        }
        pop.appendChild(ZBZ.el('div', { cls: 'entity-pop__meta', text: meta.join(' · ') }));
        if (candidate) {
            // Provenance in plain words: why the tool did not set this annotation,
            // and which listed name form produced the hit.
            pop.appendChild(ZBZ.el('div', {
                cls: 'entity-pop__note',
                text: 'For review: ' + candidateCheckLabel(candidate)
            }));
            const origin = candidateOriginLabel(candidate);
            if (origin) pop.appendChild(ZBZ.el('div', { cls: 'entity-pop__meta', text: origin }));
        } else {
            renderEntityProvenance(pop, el);
        }
        if (undecided) {
            alternatives.forEach(alt => pop.appendChild(entityAlternativeRow(alt)));
        } else {
            pop.appendChild(ZBZ.el('div', { cls: 'entity-pop__gid', text: 'GND ' + (gid || '?') }));
            if (gid) {
                pop.appendChild(ZBZ.el('a', {
                    cls: 'entity-pop__link', text: 'lobid.org',
                    attrs: {
                        href: (rec && rec.lobid) || 'https://lobid.org/gnd/' + encodeURIComponent(gid),
                        target: '_blank', rel: 'noopener'
                    }
                }));
            }
        }
        pop.hidden = false;
        positionEntityPopover(pop, el);
        entityPopoverTrigger = el;
        pop.focus();
        setTimeout(() => document.addEventListener('click', onDocClickForPopover), 0);
    }

    function positionEntityPopover(pop, el) {
        const r = el.getBoundingClientRect();
        pop.style.visibility = 'hidden';
        pop.style.left = '0px';
        pop.style.top = '0px';
        const w = pop.offsetWidth, h = pop.offsetHeight;
        const left = Math.max(8, Math.min(r.left, window.innerWidth - w - 8));
        let top = r.bottom + 6;
        if (top + h > window.innerHeight - 8) top = Math.max(8, r.top - h - 6);
        pop.style.left = left + 'px';
        pop.style.top = top + 'px';
        pop.style.visibility = '';
    }

    function closeEntityPopover(restoreFocus) {
        document.removeEventListener('click', onDocClickForPopover);
        if (!entityPopover || entityPopover.hidden) { entityPopoverTrigger = null; return; }
        entityPopover.hidden = true;
        entityPopover.innerHTML = '';
        if (restoreFocus && entityPopoverTrigger && entityPopoverTrigger.isConnected) {
            entityPopoverTrigger.focus();
        }
        entityPopoverTrigger = null;
    }

    function onDocClickForPopover(e) {
        if (entityPopover && entityPopover.contains(e.target)) return;
        if (e.target.closest && e.target.closest(ENTITY_POP_SEL)) return;
        closeEntityPopover(false);
    }

    Object.assign(ZBZ.Viewer, {
        loadEntityAssets,
        loadEntityPage,
        updateEntityUi,
        setEntityMode,
        worklistEntries,
        markWorklistCandidates,
        renderUnplacedWorklist,
        decorateEntityMentions,
        showEntityPopover,
        closeEntityPopover,
    });

    // A page change invalidates the popover position; closing it is idempotent.
    ZBZ.bus.on('page:changed', () => closeEntityPopover(false));
})();
