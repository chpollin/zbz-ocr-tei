# TEI-Mapping

Transformationsregeln von Quelltext zu TEI-XML nach DTA-Basisformat mit projektspezifischen Anpassungen.

---

## Grundprinzipien

1. **Zeichengetreuer Lesetext** mit Registererschließung
2. **DTA-Basisformat** als Grundlage
3. **Normalisierung** bestimmter Zeichen (keine diplomatische Transkription)
4. **Jede Entität wird verlinkt**, auch bei Wiederholung

---

## Dokumentstruktur

### Grundgerüst

```xml
<?xml version='1.0' encoding='UTF-8'?>
<TEI xmlns='http://www.tei-c.org/ns/1.0' type="naegeli">
  <teiHeader>
    <!-- wird per Skript befüllt -->
  </teiHeader>
  <text>
    <front><!-- optional: Vorreden, Entstehungskontext --></front>
    <body>
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

---

## Zeichennormalisierung

### Interpunktion

| Quellzeichen | Zielzeichen | Unicode | Regel |
|--------------|-------------|---------|-------|
| Bindestrich-Minus (-) | Halbgeviertstrich (–) | U+2013 | Bei Gedankenstrichen |
| Bindestrich-Minus (-) | Viertelgeviertstrich (‐) | U+2010 | Bei Trennstrichen |
| Gerade Anführungszeichen (") | Typografische ("") | U+201C/U+201D | Doppelt |
| Gerade Apostrophe (') | Typografische ('') | U+2018/U+2019 | Einfach |
| Apostroph (') | Rechtes Anführungszeichen (') | U+2019 | l'homme → l'homme |

### Leerzeichen

| Kontext | Regel |
|---------|-------|
| Vor `:` `;` `?` `!` | Löschen |
| Aufzählungen mit `-` | Normalisieren zu `/` (Zürich/Bern/Basel) |

### Sonderzeichen

| Zeichen | Behandlung |
|---------|------------|
| ß | Erhalten (U+00DF) |
| Ligaturen (œ, æ) | Erhalten |
| Akzente (é, è, ê, etc.) | Erhalten |

---

## Seitenstruktur

### Seitenumbruch

```xml
<pb facs="#f0001" n="1"/>
<pb facs="#f0002" n="2"/>
<pb facs="#f0003" n="[3]"/>  <!-- Seitenzahl nicht gedruckt -->
```

| Attribut | Bedeutung |
|----------|-----------|
| `facs` | Verweis auf Faksimile (#f + laufende Nummer) |
| `n` | Gedruckte Seitenzahl, in `[]` wenn fehlend |

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

---

## Textstruktur

### Absätze

```xml
<p facs="#facs_2_r_2">
  Text des Absatzes...
</p>
```

Einrückungen werden **nicht** ausgezeichnet.

### Überschriften

```xml
<head>
  <title type="main">Haupttitel</title>
  <title type="sub">Untertitel</title>
</head>
```

### Listen

```xml
<list>
  <item>1. Erster Punkt</item>
  <item>2. Zweiter Punkt</item>
</list>
```

Nummerierung wird **manuell** im Text belassen, nicht als Attribut.

### Tabellen

```xml
<table>
  <row>
    <cell>Zelle 1</cell>
    <cell>Zelle 2</cell>
  </row>
</table>
```

### Vertikaler Abstand

```xml
<space dim="vertical"/>
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

Sprachcodes nach ISO 639-3:
- `fra` = Französisch
- `deu` = Deutsch
- `eng` = Englisch
- `ita` = Italienisch
- `lat` = Latein

---

## Fußnoten

### Einfache Fußnote

```xml
<note place="foot" n="1" xml:id="fn566-1">
  Inhalt der Fußnote.
</note>
```

| Attribut | Bedeutung |
|----------|-----------|
| `place="foot"` | Fußnote (nicht Endnote) |
| `n` | Fußnotenzeichen |
| `xml:id` | Eindeutige ID: fn + Seitenzahl + - + Nummer |

### Mehrseitige Fußnote

```xml
<!-- Seite 566 -->
<note place="foot" n="1" xml:id="fn566-1" next="#fn567-1a">
  Beginn der Fußnote...
</note>

<!-- Seite 567 -->
<note place="foot" xml:id="fn567-1a" prev="#fn566-1">
  ...Fortsetzung der Fußnote.
</note>
```

---

## Druckfehlerkorrektur

```xml
<choice>
  <sic>Eclairement</sic>
  <corr>Éclairement</corr>
</choice>
```

---

## Spezielle Dokumenttypen

### Rezension

```xml
<div type="review">
  <head>
    <bibl corresp="GND:4343581-6">
      Karl Jaspers, <hi rendition="#i">Philosophie</hi>,
      trad. de Jeanne Hersch...
    </bibl>
  </head>
  <p>Rezensionstext...</p>
</div>
```

### Interview

```xml
<div type="interview">
  <sp>
    <speaker>Interviewer</speaker>
    <p>Frage...</p>
  </sp>
  <sp>
    <speaker>Jeanne Hersch</speaker>
    <p>Antwort...</p>
  </sp>
</div>
```

### Gesprächsrunde

```xml
<div type="conversation">
  <sp>
    <speaker>Teilnehmer A</speaker>
    <p>Beitrag...</p>
  </sp>
</div>
```

### Lexikonartikel

```xml
<div type="entry">
  <head type="lemma">Jaspers, Karl</head>
  <div n="2">
    <head>Leben</head>
    <p>...</p>
  </div>
  <div type="bibliography">
    <listBibl>
      <bibl>Werk 1</bibl>
      <bibl>Werk 2</bibl>
    </listBibl>
  </div>
</div>
```

**Wichtig:** Bibliografie in Lexikonartikeln wird **ohne** GND-Verknüpfung erfasst.

---

## Paratexte

### Front-Matter

```xml
<front>
  <div>
    <p>Redaktioneller Hinweis...</p>
  </div>
  <div>
    <p>Entstehungskontext...</p>
  </div>
</front>
```

### Back-Matter

```xml
<back>
  <div type="translation">
    <p>Hinweis auf Übersetzung...</p>
  </div>
  <div type="reprint">
    <p>Hinweis auf Nachdruck...</p>
  </div>
</back>
```

---

## Abbildungen

```xml
<figure>
  <graphic xml:id="fig1" url="[Speicherort]"/>
</figure>
```

IDs fortlaufend: fig1, fig2, fig3...

---

## Auslassungen

Folgende Elemente werden **nicht** transkribiert:

- Titelseiten (außer bei Monografien)
- Lebensläufe
- Kolumnentitel
- Klappentexte
- Urhebervermerke
- Initialen (nicht ausgezeichnet)
- Mehrspaltigkeit (nicht als solche wiedergegeben)

---

## TEI-Elementinventar

| Element | Attribute | Verwendung |
|---------|-----------|------------|
| `<TEI>` | xmlns, type="naegeli" | Wurzelelement |
| `<teiHeader>` | - | Metadaten (per Skript) |
| `<text>` | - | Textcontainer |
| `<front>` | - | Paratexte vorne |
| `<body>` | - | Haupttext |
| `<back>` | - | Paratexte hinten |
| `<div>` | n, type | Gliederung |
| `<pb>` | facs, n | Seitenumbruch |
| `<lb>` | facs, n, break | Zeilenumbruch |
| `<head>` | type | Überschrift |
| `<title>` | type | Titel |
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
| `<figure>` | - | Abbildung |
| `<graphic>` | xml:id, url | Bildreferenz |
| `<choice>` | - | Korrektur-Container |
| `<sic>` | - | Fehler im Original |
| `<corr>` | - | Korrigierte Form |
| `<sp>` | - | Redebeitrag |
| `<speaker>` | type | Sprechername |

---

## Offene Fragen

*TODO: Aus TEI-Referenzdateien klären*

- Konkrete Beispiele für mehrseitige Fußnoten mit `@next/@prev`
- Varianten bei der Druckfehlerkorrektur
- Umgang mit Abkürzungen
- Behandlung von Zitaten (eigenes Element?)

---

*Erstellt: 29.01.2026*
