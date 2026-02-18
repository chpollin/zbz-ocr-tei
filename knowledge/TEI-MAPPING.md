---
type: knowledge
created: 2026-01-29
updated: 2026-02-18
tags: [zbz-ocr-tei, tei, dta, mapping, transformation]
status: active
---

# TEI-Mapping

Transformationsregeln von Quelltext zu TEI-XML nach DTA-Basisformat mit projektspezifischen Anpassungen.

**Abhängigkeiten:** [QUELLENANALYSE](QUELLENANALYSE.md)

**Quellen:**
- `data/richtlinien/README.md` – Projektrichtlinien ZBZ
- `data/richtlinien/dta_basisformat_komplett.md` – DTA-Referenz
- `data/richtlinien/Auszeichnungsrichtlinien Hersch INTERN.docx` – Interne Richtlinien

**Offene Fragen:** Siehe [DECISIONS](DECISIONS.md) O6-O9, O13-O14.

---

## Grundprinzipien

1. **Zeichengetreuer Lesetext** mit Registererschließung
2. **DTA-Basisformat** als Grundlage mit projektspezifischen Anpassungen
3. **Normalisierung** bestimmter Zeichen (keine diplomatische Transkription)
4. **Jede Entität wird verlinkt**, auch bei Wiederholung
5. **Vorlagengetreue Transkription** – Originaltext wird bewahrt

---

## Dokumentstruktur

### Grundgerüst

```xml
<?xml version='1.0' encoding='UTF-8'?>
<TEI xmlns='http://www.tei-c.org/ns/1.0' type="naegeli">
  <teiHeader>
    <!-- wird per Skript aus ALMA befüllt -->
    <!-- enthält: Projektinterne ID, MMSID, PubForm (book, bookSection, journalArticle) -->
  </teiHeader>
  <text>
    <front><!-- optional: Vorreden, Entstehungskontext --></front>
    <body>
      <pb facs="#f0001" n="1"/>  <!-- erste Seitenzahl VOR div n="1" -->
      <div n="1"><!-- Hauptstruktur --></div>
    </body>
    <back><!-- optional: Übersetzungs-/Nachdruckhinweise --></back>
  </text>
</TEI>
```

### Hierarchische Gliederung

| Ebene | Element | Verwendung |
|-------|---------|------------|
| 1 | `<div n="1">` | Hauptkapitel |
| 2 | `<div n="2">` | Unterkapitel |
| 3 | `<div n="3">` | Abschnitt |

**Wichtig:** `<pb>`-Elemente stehen **innerhalb** der `<div>`-Elemente.

### Vollständiges Strukturbeispiel

```xml
<text>
  <body>
    <div n="1">
      <pb facs="#f0001" n="1"/>
      <head>
        <title type="main">Temps alternés</title>
        <title type="sub">roman</title>
      </head>

      <div n="2">
        <head>Kapitel 1</head>

        <div n="3">
          <head>Unterkapitel 1.1</head>
          <p>Es geht hier um Philosophie</p>
        </div>

        <div n="3">
          <head>Unterkapitel 1.2</head>
          <p>Es geht hier genauer gesagt um die Philosophie von Jeanne Hersch</p>
        </div>
      </div>
    </div>
  </body>
</text>
```

---

## Zeichennormalisierung

> **⚠️ Offene Frage:** Sollen Zeichen normalisiert oder vorlagengetreu übernommen werden? Besonders bei französischen Gepflogenheiten. Expertenmeinung (Bähler) ausstehend.

### Grundsatz

Laut interner Richtlinien (DOCX) gilt **Vorlagentreue** – die Zeichen werden so wiedergegeben, wie sie im Original stehen:

| Element | Behandlung |
|---------|------------|
| ß (scharf S) | Als solches transkribieren (U+00DF) |
| Horizontale Striche | Wie in der Vorlage (Gedankenstriche, Spiegelstriche, von-bis, Trennstriche) |
| Klammern | Wie in der Vorlage |
| Anführungszeichen | Wie in der Vorlage |
| Typografie Überschriften | Wie in der Vorlage |

### Normalisierung für LLM-Pipeline

Das README.md definiert zusätzlich Normalisierungsregeln, die für die **automatisierte Verarbeitung** relevant sein können:

| Quellzeichen | Zielzeichen | Unicode | Regel |
|--------------|-------------|---------|-------|
| Bindestrich-Minus (-) | Halbgeviertstrich (–) | U+2013 | Gedankenstriche, Spiegelstriche, von-bis-Striche |
| Bindestrich-Minus (-) | Viertelgeviertstrich (‐) | U+2010 | Trenn- und Bindestriche |
| Gerade Anführungszeichen (") | Typografische ("") | U+201C/U+201D | Doppelt: "Doppelte Anführungszeichen" |
| Gerade Apostrophe (') | Typografische ('') | U+2018/U+2019 | Einfach: 'Einfache Anführungszeichen' |
| Apostroph (') | Rechtes Anführungszeichen (') | U+2019 | l'homme → l'homme |

**Klärungsbedarf:** Diese Regeln müssen mit dem Team abgestimmt werden, da sie im Widerspruch zur Vorlagentreue stehen können.

### Leerzeichen

| Kontext | Regel |
|---------|-------|
| Vor `:` `;` `?` `!` | Löschen |
| Aufzählungen mit Trennstrichen | Normalisieren zu `/` (Zürich/Bern/Basel) |

### Sonderzeichen

| Zeichen | Behandlung |
|---------|------------|
| ß | Erhalten (U+00DF) |
| Ligaturen (œ, æ) | Erhalten |
| Akzente (é, è, ê, ë, à, â, ù, û, ç, î, ï, ô) | Erhalten |
| Klammern | So wie in der Vorlage |

---

## Seitenstruktur

### Seitenumbruch

```xml
<pb facs="#f0001" n="1"/>
<pb facs="#f0002" n="2"/>
<pb facs="#f0003" n="[3]"/>  <!-- Seitenzahl nicht gedruckt -->
```

| Attribut | Bedeutung | Format |
|----------|-----------|--------|
| `facs` | Verweis auf Digitalisat | `#f` + Digitalisierungsnummer |
| `n` | Gedruckte Seitenzahl | Zahl oder `[Zahl]` wenn fehlend |

**Regeln:**
- Seitenzahlen werden **immer zu Beginn der Seite** wiedergegeben
- Die **erste Seitenzahl steht vor `<div n="1">`**
- Auf Seitenzahlen folgt **kein Zeilen-/Seitenumbruch**
- Besonderheiten (Verzierungen, Einklammerungen) werden nicht wiedergegeben

### Zeilenumbruch

```xml
<lb facs="#facs_2_l_24" n="N001"/>
<lb facs="#facs_2_l_25" n="N002" break="no"/>  <!-- Silbentrennung -->
```

| Attribut | Bedeutung |
|----------|-----------|
| `facs` | Verweis auf Zeile in Transkribus |
| `n` | Zeilennummer (N001, N002, ...) |
| `break="no"` | Wort wurde getrennt |

**Hinweis:** Zeilenfall wird auf Datenebene bewahrt (`<lb>`), erscheint aber nicht im Frontend.

### Silbentrennung

**Quelltext:**
```
philo-
sophie
```

**TEI:**
```xml
philo<lb break="no"/>sophie
```

**Regeln:**
- Silbentrennungen am Zeilenende werden **entfernt**
- Das Trennzeichen (¬) wird **gelöscht**
- `<lb break="no"/>` wird **ohne vorangehendes Leerzeichen** gesetzt
- Bei Silbentrennung über **Seitenumbruch**: Kein `<lb break="no"/>`, Nichtzeichen (¬) durch Trennstrich (‐) ersetzen

---

## Textstruktur

### Absätze

```xml
<p facs="#facs_2_r_2">
  Text des Absatzes...
</p>
```

**Regeln:**
- Absatzstruktur wird aus der Vorlage übernommen
- Einrückungen der ersten Zeile werden **nicht** ausgezeichnet
- Zeichen für größere Absätze (Asterisk, Striche) werden **nicht** wiedergegeben

### Vertikaler Abstand

```xml
<space dim="vertical"/>
```

Für größere Abstände zwischen Absätzen.

### Überschriften

```xml
<head>
  <title type="main">Haupttitel</title>
  <title type="sub">Untertitel</title>
</head>
```

**Regeln:**
- Überschriften werden mit `<head>` getaggt
- Typografische Besonderheiten von Überschriften werden **nicht** abgebildet

### Listen

```xml
<list>
  <head>[ggf. Titel der Liste]</head>
  <item>1. [Inhalt des ersten Listenpunkts]</item>
  <item>2. [Inhalt des zweiten Listenpunkts]</item>
  <item>[n]. [Inhalt des n-ten Listenpunkts]</item>
</list>
```

**Wichtig:** Nummerierungen werden **auf Textebene** realisiert, nicht als Attribut.

### Tabellen

```xml
<table>
  <head>[ggf. Titel der Tabelle]</head>
  <row>
    <cell>[Text einer Tabellen-Zelle]</cell>
    <cell>[Text einer Tabellen-Zelle]</cell>
  </row>
</table>
```

---

## Hervorhebungen

| Rendering | TEI | Beispiel |
|-----------|-----|----------|
| Fett | `<hi rendition="#b">` | `<hi rendition="#b">wichtig</hi>` |
| Kursiv | `<hi rendition="#i">` | `<hi rendition="#i">Philosophie</hi>` |
| Unterstrichen | `<hi rendition="#u">` | `<hi rendition="#u">beachte</hi>` |
| Gesperrt | `<hi rendition="#g">` | `<hi rendition="#g">Hervorhebung</hi>` |
| Hochgestellt | `<hi rendition="#sup">` | `<hi rendition="#sup">1</hi>` |
| Tiefgestellt | `<hi rendition="#sub">` | `<hi rendition="#sub">2</hi>` |

**Wichtig:** Nur **semantisch relevante** Hervorhebungen werden ausgezeichnet, nicht rein typografische (z.B. Kapitälchen in Überschriften).

---

## Sprachwechsel

```xml
<foreign xml:lang="deu">deutscher Text</foreign>
<foreign xml:lang="eng">English text</foreign>
<foreign xml:lang="lat">Lorem ipsum</foreign>
```

Sprachcodes nach **ISO 639-3**:

| Code | Sprache |
|------|---------|
| `fra` | Französisch |
| `deu` | Deutsch |
| `eng` | Englisch |
| `ita` | Italienisch |
| `lat` | Latein |

---

## Fußnoten

### Einfache Fußnote

```xml
<p>
  Tel est le thème développé par Karl Jaspers dans son ouvrage
  La Foi philosophique
  <note place="foot" n="1" xml:id="fn125-1">
    Der philosophische Glaube, Piper Verlag, München, 1948.
  </note>
</p>
```

| Attribut | Bedeutung | Format |
|----------|-----------|--------|
| `place="foot"` | Fußnote am Seitenfuß | Konstant |
| `n` | Original-Fußnotennummer wie im Druck | Zahl/Zeichen |
| `xml:id` | Eindeutige ID | `fn[Seitenzahl]-[Nummer]` |

**Regeln:**
- `<note>` steht **direkt an der Textstelle** mit dem Fußnotenzeichen
- Das Fußnotenzeichen selbst wird **nicht** als Zeichen wiedergegeben
- Die physische Position am Seitenfuß wird über `@place="foot"` kodiert

### Mehrseitige Fußnote

```xml
<!-- Seite 125 -->
<note place="foot" n="1" xml:id="fn125-1" next="#fn126-1a">
  Beginn der Fußnote...
</note>
<lb/>

<pb facs="#f0126" n="126"/>

<!-- Text Folgeseite bis Schluss -->

<note place="foot" xml:id="fn126-1a" prev="#fn125-1">
  ...Fortsetzung der Fußnote.
</note>
<lb/>
```

**Regeln:**
- `<note>` wird **vor dem Seitenumbruch geschlossen**
- Fortsetzung wird erfasst, wo sie im Text erscheint (meist am Seitenende)
- Verbindung über `@xml:id`, `@next` und `@prev`

---

## Druckfehlerkorrektur

```xml
<choice>
  <sic>Eclairement</sic>
  <corr>Éclairement</corr>
</choice>
```

**Interne Richtlinie (DOCX):** Offensichtliche Druckfehler werden **stillschweigend korrigiert**.

> **Hinweis:** Das bedeutet, dass `<choice>/<sic>/<corr>` möglicherweise nur bei nicht-offensichtlichen Fehlern verwendet wird. Klärung erforderlich.

---

## Registereinträge (Entitäten)

### Grundregel

**Jede Nennung wird referenziert**, auch bei Wiederholungen. Alle `ref`-Attribute beziehen sich auf die GND.

**Ausnahmen:**
- Entitäten in Bildunterschriften werden **nicht** ausgezeichnet
- Möglichst kein „verschachteltes" Tagging (z.B. Person innerhalb eines Werktitels)

### Personen

```xml
<persName ref="GND:118815679">Hersch</persName>
```

**Hinweis (DOCX):** Familienname und Vornamen werden **nicht** unterschieden – nur `<persName>` ohne Untergliederung.

### Organisationen

```xml
<orgName ref="GND:1010450-1">Universität Genf</orgName>
```

### Werke

```xml
<bibl corresp="GND:1088036961">L'être et la forme</bibl>
```

**Hinweis (DOCX):** `<bibl/>` für bibliografische Nachweise.

---

## Spezielle Dokumenttypen

### Rezension

```xml
<div type="review">
  <head>
    <bibl corresp="GND:xxxx">
      Karl Jaspers,
      Philosophie, trad. de Jeanne Hersch
      avec la collaboration d'Irène Kruse et de Jeanne Etoré, Paris,
      Ed. Springer-Verlag, 26, rue des Carmes, 75005 Paris, 1986,
      relié, 17 × 25, 822 p.
    </bibl>
  </head>
  <p>Rezensionstext...</p>
</div>
```

### Redaktionelle Einleitungen/Nachbemerkungen

```xml
<ab type="redactional" hand="xy">
  An unsere Leser: Das folgende Interview wurde im Frühjahr 1975 schriftlich geführt.
</ab>
```

**Hinweis (DOCX):** Redaktionelle Texte, die nicht von Jeanne Hersch stammen, werden mit `<ab type="redactional" hand="xy">` ausgezeichnet.

### Infoboxen und Marginalien

Infoboxen, Faktenkästen oder sonstige Marginalien, die **nicht von Jeanne Hersch** verfasst wurden (z.B. „An unsere Leser"), werden nur wiedergegeben, wenn sie einen **inhaltlichen Bezug zum Haupttext** aufweisen. Die Infobox kann am Ende des Texts hinzugefügt und als Fremdtext ausgewiesen werden.

### Interview

```xml
<div type="interview">
  <head>Interview mit <persName ref="GND:118815679">Jeanne Hersch</persName> über Freiheit</head>

  <p>Das folgende Interview wurde im Frühjahr 1975 schriftlich geführt. Die Fragen stellte
     <persName ref="GND:123456789">Hans Meier</persName>.
  </p>

  <sp>
    <speaker><persName ref="GND:123456789">Hans Meier</persName>:</speaker>
    <p>Wie würden Sie Freiheit in einem Satz definieren?</p>
  </sp>

  <sp>
    <speaker><persName ref="GND:118815679">Jeanne Hersch</persName>:</speaker>
    <p>Freiheit bedeutet, das zu wollen, was man als richtig erkannt hat.</p>
  </sp>
</div>
```

**Hinweis:** `<sp>` kann durch `@type` spezifiziert werden (z.B. `@type="question"` oder `@type="answer"`).

### Gesprächsrunde

```xml
<div type="conversation">
  <head>Gesprächsrunde zum Thema „Freiheit"</head>

  <sp>
    <speaker><persName ref="GND:118815679">Hans Meier</persName>:</speaker>
    <p>Vielen Dank, dass Sie heute alle gekommen sind.</p>
  </sp>

  <sp>
    <speaker><persName ref="GND:118815679">Anna Müller</persName>:</speaker>
    <p>Gern geschehen.</p>
  </sp>
</div>
```

### Lexikonartikel

```xml
<div type="entry">
  <head type="lemma">JASPERS, Karl, 1883–1969</head>

  <p>Einleitender Überblick über Person und Bedeutung ...</p>

  <div n="2">
    <head>Leben</head>
    <p>...</p>
  </div>

  <div n="2">
    <head>Philosophie</head>
    <p>...</p>
  </div>

  <div type="bibliography">
    <head>Literatur</head>
    <listBibl>
      <bibl>...</bibl>
      <bibl>...</bibl>
    </listBibl>
  </div>
</div>
```

**Wichtig:**
- Bibliografie steht in `<div type="bibliography">` mit `<listBibl>`
- Einträge werden mit `<bibl>` ausgezeichnet, aber **ohne GND-Verknüpfung**
- Weitere Entitäten (Personen, Organisationen) in Bibliografien werden **nicht** ausgezeichnet

---

## Paratexte

### Front-Matter

```xml
<text>
  <front>
    <div type="editorial">
      <head>Vortrag an der Pestalozzifeier 1970 der Sektion Bern</head>
      <p>...</p>
    </div>
  </front>

  <body>
    <div n="1">
      <!-- hier beginnt der eigentliche Text -->
    </div>
  </body>
</text>
```

**Verwendung:** Vorworte, Redaktionelle Hinweise, einleitende Kommentare, Entstehungskontext.

### Back-Matter

```xml
<body>
  ...
</body>

<back>
  <div type="translation">
    <head>Übersetzungen</head>
    <p>Eine französische Übersetzung des Textes findet sich auf S. 52–55.</p>
  </div>
  <div type="reprint">
    <p>Nachdruck erschienen in: [bibliografische Angaben]</p>
  </div>
</back>
```

**Mögliche Formulierungen:**
- "Französische Übersetzung erschienen in: [...]"
- "Nachdruck erschienen in: [...]"
- "Auch erschienen in: [...]"

---

## Abbildungen

```xml
<figure>
  <graphic xml:id="fig1" url="..\..\images\fig1.tif"/>
  <head>[ggf. Titel der Abbildung]</head>
  <p>[ggf. Erläuterung zur Abbildung im Text]</p>
</figure>
```

**Regeln:**
- IDs fortlaufend: fig1, fig2, fig3...
- `<figure>` wird **als eigenständiger Block** ausgezeichnet, nicht innerhalb von `<p>`
- Bilder nur aufnehmen, wenn für das Verständnis des Textes **erforderlich**
- Speicherort: `images/` Ordner

---

## Auslassungen

Folgende Elemente werden **nicht** transkribiert:

| Auslassung | Anmerkung |
|------------|-----------|
| Titelseiten | Außer bei Monografien |
| Lebenslauf von Jeanne Hersch | Auch wenn vor dem Text beigefügt |
| Kolumnentitel | - |
| Klappentexte | - |
| Urhebervermerke | "von Jeanne Hersch" nur in Metadaten |
| Initialen | Nicht ausgezeichnet |
| Mehrspaltigkeit | Nicht als solche wiedergegeben |
| Fremdtexte in Marginalien | Nur wenn inhaltlich relevant |

**Bei Mehrspaltigkeit:** Beim Spaltenumbruch wird kein Absatz gemacht, das durch Transkribus generierte `<p>` wird gelöscht.

---

## TEI-Elementinventar

| Element | Attribute | Verwendung |
|---------|-----------|------------|
| `<TEI>` | xmlns, type="naegeli" | Wurzelelement |
| `<teiHeader>` | - | Metadaten (aus ALMA per Skript) |
| `<text>` | - | Textcontainer |
| `<front>` | - | Paratexte vorne |
| `<body>` | - | Haupttext |
| `<back>` | - | Paratexte hinten |
| `<div>` | n, type | Gliederung |
| `<pb>` | facs, n | Seitenumbruch |
| `<lb>` | facs, n, break | Zeilenumbruch |
| `<head>` | type | Überschrift |
| `<title>` | type (main/sub) | Titel |
| `<p>` | facs | Absatz |
| `<hi>` | rendition | Hervorhebung |
| `<persName>` | ref | Person mit GND |
| `<orgName>` | ref | Organisation mit GND |
| `<bibl>` | corresp | Werk mit GND |
| `<note>` | place, n, xml:id, next, prev | Fußnote |
| `<foreign>` | xml:lang | Sprachwechsel |
| `<space>` | dim | Abstand |
| `<list>` | - | Liste |
| `<item>` | - | Listeneintrag |
| `<table>` | - | Tabelle |
| `<row>` | - | Tabellenzeile |
| `<cell>` | - | Tabellenzelle |
| `<figure>` | xml:id | Abbildung |
| `<graphic>` | xml:id, url | Bildreferenz |
| `<choice>` | - | Korrektur-Container |
| `<sic>` | - | Fehler im Original |
| `<corr>` | - | Korrigierte Form |
| `<sp>` | type | Redebeitrag |
| `<speaker>` | - | Sprechername |
| `<listBibl>` | - | Bibliografische Liste |
| `<ab>` | type, hand | Anonymer Block (redaktionelle Texte) |

---

## Transkribus-Vorbereitung

Die Texterfassung erfolgt in Transkribus:

### OCR
- Modell: **Print M1**
- Anschließend vollständige manuelle Korrektur

### Fußnoten in Transkribus (DOCX)
- Um die Fußnote wird **eine eigene Textregion** gesetzt
- Die Fußnote wird **ans Ende aller Textregionen** verschoben

### Absätze in Transkribus (DOCX)
- Größere Absätze werden mit **(vertical)** vermerkt

### Structural Tags in Transkribus
- `footnote`
- `heading`
- `page-number`
- `caption` (für Bildunterschriften)

### Renderings in Transkribus
- `bold`
- `italic`
- `strikethrough`
- `underlined`
- `subscript`
- `superscript`

### Textual Tags (in Diskussion)
- `div`
- `organization`
- `person`
- `sic`
- `speech`
- `unclear`
- `work`

---

## Facsimile-Koordinaten (optional)

Mit Gemini 3 Agentic Vision können präzise Bounding-Box-Koordinaten für Textregionen generiert werden. Dies ermöglicht eine Verknüpfung zwischen TEI-Text und Digitalisat-Position.

### Grundstruktur

```xml
<TEI>
  <facsimile>
    <surface xml:id="f0001" ulx="0" uly="0" lrx="3683" lry="4224">
      <zone xml:id="p1_col1" ulx="100" uly="200" lrx="1800" lry="4000"/>
      <zone xml:id="p1_col2" ulx="1850" uly="200" lrx="3600" lry="4000"/>
    </surface>
  </facsimile>
  <text>
    <body>
      <div n="1">
        <pb facs="#f0001" n="1"/>
        <p facs="#p1_col1">Text der linken Spalte...</p>
        <p facs="#p1_col2">Text der rechten Spalte...</p>
      </div>
    </body>
  </text>
</TEI>
```

### Attribute

| Element | Attribut | Bedeutung |
|---------|----------|-----------|
| `<surface>` | ulx, uly, lrx, lry | Gesamtbild-Koordinaten (upper-left, lower-right) |
| `<zone>` | ulx, uly, lrx, lry | Textregion-Koordinaten |
| `<zone>` | xml:id | Eindeutige ID zur Verknüpfung mit `@facs` |

### Koordinatenformat

Gemini 3 Agentic Vision liefert Koordinaten im `xywh`-Format (x, y, width, height). Umrechnung:

```
ulx = x
uly = y
lrx = x + width
lry = y + height
```

### Nutzen

| Aspekt | Vorteil |
|--------|---------|
| Wissenschaftlich | Präzise Bild-Text-Verknüpfung |
| IIIF-kompatibel | Koordinaten können für IIIF-Annotationen genutzt werden |
| Qualitätssicherung | Visuelle Überprüfung der OCR-Zuordnung |

**Hinweis:** Facsimile-Koordinaten sind optional und erhöhen den Aufwand. Empfohlen für besonders wichtige Dokumente oder zweispaltige Layouts.

---

## Offene Fragen

### Aus internen Richtlinien (DOCX-Kommentare)

Diese Fragen wurden im internen Dokument markiert und erfordern Klärung mit Expertin Bähler:

1. **Normalisierung vs. Vorlagentreue:** Sollen Textmerkmale vereinheitlicht werden oder aus der Vorlage übernommen? Insbesondere französische Gepflogenheiten betreffend.

2. **Typografie der Überschriften:** Dieselbe Frage wie bei Normalisierungen.

3. **Metadaten-Integration:** Ist es möglich, die Metadaten aus Alma und die ID aus der Tabelle zu beziehen? (MMSIDs in Exceltabelle)

### Weitere offene Punkte

- [ ] Schlagworte: Wer erstellt diese? Kommen sie in den Header? *(DOCX: Abschnitt leer)*
- [ ] div-type-Werte für Front-Matter: editorial, context, preface, introduction, sourceNote?
- [ ] div-type-Werte für Back-Matter: translation, reprint, publication, bibliography, commentary?
- [ ] GND-Werksätze in Back-Matter?
- [ ] Systematischer Einsatz von Textual Tags in Transkribus?

---

## Dokumentmetadaten

| Quelle | Letzte Änderung | Autor |
|--------|-----------------|-------|
| README.md | – | ZBZ |
| dta_basisformat_komplett.md | – | DTA |
| Auszeichnungsrichtlinien Hersch INTERN.docx | 2025-06-25 | Marc Zobrist (Revision 74) |

**Beteiligte (DOCX):** Sharon Rom, Elias Kreyenbühl, Marc Zobrist

---

## Referenzen

- [QUELLENANALYSE](QUELLENANALYSE.md) für Korpus und Dokumenttypen
- [GND-STRATEGIE](GND-STRATEGIE.md) für Entitätsverknüpfung
- [ARCHITEKTUR](ARCHITEKTUR.md) für Pipeline-Integration
- [DECISIONS](DECISIONS.md) für offene TEI-Fragen

---

*Erstellt: 2026-01-29 | Aktualisiert: 2026-02-18*
