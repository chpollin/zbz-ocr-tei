# Workflow Diagramm Hersch

Visualisierung des Editionsworkflows der ZB Zürich für den Nachlass Jeanne Hersch.

## Ausgangspunkt

PDF-Scans (Digitalisate) bilden das Eingangsmaterial. Die Koordination aller Prozessschritte erfolgt über das Masterfile (Excel).

## Transkriptionsstrang

Digitalisat → Transkribus (Prozess variabel) → manueller TEI-XML-Export → GitLab → manuelle Auszeichnung in Oxygen → aktualisierte XML zurück auf GitLab

## Metadatenstrang

Digitalisat → Katalogisat in Alma anlegen (manuell) → Alma-ID ins Masterfile übertragen (manuell) → Titel in Swisscovery zur Spezialsammlung hinzufügen (manuell) → Metadaten für TEI-Header aus Alma (Workflow fehlt noch)

## Korrekturschleife

Oxygen XML → PDF-Export (visuell nah am Scan) → externe Lesende korrigieren → Korrekturen manuell ins XML übernehmen

## Normdatenverknüpfung

Personen, Institutionen und Werke werden in Oxygen manuell mit GND-IDs verlinkt.

## Systeme

| System | Funktion | Format |
|--------|----------|--------|
| Transkribus | OCR/HTR und Transkription | [variabel] |
| Masterfile | Workflow-Steuerung und Statusverfolgung | Excel |
| GitLab | Versionierung der TEI-Dateien | XML |
| Oxygen | TEI-Auszeichnung und Transformation | XML |
| Alma | Katalogisierung und Metadaten | Katalogdaten |
| Swisscovery | Öffentlicher Nachweis | Katalogdaten |
| GND | Normdatenverknüpfung | IDs |

## Beobachtungen

Fast alle Schritte sind manuell. Der Transkribus-Prozess ist nicht standardisiert (Fragezeichen im Diagramm). Der TEI-Header-Workflow aus Alma existiert noch nicht. Externe Korrekturen erfolgen über PDF, nicht direkt am XML.