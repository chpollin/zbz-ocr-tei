# ZBZ facsimile image-URL scheme and teiCrafter render notes

Detail liegt in `reports/`; dies ist die verdichtete, handlungsorientierte Fassung.
Zeitpunktbezogen (2026-06-07), gegen Code prüfen.

---

## Offene Punkte
1. **Entscheidung:** Bild-URL-Strategie für `<graphic url>` = **absolute gehostete URL** (empfohlen)
   vs. vendored Gleich-Origin. (Default-Empfehlung: absolut, siehe unten.)
2. **Code (M2.2):** `facsimile.js`/`edition.js` `<graphic url>` aus `<surface>` lesen
   (`surface.graphic` → imageUrl). **Über `<surface>` iterieren, `K` aus `xml:id` parsen** —
   nicht laufende Position ab 1 annehmen (Edge Case 2310).
3. Sobald M2.2 steht, folgt der Live-Render-Check (M2.3) mit ausgefüllter Render-Tabelle.

## M2.4 — Bild-URL-Schema (kopierfertig)
Für jedes `<surface xml:id="facs_K" …>`: Bild = `{id}_p{KKK}.png`, `KKK` = Ganzzahl `K`, 3-stellig.
- Beleg: Viewer baut identisch in `docs/assets/js/core.js:171` + `padPage` `core.js:113`.
- `K` = Scan-Position, **NICHT** `@n` (gedruckte Seitenzahl; z. B. `facs_2 n="566"`).
- `<graphic>` als erstes Kind *im* `<surface>`, vor `<zone>`. Schema-konform
  (`zbz_hersch.rng:3518`, bestätigt auch in integration.md §12).
- **Deployment (live, HTTP 200):** `https://chpollin.github.io/zbz-ocr-tei/images/<id>/<id>_p{KKK}.png`
  (GitHub Pages, `docs/images` git-getrackt). **Kein IIIF.** teiCrafter liegt auf eigener Origin →
  Cross-Origin-Anzeige via `<img>`/OSD `type:'image'` ok.
- **Edge Case 2310:** 3 Bilder, 2 Surfaces (`facs_2`, `facs_3`); `p001` ist Bild **ohne Surface**
  (Cover). → über `<surface>` iterieren.

## Empfohlenes Demo-Objekt
**`1540` „Mein Judentum"** (DE): Person+Ort+Org+**Werk** in einem Objekt (inkl. Herschs Werktitel,
Folio 3). Alternative **`2310` „Philosophie"** für Werk-Fokus + übt `foreign/note/hi`. Fundstellen:
`reports/cc3-bericht-m2-2026-06-07.md` §2.

## Status der ZBZ-Tests (Detail: `reports/test-plan-zbz-teicrafter-2026-06-07.md`)
- ✓ jetzt: Schema-Validierung Injektion, Surface→Bild-Mapping, URL-200, Round-Trip, Laden (285/285),
  Rendering `hi/foreign/note/figure`, `choice` (Doc 110).
- ✗ blockiert auf M2.2: Bildanzeige, Cross-Origin, Zonen-Pixel-Deckung.
- ⚠ nicht testbar: **`unclear` = 0 Docs korpus-weit**; auf ZBZ als N/A melden.
- Priorität-Safety: **H1** — TEI-XML-Edit darf nicht das ganze `_final.xml` überschreiben
  (aus Code abgeleitet, noch unreproduziert).

## Verifikation
`curl -I https://chpollin.github.io/zbz-ocr-tei/images/1000/1000_p001.png` → 200 ·
`grep -rl "<unclear" output/tei_final/*.xml` → 0 · `grep -rl "<choice" …` → 6 ·
`grep -n graphic data/schema/zbz_hersch.rng` → 3518 ·
`node test/tools/{roundtrip_sweep,hersch_loadability}.mjs` (teiCrafter).

## Sources
- `reports/cc3-bericht-m2-2026-06-07.md` — M2.4-Schema, Demo-Objekt, Render-Vorbereitung, Synthese-Fix.
- `reports/test-plan-zbz-teicrafter-2026-06-07.md` — vollständiger Testplan (T1–T9, jetzt-testbar).
