# Quelldaten

Dieses Verzeichnis enthält die Eingabedaten für das Projekt.
**Nicht versioniert** (in .gitignore) – vom ZBZ bereitgestellt.

## Struktur

```
data/
├── scans/                    # 286 PDF-Scans (Datenlieferung Feb 2026)
│   └── *.pdf                 # Benannt nach Projekt-ID (z.B. 2310.pdf)
│
├── referenz-tei/             # 25 Referenz-TEI-Dateien (ZBZ-annotiert, DTA-Basisformat)
│   └── *.xml                 # Benannt nach Projekt-ID (z.B. 2310.xml)
│
├── page-xml-transkribus/     # 24 Transkribus-Exporte (PAGE-XML Schema 2013-07-15)
│   └── {doc_id}/             # Pro Dokument ein Ordner
│       ├── mets.xml          # METS-Manifest
│       ├── metadata.xml      # Transkribus-Metadaten
│       └── page/             # PAGE-XML pro Seite (leer, kein Text)
│           └── *.xml
│
├── richtlinien/              # ZBZ-Projektrichtlinien
│   ├── dta_basisformat_komplett.md           # DTA-Referenz
│   └── Page-xml-Export Einstellungen.jpg     # Transkribus-Export-Einstellungen
│
└── projektsteuerung/         # ZBZ-Projektdaten
    └── *.xlsx                # Arbeitslisten
```

## Datenlieferung

**HerschStandFeb (Feb 2026):** 286 PDFs, 25 TEI-XMLs, 24 PAGE-XML-Exporte.
Dokumentiert in [QUELLENANALYSE](../knowledge/QUELLENANALYSE.md) §Datenlieferung und [DECISIONS](../knowledge/DECISIONS.md) E23.

| Kategorie | Anzahl | Quelle |
|-----------|--------|--------|
| PDFs mit TEI + PAGE-XML | 24 | ZBZ Transkribus (Collection 1886177) |
| PDFs ohne Annotation | 262 | ZBZ Digitalisierung |
| TEI-XMLs | 25 | Fertige Annotationen (1 XML ohne zugehoeriges PDF) |

## Hinweis

Das `data/`-Verzeichnis ist von Git ausgeschlossen, um sensible Daten und große Dateien nicht zu versionieren.
