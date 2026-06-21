# ZBZ-Lieferung 2026-06-21

Referenz-Snapshot der vom Projektpartner ZB Zuerich uebergebenen Materialien, gesichert
aus der fluechtigen Drop-Inbox (`Downloads/`). Unveraendert uebernommen.

- `README.md` -- vollstaendige, aktuelle Editionsrichtlinie der ZBZ (umfangreicher als die
  aeltere Kopie `data/source/guidelines/Editionsrichtlinien_ZBZ.md`).
- `zbz_hersch.rng` -- die zugehoerige ZBZ-Pruefvorlage (RelaxNG).

## Status

Referenz, nicht aktive Source of Truth. Das aktive Schema bleibt `data/schema/zbz_hersch.rng`.
Ob und wie dieser Snapshot das aktive Schema ersetzt, ist offen (siehe [[decisions#O26|O26]]
und `forschungsleitstelle/reports/klaerung-zbz-ocr-tei.md`, Punkt B).

## Verifizierter Befund (2026-06-21)

- Das ZBZ-Schema kennt kein `standOff`-Register; es traegt nur das Inline-Modell
  (`persName`/`orgName` mit GND-Referenz). Die README schreibt durchgaengig Inline-GND vor
  (Person/Organisation/Werk direkt am Text, Referenz immer auf die GND). Damit ist das
  Auszeichnungsmodell der Auslieferung Inline-GND, nicht das standOff-Modell aus E87.
- Schema-Abgleich gegen den Repo-Stand vor E87 (HEAD 643b2f21): nach Zeilenenden-Bereinigung
  99 echte Unterschiede. Dem ZBZ-Schema fehlen die E68-Kopf-Elemente (`revisionDesc`/`change`,
  `langUsage`, `idno` im publicationStmt, `monogr`/`imprint`), dort `<notAllowed/>`. Eine rohe
  Uebernahme wuerde alle 285 ausgelieferten Dateien invalidieren.
- Widerspruch im ZBZ-Material: die README fordert ID/MMSID/PubForm im Header (Z. 107-108),
  das ZBZ-Schema verbietet aber `idno` im publicationStmt. An ZBZ zurueckzuspielen.
