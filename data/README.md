# Quelldaten

Dieses Verzeichnis enthält die Eingabedaten für das Projekt.
**Nicht versioniert** (in .gitignore) – manuell vom ZBZ bereitgestellt.

## Struktur

```
data/
├── scans/              # PDF-Scans der Dokumente
│   └── *.pdf           # Benannt nach Projekt-ID (z.B. 2310.pdf)
│
├── referenz-tei/       # Referenz-TEI-Dateien (ZBZ-annotiert)
│   ├── Pilot/          # 18 annotierte Pilot-Dokumente
│   └── *.xml
│
├── richtlinien/        # ZBZ-Projektrichtlinien
│   ├── README.md       # Projektübersicht
│   └── dta_basisformat_komplett.md  # DTA-Referenz
│
└── projektsteuerung/   # ZBZ-Projektdaten
    └── *.xlsx          # Arbeitslisten
```

## Dateien beschaffen

Die Dateien werden vom ZBZ bereitgestellt:
1. PDFs aus dem Digitalisierungsprojekt
2. Referenz-TEI aus Transkribus-Export
3. Richtlinien aus der internen Dokumentation

## Hinweis

Das `data/`-Verzeichnis ist von Git ausgeschlossen, um sensible Daten und große Dateien nicht zu versionieren.
