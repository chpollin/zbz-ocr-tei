# Workflow Diagramm Hersch

Dokumentation des Editionsworkflows der ZB Zürich für den Nachlass Jeanne Hersch.

---

## Übersicht

Der Workflow besteht aus drei parallelen Strängen, die vom Digitalisat ausgehen:

1. **Transkriptionsstrang**: Digitalisat → Transkribus → GitLab → Oxygen → GitLab
2. **Metadatenstrang**: Digitalisat → Alma → Masterfile → Swisscovery → TEI-Header
3. **Korrekturschleife**: Oxygen → PDF → Externe Lesende → Oxygen

Das **Masterfile (Excel)** dient als zentrale Koordinationsinstanz und hält den Prozessstatus für alle Stufen fest.

---

## Ausgangspunkt

- **Digitalisierung ist abgeschlossen**: PDF-Scans der Digitalisate liegen vor
- **Masterfile (Excel)** koordiniert alle Prozessschritte und hält den Status für alle Stufen fest

---

## Transkriptionsstrang

1. **Digitalisat** → Scans der Digitalisate
2. **Transkribus** [???] → Prozess ist nicht standardisiert
3. **Export** aus Transkribus als XML (manuell, mit TEI XML Export)
4. **GitLab** → Ablegen der Dateien (manuell)
5. **Oxygen** → Weitere XML-Auszeichnungen (manuell)
6. **GitLab** → Aktualisierte XML-Datei ablegen (überschrieben?) (manuell)

---

## Metadatenstrang

1. **Digitalisat** → Katalogisat in **Alma** anlegen
2. Metadaten aufbereiten und eintragen (manuell)
3. ID von Alma ins **Masterfile** übertragen (manuell)
4. Titel in **Swisscovery** zur Spezialsammlung hinzufügen (manuell)
5. Metadaten für TEI-Header aus Alma → **Workflow fehlt noch**

---

## Korrekturschleife

1. **Oxygen XML** → Export als PDF, visuell möglichst wie Scan (Oxygen Transformation)
2. **Externe Lesende** korrigieren das PDF
3. Manuelles Updaten des XMLs in Oxygen gemäss Korrekturen

---

## Normdatenverknüpfung

Personen, Institutionen und Werke werden in Oxygen manuell mit **GND-IDs** verlinkt.

---

## Systeme

| System | Funktion | Format |
|--------|----------|--------|
| Transkribus | OCR/HTR und Transkription | [???] – nicht standardisiert |
| Masterfile | Workflow-Steuerung, Statusverfolgung (alle Stufen) | Excel |
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

*Quelle: WorkflowDiagramm_Hersch.pdf – vollständig überführt, PDF gelöscht*