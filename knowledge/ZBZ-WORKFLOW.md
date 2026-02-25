---
type: knowledge
created: 2026-01-29
updated: 2026-02-25
tags: [zbz-ocr-tei, zbz, workflow, transkribus, oxygen]
status: active
---

# ZBZ-Workflow

Dokumentation des bestehenden Editionsworkflows der ZB Zürich und die Integrationspunkte mit der automatisierten Pipeline.

**Abhängigkeiten:** Keine (Kontext-Dokument)

---

## Bestehender Workflow (manuell)

Der Workflow besteht aus drei parallelen Strängen:

1. **Transkriptionsstrang**: Digitalisat → Transkribus → GitLab → Oxygen → GitLab
2. **Metadatenstrang**: Digitalisat → Alma → Masterfile → Swisscovery → TEI-Header
3. **Korrekturschleife**: Oxygen → PDF → Externe Lesende → Oxygen

Das **Masterfile (Excel)** dient als zentrale Koordinationsinstanz.

---

## Transkriptionsstrang

1. **Digitalisat** → Scans der Digitalisate
2. **Transkribus** [???] → Prozess ist nicht standardisiert
3. **Export** aus Transkribus als XML (manuell, mit TEI XML Export)
4. **GitLab** → Ablegen der Dateien (manuell)
5. **Oxygen** → Weitere XML-Auszeichnungen (manuell)
6. **GitLab** → Aktualisierte XML-Datei ablegen (manuell)

---

## Metadatenstrang

1. **Digitalisat** → Katalogisat in **Alma** anlegen
2. Metadaten aufbereiten und eintragen (manuell)
3. ID von Alma ins **Masterfile** übertragen (manuell)
4. Titel in **Swisscovery** zur Spezialsammlung hinzufügen (manuell)
5. Metadaten für TEI-Header aus Alma → **Workflow fehlt noch**

---

## Korrekturschleife

1. **Oxygen XML** → Export als PDF, visuell wie Scan (Oxygen Transformation)
2. **Externe Lesende** korrigieren das PDF
3. Manuelles Updaten des XMLs in Oxygen

---

## Normdatenverknüpfung

Personen, Institutionen und Werke werden in Oxygen manuell mit **GND-IDs** verlinkt.

---

## Systeme

| System | Funktion | Format |
|--------|----------|--------|
| Transkribus | OCR/HTR und Transkription | [???] - nicht standardisiert |
| Masterfile | Workflow-Steuerung, Statusverfolgung | Excel |
| GitLab | Versionierung der TEI-Dateien | XML |
| Oxygen | TEI-Auszeichnung und Transformation | XML |
| Alma | Katalogisierung und Metadaten | Katalogdaten |
| Swisscovery | Öffentlicher Nachweis | Katalogdaten |
| GND | Normdatenverknüpfung | IDs |

---

## Beobachtungen

- **Fast alle Schritte sind manuell**
- Der **Transkribus-Prozess ist nicht standardisiert** (Fragezeichen im Diagramm)
- Der **TEI-Header-Workflow aus Alma existiert noch nicht**
- Externe Korrekturen erfolgen über **PDF**, nicht direkt am XML
- Unklar, ob XML auf GitLab **überschrieben** wird oder versioniert

---

## Integration: Automatisierte Pipeline

Die drei DHCraft-Tools ersetzen/ergänzen folgende Schritte im bestehenden Workflow:

```
BESTEHEND (manuell)              AUTOMATISIERT (DHCraft-Pipeline)
────────────────────────────────────────────────────────────────

Digitalisat (PDF-Scans)          Digitalisat (PDF-Scans)
        │                                │
  Transkribus [???]              ┌───────┴───────────────┐
        │                        │ zbz-ocr-tei           │
        │                        │ OCR → Layout → PAGE   │
  Manueller Export               │ → NER/GND → TEI-XML   │
        │                        └───────┬───────────────┘
  GitLab (XML ablegen)                   │ TEI-XML (DTA)
        │                                │
  Oxygen (TEI-Auszeichnung)              │
        │                                │
  Oxygen (GND-Verknüpfung)              │
        │                                │
  Externe Korrekturschleife      Finale QS in Oxygen
        │                                │
  [Publikation]                  GitLab → [Publikation]
```

### Konkrete Ersetzungen

| Bestehender Schritt | Ersetzt durch | Tool |
|--------------------|--------------|----|
| Transkribus OCR | Batch-OCR (Mistral/DeepSeek) | zbz-ocr-tei |
| Manueller Transkribus-Export | Automatischer PAGE-XML-Export | zbz-ocr-tei |
| Oxygen TEI-Grundauszeichnung | Automatische TEI-Transformation | zbz-ocr-tei |
| Manuelle GND-Verknuepfung in Oxygen | NER + lobid.org API | zbz-ocr-tei |

### Was bleibt manuell

| Schritt | Grund |
|---------|-------|
| Alma-Katalogisierung | Bibliotheksspezifisch, kein Automatisierungspotenzial |
| Masterfile-Pflege | Koordinationsaufgabe |
| Swisscovery-Zuweisung | Manueller Schritt |
| TEI-Header aus Alma | Workflow fehlt noch (-> [DECISIONS](DECISIONS.md) O8) |
| Finale QS in Oxygen | Letzte manuelle Prüfung vor Publikation |

---

## QA-Dashboard

Ergaenzend zum Produktionsworkflow steht ein automatisch generiertes Dashboard zur Verfuegung (`docs/index.html`):

- Pipeline-Status aller 15 Pilotdokumente
- CER-Vergleich zwischen Engines (Mistral, DeepSeek, LLM-korrigiert)
- Dokumentkatalog mit Engine-Filter
- Viewer mit Faksimile-OCR-Vergleich (`docs/viewer.html`)

Das Dashboard ersetzt `docs/benchmark.html` und dient als zentrales QA-Tool.

---

## Referenzen

- [PROJEKT](PROJEKT.md) fuer Projekt-Scope und Meilensteine
- [PIPELINE](PIPELINE.md) für technische Pipeline-Details
- [DECISIONS](DECISIONS.md) O8 (Alma-Metadaten), O15 (Transkribus-Tags)

---

*Quelle: WorkflowDiagramm_Hersch.pdf — vollständig überführt, PDF gelöscht*
*Erstellt: 2026-01-29 | Aktualisiert: 2026-02-25*
