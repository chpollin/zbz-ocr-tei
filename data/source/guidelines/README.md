# Editionsrichtlinien (Quelle)

Verbindliche Auszeichnungsregeln der Edition, von der ZB geliefert. Quelldaten, keine
Projekt-Interpretation -- diese leben in [knowledge/pipeline.md](../../../knowledge/pipeline.md).

## Inhalt

- **[Editionsrichtlinien_ZBZ.md](Editionsrichtlinien_ZBZ.md)** -- autoritatives ZB-Regelwerk:
  div-Typen, GND-Referenzen, Fussnoten-Modell, front/back-Matter, Muster fuer Interview,
  Rezension, Lexikonartikel. Single Source of Truth fuer das TEI-Mapping; speist u.a.
  `VALID_DIV_TYPES` in [scripts/config.py](../../../scripts/config.py).

## DTA-Basisformat

Die Edition folgt dem **DTA-Basisformat** des Deutschen Textarchivs. Die vollstaendige
Spezifikation ist kein Projekt-Artefakt, sondern ein stabiler oeffentlicher Standard und
wird daher nur verlinkt (nicht als Kopie versioniert):

- Grundsaetze: https://www.deutschestextarchiv.de/doku/basisformat/trGrundsaetze.html
- TEI-Struktur: https://www.deutschestextarchiv.de/doku/basisformat/TEIStruktur.html
- Einstiegsseite: https://www.deutschestextarchiv.de/doku/basisformat/

Abweichungen und Ergaenzungen der ZB gegenueber dem DTA-Basisformat sind in
`Editionsrichtlinien_ZBZ.md` dokumentiert.
