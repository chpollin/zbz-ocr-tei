/**
 * ZBZ Entity Utilities -- Shared entity resolution and extraction.
 * Used by both pipeline viewer (tei-viewer.js) and edition viewer (edition-tei.js).
 * Namespace: ZBZ.EntityUtils (ES5, IIFE)
 */
(function () {
    'use strict';

    window.ZBZ = window.ZBZ || {};

    /**
     * Resolve an entity reference string to a typed result.
     * @param {string} ref - e.g. "#zbz-p.1", "WD:Q123", "GND:123"
     * @param {function} lookupFn - Entity index lookup (ZBZ.lookupEntity or E.lookupEntity)
     * @returns {object|null} {type, id, label, url} or null
     */
    function resolveEntityRef(ref, lookupFn) {
        if (!ref) return null;
        // Primaer: Index-Lookup (#zbz-p.1 -> entity_index.json)
        if (ref.indexOf('#zbz-') === 0) {
            var entry = lookupFn(ref);
            if (entry && entry.wikidata_qid) {
                return { type: 'wikidata', id: entry.wikidata_qid,
                         label: entry.name,
                         url: entry.wikidata_url };
            }
            // Fallback: GND aus Wikidata P227
            if (entry && entry.gnd_id) {
                var gid = entry.gnd_id.replace('GND:', '');
                return { type: 'gnd', id: gid, label: entry.name,
                         url: 'https://lobid.org/gnd/' + gid };
            }
            if (entry) {
                return { type: 'index', id: ref.slice(1), label: entry.name, url: null };
            }
            return { type: 'index', id: ref.slice(1), label: ref, url: null };
        }
        // Fallback: direkte WD/GND Refs (Legacy)
        if (ref.indexOf('WD:') === 0) {
            var qid = ref.replace('WD:', '');
            return { type: 'wikidata', id: qid, label: 'WD:' + qid,
                     url: 'https://www.wikidata.org/wiki/' + qid };
        }
        if (ref.indexOf('GND:') === 0) {
            var gndId = ref.replace('GND:', '');
            if (gndId !== 'unknown') {
                return { type: 'gnd', id: gndId, label: 'GND:' + gndId,
                         url: 'https://lobid.org/gnd/' + gndId };
            }
        }
        return null;
    }

    /**
     * Resolve all available links for an entity reference.
     * @param {string} ref - e.g. "#zbz-p.1", "WD:Q123", "GND:123"
     * @param {function} lookupFn - Entity index lookup
     * @returns {object} {zbzId, label, links: [{type, id, url}]}
     */
    function resolveAllLinks(ref, lookupFn) {
        var result = { zbzId: null, label: ref || '', links: [] };
        if (!ref) return result;

        if (ref.indexOf('#zbz-') === 0) {
            result.zbzId = ref.slice(1);
            var entry = lookupFn(ref);
            if (entry) {
                result.label = entry.name;
                if (entry.wikidata_qid) {
                    result.links.push({ type: 'wikidata', id: entry.wikidata_qid,
                        url: entry.wikidata_url });
                }
                if (entry.gnd_id) {
                    var gid = entry.gnd_id.replace('GND:', '');
                    result.links.push({ type: 'gnd', id: gid,
                        url: 'https://lobid.org/gnd/' + gid });
                }
            }
            return result;
        }
        if (ref.indexOf('WD:') === 0) {
            var qid = ref.replace('WD:', '');
            result.label = 'WD:' + qid;
            result.links.push({ type: 'wikidata', id: qid,
                url: 'https://www.wikidata.org/wiki/' + qid });
            return result;
        }
        if (ref.indexOf('GND:') === 0) {
            var gndId = ref.replace('GND:', '');
            if (gndId !== 'unknown') {
                result.label = 'GND:' + gndId;
                result.links.push({ type: 'gnd', id: gndId,
                    url: 'https://lobid.org/gnd/' + gndId });
            }
        }
        return result;
    }

    /**
     * Create a DOM span for an entity with tooltip and click handler.
     * @param {Element} node - Source XML element
     * @param {string} type - Entity type (person, org, place, work)
     * @param {string} ref - Ref attribute value
     * @param {string} cssPrefix - CSS class prefix ('tei-entity' or 'ed-tei-entity')
     * @param {function} lookupFn - Entity index lookup function
     * @returns {Element}
     */
    function createEntitySpan(node, type, ref, cssPrefix, lookupFn) {
        var span = document.createElement('span');
        span.className = cssPrefix + ' ' + cssPrefix + '-' + type;
        if (ref) {
            span.setAttribute('data-ref', ref);
            var resolved = resolveEntityRef(ref, lookupFn);
            if (resolved && resolved.url) {
                span.addEventListener('click', function () {
                    window.open(resolved.url, '_blank');
                });
            }
            var all = resolveAllLinks(ref, lookupFn);
            var tipText = all.label;
            if (all.zbzId) tipText += ' (' + all.zbzId + ')';
            var tip = document.createElement('span');
            tip.className = cssPrefix + '-tip';
            tip.textContent = tipText;
            span.appendChild(tip);
        }
        return span;
    }

    /**
     * Extract entities from a parsed TEI XML document.
     * @param {Document} doc - Parsed XML document
     * @returns {object} {persons: [], orgs: [], places: [], works: []}
     */
    function extractEntities(doc) {
        var entities = { persons: [], orgs: [], places: [], works: [] };
        _addFromQuery(doc, 'persName[ref]', entities, 'persons', 'ref');
        _addFromQuery(doc, 'orgName[ref]', entities, 'orgs', 'ref');
        _addFromQuery(doc, 'placeName[ref]', entities, 'places', 'ref');
        _addFromQuery(doc, 'bibl[ref]', entities, 'works', 'ref');
        _addFromQuery(doc, 'bibl[corresp]:not([ref])', entities, 'works', 'corresp');
        return entities;
    }

    function _addFromQuery(doc, selector, entities, listKey, attrName) {
        var nodes = doc.querySelectorAll(selector);
        for (var i = 0; i < nodes.length; i++) {
            var name = nodes[i].textContent.trim();
            var ref = nodes[i].getAttribute(attrName);
            if (!name || !ref) continue;
            var found = false;
            for (var j = 0; j < entities[listKey].length; j++) {
                if (entities[listKey][j].ref === ref) {
                    entities[listKey][j].count++;
                    found = true;
                    break;
                }
            }
            if (!found) {
                entities[listKey].push({ name: name, ref: ref, count: 1 });
            }
        }
    }

    ZBZ.EntityUtils = {
        resolveEntityRef: resolveEntityRef,
        resolveAllLinks: resolveAllLinks,
        createEntitySpan: createEntitySpan,
        extractEntities: extractEntities
    };
})();
