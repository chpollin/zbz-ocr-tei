# Projektplan: ZBZ-OCR-TEI Pipeline

**Ziel:** LLM-gestützte Pipeline für 289 Jeanne-Hersch-Texte (7.200 Seiten)
**Workflow:** PDF → Bilder → OCR → Post-Processing → TEI-XML → GND-Verknüpfung

---

## Meilensteine

| # | Meilenstein | Aufwand | Erfolgskriterium |
|---|-------------|---------|------------------|
| M1 | OCR validiert | 5-7 Tage | ≥95% Genauigkeit alle Typen |
| M2 | TEI-Transformation | 6-9 Tage | ≥90% Struktur-Korrektheit |
| M3 | GND-Verknüpfung | 5-6 Tage | ≥85% Precision |
| M4 | Integration | 4-6 Tage | End-to-End ohne Eingriff |
| M5 | Pilotbetrieb | 6-10 Tage | Kundenabnahme |

**Gesamt:** 26-38 Tage (konservativ: 38-50 mit Puffer)

---

## Aktueller Stand (29.01.2026)

| Komponente | Status | Details |
|------------|--------|---------|
| M0 Bildextraktion | ✓ Bereit | `scripts/extract_pages.py` |
| M0 QS-Viewer | ✓ Bereit | `docs/` mit GitHub Pages |
| M1.1 Spalten-Problem | Blockiert | Docling: Windows-Fehler, DeepSeek: GPU-Last |
| M1 Phase 1 | ✓ Erledigt | 94.4% Genauigkeit (Typ A) |
| M1 Phase 2-4 | Ausstehend | GPU erforderlich |
| M2.1 TEI-Templates | ✓ Erledigt | 5 Templates erstellt |
| M3.1 GND-Seed | ✓ Erledigt | 75 Entitäten extrahiert |

---

## Abhängigkeiten

```
M0 (Bilder) ─────────────────────┐
  └── Einmalig, parallel zu OCR  │
                                 ▼
M1 (OCR) ◄─────────────────────── M0 Bilder vorhanden
  └── Spalten-Problem blockiert  │
                                 ▼
M2 (TEI) ◄────────────────────── M1 fertig
                                 │
M3 (GND) ◄────────────────────── M2 empfohlen
                                 │
M4 (Integration) ◄────────────── M2 fertig
                                 │
M5 (Pilot) ◄──────────────────── M4 fertig
```

### M0: Bildextraktion & QS-Viewer (NEU)

| Schritt | Beschreibung | Status |
|---------|--------------|--------|
| 0.1 | PDF → PNG (150 DPI) | Skript bereit |
| 0.2 | QS-Viewer (Bild + OCR) | HTML bereit |
| 0.3 | GitHub Pages aktivieren | Ausstehend |

**Vorteil:** Visuelle QS parallel zur OCR-Entwicklung möglich

---

## Risiken

| Risiko | Impact | Mitigation |
|--------|--------|------------|
| Spalten-Problem unlösbar | Hoch | Cloud-VM für Docling, notfalls manuell |
| TEI zu komplex für LLM | Hoch | Hybrid: Regeln + LLM |
| GND-Halluzinationen | Mittel | Zweistufig: NER → API-Validierung |

---

## OCR-Strategie (Empfehlung)

| Dokumenttyp | Tool | Status |
|-------------|------|--------|
| A (einspaltig) | DeepSeek-OCR-2 | ✓ Validiert |
| B (zweispaltig) | Docling | Zu testen |
| C (Monografie) | DeepSeek + Chunking | Ausstehend |
| D (Spezial) | Fallweise | Ausstehend |

---

## Kosten

| Posten | Betrag |
|--------|--------|
| LLM-API (289 Docs) | 6-15 USD |
| GPU-Cloud (optional) | ~10-20 USD |

---

*Aktualisiert: 29.01.2026*
