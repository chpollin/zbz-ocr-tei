---
type: knowledge
created: 2026-03-15
updated: 2026-03-15
tags: [zbz-ocr-tei, edition, frontend, design-system, hersch]
status: active
---

# Design-System

Design-System der digitalen Edition, basierend auf der Jeanne Hersch Design Specification v1.1.

**Dependencies:** [EDITION](EDITION.md) (Frontend-Architektur)

---

## Kernprinzipien

| Entscheidung | Begruendung |
|---|---|
| EB Garamond (Serif) als Grundschrift | Humanistische Tradition des frankophonen Raums |
| Jost (geometrische Sans) fuer Headings | Formale Klarheit als Kontrapunkt |
| Kleine Terz (1.2) als Typoskala | Feine Differenzierung, nicht dramatisch |
| Kein reines Schwarz/Weiss | Denken im Gebrochenen, Relativen |
| Ziegelrot #8B3A3A als Primaer-Akzent | Existenzielle Leiblichkeit |
| Preussischblau #2B4C7E als Sekundaer-Akzent | Universalitaetsanspruch |
| Olivgruen #6B7B5E als Tertiaer-Akzent | Natuerliche Gelassenheit |
| Warmer Anthrazit #2C2825 statt Navy | Materialitaet von Druckerschwarz auf Papier |

---

## Token-Architektur

Zweistufige CSS-Variable-Architektur:

1. **`--h-*` Hersch-Tokens** — Die kanonischen Design-Werte (Farben, Abstufungen)
2. **`--ed-*` Edition-Aliase** — Bestehende Variablen, verweisen auf `--h-*`

Diese Bridge ermoeglicht bruchfreie Migration. CSS-Klassen verwenden weiterhin `ed-*` Prefix.

### Farbpalette

```
Hintergrund:    --h-bg: #F5F0E8 (warm cream)
                --h-bg-alt: #EDE6D8
                --h-surface: #FAFAF7

Text:           --h-text: #2C2825
                --h-text-secondary: #5C554E
                --h-text-muted: #8A8279

Akzente:        --h-ziegelrot: #8B3A3A
                --h-preussischblau: #2B4C7E
                --h-olivgruen: #6B7B5E
```

### Typoskala (Ratio 1.2)

```
xs: 0.694rem | sm: 0.833rem | base: 1rem | lg: 1.2rem
xl: 1.44rem | 2xl: 1.728rem | 3xl: 2.074rem | 4xl: 2.488rem | 5xl: 2.986rem
```

---

## Hersch-spezifische Komponenten

| Komponente | CSS-Klasse | Einsatz |
|---|---|---|
| **Seuil** (Schwellenzone) | `.seuil` | Uebergaenge zwischen Kontexten |
| **Etonnement** (Staunen) | `.etonnement--decale/agrandi/vide/oblique` | Bewusste Brueche im Lesefluss |
| **Polyphonie** | `.polyphonie-grid`, `.voix[data-voix]` | Mehrstimmige Darstellung |
| **Blockquote** | `.blockquote`, `.blockquote-attribution` | Zitate mit Hersch-Stil |
| **Divider** | `.divider-seuil` | Kurzer Trennstrich zwischen Sektionen |
| **Source Label** | `.source-label` | Quellenangabe-Badge |
| **Sprach-Indikator** | `.ed-lang-label` | Inline-Sprach-Label bei `<foreign>` |

---

## Dark Mode

Implementiert via `@media (prefers-color-scheme: dark)`. Alle `--h-*` Tokens werden ueberschrieben.
Nicht mechanisch invertiert, sondern manuell justiert fuer Kontrast und Waerme.

---

## Referenz

Vollstaendige Spezifikation: `Jeanne Hersch Design Specification v1.1` (wird extern verwaltet).
Implementierungsdatei: `docs/css/edition.css`.
